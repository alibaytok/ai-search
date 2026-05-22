# ai-search - Scaffold Dry-Run Protocol

Document type: Phase 4 / Phase 9 / Scaffold dry-run protocol
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-19

---

## 1. Purpose

This document records the protocol for the scaffold-only end-to-end dry-run implemented in `harness/dry_run.py` under WO-19. The dry-run wires together the harness modules created under WO-18 (event log, fixture loader, configuration loader, contract runner, reproducibility capture, review package assembler, and the package init) using only scaffold-internal toy fixtures and a registered toy configuration. Its purpose is to verify module composition end-to-end before any real benchmark dataset, retrieval implementation, or architecture selection is ever attempted.

This is not benchmark execution. This is not architecture selection. The dry-run does not measure any retrieval system; it derives a deterministic toy response from the loaded fixture and configuration purely to exercise the contract runner.

## 2. Toy-Only Scope

- Inputs are scaffold-internal toy fixtures only (`harness/tests/fixtures/toy_scaffold_fixture.json` and `harness/tests/fixtures/toy_scaffold_config.json`). Each fixture is visibly marked as a scaffold-internal test fixture and is not a benchmark dataset.
- The toy response is derived deterministically from the fixture and configuration content. It is not a retrieval-system response.
- Default contract checks are scaffold-internal toy checks. Real benchmark contract checks remain outside scaffold scope and are Codex-authorized.
- The dry-run never reaches any production state. It never invokes a vendor, library, ANN backend, reranker, or retrieval engine.
- Tests may pass an override list of contract checks (for example, an `always_fail` check) to exercise the failure path. The override mechanism is scaffold-internal and is not a production interface.

## 3. Module Composition Order

The dry-run executes the harness modules in the following order. The order is locked under WO-19.

1. Create an `EventLog` (`harness/event_log.py`).
2. Load and SHA-256 hash-verify the toy fixture (`harness/fixture_loader.py`).
3. Load and drift-check the toy configuration (`harness/config_loader.py`).
4. Capture reproducibility evidence (`harness/reproducibility.py`).
5. Record the loaded fixture hash and configuration identifier into the reproducibility record (`harness/reproducibility.py`).
6. Create a `ContractRunner` and register the scaffold-internal toy contract checks, or a test-supplied override (`harness/contract_runner.py`).
7. Derive a toy response from the fixture and configuration (scaffold-internal helper inside `harness/dry_run.py`).
8. Run the contract checks against the toy response.
9. Assemble and return the human review package (`harness/review_package.py`).

No module is invoked out of order. No module is skipped. No measurement of any kind is performed beyond the contract checks.

## 4. Allowed Inputs

The single public function `run_toy_dry_run` accepts:

- `fixture_path` (str): filesystem path to a scaffold-internal toy fixture JSON file.
- `fixture_sha256` (str): hex-encoded expected SHA-256 content hash of the fixture file.
- `config_path` (str): filesystem path to a scaffold-internal toy configuration JSON file.
- `registered_config` (dict or other JSON-compatible value): the registered manifest record against which the active configuration content is compared.
- `deterministic_seed` (int or str): seed value recorded in the reproducibility evidence.
- `contract_checks` (optional list of `(name, callable)` pairs): override for the default toy contract checks. Defaults to the scaffold-internal toy checks defined inside `harness/dry_run.py`.

No other inputs are accepted. No CLI is required; the runner is a Python function and is invoked by tests and (in the future) by Codex-authorized scripts only.

## 5. Halt Points

- Step 2 (fixture loading): if the actual SHA-256 hash of the file at `fixture_path` does not match `fixture_sha256`, the fixture loader records a halt event in the event log and raises `FixtureHashMismatch`. Package assembly does not occur.
- Step 3 (configuration loading): if the active configuration content does not match the registered manifest record, the configuration loader records a halt event and raises `ConfigurationDrift`. Package assembly does not occur.
- Step 8 (contract checking): on the first failing contract check, the contract runner records a halt event with reason `contract_check_failed` and disqualifies the configuration. Subsequent measurement against the disqualified configuration is forbidden. Package assembly proceeds and the package records the disqualification.

Halt events recorded by the dry-run are explicit. The dry-run does not silently continue past a halt; halts that prevent package assembly raise an exception, and halts that produce disqualification surface through the assembled package's `disqualified_configurations` field.

## 6. Returned Review Package Boundary

On success, `run_toy_dry_run` returns the dictionary produced by `harness/review_package.py`'s `assemble`. The package contains:

- A `summary` string for Codex review.
- An `event_count` and the complete `all_events` recorded during the dry-run.
- Filtered subsets: `halt_events`, `contract_checks_passed`, `contract_checks_failed`.
- The list of `disqualified_configurations` from the contract runner.
- A `reproducibility` record including Python version, platform string, deterministic seed, scaffold version, fixture hashes, and configuration identifiers.
- `selection_made: false`.
- A `selection_note` clarifying that selection is a Codex decision and that the package summarizes the run only.

The package does not recommend a winner, rank configurations, declare any configuration best or production-ready, or propose any configuration. The forbidden-phrase scan inside the assembler rejects any package containing recommendation, ranking, winner, best, or production-ready language anywhere.

## 7. Forbidden Scope

The dry-run is forbidden from doing any of the following, both in its current implementation and in any future modification:

- Executing a real benchmark.
- Loading a real benchmark dataset.
- Implementing or invoking any retrieval, indexing, or ranking system.
- Selecting a vendor, vector DB, ANN backend, reranker, retrieval family, ablation cell, multi-stage variant, or architecture.
- Setting a metric threshold or weight.
- Producing a quality or performance score that is treated as selection evidence.
- Authoring a production artifact schema or production artifact contract.
- Writing to corpus documentation, route registry documentation, source quality graph records, validation evidence records, intent trace store records, candidate routes, or official routes.
- Mutating any `ai-search/` documentation file other than the three allowed under WO-19 (this protocol document, the open questions tracker, and the ledger).
- Introducing a third-party dependency.
- Introducing a CLI surface unless explicitly authorized by a future Codex packet.
- Treating the dry-run's output as benchmark validation evidence or as production trust signal.

## 8. Out Of Scope

This document is documentation-level only. It does not:

- Implement real benchmark execution.
- Author real benchmark datasets.
- Implement any retrieval, indexing, or ranking system.
- Select a vendor, library, index family, retrieval family, ANN backend, reranker, ablation cell, multi-stage variant, or architecture.
- Set metric thresholds or weights.
- Author production artifact contracts.
- Author runtime compile internals.
- Author validation framework implementation.
- Treat the dry-run as benchmark-ready, production-ready, or selection-ready.

The dry-run verifies module composition only. Any further verification (real fixtures, real configurations, real retrieval invocation, real benchmark scoring) requires a future Codex-issued Work Order.
