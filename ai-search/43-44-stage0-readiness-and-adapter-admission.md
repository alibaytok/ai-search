# ai-search - Stage 0 Readiness Review + Candidate Adapter Admission Contract Scaffold

Document type: Phase 4 / Phase 9 / Stage 0 readiness + adapter admission scaffold boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes - Stage 0 scaffold only; real-benchmark-ready remains NO
Work Order: WO-43 / WO-44 (consolidated)

---

## 1. Purpose

This document records the first executable pre-measurement scaffold
toward real benchmark start, authorized under WO-43 / WO-44 (DC-044):

- A scaffold-internal candidate adapter admission contract validator
  at `harness/candidate_adapter_contract.py`.
- A scaffold-internal Stage 0 readiness review at
  `harness/readiness_review.py` that consumes a fixture admission
  record and a candidate adapter record.
- Two toy fixture records at
  `harness/tests/fixtures/toy_candidate_adapter_record.json` and
  `harness/tests/fixtures/toy_fixture_admission_record.json`.

The scaffold is pre-measurement only. It does not author a real
adapter, does not authorize real benchmark execution, does not
collect metrics, does not score, does not rank, and does not select
any architecture / vendor / library / index family / ANN backend /
neural re-scorer / retrieval family / ablation cell / multi-stage
variant / production system. OQ-035, OQ-049, OQ-056, OQ-057, OQ-070,
OQ-075, and OQ-076 all remain OPEN. RK-039 continues to apply
unchanged.

WO-43 / WO-44 implements the safest pre-measurement scaffold pair
recommended in
`ai-search/41-42-real-benchmark-start-contract.md` Section 13
(Shape A + part of Shape B): Stage 0 readiness review scaffolding
together with the candidate adapter admission contract test surface.
The two share the candidate registration record shape and neither
authors a real adapter, a real metric, or a real benchmark step.

## 2. Why WO-43 / WO-44 Is Combined

Codex combined WO-43 (candidate adapter admission contract scaffold)
and WO-44 (Stage 0 readiness review scaffold) into a single
execution packet because:

- The Stage 0 readiness reviewer naturally consumes the candidate
  adapter admission contract; splitting them would force the WO-44
  packet to forward-declare a contract that the WO-43 packet had
  not yet recorded as approved.
- Both modules are pure dict-in / event-log-out validators. They
  share the same scaffold-marker pattern (a string scalar containing
  two required substrings) and the same forbidden-language scan
  pattern.
- Both are pre-measurement; neither admits any measurement, any
  real adapter, or any architecture / vendor / library claim.
- Combining them in one packet keeps the Indexing Excellence Gate
  audit surface narrow: a single review reads both modules' rejection
  ordering and confirms the absence of any measurement-authorization
  semantics.

The combination matches the explicit Section 13 recommendation in
`ai-search/41-42-real-benchmark-start-contract.md`: Shape A +
part of Shape B is the safest pair to combine because both are
pre-measurement scaffolding sharing the candidate registration
record shape, and pairing pre-measurement with measurement scaffolding
(Shape C) was explicitly recommended against.

## 3. Candidate Adapter Admission Contract Scaffold

The contract validator lives at
`harness/candidate_adapter_contract.py` and exposes one public
function:

```
validate_candidate_adapter_record(record, event_log) -> dict
```

Behavior:

- Accepts an already-loaded dict only. Does not read files. Does not
  write files.
- Records `candidate_adapter_record_validated` on success.
- Records an explicit halt event into `event_log` before raising on
  every rejection path.
- On success returns the input `record` unchanged.

Record requirements:

- Scaffold marker key `_candidate_adapter_marker` is present and is
  a non-empty string containing both substrings `"harness-internal"`
  and `"candidate-adapter"` (case-insensitive).
- Every required field is present:
  - `candidate_adapter_id`
  - `adapter_kind`
  - `configuration_id`
  - `planes_declared`
  - `selection_made`
  - `production_registration`
  - `real_adapter`
  - `dependencies_declared`
- `selection_made is False`.
- `production_registration is False`.
- `real_adapter is False`. The scaffold explicitly forbids any
  record that claims to be a real adapter; real-adapter
  authorization requires a separate future Codex packet.
- `planes_declared` is a list and every entry is in the canonical
  WO-21 plane set (`harness.payload_loader.WO_21_PLANE_NAMES`). No
  new copy of the plane name list is created; the WO-32 drift-risk
  policy holds.
- No phrase from `harness.review_package.FORBIDDEN_PHRASES` appears
  anywhere in record string scalars.
- No phrase from `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
  appears anywhere in record string scalars.

Rejection ordering and named exceptions (in the order the validator
evaluates):

1. Non-dict input -> `NonObjectCandidateAdapterRecord` (halt
   `candidate_adapter_non_object`).
2. Missing scaffold marker key -> `MissingCandidateAdapterMarker`
   (halt `candidate_adapter_missing_marker`).
3. Non-string or substring-missing marker ->
   `InvalidCandidateAdapterMarker` (halt
   `candidate_adapter_invalid_marker`).
4. Missing required field -> `MissingCandidateAdapterField` (halt
   `candidate_adapter_missing_field`).
5. `selection_made is not False` ->
   `CandidateAdapterDeclaresSelection` (halt
   `candidate_adapter_declares_selection`).
6. `production_registration is not False` ->
   `CandidateAdapterDeclaresProductionRegistration` (halt
   `candidate_adapter_declares_production_registration`).
7. `real_adapter is not False` ->
   `CandidateAdapterDeclaresRealAdapter` (halt
   `candidate_adapter_declares_real_adapter`).
8. Non-list `planes_declared` or unknown plane name in `planes_declared` ->
   `UnknownCandidateAdapterPlane` (halt
   `candidate_adapter_unknown_plane`).
9. Forbidden selection phrase anywhere in record strings ->
   `ForbiddenLanguageInCandidateAdapterRecord` (halt
   `candidate_adapter_forbidden_language`).
10. Forbidden claim phrase anywhere in record strings ->
    `ForbiddenClaimInCandidateAdapterRecord` (halt
    `candidate_adapter_forbidden_claim`).

The validator does not mutate the input dict. The validator imports
only `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`,
`harness.payload_loader.WO_21_PLANE_NAMES`, and
`harness.review_package.FORBIDDEN_PHRASES` (harness-internal). No
third-party dependency is added. No CLI is introduced.

## 4. Fixture Admission Scaffold Boundary

The Stage 0 readiness reviewer (Section 5) additionally validates a
fixture admission record at scaffold level. The fixture admission
record shape is documented in this section.

Record requirements:

- Scaffold marker key `_fixture_admission_marker` is present and is
  a non-empty string containing both substrings `"harness-internal"`
  and `"fixture-admission"` (case-insensitive).
- Every required field is present:
  - `fixture_set_id`
  - `fixture_classes`
  - `content_hashes`
  - `synthetic_only`
  - `real_benchmark_data`
  - `admission_authority_decided`
  - `selection_made`
- `synthetic_only is True`. The scaffold explicitly requires the
  fixture set to be marked synthetic-only; real benchmark data
  admission is out of scope under this scaffold.
- `real_benchmark_data is False`. The scaffold explicitly forbids
  any record that claims to admit real benchmark data; real data
  admission requires a separate future Codex packet that resolves
  OQ-035 (golden intent set construction) and OQ-049 (broader
  dataset suite ownership).
- `admission_authority_decided is False`. OQ-057 (configuration
  registration authority) remains OPEN; the scaffold explicitly
  forbids any record that claims authority has been decided.
- `selection_made is False`.
- No phrase from `harness.review_package.FORBIDDEN_PHRASES` appears
  anywhere in record string scalars.
- No phrase from `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
  appears anywhere in record string scalars.

The fixture admission record is observation-only. It does not
constitute admission authority. It does not promote any fixture to
real benchmark status. It does not bypass OQ-035 or OQ-049.

## 5. Stage 0 Readiness Review Boundary

The Stage 0 readiness reviewer lives at
`harness/readiness_review.py` and exposes one public function:

```
review_stage0_readiness(fixture_admission_record,
                        candidate_adapter_record,
                        event_log) -> dict
```

Behavior:

- Accepts already-loaded dicts only. Does not read files. Does not
  write files.
- Validates the fixture admission record per Section 4. Halts before
  raising on every rejection path.
- Delegates candidate adapter record validation to
  `harness.candidate_adapter_contract.validate_candidate_adapter_record(...)`.
  That function performs its own halt-and-raise rejection ordering.
- On success records a `stage0_readiness_reviewed` event into
  `event_log` and returns a fresh dict.
- Any validation failure halts before any readiness dict is
  returned. A candidate adapter rejection propagates the exception
  and prevents the Stage 0 readiness result from being assembled.

Returned dict (exactly the eleven allowed top-level keys):

- `review_kind`: literal string `"stage0_readiness_review"`.
- `stage0_ready`: literal `True` on success.
- `fixture_set_id`: pass-through from the fixture admission record.
- `candidate_adapter_id`: pass-through from the candidate adapter
  record.
- `configuration_id`: pass-through from the candidate adapter
  record.
- `fixture_class_count`: integer count of the fixture admission
  record's `fixture_classes` list.
- `candidate_plane_count`: integer count of the candidate adapter
  record's `planes_declared` list.
- `selection_made`: literal `False`. The scaffold does not make
  selections; Stage 0 readiness does not promote the system into
  any selection state.
- `measurement_authorized`: literal `False`. Stage 0 readiness is
  not authorization to measure; measurement requires a separate
  future Codex packet that authors the metric harness scaffold
  (the WO-41 / WO-42 Section 13 Shape C, or its successor).
- `real_benchmark_authorized`: literal `False`. Stage 0 readiness
  is not authorization for real benchmark execution; real execution
  requires its own future Codex packet, distinct from the metric
  scaffold packet.
- `readiness_note`: literal observation-only string referencing
  this document and the Indexing Excellence Gate.

No additional top-level key is emitted. No measurement is computed.
No quality / performance / operational signal is produced.

## 6. Event And Halt Behavior

Success events recorded into `event_log`:

- `candidate_adapter_record_validated` (per the contract validator,
  Section 3).
- `stage0_readiness_reviewed` (per the Stage 0 reviewer, Section 5).
  The candidate adapter validation event is always recorded before
  the Stage 0 readiness reviewed event on a successful path.

Halt events recorded into `event_log` (before any exception is
raised):

- Candidate adapter contract halt reasons:
  `candidate_adapter_non_object`,
  `candidate_adapter_missing_marker`,
  `candidate_adapter_invalid_marker`,
  `candidate_adapter_missing_field`,
  `candidate_adapter_declares_selection`,
  `candidate_adapter_declares_production_registration`,
  `candidate_adapter_declares_real_adapter`,
  `candidate_adapter_unknown_plane`,
  `candidate_adapter_forbidden_language`,
  `candidate_adapter_forbidden_claim`.
- Fixture admission halt reasons:
  `fixture_admission_non_object`,
  `fixture_admission_missing_marker`,
  `fixture_admission_invalid_marker`,
  `fixture_admission_missing_field`,
  `fixture_admission_not_synthetic_only`,
  `fixture_admission_declares_real_benchmark_data`,
  `fixture_admission_declares_authority_decision`,
  `fixture_admission_declares_selection`,
  `fixture_admission_forbidden_language`,
  `fixture_admission_forbidden_claim`.

The halt-and-raise behavior matches the WO-19 / DC-022 halt boundary:
every rejection records an explicit halt event before the matching
named exception is raised. The halt is observable to the caller via
`event_log.events` regardless of whether the caller catches the
exception or lets it propagate.

## 7. Non-Selection And Non-Measurement Guarantees

The WO-43 / WO-44 scaffold preserves every prior non-selection and
non-measurement boundary:

- No candidate adapter record may claim `selection_made is True`,
  `production_registration is True`, or `real_adapter is True`.
  All three are rejected with named exceptions.
- No fixture admission record may claim `synthetic_only is False`,
  `real_benchmark_data is True`, `admission_authority_decided is True`,
  or `selection_made is True`. All four are rejected with named
  exceptions.
- The Stage 0 readiness dict's `measurement_authorized` and
  `real_benchmark_authorized` are literal `False` on every
  successful path.
- The Indexing Excellence Gate (`00-controller-checklist.md`
  Section K) continues to govern selection unconditionally. Stage 0
  readiness does not promote the system into any selection state,
  and no aggregate count or boolean produced by the scaffold may
  select a winner by itself.
- The WO-19 / DC-022 halt invariant ratified at WO-36 review
  continues to hold. The scaffold does not call
  `harness.contract_runner.ContractRunner.record_measurement(...)`,
  so no measurement event is emitted.
- The WO-21 plane separation surface is preserved. The validator
  rejects any `planes_declared` entry that is not in the canonical
  five-plane set.

## 8. Relationship To WO-41 / WO-42

`ai-search/41-42-real-benchmark-start-contract.md` is the integration
document that records the admission, metric policy, and execution
protocol boundaries at integration level. WO-43 / WO-44 is the
first executable scaffold that sits inside that contract:

- The candidate adapter contract validator (Section 3) is the
  smallest implementation surface for the admission rules recorded
  in `41-42-real-benchmark-start-contract.md` Section 4 (Candidate
  Adapter Admission Boundary) and Section 5 (Candidate Adapter
  Non-Selection Rule). It rejects every record that violates either
  rule before any Stage 0 readiness output is produced.
- The fixture admission scaffold boundary (Section 4) is the
  smallest implementation surface for the fixture admission
  evidence requirement recorded in
  `41-42-real-benchmark-start-contract.md` Section 9 (Required
  Evidence Before First Real Run, item "Fixture admission
  evidence"). It enforces synthetic-only, no real benchmark data,
  no authority decision, and no selection claim.
- The Stage 0 readiness reviewer (Section 5) is the smallest
  implementation surface for the staged execution protocol
  recorded in `41-42-real-benchmark-start-contract.md` Section 8,
  step 1 ("validate fixture admission") and step 2 ("validate
  candidate adapter registration"). It does not implement step 3
  (run contract-safety checks), step 4 (collect measurements),
  step 5 (assemble human review package), or step 6 (Codex review
  under Indexing Excellence Gate); those remain out of scope under
  this scaffold and require their own future Codex packets.

WO-43 / WO-44 does not change any state recorded in
`41-42-real-benchmark-start-contract.md` Section 3 (Current Readiness
State). After WO-43 / WO-44 close, the readiness gate states remain:

| Gate | State |
|------|-------|
| scaffold-ready | YES |
| artifact-ready | YES |
| review-summary-ready | YES |
| real-benchmark-ready | NO |

`real-benchmark-ready` remains NO. The eight blockers recorded in
`39-40-batch-review-and-benchmark-readiness.md` Section 10 remain
active. WO-43 / WO-44 discharges a portion of blocker #4 ("no
execution protocol for real benchmark runs") at the Stage 0 scaffold
level only; blocker #4 in full requires Stages 1 through 5 of
`14-benchmark-execution-plan.md` to be scaffolded and exercised, and
each of those requires its own Codex packet.

## 9. What This Resolves

WO-43 / WO-44 resolves the following at scaffold level:

- Records a scaffold-level candidate adapter admission contract that
  any future real adapter must satisfy at the scaffold-record level.
- Records a scaffold-level fixture admission boundary that any
  future real fixture admission record must satisfy at the
  scaffold-record level.
- Records a scaffold-level Stage 0 readiness review that exercises
  both record validations in one pass and surfaces the result as a
  fixed eleven-field observation-only dict.
- Adds DC-044 to the trackers.
- Adds two named events to the observable event surface:
  `candidate_adapter_record_validated` and
  `stage0_readiness_reviewed`.
- Adds two scaffold-internal toy fixture records that the tests
  exercise end-to-end.

## 10. What Remains Unresolved

WO-43 / WO-44 does not resolve:

- The eight blockers recorded in
  `ai-search/39-40-batch-review-and-benchmark-readiness.md` Section
  10. Blocker #4 ("no execution protocol for real benchmark runs")
  is discharged at the Stage 0 scaffold level only; Stages 1
  through 5 remain out of scope.
- OQ-035 (golden intent set construction).
- OQ-049 (broader dataset suite ownership).
- OQ-056 (run artifact retention / storage policy).
- OQ-057 (configuration registration authority). The scaffold
  explicitly REQUIRES `admission_authority_decided is False`,
  which honors the open question rather than preempting it.
- OQ-070 (broader scope).
- OQ-075 (dependency policy beyond the first scaffold). The
  scaffold imports only Python stdlib and harness-internal symbols.
- OQ-076 (production artifact contracts).
- RK-039 (benchmark dataset contamination by production user
  feedback or recent traces; continues to apply unchanged and is
  not duplicated).
- The architecture selection decision (gated by the Indexing
  Excellence Gate and by a separate future Codex-authored selection
  Work Order).
- The `"score"` / `"scoring"` forbidden-language consolidation
  flagged by Codex at WO-39 / WO-40 review. The candidate adapter
  contract module uses only the canonical
  `harness.review_package.FORBIDDEN_PHRASES`; the test file
  applies the local-mirror extension (`+ ("score","scoring")`)
  to the readiness dict scan, consistent with the WO-35 / WO-39 /
  WO-40 pattern.

## 11. Recommended Next Packet

Codex retains all authority over the next packet. Claude's
recommendation, recorded here for forward-looking technical
judgment:

The next executable packet should pick one of the remaining
pre-measurement scaffolding shapes from
`ai-search/41-42-real-benchmark-start-contract.md` Section 13. The
recommended order is:

1. **Stage 1 contract-safety pass scaffolding (discharges part of
   blocker #4 step 3).** Author a scaffold-internal module that,
   given a Stage 0 readiness result, runs a fixed set of
   scaffold-internal contract-safety checks against the candidate
   adapter record and the fixture admission record, and records
   pass / fail per check in a result dict. Observation only; no
   real adapter is invoked.

2. **Contract-safety-pass metric observation scaffolding
   (WO-41 / WO-42 Section 13 Shape C, discharges part of blocker
   #3).** Author a scaffold-internal observation module that
   records the contract-safety pass / fail per registered
   configuration in a shape the future WO-12R Stage 1 measurement
   record can consume.

The two are independent; either can be the next packet. Combining
them in one packet would mix Stage 1 scaffolding with the
contract-safety metric observation; that combination is acceptable
ONLY if the packet explicitly records that "Stage 1 contract-safety
pass" is the only metric family produced, and that no quality /
performance / operational measurement is authored. Otherwise the
packets should remain separate.

Real benchmark execution authorization remains a separate future
packet that depends on Stages 1 through 5 each being scaffolded
and approved, plus OQ-056 and OQ-076 being explicitly resolved or
explicitly carried open with documented mitigations.

## 12. Forbidden Scope

WO-43 / WO-44 is forbidden from doing any of the following:

- Modifying any existing harness implementation module. The two
  allowed new modules are `harness/candidate_adapter_contract.py`
  and `harness/readiness_review.py`. Every other harness module
  remains byte-identical to its WO-41 / WO-42 close state.
- Modifying any existing test file under `harness/tests/`.
- Modifying any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Authoring a real adapter, a real fixture admission process, a
  real metric, a real benchmark step, or any real retrieval /
  indexing / ranking implementation.
- Performing real benchmark execution.
- Collecting quality / performance metrics.
- Scoring, ranking, or declaring any configuration a winner / best /
  production-ready / recommended.
- Authoring a production manifest schema, contract, retention
  policy, storage policy, immutability policy, access-control
  policy, or registration mechanism.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding any third-party dependency.
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

## 13. Out Of Scope

The following remain explicitly out of scope for WO-43 / WO-44 and
require separate Codex-authored Work Orders whose scope, allowed
files, required content, forbidden scope, acceptance criteria, and
evidence requirements are explicit at issue time:

- Real benchmark execution.
- Stage 1 contract-safety pass scaffolding (recommended next
  packet, Section 11).
- Stage 2 / 3 / 4 measurement scaffolding (quality, performance,
  operational).
- Stage 5 Human Architecture Review Package scaffolding.
- Real candidate retrieval adapter authoring.
- Real fixture admission / ownership process (OQ-035, OQ-049).
- Production artifact schema or contract (OQ-076).
- Retention / storage / immutability / access-control policy
  (OQ-056).
- Production registration mechanism (OQ-057).
- Architecture / vendor / library / index family / ANN backend /
  neural re-scorer / retrieval family / ablation cell / multi-stage
  selection.
- CLI, entry point, console script, or shell wrapper.
- Dependency policy beyond the first scaffold (OQ-075).
- Broader scope process (OQ-070).
- Wiring
  `harness.contract_runner.ContractRunner.record_measurement(...)`
  into `harness.dry_run.run_toy_dry_run(...)`. Until that wiring
  exists, `measurement_recorded_count` continues to accurately
  report zero under both pass and contract-failure paths.
- Consolidating the `"score"` / `"scoring"` forbidden-language
  extension into the canonical
  `harness.review_package.FORBIDDEN_PHRASES`. The local mirror
  pattern remains in place pending a separate future Codex packet.
