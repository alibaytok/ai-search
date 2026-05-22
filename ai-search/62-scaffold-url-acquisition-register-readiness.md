# ai-search - Scaffold URL Acquisition Register-Readiness Diagnostic

Document type: Phase 2 / Phase 4 / Phase 9 / Scaffold register-readiness diagnostic boundary
Owner: Codex (controller)
Author: Claude (under WO-62)
Status: Approved with notes after Codex review-time hardening
Work Order: WO-62

---

## 1. Purpose

WO-62 adds a scaffold-only diagnostic that inspects a WO-61 URL
acquisition observation and determines whether it is sufficient to
produce WO-55-compatible source reference records.

WO-61 intentionally does NOT echo the raw URL (`origin_locator`)
or the full `content_hash`; it surfaces only structural markers
(`origin_locator_observed: True`, `origin_locator_length`) and a
12-character `content_hash_prefix`. The WO-55 quarantine register
requires the full `origin` string and the full `hash` string. WO-62
makes that gap explicit and testable: for a clean WO-61
observation, the diagnostic returns `register_projection_ready:
False` plus named blocked reasons and a `missing_register_fields`
list naming exactly `origin` and `hash`.

### What this is NOT

- NOT a bridge that emits WO-55 register records.
- NOT permission to invent `origin`.
- NOT permission to invent full `hash`.
- NOT permission to infer identity from `content_hash_prefix`.
- NOT permission to invoke the WO-55 register.
- NOT real indexing / retrieval / search / ranking / scoring;
  NOT source qualification; NOT corpus admission; NOT a Source
  Card; NOT a Route Card; NOT a route validator;
  NOT benchmark execution; NOT architecture / vendor / library /
  index family / production system selection.
- NOT IDE / extension / Copilot / Waza / VS Code / LLM
  integration.

This is NOT a failure of WO-61. WO-61 is safe as an acquisition
observation. WO-62 simply records that WO-61's output is
structurally insufficient to be projected into the WO-55 register
without additional, separately-authorized identity material.

## 2. Section L Shared Scope

The shared scope for this Work Order is:

- Inspect one already-loaded WO-61-style URL acquisition
  observation dict.
- Verify it does not declare any admission / qualification /
  extraction / route-creation / measurement / benchmark-
  readiness claim.
- Verify it does not carry any raw URL / raw bytes / full hash /
  derived-material / route-shaped / Source-Card-shaped /
  benchmark-fixture-shaped field.
- Return a fresh fixed-shape diagnostic dict that records
  `register_projection_ready: False` plus named blocked reasons
  and the list of missing register fields.
- Do NOT invoke `run_scaffold_source_intake_register` (WO-55) or
  `run_scaffold_url_acquisition_executor` (WO-61); verified by
  static-scan tests.

The scope does not authorize real adapter invocation, real
benchmark execution, network calls, file IO, hash computation,
extraction, normalization, candidate-fragment derivation, identity
invention, register projection, similarity / ranking / scoring,
model judgment, architecture / vendor / library / index family /
production system choice, IDE / extension / Copilot / Waza /
VS Code / LLM integration, or any benchmark-readiness change.

## 3. Added Files

WO-62 adds:

- `harness/scaffold_url_acquisition_register_readiness.py`
- `harness/tests/test_scaffold_url_acquisition_register_readiness.py`
- `ai-search/62-scaffold-url-acquisition-register-readiness.md`

WO-62 also updates:

- `ai-search/00-open-questions.md`
- `ai-search/00-claude-task-ledger.md`

No file under `benchmark-fixtures/` is modified. The WO-50 through
WO-61 modules and their test files are not modified.
`ai-search/00-controller-checklist.md` is not modified.

## 4. Public Function

```text
run_scaffold_url_acquisition_register_readiness(url_acquisition_observation, event_log) -> dict
```

Inputs:

- `url_acquisition_observation`: one already-loaded WO-61-style
  observation dict.
- `event_log`: harness `EventLog`.

The function reads no file, writes no file, makes no network call,
computes no hash, and does not invoke WO-55 or WO-61 public
functions.

## 5. Inspection Rules

The diagnostic verifies, in this order:

1. `url_acquisition_observation` is a dict.
2. Every required top-level field is present
   (`url_acquisition_kind`, `request_count`, `fetched_count`,
   `acquired_references`, `total_content_byte_length`,
   `corpus_admitted_count`, `qualified_count`,
   `source_material_extracted_count`, `selection_made`,
   `measurement_authorized`, `real_benchmark_authorized`,
   `real_benchmark_ready`, `url_acquisition_note`).
3. `url_acquisition_kind` equals `"scaffold_url_acquisition_executor"`.
4. `acquired_references` is a list.
5. Every top-level authorization / readiness / selection boolean
   is literal False.
6. `corpus_admitted_count`, `qualified_count`,
   `source_material_extracted_count` are each literal 0.
7. No forbidden register-projection-shaped field appears at the
   top level (raw `origin_locator`, raw `content_bytes`, full
   `content_hash`, extracted / normalized / candidate fragments,
   route-shaped, Source-Card-shaped, benchmark-fixture-shaped
   fields).
8. The input's surfaced strings contain no forbidden language.
9. Every acquired reference is a dict containing every required
   field (`request_id`, `declared_kind`, `origin_locator_observed`,
   `origin_locator_length`, `content_available`,
   `content_byte_length`, `content_hash_prefix`, `content_type`,
   `fetched_at`, `corpus_admitted`, `qualified`,
   `source_material_extracted`, `route_object_created`).
10. Per-reference `corpus_admitted` / `qualified` /
    `source_material_extracted` / `route_object_created` are each
    literal False.
11. No per-reference forbidden register-projection field is
    present.

Any rejection records an explicit halt event before raising the
matching named exception.

## 6. Result Surface (Clean-Pass Only)

On clean pass, the diagnostic returns a fresh dict with exactly
fifteen allowed keys (`ALLOWED_OUTPUT_KEYS`):

- `readiness_kind`
- `url_acquisition_reference_count`
- `register_projection_ready` (literal `False`)
- `register_projection_blocked_reason_count` (literal `2` on every
  clean-pass path)
- `register_projection_blocked_reasons` (list containing
  `origin_not_available_for_wo55_register` and
  `full_hash_not_available_for_wo55_register`)
- `missing_register_fields` (list `["origin", "hash"]`)
- `safe_to_invent_missing_identity` (literal `False`)
- `source_register_invocation_authorized` (literal `False`)
- `corpus_admitted_count` (literal `0`)
- `qualified_count` (literal `0`)
- `selection_made` (literal `False`)
- `measurement_authorized` (literal `False`)
- `real_benchmark_authorized` (literal `False`)
- `real_benchmark_ready` (literal `False`)
- `readiness_note`

The diagnostic always reports `register_projection_ready: False`
on a structurally-valid WO-61 observation, because WO-61 by
construction never carries the raw `origin` or full `hash`.

## 7. Event Surface

Success events:

- `scaffold_url_acquisition_register_readiness_started`
- `scaffold_url_acquisition_register_readiness_reference_observed`
- `scaffold_url_acquisition_register_readiness_blocked`

Halt events are recorded with
`scaffold_url_acquisition_register_readiness_*` reasons before
raising the corresponding named exception.

## 8. Named Exceptions

- `NonObjectUrlAcquisitionObservation`
- `InvalidUrlAcquisitionKind`
- `MissingUrlAcquisitionObservationField`
- `InvalidAcquiredReferences`
- `NonObjectAcquiredReference`
- `MissingAcquiredReferenceField`
- `UnsafeAdmissionClaimInUrlAcquisitionObservation`
- `ForbiddenRegisterProjectionFieldPresent`
- `ForbiddenLanguageInRegisterReadinessDiagnostic`

## 9. Tests Added

`harness/tests/test_scaffold_url_acquisition_register_readiness.py`
adds 53 tests across nine `TestCase` classes after Codex
review-time hardening, covering:

- clean-pass shape; `register_projection_ready: False` literal;
  blocked reasons; missing register fields exactly
  `["origin", "hash"]`; `safe_to_invent_missing_identity: False`;
  `source_register_invocation_authorized: False`; literal-False
  authorization booleans; literal-zero admission counts; empty
  acquired-references list still blocked; `_blocked` event with
  counts; per-reference `_reference_observed` event;
- non-dict observation; wrong `url_acquisition_kind`; each
  missing top-level field; non-list `acquired_references`; each
  per-reference type / missing-field / per-reference admission-
  True case; each top-level authorization-True / count-non-zero
  case; per-reference and top-level forbidden-field rejection
  (raw `origin_locator`, raw `content_bytes`, full `content_hash`,
  derived material, candidate fragments, route-shaped,
  Source-Card-shaped, benchmark-fixture-shaped);
- output forbidden-language scan; input forbidden-language scan
  (defense-in-depth);
- input isolation; no filesystem writes;
- only stdlib + harness-internal imports;
- module source contains no `open(` / `pathlib` / `urllib` /
  `http.client` / `socket` / `subprocess` / `os.system` /
  `shutil` / `hashlib` /
  `.hexdigest` / `.sha256` tokens, no `import requests` /
  `from requests` / `requests.` library-use forms;
- module source does not invoke
  `run_scaffold_source_intake_register` (WO-55) or
  `run_scaffold_url_acquisition_executor` (WO-61);
- `benchmark-fixtures/` files not mutated.

Codex review-time hardening added:

- `test_per_reference_raw_content_bytes_rejected`, ensuring raw
  `content_bytes` is rejected at the per-reference layer as well
  as the top level.
- Static-scan coverage for `subprocess` and `os.system` tokens.

## 10. Non-Claim Constraint

The WO-47 through WO-61 explicit non-claim constraint carries
forward verbatim:

This module does not claim that any diagnostic record, blocked
reason, missing-field name, or in-memory observation is sufficient,
necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded admission surface (single
WO-61 observation kind, fixed required-field set, fixed forbidden-
field set, fixed two-entry blocked-reason list) is bounded by
WO-62 and is not claimed exhaustive.

The diagnostic records the structural gap between WO-61 acquired
references and WO-55 register records. It does not declare any
referenced source admissible, qualified, extractable,
normalizable, fragment-derivable, route-valid, or selected for any
production system.

## 11. Forbidden Scope

WO-62 does not authorize:

- real benchmark execution;
- real or mock adapter invocation;
- network calls of any kind;
- URL fetch / download / crawl / browser automation;
- local file read or file write;
- hash computation;
- extraction, normalization, or candidate-fragment derivation;
- invention of `origin` or full `hash`;
- inference of identity from `content_hash_prefix`;
- invocation of `run_scaffold_source_intake_register` (WO-55);
- invocation of `run_scaffold_url_acquisition_executor` (WO-61);
- similarity, distance, near-match, or scoring of any kind;
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
- modification of any WO-50 through WO-61 module or test file;
- closure of OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076;
- duplication of RK-039.

The Indexing Excellence Gate
(`ai-search/00-controller-checklist.md` Section K) continues to
govern selection. Real-benchmark-ready remains NO.

## 12. Verification Result

Claude verified, before submitting this entry:

- `python -B -m unittest harness.tests.test_scaffold_url_acquisition_register_readiness`
  -> 52/52 OK before tracker updates.
- `python -B -m unittest discover -s harness/tests`
  -> 814/814 OK after the new module and tests were added (762
  prior baseline + 52 new).
- The WO-50 through WO-61 modules and their test files are
  unchanged on disk.
- `ai-search/00-controller-checklist.md` is unchanged on disk.
- No new `__pycache__` directories.
- All new files are ASCII.
- Project root contents are `ai-search/`, `harness/`, and
  `benchmark-fixtures/` only.
- `benchmark-fixtures/` was not modified.
- The module source has been statically inspected for the absence
  of file-IO / network / hash tokens and for the absence of WO-55
  and WO-61 public-function names.

Codex verified after review-time hardening:

- `python -B -m unittest harness.tests.test_scaffold_url_acquisition_register_readiness -v`
  -> 53/53 OK.
- `python -B -m unittest discover -s harness/tests`
  -> 815/815 OK (762 prior baseline + 53 WO-62 tests).

Real-benchmark-ready remains NO.
