# ai-search - Scaffold System Map (Review Aid)

Document type: Compiled reference / review aid
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Purpose: Provide a compact dependency graph and vocabulary map over
the scaffold modules under `harness/` from WO-50 through WO-62, so
reviewers can orient quickly and catch naming collisions before they
land in code.

## Authority

This file is a review aid. It is NOT a project-authority document.
The canonical authority for scaffold scope, allowed inputs, allowed
outputs, halt conditions, and selection / measurement state is the
controlling project documentation set:

- `ai-search/00-controller-checklist.md`
- `ai-search/00-open-questions.md`
- the originating Work Order boundary document for each scaffold
  (`ai-search/50-...md` through `ai-search/62-...md`)
- `ai-search/00-claude-task-ledger.md`

If this map ever conflicts with the canonical documents above, the
canonical documents win and this map must be corrected to match.

`ai-search/00-wo-constraints.md` is a compiled standing-constraints
reference used alongside this map. It is also descriptive and is not
a project-authority document.

This map is descriptive. It does NOT authorize new scaffold
composition, new module invocations, new public functions, new
admission surfaces, new architecture / vendor / library / index
family / ANN backend / retrieval family / production system choices,
or any flip of an authorization / readiness / selection boolean.

## Roadmap Source

- Forward plan / roadmap authority is `ai-search/00-controller-checklist.md`.
- This system map is descriptive only.
- This system map cannot authorize next work.
- If `00-controller-checklist.md` and this system map differ, `00-controller-checklist.md` wins.
- The system map may summarize already-approved scaffold adjacency, but it must not propose, select, or approve future work.

## 1. Scaffold Dependency Graph

The graph below covers WO-50 through WO-62. Edges are labeled by
what flows between scaffolds (the observation dict shape, not raw
content). All scaffolds operate on already-loaded in-memory data;
no node performs file IO, network IO, or subprocess execution.

```
   STANDALONE PROBES AND GUARDS
   ============================
   WO-50  scaffold_route_query_probe
   WO-51  scaffold_route_query_ambiguity_probe
   WO-52  scaffold_conflicting_evidence_guard
   WO-53  scaffold_conflicting_evidence_guard  (coverage extension
                                                of WO-52 module,
                                                authorized in place
                                                by WO-53 packet)
   WO-58  scaffold_route_invariant_diagnostic_reporter
                                       (consumes scaffold observations;
                                        emits diagnostic_report)

   SOURCE-INTAKE CHAIN (in-memory only)
   ====================================
                  (input)
                    |
                    v
   source           +-------- WO-55 -------+
   reference -----> |  register            |--- register_observation -+
   records          +----------------------+                          |
                                                                      v
                                                              +-- WO-56 ---+
                          source records (in-memory) -------> |  bridge    |
                                                              +------------+
                                                                      |
                                                                      | linked_source_observation
                                                                      v
   input_prompt   ------------------------------------------>  +-- WO-54 --+
                                                               |  trace    |
                                                               +-----------+
                                                                      |
                                                                      | trace_observation
                                                                      v
                                                       +--- WO-57 composer ---+
                                                       |  smoke_package       |
                                                       +----------------------+
                                                                      |
                                                                      | package_observation
                                                                      v
                                                       +--- WO-59 composer ---+
                                                       |  visible_report      |
                                                       +----------------------+
                                                            ^                |
                                                            |                |
                                              diagnostic_report     visible_report_observation
                                                            |
                                                       +--- WO-58 ---+
                                                       |  reporter   |
                                                       +-------------+

   EXTERNAL-SOURCE ACQUISITION CHAIN (in-memory only)
   ==================================================
   acquisition
   requests       +--- WO-60 ---+
   ------------>  |  acquisition |--- acquisition_reference (no fetch)
                  |  boundary    |
                  +--------------+

   url
   request
   + injected
   fetcher        +--- WO-61 ---+
   ------------>  |  url         |--- url_acquisition_observation
                  |  executor    |    (length + 12-char prefix only;
                  |              |     no raw origin, no full hash)
                  +--------------+
                          |
                          v
                  +--- WO-62 ---+
                  |  register-   |--- register_projection_ready: False
                  |  readiness   |    + 2 named blocked reasons
                  |  diagnostic  |    + missing_register_fields list
                  +--------------+
```

Notes on the graph:

- WO-50, WO-51, WO-52 / WO-53, and WO-58 are independent of the
  source-intake chain.
- WO-57 is the only composer that calls WO-55, WO-56, and WO-54 in
  strict register -> bridge -> trace order.
- WO-59 is the only composer that calls WO-57 (smoke package) and
  WO-58 (diagnostic reporter) in strict package -> diagnostics order.
- WO-60, WO-61, and WO-62 form a separate chain. WO-61 consumes an
  injected `fetch_url` and produces an observation that is
  structurally insufficient for WO-55. WO-62 makes that gap
  explicit and emits `register_projection_ready: False`.
- No edge in this graph carries raw URL, raw bytes, full content
  hash, raw pasted text, or qualified source material. Edges carry
  structural metadata only.

## 2. Per-Work-Order Surface Table

The table records the input, output, asserted invariants, and
explicit non-actions for each scaffold from WO-50 onward. The
non-action list is bounded by the originating Work Order and is NOT
claimed exhaustive.

### WO-50 - scaffold_route_query_probe

- Input: WO-31 admitted synthetic payloads (already loaded).
- Output: route-query probe observations.
- Asserts: route-first probe behavior over synthetic payloads;
  observations are scaffold-only.
- Does NOT: invoke any real or mock adapter; perform retrieval,
  scoring, or ranking; select architecture.

### WO-51 - scaffold_route_query_ambiguity_probe

- Input: WO-31 admitted synthetic payloads plus test-time
  `declared_candidate_fixture_ids` markers.
- Output: 14-key result including `ambiguous_observation_count`.
- Asserts: ambiguity is declared by markers, never inferred;
  declared cross-plane candidates suppress exact-text route
  observations including on exact-text matches.
- Does NOT: modify the WO-50 probe module; perform similarity or
  near-match analysis; select architecture.

### WO-52 - scaffold_conflicting_evidence_guard

- Input: scaffold observation entries.
- Output: 9-key result with `inspected_entry_count`,
  `inspected_class_counts`, `declared_conflict_kinds_checked`, four
  literal-False booleans, `guard_kind`, `guard_note`.
- Asserts: five declared conflict kinds detected; halt event
  recorded before raise on each.
- Does NOT: modify the WO-50 / WO-51 probe modules; perform
  semantic conflict inference; claim exhaustiveness of the kind
  set.

### WO-53 - scaffold_conflicting_evidence_guard (coverage extension)

- In-place extension to the WO-52 module authorized by WO-53 packet
  only.
- `DECLARED_CONFLICT_KINDS` grew from 5 to 8 entries.
- Three new exception classes added (`GoldenMissWithOfficialRouteReference`,
  `HardNegativeCandidateOnlyWithoutCandidateOrNormalizedPlane`,
  `BoundaryViolationExpectedHaltWithoutClassification`).
- WO-52 public surface preserved verbatim.
- Does NOT: change the WO-52 function signature, the 9-key result
  shape, the event namespace, or the halt-before-raise pattern.

### WO-54 - scaffold_source_intake_trace

- Input: `input_prompt` (non-empty string); source records
  (already loaded).
- Output: 15-key result with structural-only `input_prompt_observed`
  and `normalized_intent_observation` (no raw text echoed), id-only
  `normalized_material_refs`, `candidate_route_fragments`,
  `candidate_workflow_fragments`, `rejected_source_count` literal 0,
  `rejection_reasons` literal `[]`, four literal-False authorization
  booleans.
- Asserts: layered route-first invariants (qualification gate
  before any derived material; extracted before normalized;
  normalized before candidate fragments; candidate fragments stay
  `candidate_only: True`); 9 route-status boolean keys plus
  `route_state == "official"` plus `plane == "official_route_results"`
  rejected at every layer including `extracted_material`.
- Does NOT: perform file IO; perform network IO; emit raw prompt
  text; emit raw source content; claim qualification, corpus
  admission, route selection, benchmark readiness, or architecture
  selection.

### WO-55 - scaffold_source_intake_register

- Input: `source_reference_records` (already loaded; list of
  six-field dicts).
- Required fields per record: `source_id`, `origin`, `declared_kind`,
  `hash`, `byte_length`, `observed_at`.
- Bounded `ALLOWED_DECLARED_KINDS`: `prompt_collection`,
  `skill_collection`, `agent_description_collection`,
  `tool_description_collection`, `document_collection`.
- Output: 11-key result with `register_entries` carrying only
  `hash_prefix` (12 chars) + `source_id` + `byte_length` +
  `observed_at` + literal-False `corpus_admitted` + literal-False
  `qualified`, plus literal-zero `corpus_admitted_count` /
  `qualified_count` and four literal-False authorization booleans.
- Asserts: 24 forbidden field names rejected at register layer
  (`qualified`, `qualification_ref`, `corpus_admitted`, plus 5
  derived-material, 6 route-shaped, 8 Source-Card-shaped, 4
  benchmark-fixture-shaped); 9 route-status booleans rejected when
  True (`official`, `is_route`, `is_official_route`,
  `selected_as_official`, `official_route_authorized`,
  `route_authorized`, `production_route`, `selected_route`,
  `executable`).
- Does NOT: compute or echo full hashes (hash is identity / integrity
  only; no `hashlib` tokens in module source); perform file IO;
  perform network IO; emit raw origin or raw bytes into output
  records; create Source Cards or Route Cards.

### WO-56 - scaffold_source_trace_admission_bridge

- Input: WO-55 clean-pass `register_observation` plus
  already-loaded source records.
- Output: 15-key result with linked-source refs (no raw text, no
  full hash, no origin); per-linked-source literal-False
  `corpus_admitted` / `qualified` / `extraction_authorized` /
  `normalization_authorized` / `candidate_derivation_authorized`;
  top-level literal-zero `corpus_admitted_count` /
  `qualified_count`; seven literal-False booleans total at the top
  level.
- Asserts: rejects register observation declaring admission /
  qualification / authorization; rejects per-entry `corpus_admitted`
  or `qualified`; rejects source records declaring derived material,
  13 route-status fields, 8 Source-Card-shaped fields; rejects
  duplicate `source_id`, unknown `source_register_ref`,
  `source_kind != declared_kind`, non-external `source_origin`.
- Does NOT: invoke `run_scaffold_source_intake_trace` or
  `run_scaffold_source_intake_register` (verified by static-scan
  tests); perform file IO; perform network IO; compute hashes.

### WO-57 - scaffold_source_intake_smoke_package

- Input: `input_prompt`, `source_reference_records`,
  `source_records`.
- Output: 20-key result embedding `register_observation`,
  `bridge_observation`, `trace_observation` verbatim, plus
  copied-from-trace candidate-fragment counts,
  `corpus_admitted_count` / `qualified_count` literal 0, and seven
  literal-False booleans.
- Asserts: composes WO-55 -> WO-56 -> WO-54 in strict order with
  short-circuit on any sub-call exception; never swallows
  exceptions; composition order verified by `unittest.mock.patch`
  order tests plus real-failure propagation tests.
- Does NOT: introduce score / scoring / search / query / retrieve /
  rank tokens (verified by static-scan tests); modify WO-54 / WO-55
  / WO-56 modules or tests.

### WO-58 - scaffold_route_invariant_diagnostic_reporter

- Input: scaffold observation list (already loaded).
- Output: 13-key result with 10 bounded diagnostic categories, 3
  allowed severities, advisory `halt_required` flag per diagnostic
  record, four literal-False authorization booleans.
- Asserts: deterministic structural inspection only - no model
  judgment, no fuzzy semantic analysis, no thresholds, no weights;
  diagnostics are review evidence only; advisory `halt_required:
  True` field does NOT cause the reporter to raise; forbidden
  language on input or output triggers halt-before-raise; 11-field
  architecture-selection watch set including `reranker` (the
  static-scan test is tightened to look for `def query` /
  `def search` / `def retrieve` / `def rank` rather than the bare
  substring `rank`, per the Constraints v1 substring-collision
  rule).
- Does NOT: validate routes; qualify sources; admit corpus;
  authorize anything; promote anything to official; perform file
  IO; perform network IO; integrate with IDE / chat / collaborator
  tooling.

### WO-59 - scaffold_source_intake_visible_report

- Input: same as WO-57.
- Output: 17-key result with `package_observation` and
  `diagnostic_report` embedded verbatim, copied-from-package
  candidate-fragment counts, `review_halt_required` advisory
  metadata (True iff `diagnostic_halt_required_count > 0`; does
  NOT flip any authorization boolean), four standard literal-False
  authorization booleans regardless of diagnostic findings.
- Asserts: composes WO-57 (smoke package) then WO-58 (diagnostic
  reporter) in strict order with short-circuit on any sub-call
  exception; never swallows exceptions; does not invoke WO-54,
  WO-55, or WO-56 directly (verified by static-scan tests).
- Does NOT: validate routes; qualify sources; admit corpus; flip
  authorization booleans.

### WO-60 - scaffold_external_source_acquisition_boundary

- Input: `acquisition_requests` (already loaded; list of
  eight-field dicts).
- Bounded `ALLOWED_ORIGIN_MODES`: `url`, `local_path`, `pasted_text`.
- Output: 13-key result with `acquisition_references` carrying
  structural data only (no raw `origin_locator`, no full
  `content_hash`, only 12-char `content_hash_prefix`),
  per-reference literal-False `corpus_admitted` / `qualified` /
  `source_material_extracted` / `route_object_created`, top-level
  literal-zero admission counts, four literal-False authorization
  booleans.
- Asserts: 28 forbidden input fields rejected at acquisition layer;
  False-content contract requires zero length and empty hash; True
  contract requires non-negative int length (bool rejected) and
  non-empty string hash; no URL fetch, no local file read, no
  pasted-text echo.
- Does NOT: fetch URL content; read local paths; echo pasted text;
  compute hashes (no `hashlib` tokens); invoke WO-50 through WO-59
  public functions; integrate with IDE / chat / collaborator
  tooling.

### WO-61 - scaffold_url_acquisition_executor

- Input: `acquisition_requests` (`origin_mode == "url"` only),
  injected `fetch_url` callable, `event_log`.
- Bounded `MAX_FETCHED_BYTES = 65536`.
- Output: 13-key result with `url_acquisition_kind`,
  `url_acquisition_reference_count`, `acquired_references` carrying
  `origin_locator_length`, `content_byte_length`, and 12-char
  `content_hash_prefix` only, per-reference literal-False admission
  booleans, top-level literal-zero `corpus_admitted_count` /
  `qualified_count` / `source_material_extracted_count`, four
  literal-False authorization booleans.
- Asserts: two-pass design (validate all then fetch all) so the
  fetcher is never called if any pre-validation fails; SHA-256
  prefix is computed over the bytes already returned by the
  injected fetcher (`hashlib` allowed in this module by DC-061);
  raw URL never emitted (only `origin_locator_length`); raw bytes
  never emitted (only `content_byte_length`); full hash never
  emitted (only 12-char prefix); strict `isinstance(content_bytes,
  bytes)` enforcement (per WO-61 Codex review-time hardening:
  `bytearray` is rejected).
- Does NOT: import `urllib`, `http.client`, `socket`, `requests`,
  `subprocess`, `os.system`, `shutil`, `pathlib`, or `open(`
  (verified by static-scan tests); invoke WO-50 through WO-60
  public functions; integrate with IDE / chat / collaborator
  tooling.

### WO-62 - scaffold_url_acquisition_register_readiness

- Input: one already-loaded WO-61-style `url_acquisition_observation`
  dict, `event_log`.
- Output: 15-key result with `readiness_kind`,
  `url_acquisition_reference_count`, `register_projection_ready`
  literal False, `register_projection_blocked_reason_count` literal
  2, `register_projection_blocked_reasons` =
  [`origin_not_available_for_wo55_register`,
  `full_hash_not_available_for_wo55_register`],
  `missing_register_fields` = [`origin`, `hash`],
  `safe_to_invent_missing_identity` literal False,
  `source_register_invocation_authorized` literal False, four
  literal-False standard authorization booleans, literal-zero
  `corpus_admitted_count` / `qualified_count`, and `readiness_note`.
- Asserts: 28 forbidden register-projection-shaped fields rejected
  (top-level and per-reference) including raw `origin_locator`, raw
  `content_bytes`, full `content_hash`, every derived-material
  field, every route-shaped field, every Source-Card-shaped field,
  and every benchmark-fixture-shaped field; structural validation
  through nine named exception classes; forbidden-language scan on
  input and output; on a structurally-valid WO-61 observation the
  diagnostic always reports `register_projection_ready: False`.
- Does NOT: invent `origin` or full `hash`; reconstruct missing
  data; relax WO-55; invoke `run_scaffold_source_intake_register`
  (WO-55) or `run_scaffold_url_acquisition_executor` (WO-61)
  (verified by static-scan tests); perform file IO; perform network
  IO; compute hashes; integrate with IDE / chat / collaborator
  tooling.

## 3. Vocabulary

This section records terms that have caused naming-gap confusion or
that future Work Orders are likely to need precisely.

### Identity / integrity terms

- `origin`: raw URL string, raw local-path string, or raw pasted-text
  identifier. Required by the WO-55 register. WO-61 does NOT emit
  this; WO-61 emits `origin_locator_length` instead.
- `origin_locator_length`: integer length of the raw origin locator,
  with no content. Emitted by WO-60 and WO-61. Does NOT satisfy the
  WO-55 `origin` field.
- `hash`: full content hash digest. Required by the WO-55 register.
  WO-61 does NOT emit this; WO-61 emits `content_hash_prefix`
  instead.
- `content_hash_prefix`: 12-character SHA-256 prefix. Emitted by
  WO-60 (declared at length 0 when no content) and WO-61 (computed
  by `hashlib.sha256` over the already-returned bytes; the only
  place `hashlib` is authorized to appear in a scaffold module per
  DC-061). Does NOT satisfy the WO-55 `hash` field.
- `content_byte_length`: integer length of fetched content, with
  no content. Emitted by WO-61. Bounded by `MAX_FETCHED_BYTES =
  65536`.

### Kind / mode terms

- `declared_kind`: WO-55 admission label. Bounded set
  (`ALLOWED_DECLARED_KINDS`):
  `prompt_collection`, `skill_collection`,
  `agent_description_collection`, `tool_description_collection`,
  `document_collection`. NOT claimed exhaustive.
- `origin_mode`: WO-60 acquisition label. Bounded set
  (`ALLOWED_ORIGIN_MODES`): `url`, `local_path`, `pasted_text`.
  Disjoint from `declared_kind`. NOT claimed exhaustive.
- `fragment_kind`: WO-54 candidate-fragment label. Bounded set
  (`ALLOWED_FRAGMENT_KINDS`): `candidate_route_fragment`,
  `candidate_workflow`. Disjoint from `declared_kind` and from
  `origin_mode`. NOT claimed exhaustive.

### Element-shape terms

- source reference: WO-55 input element. Carries the six register
  fields (`source_id`, `origin`, `declared_kind`, `hash`,
  `byte_length`, `observed_at`).
- source record: WO-56 and WO-54 input element. Structural-only;
  never qualifies the source.
- acquisition reference: WO-60 output element. Carries structural
  locator + content-availability claim + (when content declared) a
  12-char `content_hash_prefix`. No raw origin, no raw bytes, no
  full hash.
- acquired reference: WO-61 output element. Carries
  `origin_locator_length`, `content_byte_length`,
  `content_hash_prefix`, and the per-reference literal-False
  admission booleans. No raw origin, no raw bytes, no full hash.

### Process / status terms

- register projection: hypothetical conversion of an acquired
  reference (WO-61 output element) into a WO-55 source reference
  (WO-55 input element). WO-62 asserts this projection is NOT
  structurally ready on WO-61 output and names the two missing
  register fields (`origin`, `hash`).
- register invocation: actually calling
  `run_scaffold_source_intake_register`. NOT authorized by any
  documentation-only Work Order. WO-62 does NOT invoke the WO-55
  public function (verified by static-scan test).
- diagnostic blocked reason: WO-62 string token recorded in
  `register_projection_blocked_reasons`. Observational. NOT a
  recovery hint.
- halt event: `event_log.halt(reason=..., entry_index=...)` call
  recorded immediately before a scaffold module raises a named
  exception. Mandatory per Constraints v1 section D3.
- advisory `halt_required: True`: a flag inside a WO-58 diagnostic
  record that signals reviewer attention. It does NOT cause WO-58
  to raise. It is observational.
- advisory `review_halt_required`: a top-level WO-59 metadata flag
  computed from `diagnostic_halt_required_count > 0`. It does NOT
  flip any authorization / readiness / selection boolean.

## 4. Update Protocol

U1. A future Work Order that adds a new scaffold module SHOULD
append a row to the per-WO table in section 2 of this file, using
the same five-column shape (Input / Output / Asserts / Does NOT /
[implicit] originating Work Order). The row should not introduce
identifier names that collide with existing identifiers in section
3 without resolving the collision first.

U2. A future Work Order that extends a vocabulary term SHOULD
update the relevant subsection of section 3 in this file rather
than coining a parallel term. Parallel terms are how naming gaps
appear (for example, the gap between WO-55 `origin` / `hash` and
WO-61 `origin_locator_length` / `content_hash_prefix` that WO-62
was authored to make explicit).

U3. A reviewer reading a new Work Order packet SHOULD scan
sections 2 and 3 of this file for vocabulary compatibility before
approval. A naming collision flagged here is cheap to fix; a
naming collision discovered after the scaffold ships requires a
separate Work Order (such as WO-62) to make the gap explicit.

U4. This file is a review aid. If a row here ever conflicts with
its originating Work Order boundary doc (`ai-search/NN-...md`), the
boundary doc wins and this map must be corrected. The same applies
to conflicts with `00-controller-checklist.md`,
`00-open-questions.md`, or the ledger. If this file conflicts with
`00-wo-constraints.md`, both compiled references must be reconciled
against the canonical documents rather than treating either compiled
reference as authority.
