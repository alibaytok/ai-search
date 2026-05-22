# ai-search - Harness Scaffold Decision Lock

Document type: Phase 4 / Phase 9 / Harness scaffold decision lock
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-17

---

## 1. Purpose

This document records the Codex decisions that lock the minimum scaffold choices required before WO-18 minimal-scaffold implementation may proceed. It is documentation-level only. It is not harness implementation. It does not authorize benchmark execution, dataset creation, architecture selection, vendor selection, index selection, or production readiness. WO-18 (the planned minimal scaffold implementation packet) inherits this decision lock and is bounded by it.

WO-17 is still not harness implementation. No code is authored under WO-17. No scaffold files or directories are created. No third-party dependency is selected. No benchmark is run.

## 2. Codex Decisions

The following decisions are recorded as Codex-authored locks. They resolve the listed open questions and supply substantive content that the harness scaffold boundary (`16-benchmark-harness-scope.md`) and the harness implementation plan (`17-harness-implementation-plan.md`) deferred to Codex.

### 2.1 Runtime / Language

Python 3, standard library only.

Resolves OQ-072.

### 2.2 Repository Location

Root-level `harness/` directory, sibling to the documentation directory `ai-search/`. The expected absolute path is `C:\Projects\ai-search\harness\`. This corresponds to Option A described in `17-harness-implementation-plan.md` Section 4.

Resolves OQ-073.

### 2.3 Test Framework

Python standard-library `unittest`.

Resolves OQ-074. Consistent with the standard-library-only constraint in Section 2.1.

### 2.4 Dependency Policy

No third-party dependencies for the first scaffold. The scaffold uses only the Python 3 standard library.

Resolves OQ-075 for the first scaffold only. Longer-term dependency policy (review process, version pinning approach, vendored vs. published handling, transitive-dependency review beyond the first scaffold) remains owned by Codex and is tracked under the existing OQ-075.

### 2.5 Minimum Artifact Format Boundary

JSON may be used only for harness run artifacts and test fixtures under the scaffold. Schemas remain minimal and harness-internal until Codex separately approves production artifact contracts. WO-17 does not authorize production artifact contracts.

Partially resolves OQ-076: the minimum format for harness-internal use is locked to JSON; production artifact contract authority remains open under OQ-076.

### 2.6 Minimum Halt Behavior For Contract Failure

A contract failure halts measurement for the failing configuration in the current run and records an explicit halt event. There is no silent continuation against the failing configuration.

Resolves OQ-071. Consistent with `16-benchmark-harness-scope.md` Section 8 and `14-benchmark-execution-plan.md` Section 6 (Stage 1 contract violation pass).

### 2.7 Minimum Non-Mutation Guarantees

The scaffold must not write to any of the following:

- Corpus documentation.
- Route registry documentation.
- Validation evidence records.
- The source quality graph.
- The intent trace store.
- Any production-like state of any kind.

This restates and locks the non-mutation guarantee from `16-benchmark-harness-scope.md` Section 4 and `17-harness-implementation-plan.md` Section 10. The locked guarantee applies to the WO-18 scaffold and to every successor harness Work Order unless Codex separately modifies it.

## 3. Scope Of These Decisions

These decisions authorize only the future WO-18 minimal scaffold implementation. They do not authorize:

- Benchmark execution.
- Dataset creation.
- Real fixtures (test fixtures under the scaffold are scaffold-internal and not real benchmark datasets).
- Architecture selection of any kind.
- Vendor selection.
- Library selection beyond the Python standard library.
- Index family, retrieval family, ablation cell, multi-stage variant, reranker, or ANN backend selection.
- Production readiness.
- Third-party dependencies beyond the first scaffold (Codex decision required under OQ-075).
- Production artifact contracts (Codex decision required under OQ-076).
- Architecture inferences from the chosen runtime, framework, or location. Choosing Python 3 with `unittest` for the first scaffold does not imply that any retrieval architecture, vendor, library, ANN backend, reranker, or production system must be Python-based.

A WO-18 implementation packet must be issued before any code may be written. The decisions above bound that packet without authorizing it.

## 4. What WO-17 Does Not Decide

WO-17 does not decide:

- The minimum implementation surface for WO-18 (which harness responsibilities are implemented first; carried as OQ-069).
- The substantive environment snapshot content for reproducibility (carried as OQ-070).
- Longer-term dependency policy beyond the first scaffold (carried in OQ-075).
- Production artifact contract authority (carried in OQ-076).
- Any indexing architecture, retrieval family, ablation cell, multi-stage variant, reranker, ANN backend, vendor, library, or threshold.
- Any benchmark execution schedule, trigger, or operational cadence.
- Any selection or recommendation that the Indexing Excellence Gate (`00-controller-checklist.md` Section K) would otherwise govern.

## 5. Out Of Scope

This document is documentation-level only. It does not:

- Implement the harness or write code.
- Create scaffold files or directories.
- Install dependencies.
- Author schemas intended as production contracts.
- Author dataset content or real fixtures.
- Run benchmarks.
- Select indexing architecture, retrieval family, vendor, library, ANN backend, or any architecture direction.
- Set substantive metric thresholds or weights.
- Author runtime compile internals.
- Author validation framework implementation.

All such work requires a future Codex-approved Work Order.
