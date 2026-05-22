"""Tests for the WO-57 scaffold in-memory source-intake smoke package.

The tests exercise the composed read-only path through WO-55 (register),
WO-56 (bridge), and WO-54 (trace) while preserving the route-first
invariants. The same boundary as WO-50 / WO-51 / WO-52 / WO-53 / WO-54
/ WO-55 / WO-56 applies: no real retrieval call, no adapter
invocation, no network call, no file IO inside the module, no hash
computation, no metrics, no ranking, no architecture choice, and no
benchmark readiness change. The package does not derive candidate
fragments of its own; fragment counts are copied from the trace
observation verbatim.
"""

import ast
import copy
import json
import os
import tempfile
import unittest
from unittest import mock

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_source_intake_smoke_package import (
    ALLOWED_OUTPUT_KEYS,
    ForbiddenLanguageInSourceIntakeSmokePackage,
    PACKAGE_OUTPUT_FORBIDDEN_PHRASES,
    run_scaffold_source_intake_smoke_package,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT, "harness", "scaffold_source_intake_smoke_package.py"
)


_PROMPT = (
    "How does the synthetic WO-57 smoke package handle a captured "
    "prompt against an external source collection?"
)


def _reference(suffix="001", declared_kind="prompt_collection"):
    return {
        "source_id": "source-{0}".format(suffix),
        "origin": "synthetic-origin-{0}".format(suffix),
        "declared_kind": declared_kind,
        "hash": "a" * 16 + "-{0}".format(suffix),
        "byte_length": 2048,
        "observed_at": "2026-05-20T00:00:00Z",
    }


def _bare_source_record(suffix="001", declared_kind="prompt_collection"):
    return {
        "source_id": "source-{0}".format(suffix),
        "source_kind": declared_kind,
        "source_origin": "external",
        "source_register_ref": "source-{0}".format(suffix),
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


class SmokePackageCleanPassTest(unittest.TestCase):
    def test_clean_pass_with_empty_inputs(self):
        log = EventLog()
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT, [], [], log
        )
        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 20)
        self.assertEqual(
            output["package_kind"], "scaffold_source_intake_smoke_package"
        )
        self.assertEqual(output["source_reference_count"], 0)
        self.assertEqual(output["source_record_count"], 0)
        self.assertEqual(output["linked_source_count"], 0)
        self.assertEqual(output["trace_candidate_route_fragment_count"], 0)
        self.assertEqual(output["trace_candidate_workflow_fragment_count"], 0)
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        self.assertFalse(log.has_halt())

    def test_clean_pass_with_one_inert_reference_and_one_bare_source(self):
        log = EventLog()
        refs = [_reference("001", "prompt_collection")]
        sources = [_bare_source_record("001", "prompt_collection")]
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT, refs, sources, log
        )

        self.assertEqual(output["source_reference_count"], 1)
        self.assertEqual(output["source_record_count"], 1)
        self.assertEqual(output["linked_source_count"], 1)
        # bare source record carries no derived material -> trace fragment counts stay 0
        self.assertEqual(output["trace_candidate_route_fragment_count"], 0)
        self.assertEqual(output["trace_candidate_workflow_fragment_count"], 0)
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        self.assertFalse(log.has_halt())

    def test_all_authorization_readiness_selection_booleans_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT, [], [], log
        )
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "extraction_authorized",
            "normalization_authorized",
            "candidate_derivation_authorized",
        ):
            self.assertIs(output[key], False)

    def test_package_note_disclaims_qualification_admission_selection_readiness(self):
        log = EventLog()
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT, [], [], log
        )
        note = output["package_note"]
        self.assertIn("NOT source qualification", note)
        self.assertIn("NOT corpus admission", note)
        self.assertIn("NOT route selection", note)
        self.assertIn("NOT benchmark readiness", note)
        # "architecture selection" is a forbidden substring; the note must
        # convey the same meaning via different phrasing.
        self.assertNotIn("architecture selection", note)

    def test_input_prompt_observed_is_structural_only(self):
        log = EventLog()
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT, [], [], log
        )
        observed = output["input_prompt_observed"]
        self.assertIsInstance(observed, dict)
        self.assertIs(observed["observed"], True)
        self.assertEqual(
            observed["captured_intent_text_length"], len(_PROMPT)
        )
        rendered = json.dumps(output, sort_keys=True)
        self.assertNotIn(_PROMPT, rendered)

    def test_register_bridge_trace_observations_embedded(self):
        log = EventLog()
        refs = [_reference("001"), _reference("002")]
        sources = [
            _bare_source_record("001"),
            _bare_source_record("002"),
        ]
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT, refs, sources, log
        )
        self.assertEqual(
            output["register_observation"]["register_kind"],
            "scaffold_source_intake_register",
        )
        self.assertEqual(
            output["bridge_observation"]["bridge_kind"],
            "scaffold_source_trace_admission_bridge",
        )
        self.assertEqual(
            output["trace_observation"]["trace_kind"],
            "scaffold_source_intake_trace",
        )

    def test_passed_event_records_clean_counts(self):
        log = EventLog()
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT, [_reference("001")], [_bare_source_record("001")], log
        )
        passed = [
            e
            for e in log.events
            if e["type"] == "scaffold_source_intake_smoke_package_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["corpus_admitted_count"], 0)
        self.assertEqual(passed[0]["qualified_count"], 0)
        self.assertEqual(passed[0]["linked_source_count"], 1)


class SmokePackageStageOrderTest(unittest.TestCase):
    """Verify the strict register -> bridge -> trace call order using
    `unittest.mock.patch` to replace the bound names INSIDE the smoke
    package module, without modifying the original modules."""

    _MODULE = "harness.scaffold_source_intake_smoke_package"

    def _stub_register(self, calls, output):
        def _stub(source_reference_records, event_log):
            calls.append(("register", source_reference_records))
            return output
        return _stub

    def _stub_bridge(self, calls, output):
        def _stub(register_observation, source_records, event_log):
            calls.append(
                ("bridge", register_observation.get("register_kind"))
            )
            return output
        return _stub

    def _stub_trace(self, calls, output):
        def _stub(input_prompt, source_records, event_log):
            calls.append(("trace", input_prompt[:8]))
            return output
        return _stub

    def _register_output(self):
        return {
            "register_kind": "scaffold_source_intake_register",
            "references_observed_count": 0,
            "unique_origin_count": 0,
            "register_entries": [],
            "corpus_admitted_count": 0,
            "qualified_count": 0,
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
            "intake_note": "stub register observation for ordering test",
        }

    def _bridge_output(self):
        return {
            "bridge_kind": "scaffold_source_trace_admission_bridge",
            "register_entry_count": 0,
            "source_records_checked_count": 0,
            "linked_source_count": 0,
            "linked_sources": [],
            "corpus_admitted_count": 0,
            "qualified_count": 0,
            "extraction_authorized": False,
            "normalization_authorized": False,
            "candidate_derivation_authorized": False,
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
            "bridge_note": "stub bridge observation for ordering test",
        }

    def _trace_output(self):
        return {
            "trace_kind": "scaffold_source_intake_trace",
            "input_prompt_observed": {
                "observed": True,
                "captured_intent_text_length": len(_PROMPT),
            },
            "normalized_intent_observation": {
                "prompt_length": len(_PROMPT),
                "sources_with_normalized_material": 0,
            },
            "sources_touched_count": 0,
            "qualified_sources_count": 0,
            "normalized_material_refs": [],
            "candidate_route_fragments": [],
            "candidate_workflow_fragments": [],
            "rejected_source_count": 0,
            "rejection_reasons": [],
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
            "trace_note": "stub trace observation for ordering test",
        }

    def test_register_then_bridge_then_trace_called_in_order(self):
        calls = []
        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_register",
            new=self._stub_register(calls, self._register_output()),
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_trace_admission_bridge",
            new=self._stub_bridge(calls, self._bridge_output()),
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_intake_trace",
            new=self._stub_trace(calls, self._trace_output()),
        ):
            run_scaffold_source_intake_smoke_package(
                _PROMPT, [], [], EventLog()
            )
        self.assertEqual([c[0] for c in calls], ["register", "bridge", "trace"])

    def test_register_failure_prevents_bridge_and_trace(self):
        calls = []

        def _failing_register(source_reference_records, event_log):
            calls.append("register")
            raise RuntimeError("synthetic register failure")

        def _bridge_should_not_run(register_observation, source_records, event_log):
            calls.append("bridge")
            return self._bridge_output()

        def _trace_should_not_run(input_prompt, source_records, event_log):
            calls.append("trace")
            return self._trace_output()

        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_register",
            new=_failing_register,
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_trace_admission_bridge",
            new=_bridge_should_not_run,
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_intake_trace",
            new=_trace_should_not_run,
        ):
            with self.assertRaises(RuntimeError):
                run_scaffold_source_intake_smoke_package(
                    _PROMPT, [], [], EventLog()
                )
        self.assertEqual(calls, ["register"])

    def test_bridge_failure_prevents_trace(self):
        calls = []

        def _register_ok(source_reference_records, event_log):
            calls.append("register")
            return self._register_output()

        def _failing_bridge(register_observation, source_records, event_log):
            calls.append("bridge")
            raise RuntimeError("synthetic bridge failure")

        def _trace_should_not_run(input_prompt, source_records, event_log):
            calls.append("trace")
            return self._trace_output()

        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_register",
            new=_register_ok,
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_trace_admission_bridge",
            new=_failing_bridge,
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_intake_trace",
            new=_trace_should_not_run,
        ):
            with self.assertRaises(RuntimeError):
                run_scaffold_source_intake_smoke_package(
                    _PROMPT, [], [], EventLog()
                )
        self.assertEqual(calls, ["register", "bridge"])

    def test_trace_failure_propagates(self):
        calls = []

        def _register_ok(source_reference_records, event_log):
            calls.append("register")
            return self._register_output()

        def _bridge_ok(register_observation, source_records, event_log):
            calls.append("bridge")
            return self._bridge_output()

        def _failing_trace(input_prompt, source_records, event_log):
            calls.append("trace")
            raise RuntimeError("synthetic trace failure")

        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_register",
            new=_register_ok,
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_trace_admission_bridge",
            new=_bridge_ok,
        ), mock.patch(
            self._MODULE + ".run_scaffold_source_intake_trace",
            new=_failing_trace,
        ):
            with self.assertRaises(RuntimeError):
                run_scaffold_source_intake_smoke_package(
                    _PROMPT, [], [], EventLog()
                )
        self.assertEqual(calls, ["register", "bridge", "trace"])


class SmokePackageRealFailureTest(unittest.TestCase):
    """Without stubs, real WO-55 / WO-56 / WO-54 rejections propagate."""

    def test_real_register_failure_propagates_without_swallowing(self):
        log = EventLog()
        with self.assertRaises(Exception):
            run_scaffold_source_intake_smoke_package(
                _PROMPT, "not a list", [], log
            )
        # event log should contain a register-side halt and NOT a
        # smoke-package-passed event.
        types = [e["type"] for e in log.events]
        self.assertNotIn("scaffold_source_intake_smoke_package_passed", types)

    def test_real_bridge_failure_propagates_without_swallowing(self):
        # register succeeds (empty list), bridge fails because source_records is non-list
        log = EventLog()
        with self.assertRaises(Exception):
            run_scaffold_source_intake_smoke_package(
                _PROMPT, [], "not a list", log
            )
        types = [e["type"] for e in log.events]
        self.assertIn(
            "scaffold_source_intake_smoke_package_register_completed", types
        )
        self.assertNotIn("scaffold_source_intake_smoke_package_passed", types)

    def test_real_trace_failure_propagates_without_swallowing(self):
        # register and bridge succeed (both with empty inputs); trace fails
        # because input_prompt is empty
        log = EventLog()
        with self.assertRaises(Exception):
            run_scaffold_source_intake_smoke_package("", [], [], log)
        types = [e["type"] for e in log.events]
        # input_prompt is rejected by WO-54 (empty string), AFTER register
        # and bridge succeed.
        self.assertIn(
            "scaffold_source_intake_smoke_package_register_completed", types
        )
        self.assertIn(
            "scaffold_source_intake_smoke_package_bridge_completed", types
        )
        self.assertNotIn(
            "scaffold_source_intake_smoke_package_trace_completed", types
        )
        self.assertNotIn("scaffold_source_intake_smoke_package_passed", types)


class SmokePackageLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_source_intake_smoke_package(
            _PROMPT,
            [_reference("001"), _reference("002")],
            [_bare_source_record("001"), _bare_source_record("002")],
            log,
        )
        forbidden = PACKAGE_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)


class SmokePackageIsolationTest(unittest.TestCase):
    def test_does_not_mutate_inputs(self):
        prompt = _PROMPT
        refs = [_reference("001"), _reference("002")]
        sources = [_bare_source_record("001"), _bare_source_record("002")]
        before_refs = copy.deepcopy(refs)
        before_sources = copy.deepcopy(sources)
        run_scaffold_source_intake_smoke_package(
            prompt, refs, sources, EventLog()
        )
        self.assertEqual(refs, before_refs)
        self.assertEqual(sources, before_sources)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_source_intake_smoke_package(
                    _PROMPT, [], [], EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class SmokePackageImportSurfaceTest(unittest.TestCase):
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
                "unexpected import in smoke package: {0}".format(module_name),
            )

    def test_module_makes_no_file_io_network_or_hash_call(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for forbidden_token in (
            "open(",
            "pathlib",
            "urllib",
            "requests",
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
                forbidden_token,
                source_text,
                "unexpected IO / network / hash token in smoke package: "
                "{0}".format(forbidden_token),
            )

    def test_module_does_not_use_retrieval_or_search_or_score_verbs(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in (
            "def query",
            "def search",
            "def retrieve",
            "def rank",
            "score",
            "scoring",
        ):
            self.assertNotIn(
                token,
                source_text,
                "unexpected retrieval/search/score token in smoke "
                "package: {0}".format(token),
            )


class SmokePackageFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_package(self):
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
        run_scaffold_source_intake_smoke_package(
            _PROMPT,
            [_reference("001"), _reference("002")],
            [_bare_source_record("001"), _bare_source_record("002")],
            EventLog(),
        )
        after = inventory()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
