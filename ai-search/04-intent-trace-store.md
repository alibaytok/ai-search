# ai-search - Intent Trace Store

Document type: Phase 4 / Phase 7 anchor / Intent trace store boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-4

---

## 1. Purpose

The intent trace store is the auditable record of what happened when an intent met the search system. It records, at boundary level, the sequence of events from intent capture through outcome, so that downstream validation, policy review, and audit can reconstruct any single interaction without inferring from raw logs.

This document defines the trace store at documentation level only. It names what must be auditable, what references each trace event must carry, and what the trace store explicitly is not. It does not define schemas, storage models, APIs, analytics implementations, retention engines, UI, or any algorithmic behavior. Substantive contracts for those are owned by Codex.

The trace store exists to keep the architecture honest. It is the mechanism by which the invariants - search-first, validated-route-first, candidate-only-after-expanded-search-miss, no auto-promotion, and the candidate vs. official boundary - can be verified after the fact.

## 2. What The Intent Trace Store Is Not

The trace store is explicitly NOT:

- Chat transcript storage. It does not record conversation history. ai-search is not a chatbot, and the trace store does not carry conversation as its product.
- A prompt log. The trace store does not stand in for prompt history. It does not record raw user prompts as routes or as candidates. Where a captured intent contains raw user text, that text is recorded as captured intent only; raw text is not elevated to source material, candidate material, or route status by appearing in a trace record.
- A user preference engine. It does not learn preferences, infer preferences, or apply preferences as authority. User preference, where it appears in the trace, is bounded evidence (Section 4).
- An automatic promotion engine. It does not promote candidates. No accumulation, sequence, or correlation of trace signals promotes a candidate to official.
- An analytics-only event stream. It is not a metrics pipeline. Its product is auditable trace records, not aggregated counts or dashboards. Analytics may consume the trace store, but the trace store is not defined by analytics needs.

## 3. Required Trace Boundaries

Every intent traversal of the search system must be auditable across the following boundaries. Each boundary is a recorded event with references to its upstream and downstream context. The substantive content and schema of each event are owned by Codex.

- User intent capture. The recorded event that the user's intent was captured, with a reference to its canonical form. The canonical form of intent is owned by Codex and remains an open question (OQ-017).
- Initial official route search. The recorded event that the search against the existing validated route corpus ran, with a reference to the input and the result classification.
- Expanded search. The recorded event that expanded search ran, where the initial search did not yield an acceptable validated route. The trace records the result classification.
- Miss classification. The recorded event that the miss was classified, with the miss category per `06-index-miss-policy.md`.
- Candidate creation trigger, if any. The recorded event that candidate creation was triggered under the rules of `06-index-miss-policy.md` and that a candidate route was emitted by the candidate route builder (`11-candidate-route-builder.md`). The trace references the candidate route; the candidate's state remains "candidate."
- Selected route or no-route outcome. The recorded event that a route was selected for execution, with a reference to the selected route, or the recorded event that no route was selected.
- Policy / risk gate result. The recorded event that the policy and risk gate ran on the selected route, with a reference to the gate's evaluation record. Policy/risk gate substantive contracts are owned by Codex.
- Runtime compile boundary reference. The recorded event, at boundary level, that runtime compile was invoked or was not invoked. Runtime compile is a downstream phase whose substantive contract is owned by Codex.
- Validation feedback boundary reference. The recorded event, at boundary level, that validation feedback was attached or was not attached to the interaction. The validation framework's substantive contract is owned by Codex.
- Final outcome signal. The recorded event of the final outcome (route executed, route blocked, no route, error).

Trace boundaries are recorded in order. A boundary that should have been recorded but was not is itself recordable as a defect; absence is never silent.

## 4. Required Trace Principles

The following principles are properties the trace store must preserve. They are invariant.

- Search-first must be auditable. The trace must show that search ran before any candidate creation.
- Existing validated route retrieval must be auditable. The trace must show that the validated route corpus was consulted before expanded search and before candidate creation.
- Expanded search before candidate creation must be auditable. The trace must show that expanded search ran and produced a miss classification before any candidate was created.
- Candidate vs. official distinction must be preserved in every trace record. A trace event that references a candidate route does not mark that candidate as official. A trace event that references an official route does not re-label it as a candidate.
- Public and internet source contribution must remain candidate-only in the trace. The trace must not record any path in which public or internet material directly becomes an official route or is executed as one.
- Trace data cannot auto-promote candidates. No accumulation, sequence, or correlation of trace events promotes a candidate. Promotion remains an explicit, evidence-backed event recorded by the route registry (`03-route-registry.md`).
- User preference is bounded evidence, not trust authority. Where user preference is recorded in the trace, it is one bounded input. It does not override validation evidence, does not promote candidates, does not bypass the policy and risk gate, and does not change the official vs. candidate distinction.

## 5. Required Trace References (Boundary Level)

Each trace event carries, at minimum, the following references where applicable. The specific schema, storage, and granularity of these references are owned by Codex.

- Intent context reference. A reference to the captured intent for this trace.
- Route result reference. A reference to the route the initial or expanded search returned, where applicable.
- Miss event reference. A reference to the miss classification event, where expanded search produced a miss.
- Candidate route reference. A reference to the candidate route produced by the builder, where candidate creation was triggered. The candidate retains its candidate state in the trace; the trace does not elevate it.
- Source / provenance reference. A reference to the source qualification and normalization records that contributed to the route or candidate involved.
- Policy / risk gate reference. A reference to the policy and risk gate evaluation record, where the gate ran.
- Validation evidence reference. A reference to the validation evidence record, where one applied. Where no validation evidence exists, the trace records that fact; absence is not silently treated as presence.
- Feedback / outcome reference. A reference to the recorded outcome and to any user feedback attached to the interaction. Feedback is bounded evidence per Section 4.

A trace event that should carry one of these references but does not is itself recordable as a defect; absence is not silent.

## 6. Privacy And Security Boundary

- The end user must not be exposed to prompt, skill, or agent concepts through the trace store or through any surface that consumes it. The trace store is an internal audit artifact, not a user-facing concept inventory.
- The trace store does not store raw prompts as official routes. Raw prompts that appear in trace records (for example, as captured intent) are recorded as captured intent only; the trace store does not elevate them to source material, candidate material, or route status.
- The trace store does not treat raw internet content as executable evidence. Internet content can only contribute upstream material for candidate derivation after qualification and normalization; the trace store does not invert that boundary by treating internet references as proof of validation or as grounds for execution.
- The specific privacy controls, PII handling, redaction rules, retention windows, and access controls are owned by Codex and remain open questions.

## 7. Scope Of This Document

This document is documentation-level only. It does not:

- Define schemas, APIs, or data models.
- Define database tables, storage layout, or retention engines.
- Define analytics implementation, dashboards, or aggregation pipelines.
- Define a UI or any chat surface.
- Define ranking formulas.
- Define runtime compile design.
- Define the validation framework's implementation.
- Define the policy and risk gate's implementation.
- Define crawler implementation.

All such work requires a future Codex-approved Work Order.
