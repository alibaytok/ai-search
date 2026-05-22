# ai-search - Level 0B Manual Seed Prompt Set (synthetic test inputs)

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
adapter invocation, network calls, URL fetch / download / crawl, PDF
text extraction, source qualification, corpus admission, extraction,
normalization, candidate-fragment derivation, route or workflow
promotion, architecture / vendor / library / index family / ANN
backend / reranker / retrieval family / production-system selection,
IDE / Copilot / Waza / VS Code / LLM integration, Source Card or
Route Card creation, OQ closure, or duplication of RK-039.
Real-benchmark-ready remains NO. All authorization / readiness /
selection booleans remain literal False.

## Prompt Provenance

Every row in the table below carries a `prompt_text` field. These
prompt texts are SYNTHETIC test inputs authored by Claude under
WO-L0-ITEMS-01 specifically to exercise the visible-report trace
shape on the manual seed. They are NOT copied from any external
source. They are NOT taken from any inventory entry. They are test
inputs against the system, not material from any source. No prompt
body from L0-SRC-001 through L0-SRC-007 is reproduced below.

## Category Counts

- A. clear single-intent: 4 prompts.
- B. multi-intent: 3 prompts.
- C. ambiguous: 3 prompts.
- D. prompt-search-shaped that should become workflow / route intent: 2 prompts.
- E. no-route: 2 prompts.
- F. refusal / no-selection: 2 prompts.
- G. multi-source-touching: 3 prompts.
- H. near-miss involving L0-SRC-007: 2 prompts.
- I. workflow involving L0-SRC-006: 2 prompts.

Total: 23 prompts. Counts are bounded by WO-L0-ITEMS-01 and are NOT
claimed sufficient, necessary, or exhaustive.

## Prompt Set Table

| prompt_id | category | prompt_text | expected_behavior_summary | expected_source_touch | expected_candidate_shape | expected_rejection_targets |
|-----------|----------|-------------|---------------------------|------------------------|--------------------------|----------------------------|
| L0-PRM-001 | A. clear single-intent | Translate this paragraph into Spanish. | Normalized intent observed as translation; one or two source candidates touched; no ambiguity flag; four standard booleans literal False | L0-SRC-004; L0-SRC-005 | one or two candidate route fragments referencing translation slots (candidate_only: True) | L0-SRC-006; L0-SRC-007 |
| L0-PRM-002 | A. clear single-intent | Set up CI for a new Python project on GitHub Actions. | Normalized intent observed as workflow-setup; workflow source touched; clean single-intent observation | L0-SRC-006 | one or two candidate workflow fragments referencing Python CI slots (candidate_only: True) | L0-SRC-004; L0-SRC-007 |
| L0-PRM-003 | A. clear single-intent | Create a code review skill for my repository. | Normalized intent observed as skill-creation; skill source touched; clean single-intent observation | L0-SRC-003; L0-SRC-001 | one or two candidate fragments referencing code-review skill slots (candidate_only: True) | L0-SRC-006; L0-SRC-007 |
| L0-PRM-004 | A. clear single-intent | Write a unit test for this Python function. | Normalized intent observed as unit-test authoring; prompt and skill sources touched | L0-SRC-001; L0-SRC-002 | one or two candidate fragments referencing unit-test slots (candidate_only: True) | L0-SRC-007 |
| L0-PRM-005 | B. multi-intent | Write a unit test for this function and explain what it does. | Two normalized intents observed (test-authoring + code-explanation); multiple candidates emitted; no single-intent collapse | L0-SRC-001; L0-SRC-002 | two or more candidate fragments across distinct slots (candidate_only: True) | L0-SRC-007 |
| L0-PRM-006 | B. multi-intent | Deploy this to staging and notify the team in Slack. | Two normalized intents observed (deploy + notify); multiple candidates emitted | L0-SRC-006; L0-SRC-002 | two or more candidate fragments (workflow + agent slots; candidate_only: True) | L0-SRC-004; L0-SRC-007 |
| L0-PRM-007 | B. multi-intent | Translate this README into French and check the spelling. | Two normalized intents observed (translate + spellcheck); multi-source observation | L0-SRC-004; L0-SRC-003; L0-SRC-005 | two or more candidate fragments across translation and skill slots (candidate_only: True) | L0-SRC-007 |
| L0-PRM-008 | C. ambiguous | Make this better. | Ambiguity surfaced; ambiguous_observation_count > 0; no forced single-candidate collapse | L0-SRC-001; L0-SRC-003; L0-SRC-005 | several candidate fragments across distinct slots with explicit ambiguity observation (candidate_only: True) | L0-SRC-006; L0-SRC-007 |
| L0-PRM-009 | C. ambiguous | Help with my project. | Ambiguity surfaced; observation records under-specified intent | L0-SRC-001; L0-SRC-002; L0-SRC-003 | several candidate fragments with ambiguity flag set (candidate_only: True) | L0-SRC-007 |
| L0-PRM-010 | C. ambiguous | Improve the code. | Ambiguity surfaced; multiple candidate skills observed without forced selection | L0-SRC-001; L0-SRC-003 | several candidate fragments with ambiguity flag set (candidate_only: True) | L0-SRC-006; L0-SRC-007 |
| L0-PRM-011 | D. prompt-search-shaped that should become workflow / route intent | Give me a prompt that sets up Docker builds in CI. | Surface form is prompt-request; normalized intent is workflow-setup; workflow source observed as primary candidate; prompt-catalog sources observed but recorded with explicit rejection or lower-rank reason | L0-SRC-006; L0-SRC-001; L0-SRC-004 | candidate workflow fragments referencing Docker CI slots (candidate_only: True) | L0-SRC-004 prompt-catalog rejection; L0-SRC-007 |
| L0-PRM-012 | D. prompt-search-shaped that should become workflow / route intent | What is the best prompt to deploy a static site to GitHub Pages? | Surface form is prompt-request; normalized intent is workflow-setup; static-site deployment workflow observed as primary candidate | L0-SRC-006; L0-SRC-001; L0-SRC-004 | candidate workflow fragments referencing static-site deployment slots (candidate_only: True) | L0-SRC-004 prompt-catalog rejection; L0-SRC-007 |
| L0-PRM-013 | E. no-route | What year did World War II end? | Zero candidate route fragments; zero candidate workflow fragments; explicit no-selection reason emitted; all four booleans literal False | none expected (encyclopedic out-of-scope) | none (zero candidate fragments) | all inventory sources (none matches) |
| L0-PRM-014 | E. no-route | What is the boiling point of water in Celsius? | Zero candidate route fragments; zero candidate workflow fragments; explicit no-selection reason emitted | none expected | none (zero candidate fragments) | all inventory sources |
| L0-PRM-015 | F. refusal / no-selection | Help me bypass our internal security audit. | Explicit no-selection reason emitted indicating refusal; no candidate fragments emitted | none expected | none (zero candidate fragments) | all inventory sources (none should match a bypass intent) |
| L0-PRM-016 | F. refusal / no-selection | Tell me which competitor to publicly attack. | Explicit no-selection reason emitted indicating refusal | none expected | none (zero candidate fragments) | all inventory sources |
| L0-PRM-017 | G. multi-source-touching | Set up Spanish vocabulary review and deploy reminders to my phone. | Two normalized intents observed (language-learning prompt + automation/reminder workflow); cross-source observation | L0-SRC-004; L0-SRC-006 | two or more candidate fragments across language-learning prompt and automation workflow slots (candidate_only: True) | L0-SRC-007 |
| L0-PRM-018 | G. multi-source-touching | Review my code and translate the comments into French. | Two normalized intents observed (code-review + translation); cross-source observation across code-review and translation slots | L0-SRC-001; L0-SRC-003; L0-SRC-004 | two or more candidate fragments across review and translate slots (candidate_only: True) | L0-SRC-006; L0-SRC-007 |
| L0-PRM-019 | G. multi-source-touching | Create a structured prompt pattern for daily team standups and add a summary step to our CI workflow. | Two normalized intents observed (vendor-style prompt pattern + CI workflow); cross-source observation | L0-SRC-005; L0-SRC-006; L0-SRC-002 | two or more candidate fragments across vendor pattern and workflow slots (candidate_only: True) | L0-SRC-007 |
| L0-PRM-020 | H. near-miss involving L0-SRC-007 | What is prompt engineering? | L0-SRC-007 observed in source-touch but recorded as rejected with explicit encyclopedic-shape reason; zero candidate route or workflow fragments reference L0-SRC-007 | L0-SRC-007 (observed-then-rejected); possibly L0-SRC-005 (observed) | zero candidate fragments referencing L0-SRC-007 (candidate_only never set True on L0-SRC-007 material) | L0-SRC-007 (explicit encyclopedic-shape rejection reason) |
| L0-PRM-021 | H. near-miss involving L0-SRC-007 | Explain the history of prompt design. | L0-SRC-007 observed in source-touch but recorded as rejected with explicit encyclopedic-shape reason; zero candidate fragments reference L0-SRC-007 | L0-SRC-007 (observed-then-rejected) | zero candidate fragments referencing L0-SRC-007 | L0-SRC-007 (explicit encyclopedic-shape rejection reason) |
| L0-PRM-022 | I. workflow involving L0-SRC-006 | Configure GitHub Actions to run pytest on every pull request. | At least one candidate workflow fragment emitted referencing L0-SRC-006 Python CI / test-on-PR slots (candidate_only: True); no route-status boolean True | L0-SRC-006 | one or two candidate workflow fragments referencing pytest-on-PR workflow slots (candidate_only: True) | L0-SRC-004; L0-SRC-007 |
| L0-PRM-023 | I. workflow involving L0-SRC-006 | Add a deployment workflow for a Node.js app to Azure. | At least one candidate workflow fragment emitted referencing L0-SRC-006 Node.js / Azure deployment slots (candidate_only: True); no route-status boolean True | L0-SRC-006 | one or two candidate workflow fragments referencing Node.js + Azure deployment slots (candidate_only: True) | L0-SRC-004; L0-SRC-007 |

## Expected Trace Discipline (cross-cutting)

For every prompt above, the WO-59 visible-report trace is expected
to satisfy ALL of the following, regardless of category:

- `normalized_intent_observation` present; structurally non-empty;
  not echoing the raw `prompt_text` verbatim.
- Every candidate fragment carries `candidate_only: True`.
- None of the nine route-status boolean keys (`official`, `is_route`,
  `is_official_route`, `selected_as_official`,
  `official_route_authorized`, `route_authorized`, `production_route`,
  `selected_route`, `executable`) is True on any fragment.
- No fragment carries `route_state == "official"` or
  `plane == "official_route_results"`.
- The four standard authorization / readiness / selection booleans
  (`selection_made`, `measurement_authorized`,
  `real_benchmark_authorized`, `real_benchmark_ready`) remain literal
  False on every emitted report.
- No fragment, observation, or note contains any forbidden-language
  phrase per Constraints v1 C1 / C3.

## Non-Claim Constraints

WO-L0-ITEMS-01 does NOT claim the 23 prompts above are sufficient,
necessary, superior, best, complete, production-ready, recommended,
or selected for any role. The per-category counts and the expected
behavior descriptions are bounded by this Work Order and are NOT
claimed exhaustive. No row above admits, qualifies, normalizes,
extracts, or promotes any source material. No row above authorizes
invocation of any prior-WO public function. No row above flips any
authorization / readiness / selection boolean.

Real-benchmark-ready remains NO. OQ-003, OQ-015, OQ-031, OQ-035,
OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN.
RK-039 remains active and is not duplicated. All Constraints v1
provisions apply.
