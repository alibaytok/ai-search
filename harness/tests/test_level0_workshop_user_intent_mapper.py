"""Tests for the Level 0B workshop user-intent mapper."""

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
        output, _ = _map("Set up CI for a Python project")
        self.assertEqual(output["expected_item_kinds_touched"], ["workflow_file"])
        self.assertEqual(
            output["candidate_surface_expected"],
            "candidate workflow surface expected",
        )

    def test_skill_prompt_maps_to_skill_candidate_kind(self):
        output, _ = _map("Create a code review skill for this repository")
        self.assertEqual(output["normalized_intent_observation"], "skill_intent")
        self.assertEqual(output["expected_item_kinds_touched"], ["skill"])
        self.assertEqual(output["workshop_prompt_record"]["category"], "C. skill intent")

    def test_agent_workflow_prompt_maps_to_confusion_category(self):
        output, _ = _map("Use an agent persona to deploy this project")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "D. agent/persona confusion",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"], ["agent", "workflow_file"]
        )

    def test_instruction_workflow_prompt_maps_to_confusion_category(self):
        output, _ = _map("Write instructions for a docker build pipeline")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "E. instruction confusion",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["instruction", "workflow_file"],
        )

    def test_prompt_surface_workflow_intent_maps_to_cookbook_and_workflow(self):
        output, _ = _map("Give me a prompt that deploys a static site")
        self.assertEqual(
            output["workshop_prompt_record"]["category"],
            "F. prompt-search-shaped but workflow-intent",
        )
        self.assertEqual(
            output["expected_item_kinds_touched"],
            ["cookbook_entry", "workflow_file"],
        )

    def test_ambiguous_prompt_surfaces_ambiguity(self):
        output, _ = _map("make this better")
        self.assertEqual(output["workshop_prompt_record"]["category"], "G. ambiguous")
        self.assertTrue(output["ambiguity_observed"])
        self.assertGreater(len(output["expected_item_kinds_touched"]), 1)

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


if __name__ == "__main__":
    unittest.main()
