# ai-search - Payload-Mode Toy Dry-Run Invocation Protocol

Document type: Phase 4 / Phase 9 / Payload-mode toy dry-run invocation boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved
Work Order: WO-34

---

## 1. Purpose

This document records the scaffold-internal payload-mode toy dry-run
invocation protocol authorized under WO-34 at
`harness/tests/test_payload_dry_run_invocation.py`. The protocol
invokes `run_toy_dry_run(...)` end-to-end with the scaffold-internal
toy fixture, toy configuration, toy manifest, the matching
`benchmark-fixtures/<class>/wave-001.json` payload, and a temporary
snapshot output path, once for each admitted first-wave class
(`golden-intents`, `hard-negatives`, `boundary-violations`). It
verifies the returned review package and the on-disk snapshot file at
every boundary already locked under WO-19 / WO-23 / WO-25 / WO-26 /
WO-27 / WO-33, plus the no-mutation invariant for
`benchmark-fixtures/`.

The protocol exists so that a single self-contained `unittest` exercises
the current scaffold's full payload-mode execution path end-to-end:
fixture hash verification, configuration drift verification,
reproducibility capture, manifest load, manifest/configuration
identity match, registered-configuration observation derivation,
fixture-payload load, mock adapter invocation, contract checks,
review-package assembly, evidence attachment, and artifact snapshot
writing across all three admitted payload classes.

The protocol is scaffold-internal only. It is not real benchmark
execution. It is not real dataset use. It is not metric collection or
scoring. It is not production artifact contract authoring (OQ-076
remains OPEN). It is not run artifact retention or storage policy
authoring (OQ-056 remains OPEN). It is not architecture selection.

## 2. Scaffold-Only Scope

The WO-34 protocol touches only the four files allowed by the WO-34
packet: `harness/tests/test_payload_dry_run_invocation.py`,
`ai-search/34-payload-mode-dry-run-invocation.md`,
`ai-search/00-open-questions.md`, and
`ai-search/00-claude-task-ledger.md`.

The protocol does not:

- Modify any harness implementation module (including
  `harness/dry_run.py` and `harness/payload_loader.py`).
- Modify any existing test module under `harness/tests/`.
- Modify any existing fixture file under `harness/tests/fixtures/`.
- Modify any file under `benchmark-fixtures/` (no payload file, no
  `.gitkeep`, no README).
- Author any production manifest schema, production artifact contract,
  registration mechanism, retention policy, or storage policy.

The test module is Python standard library only beyond harness-internal
imports. It imports only `hashlib`, `json`, `os`, `tempfile`, and
`unittest` from the stdlib plus `harness.dry_run.run_toy_dry_run`,
`harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`, and
`harness.review_package.FORBIDDEN_PHRASES`.

## 3. Exact Invocation Inputs

For each admitted class, the protocol invokes `run_toy_dry_run(...)`
with the following inputs:

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
- `payload_path` = path to
  `benchmark-fixtures/<class>/wave-001.json` for the class being
  exercised.
- `expected_fixture_class` = the class name (matching the directory
  name).
- `snapshot_output_path` = a path inside a
  `tempfile.TemporaryDirectory()` whose lifetime is bounded by the
  test method. The directory is deleted by
  `TemporaryDirectory.__exit__` at the end of the subTest.

No other input is supplied. `contract_checks` is omitted so the
scaffold-internal default toy checks (WO-23 / WO-25-extended) are
used.

## 4. Class Coverage

The protocol exercises all three admitted first-wave payload classes
in a `unittest.subTest` loop:

- `golden-intents`
- `hard-negatives`
- `boundary-violations`

The three excluded classes (`latency-profiles`, `update-profiles`,
`adversarial`) are not exercised; their subdirectories remain
`.gitkeep`-only per WO-31 / DC-034. A future Codex packet may admit
one or more excluded classes; WO-34 does not preempt that decision.

## 5. Event-Order Assertions

For each invocation, the protocol locates the first occurrence of
each of the following four events in the returned package's
`all_events` and asserts the strict ordering:

    registered_configuration_observed
      < fixture_payload_loaded
      < mock_adapter_invoked
      < snapshot_written

This ordering extends the WO-25 / WO-26 / WO-27 invariant
(`manifest_loaded` < `registered_configuration_observed` <
`mock_adapter_invoked` < `snapshot_written`) under WO-33 to include
`fixture_payload_loaded` between `registered_configuration_observed`
and `mock_adapter_invoked`.

The protocol also asserts that no `measurement_recorded` event
appears, because the toy default contract checks all pass and no
disqualification occurs.

## 6. Snapshot Boundary

For each invocation, the protocol asserts the following snapshot
properties:

- The snapshot file exists at the caller-provided
  `snapshot_output_path`.
- The returned `snapshot_evidence` carries `output_path` equal to the
  caller-provided path, `sha256` equal to the hex SHA-256 of the
  file bytes, and `byte_length` equal to the file's length in bytes.
- The on-disk snapshot file contains `payload_evidence` because
  payload evidence is attached before snapshot writing (per WO-33
  Section 3 step 14).
- The on-disk snapshot file does not contain `snapshot_evidence`
  because that key is attached only after the snapshot is written
  (per WO-27 / DC-030 step 15).

The protocol does not assert anything about the snapshot file's
internal schema beyond the keys above. It does not author a schema, a
retention policy, an immutability rule, or any other artifact contract
surface.

## 7. No-Mutation Boundary

A second test method, `PayloadModeDryRunNoMutationTest`, captures the
`benchmark-fixtures/` inventory (relative-path-to-SHA-256 map) before
the three invocations and asserts after the invocations that:

- The set of relative paths under `benchmark-fixtures/` is unchanged
  (same files, no additions, no removals).
- Each file's SHA-256 is unchanged (no payload mutation, no
  `.gitkeep` mutation, no README mutation).
- Every snapshot file was written under a `tempfile.TemporaryDirectory()`
  path; none was written under `benchmark-fixtures/`.

This binds the invocation's write surface to the caller-provided
temporary directories. The temporary directories are deleted by
`TemporaryDirectory.__exit__` at the end of each subTest, so the
protocol leaves no on-disk artifact behind.

## 8. Forbidden Language And Claim-Phrase Boundary

The protocol scans the returned package for two distinct sets of
forbidden phrases:

- `harness.review_package.FORBIDDEN_PHRASES`: scanned across the
  returned package (via `str(package).lower()`). No
  selection / recommendation / winner / best / production-ready /
  ranking phrase may appear anywhere in the package's string
  representation.
- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`: scanned
  recursively across `payload_evidence` only. No positive claim of
  validation evidence, route trust, benchmark result, production
  readiness, or architecture selection may appear in
  `payload_evidence`.

The WO-33 review-time hardening already enforces both scans at
evidence-attachment time inside `harness/dry_run.py`. The WO-34
protocol re-asserts both checks at the integration level so that any
future regression that smuggles a claim phrase into `payload_evidence`
or any other package field is caught at the invocation surface.

## 9. Forbidden Scope

The WO-34 protocol is forbidden from doing any of the following:

- Modifying any harness implementation module (including
  `harness/dry_run.py`, `harness/payload_loader.py`, and every other
  module under `harness/`).
- Modifying any existing test module under `harness/tests/`.
- Modifying any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Performing benchmark execution, collecting metrics, scoring,
  ranking, or any retrieval / indexing / ranking implementation.
- Implementing a real retrieval adapter or a real fixture loader.
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

## 10. Not Benchmark Execution; Not Scoring; Not Validation Evidence; Not Architecture Selection

The WO-34 protocol is explicitly:

- **Not benchmark execution.** The protocol invokes the toy dry-run,
  which consumes only scaffold-internal inputs (the toy fixture, toy
  configuration, toy manifest, and the synthetic WO-31 payload files).
  No real benchmark dataset is read. No retrieval call is made. No
  metric is collected.
- **Not scoring.** The protocol does not produce any metric, score,
  ranking, or aggregate signal. The toy default contract checks
  pass; no disqualification occurs; no `measurement_recorded` event
  appears.
- **Not validation evidence.** The loaded payload remains observation
  only. No payload entry constitutes recorded validation evidence
  against any candidate or official route. The WO-32 loader and the
  WO-33 integration both attach the payload at the evidence boundary
  rather than at any validation surface.
- **Not architecture selection.** The Indexing Excellence Gate
  (`00-controller-checklist.md` Section K) continues to govern
  selection. The protocol makes no architecture, vendor, library,
  ANN backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production-system claim. Future real
  adapter, real benchmark execution, real fixture loader registration,
  or architecture selection each require separate Codex-authored
  Work Orders whose scope, allowed files, required content, forbidden
  scope, acceptance criteria, and evidence requirements are explicit
  at issue time.
