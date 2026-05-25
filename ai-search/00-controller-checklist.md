# ai-search - Controller Checklist

Document type: Baseline / Controller Checklist
Owner: Codex (controller)
Purpose: Codex uses this checklist on every Claude submission, every phase gate, and every Work Order review to verify compliance before approving advancement.
Status: Draft baseline - approved with Codex direct mutual-alignment hardening
Work Order: WO-1 (original submission), WO-1R (rework submission, approved), WO-6 (controller checklist hardening, rework required), WO-6R (approved with notes), WO-7 (approved), WO-8 (approved), WO-13 (approved), Codex direct update (mutual alignment protocol)

---

## How to use this checklist

- Codex runs every applicable section against every submission.
- Any single failed item blocks approval until resolved.
- Claude does not self-approve. Claude does not silently resolve unknowns. Findings must be recorded in 00-claude-task-ledger.md and 00-open-questions.md.
- "Pass" requires affirmative evidence, not absence of objection.

---

## A. Codex controller review checklist

- [ ] Work Order ID is referenced in the submission.
- [ ] Submission scope matches the Work Order exactly (no expansion, no contraction).
- [ ] Only files in the Work Order's allowed list were created or modified.
- [ ] No file outside the allowed list was created, modified, renamed, or deleted.
- [ ] All four baseline files exist when WO-1 / WO-1R is the active order.
- [ ] An evidence report was produced and matches the required section format.
- [ ] All assumptions made by Claude are explicitly listed.
- [ ] All open questions are recorded (none silently resolved).
- [ ] All risks are recorded.
- [ ] All decisions are recorded with rationale.
- [ ] All rejected assumptions are recorded with rationale.
- [ ] Claude did not claim approval authority.
- [ ] Claude did not advance to the next phase without explicit Codex approval.

## B. Invariant compliance checklist

For each submission, confirm the work does not violate any invariant:

- [ ] Search first is preserved (no route execution proposed before search).
- [ ] Existing validated route first is preserved.
- [ ] Candidate creation only after expanded search miss is preserved.
- [ ] Public/internet content is only ever treated as candidate material (never executable, never official).
- [ ] Official routes require validation evidence and explicit promotion.
- [ ] No auto-promotion path is introduced.
- [ ] No raw prompt is promoted to an official route.
- [ ] No raw internet content is rendered executable.
- [ ] Source qualification precedes extraction.
- [ ] Normalization precedes indexing.
- [ ] Policy/risk gate precedes runtime compile.
- [ ] Validation evidence precedes trust.
- [ ] End user is never exposed to prompt, skill, or agent concepts.
- [ ] UI does not drive architecture; UI is a surface, not a source of truth.
- [ ] Claude did not expand scope beyond the Work Order.
- [ ] Claude did not create implementation code without explicit Codex approval.
- [ ] Claude did not decide architecture direction; all architecture decisions trace to Codex.

## C. Architecture drift checklist

Reject the submission if any of the following framings has crept in:

- [ ] Project is NOT being treated as a prompt library.
- [ ] Project is NOT being treated as skill search.
- [ ] Project is NOT being treated as an agent selector.
- [ ] Project is NOT being treated as generic RAG over arbitrary documents.
- [ ] Project is NOT being framed UI-first (UI dictating model, schema, or ranking).
- [ ] Project is NOT being framed crawler-first (crawler dictating what a route is).
- [ ] Project is NOT being framed as a chat product.
- [ ] Project is NOT being framed as a plugin marketplace.
- [ ] Project IS being framed as an Intent-to-Route Search Engine.
- [ ] The "product is the route" framing is preserved end-to-end.

## D. Scope control checklist

- [ ] No new file types introduced without Codex approval.
- [ ] No new subsystems introduced without Codex approval.
- [ ] No new vocabulary introduced without Codex approval (no rebranding of route/candidate/official/validation).
- [ ] No implementation code present.
- [ ] No schema definitions present.
- [ ] No API definitions present.
- [ ] No crawler logic present.
- [ ] No ranking formula present.
- [ ] No runtime compile design present.
- [ ] No UI proposal present.
- [ ] No "while we're here" cleanup or refactor present.
- [ ] No speculative "future-proofing" abstractions present.
- [ ] No architecture direction authored by Claude rather than Codex.

## E. Promotion and validation checklist

- [ ] Candidate vs. official distinction is preserved in all language.
- [ ] No path is described that turns a candidate into an official route without explicit validation evidence.
- [ ] No promotion path is automatic; every promotion requires a recorded decision and recorded evidence.
- [ ] No path is described that lets unqualified sources contribute to official routes.
- [ ] No path is described that bypasses the policy/risk gate before runtime compile.
- [ ] Validation evidence is described as a precondition of trust, not a consequence of usage.
- [ ] Demotion / revocation is acknowledged as a real state, not just promotion.

## F. Anti-pattern guardrails (explicit rejection triggers)

Reject the submission if it does any of the following:

- [ ] Treats prompts as first-class user-facing artifacts.
- [ ] Treats skills as first-class user-facing artifacts.
- [ ] Treats agents as first-class user-facing artifacts.
- [ ] Proposes shipping internet snippets directly to users as answers.
- [ ] Proposes a single relevance score as the only gate for execution.
- [ ] Proposes letting the UI define what a "route" is.
- [ ] Proposes letting the crawler define what a "route" is.
- [ ] Proposes a chat-first or copilot-first surface.
- [ ] Proposes a marketplace, store, or social layer.
- [ ] Treats validation as optional, retroactive, or implicit.
- [ ] Has Claude authoring architecture direction in lieu of Codex.

## G. Documentation hygiene checklist

- [ ] Each baseline file declares its document type, owner, status, and Work Order.
- [ ] Each tracked item in 00-open-questions.md has ID, status, related phase, and rationale.
- [ ] 00-claude-task-ledger.md reflects every assigned Work Order and revision pass, with accurate status, Codex feedback, allowed files, changed files, and approval/rework result.
- [ ] Status fields are accurate (no "Done" without Codex sign-off).
- [ ] No retroactive edits hide prior assumptions; corrections are appended with rationale.
- [ ] Baseline documents use ASCII text and avoid unnecessary non-ASCII punctuation or arrows.

### G.1 Approval feedback audit hygiene

Added under WO-8 to prevent compressed, inferred, or forward-compatible approval records. These rules apply on every submission and every approval recording event.

- [ ] Codex approval feedback is recorded with its actual substance, not compressed to a single word when a fuller review summary exists.
- [ ] APPROVED WITH NOTES records both the approval and the note that qualifies it.
- [ ] Ledger entries distinguish active record from historical correction context.
- [ ] Correction notes must point to the correcting Work Order without rewriting the meaning of the original review.
- [ ] Claude must not invent forward-compatible audit language such as "may be corrected later" to justify an inaccurate active record.
- [ ] If Codex feedback is ambiguous or too terse to record safely, Claude must stop and ask for clarification rather than infer.
- [ ] Evidence reports must not claim "verbatim" unless the quoted text is actually the review text being preserved.

## H. Final gate

- [ ] Codex has explicitly written "approved" against this submission before any phase advances.
- [ ] If rejected, Codex feedback is captured verbatim in 00-claude-task-ledger.md under the relevant Work Order.

## I. Route object contract and lifecycle enforcement gates

Added under WO-6 to harden the checklist around route-contract substance and lifecycle enforcement.

- [ ] Is the route object contract present and explicit? (A missing or implicit route contract is a structural blocker.)
- [ ] Are the state transition rules explicit for every recorded state (candidate, under validation, official, demoted, revoked, retired)?
- [ ] Is the validation evidence bar defined? Absence of an explicit bar is automatic rejection.
- [ ] Is source qualification enforced as a real gate, not merely recorded as metadata?
- [ ] Are source authority, source trust, freshness, ownership, and provenance chain all tracked against the source itself?
- [ ] Is promotion bound to an explicit, recorded approval event?
- [ ] Is the auto-promotion possibility fully closed across every path (usage, popularity, click-through, similarity, recency, preference, rank persistence)?
- [ ] Is the policy and risk gate taxonomy defined?
- [ ] Does runtime compile re-introduce raw prompt or raw internet content as executable payload? (Reject if yes.)
- [ ] Is the intent trace append-only and auditable?
- [ ] Does the end-user surface leak prompt, skill, or agent concepts? (Reject if yes.)
- [ ] Are operational owners identified for source qualifier, route promoter, route revoker, and policy reviewer roles?
- [ ] Is the need for a golden intent set and a regression test set being tracked?
- [ ] Is RouteRank drifting toward producing trust from semantic similarity, popularity, or user preference? (Reject if yes.)

## J. RouteOps artifact readiness

Added under WO-6 to record that named artifacts are required as gates before specific lifecycle events. This section is documentation-level only: it does not author schemas, templates, formats, or implementations for any of the named artifacts. Substantive contracts for each artifact are owned by Codex and remain open questions.

- [ ] Is a Route Card recorded before any official route exists?
- [ ] Is a Source Card recorded before any extraction from a source?
- [ ] Is a Promotion Record recorded before any candidate-to-official promotion?
- [ ] Is a Policy Decision Record recorded before any runtime compile?
- [ ] Is an Intent Trace recorded for every route search, miss, rank, gate evaluation, and outcome?
- [ ] Is an Evaluation Set recorded before any ranking or runtime claim is accepted?
- [ ] Is a Regression Gate recorded before any change to official route behavior?

## K. Indexing Excellence Gate / No Pretend Completion

Added under WO-13 to prevent premature approval of any indexing/retrieval architecture. These checks apply at review time on every Work Order that touches indexing, retrieval, ranking, or benchmark scope. The gate is evidence-based, not preference-based. "Best not proven" means "not selected."

- [ ] No indexing architecture is being approved unless benchmark evidence demonstrates superiority under ai-search constraints.
- [ ] "Good enough" is being treated as not acceptable for indexing and retrieval.
- [ ] Market defaults are being treated as not evidence.
- [ ] "Vector DB plus reranker" is being treated as not a default answer.
- [ ] "Centralized single-index architecture" is being treated as not a default answer.
- [ ] If no candidate indexing approach has cleared the excellence gate, the review is recording that no selection is made.
- [ ] Contract-safety failures disqualify a configuration regardless of its quality and performance scores.
- [ ] The review is preventing an aggregate benchmark score from selecting a winner by itself.
- [ ] Ablation evidence is required and recorded before any claim that a layer (lexical, dense, hybrid, rerank, graph constraint, late interaction, or other) is necessary or unnecessary.
- [ ] Cost model evidence is required and recorded before any architecture is selected.
- [ ] Update and freshness evidence is required and recorded before any architecture is selected.
- [ ] Rollback and reproducibility evidence are required and recorded before any architecture is selected.
- [ ] Graph-constrained retrieval and multi-stage retrieval alternatives have been evaluated before any selection.
- [ ] Claude is blocked from describing the indexing scope as complete, best, or production-ready without explicit Codex approval based on recorded evidence.

## L. Mutual Alignment Protocol / Shared Scope Verification

Added by Codex direct update to prevent AI-user scope drift, false agreement, and context-loss errors. These checks apply before substantial work, after long-running work, after a halt, after a resume, before handoff, and whenever the user or Claude challenges the current direction.

- [ ] The shared state is explicit before execution: goal, current phase, authorized scope, non-goals, allowed files/actions, forbidden files/actions, accepted assumptions, open questions, risks, definition of done, and next safe step.
- [ ] Claude states its understanding in operational terms before substantial work: what it will do, what it will not do, what would trigger a halt, and what evidence will prove completion.
- [ ] User requests are checked against prior decisions, open questions, rejected assumptions, and current Work Order scope before being treated as valid instructions.
- [ ] Claude plans are checked against the same prior decisions, open questions, rejected assumptions, and current Work Order scope before being treated as valid plans.
- [ ] Agreement is not treated as proof of correctness. Claude must keep prior technical findings unless new evidence, verified context, or corrected reasoning invalidates them.
- [ ] Disagreement is surfaced as a review finding, not smoothed over. If the user asks for something that conflicts with prior reasoning or scope, Claude names the conflict and the stable technical position.
- [ ] A scope quiz is required when scope is ambiguous, drift is suspected, context is long, work resumes after interruption, a new Work Order begins, or the next action could authorize code, benchmark execution, metric collection, artifact contracts, or architecture selection.
- [ ] The scope quiz covers at minimum: current objective, allowed files/actions, forbidden files/actions, halt conditions, measurement/selection authorization state, open blockers, and next safe step.
- [ ] Failure of the scope quiz by either party blocks execution until the shared state is reconciled and recorded.
- [ ] Drift detection is applied continuously: touched files outside the allowed list, semantic claims outside authorization, unrecorded assumptions, phase jumps, implicit selection, implicit measurement, or implicit productionization each trigger a halt or review note.
- [ ] Forced handover is required before context transfer, after long-running work, after a halt, after review-time correction, and before any next Work Order prompt is issued.
- [ ] Every handover includes: goal, current phase, approved scope, changed files, tests run, verification state, open risks, open questions, forbidden next actions, unresolved blockers, and the next safe step.
- [ ] If a scope closes with a recorded or obvious follow-up scope still open, Claude/Codex must not wait for the user to ask for the next prompt. It must state the reason and provide the next Claude-ready prompt immediately, in the form: "`<reason>` nedeniyle `<next scope>` konusunun promptu asagidaki gibi; Claude baslasin." If no follow-up prompt is safe, it must say why and name the blocker.
- [ ] Claude and the user may challenge each other. Challenge handling must distinguish empathy from agreement and must revise positions only when new evidence or corrected reasoning supports revision.
- [ ] Shared understanding gates execution but does not itself authorize new scope. Any new code, dataset, benchmark execution, metric policy, production artifact contract, or architecture selection still requires explicit Codex authorization.
- [ ] If scope, authority, or shared understanding cannot be made explicit, Claude must stop and request clarification rather than proceed by implication.
- [ ] Mandatory Priority-Miss Check precedes Section L only when explicitly triggered: prompts that contain `@pmc` must include the verbatim block in `ai-search/00-claude-scope-prompt-template.md`, and the receiving Claude must answer its six numbered items before responding to the scope; ordinary questions, status checks, command-output requests, syntax fixes, clarification questions, short explanations, and same-scope continuations do not require the check unless `@pmc` is present.

## M. Deferred External Diagnostic Pattern Notes

Added by Codex direct note after review of Microsoft Chat Customizations Evaluations. This section is a non-authorizing discussion queue only. It does not approve an extension, dependency, evaluator, benchmark tool, VS Code integration, Copilot dependency, Waza dependency, prompt search, skill search, agent selection, architecture selection, source qualification, route validation, or benchmark readiness.

- [ ] Consider borrowing the diagnostic artifact shape: category, severity, target, evidence reference, invariant reference, and remediation note.
- [ ] Consider composition-conflict checks across linked or imported instruction materials, while preserving that source material is not a route object.
- [ ] Consider cognitive-load and ambiguity warnings for Work Orders, review packets, and controller instructions.
- [ ] Consider coverage-gap diagnostics for missing halt paths, missing hard negatives, missing non-claim language, and missing literal-False authorization/readiness booleans.
- [ ] Consider Problems-panel-style presentation only as a review UX pattern; UI presentation must not become an architecture source of truth.
- [ ] Any future diagnostic reporter must be deterministic unless explicitly authorized otherwise, and diagnostics must remain review evidence only.
- [ ] Any future use of LLM-assisted semantic review must be advisory, non-gating, and wrapped by explicit deterministic contract checks before it can affect approval.
- [ ] Do not treat prompt, skill, agent, or customization-file diagnostics as route validation, source qualification, benchmark evidence, or production readiness.
