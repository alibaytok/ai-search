# ai-search - Claude Scope Prompt Template

Document type: Project-local prompt template
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Status: Durable. Mandatory for every new scope prompt in this project.
Authority: This template does NOT modify canonical authority. Canonical
authority remains with `ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. On conflict, canonical wins and
this template must be corrected.

## 1. Why this template exists

This template was added because Level 0B downstream trace work
initially masked the missing upstream prompt-text-to-intent layer.
WO-L0-WORKSHOP-TRACE-01 and WO-L0-WORKSHOP-REVIEW-01 were
implemented while the genuine upstream prerequisite - turning a
free-text user prompt into a canonical intent representation -
was still absent. The packets themselves were internally
coherent, but the chain of packets was solving downstream surface
while skipping the upstream cause. The Mandatory Priority-Miss
Check below is the project-local mechanism that surfaces such
sequencing gaps before scope work begins.

This template does NOT guarantee that any new chat absolutely
remembers it. It is a project-local convention, not a machine-
enforced hook. Reviewers and prompt authors are responsible for
prepending the block; the convention exists so the responsibility
is visible and durable across sessions.

## 2. Where this template applies

The Mandatory Priority-Miss Check block in Section 4 below applies
to every new scope prompt issued in this project, including:

- implementation packets (Work Orders)
- review packets (review-only deep analysis)
- analysis packets (architecture / contract / sequencing reviews)
- Work Order drafting prompts (proposed-WO authoring)
- Claude evidence handling (evidence report drafting / review)
- diagnostic prompts that could authorize new code, benchmark
  execution, metric collection, artifact contracts, or
  architecture / vendor / library / index-family selection

It precedes - it does NOT replace - the Section L scope quiz in
`ai-search/00-controller-checklist.md`. Section L verifies that
shared state and scope are explicit; the Mandatory Priority-Miss
Check verifies that the scope itself is the correct upstream
scope to address.

## 3. How to use this template

When drafting a new scope prompt for Claude in this project:

1. Copy the entire Mandatory Priority-Miss Check block from
   Section 4 below into the top of the new prompt, verbatim.
2. Append the new scope's body beneath the block.
3. Do NOT remove or rephrase the block to make it shorter. The
   block is the contract.
4. The receiving Claude must answer the six numbered check items
   FIRST, then proceed to the requested scope. If concerns exist,
   Claude states them as blocker or risk notes before answering.
   If none exist, Claude must state the explicit literal:
   "Priority-miss check: no higher-priority missed scope found."

## 4. Mandatory Priority-Miss Check block (verbatim)

The following block is the canonical copy. It must be prepended to
every new scope prompt in this project. Do not edit it inline in
the prompt - copy verbatim.

```
Mandatory Priority-Miss Check - Required Before Scope Response

Before answering, implementing, reviewing, or proposing anything
for this scope, first check:

1. Are we forgetting a higher-priority prerequisite, upstream
   boundary, unresolved core problem, or previously recorded risk?
2. Is this scope solving a downstream surface while skipping the
   actual upstream cause?
3. Is there a safer, more direct, or more correct sequencing than
   the requested scope?
4. Does this scope conflict with any prior invariant, open OQ,
   RK risk, non-claim, or real-benchmark-ready NO boundary?
5. If any concern exists, state it first as a blocker or risk
   note before answering the requested prompt.
6. If no concern exists, explicitly say: "Priority-miss check:
   no higher-priority missed scope found."

Only after this check, answer the requested scope.

Do not optimize for agreement. Do not proceed just because the
requested scope sounds approved. Preserve prior constraints, open
questions, risks, and non-claims.
```

## 5. What this template does NOT do

- Does NOT replace, weaken, or narrow
  `ai-search/00-controller-checklist.md` Section L. Section L's
  Mutual Alignment Protocol still governs scope verification; this
  template adds a pre-Section-L priority-miss prompt convention.
- Does NOT introduce automation, scripts, generators, package
  files, CI, or new project structure.
- Does NOT introduce a Claude Code hook, settings file, or any
  machine-enforced prepend mechanism. Two stronger options
  (project-level `.claude/settings.json` `UserPromptSubmit` hook;
  user-global `~/.claude/settings.json` hook) exist and would
  actually enforce the prepend, but both require explicit Codex
  authorization in a separate packet because each counts as new
  project structure or out-of-repo state.
- Does NOT authorize real indexing, retrieval, ranking, scoring,
  source qualification, corpus admission, route creation, route
  selection, benchmark execution, real-benchmark-ready, or any
  architecture / vendor / library / index-family / ANN backend /
  reranker / retrieval-family / production-system selection.
- Does NOT close any OQ. Does NOT duplicate RK-039.
- Does NOT claim that any future chat absolutely remembers the
  block. The template is a project-local convention with the
  responsibility on prompt authors and reviewing Claude sessions.
- Does NOT claim sufficiency, necessity, superiority, best,
  complete, production-ready, recommended, or selected status for
  the priority-miss mechanism itself. It is the smallest durable
  doc-only artifact that fits the project's constraints.

## 6. Non-claim envelope

All DC-020 through DC-070 boundary invariants carry forward. This
template does not amend or broaden DC-003 through DC-070. Real-
benchmark-ready remains NO. OQ-003, OQ-015, OQ-031, OQ-035,
OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain
OPEN. RK-039 remains active and is not duplicated.
