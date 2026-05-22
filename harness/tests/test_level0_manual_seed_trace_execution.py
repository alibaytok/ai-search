"""Tests for `harness.level0_manual_seed_trace_execution`.

Tests construct synthetic in-memory `item_records`, `prompt_records`,
and `trace_case_records` that match the structural shapes required
by the WO-L0-RUN-01 manual seed validator and the WO-L0-TRACE-01
trace executor. Trace cases carry empty `source_reference_records`
and `source_records` lists (which WO-59 accepts) so the WO-59
visible-report path emits clean-pass observations.

These tests do not read any planning document at runtime. They do
not perform file IO, network calls, URL fetches, PDF reads, or hash
computation. The two prior-WO public functions invoked at runtime
are exactly those authorized by the WO-L0-TRACE-01 packet:
`run_level0_manual_seed_visible_report` and
`run_scaffold_source_intake_visible_report`.
"""

import os
import unittest
from unittest.mock import patch

from harness.event_log import EventLog
from harness.level0_manual_seed_visible_report import (
    InvalidItemRecordCount,
    ITEM_BOUNDARY_NOTE,
)
from harness.level0_manual_seed_trace_execution import (
    ALLOWED_OUTPUT_KEYS,
    DuplicateCaseId,
    DuplicatePromptIdReference,
    EXPECTED_TRACE_CASE_COUNT,
    ForbiddenLanguageInLevel0ManualSeedTraceExecution,
    InvalidCaseIdValue,
    InvalidTraceCaseBoundaryNoteLiteral,
    InvalidTraceCaseCount,
    MissingTraceCaseField,
    NonListCaseSourceReferenceRecords,
    NonListCaseSourceRecords,
    NonListTraceCaseRecords,
    NonObjectTraceCaseRecord,
    REQUIRED_TRACE_CASE_FIELDS,
    TRACE_CASE_BOUNDARY_NOTE,
    TraceCaseCategoryMismatch,
    TraceCaseInputPromptMismatch,
    UnknownPromptIdReference,
    UnknownTraceCaseField,
    run_level0_manual_seed_trace_execution,
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


def _build_clean_trace_case_records(prompt_records):
    cases = []
    for idx, prompt in enumerate(prompt_records, start=1):
        cases.append({
            "case_id": "L0-TRACE-{0:03d}".format(idx),
            "prompt_id": prompt["prompt_id"],
            "expected_category": prompt["category"],
            "input_prompt": prompt["prompt_text"],
            "source_reference_records": [],
            "source_records": [],
            "expected_source_touch": prompt["expected_source_touch"],
            "expected_candidate_shape": prompt["expected_candidate_shape"],
            "expected_rejection_targets": prompt["expected_rejection_targets"],
            "boundary_notes": TRACE_CASE_BOUNDARY_NOTE,
        })
    return cases


class CleanPassTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.cases = _build_clean_trace_case_records(self.prompts)
        self.event_log = EventLog()
        self.result = run_level0_manual_seed_trace_execution(
            self.items, self.prompts, self.cases, self.event_log
        )

    def test_clean_pass_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_clean_pass_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_clean_pass_execution_kind(self):
        self.assertEqual(
            self.result["execution_kind"],
            "level0_manual_seed_trace_execution",
        )

    def test_clean_pass_trace_case_count(self):
        self.assertEqual(self.result["trace_case_count"], 23)

    def test_clean_pass_visible_report_count(self):
        self.assertEqual(self.result["visible_report_count"], 23)
        self.assertEqual(len(self.result["visible_reports"]), 23)

    def test_clean_pass_manual_seed_shape_observation_present(self):
        observation = self.result["manual_seed_shape_observation"]
        self.assertIsInstance(observation, dict)
        self.assertEqual(observation["item_count"], 65)
        self.assertEqual(observation["prompt_count"], 23)
        self.assertIs(
            observation["manual_seed_ready_for_visible_trace"], True
        )

    def test_clean_pass_prompt_ids_executed_sorted_unique(self):
        executed = self.result["prompt_ids_executed"]
        self.assertEqual(len(executed), 23)
        self.assertEqual(len(set(executed)), 23)
        self.assertEqual(executed, sorted(executed))

    def test_clean_pass_category_counts_match_distribution(self):
        counts = self.result["category_counts"]
        for category, expected in _CATEGORY_DISTRIBUTION:
            self.assertEqual(counts[category], expected)
        self.assertEqual(sum(counts.values()), 23)

    def test_clean_pass_review_halt_required_count_is_zero(self):
        self.assertEqual(self.result["review_halt_required_count"], 0)

    def test_clean_pass_selection_made_is_literal_false(self):
        self.assertIs(self.result["selection_made"], False)

    def test_clean_pass_measurement_authorized_is_literal_false(self):
        self.assertIs(self.result["measurement_authorized"], False)

    def test_clean_pass_real_benchmark_authorized_is_literal_false(self):
        self.assertIs(self.result["real_benchmark_authorized"], False)

    def test_clean_pass_real_benchmark_ready_is_literal_false(self):
        self.assertIs(self.result["real_benchmark_ready"], False)

    def test_clean_pass_execution_note_non_empty(self):
        self.assertIsInstance(self.result["execution_note"], str)
        self.assertGreater(len(self.result["execution_note"]), 0)

    def test_clean_pass_each_visible_report_has_expected_shape(self):
        for report in self.result["visible_reports"]:
            self.assertIsInstance(report, dict)
            self.assertEqual(
                report["visible_report_kind"],
                "scaffold_source_intake_visible_report",
            )
            self.assertIs(report["selection_made"], False)
            self.assertIs(report["measurement_authorized"], False)
            self.assertIs(report["real_benchmark_authorized"], False)
            self.assertIs(report["real_benchmark_ready"], False)

    def test_clean_pass_started_and_completed_events_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn("level0_manual_seed_trace_execution_started", types)
        self.assertIn("level0_manual_seed_trace_execution_completed", types)

    def test_clean_pass_no_halt_event(self):
        self.assertFalse(self.event_log.has_halt())

    def test_clean_pass_visible_report_emitted_event_per_case(self):
        types = [event["type"] for event in self.event_log.events]
        emitted_count = sum(
            1 for t in types if t == "level0_manual_seed_visible_report_emitted"
        )
        self.assertEqual(emitted_count, 23)


class ShortCircuitOnSeedShapeFailureTest(unittest.TestCase):

    def test_seed_shape_failure_short_circuits_before_wo59(self):
        items = _build_clean_item_records()[:-1]
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        with patch(
            "harness.level0_manual_seed_trace_execution.run_scaffold_source_intake_visible_report"
        ) as mock_wo59:
            with self.assertRaises(InvalidItemRecordCount):
                run_level0_manual_seed_trace_execution(
                    items, prompts, cases, EventLog()
                )
            mock_wo59.assert_not_called()

    def test_seed_shape_failure_short_circuits_before_trace_case_validation(self):
        items = _build_clean_item_records()[:-1]
        prompts = _build_clean_prompt_records()
        # Trace cases are entirely malformed; should never be reached.
        with self.assertRaises(InvalidItemRecordCount):
            run_level0_manual_seed_trace_execution(
                items, prompts, "not a list", EventLog()
            )


class DelegateOrderTest(unittest.TestCase):

    def test_seed_validator_invoked_before_wo59(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)

        call_order = []

        original_seed = run_level0_manual_seed_trace_execution.__globals__[
            "run_level0_manual_seed_visible_report"
        ]
        original_wo59 = run_level0_manual_seed_trace_execution.__globals__[
            "run_scaffold_source_intake_visible_report"
        ]

        def wrapped_seed(*args, **kwargs):
            call_order.append("seed")
            return original_seed(*args, **kwargs)

        def wrapped_wo59(*args, **kwargs):
            call_order.append("wo59")
            return original_wo59(*args, **kwargs)

        with patch(
            "harness.level0_manual_seed_trace_execution.run_level0_manual_seed_visible_report",
            wrapped_seed,
        ), patch(
            "harness.level0_manual_seed_trace_execution.run_scaffold_source_intake_visible_report",
            wrapped_wo59,
        ):
            run_level0_manual_seed_trace_execution(
                items, prompts, cases, EventLog()
            )

        self.assertEqual(call_order[0], "seed")
        # Seed validator called exactly once.
        self.assertEqual(call_order.count("seed"), 1)
        # WO-59 called exactly 23 times.
        self.assertEqual(call_order.count("wo59"), 23)


class TraceCaseTypeValidationTest(unittest.TestCase):

    def test_non_list_trace_case_records_rejected(self):
        with self.assertRaises(NonListTraceCaseRecords):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(),
                _build_clean_prompt_records(),
                "not a list",
                EventLog(),
            )

    def test_dict_trace_case_records_rejected(self):
        with self.assertRaises(NonListTraceCaseRecords):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(),
                _build_clean_prompt_records(),
                {"k": "v"},
                EventLog(),
            )

    def test_none_trace_case_records_rejected(self):
        with self.assertRaises(NonListTraceCaseRecords):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(),
                _build_clean_prompt_records(),
                None,
                EventLog(),
            )


class TraceCaseCountValidationTest(unittest.TestCase):

    def test_too_few_trace_cases_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)[:-1]
        with self.assertRaises(InvalidTraceCaseCount):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_too_many_trace_cases_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases.append(dict(cases[0]))
        with self.assertRaises(InvalidTraceCaseCount):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_empty_trace_cases_rejected(self):
        with self.assertRaises(InvalidTraceCaseCount):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(),
                _build_clean_prompt_records(),
                [],
                EventLog(),
            )


class TraceCaseFieldValidationTest(unittest.TestCase):

    def test_non_dict_trace_case_record_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0] = "not a dict"
        with self.assertRaises(NonObjectTraceCaseRecord):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def _run_with_missing_case_field(self, field):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        del cases[0][field]
        with self.assertRaises(MissingTraceCaseField):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_missing_case_id_rejected(self):
        self._run_with_missing_case_field("case_id")

    def test_missing_prompt_id_rejected(self):
        self._run_with_missing_case_field("prompt_id")

    def test_missing_expected_category_rejected(self):
        self._run_with_missing_case_field("expected_category")

    def test_missing_input_prompt_rejected(self):
        self._run_with_missing_case_field("input_prompt")

    def test_missing_source_reference_records_rejected(self):
        self._run_with_missing_case_field("source_reference_records")

    def test_missing_source_records_rejected(self):
        self._run_with_missing_case_field("source_records")

    def test_missing_expected_source_touch_rejected(self):
        self._run_with_missing_case_field("expected_source_touch")

    def test_missing_expected_candidate_shape_rejected(self):
        self._run_with_missing_case_field("expected_candidate_shape")

    def test_missing_expected_rejection_targets_rejected(self):
        self._run_with_missing_case_field("expected_rejection_targets")

    def test_missing_boundary_notes_rejected(self):
        self._run_with_missing_case_field("boundary_notes")

    def test_every_required_trace_case_field_is_checked(self):
        for field in REQUIRED_TRACE_CASE_FIELDS:
            prompts = _build_clean_prompt_records()
            cases = _build_clean_trace_case_records(prompts)
            del cases[0][field]
            with self.assertRaises(MissingTraceCaseField):
                run_level0_manual_seed_trace_execution(
                    _build_clean_item_records(), prompts, cases, EventLog()
                )


class UnknownTraceCaseFieldTest(unittest.TestCase):

    def test_extra_field_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["extra_field"] = "should not be here"
        with self.assertRaises(UnknownTraceCaseField):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class CaseIdValidationTest(unittest.TestCase):

    def test_empty_case_id_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["case_id"] = ""
        with self.assertRaises(InvalidCaseIdValue):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_non_string_case_id_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["case_id"] = 12345
        with self.assertRaises(InvalidCaseIdValue):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_duplicate_case_id_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[1]["case_id"] = cases[0]["case_id"]
        with self.assertRaises(DuplicateCaseId):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class PromptIdReferenceTest(unittest.TestCase):

    def test_unknown_prompt_id_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["prompt_id"] = "L0-PRM-999"
        with self.assertRaises(UnknownPromptIdReference):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_duplicate_prompt_id_reference_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        # Point case[1] at the same prompt as case[0]; update expected
        # values to satisfy the per-case match check so the duplicate
        # check is the actual trigger.
        first = cases[0]
        cases[1]["prompt_id"] = first["prompt_id"]
        cases[1]["expected_category"] = first["expected_category"]
        cases[1]["input_prompt"] = first["input_prompt"]
        with self.assertRaises(DuplicatePromptIdReference):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class CategoryMismatchTest(unittest.TestCase):

    def test_category_mismatch_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["expected_category"] = "Z. some other category"
        with self.assertRaises(TraceCaseCategoryMismatch):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class InputPromptMismatchTest(unittest.TestCase):

    def test_input_prompt_mismatch_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["input_prompt"] = "a different synthetic prompt"
        with self.assertRaises(TraceCaseInputPromptMismatch):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class BoundaryNoteValidationTest(unittest.TestCase):

    def test_wrong_boundary_note_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["boundary_notes"] = "not admitted; not qualified"
        with self.assertRaises(InvalidTraceCaseBoundaryNoteLiteral):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_empty_boundary_note_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["boundary_notes"] = ""
        with self.assertRaises(InvalidTraceCaseBoundaryNoteLiteral):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class SourceListTypeTest(unittest.TestCase):

    def test_non_list_source_reference_records_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["source_reference_records"] = "not a list"
        with self.assertRaises(NonListCaseSourceReferenceRecords):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_non_list_source_records_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["source_records"] = {"not": "a list"}
        with self.assertRaises(NonListCaseSourceRecords):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class ForbiddenLanguageTest(unittest.TestCase):

    def test_forbidden_phrase_in_case_field_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["expected_source_touch"] = "the best touch"
        with self.assertRaises(ForbiddenLanguageInLevel0ManualSeedTraceExecution):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )

    def test_forbidden_claim_phrase_in_case_field_rejected(self):
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        cases[0]["expected_candidate_shape"] = "demonstrates validation evidence"
        with self.assertRaises(ForbiddenLanguageInLevel0ManualSeedTraceExecution):
            run_level0_manual_seed_trace_execution(
                _build_clean_item_records(), prompts, cases, EventLog()
            )


class InputIsolationTest(unittest.TestCase):

    def test_input_records_not_mutated_on_clean_pass(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        cases = _build_clean_trace_case_records(prompts)
        items_snapshot = [dict(record) for record in items]
        prompts_snapshot = [dict(record) for record in prompts]
        cases_snapshot = [dict(record) for record in cases]
        run_level0_manual_seed_trace_execution(
            items, prompts, cases, EventLog()
        )
        self.assertEqual(items, items_snapshot)
        self.assertEqual(prompts, prompts_snapshot)
        self.assertEqual(cases, cases_snapshot)


class StaticScanTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_manual_seed_trace_execution.py",
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

    def test_module_source_has_no_browser_automation_tokens(self):
        forbidden = ("selenium", "playwright", "webdriver", "puppeteer")
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source.lower(),
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

    def test_module_invokes_only_allowed_prior_wo_public_functions(self):
        allowed = (
            "run_level0_manual_seed_visible_report",
            "run_scaffold_source_intake_visible_report",
        )
        for token in allowed:
            self.assertIn(
                token, self.module_source,
                "module source must invoke '{0}'".format(token),
            )

    def test_module_does_not_invoke_other_prior_wo_public_functions(self):
        forbidden = (
            "run_scaffold_route_query_probe",
            "run_scaffold_route_query_ambiguity_probe",
            "run_scaffold_conflicting_evidence_guard",
            "run_scaffold_source_intake_trace",
            "run_scaffold_source_intake_register",
            "run_scaffold_source_trace_admission_bridge",
            "run_scaffold_source_intake_smoke_package",
            "run_scaffold_route_invariant_diagnostic_reporter",
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
