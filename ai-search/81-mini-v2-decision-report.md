# 81. Mini-V2 Decision Report

## Goal

Classify the 7 failing Mini-V2 admitted cases into bounded follow-up buckets
before authoring any fix packet.

This is a review-only decision report. It does not edit parser code, edit
matrix files, read holdout, invoke materializers, add architecture, or
authorize downstream product surfaces.

## Provenance

Source report:

- `harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v1.report.json`

Source matrix:

- `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json`

Observed source report state:

- 12 admitted cases
- 5 passing
- 7 failing
- 4 planner candidates

Holdout is not part of this report.

## Decision Buckets

The buckets are keyed by required follow-up shape, not by failure class.

| Bucket | Meaning |
|---|---|
| `matrix_reconcile` | Matrix expected-field edit only; no parser change |
| `parser_frame_b_canonical` | FRAME-B canonical, exclusion, alias, or table coverage change |
| `parser_frame_c_synthesis` | FRAME-C synthesis or category rule change |
| `clarification_surface_reserved` | Requires downstream clarification surface; not closable inside current gate |
| `defer` | Known issue, no follow-up authorized in this epoch |

## Planner Candidate Map

| Candidate | Failure class | Cases | Planner next packet | Decision bucket |
|---|---|---:|---|---|
| UPG-001 | `out_of_scope_underdetect` | 3 | `NO-ROUTE-HARDEN` | `parser_frame_b_canonical` |
| UPG-002 | `frame_c_synthesis_rule_gap` | 2 | `FRAME-C-HARDEN` | `parser_frame_c_synthesis` |
| UPG-003 | `expected_field_drift` | 1 | `MATRIX-RECONCILE` | `matrix_reconcile` |
| UPG-004 | `frame_c_ambiguity_misreport` | 1 | `CLARIFICATION-DESIGN` | `clarification_surface_reserved` |

The candidate order above reflects the committed Mini-V2 run report.

## Case Decisions

| Case | Failure class | Observed | Expected | Decision bucket | Rationale | Suggested packet |
|---|---|---|---|---|---|---|
| QV2-002 | `frame_c_synthesis_rule_gap` | `D. agent/persona confusion`; kinds `agent`; ambiguity `true` | `D. agent/persona confusion`; kinds `agent`, `workflow_file`; ambiguity `true` | `parser_frame_c_synthesis` | Category and ambiguity already match. The missing surface is `workflow_file`, caused by synthesis not preserving deploy/workflow evidence alongside persona evidence. | Future `MINI-V2-FRAME-C-SYNTHESIS-01`, after cheaper buckets are decided |
| QV2-004 | `out_of_scope_underdetect` | `C. skill intent`; kinds `skill`; ambiguity `false` | `H. no-route`; kinds `none`; ambiguity `false` | `parser_frame_b_canonical` | Direct unit-test writing is downstream code generation, not a bounded workshop artifact. The current gate over-routes it as a skill. | Future `MINI-V2-NO-ROUTE-HARDEN-01` |
| QV2-005 | `out_of_scope_underdetect` | `G. ambiguous`; kinds `skill`, `instruction`; ambiguity `true` | `H. no-route`; kinds `none`; ambiguity `false` | `parser_frame_b_canonical` | Direct code-writing plus explanation is downstream action. The gate should reject the action request rather than offer workshop artifact choices. | Future `MINI-V2-NO-ROUTE-HARDEN-01` |
| QV2-006 | `frame_c_ambiguity_misreport` | `B. workflow intent`; kinds `workflow_file`; ambiguity `false` | `G. ambiguous`; kinds `skill`, `instruction`, `workflow_file`; ambiguity `true` | `clarification_surface_reserved` | This is the clearest downstream clarification case: deploy/notify wording exposes multiple possible surfaces, and forcing workflow loses user choice. | Future downstream clarification-surface authorization, not current gate cleanup |
| QV2-009 | `expected_field_drift` | `H. no-route`; kinds `none`; ambiguity `false`; candidate surface `candidate fragment of declared shape`; rejection `no_forced_selection` | `H. no-route`; kinds `none`; ambiguity `false`; candidate surface `no candidate surface expected`; rejection `prompt_out_of_repo_scope` | `matrix_reconcile` | The route decision already matches no-route. Only surface labels differ. This is the narrowest matrix-only follow-up. | `MINI-V2-MATRIX-RECONCILE-01` |
| QV2-011 | `frame_c_synthesis_rule_gap` | `F. prompt-search-shaped but workflow-intent`; kinds `workflow_file`, `cookbook_entry`; ambiguity `true` | `E. instruction confusion`; kinds `workflow_file`, `instruction`; ambiguity `true` | `parser_frame_c_synthesis` | Ambiguity already matches, but prompt-pattern authoring is being synthesized as cookbook rather than instruction. This is FRAME-C shape/category behavior. | Future `MINI-V2-FRAME-C-SYNTHESIS-01`, after cheaper buckets are decided |
| QV2-012 | `out_of_scope_underdetect` | `A. clear single-intent`; kinds `cookbook_entry`; ambiguity `false` | `H. no-route`; kinds `none`; ambiguity `false` | `parser_frame_b_canonical` | Conceptual prompt-engineering history is knowledge-seeking, not a cookbook artifact. Current cookbook evidence over-routes. | Future `MINI-V2-NO-ROUTE-HARDEN-01` |

## Bucket Summary

| Bucket | Cases | Count | Follow-up status |
|---|---|---:|---|
| `matrix_reconcile` | QV2-009 | 1 | Smallest safe follow-up if one technical packet is chosen |
| `parser_frame_b_canonical` | QV2-004, QV2-005, QV2-012 | 3 | Parser-core packet; requires human-review gate and adjacent negative tests |
| `parser_frame_c_synthesis` | QV2-002, QV2-011 | 2 | Larger parser-core packet; defer until cheaper buckets are settled |
| `clarification_surface_reserved` | QV2-006 | 1 | New downstream product surface; not authorized by this report |
| `defer` | none | 0 | No case is being hidden; every failure has a bucket |

## Sequencing

If another technical packet is authorized, the narrowest sequence is:

1. `MINI-V2-MATRIX-RECONCILE-01`
   - QV2-009 only
   - matrix expected-field update
   - no parser-core edit
   - holdout untouched
2. `MINI-V2-NO-ROUTE-HARDEN-01`
   - QV2-004, QV2-005, QV2-012
   - parser-core gated packet
   - requires negative coverage for legitimate skill, instruction, and cookbook prompts
3. `MINI-V2-FRAME-C-SYNTHESIS-01`
   - QV2-002 and QV2-011
   - parser-core gated packet
   - requires adjacent negative coverage to prevent over-firing
4. Downstream clarification surface
   - QV2-006 only
   - separate product authorization
   - not a parser cleanup packet

Step 1 is optional. Steps 2 through 4 are not pre-authorized.

## Forbidden In This Packet

This report does not authorize:

- parser code edits
- Mini-V1, Mini-V2 admitted, Mini-V2 holdout, raw snapshot, or review-pack edits
- materializer invocation
- `human_review_gate=True`
- holdout reads
- new modules
- new tests
- downstream clarification, refusal, model, or action surfaces
- benchmark, production, route, source, or readiness claims

## Decision

The next safe packet, if any, is `MINI-V2-MATRIX-RECONCILE-01` for QV2-009.
That packet is narrow because it changes only matrix expected surface labels
for a case whose no-route category, no-route kind, ambiguity, and normalized
intent already match.

Stopping after this report is also valid. The report's main purpose is to make
the follow-up choice explicit before more code is written.
