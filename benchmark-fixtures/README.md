# benchmark-fixtures

Scaffold-internal fixture skeleton. Under WO-20 / DC-023 this directory was authored as an empty-only skeleton. Under WO-31 / DC-034 it admits the first synthetic payload wave for three of the six classes; the other three classes remain empty.

## Status

The first synthetic payload wave under WO-31 / DC-034 admits scaffold-internal synthetic JSON payload files under three category subdirectories only:

- `golden-intents/`
- `hard-negatives/`
- `boundary-violations/`

These payloads are scaffold-internal, hand-authored, synthetic-only, and are not benchmark evidence. They exist so that a future fixture loader and the contract-safety paths can be exercised against entries that carry the WO-30 / DC-033 conceptual properties.

The other three category subdirectories remain empty skeletons and continue to enforce the WO-20 / DC-023 invariant:

- `latency-profiles/`
- `update-profiles/`
- `adversarial/`

There is no real benchmark data in this directory. There is no production data, no user data, no production logs, no recent trace, no internet-derived example, no customer name, no private name, no real endpoint, no real vendor, library, model, vector DB, ANN backend, reranker, or production-system name, no generated benchmark result, no benchmark execution output, no validation evidence, no architecture selection, no retention or storage policy, and no production schema. The admitted payload files contain only synthetic, harness-internal markers and synthetic intent surfaces designed to exercise the WO-30 / DC-033 conceptual properties.

Future dataset expansion (additional classes admitted, additional payload waves, real fixture content of any kind), fixture loader implementation, benchmark execution, run artifact retention or storage policy, production artifact contract, and architecture selection each require a separate future Codex packet. This README does not authorize any of those.

## Category Subdirectories

Each subdirectory corresponds to a fixture category named in `ai-search/13-retrieval-benchmark-framework.md` Section 3 (Benchmark Datasets Needed).

Admitted first-wave classes (each may contain `.gitkeep` plus one or more `*.json` synthetic payload files):

- `golden-intents/` - intended for the canonical evaluation set of intents tied to known correct official routes (where one exists) and known miss categories (where none does). The WO-31 first-wave payload here is synthetic only and carries no validation evidence. Construction methodology, ownership, and refresh cadence remain Codex-owned (OQ-035, OQ-049).
- `hard-negatives/` - intended for intents paired with near-miss content that retrieval must not return as official. The WO-31 first-wave payload here is synthetic only and explicitly excludes the official-route plane from the expected output.
- `boundary-violations/` - intended for intents and corpus configurations specifically constructed to trigger contract violation paths (raw material returned as a route, candidate returned as official, demoted route returned as executable, public/internet content returned as official, policy-blocked route returned after the gate). The WO-31 first-wave payload here is synthetic only and records each entry's expected-disqualification posture against the relevant contract assertion.

Excluded first-wave classes (each must still contain exactly `.gitkeep`; the WO-20 / DC-023 empty-only invariant is preserved for these):

- `latency-profiles/` - intended for intents representative of expected production query distribution for latency and throughput measurement. Excluded from the first wave per WO-30 / DC-033 Section 5 because performance measurement is downstream of contract-safety validation per the WO-12R / DC-015 staged flow.
- `update-profiles/` - intended for corpus update events (new sources qualified, routes promoted, routes demoted/revoked/retired, normalization changes) representative of expected production update rates. Excluded from the first wave because state-mutation expectations require separate Codex scope.
- `adversarial/` - intended for intents crafted to expose known retrieval failure modes (vocabulary mismatch, paraphrase, abstraction, rare entities, ambiguous intents). Excluded from the first wave because the failure-mode taxonomy is a separate Codex decision.

## Forbidden Content

This directory must not contain:

- Real benchmark data of any kind.
- Production data.
- User data, real or simulated.
- Production logs.
- Recent intent traces.
- Internet-derived examples or unqualified internet content.
- Customer names, private names, real endpoints.
- Real vendor, library, model, vector DB, ANN backend, reranker, or production-system names.
- Generated benchmark samples or benchmark execution output.
- Validation evidence against any candidate or official route.
- A schema intended as a production artifact contract.
- Architecture, vendor, library, index family, ANN backend, reranker, retrieval family, ablation cell, multi-stage variant, or production-system selection of any kind.
- Metric thresholds, ranking formulas, weights, quality or performance scoring, or production-readiness claims.
- Selection / recommendation / winner / best / production-ready language in any payload string (enforced against `harness/review_package.py:FORBIDDEN_PHRASES`).
- Any retrieval, indexing, or ranking implementation artifact.
- Any non-JSON payload file (`.csv`, `.txt`, or other extensions) anywhere.
- Any payload file in the three excluded classes (`latency-profiles/`, `update-profiles/`, `adversarial/`).

## Future Authorization

Authoring additional dataset content (additional classes, additional payload waves, real benchmark data of any kind), implementing a fixture loader, running any real benchmark, authoring run artifact retention or storage policy, authoring a production artifact contract, or selecting any architecture, vendor, library, index family, ANN backend, reranker, retrieval family, ablation cell, multi-stage variant, or production system each require a future Codex packet. WO-31 authorizes the first synthetic payload wave only; the Indexing Excellence Gate (`ai-search/00-controller-checklist.md` Section K) and the experiment design boundary (`ai-search/15-retrieval-experiment-design.md`) continue to govern what may eventually be measured against any dataset authored here.

## Related Documents

- `ai-search/13-retrieval-benchmark-framework.md` (Section 3): names the fixture categories.
- `ai-search/14-benchmark-execution-plan.md` (Pre-Run Preparation Boundary A): requires versioned, hashed, provenance-recorded fixtures before any run.
- `ai-search/15-retrieval-experiment-design.md`: bounds the ablation matrix and contract assertions that any future fixture must support.
- `ai-search/19-scaffold-dry-run-protocol.md`: the toy/internal-fixture dry-run that has already exercised module composition without touching this directory.
- `ai-search/20-benchmark-fixture-skeleton.md`: the original documentation anchor for the empty-only skeleton.
- `ai-search/29-fixture-payload-contract-boundary.md`: the documentation-level payload contract boundary.
- `ai-search/30-fixture-payload-format-boundary.md`: the scaffold-internal format boundary for the first synthetic payload wave.
- `ai-search/31-first-synthetic-fixture-payload-wave.md`: the scope record for the first wave authored here.
