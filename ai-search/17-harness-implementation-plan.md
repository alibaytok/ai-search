# ai-search - Harness Implementation Plan (Readiness)

Document type: Phase 4 / Phase 9 readiness / Harness scaffold implementation file plan
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review (Section 1 stale Work Order sequencing reference corrected under WO-17R)
Work Order: WO-16 (approved), WO-17R (current submission for stale-sequencing correction)

---

## 1. Purpose

This document is the implementation-readiness plan for a future minimal benchmark harness scaffold. It records a concrete inspection of the repository as it stands today, names what conventions already exist (none, in this case), proposes - as proposals only - the smallest safe implementation surface that could be authorized under a future Codex-issued implementation packet, and surfaces every decision that Codex must own before code is written. It does not implement, create files, install dependencies, or choose architecture direction. The plan exists so that any future implementation packet inherits an explicit, recorded starting point rather than improvised structure.

WO-16 is readiness only. WO-17 (or a later packet) will be the implementation packet that approves a specific surface for code creation.

## 2. Repository Inspection Summary

The following inspection was performed against `C:\Projects\ai-search\` on the WO-16 submission date. Findings are concrete observations.

- Top-level project root contains exactly one subdirectory: `ai-search\`.
- The `ai-search\` subdirectory contains exactly nineteen Markdown files: the eighteen authored documentation files (`00-claude-task-ledger.md`, `00-controller-checklist.md`, `00-open-questions.md`, `00-phase-map.md`, `01-thesis.md`, `02-search-corpus.md`, `03-route-registry.md`, `04-intent-trace-store.md`, `05-ranking-model.md`, `06-index-miss-policy.md`, `08-validation-and-feedback.md`, `09-source-quality-graph.md`, `10-corpus-ingestion-pipeline.md`, `11-candidate-route-builder.md`, `12-indexing-and-retrieval-research.md`, `13-retrieval-benchmark-framework.md`, `14-benchmark-execution-plan.md`, `15-retrieval-experiment-design.md`) plus `16-benchmark-harness-scope.md`. Counting this WO-16 submission's output, the directory will hold twenty Markdown files.
- No source code files exist (no files with extensions for Python, TypeScript, Go, Rust, Java, C#, Ruby, PHP, or any other implementation language).
- No package manifest files exist (no `package.json`, `pyproject.toml`, `setup.py`, `setup.cfg`, `Cargo.toml`, `go.mod`, `pom.xml`, `build.gradle`, `*.csproj`, `Gemfile`, `composer.json`, or equivalent).
- No test directories or test files exist.
- No CI configuration files exist (no `.github/`, `.gitlab-ci.yml`, `azure-pipelines.yml`, `Jenkinsfile`, or equivalent).
- No lint, format, or typecheck configuration exists (no `.prettierrc`, `.eslintrc`, `tsconfig.json`, `pyproject.toml` configuration sections, `setup.cfg` configuration sections, `ruff.toml`, `mypy.ini`, `rustfmt.toml`, or equivalent).
- No build configuration exists.
- No `.git` directory exists. The session environment confirmed at start: "Is a git repository: false."
- No `README.md`, `LICENSE`, `CONTRIBUTING.md`, or comparable repository-level files exist.
- No scripts directory exists.
- No `.gitignore`, `.editorconfig`, or other repo-level dotfiles exist.
- The platform is Windows 11 Home (per the session environment); the shell available is PowerShell with Bash also available through the harness's Bash tool.

The repository is documentation-only as of WO-15R. Adding code requires creating a new project structure that does not currently exist. That creation is itself an architecture decision and is owned by Codex.

## 3. Existing Build And Test Conventions

There are no existing build, test, lint, typecheck, format, dependency-management, or CI conventions in this repository. The inspection in Section 2 found none. Any convention adopted for a future scaffold will therefore be a new convention rather than an extension of an existing one.

Because no convention currently exists, no language, runtime, package manager, test framework, dependency manager, lint tool, type checker, build tool, CI provider, or directory layout is established. Each of these is a Codex decision (Section 15 lists them as open questions).

Until Codex records those decisions, this plan describes what the scaffold must satisfy at boundary level only. It does not pick a language, framework, package manager, or layout.

## 4. Proposed Harness Location

Proposal only. Codex chooses.

The harness needs a home that is separable from the documentation directory so that:

- Documentation files in `ai-search/` are not accidentally mutated by harness code, tests, or build artifacts.
- The harness's code surface and the project's documentation surface have distinct trees that audit tooling can inspect independently.
- Run artifacts produced by the harness do not pollute the documentation directory.

Two illustrative location options for Codex to choose between (Codex may also choose a third option that is not listed):

- Option A. A sibling directory at the project root, for example `harness/` at `C:\Projects\ai-search\harness\`, with its own package manifest, source tree, test tree, and artifact output directory.
- Option B. A subdirectory under `ai-search/`, for example `ai-search/harness/`, sibling to the documentation files, with the same internal layout.

Tradeoffs (boundary-level only, not a recommendation):

- Option A places harness code physically separate from documentation. Easier to grant or restrict access to harness code without touching docs.
- Option B keeps the entire project under `ai-search/`. Easier to keep "one project" intuition; risk of accidental mutation of nearby documentation files if harness file globs are imprecise.

The choice is owned by Codex (new OQ).

## 5. Minimal Scaffold Responsibility

The scaffold's responsibilities are a strict subset of the allowed responsibilities recorded in `16-benchmark-harness-scope.md` Section 3. Inside that subset, the minimal first-implementation responsibility surface should be the smallest set that demonstrates the boundary while authorizing no further behavior.

Codex owns the minimum surface decision per OQ-069 (carried from WO-15). At boundary level only, the smallest plausible first-implementation surface is:

- Read an approved fixture file from a known location and verify its content hash against a recorded reference.
- Read a registered configuration manifest from a known location and verify that the active configuration matches its registered manifest record.
- Run a recorded set of contract violation tests against the configuration's responses and record pass or fail per test.
- Record a halt event on contract failure (or on fixture hash mismatch, configuration drift, or readiness failure).
- Record reproducibility evidence (deterministic seed, dependency manifest, environment snapshot) for the run.
- Assemble a human review package summarizing the above without recommending a winner.

This is the smallest surface that satisfies the scope boundary in `16-benchmark-harness-scope.md` Sections 3, 6, 7, 8, 10, 12, and 13. WO-17 (or a later packet) may approve all of it, a subset of it, or a different decomposition.

## 6. Proposed Future Files

Proposals only. None of these files exists today. None is created by WO-16. Each name and path is illustrative; Codex may rename, relocate, merge, or split any of them in the implementation packet.

The file proposals below name the categories of files a minimal scaffold needs, not concrete paths. Codex's chosen location (Section 4), language (Section 15 open question), and framework conventions will dictate the actual paths.

- A scaffold entry point file. Single executable surface for invoking a run. The scaffold must not run benchmarks by default; the entry point must require explicit invocation to do anything observable.
- A fixture loader module. Reads a fixture file from an approved location and verifies its content hash against a recorded reference. Read-only.
- A configuration loader module. Reads a registered configuration manifest from an approved location and verifies that the active configuration matches the registered manifest record. Read-only.
- A contract test runner module. Iterates a recorded contract test set against configuration responses and records pass or fail per test, with offending response provenance for failures.
- An event log module. Records the ordered event log for a run with timestamps and explicit halt events.
- A reproducibility capture module. Records deterministic seeds, dependency manifest snapshot, and environment snapshot for the run.
- A human review package assembler. Collects the readiness decision, fixture versions and hashes, configuration manifests, contract results, performance and operational placeholders (if any), reproducibility evidence, and event log into a single human-reviewable artifact location.
- Test files for each module above, covering: read-only invariants, hash verification, configuration drift detection, contract pass/fail behavior, halt-event recording, reproducibility capture, and non-mutation of source documents.
- A scaffold-level configuration file recording the harness's own version pins and runtime characteristics (separate from the registered configuration manifests it consumes).
- A dependency manifest file appropriate to the chosen language and package manager.

None of the above is approved for creation under WO-16. They are proposals subject to Codex's implementation packet.

## 7. Proposed Future Test Surface

Proposals only. No tests are written under WO-16.

The minimum test surface for the scaffold should cover, at boundary level only:

- Hash verification tests. Fixtures whose content hash matches the recorded reference are admitted; mismatched fixtures halt the run with an explicit event.
- Configuration drift tests. Configurations whose active state matches the registered manifest record are admitted; drift halts the run with an explicit event.
- Contract violation pass/fail tests. Synthetic configuration responses that violate each contract test trigger the corresponding failure recording; compliant responses produce a pass record.
- Halt-event tests. Each halt trigger (readiness failure, hash mismatch, configuration drift, contract failure) produces an explicit halt event in the event log; no silent retries occur.
- Non-mutation tests. The scaffold does not write to any path outside its own run artifact directory; in particular it does not write to the documentation directory, does not write to a future source corpus directory, does not write to a future route registry directory, and does not write to a future intent trace store directory.
- Reproducibility tests. Two runs with identical inputs and seeds produce identical observable outputs (where the harness's outputs are deterministic by design).
- Disqualification tests. A configuration that fails a contract violation test does not advance to any quality, performance, or operational measurement in the same run.

The test framework choice, the test file layout, and the test naming convention are owned by Codex (Section 15 open question).

## 8. Dependency Boundary

Proposals only. No dependencies are installed under WO-16. No specific library, framework, vendor, or version is selected; only the categories of dependency the scaffold likely needs.

The scaffold needs, at boundary level, the following capabilities. Each capability may be satisfied by the standard library of the chosen language, by a small dependency, or by a combination:

- File reading with explicit encoding (no implicit OS-level transcoding).
- Cryptographic hashing for fixture content verification (a SHA-family hash is standard for this purpose; the specific function is a Codex decision).
- Deterministic random seeding (standard library facilities in most languages).
- Structured logging with append-only event semantics (standard library typically suffices).
- A test framework (Codex decision per Section 15 open question).
- A dependency manifest format appropriate to the chosen package manager (Codex decision).

The scaffold must not depend on indexing libraries, ANN backends, embedding model libraries, ranking frameworks, retrieval engines, vector databases, or any other dependency that would constitute architecture selection. Such dependencies belong to retrieval configurations under benchmark, not to the harness itself.

The scaffold's dependency policy is owned by Codex (new OQ): how dependencies are added, how versions are pinned, how new dependencies are reviewed, and how vendored versus published dependencies are handled.

## 9. Fixture And Artifact Boundary

Per `16-benchmark-harness-scope.md` Sections 5, 6, and 11, plus `13-retrieval-benchmark-framework.md` Section 3 and `14-benchmark-execution-plan.md` Section 4:

- Fixtures are inputs the scaffold reads; they are not authored by the scaffold and not authored under WO-16.
- The scaffold reads fixtures from an approved input location recorded in the run manifest. The scaffold does not discover fixtures opportunistically.
- The scaffold writes run artifacts only to its own artifact directory. Run artifacts include the readiness decision, dataset versions and hashes admitted, configuration manifests under test, contract violation results, per-class and per-plane quality measurements (where collected), performance distributions, operational findings, reproducibility evidence, the complete event log, and the regression baseline cross-reference.
- Artifact format, storage location, retention period, immutability mechanism, and access control are owned by Codex (existing OQ-056 referenced; not duplicated). The scaffold does not author the artifact schema (new OQ).

WO-16 does not author fixtures, dataset content, or artifact templates.

## 10. Non-Mutation Guarantees

The scaffold must not mutate any of the following, under any condition:

- The source corpus.
- The source quality graph (`09-source-quality-graph.md`).
- The route registry (`03-route-registry.md`).
- Candidate routes (`11-candidate-route-builder.md`).
- Official routes.
- The validation evidence ledger (`08-validation-and-feedback.md`).
- The intent trace store (`04-intent-trace-store.md`).
- Any production state at all.
- Documentation files in `ai-search/`.
- Approved fixtures.
- Registered configuration manifests.
- Prior run artifacts.

Non-mutation tests (Section 7) verify these guarantees. The scaffold writes only to its own run artifact directory, and only with append-only semantics for the event log and reproducibility evidence.

## 11. Contract Test Runner Boundary

Per `16-benchmark-harness-scope.md` Section 8:

- The scaffold runs the contract violation tests from `13-retrieval-benchmark-framework.md` Section 8 before any quality, performance, or operational measurement against the same configuration in the same run.
- Each contract test is recorded as pass or fail. A failure records the violated test, the input that triggered it, the offending response, and the configuration manifest under which the failure occurred.
- A contract failure disqualifies the configuration for the run. The scaffold halts further measurement against that configuration and records the disqualification as an explicit event.
- The scaffold does not relax contract tests per configuration, per cell, or per run.
- The exact halt scope on contract failure (per-configuration vs. per-run) is owned by Codex (existing OQ-071 referenced).

## 12. Reproducibility Capture Boundary

Per `16-benchmark-harness-scope.md` Section 10:

- The scaffold records deterministic seeds for every stochastic step.
- The scaffold records version pins for every software dependency.
- The scaffold records the content hashes of every fixture admitted to the run.
- The scaffold records an environment snapshot. The substantive content of the snapshot is owned by Codex (existing OQ-070 referenced).
- A run that cannot be reproduced from its recorded state is annotated and excluded from the human review package until the reproducibility defect is resolved.
- The scaffold does not edit reproducibility evidence after the run. Reproducibility evidence is append-only.

## 13. Human Review Package Boundary

Per `16-benchmark-harness-scope.md` Section 12:

- The scaffold assembles a human review package per Stage 5 of `14-benchmark-execution-plan.md` after a run completes.
- The package summarizes the run artifact for Codex review. It does not recommend a winner, does not score across cells, does not rank configurations.
- A run that did not meet the acceptance boundary is recorded as such in the package; the package does not omit failing runs or hide disqualifications.
- The scaffold does not act on the human review package. Codex's selection decision is recorded by a future Codex-authored architecture selection Work Order, which is out of scope here.

## 14. Implementation Risks

Naming risks for tracking; substantive mitigations are owned by Codex.

- A scaffold built before Codex picks a language and location would either be discarded later or would silently lock in those choices. Both outcomes are bad.
- A scaffold whose entry point runs benchmarks by default would behave like a benchmark execution authorization, which WO-16 does not grant.
- A scaffold whose fixture or artifact directories overlap with the documentation directory could mutate documentation through a bug.
- A scaffold that imports an indexing library to "demonstrate" something would have crossed from harness scope into architecture selection.
- A scaffold whose proposed file plan is treated as approved would have bypassed the implementation packet.
- A scaffold whose dependencies were chosen by convenience would have bypassed the dependency policy decision.

These risks are recorded in the tracker under WO-16.

## 15. Open Questions Before Code

The following must be resolved by Codex before any harness code is written. WO-16 does not resolve them.

- What language and runtime is approved for the harness scaffold?
- Where in the repository does the harness live? (Sibling at project root, subdirectory under `ai-search/`, or another location chosen by Codex.)
- What test framework is approved?
- What package manager and dependency manifest format is approved?
- What dependency policy applies to benchmark harness code (review process, version pinning approach, vendored vs. published handling)?
- What artifact format authority is required before implementation, and how is the artifact format approved?
- What is the exact halt scope on contract failure (carried as existing OQ-071)?
- What is the substantive environment snapshot content (carried as existing OQ-070)?
- What is the minimum implementation surface that WO-17 should authorize (carried as existing OQ-069)?
- What CI surface, if any, is approved alongside the scaffold?
- What lint, typecheck, format conventions are approved?

These questions are tracked in `00-open-questions.md`. New ones added under WO-16 cover language/runtime, repository location, test framework, dependency policy, and artifact format authority; existing questions are referenced where applicable.

## 16. Out Of Scope

This document is documentation-level only. It does not:

- Implement the harness, write code, write pseudocode, write scripts, write CLI commands, or write tests.
- Create any directory, file, package manifest, or dependency lockfile.
- Install any dependency.
- Author schemas, fields, types, JSON templates, or data models.
- Author dataset content or fixtures.
- Run benchmarks.
- Select a language, runtime, package manager, test framework, lint tool, type checker, build tool, CI provider, vendor, library, index family, retrieval family, ablation cell, multi-stage variant, reranker, ANN backend, or architecture.
- Set substantive metric thresholds or weights.
- Author runtime compile internals.
- Author validation framework implementation.
- Treat the proposed file plan as implementation approval.
- Treat any harness output as route validation evidence or as production trust signal.

All such work requires a future Codex-approved Work Order.
