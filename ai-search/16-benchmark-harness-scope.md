# ai-search - Benchmark Harness Implementation Scope Boundary

Document type: Phase 4 / Phase 9 research / Benchmark harness scope boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (Section 7 mechanism-specific wording corrected under WO-15R; implementation packet sequencing wording corrected after WO-17R review)
Work Order: WO-15 (rework required), WO-15R (approved), post-WO-17R Codex hygiene correction

---

## 1. Purpose

This document defines, at documentation level only, the implementation scope boundary for a future minimal benchmark harness. It enumerates what such a harness is allowed to do, what it must not do, what inputs it may consume, what artifacts it must produce, what reproducibility evidence it must record, and what human review package it must assemble. It does not author harness code, pseudocode, scripts, file trees, schemas, type definitions, JSON templates, dataset content, or any selection. Substantive harness implementation and execution authority remain with Codex.

This document is the scope lock between the experiment design boundary (`15-retrieval-experiment-design.md`) and any future harness implementation Work Order. It prevents any jump from "we know what experiments should exist" into "we are writing scripts."

## 2. Harness Scope Principles

- Harness scope is not harness implementation. This document names what a future harness may do; it does not implement anything.
- Harness implementation requires a future Codex packet (planned as WO-18 per the WO-17 decision lock). No code may be written under WO-15.
- Harness execution requires a future Codex packet. No benchmark run may be initiated under WO-15.
- A harness built outside this scope is not a benchmark of ai-search; it is some other thing.
- Contract safety is the harness's first concern. The harness treats contract failures as disqualifying, regardless of any other measurement.
- Plane separation is preserved end-to-end. Official, candidate, and normalized material planes are kept distinct in every harness behavior.
- Source trust does not become route trust through the harness. Source-level signals from the source quality graph (`09-source-quality-graph.md`) are consulted as constraints; they are not lifted into route trust by the harness.
- Reproducibility is a precondition for admissibility. A harness output that cannot be reproduced from recorded state is not an admissible benchmark result.
- Human review precedes architecture selection. The harness assembles a review package; it does not select a winner.
- Benchmark success is not route validation evidence. Route validation is governed by `08-validation-and-feedback.md`; the harness has no role in that path.
- End-user concept hiding holds. The harness does not expose prompt, skill, or agent concepts to end users; surface presentation is owned by Codex under the Phase 8 surface contract.

## 3. Allowed Harness Responsibilities

A future minimal harness, when implemented under a Codex-issued Work Order, may:

- Read approved dataset fixture inputs and verify their version and content hash before admission to a run.
- Read registered retrieval configuration manifests and verify them against their recorded provenance.
- Run the readiness checks named in Stage 0 of `14-benchmark-execution-plan.md` and record a readiness decision.
- Run the contract violation tests named in `13-retrieval-benchmark-framework.md` Section 8 and record pass/fail per test with offending response provenance for failures.
- Run the quality metrics named in `13-retrieval-benchmark-framework.md` Section 7.1 against the golden intent set per query class.
- Run the performance metrics named in `13-retrieval-benchmark-framework.md` Section 7.2 under the latency profile set, the update profile set, and at the corpus scales required by Codex.
- Record operational findings as structured observations consistent with `13-retrieval-benchmark-framework.md` Section 7.3.
- Record reproducibility evidence (deterministic seeds, version pins, dataset hash verification results, environment snapshots).
- Maintain a complete event log of the run with timestamps and explicit halt events.
- Cross-reference each run against the regression baseline (the prior run snapshot, where one exists).
- Assemble a human review package per Stage 5 of `14-benchmark-execution-plan.md` that the harness presents to Codex but does not act on.

## 4. Forbidden Harness Responsibilities

A future harness must not:

- Write to the source corpus.
- Write to the source quality graph.
- Write to the route registry (no candidate creation, no promotion, no demotion, no revocation, no retirement).
- Write to the validation evidence ledger.
- Write to the intent trace store.
- Mutate any production state under any condition.
- Promote, demote, revoke, retire, or validate routes.
- Decide architecture selection, vendor selection, library selection, or family selection.
- Interpret an aggregate score as a selection decision.
- Treat a per-cell win as architecture selection.
- Continue measurement against a configuration that has been disqualified by a contract violation.
- Silently retry a run that failed admissibility or disqualification.
- Modify a fixture, a configuration manifest, or a prior run artifact.
- Run with floating dependencies or unrecorded environment state.
- Expose prompt, skill, or agent concepts in any output presented to end users.
- Treat any harness output as route validation evidence or as production trust signal.

## 5. Input Boundary

The harness may consume only the following inputs. Inputs not on this list are forbidden.

- Approved dataset fixtures from `13-retrieval-benchmark-framework.md` Section 3, verified by version and content hash before admission.
- Registered retrieval configuration manifests per Pre-Run Preparation Boundary B of `14-benchmark-execution-plan.md`.
- The regression baseline reference (prior run snapshot, where one exists).
- The harness environment manifest (dependency set, version pins) that the harness verifies against before admission.

The harness does not consume production traces, production user feedback, the live source corpus, the live route registry, or any other production state. The harness operates against approved fixtures only.

## 6. Fixture Loading Boundary

- Fixtures are loaded from approved input locations recorded in the run manifest. The harness does not discover fixtures opportunistically.
- Each fixture's version and content hash are verified against the registered fixture record before the fixture is admitted to the run. A hash mismatch halts the run with an explicit event.
- Fixtures are read-only in the harness. The harness does not edit, augment, or rewrite a fixture as a side effect of any run.
- Fixture isolation is preserved: the golden intent set, the hard negative set, and the boundary violation set are not used to train any retrieval configuration under benchmark.
- The harness records the loaded fixture set, including versions and hashes, as part of the run artifact.

## 7. Retrieval Configuration Registration Boundary

- Configurations are read from the registered manifest produced by Pre-Run Preparation Boundary B (`14-benchmark-execution-plan.md` Section 4). The harness does not author configurations.
- The harness verifies that each active configuration matches its registered manifest record. A drift between the live configuration and its registered manifest record halts the run with an explicit event.
- The harness records the active configuration manifest in the run artifact for every cell it exercises.
- The harness does not silently register a new configuration. Registration is a Codex-authorized activity outside the harness.

## 8. Contract Test Runner Boundary

- The harness runs the contract violation tests from `13-retrieval-benchmark-framework.md` Section 8 before any quality, performance, or operational measurement against the same configuration in the same run.
- Each contract test is recorded as pass or fail. A failure records the violated test, the input that triggered it, the offending response, and the configuration manifest under which the failure occurred.
- A contract failure disqualifies the configuration for the run. The harness halts further measurement against that configuration and records the disqualification as an explicit event.
- The harness does not relax contract tests per configuration, per cell, or per run.
- The contract test runner does not promote, validate, or select anything. It records and disqualifies.

## 9. Metric Collection Boundary

- Quality metrics, performance metrics, and operational observations are collected per `13-retrieval-benchmark-framework.md` Section 7.
- Metrics are recorded per query class and per plane separately. Aggregate values are reported as derived outputs only and never as selection signals.
- The harness does not weight metrics. Weighting is a Codex decision outside the harness.
- The harness does not threshold metrics. Thresholds are Codex-owned.
- The harness records raw distributions, not just summaries, for performance metrics where applicable.
- Metric collection does not continue against a configuration that has been disqualified by a contract violation. A halt event is recorded; later metrics for that configuration in the same run are not collected.

## 10. Reproducibility Artifact Boundary

- The harness records deterministic seeds for every stochastic step.
- The harness records version pins for every software dependency.
- The harness records the content hashes of every fixture admitted to the run.
- The harness records an environment snapshot whose substantive form is owned by Codex.
- A run that cannot be reproduced from its recorded state is annotated and excluded from the human review package until the reproducibility defect is resolved.
- The harness does not edit reproducibility evidence after the run. Reproducibility evidence is append-only.

## 11. Run Artifact Boundary

The harness produces run artifacts only. It does not produce production state.

Each run artifact records, at boundary level, the readiness decision, the dataset fixture versions and hashes admitted, the configuration manifests under test, the contract violation results with offending-response provenance for failures, the per-class and per-plane quality measurements, the performance distributions, the operational observations, the reproducibility evidence, the complete event log, and the regression baseline cross-reference.

The artifact format, storage location, retention period, immutability mechanism, and access control are owned by Codex (existing OQ-056 referenced; not duplicated). The harness does not author the artifact schema.

## 12. Human Review Package Boundary

- The harness assembles a human review package per Stage 5 of `14-benchmark-execution-plan.md` after a run completes.
- The package summarizes the run artifact for Codex review. It does not recommend a winner; it does not score across cells; it does not rank configurations.
- A run that did not meet the acceptance boundary (per `14-benchmark-execution-plan.md` Section 15) is recorded as such in the package; the package does not omit failing runs or hide disqualifications.
- The harness does not act on the human review package. Codex's selection decision is recorded by a future Codex-authored architecture selection Work Order, which is out of scope here.

## 13. Failure And Halt Boundary

- The harness halts a run on any of the following: readiness check failure at Stage 0; dataset fixture hash mismatch; configuration manifest drift; reproducibility check failure during the run; contract violation failure that disqualifies a configuration; constraint composition drop; plane isolation leak; silently degraded output without indication.
- Each halt is recorded as an explicit event in the run's event log with timestamp, cause, and affected configuration where applicable.
- The harness does not silently retry. The next run is a new run with its own admissibility check.
- The harness does not downgrade or reclassify a halt to a warning. Halts remain halts in the recorded artifact.

## 14. Non-Selection Boundary

- The harness does not select an architecture, family, vendor, library, ablation cell, multi-stage variant, reranker, or ANN backend.
- The harness does not score configurations against each other for selection.
- The harness does not derive ordering, ranking, or recommendation across runs.
- The harness does not declare an "best" or "winning" configuration in any artifact.
- The Indexing Excellence Gate (`00-controller-checklist.md` Section K) continues to govern selection. The harness produces evidence the gate may eventually evaluate against, but the harness does not pass or apply the gate.

## 15. Future Implementation Approval Boundary

- The harness will only be implemented under a future Codex-authored Work Order (planned as WO-18 per the WO-17 decision lock) that explicitly authorizes harness implementation scope.
- The implementation Work Order must specify allowed files, allowed code surface, allowed dependencies, and allowed test surface.
- The implementation Work Order must specify the minimum implementation surface that satisfies the scope boundary recorded in this document, without exceeding it. The minimum surface is owned by Codex (new OQ).
- Until that implementation Work Order is approved, no harness code, script, or executable artifact is authored.

## 16. Out Of Scope

This document is documentation-level only. It does not:

- Implement the harness, write harness code, write pseudocode, write scripts, write CLI commands, or sketch a file tree.
- Author schemas, fields, types, JSON templates, or data models for any harness artifact.
- Author dataset content or fixtures.
- Author APIs for the harness.
- Author UI for harness output presentation.
- Run benchmarks or initiate a benchmark scaffold.
- Select a vendor, library, index family, configuration, retrieval family, ablation cell, multi-stage variant, reranker, ANN backend, or architecture.
- Set substantive metric thresholds or weights.
- Author runtime compile internals.
- Author validation framework implementation.
- Treat harness scope as implementation approval.
- Treat any harness output as route validation evidence or as production trust signal.

All such work requires a future Codex-approved Work Order.
