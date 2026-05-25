"""Tests for the versioned Level 0 raw candidate snapshot."""

import json
import os
import unittest

from harness import level0_workshop_corpus_crawler as crawler


SNAPSHOT_PATH = os.path.join(
    "harness",
    "raw_candidate_pools",
    "L0-WS-RAW-CANDIDATES-v1.raw_candidates.json",
)


class Level0WorkshopRawCandidateSnapshotTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open(SNAPSHOT_PATH, "r", encoding="ascii") as handle:
            cls.snapshot = json.load(handle)

    def test_snapshot_matches_current_default_crawler_output(self):
        self.assertEqual(self.snapshot, crawler.crawl_level0_raw_candidates())

    def test_snapshot_shape_is_bounded(self):
        self.assertEqual(
            tuple(self.snapshot), crawler.RAW_CANDIDATE_REPORT_FIELDS
        )
        self.assertEqual(
            self.snapshot["raw_candidate_report_kind"],
            crawler.RAW_CANDIDATE_REPORT_KIND,
        )
        self.assertEqual(self.snapshot["candidate_count"], 69)
        self.assertEqual(self.snapshot["source_count"], 4)
        self.assertEqual(
            self.snapshot["max_candidate_count"], crawler.MAX_RAW_CANDIDATES
        )

    def test_snapshot_is_raw_only_and_non_authorizing(self):
        self.assertFalse(self.snapshot["corpus_admission_authorized"])
        self.assertFalse(self.snapshot["expected_fields_generated"])
        self.assertFalse(self.snapshot["parser_invocation_performed"])
        self.assertFalse(self.snapshot["network_access_performed"])
        for candidate in self.snapshot["candidates"]:
            self.assertEqual(tuple(candidate), crawler.RAW_CANDIDATE_FIELDS)
            self.assertEqual(candidate["admission_status"], "raw")
            self.assertEqual(
                candidate["admission_reason"], "pending_human_review"
            )
            self.assertNotIn("expected", candidate)
            self.assertNotIn("expected_fields", candidate)

    def test_snapshot_candidate_ids_and_prompts_are_deterministic(self):
        expected_ids = [
            "RC-{0:05d}".format(index)
            for index in range(1, self.snapshot["candidate_count"] + 1)
        ]
        actual_ids = [
            candidate["candidate_id"]
            for candidate in self.snapshot["candidates"]
        ]
        self.assertEqual(actual_ids, expected_ids)
        normalized_prompts = [
            candidate["prompt_text_normalized"].lower()
            for candidate in self.snapshot["candidates"]
        ]
        self.assertEqual(len(normalized_prompts), len(set(normalized_prompts)))

    def test_snapshot_keeps_mini_v1_duplicates_raw_for_future_dedup(self):
        matrix_candidates = [
            candidate for candidate in self.snapshot["candidates"]
            if candidate["source_kind"] == "matrix_file"
        ]
        self.assertEqual(len(matrix_candidates), 35)
        self.assertTrue(
            all(candidate["admission_status"] == "raw"
                for candidate in matrix_candidates)
        )

    def test_snapshot_file_is_ascii(self):
        with open(SNAPSHOT_PATH, "rb") as handle:
            payload = handle.read()
        payload.decode("ascii")


if __name__ == "__main__":
    unittest.main()
