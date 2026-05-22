"""Tests for `harness.level0_manual_seed_end_to_end_trace`.

Tests construct synthetic in-memory `item_records` and
`prompt_records` matching the WO-L0-RUN-01 validator's shape
contract, invoke the consolidated end-to-end runner, and verify the
embedded materialization observation, embedded trace execution
observation, attached source counts, and aggregate per-prompt
summary.

These tests do not read any planning document at runtime. They do
not perform file IO, network calls, URL fetches, PDF reads, or
hash computation.
"""

import os
import unittest
from unittest.mock import patch

from harness.event_log import EventLog
from harness.level0_manual_seed_end_to_end_trace import (
    ALLOWED_OUTPUT_KEYS,
    ForbiddenLanguageInLevel0EndToEndTrace,
    MaterializationReturnedInvalidShape,
    PromptExpectedSourceTouchInvalid,
    TraceCaseSourceAttachmentEmpty,
    run_level0_manual_seed_end_to_end_trace,
)
from harness.level0_manual_seed_visible_report import ITEM_BOUNDARY_NOTE


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


class CleanPassTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.event_log = EventLog()
        self.result = run_level0_manual_seed_end_to_end_trace(
            self.items, self.prompts, self.event_log
        )

    def test_clean_pass_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_clean_pass_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_clean_pass_end_to_end_kind(self):
        self.assertEqual(
            self.result["end_to_end_kind"],
            "level0_manual_seed_end_to_end_trace",
        )

    def test_clean_pass_trace_case_count_is_23(self):
        self.assertEqual(self.result["trace_case_count"], 23)

    def test_clean_pass_visible_report_count_is_23(self):
        self.assertEqual(self.result["visible_report_count"], 23)

    def test_clean_pass_source_counts_are_65(self):
        self.assertEqual(self.result["source_reference_count"], 65)
        self.assertEqual(self.result["source_record_count"], 65)

    def test_clean_pass_per_prompt_summary_has_23_entries(self):
        self.assertEqual(len(self.result["per_prompt_trace_summary"]), 23)

    def test_clean_pass_four_booleans_literal_false(self):
        self.assertIs(self.result["selection_made"], False)
        self.assertIs(self.result["measurement_authorized"], False)
        self.assertIs(self.result["real_benchmark_authorized"], False)
        self.assertIs(self.result["real_benchmark_ready"], False)

    def test_clean_pass_end_to_end_note_non_empty(self):
        self.assertIsInstance(self.result["end_to_end_note"], str)
        self.assertGreater(len(self.result["end_to_end_note"]), 0)

    def test_clean_pass_started_and_completed_events_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn("level0_manual_seed_end_to_end_trace_started", types)
        self.assertIn("level0_manual_seed_end_to_end_trace_completed", types)

    def test_clean_pass_no_halt_event(self):
        self.assertFalse(self.event_log.has_halt())


class EmbeddedObservationTest(unittest.TestCase):

    def setUp(self):
        self.result = run_level0_manual_seed_end_to_end_trace(
            _build_clean_item_records(),
            _build_clean_prompt_records(),
            EventLog(),
        )

    def test_materialization_observation_embedded(self):
        observation = self.result["materialization_observation"]
        self.assertIsInstance(observation, dict)
        self.assertEqual(observation["source_reference_count"], 65)
        self.assertEqual(observation["source_record_count"], 65)
        self.assertEqual(len(observation["source_reference_records"]), 65)
        self.assertEqual(len(observation["source_records"]), 65)

    def test_trace_execution_observation_embedded(self):
        observation = self.result["trace_execution_observation"]
        self.assertIsInstance(observation, dict)
        self.assertEqual(observation["trace_case_count"], 23)
        self.assertEqual(observation["visible_report_count"], 23)
        self.assertEqual(len(observation["visible_reports"]), 23)


class DelegateOrderTest(unittest.TestCase):

    def test_materialization_invoked_before_trace_execution(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        original_mat = run_level0_manual_seed_end_to_end_trace.__globals__[
            "run_level0_manual_seed_materialization"
        ]
        original_trace = run_level0_manual_seed_end_to_end_trace.__globals__[
            "run_level0_manual_seed_trace_execution"
        ]
        call_order = []

        def wrapped_mat(*args, **kwargs):
            call_order.append("materialization")
            return original_mat(*args, **kwargs)

        def wrapped_trace(*args, **kwargs):
            call_order.append("trace_execution")
            return original_trace(*args, **kwargs)

        with patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_materialization",
            wrapped_mat,
        ), patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_trace_execution",
            wrapped_trace,
        ):
            run_level0_manual_seed_end_to_end_trace(items, prompts, EventLog())

        self.assertEqual(call_order, ["materialization", "trace_execution"])


class PerPromptSummaryTest(unittest.TestCase):

    def setUp(self):
        self.result = run_level0_manual_seed_end_to_end_trace(
            _build_clean_item_records(),
            _build_clean_prompt_records(),
            EventLog(),
        )

    def test_summary_entries_carry_expected_fields(self):
        required = {
            "prompt_id", "category", "case_id",
            "source_reference_count", "source_record_count",
            "linked_source_count",
            "candidate_route_fragment_count",
            "candidate_workflow_fragment_count",
            "review_halt_required",
        }
        for entry in self.result["per_prompt_trace_summary"]:
            self.assertEqual(set(entry.keys()), required)

    def test_summary_preserves_prompt_order(self):
        prompts = _build_clean_prompt_records()
        for prompt, entry in zip(prompts, self.result["per_prompt_trace_summary"]):
            self.assertEqual(entry["prompt_id"], prompt["prompt_id"])
            self.assertEqual(entry["category"], prompt["category"])

    def test_summary_case_ids_unique_and_prefixed(self):
        case_ids = [
            entry["case_id"] for entry in self.result["per_prompt_trace_summary"]
        ]
        self.assertEqual(len(case_ids), len(set(case_ids)))
        for case_id in case_ids:
            self.assertTrue(case_id.startswith("L0-E2E-CASE-"))


class SourceTouchFilteringTest(unittest.TestCase):

    def test_single_valid_token_attaches_matching_subset(self):
        # Default helper uses "L0-SRC-001" for all prompts; L0-SRC-001
        # has 12 items.
        result = run_level0_manual_seed_end_to_end_trace(
            _build_clean_item_records(),
            _build_clean_prompt_records(),
            EventLog(),
        )
        for entry in result["per_prompt_trace_summary"]:
            self.assertEqual(entry["source_reference_count"], 12)
            self.assertEqual(entry["source_record_count"], 12)

    def test_multi_token_attaches_union(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        # L0-SRC-001 (12) + L0-SRC-006 (11) = 23 attached records.
        prompts[0]["expected_source_touch"] = "L0-SRC-001; L0-SRC-006"
        result = run_level0_manual_seed_end_to_end_trace(
            items, prompts, EventLog()
        )
        self.assertEqual(
            result["per_prompt_trace_summary"][0]["source_reference_count"], 23
        )
        # Other prompts unchanged.
        self.assertEqual(
            result["per_prompt_trace_summary"][1]["source_reference_count"], 12
        )

    def test_prose_only_falls_back_to_all_sources(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        prompts[0]["expected_source_touch"] = "all inventory sources"
        result = run_level0_manual_seed_end_to_end_trace(
            items, prompts, EventLog()
        )
        self.assertEqual(
            result["per_prompt_trace_summary"][0]["source_reference_count"], 65
        )

    def test_unknown_token_rejected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        prompts[0]["expected_source_touch"] = "L0-SRC-999"
        with self.assertRaises(PromptExpectedSourceTouchInvalid):
            run_level0_manual_seed_end_to_end_trace(
                items, prompts, EventLog()
            )


class EmptyAttachmentTest(unittest.TestCase):

    def test_empty_attachment_halts_before_trace_execution(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        def mock_materialization(item_records, prompt_records, event_log):
            return {
                "manual_seed_shape_observation": {"item_count": 65},
                "source_reference_records": [],
                "source_records": [],
                "source_reference_count": 0,
                "source_record_count": 0,
            }

        with patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_materialization",
            mock_materialization,
        ), patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_trace_execution"
        ) as mock_trace:
            with self.assertRaises(TraceCaseSourceAttachmentEmpty):
                run_level0_manual_seed_end_to_end_trace(
                    items, prompts, EventLog()
                )
            mock_trace.assert_not_called()


class MaterializationShapeValidationTest(unittest.TestCase):

    def test_materialization_returning_non_dict_rejected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        with patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_materialization",
            lambda *a, **kw: "not a dict",
        ):
            with self.assertRaises(MaterializationReturnedInvalidShape):
                run_level0_manual_seed_end_to_end_trace(
                    items, prompts, EventLog()
                )

    def test_materialization_missing_required_key_rejected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        with patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_materialization",
            lambda *a, **kw: {"source_reference_records": []},
        ):
            with self.assertRaises(MaterializationReturnedInvalidShape):
                run_level0_manual_seed_end_to_end_trace(
                    items, prompts, EventLog()
                )

    def test_materialization_reference_count_mismatch_rejected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        with patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_materialization",
            lambda *a, **kw: {
                "manual_seed_shape_observation": {"item_count": 65},
                "source_reference_records": [{"source_id": "L0-MAT-SRC-001"}],
                "source_records": [{"source_id": "L0-MAT-SRC-001"}],
                "source_reference_count": 2,
                "source_record_count": 1,
            },
        ):
            with self.assertRaises(MaterializationReturnedInvalidShape):
                run_level0_manual_seed_end_to_end_trace(
                    items, prompts, EventLog()
                )

    def test_materialization_record_count_mismatch_rejected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        with patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_materialization",
            lambda *a, **kw: {
                "manual_seed_shape_observation": {"item_count": 65},
                "source_reference_records": [{"source_id": "L0-MAT-SRC-001"}],
                "source_records": [{"source_id": "L0-MAT-SRC-001"}],
                "source_reference_count": 1,
                "source_record_count": 2,
            },
        ):
            with self.assertRaises(MaterializationReturnedInvalidShape):
                run_level0_manual_seed_end_to_end_trace(
                    items, prompts, EventLog()
                )

    def test_materialization_pair_count_mismatch_rejected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        with patch(
            "harness.level0_manual_seed_end_to_end_trace.run_level0_manual_seed_materialization",
            lambda *a, **kw: {
                "manual_seed_shape_observation": {"item_count": 65},
                "source_reference_records": [{"source_id": "L0-MAT-SRC-001"}],
                "source_records": [
                    {"source_id": "L0-MAT-SRC-001"},
                    {"source_id": "L0-MAT-SRC-002"},
                ],
                "source_reference_count": 1,
                "source_record_count": 2,
            },
        ):
            with self.assertRaises(MaterializationReturnedInvalidShape):
                run_level0_manual_seed_end_to_end_trace(
                    items, prompts, EventLog()
                )


class AggregateCountsTest(unittest.TestCase):

    def setUp(self):
        self.result = run_level0_manual_seed_end_to_end_trace(
            _build_clean_item_records(),
            _build_clean_prompt_records(),
            EventLog(),
        )

    def test_candidate_route_fragment_total_matches_visible_reports(self):
        expected = sum(
            r["trace_candidate_route_fragment_count"]
            for r in self.result["trace_execution_observation"]["visible_reports"]
        )
        self.assertEqual(self.result["candidate_route_fragment_total"], expected)

    def test_candidate_workflow_fragment_total_matches_visible_reports(self):
        expected = sum(
            r["trace_candidate_workflow_fragment_count"]
            for r in self.result["trace_execution_observation"]["visible_reports"]
        )
        self.assertEqual(
            self.result["candidate_workflow_fragment_total"], expected
        )

    def test_review_halt_required_count_matches_trace_execution(self):
        self.assertEqual(
            self.result["review_halt_required_count"],
            self.result["trace_execution_observation"]["review_halt_required_count"],
        )


class InputIsolationTest(unittest.TestCase):

    def test_input_records_not_mutated_on_clean_pass(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        items_snapshot = [dict(record) for record in items]
        prompts_snapshot = [dict(record) for record in prompts]
        run_level0_manual_seed_end_to_end_trace(items, prompts, EventLog())
        self.assertEqual(items, items_snapshot)
        self.assertEqual(prompts, prompts_snapshot)


class ForbiddenLanguageOutputTest(unittest.TestCase):

    def test_end_to_end_note_is_forbidden_language_clean(self):
        result = run_level0_manual_seed_end_to_end_trace(
            _build_clean_item_records(),
            _build_clean_prompt_records(),
            EventLog(),
        )
        note_lower = result["end_to_end_note"].lower()
        for phrase in (
            "recommend", "recommended", "best", "winner", "winning",
            "production-ready", "production ready", "rank", "ranked", "ranking",
        ):
            self.assertNotIn(phrase, note_lower)


class StaticScanTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_manual_seed_end_to_end_trace.py",
        )
        with open(module_path, "rb") as handle:
            cls.module_source = handle.read().decode("ascii")

    def test_no_file_io_tokens(self):
        for token in ("open(", "pathlib"):
            self.assertNotIn(token, self.module_source)

    def test_no_network_tokens(self):
        for token in ("urllib", "http.client", "socket"):
            self.assertNotIn(token, self.module_source)

    def test_no_http_library_tokens(self):
        for token in ("import requests", "from requests", "requests."):
            self.assertNotIn(token, self.module_source)

    def test_no_subprocess_or_shell_tokens(self):
        for token in ("subprocess", "os.system", "shutil"):
            self.assertNotIn(token, self.module_source)

    def test_no_hashlib_tokens(self):
        for token in ("hashlib", ".hexdigest", ".sha256"):
            self.assertNotIn(token, self.module_source)

    def test_no_browser_automation_tokens(self):
        for token in ("selenium", "playwright", "webdriver", "puppeteer"):
            self.assertNotIn(token, self.module_source.lower())

    def test_no_pdf_extraction_tokens(self):
        for token in ("pypdf", "pdfminer", "pdfplumber", "fitz", "pdftotext"):
            self.assertNotIn(token, self.module_source.lower())

    def test_no_retrieval_verb_tokens(self):
        for token in ("def query", "def search", "def retrieve", "def rank"):
            self.assertNotIn(token, self.module_source)

    def test_no_external_integration_tokens(self):
        for token in (
            "copilot", "waza", "vscode", "vs_code",
            "openai", "anthropic", "claude_api", "llm",
        ):
            self.assertNotIn(token, self.module_source.lower())

    def test_only_allowed_prior_wo_public_functions_present(self):
        # Must invoke exactly these two:
        self.assertIn(
            "run_level0_manual_seed_materialization", self.module_source
        )
        self.assertIn(
            "run_level0_manual_seed_trace_execution", self.module_source
        )

    def test_no_other_prior_wo_public_functions_present(self):
        for token in (
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
        ):
            self.assertNotIn(
                token, self.module_source,
                "module source must not invoke '{0}'".format(token),
            )


if __name__ == "__main__":
    unittest.main()
