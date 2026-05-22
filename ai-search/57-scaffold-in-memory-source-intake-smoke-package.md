# ai-search - Scaffold In-Memory Source Intake Smoke Package

Document type: Phase 2 / Phase 4 / Phase 9 / Scaffold composed-stage smoke package boundary
Owner: Codex (controller)
Author: Claude (under WO-57)
Status: Approved with notes after Codex verification
Work Order: WO-57

---

## 1. Purpose

WO-57 composes the already-approved WO-55 register, WO-56 bridge, and
WO-54 source-intake trace into a single read-only in-memory
observation. The package answers, at scaffold level only:

- I gave this input prompt.
- The system observed the prompt structurally.
- These already-loaded external source references were registered as
  inert references.
- These already-loaded source records linked to register entries.
- WO-54 trace ran only over already-loaded source records.
- No source became qualified by this package.
- No corpus admission, extraction authorization, candidate derivation
  authorization, route selection, measurement, or benchmark readiness
  occurred.

This is NOT prompt search, NOT skill search, NOT agent selection,
NOT generic RAG, NOT source qualification, NOT Source Card creation,
NOT corpus admission, NOT benchmark fixture admission, NOT production
artifact schema creation, and NOT real benchmark execution.

The module performs no file read, no file write, no network call, no
download / fetch / crawl, no hash computation, no extraction, no
normalization, no candidate-fragment derivation of its own, no real
or mock adapter invocation, no real benchmark execution, no quality
/ performance / operational measurement, no similarity / ranking /
metric computation, and no architecture / vendor / library / index
family / ANN backend / retrieval family / ablation cell / multi-stage
variant / production system choice.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Compose WO-55 (register), WO-56 (bridge), and WO-54 (trace) in
  strict order into one in-memory observation, propagating any
  exception verbatim without swallowing.
- Keep all data already-loaded in memory; module performs no file or
  network IO and computes no hash.
- Preserve every authorization / readiness / selection boolean as
  literal False at the package output (seven booleans total);
  preserve literal-zero `corpus_admitted_count` and `qualified_count`
  at the package output; copy candidate-fragment counts verbatim
  from the trace observation (not computed by scoring or search).
- Reject forbidden language on any surfaced output value with an
  explicit halt event before raising.

The scope does not authorize a real adapter, real retrieval service,
network call, third-party dependency, hash computation, extraction,
normalization, candidate-fragment derivation of its own, benchmark
run, metric collection, architecture choice, Source Card creation,
Route Card creation, production artifact contract, or
benchmark-readiness change.

## 3. Added Files

WO-57 adds:

- `harness/scaffold_source_intake_smoke_package.py`
- `harness/tests/test_scaffold_source_intake_smoke_package.py`
- `ai-search/57-scaffold-in-memory-source-intake-smoke-package.md`

WO-57 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50, WO-51,
WO-52, WO-53, WO-54, WO-55, and WO-56 modules and their test files
are not modified.

## 4. Public Function

```text
run_scaffold_source_intake_smoke_package(input_prompt, source_reference_records, source_records, event_log) -> dict
```

Inputs:

- `input_prompt`: a non-empty string per the WO-54 contract.
- `source_reference_records`: a list (possibly empty) of WO-55
  source reference dicts.
- `source_records`: a list (possibly empty) of WO-54 / WO-56 source
  record dicts.
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no network call,
computes no hash, and invokes WO-55 / WO-56 / WO-54 in strict order.

## 5. Strict Stage Order And Short-Circuit

The package invokes exactly three existing public functions in this
order:

1. `run_scaffold_source_intake_register(source_reference_records, event_log)` (WO-55)
2. `run_scaffold_source_trace_admission_bridge(register_observation, source_records, event_log)` (WO-56)
3. `run_scaffold_source_intake_trace(input_prompt, source_records, event_log)` (WO-54)

If WO-55 raises, the bridge and trace are not invoked. If WO-56
raises, the trace is not invoked. If WO-54 raises, the package
propagates the exception unchanged. The package never converts a
failure into a success summary and never swallows an exception. The
exception's propagation is verified by package-level tests that use
`unittest.mock.patch` to replace the bound names inside the smoke
package module (without modifying the existing modules).

## 6. Result Surface (Clean-Pass Only)

On clean pass, the package returns a fresh dict with exactly twenty
allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `package_kind`
- `input_prompt_observed` (copied from the trace observation;
  structural-only)
- `register_observation` (WO-55 output dict embedded verbatim)
- `bridge_observation` (WO-56 output dict embedded verbatim)
- `trace_observation` (WO-54 output dict embedded verbatim)
- `source_reference_count` (from register's
  `references_observed_count`)
- `source_record_count` (from bridge's
  `source_records_checked_count`)
- `linked_source_count` (from bridge)
- `trace_candidate_route_fragment_count` (length of trace's
  `candidate_route_fragments`; copied, not computed)
- `trace_candidate_workflow_fragment_count` (length of trace's
  `candidate_workflow_fragments`; copied, not computed)
- `corpus_admitted_count` (literal `0`)
- `qualified_count` (literal `0`)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `extraction_authorized` (literal `False`)
- `normalization_authorized` (literal `False`)
- `candidate_derivation_authorized` (literal `False`)
- `package_note`

## 7. Event Surface

Success events:

- `scaffold_source_intake_smoke_package_started`
- `scaffold_source_intake_smoke_package_register_completed`
- `scaffold_source_intake_smoke_package_bridge_completed`
- `scaffold_source_intake_smoke_package_trace_completed`
- `scaffold_source_intake_smoke_package_passed`

Rejection event:

- `scaffold_source_intake_smoke_package_forbidden_language` (only if
  the assembled package output contains a forbidden phrase; recorded
  before raising `ForbiddenLanguageInSourceIntakeSmokePackage`).

The package does not catch or convert any exception raised by
WO-55 / WO-56 / WO-54; those modules' own halt events are recorded
by them and remain visible in the event log.

## 8. Non-Admission Semantics

A successful package observation explicitly does NOT mean:

- source is qualified
- source is admitted to corpus
- source may be extracted
- source may be normalized
- source may produce candidate fragments
- source is a route
- source is benchmark data
- source is ready for any production system
- benchmark is ready

The `package_note` constant explicitly states these non-admissions
and lists the OQ tags that remain OPEN.

## 9. Forbidden-Phrase Surface Choice

WO-57 deliberately does not extend the forbidden-phrase set locally
beyond `FORBIDDEN_PHRASES`. The upstream WO-54, WO-55, and WO-56
modules already enforce the local-scope `("score", "scoring")`
extension on every value they emit, and this module's composed
output is built entirely from those observations plus the
author-controlled `_PACKAGE_NOTE` constant. Any value reachable from
the composed output has already been scrubbed at the layer that
produced it. This is an assumption Claude is flagging for Codex
review; see the WO-57 ledger entry.

## 10. Tests Added

`harness/tests/test_scaffold_source_intake_smoke_package.py` adds 21
tests across seven `TestCase` classes covering:

- clean pass with empty source-reference list and empty source-record
  list;
- clean pass with one inert reference and one matching bare source
  record;
- literal-False authorization / readiness / selection booleans (all
  seven at the package output);
- `package_note` mentions "NOT source qualification", "NOT corpus
  admission", "NOT route selection", "NOT benchmark readiness", and
  avoids the forbidden substring "architecture selection";
- structural-only `input_prompt_observed`; prompt text not echoed
  anywhere in the output;
- register / bridge / trace observations embedded verbatim;
- the `scaffold_source_intake_smoke_package_passed` event consistency;
- strict register -> bridge -> trace call order (verified with
  `unittest.mock.patch` replacing the bound names inside the smoke
  package module);
- register failure prevents bridge and trace invocation;
- bridge failure prevents trace invocation;
- trace failure propagates and leaves the event log in a partial
  state without a `_passed` event;
- real-failure tests at each stage propagate without swallowing;
- output forbidden-language scan;
- input not mutated;
- no filesystem writes;
- only stdlib + harness-internal imports;
- module source contains no `open(`, `pathlib`, `urllib`, `requests`,
  `http.client`, `socket`, `subprocess`, `os.system`, `shutil`,
  `hashlib`, `.hexdigest`, or `.sha256` tokens;
- module source contains no `def query` / `def search` /
  `def retrieve` / `def rank` / `score` / `scoring` tokens (the
  packet-required static-scan list);
- `benchmark-fixtures/` files not mutated.

## 11. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 / WO-54 /
WO-55 / WO-56 explicit non-claim constraint carries forward
verbatim:

This module does not claim that any composition, observation, or
stage is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected. The package surfaces and
the composition order are bounded by WO-57 and are not claimed
exhaustive.

The package records cross-stage composition only. It does not
declare any source admissible, qualified, extractable, normalizable,
fragment-derivable, route-valid, or selected for any production
system.

## 12. Forbidden Scope

WO-57 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- source download, fetch, crawl, or read;
- file read or file write inside the module;
- hash computation inside the module;
- extraction, normalization, or candidate-fragment derivation of its
  own (counts are copied verbatim from the trace observation);
- similarity, distance, or near-match scoring of any kind;
- quality, performance, or operational metric collection;
- ranking or winner declarations;
- a real retrieval adapter or any real retrieval / indexing /
  ranking implementation;
- architecture, vendor, library, index family, ANN backend, neural
  re-scoring, retrieval family, ablation cell, multi-stage variant,
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
  `harness/scaffold_source_intake_register.py`,
  `harness/tests/test_scaffold_source_intake_register.py`,
  `harness/scaffold_source_trace_admission_bridge.py`, or
  `harness/tests/test_scaffold_source_trace_admission_bridge.py`;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056,
  OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Real-benchmark-ready remains NO.

## 13. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_source_intake_smoke_package`
  -> 21/21 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 609/609 OK after the new module and tests were added (588
  prior baseline + 21 new).
- The WO-50, WO-51, WO-52, WO-53, WO-54, WO-55, and WO-56 modules
  and their test files are unchanged on disk during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.
- The module source contains no file-IO / network / hash tokens
  and no `def query` / `def search` / `def retrieve` / `def rank` /
  `score` / `scoring` tokens (verified by static-scan tests).

Real-benchmark-ready remains NO.

## 14. Codex Verification Note

Codex verified WO-57 locally and approved it with notes.

Verification run by Codex:

- `python -B -m unittest harness.tests.test_scaffold_source_intake_smoke_package -v`
  -> 21/21 OK.
- `python -B -m unittest discover -s harness/tests -v`
  -> 609/609 OK.

Review note: WO-57 is a bare-source smoke composition. Because the
WO-56 bridge rejects qualified and derived-material source-record
fields, this package does not make the WO-54 qualified
derived-fragment path reachable through the bridge. That is acceptable
for WO-57's smoke-package scope and remains a future-scope concern,
not a blocker for this Work Order.
