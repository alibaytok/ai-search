# ai-search - First Synthetic Fixture Payload Wave

Document type: Phase 4 / Phase 9 / First synthetic fixture payload wave boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-31 (revised; the original WO-31 packet halted correctly before file changes and was superseded by the revised packet)

---

## 1. Purpose

This document records the scope of the first synthetic fixture payload
wave authored under the revised WO-31 / DC-034 packet. The wave admits
three of the six benchmark fixture category subdirectories
(`golden-intents/`, `hard-negatives/`, `boundary-violations/`) under the
WO-30 / DC-033 format boundary, with one small synthetic JSON payload
file per admitted class and 2 entries per file. The other three
subdirectories (`latency-profiles/`, `update-profiles/`, `adversarial/`)
remain empty skeletons per WO-20 / DC-023.

This is not a production benchmark dataset. It is not validation
evidence for any candidate or official route. It is not production data
or user data. It is not a production artifact contract (OQ-076 remains
OPEN). It is not run artifact retention or storage policy (OQ-056
remains OPEN). It is not architecture, vendor, library, index family,
ANN backend, neural re-scorer, retrieval family, ablation cell,
multi-stage variant, or production-system selection.

## 2. Why The Original WO-31 Halted

The original WO-31 packet asked Claude to author payload files inside
the three admitted subdirectories but did not include
`harness/tests/test_fixture_skeleton.py` or
`benchmark-fixtures/README.md` in its allowed-files list. The skeleton
test enforced the WO-20 / DC-023 empty-only invariant on all six
categories and on every `.json` extension globally; admitting any
payload file would have failed the test, and the test could not be
relaxed within the original packet's scope.

Claude halted before any file change and submitted a halt-and-conflict
report. Codex accepted the halt as correct and reissued the revised
WO-31 packet with `harness/tests/test_fixture_skeleton.py` and
`benchmark-fixtures/README.md` added to the allowed-files list, plus
explicit skeleton-invariant transition instructions. The original
packet is superseded. The repository state at halt was preserved
exactly (89/89 tests passing; no payload file; no tracker or ledger
change).

The halt is recorded in the WO-31 ledger entry as a procedure-quality
event: scope conflicts are halt-and-report, not silently bypass.

## 3. Skeleton Invariant Transition

`harness/tests/test_fixture_skeleton.py` is rewritten under WO-31 /
DC-034 to scope its invariants by class:

- The three excluded classes (`latency-profiles`, `update-profiles`,
  `adversarial`) continue to enforce the WO-20 / DC-023 empty-only
  invariant exactly: each must contain only `.gitkeep`.
- The three admitted classes (`golden-intents`, `hard-negatives`,
  `boundary-violations`) may now contain `.gitkeep` plus one or more
  `*.json` payload files; no other entry is admitted at the skeleton
  level.
- Non-JSON payload extensions (`.csv`, `.txt`) remain forbidden anywhere
  under `benchmark-fixtures/`.
- Payload-content validation for admitted JSON files is delegated to
  the new `harness/tests/test_fixture_payloads.py`.
- The README check is updated to require the existing WO-20 literal
  phrases (`"no real benchmark data"` and `"future Codex packet"`) plus
  WO-31 scoping language (`"scaffold-internal"`, `"synthetic"`, the
  names of each admitted class, and the names of each excluded class).

The transition is the minimum surface change needed to admit the first
wave. No harness implementation module is touched.

## 4. Admitted First-Wave Classes

The three admitted classes match the WO-30 / DC-033 Section 5
restriction. One payload file per class is authored under WO-31 /
DC-034:

- `benchmark-fixtures/golden-intents/wave-001.json` - 2 entries: one
  expected-official-route case (`expected_outcome_class:
  "official_route_expected"`) and one expected-miss case
  (`expected_outcome_class: "miss_expected"`,
  `miss_classification: "no_official_route_exists"`).
- `benchmark-fixtures/hard-negatives/wave-001.json` - 2 entries: one
  near-match-with-non-official-lifecycle case
  (`near_match_reason_class: "lifecycle_state_not_official"`) and one
  near-match-with-unqualified-source case
  (`near_match_reason_class: "source_qualification_absent"`).
- `benchmark-fixtures/boundary-violations/wave-001.json` - 2 entries:
  one targeting the
  `normalized_material_must_not_be_returned_as_route` contract
  assertion and one targeting the
  `candidate_must_not_be_returned_as_executable_official` contract
  assertion. Both expect disqualification with
  `halt_classification: "contract_check_failed"` and explicitly
  describe the violation as `is_valid_output: false`,
  `is_forbidden_output: true`.

Each file carries the file-level fields named in WO-30 / DC-033
Section 3 (`_fixture_payload_marker`, `fixture_class`,
`fixture_version`, `entries`) plus four additional boolean disclaimers
at the file level (`synthetic_only`, `no_production_data`,
`no_user_data`, `not_benchmark_evidence`, `not_validation_evidence`).
The additional booleans are scaffold-internal disclaimers and do not
constitute a production schema extension; they are observation-only.

Each entry carries the entry-level properties named in WO-30 / DC-033
Section 4 (`fixture_id`, `purpose`, `non_selection_posture`, an
intent surface, plane-separation markers, a no-production/no-user-data
marker, and an entry-level version marker). Source / provenance stubs
are NOT included; the WO-30 / DC-033 prohibition continues to hold
until a future Codex packet authorizes a stub per class.

## 5. Excluded First-Wave Classes And Rationale

Three classes remain empty skeletons under WO-31 / DC-034:

- `benchmark-fixtures/latency-profiles/` - excluded because performance
  measurement is downstream of contract-safety validation per the
  WO-12R / DC-015 staged flow. Performance content before
  contract-safety content would invert the staged order.
- `benchmark-fixtures/update-profiles/` - excluded because corpus
  update semantics (lifecycle events, normalization changes) carry
  state-mutation expectations that require separate Codex scope.
- `benchmark-fixtures/adversarial/` - excluded because the failure-mode
  taxonomy is a separate Codex decision and is not bounded under
  WO-30 / DC-033 or WO-31 / DC-034.

These three subdirectories continue to contain exactly `.gitkeep`, and
the updated `test_fixture_skeleton.py` continues to enforce that
invariant. A future Codex packet may admit one or more of the excluded
classes; WO-31 does not preempt that decision.

## 6. Synthetic-Only Payload Rules

Every payload file under WO-31 / DC-034 satisfies the following rules,
which are enforced by `harness/tests/test_fixture_payloads.py`:

- The file is synthetic only; no production data, no user data, no
  production logs, no recent intent traces, no internet-derived
  examples, no customer names, no private names, no real endpoints,
  no real vendor names, no real model names, no real vector-database
  names, no real ANN backend names, no real neural re-scorer names,
  no real production-system names.
- The file carries `_fixture_payload_marker` whose value contains the
  three required substrings: `"harness-internal"`, `"synthetic"`, and
  `"not benchmark evidence"`.
- The file's `fixture_class` matches its directory name.
- The file's `entries` is a non-empty list.
- Every entry carries a synthetic-only declaration
  (`synthetic_only: true` or `no_production_user_data: true`).
- No string scalar anywhere in the file (file-level or entry-level,
  walked recursively) contains any phrase from
  `harness.review_package.FORBIDDEN_PHRASES`.
- No string scalar anywhere in the file contains any name from the
  payload-test vendor / model / index / vector-db / ANN /
  re-scorer / backend denylist (word-boundary regex match;
  case-insensitive).
- No string scalar anywhere in the file makes a positive validation,
  trust, benchmark-result, production-readiness, or
  architecture-selection claim (the
  `FORBIDDEN_CLAIM_PHRASES` tripwire list in the payload test).
- Plane-separation markers use only the five WO-21 plane names; no
  marker names the same plane in both expected and forbidden roles.
- Hard-negative entries carry
  `must_not_authorize_official_return: true` and list
  `"official_route_results"` in their `forbidden_planes`.
- Boundary-violation entries carry an `expected_disqualification`
  object with `expected_halt: true`,
  `halt_classification: "contract_check_failed"`,
  `is_valid_output: false`, `is_forbidden_output: true`, and a named
  `target_contract_assertion` string.
- Golden-intent entries that name a synthetic
  `expected_official_route_reference` explicitly disclaim
  `is_validation_evidence: false` and `is_promotion_trigger: false`.

## 7. Contamination Prevention

The first wave inherits the WO-29 / DC-032 Section 9 contamination
boundary in full. No payload entry was derived from production
feedback, recent intent traces, user data, private source material, or
unqualified internet content. Each entry was hand-authored as
synthetic content whose intent surface uses placeholder phrasing
(`"example-A scaffold task"`, `"example-B scaffold task"`) with no
real-world referent.

The existing risk RK-039 (benchmark dataset contamination by
production user feedback or recent traces) continues to apply and is
the canonical risk reference for this concern. No new RK is added under
WO-31.

The payload test's vendor / model / index / vector-db / ANN /
re-scorer / backend denylist is a tripwire to catch accidental name
inclusion; it is not a proof of absence. The denylist is documented in
the test file itself and will need updating when a future Codex packet
either expands the denylist or relaxes it for a Codex-authorized
class. WO-31 does not author the denylist as a contract.

## 8. Plane-Separation Requirements

Every entry that carries plane semantics declares its plane separation
explicitly:

- `golden-intents` entries name `expected_plane`,
  `forbidden_planes`, and (in the miss-expected entry)
  `expected_plane_must_be_empty_for_this_entry: true`.
- `hard-negatives` entries name `allowed_planes`, `forbidden_planes`,
  and `forbidden_plane_collapse: "official_route_results"`. The
  `forbidden_planes` set always includes `"official_route_results"`.
- `boundary-violations` entries name
  `violation_plane_in_observed_output` (the plane on which the
  forbidden output would appear),
  `correct_plane_for_this_content` (the plane the content would
  legitimately occupy if not violating the contract), and
  `forbidden_plane_collapse: "official_route_results"`.

The payload test enforces three plane-separation invariants:

- Every plane named in any plane-separation marker is one of the five
  WO-21 plane names.
- No entry names the same plane in both an
  `expected`/`allowed`/`correct` role and a `forbidden` role.
- Hard-negative entries always list `"official_route_results"` in
  `forbidden_planes`.

The plane-separation markers are observation only; they do not
constitute a route-returning surface and they are not propagated to any
adapter, manifest, or registered configuration observation under WO-31.

## 9. Loader-Readiness Role

The first wave exists, in part, so that a future fixture loader
authored under a separate Codex packet can be exercised against
synthetic payload content that satisfies the WO-30 / DC-033 Section 8
loader-readiness criteria:

- Every payload carries the `_fixture_payload_marker` substring rule.
- Every payload's `fixture_class` matches its directory.
- Every payload's `entries` list is present and non-empty.
- Every entry's `fixture_id` is unique within its file (assured by the
  hand-authored identifiers `<class>-wave-001-entry-A` and
  `<class>-wave-001-entry-B`).
- Every payload string is free of `FORBIDDEN_PHRASES` substrings.
- No entry carries a source / provenance / origin field.
- Every entry carries a no-production-data / no-user-data marker.
- Every entry's plane-separation markers use the WO-21 plane names
  without collapse.
- Class-specific required properties are present per WO-30 / DC-033
  Section 6 and per the per-class minimum requirements named there.

The loader itself is NOT implemented under WO-31. A future Codex
packet will implement it under its own scope.

## 10. Forbidden Scope

The WO-31 wave is forbidden from doing any of the following:

- Modifying any harness implementation module (`harness/dry_run.py`,
  `harness/artifact_snapshot.py`, `harness/manifest_loader.py`,
  `harness/mock_adapter.py`, `harness/event_log.py`,
  `harness/fixture_loader.py`, `harness/config_loader.py`,
  `harness/contract_runner.py`, `harness/reproducibility.py`,
  `harness/review_package.py`, or `harness/__init__.py`).
- Modifying any existing test module under `harness/tests/` except
  the two named in the WO-31 allowed-files list
  (`test_fixture_skeleton.py` and the new `test_fixture_payloads.py`).
- Modifying any existing fixture file under `harness/tests/fixtures/`.
- Modifying any `.gitkeep` under `benchmark-fixtures/`.
- Authoring any payload file under
  `benchmark-fixtures/latency-profiles/`,
  `benchmark-fixtures/update-profiles/`, or
  `benchmark-fixtures/adversarial/`.
- Authoring any non-JSON payload file anywhere under
  `benchmark-fixtures/`.
- Authoring a fixture loader, a production artifact schema, an
  archive format, a future filename convention beyond the three concrete
  scaffold-internal file names authored in this submission
  (`golden-intents/wave-001.json`, `hard-negatives/wave-001.json`,
  `boundary-violations/wave-001.json`), a directory layout, a retention rule, a
  storage-class rule, an immutability mechanism, an access-control
  rule, a signature scheme, or a version-pinning scheme.
- Performing benchmark execution or recording any benchmark result.
- Authoring metric thresholds, quality or performance scoring,
  ranking formulas, runtime compile internals, or validation
  framework implementations.
- Selecting any architecture, vendor, library, index family, ANN
  backend, neural re-scorer, retrieval family, ablation cell,
  multi-stage variant, or production system. The Indexing Excellence
  Gate (`00-controller-checklist.md` Section K) continues to govern
  selection.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
  All seven remain OPEN.
- Duplicating RK-039 (benchmark dataset contamination by production
  user feedback or recent traces). The contamination concern remains
  covered by the existing RK-039 reference established under WO-29 /
  DC-032 Section 9 and WO-30 / DC-033, and reinforced by the WO-31
  Section 7 contamination rules.

## 11. Not Benchmark Evidence; Not Validation Evidence; Not Production Data; Not Architecture Selection

The WO-31 payloads are scaffold-internal synthetic content authored to
exercise the WO-30 / DC-033 conceptual properties. They are explicitly:

- **Not benchmark evidence.** No payload entry constitutes a benchmark
  result, a benchmark output, a measured metric, or a measurement
  threshold. The harness does not execute against these payloads under
  WO-31; the payloads exist for future fixture-loader exercise only.
- **Not validation evidence.** No payload entry constitutes recorded
  validation evidence for any candidate or official route. Validation
  evidence is recorded by the validation framework
  (`08-validation-and-feedback.md`) and is owned by Codex; a fixture
  payload is benchmark input, not validation input.
- **Not production data.** No payload entry is drawn from production
  query logs, production retrieval logs, production error logs,
  production observability data, real user records, real customer
  transcripts, real third-party datasets, or scraped external content.
  Every payload entry is hand-authored synthetic content.
- **Not architecture selection.** No payload entry names any
  architecture, vendor, library, index family, ANN backend, neural
  re-scorer, retrieval family, ablation cell, multi-stage variant, or
  production system. The Indexing Excellence Gate
  (`00-controller-checklist.md` Section K) continues to govern
  selection. The payload test's denylist is a tripwire against
  accidental inclusion of common public vendor / model / backend
  names; it is not a proof of architecture-neutrality and is not a
  selection authority.

Future dataset expansion (additional classes, additional payload
waves, larger entry counts, real fixture content of any kind),
fixture loader implementation, benchmark execution, run artifact
retention or storage policy, production artifact contract, and
architecture selection each require a separate future Codex packet.
WO-31 / DC-034 does not authorize any of those.
