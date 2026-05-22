# 66. Consolidated Level 0B Manual Seed End-to-End Visible Trace (WO-L0-E2E-01)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-E2E-01

## Authority

This boundary document records the scaffold surface of
`harness/level0_manual_seed_end_to_end_trace.py`. It does NOT modify
canonical authority. Canonical authority remains with
`ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. If this document ever conflicts
with the canonical documents, the canonical document wins and this
document must be corrected.

`ai-search/00-wo-constraints.md` (Constraints v1) is a compiled
reference used alongside this boundary doc. It is descriptive only.
On conflict, both must be reconciled against the canonical documents.

## Scope and Boundary

WO-L0-E2E-01 wires the already-approved Level 0B manual seed pieces
into a single callable flow:

```
item_records + prompt_records
    -> WO-L0-MATERIAL-01 materialization
    -> auto-built trace_case_records (non-empty source attachments)
    -> WO-L0-TRACE-01 trace execution
    -> aggregate per-prompt visible trace summary
```

This consolidation is NOT real indexing, NOT real retrieval, NOT
source qualification, NOT corpus admission, NOT extraction, NOT
normalization, NOT candidate-fragment invention, NOT a route object,
NOT a Source Card, NOT permission to flip any authorization /
readiness boolean, NOT a benchmark-ready flip, NOT IDE / chat /
collaborator / Copilot / Waza / VS Code / LLM integration, and NOT
architecture / vendor / library / index family / ANN backend /
reranker / retrieval family / production-system selection. The
module performs no file IO, no network call, no URL fetch / download
/ crawl / browser automation, no PDF text extraction, no hash
computation, and no external process spawning.
Real-benchmark-ready remains NO.

## Public Surface

```
run_level0_manual_seed_end_to_end_trace(
    item_records, prompt_records, event_log
) -> dict
```

The module imports only:

- `harness.level0_manual_seed_materialization.run_level0_manual_seed_materialization`
- `harness.level0_manual_seed_trace_execution.run_level0_manual_seed_trace_execution`
- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`

The module invokes only the two prior-WO public functions named
above. It does NOT directly invoke the WO-54 trace, WO-55 register,
WO-56 bridge, WO-57 smoke package, WO-58 diagnostic reporter,
WO-59 visible-report, or WO-L0-RUN-01 visible-report public
functions (verified by static-scan test). WO-59 is reached
transitively via WO-L0-TRACE-01 and WO-L0-RUN-01 is reached
transitively via WO-L0-MATERIAL-01, by design.

## Inputs

- `item_records`: already-loaded list, validated transitively by
  WO-L0-MATERIAL-01 -> WO-L0-RUN-01.
- `prompt_records`: already-loaded list, validated transitively by
  WO-L0-MATERIAL-01 -> WO-L0-RUN-01.
- `event_log`: an `EventLog` instance from `harness.event_log`.

## Source-Touch Filtering Semantic

For each prompt, `expected_source_touch` is parsed for `L0-SRC-XXX`-
shaped tokens:

- **Single token** (`L0-SRC-001`): attach the materialized records
  whose corresponding item carries that `source_id` (the WO-L0-ITEMS-01
  inventory source identifier, not the synthetic `L0-MAT-SRC-XXX`).
- **Multi-token** (`L0-SRC-001; L0-SRC-006`): attach the union of
  matching records.
- **Prose only** (`none expected`, `all inventory sources`): the
  parser finds no `L0-SRC-XXX` tokens; the module falls back to
  attaching all materialized records.
- **Token outside `EXPECTED_SOURCE_IDS`** (e.g. `L0-SRC-999`):
  raise `PromptExpectedSourceTouchInvalid` and halt.
- **Final attachment empty** (defensive; can only happen under a
  broken materialization that returns short lists): raise
  `TraceCaseSourceAttachmentEmpty` and halt before invoking the
  WO-L0-TRACE-01 delegate.

## Trace Case Construction

For each prompt, one trace_case_record is built with these ten
fields (matching WO-L0-TRACE-01's `REQUIRED_TRACE_CASE_FIELDS`):

| field | value |
|-------|-------|
| `case_id` | `L0-E2E-CASE-{NNN}` (1-based 3-digit index) |
| `prompt_id` | from the prompt record |
| `expected_category` | from the prompt record `category` |
| `input_prompt` | from the prompt record `prompt_text` |
| `source_reference_records` | filtered materialized references |
| `source_records` | filtered materialized source records |
| `expected_source_touch` | from the prompt record |
| `expected_candidate_shape` | from the prompt record |
| `expected_rejection_targets` | from the prompt record |
| `boundary_notes` | literal `not admitted; not qualified; manual-seed trace only` |

## Validation Order

1. Delegate to `run_level0_manual_seed_materialization` for
   materialization. If the delegate raises, control never reaches
   any subsequent step.
2. `_validate_materialization_shape` checks the returned dict
   carries the required keys (`manual_seed_shape_observation`,
   `source_reference_records`, `source_records`,
   `source_reference_count`, `source_record_count`), that the two
   record lists are lists, that each count matches its list length,
   and that the two record lists have the same length. Raises
   `MaterializationReturnedInvalidShape` on failure.
3. Per prompt: filter materialized records by
   `expected_source_touch`; raise
   `PromptExpectedSourceTouchInvalid` if a parseable token is
   outside the bounded `_EXPECTED_SOURCE_IDS` set; raise
   `TraceCaseSourceAttachmentEmpty` if the attached set is empty.
4. Construct 23 trace_case_records.
5. Delegate to `run_level0_manual_seed_trace_execution` for trace
   execution. If the delegate raises, control never reaches any
   subsequent step.
6. `_validate_trace_execution_shape` checks the returned dict
   carries the required keys (`manual_seed_shape_observation`,
   `trace_case_count`, `visible_reports`, `visible_report_count`,
   `review_halt_required_count`) and that `visible_reports` is a
   list. Raises `TraceExecutionReturnedInvalidShape` on failure.
7. Build per-prompt summary and aggregate totals.
8. Output forbidden-language scan over the result dict (else
   `ForbiddenLanguageInLevel0EndToEndTrace`).

Every raise is preceded by an `event_log.halt(reason=..., ...)`
recording (halt-before-raise per Constraints v1 D3).

## Output Shape

Clean-pass output dict has exactly sixteen keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `end_to_end_kind` | str | `"level0_manual_seed_end_to_end_trace"` |
| `materialization_observation` | dict | full WO-L0-MATERIAL-01 clean-pass dict |
| `trace_execution_observation` | dict | full WO-L0-TRACE-01 clean-pass dict |
| `trace_case_count` | int | 23 |
| `source_reference_count` | int | 65 |
| `source_record_count` | int | 65 |
| `visible_report_count` | int | 23 |
| `per_prompt_trace_summary` | list of dict | 23 nine-field summary entries |
| `candidate_route_fragment_total` | int | tally from embedded visible reports |
| `candidate_workflow_fragment_total` | int | tally from embedded visible reports |
| `review_halt_required_count` | int | from trace execution observation |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `end_to_end_note` | str | constant Level 0B non-claim note |

## Per-Prompt Summary Shape

Each entry of `per_prompt_trace_summary` carries exactly nine fields:

| field | source |
|-------|--------|
| `prompt_id` | from prompt record |
| `category` | from prompt record |
| `case_id` | generated `L0-E2E-CASE-{NNN}` |
| `source_reference_count` | length of attached references |
| `source_record_count` | length of attached records |
| `linked_source_count` | from WO-59 report |
| `candidate_route_fragment_count` | from WO-59 report |
| `candidate_workflow_fragment_count` | from WO-59 report |
| `review_halt_required` | from WO-59 report |

## What This Scaffold Does NOT Do

- Does NOT read any planning document at runtime.
- Does NOT fetch any URL, download any content, or crawl any source.
- Does NOT read any local file.
- Does NOT extract PDF text.
- Does NOT compute any hash.
- Does NOT spawn external processes or shells.
- Does NOT integrate with editor extensions, chat plugins,
  third-party model APIs, or external collaborator tools.
- Does NOT directly invoke the WO-54 trace, WO-55 register,
  WO-56 bridge, WO-57 smoke package, WO-58 diagnostic reporter,
  WO-59 visible-report, or WO-L0-RUN-01 visible-report public
  functions (verified by static-scan test).
- Does NOT qualify any source.
- Does NOT admit any source to corpus.
- Does NOT extract, normalize, or invent candidate fragments.
- Does NOT decide architecture, vendor, library, index family,
  ANN backend, reranker, retrieval family, or production system.
- Does NOT mutate inputs (verified by regression test).
- Does NOT flip any of the four standard authorization / readiness
  / selection booleans.

## Known Gap (Documented; Out of Scope)

Because WO-L0-MATERIAL-01 emits source_records that carry no
derived material (by WO-56 contract), and because this WO does not
introduce derived-material materialization, the WO-59 reports
embedded in the trace execution observation will report
`candidate_route_fragment_count: 0` and
`candidate_workflow_fragment_count: 0` on every prompt. The
aggregate `candidate_route_fragment_total` and
`candidate_workflow_fragment_total` are accordingly zero. This is
acceptable for visible-trace plumbing verification. A future Work
Order that introduces a derived-material materialization layer
would change these totals; that work is out of WO-L0-E2E-01 scope.

## Test Surface

`harness/tests/test_level0_manual_seed_end_to_end_trace.py` contains
43 tests across the following test classes:

- `CleanPassTest` (11) - output shape, key set, count fields,
  literal-False booleans, embedded materialization / trace
  observations, started / completed events, no halt.
- `EmbeddedObservationTest` (2) - materialization observation
  embedded with correct counts; trace execution observation
  embedded with correct counts.
- `DelegateOrderTest` (1) - materialization invoked before trace
  execution (verified by patch-wrapped tracing).
- `PerPromptSummaryTest` (3) - 23 entries; entries carry the nine
  required fields; entries preserve prompt order; case_ids unique
  and prefixed `L0-E2E-CASE-`.
- `SourceTouchFilteringTest` (4) - single valid token attaches
  matching subset (12 records); multi-token attaches union (23);
  prose-only falls back to all (65); unknown token rejected.
- `EmptyAttachmentTest` (1) - mocked materialization returning
  empty source lists triggers
  `TraceCaseSourceAttachmentEmpty` before trace execution is
  invoked.
- `MaterializationShapeValidationTest` (5) - mocked materialization
  returning non-dict rejected; mocked materialization missing
  required key rejected; materialization reference count mismatch,
  source record count mismatch, and paired-list count mismatch
  rejected.
- `AggregateCountsTest` (3) - candidate route total / workflow
  total / review-halt count match embedded observations.
- `InputIsolationTest` (1) - inputs unchanged after clean pass.
- `ForbiddenLanguageOutputTest` (1) - `end_to_end_note` clean of
  all FORBIDDEN_PHRASES substrings.
- `StaticScanTest` (11) - absence of file-IO, network,
  HTTP-library, subprocess / shell, hashlib, browser-automation,
  PDF-extraction, retrieval-verb, external-integration tokens;
  presence of exactly the two allowed prior-WO public function
  names; absence of every other prior-WO public function name
  (including `run_level0_manual_seed_visible_report` to verify
  that WO-L0-RUN-01 is reached only transitively via
  WO-L0-MATERIAL-01).

## Non-Claim Constraints

WO-L0-E2E-01 does not claim any consolidated observation, attached
source subset, per-prompt summary record, computed total, or
aggregate count is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected. The bounded required
materialization output keys, the bounded required trace-execution
output keys, the per-prompt summary nine-field shape, and the
sixteen `ALLOWED_OUTPUT_KEYS` are bounded by WO-L0-E2E-01 and are
NOT claimed exhaustive.

All DC-020 through DC-065 boundary invariants carry forward.
WO-L0-E2E-01 does not amend or broaden DC-003 through DC-065.
Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031, OQ-035,
OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
RK-039 remains active and is not duplicated.
