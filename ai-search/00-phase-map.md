# ai-search - Phase Map

Document type: Baseline / Phase Map
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft baseline - pending Codex review (revised under WO-1R)
Work Order: WO-1 (original submission), WO-1R (rework submission)

---

## Product definition (locked)

ai-search is an Intent-to-Route Search Engine.
It connects human intent to the best validated execution route inside an AI work corpus.
The product is the route, not a prompt, skill, agent, chat UI, or generic RAG system.

---

## Invariants (locked, must hold across all phases)

1. Search first.
2. Existing validated route first.
3. Candidate creation only after expanded search miss.
4. Public/internet content can only create candidate routes.
5. Official routes require validation evidence and promotion.
6. No auto-promotion.
7. No raw prompt becomes an official route.
8. No raw internet content becomes executable.
9. Source qualification before extraction.
10. Normalization before indexing.
11. Policy/risk gate before runtime compile.
12. Validation evidence before trust.
13. End user never sees prompt, skill, or agent concepts.
14. UI does not drive architecture.
15. Claude does not expand scope without Codex approval.
16. Claude does not create implementation code unless explicitly approved by Codex.
17. Claude does not decide architecture direction.

---

## Implementation status (global)

Implementation is NOT approved yet.
No code, schema, API, crawler logic, ranking formula, runtime compile design, or UI is in scope at this point.
Only the four baseline documentation files in WO-1 / WO-1R are authorized.

---

## Phase list

Each phase below provides all required fields. For phases beyond Phase 0, substantive content is owned by Codex and is deferred to a future Codex-approved Work Order. The entries below carry boundary-level placeholders only: they identify the phase, name its boundary purpose, and explicitly mark substance as not yet authored.

---

### Phase 0 - Baseline documentation

- Goal: Establish controller-grade documentation scaffolding for the project before any architectural or implementation work.
- Inputs: Codex-approved Work Order 1; project definition; the seventeen invariants listed above.
- Outputs:
  - ai-search/00-phase-map.md
  - ai-search/00-controller-checklist.md
  - ai-search/00-open-questions.md
  - ai-search/00-claude-task-ledger.md
- Acceptance criteria:
  - All four files exist.
  - All four files conform to Codex-approved expectations.
  - No implementation content present.
  - Invariants restated verbatim where required.
- Rejection criteria:
  - Any file outside the approved list is created or modified.
  - Any implementation, schema, API, crawler, ranking, runtime, or UI detail is introduced.
  - Scope is expanded beyond Work Order 1 / WO-1R.
  - Open questions are silently resolved by Claude.
  - Claude decides architecture direction in lieu of Codex.
- Files to produce/update: the four files listed under Outputs.
- Current status: WO-1 submitted and reviewed; rework required; WO-1R in review (this submission).
- Review gate to next phase: Codex must explicitly approve Phase 0 before Phase 1 begins.

---

### Phase 1 - Architecture contract

- Goal: To be specified by Codex. Boundary purpose: define the authoritative architectural contract (route as data object, route lifecycle, subsystem boundaries) without proposing implementation. Substantive content is owned by Codex; not authored under WO-1 or WO-1R.
- Inputs: Approved Phase 0 baseline; Codex direction. To be specified by Codex in a future Work Order.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex in a future Work Order. No implementation outputs.
- Acceptance criteria: To be specified by Codex. Boundary: must preserve all invariants; must lock the definition of "route" and the route lifecycle states before any downstream phase begins.
- Rejection criteria: To be specified by Codex. Boundary: any framing drift toward prompt library, skill search, agent selector, generic RAG, UI-first, or crawler-first is automatic rejection; any architecture decision authored by Claude rather than Codex is automatic rejection.
- Files to produce/update: To be specified by Codex in a future Work Order. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 2.

---

### Phase 2 - Corpus contract: sources, qualification, normalization

- Goal: To be specified by Codex. Boundary purpose: define what sources are admissible, how source qualification gates extraction, and what normalization must occur before indexing. Substantive content owned by Codex; not authored under WO-1 or WO-1R.
- Inputs: Approved Phase 1 architecture contract; Codex direction. To be specified by Codex.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex. No implementation outputs.
- Acceptance criteria: To be specified by Codex. Boundary: source qualification must precede extraction; normalization must precede indexing; both are invariant.
- Rejection criteria: To be specified by Codex. Boundary: any path that indexes unqualified or non-normalized content is automatic rejection; treating the crawler as the definition of a route is automatic rejection.
- Files to produce/update: To be specified by Codex. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 3.

---

### Phase 3 - Route model: candidate vs. official, validation, promotion

- Goal: To be specified by Codex. Boundary purpose: define the route state machine (candidate, validated, official, demoted/revoked), the validation evidence bar, and the explicit, non-automatic promotion procedure. Substantive content owned by Codex.
- Inputs: Approved Phase 1 and Phase 2 contracts; Codex direction. To be specified by Codex.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex. No implementation outputs.
- Acceptance criteria: To be specified by Codex. Boundary: no auto-promotion path; validation evidence required for promotion; demotion/revocation is a real state, not only promotion.
- Rejection criteria: To be specified by Codex. Boundary: any usage-based, popularity-based, or implicit promotion mechanism is automatic rejection; any path that lets a raw prompt or raw internet content become an official route is automatic rejection.
- Files to produce/update: To be specified by Codex. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 4.

---

### Phase 4 - Intent-to-route search behavior contract

- Goal: To be specified by Codex. Boundary purpose: define how human intent is matched to existing validated routes, what "expanded search" means and how it is bounded, and the behavior on search miss. Substantive content owned by Codex.
- Inputs: Approved Phase 1, Phase 2, and Phase 3 contracts; Codex direction. To be specified by Codex.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex. No implementation outputs.
- Acceptance criteria: To be specified by Codex. Boundary: search first; existing validated route first; candidate creation only after expanded search miss.
- Rejection criteria: To be specified by Codex. Boundary: any behavior that creates candidates before exhausting expanded search is automatic rejection; any behavior that collapses into generic RAG is automatic rejection.
- Files to produce/update: To be specified by Codex. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 5.

---

### Phase 5 - Policy / risk gate contract

- Goal: To be specified by Codex. Boundary purpose: define the policy and risk checks that must run before any runtime compile, and the failure modes those checks produce. Substantive content owned by Codex.
- Inputs: Approved Phase 1 through Phase 4 contracts; Codex direction. To be specified by Codex.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex. No implementation outputs.
- Acceptance criteria: To be specified by Codex. Boundary: the gate must be substantive (not a rubber stamp); the gate precedes runtime compile.
- Rejection criteria: To be specified by Codex. Boundary: any path that allows runtime compile without passing the gate is automatic rejection; any gate definition that is purely advisory is automatic rejection.
- Files to produce/update: To be specified by Codex. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 6.

---

### Phase 6 - Runtime compile contract

- Goal: To be specified by Codex. Boundary purpose: define what "runtime compile" means in this system and what artifact it produces from a validated official route. The term is reserved; meaning is controller-defined. Substantive content owned by Codex.
- Inputs: Approved Phase 1 through Phase 5 contracts; Codex direction. To be specified by Codex.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex. No implementation outputs.
- Acceptance criteria: To be specified by Codex. Boundary: runtime compile operates only on validated official routes that have passed the policy/risk gate; raw prompt and raw internet content are not admissible payloads.
- Rejection criteria: To be specified by Codex. Boundary: any compile path that reintroduces raw prompt or raw internet content as execution payload is automatic rejection; any path that bypasses the policy/risk gate is automatic rejection.
- Files to produce/update: To be specified by Codex. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 7.

---

### Phase 7 - Evidence and trust ledger contract

- Goal: To be specified by Codex. Boundary purpose: define what evidence is recorded, where it is stored, and the retention and immutability guarantees that anchor trust in promoted routes. Substantive content owned by Codex.
- Inputs: Approved Phase 1 through Phase 6 contracts; Codex direction. To be specified by Codex.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex. No implementation outputs.
- Acceptance criteria: To be specified by Codex. Boundary: validation evidence must precede trust; the ledger must support audit of promotion and demotion events.
- Rejection criteria: To be specified by Codex. Boundary: any design that treats validation as retroactive or implicit is automatic rejection; any ledger design without immutability guarantees on promotion records is automatic rejection.
- Files to produce/update: To be specified by Codex. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 8.

---

### Phase 8 - Surface contract (what the end user sees)

- Goal: To be specified by Codex. Boundary purpose: define the user-facing surface vocabulary and presentation so the end user encounters routes and intents only, never prompt, skill, or agent concepts. Substantive content owned by Codex.
- Inputs: Approved Phase 1 through Phase 7 contracts; Codex direction. To be specified by Codex.
- Outputs: Documentation artifacts only at this stage. Specific files to be specified by Codex. No implementation outputs and no UI design under this Phase unless Codex explicitly authorizes it.
- Acceptance criteria: To be specified by Codex. Boundary: the surface contract must hide prompt, skill, and agent concepts from the end user; UI does not drive architecture.
- Rejection criteria: To be specified by Codex. Boundary: any surface that exposes prompt, skill, or agent vocabulary to end users is automatic rejection; any surface design that retroactively modifies the route model is automatic rejection.
- Files to produce/update: To be specified by Codex. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting a Codex Work Order.
- Review gate to next phase: Codex approval required before Phase 9.

---

### Phase 9 - Implementation authorization

- Goal: To be specified by Codex. Boundary purpose: Codex explicitly authorizes the transition from contract to implementation, scoped per subsystem and per Work Order. Substantive content owned by Codex.
- Inputs: Approved Phase 0 through Phase 8 contracts; Codex direction. To be specified by Codex.
- Outputs: Per-slice implementation authorizations, each as a discrete Codex Work Order. No implementation outputs under WO-1 / WO-1R.
- Acceptance criteria: To be specified by Codex. Boundary: implementation may begin only on a subsystem whose contract is approved, only after Codex issues a Work Order authorizing that specific slice.
- Rejection criteria: To be specified by Codex. Boundary: implementation work on any subsystem without an explicit Codex Work Order is automatic rejection; any cross-subsystem implementation under a single-slice authorization is automatic rejection.
- Files to produce/update: To be specified by Codex per authorized slice. None authorized under WO-1 / WO-1R.
- Current status: Not started. Not authorized. Awaiting completion of contract phases and an explicit Codex Work Order.
- Review gate to next phase: Not applicable; Phase 9 is the gate to implementation, not to a further phase.

---

## Cross-phase review gates

Between every phase:

1. Codex reviews outputs against invariants.
2. Codex reviews against drift patterns (prompt-library, skill-search, agent-selector, generic RAG, UI-first, crawler-first framing).
3. Codex confirms open questions are not silently resolved.
4. Codex confirms that no architecture direction was decided by Claude.
5. Codex approves or rejects with written feedback recorded in 00-claude-task-ledger.md.
6. Phase transitions are explicit; there is no implicit phase advancement.

---

## Explicit note on implementation

Implementation is not approved at this time.
No phase beyond Phase 0 is authored by Claude.
No code, schema, API, crawler logic, ranking formula, runtime compile design, or UI design is produced under WO-1 / WO-1R.
Any such work requires explicit Codex authorization tied to a specific Work Order.
