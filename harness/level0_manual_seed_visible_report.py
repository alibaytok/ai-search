"""Level 0B manual seed visible report scaffold.

WO-L0-RUN-01 adds a scaffold-only Level 0B runner that accepts
already-loaded manual seed item records and synthetic prompt records,
validates their shape against the WO-L0-ITEMS-01 planning artifacts
(`ai-search/00-level0-item-selection.md` and
`ai-search/00-level0-prompt-set.md`), and emits a fixed-shape Level
0B visible test report.

This module does NOT read any file. It does NOT make any network
call. It does NOT fetch, download, or crawl any URL. It does NOT
extract PDF text. It does NOT invoke any prior-WO public function
(verified by static-scan tests). It does NOT integrate with any
editor extension, chat plugin, third-party model API, or external
collaborator tool. It does NOT spawn external processes or external
shells. It does NOT compute hashes.

This module does NOT qualify any source, does NOT admit any source
to corpus, does NOT extract source material, does NOT normalize
source material, does NOT derive candidate route or candidate
workflow fragments, does NOT promote any record to an official
route, and does NOT decide architecture / vendor / library / index
family / ANN backend / reranker / retrieval family / production
system.

The Constraints v1 non-claim constraint carries forward: this module
does not claim any record, count, observed source identifier,
observed prompt category, or computed expected-count is sufficient,
necessary, superior, best, complete, production-ready, recommended,
or selected. The bounded expected-source-id set, the bounded
expected-prompt-category set, the required item / prompt field sets,
the boundary-note literal, and the fixed output key set are bounded
by WO-L0-RUN-01 and are NOT claimed exhaustive.

Public surface:

    run_level0_manual_seed_visible_report(
        item_records, prompt_records, event_log
    ) -> dict

The clean-pass output dict has exactly fifteen allowed keys in
`ALLOWED_OUTPUT_KEYS`. All four standard authorization / readiness /
selection booleans (`selection_made`, `measurement_authorized`,
`real_benchmark_authorized`, `real_benchmark_ready`) are literal
False on every emitted path.

`manual_seed_ready_for_visible_trace` is a planning-readiness flag.
It may be True only when shape validation passes. It does NOT mean
benchmark-ready. It does NOT mean source-qualified. It does NOT
mean corpus-admitted. It does NOT mean route-selected. It is a
planning observation only.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


REPORT_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "report_kind",
    "item_count",
    "prompt_count",
    "source_ids_observed",
    "prompt_categories_observed",
    "expected_workflow_prompt_count",
    "expected_near_miss_prompt_count",
    "expected_no_route_prompt_count",
    "expected_ambiguous_prompt_count",
    "manual_seed_ready_for_visible_trace",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "report_note",
)


EXPECTED_ITEM_COUNT = 65
EXPECTED_PROMPT_COUNT = 23


EXPECTED_SOURCE_IDS = (
    "L0-SRC-001",
    "L0-SRC-002",
    "L0-SRC-003",
    "L0-SRC-004",
    "L0-SRC-005",
    "L0-SRC-006",
    "L0-SRC-007",
)


EXPECTED_PROMPT_CATEGORIES = (
    "A. clear single-intent",
    "B. multi-intent",
    "C. ambiguous",
    "D. prompt-search-shaped that should become workflow / route intent",
    "E. no-route",
    "F. refusal / no-selection",
    "G. multi-source-touching",
    "H. near-miss involving L0-SRC-007",
    "I. workflow involving L0-SRC-006",
)


REQUIRED_ITEM_FIELDS = (
    "item_id",
    "source_id",
    "item_kind",
    "item_title_or_anchor",
    "item_locator",
    "intended_test_role",
    "boundary_notes",
)


REQUIRED_PROMPT_FIELDS = (
    "prompt_id",
    "category",
    "prompt_text",
    "expected_behavior_summary",
    "expected_source_touch",
    "expected_candidate_shape",
    "expected_rejection_targets",
)


ITEM_BOUNDARY_NOTE = "not admitted; not qualified; link-level/manual-seed only"


_WORKFLOW_CATEGORY = "I. workflow involving L0-SRC-006"
_NEAR_MISS_CATEGORY = "H. near-miss involving L0-SRC-007"
_NO_ROUTE_CATEGORY = "E. no-route"
_AMBIGUOUS_CATEGORY = "C. ambiguous"


_REPORT_KIND = "level0_manual_seed_visible_report"


_REPORT_NOTE = (
    "level0_manual_seed_visible_report: a clean-pass observation "
    "over the WO-L0-ITEMS-01 manual seed item table and the manual "
    "seed prompt table at planning-shape level only; this report is "
    "NOT corpus admission, NOT source qualification, NOT extraction, "
    "NOT normalization, NOT candidate-fragment derivation, NOT a "
    "route object, NOT a Source Card, NOT permission to invoke any "
    "prior-WO public function, NOT permission to flip any "
    "authorization / readiness boolean; OQ-003, OQ-015, OQ-031, "
    "OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 "
    "remain OPEN; no real adapter; no benchmark execution; no "
    "measurement authorization."
)


class NonListItemRecords(Exception):
    """Raised when `item_records` is not a list."""


class NonListPromptRecords(Exception):
    """Raised when `prompt_records` is not a list."""


class InvalidItemRecordCount(Exception):
    """Raised when `item_records` does not contain exactly
    `EXPECTED_ITEM_COUNT` entries."""


class InvalidPromptRecordCount(Exception):
    """Raised when `prompt_records` does not contain exactly
    `EXPECTED_PROMPT_COUNT` entries."""


class NonObjectItemRecord(Exception):
    """Raised when an entry in `item_records` is not a dict."""


class NonObjectPromptRecord(Exception):
    """Raised when an entry in `prompt_records` is not a dict."""


class MissingItemRecordField(Exception):
    """Raised when an item record is missing a required field."""


class MissingPromptRecordField(Exception):
    """Raised when a prompt record is missing a required field."""


class UnknownItemRecordField(Exception):
    """Raised when an item record contains a field outside the bounded
    `REQUIRED_ITEM_FIELDS` set."""


class UnknownPromptRecordField(Exception):
    """Raised when a prompt record contains a field outside the bounded
    `REQUIRED_PROMPT_FIELDS` set."""


class InvalidItemBoundaryNoteLiteral(Exception):
    """Raised when an item record's `boundary_notes` value does not
    match the required boundary-note literal."""


class UnknownSourceId(Exception):
    """Raised when an item record carries a `source_id` outside the
    bounded `EXPECTED_SOURCE_IDS` set."""


class UnknownPromptCategory(Exception):
    """Raised when a prompt record carries a `category` outside the
    bounded `EXPECTED_PROMPT_CATEGORIES` set."""


class MissingSourceIdCoverage(Exception):
    """Raised when the union of observed `source_id` values does not
    cover the bounded `EXPECTED_SOURCE_IDS` set."""


class MissingPromptCategoryCoverage(Exception):
    """Raised when the union of observed `category` values does not
    cover the bounded `EXPECTED_PROMPT_CATEGORIES` set."""


class ForbiddenLanguageInLevel0ManualSeedReport(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in either the input or the
    emitted report."""


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
        for phrase in REPORT_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_manual_seed_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0ManualSeedReport(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_manual_seed_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0ManualSeedReport(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def run_level0_manual_seed_visible_report(
    item_records, prompt_records, event_log
):
    """Validate the WO-L0-ITEMS-01 manual seed shape and emit a
    fixed-shape Level 0B visible report dict.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_manual_seed_visible_report_started")

    if not isinstance(item_records, list):
        event_log.halt(reason="level0_manual_seed_non_list_item_records")
        raise NonListItemRecords(
            "item_records must be a list"
        )

    if not isinstance(prompt_records, list):
        event_log.halt(reason="level0_manual_seed_non_list_prompt_records")
        raise NonListPromptRecords(
            "prompt_records must be a list"
        )

    if len(item_records) != EXPECTED_ITEM_COUNT:
        event_log.halt(
            reason="level0_manual_seed_invalid_item_record_count",
            expected=EXPECTED_ITEM_COUNT,
            observed=len(item_records),
        )
        raise InvalidItemRecordCount(
            "item_records must contain exactly {0} entries (observed {1})".format(
                EXPECTED_ITEM_COUNT, len(item_records)
            )
        )

    if len(prompt_records) != EXPECTED_PROMPT_COUNT:
        event_log.halt(
            reason="level0_manual_seed_invalid_prompt_record_count",
            expected=EXPECTED_PROMPT_COUNT,
            observed=len(prompt_records),
        )
        raise InvalidPromptRecordCount(
            "prompt_records must contain exactly {0} entries (observed {1})".format(
                EXPECTED_PROMPT_COUNT, len(prompt_records)
            )
        )

    for entry_index, record in enumerate(item_records):
        if not isinstance(record, dict):
            event_log.halt(
                reason="level0_manual_seed_non_object_item_record",
                entry_index=entry_index,
            )
            raise NonObjectItemRecord(
                "item_records[{0}] is not a dict".format(entry_index)
            )
        for field in REQUIRED_ITEM_FIELDS:
            if field not in record:
                event_log.halt(
                    reason="level0_manual_seed_missing_item_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise MissingItemRecordField(
                    "item_records[{0}] missing required field '{1}'".format(
                        entry_index, field
                    )
                )
        for field in record:
            if field not in REQUIRED_ITEM_FIELDS:
                event_log.halt(
                    reason="level0_manual_seed_unknown_item_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise UnknownItemRecordField(
                    "item_records[{0}] contains unknown field '{1}'".format(
                        entry_index, field
                    )
                )
        if record["boundary_notes"] != ITEM_BOUNDARY_NOTE:
            event_log.halt(
                reason="level0_manual_seed_invalid_item_boundary_note_literal",
                entry_index=entry_index,
            )
            raise InvalidItemBoundaryNoteLiteral(
                "item_records[{0}] boundary_notes does not match the required literal".format(
                    entry_index
                )
            )
        if record["source_id"] not in EXPECTED_SOURCE_IDS:
            event_log.halt(
                reason="level0_manual_seed_unknown_source_id",
                entry_index=entry_index,
                source_id_observed=record["source_id"],
            )
            raise UnknownSourceId(
                "item_records[{0}] has unknown source_id".format(entry_index)
            )
        event_log.append(
            "level0_manual_seed_item_observed",
            entry_index=entry_index,
        )

    for entry_index, record in enumerate(prompt_records):
        if not isinstance(record, dict):
            event_log.halt(
                reason="level0_manual_seed_non_object_prompt_record",
                entry_index=entry_index,
            )
            raise NonObjectPromptRecord(
                "prompt_records[{0}] is not a dict".format(entry_index)
            )
        for field in REQUIRED_PROMPT_FIELDS:
            if field not in record:
                event_log.halt(
                    reason="level0_manual_seed_missing_prompt_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise MissingPromptRecordField(
                    "prompt_records[{0}] missing required field '{1}'".format(
                        entry_index, field
                    )
                )
        for field in record:
            if field not in REQUIRED_PROMPT_FIELDS:
                event_log.halt(
                    reason="level0_manual_seed_unknown_prompt_record_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise UnknownPromptRecordField(
                    "prompt_records[{0}] contains unknown field '{1}'".format(
                        entry_index, field
                    )
                )
        if record["category"] not in EXPECTED_PROMPT_CATEGORIES:
            event_log.halt(
                reason="level0_manual_seed_unknown_prompt_category",
                entry_index=entry_index,
                category_observed=record["category"],
            )
            raise UnknownPromptCategory(
                "prompt_records[{0}] has unknown category".format(entry_index)
            )
        event_log.append(
            "level0_manual_seed_prompt_observed",
            entry_index=entry_index,
        )

    observed_source_id_set = set()
    for record in item_records:
        observed_source_id_set.add(record["source_id"])
    if observed_source_id_set != set(EXPECTED_SOURCE_IDS):
        event_log.halt(reason="level0_manual_seed_missing_source_id_coverage")
        raise MissingSourceIdCoverage(
            "item_records do not cover all expected source identifiers"
        )

    observed_category_set = set()
    for record in prompt_records:
        observed_category_set.add(record["category"])
    if observed_category_set != set(EXPECTED_PROMPT_CATEGORIES):
        event_log.halt(reason="level0_manual_seed_missing_prompt_category_coverage")
        raise MissingPromptCategoryCoverage(
            "prompt_records do not cover all expected categories"
        )

    category_counts = {category: 0 for category in EXPECTED_PROMPT_CATEGORIES}
    for record in prompt_records:
        category_counts[record["category"]] += 1

    _assert_no_forbidden_language(
        item_records, event_log, location="item_records"
    )
    _assert_no_forbidden_language(
        prompt_records, event_log, location="prompt_records"
    )

    result = {
        "report_kind": _REPORT_KIND,
        "item_count": len(item_records),
        "prompt_count": len(prompt_records),
        "source_ids_observed": sorted(observed_source_id_set),
        "prompt_categories_observed": sorted(observed_category_set),
        "expected_workflow_prompt_count": category_counts[_WORKFLOW_CATEGORY],
        "expected_near_miss_prompt_count": category_counts[_NEAR_MISS_CATEGORY],
        "expected_no_route_prompt_count": category_counts[_NO_ROUTE_CATEGORY],
        "expected_ambiguous_prompt_count": category_counts[_AMBIGUOUS_CATEGORY],
        "manual_seed_ready_for_visible_trace": True,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "report_note": _REPORT_NOTE,
    }

    _assert_no_forbidden_language(result, event_log, location="result")

    event_log.append("level0_manual_seed_visible_report_completed")
    return result
