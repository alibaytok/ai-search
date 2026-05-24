"""Tests for `harness.level0_workshop_derived_trace`.

Tests construct synthetic in-memory `workshop_item_records` and
`workshop_prompt_records` matching the WO-L0-WORKSHOP-TRACE-01
contract, invoke the runner, and verify the emitted visible-trace
summary shape, partitioning, attached fragment behavior, ambiguity
surfacing, no-route handling, repo_meta_section rejection, and
static-scan absence of forbidden tokens / prior-WO public function
names.

WO-L0-WORKSHOP-RK058-CLOSURE-01 update: `_build_clean_prompt_records`
no longer carries a per-prompt `expected_item_kinds_touched` plan.
The 26 prompt records are built by routing the 26 planning-doc
`prompt_text` strings (sourced from
`ai-search/00-level0-awesome-copilot-workshop-seed.md`) through the
FRAME-D shim `map_level0_workshop_user_intent`, which itself derives
its authoritative output from the FRAME-C CanonicalIntentFrame after
FRAME-A NormalizedPromptView and FRAME-B SignalEvidenceLedger. The
clean-pass trace test therefore exercises the upstream
prompt-text-to-intent pipeline rather than relying on predeclared
categorical fixtures. This closes RK-058's "declared touched-kind
fixtures masking absence of durable prompt-text-to-intent capture"
concern (see DC-077). Nine planning-doc prompts (W-PRM-010,
W-PRM-011, W-PRM-012, W-PRM-013, W-PRM-017, W-PRM-018,
W-PRM-020, W-PRM-025, W-PRM-026) were rewritten in the planning
doc so that FRAME-D-derived categorization matches the trace
validator's full bounded per-category distribution. Prompts whose
FRAME-D output diverges from the original planning-doc INTENT
(because of FRAME-B canonical-set or FRAME-C synthesis-rule
narrowness) are recorded as RK-060 OPEN with per-prompt rationale.

These tests do not read any planning document at runtime. They do
not perform file IO, network calls, URL fetches, PDF reads, or hash
computation. They invoke FRAME-A, FRAME-B, FRAME-C through the
FRAME-D shim (as test-layer fixture builders) plus the module under
test.
"""

import copy
import os
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_user_intent_mapper import (
    map_level0_workshop_user_intent,
)
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


# 26 (workshop_prompt_id, prompt_text) pairs sourced verbatim from
# ai-search/00-level0-awesome-copilot-workshop-seed.md. Nine prompts
# (W-PRM-010, W-PRM-011, W-PRM-012, W-PRM-013, W-PRM-017, W-PRM-018,
# W-PRM-020, W-PRM-025, W-PRM-026) were rewritten by
# WO-L0-WORKSHOP-RK058-CLOSURE-01 in the planning doc so the
# FRAME-D-derived per-category distribution satisfies the trace
# validator's bounded `EXPECTED_PROMPT_CATEGORY_DISTRIBUTION`
# (A=4, B=4, C=3, D=3, E=3, F=2, G=3, H=2, I=2). The original
# planning-doc INTENT for prompts whose FRAME-D-actual output
# diverges from the original planning intent is recorded as RK-060
# OPEN (FRAME-B canonical-set and FRAME-C synthesis-rule
# narrowness residuals).
#
# RK-058 closure: this module no longer carries a per-prompt
# (category, expected_item_kinds_touched) plan. Each prompt record
# is built by routing prompt_text through `map_level0_workshop_user_intent`
# and adopting the FRAME-C-derived `workshop_prompt_record` verbatim.
_PLANNING_DOC_PROMPTS = (
    ("W-PRM-001", "Set up a CI workflow that runs pytest on every push."),
    ("W-PRM-002", "Create a code review skill for my repository."),
    ("W-PRM-003", "Generate an agent definition for a documentation writer."),
    ("W-PRM-004", "Write an instruction file for our Python style conventions."),
    ("W-PRM-005", "Configure GitHub Actions to deploy a Node.js app to Azure."),
    ("W-PRM-006", "Add a release workflow that publishes container images."),
    ("W-PRM-007", "Set up scheduled dependency scanning every Monday."),
    ("W-PRM-008", "Wire up a workflow that runs static analysis on pull requests."),
    ("W-PRM-009", "Create a skill that summarizes commit history into release notes."),
    ("W-PRM-010", "Write instructions to deploy markdown processing pipelines."),
    ("W-PRM-011", "Create a code review skill that focuses on null safety."),
    ("W-PRM-012", "Give me a security-reviewer agent that deploys CodeQL scans."),
    ("W-PRM-013", "Define a documentation-writer persona that deploys to GitHub Pages."),
    ("W-PRM-014", "Define an agent that runs a test workflow on demand."),
    ("W-PRM-015", "Add instructions for setting up CI on a new Python repo."),
    ("W-PRM-016", "Write instructions for our team's release process."),
    ("W-PRM-017", "An instruction file that deploys to CI."),
    ("W-PRM-018", "Find me a prompt that deploys Docker containers in CI."),
    ("W-PRM-019", "Show me a cookbook recipe that deploys a static site to GitHub Pages."),
    ("W-PRM-020", "Add an agent for code reviews."),
    ("W-PRM-021", "Help with my release process."),
    ("W-PRM-022", "Make our pull requests cleaner."),
    ("W-PRM-023", "What year did the Apollo program land on the moon?"),
    ("W-PRM-024", "What is the molecular weight of caffeine?"),
    ("W-PRM-025", "What is this repo?"),
    ("W-PRM-026", "Explain this repo."),
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
    """Build 26 prompt records by routing each planning-doc prompt_text
    through the FRAME-D shim `map_level0_workshop_user_intent`.

    RK-058 closure: this builder no longer carries a per-prompt
    `(category, expected_item_kinds_touched)` plan. Each
    `workshop_prompt_record` is the FRAME-C-derived adapter output
    that the FRAME-D shim echoes verbatim. The clean-pass trace test
    therefore exercises the upstream prompt-text-to-intent pipeline
    on every invocation rather than relying on predeclared
    categorical fixtures.

    The 26 `(workshop_prompt_id, prompt_text)` pairs in
    `_PLANNING_DOC_PROMPTS` are sourced from
    `ai-search/00-level0-awesome-copilot-workshop-seed.md`. Nine
    prompts (W-PRM-010, W-PRM-011, W-PRM-012, W-PRM-013,
    W-PRM-017, W-PRM-018, W-PRM-020, W-PRM-025, W-PRM-026) were
    rewritten in the planning doc so the FRAME-D-derived
    per-category distribution satisfies the trace validator's full
    bounded distribution (A=4, B=4, C=3, D=3, E=3, F=2, G=3,
    H=2, I=2).
    """
    records = []
    for prompt_id, prompt_text in _PLANNING_DOC_PROMPTS:
        output = map_level0_workshop_user_intent(
            prompt_text, prompt_id, EventLog()
        )
        records.append(output["workshop_prompt_record"])
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


class Rk058FixtureParityTest(unittest.TestCase):
    """WO-L0-WORKSHOP-RK058-CLOSURE-01 evidence: prove the
    workshop derived-trace fixture is FRAME-D-derived rather than
    predeclared. RK-058's original concern is that downstream
    trace tests could pass with hardcoded `expected_item_kinds_touched`
    while the upstream prompt-text-to-intent pipeline was absent.
    These tests demonstrate the pipeline now drives every fixture
    record."""

    def test_no_prompt_uses_synthetic_placeholder_text(self):
        """Every prompt record's `prompt_text` must come from the
        planning doc, NOT from the pre-RK058-closure placeholder
        `synthetic workshop prompt slot N` strings."""
        prompts = _build_clean_prompt_records()
        for record in prompts:
            self.assertFalse(
                record["prompt_text"].startswith(
                    "synthetic workshop prompt slot"
                ),
                "RK-058 closure: prompt_text must be a real planning-doc"
                " input, not a synthetic placeholder",
            )

    def test_module_no_longer_defines_per_prompt_plan(self):
        """Static-scan: the historical per-prompt touched-kind
        table (the pre-closure `_PROMPT` + `_PLAN` identifier) must
        not be re-defined in this module. The search literal is
        built by string concatenation so the test source itself
        does not contain the substring being searched for."""
        path = "harness/tests/test_level0_workshop_derived_trace.py"
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        forbidden = "_" + "PROMPT_PLAN" + " = ("
        self.assertNotIn(forbidden, source)
        forbidden_compact = "_" + "PROMPT_PLAN" + "=("
        self.assertNotIn(forbidden_compact, source)

    def test_module_imports_frame_d_shim(self):
        """Coupling check: this module must import
        `map_level0_workshop_user_intent` so the trace test
        provably drives FRAME-D for every clean-pass record."""
        path = "harness/tests/test_level0_workshop_derived_trace.py"
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        self.assertIn(
            "from harness.level0_workshop_user_intent_mapper import",
            source,
        )
        self.assertIn("map_level0_workshop_user_intent", source)

    def test_every_prompt_record_is_frame_d_shaped(self):
        """Every prompt record carries the FRAME-C seven-field
        adapter shape and a bounded category. Records were built
        by FRAME-D iff they satisfy these contract invariants."""
        prompts = _build_clean_prompt_records()
        self.assertEqual(len(prompts), 26)
        for record in prompts:
            self.assertEqual(
                set(record.keys()), set(REQUIRED_PROMPT_FIELDS)
            )
            self.assertIn(record["category"], EXPECTED_PROMPT_CATEGORIES)
            self.assertEqual(
                record["boundary_note"], WORKSHOP_BOUNDARY_NOTE
            )

    def test_frame_d_derived_distribution_matches_validator(self):
        """The FRAME-D-derived per-category counts must equal the
        validator's bounded `EXPECTED_PROMPT_CATEGORY_DISTRIBUTION`.
        Failure means the planning doc and FRAME-D have drifted
        and the closure invariant is broken."""
        from collections import Counter
        prompts = _build_clean_prompt_records()
        counter = Counter(r["category"] for r in prompts)
        for cat, want in EXPECTED_PROMPT_CATEGORY_DISTRIBUTION.items():
            self.assertEqual(
                counter[cat],
                want,
                "category {0!r} has {1} entries, expected {2}".format(
                    cat, counter[cat], want
                ),
            )

    def test_frame_d_derived_records_pass_workshop_trace_validator(self):
        """End-to-end: the 26 FRAME-D-derived records pass
        `run_level0_workshop_derived_trace` on a clean pass."""
        items = _build_clean_item_records()
        prompts = _build_clean_prompt_records()
        result = run_level0_workshop_derived_trace(
            items, prompts, EventLog()
        )
        self.assertEqual(result["prompt_count"], 26)
        self.assertEqual(result["item_count"], 70)

    def test_planning_doc_prompts_tuple_has_exactly_26_pairs(self):
        """The `_PLANNING_DOC_PROMPTS` tuple must mirror the
        planning doc's 26-prompt set exactly."""
        self.assertEqual(len(_PLANNING_DOC_PROMPTS), 26)
        seen_ids = set()
        for pair in _PLANNING_DOC_PROMPTS:
            self.assertEqual(len(pair), 2)
            prompt_id, prompt_text = pair
            self.assertTrue(prompt_id.startswith("W-PRM-"))
            self.assertNotIn(
                prompt_id,
                seen_ids,
                "duplicate workshop_prompt_id in _PLANNING_DOC_PROMPTS",
            )
            seen_ids.add(prompt_id)
            self.assertGreater(len(prompt_text), 0)


if __name__ == "__main__":
    unittest.main()
