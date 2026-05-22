# ai-search - Retrieval Experiment Design

Document type: Phase 4 / Phase 9 research / Retrieval experiment design boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (Section 9 cross-reference to benchmark framework corrected under WO-14R)
Work Order: WO-14 (rework required), WO-14R (current submission)

---

## 1. Purpose

This document defines, at documentation level only, the experiment design boundary for future indexing and retrieval benchmarks. It enumerates the retrieval families to evaluate, the retrieval planes to test, the ablation matrix dimensions, the multi-stage and reranking variants, the update/freshness and cost and rollback experiment boundaries, the contract-safety assertions required per experiment, and the evidence required per experiment. It does not author benchmark code, dataset content, harness implementation, schemas, APIs, UI, or any selection. Substantive selection authority and substantive metric thresholds remain with Codex.

The experiment design is one of the prerequisites for any future benchmark run. It is bounded by the Indexing Excellence Gate (`00-controller-checklist.md` Section K). It does not bypass the gate; it scopes what evidence the gate will eventually evaluate against.

## 2. Experiment Design Principles

- Experiment design is not benchmark execution. The design names what would be measured; it does not measure anything.
- Experiment design is not architecture selection. The design lists candidates and variants without selecting a winner.
- No single experiment winner selects an architecture. A configuration that wins on one experiment cell does not thereby become the selected architecture; the Indexing Excellence Gate requires evidence across cost, update/freshness, rollback, reproducibility, ablation, and contract-safety dimensions.
- Contract-safety failures disqualify regardless of quality or performance. An experiment that surfaces a contract violation does not advance even if its other metrics are strong.
- Official route plane, candidate route plane, and normalized material support plane remain separate in every experiment.
- Candidate routes never become executable official results through retrieval. No experiment may have a passing condition that elevates a candidate to executable official.
- Normalized material never becomes a route. No experiment may have a passing condition that returns normalized material in a route-returning response.
- Public and internet source trust never becomes route trust. No experiment may have a passing condition that derives route trust from source-level signals.
- High rank, popularity, user preference, or feedback never promotes a route. Experiment outcomes do not promote candidates.
- Benchmark success is not route validation evidence. Validation evidence for routes is governed by `08-validation-and-feedback.md`.
- "Good enough" is rejected. The Excellence Gate's superiority requirement applies to the evidence produced by experiments.
- "Best not proven" means not selected. If no candidate cell clears the gate's evidence requirements, no selection is made.

## 3. Retrieval Families Under Test

The following families are candidates for inclusion in experiments. The set may be extended by Codex; it may not be silently narrowed.

- Lexical / BM25 family. Sparse keyword retrieval baselines.
- Learned sparse family / SPLADE-style. Learned sparse retrieval combining lexical interpretability with neural expansion.
- Dense vector retrieval family. Embedding-based retrieval with approximate nearest neighbor backends.
- Hybrid sparse + dense family. First-stage retrieval combining a sparse signal and a dense signal under a fusion function.
- Graph-constrained retrieval family. Retrieval that enforces structural constraints (source qualification, lifecycle state, route status) at retrieval time, with the source quality graph (`09-source-quality-graph.md`) consulted as a constraint layer.
- Metadata-filtered retrieval family. Retrieval that applies filters by lifecycle state, qualification, freshness, ownership, and other recorded boundaries.
- Late-interaction / ColBERT-style family. Per-token interaction retrieval.
- HNSW-style ANN family. Graph-based approximate nearest neighbor backends.
- IVF / IVF-PQ-style ANN family. Partitioned approximate nearest neighbor backends with product quantization variants.
- DiskANN-style disk-backed ANN family. Disk-backed ANN for corpora that exceed in-memory budgets.
- Reranking layer variant family. Separate reranking stages that apply more expensive scoring to small candidate sets.
- Multi-stage retrieval variant family. Compositions of first-stage retrieval with one or more downstream stages.

Tradeoffs for each family are described in `12-indexing-and-retrieval-research.md` Section 5. This document does not re-author those tradeoffs; it names the families as experiment inputs.

## 4. Retrieval Planes Under Test

Every experiment must declare which plane or planes it exercises and must preserve plane separation.

- Official route retrieval plane. The execution-eligible plane. Experiments on this plane verify that only validated official routes are returned and that misses route to the index miss policy.
- Candidate route retrieval plane. Exercised only under Codex-authorized non-official surfacing rules (OQ-016). Experiments must preserve the candidate vs. official distinction in every response.
- Normalized material support plane. Returns normalized material with provenance pointers for candidate derivation and audit. Normalized material is not a route; experiments on this plane never return material as a route in a route-returning response.
- Source quality constraint layer. Applied to other planes, not a plane in itself. Experiments measure both the correctness of constraint application and the cost.
- Trace and outcome signal layer. Recorded by the intent trace store (`04-intent-trace-store.md`) and consulted as a bounded signal, not as validation evidence. Experiments that admit trace/outcome signals must preserve the bounded-signal framing (OQ-027 referenced).

## 5. Ablation Matrix Boundary

The ablation matrix is the set of cells across which evidence is recorded. It is a boundary; this document does not author per-cell pass/fail thresholds or weights. Codex owns the substantive matrix scope (OQ-060 referenced).

Required cells (at boundary level only):

- Lexical only.
- Learned sparse only.
- Dense only.
- Lexical + dense hybrid.
- Hybrid + graph constraints.
- Hybrid + metadata filters.
- Hybrid + rerank.
- Hybrid + graph + rerank.
- Late-interaction rerank vs. cross-encoder rerank.
- HNSW vs. IVF/PQ vs. DiskANN-style ANN backends.
- With vs. without source-quality constraints.
- With vs. without lifecycle-state constraints.
- With vs. without candidate-plane isolation.
- With vs. without normalized-material support plane.
- With vs. without trace/outcome signals.

Each cell is exercised against the dataset fixtures and query classes defined in `13-retrieval-benchmark-framework.md` and the staged execution flow defined in `14-benchmark-execution-plan.md`. Ablation cells may be combined into compound configurations only where Codex authorizes the composition; combining cells silently does not satisfy the matrix.

## 6. Multi-Stage Retrieval Variants

Multi-stage retrieval variants compose first-stage retrieval with one or more downstream stages. The composition is itself a variable that must be ablated, not a fixed architectural assumption.

Required boundary properties for multi-stage variants:

- A multi-stage variant is one composition under test, not a default. The first-stage retriever, the rerank stage if any, and the fusion or selection function between stages are each independently identified.
- Each stage is measured independently when feasible (first-stage recall and precision; rerank delta; fusion contribution).
- Multi-stage success does not waive contract-safety. A configuration whose multi-stage pass appears to fix a contract violation is treated as having a first-stage contract violation; first-stage retrieval must itself preserve plane separation and contract safety.
- Multi-stage variants do not collapse plane separation. A variant that yields official, candidate, or normalized material in an undifferentiated single stream is not a valid variant.

## 7. Graph Constraint Variants

Graph constraint variants apply structural constraints (source qualification, lifecycle state, ownership, freshness) at retrieval time.

Required boundary properties:

- The source quality graph is consulted as a constraint, not as a retrieval engine.
- Constraints are applied uniformly across the planes they bound. A variant that applies a constraint only on the official plane while admitting unqualified material on the normalized plane is not a valid variant.
- Constraint composition correctness is a measured property. Combinations of constraints must not silently drop under composition (per `13-retrieval-benchmark-framework.md` Section 10).
- Constraint cost is a measured dimension. Variants are evaluated for both correctness and overhead.

## 8. Reranking Variants

Reranking variants apply a more expensive scoring function to a small candidate set returned by first-stage retrieval. Reranking is a downstream stage; it does not replace first-stage retrieval contract safety.

Required boundary properties:

- Reranker contribution is measured independently from first-stage retrieval. Shared candidate sets across variants enable apples-to-apples comparison.
- Late-interaction rerank and cross-encoder rerank are evaluated as separate cells in the matrix.
- A reranker that appears to fix a first-stage contract violation does not waive the first-stage requirement. The first-stage retriever must preserve plane separation and contract safety on its own.
- Reranker training data has provenance and qualification concerns that are recorded in the experiment context. A reranker is not admissible if its training data violates the source qualification boundary.

## 9. Update And Freshness Experiment Boundary

Update and freshness experiments measure the behavior of a configuration under realistic update load and the resulting freshness lag.

Required boundary properties:

- Experiments cover cold build, incremental update under the update profile set, and sustained update load.
- Freshness lag is measured end-to-end from source qualification or route promotion through retrieval availability.
- A configuration that achieves strong quality or performance only under cold builds is recorded as such; freshness behavior is part of the evidence package the Excellence Gate requires (OQ-062 referenced).
- A configuration that silently degrades under sustained update load is disqualified per `13-retrieval-benchmark-framework.md` Section 11 (Failure And Miss Tests).

## 10. Cost Model Experiment Boundary

Cost model experiments record compute and storage cost projections at multiple corpus scales.

Required boundary properties:

- Projections are recorded at a baseline scale, an expected production scale, and a stress scale.
- Cost includes both initial build cost and steady-state update cost.
- Cost projections do not select an architecture by themselves; cost is one input to the Excellence Gate (OQ-061 referenced).
- A configuration with the lowest cost but failing contract safety or producing inadequate quality is disqualified.

## 11. Rollback And Reproducibility Experiment Boundary

Rollback and reproducibility experiments record evidence that a configuration can be reverted without route trust loss and that runs can be reproduced from recorded state.

Required boundary properties:

- Rollback evidence demonstrates that a regression in a configuration can be reverted to the prior baseline configuration without losing route trust, audit trail, or evidence ledger continuity (OQ-063 referenced).
- Reproducibility evidence follows `14-benchmark-execution-plan.md` Section 13: deterministic seeds, version pins, dataset hash verification, environment snapshots.
- A configuration that cannot be reproduced or cannot be rolled back is not eligible for selection regardless of its other scores.

## 12. Contract-Safety Assertions Per Experiment

Every experiment, regardless of family or plane, carries the following contract-safety assertions. Any assertion failure disqualifies the configuration for the experiment cell (per `13-retrieval-benchmark-framework.md` Section 8).

- A raw document must never be returned as a route in a response that returns routes.
- Normalized material must never be returned as a route in a response that returns routes.
- A candidate route must never be returned as an executable official route.
- A demoted, revoked, or retired route must never be returned as an executable official route.
- Public source popularity must not raise route trust at retrieval time.
- High retrieval rank must not promote a candidate.
- Feedback recorded in the intent trace store must not enter retrieval as validation evidence.
- Source trust must not become route trust.

These assertions are not negotiable per experiment. They apply to every cell in the ablation matrix and every variant in multi-stage, graph constraint, and reranking categories.

## 13. Required Evidence Per Experiment

Every experiment cell records, at minimum, the following evidence categories. Substantive evidence content is recorded by the harness (per `14-benchmark-execution-plan.md`); this document records the categories.

- Quality evidence per query class and per plane (recall@k, precision@k, MRR/NDCG, miss classification accuracy, leakage rates as observations).
- Performance evidence (latency percentiles, throughput, memory, build/update cost, freshness lag, filter/constraint/rerank cost).
- Operational evidence (complexity, debuggability, reproducibility, rollback ability, incremental update support, isolation, auditability).
- Contract-safety evidence (pass/fail per assertion in Section 12, with offending response provenance for failures).
- Ablation evidence (delta relative to adjacent ablation cells; demonstration that a layer adds value or that its absence is acceptable).
- Cost model evidence (projections at baseline, expected production, and stress scales).
- Update and freshness evidence (cold build, incremental update, sustained update load behaviors).
- Rollback evidence (demonstrated reversion without route trust or audit loss).
- Reproducibility evidence (deterministic seeds, version pins, dataset hashes, environment snapshots).

The minimum evidence package per cell is owned by Codex (OQ-068 added under WO-14 if not already present in tracker; cross-reference recorded in evidence report).

## 14. Disqualification Rules

A configuration is disqualified for an experiment cell when any of the following occurs:

- Any contract-safety assertion in Section 12 fails.
- Plane separation is violated (official, candidate, or normalized material plane leaks results from another plane).
- A graph constraint silently drops under composition.
- Trace or outcome signals enter the configuration as if they were validation evidence (per OQ-027 boundary).
- The configuration cannot be reproduced from recorded state.
- The configuration cannot be rolled back from a regression to a prior baseline.
- The configuration silently degrades under sustained update load without indication.
- The configuration claims first-stage quality is satisfied because a downstream rerank stage compensates.

Disqualification is recorded with an explicit event per the staged execution flow in `14-benchmark-execution-plan.md`. Disqualification does not silently retry.

## 15. What This Design Does Not Decide

This document explicitly does not decide any of the following. They are bounded by future Codex-authored Work Orders.

- Which indexing architecture is selected.
- Which vendor, library, or implementation is selected.
- Which retrieval family wins.
- Which ablation cell wins.
- Which multi-stage variant wins.
- Which reranker is selected.
- Which ANN backend is selected.
- Which cost profile is acceptable.
- Which freshness target is acceptable.
- Which rollback procedure is acceptable.
- Which metric thresholds qualify a configuration for the Excellence Gate.
- Whether trace or outcome signals are admitted as inputs and under what bounded rules.
- Whether the benchmark wave is complete.
- Whether the indexing scope is complete, best, or production-ready.

The Indexing Excellence Gate (Section K of `00-controller-checklist.md`) blocks any of these decisions until recorded evidence demonstrates superiority under ai-search constraints.

## 16. Out Of Scope

This document is documentation-level only. It does not:

- Implement experiments, benchmark code, harness code, or dataset construction code.
- Build datasets or fixtures.
- Author schemas, fields, types, or data models.
- Author APIs for the harness.
- Author UI for experiment dashboards.
- Author ranking formulas or weights.
- Author runtime compile internals.
- Author validation framework implementation.
- Set substantive metric thresholds or weights.
- Define experiment scheduling, triggering, or operational cadence.
- Treat experiment design as benchmark completion.
- Treat benchmark success as route validation evidence.

All such work requires a future Codex-approved Work Order.
