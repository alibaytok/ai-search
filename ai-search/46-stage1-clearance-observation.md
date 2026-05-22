# ai-search - Stage 1 Clearance Observation Scaffold

Document type: Phase 4 / Phase 9 / Stage 1 clearance observation scaffold boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-46

---

## 1. Purpose

This document records the scaffold-internal Stage 1 clearance
observation module authorized under WO-46 (DC-046) at
`harness/stage1_clearance_observation.py`. The module accepts an
already-loaded WO-45 Stage 1 contract-safety result dict and emits
a fresh fixed-shape Stage 1 clearance observation dict ONLY when
Stage 1 passed and all authorization booleans remained False.

The module is the smallest useful bridge artifact between WO-45
Stage 1 contract-safety and a future Stage 2 packet. It is
pre-measurement only. It does not invoke a real adapter, does not
run a real benchmark, does not collect quality / performance
metrics, does not score, does not rank, and does not select any
architecture / vendor / library / index family / ANN backend /
neural re-scorer / retrieval family / ablation cell / multi-stage
variant / production system. OQ-035, OQ-049, OQ-056, OQ-057,
OQ-070, OQ-075, and OQ-076 all remain OPEN. RK-039 continues to
apply unchanged. Real-benchmark-ready remains NO.

The WO-46 packet preamble required application of
`ai-search/00-controller-checklist.md` Section L (Mutual Alignment
Protocol / Shared Scope Verification) before implementation. The
Section L scope quiz was performed and recorded in the WO-46 ledger
entry under "Pre-Implementation Review."

## 2. Relationship To WO-45

WO-45 produced the Stage 1 contract-safety pass at
`harness/stage1_contract_safety.py` (DC-045). WO-46 consumes its
output:

- The Stage 1 result dict (the dict returned by
  `harness.stage1_contract_safety.run_stage1_contract_safety(...)`)
  is the Stage 1 clearance observation input.
- The clearance module re-validates the eight documented
  constraints on the result dict before emitting an observation.
  Re-validation is a tamper-check; the WO-45 module guarantees a
  well-formed output on its successful paths, and the clearance
  module additionally guarantees that a tampered or forged result
  cannot leak through into a downstream "Stage 1 cleared" claim.
- Per the WO-46 packet preamble, the clearance module does NOT
  call `harness.stage1_contract_safety.run_stage1_contract_safety(...)`
  or any other WO-43 / WO-44 / WO-45 module. It imports only the
  canonical forbidden-language lists from `harness.review_package`
  and `harness.payload_loader`. This keeps the clearance
  observation structurally separate from the upstream Stage 1
  module so a tamper of the WO-45 module cannot silently leak
  through.

## 3. Input Contract

The function accepts two arguments:

```
record_stage1_clearance_observation(stage1_result, event_log) -> dict
```

- `stage1_result`: an already-loaded dict. The module enforces the
  following constraints in this order; the first violation raises
  the matching named exception after an explicit halt event is
  recorded:

  1. Top-level value is a dict.
  2. `result_kind == "stage1_contract_safety_result"`.
  3. `stage1_passed is True`.
  4. `contract_safety_status == "passed"`.
  5. `checks_failed_count == 0`.
  6. `failed_check_names == []`.
  7. `measurement_authorized is False`.
  8. `real_benchmark_authorized is False`.
  9. `selection_made is False`.
  10. No phrase from
      `harness.review_package.FORBIDDEN_PHRASES`, the local
      `"score"` / `"scoring"` extension, or
      `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES` appears in
      any surfaced string field (`candidate_adapter_id`,
      `configuration_id`, `fixture_set_id`, or any entry in
      `failed_check_names`).

- `event_log`: a `harness.event_log.EventLog` instance.

The module does NOT read files and does NOT write files. The input
dict is not modified.

## 4. Output Contract

On success the function returns a fresh dict with exactly the ten
allowed top-level keys (`ALLOWED_OBSERVATION_KEYS`):

- `observation_kind`: literal string `"stage1_clearance_observation"`.
- `stage1_cleared`: literal `True`. The clearance observation is
  emitted only when Stage 1 cleared; failed Stage 1 results are
  rejected before the dict is assembled.
- `candidate_adapter_id`: pass-through from the Stage 1 result.
- `configuration_id`: pass-through from the Stage 1 result.
- `fixture_set_id`: pass-through from the Stage 1 result.
- `checks_passed_count`: pass-through from the Stage 1 result.
- `selection_made`: literal `False`. The clearance observation
  does not constitute selection.
- `measurement_authorized`: literal `False`. Stage 1 clearance is
  not authorization to measure; it is a pre-measurement bridge
  marker.
- `real_benchmark_authorized`: literal `False`. Stage 1 clearance
  is not authorization for real benchmark execution.
- `observation_note`: literal observation-only string referencing
  this document and the Indexing Excellence Gate.

No additional top-level key is emitted. No per-record substantive
content beyond the four pass-through identifier / count fields is
propagated.

## 5. Event And Halt Behavior

Success event recorded into `event_log`:

- `stage1_clearance_observation_recorded` with
  `candidate_adapter_id`, `configuration_id`, `fixture_set_id`, and
  `checks_passed_count`.

Halt event reasons recorded before each rejection raises:

- `stage1_clearance_non_object` (non-dict input).
- `stage1_clearance_invalid_result_kind` (wrong `result_kind`).
- `stage1_clearance_not_passed` (with `reason_detail` of either
  `"stage1_passed_not_true"` or `"contract_safety_status_not_passed"`).
- `stage1_clearance_failed_checks_present` (with `reason_detail` of
  either `"checks_failed_count_nonzero"` or
  `"failed_check_names_nonempty"`).
- `stage1_clearance_authorizes_measurement` (`measurement_authorized`
  not False).
- `stage1_clearance_authorizes_real_benchmark`
  (`real_benchmark_authorized` not False).
- `stage1_clearance_declares_selection` (`selection_made` not False).
- `stage1_clearance_forbidden_language` (with `surface_field` and
  `forbidden_phrase`).

The halt-and-raise behavior matches the WO-19 / DC-022 halt
boundary: every rejection records an explicit halt event before
the matching named exception is raised. The halt is observable to
the caller via `event_log.events` regardless of whether the caller
catches the exception or lets it propagate.

## 6. Non-Measurement Guarantee

The Stage 1 clearance observation does not authorize measurement
under any path:

- Success path: `measurement_authorized: False` and
  `real_benchmark_authorized: False` are literal constants in the
  output dict. Stage 1 clearance is a structural marker that the
  upstream Stage 1 contract-safety passed; it is not authorization
  for measurement, real benchmark execution, or any quality /
  performance / operational signal collection.
- Rejection path: the function raises before any observation dict
  is returned. No `measurement_authorized: True` is ever emitted.
- Pre-condition check: the function rejects any Stage 1 result
  that already declared `measurement_authorized is True` or
  `real_benchmark_authorized is True`. This catches a tampered
  upstream result that attempted to declare measurement
  authorization itself.

This matches the WO-19 / DC-022 halt-before-measurement invariant
ratified at WO-36 review and carried forward through WO-43 / WO-44
and WO-45. The scaffold extends the invariant forward at every
new layer: no scaffold output can be silently upgraded to
"measurement authorized" by reading habit, because the boolean is
fixed at literal `False` in every emitted dict.

A future real-adapter or real-measurement Codex packet must
explicitly relax this rule and must record the relaxation in a new
DC-XXX tracker row. The current scaffold cannot drift into
authorizing measurement.

## 7. Non-Selection Guarantee

The Stage 1 clearance observation does not select any architecture,
vendor, library, index family, ANN backend, neural re-scorer,
retrieval family, ablation cell, multi-stage variant, or production
system:

- The output `selection_made` is literal `False` on every path.
- A Stage 1 result with `selection_made is True` is rejected
  before any observation is assembled (raises
  `Stage1DeclaresSelection`).
- The Indexing Excellence Gate (`00-controller-checklist.md`
  Section K) continues to govern selection unconditionally. "Best
  not proven = not selected" remains canonical.
- No aggregate score, no count, no boolean produced by the
  scaffold may select a winner by itself.
- The clearance observation_note references the Indexing
  Excellence Gate explicitly.

## 8. What Remains Unresolved

WO-46 does not resolve:

- Stage 2 quality measurement scaffolding.
- Stage 3 performance measurement scaffolding.
- Stage 4 operational measurement scaffolding.
- Stage 5 Human Architecture Review Package scaffolding.
- Real candidate retrieval adapter authoring. The clearance
  observation is a pre-measurement structural marker; it provides
  no real adapter response handling.
- Real fixture admission / ownership process (OQ-035 OPEN,
  OQ-049 OPEN).
- Real metric policy or scoring protocol.
- Real benchmark execution.
- Artifact retention / storage / immutability / access-control
  policy (OQ-056 OPEN).
- Production artifact contract (OQ-076 OPEN).
- Configuration registration authority (OQ-057 OPEN).
- Dependency policy beyond the first scaffold (OQ-075 OPEN).
- Broader scope process (OQ-070 OPEN).
- Architecture / vendor / library / index family / ANN backend /
  neural re-scorer / retrieval family / ablation cell / multi-stage
  variant / production-system selection.
- The `"score"` / `"scoring"` forbidden-language consolidation
  flagged by Codex at WO-39 / WO-40 review. WO-46 mirrors the
  local extension pattern at module scope (matching the WO-45
  post-Codex-hardening pattern in `harness/stage1_contract_safety.py`);
  a future Codex packet may consolidate into
  `harness/review_package.py`.

The WO-39 / WO-40 readiness gate states are unchanged by WO-46:

| Gate | State |
|------|-------|
| scaffold-ready | YES |
| artifact-ready | YES |
| review-summary-ready | YES |
| real-benchmark-ready | NO |

WO-46 is a small pre-measurement bridge. It discharges no
WO-39 / WO-40 blocker fully; it adds a structural connector
between the Stage 0 / Stage 1 scaffold already in place and the
future Stage 2 scaffold that has not yet been authorized.

## 9. Forbidden Scope

WO-46 is forbidden from doing any of the following:

- Modifying any existing harness implementation module. The one
  allowed new module is `harness/stage1_clearance_observation.py`.
- Modifying any existing test file under `harness/tests/`.
- Modifying any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Calling any WO-43 / WO-44 or WO-45 module from the new
  clearance observation module. The clearance module imports only
  canonical forbidden-language lists.
- Invoking any real adapter behavior.
- Performing real benchmark execution.
- Collecting real quality / performance / operational metrics.
- Authoring any Stage 2 / 3 / 4 / 5 scaffolding.
- Scoring, ranking, or declaring any configuration a winner /
  best / production-ready / recommended.
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
- Consolidating the `"score"` / `"scoring"` forbidden-language
  extension into `harness/review_package.py` (that file is outside
  the allowed-files list).
- Mutating corpus docs, route registry docs, validation evidence,
  source quality graph, intent trace store, candidate routes, or
  official routes.

## 10. Out Of Scope

The following remain explicitly out of scope for WO-46 and require
separate Codex-authored Work Orders whose scope, allowed files,
required content, forbidden scope, acceptance criteria, and
evidence requirements are explicit at issue time:

- Real benchmark execution.
- Stage 2 / 3 / 4 measurement scaffolding (quality, performance,
  operational).
- Stage 5 Human Architecture Review Package scaffolding.
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
- Wiring
  `harness.contract_runner.ContractRunner.record_measurement(...)`
  into `harness.dry_run.run_toy_dry_run(...)`.
- Wiring real adapter responses into Stage 1 or Stage 1 clearance.
  The current scaffold operates on observation / result dicts
  only.
- Aggregation of multiple Stage 1 clearance observations across
  multiple candidate adapters. The current scaffold processes one
  Stage 1 result per call.
- Consolidating the `"score"` / `"scoring"` forbidden-language
  extension into the canonical
  `harness.review_package.FORBIDDEN_PHRASES`.
