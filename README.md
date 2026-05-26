# ai-search

Deterministic, auditable intent-gate research for routing raw user text before
any AI model, agent, workflow, or downstream action is allowed to proceed.

This repository is not a production app, not a benchmark, not an ML training
pipeline, and not a route-validation system. It is a bounded prototype showing
how raw text can pass through a deterministic intent layer that emits
reviewable gate outputs and proposal-only improvement reports.

## Start Here

Read these first:

1. [`ai-search/80-level0-intent-gate-writeup.md`](ai-search/80-level0-intent-gate-writeup.md)
   - the current artifact summary and stop condition
2. [`ai-search/00-controller-checklist.md`](ai-search/00-controller-checklist.md)
   - controller rules, freeze gate, and corpus admission gate
3. [`harness/README.md`](harness/README.md)
   - runnable harness map
4. [`ai-search/README.md`](ai-search/README.md)
   - document index for the historical packet trail

## Current State

- Mini-V1: 35/35 passing
- Mini-V2 admitted: 9/12 passing, 3 failing, 2 proposal groups
- Mini-V2 holdout: 3 cases, isolated from autonomous-loop runs
- Full local suite at latest verification: 1814 tests passing
- Parser-core writes are frozen behind explicit human review

Key Mini-V2 run artifact:

- [`harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v3.report.json`](harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v3.report.json)

## What Exists

- deterministic workshop intent parser
- JSON matrix runner
- bounded failure taxonomy
- feedback planner and proposal grouping
- matrix / FRAME-B / composite materialization primitives with safety gates
- local-only raw candidate crawler
- raw candidate snapshot
- admission review pack
- Mini-V2 admitted matrix and isolated holdout
- proposal-only Mini-V2 autonomous-run snapshot

## What Does Not Exist

- downstream model/action execution
- "Did you mean?" clarification UI
- refusal UX
- production route creation
- source qualification
- benchmark claim
- overlay store
- confidence decay

Those are separate product decisions, not implied by this repository's current
state.

## Run Tests

```powershell
python -m unittest discover -s harness\tests
```

Regenerate the Mini-V2 proposal-only report:

```powershell
@'
from harness.level0_workshop_mini_v2_autonomous_run import (
    write_mini_v2_autonomous_run_report,
)

write_mini_v2_autonomous_run_report(
    "harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v3.report.json"
)
'@ | python -
```

## Repository Map

- `ai-search/` - design documents, controller checklist, packet trail
- `harness/` - deterministic parser, runners, planners, tests, artifacts
- `benchmark-fixtures/` - earlier scaffold fixture material

The file list is intentionally history-heavy. Use the README files as the
navigation layer before reading the numbered packet documents.
