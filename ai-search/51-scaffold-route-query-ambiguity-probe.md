# ai-search - Scaffold Route-Query Ambiguity Probe

Document type: Phase 4 / Phase 9 / Scaffold route-query ambiguity probe boundary
Owner: Codex (controller)
Author: Claude (under WO-51)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-51

---

## 1. Purpose

WO-51 adds the first scaffold-level test for the core AI-agent failure
analog: when evidence is ambiguous or cross-plane conflicting, the
probe must not silently commit to a confident route observation.

WO-50 verified that an exact synthetic intent text resolves to a
deterministic plane observation under the WO-31 admitted fixture
classes. That surface is binary by construction and cannot produce the
"confident output under ambiguous evidence" failure mode. WO-51
introduces the first probe that can refuse to choose.

The probe still does not perform real retrieval, does not compute
similarity, does not score, does not rank, does not collect metrics,
does not invoke any adapter, and does not select any architecture /
vendor / library / index family / ANN backend / neural re-scorer /
retrieval family / production system. Ambiguity is declared by
test-time synthetic markers on the query, not inferred by an
algorithm.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Start testing ambiguity-refusal behavior at the scaffold level.
- Keep all data synthetic and already admitted under WO-31.
- Keep the probe in-memory and per-call only.
- Preserve plane separation and route-first behavior from WO-47 /
  WO-48 / WO-50.
- Preserve all non-measurement / non-selection / non-readiness
  booleans as literal False.
- Add `ambiguous_observation_count` to the result surface.

The scope does not authorize a real adapter, real retrieval service,
similarity scoring, third-party dependency, benchmark run, metric
collection, architecture choice, production artifact contract, or
benchmark-readiness change.

## 3. Added Files

WO-51 adds:

- `harness/scaffold_route_query_ambiguity_probe.py`
- `harness/tests/test_scaffold_route_query_ambiguity_probe.py`
- `ai-search/51-scaffold-route-query-ambiguity-probe.md`

WO-51 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 module
`harness/scaffold_route_query_probe.py` and its test file are not
modified.

## 4. Public Function

The new public function is:

```text
run_scaffold_route_query_ambiguity_probe(payloads_by_class, queries, event_log) -> dict
```

Inputs:

- `payloads_by_class`: already-loaded dicts for the three admitted
  WO-31 classes.
- `queries`: non-empty list of dicts. Each dict has `query_id` and
  `synthetic_intent_text` as required non-empty strings. Each dict
  MAY optionally carry `declared_candidate_fixture_ids`, a list of
  fixture id strings that the test author asserts are candidate
  matches across more than one plane.
- `event_log`: harness `EventLog`.

The function reads no file and writes no file.

## 5. Ambiguity Model

Ambiguity is a property declared by the test author, not inferred by
the probe. The declaration is the
`declared_candidate_fixture_ids` field on a query spec.

For each query:

- If `declared_candidate_fixture_ids` is absent, the probe follows
  the WO-50 exact-text observation path: official, candidate,
  normalized, miss, or contract failure depending on the matched
  entry.
- If `declared_candidate_fixture_ids` is present, the probe
  validates the list and resolves each fixture id to a plane:
  - golden-intents (official or miss) -> `official_route_results`;
  - hard-negatives -> `candidate_route_results` or
    `normalized_material_support_results` based on the entry's
    `plane_separation_markers.allowed_planes`;
  - boundary-violations -> the entry's
    `plane_separation_markers.violation_plane_in_observed_output`.
- If the declared candidates resolve to two or more distinct planes,
  the probe emits an `ambiguous` observation and does not emit any
  exact-text route observation for that query, even if the
  `synthetic_intent_text` would have matched an entry exactly.

The ambiguous observation includes:

- `query_id`;
- `candidate_fixture_ids`;
- `candidate_classes`;
- `candidate_planes`;
- `ambiguity_declared: True`;
- `selection_made: False`;
- no `chosen_fixture_id` field.

The probe must not silently choose one candidate in an ambiguous case.

## 6. Rejection Rules

The probe rejects, with an explicit halt event before raising:

- `payloads_by_class` is not a dict.
- A required admitted payload class is missing.
- A per-class payload is not a dict, mismatches its `fixture_class`,
  or has missing or non-list entries.
- `queries` is not a non-empty list.
- A query is not a dict.
- A query is missing `query_id` or `synthetic_intent_text` as a
  non-empty string.
- Two queries repeat a `query_id`.
- Two entries share one `synthetic_intent_text`.
- `declared_candidate_fixture_ids` is not a list, or contains a
  non-string or empty element.
- A declared candidate fixture id is repeated.
- A declared candidate fixture id is not present in the admitted
  payloads.
- Declared candidates collapse to one plane only (including lists
  with fewer than two declared candidates).
- A hard-negative entry would observe the official plane (allowed
  planes leaked the official plane, or
  `must_not_authorize_official_return` is False).
- A boundary-violation entry is marked as a valid output (the
  `expected_disqualification` shape relaxed).
- A surfaced string contains a forbidden phrase.

## 7. Result Surface

The result dict has exactly fourteen allowed keys:

- `probe_kind`
- `indexed_entry_count`
- `queries_observed_count`
- `official_observation_count`
- `candidate_observation_count`
- `normalized_observation_count`
- `miss_observation_count`
- `contract_failure_observation_count`
- `ambiguous_observation_count`
- `selection_made`
- `measurement_authorized`
- `real_benchmark_authorized`
- `real_benchmark_ready`
- `probe_note`

The four authorization / readiness / selection booleans are literal
False on every emitted path. The thirteen-key WO-50 surface is
extended by one key (`ambiguous_observation_count`) without removing
any existing key.

## 8. Event Surface

Success events:

- `scaffold_route_query_ambiguity_probe_started`
- `scaffold_route_query_ambiguity_probe_official_observation`
- `scaffold_route_query_ambiguity_probe_candidate_observation`
- `scaffold_route_query_ambiguity_probe_normalized_observation`
- `scaffold_route_query_ambiguity_probe_miss_observation`
- `scaffold_route_query_ambiguity_probe_contract_failure_observation`
- `scaffold_route_query_ambiguity_probe_ambiguous_observation`
- `scaffold_route_query_ambiguity_probe_run_ended`

Rejection events are explicit halt events with
`scaffold_route_query_ambiguity_probe_*` reason strings. Halt events
are recorded before the corresponding exception is raised.

## 9. Tests Added

`harness/tests/test_scaffold_route_query_ambiguity_probe.py` adds 28
tests across eight `TestCase` classes:

- success counts, allowed result keys, and the fourteen-key surface;
- literal-False authorization / readiness / selection booleans;
- run-ended event / output count consistency including
  `ambiguous_observation_count`;
- ambiguous observation across golden-intent official and hard-negative
  candidate;
- ambiguous observation across hard-negative and boundary-violation;
- ambiguous query suppresses every exact-text route observation kind;
- ambiguous declaration wins over an exact-text match;
- non-ambiguous exact-text query follows the WO-50 observation path;
- unknown text without declared candidates observes a miss;
- non-object payload, non-list queries, missing query fields,
  duplicate query ids, duplicate synthetic intent text, unknown
  declared candidate id, duplicate declared candidate id, single-plane
  declared candidates, non-list declared candidates, hard-negative
  official-plane tampering on exact-match and declared-ambiguity paths,
  and boundary-violation valid-output tampering on exact-match and
  declared-ambiguity paths are rejected with explicit halt events;
- forbidden query surface text is rejected without leaking the source
  text into the event log;
- inputs are not mutated;
- no filesystem writes are performed;
- imports are stdlib + harness-internal only;
- `benchmark-fixtures/` files are not mutated.

## 10. Non-Claim Constraint

The WO-47 / WO-48 / WO-49 / WO-50 explicit non-claim constraint
carries forward verbatim:

This probe does not claim that any controller, probe, indexing
approach, index architecture, layer, constraint strategy, in-memory
probe, ambiguity-refusal rule, declared-candidate model, or
observation kind is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected.

The probe records ambiguity. It does not declare an ambiguity-refusal
policy.

## 11. Forbidden Scope

WO-51 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- quality, performance, or operational metric collection;
- Stage 2 / 3 / 4 / 5 measurement scaffolding;
- scoring, ranking, or winner declarations;
- similarity, distance, or near-match scoring of any kind;
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
- modification of the WO-50 probe module
  `harness/scaffold_route_query_probe.py` or its test file;
- closure of OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate (Section K of
`ai-search/00-controller-checklist.md`) continues to govern selection.
Real-benchmark-ready remains NO.

## 12. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_route_query_ambiguity_probe`
  -> 28/28 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 387/387 OK after the new module and tests were added
  (359 prior baseline + 28 new tests).
- Codex review-time hardening added declared-ambiguity rejection
  coverage for hard-negative official-plane tampering and
  boundary-violation valid-output tampering. These guard checks now
  apply on both exact-match and declared-ambiguity paths.
- The WO-50 module `harness/scaffold_route_query_probe.py` and the
  WO-50 test file are unchanged on disk.
- No `__pycache__` directories were created at project paths under
  Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.

Real-benchmark-ready remains NO.
