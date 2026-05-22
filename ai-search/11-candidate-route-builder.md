# ai-search - Candidate Route Builder

Document type: Phase 3 / Phase 4 anchor / Candidate route builder boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-3

---

## 1. Purpose

The candidate route builder is the only authorized producer of candidate routes. This document defines its boundary: what it is allowed to consume, what it is forbidden to consume, what it produces, the metadata its output must carry, and the rules that govern when it may run. It does not define schemas, algorithms, scoring, or implementation. Substantive contracts are owned by Codex.

The builder produces candidates only. It does not produce official routes. It does not promote, validate, rank, gate, or compile. Each of those is downstream and owned by Codex.

## 2. Allowed Inputs

The builder may consume:

- Normalized material. Material that has passed source qualification and normalization.
- Qualified source references. References to sources that have an explicit qualification record.
- Intent miss context. The recorded miss event that triggered candidate creation, including its miss category and trace, as defined in the index miss policy.
- Provenance references. References to the qualification record, the normalization step, and (where applicable) prior route or routes related to the intent.

## 3. Forbidden Inputs

The builder must not consume:

- Unqualified source material. Source qualification is a precondition; the builder cannot bypass it.
- Raw internet content as an executable payload. Internet content can become candidate material only through qualification and normalization. It is never passed to the builder as an executable.
- Raw prompts as route objects. A raw prompt is not a route. A prompt may appear as source or candidate material but is never treated by the builder as a route object.
- Documents, tools, skills, or agent descriptions presented as routes. None of these are routes. The builder rejects any input framed as "this is a route" outside of the candidate / official lifecycle defined in the route registry.

## 4. Outputs

The builder produces:

- Candidate routes only. Every artifact the builder produces is a candidate.
- No official routes. The builder cannot mark its output as official, validated, or executable on the official path.
- No directly executable official artifact. The builder does not emit a runtime-compiled or runtime-ready artifact. Runtime compile is a downstream phase, owned by Codex, and operates only on validated official routes that have passed the policy and risk gate.

## 5. Required Candidate Metadata (Boundary Level)

Every candidate emitted by the builder must carry, at minimum, the following metadata. The specific schema, storage, and granularity are owned by Codex.

- Provenance. A reference, or set of references, describing the source or sources that contributed material.
- Source qualification reference. A reference to the qualification record for each contributing source.
- Normalization reference. A reference to the normalization step that produced the inputs.
- Miss context reference. A reference to the index miss event that triggered the candidate's creation, including its miss category.
- Validation-required marker. An explicit marker indicating that the candidate has not been validated and is not eligible for execution on the official path.

A candidate that is missing any of these references is not a candidate the builder may emit. The validation-required marker in particular is not optional. It is the explicit signal that the candidate is upstream of validation and promotion.

## 6. No Auto-Promotion

- The builder does not promote. The builder cannot mark its output as official, validated, or executable.
- No usage signal, popularity signal, click-through signal, semantic similarity, recency, or user preference observed on a candidate promotes it.
- Re-use of a candidate, repeated emission of similar candidates, or convergence across candidates does not promote them.
- Promotion is a downstream event. It requires recorded validation evidence and an explicit promotion event, both owned by Codex.

## 7. Validation And Promotion Are Downstream

- Validation is a downstream phase. The builder does not run validation. The builder does not record validation outcomes.
- Promotion is a downstream phase. The builder does not promote.
- Demotion, revocation, and retirement are downstream events recorded by the route registry. The builder does not affect them.
- The substantive contracts for validation, promotion, demotion, revocation, and retirement are owned by Codex and remain open questions.

## 8. Scope Of This Document

This document is documentation-level only. It does not:

- Define schemas, APIs, or data models.
- Define algorithms, scoring, or ranking.
- Define a UI or any chat surface.
- Define crawler implementation.
- Define runtime compile design.
- Define the validation framework's implementation.
- Define the policy and risk gate's implementation.

All such work requires a future Codex-approved Work Order.
