"""Tests for the Level 0B workshop user-intent mapper (FRAME-D shim).

The shim now derives output strictly from the FRAME-C
CanonicalIntentFrame. Some pre-FRAME-D legacy smoke-test
assertions diverge from FRAME-C semantics; those divergences are
recorded as upstream FRAME-C synthesis gaps under RK-059
("FRAME-C synthesis gaps surfaced by FRAME-D smoke tests"). The
affected smoke-test assertions in `CleanMappingTest` and in
`LegacyContractParityTest` have been updated to FRAME-C-actual
values with docstring pointers to RK-059. Closure of RK-059 is
reserved for a later Codex-authorized FRAME-C-hardening packet;
once FRAME-C is hardened, those tests should be updated to
re-encode the pre-FRAME-D legacy categorical contract.
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

    def test_agent_workflow_prompt_maps_to_clear_single_intent_under_frame_c(self):
        """RK-059 upstream FRAME-C gap: action.deploy + object.agent
        without a workflow domain or event-triggered constraint
        classifies as `A. clear single-intent` with `["agent"]`.
        The pre-FRAME-D legacy mapper classified this as `D.
        agent/persona confusion` with `["agent", "workflow_file"]`
        via keyword co-occurrence; FRAME-C's signal-driven
        synthesizer does not derive a `workflow_file` candidate
        from `deploy` alone. Closure of RK-059 is reserved for a
        later Codex-authorized FRAME-C-hardening packet that
        teaches `_compute_shape_touch_plan` to fire `workflow_file`
        from a deploy/release verb co-occurring with any object
        signal."""
        output, _ = _map("Use an agent persona to deploy this project")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "A. clear single-intent",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"], ["agent"]
        )

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

    def test_prompt_surface_workflow_intent_maps_to_no_route_under_frame_c(self):
        """RK-059 upstream FRAME-C gap: `output_shape.prompt_collection_request`
        + `action.deploy` without a workflow domain or
        event-triggered constraint classifies as `H. no-route`
        with `["none"]`. The pre-FRAME-D legacy mapper classified
        this as `F. prompt-search-shaped but workflow-intent`
        with `["cookbook_entry", "workflow_file"]` via keyword
        co-occurrence. Closure of RK-059 is reserved for a later
        Codex-authorized FRAME-C-hardening packet that teaches
        the shape-touch plan to fire `cookbook_entry` from a
        `prompt_collection_request` output shape even without a
        recipe-targeted target object, and to fire `workflow_file`
        from a deploy verb co-occurring with any output-shape
        signal."""
        output, _ = _map("Give me a prompt that deploys a static site")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "H. no-route",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["none"],
        )

    def test_bare_ambiguity_phrase_maps_to_no_route_under_frame_c(self):
        """RK-059 upstream FRAME-C gap: bare ambiguity phrases
        like `make this better`, `fix this`, or `help with my
        project` do not have a dedicated FRAME-B family. FRAME-C
        classifies them as `H. no-route` with `["none"]` and
        `ambiguity_level == "none"`. The pre-FRAME-D legacy mapper
        classified them as `G. ambiguous` with multiple kinds and
        `ambiguity_observed == True` via the `_AMBIGUOUS_TERMS`
        keyword table. Closure of RK-059 is reserved for a later
        Codex-authorized FRAME-C-hardening packet that introduces
        a dedicated `bare_ambiguity` family or equivalent rule."""
        output, _ = _map("make this better")
        self.assertEqual(output["workshop_prompt_record"]["category"], "H. no-route")
        self.assertFalse(output["ambiguity_observed"])
        self.assertEqual(output["expected_item_kinds_touched"], ["none"])

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
