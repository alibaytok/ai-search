# ai-search - Manifest Loader Dry-Run Integration

Document type: Phase 4 / Phase 9 / Manifest loader dry-run integration boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-25

---

## 1. Purpose

This document records the integration of the scaffold-internal manifest
loader (authored under WO-24 / DC-027 at `harness/manifest_loader.py`)
into the toy end-to-end dry-run (authored under WO-19 / DC-022 and
extended under WO-23 / DC-026 at `harness/dry_run.py`). The integration
makes the WO-24 manifest-consumption boundary observable end-to-end with
the existing mock adapter integration, without authoring a production
manifest schema, without authorizing real benchmark execution, and
without selecting any architecture.

The integration is scaffold-internal only. It does not introduce a real
retrieval adapter, does not consume `benchmark-fixtures/` content, does
not record validation evidence, does not promote, demote, revoke, or
retire any route, and does not declare any configuration a winner, best,
recommended, or production-ready.

## 2. Scaffold-Only Scope

The integration touches only `harness/dry_run.py` and
`harness/tests/test_dry_run.py`. It does not modify `harness/manifest_loader.py`,
the mock adapter, the fixture loader, the configuration loader, the
event log, the contract runner, the reproducibility recorder, the
review-package assembler, the existing toy fixtures
(`toy_scaffold_fixture.json`, `toy_scaffold_config.json`,
`toy_retrieval_manifest.json`), or any other test module. It does not
modify any file under `benchmark-fixtures/`. The empty fixture skeleton
authorized under WO-20 remains untouched.

The dry-run continues to be a Python function (no CLI, no entry point,
no shell wrapper) consuming Python-stdlib-only inputs.

## 3. Exact Integration Order

The dry-run module composition order recorded under WO-19 and extended
under WO-23 is extended again under WO-25. Steps 3 through 6 and 8
through 12 retain their meaning; steps 1, 2, and 7 are new under WO-25.

1. Create EventLog.
2. Validate manifest parameter consistency. If exactly one of
   `manifest_path` / `expected_manifest_id` is provided, record a
   `manifest_parameters_incomplete` halt event and raise
   `IncompleteManifestParameters` before any further work. No fixture or
   configuration loading is performed in this case.
3. Load and SHA-256 hash-verify the toy fixture via
   `harness/fixture_loader.py`. Fixture hash mismatch raises
   `FixtureHashMismatch` and prevents both manifest loading and adapter
   invocation.
4. Load and drift-check the toy configuration via
   `harness/config_loader.py`. Configuration drift raises
   `ConfigurationDrift` and prevents both manifest loading and adapter
   invocation.
5. Capture reproducibility evidence via `harness/reproducibility.py`.
6. Record the loaded fixture hash and the configuration identifier into
   the reproducibility record.
7. If both manifest parameters are provided, invoke the scaffold-internal
   manifest loader via `load_manifest(manifest_path, expected_manifest_id,
   event_log)` from `harness/manifest_loader.py`. On success, the loader
   records exactly one `manifest_loaded` event into the EventLog. Manifest
   loader rejection paths raise the named exceptions from WO-24 and
   prevent adapter invocation.
8. Invoke the scaffold-internal mock adapter via
   `run_mock_adapter(fixture, configuration)` from
   `harness/mock_adapter.py`. Record a `mock_adapter_invoked` event into
   the EventLog with the adapter kind, the `selection_made` posture, the
   explicit `empty_planes` list, and the per-plane entry counts. Record
   one `adapter_plane_present` event per plane with the plane name, the
   entry count, and the `is_empty` marker.
9. Create `ContractRunner` and register the scaffold-internal toy
   contract checks (or a test-supplied override).
10. Derive a toy response from the fixture, the configuration, and the
    adapter output.
11. Run the contract checks against the toy response.
12. Assemble the human review package via `harness/review_package.py`,
    attach `adapter_output_evidence` to the package, and, when a manifest
    was loaded, attach `manifest_evidence` as well. Re-scan each attached
    structure for forbidden language using
    `harness.review_package.FORBIDDEN_PHRASES`.

## 4. Optional Manifest Mode Vs Default No-Manifest Mode

The integration adds two optional keyword parameters to
`run_toy_dry_run(...)`: `manifest_path` and `expected_manifest_id`. The
modes are both-or-neither:

- **Default no-manifest mode**: neither parameter is provided. The
  existing WO-23 dry-run behavior is preserved exactly. No
  `manifest_loaded` event is recorded; no `manifest_evidence` key is
  attached to the returned review package; no manifest loader call is
  made. Every WO-19 and WO-23 invariant carries forward unchanged.
- **Manifest mode**: both parameters are provided. The manifest loader
  is invoked exactly once after reproducibility capture and before the
  mock adapter is invoked. On success, the package carries both
  `adapter_output_evidence` (WO-23) and `manifest_evidence` (WO-25).
- **Incomplete-parameter mode is rejected**: if exactly one of the two
  parameters is provided, an `IncompleteManifestParameters` exception is
  raised after a `manifest_parameters_incomplete` halt event is recorded.
  No fixture loading, configuration loading, manifest loading, or
  adapter invocation occurs.

## 5. Halt Points

Halt behavior follows DC-020 (halt on contract failure halts measurement
for the failing configuration with an explicit halt event; no silent
continuation) and extends the WO-19 and WO-23 halt boundary:

- Incomplete manifest parameters raise `IncompleteManifestParameters`
  before any other loading. A `manifest_parameters_incomplete` halt event
  records which of the two parameters was present.
- Fixture hash mismatch raises `FixtureHashMismatch` from the fixture
  loader before manifest loading or adapter invocation.
- Configuration drift raises `ConfigurationDrift` from the configuration
  loader before manifest loading or adapter invocation.
- Manifest loader rejection paths (`MalformedManifestJSON`,
  `NonObjectManifest`, `MissingManifestScaffoldMarker`,
  `MissingRequiredManifestField`, `ManifestIdMismatch`,
  `ManifestDeclaresSelection`, `ForbiddenLanguageInManifest`) raise from
  `harness/manifest_loader.py` before the mock adapter is invoked. The
  manifest loader records the corresponding halt event into the EventLog
  before raising (see `24-retrieval-configuration-manifest-scaffold.md`
  Section 6 for the condition-to-reason table).
- Contract failure disqualifies the configuration via `ContractRunner`.
  The runner records an explicit halt event with
  `reason="contract_check_failed"` and stops further measurement against
  the failing configuration. Because the adapter is invoked after
  manifest loading and before contract checks run, the manifest evidence
  (when a manifest was loaded) and the adapter evidence are still
  attached to the assembled package; the disqualification is surfaced via
  `disqualified_configurations` and `contract_checks_failed` in the same
  package.
- A failure of the post-assemble forbidden-language re-scan over the
  adapter evidence or the manifest evidence raises
  `ForbiddenLanguageInReviewPackage` from `harness.review_package`. The
  package is not returned; the run is treated as a halt at the
  integration surface. The mock adapter's own forbidden-language test
  (WO-22) and the manifest loader's forbidden-language test (WO-24)
  prevent this in normal operation.

No silent continuation against a halted run is permitted at any of the
halt points above.

## 6. Manifest Evidence Boundary

When a manifest is loaded, the assembled review package carries a
`manifest_evidence` field containing:

- `manifest_id`: the loaded manifest's identifier.
- `adapter_kind`: the adapter kind named in the manifest.
- `configuration_id`: the configuration identifier named in the manifest.
- `planes_declared`: a copy of the manifest's declared plane list.
- `selection_made`: the manifest's non-selection posture (always `False`
  for an admitted manifest).
- `evidence_note`: a free-text note recording that the structure is
  scaffold-internal toy manifest evidence per
  `24-retrieval-configuration-manifest-scaffold.md`, and is not a
  production manifest registration, not validation evidence, and not
  architecture selection.

The structure is harness-internal observation only. It is not a
production manifest registration, not a registration authority
declaration, and not architecture selection. It is re-scanned for
forbidden language using `harness.review_package.FORBIDDEN_PHRASES`
before attachment.

In addition to `manifest_evidence`, the package's `all_events` includes
the `manifest_loaded` event recorded by the loader on success. The event
contains `path`, `manifest_id`, `adapter_kind`, `configuration_id`, and
a copy of `planes_declared` per WO-24.

## 7. Review Package Boundary

The review package returned by the dry-run is the harness-internal
package assembled by `harness/review_package.py`. Under WO-25 it carries,
in addition to the WO-19 and WO-23 fields (`summary`, `event_count`,
`all_events`, `halt_events`, `contract_checks_passed`,
`contract_checks_failed`, `disqualified_configurations`,
`reproducibility`, `selection_made`, `selection_note`,
`adapter_output_evidence`):

- `manifest_evidence` (present only when a manifest was loaded): the
  structure described in Section 6.
- `manifest_loaded` event in `all_events` (present only when a manifest
  was loaded): the loader-recorded success event.

The package format remains harness-internal and is not a production
artifact contract; production artifact contracts remain owned by Codex
under OQ-076 (which remains open). The package continues to be subject
to the forbidden-language scan in `harness/review_package.py`; the
adapter evidence and the manifest evidence are additionally re-scanned
by the integration using the same `FORBIDDEN_PHRASES` constant so that
the scans cannot drift.

The package does not propose, recommend, rank, or otherwise select any
configuration. It does not declare a configuration a winner, best, or
production-ready. It does not treat manifest content as validation
evidence, as registration authority, or as architecture approval.

## 8. Relationship To WO-24 Manifest Scaffold And WO-23 Dry-Run Integration

The integration sits inside the constraint surface established by WO-23
and WO-24:

- `23-mock-adapter-dry-run-integration.md` (WO-23 / DC-026) named the
  composition order steps 1 through 12 of the WO-23 dry-run. WO-25
  inserts the manifest-validation step (new step 2) and the manifest-load
  step (new step 7) into that order without modifying any of the WO-23
  steps' semantics. The adapter is still invoked after fixture and
  configuration loading and before contract checks run.
- `24-retrieval-configuration-manifest-scaffold.md` (WO-24 / DC-027)
  named the manifest loader's boundary (Sections 3 through 7) and the
  rejection conditions (Section 6). The WO-25 integration relies on the
  loader's behavior without modifying the loader. Manifest authority,
  manifest substance, and production manifest schema authorship remain
  with Codex; OQ-057 (configuration registration authority) and OQ-076
  (production artifact contracts) remain OPEN.
- `21-retrieval-adapter-contract.md` Section 9 (Registration Boundary):
  the adapter contract requires registered configuration manifests as
  inputs and explicitly defers manifest substance and authority to Codex.
  WO-25 wires the harness-internal toy manifest into the dry-run only;
  it does not author registration authority and does not become a
  production registration mechanism by use.
- `00-controller-checklist.md` Section K (Indexing Excellence Gate)
  continues to govern selection. The WO-25 integration's existence does
  not imply that any real adapter, vendor, library, ANN backend,
  reranker, retrieval family, ablation cell, multi-stage variant,
  registration authority, or architecture is authorized, registered,
  evaluated, or selected.

## 9. Forbidden Scope

The WO-25 integration is forbidden from doing any of the following:

- Modifying `harness/manifest_loader.py` (unless a strictly local,
  behavior-preserving bug fix is required and authorized by the WO-25
  packet's allowed-local-fix clause; documented in the evidence report).
- Modifying any existing fixture file under `harness/tests/fixtures/`.
- Authoring a production manifest schema, field-type registry, authority
  signature scheme, version pinning scheme, provenance schema, or
  production artifact contract.
- Resolving OQ-057 (configuration registration authority), OQ-070
  (broader scope), OQ-075 (dependency policy beyond the first scaffold),
  OQ-076 (production artifact contracts), OQ-035 (golden intent set
  construction), OQ-049 (broader dataset suite ownership), or OQ-056
  (run artifact retention/storage policy).
- Reading, writing, or otherwise touching any file under
  `benchmark-fixtures/`.
- Mutating corpus, route registry, source quality graph, validation
  evidence ledger, intent trace store, candidate routes, or official
  routes.
- Recording validation evidence against any candidate or official route.
- Promoting, demoting, revoking, retiring, or otherwise changing the
  lifecycle state of any route.
- Treating manifest content as validation evidence, as registration
  authority, as a promotion trigger, or as a selection input.
- Performing any real retrieval call, real index lookup, real ranking
  computation, real benchmark execution, or network call.
- Selecting any vendor, library, index family, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, or architecture.
- Declaring any configuration a winner, best, recommended, or
  production-ready (enforced by the forbidden-language scans).
- Adding third-party dependencies beyond the Python standard library.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Modifying any file outside the five files allowed under WO-25.

## 10. Not Production Manifest Registration; Not Benchmark Execution; Not Architecture Selection

The WO-25 integration is explicitly not production manifest registration.
The toy manifest loaded by the dry-run is harness-internal toy data
authored under WO-24; consuming it through the dry-run does not register
a production configuration, does not vest registration authority, and
does not constitute production admission.

The WO-25 integration is explicitly not benchmark execution. It satisfies
no prerequisite recorded in `14-benchmark-execution-plan.md` Pre-Run
Preparation Boundaries A or B. It does not produce metrics, scores,
thresholds, or rankings. It does not record validation evidence. It does
not constitute Stage 0 through Stage 5 of the benchmark execution flow.

The WO-25 integration is explicitly not architecture selection. The
manifest loader is a scaffold-internal conformance scaffold per WO-24 /
DC-027; the mock adapter is a scaffold-internal conformance scaffold per
WO-22 / DC-025; the dry-run is a scaffold-internal end-to-end runner per
WO-19 / DC-022 and WO-23 / DC-026. Together they make no architecture,
vendor, library, ANN backend, reranker, or production-system claim. The
Indexing Excellence Gate (`00-controller-checklist.md` Section K)
continues to govern selection. Any future real adapter, real manifest
registration mechanism, real benchmark execution, or architecture
selection requires separate Codex-authored Work Orders whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.

## 11. Out Of Scope

This document and the WO-25 integration are scaffold-internal only.
Neither authorizes:

- A real retrieval, indexing, or ranking implementation.
- A vendor, library, index family, retrieval family, ANN backend,
  reranker, ablation cell, multi-stage variant, or architecture choice.
- A benchmark execution against `benchmark-fixtures/` content.
- A production manifest schema, registration authority scheme, or
  artifact contract.
- A metric, threshold, weight, score, or ranking formula.
- A runtime compile design.
- A validation framework implementation.
- A treatment of the dry-run output as benchmark evidence, validation
  evidence, registered production configuration, dataset authorization,
  or architecture authorization.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.
