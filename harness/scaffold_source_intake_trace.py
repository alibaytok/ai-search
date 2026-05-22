"""Scaffold read-only source-intake and prompt-to-route trace.

WO-54 adds a scaffold-level module that traces a captured user prompt
(a non-empty string) through external source records into candidate
route and workflow fragments while preserving the route-first
invariants. The trace is read-only: it observes already-loaded source
records and emits events that narrate the layered preconditions
(qualification before extracted_material / normalized_material /
candidate_fragments; extracted_material before normalized_material;
normalized_material before candidate_fragments). It does NOT return
any route, does NOT select an official route, does NOT treat raw
prompts / skills / agent or tool descriptions / documents / internet
content as routes, and does NOT compute any similarity / score /
rank / metric.

The module performs no file read, no file write, and no network
call. It uses only Python standard library plus harness-internal
forbidden-language constants.

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 explicit
non-claim constraint carries forward: this module does not claim
that any trace, layer, marker, admission surface, fragment kind, or
in-memory observation is sufficient, necessary, superior, best,
complete, production-ready, recommended, or selected.

Public surface:

    run_scaffold_source_intake_trace(
        input_prompt, source_records, event_log
    ) -> dict

Inputs:

- `input_prompt`: a non-empty string. The prompt is captured intent
  input; it is not a route. The trace records its observation
  structurally (length and presence) and does NOT echo its text into
  the output dict.
- `source_records`: a list (possibly empty) of already-loaded source
  dicts. Each source record carries `source_id`, `source_kind`,
  `source_origin`, and may carry `qualified`, `qualification_ref`,
  `extracted_material`, `normalized_material`, and
  `candidate_fragments` per the WO-54 packet's example. Source text
  is never copied into the output dict's route or workflow fragment
  fields.
- `event_log`: harness `EventLog`.

The clean-pass result dict has exactly fifteen allowed keys in
`ALLOWED_OUTPUT_KEYS`. The four authorization / readiness /
selection booleans are literal False on every emitted path.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


TRACE_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_OUTPUT_KEYS = (
    "trace_kind",
    "input_prompt_observed",
    "normalized_intent_observation",
    "sources_touched_count",
    "qualified_sources_count",
    "normalized_material_refs",
    "candidate_route_fragments",
    "candidate_workflow_fragments",
    "rejected_source_count",
    "rejection_reasons",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "trace_note",
)

ALLOWED_SOURCE_ORIGIN = "external"

ALLOWED_FRAGMENT_KINDS = frozenset((
    "candidate_route_fragment",
    "candidate_workflow",
))

ROUTE_STATUS_CLAIM_BOOLEAN_KEYS = (
    "official",
    "is_route",
    "is_official_route",
    "selected_as_official",
    "official_route_authorized",
    "route_authorized",
    "production_route",
    "selected_route",
    "executable",
)

OFFICIAL_ROUTE_STATE_VALUE = "official"

OFFICIAL_ROUTE_PLANE_VALUE = "official_route_results"


class NonStringInputPrompt(Exception):
    """Raised when `input_prompt` is not a string."""


class EmptyInputPrompt(Exception):
    """Raised when `input_prompt` is the empty string."""


class NonListSourceRecords(Exception):
    """Raised when `source_records` is not a list."""


class NonObjectSourceRecord(Exception):
    """Raised when an entry of `source_records` is not a dict."""


class MissingSourceId(Exception):
    """Raised when a source record is missing a non-empty string `source_id`."""


class MissingSourceField(Exception):
    """Raised when a source record is missing a non-`source_id` required field."""


class SourceOriginNotExternal(Exception):
    """Raised when a source record's `source_origin` is not `external`."""


class DuplicateSourceId(Exception):
    """Raised when two source records share one `source_id`."""


class QualificationGate(Exception):
    """Raised when a source record carries `extracted_material`,
    `normalized_material`, or `candidate_fragments` without declaring
    `qualified: True`."""


class MissingQualificationRef(Exception):
    """Raised when a qualified source is missing a non-empty
    `qualification_ref` string."""


class SourceClaimsRouteStatus(Exception):
    """Raised when a source record declares a forbidden route-status marker."""


class ExtractedMaterialClaimsRouteStatus(Exception):
    """Raised when `extracted_material` declares a forbidden route-status
    marker."""


class NormalizationWithoutExtraction(Exception):
    """Raised when `normalized_material` is present without `extracted_material`."""


class NormalizationClaimsRouteStatus(Exception):
    """Raised when `normalized_material` declares a forbidden route-status
    marker."""


class CandidateFragmentsWithoutNormalization(Exception):
    """Raised when `candidate_fragments` is present without `normalized_material`."""


class NonObjectCandidateFragment(Exception):
    """Raised when a candidate fragment is not a dict."""


class MissingFragmentField(Exception):
    """Raised when a candidate fragment is missing a required non-empty
    string field."""


class CandidateFragmentNotCandidateOnly(Exception):
    """Raised when a candidate fragment does not declare `candidate_only: True`."""


class CandidateFragmentForbiddenKind(Exception):
    """Raised when a candidate fragment's `fragment_kind` is not in
    `ALLOWED_FRAGMENT_KINDS`."""


class CandidateFragmentDerivationMismatch(Exception):
    """Raised when a candidate fragment's `derived_from_normalized_id` does
    not match the source record's `normalized_material.normalized_id`."""


class CandidateFragmentClaimsRouteStatus(Exception):
    """Raised when a candidate fragment declares a forbidden route-status
    marker."""


class ForbiddenLanguageInSourceIntakeTrace(Exception):
    """Raised when forbidden language appears on a surfaced output value."""


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
    for phrase in TRACE_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_source_intake_trace_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInSourceIntakeTrace(
                "Forbidden phrase {0!r} found in source-intake trace "
                "output".format(offending)
            )


def _route_status_claim_in_layer(layer):
    """Return a (kind, value) pair describing the first route-status claim
    observed in `layer`, or None if no claim is present.

    Claims are: any key in `ROUTE_STATUS_CLAIM_BOOLEAN_KEYS` set to True;
    `route_state == "official"`; or `plane == "official_route_results"`.
    """
    if not isinstance(layer, dict):
        return None
    for key in ROUTE_STATUS_CLAIM_BOOLEAN_KEYS:
        if layer.get(key) is True:
            return ("boolean_marker", key)
    if layer.get("route_state") == OFFICIAL_ROUTE_STATE_VALUE:
        return ("route_state_value", OFFICIAL_ROUTE_STATE_VALUE)
    if layer.get("plane") == OFFICIAL_ROUTE_PLANE_VALUE:
        return ("plane_value", OFFICIAL_ROUTE_PLANE_VALUE)
    return None


def _validate_input_prompt(input_prompt, event_log):
    if not isinstance(input_prompt, str):
        event_log.halt(
            "scaffold_source_intake_trace_non_string_input_prompt",
            input_prompt_type=type(input_prompt).__name__,
        )
        raise NonStringInputPrompt("input_prompt must be a string")
    if not input_prompt:
        event_log.halt(
            "scaffold_source_intake_trace_empty_input_prompt",
        )
        raise EmptyInputPrompt("input_prompt must be a non-empty string")


def _validate_source_record_shape(source, event_log):
    if not isinstance(source, dict):
        event_log.halt(
            "scaffold_source_intake_trace_non_object_source_record",
            source_type=type(source).__name__,
        )
        raise NonObjectSourceRecord("each source record must be a dict")
    source_id = source.get("source_id")
    if not isinstance(source_id, str) or not source_id:
        event_log.halt(
            "scaffold_source_intake_trace_missing_source_id",
        )
        raise MissingSourceId(
            "source record `source_id` must be a non-empty string"
        )
    for field in ("source_kind", "source_origin"):
        value = source.get(field)
        if not isinstance(value, str) or not value:
            event_log.halt(
                "scaffold_source_intake_trace_missing_source_field",
                source_id=source_id,
                field=field,
            )
            raise MissingSourceField(
                "source record {0!r} field {1!r} must be a non-empty "
                "string".format(source_id, field)
            )
    if source["source_origin"] != ALLOWED_SOURCE_ORIGIN:
        event_log.halt(
            "scaffold_source_intake_trace_source_origin_not_external",
            source_id=source_id,
            source_origin=source["source_origin"],
        )
        raise SourceOriginNotExternal(
            "source record {0!r} declares source_origin {1!r}; only "
            "{2!r} is admitted".format(
                source_id, source["source_origin"], ALLOWED_SOURCE_ORIGIN
            )
        )
    claim = _route_status_claim_in_layer(source)
    if claim is not None:
        event_log.halt(
            "scaffold_source_intake_trace_source_claims_route_status",
            source_id=source_id,
            claim_kind=claim[0],
            claim_value=claim[1],
        )
        raise SourceClaimsRouteStatus(
            "source record {0!r} declares forbidden route-status "
            "claim {1!r}={2!r}".format(source_id, claim[0], claim[1])
        )


def _enforce_qualification_gate(source, event_log):
    """Enforce required rejection case 4 and the qualification_ref check.

    Returns True if the source is qualified with a non-empty
    `qualification_ref`. Returns False if the source has no derived
    material and is not qualified (an admitted bare source). Raises
    otherwise.
    """
    source_id = source["source_id"]
    has_derived = (
        "extracted_material" in source
        or "normalized_material" in source
        or bool(source.get("candidate_fragments"))
    )
    qualified = source.get("qualified") is True
    qualification_ref = source.get("qualification_ref")
    qualification_ref_ok = (
        isinstance(qualification_ref, str) and qualification_ref
    )

    if not qualified:
        if has_derived:
            event_log.halt(
                "scaffold_source_intake_trace_qualification_gate",
                source_id=source_id,
            )
            raise QualificationGate(
                "source record {0!r} carries derived material without "
                "declaring qualified True".format(source_id)
            )
        return False

    if not qualification_ref_ok:
        event_log.halt(
            "scaffold_source_intake_trace_missing_qualification_ref",
            source_id=source_id,
        )
        raise MissingQualificationRef(
            "source record {0!r} declares qualified True but is missing "
            "a non-empty qualification_ref".format(source_id)
        )

    return True


def _observe_extraction(source, event_log):
    extracted = source.get("extracted_material")
    if extracted is None:
        return None
    claim = _route_status_claim_in_layer(extracted)
    if claim is not None:
        event_log.halt(
            "scaffold_source_intake_trace_extracted_material_claims_route_status",
            source_id=source["source_id"],
            claim_kind=claim[0],
            claim_value=claim[1],
        )
        raise ExtractedMaterialClaimsRouteStatus(
            "source record {0!r} extracted_material declares forbidden "
            "route-status claim {1!r}={2!r}".format(
                source["source_id"], claim[0], claim[1]
            )
        )
    return extracted


def _observe_normalization(source, extracted, event_log):
    normalized = source.get("normalized_material")
    if normalized is None:
        return None
    if extracted is None:
        event_log.halt(
            "scaffold_source_intake_trace_normalization_without_extraction",
            source_id=source["source_id"],
        )
        raise NormalizationWithoutExtraction(
            "source record {0!r} carries normalized_material without "
            "extracted_material".format(source["source_id"])
        )
    claim = _route_status_claim_in_layer(normalized)
    if claim is not None:
        event_log.halt(
            "scaffold_source_intake_trace_normalization_claims_route_status",
            source_id=source["source_id"],
            claim_kind=claim[0],
            claim_value=claim[1],
        )
        raise NormalizationClaimsRouteStatus(
            "source record {0!r} normalized_material declares forbidden "
            "route-status claim {1!r}={2!r}".format(
                source["source_id"], claim[0], claim[1]
            )
        )
    return normalized


def _observe_candidate_fragments(source, normalized, event_log):
    fragments = source.get("candidate_fragments")
    if not fragments:
        return []
    if not isinstance(fragments, list):
        event_log.halt(
            "scaffold_source_intake_trace_non_object_candidate_fragment",
            source_id=source["source_id"],
            fragments_type=type(fragments).__name__,
        )
        raise NonObjectCandidateFragment(
            "source record {0!r} candidate_fragments must be a list".format(
                source["source_id"]
            )
        )
    if normalized is None:
        event_log.halt(
            "scaffold_source_intake_trace_candidate_fragments_without_normalization",
            source_id=source["source_id"],
        )
        raise CandidateFragmentsWithoutNormalization(
            "source record {0!r} carries candidate_fragments without "
            "normalized_material".format(source["source_id"])
        )

    normalized_id = normalized.get("normalized_id")
    observed = []
    for fragment in fragments:
        if not isinstance(fragment, dict):
            event_log.halt(
                "scaffold_source_intake_trace_non_object_candidate_fragment",
                source_id=source["source_id"],
                fragment_type=type(fragment).__name__,
            )
            raise NonObjectCandidateFragment(
                "candidate fragment in source {0!r} must be a dict".format(
                    source["source_id"]
                )
            )
        for field in ("fragment_id", "fragment_kind", "derived_from_normalized_id"):
            value = fragment.get(field)
            if not isinstance(value, str) or not value:
                event_log.halt(
                    "scaffold_source_intake_trace_missing_fragment_field",
                    source_id=source["source_id"],
                    field=field,
                )
                raise MissingFragmentField(
                    "candidate fragment in source {0!r} missing field "
                    "{1!r}".format(source["source_id"], field)
                )
        if fragment.get("candidate_only") is not True:
            event_log.halt(
                "scaffold_source_intake_trace_fragment_not_candidate_only",
                source_id=source["source_id"],
                fragment_id=fragment["fragment_id"],
            )
            raise CandidateFragmentNotCandidateOnly(
                "candidate fragment {0!r} in source {1!r} does not "
                "declare candidate_only True".format(
                    fragment["fragment_id"], source["source_id"]
                )
            )
        if fragment["fragment_kind"] not in ALLOWED_FRAGMENT_KINDS:
            event_log.halt(
                "scaffold_source_intake_trace_fragment_forbidden_kind",
                source_id=source["source_id"],
                fragment_id=fragment["fragment_id"],
                fragment_kind=fragment["fragment_kind"],
            )
            raise CandidateFragmentForbiddenKind(
                "candidate fragment {0!r} in source {1!r} declares "
                "fragment_kind {2!r} outside "
                "ALLOWED_FRAGMENT_KINDS".format(
                    fragment["fragment_id"],
                    source["source_id"],
                    fragment["fragment_kind"],
                )
            )
        if fragment["derived_from_normalized_id"] != normalized_id:
            event_log.halt(
                "scaffold_source_intake_trace_fragment_derivation_mismatch",
                source_id=source["source_id"],
                fragment_id=fragment["fragment_id"],
                expected_normalized_id=normalized_id,
                declared_normalized_id=fragment["derived_from_normalized_id"],
            )
            raise CandidateFragmentDerivationMismatch(
                "candidate fragment {0!r} derived_from_normalized_id "
                "{1!r} does not match source normalized_id {2!r}".format(
                    fragment["fragment_id"],
                    fragment["derived_from_normalized_id"],
                    normalized_id,
                )
            )
        claim = _route_status_claim_in_layer(fragment)
        if claim is not None:
            event_log.halt(
                "scaffold_source_intake_trace_fragment_claims_route_status",
                source_id=source["source_id"],
                fragment_id=fragment["fragment_id"],
                claim_kind=claim[0],
                claim_value=claim[1],
            )
            raise CandidateFragmentClaimsRouteStatus(
                "candidate fragment {0!r} declares forbidden route-status "
                "claim {1!r}={2!r}".format(
                    fragment["fragment_id"], claim[0], claim[1]
                )
            )
        observed.append(fragment)
    return observed


def run_scaffold_source_intake_trace(input_prompt, source_records, event_log):
    """Run the scaffold source-intake trace and return a fresh dict.

    Raises a declared exception on the first rejection observed; on
    clean pass returns a dict with exactly the fifteen allowed keys in
    `ALLOWED_OUTPUT_KEYS`.
    """
    _validate_input_prompt(input_prompt, event_log)

    if not isinstance(source_records, list):
        event_log.halt(
            "scaffold_source_intake_trace_non_list_source_records",
            source_records_type=type(source_records).__name__,
        )
        raise NonListSourceRecords("source_records must be a list")

    event_log.append(
        "scaffold_source_intake_trace_started",
        input_prompt_length=len(input_prompt),
        source_records_count=len(source_records),
    )

    qualified_sources_count = 0
    normalized_material_refs = []
    candidate_route_fragments = []
    candidate_workflow_fragments = []
    seen_source_ids = set()
    sources_with_normalized_material = 0

    for source in source_records:
        _validate_source_record_shape(source, event_log)
        source_id = source["source_id"]
        if source_id in seen_source_ids:
            event_log.halt(
                "scaffold_source_intake_trace_duplicate_source_id",
                source_id=source_id,
            )
            raise DuplicateSourceId(
                "source_id {0!r} appears more than once".format(source_id)
            )
        seen_source_ids.add(source_id)

        qualified = _enforce_qualification_gate(source, event_log)
        event_log.append(
            "scaffold_source_intake_source_observed",
            source_id=source_id,
            source_kind=source["source_kind"],
            qualified=qualified,
        )
        if qualified:
            qualified_sources_count += 1

        extracted = _observe_extraction(source, event_log)
        normalized = _observe_normalization(source, extracted, event_log)
        if normalized is not None:
            sources_with_normalized_material += 1
            normalized_material_refs.append(
                {
                    "source_id": source_id,
                    "normalized_id": normalized.get("normalized_id"),
                }
            )
            event_log.append(
                "scaffold_source_intake_normalized_material_observed",
                source_id=source_id,
                normalized_id=normalized.get("normalized_id"),
            )

        observed_fragments = _observe_candidate_fragments(
            source, normalized, event_log
        )
        for fragment in observed_fragments:
            fragment_entry = {
                "source_id": source_id,
                "fragment_id": fragment["fragment_id"],
                "derived_from_normalized_id": fragment[
                    "derived_from_normalized_id"
                ],
            }
            if fragment["fragment_kind"] == "candidate_route_fragment":
                candidate_route_fragments.append(fragment_entry)
            else:
                candidate_workflow_fragments.append(fragment_entry)
            event_log.append(
                "scaffold_source_intake_candidate_fragment_observed",
                source_id=source_id,
                fragment_id=fragment["fragment_id"],
                fragment_kind=fragment["fragment_kind"],
                derived_from_normalized_id=fragment[
                    "derived_from_normalized_id"
                ],
            )

    output = {
        "trace_kind": "scaffold_source_intake_trace",
        "input_prompt_observed": {
            "observed": True,
            "captured_intent_text_length": len(input_prompt),
        },
        "normalized_intent_observation": {
            "prompt_length": len(input_prompt),
            "sources_with_normalized_material": sources_with_normalized_material,
        },
        "sources_touched_count": len(source_records),
        "qualified_sources_count": qualified_sources_count,
        "normalized_material_refs": list(normalized_material_refs),
        "candidate_route_fragments": list(candidate_route_fragments),
        "candidate_workflow_fragments": list(candidate_workflow_fragments),
        "rejected_source_count": 0,
        "rejection_reasons": [],
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "trace_note": (
            "Scaffold read-only source-intake trace from a captured "
            "prompt through external source records to candidate route "
            "and workflow fragments; preserves route-first invariants "
            "by never returning a route; no real adapter, no benchmark "
            "execution, and no measurement authorization."
        ),
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_source_intake_trace_passed",
        sources_touched_count=len(source_records),
        qualified_sources_count=qualified_sources_count,
        normalized_material_refs_count=len(normalized_material_refs),
        candidate_route_fragments_count=len(candidate_route_fragments),
        candidate_workflow_fragments_count=len(candidate_workflow_fragments),
    )
    return output
