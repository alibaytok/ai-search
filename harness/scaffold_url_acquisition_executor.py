"""Scaffold URL acquisition executor (injected fetcher, in-memory only).

WO-61 adds the first controlled online-source acquisition step after
the WO-60 acquisition-boundary layer. It accepts URL-only acquisition
request dicts (same WO-60 shape) plus a caller-supplied `fetch_url`
callable that returns already-loaded bytes plus structural metadata.
The module then assembles an in-memory acquired-source observation
without any extraction, normalization, candidate-fragment derivation,
indexing, retrieval, ranking, scoring, or architecture selection.

This module performs no direct IO and no model judgment. It does
not import any networking client, HTTP client, filesystem client,
shell client, or process-spawning client. The only IO boundary is
the injected `fetch_url` callable supplied by the caller (and
stubbed in tests). Browser automation, HTML parsing, markdown
parsing, recursive URL discovery, retry logic, and redirect
following are all out of scope. The static-scan tests in
`harness/tests/test_scaffold_url_acquisition_executor.py` enforce
absence of forbidden client tokens in the module source.

`hashlib` is imported by WO-61 for the narrow purpose of computing
a SHA-256 prefix over the already-returned `content_bytes`. Hash is
identity / integrity only; it does NOT qualify source, NOT admit
corpus, and NOT authorize extraction.

The WO-47 through WO-60 explicit non-claim constraint carries
forward: this module does not claim any acquired reference is
sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded admission surface is not
claimed exhaustive.

Public surface:

    run_scaffold_url_acquisition_executor(
        acquisition_requests, fetch_url, event_log
    ) -> dict

Two-pass design:
- Pass 1: validate every request. If any validation fails, halt
  before any fetcher call.
- Pass 2: for each validated request, invoke `fetch_url`,
  validate the fetcher result, compute the hash prefix, and
  assemble the acquired reference.

The clean-pass output dict has exactly thirteen allowed keys in
`ALLOWED_OUTPUT_KEYS`. The four standard authorization / readiness
/ selection booleans and the three admission/extraction counts are
literal False / literal 0 on every emitted path.
"""

import hashlib

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


URL_ACQUISITION_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "url_acquisition_kind",
    "request_count",
    "fetched_count",
    "acquired_references",
    "total_content_byte_length",
    "corpus_admitted_count",
    "qualified_count",
    "source_material_extracted_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "url_acquisition_note",
)


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


REQUIRED_FETCHER_RESULT_FIELDS = (
    "fetch_status",
    "content_bytes",
    "content_type",
    "fetched_at",
)


ALLOWED_DECLARED_KINDS = frozenset((
    "prompt_collection",
    "skill_collection",
    "agent_description_collection",
    "tool_description_collection",
    "document_collection",
))


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


MAX_FETCHED_BYTES = 65536

_HASH_PREFIX_LENGTH = 12

_EXPECTED_ORIGIN_MODE = "url"
_EXPECTED_FETCH_STATUS = "fetched"


_URL_ACQUISITION_NOTE = (
    "scaffold_url_acquisition_executor: records in-memory acquired "
    "source references from URL acquisition requests through an "
    "injected fetcher callable; presence of an acquired reference is "
    "NOT corpus admission, NOT source qualification, NOT a route "
    "object, NOT content extraction, NOT normalization, NOT prompt "
    "search, NOT skill search, NOT agent selection, NOT generic RAG "
    "input, NOT benchmark evidence, and NOT architecture-selection "
    "evidence; hash is identity / integrity only; OQ-003, OQ-015, "
    "OQ-031, OQ-048, OQ-076 remain OPEN; no real adapter, no "
    "benchmark execution, and no measurement authorization."
)


class NonListUrlAcquisitionRequests(Exception):
    """Raised when `acquisition_requests` is not a list."""


class NonObjectUrlAcquisitionRequest(Exception):
    """Raised when an entry of `acquisition_requests` is not a dict."""


class MissingUrlAcquisitionRequestField(Exception):
    """Raised when a request is missing a required field."""


class UnknownUrlAcquisitionRequestField(Exception):
    """Raised when a request declares an unknown key."""


class DuplicateUrlAcquisitionRequestId(Exception):
    """Raised when two requests share one `request_id`."""


class DuplicateUrlOriginLocator(Exception):
    """Raised when two requests share one `origin_locator`."""


class NonUrlOriginModeRejected(Exception):
    """Raised when `origin_mode` is not the literal string `"url"`."""


class InvalidUrlOriginLocator(Exception):
    """Raised when `origin_locator` is not a non-empty string."""


class InvalidDeclaredKind(Exception):
    """Raised when `declared_kind` is not in `ALLOWED_DECLARED_KINDS`."""


class InputContentAlreadyAvailableRejected(Exception):
    """Raised when an input request declares pre-acquired content
    metadata (`content_available != False` or non-zero byte length /
    non-empty hash on input)."""


class ForbiddenUrlAcquisitionField(Exception):
    """Raised when a request declares a forbidden Source-Card-shaped,
    derived-material, route-shaped, or benchmark-fixture-shaped field."""


class FetcherNotCallable(Exception):
    """Raised when `fetch_url` is not callable."""


class FetcherReturnedNonObject(Exception):
    """Raised when `fetch_url` returns something other than a dict."""


class MissingFetcherResultField(Exception):
    """Raised when the fetcher result dict is missing a required field."""


class UnknownFetcherResultField(Exception):
    """Raised when the fetcher result dict declares an unknown key."""


class InvalidFetchStatus(Exception):
    """Raised when `fetch_status` is not the literal string `"fetched"`."""


class InvalidFetchedContentBytes(Exception):
    """Raised when `content_bytes` is not non-empty bytes."""


class FetchedContentTooLarge(Exception):
    """Raised when fetched content exceeds `MAX_FETCHED_BYTES`."""


class InvalidFetchedContentType(Exception):
    """Raised when `content_type` is not a non-empty string."""


class InvalidFetchedAt(Exception):
    """Raised when `fetched_at` is not a non-empty string."""


class ForbiddenLanguageInUrlAcquisitionOutput(Exception):
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
    for phrase in URL_ACQUISITION_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_url_acquisition_executor_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInUrlAcquisitionOutput(
                "Forbidden phrase {0!r} found in URL acquisition output"
                .format(offending)
            )


def _require_non_empty_string(value):
    return isinstance(value, str) and bool(value)


def _is_non_negative_int(value):
    if isinstance(value, bool):
        return False
    if not isinstance(value, int):
        return False
    return value >= 0


def _validate_request_shape(request, event_log):
    if not isinstance(request, dict):
        event_log.halt(
            "scaffold_url_acquisition_executor_non_object_request",
            request_type=type(request).__name__,
        )
        raise NonObjectUrlAcquisitionRequest(
            "each acquisition request must be a dict"
        )

    for field in REQUIRED_REQUEST_FIELDS:
        if field not in request:
            event_log.halt(
                "scaffold_url_acquisition_executor_missing_field",
                field=field,
            )
            raise MissingUrlAcquisitionRequestField(
                "acquisition request is missing required field {0!r}".format(
                    field
                )
            )

    request_id = request.get("request_id")
    for key in request.keys():
        if key in REQUIRED_REQUEST_FIELDS:
            continue
        if key in _FORBIDDEN_REQUEST_FIELDS:
            event_log.halt(
                "scaffold_url_acquisition_executor_forbidden_field",
                request_id=request_id,
                field=key,
            )
            raise ForbiddenUrlAcquisitionField(
                "acquisition request {0!r} declares forbidden field "
                "{1!r}".format(request_id, key)
            )
        event_log.halt(
            "scaffold_url_acquisition_executor_unknown_field",
            request_id=request_id,
            field=key,
        )
        raise UnknownUrlAcquisitionRequestField(
            "acquisition request {0!r} declares unknown key {1!r}".format(
                request_id, key
            )
        )

    if not _require_non_empty_string(request_id):
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_request_id",
        )
        raise MissingUrlAcquisitionRequestField(
            "acquisition request `request_id` must be a non-empty string"
        )

    if request["origin_mode"] != _EXPECTED_ORIGIN_MODE:
        event_log.halt(
            "scaffold_url_acquisition_executor_non_url_origin_mode",
            request_id=request_id,
            origin_mode=request["origin_mode"],
        )
        raise NonUrlOriginModeRejected(
            "acquisition request {0!r} declares origin_mode {1!r}; "
            "only {2!r} is admitted by WO-61".format(
                request_id, request["origin_mode"], _EXPECTED_ORIGIN_MODE
            )
        )

    if not _require_non_empty_string(request.get("origin_locator")):
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_origin_locator",
            request_id=request_id,
        )
        raise InvalidUrlOriginLocator(
            "acquisition request {0!r} origin_locator must be a "
            "non-empty string".format(request_id)
        )

    if request.get("declared_kind") not in ALLOWED_DECLARED_KINDS:
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_declared_kind",
            request_id=request_id,
            declared_kind=request.get("declared_kind"),
        )
        raise InvalidDeclaredKind(
            "acquisition request {0!r} declares declared_kind {1!r} "
            "outside ALLOWED_DECLARED_KINDS".format(
                request_id, request.get("declared_kind")
            )
        )

    if (
        request["content_available"] is not False
        or request["content_byte_length"] != 0
        or request["content_hash"] != ""
    ):
        event_log.halt(
            "scaffold_url_acquisition_executor_input_content_already_available",
            request_id=request_id,
        )
        raise InputContentAlreadyAvailableRejected(
            "acquisition request {0!r} must declare content_available "
            "False, content_byte_length 0, and empty content_hash on "
            "input".format(request_id)
        )

    if not _require_non_empty_string(request.get("observed_at")):
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_observed_at",
            request_id=request_id,
        )
        raise MissingUrlAcquisitionRequestField(
            "acquisition request {0!r} observed_at must be a non-empty "
            "string".format(request_id)
        )


def _validate_all_requests(acquisition_requests, event_log):
    seen_request_ids = set()
    seen_origins = set()

    for request in acquisition_requests:
        _validate_request_shape(request, event_log)
        request_id = request["request_id"]
        if request_id in seen_request_ids:
            event_log.halt(
                "scaffold_url_acquisition_executor_duplicate_request_id",
                request_id=request_id,
            )
            raise DuplicateUrlAcquisitionRequestId(
                "request_id {0!r} appears more than once".format(request_id)
            )
        seen_request_ids.add(request_id)

        origin_locator = request["origin_locator"]
        if origin_locator in seen_origins:
            event_log.halt(
                "scaffold_url_acquisition_executor_duplicate_origin_locator",
                request_id=request_id,
            )
            raise DuplicateUrlOriginLocator(
                "origin_locator appears more than once for request {0!r}"
                .format(request_id)
            )
        seen_origins.add(origin_locator)

        event_log.append(
            "scaffold_url_acquisition_executor_request_validated",
            request_id=request_id,
            declared_kind=request["declared_kind"],
        )


def _validate_fetcher_result(result, request_id, event_log):
    if not isinstance(result, dict):
        event_log.halt(
            "scaffold_url_acquisition_executor_fetcher_returned_non_object",
            request_id=request_id,
            result_type=type(result).__name__,
        )
        raise FetcherReturnedNonObject(
            "fetcher must return a dict for request {0!r}".format(request_id)
        )

    for field in REQUIRED_FETCHER_RESULT_FIELDS:
        if field not in result:
            event_log.halt(
                "scaffold_url_acquisition_executor_missing_fetcher_field",
                request_id=request_id,
                field=field,
            )
            raise MissingFetcherResultField(
                "fetcher result for request {0!r} is missing field "
                "{1!r}".format(request_id, field)
            )

    for key in result.keys():
        if key not in REQUIRED_FETCHER_RESULT_FIELDS:
            event_log.halt(
                "scaffold_url_acquisition_executor_unknown_fetcher_field",
                request_id=request_id,
                field=key,
            )
            raise UnknownFetcherResultField(
                "fetcher result for request {0!r} declares unknown key "
                "{1!r}".format(request_id, key)
            )

    if result["fetch_status"] != _EXPECTED_FETCH_STATUS:
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_fetch_status",
            request_id=request_id,
            fetch_status=result["fetch_status"],
        )
        raise InvalidFetchStatus(
            "fetcher result for request {0!r} fetch_status must be "
            "{1!r}".format(request_id, _EXPECTED_FETCH_STATUS)
        )

    content_bytes = result["content_bytes"]
    if not isinstance(content_bytes, bytes) or len(content_bytes) == 0:
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_content_bytes",
            request_id=request_id,
        )
        raise InvalidFetchedContentBytes(
            "fetcher result for request {0!r} content_bytes must be "
            "non-empty bytes".format(request_id)
        )

    if len(content_bytes) > MAX_FETCHED_BYTES:
        event_log.halt(
            "scaffold_url_acquisition_executor_fetched_content_too_large",
            request_id=request_id,
            byte_length=len(content_bytes),
        )
        raise FetchedContentTooLarge(
            "fetcher result for request {0!r} content_bytes length "
            "{1} exceeds MAX_FETCHED_BYTES {2}".format(
                request_id, len(content_bytes), MAX_FETCHED_BYTES
            )
        )

    if not _require_non_empty_string(result["content_type"]):
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_content_type",
            request_id=request_id,
        )
        raise InvalidFetchedContentType(
            "fetcher result for request {0!r} content_type must be a "
            "non-empty string".format(request_id)
        )

    if not _require_non_empty_string(result["fetched_at"]):
        event_log.halt(
            "scaffold_url_acquisition_executor_invalid_fetched_at",
            request_id=request_id,
        )
        raise InvalidFetchedAt(
            "fetcher result for request {0!r} fetched_at must be a "
            "non-empty string".format(request_id)
        )

    return content_bytes


def _build_acquired_reference(request, content_bytes, content_type, fetched_at):
    digest = hashlib.sha256(content_bytes).hexdigest()
    return {
        "request_id": request["request_id"],
        "declared_kind": request["declared_kind"],
        "origin_locator_observed": True,
        "origin_locator_length": len(request["origin_locator"]),
        "content_available": True,
        "content_byte_length": len(content_bytes),
        "content_hash_prefix": digest[:_HASH_PREFIX_LENGTH],
        "content_type": content_type,
        "fetched_at": fetched_at,
        "corpus_admitted": False,
        "qualified": False,
        "source_material_extracted": False,
        "route_object_created": False,
    }


def run_scaffold_url_acquisition_executor(
    acquisition_requests, fetch_url, event_log
):
    """Validate URL acquisition requests, invoke the injected fetcher
    per request in input order, and return a fresh fixed-shape
    acquired-source observation dict.
    """
    if not isinstance(acquisition_requests, list):
        event_log.halt(
            "scaffold_url_acquisition_executor_non_list_requests",
            acquisition_requests_type=type(acquisition_requests).__name__,
        )
        raise NonListUrlAcquisitionRequests(
            "acquisition_requests must be a list"
        )

    if not callable(fetch_url):
        event_log.halt(
            "scaffold_url_acquisition_executor_fetcher_not_callable",
            fetch_url_type=type(fetch_url).__name__,
        )
        raise FetcherNotCallable("fetch_url must be callable")

    event_log.append(
        "scaffold_url_acquisition_executor_started",
        request_count=len(acquisition_requests),
    )

    # Pass 1: validate all requests; halt before any fetcher call.
    _validate_all_requests(acquisition_requests, event_log)

    # Pass 2: invoke fetcher for each validated request and assemble
    # the acquired reference.
    acquired_references = []
    total_content_byte_length = 0
    for request in acquisition_requests:
        request_id = request["request_id"]
        event_log.append(
            "scaffold_url_acquisition_executor_fetch_started",
            request_id=request_id,
        )
        result = fetch_url(request["origin_locator"])
        content_bytes = _validate_fetcher_result(result, request_id, event_log)
        reference = _build_acquired_reference(
            request,
            content_bytes,
            result["content_type"],
            result["fetched_at"],
        )
        acquired_references.append(reference)
        total_content_byte_length += reference["content_byte_length"]
        event_log.append(
            "scaffold_url_acquisition_executor_fetch_completed",
            request_id=request_id,
            content_byte_length=reference["content_byte_length"],
        )

    output = {
        "url_acquisition_kind": "scaffold_url_acquisition_executor",
        "request_count": len(acquisition_requests),
        "fetched_count": len(acquired_references),
        "acquired_references": list(acquired_references),
        "total_content_byte_length": total_content_byte_length,
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "source_material_extracted_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "url_acquisition_note": _URL_ACQUISITION_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_url_acquisition_executor_passed",
        request_count=len(acquisition_requests),
        fetched_count=len(acquired_references),
        total_content_byte_length=total_content_byte_length,
    )
    return output
