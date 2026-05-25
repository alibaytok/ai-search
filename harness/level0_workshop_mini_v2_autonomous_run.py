"""Mini-V2 autonomous-loop proposal report.

This module runs the existing Level 0 workshop runner, feedback planner,
and candidate case-review reporter against the admitted Mini-V2 matrix only.
It emits a deterministic, proposal-only report. It does not read holdout,
write parser core, write matrix files, materialize any candidate, admit
corpus entries, or authorize downstream action.
"""

import copy
import hashlib
import json
import os

from harness.event_log import EventLog
from harness.level0_workshop_intent_test_matrix_runner import (
    GATING_BOOLEANS,
    run_intent_test_matrix,
)
from harness.level0_workshop_parser_quality_loop import (
    build_candidate_review_summary,
    build_feedback_report,
    build_upgrade_candidates,
)


MINI_V2_MATRIX_PATH = os.path.join(
    "harness",
    "intent_test_matrices",
    "L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json",
)

PARSER_CORE_PATHS = (
    os.path.join("harness", "level0_workshop_signal_evidence.py"),
    os.path.join("harness", "level0_workshop_canonical_intent_frame.py"),
)

MINI_V2_AUTONOMOUS_RUN_REPORT_KIND = (
    "level0_workshop_mini_v2_autonomous_run_report"
)

MINI_V2_AUTONOMOUS_RUN_REPORT_FIELDS = (
    "mini_v2_autonomous_run_report_kind",
    "matrix_path",
    "matrix_sha256",
    "parser_core_sha256",
    "parser_core_unchanged",
    "matrix_result_summary",
    "case_results",
    "feedback_report",
    "planner_result",
    "candidate_review_summary",
    "proposal_bundles",
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
    "run_note",
)

PROPOSAL_BUNDLE_FIELDS = (
    "proposal_bundle_kind",
    "candidate_id",
    "candidate",
    "case_review",
    "materialization_authorized",
    "human_review_gate",
    "variant_execution_authorized",
    "variant_execution_performed",
)

RUN_NOTE = (
    "Mini-V2 admitted-matrix proposal report only; holdout is not read; "
    "no parser-core write, matrix write, materialization, selection, "
    "measurement, source qualification, corpus admission, route creation, "
    "or downstream action is authorized"
)


class MiniV2AutonomousRunReportShapeDrift(Exception):
    """Raised when the report fields drift from the bounded tuple."""


def _sha256_path(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def _matrix_result_summary(matrix_result):
    return {
        "matrix_id": matrix_result["matrix_id"],
        "case_count": matrix_result["case_count"],
        "passed_count": matrix_result["passed_count"],
        "failed_count": matrix_result["failed_count"],
        "per_failure_class_counts": copy.deepcopy(
            matrix_result["per_failure_class_counts"]
        ),
        "per_tag_counts": copy.deepcopy(matrix_result["per_tag_counts"]),
    }


def _parser_core_hashes():
    return {
        path.replace(os.sep, "/"): _sha256_path(path)
        for path in PARSER_CORE_PATHS
    }


def _proposal_bundles(planner_result, candidate_review_summary):
    reviews_by_id = {
        review["candidate_id"]: review
        for review in candidate_review_summary["candidate_case_reviews"]
    }
    bundles = []
    for candidate in planner_result["upgrade_candidates"]:
        bundle = {
            "proposal_bundle_kind": "level0_workshop_mini_v2_proposal_bundle",
            "candidate_id": candidate["candidate_id"],
            "candidate": copy.deepcopy(candidate),
            "case_review": copy.deepcopy(reviews_by_id[candidate["candidate_id"]]),
            "materialization_authorized": False,
            "human_review_gate": False,
            "variant_execution_authorized": False,
            "variant_execution_performed": False,
        }
        if tuple(bundle) != PROPOSAL_BUNDLE_FIELDS:
            raise MiniV2AutonomousRunReportShapeDrift(
                "proposal bundle fields drifted"
            )
        bundles.append(bundle)
    return bundles


def build_mini_v2_autonomous_run_report(matrix_path=MINI_V2_MATRIX_PATH):
    """Build the proposal-only Mini-V2 autonomous-run report."""
    before_core = _parser_core_hashes()
    matrix_result = run_intent_test_matrix(matrix_path, EventLog())
    feedback_report = build_feedback_report(matrix_result)
    planner_result = build_upgrade_candidates(feedback_report)
    candidate_review_summary = build_candidate_review_summary(
        planner_result, matrix_result
    )
    after_core = _parser_core_hashes()

    report = {
        "mini_v2_autonomous_run_report_kind": (
            MINI_V2_AUTONOMOUS_RUN_REPORT_KIND
        ),
        "matrix_path": matrix_path.replace(os.sep, "/"),
        "matrix_sha256": _sha256_path(matrix_path),
        "parser_core_sha256": before_core,
        "parser_core_unchanged": before_core == after_core,
        "matrix_result_summary": _matrix_result_summary(matrix_result),
        "case_results": copy.deepcopy(matrix_result["case_results"]),
        "feedback_report": feedback_report,
        "planner_result": planner_result,
        "candidate_review_summary": candidate_review_summary,
        "proposal_bundles": _proposal_bundles(
            planner_result, candidate_review_summary
        ),
        "holdout_matrix_read": False,
        "materialization_authorized": False,
        "human_review_gate": False,
        "variant_execution_authorized": False,
        "variant_execution_performed": False,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
        "expected_fields_generated": False,
        "parser_core_write_performed": False,
        "matrix_write_performed": False,
        "run_note": RUN_NOTE,
    }
    if tuple(report) != MINI_V2_AUTONOMOUS_RUN_REPORT_FIELDS:
        raise MiniV2AutonomousRunReportShapeDrift("report fields drifted")
    return report


def write_mini_v2_autonomous_run_report(output_path):
    """Write the deterministic report artifact for review."""
    report = build_mini_v2_autonomous_run_report()
    parent = os.path.dirname(output_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(output_path, "w", encoding="ascii") as handle:
        json.dump(report, handle, ensure_ascii=True, indent=2)
        handle.write("\n")
    return report
