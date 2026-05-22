# ai-search - Combined Scaffold Batch Artifact Invocation Protocol

Document type: Phase 4 / Phase 9 / Batch artifact invocation protocol
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-38

---

## 1. Purpose

This document records the scaffold-internal invocation protocol
authorized under WO-38 / DC-041 at
`harness/tests/test_batch_artifact_invocation.py`. The protocol
invokes `harness.batch_runner.run_payload_batch(...)` once with both
the WO-35 / WO-36 per-run `snapshot_dir` and the WO-37
`batch_summary_output_path` provided simultaneously, across all three
admitted first-wave payload classes (`golden-intents`,
`hard-negatives`, `boundary-violations`), and verifies that the full
batch artifact path produces the expected on-disk artifacts and the
expected in-memory observation fields.

The protocol is an invocation protocol only. It does not modify any
harness implementation module, does not perform real benchmark
execution, does not collect metrics, does not score, does not rank,
does not declare any winner or best or production-ready or
recommended configuration, and does not select any architecture.
OQ-056 (run artifact retention / storage policy) and OQ-076
(production artifact schema) both remain OPEN.

## 2. Scaffold-Only Invocation Scope

The WO-38 protocol touches only the four files allowed by the WO-38
packet: `harness/tests/test_batch_artifact_invocation.py`,
`ai-search/38-combined-batch-artifact-invocation.md`,
`ai-search/00-open-questions.md`, and
`ai-search/00-claude-task-ledger.md`.

The protocol does not:

- Modify any harness implementation module under `harness/` other
  than test files; in fact, no harness implementation file is modified
  by WO-38 at all - the WO-38 packet allows only the one new test
  module under `harness/tests/`.
- Modify any existing test file under `harness/tests/`.
- Modify any payload file under `benchmark-fixtures/<class>/`, any
  `.gitkeep`, or `benchmark-fixtures/README.md`.
- Author a CLI, an entry point, a console script, a shell wrapper,
  or any third-party dependency.
- Author a production manifest schema, retention policy, storage
  policy, immutability policy, access-control policy, registration
  mechanism, or production artifact contract.

The test module imports only the Python stdlib (`hashlib`, `json`,
`os`, `tempfile`, `unittest`) and harness-internal symbols
(`harness.batch_runner.run_payload_batch`,
`harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`,
`harness.review_package.FORBIDDEN_PHRASES`).

## 3. Exact Inputs

The protocol drives `run_payload_batch(...)` with:

- `payload_specs`: the three admitted first-wave payload specs, one
  per class, each spec being a dict with non-empty string
  `fixture_class` (`"golden-intents"`, `"hard-negatives"`, or
  `"boundary-violations"`) and `payload_path`
  (`benchmark-fixtures/<class>/wave-001.json`).
- `common_inputs`: a dict containing exactly the seven WO-35
  required keys (`fixture_path`, `fixture_sha256`, `config_path`,
  `registered_config`, `deterministic_seed`, `manifest_path`,
  `expected_manifest_id`). The values point to the existing scaffold
  toy fixture, toy configuration, toy manifest, and the WO-19 / WO-25
  / WO-26 manifest identifier already used by every WO-35 and WO-36
  test.
- `snapshot_dir`: a `tempfile.TemporaryDirectory()` subdirectory
  `<temp dir>/per-run` (created by the test before invocation).
- `batch_summary_output_path`: `<temp dir>/batch-summary.json` at the
  top of the same temp directory.

No optional `contract_checks` override is provided; the dry-run uses
its default scaffold-internal toy contract checks (WO-23 /
WO-25-extended). The expected contract status across every per-run
summary is therefore `"passed"`.

## 4. Expected Artifact Layout Under Temp Dir

After a successful invocation, the temp directory is shaped as:

```
<temp dir>/
    batch-summary.json
    per-run/
        boundary-violations-batch-snapshot.json
        golden-intents-batch-snapshot.json
        hard-negatives-batch-snapshot.json
```

Exactly one batch-summary JSON file is written at the top of the temp
directory. Exactly three per-run snapshot JSON files are written
under the `per-run/` subdirectory, one per admitted class, named
`<class>-batch-snapshot.json` per the WO-35 deterministic per-class
filename convention recorded under DC-038. No other file is written
inside the temp directory by the runner.

The on-disk batch summary file is the pre-attachment summary; it does
not contain `batch_snapshot_evidence` (WO-37 boundary). The
`batch_snapshot_evidence` field exists only on the in-memory
returned summary.

## 5. Per-Run Snapshot Boundary

Per-run snapshots are written by `harness.dry_run.run_toy_dry_run(...)`
through the WO-27 / DC-030 artifact snapshot writer when
`snapshot_output_path` is provided. The runner provides
`<snapshot_dir>/<fixture_class>-batch-snapshot.json` per WO-35 /
DC-038 to each per-spec dry-run invocation. The on-disk per-run
snapshot files contain the per-spec review packages (adapter,
manifest, registered-configuration observation, payload evidence,
and the dry-run's pre-write events) with deterministic UTF-8 JSON
serialization (`sort_keys=True`, `ensure_ascii=True`). The protocol
does not assert per-file shape beyond per-run filename presence and
content boundaries; per-run snapshot internal-shape assertions are
covered by `harness/tests/test_toy_snapshot_invocation.py` (WO-28)
and `harness/tests/test_payload_dry_run_invocation.py` (WO-34).

## 6. Batch Summary Snapshot Boundary

The batch summary snapshot is written by
`harness.artifact_snapshot.write_scaffold_snapshot(...)` (WO-27 /
DC-030) at the caller-provided `batch_summary_output_path`. Its
contract is recorded under WO-37 / DC-040:

- The on-disk file is the pre-attachment summary; it does not contain
  `batch_snapshot_evidence`.
- The in-memory returned summary contains
  `batch_snapshot_evidence = {output_path, sha256, byte_length}`.
- `sha256` matches `hashlib.sha256(file_bytes).hexdigest()` of the
  written file.
- `byte_length` matches `os.path.getsize(output_path)` of the written
  file.
- `output_path` matches the caller-provided path verbatim.

The protocol asserts all four properties.

The on-disk file additionally contains every per-run summary, which
in turn carries the six WO-36 contract-status fields
(`contract_status`, `contract_checks_passed_count`,
`contract_checks_failed_count`, `halt_count`,
`disqualified_configuration_count`, `measurement_recorded`). Under
the default toy contract checks, every per-run on-disk
`contract_status` is `"passed"` and `measurement_recorded` is
`False`. The latter continues to reflect the WO-19 / DC-022 invariant
ratified at the WO-36 review: `run_toy_dry_run(...)` never calls
`record_measurement(...)`, so the field accurately reports `False`
in both the clean-run and the contract-failure paths.

## 7. No-Mutation Boundary

The protocol asserts two distinct no-mutation invariants:

- `benchmark-fixtures/` inventory and per-file SHA-256 are
  byte-identical before vs. after the invocation. This preserves the
  WO-31 baseline hashes that have been carried forward unchanged
  through WO-32 through WO-37.
- The harness implementation tree under `harness/` (excluding any
  `__pycache__` cache directories that may exist outside the
  `python -B` execution mode) is byte-identical before vs. after
  the invocation. The WO-38 protocol is a test; it must not mutate
  any harness file at runtime.

The runner does not walk `benchmark-fixtures/` or any other directory.
Payload files are read only via the caller-provided per-spec
`payload_path` strings. The snapshot writer writes only to the two
caller-provided paths (`<snapshot_dir>/<fixture_class>-batch-snapshot.json`
per spec and `batch_summary_output_path` once for the batch summary).
All writes are confined to `tempfile.TemporaryDirectory()`.

## 8. Forbidden-Language Boundary

The protocol asserts that every string scalar inside the returned
in-memory summary and every string scalar inside the on-disk batch
summary contains no phrase from:

- `BATCH_SUMMARY_FORBIDDEN_PHRASES` (extends
  `harness.review_package.FORBIDDEN_PHRASES` with `"score"` and
  `"scoring"` per the WO-35 Codex review-time hardening), scanned
  via `str(value).lower()` against the extended list.
- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`, scanned via a
  recursive walk over every string scalar.

The protocol does not introduce any new forbidden-language list; it
inherits the existing module-level lists.

## 9. OQ-056 / OQ-076 Non-Closure

OQ-056 (run artifact retention / storage policy) and OQ-076
(production artifact schema) both remain OPEN. The WO-38 protocol
exercises the existing scaffold-internal write paths under WO-27 /
DC-030 and WO-37 / DC-040; it does not author a retention rule, a
storage policy, an immutability rule, an access-control rule, a
registration mechanism, or a production artifact contract. The
on-disk files produced by the protocol are scaffold-internal and live
only inside a `tempfile.TemporaryDirectory()` that is reclaimed at
test teardown.

## 10. Forbidden Scope

The WO-38 protocol is forbidden from doing any of the following:

- Modifying any harness implementation module (including
  `harness/batch_runner.py`, `harness/dry_run.py`,
  `harness/payload_loader.py`, `harness/artifact_snapshot.py`,
  `harness/contract_runner.py`, `harness/review_package.py`,
  `harness/mock_adapter.py`, `harness/manifest_loader.py`, or
  `harness/reproducibility.py`).
- Modifying any existing test file under `harness/tests/`.
- Modifying any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Authoring a real retrieval adapter or any real retrieval / indexing
  / ranking algorithm.
- Performing real benchmark execution.
- Collecting quality / performance metrics; the asserted counts are
  contract-status observation only.
- Scoring, ranking, or declaring any configuration a winner / best /
  production-ready / recommended.
- Authoring a production manifest schema, retention policy, storage
  policy, immutability policy, access-control policy, registration
  mechanism, or production artifact contract.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding any third-party dependency.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
  All seven remain OPEN.
- Duplicating RK-039.
- Mutating corpus docs, route registry docs, validation evidence,
  source quality graph, intent trace store, candidate routes, or
  official routes.

## 11. Out-of-Scope

The following remain explicitly out of scope for WO-38 and require
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
  `harness.dry_run.run_toy_dry_run(...)`. The WO-36 review-discipline
  observation continues to hold: the `measurement_recorded` field
  accurately reports `False` under both pass and contract-failure
  paths until a future Codex packet authorizes actual measurement
  events. The WO-38 protocol does not exercise the failing-contract
  path; the WO-37 test
  `test_failing_contract_batch_still_writes_summary_snapshot`
  already covers that case.
- Persisting batch summaries to durable storage. The WO-38 protocol
  writes only inside a `tempfile.TemporaryDirectory()` reclaimed at
  test teardown; durable persistence is a future Codex decision tied
  to OQ-056.
