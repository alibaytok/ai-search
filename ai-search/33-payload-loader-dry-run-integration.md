# ai-search - Payload Loader Dry-Run Integration

Document type: Phase 4 / Phase 9 / Payload loader dry-run integration boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes - Codex review-time evidence-language hardening applied
Work Order: WO-33

---

## 1. Purpose

This document records the optional wiring of the scaffold-internal
fixture payload loader (authored under WO-32 / DC-035 at
`harness/payload_loader.py`) into the toy end-to-end dry-run at
`harness/dry_run.py`. The integration makes the WO-32 admission
boundary observable end-to-end through the existing dry-run modules
without authoring a real benchmark execution path, a real retrieval
adapter, or any architecture selection.

The integration is scaffold-internal only. It does not perform real
benchmark execution, does not collect metrics, does not score, does
not convert payloads into validation evidence, does not promote /
demote / revoke / retire any route, and does not declare any
configuration a winner, best, recommended, or production-ready.

## 2. Scaffold-Only Scope

The WO-33 integration touches only `harness/dry_run.py` and
`harness/tests/test_dry_run.py`. It does not modify
`harness/payload_loader.py`, the mock adapter, the manifest loader,
the fixture loader, the configuration loader, the event log, the
contract runner, the reproducibility recorder, the review-package
assembler, the artifact-snapshot writer, the toy fixtures
(`toy_scaffold_fixture.json`, `toy_scaffold_config.json`,
`toy_retrieval_manifest.json`), or any other test module. It does not
modify any file under `benchmark-fixtures/`; the three WO-31 payload
files and the six `.gitkeep` placeholders remain byte-identical to
the WO-31 / WO-32 approved state.

The dry-run continues to be a Python function (no CLI, no entry
point, no shell wrapper) consuming Python-stdlib-only inputs.

## 3. Exact Integration Order

The dry-run module composition order recorded under WO-19 and
extended under WO-23, WO-25, WO-26, and WO-27 is extended again under
WO-33. Step 8 is the new payload-loader-rejection check at function
entry (alongside the WO-25 manifest-incomplete check); a new step
8a is the payload-loader invocation between manifest-mode setup and
mock adapter invocation; and step 14 attaches `payload_evidence` to
the assembled package.

1. Create EventLog.
2. **(New under WO-33)** Validate payload parameter consistency
   (both-or-neither). If exactly one of `payload_path` /
   `expected_fixture_class` is provided, record a
   `payload_parameters_incomplete` halt event and raise
   `IncompletePayloadParameters` before any other loading.
3. Validate manifest parameter consistency. On inconsistency, record
   `manifest_parameters_incomplete` halt and raise
   `IncompleteManifestParameters`.
4. Load and SHA-256 hash-verify the toy fixture.
5. Load and drift-check the toy configuration.
6. Capture reproducibility evidence.
7. Record fixture hash and configuration identifier into the
   reproducibility record.
8. If manifest parameters are provided, invoke the manifest loader,
   verify manifest/configuration identity match, and record the
   registered configuration observation.
9. **(New under WO-33)** If payload parameters are provided, invoke
   `load_fixture_payload(payload_path, expected_fixture_class,
   event_log)`. The loader records `fixture_payload_loaded` on
   success or records an explicit halt event and raises on every
   rejection path; the adapter is not invoked on rejection.
10. Invoke the scaffold-internal mock adapter; record adapter
    invocation and per-plane events.
11. Create `ContractRunner` and register scaffold-internal toy
    contract checks (or test-supplied override).
12. Derive a toy response.
13. Run the contract checks.
14. Assemble the review package; attach `adapter_output_evidence`;
    when manifest mode is active, attach `manifest_evidence` and
    `registered_configuration_observation`; **(new under WO-33)**
    when payload mode is active, attach `payload_evidence` after a
    forbidden-language re-scan.
15. If `snapshot_output_path` was provided, write the snapshot and
    attach `snapshot_evidence`; refresh `all_events` and
    `event_count`.

The new step 9 is the WO-33 invocation point. It runs after manifest
mode is fully resolved (step 8) and before the mock adapter is
invoked (step 10), satisfying the packet requirement that "loader
rejection must halt before mock adapter invocation."

The event-ordering invariant of WO-25 / WO-26 / WO-27
(`manifest_loaded` < `registered_configuration_observed` <
`mock_adapter_invoked` < `snapshot_written`) extends under WO-33 to
include `fixture_payload_loaded` between
`registered_configuration_observed` (or
`configuration_loaded` when manifest mode is inactive) and
`mock_adapter_invoked`.

## 4. Optional Payload Mode Vs Default No-Payload Mode

The integration adds two optional keyword parameters:

- `payload_path` (default `None`)
- `expected_fixture_class` (default `None`)

The two parameters are both-or-neither:

- **Default no-payload mode**: neither parameter is provided. The
  WO-32 loader is not invoked; no `fixture_payload_loaded` event
  appears in `all_events`; no `payload_evidence` key is attached to
  the returned review package. Every WO-19 / WO-23 / WO-25 / WO-26 /
  WO-27 invariant is preserved exactly.
- **Payload mode**: both parameters are provided. The WO-32 loader is
  invoked exactly once per dry-run as step 9 above. On success the
  package carries `payload_evidence` (Section 5). On any loader
  rejection the dry-run halts before adapter invocation.
- **Incomplete-parameter mode is rejected**: if exactly one parameter
  is provided, `IncompletePayloadParameters` is raised after a
  `payload_parameters_incomplete` halt event is recorded. No fixture
  loading, configuration loading, manifest loading, payload loading,
  or adapter invocation occurs.

The default no-payload mode behavior is asserted unchanged by
`test_default_dry_run_without_payload_unchanged` (no
`payload_evidence` key; no `fixture_payload_loaded` event).

## 5. Payload Evidence Boundary

When a payload is successfully loaded, the assembled package carries
a `payload_evidence` field with the following structure:

- `fixture_class`: the loaded payload's `fixture_class`, equal to the
  caller's `expected_fixture_class`.
- `fixture_version`: the loaded payload's `fixture_version`.
- `entry_count`: the integer length of the payload's `entries` list.
- `entry_fixture_ids`: an ordered list of the entries' `fixture_id`
  strings.
- `evidence_note`: a free-text marker recording that the structure is
  scaffold-internal fixture payload evidence per `32-...md` and
  `33-...md`; it uses neutral observation-only language and avoids
  the positive-claim phrases rejected by the WO-32 payload loader.

The evidence is re-scanned against `harness.review_package.FORBIDDEN_PHRASES`
and `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES` before
attachment. (The WO-32 loader has already performed the same scans
over the full payload; the extra scan here is defense in depth.)

## 6. Halt Behavior

- **Incomplete payload parameters** halt before any fixture /
  configuration / manifest loading. The EventLog records a
  `payload_parameters_incomplete` halt event with
  `payload_path_provided` and `expected_fixture_class_provided`
  booleans.
- **Payload loader rejection** raises one of the WO-32 named
  exceptions (`MalformedPayloadJSON`, `NonObjectPayload`,
  `MissingPayloadMarker`, `InvalidPayloadMarker`,
  `PayloadFixtureClassMismatch`, `MissingPayloadFixtureVersion`,
  `EmptyOrMissingPayloadEntries`, `MissingEntryFixtureId`,
  `DuplicateEntryFixtureId`, `MissingEntrySyntheticMarker`,
  `MissingPlaneSeparationMarkers`, `ForbiddenLanguageInPayload`,
  `VendorMentionInPayload`, `ForbiddenClaimInPayload`,
  `UnknownPlaneNameInPayload`, `PlaneOverlapInPayload`). The loader
  records the corresponding halt event before raising. The mock
  adapter is not invoked when any of these are raised.
- **Contract failure after successful payload load** disqualifies
  the configuration via `ContractRunner`. The payload evidence is
  still attached to the assembled package, because it is produced
  before contract checks run.
- All prior halt points (fixture hash mismatch, configuration drift,
  manifest loader rejections, manifest/configuration mismatch,
  incomplete manifest parameters) continue to apply unchanged.

## 7. Review Package Boundary

The review package returned by the dry-run is the harness-internal
package assembled by `harness/review_package.py`. Under WO-33 it
carries, in addition to the prior fields (`summary`, `event_count`,
`all_events`, `halt_events`, `contract_checks_passed`,
`contract_checks_failed`, `disqualified_configurations`,
`reproducibility`, `selection_made`, `selection_note`,
`adapter_output_evidence`, and conditionally `manifest_evidence`,
`registered_configuration_observation`, `snapshot_evidence`):

- `payload_evidence` (present only when payload mode is active): the
  structure described in Section 5.
- `fixture_payload_loaded` event in `all_events` (present only when
  payload mode is active): the loader-recorded success event.

The package format remains harness-internal and is not a production
artifact contract; production artifact contracts remain owned by
Codex under OQ-076 (which remains OPEN).

The package does not propose, recommend, rank, or otherwise select
any configuration. It does not declare a configuration a winner,
best, or production-ready. It does not treat payload content as
validation evidence or as architecture approval.

## 8. Relationship To WO-32 And Prior Decisions

The integration sits inside the constraint surface established by
WO-32 and prior packets:

- WO-32 / DC-035 authored the loader at `harness/payload_loader.py`.
  WO-33 wires that loader into the dry-run unchanged; no loader
  module file is modified under WO-33.
- WO-25 / DC-028 established the both-or-neither pattern for optional
  loader parameters; WO-33 mirrors that pattern with
  `payload_path` / `expected_fixture_class`.
- WO-26 / DC-029 established the manifest/configuration identity
  check and the registered-configuration observation. WO-33 places
  the payload loader after that block so that when manifest mode is
  active, the payload loader runs against a configuration that has
  already been observed and recorded.
- WO-27 / DC-030 established `snapshot_evidence` attachment after all
  prior evidence keys. WO-33 places `payload_evidence` attachment
  before snapshot writing, so when snapshot mode is also active the
  on-disk snapshot file contains `payload_evidence`.
- `13-retrieval-benchmark-framework.md` Section 3 named the six
  fixture categories; WO-33 only consumes the three WO-31 admitted
  classes through the loader.
- `00-controller-checklist.md` Section K (Indexing Excellence Gate)
  continues to govern selection. WO-33 makes no architecture,
  vendor, library, ANN backend, neural re-scorer, retrieval family,
  ablation cell, multi-stage variant, or production-system claim.

## 9. Forbidden Scope

The WO-33 integration is forbidden from doing any of the following:

- Modifying `harness/payload_loader.py` or any existing harness
  implementation module other than `harness/dry_run.py`.
- Modifying any payload file under `benchmark-fixtures/<class>/`.
- Modifying any `.gitkeep` under `benchmark-fixtures/`.
- Modifying `benchmark-fixtures/README.md`.
- Modifying any existing test module under `harness/tests/` other
  than `test_dry_run.py`.
- Performing benchmark execution.
- Collecting metrics.
- Scoring.
- Authoring a retrieval / indexing / ranking implementation.
- Implementing a real retrieval adapter.
- Authoring a production manifest schema, retention policy, storage
  policy, or production artifact contract.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding third-party dependencies.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
  All seven remain OPEN.
- Duplicating RK-039 (the contamination concern remains covered by
  the existing RK-039 reference established under WO-29 / DC-032
  Section 9).

## 10. Not Benchmark Execution; Not Validation Evidence; Not Architecture Selection

Loader-integration success is explicitly:

- **Not benchmark execution.** The integration admits a payload and
  surfaces evidence of admission; it does not measure anything,
  produce any metric, or run any contract beyond the existing
  scaffold-internal toy contract checks.
- **Not validation evidence.** The loader returns observation only;
  the integration carries the same observation forward as
  `payload_evidence`. Neither constitutes recorded validation
  evidence for any candidate or official route.
- **Not architecture selection.** Loader-integration success does
  not make any architecture / vendor / library / ANN backend /
  neural re-scorer / retrieval family / ablation cell / multi-stage
  variant / production-system claim. The Indexing Excellence Gate
  (`00-controller-checklist.md` Section K) continues to govern
  selection.

Future packets that wire the loader output into a real benchmark
execution path, into ranking / scoring, into a real adapter, or into
architecture selection each require separate Codex-authored Work
Orders whose scope, allowed files, required content, forbidden
scope, acceptance criteria, and evidence requirements are explicit at
issue time.
