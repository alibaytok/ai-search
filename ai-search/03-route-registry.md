# ai-search - Route Registry

Document type: Phase 3 anchor / Route registry boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (route contract and lifecycle transitions added under WO-9; runtime-compile eligibility, re-entry, and lifecycle-transition wording corrected under WO-9R)
Work Order: WO-3 (initial draft, approved via WO-3R), WO-9 (rework required), WO-9R (current submission)

---

## 1. Purpose

The route registry is the boundary across which routes change trust state. This document defines its purpose at the documentation level. It names the categories the registry distinguishes, the lifecycle states a route can occupy, the promotion and demotion boundaries, and the provenance requirements that anchor trust. It does not define schemas, APIs, storage, or implementation. Substantive contracts for the registry are owned by Codex and remain deferred to a future Work Order.

The registry is a boundary, not an algorithm. Recording an artifact in one category does not move it across a boundary; only an explicit, recorded event can do that.

## 2. Categories Distinguished By The Registry

The registry distinguishes the following categories. The categories are walls.

- Source material. Artifacts admitted to the corpus through source qualification. Source material is not a route. Source material is not executable.
- Normalized material. Source material transformed into a form admissible for indexing and candidate route building. Normalized material is not a route. Normalized material is not automatically executable.
- Candidate route. A provisional route built from normalized, qualified material by the candidate route builder. A candidate is not an official route. A candidate is not executable on the official path.
- Official route. A route that has cleared validation and been explicitly promoted. Only official routes are trusted as executable.
- Retired / demoted / revoked route. A route that previously held trust and has had it removed by an explicit, evidence-backed event. A retired, demoted, or revoked route is not an official route. The substantive distinction among these three states is owned by Codex and remains an open question.

Raw prompts, raw documents, raw internet content, and raw tool, skill, or agent descriptions are not routes. If qualified, they may serve only as upstream source material. Route candidates may be derived from normalized material; the route candidate, not any raw artifact, is the object of validation and promotion. Only route candidates can be validated and promoted; raw artifacts are never validated and never promoted.

## 3. Route Lifecycle States (Boundary Level)

The registry recognizes the following lifecycle states. Substantive transition rules are owned by Codex.

- Candidate. Built by the candidate route builder. Awaiting validation. Not executable as official.
- Under validation. Validation activity has been recorded against the candidate. Not executable as official.
- Official. Validation evidence has cleared the evidence bar (owned by Codex) and an explicit promotion event has been recorded.
- Demoted. An official route whose trust has been explicitly withdrawn while remaining recorded in the registry. Not executable as official.
- Revoked. A route that has been explicitly removed from the trusted set, distinct from demoted. Not executable as official.
- Retired. A route that has been intentionally taken out of service by an explicit event. Not executable as official.

State transitions are explicit. No state transition is implicit, automatic, or inferred from usage, popularity, recency, semantic similarity, or user preference.

## 4. Route Contract Requirements (Boundary Level)

Added under WO-9. Every route record carries the following items at the documentation-level conceptual boundary. This section names what the record must carry. It does not author schema fields, types, encodings, storage layouts, or implementations. Substantive contracts for each item are owned by Codex and tracked as open questions in `00-open-questions.md`.

- Route identity and version boundary. A route record carries an identity that is stable across versions and a version reference that distinguishes successive revisions of the same identity. The substantive form of identity and versioning is owned by Codex.
- Lifecycle state boundary. A route record carries its current lifecycle state from the set defined in Section 3 (candidate, under validation, official, demoted, revoked, retired).
- Candidate vs. official boundary. A route record carries an explicit indication of whether it is candidate or official. The distinction is preserved in every reference to the record.
- Provenance and source qualification reference boundary. A route record carries a reference to the source qualification record or records that admitted the contributing material into the corpus. Unqualified sources cannot have appeared in the route's derivation chain.
- Normalization reference boundary. A route record carries a reference to the normalization step that produced the inputs from which the route was built.
- Validation evidence reference boundary. A route record carries a reference to the validation evidence record where one applies. Absence of validation evidence is recorded explicitly, not silently treated as presence.
- Promotion, demotion, and revocation event reference boundary. A route record carries a reference to the recorded event or events that produced its current lifecycle state. A state without an event reference is not a valid state.
- Policy and risk gate eligibility boundary. A route record carries a reference to its policy and risk gate disposition where one applies. Gate eligibility for runtime is consulted, not assumed by rank or usage.
- Runtime compile eligibility boundary. A route record carries a recorded reference to its runtime compile eligibility. Eligibility is a Codex-owned boundary; it is not derived mechanically by Claude from lifecycle state, by rank, by usage, or by mere presence of a validation evidence reference. Validation evidence must satisfy the Codex-owned sufficiency bar, an explicit promotion event must have been recorded, and the policy and risk gate (a blocking authority that runtime compile cannot bypass) must not have blocked the route. Eligibility is consulted from the recorded reference; it is never asserted by ranking, usage, or inference. This document does not author runtime compile internals.
- Operational ownership boundary. A route record carries a reference to the operational owners for the source qualifier, route promoter, route revoker, and policy reviewer roles relevant to the route.

These items name boundaries. Their substantive contracts (what exactly is recorded, in what form, with what immutability and access controls) are owned by Codex and tracked in `00-open-questions.md` (in particular OQ-022 for provenance granularity, OQ-030 for Route Card minimum contents, and OQ-005 for validation evidence sufficiency).

## 5. Lifecycle Transitions (Boundary Level)

Added under WO-9. The following are the currently named lifecycle transitions under this boundary. Each named transition requires a recorded event. Any additional transition - including any re-entry path from demoted, revoked, or retired back into the official set - requires a future Codex-authored explicit rule and is not authored here. Substantive criteria for each named transition are owned by Codex; this section names the transitions as boundaries.

- Candidate to under validation. A candidate route enters "under validation" when validation activity is explicitly initiated against it and a corresponding event is recorded.
- Under validation to official. A route transitions to "official" only when validation evidence clears the Codex-owned evidence bar (OQ-005) and an explicit promotion event is recorded.
- Official to demoted. An official route transitions to "demoted" when an explicit demotion event is recorded with reason and supporting evidence.
- Official to revoked. An official route transitions to "revoked" when an explicit revocation event is recorded with reason and supporting evidence. Revocation is distinct from demotion; the substantive distinction is owned by Codex (OQ-023).
- Official to retired. An official route transitions to "retired" when an explicit retirement event is recorded. Retirement is distinct from demotion and revocation; the substantive distinction is owned by Codex (OQ-023).
- Demoted, revoked, and retired routes do not silently become official again. Any re-entry into the official set, if Codex later defines a re-entry path, requires that explicit Codex-defined path, a recorded event, validation evidence that satisfies the Codex-owned sufficiency bar, and an explicit promotion event. This boundary does not specify the form of re-entry (whether by new identity, new version, or another Codex-defined mechanism). No path returns a demoted, revoked, or retired record directly to official without the explicit Codex-defined re-entry path.

### 5.1 Explicit State-Change Rules

- Route state changes require recorded events. No state change is implicit. A state recorded without an event reference is not a valid state.
- Usage, ranking, semantic similarity, popularity, user preference, recency, and repeated successful execution do not change lifecycle state. These signals may inform Codex-owned decisions to initiate an event; they are not the event themselves.
- Raw prompts, raw documents, raw internet content, and raw tool, skill, or agent descriptions are never route records. They may serve as upstream source material only after qualification. Route candidates may be derived from normalized material; the route candidate, not any raw artifact, is the subject of every lifecycle event.

## 6. Promotion Boundary

- Promotion from candidate to official requires recorded validation evidence.
- Promotion requires an explicit promotion event.
- There is no auto-promotion. No path turns a candidate into an official route without recorded validation evidence and an explicit promotion event.
- The evidence bar (what evidence is sufficient), the actor authorized to record the promotion event, and the procedure are owned by Codex and remain open questions.

Promotion applies to candidate routes. It does not apply to raw prompts, raw documents, or raw internet content. None of those are routes; promotion does not have them as a subject.

## 7. Demotion And Revocation Boundary

- Official routes can lose trust. Demotion and revocation are real states, not afterthoughts.
- Demotion and revocation are explicit. They require recorded reasons and supporting evidence.
- Demotion and revocation record that an explicit event has changed the route's standing. They are not retroactive trust statements.
- The substantive criteria for demotion versus revocation versus retirement, the actor authorized to record the event, and the procedural detail are owned by Codex and remain open questions.

A demoted, revoked, or retired route is not a candidate and is not eligible to be re-promoted directly. Any re-entry, if Codex later defines a re-entry path, requires that explicit Codex-defined path, a recorded event, validation evidence that satisfies the Codex-owned sufficiency bar, and an explicit promotion event. This boundary does not specify the form of re-entry. The registry preserves the historical record of the prior official state for audit purposes.

## 8. Provenance Requirements (Boundary Level)

- Every route, in every state, carries provenance.
- Provenance includes at least: a reference to the source or sources from which the route was built, a reference to the qualification record for each contributing source, a reference to the normalization step that produced the inputs, and a reference to the validation evidence where one exists.
- Provenance is required for candidate routes. It is required for official routes. It is required for demoted, revoked, and retired routes so that the historical record remains auditable.
- The specific schema, storage, granularity, and immutability characteristics of provenance are owned by Codex and remain open questions.

## 9. Explicit Statements

- Raw prompts are not official routes. A raw prompt is at most source or candidate material.
- Raw documents are not official routes. A raw document is at most source material until qualified and normalized.
- Raw internet content is not executable and cannot become an official route. It can only contribute upstream material for candidate derivation after qualification and normalization.
- Public and internet material may produce candidate routes only. The official corpus is not reachable from public or internet material without explicit validation and promotion.
- No route becomes official through usage, popularity, click-through, semantic similarity, recency, or user preference.

## 10. Scope Of This Document

This document is documentation-level only. It does not:

- Define schemas, APIs, or data models.
- Define database tables or storage layout.
- Define a UI or any chat surface.
- Define crawler implementation.
- Define ranking formulas.
- Define runtime compile design.
- Define the validation framework's implementation.
- Define the policy and risk gate's implementation.

All such work requires a future Codex-approved Work Order.
