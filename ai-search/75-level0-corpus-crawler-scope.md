# 75. Level 0 Corpus Crawler Scope

## Goal

Define and implement the first local-only raw prompt candidate crawler
for Level 0 workshop intent-gate coverage expansion. The crawler is a
candidate generator only. It does not admit corpus cases, generate
expected fields, run the parser, evaluate quality, or authorize any
parser-core change.

The crawler supports the clarified TextToAIModel goal: raw user text
must pass through a deterministic, bounded, auditable intent gate before
any downstream AI model, agent, workflow, or skill action is allowed.
The crawler expands prompt-shape observation for that gate; it is not
training-data infrastructure.

## Scope

Allowed:

- Add a deterministic stdlib-only crawler module under `harness/`.
- Add unit tests for extraction, metadata shape, determinism, forbidden
  source rejection, and parser/network isolation.
- Read explicitly provided local ASCII files.
- Extract raw candidate prompts from markdown-like local documents and
  existing local intent matrix prompt text.
- Emit an in-memory raw candidate report.

Forbidden:

- Network, web, browser, GitHub API, subprocess, socket, or third-party
  dependency use.
- Parser invocation or import of FRAME-A/B/C/D parser layers.
- Corpus admission.
- Holdout creation.
- Mini-V2 matrix creation.
- Expected-field generation.
- Copying parser output into expected fields.
- Parser-core materialization or patch-kind expansion.
- Overlay store, confidence decay, benchmark, source admission, route
  creation, or production-readiness claims.

## Raw Candidate Report

Every raw candidate must be ASCII-only and carry bounded metadata:

- deterministic `candidate_id`
- bounded `source_kind`
- local `source_path`
- `source_line`
- bounded `extraction_method`
- `source_sha256`
- `prompt_text_original`
- `prompt_text_normalized`
- `language_tag`
- `admission_status`
- `admission_reason`

All crawler-emitted candidates start with `admission_status="raw"` and
`admission_reason="pending_human_review"`.

The raw candidate report is not a corpus contract. It is input for a
future human-authored admission packet.

## First-Run Boundaries

The first crawler may be pointed at local project documents such as:

- `ai-search/00-level0-awesome-copilot-workshop-seed.md`
- `ai-search/00-level0-prompt-set.md`
- `ai-search/00-level0-item-selection.md`
- `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V1.intent.matrix.json`

The crawler has a hard cap of 500 raw candidates per report. If local
sources produce more than 500 candidates, the extraction heuristic is
too broad and must be tightened before corpus admission work begins.

## Admission Boundary

Admission is a separate future packet. The intended first admission
shape remains:

- 20 human-authored admitted Mini-V2 cases
- 5 human-authored holdout cases

Expected fields must be authored from gate-output semantics only:
category, candidate kinds, ambiguity, normalized intent, candidate
surface, and rejection surface. They must not describe downstream
action semantics.

## Non-Claims

This crawler is not a benchmark, training corpus, model dataset,
production input pipeline, source qualifier, route validator, or
automatic corpus admission system. It is a deterministic raw candidate
generator for later human review.
