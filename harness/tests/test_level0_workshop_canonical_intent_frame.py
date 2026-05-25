"""Tests for `harness.level0_workshop_canonical_intent_frame` (FRAME-C).

Tests build synthetic FRAME-B SignalEvidenceLedger fixtures by
invoking the FRAME-A view-builder and the FRAME-B extractor at
the test layer only, then exercise the FRAME-C synthesizer
against those fixtures and against deliberately mutated copies to
cover each halt branch.

The module under test does NOT invoke any prior-WO public function;
FRAME-A and FRAME-B appear only as test-layer fixture builders.

Adapter parity is verified by feeding the FRAME-C-produced
`workshop_prompt_record` into a synthetic 26-prompt fixture that
`run_level0_workshop_derived_trace` accepts on a clean pass at the
test layer; the module under test does NOT invoke that validator.
"""

import copy
import os
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_canonical_intent_frame import (
    AFFINITY_GRADES,
    ALLOWED_OUTPUT_KEYS,
    AMBIGUITY_LEVELS,
    EVIDENCE_BANDS,
    EXPECTED_LEDGER_KIND,
    FRAME_B_GATING_BOOLEANS,
    FRAME_B_REQUIRED_KEYS,
    FRAME_KIND,
    ForbiddenLanguageInLevel0WorkshopCanonicalIntentFrame,
    FrameBGatingBooleanFlipped,
    InvalidSignalEvidenceLedgerKind,
    InvalidSignalEvidenceShape,
    InvalidWorkshopPromptId,
    MissingSignalEvidenceLedgerKey,
    NonDictSignalEvidenceLedger,
    REQUESTED_OUTPUT_SHAPES,
    UnknownSignalEvidenceLedgerKey,
    WORKSHOP_BOUNDARY_NOTE_LITERAL,
    WORKSHOP_ITEM_KINDS,
    WORKSHOP_PROMPT_CATEGORIES,
    build_canonical_intent_frame,
)
from harness.level0_workshop_normalized_prompt_view import (
    build_level0_workshop_normalized_prompt_view,
)
from harness.level0_workshop_signal_evidence import (
    extract_workshop_signal_evidence,
)
from harness.level0_workshop_derived_trace import (
    run_level0_workshop_derived_trace,
)
from harness.tests.test_level0_workshop_derived_trace import (
    _build_clean_item_records,
    _build_clean_prompt_records,
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


def _ledger_for(prompt):
    """Helper: produce a FRAME-B ledger by running the FRAME-A and
    FRAME-B pipelines at the test layer only."""
    view = build_level0_workshop_normalized_prompt_view(prompt, EventLog())
    return extract_workshop_signal_evidence(view, EventLog())


def _frame_for(prompt, workshop_prompt_id="W-PRM-001"):
    """Helper: build a FRAME-C result for a prompt + id."""
    ledger = _ledger_for(prompt)
    return build_canonical_intent_frame(ledger, workshop_prompt_id, EventLog())


class CleanPassTest(unittest.TestCase):

    def setUp(self):
        self.event_log = EventLog()
        self.ledger = _ledger_for(
            "Set up a CI workflow for a Python project."
        )
        self.result = build_canonical_intent_frame(
            self.ledger, "W-PRM-001", self.event_log
        )

    def test_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_frame_kind_literal(self):
        self.assertEqual(self.result["intent_frame_kind"], FRAME_KIND)

    def test_input_prompt_observed_mirrors_ledger(self):
        self.assertEqual(
            self.result["input_prompt_observed"],
            self.ledger["input_prompt_observed"],
        )

    def test_source_signal_ledger_kind_carried_through(self):
        self.assertEqual(
            self.result["source_signal_ledger_kind"],
            EXPECTED_LEDGER_KIND,
        )

    def test_workshop_prompt_id_preserved(self):
        self.assertEqual(self.result["workshop_prompt_id"], "W-PRM-001")

    def test_evidence_band_in_bounded_set(self):
        self.assertIn(self.result["evidence_band"], EVIDENCE_BANDS)

    def test_ambiguity_level_in_bounded_set(self):
        self.assertIn(self.result["ambiguity_level"], AMBIGUITY_LEVELS)

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

    def test_frame_note_non_empty(self):
        self.assertIsInstance(self.result["frame_note"], str)
        self.assertGreater(len(self.result["frame_note"]), 0)

    def test_started_and_passed_events_emitted(self):
        types = [e["type"] for e in self.event_log.events]
        self.assertIn(
            "level0_workshop_canonical_intent_frame_started", types
        )
        self.assertIn(
            "level0_workshop_canonical_intent_frame_passed", types
        )

    def test_no_halt_event_on_clean_pass(self):
        self.assertFalse(self.event_log.has_halt())

    def test_no_route_status_field_in_result(self):
        for field in _ROUTE_STATUS_FIELDS:
            self.assertNotIn(field, self.result)

    def test_no_forbidden_output_field_name_in_result(self):
        for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
            self.assertNotIn(field, self.result)


class AffinityShapeTest(unittest.TestCase):

    def test_every_affinity_entry_has_three_required_fields(self):
        result = _frame_for("Set up a CI workflow.")
        for entry in result["source_shape_affinity"]:
            self.assertEqual(
                set(entry.keys()),
                {"item_kind", "affinity_basis", "affinity_grade"},
            )

    def test_every_affinity_item_kind_in_bounded_set_plus_none(self):
        result = _frame_for("Set up a CI workflow.")
        allowed = set(WORKSHOP_ITEM_KINDS) | {"none"}
        for entry in result["source_shape_affinity"]:
            self.assertIn(entry["item_kind"], allowed)

    def test_every_affinity_grade_in_bounded_set(self):
        result = _frame_for("Set up a CI workflow.")
        for entry in result["source_shape_affinity"]:
            self.assertIn(entry["affinity_grade"], AFFINITY_GRADES)

    def test_every_affinity_basis_is_list_of_strings(self):
        result = _frame_for("Set up a CI workflow.")
        for entry in result["source_shape_affinity"]:
            self.assertIsInstance(entry["affinity_basis"], list)
            for sid in entry["affinity_basis"]:
                self.assertIsInstance(sid, str)


class WorkflowSignalsTest(unittest.TestCase):

    def test_set_up_ci_workflow_yields_workflow_affinity(self):
        result = _frame_for("Set up a CI workflow for a Python project.")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("workflow_file", kinds)

    def test_set_up_ci_workflow_category_workflow_intent(self):
        result = _frame_for("Set up a CI workflow for a Python project.")
        # Category may be B (workflow intent) or D/E/F if other
        # families collide; assert it is at least one of the
        # workflow-shaped categories.
        self.assertIn(
            result["workshop_prompt_record"]["category"],
            {
                "B. workflow intent",
                "D. agent/persona confusion",
                "E. instruction confusion",
                "F. prompt-search-shaped but workflow-intent",
                "A. clear single-intent",
                "G. ambiguous",
            },
        )

    def test_converging_workflow_signals_yield_consistent_frame(self):
        a = _frame_for("Set up CI for the repo.")
        b = _frame_for("Set up continuous integration for the repo.")
        # Both must include workflow_file in the affinity list.
        kinds_a = [e["item_kind"] for e in a["source_shape_affinity"]]
        kinds_b = [e["item_kind"] for e in b["source_shape_affinity"]]
        self.assertIn("workflow_file", kinds_a)
        self.assertIn("workflow_file", kinds_b)


class SkillSignalsTest(unittest.TestCase):

    def test_skill_capability_phrasing_yields_skill_affinity(self):
        result = _frame_for("Create a skill for code review.")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("skill", kinds)


class InstructionSignalsTest(unittest.TestCase):

    def test_configure_instruction_phrasing_yields_instruction_affinity(self):
        result = _frame_for("Configure the instruction set for the team.")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("instruction", kinds)


class AgentSignalsTest(unittest.TestCase):

    def test_persona_phrasing_yields_agent_affinity(self):
        result = _frame_for("Define a persona for the assistant role.")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("agent", kinds)


class RepoMetaNearMissTest(unittest.TestCase):

    def test_readme_explain_yields_repo_meta_section_only(self):
        result = _frame_for("Explain the readme of this repo.")
        self.assertEqual(
            result["workshop_prompt_record"]["expected_item_kinds_touched"],
            ["repo_meta_section"],
        )
        self.assertEqual(
            result["near_miss_reason"], "repo_meta_section_near_miss"
        )

    def test_repo_meta_category_is_near_miss_rejection(self):
        result = _frame_for("Explain the readme of this repo.")
        self.assertEqual(
            result["workshop_prompt_record"]["category"],
            "I. near-miss/rejection",
        )

    def test_explain_how_this_repo_is_organized_yields_repo_meta_section(self):
        """RK-060 residual (f) closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02A: the new FRAME-B
        sibling canonical `how this repo is organized` fires on
        the planning-doc text, FRAME-C maps the
        `repo_meta_near_miss.repo_navigation` signal to
        `expected_item_kinds_touched == [repo_meta_section]`,
        and the workshop category becomes
        `I. near-miss/rejection`."""
        result = _frame_for("Explain how this repo is organized.")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "I. near-miss/rejection")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["repo_meta_section"],
        )
        self.assertEqual(
            result["near_miss_reason"], "repo_meta_section_near_miss"
        )

    def test_product_name_prompt_yields_repo_meta_section(self):
        """RK-060 residual (e) closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02A: FRAME-B assembles the
        product-name canonical from source-safe fragments, then
        FRAME-C maps the `repo_meta_near_miss.repo_navigation`
        signal to the repo-meta rejection path."""
        result = _frame_for("What is awesome-copilot?")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "I. near-miss/rejection")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["repo_meta_section"],
        )
        self.assertEqual(
            result["near_miss_reason"], "repo_meta_section_near_miss"
        )


class OutOfScopeTest(unittest.TestCase):

    def test_weather_prompt_yields_no_route(self):
        result = _frame_for("What is the weather today.")
        self.assertEqual(
            result["workshop_prompt_record"]["expected_item_kinds_touched"],
            ["none"],
        )
        self.assertEqual(
            result["no_route_reason"], "prompt_out_of_repo_scope"
        )

    def test_out_of_scope_category_is_no_route(self):
        result = _frame_for("What is the weather today.")
        self.assertEqual(
            result["workshop_prompt_record"]["category"],
            "H. no-route",
        )


class NoSignalLedgerTest(unittest.TestCase):

    def test_no_signal_prompt_yields_no_route_frame(self):
        # zzz qqq xxx yyy has no recognizable signals in FRAME-B's
        # families.
        result = _frame_for("zzz qqq xxx yyy.")
        self.assertEqual(result["evidence_band"], "no_signal")
        self.assertEqual(
            result["workshop_prompt_record"]["expected_item_kinds_touched"],
            ["none"],
        )


class ConflictingSignalsTest(unittest.TestCase):

    def test_repo_meta_with_other_signal_yields_high_ambiguity_or_near_miss(self):
        # "Set up the readme workflow" mixes repo-meta (readme) with
        # workflow signals. The repo-meta path wins and the frame
        # surfaces ambiguity reasons or a near-miss category.
        result = _frame_for("Set up the readme workflow.")
        # Either near-miss takes precedence or ambiguity is surfaced.
        category = result["workshop_prompt_record"]["category"]
        ambiguity = result["ambiguity_level"]
        # repo_meta_near_miss must be in the affinity entries.
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("repo_meta_section", kinds)
        self.assertIn(category,
                      {"I. near-miss/rejection", "G. ambiguous"})
        self.assertIn(ambiguity, ("low", "high"))


class HardenedSynthesisTest(unittest.TestCase):
    """Tests for WO-L0-WORKSHOP-FRAME-C-HARDEN-01 hardening the
    RK-059 FRAME-C synthesis gaps surfaced by FRAME-D smoke tests.

    Gap 1: action.deploy + object.agent -> D + [agent, workflow_file].
    Gap 2: action.deploy + output_shape.prompt_collection_request ->
           F + [cookbook_entry, workflow_file].
    Gap 3: bare ambiguity (action signal alone) -> G + multiple
           plausible kinds with high ambiguity.

    Gap 3 is only partially hardened: no-signal bare ambiguity
    still needs a future FRAME-B coverage packet."""

    def test_agent_plus_deploy_yields_category_D_and_workflow_co_fire(self):
        result = _frame_for(
            "Use an agent persona to deploy this project"
        )
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "D. agent/persona confusion")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["agent", "workflow_file"],
        )
        self.assertEqual(result["ambiguity_level"], "high")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("agent", kinds)
        self.assertIn("workflow_file", kinds)

    def test_agent_plus_deploy_workflow_co_fire_basis_is_action_signal(self):
        result = _frame_for(
            "Use an agent persona to deploy this project"
        )
        workflow_entries = [
            e for e in result["source_shape_affinity"]
            if e["item_kind"] == "workflow_file"
        ]
        self.assertEqual(len(workflow_entries), 1)
        # The co-fire entry's basis points at action signals
        # (which is where the deploy verb evidence lives).
        action_ids = {
            s["signal_id"] for s in result["signal_evidence"]
            if s["family_kind"] == "action"
        }
        self.assertTrue(
            set(workflow_entries[0]["affinity_basis"]).issubset(action_ids)
        )

    def test_prompt_collection_plus_deploy_yields_category_F(self):
        result = _frame_for(
            "Give me a prompt that deploys a static site"
        )
        record = result["workshop_prompt_record"]
        self.assertEqual(
            record["category"],
            "F. prompt-search-shaped but workflow-intent",
        )
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["cookbook_entry", "workflow_file"],
        )
        self.assertEqual(result["ambiguity_level"], "high")
        self.assertEqual(
            result["requested_output_shape"], "prompt_collection_request"
        )

    def test_prompt_collection_request_alone_fires_cookbook_entry(self):
        """Cookbook_entry now also fires when
        `requested_output_shape == prompt_collection_request`
        (extended rule). Without a deploy verb the result is a
        clean single cookbook candidate."""
        result = _frame_for("Show me a prompt for code review.")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("cookbook_entry", kinds)
        # Without a deploy verb the workflow_file co-fire does NOT
        # fire; the result is a clean single-intent.
        self.assertNotIn("workflow_file", kinds)

    def test_bare_ambiguity_make_this_better_yields_category_G(self):
        result = _frame_for("make this better")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(result["ambiguity_level"], "high")
        self.assertIn(
            "bare_ambiguity_action_only",
            result["ambiguity_reasons"],
        )
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["skill", "instruction", "workflow_file"],
        )

    def test_bare_ambiguity_fix_this_yields_category_G(self):
        result = _frame_for("fix this")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(result["ambiguity_level"], "high")
        self.assertIn(
            "bare_ambiguity_action_only",
            result["ambiguity_reasons"],
        )

    def test_bare_ambiguity_help_with_my_project_yields_category_G(self):
        """RK-059 residual closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-01: the new FRAME-B
        `action.assist` family extracts `help` from
        `help with my project`, so FRAME-C's bare-ambiguity rule
        fires and the result is `G. ambiguous` with
        `ambiguity_level == "high"` and
        `expected_item_kinds_touched == ["skill", "instruction",
        "workflow_file"]`.
        """
        result = _frame_for("help with my project")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(result["ambiguity_level"], "high")
        self.assertIn(
            "bare_ambiguity_action_only", result["ambiguity_reasons"]
        )
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["skill", "instruction", "workflow_file"],
        )

    def test_action_assist_canonical_help_matches(self):
        """The new `action.assist` family extracts a signal from
        the canonical token `help`."""
        result = _frame_for("can you help")
        action_families = {
            s["signal_family"] for s in result["signal_evidence"]
            if s["family_kind"] == "action"
        }
        self.assertIn("action.assist", action_families)

    def test_action_assist_canonical_assist_matches(self):
        """The new `action.assist` family extracts a signal from
        the canonical token `assist`."""
        result = _frame_for("please assist")
        action_families = {
            s["signal_family"] for s in result["signal_evidence"]
            if s["family_kind"] == "action"
        }
        self.assertIn("action.assist", action_families)

    def test_action_assist_turkish_alias_matches(self):
        """The new `action.assist` family extracts a signal from
        the Turkish alias `yardim`."""
        result = _frame_for("yardim et")
        action_families = {
            s["signal_family"] for s in result["signal_evidence"]
            if s["family_kind"] == "action"
        }
        self.assertIn("action.assist", action_families)

    def test_bare_ambiguity_entries_have_ambiguous_grade(self):
        result = _frame_for("make this better")
        for entry in result["source_shape_affinity"]:
            self.assertEqual(entry["affinity_grade"], "ambiguous")

    def test_bare_ambiguity_does_not_fire_when_target_present(self):
        """A prompt with both an action and a target object does
        NOT trigger bare-ambiguity. `Create a skill for code review.`
        has action.create + object.skill + domain.code_review."""
        result = _frame_for("Create a skill for code review.")
        self.assertNotIn(
            "bare_ambiguity_action_only",
            result["ambiguity_reasons"],
        )
        self.assertEqual(
            result["workshop_prompt_record"]["category"],
            "C. skill intent",
        )

    def test_bare_ambiguity_does_not_fire_when_no_signals(self):
        """`zzz qqq.` has no FRAME-B signal at all; bare-ambiguity
        requires at least an action signal and therefore does not
        fire. The result remains H. no-route via the no-signal
        path."""
        result = _frame_for("zzz qqq.")
        self.assertNotIn(
            "bare_ambiguity_action_only",
            result["ambiguity_reasons"],
        )
        self.assertEqual(
            result["workshop_prompt_record"]["category"], "H. no-route"
        )

    def test_workflow_co_fire_skipped_when_workflow_domain_present(self):
        """When a workflow domain is already firing, the primary
        `_is_workflow_intent` rule fires and the co-fire rule is
        skipped (because `workflow_file` is already in
        `candidate_entries`)."""
        result = _frame_for("Deploy to ci with a workflow")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        workflow_count = sum(1 for k in kinds if k == "workflow_file")
        self.assertEqual(workflow_count, 1)

    def test_improve_plus_code_review_yields_skill_instruction_agent_ambiguity(self):
        """RK-060 residual (c) closed by
        WO-L0-WORKSHOP-FRAME-C-HARDEN-02: the new bounded vague
        improve-plus-code-review ambiguity rule appends
        `instruction` and `agent` candidates alongside the
        already-firing `skill` candidate when
        `primary_action == "improve"` AND `domain.code_review`
        fires AND no informative target_object is present AND no
        constraint AND no output_shape. The result for
        `Improve the way we handle code reviews.` is
        `G. ambiguous` with the ordered kinds
        `[skill, instruction, agent]`."""
        result = _frame_for("Improve the way we handle code reviews.")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["skill", "instruction", "agent"],
        )
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("skill", kinds)
        self.assertIn("instruction", kinds)
        self.assertIn("agent", kinds)
        self.assertEqual(result["ambiguity_level"], "high")

    def test_improve_plus_code_review_with_object_target_stays_single(self):
        """Negative regression: when an informative target_object
        is present alongside `improve` + `code_review`, the new
        ambiguity rule does NOT fire and the existing
        single-skill resolution is preserved. `Improve our code
        review skill.` has both `action.improve` + `object.skill`
        + `domain.code_review`, so `_is_skill_intent` fires from
        the object path and the new rule's guard
        (`not distinct_target_objects`) suppresses the extra
        emission."""
        result = _frame_for("Improve our code review skill.")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "C. skill intent")
        self.assertEqual(record["expected_item_kinds_touched"], ["skill"])

    def test_bare_ambiguity_deploy_variant_emits_workflow_instruction_cookbook(self):
        """RK-060 residual (d) closed by
        WO-L0-WORKSHOP-FRAME-C-HARDEN-02: when bare-ambiguity
        fires AND `primary_action == "deploy"` (e.g.,
        `Help with my release process.` where `release` matches
        action.deploy), the new deploy-variant emission set
        `(workflow_file, instruction, cookbook_entry)` replaces
        the default `(skill, instruction, workflow_file)`. The
        result is `G. ambiguous` with the ordered kinds
        `[workflow_file, instruction, cookbook_entry]`."""
        result = _frame_for("Help with my release process.")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["workflow_file", "instruction", "cookbook_entry"],
        )
        self.assertIn(
            "bare_ambiguity_action_only", result["ambiguity_reasons"]
        )

    def test_bare_ambiguity_default_emission_preserved_for_non_deploy(self):
        """Negative regression: bare-ambiguity for a non-deploy
        action verb continues to emit the default
        `(skill, instruction, workflow_file)` tuple. `make this
        better` has `action.create` (from `make`) and
        `action.improve` (from `better`) but no deploy action."""
        result = _frame_for("make this better")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["skill", "instruction", "workflow_file"],
        )
        self.assertIn(
            "bare_ambiguity_action_only", result["ambiguity_reasons"]
        )

    def test_workflow_hook_candidate_set_maps_to_workflow_under_high_ambiguity(self):
        """W-PRM-007 B/G sibling observation closed by
        WO-L0-WORKSHOP-FRAME-C-HARDEN-02: when the candidate
        set is exactly `{workflow_file, hook}` and ambiguity is
        high (2+ candidate kinds), FRAME-C's
        `_select_workshop_category` returns
        `B. workflow intent` rather than the generic
        `G. ambiguous` fallback. For
        `Set up scheduled dependency scanning every Monday.` the
        FRAME-B `scheduled` canonical (added by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02C) on both
        `constraint.event_triggered` and `object.hook` causes
        `workflow_file` and `hook` to co-fire; the new
        category-selector branch surfaces the workshop category
        as B with the kinds `[workflow_file, hook]`."""
        result = _frame_for(
            "Set up scheduled dependency scanning every Monday."
        )
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "B. workflow intent")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["workflow_file", "hook"],
        )
        self.assertEqual(result["ambiguity_level"], "high")

    def test_scheduled_trigger_yields_workflow_hook_surrogate(self):
        """RK-060 residual (a) closed at the FRAME-B layer by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02C: the new FRAME-B
        `scheduled` canonical on both `constraint.event_triggered`
        and `object.hook` suppresses bare-ambiguity (a constraint
        and a target_object are present) and lets FRAME-C's
        `_is_workflow_intent` (action.set_up + has_event_constraint)
        and `_is_hook_intent` (hook in distinct_target_objects)
        both fire on the planning-doc text `Set up scheduled
        dependency scanning every Monday.`. WO-L0-WORKSHOP-
        FRAME-C-HARDEN-02 extended `_select_workshop_category`
        so the candidate set `{workflow_file, hook}` maps to
        `B. workflow intent` even under high ambiguity, closing
        the W-PRM-007 B/G sibling observation that was
        recorded under DC-080. The kinds set `[workflow_file,
        hook]` matches the planning intent and the trace
        validator distribution is preserved (W-PRM-008
        rebalanced from B to A absorbs the W-PRM-007 G to B
        shift)."""
        result = _frame_for(
            "Set up scheduled dependency scanning every Monday."
        )
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "B. workflow intent")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["workflow_file", "hook"],
        )
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("workflow_file", kinds)
        self.assertIn("hook", kinds)
        self.assertNotIn(
            "bare_ambiguity_action_only", result["ambiguity_reasons"]
        )

    def test_setting_up_inflection_yields_instruction_confusion(self):
        """RK-060 residual (b) closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02B: the new FRAME-B
        canonicals `setting up` / `sets up` make action.set_up
        fire on the planning-doc text `Add instructions for
        setting up CI on a new Python repo.`. FRAME-C's
        `_is_workflow_intent` then fires (action.set_up +
        domain.ci) and workflow_file co-fires alongside the
        already-firing instruction candidate; the workshop
        category becomes `E. instruction confusion` with the
        ordered kinds `[workflow_file, instruction]`."""
        result = _frame_for(
            "Add instructions for setting up CI on a new Python repo."
        )
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "E. instruction confusion")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["workflow_file", "instruction"],
        )
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        self.assertIn("workflow_file", kinds)
        self.assertIn("instruction", kinds)

    def test_workflow_co_fire_only_triggers_for_action_deploy(self):
        """The co-fire rule narrows to `primary_action == deploy`
        so non-deploy actions like `configure` do not pull
        workflow_file into otherwise clean single-intent cases."""
        result = _frame_for("Configure the instruction set for the team.")
        kinds = [e["item_kind"] for e in result["source_shape_affinity"]]
        # The pre-hardening behavior for configure+instruction is
        # preserved: single instruction candidate, no co-fire
        # workflow_file. (Note: action.configure is in the FRAME-C
        # workflow_actions set used by `_is_workflow_intent`, but
        # absent any workflow domain or event constraint the
        # primary workflow rule does not fire; the co-fire rule
        # is intentionally narrower than `_is_workflow_intent` and
        # only fires for `primary_action == deploy`.)
        self.assertNotIn("workflow_file", kinds)
        self.assertEqual(
            result["workshop_prompt_record"]["category"],
            "A. clear single-intent",
        )


class MiniV1FrameCHardeningTest(unittest.TestCase):

    def test_generic_automation_repository_surfaces_bare_shape_ambiguity(self):
        result = _frame_for("Add automation to the repository.")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(
            record["expected_item_kinds_touched"],
            ["skill", "instruction", "workflow_file"],
        )
        self.assertEqual(result["ambiguity_level"], "high")

    def test_ci_domain_with_integration_token_maps_to_workflow(self):
        result = _frame_for("Establish a continuous integration job.")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "B. workflow intent")
        self.assertEqual(
            record["expected_item_kinds_touched"], ["workflow_file"]
        )

    def test_explicit_skill_or_agent_surfaces_both_candidates(self):
        result = _frame_for("Should this be a skill or an agent?")
        record = result["workshop_prompt_record"]
        self.assertEqual(record["category"], "G. ambiguous")
        self.assertEqual(
            record["expected_item_kinds_touched"], ["agent", "skill"]
        )
        self.assertEqual(result["ambiguity_level"], "high")


class EvidenceBandTest(unittest.TestCase):

    def test_evidence_band_no_signal_for_unrecognized_prompt(self):
        result = _frame_for("zzz qqq.")
        self.assertEqual(result["evidence_band"], "no_signal")

    def test_evidence_band_is_categorical_only(self):
        result = _frame_for("Set up CI workflow.")
        self.assertIsInstance(result["evidence_band"], str)
        self.assertIn(result["evidence_band"], EVIDENCE_BANDS)


class AdapterRecordShapeTest(unittest.TestCase):

    def setUp(self):
        self.result = _frame_for("Set up a CI workflow for a Python project.")
        self.record = self.result["workshop_prompt_record"]

    def test_record_has_required_fields(self):
        required = {
            "workshop_prompt_id", "category", "prompt_text",
            "expected_item_kinds_touched", "expected_candidate_surface",
            "expected_rejection_surface", "boundary_note",
        }
        self.assertEqual(set(self.record.keys()), required)

    def test_record_category_in_bounded_workshop_set(self):
        self.assertIn(self.record["category"], WORKSHOP_PROMPT_CATEGORIES)

    def test_record_boundary_note_literal(self):
        self.assertEqual(
            self.record["boundary_note"], WORKSHOP_BOUNDARY_NOTE_LITERAL
        )

    def test_record_no_route_status_field(self):
        for field in _ROUTE_STATUS_FIELDS:
            self.assertNotIn(field, self.record)

    def test_record_no_forbidden_output_field_name(self):
        for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
            self.assertNotIn(field, self.record)


class AdapterTraceCompatibilityTest(unittest.TestCase):
    """Verify the FRAME-C adapter output is shape-compatible with
    the existing workshop derived-trace validator. The module under
    test does NOT call that validator; only this test does."""

    def test_record_satisfies_workshop_derived_trace_per_record_contract(self):
        prompts = _build_clean_prompt_records()
        frame = _frame_for(
            "Set up a CI workflow for a Python project.",
            workshop_prompt_id="W-PRM-002",
        )
        replacement = frame["workshop_prompt_record"]
        self.assertEqual(replacement["category"], "B. workflow intent")
        replaced = False
        for index, record in enumerate(prompts):
            if record["category"] == replacement["category"]:
                replacement["workshop_prompt_id"] = record[
                    "workshop_prompt_id"
                ]
                prompts[index] = replacement
                replaced = True
                break
        self.assertTrue(replaced)
        result = run_level0_workshop_derived_trace(
            _build_clean_item_records(), prompts, EventLog()
        )
        self.assertEqual(result["prompt_count"], 26)


class InputValidationHaltTest(unittest.TestCase):

    def _mutate_ledger_and_expect(self, mutate, exception_cls):
        ledger = _ledger_for("Set up a CI workflow for a Python project.")
        mutate(ledger)
        event_log = EventLog()
        with self.assertRaises(exception_cls):
            build_canonical_intent_frame(ledger, "W-PRM-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_non_dict_ledger_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonDictSignalEvidenceLedger):
            build_canonical_intent_frame("not a dict", "W-PRM-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_missing_ledger_key_halts(self):
        def mutate(ledger):
            del ledger["signal_evidence"]
        self._mutate_ledger_and_expect(mutate, MissingSignalEvidenceLedgerKey)

    def test_unknown_ledger_key_halts(self):
        def mutate(ledger):
            ledger["extra_unknown_key"] = "synthetic extra"
        self._mutate_ledger_and_expect(mutate, UnknownSignalEvidenceLedgerKey)

    def test_invalid_ledger_kind_halts(self):
        def mutate(ledger):
            ledger["signal_evidence_ledger_kind"] = "something_else"
        self._mutate_ledger_and_expect(mutate, InvalidSignalEvidenceLedgerKind)

    def test_selection_made_flip_halts(self):
        def mutate(ledger):
            ledger["selection_made"] = True
        self._mutate_ledger_and_expect(mutate, FrameBGatingBooleanFlipped)

    def test_route_created_flip_halts(self):
        def mutate(ledger):
            ledger["route_created"] = True
        self._mutate_ledger_and_expect(mutate, FrameBGatingBooleanFlipped)

    def test_non_list_signal_evidence_halts(self):
        def mutate(ledger):
            ledger["signal_evidence"] = "not a list"
        self._mutate_ledger_and_expect(mutate, InvalidSignalEvidenceShape)

    def test_non_dict_signal_record_halts(self):
        def mutate(ledger):
            if ledger["signal_evidence"]:
                ledger["signal_evidence"][0] = "not a dict"
            else:
                ledger["signal_evidence"] = ["not a dict"]
        self._mutate_ledger_and_expect(mutate, InvalidSignalEvidenceShape)

    def test_malformed_signal_record_field_set_halts(self):
        def mutate(ledger):
            if ledger["signal_evidence"]:
                del ledger["signal_evidence"][0]["signal_id"]
            else:
                # Construct a malformed record
                ledger["signal_evidence"] = [{"only": "one_field"}]
        self._mutate_ledger_and_expect(mutate, InvalidSignalEvidenceShape)

    def test_empty_workshop_prompt_id_halts(self):
        ledger = _ledger_for("Set up CI.")
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopPromptId):
            build_canonical_intent_frame(ledger, "", event_log)
        self.assertTrue(event_log.has_halt())

    def test_non_string_workshop_prompt_id_halts(self):
        ledger = _ledger_for("Set up CI.")
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopPromptId):
            build_canonical_intent_frame(ledger, 42, event_log)
        self.assertTrue(event_log.has_halt())


class ForbiddenLanguageHaltTest(unittest.TestCase):

    def test_forbidden_phrase_in_input_halts(self):
        ledger = _ledger_for("Set up CI.")
        ledger["ledger_note"] = "this is the best ledger"
        event_log = EventLog()
        with self.assertRaises(
            ForbiddenLanguageInLevel0WorkshopCanonicalIntentFrame
        ):
            build_canonical_intent_frame(ledger, "W-PRM-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_forbidden_claim_phrase_in_input_halts(self):
        ledger = _ledger_for("Set up CI.")
        ledger["ledger_note"] = "this contains a validated route claim"
        event_log = EventLog()
        with self.assertRaises(
            ForbiddenLanguageInLevel0WorkshopCanonicalIntentFrame
        ):
            build_canonical_intent_frame(ledger, "W-PRM-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_user_authored_forbidden_phrase_is_preserved_as_evidence(self):
        ledger = _ledger_for("Set up the best CI workflow.")
        result = build_canonical_intent_frame(
            ledger, "W-PRM-001", EventLog()
        )
        self.assertEqual(
            result["input_prompt_observed"],
            "Set up the best CI workflow.",
        )

    def test_user_authored_claim_phrase_is_preserved_as_evidence(self):
        ledger = _ledger_for("Set up validated route workflow.")
        result = build_canonical_intent_frame(
            ledger, "W-PRM-001", EventLog()
        )
        self.assertEqual(
            result["workshop_prompt_record"]["prompt_text"],
            "Set up validated route workflow.",
        )


class InputIsolationTest(unittest.TestCase):

    def test_input_ledger_not_mutated(self):
        ledger = _ledger_for("Set up a CI workflow for a Python project.")
        before = copy.deepcopy(ledger)
        build_canonical_intent_frame(ledger, "W-PRM-001", EventLog())
        self.assertEqual(ledger, before)


class RequestedOutputShapeEnumTest(unittest.TestCase):

    def test_recipe_phrasing_yields_recipe_shape_or_none(self):
        result = _frame_for("Give me a recipe to set up CI.")
        self.assertIn(
            result["requested_output_shape"],
            list(REQUESTED_OUTPUT_SHAPES) + [None],
        )

    def test_no_shape_phrasing_yields_none_or_one_of_bounded(self):
        result = _frame_for("zzz qqq.")
        self.assertIn(
            result["requested_output_shape"],
            list(REQUESTED_OUTPUT_SHAPES) + [None],
        )

    def test_no_prompt_item_kind_value_used_for_shape(self):
        # The bounded REQUESTED_OUTPUT_SHAPES must never include the
        # bare value "prompt" (workshop item-kind namespace
        # collision). The value used for prompt-collection-request
        # is "prompt_collection_request".
        self.assertNotIn("prompt", REQUESTED_OUTPUT_SHAPES)
        self.assertIn("prompt_collection_request", REQUESTED_OUTPUT_SHAPES)


class SignalEvidenceEchoTest(unittest.TestCase):

    def test_signal_evidence_echoed_from_ledger(self):
        ledger = _ledger_for("Set up a CI workflow for a Python project.")
        result = build_canonical_intent_frame(
            ledger, "W-PRM-001", EventLog()
        )
        # The echoed list IS the same as the ledger's signal_evidence
        # (the synthesizer does not modify records). We compare by
        # value to allow either identity or deep-equal.
        self.assertEqual(
            result["signal_evidence"], ledger["signal_evidence"]
        )

    def test_affinity_basis_references_existing_signal_ids(self):
        ledger = _ledger_for(
            "Set up a CI workflow for a Python project."
        )
        result = build_canonical_intent_frame(
            ledger, "W-PRM-001", EventLog()
        )
        all_signal_ids = {sig["signal_id"]
                          for sig in ledger["signal_evidence"]}
        for entry in result["source_shape_affinity"]:
            for sid in entry["affinity_basis"]:
                self.assertIn(sid, all_signal_ids)


class StaticScanTest(unittest.TestCase):

    def setUp(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_canonical_intent_frame.py",
        )
        with open(module_path, "r", encoding="ascii") as handle:
            self.source = handle.read()
        self.module_path = module_path

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
        for token in ("def query", "def search", "def retrieve",
                      "def rank"):
            self.assertNotIn(token, self.source)

    def test_no_scoring_or_score_tokens(self):
        for token in ("score", "scoring"):
            self.assertNotIn(token, self.source)

    def test_no_forbidden_output_field_name_substrings_in_source(self):
        for token in ("ranking_performed", "scoring_performed",
                      "confidence", "best_match", "threshold",
                      "similarity"):
            self.assertNotIn(token, self.source)

    def test_no_embedding_vector_ann_reranker_tokens(self):
        for token in (
            "embedding(", "vectorize(", " ann_", "approximate_nearest",
            "reranker(", "rerank_",
        ):
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
            "run_level0_workshop_trace_review",
            "map_level0_workshop_user_intent",
            "build_level0_workshop_normalized_prompt_view",
            "extract_workshop_signal_evidence",
        )
        for name in prior_public_functions:
            self.assertNotIn(name, self.source)

    def test_module_file_is_ascii(self):
        with open(self.module_path, "rb") as handle:
            raw = handle.read()
        non_ascii = sum(1 for b in raw if b > 127)
        self.assertEqual(non_ascii, 0)


if __name__ == "__main__":
    unittest.main()
