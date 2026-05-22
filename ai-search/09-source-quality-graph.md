# ai-search - Source Quality Graph

Document type: Phase 2 anchor / Source quality and source trust boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-10

---

## 1. Purpose

The source quality graph records what is known about each source: whether it has been qualified for the corpus, what authority and trust have been recorded against it, what provenance chain led to its qualification, and whether it is a public or internet source. This document defines the source quality graph at the documentation level only. It does not author schemas, fields, types, storage models, APIs, crawler logic, ranking, or any algorithm. Substantive contracts are owned by Codex and remain deferred.

The source quality graph anchors source qualification as a real gate. It does not anchor route trust. Source trust and route trust are distinct.

## 2. What The Source Quality Graph Is

- A record of qualified sources and the authority, trust, freshness signal, and provenance chain recorded against each. The specific form of recording is owned by Codex.
- The artifact consulted by ingestion to confirm that a source has been qualified before extraction.
- The artifact consulted during candidate route derivation to retrieve provenance pointers for normalized material.
- A boundary that distinguishes source-level trust (recorded against the source) from route-level trust (recorded against route candidates and official routes through validation and promotion as defined in `03-route-registry.md` and `08-validation-and-feedback.md`).

## 3. What The Source Quality Graph Is Not

- It is not a crawler. It does not fetch, discover, or admit content. Source discovery is upstream; the graph records the outcome of qualification decisions.
- It is not an extractor. Extraction operates on qualified sources; the graph does not draw content from sources.
- It is not a normalizer. Normalization operates on extracted content; the graph does not transform content.
- It is not a route ranker. RouteRank operates on retrieved route results; the graph does not order routes.
- It is not a route validator. Validation operates on route candidates; the graph does not produce validation evidence.
- It is not a route promoter. Promotion operates on candidates via recorded validation evidence and an explicit promotion event; the graph does not transition route lifecycle state.
- It is not a runtime compiler. Runtime compile is downstream of validated official routes that have passed the policy and risk gate; the graph has no role in execution.
- It is not a popularity scorecard. Source quality is not a function of popularity, citation count, SEO rank, or recency by itself.

## 4. Source Qualification Boundary

- Source qualification is a recorded decision against a specific source, made before any extraction operates on that source.
- Qualification is a gate, not a tag. Recording qualification metadata does not by itself satisfy the gate; an explicit qualification decision must be recorded.
- Unqualified sources cannot contribute material to the corpus. They cannot be extracted, normalized, or used in candidate derivation.
- Qualification criteria, the actor authorized to record a qualification event, and the form of the qualification record are owned by Codex and tracked as open questions in `00-open-questions.md` (OQ-003, OQ-015, OQ-031, and questions added under WO-10).
- Qualification can fail. A source that fails qualification does not silently become qualified later. Re-evaluation, if Codex allows it, requires an explicit re-evaluation event; absence of a recorded re-evaluation is not implicit re-qualification.

## 5. Source Trust Boundary

- Source trust is recorded against the source, not against any route.
- Source trust is one input among many to qualification and to downstream Codex-owned decisions. It is not a substitute for any other boundary.
- Source trust does not promote a candidate. A high-trust source contributing material to a candidate does not promote the candidate.
- Source trust does not make source material executable. Source material is not a route in any state.
- Source trust does not waive the policy and risk gate. Trust at the source level does not exempt downstream routes from the gate.
- Source trust can decay. Freshness, ownership change, authority change, or recorded incidents may erode trust. The substantive decay rules are owned by Codex and tracked as an open question.

## 6. Provenance Boundary

- The graph records the provenance chain that supports each qualification. The provenance chain is a reference, not a narrative.
- Provenance references include, at boundary level, the discovery event, the qualifying authority reference, the trust recording, and any prior qualification or revocation events.
- Provenance pointers from candidate routes resolve back into the graph for the source records that contributed material.
- The substantive granularity, immutability, and storage of provenance references are owned by Codex and tracked in `00-open-questions.md` (in particular OQ-022).

## 7. Public / Internet Source Boundary

- Public and internet sources are not implicitly qualified. Their public status, popularity, citation count, SEO rank, authoritative appearance, recency, or user preference do not constitute qualification.
- A public or internet source may be qualified through the same explicit qualification process applied to any other source. The graph records public/internet origin as a property of the source so downstream stages can apply Codex-owned public/internet rules.
- Public and internet sources can contribute upstream material for candidate derivation only after qualification and normalization.
- Public and internet material remains candidate-only at the route level. The graph does not change that boundary.

## 8. Relationship To Candidate Routes

- The source quality graph is upstream of candidate route building. The graph supplies qualification status and provenance references; it does not build candidates.
- A candidate route's provenance references resolve into the graph for source records.
- A high-trust source does not produce a high-trust candidate. Trust at the source level does not transfer to the candidate. The candidate's trust state is determined by validation evidence and promotion events recorded in the route registry, not by source-level trust.
- A candidate built from public or internet material remains a candidate. Source qualification does not promote.
- Conflicting qualified sources (sources that have been qualified but disagree on content that would inform the same candidate) require an explicit conflict handling boundary owned by Codex and tracked as an open question.

## 9. Explicit Anti-Patterns

The following framings are explicitly rejected. Any design or proposal that exhibits them must be rejected at review.

- "Public popularity equals qualification." Popularity is not qualification.
- "Citation count, SEO rank, or authoritative appearance equals qualification." None of these constitute a recorded qualification event.
- "Recency equals qualification." A recent source is not therefore qualified.
- "User preference for a source equals qualification." Preference signals are bounded; they are not qualification events.
- "A high-trust source produces high-trust routes by inheritance." Source trust does not transfer to route trust.
- "Source quality makes source material executable." Source material is not a route in any state.
- "Crawler output is implicitly qualified." Crawler output is a discovery signal at most, and only an explicit qualification event admits the source.
- "A failed qualification can be retried silently." Re-evaluation, if Codex allows it, requires an explicit event.

## 10. Out Of Scope

This document is documentation-level only. It does not:

- Define schemas, fields, types, or data models.
- Define database tables, storage layout, immutability mechanisms, or retention engines.
- Define crawler implementation, fetcher logic, or selection algorithms.
- Define extraction, normalization, or candidate route building procedures.
- Define ranking formulas.
- Define runtime compile design.
- Define validation framework implementation.
- Define a UI or any chat surface.
- Define a Source Card or Route Card template.

All such work requires a future Codex-approved Work Order.
