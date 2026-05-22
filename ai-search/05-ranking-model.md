# ai-search - RouteRank (Ranking Model Boundary)

Document type: Phase 4 anchor / RouteRank boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-5

---

## 1. Purpose

RouteRank is the boundary at which retrieved route results are ordered for intent fit. This document defines RouteRank at the documentation level only: its purpose, what it is not, the inputs it consumes at boundary level, the constraints it must preserve, the explainability it must produce, and how it routes failure and rejection cases. It does not define a ranking formula, score weights, feature weights, scoring function, model architecture, algorithm, schema, API, storage, UI, or any runtime behavior. Substantive contracts for those are owned by Codex and remain deferred.

RouteRank exists to order route result sets produced during official route search and expanded search. If RouteRank cannot identify an acceptable official route, control passes to the index miss policy (`06-index-miss-policy.md`); candidate creation, where the miss policy authorizes it, remains a step after expanded search miss classification and is governed by that policy together with the candidate route builder (`11-candidate-route-builder.md`). Candidate ranking or surfacing, if Codex ever authorizes it, is non-official and is owned by Codex. RouteRank is a relevance and trust ordering, not an execution authority.

## 2. What RouteRank Is Not

RouteRank is explicitly NOT:

- Semantic search alone. Semantic similarity is one relevance signal consumed by RouteRank; it is not RouteRank's definition and it is not sufficient for execution.
- Popularity ranking. Usage frequency, click-through, recency of selection, repetition, and accumulated engagement do not dominate the rank.
- User preference ranking. User preference is bounded evidence; it cannot dominate trust, override validation, or change the official vs. candidate distinction.
- An agent, tool, or skill selector. RouteRank does not select an agent, a tool, or a skill. It ranks routes. Routes are the product object.
- An auto-promotion mechanism. RouteRank does not promote candidates. No rank value, however high or stable over time, promotes a candidate to official.
- A policy or risk gate replacement. RouteRank does not enforce policy or risk controls. The policy and risk gate runs downstream of ranking and is not bypassed by rank.
- A validation replacement. RouteRank does not validate routes. Validation is a separate phase whose substantive contract is owned by Codex.

## 3. Ranking Boundary

RouteRank:

- Ranks route results for intent fit.
- Does not create routes. Candidate creation is governed by `06-index-miss-policy.md` and `11-candidate-route-builder.md`.
- Does not promote candidates. Promotion is an explicit, evidence-backed event recorded by the route registry (`03-route-registry.md`).
- Does not validate routes. Validation is a downstream phase.
- Does not compile routes. Runtime compile is a downstream phase.
- Does not bypass the policy and risk gate. A high rank does not grant a route any exemption from the gate.

Official validated routes are the execution-eligible class. Candidate routes are not execution-eligible as official routes. Whether candidate routes surface in ranked results at all, and under what visibility rules distinct from official routes, is owned by Codex (tracked as an open question in `00-open-questions.md`).

## 4. Required Ranking Inputs (Boundary Level)

RouteRank consumes the following inputs at boundary level. The specific schema, encoding, granularity, and weighting of each input are owned by Codex and are not authored under WO-5.

- Intent context. A reference to the captured intent for the current interaction.
- Official route status. Whether each candidate-for-ranking is recorded as an official validated route in the route registry.
- Candidate route status. Where candidate routes are eligible for non-official surfacing under future Codex rules, RouteRank consumes the candidate status reference. Candidate status is not equivalent to official status.
- Validation evidence reference. A reference to the validation evidence record for any route under ranking. Absence of validation evidence is recorded explicitly, not silently treated as presence.
- Provenance and source qualification reference. A reference to the qualification record for the source or sources that contributed to the route.
- Normalization reference. A reference to the normalization step from which the route or candidate was built.
- Route lifecycle state. The lifecycle state recorded in the route registry (candidate, under validation, official, demoted, revoked, retired). State is consulted as a constraint per Section 5, not only as a tie-breaker.
- Policy and risk signal reference. A reference to any prior policy and risk gate evaluation associated with the route or the intent context. RouteRank does not run the gate; it consumes the reference.
- Historical outcome and feedback reference. A reference to prior outcomes and user feedback recorded in the intent trace store (`04-intent-trace-store.md`). Feedback is bounded evidence per Section 5; it does not dominate.
- Freshness and staleness signal. A reference to any recorded freshness or staleness indicator for the route. The substantive freshness signal and the authority to mark staleness are owned by Codex (tracked as open questions in `00-open-questions.md`).

## 5. Required Ranking Constraints

The following constraints are invariant. RouteRank must preserve them.

- Official validated routes are the execution-eligible class. Only routes whose lifecycle state is "official" and whose validation evidence is recorded may be presented as executable by ranking.
- Candidate routes are not execution-eligible as official routes. Where Codex authorizes a non-official surfacing rule, candidates may appear in rank output only with their candidate status clearly distinguished from official status. Candidates are never returned as executable officials by rank.
- Public and internet origin does not raise a route toward official status by rank. Candidate routes derived from public or internet material remain candidates; promotion still requires validation evidence and an explicit promotion event recorded by the route registry.
- User preference is bounded and cannot dominate trust. Preference signals enter ranking as bounded evidence. They do not override validation evidence, do not change route status, and do not bypass the policy and risk gate.
- Semantic similarity is a relevance signal only, not execution authority. A high similarity score does not satisfy the validation gate, does not promote a candidate, and does not authorize execution.
- The policy and risk gate can block a high-ranked route. RouteRank's output is subject to the gate downstream; a high rank does not exempt any route from the gate.
- Revoked, demoted, retired, and stale routes cannot rank as executable official routes. They are removed from the execution-eligible class regardless of their relevance to the intent.

## 6. Explainability Requirements

- Every ranked result must be explainable by references, not by opaque scores or vibes. The explanation is a structured set of references, not a free-form narrative.
- The explanation must include, where applicable: the route's status (official vs. candidate); the validation evidence reference; the source and provenance reference; the route lifecycle state; and the policy and risk gate disposition.
- The explanation must not expose prompt, skill, or agent concepts to end users. Explainability is a property of audit and of surface presentation; surface vocabulary is owned by Codex.
- Absence is recorded, not silent. Where an explanation reference is missing (for example, where no validation evidence exists), the absence is recorded explicitly. The explanation does not omit the field.
- The form of the explanation artifact - returned with every ranked result, available on-demand, or stored only in the trace - is owned by Codex and remains an open question.

## 7. Failure And Rejection Boundaries

- Low-confidence ranked result. If the ranked result fails the confidence threshold for execution, it is routed to the index miss policy for classification. It is not forced into execution. The confidence threshold's definition is owned by Codex (tracked as an open question in `00-open-questions.md`).
- No acceptable route. If no route is acceptable, the result is routed to the index miss policy. RouteRank does not synthesize an answer, does not return arbitrary content, and does not invoke the candidate route builder directly. Candidate creation remains governed by the index miss policy.
- Policy-blocked result. If a route is blocked by the policy and risk gate, the block is not bypassed by re-ranking. A blocked result does not become a candidate by virtue of being blocked; the candidate creation trigger rules in the index miss policy are unaffected by ranking.

In all three cases, ranking does not invent execution. Downstream behavior is owned by the index miss policy, the policy and risk gate, the candidate route builder, and the route registry.

## 8. Scope Of This Document

This document is documentation-level only. It does not:

- Define a ranking formula, score weights, feature weights, scoring function, or model architecture.
- Define algorithms, retrieval mechanisms, or scoring procedures.
- Define schemas, APIs, or data models.
- Define database tables, storage layout, or retention engines.
- Define a UI or any chat surface.
- Define runtime compile design.
- Define the validation framework's implementation.
- Define the policy and risk gate's implementation.
- Define crawler implementation.

All such work requires a future Codex-approved Work Order.
