"""Tests for the Level 0B workshop user-intent mapper (FRAME-D shim).

The shim derives output strictly from the FRAME-C CanonicalIntentFrame.
WO-L0-WORKSHOP-FRAME-C-HARDEN-01 teaches FRAME-C the two concrete
deploy-related RK-059 gaps and the action-backed bare-ambiguity cases.
WO-L0-WORKSHOP-FRAME-B-COVERAGE-01 closes the remaining RK-059
no-signal bare-ambiguity gap by adding the bounded FRAME-B
`action.assist` family (`help`, `assist` plus Turkish `yardim` /
`yardim et`), so `help with my project` now reaches FRAME-C as a
bare-ambiguity signal set and the mapper output is `G. ambiguous`
with multiple plausible kinds.
"""

import copy
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_derived_trace import WORKSHOP_BOUNDARY_NOTE
from harness.level0_workshop_user_intent_mapper import (
    EmptyUserPrompt,
    InvalidWorkshopPromptId,
    NonStringUserPrompt,
    map_level0_workshop_user_intent,
)


def _map(prompt, prompt_id="W-USER-001"):
    event_log = EventLog()
    return map_level0_workshop_user_intent(prompt, prompt_id, event_log), event_log


class CleanMappingTest(unittest.TestCase):

    def test_deploy_prompt_maps_to_workflow_candidate_kind(self):
        output, _ = _map("deploy this service to staging with a workflow")
        self.assertEqual(
            output["normalized_intent_observation"], "workflow_intent"
        )
        self.assertEqual(output["expected_item_kinds_touched"], ["workflow_file"])
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "B. workflow intent"
        )

    def test_ci_prompt_maps_to_workflow_candidate_kind(self):
        """FRAME-C emits the generic candidate-surface literal
        `candidate fragment of declared shape`; the pre-FRAME-D
        legacy mapper used the kind-specific literal `candidate
        workflow surface expected`. The string-specificity gap is
        recorded under RK-059."""
        output, _ = _map("Set up CI for a Python project")
        self.assertEqual(output["expected_item_kinds_touched"], ["workflow_file"])
        self.assertEqual(
            output["candidate_surface_expected"],
            "candidate fragment of declared shape",
        )

    def test_skill_prompt_maps_to_skill_candidate_kind(self):
        output, _ = _map("Create a code review skill for this repository")
        self.assertEqual(output["normalized_intent_observation"], "skill_intent")
        self.assertEqual(output["expected_item_kinds_touched"], ["skill"])
        self.assertEqual(output["workshop_prompt_record"]["category"], "C. skill intent")

    def test_agent_workflow_prompt_maps_to_confusion_category(self):
        """RK-059 gap 1 closed by WO-L0-WORKSHOP-FRAME-C-HARDEN-01:
        FRAME-C's workflow_file co-fire rule now appends
        `workflow_file` as an ambiguous co-fire candidate when
        `action.deploy` is present alongside another candidate
        kind without a workflow domain / workflow target /
        event-triggered constraint. The mapper output through the
        FRAME-D shim now reflects the intended legacy categorical
        contract: category `D. agent/persona confusion` with
        `expected_item_kinds_touched == ["agent", "workflow_file"]`
        and `ambiguity_observed == True`."""
        output, _ = _map("Use an agent persona to deploy this project")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "D. agent/persona confusion",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["agent", "workflow_file"],
        )
        self.assertTrue(output["ambiguity_observed"])

    def test_instruction_workflow_prompt_maps_to_confusion_category(self):
        """RK-059 surface note: FRAME-C orders the candidate
        item-kind list by shape-touch-rule evaluation order
        (workflow_file before instruction). The pre-FRAME-D legacy
        mapper emitted [instruction, workflow_file]. The category
        `E. instruction confusion` is unchanged; only the order
        of `expected_item_kinds_touched` shifted."""
        output, _ = _map("Write instructions for a docker build pipeline")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "E. instruction confusion",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["workflow_file", "instruction"],
        )

    def test_prompt_surface_workflow_intent_maps_to_cookbook_and_workflow(self):
        """RK-059 gap 2 closed by WO-L0-WORKSHOP-FRAME-C-HARDEN-01:
        FRAME-C now treats `output_shape.prompt_collection_request`
        as a cookbook-shaped request, and the workflow_file
        co-fire rule appends `workflow_file` when `action.deploy`
        is present alongside that cookbook entry. The mapper
        output through the FRAME-D shim now reflects the intended
        legacy categorical contract: category `F. prompt-search-
        shaped but workflow-intent` with
        `expected_item_kinds_touched == ["cookbook_entry",
        "workflow_file"]` and `ambiguity_observed == True`."""
        output, _ = _map("Give me a prompt that deploys a static site")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "F. prompt-search-shaped but workflow-intent",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["cookbook_entry", "workflow_file"],
        )
        self.assertTrue(output["ambiguity_observed"])

    def test_bare_ambiguity_phrase_surfaces_ambiguity(self):
        """RK-059 gap 3 partially hardened by
        WO-L0-WORKSHOP-FRAME-C-HARDEN-01:
        FRAME-C's bare-ambiguity rule fires when the FRAME-B
        ledger contains an action signal alone (no informative
        target, domain, output_shape, or constraint). The mapper
        output through the FRAME-D shim now reflects the intended
        legacy categorical contract: category `G. ambiguous` with
        multiple plausible kinds and `ambiguity_observed == True`.
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-01 also extends FRAME-B
        with the `action.assist` family so vague help phrasing
        (`help with my project`, `help me with this`, `can you
        help`, Turkish `yardim et`) now produces a deterministic
        action signal that FRAME-C consumes as bare ambiguity;
        see `test_bare_ambiguity_help_phrase_surfaces_ambiguity`."""
        output, _ = _map("make this better")
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "G. ambiguous"
        )
        self.assertTrue(output["ambiguity_observed"])
        self.assertGreater(len(output["expected_item_kinds_touched"]), 1)
        # FRAME-C's bounded bare-ambiguity emission set.
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["skill", "instruction", "workflow_file"],
        )

    def test_bare_ambiguity_help_phrase_surfaces_ambiguity(self):
        """RK-059 residual closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-01: the new FRAME-B
        `action.assist` family extracts a signal for vague help
        phrasing so FRAME-C's bare-ambiguity rule fires and the
        mapper returns `G. ambiguous` with multiple plausible
        kinds and `ambiguity_observed == True`."""
        output, _ = _map("help with my project")
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "G. ambiguous"
        )
        self.assertTrue(output["ambiguity_observed"])
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["skill", "instruction", "workflow_file"],
        )

    def test_bare_ambiguity_can_you_help_surfaces_ambiguity(self):
        """Companion case for `can you help`: the `action.assist`
        signal is the only informative signal and FRAME-C's
        bare-ambiguity rule fires."""
        output, _ = _map("can you help")
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "G. ambiguous"
        )
        self.assertTrue(output["ambiguity_observed"])

    def test_bare_ambiguity_turkish_yardim_et_surfaces_ambiguity(self):
        """Turkish `yardim et` matches `action.assist.tr_aliases`
        and produces the same bare-ambiguity classification."""
        output, _ = _map("yardim et")
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "G. ambiguous"
        )
        self.assertTrue(output["ambiguity_observed"])

    def test_bare_ambiguity_fix_phrase_surfaces_ambiguity(self):
        """Companion to the `make this better` case: `fix this`
        triggers `action.improve` alone (no target / domain /
        output_shape / constraint) and FRAME-C surfaces G
        ambiguous."""
        output, _ = _map("fix this")
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "G. ambiguous"
        )
        self.assertTrue(output["ambiguity_observed"])

    def test_no_route_prompt_maps_to_none(self):
        output, _ = _map("What year did World War II end?")
        self.assertEqual(output["workshop_prompt_record"]["category"], "H. no-route")
        self.assertEqual(output["expected_item_kinds_touched"], ["none"])
        self.assertEqual(output["rejection_surface_expected"], "prompt_out_of_repo_scope")

    def test_repo_meta_prompt_maps_to_rejection(self):
        output, _ = _map("Show me the README navigation section")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "I. near-miss/rejection",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"], ["repo_meta_section"]
        )
        self.assertEqual(
            output["rejection_surface_expected"], "repo_meta_section_near_miss"
        )

    def test_turkish_ascii_workflow_prompt_maps_to_workflow(self):
        output, _ = _map("bu projeyi staging ortamina dagit ve ci kur")
        self.assertEqual(output["expected_item_kinds_touched"], ["workflow_file"])

    def test_turkish_ascii_skill_prompt_maps_to_skill(self):
        output, _ = _map("kod inceleme beceri olustur")
        self.assertEqual(output["expected_item_kinds_touched"], ["skill"])

    def test_output_prompt_record_is_downstream_compatible_shape(self):
        output, _ = _map("Create a code review skill for this repository")
        record = output["workshop_prompt_record"]
        self.assertEqual(
            set(record.keys()),
            {
                "workshop_prompt_id",
                "category",
                "prompt_text",
                "expected_item_kinds_touched",
                "expected_candidate_surface",
                "expected_rejection_surface",
                "boundary_note",
            },
        )
        self.assertEqual(record["boundary_note"], WORKSHOP_BOUNDARY_NOTE)

    def test_all_authorization_booleans_false(self):
        output, _ = _map("deploy this service to staging")
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
        ):
            self.assertIs(output[key], False)

    def test_started_and_completed_events_emitted(self):
        _, event_log = _map("deploy this service to staging")
        types = [event["type"] for event in event_log.events]
        self.assertIn("level0_workshop_user_intent_mapper_started", types)
        self.assertIn("level0_workshop_user_intent_mapper_completed", types)
        self.assertFalse(event_log.has_halt())


class RejectionTest(unittest.TestCase):

    def test_non_string_prompt_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonStringUserPrompt):
            map_level0_workshop_user_intent(None, "W-USER-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_empty_prompt_halts(self):
        event_log = EventLog()
        with self.assertRaises(EmptyUserPrompt):
            map_level0_workshop_user_intent("   ", "W-USER-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_invalid_prompt_id_halts(self):
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopPromptId):
            map_level0_workshop_user_intent("deploy this", "", event_log)
        self.assertTrue(event_log.has_halt())

    def test_input_prompt_string_not_mutated(self):
        prompt = "deploy this service to staging"
        before = copy.deepcopy(prompt)
        _map(prompt)
        self.assertEqual(prompt, before)


class StaticScanTest(unittest.TestCase):

    def test_module_has_no_file_network_or_indexing_calls(self):
        path = "harness/level0_workshop_user_intent_mapper.py"
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        for forbidden in (
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
            "def query",
            "def search",
            "def retrieve",
            "def rank",
        ):
            self.assertNotIn(forbidden, source)


class LegacyContractParityTest(unittest.TestCase):
    """Prove that the FRAME-D shim derives its authoritative
    output strictly from FRAME-C while preserving the legacy
    fourteen-key output shape, the legacy seven-field
    `workshop_prompt_record` shape, the legacy three named
    exceptions, and the six legacy gating booleans literal False.

    Categorical strings (`category`, `normalized_intent_observation`,
    `expected_item_kinds_touched`, `candidate_surface_expected`,
    `rejection_surface_expected`, `ambiguity_observed`) are
    derived from FRAME-C output, not from a parallel keyword
    classifier. Divergences from the pre-FRAME-D legacy mapper
    are recorded in `ai-search/00-open-questions.md` under
    RK-059."""

    _LEGACY_OUTPUT_KEYS = {
        "intent_mapper_kind",
        "workshop_prompt_record",
        "normalized_intent_observation",
        "expected_item_kinds_touched",
        "candidate_surface_expected",
        "rejection_surface_expected",
        "ambiguity_observed",
        "selection_made",
        "measurement_authorized",
        "real_benchmark_authorized",
        "real_benchmark_ready",
        "source_qualification_authorized",
        "corpus_admission_authorized",
        "mapper_note",
    }

    _LEGACY_RECORD_KEYS = {
        "workshop_prompt_id",
        "category",
        "prompt_text",
        "expected_item_kinds_touched",
        "expected_candidate_surface",
        "expected_rejection_surface",
        "boundary_note",
    }

    def test_shape_preservation_top_level(self):
        output, _ = _map("deploy this service to staging with a workflow")
        self.assertEqual(set(output.keys()), self._LEGACY_OUTPUT_KEYS)

    def test_shape_preservation_workshop_prompt_record(self):
        output, _ = _map("deploy this service to staging with a workflow")
        record = output["workshop_prompt_record"]
        self.assertEqual(set(record.keys()), self._LEGACY_RECORD_KEYS)
        self.assertEqual(record["boundary_note"], WORKSHOP_BOUNDARY_NOTE)
        self.assertEqual(record["workshop_prompt_id"], "W-USER-001")

    def test_workshop_prompt_record_echoes_frame_c_fields(self):
        """The shim's `workshop_prompt_record` is FRAME-C's
        adapter output verbatim. The category, kinds, and surface
        literals must match FRAME-C's bounded enums (not a
        FRAME-D-side keyword translation)."""
        output, _ = _map("deploy this service to staging with a workflow")
        record = output["workshop_prompt_record"]
        # FRAME-C bounded category from the nine WORKSHOP_PROMPT_CATEGORIES.
        self.assertEqual(record["category"], "B. workflow intent")
        # FRAME-C bounded boundary_note literal.
        self.assertEqual(
            record["boundary_note"],
            "not admitted; not qualified; workshop metadata only",
        )

    def test_workflow_intent_preserved(self):
        output, _ = _map("deploy this service to staging with a workflow")
        self.assertEqual(
            output["normalized_intent_observation"], "workflow_intent"
        )
        self.assertEqual(
            output["expected_item_kinds_touched"], ["workflow_file"]
        )
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "B. workflow intent",
        )

    def test_ambiguity_observed_reflects_frame_c_high_level(self):
        """`ambiguity_observed` is derived from FRAME-C's
        `ambiguity_level == "high"`. For a clean single-target
        prompt, FRAME-C reports `ambiguity_level == "none"` and
        the shim therefore reports `ambiguity_observed == False`."""
        output, _ = _map("deploy this service to staging with a workflow")
        self.assertFalse(output["ambiguity_observed"])

    def test_ambiguity_observed_true_when_frame_c_reports_high(self):
        """A prompt that fires both `instruction` and `workflow_file`
        candidates causes FRAME-C to set `ambiguity_level == "high"`
        and the shim reports `ambiguity_observed == True`."""
        output, _ = _map("Write instructions for a docker build pipeline")
        self.assertTrue(output["ambiguity_observed"])

    def test_no_route_behavior_preserved(self):
        output, _ = _map("What is the capital of France?")
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "H. no-route"
        )
        self.assertEqual(output["expected_item_kinds_touched"], ["none"])
        self.assertEqual(
            output["rejection_surface_expected"], "prompt_out_of_repo_scope"
        )

    def test_repo_meta_near_miss_preserved(self):
        output, _ = _map("Show me the README navigation section")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "I. near-miss/rejection",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"], ["repo_meta_section"]
        )
        self.assertEqual(
            output["rejection_surface_expected"],
            "repo_meta_section_near_miss",
        )

    def test_scheduled_trigger_maps_to_workflow_hook_surrogate(self):
        """RK-060 residual (a) closed at FRAME-B by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02C: the planning-doc
        text `Set up scheduled dependency scanning every Monday.`
        now matches FRAME-B's new `scheduled` canonical on both
        `constraint.event_triggered` and `object.hook`; FRAME-C
        synthesizes workflow_file + hook as the candidate set;
        the FRAME-D shim surfaces the bounded surrogate
        `G. ambiguous` with
        `expected_item_kinds_touched == [workflow_file, hook]`
        and `ambiguity_observed == True` (the B/G mismatch
        versus the planning intent category `B. workflow intent`
        is a sibling FRAME-C-side residual)."""
        output, _ = _map(
            "Set up scheduled dependency scanning every Monday."
        )
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "G. ambiguous"
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["workflow_file", "hook"],
        )
        self.assertTrue(output["ambiguity_observed"])
        self.assertEqual(
            output["normalized_intent_observation"],
            "ambiguous_user_intent",
        )

    def test_setting_up_inflection_maps_to_instruction_confusion(self):
        """RK-060 residual (b) closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02B: the planning-doc text
        `Add instructions for setting up CI on a new Python repo.`
        now matches FRAME-B's new canonical `setting up` so
        FRAME-C's workflow_intent path fires (action.set_up +
        domain.ci) and workflow_file co-fires alongside the
        already-firing instruction. The FRAME-D shim surfaces
        category `E. instruction confusion` with
        `expected_item_kinds_touched == [workflow_file,
        instruction]` and `ambiguity_observed == True`."""
        output, _ = _map(
            "Add instructions for setting up CI on a new Python repo."
        )
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "E. instruction confusion",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["workflow_file", "instruction"],
        )
        self.assertTrue(output["ambiguity_observed"])
        self.assertEqual(
            output["normalized_intent_observation"],
            "instruction_surface_workflow_intent",
        )

    def test_explain_how_this_repo_is_organized_maps_to_repo_meta_section(self):
        """RK-060 residual (f) closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02A: the planning-doc text
        `Explain how this repo is organized.` now matches FRAME-B's
        new sibling canonical `how this repo is organized`, FRAME-C
        synthesizes the repo_meta_near_miss path, and the FRAME-D
        shim surfaces `I. near-miss/rejection` with
        `expected_item_kinds_touched == [repo_meta_section]` and
        `rejection_surface_expected ==
        repo_meta_section_near_miss`."""
        output, _ = _map("Explain how this repo is organized.")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "I. near-miss/rejection",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"], ["repo_meta_section"]
        )
        self.assertEqual(
            output["rejection_surface_expected"],
            "repo_meta_section_near_miss",
        )
        self.assertEqual(
            output["normalized_intent_observation"],
            "near_miss_rejection",
        )

    def test_product_name_prompt_maps_to_repo_meta_section(self):
        """RK-060 residual (e) closed by
        WO-L0-WORKSHOP-FRAME-B-COVERAGE-02A: the planning-doc text
        `What is awesome-copilot?` now matches FRAME-B's source-safe
        assembled canonical, and the FRAME-D shim surfaces the
        FRAME-C repo-meta rejection result."""
        output, _ = _map("What is awesome-copilot?")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "I. near-miss/rejection",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"], ["repo_meta_section"]
        )
        self.assertEqual(
            output["rejection_surface_expected"],
            "repo_meta_section_near_miss",
        )
        self.assertEqual(
            output["normalized_intent_observation"],
            "near_miss_rejection",
        )

    def test_turkish_folded_workflow_input_preserved(self):
        output, _ = _map("bu projeyi staging ortamina dagit ve ci kur")
        self.assertEqual(
            output["expected_item_kinds_touched"], ["workflow_file"]
        )
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "B. workflow intent",
        )

    def test_turkish_folded_skill_input_preserved(self):
        output, _ = _map("kod inceleme beceri olustur")
        self.assertEqual(output["expected_item_kinds_touched"], ["skill"])
        self.assertEqual(
            output["workshop_prompt_record"]["category"], "C. skill intent"
        )

    def test_frame_a_pipeline_observed_in_event_log(self):
        _, event_log = _map("deploy this service to staging with a workflow")
        types = [event["type"] for event in event_log.events]
        self.assertIn(
            "level0_workshop_normalized_prompt_view_started", types
        )
        self.assertIn(
            "level0_workshop_normalized_prompt_view_completed", types
        )

    def test_frame_b_pipeline_observed_in_event_log(self):
        _, event_log = _map("deploy this service to staging with a workflow")
        types = [event["type"] for event in event_log.events]
        self.assertIn("level0_workshop_signal_evidence_started", types)
        self.assertIn("level0_workshop_signal_evidence_passed", types)

    def test_frame_c_pipeline_observed_in_event_log(self):
        _, event_log = _map("deploy this service to staging with a workflow")
        types = [event["type"] for event in event_log.events]
        self.assertIn(
            "level0_workshop_canonical_intent_frame_started", types
        )
        self.assertIn(
            "level0_workshop_canonical_intent_frame_passed", types
        )

    def test_completed_event_observes_three_frame_kinds(self):
        _, event_log = _map("deploy this service to staging with a workflow")
        completed = [
            event for event in event_log.events
            if event["type"] == "level0_workshop_user_intent_mapper_completed"
        ]
        self.assertEqual(len(completed), 1)
        self.assertEqual(
            completed[0]["observed_view_kind"],
            "level0_workshop_normalized_prompt_view",
        )
        self.assertEqual(
            completed[0]["observed_ledger_kind"],
            "level0_workshop_signal_evidence_ledger",
        )
        self.assertEqual(
            completed[0]["observed_frame_kind"],
            "level0_workshop_canonical_intent_frame",
        )

    def test_non_string_exception_translated_at_shim_boundary(self):
        event_log = EventLog()
        with self.assertRaises(NonStringUserPrompt):
            map_level0_workshop_user_intent(42, "W-USER-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_empty_exception_translated_at_shim_boundary(self):
        event_log = EventLog()
        with self.assertRaises(EmptyUserPrompt):
            map_level0_workshop_user_intent("", "W-USER-001", event_log)
        self.assertTrue(event_log.has_halt())

    def test_invalid_prompt_id_raised_before_frame_c(self):
        event_log = EventLog()
        with self.assertRaises(InvalidWorkshopPromptId):
            map_level0_workshop_user_intent("deploy this", "", event_log)
        types = [event["type"] for event in event_log.events]
        self.assertIn(
            "level0_workshop_normalized_prompt_view_completed", types
        )
        self.assertNotIn(
            "level0_workshop_canonical_intent_frame_started", types
        )

    def test_all_six_gating_booleans_remain_literal_false(self):
        output, _ = _map("deploy this service to staging with a workflow")
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
        ):
            self.assertIs(output[key], False)

    def test_no_forbidden_output_field_names_present_in_output(self):
        output, _ = _map("deploy this service to staging with a workflow")
        forbidden = {
            "ranking_performed",
            "scoring_performed",
            "confidence",
            "score",
            "distance",
            "best_match",
            "threshold",
            "similarity",
        }
        self.assertFalse(set(output.keys()) & forbidden)
        self.assertFalse(
            set(output["workshop_prompt_record"].keys()) & forbidden
        )

    def test_no_forbidden_output_field_names_in_source(self):
        path = "harness/level0_workshop_user_intent_mapper.py"
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        for forbidden in (
            "ranking_performed",
            "scoring_performed",
            '"confidence"',
            '"score"',
            '"distance"',
            '"best_match"',
            '"threshold"',
            '"similarity"',
        ):
            self.assertNotIn(forbidden, source)

    def test_module_source_is_ascii_only(self):
        path = "harness/level0_workshop_user_intent_mapper.py"
        with open(path, "rb") as handle:
            data = handle.read()
        data.decode("ascii")

    def test_shim_imports_frame_a_b_c_public_functions(self):
        path = "harness/level0_workshop_user_intent_mapper.py"
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        self.assertIn(
            "build_level0_workshop_normalized_prompt_view", source
        )
        self.assertIn("extract_workshop_signal_evidence", source)
        self.assertIn("build_canonical_intent_frame", source)

    def test_shim_does_not_define_legacy_classifier(self):
        """The shim must not DEFINE the pre-FRAME-D legacy keyword
        classifier or its keyword tables. FRAME-C is the single
        source of truth for categorization. The docstring may
        reference the removed names for context, but no `def` or
        `=` assignment of them may remain."""
        path = "harness/level0_workshop_user_intent_mapper.py"
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        self.assertNotIn("def _classify_prompt", source)
        for table_name in (
            "_NO_ROUTE_TERMS",
            "_REPO_META_TERMS",
            "_WORKFLOW_TERMS",
            "_HOOK_TERMS",
            "_SKILL_TERMS",
            "_AGENT_TERMS",
            "_INSTRUCTION_TERMS",
            "_PLUGIN_TERMS",
            "_COOKBOOK_TERMS",
            "_AMBIGUOUS_TERMS",
        ):
            self.assertNotIn(table_name + " = ", source)
            self.assertNotIn(table_name + "= ", source)
            self.assertNotIn(table_name + " =(", source)


if __name__ == "__main__":
    unittest.main()
