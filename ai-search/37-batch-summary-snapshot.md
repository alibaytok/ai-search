# ai-search - Scaffold Batch Summary Snapshot Boundary

Document type: Phase 4 / Phase 9 / Batch summary snapshot boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes - Codex corrected the WO-27 cross-reference during review
Work Order: WO-37

---

## 1. Purpose

This document records the scaffold-internal extension to the WO-35 /
WO-36 batch dry-run runner authorized under WO-37 / DC-040 at
`harness/batch_runner.py`. The extension persists the batch summary
itself - the dict that `run_payload_batch(...)` already returns - to a
caller-provided path using the existing scaffold-internal artifact
snapshot writer (`harness.artifact_snapshot.write_scaffold_snapshot`,
WO-27 / DC-030). The writer's returned metadata is then attached to
the in-memory returned summary as `batch_snapshot_evidence`. The
on-disk JSON file is the pre-attachment summary and does not contain
`batch_snapshot_evidence`.

The extension is scaffold-internal only. It does not introduce a
retention policy, a storage policy, an immutability policy, an
access-control policy, a registration mechanism, a production
artifact contract, a production artifact schema, real benchmark
execution, real metric collection, scoring, ranking, or architecture
selection. OQ-056 (run artifact retention / storage policy) and
OQ-076 (production artifact schema) both remain OPEN.

## 2. Scaffold-Only Scope

The WO-37 extension touches only the five files allowed by the WO-37
packet: `harness/batch_runner.py`,
`harness/tests/test_batch_runner.py`,
`ai-search/37-batch-summary-snapshot.md`,
`ai-search/00-open-questions.md`, and
`ai-search/00-claude-task-ledger.md`.

The extension does not:

- Modify `harness/dry_run.py`, `harness/payload_loader.py`,
  `harness/artifact_snapshot.py`, or any other harness implementation
  module beyond `harness/batch_runner.py`.
- Modify any existing test file under `harness/tests/` other than
  `test_batch_runner.py`.
- Modify any payload file under `benchmark-fixtures/<class>/`, any
  `.gitkeep`, or `benchmark-fixtures/README.md`.
- Auto-discover payload files (the WO-35 boundary holds).
- Invent any directory policy, filename convention, registration
  mechanism, retention policy, storage policy, immutability policy,
  or access-control policy.
- Author a production manifest schema or production artifact contract.

The module continues to import only the Python stdlib `os` and two
harness-internal symbols: `harness.dry_run.run_toy_dry_run` and
`harness.artifact_snapshot.write_scaffold_snapshot`.

## 3. Invocation Boundary

The public surface is:

```
run_payload_batch(payload_specs, common_inputs,
                  snapshot_dir=None,
                  batch_summary_output_path=None) -> dict
```

`batch_summary_output_path` is a new optional keyword. When `None`
(the default), the runner behaves exactly as it did under WO-35 /
WO-36: it builds and returns the batch summary in memory and writes
no batch-summary file. When set to a non-`None` value, the runner:

1. Builds the batch summary exactly as before (no field added before
   the file is written).
2. Calls `harness.artifact_snapshot.write_scaffold_snapshot(summary,
   batch_summary_output_path)`.
3. Receives the writer's returned metadata dict
   (`{output_path, sha256, byte_length}`).
4. Attaches that dict to the in-memory summary as the field
   `batch_snapshot_evidence`.
5. Returns the in-memory summary.

The caller owns the path. The runner does not create parent
directories, derive filenames from the package contents, enforce any
prefix, or choose any path component. The runner does not write to
any path the caller did not provide.

## 4. Deterministic Write Behavior

`write_scaffold_snapshot(...)` (WO-27 / DC-030) writes deterministic
UTF-8 JSON with `sort_keys=True` and `ensure_ascii=True`. For a given
batch summary the on-disk file is byte-for-byte identical across
runs. The runner does not introduce any non-determinism between
building the summary and calling the writer; no timestamps, random
identifiers, or system-dependent values are added to the summary by
the WO-37 extension.

The writer's existing rejection ordering still applies:

1. Non-dict package -> `NonObjectSnapshotPackage`. The batch summary
   is always a dict, so this path is unreachable in practice.
2. Forbidden language anywhere in the package strings ->
   `ForbiddenLanguageInSnapshotPackage`. The batch summary contains
   no phrase from `harness.review_package.FORBIDDEN_PHRASES`, so this
   path is unreachable in practice (see Section 8).
3. Serialization or write failure -> `SnapshotWriteError`. The runner
   propagates this exception unchanged when it occurs.

## 5. Returned Metadata Boundary

When `batch_summary_output_path is not None`, the in-memory returned
summary acquires exactly one new field:

- `batch_snapshot_evidence`: a dict with exactly three keys produced
  by the writer:
  - `output_path` (string): the caller-provided path, verbatim.
  - `sha256` (string): hex digest of the written file's bytes.
  - `byte_length` (integer): byte length of the written file.

The field is observation-only. It is not validation evidence, not
benchmark output, not a quality / performance metric, not a route
trust signal, not a registration record, and not a production
artifact contract. It is a scaffold-internal pointer plus integrity
fingerprint of a scaffold-internal file.

The on-disk JSON file does NOT contain `batch_snapshot_evidence`.
The metadata is attached only to the in-memory dict, and only after
the file has been written, so the on-disk file remains the
pre-attachment summary. A test
(`test_on_disk_summary_omits_batch_snapshot_evidence`) asserts this.

When `batch_summary_output_path is None`, the returned summary does
not contain `batch_snapshot_evidence`. A test
(`test_default_call_attaches_no_batch_snapshot_evidence`) asserts
this.

## 6. Relationship to WO-27 Artifact Snapshot Writer

The WO-37 extension is a one-line application of the existing WO-27 /
DC-030 writer. Specifically:

- WO-27 / DC-030 introduced `write_scaffold_snapshot(package,
  output_path, event_log=None)` as a scaffold-only writer for toy
  dry-run review packages. The writer's contract is documented in
  `ai-search/27-scaffold-run-artifact-snapshot.md`.
- WO-37 reuses that writer verbatim. It does not add a new writer,
  modify the existing writer, change the writer's signature, change
  the writer's output format, change the writer's rejection ordering,
  or change the writer's determinism guarantees.
- The package passed to the writer under WO-37 is the batch summary
  dict, not a per-spec review package. The writer accepts any dict;
  there is no per-shape special-casing.
- The `event_log` parameter is not used by the WO-37 caller (the
  batch runner does not own an event log). The writer's optional
  event-log code path is unaffected.

## 7. Relationship to WO-35 / WO-36 Batch Runner

The WO-37 extension is additive. It changes the public signature of
`run_payload_batch(...)` only by adding one optional keyword with a
default of `None`. All WO-35 and WO-36 invariants continue to hold:

- The runner still does not perform real benchmark execution.
- The runner still does not collect quality / performance metrics.
- The runner still does not score, rank, or declare any winner /
  best / production-ready / recommended configuration.
- The runner still does not auto-discover payload files; it consumes
  only caller-provided specs.
- The runner still does not walk `benchmark-fixtures/` or any other
  directory.
- The per-run summary still contains the WO-35 fields
  (`fixture_class`, `payload_entry_count`, `event_count`,
  `selection_made`, `snapshot_written`) and the WO-36 fields
  (`contract_status`, `contract_checks_passed_count`,
  `contract_checks_failed_count`, `halt_count`,
  `disqualified_configuration_count`, `measurement_recorded`).
- The WO-36 review-discipline observation continues to hold under
  WO-37: under the failing-contract path the on-disk summary records
  `contract_status == "failed"` and `measurement_recorded is False`
  for every per-run summary, because `run_toy_dry_run(...)` still
  never calls `record_measurement(...)` (WO-19 / DC-022 invariant).
  A test (`test_failing_contract_batch_still_writes_summary_snapshot`)
  asserts the WO-37 write path succeeds under failing contracts and
  preserves this observation on disk.

## 8. Forbidden Summary Language Boundary

The persisted batch summary continues to satisfy every WO-35 / WO-36
language hygiene assertion:

- `str(summary).lower()` contains no phrase from
  `BATCH_SUMMARY_FORBIDDEN_PHRASES` (which extends
  `harness.review_package.FORBIDDEN_PHRASES` with `"score"` and
  `"scoring"` per the Codex WO-35 review-time hardening).
- Every string scalar in the summary is free of every phrase in
  `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`.

Two tests
(`test_persisted_summary_has_no_forbidden_selection_language` and
`test_persisted_summary_has_no_forbidden_claim_phrases`) assert this
against the on-disk file, not only the in-memory dict.

The new `batch_snapshot_evidence` field contains only the writer's
three keys (`output_path`, `sha256`, `byte_length`). None of these
keys or their string values can introduce a forbidden phrase. The
field is added only to the in-memory dict, after the language hygiene
check inside the writer has already passed.

## 9. No-Mutation Boundary

The WO-37 extension does not mutate any file under
`benchmark-fixtures/`. A new test
(`test_batch_summary_snapshot_does_not_mutate_benchmark_fixtures`)
asserts that the `benchmark-fixtures/` inventory and per-file
SHA-256 are bit-identical before vs. after a batch run that persists
its summary to a tempfile path.

The runner still does not walk `benchmark-fixtures/`. Payload files
are consumed only via the per-spec `payload_path` provided by the
caller. The batch summary output path is the only new file the
runner writes when this feature is invoked.

## 10. OQ-056 / OQ-076 Non-Closure

OQ-056 (run artifact retention / storage policy) and OQ-076 (production
artifact schema) both remain OPEN. The WO-37 extension persists a
scaffold-internal file at a caller-provided path. It:

- Defines no retention policy, no expiration policy, no rotation
  policy, no eviction policy, no storage policy, no immutability
  policy, no replication policy, and no access-control policy for
  scaffold or production artifacts.
- Defines no registration mechanism (no manifest entry, no index,
  no catalog, no registry, no notification, no event bus).
- Defines no production artifact schema. The on-disk format is the
  existing scaffold dict, serialized via the existing scaffold writer.
- Does not constitute the future production artifact contract. A
  separate Codex-authored Work Order is required for that.

## 11. Forbidden Scope

The WO-37 extension is forbidden from doing any of the following:

- Modifying any harness implementation module other than
  `harness/batch_runner.py`.
- Modifying any existing test file other than
  `harness/tests/test_batch_runner.py`.
- Modifying any payload file, any `.gitkeep`, or any README.
- Auto-discovering payload files by walking any directory.
- Collecting quality / performance metrics; the persisted file is
  a verbatim copy of the existing scaffold batch summary.
- Performing real benchmark execution.
- Scoring, ranking, or declaring any configuration a winner / best /
  production-ready / recommended.
- Authoring a real retrieval adapter or any real retrieval /
  indexing / ranking algorithm.
- Authoring a production manifest schema, retention policy, storage
  policy, immutability policy, access-control policy, registration
  mechanism, or production artifact contract.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding third-party dependencies.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
  All seven remain OPEN.
- Duplicating RK-039.
- Mutating corpus docs, route registry docs, validation evidence,
  source quality graph, intent trace store, candidate routes, or
  official routes.

## 12. Out-of-Scope

The following remain explicitly out of scope for WO-37 and require
separate Codex-authored Work Orders whose scope, allowed files,
required content, forbidden scope, acceptance criteria, and evidence
requirements are explicit at issue time:

- Real benchmark execution.
- Real metric collection or scoring.
- Real retrieval / indexing / ranking implementation.
- Real adapter integration.
- Production artifact schema (OQ-076).
- Retention / storage / immutability / access-control policy
  (OQ-056).
- Production registration mechanism.
- Architecture / vendor / library / index family / ANN backend /
  neural re-scorer / retrieval family / ablation cell / multi-stage
  selection.
- CLI, entry point, console script, or shell wrapper.
- Wiring `harness.contract_runner.record_measurement(...)` into
  `harness.dry_run.run_toy_dry_run(...)`. (This wiring would flip
  `measurement_recorded` to True under measurement paths; until then
  the field accurately reports False under both pass and contract-
  failure paths per the WO-19 / DC-022 invariant ratified by the
  Codex WO-36 review.)
