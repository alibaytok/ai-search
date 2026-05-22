# ai-search - Toy Dry-Run Snapshot Invocation Protocol

Document type: Phase 4 / Phase 9 / Toy dry-run snapshot invocation boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-28

---

## 1. Purpose

This document records the scaffold-internal toy dry-run snapshot
invocation protocol authorized under WO-28 at
`harness/tests/test_toy_snapshot_invocation.py`. The protocol exercises
`run_toy_dry_run(...)` end-to-end with the existing scaffold-internal
toy fixture, toy configuration, toy manifest, and a temporary snapshot
output path, and verifies the assembled review package and the on-disk
snapshot file at every boundary already locked under WO-19 / WO-23 /
WO-25 / WO-26 / WO-27.

The protocol exists so that a single self-contained `unittest` exercises
the current scaffold's full toy execution path - fixture hash
verification, configuration drift verification, reproducibility capture,
manifest load, manifest/configuration identity match, registered
configuration observation derivation, mock adapter invocation, contract
checks, review package assembly, evidence attachment, and artifact
snapshot writing - and proves that the integrated path produces the
expected event ordering, the expected evidence attachments, and a
deterministic on-disk snapshot whose hash and byte length match the
caller-visible metadata.

The protocol is scaffold-internal only. It is not real benchmark
execution. It is not real dataset use. It is not production artifact
contract authoring (OQ-076 remains OPEN). It is not run artifact
retention or storage policy authoring (OQ-056 remains OPEN). It is not
architecture selection.

## 2. Toy-Only Invocation Scope

The WO-28 protocol touches only the four files allowed by the WO-28
packet: `harness/tests/test_toy_snapshot_invocation.py`,
`ai-search/28-toy-dry-run-snapshot-invocation.md`,
`ai-search/00-open-questions.md`, and
`ai-search/00-claude-task-ledger.md`.

The protocol does not:

- Modify any harness implementation module (`harness/dry_run.py`,
  `harness/artifact_snapshot.py`, `harness/manifest_loader.py`,
  `harness/mock_adapter.py`, `harness/event_log.py`,
  `harness/fixture_loader.py`, `harness/config_loader.py`,
  `harness/contract_runner.py`, `harness/reproducibility.py`,
  `harness/review_package.py`, or `harness/__init__.py`).
- Modify any existing test module under `harness/tests/`.
- Modify any existing fixture file under `harness/tests/fixtures/`. The
  existing `toy_scaffold_fixture.json`, `toy_scaffold_config.json`, and
  `toy_retrieval_manifest.json` are read by the test but not modified.
- Modify any file under `benchmark-fixtures/`. The empty fixture
  skeleton authorized under WO-20 remains untouched.
- Author any production manifest schema, production artifact contract,
  registration mechanism, retention policy, or storage policy.

The test module is Python standard library only beyond harness-internal
imports. It imports only `hashlib`, `json`, `os`, `tempfile`, and
`unittest` from the stdlib plus `harness.dry_run.run_toy_dry_run` and
`harness.review_package.FORBIDDEN_PHRASES`.

## 3. Exact Invocation Inputs

The protocol invokes `run_toy_dry_run(...)` with the following
scaffold-internal inputs:

- `fixture_path` = path to `harness/tests/fixtures/toy_scaffold_fixture.json`.
- `fixture_sha256` = the SHA-256 hex digest computed from the toy
  fixture file at test time.
- `config_path` = path to `harness/tests/fixtures/toy_scaffold_config.json`.
- `registered_config` = the parsed JSON content of the toy configuration
  file (loaded once at test time).
- `deterministic_seed` = `42` (an arbitrary scaffold-internal fixed
  integer; not a production seed).
- `manifest_path` = path to `harness/tests/fixtures/toy_retrieval_manifest.json`.
- `expected_manifest_id` = `"toy-scaffold-manifest"`.
- `snapshot_output_path` = a path inside a
  `tempfile.TemporaryDirectory()` whose lifetime is bounded by the test
  method. The directory is deleted by `TemporaryDirectory.__exit__` at
  the end of the test.

No other input is supplied. `contract_checks` is omitted so the
scaffold-internal default toy checks (WO-23 / WO-25-extended) are used.

## 4. Exact Event Order

The invocation's `all_events` (as exposed in the returned package after
WO-27's post-snapshot event-view refresh) is required to contain the
following event types in the following strict order:

    fixture_loaded
      < configuration_loaded
      < manifest_loaded
      < registered_configuration_observed
      < mock_adapter_invoked
      < snapshot_written

The protocol verifies the ordering by locating the index of each event
type's first occurrence in `all_events` and asserting strict-less-than
between consecutive indices. The protocol also verifies that no
`measurement_recorded` event appears, because the toy default contract
checks all pass and no disqualification occurs.

The protocol does not enumerate the per-plane `adapter_plane_present`
events; their per-event payloads are exercised in WO-23 and WO-26 tests.
The protocol's only ordering claim is over the six events listed above.

## 5. Snapshot Artifact Boundary

The protocol verifies the snapshot artifact at the boundary level only:

- The snapshot file exists at the caller-provided `snapshot_output_path`.
- The returned `snapshot_evidence` carries `output_path` equal to the
  caller-provided path, `sha256` equal to the hex SHA-256 of the file
  bytes, and `byte_length` equal to the file's length in bytes.
- The on-disk snapshot file does not contain a `snapshot_evidence` key
  (that key is attached only after the file is written; see WO-27 /
  DC-030 step 15).
- The on-disk snapshot file does contain `adapter_output_evidence`,
  `manifest_evidence`, and `registered_configuration_observation`
  (all attached before the snapshot was written).
- Neither the returned in-memory package nor the on-disk snapshot file
  contains any phrase from `harness.review_package.FORBIDDEN_PHRASES`.

The protocol does not assert anything about the snapshot's internal
schema beyond the keys above. It does not author a schema, a retention
policy, an immutability rule, or any other artifact contract surface.
Production artifact contracts remain owned by Codex under OQ-076; run
artifact retention/storage policy remains owned by Codex under OQ-056.
Neither is closed by WO-28.

## 6. Temporary-Output-Only Boundary

The protocol's second test method captures the `benchmark-fixtures/`
inventory before the invocation, invokes `run_toy_dry_run(...)` with
`snapshot_output_path` inside a `tempfile.TemporaryDirectory()`, and
asserts after the invocation that:

- The snapshot file exists under the temporary directory.
- The snapshot file path does not start with the project's
  `benchmark-fixtures/` path.
- The `benchmark-fixtures/` inventory (sorted relative paths) is
  unchanged before vs. after the invocation.

This binds the invocation's write surface to the caller-provided
temporary directory and reaffirms that no harness module writes under
`benchmark-fixtures/`. The temporary directory is deleted by
`TemporaryDirectory.__exit__` at the end of the test, so the test
leaves no on-disk artifact behind.

## 7. Forbidden Scope

The WO-28 protocol is forbidden from doing any of the following:

- Modifying any harness implementation module. If a bug is discovered
  during invocation, the protocol must stop and report it rather than
  patching any module under `harness/`. (WO-28 allows no harness module
  in its allowed files.)
- Authoring a production manifest schema, production artifact schema,
  archive format, filename convention, directory layout, retention rule,
  storage-class rule, immutability mechanism, access-control rule,
  signature scheme, or version-pinning scheme.
- Closing OQ-056 (run artifact retention/storage policy), OQ-076
  (production artifact contracts), OQ-057 (configuration registration
  authority), OQ-070 (broader scope), OQ-075 (dependency policy beyond
  the first scaffold), OQ-035 (golden intent set construction), or
  OQ-049 (broader dataset suite ownership).
- Writing or mutating any file under `benchmark-fixtures/`, or consuming
  any benchmark fixture payload. Inventory-only inspection is allowed
  for the WO-28 test's before/after no-mutation assertion.
- Performing real benchmark execution, consuming real benchmark
  datasets, or using any production-like state.
- Authoring a real retrieval, indexing, or ranking implementation, or
  contacting any retrieval system.
- Selecting any vendor, vector DB, ANN backend, reranker, retrieval
  family, ablation cell, multi-stage variant, or architecture.
- Adding third-party dependencies beyond the Python standard library.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Authoring metric thresholds, quality or performance scoring, ranking
  formulas, runtime compile internals, or validation framework
  implementations.
- Writing to corpus docs, route registry docs, source quality graph,
  validation evidence ledger, intent trace store, candidate routes, or
  official routes.
- Modifying any file outside the four files allowed under WO-28.

## 8. Relationship To WO-27, OQ-056, And OQ-076

The protocol sits inside the constraint surface established by WO-27 and
prior packets:

- `27-scaffold-run-artifact-snapshot.md` (WO-27 / DC-030) named the
  scaffold-internal artifact snapshot writer at
  `harness/artifact_snapshot.py` and its optional wiring into
  `harness/dry_run.py`. WO-28 exercises that wiring with the toy fixture
  set; it does not add to the writer or the wiring.
- `26-toy-registered-configuration-flow.md` (WO-26 / DC-029) and
  `25-manifest-loader-dry-run-integration.md` (WO-25 / DC-028) named
  the registered configuration observation step and the optional
  manifest loader integration. WO-28 exercises both with the toy
  manifest; it does not add to either.
- `23-mock-adapter-dry-run-integration.md` (WO-23 / DC-026) and
  `21-retrieval-adapter-contract.md` continue to bound adapter
  behavior. WO-28 exercises the mock adapter as integrated under WO-23;
  it does not author or call any real adapter.
- OQ-056 (run artifact retention/storage policy) remains OPEN. WO-28
  does not author any retention or storage policy. The snapshot file's
  lifetime is bounded by the test's `tempfile.TemporaryDirectory()`;
  this is a test-local cleanup mechanism, not a retention policy.
- OQ-076 (production artifact contracts) remains OPEN. WO-28 does not
  author any production artifact contract. The snapshot file format is
  the deterministic UTF-8 JSON serialization defined by the WO-27 writer
  and no broader contract is authored or implied.
- `00-controller-checklist.md` Section K (Indexing Excellence Gate)
  continues to govern selection. The invocation makes no architecture,
  vendor, library, ANN backend, reranker, or production-system claim.

## 9. Not Real Benchmark Execution; Not Architecture Selection

The WO-28 protocol is explicitly not real benchmark execution. It
satisfies no prerequisite recorded in `14-benchmark-execution-plan.md`
Pre-Run Preparation Boundaries A or B. It does not produce metrics,
scores, thresholds, or rankings. It does not record validation evidence.
It does not constitute Stage 0 through Stage 5 of the benchmark
execution flow.

The WO-28 protocol is explicitly not architecture selection. The
Indexing Excellence Gate (`00-controller-checklist.md` Section K)
continues to govern selection. The protocol makes no architecture,
vendor, library, ANN backend, reranker, or production-system claim. Any
future real adapter, real registration mechanism, real benchmark
execution, or architecture selection requires separate Codex-authored
Work Orders whose scope, allowed files, required content, forbidden
scope, acceptance criteria, and evidence requirements are explicit at
issue time.

## 10. Out Of Scope

This document and the WO-28 protocol are scaffold-internal only. Neither
authorizes:

- A real retrieval, indexing, or ranking implementation.
- A vendor, library, index family, retrieval family, ANN backend,
  reranker, ablation cell, multi-stage variant, or architecture choice.
- A benchmark execution against `benchmark-fixtures/` content.
- A production manifest schema, registration mechanism, registration
  authority scheme, or artifact contract.
- A run artifact retention or storage policy.
- A metric, threshold, weight, score, or ranking formula.
- A runtime compile design.
- A validation framework implementation.
- A treatment of the invocation output or the on-disk snapshot file as
  benchmark evidence, validation evidence, registered production
  configuration, dataset authorization, or architecture authorization.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.
