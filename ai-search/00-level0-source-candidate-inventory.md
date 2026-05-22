# ai-search - Level 0 Source Candidate Inventory

Document type: Non-authoritative working inventory
Owner: Codex (controller)
Purpose: Track manually identified external source candidates for a
future Level 0 manual-seed test. This file records link-level source
observations only.
Status: Working inventory; not a Work Order; not a Decision; not corpus
admission; not source qualification; not benchmark evidence.

## Authority

This file is descriptive only. It does not authorize download, fetch,
crawl, extraction, normalization, source qualification, corpus admission,
candidate route derivation, index construction, benchmark execution, or
architecture selection.

Canonical authority remains with:

- `ai-search/00-controller-checklist.md`
- `ai-search/00-open-questions.md`
- the active Work Order packet, when one exists
- `ai-search/00-claude-task-ledger.md`

If this file conflicts with canonical project documents, canonical wins
and this file must be corrected.

## Level 0 Boundary

Level 0 manual-seed observation means:

- manually identified candidate links only;
- no content download by this file;
- no source qualification;
- no corpus admission;
- no extraction or normalization;
- no route or workflow object creation;
- no claim that any source is sufficient, necessary, superior, best,
  complete, production-ready, recommended, selected, or exhaustive.

## Candidate Sources

| ID | URL | Observed kind | Why it is useful for Level 0 | Boundary notes |
| --- | --- | --- | --- | --- |
| L0-SRC-001 | https://github.com/github/awesome-copilot | mixed customization collection | Large collection of agents, instructions, skills, hooks, workflows, and plugins; useful for testing whether ai-search can observe mixed customization material without treating it as route objects. | Link-level candidate only; not admitted; not qualified. |
| L0-SRC-002 | https://github.com/Code-and-Sorts/awesome-copilot-agents | mixed prompt / agent / instruction / skill index | Curated list explicitly covering `.instructions.md`, `.prompt.md`, `.agent.md`, and `SKILL.md` materials; useful for route/workflow candidate-boundary tests. | Link-level candidate only; not admitted; not qualified. |
| L0-SRC-003 | https://github.com/theneoai/awesome-skills | skill collection | High-volume skill collection with many persona/methodology-style skills; useful for testing noisy skill catalogs and ensuring persona prompts are not promoted to routes. | Link-level candidate only; not admitted; not qualified. |
| L0-SRC-004 | https://promptadvance.club/claude-prompts#language-learning | prompt collection | Claude prompt catalog with learning/language-learning category anchors; useful noisy prompt-catalog seed for checking prompt-vs-route separation. | User-supplied link; link-level candidate only; not admitted; not qualified. |
| L0-SRC-005 | https://services.google.com/fh/files/misc/gemini_for_workspace_prompt_guide_october_2024_digital_final.pdf | document collection | Structured Gemini for Workspace prompting guide PDF; useful as a higher-structure prompt/workflow guide seed distinct from noisy prompt catalogs. | User-supplied link; link-level candidate only; not admitted; not qualified. |
| L0-SRC-006 | https://github.com/actions/starter-workflows | workflow / playbook collection | GitHub Actions starter workflow repository with YAML workflow templates and workflow metadata; useful for testing workflow-shaped material distinct from prompt, skill, and guide sources. | Link-level candidate only; not admitted; not qualified; GitHub ownership does not imply authority or route status. |
| L0-SRC-007 | https://en.wikipedia.org/wiki/Prompt_engineering | negative / near-miss document | Encyclopedic prompt-engineering article; useful as topically adjacent material that should not produce route or workflow candidates by topical proximity alone. | Link-level candidate only; not admitted; not qualified; encyclopedic relevance does not imply route/workflow suitability. |

## Current Review Notes

- `L0-SRC-004` should stress-test noisy prompt catalog handling.
- `L0-SRC-005` should stress-test structured guide handling.
- `L0-SRC-006` should stress-test workflow-shaped source handling without
  route-status promotion.
- `L0-SRC-007` should stress-test near-miss rejection behavior.
- Neither source should be treated as a route, workflow, source card,
  benchmark fixture, validation evidence, or production artifact.
- The next Work Order, if any, must decide whether these links remain
  manual metadata only or whether a separately authorized acquisition
  step is allowed.
