# ai-search - Batch Contract Status Surface

Document type: Phase 4 / Phase 9 / Batch contract status surface boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes - Codex ratified the WO-19 / DC-022 measurement boundary under WO-36 review
Work Order: WO-36

---

## 1. Purpose

This document records the scaffold-internal extension to the WO-35 /
DC-038 batch dry-run runner authorized under WO-36 / DC-039 at
`harness/batch_runner.py`. The extension surfaces contract pass /
fail / disqualification status from each per-spec
`run_toy_dry_run(...)` invocation into the per-run summary entries
the runner returns, plus a `measurement_recorded` observation
boolean.

The extension is scaffold-internal only. The added fields are
observation counts and booleans derived directly from the assembled
review package's existing fields and event log. They are not
quality / performance metrics. The runner still does not perform
real benchmark execution, does not score, does not rank, does not
convert payloads into validation evidence, and does not select any
architecture.

## 2. Scaffold-Only Scope

The WO-36 extension touches only the five files allowed by the WO-36
packet: `harness/batch_runner.py`,
`harness/tests/test_batch_runner.py`,
`ai-search/36-batch-contract-status-surface.md`,
`ai-search/00-open-questions.md`, and
`ai-search/00-claude-task-ledger.md`.

The extension does not:

- Modify `harness/dry_run.py`, `harness/payload_loader.py`, or any
  other harness implementation module beyond
  `harness/batch_runner.py`.
- Modify any existing test file under `harness/tests/` other than
  `test_batch_runner.py`.
- Modify any payload file under `benchmark-fixtures/<class>/`, any
  `.gitkeep`, or `benchmark-fixtures/README.md`.
- Auto-discover payload files (the WO-35 boundary holds).
- Author a production manifest schema, retention policy, storage
  policy, registration mechanism, or production artifact contract.

The module continues to import only the Python stdlib `os` and one
harness-internal symbol: `harness.dry_run.run_toy_dry_run`.

## 3. Contract-Status Fields

Each per-run summary returned by `run_payload_batch(...)` now carries
six observation-only fields, in addition to the WO-35 fields
(`fixture_class`, `payload_entry_count`, `event_count`,
`selection_made`, `snapshot_written`):

- `contract_status`: string. One of `"passed"` or `"failed"`. See
  Section 4 for the derivation rule.
- `contract_checks_passed_count`: integer count of
  `contract_check_pass` events in the per-spec package
  (`len(package["contract_checks_passed"])`).
- `contract_checks_failed_count`: integer count of contract failures
  (`len(package["contract_checks_failed"])`).
- `halt_count`: integer count of halt events recorded by the per-spec
  dry-run (`len(package["halt_events"])`).
- `disqualified_configuration_count`: integer count of configurations
  disqualified by the contract runner during the per-spec dry-run
  (`len(package["disqualified_configurations"])`).
- `measurement_recorded`: boolean. `True` iff any event with
  `type == "measurement_recorded"` appears in
  `package["all_events"]`; `False` otherwise. See Section 6 for the
  observation boundary and the WO-19 / DC-022 interaction.

The added fields are observation counts and booleans only. They are
not aggregate metrics, scores, rankings, thresholds, or selection
signals.

## 4. Pass / Fail Derivation

The `contract_status` field is derived from the per-spec package by
the following rule, applied locally in
`harness/batch_runner.py:_per_run_summary(...)`:

```
contract_status = "passed"
    if contract_checks_failed_count == 0
       and disqualified_configuration_count == 0
    else "failed"
```

Both conditions must hold for `"passed"`. Either condition alone is
sufficient to set `"failed"`. This mirrors the existing WO-19 /
DC-022 invariant that contract failure disqualifies a configuration
and is observable via the `contract_checks_failed` and
`disqualified_configurations` fields the review package already
exposes.

The rule operates on counts already produced by the underlying dry-run
and the review-package assembler. The batch runner does not invent
any new contract-status signal; it only surfaces the counts.

## 5. Optional Scaffold-Internal `contract_checks` Pass-Through

The WO-36 extension adds one optional `common_inputs` key:

- `contract_checks` (optional): when present, the runner forwards
  it verbatim to `run_toy_dry_run(...)` via the `contract_checks`
  keyword parameter. When absent, the dry-run's default
  scaffold-internal toy contract checks are used (WO-23 /
  WO-25-extended).

The pass-through key is intentionally a scaffold-internal test
surface. Its only purpose is to allow the WO-36 tests to inject an
always-fail contract check so the failed status path can be
exercised end-to-end. Production contract checks remain
Codex-owned and outside this scope.

The key is not added to `REQUIRED_COMMON_INPUT_KEYS`; the seven
existing required keys remain the only required keys. Any value
caller-provided for `contract_checks` is forwarded as-is; the
batch runner does not validate its shape. The downstream dry-run and
contract runner perform their own validation.

## 6. Measurement-Recorded Observation Boundary

The `measurement_recorded` field is a pure observation:

- It reports `True` iff a `measurement_recorded` event exists in
  `package["all_events"]`.
- It reports `False` otherwise.

WO-19 / DC-022 invariant interaction: the dry-run never emits a
`measurement_recorded` event in either the clean-run path or the
contract-failure path. The contract runner emits the event only from
`record_measurement(configuration_id, measurement_kind, payload)`,
which the dry-run does not call. Consequently, in the current
scaffold, `measurement_recorded` accurately reports `False` for both
the passed and the failed contract-status cases. A future Codex
packet that wires real measurement collection into the dry-run will
cause the field to flip to `True` for runs that record measurements;
the field is named here so that future change is observable without
schema drift.

The field is observation only. It is not a metric. It does not
count measurements. It is a single boolean reflecting whether the
event class is present in the package.

## 7. No-Mutation Boundary

The WO-36 extension does not mutate any file under
`benchmark-fixtures/`. The WO-35 no-mutation guarantees continue to
hold:

- The runner does not walk `benchmark-fixtures/` or any other
  directory.
- The runner does not write any file outside the per-spec snapshot
  path (when `snapshot_dir` is provided).
- The runner does not modify the caller-provided `payload_specs` or
  `common_inputs` dicts.

A new test
(`BatchRunnerFailingContractNoMutationTest`) asserts that an
always-fail contract-check batch leaves the `benchmark-fixtures/`
inventory and per-file SHA-256 unchanged before vs. after the batch
runs.

## 8. Forbidden Summary Language Boundary

The batch summary returned by `run_payload_batch(...)` continues to
contain no forbidden selection language and no forbidden claim
phrases. The WO-35 invariants extend under WO-36:

- The batch summary as a whole is scanned via `str(summary).lower()`
  against `BATCH_SUMMARY_FORBIDDEN_PHRASES`, which extends
  `harness.review_package.FORBIDDEN_PHRASES` with `"score"` and
  `"scoring"` (the Codex review-time hardening from the WO-35
  review). No phrase from this extended list may appear.
- Every string scalar inside the summary is scanned against
  `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`. No phrase from
  that list may appear.

The contract-status fields themselves contain only the strings
`"passed"` and `"failed"`. These two values are scaffold-internal
status terms. They contain no forbidden phrase. They do not
constitute a selection / recommendation / winner / best /
production-ready / ranking claim.

Under the always-fail contract-check test scenario, the per-run
summary's `contract_status` is `"failed"` and the batch summary
remains free of all forbidden phrases. Two tests
(`test_failing_batch_summary_has_no_forbidden_selection_language`
and `test_failing_batch_summary_has_no_forbidden_claim_phrases`)
assert this.

## 9. Forbidden Scope

The WO-36 extension is forbidden from doing any of the following:

- Modifying any harness implementation module other than
  `harness/batch_runner.py`.
- Modifying any existing test file other than
  `harness/tests/test_batch_runner.py`.
- Modifying any payload file, any `.gitkeep`, or any README.
- Auto-discovering payload files by walking any directory.
- Collecting quality / performance metrics; the added counts are
  contract-status observation only, not metrics.
- Performing real benchmark execution.
- Scoring, ranking, or declaring any configuration a winner / best /
  production-ready / recommended.
- Authoring a real retrieval adapter or any real retrieval /
  indexing / ranking algorithm.
- Authoring a production manifest schema, retention policy, storage
  policy, registration mechanism, or production artifact contract.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding third-party dependencies.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
  All seven remain OPEN.
- Duplicating RK-039.

## 10. Not Benchmark Execution; Not Metric Scoring; Not Validation Evidence; Not Architecture Selection

WO-36 extension success is explicitly:

- **Not benchmark execution.** The extension surfaces existing
  contract-status fields from the per-spec review packages. It does
  not run any benchmark, does not read any benchmark dataset, and
  does not produce any benchmark output.
- **Not metric scoring.** The added counts are observation counts
  derived from the contract runner's pass / fail / halt /
  disqualification events. They are not quality scores, performance
  scores, ranking scores, or thresholds.
- **Not validation evidence.** A `contract_status` of `"passed"` or
  `"failed"` is a per-run contract observation. It does not
  constitute validation evidence against any candidate or official
  route. Validation evidence is recorded by the validation
  framework (`08-validation-and-feedback.md`); per-run contract
  status is benchmark-harness observation only.
- **Not architecture selection.** The Indexing Excellence Gate
  (`00-controller-checklist.md` Section K) continues to govern
  selection. The extension makes no architecture, vendor, library,
  ANN backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production-system claim. Future real
  adapter integration, real benchmark execution, real fixture
  loader registration, real artifact contract, or architecture
  selection each require separate Codex-authored Work Orders whose
  scope, allowed files, required content, forbidden scope,
  acceptance criteria, and evidence requirements are explicit at
  issue time.
