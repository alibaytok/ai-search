"""Tests for bounded composite patch autonomy."""

import copy
import json
import os
import tempfile
import unittest
from unittest import mock

from harness.event_log import EventLog
import harness.level0_workshop_composite_patch_autonomy as autonomy
from harness.level0_workshop_composite_patch_autonomy import (
    CompositePatchMalformedDelta,
    CompositePatchMaterializationNotAuthorized,
    CompositePatchMaterializationRejectedBundle,
    CompositePatchMaterializationStaleSource,
    CompositePatchMaterializationVerificationFailed,
    materialize_accepted_composite_patch,
    run_composite_patch_candidate,
)
import harness.level0_workshop_signal_evidence as signal_evidence_module


MINI_V1_PATH = (
    "harness/intent_test_matrices/"
    "L0-WS-PARSER-QUALITY-MINI-V1.intent.matrix.json"
)


def _load_mini_v1():
    with open(MINI_V1_PATH, "r", encoding="ascii") as handle:
        return json.load(handle)


def _write_temp_matrix(matrix_dict):
    fd, path = tempfile.mkstemp(
        suffix=".intent.matrix.json", prefix="L0WS_COMPOSITE_TEST_"
    )
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        json.dump(matrix_dict, handle, ensure_ascii=True, sort_keys=True)
    return path


def _make_temp_source_copy():
    with open(signal_evidence_module.__file__, "rb") as handle:
        payload = handle.read()
    fd, path = tempfile.mkstemp(
        suffix=".py", prefix="L0WS_COMPOSITE_SIGNAL_TEST_"
    )
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
    return path


def _matrix_with_composite_case():
    matrix = _load_mini_v1()
    matrix["cases"].append(
        {
            "case_id": "TC-COMP-001",
            "prompt_text": "Compose a skill for incident triage.",
            "expected": {
                "category": "C. skill intent",
                "expected_item_kinds_touched": ["skill"],
                "ambiguity_observed": True,
                "normalized_intent_observation": "skill_intent",
                "candidate_surface_expected": (
                    "multiple candidate surfaces expected"
                ),
                "rejection_surface_expected": "no_forced_selection",
            },
            "tolerated_variants": [],
            "tags": ["composite_test"],
            "rationale": "Synthetic composite case for ordered deltas.",
        }
    )
    return matrix


def _composite_delta():
    return {
        "patch_kind": "composite_patch",
        "steps": [
            {
                "patch_kind": "frame_b_canonical_addition",
                "canonical_additions": {"action.create": ["compose"]},
            },
            {
                "patch_kind": "matrix_expected_field_update",
                "case_id": "TC-COMP-001",
                "expected_updates": {
                    "ambiguity_observed": False,
                    "candidate_surface_expected": (
                        "candidate fragment of declared shape"
                    ),
                },
            },
        ],
    }


class CompositePatchAutonomyTest(unittest.TestCase):
    def test_candidate_accepts_ordered_composite_patch(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
        finally:
            os.remove(path)
        self.assertEqual(bundle["decision"], "accepted")
        self.assertEqual(
            bundle["decision_reasons"], ["accepted_strict_improvement"]
        )
        self.assertEqual(bundle["comparison"]["improved_cases"], ["TC-COMP-001"])
        self.assertEqual(bundle["comparison"]["regressed_cases"], [])
        self.assertEqual(bundle["baseline_result_summary"]["passed_count"], 28)
        self.assertEqual(bundle["candidate_result_summary"]["passed_count"], 29)

    def test_candidate_shape_and_gating_booleans(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
        finally:
            os.remove(path)
        self.assertEqual(
            tuple(bundle), autonomy.COMPOSITE_PATCH_CANDIDATE_FIELDS
        )
        self.assertRegex(bundle["baseline_matrix_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(bundle["frame_b_source_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(
            bundle["candidate_case_results_sha256"], r"^[0-9a-f]{64}$"
        )
        self.assertEqual(len(bundle["candidate_case_results"]), 36)
        self.assertIs(bundle["materialization_authorized"], False)
        self.assertIs(bundle["variant_execution_performed"], True)
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
        ):
            self.assertIs(bundle[key], False)

    def test_execution_log_is_ordered_and_bounded(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
        finally:
            os.remove(path)
        stages = [event["stage"] for event in bundle["execution_log"]]
        self.assertEqual(
            stages,
            [
                "validate_composite_delta",
                "run_baseline_matrix",
                "apply_matrix_steps",
                "build_frame_b_overlay",
                "write_candidate_matrix",
                "run_candidate_matrix",
                "delete_candidate_matrix",
                "compare_and_decide",
                "scan_candidate",
            ],
        )
        for event in bundle["execution_log"]:
            self.assertEqual(
                tuple(event), autonomy.COMPOSITE_PATCH_EXECUTION_LOG_FIELDS
            )

    def test_rejects_malformed_composite_delta(self):
        with self.assertRaises(CompositePatchMalformedDelta):
            run_composite_patch_candidate(
                MINI_V1_PATH,
                {"patch_kind": "composite_patch", "steps": []},
                EventLog(),
            )
        bad_delta = _composite_delta()
        bad_delta["steps"][0]["patch_kind"] = "composite_patch"
        with self.assertRaises(CompositePatchMalformedDelta):
            run_composite_patch_candidate(MINI_V1_PATH, bad_delta, EventLog())

    def test_epoch_boundary_allows_only_table_and_matrix_inner_steps(self):
        self.assertEqual(autonomy.MAX_COMPOSITE_STEPS, 5)
        self.assertEqual(
            autonomy.COMPOSITE_INNER_PATCH_KINDS,
            ("frame_b_canonical_addition", "matrix_expected_field_update"),
        )
        forbidden_step_kinds = (
            "composite_patch",
            "frame_c_shape_rule_update",
            "clarification_surface_update",
            "vocabulary_correction_update",
        )
        for patch_kind in forbidden_step_kinds:
            delta = _composite_delta()
            delta["steps"][0]["patch_kind"] = patch_kind
            with self.assertRaises(CompositePatchMalformedDelta):
                run_composite_patch_candidate(MINI_V1_PATH, delta, EventLog())

    def test_rejects_conflicting_matrix_step_values(self):
        delta = _composite_delta()
        delta["steps"].append(
            {
                "patch_kind": "matrix_expected_field_update",
                "case_id": "TC-COMP-001",
                "expected_updates": {"ambiguity_observed": True},
            }
        )
        path = _write_temp_matrix(_matrix_with_composite_case())
        try:
            with self.assertRaises(CompositePatchMalformedDelta):
                run_composite_patch_candidate(path, delta, EventLog())
        finally:
            os.remove(path)

    def test_input_delta_is_not_mutated(self):
        delta = _composite_delta()
        original = copy.deepcopy(delta)
        path = _write_temp_matrix(_matrix_with_composite_case())
        try:
            run_composite_patch_candidate(path, delta, EventLog())
        finally:
            os.remove(path)
        self.assertEqual(delta, original)

    def test_materializer_requires_explicit_authorization(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        source_path = _make_temp_source_copy()
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
            with self.assertRaises(CompositePatchMaterializationNotAuthorized):
                materialize_accepted_composite_patch(
                    bundle, path, source_path, event_log=EventLog()
                )
        finally:
            os.remove(path)
            os.remove(source_path)

    def test_materializer_rejects_rejected_bundle(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        source_path = _make_temp_source_copy()
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
            bundle["decision"] = "rejected"
            bundle["decision_reasons"] = ["rejected_no_improvement"]
            with self.assertRaises(CompositePatchMaterializationRejectedBundle):
                materialize_accepted_composite_patch(
                    bundle,
                    path,
                    source_path,
                    materialization_authorized=True,
                    event_log=EventLog(),
                )
        finally:
            os.remove(path)
            os.remove(source_path)

    def test_materializer_rejects_stale_matrix_or_source(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        source_path = _make_temp_source_copy()
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
            with open(path, "a", encoding="ascii") as handle:
                handle.write(" ")
            with self.assertRaises(CompositePatchMaterializationStaleSource):
                materialize_accepted_composite_patch(
                    bundle,
                    path,
                    source_path,
                    materialization_authorized=True,
                    event_log=EventLog(),
                )
        finally:
            os.remove(path)
            os.remove(source_path)

        path = _write_temp_matrix(_matrix_with_composite_case())
        source_path = _make_temp_source_copy()
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
            with open(source_path, "a", encoding="ascii") as handle:
                handle.write("# stale\n")
            with self.assertRaises(CompositePatchMaterializationStaleSource):
                materialize_accepted_composite_patch(
                    bundle,
                    path,
                    source_path,
                    materialization_authorized=True,
                    event_log=EventLog(),
                )
        finally:
            os.remove(path)
            os.remove(source_path)

    def test_materializer_writes_both_artifacts_to_temp_paths(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        source_path = _make_temp_source_copy()
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
            result = materialize_accepted_composite_patch(
                bundle,
                path,
                source_path,
                materialization_authorized=True,
                event_log=EventLog(),
            )
            with open(source_path, "r", encoding="ascii") as handle:
                source = handle.read()
            with open(path, "r", encoding="ascii") as handle:
                matrix = json.load(handle)
            self.assertIn('"compose",', source)
            compile(source, source_path, "exec")
            case = next(
                item for item in matrix["cases"]
                if item["case_id"] == "TC-COMP-001"
            )
            self.assertIs(case["expected"]["ambiguity_observed"], False)
            self.assertEqual(
                case["expected"]["candidate_surface_expected"],
                "candidate fragment of declared shape",
            )
            self.assertEqual(
                tuple(result), autonomy.COMPOSITE_PATCH_MATERIALIZATION_FIELDS
            )
            self.assertIs(result["materialization_performed"], True)
            self.assertIsNone(result["materialized_case_results_sha256"])
        finally:
            os.remove(path)
            os.remove(source_path)

    def test_materializer_rolls_back_both_artifacts_on_verification_mismatch(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        source_path = _make_temp_source_copy()
        with open(path, "rb") as handle:
            original_matrix = handle.read()
        with open(source_path, "rb") as handle:
            original_source = handle.read()
        try:
            bundle = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
            poisoned = copy.deepcopy(bundle)
            poisoned["candidate_case_results_sha256"] = "0" * 64
            with mock.patch.object(
                autonomy.frame_b_autonomy,
                "_source_path_is_real_signal_module",
                return_value=True,
            ), mock.patch.object(
                autonomy.frame_b_autonomy, "_reload_parser_modules"
            ):
                with self.assertRaises(
                    CompositePatchMaterializationVerificationFailed
                ):
                    materialize_accepted_composite_patch(
                        poisoned,
                        path,
                        source_path,
                        materialization_authorized=True,
                        event_log=EventLog(),
                    )
            with open(path, "rb") as handle:
                self.assertEqual(handle.read(), original_matrix)
            with open(source_path, "rb") as handle:
                self.assertEqual(handle.read(), original_source)
        finally:
            if os.path.exists(path):
                with open(path, "wb") as handle:
                    handle.write(original_matrix)
                os.remove(path)
            if os.path.exists(source_path):
                with open(source_path, "wb") as handle:
                    handle.write(original_source)
                os.remove(source_path)

    def test_repeated_candidate_runs_are_deterministic(self):
        path = _write_temp_matrix(_matrix_with_composite_case())
        try:
            first = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
            second = run_composite_patch_candidate(
                path, _composite_delta(), EventLog()
            )
        finally:
            os.remove(path)
        self.assertEqual(first, second)

    def test_static_scan_has_no_process_or_network_imports(self):
        with open(
            "harness/level0_workshop_composite_patch_autonomy.py",
            "r",
            encoding="ascii",
        ) as handle:
            source = handle.read()
        for forbidden in (
            "subprocess",
            "socket",
            "urllib",
            "http",
            "requests",
            "os.environ",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
