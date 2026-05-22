# ai-search - Scaffold URL Acquisition Executor (Injected Fetcher, In-Memory Only)

Document type: Phase 2 / Phase 4 / Phase 9 / Scaffold URL-acquisition boundary
Owner: Codex (controller)
Author: Claude (under WO-61)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-61

---

## 1. Purpose

WO-61 adds the first controlled online-source acquisition step
after the WO-60 acquisition-boundary layer. WO-60 records URL /
local / paste acquisition requests but does not fetch. WO-61 may
execute URL acquisition, but only through an injected fetcher
callable supplied by the caller (and stubbed by tests). The module
itself does not import any networking, HTTP, filesystem, shell, or
process-spawning client, and does not perform direct network IO.
Tests stay deterministic; no real internet dependency.

### What this is NOT

- NOT a crawler / downloader / browser automation framework.
- NOT recursive URL discovery; NOT HTML parsing; NOT markdown
  parsing; NOT retry logic; NOT follow-redirect logic.
- NOT real indexing; NOT real retrieval; NOT prompt search / skill
  search / agent selection / generic RAG.
- NOT source qualification; NOT corpus admission; NOT a Source
  Card; NOT a Route Card; NOT a route validator.
- NOT benchmark execution; NOT a benchmark-readiness flip; NOT
  architecture / vendor / library / index family / production
  system selection.
- NOT IDE / extension / Copilot / Waza / VS Code / LLM / model
  integration.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Accept WO-60-style URL acquisition request dicts (restricted to
  `origin_mode == "url"`).
- Invoke a caller-supplied `fetch_url` callable exactly once per
  validated request, in input order, only after all requests have
  been validated.
- Compute a SHA-256 prefix over the already-returned `content_bytes`
  as identity / integrity metadata only.
- Preserve every output authorization / readiness / selection
  boolean as literal False; preserve `corpus_admitted_count` /
  `qualified_count` / `source_material_extracted_count` as literal
  0; preserve every per-reference admission boolean as literal
  False.
- Never echo raw URL or raw bytes into output; record only
  structural markers (`origin_locator_length`, `content_byte_length`,
  `content_hash_prefix`, `content_type`, `fetched_at`).
- Bound each fetcher result by `MAX_FETCHED_BYTES = 65536`.
- Do NOT invoke any WO-50 through WO-60 public function.

The scope does not authorize real adapter invocation, real benchmark
execution, direct network IO, file IO, hash computation outside the
narrow content-bytes SHA-256, extraction, normalization, candidate-
fragment derivation, similarity / ranking / scoring, model judgment,
architecture / vendor / library / index family / production system
choice, IDE / extension / Copilot / Waza / VS Code / LLM
integration, or any benchmark-readiness change.

## 3. Added Files

WO-61 adds:

- `harness/scaffold_url_acquisition_executor.py`
- `harness/tests/test_scaffold_url_acquisition_executor.py`
- `ai-search/61-scaffold-url-acquisition-executor.md`

WO-61 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 through
WO-60 modules and their test files are not modified.
`ai-search/00-controller-checklist.md` is not modified.

## 4. Public Function

```text
run_scaffold_url_acquisition_executor(acquisition_requests, fetch_url, event_log) -> dict
```

Inputs:

- `acquisition_requests`: a list (possibly empty) of WO-60-style
  acquisition request dicts, restricted to `origin_mode == "url"`.
- `fetch_url`: a caller-supplied callable taking a URL string and
  returning a dict with exactly four keys (`fetch_status`,
  `content_bytes`, `content_type`, `fetched_at`).
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no direct network
call, does not invoke any WO-50 through WO-60 public function, and
uses `hashlib` only for SHA-256 over the already-returned
`content_bytes`.

## 5. Two-Pass Design

The module runs two passes:

1. **Validate all requests.** For each request: enforce shape,
   required fields, no unknown keys, no forbidden Source-Card- /
   derived-material- / route-shaped / benchmark-fixture-shaped
   fields, `origin_mode == "url"`, non-empty `origin_locator`,
   bounded `declared_kind`, `content_available is False`,
   `content_byte_length == 0`, `content_hash == ""`, no duplicate
   `request_id`, no duplicate `origin_locator`. If any validation
   fails, the fetcher is NOT called.
2. **Invoke fetcher.** For each validated request, invoke
   `fetch_url(origin_locator)` exactly once in input order;
   validate the returned dict; compute the hash prefix; assemble
   the acquired reference.

## 6. Required Request Fields

Exactly eight (`REQUIRED_REQUEST_FIELDS`): `request_id`,
`origin_mode`, `origin_locator`, `declared_kind`, `content_available`,
`content_byte_length`, `content_hash`, `observed_at`.

`origin_mode` must equal `"url"`.
`declared_kind` must be in the WO-55 bounded label set
(`prompt_collection`, `skill_collection`,
`agent_description_collection`, `tool_description_collection`,
`document_collection`).
`content_available` must be literal `False`; `content_byte_length`
must be `0`; `content_hash` must be `""`.

## 7. Forbidden Request Fields

Twenty-eight forbidden Source-Card-shaped, derived-material,
route-shaped, and benchmark-fixture-shaped fields are rejected
(same set as WO-60). Each rejection records a halt event before
raising `ForbiddenUrlAcquisitionField`.

## 8. Required Fetcher Result Fields

Exactly four (`REQUIRED_FETCHER_RESULT_FIELDS`): `fetch_status`,
`content_bytes`, `content_type`, `fetched_at`.

- `fetch_status` must equal `"fetched"`.
- `content_bytes` must be non-empty `bytes`; `bytearray` is
  rejected.
- `len(content_bytes) <= MAX_FETCHED_BYTES` (65536).
- `content_type` must be a non-empty string.
- `fetched_at` must be a non-empty string.

Unknown keys in the fetcher result are rejected with
`UnknownFetcherResultField`.

## 9. Result Surface (Clean-Pass Only)

On clean pass, the module returns a fresh dict with exactly
thirteen allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `url_acquisition_kind`
- `request_count`
- `fetched_count`
- `acquired_references` (list of structural acquired refs)
- `total_content_byte_length`
- `corpus_admitted_count` (literal `0`)
- `qualified_count` (literal `0`)
- `source_material_extracted_count` (literal `0`)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `url_acquisition_note`

Each `acquired_references` entry contains only structural data:

- `request_id`
- `declared_kind`
- `origin_locator_observed: True`
- `origin_locator_length`
- `content_available: True`
- `content_byte_length`
- `content_hash_prefix` (first 12 chars of SHA-256 hex digest)
- `content_type`
- `fetched_at`
- `corpus_admitted: False`
- `qualified: False`
- `source_material_extracted: False`
- `route_object_created: False`

Raw URL (`origin_locator`), raw `content_bytes`, and full
`content_hash` are NOT echoed.

## 10. Event Surface

Success events:

- `scaffold_url_acquisition_executor_started`
- `scaffold_url_acquisition_executor_request_validated`
- `scaffold_url_acquisition_executor_fetch_started`
- `scaffold_url_acquisition_executor_fetch_completed`
- `scaffold_url_acquisition_executor_passed`

Halt events are recorded with `scaffold_url_acquisition_executor_*`
reasons before raising the corresponding named exception.

## 11. Named Exceptions

- `NonListUrlAcquisitionRequests`
- `NonObjectUrlAcquisitionRequest`
- `MissingUrlAcquisitionRequestField`
- `UnknownUrlAcquisitionRequestField`
- `DuplicateUrlAcquisitionRequestId`
- `DuplicateUrlOriginLocator`
- `NonUrlOriginModeRejected`
- `InvalidUrlOriginLocator`
- `InvalidDeclaredKind`
- `InputContentAlreadyAvailableRejected`
- `ForbiddenUrlAcquisitionField`
- `FetcherNotCallable`
- `FetcherReturnedNonObject`
- `MissingFetcherResultField`
- `UnknownFetcherResultField`
- `InvalidFetchStatus`
- `InvalidFetchedContentBytes`
- `FetchedContentTooLarge`
- `InvalidFetchedContentType`
- `InvalidFetchedAt`
- `ForbiddenLanguageInUrlAcquisitionOutput`

## 12. Tests Added

`harness/tests/test_scaffold_url_acquisition_executor.py` adds 48
tests across nine `TestCase` classes covering:

- clean pass with empty list; clean pass with one URL; clean pass
  with multiple URLs in input order;
- literal-False authorization / readiness / selection booleans;
- per-reference literal-False admission booleans;
- literal-zero admission / extraction counts;
- deterministic SHA-256 prefix over fake fetcher bytes;
- `total_content_byte_length` is the sum;
- `_passed` event records clean counts;
- raw URL not echoed; raw bytes not echoed;
- non-list / non-dict / each missing field rejected before any
  fetcher call;
- unknown field rejected;
- each of the 28 forbidden input fields rejected individually
  before any fetcher call;
- duplicate `request_id` / duplicate `origin_locator` rejected
  before any fetcher call;
- `local_path` / `pasted_text` origin rejected;
- invalid `origin_locator` / `declared_kind` rejected;
- `content_available: True` / non-zero byte length / non-empty hash
  on input rejected;
- fetcher non-callable rejected;
- fetcher non-dict return / missing field / unknown field / invalid
  status / non-bytes / bytearray / empty / oversized / invalid
  content_type / invalid fetched_at rejected;
- forbidden language in fetcher result halts (with
  `ForbiddenLanguageInUrlAcquisitionOutput`);
- output forbidden-language scan;
- input not mutated; no filesystem writes;
- module imports only stdlib (`hashlib`) plus harness-internal;
- module source contains no `open(` / `pathlib` / `urllib` /
  `http.client` / `socket` / `subprocess` / `os.system` / `shutil`
  tokens, and no `import requests` / `from requests` /
  `requests.` library-use forms;
- module source contains no `def query` / `def search` /
  `def retrieve` / `def rank` tokens;
- module source contains no `run_scaffold_*` references to WO-50
  through WO-60 public functions;
- module source contains no `copilot` / `waza` / `vscode` /
  `vs_code` / `openai` / `anthropic` / `claude_api` / `llm`
  tokens;
- `benchmark-fixtures/` files not mutated;
- `MAX_FETCHED_BYTES == 65536`; `ALLOWED_DECLARED_KINDS` matches
  WO-55.

## 13. Non-Claim Constraint

The WO-47 through WO-60 explicit non-claim constraint carries
forward verbatim:

This module does not claim that any acquired reference, origin
mode, declared kind, content-availability marker, hash prefix, or
in-memory observation is sufficient, necessary, superior, best,
complete, production-ready, recommended, or selected. The bounded
admission surface, the eight required request fields, the four
required fetcher result fields, the 28 forbidden input fields, and
the `MAX_FETCHED_BYTES` cap are bounded by WO-61 and are not
claimed exhaustive.

The module records in-memory acquired references only. It does
not declare any referenced source admissible, qualified,
extractable, normalizable, fragment-derivable, route-valid, or
selected for any production system.

## 14. Forbidden Scope

WO-61 does not authorize:

- real benchmark execution;
- real or mock adapter invocation (the injected fetcher is NOT a
  retrieval adapter);
- direct network calls from the module;
- crawler loops or recursive URL discovery;
- HTML / markdown parsing;
- retry or follow-redirect logic;
- local file read or file write;
- hash computation over anything except the already-returned
  `content_bytes`;
- extraction, normalization, or candidate-fragment derivation;
- similarity, distance, near-match, or scoring of any kind;
- quality, performance, or operational metric collection;
- ranking or winner declarations;
- model judgments, fuzzy semantic analysis, thresholds, or
  weights;
- architecture, vendor, library, index family, ANN backend,
  neural re-scoring, retrieval family, ablation cell, multi-stage
  variant, or production system choice;
- IDE / extension / chat / collaborator / Copilot / Waza /
  VS Code / LLM integration;
- prompt / skill / agent evaluation;
- Source Card creation;
- Route Card creation;
- production artifact schema, retention, storage, immutability,
  access-control, or registration policy;
- third-party dependency;
- CLI / entry point / console script;
- shell or process-spawning execution;
- mutation of any file under `benchmark-fixtures/`;
- modification of `ai-search/00-controller-checklist.md`;
- modification of any WO-50 through WO-60 module or test file;
- direct invocation of WO-50 through WO-60 public functions;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Section M of that document is treated as deferred
discussion notes only. Real-benchmark-ready remains NO.

## 15. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_url_acquisition_executor`
  -> 47/47 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 761/761 OK after the new module and tests were added (714
  prior baseline + 47 new).
- The WO-50 through WO-60 modules and their test files are
  unchanged on disk during this Work Order.
- `ai-search/00-controller-checklist.md` is unchanged on disk
  during this Work Order.
- No new `__pycache__` directories were created at project paths
  under Claude's control.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified during this Work Order.
- No real internet was used; every test supplies a fake fetcher
  callable.
- The module source has been statically inspected (via tests) for
  the absence of file-IO / network / shell / process-spawning /
  external-integration tokens and for the absence of any WO-50
  through WO-60 public-function name.

Codex review-time hardening tightened the fetcher output contract
to the packet's `bytes only` requirement:

- `bytearray` is now rejected by `InvalidFetchedContentBytes`
  instead of being converted to `bytes`.
- Regression test `test_fetcher_bytearray_content_rejected` was
  added.

Codex verified after hardening:

- `python -B -m unittest harness.tests.test_scaffold_url_acquisition_executor -v`
  -> 48/48 OK.
- `python -B -m unittest discover -s harness/tests -v`
  -> 762/762 OK (714 prior baseline + 48 WO-61 tests).

Real-benchmark-ready remains NO.
