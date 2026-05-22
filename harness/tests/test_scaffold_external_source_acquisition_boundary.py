"""Tests for the WO-60 scaffold external-source acquisition boundary.

The tests exercise the inert acquisition-boundary observation across
three origin modes (`url`, `local_path`, `pasted_text`) without
fetching, reading, or echoing any external content. The same
boundary as WO-50 through WO-59 applies: no real retrieval call, no
adapter invocation, no network call, no file IO inside the module,
no hash computation, no metrics, no ranking, no architecture choice,
and no benchmark readiness change.
"""

import ast
import copy
import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_external_source_acquisition_boundary import (
    ACQUISITION_OUTPUT_FORBIDDEN_PHRASES,
    ALLOWED_DECLARED_KINDS,
    ALLOWED_ORIGIN_MODES,
    ALLOWED_OUTPUT_KEYS,
    DuplicateAcquisitionOrigin,
    DuplicateAcquisitionRequestId,
    ForbiddenAcquisitionField,
    ForbiddenLanguageInAcquisitionBoundary,
    InvalidContentAvailability,
    InvalidContentHash,
    InvalidContentLength,
    InvalidDeclaredKind,
    InvalidOriginMode,
    MissingAcquisitionRequestField,
    NonListAcquisitionRequests,
    NonObjectAcquisitionRequest,
    ORIGIN_MODE_ORDER,
    REQUIRED_REQUEST_FIELDS,
    UnknownAcquisitionRequestField,
    run_scaffold_external_source_acquisition_boundary,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT, "harness", "scaffold_external_source_acquisition_boundary.py"
)


def _url_request(suffix="001", content_available=False):
    return {
        "request_id": "req-{0}".format(suffix),
        "origin_mode": "url",
        "origin_locator": "https://synthetic-external-source.invalid/path/{0}".format(suffix),
        "declared_kind": "prompt_collection",
        "content_available": content_available,
        "content_byte_length": 4096 if content_available else 0,
        "content_hash": (
            "deadbeef" + "0" * 56 + "-{0}".format(suffix)
            if content_available
            else ""
        ),
        "observed_at": "2026-05-20T00:00:00Z",
    }


def _local_path_request(suffix="002", content_available=False):
    return {
        "request_id": "req-{0}".format(suffix),
        "origin_mode": "local_path",
        "origin_locator": "/synthetic/path/to/file-{0}.txt".format(suffix),
        "declared_kind": "document_collection",
        "content_available": content_available,
        "content_byte_length": 2048 if content_available else 0,
        "content_hash": (
            "beefcafe" + "0" * 56 + "-{0}".format(suffix)
            if content_available
            else ""
        ),
        "observed_at": "2026-05-20T00:00:00Z",
    }


def _pasted_text_request(suffix="003", content_available=True):
    return {
        "request_id": "req-{0}".format(suffix),
        "origin_mode": "pasted_text",
        "origin_locator": "user-pasted-block-{0}".format(suffix),
        "declared_kind": "skill_collection",
        "content_available": content_available,
        "content_byte_length": 1024 if content_available else 0,
        "content_hash": (
            "feedface" + "0" * 56 + "-{0}".format(suffix)
            if content_available
            else ""
        ),
        "observed_at": "2026-05-20T00:00:00Z",
    }


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


def _halt_came_before_raise(event_log, halt_reason):
    halt = _last_halt_event(event_log)
    return halt is not None and halt["reason"] == halt_reason


class AcquisitionBoundaryCleanPassTest(unittest.TestCase):
    def test_clean_pass_empty_list(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary([], log)
        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 13)
        self.assertEqual(
            output["acquisition_boundary_kind"],
            "scaffold_external_source_acquisition_boundary",
        )
        self.assertEqual(output["request_count"], 0)
        self.assertEqual(output["acquisition_references"], [])
        self.assertEqual(output["content_available_count"], 0)
        self.assertEqual(output["content_missing_count"], 0)
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        self.assertFalse(log.has_halt())

    def test_clean_pass_one_url_request_content_not_available(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [_url_request("u1", content_available=False)], log
        )
        self.assertEqual(output["request_count"], 1)
        self.assertEqual(output["origin_mode_counts"]["url"], 1)
        self.assertEqual(output["origin_mode_counts"]["local_path"], 0)
        self.assertEqual(output["origin_mode_counts"]["pasted_text"], 0)
        self.assertEqual(output["content_missing_count"], 1)
        self.assertEqual(output["content_available_count"], 0)

    def test_clean_pass_one_local_path_request_content_not_available(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [_local_path_request("p1", content_available=False)], log
        )
        self.assertEqual(output["request_count"], 1)
        self.assertEqual(output["origin_mode_counts"]["local_path"], 1)
        self.assertEqual(output["content_missing_count"], 1)

    def test_clean_pass_one_pasted_text_request_content_available_only_metadata(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [_pasted_text_request("t1", content_available=True)], log
        )
        self.assertEqual(output["request_count"], 1)
        self.assertEqual(output["origin_mode_counts"]["pasted_text"], 1)
        self.assertEqual(output["content_available_count"], 1)
        # No raw pasted text should appear in the assembled output.
        # The pasted_text request only has structural fields, so the
        # output cannot contain anything that looks like raw text.
        reference = output["acquisition_references"][0]
        self.assertNotIn("text", reference)
        self.assertNotIn("body", reference)
        self.assertNotIn("content", reference)

    def test_clean_pass_with_all_three_origin_modes(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [
                _url_request("u1"),
                _local_path_request("p1"),
                _pasted_text_request("t1"),
            ],
            log,
        )
        self.assertEqual(output["request_count"], 3)
        self.assertEqual(output["origin_mode_counts"]["url"], 1)
        self.assertEqual(output["origin_mode_counts"]["local_path"], 1)
        self.assertEqual(output["origin_mode_counts"]["pasted_text"], 1)

    def test_all_authorization_booleans_remain_literal_false(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [_url_request("u1")], log
        )
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
        ):
            self.assertIs(output[key], False)

    def test_per_reference_admission_booleans_literal_false(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [
                _url_request("u1"),
                _pasted_text_request("t1", content_available=True),
            ],
            log,
        )
        for ref in output["acquisition_references"]:
            self.assertIs(ref["corpus_admitted"], False)
            self.assertIs(ref["qualified"], False)
            self.assertIs(ref["source_material_extracted"], False)
            self.assertIs(ref["route_object_created"], False)

    def test_content_available_true_does_not_flip_admission_or_qualification(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [
                _url_request("u1", content_available=True),
                _local_path_request("p1", content_available=True),
                _pasted_text_request("t1", content_available=True),
            ],
            log,
        )
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        for ref in output["acquisition_references"]:
            self.assertIs(ref["corpus_admitted"], False)
            self.assertIs(ref["qualified"], False)

    def test_hash_presence_does_not_flip_admission_or_qualification(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [_url_request("u1", content_available=True)], log
        )
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        ref = output["acquisition_references"][0]
        self.assertNotEqual(ref["content_hash_prefix"], "")
        # Full hash not echoed.
        self.assertNotIn("content_hash", ref)

    def test_passed_event_records_clean_counts(self):
        log = EventLog()
        run_scaffold_external_source_acquisition_boundary(
            [_url_request("u1"), _local_path_request("p1")], log
        )
        passed = [
            e
            for e in log.events
            if e["type"]
            == "scaffold_external_source_acquisition_boundary_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["request_count"], 2)
        self.assertEqual(passed[0]["corpus_admitted_count"], 0)
        self.assertEqual(passed[0]["qualified_count"], 0)


class AcquisitionBoundaryNonEchoTest(unittest.TestCase):
    def test_origin_locator_not_echoed_into_acquisition_boundary_note(self):
        sentinel_locator = "https://synthetic-WO60-LOCATOR-SENTINEL.invalid/aaa"
        request = _url_request("u1")
        request["origin_locator"] = sentinel_locator
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [request], log
        )
        self.assertNotIn(sentinel_locator, output["acquisition_boundary_note"])

    def test_origin_locator_not_echoed_into_references(self):
        sentinel_locator = "https://synthetic-WO60-LOCATOR-SENTINEL-BBB.invalid/bbb"
        request = _url_request("u1")
        request["origin_locator"] = sentinel_locator
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [request], log
        )
        rendered = json.dumps(output["acquisition_references"], sort_keys=True)
        self.assertNotIn(sentinel_locator, rendered)

    def test_origin_locator_length_recorded_instead(self):
        request = _url_request("u1")
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [request], log
        )
        reference = output["acquisition_references"][0]
        self.assertIn("origin_locator_length", reference)
        self.assertEqual(
            reference["origin_locator_length"], len(request["origin_locator"])
        )


class AcquisitionBoundaryShapeRejectionTest(unittest.TestCase):
    def test_non_list_rejected(self):
        log = EventLog()
        with self.assertRaises(NonListAcquisitionRequests):
            run_scaffold_external_source_acquisition_boundary("not a list", log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_external_source_acquisition_boundary_non_list_requests",
            )
        )

    def test_non_dict_request_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectAcquisitionRequest):
            run_scaffold_external_source_acquisition_boundary(
                ["not a dict"], log
            )

    def test_each_missing_required_field_rejected(self):
        for field in REQUIRED_REQUEST_FIELDS:
            request = _url_request("u1")
            del request[field]
            log = EventLog()
            with self.assertRaises(MissingAcquisitionRequestField):
                run_scaffold_external_source_acquisition_boundary([request], log)

    def test_unknown_field_rejected(self):
        request = _url_request("u1")
        request["mystery_field"] = "value"
        log = EventLog()
        with self.assertRaises(UnknownAcquisitionRequestField):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_duplicate_request_id_rejected(self):
        log = EventLog()
        with self.assertRaises(DuplicateAcquisitionRequestId):
            run_scaffold_external_source_acquisition_boundary(
                [_url_request("dup"), _url_request("dup")], log
            )

    def test_duplicate_origin_rejected(self):
        log = EventLog()
        r1 = _url_request("u1")
        r2 = _url_request("u2")
        r2["origin_locator"] = r1["origin_locator"]  # same origin
        with self.assertRaises(DuplicateAcquisitionOrigin):
            run_scaffold_external_source_acquisition_boundary([r1, r2], log)

    def test_invalid_origin_mode_rejected(self):
        request = _url_request("u1")
        request["origin_mode"] = "mystery_mode"
        log = EventLog()
        with self.assertRaises(InvalidOriginMode):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_invalid_declared_kind_rejected(self):
        request = _url_request("u1")
        request["declared_kind"] = "not_a_known_label"
        log = EventLog()
        with self.assertRaises(InvalidDeclaredKind):
            run_scaffold_external_source_acquisition_boundary([request], log)


class AcquisitionBoundaryContentAvailabilityTest(unittest.TestCase):
    def test_content_available_must_be_bool(self):
        request = _url_request("u1")
        request["content_available"] = "yes"
        log = EventLog()
        with self.assertRaises(InvalidContentAvailability):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_content_available_false_requires_zero_byte_length(self):
        request = _url_request("u1", content_available=False)
        request["content_byte_length"] = 42
        log = EventLog()
        with self.assertRaises(InvalidContentLength):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_content_available_false_requires_empty_hash(self):
        request = _url_request("u1", content_available=False)
        request["content_hash"] = "should-be-empty"
        log = EventLog()
        with self.assertRaises(InvalidContentHash):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_content_available_true_requires_non_negative_int_byte_length(self):
        request = _url_request("u1", content_available=True)
        request["content_byte_length"] = -1
        log = EventLog()
        with self.assertRaises(InvalidContentLength):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_content_available_true_rejects_bool_byte_length(self):
        request = _url_request("u1", content_available=True)
        request["content_byte_length"] = True
        log = EventLog()
        with self.assertRaises(InvalidContentLength):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_content_available_true_requires_non_empty_hash(self):
        request = _url_request("u1", content_available=True)
        request["content_hash"] = ""
        log = EventLog()
        with self.assertRaises(InvalidContentHash):
            run_scaffold_external_source_acquisition_boundary([request], log)

    def test_content_available_true_rejects_non_string_hash(self):
        request = _url_request("u1", content_available=True)
        request["content_hash"] = 12345
        log = EventLog()
        with self.assertRaises(InvalidContentHash):
            run_scaffold_external_source_acquisition_boundary([request], log)


class AcquisitionBoundaryForbiddenFieldTest(unittest.TestCase):
    def test_each_forbidden_field_rejected(self):
        forbidden_fields = (
            "qualified",
            "qualification_ref",
            "corpus_admitted",
            "source_card",
            "route_card",
            "authority",
            "trust",
            "freshness",
            "ownership",
            "validation_evidence",
            "qualification_evidence",
            "extracted_material",
            "normalized_material",
            "candidate_fragments",
            "candidate_route_fragments",
            "candidate_workflow_fragments",
            "route",
            "route_id",
            "route_state",
            "plane",
            "official",
            "executable",
            "selected_route",
            "production_route",
            "benchmark_fixture_class",
            "golden_intent",
            "hard_negative",
            "boundary_violation",
        )
        for field in forbidden_fields:
            request = _url_request("u1")
            request[field] = "any value"
            log = EventLog()
            with self.assertRaises(
                ForbiddenAcquisitionField,
                msg="forbidden field {0!r} should be rejected".format(field),
            ):
                run_scaffold_external_source_acquisition_boundary(
                    [request], log
                )


class AcquisitionBoundaryLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [
                _url_request("u1"),
                _local_path_request("p1"),
                _pasted_text_request("t1"),
            ],
            log,
        )
        forbidden = (
            ACQUISITION_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        )
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)


class AcquisitionBoundaryIsolationTest(unittest.TestCase):
    def test_does_not_mutate_inputs(self):
        requests = [
            _url_request("u1"),
            _local_path_request("p1"),
            _pasted_text_request("t1"),
        ]
        before = copy.deepcopy(requests)
        run_scaffold_external_source_acquisition_boundary(
            requests, EventLog()
        )
        self.assertEqual(requests, before)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_external_source_acquisition_boundary(
                    [_url_request("u1")], EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class AcquisitionBoundaryImportSurfaceTest(unittest.TestCase):
    def test_no_third_party_imports(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        for module_name in imports:
            self.assertTrue(
                module_name.startswith("harness."),
                "unexpected import in acquisition boundary: {0}".format(
                    module_name
                ),
            )

    def test_module_makes_no_file_io_network_or_hash_call(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        # Substring-based scan for tokens that should never appear.
        for token in (
            "open(",
            "pathlib",
            "urllib",
            "http.client",
            "socket",
            "subprocess",
            "os.system",
            "shutil",
            "hashlib",
            ".hexdigest",
            ".sha256",
        ):
            self.assertNotIn(
                token,
                source_text,
                "unexpected IO / network / hash token in acquisition "
                "boundary: {0}".format(token),
            )
        # `requests` is a real HTTP library; the local parameter name
        # `acquisition_requests` is not a use of that library. Scan for
        # actual library invocations only.
        for forbidden_use in (
            "import requests",
            "from requests",
            "requests.",
        ):
            self.assertNotIn(
                forbidden_use,
                source_text,
                "unexpected requests-library use in acquisition "
                "boundary: {0}".format(forbidden_use),
            )

    def test_module_does_not_use_retrieval_or_search_verbs(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in ("def query", "def search", "def retrieve", "def rank"):
            self.assertNotIn(
                token,
                source_text,
                "unexpected retrieval/search verb in acquisition boundary: "
                "{0}".format(token),
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
            self.assertNotIn(
                token,
                source_text,
                "unexpected external-integration token: {0}".format(token),
            )


class AcquisitionBoundaryFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_boundary(self):
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
        run_scaffold_external_source_acquisition_boundary(
            [_url_request("u1"), _local_path_request("p1")], EventLog()
        )
        after = inventory()
        self.assertEqual(after, before)


class AcquisitionBoundaryConstantsTest(unittest.TestCase):
    def test_allowed_origin_modes_match_packet(self):
        self.assertEqual(
            set(ALLOWED_ORIGIN_MODES),
            {"url", "local_path", "pasted_text"},
        )

    def test_origin_mode_count_order_is_deterministic(self):
        log = EventLog()
        output = run_scaffold_external_source_acquisition_boundary(
            [
                _url_request("u1"),
                _local_path_request("p1"),
                _pasted_text_request("t1"),
            ],
            log,
        )
        self.assertEqual(tuple(output["origin_mode_counts"].keys()),
                         ORIGIN_MODE_ORDER)

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
