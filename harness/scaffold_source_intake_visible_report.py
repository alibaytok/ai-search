"""Scaffold visible source-intake flow report.

WO-59 composes the WO-57 in-memory source-intake smoke package with
the WO-58 route-invariant diagnostic reporter into a single
read-only visible review observation. The report answers, at
scaffold level only:

- what input prompt was observed structurally;
- which source references were registered;
- which source records were linked;
- what the WO-54 trace observation produced (embedded via WO-57);
- which candidate route / workflow fragments were observed;
- what WO-58 diagnostics reported;
- whether any review halt is advised.

The report is the first end-to-end visible local flow surface. It
is NOT real indexing, NOT real retrieval, NOT prompt search, NOT
skill search, NOT agent selection, NOT generic RAG, NOT benchmark
execution, NOT architecture selection, NOT source qualification,
NOT corpus admission, NOT a route validator, and NOT a real-
benchmark-ready flip.

This module performs no file IO, no network call, no hash
computation, no real or mock adapter invocation, no real benchmark
execution, no metric / quality / performance measurement, no
similarity / ranking / scoring of any kind, no model judgment, no
fuzzy semantic analysis, no thresholds, no weights, no
architecture / vendor / library / index family / production system
choice, no shell execution, and no external integration. It uses
only Python standard library plus harness-internal imports.

The WO-47 through WO-58 explicit non-claim constraint carries
forward: this module does not claim that any composition, report,
diagnostic, or observation is sufficient, necessary, superior,
best, complete, production-ready, recommended, or selected.

Public surface:

    run_scaffold_source_intake_visible_report(
        input_prompt, source_reference_records, source_records,
        event_log
    ) -> dict

The clean-pass output dict has exactly seventeen allowed keys in
`ALLOWED_OUTPUT_KEYS`. The four authorization / readiness /
selection booleans are literal False on every emitted path,
regardless of how many diagnostic findings with `halt_required:
True` appear in the embedded `diagnostic_report`.

The advisory `review_halt_required` field is True only when the
embedded diagnostic report's `halt_required_count` is greater than
zero. It is metadata about what the caller should do; it does NOT
cause the report itself to raise.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_route_invariant_diagnostic_reporter import (
    run_scaffold_route_invariant_diagnostic_reporter,
)
from harness.scaffold_source_intake_smoke_package import (
    run_scaffold_source_intake_smoke_package,
)


VISIBLE_REPORT_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "visible_report_kind",
    "input_prompt_observed",
    "source_reference_count",
    "source_record_count",
    "linked_source_count",
    "trace_candidate_route_fragment_count",
    "trace_candidate_workflow_fragment_count",
    "package_observation",
    "diagnostic_report",
    "diagnostic_error_count",
    "diagnostic_halt_required_count",
    "review_halt_required",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "visible_report_note",
)


_PACKAGE_OBSERVATION_KIND = "scaffold_source_intake_smoke_package"


_VISIBLE_REPORT_NOTE = (
    "scaffold_source_intake_visible_report: composes the WO-57 smoke "
    "package and the WO-58 route-invariant diagnostic reporter into "
    "one end-to-end visible review observation; report success is "
    "NOT source qualification, NOT corpus admission, NOT route "
    "selection, NOT benchmark readiness, and does NOT select any "
    "architecture / vendor / library / index family / ANN backend / "
    "retrieval family / production system; review_halt_required True "
    "is advisory report metadata only and does NOT cause the report "
    "to raise or flip any authorization boolean; OQ-003, OQ-015, "
    "OQ-031, OQ-035, OQ-048, OQ-076 remain OPEN; no real adapter, "
    "no benchmark execution, and no measurement authorization."
)


class ForbiddenLanguageInVisibleSourceIntakeReport(Exception):
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
    for phrase in VISIBLE_REPORT_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_source_intake_visible_report_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInVisibleSourceIntakeReport(
                "Forbidden phrase {0!r} found in visible source-intake "
                "report output".format(offending)
            )


def _wrap_as_diagnostic_observation(package_observation):
    """Shallow-copy the WO-57 package observation and add the
    `observation_kind` key required by the WO-58 diagnostic reporter.

    The WO-57 output dict carries `package_kind`. The diagnostic
    reporter requires `observation_kind`. This wrapper does not
    mutate the input dict; it returns a new dict with the
    `observation_kind` key set to the recognized scaffold-layer kind.
    """
    observation = dict(package_observation)
    observation["observation_kind"] = _PACKAGE_OBSERVATION_KIND
    return observation


def run_scaffold_source_intake_visible_report(
    input_prompt, source_reference_records, source_records, event_log
):
    """Compose WO-57 and WO-58 into one read-only visible report.

    Returns a fresh dict with exactly the seventeen allowed keys in
    `ALLOWED_OUTPUT_KEYS` on clean pass. Propagates any exception
    raised by WO-57 or WO-58 verbatim; never swallows.
    """
    event_log.append(
        "scaffold_source_intake_visible_report_started",
        source_reference_count=(
            len(source_reference_records)
            if isinstance(source_reference_records, list)
            else None
        ),
        source_record_count=(
            len(source_records) if isinstance(source_records, list) else None
        ),
    )

    package_observation = run_scaffold_source_intake_smoke_package(
        input_prompt, source_reference_records, source_records, event_log
    )
    event_log.append(
        "scaffold_source_intake_visible_report_package_completed",
        linked_source_count=package_observation["linked_source_count"],
        trace_candidate_route_fragment_count=package_observation[
            "trace_candidate_route_fragment_count"
        ],
        trace_candidate_workflow_fragment_count=package_observation[
            "trace_candidate_workflow_fragment_count"
        ],
    )

    diagnostic_observation = _wrap_as_diagnostic_observation(
        package_observation
    )
    diagnostic_report = run_scaffold_route_invariant_diagnostic_reporter(
        [diagnostic_observation], event_log
    )
    event_log.append(
        "scaffold_source_intake_visible_report_diagnostics_completed",
        diagnostics_count=diagnostic_report["diagnostics_count"],
        error_count=diagnostic_report["error_count"],
        halt_required_count=diagnostic_report["halt_required_count"],
    )

    review_halt_required = diagnostic_report["halt_required_count"] > 0

    output = {
        "visible_report_kind": "scaffold_source_intake_visible_report",
        "input_prompt_observed": package_observation["input_prompt_observed"],
        "source_reference_count": package_observation["source_reference_count"],
        "source_record_count": package_observation["source_record_count"],
        "linked_source_count": package_observation["linked_source_count"],
        "trace_candidate_route_fragment_count": package_observation[
            "trace_candidate_route_fragment_count"
        ],
        "trace_candidate_workflow_fragment_count": package_observation[
            "trace_candidate_workflow_fragment_count"
        ],
        "package_observation": package_observation,
        "diagnostic_report": diagnostic_report,
        "diagnostic_error_count": diagnostic_report["error_count"],
        "diagnostic_halt_required_count": diagnostic_report[
            "halt_required_count"
        ],
        "review_halt_required": review_halt_required,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "visible_report_note": _VISIBLE_REPORT_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_source_intake_visible_report_passed",
        source_reference_count=output["source_reference_count"],
        source_record_count=output["source_record_count"],
        linked_source_count=output["linked_source_count"],
        trace_candidate_route_fragment_count=output[
            "trace_candidate_route_fragment_count"
        ],
        trace_candidate_workflow_fragment_count=output[
            "trace_candidate_workflow_fragment_count"
        ],
        diagnostic_error_count=output["diagnostic_error_count"],
        diagnostic_halt_required_count=output["diagnostic_halt_required_count"],
        review_halt_required=review_halt_required,
    )
    return output
