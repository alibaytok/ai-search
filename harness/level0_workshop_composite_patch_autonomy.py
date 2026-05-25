"""Composite patch autonomy for bounded parser-quality deltas."""

import copy
import os

from harness.event_log import EventLog
from harness.level0_workshop_intent_test_matrix_runner import (
    GATING_BOOLEANS,
    run_intent_test_matrix,
)
import harness.level0_workshop_frame_b_overlay_autonomy as frame_b_autonomy
import harness.level0_workshop_matrix_delta_autonomy as matrix_autonomy
from harness.level0_workshop_parser_quality_loop import (
    ParserQualityLoopForbiddenClaimPhrase,
    _assert_no_forbidden_claim_phrase,
    compare_parser_result_sets,
)
from harness.level0_workshop_signal_families_overlay import (
    build_signal_families_overlay,
    validate_signal_families_delta,
)


COMPOSITE_PATCH_KINDS = ("composite_patch",)

COMPOSITE_INNER_PATCH_KINDS = (
    "frame_b_canonical_addition",
    "matrix_expected_field_update",
)

COMPOSITE_PATCH_DECISIONS = ("accepted", "rejected")

COMPOSITE_PATCH_DECISION_REASONS = (
    "accepted_strict_improvement",
    "rejected_no_improvement",
    "rejected_regression",
    "rejected_gating_flip",
)

COMPOSITE_PATCH_CANDIDATE_FIELDS = (
    "composite_patch_candidate_kind",
    "patch_kind",
    "steps",
    "execution_log",
    "baseline_matrix_sha256",
    "frame_b_source_sha256",
    "baseline_result_summary",
    "candidate_result_summary",
    "candidate_case_results_sha256",
    "candidate_case_results",
    "comparison",
    "decision",
    "decision_reasons",
    "materialization_authorized",
    "variant_execution_performed",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)

COMPOSITE_PATCH_MATERIALIZATION_FIELDS = (
    "composite_patch_materialization_kind",
    "patch_kind",
    "step_count",
    "materialization_requested",
    "materialization_performed",
    "verification_passed",
    "baseline_matrix_sha256",
    "frame_b_source_sha256",
    "materialized_case_results_sha256",
    "materialized_result_summary",
    "execution_log",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)

COMPOSITE_PATCH_EXECUTION_LOG_FIELDS = (
    "event_index",
    "step_index",
    "stage",
    "detail",
)

MAX_COMPOSITE_STEPS = 5


class CompositePatchMalformedDelta(Exception):
    """Raised when a composite patch is outside the bounded schema."""


class CompositePatchForbiddenClaimPhrase(Exception):
    """Raised when emitted composite text contains forbidden terms."""


class CompositePatchMaterializationNotAuthorized(Exception):
    """Raised when composite materialization lacks explicit authority."""


class CompositePatchParserCoreFreezeViolation(
    CompositePatchMaterializationNotAuthorized
):
    """Raised when parser-core writes lack the human review gate."""


class CompositePatchMaterializationRejectedBundle(Exception):
    """Raised when a rejected composite bundle is materialized."""


class CompositePatchMaterializationStaleSource(Exception):
    """Raised when a source artifact changed after candidate evaluation."""


class CompositePatchMaterializationVerificationFailed(Exception):
    """Raised when materialized output diverges from candidate output."""


def _ensure_event_log(event_log):
    if event_log is None:
        return EventLog()
    return event_log


def _append_execution_event(execution_log, step_index, stage, detail):
    event = {
        "event_index": len(execution_log) + 1,
        "step_index": step_index,
        "stage": stage,
        "detail": detail,
    }
    if tuple(event) != COMPOSITE_PATCH_EXECUTION_LOG_FIELDS:
        raise CompositePatchMalformedDelta("composite execution log drifted")
    execution_log.append(event)


def _result_summary(matrix_result):
    return {
        "matrix_id": matrix_result.get("matrix_id"),
        "case_count": matrix_result.get("case_count"),
        "passed_count": matrix_result.get("passed_count"),
        "failed_count": matrix_result.get("failed_count"),
    }


def _case_results(matrix_result):
    return copy.deepcopy(matrix_result.get("case_results", []))


def _gating_booleans_false(matrix_result):
    return all(matrix_result.get(key) is False for key in GATING_BOOLEANS)


def _decide(baseline_result, candidate_result, comparison):
    reasons = []
    if not _gating_booleans_false(baseline_result) or not _gating_booleans_false(
        candidate_result
    ):
        reasons.append("rejected_gating_flip")
    if comparison["regressed_cases"]:
        reasons.append("rejected_regression")
    if not comparison["improved_cases"]:
        reasons.append("rejected_no_improvement")
    if reasons:
        return "rejected", reasons
    return "accepted", ["accepted_strict_improvement"]


def _validate_composite_delta(delta, event_log=None):
    if not isinstance(delta, dict):
        raise CompositePatchMalformedDelta("delta must be a dict")
    if delta.get("patch_kind") not in COMPOSITE_PATCH_KINDS:
        raise CompositePatchMalformedDelta("unknown composite patch_kind")
    steps = delta.get("steps")
    if not isinstance(steps, list) or not steps:
        raise CompositePatchMalformedDelta("steps must be a non-empty list")
    if len(steps) > MAX_COMPOSITE_STEPS:
        raise CompositePatchMalformedDelta("too many composite steps")
    seen_case_fields = {}
    for step in steps:
        if not isinstance(step, dict):
            raise CompositePatchMalformedDelta("step must be a dict")
        patch_kind = step.get("patch_kind")
        if patch_kind not in COMPOSITE_INNER_PATCH_KINDS:
            raise CompositePatchMalformedDelta("unknown inner patch_kind")
        if patch_kind == "frame_b_canonical_addition":
            validate_signal_families_delta(step, event_log=event_log)
        elif patch_kind == "matrix_expected_field_update":
            matrix_autonomy._validate_delta(step, event_log=event_log)
            case_id = step["case_id"]
            for field, value in step["expected_updates"].items():
                key = (case_id, field)
                if key in seen_case_fields and seen_case_fields[key] != value:
                    raise CompositePatchMalformedDelta(
                        "conflicting matrix update for case field"
                    )
                seen_case_fields[key] = copy.deepcopy(value)


def _canonical_additions_from_steps(steps):
    additions = {}
    for step in steps:
        if step["patch_kind"] != "frame_b_canonical_addition":
            continue
        for family_id, terms in step["canonical_additions"].items():
            additions.setdefault(family_id, [])
            for term in terms:
                if term not in additions[family_id]:
                    additions[family_id].append(term)
    return additions


def _apply_matrix_steps(matrix_dict, steps, event_log=None):
    next_matrix = copy.deepcopy(matrix_dict)
    for step in steps:
        if step["patch_kind"] == "matrix_expected_field_update":
            next_matrix = matrix_autonomy._apply_delta(
                next_matrix, step, event_log=event_log
            )
    return next_matrix


def _assert_candidate_shape(bundle):
    if tuple(bundle) != COMPOSITE_PATCH_CANDIDATE_FIELDS:
        raise CompositePatchMalformedDelta("composite candidate fields drifted")
    if bundle["decision"] not in COMPOSITE_PATCH_DECISIONS:
        raise CompositePatchMalformedDelta("unknown composite decision")
    for reason in bundle["decision_reasons"]:
        if reason not in COMPOSITE_PATCH_DECISION_REASONS:
            raise CompositePatchMalformedDelta("unknown composite decision reason")


def _assert_materialization_shape(result):
    if tuple(result) != COMPOSITE_PATCH_MATERIALIZATION_FIELDS:
        raise CompositePatchMalformedDelta(
            "composite materialization fields drifted"
        )


def run_composite_patch_candidate(matrix_path, delta, event_log=None):
    """Run a bounded ordered composite patch as one candidate variant."""
    event_log = _ensure_event_log(event_log)
    delta_copy = copy.deepcopy(delta)
    execution_log = []
    _validate_composite_delta(delta_copy, event_log=event_log)
    _append_execution_event(
        execution_log, 1, "validate_composite_delta", "composite delta accepted"
    )
    baseline_matrix_sha256 = matrix_autonomy._path_sha256(matrix_path)
    frame_b_source_sha256 = frame_b_autonomy._path_sha256(
        frame_b_autonomy.signal_evidence_module.__file__
    )
    baseline_result = run_intent_test_matrix(matrix_path, event_log)
    _append_execution_event(
        execution_log, 2, "run_baseline_matrix", "baseline matrix run completed"
    )
    matrix_dict = matrix_autonomy._load_matrix(matrix_path)
    candidate_matrix = _apply_matrix_steps(
        matrix_dict, delta_copy["steps"], event_log=event_log
    )
    _append_execution_event(
        execution_log, 3, "apply_matrix_steps", "matrix steps applied to copy"
    )
    canonical_additions = _canonical_additions_from_steps(delta_copy["steps"])
    overlay = None
    if canonical_additions:
        overlay_delta = {
            "patch_kind": "frame_b_canonical_addition",
            "canonical_additions": canonical_additions,
        }
        overlay = build_signal_families_overlay(
            frame_b_autonomy.SIGNAL_FAMILIES,
            overlay_delta,
            event_log=event_log,
        )
    _append_execution_event(
        execution_log, 4, "build_frame_b_overlay", "frame b overlay prepared"
    )
    temp_path = None
    try:
        temp_path = matrix_autonomy._write_temp_matrix(candidate_matrix)
        _append_execution_event(
            execution_log, 5, "write_candidate_matrix", "candidate matrix written"
        )
        candidate_result = run_intent_test_matrix(
            temp_path, event_log, signal_families=overlay
        )
        _append_execution_event(
            execution_log, 6, "run_candidate_matrix", "candidate matrix completed"
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        _append_execution_event(
            execution_log, 7, "delete_candidate_matrix", "candidate matrix deleted"
        )
    comparison = compare_parser_result_sets(
        baseline_result, candidate_result, event_log=event_log
    )
    decision, reasons = _decide(baseline_result, candidate_result, comparison)
    _append_execution_event(
        execution_log, 8, "compare_and_decide", "composite decision completed"
    )
    candidate_case_results = _case_results(candidate_result)
    bundle = {
        "composite_patch_candidate_kind": (
            "level0_workshop_composite_patch_candidate"
        ),
        "patch_kind": delta_copy["patch_kind"],
        "steps": copy.deepcopy(delta_copy["steps"]),
        "execution_log": execution_log,
        "baseline_matrix_sha256": baseline_matrix_sha256,
        "frame_b_source_sha256": frame_b_source_sha256,
        "baseline_result_summary": _result_summary(baseline_result),
        "candidate_result_summary": _result_summary(candidate_result),
        "candidate_case_results_sha256": frame_b_autonomy._stable_json_sha256(
            candidate_case_results
        ),
        "candidate_case_results": candidate_case_results,
        "comparison": comparison,
        "decision": decision,
        "decision_reasons": reasons,
        "materialization_authorized": False,
        "variant_execution_performed": True,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }
    _assert_candidate_shape(bundle)
    try:
        _assert_no_forbidden_claim_phrase(
            bundle, event_log, "composite_patch_candidate"
        )
    except ParserQualityLoopForbiddenClaimPhrase as exc:
        raise CompositePatchForbiddenClaimPhrase(str(exc))
    _append_execution_event(
        execution_log, 9, "scan_candidate", "forbidden phrase scan passed"
    )
    _assert_candidate_shape(bundle)
    return bundle


def _restore_bytes(path, payload):
    with open(path, "wb") as handle:
        handle.write(payload)


def materialize_accepted_composite_patch(
    bundle,
    matrix_path,
    signal_evidence_path,
    materialization_authorized=False,
    human_review_gate=False,
    event_log=None,
):
    """Materialize one accepted composite patch transactionally."""
    event_log = _ensure_event_log(event_log)
    _assert_candidate_shape(bundle)
    execution_log = []
    _append_execution_event(
        execution_log,
        1,
        "validate_materialization_request",
        "composite materialization request accepted",
    )
    if materialization_authorized is not True:
        raise CompositePatchMaterializationNotAuthorized(
            "materialization_authorized must be True"
        )
    if human_review_gate is not True:
        raise CompositePatchParserCoreFreezeViolation(
            "human_review_gate must be True for parser-core writes"
        )
    if bundle["decision"] != "accepted":
        raise CompositePatchMaterializationRejectedBundle(
            "only accepted composite bundles may be materialized"
        )
    _validate_composite_delta(
        {"patch_kind": bundle["patch_kind"], "steps": bundle["steps"]},
        event_log=event_log,
    )
    with open(matrix_path, "rb") as handle:
        original_matrix_bytes = handle.read()
    with open(signal_evidence_path, "rb") as handle:
        original_source_bytes = handle.read()
    matrix_sha256 = matrix_autonomy._sha256_bytes(original_matrix_bytes)
    source_sha256 = frame_b_autonomy._sha256_bytes(original_source_bytes)
    if matrix_sha256 != bundle["baseline_matrix_sha256"]:
        raise CompositePatchMaterializationStaleSource(
            "matrix changed after candidate evaluation"
        )
    if source_sha256 != bundle["frame_b_source_sha256"]:
        raise CompositePatchMaterializationStaleSource(
            "FRAME-B source changed after candidate evaluation"
        )
    matrix_dict = matrix_autonomy._load_matrix(matrix_path)
    materialized_matrix = _apply_matrix_steps(
        matrix_dict, bundle["steps"], event_log=event_log
    )
    canonical_additions = _canonical_additions_from_steps(bundle["steps"])
    source_text = original_source_bytes.decode("ascii")
    next_source = frame_b_autonomy._apply_materialized_terms(
        source_text, canonical_additions
    )
    rollback_done = False
    materialized_result = None
    try:
        with open(signal_evidence_path, "w", encoding="ascii") as handle:
            handle.write(next_source)
        matrix_autonomy._write_matrix(matrix_path, materialized_matrix)
        _append_execution_event(
            execution_log, 2, "write_materialized_artifacts",
            "FRAME-B source and matrix written"
            )
        if frame_b_autonomy._source_path_is_real_signal_module(
            signal_evidence_path
        ):
            frame_b_autonomy._reload_parser_modules()
            materialized_result = frame_b_autonomy.run_intent_test_matrix(
                matrix_path, event_log
            )
            materialized_case_results = _case_results(materialized_result)
            materialized_case_results_sha256 = (
                frame_b_autonomy._stable_json_sha256(materialized_case_results)
            )
            _append_execution_event(
                execution_log, 3, "run_materialized_matrix",
                "materialized composite matrix run completed"
            )
            if (
                materialized_case_results_sha256
                != bundle["candidate_case_results_sha256"]
                or materialized_case_results != bundle["candidate_case_results"]
            ):
                _restore_bytes(signal_evidence_path, original_source_bytes)
                _restore_bytes(matrix_path, original_matrix_bytes)
                rollback_done = True
                frame_b_autonomy._reload_parser_modules()
                raise CompositePatchMaterializationVerificationFailed(
                    "materialized result diverged from composite candidate"
                )
        else:
            materialized_case_results_sha256 = None
            _append_execution_event(
                execution_log, 3, "run_materialized_matrix",
                "materialized run skipped for temp source"
            )
    except Exception:
        if not rollback_done:
            if os.path.exists(signal_evidence_path):
                with open(signal_evidence_path, "rb") as handle:
                    if handle.read() != original_source_bytes:
                        _restore_bytes(signal_evidence_path, original_source_bytes)
            if os.path.exists(matrix_path):
                with open(matrix_path, "rb") as handle:
                    if handle.read() != original_matrix_bytes:
                        _restore_bytes(matrix_path, original_matrix_bytes)
            if frame_b_autonomy._source_path_is_real_signal_module(
                signal_evidence_path
            ):
                frame_b_autonomy._reload_parser_modules()
        raise
    result = {
        "composite_patch_materialization_kind": (
            "level0_workshop_composite_patch_materialization"
        ),
        "patch_kind": bundle["patch_kind"],
        "step_count": len(bundle["steps"]),
        "materialization_requested": True,
        "materialization_performed": True,
        "verification_passed": True,
        "baseline_matrix_sha256": matrix_sha256,
        "frame_b_source_sha256": source_sha256,
        "materialized_case_results_sha256": materialized_case_results_sha256,
        "materialized_result_summary": (
            _result_summary(materialized_result)
            if materialized_result is not None else None
        ),
        "execution_log": execution_log,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }
    _assert_materialization_shape(result)
    _assert_no_forbidden_claim_phrase(
        result, event_log, "composite_patch_materialization"
    )
    _append_execution_event(
        execution_log, 4, "scan_materialization_result",
        "forbidden phrase scan passed"
    )
    _assert_materialization_shape(result)
    return result
