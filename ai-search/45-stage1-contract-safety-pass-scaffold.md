# ai-search - Stage 1 Contract-Safety Pass Scaffold

Document type: Phase 4 / Phase 9 / Stage 1 contract-safety scaffold boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes after Codex review
Work Order: WO-45

---

## 1. Purpose

This document records the scaffold-internal Stage 1 contract-safety
pass authorized under WO-45 (DC-045) at
`harness/stage1_contract_safety.py`. The module runs a fixed-shape
contract-safety pass over the WO-43 / WO-44 Stage 0 readiness output
and the already-loaded scaffold fixture admission and candidate
adapter records.

The scaffold is pre-measurement only. It does not invoke a real
adapter, does not run a real benchmark, does not collect quality /
performance metrics, and does not select any architecture / vendor /
library / index family / ANN backend / neural re-scorer / retrieval
family / ablation cell / multi-stage variant / production system.
OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, and OQ-076 all
remain OPEN. RK-039 continues to apply unchanged.

**Scope note (carried forward into Section 11):** WO-45 Stage 1 is a
scaffold approximation of WO-12R `ai-search/14-benchmark-execution-plan.md`
Section 6 (real Stage 1 contract violation pass). Real Stage 1
would run contract violation tests against actual adapter responses
produced by a real adapter call (per
`ai-search/13-retrieval-benchmark-framework.md` Section 8). The
WO-45 module operates ONLY on a scaffold observation dict derived
from the Stage 0 readiness; when real adapter integration arrives,
the Stage 1 module must be extended (or paired with a sibling
module) to consume real responses. WO-45 does not author that
extension.

## 2. Relationship To WO-43 / WO-44

WO-43 / WO-44 produced the Stage 0 readiness review and the
candidate adapter admission contract. WO-45 consumes both:

- The Stage 0 readiness dict (output of
  `harness.readiness_review.review_stage0_readiness(...)`) is the
  Stage 1 input. The Stage 1 module re-validates the literal False
  authorization booleans (`measurement_authorized`,
  `real_benchmark_authorized`, `selection_made`) and the literal
  `True` value of `stage0_ready`, and rejects any tampered readiness
  dict before any contract check runs.
- The fixture admission record and the candidate adapter record
  (the same dicts the Stage 0 reviewer validated upstream) are the
  Stage 1 secondary inputs. The Stage 1 module performs a tamper
  check on the four scaffold-only booleans (`real_benchmark_data`,
  `real_adapter`, `production_registration`, `selection_made`); it
  does not re-run the full WO-43 / WO-44 validators.

The Stage 1 module imports only canonical forbidden-language lists
and does NOT call any WO-43 / WO-44 module directly. This keeps
WO-45 a pure tamper-check + check-runner; the full WO-43 / WO-44
admission contracts remain the responsibility of upstream callers.

## 3. Stage 1 Contract-Safety Boundary

The Stage 1 module lives at `harness/stage1_contract_safety.py` and
exposes one public function:

```
run_stage1_contract_safety(stage0_readiness,
                           fixture_admission_record,
                           candidate_adapter_record,
                           contract_checks,
                           event_log) -> dict
```

Behavior:

- Accepts already-loaded dicts only. Does not read files. Does not
  write files.
- Does not invoke any real adapter.
- Does not record any measurement event.
- Validates the Stage 0 readiness, the two records, and the
  contract-check list (halt before raising on every rejection).
- Builds a fixed-shape observation dict (Section 5) from the Stage 0
  readiness.
- Runs each contract check in list order against a fresh copy of
  the observation dict.
- Records one `stage1_contract_check_passed` event per pass; one
  `stage1_contract_check_failed` event on first failure followed by
  a halt event `stage1_contract_safety_failed`; no later checks
  run after first failure.
- Records `stage1_contract_safety_passed` on full success.
- Returns a dict with exactly the fourteen `ALLOWED_RESULT_KEYS`
  (Section 6).

The function does not invoke `run_toy_dry_run(...)`, does not
invoke `run_payload_batch(...)`, and does not call any other
harness component that touches a payload file or a real adapter.

## 4. Input Boundary

The function accepts five arguments:

- `stage0_readiness`: a dict that must satisfy:
  - `review_kind == "stage0_readiness_review"`
  - `stage0_ready is True`
  - `measurement_authorized is False`
  - `real_benchmark_authorized is False`
  - `selection_made is False`

  Any violation raises one of `NonObjectStage0Readiness`,
  `InvalidStage0Readiness`, `Stage0AuthorizesMeasurement`,
  `Stage0AuthorizesRealBenchmark`, or `Stage0DeclaresSelection`
  with an explicit halt event before raising.

- `fixture_admission_record`: a dict that must carry
  `real_benchmark_data is False` and `selection_made is False`.
  Violations raise `NonObjectStage1Record` (if not a dict),
  `Stage1RecordDeclaresRealBenchmarkData`, or
  `Stage1RecordDeclaresSelection`.

- `candidate_adapter_record`: a dict that must carry
  `real_adapter is False`, `production_registration is False`, and
  `selection_made is False`. Violations raise
  `NonObjectStage1Record`, `Stage1RecordDeclaresRealAdapter`,
  `Stage1RecordDeclaresProductionRegistration`, or
  `Stage1RecordDeclaresSelection`.

- `contract_checks`: a non-empty list of `(name, callable)` pairs.
  `name` must be a non-empty string; `callable` must be a callable
  that accepts the observation dict and returns truthy on pass /
  falsy on fail. Because the check name is surfaced in the result
  and event log, `name` must not contain any
  `harness.review_package.FORBIDDEN_PHRASES` substring, the local
  `"score"` / `"scoring"` extension, or any
  `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES` substring.
  Violations raise `InvalidContractCheckList` (if not a non-empty
  list) or `InvalidContractCheck` (if any entry is not a
  `(non-empty-string, callable)` pair or has a forbidden name).

- `event_log`: a `harness.event_log.EventLog` instance.

## 5. Contract Check Boundary

Each contract check receives a fresh observation dict containing
ONLY these nine keys (the `OBSERVATION_KEYS` constant):

- `stage0_ready`
- `fixture_set_id`
- `candidate_adapter_id`
- `configuration_id`
- `fixture_class_count`
- `candidate_plane_count`
- `selection_made`
- `measurement_authorized`
- `real_benchmark_authorized`

Per-record substantive content (planes_declared lists, content
hashes, adapter kind, fixture classes, scaffold markers, etc.) is
NOT propagated into the check input. This keeps the scaffold
contract checks operating against the Stage 0 readiness state
only, not against any real adapter output. Real adapter response
inspection requires the future extension noted in Section 1 and
Section 11.

Each check is called as `check_fn(observation)` and is expected to
return a truthy value for pass or a falsy value for fail. A check
callable that RAISES is treated as a check failure under this
scaffold; the exception is caught, the check is recorded as
failed, and the halt event is recorded normally. This prevents a
buggy check callable from leaving the event log in an
inconsistent state.

Codex review-time hardening: check names are rejected before any
check runs if they contain forbidden result-surface language,
including the local `"score"` / `"scoring"` extension. This closes
the otherwise possible path where an invalid check name could leak
forbidden language through `failed_check_names`, `check_name`, or
`failed_check_name`.

Each check receives a NEW dict per call, so a check callable that
mutates its argument cannot affect later checks. (Halt-on-first-
failure means later checks do not run after a failure, but the
isolation guarantee holds for the pass-pass-pass sequence too.)

## 6. Pass Behavior

When every check passes, the function:

1. Records one `stage1_contract_check_passed` event per check, in
   the order the checks ran. Each event carries
   `candidate_adapter_id`, `configuration_id`, and `check_name`.
2. After the last check passes, records one
   `stage1_contract_safety_passed` event with
   `candidate_adapter_id`, `configuration_id`, and
   `checks_passed_count`.
3. Returns a dict with exactly the fourteen `ALLOWED_RESULT_KEYS`:
   - `result_kind`: literal string `"stage1_contract_safety_result"`.
   - `contract_safety_status`: literal `"passed"`.
   - `stage1_passed`: literal `True`.
   - `checks_run_count`: integer count of checks executed.
   - `checks_passed_count`: integer count of checks that returned
     truthy.
   - `checks_failed_count`: literal `0` on a pass.
   - `failed_check_names`: literal `[]` on a pass.
   - `candidate_adapter_id`: pass-through from the candidate
     adapter record.
   - `configuration_id`: pass-through from the candidate adapter
     record.
   - `fixture_set_id`: pass-through from the fixture admission
     record.
   - `selection_made`: literal `False`.
   - `measurement_authorized`: literal `False`. Stage 1 pass does
     NOT authorize measurement; it only records that the scaffold
     contract checks passed against the readiness state.
   - `real_benchmark_authorized`: literal `False`. Stage 1 pass
     does NOT authorize real benchmark execution.
   - `result_note`: observation-only literal string referencing
     this document and the Indexing Excellence Gate.

The pass result is observation-only. It is not validation evidence
for any route, not benchmark output, not architecture approval, and
not a winner / best / production-ready / recommended declaration.

## 7. Failure And Halt Behavior

On the first failing check, the function:

1. Records one `stage1_contract_check_failed` event for the failed
   check with `candidate_adapter_id`, `configuration_id`, and
   `check_name`.
2. Records one halt event `stage1_contract_safety_failed` with
   `candidate_adapter_id`, `configuration_id`, and
   `failed_check_name`.
3. Stops the check loop. No later checks run.
4. Returns a dict with exactly the fourteen `ALLOWED_RESULT_KEYS`:
   - `contract_safety_status`: literal `"failed"`.
   - `stage1_passed`: literal `False`.
   - `checks_run_count`: integer count of checks executed (passing
     checks before the failure plus the failed check).
   - `checks_passed_count`: integer count of passing checks before
     the failure.
   - `checks_failed_count`: literal `1` (halt-on-first-failure).
   - `failed_check_names`: list with the failed check's name.
   - Identity pass-through fields are populated as in the pass
     case.
   - `selection_made`, `measurement_authorized`,
     `real_benchmark_authorized`: all literal `False`. A Stage 1
     failure does NOT authorize measurement, real benchmark
     execution, or selection; failure simply records that the
     scaffold contract checks did not pass.
   - `result_note`: same observation-only literal as the pass
     case.

A failing check callable that raises is treated as a failure (see
Section 5); the same recording sequence applies.

## 8. Non-Measurement Guarantee

The Stage 1 scaffold does not authorize measurement under ANY path:

- Pass path: `measurement_authorized: False`. Stage 1 contract
  safety passing means the scaffold readiness observation
  satisfied the caller-supplied checks; it does not authorize
  measurement.
- Failure path: `measurement_authorized: False`. Stage 1 contract
  safety failing means the scaffold readiness observation did not
  satisfy the caller-supplied checks; this is an even stronger
  reason not to authorize measurement.
- Pre-check input rejection (Stage 0 tampered, records tampered,
  contract list invalid): the function raises before returning any
  result dict. No `measurement_authorized: True` is ever emitted.

This matches the WO-19 / DC-022 halt-before-measurement invariant
ratified at WO-36 review. The scaffold extends the invariant
forward: no future Stage 1 scaffold output can be silently
upgraded to "measurement authorized" by reading habit, because the
boolean is fixed at literal `False` in every emitted dict.

A future real-adapter Codex packet that introduces real
measurement must explicitly relax this scaffold rule (or replace
the module with a sibling that authors a different output shape);
the current scaffold cannot drift into authorizing measurement.

## 9. Non-Selection Guarantee

The Stage 1 scaffold does not select any architecture, vendor,
library, index family, ANN backend, neural re-scorer, retrieval
family, ablation cell, multi-stage variant, or production system:

- The output `selection_made` is literal `False` on every path.
- Stage 0 readiness with `selection_made is True` is rejected
  before any check runs (raises `Stage0DeclaresSelection`).
- Either record with `selection_made is True` is rejected before
  any check runs (raises `Stage1RecordDeclaresSelection`).
- The contract checks operate on a scaffold observation dict whose
  `selection_made` field is also literal `False`; the checks
  cannot read any "selected configuration" signal because none
  exists at scaffold level.
- The Indexing Excellence Gate (`00-controller-checklist.md`
  Section K) continues to govern selection unconditionally. "Best
  not proven = not selected" remains canonical.
- No aggregate score from any source may select a winner by itself.
  The scaffold does not compute aggregate scores; the
  `contract_safety_status` literal strings (`"passed"`, `"failed"`)
  are not scores.

## 10. What This Resolves

WO-45 resolves the following at scaffold level:

- Records a scaffold-level Stage 1 contract-safety pass that any
  future real Stage 1 implementation must remain consistent with
  at the observation-and-event-shape level.
- Adds DC-045 to the trackers.
- Adds three named events to the observable event surface:
  `stage1_contract_check_passed`, `stage1_contract_check_failed`,
  and `stage1_contract_safety_passed` (plus the halt reason
  `stage1_contract_safety_failed`).
- Discharges WO-39 / WO-40 blocker number 4 (the execution protocol
  blocker) one further step beyond what WO-43 / WO-44 discharged.
  Stage 0 + Stage 1 scaffolds are now both in place; Stages 2
  through 5 remain blocked.

## 11. What Remains Unresolved

WO-45 does not resolve:

- Stage 2 quality measurement scaffolding.
- Stage 3 performance measurement scaffolding.
- Stage 4 operational measurement scaffolding.
- Stage 5 Human Architecture Review Package scaffolding.
- Real candidate retrieval adapter authoring (real adapter
  integration; the Stage 1 module would need to be extended or
  paired with a sibling module to consume real responses).
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
  flagged by Codex at WO-39 / WO-40 review. The Stage 1 module
  imports only canonical `FORBIDDEN_PHRASES`; the test file applies
  the local-mirror extension. A future Codex packet may
  consolidate.

The WO-39 / WO-40 readiness gate states are unchanged by WO-45:

| Gate | State |
|------|-------|
| scaffold-ready | YES |
| artifact-ready | YES |
| review-summary-ready | YES |
| real-benchmark-ready | NO |

## 12. Recommended Next Packet

Codex retains all authority over the next packet. Claude's
forward-looking recommendation:

The next executable packet should pick exactly one of the
remaining pre-measurement scaffolding shapes, keeping the
Indexing Excellence Gate audit surface narrow. Recommended
shapes, in order of safest pairing with the current scaffold:

1. **Stage 1 measurement-record observation scaffolding (the
   bridge between Stage 1 contract-safety and Stage 2 quality
   measurement, discharging the boundary between the two).**
   Author a scaffold-internal module that records a Stage 1
   "configuration cleared contract-safety" observation in a fixed
   shape that the future Stage 2 quality measurement scaffold can
   consume. The observation is NOT a measurement; it is a
   structural marker that Stage 1 passed. The module must keep
   `measurement_authorized: False` on every output (Stage 1 pass
   is the precondition for Stage 2, not authorization for Stage
   2).

2. **Stage 1 result aggregation across multiple candidate
   adapters (still pre-measurement).** Author a scaffold-internal
   module that consumes multiple Stage 1 results and produces a
   per-candidate-adapter pass / fail summary without ranking or
   scoring. Useful for staging multiple candidates before any
   measurement.

3. **Stage 2 quality measurement scaffold (the first real
   metric-collection scaffold, even if no real adapter is wired
   in).** This packet must author the metric harness shape with
   `measurement_authorized` becoming `True` only for configurations
   that passed Stage 1. This is a larger step and should NOT be
   combined with any other shape; it is the first packet that
   crosses the measurement-authorization boundary.

Any packet that crosses from "scaffold observation" to "real
measurement" or "real adapter response" must explicitly relax the
literal-False `measurement_authorized` rule, must explicitly
relax the literal-False `real_adapter` rule, and must record the
relaxation in DC-XXX tracker rows. The current scaffold cannot
drift into either authorization state silently.

Real benchmark execution authorization remains a separate future
packet that depends on Stages 1 through 5 each being scaffolded
and approved, plus OQ-056 and OQ-076 being explicitly resolved or
explicitly carried open with documented mitigations.

## 13. Forbidden Scope

WO-45 is forbidden from doing any of the following:

- Modifying any existing harness implementation module. The one
  allowed new module is `harness/stage1_contract_safety.py`.
- Modifying any existing test file under `harness/tests/`.
- Modifying any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Invoking any real adapter behavior.
- Performing real benchmark execution.
- Collecting real quality / performance / operational metrics.
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

## 14. Out Of Scope

The following remain explicitly out of scope for WO-45 and require
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
- Wiring real adapter responses into the Stage 1 contract checks.
  The current scaffold checks see only the readiness observation
  dict.
- Consolidating the `"score"` / `"scoring"` forbidden-language
  extension into the canonical
  `harness.review_package.FORBIDDEN_PHRASES`.
