# ai-search - Retrieval Benchmark Framework

Document type: Phase 4 / Phase 9 research / Retrieval benchmark boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (Section 6 combined-flow ordering corrected under WO-11R)
Work Order: WO-11 (rework required), WO-11R (current submission)

---

## 1. Purpose

This document defines, at documentation level only, the benchmark framework through which indexing and retrieval alternatives surveyed in `12-indexing-and-retrieval-research.md` will be evaluated against ai-search's route-first constraints. It enumerates the datasets, query classes, retrieval planes, metrics, contract violation tests, performance tests, and acceptance gates that must be in place before any indexing architecture can be selected. It does not implement benchmarks, does not run them, does not choose a winner, does not author schemas, code, APIs, or UI. Substantive ownership of benchmark execution and final selection remain with Codex.

The framework is benchmark-first. Selection is not authorized until the framework has been exercised and recorded results meet the acceptance gate that Codex will define.

## 2. Benchmark Philosophy

- The benchmark exists to verify, not to discover. It does not generate validation evidence for routes; it produces recorded evidence about candidate indexing approaches.
- Quality, performance, and contract safety are measured separately. An indexing approach that fails contract safety does not advance regardless of its quality or performance scores.
- No single aggregate score selects a winner. Codex weighs benchmark dimensions per ai-search's constraints; weights are not authored here.
- Reproducibility is a precondition. A benchmark result that cannot be reproduced from recorded state is not admissible.
- Benchmark success is not validation evidence for routes. The benchmark validates the retrieval substrate; validation evidence for routes is recorded by the validation framework (`08-validation-and-feedback.md`).
- Benchmark results are recorded with provenance and version pinning so successor benchmarks can compare against prior runs.

## 3. Benchmark Datasets Needed

- Golden intent set. The canonical evaluation set of intents tied to known correct official routes (where one exists) and known miss categories (where none does). Construction and ownership are Codex-owned (OQ-035, referenced; not duplicated).
- Hard negative set. A set of intents paired with near-miss content that retrieval must not return as official.
- Boundary violation set. A set of intents and corpus configurations specifically constructed to trigger contract violation paths (raw material returned as route, candidate returned as official, demoted route returned as executable, public/internet content returned as official, policy-blocked route returned after the gate).
- Latency profile set. A set of intents representative of expected production query distribution for latency and throughput measurement.
- Update profile set. A set of corpus update events (new sources qualified, routes promoted, routes demoted/revoked/retired, normalization changes) representative of expected production update rates.
- Adversarial set. A set of intents crafted to expose known retrieval failure modes (vocabulary mismatch, paraphrase, abstraction, rare entities, ambiguous intents).

Dataset construction methodology, refresh cadence, and ownership are Codex-owned.

## 4. Golden Intent Set

- The golden intent set is the spine of the benchmark. Without it, no quality claim is admissible.
- Construction methodology is owned by Codex (OQ-035, referenced; not duplicated).
- Each intent in the set carries: the intent text or canonical form, the known correct official route (if one exists), the known miss category (if no correct official route exists), and provenance for the intent's inclusion.
- The set must be versioned. Benchmark runs record the golden intent set version against which they were executed.
- The set must be revisable but not silently editable. Edits require a recorded event.
- The set must not be contaminated by production user feedback or recent traces. Contamination invalidates quality claims.

## 5. Query Classes

Query classes are measured separately so an aggregate score does not hide class-specific regressions.

- Exact-match queries. The intent maps closely to existing route terminology.
- Paraphrase queries. The intent maps to existing route content but uses different words.
- Compositional queries. The intent combines multiple aspects, each of which may map to different parts of routes.
- Rare-entity queries. The intent names entities that appear infrequently in the corpus.
- Ambiguous queries. The intent admits multiple acceptable routes.
- No-route queries. The intent has no acceptable official route and should produce a classified miss.
- Boundary-stress queries. The intent has content that resembles boundary violations (for example, a candidate that looks like an official, a normalized fragment that looks like a route).

## 6. Retrieval Planes To Test

The benchmark exercises retrieval planes separately and in combination.

- Official route plane alone. Verifies that the execution-eligible plane returns only validated official routes and routes correct misses to the miss policy.
- Candidate route plane alone, under Codex-authorized non-official surfacing rules only.
- Normalized material support plane alone. Verifies that this plane returns normalized material with provenance, never as a route in a route-returning response.
- Source quality constraint layer applied to each plane. Verifies that unqualified sources are excluded and that public/internet origin is recorded.
- Combined retrieval flows. Verifies that the planes compose correctly against the WO-5R-locked ordering:
  - Official route retrieval first.
  - Expanded search second.
  - RouteRank orders the official and expanded-search result sets returned by retrieval.
  - If no acceptable official route is found, control passes to the index miss policy.
  - Candidate creation occurs only after expanded search miss classification, where authorized by the index miss policy and the candidate route builder.
  - Candidate ranking or surfacing, if Codex ever authorizes it, is non-official and Codex-owned.
  - The policy and risk gate remains blocking authority before runtime compile.

## 7. Metrics

The benchmark records the following dimensions. Codex weights them; this document does not author weights.

### 7.1 Quality

- Official route recall at k for the golden intent set.
- Official route precision at k for the golden intent set.
- MRR and NDCG for official route retrieval.
- Miss classification accuracy: when no acceptable official route exists, the response routes to the miss policy with the correct miss category.
- False official risk: the rate at which a non-official artifact is returned as if it were an executable official route.
- Candidate leakage rate: the rate at which a candidate is returned in a context that implies official status.
- Normalized-material-as-route leakage rate: the rate at which normalized material appears in a response that returns routes.
- Public/internet trust leakage rate: the rate at which public/internet-origin material is returned in a context implying official trust.
- Policy-blocked route leakage rate: the rate at which a policy-blocked route is returned after the gate has blocked it.

### 7.2 Performance

- p50, p95, and p99 query latency.
- QPS under realistic concurrency.
- Memory footprint (resident set, index size).
- Index build time (cold build).
- Index update latency (incremental update from source qualification through availability).
- Freshness lag (end-to-end from source qualification event to retrieval availability).
- Filter cost (constraint-layer overhead).
- Graph traversal cost (when graph constraints are applied).
- Rerank cost (when a rerank layer is used).

### 7.3 Operational

- Implementation complexity.
- Debuggability of retrieval responses.
- Reproducibility: recorded state suffices to replay a run.
- Rollback ability: revert to prior index or configuration.
- Incremental update support.
- Source / candidate / official isolation (physical or logical).
- Auditability: a retrieval response can be reconstructed from recorded state.

## 8. Contract Violation Tests

These tests are pass/fail. Any failure disqualifies the configuration regardless of quality or performance scores.

- A raw document must never be returned as a route in a response that returns routes.
- Normalized material must never be returned as a route in a response that returns routes.
- A candidate route must never be returned as an executable official route.
- A demoted, revoked, or retired route must never be returned as an executable official route.
- Public source popularity must not raise route trust at retrieval time. A retrieval response must not promote material based on popularity.
- High retrieval rank must not promote a candidate. Persistence in top-k must not change lifecycle state.
- Feedback must not validate. Trace-recorded feedback must not enter retrieval as if it were validation evidence.
- Source trust must not become route trust. A high-trust source contributing to a candidate must not produce an executable official artifact in retrieval.

## 9. Latency / Throughput / Cost Tests

- Latency under realistic query mix (golden intent set plus latency profile set).
- Throughput under concurrent load (steady state and burst).
- Memory under sustained load.
- Index build and update cost under the update profile set.
- Freshness lag measurement end-to-end.
- Cost projections (compute and storage) at multiple corpus scales: a baseline scale, an expected production scale, and a stress scale.

## 10. Graph Constraint Tests

- Qualification constraint correctness: unqualified sources never contribute to retrieval results.
- Lifecycle constraint correctness: only "official" routes appear in the execution-eligible plane.
- Public/internet origin constraint correctness: candidates derived from public/internet material never appear as officials at retrieval.
- Constraint overhead measurement: the cost of applying graph constraints under realistic constraint cardinality.
- Constraint composition correctness: combinations of constraints behave as intended (no constraint is silently dropped under composition).

## 11. Failure And Miss Tests

- Miss classification correctness across all categories in `06-index-miss-policy.md` (no route found, below confidence threshold, policy/risk blocked, stale or revoked, source/corpus coverage gap).
- Behavior when retrieval times out or the index is partially unavailable: the response must not silently return degraded results as if they were official.
- Behavior when the candidate creation trigger fires: retrieval must not invoke candidate building directly; the miss policy governs.
- Behavior when reranking fails: the system must not fall back to first-stage results without indication.

## 12. Regression Tests

- The snapshot of the prior benchmark run is the regression baseline. New runs report delta on every metric.
- Any regression on a contract violation test is a blocker.
- Any regression beyond a Codex-owned threshold on a quality, performance, or operational metric requires recorded justification.
- Regression gate triggers and thresholds are owned by Codex (OQ-036, referenced; not duplicated). Benchmark-specific threshold authority is tracked separately under WO-11 (new OQ).

## 13. Human Review Requirements

- Contract violation test failures require human review. Automated pass/fail is the gate; the recorded reason and remediation are reviewed.
- Quality regressions on the golden intent set require human review of the failing intents to confirm the regression is not an artifact of dataset drift.
- Benchmark configuration changes (dataset version, query class definition, plane composition, constraint application) require human review and a recorded change event.
- Final selection of an indexing architecture is a Codex decision. No automated benchmark score selects a winner.

## 14. Benchmark Acceptance Gate

- The benchmark framework is not a substitute for the regression gate, the policy and risk gate, the validation framework, or the route registry's promotion event. It is a separate gate that bounds index selection.
- Acceptance requires: all contract violation tests pass; quality, performance, and operational metrics fall within Codex-owned thresholds; reproducibility evidence is recorded; the run is documented against a versioned golden intent set and dataset suite.
- A benchmark pass does not constitute architecture selection. Selection is a Codex decision recorded by a future Work Order.
- A benchmark fail does not silently retry. Failures and remediation are recorded; the next run is a new run.

## 15. Out Of Scope

This document is research and design-control content at documentation level only. It does not:

- Implement benchmarks or run them.
- Author benchmark code, dataset construction code, or harness code.
- Author dataset content beyond naming the required sets.
- Author schemas, fields, types, or data models for benchmark results.
- Author APIs.
- Author UI for benchmark dashboards.
- Author ranking formulas or weights.
- Author runtime compile internals.
- Author validation framework implementation.
- Choose a winning index, library, vendor, or configuration.
- Define benchmark pass/fail thresholds substantively. Threshold authority is owned by Codex; OQ-036 covers the regression gate's pass/fail criterion at a different scope, and a benchmark-specific threshold authority question is added under WO-11.

All such work requires a future Codex-approved Work Order.
