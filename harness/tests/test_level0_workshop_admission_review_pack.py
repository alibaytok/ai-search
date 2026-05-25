"""Tests for the Level 0 raw-candidate admission review pack."""

import ast
import glob
import json
import os
import unittest

from harness import level0_workshop_corpus_crawler as crawler


SNAPSHOT_PATH = os.path.join(
    "harness",
    "raw_candidate_pools",
    "L0-WS-RAW-CANDIDATES-v1.raw_candidates.json",
)
SNAPSHOT_REF = (
    "harness/raw_candidate_pools/"
    "L0-WS-RAW-CANDIDATES-v1.raw_candidates.json"
)

REVIEW_PACK_PATH = os.path.join(
    "harness",
    "admission_review_packs",
    "L0-WS-RAW-CANDIDATES-v1.admission_review.json",
)

ADMISSION_REVIEW_PACK_FIELDS = (
    "admission_review_pack_kind",
    "snapshot_path",
    "snapshot_candidate_count",
    "eligible_candidate_count",
    "excluded_candidate_count",
    "target_admitted_count",
    "target_holdout_count",
    "target_met",
    "review_conclusion",
    "shape_axis_enum",
    "eligible_candidates",
    "excluded_candidates",
    "corpus_admission_authorized",
    "holdout_created",
    "expected_fields_generated",
    "parser_invocation_performed",
)

ELIGIBLE_CANDIDATE_FIELDS = (
    "candidate_id",
    "source_kind",
    "source_path",
    "source_line",
    "prompt_text_normalized",
    "review_status",
    "suggested_shape_axes",
    "admission_status",
    "holdout_status",
)

EXCLUDED_CANDIDATE_FIELDS = (
    "candidate_id",
    "source_kind",
    "source_path",
    "source_line",
    "prompt_text_normalized",
    "review_status",
    "duplicate_references",
)

SHAPE_AXIS_ENUM = (
    "agent_persona_surface",
    "deployment_surface",
    "docs_instruction_surface",
    "general_world_question",
    "long_prompt",
    "multi_intent",
    "prompt_meta_question",
    "repo_workflow_surface",
    "test_generation_surface",
    "translation_or_language_surface",
    "vague_request",
)


def _normalize(text):
    return " ".join(text.split()).lower()


def _existing_prompt_keys():
    keys = set()
    for path in glob.glob(
        os.path.join("harness", "intent_test_matrices", "*.intent.matrix.json")
    ):
        if os.path.basename(path).startswith("L0-WS-PARSER-QUALITY-MINI-V2"):
            continue
        with open(path, "r", encoding="ascii") as handle:
            matrix = json.load(handle)
        for case in matrix.get("cases", []):
            prompt = case.get("prompt_text")
            if isinstance(prompt, str):
                keys.add(_normalize(prompt))

    with open(
        os.path.join("harness", "tests", "test_level0_workshop_derived_trace.py"),
        "r",
        encoding="ascii",
    ) as handle:
        module = ast.parse(handle.read())
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "_PLANNING_DOC_PROMPTS":
                for _prompt_id, prompt_text in ast.literal_eval(node.value):
                    keys.add(_normalize(prompt_text))
    return keys


class Level0WorkshopAdmissionReviewPackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SNAPSHOT_PATH, "r", encoding="ascii") as handle:
            cls.snapshot = json.load(handle)
        with open(REVIEW_PACK_PATH, "r", encoding="ascii") as handle:
            cls.pack = json.load(handle)

    def test_review_pack_shape_and_counts(self):
        self.assertEqual(tuple(self.pack), ADMISSION_REVIEW_PACK_FIELDS)
        self.assertEqual(
            self.pack["admission_review_pack_kind"],
            "level0_workshop_admission_review_pack",
        )
        self.assertEqual(self.pack["snapshot_path"], SNAPSHOT_REF)
        self.assertEqual(self.pack["snapshot_candidate_count"], 69)
        self.assertEqual(self.pack["eligible_candidate_count"], 18)
        self.assertEqual(self.pack["excluded_candidate_count"], 51)
        self.assertEqual(self.pack["target_admitted_count"], 20)
        self.assertEqual(self.pack["target_holdout_count"], 5)
        self.assertIs(self.pack["target_met"], False)
        self.assertEqual(
            self.pack["review_conclusion"],
            "insufficient_unique_candidates_for_20_plus_5",
        )

    def test_review_pack_is_non_authorizing(self):
        self.assertFalse(self.pack["corpus_admission_authorized"])
        self.assertFalse(self.pack["holdout_created"])
        self.assertFalse(self.pack["expected_fields_generated"])
        self.assertFalse(self.pack["parser_invocation_performed"])

    def test_eligible_candidates_are_unique_and_not_existing_prompts(self):
        existing = _existing_prompt_keys()
        prompts = []
        for candidate in self.pack["eligible_candidates"]:
            self.assertEqual(tuple(candidate), ELIGIBLE_CANDIDATE_FIELDS)
            self.assertEqual(
                candidate["review_status"],
                "eligible_for_human_admission_review",
            )
            self.assertEqual(candidate["admission_status"], "not_admitted")
            self.assertEqual(candidate["holdout_status"], "not_holdout")
            prompt_key = _normalize(candidate["prompt_text_normalized"])
            self.assertNotIn(prompt_key, existing)
            prompts.append(prompt_key)
            self.assertNotIn("expected", candidate)
        self.assertEqual(len(prompts), len(set(prompts)))

    def test_excluded_candidates_are_existing_prompt_duplicates(self):
        existing = _existing_prompt_keys()
        for candidate in self.pack["excluded_candidates"]:
            self.assertEqual(tuple(candidate), EXCLUDED_CANDIDATE_FIELDS)
            self.assertEqual(
                candidate["review_status"],
                "excluded_duplicate_existing_prompt",
            )
            self.assertIn(_normalize(candidate["prompt_text_normalized"]), existing)
            self.assertGreaterEqual(len(candidate["duplicate_references"]), 1)

    def test_review_pack_candidates_cover_snapshot_once(self):
        snapshot_ids = {
            candidate["candidate_id"] for candidate in self.snapshot["candidates"]
        }
        review_ids = {
            candidate["candidate_id"]
            for candidate in self.pack["eligible_candidates"]
        } | {
            candidate["candidate_id"]
            for candidate in self.pack["excluded_candidates"]
        }
        self.assertEqual(review_ids, snapshot_ids)

    def test_shape_axes_are_bounded_review_metadata_only(self):
        self.assertEqual(tuple(self.pack["shape_axis_enum"]), SHAPE_AXIS_ENUM)
        for candidate in self.pack["eligible_candidates"]:
            self.assertGreaterEqual(len(candidate["suggested_shape_axes"]), 1)
            for axis in candidate["suggested_shape_axes"]:
                self.assertIn(axis, SHAPE_AXIS_ENUM)

    def test_review_pack_file_is_ascii(self):
        with open(REVIEW_PACK_PATH, "rb") as handle:
            handle.read().decode("ascii")


if __name__ == "__main__":
    unittest.main()
