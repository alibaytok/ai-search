# ai-search - Scaffold Visible Source-Intake Flow Report

Document type: Phase 2 / Phase 4 / Phase 9 / Scaffold composed visible-report boundary
Owner: Codex (controller)
Author: Claude (under WO-59)
Status: Approved after Codex verification
Work Order: WO-59

---

## 1. Purpose

WO-59 composes the WO-57 in-memory source-intake smoke package and
the WO-58 route-invariant diagnostic reporter into a single
read-only visible review observation. The report is the first
end-to-end visible local flow surface, surfacing:

- what input prompt was observed structurally;
- which source references were registered;
- which source records were linked;
- what the WO-54 trace observation produced (embedded via WO-57);
- which candidate route / workflow fragments were observed;
- what WO-58 diagnostics reported;
- whether any review halt is advised.

### What this is NOT

- NOT real indexing; NOT real retrieval; NOT prompt search; NOT
  skill search; NOT agent selection; NOT generic RAG.
- NOT benchmark execution; NOT a benchmark-readiness flip; NOT a
  metric / scoring / ranking / similarity / threshold / weight
  surface.
- NOT source qualification; NOT corpus admission; NOT a route
  validator; NOT a Source Card; NOT a Route Card.
- NOT architecture / vendor / library / index family / ANN backend
  / retrieval family / production system selection.
- NOT Microsoft extension integration; NOT Copilot / Waza / VS
  Code integration; NOT LLM / model integration; NOT IDE-side
  integration of any kind.
- NOT a prompt / skill / agent evaluation harness.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Compose WO-57 (smoke package) and WO-58 (diagnostic reporter) in
  strict order, propagating any exception verbatim without
  swallowing.
- Keep all data already-loaded in memory; module performs no file
  or network IO and computes no hash.
- Preserve every report-output standard authorization / readiness /
  selection boolean as literal False, regardless of how many
  diagnostic findings with `halt_required: True` appear in the
  embedded `diagnostic_report`.
- Surface `review_halt_required` as advisory metadata only.
- Do NOT invoke WO-54, WO-55, or WO-56 directly; only compose
  through WO-57 and WO-58. Verified by static-scan tests that
  reject the WO-54 / WO-55 / WO-56 public-function names in the
  module source.

The scope does not authorize real adapter invocation, real
benchmark execution, network calls, file IO, hash computation,
extraction, normalization, candidate-fragment derivation of its
own, similarity / ranking / scoring, model judgment, fuzzy semantic
analysis, thresholds, weights, architecture / vendor / library /
index family / production system choice, subprocess / shell
execution, external IDE / model / chat / collaborator
integrations, or any benchmark-readiness change.

## 3. Added Files

WO-59 adds:

- `harness/scaffold_source_intake_visible_report.py`
- `harness/tests/test_scaffold_source_intake_visible_report.py`
- `ai-search/59-scaffold-visible-source-intake-flow-report.md`

WO-59 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 through
WO-58 modules and their test files are not modified.
`ai-search/00-controller-checklist.md` is not modified.

## 4. Public Function

```text
run_scaffold_source_intake_visible_report(input_prompt, source_reference_records, source_records, event_log) -> dict
```

Inputs:

- `input_prompt`: a non-empty string per the WO-54 contract (passed
  through WO-57).
- `source_reference_records`: a list (possibly empty) of WO-55
  source reference dicts (passed through WO-57).
- `source_records`: a list (possibly empty) of WO-56 / WO-54 source
  record dicts (passed through WO-57).
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no network call,
computes no hash, and does not invoke WO-54 / WO-55 / WO-56 public
functions directly.

## 5. Strict Stage Order And Short-Circuit

The visible report invokes exactly two existing public functions in
this order:

1. `run_scaffold_source_intake_smoke_package(input_prompt,
   source_reference_records, source_records, event_log)` (WO-57)
2. `run_scaffold_route_invariant_diagnostic_reporter(observations,
   event_log)` (WO-58), where `observations` is a single-element
   list containing a shallow copy of the WO-57 output dict with an
   `observation_kind` key set to `"scaffold_source_intake_smoke_package"`.

If WO-57 raises, WO-58 is not invoked and the exception propagates
unchanged. If WO-58 raises, the exception propagates unchanged. The
module never converts a failure into a success summary and never
swallows an exception. Order is verified by tests using
`unittest.mock.patch` to replace the bound names inside the visible
report module (without modifying the WO-57 / WO-58 modules).

## 6. Result Surface (Clean-Pass Only)

On clean pass, the report returns a fresh dict with exactly
seventeen allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `visible_report_kind`
- `input_prompt_observed` (copied from the WO-57 package
  observation; structural-only)
- `source_reference_count`
- `source_record_count`
- `linked_source_count`
- `trace_candidate_route_fragment_count` (copied from the WO-57
  package observation, not computed by scoring or search)
- `trace_candidate_workflow_fragment_count` (copied from the WO-57
  package observation, not computed by scoring or search)
- `package_observation` (WO-57 output dict embedded verbatim)
- `diagnostic_report` (WO-58 output dict embedded verbatim)
- `diagnostic_error_count` (copied from `diagnostic_report.error_count`)
- `diagnostic_halt_required_count` (copied from
  `diagnostic_report.halt_required_count`)
- `review_halt_required` (boolean; True iff
  `diagnostic_halt_required_count > 0`)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `visible_report_note`

The four standard authorization / readiness / selection booleans
are literal False on every emitted path, regardless of how many
diagnostic findings with `halt_required: True` appear in the
embedded `diagnostic_report`.

## 7. `review_halt_required` Semantics

`review_halt_required` is True if and only if the embedded
`diagnostic_report["halt_required_count"]` is greater than zero. It
is advisory report metadata for the caller; it does NOT cause the
visible report to raise, and it does NOT flip any of the four
standard authorization / readiness / selection booleans in the
report's own output.

## 8. Event Surface

Success events:

- `scaffold_source_intake_visible_report_started`
- `scaffold_source_intake_visible_report_package_completed`
- `scaffold_source_intake_visible_report_diagnostics_completed`
- `scaffold_source_intake_visible_report_passed`

Halt event (only on package-local forbidden-language failure on
output):

- `scaffold_source_intake_visible_report_forbidden_language`

Exceptions raised by WO-57 or WO-58 are propagated verbatim; the
visible report does not catch or convert them.

## 9. Non-Echo Of Raw Source Text

The visible report:

- copies `input_prompt_observed` from the WO-57 package
  observation, which is a structural-only dict
  (`{observed: True, captured_intent_text_length: N}`);
- never echoes the raw `input_prompt` string into any of the
  visible report's top-level free-text output fields;
- copies `trace_candidate_route_fragment_count` and
  `trace_candidate_workflow_fragment_count` as integers (length of
  the embedded fragment lists);
- embeds `package_observation` and `diagnostic_report` verbatim; raw
  text already excluded by those upstream modules remains excluded.

## 10. Tests Added

`harness/tests/test_scaffold_source_intake_visible_report.py` adds
23 tests across seven `TestCase` classes covering:

- clean pass with empty inputs;
- clean pass with one inert reference and one matching bare source
  record;
- literal-False standard authorization booleans;
- `review_halt_required: False` when no halt-required diagnostics;
- `package_observation` and `diagnostic_report` embedded verbatim;
- structural-only `input_prompt_observed`; prompt text not echoed
  into top-level free-text fields;
- candidate-fragment counts copied verbatim from the package
  observation;
- the `_passed` event consistency;
- strict package -> diagnostics call order via
  `unittest.mock.patch`;
- package failure prevents diagnostics invocation;
- diagnostic failure propagates;
- `review_halt_required: True` when the diagnostic report flags
  halt-required findings, with standard authorization booleans
  still literal False;
- real-failure propagation through WO-57;
- output forbidden-language scan;
- input not mutated;
- no filesystem writes;
- only stdlib + harness-internal imports;
- module source contains no `open(`, `pathlib`, `urllib`,
  `requests`, `http.client`, `socket`, `subprocess`, `os.system`,
  `shutil`, `hashlib`, `.hexdigest`, or `.sha256` tokens;
- module source contains no `def query` / `def search` /
  `def retrieve` / `def rank` tokens;
- module source does not reference
  `run_scaffold_source_intake_trace`,
  `run_scaffold_source_intake_register`, or
  `run_scaffold_source_trace_admission_bridge` (no direct
  invocation of WO-54 / WO-55 / WO-56 public functions);
- module source contains no `copilot` / `waza` / `vscode` /
  `vs_code` / `openai` / `anthropic` / `claude_api` / `llm` tokens;
- `benchmark-fixtures/` files not mutated.

## 11. Non-Claim Constraint

The WO-47 through WO-58 explicit non-claim constraint carries
forward verbatim:

This module does not claim that any composition, report,
diagnostic, observation, or stage is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected. The report surface and the composition order are bounded
by WO-59 and are not claimed exhaustive.

The visible report records cross-stage composition only. It does
not declare any source admissible, qualified, extractable,
normalizable, fragment-derivable, route-valid, or selected for any
production system. `review_halt_required: True` is advisory
metadata only and is not a validator decision.

## 12. Forbidden Scope

WO-59 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- source download, fetch, crawl, or read;
- file read or file write inside the module;
- hash computation inside the module;
- extraction, normalization, or candidate-fragment derivation of
  its own;
- direct invocation of WO-54 / WO-55 / WO-56 public functions;
- similarity, distance, or near-match scoring of any kind;
- quality, performance, or operational metric collection;
- ranking or winner declarations;
- model judgments, fuzzy semantic analysis, thresholds, or weights;
- architecture, vendor, library, index family, ANN backend, neural
  re-scoring, retrieval family, ablation cell, multi-stage variant,
  or production system choice;
- IDE extension, editor plugin, problems-panel integration, chat-
  side surface, copilot integration, waza integration, vscode
  integration, or external collaborator-tool integration;
- prompt evaluation, skill evaluation, or agent evaluation;
- Source Card creation;
- Route Card creation;
- production artifact schema, retention, storage, immutability,
  access-control, or registration policy;
- third-party dependency;
- CLI / entry point / console script;
- subprocess / shell execution;
- mutation of any file under `benchmark-fixtures/`;
- modification of `ai-search/00-controller-checklist.md`;
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
  `harness/scaffold_source_trace_admission_bridge.py`,
  `harness/tests/test_scaffold_source_trace_admission_bridge.py`,
  `harness/scaffold_source_intake_smoke_package.py`,
  `harness/tests/test_scaffold_source_intake_smoke_package.py`,
  `harness/scaffold_route_invariant_diagnostic_reporter.py`, or
  `harness/tests/test_scaffold_route_invariant_diagnostic_reporter.py`;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Section M of that document is treated as deferred
discussion notes only, not authorization. Real-benchmark-ready
remains NO.

## 13. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_source_intake_visible_report`
  -> 23/23 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 674/674 OK after the new module and tests were added (651
  prior baseline + 23 new).
- The WO-50 through WO-58 modules and their test files are
  unchanged on disk during this Work Order.
- `ai-search/00-controller-checklist.md` is unchanged on disk
  during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.
- The module source contains no file-IO / network / hash /
  retrieval-verb / WO-54-WO-55-WO-56 invocation /
  external-integration tokens (verified by static-scan tests).

Real-benchmark-ready remains NO.

## 14. Codex Verification Result

Codex approved WO-59 after local verification. No review-time code
hardening was required.

- `python -B -m unittest harness.tests.test_scaffold_source_intake_visible_report -v`
  -> 23/23 OK.
- `python -B -m unittest discover -s harness/tests -v`
  -> 674/674 OK.

Codex also ran a concrete in-memory visible-report sample with one
`prompt_collection` source reference and one matching bare source
record. The sample returned structural prompt observation only,
linked-source count 1, candidate route/workflow fragment counts 0,
diagnostic error count 0, diagnostic halt-required count 0,
`review_halt_required: False`, and all four standard authorization /
readiness / selection booleans literal False.

This approval does not authorize real indexing, real retrieval,
source qualification, corpus admission, benchmark execution, route
selection, or architecture selection. Real-benchmark-ready remains NO.
