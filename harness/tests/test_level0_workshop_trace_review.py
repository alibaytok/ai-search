"""Tests for `harness.level0_workshop_trace_review`.

Tests build a clean synthetic workshop trace report by invoking
`run_level0_workshop_derived_trace` (WO-L0-WORKSHOP-TRACE-01) at the
test layer to produce a real input dict, then exercise the review
module against that dict and against deliberately mutated copies to
cover each halt branch.

The module under test does NOT invoke any prior-WO public function;
the upstream invocation here is test-only fixture construction.
"""

import copy
import os
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_derived_trace import (
    EXPECTED_ITEM_KIND_DISTRIBUTION,
    WORKSHOP_BOUNDARY_NOTE,
    run_level0_workshop_derived_trace,
)
from harness.level0_workshop_trace_review import (
    ALLOWED_OUTPUT_KEYS,
    ForbiddenLanguageInLevel0WorkshopTraceReview,
    InvalidWorkshopTraceKind,
    MissingWorkshopTraceReportKey,
    NonDictWorkshopTraceReport,
    REQUIRED_INPUT_KEYS,
    UnknownWorkshopTraceReportKey,
    WorkshopTraceAmbiguousMissingMarker,
    WorkshopTraceAuthorizationBooleanFlipped,
    WorkshopTraceCandidateOnlyNotTrue,
    WorkshopTraceCountMismatch,
    WorkshopTraceForbiddenFlipPresent,
    WorkshopTraceNearMissInvariantViolated,
    WorkshopTraceNoRouteInvariantViolated,
    WorkshopTraceRouteStatusFieldPresent,
    run_level0_workshop_trace_review,
)


_PROMPT_PLAN = (
    ("A. clear single-intent", ["skill"]),
    ("A. clear single-intent", ["instruction"]),
    ("A. clear single-intent", ["agent"]),
    ("A. clear single-intent", ["plugin"]),
    ("B. workflow intent", ["workflow_file"]),
    ("B. workflow intent", ["workflow_file"]),
    ("B. workflow intent", ["workflow_file", "hook"]),
    ("B. workflow intent", ["workflow_file"]),
    ("C. skill intent", ["skill"]),
    ("C. skill intent", ["skill"]),
    ("C. skill intent", ["skill"]),
    ("D. agent/persona confusion", ["agent", "workflow_file"]),
    ("D. agent/persona confusion", ["agent", "workflow_file"]),
    ("D. agent/persona confusion", ["agent", "workflow_file"]),
    ("E. instruction confusion", ["instruction", "workflow_file"]),
    ("E. instruction confusion", ["instruction", "workflow_file"]),
    ("E. instruction confusion", ["instruction", "workflow_file"]),
    ("F. prompt-search-shaped but workflow-intent", ["cookbook_entry", "workflow_file"]),
    ("F. prompt-search-shaped but workflow-intent", ["cookbook_entry", "workflow_file"]),
    ("G. ambiguous", ["skill", "instruction", "agent"]),
    ("G. ambiguous", ["workflow_file", "instruction", "cookbook_entry"]),
    ("G. ambiguous", ["skill", "instruction", "workflow_file"]),
    ("H. no-route", ["none"]),
    ("H. no-route", ["none"]),
    ("I. near-miss/rejection", ["repo_meta_section"]),
    ("I. near-miss/rejection", ["repo_meta_section"]),
)


def _build_clean_item_records():
    records = []
    next_index = 1
    for kind, expected in EXPECTED_ITEM_KIND_DISTRIBUTION.items():
        for _ in range(expected):
            records.append({
                "workshop_item_id": "W-ITEM-{0:03d}".format(next_index),
                "repo_path_shape": "{0}/".format(kind),
                "item_kind": kind,
                "selection_locator_hint": "{0} slot hint {1}".format(
                    kind, next_index
                ),
                "material_role": "{0} role for slot {1}".format(
                    kind, next_index
                ),
                "expected_trace_surface": "candidate fragment of {0} shape".format(
                    kind
                ),
                "boundary_note": WORKSHOP_BOUNDARY_NOTE,
            })
            next_index += 1
    return records


def _build_clean_prompt_records():
    records = []
    next_index = 1
    for category, kinds in _PROMPT_PLAN:
        records.append({
            "workshop_prompt_id": "W-PRM-{0:03d}".format(next_index),
            "category": category,
            "prompt_text": "synthetic workshop prompt slot {0}".format(
                next_index
            ),
            "expected_item_kinds_touched": list(kinds),
            "expected_candidate_surface": "candidate fragment of declared shape",
            "expected_rejection_surface": "no forced selection",
            "boundary_note": WORKSHOP_BOUNDARY_NOTE,
        })
        next_index += 1
    return records


def _build_clean_workshop_trace_report():
    items = _build_clean_item_records()
    prompts = _build_clean_prompt_records()
    return run_level0_workshop_derived_trace(items, prompts, EventLog())


class CleanPassTest(unittest.TestCase):

    def setUp(self):
        self.report = _build_clean_workshop_trace_report()
        self.event_log = EventLog()
        self.result = run_level0_workshop_trace_review(
            self.report, self.event_log
        )

    def test_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_workshop_review_kind_literal(self):
        self.assertEqual(
            self.result["workshop_review_kind"],
            "level0_workshop_trace_review",
        )

    def test_input_trace_kind_carried_through(self):
        self.assertEqual(
            self.result["input_trace_kind"],
            "level0_workshop_derived_trace",
        )

    def test_review_passed_literal_true(self):
        self.assertIs(self.result["review_passed"], True)

    def test_review_halt_required_literal_false(self):
        self.assertIs(self.result["review_halt_required"], False)

    def test_observed_item_count_70(self):
        self.assertEqual(self.result["observed_item_count"], 70)

    def test_observed_prompt_count_26(self):
        self.assertEqual(self.result["observed_prompt_count"], 26)

    def test_observed_candidate_route_count_51(self):
        self.assertEqual(
            self.result["observed_candidate_route_fragment_count"], 51
        )

    def test_observed_candidate_workflow_count_13(self):
        self.assertEqual(
            self.result["observed_candidate_workflow_fragment_count"], 13
        )

    def test_observed_rejected_count_6(self):
        self.assertEqual(self.result["observed_rejected_material_count"], 6)

    def test_ambiguous_prompt_count_3(self):
        self.assertEqual(self.result["ambiguous_prompt_count"], 3)

    def test_no_route_prompt_count_2(self):
        self.assertEqual(self.result["no_route_prompt_count"], 2)

    def test_near_miss_prompt_count_2(self):
        self.assertEqual(self.result["near_miss_prompt_count"], 2)

    def test_candidate_surface_observed_true(self):
        self.assertIs(self.result["candidate_surface_observed"], True)

    def test_workflow_surface_observed_true(self):
        self.assertIs(self.result["workflow_surface_observed"], True)

    def test_rejection_surface_observed_true(self):
        self.assertIs(self.result["rejection_surface_observed"], True)

    def test_route_created_literal_false(self):
        self.assertIs(self.result["route_created"], False)

    def test_selection_made_literal_false(self):
        self.assertIs(self.result["selection_made"], False)

    def test_measurement_authorized_literal_false(self):
        self.assertIs(self.result["measurement_authorized"], False)

    def test_real_benchmark_authorized_literal_false(self):
        self.assertIs(self.result["real_benchmark_authorized"], False)

    def test_real_benchmark_ready_literal_false(self):
        self.assertIs(self.result["real_benchmark_ready"], False)

    def test_source_qualification_authorized_literal_false(self):
        self.assertIs(self.result["source_qualification_authorized"], False)

    def test_corpus_admission_authorized_literal_false(self):
        self.assertIs(self.result["corpus_admission_authorized"], False)

    def test_next_gap_notes_bounded_list(self):
        self.assertEqual(self.result["next_gap_notes"], [
            "semantic_content_extraction_not_tested",
            "real_indexing_not_implemented",
            "route_selection_not_authorized",
            "cross_vendor_seed_not_executed",
        ])

    def test_review_note_non_empty_string(self):
        self.assertIsInstance(self.result["review_note"], str)
        self.assertGreater(len(self.result["review_note"]), 0)

    def test_started_and_completed_events_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn("level0_workshop_trace_review_started", types)
        self.assertIn("level0_workshop_trace_review_completed", types)

    def test_no_halt_event(self):
        self.assertFalse(self.event_log.has_halt())


class TopLevelInputValidationTest(unittest.TestCase):

    def test_non_dict_report_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonDictWorkshopTraceReport):
            run_level0_workshop_trace_review("not a dict", event_log)
        self.assertTrue(event_log.has_halt())

    def test_missing_top_level_key_halts(self):
        report = _build_clean_workshop_trace_report()
        del report["per_prompt_trace_summary"]
        event_log = EventLog()
        with self.assertRaises(MissingWorkshopTraceReportKey):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_unknown_top_level_key_halts(self):
        report = _build_clean_workshop_trace_report()
        report["extra_unknown_key"] = "synthetic extra"
        event_log = EventLog()
        with self.assertRaises(UnknownWorkshopTraceReportKey):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_invalid_workshop_trace_kind_halts(self):
        report = _build_clean_workshop_trace_report()
        report["workshop_trace_kind"] = "some_other_kind"
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopTraceKind):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())


class CountMismatchTest(unittest.TestCase):

    def _mutate_and_expect_count_mismatch(self, key, new_value):
        report = _build_clean_workshop_trace_report()
        report[key] = new_value
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceCountMismatch):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_item_count_mismatch_halts(self):
        self._mutate_and_expect_count_mismatch("item_count", 71)

    def test_prompt_count_mismatch_halts(self):
        self._mutate_and_expect_count_mismatch("prompt_count", 27)

    def test_derived_material_count_mismatch_halts(self):
        self._mutate_and_expect_count_mismatch("derived_material_count", 69)

    def test_candidate_route_count_mismatch_halts(self):
        self._mutate_and_expect_count_mismatch("candidate_route_fragment_count", 50)

    def test_candidate_workflow_count_mismatch_halts(self):
        self._mutate_and_expect_count_mismatch(
            "candidate_workflow_fragment_count", 12
        )

    def test_rejected_count_mismatch_halts(self):
        self._mutate_and_expect_count_mismatch("rejected_material_count", 5)

    def test_derived_material_records_length_mismatch_halts(self):
        report = _build_clean_workshop_trace_report()
        report["derived_material_records"] = report["derived_material_records"][:69]
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceCountMismatch):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_candidate_route_records_length_mismatch_halts(self):
        report = _build_clean_workshop_trace_report()
        report["candidate_route_fragment_records"] = (
            report["candidate_route_fragment_records"][:50]
        )
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceCountMismatch):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_candidate_workflow_records_length_mismatch_halts(self):
        report = _build_clean_workshop_trace_report()
        report["candidate_workflow_fragment_records"] = (
            report["candidate_workflow_fragment_records"][:12]
        )
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceCountMismatch):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_rejected_material_records_length_mismatch_halts(self):
        report = _build_clean_workshop_trace_report()
        report["rejected_material_records"] = report["rejected_material_records"][:5]
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceCountMismatch):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_per_prompt_summary_length_mismatch_halts(self):
        report = _build_clean_workshop_trace_report()
        report["per_prompt_trace_summary"] = report["per_prompt_trace_summary"][:25]
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceCountMismatch):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())


class AuthorizationBooleanFlipTest(unittest.TestCase):

    def _flip_and_expect_halt(self, key):
        report = _build_clean_workshop_trace_report()
        report[key] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceAuthorizationBooleanFlipped):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_selection_made_flip_halts(self):
        self._flip_and_expect_halt("selection_made")

    def test_measurement_authorized_flip_halts(self):
        self._flip_and_expect_halt("measurement_authorized")

    def test_real_benchmark_authorized_flip_halts(self):
        self._flip_and_expect_halt("real_benchmark_authorized")

    def test_real_benchmark_ready_flip_halts(self):
        self._flip_and_expect_halt("real_benchmark_ready")

    def test_source_qualification_authorized_flip_halts(self):
        self._flip_and_expect_halt("source_qualification_authorized")

    def test_corpus_admission_authorized_flip_halts(self):
        self._flip_and_expect_halt("corpus_admission_authorized")


class NestedRecordCheckTest(unittest.TestCase):

    def test_route_status_field_injection_halts(self):
        report = _build_clean_workshop_trace_report()
        report["derived_material_records"][0]["official"] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceRouteStatusFieldPresent):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_route_status_field_in_candidate_workflow_halts(self):
        report = _build_clean_workshop_trace_report()
        report["candidate_workflow_fragment_records"][0]["is_route"] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceRouteStatusFieldPresent):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_route_status_field_in_per_prompt_summary_halts(self):
        report = _build_clean_workshop_trace_report()
        report["per_prompt_trace_summary"][0]["selected_route"] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceRouteStatusFieldPresent):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_candidate_only_false_halts(self):
        report = _build_clean_workshop_trace_report()
        report["derived_material_records"][0]["candidate_only"] = False
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceCandidateOnlyNotTrue):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_qualified_flip_halts(self):
        report = _build_clean_workshop_trace_report()
        report["derived_material_records"][0]["qualified"] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceForbiddenFlipPresent):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_corpus_admitted_flip_halts(self):
        report = _build_clean_workshop_trace_report()
        report["derived_material_records"][0]["corpus_admitted"] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceForbiddenFlipPresent):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_route_object_created_flip_halts(self):
        report = _build_clean_workshop_trace_report()
        report["derived_material_records"][0]["route_object_created"] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceForbiddenFlipPresent):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_source_material_extracted_flip_halts(self):
        report = _build_clean_workshop_trace_report()
        report["derived_material_records"][0]["source_material_extracted"] = True
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceForbiddenFlipPresent):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())


class PerPromptInvariantTest(unittest.TestCase):

    def _find_index_by_category(self, summary, category):
        for index, entry in enumerate(summary):
            if entry.get("category") == category:
                return index
        raise AssertionError("no entry for category {0!r}".format(category))

    def test_ambiguous_without_marker_halts(self):
        report = _build_clean_workshop_trace_report()
        idx = self._find_index_by_category(
            report["per_prompt_trace_summary"], "G. ambiguous"
        )
        report["per_prompt_trace_summary"][idx]["ambiguity_observed"] = False
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceAmbiguousMissingMarker):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_no_route_with_candidate_halts(self):
        report = _build_clean_workshop_trace_report()
        idx = self._find_index_by_category(
            report["per_prompt_trace_summary"], "H. no-route"
        )
        report["per_prompt_trace_summary"][idx]["attached_candidate_route_fragment_count"] = 1
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceNoRouteInvariantViolated):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_no_route_with_wrong_reason_halts(self):
        report = _build_clean_workshop_trace_report()
        idx = self._find_index_by_category(
            report["per_prompt_trace_summary"], "H. no-route"
        )
        report["per_prompt_trace_summary"][idx]["no_selection_reason"] = "wrong_reason"
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceNoRouteInvariantViolated):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_near_miss_with_route_candidate_halts(self):
        report = _build_clean_workshop_trace_report()
        idx = self._find_index_by_category(
            report["per_prompt_trace_summary"], "I. near-miss/rejection"
        )
        report["per_prompt_trace_summary"][idx]["attached_candidate_route_fragment_count"] = 1
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceNearMissInvariantViolated):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_near_miss_with_workflow_candidate_halts(self):
        report = _build_clean_workshop_trace_report()
        idx = self._find_index_by_category(
            report["per_prompt_trace_summary"], "I. near-miss/rejection"
        )
        report["per_prompt_trace_summary"][idx]["attached_candidate_workflow_fragment_count"] = 1
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceNearMissInvariantViolated):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_near_miss_with_empty_rejected_halts(self):
        report = _build_clean_workshop_trace_report()
        idx = self._find_index_by_category(
            report["per_prompt_trace_summary"], "I. near-miss/rejection"
        )
        report["per_prompt_trace_summary"][idx]["attached_rejected_material_count"] = 0
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceNearMissInvariantViolated):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_near_miss_with_wrong_reason_halts(self):
        report = _build_clean_workshop_trace_report()
        idx = self._find_index_by_category(
            report["per_prompt_trace_summary"], "I. near-miss/rejection"
        )
        report["per_prompt_trace_summary"][idx]["no_selection_reason"] = "wrong_reason"
        event_log = EventLog()
        with self.assertRaises(WorkshopTraceNearMissInvariantViolated):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())


class ForbiddenLanguageTest(unittest.TestCase):

    def test_forbidden_phrase_in_input_halts(self):
        report = _build_clean_workshop_trace_report()
        report["workshop_trace_note"] = "this is the best of the scaffolds"
        event_log = EventLog()
        with self.assertRaises(ForbiddenLanguageInLevel0WorkshopTraceReview):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())

    def test_forbidden_claim_phrase_in_input_halts(self):
        report = _build_clean_workshop_trace_report()
        report["workshop_trace_note"] = "this is a validated route note"
        event_log = EventLog()
        with self.assertRaises(ForbiddenLanguageInLevel0WorkshopTraceReview):
            run_level0_workshop_trace_review(report, event_log)
        self.assertTrue(event_log.has_halt())


class InputIsolationTest(unittest.TestCase):

    def test_input_dict_not_mutated(self):
        report = _build_clean_workshop_trace_report()
        before = copy.deepcopy(report)
        run_level0_workshop_trace_review(report, EventLog())
        self.assertEqual(report, before)


class StaticScanTest(unittest.TestCase):

    def setUp(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_trace_review.py",
        )
        with open(module_path, "r", encoding="ascii") as handle:
            self.source = handle.read()

    def test_no_file_io_calls(self):
        for token in ("open(", "pathlib"):
            self.assertNotIn(token, self.source)

    def test_no_network_or_http_tokens(self):
        for token in ("urllib", "http.client", "socket"):
            self.assertNotIn(token, self.source)

    def test_no_requests_library_token(self):
        for token in ("import requests", "from requests", "requests."):
            self.assertNotIn(token, self.source)

    def test_no_subprocess_or_shell_tokens(self):
        for token in ("subprocess", "os.system", "shutil"):
            self.assertNotIn(token, self.source)

    def test_no_hash_tokens(self):
        for token in ("hashlib", ".hexdigest", ".sha256"):
            self.assertNotIn(token, self.source)

    def test_no_retrieval_verb_definitions(self):
        for token in ("def query", "def search", "def retrieve", "def rank"):
            self.assertNotIn(token, self.source)

    def test_no_scoring_tokens(self):
        for token in ("score", "scoring"):
            self.assertNotIn(token, self.source)

    def test_no_external_integration_tokens(self):
        for token in (
            "copilot", "waza", "vscode", "vs_code", "openai",
            "anthropic", "claude_api", "llm",
        ):
            self.assertNotIn(token, self.source)

    def test_no_prior_wo_public_function_invoked(self):
        prior_public_functions = (
            "run_scaffold_route_query_probe",
            "run_scaffold_route_query_ambiguity_probe",
            "run_scaffold_conflicting_evidence_guard",
            "run_scaffold_source_intake_trace",
            "run_scaffold_source_intake_register",
            "run_scaffold_source_trace_admission_bridge",
            "run_scaffold_source_intake_smoke_package",
            "run_scaffold_route_invariant_diagnostic_reporter",
            "run_scaffold_source_intake_visible_report",
            "run_scaffold_external_source_acquisition_boundary",
            "run_scaffold_url_acquisition_executor",
            "run_scaffold_url_acquisition_register_readiness",
            "run_level0_manual_seed_visible_report",
            "run_level0_manual_seed_trace_execution",
            "run_level0_manual_seed_materialization",
            "run_level0_manual_seed_end_to_end_trace",
            "run_level0_workshop_derived_trace",
        )
        for name in prior_public_functions:
            self.assertNotIn(name, self.source)

    def test_module_file_is_ascii(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_trace_review.py",
        )
        with open(module_path, "rb") as handle:
            raw = handle.read()
        non_ascii = sum(1 for b in raw if b > 127)
        self.assertEqual(non_ascii, 0)


if __name__ == "__main__":
    unittest.main()
