# 84. Mini-V2 FRAME-C Synthesis

## Goal

Close the Mini-V2 `frame_c_synthesis_rule_gap` bucket identified in
`81-mini-v2-decision-report.md` without editing matrices, FRAME-B, holdout, or
autonomous-loop machinery.

## Scope

This packet changes only FRAME-C synthesis behavior in
`harness/level0_workshop_canonical_intent_frame.py`.

Two bounded rules were added:

- A deploy secondary action can co-fire `workflow_file` only when the prompt is
  already on an agent/persona surface, preserving QV2-002 without widening
  release-note skill prompts into workflow ambiguity.
- A `prompt_collection_request` combined with explicit CI/workflow evidence is
  treated as an instruction/workflow ambiguity rather than a cookbook/workflow
  ambiguity, preserving QV2-011 while leaving prompt-only collection requests as
  cookbook-shaped.

## Cases Closed

| Case | Prior observed | Intended result |
|---|---|---|
| QV2-002 | D with `agent` only | D with `agent`, `workflow_file` |
| QV2-011 | F with `workflow_file`, `cookbook_entry` | E with `workflow_file`, `instruction` |

## Regression Controls

The test packet pins adjacent shapes:

- release-note skill prompts stay `C / skill`
- release-process instruction prompts stay `E / instruction`
- prompt-collection requests without CI/workflow evidence stay cookbook-shaped
- Mini-V1 remains 35/35
- Mini-V2 admitted moves to 11/12

## Run Artifact

The current proposal-only run snapshot is:

- `harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v4.report.json`

It records:

- Mini-V2 admitted: 11 passing, 1 failing
- `frame_c_synthesis_rule_gap`: 0
- remaining failure: one `frame_c_ambiguity_misreport` case

## Non-Claims

This packet does not authorize downstream model/action execution,
clarification UI, route creation, source qualification, benchmark claims,
holdout measurement, corpus expansion, overlay storage, or confidence decay.
