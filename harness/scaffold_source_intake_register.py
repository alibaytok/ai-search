"""Scaffold external source reference quarantine register.

WO-55 adds the upstream quarantine boundary for external source
collections. The register admits already-loaded source reference dicts
into an in-memory intake layer that explicitly records non-admission,
non-qualification, and non-route status. The register sits upstream of
the WO-54 source-intake trace: WO-55 records the fact that a source
exists as an inert reference; WO-54 (or any future scaffold) is the
only place where downstream observation occurs, and only over its own
already-loaded source records.

This module does NOT download sources, does NOT read source files,
does NOT write source files, does NOT compute file hashes, does NOT
call network, does NOT implement extraction, does NOT implement
normalization, does NOT implement candidate fragment derivation, does
NOT implement real retrieval / indexing / ranking / similarity /
scoring / metric collection, does NOT invoke a real or mock adapter,
does NOT run a real benchmark, does NOT collect quality / performance
/ operational measurements, does NOT select architecture / vendor /
library / index family / ANN backend / neural re-scorer / retrieval
family / ablation cell / multi-stage variant / production system,
does NOT create Source Cards or Route Cards, does NOT create a
production artifact schema, and does NOT mutate `benchmark-fixtures/`.

This is NOT prompt search, NOT skill search, NOT agent selection,
NOT generic RAG, NOT source qualification, NOT Source Card creation,
NOT corpus admission, NOT benchmark fixture admission, and NOT
production artifact schema creation.

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 / WO-54
explicit non-claim constraint carries forward: this module does not
claim that any register entry, declared kind, identity field, or
quarantine boundary is sufficient, necessary, superior, best,
complete, production-ready, recommended, or selected. The bounded
admission surfaces are not claimed exhaustive.

Public surface:

    run_scaffold_source_intake_register(
        source_reference_records, event_log
    ) -> dict

Inputs:

- `source_reference_records`: a list (possibly empty) of already-loaded
  source reference dicts. Each dict must contain EXACTLY the six
  allowed fields (`source_id`, `origin`, `declared_kind`, `hash`,
  `byte_length`, `observed_at`); unknown keys and any forbidden
  field are rejected.
- `event_log`: harness `EventLog`.

The clean-pass result dict has exactly eleven allowed top-level keys
in `ALLOWED_OUTPUT_KEYS`. Every authorization / readiness / selection
boolean is literal False on every emitted path. Every per-entry
`corpus_admitted` is literal False. Every per-entry `qualified` is
literal False. `corpus_admitted_count` is literal 0.
`qualified_count` is literal 0.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


REGISTER_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_OUTPUT_KEYS = (
    "register_kind",
    "references_observed_count",
    "unique_origin_count",
    "register_entries",
    "corpus_admitted_count",
    "qualified_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "intake_note",
)

ALLOWED_REFERENCE_FIELDS = frozenset((
    "source_id",
    "origin",
    "declared_kind",
    "hash",
    "byte_length",
    "observed_at",
))

ALLOWED_DECLARED_KINDS = frozenset((
    "prompt_collection",
    "skill_collection",
    "agent_description_collection",
    "tool_description_collection",
    "document_collection",
))

_HASH_PREFIX_LENGTH = 12

_QUALIFIED_FIELD = "qualified"
_QUALIFICATION_REF_FIELD = "qualification_ref"
_CORPUS_ADMISSION_FIELD = "corpus_admitted"

_DERIVED_MATERIAL_FIELDS = frozenset((
    "extracted_material",
    "normalized_material",
    "candidate_fragments",
    "candidate_route_fragments",
    "candidate_workflow_fragments",
))

_ROUTE_FIELDS = frozenset((
    "route",
    "route_id",
    "route_state",
    "plane",
    "official",
    "executable",
))

_SOURCE_CARD_SHAPED_FIELDS = frozenset((
    "authority",
    "trust",
    "freshness",
    "ownership",
    "source_card",
    "route_card",
    "qualification_evidence",
    "validation_evidence",
))

_BENCHMARK_FIXTURE_SHAPED_FIELDS = frozenset((
    "benchmark_fixture_class",
    "golden_intent",
    "hard_negative",
    "boundary_violation",
))

ROUTE_STATUS_BOOLEAN_KEYS = (
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


_INTAKE_NOTE = (
    "scaffold_source_intake_register quarantine layer: each register "
    "entry records identity and integrity metadata only; presence of a "
    "reference is not corpus admission and is not source qualification; "
    "hash is identity / integrity only; OQ-003, OQ-015, OQ-031, OQ-048, "
    "OQ-076 remain OPEN; no real adapter, no benchmark execution, and "
    "no measurement authorization."
)


class NonListSourceReferences(Exception):
    """Raised when `source_reference_records` is not a list."""


class NonObjectSourceReference(Exception):
    """Raised when an entry of `source_reference_records` is not a dict."""


class MissingReferenceField(Exception):
    """Raised when a source reference is missing a required field."""


class UnknownReferenceField(Exception):
    """Raised when a source reference declares a key outside the allowed
    field set and outside every named-forbidden category."""


class DuplicateSourceId(Exception):
    """Raised when two source references share one `source_id`."""


class DeclaredKindNotAllowed(Exception):
    """Raised when `declared_kind` is not in `ALLOWED_DECLARED_KINDS`."""


class InvalidHashField(Exception):
    """Raised when `hash` is not a non-empty string."""


class InvalidByteLength(Exception):
    """Raised when `byte_length` is not a non-negative int (and not a bool)."""


class QualifiedFieldForbiddenAtRegisterLayer(Exception):
    """Raised when a source reference declares the `qualified` field."""


class QualificationRefFieldForbiddenAtRegisterLayer(Exception):
    """Raised when a source reference declares the `qualification_ref` field."""


class CorpusAdmissionFieldForbiddenAtRegisterLayer(Exception):
    """Raised when a source reference declares the `corpus_admitted` field."""


class DerivedMaterialForbiddenAtRegisterLayer(Exception):
    """Raised when a source reference declares any derived-material field."""


class RouteFieldForbiddenAtRegisterLayer(Exception):
    """Raised when a source reference declares any route-shaped field."""


class RouteStatusClaimAtRegisterLayer(Exception):
    """Raised when a source reference declares a route-status claim
    (a route-status boolean set to True)."""


class SourceCardShapedFieldRejected(Exception):
    """Raised when a source reference declares any Source-Card-shaped
    field (authority / trust / freshness / ownership / source_card /
    route_card / qualification_evidence / validation_evidence)."""


class BenchmarkFixtureFieldRejected(Exception):
    """Raised when a source reference declares any benchmark-fixture-shaped
    field (benchmark_fixture_class / golden_intent / hard_negative /
    boundary_violation)."""


class ForbiddenLanguageInSourceIntakeRegister(Exception):
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
    for phrase in REGISTER_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_source_intake_register_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInSourceIntakeRegister(
                "Forbidden phrase {0!r} found in source-intake register "
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


def _validate_required_fields(reference, event_log):
    for field in ("source_id", "origin", "declared_kind", "hash", "observed_at"):
        if field not in reference or not _require_non_empty_string(
            reference.get(field)
        ):
            event_log.halt(
                "scaffold_source_intake_register_missing_reference_field",
                field=field,
            )
            raise MissingReferenceField(
                "source reference is missing required non-empty string field "
                "{0!r}".format(field)
            )
    if "byte_length" not in reference:
        event_log.halt(
            "scaffold_source_intake_register_missing_reference_field",
            field="byte_length",
        )
        raise MissingReferenceField(
            "source reference is missing required field 'byte_length'"
        )


def _validate_field_values(reference, event_log):
    source_id = reference["source_id"]
    if reference["declared_kind"] not in ALLOWED_DECLARED_KINDS:
        event_log.halt(
            "scaffold_source_intake_register_declared_kind_not_allowed",
            source_id=source_id,
            declared_kind=reference["declared_kind"],
        )
        raise DeclaredKindNotAllowed(
            "source reference {0!r} declares declared_kind {1!r} outside "
            "ALLOWED_DECLARED_KINDS".format(source_id, reference["declared_kind"])
        )
    if not _require_non_empty_string(reference.get("hash")):
        event_log.halt(
            "scaffold_source_intake_register_invalid_hash",
            source_id=source_id,
        )
        raise InvalidHashField(
            "source reference {0!r} hash must be a non-empty string".format(
                source_id
            )
        )
    if not _is_non_negative_int(reference.get("byte_length")):
        event_log.halt(
            "scaffold_source_intake_register_invalid_byte_length",
            source_id=source_id,
        )
        raise InvalidByteLength(
            "source reference {0!r} byte_length must be a non-negative int "
            "(bools rejected)".format(source_id)
        )


def _reject_forbidden_keys(reference, event_log):
    source_id = reference.get("source_id")
    for key in reference.keys():
        if key in ALLOWED_REFERENCE_FIELDS:
            continue
        if key == _QUALIFIED_FIELD:
            event_log.halt(
                "scaffold_source_intake_register_qualified_field_forbidden",
                source_id=source_id,
            )
            raise QualifiedFieldForbiddenAtRegisterLayer(
                "source reference {0!r} declares forbidden field 'qualified' "
                "at the register layer".format(source_id)
            )
        if key == _QUALIFICATION_REF_FIELD:
            event_log.halt(
                "scaffold_source_intake_register_qualification_ref_field_forbidden",
                source_id=source_id,
            )
            raise QualificationRefFieldForbiddenAtRegisterLayer(
                "source reference {0!r} declares forbidden field "
                "'qualification_ref' at the register layer".format(source_id)
            )
        if key == _CORPUS_ADMISSION_FIELD:
            event_log.halt(
                "scaffold_source_intake_register_corpus_admission_field_forbidden",
                source_id=source_id,
            )
            raise CorpusAdmissionFieldForbiddenAtRegisterLayer(
                "source reference {0!r} declares forbidden field "
                "'corpus_admitted' at the register layer".format(source_id)
            )
        if key in _DERIVED_MATERIAL_FIELDS:
            event_log.halt(
                "scaffold_source_intake_register_derived_material_field_forbidden",
                source_id=source_id,
                field=key,
            )
            raise DerivedMaterialForbiddenAtRegisterLayer(
                "source reference {0!r} declares forbidden derived-material "
                "field {1!r} at the register layer".format(source_id, key)
            )
        if key in _ROUTE_FIELDS:
            event_log.halt(
                "scaffold_source_intake_register_route_field_forbidden",
                source_id=source_id,
                field=key,
            )
            raise RouteFieldForbiddenAtRegisterLayer(
                "source reference {0!r} declares forbidden route field "
                "{1!r} at the register layer".format(source_id, key)
            )
        if key in _SOURCE_CARD_SHAPED_FIELDS:
            event_log.halt(
                "scaffold_source_intake_register_source_card_shaped_field_rejected",
                source_id=source_id,
                field=key,
            )
            raise SourceCardShapedFieldRejected(
                "source reference {0!r} declares Source-Card-shaped field "
                "{1!r}; OQ-031 remains OPEN".format(source_id, key)
            )
        if key in _BENCHMARK_FIXTURE_SHAPED_FIELDS:
            event_log.halt(
                "scaffold_source_intake_register_benchmark_fixture_field_rejected",
                source_id=source_id,
                field=key,
            )
            raise BenchmarkFixtureFieldRejected(
                "source reference {0!r} declares benchmark-fixture-shaped "
                "field {1!r}; RK-039 not relaxed".format(source_id, key)
            )
        if key in ROUTE_STATUS_BOOLEAN_KEYS and reference[key] is True:
            event_log.halt(
                "scaffold_source_intake_register_route_status_claim",
                source_id=source_id,
                field=key,
            )
            raise RouteStatusClaimAtRegisterLayer(
                "source reference {0!r} declares route-status claim "
                "{1!r}=True at the register layer".format(source_id, key)
            )
        event_log.halt(
            "scaffold_source_intake_register_unknown_field",
            source_id=source_id,
            field=key,
        )
        raise UnknownReferenceField(
            "source reference {0!r} declares unknown key {1!r}".format(
                source_id, key
            )
        )


def _validate_reference(reference, event_log):
    if not isinstance(reference, dict):
        event_log.halt(
            "scaffold_source_intake_register_non_object_reference",
            reference_type=type(reference).__name__,
        )
        raise NonObjectSourceReference("each source reference must be a dict")
    _validate_required_fields(reference, event_log)
    _reject_forbidden_keys(reference, event_log)
    _validate_field_values(reference, event_log)


def run_scaffold_source_intake_register(source_reference_records, event_log):
    """Run the scaffold source-intake register and return a fresh dict.

    Raises a declared exception on the first rejection observed; on
    clean pass returns a dict with exactly the eleven allowed keys in
    `ALLOWED_OUTPUT_KEYS`.
    """
    if not isinstance(source_reference_records, list):
        event_log.halt(
            "scaffold_source_intake_register_non_list_source_references",
            source_reference_records_type=type(source_reference_records).__name__,
        )
        raise NonListSourceReferences(
            "source_reference_records must be a list"
        )

    event_log.append(
        "scaffold_source_intake_register_started",
        references_count=len(source_reference_records),
    )

    register_entries = []
    seen_source_ids = set()
    unique_origins = set()

    for reference in source_reference_records:
        _validate_reference(reference, event_log)
        source_id = reference["source_id"]
        if source_id in seen_source_ids:
            event_log.halt(
                "scaffold_source_intake_register_duplicate_source_id",
                source_id=source_id,
            )
            raise DuplicateSourceId(
                "source_id {0!r} appears more than once".format(source_id)
            )
        seen_source_ids.add(source_id)
        unique_origins.add(reference["origin"])

        entry = {
            "source_id": source_id,
            "declared_kind": reference["declared_kind"],
            "hash_prefix": reference["hash"][:_HASH_PREFIX_LENGTH],
            "byte_length": reference["byte_length"],
            "observed_at": reference["observed_at"],
            "corpus_admitted": False,
            "qualified": False,
        }
        register_entries.append(entry)
        event_log.append(
            "scaffold_source_intake_reference_observed",
            source_id=source_id,
            declared_kind=reference["declared_kind"],
            byte_length=reference["byte_length"],
        )

    output = {
        "register_kind": "scaffold_source_intake_register",
        "references_observed_count": len(source_reference_records),
        "unique_origin_count": len(unique_origins),
        "register_entries": list(register_entries),
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "intake_note": _INTAKE_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_source_intake_register_passed",
        references_observed_count=len(source_reference_records),
        unique_origin_count=len(unique_origins),
        corpus_admitted_count=0,
        qualified_count=0,
    )
    return output
