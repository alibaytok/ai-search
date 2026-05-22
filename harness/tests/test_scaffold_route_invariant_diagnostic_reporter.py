"""Tests for the WO-58 scaffold route-invariant diagnostic reporter.

The tests exercise the deterministic, structural-only diagnostic
inspection of already-loaded scaffold observation dicts. The same
boundary as WO-50 through WO-57 applies: no real retrieval call, no
adapter invocation, no network call, no file IO inside the module,
no hash computation, no metrics, no ranking, no architecture choice,
no model judgment, no fuzzy semantic analysis, and no benchmark
readiness change. Diagnostics are review evidence only; an
authorization / readiness / selection boolean inside a diagnostic
record does NOT flip the reporter's own output booleans.
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
from harness.scaffold_route_invariant_diagnostic_reporter import (
    ALLOWED_OUTPUT_KEYS,
    ALLOWED_SEVERITIES,
    ARCHITECTURE_SELECTION_FIELDS,
    DIAGNOSTIC_CATEGORIES,
    ForbiddenLanguageInRouteInvariantDiagnostics,
    MissingObservationKind,
    NonListDiagnosticObservations,
    NonObjectDiagnosticObservation,
    REPORTER_OUTPUT_FORBIDDEN_PHRASES,
    ROUTE_STATUS_FIELDS,
    run_scaffold_route_invariant_diagnostic_reporter,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT, "harness", "scaffold_route_invariant_diagnostic_reporter.py"
)


def _wo57_like_observation():
    return {
        "observation_kind": "scaffold_source_intake_smoke_package",
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
        "package_note": (
            "scaffold smoke package note: this is not corpus admission, "
            "this is not source qualification, this is not route "
            "selection, this is not benchmark readiness"
        ),
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


class ReporterCleanPassTest(unittest.TestCase):
    def test_empty_observations_returns_zero_diagnostics(self):
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter([], log)
        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 13)
        self.assertEqual(output["observations_checked_count"], 0)
        self.assertEqual(output["diagnostics_count"], 0)
        self.assertEqual(output["error_count"], 0)
        self.assertEqual(output["warning_count"], 0)
        self.assertEqual(output["info_count"], 0)
        self.assertEqual(output["halt_required_count"], 0)
        self.assertEqual(output["diagnostics"], [])
        self.assertFalse(log.has_halt())

    def test_clean_wo57_like_observation_no_error_diagnostics(self):
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [_wo57_like_observation()], log
        )
        self.assertEqual(output["observations_checked_count"], 1)
        self.assertEqual(output["error_count"], 0)
        self.assertEqual(output["halt_required_count"], 0)
        # All four reporter output booleans literal False regardless.
        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)
        self.assertFalse(log.has_halt())

    def test_all_authorization_booleans_remain_literal_false(self):
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [_wo57_like_observation()], log
        )
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
        ):
            self.assertIs(output[key], False)

    def test_reporter_note_disclaims_validation_qualification_admission(self):
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [_wo57_like_observation()], log
        )
        note = output["reporter_note"]
        self.assertIn("NOT validate routes", note)
        self.assertIn("NOT", note)
        self.assertIn("qualify sources", note)
        self.assertIn("admit corpus", note)

    def test_passed_event_records_counts(self):
        log = EventLog()
        run_scaffold_route_invariant_diagnostic_reporter(
            [_wo57_like_observation()], log
        )
        passed = [
            e
            for e in log.events
            if e["type"]
            == "scaffold_route_invariant_diagnostic_reporter_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["observations_checked_count"], 1)


class ReporterAdvisoryDiagnosticTest(unittest.TestCase):
    """An error diagnostic with halt_required: True is advisory.
    The reporter does NOT raise on it, and its own booleans stay
    literal False."""

    def test_selection_made_true_produces_error_but_no_raise(self):
        observation = _wo57_like_observation()
        observation["selection_made"] = True
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        self.assertGreaterEqual(output["error_count"], 1)
        self.assertGreaterEqual(output["halt_required_count"], 1)
        # Reporter output booleans STILL literal False.
        self.assertIs(output["selection_made"], False)
        self.assertFalse(log.has_halt())

    def test_measurement_authorized_true_produces_error(self):
        observation = _wo57_like_observation()
        observation["measurement_authorized"] = True
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("authorization_boolean_true", categories)
        self.assertIs(output["measurement_authorized"], False)

    def test_real_benchmark_ready_true_produces_benchmark_readiness_diagnostic(
        self,
    ):
        observation = _wo57_like_observation()
        observation["real_benchmark_ready"] = True
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("benchmark_readiness_claim", categories)
        self.assertIs(output["real_benchmark_ready"], False)

    def test_real_benchmark_authorized_true_produces_error(self):
        observation = _wo57_like_observation()
        observation["real_benchmark_authorized"] = True
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("authorization_boolean_true", categories)

    def test_corpus_admitted_count_nonzero_produces_admission_diagnostic(self):
        observation = _wo57_like_observation()
        observation["corpus_admitted_count"] = 3
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("admission_or_qualification_count_nonzero", categories)

    def test_qualified_count_nonzero_produces_qualification_diagnostic(self):
        observation = _wo57_like_observation()
        observation["qualified_count"] = 2
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("admission_or_qualification_count_nonzero", categories)

    def test_route_field_produces_route_status_and_route_first_diagnostics(self):
        observation = _wo57_like_observation()
        observation["route_id"] = "synthetic-route-001"
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("route_status_claim", categories)
        self.assertIn("route_first_violation", categories)

    def test_each_route_status_field_individually_produces_diagnostic(self):
        for field in ROUTE_STATUS_FIELDS:
            observation = _wo57_like_observation()
            observation[field] = "synthetic-value"
            log = EventLog()
            output = run_scaffold_route_invariant_diagnostic_reporter(
                [observation], log
            )
            categories = [d["category"] for d in output["diagnostics"]]
            self.assertIn(
                "route_status_claim",
                categories,
                "route_status_claim missing for field {0!r}".format(field),
            )

    def test_architecture_selection_field_produces_architecture_diagnostic(self):
        observation = _wo57_like_observation()
        observation["index_family"] = "synthetic-family"
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("architecture_selection_claim", categories)

    def test_architecture_selection_value_produces_architecture_diagnostic(self):
        observation = _wo57_like_observation()
        observation["claim_marker"] = "selected_architecture"
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("architecture_selection_claim", categories)
        rendered = json.dumps(output, sort_keys=True)
        self.assertNotIn("selected_architecture", rendered)

    def test_each_architecture_selection_field_individually(self):
        for field in ARCHITECTURE_SELECTION_FIELDS:
            if field == "reranker":
                continue
            observation = _wo57_like_observation()
            observation[field] = "synthetic-value"
            log = EventLog()
            output = run_scaffold_route_invariant_diagnostic_reporter(
                [observation], log
            )
            categories = [d["category"] for d in output["diagnostics"]]
            self.assertIn(
                "architecture_selection_claim",
                categories,
                "architecture_selection_claim missing for {0!r}".format(field),
            )

    def test_reranker_field_halts_as_forbidden_language(self):
        observation = _wo57_like_observation()
        observation["reranker"] = "synthetic-value"
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInRouteInvariantDiagnostics):
            run_scaffold_route_invariant_diagnostic_reporter(
                [observation], log
            )
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_route_invariant_diagnostic_reporter_forbidden_language",
            )
        )

    def test_per_entry_qualified_true_produces_quarantine_diagnostic(self):
        observation = {
            "observation_kind": "scaffold_source_intake_register",
            "register_entries": [
                {
                    "source_id": "source-001",
                    "qualified": True,
                    "corpus_admitted": False,
                }
            ],
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
        }
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("source_quarantine_violation", categories)

    def test_per_entry_corpus_admitted_true_produces_quarantine_diagnostic(self):
        observation = {
            "observation_kind": "scaffold_source_intake_register",
            "register_entries": [
                {
                    "source_id": "source-001",
                    "qualified": False,
                    "corpus_admitted": True,
                }
            ],
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
        }
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("source_quarantine_violation", categories)

    def test_extraction_authorized_true_produces_authorization_diagnostic(self):
        observation = _wo57_like_observation()
        observation["extraction_authorized"] = True
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("authorization_boolean_true", categories)


class ReporterDiagnosticShapeTest(unittest.TestCase):
    def test_diagnostic_has_required_fields(self):
        observation = _wo57_like_observation()
        observation["selection_made"] = True
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        for diagnostic in output["diagnostics"]:
            self.assertEqual(
                set(diagnostic.keys()),
                {
                    "diagnostic_id",
                    "category",
                    "severity",
                    "target_observation_kind",
                    "target_path",
                    "invariant_ref",
                    "message",
                    "halt_required",
                },
            )

    def test_diagnostic_severity_in_allowed_set(self):
        observation = _wo57_like_observation()
        observation["selection_made"] = True
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        for diagnostic in output["diagnostics"]:
            self.assertIn(diagnostic["severity"], ALLOWED_SEVERITIES)

    def test_diagnostic_category_in_allowed_set(self):
        observation = _wo57_like_observation()
        observation["selection_made"] = True
        observation["route_id"] = "x"
        observation["index_family"] = "x"
        observation["corpus_admitted_count"] = 1
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        for diagnostic in output["diagnostics"]:
            self.assertIn(diagnostic["category"], DIAGNOSTIC_CATEGORIES)

    def test_unknown_observation_kind_produces_info_diagnostic(self):
        observation = {
            "observation_kind": "synthetic-unknown-layer",
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
        }
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [observation], log
        )
        categories = [d["category"] for d in output["diagnostics"]]
        self.assertIn("diagnostic_input_shape", categories)


class ReporterInputRejectionTest(unittest.TestCase):
    def test_non_list_observations_rejected(self):
        log = EventLog()
        with self.assertRaises(NonListDiagnosticObservations):
            run_scaffold_route_invariant_diagnostic_reporter("not a list", log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_route_invariant_diagnostic_reporter_non_list_observations",
            )
        )

    def test_non_dict_observation_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectDiagnosticObservation):
            run_scaffold_route_invariant_diagnostic_reporter(
                ["not a dict"], log
            )
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_route_invariant_diagnostic_reporter_non_object_observation",
            )
        )

    def test_missing_observation_kind_rejected(self):
        log = EventLog()
        with self.assertRaises(MissingObservationKind):
            run_scaffold_route_invariant_diagnostic_reporter([{}], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_route_invariant_diagnostic_reporter_missing_observation_kind",
            )
        )

    def test_empty_observation_kind_rejected(self):
        log = EventLog()
        with self.assertRaises(MissingObservationKind):
            run_scaffold_route_invariant_diagnostic_reporter(
                [{"observation_kind": ""}], log
            )


class ReporterForbiddenLanguageTest(unittest.TestCase):
    def test_forbidden_language_in_observation_string_propagates_halt(self):
        observation = _wo57_like_observation()
        observation["leaked_text"] = "this content contains validation evidence"
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInRouteInvariantDiagnostics):
            run_scaffold_route_invariant_diagnostic_reporter([observation], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_route_invariant_diagnostic_reporter_forbidden_language",
            )
        )

    def test_reporter_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_route_invariant_diagnostic_reporter(
            [_wo57_like_observation()], log
        )
        forbidden = REPORTER_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)


class ReporterIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_inputs(self):
        observations = [_wo57_like_observation(), _wo57_like_observation()]
        observations[0]["selection_made"] = True
        before = copy.deepcopy(observations)
        run_scaffold_route_invariant_diagnostic_reporter(
            observations, EventLog()
        )
        self.assertEqual(observations, before)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_route_invariant_diagnostic_reporter(
                    [_wo57_like_observation()], EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class ReporterImportSurfaceTest(unittest.TestCase):
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
                "unexpected import in reporter: {0}".format(module_name),
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
                "unexpected IO / network / hash token in reporter: "
                "{0}".format(token),
            )

    def test_module_does_not_use_retrieval_or_search_verbs(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in ("def query", "def search", "def retrieve", "def rank"):
            self.assertNotIn(
                token,
                source_text,
                "unexpected retrieval/search verb in reporter: {0}".format(
                    token
                ),
            )

    def test_module_does_not_invoke_wo54_through_wo57_public_functions(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for func in (
            "run_scaffold_source_intake_trace",
            "run_scaffold_source_intake_register",
            "run_scaffold_source_trace_admission_bridge",
            "run_scaffold_source_intake_smoke_package",
        ):
            self.assertNotIn(
                func,
                source_text,
                "reporter must not reference {0}".format(func),
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
        ):
            self.assertNotIn(
                token,
                source_text,
                "unexpected external-integration token in reporter: "
                "{0}".format(token),
            )


class ReporterFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_reporter(self):
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
        run_scaffold_route_invariant_diagnostic_reporter(
            [_wo57_like_observation()], EventLog()
        )
        after = inventory()
        self.assertEqual(after, before)


class ReporterConstantsTest(unittest.TestCase):
    def test_allowed_output_keys_exactly_thirteen(self):
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 13)

    def test_diagnostic_categories_exactly_ten(self):
        self.assertEqual(len(DIAGNOSTIC_CATEGORIES), 10)
        for required_category in (
            "route_first_violation",
            "source_quarantine_violation",
            "route_status_claim",
            "benchmark_readiness_claim",
            "architecture_selection_claim",
            "authorization_boolean_true",
            "admission_or_qualification_count_nonzero",
            "missing_literal_false_authorization_boolean",
            "missing_non_claim_note",
            "diagnostic_input_shape",
        ):
            self.assertIn(required_category, DIAGNOSTIC_CATEGORIES)

    def test_allowed_severities_are_info_warning_error(self):
        self.assertEqual(set(ALLOWED_SEVERITIES), {"info", "warning", "error"})

    def test_route_status_fields_include_packet_required_markers(self):
        for required in (
            "route",
            "route_id",
            "route_state",
            "plane",
            "official",
            "executable",
            "selected_route",
            "production_route",
            "selected_as_official",
            "route_authorized",
            "official_route_authorized",
        ):
            self.assertIn(required, ROUTE_STATUS_FIELDS)


if __name__ == "__main__":
    unittest.main()
