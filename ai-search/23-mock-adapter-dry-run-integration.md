# ai-search - Mock Adapter Dry-Run Integration

Document type: Phase 4 / Phase 9 / Mock adapter dry-run integration boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-23

---

## 1. Purpose

This document records the integration of the scaffold-internal mock retrieval
adapter (authored under WO-22 and recorded in
`22-mock-retrieval-adapter.md`) into the toy end-to-end dry-run (authored
under WO-19 and recorded in `19-scaffold-dry-run-protocol.md`). The
integration makes the WO-21 retrieval adapter contract boundary observable
end-to-end through the existing harness modules, without authoring a real
retrieval implementation and without authorizing any architecture decision.

The integration is scaffold-internal only. It does not introduce a real
retrieval call, does not consume `benchmark-fixtures/` content, does not
record validation evidence, does not select any architecture, vendor,
library, index family, ANN backend, reranker, retrieval family, ablation
cell, multi-stage variant, or production system, and does not declare any
configuration a winner, best, recommended, or production-ready.

## 2. Toy-Only Scope

The integration touches only `harness/dry_run.py` and
`harness/tests/test_dry_run.py`. It does not modify the mock adapter, the
event log, the fixture loader, the configuration loader, the contract
runner, the reproducibility recorder, or the review-package assembler. It
does not modify any document under `ai-search/` other than the three
allowed tracker/ledger/protocol files. It does not modify any file under
`benchmark-fixtures/`. The toy fixtures and configuration under
`harness/tests/fixtures/` are unchanged.

The dry-run continues to be a Python function (no CLI, no entry point, no
shell wrapper) consuming Python-stdlib-only inputs.

## 3. Exact Integration Order

The dry-run module composition order recorded under WO-19 is extended
under WO-23 as follows. Steps 1 through 5 and 7 through 9 retain their
WO-19 meaning; step 6 is the new adapter-invocation step.

1. Create EventLog.
2. Load and SHA-256 hash-verify the toy fixture via
   `harness/fixture_loader.py`. Fixture hash mismatch raises
   `FixtureHashMismatch` and prevents adapter invocation and package
   assembly.
3. Load and drift-check the toy configuration via
   `harness/config_loader.py`. Configuration drift raises
   `ConfigurationDrift` and prevents adapter invocation and package
   assembly.
4. Capture reproducibility evidence via `harness/reproducibility.py`.
5. Record the loaded fixture hash and the configuration identifier into
   the reproducibility record.
6. Invoke the scaffold-internal mock adapter via
   `run_mock_adapter(fixture, configuration)` from
   `harness/mock_adapter.py`. Record a `mock_adapter_invoked` event into
   the EventLog with the adapter kind, the `selection_made` posture, the
   explicit `empty_planes` list, and the per-plane entry counts. Record
   one `adapter_plane_present` event per plane with the plane name, the
   entry count, and the `is_empty` marker.
7. Create `ContractRunner` and register the scaffold-internal toy contract
   checks (or a test-supplied override).
8. Derive a toy response from the fixture, the configuration, and the
   adapter output. The response surfaces a sanitized view of the adapter
   output for contract checks (per-plane entry count and is-empty marker,
   adapter kind, non-selection posture, plane-separation marker, explicit
   empty-plane list).
9. Run the contract checks against the toy response.
10. Assemble the human review package via `harness/review_package.py` and
    attach `adapter_output_evidence` to the package. Re-scan the attached
    evidence for forbidden language using the
    `harness.review_package.FORBIDDEN_PHRASES` constant.

## 4. Adapter Output Boundary

The adapter is invoked exactly once per dry-run and its output is treated
as observation only. The integration does not interpret the adapter
output as retrieval results, does not promote, demote, revoke, or retire
any route based on the output, and does not record any output entry as
validation evidence.

The `adapter_output_evidence` attached to the review package preserves the
five planes named in `21-retrieval-adapter-contract.md` Section 3:

- `official_route_results` (empty by design under the mock adapter).
- `candidate_route_results` (one deterministic toy entry; marked candidate,
  non-official, non-executable as official; carries explicit absence
  markers for source, lifecycle, and policy references).
- `normalized_material_support_results` (one deterministic toy observation;
  marked non-candidate, non-official, non-route support material).
- `source_quality_constraint_observations` (one explicit absence record;
  records that the mock adapter consulted no qualified source).
- `trace_outcome_signal_observations` (empty by design under the mock
  adapter).

Empty planes are recorded explicitly in `evidence["empty_planes"]`. Every
plane entry retains its `plane` marker matching its container key. Every
plane entry retains the `is_candidate`, `is_official`, and `executability`
markers it carried in the adapter output, plus any explicit absence
markers (`*_is_absent` boolean fields).

The adapter evidence carries `adapter_kind: "mock_scaffold_internal"`,
`selection_made: false`, a `selection_note` recording that selection
authority remains with Codex under the Indexing Excellence Gate, and an
`evidence_note` recording that the structure is conformance evidence per
`21-retrieval-adapter-contract.md` and is not a retrieval result, not
validation evidence, and not architecture selection.

## 5. Contract-Check Derivation Boundary

The toy response passed to the contract runner is derived from the fixture,
configuration, and adapter output. The derivation is local to
`harness/dry_run.py` and exposes a sanitized view of the adapter output:

- `fixture_marker` and `sample_record_id` from the fixture.
- `configuration_id` from the configuration.
- `adapter_kind`, `selection_made`, `empty_planes` from the adapter output.
- `plane_summary` mapping each plane name to its `entry_count` and
  `is_empty` marker.
- `plane_separation_preserved`: a boolean computed locally by checking that
  every entry under every plane carries a `plane` marker equal to its
  container key.

The response itself is not a route, not a retrieval result, and not a
validation outcome. It exists only so the contract runner has a defined
surface to check. The default contract checks under WO-23 verify:
fixture marker presence, configuration-id presence, absence of any
`raw_internet_content` key, adapter kind equals
`"mock_scaffold_internal"`, `selection_made` is `False`,
`plane_separation_preserved` is `True`, and `empty_planes` is a list.

Tests may override the default checks via the `contract_checks` parameter
to exercise the contract failure path; this control is preserved from
WO-19.

## 6. Halt Behavior

Halt behavior follows DC-020 (halt on contract failure halts measurement
for the failing configuration with an explicit halt event; no silent
continuation) and the WO-19 boundary:

- Fixture hash mismatch raises `FixtureHashMismatch` from the fixture
  loader before the adapter is invoked. No adapter event is recorded; no
  package is assembled; no adapter evidence is produced.
- Configuration drift raises `ConfigurationDrift` from the configuration
  loader before the adapter is invoked. No adapter event is recorded; no
  package is assembled; no adapter evidence is produced.
- Contract failure disqualifies the configuration via `ContractRunner`.
  The runner records an explicit halt event with
  `reason="contract_check_failed"` and stops further measurement against
  the failing configuration. Because the adapter is invoked before the
  contract checks run, the adapter events and the
  `adapter_output_evidence` are still produced and attached to the
  assembled package; the disqualification is surfaced via
  `disqualified_configurations` and `contract_checks_failed` in the same
  package.
- A failure of the adapter-evidence forbidden-language re-scan raises
  `ForbiddenLanguageInReviewPackage` from `harness.review_package`. The
  package is not returned; the run is treated as a halt at the integration
  surface. The mock adapter's own test
  `test_output_contains_no_selection_or_recommendation_language` (under
  WO-22) prevents this in normal operation.

No silent continuation against a halted run is permitted at any of the
halt points above.

## 7. Review Package Boundary

The review package returned by the dry-run is the harness-internal
package assembled by `harness/review_package.py`. Under WO-23 it carries,
in addition to the WO-19 fields (`summary`, `event_count`, `all_events`,
`halt_events`, `contract_checks_passed`, `contract_checks_failed`,
`disqualified_configurations`, `reproducibility`, `selection_made`,
`selection_note`):

- `adapter_output_evidence` containing the five planes (with per-plane
  `entry_count`, `is_empty`, and `entries`), `adapter_kind`,
  `selection_made`, `selection_note`, explicit `empty_planes`, and an
  `evidence_note`.
- `mock_adapter_invoked` and per-plane `adapter_plane_present` events in
  `all_events` (records of the adapter invocation and per-plane
  presence/absence).

The package format remains harness-internal and is not a production
artifact contract; production artifact contracts remain owned by Codex
under OQ-076 (which remains open). The package continues to be subject to
the forbidden-language scan in `harness/review_package.py`; the
adapter-attached evidence is additionally re-scanned by the integration
using the same `FORBIDDEN_PHRASES` constant so that the two scans cannot
drift.

The package does not propose, recommend, rank, or otherwise select any
configuration. It does not declare a configuration a winner, best, or
production-ready. It does not treat adapter output as validation evidence
or as architecture approval.

## 8. Forbidden Scope

The WO-23 integration is forbidden from doing any of the following:

- Authoring a real retrieval adapter, a real retrieval call, or any
  retrieval/indexing/ranking algorithm.
- Authoring a registration manifest schema, a production artifact contract,
  or any field type definitions intended as a production schema.
- Consuming any content under `benchmark-fixtures/`. The dry-run continues
  to operate exclusively against `harness/tests/fixtures/`.
- Mutating corpus, route registry, source quality graph, validation
  evidence ledger, intent trace store, candidate routes, or official
  routes.
- Recording validation evidence against any candidate or official route.
- Promoting, demoting, revoking, retiring, or otherwise changing the
  lifecycle state of any route.
- Treating adapter output as validation evidence, as a promotion trigger,
  or as a selection input.
- Selecting any vendor, library, index family, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, or architecture.
- Declaring any configuration a winner, best, recommended, or
  production-ready.
- Producing any metric threshold, score, ranking formula, or quality
  judgment.
- Adding third-party dependencies beyond the Python standard library
  (OQ-075 remains open).
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Modifying any file outside the five files allowed under WO-23.

## 9. Not Real Benchmark Execution; Not Architecture Selection

The WO-23 integration is explicitly not real benchmark execution. It does
not satisfy any prerequisite recorded in `14-benchmark-execution-plan.md`
Pre-Run Preparation Boundaries A or B. It does not produce metrics, scores,
thresholds, or rankings. It does not record validation evidence. It does
not constitute Stage 0 through Stage 5 of the benchmark execution flow.

The WO-23 integration is explicitly not architecture selection. The mock
adapter is a scaffold-internal conformance scaffold per WO-22 / DC-025; it
makes no architecture, vendor, library, ANN backend, reranker, or
production-system claim. The Indexing Excellence Gate
(`00-controller-checklist.md` Section K) continues to govern selection.
Any future real adapter and any future architecture selection require
separate Codex-authored Work Orders whose scope, allowed files, required
content, forbidden scope, acceptance criteria, and evidence requirements
are explicit at issue time.

## 10. Out Of Scope

This document and the WO-23 integration are scaffold-internal only.
Neither authorizes:

- A real retrieval, indexing, or ranking implementation.
- A vendor, library, index family, retrieval family, ANN backend, reranker,
  ablation cell, multi-stage variant, or architecture choice.
- A benchmark execution against `benchmark-fixtures/` content.
- A registration manifest schema or template.
- A metric, threshold, weight, score, or ranking formula.
- A runtime compile design.
- A validation framework implementation.
- A treatment of the dry-run output as benchmark evidence, validation
  evidence, dataset authorization, or architecture authorization.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.
