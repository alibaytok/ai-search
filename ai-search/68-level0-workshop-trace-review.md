# 68. Level 0B Workshop Trace Review Scaffold (WO-L0-WORKSHOP-REVIEW-01)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-WORKSHOP-REVIEW-01

## Authority

This boundary document records the scaffold surface of
`harness/level0_workshop_trace_review.py`. It does NOT modify
canonical authority. Canonical authority remains with
`ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. If this document ever conflicts
with the canonical documents, the canonical document wins and this
document must be corrected.

`ai-search/00-wo-constraints.md` (Constraints v1) is a compiled
reference used alongside this boundary doc. It is descriptive only.
On conflict, both must be reconciled against the canonical
documents.

## Scope and Boundary

WO-L0-WORKSHOP-REVIEW-01 added the final compact review layer for
the Level 0B workshop path. The module consumes an already-loaded
output dict produced by the upstream workshop derived-trace
scaffold and emits a fixed-shape review observation: shape checks,
per-category counts, candidate / workflow / rejection surface
presence flags, ambiguity / no-selection / rejection invariants
per prompt, and a bounded list of next-gap notes.

The module performs no file IO, no network call, no URL fetch /
download / crawl / browser automation, no PDF text extraction, no
hash computation, no external process spawning, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools.

WO-L0-WORKSHOP-REVIEW-01 does NOT authorize real benchmark
execution, real or mock adapter invocation, source qualification,
corpus admission, extraction, normalization, candidate-fragment
promotion to route, architecture / vendor / library / index family
/ ANN backend / reranker / retrieval family / production-system
selection, Source Card or Route Card creation, OQ closure, or
duplication of RK-039.

Passing this review means only that the scaffold trace surface is
internally coherent for the Level 0B workshop seed. It does NOT
mean sufficient, necessary, best, complete, production-ready,
recommended, selected, benchmark-ready, or route-ready.
Real-benchmark-ready remains NO.

WO-L0-WORKSHOP-RK058-CLOSURE-01 addendum: the upstream workshop
derived-trace test now derives its 26 `workshop_prompt_record`
inputs by routing the planning-doc `prompt_text` strings through
the FRAME-D shim `map_level0_workshop_user_intent`. The review
module's contract is unchanged - it still consumes an
already-loaded workshop derived-trace output dict - but the
records the review module sees in the test layer are now
FRAME-C-derived rather than predeclared. RK-058 closed by
DC-077. Residual planning-intent vs FRAME-D-actual divergences
are recorded as RK-060 OPEN; the review module does not need to
change for any of those residuals because the upstream trace
contract is preserved.

## Public Surface

```
run_level0_workshop_trace_review(
    workshop_trace_report, event_log
) -> dict
```

The module imports only:

- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`

The module invokes NO prior-WO public function. It does not import
or call the upstream workshop derived-trace scaffold or any other
prior-WO public function (verified by static-scan test). The
upstream scaffold may appear at the test layer to build a clean
synthetic input fixture; that is a test-only concern outside the
module under test.

## Inputs

- `workshop_trace_report`: already-loaded dict whose shape matches
  the upstream workshop derived-trace nineteen-key clean-pass
  output.
- `event_log`: an `EventLog` instance from `harness.event_log`.

## Required Input Keys

Exactly nineteen required keys, no extras:

`workshop_trace_kind`, `item_count`, `prompt_count`,
`derived_material_records`, `derived_material_count`,
`candidate_route_fragment_records`, `candidate_route_fragment_count`,
`candidate_workflow_fragment_records`,
`candidate_workflow_fragment_count`, `rejected_material_records`,
`rejected_material_count`, `per_prompt_trace_summary`,
`selection_made`, `measurement_authorized`,
`real_benchmark_authorized`, `real_benchmark_ready`,
`source_qualification_authorized`, `corpus_admission_authorized`,
`workshop_trace_note`.

`workshop_trace_kind` must equal the literal
`level0_workshop_derived_trace`.

## Expected Counts

| field | expected |
|-------|----------|
| `item_count` | 70 |
| `prompt_count` | 26 |
| `derived_material_count` | 70 |
| `candidate_route_fragment_count` | 51 |
| `candidate_workflow_fragment_count` | 13 |
| `rejected_material_count` | 6 |
| `len(derived_material_records)` | 70 |
| `len(candidate_route_fragment_records)` | 51 |
| `len(candidate_workflow_fragment_records)` | 13 |
| `len(rejected_material_records)` | 6 |
| `len(per_prompt_trace_summary)` | 26 |

Any deviation raises `WorkshopTraceCountMismatch`
(halt-before-raise).

## Authorization-Boolean Constraint

The six gating booleans (`selection_made`, `measurement_authorized`,
`real_benchmark_authorized`, `real_benchmark_ready`,
`source_qualification_authorized`, `corpus_admission_authorized`)
in the input must all be literal False; any other value raises
`WorkshopTraceAuthorizationBooleanFlipped`.

## Nested-Record Constraints

For every record in `derived_material_records`,
`candidate_route_fragment_records`,
`candidate_workflow_fragment_records`, `rejected_material_records`,
and `per_prompt_trace_summary`:

- No record may carry any of `official`, `is_route`,
  `is_official_route`, `selected_as_official`,
  `official_route_authorized`, `route_authorized`,
  `production_route`, `selected_route`, `executable`,
  `route_state`, or `plane`. Presence of any such key raises
  `WorkshopTraceRouteStatusFieldPresent`.
- Where `candidate_only` is present, it must be literal True;
  otherwise raises `WorkshopTraceCandidateOnlyNotTrue`.
- Where `qualified`, `corpus_admitted`, `route_object_created`, or
  `source_material_extracted` is present, it must be literal False;
  otherwise raises `WorkshopTraceForbiddenFlipPresent`.

## Per-Prompt Invariants

For each entry in `per_prompt_trace_summary`:

- Category `G. ambiguous` must carry `ambiguity_observed: True`;
  otherwise raises `WorkshopTraceAmbiguousMissingMarker`.
- Category `H. no-route` must carry
  `attached_candidate_route_fragment_count == 0`,
  `attached_candidate_workflow_fragment_count == 0`,
  `attached_rejected_material_count == 0`, and
  `no_selection_reason == "prompt_out_of_repo_scope"`; otherwise
  raises `WorkshopTraceNoRouteInvariantViolated`.
- Category `I. near-miss/rejection` must carry
  `attached_candidate_route_fragment_count == 0`,
  `attached_candidate_workflow_fragment_count == 0`,
  `attached_rejected_material_count > 0`, and
  `no_selection_reason == "repo_meta_section_near_miss"`; otherwise
  raises `WorkshopTraceNearMissInvariantViolated`.

## Per-Category Count Invariants

After per-prompt scans:

| category | expected |
|----------|----------|
| `G. ambiguous` | 3 |
| `H. no-route` | 2 |
| `I. near-miss/rejection` | 2 |

Any deviation raises `WorkshopTraceCountMismatch`.

## Validation Order

1. Type check: `workshop_trace_report` is a dict.
2. Required key presence; unknown key rejection.
3. Input forbidden-language scan.
4. `workshop_trace_kind` literal check.
5. Top-level count checks (six counts) plus nested collection
   length checks (five collections).
6. Authorization-boolean check (six booleans literal False).
7. Nested route-status-field check (five collections).
8. Nested `candidate_only` / forbidden-flip check (five
   collections).
9. Per-prompt invariant checks (ambiguous / no-route /
   near-miss).
10. Per-category count check (three counts).
11. Output forbidden-language scan.

## Output Shape

Clean-pass output dict has exactly twenty-four keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `workshop_review_kind` | str | `"level0_workshop_trace_review"` |
| `input_trace_kind` | str | `"level0_workshop_derived_trace"` |
| `review_passed` | bool | literal True |
| `review_halt_required` | bool | literal False |
| `observed_item_count` | int | 70 |
| `observed_prompt_count` | int | 26 |
| `observed_candidate_route_fragment_count` | int | 51 |
| `observed_candidate_workflow_fragment_count` | int | 13 |
| `observed_rejected_material_count` | int | 6 |
| `ambiguous_prompt_count` | int | 3 |
| `no_route_prompt_count` | int | 2 |
| `near_miss_prompt_count` | int | 2 |
| `candidate_surface_observed` | bool | True |
| `workflow_surface_observed` | bool | True |
| `rejection_surface_observed` | bool | True |
| `route_created` | bool | literal False |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `source_qualification_authorized` | bool | literal False |
| `corpus_admission_authorized` | bool | literal False |
| `next_gap_notes` | list of str | bounded four-entry list |
| `review_note` | str | constant Level 0B non-claim note |

`next_gap_notes` is the literal list:

- `"semantic_content_extraction_not_tested"`
- `"real_indexing_not_implemented"`
- `"route_selection_not_authorized"`
- `"cross_vendor_seed_not_executed"`

`review_passed: True` and `review_halt_required: False` are emitted
only on clean pass. Halt paths raise named exceptions before any
result dict is built.

## Static Scan

The module file contains none of:

- `open(`, `pathlib`
- `urllib`, `http.client`, `socket`
- `import requests`, `from requests`, `requests.`
- `subprocess`, `os.system`, `shutil`
- `hashlib`, `.hexdigest`, `.sha256`
- `def query`, `def search`, `def retrieve`, `def rank`
- `score`, `scoring`
- `copilot`, `waza`, `vscode`, `openai`, `anthropic`, `claude_api`,
  `llm`

The module file contains no name of any prior-WO public function
(WO-50 through WO-62 plus the four manual-seed L0 modules plus the
upstream workshop derived-trace public function).

## What This Scaffold Does NOT Do

- Does NOT read any planning document at runtime.
- Does NOT fetch any URL, download any content, or crawl any
  source.
- Does NOT read any local file.
- Does NOT extract PDF text.
- Does NOT compute any hash via `hashlib` or any other library.
- Does NOT spawn external processes or shells.
- Does NOT integrate with editor extensions, chat plugins,
  third-party model APIs, or external collaborator tools.
- Does NOT invoke any prior-WO public function (verified by
  static-scan test). Tests at the test layer may invoke the
  upstream workshop derived-trace public function to build a clean
  synthetic input; the module under test does not.
- Does NOT mutate inputs (verified by regression test).
- Does NOT flip any of the seven gating booleans
  (`route_created`, `selection_made`, `measurement_authorized`,
  `real_benchmark_authorized`, `real_benchmark_ready`,
  `source_qualification_authorized`,
  `corpus_admission_authorized`).
- Does NOT promote any candidate fragment to a route.
- Does NOT compute any similarity / distance / ranking / metric.

## Test Surface

`harness/tests/test_level0_workshop_trace_review.py` contains 77
tests across the following test classes:

- `CleanPassTest` (28) - output shape, fixed key set, all
  count and surface-presence fields, all seven literal-False
  gating booleans, next-gap-notes literal list, review_note
  non-empty, started / completed events, no halt.
- `TopLevelInputValidationTest` (4) - non-dict report halts;
  missing top-level key halts; unknown top-level key halts;
  invalid `workshop_trace_kind` halts.
- `CountMismatchTest` (11) - each of the six expected count fields
  plus five nested collection lengths, when mismatched, raises
  `WorkshopTraceCountMismatch`.
- `AuthorizationBooleanFlipTest` (6) - each of the six gating
  booleans flipped to True halts.
- `NestedRecordCheckTest` (8) - route-status field injection halts
  for three different nested collections; `candidate_only: False`
  halts; each of the four forbidden flip keys (`qualified`,
  `corpus_admitted`, `route_object_created`,
  `source_material_extracted`) flipped to True halts.
- `PerPromptInvariantTest` (7) - ambiguous prompt without marker
  halts; no-route prompt with candidate halts; no-route prompt
  with wrong reason halts; near-miss prompt with route candidate
  halts; near-miss prompt with workflow candidate halts;
  near-miss prompt with empty rejected attachment halts;
  near-miss prompt with wrong reason halts.
- `ForbiddenLanguageTest` (2) - forbidden phrase in input halts;
  forbidden claim phrase in input halts.
- `InputIsolationTest` (1) - input dict unchanged after clean
  pass.
- `StaticScanTest` (10) - absence of file-IO, network,
  HTTP-library, subprocess / shell, hashlib, retrieval-verb,
  scoring, and external-integration tokens; absence of any
  prior-WO public function name including the upstream workshop
  derived-trace public function; module file is ASCII.

## Non-Claim Constraints

WO-L0-WORKSHOP-REVIEW-01 does not claim any observed count,
observed surface flag, next-gap-note literal, per-prompt invariant
check, or computed observation is sufficient, necessary, superior,
best, complete, production-ready, recommended, or selected.
Passing this review means only that the scaffold trace surface is
internally coherent for the Level 0B workshop seed. The bounded
required-input-key set (nineteen entries), the bounded gating
booleans (six on input, seven on output), the bounded
route-status field list (eleven entries), the bounded forbidden
flip keys (four entries), the bounded per-prompt invariant rules
(three categories), the bounded next-gap-notes literal list (four
entries), and the twenty-four `ALLOWED_OUTPUT_KEYS` are bounded by
WO-L0-WORKSHOP-REVIEW-01 and are NOT claimed exhaustive.

All DC-020 through DC-069 boundary invariants carry forward.
WO-L0-WORKSHOP-REVIEW-01 does not amend or broaden DC-003 through
DC-069. Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031,
OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076
remain OPEN. RK-039 remains active and is not duplicated.
