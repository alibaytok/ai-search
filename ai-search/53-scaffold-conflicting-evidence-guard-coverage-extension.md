# ai-search - Scaffold Conflicting-Evidence Guard Coverage Extension

Document type: Phase 4 / Phase 9 / Scaffold conflicting-evidence guard coverage extension boundary
Owner: Codex (controller)
Author: Claude (under WO-53)
Status: Implemented; pending Codex review
Work Order: WO-53

---

## 1. Purpose

WO-53 extends the WO-52 scaffold conflicting-evidence guard at
`harness/scaffold_conflicting_evidence_guard.py` with three additional
same-entry contradiction checks. The check surface, public function
signature, result-dict shape, event namespace, and halt-before-raise
pattern from WO-52 are preserved. Only the
`DECLARED_CONFLICT_KINDS` tuple, the exception classes, and the
internal per-class check helpers grow.

This is not real benchmark execution. It does not invoke a real or
mock adapter, compute similarity, score, rank, collect metrics,
choose an architecture, or change benchmark readiness.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Extend WO-52 with three more same-entry contradiction checks.
- Keep all data synthetic and already admitted.
- Keep the guard in-memory and per-call only.
- Preserve the WO-52 public surface (function signature, result-dict
  keys, event namespace, halt-before-raise pattern).
- Preserve all non-measurement / non-selection / non-readiness
  booleans as literal False.
- Not claim that the new conflict kinds, taken with the WO-52 kinds,
  are exhaustive.

The scope does not authorize a real adapter, real retrieval service,
similarity scoring, third-party dependency, benchmark run, metric
collection, architecture choice, production artifact contract, or
benchmark-readiness change.

## 3. Added And Modified Files

WO-53 modifies:

- `harness/scaffold_conflicting_evidence_guard.py` (WO-52 module
  extended in place per the WO-53 allowed-files list)
- `harness/tests/test_scaffold_conflicting_evidence_guard.py` (three
  new conflict-rejection tests appended; existing tests unchanged)

WO-53 adds:

- `ai-search/53-scaffold-conflicting-evidence-guard-coverage-extension.md`

WO-53 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 / WO-51
probe modules and their test files are not modified.

## 4. New Declared Conflict Kinds

The guard now declares eight conflict kinds. The three new kinds
added under WO-53 are:

6. **`golden_miss_with_official_route_reference`** - a golden-intents
   entry declares `expected_outcome_class: miss_expected` while also
   carrying a non-empty `expected_official_route_reference` dict.
7. **`hard_negative_candidate_only_without_candidate_or_normalized_plane`**
   - a hard-negatives entry declares `near_match_classification:
   candidate_only` but its
   `plane_separation_markers.allowed_planes` contains neither
   `candidate_route_results` nor `normalized_material_support_results`.
8. **`boundary_violation_expected_halt_without_classification`** - a
   boundary-violations entry declares
   `expected_disqualification.expected_halt: True` but does not
   declare a non-empty `halt_classification` string.

Each new conflict records an explicit halt event with the
corresponding `scaffold_conflicting_evidence_guard_*` reason string
before its named exception is raised. The named exception classes
introduced are:

- `GoldenMissWithOfficialRouteReference`
- `HardNegativeCandidateOnlyWithoutCandidateOrNormalizedPlane`
- `BoundaryViolationExpectedHaltWithoutClassification`

## 5. Preserved WO-52 Surface

The following remain unchanged from WO-52:

- The public function
  `run_scaffold_conflicting_evidence_guard(payloads_by_class,
  event_log) -> dict`.
- The nine-key clean-pass result dict shape.
- The four literal-False authorization / readiness / selection
  booleans.
- The event namespace
  (`scaffold_conflicting_evidence_guard_started`,
  `scaffold_conflicting_evidence_guard_entry_inspected`,
  `scaffold_conflicting_evidence_guard_run_ended`).
- The halt-before-raise pattern for every rejection path.
- The input-validation rejection paths (non-object payloads, missing
  class, non-object payload, class mismatch, non-list entries).
- The forbidden-language scan over payloads and output.
- The class-then-entry-order walk over
  `REQUIRED_PAYLOAD_CLASSES`.

The `inspected_entry_count` and `inspected_class_counts` keys retain
their WO-52 semantics. The `declared_conflict_kinds_checked` list now
contains eight names instead of five.

## 6. WO-31 Baseline Verification

Claude verified, by direct inspection of the admitted WO-31 fixture
entries, that none of the baseline entries triggers any of the three
new conflict kinds:

- golden-intents entry-A declares `official_route_expected` (not
  `miss_expected`); kind 6 does not apply.
- golden-intents entry-B declares `miss_expected` and does not carry
  `expected_official_route_reference`; kind 6 passes.
- hard-negatives entry-A declares `near_match_classification:
  candidate_only` and `allowed_planes` contains
  `candidate_route_results`; kind 7 passes.
- hard-negatives entry-B declares `near_match_classification:
  candidate_only` and `allowed_planes` contains
  `candidate_route_results`; kind 7 passes.
- boundary-violations entry-A and entry-B each declare
  `expected_halt: True` and a non-empty `halt_classification`
  (`"contract_check_failed"`); kind 8 passes.

The baseline payloads therefore continue to satisfy the
clean-pass observation shape.

## 7. Tests Added

`harness/tests/test_scaffold_conflicting_evidence_guard.py` adds
three tests inside the existing
`ScaffoldConflictingEvidenceGuardConflictTest` class:

- `test_golden_miss_with_official_route_reference_rejected`
- `test_hard_negative_candidate_only_without_candidate_or_normalized_plane_rejected`
- `test_boundary_violation_expected_halt_without_classification_rejected`

Each test deep-loads the WO-31 baseline payloads, introduces the
single contradiction in memory, runs the guard, and asserts both the
named exception is raised and the corresponding
`scaffold_conflicting_evidence_guard_*` halt reason is recorded.

The pre-existing 19 WO-52 tests are not modified and continue to pass
without change.

## 8. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 / WO-52 explicit non-claim
constraint carries forward verbatim:

This guard does not claim that any guard, check, conflict kind,
observation shape, or in-memory probe is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected. The eight declared conflict kinds (five from WO-52 plus
three from WO-53) are not a claim of completeness.

The guard records the absence of the eight declared conflict kinds
in the inspected entries. It does not declare the inspected entries
conflict-free, contradiction-free, or admissible as benchmark
evidence.

## 9. Forbidden Scope

WO-53 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- quality, performance, or operational metric collection;
- Stage 2 / 3 / 4 / 5 measurement scaffolding;
- scoring, ranking, or winner declarations;
- similarity, distance, or near-match scoring of any kind;
- a real retrieval adapter or real retrieval / indexing / ranking
  implementation;
- architecture, vendor, library, index family, ANN backend, neural
  re-scorer, retrieval family, ablation cell, multi-stage variant, or
  production system choice;
- production artifact schema, retention policy, storage policy,
  immutability policy, access-control policy, or registration mechanism;
- third-party dependency;
- CLI / entry point / console script;
- mutation of any file under `benchmark-fixtures/`;
- modification of `harness/scaffold_route_query_probe.py`,
  `harness/tests/test_scaffold_route_query_probe.py`,
  `harness/scaffold_route_query_ambiguity_probe.py`, or
  `harness/tests/test_scaffold_route_query_ambiguity_probe.py`;
- closure of OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate (`ai-search/00-controller-checklist.md`
Section K) continues to govern selection. Real-benchmark-ready
remains NO.

## 10. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_conflicting_evidence_guard`
  -> 22/22 OK before tracker updates (19 WO-52 tests + 3 new).
- `python -B -m unittest discover -s harness/tests`
  -> 409/409 OK after the module extension and new tests were added
  (406 prior baseline + 3 new).
- The WO-50 module `harness/scaffold_route_query_probe.py`, its
  test file, the WO-51 module
  `harness/scaffold_route_query_ambiguity_probe.py`, and its test
  file are unchanged on disk.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All touched files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.

Real-benchmark-ready remains NO.
