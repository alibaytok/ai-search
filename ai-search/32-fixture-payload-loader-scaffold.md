# ai-search - Fixture Payload Loader Scaffold

Document type: Phase 4 / Phase 9 / Fixture payload loader scaffold boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-32

---

## 1. Purpose

This document records the scaffold-internal fixture payload loader
authorized under WO-32 / DC-035 at `harness/payload_loader.py`. The
loader reads and validates the first synthetic fixture payload wave
authored under WO-31 / DC-034 at `benchmark-fixtures/<class>/wave-001.json`
for the three admitted classes (`golden-intents`, `hard-negatives`,
`boundary-violations`). The loader performs admission validation only;
it does not execute benchmarks, does not score, does not select an
architecture, and does not convert payloads into validation evidence.

WO-32 is the natural follow-on to WO-31. WO-31 authored the synthetic
payload content; WO-32 makes that content programmatically readable
through a validated boundary. Loader success returns the parsed
payload object plus a single `fixture_payload_loaded` event; loader
failure raises a named exception after recording an explicit halt
event into the EventLog. The loader is not wired into the dry-run
under WO-32; a future Codex packet may wire it in under separate
scope.

WO-32 is scaffold-internal only. It does not author a production
manifest schema (OQ-076 remains OPEN). It does not author run artifact
retention or storage policy (OQ-056 remains OPEN). It does not vest
configuration registration authority (OQ-057 remains OPEN). It does
not select any retrieval architecture, vendor, library, index family,
ANN backend, neural re-scorer, retrieval family, ablation cell,
multi-stage variant, or production system. The Indexing Excellence
Gate (`00-controller-checklist.md` Section K) continues to govern
selection.

## 2. Loader Scope

The loader exposes one public function at module
`harness/payload_loader.py`:

    load_fixture_payload(payload_path, expected_fixture_class, event_log)

- `payload_path` is the absolute or relative path to a JSON file under
  `benchmark-fixtures/<class>/`. The loader does not invent paths; it
  reads only what the caller passes.
- `expected_fixture_class` is the class name the caller asserts the
  payload should declare; the loader rejects on mismatch.
- `event_log` is a `harness.event_log.EventLog` instance owned by the
  caller. The loader never creates an event log on its own.

The loader returns the parsed JSON object on success and raises a
named exception on rejection. The loader writes no file, mutates no
payload, executes no retrieval, invokes no mock adapter, calls no
dry-run, collects no metric, infers no benchmark readiness, and infers
no architecture selection. It is Python standard library only beyond
harness-internal imports (`harness.review_package.FORBIDDEN_PHRASES`).

## 3. First-Wave Classes Admitted

The loader admits, under WO-32, the three classes admitted under
WO-31 / DC-034:

- `golden-intents`
- `hard-negatives`
- `boundary-violations`

The three excluded WO-31 classes (`latency-profiles`,
`update-profiles`, `adversarial`) continue to be excluded; their
subdirectories remain `.gitkeep`-only at the skeleton level
(enforced by `harness/tests/test_fixture_skeleton.py`). A future
Codex packet may admit one or more excluded classes; WO-32 does not
preempt that decision and the loader's `expected_fixture_class`
parameter is open to any string that a future packet authorizes.

## 4. Read-Only Inputs

The loader reads exactly one input class per invocation: a single
JSON payload file at the caller-provided `payload_path`. The loader
does not read:

- Any file under `harness/` other than its own imports.
- Any file under `ai-search/`.
- Any other file under `benchmark-fixtures/` than the one named.
- Any external content, network endpoint, or production-like state.

The loader does not derive `payload_path` from any payload contents
and does not enumerate directories. Per-payload validation is bounded
to the file at the path the caller passes.

## 5. Validation Order

The loader applies the following ordered checks. Codex review-time hardening requires non-empty fixture ids and explicit per-entry plane-separation marker objects. Earlier checks halt
the loader before any later check runs:

1. **JSON parse.** Open `payload_path` read-only with UTF-8 encoding
   and parse via `json.load`. Parse failure raises
   `MalformedPayloadJSON` after a `payload_malformed_json` halt
   event.
2. **Top-level object.** The parsed value must be a `dict`. Otherwise
   raise `NonObjectPayload` after a `payload_non_object` halt event.
3. **Marker present.** The top-level dict must have the
   `_fixture_payload_marker` key. Otherwise raise
   `MissingPayloadMarker` after a `payload_missing_marker` halt event.
4. **Marker valid.** The marker value must be a string containing each
   of the three required substrings: `harness-internal`, `synthetic`,
   and `not benchmark evidence`. Otherwise raise
   `InvalidPayloadMarker` after a `payload_invalid_marker` halt event
   (with `marker_type` or `missing_required_substring` payload field).
5. **`fixture_class` matches expected.** The payload's `fixture_class`
   must be present and must equal `expected_fixture_class`. Otherwise
   raise `PayloadFixtureClassMismatch` after a
   `payload_fixture_class_mismatch` halt event.
6. **`fixture_version` present.** The payload must have a
   `fixture_version` key. Otherwise raise
   `MissingPayloadFixtureVersion` after a
   `payload_missing_fixture_version` halt event.
7. **`entries` non-empty list.** The payload must carry an `entries`
   list with at least one element. Otherwise raise
   `EmptyOrMissingPayloadEntries` after a
   `payload_empty_or_missing_entries` halt event.
8. **Per-entry `fixture_id`.** Every entry must be a dict carrying a
   non-empty string `fixture_id`. Otherwise raise `MissingEntryFixtureId`
   after a `payload_missing_entry_fixture_id` halt event.
9. **fixture_ids unique within file.** No two entries may share a
   `fixture_id`. Otherwise raise `DuplicateEntryFixtureId` after a
   `payload_duplicate_entry_fixture_id` halt event.
10. **Per-entry synthetic marker.** Every entry must carry
    `synthetic_only is True` or `no_production_user_data is True`.
    Otherwise raise `MissingEntrySyntheticMarker` after a
    `payload_missing_entry_synthetic_marker` halt event.
11. **Per-entry plane-separation marker.** Every entry must carry a
    `plane_separation_markers` object. Otherwise raise
    `MissingPlaneSeparationMarkers` after a
    `payload_missing_plane_separation_markers` halt event.
12. **`FORBIDDEN_PHRASES` absent.** No string scalar anywhere in the
    payload may contain any phrase from
    `harness.review_package.FORBIDDEN_PHRASES`. Otherwise raise
    `ForbiddenLanguageInPayload` after a `payload_forbidden_language`
    halt event.
13. **Vendor / model denylist absent.** No string scalar may
    word-boundary-match any name in the loader's `VENDOR_DENYLIST`.
    Otherwise raise `VendorMentionInPayload` after a
    `payload_vendor_mention` halt event.
14. **`FORBIDDEN_CLAIM_PHRASES` absent.** No string scalar may contain
    any positive-claim phrase from the loader's
    `FORBIDDEN_CLAIM_PHRASES` tripwire list. Otherwise raise
    `ForbiddenClaimInPayload` after a `payload_forbidden_claim` halt
    event.
15. **Plane name in WO-21 set.** Every plane name in any plane
    separation marker must be one of the five plane names from
    `21-retrieval-adapter-contract.md` Section 3
    (`official_route_results`, `candidate_route_results`,
    `normalized_material_support_results`,
    `source_quality_constraint_observations`,
    `trace_outcome_signal_observations`). Otherwise raise
    `UnknownPlaneNameInPayload` after a
    `payload_unknown_plane_name` halt event.
16. **No plane overlap.** For each entry, the union of
    `expected_plane` / `allowed_planes` /
    `correct_plane_for_this_content` (the "expected/allowed/correct"
    set) and the union of `forbidden_planes` /
    `violation_plane_in_observed_output` / `forbidden_plane_collapse`
    (the "forbidden" set) must be disjoint. Otherwise raise
    `PlaneOverlapInPayload` after a `payload_plane_overlap` halt
    event.
17. **Success.** Record a single `fixture_payload_loaded` event into
    the EventLog with `path`, `fixture_class`, `fixture_version`,
    `entry_count`, and `entry_fixture_ids` (ordered list). Return the
    parsed payload object.

No rejection path returns. No silent admission is permitted. The check
order is fixed; later checks never run when an earlier check halts.

## 6. Rejection Classes And Halt Behavior

Each rejection class is recorded as both an exception and a halt
event:

| Condition                                     | Exception                          | Halt event reason                          |
|-----------------------------------------------|------------------------------------|--------------------------------------------|
| JSON parse failure                            | `MalformedPayloadJSON`             | `payload_malformed_json`                   |
| Top-level not a `dict`                        | `NonObjectPayload`                 | `payload_non_object`                       |
| Marker key missing                            | `MissingPayloadMarker`             | `payload_missing_marker`                   |
| Marker value not a string                     | `InvalidPayloadMarker`             | `payload_invalid_marker`                   |
| Marker missing a required substring           | `InvalidPayloadMarker`             | `payload_invalid_marker`                   |
| `fixture_class` missing / mismatch            | `PayloadFixtureClassMismatch`      | `payload_fixture_class_mismatch`           |
| `fixture_version` missing                     | `MissingPayloadFixtureVersion`     | `payload_missing_fixture_version`          |
| `entries` missing / not list / empty          | `EmptyOrMissingPayloadEntries`     | `payload_empty_or_missing_entries`         |
| Entry missing non-empty `fixture_id` string   | `MissingEntryFixtureId`            | `payload_missing_entry_fixture_id`         |
| Two entries share `fixture_id`                | `DuplicateEntryFixtureId`          | `payload_duplicate_entry_fixture_id`       |
| Entry missing synthetic / no-prod marker      | `MissingEntrySyntheticMarker`      | `payload_missing_entry_synthetic_marker`   |
| Entry missing plane-separation marker object  | `MissingPlaneSeparationMarkers`    | `payload_missing_plane_separation_markers` |
| `FORBIDDEN_PHRASES` substring hit             | `ForbiddenLanguageInPayload`       | `payload_forbidden_language`               |
| `VENDOR_DENYLIST` word-boundary hit           | `VendorMentionInPayload`           | `payload_vendor_mention`                   |
| `FORBIDDEN_CLAIM_PHRASES` substring hit       | `ForbiddenClaimInPayload`          | `payload_forbidden_claim`                  |
| Plane name not in WO-21 plane set             | `UnknownPlaneNameInPayload`        | `payload_unknown_plane_name`               |
| Plane overlap expected/allowed/correct vs forbidden | `PlaneOverlapInPayload`      | `payload_plane_overlap`                    |

Halt events are recorded into the caller-owned `event_log` before the
exception is raised. Every halt event carries `path=payload_path` plus
a per-reason diagnostic field (e.g. `forbidden_phrase`, `vendor_name`,
`unknown_plane`, `overlapping_planes`, `duplicate_fixture_id`,
`entry_fixture_id`).

## 7. Event Boundary

On success, the loader records exactly one
`fixture_payload_loaded` event with the following fields:

- `path`: the caller-provided `payload_path`.
- `fixture_class`: the payload's `fixture_class` (matches
  `expected_fixture_class`).
- `fixture_version`: the payload's `fixture_version`.
- `entry_count`: the integer length of `entries`.
- `entry_fixture_ids`: an ordered list of the entries' `fixture_id`
  values, preserving payload order.

On every rejection, the loader records exactly one halt event with
the table-row fields above before raising. No other event type is
recorded by this loader.

The event log is the caller's; the loader holds no reference to it
beyond the call.

## 8. No-Mutation Guarantee

The loader writes no file. It opens `payload_path` in read-only mode
(`"r"`) with UTF-8 encoding. It does not call `open` in any other
mode. The test
`NoFilesystemWriteOnSuccessTest.test_loader_performs_no_filesystem_writes_during_success`
monkey-patches `builtins.open` so any write-mode invocation
(`"w"`, `"a"`, `"x"`, or any mode containing `"+"`) fails the test.

The loader does not mutate the payload object it returns. It does not
add fields, remove fields, normalize values, or transform the dict.
The returned object is the value `json.load` produced.

The loader does not modify any existing fixture payload file. The
test `SuccessfulLoadTest.test_success_path_does_not_modify_existing_payload_files`
computes a SHA-256 of each on-disk WO-31 payload before and after
loading and asserts equality.

The loader does not touch any other file or any production-like
state.

## 9. Relationship To WO-29 / WO-30 / WO-31

The loader sits inside the constraint surface established by the
prior three packets:

- `29-fixture-payload-contract-boundary.md` (WO-29 / DC-032) recorded
  the documentation-level contract boundary for what future benchmark
  fixture payloads must and must not represent. The loader's
  rejection list (vendor / model names, validation / trust / benchmark
  / production / architecture claim phrases, source / provenance
  fields) directly implements that boundary's prohibitions.
- `30-fixture-payload-format-boundary.md` (WO-30 / DC-033) recorded
  the scaffold-internal JSON format for the first wave. The loader's
  file-level and entry-level checks implement that format's
  conceptual properties (marker, `fixture_class`, `fixture_version`,
  non-empty `entries`, per-entry `fixture_id` / `purpose` / synthetic
  marker / plane-separation markers).
- `31-first-synthetic-fixture-payload-wave.md` (WO-31 / DC-034)
  authored the synthetic payload files. The loader is exercised
  against each of those files (one per admitted class) in
  `SuccessfulLoadTest`, and its plane-overlap detection matches the
  plane-marker keys those files use (`expected_plane`,
  `allowed_planes`, `correct_plane_for_this_content`,
  `forbidden_planes`, `violation_plane_in_observed_output`,
  `forbidden_plane_collapse`).

The loader is not wired into `harness/dry_run.py` under WO-32. A
future Codex packet may wire it in under separate scope; the loader's
public function signature is stable for that wiring.

## 10. Forbidden Scope

The WO-32 scaffold is forbidden from doing any of the following:

- Modifying any existing fixture payload file
  (`benchmark-fixtures/<class>/wave-001.json` or any `.gitkeep`).
- Modifying `benchmark-fixtures/README.md`.
- Modifying `harness/dry_run.py` or any existing harness implementation
  module.
- Modifying `harness/tests/test_fixture_payloads.py` or
  `harness/tests/test_fixture_skeleton.py`.
- Authoring a fixture loader registration mechanism, a production
  artifact schema, a retention policy, a storage policy, a directory
  layout, a sharding scheme, an archive format, a signature scheme,
  or a version-pinning scheme.
- Authoring a configuration registration authority decision.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
  All seven remain OPEN.
- Performing benchmark execution.
- Authoring metric thresholds, quality or performance scoring,
  ranking formulas, runtime compile internals, or validation
  framework implementations.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Adding third-party dependencies.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Duplicating RK-039 (benchmark dataset contamination by production
  user feedback or recent traces); the existing RK-039 reference
  established under WO-29 / DC-032 Section 9 continues to apply.
- Wiring the loader into `harness/dry_run.py` under WO-32.

## 11. Not Benchmark Evidence; Not Validation Evidence; Not Production Readiness; Not Architecture Selection

Loader success is explicitly:

- **Not benchmark evidence.** The loader admits a payload; it does not
  measure anything, score anything, or produce any metric. The
  returned object is the parsed JSON only.
- **Not validation evidence.** The loader does not record any
  validation outcome against any candidate or official route.
  Validation evidence is recorded by the validation framework
  (`08-validation-and-feedback.md`); a loaded payload remains a
  benchmark input, not a validation input.
- **Not production readiness.** The loader admits scaffold-internal
  synthetic content only. A successful load proves admission against
  the WO-30 / DC-033 conceptual shape; it does not prove production
  readiness, production schema sufficiency, or production artifact
  contract satisfaction. OQ-076 remains OPEN.
- **Not architecture selection.** Loader success makes no
  architecture, vendor, library, ANN backend, neural re-scorer,
  retrieval family, ablation cell, multi-stage variant, or
  production-system claim. The Indexing Excellence Gate
  (`00-controller-checklist.md` Section K) continues to govern
  selection.

Future fixture loader integration into the dry-run, future payload
waves, future class admission for the three currently excluded
classes, future production artifact contract authoring, future
benchmark execution, and future architecture selection each require
separate future Codex packets. WO-32 / DC-035 authorizes none of
these.
