# ai-search - Scaffold Index Probe Coverage Extension

Document type: Phase 4 / Phase 9 / Scaffold indexing-logic probe coverage boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes after Codex review
Work Order: WO-48

---

## 1. Purpose

This document records the WO-48 (DC-048) coverage extension to the
WO-47 scaffold indexing-logic probe at
`harness/scaffold_index_probe.py`. WO-48 adds a new test file at
`harness/tests/test_scaffold_index_probe_coverage.py` containing
seven `TestCase` classes and twelve test methods that exercise
route-first behavior, plane separation evidence, miss handling,
candidate-vs-official separation, boundary-violation handling, and
event / output evidence consistency.

WO-48 does NOT modify the probe module. It does NOT perform real
benchmark execution, does NOT invoke any real or mock adapter, does
NOT collect quality / performance metrics, does NOT score, does
NOT rank, and does NOT select any architecture / vendor / library /
index family / ANN backend / neural re-scorer / retrieval family /
ablation cell / multi-stage variant / production system. OQ-035,
OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 all remain OPEN.
RK-039 continues to apply unchanged. **Real-benchmark-ready remains
NO.**

The WO-47 explicit non-claim constraint added under Codex's
review-time hardening (the constraint that no surface may claim an
indexing approach / index architecture / retrieval family / layer /
constraint strategy / in-memory probe is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected) is preserved verbatim under WO-48. No test docstring,
class name, or method name in the new test file asserts the probe
is any of those things.

## 2. Why A Coverage Extension Is Needed

WO-47 close (Codex-approved with notes) recorded 28 tests across
seven `TestCase` classes covering per-class behavior, rejection
paths, language hygiene, isolation, import surface, and
`benchmark-fixtures/` no-mutation. Coverage gaps existed for
route-first evidence properties that the probe module already
implements but that the WO-47 tests did not assert directly:

- Output-dict counts vs. per-event-type counts in the event log:
  not directly asserted.
- The `normalized` observation kind: never exercised by the WO-31
  wave because both WO-31 hard-negative entries include
  `candidate_route_results` in `allowed_planes`, so the dispatcher
  preference resolves to `candidate` for both.
- The empty-`allowed_planes` fallback path for hard-negatives:
  exists in the dispatcher (per the probe module docstring) but
  was untested.
- Per-entry observation event ordering: the probe iterates classes
  in `REQUIRED_PAYLOAD_CLASSES` order and entries in input order;
  the invariant was not asserted.
- Cross-class identity integrity: each event's `class_name` must
  pair correctly with its `fixture_id`; no cross-leakage was
  asserted.
- `forbidden_plane_collapse` field preserved on contract-failure
  observations: accessed in WO-47 tests but not explicitly
  asserted against the source entry's field value.
- Idempotency under deep-copied identical inputs: not asserted.

WO-48 fills these seven gaps using only new tests. No probe-module
change. No metric. No measurement authorization.

## 3. Scope

WO-48 is bounded to:

- Add `harness/tests/test_scaffold_index_probe_coverage.py` (new
  test module).
- Add `ai-search/48-scaffold-index-probe-coverage-extension.md`
  (this document).
- Append DC-048 to `ai-search/00-open-questions.md`.
- Append the WO-48 ledger entry to
  `ai-search/00-claude-task-ledger.md`.

WO-48 is forbidden from:

- Modifying `harness/scaffold_index_probe.py`.
- Modifying `harness/tests/test_scaffold_index_probe.py`.
- Modifying any other existing harness module or test.
- Mutating any file under `benchmark-fixtures/`.
- Adding any third-party dependency.
- Authoring Stage 2 / 3 / 4 / 5 measurement scaffolding.
- Authoring a real or mock adapter call surface.
- Authoring a metric, score, ranking, winner declaration, or any
  configuration choice.
- Producing any production artifact, retention / storage policy,
  registration mechanism, or access-control policy.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.

## 4. Coverage Added

The new test file contains seven `TestCase` classes and twelve
test methods:

### 4.1 `EventCountConsistencyTest` (3 tests)

- The output dict's five per-kind observation counts each equal
  the count of the corresponding event type in the event log.
- The output dict's `entries_indexed_count` equals the total
  number of per-entry observation events emitted.
- The `scaffold_index_probe_run_ended` event carries
  `entries_indexed_count` and the five per-kind counts that match
  the returned output dict's same-named fields.

### 4.2 `HardNegativeNormalizedFallbackTest` (1 test)

Constructs an in-memory hard-negative payload whose
`allowed_planes` contains only
`normalized_material_support_results` (excluding
`candidate_route_results`). Asserts the probe emits a
`scaffold_index_probe_normalized_observation` event on the
normalized plane and increments
`normalized_observation_count`. Confirms the `normalized`
observation-kind code path executes (the WO-31 wave does not
exercise it).

### 4.3 `HardNegativeEmptyAllowedPlanesFallbackTest` (2 tests)

Constructs an in-memory hard-negative payload with
`allowed_planes: []`. Asserts the probe falls back to the
candidate plane and emits a
`scaffold_index_probe_candidate_observation` event with
`plane == "candidate_route_results"`. Also asserts the official
plane is never chosen under this fallback path.

### 4.4 `EntryOrderPreservationTest` (2 tests)

- The class-order of per-entry observation events matches
  `REQUIRED_PAYLOAD_CLASSES` order (each class contributes its
  entries as a contiguous block).
- Within each class, the per-entry observation events appear in
  the input list order.

### 4.5 `CrossClassIdentityIntegrityTest` (1 test)

For every per-entry observation event in the log, the recorded
`class_name` matches the source class of the entry whose
`fixture_id` the event carries. No cross-class leakage.

### 4.6 `ForbiddenPlaneCollapseFieldPreservedTest` (1 test)

For every boundary-violations entry, the contract-failure
observation event's `observation["forbidden_plane_collapse"]`
equals the source entry's
`plane_separation_markers["forbidden_plane_collapse"]`. Plane
separation evidence is preserved at the observation surface.

### 4.7 `ProbeIdempotencyTest` (2 tests)

- Two consecutive invocations of the probe with deep-copied
  identical input dicts produce equal output dicts (output dict
  equality includes all twelve allowed output keys).
- The per-entry observation events from two consecutive
  invocations carry identical `(type, class_name, fixture_id,
  observation)` tuples.

## 5. Non-Claim Constraint Application

The WO-47 explicit non-claim constraint (introduced as Section
10.1 of `ai-search/47-scaffold-indexing-logic-probe.md` after
Codex review) is preserved verbatim under WO-48:

> The probe may test route-first indexing behavior, but it must not
> claim an indexing approach, index architecture, retrieval family,
> layer, constraint strategy, or in-memory probe is sufficient,
> necessary, superior, best, complete, production-ready,
> recommended, or selected.

The constraint applies at every WO-48 surface:

- The new test module's docstring records the constraint and
  references the WO-47 / WO-48 boundary.
- Test class names and test method names contain none of the
  forbidden affirmative claim words.
- Test assertion messages contain none of the forbidden claim
  words applied to the probe.
- The boundary document (this file), the DC-048 tracker row, and
  the WO-48 ledger entry contain only meta-language and
  negations of the forbidden claims (listing what the document
  refuses to assert, or asserting the probe is NOT something).
  Meta-language and negations do not violate the constraint;
  they enforce it.

The new test file's docstring contains a single direct
acknowledgment of the constraint and the words it forbids, in the
same meta-language style as `ai-search/47-...md` Section 10.1.

## 6. What Is Not Changed Under WO-48

- `harness/scaffold_index_probe.py` is byte-identical to its
  WO-47-close state. No code-path change. No new function. No new
  exception. No new module-level constant.
- `harness/tests/test_scaffold_index_probe.py` is byte-identical
  to its WO-47-close state. The Codex review-time `test_forbidden_language_in_event_surface_rejected` addition under WO-47
  is preserved.
- Every other harness implementation module is byte-identical to
  its WO-47-close state.
- Every other test file under `harness/tests/` is byte-identical.
- Every file under `benchmark-fixtures/` is byte-identical (SHA-256
  unchanged from the WO-31 baseline).
- The WO-39 / WO-40 readiness gate states are unchanged:
  scaffold-ready YES, artifact-ready YES, review-summary-ready
  YES, real-benchmark-ready NO. Real-benchmark-ready remains NO.

## 7. Forbidden Scope (WO-48)

WO-48 is forbidden from doing any of the following:

- Modifying `harness/scaffold_index_probe.py` or any other harness
  implementation module.
- Modifying `harness/tests/test_scaffold_index_probe.py` or any
  other existing test file.
- Mutating any file under `benchmark-fixtures/<class>/`, any
  `.gitkeep`, or `benchmark-fixtures/README.md`.
- Invoking any real or mock adapter.
- Performing real benchmark execution.
- Collecting quality / performance / operational metrics.
- Scoring, ranking, or declaring any configuration a winner /
  best / production-ready / recommended.
- Authoring Stage 2 / 3 / 4 / 5 measurement scaffolding.
- Authoring a production manifest schema, contract, retention
  policy, storage policy, immutability policy, access-control
  policy, or registration mechanism.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding any third-party dependency.
- Introducing a CLI, an entry point, a console script, or any
  shell wrapper.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076. All seven remain OPEN.
- Duplicating RK-039.
- Asserting (in any test, doc, or tracker text) that the probe or
  any indexing approach is sufficient, necessary, superior, best,
  complete, production-ready, recommended, or selected.

## 8. Out Of Scope

The following remain out of scope for WO-48 and require separate
Codex-authored Work Orders:

- Real benchmark execution.
- Stage 2 / 3 / 4 / 5 measurement scaffolding.
- Real candidate retrieval adapter authoring.
- Real fixture admission / ownership process (OQ-035, OQ-049).
- Production artifact schema or contract (OQ-076).
- Retention / storage / immutability / access-control policy
  (OQ-056).
- Production registration mechanism (OQ-057).
- Architecture / vendor / library / index family / ANN backend /
  neural re-scorer / retrieval family / ablation cell / multi-stage
  selection.
- CLI, entry point, console script, or shell wrapper.
- Dependency policy beyond the first scaffold (OQ-075).
- Broader scope process (OQ-070).
- Any change to the probe module's behavior, output shape, event
  ordering, or rejection list.
- Any modification of the WO-47 boundary document.
- Any new payload file under `benchmark-fixtures/`.
