# ai-search - Batch Human Review Summary And Benchmark Readiness Gate

Document type: Phase 4 / Phase 9 / Scaffold review + readiness gate boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Approved with notes - real-benchmark-ready remains NO
Work Order: WO-39 / WO-40 (consolidated)

---

## 1. Purpose

This document records two consolidated deliverables authorized under
WO-39 / WO-40 (DC-042):

- A scaffold-only human review summary assembler at
  `harness/batch_review.py` that reduces the existing scaffold batch
  summary returned by `harness.batch_runner.run_payload_batch(...)`
  to a minimal observation-only review summary for the human reviewer
  (Codex).
- A benchmark readiness gate that records, at this point in time,
  what is proven by the scaffold, what is still not proven, and what
  remains before real benchmark execution can begin.

Both deliverables are scaffold-internal only. Neither performs real
benchmark execution, real metric collection, real adapter execution,
or architecture selection. Neither closes any open question. The
Indexing Excellence Gate (`00-controller-checklist.md` Section K)
continues to govern selection.

## 2. Consolidation Rationale

Codex consolidated WO-39 (human review summary) and WO-40
(benchmark readiness gate) into a single execution packet to reduce
Work Order fragmentation. The two deliverables share:

- the same input boundary (the existing scaffold batch summary shape
  locked under WO-35 / WO-36 / WO-37);
- the same reviewer audience (Codex at human review time);
- the same point-in-time semantics ("what does the scaffold know
  right now?").

Splitting them into separate packets would add packet overhead
without changing the evidence each one carries. The consolidation
makes the gate document immediately co-located with the review
summary it summarizes, so Codex can read both in a single review
pass.

## 3. Human Review Summary Boundary

The review summary is a minimal observation-only reduction of the
batch summary. The public surface is one function in
`harness/batch_review.py`:

```
assemble_batch_review_summary(batch_summary) -> dict
```

The function takes the existing scaffold batch summary returned by
`run_payload_batch(...)` and returns a fresh dict with exactly the
eight allowed top-level keys named in Section 5. The input batch
summary is not modified.

The review summary is not a metric collector, not a scoring engine,
not a ranking engine, not a winner declarer, not a best declarer,
not a production-readiness declarer, and not a recommendation
producer. It does not treat contract pass as validation evidence
and it does not select any architecture. It is a small fixed set
of counts plus a literal status-string view of the per-run
summaries the runner has already assembled.

## 4. Batch Review Input Boundary

The function accepts the existing scaffold batch summary returned by
`run_payload_batch(...)`. The input must satisfy:

- The input is a dict.
- The input contains a `per_run_summaries` key.
- `per_run_summaries` is a list (possibly empty).
- The input's `selection_made` is not `True`. Missing,
  `False`, or `None` are all acceptable; only `True` is a rejection
  trigger.
- No string scalar inside the input contains any phrase from the
  WO-35-extended forbidden selection list
  (`harness.review_package.FORBIDDEN_PHRASES + ("score","scoring")`).
- No string scalar inside the input contains any phrase from
  `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`.

The five conditions are checked in order. The first violation
raises the matching named exception (see Section 6) before any
aggregation is computed.

## 5. Batch Review Output Boundary

On success the function returns a fresh dict with exactly the eight
allowed top-level keys:

- `review_kind`: literal string `"scaffold_batch_review_summary"`.
- `run_count`: integer length of `per_run_summaries`.
- `fixture_classes`: ordered list of `fixture_class` strings from
  each per-run entry (per-entry order preserved).
- `contract_status_counts`: dict with exactly two integer keys,
  `"passed"` (count of per-run entries with
  `contract_status == "passed"`) and `"failed"` (count with
  `contract_status == "failed"`).
- `snapshot_counts`: dict with exactly two integer keys,
  `"written"` (count with `snapshot_written is True`) and
  `"not_written"` (count with `snapshot_written is False`).
- `measurement_recorded_count`: integer count of per-run entries
  with `measurement_recorded is True`.
- `selection_made`: always literal `False`. The scaffold does not
  make selections; the function will not assemble a summary for any
  input that claims `selection_made is True`.
- `review_note`: literal observation-only string referencing this
  document and the Indexing Excellence Gate.

No additional top-level key is emitted. No per-run content beyond
the listed fields is propagated. No metric, score, rank, threshold,
or selection signal is computed.

Per WO-19 / DC-022 ratified at WO-36 review:
`measurement_recorded_count` is zero under both the clean-run and
the contract-failure paths in the current scaffold because
`run_toy_dry_run(...)` never calls
`harness.contract_runner.ContractRunner.record_measurement(...)`. A
future Codex packet that wires real measurement collection into the
dry-run will cause the count to rise; the field is named now so
that future change is observable without schema drift.

## 6. Rejection Behavior

The function raises one of six named exceptions, in order:

1. `NonDictBatchSummary` - the input is not a dict.
2. `MissingPerRunSummaries` - the input lacks `per_run_summaries`.
3. `NonListPerRunSummaries` - `per_run_summaries` exists but is not
   a list.
4. `SelectionMadeInBatchSummary` - the input claims
   `selection_made is True`.
5. `ForbiddenLanguageInBatchSummary` - some string scalar inside
   the input contains a phrase from the WO-35-extended forbidden
   selection list.
6. `ForbiddenClaimInBatchSummary` - some string scalar inside the
   input contains a phrase from
   `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`.

Each exception is raised before any aggregation. No partial review
summary is ever returned.

## 7. What Is Now Proven

As of WO-39 / WO-40 close, the following are proven by recorded
tests:

- **Scaffold readiness.** The scaffold dry-run, contract runner,
  mock adapter, manifest loader, payload loader, batch runner,
  artifact snapshot writer, and review summary assembler all run
  end-to-end against scaffold-internal toy fixtures and the three
  WO-31 synthetic payload files. 205 tests pass under
  `python -B -m unittest discover -s harness/tests -v`.
- **Artifact readiness.** The WO-27 / WO-37 artifact snapshot
  writer produces deterministic UTF-8 JSON files at caller-provided
  paths and returns SHA-256 / byte-length metadata that matches the
  on-disk bytes. The WO-38 combined invocation test exercises both
  per-run snapshots (three files) and the batch summary snapshot
  (one file) in a single end-to-end run.
- **Review summary readiness.** The WO-39 / WO-40 review summary
  produces a fixed eight-field observation-only view over the batch
  summary. Every rejection path is named and tested. No forbidden
  selection phrase and no forbidden claim phrase can appear in the
  output. Contract pass status is surfaced as a count, not treated
  as validation evidence.
- **No-mutation invariants.** Every test that touches
  `benchmark-fixtures/` asserts per-file SHA-256 before vs. after.
  The WO-38 invocation test additionally asserts that every
  non-`__pycache__` file under `harness/` is byte-identical before
  vs. after the batch invocation.
- **Plane separation hygiene.** The WO-21 five planes are honored
  by the payload loader, the review package assembler, the artifact
  snapshot writer, the batch runner, and the review summary
  assembler. No plane collapse is introduced by any scaffold module.
- **Forbidden-language hygiene.** Every scaffold-emitted artifact
  (review package, snapshot, batch summary, review summary) is
  asserted free of `harness.review_package.FORBIDDEN_PHRASES` plus
  the WO-35-extended `"score"` / `"scoring"` and free of
  `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`. Contract status
  is surfaced as literal `"passed"` / `"failed"` only; these strings
  contain no forbidden phrase.

## 8. What Is Still Not Proven

As of WO-39 / WO-40 close, the following are explicitly not proven:

- **No real benchmark has been run.** Every test exercises a
  scaffold-internal toy dry-run and a mock adapter. No real
  retrieval, indexing, ranking, or evaluation has happened.
- **No real fixture admission process exists.** The three WO-31
  first-wave synthetic payloads (`benchmark-fixtures/<class>/wave-001.json`)
  are scaffold-internal synthetic payloads with explicit
  `not_benchmark_evidence: true` markers. They are not real
  benchmark data and have no admission / qualification / ownership
  process.
- **No real adapter exists.** `harness/mock_adapter.py` is a toy
  scaffold; no real retrieval or ranking code lives in the repo.
- **No metric policy exists.** No quality / performance metric is
  collected by any scaffold module. The Indexing Excellence Gate
  requires ablation, cost, update / freshness, rollback, and
  reproducibility evidence, none of which are present.
- **No execution protocol for real benchmark runs exists.** The
  WO-14 benchmark execution plan is documentation only.
- **No artifact retention / storage / immutability /
  access-control policy exists (OQ-056 OPEN).** Snapshot files
  written by the scaffold live only in caller-provided temp
  directories under `tempfile.TemporaryDirectory()`.
- **No production artifact schema or contract exists (OQ-076
  OPEN).** The on-disk JSON shape is the scaffold-internal review
  package / batch summary shape; it is not a production contract.
- **No architecture / vendor / library / index family / ANN
  backend / neural re-scorer / retrieval family / ablation cell /
  multi-stage variant / production system has been selected.** No
  selection event has occurred and no candidate has cleared the
  Indexing Excellence Gate (Section K of
  `00-controller-checklist.md`).
- **No registration mechanism / registration authority exists
  (OQ-057 OPEN).** The toy registered-configuration observation
  flow is scaffold-internal observation only.
- **No dependency policy beyond the first scaffold exists
  (OQ-075 OPEN).** The harness is stdlib-only.
- **No golden intent set construction process exists (OQ-035
  OPEN).** The two-entry-per-class WO-31 synthetic payloads are
  scaffold-internal stubs.
- **No broader dataset suite ownership process exists (OQ-049
  OPEN).** OQ-049 remains the open canonical question for
  dataset ownership at scale.
- **No broader scope process exists (OQ-070 OPEN).** Each step
  beyond the scaffold requires an explicit Codex packet.
- **The contamination concern (RK-039) continues to apply.** No
  data from production user feedback, recent traces, user data,
  private source material, or unqualified internet content has been
  admitted to `benchmark-fixtures/`, and no admission process
  authorizes such admission.

## 9. Benchmark Readiness Gate

At WO-39 / WO-40 close, the recorded gate state is:

| Gate | State | Source |
|------|-------|--------|
| scaffold-ready | YES | `python -B -m unittest discover -s harness/tests -v` passes; every scaffold module has tests; every no-mutation invariant holds. |
| artifact-ready | YES | WO-27 / WO-37 writer produces deterministic snapshots; WO-38 invocation test exercises both per-run and batch summary snapshots end-to-end. |
| review-summary-ready | YES | WO-39 / WO-40 review summary assembles a fixed eight-field observation-only view; every rejection path is named and tested; forbidden-language hygiene holds. |
| real-benchmark-ready | **NO** | See Section 10. |

The Indexing Excellence Gate (Section K of
`00-controller-checklist.md`) continues to govern selection. "Best
not proven = not selected." No aggregate benchmark score may select
a winner by itself, and contract-safety failures disqualify a
configuration regardless of any other signal.

## 10. Remaining Blockers Before Real Benchmark Execution

`real-benchmark-ready: NO` because every one of the following
blockers remains open:

1. **No real candidate retrieval adapter exists.** The only
   adapter in the repo is `harness/mock_adapter.py`, a scaffold
   toy. A real adapter requires a Codex-authored Work Order
   defining the adapter interface, the registration mechanism, the
   dependency policy interaction (OQ-075), the candidate vs.
   official boundary preservation, and the contract-safety
   integration.
2. **No real fixture admission / ownership process exists.** The
   WO-31 first-wave synthetic payloads are scaffold-internal. A
   real fixture admission process requires Codex packets that
   resolve OQ-035 (golden intent set construction) and OQ-049
   (broader dataset suite ownership), and that record the
   contamination boundary (RK-039) at the admission gate, not only
   at the documentation gate.
3. **No metric policy or scoring protocol exists.** No metric is
   computed today, by design (contract-status counts are not
   metrics). The Indexing Excellence Gate requires ablation, cost,
   update / freshness, rollback, and reproducibility evidence; a
   real metric policy is the prerequisite for that evidence and
   requires a Codex packet.
4. **No execution protocol for real benchmark runs exists.**
   `14-benchmark-execution-plan.md` is documentation only. A real
   execution protocol requires Codex authorization of the staged
   flow, the per-stage halt rules, the per-stage evidence records,
   and the Stage 5 Human Architecture Review Package boundary.
5. **No artifact retention / storage / immutability /
   access-control policy exists (OQ-056 OPEN).** Snapshot files
   are scaffold-internal and live only inside temp directories.
   A real benchmark run would produce durable artifacts that need
   policy.
6. **No production artifact contract exists (OQ-076 OPEN).** The
   on-disk JSON shape is the scaffold dict shape; it is not a
   contract for a real benchmark or for production routes.
7. **No architecture, vendor, library, index family, ANN backend,
   neural re-scorer, retrieval family, ablation cell, multi-stage
   variant, or production system has been selected.** No
   candidate has cleared the Indexing Excellence Gate; no aggregate
   score from any source may select a winner by itself; no Codex
   selection event has occurred.
8. **The Indexing Excellence Gate (Section K) still governs
   selection.** "Best not proven = not selected" is the canonical
   rule. The scaffold does not satisfy the gate, and the scaffold
   was not designed to satisfy the gate. A separate Codex packet
   must define what evidence the gate accepts and what evidence
   the future real benchmark must produce.

Each of the eight blockers is independent; none can be discharged
silently by accumulated scaffold work, by usage signals, by
benchmark execution alone, or by any phrase in any scaffold
artifact.

## 11. Required Next Packet For Real Benchmark Start

The next Codex packet that proposes real benchmark start must, at
minimum, address every one of the following before any real
execution occurs:

- Author or wire a real candidate retrieval adapter, with explicit
  allowed-files list, dependency policy interaction (OQ-075), and
  contract-safety integration.
- Author or formalize a real fixture admission process, with
  explicit allowed-files list and a recorded contamination boundary
  (RK-039) at the admission gate.
- Author a metric policy and a scoring protocol that explicitly
  satisfy the Indexing Excellence Gate's ablation / cost / update /
  freshness / rollback / reproducibility requirements, with a
  Codex-owned sufficiency bar named at packet-issue time.
- Author an execution protocol for real benchmark runs that
  reflects the staged flow in `14-benchmark-execution-plan.md` and
  the WO-12R / WO-12R2 Stage 5 Human Architecture Review Package
  boundary.
- Resolve or explicitly leave open OQ-056 (retention / storage /
  policy), OQ-076 (production artifact contract), OQ-057
  (registration authority), OQ-075 (dependency policy), OQ-035
  (golden intent set construction), OQ-049 (broader dataset
  ownership), and OQ-070 (broader scope).
- Restate that selection still requires a separate Codex
  selection event; benchmark execution does not by itself
  constitute selection.

Until that next packet is issued and approved, no real benchmark
execution is authorized. The scaffold's current state is the
ceiling of what is proven.

## 12. Forbidden Scope

The WO-39 / WO-40 consolidated packet is forbidden from doing any
of the following:

- Modifying any harness implementation module other than adding
  `harness/batch_review.py`. In particular, `harness/dry_run.py`,
  `harness/payload_loader.py`, `harness/artifact_snapshot.py`,
  `harness/batch_runner.py`, `harness/contract_runner.py`,
  `harness/review_package.py`, `harness/mock_adapter.py`,
  `harness/manifest_loader.py`, and `harness/reproducibility.py`
  remain untouched.
- Modifying any existing test file. Specifically,
  `harness/tests/test_batch_artifact_invocation.py` and
  `harness/tests/test_batch_runner.py` remain untouched.
- Modifying any payload file under `benchmark-fixtures/<class>/`,
  any `.gitkeep`, or `benchmark-fixtures/README.md`.
- Performing real benchmark execution.
- Scoring, ranking, or declaring any configuration a winner / best
  / production-ready / recommended.
- Authoring any real retrieval / indexing / ranking algorithm or
  any real adapter.
- Authoring a production artifact schema or contract.
- Authoring a retention / storage / immutability / access-control
  policy or a production registration mechanism.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding any third-party dependency.
- Introducing a CLI, entry point, console script, or shell wrapper.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076. All seven remain OPEN.
- Duplicating RK-039.
- Mutating corpus docs, route registry docs, validation evidence,
  source quality graph, intent trace store, candidate routes, or
  official routes.

## 13. Out Of Scope

The following remain explicitly out of scope for WO-39 / WO-40 and
require separate Codex-authored Work Orders whose scope, allowed
files, required content, forbidden scope, acceptance criteria, and
evidence requirements are explicit at issue time:

- Real benchmark execution.
- Real metric collection, scoring, ranking, or aggregation
  protocols.
- Real retrieval / indexing / ranking implementation.
- Real adapter integration.
- Production artifact schema or contract (OQ-076).
- Retention / storage / immutability / access-control policy
  (OQ-056).
- Production registration mechanism (OQ-057).
- Architecture / vendor / library / index family / ANN backend /
  neural re-scorer / retrieval family / ablation cell / multi-stage
  selection.
- CLI, entry point, console script, or shell wrapper.
- Golden intent set construction process (OQ-035).
- Broader dataset suite ownership process (OQ-049).
- Broader scope process (OQ-070).
- Dependency policy beyond the first scaffold (OQ-075).
- Wiring
  `harness.contract_runner.ContractRunner.record_measurement(...)`
  into `harness.dry_run.run_toy_dry_run(...)`. Until that wiring
  exists, `measurement_recorded_count` accurately reports zero
  under both pass and contract-failure paths.
- Moving the WO-35-extended `"score"` / `"scoring"` forbidden
  phrases from local-by-convention scope into
  `harness.review_package.FORBIDDEN_PHRASES`. The local mirror in
  `harness/batch_review.py` and in `harness/tests/test_batch_runner.py`
  is the current pattern; a future Codex packet may consolidate
  these copies into the canonical list.
