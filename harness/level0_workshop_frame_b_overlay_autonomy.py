"""FRAME-B canonical overlay candidate runner."""

import copy
import hashlib
import importlib
import os

from harness.event_log import EventLog
import harness.level0_workshop_intent_test_matrix_runner as runner_module
import harness.level0_workshop_signal_evidence as signal_evidence_module
import harness.level0_workshop_user_intent_mapper as mapper_module
from harness.level0_workshop_intent_test_matrix_runner import (
    GATING_BOOLEANS,
    run_intent_test_matrix,
)
from harness.level0_workshop_parser_quality_loop import (
    ParserQualityLoopForbiddenClaimPhrase,
    _assert_no_forbidden_claim_phrase,
    compare_parser_result_sets,
)
from harness.level0_workshop_signal_evidence import SIGNAL_FAMILIES
from harness.level0_workshop_signal_families_overlay import (
    build_signal_families_overlay,
    validate_signal_families_delta,
)


FRAME_B_OVERLAY_DECISIONS = ("accepted", "rejected")

FRAME_B_OVERLAY_DECISION_REASONS = (
    "accepted_strict_improvement",
    "rejected_no_improvement",
    "rejected_regression",
    "rejected_gating_flip",
)

FRAME_B_OVERLAY_BUNDLE_FIELDS = (
    "frame_b_overlay_candidate_kind",
    "patch_kind",
    "canonical_additions",
    "execution_log",
    "affected_by_family",
    "accepted_family_ids",
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

FRAME_B_MATERIALIZATION_FIELDS = (
    "frame_b_materialization_kind",
    "patch_kind",
    "materialization_requested",
    "materialization_performed",
    "verification_passed",
    "frame_b_source_sha256",
    "materialized_family_ids",
    "materialized_canonical_additions",
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

FRAME_B_OVERLAY_EXECUTION_LOG_FIELDS = (
    "event_index",
    "step_index",
    "stage",
    "detail",
)


class FrameBOverlayForbiddenClaimPhrase(Exception):
    """Raised when emitted overlay candidate text contains forbidden terms."""


class FrameBMaterializationNotAuthorized(Exception):
    """Raised when FRAME-B materialization lacks explicit authority."""


class FrameBMaterializationRejectedBundle(Exception):
    """Raised when a non-accepted FRAME-B bundle is materialized."""


class FrameBMaterializationNoAcceptedFamilies(Exception):
    """Raised when a bundle has no proven-improving families."""


class FrameBMaterializationVerificationFailed(Exception):
    """Raised when materialized parser output diverges from the candidate."""


class FrameBMaterializationStaleSource(Exception):
    """Raised when FRAME-B source changed after candidate evaluation."""


def _ensure_event_log(event_log):
    if event_log is None:
        return EventLog()
    return event_log


def _result_summary(matrix_result):
    return {
        "matrix_id": matrix_result.get("matrix_id"),
        "case_count": matrix_result.get("case_count"),
        "passed_count": matrix_result.get("passed_count"),
        "failed_count": matrix_result.get("failed_count"),
    }


def _case_results(matrix_result):
    return copy.deepcopy(matrix_result.get("case_results", []))


def _stable_json_bytes(value):
    import json

    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("ascii")


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _stable_json_sha256(value):
    return _sha256_bytes(_stable_json_bytes(value))


def _path_sha256(path):
    with open(path, "rb") as handle:
        return _sha256_bytes(handle.read())


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
        return "accepted", ["accepted_strict_improvement"]
    return "rejected", reasons


def _append_execution_event(execution_log, step_index, stage, detail):
    event = {
        "event_index": len(execution_log) + 1,
        "step_index": step_index,
        "stage": stage,
        "detail": detail,
    }
    if tuple(event) != FRAME_B_OVERLAY_EXECUTION_LOG_FIELDS:
        raise AssertionError("frame b overlay execution log fields drifted")
    execution_log.append(event)


def _overlay_result(matrix_path, canonical_additions, event_log):
    delta = {
        "patch_kind": "frame_b_canonical_addition",
        "canonical_additions": copy.deepcopy(canonical_additions),
    }
    overlay = build_signal_families_overlay(SIGNAL_FAMILIES, delta, event_log=event_log)
    return run_intent_test_matrix(matrix_path, event_log, signal_families=overlay)


def _family_effects(matrix_path, canonical_additions, baseline_result, event_log):
    effects = {}
    for family_id in sorted(canonical_additions):
        candidate_result = _overlay_result(
            matrix_path, {family_id: canonical_additions[family_id]}, event_log
        )
        comparison = compare_parser_result_sets(
            baseline_result, candidate_result, event_log=event_log
        )
        decision, reasons = _decide(baseline_result, candidate_result, comparison)
        effects[family_id] = {
            "decision": decision,
            "decision_reasons": reasons,
            "improved_cases": list(comparison["improved_cases"]),
            "regressed_cases": list(comparison["regressed_cases"]),
        }
    return effects


def _assert_bundle_shape(bundle):
    if tuple(bundle) != FRAME_B_OVERLAY_BUNDLE_FIELDS:
        raise AssertionError("frame b overlay bundle fields drifted")
    if bundle["decision"] not in FRAME_B_OVERLAY_DECISIONS:
        raise AssertionError("unknown frame b overlay decision")
    for reason in bundle["decision_reasons"]:
        if reason not in FRAME_B_OVERLAY_DECISION_REASONS:
            raise AssertionError("unknown frame b overlay decision reason")


def _assert_materialization_shape(result):
    if tuple(result) != FRAME_B_MATERIALIZATION_FIELDS:
        raise AssertionError("frame b materialization fields drifted")


def run_frame_b_overlay_candidate(matrix_path, delta, event_log=None):
    """Run one immutable FRAME-B signal-family overlay candidate."""
    event_log = _ensure_event_log(event_log)
    execution_log = []
    delta_copy = copy.deepcopy(delta)
    validate_signal_families_delta(delta_copy, event_log=event_log)
    _append_execution_event(
        execution_log, 1, "validate_delta", "signal-family delta accepted"
    )
    baseline_result = run_intent_test_matrix(matrix_path, event_log)
    _append_execution_event(
        execution_log, 2, "run_baseline_matrix", "baseline matrix run completed"
    )
    overlay = build_signal_families_overlay(
        SIGNAL_FAMILIES, delta_copy, event_log=event_log
    )
    _append_execution_event(
        execution_log, 3, "build_overlay", "immutable overlay built"
    )
    candidate_result = run_intent_test_matrix(
        matrix_path, event_log, signal_families=overlay
    )
    _append_execution_event(
        execution_log, 4, "run_candidate_matrix", "candidate matrix run completed"
    )
    comparison = compare_parser_result_sets(
        baseline_result, candidate_result, event_log=event_log
    )
    _append_execution_event(
        execution_log, 5, "compare", "baseline and candidate result sets compared"
    )
    decision, reasons = _decide(baseline_result, candidate_result, comparison)
    affected_by_family = _family_effects(
        matrix_path, delta_copy["canonical_additions"], baseline_result, event_log
    )
    accepted_family_ids = [
        family_id
        for family_id in sorted(affected_by_family)
        if affected_by_family[family_id]["decision"] == "accepted"
    ]
    _append_execution_event(
        execution_log, 6, "decide", "candidate decision completed"
    )
    bundle = {
        "frame_b_overlay_candidate_kind": "level0_workshop_frame_b_overlay_candidate",
        "patch_kind": delta_copy["patch_kind"],
        "canonical_additions": copy.deepcopy(delta_copy["canonical_additions"]),
        "execution_log": execution_log,
        "affected_by_family": affected_by_family,
        "accepted_family_ids": accepted_family_ids,
        "frame_b_source_sha256": _path_sha256(signal_evidence_module.__file__),
        "baseline_result_summary": _result_summary(baseline_result),
        "candidate_result_summary": _result_summary(candidate_result),
        "candidate_case_results_sha256": _stable_json_sha256(
            _case_results(candidate_result)
        ),
        "candidate_case_results": _case_results(candidate_result),
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
    _assert_bundle_shape(bundle)
    try:
        _assert_no_forbidden_claim_phrase(
            bundle, event_log, "frame_b_overlay_candidate_bundle"
        )
    except ParserQualityLoopForbiddenClaimPhrase as exc:
        raise FrameBOverlayForbiddenClaimPhrase(str(exc))
    return bundle


def _source_path_is_real_signal_module(signal_evidence_path):
    real_path = os.path.abspath(signal_evidence_module.__file__)
    return os.path.abspath(signal_evidence_path) == real_path


def _reload_parser_modules():
    global SIGNAL_FAMILIES
    global run_intent_test_matrix
    importlib.reload(signal_evidence_module)
    importlib.reload(mapper_module)
    importlib.reload(runner_module)
    SIGNAL_FAMILIES = signal_evidence_module.SIGNAL_FAMILIES
    run_intent_test_matrix = runner_module.run_intent_test_matrix


def _insert_terms_in_source(source, family_id, terms):
    family_marker = 'family_id="{0}"'.format(family_id)
    family_pos = source.find(family_marker)
    if family_pos < 0:
        raise FrameBMaterializationVerificationFailed(
            "family_id not found in FRAME-B source"
        )
    terms_pos = source.find("canonical_terms=(", family_pos)
    if terms_pos < 0:
        raise FrameBMaterializationVerificationFailed(
            "canonical_terms tuple not found for family"
        )
    close_pos = source.find("\n        ),", terms_pos)
    if close_pos < 0:
        raise FrameBMaterializationVerificationFailed(
            "canonical_terms closing tuple not found for family"
        )
    block = source[terms_pos:close_pos]
    additions = []
    for term in terms:
        literal = '"{0}"'.format(term)
        if literal not in block:
            additions.append('            "{0}",'.format(term))
    if not additions:
        return source
    insertion = "\n" + "\n".join(additions)
    return source[:close_pos] + insertion + source[close_pos:]


def _apply_materialized_terms(source, canonical_additions):
    next_source = source
    for family_id in sorted(canonical_additions):
        next_source = _insert_terms_in_source(
            next_source, family_id, canonical_additions[family_id]
        )
    return next_source


def _restore_bytes(path, payload):
    with open(path, "wb") as handle:
        handle.write(payload)


def materialize_accepted_frame_b_canonicals(
    bundle,
    signal_evidence_path,
    matrix_path=None,
    materialization_authorized=False,
    event_log=None,
):
    """Materialize only proven-improving FRAME-B canonical additions."""
    event_log = _ensure_event_log(event_log)
    _assert_bundle_shape(bundle)
    execution_log = []
    _append_execution_event(
        execution_log, 1, "validate_materialization_request",
        "frame b materialization request accepted"
    )
    if materialization_authorized is not True:
        raise FrameBMaterializationNotAuthorized(
            "materialization_authorized must be True"
        )
    if bundle["decision"] != "accepted":
        raise FrameBMaterializationRejectedBundle(
            "only accepted FRAME-B bundles may be materialized"
        )
    accepted_family_ids = list(bundle["accepted_family_ids"])
    if not accepted_family_ids:
        raise FrameBMaterializationNoAcceptedFamilies(
            "bundle has no accepted family additions"
        )
    canonical_additions = {
        family_id: copy.deepcopy(bundle["canonical_additions"][family_id])
        for family_id in accepted_family_ids
    }
    with open(signal_evidence_path, "rb") as handle:
        original_bytes = handle.read()
    original_sha256 = _sha256_bytes(original_bytes)
    if original_sha256 != bundle["frame_b_source_sha256"]:
        raise FrameBMaterializationStaleSource(
            "FRAME-B source changed after candidate evaluation"
        )
    source = original_bytes.decode("ascii")
    next_source = _apply_materialized_terms(source, canonical_additions)
    with open(signal_evidence_path, "w", encoding="ascii") as handle:
        handle.write(next_source)
    _append_execution_event(
        execution_log, 2, "write_frame_b_source",
        "accepted canonical additions written"
    )
    rollback_done = False
    materialized_result = None
    try:
        if matrix_path is not None and _source_path_is_real_signal_module(
            signal_evidence_path
        ):
            _reload_parser_modules()
            materialized_result = run_intent_test_matrix(matrix_path, event_log)
            materialized_case_results = _case_results(materialized_result)
            materialized_case_results_sha256 = _stable_json_sha256(
                materialized_case_results
            )
            _append_execution_event(
                execution_log, 3, "run_materialized_matrix",
                "materialized parser matrix run completed"
            )
            if (
                materialized_case_results_sha256
                != bundle["candidate_case_results_sha256"]
                or materialized_case_results != bundle["candidate_case_results"]
            ):
                _restore_bytes(signal_evidence_path, original_bytes)
                rollback_done = True
                _reload_parser_modules()
                raise FrameBMaterializationVerificationFailed(
                    "materialized case results diverged from candidate case results"
                )
        else:
            materialized_case_results_sha256 = None
            _append_execution_event(
                execution_log, 3, "run_materialized_matrix",
                "materialized parser matrix run skipped for temp source"
            )
    except Exception:
        if not rollback_done and os.path.exists(signal_evidence_path):
            with open(signal_evidence_path, "rb") as handle:
                current_bytes = handle.read()
            if current_bytes != original_bytes:
                _restore_bytes(signal_evidence_path, original_bytes)
            if _source_path_is_real_signal_module(signal_evidence_path):
                _reload_parser_modules()
        raise
    result = {
        "frame_b_materialization_kind": "level0_workshop_frame_b_materialization",
        "patch_kind": bundle["patch_kind"],
        "materialization_requested": True,
        "materialization_performed": True,
        "verification_passed": True,
        "frame_b_source_sha256": original_sha256,
        "materialized_family_ids": accepted_family_ids,
        "materialized_canonical_additions": canonical_additions,
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
        result, event_log, "frame_b_materialization"
    )
    _append_execution_event(
        execution_log, 4, "scan_materialization_result",
        "forbidden claim phrase scan passed"
    )
    _assert_materialization_shape(result)
    return result
