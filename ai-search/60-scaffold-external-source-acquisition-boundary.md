# ai-search - Scaffold External Source Acquisition Boundary

Document type: Phase 2 / Phase 4 / Phase 9 / Scaffold acquisition-boundary boundary
Owner: Codex (controller)
Author: Claude (under WO-60)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-60

---

## 1. Purpose

WO-60 adds a scaffold-only acquisition-boundary layer that describes
external source acquisition requests across three origin modes
without treating any acquired material as corpus, qualification
evidence, route object, search data, benchmark evidence, or
architecture-selection evidence.

The system must not assume "local files only". External sources can
arrive as URL references, local-path references, or already-pasted
text. WO-60 records the acquisition intent and inert identity /
integrity metadata for each request, while explicitly NOT fetching
the URL, NOT reading the local path, and NOT echoing the pasted
text.

### What this is NOT

- NOT a crawler / downloader / file reader / browser automation /
  shell runner.
- NOT real indexing / real retrieval / prompt search / skill search /
  agent selection / generic RAG.
- NOT source qualification; NOT corpus admission; NOT a Source Card;
  NOT a Route Card; NOT a route validator.
- NOT benchmark execution; NOT a benchmark-readiness flip; NOT
  benchmark evidence; NOT architecture / vendor / library / index
  family / production system selection.
- NOT IDE / extension / Copilot / Waza / VS Code / LLM / model
  integration.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Admit three origin modes (`url`, `local_path`, `pasted_text`) as
  inert locator references only.
- Keep all data already-loaded in memory; module performs no file
  or network IO, no hash computation, no subprocess execution, and
  no model judgment.
- Preserve every output authorization / readiness / selection
  boolean as literal False; preserve `corpus_admitted_count` /
  `qualified_count` as literal 0; preserve every per-reference
  `corpus_admitted` / `qualified` / `source_material_extracted` /
  `route_object_created` as literal False.
- Reject every Source-Card-shaped, derived-material, route-shaped,
  and benchmark-fixture-shaped field on input.
- Never echo raw locator content (URL string, local path string, or
  pasted text) into the report's free-text output fields; record
  only inert structural markers (length, hash prefix).
- Do not invoke WO-50 through WO-59 public functions.

## 3. Added Files

WO-60 adds:

- `harness/scaffold_external_source_acquisition_boundary.py`
- `harness/tests/test_scaffold_external_source_acquisition_boundary.py`
- `ai-search/60-scaffold-external-source-acquisition-boundary.md`

WO-60 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 through
WO-59 modules and their test files are not modified.
`ai-search/00-controller-checklist.md` is not modified.

## 4. Public Function

```text
run_scaffold_external_source_acquisition_boundary(acquisition_requests, event_log) -> dict
```

Inputs:

- `acquisition_requests`: a list (possibly empty) of already-loaded
  acquisition request dicts.
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no network call,
computes no hash, and does not invoke any other scaffold-layer
public function.

## 5. Origin Modes

`ALLOWED_ORIGIN_MODES = frozenset({"url", "local_path", "pasted_text"})`.

- `url`: the `origin_locator` is a URL string. The module does NOT
  fetch the URL; the locator is recorded as an inert string and only
  its length is echoed into the output reference.
- `local_path`: the `origin_locator` is a local filesystem path
  string. The module does NOT read the path; the locator is treated
  as an inert string.
- `pasted_text`: the `origin_locator` is a user-supplied identifier
  for the pasted block (NOT the pasted text itself). Pasted content,
  if represented at all, is represented only by `content_byte_length`
  and `content_hash` in the request; the module never echoes raw
  pasted text.

## 6. Required Request Fields

`REQUIRED_REQUEST_FIELDS` (exact set; unknown keys rejected):

- `request_id` (non-empty string)
- `origin_mode` (one of `ALLOWED_ORIGIN_MODES`)
- `origin_locator` (non-empty string; inert)
- `declared_kind` (one of `ALLOWED_DECLARED_KINDS`, matching the
  WO-55 label set)
- `content_available` (literal boolean)
- `content_byte_length` (non-negative int; must be 0 when
  `content_available is False`)
- `content_hash` (non-empty string when `content_available is True`;
  must be empty string when `content_available is False`)
- `observed_at` (non-empty string)

`ALLOWED_DECLARED_KINDS` matches the WO-55 set:
`prompt_collection`, `skill_collection`,
`agent_description_collection`, `tool_description_collection`,
`document_collection`.

## 7. Forbidden Request Fields

Each request is rejected if it declares any of the following keys
(regardless of value):

`qualified`, `qualification_ref`, `corpus_admitted`,
`source_card`, `route_card`, `authority`, `trust`, `freshness`,
`ownership`, `validation_evidence`, `qualification_evidence`,
`extracted_material`, `normalized_material`, `candidate_fragments`,
`candidate_route_fragments`, `candidate_workflow_fragments`,
`route`, `route_id`, `route_state`, `plane`, `official`,
`executable`, `selected_route`, `production_route`,
`benchmark_fixture_class`, `golden_intent`, `hard_negative`,
`boundary_violation`.

Each rejection records a halt event before raising
`ForbiddenAcquisitionField`.

## 8. Content-Availability Contract

- `content_available: False` requires `content_byte_length == 0` and
  `content_hash == ""`.
- `content_available: True` requires `content_byte_length` to be a
  non-negative int (bools rejected) and `content_hash` to be a
  non-empty string.
- `content_available` must itself be a literal Python boolean.
- `content_hash` is identity / integrity only. Its presence does NOT
  qualify the source, does NOT admit corpus, and does NOT flip any
  authorization boolean.

## 9. Result Surface (Clean-Pass Only)

On clean pass, the module returns a fresh dict with exactly thirteen
allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `acquisition_boundary_kind`
- `request_count`
- `origin_mode_counts` (dict keyed by origin mode; per-mode count)
- `acquisition_references` (list of structural acquisition refs)
- `content_available_count`
- `content_missing_count`
- `corpus_admitted_count` (literal `0`)
- `qualified_count` (literal `0`)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `acquisition_boundary_note`

Each `acquisition_references` entry contains only structural data:

- `request_id`
- `origin_mode`
- `declared_kind`
- `origin_locator_observed: True`
- `origin_locator_length`
- `content_available`
- `content_byte_length`
- `content_hash_prefix` (12 chars; empty string if no content)
- `corpus_admitted: False`
- `qualified: False`
- `source_material_extracted: False`
- `route_object_created: False`

The raw `origin_locator` value is NOT echoed into the output
references. The full `content_hash` is NOT echoed (only a 12-char
prefix is recorded).

## 10. Event Surface

Success events:

- `scaffold_external_source_acquisition_boundary_started`
- `scaffold_external_source_acquisition_request_observed`
- `scaffold_external_source_acquisition_boundary_passed`

Halt events:

- `scaffold_external_source_acquisition_boundary_non_list_requests`
- `scaffold_external_source_acquisition_boundary_non_object_request`
- `scaffold_external_source_acquisition_boundary_missing_field`
- `scaffold_external_source_acquisition_boundary_invalid_string_field`
- `scaffold_external_source_acquisition_boundary_unknown_field`
- `scaffold_external_source_acquisition_boundary_forbidden_field`
- `scaffold_external_source_acquisition_boundary_duplicate_request_id`
- `scaffold_external_source_acquisition_boundary_duplicate_origin`
- `scaffold_external_source_acquisition_boundary_invalid_origin_mode`
- `scaffold_external_source_acquisition_boundary_invalid_declared_kind`
- `scaffold_external_source_acquisition_boundary_invalid_content_availability`
- `scaffold_external_source_acquisition_boundary_invalid_content_length`
- `scaffold_external_source_acquisition_boundary_invalid_content_hash`
- `scaffold_external_source_acquisition_boundary_forbidden_language`

Each halt event is recorded before the corresponding named
exception is raised.

## 11. Named Exceptions

- `NonListAcquisitionRequests`
- `NonObjectAcquisitionRequest`
- `MissingAcquisitionRequestField`
- `UnknownAcquisitionRequestField`
- `DuplicateAcquisitionRequestId`
- `DuplicateAcquisitionOrigin`
- `InvalidOriginMode`
- `InvalidDeclaredKind`
- `InvalidContentAvailability`
- `InvalidContentLength`
- `InvalidContentHash`
- `ForbiddenAcquisitionField`
- `ForbiddenLanguageInAcquisitionBoundary`

## 12. Tests Added

`harness/tests/test_scaffold_external_source_acquisition_boundary.py`
adds 39 tests across nine `TestCase` classes covering:

- clean pass with empty list;
- clean pass with one `url` request, `content_available: False`;
- clean pass with one `local_path` request, `content_available:
  False`;
- clean pass with one `pasted_text` request, `content_available:
  True` (only length / hash metadata; no raw text in output);
- clean pass with all three origin modes;
- literal-False output authorization / readiness / selection
  booleans;
- per-reference literal-False `corpus_admitted` / `qualified` /
  `source_material_extracted` / `route_object_created`;
- `content_available: True` does not flip admission or
  qualification;
- hash presence does not flip admission or qualification (full hash
  never echoed; only `content_hash_prefix`);
- `_passed` event records clean counts;
- `origin_locator` not echoed into `acquisition_boundary_note`;
- `origin_locator` not echoed into references (sentinel-string
  test);
- `origin_locator_length` recorded instead;
- non-list / non-dict / each missing field / unknown field / each
  forbidden field individually / duplicate `request_id` / duplicate
  `(origin_mode, origin_locator)` rejection paths;
- invalid `origin_mode` / invalid `declared_kind` rejection;
- `content_available` must be bool;
- `content_available: False` requires zero byte length and empty
  hash;
- `content_available: True` requires non-negative int byte length
  (bool rejected), non-empty string hash;
- output forbidden-language scan;
- input not mutated;
- no filesystem writes;
- only stdlib + harness-internal imports;
- module source contains no `open(` / `pathlib` / `urllib` /
  `http.client` / `socket` / `subprocess` / `os.system` / `shutil` /
  `hashlib` / `.hexdigest` / `.sha256` tokens, and no `import
  requests` / `from requests` / `requests.` library-use forms;
- module source contains no `def query` / `def search` /
  `def retrieve` / `def rank` tokens;
- module source contains no `copilot` / `waza` / `vscode` /
  `vs_code` / `openai` / `anthropic` / `claude_api` / `llm` tokens;
- `benchmark-fixtures/` files not mutated;
- constants admissibility (`ALLOWED_ORIGIN_MODES` matches packet,
  `ALLOWED_DECLARED_KINDS` matches WO-55).

## 13. Non-Claim Constraint

The WO-47 through WO-59 explicit non-claim constraint carries
forward verbatim:

This module does not claim that any acquisition reference, origin
mode, declared kind, content-availability marker, or in-memory
observation is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected. The bounded admission
surfaces (three origin modes, five declared kinds, 28 forbidden
input fields) are not claimed exhaustive.

The module records inert acquisition references only. It does not
declare any referenced source admissible, qualified, extractable,
normalizable, fragment-derivable, route-valid, or selected for any
production system.

## 14. Forbidden Scope

WO-60 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- URL fetch / download / crawl / browser automation;
- local file read or file write;
- pasted-text echo into output;
- hash computation inside the module;
- extraction, normalization, or candidate-fragment derivation;
- similarity, distance, near-match, or scoring of any kind;
- quality, performance, or operational metric collection;
- ranking or winner declarations;
- model judgments, fuzzy semantic analysis, thresholds, or weights;
- architecture, vendor, library, index family, ANN backend,
  retrieval family, ablation cell, multi-stage variant, or
  production system choice;
- IDE / extension / chat / collaborator / Copilot / Waza / VS Code
  / LLM integration;
- prompt / skill / agent evaluation;
- Source Card creation;
- Route Card creation;
- production artifact schema, retention, storage, immutability,
  access-control, or registration policy;
- third-party dependency;
- CLI / entry point / console script;
- subprocess / shell execution;
- mutation of any file under `benchmark-fixtures/`;
- modification of `ai-search/00-controller-checklist.md`;
- modification of any WO-50 through WO-59 module or test file;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Section M of that document is treated as deferred
discussion notes only, not authorization. Real-benchmark-ready
remains NO.

## 15. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_external_source_acquisition_boundary`
  -> 39/39 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 713/713 OK after the new module and tests were added (674
  prior baseline + 39 new).
- The WO-50 through WO-59 modules and their test files are
  unchanged on disk during this Work Order.
- `ai-search/00-controller-checklist.md` is unchanged on disk
  during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.
- The module source contains no file-IO / network / hash /
  retrieval-verb / external-integration tokens, and does not use
  the `requests` HTTP library (verified by static-scan tests).

Codex review-time hardening added deterministic origin-mode count
ordering:

- `ORIGIN_MODE_ORDER = ("url", "local_path", "pasted_text")`
  now records the packet order explicitly.
- `ALLOWED_ORIGIN_MODES` remains the bounded membership set but is
  derived from `ORIGIN_MODE_ORDER`.
- `origin_mode_counts` is built from `ORIGIN_MODE_ORDER`, not from
  the unordered membership set.
- Regression test
  `test_origin_mode_count_order_is_deterministic` verifies the
  clean-pass output order.

Codex verified after hardening:

- `python -B -m unittest harness.tests.test_scaffold_external_source_acquisition_boundary -v`
  -> 40/40 OK.
- `python -B -m unittest discover -s harness/tests -v`
  -> 714/714 OK (674 prior baseline + 40 WO-60 tests).

Real-benchmark-ready remains NO.
