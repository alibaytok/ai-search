# 72 - Level 0B Workshop Intent Mapper Compatibility Shim (FRAME-D / FRAME-D-R)

Document type: Boundary doc for WO-L0-WORKSHOP-FRAME-D and its
rework pass WO-L0-WORKSHOP-FRAME-D-R
Owner: Codex (controller)
Author of entry: Claude (builder/documentation agent)
Status: Implemented; pending Codex review.

## 1. Purpose

This document records the exact contract of the FRAME-D
compatibility shim that rewrites the existing public function
`map_level0_workshop_user_intent(input_prompt, workshop_prompt_id,
event_log) -> dict` so the shim now derives its authoritative
output strictly from the WO-L0-WORKSHOP-FRAME-C
CanonicalIntentFrame synthesizer, while routing input through the
WO-L0-WORKSHOP-FRAME-A NormalizedPromptView and the
WO-L0-WORKSHOP-FRAME-B SignalEvidenceLedger on the way.

This document does not authorize route creation, route selection,
source qualification, corpus admission, real indexing, retrieval,
ranking, scoring, similarity, distance, embedding, vector, ANN
backend, reranker, provider call, LLM call, architecture
selection, vendor selection, library selection, index-family
selection, production-system selection, or benchmark execution.
Real-benchmark-ready remains NO. RK-058 remains OPEN. RK-059 is
added (FRAME-C synthesis gaps surfaced by FRAME-D smoke tests)
and remains OPEN. OQ-003, OQ-015, OQ-031, OQ-035, OQ-048,
OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
RK-039 single.

## 2. Public surface

```
map_level0_workshop_user_intent(input_prompt, workshop_prompt_id,
                                event_log) -> dict
```

Unchanged from the pre-FRAME-D mapper. The function name, the
argument list, the argument order, and the return type are
preserved.

## 3. Pipeline position

```
PromptText
  -> FRAME-A NormalizedPromptView         (input validation +
                                           normalization)
  -> FRAME-B SignalEvidenceLedger         (signal observation)
  -> FRAME-C CanonicalIntentFrame +       (synthesis +
     ShapeTouchPlan +                      adapter)
     WorkshopPromptRecordAdapter
  -> FRAME-D legacy contract shim         (translator only)
```

On every clean-path invocation the shim calls, in order:

1. `build_level0_workshop_normalized_prompt_view(input_prompt,
   event_log)` (FRAME-A).
2. The shim validates `workshop_prompt_id` against the legacy
   contract (raising the legacy `InvalidWorkshopPromptId`)
   before calling FRAME-B or FRAME-C.
3. `extract_workshop_signal_evidence(normalized_view, event_log)`
   (FRAME-B).
4. `build_canonical_intent_frame(signal_evidence_ledger,
   workshop_prompt_id, event_log)` (FRAME-C).
5. `_derive_legacy_output(canonical_intent_frame)` translates the
   FRAME-C output to the legacy fourteen-key shape.

## 4. Authoritative output source: FRAME-C

The shim does NOT carry a parallel keyword classifier. The
pre-FRAME-D `_classify_prompt` function and its ten keyword
tables (`_NO_ROUTE_TERMS`, `_REPO_META_TERMS`, `_WORKFLOW_TERMS`,
`_HOOK_TERMS`, `_SKILL_TERMS`, `_AGENT_TERMS`,
`_INSTRUCTION_TERMS`, `_PLUGIN_TERMS`, `_COOKBOOK_TERMS`,
`_AMBIGUOUS_TERMS`) have been REMOVED from the shim module.
Absence is verified by the test
`LegacyContractParityTest.test_shim_does_not_define_legacy_classifier`.

The authoritative source of `workshop_prompt_record` and of the
legacy mirror fields is the FRAME-C output. The shim:

1. echoes FRAME-C's `workshop_prompt_record` verbatim into the
   legacy `workshop_prompt_record` slot (same seven keys, same
   `boundary_note` literal `not admitted; not qualified;
   workshop metadata only` identical to `WORKSHOP_BOUNDARY_NOTE`);
2. derives `normalized_intent_observation` from FRAME-C's
   `workshop_prompt_record["category"]` via the bounded
   nine-entry rename table `_NORMALIZED_INTENT_BY_CATEGORY`
   (see Section 5);
3. echoes FRAME-C's `expected_item_kinds_touched`,
   `expected_candidate_surface`, and `expected_rejection_surface`
   into the legacy mirror keys without rewording;
4. derives `ambiguity_observed` from FRAME-C's `ambiguity_level`
   (True iff the literal `"high"`);
5. forces the six legacy gating booleans (`selection_made`,
   `measurement_authorized`, `real_benchmark_authorized`,
   `real_benchmark_ready`, `source_qualification_authorized`,
   `corpus_admission_authorized`) to literal False.

## 5. Translation table (FRAME-C category -> legacy intent label)

```
_NORMALIZED_INTENT_BY_CATEGORY = {
    "A. clear single-intent":
        "clear_single_intent",
    "B. workflow intent":
        "workflow_intent",
    "C. skill intent":
        "skill_intent",
    "D. agent/persona confusion":
        "agent_surface_workflow_intent",
    "E. instruction confusion":
        "instruction_surface_workflow_intent",
    "F. prompt-search-shaped but workflow-intent":
        "prompt_surface_workflow_intent",
    "G. ambiguous":
        "ambiguous_user_intent",
    "H. no-route":
        "no_route",
    "I. near-miss/rejection":
        "near_miss_rejection",
}
```

This table is asserted at import time to cover every FRAME-C
`WORKSHOP_PROMPT_CATEGORIES` entry. The table is a pure rename
only; FRAME-C decides the category and FRAME-D translates the
label. The table is bounded by FRAME-D and is NOT claimed
exhaustive.

## 6. Output contract (preserved from the legacy mapper)

The clean-pass output is a fixed 14-key dict whose key set
equals:

```
intent_mapper_kind
workshop_prompt_record
normalized_intent_observation
expected_item_kinds_touched
candidate_surface_expected
rejection_surface_expected
ambiguity_observed
selection_made
measurement_authorized
real_benchmark_authorized
real_benchmark_ready
source_qualification_authorized
corpus_admission_authorized
mapper_note
```

`workshop_prompt_record` is a fixed seven-key dict whose key set
equals:

```
workshop_prompt_id
category
prompt_text
expected_item_kinds_touched
expected_candidate_surface
expected_rejection_surface
boundary_note
```

`boundary_note` is the literal `not admitted; not qualified;
workshop metadata only`, identical to `WORKSHOP_BOUNDARY_NOTE`
re-exported from the workshop derived-trace module and identical
to the literal emitted by the FRAME-C `workshop_prompt_record`
adapter.

`category` is one of the bounded nine workshop trace categories
(`A. clear single-intent`, `B. workflow intent`, `C. skill
intent`, `D. agent/persona confusion`, `E. instruction
confusion`, `F. prompt-search-shaped but workflow-intent`,
`G. ambiguous`, `H. no-route`, `I. near-miss/rejection`).

The six gating booleans are literal False on every emitted path.

## 7. Named exceptions

The shim preserves the three legacy named exceptions:

- `NonStringUserPrompt` - raised when `input_prompt` is not a
  string.
- `EmptyUserPrompt` - raised when `input_prompt` is empty or
  whitespace-only after trimming.
- `InvalidWorkshopPromptId` - raised when `workshop_prompt_id`
  is not a non-empty string.

Translation rules at the shim boundary:

- FRAME-A `NonStringInputPrompt` -> `NonStringUserPrompt`.
- FRAME-A `EmptyInputPrompt` -> `EmptyUserPrompt`.
- FRAME-A `WhitespaceOnlyInputPrompt` -> `EmptyUserPrompt`.
- FRAME-C `InvalidWorkshopPromptId` -> mapper
  `InvalidWorkshopPromptId` (defensive; the shim validates
  `workshop_prompt_id` before calling FRAME-B and FRAME-C, so
  the FRAME-C named exception is not expected on the legacy
  contract path).

The shim emits an additional mapper-scoped halt event with one
of the bounded halt reasons before raising the translated legacy
exception, so existing legacy halt-reason consumers continue to
observe a mapper-scoped halt alongside the FRAME-A halt event.

## 8. RK-059 - upstream FRAME-C synthesis gaps surfaced by FRAME-D

The FRAME-D rework pass (WO-L0-WORKSHOP-FRAME-D-R) derives
output strictly from FRAME-C. Three pre-FRAME-D legacy
categorical assertions diverge from FRAME-C-actual behavior;
these divergences are recorded as RK-059 in
`ai-search/00-open-questions.md` and remain OPEN. Closure is
reserved for a later Codex-authorized FRAME-C-hardening packet;
closure must NOT happen inside FRAME-D and must NOT introduce a
parallel keyword classifier in any downstream module.

The three gaps:

1. **agent + deploy**: `action.deploy` + `object.agent` without
   a workflow-domain signal or event-triggered constraint
   classifies as `A. clear single-intent` with `["agent"]`
   (FRAME-C) rather than `D. agent/persona confusion` with
   `["agent", "workflow_file"]` (pre-FRAME-D legacy).
2. **prompt + deploy**: `action.deploy` +
   `output_shape.prompt_collection_request` without a
   workflow-domain signal or event-triggered constraint
   classifies as `H. no-route` with `["none"]` (FRAME-C) rather
   than `F. prompt-search-shaped but workflow-intent` with
   `["cookbook_entry", "workflow_file"]` (pre-FRAME-D legacy).
3. **bare ambiguity**: Bare ambiguity phrases like
   `make this better`, `fix this`, or `help with my project` do
   not have a dedicated FRAME-B family and so classify as
   `H. no-route` with `["none"]` and `ambiguity_level == "none"`
   (FRAME-C) rather than `G. ambiguous` with multiple kinds and
   `ambiguity_observed == True` (pre-FRAME-D legacy).

Three smoke-test methods document these gaps with docstring
pointers to RK-059:

- `test_agent_workflow_prompt_maps_to_clear_single_intent_under_frame_c`
- `test_prompt_surface_workflow_intent_maps_to_no_route_under_frame_c`
- `test_bare_ambiguity_phrase_maps_to_no_route_under_frame_c`

## 9. Validation order

1. Mapper-started event emitted.
2. FRAME-A called; named exceptions translated to legacy
   exceptions and halt events emitted.
3. `workshop_prompt_id` non-empty string check (raises legacy
   `InvalidWorkshopPromptId`); this precedes the FRAME-B and
   FRAME-C calls so neither runs when the id is invalid.
4. FRAME-B called over the validated FRAME-A view.
5. FRAME-C called over the validated FRAME-B ledger and the
   validated `workshop_prompt_id`.
6. `_derive_legacy_output` translates the FRAME-C frame to the
   legacy fourteen-key shape via direct echo plus the rename
   table.
7. Defensive `boundary_note` literal check.
8. Mapper-completed event emitted with the observed FRAME-A,
   FRAME-B, and FRAME-C kind literals.
9. Defensive output and `workshop_prompt_record` shape-drift
   checks raise `AssertionError` on mismatch.

## 10. Non-claims (carried forward)

- The shim does not classify a route, does not select an item,
  does not qualify a source, does not admit a corpus, and does
  not retrieve, embed, vectorize, score, rank, compute
  similarity, or compute distance.
- The shim does not call any LLM, provider, external API,
  embedding service, vector store, ANN backend, reranker, or
  retrieval family.
- The shim does not perform file IO, network calls, URL fetch /
  download / crawl / browser automation, PDF text extraction,
  hash computation, external process spawning, or integration
  with editor extensions / chat plugins / third-party model APIs
  / external collaborator tools.
- The shim does not select architecture, vendor, library,
  index-family, production system, retrieval family, ANN
  backend, reranker, or any indexing-class.
- The shim does not create Source Cards or Route Cards.
- The shim does not authorize new code, new datasets, benchmark
  execution, metric collection, artifact contracts, or
  real-benchmark-ready.
- The shim does not add field names from the forbidden output
  field set (`ranking_performed`, `scoring_performed`,
  `confidence`, `score`, `distance`, `best_match`, `threshold`,
  `similarity`).
- The shim does not close OQ-003, OQ-015, OQ-031, OQ-035,
  OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
- The shim does not close RK-058. Closure remains reserved for a
  later Codex-authorized packet.
- The shim does not close RK-059. Closure remains reserved for a
  later Codex-authorized FRAME-C-hardening packet.
- The shim does not duplicate RK-039.
- All DC-020 through DC-073 boundary invariants carry forward.

## 11. Known surface widening

FRAME-A enforces `MAX_PROMPT_LENGTH = 2048` and raises
`InputPromptExceedsMaxLength` for prompts longer than 2048
characters. The pre-FRAME-D legacy mapper did not enforce a
length cap. The shim does NOT translate this exception (no
legacy exception name applies), so callers passing prompts
longer than 2048 characters now observe the FRAME-A named
exception. The legacy smoke-test suite does not exercise this
path. This is recorded as a known surface widening, not as a
contract change for the legacy categorical strings or the
14-key output shape.

## 12. Test surface

`harness/tests/test_level0_workshop_user_intent_mapper.py`
contains 42 tests across four TestCase classes:

- `CleanMappingTest` (16): legacy smoke tests covering deploy /
  CI / skill / agent+deploy / instruction+pipeline /
  prompt+deploy / bare-ambiguity / no-route / repo-meta /
  Turkish workflow / Turkish skill / downstream-compatible record
  shape / authorization-boolean check / event emission. Three
  cases were renamed and reworded to reflect FRAME-C-actual
  behavior with docstring pointers to RK-059
  (`test_agent_workflow_prompt_maps_to_clear_single_intent_under_frame_c`,
  `test_prompt_surface_workflow_intent_maps_to_no_route_under_frame_c`,
  `test_bare_ambiguity_phrase_maps_to_no_route_under_frame_c`).
- `RejectionTest` (4): legacy halt-and-translate tests
  (non-string, empty, invalid id, string-immutability).
- `StaticScanTest` (1): legacy file-IO / network / indexing
  token absence.
- `LegacyContractParityTest` (21): proves the FRAME-D shim
  derives output strictly from FRAME-C while preserving the
  legacy fourteen-key shape, the legacy seven-key
  `workshop_prompt_record` shape, the legacy three named
  exceptions, and the six legacy gating booleans literal False;
  verifies FRAME-A / FRAME-B / FRAME-C pipeline events in the
  log; verifies the FRAME kind literals in the mapper-completed
  event; verifies absence of forbidden output field names in
  both output and source; verifies ASCII purity of the module
  file; verifies presence of the FRAME-A / FRAME-B / FRAME-C
  public function names in the module source; and verifies
  absence of the legacy keyword classifier definition and the
  ten legacy keyword tables in the module source.

## 13. Verification

- `python -B -m unittest harness.tests.test_level0_workshop_user_intent_mapper`
  -> 42/42 OK.
- `python -B -m unittest discover -s harness/tests` -> 1484/1484
  OK (baseline 1461 with 19 prior mapper tests removed and 42
  new mapper tests added).
- Module source ASCII-only.
- No `__pycache__` artifacts under `harness/`.
- Project root contains exactly `ai-search/`, `harness/`, and
  `benchmark-fixtures/`.
- `benchmark-fixtures/` unchanged.
- FRAME-A, FRAME-B, FRAME-C modules / tests unchanged.
- Workshop trace / review modules / tests unchanged.
- WO-50 through WO-62 modules / tests unchanged.
- `00-controller-checklist.md` unchanged.
- OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056,
  OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
- RK-039 single.
- RK-058 remains OPEN.
- RK-059 added OPEN.
- Real-benchmark-ready remains NO.
