# ai-search - Scaffold Route-Query Index Probe

Document type: Phase 4 / Phase 9 / Scaffold route-query index probe boundary
Owner: Codex (controller)
Author: Codex
Status: Implemented and verified by Codex
Work Order: WO-50

---

## 1. Purpose

WO-50 starts the next executable indexing-logic test after WO-47 and
WO-48. It adds a scaffold-only route-query probe that accepts
already-loaded synthetic fixture payloads and synthetic query specs,
builds a temporary in-memory query map, and records route-first
observations.

This is still not real benchmark execution. It is a controlled
behavior test over the WO-31 synthetic fixture wave.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Start testing indexing logic more directly than WO-47 / WO-48.
- Keep all data synthetic and already admitted.
- Keep the probe in-memory and per-call only.
- Preserve plane separation and route-first behavior.
- Preserve all non-measurement and non-selection booleans as literal
  False.

The scope does not authorize a real adapter, real retrieval service,
third-party dependency, benchmark run, metric collection, architecture
choice, production artifact contract, or benchmark-readiness change.

## 3. Added Files

WO-50 adds:

- `harness/scaffold_route_query_probe.py`
- `harness/tests/test_scaffold_route_query_probe.py`
- `ai-search/50-scaffold-route-query-index-probe.md`

WO-50 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified.

## 4. Public Function

The new public function is:

```text
run_scaffold_route_query_probe(payloads_by_class, queries, event_log) -> dict
```

Inputs:

- `payloads_by_class`: already-loaded dicts for the three admitted
  WO-31 classes.
- `queries`: non-empty list of dicts with `query_id` and
  `synthetic_intent_text`.
- `event_log`: harness `EventLog`.

The function reads no file and writes no file.

## 5. Behavior Under Test

The probe builds a temporary query map from each entry's
`intent_surface.synthetic_intent_text`.

For each query:

- Matching a golden-intent official entry records an official
  observation with its synthetic route identifier.
- Matching a golden-intent miss entry records a miss observation.
- Matching a hard-negative entry records a candidate or normalized
  observation and never records an official observation.
- Matching a boundary-violation entry records a contract-failure
  observation and never turns the violation into a route observation.
- Matching no entry records a miss observation.

Duplicate synthetic intent text is rejected because query identity would
be ambiguous.

## 6. Result Surface

The result dict has exactly thirteen keys:

- `probe_kind`
- `indexed_entry_count`
- `queries_observed_count`
- `official_observation_count`
- `candidate_observation_count`
- `normalized_observation_count`
- `miss_observation_count`
- `contract_failure_observation_count`
- `selection_made`
- `measurement_authorized`
- `real_benchmark_authorized`
- `real_benchmark_ready`
- `probe_note`

The four authorization / readiness / selection booleans are literal
False on every emitted path.

## 7. Event Surface

Success events:

- `scaffold_route_query_probe_started`
- `scaffold_route_query_probe_official_observation`
- `scaffold_route_query_probe_candidate_observation`
- `scaffold_route_query_probe_normalized_observation`
- `scaffold_route_query_probe_miss_observation`
- `scaffold_route_query_probe_contract_failure_observation`
- `scaffold_route_query_probe_run_ended`

Rejection events are explicit halt events with
`scaffold_route_query_probe_*` reason strings. Halt events are recorded
before the corresponding exception is raised.

## 8. Tests Added

`harness/tests/test_scaffold_route_query_probe.py` adds 21 tests across
seven `TestCase` classes:

- success counts and allowed result keys;
- literal-False authorization booleans;
- run-ended event / output count consistency;
- official query observation;
- hard-negative official-plane guard;
- normalized hard-negative observation;
- boundary-violation contract-failure observation;
- unknown-query miss observation;
- input and query rejection paths;
- duplicate synthetic-intent rejection;
- forbidden-language rejection without leaking the source text;
- input isolation and no filesystem writes;
- static import-surface check;
- benchmark fixture no-mutation check.

## 9. Forbidden Scope

WO-50 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- quality, performance, or operational metric collection;
- Stage 2 / 3 / 4 / 5 measurement scaffolding;
- scoring, ranking, or winner declarations;
- a real retrieval adapter or real retrieval / indexing / ranking
  implementation;
- architecture, vendor, library, index family, ANN backend, neural
  re-scorer, retrieval family, ablation cell, multi-stage variant, or
  production system choice;
- production artifact schema, retention policy, storage policy,
  immutability policy, access-control policy, or registration mechanism;
- third-party dependency;
- CLI / entry point / console script;
- mutation of any file under `benchmark-fixtures/`;
- closure of OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076;
- duplication of RK-039.

The WO-47 / WO-48 non-claim constraint carries forward: this probe may
test route-first indexing behavior, but it does not claim that an
indexing approach, index architecture, retrieval family, layer,
constraint strategy, or in-memory probe is sufficient, necessary,
superior, best, complete, production-ready, recommended, or selected.

## 10. Verification Result

Codex verified:

- `python -B -m unittest harness.tests.test_scaffold_route_query_probe -v`
  -> 21/21 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests -v`
  -> 359/359 OK after tracker updates.
- No `__pycache__` directories.
- ASCII compliance across `.py`, `.md`, `.json`, `.gitkeep`, and
  `.gitignore` files.
- Project root contains exactly `ai-search/`, `harness/`, and
  `benchmark-fixtures/`.

Real-benchmark-ready remains NO.
