# ai-search - Scaffold Source Register-To-Trace Admission Bridge

Document type: Phase 2 / Phase 4 / Phase 9 / Scaffold pre-trace admission boundary
Owner: Codex (controller)
Author: Claude (under WO-56)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-56

---

## 1. Purpose

WO-56 adds the pre-trace admission bridge that sits between WO-55
(the inert source reference quarantine register) and WO-54 (the
read-only source-intake trace). The bridge accepts the WO-55
clean-pass register observation dict plus a list of already-loaded
source record dicts and verifies that:

- the register observation is shaped as a WO-55 clean-pass output and
  asserts no admission / no qualification / no authorization at the
  register layer;
- every source record references an existing register entry by
  `source_register_ref`;
- the matched register entry's `declared_kind` agrees with the source
  record's `source_kind`;
- no source record declares qualification, carries derived material,
  declares route status, or carries Source-Card-shaped fields.

A successful bridge observation means ONLY that the cross-references
are consistent. It does NOT mean any source is qualified, admitted,
extractable, normalizable, fragment-derivable, route-valid, or
benchmark-ready.

This is NOT prompt search, NOT skill search, NOT agent selection,
NOT generic RAG, NOT source qualification, NOT Source Card creation,
NOT corpus admission, NOT benchmark fixture admission, and NOT
production artifact schema creation.

The module performs no file read, no file write, no network call, no
download / fetch / crawl, no hash computation. It does NOT invoke
the WO-54 trace or the WO-55 register; it only reads the WO-55 clean-
pass output dict and the WO-54-shaped source record dicts that the
caller has already loaded.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Establish a named pre-trace admission boundary between WO-55 and
  WO-54 that verifies cross-references without admitting, qualifying,
  or authorizing any source.
- Keep all data already-loaded in memory; module performs no file or
  network IO and computes no hash.
- Preserve all non-measurement / non-selection / non-readiness
  booleans as literal False; preserve literal-False
  `extraction_authorized`, `normalization_authorized`, and
  `candidate_derivation_authorized`; preserve literal-False
  `corpus_admitted` and `qualified` per linked source; preserve
  literal-zero `corpus_admitted_count` and `qualified_count`.
- Reject any register observation that itself declares admission,
  qualification, or authorization.
- Reject any source record that declares qualification, derived
  material, route status, or Source-Card-shaped fields.

The scope does not authorize a real adapter, real retrieval service,
network call, third-party dependency, hash computation, extraction,
normalization, candidate fragment derivation, benchmark run, metric
collection, architecture choice, Source Card creation, Route Card
creation, production artifact contract, or benchmark-readiness
change.

## 3. Added Files

WO-56 adds:

- `harness/scaffold_source_trace_admission_bridge.py`
- `harness/tests/test_scaffold_source_trace_admission_bridge.py`
- `ai-search/56-scaffold-source-register-to-trace-admission-bridge.md`

WO-56 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50, WO-51,
WO-52, WO-53, WO-54, and WO-55 modules and their test files are not
modified.

## 4. Public Function

```text
run_scaffold_source_trace_admission_bridge(register_observation, source_records, event_log) -> dict
```

Inputs:

- `register_observation`: the WO-55 clean-pass output dict.
- `source_records`: a list (possibly empty) of already-loaded source
  record dicts. Each must carry `source_id`, `source_kind`,
  `source_origin == "external"`, and `source_register_ref` matching
  a register entry `source_id`.
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no network call,
computes no hash, and does not invoke either WO-54 or WO-55.

## 5. Register Observation Requirements

The bridge accepts only a WO-55 clean-pass output:

- `register_kind == "scaffold_source_intake_register"`
- `register_entries` is a list
- every register entry carries the seven required fields
  (`source_id`, `declared_kind`, `hash_prefix`, `byte_length`,
  `observed_at`, `corpus_admitted`, `qualified`)
- register entry `source_id` values are unique within the supplied
  register observation
- per-entry `corpus_admitted is False` and `qualified is False`
- top-level `corpus_admitted_count == 0`
- top-level `qualified_count == 0`
- top-level `selection_made`, `measurement_authorized`,
  `real_benchmark_authorized`, `real_benchmark_ready` all literal
  `False`

Any deviation halts and raises one of:

- `NonObjectRegisterObservation`
- `InvalidRegisterObservationShape`
- `DuplicateRegisterSourceId`
- `RegisterObservationDeclaresCorpusAdmission`
- `RegisterObservationDeclaresQualification`
- `RegisterObservationDeclaresAuthorization`

## 6. Source Record Bridge Requirements

Each source record must be a dict carrying the four required fields
(`source_id`, `source_kind`, `source_origin`, `source_register_ref`)
as non-empty strings, with `source_origin == "external"` and
`source_register_ref` matching an existing register entry
`source_id`. The matched register entry's `declared_kind` must equal
the source record's `source_kind`. Duplicate `source_id` values
across source records are rejected.

The bridge also rejects, with an explicit halt event before raising,
any source record declaring or carrying:

- `qualified` (any value) -> `SourceRecordDeclaresQualification`
- `qualification_ref` -> `SourceRecordCarriesQualificationRef`
- `extracted_material`, `normalized_material`,
  `candidate_fragments`, `candidate_route_fragments`, or
  `candidate_workflow_fragments` ->
  `SourceRecordCarriesDerivedMaterial`
- `route`, `route_id`, `route_state`, `plane`, `official`,
  `executable`, `is_route`, `is_official_route`,
  `selected_as_official`, `official_route_authorized`,
  `route_authorized`, `production_route`, `selected_route` ->
  `SourceRecordClaimsRouteStatus`
- `authority`, `trust`, `freshness`, `ownership`, `source_card`,
  `route_card`, `qualification_evidence`, `validation_evidence` ->
  `SourceCardShapedFieldRejected`

Source-record fields outside the required set and outside the
forbidden categories above are tolerated; the bridge does not
enforce an exhaustive source-record schema. The bounded forbidden
categories are not claimed exhaustive.

## 7. Non-Admission Semantics

A successful bridge observation explicitly does NOT mean:

- source is qualified
- source is admitted to corpus
- source may be extracted
- source may be normalized
- source may produce candidate fragments
- source is a route
- source is benchmark data
- source is ready for WO-54 trace
- benchmark is ready

The output dict carries `extraction_authorized: False`,
`normalization_authorized: False`,
`candidate_derivation_authorized: False`,
`corpus_admitted_count: 0`, and `qualified_count: 0`, and each
linked source carries `corpus_admitted: False`, `qualified: False`,
`extraction_authorized: False`, `normalization_authorized: False`,
and `candidate_derivation_authorized: False`.

## 8. Result Surface (Clean-Pass Only)

On clean pass, the bridge returns a fresh dict with exactly fifteen
allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `bridge_kind`
- `register_entry_count`
- `source_records_checked_count`
- `linked_source_count`
- `linked_sources` (list of `{source_id, source_register_ref,
  declared_kind, source_kind, corpus_admitted: False, qualified:
  False, extraction_authorized: False, normalization_authorized:
  False, candidate_derivation_authorized: False}` items; no raw
  text, no origin, no full hash)
- `corpus_admitted_count` (literal `0`)
- `qualified_count` (literal `0`)
- `extraction_authorized` (literal `False`)
- `normalization_authorized` (literal `False`)
- `candidate_derivation_authorized` (literal `False`)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `bridge_note`

## 9. Event Surface

Success events:

- `scaffold_source_trace_admission_bridge_started`
- `scaffold_source_trace_admission_bridge_source_linked`
- `scaffold_source_trace_admission_bridge_passed`

Rejection events are explicit halt events with
`scaffold_source_trace_admission_bridge_*` reason strings. Halt
events are recorded before the corresponding named exception is
raised.

## 10. Named Exceptions

- `NonObjectRegisterObservation`
- `InvalidRegisterObservationShape`
- `RegisterObservationDeclaresCorpusAdmission`
- `RegisterObservationDeclaresQualification`
- `RegisterObservationDeclaresAuthorization`
- `NonListSourceRecords`
- `NonObjectSourceRecord`
- `MissingSourceRecordField`
- `DuplicateSourceId`
- `SourceOriginNotExternal`
- `UnknownSourceRegisterRef`
- `SourceKindRegisterKindMismatch`
- `SourceRecordDeclaresQualification`
- `SourceRecordCarriesQualificationRef`
- `SourceRecordCarriesDerivedMaterial`
- `SourceRecordClaimsRouteStatus`
- `SourceCardShapedFieldRejected`
- `ForbiddenLanguageInSourceTraceAdmissionBridge`

## 11. Tests Added

`harness/tests/test_scaffold_source_trace_admission_bridge.py` adds
60 tests across nine `TestCase` classes covering:

- clean pass linking prompt / skill / document source records to
  register entries;
- literal-False authorization / readiness / selection booleans;
- literal-zero counts;
- per-linked-source literal-False `corpus_admitted`, `qualified`,
  `extraction_authorized`, `normalization_authorized`,
  `candidate_derivation_authorized`;
- empty source records with non-empty register allowed;
- empty register and empty source records allowed;
- the `scaffold_source_trace_admission_bridge_passed` event;
- non-object / invalid-kind / missing-entries / missing-entry-field
  / corpus-admitted-true / qualified-true /
  count-nonzero / authorization-true / duplicate-register-source-id
  rejections at the register layer;
- non-list / non-object / missing-required-field /
  non-external-origin / duplicate-source-id / unknown-register-ref
  / source-kind-mismatch rejections at the source-record layer;
- every forbidden-field rejection (qualified True / False;
  qualification_ref; each derived-material field; each
  route-status field; each Source-Card-shaped field);
- output forbidden-language scan;
- input isolation;
- no filesystem writes;
- only stdlib + harness-internal imports;
- module source contains no `open(`, `pathlib`, `urllib`,
  `requests`, `http.client`, `socket`, `subprocess`, `os.system`,
  `shutil`, `hashlib`, `.hexdigest`, or `.sha256` tokens;
- module source does not reference `run_scaffold_source_intake_trace`
  or `run_scaffold_source_intake_register` (no WO-54 / WO-55
  invocation);
- module source contains no `def query` / `def search` /
  `def retrieve` / `def rank` public-surface verbs;
- `benchmark-fixtures/` files not mutated;
- constants admissibility (`EXPECTED_REGISTER_KIND`,
  `REGISTER_ENTRY_REQUIRED_FIELDS`,
  `SOURCE_RECORD_REQUIRED_FIELDS`, `ALLOWED_SOURCE_ORIGIN`,
  `ROUTE_STATUS_FIELDS`).

## 12. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 / WO-54 /
WO-55 explicit non-claim constraint carries forward verbatim:

This module does not claim that any bridge, link, admission surface,
register entry, or in-memory observation is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected. The bounded admission surfaces and the bounded forbidden
categories are not claimed exhaustive.

The bridge records cross-reference consistency only. It does not
declare any referenced source admissible, qualified, extractable,
normalizable, fragment-derivable, route-valid, or selected for any
production system.

## 13. Forbidden Scope

WO-56 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- source download, fetch, crawl, or read;
- file read or file write inside the module;
- hash computation inside the module;
- extraction, normalization, or candidate fragment derivation;
- invocation of the WO-54 source-intake trace;
- invocation of the WO-55 source-intake register;
- similarity, distance, or near-match scoring of any kind;
- quality, performance, or operational metric collection;
- scoring, ranking, or winner declarations;
- a real retrieval adapter or any real retrieval / indexing /
  ranking implementation;
- architecture, vendor, library, index family, ANN backend, neural
  re-scorer, retrieval family, ablation cell, multi-stage variant,
  or production system choice;
- Source Card creation;
- Route Card creation;
- production artifact schema, retention, storage, immutability,
  access-control, or registration policy;
- third-party dependency;
- CLI / entry point / console script;
- mutation of any file under `benchmark-fixtures/`;
- modification of `harness/scaffold_route_query_probe.py`,
  `harness/tests/test_scaffold_route_query_probe.py`,
  `harness/scaffold_route_query_ambiguity_probe.py`,
  `harness/tests/test_scaffold_route_query_ambiguity_probe.py`,
  `harness/scaffold_conflicting_evidence_guard.py`,
  `harness/tests/test_scaffold_conflicting_evidence_guard.py`,
  `harness/scaffold_source_intake_trace.py`,
  `harness/tests/test_scaffold_source_intake_trace.py`,
  `harness/scaffold_source_intake_register.py`, or
  `harness/tests/test_scaffold_source_intake_register.py`;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056,
  OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Real-benchmark-ready remains NO.

## 14. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_source_trace_admission_bridge`
  -> 59/59 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 587/587 OK after the new module and tests were added (528
  prior baseline + 59 new).
- The WO-50, WO-51, WO-52, WO-53, WO-54, and WO-55 modules and
  their test files are unchanged on disk during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.
- The module source contains no file-IO / network / hash tokens
  and no reference to the WO-54 or WO-55 public-function names
  (verified by static-scan tests).

Real-benchmark-ready remains NO.

## 15. Codex Review-Time Hardening

Codex found one contract-safety gap during final verification: a
tampered register observation with duplicate register entry
`source_id` values could silently overwrite the first entry in the
bridge lookup index. That made source linkage depend on entry order
instead of a unique register identity.

Hardening added:

- named exception `DuplicateRegisterSourceId`;
- halt reason
  `scaffold_source_trace_admission_bridge_duplicate_register_source_id`;
- rejection before bridge linkage when duplicate register entry
  `source_id` values are present;
- regression test `test_duplicate_register_source_id_rejected`.

Codex verified after this hardening:

- `python -B -m unittest harness.tests.test_scaffold_source_trace_admission_bridge -v`
  -> 60/60 OK.
- `python -B -m unittest discover -s harness/tests`
  -> 588/588 OK.

This hardening does not authorize source qualification, corpus
admission, extraction, normalization, candidate derivation, real
benchmark execution, or architecture selection. Real-benchmark-ready
remains NO.
