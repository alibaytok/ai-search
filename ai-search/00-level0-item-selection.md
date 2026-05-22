# ai-search - Level 0B Manual Seed Item Selection (planning slots)

Document type: Level 0B planning artifact / review aid
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-ITEMS-01

## Authority

This file is a Level 0B planning artifact. It is NOT a project-authority
document and it does NOT authorize any execution. Canonical authority
remains with the controlling project documents:

- `ai-search/00-controller-checklist.md`
- `ai-search/00-open-questions.md`
- the active Work Order packet
- `ai-search/00-claude-task-ledger.md`

If this file ever conflicts with the canonical documents above, the
canonical documents win and this file must be corrected.

`ai-search/00-wo-constraints.md` (Constraints v1) is a compiled
reference used alongside this planning artifact. It is descriptive,
not project authority. If this file and Constraints v1 conflict, both
references must be reconciled against the canonical documents above.

## Scope and Boundary

WO-L0-ITEMS-01 created this file. WO-L0-ITEMS-01 is documentation-only.
This file does NOT authorize real benchmark execution, real or mock
adapter invocation, network calls, URL fetch / download / crawl /
browser automation, local file read or write, PDF text extraction,
source qualification, corpus admission, extraction, normalization,
candidate-fragment derivation, route or workflow promotion,
architecture / vendor / library / index family / ANN backend /
reranker / retrieval family / production-system selection, IDE /
Copilot / Waza / VS Code / LLM integration, Source Card or Route Card
creation, OQ closure, or duplication of RK-039. Real-benchmark-ready
remains NO. All authorization / readiness / selection booleans remain
literal False.

Every row in the table below is a planning slot at link / locator /
section-heading granularity. No row contains fetched content. No row
contains a verbatim copy of an external entry title, description, or
body. The `item_title_or_anchor` column records what KIND of item the
manual reviewer should select to fulfill the slot; the `item_locator`
column records the source-relative anchor or section the reviewer
should select from. The actual item titles will be filled in by the
manual reviewer at verification time and are explicitly NOT contained
in this planning table.

The seven sources referenced are defined in
`ai-search/00-level0-source-candidate-inventory.md`.

## Per-Source Slot Counts

- L0-SRC-001 (`github/awesome-copilot`): 12 slots.
- L0-SRC-002 (`Code-and-Sorts/awesome-copilot-agents`): 10 slots.
- L0-SRC-003 (`theneoai/awesome-skills`): 9 slots.
- L0-SRC-004 (PromptAdvance Claude Prompts - language-learning page): 9 slots.
- L0-SRC-005 (Gemini for Workspace Prompt Guide PDF): 9 slots.
- L0-SRC-006 (`actions/starter-workflows`): 11 slots.
- L0-SRC-007 (Wikipedia "Prompt engineering"): 5 slots.

Total: 65 slots. This total is bounded by WO-L0-ITEMS-01 and is NOT
claimed sufficient, necessary, or exhaustive.

## Item Selection Table

| item_id | source_id | item_kind | item_title_or_anchor | item_locator | intended_test_role | boundary_notes |
|---------|-----------|-----------|----------------------|--------------|--------------------|----------------|
| L0-ITEM-001 | L0-SRC-001 | prompt | Python unit-test prompt slot | L0-SRC-001 prompts/ subfolder | supports L0-PRM-004 clear single-intent unit-test prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-002 | L0-SRC-001 | prompt | code-explanation prompt slot | L0-SRC-001 prompts/ subfolder | supports L0-PRM-005 multi-intent test+explain prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-003 | L0-SRC-001 | prompt | refactor-suggestion prompt slot | L0-SRC-001 prompts/ subfolder | supports L0-PRM-008 ambiguous "make this better" prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-004 | L0-SRC-001 | prompt | comment-translation prompt slot | L0-SRC-001 prompts/ subfolder | supports L0-PRM-018 multi-source review+translate prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-005 | L0-SRC-001 | skill | code-review skill slot | L0-SRC-001 skills/ subfolder | supports L0-PRM-003 clear single-intent code-review prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-006 | L0-SRC-001 | skill | doc-generation skill slot | L0-SRC-001 skills/ subfolder | supports L0-PRM-009 ambiguous "help with my project" prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-007 | L0-SRC-001 | skill | linting skill slot | L0-SRC-001 skills/ subfolder | supports L0-PRM-010 ambiguous "improve the code" prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-008 | L0-SRC-001 | agent | reviewer-persona agent slot | L0-SRC-001 agents/ or chatmodes/ subfolder | supports L0-PRM-005 multi-intent prompt; agent-vs-route discipline | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-009 | L0-SRC-001 | agent | refactorer-persona agent slot | L0-SRC-001 agents/ or chatmodes/ subfolder | supports agent-shape rejection on near-miss prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-010 | L0-SRC-001 | agent | translator-persona agent slot | L0-SRC-001 agents/ or chatmodes/ subfolder | supports L0-PRM-018 cross-shape observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-011 | L0-SRC-001 | instruction | repository-style-guide instruction slot | L0-SRC-001 instructions/ subfolder | supports instruction-shape distinction from prompt-shape | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-012 | L0-SRC-001 | instruction | test-conventions instruction slot | L0-SRC-001 instructions/ subfolder | supports L0-PRM-001 cross-source observation discipline | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-013 | L0-SRC-002 | agent | testing-agent slot | L0-SRC-002 agents/ section | supports L0-PRM-005 multi-intent prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-014 | L0-SRC-002 | agent | deployment-agent slot | L0-SRC-002 agents/ section | supports L0-PRM-006 deploy+notify prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-015 | L0-SRC-002 | agent | documentation-agent slot | L0-SRC-002 agents/ section | supports L0-PRM-018 review+translate prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-016 | L0-SRC-002 | agent | notification-agent slot | L0-SRC-002 agents/ section | supports L0-PRM-006 second-intent observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-017 | L0-SRC-002 | instruction | agent-handoff instruction slot | L0-SRC-002 instructions/ section | supports instruction-shape rejection on workflow prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-018 | L0-SRC-002 | instruction | agent-prompt-format instruction slot | L0-SRC-002 instructions/ section | supports instruction-vs-prompt discipline | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-019 | L0-SRC-002 | instruction | agent-state instruction slot | L0-SRC-002 instructions/ section | supports L0-PRM-009 ambiguous-prompt observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-020 | L0-SRC-002 | prompt | agent-prompt slot A | L0-SRC-002 prompts/ section | supports L0-PRM-004 single-intent unit-test prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-021 | L0-SRC-002 | prompt | agent-prompt slot B | L0-SRC-002 prompts/ section | supports L0-PRM-011 prompt-search-shaped-but-workflow prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-022 | L0-SRC-002 | skill | mixed-index skill slot | L0-SRC-002 skills/ section | supports L0-PRM-003 single-intent skill observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-023 | L0-SRC-003 | skill | code-review skill slot | L0-SRC-003 readme skill list | supports L0-PRM-003 single-intent skill prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-024 | L0-SRC-003 | skill | summarization skill slot | L0-SRC-003 readme skill list | supports L0-PRM-009 ambiguous-prompt observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-025 | L0-SRC-003 | skill | translation skill slot | L0-SRC-003 readme skill list | supports L0-PRM-018 review+translate prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-026 | L0-SRC-003 | skill | search skill slot | L0-SRC-003 readme skill list | supports L0-PRM-010 ambiguous-prompt observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-027 | L0-SRC-003 | skill | classification skill slot | L0-SRC-003 readme skill list | supports L0-PRM-008 ambiguous-prompt observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-028 | L0-SRC-003 | skill | extraction skill slot | L0-SRC-003 readme skill list | supports skill-shape rejection on workflow prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-029 | L0-SRC-003 | skill | data-cleanup skill slot | L0-SRC-003 readme skill list | supports L0-PRM-007 multi-intent translate+spellcheck prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-030 | L0-SRC-003 | skill | format-conversion skill slot | L0-SRC-003 readme skill list | supports skill-shape rejection on encyclopedic prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-031 | L0-SRC-003 | skill | reporting skill slot | L0-SRC-003 readme skill list | supports L0-PRM-019 multi-source report+CI prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-032 | L0-SRC-004 | prompt | language-learning prompt slot A | L0-SRC-004 #language-learning section | supports L0-PRM-001 single-intent translate prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-033 | L0-SRC-004 | prompt | language-learning prompt slot B | L0-SRC-004 #language-learning section | supports L0-PRM-017 Spanish-vocabulary multi-source prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-034 | L0-SRC-004 | prompt | language-learning prompt slot C | L0-SRC-004 #language-learning section | supports L0-PRM-007 translate+spellcheck multi-intent prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-035 | L0-SRC-004 | prompt | language-learning prompt slot D | L0-SRC-004 #language-learning section | supports L0-PRM-018 review+translate multi-source prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-036 | L0-SRC-004 | prompt | language-learning prompt slot E | L0-SRC-004 #language-learning section | supports prompt-shape rejection on workflow prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-037 | L0-SRC-004 | prompt | language-learning prompt slot F | L0-SRC-004 #language-learning section | supports prompt-shape rejection on encyclopedic prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-038 | L0-SRC-004 | prompt | language-learning prompt slot G | L0-SRC-004 #language-learning section | supports L0-PRM-002 cross-source CI observation discipline | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-039 | L0-SRC-004 | prompt | language-learning prompt slot H | L0-SRC-004 #language-learning section | supports L0-PRM-019 Gemini-style cross-source prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-040 | L0-SRC-004 | prompt | language-learning prompt slot I | L0-SRC-004 #language-learning section | supports noisy-catalog bias detection | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-041 | L0-SRC-005 | vendor_prompt_pattern | role-and-task pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-019 vendor-style multi-source prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-042 | L0-SRC-005 | vendor_prompt_pattern | context-and-instruction pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-005 multi-intent prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-043 | L0-SRC-005 | vendor_prompt_pattern | iterate-and-refine pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-008 ambiguous-prompt observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-044 | L0-SRC-005 | vendor_prompt_pattern | document-summary pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-020 encyclopedic near-miss observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-045 | L0-SRC-005 | vendor_prompt_pattern | meeting-summary pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-019 standup-summary multi-source prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-046 | L0-SRC-005 | vendor_prompt_pattern | translation pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-001 single-intent translate prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-047 | L0-SRC-005 | vendor_prompt_pattern | data-extraction pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-007 multi-intent translate+spellcheck prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-048 | L0-SRC-005 | vendor_prompt_pattern | brainstorming pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-009 ambiguous-prompt observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-049 | L0-SRC-005 | vendor_prompt_pattern | drafting pattern slot | L0-SRC-005 PDF body section (slot) | supports L0-PRM-010 ambiguous-prompt observation | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-050 | L0-SRC-006 | workflow_file | Python CI starter slot | L0-SRC-006 ci/ subfolder | supports L0-PRM-002 single-intent CI prompt; L0-PRM-022 pytest workflow | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-051 | L0-SRC-006 | workflow_file | Node.js CI starter slot | L0-SRC-006 ci/ subfolder | supports L0-PRM-023 Node.js deployment workflow prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-052 | L0-SRC-006 | workflow_file | Docker CI starter slot | L0-SRC-006 ci/ subfolder | supports L0-PRM-011 prompt-search-shaped-but-workflow Docker prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-053 | L0-SRC-006 | workflow_file | generic test-on-PR CI starter slot | L0-SRC-006 ci/ subfolder | supports L0-PRM-022 pytest-on-PR workflow prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-054 | L0-SRC-006 | workflow_file | static-site deployment starter slot | L0-SRC-006 deployments/ subfolder | supports L0-PRM-012 prompt-search-shaped-but-workflow GH Pages prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-055 | L0-SRC-006 | workflow_file | Azure deployment starter slot | L0-SRC-006 deployments/ subfolder | supports L0-PRM-023 Azure deployment workflow prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-056 | L0-SRC-006 | workflow_file | container-registry deployment starter slot | L0-SRC-006 deployments/ subfolder | supports L0-PRM-006 deploy+notify multi-intent prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-057 | L0-SRC-006 | workflow_file | CodeQL code-scanning starter slot | L0-SRC-006 code-scanning/ subfolder | supports workflow-shape distinction from prompt-shape | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-058 | L0-SRC-006 | workflow_file | dependency-scanning starter slot | L0-SRC-006 code-scanning/ subfolder | supports L0-PRM-013 no-route boundary (out-of-scope adjacency) | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-059 | L0-SRC-006 | workflow_file | scheduled-cleanup automation starter slot | L0-SRC-006 automation/ subfolder | supports L0-PRM-017 reminders multi-source prompt | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-060 | L0-SRC-006 | workflow_file | labeler automation starter slot | L0-SRC-006 automation/ subfolder | supports workflow-shape ambiguity vs agent-shape | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-061 | L0-SRC-007 | encyclopedic_section | Wikipedia article lead section slot | L0-SRC-007 article lead | supports L0-PRM-020 "what is prompt engineering" near-miss rejection | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-062 | L0-SRC-007 | encyclopedic_section | Wikipedia "History" section slot | L0-SRC-007 #History | supports L0-PRM-021 history-of-prompt-design near-miss rejection | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-063 | L0-SRC-007 | encyclopedic_section | Wikipedia "Techniques" section slot | L0-SRC-007 #Techniques (or analogous) | supports near-miss rejection on technique-oriented prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-064 | L0-SRC-007 | encyclopedic_section | Wikipedia "Applications" section slot | L0-SRC-007 #Applications (or analogous) | supports near-miss rejection on application-oriented prompts | not admitted; not qualified; link-level/manual-seed only |
| L0-ITEM-065 | L0-SRC-007 | encyclopedic_section | Wikipedia "Limitations" section slot | L0-SRC-007 #Limitations (or analogous) | supports near-miss rejection on limitation-oriented prompts | not admitted; not qualified; link-level/manual-seed only |

## Non-Claim Constraints

WO-L0-ITEMS-01 does NOT claim any of the 65 slots above is sufficient,
necessary, superior, best, complete, production-ready, recommended,
or selected. The per-source slot counts and item-kind distributions
are bounded by this Work Order and are NOT claimed exhaustive. No
slot above admits, qualifies, normalizes, extracts, or promotes any
source material. No slot above authorizes invocation of any prior-WO
public function. No slot above flips any authorization / readiness /
selection boolean.

Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031, OQ-035,
OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
RK-039 remains active and is not duplicated. All Constraints v1
provisions apply.

The actual item titles, full URLs, and verified anchors are to be
populated by the manual reviewer at verification time; they are NOT
contained in this planning table by design.
