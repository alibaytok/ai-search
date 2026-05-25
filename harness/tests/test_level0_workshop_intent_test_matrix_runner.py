"""Tests for `harness.level0_workshop_intent_test_matrix_runner`
(WO-L0-WORKSHOP-INTENT-TEST-MATRIX-RUNNER-01).

Tests load the committed smoke matrix from
`harness/intent_test_matrices/L0-WS-INTENT-MATRIX-SMOKE-001.intent.matrix.json`,
exercise every halt branch of the matrix loader / validator with
synthetic mutated copies, exercise the failure classifier with
synthetic mismatch fixtures for each emit-eligible class, prove the
reserved classes (`vocabulary_correction_miss`,
`ambiguity_clarification_gap`) are present in the bounded enum but
NOT emitted, prove `tolerated_variants` accepts alternative
orderings, and prove the static-scan and parser-isolation discipline.
"""

import copy
import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_canonical_intent_frame import (
    WORKSHOP_ITEM_KINDS,
    WORKSHOP_PROMPT_CATEGORIES,
)
from harness.level0_workshop_intent_test_matrix_runner import (
    ALLOWED_OUTPUT_KEYS,
    DuplicateCaseId,
    EmptyCases,
    EmptyPromptText,
    FAILURE_CLASSES,
    ForbiddenLanguageInLevel0WorkshopIntentTestMatrixRunner,
    GATING_BOOLEANS,
    INTENT_TEST_MATRIX_KIND,
    INTENT_TEST_MATRIX_RUNNER_KIND,
    IntentTestMatrixRunnerGatingBooleanFlipped,
    InvalidJSONMatrix,
    InvalidMatrixKind,
    MatrixFileNotFound,
    MissingCaseKey,
    MissingMatrixKey,
    NonBooleanAmbiguity,
    NonDictExpected,
    NonDictMatrix,
    NonListCases,
    NonListExpectedKinds,
    NonListTags,
    NonListToleratedVariants,
    NonObjectCase,
    NonObjectToleratedVariant,
    NonStringCaseId,
    NonStringMatrixId,
    NonStringMatrixNote,
    NonStringMatrixPath,
    NonStringPromptText,
    NonStringRationale,
    NonStringTag,
    RESERVED_FAILURE_CLASSES,
    UnknownCandidateSurface,
    UnknownCaseKey,
    UnknownCategory,
    UnknownExpectedKey,
    UnknownItemKind,
    UnknownMatrixKey,
    UnknownNormalizedIntent,
    UnknownRejectionSurface,
    run_intent_test_matrix,
)


_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(os.path.dirname(_THIS_DIR))
_SMOKE_MATRIX_PATH = os.path.join(
    _REPO_ROOT,
    "harness",
    "intent_test_matrices",
    "L0-WS-INTENT-MATRIX-SMOKE-001.intent.matrix.json",
)


_ROUTE_STATUS_FIELDS = (
    "official", "is_route", "is_official_route", "selected_as_official",
    "official_route_authorized", "route_authorized", "production_route",
    "selected_route", "executable", "route_state", "plane",
)


_FORBIDDEN_OUTPUT_FIELD_NAMES = (
    "ranking_performed",
    "scoring_performed",
    "confidence",
    "score",
    "distance",
    "best_match",
    "threshold",
    "similarity",
)


def _load_smoke_matrix_dict():
    with open(_SMOKE_MATRIX_PATH, "r", encoding="ascii") as handle:
        return json.loads(handle.read())


def _write_temp_matrix(matrix_dict):
    """Write `matrix_dict` to a temporary file and return the path.
    Caller is responsible for unlinking the path."""
    handle = tempfile.NamedTemporaryFile(
        mode="w", suffix=".intent.matrix.json", delete=False, encoding="ascii"
    )
    json.dump(matrix_dict, handle, ensure_ascii=True)
    handle.close()
    return handle.name


def _run_temp(matrix_dict):
    """Write `matrix_dict` to a temp file, run the runner, return the
    result (or raise). Cleans up the temp file."""
    path = _write_temp_matrix(matrix_dict)
    try:
        return run_intent_test_matrix(path, EventLog())
    finally:
        os.unlink(path)


def _expect_halt(test_case, matrix_dict, exception_cls):
    """Run the runner on `matrix_dict` and assert it raises
    `exception_cls` with a halt event recorded."""
    path = _write_temp_matrix(matrix_dict)
    try:
        event_log = EventLog()
        with test_case.assertRaises(exception_cls):
            run_intent_test_matrix(path, event_log)
        test_case.assertTrue(event_log.has_halt())
    finally:
        os.unlink(path)


class SmokeMatrixCleanPassTest(unittest.TestCase):
    """The committed smoke matrix passes end-to-end against the
    current FRAME-D shim."""

    def setUp(self):
        self.event_log = EventLog()
        self.result = run_intent_test_matrix(
            _SMOKE_MATRIX_PATH, self.event_log
        )

    def test_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))

    def test_runner_kind_literal(self):
        self.assertEqual(
            self.result["intent_test_matrix_runner_kind"],
            INTENT_TEST_MATRIX_RUNNER_KIND,
        )

    def test_matrix_id_mirrored(self):
        self.assertEqual(
            self.result["matrix_id"], "L0-WS-INTENT-MATRIX-SMOKE-001"
        )

    def test_case_count_is_15(self):
        self.assertEqual(self.result["case_count"], 15)

    def test_all_cases_passed(self):
        self.assertEqual(self.result["passed_count"], 15)
        self.assertEqual(self.result["failed_count"], 0)

    def test_every_case_result_has_required_fields(self):
        required = {
            "case_id", "match", "classified_as",
            "observed_category", "expected_category",
            "observed_kinds", "expected_kinds",
            "observed_ambiguity", "expected_ambiguity",
            "observed_normalized_intent", "expected_normalized_intent",
            "observed_candidate_surface", "expected_candidate_surface",
            "observed_rejection_surface", "expected_rejection_surface",
            "differing_fields", "tags", "rationale",
        }
        for cr in self.result["case_results"]:
            self.assertEqual(set(cr.keys()), required)

    def test_per_failure_class_counts_all_zero(self):
        for fc in FAILURE_CLASSES:
            self.assertEqual(self.result["per_failure_class_counts"][fc], 0)

    def test_per_tag_counts_present(self):
        self.assertIn("rk060_a", self.result["per_tag_counts"])
        self.assertIn("rk060_e", self.result["per_tag_counts"])
        self.assertIn("rk060_f", self.result["per_tag_counts"])
        self.assertIn("turkish_alias", self.result["per_tag_counts"])
        for tag, counts in self.result["per_tag_counts"].items():
            self.assertEqual(counts["failed"], 0)

    def test_runner_gating_booleans_all_literal_false(self):
        for key in GATING_BOOLEANS:
            self.assertIs(self.result[key], False)

    def test_runner_note_non_empty_string(self):
        self.assertIsInstance(self.result["runner_note"], str)
        self.assertGreater(len(self.result["runner_note"]), 0)

    def test_no_route_status_fields_in_result(self):
        for field in _ROUTE_STATUS_FIELDS:
            self.assertNotIn(field, self.result)

    def test_no_forbidden_output_field_names_in_result(self):
        for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
            self.assertNotIn(field, self.result)

    def test_no_route_status_fields_in_case_results(self):
        for cr in self.result["case_results"]:
            for field in _ROUTE_STATUS_FIELDS:
                self.assertNotIn(field, cr)

    def test_no_forbidden_output_field_names_in_case_results(self):
        for cr in self.result["case_results"]:
            for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
                self.assertNotIn(field, cr)

    def test_started_and_completed_events_emitted(self):
        types = [e["type"] for e in self.event_log.events]
        self.assertIn("intent_test_matrix_runner_started", types)
        self.assertIn("intent_test_matrix_runner_completed", types)

    def test_no_halt_event_on_clean_pass(self):
        self.assertFalse(self.event_log.has_halt())

    def test_kind_order_tolerated_variant_matches(self):
        kind_order_case = next(
            cr for cr in self.result["case_results"]
            if cr["case_id"] == "SM-014"
        )
        self.assertTrue(kind_order_case["match"])
        self.assertEqual(
            kind_order_case["observed_kinds"], ["workflow_file", "agent"]
        )
        self.assertEqual(
            kind_order_case["expected_kinds"], ["agent", "workflow_file"]
        )


class FailureClassEnumTest(unittest.TestCase):
    """The bounded failure class enum is exactly fourteen entries
    including the two RESERVED entries."""

    def test_failure_classes_count(self):
        self.assertEqual(len(FAILURE_CLASSES), 14)

    def test_failure_classes_set_size(self):
        self.assertEqual(len(set(FAILURE_CLASSES)), 14)

    def test_reserved_classes_present(self):
        self.assertIn("vocabulary_correction_miss", FAILURE_CLASSES)
        self.assertIn("ambiguity_clarification_gap", FAILURE_CLASSES)

    def test_reserved_classes_subset(self):
        self.assertEqual(
            RESERVED_FAILURE_CLASSES,
            frozenset({"vocabulary_correction_miss", "ambiguity_clarification_gap"}),
        )

    def test_unknown_class_present(self):
        self.assertIn("unknown", FAILURE_CLASSES)


def _build_minimal_matrix(case_overrides=None):
    """Build a single-case smoke-shaped matrix; case_overrides merges
    into the default case. Returns a fresh dict each call."""
    case = {
        "case_id": "X-001",
        "prompt_text": "Configure GitHub Actions to deploy a Node.js app to Azure.",
        "expected": {
            "category": "B. workflow intent",
            "expected_item_kinds_touched": ["workflow_file"],
            "ambiguity_observed": False,
            "normalized_intent_observation": "workflow_intent",
            "candidate_surface_expected": "candidate fragment of declared shape",
            "rejection_surface_expected": "no_forced_selection",
        },
        "tolerated_variants": [],
        "tags": ["synthetic"],
        "rationale": "synthetic minimal case for runner tests",
    }
    if case_overrides:
        case.update(case_overrides)
    return {
        "intent_test_matrix_kind": INTENT_TEST_MATRIX_KIND,
        "matrix_id": "X-MATRIX-001",
        "matrix_note": "synthetic minimal matrix used by the runner test suite; not a benchmark; not a corpus",
        "cases": [case],
    }


class MatrixLoaderHaltTest(unittest.TestCase):
    """Every malformed-matrix branch records a halt and raises the
    appropriate exception."""

    def test_non_string_matrix_path_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonStringMatrixPath):
            run_intent_test_matrix(42, event_log)
        self.assertTrue(event_log.has_halt())

    def test_missing_file_halts(self):
        event_log = EventLog()
        with self.assertRaises(MatrixFileNotFound):
            run_intent_test_matrix(
                os.path.join(_REPO_ROOT, "does_not_exist.json"), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_invalid_json_halts(self):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="ascii"
        )
        handle.write("not valid json {")
        handle.close()
        try:
            event_log = EventLog()
            with self.assertRaises(InvalidJSONMatrix):
                run_intent_test_matrix(handle.name, event_log)
            self.assertTrue(event_log.has_halt())
        finally:
            os.unlink(handle.name)

    def test_non_dict_matrix_halts(self):
        handle = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False, encoding="ascii"
        )
        json.dump(["not", "a", "dict"], handle)
        handle.close()
        try:
            event_log = EventLog()
            with self.assertRaises(NonDictMatrix):
                run_intent_test_matrix(handle.name, event_log)
            self.assertTrue(event_log.has_halt())
        finally:
            os.unlink(handle.name)

    def test_missing_matrix_key_halts(self):
        matrix = _build_minimal_matrix()
        del matrix["matrix_id"]
        _expect_halt(self, matrix, MissingMatrixKey)

    def test_unknown_matrix_key_halts(self):
        matrix = _build_minimal_matrix()
        matrix["extra_unknown_key"] = "junk"
        _expect_halt(self, matrix, UnknownMatrixKey)

    def test_invalid_matrix_kind_halts(self):
        matrix = _build_minimal_matrix()
        matrix["intent_test_matrix_kind"] = "wrong_kind"
        _expect_halt(self, matrix, InvalidMatrixKind)

    def test_non_string_matrix_id_halts(self):
        matrix = _build_minimal_matrix()
        matrix["matrix_id"] = 42
        _expect_halt(self, matrix, NonStringMatrixId)

    def test_empty_matrix_id_halts(self):
        matrix = _build_minimal_matrix()
        matrix["matrix_id"] = ""
        _expect_halt(self, matrix, NonStringMatrixId)

    def test_non_string_matrix_note_halts(self):
        matrix = _build_minimal_matrix()
        matrix["matrix_note"] = 42
        _expect_halt(self, matrix, NonStringMatrixNote)

    def test_non_list_cases_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"] = "not a list"
        _expect_halt(self, matrix, NonListCases)

    def test_empty_cases_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"] = []
        _expect_halt(self, matrix, EmptyCases)

    def test_non_object_case_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"] = ["not a dict"]
        _expect_halt(self, matrix, NonObjectCase)

    def test_missing_case_key_halts(self):
        matrix = _build_minimal_matrix()
        del matrix["cases"][0]["rationale"]
        _expect_halt(self, matrix, MissingCaseKey)

    def test_unknown_case_key_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["extra_unknown_key"] = "junk"
        _expect_halt(self, matrix, UnknownCaseKey)

    def test_non_string_case_id_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["case_id"] = 42
        _expect_halt(self, matrix, NonStringCaseId)

    def test_empty_case_id_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["case_id"] = ""
        _expect_halt(self, matrix, NonStringCaseId)

    def test_duplicate_case_id_halts(self):
        matrix = _build_minimal_matrix()
        case_copy = copy.deepcopy(matrix["cases"][0])
        matrix["cases"].append(case_copy)
        _expect_halt(self, matrix, DuplicateCaseId)

    def test_non_string_prompt_text_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["prompt_text"] = 42
        _expect_halt(self, matrix, NonStringPromptText)

    def test_empty_prompt_text_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["prompt_text"] = "   "
        _expect_halt(self, matrix, EmptyPromptText)

    def test_non_dict_expected_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"] = "not a dict"
        _expect_halt(self, matrix, NonDictExpected)

    def test_unknown_expected_key_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["something_else"] = "junk"
        _expect_halt(self, matrix, UnknownExpectedKey)

    def test_unknown_category_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["category"] = "Z. fictional"
        _expect_halt(self, matrix, UnknownCategory)

    def test_non_list_expected_kinds_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["expected_item_kinds_touched"] = "kind"
        _expect_halt(self, matrix, NonListExpectedKinds)

    def test_unknown_item_kind_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["expected_item_kinds_touched"] = ["bogus_kind"]
        _expect_halt(self, matrix, UnknownItemKind)

    def test_none_kind_sentinel_accepted(self):
        """`none` is accepted as an expected-kind sentinel for
        no-route cases (mirrors `_NO_ROUTE_KIND_LITERAL`)."""
        matrix = _build_minimal_matrix({
            "prompt_text": "What year did the Apollo program land on the moon?",
            "expected": {
                "category": "H. no-route",
                "expected_item_kinds_touched": ["none"],
                "ambiguity_observed": False,
                "normalized_intent_observation": "no_route",
                "candidate_surface_expected": "candidate fragment of declared shape",
                "rejection_surface_expected": "no_forced_selection",
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(result["passed_count"], 1)

    def test_non_boolean_ambiguity_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["ambiguity_observed"] = "yes"
        _expect_halt(self, matrix, NonBooleanAmbiguity)

    def test_unknown_normalized_intent_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["normalized_intent_observation"] = "bogus"
        _expect_halt(self, matrix, UnknownNormalizedIntent)

    def test_unknown_candidate_surface_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["candidate_surface_expected"] = "bogus surface"
        _expect_halt(self, matrix, UnknownCandidateSurface)

    def test_unknown_rejection_surface_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["expected"]["rejection_surface_expected"] = "bogus rejection"
        _expect_halt(self, matrix, UnknownRejectionSurface)

    def test_non_list_tolerated_variants_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["tolerated_variants"] = "not a list"
        _expect_halt(self, matrix, NonListToleratedVariants)

    def test_non_object_tolerated_variant_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["tolerated_variants"] = ["not a dict"]
        _expect_halt(self, matrix, NonObjectToleratedVariant)

    def test_unknown_tolerated_variant_key_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["tolerated_variants"] = [{"unknown_key": "x"}]
        _expect_halt(self, matrix, UnknownExpectedKey)

    def test_unknown_tolerated_variant_kind_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["tolerated_variants"] = [
            {"expected_item_kinds_touched": ["bogus_kind"]}
        ]
        _expect_halt(self, matrix, UnknownItemKind)

    def test_non_list_tags_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["tags"] = "not a list"
        _expect_halt(self, matrix, NonListTags)

    def test_non_string_tag_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["tags"] = [42]
        _expect_halt(self, matrix, NonStringTag)

    def test_non_string_rationale_halts(self):
        matrix = _build_minimal_matrix()
        matrix["cases"][0]["rationale"] = 42
        _expect_halt(self, matrix, NonStringRationale)


class ToleratedVariantTest(unittest.TestCase):
    """`tolerated_variants` accept alternative orderings without
    triggering a mismatch."""

    def test_alternative_kind_order_accepted(self):
        matrix = _build_minimal_matrix({
            "prompt_text": "Define an agent that runs a test workflow on demand.",
            "expected": {
                "category": "D. agent/persona confusion",
                "expected_item_kinds_touched": ["agent", "workflow_file"],
                "ambiguity_observed": True,
                "normalized_intent_observation": "agent_surface_workflow_intent",
                "candidate_surface_expected": "multiple candidate surfaces expected",
                "rejection_surface_expected": "no_forced_selection",
            },
            "tolerated_variants": [
                {"expected_item_kinds_touched": ["workflow_file", "agent"],
                 "rationale": "kind-order tolerance"}
            ],
        })
        result = _run_temp(matrix)
        self.assertEqual(result["passed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["observed_kinds"],
            ["workflow_file", "agent"],
        )
        self.assertEqual(
            result["case_results"][0]["expected_kinds"],
            ["agent", "workflow_file"],
        )

    def test_no_tolerated_variant_means_strict_order(self):
        matrix = _build_minimal_matrix({
            "prompt_text": "Define an agent that runs a test workflow on demand.",
            "expected": {
                "category": "D. agent/persona confusion",
                "expected_item_kinds_touched": ["agent", "workflow_file"],
                "ambiguity_observed": True,
                "normalized_intent_observation": "agent_surface_workflow_intent",
                "candidate_surface_expected": "multiple candidate surfaces expected",
                "rejection_surface_expected": "no_forced_selection",
            },
            "tolerated_variants": [],
        })
        result = _run_temp(matrix)
        # Strict order: observed [workflow_file, agent] != expected
        # [agent, workflow_file] without a tolerated variant -> fail.
        self.assertEqual(result["failed_count"], 1)
        cr = result["case_results"][0]
        self.assertFalse(cr["match"])
        self.assertEqual(
            cr["classified_as"], "frame_c_synthesis_rule_gap"
        )


class FailureClassificationTest(unittest.TestCase):
    """Synthetic mismatch fixtures classify each emit-eligible failure
    class deterministically."""

    def test_out_of_scope_underdetect_classified(self):
        """Expected H but observed != H => out_of_scope_underdetect."""
        matrix = _build_minimal_matrix({
            "prompt_text": "Configure GitHub Actions to deploy a Node.js app to Azure.",
            "expected": {
                "category": "H. no-route",
                "expected_item_kinds_touched": ["none"],
                "ambiguity_observed": False,
                "normalized_intent_observation": "no_route",
                "candidate_surface_expected": "no candidate surface expected",
                "rejection_surface_expected": "prompt_out_of_repo_scope",
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "out_of_scope_underdetect",
        )

    def test_frame_b_canonical_set_gap_classified(self):
        """Expected non-H but observed H (parser said no-signal) =>
        frame_b_canonical_set_gap."""
        matrix = _build_minimal_matrix({
            "prompt_text": "What year did the Apollo program land on the moon?",
            "expected": {
                "category": "B. workflow intent",
                "expected_item_kinds_touched": ["workflow_file"],
                "ambiguity_observed": False,
                "normalized_intent_observation": "workflow_intent",
                "candidate_surface_expected": "candidate fragment of declared shape",
                "rejection_surface_expected": "no_forced_selection",
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_b_canonical_set_gap",
        )

    def test_frame_c_category_selector_gap_classified(self):
        """Same kinds but different category => frame_c_category_selector_gap."""
        matrix = _build_minimal_matrix({
            "prompt_text": "Configure GitHub Actions to deploy a Node.js app to Azure.",
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
                "ambiguity_observed": False,
                "normalized_intent_observation": "clear_single_intent",
                "candidate_surface_expected": "candidate fragment of declared shape",
                "rejection_surface_expected": "no_forced_selection",
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_c_category_selector_gap",
        )

    def test_frame_c_synthesis_rule_gap_classified(self):
        """Same category but different kinds => frame_c_synthesis_rule_gap."""
        matrix = _build_minimal_matrix({
            "prompt_text": "Configure GitHub Actions to deploy a Node.js app to Azure.",
            "expected": {
                "category": "B. workflow intent",
                "expected_item_kinds_touched": ["workflow_file", "hook"],
                "ambiguity_observed": False,
                "normalized_intent_observation": "workflow_intent",
                "candidate_surface_expected": "candidate fragment of declared shape",
                "rejection_surface_expected": "no_forced_selection",
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_c_synthesis_rule_gap",
        )

    def test_frame_c_ambiguity_misreport_classified(self):
        """Only ambiguity differs => frame_c_ambiguity_misreport."""
        matrix = _build_minimal_matrix({
            "prompt_text": "Configure GitHub Actions to deploy a Node.js app to Azure.",
            "expected": {
                "category": "B. workflow intent",
                "expected_item_kinds_touched": ["workflow_file"],
                "ambiguity_observed": True,
                "normalized_intent_observation": "workflow_intent",
                "candidate_surface_expected": "candidate fragment of declared shape",
                "rejection_surface_expected": "no_forced_selection",
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_c_ambiguity_misreport",
        )

    def test_expected_field_drift_classified_for_surfaces_only(self):
        """Only candidate_surface_expected differs => expected_field_drift."""
        matrix = _build_minimal_matrix({
            "prompt_text": "Configure GitHub Actions to deploy a Node.js app to Azure.",
            "expected": {
                "category": "B. workflow intent",
                "expected_item_kinds_touched": ["workflow_file"],
                "ambiguity_observed": False,
                "normalized_intent_observation": "workflow_intent",
                "candidate_surface_expected": "multiple candidate surfaces expected",
                "rejection_surface_expected": "no_forced_selection",
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "expected_field_drift",
        )

    def test_tag_override_forces_frame_b_inflection_gap(self):
        matrix = _build_minimal_matrix({
            "prompt_text": "Configure GitHub Actions to deploy a Node.js app to Azure.",
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["force_frame_b_inflection_gap"],
        })
        result = _run_temp(matrix)
        self.assertEqual(result["failed_count"], 1)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_b_inflection_gap",
        )

    def test_tag_override_forces_frame_b_negation_gap(self):
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["force_frame_b_negation_gap"],
        })
        result = _run_temp(matrix)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_b_negation_gap",
        )

    def test_tag_override_forces_frame_a_normalization_gap(self):
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["force_frame_a_normalization_gap"],
        })
        result = _run_temp(matrix)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_a_normalization_gap",
        )

    def test_tag_override_forces_frame_d_translation_gap(self):
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["force_frame_d_translation_gap"],
        })
        result = _run_temp(matrix)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "frame_d_translation_gap",
        )

    def test_tag_override_forces_fixture_distribution_drift(self):
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["force_fixture_distribution_drift"],
        })
        result = _run_temp(matrix)
        self.assertEqual(
            result["case_results"][0]["classified_as"],
            "fixture_distribution_drift",
        )

    def test_reserved_ambiguity_clarification_gap_not_emitted(self):
        """Tag override for the reserved class
        `ambiguity_clarification_gap` is rewritten to `unknown` by
        the classifier since the upstream layer is not authorized."""
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["force_ambiguity_clarification_gap"],
        })
        result = _run_temp(matrix)
        self.assertEqual(
            result["case_results"][0]["classified_as"], "unknown"
        )

    def test_reserved_vocabulary_correction_miss_not_emitted(self):
        """Tag override for the reserved class
        `vocabulary_correction_miss` is rewritten to `unknown` by
        the classifier since the upstream vocabulary-correction layer
        is not yet authorized."""
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["force_vocabulary_correction_miss"],
        })
        result = _run_temp(matrix)
        self.assertEqual(
            result["case_results"][0]["classified_as"], "unknown"
        )


class ForbiddenLanguageHaltTest(unittest.TestCase):
    """Module-authored matrix strings (matrix_note, matrix_id) are
    scanned for forbidden phrases; user-authored prompt_text and
    rationale are preserved as evidence and NOT scanned."""

    def test_forbidden_phrase_in_matrix_note_halts(self):
        matrix = _build_minimal_matrix()
        matrix["matrix_note"] = "this matrix is the best"
        _expect_halt(
            self, matrix,
            ForbiddenLanguageInLevel0WorkshopIntentTestMatrixRunner,
        )

    def test_forbidden_claim_phrase_in_matrix_note_halts(self):
        matrix = _build_minimal_matrix()
        matrix["matrix_note"] = "this contains validation evidence"
        _expect_halt(
            self, matrix,
            ForbiddenLanguageInLevel0WorkshopIntentTestMatrixRunner,
        )

    def test_user_authored_prompt_text_not_scanned(self):
        """A prompt containing a forbidden phrase as USER text is
        preserved as evidence and does NOT halt."""
        matrix = _build_minimal_matrix({
            "prompt_text": "What is the best CI workflow?",
        })
        # No halt expected (prompt_text is user-authored evidence).
        path = _write_temp_matrix(matrix)
        try:
            event_log = EventLog()
            result = run_intent_test_matrix(path, event_log)
            self.assertEqual(result["case_count"], 1)
        finally:
            os.unlink(path)


class GatingBooleanFlippedTest(unittest.TestCase):
    """The runner refuses to emit any case result whose observed
    FRAME-D output flips any gating boolean True (halt-before-raise).

    Tested by monkey-patching the FRAME-D import at module scope with
    a fake callable that returns a flipped boolean dict, then running
    a one-case matrix. Restores the original after the test.
    """

    def test_observed_gating_boolean_flip_halts(self):
        import harness.level0_workshop_intent_test_matrix_runner as runner_mod
        original = runner_mod.map_level0_workshop_user_intent

        def fake_mapper(prompt_text, case_id, event_log):
            return {
                "intent_mapper_kind": "level0_workshop_user_intent_mapper",
                "workshop_prompt_record": {
                    "workshop_prompt_id": case_id,
                    "category": "B. workflow intent",
                    "prompt_text": prompt_text,
                    "expected_item_kinds_touched": ["workflow_file"],
                    "expected_candidate_surface": "candidate fragment of declared shape",
                    "expected_rejection_surface": "no_forced_selection",
                    "boundary_note": "not admitted; not qualified; workshop metadata only",
                },
                "normalized_intent_observation": "workflow_intent",
                "expected_item_kinds_touched": ["workflow_file"],
                "candidate_surface_expected": "candidate fragment of declared shape",
                "rejection_surface_expected": "no_forced_selection",
                "ambiguity_observed": False,
                "selection_made": True,  # FLIPPED
                "measurement_authorized": False,
                "real_benchmark_authorized": False,
                "real_benchmark_ready": False,
                "source_qualification_authorized": False,
                "corpus_admission_authorized": False,
                "mapper_note": "fake",
            }

        runner_mod.map_level0_workshop_user_intent = fake_mapper
        try:
            matrix = _build_minimal_matrix()
            path = _write_temp_matrix(matrix)
            try:
                event_log = EventLog()
                with self.assertRaises(
                    IntentTestMatrixRunnerGatingBooleanFlipped
                ):
                    run_intent_test_matrix(path, event_log)
                self.assertTrue(event_log.has_halt())
            finally:
                os.unlink(path)
        finally:
            runner_mod.map_level0_workshop_user_intent = original


class AggregationTest(unittest.TestCase):
    """per_failure_class_counts and per_tag_counts are aggregated
    correctly."""

    def test_per_tag_counts_includes_failed_count(self):
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
            "tags": ["taga", "tagb"],
        })
        result = _run_temp(matrix)
        self.assertEqual(result["per_tag_counts"]["taga"]["failed"], 1)
        self.assertEqual(result["per_tag_counts"]["tagb"]["failed"], 1)
        self.assertEqual(result["per_tag_counts"]["taga"]["passed"], 0)

    def test_per_failure_class_counts_increments(self):
        matrix = _build_minimal_matrix({
            "expected": {
                "category": "A. clear single-intent",
                "expected_item_kinds_touched": ["workflow_file"],
            },
        })
        result = _run_temp(matrix)
        self.assertEqual(
            result["per_failure_class_counts"]["frame_c_category_selector_gap"], 1
        )
        for fc in FAILURE_CLASSES:
            if fc != "frame_c_category_selector_gap":
                self.assertEqual(result["per_failure_class_counts"][fc], 0)


class StaticScanTest(unittest.TestCase):
    """Static scans on the runner module source."""

    def setUp(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_intent_test_matrix_runner.py",
        )
        with open(module_path, "r", encoding="ascii") as handle:
            self.source = handle.read()
        self.module_path = module_path

    def test_module_file_is_ascii(self):
        with open(self.module_path, "rb") as handle:
            raw = handle.read()
        non_ascii = sum(1 for b in raw if b > 127)
        self.assertEqual(non_ascii, 0)

    def test_no_third_party_imports(self):
        for token in ("import openai", "import anthropic", "import requests",
                      "from openai", "from anthropic", "from requests",
                      "import promptfoo", "from promptfoo",
                      "import litellm", "from litellm"):
            self.assertNotIn(token, self.source)

    def test_no_external_integration_call_patterns(self):
        # Patterns that would represent an actual call out to an LLM /
        # provider / external integration. Plain word substrings are
        # not checked here because the module docstring carries
        # non-claim references ("not an LLM / provider call").
        import re
        for pattern in (
            r"openai\.\w+\(",
            r"anthropic\.\w+\(",
            r"promptfoo\.\w+\(",
            r"litellm\.\w+\(",
        ):
            self.assertEqual(
                re.findall(pattern, self.source), [],
                "external integration call pattern found: {0}".format(pattern),
            )

    def test_no_network_or_subprocess_imports(self):
        for token in ("import urllib", "from urllib",
                      "import http.client", "from http.client",
                      "import socket", "from socket",
                      "import subprocess", "from subprocess",
                      "os.system(", "shutil.copy("):
            self.assertNotIn(token, self.source)

    def test_no_hash_imports(self):
        for token in ("import hashlib", "from hashlib",
                      ".hexdigest(", ".sha256("):
            self.assertNotIn(token, self.source)

    def test_no_retrieval_verb_definitions(self):
        for token in ("def query", "def search", "def retrieve",
                      "def rank"):
            self.assertNotIn(token, self.source)

    def test_no_scoring_call_patterns(self):
        for token in (" score(", " scoring(", "ranked_", "winner"):
            self.assertNotIn(token, self.source)

    def test_no_forbidden_output_field_name_substrings(self):
        # `ranking_performed` and `scoring_performed` are forbidden
        # FRAME-A / B / C / D output field names. The runner must not
        # declare them as identifiers.
        import re
        for token in ("ranking_performed", "scoring_performed"):
            # Check for actual identifier usage, not docstring mention.
            matches = re.findall(r"\b" + token + r"\b\s*[=:]", self.source)
            self.assertEqual(
                matches, [],
                "forbidden output field name as identifier: {0}".format(token),
            )

    def test_no_vocabulary_collision_call_patterns(self):
        # The module must not declare any of these as identifiers or
        # output keys. Docstring mentions are tolerated; actual code
        # use (assignment, dict key, function call) is forbidden.
        import re
        for token in ("golden_set", "evaluation_set", "regression_gate",
                      "validated_route", "route_trust", "benchmark_result",
                      "benchmark_output", "architecture_selection",
                      "production_ready"):
            matches = re.findall(r"\b" + token + r"\b\s*[=:]", self.source)
            self.assertEqual(
                matches, [],
                "vocabulary-collision identifier found: {0}".format(token),
            )

    def test_no_payload_loader_reuse(self):
        """The runner does NOT reuse `harness/payload_loader.py`
        functions; only the bounded `FORBIDDEN_CLAIM_PHRASES` constant
        is imported for the forbidden-language scan.

        The substring `payload_loader.` may appear in the module
        docstring (referencing `harness/payload_loader.py` as a name);
        this test asserts no attribute-access or function-call against
        the module."""
        # No attribute access via the module name. Any such call would
        # look like `payload_loader.<name>(` in source.
        # The import line uses `from harness.payload_loader import ...`
        # which does NOT match `payload_loader.<call>` syntax.
        import re
        # Match `payload_loader.<word>(` to catch function calls.
        matches = re.findall(r"payload_loader\.\w+\(", self.source)
        self.assertEqual(matches, [], "runner must not call payload_loader.* functions")
        self.assertIn("from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES",
                      self.source)


class ParserIsolationTest(unittest.TestCase):
    """The runner imports only the FRAME-D public function plus the
    bounded enum constants from FRAME-C. FRAME-A / B / C / D modules
    do NOT import the runner."""

    def setUp(self):
        self.runner_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_intent_test_matrix_runner.py",
        )
        with open(self.runner_path, "r", encoding="ascii") as handle:
            self.runner_source = handle.read()

    def test_runner_imports_only_frame_d_public_and_frame_c_enums(self):
        self.assertIn(
            "from harness.level0_workshop_user_intent_mapper import (",
            self.runner_source,
        )
        self.assertIn("map_level0_workshop_user_intent", self.runner_source)
        # FRAME-C: only bounded enum constants.
        self.assertIn(
            "from harness.level0_workshop_canonical_intent_frame import (",
            self.runner_source,
        )
        self.assertIn("WORKSHOP_ITEM_KINDS", self.runner_source)
        self.assertIn("WORKSHOP_PROMPT_CATEGORIES", self.runner_source)
        # FRAME-A: NOT imported.
        self.assertNotIn(
            "from harness.level0_workshop_normalized_prompt_view",
            self.runner_source,
        )
        # FRAME-B: NOT imported.
        self.assertNotIn(
            "from harness.level0_workshop_signal_evidence",
            self.runner_source,
        )

    def test_runner_does_not_call_frame_c_internal(self):
        """The runner does NOT call FRAME-C's `build_canonical_intent_frame`."""
        self.assertNotIn(
            "build_canonical_intent_frame(", self.runner_source
        )
        self.assertNotIn(
            "build_level0_workshop_normalized_prompt_view(",
            self.runner_source,
        )
        self.assertNotIn(
            "extract_workshop_signal_evidence(", self.runner_source
        )

    def test_frame_a_b_c_d_modules_do_not_import_runner(self):
        """The four parser modules do NOT reference the runner module."""
        parser_modules = (
            "level0_workshop_normalized_prompt_view.py",
            "level0_workshop_signal_evidence.py",
            "level0_workshop_canonical_intent_frame.py",
            "level0_workshop_user_intent_mapper.py",
        )
        runner_name = "level0_workshop_intent_test_matrix_runner"
        for fname in parser_modules:
            path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                fname,
            )
            with open(path, "r", encoding="ascii") as handle:
                source = handle.read()
            self.assertNotIn(runner_name, source)


if __name__ == "__main__":
    unittest.main()
