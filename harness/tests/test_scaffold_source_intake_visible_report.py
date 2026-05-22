"""Tests for the WO-59 scaffold visible source-intake flow report.

The tests exercise the composed read-only review observation that
chains the WO-57 smoke package and the WO-58 diagnostic reporter.
The same boundary as WO-50 through WO-58 applies: no real retrieval
call, no adapter invocation, no network call, no file IO inside the
module, no hash computation, no metrics, no ranking, no architecture
choice, no model judgment, and no benchmark readiness change. The
visible report does not derive candidate fragments of its own;
fragment counts are copied verbatim from the embedded WO-57 package
observation.
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
from harness.scaffold_source_intake_visible_report import (
    ALLOWED_OUTPUT_KEYS,
    ForbiddenLanguageInVisibleSourceIntakeReport,
    VISIBLE_REPORT_OUTPUT_FORBIDDEN_PHRASES,
    run_scaffold_source_intake_visible_report,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT, "harness", "scaffold_source_intake_visible_report.py"
)


_PROMPT = (
    "How does the synthetic WO-59 visible report handle a captured "
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


def _last_halt_event(event_log):
    for event in reversed(event_log.events):
        if event["type"] == "halt":
            return event
    return None


class VisibleReportCleanPassTest(unittest.TestCase):
    def test_clean_pass_with_empty_inputs(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT, [], [], log
        )
        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 17)
        self.assertEqual(
            output["visible_report_kind"],
            "scaffold_source_intake_visible_report",
        )
        self.assertEqual(output["source_reference_count"], 0)
        self.assertEqual(output["source_record_count"], 0)
        self.assertEqual(output["linked_source_count"], 0)
        self.assertEqual(output["trace_candidate_route_fragment_count"], 0)
        self.assertEqual(output["trace_candidate_workflow_fragment_count"], 0)

    def test_clean_pass_with_one_reference_and_matching_bare_source(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT,
            [_reference("001", "prompt_collection")],
            [_bare_source_record("001", "prompt_collection")],
            log,
        )
        self.assertEqual(output["source_reference_count"], 1)
        self.assertEqual(output["source_record_count"], 1)
        self.assertEqual(output["linked_source_count"], 1)
        # bare source -> no derived material -> trace fragment counts 0
        self.assertEqual(output["trace_candidate_route_fragment_count"], 0)
        self.assertEqual(output["trace_candidate_workflow_fragment_count"], 0)

    def test_standard_authorization_booleans_remain_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT, [], [], log
        )
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
        ):
            self.assertIs(output[key], False)

    def test_review_halt_required_false_when_no_halt_diagnostics(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT, [], [], log
        )
        self.assertEqual(output["diagnostic_halt_required_count"], 0)
        self.assertIs(output["review_halt_required"], False)

    def test_package_observation_embedded_verbatim(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT,
            [_reference("001")],
            [_bare_source_record("001")],
            log,
        )
        self.assertEqual(
            output["package_observation"]["package_kind"],
            "scaffold_source_intake_smoke_package",
        )

    def test_diagnostic_report_embedded_verbatim(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT,
            [_reference("001")],
            [_bare_source_record("001")],
            log,
        )
        self.assertEqual(
            output["diagnostic_report"]["reporter_kind"],
            "scaffold_route_invariant_diagnostic_reporter",
        )

    def test_input_prompt_observed_is_structural_only(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT, [], [], log
        )
        observed = output["input_prompt_observed"]
        self.assertIsInstance(observed, dict)
        self.assertIs(observed["observed"], True)
        self.assertEqual(
            observed["captured_intent_text_length"], len(_PROMPT)
        )
        # Top-level keys should not echo the raw prompt text.
        for top_key in (
            "visible_report_kind",
            "visible_report_note",
        ):
            self.assertNotIn(_PROMPT, output[top_key])

    def test_candidate_counts_copied_from_package_observation(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT,
            [_reference("001")],
            [_bare_source_record("001")],
            log,
        )
        self.assertEqual(
            output["trace_candidate_route_fragment_count"],
            output["package_observation"][
                "trace_candidate_route_fragment_count"
            ],
        )
        self.assertEqual(
            output["trace_candidate_workflow_fragment_count"],
            output["package_observation"][
                "trace_candidate_workflow_fragment_count"
            ],
        )

    def test_passed_event_recorded(self):
        log = EventLog()
        run_scaffold_source_intake_visible_report(_PROMPT, [], [], log)
        passed = [
            e
            for e in log.events
            if e["type"] == "scaffold_source_intake_visible_report_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertIs(passed[0]["review_halt_required"], False)


class VisibleReportOrderingTest(unittest.TestCase):
    """Verify the strict package -> diagnostics call order using
    `unittest.mock.patch` to replace the bound names INSIDE the
    visible report module, without modifying the original modules."""

    _MODULE = "harness.scaffold_source_intake_visible_report"

    def _stub_package_output(self):
        return {
            "package_kind": "scaffold_source_intake_smoke_package",
            "input_prompt_observed": {
                "observed": True,
                "captured_intent_text_length": len(_PROMPT),
            },
            "register_observation": {
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
                "intake_note": "stub register",
            },
            "bridge_observation": {
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
                "bridge_note": "stub bridge",
            },
            "trace_observation": {
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
                "trace_note": "stub trace",
            },
            "source_reference_count": 0,
            "source_record_count": 0,
            "linked_source_count": 0,
            "trace_candidate_route_fragment_count": 0,
            "trace_candidate_workflow_fragment_count": 0,
            "corpus_admitted_count": 0,
            "qualified_count": 0,
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
            "extraction_authorized": False,
            "normalization_authorized": False,
            "candidate_derivation_authorized": False,
            "package_note": "stub package",
        }

    def _stub_diagnostic_output(self):
        return {
            "reporter_kind": "scaffold_route_invariant_diagnostic_reporter",
            "observations_checked_count": 1,
            "diagnostics_count": 0,
            "error_count": 0,
            "warning_count": 0,
            "info_count": 0,
            "halt_required_count": 0,
            "diagnostics": [],
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
            "reporter_note": "stub reporter",
        }

    def test_package_called_before_diagnostics(self):
        calls = []

        def _package_stub(prompt, refs, records, event_log):
            calls.append("package")
            return self._stub_package_output()

        def _diagnostic_stub(observations, event_log):
            calls.append("diagnostics")
            return self._stub_diagnostic_output()

        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_smoke_package",
            new=_package_stub,
        ), mock.patch(
            self._MODULE
            + ".run_scaffold_route_invariant_diagnostic_reporter",
            new=_diagnostic_stub,
        ):
            run_scaffold_source_intake_visible_report(
                _PROMPT, [], [], EventLog()
            )
        self.assertEqual(calls, ["package", "diagnostics"])

    def test_package_failure_prevents_diagnostics(self):
        calls = []

        def _failing_package(prompt, refs, records, event_log):
            calls.append("package")
            raise RuntimeError("synthetic package failure")

        def _diagnostic_should_not_run(observations, event_log):
            calls.append("diagnostics")
            return self._stub_diagnostic_output()

        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_smoke_package",
            new=_failing_package,
        ), mock.patch(
            self._MODULE
            + ".run_scaffold_route_invariant_diagnostic_reporter",
            new=_diagnostic_should_not_run,
        ):
            with self.assertRaises(RuntimeError):
                run_scaffold_source_intake_visible_report(
                    _PROMPT, [], [], EventLog()
                )
        self.assertEqual(calls, ["package"])

    def test_diagnostic_failure_propagates(self):
        calls = []

        def _package_ok(prompt, refs, records, event_log):
            calls.append("package")
            return self._stub_package_output()

        def _failing_diagnostic(observations, event_log):
            calls.append("diagnostics")
            raise RuntimeError("synthetic diagnostic failure")

        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_smoke_package",
            new=_package_ok,
        ), mock.patch(
            self._MODULE
            + ".run_scaffold_route_invariant_diagnostic_reporter",
            new=_failing_diagnostic,
        ):
            with self.assertRaises(RuntimeError):
                run_scaffold_source_intake_visible_report(
                    _PROMPT, [], [], EventLog()
                )
        self.assertEqual(calls, ["package", "diagnostics"])

    def test_review_halt_required_true_when_diagnostic_report_flags_halt(self):
        def _package_ok(prompt, refs, records, event_log):
            return self._stub_package_output()

        def _diagnostic_with_halt(observations, event_log):
            output = self._stub_diagnostic_output()
            output["diagnostics_count"] = 1
            output["error_count"] = 1
            output["halt_required_count"] = 1
            output["diagnostics"] = [
                {
                    "diagnostic_id": "diag-000001",
                    "category": "authorization_boolean_true",
                    "severity": "error",
                    "target_observation_kind": "synthetic",
                    "target_path": "selection_made",
                    "invariant_ref": "synthetic invariant",
                    "message": "synthetic halt-required diagnostic for test",
                    "halt_required": True,
                }
            ]
            return output

        with mock.patch(
            self._MODULE + ".run_scaffold_source_intake_smoke_package",
            new=_package_ok,
        ), mock.patch(
            self._MODULE
            + ".run_scaffold_route_invariant_diagnostic_reporter",
            new=_diagnostic_with_halt,
        ):
            log = EventLog()
            output = run_scaffold_source_intake_visible_report(
                _PROMPT, [], [], log
            )
        self.assertIs(output["review_halt_required"], True)
        self.assertEqual(output["diagnostic_halt_required_count"], 1)
        # Reporter's authorization booleans still literal False.
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
        ):
            self.assertIs(output[key], False)


class VisibleReportRealFailureTest(unittest.TestCase):
    def test_real_package_failure_propagates_without_swallowing(self):
        log = EventLog()
        with self.assertRaises(Exception):
            run_scaffold_source_intake_visible_report(
                _PROMPT, "not a list", [], log
            )
        types = [e["type"] for e in log.events]
        self.assertNotIn(
            "scaffold_source_intake_visible_report_package_completed", types
        )
        self.assertNotIn(
            "scaffold_source_intake_visible_report_passed", types
        )


class VisibleReportLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_source_intake_visible_report(
            _PROMPT,
            [_reference("001")],
            [_bare_source_record("001")],
            log,
        )
        forbidden = (
            VISIBLE_REPORT_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        )
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)


class VisibleReportIsolationTest(unittest.TestCase):
    def test_does_not_mutate_inputs(self):
        refs = [_reference("001")]
        sources = [_bare_source_record("001")]
        before_refs = copy.deepcopy(refs)
        before_sources = copy.deepcopy(sources)
        run_scaffold_source_intake_visible_report(
            _PROMPT, refs, sources, EventLog()
        )
        self.assertEqual(refs, before_refs)
        self.assertEqual(sources, before_sources)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_source_intake_visible_report(
                    _PROMPT, [], [], EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class VisibleReportImportSurfaceTest(unittest.TestCase):
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
                "unexpected import in visible report: {0}".format(module_name),
            )

    def test_module_makes_no_file_io_network_or_hash_call(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in (
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
                token,
                source_text,
                "unexpected IO / network / hash token in visible report: "
                "{0}".format(token),
            )

    def test_module_does_not_use_retrieval_or_search_verbs(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in ("def query", "def search", "def retrieve", "def rank"):
            self.assertNotIn(
                token,
                source_text,
                "unexpected retrieval/search verb in visible report: "
                "{0}".format(token),
            )

    def test_module_does_not_directly_invoke_wo54_wo55_wo56_public_functions(
        self,
    ):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for forbidden_invocation in (
            "run_scaffold_source_intake_trace",
            "run_scaffold_source_intake_register",
            "run_scaffold_source_trace_admission_bridge",
        ):
            self.assertNotIn(
                forbidden_invocation,
                source_text,
                "visible report must not directly invoke WO-54 / WO-55 / "
                "WO-56 public function: {0}".format(forbidden_invocation),
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
                "unexpected external-integration token in visible report: "
                "{0}".format(token),
            )


class VisibleReportFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_report(self):
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
        run_scaffold_source_intake_visible_report(
            _PROMPT,
            [_reference("001")],
            [_bare_source_record("001")],
            EventLog(),
        )
        after = inventory()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
