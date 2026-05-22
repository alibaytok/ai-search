"""Scaffold source register-to-trace admission bridge.

WO-56 adds the pre-trace admission bridge that sits between WO-55
(the inert source reference quarantine register) and WO-54 (the
read-only source-intake trace). The bridge accepts the WO-55 clean-pass
register observation dict plus a list of already-loaded source record
dicts and verifies that:

- the register observation is shaped as a WO-55 clean-pass output and
  asserts no admission / no qualification / no authorization at the
  register layer;
- every source record references an existing register entry by
  `source_register_ref`;
- the matched register entry's `declared_kind` agrees with the source
  record's `source_kind`;
- no source record declares qualification, carries derived material,
  declares route status, or carries Source-Card-shaped fields.

A successful bridge observation means ONLY that the cross-references
between the source records and the register are consistent. It does
NOT mean any source is qualified, admitted, extractable, normalizable,
fragment-derivable, route-valid, or benchmark-ready.

The module performs no file read, no file write, no network call, no
download / fetch / crawl, and no hash computation. It does NOT invoke
the WO-54 trace or the WO-55 register; it only reads the WO-55 clean-
pass output dict and the WO-54-shaped source record dicts that the
caller has already loaded. Real-benchmark-ready remains NO.

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 / WO-54 /
WO-55 explicit non-claim constraint carries forward: this module does
not claim that any bridge, link, admission surface, register entry,
or in-memory observation is sufficient, necessary, superior, best,
complete, production-ready, recommended, or selected.

Public surface:

    run_scaffold_source_trace_admission_bridge(
        register_observation, source_records, event_log
    ) -> dict

Inputs:

- `register_observation`: a dict matching the WO-55 clean-pass output
  shape (`register_kind == "scaffold_source_intake_register"`,
  `register_entries` as a list of per-entry dicts each with
  `corpus_admitted is False` and `qualified is False`, top-level
  `corpus_admitted_count == 0`, `qualified_count == 0`, and four
  literal-False authorization / readiness / selection booleans).
- `source_records`: a list (possibly empty) of already-loaded source
  record dicts. Each dict must carry `source_id`, `source_kind`,
  `source_origin == "external"`, and `source_register_ref` matching
  an existing register entry `source_id`. The bridge rejects any
  source record carrying qualification, derived material, route
  status, or Source-Card-shaped fields.
- `event_log`: harness `EventLog`.

Clean-pass output keys: see `ALLOWED_OUTPUT_KEYS` (15 keys total).
The seven literal-False booleans (`selection_made`,
`measurement_authorized`, `real_benchmark_authorized`,
`real_benchmark_ready`, `extraction_authorized`,
`normalization_authorized`, `candidate_derivation_authorized`) are
emitted as literal False on every clean-pass path. The two literal-
zero counts (`corpus_admitted_count`, `qualified_count`) are emitted
as literal 0 on every clean-pass path.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


BRIDGE_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_OUTPUT_KEYS = (
    "bridge_kind",
    "register_entry_count",
    "source_records_checked_count",
    "linked_source_count",
    "linked_sources",
    "corpus_admitted_count",
    "qualified_count",
    "extraction_authorized",
    "normalization_authorized",
    "candidate_derivation_authorized",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "bridge_note",
)

EXPECTED_REGISTER_KIND = "scaffold_source_intake_register"

REGISTER_ENTRY_REQUIRED_FIELDS = (
    "source_id",
    "declared_kind",
    "hash_prefix",
    "byte_length",
    "observed_at",
    "corpus_admitted",
    "qualified",
)

SOURCE_RECORD_REQUIRED_FIELDS = (
    "source_id",
    "source_kind",
    "source_origin",
    "source_register_ref",
)

ALLOWED_SOURCE_ORIGIN = "external"

_DERIVED_MATERIAL_FIELDS = frozenset((
    "extracted_material",
    "normalized_material",
    "candidate_fragments",
    "candidate_route_fragments",
    "candidate_workflow_fragments",
))

ROUTE_STATUS_FIELDS = frozenset((
    "route",
    "route_id",
    "route_state",
    "plane",
    "official",
    "executable",
    "is_route",
    "is_official_route",
    "selected_as_official",
    "official_route_authorized",
    "route_authorized",
    "production_route",
    "selected_route",
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


_BRIDGE_NOTE = (
    "scaffold_source_trace_admission_bridge: a clean-pass bridge "
    "observation records that source records reference known register "
    "entries with consistent declared / source kinds only; it does NOT "
    "authorize extraction, normalization, candidate fragment "
    "derivation, route status, corpus admission, or benchmark "
    "readiness; OQ-003, OQ-015, OQ-031, OQ-048, OQ-076 remain OPEN; "
    "no real adapter, no benchmark execution, and no measurement "
    "authorization."
)


class NonObjectRegisterObservation(Exception):
    """Raised when `register_observation` is not a dict."""


class InvalidRegisterObservationShape(Exception):
    """Raised when `register_observation` is missing a required field or
    its `register_kind` / `register_entries` is the wrong shape."""


class RegisterObservationDeclaresCorpusAdmission(Exception):
    """Raised when the register observation declares any non-zero
    `corpus_admitted_count` or any per-entry `corpus_admitted is True`."""


class RegisterObservationDeclaresQualification(Exception):
    """Raised when the register observation declares any non-zero
    `qualified_count` or any per-entry `qualified is True`."""


class RegisterObservationDeclaresAuthorization(Exception):
    """Raised when the register observation declares any of the four
    authorization / readiness / selection booleans as not literal False."""


class NonListSourceRecords(Exception):
    """Raised when `source_records` is not a list."""


class NonObjectSourceRecord(Exception):
    """Raised when an entry of `source_records` is not a dict."""


class MissingSourceRecordField(Exception):
    """Raised when a source record is missing a required non-empty string
    field."""


class DuplicateSourceId(Exception):
    """Raised when two source records share one `source_id`."""


class DuplicateRegisterSourceId(Exception):
    """Raised when two register entries share one `source_id`."""


class SourceOriginNotExternal(Exception):
    """Raised when a source record's `source_origin` is not `external`."""


class UnknownSourceRegisterRef(Exception):
    """Raised when a source record's `source_register_ref` is not present
    as any register entry `source_id`."""


class SourceKindRegisterKindMismatch(Exception):
    """Raised when a source record's `source_kind` does not equal the
    matched register entry's `declared_kind`."""


class SourceRecordDeclaresQualification(Exception):
    """Raised when a source record declares `qualified` (with any value)."""


class SourceRecordCarriesQualificationRef(Exception):
    """Raised when a source record carries `qualification_ref`."""


class SourceRecordCarriesDerivedMaterial(Exception):
    """Raised when a source record carries `extracted_material`,
    `normalized_material`, `candidate_fragments`,
    `candidate_route_fragments`, or `candidate_workflow_fragments`."""


class SourceRecordClaimsRouteStatus(Exception):
    """Raised when a source record declares any route-status field or
    marker."""


class SourceCardShapedFieldRejected(Exception):
    """Raised when a source record declares any Source-Card-shaped field."""


class ForbiddenLanguageInSourceTraceAdmissionBridge(Exception):
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
    for phrase in BRIDGE_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_source_trace_admission_bridge_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInSourceTraceAdmissionBridge(
                "Forbidden phrase {0!r} found in source-trace admission "
                "bridge output".format(offending)
            )


def _require_non_empty_string(value):
    return isinstance(value, str) and bool(value)


def _validate_register_observation(register_observation, event_log):
    if not isinstance(register_observation, dict):
        event_log.halt(
            "scaffold_source_trace_admission_bridge_non_object_register_observation",
            register_observation_type=type(register_observation).__name__,
        )
        raise NonObjectRegisterObservation(
            "register_observation must be a dict"
        )
    if register_observation.get("register_kind") != EXPECTED_REGISTER_KIND:
        event_log.halt(
            "scaffold_source_trace_admission_bridge_invalid_register_kind",
            declared_register_kind=register_observation.get("register_kind"),
        )
        raise InvalidRegisterObservationShape(
            "register_observation register_kind must be {0!r}".format(
                EXPECTED_REGISTER_KIND
            )
        )
    entries = register_observation.get("register_entries")
    if not isinstance(entries, list):
        event_log.halt(
            "scaffold_source_trace_admission_bridge_invalid_register_entries",
        )
        raise InvalidRegisterObservationShape(
            "register_observation register_entries must be a list"
        )

    for boolean_key in (
        "selection_made",
        "measurement_authorized",
        "real_benchmark_authorized",
        "real_benchmark_ready",
    ):
        if register_observation.get(boolean_key) is not False:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_register_declares_authorization",
                boolean_key=boolean_key,
            )
            raise RegisterObservationDeclaresAuthorization(
                "register_observation {0!r} must be literal False".format(
                    boolean_key
                )
            )

    if register_observation.get("corpus_admitted_count") != 0:
        event_log.halt(
            "scaffold_source_trace_admission_bridge_register_declares_corpus_admission",
            corpus_admitted_count=register_observation.get(
                "corpus_admitted_count"
            ),
        )
        raise RegisterObservationDeclaresCorpusAdmission(
            "register_observation corpus_admitted_count must be literal 0"
        )
    if register_observation.get("qualified_count") != 0:
        event_log.halt(
            "scaffold_source_trace_admission_bridge_register_declares_qualification",
            qualified_count=register_observation.get("qualified_count"),
        )
        raise RegisterObservationDeclaresQualification(
            "register_observation qualified_count must be literal 0"
        )

    return entries


def _validate_register_entries(entries, event_log):
    index = {}
    for entry in entries:
        if not isinstance(entry, dict):
            event_log.halt(
                "scaffold_source_trace_admission_bridge_invalid_register_entry",
                entry_type=type(entry).__name__,
            )
            raise InvalidRegisterObservationShape(
                "every register entry must be a dict"
            )
        for field in REGISTER_ENTRY_REQUIRED_FIELDS:
            if field not in entry:
                event_log.halt(
                    "scaffold_source_trace_admission_bridge_register_entry_missing_field",
                    field=field,
                )
                raise InvalidRegisterObservationShape(
                    "register entry missing required field {0!r}".format(field)
                )
        if entry.get("corpus_admitted") is True:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_register_entry_corpus_admitted_true",
                source_id=entry.get("source_id"),
            )
            raise RegisterObservationDeclaresCorpusAdmission(
                "register entry {0!r} declares corpus_admitted True".format(
                    entry.get("source_id")
                )
            )
        if entry.get("qualified") is True:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_register_entry_qualified_true",
                source_id=entry.get("source_id"),
            )
            raise RegisterObservationDeclaresQualification(
                "register entry {0!r} declares qualified True".format(
                    entry.get("source_id")
                )
            )
        source_id = entry["source_id"]
        if source_id in index:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_duplicate_register_source_id",
                source_id=source_id,
            )
            raise DuplicateRegisterSourceId(
                "register entry source_id {0!r} appears more than once".format(
                    source_id
                )
            )
        index[source_id] = entry
    return index


def _reject_source_record_forbidden_fields(source, event_log):
    source_id = source.get("source_id")
    for key in source.keys():
        if key in SOURCE_RECORD_REQUIRED_FIELDS:
            continue
        if key == "qualified":
            event_log.halt(
                "scaffold_source_trace_admission_bridge_source_declares_qualification",
                source_id=source_id,
            )
            raise SourceRecordDeclaresQualification(
                "source record {0!r} declares qualified at the bridge "
                "layer".format(source_id)
            )
        if key == "qualification_ref":
            event_log.halt(
                "scaffold_source_trace_admission_bridge_source_carries_qualification_ref",
                source_id=source_id,
            )
            raise SourceRecordCarriesQualificationRef(
                "source record {0!r} carries qualification_ref at the "
                "bridge layer".format(source_id)
            )
        if key in _DERIVED_MATERIAL_FIELDS:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_source_carries_derived_material",
                source_id=source_id,
                field=key,
            )
            raise SourceRecordCarriesDerivedMaterial(
                "source record {0!r} carries derived-material field {1!r} "
                "at the bridge layer".format(source_id, key)
            )
        if key in ROUTE_STATUS_FIELDS:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_source_claims_route_status",
                source_id=source_id,
                field=key,
            )
            raise SourceRecordClaimsRouteStatus(
                "source record {0!r} declares route-status field {1!r} at "
                "the bridge layer".format(source_id, key)
            )
        if key in _SOURCE_CARD_SHAPED_FIELDS:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_source_card_shaped_field_rejected",
                source_id=source_id,
                field=key,
            )
            raise SourceCardShapedFieldRejected(
                "source record {0!r} declares Source-Card-shaped field "
                "{1!r}; OQ-031 remains OPEN".format(source_id, key)
            )
        # Any other key is permitted at the bridge layer; the bridge does
        # not enforce an exact-key set on source records (WO-54 already
        # admits richer shapes). This permissive position is intentional
        # and bounded by the explicit forbidden categories above.


def _validate_source_record(source, register_index, event_log):
    if not isinstance(source, dict):
        event_log.halt(
            "scaffold_source_trace_admission_bridge_non_object_source_record",
            source_type=type(source).__name__,
        )
        raise NonObjectSourceRecord("each source record must be a dict")
    for field in SOURCE_RECORD_REQUIRED_FIELDS:
        value = source.get(field)
        if not _require_non_empty_string(value):
            event_log.halt(
                "scaffold_source_trace_admission_bridge_missing_source_record_field",
                field=field,
            )
            raise MissingSourceRecordField(
                "source record field {0!r} must be a non-empty string".format(
                    field
                )
            )
    if source["source_origin"] != ALLOWED_SOURCE_ORIGIN:
        event_log.halt(
            "scaffold_source_trace_admission_bridge_source_origin_not_external",
            source_id=source["source_id"],
            source_origin=source["source_origin"],
        )
        raise SourceOriginNotExternal(
            "source record {0!r} source_origin {1!r} is not the admitted "
            "external value".format(source["source_id"], source["source_origin"])
        )
    _reject_source_record_forbidden_fields(source, event_log)

    ref = source["source_register_ref"]
    if ref not in register_index:
        event_log.halt(
            "scaffold_source_trace_admission_bridge_unknown_source_register_ref",
            source_id=source["source_id"],
            source_register_ref=ref,
        )
        raise UnknownSourceRegisterRef(
            "source record {0!r} source_register_ref {1!r} is not present "
            "in the register".format(source["source_id"], ref)
        )

    register_entry = register_index[ref]
    if source["source_kind"] != register_entry.get("declared_kind"):
        event_log.halt(
            "scaffold_source_trace_admission_bridge_source_kind_register_kind_mismatch",
            source_id=source["source_id"],
            source_kind=source["source_kind"],
            declared_kind=register_entry.get("declared_kind"),
        )
        raise SourceKindRegisterKindMismatch(
            "source record {0!r} source_kind {1!r} does not match register "
            "entry declared_kind {2!r}".format(
                source["source_id"],
                source["source_kind"],
                register_entry.get("declared_kind"),
            )
        )

    return register_entry


def run_scaffold_source_trace_admission_bridge(
    register_observation, source_records, event_log
):
    """Run the scaffold source register-to-trace admission bridge and
    return a fresh dict.

    Raises a declared exception on the first rejection observed; on
    clean pass returns a dict with exactly the fifteen allowed keys in
    `ALLOWED_OUTPUT_KEYS`.
    """
    entries = _validate_register_observation(register_observation, event_log)
    register_index = _validate_register_entries(entries, event_log)

    if not isinstance(source_records, list):
        event_log.halt(
            "scaffold_source_trace_admission_bridge_non_list_source_records",
            source_records_type=type(source_records).__name__,
        )
        raise NonListSourceRecords("source_records must be a list")

    event_log.append(
        "scaffold_source_trace_admission_bridge_started",
        register_entry_count=len(entries),
        source_records_count=len(source_records),
    )

    linked_sources = []
    seen_source_ids = set()

    for source in source_records:
        register_entry = _validate_source_record(source, register_index, event_log)
        source_id = source["source_id"]
        if source_id in seen_source_ids:
            event_log.halt(
                "scaffold_source_trace_admission_bridge_duplicate_source_id",
                source_id=source_id,
            )
            raise DuplicateSourceId(
                "source_id {0!r} appears more than once".format(source_id)
            )
        seen_source_ids.add(source_id)

        linked = {
            "source_id": source_id,
            "source_register_ref": source["source_register_ref"],
            "declared_kind": register_entry["declared_kind"],
            "source_kind": source["source_kind"],
            "corpus_admitted": False,
            "qualified": False,
            "extraction_authorized": False,
            "normalization_authorized": False,
            "candidate_derivation_authorized": False,
        }
        linked_sources.append(linked)
        event_log.append(
            "scaffold_source_trace_admission_bridge_source_linked",
            source_id=source_id,
            source_register_ref=source["source_register_ref"],
            declared_kind=register_entry["declared_kind"],
            source_kind=source["source_kind"],
        )

    output = {
        "bridge_kind": "scaffold_source_trace_admission_bridge",
        "register_entry_count": len(entries),
        "source_records_checked_count": len(source_records),
        "linked_source_count": len(linked_sources),
        "linked_sources": list(linked_sources),
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "extraction_authorized": False,
        "normalization_authorized": False,
        "candidate_derivation_authorized": False,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "bridge_note": _BRIDGE_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_source_trace_admission_bridge_passed",
        register_entry_count=len(entries),
        source_records_checked_count=len(source_records),
        linked_source_count=len(linked_sources),
        corpus_admitted_count=0,
        qualified_count=0,
    )
    return output
