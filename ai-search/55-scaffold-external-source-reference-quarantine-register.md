# ai-search - Scaffold External Source Reference Quarantine Register

Document type: Phase 2 / Phase 4 / Phase 9 / Scaffold source-intake quarantine boundary
Owner: Codex (controller)
Author: Claude (under WO-55)
Status: Approved after Codex verification
Work Order: WO-55

---

## 1. Purpose

WO-55 adds the upstream quarantine boundary for external source
collections. The register admits already-loaded source reference
dicts (identity + integrity metadata only) into an in-memory intake
layer that explicitly records non-admission, non-qualification, and
non-route status. The register sits upstream of the WO-54
source-intake trace: WO-55 records the fact that an external source
exists as an inert reference; WO-54 (or any future scaffold) is the
only place where downstream observation occurs, and only over its own
already-loaded source records.

This is NOT prompt search, NOT skill search, NOT agent selection,
NOT generic RAG, NOT source qualification, NOT Source Card creation,
NOT corpus admission, NOT benchmark fixture admission, and NOT
production artifact schema creation.

The module performs no file read, no file write, no network call, no
download / fetch / crawl, no hash computation, no extraction, no
normalization, no candidate fragment derivation, no real retrieval /
indexing / ranking / similarity / scoring / metric collection, no
real or mock adapter invocation, no real benchmark execution, no
quality / performance / operational measurement, and no architecture
/ vendor / library / index family / ANN backend / neural re-scorer /
retrieval family / ablation cell / multi-stage variant / production
system choice.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Establish a named quarantine layer upstream of WO-54 that admits
  inert source references without admitting their content.
- Keep all data already-loaded in memory; module performs no file or
  network IO.
- Preserve all non-measurement / non-selection / non-readiness
  booleans as literal False; preserve literal-False
  `corpus_admitted` and `qualified` per register entry; preserve
  literal-zero `corpus_admitted_count` and `qualified_count`.
- Bound the admission surfaces (allowed field set, declared-kind
  set, route-status boolean set, forbidden field set) by the packet
  and explicitly not claim them exhaustive.

The scope does not authorize a real adapter, real retrieval service,
network call, third-party dependency, hash computation, benchmark
run, metric collection, architecture choice, Source Card creation,
Route Card creation, production artifact contract, or benchmark-
readiness change.

## 3. Added Files

WO-55 adds:

- `harness/scaffold_source_intake_register.py`
- `harness/tests/test_scaffold_source_intake_register.py`
- `ai-search/55-scaffold-external-source-reference-quarantine-register.md`

WO-55 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50, WO-51,
WO-52, WO-53, and WO-54 modules and their test files are not
modified.

## 4. Public Function

The new public function is:

```text
run_scaffold_source_intake_register(source_reference_records, event_log) -> dict
```

Inputs:

- `source_reference_records`: a list (possibly empty) of already-loaded
  source reference dicts. Each dict must contain EXACTLY the six
  allowed fields in `ALLOWED_REFERENCE_FIELDS`.
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no network call,
and computes no hash.

## 5. Allowed Reference Fields

`ALLOWED_REFERENCE_FIELDS` (exact set; unknown keys rejected):

- `source_id` (non-empty string)
- `origin` (non-empty string; inert reference only, not fetched,
  not read; counted for uniqueness; not echoed into any free-text
  output field)
- `declared_kind` (non-empty string; must be in `ALLOWED_DECLARED_KINDS`)
- `hash` (non-empty string; identity / integrity only; not
  qualification, not corpus admission, not validation)
- `byte_length` (non-negative `int`; `bool` rejected)
- `observed_at` (non-empty string)

`ALLOWED_DECLARED_KINDS`:

- `prompt_collection`
- `skill_collection`
- `agent_description_collection`
- `tool_description_collection`
- `document_collection`

These are source-reference labels only. They are not product
objects and not route kinds. The set is bounded by WO-55 and is
not claimed exhaustive.

## 6. Forbidden Reference Fields

Each source reference is rejected if it declares any of the
following keys (the field name alone is forbidden, regardless of
value, except where noted):

- Qualification space: `qualified`, `qualification_ref`,
  `corpus_admitted` (each rejected with its own named exception).
- Derived material: `extracted_material`, `normalized_material`,
  `candidate_fragments`, `candidate_route_fragments`,
  `candidate_workflow_fragments` (rejected with
  `DerivedMaterialForbiddenAtRegisterLayer`).
- Route-shaped: `route`, `route_id`, `route_state`, `plane`,
  `official`, `executable` (rejected with
  `RouteFieldForbiddenAtRegisterLayer`).
- Source-Card-shaped: `authority`, `trust`, `freshness`,
  `ownership`, `source_card`, `route_card`,
  `qualification_evidence`, `validation_evidence` (rejected with
  `SourceCardShapedFieldRejected`; OQ-031 remains OPEN).
- Benchmark-fixture-shaped: `benchmark_fixture_class`,
  `golden_intent`, `hard_negative`, `boundary_violation` (rejected
  with `BenchmarkFixtureFieldRejected`; RK-039 not relaxed).
- Any other route-status boolean key (`is_route`,
  `is_official_route`, `selected_as_official`,
  `official_route_authorized`, `route_authorized`,
  `production_route`, `selected_route`) set to `True` is rejected
  with `RouteStatusClaimAtRegisterLayer`. The same keys with non-True
  values fall through to `UnknownReferenceField`.
- Any other key falls through to `UnknownReferenceField`.

## 7. Hash / Integrity Rule

- `hash` is identity / integrity metadata only.
- `hash` never implies source qualification, corpus admission,
  validation, benchmark admission, or route trust.
- The module does not compute hashes (no `hashlib`, `.hexdigest`,
  `.sha256` tokens in the module source; verified by static-scan
  test).
- The module does not read bytes from disk.
- Per-entry `qualified` and `corpus_admitted` remain literal False
  on every emitted path regardless of any hash value.

## 8. Result Surface (Clean-Pass Only)

On clean pass, the register returns a fresh dict with exactly
eleven allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `register_kind`
- `references_observed_count`
- `unique_origin_count`
- `register_entries` (list of `{source_id, declared_kind,
  hash_prefix, byte_length, observed_at, corpus_admitted: False,
  qualified: False}` items; no `origin` echoed; no full `hash`
  echoed)
- `corpus_admitted_count` (literal `0`)
- `qualified_count` (literal `0`)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `intake_note`

Each `register_entries` entry carries only structural ids /
identity-prefix / length / observed-at, plus literal-False
`corpus_admitted` and `qualified` booleans. The `origin` value is
used for `unique_origin_count` only and is never copied into any
free-text output field. The `hash` value is truncated to a
non-leaky 12-character `hash_prefix` for the output entry.

## 9. Event Surface

Success events:

- `scaffold_source_intake_register_started`
- `scaffold_source_intake_reference_observed`
- `scaffold_source_intake_register_passed`

Rejection events are explicit halt events with
`scaffold_source_intake_register_*` reason strings. Halt events are
recorded before the corresponding named exception is raised.

## 10. Named Exceptions

- `NonListSourceReferences`
- `NonObjectSourceReference`
- `MissingReferenceField`
- `UnknownReferenceField`
- `DuplicateSourceId`
- `DeclaredKindNotAllowed`
- `InvalidHashField`
- `InvalidByteLength`
- `QualifiedFieldForbiddenAtRegisterLayer`
- `QualificationRefFieldForbiddenAtRegisterLayer`
- `CorpusAdmissionFieldForbiddenAtRegisterLayer`
- `DerivedMaterialForbiddenAtRegisterLayer`
- `RouteFieldForbiddenAtRegisterLayer`
- `RouteStatusClaimAtRegisterLayer`
- `SourceCardShapedFieldRejected`
- `BenchmarkFixtureFieldRejected`
- `ForbiddenLanguageInSourceIntakeRegister`

## 11. Tests Added

`harness/tests/test_scaffold_source_intake_register.py` adds 73 tests
across 12 `TestCase` classes covering:

- clean pass with prompt / skill / document collection references;
- empty reference list allowed;
- fixed eleven-key output shape;
- literal-False authorization / readiness / selection booleans;
- per-entry literal-False `corpus_admitted` and `qualified`;
- `hash_prefix` recorded in output; full hash not echoed;
- `scaffold_source_intake_register_passed` event with clean counts;
- non-list / non-object / missing-field / unknown-field /
  duplicate-source-id / non-allowed-declared-kind / invalid-hash /
  negative- or non-int- or bool-`byte_length` rejections;
- each of the forbidden-field rejection paths (`qualified` with
  `True` or `False`, `qualification_ref`, `corpus_admitted`,
  `extracted_material`, `normalized_material`, `candidate_fragments`,
  `candidate_route_fragments`, `candidate_workflow_fragments`,
  `route`, `route_id`, `route_state`, `plane`, `official`,
  `executable`);
- each of the route-status-claim paths (`is_route`,
  `is_official_route`, `selected_as_official`, `route_authorized`,
  `production_route` set to `True`);
- `is_route: False` falls through to `UnknownReferenceField`;
- each of the Source-Card-shaped field rejections;
- each of the benchmark-fixture-shaped field rejections;
- hash presence does not imply qualification or corpus admission;
- distinct hashes do not flip any boolean;
- origin is not echoed into `intake_note`;
- origin counted for uniqueness only;
- origin not appearing in `register_entries` output;
- output forbidden-language scan;
- input isolation;
- no filesystem writes;
- only stdlib + harness-internal imports;
- module source contains no `open(`, `pathlib`, `urllib`,
  `requests`, `http.client`, `socket`, `subprocess`, `os.system`, or
  `shutil` tokens;
- module source contains no `hashlib`, `.hexdigest`, or `.sha256`
  tokens (no hash computation);
- module source contains no `def query`, `def search`,
  `def retrieve`, or `def rank` public-surface verbs;
- `benchmark-fixtures/` files not mutated;
- constants admissibility (`ALLOWED_REFERENCE_FIELDS` exact
  six-field set; `ALLOWED_DECLARED_KINDS` matches packet;
  `ROUTE_STATUS_BOOLEAN_KEYS` contains every packet-required marker).

## 12. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 / WO-54
explicit non-claim constraint carries forward verbatim:

This module does not claim that any register entry, declared kind,
identity field, quarantine boundary, or in-memory observation is
sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded admission surfaces are not
claimed exhaustive.

The register records absence of corpus admission, absence of
qualification, absence of route-status claims, absence of derived
material, absence of Source-Card-shaped fields, and absence of
benchmark-fixture-shaped fields in the observed references. It does
not declare any referenced source admissible, qualified,
benchmark-eligible, or selected for any production system.

## 13. Forbidden Scope

WO-55 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- source download, fetch, crawl, or read;
- file read or file write inside the module;
- hash computation inside the module;
- extraction, normalization, or candidate fragment derivation;
- similarity, distance, or near-match scoring of any kind;
- quality, performance, or operational metric collection;
- Stage 2 / 3 / 4 / 5 measurement scaffolding;
- scoring, ranking, or winner declarations;
- a real retrieval adapter or any real retrieval / indexing /
  ranking implementation;
- architecture, vendor, library, index family, ANN backend, neural
  re-scorer, retrieval family, ablation cell, multi-stage variant,
  or production system choice;
- production artifact schema, retention policy, storage policy,
  immutability policy, access-control policy, or registration
  mechanism;
- Source Card creation;
- Route Card creation;
- third-party dependency;
- CLI / entry point / console script;
- mutation of any file under `benchmark-fixtures/`;
- modification of `harness/scaffold_route_query_probe.py`,
  `harness/tests/test_scaffold_route_query_probe.py`,
  `harness/scaffold_route_query_ambiguity_probe.py`,
  `harness/tests/test_scaffold_route_query_ambiguity_probe.py`,
  `harness/scaffold_conflicting_evidence_guard.py`,
  `harness/tests/test_scaffold_conflicting_evidence_guard.py`,
  `harness/scaffold_source_intake_trace.py`, or
  `harness/tests/test_scaffold_source_intake_trace.py`;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056,
  OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Real-benchmark-ready remains NO.

## 14. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_source_intake_register`
  -> 73/73 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 528/528 OK after the new module and tests were added (455
  prior baseline + 73 new).
- The WO-50, WO-51, WO-52, WO-53, and WO-54 modules and their test
  files are unchanged on disk during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order
  (SHA inventory unchanged).
- The module source has been statically inspected (via tests) for
  the absence of file-IO, network, and hash-computation tokens; no
  such tokens are present.

Real-benchmark-ready remains NO.
