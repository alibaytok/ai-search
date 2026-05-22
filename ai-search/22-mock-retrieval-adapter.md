# ai-search - Mock Retrieval Adapter Scaffold

Document type: Phase 4 / Phase 9 / Mock retrieval adapter scaffold boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-22

---

## 1. Purpose

This document records the scaffold-internal mock retrieval adapter authorized
under WO-22. The mock adapter is a deterministic, toy-only conformance
scaffold against the WO-21 retrieval adapter contract boundary recorded in
`21-retrieval-adapter-contract.md`. Its only role is to make the contract
boundary testable in code without introducing a real retrieval implementation
and without authorizing any architecture decision.

The mock adapter exists so that future Codex packets can extend or replace it
against a tested conformance surface. It does not become a real retrieval
adapter through use. It does not select any architecture, vendor, library,
index family, ANN backend, reranker, or production system. It does not collapse
the five planes named in `21-retrieval-adapter-contract.md` Section 3.

## 2. Toy-Only Scope

The mock adapter is implemented at `harness/mock_adapter.py` as a single
function `run_mock_adapter(fixture, configuration)` that:

- Operates only on already-loaded fixture and configuration objects passed in
  by the caller (typically produced by `harness/fixture_loader.py` and
  `harness/config_loader.py`).
- Performs no filesystem I/O, no network calls, no third-party imports, and
  uses no retrieval, indexing, or ranking library.
- Returns a deterministic observation dictionary for the same input.
- Carries no schema commitment beyond what `21-retrieval-adapter-contract.md`
  Section 6 names at boundary level. The shape is a scaffold-internal test
  surface, not an approved manifest contract.

The unit tests at `harness/tests/test_mock_adapter.py` exercise the function
with the scaffold-internal toy fixture and configuration objects only. The
adapter is never invoked against `benchmark-fixtures/` content; `benchmark-fixtures/`
remains the empty skeleton authorized under WO-20.

## 3. Relationship To `21-retrieval-adapter-contract.md`

The contract boundary in `21-retrieval-adapter-contract.md` defines the
adapter role, input boundary, output boundary, forbidden plane collapses,
contract violation surface, registration boundary, and non-selection boundary
at documentation level only. WO-22 authorizes a single scaffold-internal
implementation that conforms to that boundary in code:

- Section 2 (Adapter Role): the mock adapter does not decide route validity,
  does not promote, demote, revoke, or retire any route, does not evaluate
  the policy and risk gate, does not execute routes, and does not select
  itself or other adapters. The mock adapter's output explicitly marks its
  toy candidate as non-official, non-executable as official, and carries
  explicit absence markers for source, lifecycle, and policy references.
- Section 3 (Required Plane Separation): all five planes are present in
  every output. Empty planes are recorded explicitly via `empty_planes`.
- Section 5 (Input Boundary): the adapter consumes only inputs passed in by
  the caller. It does not open files, read live state, or ingest unqualified
  content.
- Section 6 (Output Boundary): every output entry carries a `plane` marker
  matching its container key, an `is_candidate` / `is_official` pair, an
  `executability` indicator, and explicit absence markers for missing
  references.

## 4. Five Output Planes

`run_mock_adapter(fixture, configuration)` returns a dictionary with the
five planes named in `21-retrieval-adapter-contract.md` Section 3:

- `official_route_results`. Empty by design. The mock adapter does not
  produce validated official routes; no fixture-derived entry crosses the
  validation or promotion boundary.
- `candidate_route_results`. Contains one deterministic toy entry when both a
  fixture record identifier and a configuration identifier are available.
  The entry is marked candidate, non-official, and non-executable as official,
  and carries explicit absence markers for source, lifecycle, and policy
  references.
- `normalized_material_support_results`. Contains one deterministic toy
  observation when a fixture record identifier is available. The entry is
  marked non-candidate, non-official, and non-route support material.
- `source_quality_constraint_observations`. Contains one explicit absence
  record stating that the mock adapter consulted no qualified source. The
  absence of any qualification status reference is recorded rather than
  treated as presence (per `09-source-quality-graph.md` Section 6).
- `trace_outcome_signal_observations`. Empty by design. The plane is
  recorded as future structure only; no trace or outcome signal is admitted
  by the mock adapter (per `04-intent-trace-store.md` Section 4 and
  `21-retrieval-adapter-contract.md` Section 3).

The output also carries an `empty_planes` field listing every plane that is
empty, an `adapter_kind` field set to `"mock_scaffold_internal"`, a
`selection_made` field set to `false`, and a `selection_note` recording that
selection authority remains with Codex under the Indexing Excellence Gate.

## 5. Forbidden Plane Collapse

The mock adapter does not collapse any of the plane separations forbidden by
`21-retrieval-adapter-contract.md` Section 4:

- Normalized material is never returned in `official_route_results` or
  `candidate_route_results`; it appears only under
  `normalized_material_support_results` and is marked non-candidate and
  non-official.
- The candidate route entry is never returned as an executable official
  route; `official_route_results` is empty and the candidate entry's
  `executability` is `"candidate_only_non_executable_as_official"`.
- Source trust is never elevated into route trust; source quality
  observations are recorded under their own plane with explicit absence
  markers and never carried into `official_route_results` or
  `candidate_route_results`.
- Trace and outcome signals are never used as validation evidence or as a
  promotion trigger; the plane is empty.
- No public or internet content is referenced or elevated; the adapter
  consults no external content of any kind.
- No aggregate performance treatment is produced; the adapter records no
  metric, score, or ranking signal.

The unit tests at `harness/tests/test_mock_adapter.py` exercise each of the
above invariants.

## 6. Non-Selection Boundary

The mock adapter does not select any configuration, vendor, library, index
family, ANN backend, reranker, retrieval family, ablation cell, multi-stage
variant, or architecture. The output's `selection_made` field is always
`false`, and the `selection_note` records that selection authority remains
with Codex under the Indexing Excellence Gate (`00-controller-checklist.md`
Section K). The unit test
`test_output_contains_no_selection_or_recommendation_language` asserts that
no string in the output contains any phrase from `FORBIDDEN_PHRASES` in
`harness/review_package.py`.

## 7. Not A Real Retrieval Implementation

The mock adapter is explicitly not a real retrieval implementation:

- It does not connect to any retrieval system, vendor, library, ANN backend,
  reranker, or external service.
- It does not implement any retrieval, indexing, or ranking algorithm.
- It does not consult a corpus, an index, a route registry, an intent trace
  store, a source quality graph, a validation evidence ledger, or any live
  state.
- It produces a fixed-shape toy observation derived from the input
  identifiers; no retrieval semantics are claimed.

A real retrieval adapter requires a separate future Codex packet that
explicitly approves real-system contact, dependency policy beyond the first
scaffold (tracked under OQ-075), input expansion beyond the scaffold inputs,
and any registration manifest substance (tracked under OQ-057 and OQ-076).

## 8. Not Benchmark Execution

The mock adapter is not benchmark execution:

- It does not load benchmark fixtures from `benchmark-fixtures/`.
- It does not produce metrics, scores, thresholds, weights, or rankings.
- It does not record validation evidence or promotion events.
- It does not run any contract violation test; contract violation testing is
  owned by `harness/contract_runner.py` and by the harness dry-run package
  at `harness/dry_run.py`.
- It does not constitute a benchmark run for the purposes of
  `14-benchmark-execution-plan.md` Pre-Run Preparation Boundaries A and B.

The harness scaffold continues to consume only the scaffold-internal toy
fixtures under `harness/tests/fixtures/` for unit tests and the scaffold
dry-run at `harness/dry_run.py`.

## 9. Future Adapter Implementation Boundary

The mock adapter does not author the surface of a future real adapter. Future
Codex packets that introduce a real retrieval adapter must, at minimum,
respect the boundaries already recorded in prior decisions:

- The five-plane separation in `21-retrieval-adapter-contract.md` Section 3
  is non-negotiable across any adapter implementation.
- The contract violation surface in `21-retrieval-adapter-contract.md`
  Section 7 applies to every adapter output, including under failure,
  partial availability, timeout, or other degraded modes.
- The input boundary in `21-retrieval-adapter-contract.md` Section 5
  prohibits live state, unqualified content, and opportunistic discovery
  unless a future Codex packet explicitly authorizes the input.
- The registration boundary in `21-retrieval-adapter-contract.md` Section 9
  remains owned by Codex; OQ-057 (configuration registration authority),
  OQ-075 (dependency policy beyond the first scaffold), and OQ-076
  (production artifact contracts) remain open.
- The non-selection boundary in `21-retrieval-adapter-contract.md` Section 8
  applies regardless of the adapter's measured performance. The Indexing
  Excellence Gate (`00-controller-checklist.md` Section K) continues to
  govern selection.

The mock adapter's existence does not imply that any real adapter is
authorized, registered, evaluated, or selected. The mock adapter is a
conformance scaffold only.

## 10. Out Of Scope

This document and the mock adapter are scaffold-internal only. Neither
authorizes:

- A real retrieval, indexing, or ranking implementation.
- A vendor, library, index family, retrieval family, ANN backend, reranker,
  ablation cell, multi-stage variant, or architecture choice.
- A benchmark execution against `benchmark-fixtures/` content.
- A registration manifest schema or template.
- A metric, threshold, weight, score, or ranking formula.
- A runtime compile design.
- A validation framework implementation.
- A treatment of the mock adapter as adapter authorization, benchmark
  authorization, dataset authorization, or architecture authorization.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria, and
evidence requirements are explicit at issue time.
