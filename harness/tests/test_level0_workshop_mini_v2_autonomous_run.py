"""Tests for the Mini-V2 autonomous-loop proposal report."""

import json
import os
import unittest

from harness import level0_workshop_mini_v2_autonomous_run as mini_v2_run
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


REPORT_PATH = os.path.join(
    "harness",
    "mini_v2_runs",
    "L0-WS-MINI-V2-AUTONOMOUS-RUN-v2.report.json",
)

HOLDOUT_NAME = "L0-WS-PARSER-QUALITY-MINI-V2-HOLDOUT.intent.matrix.json"


def _load_report():
    with open(REPORT_PATH, "r", encoding="ascii") as handle:
        return json.load(handle)


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, sub_value in value.items():
            yield from _walk_strings(key)
            yield from _walk_strings(sub_value)
    elif isinstance(value, list):
        for sub_value in value:
            yield from _walk_strings(sub_value)


class Level0WorkshopMiniV2AutonomousRunTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = _load_report()

    def test_report_matches_live_run_output(self):
        live = mini_v2_run.build_mini_v2_autonomous_run_report()
        self.assertEqual(self.report, live)

    def test_report_shape_and_counts(self):
        self.assertEqual(
            tuple(self.report),
            mini_v2_run.MINI_V2_AUTONOMOUS_RUN_REPORT_FIELDS,
        )
        self.assertEqual(
            self.report["mini_v2_autonomous_run_report_kind"],
            mini_v2_run.MINI_V2_AUTONOMOUS_RUN_REPORT_KIND,
        )
        summary = self.report["matrix_result_summary"]
        self.assertEqual(summary["matrix_id"], "L0-WS-PARSER-QUALITY-MINI-V2")
        self.assertEqual(summary["case_count"], 12)
        self.assertEqual(summary["passed_count"], 6)
        self.assertEqual(summary["failed_count"], 6)
        self.assertEqual(
            summary["per_failure_class_counts"]["out_of_scope_underdetect"],
            3,
        )
        self.assertEqual(
            summary["per_failure_class_counts"]["frame_c_synthesis_rule_gap"],
            2,
        )
        self.assertEqual(
            summary["per_failure_class_counts"]["frame_c_ambiguity_misreport"],
            1,
        )
        self.assertEqual(
            summary["per_failure_class_counts"]["expected_field_drift"],
            0,
        )

    def test_report_is_proposal_only_and_non_authorizing(self):
        for key in (
            "holdout_matrix_read",
            "materialization_authorized",
            "human_review_gate",
            "variant_execution_authorized",
            "variant_execution_performed",
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
            "expected_fields_generated",
            "parser_core_write_performed",
            "matrix_write_performed",
        ):
            self.assertIs(self.report[key], False)
        self.assertTrue(self.report["parser_core_unchanged"])

    def test_proposal_bundles_cover_planner_candidates_without_variants(self):
        candidates = self.report["planner_result"]["upgrade_candidates"]
        bundles = self.report["proposal_bundles"]
        self.assertEqual(self.report["planner_result"]["candidate_count"], 3)
        self.assertEqual(len(bundles), len(candidates))
        self.assertEqual(
            [bundle["candidate_id"] for bundle in bundles],
            [candidate["candidate_id"] for candidate in candidates],
        )
        for bundle in bundles:
            self.assertEqual(
                tuple(bundle), mini_v2_run.PROPOSAL_BUNDLE_FIELDS
            )
            self.assertIs(bundle["materialization_authorized"], False)
            self.assertIs(bundle["human_review_gate"], False)
            self.assertIs(bundle["variant_execution_authorized"], False)
            self.assertIs(bundle["variant_execution_performed"], False)
            self.assertEqual(
                bundle["case_review"]["candidate_id"], bundle["candidate_id"]
            )

    def test_report_generation_leaves_parser_core_and_matrices_unchanged(self):
        paths = list(mini_v2_run.PARSER_CORE_PATHS) + [
            mini_v2_run.MINI_V2_MATRIX_PATH,
            os.path.join(
                "harness",
                "intent_test_matrices",
                HOLDOUT_NAME,
            ),
        ]
        before = {}
        for path in paths:
            with open(path, "rb") as handle:
                before[path] = handle.read()
        mini_v2_run.build_mini_v2_autonomous_run_report()
        for path in paths:
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), before[path])

    def test_holdout_is_not_referenced_by_autonomous_run_paths(self):
        scanned_paths = [
            os.path.join("harness", "level0_workshop_mini_v2_autonomous_run.py"),
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
                self.assertNotIn(HOLDOUT_NAME, handle.read())

    def test_autonomous_run_module_does_not_import_materializers(self):
        with open(
            os.path.join("harness", "level0_workshop_mini_v2_autonomous_run.py"),
            "r",
            encoding="ascii",
        ) as handle:
            source = handle.read()
        forbidden = (
            "level0_workshop_matrix_delta_autonomy",
            "level0_workshop_frame_b_overlay_autonomy",
            "level0_workshop_composite_patch_autonomy",
            "materialize_accepted",
            "human_review_gate=True",
            "materialization_authorized=True",
            "import subprocess",
            "from subprocess",
            "import socket",
            "from socket",
            "import urllib",
            "from urllib",
            "os.environ",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_report_contains_no_forbidden_claim_phrases(self):
        for text in _walk_strings(self.report):
            lowered = text.lower()
            for phrase in FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(phrase, lowered)

    def test_report_file_is_ascii(self):
        with open(REPORT_PATH, "rb") as handle:
            handle.read().decode("ascii")


if __name__ == "__main__":
    unittest.main()
