# ai-search - Benchmark Execution Plan

Document type: Phase 4 / Phase 9 research / Benchmark execution boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (lifecycle distinction between pre-run preparation boundaries and run execution stages corrected under WO-12R)
Work Order: WO-12 (rework required), WO-12R (current submission)

---

## 1. Purpose

This document defines, at documentation level only, the execution plan boundary for the retrieval benchmark framework defined in `13-retrieval-benchmark-framework.md`. It distinguishes the pre-run preparation boundaries (dataset fixture preparation, retrieval configuration registration) from the run execution stages (readiness review, contract violation pass, quality measurement pass, performance measurement pass, operational review pass, human architecture review package). It enumerates the evaluation matrix, the run artifacts that every run must record, reproducibility requirements, disqualification conditions, and the acceptance boundary. It does not implement the benchmark, does not author harness code, does not author schemas, does not author dataset content, does not select a winning architecture, vendor, or library, and does not set substantive metric thresholds.

The plan is the boundary that any future benchmark scaffold must respect. A scaffold built outside this boundary is not a benchmark of ai-search; it is some other thing.

## 2. Benchmark Execution Principles

- Pre-run preparation boundaries are completed before a benchmark run begins. They produce the dataset fixtures and the registered retrieval configurations that the run consumes. Pre-run preparation is not a run stage; preparation outputs are inputs that Stage 0 verifies.
- Run execution stages are ordered. Within a run, no stage may be skipped, parallelized into a stage it depends on, or backfilled.
- Contract safety is the first measurement inside a run, not the last. Stage 1 (Contract Violation Test Pass) precedes every quality, performance, and operational measurement.
- Disqualification on contract violation is binary and immediate. No quality or performance score overrides a contract failure.
- Reproducibility is a precondition for admissibility. A run that cannot be reproduced from recorded state is not an admissible benchmark result.
- Run artifacts are evidence. Summary metrics without artifacts are not benchmark output.
- Human review precedes architecture selection. No automated aggregate score selects a winning index, vendor, library, or family. Selection authority remains with Codex.
- Benchmark success is not route validation evidence. The benchmark validates the retrieval substrate's behavior under ai-search's constraints; it does not validate routes. Validation evidence for routes is governed by `08-validation-and-feedback.md`.

## 3. Pre-Run Preparation Boundary A - Dataset Fixture Preparation

Dataset fixtures are prerequisites prepared before a benchmark run begins. They are not a run stage. Their preparation produces inputs that Stage 0 (Readiness Review) verifies before the run starts.

The dataset fixture categories required by `13-retrieval-benchmark-framework.md` Section 3 are: golden intent set, hard negative set, boundary violation set, latency profile set, update profile set, adversarial set.

Boundary requirements for fixture preparation:

- Each fixture is versioned. Benchmark runs record the fixture version against which they were executed.
- Each fixture is content-hashed. The harness verifies the hash before the fixture is admitted to the run.
- Each fixture carries provenance: when it was constructed, who authorized it, what inputs informed it.
- Fixtures are revisable but not silently editable. Edits require a recorded event and a new version.
- Fixtures are isolated. The golden intent set, the hard negative set, and the boundary violation set may not be used to train any retrieval configuration under benchmark.
- Construction methodology, ownership, refresh cadence, and authority remain Codex-owned (existing OQ-035 and OQ-049 referenced; not duplicated).

This boundary does not build datasets. Building datasets is out of scope for WO-12.

## 4. Pre-Run Preparation Boundary B - Retrieval Configuration Registration

Retrieval configurations are prerequisites prepared before a benchmark run begins. A registered configuration is the unit of evaluation. Registration is not a run stage; it precedes the run, and Stage 0 (Readiness Review) verifies that at least one registered configuration exists before the run starts.

Boundary requirements for configuration registration:

- Each registered configuration carries: the retrieval family (per `12-indexing-and-retrieval-research.md` Section 5); the retrieval planes covered; the parameter set; the constraint mode (which graph constraints are applied); the rerank mode (none, late-interaction, cross-encoder, or other); the version pins of all software dependencies; and the operational profile (in-memory, disk-backed, etc.).
- Configurations are versioned. Modifications produce new configuration versions; they do not silently rewrite a registered version.
- Configurations are isolated. Two configurations under test in the same run must not share state that would contaminate either's measurements.
- Configurations are not selected by registration. Registration is a precondition for measurement; it is not approval. Selection is a Codex decision following Stage 5 (Human Architecture Review Package).
- Registration authority is owned by Codex (OQ-057).

## 5. Stage 0 - Benchmark Readiness Review

The readiness review precedes the contract violation pass and every subsequent measurement stage. It records whether the run is admissible before any measurement begins.

Within the run, Stage 0 verifies that the pre-run preparation boundaries (Sections 3 and 4) have produced their required outputs and that the harness environment is in a state that supports an admissible run.

- Confirm dataset fixture versions are present and hashed (outputs from Pre-Run Preparation Boundary A available).
- Confirm at least one retrieval configuration is registered (outputs from Pre-Run Preparation Boundary B available).
- Confirm prior run artifacts are archived under their recorded provenance and have not been mutated.
- Confirm the harness environment, dependency set, and configuration manifest are version-pinned.
- Confirm no dataset is contaminated by production user feedback or recent traces (per `13-retrieval-benchmark-framework.md` Section 4).
- Confirm the regression baseline (prior run snapshot, where one exists) is referenced.
- Record a readiness decision: admissible or not admissible. Not admissible halts the run with an explicit halt event.

The substantive readiness checklist is owned by Codex (OQ-055); this section records the boundary that such a checklist exists.

## 6. Stage 1 - Contract Violation Test Pass

Stage 1 runs the contract violation tests defined in `13-retrieval-benchmark-framework.md` Section 8. Each test is pass/fail and disqualifying.

Required behaviors:

- Stage 1 runs after Stage 0 admissibility is recorded and before any quality, performance, or operational measurement against the same configuration in the same run.
- Any contract violation failure disqualifies the configuration for the run. The run records the failure, the violated test, and the offending response with provenance.
- A disqualified configuration does not advance to Stages 2 through 4 in the current run.
- A disqualification is recorded with an explicit event; it does not silently retry.
- The contract violation test set is fixed for the run. Per-configuration relaxations are not allowed.

Tests covered (from `13-retrieval-benchmark-framework.md` Section 8): raw document never returned as a route; normalized material never returned as a route; candidate never returned as an executable official; demoted/revoked/retired routes never returned as executable officials; popularity does not raise trust; high rank does not promote; feedback does not validate; source trust does not become route trust.

## 7. Stage 2 - Quality Measurement Pass

Stage 2 runs only for configurations that passed Stage 1.

Required behaviors:

- Run the quality metrics defined in `13-retrieval-benchmark-framework.md` Section 7.1 against the golden intent set per query class.
- Record per-class metrics separately. Aggregate scores are computed for reporting only and do not select a winner.
- Record miss classification accuracy per category in `06-index-miss-policy.md`.
- Record per-plane metrics: official route plane, candidate route plane (where Codex-authorized non-official surfacing applies), normalized material support plane.
- Record leakage rates as quality observations, even though the corresponding contract tests already ran in Stage 1. Leakage rate is a continuous measurement; Stage 1 records pass/fail on the canonical test set.

## 8. Stage 3 - Performance Measurement Pass

Stage 3 runs only for configurations that completed Stage 2, or under Codex-defined sequencing for runs whose scope is performance-only.

Required behaviors:

- Run the performance metrics defined in `13-retrieval-benchmark-framework.md` Section 7.2: p50/p95/p99 latency, QPS under concurrency, memory footprint, index build time, incremental update latency, freshness lag, filter/constraint/rerank cost.
- Run latency under the latency profile set; throughput under realistic concurrency; index update cost under the update profile set.
- Cost projections at multiple corpus scales: baseline, expected production, stress.
- Performance metrics do not override contract violations or quality observations; they are recorded alongside.

## 9. Stage 4 - Operational Review Pass

Stage 4 runs only for configurations that completed Stage 3.

Required behaviors:

- Review the operational metrics defined in `13-retrieval-benchmark-framework.md` Section 7.3: implementation complexity; debuggability; reproducibility; rollback ability; incremental update support; source/candidate/official isolation; auditability.
- Operational review is structured human review. Required reviewer roles and reviewer authority are owned by Codex; this document records the boundary.
- Operational findings are recorded as part of the run artifacts.

## 10. Stage 5 - Human Architecture Review Package

Stage 5 assembles the evidence package for Codex review. No selection is made by the harness; selection is a Codex decision.

The package must include:

- The readiness decision and any non-admissibility events from Stage 0.
- Dataset fixture versions and hashes from Pre-Run Preparation Boundary A.
- The registered configuration manifests from Pre-Run Preparation Boundary B.
- Contract violation results from Stage 1, including any disqualification events.
- Per-class, per-plane quality results from Stage 2.
- Performance and cost projection results from Stage 3.
- Operational review findings from Stage 4.
- Reproducibility evidence (deterministic seed records, environment snapshots, dependency manifests, dataset hashes).
- Cross-references to the relevant `13-retrieval-benchmark-framework.md` sections.

The package is the input to Codex's selection decision. No part of the package recommends a winner. Selection follows the Codex-authored architecture selection Work Order, which is out of scope for WO-12.

## 11. Evaluation Matrix

The matrix is the cross-product of the following dimensions. Each cell is a benchmark run unit; not every cell must be filled in every run, but the matrix bounds what may be measured.

- Retrieval family (per `12-indexing-and-retrieval-research.md` Section 5).
- Retrieval plane (official, candidate where Codex-authorized, normalized material support).
- Query class (per `13-retrieval-benchmark-framework.md` Section 5).
- Dataset fixture (per Pre-Run Preparation Boundary A categories).
- Constraint mode (which graph and metadata constraints are applied).
- Rerank mode (none, late-interaction, cross-encoder, or other).
- Update profile (cold build only, incremental update under update profile set, sustained update load).
- Failure mode (steady state, timeout simulation, partial index unavailability, reranker failure).

The matrix is not a selection rubric. It bounds the measurement surface so a single configuration's performance is not extrapolated beyond what was actually measured.

## 12. Required Run Artifacts

Every run records, at minimum:

- The readiness decision from Stage 0 and any halt events.
- Dataset fixture versions and content hashes (from Pre-Run Preparation Boundary A).
- Configuration manifests with full parameter sets and version pins (from Pre-Run Preparation Boundary B).
- Contract violation results from Stage 1 (pass/fail per test, with offending response provenance for failures).
- Per-class quality measurements from Stage 2 with intent-level traceability where relevant.
- Per-plane quality measurements from Stage 2.
- Performance measurements from Stage 3 with raw timing distributions, not just aggregates.
- Operational findings from Stage 4 as structured records.
- Reproducibility evidence: deterministic seeds, environment snapshot, dependency hashes.
- The complete event log for the run, in order, with timestamps.
- Cross-references to the regression baseline (prior run snapshot) and any deltas.

The substantive storage form, retention period, immutability mechanism, and access controls for run artifacts are owned by Codex (OQ-056).

## 13. Reproducibility Requirements

- A run is admissible only if it is reproducible from recorded state. The harness must not produce results that depend on state external to the recorded artifacts.
- Deterministic seeds are required for every stochastic step. Non-deterministic runs are not admissible.
- Dependency versions and content hashes are recorded. Floating dependency references are not admissible.
- Dataset hashes are verified at Stage 0. A hash mismatch halts the run with an explicit event.
- Environment snapshots are recorded. The substantive form of the snapshot is owned by Codex.
- A run that cannot be reproduced from its recorded state is annotated as such and excluded from Stage 5 packages until the reproducibility defect is resolved.

## 14. Disqualification Conditions

A configuration is disqualified for a run when any of the following occurs:

- Any contract violation test fails in Stage 1.
- A dataset fixture hash mismatch is detected (at Stage 0 or during a stage's verification).
- A configuration drifts from its registered manifest during the run.
- A reproducibility check fails (non-deterministic divergence; missing environment record).
- A graph constraint silently drops under composition (per `13-retrieval-benchmark-framework.md` Section 10).
- A retrieval plane leaks results from another plane.
- A failure or miss test produces silently degraded output without the required indication.

Disqualification is recorded with an explicit event. Disqualification does not silently retry; the next run is a new run.

## 15. Acceptance Boundary

- The acceptance boundary for the benchmark framework is the gate that bounds architecture selection. It does not select.
- Acceptance for a run requires: Pre-Run Preparation Boundaries A and B completed before the run; Stage 0 admissibility; Stage 1 contract violation pass for every configuration that advanced; Stages 2 through 4 completed with recorded artifacts; reproducibility evidence; Stage 5 package assembled.
- A run that meets the acceptance boundary is admissible as input to Codex's architecture selection decision. It is not architecture selection.
- A run that fails the acceptance boundary is not silently retried. Failures and remediation are recorded; the next run is a new run.
- Final acceptance and selection are Codex decisions. Threshold authority is owned by Codex (existing OQ-052 referenced; not duplicated).

## 16. Out Of Scope

This document is documentation-level only. It does not:

- Implement the benchmark, the harness, or any of its stages.
- Author benchmark code, harness code, or dataset construction code.
- Author dataset content beyond naming the required fixture categories.
- Author schemas, fields, types, or data models for run artifacts.
- Author APIs for the harness.
- Author UI for benchmark dashboards.
- Author ranking formulas or weights.
- Author runtime compile internals.
- Author validation framework implementation.
- Select a winning index, family, configuration, library, vendor, or runtime profile.
- Set substantive metric thresholds. Threshold authority is owned by Codex.
- Define benchmark scheduling, triggering, or operational cadence (OQ-058).

All such work requires a future Codex-approved Work Order.
