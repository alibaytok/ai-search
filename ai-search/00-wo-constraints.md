# ai-search - Standing Work Order Constraints Reference (Constraints v1)

Document type: Compiled reference / review aid
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Version: Constraints v1
Purpose: Compile, in one place, the recurring constraints that Codex has
imposed on every Work Order from WO-47 onward, so future packets can
reference "Constraints v1 apply" while still restating critical scope
constraints until Codex approves a migration.

## Authority

This file is a compiled reference. It is NOT the only source of truth
and it is NOT a project-authority document. The canonical authority
for project scope, allowed and forbidden actions, halt conditions,
and selection / measurement state remains with the controlling
project documents, in particular:

- `ai-search/00-controller-checklist.md` (controller checklist)
- `ai-search/00-open-questions.md` (open questions, risks, decisions,
  rejected assumptions)
- the active Work Order packet
- `ai-search/00-claude-task-ledger.md` (audit ledger of Work Orders)

If this constraints reference ever conflicts with any of the above
canonical documents, the canonical document wins and this reference
must be corrected to match. This file does not extend, broaden, narrow,
or amend the controller checklist or any prior Decision (DC-001
through DC-062). It does not authorize any new work.

A future Work Order packet may, at Codex's option, say "Constraints v1
apply" instead of restating the full standing constraint list. Until
Codex explicitly approves that migration, packets should still
restate the critical scope constraints inline. Treat this file as
additive review aid, not as a substitute for packet-level scope.

## Scope

WO-META-01 created this file. WO-META-01 is documentation-only and
does NOT authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- URL fetch / download / crawl / browser automation;
- local file read or file write inside any scaffold module;
- source qualification;
- corpus admission;
- extraction, normalization, or candidate-fragment derivation;
- invention of `origin` or full `hash`;
- invocation of `run_scaffold_source_intake_register` (WO-55),
  `run_scaffold_url_acquisition_executor` (WO-61), or any other
  prior-WO public function from a new module;
- ranking, scoring, similarity, distance, near-match, fuzzy
  semantic analysis, thresholds, weights, or model judgments;
- architecture / vendor / library / index family / ANN backend /
  neural re-scorer / retrieval family / ablation cell /
  multi-stage variant / production system choice;
- IDE / extension / chat / collaborator / Copilot / Waza / VS Code
  / LLM integration;
- Source Card or Route Card creation;
- production artifact contracts;
- subprocess or shell execution;
- mutation under `benchmark-fixtures/`;
- modification of `ai-search/00-controller-checklist.md`;
- modification of WO-50 through WO-62 modules or tests;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

Real-benchmark-ready remains NO.

## A. Project-Level Standing Constraints

A1. Real-benchmark-ready remains NO unless a future Work Order
explicitly flips it.

A2. No real adapter and no real benchmark execution unless
separately authorized by a future Work Order packet.

A3. No architecture / vendor / library / index family / ANN backend
/ neural re-scorer / retrieval family / ablation cell / multi-stage
variant / production system selection is authorized.

A4. No mutation under `benchmark-fixtures/`. The fixture inventory
SHA set must remain unchanged across every Work Order.

A5. No modification of `ai-search/00-controller-checklist.md`
unless explicitly authorized by a future Work Order packet.

A6. No modification of prior-WO modules or their test files unless
explicitly authorized by a future Work Order packet. Coverage
extensions (such as WO-48 over WO-47 or WO-53 over WO-52) are the
exception only when the extending Work Order packet states the
extension explicitly.

A7. No IDE / extension / chat / collaborator / Copilot / Waza /
VS Code / LLM integration. Scaffold modules do not invoke external
LLMs, do not embed prompts into vendor APIs, and do not depend on
editor tooling.

A8. The set of open OQs and active risks carries forward across
every Work Order. As of Constraints v1 the carry-forward set is:
OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057,
OQ-070, OQ-075, OQ-076 remain OPEN; RK-039 remains active and must
not be duplicated.

## B. Authorization / Readiness / Selection Booleans

B1. The following booleans appear in scaffold output dicts and in
boundary records. All of them remain literal False across every
scaffold module unless a future Work Order packet explicitly
authorizes flipping a named one:

- `selection_made`
- `measurement_authorized`
- `real_benchmark_authorized`
- `real_benchmark_ready`

B2. The following per-output booleans also remain literal False
unless explicitly authorized:

- `extraction_authorized`
- `normalization_authorized`
- `candidate_derivation_authorized`
- `source_register_invocation_authorized`
- `safe_to_invent_missing_identity`
- per-reference `corpus_admitted`
- per-reference `qualified`
- per-reference `source_material_extracted`
- per-reference `route_object_created`

B3. Top-level admission counts (`corpus_admitted_count`,
`qualified_count`, `source_material_extracted_count`) remain literal
zero unless explicitly authorized.

## C. Language Discipline

C1. Scaffold modules, scaffold tests, boundary docs, tracker
entries, and ledger entries do NOT claim that any scaffold output,
diagnostic record, blocked reason, missing-field name, observation,
selection, configuration, ranking, scoring, or production artifact
is sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected.

C2. Bounded admission surfaces (allowed declared-kind sets, allowed
origin-mode sets, allowed fragment-kind sets, allowed diagnostic
categories, forbidden-field sets) are bounded by the authoring Work
Order and are NOT claimed exhaustive.

C3. Forbidden-language scans cover at minimum the phrase list
exported by `harness.review_package.FORBIDDEN_PHRASES` and the
claim-phrase list exported by `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`.
A module that emits text into its output dict or events must scan
both that output and (defense-in-depth) its input for these phrases
before returning.

C4. Hash is identity / integrity only. Hash never qualifies a
source. A scaffold module that emits hash material emits either a
full digest (only when explicitly authorized, as in the WO-55
register's `hash` field) or a fixed-length prefix (such as the
12-character `content_hash_prefix` in WO-61). The prefix never
qualifies for the register's `hash` field.

## D. Work Order Protocol

D1. A pre-implementation review note is required before file edits
in any Work Order that touches `harness/` or `ai-search/`. The note
answers the packet's listed review questions and is included in the
ledger entry under "Pre-Implementation Review Note".

D2. A Section L scope quiz is required before substantial work in
any Work Order whose scope is non-trivial or could authorize code,
benchmark execution, metric collection, artifact contracts, or
architecture selection. The quiz covers at minimum the seven items
listed in `00-controller-checklist.md` Section L item 202.

D3. Halt-before-raise pattern. Every scaffold module that raises a
named exception records a halt event via
`event_log.halt(reason=..., entry_index=...)` immediately before the
`raise`. The advisory `halt_required: True` diagnostic field
emitted by WO-58 does NOT itself cause the reporter to raise; it is
observational.

D4. Targeted test, full suite, and hygiene must all pass before the
evidence report is emitted. "Hygiene" means: ASCII clean on every
touched file, no `__pycache__` directories anywhere under the project
root, the project root contains exactly `ai-search/`, `harness/`,
and `benchmark-fixtures/`, and the `benchmark-fixtures/` SHA inventory
is unchanged.

D5. Stop after the evidence report. The builder does NOT propose a
next Work Order from inside the evidence report.

## E. Tracker And Artifact Discipline

E1. `ai-search/00-open-questions.md` is append-mostly. New OQ / RK /
DC / RA rows are appended at the end of their respective tables.
The header `Status` line and the `Work Order` chronology line at the
top of the file may be updated per Work Order to reflect the latest
state. Existing rows in the four tables are NOT rewritten by Claude
without an explicit Codex Decision authorizing the rewrite.

E2. `ai-search/00-claude-task-ledger.md` is append-only for Work
Order entries. The "Status" header at the top of the file is treated
as the cumulative-status string and is updated by Codex review or by
the most-recent Work Order. Older Work Order entry bodies are NOT
rewritten by Claude except to record Codex feedback and review
results via append.

E3. Boundary docs (`ai-search/NN-...md`) are written once per Work
Order and not later modified by Claude without an explicit Codex
Decision authorizing the modification.

## F. Static-Scan Tokens (For Scaffold Modules)

F1. Scaffold module source files must NOT contain the following
substring tokens unless the authoring Work Order packet explicitly
authorizes them. The list is bounded by Constraints v1 and is NOT
claimed exhaustive:

- file IO: `open(`, `pathlib`
- network: `urllib`, `http.client`, `socket`
- HTTP library: `import requests`, `from requests`, `requests.`
- shell / process: `subprocess`, `os.system`, `shutil`
- hashing: `hashlib`, `.hexdigest`, `.sha256` (authorized only in
  WO-61 by DC-061)
- retrieval verbs: `def query`, `def search`, `def retrieve`,
  `def rank`
- external integration: `copilot`, `waza`, `vscode`, `vs_code`,
  `openai`, `anthropic`, `claude_api`, `llm`

F2. Static-scan tests are added per Work Order to assert the
absence of the F1 tokens in the new module source. Static-scan
tests also assert the absence of prior-WO public function names
that the new module is forbidden from invoking.

## G. Substring-Collision Rule

G1. When a needed identifier shares a substring with a forbidden
token, the resolution is to tighten the static scan, not to relax
the ban. For example: `reranker` contains the substring `rank`;
the static-scan test is tightened to look for `def query` /
`def search` / `def retrieve` / `def rank` specifically, not for
the bare substring `rank`. The HTTP-library ban looks for
`import requests` / `from requests` / `requests.` specifically,
because a module parameter named `acquisition_requests` legitimately
contains the substring `requests`.

G2. When a forbidden token genuinely cannot be reconciled with the
identifier set, the resolution is to rename the identifier, not to
relax the ban.

## H. Open Questions And Active Risks Carry-Forward

H1. The following OQs remain OPEN as of Constraints v1 and must not
be closed by any documentation-only or scaffold-only Work Order:
OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057,
OQ-070, OQ-075, OQ-076.

H2. RK-039 remains active and must not be duplicated by any new
RK row.

H3. Closure of any OQ requires an explicit Codex Decision row in
`00-open-questions.md` Decisions Tracker and a corresponding Codex
Status update in `00-claude-task-ledger.md`.

## I. Evidence Report Template

I1. Every scaffold or documentation Work Order ends with an
evidence report that includes at minimum:

- Section L scope quiz result;
- Pre-implementation review note result;
- Exact files touched;
- Targeted test result, or `not applicable - documentation-only`
  if no targeted test exists;
- Full suite result (test count and OK status);
- ASCII check result on every touched file;
- `__pycache__` absence check;
- Project root directory check (`ai-search/`, `harness/`,
  `benchmark-fixtures/` only);
- `benchmark-fixtures/` unchanged confirmation;
- `harness/` unchanged confirmation for documentation-only WOs,
  or modified-file list for scaffold WOs;
- `00-controller-checklist.md` unchanged confirmation;
- "No OQ closed" confirmation;
- "RK-039 not duplicated" confirmation;
- "Real-benchmark-ready remains NO" confirmation.

I2. Optional non-binding slot (added by WO-META-01):

```
Structural gaps noticed (non-binding):
```

If none, write `none`. The slot records observations only. It does
NOT propose, recommend, authorize, or schedule new Work Orders. It
does NOT flip any authorization / readiness / selection boolean. It
is review evidence for Codex only.

I3. Stop after the evidence report. The builder does NOT propose a
next Work Order from inside the evidence report.

## J. Constraints Version Discipline

J1. This file is versioned. Constraints v1 is the version
established by WO-META-01.

J2. Any change to the standing constraint set bumps the version. A
future Work Order that introduces Constraints v2 must call out the
diff against Constraints v1 explicitly in its packet.

J3. The constraints version a Work Order operated under is recorded
in the Work Order's ledger entry. Until a future Work Order packet
says "Constraints v1 apply" (or "Constraints v2 apply" once v2
exists), Work Order packets continue to restate the critical scope
constraints inline.
