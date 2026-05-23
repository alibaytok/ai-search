"""Level 0B Awesome Copilot workshop derived-material visible-trace scaffold.

WO-L0-WORKSHOP-TRACE-01 adds a scaffold-only module that combines a
derived-material observation pass and a visible-trace pass for the
Level 0B workshop seed planning document referenced by Codex (see
the workshop seed plan in `ai-search/`). The module validates
already-loaded `workshop_item_records` (70 entries across
eight bounded item kinds) and `workshop_prompt_records` (26 entries
across nine bounded categories), derives exactly one metadata-only
`derived_material_record` per item record, partitions those records
into candidate route fragments / candidate workflow fragments /
rejected material by item_kind, attaches matching derived material
per prompt by declared `expected_item_kinds_touched`, and emits a
fixed-shape visible-trace summary.

This module performs no file IO, no network call, no URL fetch /
download / crawl, no PDF text extraction, no hash computation, no
external process or external shell execution, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools.

This module invokes NO prior-WO public function. The workshop seed
is independent of the seven-source manual-seed chain; the workshop-
trace module owns its own bounded item-kind set, its own bounded
prompt-category set, and its own bounded boundary-note literal. The
seven-source manual-seed chain (WO-L0-RUN-01, WO-L0-TRACE-01,
WO-L0-MATERIAL-01, WO-L0-E2E-01) is not invoked here.

This module does NOT qualify any source, does NOT admit any source
to corpus, does NOT extract or normalize source material, does NOT
promote any record to an official route, does NOT compute any
similarity / distance / ranking / metric, and does NOT decide
architecture / vendor / library / index family / ANN backend /
reranker / retrieval family / production system.

The Constraints v1 non-claim constraint carries forward: this module
does not claim any derived material record, candidate route
fragment, candidate workflow fragment, rejected material record,
attached fragment list, ambiguity observation, or computed count is
sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded eight item kinds, the bounded
nine prompt categories, the bounded per-kind distributions, the
bounded boundary-note literal, the bounded required-field sets, and
the fixed output key set are bounded by WO-L0-WORKSHOP-TRACE-01 and
are NOT claimed exhaustive.

Public surface:

    run_level0_workshop_derived_trace(
        workshop_item_records, workshop_prompt_records, event_log
    ) -> dict

All four standard authorization / readiness / selection booleans
(`selection_made`, `measurement_authorized`,
`real_benchmark_authorized`, `real_benchmark_ready`) are literal
False on every emitted path, alongside two additional workshop
booleans (`source_qualification_authorized`,
`corpus_admission_authorized`) also literal False.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


WORKSHOP_TRACE_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
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


EXPECTED_ITEM_COUNT = 70
EXPECTED_PROMPT_COUNT = 26


EXPECTED_ITEM_KINDS = (
    "skill",
    "instruction",
    "agent",
    "workflow_file",
    "hook",
    "plugin",
    "cookbook_entry",
    "repo_meta_section",
)


EXPECTED_ITEM_KIND_DISTRIBUTION = {
    "skill": 16,
    "instruction": 12,
    "agent": 12,
    "workflow_file": 8,
    "hook": 5,
    "plugin": 4,
    "cookbook_entry": 7,
    "repo_meta_section": 6,
}


EXPECTED_PROMPT_CATEGORIES = (
    "A. clear single-intent",
    "B. workflow intent",
    "C. skill intent",
    "D. agent/persona confusion",
    "E. instruction confusion",
    "F. prompt-search-shaped but workflow-intent",
    "G. ambiguous",
    "H. no-route",
    "I. near-miss/rejection",
)


EXPECTED_PROMPT_CATEGORY_DISTRIBUTION = {
    "A. clear single-intent": 4,
    "B. workflow intent": 4,
    "C. skill intent": 3,
    "D. agent/persona confusion": 3,
    "E. instruction confusion": 3,
    "F. prompt-search-shaped but workflow-intent": 2,
    "G. ambiguous": 3,
    "H. no-route": 2,
    "I. near-miss/rejection": 2,
}


REQUIRED_ITEM_FIELDS = (
    "workshop_item_id",
    "repo_path_shape",
    "item_kind",
    "selection_locator_hint",
    "material_role",
    "expected_trace_surface",
    "boundary_note",
)


REQUIRED_PROMPT_FIELDS = (
    "workshop_prompt_id",
    "category",
    "prompt_text",
    "expected_item_kinds_touched",
    "expected_candidate_surface",
    "expected_rejection_surface",
    "boundary_note",
)


WORKSHOP_BOUNDARY_NOTE = "not admitted; not qualified; workshop metadata only"


CANDIDATE_ROUTE_KINDS = frozenset({
    "skill", "instruction", "agent", "plugin", "cookbook_entry",
})


CANDIDATE_WORKFLOW_KINDS = frozenset({
    "workflow_file", "hook",
})


REJECTED_ONLY_KINDS = frozenset({
    "repo_meta_section",
})


_REPO_META_REJECTION_REASON = "repo_meta_section_near_miss"


_NO_ROUTE_KIND_LITERAL = "none"


_AMBIGUOUS_CATEGORY = "G. ambiguous"
_NO_ROUTE_CATEGORY = "H. no-route"
_REJECTION_CATEGORY = "I. near-miss/rejection"


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


_DERIVED_MATERIAL_ID_PREFIX = "L0-WS-DER"


_WORKSHOP_TRACE_KIND = "level0_workshop_derived_trace"


_WORKSHOP_TRACE_NOTE = (
    "level0_workshop_derived_trace: a clean-pass observation over "
    "the Level 0B Awesome-Copilot workshop seed at planning-shape "
    "level only; emits exactly one metadata-only derived material "
    "record per workshop item record, partitions those records into "
    "candidate route fragments / candidate workflow fragments / "
    "rejected material by item_kind, and attaches matching derived "
    "material per prompt by declared expected_item_kinds_touched; "
    "this trace is NOT corpus admission, NOT source qualification, "
    "NOT extraction, NOT normalization, NOT a route object, NOT a "
    "Source Card, NOT permission to flip any authorization / "
    "readiness boolean, and NOT a benchmark-ready flip; OQ-003, "
    "OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, "
    "OQ-075, OQ-076 remain OPEN; no real adapter; no benchmark "
    "execution; no measurement authorization."
)


class NonListWorkshopItemRecords(Exception):
    """Raised when `workshop_item_records` is not a list."""


class NonListWorkshopPromptRecords(Exception):
    """Raised when `workshop_prompt_records` is not a list."""


class InvalidWorkshopItemRecordCount(Exception):
    """Raised when `workshop_item_records` does not contain exactly
    `EXPECTED_ITEM_COUNT` entries."""


class InvalidWorkshopPromptRecordCount(Exception):
    """Raised when `workshop_prompt_records` does not contain exactly
    `EXPECTED_PROMPT_COUNT` entries."""


class NonObjectWorkshopItemRecord(Exception):
    """Raised when an entry in `workshop_item_records` is not a dict."""


class NonObjectWorkshopPromptRecord(Exception):
    """Raised when an entry in `workshop_prompt_records` is not a dict."""


class MissingWorkshopItemRecordField(Exception):
    """Raised when a workshop item record is missing a required field."""


class MissingWorkshopPromptRecordField(Exception):
    """Raised when a workshop prompt record is missing a required field."""


class UnknownWorkshopItemRecordField(Exception):
    """Raised when a workshop item record contains a field outside the
    bounded `REQUIRED_ITEM_FIELDS` set."""


class UnknownWorkshopPromptRecordField(Exception):
    """Raised when a workshop prompt record contains a field outside the
    bounded `REQUIRED_PROMPT_FIELDS` set."""


class UnknownItemKind(Exception):
    """Raised when an item record carries an `item_kind` outside the
    bounded `EXPECTED_ITEM_KINDS` set."""


class UnknownPromptCategory(Exception):
    """Raised when a prompt record carries a `category` outside the
    bounded `EXPECTED_PROMPT_CATEGORIES` set."""


class InvalidItemKindDistribution(Exception):
    """Raised when observed per-kind counts do not match the bounded
    `EXPECTED_ITEM_KIND_DISTRIBUTION`."""


class InvalidPromptCategoryDistribution(Exception):
    """Raised when observed per-category counts do not match the bounded
    `EXPECTED_PROMPT_CATEGORY_DISTRIBUTION`."""


class DuplicateWorkshopItemId(Exception):
    """Raised when two workshop item records share a `workshop_item_id`."""


class DuplicateWorkshopPromptId(Exception):
    """Raised when two workshop prompt records share a
    `workshop_prompt_id`."""


class InvalidWorkshopItemBoundaryNoteLiteral(Exception):
    """Raised when an item record `boundary_note` does not match the
    required workshop boundary-note literal."""


class InvalidWorkshopPromptBoundaryNoteLiteral(Exception):
    """Raised when a prompt record `boundary_note` does not match the
    required workshop boundary-note literal."""


class NonListExpectedItemKindsTouched(Exception):
    """Raised when a prompt record `expected_item_kinds_touched` is not a
    list."""


class EmptyExpectedItemKindsTouched(Exception):
    """Raised when a prompt record `expected_item_kinds_touched` is an
    empty list."""


class UnknownExpectedItemKind(Exception):
    """Raised when a prompt record `expected_item_kinds_touched` contains
    a value outside the bounded `EXPECTED_ITEM_KINDS` set (or the
    literal `none` sentinel)."""


class AmbiguousPromptMissingMultipleKinds(Exception):
    """Raised when a prompt declared in category `G. ambiguous` does not
    declare at least two distinct `expected_item_kinds_touched`."""


class ForbiddenLanguageInLevel0WorkshopDerivedTrace(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in either the input or the
    emitted workshop trace report."""


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
        for phrase in WORKSHOP_TRACE_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_derived_trace_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopDerivedTrace(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_derived_trace_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopDerivedTrace(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _validate_item_records(workshop_item_records, event_log):
    """Validate workshop item records shape; halt-before-raise on error."""
    if not isinstance(workshop_item_records, list):
        event_log.halt(
            reason="level0_workshop_derived_trace_non_list_workshop_item_records"
        )
        raise NonListWorkshopItemRecords(
            "workshop_item_records must be a list"
        )

    if len(workshop_item_records) != EXPECTED_ITEM_COUNT:
        event_log.halt(
            reason="level0_workshop_derived_trace_invalid_workshop_item_record_count",
            expected=EXPECTED_ITEM_COUNT,
            observed=len(workshop_item_records),
        )
        raise InvalidWorkshopItemRecordCount(
            "workshop_item_records must contain exactly {0} entries (observed {1})".format(
                EXPECTED_ITEM_COUNT, len(workshop_item_records)
            )
        )

    seen_item_ids = set()
    item_kind_counts = {kind: 0 for kind in EXPECTED_ITEM_KINDS}

    for entry_index, record in enumerate(workshop_item_records):
        if not isinstance(record, dict):
            event_log.halt(
                reason="level0_workshop_derived_trace_non_object_workshop_item_record",
                entry_index=entry_index,
            )
            raise NonObjectWorkshopItemRecord(
                "workshop_item_records[{0}] is not a dict".format(entry_index)
            )

        for field in REQUIRED_ITEM_FIELDS:
            if field not in record:
                event_log.halt(
                    reason="level0_workshop_derived_trace_missing_workshop_item_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise MissingWorkshopItemRecordField(
                    "workshop_item_records[{0}] missing required field '{1}'".format(
                        entry_index, field
                    )
                )

        for field in record.keys():
            if field not in REQUIRED_ITEM_FIELDS:
                event_log.halt(
                    reason="level0_workshop_derived_trace_unknown_workshop_item_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise UnknownWorkshopItemRecordField(
                    "workshop_item_records[{0}] contains unknown field '{1}'".format(
                        entry_index, field
                    )
                )

        if record["boundary_note"] != WORKSHOP_BOUNDARY_NOTE:
            event_log.halt(
                reason="level0_workshop_derived_trace_invalid_workshop_item_boundary_note_literal",
                entry_index=entry_index,
            )
            raise InvalidWorkshopItemBoundaryNoteLiteral(
                "workshop_item_records[{0}] boundary_note does not match required literal".format(
                    entry_index
                )
            )

        item_kind = record["item_kind"]
        if item_kind not in EXPECTED_ITEM_KINDS:
            event_log.halt(
                reason="level0_workshop_derived_trace_unknown_item_kind",
                entry_index=entry_index,
                item_kind=item_kind,
            )
            raise UnknownItemKind(
                "workshop_item_records[{0}] has unknown item_kind '{1}'".format(
                    entry_index, item_kind
                )
            )

        workshop_item_id = record["workshop_item_id"]
        if workshop_item_id in seen_item_ids:
            event_log.halt(
                reason="level0_workshop_derived_trace_duplicate_workshop_item_id",
                entry_index=entry_index,
                workshop_item_id=workshop_item_id,
            )
            raise DuplicateWorkshopItemId(
                "workshop_item_records[{0}] duplicate workshop_item_id '{1}'".format(
                    entry_index, workshop_item_id
                )
            )
        seen_item_ids.add(workshop_item_id)
        item_kind_counts[item_kind] += 1

        event_log.append(
            "level0_workshop_item_observed",
            entry_index=entry_index,
        )

    for kind, expected in EXPECTED_ITEM_KIND_DISTRIBUTION.items():
        if item_kind_counts[kind] != expected:
            event_log.halt(
                reason="level0_workshop_derived_trace_invalid_item_kind_distribution",
                item_kind=kind,
                expected=expected,
                observed=item_kind_counts[kind],
            )
            raise InvalidItemKindDistribution(
                "item_kind '{0}' expected {1} entries (observed {2})".format(
                    kind, expected, item_kind_counts[kind]
                )
            )

    return item_kind_counts


def _validate_prompt_records(workshop_prompt_records, event_log):
    """Validate workshop prompt records shape; halt-before-raise on error."""
    if not isinstance(workshop_prompt_records, list):
        event_log.halt(
            reason="level0_workshop_derived_trace_non_list_workshop_prompt_records"
        )
        raise NonListWorkshopPromptRecords(
            "workshop_prompt_records must be a list"
        )

    if len(workshop_prompt_records) != EXPECTED_PROMPT_COUNT:
        event_log.halt(
            reason="level0_workshop_derived_trace_invalid_workshop_prompt_record_count",
            expected=EXPECTED_PROMPT_COUNT,
            observed=len(workshop_prompt_records),
        )
        raise InvalidWorkshopPromptRecordCount(
            "workshop_prompt_records must contain exactly {0} entries (observed {1})".format(
                EXPECTED_PROMPT_COUNT, len(workshop_prompt_records)
            )
        )

    seen_prompt_ids = set()
    category_counts = {cat: 0 for cat in EXPECTED_PROMPT_CATEGORIES}

    for entry_index, record in enumerate(workshop_prompt_records):
        if not isinstance(record, dict):
            event_log.halt(
                reason="level0_workshop_derived_trace_non_object_workshop_prompt_record",
                entry_index=entry_index,
            )
            raise NonObjectWorkshopPromptRecord(
                "workshop_prompt_records[{0}] is not a dict".format(entry_index)
            )

        for field in REQUIRED_PROMPT_FIELDS:
            if field not in record:
                event_log.halt(
                    reason="level0_workshop_derived_trace_missing_workshop_prompt_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise MissingWorkshopPromptRecordField(
                    "workshop_prompt_records[{0}] missing required field '{1}'".format(
                        entry_index, field
                    )
                )

        for field in record.keys():
            if field not in REQUIRED_PROMPT_FIELDS:
                event_log.halt(
                    reason="level0_workshop_derived_trace_unknown_workshop_prompt_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise UnknownWorkshopPromptRecordField(
                    "workshop_prompt_records[{0}] contains unknown field '{1}'".format(
                        entry_index, field
                    )
                )

        if record["boundary_note"] != WORKSHOP_BOUNDARY_NOTE:
            event_log.halt(
                reason="level0_workshop_derived_trace_invalid_workshop_prompt_boundary_note_literal",
                entry_index=entry_index,
            )
            raise InvalidWorkshopPromptBoundaryNoteLiteral(
                "workshop_prompt_records[{0}] boundary_note does not match required literal".format(
                    entry_index
                )
            )

        category = record["category"]
        if category not in EXPECTED_PROMPT_CATEGORIES:
            event_log.halt(
                reason="level0_workshop_derived_trace_unknown_prompt_category",
                entry_index=entry_index,
                category=category,
            )
            raise UnknownPromptCategory(
                "workshop_prompt_records[{0}] has unknown category '{1}'".format(
                    entry_index, category
                )
            )

        expected_kinds = record["expected_item_kinds_touched"]
        if not isinstance(expected_kinds, list):
            event_log.halt(
                reason="level0_workshop_derived_trace_non_list_expected_item_kinds_touched",
                entry_index=entry_index,
            )
            raise NonListExpectedItemKindsTouched(
                "workshop_prompt_records[{0}] expected_item_kinds_touched must be a list".format(
                    entry_index
                )
            )
        if len(expected_kinds) == 0:
            event_log.halt(
                reason="level0_workshop_derived_trace_empty_expected_item_kinds_touched",
                entry_index=entry_index,
            )
            raise EmptyExpectedItemKindsTouched(
                "workshop_prompt_records[{0}] expected_item_kinds_touched is empty".format(
                    entry_index
                )
            )
        for kind in expected_kinds:
            if kind == _NO_ROUTE_KIND_LITERAL:
                continue
            if kind not in EXPECTED_ITEM_KINDS:
                event_log.halt(
                    reason="level0_workshop_derived_trace_unknown_expected_item_kind",
                    entry_index=entry_index,
                    expected_item_kind=kind,
                )
                raise UnknownExpectedItemKind(
                    "workshop_prompt_records[{0}] expected_item_kinds_touched contains unknown kind '{1}'".format(
                        entry_index, kind
                    )
                )

        if category == _AMBIGUOUS_CATEGORY:
            distinct = {k for k in expected_kinds if k != _NO_ROUTE_KIND_LITERAL}
            if len(distinct) < 2:
                event_log.halt(
                    reason="level0_workshop_derived_trace_ambiguous_prompt_missing_multiple_kinds",
                    entry_index=entry_index,
                )
                raise AmbiguousPromptMissingMultipleKinds(
                    "workshop_prompt_records[{0}] ambiguous category must declare at least two distinct kinds".format(
                        entry_index
                    )
                )

        workshop_prompt_id = record["workshop_prompt_id"]
        if workshop_prompt_id in seen_prompt_ids:
            event_log.halt(
                reason="level0_workshop_derived_trace_duplicate_workshop_prompt_id",
                entry_index=entry_index,
                workshop_prompt_id=workshop_prompt_id,
            )
            raise DuplicateWorkshopPromptId(
                "workshop_prompt_records[{0}] duplicate workshop_prompt_id '{1}'".format(
                    entry_index, workshop_prompt_id
                )
            )
        seen_prompt_ids.add(workshop_prompt_id)
        category_counts[category] += 1

        event_log.append(
            "level0_workshop_prompt_observed",
            entry_index=entry_index,
        )

    for category, expected in EXPECTED_PROMPT_CATEGORY_DISTRIBUTION.items():
        if category_counts[category] != expected:
            event_log.halt(
                reason="level0_workshop_derived_trace_invalid_prompt_category_distribution",
                category=category,
                expected=expected,
                observed=category_counts[category],
            )
            raise InvalidPromptCategoryDistribution(
                "category '{0}' expected {1} entries (observed {2})".format(
                    category, expected, category_counts[category]
                )
            )

    return category_counts


def _derive_material_for_item(item_record, entry_index):
    """Build one metadata-only derived material record from item metadata."""
    derived_material_id = "{0}-{1:03d}".format(
        _DERIVED_MATERIAL_ID_PREFIX, entry_index + 1
    )
    return {
        "derived_material_id": derived_material_id,
        "workshop_item_id": item_record["workshop_item_id"],
        "item_kind": item_record["item_kind"],
        "repo_path_shape": item_record["repo_path_shape"],
        "material_role": item_record["material_role"],
        "candidate_only": True,
        "qualified": False,
        "corpus_admitted": False,
        "route_object_created": False,
        "source_material_extracted": False,
        "material_observation_basis": "workshop_metadata_only",
    }


def _partition_derived_records(derived_material_records):
    """Partition derived material into route candidates / workflow
    candidates / rejected material by item_kind. `repo_meta_section`
    is never a candidate; it appears only in rejected material with
    the literal rejection reason."""
    candidate_route = []
    candidate_workflow = []
    rejected = []
    for derived in derived_material_records:
        kind = derived["item_kind"]
        if kind in CANDIDATE_ROUTE_KINDS:
            candidate_route.append(derived)
        elif kind in CANDIDATE_WORKFLOW_KINDS:
            candidate_workflow.append(derived)
        elif kind in REJECTED_ONLY_KINDS:
            rejected.append({
                "derived_material_id": derived["derived_material_id"],
                "workshop_item_id": derived["workshop_item_id"],
                "item_kind": kind,
                "rejection_reason": _REPO_META_REJECTION_REASON,
                "candidate_only": True,
                "qualified": False,
                "corpus_admitted": False,
                "route_object_created": False,
                "source_material_extracted": False,
                "material_observation_basis": "workshop_metadata_only",
            })
    return candidate_route, candidate_workflow, rejected


def _attached_derived_for_prompt(
    expected_kinds,
    derived_by_kind,
    candidate_route_ids,
    candidate_workflow_ids,
    rejected_ids,
):
    """Attach derived material ids to a prompt by declared expected kinds.

    Returns a tuple of:
      (attached_route_ids, attached_workflow_ids, attached_rejected_ids,
       attached_kinds_observed)
    """
    attached_route = []
    attached_workflow = []
    attached_rejected = []
    attached_kinds_observed = []
    for kind in expected_kinds:
        if kind == _NO_ROUTE_KIND_LITERAL:
            continue
        derived_records_for_kind = derived_by_kind.get(kind, [])
        attached_kinds_observed.append(kind)
        for derived in derived_records_for_kind:
            material_id = derived["derived_material_id"]
            if material_id in candidate_route_ids:
                attached_route.append(material_id)
            elif material_id in candidate_workflow_ids:
                attached_workflow.append(material_id)
            elif material_id in rejected_ids:
                attached_rejected.append(material_id)
    return (
        attached_route,
        attached_workflow,
        attached_rejected,
        attached_kinds_observed,
    )


def _build_per_prompt_trace_summary(
    workshop_prompt_records,
    derived_material_records,
    candidate_route_records,
    candidate_workflow_records,
    rejected_material_records,
):
    """Build the per-prompt trace summary list, in input order."""
    derived_by_kind = {}
    for derived in derived_material_records:
        derived_by_kind.setdefault(derived["item_kind"], []).append(derived)

    candidate_route_ids = {r["derived_material_id"] for r in candidate_route_records}
    candidate_workflow_ids = {
        r["derived_material_id"] for r in candidate_workflow_records
    }
    rejected_ids = {r["derived_material_id"] for r in rejected_material_records}

    summary = []
    for record in workshop_prompt_records:
        expected_kinds = record["expected_item_kinds_touched"]
        category = record["category"]
        is_no_route = (_NO_ROUTE_KIND_LITERAL in expected_kinds)
        is_ambiguous = (category == _AMBIGUOUS_CATEGORY)
        is_rejection_category = (category == _REJECTION_CATEGORY)

        if is_no_route:
            attached_route = []
            attached_workflow = []
            attached_rejected = []
            attached_kinds_observed = []
            no_selection_reason = "prompt_out_of_repo_scope"
        else:
            (
                attached_route,
                attached_workflow,
                attached_rejected,
                attached_kinds_observed,
            ) = _attached_derived_for_prompt(
                expected_kinds,
                derived_by_kind,
                candidate_route_ids,
                candidate_workflow_ids,
                rejected_ids,
            )
            if is_rejection_category and not attached_route and not attached_workflow:
                no_selection_reason = _REPO_META_REJECTION_REASON
            else:
                no_selection_reason = "no_forced_selection"

        entry = {
            "workshop_prompt_id": record["workshop_prompt_id"],
            "category": category,
            "expected_item_kinds_touched": list(expected_kinds),
            "attached_kinds_observed": attached_kinds_observed,
            "attached_candidate_route_fragment_ids": attached_route,
            "attached_candidate_workflow_fragment_ids": attached_workflow,
            "attached_rejected_material_ids": attached_rejected,
            "attached_candidate_route_fragment_count": len(attached_route),
            "attached_candidate_workflow_fragment_count": len(attached_workflow),
            "attached_rejected_material_count": len(attached_rejected),
            "ambiguity_observed": is_ambiguous,
            "no_selection_reason": no_selection_reason,
            "route_selection_made": False,
            "candidate_only": True,
        }
        summary.append(entry)
    return summary


def _assert_no_route_status_fields(result, event_log):
    """Defensive check: no record in the result carries any route-status
    field set to a True value. The module never produces such fields,
    but this verifies the output before returning."""
    def _check(record, location):
        if not isinstance(record, dict):
            return
        for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
            if field in record:
                event_log.halt(
                    reason="level0_workshop_derived_trace_route_status_field_present",
                    location=location,
                    field=field,
                )
                raise ForbiddenLanguageInLevel0WorkshopDerivedTrace(
                    "Route-status field '{0}' present in {1}".format(
                        field, location
                    )
                )

    for derived in result["derived_material_records"]:
        _check(derived, "derived_material_records")
    for rec in result["candidate_route_fragment_records"]:
        _check(rec, "candidate_route_fragment_records")
    for rec in result["candidate_workflow_fragment_records"]:
        _check(rec, "candidate_workflow_fragment_records")
    for rec in result["rejected_material_records"]:
        _check(rec, "rejected_material_records")
    for rec in result["per_prompt_trace_summary"]:
        _check(rec, "per_prompt_trace_summary")


def run_level0_workshop_derived_trace(
    workshop_item_records, workshop_prompt_records, event_log
):
    """Validate the Level 0B workshop seed shape, derive metadata-only
    material observations, attach those observations per prompt by
    declared expected item kinds, and emit a fixed-shape visible trace
    summary dict.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_workshop_derived_trace_started")

    _assert_no_forbidden_language(
        workshop_item_records, event_log, location="workshop_item_records"
    )
    _assert_no_forbidden_language(
        workshop_prompt_records, event_log, location="workshop_prompt_records"
    )

    _validate_item_records(workshop_item_records, event_log)
    _validate_prompt_records(workshop_prompt_records, event_log)

    derived_material_records = []
    for entry_index, record in enumerate(workshop_item_records):
        derived = _derive_material_for_item(record, entry_index)
        derived_material_records.append(derived)
        event_log.append(
            "level0_workshop_derived_material_built",
            entry_index=entry_index,
            derived_material_id=derived["derived_material_id"],
        )

    (
        candidate_route_records,
        candidate_workflow_records,
        rejected_material_records,
    ) = _partition_derived_records(derived_material_records)

    per_prompt_trace_summary = _build_per_prompt_trace_summary(
        workshop_prompt_records,
        derived_material_records,
        candidate_route_records,
        candidate_workflow_records,
        rejected_material_records,
    )

    result = {
        "workshop_trace_kind": _WORKSHOP_TRACE_KIND,
        "item_count": len(workshop_item_records),
        "prompt_count": len(workshop_prompt_records),
        "derived_material_records": derived_material_records,
        "derived_material_count": len(derived_material_records),
        "candidate_route_fragment_records": candidate_route_records,
        "candidate_route_fragment_count": len(candidate_route_records),
        "candidate_workflow_fragment_records": candidate_workflow_records,
        "candidate_workflow_fragment_count": len(candidate_workflow_records),
        "rejected_material_records": rejected_material_records,
        "rejected_material_count": len(rejected_material_records),
        "per_prompt_trace_summary": per_prompt_trace_summary,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "workshop_trace_note": _WORKSHOP_TRACE_NOTE,
    }

    _assert_no_route_status_fields(result, event_log)
    _assert_no_forbidden_language(result, event_log, location="result")

    event_log.append("level0_workshop_derived_trace_completed")
    return result
