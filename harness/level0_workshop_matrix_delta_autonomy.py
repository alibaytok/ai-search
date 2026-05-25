"""Matrix expected-field delta autonomy for Level 0B parser review.

This module runs one typed matrix expected-field update as an isolated
candidate variant. It never mutates the source matrix file, parser modules,
route/source/corpus state, or readiness booleans.
"""

import copy
import hashlib
import json
import os
import tempfile

from harness.event_log import EventLog
from harness.level0_workshop_intent_test_matrix_runner import (
    EXPECTED_FIELDS,
    GATING_BOOLEANS,
    WORKSHOP_ITEM_KINDS,
    WORKSHOP_PROMPT_CATEGORIES,
    _ALLOWED_CANDIDATE_SURFACE_SET,
    _ALLOWED_NORMALIZED_INTENT_SET,
    _ALLOWED_REJECTION_SURFACE_SET,
    run_intent_test_matrix,
)
from harness.level0_workshop_parser_quality_loop import (
    ParserVariantCaseSetMismatch,
    _assert_no_forbidden_claim_phrase,
    compare_parser_result_sets,
)


MATRIX_DELTA_PATCH_KINDS = ("matrix_expected_field_update",)

MATRIX_DELTA_DECISIONS = ("accepted", "rejected")

MATRIX_DELTA_DECISION_REASONS = (
    "accepted_strict_improvement",
    "rejected_no_improvement",
    "rejected_regression",
    "rejected_gating_flip",
    "rejected_forbidden_phrase",
    "rejected_invalid_delta",
)

MATRIX_DELTA_EXECUTION_LOG_FIELDS = (
    "event_index",
    "step_index",
    "iteration",
    "stage",
    "status",
    "case_id",
    "patch_kind",
    "detail",
)

MATRIX_DELTA_BUNDLE_FIELDS = (
    "matrix_delta_candidate_kind",
    "patch_kind",
    "case_id",
    "expected_updates",
    "baseline_matrix_sha256",
    "baseline_result_summary",
    "candidate_result_summary",
    "candidate_case_results_sha256",
    "candidate_result",
    "comparison",
    "decision",
    "decision_reasons",
    "execution_log",
    "materialization_authorized",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)

MATRIX_DELTA_MATERIALIZATION_FIELDS = (
    "matrix_delta_materialization_kind",
    "patch_kind",
    "case_id",
    "materialization_requested",
    "materialization_performed",
    "verification_passed",
    "baseline_matrix_sha256",
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

MATRIX_DELTA_NOTE = (
    "bounded matrix delta candidate only; no parser mutation, matrix source "
    "mutation, materialization, selection, measurement, source, route, or "
    "readiness authority"
)

_ALLOWED_KIND_VALUES = frozenset(set(WORKSHOP_ITEM_KINDS) | {"none"})


class MatrixDeltaAutonomyMalformedDelta(Exception):
    """Raised when a matrix delta is outside the bounded schema."""


class MatrixDeltaAutonomyCaseNotFound(Exception):
    """Raised when a matrix delta case_id is absent from the matrix."""


class MatrixDeltaAutonomyForbiddenClaimPhrase(Exception):
    """Raised when emitted bundle text contains a forbidden claim phrase."""


class MatrixDeltaAutonomyMaterializationNotAuthorized(Exception):
    """Raised when materialization is requested without explicit authority."""


class MatrixDeltaAutonomyMaterializationRejected(Exception):
    """Raised when a non-accepted bundle is materialized."""


class MatrixDeltaAutonomyMaterializationVerificationFailed(Exception):
    """Raised when materialized output diverges from the candidate output."""


class MatrixDeltaAutonomyStaleBaseline(Exception):
    """Raised when the source matrix changed after candidate evaluation."""


def _halt(event_log, reason, **payload):
    if event_log is not None and hasattr(event_log, "halt"):
        event_log.halt(reason=reason, **payload)


def _ensure_event_log(event_log):
    if event_log is None:
        return EventLog()
    return event_log


def _append_execution_event(
    execution_log,
    step_index,
    iteration,
    stage,
    status,
    detail,
    case_id=None,
    patch_kind=None,
):
    event = {
        "event_index": len(execution_log) + 1,
        "step_index": step_index,
        "iteration": iteration,
        "stage": stage,
        "status": status,
        "case_id": case_id,
        "patch_kind": patch_kind,
        "detail": detail,
    }
    if tuple(event) != MATRIX_DELTA_EXECUTION_LOG_FIELDS:
        raise MatrixDeltaAutonomyMalformedDelta(
            "matrix delta execution log fields drifted"
        )
    execution_log.append(event)


def _load_matrix(path):
    with open(path, "r", encoding="ascii") as handle:
        return json.load(handle)


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _path_sha256(path):
    with open(path, "rb") as handle:
        return _sha256_bytes(handle.read())


def _stable_json_bytes(value):
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")


def _stable_json_sha256(value):
    return _sha256_bytes(_stable_json_bytes(value))


def _case_results(matrix_result):
    return copy.deepcopy(matrix_result.get("case_results", []))


def _write_temp_matrix(matrix_dict):
    fd, temp_path = tempfile.mkstemp(
        suffix=".intent.matrix.json", prefix="L0WS_VARIANT_"
    )
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        json.dump(matrix_dict, handle, ensure_ascii=True, sort_keys=True)
    return temp_path


def _write_matrix(path, matrix_dict):
    with open(path, "w", encoding="ascii") as handle:
        json.dump(matrix_dict, handle, ensure_ascii=True, sort_keys=True)


def _validate_expected_update_field(field, value):
    if field not in EXPECTED_FIELDS:
        raise MatrixDeltaAutonomyMalformedDelta(
            "Unknown expected update field: {0}".format(field)
        )
    if field == "category" and value not in WORKSHOP_PROMPT_CATEGORIES:
        raise MatrixDeltaAutonomyMalformedDelta("Unknown category value")
    if field == "expected_item_kinds_touched":
        if not isinstance(value, list):
            raise MatrixDeltaAutonomyMalformedDelta(
                "expected_item_kinds_touched must be a list"
            )
        for kind in value:
            if kind not in _ALLOWED_KIND_VALUES:
                raise MatrixDeltaAutonomyMalformedDelta(
                    "Unknown item kind value"
                )
    if field == "ambiguity_observed" and not isinstance(value, bool):
        raise MatrixDeltaAutonomyMalformedDelta(
            "ambiguity_observed must be bool"
        )
    if (
        field == "normalized_intent_observation"
        and value not in _ALLOWED_NORMALIZED_INTENT_SET
    ):
        raise MatrixDeltaAutonomyMalformedDelta(
            "Unknown normalized intent value"
        )
    if (
        field == "candidate_surface_expected"
        and value not in _ALLOWED_CANDIDATE_SURFACE_SET
    ):
        raise MatrixDeltaAutonomyMalformedDelta(
            "Unknown candidate surface value"
        )
    if (
        field == "rejection_surface_expected"
        and value not in _ALLOWED_REJECTION_SURFACE_SET
    ):
        raise MatrixDeltaAutonomyMalformedDelta(
            "Unknown rejection surface value"
        )


def _validate_delta(delta, event_log=None):
    if not isinstance(delta, dict):
        _halt(event_log, "matrix_delta_non_dict_delta")
        raise MatrixDeltaAutonomyMalformedDelta("delta must be a dict")
    if delta.get("patch_kind") not in MATRIX_DELTA_PATCH_KINDS:
        _halt(event_log, "matrix_delta_unknown_patch_kind")
        raise MatrixDeltaAutonomyMalformedDelta("unknown patch_kind")
    if not isinstance(delta.get("case_id"), str) or not delta["case_id"]:
        _halt(event_log, "matrix_delta_invalid_case_id")
        raise MatrixDeltaAutonomyMalformedDelta("case_id must be non-empty str")
    updates = delta.get("expected_updates")
    if not isinstance(updates, dict) or not updates:
        _halt(event_log, "matrix_delta_invalid_expected_updates")
        raise MatrixDeltaAutonomyMalformedDelta(
            "expected_updates must be a non-empty dict"
        )
    for field, value in updates.items():
        _validate_expected_update_field(field, value)


def _apply_delta(matrix_dict, delta, event_log=None):
    candidate_matrix = copy.deepcopy(matrix_dict)
    case_id = delta["case_id"]
    for case in candidate_matrix["cases"]:
        if case["case_id"] == case_id:
            expected = case["expected"]
            for field, value in delta["expected_updates"].items():
                expected[field] = copy.deepcopy(value)
            return candidate_matrix
    _halt(event_log, "matrix_delta_case_not_found", case_id=case_id)
    raise MatrixDeltaAutonomyCaseNotFound(
        "case_id not found in matrix: {0}".format(case_id)
    )


def _result_summary(matrix_result):
    return {
        "matrix_id": matrix_result.get("matrix_id"),
        "case_count": matrix_result.get("case_count"),
        "passed_count": matrix_result.get("passed_count"),
        "failed_count": matrix_result.get("failed_count"),
    }


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
    if not reasons:
        reasons.append("accepted_strict_improvement")
        return "accepted", reasons
    return "rejected", reasons


def _empty_rejected_bundle(
    delta, baseline_matrix_sha256, baseline_result, execution_log, reason
):
    return {
        "matrix_delta_candidate_kind": "level0_workshop_matrix_delta_candidate",
        "patch_kind": delta.get("patch_kind"),
        "case_id": delta.get("case_id"),
        "expected_updates": copy.deepcopy(delta.get("expected_updates")),
        "baseline_matrix_sha256": baseline_matrix_sha256,
        "baseline_result_summary": _result_summary(baseline_result),
        "candidate_result_summary": None,
        "candidate_case_results_sha256": None,
        "candidate_result": None,
        "comparison": None,
        "decision": "rejected",
        "decision_reasons": [reason],
        "execution_log": execution_log,
        "materialization_authorized": False,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }


def _assert_bundle_shape(bundle):
    if tuple(bundle) != MATRIX_DELTA_BUNDLE_FIELDS:
        raise MatrixDeltaAutonomyMalformedDelta(
            "matrix delta bundle fields drifted"
        )
    if bundle["decision"] not in MATRIX_DELTA_DECISIONS:
        raise MatrixDeltaAutonomyMalformedDelta("unknown decision")
    for reason in bundle["decision_reasons"]:
        if reason not in MATRIX_DELTA_DECISION_REASONS:
            raise MatrixDeltaAutonomyMalformedDelta("unknown decision reason")
    if bundle["materialization_authorized"] is not False:
        raise MatrixDeltaAutonomyMalformedDelta(
            "materialization_authorized must be false"
        )


def _assert_materialization_shape(result):
    if tuple(result) != MATRIX_DELTA_MATERIALIZATION_FIELDS:
        raise MatrixDeltaAutonomyMalformedDelta(
            "matrix delta materialization fields drifted"
        )


def run_matrix_delta_candidate(baseline_matrix_path, delta, event_log=None):
    """Run one typed matrix expected-field delta as an isolated candidate."""
    event_log = _ensure_event_log(event_log)
    delta_copy = copy.deepcopy(delta)
    execution_log = []
    _validate_delta(delta_copy, event_log=event_log)
    _append_execution_event(
        execution_log,
        1,
        1,
        "validate_delta",
        "passed",
        "delta shape accepted",
        case_id=delta_copy["case_id"],
        patch_kind=delta_copy["patch_kind"],
    )
    baseline_matrix_sha256 = _path_sha256(baseline_matrix_path)
    baseline_matrix = _load_matrix(baseline_matrix_path)
    baseline_result = run_intent_test_matrix(baseline_matrix_path, event_log)
    _append_execution_event(
        execution_log,
        2,
        1,
        "run_baseline_matrix",
        "passed",
        "baseline matrix run completed",
        case_id=delta_copy["case_id"],
        patch_kind=delta_copy["patch_kind"],
    )
    candidate_matrix = _apply_delta(
        baseline_matrix, delta_copy, event_log=event_log
    )
    _append_execution_event(
        execution_log,
        3,
        1,
        "apply_delta",
        "passed",
        "delta applied to candidate matrix copy",
        case_id=delta_copy["case_id"],
        patch_kind=delta_copy["patch_kind"],
    )
    temp_path = None
    try:
        temp_path = _write_temp_matrix(candidate_matrix)
        _append_execution_event(
            execution_log,
            4,
            1,
            "write_candidate_matrix",
            "passed",
            "candidate matrix temp file written",
            case_id=delta_copy["case_id"],
            patch_kind=delta_copy["patch_kind"],
        )
        candidate_result = run_intent_test_matrix(temp_path, event_log)
        _append_execution_event(
            execution_log,
            5,
            1,
            "run_candidate_matrix",
            "passed",
            "candidate matrix run completed",
            case_id=delta_copy["case_id"],
            patch_kind=delta_copy["patch_kind"],
        )
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        _append_execution_event(
            execution_log,
            6,
            1,
            "delete_candidate_matrix",
            "passed",
            "candidate matrix temp file deleted",
            case_id=delta_copy["case_id"],
            patch_kind=delta_copy["patch_kind"],
        )
    try:
        comparison = compare_parser_result_sets(
            baseline_result, candidate_result, event_log=event_log
        )
    except ParserVariantCaseSetMismatch:
        bundle = _empty_rejected_bundle(
            delta_copy,
            baseline_matrix_sha256,
            baseline_result,
            execution_log,
            "rejected_invalid_delta",
        )
        _assert_bundle_shape(bundle)
        return bundle
    _append_execution_event(
        execution_log,
        7,
        1,
        "compare",
        "passed",
        "baseline and candidate results compared",
        case_id=delta_copy["case_id"],
        patch_kind=delta_copy["patch_kind"],
    )
    decision, reasons = _decide(baseline_result, candidate_result, comparison)
    _append_execution_event(
        execution_log,
        8,
        1,
        "decide",
        "passed",
        "candidate decision computed",
        case_id=delta_copy["case_id"],
        patch_kind=delta_copy["patch_kind"],
    )
    bundle = {
        "matrix_delta_candidate_kind": "level0_workshop_matrix_delta_candidate",
        "patch_kind": delta_copy["patch_kind"],
        "case_id": delta_copy["case_id"],
        "expected_updates": copy.deepcopy(delta_copy["expected_updates"]),
        "baseline_matrix_sha256": baseline_matrix_sha256,
        "baseline_result_summary": _result_summary(baseline_result),
        "candidate_result_summary": _result_summary(candidate_result),
        "candidate_case_results_sha256": _stable_json_sha256(
            _case_results(candidate_result)
        ),
        "candidate_result": candidate_result,
        "comparison": comparison,
        "decision": decision,
        "decision_reasons": reasons,
        "execution_log": execution_log,
        "materialization_authorized": False,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }
    _assert_bundle_shape(bundle)
    try:
        _assert_no_forbidden_claim_phrase(
            bundle, event_log, "matrix_delta_candidate_bundle"
        )
    except Exception as exc:
        raise MatrixDeltaAutonomyForbiddenClaimPhrase(str(exc))
    _append_execution_event(
        execution_log,
        9,
        1,
        "scan_bundle",
        "passed",
        "forbidden claim phrase scan passed",
        case_id=delta_copy["case_id"],
        patch_kind=delta_copy["patch_kind"],
    )
    _assert_bundle_shape(bundle)
    return bundle


def _bundle_delta(bundle):
    return {
        "patch_kind": bundle.get("patch_kind"),
        "case_id": bundle.get("case_id"),
        "expected_updates": copy.deepcopy(bundle.get("expected_updates")),
    }


def _restore_bytes(path, original_bytes):
    with open(path, "wb") as handle:
        handle.write(original_bytes)


def materialize_accepted_matrix_delta(
    bundle, baseline_matrix_path, materialization_authorized=False, event_log=None
):
    """Materialize one accepted matrix delta after explicit authorization."""
    event_log = _ensure_event_log(event_log)
    _assert_bundle_shape(bundle)
    execution_log = []
    _append_execution_event(
        execution_log,
        1,
        1,
        "validate_materialization_request",
        "passed",
        "materialization request shape accepted",
        case_id=bundle["case_id"],
        patch_kind=bundle["patch_kind"],
    )
    if materialization_authorized is not True:
        _halt(event_log, "matrix_delta_materialization_not_authorized")
        raise MatrixDeltaAutonomyMaterializationNotAuthorized(
            "materialization_authorized must be True"
        )
    if bundle["decision"] != "accepted":
        _halt(event_log, "matrix_delta_materialization_rejected_bundle")
        raise MatrixDeltaAutonomyMaterializationRejected(
            "only accepted bundles may be materialized"
        )
    delta = _bundle_delta(bundle)
    _validate_delta(delta, event_log=event_log)
    with open(baseline_matrix_path, "rb") as handle:
        original_bytes = handle.read()
    original_sha256 = _sha256_bytes(original_bytes)
    if original_sha256 != bundle["baseline_matrix_sha256"]:
        _halt(event_log, "matrix_delta_materialization_stale_baseline")
        raise MatrixDeltaAutonomyStaleBaseline(
            "baseline matrix changed after candidate evaluation"
        )
    matrix = _load_matrix(baseline_matrix_path)
    materialized_matrix = _apply_delta(matrix, delta, event_log=event_log)
    _append_execution_event(
        execution_log,
        2,
        1,
        "apply_materialized_delta",
        "passed",
        "delta applied to matrix copy for materialization",
        case_id=bundle["case_id"],
        patch_kind=bundle["patch_kind"],
    )
    rollback_done = False
    try:
        _write_matrix(baseline_matrix_path, materialized_matrix)
        _append_execution_event(
            execution_log,
            3,
            1,
            "write_materialized_matrix",
            "passed",
            "matrix file updated with accepted delta",
            case_id=bundle["case_id"],
            patch_kind=bundle["patch_kind"],
        )
        materialized_result = run_intent_test_matrix(
            baseline_matrix_path, event_log
        )
        _append_execution_event(
            execution_log,
            4,
            1,
            "run_materialized_matrix",
            "passed",
            "materialized matrix run completed",
            case_id=bundle["case_id"],
            patch_kind=bundle["patch_kind"],
        )
        materialized_case_results_sha256 = _stable_json_sha256(
            _case_results(materialized_result)
        )
        if (
            materialized_case_results_sha256
            != bundle["candidate_case_results_sha256"]
            or _case_results(materialized_result)
            != _case_results(bundle["candidate_result"])
        ):
            _restore_bytes(baseline_matrix_path, original_bytes)
            rollback_done = True
            _append_execution_event(
                execution_log,
                5,
                1,
                "rollback_materialized_matrix",
                "passed",
                "materialized result mismatch; original matrix restored",
                case_id=bundle["case_id"],
                patch_kind=bundle["patch_kind"],
            )
            raise MatrixDeltaAutonomyMaterializationVerificationFailed(
                "materialized case results diverged from candidate case results"
            )
    except Exception:
        if not rollback_done and os.path.exists(baseline_matrix_path):
            current_bytes = None
            with open(baseline_matrix_path, "rb") as handle:
                current_bytes = handle.read()
            if current_bytes != original_bytes:
                _restore_bytes(baseline_matrix_path, original_bytes)
        raise
    result = {
        "matrix_delta_materialization_kind": (
            "level0_workshop_matrix_delta_materialization"
        ),
        "patch_kind": bundle["patch_kind"],
        "case_id": bundle["case_id"],
        "materialization_requested": True,
        "materialization_performed": True,
        "verification_passed": True,
        "baseline_matrix_sha256": original_sha256,
        "materialized_case_results_sha256": materialized_case_results_sha256,
        "materialized_result_summary": _result_summary(materialized_result),
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
        result, event_log, "matrix_delta_materialization"
    )
    _append_execution_event(
        execution_log,
        5,
        1,
        "scan_materialization_result",
        "passed",
        "forbidden claim phrase scan passed",
        case_id=bundle["case_id"],
        patch_kind=bundle["patch_kind"],
    )
    _assert_materialization_shape(result)
    return result
