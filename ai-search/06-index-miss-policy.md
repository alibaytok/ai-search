# ai-search - Index Miss Policy

Document type: Phase 4 anchor / Search miss policy
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-3

---

## 1. Purpose

This document defines, at the documentation level, what ai-search does when search does not return an acceptable validated route. It locks search-first and existing-validated-route-first behavior, requires expanded search before any candidate creation, names the miss categories the system distinguishes, states the candidate creation trigger rules, and explicitly rejects fallbacks that would collapse the architecture. It does not define ranking formulas, scoring functions, retrieval algorithms, or runtime behavior. Substantive content of those subsystems is owned by Codex.

## 2. Required Search Order

The following order is invariant. No step may be skipped, reordered, or made implicit.

1. Search the existing official / validated route corpus.
2. If no acceptable validated route is identified, perform expanded search. The definition and bounds of "expanded search" are owned by Codex and remain an open question. Expanded search does not become generic RAG; that bound is itself an invariant.
3. If expanded search does not yield an acceptable validated route, classify the miss according to the taxonomy in Section 3.
4. Only after the miss is classified, and only when the rules in Section 4 are satisfied, may the candidate route builder be invoked.

A first search returning no acceptable validated route is not a miss for the purposes of candidate creation. Only an expanded search miss may trigger candidate creation.

## 3. Miss Taxonomy (Boundary Level)

The system distinguishes at least the following miss categories. The category set may be extended by Codex; it must not be collapsed.

- No route found. Neither the existing validated corpus nor expanded search returned an acceptable route.
- Route found but below confidence threshold. A route was returned but did not clear the confidence bar. The confidence bar's definition is owned by Codex and is tracked as an open question.
- Route found but policy/risk blocked. A route was acceptable on relevance grounds but was blocked by the policy and risk gate.
- Route found but stale or revoked. A route was returned but is in a state (demoted, revoked, retired, or stale) that disqualifies it from being served as official.
- Source/corpus coverage gap. The intent falls outside the qualified source coverage. No qualified material exists from which to build.

Each miss event is recorded with its category. Specific trace fields are owned by Codex; this document only asserts that the category and the trigger context must be recorded.

## 4. Candidate Creation Trigger Rules

- Candidate creation is allowed only after an expanded search miss has been classified.
- Candidate creation is allowed only for miss categories that are admissible under Codex-owned rules. The admissible set is not authored here.
- A first-search miss alone does not trigger candidate creation.
- A policy/risk-blocked miss does not bypass the policy and risk gate by becoming a candidate. The gate continues to apply downstream.
- A stale-or-revoked miss does not silently revive the prior route. Any new candidate is a new candidate, with its own provenance and its own validation requirement.
- A coverage-gap miss does not authorize unqualified source admission. Source qualification remains a precondition; the coverage gap is a signal to expand qualified coverage, not to bypass qualification.

## 5. Rejected Fallbacks

The following fallbacks are explicitly rejected. They must not be introduced under any condition.

- First-miss candidate generation. Generating a candidate on the first search miss, before expanded search, is forbidden.
- Generic RAG fallback. Returning a synthesized answer assembled from arbitrary retrieved documents is forbidden. ai-search is not generic RAG.
- Direct internet answer fallback. Returning an answer drawn directly from internet content is forbidden. Internet content can only contribute candidate material, never a served answer.
- Semantic-similarity-only execution. Executing a route purely because it is similar to the intent is forbidden. Similarity is one signal to ranking; it is not a gate.
- User-preference override. Letting a user preference promote, validate, gate-bypass, or short-circuit a route is forbidden.

## 6. Trace And Evidence Requirements (Boundary Level)

- Every miss event is traced.
- A miss trace records, at minimum, the intent context, the search stages traversed, the miss category, and the routing decision (no action, candidate created, gate blocked, and similar).
- Trace records are required so that downstream validation, policy and risk, and audit can reason about the miss history of an intent or a candidate.
- The trace schema, storage, and retention are owned by Codex and remain open questions.

## 7. Scope Of This Document

This document is documentation-level only. It does not:

- Define ranking formulas, scoring functions, or retrieval algorithms.
- Define runtime behavior, the runtime compile artifact, or execution semantics.
- Define schemas, APIs, or storage.
- Define a UI or any chat surface.
- Define crawler implementation.
- Define the validation framework's implementation.
- Define the policy and risk gate's implementation.

All such work requires a future Codex-approved Work Order.
