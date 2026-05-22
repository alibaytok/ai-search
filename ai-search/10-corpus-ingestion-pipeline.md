# ai-search - Corpus Ingestion Pipeline

Document type: Phase 2 anchor / Corpus ingestion boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-10

---

## 1. Purpose

The corpus ingestion pipeline defines the boundary order through which material enters the corpus, from source discovery to indexed candidate. This document names the stages, asserts their order as invariant, and rejects the bypass framings that allow crawlers, raw documents, or public/internet content to short-circuit the gates. It does not author crawler implementation, extractor logic, normalization procedures, candidate route building algorithms, indexing internals, or any schema. Substantive contracts for each stage are owned by Codex.

The ingestion pipeline anchors the corpus boundary: qualified, normalized material is the only basis from which candidate routes may be built, and routes (not raw artifacts) are the only objects the route registry accepts.

## 2. Ingestion Stage Order

The following stage order is invariant. No stage may be skipped, reordered, or made implicit.

1. Source discovery.
2. Source qualification.
3. Extraction.
4. Normalization.
5. Candidate route building.
6. Indexing.

Downstream of indexing, ranking (`05-ranking-model.md`), the policy and risk gate, validation (`08-validation-and-feedback.md`), and runtime compile operate as defined in their respective phase anchors. They are not part of ingestion.

Ordering constraints:

- Extraction cannot occur before qualification.
- Normalization cannot occur before extraction.
- Candidate route building cannot occur before normalization.
- Indexing operates on normalized material; raw material is not indexed as a route.
- Indexing preserves the candidate vs. official distinction.

## 3. Source Discovery Boundary

- Source discovery is the identification of potential sources. Discovery alone does not admit material to the corpus.
- Discovery does not extract content. It produces a discovery event referencing the source.
- Crawler activity, where it exists, operates within the source discovery boundary. Crawler output is a discovery signal; it is not corpus material and it is not a route.
- The crawler does not decide qualification. Qualification is recorded against the source by the source quality graph (`09-source-quality-graph.md`) per Codex-owned criteria.
- Crawler admission boundaries (what the crawler is permitted to attempt to fetch, and from where) are owned by Codex and tracked as an open question.

## 4. Source Qualification Boundary

- Source qualification is a recorded decision against the source, made before extraction.
- Qualification is consulted from the source quality graph (`09-source-quality-graph.md`).
- Unqualified sources cannot proceed to extraction. The pipeline rejects extraction attempts against unqualified sources.
- Qualification criteria, the actor authorized to record qualification, and the form of the qualification record are owned by Codex and tracked as open questions in `00-open-questions.md`.

## 5. Extraction Boundary

- Extraction operates only on qualified sources.
- Extraction produces source material that is recorded with provenance pointers to the originating source and to the discovery and qualification events.
- Extracted source material is not a route in any state.
- Extracted material is not automatically eligible for indexing. It must pass normalization first.
- Extraction can fail. Failed extraction is recorded with an explicit failure event; failure does not silently retry or silently succeed.

## 6. Normalization Boundary

- Normalization operates on extracted source material.
- Normalization produces normalized material recorded with provenance pointers to the extraction event.
- Normalized material is not a route. Normalization is a precondition for indexing and candidate route building; it is not a trust event.
- Normalization can fail. Failed normalization is recorded with an explicit failure event.
- The substantive normalization contract (what shape normalized material takes, what is preserved, what is dropped) is owned by Codex and remains an open question (OQ-004).

## 7. Candidate Route Building Boundary

- Candidate route building operates only on normalized material.
- Candidates are produced by the candidate route builder (`11-candidate-route-builder.md`) under the rules of the index miss policy (`06-index-miss-policy.md`).
- Candidate building does not produce official routes. It does not promote.
- A candidate built from public or internet material remains a candidate. Origin does not raise the candidate toward official by ingestion.
- Candidate building can reject inputs. A rejected candidate-building attempt is recorded with an explicit rejection event.

## 8. Indexing Boundary

- Indexing operates on normalized material and on candidate routes. Indexing does not admit raw material; raw source material is not indexed as a route.
- Indexing preserves the candidate vs. official distinction. Indexed candidates are not equivalent to indexed officials; the distinction is preserved in every reference to indexed material.
- Whether candidates are surfaced from the index and under what visibility rules distinct from official routes is owned by Codex (OQ-016).
- Indexing does not promote, validate, or rank. It makes admissible material searchable.

## 9. Public / Internet Ingestion Boundary

- Public and internet content enters discovery the same way any other source enters discovery: as a discovery event referencing a potential source. Public/internet origin is recorded as a property of the source.
- Public and internet content cannot bypass qualification. Public popularity, citation count, SEO rank, authoritative appearance, recency, or user preference do not qualify the source.
- Public and internet content cannot bypass normalization. Raw internet content is not admissible to indexing or candidate building.
- Public and internet content cannot bypass validation. A candidate built from public or internet material requires the same validation evidence and explicit promotion event as any other candidate before it can be official.
- Public and internet content cannot bypass the policy and risk gate. The gate applies downstream regardless of source origin.
- Public and internet content remains candidate-only at the route level. The pipeline does not change that boundary.

## 10. Failure / Rejection States

- Failed qualification. A source that did not pass qualification is recorded with an explicit failure event. Failed qualification does not silently promote to qualified later; re-evaluation, if Codex allows it, requires an explicit re-evaluation event.
- Failed extraction. An extraction attempt that did not complete is recorded with an explicit failure event. Failure does not silently retry or silently succeed.
- Failed normalization. A normalization attempt that did not produce admissible material is recorded with an explicit failure event.
- Rejected candidate. A candidate-building attempt that did not produce an admissible candidate is recorded with an explicit rejection event.
- Failure and rejection states are explicit. Absence of a recorded failure or rejection is not implicit success.
- Retention of failed and rejected states is owned by Codex and tracked as an open question.

## 11. Explicit Anti-Patterns

The following framings are explicitly rejected. Any design or proposal that exhibits them must be rejected at review.

- "The crawler indexes everything." Crawler output is a discovery signal at most; qualification, extraction, and normalization gates apply.
- "Raw documents are routes." A document is not a route. A document is at most source material after qualification.
- "Raw prompts are routes." A raw prompt is not a route; it may serve as upstream source material only after qualification.
- "Tool descriptions, skill descriptions, or agent descriptions are routes." None of these are routes in any state.
- "Public popularity equals qualification." Popularity is not qualification.
- "Normalization is optional if the source is already well-structured." Normalization is a precondition for indexing; structure of the source does not waive it.
- "A failed stage can be silently retried." Re-evaluation, retry, or recovery requires an explicit event.
- "Indexing can admit raw material as a route." Raw material is not a route in any state.
- "Public/internet content can bypass qualification, normalization, validation, promotion, or the policy and risk gate." Each gate applies independently; bypass at any stage is forbidden.

## 12. Out Of Scope

This document is documentation-level only. It does not:

- Define crawler implementation, fetcher logic, or crawler selection algorithms.
- Define extractor implementation or extraction parsers.
- Define normalization procedures, transforms, or canonical forms.
- Define candidate route building algorithms or scoring.
- Define indexing data structures, retrieval algorithms, or storage layout.
- Define schemas, fields, types, or data models.
- Define APIs.
- Define a UI or any chat surface.
- Define ranking formulas.
- Define runtime compile design.
- Define validation framework implementation.
- Define a Source Card or Route Card template.

All such work requires a future Codex-approved Work Order.
