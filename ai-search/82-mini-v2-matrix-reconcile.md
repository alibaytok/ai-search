# 82. Mini-V2 Matrix Reconcile

## Goal

Materialize the narrow Mini-V2 matrix reconciliation identified in
`81-mini-v2-decision-report.md` for QV2-009.

This packet updates expected surface labels only. It does not edit parser core,
read holdout, invoke parser-core materializers, add architecture, or authorize
downstream action.

## Source Decision

Source report:

- `ai-search/81-mini-v2-decision-report.md`

Affected case:

- QV2-009

Reason:

- The observed and expected route decision already agreed on no-route.
- Category, kind, ambiguity, and normalized intent already matched.
- Only `candidate_surface_expected` and `rejection_surface_expected` differed.

## Materialized Delta

Matrix:

- `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json`

Delta:

```json
{
  "patch_kind": "matrix_expected_field_update",
  "case_id": "QV2-009",
  "expected_updates": {
    "candidate_surface_expected": "candidate fragment of declared shape",
    "rejection_surface_expected": "no_forced_selection"
  }
}
```

The existing matrix-delta materializer accepted the candidate with:

- decision: `accepted`
- reason: `accepted_strict_improvement`
- improved cases: `["QV2-009"]`
- regressed cases: `[]`

## Result

Mini-V2 admitted after materialization:

- 12 cases
- 6 passing
- 6 failing
- 3 planner candidates

Remaining failure buckets:

- `out_of_scope_underdetect`: 3 cases
- `frame_c_synthesis_rule_gap`: 2 cases
- `frame_c_ambiguity_misreport`: 1 case
- `expected_field_drift`: 0 cases

Updated run artifact:

- `harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v2.report.json`

## Boundary

This is matrix reconciliation only. It does not claim parser completeness,
benchmark readiness, production readiness, route validation, source
qualification, corpus completeness, or downstream model/action safety.

The holdout file remains isolated.
