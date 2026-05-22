# ai-search - Scaffold Fixture Payload Format Boundary

Document type: Phase 4 / Phase 9 / Scaffold fixture payload format boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-30

---

## 1. Purpose

This document records the scaffold-internal fixture payload format
boundary for the first wave of synthetic benchmark fixture payloads
that may be authored under a future WO-31 packet. WO-30 names a
minimal scaffold JSON shape (file-level and entry-level) that those
future payloads will conform to, and a checklist that the payload
authoring packet (WO-31) and a future fixture loader will use to
admit them.

WO-30 is the final contract step before payload authoring. It does not
create any payload file, does not author any schema language, does not
implement any fixture loader, does not perform benchmark execution, and
does not select any retrieval architecture, vendor, library, index
family, ANN backend, reranker, retrieval family, ablation cell,
multi-stage variant, or production system.

WO-30 is documentation-level only. It does not modify any file under
`harness/`. It does not modify any file under `benchmark-fixtures/`. It
does not modify the existing scaffold-internal toy fixtures under
`harness/tests/fixtures/`. It does not create any payload files.

## 2. Format Status

The format named in this document is scaffold-internal only:

- It is not a production artifact contract. Production artifact
  contracts remain owned by Codex and are tracked under OQ-076 (which
  remains OPEN). WO-30 does not close OQ-076 and does not preempt the
  future Codex decision that will author production artifact
  contracts.
- It is not the final schema. WO-30 records conceptual properties at
  boundary level only. No JSON schema syntax, field type registry,
  ordering rule, or naming convention is authored. Future Codex
  packets may revise the format at any time; the boundary recorded
  here is the starting shape for the first synthetic payload wave
  only.
- It is not OQ-076 closure. The decision that authors the production
  artifact contract is a separate Codex Work Order whose scope,
  allowed files, required content, forbidden scope, acceptance
  criteria, and evidence requirements are explicit at issue time.
- It is not run artifact retention or storage policy authorship.
  OQ-056 (run artifact retention/storage policy) remains OPEN.

Future Codex packets may revise the file-level shape and the
entry-level shape recorded in Sections 3 and 4 at any time. WO-30 does
not bind any future Codex decision.

## 3. File-Level Shape

A future synthetic benchmark fixture payload file conforms to a JSON
object whose top-level keys are constrained to the following
conceptual fields. WO-30 does not author concrete sample JSON values,
field types, or schema syntax; the field names are conceptual contract
markers only.

- `_fixture_payload_marker`. A harness-internal marker string proving
  the file is scaffold-internal synthetic content. The marker carries
  the same boundary role as the existing `_fixture_marker` and
  `_manifest_marker` keys on the scaffold-internal toy fixtures under
  `harness/tests/fixtures/`. Concrete marker content is owned by the
  future WO-31 packet; the WO-24 / DC-027 precedent (marker must be a
  string carrying a harness-internal substring) is the precedent for
  any future loader's validation rule.
- `fixture_class`. Identifies which of the WO-20 / WO-29 payload
  classes the file populates. Only the classes admitted under WO-30
  Section 5 are valid values for the first wave; future Codex packets
  may admit additional classes.
- `fixture_version`. A version or revision marker for the file as a
  whole. Pre-Run Preparation Boundary A of
  `14-benchmark-execution-plan.md` requires versioned, content-hashed,
  provenance-recorded fixtures before any benchmark run; the
  file-level version marker named here is one of the property-level
  inputs to that requirement. Concrete version content is owned by
  the future WO-31 packet.
- `entries`. A list of entry-level records (Section 4). The list is
  the only content-bearing top-level field. Empty lists are not
  forbidden at the format level; admission rules for empty payload
  files are a future Codex decision.

No other top-level field is admitted at the format boundary level. A
future WO-31 packet that needs an additional top-level field must
either add it to this document via amendment or scope the addition
inside its own packet.

## 4. Entry-Level Shape

Each entry under `entries` is a JSON object whose conceptual
properties are constrained as follows. WO-30 does not author concrete
sample entries, field types, ordering rules, or schema syntax.

- `fixture_id`. A stable identifier for the entry. Identifiers are
  unique within the file (a future loader will verify uniqueness per
  Section 8). Identifiers are stable across runs and across
  regenerations; an identifier is never reused for a different entry
  under any future revision.
- `purpose`. A free-text human-readable note recording why the entry
  exists and what class invariant it exercises. The note is human
  review material, not a substitute for the structured markers below.
- `non_selection_posture`. An explicit marker recording that the
  entry's admission does not constitute selection of any retrieval
  architecture, vendor, library, index family, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, or production
  system.
- Class-specific intent / query surface (where applicable). Classes
  whose entries pair an intent with an expected outcome
  (golden-intents, hard-negatives, boundary-violations under WO-30
  Section 5) carry an intent surface at boundary level. The intent
  surface is a Codex-authorized form; WO-30 does not author the form.
- Expected plane boundary (where applicable). Classes whose entries
  imply expected harness output on one of the five planes named in
  `21-retrieval-adapter-contract.md` Section 3 carry an explicit
  expected-plane marker. The plane boundary identifies which plane is
  expected to contain (or to remain empty of) the entry's expected
  result, never collapsed across planes.
- Expected halt / disqualification (where applicable). Classes whose
  entries should cause the harness to halt or to disqualify a
  configuration carry an explicit expected-halt or
  expected-disqualification marker. Per
  `13-retrieval-benchmark-framework.md` Section 8 and
  `15-retrieval-experiment-design.md` Section 12, contract-safety
  violations disqualify regardless of any other measurement.
- Forbidden plane collapse marker (where applicable). Classes whose
  entries target a contract violation path
  (`21-retrieval-adapter-contract.md` Section 4) carry an explicit
  forbidden-collapse marker that the harness can verify against
  without the marker itself becoming a route-returning surface.
- Source / provenance stub - prohibited unless a future Codex packet
  explicitly authorizes. By default no entry carries any source or
  provenance field. WO-30 does not authorize any class to carry such
  a field; a future Codex packet that admits a stub for a specific
  class will scope that admission inside its own packet.
- No-production / no-user-data marker. An explicit marker recording
  that the entry carries no production data, no user data (real or
  simulated), no production logs, no recent traces, and no
  unqualified internet content. The marker is a positive assertion
  that the authoring process is constrained per WO-29 Section 3 and
  WO-30 Section 7.
- Version / revision marker. An entry-level version or revision
  marker so the harness can record exactly which entry revision a run
  consumed. The entry marker is independent of the file-level
  `fixture_version` field; both are required.

These properties are conceptual only. WO-30 does not author field
names, field types, JSON shapes, file formats, encoding rules, naming
conventions, ordering rules, or any production schema substance.
Concrete realization of each property is owned by the future WO-31
packet, subject to the loader-readiness criteria in Section 8.

## 5. Allowed Fixture Classes For First Payload Wave

The first synthetic payload wave admits only three of the six WO-20
classes:

- `golden-intents`
- `hard-negatives`
- `boundary-violations`

The three remaining classes - `latency-profiles`, `update-profiles`,
and `adversarial` - are explicitly excluded from the first wave under
WO-30, unless a future Codex packet overrides the exclusion at issue
time.

Rationale: the first wave's only role is to validate contract safety
and plane separation through the existing harness path (loader -
manifest - adapter - registered observation - mock adapter - contract
checks - review package - artifact snapshot). The three included
classes target exactly that role:

- `golden-intents` exercise the expected official-or-miss outcome
  boundary on the official and candidate planes.
- `hard-negatives` exercise the contract assertion that near-match
  content must not be returned as official, on the candidate plane
  and on the source-quality-constraint plane.
- `boundary-violations` exercise the contract violation surface
  recorded in `13-retrieval-benchmark-framework.md` Section 8 and
  `21-retrieval-adapter-contract.md` Section 7 directly.

The three excluded classes carry additional complexity that is not
required by the first-wave goal:

- `latency-profiles` add performance / throughput measurement
  semantics. Performance measurement is governed by
  `13-retrieval-benchmark-framework.md` Section 9 and is downstream
  of contract-safety validation per `14-benchmark-execution-plan.md`
  staged flow; performance content before contract-safety content
  would invert the staged order.
- `update-profiles` add corpus update semantics (lifecycle events,
  normalization changes) whose state-mutation expectations require
  separate Codex scope.
- `adversarial` adds failure-mode tagging whose taxonomy is a Codex
  decision and is not bounded under WO-30.

A future Codex packet may admit one or more of the excluded classes
under its own scope. WO-30 does not preempt that decision; it bounds
only the first wave.

## 6. Per-Class Minimum Requirements

At boundary level, each first-wave class carries the following
minimum requirements. WO-30 does not author concrete entries; the
requirements are property-level only and are realized by the future
WO-31 packet.

- `golden-intents`. Each entry records an expected
  official-or-miss outcome boundary at boundary level. The outcome
  is one of: official-route-expected (with an explicit
  expected-plane marker for the `official_route_results` plane), or
  miss-expected (with an explicit miss classification). The entry is
  not route validation evidence; the validation framework records
  route validation evidence per `08-validation-and-feedback.md` and a
  fixture entry is benchmark input, not validation input.
- `hard-negatives`. Each entry records that a specific near-match
  content must not be returned as official. The expected harness
  behavior is that the near-match appears (if at all) only on the
  candidate or normalized-material-support plane, never on the
  official plane. The entry's expected-plane marker explicitly
  excludes the `official_route_results` plane.
- `boundary-violations`. Each entry records which contract assertion
  it targets (drawn from `13-retrieval-benchmark-framework.md`
  Section 8 and `21-retrieval-adapter-contract.md` Section 7) and
  the expected harness halt or disqualification boundary. Per DC-020,
  any contract assertion failure disqualifies the configuration; the
  entry's expected-disqualification marker carries that expectation.

No concrete entries are authored under WO-30. A future Codex packet
that authors entries will record them inside its own packet and
satisfy each property above.

## 7. Payload Authoring Checklist For WO-31

The future WO-31 packet that authors synthetic payload content will
verify the following checklist at issue time:

- All payload entries are synthetic only. No item is drawn from any
  real query log, production trace, user feedback, customer
  transcript, third-party dataset, or scraped external content.
- No user data is present. No personally identifying information, no
  account identifier, no session identifier, and no
  user-attributable content is admitted.
- No production logs are present. No production query log, no
  production retrieval log, no production error log, and no
  production observability data is admitted.
- No recent traces are present. The intent trace store
  (`04-intent-trace-store.md`) is not a payload source. The
  isolation guarantee against the golden intent set named in
  `13-retrieval-benchmark-framework.md` Section 4 continues to hold.
- No unqualified internet content is present. Public source material
  may contribute candidate-derivation input only after explicit
  qualification and normalization per
  `09-source-quality-graph.md`; it may never enter a fixture payload
  as an answer or as a route.
- No architecture, vendor, library, ANN backend, reranker, retrieval
  family, ablation cell, multi-stage variant, or production-system
  name appears in any payload string. No commercial product name, no
  embedding model name, no vector-database name, no reranker model
  name, no LLM provider name, and no specific open-source retrieval
  project name is admitted.
- No ranking or selection language appears in any payload string.
  The `harness.review_package.FORBIDDEN_PHRASES` constant is the
  canonical list; payload strings authoring is held to the same
  standard.
- No prompt / skill / agent terminology appears. The product is the
  route per DC-001; payloads do not introduce competing user-facing
  vocabulary.
- Each entry carries class identity and a stable, file-unique
  identifier.
- Each entry carries an explicit non-selection posture marker.
- Each payload file remains scaffold-internal: the
  `_fixture_payload_marker` carries a harness-internal substring and
  the file is not treated as a production artifact by use.

The checklist is the WO-31 authoring contract. WO-30 records it
without admitting any payload content.

## 8. Loader Readiness Criteria

A future fixture loader that admits payload files into the harness
must verify, at minimum, the following before admitting a file. WO-30
does not implement the loader; the criteria are stated at boundary
level only and are precedent for any future Codex packet that
implements one.

- The `_fixture_payload_marker` key is present and carries the
  harness-internal substring required by the future loader's
  validation rule (precedent: WO-24 / DC-027 marker rule).
- The `fixture_class` value is one of the classes admitted under
  WO-30 Section 5 (or extended by a future Codex packet). Unknown
  classes are rejected.
- The `entries` list is present and is a JSON array.
- Every entry's `fixture_id` is unique within the file. Duplicate
  identifiers are rejected; the loader records an explicit halt
  event before raising.
- No string scalar anywhere in the payload (file-level or entry-level)
  contains any phrase from `harness.review_package.FORBIDDEN_PHRASES`.
  Hits are rejected; the loader records an explicit halt event
  before raising. (Precedent: WO-24 / DC-027 manifest loader and
  WO-27 / DC-030 snapshot writer.)
- No entry carries a source / provenance / origin field unless a
  future Codex packet has explicitly authorized one for the
  entry's class. Until that packet exists, presence of any such
  field is rejected.
- No entry carries a production-data marker, a user-data marker, a
  recent-trace marker, or an unqualified-internet-content marker
  set to a truthy value. The positive no-production / no-user-data
  marker is required; the negative-presence assertion is verified.
- No string scalar anywhere in the payload contains any architecture,
  vendor, library, ANN backend, reranker, retrieval family,
  ablation cell, multi-stage variant, or production-system name. A
  future Codex packet will author the loader's denylist; until then
  the loader treats any such hit as a rejection class.
- Expected plane boundary markers do not collapse planes. An entry
  whose expected-plane marker names more than one plane in a manner
  that conflates the five WO-21 planes is rejected.
- Class-specific required conceptual properties (Section 6) are
  present. An entry missing its class's required property is
  rejected.

The loader records a success event on admission and an explicit halt
event before raising on every rejection path. The event naming and
field set are owned by the future Codex packet that implements the
loader; WO-30 does not author them.

## 9. Relationship To WO-29

WO-29 / DC-032 (`29-fixture-payload-contract-boundary.md`) authored
the documentation-level contract boundary for what future benchmark
fixture payloads must and must not represent: payload classes (six),
payload non-goals (seven), minimum conceptual properties (ten),
explicit schema non-authorization, relationship to the existing
fixture skeleton, relationship to existing toy harness fixtures,
payload admission boundary, contamination / leakage boundary
referencing RK-039, forbidden scope, and out-of-scope.

WO-30 records the scaffold-internal JSON format boundary for the
first synthetic payload wave. It sits inside the WO-29 boundary and
adds three things WO-29 did not author:

- A file-level shape with four conceptual top-level fields
  (Section 3).
- An entry-level shape with the ten WO-29 properties realized at
  conceptual property level (Section 4), plus a first-wave class
  restriction (Section 5) and per-class minimum requirements
  (Section 6).
- A payload authoring checklist for the future WO-31 packet
  (Section 7) and loader readiness criteria for any future loader
  (Section 8).

WO-30 does not supersede WO-29. Every WO-29 prohibition continues
to apply. Where the two documents speak to the same property, the
WO-30 entry-level shape is the realization of the WO-29 conceptual
property at the format-boundary level. A conflict between the two
documents is resolved by Codex.

## 10. Relationship To OQs

WO-30 does not close any open question. Each non-closure is recorded
below.

- OQ-035 (golden intent set construction). Remains OPEN. WO-30
  bounds the file-level and entry-level shape that a future
  golden-intents payload will use; it does not author the
  construction methodology, the intent collection process, the
  ownership, or the refresh cadence. OQ-035 is the canonical
  question for those decisions and is not preempted.
- OQ-049 (broader dataset suite ownership). Remains OPEN. WO-30
  bounds the first synthetic payload wave but does not author
  dataset suite ownership across all six classes; OQ-049 continues
  to be the canonical question.
- OQ-056 (run artifact retention / storage policy). Remains OPEN.
  WO-30 does not author retention or storage policy for any payload
  file, any snapshot artifact, or any other run artifact. OQ-056 is
  not preempted.
- OQ-057 (configuration registration authority). Remains OPEN.
  WO-30 does not author payload registration authority or admission
  authority; the payload admission boundary in WO-29 Section 8 and
  the WO-30 loader-readiness criteria are technical preconditions,
  not authority decisions.
- OQ-070 (broader scope per WO-20 carry-forward note). Remains
  OPEN. WO-30 does not author broader scope across the carry-forward
  note's questions.
- OQ-075 (dependency policy beyond the first scaffold). Remains
  OPEN. WO-30 authors no dependency. The future fixture loader and
  the future WO-31 payload authoring remain Python-stdlib-only by
  precedent (WO-17 / DC-020) unless a separate Codex packet alters
  the dependency policy.
- OQ-076 (production artifact contracts). Remains OPEN. The WO-30
  format is scaffold-internal only; it is not a production artifact
  contract. OQ-076 is the canonical question for production
  artifact contract authorship and is not preempted.

## 11. Forbidden Scope

The WO-30 boundary is forbidden from doing any of the following:

- Creating any payload file under `benchmark-fixtures/` or anywhere
  else.
- Authoring any sample JSON, sample entry, sample query, sample
  intent, sample route, sample miss classification, sample halt
  event, or sample expected outcome.
- Authoring any schema language, schema syntax, field type
  registry, type system, interface contract, file naming
  convention, directory layout, sharding scheme, or archive format.
- Creating, modifying, renaming, or deleting any file under
  `harness/`.
- Modifying any file under `benchmark-fixtures/`.
- Modifying any existing toy fixture under `harness/tests/fixtures/`.
- Performing benchmark execution or recording any benchmark result.
- Selecting any vendor, library, index family, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, or
  architecture.
- Authoring metric thresholds, quality / performance scoring,
  ranking formulas, runtime compile internals, or validation
  framework implementations.
- Authoring a production artifact contract.
- Closing OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, or
  OQ-076. All seven remain OPEN.
- Duplicating RK-039 (benchmark dataset contamination by production
  user feedback or recent traces). The contamination concern is
  covered by the existing RK-039 reference in WO-29 Section 9 and
  reinforced by the WO-30 Section 7 checklist; no new RK is added
  under WO-30.

## 12. Out Of Scope

This document is documentation-level only. It does not:

- Author actual payload content. Payload authoring is the future
  WO-31 packet's responsibility (subject to the checklist in
  Section 7).
- Implement a fixture loader. Loader implementation is a separate
  future Codex packet's responsibility (subject to the readiness
  criteria in Section 8).
- Author or perform real benchmark execution. The full execution
  flow remains governed by `14-benchmark-execution-plan.md`.
- Author dataset ownership or refresh cadence.
- Author retention or storage policy for fixture payloads or for
  run artifacts derived from them.
- Author production artifact contracts.
- Author retrieval candidate adapters. Adapter authoring is bounded
  by `21-retrieval-adapter-contract.md` and the scaffold-internal
  mock adapter at `harness/mock_adapter.py`; no real adapter is
  authored under WO-30.

All such work requires a future Codex-approved Work Order whose
scope, allowed files, required content, forbidden scope, acceptance
criteria, and evidence requirements are explicit at issue time.
