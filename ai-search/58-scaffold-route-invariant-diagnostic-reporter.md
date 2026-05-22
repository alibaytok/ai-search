# ai-search - Scaffold Route-Invariant Diagnostic Reporter

Document type: Phase 4 / Phase 9 / Scaffold deterministic diagnostic boundary
Owner: Codex (controller)
Author: Claude (under WO-58)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-58

---

## 1. Purpose

WO-58 adds a scaffold-only deterministic diagnostic reporter that
inspects already-loaded in-memory observation dicts from recent
scaffold layers and emits review diagnostics for ai-search contract
risks.

### What this is

- A deterministic structural inspector over already-loaded scaffold
  observation dicts.
- A producer of review-only diagnostic records.
- A consumer of WO-50 through WO-57 outputs as inert dict inputs
  only.

### What this is NOT

- **NOT Microsoft extension integration.** This module is not a VS
  Code extension, not a Microsoft Chat Customizations Evaluations
  integration, not an editor plugin, and not an IDE-side reporter.
  It borrows only the safe idea that diagnostics can be first-class
  review artifacts.
- **NOT Copilot / Waza / VS Code integration.** No IDE-side
  integration; no editor problems panel; no chat-side surface; no
  collaborator-tool integration.
- **NOT prompt evaluation, skill evaluation, or agent evaluation.**
  This module does not score prompts, skills, agents, or tools; it
  does not rank candidates; it does not select among alternatives.
- **NOT a route validator.** Diagnostics are advisory metadata; the
  reporter never flips a `validated` / `validated_route` boolean.
- **NOT source qualification.** The reporter never sets
  `qualified` / `corpus_admitted` to True; on the contrary, those
  conditions in inspected observations produce error diagnostics.
- **NOT benchmark evidence or benchmark readiness.** Diagnostics
  are not benchmark output and never flip `real_benchmark_ready`.
- **NOT architecture selection.** No architecture / vendor /
  library / index family / ANN backend / retrieval family /
  production system is selected or recommended.
- **NOT a real-benchmark-readiness flip.** Real-benchmark-ready
  remains NO.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Inspect already-loaded observation dicts deterministically.
- Emit fixed-shape diagnostic records as review evidence only.
- Preserve every reporter-output authorization / readiness /
  selection boolean as literal False, regardless of how many error
  diagnostics with `halt_required: True` are emitted.
- Halt the reporter only on malformed input or on forbidden
  language appearing on any surfaced input or output value.

The scope does not authorize real adapter invocation, real
benchmark execution, network calls, file IO, hash computation,
similarity / ranking / scoring, model judgment, fuzzy semantic
analysis, thresholds, weights, architecture / vendor / library /
index family / production system choice, subprocess execution,
external IDE / model / chat / collaborator integrations, or any
benchmark-readiness change.

## 3. Added Files

WO-58 adds:

- `harness/scaffold_route_invariant_diagnostic_reporter.py`
- `harness/tests/test_scaffold_route_invariant_diagnostic_reporter.py`
- `ai-search/58-scaffold-route-invariant-diagnostic-reporter.md`

WO-58 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 through
WO-57 modules and their test files are not modified.
`ai-search/00-controller-checklist.md` is not modified; Section M
of that document is treated as deferred discussion notes only and
is not authorization for any module behavior.

## 4. Public Function

```text
run_scaffold_route_invariant_diagnostic_reporter(observations, event_log) -> dict
```

Inputs:

- `observations`: a list (possibly empty) of already-loaded scaffold
  observation dicts. Each dict must declare a non-empty string
  `observation_kind`.
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no network call,
computes no hash, and does not invoke any other scaffold-layer
public function.

## 5. Diagnostic Categories

Each diagnostic record's `category` is exactly one of the ten:

1. `route_first_violation`
2. `source_quarantine_violation`
3. `route_status_claim`
4. `benchmark_readiness_claim`
5. `architecture_selection_claim`
6. `authorization_boolean_true`
7. `admission_or_qualification_count_nonzero`
8. `missing_literal_false_authorization_boolean`
9. `missing_non_claim_note`
10. `diagnostic_input_shape`

The set is bounded by WO-58 and is not claimed exhaustive.

## 6. Diagnostic Record Shape

Each diagnostic is a dict with exactly the eight fields:

- `diagnostic_id`
- `category` (one of the ten above)
- `severity` (one of `info`, `warning`, `error`)
- `target_observation_kind`
- `target_path`
- `invariant_ref`
- `message`
- `halt_required` (boolean)

`halt_required: True` is advisory metadata about what the caller
should do; it does NOT cause the reporter itself to raise.

## 7. Severity Mapping

- **`info`**: structural observations about scaffold-layer shape
  (missing literal-False authorization boolean fields; missing
  non-claim note; unknown `observation_kind`).
- **`warning`**: reserved for future use; the reporter does not
  currently emit warning-severity diagnostics.
- **`error` with `halt_required: True`**: any authorization /
  readiness / selection boolean literal True;
  `real_benchmark_ready: True`; `corpus_admitted_count` or
  `qualified_count` non-zero; per-entry `qualified: True` or
  `corpus_admitted: True`; any of `ROUTE_STATUS_FIELDS` present;
  any of `ARCHITECTURE_SELECTION_FIELDS` present.

## 8. Watch Sets

`ROUTE_STATUS_FIELDS` (11 names, packet-required):

`route`, `route_id`, `route_state`, `plane`, `official`,
`executable`, `selected_route`, `production_route`,
`selected_as_official`, `route_authorized`,
`official_route_authorized`.

`ARCHITECTURE_SELECTION_FIELDS` (11 names; bounded):

`architecture`, `vendor`, `library`, `index_family`, `ann_backend`,
`reranker`, `retrieval_family`, `production_system`,
`architecture_selected`, `selected_architecture`,
`architecture_choice`.

Architecture-shaped string values are also checked without echoing
the offending value into diagnostic output. The field name
`reranker` is handled by the forbidden-language halt path because it
contains the forbidden `rank` substring, so it cannot be surfaced
safely as a diagnostic target path.

## 9. Result Surface (Clean-Pass Only)

On clean pass, the reporter returns a fresh dict with exactly
thirteen allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `reporter_kind`
- `observations_checked_count`
- `diagnostics_count`
- `error_count`
- `warning_count`
- `info_count`
- `halt_required_count`
- `diagnostics` (list of diagnostic records)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `reporter_note`

The four authorization / readiness / selection booleans are
literal False on every emitted path, regardless of how many
error diagnostics with `halt_required: True` are recorded.

## 10. Event Surface

Success events:

- `scaffold_route_invariant_diagnostic_reporter_started`
- `scaffold_route_invariant_diagnostic_observed`
- `scaffold_route_invariant_diagnostic_reporter_passed`

Halt events:

- `scaffold_route_invariant_diagnostic_reporter_non_list_observations`
- `scaffold_route_invariant_diagnostic_reporter_non_object_observation`
- `scaffold_route_invariant_diagnostic_reporter_missing_observation_kind`
- `scaffold_route_invariant_diagnostic_reporter_forbidden_language`

Each halt event is recorded before the corresponding named
exception is raised.

## 11. Tests Added

`harness/tests/test_scaffold_route_invariant_diagnostic_reporter.py`
adds 42 tests across nine `TestCase` classes covering:

- empty observations list returns zero diagnostics;
- clean WO-57-like observation produces no error diagnostics;
- literal-False per-output authorization booleans (all four);
- the `_passed` event consistency;
- `reporter_note` disclaims validation / qualification / admission;
- every authorization boolean true (per scaffold layer) produces an
  error diagnostic;
- `real_benchmark_ready: True` produces a `benchmark_readiness_claim`
  diagnostic;
- `corpus_admitted_count` / `qualified_count` non-zero produces an
  `admission_or_qualification_count_nonzero` diagnostic;
- each of the 11 route-status fields individually produces a
  `route_status_claim` diagnostic plus a `route_first_violation`
  diagnostic;
- each architecture-selection field except `reranker` individually
  produces an `architecture_selection_claim` diagnostic;
- `reranker` as an input field halts through the forbidden-language
  path before returning a report;
- architecture-shaped string values produce an
  `architecture_selection_claim` diagnostic without echoing the
  offending value into output;
- per-entry `qualified: True` or `corpus_admitted: True` produces a
  `source_quarantine_violation` diagnostic;
- `extraction_authorized` / `normalization_authorized` /
  `candidate_derivation_authorized` literal True produces an
  authorization diagnostic;
- diagnostic shape compliance (exact eight fields per record;
  severity in `{info, warning, error}`; category in the bounded
  10);
- unknown `observation_kind` produces an info `diagnostic_input_shape`
  diagnostic;
- non-list observations / non-dict observation /
  missing-`observation_kind` halt before raising;
- forbidden language in input observation halts before raising;
- output forbidden-language scan;
- input not mutated;
- no filesystem writes;
- only stdlib + harness-internal imports;
- module source contains no `open(`, `pathlib`, `urllib`,
  `requests`, `http.client`, `socket`, `subprocess`, `os.system`,
  `shutil`, `hashlib`, `.hexdigest`, or `.sha256` tokens;
- module source contains no `def query` / `def search` /
  `def retrieve` / `def rank` tokens;
- module source does not reference `run_scaffold_source_intake_trace`,
  `run_scaffold_source_intake_register`,
  `run_scaffold_source_trace_admission_bridge`, or
  `run_scaffold_source_intake_smoke_package` (no WO-54 through
  WO-57 invocation);
- module source contains no external-integration tokens
  (`copilot`, `waza`, `vscode`, `vs_code`, `openai`, `anthropic`,
  `claude_api`);
- `benchmark-fixtures/` files not mutated;
- constants admissibility (13 output keys; 10 categories; 3
  severities; route-status field list contains all 11 packet-
  required markers).

## 12. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 / WO-53 / WO-54 /
WO-55 / WO-56 / WO-57 explicit non-claim constraint carries
forward verbatim:

This module does not claim that any diagnostic, category, severity,
or invariant reference is sufficient, necessary, superior, best,
complete, production-ready, recommended, or selected. The
diagnostic categories, watch sets, and recognized scaffold-layer
observation kinds are bounded by WO-58 and are not claimed
exhaustive. Diagnostics are review evidence only; they do not
validate routes, qualify sources, admit corpus, authorize
extraction, authorize normalization, authorize candidate
derivation, authorize measurement, authorize benchmark execution,
prove benchmark readiness, select architecture, select route /
workflow / candidate, or promote anything to official.

## 13. Forbidden Scope

WO-58 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- file read or file write inside the module;
- hash computation inside the module;
- extraction, normalization, or candidate-fragment derivation;
- similarity, distance, near-match, or scoring of any kind;
- ranking or winner declarations;
- model judgments or fuzzy semantic analysis;
- thresholds or weights;
- architecture, vendor, library, index family, ANN backend,
  retrieval family, ablation cell, multi-stage variant, or
  production system choice;
- IDE extension, editor plugin, problems-panel integration, chat-side
  surface, copilot integration, waza integration, vscode integration,
  or external collaborator-tool integration;
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
  `harness/scaffold_source_intake_smoke_package.py`, or
  `harness/tests/test_scaffold_source_intake_smoke_package.py`;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Section M of that document is treated as
deferred discussion notes only, not authorization. Real-benchmark-
ready remains NO.

## 14. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_route_invariant_diagnostic_reporter`
  -> 42/42 OK after Codex review-time hardening.
- `python -B -m unittest discover -s harness/tests`
  -> 651/651 OK after Codex review-time hardening (609 prior
  baseline + 42 WO-58 tests).
- The WO-50 through WO-57 modules and their test files are
  unchanged on disk during this Work Order.
- `ai-search/00-controller-checklist.md` is unchanged on disk
  during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.
- The module source has been statically inspected (via tests) for
  the absence of file-IO / network / hash / retrieval-verb /
  WO-54-through-WO-57 invocation / external-integration tokens; no
  such tokens are present.

Real-benchmark-ready remains NO.

## 15. Codex Review-Time Hardening

Codex found two WO-58 watch-surface gaps during final verification:

- `reranker` was omitted from the architecture-selection watch set
  because it contains the forbidden `rank` substring.
- Architecture-shaped string values were not checked, only field
  names.

Hardening applied:

- Added `reranker` to `ARCHITECTURE_SELECTION_FIELDS`.
- Added a regression test proving `reranker` as an input field halts
  through forbidden-language handling before a report is returned.
- Added detection for architecture-shaped string values without
  echoing the offending value into diagnostic output.
- Added a regression test for architecture-shaped string values.

Codex verified:

- `python -B -m unittest harness.tests.test_scaffold_route_invariant_diagnostic_reporter -v`
  -> 42/42 OK.
- `python -B -m unittest discover -s harness/tests -v`
  -> 651/651 OK.

This hardening does not authorize source qualification, corpus
admission, route validation, benchmark execution, or architecture
selection. Real-benchmark-ready remains NO.
