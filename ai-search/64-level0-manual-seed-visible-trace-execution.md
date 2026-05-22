# 64. Level 0B Manual Seed Visible Trace Execution Scaffold (WO-L0-TRACE-01)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-TRACE-01

## Authority

This boundary document records the scaffold surface of
`harness/level0_manual_seed_trace_execution.py`. It does NOT modify
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

WO-L0-TRACE-01 added a scaffold-only Level 0B trace execution
module that:

1. Validates the manual seed item and prompt records by delegating
   to `run_level0_manual_seed_visible_report` (WO-L0-RUN-01). If
   that delegate raises, the execution short-circuits before any
   WO-59 visible report is produced.
2. For each `trace_case_record`, emits one WO-59 visible-report
   observation by delegating to
   `run_scaffold_source_intake_visible_report` (WO-59).

WO-L0-TRACE-01 does NOT authorize real benchmark execution, real or
mock adapter invocation, network calls, URL fetch / download /
crawl / browser automation, local file read or write, PDF text
extraction, source qualification, corpus admission, extraction or
normalization beyond what WO-59 already produces, candidate-fragment
derivation beyond what WO-59 already produces, route or workflow
promotion, architecture / vendor / library / index family / ANN
backend / reranker / retrieval family / production-system selection,
IDE / chat / collaborator / Copilot / Waza / VS Code / LLM
integration, Source Card or Route Card creation, OQ closure, or
duplication of RK-039. Real-benchmark-ready remains NO.

## Public Surface

```
run_level0_manual_seed_trace_execution(
    item_records, prompt_records, trace_case_records, event_log
) -> dict
```

The module imports only:

- `harness.level0_manual_seed_visible_report.run_level0_manual_seed_visible_report`
- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`
- `harness.scaffold_source_intake_visible_report.run_scaffold_source_intake_visible_report`

The module invokes only the two prior-WO public functions named
above. It does NOT invoke WO-50, WO-51, WO-52, WO-53, WO-54, WO-55,
WO-56, WO-57, WO-58, WO-60, WO-61, or WO-62 public functions
(verified by static-scan test).

## Inputs

- `item_records`: already-loaded list. Validated by
  `run_level0_manual_seed_visible_report`.
- `prompt_records`: already-loaded list. Validated by
  `run_level0_manual_seed_visible_report`.
- `trace_case_records`: already-loaded list of exactly
  `EXPECTED_TRACE_CASE_COUNT = 23` dicts. Each dict carries the ten
  required fields in `REQUIRED_TRACE_CASE_FIELDS`:
  `case_id`, `prompt_id`, `expected_category`, `input_prompt`,
  `source_reference_records`, `source_records`,
  `expected_source_touch`, `expected_candidate_shape`,
  `expected_rejection_targets`, `boundary_notes`.
- `event_log`: an `EventLog` instance from `harness.event_log`.

## Bounded Surfaces

- `EXPECTED_TRACE_CASE_COUNT = 23`.
- `REQUIRED_TRACE_CASE_FIELDS` (10): exact field names listed above.
- `TRACE_CASE_BOUNDARY_NOTE` literal:
  `not admitted; not qualified; manual-seed trace only`.
- `ALLOWED_OUTPUT_KEYS` (13): the keys listed in section "Output
  Shape" below.

All four surfaces are bounded by WO-L0-TRACE-01 and are NOT claimed
exhaustive.

## Validation Order

1. Delegate manual seed shape validation to
   `run_level0_manual_seed_visible_report`. If that delegate
   raises, control never reaches steps 2 onward; no trace-case
   validation, no WO-59 invocation, and no result is produced
   (short-circuit).
2. `trace_case_records` is a list (else `NonListTraceCaseRecords`).
3. `len(trace_case_records) == 23` (else `InvalidTraceCaseCount`).
4. Per case:
   - is a dict (else `NonObjectTraceCaseRecord`);
   - carries every field in `REQUIRED_TRACE_CASE_FIELDS` (else
     `MissingTraceCaseField`);
   - carries no field outside `REQUIRED_TRACE_CASE_FIELDS` (else
     `UnknownTraceCaseField`);
   - `case_id` is a non-empty string (else `InvalidCaseIdValue`);
   - `case_id` is unique across cases (else `DuplicateCaseId`);
   - `prompt_id` is present in `prompt_records` (else
     `UnknownPromptIdReference`);
   - `prompt_id` is unique across cases (else
     `DuplicatePromptIdReference`);
   - `expected_category` equals the referenced prompt record's
     `category` (else `TraceCaseCategoryMismatch`);
   - `input_prompt` equals the referenced prompt record's
     `prompt_text` (else `TraceCaseInputPromptMismatch`);
   - `boundary_notes` equals the literal (else
     `InvalidTraceCaseBoundaryNoteLiteral`);
   - `source_reference_records` is a list (else
     `NonListCaseSourceReferenceRecords`);
   - `source_records` is a list (else `NonListCaseSourceRecords`).
5. Coverage:
   - observed `prompt_id` set equals `set(prompt_records prompt_id)`
     (else `MissingTraceCasePromptIdCoverage`; defensive: by
     pigeonhole with steps above this cannot be reached when
     trace_case_count equals prompt_records length and all
     references are known and distinct);
   - every Level 0B category has at least one trace case (else
     `MissingTraceCaseCategoryCoverage`; defensive).
6. Input forbidden-language scan over `trace_case_records` against
   `FORBIDDEN_PHRASES` and `FORBIDDEN_CLAIM_PHRASES` (else
   `ForbiddenLanguageInLevel0ManualSeedTraceExecution`).
7. For each trace case, invoke
   `run_scaffold_source_intake_visible_report(case["input_prompt"],
   case["source_reference_records"], case["source_records"],
   event_log)`. Collect the returned dict; tally
   `review_halt_required_count` from `report["review_halt_required"]`.
8. Build result dict.
9. Output forbidden-language scan (else
   `ForbiddenLanguageInLevel0ManualSeedTraceExecution`).

Every raise is preceded by an `event_log.halt(reason=..., ...)`
recording (halt-before-raise per Constraints v1 D3).

## Output Shape

Clean-pass output dict has exactly thirteen keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `execution_kind` | str | `"level0_manual_seed_trace_execution"` |
| `manual_seed_shape_observation` | dict | the 15-key WO-L0-RUN-01 clean-pass dict |
| `trace_case_count` | int | 23 |
| `prompt_ids_executed` | list of str | sorted 23 distinct ids |
| `category_counts` | dict | per-category integer counts summing to 23 |
| `visible_reports` | list of dict | 23 WO-59 visible-report dicts |
| `visible_report_count` | int | 23 |
| `review_halt_required_count` | int | tally of `review_halt_required: True` entries |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `execution_note` | str | constant Level 0B non-claim note |

The four standard authorization / readiness / selection booleans
remain literal False on every emitted path regardless of how many
embedded WO-59 reports carry `review_halt_required: True`.
`review_halt_required_count` is observational metadata for Codex
review only; it does NOT cause this module to raise and does NOT
flip any authorization boolean.

## What This Scaffold Does NOT Do

- Does NOT read any planning document at runtime.
- Does NOT perform network calls of any kind.
- Does NOT fetch, download, crawl, or browse any URL.
- Does NOT extract PDF text.
- Does NOT compute hashes.
- Does NOT spawn external processes or external shells.
- Does NOT integrate with editor extensions, chat plugins,
  third-party model APIs, or external collaborator tools.
- Does NOT invoke `run_scaffold_route_query_probe` (WO-50),
  `run_scaffold_route_query_ambiguity_probe` (WO-51),
  `run_scaffold_conflicting_evidence_guard` (WO-52, WO-53),
  `run_scaffold_source_intake_trace` (WO-54),
  `run_scaffold_source_intake_register` (WO-55),
  `run_scaffold_source_trace_admission_bridge` (WO-56),
  `run_scaffold_source_intake_smoke_package` (WO-57),
  `run_scaffold_route_invariant_diagnostic_reporter` (WO-58),
  `run_scaffold_external_source_acquisition_boundary` (WO-60),
  `run_scaffold_url_acquisition_executor` (WO-61), or
  `run_scaffold_url_acquisition_register_readiness` (WO-62)
  (verified by static-scan test).
- Does NOT qualify any source.
- Does NOT admit any source to corpus.
- Does NOT extract, normalize, or derive candidate fragments
  beyond what WO-59 already produces.
- Does NOT decide architecture, vendor, library, index family,
  ANN backend, reranker, retrieval family, or production system.
- Does NOT mutate inputs (verified by regression test).
- Does NOT flip any of the four standard authorization / readiness
  / selection booleans.

## Test Surface

`harness/tests/test_level0_manual_seed_trace_execution.py` contains
64 tests across the following test classes:

- `CleanPassTest` (18) - output shape, key set, count fields,
  literal-False booleans, embedded manual-seed observation,
  embedded WO-59 report shape, event emission, no halt.
- `ShortCircuitOnSeedShapeFailureTest` (2) - seed-shape failure
  short-circuits before any WO-59 invocation; seed-shape failure
  short-circuits before any trace-case validation.
- `DelegateOrderTest` (1) - seed validator invoked exactly once
  before any WO-59 invocation; WO-59 invoked exactly 23 times.
- `TraceCaseTypeValidationTest` (3) - non-list, dict, None
  rejection.
- `TraceCaseCountValidationTest` (3) - too few, too many, empty.
- `TraceCaseFieldValidationTest` (12) - non-dict case; each of the
  ten required fields tested individually; parameterized full-set
  test.
- `UnknownTraceCaseFieldTest` (1) - extra field rejection.
- `CaseIdValidationTest` (3) - empty, non-string, duplicate
  `case_id`.
- `PromptIdReferenceTest` (2) - unknown and duplicate `prompt_id`
  reference.
- `CategoryMismatchTest` (1) - `expected_category` does not match
  referenced prompt record.
- `InputPromptMismatchTest` (1) - `input_prompt` does not match
  referenced `prompt_text`.
- `BoundaryNoteValidationTest` (2) - wrong literal; empty literal.
- `SourceListTypeTest` (2) - non-list `source_reference_records`;
  non-list `source_records`.
- `ForbiddenLanguageTest` (2) - `FORBIDDEN_PHRASES` phrase in case
  field; `FORBIDDEN_CLAIM_PHRASES` phrase in case field.
- `InputIsolationTest` (1) - inputs unchanged after clean pass.
- `StaticScanTest` (10) - absence of file-IO, network, HTTP-library,
  subprocess / shell, hashlib, browser-automation, retrieval-verb,
  and external-integration tokens; presence of exactly the two
  allowed prior-WO public function names; absence of all other
  WO-50 through WO-62 public function names.

## Non-Claim Constraints

WO-L0-TRACE-01 does not claim any trace case, embedded visible
report, observed prompt identifier, observed category count,
computed review-halt count, output key, halt reason, or event name
is sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded `EXPECTED_TRACE_CASE_COUNT`,
the bounded `REQUIRED_TRACE_CASE_FIELDS`, the
`TRACE_CASE_BOUNDARY_NOTE` literal, and the thirteen
`ALLOWED_OUTPUT_KEYS` are bounded by WO-L0-TRACE-01 and are NOT
claimed exhaustive.

`review_halt_required_count` is observational metadata only. It
does NOT authorize benchmark execution. It does NOT mean
source-qualified. It does NOT mean corpus-admitted. It does NOT
mean route-selected.

All DC-020 through DC-063 boundary invariants carry forward.
WO-L0-TRACE-01 does not amend or broaden DC-003 through DC-063.
Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031, OQ-035,
OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
RK-039 remains active and is not duplicated.
