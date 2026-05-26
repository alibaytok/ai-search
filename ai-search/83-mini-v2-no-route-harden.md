# 83. Mini-V2 No-Route Harden

## Goal

Close the Mini-V2 `out_of_scope_underdetect` bucket identified in
`81-mini-v2-decision-report.md`.

This packet adds bounded FRAME-B out-of-scope canonicals for three admitted
Mini-V2 prompts that should not route to downstream code generation,
instruction generation, or cookbook-style artifact creation.

## Scope

Parser source touched:

- `harness/level0_workshop_signal_evidence.py`

Family touched:

- `out_of_scope.general_world`

Canonical additions:

- `unit test for this`
- `what is prompt engineering`

No new family was added. FRAME-C, FRAME-D, matrix files, holdout, crawler,
admission review pack, materializer modules, and quality-loop modules were not
changed.

## Source Decision

Source report:

- `ai-search/81-mini-v2-decision-report.md`

Affected cases:

- QV2-004
- QV2-005
- QV2-012

These were over-routed as skill, instruction, or cookbook-shaped intents. The
intended gate behavior is no-route because the prompts ask for downstream code
generation or general knowledge rather than a bounded workshop artifact.

## Materialization Evidence

The FRAME-B overlay candidate was run against Mini-V2 admitted before source
materialization.

Candidate result:

- decision: `accepted`
- reason: `accepted_strict_improvement`
- improved cases: `["QV2-004", "QV2-005", "QV2-012"]`
- regressed cases: `[]`
- candidate Mini-V2 result: 9 passing, 3 failing

The accepted bundle was materialized with both parser-core gates set:

- `materialization_authorized=True`
- `human_review_gate=True`

## Regression Controls

Negative tests assert that the new out-of-scope terms do not fire for adjacent
workshop-shaped prompts:

- workflow prompt with unit-test vocabulary
- skill prompt with unit-test vocabulary
- skill prompt with prompt-engineering vocabulary
- instruction prompt with prompt-engineering vocabulary

Mini-V1 remains closed:

- 35 passing
- 0 failing

Mini-V2 admitted after this packet:

- 12 cases
- 9 passing
- 3 failing
- 2 planner candidates

Remaining failure buckets:

- `frame_c_synthesis_rule_gap`: 2 cases
- `frame_c_ambiguity_misreport`: 1 case

Updated run artifact:

- `harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v3.report.json`

## Boundary

This packet does not claim parser completeness, benchmark readiness,
production readiness, route validation, source qualification, corpus
completeness, downstream model/action safety, or clarification-surface
readiness.

The holdout file remains isolated.
