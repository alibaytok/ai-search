"""Tests for the WO-61 scaffold URL acquisition executor.

The tests exercise the injected-fetcher pattern: every test supplies
a fake `fetch_url` callable, and the module never opens a real
network connection. The same boundary as WO-50 through WO-60
applies: no real retrieval call, no adapter invocation, no network
call inside the module, no file IO inside the module, no metrics,
no ranking, no architecture choice, and no benchmark readiness
change.
"""

import ast
import copy
import hashlib
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_url_acquisition_executor import (
    ALLOWED_DECLARED_KINDS,
    ALLOWED_OUTPUT_KEYS,
    DuplicateUrlAcquisitionRequestId,
    DuplicateUrlOriginLocator,
    FetcherNotCallable,
    FetcherReturnedNonObject,
    FetchedContentTooLarge,
    ForbiddenLanguageInUrlAcquisitionOutput,
    ForbiddenUrlAcquisitionField,
    InputContentAlreadyAvailableRejected,
    InvalidDeclaredKind,
    InvalidFetchStatus,
    InvalidFetchedAt,
    InvalidFetchedContentBytes,
    InvalidFetchedContentType,
    InvalidUrlOriginLocator,
    MAX_FETCHED_BYTES,
    MissingFetcherResultField,
    MissingUrlAcquisitionRequestField,
    NonListUrlAcquisitionRequests,
    NonObjectUrlAcquisitionRequest,
    NonUrlOriginModeRejected,
    REQUIRED_REQUEST_FIELDS,
    UnknownFetcherResultField,
    UnknownUrlAcquisitionRequestField,
    URL_ACQUISITION_OUTPUT_FORBIDDEN_PHRASES,
    run_scaffold_url_acquisition_executor,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT, "harness", "scaffold_url_acquisition_executor.py"
)


def _url_request(suffix="001", declared_kind="prompt_collection"):
    return {
        "request_id": "req-{0}".format(suffix),
        "origin_mode": "url",
        "origin_locator": "https://synthetic-external-source.invalid/path/{0}".format(suffix),
        "declared_kind": declared_kind,
        "content_available": False,
        "content_byte_length": 0,
        "content_hash": "",
        "observed_at": "2026-05-20T00:00:00Z",
    }


def _make_fake_fetcher(bytes_per_url=None, content_type="text/plain"):
    """Return a fake fetcher that records calls and returns a fixed shape."""
    calls = []
    bytes_per_url = bytes_per_url or {}

    def _fetch_url(url):
        calls.append(url)
        body = bytes_per_url.get(url, b"synthetic-WO61-content-bytes")
        return {
            "fetch_status": "fetched",
            "content_bytes": body,
            "content_type": content_type,
            "fetched_at": "2026-05-20T00:00:01Z",
        }

    return _fetch_url, calls


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, sub_value in value.items():
            for inner in _walk_strings(key):
                yield inner
            for inner in _walk_strings(sub_value):
                yield inner
    elif isinstance(value, (list, tuple)):
        for sub_value in value:
            for inner in _walk_strings(sub_value):
                yield inner


def _last_halt_event(event_log):
    for event in reversed(event_log.events):
        if event["type"] == "halt":
            return event
    return None


class UrlAcquisitionExecutorCleanPassTest(unittest.TestCase):
    def test_clean_pass_empty_list(self):
        fetcher, calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor([], fetcher, log)
        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 13)
        self.assertEqual(output["request_count"], 0)
        self.assertEqual(output["fetched_count"], 0)
        self.assertEqual(output["acquired_references"], [])
        self.assertEqual(output["total_content_byte_length"], 0)
        self.assertEqual(calls, [])
        self.assertFalse(log.has_halt())

    def test_clean_pass_one_url(self):
        request = _url_request("u1")
        fetcher, calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [request], fetcher, log
        )
        self.assertEqual(output["request_count"], 1)
        self.assertEqual(output["fetched_count"], 1)
        self.assertEqual(len(output["acquired_references"]), 1)
        ref = output["acquired_references"][0]
        self.assertEqual(ref["request_id"], "req-u1")
        self.assertEqual(ref["declared_kind"], "prompt_collection")
        self.assertIs(ref["origin_locator_observed"], True)
        self.assertEqual(
            ref["origin_locator_length"], len(request["origin_locator"])
        )
        self.assertIs(ref["content_available"], True)
        self.assertGreater(ref["content_byte_length"], 0)
        self.assertEqual(len(ref["content_hash_prefix"]), 12)
        self.assertEqual(ref["content_type"], "text/plain")
        # fetcher called once with the URL
        self.assertEqual(calls, [request["origin_locator"]])

    def test_clean_pass_multiple_urls_called_in_input_order(self):
        requests = [
            _url_request("u1"),
            _url_request("u2"),
            _url_request("u3"),
        ]
        fetcher, calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            requests, fetcher, log
        )
        self.assertEqual(output["request_count"], 3)
        self.assertEqual(output["fetched_count"], 3)
        self.assertEqual(
            calls,
            [r["origin_locator"] for r in requests],
        )

    def test_all_authorization_booleans_remain_literal_false(self):
        fetcher, _calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [_url_request("u1")], fetcher, log
        )
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
        ):
            self.assertIs(output[key], False)

    def test_per_reference_admission_booleans_literal_false(self):
        fetcher, _calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [_url_request("u1")], fetcher, log
        )
        ref = output["acquired_references"][0]
        for key in (
            "corpus_admitted",
            "qualified",
            "source_material_extracted",
            "route_object_created",
        ):
            self.assertIs(ref[key], False)

    def test_admission_counts_literal_zero(self):
        fetcher, _calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [_url_request("u1"), _url_request("u2")], fetcher, log
        )
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        self.assertEqual(output["source_material_extracted_count"], 0)

    def test_hash_prefix_is_deterministic_sha256_truncation(self):
        body = b"deterministic-WO61-content-for-hash-test"
        request = _url_request("u1")

        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": body,
                "content_type": "text/plain",
                "fetched_at": "2026-05-20T00:00:01Z",
            }

        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [request], _fetcher, log
        )
        ref = output["acquired_references"][0]
        expected_prefix = hashlib.sha256(body).hexdigest()[:12]
        self.assertEqual(ref["content_hash_prefix"], expected_prefix)

    def test_total_content_byte_length_is_sum(self):
        body1 = b"AAAA"
        body2 = b"BBBBBBBB"
        bytes_per_url = {}
        requests = [_url_request("u1"), _url_request("u2")]
        bytes_per_url[requests[0]["origin_locator"]] = body1
        bytes_per_url[requests[1]["origin_locator"]] = body2
        fetcher, _calls = _make_fake_fetcher(bytes_per_url=bytes_per_url)
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            requests, fetcher, log
        )
        self.assertEqual(
            output["total_content_byte_length"], len(body1) + len(body2)
        )

    def test_passed_event_records_clean_counts(self):
        fetcher, _calls = _make_fake_fetcher()
        log = EventLog()
        run_scaffold_url_acquisition_executor(
            [_url_request("u1"), _url_request("u2")], fetcher, log
        )
        passed = [
            e
            for e in log.events
            if e["type"] == "scaffold_url_acquisition_executor_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["request_count"], 2)
        self.assertEqual(passed[0]["fetched_count"], 2)


class UrlAcquisitionExecutorNonEchoTest(unittest.TestCase):
    def test_raw_url_not_echoed_into_references(self):
        sentinel_url = "https://synthetic-WO61-URL-SENTINEL.invalid/aaa"
        request = _url_request("u1")
        request["origin_locator"] = sentinel_url
        fetcher, _calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [request], fetcher, log
        )
        # Output dict should not contain the raw URL anywhere.
        for text in _walk_strings(output):
            self.assertNotIn(sentinel_url, text)

    def test_raw_bytes_not_echoed_into_output(self):
        sentinel_body = b"SYNTHETIC-WO61-BODY-SENTINEL-DO-NOT-LEAK"
        request = _url_request("u1")
        bytes_per_url = {request["origin_locator"]: sentinel_body}
        fetcher, _calls = _make_fake_fetcher(bytes_per_url=bytes_per_url)
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [request], fetcher, log
        )
        for text in _walk_strings(output):
            self.assertNotIn(sentinel_body.decode("ascii"), text)


class UrlAcquisitionExecutorPreFetchRejectionTest(unittest.TestCase):
    def _fetcher_must_not_be_called(self, calls):
        def _f(url):
            calls.append(url)
            return {
                "fetch_status": "fetched",
                "content_bytes": b"x",
                "content_type": "text/plain",
                "fetched_at": "now",
            }
        return _f

    def test_non_list_requests_rejected_before_fetcher_call(self):
        calls = []
        log = EventLog()
        with self.assertRaises(NonListUrlAcquisitionRequests):
            run_scaffold_url_acquisition_executor(
                "not a list",
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_non_dict_request_rejected_before_fetcher_call(self):
        calls = []
        log = EventLog()
        with self.assertRaises(NonObjectUrlAcquisitionRequest):
            run_scaffold_url_acquisition_executor(
                ["not a dict"],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_each_missing_required_field_rejected_before_fetcher_call(self):
        for field in REQUIRED_REQUEST_FIELDS:
            request = _url_request("u1")
            del request[field]
            calls = []
            log = EventLog()
            with self.assertRaises(MissingUrlAcquisitionRequestField):
                run_scaffold_url_acquisition_executor(
                    [request],
                    self._fetcher_must_not_be_called(calls),
                    log,
                )
            self.assertEqual(calls, [])

    def test_unknown_field_rejected(self):
        request = _url_request("u1")
        request["mystery"] = "value"
        calls = []
        log = EventLog()
        with self.assertRaises(UnknownUrlAcquisitionRequestField):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_each_forbidden_input_field_rejected(self):
        forbidden = (
            "qualified", "qualification_ref", "corpus_admitted",
            "source_card", "route_card", "authority", "trust",
            "freshness", "ownership", "validation_evidence",
            "qualification_evidence", "extracted_material",
            "normalized_material", "candidate_fragments",
            "candidate_route_fragments", "candidate_workflow_fragments",
            "route", "route_id", "route_state", "plane", "official",
            "executable", "selected_route", "production_route",
            "benchmark_fixture_class", "golden_intent", "hard_negative",
            "boundary_violation",
        )
        for field in forbidden:
            request = _url_request("u1")
            request[field] = "value"
            calls = []
            log = EventLog()
            with self.assertRaises(ForbiddenUrlAcquisitionField):
                run_scaffold_url_acquisition_executor(
                    [request],
                    self._fetcher_must_not_be_called(calls),
                    log,
                )
            self.assertEqual(calls, [])

    def test_duplicate_request_id_rejected_before_fetcher_call(self):
        calls = []
        log = EventLog()
        with self.assertRaises(DuplicateUrlAcquisitionRequestId):
            run_scaffold_url_acquisition_executor(
                [_url_request("dup"), _url_request("dup")],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        # Validation pass 1 may have validated the first request and
        # caught the second's duplicate id, but no fetcher call
        # should have been made.
        self.assertEqual(calls, [])

    def test_duplicate_origin_locator_rejected_before_fetcher_call(self):
        r1 = _url_request("u1")
        r2 = _url_request("u2")
        r2["origin_locator"] = r1["origin_locator"]
        calls = []
        log = EventLog()
        with self.assertRaises(DuplicateUrlOriginLocator):
            run_scaffold_url_acquisition_executor(
                [r1, r2],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_local_path_origin_rejected(self):
        request = _url_request("u1")
        request["origin_mode"] = "local_path"
        calls = []
        log = EventLog()
        with self.assertRaises(NonUrlOriginModeRejected):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_pasted_text_origin_rejected(self):
        request = _url_request("u1")
        request["origin_mode"] = "pasted_text"
        calls = []
        log = EventLog()
        with self.assertRaises(NonUrlOriginModeRejected):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_invalid_origin_locator_rejected(self):
        request = _url_request("u1")
        request["origin_locator"] = ""
        calls = []
        log = EventLog()
        with self.assertRaises(InvalidUrlOriginLocator):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_invalid_declared_kind_rejected(self):
        request = _url_request("u1")
        request["declared_kind"] = "mystery_kind"
        calls = []
        log = EventLog()
        with self.assertRaises(InvalidDeclaredKind):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_content_available_true_on_input_rejected(self):
        request = _url_request("u1")
        request["content_available"] = True
        calls = []
        log = EventLog()
        with self.assertRaises(InputContentAlreadyAvailableRejected):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_content_byte_length_nonzero_on_input_rejected(self):
        request = _url_request("u1")
        request["content_byte_length"] = 1
        calls = []
        log = EventLog()
        with self.assertRaises(InputContentAlreadyAvailableRejected):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])

    def test_content_hash_nonempty_on_input_rejected(self):
        request = _url_request("u1")
        request["content_hash"] = "preset"
        calls = []
        log = EventLog()
        with self.assertRaises(InputContentAlreadyAvailableRejected):
            run_scaffold_url_acquisition_executor(
                [request],
                self._fetcher_must_not_be_called(calls),
                log,
            )
        self.assertEqual(calls, [])


class UrlAcquisitionExecutorFetcherRejectionTest(unittest.TestCase):
    def test_non_callable_fetcher_rejected(self):
        log = EventLog()
        with self.assertRaises(FetcherNotCallable):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], "not callable", log
            )

    def test_fetcher_returning_non_dict_rejected(self):
        def _fetcher(url):
            return "not a dict"
        log = EventLog()
        with self.assertRaises(FetcherReturnedNonObject):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_missing_field_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": b"x",
                "content_type": "text/plain",
                # missing fetched_at
            }
        log = EventLog()
        with self.assertRaises(MissingFetcherResultField):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_unknown_field_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": b"x",
                "content_type": "text/plain",
                "fetched_at": "now",
                "mystery": "value",
            }
        log = EventLog()
        with self.assertRaises(UnknownFetcherResultField):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_invalid_status_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "failed",
                "content_bytes": b"x",
                "content_type": "text/plain",
                "fetched_at": "now",
            }
        log = EventLog()
        with self.assertRaises(InvalidFetchStatus):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_non_bytes_content_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": "not bytes",
                "content_type": "text/plain",
                "fetched_at": "now",
            }
        log = EventLog()
        with self.assertRaises(InvalidFetchedContentBytes):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_bytearray_content_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": bytearray(b"x"),
                "content_type": "text/plain",
                "fetched_at": "now",
            }
        log = EventLog()
        with self.assertRaises(InvalidFetchedContentBytes):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_empty_content_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": b"",
                "content_type": "text/plain",
                "fetched_at": "now",
            }
        log = EventLog()
        with self.assertRaises(InvalidFetchedContentBytes):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_oversized_content_rejected(self):
        oversized = b"x" * (MAX_FETCHED_BYTES + 1)

        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": oversized,
                "content_type": "text/plain",
                "fetched_at": "now",
            }
        log = EventLog()
        with self.assertRaises(FetchedContentTooLarge):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_invalid_content_type_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": b"x",
                "content_type": "",
                "fetched_at": "now",
            }
        log = EventLog()
        with self.assertRaises(InvalidFetchedContentType):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )

    def test_fetcher_invalid_fetched_at_rejected(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": b"x",
                "content_type": "text/plain",
                "fetched_at": "",
            }
        log = EventLog()
        with self.assertRaises(InvalidFetchedAt):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )


class UrlAcquisitionExecutorLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        fetcher, _calls = _make_fake_fetcher()
        log = EventLog()
        output = run_scaffold_url_acquisition_executor(
            [_url_request("u1"), _url_request("u2")], fetcher, log
        )
        forbidden = (
            URL_ACQUISITION_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        )
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)

    def test_forbidden_language_in_fetcher_content_type_halts(self):
        def _fetcher(url):
            return {
                "fetch_status": "fetched",
                "content_bytes": b"x",
                "content_type": "synthetic/validation evidence",
                "fetched_at": "now",
            }
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInUrlAcquisitionOutput):
            run_scaffold_url_acquisition_executor(
                [_url_request("u1")], _fetcher, log
            )


class UrlAcquisitionExecutorIsolationTest(unittest.TestCase):
    def test_does_not_mutate_inputs(self):
        requests = [_url_request("u1"), _url_request("u2")]
        before = copy.deepcopy(requests)
        fetcher, _calls = _make_fake_fetcher()
        run_scaffold_url_acquisition_executor(requests, fetcher, EventLog())
        self.assertEqual(requests, before)

    def test_function_writes_no_files(self):
        fetcher, _calls = _make_fake_fetcher()
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_url_acquisition_executor(
                    [_url_request("u1")], fetcher, EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class UrlAcquisitionExecutorImportSurfaceTest(unittest.TestCase):
    def test_module_imports_only_stdlib_or_harness(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        allowed_stdlib = {"hashlib"}
        for module_name in imports:
            if module_name.startswith("harness."):
                continue
            self.assertIn(
                module_name,
                allowed_stdlib,
                "unexpected import in URL acquisition executor: {0}".format(
                    module_name
                ),
            )

    def test_module_has_no_network_or_file_io_tokens(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in (
            "open(",
            "pathlib",
            "urllib",
            "http.client",
            "socket",
            "subprocess",
            "os.system",
            "shutil",
        ):
            self.assertNotIn(
                token,
                source_text,
                "unexpected IO / network token in URL acquisition "
                "executor: {0}".format(token),
            )
        # `requests` HTTP library specifically
        for forbidden_use in (
            "import requests",
            "from requests",
            "requests.",
        ):
            self.assertNotIn(
                forbidden_use,
                source_text,
                "unexpected requests-library use: {0}".format(forbidden_use),
            )

    def test_module_does_not_use_retrieval_or_search_verbs(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in ("def query", "def search", "def retrieve", "def rank"):
            self.assertNotIn(token, source_text)

    def test_module_does_not_invoke_wo50_through_wo60_public_functions(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for func in (
            "run_scaffold_source_intake_trace",
            "run_scaffold_source_intake_register",
            "run_scaffold_source_trace_admission_bridge",
            "run_scaffold_source_intake_smoke_package",
            "run_scaffold_route_invariant_diagnostic_reporter",
            "run_scaffold_source_intake_visible_report",
            "run_scaffold_external_source_acquisition_boundary",
        ):
            self.assertNotIn(
                func,
                source_text,
                "URL acquisition executor must not invoke {0}".format(func),
            )

    def test_module_does_not_reference_external_integration_tokens(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read().lower()
        for token in (
            "copilot",
            "waza",
            "vscode",
            "vs_code",
            "openai",
            "anthropic",
            "claude_api",
            "llm",
        ):
            self.assertNotIn(token, source_text)


class UrlAcquisitionExecutorFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_executor(self):
        def inventory():
            output = {}
            for root, _, filenames in os.walk(_BENCHMARK_FIXTURES_ROOT):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    rel = os.path.relpath(path, _BENCHMARK_FIXTURES_ROOT)
                    with open(path, "rb") as handle:
                        output[rel] = handle.read()
            return output

        before = inventory()
        fetcher, _calls = _make_fake_fetcher()
        run_scaffold_url_acquisition_executor(
            [_url_request("u1")], fetcher, EventLog()
        )
        after = inventory()
        self.assertEqual(after, before)


class UrlAcquisitionExecutorConstantsTest(unittest.TestCase):
    def test_max_fetched_bytes_constant(self):
        self.assertEqual(MAX_FETCHED_BYTES, 65536)

    def test_allowed_declared_kinds_match_wo55(self):
        self.assertEqual(
            set(ALLOWED_DECLARED_KINDS),
            {
                "prompt_collection",
                "skill_collection",
                "agent_description_collection",
                "tool_description_collection",
                "document_collection",
            },
        )


if __name__ == "__main__":
    unittest.main()
