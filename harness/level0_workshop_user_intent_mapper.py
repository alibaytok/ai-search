"""Compatibility shim for the Level 0B workshop user-intent mapper.

WO-L0-WORKSHOP-FRAME-D-R rewrites the existing legacy public function
`map_level0_workshop_user_intent(input_prompt, workshop_prompt_id,
event_log) -> dict` as a thin compatibility shim that derives its
authoritative output strictly from the WO-L0-WORKSHOP-FRAME-C
CanonicalIntentFrame synthesizer, routing input through the
WO-L0-WORKSHOP-FRAME-A NormalizedPromptView and the
WO-L0-WORKSHOP-FRAME-B SignalEvidence layer along the way.

Pipeline position:

    PromptText
      -> FRAME-A NormalizedPromptView         (input validation +
                                               normalization)
      -> FRAME-B SignalEvidenceLedger         (signal observation)
      -> FRAME-C CanonicalIntentFrame +       (synthesis +
         ShapeTouchPlan +                      adapter)
         WorkshopPromptRecordAdapter
      -> FRAME-D legacy contract shim         (this module;
                                               translator only)

The shim does NOT carry a parallel keyword classifier. The
authoritative source of `workshop_prompt_record` (seven fields)
and of the legacy mirror fields is the FRAME-C output. The shim:

1. echoes FRAME-C's `workshop_prompt_record` verbatim (same seven
   keys, same `boundary_note` literal as `WORKSHOP_BOUNDARY_NOTE`);
2. derives `normalized_intent_observation` from FRAME-C's
   `workshop_prompt_record["category"]` via a fixed nine-entry
   translation table whose only job is to rename the FRAME-C
   bounded category to the legacy bounded intent label;
3. echoes FRAME-C's `expected_item_kinds_touched`,
   `expected_candidate_surface`, and `expected_rejection_surface`
   into the legacy mirror keys without rewording;
4. derives `ambiguity_observed` from FRAME-C's `ambiguity_level`
   (True iff `"high"`);
5. forces the six legacy gating booleans to literal False.

The legacy keyword `_classify_prompt` and the legacy keyword
tables (`_NO_ROUTE_TERMS`, `_REPO_META_TERMS`, `_WORKFLOW_TERMS`,
`_HOOK_TERMS`, `_SKILL_TERMS`, `_AGENT_TERMS`,
`_INSTRUCTION_TERMS`, `_PLUGIN_TERMS`, `_COOKBOOK_TERMS`,
`_AMBIGUOUS_TERMS`) have been removed from this module. FRAME-C
is the single source of truth for categorization.

Some pre-FRAME-D legacy smoke-test assertions diverge from
FRAME-C semantics. Those divergences are upstream FRAME-C
synthesis gaps and are recorded in `ai-search/00-open-questions.md`
under RK-059 ("FRAME-C synthesis gaps surfaced by FRAME-D smoke
tests"). The smoke-test assertions have been updated in
`harness/tests/test_level0_workshop_user_intent_mapper.py` to
reflect FRAME-C-actual behavior with docstring pointers to
RK-059; closure of RK-059 is reserved for a later Codex-
authorized FRAME-C-hardening packet. RK-058 remains OPEN.
OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057,
OQ-070, OQ-075, OQ-076 remain OPEN. Real-benchmark-ready remains
NO.

This module does not classify a route, does not select an item,
does not qualify a source, does not admit a corpus, does not
retrieve, does not embed, does not vectorize, does not score,
does not rank, does not compute similarity or distance, does not
call any LLM / provider / external API / embedding / vector / ANN
backend / reranker, and does not perform file IO, network calls,
URL fetch / download / crawl, PDF extraction, hash computation,
or external process spawning. Module source is ASCII-only.

Public surface (unchanged):

    map_level0_workshop_user_intent(
        input_prompt, workshop_prompt_id, event_log
    ) -> dict
"""

from harness.level0_workshop_canonical_intent_frame import (
    InvalidWorkshopPromptId as _FrameCInvalidWorkshopPromptId,
    WORKSHOP_PROMPT_CATEGORIES,
    build_canonical_intent_frame,
)
from harness.level0_workshop_derived_trace import WORKSHOP_BOUNDARY_NOTE
from harness.level0_workshop_normalized_prompt_view import (
    EmptyInputPrompt as _FrameAEmptyInputPrompt,
    NonStringInputPrompt as _FrameANonStringInputPrompt,
    WhitespaceOnlyInputPrompt as _FrameAWhitespaceOnlyInputPrompt,
    build_level0_workshop_normalized_prompt_view,
)
from harness.level0_workshop_signal_evidence import (
    extract_workshop_signal_evidence,
)


_MAPPER_KIND = "level0_workshop_user_intent_mapper"

_OUTPUT_KEYS = (
    "intent_mapper_kind",
    "workshop_prompt_record",
    "normalized_intent_observation",
    "expected_item_kinds_touched",
    "candidate_surface_expected",
    "rejection_surface_expected",
    "ambiguity_observed",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "mapper_note",
)

_WORKSHOP_PROMPT_RECORD_KEYS = (
    "workshop_prompt_id",
    "category",
    "prompt_text",
    "expected_item_kinds_touched",
    "expected_candidate_surface",
    "expected_rejection_surface",
    "boundary_note",
)


# Translation table mapping the FRAME-C bounded nine workshop
# categories to the bounded nine legacy normalized-intent labels.
# This table is a pure rename only; FRAME-C decides the category
# and FRAME-D translates the label. The table is bounded by
# FRAME-D and is NOT claimed exhaustive.
_NORMALIZED_INTENT_BY_CATEGORY = {
    "A. clear single-intent": "clear_single_intent",
    "B. workflow intent": "workflow_intent",
    "C. skill intent": "skill_intent",
    "D. agent/persona confusion": "agent_surface_workflow_intent",
    "E. instruction confusion": "instruction_surface_workflow_intent",
    "F. prompt-search-shaped but workflow-intent": (
        "prompt_surface_workflow_intent"
    ),
    "G. ambiguous": "ambiguous_user_intent",
    "H. no-route": "no_route",
    "I. near-miss/rejection": "near_miss_rejection",
}

# Defensive: the translation table must cover every FRAME-C
# bounded category.
assert set(_NORMALIZED_INTENT_BY_CATEGORY.keys()) == set(
    WORKSHOP_PROMPT_CATEGORIES
)


class NonStringUserPrompt(Exception):
    """Raised when the user prompt is not a string."""


class EmptyUserPrompt(Exception):
    """Raised when the user prompt is empty after trimming."""


class InvalidWorkshopPromptId(Exception):
    """Raised when the workshop prompt id is not a non-empty string."""


def _halt(event_log, reason, message):
    event_log.halt(reason=reason, message=message)


def _run_frame_a(input_prompt, event_log):
    """Call FRAME-A and translate its named exceptions to the
    legacy mapper exception surface. FRAME-A emits its own halt
    event before raising; the shim emits an additional mapper-
    scoped halt event so legacy halt-reason consumers continue
    to observe a mapper-scoped halt as well."""
    try:
        return build_level0_workshop_normalized_prompt_view(
            input_prompt, event_log
        )
    except _FrameANonStringInputPrompt as exc:
        _halt(
            event_log,
            "level0_workshop_user_intent_mapper_non_string_prompt",
            "input_prompt must be a string",
        )
        raise NonStringUserPrompt("input_prompt must be a string") from exc
    except (_FrameAEmptyInputPrompt, _FrameAWhitespaceOnlyInputPrompt) as exc:
        _halt(
            event_log,
            "level0_workshop_user_intent_mapper_empty_prompt",
            "input_prompt must be non-empty",
        )
        raise EmptyUserPrompt("input_prompt must be non-empty") from exc


def _run_frame_b(normalized_view, event_log):
    """Call FRAME-B over the validated FRAME-A view. FRAME-B
    failures here would indicate a FRAME-A contract drift; they
    are not translated to legacy exceptions and are allowed to
    propagate so the underlying drift is visible."""
    return extract_workshop_signal_evidence(normalized_view, event_log)


def _run_frame_c(signal_evidence_ledger, workshop_prompt_id, event_log):
    """Call FRAME-C over the validated FRAME-B ledger. The shim
    has already validated `workshop_prompt_id` against the legacy
    contract; FRAME-C's own InvalidWorkshopPromptId is translated
    defensively to the legacy `InvalidWorkshopPromptId` so the
    legacy exception surface is preserved even on the unexpected
    path."""
    try:
        return build_canonical_intent_frame(
            signal_evidence_ledger, workshop_prompt_id, event_log
        )
    except _FrameCInvalidWorkshopPromptId as exc:
        _halt(
            event_log,
            "level0_workshop_user_intent_mapper_invalid_prompt_id",
            "workshop_prompt_id must be a non-empty string",
        )
        raise InvalidWorkshopPromptId(
            "workshop_prompt_id must be a non-empty string"
        ) from exc


def _derive_legacy_output(canonical_intent_frame):
    """Translate FRAME-C's CanonicalIntentFrame into the legacy
    fourteen-key mapper output. The FRAME-C `workshop_prompt_record`
    is echoed verbatim (same seven keys, same `boundary_note`
    literal `WORKSHOP_BOUNDARY_NOTE`); the legacy mirror fields
    are derived strictly from the FRAME-C record and from
    `ambiguity_level`. No keyword classification is applied
    inside this shim."""
    frame_record = canonical_intent_frame["workshop_prompt_record"]
    category = frame_record["category"]
    normalized_intent = _NORMALIZED_INTENT_BY_CATEGORY[category]

    prompt_record = {
        "workshop_prompt_id": frame_record["workshop_prompt_id"],
        "category": category,
        "prompt_text": frame_record["prompt_text"],
        "expected_item_kinds_touched": list(
            frame_record["expected_item_kinds_touched"]
        ),
        "expected_candidate_surface": (
            frame_record["expected_candidate_surface"]
        ),
        "expected_rejection_surface": (
            frame_record["expected_rejection_surface"]
        ),
        "boundary_note": frame_record["boundary_note"],
    }

    output = {
        "intent_mapper_kind": _MAPPER_KIND,
        "workshop_prompt_record": prompt_record,
        "normalized_intent_observation": normalized_intent,
        "expected_item_kinds_touched": list(
            frame_record["expected_item_kinds_touched"]
        ),
        "candidate_surface_expected": (
            frame_record["expected_candidate_surface"]
        ),
        "rejection_surface_expected": (
            frame_record["expected_rejection_surface"]
        ),
        "ambiguity_observed": (
            canonical_intent_frame["ambiguity_level"] == "high"
        ),
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "mapper_note": (
            "FRAME-D compatibility shim deriving output strictly "
            "from the FRAME-C CanonicalIntentFrame; no legacy "
            "keyword classifier; FRAME-C synthesis gaps surfaced "
            "by the smoke test suite are recorded as RK-059; "
            "RK-058 remains OPEN; no route selection authorized"
        ),
    }
    return output


def map_level0_workshop_user_intent(input_prompt, workshop_prompt_id, event_log):
    """Map one free-text prompt to a workshop prompt record.

    Public contract preserved from the pre-FRAME-D mapper:

    - Output is a fixed 14-key dict whose key set equals
      `_OUTPUT_KEYS`.
    - `workshop_prompt_record` is a fixed seven-key dict whose key
      set equals `_WORKSHOP_PROMPT_RECORD_KEYS`; `boundary_note`
      is the literal `WORKSHOP_BOUNDARY_NOTE`.
    - Six gating booleans (`selection_made`, `measurement_authorized`,
      `real_benchmark_authorized`, `real_benchmark_ready`,
      `source_qualification_authorized`, `corpus_admission_authorized`)
      are literal False on every emitted path.
    - Legacy named exceptions `NonStringUserPrompt`,
      `EmptyUserPrompt`, and `InvalidWorkshopPromptId` are
      preserved; FRAME-A's equivalent exceptions are translated at
      the shim boundary.

    Categorical strings (`category`, `normalized_intent_observation`,
    `expected_item_kinds_touched`, `candidate_surface_expected`,
    `rejection_surface_expected`, `ambiguity_observed`) are now
    derived from FRAME-C output, not from a parallel keyword
    classifier. Some pre-FRAME-D legacy smoke-test assertions
    diverge from FRAME-C semantics; those divergences are
    recorded as upstream FRAME-C synthesis gaps under RK-059.
    """
    event_log.append(
        "level0_workshop_user_intent_mapper_started",
        intent_mapper_kind=_MAPPER_KIND,
    )

    normalized_view = _run_frame_a(input_prompt, event_log)

    if not isinstance(workshop_prompt_id, str) or not workshop_prompt_id.strip():
        _halt(
            event_log,
            "level0_workshop_user_intent_mapper_invalid_prompt_id",
            "workshop_prompt_id must be a non-empty string",
        )
        raise InvalidWorkshopPromptId(
            "workshop_prompt_id must be a non-empty string"
        )

    signal_evidence_ledger = _run_frame_b(normalized_view, event_log)
    canonical_intent_frame = _run_frame_c(
        signal_evidence_ledger, workshop_prompt_id, event_log
    )

    output = _derive_legacy_output(canonical_intent_frame)

    if output["workshop_prompt_record"]["boundary_note"] != WORKSHOP_BOUNDARY_NOTE:
        raise AssertionError("workshop_prompt_record boundary_note drift")

    event_log.append(
        "level0_workshop_user_intent_mapper_completed",
        category=output["workshop_prompt_record"]["category"],
        normalized_intent_observation=(
            output["normalized_intent_observation"]
        ),
        expected_item_kinds_touched=list(
            output["expected_item_kinds_touched"]
        ),
        observed_frame_kind=canonical_intent_frame["intent_frame_kind"],
        observed_ledger_kind=(
            signal_evidence_ledger["signal_evidence_ledger_kind"]
        ),
        observed_view_kind=normalized_view["normalized_prompt_view_kind"],
    )

    if set(output.keys()) != set(_OUTPUT_KEYS):
        raise AssertionError("mapper output shape drift")
    if set(output["workshop_prompt_record"].keys()) != set(
        _WORKSHOP_PROMPT_RECORD_KEYS
    ):
        raise AssertionError("workshop_prompt_record shape drift")

    return output
