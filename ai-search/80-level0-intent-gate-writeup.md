# 80. Level 0 Intent Gate Writeup

## Thesis

Raw user text should not flow directly into AI model or agent action. It
should first pass through a deterministic, bounded, auditable intent gate.

The Level 0 workshop intent gate is that artifact. It is not an ML model, not
a benchmark, not a production route validator, and not a downstream action
executor. It is a narrow parser and review loop that turns user text into a
bounded intent record, detects where that record disagrees with a human-authored
matrix, and emits reviewable proposals without mutating parser core
autonomously.

The product idea is simple:

```text
raw user text
  -> deterministic intent gate
  -> clear and allowed intent: downstream action may be considered later
  -> ambiguous intent: ask a bounded clarification at the product surface
  -> out-of-scope intent: no route / refusal later
```

This packet documents the gate and the first CLI demo surface. It does not
build downstream action, route creation, source admission, benchmark execution,
or production integration.

## What Exists

The current Level 0 workshop stack contains five concrete layers.

1. **Parser core**

   The parser maps raw workshop text into bounded prompt categories, item
   kinds, ambiguity status, normalized intent labels, candidate-surface labels,
   and rejection-surface labels.

   Key files:

   - `harness/level0_workshop_signal_evidence.py`
   - `harness/level0_workshop_canonical_intent_frame.py`
   - `harness/level0_workshop_user_intent_mapper.py`

2. **Matrix runner**

   The runner reads a JSON matrix of human-authored prompts and expected gate
   outputs, invokes the public FRAME-D mapper, compares observed vs expected
   fields, and classifies mismatches into a bounded failure taxonomy.

   Key file:

   - `harness/level0_workshop_intent_test_matrix_runner.py`

3. **Feedback planner**

   The planner converts failed case results into bounded upgrade candidates and
   case-review labels. It groups the failure surface; it does not select,
   measure, materialize, or claim readiness.

   Key file:

   - `harness/level0_workshop_parser_quality_loop.py`

4. **Safe materialization primitives**

   Three materializers exist for human-authorized packets:

   - matrix expected-field updates
   - FRAME-B canonical additions
   - composite matrix + FRAME-B patches

   Parser-core materializers are now frozen behind two gates:

   - `materialization_authorized=True`
   - `human_review_gate=True`

   Without both, parser-core writes fail closed.

   Key files:

   - `harness/level0_workshop_matrix_delta_autonomy.py`
   - `harness/level0_workshop_frame_b_overlay_autonomy.py`
   - `harness/level0_workshop_composite_patch_autonomy.py`

5. **Corpus growth path**

   The corpus path is deliberately staged:

   - local-only raw candidate crawler
   - versioned raw snapshot
   - admission review pack
   - human-authored Mini-V2 admission
   - isolated holdout
   - proposal-only Mini-V2 autonomous run

   Key files:

   - `harness/level0_workshop_corpus_crawler.py`
   - `harness/raw_candidate_pools/L0-WS-RAW-CANDIDATES-v1.raw_candidates.json`
   - `harness/admission_review_packs/L0-WS-RAW-CANDIDATES-v1.admission_review.json`
   - `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2.intent.matrix.json`
   - `harness/intent_test_matrices/L0-WS-PARSER-QUALITY-MINI-V2-HOLDOUT.intent.matrix.json`
   - `harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v4.report.json`

6. **CLI gate demo**

   The demo is the first user-visible product surface around the gate. It
   displays one of three branches and stops:

   - `clear`: display category and item kinds
   - `clarify`: display bounded choices and optionally record one user choice
   - `refuse`: display no-route / near-miss refusal text

   The demo writes local JSON-lines audit records, but those records are user
   input records only. They do not train the parser, admit corpus data, update
   expected matrix fields, create routes, or authorize downstream action.

   Key files:

   - `harness/level0_workshop_gate_demo.py`
   - `harness/tests/test_level0_workshop_gate_demo.py`
   - `ai-search/85-level0-gate-demo.md`

## What The Gate Emits

The gate does not emit free-form intent claims. It emits bounded fields.

The important output surfaces are:

- prompt category, such as workflow intent, skill intent, ambiguous, or no-route
- touched item kinds, such as workflow file, skill, agent, instruction, cookbook,
  or none
- ambiguity status
- normalized intent observation
- candidate-surface expectation
- rejection-surface expectation

Those fields are useful because they are inspectable. A reviewer can see
exactly where observed behavior differs from expected gate semantics.

## Safety Architecture

The safety story is the main artifact.

The loop can:

- run matrices
- classify failures
- group upgrade candidates
- compare variants
- produce proposal bundles

The loop cannot, by itself:

- mutate parser core
- admit corpus cases
- read holdout during autonomous runs
- claim benchmark or production readiness
- create or validate routes
- call an LLM, network, or downstream action layer

The key safeguards are:

- bounded enums for failure classes, patch kinds, next-packet types, and review
  labels
- literal false readiness and authorization booleans
- SHA-256 staleness checks before materialization
- semantic case-results verification, not just summary counts
- transactional rollback for source and matrix writes
- parser-core freeze requiring a second human-review gate
- holdout isolation tests
- raw-candidate snapshot and admission review pack before Mini-V2 admission
- explicit non-claim language in runner, planner, admission, and run artifacts
- Section P demo-surface rules that keep CLI output display-only and audit logs
  out of parser, admission, benchmark, and autonomous-loop paths

The core freeze and corpus admission gates are recorded in:

- `ai-search/00-controller-checklist.md` Section N
- `ai-search/00-controller-checklist.md` Section O
- `ai-search/00-controller-checklist.md` Section P

## Evidence So Far

Mini-V1 is closed:

- 35 cases
- 35 passing
- 0 failing

Mini-V2 admitted is intentionally not closed:

- 12 cases
- 11 passing
- 1 failing
- 1 planner candidate

Mini-V2 holdout exists but remains isolated:

- 3 cases
- not read by the autonomous-run packet
- reserved for a separate human measurement decision

The Mini-V2 proposal-only run reports these failure buckets:

- `out_of_scope_underdetect`: 0 cases
- `frame_c_synthesis_rule_gap`: 0 cases
- `frame_c_ambiguity_misreport`: 1 case
- `expected_field_drift`: 0 cases

The important point is not that Mini-V2 is green. It is not. The important
point is that the gate exposes the failures in bounded, reviewable form without
silently changing parser core or copying parser observations into expected
fields.

## What This Is Not

This artifact does not prove:

- parser completeness
- production readiness
- benchmark performance
- route validation
- source qualification
- downstream action safety
- general-purpose text-to-AI-model capability

It also does not train or fine-tune anything. The matrices are regression and
coverage contracts, not training data.

The right claim is narrower:

> This repository contains a deterministic, auditable intent-gate prototype
> that can run human-authored prompt matrices, classify mismatches, propose
> bounded follow-up work, and prevent autonomous parser-core mutation without
> explicit human review.

## Why Mini-V2 Matters

Mini-V2 matters because it changed the gate from a closed starter set into a
growth surface.

The raw crawler generated 69 local-only candidates. The admission review pack
proved that only 18 were novel after de-duplicating against Mini-V1 and
planning-doc fixtures. Human admission selected 12 admitted cases and 3 holdout
cases.

That prevented two common corpus failures:

- treating crawler output as admitted evaluation data
- copying parser observations into expected fields

Mini-V2 then failed on 1 of 12 cases. That is useful evidence. It shows the gate
is not just memorizing Mini-V1. It also shows where the next product decisions
would be if the project continued.

## The Demo Product Surface

The gate now has a CLI-only demo surface. That surface is deliberately thin: it
lets a user enter one prompt, see how the gate classifies it, optionally choose
from bounded clarification options, and record a local audit line.

The demo is not a downstream consumer. It does not generate workflow files,
skills, agents, instructions, or any other artifact. It does not invoke a
model, planner, materializer, crawler, network client, subprocess, or
third-party service.

The eventual downstream consumer, if one is ever built, would still need to
decide what to do with each gate result:

- clear and allowed intent: maybe pass a structured request to a model/action
  layer
- ambiguous intent: ask "Did you mean?" using bounded choices
- out-of-scope intent: return no-route/refusal
- matrix drift: correct the human-authored evaluation contract

That remains a separate product decision. The demo demonstrates that the gate
can expose a bounded product surface; it does not prove that any downstream
action is safe or ready.

QV2-006 is the important example. The parser still treats the deploy/notify
prompt as workflow intent. The demo layer handles the product ambiguity by
offering `workflow_file`, `skill`, and `instruction` as bounded choices. That is
intentional product-surface behavior, not parser-core hardening and not a
matrix patch to force Mini-V2 to 12/12.

## Current Follow-Up Choices

The current Mini-V2 run produces one proposal group:

| Candidate | Failure class | Count | Follow-up type |
|---|---:|---:|---|
| UPG-001 | `frame_c_ambiguity_misreport` | 1 | downstream clarification-surface decision demonstrated by the CLI demo |

The safest next action is not to force Mini-V2 to 12/12. The safest next action
is to stop, publish the artifact, and decide later whether a real downstream
consumer is worth building.

The prior matrix reconciliation item was closed by
`82-mini-v2-matrix-reconcile.md`. The prior no-route hardening bucket was
closed by `83-mini-v2-no-route-harden.md`. The prior FRAME-C synthesis bucket
was closed by `84-mini-v2-frame-c-synthesis.md`.

## How To Reproduce The Current Evidence

Run the full test suite:

```powershell
python -m unittest discover -s harness\tests
```

The gate-demo packet recorded this full-suite line against commit `0734ad6`:

```text
Ran 1837 tests in 76.437s

OK
```

Run the CLI demo:

```powershell
python -m harness.level0_workshop_gate_demo "Deploy this workflow and notify me if it fails" --choice workflow
```

Expected branch shape:

```text
Level 0 gate demo
Branch: clarify
Category: B. workflow intent
Item kinds: workflow_file
Clarification: Did you mean one of these?
Choices: workflow_file, skill, instruction
Chosen kind: workflow_file
```

Regenerate the Mini-V2 proposal-only report:

```powershell
@'
from harness.level0_workshop_mini_v2_autonomous_run import (
    write_mini_v2_autonomous_run_report,
)

write_mini_v2_autonomous_run_report(
    "harness/mini_v2_runs/L0-WS-MINI-V2-AUTONOMOUS-RUN-v4.report.json"
)
'@ | python -
```

The report test asserts that the committed artifact equals a fresh live run:

```powershell
python -m unittest harness.tests.test_level0_workshop_mini_v2_autonomous_run
```

## Stop Condition

The current artifact is complete enough to document and pause.

The next phase should not begin by default. It should require a new product
decision:

- build real downstream clarification/refusal/action surfaces beyond the CLI
  demo, or
- expand the corpus with new local sources, or
- stop permanently and preserve this as the bounded intent-gate artifact.

The strongest next move is: document, publish, and stop before adding more
architecture.
