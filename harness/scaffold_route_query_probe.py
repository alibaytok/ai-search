"""Scaffold route-query probe over admitted synthetic payloads.

This module is a narrow follow-up to the WO-47 / WO-48 scaffold index
probe. It builds a temporary in-memory query map from already-loaded
synthetic fixture entries and observes how route-first boundaries behave
when a caller submits synthetic query specs.

It does not read files, write files, invoke an adapter, collect metrics,
rank, or choose any architecture / vendor / library / index family / ANN
backend / neural re-scorer / retrieval family / production system.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_index_probe import (
    CANDIDATE_PLANE,
    NORMALIZED_PLANE,
    OFFICIAL_PLANE,
    REQUIRED_PAYLOAD_CLASSES,
)


PROBE_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_OUTPUT_KEYS = (
    "probe_kind",
    "indexed_entry_count",
    "queries_observed_count",
    "official_observation_count",
    "candidate_observation_count",
    "normalized_observation_count",
    "miss_observation_count",
    "contract_failure_observation_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "probe_note",
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


class NonListQueries(Exception):
    """Raised when query specs are not a non-empty list."""


class NonObjectQuery(Exception):
    """Raised when an individual query spec is not a dict."""


class MissingQueryField(Exception):
    """Raised when a query spec is missing a required string field."""


class DuplicateQueryId(Exception):
    """Raised when query specs repeat a query_id."""


class DuplicateSyntheticIntentText(Exception):
    """Raised when two indexed entries share one synthetic intent text."""


class HardNegativeForbiddenOfficialReturn(Exception):
    """Raised when a hard-negative query would land on the official plane."""


class BoundaryViolationTreatedAsSuccess(Exception):
    """Raised when a boundary-violation query is marked as a valid output."""


class ForbiddenLanguageInRouteQueryProbe(Exception):
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
    for phrase in PROBE_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_route_query_probe_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInRouteQueryProbe(
                "Forbidden phrase {0!r} found in route-query probe surface".format(
                    offending
                )
            )


def _validate_payloads(payloads_by_class, event_log):
    if not isinstance(payloads_by_class, dict):
        event_log.halt(
            "scaffold_route_query_probe_non_object_input",
            payloads_by_class_type=type(payloads_by_class).__name__,
        )
        raise NonObjectPayloadsByClass("payloads_by_class must be a dict")

    for class_name in REQUIRED_PAYLOAD_CLASSES:
        if class_name not in payloads_by_class:
            event_log.halt(
                "scaffold_route_query_probe_missing_required_class",
                class_name=class_name,
            )
            raise MissingRequiredPayloadClass(
                "payloads_by_class is missing {0!r}".format(class_name)
            )
        payload = payloads_by_class[class_name]
        if not isinstance(payload, dict):
            event_log.halt(
                "scaffold_route_query_probe_non_object_payload",
                class_name=class_name,
                payload_type=type(payload).__name__,
            )
            raise NonObjectPayload(
                "payload for class {0!r} must be a dict".format(class_name)
            )
        if payload.get("fixture_class") != class_name:
            event_log.halt(
                "scaffold_route_query_probe_class_mismatch",
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
                "scaffold_route_query_probe_missing_or_non_list_entries",
                class_name=class_name,
            )
            raise MissingOrNonListEntries(
                "payload for class {0!r} has missing or non-list entries".format(
                    class_name
                )
            )


def _validate_queries(queries, event_log):
    if not isinstance(queries, list) or not queries:
        event_log.halt(
            "scaffold_route_query_probe_non_list_queries",
            queries_type=type(queries).__name__,
        )
        raise NonListQueries("queries must be a non-empty list")

    seen_query_ids = set()
    for query in queries:
        if not isinstance(query, dict):
            event_log.halt(
                "scaffold_route_query_probe_non_object_query",
                query_type=type(query).__name__,
            )
            raise NonObjectQuery("each query must be a dict")
        for field in ("query_id", "synthetic_intent_text"):
            if not isinstance(query.get(field), str) or not query.get(field):
                event_log.halt(
                    "scaffold_route_query_probe_missing_query_field",
                    field=field,
                )
                raise MissingQueryField(
                    "query field {0!r} must be a non-empty string".format(field)
                )
        query_id = query["query_id"]
        if query_id in seen_query_ids:
            event_log.halt(
                "scaffold_route_query_probe_duplicate_query_id",
                query_id=query_id,
            )
            raise DuplicateQueryId(
                "query_id {0!r} appears more than once".format(query_id)
            )
        seen_query_ids.add(query_id)


def _entry_intent_text(entry):
    surface = entry.get("intent_surface") or {}
    if not isinstance(surface, dict):
        return None
    return surface.get("synthetic_intent_text")


def _build_query_index(payloads_by_class, event_log):
    index = {}
    for class_name in REQUIRED_PAYLOAD_CLASSES:
        for entry in payloads_by_class[class_name]["entries"]:
            text = _entry_intent_text(entry)
            if not isinstance(text, str) or not text:
                continue
            if text in index:
                first_class, first_entry = index[text]
                event_log.halt(
                    "scaffold_route_query_probe_duplicate_intent_text",
                    first_fixture_id=first_entry.get("fixture_id"),
                    first_class=first_class,
                    second_fixture_id=entry.get("fixture_id"),
                    second_class=class_name,
                )
                raise DuplicateSyntheticIntentText(
                    "synthetic intent text maps to more than one fixture entry"
                )
            index[text] = (class_name, entry)
    return index


def _observe_golden_entry(entry):
    if entry.get("expected_outcome_class") == "official_route_expected":
        ref = entry.get("expected_official_route_reference") or {}
        return "official", {
            "plane": OFFICIAL_PLANE,
            "fixture_id": entry.get("fixture_id"),
            "synthetic_route_identifier": ref.get("synthetic_route_identifier"),
            "is_promotion_trigger": False,
        }
    return "miss", {
        "plane": OFFICIAL_PLANE,
        "fixture_id": entry.get("fixture_id"),
        "plane_is_empty_for_this_entry": True,
        "miss_classification": entry.get("miss_classification"),
    }


def _observe_hard_negative_entry(entry, event_log):
    markers = entry.get("plane_separation_markers") or {}
    allowed_planes = markers.get("allowed_planes") or []
    if not isinstance(allowed_planes, list):
        allowed_planes = []

    if OFFICIAL_PLANE in allowed_planes:
        event_log.halt(
            "scaffold_route_query_probe_hard_negative_forbidden_official",
            fixture_id=entry.get("fixture_id"),
        )
        raise HardNegativeForbiddenOfficialReturn(
            "hard-negative fixture cannot observe the official plane"
        )
    if entry.get("must_not_authorize_official_return") is False:
        event_log.halt(
            "scaffold_route_query_probe_hard_negative_forbidden_official",
            fixture_id=entry.get("fixture_id"),
            reason_detail="must_not_authorize_official_return_false",
        )
        raise HardNegativeForbiddenOfficialReturn(
            "hard-negative fixture relaxed the official-plane guard"
        )

    if CANDIDATE_PLANE in allowed_planes:
        kind = "candidate"
        plane = CANDIDATE_PLANE
    elif NORMALIZED_PLANE in allowed_planes:
        kind = "normalized"
        plane = NORMALIZED_PLANE
    else:
        kind = "candidate"
        plane = CANDIDATE_PLANE

    return kind, {
        "plane": plane,
        "fixture_id": entry.get("fixture_id"),
        "near_match_classification": entry.get("near_match_classification"),
        "allowed_planes": list(allowed_planes),
        "must_not_authorize_official_return": True,
    }


def _observe_boundary_entry(entry, event_log):
    expected = entry.get("expected_disqualification") or {}
    if not isinstance(expected, dict):
        expected = {}
    if (
        expected.get("expected_halt") is not True
        or expected.get("is_forbidden_output") is not True
        or expected.get("is_valid_output") is True
    ):
        event_log.halt(
            "scaffold_route_query_probe_boundary_violation_treated_as_success",
            fixture_id=entry.get("fixture_id"),
        )
        raise BoundaryViolationTreatedAsSuccess(
            "boundary-violation fixture is not a valid route observation"
        )

    markers = entry.get("plane_separation_markers") or {}
    return "contract_failure", {
        "fixture_id": entry.get("fixture_id"),
        "target_contract_assertion": entry.get("target_contract_assertion"),
        "violation_plane_in_observed_output": markers.get(
            "violation_plane_in_observed_output"
        ),
        "forbidden_plane_collapse": markers.get("forbidden_plane_collapse"),
        "halt_classification": expected.get("halt_classification"),
        "is_forbidden_output": True,
        "is_valid_output": False,
    }


def _observe_matched_entry(class_name, entry, event_log):
    if class_name == "golden-intents":
        return _observe_golden_entry(entry)
    if class_name == "hard-negatives":
        return _observe_hard_negative_entry(entry, event_log)
    return _observe_boundary_entry(entry, event_log)


def run_scaffold_route_query_probe(payloads_by_class, queries, event_log):
    """Run the scaffold route-query probe and return a fresh result dict."""
    _validate_payloads(payloads_by_class, event_log)
    _validate_queries(queries, event_log)
    _assert_no_forbidden_language(payloads_by_class, event_log)
    _assert_no_forbidden_language(queries, event_log)

    index = _build_query_index(payloads_by_class, event_log)
    event_log.append(
        "scaffold_route_query_probe_started",
        indexed_entry_count=len(index),
        queries_observed_count=len(queries),
    )

    official_count = 0
    candidate_count = 0
    normalized_count = 0
    miss_count = 0
    contract_failure_count = 0

    for query in queries:
        query_id = query["query_id"]
        text = query["synthetic_intent_text"]
        match = index.get(text)
        if match is None:
            kind = "miss"
            class_name = None
            fixture_id = None
            observation = {
                "matched": False,
                "plane": OFFICIAL_PLANE,
                "plane_is_empty_for_this_query": True,
            }
        else:
            class_name, entry = match
            fixture_id = entry.get("fixture_id")
            kind, observation = _observe_matched_entry(class_name, entry, event_log)

        if kind == "official":
            official_count += 1
            event_type = "scaffold_route_query_probe_official_observation"
        elif kind == "candidate":
            candidate_count += 1
            event_type = "scaffold_route_query_probe_candidate_observation"
        elif kind == "normalized":
            normalized_count += 1
            event_type = "scaffold_route_query_probe_normalized_observation"
        elif kind == "contract_failure":
            contract_failure_count += 1
            event_type = "scaffold_route_query_probe_contract_failure_observation"
        else:
            miss_count += 1
            event_type = "scaffold_route_query_probe_miss_observation"

        event_log.append(
            event_type,
            query_id=query_id,
            class_name=class_name,
            fixture_id=fixture_id,
            observation=observation,
        )

    output = {
        "probe_kind": "scaffold_route_query_probe",
        "indexed_entry_count": len(index),
        "queries_observed_count": len(queries),
        "official_observation_count": official_count,
        "candidate_observation_count": candidate_count,
        "normalized_observation_count": normalized_count,
        "miss_observation_count": miss_count,
        "contract_failure_observation_count": contract_failure_count,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "probe_note": (
            "Scaffold route-query observation over admitted synthetic "
            "payloads; no real retrieval, no benchmark execution, and "
            "no measurement authorization."
        ),
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_route_query_probe_run_ended",
        indexed_entry_count=len(index),
        queries_observed_count=len(queries),
        official_observation_count=official_count,
        candidate_observation_count=candidate_count,
        normalized_observation_count=normalized_count,
        miss_observation_count=miss_count,
        contract_failure_observation_count=contract_failure_count,
    )
    return output
