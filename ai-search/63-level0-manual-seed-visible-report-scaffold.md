# 63. Level 0B Manual Seed Visible Report Scaffold (WO-L0-RUN-01)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-RUN-01

## Authority

This boundary document records the scaffold surface of
`harness/level0_manual_seed_visible_report.py`. It does NOT modify
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

WO-L0-RUN-01 added a scaffold-only Level 0B runner that accepts
already-loaded manual seed item records and synthetic prompt records,
validates their shape against the WO-L0-ITEMS-01 planning artifacts
(`ai-search/00-level0-item-selection.md` and
`ai-search/00-level0-prompt-set.md`), and emits a fixed-shape Level
0B visible test report dict.

WO-L0-RUN-01 does NOT authorize real benchmark execution, real or
mock adapter invocation, network calls, URL fetch / download / crawl
/ browser automation, local file read or write, PDF text extraction,
source qualification, corpus admission, extraction, normalization,
candidate-fragment derivation, route or workflow promotion,
architecture / vendor / library / index family / ANN backend /
reranker / retrieval family / production-system selection, IDE /
chat / collaborator / Copilot / Waza / VS Code / LLM integration,
Source Card or Route Card creation, OQ closure, or duplication of
RK-039. Real-benchmark-ready remains NO.

## Public Surface

```
run_level0_manual_seed_visible_report(
    item_records, prompt_records, event_log
) -> dict
```

The module imports only
`harness.payload_loader.FORBIDDEN_CLAIM_PHRASES` and
`harness.review_package.FORBIDDEN_PHRASES`. It does NOT invoke any
prior-WO public function (verified by static-scan test).

## Inputs

- `item_records`: already-loaded list. Required count is
  `EXPECTED_ITEM_COUNT = 65`. Each record is a dict carrying the
  seven required fields in `REQUIRED_ITEM_FIELDS`:
  `item_id`, `source_id`, `item_kind`, `item_title_or_anchor`,
  `item_locator`, `intended_test_role`, `boundary_notes`.
- `prompt_records`: already-loaded list. Required count is
  `EXPECTED_PROMPT_COUNT = 23`. Each record is a dict carrying the
  seven required fields in `REQUIRED_PROMPT_FIELDS`:
  `prompt_id`, `category`, `prompt_text`, `expected_behavior_summary`,
  `expected_source_touch`, `expected_candidate_shape`,
  `expected_rejection_targets`.
- `event_log`: an `EventLog` instance from `harness.event_log`.

## Bounded Admission Surfaces

- `EXPECTED_SOURCE_IDS` (7): `L0-SRC-001`, `L0-SRC-002`, `L0-SRC-003`,
  `L0-SRC-004`, `L0-SRC-005`, `L0-SRC-006`, `L0-SRC-007`.
- `EXPECTED_PROMPT_CATEGORIES` (9):
  `A. clear single-intent`,
  `B. multi-intent`,
  `C. ambiguous`,
  `D. prompt-search-shaped that should become workflow / route intent`,
  `E. no-route`,
  `F. refusal / no-selection`,
  `G. multi-source-touching`,
  `H. near-miss involving L0-SRC-007`,
  `I. workflow involving L0-SRC-006`.
- `ITEM_BOUNDARY_NOTE` literal:
  `not admitted; not qualified; link-level/manual-seed only`.

All three sets are bounded by WO-L0-RUN-01 and are NOT claimed
exhaustive.

## Validation Order

1. `item_records` is a list (else `NonListItemRecords`).
2. `prompt_records` is a list (else `NonListPromptRecords`).
3. `len(item_records) == EXPECTED_ITEM_COUNT` (else
   `InvalidItemRecordCount`).
4. `len(prompt_records) == EXPECTED_PROMPT_COUNT` (else
   `InvalidPromptRecordCount`).
5. Per item: is a dict (else `NonObjectItemRecord`); carries every
   field in `REQUIRED_ITEM_FIELDS` (else `MissingItemRecordField`);
   carries no field outside `REQUIRED_ITEM_FIELDS` (else
   `UnknownItemRecordField`); `boundary_notes` equals the literal (else
   `InvalidItemBoundaryNoteLiteral`); `source_id` is in
   `EXPECTED_SOURCE_IDS` (else `UnknownSourceId`).
6. Per prompt: is a dict (else `NonObjectPromptRecord`); carries
   every field in `REQUIRED_PROMPT_FIELDS` (else
   `MissingPromptRecordField`); carries no field outside
   `REQUIRED_PROMPT_FIELDS` (else `UnknownPromptRecordField`);
   `category` is in
   `EXPECTED_PROMPT_CATEGORIES` (else `UnknownPromptCategory`).
7. Source-id coverage equals `set(EXPECTED_SOURCE_IDS)` (else
   `MissingSourceIdCoverage`).
8. Category coverage equals `set(EXPECTED_PROMPT_CATEGORIES)` (else
   `MissingPromptCategoryCoverage`).
9. Forbidden-language scan over inputs (else
   `ForbiddenLanguageInLevel0ManualSeedReport`).
10. Build result dict.
11. Forbidden-language scan over the result dict (else
    `ForbiddenLanguageInLevel0ManualSeedReport`).

Every raise is preceded by a `event_log.halt(reason=..., ...)`
recording (halt-before-raise per Constraints v1 D3).

## Output Shape

Clean-pass output dict has exactly fifteen keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `report_kind` | str | `"level0_manual_seed_visible_report"` |
| `item_count` | int | 65 |
| `prompt_count` | int | 23 |
| `source_ids_observed` | list of str | sorted 7 ids |
| `prompt_categories_observed` | list of str | sorted 9 categories |
| `expected_workflow_prompt_count` | int | 2 |
| `expected_near_miss_prompt_count` | int | 2 |
| `expected_no_route_prompt_count` | int | 2 |
| `expected_ambiguous_prompt_count` | int | 3 |
| `manual_seed_ready_for_visible_trace` | bool | True |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `report_note` | str | constant Level 0B non-claim note |

`manual_seed_ready_for_visible_trace` is a planning-readiness flag.
It is True only when shape validation passes. It does NOT mean
benchmark-ready, source-qualified, corpus-admitted, or
route-selected.

## What This Scaffold Does NOT Do

- Does NOT read `00-level0-item-selection.md`,
  `00-level0-prompt-set.md`, `00-level0-source-candidate-inventory.md`,
  or any other file. The module performs no file IO.
- Does NOT perform network calls of any kind.
- Does NOT fetch, download, crawl, or browse any URL.
- Does NOT extract PDF text.
- Does NOT compute hashes.
- Does NOT invoke `run_scaffold_source_intake_trace` (WO-54),
  `run_scaffold_source_intake_register` (WO-55),
  `run_scaffold_source_trace_admission_bridge` (WO-56),
  `run_scaffold_source_intake_smoke_package` (WO-57),
  `run_scaffold_route_invariant_diagnostic_reporter` (WO-58),
  `run_scaffold_source_intake_visible_report` (WO-59),
  `run_scaffold_external_source_acquisition_boundary` (WO-60),
  `run_scaffold_url_acquisition_executor` (WO-61),
  `run_scaffold_url_acquisition_register_readiness` (WO-62), or any
  other prior-WO public function (verified by static-scan test).
- Does NOT integrate with editor extensions, chat plugins,
  third-party model APIs, or external collaborator tools.
- Does NOT qualify any source.
- Does NOT admit any source to corpus.
- Does NOT extract, normalize, or derive candidate fragments.
- Does NOT decide architecture, vendor, library, index family,
  ANN backend, reranker, retrieval family, or production system.
- Does NOT mutate inputs (verified by regression test).
- Does NOT flip any of the four standard authorization / readiness
  / selection booleans.
- Does NOT accept route-status, qualification, or admission markers
  as extra item/prompt fields; the input record surfaces are exact
  field sets.

## Test Surface

`harness/tests/test_level0_manual_seed_visible_report.py` contains
71 tests across the following test classes:

- `CleanPassTest` (20 tests) - clean-pass output shape, key set,
  literal-False booleans, planning-readiness flag True, event
  emission, no halt.
- `InputTypeValidationTest` (4 tests) - non-list input rejection.
- `RecordCountValidationTest` (6 tests) - too few / too many /
  empty inputs.
- `ItemFieldValidationTest` (11 tests) - non-dict item; each of the
  seven required item fields tested individually; parameterized
  full-set test; unknown item field rejection; admission-shaped
  item field rejection.
- `PromptFieldValidationTest` (11 tests) - non-dict prompt; each of
  the seven required prompt fields tested individually;
  parameterized full-set test; unknown prompt field rejection;
  qualification-shaped prompt field rejection.
- `BoundaryNoteValidationTest` (2 tests) - wrong literal; empty
  literal.
- `SourceIdValidationTest` (1 test) - unknown source identifier
  rejection.
- `PromptCategoryValidationTest` (1 test) - unknown category
  rejection.
- `CoverageValidationTest` (2 tests) - missing source coverage;
  missing category coverage.
- `ForbiddenLanguageTest` (4 tests) - forbidden phrase in item
  field; forbidden phrase in prompt field; forbidden phrase
  `winning` in input; forbidden claim phrase
  `validation evidence` in input.
- `InputIsolationTest` (1 test) - input records unchanged after
  clean pass.
- `StaticScanTest` (8 tests) - module source absence of file-IO
  tokens (`open(`, `pathlib`); network tokens (`urllib`,
  `http.client`, `socket`); HTTP library tokens (`import requests`,
  `from requests`, `requests.`); subprocess / shell tokens
  (`subprocess`, `os.system`, `shutil`); hashlib tokens
  (`hashlib`, `.hexdigest`, `.sha256`); retrieval verb tokens
  (`def query`, `def search`, `def retrieve`, `def rank`);
  external integration tokens (`copilot`, `waza`, `vscode`,
  `vs_code`, `openai`, `anthropic`, `claude_api`, `llm`);
  prior-WO public function invocation tokens (WO-50 through
  WO-62).

## Non-Claim Constraints

WO-L0-RUN-01 does not claim any record, count, observed source
identifier, observed prompt category, computed expected-count,
output key, halt reason, or event name is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected. The bounded `EXPECTED_SOURCE_IDS` set, the bounded
`EXPECTED_PROMPT_CATEGORIES` set, the `REQUIRED_ITEM_FIELDS` set,
the `REQUIRED_PROMPT_FIELDS` set, the `ITEM_BOUNDARY_NOTE`
literal, and the fifteen `ALLOWED_OUTPUT_KEYS` are bounded by
WO-L0-RUN-01 and are NOT claimed exhaustive.

`manual_seed_ready_for_visible_trace: True` is a planning-readiness
observation only. It does NOT authorize benchmark execution. It does
NOT mean source-qualified. It does NOT mean corpus-admitted. It does
NOT mean route-selected.

All DC-020 through DC-062 boundary invariants carry forward.
WO-L0-RUN-01 does not amend or broaden DC-003 through DC-062.
Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031, OQ-035,
OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
RK-039 remains active and is not duplicated.
