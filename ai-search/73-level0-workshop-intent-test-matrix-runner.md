# 73. Level 0B Workshop Intent Test Matrix Runner

## Goal
Add a deterministic JSON matrix runner that observes the existing FRAME-D mapper output and emits bounded parser review evidence. The smoke matrix is not the parser-quality corpus and the 26 seed prompts are not the system boundary.

## Scope
Allowed: `harness/level0_workshop_intent_test_matrix_runner.py`, `harness/tests/test_level0_workshop_intent_test_matrix_runner.py`, and `harness/intent_test_matrices/*.intent.matrix.json`.

Forbidden: parser module modification, benchmark-fixtures mutation, controller-checklist mutation, LLM/provider/network/subprocess calls, third-party dependencies, route/source/corpus/benchmark authorization, matrix-level quality claims, and real-benchmark-ready flips.

## Verification
Runner tests pass, full suite passes, `benchmark-fixtures/` remains unchanged, FRAME-A/B/C/D modules remain unchanged, and all emitted gating booleans remain literal False.
