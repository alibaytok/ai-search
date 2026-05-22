# ai-search - Agent Controller Operating Model / Scoped Editable Memory Boundary

Document type: Phase 4 / Phase 9 / Agent controller operating model boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes after Codex review
Work Order: WO-49

---

## 1. Purpose

This document records the ai-search agent controller operating model
at documentation level only. It captures the model as a
phase-aware, scope-aware, assumption-aware agent controller with
editable memory. It is not an implementation. It does not author a
controller program, a memory database, a tool integration, a plugin
runtime, or an automation system. It does not change harness code
or tests. It does not change the WO-39 / WO-40 readiness gate
states.

OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, and OQ-076 all
remain OPEN. RK-039 continues to apply unchanged.
**Real-benchmark-ready remains NO.**

The WO-47 / WO-48 explicit non-claim constraint is inherited
verbatim: this document does not claim the controller, any
controller node, or any memory scope is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected.

## 2. Non-Clone Boundary

This operating model is not a copy of any external "Superpowers"
system, and the document does not claim to implement a software
factory. Both terms are external naming patterns that may exist in
unrelated contexts; this model neither inherits from nor competes
with them.

The actual model recorded here is narrower and ai-search-specific:

- **Phase-aware.** The controller distinguishes conversation phases
  (session start, task intake, mid-work, correction or challenge,
  approval-to-implement, pre-edit, pre-final, new task,
  context-loss or resume) and selects different behavior for each.
- **Scope-aware.** The controller distinguishes task scopes (tiny,
  bounded, shared-surface, runtime / debug, contract / API /
  send-flow, migration / refactor) and selects different
  verification discipline for each.
- **Assumption-aware.** The controller classifies each assumption
  it surfaces (safe, researchable, user-required, blocking) and
  routes accordingly: researchable assumptions are inspected or
  researched before being asked of the user; blocking
  user-required assumptions prevent final output until resolved.
- **Editable memory.** The controller's memory is partitioned into
  four scopes (conversation, project, global, user preference);
  every memory item has a lifecycle (active, draft, needs-review,
  obsolete); every memory item supports list / edit / delete /
  promote / demote / mark-obsolete / show-why-applied /
  disable-for-current-task operations.

The model is a control plane around prompt handling. It does not
prescribe a particular AI provider, a particular language, a
particular IDE integration, a particular plugin runtime, or a
particular memory back-end. Those are implementation choices and
remain out of scope here.

## 3. Main Controller Graph

The controller is described as a graph of twelve nodes traversed
during a prompt-response cycle. Edges are not exhaustively
enumerated; the document defines what each node does. Skips and
loops are governed by the routing rules in later sections.

1. **User Prompt.** The new input from the user. Captured verbatim;
   no paraphrase yet.
2. **Conversation Replay.** Stable prior decisions from this
   conversation are surfaced as a small ordered list (see Section
   8). New evidence is separated from new framing.
3. **Memory Retrieval.** Project, global, and user-preference
   memory entries scoped to the current intent are surfaced.
   Conversation memory is already in context.
4. **Intent Parse.** The user's intent is extracted into an
   operational statement: what is asked, what is not asked, what
   would be a halt condition.
5. **Assumption Ledger.** Each assumption the agent makes is
   classified (safe / researchable / user-required / blocking).
   See Section 7.
6. **Inspect/Research vs Ask User branch.** Researchable
   assumptions are inspected or researched before being asked of
   the user. Blocking user-required assumptions are asked. Safe
   assumptions are stated and proceeded with.
7. **Scope + Phase Classifier.** The current task is placed on
   both classifier axes (see Section 4).
8. **Workflow Selector.** Based on scope and phase, a workflow is
   selected from Section 5.
9. **Execution / Answer.** The selected workflow runs. This may be
   a quick answer, a small patch, a discovery + plan + scoped
   patch, an observation-and-fix loop, a payload-and-approval
   gate, or a plan + staged execution.
10. **Verification Gate.** Before any final output, the agent ties
    final claims to proof. If proof is incomplete, the agent
    states residual risk explicitly. See Section 11.
11. **Final Output or Residual Risk / Question.** The agent either
    delivers the final output, returns residual risk, or returns a
    question. Final output is allowed only when the conditions in
    Section 6 are met.
12. **Lesson Capture / Memory Update.** Observations worth
    remembering are recorded into conversation memory; promotion
    to project / global / user-preference memory follows the
    lifecycle in Section 15.

## 4. Classifier Axes

### 4.1 Task Scope (six levels)

- **tiny** - one-line answer, micro-edit, fact lookup; no
  cross-file concern.
- **bounded** - one file or a small known set of files; targeted
  intent; clear pre-state.
- **shared-surface** - touches a contract, schema, public API,
  protocol, or multi-consumer module; requires discovery before
  change.
- **runtime / debug** - the system already runs and exhibits a
  symptom; the task is to observe, reproduce, root-cause, and
  fix.
- **contract / API / send-flow** - the change affects a payload, a
  send-side effect, an external system call, or a downstream
  consumer; approval gate required before execution.
- **migration / refactor** - non-trivial restructuring; plan
  artifact required; staged execution; review gate.

### 4.2 Conversation Phase (nine values)

- **session start** - the first turn of a new session.
- **task intake** - a new task has been described; the agent has
  not yet committed to an approach.
- **mid-work** - the agent is mid-execution of an accepted plan.
- **correction or challenge** - the user has corrected, pushed
  back, or asked the agent to reconsider.
- **approval-to-implement** - the user has approved a plan; the
  agent is about to start implementation.
- **pre-edit** - the agent is about to write or modify a file.
- **pre-final** - the agent is about to issue a final answer or
  submit an evidence report.
- **new task** - the user has switched intent away from the
  current task.
- **context-loss or resume** - a context window has been summarized
  or a session is being resumed; the agent must re-anchor before
  acting.

## 5. Workflow Routing Rules

Selection is driven by task scope, with phase modulating
verification depth. The six routing rules:

- **tiny -> quick answer / small patch / minimal verification.**
  Answer directly; if a patch is involved, apply it; verify only
  the immediate change.
- **bounded -> read relevant files / scoped patch / targeted
  test.** Read the files in scope; produce a scoped patch; add or
  run a targeted test that exercises the change.
- **shared-surface -> discovery / explicit plan / regression or
  TDD / multi-test.** Conduct discovery of the shared surface;
  produce an explicit written plan; add regression tests or
  follow test-driven development; run multiple tests covering the
  affected consumers.
- **runtime / debug -> observe / reproduce / root cause / fix /
  verify.** Capture observations before patching; reproduce the
  symptom; identify the root cause; only then fix; verify the fix
  against the reproduction.
- **contract / API / send-flow -> payload / dry-run / approval
  gate.** Construct the payload or send-side change; dry-run
  where possible; pause for explicit approval before any
  irreversible side effect.
- **migration / refactor -> plan artifact / staged execution /
  review gate.** Produce a plan artifact (file, document, or
  ledger entry); execute in stages; gate the final stage on
  review.

Phase modulates: in **correction or challenge** phase, the agent
re-validates prior reasoning before continuing; in **pre-final**
phase, the agent applies Section 11 verification before issuing
final output; in **context-loss or resume**, the agent runs the
re-anchor routine from Section 10.

## 6. Prompt Handling Rule

The agent does not always issue a final answer immediately on
receiving a prompt. The decision is governed by three conditions
that must all hold for final output to be allowed:

1. **Intent is clear.** The user's request is operationally
   parsed; no ambiguity that would change the action.
2. **Assumptions are low-risk or resolved.** Every assumption is
   classified per Section 7; no blocking user-required assumption
   is unresolved.
3. **Proof exists or residual risk is stated.** Either the agent
   has verification evidence for the claims it is about to make,
   or it explicitly names what remains unverified.

No final output is issued when any of the following holds:

- A blocking user-required assumption is unresolved.
- The change carries destructive risk, live-system risk, or
  contract risk that has not been explicitly approved.
- The agent is guessing rather than reasoning from evidence or
  recorded decisions.

In these cases the agent returns either a clarifying question, a
residual-risk statement, or a halt-and-report.

## 7. Assumption Ledger

Every assumption the agent makes in the current task is classified
into one of four categories:

- **safe** - the assumption is consistent with stable repository
  decisions and is unlikely to change the action. State it and
  proceed.
- **researchable** - the assumption can be confirmed or rejected
  by inspecting code, docs, trackers, prior decisions, or
  recorded artifacts. The agent inspects or researches before
  asking the user.
- **user-required** - the assumption depends on user-side
  preference, environment, or external state that the agent
  cannot inspect. The agent asks the user.
- **blocking** - a user-required assumption whose resolution
  changes the action. Final output is withheld until the user
  resolves the assumption.

Routing rule (cross-cutting): a researchable assumption MAY NOT
be escalated to a user-required question before the agent has
attempted inspection or research. The conversation should not
ask the user a question the agent can answer from recorded
state.

## 8. Conversation Replay / Decision Ledger

Stable prior decisions in the current conversation are checked
before the agent acts on a new prompt that could conflict with
them. Replay rules:

- The agent maintains an ordered list of stable prior decisions
  for the conversation. "Stable" means the decision has been
  recorded as a finding, a halt, a recorded scope quiz, or a
  Codex-approved direction.
- New input is classified as either **new evidence** (facts,
  measurements, citations, recorded changes) or **new framing**
  (rephrasing, rhetorical pressure, opinion). New framing alone
  does NOT override a stable prior technical position.
- A prior technical position is revised only when new evidence
  or corrected reasoning supports revision. The revision is
  recorded explicitly with a reason.
- Codex-recorded decisions (DC entries in `00-open-questions.md`)
  are the highest tier of stable prior decisions; the agent
  does not override them in conversation.

## 9. Intent Echo / Hard Debug

Intent echo is the practice of restating the user's request in
operational terms before acting. Hard debug is the practice of
exposing the agent's reasoning at depth so the user can audit it
in flight.

Both are tools, not defaults. The agent uses them when:

- The user explicitly requests an echo or a hard debug.
- The prompt is ambiguous or risky (contract surface, destructive
  operation, multi-step workflow).
- The agent's prior reading of the user's intent has produced a
  visible correction in the conversation.

The agent does NOT run intent echo or hard debug on every prompt.
Default-on intent echo is a friction tax on simple work; it is
applied only when the cost of misreading is high.

## 10. Agent Mode Router

The agent runs a bootstrap routine (scope load, decision replay,
memory retrieval, classifier reset) only at a small set of
moments:

- **Session start.** First turn of a new session.
- **New task.** The user has switched intent away from the current
  task.
- **Scope change.** The current task's classifier axis assignment
  has changed (e.g., bounded -> shared-surface).
- **Risk escalation.** A new risk has been identified that
  changes verification depth.
- **Context loss.** A context window summarization has happened, or
  the session is being resumed.

The agent does NOT re-run heavy bootstrap on every prompt. Doing
so would tax tiny tasks with the cost of large-task discipline.
The bootstrap routine is the most-expensive controller behavior;
its trigger set is deliberately small.

## 11. Pre-Completion Verification

Before final output, the agent ties claims to proof:

- For factual claims, the agent cites the source (file path, line
  reference, test result, recorded decision, command output).
- For implementation claims ("done", "passing", "verified"), the
  agent runs the relevant verification (test suite, type check,
  build, observable behavior) and records the result.
- When proof is incomplete (e.g., the agent could not run a test,
  the user-facing behavior was not observed end-to-end), the
  agent uses **residual-risk language**: "this is implemented as
  described and passes the recorded verification; the following
  is not verified: ...".
- The words "done", "validated", "verified", or equivalents are
  allowed only when the evidence level matches. Using strong
  completion language without matching evidence is a verification
  failure that the agent must correct before final output.

## 12. Dirty Worktree Protection

Before any code edit, the agent inspects local repository state
when applicable:

- The agent distinguishes **user changes** (uncommitted edits made
  by the user) from **agent changes** (edits made earlier in the
  same session by the agent).
- The agent does not overwrite user changes silently. If a
  user-modified file is about to be touched, the agent surfaces
  this and asks before proceeding.
- The agent does not assume a clean worktree. If the worktree is
  dirty, the agent records that the dirtiness predates the
  agent's session.
- For destructive operations (force-push, hard reset, branch
  delete), the agent asks explicitly before acting.

This protection applies only where code edits are part of the
workflow. Conversation-only or documentation-only turns do not
trigger it.

## 13. Systematic Debugging

When the task is **runtime / debug**, the agent does not patch
before root cause. The discipline is:

1. **Observe.** Capture the symptom as reported, plus any logs,
   stack traces, or repro inputs available.
2. **Reproduce.** Construct a minimal reproduction. If the agent
   cannot reproduce, that fact is itself an observation, not a
   reason to guess.
3. **Root cause.** Identify the cause. Separate **observations**
   (what is recorded) from **guesses** (what the agent suspects).
   Guesses are stated as guesses.
4. **Fix.** Apply the smallest change that addresses the root
   cause. Larger refactors are deferred to a separate task.
5. **Verify.** Re-run the reproduction. The fix is "verified" only
   when the reproduction no longer triggers the symptom.

Snapshots, test results, logs, and reproductions are first-class
observations. Guesses are not. The two are kept separate in the
agent's reasoning.

## 14. Shared-Change TDD

Test-driven development (write the test, watch it fail, write the
code, watch it pass) is required for **shared-surface** or
**contract-sensitive** changes (a public function, an API
contract, a payload schema, a registered interface).

TDD is NOT mandatory for every tiny task. A spelling fix in a
comment, a one-line patch to a private helper, or a documentation
edit does not require a test-first cycle.

The threshold is the blast radius of the change. Higher blast
radius -> stricter test-first discipline. Lower blast radius ->
the testing cost is matched to the change size.

## 15. Memory Scope And Editability

The controller's memory is partitioned into four scopes:

- **conversation memory** - bounded to the current conversation;
  ephemeral by default; promoted only when explicitly captured.
- **project memory** - scoped to the current project (this
  repository); persists across conversations within the project;
  consulted on every project-scoped task.
- **global memory** - scoped across projects; persists; consulted
  when project memory is absent or the question is
  project-agnostic.
- **user preference memory** - records user-stated preferences
  (style, terminology, workflow defaults); consulted to align
  responses with the user's preferred form.

### 15.1 Promotion path

Observations move along an explicit path; no scope is auto-promoted:

1. **Chat observation.** A noticed pattern in the current turn.
2. **Conversation memory.** Captured for the current conversation
   after it is named or referenced more than once.
3. **Project memory.** Promoted when repeated across sessions OR
   when the user confirms the observation is project-stable.
4. **Global memory.** Promoted only after the observation has
   proven stable across multiple projects.

### 15.2 Lifecycle

Each memory item carries a lifecycle state:

- **active** - in force; consulted on the relevant scope.
- **draft** - captured but not yet active; under review.
- **needs-review** - active but a signal has questioned its
  validity (a contradicting observation, a stale citation, a
  user correction); pending re-evaluation.
- **obsolete** - retired; not consulted; preserved for audit.

### 15.3 Required operations

Every memory item must support, at boundary level:

- **list** - enumerate items in a scope.
- **edit** - revise the item's content.
- **delete** - remove the item from active consultation (with
  audit trail).
- **promote** - move along the promotion path in Section 15.1.
- **demote** - move backward along the promotion path when a
  scope no longer holds.
- **mark obsolete** - move to the obsolete lifecycle state.
- **show why applied** - reveal which memory item informed a
  given response, with citation.
- **disable for current task** - temporarily exclude an item
  from consultation without changing its lifecycle state.

The list of operations is a boundary requirement, not an
implementation. A future Codex packet may author the
implementation surface (storage, indexing, edit UI). WO-49 does
not author it.

## 16. Priority Order

When multiple controller behaviors apply to the same prompt, they
run in this priority order (highest first):

1. **conversation-replay-ledger** - stable prior decisions in this
   conversation are surfaced first; new framing does not override
   them.
2. **assumption-ledger** - each assumption is classified before
   action is selected.
3. **agent-mode-router** - bootstrap runs only at the trigger
   moments in Section 10, not on every prompt.
4. **pre-completion-verification** - final claims are tied to
   proof before output is issued.
5. **dirty-worktree-protection** - code edits inspect local state
   first.
6. **systematic-debugging** - debug workflow observes before
   patching.
7. **shared-change-tdd** - shared-surface or contract-sensitive
   changes follow test-first discipline.
8. **memory-scope-editability** - memory operations follow the
   scope and lifecycle in Section 15.
9. **light bootstrap** - the minimal re-anchor (scope load,
   decision replay) runs LAST in the priority order; it is the
   smallest-cost behavior and is acceptable on every prompt where
   the heavy bootstrap is not triggered.

## 17. Controller Principle

**Keep simple work simple. Put risky work under discipline.**

The controller is not an everything-everywhere protocol. Tiny
tasks should not pay the cost of shared-surface discipline.
Shared-surface tasks should not skip discipline because the
prompt sounds simple. The classifier (Section 4) and the routing
rules (Section 5) match the cost of verification to the blast
radius of the change.

## 18. Forbidden Scope

WO-49 is forbidden from doing any of the following:

- Implementing a controller program, a memory database, a
  plugin runtime, a tool integration framework, or an automation
  system.
- Modifying any harness implementation module or any harness
  test file.
- Adding any third-party dependency.
- Authoring code anywhere outside the three allowed files.
- Claiming the controller is "the" software factory, a clone of
  any external system, or a global behavior protocol.
- Claiming the controller, any controller node, any classifier
  axis, any routing rule, any memory scope, or any priority
  level is sufficient, necessary, superior, best, complete,
  production-ready, recommended, or selected.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Changing the WO-39 / WO-40 readiness gate states. The four
  states (scaffold-ready YES, artifact-ready YES,
  review-summary-ready YES, real-benchmark-ready NO) are
  unchanged by WO-49.
- Performing real benchmark execution.
- Mutating any file under `benchmark-fixtures/`.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076. All seven remain OPEN.
- Duplicating RK-039.
- Introducing a CLI, an entry point, a console script, or any
  shell wrapper.
- Authoring Stage 2 / 3 / 4 / 5 measurement scaffolding or any
  real adapter / real metric / real benchmark surface.

The model is documentation only. A future Codex packet that
proposes implementing any part of the model must explicitly name
the scope, allowed files, forbidden scope, acceptance criteria,
and evidence requirements at issue time.
