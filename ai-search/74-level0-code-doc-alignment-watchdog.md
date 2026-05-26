# 74. Level 0 Code-Doc Alignment Watchdog

## Goal

Define a read-only watchdog scope that compares high-signal ai-search
documentation claims against the current code, tests, and matrix state.
The watchdog exists to catch material drift before new parser, corpus,
crawler, route, source, benchmark, or autonomous-loop work is approved.

This document defines the watchdog boundary only. It does not create an
automation, add a hook, run a monitor, change parser behavior, admit
corpus content, authorize crawler work, authorize overlay storage, or
close any open question.

## Authority

Canonical authority remains with:

- `ai-search/00-controller-checklist.md`
- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`
- the active Work Order packet under review

If this document conflicts with those files, the canonical files win and
this document must be corrected.

## Scope

Allowed watchdog actions:

- Read local repository files.
- Inspect `git status`, `git diff`, and relevant local test output when
  already available or explicitly run by the reviewer.
- Compare documentation claims against implemented code, tests, matrix
  files, and explicit guardrails.
- Report blockers, warnings, file references, and recommended next
  actions.

Forbidden watchdog actions:

- Edit files.
- Create commits, branches, pull requests, or automation records.
- Run network, web crawl, GitHub API, browser, subprocess fetch, or
  third-party dependency workflows.
- Admit raw candidates into any corpus.
- Generate expected fields from parser output.
- Materialize parser-core changes.
- Expand patch kinds, overlay storage, confidence decay, corpus scope,
  benchmark scope, source admission, route creation, or production
  readiness.

## High-Signal Documents

The watchdog should prioritize these files before scanning lower-signal
material:

- `ai-search/00-controller-checklist.md`
- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`
- `ai-search/00-system-map.md`
- `ai-search/00-claude-scope-prompt-template.md`
- `ai-search/73-level0-workshop-intent-test-matrix-runner.md`
- any newly added Level 0 workshop scope document
- any recently changed `.md` file

The watchdog should ignore cosmetic wording, line wrapping, and minor
style differences unless they change a boundary, claim, or readiness
state.

## Material Drift Checks

The watchdog must look for these classes of drift:

- Documentation claims Mini-V1, Mini-V2, or a future matrix is closed
  without current runner/test evidence.
- Documentation implies benchmark, production, source qualification,
  route validation, corpus admission, or model-quality readiness from a
  parser-quality matrix.
- Documentation says parser-core writes are frozen while code permits a
  parser-core materializer to write without an explicit human-review
  gate.
- Documentation says the autonomous loop is proposals-only while a code
  path can mutate parser core with only `materialization_authorized=True`.
- Documentation describes bounded patch kinds but code widens patch-kind
  enums without a matching scope decision.
- Documentation says holdout or raw candidates are isolated while code
  reads them through autonomous-loop paths.
- Documentation describes crawler scope as local-only while code or
  tests introduce network, web, browser, or subprocess fetch behavior.
- Documentation states a test count, pass count, or matrix count that is
  stale relative to current local evidence.

## Report Format

The watchdog report must be short and evidence-first:

1. `BLOCKERS` - issues that should stop new Claude/Codex
   implementation before review.
2. `WARNINGS` - material drift that can wait but should be corrected.
3. `EVIDENCE` - exact files, line references, commands, or test outputs
   supporting each finding.
4. `NEXT ACTION` - the smallest correction or review step.

For every blocker or warning, the report must name the related file(s)
explicitly. If the finding is code-doc drift, name both sides: the
documentation file carrying the claim and the code, test, matrix, or
snapshot file that proves the current state.

If there is no material drift, the report must say:

`No material code-doc drift detected.`

## Automation Prompt Template

If a future packet creates a Codex automation for this watchdog, use this
prompt as the starting point and keep the automation read-only:

```text
Act as a strict code-document alignment watchdog for the ai-search
workspace. Do not edit files. Inspect the current repository state and
compare implemented code/tests against claims in high-signal docs:
ai-search/00-controller-checklist.md, ai-search/00-open-questions.md,
ai-search/00-claude-task-ledger.md, ai-search/00-system-map.md,
ai-search/00-claude-scope-prompt-template.md,
ai-search/73-level0-workshop-intent-test-matrix-runner.md, any newly
added Level 0 workshop scope document, and any recently changed docs.

Focus on material drift: docs claiming a matrix, epoch, freeze, corpus,
crawler, route, source, benchmark, or production state without matching
code/test evidence; stale test counts; parser-core freeze claims not
enforced by materializer gates; autonomous-loop write capability that
contradicts proposal-only language; widened patch kinds not reflected in
scope docs; holdout/raw-candidate leakage into autonomous-loop paths; or
docs overstating benchmark, source, route, corpus, or production
readiness.

Ignore cosmetic wording and minor formatting. Report: (1) BLOCKERS that
should stop new implementation before review, (2) WARNINGS that can
wait, (3) exact files/lines or commands supporting each finding, and
(4) recommended next action. For every blocker or warning, name the
related file(s) explicitly; for code-doc drift, name both the doc claim
file and the code/test/matrix/snapshot evidence file. If there is no
material drift, say 'No material code-doc drift detected.' Do not create
commits, branches, automations, or modify files.
```

## Non-Claims

This watchdog is not a benchmark, test harness, corpus admission tool,
crawler, source qualifier, route validator, production gate, or model
evaluation system. It is a read-only review aid for detecting mismatch
between project claims and local implementation evidence.
