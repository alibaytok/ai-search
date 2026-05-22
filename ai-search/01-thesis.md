# ai-search - Product Thesis

Document type: Phase 1 anchor / Product thesis
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-2

---

## 1. Product Definition

ai-search is an Intent-to-Route Search Engine.

It connects human intent to the best validated execution route inside an AI work corpus.

The product is the route.

Search returns a route, not a prompt, a skill, an agent, a document, a tool, a web page, or a generic synthesized answer. A route is the executable unit that ai-search trusts. Everything upstream of a route is either source material, candidate material, or supporting evidence; it is not the product.

## 2. What ai-search Is Not

ai-search is explicitly NOT:

- A prompt library. Prompts are not the product. A raw prompt is not a route.
- A skill search engine. Skills are an implementation concept, not a user-facing artifact.
- An agent selector or agent router. Agents are not the product surface.
- A chatbot. A conversation surface is not the product, and chat does not define what a route is.
- Generic RAG. ai-search does not retrieve arbitrary documents and synthesize answers from them.
- A crawler-first corpus product. The crawler does not define what a route is. The crawler can only produce candidate material.
- A UI-first product. The user interface does not dictate the route model, the route lifecycle, ranking, or validation.

These are not stylistic distinctions. Each rejected framing, if adopted, collapses one or more invariants enumerated in `00-phase-map.md`.

## 3. Search-First Thesis

- Search comes first. Execution does not precede search.
- ai-search searches existing validated routes first.
- An existing validated route, when it matches the intent, is retrieved before any candidate is created.
- Candidate creation is allowed only after an expanded search returns no acceptable validated route.
- The definition and bounds of "expanded search" are owned by Codex and remain an open question. They are not authored under WO-2.

## 4. Route Trust Thesis

- An official route is a route that has cleared validation and been explicitly promoted.
- A candidate route is a provisional route that has not cleared validation and has not been promoted.
- Candidate routes are not official, regardless of popularity, usage, ranking, semantic similarity to other routes, or origin.
- Promotion of a candidate to official status is explicit and evidence-backed.
- There is no auto-promotion path. Usage, popularity, click-through, semantic similarity, recency, and user preference do not promote a candidate.
- Demotion and revocation of official routes are real states. Their procedural definition is owned by Codex and is tracked as an open question.

## 5. Source Thesis

- Public and internet sources may contribute candidate material only.
- Public and internet sources cannot directly contribute official routes.
- Raw internet content is not executable. It cannot be served as an answer and it cannot be compiled into a route at runtime.
- Raw prompts are not routes. Routes are the product object; prompts are not. A prompt is at most source material or candidate material. Promotion applies to route candidates, not to raw prompts. A raw prompt does not become an official route through any path.
- Source authority and trust are recorded against the source itself, not inferred from any downstream artifact. The specific form of that recording is owned by Codex and is tracked as an open question.

## 6. End-User Thesis

- End users do not see prompt, skill, or agent concepts.
- End users express intent.
- End users receive route-backed outcomes.
- The vocabulary and presentation visible to the end user are owned by Codex under the surface contract phase and are not authored under WO-2.

## 7. Invariants Reaffirmed

The thesis above is consistent with, and bounded by, the seventeen invariants enumerated in `00-phase-map.md`. Nothing in this document overrides those invariants. Where this document is silent, the invariants govern. Where this document and the invariants appear to conflict, the invariants govern and the apparent conflict must be raised to Codex.

## 8. Scope Of This Document

This document is documentation-level only. It does not:

- Define schemas, APIs, or data models.
- Define a UI or chat interface.
- Define crawler implementation.
- Define ranking formulas.
- Define runtime compile design.
- Define route registry details beyond boundary references.
- Define validation framework details beyond boundary references.

All such work requires a future Codex-approved Work Order.
