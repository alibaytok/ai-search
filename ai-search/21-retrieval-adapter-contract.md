# ai-search - Retrieval Adapter Contract Boundary

Document type: Phase 4 / Phase 9 / Retrieval adapter contract boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-21

---

## 1. Purpose

This document defines, at documentation level only, the contract boundary for retrieval adapters that may eventually plug into the benchmark harness. An adapter is the surface through which a candidate retrieval configuration is presented to the harness for evaluation; it is not a production retrieval API and it is not architecture approval.

The adapter boundary exists only for benchmark evaluation. It does not authorize an adapter implementation under WO-21. It does not select any retrieval architecture, vendor, library, index family, ANN backend, reranker, or production system. It does not collapse the official, candidate, normalized-material, source-quality-constraint, and trace/outcome plane separations. It does not create an implicit production contract through use.

WO-21 is the missing surface that names what a future retrieval candidate looks like when it is observed by the harness, without authoring that observation in code. A future Codex packet may implement a mock adapter; a separate future Codex packet may implement a real adapter; neither is authorized under WO-21.

## 2. Adapter Role

A retrieval adapter is a benchmark-facing wrapper around a candidate retrieval configuration. Its role is bounded:

- The adapter exposes controlled inputs to the harness (the inputs named in Section 5) and produces controlled outputs (the outputs named in Section 6).
- The adapter does not decide route validity. Validation evidence is recorded by the validation framework (`08-validation-and-feedback.md`); the adapter consults references where applicable but does not issue them.
- The adapter does not promote, demote, revoke, retire, or otherwise change the lifecycle state of any route. Lifecycle transitions are recorded by the route registry (`03-route-registry.md`) under explicit events; the adapter has no role in that recording.
- The adapter does not evaluate the policy and risk gate. Gate disposition is recorded externally; the adapter consults references where applicable but does not produce them.
- The adapter does not execute routes at runtime. Runtime compile is a downstream phase whose substantive contract is owned by Codex; the adapter has no execution surface.
- The adapter does not select itself or other adapters. Selection authority lives with Codex under the Indexing Excellence Gate (`00-controller-checklist.md` Section K).

## 3. Required Plane Separation

Adapter outputs must preserve five planes at boundary level. The planes are distinguishable in every adapter response; outputs that flatten or co-mingle planes are non-conformant.

- Official route results. Returned only when an official, validated route exists and is eligible (per `03-route-registry.md` Section 4 promotion boundary). Marked as official in every reference.
- Candidate route results. Returned only under Codex-authorized non-official surfacing rules (OQ-016 remains open). Marked as candidate in every reference and visibly distinct from official.
- Normalized material support results. Returned to support candidate derivation and audit. Marked as normalized material; never returned as a route in a route-returning response.
- Source quality constraint observations. Observations about the source qualification, authority, freshness, trust, and provenance applied to the result set. Consulted as a constraint; never lifted into route trust by the adapter.
- Trace and outcome signal observations, if and only if a future Codex packet admits them. Observations recorded via `04-intent-trace-store.md` are bounded evidence per Section 4 of that document; an adapter must not treat them as validation evidence or as selection signals. Until such a future packet, this plane is recorded only as future structure.

## 4. Forbidden Plane Collapse

The following collapses are explicitly forbidden in any adapter output. Each is a contract violation.

- Normalized material returned as a route in a route-returning response.
- A candidate route returned as an executable official route.
- Source trust elevated into route trust by the adapter.
- Trace or outcome feedback used as validation evidence or as a promotion trigger.
- Public or internet content elevated into official status by retrieval rank, score, or popularity.
- Aggregate retrieval performance treated as architecture approval (via aggregate scoring, leaderboard placement, or any other implicit selection mechanism).

These prohibitions apply at every output of the adapter, including responses produced under failure, partial availability, timeout, or other degraded modes. A degraded mode that silently collapses a plane is still a violation.

## 5. Input Boundary

An adapter may consume only the following inputs. Each input class is named at boundary level; substantive content and form are owned by Codex and bounded by prior decisions.

- Codex-approved benchmark fixtures from `benchmark-fixtures/` (currently the empty skeleton authorized under WO-20 / DC-023). No real fixture content yet exists; future Codex packets author fixture content.
- Registered retrieval configuration manifests per Pre-Run Preparation Boundary B of `14-benchmark-execution-plan.md` and the registration authority question recorded as OQ-057.
- Scaffold and harness inputs that a future Codex packet explicitly authorizes the adapter to read.

The adapter must not consume any of the following unless a future Codex packet explicitly authorizes the input:

- Live production user traces or feedback.
- Live route registry state.
- Live corpus state.
- Live source quality graph state.
- Live validation evidence ledger state.
- Live intent trace store state.
- Unqualified internet or public content.
- Any state that has not been admitted through the source qualification gate (`09-source-quality-graph.md`).

The adapter does not silently discover inputs. Every input is named in the active configuration manifest or in a future Codex authorization; opportunistic input ingestion is non-conformant.

## 6. Output Boundary

Adapter outputs are benchmark observations only. They are not production answers, not route promotions, not validation evidence, and not architecture proposals.

Each adapter output must carry, at boundary level, enough structure for the harness to test the following properties. The structure is described conceptually only; this document does not define schemas, JSON templates, classes, function signatures, or implementation types.

- Plane identity: which of the five planes (official, candidate, normalized material, source-quality observation, trace/outcome observation) does this output entry belong to?
- Candidate vs. official distinction: where the output entry represents a route, is it marked candidate or official, and is the marking unambiguous?
- Source and provenance reference presence or absence: does the entry carry a reference to its source qualification record, and is absence recorded explicitly (per `09-source-quality-graph.md` Section 6) rather than treated as presence?
- Lifecycle and status reference presence or absence: does the entry carry a reference to the route's lifecycle state (per `03-route-registry.md` Section 3), and is absence recorded explicitly?
- Policy and risk gate disposition reference presence or absence: does the entry carry a reference to a recorded gate disposition where one applies, and is absence recorded explicitly?
- Executability indicator: is the entry "executable official", "candidate-only (non-executable as official)", or "non-route support material (never a route in any state)"?

Every output entry must answer these questions discriminably. An output that is silent on any of them, or that conflates two answer categories, is non-conformant. The adapter does not assert a positive answer where one is not justified by the inputs; absence is recorded.

## 7. Contract Violation Surface

Adapter outputs must be testable against the contract violation tests defined in `13-retrieval-benchmark-framework.md` Section 8 and the contract-safety assertions per experiment in `15-retrieval-experiment-design.md` Section 12. The full surface, restated for the adapter:

- Raw document must never be returned as a route in a route-returning response.
- Normalized material must never be returned as a route in a route-returning response.
- A candidate route must never be returned as an executable official route.
- A demoted, revoked, or retired route must never be returned as an executable official route.
- Popularity must never raise route trust at retrieval time.
- High retrieval rank must never promote a candidate or elevate it to official.
- Feedback must never validate a route.
- Source trust must never become route trust.

Any violation of any assertion disqualifies the adapter configuration for the run (per `14-benchmark-execution-plan.md` Section 6 and `16-benchmark-harness-scope.md` Section 8). Disqualification is recorded as an explicit halt event in the run's event log; no silent continuation against the disqualified configuration is permitted (per DC-020 halt behavior).

## 8. Non-Selection Boundary

The harness may consume adapter outputs as evidence under a future benchmark execution packet. It may not, under any future packet, do any of the following based on adapter outputs alone:

- Recommend an adapter.
- Rank adapters as architecture choices.
- Select a vendor, library, index family, ANN backend, reranker, retrieval family, ablation cell, or multi-stage variant.
- Declare a winner, best, production-ready, or sufficient configuration.
- Treat aggregate performance as selection authority.

Selection remains under the Indexing Excellence Gate (`00-controller-checklist.md` Section K) and is a Codex decision recorded by a future Codex-authored architecture selection Work Order. The adapter contract does not bypass the gate; it bounds what the gate may eventually evaluate against.

## 9. Registration Boundary

Adapter configurations must be registered before any benchmark run that consumes them. Registration is a Codex-authorized activity; the adapter contract does not author the registration mechanism.

- The substance of an adapter registration record (its fields, its provenance, its version pinning, its authority signature) is owned by Codex and is not authored under WO-21.
- Registration authority remains tracked under OQ-057 (configuration registration authority) and is open.
- This document does not define a manifest schema. Any future schema or template is owned by a future Codex packet and may not be implied by adapter behavior under use (per RK-053 and RA-068 boundaries).

## 10. Mock And Future Implementation Boundary

A mock adapter may be authored under a future Work Order, scoped explicitly by Codex. Under that future packet:

- The mock adapter is scaffold-internal and produces deterministic, fixture-derived observations only.
- The mock adapter does not connect to any retrieval system, vendor, library, ANN backend, reranker, or external service.
- The mock adapter does not become a real retrieval implementation by use. A real retrieval adapter requires a separate Codex authorization that explicitly approves real-system contact, dependency policy beyond the first scaffold (OQ-075), and any input expansion beyond the scaffold inputs.
- The mock adapter conforms to every plane separation requirement in Section 3, every input boundary in Section 5, every output boundary in Section 6, and every contract violation assertion in Section 7.

Until a Codex packet authorizes a mock implementation, no adapter code, schema, or interface is authored, and the harness continues to read only the scaffold-internal toy fixtures under `harness/tests/fixtures/`.

## 11. Relationship To Existing Documents

The adapter contract sits inside the constraint surface already established by prior Work Orders. Cross-references for any reader inspecting the contract:

- `13-retrieval-benchmark-framework.md` (Section 7 metrics, Section 8 contract violation tests, Section 10 graph constraint tests, Section 11 failure and miss tests) names the substantive measurements and assertions that any adapter must remain testable against.
- `14-benchmark-execution-plan.md` (Pre-Run Preparation Boundaries A and B; Stages 0 through 5) names the lifecycle the adapter participates in as a registered configuration.
- `15-retrieval-experiment-design.md` (Sections 3-8 family/plane/ablation/variant boundaries; Sections 12-13 contract-safety assertions and required evidence) names the experiment surface the adapter must support without becoming architecture selection.
- `16-benchmark-harness-scope.md` (Sections 3-14 allowed and forbidden responsibilities, plane separation, halt behavior, non-selection) names the harness behaviors the adapter interacts with.
- `19-scaffold-dry-run-protocol.md` (Sections 3-7 composition order, halt points, returned package boundary) names the scaffold-level dry-run pattern that any future adapter exercise must respect.
- `20-benchmark-fixture-skeleton.md` (Sections 2-6 category list, non-dataset status, forbidden content) names the fixture-side of the contract; the adapter consumes from this skeleton only after future Codex packets author content into it.
- `00-controller-checklist.md` Section K (Indexing Excellence Gate) continues to govern selection. The adapter contract does not bypass the gate.

## 12. Out Of Scope

This document is documentation-level only. It does not:

- Author adapter code, interface classes, function signatures, type definitions, JSON templates, or schemas.
- Author a registration manifest schema or template.
- Implement any retrieval, indexing, or ranking system.
- Make any real retrieval call.
- Select a vendor, library, index family, retrieval family, ANN backend, reranker, ablation cell, multi-stage variant, or architecture.
- Author benchmark fixtures or dataset content.
- Run any benchmark.
- Set metric thresholds or weights.
- Score adapters on quality or performance.
- Design a production retrieval API.
- Author runtime compile internals.
- Author validation framework implementation.
- Treat the adapter contract as adapter authorization, benchmark authorization, dataset authorization, or architecture authorization.

All such work requires a future Codex-approved Work Order whose scope, allowed files, required content, forbidden scope, acceptance criteria, and evidence requirements are explicit at issue time.
