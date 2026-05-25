"""Contract tests for matrix expected-field delta autonomy."""

import copy
import glob
import hashlib
import json
import os
import tempfile
import unittest
from unittest import mock

from harness.event_log import EventLog
from harness.level0_workshop_intent_test_matrix_runner import (
    run_intent_test_matrix,
)
from harness import level0_workshop_matrix_delta_autonomy as autonomy


_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
_MINI_V1_PATH = os.path.join(
    _ROOT,
    "harness",
    "intent_test_matrices",
    "L0-WS-PARSER-QUALITY-MINI-V1.intent.matrix.json",
)


def _sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        digest.update(handle.read())
    return digest.hexdigest()


def _accepted_qm011_delta():
    return {
        "patch_kind": "matrix_expected_field_update",
        "case_id": "QM-011",
        "expected_updates": {
            "candidate_surface_expected": "candidate fragment of declared shape",
            "rejection_surface_expected": "no_forced_selection",
        },
    }


def _no_improvement_delta():
    return {
        "patch_kind": "matrix_expected_field_update",
        "case_id": "QM-001",
        "expected_updates": {
            "category": "B. workflow intent",
            "expected_item_kinds_touched": ["workflow_file"],
            "ambiguity_observed": False,
            "normalized_intent_observation": "workflow_intent",
            "candidate_surface_expected": "candidate fragment of declared shape",
            "rejection_surface_expected": "no_forced_selection",
        },
    }


def _temp_variant_paths():
    return set(glob.glob(os.path.join(tempfile.gettempdir(), "L0WS_VARIANT_*")))


def _make_temp_matrix_copy():
    fd, path = tempfile.mkstemp(
        suffix=".intent.matrix.json", prefix="L0WS_MATERIALIZE_TEST_"
    )
    os.close(fd)
    with open(_MINI_V1_PATH, "rb") as source:
        data = source.read()
    with open(path, "wb") as target:
        target.write(data)
    return path


def _make_temp_matrix_copy_with_qm011_drift():
    path = _make_temp_matrix_copy()
    with open(path, "r", encoding="ascii") as handle:
        matrix = json.load(handle)
    for case in matrix["cases"]:
        if case["case_id"] == "QM-011":
            case["expected"]["candidate_surface_expected"] = (
                "no candidate surface expected"
            )
            case["expected"]["rejection_surface_expected"] = (
                "prompt_out_of_repo_scope"
            )
            break
    with open(path, "w", encoding="ascii") as handle:
        json.dump(matrix, handle, ensure_ascii=True, sort_keys=True)
    return path


class MatrixDeltaAutonomyTest(unittest.TestCase):
    def test_happy_path_accepts_qm011_expected_field_update(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            self.assertEqual(bundle["decision"], "accepted")
            self.assertEqual(
                bundle["decision_reasons"], ["accepted_strict_improvement"]
            )
            self.assertEqual(bundle["comparison"]["improved_cases"], ["QM-011"])
            self.assertEqual(bundle["comparison"]["regressed_cases"], [])
            self.assertIs(bundle["materialization_authorized"], False)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_no_improvement_rejects_passing_case_delta(self):
        bundle = autonomy.run_matrix_delta_candidate(
            _MINI_V1_PATH, _no_improvement_delta(), EventLog()
        )
        self.assertEqual(bundle["decision"], "rejected")
        self.assertIn("rejected_no_improvement", bundle["decision_reasons"])
        self.assertEqual(bundle["comparison"]["improved_cases"], [])

    def test_regression_rejects_even_with_improvement(self):
        fake_comparison = {
            "parser_variant_comparison_kind": (
                "level0_workshop_parser_variant_comparison"
            ),
            "baseline_matrix_id": "L0-WS-PARSER-QUALITY-MINI-V1",
            "candidate_matrix_id": "L0-WS-PARSER-QUALITY-MINI-V1",
            "baseline_passed_count": 16,
            "candidate_passed_count": 16,
            "improved_cases": ["QM-011"],
            "regressed_cases": ["QM-001"],
            "unchanged_failures": [],
            "newly_failed_cases": ["QM-001"],
            "per_tag_delta": {},
            "per_failure_class_delta": {},
            "comparison_note": "bounded parser feedback only",
            "selection_made": False,
            "measurement_authorized": False,
            "real_benchmark_authorized": False,
            "real_benchmark_ready": False,
            "source_qualification_authorized": False,
            "corpus_admission_authorized": False,
            "route_created": False,
        }
        with mock.patch.object(
            autonomy, "compare_parser_result_sets", return_value=fake_comparison
        ):
            bundle = autonomy.run_matrix_delta_candidate(
                _MINI_V1_PATH, _accepted_qm011_delta(), EventLog()
            )
        self.assertEqual(bundle["decision"], "rejected")
        self.assertIn("rejected_regression", bundle["decision_reasons"])

    def test_unknown_case_id_halts_before_candidate_run(self):
        delta = _accepted_qm011_delta()
        delta["case_id"] = "NO-SUCH-CASE"
        with self.assertRaises(autonomy.MatrixDeltaAutonomyCaseNotFound):
            autonomy.run_matrix_delta_candidate(_MINI_V1_PATH, delta, EventLog())

    def test_unknown_patch_kind_rejected_by_schema(self):
        delta = _accepted_qm011_delta()
        delta["patch_kind"] = "frame_b_canonical_addition"
        with self.assertRaises(autonomy.MatrixDeltaAutonomyMalformedDelta):
            autonomy.run_matrix_delta_candidate(_MINI_V1_PATH, delta, EventLog())

    def test_invalid_enum_value_rejected_by_schema(self):
        delta = _accepted_qm011_delta()
        delta["expected_updates"] = {"category": "Z. invalid"}
        with self.assertRaises(autonomy.MatrixDeltaAutonomyMalformedDelta):
            autonomy.run_matrix_delta_candidate(_MINI_V1_PATH, delta, EventLog())

    def test_baseline_matrix_file_is_byte_identical_after_call(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            before = _sha256(path)
            autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            self.assertEqual(_sha256(path), before)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_temp_file_cleaned_up_on_success(self):
        before = _temp_variant_paths()
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            self.assertEqual(_temp_variant_paths(), before)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_temp_file_cleaned_up_on_candidate_exception(self):
        before = _temp_variant_paths()
        real_runner = autonomy.run_intent_test_matrix
        calls = {"count": 0}

        def fake_runner(path, event_log):
            calls["count"] += 1
            if calls["count"] == 2:
                raise RuntimeError("synthetic candidate failure")
            return real_runner(path, event_log)

        with mock.patch.object(autonomy, "run_intent_test_matrix", fake_runner):
            with self.assertRaises(RuntimeError):
                autonomy.run_matrix_delta_candidate(
                    _MINI_V1_PATH, _accepted_qm011_delta(), EventLog()
                )
        self.assertEqual(_temp_variant_paths(), before)

    def test_bundle_shape_and_gating_booleans(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.assertEqual(tuple(bundle), autonomy.MATRIX_DELTA_BUNDLE_FIELDS)
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
            "materialization_authorized",
        ):
            self.assertIs(bundle[key], False)
        self.assertIn("expected_updates", bundle)
        self.assertIn("candidate_result", bundle)
        self.assertRegex(bundle["baseline_matrix_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(
            bundle["candidate_case_results_sha256"], r"^[0-9a-f]{64}$"
        )

    def test_decision_reasons_are_bounded_enum_values(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
        finally:
            if os.path.exists(path):
                os.remove(path)
        for reason in bundle["decision_reasons"]:
            self.assertIn(reason, autonomy.MATRIX_DELTA_DECISION_REASONS)
        self.assertEqual(
            autonomy.MATRIX_DELTA_PATCH_KINDS,
            ("matrix_expected_field_update",),
        )

    def test_execution_log_has_expected_stages(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
        finally:
            if os.path.exists(path):
                os.remove(path)
        self.assertEqual(
            [entry["stage"] for entry in bundle["execution_log"]],
            [
                "validate_delta",
                "run_baseline_matrix",
                "apply_delta",
                "write_candidate_matrix",
                "run_candidate_matrix",
                "delete_candidate_matrix",
                "compare",
                "decide",
                "scan_bundle",
            ],
        )
        self.assertEqual(
            [entry["event_index"] for entry in bundle["execution_log"]],
            list(range(1, 10)),
        )
        for entry in bundle["execution_log"]:
            self.assertEqual(
                tuple(entry), autonomy.MATRIX_DELTA_EXECUTION_LOG_FIELDS
            )

    def test_forbidden_phrase_scan_runs_before_return(self):
        original = autonomy._result_summary

        def poisoned_summary(_matrix_result):
            return {"matrix_id": "production-grade"}

        try:
            autonomy._result_summary = poisoned_summary
            path = _make_temp_matrix_copy_with_qm011_drift()
            try:
                with self.assertRaises(
                    autonomy.MatrixDeltaAutonomyForbiddenClaimPhrase
                ):
                    autonomy.run_matrix_delta_candidate(
                        path, _accepted_qm011_delta(), EventLog()
                    )
            finally:
                if os.path.exists(path):
                    os.remove(path)
        finally:
            autonomy._result_summary = original

    def test_repeated_runs_are_deterministic(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            first = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            second = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            self.assertEqual(first, second)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_static_scan_has_no_parser_layer_or_process_imports(self):
        path = os.path.join(
            _ROOT, "harness", "level0_workshop_matrix_delta_autonomy.py"
        )
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        for token in (
            "level0_workshop_normalized_prompt_view",
            "level0_workshop_signal_evidence",
            "level0_workshop_canonical_intent_frame",
            "level0_workshop_user_intent_mapper",
            "subprocess",
            "socket",
            "urllib",
            "http",
            "os.environ",
        ):
            self.assertNotIn(token, source)

    def test_delta_input_is_not_mutated(self):
        delta = _accepted_qm011_delta()
        original = copy.deepcopy(delta)
        autonomy.run_matrix_delta_candidate(_MINI_V1_PATH, delta, EventLog())
        self.assertEqual(delta, original)

    def test_materialize_accepted_delta_updates_temp_matrix_and_verifies(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            result = autonomy.materialize_accepted_matrix_delta(
                bundle, path, materialization_authorized=True, event_log=EventLog()
            )
            self.assertEqual(
                result["matrix_delta_materialization_kind"],
                "level0_workshop_matrix_delta_materialization",
            )
            self.assertIs(result["materialization_requested"], True)
            self.assertIs(result["materialization_performed"], True)
            self.assertIs(result["verification_passed"], True)
            matrix_result = run_intent_test_matrix(path, EventLog())
            qm011 = next(
                cr for cr in matrix_result["case_results"]
                if cr["case_id"] == "QM-011"
            )
            self.assertIs(qm011["match"], True)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_materialize_requires_explicit_authorization(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            before = _sha256(path)
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            with self.assertRaises(
                autonomy.MatrixDeltaAutonomyMaterializationNotAuthorized
            ):
                autonomy.materialize_accepted_matrix_delta(
                    bundle, path, materialization_authorized=False
                )
            self.assertEqual(_sha256(path), before)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_materialize_rejects_stale_baseline_matrix(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            with open(path, "r", encoding="ascii") as handle:
                matrix = json.load(handle)
            matrix["matrix_note"] = "bounded parser review matrix changed"
            with open(path, "w", encoding="ascii") as handle:
                json.dump(matrix, handle, ensure_ascii=True, sort_keys=True)
            changed_hash = _sha256(path)
            with self.assertRaises(autonomy.MatrixDeltaAutonomyStaleBaseline):
                autonomy.materialize_accepted_matrix_delta(
                    bundle, path, materialization_authorized=True
                )
            self.assertEqual(_sha256(path), changed_hash)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_materialize_rejects_rejected_bundle(self):
        path = _make_temp_matrix_copy()
        try:
            before = _sha256(path)
            bundle = autonomy.run_matrix_delta_candidate(
                path, _no_improvement_delta(), EventLog()
            )
            self.assertEqual(bundle["decision"], "rejected")
            with self.assertRaises(
                autonomy.MatrixDeltaAutonomyMaterializationRejected
            ):
                autonomy.materialize_accepted_matrix_delta(
                    bundle, path, materialization_authorized=True
                )
            self.assertEqual(_sha256(path), before)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_materialize_rolls_back_on_verification_mismatch(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            before = _sha256(path)
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            poisoned = copy.deepcopy(bundle)
            poisoned["candidate_result"]["case_results"][0]["match"] = (
                not poisoned["candidate_result"]["case_results"][0]["match"]
            )
            with self.assertRaises(
                autonomy.MatrixDeltaAutonomyMaterializationVerificationFailed
            ):
                autonomy.materialize_accepted_matrix_delta(
                    poisoned, path, materialization_authorized=True
                )
            self.assertEqual(_sha256(path), before)
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_materialization_result_shape_and_gating_booleans(self):
        path = _make_temp_matrix_copy_with_qm011_drift()
        try:
            bundle = autonomy.run_matrix_delta_candidate(
                path, _accepted_qm011_delta(), EventLog()
            )
            result = autonomy.materialize_accepted_matrix_delta(
                bundle, path, materialization_authorized=True
            )
            self.assertEqual(
                tuple(result), autonomy.MATRIX_DELTA_MATERIALIZATION_FIELDS
            )
            self.assertRegex(result["baseline_matrix_sha256"], r"^[0-9a-f]{64}$")
            self.assertRegex(
                result["materialized_case_results_sha256"], r"^[0-9a-f]{64}$"
            )
            for key in (
                "selection_made",
                "measurement_authorized",
                "real_benchmark_authorized",
                "real_benchmark_ready",
                "source_qualification_authorized",
                "corpus_admission_authorized",
                "route_created",
            ):
                self.assertIs(result[key], False)
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
