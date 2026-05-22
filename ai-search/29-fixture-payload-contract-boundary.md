# ai-search - Benchmark Fixture Payload Contract Boundary

Document type: Phase 4 / Phase 9 / Benchmark fixture payload contract boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-29

---

## 1. Purpose

This document records the documentation-level contract boundary for
future benchmark fixture payloads that will eventually populate the
empty fixture skeleton recorded under WO-20 / DC-023 at
`benchmark-fixtures/`. WO-29 defines what future payloads must and must
not represent before any real fixture content is authored. It does not
author payload content, does not author a payload schema, does not
admit a payload into the harness, and does not authorize benchmark
execution against any payload.

WO-29 is documentation-level only. It does not modify any file under
`harness/`. It does not modify any file under `benchmark-fixtures/`. It
does not create any fixture payload files. It does not modify the
existing scaffold-internal toy fixtures under `harness/tests/fixtures/`.
It does not select any retrieval architecture, vendor, library, index
family, ANN backend, reranker, retrieval family, ablation cell,
multi-stage variant, or production system.

The boundary exists so that any future Codex packet that authors fixture
payload content does so against a recorded, audit-visible contract for
what those payloads may and may not be. The boundary is preventive: it
records constraints before payload-authoring tempo begins, so payload
work cannot drift into dataset contamination, production-data leakage,
implicit architecture selection, or unrecorded artifact-contract growth.

## 2. Fixture Payload Classes

Six payload classes are named in the WO-20 fixture skeleton at
`benchmark-fixtures/` and in `13-retrieval-benchmark-framework.md`
Section 3. Each class is described at boundary level only; no payload
examples, sample structures, or JSON shapes are authored here.

- **Golden intent fixtures** (`benchmark-fixtures/golden-intents/`):
  the canonical evaluation set of intents paired with the official route
  that the harness expects (where one exists) or with an explicit miss
  classification (where none does). Future payloads in this class must
  carry an unambiguous identifier per intent, a non-ambiguous expected
  outcome at boundary level, and an explicit absence marker where the
  expected outcome is a known miss.
- **Hard negative fixtures** (`benchmark-fixtures/hard-negatives/`):
  intents paired with near-miss content that retrieval must not return
  as official. Future payloads in this class must explicitly mark the
  near-miss content as a forbidden official-return and must record the
  reason class (lifecycle state, policy gate disposition, source
  qualification absence, or other Codex-defined reason).
- **Boundary violation fixtures**
  (`benchmark-fixtures/boundary-violations/`): intents and corpus
  configurations specifically constructed to trigger contract violation
  paths recorded in `13-retrieval-benchmark-framework.md` Section 8 and
  in `21-retrieval-adapter-contract.md` Section 7. Future payloads in
  this class must record which contract assertion they target and must
  carry an explicit forbidden-plane-collapse marker that the harness
  can verify against.
- **Latency profile fixtures** (`benchmark-fixtures/latency-profiles/`):
  intents representative of expected production query distribution for
  latency and throughput measurement. Future payloads in this class
  must carry distribution metadata at boundary level only (not raw
  production traces). The profile is a measurement input, not a
  validation input.
- **Update profile fixtures** (`benchmark-fixtures/update-profiles/`):
  corpus update events (new sources qualified, routes promoted,
  routes demoted / revoked / retired, normalization changes)
  representative of expected production update rates. Future payloads
  in this class must record the lifecycle event class and the expected
  harness halt or admit behavior, with no implicit lifecycle mutation
  outside the registry's recorded events.
- **Adversarial fixtures** (`benchmark-fixtures/adversarial/`): intents
  crafted to expose known retrieval failure modes (vocabulary
  mismatch, paraphrase, abstraction, rare entities, ambiguous
  intents). Future payloads in this class must carry an explicit
  failure-mode tag at boundary level and an explicit expected
  observation (miss class, candidate-only outcome, halt, or other
  Codex-defined outcome).

Each class is named here to bound future authoring. The substantive
content of any class is owned by Codex and is not authored under WO-29.

## 3. Fixture Payload Non-Goals

Future fixture payloads are explicitly not:

- Production data. Real production query logs, real production user
  records, real production route registries, and real production source
  graphs are forbidden as payload content unless an explicit future
  Codex authorization admits a specific class with explicit handling.
- User data, real or simulated. Personally identifying information,
  account identifiers, session identifiers, and any user-attributable
  content are forbidden as payload content.
- Route validation evidence. Validation evidence is recorded by the
  validation framework (`08-validation-and-feedback.md`); a fixture
  payload is benchmark input, not validation evidence for any
  candidate or official route.
- Source qualification evidence. Source qualification is recorded by
  the source quality graph (`09-source-quality-graph.md`); a fixture
  payload is benchmark input, not qualification evidence for any
  source.
- Architecture selection evidence by itself. Aggregate benchmark
  performance against fixture payloads is one input to the Indexing
  Excellence Gate (`00-controller-checklist.md` Section K), not
  selection authority. A payload's own existence and the harness's
  measurement of it never select an architecture, vendor, library,
  index family, ANN backend, reranker, retrieval family, ablation
  cell, or multi-stage variant.
- Ranking formula input by itself. Fixture payloads do not author
  ranking formulas, weights, or scoring inputs. Ranking formula
  authorship is a separate Codex decision.
- Runtime compile input. Fixture payloads do not author runtime
  compile inputs. Runtime compile internals are a separate Codex
  decision.

## 4. Minimum Future Payload Properties

A future fixture payload, when its class authors content, must carry
the following conceptual properties at boundary level. The set is
intentionally property-level, not field-level: WO-29 does not author
field names, field types, JSON shapes, or any production schema.

- **Fixture class identity.** Every payload entry records which of the
  six classes it belongs to. Class identity is non-ambiguous; an entry
  belongs to exactly one class.
- **Stable fixture identifier.** Every payload entry carries an
  identifier that is stable across runs and across regenerations. The
  identifier is not reused for a different entry under any future
  revision.
- **Intent / query surface (where applicable).** Classes that pair an
  intent with an expected outcome (golden intent, hard negative,
  boundary violation, adversarial) carry an intent surface at boundary
  level. The intent surface is a Codex-authorized form; WO-29 does not
  author the form.
- **Expected plane boundary (where applicable).** Classes whose entries
  imply expected harness output on one of the five planes named in
  `21-retrieval-adapter-contract.md` Section 3 carry an explicit
  expected-plane marker. The plane boundary identifies which plane is
  expected to contain (or to remain empty of) the entry's expected
  result, never collapsed across planes.
- **Forbidden plane collapse marker (where applicable).** Classes
  whose entries target a contract violation path
  (`21-retrieval-adapter-contract.md` Section 4) carry an explicit
  forbidden-collapse marker that the harness can verify against
  without the marker itself becoming a route-returning surface.
- **Expected halt or disqualification condition (where applicable).**
  Classes whose entries should cause the harness to halt or to
  disqualify a configuration (per `13-retrieval-benchmark-framework.md`
  Section 8 and `15-retrieval-experiment-design.md` Section 12) carry
  an explicit expected-halt or expected-disqualification marker.
- **Provenance / source stub (only if a future Codex packet
  authorizes).** Payloads do not carry provenance or source fields by
  default. A future Codex packet may authorize a stub for a specific
  class; until then no provenance or source fields are admitted.
- **Expected non-selection posture.** Every payload entry carries an
  explicit marker that its admission does not constitute selection of
  any retrieval architecture, vendor, library, index family, ANN
  backend, reranker, retrieval family, ablation cell, multi-stage
  variant, or production system.
- **Fixture version or revision marker.** Every payload entry carries
  a version or revision marker so the harness can record exactly
  which payload revision a run consumed. Pre-Run Preparation Boundary
  A of `14-benchmark-execution-plan.md` requires versioned, content-
  hashed, provenance-recorded fixtures; the version marker named here
  is one of the property-level inputs to that requirement.
- **Fixture purpose note.** Every payload entry carries a free-text
  purpose note recording why the entry exists and what class invariant
  it exercises. The note is human review material, not a substitute
  for the structured markers above.

These properties are conceptual only. WO-29 does not author field
names, field types, JSON shapes, file formats, encoding rules, naming
conventions, ordering rules, or any production schema substance. A
future Codex packet that authors payload content may choose to satisfy
each property through any concrete mechanism it authorizes; the WO-29
boundary states only that the property must be satisfied somehow at
the entry level.

## 5. Explicit Schema Non-Authorization

WO-29 explicitly does not author:

- A JSON schema, XML schema, protobuf schema, or any structured
  validation schema.
- A field type registry, type system, or interface contract.
- A file naming convention, file extension convention, directory
  layout, sharding scheme, or archive format.
- A production artifact contract. Production artifact contracts
  remain owned by Codex and are tracked under OQ-076 (which remains
  OPEN). The WO-29 contract boundary is not a substitute for, and
  does not preempt, that decision.
- A benchmark dataset content. WO-29 records constraints on future
  payloads but adds none.

A future Codex packet that adds payload content will choose its own
substantive form against the property-level constraints in Section 4
and the prohibitions throughout this document. The choice of form is
a separate Codex decision and is not implied by use of any WO-29
language.

## 6. Relationship To Existing Fixture Skeleton

The empty fixture skeleton authorized under WO-20 / DC-023 at
`benchmark-fixtures/` is unchanged by WO-29:

- `benchmark-fixtures/README.md` is unchanged.
- The six category subdirectories
  (`benchmark-fixtures/golden-intents/`,
  `benchmark-fixtures/hard-negatives/`,
  `benchmark-fixtures/boundary-violations/`,
  `benchmark-fixtures/latency-profiles/`,
  `benchmark-fixtures/update-profiles/`,
  `benchmark-fixtures/adversarial/`) remain present.
- Each subdirectory still contains exactly one `.gitkeep` placeholder
  file and no other content.
- The `harness/tests/test_fixture_skeleton.py` test continues to
  enforce the empty-skeleton invariant on every test run.

WO-29 adds no payload files. WO-29 modifies no `.gitkeep` placeholder.
WO-29 modifies no `README.md`. The skeleton's empty-by-design status
recorded under WO-20 / DC-023 Section 3 continues to hold.

## 7. Relationship To Toy Harness Fixtures

The existing scaffold-internal toy fixtures under
`harness/tests/fixtures/` (`toy_scaffold_fixture.json`,
`toy_scaffold_config.json`, `toy_retrieval_manifest.json`) are
scaffold-internal only:

- They are harness-internal test fixtures and not benchmark datasets.
- They carry scaffold-internal markers (e.g., `_fixture_marker`,
  `_manifest_marker`) that identify them as toy data.
- They are consumed only by harness unit tests under `harness/tests/`
  and by the dry-run path at `harness/dry_run.py` when the scaffold's
  own tests invoke it.
- They are not templates for production fixture payloads. A future
  Codex packet that authors payload content may or may not draw
  inspiration from these toy fixtures; it does not inherit their form
  as a contract.

WO-29 modifies none of the existing toy fixtures and does not promote
any of their fields, markers, or shapes into a future production
payload schema.

## 8. Payload Admission Boundary

Future payload admission is bounded as follows:

- Authoring of any payload class content requires a separate
  Codex-authored Work Order whose scope, allowed files, required
  content, forbidden scope, acceptance criteria, and evidence
  requirements are explicit at issue time. WO-29 does not authorize
  any such authoring.
- Every payload entry must be reviewed by Codex before harness
  admission. Admission is not implicit by file placement under
  `benchmark-fixtures/`; it is a Codex-recorded event under a future
  packet.
- Payload admission does not equal benchmark execution. Benchmark
  execution is governed by `14-benchmark-execution-plan.md` Pre-Run
  Preparation Boundaries A and B and by the staged in-run flow. A
  payload that has been admitted into the fixture set is still subject
  to those boundaries before any run consumes it.
- Payload admission does not equal architecture selection. The
  Indexing Excellence Gate (`00-controller-checklist.md` Section K)
  continues to govern selection. A payload's existence in
  `benchmark-fixtures/` confers no selection authority and no
  vendor / library / index family / ANN backend / reranker /
  retrieval family / ablation cell / multi-stage variant /
  architecture choice.

## 9. Contamination And Leakage Boundary

Fixture payloads must not silently come from any of the following
sources:

- Production user feedback or any aggregate derived from production
  user feedback.
- Recent intent traces from the intent trace store
  (`04-intent-trace-store.md`); the golden intent set isolation
  requirement in `13-retrieval-benchmark-framework.md` Section 4
  applies.
- Real user data, real user account identifiers, real session
  identifiers, or any user-attributable content.
- Private source material that has not passed the source qualification
  gate (`09-source-quality-graph.md`).
- Unqualified internet or public content. Public source material may
  contribute candidate-derivation input only after explicit
  qualification and normalization; it may never enter fixture payloads
  as an answer or as a route.

Any payload source that falls under one of the categories above
requires explicit Codex authorization. The authorization records the
source, the qualification path, the isolation guarantee against the
golden intent set, and the audit visibility of the admission.

Dataset contamination remains an active risk class. The existing risk
RK-039 (benchmark dataset contamination by production user feedback or
recent traces) continues to apply and is the canonical reference for
this risk. WO-29 does not add a new risk entry; the contamination
concern named here is covered by RK-039 and reinforced by the explicit
prohibitions in this section.

## 10. Forbidden Scope

The WO-29 protocol is forbidden from doing any of the following:

- Authoring any payload example, sample entry, sample JSON, sample
  query, sample intent, sample route, sample miss classification,
  sample halt event, or sample expected outcome.
- Authoring any schema, field type registry, type system, interface
  contract, file naming convention, directory layout, sharding scheme,
  or archive format.
- Creating, modifying, renaming, or deleting any file under
  `benchmark-fixtures/`.
- Creating, modifying, renaming, or deleting any file under
  `harness/`.
- Creating, modifying, renaming, or deleting any test, fixture, or
  module other than the three files allowed under WO-29.
- Performing benchmark execution or recording any benchmark result.
- Authoring metric thresholds, quality / performance scoring, ranking
  formulas, runtime compile internals, or validation framework
  implementations.
- Authoring selection criteria of any kind. The Indexing Excellence
  Gate (`00-controller-checklist.md` Section K) continues to govern
  selection.
- Authoring a real retrieval, indexing, or ranking implementation, or
  contacting any retrieval system.
- Selecting any vendor, library, index family, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, or
  architecture.
- Closing OQ-035 (golden intent set construction), OQ-049 (broader
  dataset suite ownership), OQ-056 (run artifact retention / storage
  policy), OQ-057 (configuration registration authority), OQ-070
  (broader scope), OQ-075 (dependency policy beyond the first
  scaffold), or OQ-076 (production artifact contracts). All seven
  remain OPEN.

## 11. Out Of Scope

This document is documentation-level only. It does not:

- Author fixture construction methodology (e.g., how golden intents are
  collected, how hard negatives are derived, how boundary violations
  are constructed, how latency profiles are sampled, how update
  profiles are recorded, how adversarial cases are generated).
- Author dataset ownership (who is responsible for each class's
  content and review).
- Author refresh cadence (how often a class is regenerated or
  amended, and under what trigger).
- Author retention or storage policy for fixture payloads or for run
  artifacts derived from them. Run artifact retention / storage
  policy remains owned by Codex under OQ-056 (which remains OPEN).
- Author production artifact contracts. OQ-076 remains OPEN.
- Author or perform real benchmark execution. The full execution flow
  remains governed by `14-benchmark-execution-plan.md`.
- Author or select any retrieval architecture, vendor, library, index
  family, ANN backend, reranker, retrieval family, ablation cell,
  multi-stage variant, or production system.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.
