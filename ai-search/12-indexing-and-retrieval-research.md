# ai-search - Indexing And Retrieval Research

Document type: Phase 4 / Phase 9 research / Indexing and retrieval evaluation boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (research sources updated under WO-11R)
Work Order: WO-11 (rework required), WO-11R (current submission)

---

## 1. Purpose

This document surveys indexing and retrieval families that could be evaluated for ai-search and names the tradeoffs that the benchmark framework (`13-retrieval-benchmark-framework.md`) must measure. It is research and design-control content at documentation level only. It does not select a winning architecture, does not recommend a single technology, does not implement, and does not pick a vendor. Substantive selection authority remains with Codex.

The purpose of the survey is to scope what must be measured before any indexing architecture can be selected. The premise is that the right answer for ai-search depends on route-first constraints, the candidate vs. official distinction, source qualification, public/internet ingestion limits, and the policy and risk gate boundary - not on aggregate benchmark scores alone.

## 2. Why There Is No Universal Best Index

- Retrieval quality is not a single number. Different intent classes, different content classes, and different latency budgets favor different indexing approaches.
- Quality benchmarks vary widely by dataset and by query class. An index that ranks well on a news-style dataset may rank poorly on procedural or task-style intents, and vice versa.
- Cost, latency, and operational characteristics often diverge from quality. The lowest-latency option may have the highest update cost; the highest-quality option may not be operationally feasible at scale.
- ai-search has constraints beyond generic retrieval: official routes are the only execution-eligible class; candidate routes must be visibly distinct; source qualification gates corpus entry; public/internet origin remains candidate-only. An indexing approach that maximizes generic relevance but blurs these boundaries fails ai-search's route-first thesis even if its top-k recall is high.
- Different retrieval planes serve different purposes. Indexing normalized material to support candidate derivation is a different task from indexing candidate routes for ranked surfacing, which in turn is different from indexing official routes for execution-eligible retrieval. A single index may not serve all three planes equally well.

## 3. ai-search Retrieval Constraints

The following constraints bound any indexing choice for ai-search. They are documented here as benchmark inputs; they are not authored anew.

- Search-first thesis (`01-thesis.md`): search returns a route, not a synthesized answer.
- Existing validated route first (`06-index-miss-policy.md`): the official route corpus is searched before any expanded search and before any candidate creation.
- Candidate vs. official distinction (`03-route-registry.md`): candidate routes are not execution-eligible; their visibility in search is owned by Codex.
- Source qualification (`02-search-corpus.md`, `09-source-quality-graph.md`): unqualified sources cannot contribute material; the source quality graph is consulted as a constraint, not as a trust generator.
- Public/internet origin: candidate-only at the route level; cannot bypass qualification, normalization, validation, promotion, or the policy and risk gate.
- Validation evidence (`08-validation-and-feedback.md`): a precondition for official trust; retrieval performance does not substitute.
- Policy and risk gate: blocking authority that retrieval cannot bypass.
- No auto-promotion: retrieval signals do not promote candidates.

## 4. Retrieval Planes Under Consideration

The benchmark must consider these planes separately. They are conceptual planes; whether they are implemented as separate indices, separate views over a shared index, or some Codex-authorized mix is a future selection decision.

- Official route retrieval plane. The plane consulted first per the miss policy. Returns official validated routes only.
- Candidate route retrieval plane. The plane that supports any Codex-authorized non-official surfacing of candidate routes. Visibility rules owned by Codex (OQ-016).
- Normalized material support plane. The plane that supports candidate route building and audit. Returns normalized material with provenance pointers. Normalized material is not a route; this plane does not return routes.
- Source quality graph constraint layer. Not a retrieval plane in itself; consulted as a constraint over the other planes (qualification status, public/internet origin, trust state).
- Trace and outcome signal layer. Not a retrieval plane in itself; recorded by the intent trace store (`04-intent-trace-store.md`) and consulted as a signal, not as validation evidence.

## 5. Indexing Families To Evaluate

Each family is described as a candidate for benchmark inclusion. Tradeoffs are summarized; winners are not selected.

### 5.1 Lexical Retrieval (BM25 / Sparse Keyword Search)

Strengths: high precision on exact and near-exact term matches; transparent and explainable; mature operational characteristics; cheap to index and update; well-understood failure modes.

Weaknesses: vocabulary mismatch (intent expressed in one wording, route described in another); limited handling of paraphrase and abstraction; sensitive to tokenization, stemming, and stopword choices.

Benchmark notes: a strong baseline against which other families are compared; should be tested as a standalone plane and as part of hybrid retrieval.

### 5.2 Dense Vector Retrieval (Embeddings With ANN)

Strengths: handles paraphrase, abstraction, and semantic similarity; tolerant of vocabulary mismatch; well-suited to dense embeddings produced by general-purpose or domain-specific models.

Weaknesses: opacity (similarity scores are not directly interpretable); susceptible to embedding drift across model versions; semantic similarity alone does not constitute trust; embedding choice introduces additional Codex-owned decisions; can produce confident but incorrect matches on rare terms or named entities.

Benchmark notes: must be evaluated with explicit guardrails against the anti-pattern "similarity equals execution authority." Per `05-ranking-model.md`, similarity is a relevance signal only.

### 5.3 Hybrid Sparse + Dense Retrieval

Strengths: combines BM25 precision on exact terms with dense recall on paraphrased intents; commonly outperforms either family alone on heterogeneous query mixes.

Weaknesses: doubles operational complexity; the combination function (linear fusion, reciprocal rank fusion, learned fusion) is itself a Codex-owned decision and a benchmark variable; tuning surface is larger.

Benchmark notes: hybrid configurations should be tested with multiple fusion strategies, and the fusion function should be measured independently.

### 5.4 Graph-Constrained Retrieval

Strengths: enforces structural constraints (source qualification, candidate vs. official distinction, lifecycle state) at retrieval time, not after the fact; aligns naturally with ai-search's invariants because the source quality graph and the route registry already define graph-shaped state.

Weaknesses: graph traversal cost; correctness of the constraint definition becomes a benchmark variable; constraint complexity can grow if not bounded.

Benchmark notes: graph constraints are not a retrieval plane in themselves; they are a constraint layer applied to other planes. The benchmark must measure both the cost and the correctness of constraint application.

### 5.5 Metadata-Filtered Retrieval

Strengths: supports filtering by lifecycle state, source qualification status, freshness, ownership, and other recorded boundaries; cheap when filter cardinality is low; preserves boundary distinctions cleanly.

Weaknesses: filter cost can grow with cardinality and combination depth; some indexing families (notably ANN) have weaker support for high-selectivity filters; pre-filter vs. post-filter performance differs widely.

Benchmark notes: every retrieval plane must support metadata filters that distinguish official from candidate, qualified from unqualified, and current from demoted/revoked/retired. Filter cost is a measured dimension.

### 5.6 Late-Interaction Retrieval (ColBERT-Style)

Strengths: per-token interaction captures finer-grained relevance than single-vector dense retrieval; tends to be stronger on long-form or compositional intents.

Weaknesses: substantially higher storage cost (per-token vectors); higher query-time cost; operational maturity varies across implementations.

Benchmark notes: candidate for the rerank stage rather than first-stage retrieval; must be compared to single-vector dense retrieval on the same query classes and the same latency budget.

### 5.7 HNSW-Style Graph ANN

Strengths: strong recall vs. latency tradeoff for in-memory dense retrieval at moderate scale; well-supported across vector engines; predictable query-time complexity.

Weaknesses: in-memory cost grows with corpus size; update characteristics vary by implementation; filter integration depends on engine.

Benchmark notes: a primary candidate for the dense plane; benchmark must measure recall at multiple ef values and at multiple corpus sizes.

### 5.8 IVF / IVF-PQ Style Partitioned ANN

Strengths: scales to large corpora by partitioning the vector space; product quantization reduces memory at the cost of recall; supports parallelism across partitions.

Weaknesses: recall sensitivity to partition count and probe count; product quantization introduces recall loss that depends on dimensionality and quantizer training; update cost varies by implementation.

Benchmark notes: alternative dense plane candidate, especially at larger scales; benchmark must vary partition/probe parameters and measure recall vs. latency curves.

### 5.9 DiskANN-Style Disk-Backed ANN

Strengths: serves much larger corpora than in-memory ANN by keeping the index on SSD with bounded in-memory state; competitive recall at moderate latency.

Weaknesses: latency sensitivity to disk hardware and I/O contention; update characteristics constrained; operational tooling less mature than in-memory options.

Benchmark notes: candidate when corpus size or memory cost preclude in-memory ANN; benchmark must include realistic disk and I/O conditions.

### 5.10 Reranking Layer Options

Strengths: a separate reranking stage can apply a more expensive scoring function (cross-encoder, late-interaction, learned-to-rank) to a small candidate set returned by first-stage retrieval; can substantially improve top-k quality without first-stage cost.

Weaknesses: adds latency and cost; the reranker becomes a separate Codex-owned decision and a benchmark variable; reranker quality depends on training data, which has its own provenance and qualification concerns.

Benchmark notes: rerankers should be evaluated independently from the first-stage retriever, with shared candidate sets, so the contribution of each stage is measurable.

## 6. Graph And Constraint Layers

- The source quality graph (`09-source-quality-graph.md`) is consulted as a constraint, not as a retrieval engine. The graph records qualification, authority, trust, freshness, and provenance; it does not return routes.
- The route registry (`03-route-registry.md`) supplies lifecycle state and the candidate vs. official distinction as constraints over every retrieval plane.
- Policy and risk gate disposition (a Codex-owned boundary) is consulted as a constraint over the official retrieval plane.
- Constraint application is part of retrieval, not part of trust. Constraints filter what may be returned; they do not create trust where validation evidence is absent.

## 7. Ranking vs. Retrieval vs. Validation Boundary

- Retrieval returns candidate result sets. It does not rank for execution and does not validate.
- Ranking (`05-ranking-model.md`) orders retrieved result sets for intent fit. It is one stage above retrieval.
- Validation (`08-validation-and-feedback.md`) produces recorded evidence that satisfies a Codex-owned sufficiency bar. It is independent of retrieval performance.
- Promotion records an explicit event that elevates a candidate to official. It is independent of retrieval performance and of ranking score.

Retrieval performance does not promote candidates. Retrieval recall does not validate routes. Retrieval precision does not exempt routes from the policy and risk gate.

## 8. Candidate / Official / Normalized Material Separation

- Official route retrieval is the execution-eligible plane. Indexing choices must preserve the property that only validated official routes appear in this plane.
- Candidate route retrieval, where Codex authorizes any non-official surfacing, must visibly distinguish candidates from officials. Indexing choices that blur this distinction (for example, single-plane retrieval over both classes with no preserved trust label) are unsafe.
- Normalized material indexing exists to support candidate route building and audit. Normalized material must never appear as a route in any retrieval response that returns routes. Indexing choices that expose normalized material as a route - directly or indirectly - violate the corpus boundary.

The benchmark framework must measure the rate at which each indexing configuration violates these separations.

## 9. Performance Tradeoffs To Measure

The benchmark framework defines the substantive metrics in `13-retrieval-benchmark-framework.md`. The following are the high-level dimensions:

- Query latency at the relevant percentiles (p50, p95, p99).
- Throughput under realistic concurrency.
- Memory footprint and index size.
- Index build time and incremental update latency.
- Freshness lag from source qualification through availability in retrieval.
- Filter and constraint-layer overhead.
- Reranker overhead when applicable.

## 10. Quality Tradeoffs To Measure

- Recall at k for official route retrieval.
- Precision at k for official route retrieval.
- Mean reciprocal rank (MRR) and normalized discounted cumulative gain (NDCG) for ranked retrieval evaluation.
- Miss classification accuracy: when no acceptable validated route exists, does retrieval correctly route to the miss policy?
- False official risk: how often does retrieval return a non-official artifact as if it were an executable official route?
- Candidate leakage rate: how often does a candidate route appear in a context that implies official status?
- Normalized-material-as-route leakage rate: how often does normalized material appear in a response that returns routes?
- Public/internet trust leakage rate: how often does public/internet-origin material appear in a context that implies official trust?
- Policy-blocked route leakage rate: how often does a policy-blocked route appear in a response after the gate has blocked it?

## 11. Operational Tradeoffs To Measure

- Implementation and operational complexity.
- Debuggability and explainability of retrieval results.
- Reproducibility of benchmark runs (deterministic seeds, version pinning, dataset hashing).
- Rollback capability when a new index or configuration regresses.
- Incremental update support and update latency under realistic write load.
- Source / candidate / official isolation: are the three classes physically or logically separable for audit?
- Auditability: can a retrieval response be reproduced from recorded state for incident review?

## 12. Explicit Anti-Patterns

The following framings are explicitly rejected as outcomes of the benchmark process.

- "Single-plane retrieval over all material is acceptable if recall is high." Recall does not waive the candidate vs. official distinction.
- "Whichever index has the best aggregate score is the right index." Aggregate scores ignore contract safety and operational characteristics.
- "Retrieval performance is validation evidence." Performance is not evidence.
- "Source trust transfers to route trust via retrieval rank." Source trust does not transfer.
- "If the reranker fixes the contract violations, the first-stage retriever does not need to preserve boundaries." The reranker is downstream of retrieval; first-stage retrieval must itself preserve the candidate vs. official distinction and the source qualification boundary.
- "Benchmark success means the index can ship." Benchmark success is one input; final selection authority is Codex's.

## 13. Out Of Scope

This document is research and design-control content at documentation level only. It does not:

- Select a winning indexing family or technology.
- Recommend a single vendor, library, or implementation.
- Author benchmark code.
- Author schemas, fields, types, or data models.
- Author APIs.
- Author UI.
- Author ranking formulas or weights.
- Author runtime compile internals.
- Author validation framework implementation.
- Author the source quality graph, the route registry, or the policy and risk gate substantive contracts.
- Make any selection that requires Codex-authored architecture direction.

## 14. Research Sources Consulted

The following sources are recorded as evidence inputs for the benchmark design under `13-retrieval-benchmark-framework.md`. None of these sources is imported as architecture direction; each is referenced as an evidence input to be re-evaluated by ai-search's benchmark against ai-search's route-first constraints, the candidate vs. official distinction, source qualification, and the policy and risk gate. Final selection authority remains with Codex.

### 14.1 Retrieval Benchmark References

- BEIR: A Heterogeneous Benchmark for Zero-shot Evaluation of Information Retrieval Models (Thakur et al., 2021). https://arxiv.org/abs/2104.08663. Heterogeneous IR benchmark covering multiple retrieval task families. Referenced as evidence for the position that retrieval quality varies by dataset and task; informs the query class separation in `13-retrieval-benchmark-framework.md` Section 5.
- ANN-Benchmarks. https://ann-benchmarks.com/. Public reference suite for comparing approximate nearest neighbor implementations on recall vs. queries-per-second tradeoffs. Referenced as evidence input for performance dimensions in `13-retrieval-benchmark-framework.md` Sections 7 and 9. ai-search's benchmark adds contract violation tests and isolation tests that ANN-Benchmarks does not address.

### 14.2 Dense Retrieval And ANN Algorithms

- HNSW: Efficient and robust approximate nearest neighbor search using Hierarchical Navigable Small World graphs (Malkov & Yashunin, 2016/2018). https://arxiv.org/abs/1603.09320. Foundational graph-based ANN method. Referenced as evidence input for Section 5.7 (HNSW family). No specific recall, latency, or parameter claim is imported as direction.
- FAISS: Billion-scale similarity search with GPUs (Johnson, Douze, and Jegou, 2017). https://arxiv.org/abs/1702.08734. Library and methodology for large-scale ANN including IVF and product quantization. Referenced as evidence input for Sections 5.7 and 5.8. No specific performance claim is imported as direction.
- DiskANN: Fast Accurate Billion-point Nearest Neighbor Search on a Single Node (Subramanya et al., NeurIPS 2019). https://www.microsoft.com/en-us/research/publication/diskann-fast-accurate-billion-point-nearest-neighbor-search-on-a-single-node/. Disk-backed ANN for corpora that exceed in-memory budgets. Referenced as evidence input for Section 5.9. No specific scale or recall claim is imported as direction.
- ScaNN: Accelerating Large-Scale Inference with Anisotropic Vector Quantization. https://research.google/blog/announcing-scann-efficient-vector-similarity-search/. Anisotropic quantization for high-recall ANN. Referenced as evidence input adjacent to the IVF/IVF-PQ family in Section 5.8 and to dense retrieval benchmark planes more broadly. No specific quantization or quality claim is imported as direction.

### 14.3 Late-Interaction And Hybrid Retrieval

- ColBERT: Efficient and Effective Passage Search via Contextualized Late Interaction over BERT (Khattab and Zaharia, SIGIR 2020). https://arxiv.org/abs/2004.12832. Per-token late-interaction model. Referenced as evidence input for Section 5.6 (late-interaction family). No specific quality or operational claim is imported as direction.
- SPLADE: Sparse Lexical and Expansion Model for First Stage Ranking (Formal et al., SIGIR 2021). https://arxiv.org/abs/2107.05720. Learned sparse retrieval combining lexical interpretability with neural expansion. Referenced as evidence input for hybrid retrieval evaluation in Section 5.3 and for the lexical/dense interaction discussion. No specific quality or coverage claim is imported as direction.

### 14.4 Internal ai-search Documents

The following prior Work Order outputs are the constraint source for ai-search's specific retrieval requirements and are referenced throughout this document and `13-retrieval-benchmark-framework.md`: `01-thesis.md`, `02-search-corpus.md`, `03-route-registry.md`, `04-intent-trace-store.md`, `05-ranking-model.md`, `06-index-miss-policy.md`, `08-validation-and-feedback.md`, `09-source-quality-graph.md`, `10-corpus-ingestion-pipeline.md`, `11-candidate-route-builder.md`.

### 14.5 Sources As Evidence, Not As Direction

None of the external sources above is imported as architecture direction. They are evidence inputs that inform what must be measured by the benchmark. ai-search's benchmark framework (`13-retrieval-benchmark-framework.md`) re-evaluates any specific source's claims against ai-search's constraints. A claim in a paper or a benchmark suite is admissible as a benchmark input; it is not admissible as a selection decision. The benchmark's contract violation tests, isolation tests, and route-first constraints are independent of any external source. Final selection authority is Codex's.
