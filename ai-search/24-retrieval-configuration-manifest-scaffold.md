# ai-search - Retrieval Configuration Manifest Scaffold

Document type: Phase 4 / Phase 9 / Retrieval configuration manifest scaffold boundary
Owner: Codex (controller)
Author of this draft: Claude (builder/documentation agent)
Status: Draft - pending Codex review
Work Order: WO-24

---

## 1. Purpose

This document records the scaffold-internal retrieval configuration manifest
loader authorized under WO-24 at `harness/manifest_loader.py` together with
the harness-internal toy manifest fixture at
`harness/tests/fixtures/toy_retrieval_manifest.json`. Their sole role is to
make registered configuration manifests observable through the harness
without authoring a production manifest schema and without selecting any
architecture.

The manifest loader exists so that future adapter and dry-run work can
consume a registered manifest object through a tested loader rather than
constructing manifest objects inline. The loader is scaffold-internal: it
admits a toy manifest carrying explicit harness-internal markers and
rejects any manifest that violates the scaffold-level shape and boundary
rules.

The manifest loader is not a production manifest schema. The substantive
contents of a production manifest (its fields, their types, their
provenance, their version pinning, and their authority signature) remain
owned by Codex and are tracked under OQ-057 (configuration registration
authority) and OQ-076 (production artifact contracts). Both remain open.

## 2. Scaffold-Only Scope

The WO-24 scaffold touches only the six files allowed by the WO-24 packet:
`harness/manifest_loader.py`, `harness/tests/test_manifest_loader.py`,
`harness/tests/fixtures/toy_retrieval_manifest.json`,
`ai-search/24-retrieval-configuration-manifest-scaffold.md`,
`ai-search/00-open-questions.md`, and `ai-search/00-claude-task-ledger.md`.

The scaffold does not:

- Modify the mock adapter (`harness/mock_adapter.py`), the dry-run
  (`harness/dry_run.py`), the fixture loader, the configuration loader,
  the event log, the contract runner, the reproducibility recorder, the
  review-package assembler, or any test under `harness/tests/` other than
  the new `test_manifest_loader.py`.
- Modify any file under `benchmark-fixtures/`. The empty fixture skeleton
  authorized under WO-20 remains untouched.
- Author a production manifest schema, a field-type registry, an
  authority signature scheme, a version pinning scheme, a provenance
  schema, or any production artifact contract.

The loader is Python standard library only. It declares no third-party
imports.

## 3. Manifest Loader Boundary

The loader exposes a single public function:

    load_manifest(manifest_path, expected_manifest_id, event_log)

The function:

- Opens `manifest_path` read-only with UTF-8 encoding and parses it as
  JSON. Parse failure raises `MalformedManifestJSON` after a
  `manifest_malformed_json` halt event is recorded.
- Verifies the top-level value is a JSON object. Otherwise raises
  `NonObjectManifest` after a `manifest_non_object` halt event.
- Verifies the scaffold marker key (`_manifest_marker`) is present in the
  top-level object and carries a harness-internal marker string. Otherwise
  raises `MissingManifestScaffoldMarker` after a
  `manifest_missing_scaffold_marker` halt event.
- Verifies every required scaffold-level field is present:
  `manifest_id`, `adapter_kind`, `configuration_id`, `planes_declared`,
  `selection_made`. Missing any of these raises
  `MissingRequiredManifestField` after a
  `manifest_missing_required_field` halt event whose payload names the
  missing field.
- Verifies `manifest["manifest_id"] == expected_manifest_id`. Otherwise
  raises `ManifestIdMismatch` after a `manifest_id_mismatch` halt event.
- Verifies `manifest["selection_made"] is False` (exactly the boolean
  literal `False`, not a truthy value). Otherwise raises
  `ManifestDeclaresSelection` after a `manifest_declares_selection`
  halt event.
- Re-scans every string scalar inside the manifest for any phrase in
  `harness.review_package.FORBIDDEN_PHRASES`. Any hit raises
  `ForbiddenLanguageInManifest` after a `manifest_forbidden_language`
  halt event whose payload names the offending phrase.
- On success, records exactly one `manifest_loaded` event into the
  EventLog with `path`, `manifest_id`, `adapter_kind`,
  `configuration_id`, and a copy of `planes_declared`, and returns the
  parsed manifest object.

The loader does not perform retrieval, indexing, ranking, network calls,
or any architecture decision. It does not consume `benchmark-fixtures/`
content. It does not mutate any production-like state.

## 4. Toy Manifest Boundary

The on-disk toy manifest at
`harness/tests/fixtures/toy_retrieval_manifest.json` carries:

- `_manifest_marker`: a harness-internal marker string identifying the
  file as toy data.
- `_purpose`: a free-text purpose note recording that the file is a
  scaffold unit test fixture per WO-24 / DC-027.
- `manifest_id`: `"toy-scaffold-manifest"`.
- `adapter_kind`: `"mock_scaffold_internal"` matching the scaffold-internal
  mock adapter under DC-025.
- `configuration_id`: `"toy-scaffold-config"` matching the existing toy
  configuration under `harness/tests/fixtures/toy_scaffold_config.json`.
- `planes_declared`: the five plane names from
  `21-retrieval-adapter-contract.md` Section 3.
- `selection_made`: `false`.
- `selection_note`: a string recording that the toy manifest does not
  propose any configuration and that selection authority remains with
  Codex under the Indexing Excellence Gate.

The toy manifest does not contain real benchmark data, real retrieval
parameters, real vendor names, real ANN backend names, real reranker
names, embedding model names, index family choices, ablation cell
definitions, or any architecture claim. It is harness-internal toy data
only and is consumed only by the scaffold's unit tests.

## 5. Required Manifest Properties At Scaffold Level

A scaffold-level manifest admitted by the loader must satisfy every one
of the following properties. Each property is enforced in code by the
loader and exercised in tests:

- The top-level value is a JSON object.
- The scaffold marker key (`_manifest_marker`) is present and carries a
  harness-internal marker string.
- The required-field set is present: `manifest_id`, `adapter_kind`,
  `configuration_id`, `planes_declared`, `selection_made`.
- `manifest_id` equals the caller-supplied `expected_manifest_id`.
- `selection_made` is exactly the boolean literal `False`.
- No string scalar anywhere in the manifest contains any phrase from
  `harness.review_package.FORBIDDEN_PHRASES`.

These properties are scaffold-level only and do not imply or pre-empt a
production manifest schema. The set of required fields is the minimum
needed to make scaffold consumption observable; production schema
authority remains with Codex.

## 6. Rejection Conditions

The loader rejects a manifest at every named boundary. Each rejection is
both an exception raised to the caller and a halt event recorded into the
event log; no rejection is silent.

| Condition | Exception | Halt event reason |
|-----------|-----------|-------------------|
| File does not parse as JSON | `MalformedManifestJSON` | `manifest_malformed_json` |
| Top-level JSON value is not an object | `NonObjectManifest` | `manifest_non_object` |
| Scaffold marker key missing or invalid | `MissingManifestScaffoldMarker` | `manifest_missing_scaffold_marker` |
| Required field missing | `MissingRequiredManifestField` | `manifest_missing_required_field` |
| `manifest_id` does not match expected | `ManifestIdMismatch` | `manifest_id_mismatch` |
| `selection_made` is not exactly `False` | `ManifestDeclaresSelection` | `manifest_declares_selection` |
| Forbidden selection phrase appears anywhere in manifest strings | `ForbiddenLanguageInManifest` | `manifest_forbidden_language` |

No silent admission is permitted. No rejection path returns a partially
admitted manifest. The order of checks is fixed: JSON parse, top-level
object, scaffold marker, required-field presence, manifest-id match,
non-selection posture, forbidden-language scan, then the success event
and return.

## 7. Event-Log Behavior

- On success, exactly one `manifest_loaded` event is appended to the
  event log with `path`, `manifest_id`, `adapter_kind`,
  `configuration_id`, and a copy of `planes_declared`. No halt event is
  recorded on the success path.
- On every rejection path, an explicit halt event is appended before the
  exception is raised, with a `reason` from the table in Section 6 and
  payload fields identifying the offending path, missing field, expected
  vs. actual manifest id, or offending forbidden phrase as applicable.
- The loader does not record any event other than the success event and
  the named halt events. It does not record validation events, promotion
  events, demotion events, selection events, or measurement events.

## 8. Relationship To WO-21 Adapter Contract And WO-23 Dry-Run Integration

This scaffold sits inside the constraint surface already established by
WO-21 and WO-23:

- `21-retrieval-adapter-contract.md` Section 9 (Registration Boundary):
  the adapter contract requires registered configuration manifests as
  inputs and explicitly defers manifest substance and authority to Codex
  (OQ-057 remains open). The WO-24 scaffold provides a loader for
  harness-internal toy manifests only; it does not author registration
  authority, does not implement the production manifest substance, and
  does not become a production manifest contract by use.
- `23-mock-adapter-dry-run-integration.md` Section 3 (Exact Integration
  Order): the WO-23 dry-run currently consumes the existing
  scaffold-internal toy configuration via `harness/config_loader.py`. The
  WO-24 manifest loader is not wired into the dry-run under WO-24; any
  future packet that wires it in must respect every boundary in
  Sections 2 through 7 of this document and the dry-run's halt
  invariants.
- `00-controller-checklist.md` Section K (Indexing Excellence Gate)
  continues to govern selection. The manifest loader's existence does
  not imply that any real adapter, vendor, library, ANN backend,
  reranker, retrieval family, ablation cell, multi-stage variant, or
  architecture is authorized, registered, evaluated, or selected.

## 9. Forbidden Scope

The WO-24 scaffold is forbidden from doing any of the following:

- Authoring a production manifest schema, field-type registry, authority
  signature scheme, version pinning scheme, or provenance schema.
- Resolving OQ-057 (configuration registration authority), OQ-076
  (production artifact contracts), OQ-075 (dependency policy beyond the
  first scaffold), or any other open question.
- Reading, writing, or otherwise touching any file under
  `benchmark-fixtures/`.
- Reading, writing, or otherwise touching any production-like state
  (corpus, route registry, source quality graph, validation evidence
  ledger, intent trace store, candidate routes, official routes).
- Performing any real retrieval call, real index lookup, real ranking
  computation, or any network call.
- Selecting any vendor, library, index family, ANN backend, reranker,
  retrieval family, ablation cell, multi-stage variant, or architecture.
- Declaring any configuration a winner, best, recommended, or
  production-ready (enforced by the forbidden-language scan).
- Treating manifest content as validation evidence, as a promotion
  trigger, or as a selection input.
- Introducing a CLI, an entry point, a console script, or any shell
  wrapper.
- Adding third-party dependencies beyond the Python standard library.
- Modifying any file outside the six files allowed under WO-24.

## 10. Not A Production Manifest Schema; Not Architecture Selection

The WO-24 scaffold is explicitly not a production manifest schema. The
required-field set is the minimum needed to make scaffold consumption
observable and to make boundary violations testable. It does not commit
to production field types, production authority signatures, production
provenance rules, production version pinning, production immutability
rules, or production retention rules. All of those remain Codex-owned
and are tracked under OQ-057 and OQ-076.

The WO-24 scaffold is explicitly not architecture selection. The
manifest loader makes no statement about which adapter, vendor, library,
index family, ANN backend, reranker, retrieval family, ablation cell,
multi-stage variant, or architecture is correct, sufficient, preferred,
or production-ready. The Indexing Excellence Gate
(`00-controller-checklist.md` Section K) continues to govern selection.

Any future production manifest schema, real adapter, real benchmark
execution, or architecture selection requires a separate Codex-authored
Work Order whose scope, allowed files, required content, forbidden
scope, acceptance criteria, and evidence requirements are explicit at
issue time.

## 11. Out Of Scope

This document and the WO-24 scaffold are scaffold-internal only. Neither
authorizes:

- A real retrieval, indexing, or ranking implementation.
- A vendor, library, index family, retrieval family, ANN backend,
  reranker, ablation cell, multi-stage variant, or architecture choice.
- A benchmark execution against `benchmark-fixtures/` content.
- A production manifest schema or registration authority scheme.
- A metric, threshold, weight, score, or ranking formula.
- A runtime compile design.
- A validation framework implementation.
- A treatment of the toy manifest as a registered production
  configuration, as benchmark evidence, as validation evidence, or as
  architecture authorization.

All such work requires a future Codex-approved Work Order whose scope,
allowed files, required content, forbidden scope, acceptance criteria,
and evidence requirements are explicit at issue time.
