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
Real-benchmark-ready remains NO. RK-058 remains OPEN. RK-059
(FRAME-C synthesis gaps surfaced by FRAME-D smoke tests) was
partially hardened by WO-L0-WORKSHOP-FRAME-C-HARDEN-01 via
FRAME-C synthesis rule additions (bare-ambiguity short-circuit,
workflow_file co-fire from action.deploy, cookbook_entry
extension to prompt_collection_request). RK-059 remains OPEN
because no-signal bare ambiguity such as `help with my project`
still needs FRAME-B signal coverage. OQ-003, OQ-015, OQ-031,
OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075,
OQ-076 remain OPEN. RK-039 single.

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

## 8. RK-059 partial hardening - FRAME-C synthesis fixed where signal evidence exists

The FRAME-D rework pass (WO-L0-WORKSHOP-FRAME-D-R) derived
output strictly from FRAME-C and recorded three pre-FRAME-D
legacy categorical divergences as RK-059. The follow-up packet
**WO-L0-WORKSHOP-FRAME-C-HARDEN-01** fixes the FRAME-C synthesis
cases that have signal evidence, but does not close RK-059
because one no-signal bare-ambiguity case still requires FRAME-B
coverage. The hardening is at the FRAME-C synthesis layer (not in
FRAME-D) via three deterministic rule additions:

1. **bare-ambiguity short-circuit** in
   `_compute_shape_touch_plan`: when the FRAME-B ledger contains
   an action signal alone (no target / domain / output_shape /
   constraint / repo-meta / out-of-scope), emit a bounded
   three-entry ambiguous list (`skill`, `instruction`,
   `workflow_file`) and add `bare_ambiguity_action_only` to
   `ambiguity_reasons`. The category selector short-circuits to
   `G. ambiguous`. Partially hardens gap 3 for action-backed
   bare ambiguity (`make this better`, `fix this`).
2. **workflow_file co-fire from action.deploy**: when
   `primary_action == "deploy"` and the primary workflow rule
   did NOT fire (no workflow domain / workflow target / event
   constraint) but at least one non-workflow candidate already
   fires, append `workflow_file` with grade `"ambiguous"`. The
   downstream `>= 2 candidate kinds` rule then sets
   `ambiguity_level == "high"`, and the category selector
   returns D (agent + workflow), F (cookbook + workflow), or G
   as appropriate. Closes gap 1 (`Use an agent persona to deploy
   this project`) and contributes to gap 2.
3. **`cookbook_entry` extended to `prompt_collection_request`**:
   `_is_cookbook_intent` now returns True for
   `requested_output_shape in (recipe,
   prompt_collection_request)`. Combined with the workflow_file
   co-fire rule above, this closes gap 2 (`Give me a prompt
   that deploys a static site`).

RK-059 status: OPEN, with DC-075 recording partial hardening
evidence. The corresponding smoke tests have been renamed and
reworded to assert the intended
legacy categorical contract through FRAME-D's FRAME-C-derived
output:

- `test_agent_workflow_prompt_maps_to_confusion_category`
- `test_prompt_surface_workflow_intent_maps_to_cookbook_and_workflow`
- `test_bare_ambiguity_phrase_surfaces_ambiguity`
- `test_bare_ambiguity_fix_phrase_surfaces_ambiguity`

The FRAME-D module did NOT change in this hardening packet; the
hardening is entirely in `harness/level0_workshop_canonical_intent_frame.py`.

### Residual RK-059 / FRAME-B coverage limitation

Bare-ambiguity inputs that FRAME-B cannot extract any action
signal from (for example `help with my project`, whose tokens
are absent from every FRAME-B canonical and alias) still
classify as `H. no-route` via the no-signal path because the
bare-ambiguity rule requires at least one `action.*` signal to
fire in the FRAME-B ledger. This is a FRAME-B coverage concern
(would require extending FRAME-B's families), and remains the
open RK-059 residual for a future Codex-authorized FRAME-B
coverage packet.

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
- RK-059 remains OPEN after WO-L0-WORKSHOP-FRAME-C-HARDEN-01;
  DC-075 records partial hardening at the FRAME-C synthesis
  layer, and the FRAME-D shim was NOT modified by that packet.
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
contains 44 tests across four TestCase classes:

- `CleanMappingTest` (16): legacy smoke tests covering deploy /
  CI / skill / agent+deploy / instruction+pipeline /
  prompt+deploy / bare-ambiguity / residual no-signal
  bare-ambiguity / no-route / repo-meta /
  Turkish workflow / Turkish skill / downstream-compatible record
  shape / authorization-boolean check / event emission. Three
  cases were renamed and reworded to assert the intended
  categorical contract after FRAME-C hardening; one residual test
  records that `help with my project` still no-routes until
  FRAME-B emits a signal for it.
- `RejectionTest` (4): legacy halt-and-translate tests
  (non-string, empty, invalid id, string-immutability).
- `StaticScanTest` (1): legacy file-IO / network / indexing
  token absence.
- `LegacyContractParityTest` (23): proves the FRAME-D shim
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
