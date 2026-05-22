"""Scaffold in-memory source-intake smoke package.

WO-57 composes the already-approved WO-55 register, WO-56 bridge, and
WO-54 source-intake trace into a single in-memory, read-only
observation. The package invokes the three existing public functions
in strict order:

  1. `run_scaffold_source_intake_register(source_reference_records,
     event_log)` (WO-55)
  2. `run_scaffold_source_trace_admission_bridge(register_observation,
     source_records, event_log)` (WO-56)
  3. `run_scaffold_source_intake_trace(input_prompt, source_records,
     event_log)` (WO-54)

If any prior stage raises, the package does not continue to later
stages and does not swallow the exception. The package never converts
a failure into a success summary.

This module does NOT read files, write files, call the network,
download, fetch, crawl, compute hashes, run a real benchmark, invoke
any real or mock adapter, perform retrieval, ranking, similarity,
metrics, or any architecture / vendor / library / index family /
ANN backend / retrieval family / ablation cell / multi-stage variant
/ production system choice. The package does not perform source
qualification, corpus admission, or candidate-fragment derivation of
its own; counts that flow into the output are copied verbatim from
the WO-54 trace observation.

The WO-47 through WO-56 explicit non-claim constraint carries forward:
this module does not claim that any composition, observation, or
stage is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected.

Public surface:

    run_scaffold_source_intake_smoke_package(
        input_prompt, source_reference_records, source_records,
        event_log
    ) -> dict

The clean-pass output dict has exactly twenty allowed keys in
`ALLOWED_OUTPUT_KEYS`. Seven literal-False authorization / readiness /
selection booleans and two literal-zero counts are emitted on every
clean-pass path.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_source_intake_register import (
    run_scaffold_source_intake_register,
)
from harness.scaffold_source_intake_trace import (
    run_scaffold_source_intake_trace,
)
from harness.scaffold_source_trace_admission_bridge import (
    run_scaffold_source_trace_admission_bridge,
)


# Note: WO-57 deliberately does not extend the forbidden-phrase set
# locally beyond FORBIDDEN_PHRASES. The upstream WO-54, WO-55, and
# WO-56 modules already enforce the local extension on every value
# they emit, and this module's composed output is built entirely from
# their observations plus an author-controlled constant note. Any
# value reachable from the composed output has already been scrubbed
# at the layer that produced it. This is an assumption Claude is
# flagging for Codex review; see the WO-57 ledger entry.
PACKAGE_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "package_kind",
    "input_prompt_observed",
    "register_observation",
    "bridge_observation",
    "trace_observation",
    "source_reference_count",
    "source_record_count",
    "linked_source_count",
    "trace_candidate_route_fragment_count",
    "trace_candidate_workflow_fragment_count",
    "corpus_admitted_count",
    "qualified_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "extraction_authorized",
    "normalization_authorized",
    "candidate_derivation_authorized",
    "package_note",
)


_PACKAGE_NOTE = (
    "scaffold_source_intake_smoke_package: composes the WO-55 "
    "register, WO-56 bridge, and WO-54 trace into one in-memory "
    "observation; package success is NOT source qualification, NOT "
    "corpus admission, NOT route selection, NOT benchmark readiness, "
    "and does NOT select any architecture / vendor / library / index "
    "family / ANN backend / retrieval family / production system; "
    "OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-076 remain OPEN; no "
    "real adapter, no benchmark execution, and no measurement "
    "authorization."
)


class ForbiddenLanguageInSourceIntakeSmokePackage(Exception):
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
    for phrase in PACKAGE_OUTPUT_FORBIDDEN_PHRASES:
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
                "scaffold_source_intake_smoke_package_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInSourceIntakeSmokePackage(
                "Forbidden phrase {0!r} found in source-intake smoke "
                "package output".format(offending)
            )


def run_scaffold_source_intake_smoke_package(
    input_prompt, source_reference_records, source_records, event_log
):
    """Compose WO-55, WO-56, and WO-54 in strict order.

    Returns a fresh dict with exactly the twenty allowed keys in
    `ALLOWED_OUTPUT_KEYS` on clean pass. Propagates any exception
    raised by WO-55 / WO-56 / WO-54 verbatim; never swallows.
    """
    event_log.append(
        "scaffold_source_intake_smoke_package_started",
        source_reference_count=(
            len(source_reference_records)
            if isinstance(source_reference_records, list)
            else None
        ),
        source_record_count=(
            len(source_records) if isinstance(source_records, list) else None
        ),
    )

    register_observation = run_scaffold_source_intake_register(
        source_reference_records, event_log
    )
    event_log.append(
        "scaffold_source_intake_smoke_package_register_completed",
        references_observed_count=register_observation[
            "references_observed_count"
        ],
    )

    bridge_observation = run_scaffold_source_trace_admission_bridge(
        register_observation, source_records, event_log
    )
    event_log.append(
        "scaffold_source_intake_smoke_package_bridge_completed",
        linked_source_count=bridge_observation["linked_source_count"],
    )

    trace_observation = run_scaffold_source_intake_trace(
        input_prompt, source_records, event_log
    )
    event_log.append(
        "scaffold_source_intake_smoke_package_trace_completed",
        sources_touched_count=trace_observation["sources_touched_count"],
        candidate_route_fragments_count=len(
            trace_observation["candidate_route_fragments"]
        ),
        candidate_workflow_fragments_count=len(
            trace_observation["candidate_workflow_fragments"]
        ),
    )

    output = {
        "package_kind": "scaffold_source_intake_smoke_package",
        "input_prompt_observed": trace_observation["input_prompt_observed"],
        "register_observation": register_observation,
        "bridge_observation": bridge_observation,
        "trace_observation": trace_observation,
        "source_reference_count": register_observation[
            "references_observed_count"
        ],
        "source_record_count": bridge_observation[
            "source_records_checked_count"
        ],
        "linked_source_count": bridge_observation["linked_source_count"],
        "trace_candidate_route_fragment_count": len(
            trace_observation["candidate_route_fragments"]
        ),
        "trace_candidate_workflow_fragment_count": len(
            trace_observation["candidate_workflow_fragments"]
        ),
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "extraction_authorized": False,
        "normalization_authorized": False,
        "candidate_derivation_authorized": False,
        "package_note": _PACKAGE_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_source_intake_smoke_package_passed",
        source_reference_count=output["source_reference_count"],
        source_record_count=output["source_record_count"],
        linked_source_count=output["linked_source_count"],
        trace_candidate_route_fragment_count=output[
            "trace_candidate_route_fragment_count"
        ],
        trace_candidate_workflow_fragment_count=output[
            "trace_candidate_workflow_fragment_count"
        ],
        corpus_admitted_count=0,
        qualified_count=0,
    )
    return output
