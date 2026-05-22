"""Scaffold URL acquisition register-readiness diagnostic.

WO-62 adds a scaffold-only diagnostic that inspects a WO-61 URL
acquisition observation and determines whether it is sufficient to
produce WO-55-compatible source reference records.

WO-61 intentionally does NOT echo the raw URL (`origin_locator`) or
the full `content_hash`; it emits only structural markers
(`origin_locator_length`, `origin_locator_observed: True`) and a
truncated `content_hash_prefix`. The WO-55 quarantine register
requires the full `origin` string and the full `hash` string. WO-62
makes that gap explicit and testable: for a clean WO-61 observation,
the diagnostic returns `register_projection_ready: False` along with
named blocked reasons.

This diagnostic does NOT invent `origin`, does NOT invent `hash`,
does NOT reconstruct missing identity from `content_hash_prefix`,
does NOT fetch URLs, does NOT compute hashes, does NOT read files,
does NOT extract / normalize / index / retrieve / rank / score, and
does NOT invoke WO-55 or WO-61 public functions. The module imports
only harness-internal forbidden-language constants.

The WO-47 through WO-61 explicit non-claim constraint carries
forward: this module does not claim any diagnostic record, blocked
reason, missing-field name, or in-memory observation is sufficient,
necessary, superior, best, complete, production-ready, recommended,
or selected. The bounded admission surface is not claimed exhaustive.

Public surface:

    run_scaffold_url_acquisition_register_readiness(
        url_acquisition_observation, event_log
    ) -> dict

The clean-pass output dict has exactly fifteen allowed keys in
`ALLOWED_OUTPUT_KEYS`. Every authorization / readiness / selection
boolean and the three per-output admission booleans
(`register_projection_ready`, `safe_to_invent_missing_identity`,
`source_register_invocation_authorized`) are literal False on every
emitted path. The two admission/qualification counts are literal 0.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


READINESS_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "readiness_kind",
    "url_acquisition_reference_count",
    "register_projection_ready",
    "register_projection_blocked_reason_count",
    "register_projection_blocked_reasons",
    "missing_register_fields",
    "safe_to_invent_missing_identity",
    "source_register_invocation_authorized",
    "corpus_admitted_count",
    "qualified_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "readiness_note",
)


_EXPECTED_URL_ACQUISITION_KIND = "scaffold_url_acquisition_executor"


REQUIRED_OBSERVATION_FIELDS = (
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


REQUIRED_ACQUIRED_REFERENCE_FIELDS = (
    "request_id",
    "declared_kind",
    "origin_locator_observed",
    "origin_locator_length",
    "content_available",
    "content_byte_length",
    "content_hash_prefix",
    "content_type",
    "fetched_at",
    "corpus_admitted",
    "qualified",
    "source_material_extracted",
    "route_object_created",
)


_PER_REFERENCE_UNSAFE_ADMISSION_KEYS = (
    "corpus_admitted",
    "qualified",
    "source_material_extracted",
    "route_object_created",
)


_TOP_LEVEL_UNSAFE_BOOLEAN_KEYS = (
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
)


_TOP_LEVEL_UNSAFE_COUNT_KEYS = (
    "corpus_admitted_count",
    "qualified_count",
    "source_material_extracted_count",
)


# Fields that, if present in either the top-level observation dict or in any
# per-reference dict, indicate the WO-61 non-echo boundary has been violated
# or that the input has been mixed with downstream-shaped material.
_FORBIDDEN_REGISTER_PROJECTION_FIELDS = frozenset((
    "origin_locator",
    "content_bytes",
    "content_hash",
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
    "source_card",
    "route_card",
    "authority",
    "trust",
    "freshness",
    "ownership",
    "validation_evidence",
    "qualification_evidence",
    "benchmark_fixture_class",
    "golden_intent",
    "hard_negative",
    "boundary_violation",
))


_BLOCKED_REASON_ORIGIN_MISSING = "origin_not_available_for_wo55_register"
_BLOCKED_REASON_HASH_MISSING = "full_hash_not_available_for_wo55_register"

_MISSING_REGISTER_FIELDS = ("origin", "hash")


_READINESS_NOTE = (
    "scaffold_url_acquisition_register_readiness: a clean-pass "
    "diagnostic over a WO-61 URL acquisition observation reports "
    "that register projection is NOT ready because the WO-61 "
    "observation only exposes structural URL observation and a "
    "hash prefix, not the full origin and full hash required by "
    "the WO-55 quarantine register; presence of this diagnostic "
    "is NOT corpus admission, NOT source qualification, NOT a "
    "route object, NOT a Source Card, NOT a register record, NOT "
    "permission to invent missing identity, and NOT permission to "
    "invoke the WO-55 register; OQ-003, OQ-015, OQ-031, OQ-048, "
    "OQ-076 remain OPEN; no real adapter, no benchmark execution, "
    "and no measurement authorization."
)


class NonObjectUrlAcquisitionObservation(Exception):
    """Raised when `url_acquisition_observation` is not a dict."""


class InvalidUrlAcquisitionKind(Exception):
    """Raised when `url_acquisition_kind` does not equal the expected
    WO-61 kind string."""


class MissingUrlAcquisitionObservationField(Exception):
    """Raised when a top-level required observation field is missing."""


class InvalidAcquiredReferences(Exception):
    """Raised when `acquired_references` is not a list."""


class NonObjectAcquiredReference(Exception):
    """Raised when an entry of `acquired_references` is not a dict."""


class MissingAcquiredReferenceField(Exception):
    """Raised when an acquired reference is missing a required field."""


class UnsafeAdmissionClaimInUrlAcquisitionObservation(Exception):
    """Raised when the input observation declares any admission /
    qualification / extraction / route-creation / measurement /
    benchmark-readiness claim."""


class ForbiddenRegisterProjectionFieldPresent(Exception):
    """Raised when a forbidden register-projection-shaped field appears
    in the input observation at the top level or per-reference."""


class ForbiddenLanguageInRegisterReadinessDiagnostic(Exception):
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
    for phrase in READINESS_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_url_acquisition_register_readiness_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInRegisterReadinessDiagnostic(
                "Forbidden phrase {0!r} found in register readiness "
                "diagnostic output".format(offending)
            )


def _reject_forbidden_register_projection_fields(
    observation, event_log, _scope_label
):
    for key in observation.keys():
        if key in _FORBIDDEN_REGISTER_PROJECTION_FIELDS:
            event_log.halt(
                "scaffold_url_acquisition_register_readiness_forbidden_field",
                scope=_scope_label,
                field=key,
            )
            raise ForbiddenRegisterProjectionFieldPresent(
                "{0!r} declares forbidden register-projection-shaped "
                "field {1!r}".format(_scope_label, key)
            )


def _validate_top_level_observation(observation, event_log):
    if not isinstance(observation, dict):
        event_log.halt(
            "scaffold_url_acquisition_register_readiness_non_object_observation",
            observation_type=type(observation).__name__,
        )
        raise NonObjectUrlAcquisitionObservation(
            "url_acquisition_observation must be a dict"
        )

    for field in REQUIRED_OBSERVATION_FIELDS:
        if field not in observation:
            event_log.halt(
                "scaffold_url_acquisition_register_readiness_missing_observation_field",
                field=field,
            )
            raise MissingUrlAcquisitionObservationField(
                "url_acquisition_observation is missing required field "
                "{0!r}".format(field)
            )

    if observation["url_acquisition_kind"] != _EXPECTED_URL_ACQUISITION_KIND:
        event_log.halt(
            "scaffold_url_acquisition_register_readiness_invalid_kind",
            url_acquisition_kind=observation["url_acquisition_kind"],
        )
        raise InvalidUrlAcquisitionKind(
            "url_acquisition_kind must equal {0!r}".format(
                _EXPECTED_URL_ACQUISITION_KIND
            )
        )

    if not isinstance(observation["acquired_references"], list):
        event_log.halt(
            "scaffold_url_acquisition_register_readiness_invalid_acquired_references",
            acquired_references_type=type(
                observation["acquired_references"]
            ).__name__,
        )
        raise InvalidAcquiredReferences(
            "acquired_references must be a list"
        )

    for boolean_key in _TOP_LEVEL_UNSAFE_BOOLEAN_KEYS:
        if observation[boolean_key] is not False:
            event_log.halt(
                "scaffold_url_acquisition_register_readiness_top_level_unsafe_boolean",
                key=boolean_key,
            )
            raise UnsafeAdmissionClaimInUrlAcquisitionObservation(
                "observation declares {0!r} as not literal False".format(
                    boolean_key
                )
            )

    for count_key in _TOP_LEVEL_UNSAFE_COUNT_KEYS:
        if observation[count_key] != 0:
            event_log.halt(
                "scaffold_url_acquisition_register_readiness_top_level_unsafe_count",
                key=count_key,
                value=observation[count_key],
            )
            raise UnsafeAdmissionClaimInUrlAcquisitionObservation(
                "observation declares {0!r} as non-zero".format(count_key)
            )

    _reject_forbidden_register_projection_fields(
        observation, event_log, "url_acquisition_observation"
    )


def _validate_acquired_reference(reference, event_log):
    if not isinstance(reference, dict):
        event_log.halt(
            "scaffold_url_acquisition_register_readiness_non_object_reference",
            reference_type=type(reference).__name__,
        )
        raise NonObjectAcquiredReference(
            "each acquired reference must be a dict"
        )

    for field in REQUIRED_ACQUIRED_REFERENCE_FIELDS:
        if field not in reference:
            event_log.halt(
                "scaffold_url_acquisition_register_readiness_missing_reference_field",
                field=field,
            )
            raise MissingAcquiredReferenceField(
                "acquired reference is missing required field {0!r}".format(
                    field
                )
            )

    for boolean_key in _PER_REFERENCE_UNSAFE_ADMISSION_KEYS:
        if reference[boolean_key] is not False:
            event_log.halt(
                "scaffold_url_acquisition_register_readiness_per_reference_unsafe_boolean",
                request_id=reference.get("request_id"),
                key=boolean_key,
            )
            raise UnsafeAdmissionClaimInUrlAcquisitionObservation(
                "acquired reference {0!r} declares {1!r} as not literal "
                "False".format(reference.get("request_id"), boolean_key)
            )

    _reject_forbidden_register_projection_fields(
        reference, event_log, "acquired_reference"
    )


def run_scaffold_url_acquisition_register_readiness(
    url_acquisition_observation, event_log
):
    """Inspect a WO-61 URL acquisition observation and return a fresh
    fixed-shape register-readiness diagnostic dict.

    The clean-pass result always reports
    `register_projection_ready: False` with named blocked reasons,
    because the WO-61 observation by construction does not carry the
    full `origin` and full `hash` fields the WO-55 register requires.
    """
    _validate_top_level_observation(url_acquisition_observation, event_log)
    _assert_no_forbidden_language(url_acquisition_observation, event_log)

    event_log.append(
        "scaffold_url_acquisition_register_readiness_started",
        url_acquisition_kind=url_acquisition_observation["url_acquisition_kind"],
        acquired_reference_count=len(
            url_acquisition_observation["acquired_references"]
        ),
    )

    for reference in url_acquisition_observation["acquired_references"]:
        _validate_acquired_reference(reference, event_log)
        event_log.append(
            "scaffold_url_acquisition_register_readiness_reference_observed",
            request_id=reference["request_id"],
            declared_kind=reference["declared_kind"],
        )

    blocked_reasons = [
        _BLOCKED_REASON_ORIGIN_MISSING,
        _BLOCKED_REASON_HASH_MISSING,
    ]

    output = {
        "readiness_kind": "scaffold_url_acquisition_register_readiness",
        "url_acquisition_reference_count": len(
            url_acquisition_observation["acquired_references"]
        ),
        "register_projection_ready": False,
        "register_projection_blocked_reason_count": len(blocked_reasons),
        "register_projection_blocked_reasons": list(blocked_reasons),
        "missing_register_fields": list(_MISSING_REGISTER_FIELDS),
        "safe_to_invent_missing_identity": False,
        "source_register_invocation_authorized": False,
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "readiness_note": _READINESS_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_url_acquisition_register_readiness_blocked",
        url_acquisition_reference_count=output[
            "url_acquisition_reference_count"
        ],
        register_projection_blocked_reason_count=output[
            "register_projection_blocked_reason_count"
        ],
        register_projection_blocked_reasons=list(blocked_reasons),
        missing_register_fields=list(_MISSING_REGISTER_FIELDS),
    )
    return output
