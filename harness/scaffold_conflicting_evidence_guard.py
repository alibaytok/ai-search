"""Scaffold conflicting-evidence guard over admitted synthetic payloads.

WO-52 adds a scaffold-level guard that inspects already-loaded
synthetic fixture entries for declared structural contradictions
BEFORE any route-query observation is performed. The guard models the
"contradictory evidence inside one entry" failure case that the
WO-47 / WO-48 / WO-50 / WO-51 observation paths assume away.

This module does NOT perform real retrieval, does NOT compute
similarity, does NOT score, does NOT rank, does NOT collect metrics,
does NOT invoke any adapter, does NOT mutate `benchmark-fixtures/`,
does NOT read or write files, and does NOT select any architecture /
vendor / library / index family / ANN backend / neural re-scorer /
retrieval family / ablation cell / multi-stage variant / production
system.

The guard checks eight declared conflict kinds (five admitted under
WO-52; three added under WO-53). The eight declared kinds are NOT a
claim of completeness. The list is bounded by the WO-52 / WO-53
packets and may be extended by future Codex packets. This module does
not claim that any guard, check, conflict kind, observation shape, or
in-memory probe is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected. The WO-47 / WO-48 / WO-49
/ WO-50 / WO-51 non-claim constraint carries forward verbatim.

Declared conflict kinds (each halts and raises on first occurrence):

1. `golden_official_with_expected_halt`: a golden-intents entry
   declares `expected_outcome_class: official_route_expected` and
   also carries `expected_disqualification.expected_halt: True`.
2. `golden_official_reference_with_miss_classification`: a
   golden-intents entry declares an `expected_official_route_reference`
   (a non-empty dict) and also declares `miss_classification` (a
   non-empty string).
3. `hard_negative_allows_official_despite_guard`: a hard-negatives
   entry declares `must_not_authorize_official_return: True` and
   also carries `plane_separation_markers.allowed_planes` containing
   `official_route_results`.
4. `boundary_violation_both_valid_and_forbidden`: a boundary-violations
   entry declares both
   `expected_disqualification.is_forbidden_output: True` and
   `expected_disqualification.is_valid_output: True`.
5. `boundary_violation_official_plane_without_collapse`: a
   boundary-violations entry declares
   `plane_separation_markers.violation_plane_in_observed_output:
   "official_route_results"` but does not declare a non-empty
   `forbidden_plane_collapse` marker.
6. `golden_miss_with_official_route_reference` (WO-53): a
   golden-intents entry declares `expected_outcome_class:
   miss_expected` while also carrying a non-empty
   `expected_official_route_reference` dict.
7. `hard_negative_candidate_only_without_candidate_or_normalized_plane`
   (WO-53): a hard-negatives entry declares
   `near_match_classification: candidate_only` but its
   `plane_separation_markers.allowed_planes` contains neither the
   candidate plane nor the normalized plane.
8. `boundary_violation_expected_halt_without_classification` (WO-53):
   a boundary-violations entry declares
   `expected_disqualification.expected_halt: True` but does not
   declare a non-empty `halt_classification` string.

Public surface:

    run_scaffold_conflicting_evidence_guard(
        payloads_by_class, event_log
    ) -> dict

The function:

- Accepts already-loaded WO-31 synthetic payload dicts for the three
  admitted fixture classes.
- Reads no files. Writes no files. Imports only stdlib and
  harness-internal symbols.
- Validates inputs in documented order.
- Walks every entry in `REQUIRED_PAYLOAD_CLASSES` order, then within
  each class in input list order. The first declared conflict found
  records a halt event and raises the corresponding exception.
- On clean pass, returns a fresh dict with exactly the nine allowed
  top-level keys in `ALLOWED_OUTPUT_KEYS`.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_index_probe import (
    CANDIDATE_PLANE,
    NORMALIZED_PLANE,
    OFFICIAL_PLANE,
    REQUIRED_PAYLOAD_CLASSES,
)


GUARD_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_OUTPUT_KEYS = (
    "guard_kind",
    "inspected_entry_count",
    "inspected_class_counts",
    "declared_conflict_kinds_checked",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "guard_note",
)


DECLARED_CONFLICT_KINDS = (
    "golden_official_with_expected_halt",
    "golden_official_reference_with_miss_classification",
    "hard_negative_allows_official_despite_guard",
    "boundary_violation_both_valid_and_forbidden",
    "boundary_violation_official_plane_without_collapse",
    "golden_miss_with_official_route_reference",
    "hard_negative_candidate_only_without_candidate_or_normalized_plane",
    "boundary_violation_expected_halt_without_classification",
)


class NonObjectPayloadsByClass(Exception):
    """Raised when `payloads_by_class` is not a dict."""


class MissingRequiredPayloadClass(Exception):
    """Raised when a required admitted payload class is absent."""


class NonObjectPayload(Exception):
    """Raised when a per-class payload is not a dict."""


class MissingOrNonListEntries(Exception):
    """Raised when payload entries are missing or not a list."""


class PayloadClassMismatch(Exception):
    """Raised when a payload declares a different fixture class."""


class GoldenOfficialWithExpectedHalt(Exception):
    """Raised when a golden-intents entry declares both an official-route
    outcome and an expected disqualification halt."""


class GoldenOfficialReferenceWithMissClassification(Exception):
    """Raised when a golden-intents entry declares both an official route
    reference and a miss classification."""


class HardNegativeAllowsOfficialDespiteGuard(Exception):
    """Raised when a hard-negatives entry declares
    `must_not_authorize_official_return: True` but lists the official
    plane in its allowed planes."""


class BoundaryViolationBothValidAndForbidden(Exception):
    """Raised when a boundary-violations entry's expected disqualification
    is marked both valid and forbidden."""


class BoundaryViolationOfficialPlaneWithoutCollapse(Exception):
    """Raised when a boundary-violations entry's observed violation lands
    on the official plane but does not record a `forbidden_plane_collapse`."""


class GoldenMissWithOfficialRouteReference(Exception):
    """Raised when a golden-intents entry declares `expected_outcome_class:
    miss_expected` while also carrying a non-empty
    `expected_official_route_reference`."""


class HardNegativeCandidateOnlyWithoutCandidateOrNormalizedPlane(Exception):
    """Raised when a hard-negatives entry declares
    `near_match_classification: candidate_only` but its
    `plane_separation_markers.allowed_planes` contains neither the
    candidate plane nor the normalized plane."""


class BoundaryViolationExpectedHaltWithoutClassification(Exception):
    """Raised when a boundary-violations entry declares
    `expected_disqualification.expected_halt: True` but does not declare a
    non-empty `halt_classification` string."""


class ForbiddenLanguageInConflictingEvidenceGuard(Exception):
    """Raised when forbidden language appears on a surfaced value."""


def _walk_strings(value):
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


def _first_forbidden_phrase(text):
    lowered = text.lower()
    for phrase in GUARD_OUTPUT_FORBIDDEN_PHRASES:
        if phrase in lowered:
            return phrase
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def _assert_no_forbidden_language(value, event_log):
    for text in _walk_strings(value):
        offending = _first_forbidden_phrase(text)
        if offending is not None:
            event_log.halt(
                "scaffold_conflicting_evidence_guard_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInConflictingEvidenceGuard(
                "Forbidden phrase {0!r} found in conflicting-evidence "
                "guard surface".format(offending)
            )


def _validate_payloads(payloads_by_class, event_log):
    if not isinstance(payloads_by_class, dict):
        event_log.halt(
            "scaffold_conflicting_evidence_guard_non_object_input",
            payloads_by_class_type=type(payloads_by_class).__name__,
        )
        raise NonObjectPayloadsByClass("payloads_by_class must be a dict")

    for class_name in REQUIRED_PAYLOAD_CLASSES:
        if class_name not in payloads_by_class:
            event_log.halt(
                "scaffold_conflicting_evidence_guard_missing_required_class",
                class_name=class_name,
            )
            raise MissingRequiredPayloadClass(
                "payloads_by_class is missing {0!r}".format(class_name)
            )
        payload = payloads_by_class[class_name]
        if not isinstance(payload, dict):
            event_log.halt(
                "scaffold_conflicting_evidence_guard_non_object_payload",
                class_name=class_name,
                payload_type=type(payload).__name__,
            )
            raise NonObjectPayload(
                "payload for class {0!r} must be a dict".format(class_name)
            )
        if payload.get("fixture_class") != class_name:
            event_log.halt(
                "scaffold_conflicting_evidence_guard_class_mismatch",
                class_name=class_name,
                declared_class=payload.get("fixture_class"),
            )
            raise PayloadClassMismatch(
                "payload for class {0!r} declares fixture_class={1!r}".format(
                    class_name, payload.get("fixture_class")
                )
            )
        if not isinstance(payload.get("entries"), list):
            event_log.halt(
                "scaffold_conflicting_evidence_guard_missing_or_non_list_entries",
                class_name=class_name,
            )
            raise MissingOrNonListEntries(
                "payload for class {0!r} has missing or non-list entries".format(
                    class_name
                )
            )


def _check_golden_entry(entry, event_log):
    fixture_id = entry.get("fixture_id")
    expected_outcome = entry.get("expected_outcome_class")
    disqualification = entry.get("expected_disqualification") or {}
    if not isinstance(disqualification, dict):
        disqualification = {}

    if (
        expected_outcome == "official_route_expected"
        and disqualification.get("expected_halt") is True
    ):
        event_log.halt(
            "scaffold_conflicting_evidence_guard_golden_official_with_expected_halt",
            fixture_id=fixture_id,
        )
        raise GoldenOfficialWithExpectedHalt(
            "golden-intents entry {0!r} declares official-route outcome and "
            "expected disqualification halt".format(fixture_id)
        )

    reference = entry.get("expected_official_route_reference")
    miss_classification = entry.get("miss_classification")
    if (
        isinstance(reference, dict)
        and reference
        and isinstance(miss_classification, str)
        and miss_classification
    ):
        event_log.halt(
            "scaffold_conflicting_evidence_guard_golden_official_reference_with_miss_classification",
            fixture_id=fixture_id,
        )
        raise GoldenOfficialReferenceWithMissClassification(
            "golden-intents entry {0!r} declares an official route "
            "reference and a miss classification".format(fixture_id)
        )

    if (
        expected_outcome == "miss_expected"
        and isinstance(reference, dict)
        and reference
    ):
        event_log.halt(
            "scaffold_conflicting_evidence_guard_golden_miss_with_official_route_reference",
            fixture_id=fixture_id,
        )
        raise GoldenMissWithOfficialRouteReference(
            "golden-intents entry {0!r} declares miss_expected outcome while "
            "carrying a non-empty expected_official_route_reference".format(
                fixture_id
            )
        )


def _check_hard_negative_entry(entry, event_log):
    fixture_id = entry.get("fixture_id")
    markers = entry.get("plane_separation_markers") or {}
    if not isinstance(markers, dict):
        markers = {}
    allowed = markers.get("allowed_planes") or []
    if not isinstance(allowed, list):
        allowed = []

    if entry.get("must_not_authorize_official_return") is True:
        if OFFICIAL_PLANE in allowed:
            event_log.halt(
                "scaffold_conflicting_evidence_guard_hard_negative_allows_official_despite_guard",
                fixture_id=fixture_id,
            )
            raise HardNegativeAllowsOfficialDespiteGuard(
                "hard-negatives entry {0!r} declares must_not_authorize_official_return "
                "True but lists the official plane in allowed_planes".format(fixture_id)
            )

    if entry.get("near_match_classification") == "candidate_only" and (
        CANDIDATE_PLANE not in allowed and NORMALIZED_PLANE not in allowed
    ):
        event_log.halt(
            "scaffold_conflicting_evidence_guard_hard_negative_candidate_only_without_candidate_or_normalized_plane",
            fixture_id=fixture_id,
        )
        raise HardNegativeCandidateOnlyWithoutCandidateOrNormalizedPlane(
            "hard-negatives entry {0!r} declares near_match_classification "
            "candidate_only but allowed_planes contains neither the candidate "
            "plane nor the normalized plane".format(fixture_id)
        )


def _check_boundary_entry(entry, event_log):
    fixture_id = entry.get("fixture_id")
    disqualification = entry.get("expected_disqualification") or {}
    if not isinstance(disqualification, dict):
        disqualification = {}

    if (
        disqualification.get("is_forbidden_output") is True
        and disqualification.get("is_valid_output") is True
    ):
        event_log.halt(
            "scaffold_conflicting_evidence_guard_boundary_violation_both_valid_and_forbidden",
            fixture_id=fixture_id,
        )
        raise BoundaryViolationBothValidAndForbidden(
            "boundary-violations entry {0!r} declares both "
            "is_forbidden_output and is_valid_output as True".format(fixture_id)
        )

    markers = entry.get("plane_separation_markers") or {}
    if not isinstance(markers, dict):
        markers = {}
    violation_plane = markers.get("violation_plane_in_observed_output")
    collapse = markers.get("forbidden_plane_collapse")

    if violation_plane == OFFICIAL_PLANE and not (
        isinstance(collapse, str) and collapse
    ):
        event_log.halt(
            "scaffold_conflicting_evidence_guard_boundary_violation_official_plane_without_collapse",
            fixture_id=fixture_id,
        )
        raise BoundaryViolationOfficialPlaneWithoutCollapse(
            "boundary-violations entry {0!r} declares violation_plane_in_observed_output "
            "as official_route_results but does not declare a non-empty "
            "forbidden_plane_collapse".format(fixture_id)
        )

    if disqualification.get("expected_halt") is True:
        halt_classification = disqualification.get("halt_classification")
        if not (isinstance(halt_classification, str) and halt_classification):
            event_log.halt(
                "scaffold_conflicting_evidence_guard_boundary_violation_expected_halt_without_classification",
                fixture_id=fixture_id,
            )
            raise BoundaryViolationExpectedHaltWithoutClassification(
                "boundary-violations entry {0!r} declares "
                "expected_disqualification.expected_halt True but does not "
                "declare a non-empty halt_classification string".format(fixture_id)
            )


def _check_entry(class_name, entry, event_log):
    if class_name == "golden-intents":
        _check_golden_entry(entry, event_log)
    elif class_name == "hard-negatives":
        _check_hard_negative_entry(entry, event_log)
    else:
        _check_boundary_entry(entry, event_log)


def run_scaffold_conflicting_evidence_guard(payloads_by_class, event_log):
    """Run the scaffold conflicting-evidence guard and return a fresh dict.

    Raises a declared exception on the first conflict observed; on clean
    pass returns a dict with exactly the nine allowed keys in
    `ALLOWED_OUTPUT_KEYS`.
    """
    _validate_payloads(payloads_by_class, event_log)
    _assert_no_forbidden_language(payloads_by_class, event_log)

    inspected_class_counts = {}
    inspected_entry_count = 0
    for class_name in REQUIRED_PAYLOAD_CLASSES:
        inspected_class_counts[class_name] = 0

    event_log.append(
        "scaffold_conflicting_evidence_guard_started",
        declared_conflict_kinds_checked=list(DECLARED_CONFLICT_KINDS),
    )

    for class_name in REQUIRED_PAYLOAD_CLASSES:
        for entry in payloads_by_class[class_name]["entries"]:
            _check_entry(class_name, entry, event_log)
            inspected_class_counts[class_name] += 1
            inspected_entry_count += 1
            event_log.append(
                "scaffold_conflicting_evidence_guard_entry_inspected",
                class_name=class_name,
                fixture_id=entry.get("fixture_id"),
            )

    output = {
        "guard_kind": "scaffold_conflicting_evidence_guard",
        "inspected_entry_count": inspected_entry_count,
        "inspected_class_counts": dict(inspected_class_counts),
        "declared_conflict_kinds_checked": list(DECLARED_CONFLICT_KINDS),
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "guard_note": (
            "Scaffold conflicting-evidence guard over admitted synthetic "
            "payloads; checks the five declared conflict kinds only; "
            "passing this guard is not a claim that the inspected entries "
            "are conflict-free; no real retrieval, no benchmark execution, "
            "and no measurement authorization."
        ),
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_conflicting_evidence_guard_run_ended",
        inspected_entry_count=inspected_entry_count,
        inspected_class_counts=dict(inspected_class_counts),
        declared_conflict_kinds_checked=list(DECLARED_CONFLICT_KINDS),
    )
    return output
