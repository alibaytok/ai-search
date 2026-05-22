# ai-search - Scaffold Conflicting-Evidence Guard

Document type: Phase 4 / Phase 9 / Scaffold conflicting-evidence guard boundary
Owner: Codex (controller)
Author: Claude (under WO-52)
Status: Approved after Codex verification
Work Order: WO-52

---

## 1. Purpose

WO-52 adds the first scaffold-level guard that inspects already-loaded
synthetic fixture entries for declared structural contradictions
BEFORE any route-query observation is performed. The guard models the
"contradictory evidence inside one entry" failure case that the
WO-47 / WO-48 / WO-50 / WO-51 observation paths assume away by
construction.

This is not real benchmark execution. It does not invoke a real or
mock adapter, compute similarity, score, rank, collect metrics,
choose an architecture, or change benchmark readiness.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Detect same-entry contradictions in admitted WO-31 synthetic
  fixture entries.
- Keep all data synthetic and already admitted.
- Keep the guard in-memory and per-call only.
- Preserve plane separation and route-first behavior from WO-47 /
  WO-48 / WO-50 / WO-51.
- Preserve all non-measurement / non-selection / non-readiness
  booleans as literal False.
- Bound the guard to the five declared conflict kinds listed below.
- Not claim that the five declared kinds are exhaustive.

The scope does not authorize a real adapter, real retrieval service,
similarity scoring, third-party dependency, benchmark run, metric
collection, architecture choice, production artifact contract, or
benchmark-readiness change.

## 3. Added Files

WO-52 adds:

- `harness/scaffold_conflicting_evidence_guard.py`
- `harness/tests/test_scaffold_conflicting_evidence_guard.py`
- `ai-search/52-scaffold-conflicting-evidence-guard.md`

WO-52 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 / WO-51
probe modules and their test files are not modified.

## 4. Public Function

The new public function is:

```text
run_scaffold_conflicting_evidence_guard(payloads_by_class, event_log) -> dict
```

Inputs:

- `payloads_by_class`: already-loaded dicts for the three admitted
  WO-31 classes.
- `event_log`: harness `EventLog`.

The function reads no file and writes no file.

## 5. Declared Conflict Kinds

The guard halts and raises on the first occurrence of any of the
following same-entry contradictions. The five declared kinds are not
a claim of completeness; future Codex packets may extend the list.

1. **`golden_official_with_expected_halt`** - a golden-intents entry
   declares `expected_outcome_class: official_route_expected` and
   also carries `expected_disqualification.expected_halt: True`.
2. **`golden_official_reference_with_miss_classification`** - a
   golden-intents entry declares an
   `expected_official_route_reference` (a non-empty dict) and also
   declares `miss_classification` (a non-empty string).
3. **`hard_negative_allows_official_despite_guard`** - a
   hard-negatives entry declares
   `must_not_authorize_official_return: True` and also carries
   `plane_separation_markers.allowed_planes` containing
   `official_route_results`.
4. **`boundary_violation_both_valid_and_forbidden`** - a
   boundary-violations entry declares both
   `expected_disqualification.is_forbidden_output: True` and
   `expected_disqualification.is_valid_output: True`.
5. **`boundary_violation_official_plane_without_collapse`** - a
   boundary-violations entry declares
   `plane_separation_markers.violation_plane_in_observed_output:
   "official_route_results"` but does not declare a non-empty
   `forbidden_plane_collapse` marker.

Each conflict records an explicit halt event with a
`scaffold_conflicting_evidence_guard_*` reason string before the
corresponding exception is raised.

## 6. Input Validation

The guard rejects, with an explicit halt event before raising:

- `payloads_by_class` is not a dict.
- A required admitted payload class is missing.
- A per-class payload is not a dict, mismatches its `fixture_class`,
  or has missing or non-list entries.
- A surfaced string in the payloads or in the output contains a
  forbidden phrase.

## 7. Result Surface (Clean-Pass Only)

On clean pass, the guard returns a fresh dict with exactly nine
allowed keys:

- `guard_kind`
- `inspected_entry_count`
- `inspected_class_counts`
- `declared_conflict_kinds_checked`
- `selection_made`
- `measurement_authorized`
- `real_benchmark_authorized`
- `real_benchmark_ready`
- `guard_note`

The four authorization / readiness / selection booleans are literal
False on every emitted path. The `guard_note` explicitly states that
passing this guard is not a claim that the inspected entries are
conflict-free; only that the five declared conflict kinds were not
observed.

## 8. Event Surface

Success events:

- `scaffold_conflicting_evidence_guard_started`
- `scaffold_conflicting_evidence_guard_entry_inspected`
- `scaffold_conflicting_evidence_guard_run_ended`

Rejection events are explicit halt events with
`scaffold_conflicting_evidence_guard_*` reason strings. Halt events
are recorded before the corresponding exception is raised.

## 9. Tests Added

`harness/tests/test_scaffold_conflicting_evidence_guard.py` adds 19
tests across eight `TestCase` classes:

- baseline payloads pass with expected observation shape;
- literal-False authorization / readiness / selection booleans;
- run-ended event records the expected declared conflict kinds;
- per-entry inspected events appear in class-order then entry-order;
- each of the five declared conflict kinds is rejected with the
  correct halt reason;
- non-object payloads, missing required class, payload class
  mismatch, and non-list entries are rejected;
- output has no forbidden language;
- forbidden payload string is rejected without leaking the source
  text;
- inputs are not mutated;
- no filesystem writes are performed;
- imports are stdlib + harness-internal only;
- `benchmark-fixtures/` files are not mutated.

## 10. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 / WO-51 explicit non-claim
constraint carries forward verbatim:

This guard does not claim that any guard, check, conflict kind,
observation shape, or in-memory probe is sufficient, necessary,
superior, best, complete, production-ready, recommended, or selected.

The guard records the absence of the five declared conflict kinds in
the inspected entries. It does not declare the inspected entries
conflict-free, contradiction-free, or admissible as benchmark
evidence.

## 11. Forbidden Scope

WO-52 does not authorize:

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
- modification of `harness/scaffold_route_query_probe.py` or
  `harness/scaffold_route_query_ambiguity_probe.py` or their test
  files;
- closure of OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate (`ai-search/00-controller-checklist.md`
Section K) continues to govern selection. Real-benchmark-ready
remains NO.

## 12. Verification Result

Claude verified before submitting this entry. Codex verified after
review against the authoritative five-conflict WO-52 prompt:

- `python -B -m unittest harness.tests.test_scaffold_conflicting_evidence_guard`
  -> 19/19 OK.
- `python -B -m unittest discover -s harness/tests`
  -> 406/406 OK after WO-52 (387 prior baseline + 19 WO-52 tests).
- The WO-50 and WO-51 probe modules and their test files are
  unchanged on disk.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.

Real-benchmark-ready remains NO.
