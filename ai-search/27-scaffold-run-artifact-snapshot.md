# ai-search - Scaffold Run Artifact Snapshot Boundary

Document type: Phase 4 / Phase 9 / Scaffold run artifact snapshot boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-27

---

## 1. Purpose

This document records the scaffold-internal run artifact snapshot writer
authorized under WO-27 at `harness/artifact_snapshot.py` and its optional
wiring into the toy dry-run at `harness/dry_run.py`. The writer's only
role is to make an already-assembled toy dry-run review package
serializable to disk as a deterministic UTF-8 JSON file when a caller
chooses to do so.

The writer exists so that scaffold-internal tests, harness self-checks,
and future Codex packets can persist a single dry-run's review package
to a caller-chosen path without authoring any production artifact
contract and without selecting any architecture. The writer is the
minimum surface that makes scaffold artifacts persistable; it does not
author a production artifact schema, a run artifact retention or
storage policy, a directory layout, a filename convention, an archive
format, or any production registration mechanism.

The writer is scaffold-internal only. It is not a production artifact
contract (OQ-076 remains open). It is not a run artifact retention or
storage policy decision (OQ-056 remains open). It is not benchmark
execution. It is not architecture selection.

## 2. Scaffold-Only Artifact Snapshot Boundary

The WO-27 scaffold touches only the seven files allowed by the WO-27
packet: `harness/artifact_snapshot.py`,
`harness/tests/test_artifact_snapshot.py`, `harness/dry_run.py`,
`harness/tests/test_dry_run.py`,
`ai-search/27-scaffold-run-artifact-snapshot.md`,
`ai-search/00-open-questions.md`, and
`ai-search/00-claude-task-ledger.md`.

The scaffold does not:

- Modify the mock adapter, the manifest loader, the fixture loader, the
  configuration loader, the event log, the contract runner, the
  reproducibility recorder, the review-package assembler, or any
  existing test module other than `test_dry_run.py`.
- Modify any existing fixture file under `harness/tests/fixtures/`.
- Modify any file under `benchmark-fixtures/`. The empty fixture
  skeleton authorized under WO-20 remains untouched.
- Author a production artifact schema, archive format, filename
  convention, directory layout, retention rule, immutability rule, or
  access-control rule.
- Author a production registration mechanism, a registration authority
  scheme, or any artifact-side production contract.

The writer is Python standard library only. `harness/artifact_snapshot.py`
imports only `hashlib`, `json`, and `harness.review_package.FORBIDDEN_PHRASES`.

## 3. Exact Write Order

The writer exposes a single public function:

    write_scaffold_snapshot(package, output_path, event_log=None)

The function performs the following ordered steps:

1. Type check the package. If `package` is not a `dict`, record an
   `event_log.halt("snapshot_non_object_package", ...)` event (when
   `event_log` is provided) and raise `NonObjectSnapshotPackage` before
   any file write occurs.
2. Forbidden-language scan. Walk every string scalar inside the package
   (keys and values, recursively) and check it against
   `harness.review_package.FORBIDDEN_PHRASES`. On any hit, record an
   `event_log.halt("snapshot_forbidden_language", ...)` event (when
   `event_log` is provided) and raise
   `ForbiddenLanguageInSnapshotPackage` before any file write occurs.
3. Deterministic serialization. Serialize the package via
   `json.dumps(package, sort_keys=True, ensure_ascii=True)`. On
   serialization failure, record an `event_log.halt(
   "snapshot_write_error", ...)` event (when `event_log` is provided)
   and raise `SnapshotWriteError`.
4. Write the encoded UTF-8 bytes to `output_path` using
   `open(output_path, "wb")`. On `OSError`, record an
   `event_log.halt("snapshot_write_error", ...)` event (when
   `event_log` is provided) and raise `SnapshotWriteError`.
5. Compute the SHA-256 hex digest of the written bytes.
6. Record a `snapshot_written` event into `event_log` (when provided)
   with `output_path`, `sha256`, and `byte_length`.
7. Return a minimal metadata dict containing `output_path`, `sha256`,
   and `byte_length`.

The writer is purely functional with respect to the package contents;
it does not modify the input package and does not perform any retrieval,
indexing, ranking, network, or mutation of production-like state.

The optional dry-run wiring runs the writer as the final step of the
WO-19 / WO-23 / WO-25 / WO-26 module composition order. The new step 15
is:

15. If `snapshot_output_path` was provided to `run_toy_dry_run(...)`,
    invoke `write_scaffold_snapshot(package, snapshot_output_path,
    event_log=event_log)` after package assembly and all WO-23 / WO-25
    / WO-26 evidence attachment, and attach the returned metadata as
    `snapshot_evidence` on the returned package. Refresh the returned
    package's `all_events` and `event_count` so the `snapshot_written`
    event recorded by the writer is observable to the caller. When
    omitted, this step is skipped and no file is written.

The snapshot file therefore captures the package with adapter,
manifest, and registered configuration observation evidence already in
place; the `snapshot_evidence` key is attached to the in-memory
returned package only after the snapshot is written, so the snapshot
file itself does not contain `snapshot_evidence`. The returned package's
event view is refreshed after the write; the snapshot file itself does
not include the post-write `snapshot_written` event.

## 4. Allowed Input

The writer accepts exactly one input class: an already-assembled
dry-run review package produced by `harness/review_package.assemble(...)`
and optionally augmented by `run_toy_dry_run(...)` with
`adapter_output_evidence`, `manifest_evidence`, and
`registered_configuration_observation`. Any Python `dict` whose values
are JSON-serializable and whose string scalars contain no forbidden
phrase is accepted at boundary level. Non-`dict` inputs and inputs
carrying forbidden language are rejected before any file write.

The writer does not consume any other input class. In particular, it
does not consume:

- Raw fixtures, raw configurations, or raw manifests.
- Production benchmark datasets (no file under `benchmark-fixtures/` is
  ever read by the writer).
- Live retrieval state, corpus state, route registry state, source
  quality graph state, validation evidence ledger state, or intent
  trace store state.
- Unqualified internet or public content.

The optional `event_log` argument is a `harness.event_log.EventLog`
instance owned by the caller. The writer never creates an event log on
its own.

## 5. Output Metadata Boundary

On success, the writer returns a minimal metadata `dict`:

    {
        "output_path": <the caller-provided output path verbatim>,
        "sha256": <hex SHA-256 of the written file bytes>,
        "byte_length": <length of the written file in bytes>,
    }

The metadata is intentionally minimal. It does not include retention,
storage class, archival policy, encryption status, access-control
status, ingestion-time provenance, version-pinning, signature, or any
field that would imply a production artifact contract. The metadata is
fit only for scaffold-internal sanity checks.

When the writer is invoked via `run_toy_dry_run(snapshot_output_path=...)`,
the same metadata dict is attached to the returned in-memory review
package under the key `snapshot_evidence`. The snapshot file on disk
does not contain `snapshot_evidence` itself, since that key is added
only after the file is written.

## 6. Halt And Rejection Behavior

The writer rejects at every named boundary. Each rejection is both an
exception raised to the caller and (when `event_log` is provided) an
explicit halt event recorded into the event log. No rejection is silent.

| Condition | Exception | Halt event reason |
|-----------|-----------|-------------------|
| `package` is not a `dict` | `NonObjectSnapshotPackage` | `snapshot_non_object_package` |
| Forbidden phrase appears anywhere in package strings | `ForbiddenLanguageInSnapshotPackage` | `snapshot_forbidden_language` |
| JSON serialization fails (e.g., non-serializable value) | `SnapshotWriteError` | `snapshot_write_error` |
| OS write failure (e.g., missing parent directory) | `SnapshotWriteError` | `snapshot_write_error` |

In all rejection cases, no snapshot file is written and no
`snapshot_written` event is recorded. The check order is fixed (type
check, forbidden-language scan, serialization, file write, hash, event,
return) so a forbidden-language reject occurs before any file system
contact and a serialization reject occurs before any file system
contact.

When wired through `run_toy_dry_run(...)`, all prior halt boundaries
remain in force: incomplete manifest parameters, fixture hash mismatch,
configuration drift, manifest loader rejections, and
manifest/configuration identity mismatch all halt before the snapshot
step is reached. Contract failure still produces a package, so the
snapshot step still writes the package when `snapshot_output_path` is
provided.

## 7. Relationship To OQ-056 And OQ-076

OQ-056 (run artifact retention/storage policy) and OQ-076 (production
artifact contracts) both remain OPEN. WO-27 does not author either:

- The writer enforces no retention rule, no storage class, no
  immutability mechanism, and no access-control rule. The caller
  chooses the `output_path` and is responsible for everything beyond
  the single file's byte content and SHA-256. OQ-056 remains the
  authoritative question for those policies and is not closed by
  WO-27.
- The writer authors no production artifact schema, no field-type
  registry, no provenance scheme, no version-pinning scheme, no
  signature scheme, and no archive format. The only structure committed
  by WO-27 is the minimal three-field metadata dict returned to the
  caller (`output_path`, `sha256`, `byte_length`), which is fit only for
  scaffold-internal sanity checks. OQ-076 remains the authoritative
  question for production artifact contracts and is not closed by
  WO-27.

The writer's existence does not preempt either decision. A future Codex
packet that authors a real artifact contract or a real run-artifact
retention policy will do so explicitly; the WO-27 scaffold can be
replaced or wrapped by that future packet without claiming any prior
authority by use.

## 8. Forbidden Scope

The WO-27 scaffold is forbidden from doing any of the following:

- Authoring a production artifact schema, archive format, filename
  convention, directory layout, retention rule, storage-class rule,
  immutability mechanism, access-control rule, signature scheme, or
  version-pinning scheme.
- Closing OQ-056 (run artifact retention/storage policy) or OQ-076
  (production artifact contracts), or any other open question.
- Performing real benchmark execution, consuming real benchmark
  datasets, or reading any file under `benchmark-fixtures/`.
- Authoring a real retrieval, indexing, or ranking implementation.
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
- Mutating any file under `benchmark-fixtures/`.
- Modifying any file outside the seven files allowed under WO-27.

## 9. Not Benchmark Execution; Not Production Artifact Contract; Not Architecture Selection

The WO-27 scaffold is explicitly not benchmark execution. It satisfies
no prerequisite recorded in `14-benchmark-execution-plan.md` Pre-Run
Preparation Boundaries A or B. It does not produce metrics, scores,
thresholds, or rankings. It does not record validation evidence. It
does not constitute Stage 0 through Stage 5 of the benchmark execution
flow.

The WO-27 scaffold is explicitly not a production artifact contract.
The returned metadata is intentionally minimal and the snapshot file
format is intentionally a single deterministic JSON serialization of an
in-memory package; nothing about the writer commits to production
schema substance. Production artifact contracts remain owned by Codex
under OQ-076.

The WO-27 scaffold is explicitly not architecture selection. The
Indexing Excellence Gate (`00-controller-checklist.md` Section K)
continues to govern selection. The writer makes no architecture,
vendor, library, ANN backend, reranker, or production-system claim.
Any future production artifact contract, run artifact retention/storage
policy, real benchmark execution, or architecture selection requires
separate Codex-authored Work Orders whose scope, allowed files,
required content, forbidden scope, acceptance criteria, and evidence
requirements are explicit at issue time.

## 10. Out Of Scope

This document and the WO-27 scaffold are scaffold-internal only.
Neither authorizes:

- A real retrieval, indexing, or ranking implementation.
- A vendor, library, index family, retrieval family, ANN backend,
  reranker, ablation cell, multi-stage variant, or architecture choice.
- A benchmark execution against `benchmark-fixtures/` content.
- A production artifact schema, archive format, retention policy, or
  storage policy.
- A registration mechanism or registration authority scheme.
- A metric, threshold, weight, score, or ranking formula.
- A runtime compile design.
- A validation framework implementation.
- A treatment of the snapshot file as benchmark evidence, validation
  evidence, registered production configuration, dataset
  authorization, or architecture authorization.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.
