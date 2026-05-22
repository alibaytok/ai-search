# ai-search - Read-Only External Source Intake And Prompt-To-Route Trace

Document type: Phase 4 / Phase 9 / Scaffold source-intake trace boundary
Owner: Codex (controller)
Author: Claude (under WO-54)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-54

---

## 1. Purpose

WO-54 adds the first scaffold-level module that traces a captured
user prompt (a non-empty string) through external source records
into candidate route and workflow fragments while preserving the
route-first invariants. The trace is read-only: it observes
already-loaded source records and emits events that narrate the
layered preconditions (qualification before extracted_material /
normalized_material / candidate_fragments; extracted_material
before normalized_material; normalized_material before
candidate_fragments).

This is NOT prompt search, NOT skill search, NOT agent selection,
NOT generic RAG, and NOT real benchmark execution. The module
performs no file read, no file write, and no network call. It uses
only Python standard library plus harness-internal forbidden-language
constants.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Make the first observable path from a user prompt through external
  source material to candidate fragments visible.
- Keep all data already-loaded in memory; module performs no file or
  network IO.
- Preserve the route-first invariants: raw prompt / skill / agent /
  tool / document / internet content is never returned as a route;
  candidate fragments stay candidate-only; normalized material stays
  normalized-only; no official route selection is performed.
- Preserve all non-measurement / non-selection / non-readiness
  booleans as literal False.

The scope does not authorize a real adapter, real retrieval service,
network call, third-party dependency, benchmark run, metric
collection, architecture choice, production artifact contract, or
benchmark-readiness change.

## 3. Added Files

WO-54 adds:

- `harness/scaffold_source_intake_trace.py`
- `harness/tests/test_scaffold_source_intake_trace.py`
- `ai-search/54-read-only-external-source-intake-and-prompt-to-route-trace.md`

WO-54 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50, WO-51,
WO-52, and WO-53 modules and their test files are not modified.

## 4. Public Function

The new public function is:

```text
run_scaffold_source_intake_trace(input_prompt, source_records, event_log) -> dict
```

Inputs:

- `input_prompt`: a non-empty string. The prompt is captured intent
  input; it is not a route. The trace records its observation
  structurally (`{observed: True, captured_intent_text_length: N}`)
  and does NOT echo its text into the output dict.
- `source_records`: a list (possibly empty) of already-loaded source
  dicts. Each source record carries `source_id`, `source_kind`,
  `source_origin`, and may carry `qualified`, `qualification_ref`,
  `extracted_material`, `normalized_material`, and
  `candidate_fragments` per the WO-54 packet's example.
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, and makes no network
call.

## 5. Route-First Layered Preconditions

The trace enforces the following layered preconditions (each is
recorded with an explicit halt event before the corresponding named
exception is raised):

1. **Qualification gate.** A source record carrying any of
   `extracted_material`, `normalized_material`, or
   `candidate_fragments` must declare `qualified: True`. Otherwise
   `QualificationGate` is raised.
2. **Qualification reference.** Any source declaring `qualified:
   True` must declare a non-empty `qualification_ref` string.
   Otherwise `MissingQualificationRef` is raised.
3. **Extraction before normalization.** A source record's
   `normalized_material` is only observed when the source carries
   `extracted_material`. Otherwise `NormalizationWithoutExtraction`
   is raised.
4. **Normalization before candidate fragments.** A source record's
   `candidate_fragments` are only observed when the source carries
   `normalized_material`. Otherwise
   `CandidateFragmentsWithoutNormalization` is raised.
5. **Candidate-only candidate fragments.** Each candidate fragment
   must declare `candidate_only: True`, must declare a
   `fragment_kind` in `ALLOWED_FRAGMENT_KINDS` (one of
   `candidate_route_fragment`, `candidate_workflow`), and must
   declare a `derived_from_normalized_id` that matches the source
   record's `normalized_material.normalized_id`.

A source record may be admitted with `source_id`, `source_kind`,
`source_origin` only (a bare unqualified source) without raising;
such a source contributes zero to all derived counts and to the
output's qualified / extracted / normalized / fragment fields.

## 6. Route-Status Marker Guard

The module rejects any of the following route-status claims when
declared at any input layer (source record, `extracted_material`,
`normalized_material`, candidate fragment):

- Any of `ROUTE_STATUS_CLAIM_BOOLEAN_KEYS` set to `True`
  (`official`, `is_route`, `is_official_route`,
  `selected_as_official`, `official_route_authorized`,
  `route_authorized`, `production_route`, `selected_route`,
  `executable`).
- `route_state` field set to `"official"`.
- `plane` field set to `"official_route_results"`.

Each route-status claim records an explicit halt event before
raising the corresponding named exception
(`SourceClaimsRouteStatus`, `ExtractedMaterialClaimsRouteStatus`,
`NormalizationClaimsRouteStatus`,
`CandidateFragmentClaimsRouteStatus`).

## 7. Admission Surfaces

- `ALLOWED_SOURCE_ORIGIN = "external"`. The module rejects any
  source record whose `source_origin` is not `external`.
- `ALLOWED_FRAGMENT_KINDS = {candidate_route_fragment,
  candidate_workflow}`. Any other `fragment_kind` is rejected with
  `CandidateFragmentForbiddenKind`.
- `ROUTE_STATUS_CLAIM_BOOLEAN_KEYS`, `OFFICIAL_ROUTE_STATE_VALUE`,
  and `OFFICIAL_ROUTE_PLANE_VALUE` define the forbidden route-status
  claim space.

The admission surfaces are bounded by WO-54 and are not a claim of
completeness; future Codex packets may extend them.

## 8. Result Surface (Clean-Pass Only)

On clean pass, the trace returns a fresh dict with exactly fifteen
allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `trace_kind`
- `input_prompt_observed` (structural observation only; the prompt
  text is never copied)
- `normalized_intent_observation` (structural observation only)
- `sources_touched_count`
- `qualified_sources_count`
- `normalized_material_refs` (list of `{source_id, normalized_id}`
  refs; no raw text)
- `candidate_route_fragments` (list of `{source_id, fragment_id,
  derived_from_normalized_id}` refs for fragments with
  `fragment_kind == "candidate_route_fragment"`; no raw text)
- `candidate_workflow_fragments` (list of the same shape for
  fragments with `fragment_kind == "candidate_workflow"`; no raw
  text)
- `rejected_source_count` (literal `0`; rejections halt)
- `rejection_reasons` (literal `[]`; rejections halt)
- `selection_made`
- `measurement_authorized`
- `real_benchmark_authorized`
- `real_benchmark_ready`
- `trace_note`

The four authorization / readiness / selection booleans are literal
False on every emitted path.

## 9. Event Surface

Success events:

- `scaffold_source_intake_trace_started`
- `scaffold_source_intake_source_observed`
- `scaffold_source_intake_normalized_material_observed`
- `scaffold_source_intake_candidate_fragment_observed`
- `scaffold_source_intake_trace_passed`

Rejection events are explicit halt events with
`scaffold_source_intake_trace_*` reason strings. Halt events are
recorded before the corresponding exception is raised. A
`scaffold_source_intake_source_rejected` event name is reserved by
the packet for a future non-halting rejection mode; the current
module always halts on the first rejection so the event is not
emitted in WO-54.

## 10. Tests Added

`harness/tests/test_scaffold_source_intake_trace.py` adds 46 tests
across 13 `TestCase` classes covering:

- clean pass with required source mix (one prompt-like source +
  one skill-like source + one `candidate_route_fragment` + one
  `candidate_workflow`);
- literal-False authorization / readiness / selection booleans;
- empty `source_records` allowed;
- `input_prompt_observed` is structural only; prompt text is not
  echoed into the output;
- `scaffold_source_intake_trace_passed` event counts match output
  counts;
- raw extracted text (sentinel strings) is not copied into
  `normalized_material_refs`, `candidate_route_fragments`, or
  `candidate_workflow_fragments`;
- non-string input prompt rejected;
- empty input prompt rejected;
- non-list source records rejected;
- non-object source record rejected;
- missing `source_id` rejected;
- missing `source_kind` / `source_origin` rejected;
- non-external `source_origin` rejected;
- duplicate `source_id` rejected;
- source declares route-status claim rejected;
- qualification gate rejects extracted / normalized / fragments
  without `qualified: True` (three tests);
- qualified source without non-empty `qualification_ref` rejected,
  including the bare qualified-without-derived-material path added by
  Codex review-time hardening;
- bare unqualified source admitted as touched-but-not-qualified;
- normalized_material without extracted_material rejected;
- candidate_fragments without normalized_material rejected;
- extracted_material `route_state == "official"` rejected;
- extracted_material `plane == "official_route_results"` rejected;
- extracted_material `executable: True` rejected;
- normalized_material declares route-status claim rejected;
- non-object candidate fragment rejected;
- missing fragment field rejected;
- fragment not `candidate_only: True` rejected;
- fragment `fragment_kind` outside allowed set rejected;
- fragment `derived_from_normalized_id` mismatch rejected;
- fragment `official: True` rejected;
- fragment `route_state == "official"` rejected;
- fragment `plane == "official_route_results"` rejected;
- output has no forbidden language;
- inputs not mutated;
- no filesystem writes;
- module imports only stdlib + harness-internal;
- module source contains no `open(`, `pathlib`, `urllib`,
  `requests`, `http.client`, `socket`, `subprocess`, `os.system`,
  or `shutil` tokens;
- `benchmark-fixtures/` files not mutated;
- packet-required route-status markers (`official`, `executable`)
  are present in `ROUTE_STATUS_CLAIM_BOOLEAN_KEYS`;
  `OFFICIAL_ROUTE_STATE_VALUE`, `OFFICIAL_ROUTE_PLANE_VALUE`,
  `ALLOWED_SOURCE_ORIGIN`, and `ALLOWED_FRAGMENT_KINDS` match
  packet definitions.

## 11. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 explicit
non-claim constraint carries forward verbatim:

This module does not claim that any trace, layer, marker, admission
surface, fragment kind, or in-memory observation is sufficient,
necessary, superior, best, complete, production-ready, recommended,
or selected. The admission surfaces and the route-status claim space
are bounded by WO-54 and are not claimed exhaustive.

The trace records absence of route-status claims and absence of
forbidden-kind fragments in the observed inputs. It does not
declare the observed inputs admissible as benchmark evidence,
production-ready, or selected for any production system.

## 12. Forbidden Scope

WO-54 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- file read or file write inside the module;
- similarity, distance, or near-match scoring of any kind;
- quality, performance, or operational metric collection;
- Stage 2 / 3 / 4 / 5 measurement scaffolding;
- scoring, ranking, or winner declarations;
- a real retrieval adapter or real retrieval / indexing / ranking
  implementation;
- architecture, vendor, library, index family, ANN backend, neural
  re-scorer, retrieval family, ablation cell, multi-stage variant,
  or production system choice;
- production artifact schema, retention policy, storage policy,
  immutability policy, access-control policy, or registration
  mechanism;
- third-party dependency;
- CLI / entry point / console script;
- mutation of any file under `benchmark-fixtures/`;
- modification of `harness/scaffold_route_query_probe.py`,
  `harness/tests/test_scaffold_route_query_probe.py`,
  `harness/scaffold_route_query_ambiguity_probe.py`,
  `harness/tests/test_scaffold_route_query_ambiguity_probe.py`,
  `harness/scaffold_conflicting_evidence_guard.py`, or
  `harness/tests/test_scaffold_conflicting_evidence_guard.py`;
- closure of OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Real-benchmark-ready remains NO.

## 13. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_source_intake_trace`
  -> 46/46 OK after Codex review-time hardening.
- `python -B -m unittest discover -s harness/tests`
  -> 455/455 OK after Codex review-time hardening (409 prior
  baseline + 46 WO-54 tests).
- The WO-50, WO-51, WO-52, and WO-53 modules and their test files
  are unchanged on disk during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.

Real-benchmark-ready remains NO.
