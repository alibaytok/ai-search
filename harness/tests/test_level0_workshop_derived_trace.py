"""Tests for `harness.level0_workshop_derived_trace`.

Tests construct synthetic in-memory `workshop_item_records` and
`workshop_prompt_records` matching the WO-L0-WORKSHOP-TRACE-01
contract, invoke the runner, and verify the emitted visible-trace
summary shape, partitioning, attached fragment behavior, ambiguity
surfacing, no-route handling, repo_meta_section rejection, and
static-scan absence of forbidden tokens / prior-WO public function
names.

These tests do not read any planning document at runtime. They do
not perform file IO, network calls, URL fetches, PDF reads, or hash
computation. They invoke only the module under test.
"""

import copy
import os
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_derived_trace import (
    ALLOWED_OUTPUT_KEYS,
    AmbiguousPromptMissingMultipleKinds,
    CANDIDATE_ROUTE_KINDS,
    CANDIDATE_WORKFLOW_KINDS,
    DuplicateWorkshopItemId,
    DuplicateWorkshopPromptId,
    EXPECTED_ITEM_KIND_DISTRIBUTION,
    EXPECTED_ITEM_KINDS,
    EXPECTED_PROMPT_CATEGORIES,
    EXPECTED_PROMPT_CATEGORY_DISTRIBUTION,
    EmptyExpectedItemKindsTouched,
    ForbiddenLanguageInLevel0WorkshopDerivedTrace,
    InvalidItemKindDistribution,
    InvalidPromptCategoryDistribution,
    InvalidWorkshopItemBoundaryNoteLiteral,
    InvalidWorkshopItemRecordCount,
    InvalidWorkshopPromptBoundaryNoteLiteral,
    InvalidWorkshopPromptRecordCount,
    MissingWorkshopItemRecordField,
    MissingWorkshopPromptRecordField,
    NonListExpectedItemKindsTouched,
    NonListWorkshopItemRecords,
    NonListWorkshopPromptRecords,
    NonObjectWorkshopItemRecord,
    NonObjectWorkshopPromptRecord,
    REJECTED_ONLY_KINDS,
    REQUIRED_ITEM_FIELDS,
    REQUIRED_PROMPT_FIELDS,
    UnknownExpectedItemKind,
    UnknownItemKind,
    UnknownPromptCategory,
    UnknownWorkshopItemRecordField,
    UnknownWorkshopPromptRecordField,
    WORKSHOP_BOUNDARY_NOTE,
    run_level0_workshop_derived_trace,
)


_ROUTE_STATUS_FIELDS = (
    "official", "is_route", "is_official_route", "selected_as_official",
    "official_route_authorized", "route_authorized", "production_route",
    "selected_route", "executable", "route_state", "plane",
)


# Prompt category -> (count, kinds_touched) plan. Values chosen so
# every category covers its declared distribution and so that
# ambiguous prompts always declare at least two distinct kinds.
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
    """Build 70 item records matching the bounded distribution.

    repo_path_shape and material_role are synthetic but non-empty;
    selection_locator_hint is also synthetic. boundary_note is the
    required workshop literal.
    """
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
    """Build 26 prompt records matching the bounded category distribution.

    prompt_text strings are synthetic test inputs authored locally for
    this test module; no external prompt body is copied. Strings
    deliberately avoid any FORBIDDEN_PHRASES or FORBIDDEN_CLAIM_PHRASES
    tokens.
    """
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


class CleanPassTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.event_log = EventLog()
        self.result = run_level0_workshop_derived_trace(
            self.items, self.prompts, self.event_log
        )

    def test_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_workshop_trace_kind_literal(self):
        self.assertEqual(
            self.result["workshop_trace_kind"],
            "level0_workshop_derived_trace",
        )

    def test_item_count_is_70(self):
        self.assertEqual(self.result["item_count"], 70)

    def test_prompt_count_is_26(self):
        self.assertEqual(self.result["prompt_count"], 26)

    def test_derived_material_count_is_70(self):
        self.assertEqual(self.result["derived_material_count"], 70)
        self.assertEqual(len(self.result["derived_material_records"]), 70)

    def test_candidate_route_fragment_count_is_non_zero(self):
        self.assertGreater(self.result["candidate_route_fragment_count"], 0)
        self.assertEqual(
            self.result["candidate_route_fragment_count"],
            len(self.result["candidate_route_fragment_records"]),
        )

    def test_candidate_workflow_fragment_count_is_non_zero(self):
        self.assertGreater(self.result["candidate_workflow_fragment_count"], 0)
        self.assertEqual(
            self.result["candidate_workflow_fragment_count"],
            len(self.result["candidate_workflow_fragment_records"]),
        )

    def test_rejected_material_count_is_non_zero(self):
        self.assertGreater(self.result["rejected_material_count"], 0)
        self.assertEqual(
            self.result["rejected_material_count"],
            len(self.result["rejected_material_records"]),
        )

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

    def test_workshop_trace_note_non_empty_string(self):
        self.assertIsInstance(self.result["workshop_trace_note"], str)
        self.assertGreater(len(self.result["workshop_trace_note"]), 0)

    def test_started_and_completed_events_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn("level0_workshop_derived_trace_started", types)
        self.assertIn("level0_workshop_derived_trace_completed", types)

    def test_no_halt_event(self):
        self.assertFalse(self.event_log.has_halt())


class DerivedMaterialShapeTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.result = run_level0_workshop_derived_trace(
            self.items, self.prompts, EventLog()
        )

    def test_each_derived_record_has_required_fields(self):
        required = {
            "derived_material_id", "workshop_item_id", "item_kind",
            "repo_path_shape", "material_role", "candidate_only",
            "qualified", "corpus_admitted", "route_object_created",
            "source_material_extracted", "material_observation_basis",
        }
        for derived in self.result["derived_material_records"]:
            self.assertEqual(set(derived.keys()), required)

    def test_each_derived_record_candidate_only_true(self):
        for derived in self.result["derived_material_records"]:
            self.assertIs(derived["candidate_only"], True)

    def test_each_derived_record_qualified_false(self):
        for derived in self.result["derived_material_records"]:
            self.assertIs(derived["qualified"], False)

    def test_each_derived_record_corpus_admitted_false(self):
        for derived in self.result["derived_material_records"]:
            self.assertIs(derived["corpus_admitted"], False)

    def test_each_derived_record_route_object_created_false(self):
        for derived in self.result["derived_material_records"]:
            self.assertIs(derived["route_object_created"], False)

    def test_each_derived_record_source_material_extracted_false(self):
        for derived in self.result["derived_material_records"]:
            self.assertIs(derived["source_material_extracted"], False)

    def test_each_derived_record_observation_basis_workshop_metadata_only(self):
        for derived in self.result["derived_material_records"]:
            self.assertEqual(
                derived["material_observation_basis"], "workshop_metadata_only"
            )

    def test_derived_material_ids_unique_and_prefixed(self):
        ids = [d["derived_material_id"] for d in self.result["derived_material_records"]]
        self.assertEqual(len(ids), len(set(ids)))
        for material_id in ids:
            self.assertTrue(material_id.startswith("L0-WS-DER-"))

    def test_each_derived_record_carries_no_route_status_field(self):
        for derived in self.result["derived_material_records"]:
            for field in _ROUTE_STATUS_FIELDS:
                self.assertNotIn(field, derived)


class PartitionTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.result = run_level0_workshop_derived_trace(
            self.items, self.prompts, EventLog()
        )

    def test_candidate_route_kinds_only_route_kinds(self):
        for rec in self.result["candidate_route_fragment_records"]:
            self.assertIn(rec["item_kind"], CANDIDATE_ROUTE_KINDS)

    def test_candidate_workflow_kinds_only_workflow_kinds(self):
        for rec in self.result["candidate_workflow_fragment_records"]:
            self.assertIn(rec["item_kind"], CANDIDATE_WORKFLOW_KINDS)

    def test_rejected_kinds_only_rejected_only_kinds(self):
        for rec in self.result["rejected_material_records"]:
            self.assertIn(rec["item_kind"], REJECTED_ONLY_KINDS)

    def test_candidate_route_count_equals_sum_of_route_kind_counts(self):
        expected = sum(
            EXPECTED_ITEM_KIND_DISTRIBUTION[k]
            for k in CANDIDATE_ROUTE_KINDS
        )
        self.assertEqual(
            self.result["candidate_route_fragment_count"], expected
        )

    def test_candidate_workflow_count_equals_sum_of_workflow_kind_counts(self):
        expected = sum(
            EXPECTED_ITEM_KIND_DISTRIBUTION[k]
            for k in CANDIDATE_WORKFLOW_KINDS
        )
        self.assertEqual(
            self.result["candidate_workflow_fragment_count"], expected
        )

    def test_rejected_count_equals_repo_meta_section_count(self):
        self.assertEqual(
            self.result["rejected_material_count"],
            EXPECTED_ITEM_KIND_DISTRIBUTION["repo_meta_section"],
        )

    def test_rejection_reason_literal(self):
        for rec in self.result["rejected_material_records"]:
            self.assertEqual(
                rec["rejection_reason"], "repo_meta_section_near_miss"
            )

    def test_repo_meta_section_never_in_candidate_route(self):
        for rec in self.result["candidate_route_fragment_records"]:
            self.assertNotEqual(rec["item_kind"], "repo_meta_section")

    def test_repo_meta_section_never_in_candidate_workflow(self):
        for rec in self.result["candidate_workflow_fragment_records"]:
            self.assertNotEqual(rec["item_kind"], "repo_meta_section")

    def test_rejected_record_carries_no_route_status_field(self):
        for rec in self.result["rejected_material_records"]:
            for field in _ROUTE_STATUS_FIELDS:
                self.assertNotIn(field, rec)


class PerPromptTraceSummaryTest(unittest.TestCase):

    def setUp(self):
        self.items = _build_clean_item_records()
        self.prompts = _build_clean_prompt_records()
        self.result = run_level0_workshop_derived_trace(
            self.items, self.prompts, EventLog()
        )
        self.summary = self.result["per_prompt_trace_summary"]
        self.by_id = {entry["workshop_prompt_id"]: entry for entry in self.summary}

    def test_summary_has_one_entry_per_prompt(self):
        self.assertEqual(len(self.summary), 26)
        self.assertEqual(
            len({entry["workshop_prompt_id"] for entry in self.summary}),
            26,
        )

    def test_each_summary_entry_has_required_fields(self):
        required = {
            "workshop_prompt_id", "category", "expected_item_kinds_touched",
            "attached_kinds_observed",
            "attached_candidate_route_fragment_ids",
            "attached_candidate_workflow_fragment_ids",
            "attached_rejected_material_ids",
            "attached_candidate_route_fragment_count",
            "attached_candidate_workflow_fragment_count",
            "attached_rejected_material_count",
            "ambiguity_observed", "no_selection_reason",
            "route_selection_made", "candidate_only",
        }
        for entry in self.summary:
            self.assertEqual(set(entry.keys()), required)

    def test_no_route_prompts_have_zero_candidates(self):
        no_route_prompts = [
            entry for entry in self.summary if entry["category"] == "H. no-route"
        ]
        self.assertEqual(len(no_route_prompts), 2)
        for entry in no_route_prompts:
            self.assertEqual(entry["attached_candidate_route_fragment_count"], 0)
            self.assertEqual(entry["attached_candidate_workflow_fragment_count"], 0)
            self.assertEqual(entry["attached_rejected_material_count"], 0)
            self.assertEqual(entry["no_selection_reason"], "prompt_out_of_repo_scope")

    def test_ambiguous_prompts_surface_ambiguity(self):
        ambiguous_prompts = [
            entry for entry in self.summary if entry["category"] == "G. ambiguous"
        ]
        self.assertEqual(len(ambiguous_prompts), 3)
        for entry in ambiguous_prompts:
            self.assertIs(entry["ambiguity_observed"], True)

    def test_non_ambiguous_prompts_do_not_surface_ambiguity(self):
        for entry in self.summary:
            if entry["category"] != "G. ambiguous":
                self.assertIs(entry["ambiguity_observed"], False)

    def test_rejection_category_prompts_have_zero_candidate_route_and_workflow(self):
        rejection_prompts = [
            entry for entry in self.summary
            if entry["category"] == "I. near-miss/rejection"
        ]
        self.assertEqual(len(rejection_prompts), 2)
        for entry in rejection_prompts:
            self.assertEqual(entry["attached_candidate_route_fragment_count"], 0)
            self.assertEqual(entry["attached_candidate_workflow_fragment_count"], 0)
            self.assertGreater(entry["attached_rejected_material_count"], 0)
            self.assertEqual(
                entry["no_selection_reason"], "repo_meta_section_near_miss"
            )

    def test_every_route_selection_made_is_literal_false(self):
        for entry in self.summary:
            self.assertIs(entry["route_selection_made"], False)

    def test_every_entry_candidate_only_true(self):
        for entry in self.summary:
            self.assertIs(entry["candidate_only"], True)

    def test_clear_single_intent_prompts_attach_at_least_one_candidate(self):
        clear_prompts = [
            entry for entry in self.summary
            if entry["category"] == "A. clear single-intent"
        ]
        for entry in clear_prompts:
            total = (
                entry["attached_candidate_route_fragment_count"]
                + entry["attached_candidate_workflow_fragment_count"]
            )
            self.assertGreater(total, 0)

    def test_workflow_intent_prompts_attach_workflow_candidate(self):
        workflow_prompts = [
            entry for entry in self.summary
            if entry["category"] == "B. workflow intent"
        ]
        for entry in workflow_prompts:
            self.assertGreater(
                entry["attached_candidate_workflow_fragment_count"], 0
            )

    def test_attached_kinds_observed_subset_of_expected(self):
        for entry in self.summary:
            expected = set(entry["expected_item_kinds_touched"])
            for kind in entry["attached_kinds_observed"]:
                self.assertIn(kind, expected)

    def test_no_summary_entry_carries_route_status_field(self):
        for entry in self.summary:
            for field in _ROUTE_STATUS_FIELDS:
                self.assertNotIn(field, entry)


class DistributionTest(unittest.TestCase):

    def test_observed_item_kind_distribution_matches_expected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        result = run_level0_workshop_derived_trace(items, prompts, EventLog())
        observed = {kind: 0 for kind in EXPECTED_ITEM_KINDS}
        for derived in result["derived_material_records"]:
            observed[derived["item_kind"]] += 1
        self.assertEqual(observed, EXPECTED_ITEM_KIND_DISTRIBUTION)

    def test_observed_prompt_category_distribution_matches_expected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        result = run_level0_workshop_derived_trace(items, prompts, EventLog())
        observed = {cat: 0 for cat in EXPECTED_PROMPT_CATEGORIES}
        for entry in result["per_prompt_trace_summary"]:
            observed[entry["category"]] += 1
        self.assertEqual(observed, EXPECTED_PROMPT_CATEGORY_DISTRIBUTION)

    def test_item_distribution_mismatch_rejected(self):
        items = _build_clean_item_records()
        # Mutate one skill into another instruction; counts skew
        for record in items:
            if record["item_kind"] == "skill":
                record["item_kind"] = "instruction"
                break
        prompts = _build_clean_prompt_records()
        event_log = EventLog()
        with self.assertRaises(InvalidItemKindDistribution):
            run_level0_workshop_derived_trace(items, prompts, event_log)
        self.assertTrue(event_log.has_halt())

    def test_prompt_category_distribution_mismatch_rejected(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        for record in prompts:
            if record["category"] == "A. clear single-intent":
                record["category"] = "B. workflow intent"
                # Ensure expected_item_kinds_touched stays valid
                record["expected_item_kinds_touched"] = ["workflow_file"]
                break
        event_log = EventLog()
        with self.assertRaises(InvalidPromptCategoryDistribution):
            run_level0_workshop_derived_trace(items, prompts, event_log)
        self.assertTrue(event_log.has_halt())


class MalformedInputHaltTest(unittest.TestCase):

    def test_non_list_workshop_item_records_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonListWorkshopItemRecords):
            run_level0_workshop_derived_trace(
                "not a list", _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_non_list_workshop_prompt_records_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonListWorkshopPromptRecords):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), "not a list", event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_wrong_item_count_halts(self):
        items = _build_clean_item_records()[:69]
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopItemRecordCount):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_wrong_prompt_count_halts(self):
        prompts = _build_clean_prompt_records()[:25]
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopPromptRecordCount):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_non_object_item_record_halts(self):
        items = _build_clean_item_records()
        items[3] = "not a dict"
        event_log = EventLog()
        with self.assertRaises(NonObjectWorkshopItemRecord):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_non_object_prompt_record_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[3] = "not a dict"
        event_log = EventLog()
        with self.assertRaises(NonObjectWorkshopPromptRecord):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_missing_item_field_halts(self):
        items = _build_clean_item_records()
        del items[0]["material_role"]
        event_log = EventLog()
        with self.assertRaises(MissingWorkshopItemRecordField):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_unknown_item_field_halts(self):
        items = _build_clean_item_records()
        items[0]["extra_field"] = "synthetic extra"
        event_log = EventLog()
        with self.assertRaises(UnknownWorkshopItemRecordField):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_missing_prompt_field_halts(self):
        prompts = _build_clean_prompt_records()
        del prompts[0]["expected_candidate_surface"]
        event_log = EventLog()
        with self.assertRaises(MissingWorkshopPromptRecordField):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_unknown_prompt_field_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["extra_field"] = "synthetic extra"
        event_log = EventLog()
        with self.assertRaises(UnknownWorkshopPromptRecordField):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_invalid_item_boundary_note_halts(self):
        items = _build_clean_item_records()
        items[0]["boundary_note"] = "wrong literal"
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopItemBoundaryNoteLiteral):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_invalid_prompt_boundary_note_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["boundary_note"] = "wrong literal"
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopPromptBoundaryNoteLiteral):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_non_list_expected_item_kinds_touched_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["expected_item_kinds_touched"] = "skill"
        event_log = EventLog()
        with self.assertRaises(NonListExpectedItemKindsTouched):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_empty_expected_item_kinds_touched_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["expected_item_kinds_touched"] = []
        event_log = EventLog()
        with self.assertRaises(EmptyExpectedItemKindsTouched):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_ambiguous_prompt_with_single_kind_halts(self):
        prompts = _build_clean_prompt_records()
        for entry_index, record in enumerate(prompts):
            if record["category"] == "G. ambiguous":
                prompts[entry_index]["expected_item_kinds_touched"] = ["skill"]
                break
        event_log = EventLog()
        with self.assertRaises(AmbiguousPromptMissingMultipleKinds):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())


class DuplicateAndUnknownHaltTest(unittest.TestCase):

    def test_duplicate_workshop_item_id_halts(self):
        items = _build_clean_item_records()
        items[1]["workshop_item_id"] = items[0]["workshop_item_id"]
        event_log = EventLog()
        with self.assertRaises(DuplicateWorkshopItemId):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_duplicate_workshop_prompt_id_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[1]["workshop_prompt_id"] = prompts[0]["workshop_prompt_id"]
        event_log = EventLog()
        with self.assertRaises(DuplicateWorkshopPromptId):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_unknown_item_kind_halts(self):
        items = _build_clean_item_records()
        items[0]["item_kind"] = "synthetic_unknown_kind"
        event_log = EventLog()
        with self.assertRaises(UnknownItemKind):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_unknown_prompt_category_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["category"] = "Z. synthetic unknown"
        event_log = EventLog()
        with self.assertRaises(UnknownPromptCategory):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_unknown_expected_item_kind_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["expected_item_kinds_touched"] = ["synthetic_unknown_kind"]
        event_log = EventLog()
        with self.assertRaises(UnknownExpectedItemKind):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())


class ForbiddenLanguageHaltTest(unittest.TestCase):

    def test_forbidden_phrase_in_item_record_halts(self):
        items = _build_clean_item_records()
        items[0]["material_role"] = "this is the best of the slots"
        event_log = EventLog()
        with self.assertRaises(ForbiddenLanguageInLevel0WorkshopDerivedTrace):
            run_level0_workshop_derived_trace(
                items, _build_clean_prompt_records(), event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_forbidden_claim_phrase_in_prompt_record_halts(self):
        prompts = _build_clean_prompt_records()
        prompts[0]["expected_candidate_surface"] = "validated route fragment"
        event_log = EventLog()
        with self.assertRaises(ForbiddenLanguageInLevel0WorkshopDerivedTrace):
            run_level0_workshop_derived_trace(
                _build_clean_item_records(), prompts, event_log
            )
        self.assertTrue(event_log.has_halt())


class InputIsolationTest(unittest.TestCase):

    def test_input_records_not_mutated(self):
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        items_before = copy.deepcopy(items)
        prompts_before = copy.deepcopy(prompts)
        run_level0_workshop_derived_trace(items, prompts, EventLog())
        self.assertEqual(items, items_before)
        self.assertEqual(prompts, prompts_before)


class StaticScanTest(unittest.TestCase):

    def setUp(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_derived_trace.py",
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
        )
        for name in prior_public_functions:
            self.assertNotIn(name, self.source)

    def test_module_file_is_ascii(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_derived_trace.py",
        )
        with open(module_path, "rb") as handle:
            raw = handle.read()
        non_ascii = sum(1 for b in raw if b > 127)
        self.assertEqual(non_ascii, 0)


if __name__ == "__main__":
    unittest.main()
