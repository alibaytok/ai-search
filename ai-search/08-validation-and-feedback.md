# ai-search - Validation And Feedback

Document type: Phase 3 / Phase 7 anchor / Validation and feedback boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (re-entry over-specification corrected under WO-9R)
Work Order: WO-9 (rework required), WO-9R (current submission)

---

## 1. Purpose

This document defines the validation evidence boundary and the feedback boundary at the documentation level. It names what validation is, what validation is not, what is required for promotion, and what is required for demotion, revocation, and retirement. It does not define schemas, schemas for evidence records, validation test framework implementation, scoring procedures, APIs, storage models, UI, or any algorithmic behavior. Substantive contracts for the validation framework, the evidence ledger, and the policy and risk gate are owned by Codex and remain deferred to future Work Orders.

Validation is the boundary across which a route candidate may become an official route. It is the only path to official trust. No other signal substitutes for it.

## 2. What Validation Is

- Validation is the process by which a candidate route accumulates recorded evidence that satisfies a Codex-owned sufficiency bar.
- Validation applies to route candidates only. It does not apply to raw prompts, raw documents, raw internet content, raw tool, skill, or agent descriptions, or source material. None of those are routes; validation has no subject when applied to them.
- Validation produces a validation evidence record, which the route registry (`03-route-registry.md`) references when transitioning a candidate to official via an explicit promotion event.
- Validation evidence is a precondition for official trust. A route cannot be official without recorded validation evidence and an explicit promotion event.

## 3. What Validation Is Not

- Validation is not feedback. Feedback recorded in the intent trace store is bounded evidence per `04-intent-trace-store.md` Section 4; feedback is not validation evidence unless Codex later defines an explicit conversion rule.
- Validation is not reviewer confidence. A reviewer's intuition that a candidate "looks good" is not validation evidence.
- Validation is not user preference. User preferences recorded against a route, an intent, or a candidate are not validation evidence.
- Validation is not high rank. A high RouteRank score is not validation evidence; ranking is a relevance and trust ordering, not an evidence-producing process.
- Validation is not a count of successful execution traces. Successful executions of an official route are recorded by the trace store but do not retroactively constitute validation evidence for the route or for any related candidate. No accumulation, sequence, or correlation of successful traces produces validation evidence by itself.
- Validation is not a citation to internet or public sources. Internet or public source references contribute upstream material only after qualification and normalization; their presence in a candidate's provenance is not validation evidence by itself.
- Validation does not make raw prompts or raw internet content official routes. Validation has no subject on raw artifacts; validation applies to route candidates only.

## 4. Validation Evidence Boundary

- A validation evidence record is the artifact produced by validation activity against a specific route candidate.
- Each validation evidence record carries, at boundary level, a reference to the candidate it validates, a reference to the validation activity that produced it, and a reference to the outcome.
- The substantive contents of a validation evidence record - what activity is admissible, what outcome shape is sufficient, what coverage minimum applies, what expiration or freshness rules apply - are owned by Codex and tracked as open questions in `00-open-questions.md`.
- Validation evidence is required for the candidate-to-official transition. Promotion without recorded validation evidence is forbidden; no path bypasses this requirement.
- Absence of validation evidence is recorded explicitly. The registry does not silently treat absence as presence.

## 5. Feedback Boundary

- Feedback is recorded by the intent trace store as bounded evidence per `04-intent-trace-store.md` Section 4.
- Feedback is one input that may inform Codex-owned decisions, including the decision to initiate a validation activity or to record a demotion event. Feedback is not the event itself.
- Feedback does not promote a candidate. Feedback does not change a route's lifecycle state. Feedback does not bypass the policy and risk gate. Feedback does not override validation evidence.
- A feedback-to-evidence conversion rule, if Codex ever defines one, must be explicit, recorded, and reviewable. In the absence of such a rule, feedback remains bounded evidence only and does not enter the validation evidence record.

## 6. Promotion Boundary

- Promotion of a candidate to official requires recorded validation evidence and an explicit promotion event.
- The promotion event records the actor authorized to perform the promotion, the candidate being promoted, the validation evidence reference, and the resulting official route identity and version.
- There is no auto-promotion. No accumulation of usage, popularity, similarity, recency, preference, rank persistence, or successful traces promotes a candidate.
- Promotion applies to route candidates only. A raw prompt, raw document, raw internet content, or raw tool, skill, or agent description is not a candidate and is not the subject of a promotion event.
- The actor authorized to record the promotion event is owned by Codex.

## 7. Demotion / Revocation / Retirement Boundary

- An official route can lose trust. Demotion, revocation, and retirement are real registry states, not afterthoughts.
- A demotion, revocation, or retirement event is explicit. It records the reason, the supporting evidence (where applicable), and the authority that recorded the event.
- A demoted, revoked, or retired route does not silently become official again. Any re-entry into the official set, if Codex later defines a re-entry path, requires that explicit Codex-defined path, a recorded event, validation evidence that satisfies the Codex-owned sufficiency bar, and an explicit promotion event. This boundary does not specify the form of re-entry (whether by new identity, new version, or another Codex-defined mechanism).
- An emergency revocation path - a fast path for severe safety or policy concerns - may exist. If it does, its substantive contract is owned by Codex and must preserve recorded reason, recorded authority, and audit trail. An emergency path does not waive the requirement for an explicit event.
- The substantive distinction between demoted, revoked, and retired is owned by Codex (OQ-023). The authority for each event is owned by Codex.

## 8. Evidence Sufficiency Open Questions

The following items are unresolved and are tracked in `00-open-questions.md`. They are not authored under WO-9.

- What constitutes sufficient validation evidence to promote a candidate to official? (Existing OQ-005; this document references the question but does not duplicate it.)
- What validation reviewer authority is required to record a promotion event, and what authority is required to record a demotion, revocation, or retirement event?
- What expiration or freshness rules apply to validation evidence?
- What minimum validation test coverage is required for a candidate before promotion?
- Under what conditions, if any, can feedback be converted to validation evidence, and how is the conversion recorded?
- What revocation authority and emergency revocation path apply, and how are they distinguished from ordinary demotion?
- Under what conditions is revalidation triggered on an official route (time-based, signal-based, policy-driven), and what is the revalidation outcome boundary?

The presence of these open questions is not a license to assume. Promotion remains gated by recorded validation evidence that clears Codex's substantive sufficiency bar.

## 9. Explicit Anti-Patterns

The following framings are explicitly rejected. Any design or proposal that exhibits them must be rejected at review.

- "Feedback is validation evidence." Feedback is bounded evidence at most; conversion to validation evidence requires an explicit Codex-defined rule that does not currently exist.
- "Reviewer confidence is validation evidence." Reviewer intuition is not a recorded artifact and is not admissible as evidence.
- "User preference is validation evidence." Preference signals are bounded input only.
- "High rank is validation evidence." RouteRank produces relevance and trust ordering; it does not produce evidence.
- "Successful execution traces are automatic validation evidence." Successful traces are operational signals; they do not retroactively constitute validation.
- "Internet or public source citations are validation evidence." Internet content can contribute upstream material only after qualification and normalization; its presence in provenance is not evidence.
- "Validation can be applied to raw prompts." Validation applies to route candidates only; raw prompts are not candidates.
- "Validation can be applied to raw internet content." Same rule as for raw prompts.
- "Demotion is a maintenance task, not a real registry state." Demotion is a real lifecycle state with an explicit, recorded event.
- "A demoted, revoked, or retired route can return to official without an explicit Codex-defined re-entry path." Re-entry, if Codex later defines it, requires the explicit path, a recorded event, validation evidence that satisfies the Codex-owned sufficiency bar, and an explicit promotion event. The form of re-entry is not specified here.

## 10. Out Of Scope

This document is documentation-level only. It does not:

- Define schemas, APIs, or data models for validation evidence records, feedback records, promotion events, or demotion, revocation, or retirement events.
- Define database tables, storage layouts, or retention engines.
- Define validation test framework implementation.
- Define scoring procedures, statistical thresholds, or coverage metrics.
- Define a UI or any chat surface.
- Define ranking formulas.
- Define runtime compile design.
- Define crawler implementation.
- Define a Route Card or Source Card template.

All such work requires a future Codex-approved Work Order.
