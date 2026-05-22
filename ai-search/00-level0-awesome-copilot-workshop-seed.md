# Level 0B Awesome-Copilot Workshop Seed Plan

Document type: Planning artifact / workshop seed
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-WORKSHOP-01

## Authority

This is a planning artifact. It is NOT a project-authority document
and does NOT authorize implementation. Canonical authority remains
with `ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. If this file conflicts with
canonical documents, canonical wins.

This workshop seed is the next-immediate Level 0B planning variant;
it does NOT replace the broader seven-source Level 0B seed, which
remains scheduled for a later run.

## 1. Purpose

This document defines a single-repo Level 0B workshop seed using
`github/awesome-copilot` for prompt-router indexing trace
observability. The visible trace chain we are testing is:

```
prompt -> normalized intent -> touched material refs ->
candidate route / workflow fragments -> rejection reasons ->
no forced selection
```

The workshop seed is faster than the seven-source seed because one
repo provides multiple structurally-distinct shapes in one license
and one navigation convention. It is narrower because it
concentrates on a single-vendor surface; the seven-source seed
remains the cross-vendor variant for later coverage.

Codex-verified repo structure (top-level): `skills/`, `plugins/`,
`agents/`, `instructions/`, `cookbook/`, `hooks/`, `workflows/`,
`docs/`, and repo meta files. There is no `prompts/` folder and no
`chatmodes/` folder. `*.prompt.md` count is 0. Verified
file-pattern counts: `*.agent.md` = 215; `*.instructions.md` = 184;
`SKILL.md` = 494.

## 2. Source-Shape Table

| item_kind | verified folder | role for Level 0B trace |
|-----------|-----------------|-------------------------|
| `skill` | `skills/` (494 `SKILL.md` candidates) | Skill collection material. Candidate-only; must not be promoted to route. |
| `instruction` | `instructions/` (184 `*.instructions.md` candidates) | Instruction / behavior-customization material. Distinct from skill shape; candidate-only. |
| `agent` | `agents/` (215 `*.agent.md` candidates) | Agent / persona material. Route-adjacent in shape; explicitly NOT a route. |
| `workflow_file` | `workflows/` | Multi-step recipe material. Most route-adjacent shape; eligible to become candidate workflow fragments with `candidate_only: True`. |
| `hook` | `hooks/` | Event-trigger configurations. Workflow-adjacent but operationally distinct from invocation-style workflows. |
| `plugin` | `plugins/` | Tool / integration definitions. Tool-description-shape. |
| `cookbook_entry` | `cookbook/` | Narrative / recipe / how-to content. Doubles as in-repo prompt-like material (since `*.prompt.md` count is 0) AND as some-near-miss narrative. |
| `repo_meta_section` | `docs/` plus root meta files | In-repo encyclopedic / near-miss material. Must be rejected with an explicit reason. |

These eight item kinds are bounded by WO-L0-WORKSHOP-01 and are NOT
claimed exhaustive.

## 3. Item Slot Plan

Target: 70 slot rows (within the 60-80 range). All rows are at
slot / locator / shape granularity only. No external content body
is copied. The boundary_note literal is exactly
`not admitted; not qualified; workshop metadata only`.

Per-kind counts:

- skill: 16
- instruction: 12
- agent: 12
- workflow_file: 8
- hook: 5
- plugin: 4
- cookbook_entry: 7
- repo_meta_section: 6
- **Total: 70**

| workshop_item_id | repo_path_shape | item_kind | selection_locator_hint | material_role | expected_trace_surface | boundary_note |
|------------------|-----------------|-----------|------------------------|---------------|------------------------|---------------|
| W-ITEM-001 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` (one of 494; reviewer selects) | code-review-shaped skill slot | candidate skill fragment with `candidate_only: True` | not admitted; not qualified; workshop metadata only |
| W-ITEM-002 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | summarization-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-003 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | translation-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-004 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | linting-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-005 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | test-authoring-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-006 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | doc-generation-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-007 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | release-notes-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-008 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | refactor-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-009 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | format-conversion-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-010 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | classification-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-011 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | data-extraction-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-012 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | static-analysis-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-013 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | search-helper-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-014 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | reporting-shaped skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-015 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` (one of 184) | Python-conventions instruction slot | candidate instruction fragment distinct from skill shape | not admitted; not qualified; workshop metadata only |
| W-ITEM-016 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | code-review instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-017 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | testing instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-018 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | docs-style instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-019 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | release-process instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-020 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | commit-message instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-021 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | security-review instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-022 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | refactor instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-023 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | translation-conventions instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-024 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | accessibility instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-025 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | dependency-policy instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-026 | `agents/` | agent | `agents/<NAME>.agent.md` (one of 215) | code-reviewer agent slot | candidate agent fragment; must NOT be promoted to route | not admitted; not qualified; workshop metadata only |
| W-ITEM-027 | `agents/` | agent | `agents/<NAME>.agent.md` | documentation-writer agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-028 | `agents/` | agent | `agents/<NAME>.agent.md` | refactorer agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-029 | `agents/` | agent | `agents/<NAME>.agent.md` | release-manager agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-030 | `agents/` | agent | `agents/<NAME>.agent.md` | security-reviewer agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-031 | `agents/` | agent | `agents/<NAME>.agent.md` | test-author agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-032 | `agents/` | agent | `agents/<NAME>.agent.md` | translator agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-033 | `agents/` | agent | `agents/<NAME>.agent.md` | summarizer agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-034 | `agents/` | agent | `agents/<NAME>.agent.md` | static-analysis agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-035 | `agents/` | agent | `agents/<NAME>.agent.md` | dependency-auditor agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-036 | `agents/` | agent | `agents/<NAME>.agent.md` | accessibility-reviewer agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-037 | `agents/` | agent | `agents/<NAME>.agent.md` | release-notes agent slot | candidate agent fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-038 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | Python CI starter workflow slot | candidate workflow fragment with `candidate_only: True` | not admitted; not qualified; workshop metadata only |
| W-ITEM-039 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | Node.js CI starter workflow slot | candidate workflow fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-040 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | Docker CI starter workflow slot | candidate workflow fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-041 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | static-site deployment workflow slot | candidate workflow fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-042 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | Azure deployment workflow slot | candidate workflow fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-043 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | container-registry release workflow slot | candidate workflow fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-044 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | CodeQL static-analysis workflow slot | candidate workflow fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-045 | `workflows/` | workflow_file | `workflows/<sub-folder>/<NAME>` | dependency-scanning workflow slot | candidate workflow fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-046 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | workflow-troubleshooting skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-047 | `skills/` | skill | `skills/<sub-folder>/SKILL.md` | CI-guidance skill slot | candidate skill fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-048 | `instructions/` | instruction | `instructions/<NAME>.instructions.md` | workflow-review instruction slot | candidate instruction fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-049 | `cookbook/` | cookbook_entry | `cookbook/<NAME>` | how-to recipe slot (test-on-PR workflow) | candidate cookbook-narrative fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-050 | `hooks/` | hook | `hooks/<NAME>` (reviewer verifies) | pre-commit hook slot | candidate workflow-shape material distinct from invocation workflows | not admitted; not qualified; workshop metadata only |
| W-ITEM-051 | `hooks/` | hook | `hooks/<NAME>` | post-merge hook slot | candidate workflow-shape material | not admitted; not qualified; workshop metadata only |
| W-ITEM-052 | `hooks/` | hook | `hooks/<NAME>` | release-tag hook slot | candidate workflow-shape material | not admitted; not qualified; workshop metadata only |
| W-ITEM-053 | `hooks/` | hook | `hooks/<NAME>` | scheduled-event hook slot | candidate workflow-shape material | not admitted; not qualified; workshop metadata only |
| W-ITEM-054 | `hooks/` | hook | `hooks/<NAME>` | issue-event hook slot | candidate workflow-shape material | not admitted; not qualified; workshop metadata only |
| W-ITEM-055 | `plugins/` | plugin | `plugins/<NAME>` | tool-integration plugin slot | candidate tool-description fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-056 | `plugins/` | plugin | `plugins/<NAME>` | linting plugin slot | candidate tool-description fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-057 | `plugins/` | plugin | `plugins/<NAME>` | reporting plugin slot | candidate tool-description fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-058 | `plugins/` | plugin | `plugins/<NAME>` | notification plugin slot | candidate tool-description fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-059 | `cookbook/` | cookbook_entry | `cookbook/<NAME>` | how-to recipe slot (CI setup) | candidate cookbook-narrative fragment for prompt-like intent | not admitted; not qualified; workshop metadata only |
| W-ITEM-060 | `cookbook/` | cookbook_entry | `cookbook/<NAME>` | how-to recipe slot (deployment) | candidate cookbook-narrative fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-061 | `cookbook/` | cookbook_entry | `cookbook/<NAME>` | how-to recipe slot (release process) | candidate cookbook-narrative fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-062 | `cookbook/` | cookbook_entry | `cookbook/<NAME>` | how-to recipe slot (code review) | candidate cookbook-narrative fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-063 | `cookbook/` | cookbook_entry | `cookbook/<NAME>` | how-to recipe slot (static-site publish) | candidate cookbook-narrative fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-064 | `cookbook/` | cookbook_entry | `cookbook/<NAME>` | how-to recipe slot (dependency hygiene) | candidate cookbook-narrative fragment | not admitted; not qualified; workshop metadata only |
| W-ITEM-065 | root meta | repo_meta_section | `README.md` lead section | in-repo encyclopedic near-miss material | observed and rejected with explicit `repo_meta_section` reason | not admitted; not qualified; workshop metadata only |
| W-ITEM-066 | root meta | repo_meta_section | `README.md` navigation table | repo navigation; near-miss | observed and rejected | not admitted; not qualified; workshop metadata only |
| W-ITEM-067 | root meta | repo_meta_section | `CONTRIBUTING.md` | contribution-guide near-miss | observed and rejected | not admitted; not qualified; workshop metadata only |
| W-ITEM-068 | `docs/` | repo_meta_section | `docs/<NAME>.md` overview | docs-overview near-miss | observed and rejected | not admitted; not qualified; workshop metadata only |
| W-ITEM-069 | `docs/` | repo_meta_section | `docs/<NAME>.md` glossary-shaped | docs-glossary near-miss | observed and rejected | not admitted; not qualified; workshop metadata only |
| W-ITEM-070 | root meta | repo_meta_section | license / badges block | repo-meta administrative content | observed and rejected | not admitted; not qualified; workshop metadata only |

## 4. Prompt Slot Plan

Target: 26 prompts. All `prompt_text` strings below are synthetic
test inputs authored by Claude under WO-L0-WORKSHOP-01 specifically
to exercise the visible-trace path. No external prompt body is
copied. The boundary_note literal is exactly
`not admitted; not qualified; workshop metadata only`.

Per-category counts:

- A. clear single-intent: 4
- B. workflow intent: 4
- C. skill intent: 3
- D. agent / persona confusion: 3
- E. instruction confusion: 3
- F. prompt-search-shaped but workflow-intent: 2
- G. ambiguous: 3
- H. no-route: 2
- I. near-miss / rejection: 2
- **Total: 26**

| workshop_prompt_id | category | prompt_text | expected_item_kinds_touched | expected_candidate_surface | expected_rejection_surface | boundary_note |
|---------------------|----------|-------------|------------------------------|----------------------------|----------------------------|---------------|
| W-PRM-001 | A. clear single-intent | Set up a CI workflow that runs pytest on every push. | workflow_file | candidate workflow fragment referencing Python CI workflow slot, `candidate_only: True` | none | not admitted; not qualified; workshop metadata only |
| W-PRM-002 | A. clear single-intent | Create a code review skill for my repository. | skill | candidate skill fragment, `candidate_only: True` | none | not admitted; not qualified; workshop metadata only |
| W-PRM-003 | A. clear single-intent | Generate an agent definition for a documentation writer. | agent | candidate agent fragment, `candidate_only: True`; not promoted to route | none | not admitted; not qualified; workshop metadata only |
| W-PRM-004 | A. clear single-intent | Write an instruction file for our Python style conventions. | instruction | candidate instruction fragment, `candidate_only: True` | none | not admitted; not qualified; workshop metadata only |
| W-PRM-005 | B. workflow intent | Configure GitHub Actions to deploy a Node.js app to Azure. | workflow_file | candidate workflow fragments referencing Node.js / Azure deployment slots | none | not admitted; not qualified; workshop metadata only |
| W-PRM-006 | B. workflow intent | Add a release workflow that publishes container images. | workflow_file | candidate workflow fragment referencing container-registry release slot | none | not admitted; not qualified; workshop metadata only |
| W-PRM-007 | B. workflow intent | Set up scheduled dependency scanning every Monday. | workflow_file; hook | candidate workflow fragment referencing dependency-scanning slot; hook material observed | none | not admitted; not qualified; workshop metadata only |
| W-PRM-008 | B. workflow intent | Wire up a workflow that runs static analysis on pull requests. | workflow_file | candidate workflow fragment referencing CodeQL / static-analysis slot | none | not admitted; not qualified; workshop metadata only |
| W-PRM-009 | C. skill intent | Create a skill that summarizes commit history into release notes. | skill | candidate skill fragment referencing summarization / release-notes slot | none | not admitted; not qualified; workshop metadata only |
| W-PRM-010 | C. skill intent | Add a skill that converts markdown tables into JSON. | skill | candidate skill fragment referencing format-conversion slot | none | not admitted; not qualified; workshop metadata only |
| W-PRM-011 | C. skill intent | Define a code-review skill that focuses on null-safety. | skill | candidate skill fragment referencing code-review-shaped slot | none | not admitted; not qualified; workshop metadata only |
| W-PRM-012 | D. agent/persona confusion | Give me a security-reviewer agent that runs CodeQL. | agent; workflow_file | candidate agent fragment (security-reviewer) AND candidate workflow fragment (CodeQL); agent NOT promoted to route | possibly secondary rejection of pure-agent interpretation if intent resolves to workflow | not admitted; not qualified; workshop metadata only |
| W-PRM-013 | D. agent/persona confusion | Set up a documentation-writer persona that publishes to GitHub Pages. | agent; workflow_file | candidate agent fragment (documentation-writer) AND candidate workflow fragment (static-site publish); intent resolves to multi-shape | possibly secondary rejection of pure-persona interpretation | not admitted; not qualified; workshop metadata only |
| W-PRM-014 | D. agent/persona confusion | Define an agent that runs a test workflow on demand. | agent; workflow_file | candidate agent fragment AND candidate workflow fragment (test-on-PR); not promoted to route | possibly secondary rejection if surface-form-only interpretation | not admitted; not qualified; workshop metadata only |
| W-PRM-015 | E. instruction confusion | Add instructions for setting up CI on a new Python repo. | instruction; workflow_file | candidate instruction fragment AND candidate workflow fragment (Python CI); both candidate-only | possibly secondary rejection of pure-instruction interpretation | not admitted; not qualified; workshop metadata only |
| W-PRM-016 | E. instruction confusion | Write instructions for our team's release process. | instruction; workflow_file | candidate instruction fragment AND candidate workflow fragment (release-publish); both candidate-only | possibly secondary rejection of pure-instruction interpretation | not admitted; not qualified; workshop metadata only |
| W-PRM-017 | E. instruction confusion | Document the steps an instruction file should follow to deploy. | instruction; workflow_file | candidate instruction fragment AND candidate workflow fragment (deployment); both candidate-only | possibly secondary rejection of pure-instruction interpretation | not admitted; not qualified; workshop metadata only |
| W-PRM-018 | F. prompt-search-shaped but workflow-intent | Find me a prompt that sets up Docker builds in CI. | cookbook_entry; workflow_file | candidate workflow fragment referencing Docker CI slot AND candidate cookbook-narrative fragment; intent resolves to workflow despite surface | rejection of pure-prompt-search interpretation (no `prompts/` folder exists) | not admitted; not qualified; workshop metadata only |
| W-PRM-019 | F. prompt-search-shaped but workflow-intent | Show me a cookbook recipe that deploys a static site to GitHub Pages. | cookbook_entry; workflow_file | candidate cookbook-narrative fragment AND candidate workflow fragment (static-site deployment); both candidate-only | none | not admitted; not qualified; workshop metadata only |
| W-PRM-020 | G. ambiguous | Improve the way we handle code reviews. | skill; instruction; agent | several candidate fragments across multiple shapes with explicit ambiguity observation | none forced | not admitted; not qualified; workshop metadata only |
| W-PRM-021 | G. ambiguous | Help with my release process. | workflow_file; instruction; cookbook_entry | several candidate fragments with ambiguity observation | none forced | not admitted; not qualified; workshop metadata only |
| W-PRM-022 | G. ambiguous | Make our pull requests cleaner. | skill; instruction; workflow_file | several candidate fragments with ambiguity observation | none forced | not admitted; not qualified; workshop metadata only |
| W-PRM-023 | H. no-route | What year did the Apollo program land on the moon? | none (out of repo scope) | none (zero candidate fragments) | explicit no-selection reason | not admitted; not qualified; workshop metadata only |
| W-PRM-024 | H. no-route | What is the molecular weight of caffeine? | none (out of repo scope) | none (zero candidate fragments) | explicit no-selection reason | not admitted; not qualified; workshop metadata only |
| W-PRM-025 | I. near-miss/rejection | What is awesome-copilot? | repo_meta_section | none (zero candidate route or workflow fragments) | explicit `repo_meta_section` rejection reason; repo-meta material observed but rejected | not admitted; not qualified; workshop metadata only |
| W-PRM-026 | I. near-miss/rejection | Explain how this repo is organized. | repo_meta_section | none (zero candidate route or workflow fragments) | explicit `repo_meta_section` rejection reason | not admitted; not qualified; workshop metadata only |

## 5. Derived-Material Implications

A future `WO-L0-DERIVED-WORKSHOP-01` packet (subject to its own
Codex authorization) should use exactly these eight item kinds for
the workshop variant:

- `skill`
- `instruction`
- `agent`
- `workflow_file`
- `hook`
- `plugin`
- `cookbook_entry`
- `repo_meta_section`

The workshop variant must NOT include `prompt` as an item kind
(because the repo has zero `*.prompt.md` files), and must NOT
include `vendor_pattern` as an item kind (because no vendor-guide
shape is present in this single-repo seed).

This is a planning observation only. It does NOT authorize
implementation of `WO-L0-DERIVED-WORKSHOP-01`. It does NOT
authorize the workshop variant to replace the existing seven-source
`ITEM_KIND_TO_DECLARED_KIND` mapping in
`harness/level0_manual_seed_materialization.py`. Any change to that
mapping requires its own packet.

## 6. Non-Claims

This workshop seed plan:

- Does NOT authorize implementation of any workshop scaffold.
- Does NOT authorize real indexing.
- Does NOT authorize real retrieval.
- Does NOT authorize ranking, scoring, similarity, or metric
  computation.
- Does NOT authorize source qualification.
- Does NOT authorize corpus admission.
- Does NOT authorize route selection.
- Does NOT select any architecture, vendor, library, index family,
  ANN backend, reranker, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Does NOT modify `ai-search/00-controller-checklist.md`.
- Does NOT modify any `harness/` file.
- Does NOT mutate `benchmark-fixtures/`.
- Does NOT modify any prior WO boundary doc.
- Does NOT modify the existing L0 item / prompt planning docs.
- Does NOT modify `ai-search/00-level0-source-candidate-inventory.md`.
- Does NOT close OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
- Does NOT duplicate RK-039.
- Does NOT claim any item slot, prompt slot, source-shape row,
  derived-material kind, or proposed Work Order is sufficient,
  necessary, superior, best, complete, production-ready,
  recommended, or selected.

All DC-020 through DC-067 boundary invariants carry forward.
WO-L0-WORKSHOP-01 does not amend or broaden DC-003 through DC-067.
Real-benchmark-ready remains NO.
