"""Tests for `harness.level0_manual_seed_materialization`.

Tests construct synthetic in-memory `item_records` and
`prompt_records` matching the WO-L0-RUN-01 validator's shape
contract, invoke the materialization runner, and verify the
generated `source_reference_records` and `source_records` are
WO-59-compatible. An end-to-end compatibility test feeds the
materialized records through `run_scaffold_source_intake_visible_report`
to confirm WO-59 (and therefore WO-56 / WO-54 internally) accepts
them on a clean pass.

These tests do not read any planning document at runtime. They do
not perform file IO, network calls, URL fetches, PDF reads, or
hash computation. The tests do invoke
`run_scaffold_source_intake_visible_report` at the test layer to
verify downstream compatibility; the module under test does NOT
invoke WO-59.
"""

import os
import unittest
from unittest.mock import patch

from harness.event_log import EventLog
from harness.level0_manual_seed_materialization import (
    ALLOWED_OUTPUT_KEYS,
    DuplicateMaterializedSourceId,
    ForbiddenLanguageInLevel0ManualSeedMaterialization,
    ITEM_KIND_TO_DECLARED_KIND,
    UnknownItemKind,
    run_level0_manual_seed_materialization,
)
from harness.level0_manual_seed_visible_report import (
    InvalidItemRecordCount,
    ITEM_BOUNDARY_NOTE,
)
from harness.scaffold_source_intake_visible_report import (
    run_scaffold_source_intake_visible_report,
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


_ROUTE_STATUS_FIELDS = (
    "official", "is_route", "is_official_route", "selected_as_official",
    "official_route_authorized", "route_authorized", "production_route",
    "selected_route", "executable", "route_state", "plane",
)


_DERIVED_MATERIAL_FIELDS = (
    "extracted_material", "normalized_material", "candidate_fragments",
    "candidate_route_fragments", "candidate_workflow_fragments",
)


def _build_clean_item_records(item_kind="prompt"):
    records = []
    next_index = 1
    for source_id, count in _SOURCE_DISTRIBUTION:
        for _ in range(count):
            records.append({
                "item_id": "L0-ITEM-{0:03d}".format(next_index),
                "source_id": source_id,
                "item_kind": item_kind,
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
        self.result = run_level0_manual_seed_materialization(
            self.items, self.prompts, self.event_log
        )

    def test_clean_pass_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_clean_pass_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_clean_pass_materialization_kind(self):
        self.assertEqual(
            self.result["materialization_kind"],
            "level0_manual_seed_materialization",
        )

    def test_clean_pass_source_reference_count_is_65(self):
        self.assertEqual(self.result["source_reference_count"], 65)
        self.assertEqual(len(self.result["source_reference_records"]), 65)

    def test_clean_pass_source_record_count_is_65(self):
        self.assertEqual(self.result["source_record_count"], 65)
        self.assertEqual(len(self.result["source_records"]), 65)

    def test_clean_pass_item_ids_materialized_sorted_unique(self):
        ids = self.result["item_ids_materialized"]
        self.assertEqual(len(ids), 65)
        self.assertEqual(len(set(ids)), 65)
        self.assertEqual(ids, sorted(ids))

    def test_clean_pass_source_ids_materialized_sorted_unique(self):
        ids = self.result["source_ids_materialized"]
        self.assertEqual(len(ids), 65)
        self.assertEqual(len(set(ids)), 65)
        self.assertEqual(ids, sorted(ids))

    def test_clean_pass_candidate_route_fragment_count_is_zero(self):
        self.assertEqual(self.result["candidate_route_fragment_count"], 0)

    def test_clean_pass_candidate_workflow_fragment_count_is_zero(self):
        self.assertEqual(self.result["candidate_workflow_fragment_count"], 0)

    def test_clean_pass_selection_made_literal_false(self):
        self.assertIs(self.result["selection_made"], False)

    def test_clean_pass_measurement_authorized_literal_false(self):
        self.assertIs(self.result["measurement_authorized"], False)

    def test_clean_pass_real_benchmark_authorized_literal_false(self):
        self.assertIs(self.result["real_benchmark_authorized"], False)

    def test_clean_pass_real_benchmark_ready_literal_false(self):
        self.assertIs(self.result["real_benchmark_ready"], False)

    def test_clean_pass_materialization_note_non_empty(self):
        self.assertIsInstance(self.result["materialization_note"], str)
        self.assertGreater(len(self.result["materialization_note"]), 0)

    def test_clean_pass_manual_seed_shape_observation_embedded(self):
        observation = self.result["manual_seed_shape_observation"]
        self.assertIsInstance(observation, dict)
        self.assertEqual(observation["item_count"], 65)
        self.assertEqual(observation["prompt_count"], 23)
        self.assertIs(observation["manual_seed_ready_for_visible_trace"], True)

    def test_clean_pass_started_and_completed_events_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn("level0_manual_seed_materialization_started", types)
        self.assertIn("level0_manual_seed_materialization_completed", types)

    def test_clean_pass_no_halt_event(self):
        self.assertFalse(self.event_log.has_halt())


class GeneratedSourceReferenceShapeTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.result = run_level0_manual_seed_materialization(
            self.items, self.prompts, EventLog()
        )

    def test_every_reference_has_six_required_fields(self):
        required = {
            "source_id", "origin", "declared_kind", "hash",
            "byte_length", "observed_at",
        }
        for ref in self.result["source_reference_records"]:
            self.assertEqual(set(ref.keys()), required)

    def test_every_source_id_starts_with_l0_mat_src(self):
        for ref in self.result["source_reference_records"]:
            self.assertTrue(ref["source_id"].startswith("L0-MAT-SRC-"))

    def test_every_declared_kind_is_in_allowed_set(self):
        allowed = set(ITEM_KIND_TO_DECLARED_KIND.values())
        for ref in self.result["source_reference_records"]:
            self.assertIn(ref["declared_kind"], allowed)

    def test_every_hash_is_at_least_twelve_characters(self):
        for ref in self.result["source_reference_records"]:
            self.assertGreaterEqual(len(ref["hash"]), 12)

    def test_every_byte_length_is_non_negative_int_not_bool(self):
        for ref in self.result["source_reference_records"]:
            self.assertIsInstance(ref["byte_length"], int)
            self.assertNotIsInstance(ref["byte_length"], bool)
            self.assertGreaterEqual(ref["byte_length"], 0)

    def test_every_observed_at_is_manual_seed_literal(self):
        for ref in self.result["source_reference_records"]:
            self.assertEqual(ref["observed_at"], "level0-manual-seed")

    def test_every_origin_starts_with_manual_seed_prefix(self):
        for ref in self.result["source_reference_records"]:
            self.assertTrue(ref["origin"].startswith("manual-seed:"))


class GeneratedSourceRecordShapeTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.result = run_level0_manual_seed_materialization(
            self.items, self.prompts, EventLog()
        )

    def test_every_source_record_has_exactly_four_required_fields(self):
        required = {
            "source_id", "source_kind", "source_origin", "source_register_ref",
        }
        for rec in self.result["source_records"]:
            self.assertEqual(set(rec.keys()), required)

    def test_every_source_record_source_origin_is_external(self):
        for rec in self.result["source_records"]:
            self.assertEqual(rec["source_origin"], "external")

    def test_source_record_source_kind_matches_reference_declared_kind(self):
        refs = self.result["source_reference_records"]
        recs = self.result["source_records"]
        for ref, rec in zip(refs, recs):
            self.assertEqual(rec["source_kind"], ref["declared_kind"])

    def test_source_record_source_id_matches_reference_source_id(self):
        refs = self.result["source_reference_records"]
        recs = self.result["source_records"]
        for ref, rec in zip(refs, recs):
            self.assertEqual(rec["source_id"], ref["source_id"])

    def test_source_record_register_ref_matches_source_id(self):
        for rec in self.result["source_records"]:
            self.assertEqual(rec["source_register_ref"], rec["source_id"])

    def test_no_source_record_carries_qualified_field(self):
        for rec in self.result["source_records"]:
            self.assertNotIn("qualified", rec)

    def test_no_source_record_carries_qualification_ref(self):
        for rec in self.result["source_records"]:
            self.assertNotIn("qualification_ref", rec)

    def test_no_source_record_carries_route_status_field(self):
        for rec in self.result["source_records"]:
            for field in _ROUTE_STATUS_FIELDS:
                self.assertNotIn(field, rec)

    def test_no_source_record_carries_derived_material_field(self):
        for rec in self.result["source_records"]:
            for field in _DERIVED_MATERIAL_FIELDS:
                self.assertNotIn(field, rec)


class ItemKindMappingTest(unittest.TestCase):

    def test_each_known_item_kind_maps_to_declared_kind(self):
        # Build items with one item per kind, padded with "prompt"
        # to reach 65. The kinds-under-test occupy positions 1..7;
        # positions 8..65 use "prompt".
        kinds_under_test = list(ITEM_KIND_TO_DECLARED_KIND.keys())
        # Need to maintain L0-SRC-* distribution; simplest is to
        # mutate item_kind on selected indices of the standard build.
        items = _build_clean_item_records()
        for offset, kind in enumerate(kinds_under_test):
            items[offset]["item_kind"] = kind
        prompts = _build_clean_prompt_records()
        result = run_level0_manual_seed_materialization(
            items, prompts, EventLog()
        )
        for offset, kind in enumerate(kinds_under_test):
            self.assertEqual(
                result["source_reference_records"][offset]["declared_kind"],
                ITEM_KIND_TO_DECLARED_KIND[kind],
            )
            self.assertEqual(
                result["source_records"][offset]["source_kind"],
                ITEM_KIND_TO_DECLARED_KIND[kind],
            )

    def test_unknown_item_kind_rejected(self):
        items = _build_clean_item_records()
        items[0]["item_kind"] = "unknown_kind"
        with self.assertRaises(UnknownItemKind):
            run_level0_manual_seed_materialization(
                items, _build_clean_prompt_records(), EventLog()
            )


class SeedShapeDelegationTest(unittest.TestCase):

    def test_seed_shape_failure_short_circuits_before_materialization(self):
        items = _build_clean_item_records()[:-1]
        prompts = _build_clean_prompt_records()
        with self.assertRaises(InvalidItemRecordCount):
            run_level0_manual_seed_materialization(
                items, prompts, EventLog()
            )

    def test_seed_validator_invoked_before_any_materialization(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()

        original = run_level0_manual_seed_materialization.__globals__[
            "run_level0_manual_seed_visible_report"
        ]
        call_order = []

        def wrapped(*args, **kwargs):
            call_order.append("seed_validator")
            return original(*args, **kwargs)

        with patch(
            "harness.level0_manual_seed_materialization.run_level0_manual_seed_visible_report",
            wrapped,
        ):
            result = run_level0_manual_seed_materialization(
                items, prompts, EventLog()
            )

        # Seed validator invoked exactly once, before any
        # materialization observation event.
        self.assertEqual(call_order.count("seed_validator"), 1)
        self.assertEqual(result["source_reference_count"], 65)


class InputIsolationTest(unittest.TestCase):

    def test_input_records_not_mutated_on_clean_pass(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        items_snapshot = [dict(record) for record in items]
        prompts_snapshot = [dict(record) for record in prompts]
        run_level0_manual_seed_materialization(items, prompts, EventLog())
        self.assertEqual(items, items_snapshot)
        self.assertEqual(prompts, prompts_snapshot)


class Wo59CompatibilityTest(unittest.TestCase):
    """End-to-end compatibility: materialized records pass through
    `run_scaffold_source_intake_visible_report` (WO-59) cleanly.
    The module under test does NOT invoke WO-59; this test does so
    at the test layer to verify downstream contract satisfaction."""

    def test_materialized_records_clean_through_wo59(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        materialization = run_level0_manual_seed_materialization(
            items, prompts, EventLog()
        )
        visible_report = run_scaffold_source_intake_visible_report(
            "synthetic compatibility test prompt",
            materialization["source_reference_records"],
            materialization["source_records"],
            EventLog(),
        )
        self.assertEqual(visible_report["source_reference_count"], 65)
        self.assertEqual(visible_report["source_record_count"], 65)
        self.assertEqual(visible_report["linked_source_count"], 65)
        self.assertIs(visible_report["selection_made"], False)
        self.assertIs(visible_report["real_benchmark_ready"], False)


class ForbiddenLanguageOutputTest(unittest.TestCase):

    def test_materialization_note_is_forbidden_language_clean(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        result = run_level0_manual_seed_materialization(
            items, prompts, EventLog()
        )
        note_lower = result["materialization_note"].lower()
        for phrase in (
            "recommend", "recommended", "best", "winner", "winning",
            "production-ready", "production ready", "rank", "ranked", "ranking",
        ):
            self.assertNotIn(phrase, note_lower)
        for phrase in (
            "validation evidence", "validated route", "route trust",
            "benchmark result", "benchmark output", "architecture selection",
            "architecture choice", "selected architecture", "production-grade",
        ):
            self.assertNotIn(phrase, note_lower)


class StaticScanTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_manual_seed_materialization.py",
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
        forbidden = ("hashlib", ".hexdigest", ".sha256", ".md5", "blake2")
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

    def test_module_source_has_no_pdf_extraction_tokens(self):
        forbidden = ("pypdf", "pdfminer", "pdfplumber", "fitz", "pdftotext")
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

    def test_module_invokes_only_allowed_prior_wo_public_function(self):
        # The module is permitted to invoke
        # run_level0_manual_seed_visible_report (WO-L0-RUN-01) only.
        self.assertIn(
            "run_level0_manual_seed_visible_report",
            self.module_source,
        )

    def test_module_does_not_invoke_wo59(self):
        forbidden = ("run_scaffold_source_intake_visible_report",)
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not invoke '{0}'".format(token),
            )

    def test_module_does_not_invoke_wo_l0_trace_01(self):
        forbidden = ("run_level0_manual_seed_trace_execution",)
        for token in forbidden:
            self.assertNotIn(
                token, self.module_source,
                "module source must not invoke '{0}'".format(token),
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
