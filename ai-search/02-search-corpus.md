# ai-search - Search Corpus Boundaries

Document type: Phase 2 anchor / Corpus boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (cross-references to source quality graph and corpus ingestion pipeline added under WO-10)
Work Order: WO-2 (initial draft, approved via WO-2R), WO-10 (current submission)

---

## 1. Purpose

This document defines the search corpus at the boundary level. It names the distinct corpora ai-search reasons over, the lifecycle stages between them, and the gates that separate them. It does not author implementation, schemas, APIs, crawler logic, ranking formulas, or runtime compile design. Substantive contracts for each corpus and each lifecycle stage are owned by Codex and remain deferred to future Work Orders.

## 2. Corpus Boundary Definitions

ai-search distinguishes the following corpora. These are conceptual boundaries. Their physical representation is not authored here.

- Official route corpus. Routes that have cleared validation and been explicitly promoted. The only routes ai-search trusts as executable. Membership requires recorded validation evidence and an explicit promotion event.
- Candidate route corpus. Provisional routes that have been constructed from qualified, normalized source material but have not cleared validation and have not been promoted. Candidates are never executable on the official path. Public and internet material can produce only candidates.
- Source material. Artifacts that have been admitted to the corpus through source qualification and may be subject to extraction and normalization. Source material is not a route. Source material is not executable.
- Public/internet source material. Source material whose origin is public or internet. Subject to the same qualification, extraction, and normalization gates as any other source, and explicitly restricted to producing candidate material only.
- Validation evidence. The recorded basis on which a candidate route may be promoted to official. The form of evidence, sufficiency bar, storage, and retention of validation evidence are owned by Codex and remain open questions. This corpus is referenced here only as a boundary.

The boundaries above are walls, not labels. Crossing a boundary requires an explicit gate. Sections 3 through 6 name those gates at the documentation level.

## 3. Corpus Lifecycle (Boundary Level)

The following stages are listed in dependency order. Each stage is a boundary. Substantive content for each stage is owned by Codex.

1. Source discovery. Identification of potential source material. Discovery alone does not admit material to the corpus.
2. Source qualification. An explicit decision about whether a source may contribute material. Qualification is a precondition for extraction.
3. Extraction. Drawing content from a qualified source. Extraction may not operate on unqualified sources.
4. Normalization. Transforming extracted content into a form admissible for indexing. Normalization is a precondition for indexing.
5. Candidate route building. Constructing provisional routes from normalized material. Candidate building does not produce official routes.
6. Indexing. Making material searchable. Indexing operates on normalized material. Raw source material is not indexed.
7. Ranking (boundary reference). Ordering of search results. The ranking model is owned by Codex; this document refers to ranking only as a boundary.
8. Policy and risk gate (boundary reference). Checks that must precede any runtime compile. The policy and risk model is owned by Codex; this document refers to it only as a boundary.
9. Validation and promotion (boundary reference). The procedure by which a candidate may become official. Validation criteria, the evidence bar, and the promotion procedure are owned by Codex; this document refers to them only as a boundary.

Stage ordering is itself an invariant. No stage may be skipped, reordered, or made implicit.

Cross-reference: `10-corpus-ingestion-pipeline.md` defines the ingestion stage order and the failure/rejection states at boundary level.

## 4. Source Qualification Requirement

- Source qualification precedes extraction.
- Source authority and trust must be recorded against the source itself, not inferred from a downstream artifact.
- Unqualified sources cannot contribute material to the official route corpus.
- Qualification is a gate, not a tag. Recording qualification metadata does not by itself satisfy the gate; the gate is satisfied only by an explicit qualification decision that is recorded against the source.
- The specific qualification criteria, the authority that makes the decision, and the form of the trust record are owned by Codex and remain open questions.

Cross-reference: `09-source-quality-graph.md` defines the source quality and source trust boundary at documentation level, including the public/internet source boundary and the relationship between source trust and route trust.

## 5. Normalization Requirement

- Normalization precedes indexing.
- Raw source material is not a route. No degree of structural similarity to a route makes raw source material a route.
- Normalized material is not automatically executable. Normalization is a precondition for indexing and candidate route building; it is not a trust event.
- The specific normalization contract (what shape normalized material takes, what is preserved, what is dropped) is owned by Codex and remains an open question.

## 6. Candidate Boundary

- Candidate routes are provisional.
- Candidate routes require validation evidence and an explicit promotion event before they may be considered official.
- Public and internet material can produce only candidate routes. Public and internet material cannot directly enter the official route corpus.
- Candidate visibility within the search subsystem and within the end-user surface is owned by Codex and remains an open question; this document only asserts that any visibility rules must preserve the official vs. candidate distinction.
- A candidate that is never promoted remains a candidate. It does not decay into an official route through usage, time, popularity, or recurrence.

## 7. Explicit Anti-Patterns

The following framings are explicitly rejected. Any design or proposal that exhibits them must be rejected at review.

- "The crawler indexes everything." Source qualification is a hard gate; indexing without qualification is forbidden.
- "Raw documents are routes." A document, however well-structured, is not a route. Routes are produced from normalized material through candidate route building and become official only with validation evidence and explicit promotion.
- "A prompt is a route." A prompt is not a route. A raw prompt does not become an official route through any path.
- "Semantic similarity alone decides execution." Similarity is one signal to ranking; it is not a gate. Execution requires an official, validated route that has passed the policy and risk gate.
- "Public source popularity implies trust." Popularity of a source does not qualify the source. Source qualification is an explicit decision recorded against the source.
- "User preference overrides validation." User preference is an input to search behavior; it does not override validation evidence or promotion state.

## 8. Scope Of This Document

This document is documentation-level only. It does not:

- Define schemas, APIs, or data models.
- Define a UI or chat surface.
- Define crawler implementation.
- Define ranking formulas.
- Define runtime compile design.
- Define route registry details beyond boundary references.
- Define validation framework details beyond boundary references.
- Define evidence ledger details beyond boundary references.
- Define policy and risk gate details beyond boundary references.

All such work requires a future Codex-approved Work Order.
