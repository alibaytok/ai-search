"""Scaffold external-source acquisition boundary.

WO-60 adds a scaffold-only acquisition-boundary layer that describes
external source acquisition requests across three origin modes
without treating any acquired material as corpus, qualification
evidence, route object, search data, benchmark evidence, or
architecture-selection evidence.

This module does NOT implement real crawling, real downloading, web
fetching, GitHub fetching, browser automation, network calls, file
reads, file writes, content extraction, hash computation, or model
judgment. The three admitted origin modes are inert locators only:

- `url`: do NOT fetch.
- `local_path`: do NOT read.
- `pasted_text`: do NOT echo pasted text.

The module accepts already-loaded acquisition request dicts. Any
content already-known is represented only by its byte length and
hash prefix; raw text and raw locator content are never echoed
into the output's free-text fields.

The WO-47 through WO-59 explicit non-claim constraint carries
forward: this module does not claim that any acquisition reference,
origin mode, declared kind, or in-memory observation is sufficient,
necessary, superior, best, complete, production-ready, recommended,
or selected. The bounded admission surfaces are not claimed
exhaustive.

Public surface:

    run_scaffold_external_source_acquisition_boundary(
        acquisition_requests, event_log
    ) -> dict

The clean-pass output dict has exactly thirteen allowed keys in
`ALLOWED_OUTPUT_KEYS`. The four authorization / readiness /
selection booleans and the two admission/qualification counts are
literal False / literal 0 on every emitted path.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


ACQUISITION_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "acquisition_boundary_kind",
    "request_count",
    "origin_mode_counts",
    "acquisition_references",
    "content_available_count",
    "content_missing_count",
    "corpus_admitted_count",
    "qualified_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "acquisition_boundary_note",
)


ORIGIN_MODE_ORDER = ("url", "local_path", "pasted_text")


ALLOWED_ORIGIN_MODES = frozenset(ORIGIN_MODE_ORDER)


ALLOWED_DECLARED_KINDS = frozenset((
    "prompt_collection",
    "skill_collection",
    "agent_description_collection",
    "tool_description_collection",
    "document_collection",
))


REQUIRED_REQUEST_FIELDS = (
    "request_id",
    "origin_mode",
    "origin_locator",
    "declared_kind",
    "content_available",
    "content_byte_length",
    "content_hash",
    "observed_at",
)


_FORBIDDEN_REQUEST_FIELDS = frozenset((
    "qualified",
    "qualification_ref",
    "corpus_admitted",
    "source_card",
    "route_card",
    "authority",
    "trust",
    "freshness",
    "ownership",
    "validation_evidence",
    "qualification_evidence",
    "extracted_material",
    "normalized_material",
    "candidate_fragments",
    "candidate_route_fragments",
    "candidate_workflow_fragments",
    "route",
    "route_id",
    "route_state",
    "plane",
    "official",
    "executable",
    "selected_route",
    "production_route",
    "benchmark_fixture_class",
    "golden_intent",
    "hard_negative",
    "boundary_violation",
))


_HASH_PREFIX_LENGTH = 12


_ACQUISITION_BOUNDARY_NOTE = (
    "scaffold_external_source_acquisition_boundary: records inert "
    "acquisition references across url / local_path / pasted_text "
    "origin modes only; presence of a request is NOT corpus "
    "admission, NOT source qualification, NOT a route object, NOT "
    "content extraction, NOT prompt search, NOT skill search, NOT "
    "agent selection, NOT generic RAG input, NOT benchmark "
    "evidence, and NOT architecture-selection evidence; url is not "
    "fetched, local_path is not read, pasted_text is not echoed; "
    "hash is identity / integrity only; OQ-003, OQ-015, OQ-031, "
    "OQ-048, OQ-076 remain OPEN; no real adapter, no benchmark "
    "execution, and no measurement authorization."
)


class NonListAcquisitionRequests(Exception):
    """Raised when `acquisition_requests` is not a list."""


class NonObjectAcquisitionRequest(Exception):
    """Raised when an entry of `acquisition_requests` is not a dict."""


class MissingAcquisitionRequestField(Exception):
    """Raised when a request is missing a required field."""


class UnknownAcquisitionRequestField(Exception):
    """Raised when a request declares an unknown key."""


class DuplicateAcquisitionRequestId(Exception):
    """Raised when two requests share one `request_id`."""


class DuplicateAcquisitionOrigin(Exception):
    """Raised when two requests share one `(origin_mode, origin_locator)`."""


class InvalidOriginMode(Exception):
    """Raised when `origin_mode` is not in `ALLOWED_ORIGIN_MODES`."""


class InvalidDeclaredKind(Exception):
    """Raised when `declared_kind` is not in `ALLOWED_DECLARED_KINDS`."""


class InvalidContentAvailability(Exception):
    """Raised when `content_available` is not a literal boolean."""


class InvalidContentLength(Exception):
    """Raised when `content_byte_length` violates the content-availability
    contract."""


class InvalidContentHash(Exception):
    """Raised when `content_hash` violates the content-availability
    contract."""


class ForbiddenAcquisitionField(Exception):
    """Raised when a request declares a forbidden Source-Card-shaped,
    derived-material, route-shaped, or benchmark-fixture-shaped field."""


class ForbiddenLanguageInAcquisitionBoundary(Exception):
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
    for phrase in ACQUISITION_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_external_source_acquisition_boundary_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInAcquisitionBoundary(
                "Forbidden phrase {0!r} found in acquisition boundary "
                "output".format(offending)
            )


def _require_non_empty_string(value):
    return isinstance(value, str) and bool(value)


def _is_non_negative_int(value):
    if isinstance(value, bool):
        return False
    if not isinstance(value, int):
        return False
    return value >= 0


def _validate_required_fields(request, event_log):
    for field in REQUIRED_REQUEST_FIELDS:
        if field not in request:
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_missing_field",
                field=field,
            )
            raise MissingAcquisitionRequestField(
                "acquisition request is missing required field {0!r}".format(
                    field
                )
            )


def _reject_unknown_and_forbidden_keys(request, event_log):
    request_id = request.get("request_id")
    for key in request.keys():
        if key in REQUIRED_REQUEST_FIELDS:
            continue
        if key in _FORBIDDEN_REQUEST_FIELDS:
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_forbidden_field",
                request_id=request_id,
                field=key,
            )
            raise ForbiddenAcquisitionField(
                "acquisition request {0!r} declares forbidden field "
                "{1!r}".format(request_id, key)
            )
        event_log.halt(
            "scaffold_external_source_acquisition_boundary_unknown_field",
            request_id=request_id,
            field=key,
        )
        raise UnknownAcquisitionRequestField(
            "acquisition request {0!r} declares unknown key {1!r}".format(
                request_id, key
            )
        )


def _validate_string_fields(request, event_log):
    for field in ("request_id", "origin_mode", "origin_locator",
                  "declared_kind", "observed_at"):
        if not _require_non_empty_string(request.get(field)):
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_invalid_string_field",
                field=field,
            )
            raise MissingAcquisitionRequestField(
                "acquisition request field {0!r} must be a non-empty "
                "string".format(field)
            )


def _validate_origin_mode(request, event_log):
    request_id = request["request_id"]
    if request["origin_mode"] not in ALLOWED_ORIGIN_MODES:
        event_log.halt(
            "scaffold_external_source_acquisition_boundary_invalid_origin_mode",
            request_id=request_id,
            origin_mode=request["origin_mode"],
        )
        raise InvalidOriginMode(
            "acquisition request {0!r} declares origin_mode {1!r} outside "
            "ALLOWED_ORIGIN_MODES".format(request_id, request["origin_mode"])
        )


def _validate_declared_kind(request, event_log):
    request_id = request["request_id"]
    if request["declared_kind"] not in ALLOWED_DECLARED_KINDS:
        event_log.halt(
            "scaffold_external_source_acquisition_boundary_invalid_declared_kind",
            request_id=request_id,
            declared_kind=request["declared_kind"],
        )
        raise InvalidDeclaredKind(
            "acquisition request {0!r} declares declared_kind {1!r} outside "
            "ALLOWED_DECLARED_KINDS".format(request_id, request["declared_kind"])
        )


def _validate_content_availability(request, event_log):
    request_id = request["request_id"]
    content_available = request["content_available"]
    if not isinstance(content_available, bool):
        event_log.halt(
            "scaffold_external_source_acquisition_boundary_invalid_content_availability",
            request_id=request_id,
        )
        raise InvalidContentAvailability(
            "acquisition request {0!r} content_available must be a literal "
            "boolean".format(request_id)
        )
    byte_length = request["content_byte_length"]
    content_hash = request["content_hash"]

    if content_available is True:
        if not _is_non_negative_int(byte_length):
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_invalid_content_length",
                request_id=request_id,
            )
            raise InvalidContentLength(
                "acquisition request {0!r} content_byte_length must be a "
                "non-negative int (bools rejected) when content_available "
                "is True".format(request_id)
            )
        if not _require_non_empty_string(content_hash):
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_invalid_content_hash",
                request_id=request_id,
            )
            raise InvalidContentHash(
                "acquisition request {0!r} content_hash must be a "
                "non-empty string when content_available is True".format(
                    request_id
                )
            )
    else:
        if byte_length != 0:
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_invalid_content_length",
                request_id=request_id,
            )
            raise InvalidContentLength(
                "acquisition request {0!r} content_byte_length must be 0 "
                "when content_available is False".format(request_id)
            )
        if content_hash != "":
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_invalid_content_hash",
                request_id=request_id,
            )
            raise InvalidContentHash(
                "acquisition request {0!r} content_hash must be empty when "
                "content_available is False".format(request_id)
            )


def _build_reference(request):
    content_hash = request["content_hash"]
    hash_prefix = (
        content_hash[:_HASH_PREFIX_LENGTH] if content_hash else ""
    )
    return {
        "request_id": request["request_id"],
        "origin_mode": request["origin_mode"],
        "declared_kind": request["declared_kind"],
        "origin_locator_observed": True,
        "origin_locator_length": len(request["origin_locator"]),
        "content_available": request["content_available"],
        "content_byte_length": request["content_byte_length"],
        "content_hash_prefix": hash_prefix,
        "corpus_admitted": False,
        "qualified": False,
        "source_material_extracted": False,
        "route_object_created": False,
    }


def run_scaffold_external_source_acquisition_boundary(
    acquisition_requests, event_log
):
    """Inspect already-loaded acquisition requests and return a fresh
    fixed-shape acquisition-boundary observation dict.
    """
    if not isinstance(acquisition_requests, list):
        event_log.halt(
            "scaffold_external_source_acquisition_boundary_non_list_requests",
            acquisition_requests_type=type(acquisition_requests).__name__,
        )
        raise NonListAcquisitionRequests(
            "acquisition_requests must be a list"
        )

    event_log.append(
        "scaffold_external_source_acquisition_boundary_started",
        request_count=len(acquisition_requests),
    )

    references = []
    seen_request_ids = set()
    seen_origins = set()
    origin_mode_counts = {mode: 0 for mode in ORIGIN_MODE_ORDER}
    content_available_count = 0
    content_missing_count = 0

    for request in acquisition_requests:
        if not isinstance(request, dict):
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_non_object_request",
                request_type=type(request).__name__,
            )
            raise NonObjectAcquisitionRequest(
                "each acquisition request must be a dict"
            )
        _validate_required_fields(request, event_log)
        _reject_unknown_and_forbidden_keys(request, event_log)
        _validate_string_fields(request, event_log)
        _validate_origin_mode(request, event_log)
        _validate_declared_kind(request, event_log)
        _validate_content_availability(request, event_log)

        request_id = request["request_id"]
        if request_id in seen_request_ids:
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_duplicate_request_id",
                request_id=request_id,
            )
            raise DuplicateAcquisitionRequestId(
                "request_id {0!r} appears more than once".format(request_id)
            )
        seen_request_ids.add(request_id)

        origin_key = (request["origin_mode"], request["origin_locator"])
        if origin_key in seen_origins:
            event_log.halt(
                "scaffold_external_source_acquisition_boundary_duplicate_origin",
                request_id=request_id,
                origin_mode=request["origin_mode"],
            )
            raise DuplicateAcquisitionOrigin(
                "acquisition request {0!r} duplicates an earlier "
                "(origin_mode, origin_locator) pair".format(request_id)
            )
        seen_origins.add(origin_key)

        origin_mode_counts[request["origin_mode"]] += 1
        if request["content_available"]:
            content_available_count += 1
        else:
            content_missing_count += 1

        reference = _build_reference(request)
        references.append(reference)
        event_log.append(
            "scaffold_external_source_acquisition_request_observed",
            request_id=request_id,
            origin_mode=request["origin_mode"],
            declared_kind=request["declared_kind"],
            content_available=request["content_available"],
        )

    output = {
        "acquisition_boundary_kind": (
            "scaffold_external_source_acquisition_boundary"
        ),
        "request_count": len(acquisition_requests),
        "origin_mode_counts": dict(origin_mode_counts),
        "acquisition_references": list(references),
        "content_available_count": content_available_count,
        "content_missing_count": content_missing_count,
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "acquisition_boundary_note": _ACQUISITION_BOUNDARY_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_external_source_acquisition_boundary_passed",
        request_count=len(acquisition_requests),
        content_available_count=content_available_count,
        content_missing_count=content_missing_count,
        corpus_admitted_count=0,
        qualified_count=0,
    )
    return output
