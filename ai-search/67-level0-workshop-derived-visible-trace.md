# 67. Level 0B Workshop Derived-Material Visible-Trace Scaffold (WO-L0-WORKSHOP-TRACE-01)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-WORKSHOP-TRACE-01

## Authority

This boundary document records the scaffold surface of
`harness/level0_workshop_derived_trace.py`. It does NOT modify
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

WO-L0-WORKSHOP-TRACE-01 added a scaffold-only combined module that
performs two passes over already-loaded records shaped by the Level
0B workshop seed planning artifact
(`ai-search/00-level0-awesome-copilot-workshop-seed.md`). The module
does not read that planning document at runtime:

1. A derived-material observation pass that constructs exactly one
   metadata-only `derived_material_record` per workshop item record
   (70 in total). Each derived record mirrors `workshop_item_id`,
   `item_kind`, `repo_path_shape`, and `material_role` from the
   input record and stamps fixed boolean / literal fields
   (`candidate_only: True`, `qualified: False`, `corpus_admitted:
   False`, `route_object_created: False`,
   `source_material_extracted: False`,
   `material_observation_basis: "workshop_metadata_only"`). No URL
   is fetched, no file is read, no PDF text is extracted, no hash
   library is used, and no external prompt or source body is
   copied.
2. A visible-trace pass that partitions the derived records into
   candidate route fragments / candidate workflow fragments /
   rejected material by item_kind, attaches matching derived
   material per workshop prompt by the prompt's declared
   `expected_item_kinds_touched`, and emits one
   `per_prompt_trace_summary` entry per prompt (26 in total).

The module performs no file IO, no network call, no URL fetch /
download / crawl / browser automation, no PDF text extraction, no
hash computation, no external process spawning, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools.

WO-L0-WORKSHOP-TRACE-01 does NOT authorize real benchmark execution,
real or mock adapter invocation, source qualification, corpus
admission, extraction, normalization, candidate-fragment promotion
to route, architecture / vendor / library / index family / ANN
backend / reranker / retrieval family / production-system selection,
Source Card or Route Card creation, OQ closure, or duplication of
RK-039. Real-benchmark-ready remains NO.

## Public Surface

```
run_level0_workshop_derived_trace(
    workshop_item_records, workshop_prompt_records, event_log
) -> dict
```

The module imports only:

- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`

The module invokes NO prior-WO public function. The workshop seed
is independent of the seven-source manual-seed chain; WO-L0-RUN-01,
WO-L0-TRACE-01, WO-L0-MATERIAL-01, and WO-L0-E2E-01 are not invoked
here. WO-50 through WO-62 public functions are not invoked here
(verified by static-scan test).

## Inputs

- `workshop_item_records`: already-loaded list of 70 entries.
- `workshop_prompt_records`: already-loaded list of 26 entries.
- `event_log`: an `EventLog` instance from `harness.event_log`.

## Bounded Item Kinds

Eight item kinds, bounded by WO-L0-WORKSHOP-TRACE-01 and NOT
claimed exhaustive:

`skill`, `instruction`, `agent`, `workflow_file`, `hook`, `plugin`,
`cookbook_entry`, `repo_meta_section`.

`prompt` and `vendor_pattern` are explicitly excluded (the workshop
repository has zero `*.prompt.md` files and no vendor-guide shape).

## Item Kind Distribution

Exactly 70 items across the eight kinds:

| item_kind | count |
|-----------|-------|
| `skill` | 16 |
| `instruction` | 12 |
| `agent` | 12 |
| `workflow_file` | 8 |
| `hook` | 5 |
| `plugin` | 4 |
| `cookbook_entry` | 7 |
| `repo_meta_section` | 6 |

Any deviation raises `InvalidItemKindDistribution` (halt-before-raise).

## Bounded Prompt Categories

Nine prompt categories, bounded by WO-L0-WORKSHOP-TRACE-01 and NOT
claimed exhaustive:

`A. clear single-intent`, `B. workflow intent`, `C. skill intent`,
`D. agent/persona confusion`, `E. instruction confusion`,
`F. prompt-search-shaped but workflow-intent`, `G. ambiguous`,
`H. no-route`, `I. near-miss/rejection`.

## Prompt Category Distribution

Exactly 26 prompts across the nine categories:

| category | count |
|----------|-------|
| `A. clear single-intent` | 4 |
| `B. workflow intent` | 4 |
| `C. skill intent` | 3 |
| `D. agent/persona confusion` | 3 |
| `E. instruction confusion` | 3 |
| `F. prompt-search-shaped but workflow-intent` | 2 |
| `G. ambiguous` | 3 |
| `H. no-route` | 2 |
| `I. near-miss/rejection` | 2 |

Any deviation raises `InvalidPromptCategoryDistribution`
(halt-before-raise).

## Item Record Required Fields

Exactly seven required fields, no extras:

`workshop_item_id`, `repo_path_shape`, `item_kind`,
`selection_locator_hint`, `material_role`, `expected_trace_surface`,
`boundary_note`.

`boundary_note` must equal the literal
`not admitted; not qualified; workshop metadata only`.

## Prompt Record Required Fields

Exactly seven required fields, no extras:

`workshop_prompt_id`, `category`, `prompt_text`,
`expected_item_kinds_touched`, `expected_candidate_surface`,
`expected_rejection_surface`, `boundary_note`.

`expected_item_kinds_touched` must be a non-empty list whose entries
are either the literal `none` sentinel or members of the bounded
eight item kinds.

A prompt in category `G. ambiguous` must declare at least two
distinct non-`none` kinds; failing that raises
`AmbiguousPromptMissingMultipleKinds` (halt-before-raise).

`boundary_note` must equal the literal
`not admitted; not qualified; workshop metadata only`.

## Generated Derived Material Record Shape

Exactly eleven fields per record, no extras:

| field | value |
|-------|-------|
| `derived_material_id` | `L0-WS-DER-{NNN}` (1-based 3-digit index) |
| `workshop_item_id` | mirrored from the input record |
| `item_kind` | mirrored from the input record |
| `repo_path_shape` | mirrored from the input record |
| `material_role` | mirrored from the input record |
| `candidate_only` | literal True |
| `qualified` | literal False |
| `corpus_admitted` | literal False |
| `route_object_created` | literal False |
| `source_material_extracted` | literal False |
| `material_observation_basis` | literal `workshop_metadata_only` |

## Candidate / Rejected Partitioning

| item_kind | partition |
|-----------|-----------|
| `skill` | candidate route fragment |
| `instruction` | candidate route fragment |
| `agent` | candidate route fragment |
| `plugin` | candidate route fragment |
| `cookbook_entry` | candidate route fragment |
| `workflow_file` | candidate workflow fragment |
| `hook` | candidate workflow fragment |
| `repo_meta_section` | rejected material only (NEVER candidate) |

Rejected material carries `rejection_reason: "repo_meta_section_near_miss"`.
No rejected material may appear in candidate route fragments or
candidate workflow fragments (verified by per-record-kind test).

## Per-Prompt Trace Summary Shape

Exactly fourteen fields per summary entry:

| field | type | clean-pass value |
|-------|------|------------------|
| `workshop_prompt_id` | str | mirrored from the input record |
| `category` | str | mirrored from the input record |
| `expected_item_kinds_touched` | list | mirrored from the input record (copy) |
| `attached_kinds_observed` | list | bounded kinds actually attached |
| `attached_candidate_route_fragment_ids` | list | derived ids from `CANDIDATE_ROUTE_KINDS` |
| `attached_candidate_workflow_fragment_ids` | list | derived ids from `CANDIDATE_WORKFLOW_KINDS` |
| `attached_rejected_material_ids` | list | derived ids from `REJECTED_ONLY_KINDS` |
| `attached_candidate_route_fragment_count` | int | `len(attached_candidate_route_fragment_ids)` |
| `attached_candidate_workflow_fragment_count` | int | `len(attached_candidate_workflow_fragment_ids)` |
| `attached_rejected_material_count` | int | `len(attached_rejected_material_ids)` |
| `ambiguity_observed` | bool | True iff category is `G. ambiguous` |
| `no_selection_reason` | str | `"prompt_out_of_repo_scope"` for no-route; `"repo_meta_section_near_miss"` for rejection-category prompts with zero candidates; otherwise `"no_forced_selection"` |
| `route_selection_made` | bool | literal False |
| `candidate_only` | bool | literal True |

Each summary entry's key set is verified by per-entry-key test.

## Output Shape

Clean-pass output dict has exactly nineteen keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `workshop_trace_kind` | str | `"level0_workshop_derived_trace"` |
| `item_count` | int | 70 |
| `prompt_count` | int | 26 |
| `derived_material_records` | list of dict | 70 generated derived records |
| `derived_material_count` | int | 70 |
| `candidate_route_fragment_records` | list of dict | derived records partitioned by route kind |
| `candidate_route_fragment_count` | int | length of route partition |
| `candidate_workflow_fragment_records` | list of dict | derived records partitioned by workflow kind |
| `candidate_workflow_fragment_count` | int | length of workflow partition |
| `rejected_material_records` | list of dict | rejected partition with `repo_meta_section_near_miss` reason |
| `rejected_material_count` | int | length of rejected partition |
| `per_prompt_trace_summary` | list of dict | 26 per-prompt entries |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `source_qualification_authorized` | bool | literal False |
| `corpus_admission_authorized` | bool | literal False |
| `workshop_trace_note` | str | constant Level 0B non-claim note |

`candidate_route_fragment_count`,
`candidate_workflow_fragment_count`, and `rejected_material_count`
are non-zero by construction with the bounded item-kind
distribution. The partition sums (16 + 12 + 12 + 4 + 7 = 51 route
candidates; 8 + 5 = 13 workflow candidates; 6 rejected) sum to the
70 derived material records.

## Forbidden Route-Status Fields

The output is checked defensively before return. No record in any
output collection may carry any of:

`official`, `is_route`, `is_official_route`, `selected_as_official`,
`official_route_authorized`, `route_authorized`, `production_route`,
`selected_route`, `executable`, `route_state`, `plane`.

If any such field is present, the module halts and raises
`ForbiddenLanguageInLevel0WorkshopDerivedTrace`.

## Static Scan

The module file contains none of:

- `open(`, `pathlib`
- `urllib`, `http.client`, `socket`
- `import requests`, `from requests`, `requests.`
- `subprocess`, `os.system`, `shutil`
- `hashlib`, `.hexdigest`, `.sha256`
- `def query`, `def search`, `def retrieve`, `def rank`
- `score`, `scoring`
- `copilot`, `waza`, `vscode`, `openai`, `anthropic`, `llm`

The module file contains no name of any prior-WO public function
(WO-50 through WO-62 plus the four manual-seed L0 modules).

## Validation Order

1. Forbidden-language scan over `workshop_item_records`
   (halts before any per-record traversal if violated).
2. Forbidden-language scan over `workshop_prompt_records`.
3. Validate item records: list type, count, dict per entry,
   required fields, no unknown fields, boundary-note literal,
   bounded `item_kind`, unique `workshop_item_id`, then per-kind
   distribution.
4. Validate prompt records: list type, count, dict per entry,
   required fields, no unknown fields, boundary-note literal,
   bounded `category`, list-shape `expected_item_kinds_touched`
   that is non-empty and contains only bounded kinds (or the
   literal `none`), ambiguous-category multi-kind requirement,
   unique `workshop_prompt_id`, then per-category distribution.
5. Derive one metadata-only material record per item.
6. Partition derived records into route candidates / workflow
   candidates / rejected by item_kind.
7. Build the per-prompt trace summary.
8. Defensive route-status-field check on every output collection.
9. Forbidden-language scan on the assembled result dict.

Any failure halts and raises a named exception before the next
phase begins.

## What This Scaffold Does NOT Do

- Does NOT read any planning document at runtime.
- Does NOT fetch any URL, download any content, or crawl any source.
- Does NOT read any local file.
- Does NOT extract PDF text.
- Does NOT compute any hash via `hashlib` or any other library.
- Does NOT spawn external processes or shells.
- Does NOT integrate with editor extensions, chat plugins,
  third-party model APIs, or external collaborator tools.
- Does NOT invoke any prior-WO public function (WO-50 through
  WO-62, WO-L0-RUN-01, WO-L0-TRACE-01, WO-L0-MATERIAL-01,
  WO-L0-E2E-01).
- Does NOT emit any `qualified: True`, `corpus_admitted: True`,
  `route_object_created: True`, `source_material_extracted: True`,
  or any route-status field on any record (verified by
  per-record-field tests and a defensive output check).
- Does NOT mutate inputs (verified by regression test).
- Does NOT flip any of the four standard authorization / readiness
  / selection booleans, nor the two workshop booleans
  `source_qualification_authorized` and `corpus_admission_authorized`.
- Does NOT promote any candidate fragment to a route.
- Does NOT compute any similarity / distance / ranking / metric.
- Does NOT include `prompt` or `vendor_pattern` in the bounded
  item-kind set.

## Test Surface

`harness/tests/test_level0_workshop_derived_trace.py` contains 86
tests across the following test classes:

- `CleanPassTest` (18) - output shape, fixed key set, count fields,
  literal-False booleans, started / completed events, no halt.
- `DerivedMaterialShapeTest` (9) - per-record required fields,
  literal-True / literal-False fixed values,
  `material_observation_basis` literal, derived-id prefix and
  uniqueness, no route-status field.
- `PartitionTest` (10) - per-kind partition mapping, rejection
  reason literal, route / workflow / rejected counts match the
  bounded distribution, no `repo_meta_section` in candidate
  partitions, no route-status field on rejected records.
- `PerPromptTraceSummaryTest` (12) - one summary entry per prompt,
  per-entry required fields, no-route prompts produce zero
  candidates with `prompt_out_of_repo_scope`, ambiguous prompts
  surface `ambiguity_observed: True`, rejection-category prompts
  produce zero candidate route / workflow fragments and the
  rejection reason, every entry has `route_selection_made: False`
  and `candidate_only: True`, clear single-intent prompts attach
  at least one candidate, workflow-intent prompts attach at least
  one workflow candidate, attached kinds are a subset of expected
  kinds, no summary entry carries any route-status field.
- `DistributionTest` (4) - observed item-kind distribution matches
  expected; observed prompt-category distribution matches expected;
  item-kind distribution mismatch halts; prompt-category
  distribution mismatch halts.
- `MalformedInputHaltTest` (15) - non-list inputs halt; wrong
  counts halt; non-dict entries halt; missing / unknown fields
  halt for both item and prompt records; invalid boundary-note
  literal halts on both sides; non-list / empty
  `expected_item_kinds_touched` halts; ambiguous prompt with a
  single kind halts.
- `DuplicateAndUnknownHaltTest` (5) - duplicate `workshop_item_id`,
  duplicate `workshop_prompt_id`, unknown `item_kind`, unknown
  prompt `category`, unknown `expected_item_kinds_touched` entry.
- `ForbiddenLanguageHaltTest` (2) - forbidden phrase in item
  record halts; forbidden claim phrase in prompt record halts.
- `InputIsolationTest` (1) - inputs unchanged after clean pass.
- `StaticScanTest` (10) - absence of file-IO, network,
  HTTP-library, subprocess / shell, hashlib, retrieval-verb,
  scoring, external-integration tokens; absence of any prior-WO
  public function name; module file is ASCII.

## Non-Claim Constraints

WO-L0-WORKSHOP-TRACE-01 does not claim any derived material record,
candidate route fragment, candidate workflow fragment, rejected
material record, attached fragment list, ambiguity observation,
no-selection reason literal, or computed count is sufficient,
necessary, superior, best, complete, production-ready, recommended,
or selected. The bounded eight item kinds, the bounded nine prompt
categories, the bounded per-kind / per-category distributions, the
bounded boundary-note literal, the bounded required-field sets, the
bounded eleven derived-material fields, the bounded thirteen
candidate / rejected partition rules, the synthetic
`L0-WS-DER-` identifier format, the literal
`workshop_metadata_only` material-observation-basis marker, and the
nineteen `ALLOWED_OUTPUT_KEYS` are bounded by
WO-L0-WORKSHOP-TRACE-01 and are NOT claimed exhaustive.

All DC-020 through DC-068 boundary invariants carry forward.
WO-L0-WORKSHOP-TRACE-01 does not amend or broaden DC-003 through
DC-068. Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031,
OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076
remain OPEN. RK-039 remains active and is not duplicated.
