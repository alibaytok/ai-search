"""Parser quality-loop contracts for Level 0B workshop intent.

This module turns matrix runner case results into bounded feedback rows and
compares two parser result sets. It does not run the parser, mutate parser
code, correct vocabulary, call a provider, or authorize benchmark / route /
source behavior. It is a deterministic planning helper for review evidence.
"""

from harness.level0_workshop_intent_test_matrix_runner import (
    FAILURE_CLASSES,
    FORBIDDEN_CLAIM_PHRASES,
)


UPGRADE_PLAN_FIELDS = (
    "case_id",
    "failure_class",
    "likely_layer",
    "observed_fields",
    "expected_fields",
    "affected_tags",
    "suggested_upgrade_type",
    "suggested_next_packet_type",
    "patch_surface",
    "safety_tier",
    "risk_note",
    "precedent_dc_reference",
)


SUGGESTED_UPGRADE_TYPES = (
    "add_frame_b_canonical",
    "add_frame_b_alias",
    "add_frame_b_inflection",
    "add_frame_b_negation",
    "add_frame_c_shape_rule",
    "add_frame_c_category_rule",
    "add_ambiguity_clarification",
    "add_clarification_prompt_surface",
    "update_expected_case",
    "add_tolerated_variant",
    "split_case",
    "mark_case_out_of_scope",
    "unknown",
)


SAFETY_TIERS = ("proposal_only", "forbidden")


CANDIDATE_SAFETY_TIERS = (
    "proposal_only",
    "requires_reserved_layer",
    "forbidden",
)


CANDIDATE_INTENTS = (
    "parser_improvement",
    "matrix_reconciliation",
    "reserved_layer_design_proposal",
    "requires_triage",
)


EXPECTATION_DRIFT_RISKS = ("low", "medium", "high")


CASE_REVIEW_LABELS = (
    "likely_matrix_expectation_drift",
    "likely_negation_gap",
    "likely_synthesis_gap",
    "needs_human_review",
)


PLANNER_EXECUTION_LOG_FIELDS = (
    "event_index",
    "step_index",
    "iteration",
    "stage",
    "status",
    "case_id",
    "candidate_id",
    "failure_class",
    "suggested_upgrade_type",
    "detail",
)


AMBIGUITY_DIRECTIONS = ("underreport", "overreport", "none")


LIKELY_LAYERS = (
    "FRAME-A",
    "FRAME-B",
    "FRAME-C",
    "FRAME-D",
    "MATRIX",
    "OUT_OF_SCOPE",
    "CLARIFICATION",
    "UNKNOWN",
)


SUGGESTED_NEXT_PACKET_TYPES = (
    "FRAME-A-HARDEN",
    "FRAME-B-COVERAGE",
    "FRAME-C-HARDEN",
    "FRAME-D-COMPAT",
    "CLARIFICATION-DESIGN",
    "NO-ROUTE-HARDEN",
    "MATRIX-RECONCILE",
    "TRIAGE",
)


REPORT_NOTE = (
    "bounded parser feedback only; no selection, measurement, source, "
    "route, or readiness authority"
)


PLANNER_REPORT_NOTE = (
    "bounded upgrade grouping only; no selection, measurement, source, "
    "route, or readiness authority"
)


CANDIDATE_REVIEW_NOTE = (
    "bounded candidate case review only; no parser mutation, matrix mutation, "
    "selection, measurement, source, route, or readiness authority"
)


UPGRADE_CANDIDATE_FIELDS = (
    "candidate_id",
    "failure_class",
    "suggested_upgrade_type",
    "suggested_next_packet_type",
    "candidate_intent",
    "likely_layer",
    "safety_tier",
    "expectation_drift_risk",
    "affected_case_ids",
    "affected_tags",
    "affected_count",
    "patch_plan_skeleton",
    "required_tests",
    "risk_notes",
    "precedent_dc_reference",
)


CANDIDATE_CASE_REVIEW_FIELDS = (
    "case_id",
    "review_label",
    "expected_category",
    "observed_category",
    "expected_kinds",
    "observed_kinds",
    "expected_ambiguity",
    "observed_ambiguity",
    "differing_fields",
    "tags",
)


CANDIDATE_CASE_REVIEW_REPORT_FIELDS = (
    "candidate_case_review_kind",
    "candidate_id",
    "failure_class",
    "affected_count",
    "case_reviews",
    "per_review_label_counts",
    "review_note",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)


CANDIDATE_REVIEW_SUMMARY_FIELDS = (
    "candidate_review_summary_kind",
    "matrix_id",
    "candidate_count",
    "candidate_case_reviews",
    "overall_review_label_counts",
    "review_note",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)


PATCH_PLAN_TEMPLATES = {
    ("FRAME-B", "add_frame_b_canonical"): (
        "Add a bounded FRAME-B canonical or alias entry under the existing "
        "family budget, with collision tests."
    ),
    ("FRAME-C", "add_frame_c_shape_rule"): (
        "Add a bounded FRAME-C shape-touch synthesis rule, with negative "
        "tests for adjacent prompts."
    ),
    ("FRAME-C", "add_ambiguity_clarification"): (
        "Design a reserved clarification surface before changing parser "
        "behavior for ambiguous cases."
    ),
    ("MATRIX", "update_expected_case"): (
        "Review and update the matrix expected fields if the parser output "
        "matches the intended contract."
    ),
    ("UNKNOWN", "unknown"): (
        "Escalate for manual triage; no bounded patch surface is inferred."
    ),
}


REQUIRED_TESTS_BY_NEXT_PACKET = {
    "FRAME-A-HARDEN": (
        "frame_a_normalization_contract_test",
        "frame_a_downstream_regression_test",
    ),
    "FRAME-B-COVERAGE": (
        "frame_b_canonical_match_test",
        "frame_b_alias_collision_test",
    ),
    "FRAME-C-HARDEN": (
        "frame_c_shape_rule_positive_test",
        "frame_c_shape_rule_negative_test",
    ),
    "FRAME-D-COMPAT": (
        "frame_d_translation_contract_test",
        "frame_d_legacy_surface_test",
    ),
    "CLARIFICATION-DESIGN": (
        "clarification_candidate_surface_contract_test",
        "ambiguity_direction_contract_test",
    ),
    "NO-ROUTE-HARDEN": (
        "no_route_positive_test",
        "out_of_scope_negative_test",
    ),
    "MATRIX-RECONCILE": (
        "matrix_expected_field_review_test",
        "matrix_runner_clean_pass_test",
    ),
    "TRIAGE": ("manual_triage_contract_test",),
}


RISK_NOTES_BY_LAYER_AND_TYPE = {
    ("FRAME-B", "add_frame_b_canonical"): (
        "Canonical additions can create near-match collisions; keep the "
        "change bounded and test adjacent prompts."
    ),
    ("FRAME-C", "add_frame_c_shape_rule"): (
        "Shape rules can over-fire across prompt families; require negative "
        "coverage around the affected tags."
    ),
    ("FRAME-C", "add_ambiguity_clarification"): (
        "Clarification is a reserved surface; do not implement product "
        "behavior from this group alone."
    ),
    ("MATRIX", "update_expected_case"): (
        "Matrix drift should be reconciled before treating the case as a "
        "parser defect."
    ),
    ("UNKNOWN", "unknown"): (
        "No bounded layer was inferred; keep this in manual triage."
    ),
}


_PLAN_BY_FAILURE_CLASS = {
    "frame_a_normalization_gap": {
        "likely_layer": "FRAME-A",
        "suggested_upgrade_type": "unknown",
        "suggested_next_packet_type": "FRAME-A-HARDEN",
        "patch_surface": "normalized prompt view normalization contract",
        "risk_note": "Normalization changes can perturb every downstream signal.",
        "precedent_dc_reference": "DC-020",
    },
    "frame_b_canonical_set_gap": {
        "likely_layer": "FRAME-B",
        "suggested_upgrade_type": "add_frame_b_canonical",
        "suggested_next_packet_type": "FRAME-B-COVERAGE",
        "patch_surface": "SIGNAL_FAMILIES canonical_terms / alias surface",
        "risk_note": "Bound canonical additions and rerun matrix for collisions.",
        "precedent_dc_reference": "DC-078 / DC-080",
    },
    "frame_b_inflection_gap": {
        "likely_layer": "FRAME-B",
        "suggested_upgrade_type": "add_frame_b_inflection",
        "suggested_next_packet_type": "FRAME-B-COVERAGE",
        "patch_surface": "SIGNAL_FAMILIES bounded inflection surface",
        "risk_note": "Prefer explicit terms over matching-policy widening.",
        "precedent_dc_reference": "DC-079",
    },
    "frame_b_negation_gap": {
        "likely_layer": "FRAME-B",
        "suggested_upgrade_type": "add_frame_b_negation",
        "suggested_next_packet_type": "FRAME-B-COVERAGE",
        "patch_surface": "negation signal family",
        "risk_note": "Negation can invert otherwise clean intent evidence.",
        "precedent_dc_reference": "DC-076",
    },
    "frame_c_synthesis_rule_gap": {
        "likely_layer": "FRAME-C",
        "suggested_upgrade_type": "add_frame_c_shape_rule",
        "suggested_next_packet_type": "FRAME-C-HARDEN",
        "patch_surface": "shape touch plan synthesis rule",
        "risk_note": "Guard with negative tests so the rule stays narrow.",
        "precedent_dc_reference": "DC-081",
    },
    "frame_c_category_selector_gap": {
        "likely_layer": "FRAME-C",
        "suggested_upgrade_type": "add_frame_c_category_rule",
        "suggested_next_packet_type": "FRAME-C-HARDEN",
        "patch_surface": "category selection rule",
        "risk_note": "Category selector changes can rebalance matrix groups.",
        "precedent_dc_reference": "DC-081",
    },
    "frame_c_ambiguity_misreport": {
        "likely_layer": "FRAME-C",
        "suggested_upgrade_type": "add_ambiguity_clarification",
        "suggested_next_packet_type": "CLARIFICATION-DESIGN",
        "patch_surface": "ambiguity reporting / clarification surface",
        "risk_note": "Do not force a single category when evidence is tied.",
        "precedent_dc_reference": "DC-075 / DC-081",
    },
    "ambiguity_clarification_gap": {
        "likely_layer": "CLARIFICATION",
        "suggested_upgrade_type": "add_clarification_prompt_surface",
        "suggested_next_packet_type": "CLARIFICATION-DESIGN",
        "patch_surface": "future did-you-mean surface",
        "risk_note": "Clarification UI is a separate product surface.",
        "precedent_dc_reference": "reserved",
    },
    "frame_d_translation_gap": {
        "likely_layer": "FRAME-D",
        "suggested_upgrade_type": "unknown",
        "suggested_next_packet_type": "FRAME-D-COMPAT",
        "patch_surface": "legacy mapper translation surface",
        "risk_note": "Keep FRAME-D derived from FRAME-C; no parallel classifier.",
        "precedent_dc_reference": "DC-074",
    },
    "out_of_scope_underdetect": {
        "likely_layer": "OUT_OF_SCOPE",
        "suggested_upgrade_type": "mark_case_out_of_scope",
        "suggested_next_packet_type": "NO-ROUTE-HARDEN",
        "patch_surface": "out-of-scope signal or no-route synthesis",
        "risk_note": "Out-of-scope behavior must remain no-selection.",
        "precedent_dc_reference": "DC-074",
    },
    "fixture_distribution_drift": {
        "likely_layer": "MATRIX",
        "suggested_upgrade_type": "update_expected_case",
        "suggested_next_packet_type": "MATRIX-RECONCILE",
        "patch_surface": "matrix expected fields / grouping",
        "risk_note": "Treat as fixture drift unless parser output is invalid.",
        "precedent_dc_reference": "DC-077",
    },
    "expected_field_drift": {
        "likely_layer": "MATRIX",
        "suggested_upgrade_type": "update_expected_case",
        "suggested_next_packet_type": "MATRIX-RECONCILE",
        "patch_surface": "matrix expected fields",
        "risk_note": "Review whether expectation or parser contract changed.",
        "precedent_dc_reference": "DC-077",
    },
    "unknown": {
        "likely_layer": "UNKNOWN",
        "suggested_upgrade_type": "unknown",
        "suggested_next_packet_type": "TRIAGE",
        "patch_surface": "manual triage",
        "risk_note": "No bounded fix surface inferred.",
        "precedent_dc_reference": "none",
    },
}


_FORBIDDEN_TAGS = frozenset({
    "route_selection",
    "retrieval",
    "ranking",
    "source_admission",
    "benchmark_execution",
})


class ParserVariantCaseSetMismatch(Exception):
    """Raised when two result sets do not cover the same case ids."""


class ParserQualityLoopMalformedCaseResult(Exception):
    """Raised when a case_result is missing required shape."""


class ParserQualityLoopMalformedMatrixResult(Exception):
    """Raised when a matrix result is missing required shape."""


class ParserQualityLoopMalformedFeedbackReport(Exception):
    """Raised when a feedback report is missing required shape."""


class ParserQualityLoopMalformedUpgradeCandidate(Exception):
    """Raised when an upgrade candidate is missing required shape."""


class ParserQualityLoopUnknownFailureClass(Exception):
    """Raised when classified_as is outside the bounded failure classes."""


class ParserQualityLoopForbiddenClaimPhrase(Exception):
    """Raised when an emitted output contains a forbidden claim phrase."""


_REQUIRED_CASE_RESULT_KEYS = frozenset({
    "case_id",
    "match",
    "classified_as",
    "observed_category",
    "expected_category",
    "observed_kinds",
    "expected_kinds",
    "observed_ambiguity",
    "expected_ambiguity",
    "observed_normalized_intent",
    "expected_normalized_intent",
    "observed_candidate_surface",
    "expected_candidate_surface",
    "observed_rejection_surface",
    "expected_rejection_surface",
    "differing_fields",
    "tags",
})


def _halt(event_log, reason, **payload):
    if event_log is not None and hasattr(event_log, "halt"):
        event_log.halt(reason=reason, **payload)


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, sub_value in value.items():
            yield from _walk_strings(key)
            yield from _walk_strings(sub_value)
    elif isinstance(value, (list, tuple)):
        for sub_value in value:
            yield from _walk_strings(sub_value)


def _assert_no_forbidden_claim_phrase(value, event_log, location):
    for text in _walk_strings(value):
        lowered = text.lower()
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                _halt(
                    event_log,
                    "parser_quality_loop_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ParserQualityLoopForbiddenClaimPhrase(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _validate_case_result(case_result, event_log=None):
    if not isinstance(case_result, dict):
        _halt(event_log, "parser_quality_loop_non_dict_case_result")
        raise ParserQualityLoopMalformedCaseResult(
            "case_result must be a dict"
        )
    missing = _REQUIRED_CASE_RESULT_KEYS - set(case_result)
    if missing:
        _halt(
            event_log,
            "parser_quality_loop_missing_case_result_key",
            missing=sorted(missing),
        )
        raise ParserQualityLoopMalformedCaseResult(
            "case_result missing required keys: {0}".format(sorted(missing))
        )
    if case_result["classified_as"] not in set(FAILURE_CLASSES) | {"match"}:
        _halt(
            event_log,
            "parser_quality_loop_unknown_failure_class",
            classified_as=case_result["classified_as"],
        )
        raise ParserQualityLoopUnknownFailureClass(
            "Unknown failure class: {0}".format(case_result["classified_as"])
        )
    if not isinstance(case_result["differing_fields"], list):
        _halt(event_log, "parser_quality_loop_non_list_differing_fields")
        raise ParserQualityLoopMalformedCaseResult(
            "differing_fields must be a list"
        )
    if not isinstance(case_result["tags"], list):
        _halt(event_log, "parser_quality_loop_non_list_tags")
        raise ParserQualityLoopMalformedCaseResult("tags must be a list")


def _validate_matrix_result(matrix_result, event_log=None):
    if not isinstance(matrix_result, dict):
        _halt(event_log, "parser_quality_loop_non_dict_matrix_result")
        raise ParserQualityLoopMalformedMatrixResult(
            "matrix_result must be a dict"
        )
    if (
        matrix_result.get("intent_test_matrix_runner_kind")
        != "level0_workshop_intent_test_matrix_runner"
    ):
        _halt(event_log, "parser_quality_loop_invalid_runner_kind")
        raise ParserQualityLoopMalformedMatrixResult(
            "intent_test_matrix_runner_kind is missing or invalid"
        )
    if "case_results" not in matrix_result:
        _halt(event_log, "parser_quality_loop_missing_case_results")
        raise ParserQualityLoopMalformedMatrixResult(
            "case_results is required"
        )
    if not isinstance(matrix_result["case_results"], list):
        _halt(event_log, "parser_quality_loop_non_list_case_results")
        raise ParserQualityLoopMalformedMatrixResult(
            "case_results must be a list"
        )
    for case_result in matrix_result["case_results"]:
        _validate_case_result(case_result, event_log=event_log)


def _validate_feedback_report(feedback_report, event_log=None):
    if not isinstance(feedback_report, dict):
        _halt(event_log, "parser_quality_loop_non_dict_feedback_report")
        raise ParserQualityLoopMalformedFeedbackReport(
            "feedback_report must be a dict"
        )
    if (
        feedback_report.get("parser_quality_feedback_kind")
        != "level0_workshop_parser_quality_feedback"
    ):
        _halt(event_log, "parser_quality_loop_invalid_feedback_kind")
        raise ParserQualityLoopMalformedFeedbackReport(
            "parser_quality_feedback_kind is missing or invalid"
        )
    if "upgrade_plans" not in feedback_report:
        _halt(event_log, "parser_quality_loop_missing_upgrade_plans")
        raise ParserQualityLoopMalformedFeedbackReport(
            "upgrade_plans is required"
        )
    if not isinstance(feedback_report["upgrade_plans"], list):
        _halt(event_log, "parser_quality_loop_non_list_upgrade_plans")
        raise ParserQualityLoopMalformedFeedbackReport(
            "upgrade_plans must be a list"
        )
    for plan in feedback_report["upgrade_plans"]:
        if not isinstance(plan, dict):
            _halt(event_log, "parser_quality_loop_non_dict_upgrade_plan")
            raise ParserQualityLoopMalformedFeedbackReport(
                "upgrade_plans entries must be dicts"
            )
        missing = set(UPGRADE_PLAN_FIELDS) - set(plan)
        if missing:
            _halt(
                event_log,
                "parser_quality_loop_missing_upgrade_plan_key",
                missing=sorted(missing),
            )
            raise ParserQualityLoopMalformedFeedbackReport(
                "upgrade plan missing required keys: {0}".format(
                    sorted(missing)
                )
            )
        if plan["failure_class"] not in set(FAILURE_CLASSES) | {"unknown"}:
            _halt(
                event_log,
                "parser_quality_loop_unknown_upgrade_plan_failure_class",
                failure_class=plan["failure_class"],
            )
            raise ParserQualityLoopUnknownFailureClass(
                "Unknown failure class: {0}".format(plan["failure_class"])
            )
        if plan["suggested_upgrade_type"] not in SUGGESTED_UPGRADE_TYPES:
            _halt(
                event_log,
                "parser_quality_loop_unknown_upgrade_type",
                suggested_upgrade_type=plan["suggested_upgrade_type"],
            )
            raise ParserQualityLoopMalformedFeedbackReport(
                "Unknown suggested_upgrade_type: {0}".format(
                    plan["suggested_upgrade_type"]
                )
            )


def _validate_upgrade_candidate(candidate, event_log=None):
    if not isinstance(candidate, dict):
        _halt(event_log, "parser_quality_loop_non_dict_upgrade_candidate")
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "upgrade candidate must be a dict"
        )
    missing = set(UPGRADE_CANDIDATE_FIELDS) - set(candidate)
    if missing:
        _halt(
            event_log,
            "parser_quality_loop_missing_upgrade_candidate_key",
            missing=sorted(missing),
        )
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "upgrade candidate missing required keys: {0}".format(
                sorted(missing)
            )
        )
    if candidate["failure_class"] not in set(FAILURE_CLASSES) | {"unknown"}:
        _halt(
            event_log,
            "parser_quality_loop_unknown_candidate_failure_class",
            failure_class=candidate["failure_class"],
        )
        raise ParserQualityLoopUnknownFailureClass(
            "Unknown candidate failure class: {0}".format(
                candidate["failure_class"]
            )
        )
    if candidate["suggested_upgrade_type"] not in SUGGESTED_UPGRADE_TYPES:
        _halt(
            event_log,
            "parser_quality_loop_unknown_candidate_upgrade_type",
            suggested_upgrade_type=candidate["suggested_upgrade_type"],
        )
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "Unknown candidate suggested_upgrade_type: {0}".format(
                candidate["suggested_upgrade_type"]
            )
        )
    if not isinstance(candidate["affected_case_ids"], list):
        _halt(event_log, "parser_quality_loop_non_list_affected_case_ids")
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "affected_case_ids must be a list"
        )


def _ambiguity_direction(case_result):
    observed = case_result.get("observed_ambiguity")
    expected = case_result.get("expected_ambiguity")
    if observed is False and expected is True:
        return "underreport"
    if observed is True and expected is False:
        return "overreport"
    return "none"


def _field_snapshot(case_result, prefix):
    return {
        "category": case_result.get(prefix + "_category"),
        "kinds": case_result.get(prefix + "_kinds"),
        "ambiguity": case_result.get(prefix + "_ambiguity"),
        "normalized_intent": case_result.get(prefix + "_normalized_intent"),
        "candidate_surface": case_result.get(prefix + "_candidate_surface"),
        "rejection_surface": case_result.get(prefix + "_rejection_surface"),
    }


def plan_upgrade_for_case_result(case_result, event_log=None):
    """Return a fixed-shape upgrade plan for one failed case result."""
    _validate_case_result(case_result, event_log=event_log)
    failure_class = case_result.get("classified_as", "unknown")
    plan_template = _PLAN_BY_FAILURE_CLASS.get(
        failure_class, _PLAN_BY_FAILURE_CLASS["unknown"]
    )
    tags = tuple(case_result.get("tags", ()))
    forbidden = bool(set(tags) & _FORBIDDEN_TAGS)
    safety_tier = "forbidden" if forbidden else "proposal_only"
    suggested_upgrade_type = (
        "unknown" if forbidden else plan_template["suggested_upgrade_type"]
    )
    plan = {
        "case_id": case_result.get("case_id"),
        "failure_class": failure_class,
        "likely_layer": plan_template["likely_layer"],
        "observed_fields": _field_snapshot(case_result, "observed"),
        "expected_fields": _field_snapshot(case_result, "expected"),
        "affected_tags": list(tags),
        "suggested_upgrade_type": suggested_upgrade_type,
        "suggested_next_packet_type": plan_template["suggested_next_packet_type"],
        "patch_surface": plan_template["patch_surface"],
        "safety_tier": safety_tier,
        "risk_note": plan_template["risk_note"],
        "precedent_dc_reference": plan_template["precedent_dc_reference"],
    }
    if failure_class == "frame_c_ambiguity_misreport":
        plan["ambiguity_direction"] = _ambiguity_direction(case_result)
        if plan["ambiguity_direction"] not in AMBIGUITY_DIRECTIONS:
            plan["ambiguity_direction"] = "none"
    return plan


def build_feedback_report(matrix_result, event_log=None):
    """Build a deterministic feedback report from a matrix result."""
    _validate_matrix_result(matrix_result, event_log=event_log)
    failed_cases = [
        case_result
        for case_result in matrix_result.get("case_results", ())
        if not case_result.get("match")
    ]
    upgrade_plans = [
        plan_upgrade_for_case_result(case_result, event_log=event_log)
        for case_result in failed_cases
    ]
    per_upgrade_type_counts = {}
    for plan in upgrade_plans:
        upgrade_type = plan["suggested_upgrade_type"]
        per_upgrade_type_counts[upgrade_type] = (
            per_upgrade_type_counts.get(upgrade_type, 0) + 1
        )
    return {
        "parser_quality_feedback_kind": "level0_workshop_parser_quality_feedback",
        "matrix_id": matrix_result.get("matrix_id"),
        "case_count": matrix_result.get("case_count"),
        "failed_count": matrix_result.get("failed_count"),
        "upgrade_plans": upgrade_plans,
        "per_upgrade_type_counts": per_upgrade_type_counts,
        "report_note": REPORT_NOTE,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }
    _assert_no_forbidden_claim_phrase(
        report, event_log, "parser_quality_feedback_report"
    )
    return report


def _case_map(result):
    return {
        case_result["case_id"]: case_result
        for case_result in result.get("case_results", ())
    }


def _tag_delta_counts(baseline_cases, candidate_cases):
    values = set()
    for case in baseline_cases.values():
        values.update(case.get("tags", ()))
    for case in candidate_cases.values():
        values.update(case.get("tags", ()))
    deltas = {}
    for value in sorted(values):
        baseline_failures = sum(
            1
            for case in baseline_cases.values()
            if not case.get("match") and value in case.get("tags", ())
        )
        candidate_failures = sum(
            1
            for case in candidate_cases.values()
            if not case.get("match") and value in case.get("tags", ())
        )
        deltas[value] = {
            "baseline": baseline_failures,
            "candidate": candidate_failures,
            "delta": candidate_failures - baseline_failures,
        }
    return deltas


def _failure_class_delta_counts(baseline_cases, candidate_cases):
    deltas = {}
    for failure_class in FAILURE_CLASSES:
        baseline_count = sum(
            1
            for case in baseline_cases.values()
            if not case.get("match") and case.get("classified_as") == failure_class
        )
        candidate_count = sum(
            1
            for case in candidate_cases.values()
            if not case.get("match") and case.get("classified_as") == failure_class
        )
        deltas[failure_class] = {
            "baseline": baseline_count,
            "candidate": candidate_count,
            "delta": candidate_count - baseline_count,
        }
    return deltas


def _candidate_intent_and_tier(plan_group):
    first_plan = plan_group[0]
    next_packet = first_plan["suggested_next_packet_type"]
    upgrade_type = first_plan["suggested_upgrade_type"]
    safety_tier = "proposal_only"
    if any(plan.get("safety_tier") == "forbidden" for plan in plan_group):
        safety_tier = "forbidden"
    if next_packet == "MATRIX-RECONCILE":
        intent = "matrix_reconciliation"
    elif next_packet in ("CLARIFICATION-DESIGN", "FRAME-A-HARDEN", "FRAME-D-COMPAT"):
        intent = "reserved_layer_design_proposal"
        if safety_tier != "forbidden":
            safety_tier = "requires_reserved_layer"
    elif upgrade_type == "unknown":
        intent = "requires_triage"
    else:
        intent = "parser_improvement"
    return intent, safety_tier


def _expectation_drift_risk(plan_group):
    if any(plan["failure_class"] == "expected_field_drift" for plan in plan_group):
        return "high"
    if any(
        plan["suggested_upgrade_type"] == "update_expected_case"
        for plan in plan_group
    ):
        return "medium"
    return "low"


def _patch_template_for(likely_layer, suggested_upgrade_type):
    return PATCH_PLAN_TEMPLATES.get(
        (likely_layer, suggested_upgrade_type),
        PATCH_PLAN_TEMPLATES[("UNKNOWN", "unknown")],
    )


def _required_tests_for(next_packet_type):
    return list(
        REQUIRED_TESTS_BY_NEXT_PACKET.get(
            next_packet_type, REQUIRED_TESTS_BY_NEXT_PACKET["TRIAGE"]
        )
    )


def _risk_note_for(likely_layer, suggested_upgrade_type):
    return RISK_NOTES_BY_LAYER_AND_TYPE.get(
        (likely_layer, suggested_upgrade_type),
        RISK_NOTES_BY_LAYER_AND_TYPE[("UNKNOWN", "unknown")],
    )


def _safety_tier_sort_key(safety_tier):
    return CANDIDATE_SAFETY_TIERS.index(safety_tier)


def _failure_class_sort_key(failure_class):
    if failure_class in FAILURE_CLASSES:
        return FAILURE_CLASSES.index(failure_class)
    return len(FAILURE_CLASSES)


def _append_execution_event(
    execution_log,
    step_index,
    iteration,
    stage,
    status,
    detail,
    case_id=None,
    candidate_id=None,
    failure_class=None,
    suggested_upgrade_type=None,
):
    event = {
        "event_index": len(execution_log) + 1,
        "step_index": step_index,
        "iteration": iteration,
        "stage": stage,
        "status": status,
        "case_id": case_id,
        "candidate_id": candidate_id,
        "failure_class": failure_class,
        "suggested_upgrade_type": suggested_upgrade_type,
        "detail": detail,
    }
    if tuple(event) != PLANNER_EXECUTION_LOG_FIELDS:
        raise ParserQualityLoopMalformedFeedbackReport(
            "planner execution log fields drifted"
        )
    execution_log.append(event)


def _candidate_sort_key(candidate):
    return (
        -candidate["affected_count"],
        _safety_tier_sort_key(candidate["safety_tier"]),
        _failure_class_sort_key(candidate["failure_class"]),
        candidate["failure_class"],
        candidate["suggested_upgrade_type"],
    )


def build_upgrade_candidates(feedback_report, event_log=None):
    """Group feedback plans into bounded upgrade candidates for review."""
    _validate_feedback_report(feedback_report, event_log=event_log)
    execution_log = []
    _append_execution_event(
        execution_log,
        1,
        1,
        "validate_feedback_report",
        "passed",
        "feedback report shape accepted",
    )
    grouped = {}
    for iteration, plan in enumerate(feedback_report["upgrade_plans"], start=1):
        key = (plan["failure_class"], plan["suggested_upgrade_type"])
        grouped.setdefault(key, []).append(plan)
        _append_execution_event(
            execution_log,
            2,
            iteration,
            "group_upgrade_plan",
            "passed",
            "upgrade plan assigned to group",
            case_id=plan["case_id"],
            failure_class=plan["failure_class"],
            suggested_upgrade_type=plan["suggested_upgrade_type"],
        )
    candidates = []
    for iteration, ((failure_class, upgrade_type), plan_group) in enumerate(
        grouped.items(), start=1
    ):
        first_plan = plan_group[0]
        candidate_intent, safety_tier = _candidate_intent_and_tier(plan_group)
        likely_layer = first_plan["likely_layer"]
        next_packet = first_plan["suggested_next_packet_type"]
        candidate = {
            "candidate_id": "",
            "failure_class": failure_class,
            "suggested_upgrade_type": upgrade_type,
            "suggested_next_packet_type": next_packet,
            "candidate_intent": candidate_intent,
            "likely_layer": likely_layer,
            "safety_tier": safety_tier,
            "expectation_drift_risk": _expectation_drift_risk(plan_group),
            "affected_case_ids": sorted(plan["case_id"] for plan in plan_group),
            "affected_tags": sorted({
                tag
                for plan in plan_group
                for tag in plan.get("affected_tags", ())
            }),
            "affected_count": len(plan_group),
            "patch_plan_skeleton": _patch_template_for(
                likely_layer, upgrade_type
            ),
            "required_tests": _required_tests_for(next_packet),
            "risk_notes": _risk_note_for(likely_layer, upgrade_type),
            "precedent_dc_reference": first_plan["precedent_dc_reference"],
        }
        if tuple(candidate) != UPGRADE_CANDIDATE_FIELDS:
            _halt(event_log, "parser_quality_loop_candidate_field_drift")
            raise ParserQualityLoopMalformedFeedbackReport(
                "upgrade candidate fields drifted"
            )
        candidates.append(candidate)
        _append_execution_event(
            execution_log,
            3,
            iteration,
            "build_upgrade_candidate",
            "passed",
            "candidate built from grouped plans",
            failure_class=failure_class,
            suggested_upgrade_type=upgrade_type,
        )
    candidates.sort(key=_candidate_sort_key)
    _append_execution_event(
        execution_log,
        4,
        1,
        "sort_upgrade_candidates",
        "passed",
        "candidates sorted by count, safety, failure class, and key",
    )
    for index, candidate in enumerate(candidates, start=1):
        candidate["candidate_id"] = "UPG-{0:03d}".format(index)
        _append_execution_event(
            execution_log,
            5,
            index,
            "assign_candidate_id",
            "passed",
            "candidate id assigned after sort",
            candidate_id=candidate["candidate_id"],
            failure_class=candidate["failure_class"],
            suggested_upgrade_type=candidate["suggested_upgrade_type"],
        )
    result = {
        "upgrade_candidates_kind": "level0_workshop_upgrade_candidates",
        "matrix_id": feedback_report.get("matrix_id"),
        "case_count": feedback_report.get("case_count"),
        "failed_count": feedback_report.get("failed_count"),
        "upgrade_candidates": candidates,
        "candidate_count": len(candidates),
        "execution_log": execution_log,
        "planner_note": PLANNER_REPORT_NOTE,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
        "variant_execution_authorized": False,
    }
    _assert_no_forbidden_claim_phrase(
        result, event_log, "parser_quality_upgrade_candidates"
    )
    _append_execution_event(
        execution_log,
        6,
        1,
        "scan_planner_output",
        "passed",
        "forbidden claim phrase scan passed",
    )
    _assert_no_forbidden_claim_phrase(
        result, event_log, "parser_quality_upgrade_candidates"
    )
    return result


def _case_result_by_id(matrix_result):
    return {
        case_result["case_id"]: case_result
        for case_result in matrix_result.get("case_results", ())
    }


def _only_ambiguity_surface_differs(case_result):
    differing = set(case_result.get("differing_fields", ()))
    allowed = {"ambiguity_observed", "candidate_surface_expected"}
    return bool(differing) and differing <= allowed


def _category_and_kinds_match(case_result):
    return (
        case_result.get("observed_category") == case_result.get("expected_category")
        and case_result.get("observed_kinds") == case_result.get("expected_kinds")
    )


def _review_label_for_case(candidate, case_result):
    tags = set(case_result.get("tags", ()))
    if "negation" in tags:
        return "likely_negation_gap"
    if (
        candidate["failure_class"] == "frame_c_ambiguity_misreport"
        and _category_and_kinds_match(case_result)
        and _only_ambiguity_surface_differs(case_result)
    ):
        return "likely_matrix_expectation_drift"
    if (
        candidate["failure_class"] == "frame_c_ambiguity_misreport"
        and not _category_and_kinds_match(case_result)
    ):
        return "likely_synthesis_gap"
    return "needs_human_review"


def _case_review_row(candidate, case_result):
    review_label = _review_label_for_case(candidate, case_result)
    if review_label not in CASE_REVIEW_LABELS:
        review_label = "needs_human_review"
    row = {
        "case_id": case_result["case_id"],
        "review_label": review_label,
        "expected_category": case_result["expected_category"],
        "observed_category": case_result["observed_category"],
        "expected_kinds": list(case_result["expected_kinds"]),
        "observed_kinds": list(case_result["observed_kinds"]),
        "expected_ambiguity": case_result["expected_ambiguity"],
        "observed_ambiguity": case_result["observed_ambiguity"],
        "differing_fields": list(case_result["differing_fields"]),
        "tags": list(case_result["tags"]),
    }
    if tuple(row) != CANDIDATE_CASE_REVIEW_FIELDS:
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "candidate case review fields drifted"
        )
    return row


def _review_label_counts(case_reviews):
    counts = {label: 0 for label in CASE_REVIEW_LABELS}
    for row in case_reviews:
        counts[row["review_label"]] += 1
    return counts


def build_candidate_case_review(candidate, matrix_result, event_log=None):
    """Split one upgrade candidate into bounded per-case review labels."""
    _validate_upgrade_candidate(candidate, event_log=event_log)
    _validate_matrix_result(matrix_result, event_log=event_log)
    case_map = _case_result_by_id(matrix_result)
    case_reviews = []
    for case_id in candidate["affected_case_ids"]:
        if case_id not in case_map:
            _halt(
                event_log,
                "parser_quality_loop_candidate_case_missing",
                case_id=case_id,
            )
            raise ParserQualityLoopMalformedUpgradeCandidate(
                "candidate case_id not present in matrix result: {0}".format(
                    case_id
                )
            )
        case_reviews.append(_case_review_row(candidate, case_map[case_id]))
    report = {
        "candidate_case_review_kind": (
            "level0_workshop_candidate_case_review"
        ),
        "candidate_id": candidate["candidate_id"],
        "failure_class": candidate["failure_class"],
        "affected_count": candidate["affected_count"],
        "case_reviews": case_reviews,
        "per_review_label_counts": _review_label_counts(case_reviews),
        "review_note": CANDIDATE_REVIEW_NOTE,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }
    if tuple(report) != CANDIDATE_CASE_REVIEW_REPORT_FIELDS:
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "candidate case review report fields drifted"
        )
    _assert_no_forbidden_claim_phrase(
        report, event_log, "parser_quality_candidate_case_review"
    )
    return report


def build_candidate_review_summary(planner_result, matrix_result, event_log=None):
    """Build case-review reports for every upgrade candidate."""
    if not isinstance(planner_result, dict):
        _halt(event_log, "parser_quality_loop_non_dict_planner_result")
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "planner_result must be a dict"
        )
    if (
        planner_result.get("upgrade_candidates_kind")
        != "level0_workshop_upgrade_candidates"
    ):
        _halt(event_log, "parser_quality_loop_invalid_planner_result_kind")
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "upgrade_candidates_kind is missing or invalid"
        )
    if not isinstance(planner_result.get("upgrade_candidates"), list):
        _halt(event_log, "parser_quality_loop_non_list_upgrade_candidates")
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "upgrade_candidates must be a list"
        )
    reviews = [
        build_candidate_case_review(candidate, matrix_result, event_log=event_log)
        for candidate in planner_result["upgrade_candidates"]
    ]
    overall = {label: 0 for label in CASE_REVIEW_LABELS}
    for review in reviews:
        for label, count in review["per_review_label_counts"].items():
            overall[label] += count
    summary = {
        "candidate_review_summary_kind": (
            "level0_workshop_candidate_review_summary"
        ),
        "matrix_id": planner_result.get("matrix_id"),
        "candidate_count": len(reviews),
        "candidate_case_reviews": reviews,
        "overall_review_label_counts": overall,
        "review_note": CANDIDATE_REVIEW_NOTE,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }
    if tuple(summary) != CANDIDATE_REVIEW_SUMMARY_FIELDS:
        raise ParserQualityLoopMalformedUpgradeCandidate(
            "candidate review summary fields drifted"
        )
    _assert_no_forbidden_claim_phrase(
        summary, event_log, "parser_quality_candidate_review_summary"
    )
    return summary


def compare_parser_result_sets(baseline_result, candidate_result, event_log=None):
    """Compare two parser matrix result sets by case id."""
    _validate_matrix_result(baseline_result, event_log=event_log)
    _validate_matrix_result(candidate_result, event_log=event_log)
    baseline_cases = _case_map(baseline_result)
    candidate_cases = _case_map(candidate_result)
    if set(baseline_cases) != set(candidate_cases):
        _halt(event_log, "parser_variant_case_set_mismatch")
        raise ParserVariantCaseSetMismatch(
            "Parser variant result sets must cover the same case ids."
        )
    improved_cases = []
    regressed_cases = []
    unchanged_failures = []
    newly_failed_cases = []
    for case_id in [case["case_id"] for case in baseline_result["case_results"]]:
        baseline_match = bool(baseline_cases[case_id].get("match"))
        candidate_match = bool(candidate_cases[case_id].get("match"))
        if not baseline_match and candidate_match:
            improved_cases.append(case_id)
        elif baseline_match and not candidate_match:
            regressed_cases.append(case_id)
            newly_failed_cases.append(case_id)
        elif not baseline_match and not candidate_match:
            unchanged_failures.append(case_id)
    comparison = {
        "parser_variant_comparison_kind": (
            "level0_workshop_parser_variant_comparison"
        ),
        "baseline_matrix_id": baseline_result.get("matrix_id"),
        "candidate_matrix_id": candidate_result.get("matrix_id"),
        "baseline_passed_count": baseline_result.get("passed_count"),
        "candidate_passed_count": candidate_result.get("passed_count"),
        "improved_cases": improved_cases,
        "regressed_cases": regressed_cases,
        "unchanged_failures": unchanged_failures,
        "newly_failed_cases": newly_failed_cases,
        "per_tag_delta": _tag_delta_counts(baseline_cases, candidate_cases),
        "per_failure_class_delta": _failure_class_delta_counts(
            baseline_cases, candidate_cases
        ),
        "comparison_note": REPORT_NOTE,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
    }
    _assert_no_forbidden_claim_phrase(
        comparison, event_log, "parser_variant_comparison"
    )
    return comparison
