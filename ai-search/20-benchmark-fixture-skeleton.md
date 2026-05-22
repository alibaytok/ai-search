# ai-search - Benchmark Fixture Skeleton

Document type: Phase 4 / Phase 9 / Benchmark fixture skeleton boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-20

---

## 1. Purpose

This document records the empty fixture skeleton authorized under WO-20. The skeleton is a directory structure at `benchmark-fixtures/` (root-level sibling to `ai-search/` and `harness/`) that names the fixture categories required by `13-retrieval-benchmark-framework.md` Section 3 but contains no real benchmark data. WO-20 authorizes the empty skeleton only; authoring real fixture content requires a separate Codex packet.

This is not real benchmark dataset creation. This is not benchmark execution. The skeleton exists so that the structural shape of future datasets is recorded, audited, and tested before any payload is added.

## 2. Category List And Intended Future Role

The skeleton has six category subdirectories at boundary level only. Each subdirectory contains a single `.gitkeep` placeholder file under WO-20. Substantive content for each category is Codex-owned and is not authored under WO-20.

- `benchmark-fixtures/golden-intents/` - intended future role: the canonical evaluation set of intents tied to known correct official routes (where one exists) and known miss categories (where none does). Construction methodology, ownership, and refresh cadence are owned by Codex and tracked under OQ-035 (golden intent set construction) and OQ-049 (broader dataset suite ownership).
- `benchmark-fixtures/hard-negatives/` - intended future role: intents paired with near-miss content that retrieval must not return as official.
- `benchmark-fixtures/boundary-violations/` - intended future role: intents and corpus configurations specifically constructed to trigger contract violation paths (raw material returned as a route, candidate returned as official, demoted route returned as executable, public/internet content returned as official, policy-blocked route returned after the gate). Aligns with the contract violation tests in `13-retrieval-benchmark-framework.md` Section 8 and the experiment-design contract-safety assertions in `15-retrieval-experiment-design.md` Section 12.
- `benchmark-fixtures/latency-profiles/` - intended future role: intents representative of expected production query distribution for latency and throughput measurement. Aligns with the latency/throughput/cost tests in `13-retrieval-benchmark-framework.md` Section 9.
- `benchmark-fixtures/update-profiles/` - intended future role: corpus update events (new sources qualified, routes promoted, routes demoted/revoked/retired, normalization changes) representative of expected production update rates.
- `benchmark-fixtures/adversarial/` - intended future role: intents crafted to expose known retrieval failure modes (vocabulary mismatch, paraphrase, abstraction, rare entities, ambiguous intents).

## 3. Explicit Non-Dataset Status

The skeleton is explicitly empty by design under WO-20:

- No real benchmark data of any kind exists in `benchmark-fixtures/`.
- No production data, user data, or generated benchmark samples exist.
- No JSON, CSV, TXT, or other payload files exist beyond the `.gitkeep` placeholders required to preserve empty directories in version control.
- No schema for fixture content is approved. Production artifact contracts remain owned by Codex and are tracked under OQ-076.
- The `harness/tests/test_fixture_skeleton.py` test enforces these invariants on every test run.

## 4. Relationship To Other Documents

The fixture skeleton is one piece of the larger benchmark control surface. Its place in that surface is:

- `13-retrieval-benchmark-framework.md` (Section 3, Benchmark Datasets Needed) named the six fixture categories. WO-20 creates a directory for each named category and nothing more.
- `14-benchmark-execution-plan.md` (Pre-Run Preparation Boundary A) requires versioned, content-hashed, provenance-recorded fixtures before any benchmark run. WO-20 does not version, hash, or provenance-record any fixture because no fixture content yet exists; those obligations attach when content is authored under a future Codex packet.
- `15-retrieval-experiment-design.md` defines the ablation matrix and contract-safety assertions that any future fixture content must support. WO-20 does not author content; it preserves the future content boundary.
- `16-benchmark-harness-scope.md` and `17-harness-implementation-plan.md` established the harness scope and minimum implementation surface; the harness consumes fixtures from approved locations only. The skeleton's empty subdirectories are not approved locations for harness execution; the harness consumes only the scaffold-internal `harness/tests/fixtures/` toy files at present.
- `18-harness-scaffold-decision-lock.md` and `19-scaffold-dry-run-protocol.md` cover the WO-18 minimal scaffold implementation and the WO-19 scaffold-only end-to-end dry-run. Neither reads from `benchmark-fixtures/`; the dry-run reads only scaffold-internal toy fixtures.

## 5. Allowed Future Content Boundary

Future packets that author content into `benchmark-fixtures/` must, at minimum, satisfy these boundary conditions (set by prior decisions; not authored under WO-20):

- Per `14-benchmark-execution-plan.md` Pre-Run Preparation Boundary A: every fixture is versioned, content-hashed, carries provenance, and is revisable only via a recorded event. The golden intent set, hard negative set, and boundary violation set are isolated from any training corpus.
- Per `13-retrieval-benchmark-framework.md` Section 4 (Golden Intent Set): the golden intent set is not contaminated by production user feedback or recent traces.
- Per `15-retrieval-experiment-design.md` Section 12 (Contract-Safety Assertions Per Experiment): the eight contract assertions are non-negotiable across all ablation cells and experiment variants.
- Per the Indexing Excellence Gate (`00-controller-checklist.md` Section K): fixture content does not by itself select an architecture; the gate's evidence requirements continue to apply.

These conditions describe what a future content-authoring packet must respect. WO-20 does not author content; the conditions are recorded here for reference.

## 6. Forbidden Scope

The fixture skeleton is forbidden from containing or representing any of the following, both under WO-20 and in any future modification:

- Real benchmark data of any kind.
- Production data.
- User data (real or simulated).
- Generated benchmark samples produced by any model or pipeline.
- JSON, CSV, TXT, or any other payload files beyond the `.gitkeep` placeholders required by version control.
- A schema intended as a production artifact contract.
- A retrieval, indexing, or ranking implementation artifact.
- A vendor selection, library selection, ANN backend selection, reranker selection, retrieval family selection, ablation cell selection, multi-stage variant selection, or architecture selection of any kind.
- A metric threshold, ranking formula, quality score, or performance score.
- A runtime compile design or validation framework implementation.

## 7. Out Of Scope

This document is documentation-level only. It does not:

- Author real benchmark datasets.
- Author dataset construction methodology, refresh cadence, or ownership rules.
- Author production artifact contracts or schemas.
- Author retrieval, indexing, or ranking system code.
- Select a vendor, library, index family, retrieval family, ANN backend, reranker, ablation cell, multi-stage variant, or architecture.
- Set metric thresholds or weights.
- Author runtime compile internals.
- Author validation framework implementation.
- Treat the skeleton as benchmark-ready, dataset-ready, or selection-ready.

The fixture skeleton records structure only. Any further authoring requires a future Codex-issued Work Order whose scope, allowed files, required content, and evidence requirements are explicit at issue time.
