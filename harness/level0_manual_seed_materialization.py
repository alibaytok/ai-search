"""Level 0B manual seed source record materialization scaffold.

WO-L0-MATERIAL-01 adds a scaffold-only module that turns already-loaded
Level 0B manual seed item records into already-loaded
WO-59-compatible `source_reference_records` (WO-55-shaped) and
`source_records` (WO-56-shaped). The generated records derive only
from item metadata already present in the input; no URL is fetched,
no file is read, no PDF text is extracted, no external prompt or
source body is copied, no hash library is used, and no external
process is spawned.

This module first delegates manual seed shape validation to
`harness.level0_manual_seed_visible_report.run_level0_manual_seed_visible_report`
(WO-L0-RUN-01). If that delegate raises, the materialization
short-circuits before any source record is constructed.

This module does NOT invoke the WO-59 visible-report public
function and does NOT invoke the WO-L0-TRACE-01 trace-execution
public function; it does NOT invoke any other WO-50 through WO-62
public function (verified by static-scan test).

This module does NOT qualify any source, does NOT admit any source
to corpus, does NOT extract or normalize source material, does NOT
derive candidate route or candidate workflow fragments, does NOT
promote any record to an official route, does NOT compute any
similarity / distance / ranking / scoring / metric, and does NOT
decide architecture / vendor / library / index family / ANN backend
/ reranker / retrieval family / production system.

Contract reconciliation note (Constraints v1 hygiene): the
WO-L0-MATERIAL-01 packet text states the generated `source_record`
should carry `qualified: literal False`. The downstream WO-56
bridge contract rejects ANY presence of a `qualified` field in
source records (regardless of value). To keep the generated records
WO-59-compatible (since WO-59 calls WO-56 internally), this module
deliberately OMITS the `qualified` field from generated source
records. This is a deviation from the packet text and is
documented explicitly in the boundary document
`ai-search/65-level0-manual-seed-materialization-scaffold.md`,
in DC-065, and in the ledger entry. Canonical authority remains
with the downstream contract; the packet text is read here as a
description of intended unqualified state, not as an instruction
to add a field that would trigger downstream rejection.

The Constraints v1 non-claim constraint carries forward: this
module does not claim any generated source identifier, origin
string, declared kind mapping, synthetic hash, byte length count,
or observed-at marker is sufficient, necessary, superior, best,
complete, production-ready, recommended, or selected. The bounded
required field sets, the bounded item-kind to declared-kind
mapping, and the fixed output key set are bounded by
WO-L0-MATERIAL-01 and are NOT claimed exhaustive.

Public surface:

    run_level0_manual_seed_materialization(
        item_records, prompt_records, event_log
    ) -> dict
"""

from harness.level0_manual_seed_visible_report import (
    run_level0_manual_seed_visible_report,
)
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


MATERIALIZATION_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "materialization_kind",
    "manual_seed_shape_observation",
    "source_reference_records",
    "source_records",
    "source_reference_count",
    "source_record_count",
    "item_ids_materialized",
    "source_ids_materialized",
    "candidate_route_fragment_count",
    "candidate_workflow_fragment_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "materialization_note",
)


# Mapping from item_kind (as used in the WO-L0-ITEMS-01 planning
# tables) to WO-55 ALLOWED_DECLARED_KINDS. Bounded by
# WO-L0-MATERIAL-01 and NOT claimed exhaustive.
ITEM_KIND_TO_DECLARED_KIND = {
    "prompt": "prompt_collection",
    "skill": "skill_collection",
    "agent": "agent_description_collection",
    "instruction": "tool_description_collection",
    "workflow_file": "document_collection",
    "vendor_prompt_pattern": "prompt_collection",
    "encyclopedic_section": "document_collection",
}


_MATERIALIZED_SOURCE_ID_PREFIX = "L0-MAT-SRC"
_MATERIALIZED_HASH_PREFIX = "L0-MAT-HASH"
_OBSERVED_AT_LITERAL = "level0-manual-seed"
_SOURCE_ORIGIN_LITERAL = "external"
_ORIGIN_PREFIX = "manual-seed"


_MATERIALIZATION_KIND = "level0_manual_seed_materialization"


_MATERIALIZATION_NOTE = (
    "level0_manual_seed_materialization: a clean-pass observation "
    "that emits synthetic, metadata-only source_reference_records "
    "and source_records derived only from already-loaded item "
    "metadata; no URL is fetched, no file is read, no PDF text is "
    "extracted, no hash library is used, and no external prompt or "
    "source body is copied; this materialization is NOT corpus "
    "admission, NOT source qualification, NOT extraction, NOT "
    "normalization, NOT candidate-fragment derivation, NOT a route "
    "object, NOT a Source Card, NOT permission to flip any "
    "authorization / readiness boolean, and NOT a benchmark-ready "
    "flip; OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, "
    "OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN; no real adapter; "
    "no benchmark execution; no measurement authorization."
)


class UnknownItemKind(Exception):
    """Raised when an item record's `item_kind` does not appear in
    the bounded `ITEM_KIND_TO_DECLARED_KIND` mapping."""


class DuplicateMaterializedSourceId(Exception):
    """Raised when two materialized records would share the same
    generated `source_id`. Defensive: the generator uses a
    1-based index, so this can only fire under a programmer error."""


class ForbiddenLanguageInLevel0ManualSeedMaterialization(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in the emitted
    materialization report."""


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
        for phrase in MATERIALIZATION_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_manual_seed_materialization_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0ManualSeedMaterialization(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_manual_seed_materialization_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0ManualSeedMaterialization(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _materialize_one(item, materialized_source_id):
    """Build one source_reference_record and one source_record from
    already-present item metadata only.

    Field sources:
    - `origin` = "manual-seed:{item_id}:{item_locator}" (inert; no
      raw fetched content).
    - `declared_kind` = mapped from `item_kind` via
      ITEM_KIND_TO_DECLARED_KIND.
    - `hash` = "{prefix}-{NNN}-{item_id}" - a synthetic identity
      string of at least 12 characters, computed without any hash
      library.
    - `byte_length` = sum of metadata-string lengths
      (item_id + item_locator + item_title_or_anchor); this is a
      metadata count, NOT a fetched content length.
    - `observed_at` = literal "level0-manual-seed".
    """
    item_id = item["item_id"]
    item_kind = item["item_kind"]

    if item_kind not in ITEM_KIND_TO_DECLARED_KIND:
        # Caller raises; we just return None to signal a known
        # condition. (Actual exception raised by caller so it can
        # log entry_index.)
        return None

    declared_kind = ITEM_KIND_TO_DECLARED_KIND[item_kind]

    origin = "{0}:{1}:{2}".format(
        _ORIGIN_PREFIX, item_id, item["item_locator"]
    )

    hash_value = "{0}-{1}-{2}".format(
        _MATERIALIZED_HASH_PREFIX,
        materialized_source_id[-3:],
        item_id,
    )

    byte_length = (
        len(item_id)
        + len(item["item_locator"])
        + len(item["item_title_or_anchor"])
    )

    source_reference_record = {
        "source_id": materialized_source_id,
        "origin": origin,
        "declared_kind": declared_kind,
        "hash": hash_value,
        "byte_length": byte_length,
        "observed_at": _OBSERVED_AT_LITERAL,
    }

    # Note: per the contract-reconciliation note in the module
    # docstring, `qualified` is intentionally OMITTED from the
    # source_record. WO-56 rejects any presence of that field.
    source_record = {
        "source_id": materialized_source_id,
        "source_kind": declared_kind,
        "source_origin": _SOURCE_ORIGIN_LITERAL,
        "source_register_ref": materialized_source_id,
    }

    return source_reference_record, source_record


def run_level0_manual_seed_materialization(
    item_records, prompt_records, event_log
):
    """Validate manual seed shape and emit synthetic, metadata-only
    WO-59-compatible source records.

    See module docstring for the full non-claim constraint and the
    contract-reconciliation note regarding the `qualified` field.
    """
    event_log.append("level0_manual_seed_materialization_started")

    # Phase 1: delegate to WO-L0-RUN-01 for manual seed shape
    # validation. If this delegate raises, control never reaches the
    # materialization loop below; the execution short-circuits before
    # any source record is constructed.
    manual_seed_shape_observation = run_level0_manual_seed_visible_report(
        item_records, prompt_records, event_log
    )

    # Phase 2: materialize per item.
    source_reference_records = []
    source_records = []
    seen_source_ids = set()

    for entry_index, item in enumerate(item_records):
        materialized_source_id = "{0}-{1:03d}".format(
            _MATERIALIZED_SOURCE_ID_PREFIX, entry_index + 1
        )

        if materialized_source_id in seen_source_ids:
            event_log.halt(
                reason="level0_manual_seed_materialization_duplicate_materialized_source_id",
                entry_index=entry_index,
                materialized_source_id=materialized_source_id,
            )
            raise DuplicateMaterializedSourceId(
                "materialized source_id {0!r} appears more than once".format(
                    materialized_source_id
                )
            )

        item_kind = item["item_kind"]
        if item_kind not in ITEM_KIND_TO_DECLARED_KIND:
            event_log.halt(
                reason="level0_manual_seed_materialization_unknown_item_kind",
                entry_index=entry_index,
                item_kind=item_kind,
            )
            raise UnknownItemKind(
                "item_records[{0}] item_kind {1!r} is not in the bounded "
                "ITEM_KIND_TO_DECLARED_KIND mapping".format(
                    entry_index, item_kind
                )
            )

        pair = _materialize_one(item, materialized_source_id)
        source_reference_record, source_record = pair
        source_reference_records.append(source_reference_record)
        source_records.append(source_record)
        seen_source_ids.add(materialized_source_id)

        event_log.append(
            "level0_manual_seed_materialized",
            entry_index=entry_index,
            source_id=materialized_source_id,
        )

    item_ids_materialized = sorted({item["item_id"] for item in item_records})
    source_ids_materialized = sorted(seen_source_ids)

    result = {
        "materialization_kind": _MATERIALIZATION_KIND,
        "manual_seed_shape_observation": manual_seed_shape_observation,
        "source_reference_records": source_reference_records,
        "source_records": source_records,
        "source_reference_count": len(source_reference_records),
        "source_record_count": len(source_records),
        "item_ids_materialized": item_ids_materialized,
        "source_ids_materialized": source_ids_materialized,
        "candidate_route_fragment_count": 0,
        "candidate_workflow_fragment_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "materialization_note": _MATERIALIZATION_NOTE,
    }

    _assert_no_forbidden_language(result, event_log, location="result")

    event_log.append("level0_manual_seed_materialization_completed")
    return result
