# ai-search - Scaffold Payload Batch Dry-Run Runner

Document type: Phase 4 / Phase 9 / Scaffold payload batch dry-run runner boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes - Codex review-time summary-language hardening applied
Work Order: WO-35

---

## 1. Purpose

This document records the scaffold-internal batch dry-run runner
authorized under WO-35 / DC-038 at `harness/batch_runner.py`. The
runner is a thin orchestrator over the existing
`harness.dry_run.run_toy_dry_run(...)` function: it invokes the
existing dry-run once per caller-provided payload spec and returns a
batch summary dict.

The runner is scaffold-internal only. It does not perform real
benchmark execution. It does not collect metrics. It does not score,
rank, or declare any configuration a winner / best / production-ready.
It does not convert payloads into validation evidence. It does not
select any architecture, vendor, library, index family, ANN backend,
neural re-scorer, retrieval family, ablation cell, multi-stage
variant, or production system. The Indexing Excellence Gate
(`00-controller-checklist.md` Section K) continues to govern selection.

## 2. Scaffold-Only Scope

The WO-35 runner touches only the five files allowed by the WO-35
packet: `harness/batch_runner.py`,
`harness/tests/test_batch_runner.py`,
`ai-search/35-scaffold-payload-batch-runner.md`,
`ai-search/00-open-questions.md`, and
`ai-search/00-claude-task-ledger.md`.

The runner does not:

- Modify any existing harness implementation module (`harness/dry_run.py`,
  `harness/payload_loader.py`, and every other module under `harness/`).
- Modify any existing test file under `harness/tests/`.
- Modify any payload file under `benchmark-fixtures/<class>/`, any
  `.gitkeep`, or `benchmark-fixtures/README.md`.
- Auto-discover payload files by walking `benchmark-fixtures/` or any
  other directory.
- Author a production manifest schema, retention policy, storage
  policy, registration mechanism, or production artifact contract.

The module imports only the Python stdlib `os` and one harness-internal
symbol: `harness.dry_run.run_toy_dry_run`.

## 3. Caller-Provided Payload Spec Boundary

The runner consumes a non-empty list of caller-provided payload specs
via the `payload_specs` parameter. Each spec is a dict with at least:

- `fixture_class` (non-empty string): the class name the runner asserts
  the payload should declare.
- `payload_path` (non-empty string): the path to the payload file.

Specs may carry additional keys; those are ignored. The runner does not
inspect the payload-path filesystem location beyond passing it through
to `run_toy_dry_run(...)`. The runner does not enumerate
`benchmark-fixtures/` or any other directory. The caller is fully
responsible for providing the path strings; this is a "caller-provided
specs only" boundary, explicitly distinct from any future auto-discovery
mechanism.

Validation rejects:

- a non-list or empty `payload_specs` (`EmptyPayloadSpecs`),
- a non-dict spec entry, a spec missing `fixture_class` or
  `payload_path`, or a spec whose value for either is not a non-empty
  string (`MalformedPayloadSpec`).

All validation runs before any `run_toy_dry_run(...)` invocation. A
test (`test_validation_runs_before_any_dry_run_invocation`) asserts the
invariant by monkey-patching `run_toy_dry_run` to fail the test if
invoked.

## 4. Common Input Boundary

The runner consumes a `common_inputs` dict passed once per batch. It
must contain every key in `REQUIRED_COMMON_INPUT_KEYS`:

- `fixture_path`
- `fixture_sha256`
- `config_path`
- `registered_config`
- `deterministic_seed`
- `manifest_path`
- `expected_manifest_id`

These are the seven inputs that `run_toy_dry_run(...)` requires aside
from the per-spec payload parameters. Validation rejects a non-dict
`common_inputs` or any missing key (`MissingCommonInput`). Validation
runs before any `run_toy_dry_run(...)` invocation.

The runner does not validate the substantive contents of any common
input beyond key presence. The downstream `run_toy_dry_run(...)`,
manifest loader, and payload loader perform their own validation; the
batch runner is intentionally a thin orchestrator.

## 5. Batch Execution Order

For each spec in `payload_specs`, in list order, the runner:

1. Selects the per-spec snapshot output path. If `snapshot_dir` is
   `None`, the snapshot path is `None` and no snapshot is written. If
   `snapshot_dir` is provided, the snapshot path is
   `<snapshot_dir>/<fixture_class>-batch-snapshot.json`. The runner
   does not create `snapshot_dir`; the caller owns its lifetime.
2. Invokes `run_toy_dry_run(...)` with the common inputs, the
   per-spec `payload_path` and `expected_fixture_class`, and the
   selected snapshot output path.
3. Derives a per-run summary from the returned package's
   `payload_evidence` (entry count), `event_count` (or
   `len(all_events)`), and `selection_made` field, plus the per-spec
   `fixture_class` and a boolean recording whether a snapshot was
   written.

The batch summary preserves spec order: `fixture_classes` and
`per_run_summaries` are returned in the order the specs appeared.

If any `run_toy_dry_run(...)` invocation raises (e.g., the WO-32
payload loader rejects a payload), the exception propagates and the
batch loop aborts immediately. Subsequent specs are not invoked. A
test (`test_payload_loader_rejection_stops_batch_before_later_specs`)
asserts the invariant by injecting a deliberately mismatched first
spec and counting invocations.

## 6. Snapshot Boundary

The `snapshot_dir` parameter is optional and defaults to `None`:

- **No snapshot mode** (`snapshot_dir=None`): no snapshot file is
  written for any spec. Each per-run summary records
  `snapshot_written: False`.
- **Snapshot mode** (`snapshot_dir=<path>`): the runner writes one
  snapshot per spec under `snapshot_dir` using the deterministic
  filename `<fixture_class>-batch-snapshot.json`. The caller owns the
  directory's lifetime. The runner does not create
  `<snapshot_dir>`; if it does not exist, the underlying snapshot
  write inside `run_toy_dry_run(...)` raises.

The runner does not invent any other filename. The runner does not
write any snapshot under `benchmark-fixtures/`. A test
(`test_snapshot_files_not_written_under_benchmark_fixtures`) asserts
that the written paths all start with the caller's temporary directory
and not with the project's `benchmark-fixtures/` path.

## 7. Batch Summary Boundary

The runner returns a dict with the following fields:

- `batch_kind`: the constant string `"scaffold_payload_batch"`. This
  marker tags the dict as a scaffold-internal observation and not a
  production artifact.
- `run_count`: integer count of per-run summaries (equal to
  `len(payload_specs)` on the success path).
- `fixture_classes`: ordered list of per-spec `fixture_class` values,
  in spec order.
- `per_run_summaries`: ordered list of per-run summary dicts. Each
  per-run summary contains `fixture_class`, `payload_entry_count`,
  `event_count`, `selection_made` (always `False` on the success
  path), and `snapshot_written` (boolean reflecting whether the
  per-spec invocation requested a snapshot).
- `selection_made`: literal `False`. The batch as a whole proposes no
  configuration.
- `batch_note`: a free-text marker using neutral observation-only
  language; records that the batch proposes no configuration and
  records only scaffold counts and booleans.

The summary is re-scanned at test time against
`harness.review_package.FORBIDDEN_PHRASES` (selection / recommendation
/ winner / best / production-ready / ranking) and against
`harness.payload_loader.FORBIDDEN_CLAIM_PHRASES` (validation evidence /
validated route / route trust / benchmark result / benchmark output /
architecture selection / architecture choice / selected architecture /
production-grade). Under Codex review-time hardening, the summary test
also rejects `score` and `scoring` as returned-summary language. No
phrase from those lists may appear in the returned summary.

## 8. Halt And Rejection Behavior

The runner rejects at every named boundary. Each rejection raises a
named exception before any further work; no rejection is silent.

| Condition | Exception |
|-----------|-----------|
| `payload_specs` is not a non-empty list | `EmptyPayloadSpecs` |
| Spec is not a dict; spec missing `fixture_class` or `payload_path`; spec value not a non-empty string | `MalformedPayloadSpec` |
| `common_inputs` is not a dict; common-input dict missing a required key | `MissingCommonInput` |
| `run_toy_dry_run(...)` raises (e.g., fixture / config / manifest / payload loader rejection) | The named exception from the underlying loader (propagated) |

Validation rejections happen before any `run_toy_dry_run(...)`
invocation. Underlying-loader rejections happen during a per-spec
invocation; the batch loop aborts immediately on the first such
rejection and does not invoke subsequent specs.

The runner does not record any halt event into any event log of its
own; the underlying `run_toy_dry_run(...)` records the per-invocation
halt events into the per-invocation `EventLog`. The runner is
stateless across invocations.

## 9. No-Mutation Boundary

The runner does not mutate any file under `benchmark-fixtures/`. A
test (`test_benchmark_fixtures_unchanged_after_batch`) captures the
relative-path-to-SHA-256 inventory of `benchmark-fixtures/` before the
batch runs and asserts the inventory and per-file SHA-256 are unchanged
after the batch.

The runner does not auto-discover payload files. A second test
(`test_runner_does_not_auto_discover_from_benchmark_fixtures`) stages
copies of the WO-31 payloads into a temporary directory, provides
specs whose `payload_path` values point at the staged copies, and
asserts the batch runs successfully against those caller-provided
paths while `benchmark-fixtures/` itself is untouched.

The runner does not mutate the caller-provided `payload_specs` or
`common_inputs` dicts.

## 10. Forbidden Scope

The WO-35 runner is forbidden from doing any of the following:

- Modifying any existing harness implementation module or any existing
  test module.
- Modifying any payload file, any `.gitkeep`, or any README.
- Auto-discovering payload files by walking any directory.
- Performing real benchmark execution.
- Collecting metrics, scoring, ranking, or declaring any configuration
  a winner / best / production-ready / recommended.
- Implementing a real retrieval adapter or any real retrieval /
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
- Duplicating RK-039 (benchmark dataset contamination by production
  user feedback or recent traces); the existing RK-039 reference
  established under WO-29 / DC-032 Section 9 continues to apply.

## 11. Not Benchmark Execution; Not Scoring; Not Validation Evidence; Not Architecture Selection

Batch-runner success is explicitly:

- **Not benchmark execution.** The runner invokes the existing toy
  dry-run, which consumes only scaffold-internal toy inputs and
  synthetic WO-31 payload content. No real benchmark dataset is read.
  No real retrieval call is made. No metric is collected.
- **Not scoring.** The runner does not produce any metric, score,
  ranking, or aggregate signal. The toy default contract checks pass
  per-invocation; no disqualification occurs; no `measurement_recorded`
  event appears in any per-invocation package.
- **Not validation evidence.** Loaded payloads remain observation
  only. The batch summary surfaces only counts and identifiers, not
  per-route trust or per-route validation outcomes.
- **Not architecture selection.** The runner makes no architecture,
  vendor, library, ANN backend, neural re-scorer, retrieval family,
  ablation cell, multi-stage variant, or production-system claim. The
  Indexing Excellence Gate continues to govern selection. Future real
  adapter integration, real benchmark execution, real fixture loader
  registration, real artifact contract, or architecture selection each
  require separate Codex-authored Work Orders whose scope, allowed
  files, required content, forbidden scope, acceptance criteria, and
  evidence requirements are explicit at issue time.
