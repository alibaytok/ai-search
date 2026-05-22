"""Consolidated Level 0B manual seed end-to-end visible trace scaffold.

WO-L0-E2E-01 wires the already-approved Level 0B manual seed
pieces into a single callable flow:

    item_records + prompt_records
      -> run_level0_manual_seed_materialization  (WO-L0-MATERIAL-01)
      -> auto-built trace_case_records with non-empty
         source_reference_records / source_records attached
      -> run_level0_manual_seed_trace_execution  (WO-L0-TRACE-01)
      -> aggregate per-prompt visible trace summary

This module performs no file IO, no network call, no URL fetch /
download / crawl / browser automation, no PDF text extraction, no
hash computation, and no external process spawning.

This module invokes only two prior-WO public functions:
`run_level0_manual_seed_materialization` and
`run_level0_manual_seed_trace_execution`. It does NOT directly
invoke the WO-54 trace, WO-55 register, WO-56 bridge, WO-57 smoke
package, WO-58 diagnostic reporter, or WO-59 visible-report public
functions (verified by static-scan test). WO-59 is reached
transitively via WO-L0-TRACE-01, by design.

This module does NOT qualify any source, does NOT admit any source
to corpus, does NOT extract or normalize source material, does NOT
invent candidate route or candidate workflow fragments (the totals
reported here are taken verbatim from the WO-59 reports embedded by
WO-L0-TRACE-01), does NOT promote any record to an official route,
does NOT compute any similarity / distance / ranking / scoring /
metric, and does NOT decide architecture / vendor / library / index
family / ANN backend / reranker / retrieval family / production
system.

The Constraints v1 non-claim constraint carries forward: this
module does not claim any consolidated observation, attached source
subset, per-prompt summary record, computed total, or aggregate
count is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected. The bounded required
materialization output keys, the bounded required trace-execution
output keys, the per-prompt summary shape, and the fixed aggregate
output key set are bounded by WO-L0-E2E-01 and are NOT claimed
exhaustive.

Public surface:

    run_level0_manual_seed_end_to_end_trace(
        item_records, prompt_records, event_log
    ) -> dict
"""

from harness.level0_manual_seed_materialization import (
    run_level0_manual_seed_materialization,
)
from harness.level0_manual_seed_trace_execution import (
    run_level0_manual_seed_trace_execution,
)
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


END_TO_END_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "end_to_end_kind",
    "materialization_observation",
    "trace_execution_observation",
    "trace_case_count",
    "source_reference_count",
    "source_record_count",
    "visible_report_count",
    "per_prompt_trace_summary",
    "candidate_route_fragment_total",
    "candidate_workflow_fragment_total",
    "review_halt_required_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "end_to_end_note",
)


_REQUIRED_MATERIALIZATION_KEYS = (
    "manual_seed_shape_observation",
    "source_reference_records",
    "source_records",
    "source_reference_count",
    "source_record_count",
)


_REQUIRED_TRACE_EXECUTION_KEYS = (
    "manual_seed_shape_observation",
    "trace_case_count",
    "visible_reports",
    "visible_report_count",
    "review_halt_required_count",
)


_EXPECTED_SOURCE_IDS = (
    "L0-SRC-001",
    "L0-SRC-002",
    "L0-SRC-003",
    "L0-SRC-004",
    "L0-SRC-005",
    "L0-SRC-006",
    "L0-SRC-007",
)


_TRACE_CASE_BOUNDARY_NOTE = (
    "not admitted; not qualified; manual-seed trace only"
)


_CASE_ID_PREFIX = "L0-E2E-CASE"


_END_TO_END_KIND = "level0_manual_seed_end_to_end_trace"


_END_TO_END_NOTE = (
    "level0_manual_seed_end_to_end_trace: a clean-pass observation "
    "that consolidates the WO-L0-MATERIAL-01 source record "
    "materialization and the WO-L0-TRACE-01 trace execution into a "
    "single visible-trace flow over the already-loaded Level 0B "
    "manual seed; this consolidation is NOT real indexing, NOT "
    "real retrieval, NOT source qualification, NOT corpus admission, "
    "NOT extraction, NOT normalization, NOT candidate-fragment "
    "invention, NOT a route object, NOT a Source Card, NOT "
    "permission to flip any authorization / readiness boolean, and "
    "NOT a benchmark-ready flip; candidate fragment totals may be "
    "zero because derived-material materialization is out of "
    "WO-L0-E2E-01 scope; OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, "
    "OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN; "
    "no real adapter; no benchmark execution; no measurement "
    "authorization."
)


class MaterializationReturnedInvalidShape(Exception):
    """Raised when the WO-L0-MATERIAL-01 delegate returns a dict
    missing one of the required materialization observation keys
    or carrying a non-list `source_reference_records` /
    `source_records`."""


class PromptExpectedSourceTouchInvalid(Exception):
    """Raised when a prompt's `expected_source_touch` contains a
    parseable `L0-SRC-XXX` token that is not in the bounded
    `_EXPECTED_SOURCE_IDS` set."""


class TraceCaseSourceAttachmentEmpty(Exception):
    """Raised when the attached `source_reference_records` /
    `source_records` for any constructed trace case is empty
    (after both filter-by-touch and fallback-to-all paths)."""


class TraceExecutionReturnedInvalidShape(Exception):
    """Raised when the WO-L0-TRACE-01 delegate returns a dict
    missing one of the required trace-execution observation keys."""


class ForbiddenLanguageInLevel0EndToEndTrace(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in the emitted end-to-end
    aggregate dict."""


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


def _assert_no_forbidden_language(value, event_log, location):
    for text in _walk_strings(value):
        lowered = text.lower()
        for phrase in END_TO_END_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_end_to_end_trace_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0EndToEndTrace(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_end_to_end_trace_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0EndToEndTrace(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _validate_materialization_shape(observation, event_log):
    if not isinstance(observation, dict):
        event_log.halt(
            reason="level0_end_to_end_materialization_non_dict"
        )
        raise MaterializationReturnedInvalidShape(
            "materialization delegate did not return a dict"
        )
    for key in _REQUIRED_MATERIALIZATION_KEYS:
        if key not in observation:
            event_log.halt(
                reason="level0_end_to_end_materialization_missing_key",
                key=key,
            )
            raise MaterializationReturnedInvalidShape(
                "materialization observation missing key '{0}'".format(key)
            )
    if not isinstance(observation["source_reference_records"], list):
        event_log.halt(
            reason="level0_end_to_end_materialization_non_list_references"
        )
        raise MaterializationReturnedInvalidShape(
            "materialization source_reference_records is not a list"
        )
    if not isinstance(observation["source_records"], list):
        event_log.halt(
            reason="level0_end_to_end_materialization_non_list_records"
        )
        raise MaterializationReturnedInvalidShape(
            "materialization source_records is not a list"
        )
    reference_count = observation["source_reference_count"]
    if (
        not isinstance(reference_count, int)
        or isinstance(reference_count, bool)
        or reference_count != len(observation["source_reference_records"])
    ):
        event_log.halt(
            reason="level0_end_to_end_materialization_reference_count_mismatch"
        )
        raise MaterializationReturnedInvalidShape(
            "materialization source_reference_count does not match "
            "source_reference_records length"
        )
    record_count = observation["source_record_count"]
    if (
        not isinstance(record_count, int)
        or isinstance(record_count, bool)
        or record_count != len(observation["source_records"])
    ):
        event_log.halt(
            reason="level0_end_to_end_materialization_record_count_mismatch"
        )
        raise MaterializationReturnedInvalidShape(
            "materialization source_record_count does not match "
            "source_records length"
        )
    if len(observation["source_reference_records"]) != len(
        observation["source_records"]
    ):
        event_log.halt(
            reason="level0_end_to_end_materialization_record_pair_count_mismatch"
        )
        raise MaterializationReturnedInvalidShape(
            "materialization reference and source record list lengths differ"
        )


def _validate_trace_execution_shape(observation, event_log):
    if not isinstance(observation, dict):
        event_log.halt(
            reason="level0_end_to_end_trace_execution_non_dict"
        )
        raise TraceExecutionReturnedInvalidShape(
            "trace execution delegate did not return a dict"
        )
    for key in _REQUIRED_TRACE_EXECUTION_KEYS:
        if key not in observation:
            event_log.halt(
                reason="level0_end_to_end_trace_execution_missing_key",
                key=key,
            )
            raise TraceExecutionReturnedInvalidShape(
                "trace execution observation missing key '{0}'".format(key)
            )
    if not isinstance(observation["visible_reports"], list):
        event_log.halt(
            reason="level0_end_to_end_trace_execution_non_list_reports"
        )
        raise TraceExecutionReturnedInvalidShape(
            "trace execution visible_reports is not a list"
        )


def _parse_expected_source_touch_tokens(expected_source_touch):
    """Extract `L0-SRC-XXX`-shaped tokens from a prompt's
    `expected_source_touch` string.

    The string may be a single token (`L0-SRC-001`), a
    semicolon-separated list (`L0-SRC-006; L0-SRC-001`), or a prose
    description that contains zero such tokens (`none expected`).
    This helper extracts tokens by checking each whitespace- and
    punctuation-separated segment for the `L0-SRC-` prefix followed
    by a 3-digit suffix.
    """
    if not isinstance(expected_source_touch, str):
        return []
    tokens = []
    # Split on common separators in the prompt-set table: semicolon,
    # comma, whitespace, parenthesis.
    raw = expected_source_touch
    for ch in (";", ",", "(", ")", "[", "]", "\t"):
        raw = raw.replace(ch, " ")
    for segment in raw.split():
        # Each candidate L0-SRC-XXX token is 10 characters: "L0-SRC-"
        # (7 chars) + a 3-character numeric suffix.
        if len(segment) >= 10 and segment.startswith("L0-SRC-"):
            head = segment[:10]
            if head[7:].isdigit():
                tokens.append(head)
    return tokens


def _filter_sources_for_prompt(
    prompt, item_records, source_reference_records, source_records,
    event_log, prompt_index,
):
    """Filter materialized source records for one prompt.

    Returns (filtered_references, filtered_records). Raises
    `PromptExpectedSourceTouchInvalid` if a parseable token is
    outside `_EXPECTED_SOURCE_IDS`. Raises
    `TraceCaseSourceAttachmentEmpty` if the attached set would be
    empty.
    """
    tokens = _parse_expected_source_touch_tokens(prompt["expected_source_touch"])
    for token in tokens:
        if token not in _EXPECTED_SOURCE_IDS:
            event_log.halt(
                reason="level0_end_to_end_prompt_expected_source_touch_invalid",
                prompt_index=prompt_index,
                token=token,
            )
            raise PromptExpectedSourceTouchInvalid(
                "prompt_records[{0}] expected_source_touch contains "
                "token {1!r} outside _EXPECTED_SOURCE_IDS".format(
                    prompt_index, token
                )
            )

    if tokens:
        # Filter: include positions whose item.source_id appears in
        # the token set.
        token_set = set(tokens)
        indices = [
            i
            for i, item in enumerate(item_records)
            if item["source_id"] in token_set
        ]
    else:
        # Fallback: prose-only expected_source_touch (e.g.,
        # "none expected", "all inventory sources"). Attach all
        # materialized sources.
        indices = list(range(len(item_records)))

    # Defensive bounds check: only include indices that map to an
    # actual materialized record. Out-of-range indices silently drop;
    # if all drop, the empty-attachment halt below fires.
    max_index = min(len(source_reference_records), len(source_records))
    indices = [i for i in indices if i < max_index]

    filtered_references = [source_reference_records[i] for i in indices]
    filtered_records = [source_records[i] for i in indices]

    if not filtered_references:
        event_log.halt(
            reason="level0_end_to_end_trace_case_source_attachment_empty",
            prompt_index=prompt_index,
        )
        raise TraceCaseSourceAttachmentEmpty(
            "trace case for prompt_records[{0}] has empty attached "
            "source set".format(prompt_index)
        )

    return filtered_references, filtered_records


def _build_trace_case_records(
    item_records, prompt_records,
    source_reference_records, source_records, event_log,
):
    """Build one trace_case_record per prompt, attaching filtered
    source records."""
    trace_case_records = []
    for prompt_index, prompt in enumerate(prompt_records):
        filtered_refs, filtered_recs = _filter_sources_for_prompt(
            prompt,
            item_records,
            source_reference_records,
            source_records,
            event_log,
            prompt_index,
        )
        case_id = "{0}-{1:03d}".format(_CASE_ID_PREFIX, prompt_index + 1)
        trace_case_records.append({
            "case_id": case_id,
            "prompt_id": prompt["prompt_id"],
            "expected_category": prompt["category"],
            "input_prompt": prompt["prompt_text"],
            "source_reference_records": filtered_refs,
            "source_records": filtered_recs,
            "expected_source_touch": prompt["expected_source_touch"],
            "expected_candidate_shape": prompt["expected_candidate_shape"],
            "expected_rejection_targets": prompt["expected_rejection_targets"],
            "boundary_notes": _TRACE_CASE_BOUNDARY_NOTE,
        })
    return trace_case_records


def _build_per_prompt_summary(prompt_records, trace_case_records, visible_reports):
    """Produce one summary dict per prompt, with fields derived from
    the trace case and the corresponding WO-59 visible report."""
    summary = []
    for prompt, case, report in zip(prompt_records, trace_case_records, visible_reports):
        summary.append({
            "prompt_id": prompt["prompt_id"],
            "category": prompt["category"],
            "case_id": case["case_id"],
            "source_reference_count": len(case["source_reference_records"]),
            "source_record_count": len(case["source_records"]),
            "linked_source_count": report["linked_source_count"],
            "candidate_route_fragment_count": report[
                "trace_candidate_route_fragment_count"
            ],
            "candidate_workflow_fragment_count": report[
                "trace_candidate_workflow_fragment_count"
            ],
            "review_halt_required": report["review_halt_required"],
        })
    return summary


def run_level0_manual_seed_end_to_end_trace(
    item_records, prompt_records, event_log
):
    """Run the consolidated Level 0B manual seed end-to-end visible
    trace flow.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_manual_seed_end_to_end_trace_started")

    # Phase 1: delegate to WO-L0-MATERIAL-01 for materialization.
    materialization_observation = run_level0_manual_seed_materialization(
        item_records, prompt_records, event_log
    )
    _validate_materialization_shape(materialization_observation, event_log)

    # Phase 2: build trace_case_records from prompts and materialized
    # source records.
    trace_case_records = _build_trace_case_records(
        item_records,
        prompt_records,
        materialization_observation["source_reference_records"],
        materialization_observation["source_records"],
        event_log,
    )

    # Phase 3: delegate to WO-L0-TRACE-01 for trace execution.
    trace_execution_observation = run_level0_manual_seed_trace_execution(
        item_records,
        prompt_records,
        trace_case_records,
        event_log,
    )
    _validate_trace_execution_shape(trace_execution_observation, event_log)

    # Phase 4: build per-prompt summary and aggregate counts.
    visible_reports = trace_execution_observation["visible_reports"]
    per_prompt_summary = _build_per_prompt_summary(
        prompt_records, trace_case_records, visible_reports
    )

    candidate_route_total = sum(
        report["trace_candidate_route_fragment_count"]
        for report in visible_reports
    )
    candidate_workflow_total = sum(
        report["trace_candidate_workflow_fragment_count"]
        for report in visible_reports
    )

    source_reference_count = materialization_observation["source_reference_count"]
    source_record_count = materialization_observation["source_record_count"]

    result = {
        "end_to_end_kind": _END_TO_END_KIND,
        "materialization_observation": materialization_observation,
        "trace_execution_observation": trace_execution_observation,
        "trace_case_count": len(trace_case_records),
        "source_reference_count": source_reference_count,
        "source_record_count": source_record_count,
        "visible_report_count": trace_execution_observation["visible_report_count"],
        "per_prompt_trace_summary": per_prompt_summary,
        "candidate_route_fragment_total": candidate_route_total,
        "candidate_workflow_fragment_total": candidate_workflow_total,
        "review_halt_required_count": trace_execution_observation[
            "review_halt_required_count"
        ],
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "end_to_end_note": _END_TO_END_NOTE,
    }

    _assert_no_forbidden_language(result, event_log, location="result")

    event_log.append("level0_manual_seed_end_to_end_trace_completed")
    return result
