"""Level 0B manual seed visible trace execution scaffold.

WO-L0-TRACE-01 adds a scaffold-only Level 0B runner that:

1. Validates the manual seed item-record and prompt-record shape by
   delegating to `harness.level0_manual_seed_visible_report.
   run_level0_manual_seed_visible_report` (WO-L0-RUN-01). If that
   delegate raises, this module short-circuits before any WO-59
   visible-report call is made.
2. For each already-loaded `trace_case_record`, executes one WO-59
   visible-report observation by delegating to
   `harness.scaffold_source_intake_visible_report.
   run_scaffold_source_intake_visible_report` (WO-59).

This module performs no file IO, no network call, no URL fetch /
download / crawl, no PDF text extraction, no hash computation, no
external process or external shell execution, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools.

This module invokes only two prior-WO public functions:
`run_level0_manual_seed_visible_report` and
`run_scaffold_source_intake_visible_report`. It does NOT invoke
WO-50, WO-51, WO-52, WO-53, WO-54, WO-55, WO-56, WO-57, WO-58,
WO-60, WO-61, or WO-62 public functions (verified by static-scan
test).

This module does NOT qualify any source, does NOT admit any source
to corpus, does NOT extract or normalize source material, does NOT
derive candidate route or candidate workflow fragments outside what
WO-59 already produces, does NOT promote any record to an official
route, does NOT compute any similarity / distance / ranking /
scoring / metric, and does NOT decide architecture / vendor /
library / index family / ANN backend / reranker / retrieval family
/ production system.

The Constraints v1 non-claim constraint carries forward: this
module does not claim any trace case, embedded visible report,
observed prompt identifier, observed category count, or computed
review-halt count is sufficient, necessary, superior, best,
complete, production-ready, recommended, or selected. The bounded
required-trace-case field set, the bounded boundary-note literal,
and the fixed output key set are bounded by WO-L0-TRACE-01 and are
NOT claimed exhaustive.

Public surface:

    run_level0_manual_seed_trace_execution(
        item_records, prompt_records, trace_case_records, event_log
    ) -> dict

The clean-pass output dict has exactly thirteen allowed keys in
`ALLOWED_OUTPUT_KEYS`. All four standard authorization / readiness
/ selection booleans are literal False on every emitted path
regardless of how many embedded WO-59 reports carry
`review_halt_required: True`.
"""

from harness.level0_manual_seed_visible_report import (
    run_level0_manual_seed_visible_report,
)
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_source_intake_visible_report import (
    run_scaffold_source_intake_visible_report,
)


TRACE_EXECUTION_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "execution_kind",
    "manual_seed_shape_observation",
    "trace_case_count",
    "prompt_ids_executed",
    "category_counts",
    "visible_reports",
    "visible_report_count",
    "review_halt_required_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "execution_note",
)


EXPECTED_TRACE_CASE_COUNT = 23


REQUIRED_TRACE_CASE_FIELDS = (
    "case_id",
    "prompt_id",
    "expected_category",
    "input_prompt",
    "source_reference_records",
    "source_records",
    "expected_source_touch",
    "expected_candidate_shape",
    "expected_rejection_targets",
    "boundary_notes",
)

_REQUIRED_TRACE_CASE_FIELD_SET = frozenset(REQUIRED_TRACE_CASE_FIELDS)


TRACE_CASE_BOUNDARY_NOTE = (
    "not admitted; not qualified; manual-seed trace only"
)


_EXPECTED_PROMPT_CATEGORIES = (
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


_EXECUTION_KIND = "level0_manual_seed_trace_execution"


_EXECUTION_NOTE = (
    "level0_manual_seed_trace_execution: a clean-pass execution that "
    "delegates manual seed shape validation to the WO-L0-RUN-01 "
    "scaffold and emits one WO-59 visible-report observation per "
    "trace case; this execution is NOT corpus admission, NOT source "
    "qualification, NOT extraction, NOT normalization, NOT "
    "candidate-fragment derivation beyond what WO-59 already "
    "produces, NOT a route object, NOT a Source Card, NOT permission "
    "to flip any authorization / readiness boolean, and NOT a "
    "benchmark-ready flip; OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, "
    "OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN; no "
    "real adapter; no benchmark execution; no measurement "
    "authorization."
)


class NonListTraceCaseRecords(Exception):
    """Raised when `trace_case_records` is not a list."""


class InvalidTraceCaseCount(Exception):
    """Raised when `trace_case_records` does not contain exactly
    `EXPECTED_TRACE_CASE_COUNT` entries."""


class NonObjectTraceCaseRecord(Exception):
    """Raised when an entry in `trace_case_records` is not a dict."""


class MissingTraceCaseField(Exception):
    """Raised when a trace case record is missing a required field."""


class UnknownTraceCaseField(Exception):
    """Raised when a trace case record carries a field outside the
    bounded `REQUIRED_TRACE_CASE_FIELDS` set."""


class InvalidCaseIdValue(Exception):
    """Raised when `case_id` is not a non-empty string."""


class DuplicateCaseId(Exception):
    """Raised when two trace case records share a `case_id`."""


class UnknownPromptIdReference(Exception):
    """Raised when a trace case `prompt_id` is not present in
    `prompt_records`."""


class DuplicatePromptIdReference(Exception):
    """Raised when two trace case records reference the same
    `prompt_id`."""


class TraceCaseCategoryMismatch(Exception):
    """Raised when a trace case `expected_category` does not match the
    referenced prompt record's `category`."""


class TraceCaseInputPromptMismatch(Exception):
    """Raised when a trace case `input_prompt` does not match the
    referenced prompt record's `prompt_text`."""


class InvalidTraceCaseBoundaryNoteLiteral(Exception):
    """Raised when a trace case `boundary_notes` value does not match
    the required boundary-note literal."""


class NonListCaseSourceReferenceRecords(Exception):
    """Raised when a trace case `source_reference_records` is not a list."""


class NonListCaseSourceRecords(Exception):
    """Raised when a trace case `source_records` is not a list."""


class MissingTraceCasePromptIdCoverage(Exception):
    """Raised when the union of observed `prompt_id` references does not
    cover every `prompt_id` in `prompt_records`."""


class MissingTraceCaseCategoryCoverage(Exception):
    """Raised when the trace cases do not cover every Level 0B
    category."""


class ForbiddenLanguageInLevel0ManualSeedTraceExecution(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in either the input trace case
    records or the emitted execution report."""


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
        for phrase in TRACE_EXECUTION_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_manual_seed_trace_execution_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0ManualSeedTraceExecution(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_manual_seed_trace_execution_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0ManualSeedTraceExecution(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def run_level0_manual_seed_trace_execution(
    item_records, prompt_records, trace_case_records, event_log
):
    """Validate the manual seed shape and emit one WO-59 visible
    report per Level 0B trace case.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_manual_seed_trace_execution_started")

    # Phase 1: delegate to WO-L0-RUN-01 for manual seed shape
    # validation. If this delegate raises, control never reaches the
    # trace-case validation below or the WO-59 invocation below; the
    # execution short-circuits before any visible report is produced.
    manual_seed_shape_observation = run_level0_manual_seed_visible_report(
        item_records, prompt_records, event_log
    )

    # Phase 2: validate trace_case_records type and count.
    if not isinstance(trace_case_records, list):
        event_log.halt(
            reason="level0_manual_seed_trace_non_list_trace_case_records"
        )
        raise NonListTraceCaseRecords(
            "trace_case_records must be a list"
        )

    if len(trace_case_records) != EXPECTED_TRACE_CASE_COUNT:
        event_log.halt(
            reason="level0_manual_seed_trace_invalid_trace_case_count",
            expected=EXPECTED_TRACE_CASE_COUNT,
            observed=len(trace_case_records),
        )
        raise InvalidTraceCaseCount(
            "trace_case_records must contain exactly {0} entries (observed {1})".format(
                EXPECTED_TRACE_CASE_COUNT, len(trace_case_records)
            )
        )

    # Build prompt lookup. `prompt_records` was validated by the
    # delegate above; we trust its shape.
    prompt_lookup = {
        record["prompt_id"]: record for record in prompt_records
    }
    all_prompt_id_set = set(prompt_lookup.keys())

    # Phase 3: per-trace-case validation.
    case_ids_seen = set()
    prompt_ids_seen = set()
    category_counts = {category: 0 for category in _EXPECTED_PROMPT_CATEGORIES}

    for entry_index, case in enumerate(trace_case_records):
        if not isinstance(case, dict):
            event_log.halt(
                reason="level0_manual_seed_trace_non_object_trace_case_record",
                entry_index=entry_index,
            )
            raise NonObjectTraceCaseRecord(
                "trace_case_records[{0}] is not a dict".format(entry_index)
            )

        for field in REQUIRED_TRACE_CASE_FIELDS:
            if field not in case:
                event_log.halt(
                    reason="level0_manual_seed_trace_missing_trace_case_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise MissingTraceCaseField(
                    "trace_case_records[{0}] missing required field '{1}'".format(
                        entry_index, field
                    )
                )

        for field in case.keys():
            if field not in _REQUIRED_TRACE_CASE_FIELD_SET:
                event_log.halt(
                    reason="level0_manual_seed_trace_unknown_trace_case_field",
                    entry_index=entry_index,
                    field=field,
                )
                raise UnknownTraceCaseField(
                    "trace_case_records[{0}] carries unknown field '{1}'".format(
                        entry_index, field
                    )
                )

        case_id = case["case_id"]
        if not isinstance(case_id, str) or case_id == "":
            event_log.halt(
                reason="level0_manual_seed_trace_invalid_case_id_value",
                entry_index=entry_index,
            )
            raise InvalidCaseIdValue(
                "trace_case_records[{0}] case_id must be a non-empty string".format(
                    entry_index
                )
            )
        if case_id in case_ids_seen:
            event_log.halt(
                reason="level0_manual_seed_trace_duplicate_case_id",
                entry_index=entry_index,
                case_id=case_id,
            )
            raise DuplicateCaseId(
                "trace_case_records[{0}] duplicate case_id".format(entry_index)
            )
        case_ids_seen.add(case_id)

        prompt_id = case["prompt_id"]
        if prompt_id not in prompt_lookup:
            event_log.halt(
                reason="level0_manual_seed_trace_unknown_prompt_id_reference",
                entry_index=entry_index,
                prompt_id=prompt_id,
            )
            raise UnknownPromptIdReference(
                "trace_case_records[{0}] references unknown prompt_id".format(
                    entry_index
                )
            )
        if prompt_id in prompt_ids_seen:
            event_log.halt(
                reason="level0_manual_seed_trace_duplicate_prompt_id_reference",
                entry_index=entry_index,
                prompt_id=prompt_id,
            )
            raise DuplicatePromptIdReference(
                "trace_case_records[{0}] duplicate prompt_id reference".format(
                    entry_index
                )
            )
        prompt_ids_seen.add(prompt_id)

        prompt_record = prompt_lookup[prompt_id]

        if case["expected_category"] != prompt_record["category"]:
            event_log.halt(
                reason="level0_manual_seed_trace_category_mismatch",
                entry_index=entry_index,
                prompt_id=prompt_id,
            )
            raise TraceCaseCategoryMismatch(
                "trace_case_records[{0}] expected_category does not match referenced prompt".format(
                    entry_index
                )
            )

        if case["input_prompt"] != prompt_record["prompt_text"]:
            event_log.halt(
                reason="level0_manual_seed_trace_input_prompt_mismatch",
                entry_index=entry_index,
                prompt_id=prompt_id,
            )
            raise TraceCaseInputPromptMismatch(
                "trace_case_records[{0}] input_prompt does not match referenced prompt_text".format(
                    entry_index
                )
            )

        if case["boundary_notes"] != TRACE_CASE_BOUNDARY_NOTE:
            event_log.halt(
                reason="level0_manual_seed_trace_invalid_boundary_note_literal",
                entry_index=entry_index,
            )
            raise InvalidTraceCaseBoundaryNoteLiteral(
                "trace_case_records[{0}] boundary_notes does not match the required literal".format(
                    entry_index
                )
            )

        if not isinstance(case["source_reference_records"], list):
            event_log.halt(
                reason="level0_manual_seed_trace_non_list_case_source_reference_records",
                entry_index=entry_index,
            )
            raise NonListCaseSourceReferenceRecords(
                "trace_case_records[{0}] source_reference_records must be a list".format(
                    entry_index
                )
            )

        if not isinstance(case["source_records"], list):
            event_log.halt(
                reason="level0_manual_seed_trace_non_list_case_source_records",
                entry_index=entry_index,
            )
            raise NonListCaseSourceRecords(
                "trace_case_records[{0}] source_records must be a list".format(
                    entry_index
                )
            )

        category_counts[prompt_record["category"]] += 1
        event_log.append(
            "level0_manual_seed_trace_case_validated",
            entry_index=entry_index,
            case_id=case_id,
            prompt_id=prompt_id,
        )

    # Phase 4: coverage checks.
    if prompt_ids_seen != all_prompt_id_set:
        event_log.halt(
            reason="level0_manual_seed_trace_missing_prompt_id_coverage"
        )
        raise MissingTraceCasePromptIdCoverage(
            "trace_case_records do not cover every prompt_id from prompt_records"
        )

    missing_categories = [
        category for category, count in category_counts.items() if count == 0
    ]
    if missing_categories:
        event_log.halt(
            reason="level0_manual_seed_trace_missing_category_coverage"
        )
        raise MissingTraceCaseCategoryCoverage(
            "trace_case_records do not cover every Level 0B category"
        )

    # Forbidden-language scan on input trace cases (defense-in-depth).
    _assert_no_forbidden_language(
        trace_case_records, event_log, location="trace_case_records"
    )

    # Phase 5: execute WO-59 visible report per trace case.
    visible_reports = []
    review_halt_required_count = 0
    for case in trace_case_records:
        report = run_scaffold_source_intake_visible_report(
            case["input_prompt"],
            case["source_reference_records"],
            case["source_records"],
            event_log,
        )
        visible_reports.append(report)
        if report["review_halt_required"]:
            review_halt_required_count += 1
        event_log.append(
            "level0_manual_seed_visible_report_emitted",
            case_id=case["case_id"],
        )

    # Build result.
    result = {
        "execution_kind": _EXECUTION_KIND,
        "manual_seed_shape_observation": manual_seed_shape_observation,
        "trace_case_count": len(trace_case_records),
        "prompt_ids_executed": sorted(prompt_ids_seen),
        "category_counts": dict(category_counts),
        "visible_reports": visible_reports,
        "visible_report_count": len(visible_reports),
        "review_halt_required_count": review_halt_required_count,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "execution_note": _EXECUTION_NOTE,
    }

    # Output forbidden-language scan.
    _assert_no_forbidden_language(result, event_log, location="result")

    event_log.append("level0_manual_seed_trace_execution_completed")
    return result
