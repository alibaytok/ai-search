"""Tests for human-authored Mini-V2 admission and holdout boundaries."""

import ast
import glob
import json
import os
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_intent_test_matrix_runner import run_intent_test_matrix


ADMITTED_PATH = os.path.join(
    "harness",
    "intent_test_matrices",
    "L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json",
)

HOLDOUT_PATH = os.path.join(
    "harness",
    "intent_test_matrices",
    "L0-WS-PARSER-QUALITY-MINI-V2-HOLDOUT.intent.matrix.json",
)

REVIEW_PACK_PATH = os.path.join(
    "harness",
    "admission_review_packs",
    "L0-WS-RAW-CANDIDATES-v1.admission_review.json",
)


def _load_json(path):
    with open(path, "r", encoding="ascii") as handle:
        return json.load(handle)


def _normalize(text):
    return " ".join(text.split()).lower()


def _planning_doc_prompt_keys():
    with open(
        os.path.join("harness", "tests", "test_level0_workshop_derived_trace.py"),
        "r",
        encoding="ascii",
    ) as handle:
        module = ast.parse(handle.read())
    keys = set()
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "_PLANNING_DOC_PROMPTS":
                for _prompt_id, prompt_text in ast.literal_eval(node.value):
                    keys.add(_normalize(prompt_text))
    return keys


def _older_matrix_prompt_keys():
    keys = set()
    for path in glob.glob(
        os.path.join("harness", "intent_test_matrices", "*.intent.matrix.json")
    ):
        if os.path.normpath(path) in {
            os.path.normpath(ADMITTED_PATH),
            os.path.normpath(HOLDOUT_PATH),
        }:
            continue
        matrix = _load_json(path)
        for case in matrix.get("cases", []):
            prompt = case.get("prompt_text")
            if isinstance(prompt, str):
                keys.add(_normalize(prompt))
    return keys


class Level0WorkshopMiniV2AdmissionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admitted = _load_json(ADMITTED_PATH)
        cls.holdout = _load_json(HOLDOUT_PATH)
        cls.review_pack = _load_json(REVIEW_PACK_PATH)
        cls.eligible_by_id = {
            candidate["candidate_id"]: candidate
            for candidate in cls.review_pack["eligible_candidates"]
        }

    def test_matrix_counts_and_ids(self):
        self.assertEqual(
            self.admitted["matrix_id"], "L0-WS-PARSER-QUALITY-MINI-V2"
        )
        self.assertEqual(
            self.holdout["matrix_id"], "L0-WS-PARSER-QUALITY-MINI-V2-HOLDOUT"
        )
        self.assertEqual(len(self.admitted["cases"]), 12)
        self.assertEqual(len(self.holdout["cases"]), 3)
        self.assertIn("expected fields", self.admitted["matrix_note"])
        self.assertIn("holdout", self.holdout["matrix_note"])

    def test_all_cases_reference_eligible_review_pack_candidates(self):
        selected_ids = []
        for case in self.admitted["cases"] + self.holdout["cases"]:
            rc_tags = [tag for tag in case["tags"] if tag.startswith("rc_")]
            self.assertEqual(len(rc_tags), 1)
            candidate_id = "RC-" + rc_tags[0].split("_", 1)[1]
            selected_ids.append(candidate_id)
            self.assertIn(candidate_id, self.eligible_by_id)
            self.assertEqual(
                _normalize(case["prompt_text"]),
                _normalize(self.eligible_by_id[candidate_id]["prompt_text_normalized"]),
            )
        self.assertEqual(len(selected_ids), len(set(selected_ids)))

    def test_admitted_cases_are_not_existing_matrix_or_planning_prompts(self):
        existing = _older_matrix_prompt_keys() | _planning_doc_prompt_keys()
        for case in self.admitted["cases"] + self.holdout["cases"]:
            self.assertNotIn(_normalize(case["prompt_text"]), existing)

    def test_expected_fields_are_present_and_rationales_are_per_case(self):
        required_expected = {
            "category",
            "expected_item_kinds_touched",
            "ambiguity_observed",
            "normalized_intent_observation",
            "candidate_surface_expected",
            "rejection_surface_expected",
        }
        for case in self.admitted["cases"] + self.holdout["cases"]:
            self.assertEqual(set(case["expected"]), required_expected)
            self.assertIn(
                "Human-authored",
                case["rationale"],
            )
            self.assertIn("Source raw candidate: RC-", case["rationale"])
            self.assertNotIn("parser observed", case["rationale"].lower())
            self.assertNotIn("copied from parser", case["rationale"].lower())

    def test_holdout_is_not_referenced_by_autonomous_loop_paths(self):
        holdout_name = os.path.basename(HOLDOUT_PATH)
        scanned_paths = [
            os.path.join("harness", "level0_workshop_matrix_delta_autonomy.py"),
            os.path.join("harness", "level0_workshop_frame_b_overlay_autonomy.py"),
            os.path.join("harness", "level0_workshop_composite_patch_autonomy.py"),
            os.path.join("harness", "level0_workshop_parser_quality_loop.py"),
            os.path.join("harness", "tests", "test_level0_workshop_matrix_delta_autonomy.py"),
            os.path.join("harness", "tests", "test_level0_workshop_frame_b_overlay_autonomy.py"),
            os.path.join("harness", "tests", "test_level0_workshop_composite_patch_autonomy.py"),
            os.path.join("harness", "tests", "test_level0_workshop_parser_quality_loop_contract.py"),
        ]
        for path in scanned_paths:
            with open(path, "r", encoding="ascii") as handle:
                self.assertNotIn(holdout_name, handle.read())

    def test_admitted_and_holdout_matrices_validate_with_runner(self):
        admitted_result = run_intent_test_matrix(ADMITTED_PATH, EventLog())
        holdout_result = run_intent_test_matrix(HOLDOUT_PATH, EventLog())
        self.assertEqual(admitted_result["case_count"], 12)
        self.assertEqual(holdout_result["case_count"], 3)
        self.assertIs(admitted_result["corpus_admission_authorized"], False)
        self.assertIs(holdout_result["corpus_admission_authorized"], False)

    def test_qv2_009_matrix_reconcile_is_documented(self):
        case = next(
            item for item in self.admitted["cases"]
            if item["case_id"] == "QV2-009"
        )
        self.assertEqual(case["expected"]["category"], "H. no-route")
        self.assertEqual(
            case["expected"]["candidate_surface_expected"],
            "candidate fragment of declared shape",
        )
        self.assertEqual(
            case["expected"]["rejection_surface_expected"],
            "no_forced_selection",
        )

    def test_section_o_admission_gate_exists(self):
        with open(
            os.path.join("ai-search", "00-controller-checklist.md"),
            "r",
            encoding="ascii",
        ) as handle:
            checklist = handle.read()
        self.assertIn("## O. Level 0 Workshop Corpus Admission Gate", checklist)
        self.assertIn("No autonomous admission is allowed", checklist)
        self.assertIn("parser observations must not be copied", checklist)
        self.assertIn("Holdout files must remain isolated", checklist)


if __name__ == "__main__":
    unittest.main()
