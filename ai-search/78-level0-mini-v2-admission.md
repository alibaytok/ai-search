# 78. Level 0 Mini-V2 Admission

## Goal

Admit a small Mini-V2 evaluation surface from raw candidate snapshot v1
after the admission review pack showed that 20 admitted + 5 holdout is
not realistic from the current 18 eligible candidates.

This packet admits 12 cases and creates a 3-case holdout. Expected fields
are human-authored gate-output semantics only. They are not copied from
parser observations.

## Inputs

Source artifacts:

- `harness/raw_candidate_pools/L0-WS-RAW-CANDIDATES-v1.raw_candidates.json`
- `harness/admission_review_packs/L0-WS-RAW-CANDIDATES-v1.admission_review.json`

Admission uses only candidates marked
`eligible_for_human_admission_review` in the review pack.

## Outputs

- `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json`
- `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2-HOLDOUT.intent.matrix.json`

Mini-V2 contains 12 admitted cases. Holdout contains 3 cases.

## Boundary

This packet does not run the autonomous loop against Mini-V2, does not
materialize parser changes, does not admit holdout into autonomous-loop
visibility, does not create corpus completeness claims, and does not
authorize benchmark, source, route, production, or downstream model/action
claims.

## Consequence

The next packet may run the existing runner/planner against Mini-V2 only.
The holdout file must remain outside autonomous-loop paths until a
separate human measurement packet authorizes reading it.
