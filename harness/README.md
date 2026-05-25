# Harness Map

This folder contains the runnable deterministic harness for the current
intent-gate artifact plus earlier scaffold modules.

## Current Level 0 Intent Gate Files

| File | Role |
|---|---|
| `level0_workshop_normalized_prompt_view.py` | FRAME-A normalized prompt view |
| `level0_workshop_signal_evidence.py` | FRAME-B signal evidence |
| `level0_workshop_canonical_intent_frame.py` | FRAME-C canonical intent frame |
| `level0_workshop_user_intent_mapper.py` | FRAME-D public mapper shim |
| `level0_workshop_intent_test_matrix_runner.py` | JSON matrix runner |
| `level0_workshop_parser_quality_loop.py` | Feedback report, planner, case-review reporter |
| `level0_workshop_matrix_delta_autonomy.py` | Matrix expected-field candidate/materializer |
| `level0_workshop_frame_b_overlay_autonomy.py` | FRAME-B overlay candidate/materializer |
| `level0_workshop_composite_patch_autonomy.py` | Transactional matrix + FRAME-B composite primitive |
| `level0_workshop_corpus_crawler.py` | Local-only raw candidate crawler |
| `level0_workshop_mini_v2_autonomous_run.py` | Mini-V2 proposal-only report builder |

## Current Data Artifacts

| Path | Role |
|---|---|
| `intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V1.intent.matrix.json` | Closed Mini-V1 matrix |
| `intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json` | Mini-V2 admitted matrix |
| `intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2-HOLDOUT.intent.matrix.json` | Mini-V2 holdout, isolated from autonomous runs |
| `raw_candidate_pools/L0-WS-RAW-CANDIDATES-v1.raw_candidates.json` | Raw local candidate snapshot |
| `admission_review_packs/L0-WS-RAW-CANDIDATES-v1.admission_review.json` | Dedupe/admission review pack |
| `mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v1.report.json` | Proposal-only Mini-V2 run report |

## Tests

Run the full suite:

```powershell
python -m unittest discover -s harness\tests
```

Run the current Mini-V2 proposal report tests:

```powershell
python -m unittest harness.tests.test_level0_workshop_mini_v2_autonomous_run
```

## Boundaries

The harness does not authorize production readiness, benchmark claims,
route validation, source qualification, corpus admission, downstream
model/action execution, or holdout measurement. Those are separate product
decisions.
