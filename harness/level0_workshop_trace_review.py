"""Level 0B Awesome Copilot workshop trace review scaffold.

WO-L0-WORKSHOP-REVIEW-01 adds a scaffold-only review-layer module
that consumes the already-loaded output dict from the upstream
WO-L0-WORKSHOP-TRACE-01 scaffold and emits a fixed-shape bounded
review observation: shape checks, per-category counts, candidate /
rejection surface presence checks, ambiguity / no-selection /
rejection invariants, and explicit next-gap notes.

This module performs no file IO, no network call, no URL fetch /
download / crawl, no PDF text extraction, no hash computation, no
external process or external shell execution, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools.

This module invokes NO prior-WO public function. The review module
takes an already-loaded dict only; it does not import or call the
upstream trace scaffold or any other prior-WO public function
(verified by static-scan test).

This module does NOT qualify any source, does NOT admit any source
to corpus, does NOT extract or normalize source material, does NOT
promote any record to an official route, does NOT compute any
similarity / distance / ranking / metric, and does NOT decide
architecture / vendor / library / index family / ANN backend /
reranker / retrieval family / production system.

Passing this review means only that the scaffold trace surface is
internally coherent for the Level 0B workshop seed. It does NOT
mean sufficient, necessary, best, complete, production-ready,
recommended, selected, benchmark-ready, or route-ready.

The Constraints v1 non-claim constraint carries forward: this
module does not claim any observed count, observed surface flag,
next-gap note, or computed observation is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected. The bounded required-key set, the bounded next-gap-note
literals, and the fixed output key set are bounded by
WO-L0-WORKSHOP-REVIEW-01 and are NOT claimed exhaustive.

Public surface:

    run_level0_workshop_trace_review(
        workshop_trace_report, event_log
    ) -> dict

All seven gating booleans (`route_created`, `selection_made`,
`measurement_authorized`, `real_benchmark_authorized`,
`real_benchmark_ready`, `source_qualification_authorized`,
`corpus_admission_authorized`) are literal False on every emitted
path. `review_halt_required` is literal False on every clean-pass
emit; halt paths raise named exceptions before emitting a dict.
`review_passed` is literal True only on clean pass.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


REVIEW_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "workshop_review_kind",
    "input_trace_kind",
    "review_passed",
    "review_halt_required",
    "observed_item_count",
    "observed_prompt_count",
    "observed_candidate_route_fragment_count",
    "observed_candidate_workflow_fragment_count",
    "observed_rejected_material_count",
    "ambiguous_prompt_count",
    "no_route_prompt_count",
    "near_miss_prompt_count",
    "candidate_surface_observed",
    "workflow_surface_observed",
    "rejection_surface_observed",
    "route_created",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "next_gap_notes",
    "review_note",
)


# Required keys on the input workshop-trace report. Mirrors the
# WO-L0-WORKSHOP-TRACE-01 nineteen-key clean-pass output.
REQUIRED_INPUT_KEYS = (
    "workshop_trace_kind",
    "item_count",
    "prompt_count",
    "derived_material_records",
    "derived_material_count",
    "candidate_route_fragment_records",
    "candidate_route_fragment_count",
    "candidate_workflow_fragment_records",
    "candidate_workflow_fragment_count",
    "rejected_material_records",
    "rejected_material_count",
    "per_prompt_trace_summary",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "workshop_trace_note",
)
_REQUIRED_INPUT_KEY_SET = frozenset(REQUIRED_INPUT_KEYS)


_EXPECTED_INPUT_TRACE_KIND = "level0_workshop_derived_trace"

_EXPECTED_ITEM_COUNT = 70
_EXPECTED_PROMPT_COUNT = 26
_EXPECTED_DERIVED_COUNT = 70
_EXPECTED_CANDIDATE_ROUTE_COUNT = 51
_EXPECTED_CANDIDATE_WORKFLOW_COUNT = 13
_EXPECTED_REJECTED_COUNT = 6
_EXPECTED_AMBIGUOUS_COUNT = 3
_EXPECTED_NO_ROUTE_COUNT = 2
_EXPECTED_NEAR_MISS_COUNT = 2


_AMBIGUOUS_CATEGORY = "G. ambiguous"
_NO_ROUTE_CATEGORY = "H. no-route"
_REJECTION_CATEGORY = "I. near-miss/rejection"

_NO_ROUTE_REASON = "prompt_out_of_repo_scope"
_REJECTION_REASON = "repo_meta_section_near_miss"


_AUTH_BOOLEAN_KEYS = (
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
)


_FORBIDDEN_ROUTE_STATUS_FIELDS = (
    "official",
    "is_route",
    "is_official_route",
    "selected_as_official",
    "official_route_authorized",
    "route_authorized",
    "production_route",
    "selected_route",
    "executable",
    "route_state",
    "plane",
)


_NEXT_GAP_NOTES = (
    "semantic_content_extraction_not_tested",
    "real_indexing_not_implemented",
    "route_selection_not_authorized",
    "cross_vendor_seed_not_executed",
)


_WORKSHOP_REVIEW_KIND = "level0_workshop_trace_review"


_REVIEW_NOTE = (
    "level0_workshop_trace_review: a clean-pass review observation "
    "over an already-loaded WO-L0-WORKSHOP-TRACE-01 output dict; "
    "verifies shape / counts / surface presence / per-prompt "
    "invariants only; this review is NOT corpus admission, NOT "
    "source qualification, NOT extraction, NOT normalization, NOT "
    "candidate-fragment promotion, NOT a route object, NOT a "
    "Source Card, NOT permission to flip any authorization / "
    "readiness boolean, and NOT a benchmark-ready flip; passing "
    "the review means only that the scaffold trace surface is "
    "internally coherent for the workshop seed; OQ-003, OQ-015, "
    "OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, "
    "OQ-075, OQ-076 remain OPEN; no real adapter; no benchmark "
    "execution; no measurement authorization."
)


class NonDictWorkshopTraceReport(Exception):
    """Raised when `workshop_trace_report` is not a dict."""


class MissingWorkshopTraceReportKey(Exception):
    """Raised when the input dict is missing a required top-level key."""


class UnknownWorkshopTraceReportKey(Exception):
    """Raised when the input dict carries a top-level key outside the
    bounded `REQUIRED_INPUT_KEYS` set."""


class InvalidWorkshopTraceKind(Exception):
    """Raised when `workshop_trace_kind` is not the expected literal."""


class WorkshopTraceCountMismatch(Exception):
    """Raised when an expected count field does not match its bounded
    value."""


class WorkshopTraceAuthorizationBooleanFlipped(Exception):
    """Raised when any authorization / readiness / selection boolean is
    not literal False."""


class WorkshopTraceRouteStatusFieldPresent(Exception):
    """Raised when any record in any nested collection carries a
    route-status field."""


class WorkshopTraceCandidateOnlyNotTrue(Exception):
    """Raised when any nested record has `candidate_only` not literal
    True."""


class WorkshopTraceForbiddenFlipPresent(Exception):
    """Raised when any nested record has `qualified` /
    `corpus_admitted` / `route_object_created` /
    `source_material_extracted` not literal False where present."""


class WorkshopTraceAmbiguousMissingMarker(Exception):
    """Raised when a `G. ambiguous` per-prompt summary entry does not
    carry `ambiguity_observed: True`."""


class WorkshopTraceNoRouteInvariantViolated(Exception):
    """Raised when an `H. no-route` per-prompt summary entry has any
    non-zero attached count or wrong `no_selection_reason`."""


class WorkshopTraceNearMissInvariantViolated(Exception):
    """Raised when an `I. near-miss/rejection` per-prompt summary entry
    has any non-zero candidate route / workflow count, empty rejected
    attachment, or wrong `no_selection_reason`."""


class ForbiddenLanguageInLevel0WorkshopTraceReview(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in either the input report or
    the emitted review report."""


def _walk_strings(value):
    """Yield every string scalar inside a nested value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, sub_value in value.items():
            for inner in _walk_strings(key):
                yield inner
            for inner in _walk_strings(sub_value):
                yield inner
    elif isinstance(value, (list, tuple)):
        for sub_value in value:
            for inner in _walk_strings(sub_value):
                yield inner


def _assert_no_forbidden_language(value, event_log, location):
    """Halt and raise if any forbidden phrase appears in `value`."""
    for text in _walk_strings(value):
        lowered = text.lower()
        for phrase in REVIEW_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_trace_review_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopTraceReview(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_trace_review_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopTraceReview(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _check_count(report, key, expected, event_log):
    observed = report[key]
    if observed != expected:
        event_log.halt(
            reason="level0_workshop_trace_review_count_mismatch",
            key=key,
            expected=expected,
            observed=observed,
        )
        raise WorkshopTraceCountMismatch(
            "report[{0!r}] expected {1} (observed {2!r})".format(
                key, expected, observed
            )
        )


def _check_collection_length(report, key, expected, event_log):
    observed = len(report[key])
    if observed != expected:
        event_log.halt(
            reason="level0_workshop_trace_review_collection_length_mismatch",
            key=key,
            expected=expected,
            observed=observed,
        )
        raise WorkshopTraceCountMismatch(
            "len(report[{0!r}]) expected {1} (observed {2})".format(
                key, expected, observed
            )
        )


def _check_authorization_booleans(report, event_log):
    for key in _AUTH_BOOLEAN_KEYS:
        if report[key] is not False:
            event_log.halt(
                reason="level0_workshop_trace_review_authorization_boolean_flipped",
                key=key,
            )
            raise WorkshopTraceAuthorizationBooleanFlipped(
                "report[{0!r}] must be literal False".format(key)
            )


def _check_no_route_status_fields(report, event_log):
    record_collections = (
        ("derived_material_records", report["derived_material_records"]),
        ("candidate_route_fragment_records",
         report["candidate_route_fragment_records"]),
        ("candidate_workflow_fragment_records",
         report["candidate_workflow_fragment_records"]),
        ("rejected_material_records", report["rejected_material_records"]),
        ("per_prompt_trace_summary", report["per_prompt_trace_summary"]),
    )
    for location, records in record_collections:
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
                if field in record:
                    event_log.halt(
                        reason="level0_workshop_trace_review_route_status_field_present",
                        location=location,
                        index=index,
                        field=field,
                    )
                    raise WorkshopTraceRouteStatusFieldPresent(
                        "{0}[{1}] carries route-status field '{2}'".format(
                            location, index, field
                        )
                    )


def _check_candidate_only_and_forbidden_flips(report, event_log):
    record_collections = (
        ("derived_material_records", report["derived_material_records"]),
        ("candidate_route_fragment_records",
         report["candidate_route_fragment_records"]),
        ("candidate_workflow_fragment_records",
         report["candidate_workflow_fragment_records"]),
        ("rejected_material_records", report["rejected_material_records"]),
        ("per_prompt_trace_summary", report["per_prompt_trace_summary"]),
    )
    forbidden_flip_keys = (
        "qualified",
        "corpus_admitted",
        "route_object_created",
        "source_material_extracted",
    )
    for location, records in record_collections:
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                continue
            if "candidate_only" in record and record["candidate_only"] is not True:
                event_log.halt(
                    reason="level0_workshop_trace_review_candidate_only_not_true",
                    location=location,
                    index=index,
                )
                raise WorkshopTraceCandidateOnlyNotTrue(
                    "{0}[{1}] candidate_only must be literal True".format(
                        location, index
                    )
                )
            for key in forbidden_flip_keys:
                if key in record and record[key] is not False:
                    event_log.halt(
                        reason="level0_workshop_trace_review_forbidden_flip_present",
                        location=location,
                        index=index,
                        key=key,
                    )
                    raise WorkshopTraceForbiddenFlipPresent(
                        "{0}[{1}] {2!r} must be literal False".format(
                            location, index, key
                        )
                    )


def _count_per_category(per_prompt_summary):
    counts = {
        _AMBIGUOUS_CATEGORY: 0,
        _NO_ROUTE_CATEGORY: 0,
        _REJECTION_CATEGORY: 0,
    }
    for entry in per_prompt_summary:
        if not isinstance(entry, dict):
            continue
        category = entry.get("category")
        if category in counts:
            counts[category] += 1
    return counts


def _check_per_prompt_invariants(per_prompt_summary, event_log):
    for index, entry in enumerate(per_prompt_summary):
        if not isinstance(entry, dict):
            continue
        category = entry.get("category")
        if category == _AMBIGUOUS_CATEGORY:
            if entry.get("ambiguity_observed") is not True:
                event_log.halt(
                    reason="level0_workshop_trace_review_ambiguous_missing_marker",
                    index=index,
                )
                raise WorkshopTraceAmbiguousMissingMarker(
                    "per_prompt_trace_summary[{0}] is ambiguous but ambiguity_observed is not True".format(
                        index
                    )
                )
        elif category == _NO_ROUTE_CATEGORY:
            route_count = entry.get("attached_candidate_route_fragment_count", 0)
            workflow_count = entry.get("attached_candidate_workflow_fragment_count", 0)
            rejected_count = entry.get("attached_rejected_material_count", 0)
            reason = entry.get("no_selection_reason")
            if (
                route_count != 0
                or workflow_count != 0
                or rejected_count != 0
                or reason != _NO_ROUTE_REASON
            ):
                event_log.halt(
                    reason="level0_workshop_trace_review_no_route_invariant_violated",
                    index=index,
                    route_count=route_count,
                    workflow_count=workflow_count,
                    rejected_count=rejected_count,
                    observed_reason=reason,
                )
                raise WorkshopTraceNoRouteInvariantViolated(
                    "per_prompt_trace_summary[{0}] violates no-route invariant".format(
                        index
                    )
                )
        elif category == _REJECTION_CATEGORY:
            route_count = entry.get("attached_candidate_route_fragment_count", 0)
            workflow_count = entry.get("attached_candidate_workflow_fragment_count", 0)
            rejected_count = entry.get("attached_rejected_material_count", 0)
            reason = entry.get("no_selection_reason")
            if (
                route_count != 0
                or workflow_count != 0
                or rejected_count <= 0
                or reason != _REJECTION_REASON
            ):
                event_log.halt(
                    reason="level0_workshop_trace_review_near_miss_invariant_violated",
                    index=index,
                    route_count=route_count,
                    workflow_count=workflow_count,
                    rejected_count=rejected_count,
                    observed_reason=reason,
                )
                raise WorkshopTraceNearMissInvariantViolated(
                    "per_prompt_trace_summary[{0}] violates near-miss invariant".format(
                        index
                    )
                )


def run_level0_workshop_trace_review(workshop_trace_report, event_log):
    """Validate and emit a fixed-shape review observation over an
    already-loaded WO-L0-WORKSHOP-TRACE-01 output dict.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_workshop_trace_review_started")

    if not isinstance(workshop_trace_report, dict):
        event_log.halt(
            reason="level0_workshop_trace_review_non_dict_workshop_trace_report"
        )
        raise NonDictWorkshopTraceReport(
            "workshop_trace_report must be a dict"
        )

    for key in REQUIRED_INPUT_KEYS:
        if key not in workshop_trace_report:
            event_log.halt(
                reason="level0_workshop_trace_review_missing_workshop_trace_report_key",
                key=key,
            )
            raise MissingWorkshopTraceReportKey(
                "workshop_trace_report missing required key '{0}'".format(key)
            )

    for key in workshop_trace_report.keys():
        if key not in _REQUIRED_INPUT_KEY_SET:
            event_log.halt(
                reason="level0_workshop_trace_review_unknown_workshop_trace_report_key",
                key=key,
            )
            raise UnknownWorkshopTraceReportKey(
                "workshop_trace_report contains unknown key '{0}'".format(key)
            )

    _assert_no_forbidden_language(
        workshop_trace_report, event_log, location="workshop_trace_report"
    )

    if workshop_trace_report["workshop_trace_kind"] != _EXPECTED_INPUT_TRACE_KIND:
        event_log.halt(
            reason="level0_workshop_trace_review_invalid_workshop_trace_kind",
            observed=workshop_trace_report["workshop_trace_kind"],
        )
        raise InvalidWorkshopTraceKind(
            "workshop_trace_kind must be '{0}'".format(_EXPECTED_INPUT_TRACE_KIND)
        )

    _check_count(workshop_trace_report, "item_count", _EXPECTED_ITEM_COUNT, event_log)
    _check_count(workshop_trace_report, "prompt_count", _EXPECTED_PROMPT_COUNT, event_log)
    _check_count(
        workshop_trace_report, "derived_material_count",
        _EXPECTED_DERIVED_COUNT, event_log,
    )
    _check_count(
        workshop_trace_report, "candidate_route_fragment_count",
        _EXPECTED_CANDIDATE_ROUTE_COUNT, event_log,
    )
    _check_count(
        workshop_trace_report, "candidate_workflow_fragment_count",
        _EXPECTED_CANDIDATE_WORKFLOW_COUNT, event_log,
    )
    _check_count(
        workshop_trace_report, "rejected_material_count",
        _EXPECTED_REJECTED_COUNT, event_log,
    )

    _check_collection_length(
        workshop_trace_report, "derived_material_records",
        _EXPECTED_DERIVED_COUNT, event_log,
    )
    _check_collection_length(
        workshop_trace_report, "candidate_route_fragment_records",
        _EXPECTED_CANDIDATE_ROUTE_COUNT, event_log,
    )
    _check_collection_length(
        workshop_trace_report, "candidate_workflow_fragment_records",
        _EXPECTED_CANDIDATE_WORKFLOW_COUNT, event_log,
    )
    _check_collection_length(
        workshop_trace_report, "rejected_material_records",
        _EXPECTED_REJECTED_COUNT, event_log,
    )
    _check_collection_length(
        workshop_trace_report, "per_prompt_trace_summary",
        _EXPECTED_PROMPT_COUNT, event_log,
    )

    per_prompt_summary = workshop_trace_report["per_prompt_trace_summary"]

    _check_authorization_booleans(workshop_trace_report, event_log)
    _check_no_route_status_fields(workshop_trace_report, event_log)
    _check_candidate_only_and_forbidden_flips(workshop_trace_report, event_log)
    _check_per_prompt_invariants(per_prompt_summary, event_log)

    category_counts = _count_per_category(per_prompt_summary)
    if category_counts[_AMBIGUOUS_CATEGORY] != _EXPECTED_AMBIGUOUS_COUNT:
        event_log.halt(
            reason="level0_workshop_trace_review_ambiguous_count_mismatch",
            expected=_EXPECTED_AMBIGUOUS_COUNT,
            observed=category_counts[_AMBIGUOUS_CATEGORY],
        )
        raise WorkshopTraceCountMismatch(
            "ambiguous prompt count expected {0} (observed {1})".format(
                _EXPECTED_AMBIGUOUS_COUNT, category_counts[_AMBIGUOUS_CATEGORY]
            )
        )
    if category_counts[_NO_ROUTE_CATEGORY] != _EXPECTED_NO_ROUTE_COUNT:
        event_log.halt(
            reason="level0_workshop_trace_review_no_route_count_mismatch",
            expected=_EXPECTED_NO_ROUTE_COUNT,
            observed=category_counts[_NO_ROUTE_CATEGORY],
        )
        raise WorkshopTraceCountMismatch(
            "no-route prompt count expected {0} (observed {1})".format(
                _EXPECTED_NO_ROUTE_COUNT, category_counts[_NO_ROUTE_CATEGORY]
            )
        )
    if category_counts[_REJECTION_CATEGORY] != _EXPECTED_NEAR_MISS_COUNT:
        event_log.halt(
            reason="level0_workshop_trace_review_near_miss_count_mismatch",
            expected=_EXPECTED_NEAR_MISS_COUNT,
            observed=category_counts[_REJECTION_CATEGORY],
        )
        raise WorkshopTraceCountMismatch(
            "near-miss prompt count expected {0} (observed {1})".format(
                _EXPECTED_NEAR_MISS_COUNT, category_counts[_REJECTION_CATEGORY]
            )
        )

    candidate_surface_observed = (
        workshop_trace_report["candidate_route_fragment_count"] > 0
    )
    workflow_surface_observed = (
        workshop_trace_report["candidate_workflow_fragment_count"] > 0
    )
    rejection_surface_observed = (
        workshop_trace_report["rejected_material_count"] > 0
    )

    result = {
        "workshop_review_kind": _WORKSHOP_REVIEW_KIND,
        "input_trace_kind": workshop_trace_report["workshop_trace_kind"],
        "review_passed": True,
        "review_halt_required": False,
        "observed_item_count": workshop_trace_report["item_count"],
        "observed_prompt_count": workshop_trace_report["prompt_count"],
        "observed_candidate_route_fragment_count": (
            workshop_trace_report["candidate_route_fragment_count"]
        ),
        "observed_candidate_workflow_fragment_count": (
            workshop_trace_report["candidate_workflow_fragment_count"]
        ),
        "observed_rejected_material_count": (
            workshop_trace_report["rejected_material_count"]
        ),
        "ambiguous_prompt_count": category_counts[_AMBIGUOUS_CATEGORY],
        "no_route_prompt_count": category_counts[_NO_ROUTE_CATEGORY],
        "near_miss_prompt_count": category_counts[_REJECTION_CATEGORY],
        "candidate_surface_observed": candidate_surface_observed,
        "workflow_surface_observed": workflow_surface_observed,
        "rejection_surface_observed": rejection_surface_observed,
        "route_created": False,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "next_gap_notes": list(_NEXT_GAP_NOTES),
        "review_note": _REVIEW_NOTE,
    }

    _assert_no_forbidden_language(result, event_log, location="result")

    event_log.append("level0_workshop_trace_review_completed")
    return result
