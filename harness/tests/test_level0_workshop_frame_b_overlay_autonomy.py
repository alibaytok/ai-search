import copy
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_frame_b_overlay_autonomy import (
    FRAME_B_OVERLAY_BUNDLE_FIELDS,
    FRAME_B_OVERLAY_DECISION_REASONS,
    FRAME_B_OVERLAY_EXECUTION_LOG_FIELDS,
    FrameBMaterializationNotAuthorized,
    FrameBMaterializationStaleSource,
    materialize_accepted_frame_b_canonicals,
    run_frame_b_overlay_candidate,
)
from harness.level0_workshop_intent_test_matrix_runner import (
    GATING_BOOLEANS,
    run_intent_test_matrix,
)
from harness.level0_workshop_signal_evidence import SIGNAL_FAMILIES


MINI_V1_PATH = os.path.join(
    "harness",
    "intent_test_matrices",
    "L0-WS-PARSER-QUALITY-MINI-V1.intent.matrix.json",
)


def _upg_002_delta():
    return {
        "patch_kind": "frame_b_canonical_addition",
        "canonical_additions": {
            "action.create": ["author", "define", "draft"],
            "repo_meta_near_miss.repo_navigation": [
                "what is this repository about",
                "how is the project structured",
            ],
            "action.set_up": ["run"],
        },
    }


def _accepted_materialization_bundle():
    bundle = copy.deepcopy(FrameBOverlayAutonomyTest.bundle)
    bundle["decision"] = "accepted"
    bundle["decision_reasons"] = ["accepted_strict_improvement"]
    bundle["accepted_family_ids"] = ["action.create"]
    bundle["canonical_additions"]["action.create"] = ["draft"]
    bundle["canonical_additions"]["action.set_up"] = ["bootstrap"]
    return bundle


class FrameBOverlayAutonomyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = run_frame_b_overlay_candidate(
            MINI_V1_PATH, _upg_002_delta(), EventLog()
        )

    def test_overlay_candidate_has_no_remaining_strict_improvement(self):
        self.assertEqual(self.bundle["decision"], "rejected")
        self.assertEqual(
            self.bundle["decision_reasons"], ["rejected_no_improvement"]
        )
        self.assertEqual(
            sorted(self.bundle["comparison"]["improved_cases"]),
            [],
        )
        self.assertEqual(self.bundle["comparison"]["regressed_cases"], [])
        self.assertEqual(self.bundle["comparison"]["newly_failed_cases"], [])

    def test_overlay_candidate_counts_match_probe(self):
        self.assertEqual(
            self.bundle["baseline_result_summary"],
            {
                "matrix_id": "L0-WS-PARSER-QUALITY-MINI-V1",
                "case_count": 35,
                "passed_count": 28,
                "failed_count": 7,
            },
        )
        self.assertEqual(
            self.bundle["candidate_result_summary"],
            {
                "matrix_id": "L0-WS-PARSER-QUALITY-MINI-V1",
                "case_count": 35,
                "passed_count": 28,
                "failed_count": 7,
            },
        )

    def test_bundle_shape_and_gating_booleans(self):
        self.assertEqual(tuple(self.bundle), FRAME_B_OVERLAY_BUNDLE_FIELDS)
        self.assertRegex(self.bundle["frame_b_source_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(
            self.bundle["candidate_case_results_sha256"], r"^[0-9a-f]{64}$"
        )
        self.assertEqual(len(self.bundle["candidate_case_results"]), 35)
        self.assertFalse(self.bundle["materialization_authorized"])
        self.assertTrue(self.bundle["variant_execution_performed"])
        for key in GATING_BOOLEANS:
            self.assertIs(self.bundle[key], False)

    def test_per_family_effects_identify_only_proven_groups(self):
        self.assertEqual(
            self.bundle["accepted_family_ids"],
            [],
        )
        self.assertEqual(
            self.bundle["affected_by_family"]["action.create"]["decision"],
            "rejected",
        )
        self.assertEqual(
            self.bundle["affected_by_family"]["repo_meta_near_miss.repo_navigation"][
                "decision"
            ],
            "rejected",
        )
        self.assertEqual(
            self.bundle["affected_by_family"]["action.set_up"]["decision"],
            "rejected",
        )

    def test_execution_log_is_ordered_and_bounded(self):
        self.assertEqual(
            [event["stage"] for event in self.bundle["execution_log"]],
            [
                "validate_delta",
                "run_baseline_matrix",
                "build_overlay",
                "run_candidate_matrix",
                "compare",
                "decide",
            ],
        )
        for index, event in enumerate(self.bundle["execution_log"], start=1):
            self.assertEqual(tuple(event), FRAME_B_OVERLAY_EXECUTION_LOG_FIELDS)
            self.assertEqual(event["event_index"], index)
            self.assertEqual(event["step_index"], index)

    def test_decision_reasons_are_bounded(self):
        for reason in self.bundle["decision_reasons"]:
            self.assertIn(reason, FRAME_B_OVERLAY_DECISION_REASONS)

    def test_no_overlay_path_is_identity(self):
        baseline = run_intent_test_matrix(MINI_V1_PATH, EventLog())
        explicit_none = run_intent_test_matrix(
            MINI_V1_PATH, EventLog(), signal_families=None
        )
        self.assertEqual(explicit_none, baseline)

    def test_signal_families_not_mutated(self):
        before = copy.deepcopy(SIGNAL_FAMILIES)
        before_id = id(SIGNAL_FAMILIES)
        run_frame_b_overlay_candidate(MINI_V1_PATH, _upg_002_delta(), EventLog())
        self.assertEqual(id(SIGNAL_FAMILIES), before_id)
        self.assertEqual(SIGNAL_FAMILIES, before)

    def test_input_delta_is_not_mutated(self):
        delta = _upg_002_delta()
        before = copy.deepcopy(delta)
        run_frame_b_overlay_candidate(MINI_V1_PATH, delta, EventLog())
        self.assertEqual(delta, before)

    def test_invalid_delta_rejected_before_variant_run(self):
        with self.assertRaises(Exception):
            run_frame_b_overlay_candidate(
                MINI_V1_PATH,
                {
                    "patch_kind": "frame_b_logic_change",
                    "canonical_additions": {"action.create": ["author"]},
                },
                EventLog(),
            )

    def test_runner_optional_overlay_does_not_change_baseline_contract(self):
        result = run_intent_test_matrix(MINI_V1_PATH, EventLog())
        self.assertEqual(result["case_count"], 35)
        self.assertEqual(result["passed_count"], 28)
        self.assertEqual(result["failed_count"], 7)

    def test_frame_b_single_resolver_invariant(self):
        path = os.path.join("harness", "level0_workshop_signal_evidence.py")
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        self.assertIn("def _resolve_signal_families(signal_families):", source)
        self.assertIn(
            "families = _resolve_signal_families(signal_families)", source
        )
        self.assertNotIn("for family in SIGNAL_FAMILIES:", source)

    def test_static_scan_has_no_process_or_network_imports(self):
        paths = [
            os.path.join("harness", "level0_workshop_frame_b_overlay_autonomy.py"),
            os.path.join("harness", "level0_workshop_signal_families_overlay.py"),
        ]
        forbidden = (
            "import subprocess",
            "from subprocess",
            "import socket",
            "from socket",
            "import urllib",
            "from urllib",
            "import http",
            "from http",
            "os.environ",
        )
        for path in paths:
            with self.subTest(path=path):
                with open(path, "r", encoding="ascii") as handle:
                    source = handle.read()
                for token in forbidden:
                    self.assertNotIn(token, source)

    def test_static_scan_import_scope_is_bounded(self):
        path = os.path.join("harness", "level0_workshop_frame_b_overlay_autonomy.py")
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        forbidden_parser_imports = (
            "level0_workshop_normalized_prompt_view",
            "level0_workshop_canonical_intent_frame",
        )
        for token in forbidden_parser_imports:
            self.assertNotIn(token, source)
        self.assertIn("from harness.level0_workshop_signal_evidence import", source)

    def _temp_signal_source(self):
        source_path = os.path.join("harness", "level0_workshop_signal_evidence.py")
        handle = tempfile.NamedTemporaryFile(delete=False, suffix=".py")
        handle.close()
        with open(source_path, "rb") as src:
            original = src.read()
        with open(handle.name, "wb") as dst:
            dst.write(original)
        return handle.name, original

    def test_materializer_requires_explicit_authorization(self):
        path, original = self._temp_signal_source()
        try:
            with self.assertRaises(FrameBMaterializationNotAuthorized):
                materialize_accepted_frame_b_canonicals(
                    _accepted_materialization_bundle(),
                    path,
                    materialization_authorized=False,
                )
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), original)
        finally:
            os.remove(path)

    def test_materializer_rejects_stale_source(self):
        path, original = self._temp_signal_source()
        try:
            with open(path, "a", encoding="ascii") as handle:
                handle.write("\n# stale source marker\n")
            changed = None
            with open(path, "rb") as handle:
                changed = handle.read()
            with self.assertRaises(FrameBMaterializationStaleSource):
                materialize_accepted_frame_b_canonicals(
                    _accepted_materialization_bundle(),
                    path,
                    materialization_authorized=True,
                )
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), changed)
        finally:
            os.remove(path)

    def test_materializer_writes_only_accepted_family_terms_to_temp_source(self):
        path, original = self._temp_signal_source()
        try:
            result = materialize_accepted_frame_b_canonicals(
                _accepted_materialization_bundle(),
                path,
                materialization_authorized=True,
            )
            self.assertEqual(
                result["materialized_family_ids"],
                ["action.create"],
            )
            self.assertRegex(result["frame_b_source_sha256"], r"^[0-9a-f]{64}$")
            self.assertIsNone(result["materialized_case_results_sha256"])
            with open(path, "r", encoding="ascii") as handle:
                source = handle.read()
            self.assertIn('"author",', source)
            self.assertIn('"define",', source)
            self.assertIn('"draft",', source)
            self.assertNotIn('"bootstrap",', source)
            compile(source, path, "exec")
            self.assertNotEqual(source.encode("ascii"), original)
        finally:
            os.remove(path)


if __name__ == "__main__":
    unittest.main()
