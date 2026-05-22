# ai-search - Scaffold Indexing Logic Probe

Document type: Phase 4 / Phase 9 / Scaffold indexing-logic probe boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-47

---

## 1. Purpose

This document records the scaffold-internal indexing-logic probe
authorized under WO-47 (DC-047) at
`harness/scaffold_index_probe.py`. The module builds a small
in-memory probe index from already-loaded WO-31 admitted synthetic
payload entries and exercises route-first retrieval boundary
behavior at the scaffold level. It is the first executable scaffold
environment that tests indexing / retrieval LOGIC without invoking
any real or mock adapter.

The probe is scaffold-only. It does NOT perform real benchmark
execution, does NOT invoke a real or mock adapter, does NOT consume
external corpora, does NOT collect quality / performance metrics,
does NOT score, does NOT rank, and does NOT select any architecture
/ vendor / library / index family / ANN backend / neural re-scorer /
retrieval family / ablation cell / multi-stage variant / production
system. OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, and OQ-076
all remain OPEN. RK-039 continues to apply unchanged.
Real-benchmark-ready remains NO. The probe output carries
`selection_made: False`, `measurement_authorized: False`,
`real_benchmark_authorized: False`, and `real_benchmark_ready: False`
as literal constants on every emitted path.

The WO-47 packet preamble required application of
`ai-search/00-controller-checklist.md` Section L (Mutual Alignment
Protocol / Shared Scope Verification) before implementation. The
Section L scope quiz was performed and recorded in the WO-47 ledger
entry under "Pre-Implementation Review."

## 2. Relationship To WO-30 / WO-31 / WO-35 And WO-45 / WO-46

- WO-30 (`30-fixture-payload-format-boundary.md`) recorded the
  scaffold-internal entry-level payload shape (intent surface,
  expected outcome class, plane separation markers, expected
  disqualification, etc.).
- WO-31 (`31-first-synthetic-fixture-payload-wave.md` / DC-034)
  authored the first synthetic wave of three admitted payload
  classes (`golden-intents`, `hard-negatives`, `boundary-violations`)
  at `benchmark-fixtures/<class>/wave-001.json`.
- WO-35 (`35-scaffold-payload-batch-runner.md`) introduced the
  scaffold batch runner over the same payloads.
- WO-45 (`45-stage1-contract-safety-pass-scaffold.md`) introduced
  the Stage 1 contract-safety pass scaffold; it operates on the
  Stage 0 readiness observation, not on payload entries directly.
- WO-46 (`46-stage1-clearance-observation.md`) introduced the
  Stage 1 clearance observation bridge; it operates on the Stage 1
  result, not on payload entries directly.

WO-47 sits beside WO-45 / WO-46: it does not consume the Stage 1
result; it consumes the admitted WO-31 payloads directly and tests
their route-first boundary behavior at the scaffold level. WO-47
is a logic probe, not a Stage 2 measurement scaffold. It does NOT
authorize Stage 2 quality measurement; the output's
`measurement_authorized` and `real_benchmark_authorized` are fixed
to literal `False`.

## 3. Why This Is An Indexing-Logic Probe, Not A Real Benchmark

The distinction is important and the language of the module carries
it:

- **No real adapter call.** The probe does not invoke
  `harness.mock_adapter.run_mock_adapter(...)`, does not invoke
  `harness.dry_run.run_toy_dry_run(...)`, and does not call any
  retrieval, indexing, ranking, or network function.
- **No external corpus.** The probe consumes only the
  caller-provided payload dicts (already loaded by the caller).
- **No metric.** No score is computed, no aggregation is performed,
  no threshold is applied, no ranking is constructed.
- **No selection.** The probe index is a scaffold-only in-memory
  mapping from `fixture_id` to `(class_name, entry)`. It is NOT a
  selected index architecture; the output `probe_kind` is
  `"scaffold_indexing_logic_probe"` precisely so it cannot be
  misread as a selection.
- **No third-party dependency.** The module imports only Python
  stdlib (none required at module scope) and harness-internal
  symbols (`harness.payload_loader`, `harness.review_package`).

The probe verifies that route-first boundary rules HOLD across the
admitted entries. It does NOT test which retrieval architecture
would best discover the entries. Architecture comparison remains
gated by the Indexing Excellence Gate
(`00-controller-checklist.md` Section K) and requires a separate
future Codex packet.

## 4. Input Contract

The function accepts two arguments:

```
run_scaffold_index_probe(payloads_by_class, event_log) -> dict
```

- `payloads_by_class`: a dict mapping admitted-class strings to
  already-loaded payload dicts. The module enforces:
  1. Top-level value is a dict.
  2. Every entry in `REQUIRED_PAYLOAD_CLASSES` (the three admitted
     first-wave classes `golden-intents`, `hard-negatives`,
     `boundary-violations`) is present as a key.
  3. Each per-class value is a dict.
  4. Each payload's `fixture_class` matches its key.
  5. Each payload's `entries` is a non-empty list.

  Each violation records an explicit halt event before raising the
  matching named exception.

- `event_log`: a `harness.event_log.EventLog` instance.

The probe does NOT read files. The caller is responsible for
loading the payload JSON.

## 5. In-Memory Probe Index Boundary

The probe builds a flat dict mapping `fixture_id` -> `(class_name,
entry)` and an ordering list. The dict is local to the function
call and is not exposed outside; it is not a registered index, not
a selected index, and not a production index.

Duplicate `fixture_id` across the probe input is rejected with
`DuplicateFixtureIdAcrossProbe`. A duplicate would either mean two
different entries sharing an id (a content-integrity error) or the
same entry surfacing twice (a probe-input error). Either way,
ambiguous identity is rejected before any per-entry observation
runs.

The probe index does not persist beyond the function call. There
is no on-disk index, no warm cache, no cross-call state.

## 6. Per-Class Behavior

The probe dispatches each entry to a per-class observer based on
its class:

### 6.1 golden-intents

- An entry with `expected_outcome_class == "official_route_expected"`
  produces an **official observation** carrying the synthetic
  route identifier from `expected_official_route_reference`. The
  observation lands on `official_route_results`. The observation
  explicitly carries `is_promotion_trigger: False` (mirroring the
  WO-31 entry-level disclaimer).
- An entry with `expected_outcome_class == "miss_expected"`
  produces a **miss observation** carrying the
  `miss_classification` field from the entry. The observation
  records that the official plane is empty for this entry
  (`plane_is_empty_for_this_entry: True`).

### 6.2 hard-negatives

- The probe observes the entry on one of the entry's
  `plane_separation_markers.allowed_planes`. If the candidate
  plane is allowed, the observation lands there; otherwise the
  normalized-material plane is preferred.
- The probe explicitly REJECTS any hard-negatives entry whose
  `allowed_planes` includes `official_route_results` with
  `HardNegativeForbiddenOfficialReturn`. The hard-negatives
  contract forbids the official plane unconditionally.
- The probe also REJECTS any hard-negatives entry that declares
  `must_not_authorize_official_return: False` (a tampered
  payload).
- The observation carries the entry's `near_match_classification`
  and the full `allowed_planes` list so downstream readers can
  verify the boundary was honored.

### 6.3 boundary-violations

- The probe always produces a **contract-failure observation** for
  a well-formed boundary-violations entry. It NEVER produces a
  successful retrieval observation for such an entry.
- The probe REJECTS any boundary-violations entry whose
  `expected_disqualification.expected_halt` is not True, or
  whose `is_forbidden_output` is not True, or whose
  `is_valid_output` is True. All three are tampering signals; any
  one of them raises `BoundaryViolationTreatedAsSuccess`.
- The observation carries the entry's `target_contract_assertion`,
  the `violation_plane_in_observed_output`, the
  `forbidden_plane_collapse`, and the
  `halt_classification` from `expected_disqualification`.

## 7. Output Contract

On success the function returns a fresh dict with exactly the
twelve allowed top-level keys (`ALLOWED_OUTPUT_KEYS`):

- `probe_kind`: literal `"scaffold_indexing_logic_probe"`.
- `entries_indexed_count`: integer total of entries observed.
- `official_observation_count`: integer count of official
  observation events emitted.
- `candidate_observation_count`: integer count of candidate
  observation events emitted.
- `normalized_observation_count`: integer count of normalized
  observation events emitted.
- `miss_observation_count`: integer count of miss observation
  events emitted.
- `contract_failure_observation_count`: integer count of
  contract-failure observation events emitted.
- `selection_made`: literal `False`.
- `measurement_authorized`: literal `False`.
- `real_benchmark_authorized`: literal `False`.
- `real_benchmark_ready`: literal `False`. This field makes the
  WO-39 / WO-40 readiness state observable directly inside the
  probe output, so a downstream reader cannot mistake the probe's
  successful run for a real-benchmark-ready signal.
- `probe_note`: literal observation-only string referencing this
  document and the Indexing Excellence Gate.

No additional top-level key is emitted. The counts are integers
only; no aggregated score, no rank, no threshold, no winner
appears.

## 8. Event And Halt Behavior

Events recorded into `event_log` on the success path:

- `scaffold_index_probe_started` (with `entries_indexed_count` and
  `class_count`).
- One per-entry observation event per entry. The event type is one
  of:
  - `scaffold_index_probe_official_observation`
  - `scaffold_index_probe_candidate_observation`
  - `scaffold_index_probe_normalized_observation`
  - `scaffold_index_probe_miss_observation`
  - `scaffold_index_probe_contract_failure_observation`
  Each event carries `class_name`, `fixture_id`, and the
  per-entry observation dict.
- `scaffold_index_probe_run_ended` (with the entries-indexed and
  per-kind counts).

Halt event reasons recorded before each rejection raises:

- `scaffold_index_probe_non_object_input` (non-dict input).
- `scaffold_index_probe_missing_required_class` (missing admitted
  class key).
- `scaffold_index_probe_non_object_payload` (per-class value not a
  dict) and `scaffold_index_probe_non_object_entry` (entry not a
  dict).
- `scaffold_index_probe_missing_or_non_list_entries`
  (`entries` missing or not a non-empty list).
- `scaffold_index_probe_class_mismatch` (`fixture_class` mismatch).
- `scaffold_index_probe_duplicate_fixture_id` (duplicate
  `fixture_id` across the probe input).
- `scaffold_index_probe_hard_negative_forbidden_official`
  (hard-negatives entry would land on the official plane).
- `scaffold_index_probe_boundary_violation_treated_as_success`
  (boundary-violations entry declares a non-forbidden outcome).
- `scaffold_index_probe_forbidden_language` (forbidden phrase in
  the accepted payload surface or probe output).
- `scaffold_index_probe_unknown_class` (defensive; raised only if
  `REQUIRED_PAYLOAD_CLASSES` is ever extended without updating
  the dispatcher).

Codex review-time hardening added a pre-event surface scan after
input shape validation and before any entry values are copied into
observation events. This closes the event-field leak case: a
tampered but otherwise well-shaped payload value such as a
forbidden phrase inside `fixture_id` is rejected before it can
appear in `class_name`, `fixture_id`, or an observation dict. The
halt event records only the offending phrase, not the source text,
so the rejection path does not echo the forbidden value.

The halt-and-raise behavior matches the WO-19 / DC-022 halt
boundary: every rejection records an explicit halt event before
the matching named exception is raised.

## 9. Non-Measurement Guarantee

The probe does not authorize measurement under any path:

- Success path: `measurement_authorized: False` and
  `real_benchmark_authorized: False` and `real_benchmark_ready:
  False` are literal constants in the output dict.
- Failure path: the function raises before any output is returned.
  No `measurement_authorized: True` is ever emitted.
- The per-entry observation events carry only the entry's own
  shape data plus a plane / kind label; they contain no metric,
  no score, no rank, no aggregation, and no quality / performance
  signal.

This matches the WO-19 / DC-022 halt-before-measurement invariant
ratified at WO-36 review and carried forward through WO-43 / WO-44,
WO-45, and WO-46. The scaffold extends the invariant forward at
this new layer.

A future Codex packet that introduces real measurement must
explicitly relax this rule and must record the relaxation in a new
DC-XXX tracker row. The current scaffold cannot drift into
authorizing measurement.

## 10. Non-Selection Guarantee

The probe does not select any architecture, vendor, library,
index family, ANN backend, neural re-scorer, retrieval family,
ablation cell, multi-stage variant, or production system:

- The output `selection_made` is literal `False` on every path.
- The output `probe_kind` is literal
  `"scaffold_indexing_logic_probe"`. This naming is deliberate:
  the probe is NOT a selected index architecture, and the output
  cannot be misread as one.
- The probe-index data structure is local to the function call;
  it is not exposed outside and is not registered.
- The Indexing Excellence Gate (`00-controller-checklist.md`
  Section K) continues to govern selection unconditionally. "Best
  not proven = not selected" remains canonical.
- No aggregate count produced by the probe may select a winner by
  itself. The counts are observation counts only.

### 10.1 Explicit Non-Claim Constraint (added under review)

Codex added an explicit checklist constraint during WO-47 review:

> The probe may test route-first indexing behavior, but it must not
> claim an indexing approach, index architecture, retrieval family,
> layer, constraint strategy, or in-memory probe is sufficient,
> necessary, superior, best, complete, production-ready,
> recommended, or selected.

The constraint applies at every WO-47 surface: implementation
output strings, event names and event fields, result keys and
result values, test fixture helper names where surfaced, this
boundary document's language, and the tracker / ledger text. The
WO-47 implementation honors the constraint:

- The result dict contains no string that asserts the probe or any
  indexing approach is `sufficient`, `necessary`, `superior`,
  `best`, `complete`, `production-ready`, `recommended`, or
  `selected`.
- Event field values are guarded by scanning the accepted payload
  string surface before event emission. A forbidden term in a
  surfaced payload value raises `ForbiddenLanguageInProbeOutput`
  before any observation event can copy that value.
- The event name `scaffold_index_probe_run_ended` is a purely
  temporal marker that the probe run finished; it does not assert
  the probe is `complete` as a qualitative property. (The earlier
  draft used `scaffold_index_probe_completed`; renamed under this
  constraint to remove the `"complete"` stem.)
- Negations of the form "the probe is NOT a selected index
  architecture" are explicit non-claims and are preserved; they
  state what the probe is NOT and therefore honor the constraint
  rather than violate it.
- The "Forbidden Scope" enumeration of `"winner / best /
  production-ready / recommended"` is meta-language naming what
  the document refuses to assert. Listing the forbidden terms is
  not asserting them.

## 11. Forbidden Scope

WO-47 is forbidden from doing any of the following:

- Modifying any existing harness implementation module. The one
  allowed new module is `harness/scaffold_index_probe.py`.
- Modifying any existing test file under `harness/tests/`.
- Mutating any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Invoking a real or mock adapter from the new module.
- Calling `harness.dry_run.run_toy_dry_run(...)`,
  `harness.batch_runner.run_payload_batch(...)`, or any other
  harness component that touches a payload file or a real
  retrieval surface.
- Performing real benchmark execution.
- Collecting quality / performance / operational metrics.
- Authoring any Stage 2 / 3 / 4 / 5 scaffolding.
- Scoring, ranking, or declaring any configuration a winner /
  best / production-ready / recommended.
- Authoring a production manifest schema, contract, retention
  policy, storage policy, immutability policy, access-control
  policy, or registration mechanism.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding any third-party dependency. The
  `test_no_third_party_imports` test enforces this by AST-parsing
  the module and asserting every import root is in
  `sys.stdlib_module_names` or is `"harness"`.
- Introducing a CLI, an entry point, a console script, or any
  shell wrapper.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076. All seven remain OPEN.
- Duplicating RK-039.
- Consolidating the `"score"` / `"scoring"` forbidden-language
  extension into `harness/review_package.py` (that file is outside
  the allowed-files list).
- Mutating corpus docs, route registry docs, validation evidence,
  source quality graph, intent trace store, candidate routes, or
  official routes.

## 12. What Remains Unresolved

WO-47 does not resolve:

- Stage 2 quality measurement scaffolding.
- Stage 3 performance measurement scaffolding.
- Stage 4 operational measurement scaffolding.
- Stage 5 Human Architecture Review Package scaffolding.
- Real candidate retrieval adapter authoring.
- Real fixture admission / ownership process (OQ-035 OPEN,
  OQ-049 OPEN).
- Real metric policy or scoring protocol.
- Real benchmark execution.
- Artifact retention / storage / immutability / access-control
  policy (OQ-056 OPEN).
- Production artifact contract (OQ-076 OPEN).
- Configuration registration authority (OQ-057 OPEN).
- Dependency policy beyond the first scaffold (OQ-075 OPEN).
- Broader scope process (OQ-070 OPEN).
- Architecture / vendor / library / index family / ANN backend /
  neural re-scorer / retrieval family / ablation cell / multi-stage
  variant / production-system selection.
- The `"score"` / `"scoring"` forbidden-language consolidation
  flagged by Codex at WO-39 / WO-40 review.

The WO-39 / WO-40 readiness gate states are unchanged by WO-47:

| Gate | State |
|------|-------|
| scaffold-ready | YES |
| artifact-ready | YES |
| review-summary-ready | YES |
| real-benchmark-ready | NO |

WO-47 starts scaffold indexing-logic TESTING; it does not start
real benchmark execution. The output's
`real_benchmark_ready: False` literal makes this explicit at the
data surface.
