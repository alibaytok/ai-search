# 65. Level 0B Manual Seed Source Record Materialization Scaffold (WO-L0-MATERIAL-01)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-MATERIAL-01

## Authority

This boundary document records the scaffold surface of
`harness/level0_manual_seed_materialization.py`. It does NOT modify
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

WO-L0-MATERIAL-01 added a scaffold-only module that turns
already-loaded Level 0B manual seed item records into already-loaded
WO-59-compatible `source_reference_records` (WO-55-shaped) and
`source_records` (WO-56-shaped). The generated records derive only
from item metadata already present in the input. The module performs
no file IO, no network call, no URL fetch / download / crawl /
browser automation, no PDF text extraction, no hash computation, no
external process spawning, and no integration with editor extensions,
chat plugins, third-party model APIs, or external collaborator tools.

WO-L0-MATERIAL-01 does NOT authorize real benchmark execution, real
or mock adapter invocation, source qualification, corpus admission,
extraction, normalization, candidate-fragment derivation, route or
workflow promotion, architecture / vendor / library / index family /
ANN backend / reranker / retrieval family / production-system
selection, Source Card or Route Card creation, OQ closure, or
duplication of RK-039. Real-benchmark-ready remains NO.

## Contract Reconciliation - Deliberate Deviation From Packet Text

The WO-L0-MATERIAL-01 packet text states the generated
`source_record` should carry `qualified: literal False`. The
downstream WO-56 bridge contract rejects ANY presence of a
`qualified` field in source records (regardless of value), by
design - WO-56's `_reject_source_record_forbidden_fields` raises
`SourceRecordDeclaresQualification` when `qualified` appears.

To keep the generated records WO-59-compatible (since WO-59 invokes
WO-56 internally via WO-57), this module deliberately OMITS the
`qualified` field from generated source records. The intended
unqualified semantic is preserved by ABSENCE of the field; the
WO-56 contract treats this as the correct unqualified state.

This deviation is documented here, in the module docstring, in
DC-065, and in the ledger entry. Canonical authority (the WO-56
contract as encoded in `harness/scaffold_source_trace_admission_bridge.py`)
takes precedence over the packet's design suggestion when they
conflict.

## Public Surface

```
run_level0_manual_seed_materialization(
    item_records, prompt_records, event_log
) -> dict
```

The module imports only:

- `harness.level0_manual_seed_visible_report.run_level0_manual_seed_visible_report`
- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`

The module invokes only the WO-L0-RUN-01 public function for shape
delegation. It does NOT invoke the WO-59 visible-report public
function, the WO-L0-TRACE-01 trace-execution public function, or
any other WO-50 through WO-62 public function (verified by
static-scan test).

## Inputs

- `item_records`: already-loaded list. Validated by the
  WO-L0-RUN-01 delegate (65 items; seven required fields; bounded
  source-id set; bounded boundary-note literal).
- `prompt_records`: already-loaded list. Validated by the
  WO-L0-RUN-01 delegate (23 prompts; nine required fields; bounded
  category set).
- `event_log`: an `EventLog` instance from `harness.event_log`.

## Item Kind to Declared Kind Mapping

`ITEM_KIND_TO_DECLARED_KIND` is bounded by WO-L0-MATERIAL-01 and is
NOT claimed exhaustive:

| item_kind | declared_kind |
|-----------|---------------|
| `prompt` | `prompt_collection` |
| `skill` | `skill_collection` |
| `agent` | `agent_description_collection` |
| `instruction` | `tool_description_collection` |
| `workflow_file` | `document_collection` |
| `vendor_prompt_pattern` | `prompt_collection` |
| `encyclopedic_section` | `document_collection` |

Any `item_kind` outside this mapping raises `UnknownItemKind`
(halt-before-raise).

## Generated Source Reference Record Shape (WO-55-compatible)

Exactly six required fields, no extras:

| field | derivation |
|-------|------------|
| `source_id` | `L0-MAT-SRC-{NNN}` (1-based 3-digit index) |
| `origin` | `manual-seed:{item_id}:{item_locator}` (inert; no fetched content) |
| `declared_kind` | mapped from `item_kind` |
| `hash` | `L0-MAT-HASH-{NNN}-{item_id}` (synthetic; no hash library used) |
| `byte_length` | `len(item_id) + len(item_locator) + len(item_title_or_anchor)` (metadata-string length sum; NOT fetched content length) |
| `observed_at` | literal `level0-manual-seed` |

## Generated Source Record Shape (WO-54 / WO-56 / WO-59-compatible)

Exactly four required fields, no extras (the `qualified` field is
intentionally OMITTED per the contract reconciliation note above):

| field | value |
|-------|-------|
| `source_id` | same as the paired source_reference_record `source_id` |
| `source_kind` | same as the paired source_reference_record `declared_kind` |
| `source_origin` | literal `external` |
| `source_register_ref` | same as the paired source_reference_record `source_id` |

## Validation Order

1. Delegate manual seed shape validation to
   `run_level0_manual_seed_visible_report`. If the delegate raises,
   the materialization short-circuits before any source record is
   constructed.
2. Per item:
   - compute `L0-MAT-SRC-{NNN}` based on 1-based index;
   - check uniqueness (defensive; can only fire under programmer
     error since indices are unique by construction);
   - if uniqueness fails, halt and raise
     `DuplicateMaterializedSourceId`;
   - check `item_kind` against `ITEM_KIND_TO_DECLARED_KIND`;
   - if unknown, halt and raise `UnknownItemKind`;
   - build the source_reference_record and source_record pair from
     metadata only.
3. Forbidden-language scan on the assembled result dict (else
   `ForbiddenLanguageInLevel0ManualSeedMaterialization`).

## Output Shape

Clean-pass output dict has exactly fifteen keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `materialization_kind` | str | `"level0_manual_seed_materialization"` |
| `manual_seed_shape_observation` | dict | the 15-key WO-L0-RUN-01 clean-pass dict |
| `source_reference_records` | list of dict | 65 generated 6-field references |
| `source_records` | list of dict | 65 generated 4-field records |
| `source_reference_count` | int | 65 |
| `source_record_count` | int | 65 |
| `item_ids_materialized` | list of str | sorted 65 unique item ids |
| `source_ids_materialized` | list of str | sorted 65 unique generated source ids |
| `candidate_route_fragment_count` | int | 0 |
| `candidate_workflow_fragment_count` | int | 0 |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `materialization_note` | str | constant Level 0B non-claim note |

`candidate_route_fragment_count` and
`candidate_workflow_fragment_count` are literal 0 because the
generated source records carry NO `extracted_material`, NO
`normalized_material`, and NO `candidate_fragments` (those fields
would be rejected by WO-56). WO-59 invoked at downstream-test time
will accordingly produce zero candidate fragments from these
records. The packet permits this outcome.

## What This Scaffold Does NOT Do

- Does NOT read any planning document at runtime.
- Does NOT fetch any URL, download any content, or crawl any source.
- Does NOT read any local file.
- Does NOT extract PDF text.
- Does NOT compute any hash via `hashlib` or any other library.
- Does NOT spawn external processes or shells.
- Does NOT integrate with editor extensions, chat plugins,
  third-party model APIs, or external collaborator tools.
- Does NOT invoke the WO-59 visible-report public function.
- Does NOT invoke the WO-L0-TRACE-01 trace-execution public function.
- Does NOT invoke WO-50, WO-51, WO-52, WO-53, WO-54, WO-55, WO-56,
  WO-57, WO-58, WO-60, WO-61, or WO-62 public functions
  (verified by static-scan test).
- Does NOT emit any `qualified`, `qualification_ref`,
  `extracted_material`, `normalized_material`, `candidate_fragments`,
  `candidate_route_fragments`, `candidate_workflow_fragments`,
  `official`, `is_route`, `is_official_route`, `selected_as_official`,
  `official_route_authorized`, `route_authorized`,
  `production_route`, `selected_route`, `executable`, `route_state`,
  or `plane` field in generated source records (verified by
  per-record-field tests).
- Does NOT mutate inputs (verified by regression test).
- Does NOT flip any of the four standard authorization / readiness
  / selection booleans.

## Test Surface

`harness/tests/test_level0_manual_seed_materialization.py` contains
53 tests across the following test classes:

- `CleanPassTest` (18) - output shape, fixed key set, count fields,
  embedded manual-seed observation, literal-False booleans, started
  / completed events, no halt.
- `GeneratedSourceReferenceShapeTest` (7) - per-reference six
  required fields; `source_id` prefix; `declared_kind` in WO-55
  allowed set; `hash` length at least 12; `byte_length` non-negative
  int rejecting bools; `observed_at` literal; `origin` prefix.
- `GeneratedSourceRecordShapeTest` (9) - per-record four required
  fields; `source_origin` literal `external`; `source_kind` matches
  reference `declared_kind`; `source_id` matches reference;
  `source_register_ref` matches `source_id`; no `qualified` field;
  no `qualification_ref`; no route-status field; no derived-material
  field.
- `ItemKindMappingTest` (2) - each of the seven known item kinds
  maps correctly; unknown kind rejected.
- `SeedShapeDelegationTest` (2) - seed-shape failure short-circuits
  before materialization; seed validator invoked exactly once
  before any materialization observation event.
- `InputIsolationTest` (1) - inputs unchanged after clean pass.
- `Wo59CompatibilityTest` (1) - end-to-end pass: materialized
  records run cleanly through
  `run_scaffold_source_intake_visible_report` (WO-59) at the test
  layer (the module under test does NOT invoke WO-59); WO-59
  reports `source_reference_count: 65`, `source_record_count: 65`,
  `linked_source_count: 65`, and literal-False booleans.
- `ForbiddenLanguageOutputTest` (1) - `materialization_note` clean
  of all `FORBIDDEN_PHRASES` and `FORBIDDEN_CLAIM_PHRASES`.
- `StaticScanTest` (12) - absence of file-IO, network, HTTP-library,
  subprocess / shell, hashlib, browser-automation, PDF-extraction,
  retrieval-verb, external-integration tokens; presence of exactly
  the one allowed prior-WO public function name
  (`run_level0_manual_seed_visible_report`); absence of WO-59
  invocation; absence of WO-L0-TRACE-01 invocation; absence of all
  other WO-50 through WO-62 public function names.

## Non-Claim Constraints

WO-L0-MATERIAL-01 does not claim any generated source identifier,
origin string, declared kind mapping, synthetic hash, byte length
count, observed-at marker, item-id list, or computed count is
sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded `ITEM_KIND_TO_DECLARED_KIND`
mapping (7 entries), the bounded six required source-reference
fields, the bounded four required source-record fields, the
synthetic `L0-MAT-SRC-` / `L0-MAT-HASH-` identifier formats, the
literal `level0-manual-seed` observed-at marker, the literal
`external` source-origin marker, and the fifteen
`ALLOWED_OUTPUT_KEYS` are bounded by WO-L0-MATERIAL-01 and are NOT
claimed exhaustive.

All DC-020 through DC-064 boundary invariants carry forward.
WO-L0-MATERIAL-01 does not amend or broaden DC-003 through DC-064.
Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031, OQ-035,
OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
RK-039 remains active and is not duplicated.
