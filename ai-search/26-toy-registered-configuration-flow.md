# ai-search - Toy Registered Configuration Flow

Document type: Phase 4 / Phase 9 / Toy registered configuration flow boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-26

---

## 1. Purpose

This document records the scaffold-internal registered configuration
observation flow authorized under WO-26 inside `harness/dry_run.py`. The
flow combines the already-loaded toy configuration (via the existing
WO-19 configuration loader) and the already-loaded toy manifest (via the
WO-24 manifest loader integrated under WO-25) into a bounded observation
object before the mock adapter is invoked, and surfaces that observation
in the assembled review package.

The flow exists so that future packets can reason about a registered
configuration as a single observable boundary, derived from the
configuration plus the manifest, without authoring production
configuration registration and without selecting any architecture.

The flow is scaffold-internal only. It does not constitute production
registration. It does not vest registration authority. It does not
record validation evidence. It does not promote, demote, revoke, or
retire any route. It does not declare any configuration a winner, best,
recommended, or production-ready.

## 2. Scaffold-Only Scope

The WO-26 scaffold touches only `harness/dry_run.py` and
`harness/tests/test_dry_run.py`. It does not modify
`harness/manifest_loader.py`, the mock adapter, the fixture loader, the
configuration loader, the event log, the contract runner, the
reproducibility recorder, the review-package assembler, the existing
toy fixtures (`toy_scaffold_fixture.json`, `toy_scaffold_config.json`,
`toy_retrieval_manifest.json`), or any other test module. It does not
modify any file under `benchmark-fixtures/`. The empty fixture skeleton
authorized under WO-20 remains untouched.

The dry-run continues to be a Python function (no CLI, no entry point,
no shell wrapper) consuming Python-stdlib-only inputs.

## 3. Exact Flow Order

The dry-run module composition order recorded under WO-19, WO-23, and
WO-25 is extended under WO-26. Step 8 verifies that the loaded manifest
names the loaded configuration, and step 9 is the new registered
configuration observation step.

1. Create EventLog.
2. Validate manifest parameter consistency (both-or-neither). On
   inconsistency, record a `manifest_parameters_incomplete` halt event
   and raise `IncompleteManifestParameters` before any loading occurs.
3. Load and SHA-256 hash-verify the toy fixture via
   `harness/fixture_loader.py`.
4. Load and drift-check the toy configuration via
   `harness/config_loader.py`.
5. Capture reproducibility evidence via `harness/reproducibility.py`.
6. Record the loaded fixture hash and the configuration identifier into
   the reproducibility record.
7. If manifest parameters are provided, invoke the scaffold-internal
   manifest loader via `load_manifest(manifest_path,
   expected_manifest_id, event_log)`. Manifest loader rejection paths
   halt before any further step.
8. If a manifest was successfully loaded, verify that the loaded
   manifest's `configuration_id` matches the loaded configuration
   identifier. A mismatch records a `manifest_configuration_mismatch`
   halt event and raises `ManifestConfigurationMismatch` before the
   observation step or adapter invocation.
9. If a manifest was successfully loaded and its configuration id
   matches, derive the registered configuration observation via
   `_registered_configuration_observation(configuration_id, manifest)`.
   Record a `registered_configuration_observed` event into the EventLog
   summarizing the observation's identifiers (`configuration_id`,
   `manifest_id`, `adapter_kind`, `planes_declared`, `selection_made`)
   and the explicit non-authority markers
   (`registration_authority_decided: False`,
   `production_registration: False`).
10. Invoke the scaffold-internal mock adapter via
   `run_mock_adapter(fixture, configuration)`; record the
   `mock_adapter_invoked` event and one `adapter_plane_present` event
   per plane into the EventLog.
11. Create `ContractRunner` and register the scaffold-internal toy
    contract checks (or a test-supplied override).
12. Derive the toy response from the fixture, the configuration, and the
    adapter output.
13. Run the contract checks against the toy response.
14. Assemble the human review package via `harness/review_package.py`,
    attach `adapter_output_evidence` to the package, and, when a
    manifest was loaded, attach `manifest_evidence` and
    `registered_configuration_observation` as well. Re-scan each
    attached structure for forbidden language using
    `harness.review_package.FORBIDDEN_PHRASES`.

The event ordering invariant of WO-25 (`manifest_loaded` before
`mock_adapter_invoked`) extends under WO-26 to:
`manifest_loaded` < `registered_configuration_observed` < `mock_adapter_invoked`.

## 4. Registered Configuration Observation Boundary

The observation attached to the assembled package as
`registered_configuration_observation` carries the following fields:

- `configuration_id`: the configuration identifier loaded by
  `harness/config_loader.py` (`"toy-scaffold-config"` for the
  scaffold-internal toy configuration).
- `manifest_id`: the manifest identifier admitted by the WO-24 manifest
  loader (the value of `manifest["manifest_id"]`).
- `adapter_kind`: the adapter kind named in the loaded manifest
  (`"mock_scaffold_internal"` for the scaffold-internal toy manifest).
- `planes_declared`: a copy of the manifest's declared plane list,
  matching the five plane names from
  `21-retrieval-adapter-contract.md` Section 3.
- `selection_made`: the manifest's non-selection posture (always `False`
  for an admitted manifest, since the WO-24 loader rejects manifests
  whose `selection_made` is not exactly `False`).
- `registration_authority_decided`: explicit boolean `False`.
  Registration authority is owned by Codex and is tracked under OQ-057;
  the observation does not vest that authority by use.
- `production_registration`: explicit boolean `False`. The observation
  is harness-internal and does not constitute production admission.
- `evidence_note`: a free-text string recording that the structure is a
  scaffold-internal registered configuration observation per
  `26-toy-registered-configuration-flow.md` and is not production
  registration, not registration authority decision, not validation
  evidence, and not architecture selection.

The structure is harness-internal observation only. It does not invoke
any retrieval system, does not consult production state, and does not
mutate any production-like state. It is re-scanned for forbidden
language using `harness.review_package.FORBIDDEN_PHRASES` before
attachment so the integration scan and the review-package scan cannot
drift.

In addition to the `registered_configuration_observation` field, the
package's `all_events` includes a `registered_configuration_observed`
event recorded in step 9 of the flow order. The event carries the
identifiers and non-authority markers above for audit visibility.

## 5. Default No-Manifest Behavior

The observation step runs only in manifest mode. In default no-manifest
mode (neither `manifest_path` nor `expected_manifest_id` provided), the
flow preserves the WO-23 behavior exactly:

- `load_manifest(...)` is not called.
- No `manifest_loaded` event is recorded.
- No `registered_configuration_observed` event is recorded.
- The assembled package carries `adapter_output_evidence` (WO-23
  invariant) but does not carry `manifest_evidence` (WO-25) or
  `registered_configuration_observation` (WO-26).
- Every WO-19, WO-23, and WO-25 invariant carries forward unchanged.

## 6. Halt Behavior

Halt behavior follows DC-020 (halt on contract failure halts measurement
for the failing configuration with an explicit halt event; no silent
continuation) and extends the WO-19 / WO-23 / WO-25 halt boundary:

- Incomplete manifest parameters raise `IncompleteManifestParameters`
  before any other loading. The observation step is not reached.
- Fixture hash mismatch and configuration drift raise from their
  respective loaders before manifest loading. The observation step is
  not reached.
- Manifest loader rejection paths raise from
  `harness/manifest_loader.py` before the observation step runs and
  before the mock adapter is invoked. No observation is built; no
  `registered_configuration_observed` event is recorded.
- Manifest/configuration mismatch raises `ManifestConfigurationMismatch`
  after a `manifest_configuration_mismatch` halt event is recorded and
  before the observation step runs or the mock adapter is invoked. No
  observation is built; no `registered_configuration_observed` event is
  recorded.
- Contract failure disqualifies the configuration via `ContractRunner`.
  Because the observation step runs after manifest load and before
  contract checks, a contract failure with a successfully loaded
  manifest still produces an assembled package that carries
  `adapter_output_evidence`, `manifest_evidence`, and
  `registered_configuration_observation`; the disqualification is
  surfaced via `disqualified_configurations` and
  `contract_checks_failed` in the same package.
- A failure of the post-assemble forbidden-language re-scan over the
  observation raises `ForbiddenLanguageInReviewPackage` from
  `harness.review_package`. The package is not returned; the run is
  treated as a halt at the integration surface. The observation's
  `evidence_note` and the manifest-derived strings were authored to
  contain no forbidden phrase, so this halt does not fire in normal
  operation.

No silent continuation against a halted run is permitted at any of the
halt points above.

## 7. Review Package Boundary

The review package returned by the dry-run is the harness-internal
package assembled by `harness/review_package.py`. Under WO-26 it
carries, in addition to the WO-19, WO-23, and WO-25 fields (`summary`,
`event_count`, `all_events`, `halt_events`, `contract_checks_passed`,
`contract_checks_failed`, `disqualified_configurations`,
`reproducibility`, `selection_made`, `selection_note`,
`adapter_output_evidence`, and conditionally `manifest_evidence`):

- `registered_configuration_observation` (present only when a manifest
  was loaded): the structure described in Section 4.
- `registered_configuration_observed` event in `all_events` (present
  only when a manifest was loaded): the audit record described in
  Section 3, step 9.

The package format remains harness-internal and is not a production
artifact contract; production artifact contracts remain owned by Codex
under OQ-076 (which remains open). The package continues to be subject
to the forbidden-language scan in `harness/review_package.py`; the
observation is additionally re-scanned by the integration using the
same `FORBIDDEN_PHRASES` constant so that the scans cannot drift.

The package does not propose, recommend, rank, or otherwise select any
configuration. It does not declare a configuration a winner, best, or
production-ready. It does not treat the registered configuration
observation as registration authority, as validation evidence, or as
architecture approval.

## 8. Relationship To WO-24 And WO-25

The flow sits inside the constraint surface established by WO-24 and
WO-25:

- `24-retrieval-configuration-manifest-scaffold.md` (WO-24 / DC-027):
  named the manifest loader's boundary, the required scaffold-level
  fields, the rejection conditions, and the event-log behavior. WO-26
  consumes a manifest admitted by that loader and derives the
  observation from `manifest["manifest_id"]`,
  `manifest["adapter_kind"]`, `manifest["planes_declared"]`, and
  `manifest["selection_made"]`. The observation never re-validates the
  manifest's fields; the loader is authoritative.
- `25-manifest-loader-dry-run-integration.md` (WO-25 / DC-028): named
  the optional manifest mode, the halt order, the manifest evidence
  boundary, and the WO-23 invariants that the integration preserves.
  WO-26 inserts the observation step at the manifest-mode-only point
  between manifest load and adapter invocation without modifying any
  WO-25 semantic.
- `21-retrieval-adapter-contract.md` Section 9 (Registration Boundary):
  the adapter contract requires registered configuration manifests as
  inputs and explicitly defers manifest substance and registration
  authority to Codex. WO-26 surfaces a harness-internal observation
  only; it does not author registration authority and does not become
  a production registration mechanism by use.
- `00-controller-checklist.md` Section K (Indexing Excellence Gate):
  continues to govern selection. The observation step does not imply
  that any real adapter, vendor, library, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, registration
  authority, or architecture is authorized, registered, evaluated, or
  selected.

OQ-057 (configuration registration authority), OQ-076 (production
artifact contracts), OQ-075 (dependency policy beyond the first
scaffold), OQ-035 (golden intent set construction), OQ-049 (broader
dataset suite ownership), OQ-070 (broader scope per WO-20 carry-forward
note), and OQ-056 (run artifact retention/storage policy) all remain
OPEN.

## 9. Forbidden Scope

The WO-26 flow is forbidden from doing any of the following:

- Modifying `harness/manifest_loader.py` (no allowed-local-fix is
  required under WO-26).
- Modifying any existing fixture file under `harness/tests/fixtures/`.
- Authoring a production registration mechanism, registration authority
  scheme, manifest schema, field-type registry, authority signature
  scheme, version pinning scheme, provenance schema, or production
  artifact contract.
- Resolving OQ-057, OQ-070, OQ-075, OQ-076, OQ-035, OQ-049, or OQ-056.
- Reading, writing, or otherwise touching any file under
  `benchmark-fixtures/`.
- Mutating corpus, route registry, source quality graph, validation
  evidence ledger, intent trace store, candidate routes, or official
  routes.
- Recording validation evidence against any candidate or official
  route.
- Promoting, demoting, revoking, retiring, or otherwise changing the
  lifecycle state of any route.
- Treating the registered configuration observation as registration
  authority, as production admission, as validation evidence, as a
  promotion trigger, or as a selection input.
- Performing any real retrieval call, real index lookup, real ranking
  computation, real benchmark execution, or network call.
- Selecting any vendor, library, index family, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, or
  architecture.
- Declaring any configuration a winner, best, recommended, or
  production-ready (enforced by the forbidden-language scans).
- Adding third-party dependencies beyond the Python standard library.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Modifying any file outside the five files allowed under WO-26.

## 10. Not Production Registration; Not Benchmark Execution; Not Architecture Selection

The WO-26 flow is explicitly not production registration. The
observation it surfaces carries explicit `registration_authority_decided:
False` and `production_registration: False` markers; surfacing this
observation through the dry-run does not register a production
configuration, does not vest registration authority, and does not
constitute production admission. Registration authority remains owned
by Codex under OQ-057.

The WO-26 flow is explicitly not benchmark execution. It satisfies no
prerequisite recorded in `14-benchmark-execution-plan.md` Pre-Run
Preparation Boundaries A or B. It does not produce metrics, scores,
thresholds, or rankings. It does not record validation evidence. It
does not constitute Stage 0 through Stage 5 of the benchmark execution
flow.

The WO-26 flow is explicitly not architecture selection. The Indexing
Excellence Gate (`00-controller-checklist.md` Section K) continues to
govern selection. The observation makes no architecture, vendor,
library, ANN backend, reranker, or production-system claim. Any future
real adapter, real registration mechanism, real benchmark execution, or
architecture selection requires separate Codex-authored Work Orders
whose scope, allowed files, required content, forbidden scope,
acceptance criteria, and evidence requirements are explicit at issue
time.

## 11. Out Of Scope

This document and the WO-26 flow are scaffold-internal only. Neither
authorizes:

- A real retrieval, indexing, or ranking implementation.
- A vendor, library, index family, retrieval family, ANN backend,
  reranker, ablation cell, multi-stage variant, or architecture choice.
- A benchmark execution against `benchmark-fixtures/` content.
- A production manifest schema, registration mechanism, registration
  authority scheme, or artifact contract.
- A metric, threshold, weight, score, or ranking formula.
- A runtime compile design.
- A validation framework implementation.
- A treatment of the dry-run output or the registered configuration
  observation as benchmark evidence, validation evidence, registered
  production configuration, dataset authorization, or architecture
  authorization.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.
