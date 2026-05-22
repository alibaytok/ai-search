# ai-search - Real Benchmark Start Contract

Document type: Phase 4 / Phase 9 / Real benchmark start contract boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes - documentation-only; real-benchmark-ready remains NO
Work Order: WO-41 / WO-42 (consolidated)

---

## 1. Purpose

This document records the integrated contract that governs the
transition from scaffold-ready / artifact-ready / review-summary-ready
(the close state of WO-39 / WO-40) toward real benchmark execution.

It is a documentation-only document. It does not author code, does
not run a benchmark, does not implement any adapter, does not collect
metrics, and does not select any architecture, vendor, library, index
family, ANN backend, neural re-scorer, retrieval family, ablation
cell, or multi-stage variant.

The document's value is integrative. WO-11 / `13-retrieval-benchmark-framework.md`,
WO-12R / `14-benchmark-execution-plan.md`, WO-21 /
`21-retrieval-adapter-contract.md`, and WO-39 / WO-40 /
`39-40-batch-review-and-benchmark-readiness.md` already record most
of the constituent boundaries. WO-41 / WO-42 pulls them onto a single
reading surface, names the three concrete admission rules that the
next code packet must respect (candidate-adapter admission, metric
policy, execution protocol), records what remains unresolved, and
recommends the next executable Work Order at the granularity the
Indexing Excellence Gate can audit.

## 2. Why WO-41 / WO-42 Is Consolidated

Codex consolidated WO-41 (real-benchmark-start adapter and metric
contract) and WO-42 (real-benchmark-start execution protocol and next
packet recommendation) into a single execution packet to reduce Work
Order fragmentation. The two would otherwise share:

- the same documentation-only allowed-files list;
- the same upstream cross-references (WO-11, WO-12R, WO-21,
  WO-39 / WO-40);
- the same reader audience (Codex deciding what concrete next
  Codex packet to author);
- the same point-in-time semantics ("what must the next packet
  satisfy before any real run?").

Splitting them would add packet overhead without changing the
evidence the integrated record carries.

The consolidation is also a deliberate signal: WO-41 / WO-42 is the
last documentation-only contract before real benchmark start. It
does not authorize real work; the next Codex packet must.

## 3. Current Readiness State

At WO-39 / WO-40 close (verified state: 205 / 205 tests pass), the
recorded benchmark readiness gate (per
`39-40-batch-review-and-benchmark-readiness.md` Section 9) is:

| Gate | State |
|------|-------|
| scaffold-ready | YES |
| artifact-ready | YES |
| review-summary-ready | YES |
| real-benchmark-ready | NO |

WO-41 / WO-42 does not change any of these states. WO-41 / WO-42 is
a documentation deliverable; it does not author code, does not run
tests beyond verification, and does not move the readiness gate.

The eight blockers recorded in
`39-40-batch-review-and-benchmark-readiness.md` Section 10 remain
active:

1. No real candidate retrieval adapter.
2. No real fixture admission / ownership process.
3. No metric policy or scoring protocol.
4. No execution protocol for real benchmark runs (documented at
   boundary level by `14-benchmark-execution-plan.md`, but no
   scaffolding under that boundary yet).
5. No artifact retention / storage / immutability / access-control
   policy (OQ-056 OPEN).
6. No production artifact contract (OQ-076 OPEN).
7. No architecture / vendor / library / index family / ANN backend /
   neural re-scorer / retrieval family / ablation cell / multi-stage
   variant / production-system selection.
8. Indexing Excellence Gate (`00-controller-checklist.md` Section K)
   still governs selection.

## 4. Candidate Adapter Admission Boundary

The substantive adapter contract is recorded in
`21-retrieval-adapter-contract.md`. This section restates only the
admission rules at integration-level.

A candidate adapter may be admitted for evaluation only. Admission
is the act of registering a candidate retrieval configuration as a
unit of evaluation in a future benchmark run (per
`14-benchmark-execution-plan.md` Section 4, Pre-Run Preparation
Boundary B). Admission boundary rules:

- A candidate adapter may be admitted for evaluation. Admission is
  not selection (per `21-retrieval-adapter-contract.md` Section 8).
- Registration is not production approval. Registration is a
  precondition for measurement, not a candidate-vs-official
  promotion event (per `14-benchmark-execution-plan.md` Section 4
  and `03-route-registry.md` boundary).
- A candidate adapter may fail contract-safety before any
  measurement. Contract-safety is the first measurement inside a run
  (per `14-benchmark-execution-plan.md` Section 6, Stage 1) and
  precedes every quality / performance / operational measurement;
  failure disqualifies the adapter for the run without producing
  any measurement against that adapter.
- Candidate adapter outputs must preserve the five WO-21 planes
  (per `21-retrieval-adapter-contract.md` Section 3): official
  route results, candidate route results, normalized material
  support results, source quality constraint observations, and
  trace / outcome observations (only when a future Codex packet
  admits the trace / outcome plane).
- Forbidden plane collapses (per
  `21-retrieval-adapter-contract.md` Section 4) apply in every
  degraded mode, including failure, partial availability, timeout,
  and any other non-success path.
- A real candidate adapter needs its own future allowed-files list
  and tests, authored under a separate Codex packet. WO-41 / WO-42
  does not author that packet's allowed-files list, does not author
  the adapter's interface, does not author the adapter's tests,
  and does not authorize real-system contact, network access, or
  any third-party dependency.

## 5. Candidate Adapter Non-Selection Rule

No vendor, library, index family, ANN backend, neural re-scorer,
retrieval family, ablation cell, multi-stage variant, or architecture
is approved by this document. Specifically:

- Admission of one or more candidate adapters by any future Codex
  packet does not constitute selection of any of those candidates.
- Selection is a Codex decision recorded by a separate future
  Codex-authored architecture selection Work Order, after the
  staged execution flow completes through Stage 5 (Human
  Architecture Review Package) and after the Indexing Excellence
  Gate is satisfied per recorded evidence (per
  `00-controller-checklist.md` Section K).
- Adapter registration, adapter conformance to the WO-21 plane
  separation surface, adapter passing contract-safety, adapter
  passing quality measurement, adapter passing performance
  measurement, and adapter passing operational measurement are
  each necessary preconditions and none of them, alone or
  together, constitutes selection.
- No aggregate score from any source may select a winner by
  itself (per `13-retrieval-benchmark-framework.md` Section 7 and
  Section 14, and `00-controller-checklist.md` Section K).

The rule operates at every observation surface: scaffold review
summaries, scaffold artifact snapshots, scaffold batch summaries,
future real adapter outputs, future real benchmark artifacts, and
any future review surface a Codex packet adds.

## 6. Metric Policy Boundary

The substantive metric framework is recorded in
`13-retrieval-benchmark-framework.md` Section 7 (quality,
performance, operational). This section restates only the policy
rules at integration-level.

- Contract pass / fail is not a quality metric. It is a
  disqualification gate (per
  `13-retrieval-benchmark-framework.md` Section 8 and
  `14-benchmark-execution-plan.md` Section 6, Stage 1).
- Measurement starts only after contract-safety passes. No
  quality / performance / operational measurement against a
  configuration may be recorded in the same run if contract-safety
  has failed for that configuration (per
  `14-benchmark-execution-plan.md` Section 6, and the WO-19 /
  DC-022 halt-before-measurement invariant ratified at WO-36
  review).
- Metrics must be observation-only until Codex selection review.
  Recorded metrics are evidence; they are not selection authority,
  not validation evidence for routes, and not architecture
  approval.
- No aggregate score may select a winner by itself. Selection
  remains a Codex decision recorded by a separate future Codex
  Work Order; benchmark scores are inputs to that decision, not the
  decision.

Minimum metric families that future execution must address (boundary
level; no formulas, no weights, no thresholds, no winner rules
authored here):

- **Contract-safety pass / fail.** Per
  `13-retrieval-benchmark-framework.md` Section 8: raw documents,
  normalized material, candidate routes, demoted / revoked / retired
  routes, popularity-elevated material, rank-elevated candidates,
  feedback-validated routes, and source-trust-elevated material
  must each be subject to recorded pass / fail tests.
- **Fixture-class coverage.** Per
  `13-retrieval-benchmark-framework.md` Section 3: golden intent,
  hard negative, boundary violation classes must each be exercised.
  Latency profile, update profile, and adversarial classes require
  separate Codex authorization at the point each is admitted.
- **Precision / false-positive behavior for hard negatives.** The
  rate at which hard-negative intents return material as if it were
  an official route is a recorded false-positive measurement.
- **Boundary-violation rejection behavior.** The rate at which
  boundary-violation intents trigger contract-safety failure (the
  expected behavior, per the WO-31 boundary-violations payload
  `expected_disqualification` markers) is a recorded measurement.
- **Latency / cost only after separate authorization.** Latency,
  throughput, memory, and cost measurement require their own Codex
  packet, including the latency profile set (per
  `13-retrieval-benchmark-framework.md` Section 9), realistic
  query mix, and cost projection scale. Until that packet is
  authorized, the metric family is named but not measured.
- **Reproducibility evidence.** Per
  `13-retrieval-benchmark-framework.md` Section 7.3 and Section 12:
  recorded state must suffice to replay a run.
- **Artifact integrity.** Per WO-27 / DC-030 and WO-37 / DC-040: the
  SHA-256 of every persisted run artifact must be recorded and
  verifiable on read. Retention / storage / immutability / access
  control remain blocked by OQ-056.

No formula, weight, threshold, or winner rule is authored under
WO-41 / WO-42. Substantive metric authority is owned by Codex.

## 7. Metric Non-Selection Rule

Restated for unambiguity:

- A passing metric does not select a configuration. Selection is a
  Codex decision recorded by a future Codex Work Order.
- An aggregate metric does not select a configuration. Aggregation
  authority is Codex's; the harness does not aggregate by default.
- A high metric does not promote a configuration to "best",
  "winner", "recommended", "production-ready", or "selected".
  These words are blocked at every scaffold output surface today
  (per the WO-35-extended forbidden language list) and remain
  blocked for any future real-benchmark output unless a future
  Codex packet explicitly authorizes them in a specified form.
- A metric regression does not by itself remove a candidate from
  consideration; it is recorded as evidence for human review (per
  `13-retrieval-benchmark-framework.md` Section 12 and
  `14-benchmark-execution-plan.md` Section 10).

## 8. Real Benchmark Execution Protocol Boundary

The substantive execution plan is recorded in
`14-benchmark-execution-plan.md` Sections 3-10. This section
restates only the staging rules at integration-level.

Real benchmark execution requires a future Codex packet (or
sequence of packets). Real execution must be staged. The staging
parallels `14-benchmark-execution-plan.md` Stage 0 through Stage 5:

1. **Validate fixture admission.** Confirm dataset fixtures are
   present, content-hashed, version-pinned, and Codex-owned
   admission events are recorded. (Per
   `14-benchmark-execution-plan.md` Section 3 and Stage 0;
   OQ-035 / OQ-049 governance.)
2. **Validate candidate adapter registration.** Confirm at least
   one candidate adapter is registered per
   `14-benchmark-execution-plan.md` Section 4 with its retrieval
   family, planes covered, parameter set, constraint mode, rerank
   mode, dependency version pins, and operational profile
   recorded. (Per Stage 0; OQ-057 governance.)
3. **Run contract-safety checks.** Per
   `13-retrieval-benchmark-framework.md` Section 8 and Stage 1.
   Pass / fail; failure disqualifies the configuration for the
   run and halts measurement against that configuration.
4. **Only then collect measurements.** Quality (Stage 2),
   performance (Stage 3), and operational (Stage 4) measurements
   run only against configurations that passed contract-safety
   in step 3.
5. **Assemble human review package.** Stage 5: Human Architecture
   Review Package per `14-benchmark-execution-plan.md` Section 10,
   including every recorded measurement, every recorded halt,
   every recorded disqualification, the reproducibility evidence,
   and the artifact integrity attestations.
6. **Codex review under Indexing Excellence Gate.** Selection
   review per `00-controller-checklist.md` Section K. Selection
   is a Codex decision recorded by a separate future Codex Work
   Order; passing through Stage 5 does not constitute selection.

Any halt prevents later-stage measurement for that candidate /
configuration in the same run. This is the WO-19 / DC-022 halt
invariant ratified at WO-36 review, extended forward to every
future real-benchmark execution.

Artifact retention / storage / immutability / access-control
remains blocked by OQ-056 unless explicitly resolved later.
Production artifact contract remains blocked by OQ-076 unless
explicitly resolved later. The staged execution protocol does not
preempt either open question; it depends on each being resolved
before durable artifacts beyond the scaffold-internal `tempfile`
boundary are written.

## 9. Required Evidence For First Real Run

Synthesized from `13-retrieval-benchmark-framework.md` Section 14,
`14-benchmark-execution-plan.md` Sections 3-10, and
`21-retrieval-adapter-contract.md` Sections 6-9.

Before the first real benchmark run is authorized, the future
execution packet must distinguish two evidence classes:

- **Pre-run admission evidence.** Evidence that must exist before
  the run starts.
- **Run-produced evidence.** Evidence that must be produced by the
  run in the documented stage order.

The following evidence contract must be satisfied:

- **Fixture admission evidence.** Each admitted fixture (initially
  the WO-31 first-wave synthetic payloads or a real-data successor)
  carries a recorded admission event, a content hash, a version
  marker, provenance, and a recorded contamination check (per
  RK-039).
- **Candidate adapter registration evidence.** Each registered
  candidate adapter carries the WO-12R Section 4 registration
  fields (retrieval family, planes covered, parameter set,
  constraint mode, rerank mode, dependency version pins,
  operational profile). Registration is signed by a recorded
  Codex authority (OQ-057 OPEN).
- **Stage 0 readiness decision.** A recorded admissible /
  not-admissible decision per
  `14-benchmark-execution-plan.md` Section 5.
- **Stage 1 contract-safety record.** Run-produced evidence:
  a recorded pass / fail
  per contract-safety test per
  `13-retrieval-benchmark-framework.md` Section 8 for every
  registered configuration.
- **Stage 2 / 3 / 4 measurements.** Run-produced evidence,
  recorded against contract-safety passing configurations only,
  per the metric families named in Section 6 above and in
  `13-retrieval-benchmark-framework.md` Section 7.
- **Reproducibility evidence.** Run-produced evidence:
  recorded state sufficient to replay each run.
- **Artifact integrity evidence.** Run-produced evidence:
  SHA-256 of every persisted
  artifact, byte length of every persisted artifact, and the
  caller-provided output path verbatim (per WO-27 / DC-030 and
  WO-37 / DC-040).
- **Halt and disqualification log.** Run-produced evidence:
  every halt event with
  classification, every disqualification event with the
  configuration identifier and the violated test.
- **Forbidden-language hygiene attestation.** Run-produced
  evidence: every recorded
  artifact passes the
  `harness.review_package.FORBIDDEN_PHRASES`-extended language
  scan and the `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
  scan.
- **No-mutation attestation.** Run-produced evidence:
  no file under `benchmark-fixtures/` is mutated during the run.

None of these evidence categories is recorded by WO-41 / WO-42
itself. WO-41 / WO-42 records that pre-run evidence must exist
before execution starts, and run-produced evidence must be
instrumented in the execution packet before the first real run is
authorized.

## 10. Relationship To Indexing Excellence Gate Section K

The Indexing Excellence Gate (`00-controller-checklist.md`
Section K, added under WO-13) continues to govern selection
unconditionally. WO-41 / WO-42 does not modify, narrow, broaden,
or suspend the gate. Specifically:

- "Best not proven = not selected" (Section K, opening principle)
  remains the canonical rule.
- "Good enough" is not acceptable.
- Market defaults are not evidence.
- "Vector DB plus reranker" is not a default answer.
- "Centralized single-index architecture" is not a default answer.
- If no candidate has cleared the gate, the review is recording
  that no selection is made (Section K, item 6).
- Contract-safety failures disqualify a configuration regardless
  of any quality or performance score (Section K, item 7;
  consistent with `13-retrieval-benchmark-framework.md` Section 8).
- An aggregate benchmark score cannot select a winner by itself
  (Section K, item 8).
- Ablation, cost, update / freshness, rollback, and reproducibility
  evidence are each required before any architecture is selected
  (Section K, items 9-11).
- Graph-constrained retrieval and multi-stage retrieval
  alternatives have been evaluated before any selection (Section
  K, item 12).
- Claude is blocked from describing the indexing scope as
  complete, best, or production-ready without explicit Codex
  approval based on recorded evidence (Section K, item 13).

WO-41 / WO-42 satisfies the gate's requirement that the review
record what is and is not proven, by deferring to WO-39 / WO-40
Section 9 (the readiness gate table) and naming `real-benchmark-ready: NO`
as the current state.

## 11. What This Packet Resolves

WO-41 / WO-42 resolves the following:

- Records, in one reading surface, the integrated real-benchmark-start
  contract. Future Codex packets that propose real benchmark work
  can be audited against this document in addition to the upstream
  WO-11 / WO-12R / WO-21 / WO-39 / WO-40 documents.
- Restates the admission-vs-selection distinction at integration
  level. The distinction is not new (WO-21 Section 8 records it),
  but the WO-41 / WO-42 doc co-locates the rule with the metric
  policy rule and the execution protocol rule so a single reader
  sees all three.
- Names a concrete recommendation for the next executable Work
  Order in Section 13.
- Records DC-043 under the trackers (`00-open-questions.md`).

## 12. What Remains Unresolved

WO-41 / WO-42 does not resolve:

- The eight WO-39 / WO-40 blockers (Section 3 above).
- OQ-035 (golden intent set construction).
- OQ-049 (broader dataset suite ownership).
- OQ-056 (run artifact retention / storage policy).
- OQ-057 (configuration registration authority).
- OQ-070 (broader scope).
- OQ-075 (dependency policy beyond the first scaffold).
- OQ-076 (production artifact contracts).
- RK-039 (benchmark dataset contamination by production user
  feedback or recent traces; the contamination concern continues
  to apply, not duplicated).
- The architecture selection decision (gated by the Indexing
  Excellence Gate and by a separate future Codex-authored
  selection Work Order).
- The `"score"` / `"scoring"` forbidden-language consolidation
  noted by Codex at WO-39 / WO-40 review. The extended list
  currently lives at module / test scope as a local mirror; a
  future Codex packet may consolidate it into
  `harness.review_package.FORBIDDEN_PHRASES`. WO-41 / WO-42 does
  not consolidate it, because that consolidation requires
  modifying `harness/review_package.py`, which is outside the
  WO-41 / WO-42 allowed-files list.

## 13. Required Next Executable Work Order

Codex retains all authority over the next packet. Claude's
recommendation, recorded here per the WO-41 / WO-42 packet
preamble's explicit invitation for forward-looking technical
judgment, is:

**The next executable Codex packet should be small, concrete, and
bound to exactly one of the eight WO-39 / WO-40 blockers.** The
risk of a wide multi-section packet is that "admitted" silently
becomes "selected" by reading habit; small packets keep the
Indexing Excellence Gate honest at every step.

Recommended candidate next-packet shapes, any one of which would
discharge exactly one blocker without architecting anything:

- **Candidate next packet shape A - Stage 0 readiness review
  scaffolding (discharges part of blocker #4).** Author a
  scaffold-internal `harness/readiness_review.py` (or equivalent)
  that, given a candidate adapter registration record and a
  fixture admission record (both still scaffold-internal stubs),
  produces an admissible / not-admissible boolean plus a halt
  event under the existing WO-19 / DC-022 halt boundary. No real
  adapter, no real fixture admission, no metric. The packet
  records what Stage 0 emits and which fields are required.

- **Candidate next packet shape B - candidate adapter interface
  contract scaffolding (begins blocker #1 at scaffold level).**
  Author a documentation-only contract test scaffold that records
  what a real candidate adapter must provide to be admitted, in
  the form of a contract test (no implementation). Allowed files:
  one new harness module plus its test plus a new boundary doc.
  The packet does not author a real adapter; it authors the
  admission contract test surface so any future real adapter has
  a fixed admission target.

- **Candidate next packet shape C - contract-safety-pass metric
  observation scaffolding (begins blocker #3 at scaffold level).**
  Author a scaffold-internal observation module that records the
  contract-safety pass / fail per registered configuration in a
  shape that the future WO-12R Stage 1 measurement record can
  consume. Observation only; no formula, no weight, no threshold,
  no winner rule.

If Codex chooses to combine, the safest pair is **shape A + part
of shape B** (Stage 0 readiness review plus the admission
contract test surface), because both are pre-measurement
scaffolding that share the candidate registration record shape
and neither authors a real adapter or a real metric. Pairing
shape A with shape C, or shape B with shape C, mixes pre-measurement
and measurement scaffolding and risks ambiguity about what
"admitted" means before contract-safety has been recorded.

**The packet that authorizes real benchmark execution must
remain separate from all three shapes above.** Real execution
must depend on shapes A, B, and C (or their equivalents) being
recorded as approved, plus OQ-056 and OQ-076 being explicitly
resolved or explicitly carried open with documented mitigations.

## 14. Forbidden Scope

WO-41 / WO-42 is forbidden from doing any of the following:

- Modifying any harness implementation file. The three allowed
  files are documentation / tracker only.
- Modifying any existing test file under `harness/tests/`.
- Modifying any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Running any benchmark (real or scaffold).
- Authoring any retrieval / indexing / ranking implementation.
- Authoring any real adapter.
- Authoring any metric formula, weight, threshold, or winner
  rule.
- Authoring a production artifact schema, contract, retention
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
  extension into `harness/review_package.py` (that consolidation
  would modify a forbidden file).
- Mutating corpus docs, route registry docs, validation evidence,
  source quality graph, intent trace store, candidate routes,
  or official routes.

## 15. Out Of Scope

The following remain explicitly out of scope for WO-41 / WO-42
and require separate Codex-authored Work Orders whose scope,
allowed files, required content, forbidden scope, acceptance
criteria, and evidence requirements are explicit at issue time:

- Real benchmark execution.
- Real metric collection, scoring protocol, or aggregation
  protocol.
- Real candidate retrieval adapter authoring.
- Stage 0 readiness review scaffolding (next-packet shape A
  from Section 13).
- Candidate adapter interface contract test scaffolding (next-packet
  shape B from Section 13).
- Contract-safety-pass metric observation scaffolding (next-packet
  shape C from Section 13).
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
  exists, `measurement_recorded_count` accurately reports zero
  under both pass and contract-failure paths (the WO-19 /
  DC-022 invariant ratified at WO-36 review).
- Consolidating the `"score"` / `"scoring"` forbidden-language
  extension into the canonical
  `harness.review_package.FORBIDDEN_PHRASES`. The local mirror
  pattern recorded at WO-39 / WO-40 close remains in place
  pending a separate future Codex packet.
