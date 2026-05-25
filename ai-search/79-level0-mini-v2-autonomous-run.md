# 79. Level 0 Mini-V2 Autonomous Run

## Goal

Run the existing Level 0 workshop runner, feedback planner, and candidate
case-review reporter against the admitted Mini-V2 matrix as a proposal-only
snapshot.

This packet does not read the Mini-V2 holdout file, does not materialize any
candidate, does not write parser core, does not write matrix files, and does
not authorize corpus admission or downstream action.

## Input

Admitted matrix:

- `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json`

The holdout matrix remains isolated and is not an input to this packet.

## Output

Run report:

- `harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v1.report.json`

The report records:

- Mini-V2 admitted matrix SHA-256
- parser-core SHA-256 values before the run
- runner summary and case results
- feedback report
- planner candidates
- candidate case-review summaries
- proposal bundles with materialization and variant execution flags set to
  false

## Result

Mini-V2 admitted currently reports:

- 12 cases
- 5 passing
- 7 failing
- 4 planner candidates

Failure buckets:

- `out_of_scope_underdetect`: 3 cases
- `frame_c_synthesis_rule_gap`: 2 cases
- `frame_c_ambiguity_misreport`: 1 case
- `expected_field_drift`: 1 case

These are proposal inputs only. Any follow-up correction, matrix edit, parser
change, or human-review decision is a separate packet.

## Boundary

The report is not a readiness claim, route claim, source claim, corpus
admission, or downstream model/action claim. It is a deterministic review
artifact over the admitted Mini-V2 matrix only.
