"""Tests for `harness.level0_manual_seed_visible_report`.

Tests construct synthetic in-memory `item_records` and `prompt_records`
that match the structural shape described in the WO-L0-ITEMS-01
planning artifacts (`ai-search/00-level0-item-selection.md` and
`ai-search/00-level0-prompt-set.md`). The tests deliberately use
clean placeholder strings for free-text fields so that the module's
forbidden-language scan is exercised by targeted negative tests
rather than by incidental phrasing in synthetic inputs.

These tests do not read either planning document at runtime. They
do not perform file IO, network calls, URL fetches, PDF reads, or
hashing. They do not invoke any prior-WO public function.
"""

import os
import unittest

from harness.event_log import EventLog
from harness.level0_manual_seed_visible_report import (
    ALLOWED_OUTPUT_KEYS,
    EXPECTED_ITEM_COUNT,
    EXPECTED_PROMPT_CATEGORIES,
    EXPECTED_PROMPT_COUNT,
    EXPECTED_SOURCE_IDS,
    ForbiddenLanguageInLevel0ManualSeedReport,
    InvalidItemBoundaryNoteLiteral,
    InvalidItemRecordCount,
    InvalidPromptRecordCount,
    ITEM_BOUNDARY_NOTE,
    MissingItemRecordField,
    MissingPromptCategoryCoverage,
    MissingPromptRecordField,
    MissingSourceIdCoverage,
    NonListItemRecords,
    NonListPromptRecords,
    NonObjectItemRecord,
    NonObjectPromptRecord,
    REQUIRED_ITEM_FIELDS,
    REQUIRED_PROMPT_FIELDS,
    UnknownItemRecordField,
    UnknownPromptCategory,
    UnknownPromptRecordField,
    UnknownSourceId,
    run_level0_manual_seed_visible_report,
)


_SOURCE_DISTRIBUTION = (
    ("L0-SRC-001", 12),
    ("L0-SRC-002", 10),
    ("L0-SRC-003", 9),
    ("L0-SRC-004", 9),
    ("L0-SRC-005", 9),
    ("L0-SRC-006", 11),
    ("L0-SRC-007", 5),
)


_CATEGORY_DISTRIBUTION = (
    ("A. clear single-intent", 4),
    ("B. multi-intent", 3),
    ("C. ambiguous", 3),
    ("D. prompt-search-shaped that should become workflow / route intent", 2),
    ("E. no-route", 2),
    ("F. refusal / no-selection", 2),
    ("G. multi-source-touching", 3),
    ("H. near-miss involving L0-SRC-007", 2),
    ("I. workflow involving L0-SRC-006", 2),
)


def _build_clean_item_records():
    """Build 65 synthetic item records that pass clean-pass validation."""
    records = []
    next_index = 1
    for source_id, count in _SOURCE_DISTRIBUTION:
        for _ in range(count):
            records.append({
                "item_id": "L0-ITEM-{0:03d}".format(next_index),
                "source_id": source_id,
                "item_kind": "prompt",
                "item_title_or_anchor": "synthetic slot {0}".format(next_index),
                "item_locator": "{0} subfolder".format(source_id),
                "intended_test_role": "supports synthetic prompt {0}".format(
                    next_index
                ),
                "boundary_notes": ITEM_BOUNDARY_NOTE,
            })
            next_index += 1
    return records


def _build_clean_prompt_records():
    """Build 23 synthetic prompt records that pass clean-pass validation."""
    records = []
    next_index = 1
    for category, count in _CATEGORY_DISTRIBUTION:
        for _ in range(count):
            records.append({
                "prompt_id": "L0-PRM-{0:03d}".format(next_index),
                "category": category,
                "prompt_text": "synthetic test prompt {0}".format(next_index),
                "expected_behavior_summary": (
                    "synthetic observation expected for prompt {0}".format(
                        next_index
                    )
                ),
                "expected_source_touch": "L0-SRC-001",
                "expected_candidate_shape": "candidate_only_fragments",
                "expected_rejection_targets": "L0-SRC-007",
            })
            next_index += 1
    return records


class CleanPassTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.event_log = EventLog()
        self.result = run_level0_manual_seed_visible_report(
            self.items, self.prompts, self.event_log
        )

    def test_clean_pass_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_clean_pass_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_clean_pass_report_kind(self):
        self.assertEqual(
            self.result["report_kind"], "level0_manual_seed_visible_report"
        )

    def test_clean_pass_item_count(self):
        self.assertEqual(self.result["item_count"], 65)

    def test_clean_pass_prompt_count(self):
        self.assertEqual(self.result["prompt_count"], 23)

    def test_clean_pass_source_ids_observed_sorted_seven(self):
        self.assertEqual(
            self.result["source_ids_observed"], sorted(EXPECTED_SOURCE_IDS)
        )
        self.assertEqual(len(self.result["source_ids_observed"]), 7)

    def test_clean_pass_prompt_categories_observed_sorted_nine(self):
        self.assertEqual(
            self.result["prompt_categories_observed"],
            sorted(EXPECTED_PROMPT_CATEGORIES),
        )
        self.assertEqual(len(self.result["prompt_categories_observed"]), 9)

    def test_clean_pass_expected_workflow_prompt_count_is_two(self):
        self.assertEqual(self.result["expected_workflow_prompt_count"], 2)

    def test_clean_pass_expected_near_miss_prompt_count_is_two(self):
        self.assertEqual(self.result["expected_near_miss_prompt_count"], 2)

    def test_clean_pass_expected_no_route_prompt_count_is_two(self):
        self.assertEqual(self.result["expected_no_route_prompt_count"], 2)

    def test_clean_pass_expected_ambiguous_prompt_count_is_three(self):
        self.assertEqual(self.result["expected_ambiguous_prompt_count"], 3)

    def test_clean_pass_manual_seed_ready_for_visible_trace_is_true(self):
        self.assertIs(
            self.result["manual_seed_ready_for_visible_trace"], True
        )

    def test_clean_pass_selection_made_is_literal_false(self):
        self.assertIs(self.result["selection_made"], False)

    def test_clean_pass_measurement_authorized_is_literal_false(self):
        self.assertIs(self.result["measurement_authorized"], False)

    def test_clean_pass_real_benchmark_authorized_is_literal_false(self):
        self.assertIs(self.result["real_benchmark_authorized"], False)

    def test_clean_pass_real_benchmark_ready_is_literal_false(self):
        self.assertIs(self.result["real_benchmark_ready"], False)

    def test_clean_pass_report_note_is_non_empty_string(self):
        self.assertIsInstance(self.result["report_note"], str)
        self.assertGreater(len(self.result["report_note"]), 0)

    def test_clean_pass_started_event_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn("level0_manual_seed_visible_report_started", types)

    def test_clean_pass_completed_event_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn("level0_manual_seed_visible_report_completed", types)

    def test_clean_pass_no_halt_event(self):
        self.assertFalse(self.event_log.has_halt())


class InputTypeValidationTest(unittest.TestCase):

    def test_non_list_item_records_rejected(self):
        with self.assertRaises(NonListItemRecords):
            run_level0_manual_seed_visible_report(
                "not a list", _build_clean_prompt_records(), EventLog()
            )

    def test_non_list_prompt_records_rejected(self):
        with self.assertRaises(NonListPromptRecords):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), {"not": "a list"}, EventLog()
            )

    def test_dict_item_records_rejected(self):
        with self.assertRaises(NonListItemRecords):
            run_level0_manual_seed_visible_report(
                {"k": "v"}, _build_clean_prompt_records(), EventLog()
            )

    def test_none_item_records_rejected(self):
        with self.assertRaises(NonListItemRecords):
            run_level0_manual_seed_visible_report(
                None, _build_clean_prompt_records(), EventLog()
            )


class RecordCountValidationTest(unittest.TestCase):

    def test_too_few_items_rejected(self):
        items = _build_clean_item_records()[:-1]
        with self.assertRaises(InvalidItemRecordCount):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_too_many_items_rejected(self):
        items = _build_clean_item_records()
        items.append(dict(items[0]))
        with self.assertRaises(InvalidItemRecordCount):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_too_few_prompts_rejected(self):
        prompts = _build_clean_prompt_records()[:-1]
        with self.assertRaises(InvalidPromptRecordCount):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )

    def test_too_many_prompts_rejected(self):
        prompts = _build_clean_prompt_records()
        prompts.append(dict(prompts[0]))
        with self.assertRaises(InvalidPromptRecordCount):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )

    def test_empty_items_rejected(self):
        with self.assertRaises(InvalidItemRecordCount):
            run_level0_manual_seed_visible_report(
                [], _build_clean_prompt_records(), EventLog()
            )

    def test_empty_prompts_rejected(self):
        with self.assertRaises(InvalidPromptRecordCount):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), [], EventLog()
            )


class ItemFieldValidationTest(unittest.TestCase):

    def test_non_dict_item_record_rejected(self):
        items = _build_clean_item_records()
        items[0] = "not a dict"
        with self.assertRaises(NonObjectItemRecord):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def _run_with_missing_item_field(self, field):
        items = _build_clean_item_records()
        del items[0][field]
        with self.assertRaises(MissingItemRecordField):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_missing_item_id_rejected(self):
        self._run_with_missing_item_field("item_id")

    def test_missing_source_id_rejected(self):
        self._run_with_missing_item_field("source_id")

    def test_missing_item_kind_rejected(self):
        self._run_with_missing_item_field("item_kind")

    def test_missing_item_title_or_anchor_rejected(self):
        self._run_with_missing_item_field("item_title_or_anchor")

    def test_missing_item_locator_rejected(self):
        self._run_with_missing_item_field("item_locator")

    def test_missing_intended_test_role_rejected(self):
        self._run_with_missing_item_field("intended_test_role")

    def test_missing_boundary_notes_rejected(self):
        self._run_with_missing_item_field("boundary_notes")

    def test_every_required_item_field_is_checked(self):
        for field in REQUIRED_ITEM_FIELDS:
            items = _build_clean_item_records()
            del items[0][field]
            with self.assertRaises(MissingItemRecordField):
                run_level0_manual_seed_visible_report(
                    items, _build_clean_prompt_records(), EventLog()
                )

    def test_unknown_item_field_rejected(self):
        items = _build_clean_item_records()
        items[0]["route_state"] = "official"
        with self.assertRaises(UnknownItemRecordField):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_corpus_admitted_item_field_rejected(self):
        items = _build_clean_item_records()
        items[0]["corpus_admitted"] = True
        with self.assertRaises(UnknownItemRecordField):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )


class PromptFieldValidationTest(unittest.TestCase):

    def test_non_dict_prompt_record_rejected(self):
        prompts = _build_clean_prompt_records()
        prompts[0] = ["not", "a", "dict"]
        with self.assertRaises(NonObjectPromptRecord):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )

    def _run_with_missing_prompt_field(self, field):
        prompts = _build_clean_prompt_records()
        del prompts[0][field]
        with self.assertRaises(MissingPromptRecordField):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )

    def test_missing_prompt_id_rejected(self):
        self._run_with_missing_prompt_field("prompt_id")

    def test_missing_category_rejected(self):
        self._run_with_missing_prompt_field("category")

    def test_missing_prompt_text_rejected(self):
        self._run_with_missing_prompt_field("prompt_text")

    def test_missing_expected_behavior_summary_rejected(self):
        self._run_with_missing_prompt_field("expected_behavior_summary")

    def test_missing_expected_source_touch_rejected(self):
        self._run_with_missing_prompt_field("expected_source_touch")

    def test_missing_expected_candidate_shape_rejected(self):
        self._run_with_missing_prompt_field("expected_candidate_shape")

    def test_missing_expected_rejection_targets_rejected(self):
        self._run_with_missing_prompt_field("expected_rejection_targets")

    def test_every_required_prompt_field_is_checked(self):
        for field in REQUIRED_PROMPT_FIELDS:
            prompts = _build_clean_prompt_records()
            del prompts[0][field]
            with self.assertRaises(MissingPromptRecordField):
                run_level0_manual_seed_visible_report(
                    _build_clean_item_records(), prompts, EventLog()
                )

    def test_unknown_prompt_field_rejected(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["plane"] = "official_route_results"
        with self.assertRaises(UnknownPromptRecordField):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )

    def test_qualified_prompt_field_rejected(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["qualified"] = True
        with self.assertRaises(UnknownPromptRecordField):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )


class BoundaryNoteValidationTest(unittest.TestCase):

    def test_wrong_boundary_note_rejected(self):
        items = _build_clean_item_records()
        items[0]["boundary_notes"] = "not admitted; not qualified"
        with self.assertRaises(InvalidItemBoundaryNoteLiteral):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_empty_boundary_note_rejected(self):
        items = _build_clean_item_records()
        items[0]["boundary_notes"] = ""
        with self.assertRaises(InvalidItemBoundaryNoteLiteral):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )


class SourceIdValidationTest(unittest.TestCase):

    def test_unknown_source_id_rejected(self):
        items = _build_clean_item_records()
        items[0]["source_id"] = "L0-SRC-999"
        with self.assertRaises(UnknownSourceId):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )


class PromptCategoryValidationTest(unittest.TestCase):

    def test_unknown_prompt_category_rejected(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["category"] = "Z. unknown category"
        with self.assertRaises(UnknownPromptCategory):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )


class CoverageValidationTest(unittest.TestCase):

    def test_missing_source_id_coverage_rejected(self):
        items = _build_clean_item_records()
        for record in items:
            if record["source_id"] == "L0-SRC-007":
                record["source_id"] = "L0-SRC-001"
        with self.assertRaises(MissingSourceIdCoverage):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_missing_prompt_category_coverage_rejected(self):
        prompts = _build_clean_prompt_records()
        target = "I. workflow involving L0-SRC-006"
        replacement = "A. clear single-intent"
        for record in prompts:
            if record["category"] == target:
                record["category"] = replacement
        with self.assertRaises(MissingPromptCategoryCoverage):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )


class ForbiddenLanguageTest(unittest.TestCase):

    def test_forbidden_phrase_in_item_title_rejected(self):
        items = _build_clean_item_records()
        items[0]["item_title_or_anchor"] = "the recommended slot"
        with self.assertRaises(ForbiddenLanguageInLevel0ManualSeedReport):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_forbidden_phrase_in_prompt_expected_summary_rejected(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["expected_behavior_summary"] = "best observation"
        with self.assertRaises(ForbiddenLanguageInLevel0ManualSeedReport):
            run_level0_manual_seed_visible_report(
                _build_clean_item_records(), prompts, EventLog()
            )

    def test_forbidden_phrase_winning_in_input_rejected(self):
        items = _build_clean_item_records()
        items[0]["intended_test_role"] = "winning slot description"
        with self.assertRaises(ForbiddenLanguageInLevel0ManualSeedReport):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )

    def test_forbidden_claim_phrase_in_input_rejected(self):
        items = _build_clean_item_records()
        items[0]["intended_test_role"] = (
            "demonstrates validation evidence pattern"
        )
        with self.assertRaises(ForbiddenLanguageInLevel0ManualSeedReport):
            run_level0_manual_seed_visible_report(
                items, _build_clean_prompt_records(), EventLog()
            )


class InputIsolationTest(unittest.TestCase):

    def test_input_records_not_mutated_on_clean_pass(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        items_snapshot = [dict(record) for record in items]
        prompts_snapshot = [dict(record) for record in prompts]
        run_level0_manual_seed_visible_report(items, prompts, EventLog())
        self.assertEqual(items, items_snapshot)
        self.assertEqual(prompts, prompts_snapshot)


class StaticScanTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_manual_seed_visible_report.py",
        )
        with open(module_path, "rb") as handle:
            cls.module_source = handle.read().decode("ascii")

    def test_module_source_has_no_file_io_tokens(self):
        forbidden = ("open(", "pathlib")
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not contain '{0}'".format(token),
            )

    def test_module_source_has_no_network_tokens(self):
        forbidden = ("urllib", "http.client", "socket")
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not contain '{0}'".format(token),
            )

    def test_module_source_has_no_http_library_tokens(self):
        forbidden = ("import requests", "from requests", "requests.")
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not contain '{0}'".format(token),
            )

    def test_module_source_has_no_subprocess_or_shell_tokens(self):
        forbidden = ("subprocess", "os.system", "shutil")
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not contain '{0}'".format(token),
            )

    def test_module_source_has_no_hashlib_tokens(self):
        forbidden = ("hashlib", ".hexdigest", ".sha256")
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not contain '{0}'".format(token),
            )

    def test_module_source_has_no_retrieval_verb_tokens(self):
        forbidden = ("def query", "def search", "def retrieve", "def rank")
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not contain '{0}'".format(token),
            )

    def test_module_source_has_no_external_integration_tokens(self):
        forbidden = (
            "copilot", "waza", "vscode", "vs_code",
            "openai", "anthropic", "claude_api", "llm",
        )
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source.lower(),
                "module source must not contain '{0}'".format(token),
            )

    def test_module_does_not_invoke_prior_wo_public_functions(self):
        forbidden = (
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
        )
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not invoke '{0}'".format(token),
            )


if __name__ == "__main__":
    unittest.main()
