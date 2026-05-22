"""End-to-end scaffold dry-run for the minimal benchmark harness.

Per WO-19 (DC-022): this is a toy-only end-to-end runner that wires the
harness modules together. It is not real benchmark execution and not
architecture selection. The dry-run consumes scaffold-internal toy
fixtures and a registered toy configuration; it produces a human review
package via the harness review_package assembler.

Per WO-23 (DC-026): the default path wires the scaffold-internal mock
retrieval adapter from `harness/mock_adapter.py` into the dry-run. The
adapter is invoked after fixture and configuration loading; its output
preserves the five planes named in `21-retrieval-adapter-contract.md`
Section 3 with explicit empty-plane recording and records no selection,
recommendation, winner, best, or production-ready claim. The toy response
used by the contract runner is derived from the adapter output; the
review package surfaces adapter-output evidence at boundary level. This
is not real retrieval; the adapter does not contact any retrieval system.

Per WO-25 (DC-028): the dry-run optionally accepts `manifest_path` and
`expected_manifest_id` parameters. When both are provided, the
scaffold-internal manifest loader from `harness/manifest_loader.py` is
invoked after reproducibility capture and before the mock adapter is
invoked; the loaded manifest's identifiers are surfaced in the assembled
review package as `manifest_evidence`. When neither is provided, the
existing WO-23 behavior is preserved unchanged. When exactly one is
provided, an `IncompleteManifestParameters` error is raised after an
explicit halt event is recorded; no fixture or configuration loading is
performed in that case. The manifest is consumed as observation only;
the loader's existence does not authorize production manifest
registration, real benchmark execution, or any architecture selection.

Per WO-26 (DC-029): in manifest mode, after the manifest loader succeeds
and before the mock adapter is invoked, the dry-run verifies that the
loaded manifest's configuration identifier matches the loaded
configuration. Only after that match does it derive a bounded
scaffold-internal registered configuration observation from the loaded
configuration identifier and the loaded manifest. The observation records
the configuration id, manifest id, adapter kind, declared planes,
manifest non-selection posture, and explicit non-authority markers
(`registration_authority_decided: False` and
`production_registration: False`). It is attached to the assembled review
package as `registered_configuration_observation` after a
forbidden-language re-scan. The observation step does not run in default
no-manifest mode and is skipped on any manifest loader rejection or
manifest/configuration identity mismatch. It is not production
registration, not registration authority, not validation evidence, and
not architecture selection.

Per WO-27 (DC-030): the dry-run optionally accepts a
`snapshot_output_path` parameter. When provided, after package assembly
and all evidence attachment, the scaffold-internal artifact snapshot
writer from `harness/artifact_snapshot.py` writes a deterministic UTF-8
JSON snapshot of the assembled package (with adapter, manifest, and
registered configuration observation evidence already in place) to the
caller-provided path; the returned snapshot metadata (`output_path`,
`sha256`, `byte_length`) is attached to the package as
`snapshot_evidence`. When `snapshot_output_path` is omitted the default
WO-26 behavior is preserved exactly and no file is written. The writer
records a `snapshot_written` event on success and rejects forbidden
selection language or a non-dict package before any write occurs. This
is not a production artifact contract, not run artifact retention or
storage policy (OQ-056 remains open), not a production artifact schema
(OQ-076 remains open), not benchmark execution, and not architecture
selection.

Module composition order (locked under WO-19, extended under WO-23,
WO-25, WO-26, and WO-27):
  1. Create EventLog.
  2. Validate manifest parameter consistency (both-or-neither). On
     inconsistency, record a `manifest_parameters_incomplete` halt event
     and raise IncompleteManifestParameters before any loading occurs.
  3. Load and SHA-256 hash-verify the toy fixture.
  4. Load and drift-check the toy configuration.
  5. Capture reproducibility evidence.
  6. Record loaded fixture hash and configuration identifier into the
     reproducibility record.
  7. If manifest parameters are provided, invoke the scaffold-internal
     manifest loader. Manifest loader rejection paths halt before adapter
     invocation and before the registered configuration observation
     step.
  8. If a manifest was successfully loaded, verify that its
     configuration identifier matches the loaded configuration. On
     mismatch, record a `manifest_configuration_mismatch` halt event and
     raise ManifestConfigurationMismatch before observation or adapter
     invocation.
  9. If a manifest was successfully loaded and matched, derive the
     scaffold-internal registered configuration observation from the
     loaded configuration identifier and the loaded manifest. Record a
     `registered_configuration_observed` event into the EventLog
     summarizing the observation's identifiers and non-authority
     markers.
 10. Invoke the scaffold-internal mock adapter on the loaded fixture and
     configuration; record adapter invocation and per-plane presence
     events into the EventLog.
 11. Create ContractRunner and register scaffold-internal toy contract
     checks (or a test-supplied override).
 12. Derive a toy response from the fixture, configuration, and adapter
     output.
 13. Run the contract checks against the toy response.
 14. Assemble the human review package and attach adapter-output evidence
     to it. If a manifest was loaded, attach manifest evidence and the
     registered configuration observation to the package as well.
     Re-scan each attached structure for forbidden language.
 15. If `snapshot_output_path` was provided, write the assembled package
     (with all evidence in place from step 14) as a deterministic UTF-8
     JSON snapshot via `harness/artifact_snapshot.py`. Attach the
     returned metadata (`output_path`, `sha256`, `byte_length`) to the
     package as `snapshot_evidence` and refresh the returned package's
     event view so the `snapshot_written` event is observable to the
     caller. When `snapshot_output_path` is omitted, this step is skipped
     and no file is written.

Halt points: incomplete manifest parameters raise
IncompleteManifestParameters before any other loading. Fixture hash
mismatch raises FixtureHashMismatch and prevents both adapter invocation
and package assembly. Configuration drift raises ConfigurationDrift and
prevents both adapter invocation and package assembly. Manifest loader
rejection paths (`MalformedManifestJSON`, `NonObjectManifest`,
`MissingManifestScaffoldMarker`, `MissingRequiredManifestField`,
`ManifestIdMismatch`, `ManifestDeclaresSelection`,
`ForbiddenLanguageInManifest`) prevent adapter invocation. Manifest and
configuration identifier mismatch raises ManifestConfigurationMismatch
and prevents observation creation, adapter invocation, and package
assembly. Contract failure disqualifies the toy configuration; the
package is assembled and surfaces the disqualification.
"""

import os

from harness.artifact_snapshot import write_scaffold_snapshot
from harness.config_loader import load_configuration
from harness.contract_runner import ContractRunner
from harness.event_log import EventLog
from harness.fixture_loader import load_fixture
from harness.manifest_loader import load_manifest
from harness.mock_adapter import PLANE_NAMES, run_mock_adapter
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES, load_fixture_payload
from harness.reproducibility import (
    add_configuration_identifier,
    add_fixture_hash,
    capture_environment,
)
from harness.review_package import (
    FORBIDDEN_PHRASES,
    ForbiddenLanguageInReviewPackage,
    assemble,
)


class IncompleteManifestParameters(Exception):
    """Raised when exactly one of manifest_path / expected_manifest_id is provided."""


class ManifestConfigurationMismatch(Exception):
    """Raised when a loaded manifest does not name the loaded configuration."""


class IncompletePayloadParameters(Exception):
    """Raised when exactly one of payload_path / expected_fixture_class is provided."""


def _default_toy_contract_checks():
    """Return the scaffold-internal toy contract checks for the dry-run.

    Under WO-23, the toy response is derived from the mock adapter output.
    These checks operate on that response and verify that the adapter
    output's plane separation, empty-plane recording, and non-selection
    posture are preserved through to the contract-check surface. They are
    illustrative; real benchmark contract checks are Codex-authorized and
    outside the scaffold's scope.
    """
    return [
        (
            "toy_response_has_fixture_marker",
            lambda response: "fixture_marker" in response,
        ),
        (
            "toy_response_has_configuration_id",
            lambda response: response.get("configuration_id") is not None,
        ),
        (
            "toy_response_no_raw_internet_content",
            lambda response: "raw_internet_content" not in response,
        ),
        (
            "toy_response_has_adapter_kind",
            lambda response: response.get("adapter_kind") == "mock_scaffold_internal",
        ),
        (
            "toy_response_records_no_selection",
            lambda response: response.get("selection_made") is False,
        ),
        (
            "toy_response_preserves_plane_separation",
            lambda response: response.get("plane_separation_preserved") is True,
        ),
        (
            "toy_response_records_empty_planes_explicitly",
            lambda response: isinstance(response.get("empty_planes"), list),
        ),
    ]


def _derive_toy_response(fixture, configuration, adapter_output):
    """Derive a deterministic toy response from the fixture, configuration,
    and mock adapter output.

    The response is scaffold-internal and exists only to exercise the
    contract runner. It is not a retrieval-system response and carries no
    quality or performance semantics. It surfaces a sanitized view of the
    adapter output (per-plane entry count and is_empty marker, plus the
    adapter's non-selection posture) so contract checks can verify plane
    preservation without making the response itself a route-returning
    surface.
    """
    fixture_marker = None
    sample_record_id = None
    if isinstance(fixture, dict):
        fixture_marker = fixture.get("_fixture_marker")
        record = fixture.get("sample_record")
        if isinstance(record, dict):
            sample_record_id = record.get("id")
    configuration_id = None
    if isinstance(configuration, dict):
        configuration_id = configuration.get("id")
    plane_summary = {
        plane: {
            "entry_count": len(adapter_output[plane]),
            "is_empty": plane in adapter_output["empty_planes"],
        }
        for plane in PLANE_NAMES
    }
    plane_separation_preserved = all(
        all(entry.get("plane") == plane for entry in adapter_output[plane])
        for plane in PLANE_NAMES
    )
    return {
        "fixture_marker": fixture_marker,
        "configuration_id": configuration_id,
        "sample_record_id": sample_record_id,
        "adapter_kind": adapter_output["adapter_kind"],
        "selection_made": adapter_output["selection_made"],
        "plane_summary": plane_summary,
        "empty_planes": list(adapter_output["empty_planes"]),
        "plane_separation_preserved": plane_separation_preserved,
    }


def _adapter_output_evidence(adapter_output):
    """Derive structured evidence summarizing the adapter output for the
    review package.

    The structure preserves the five-plane separation and explicit
    empty-plane recording. It is scaffold-internal observation only.
    """
    planes = {}
    for plane in PLANE_NAMES:
        entries = adapter_output[plane]
        planes[plane] = {
            "entry_count": len(entries),
            "is_empty": plane in adapter_output["empty_planes"],
            "entries": [dict(entry) for entry in entries],
        }
    return {
        "adapter_kind": adapter_output["adapter_kind"],
        "selection_made": adapter_output["selection_made"],
        "selection_note": adapter_output["selection_note"],
        "empty_planes": list(adapter_output["empty_planes"]),
        "planes": planes,
        "evidence_note": (
            "Scaffold-internal mock adapter conformance evidence per "
            "ai-search/21-retrieval-adapter-contract.md. Observation "
            "only; no retrieval output, validation input, or system "
            "choice."
        ),
    }


def _registered_configuration_observation(configuration_id, manifest):
    """Derive a bounded scaffold-internal registered configuration
    observation from the loaded configuration identifier and the loaded
    manifest.

    The observation records configuration and manifest identifiers, the
    manifest's adapter kind, the declared plane list, and the manifest's
    non-selection posture; it also records explicit non-authority markers
    (`registration_authority_decided`, `production_registration`) and an
    evidence note. It is scaffold-internal observation only.
    """
    return {
        "configuration_id": configuration_id,
        "manifest_id": manifest["manifest_id"],
        "adapter_kind": manifest["adapter_kind"],
        "planes_declared": list(manifest["planes_declared"]),
        "selection_made": manifest["selection_made"],
        "registration_authority_decided": False,
        "production_registration": False,
        "evidence_note": (
            "Scaffold-internal registered configuration observation per "
            "ai-search/26-toy-registered-configuration-flow.md. "
            "Observation only; no production registration, registration "
            "authority decision, validation input, or system choice."
        ),
    }


def _manifest_evidence(manifest):
    """Derive structured evidence summarizing the loaded manifest for the
    review package.

    The structure surfaces the manifest identifiers and the declared plane
    list at boundary level. It is scaffold-internal observation only.
    """
    return {
        "manifest_id": manifest["manifest_id"],
        "adapter_kind": manifest["adapter_kind"],
        "configuration_id": manifest["configuration_id"],
        "planes_declared": list(manifest["planes_declared"]),
        "selection_made": manifest["selection_made"],
        "evidence_note": (
            "Scaffold-internal toy manifest evidence per "
            "ai-search/24-retrieval-configuration-manifest-scaffold.md. "
            "Observation only; no production manifest registration, "
            "validation input, or system choice."
        ),
    }


def _payload_evidence(payload):
    """Derive structured evidence summarizing the loaded fixture payload
    for the review package.

    The structure surfaces payload identifiers and entry count at boundary
    level. It is scaffold-internal observation only. Per WO-33 / DC-036,
    the payload loader (`harness/payload_loader.py`) has already verified
    that no string scalar inside the payload contains any forbidden
    phrase, vendor / model name, or positive-claim phrase; the evidence
    helper extracts only the identifiers needed for review.
    """
    entries = payload.get("entries", []) or []
    entry_ids = []
    for entry in entries:
        if isinstance(entry, dict) and isinstance(entry.get("fixture_id"), str):
            entry_ids.append(entry["fixture_id"])
    return {
        "fixture_class": payload.get("fixture_class"),
        "fixture_version": payload.get("fixture_version"),
        "entry_count": len(entries),
        "entry_fixture_ids": entry_ids,
        "evidence_note": (
            "Scaffold-internal fixture payload evidence per "
            "ai-search/32-fixture-payload-loader-scaffold.md and "
            "ai-search/33-payload-loader-dry-run-integration.md. "
            "Observation only; no measurement report, validation input, "
            "production registration, or system choice."
        ),
    }


def _walk_strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, sub_value in value.items():
            for inner in _walk_strings(key):
                yield inner
            for inner in _walk_strings(sub_value):
                yield inner
    elif isinstance(value, (list, tuple)):
        for sub_value in value:
            for inner in _walk_strings(sub_value):
                yield inner


def _assert_no_forbidden_language(value, structure_name):
    """Re-apply the forbidden-language scans to a structure attached to
    the package after assemble() returns.

    The selection-language scan mirrors `harness/review_package.py`.
    The positive-claim scan mirrors `harness/payload_loader.py`, because
    post-assembly evidence must not reintroduce claim phrases removed
    from admitted payloads.
    """
    for text in _walk_strings(value):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                raise ForbiddenLanguageInReviewPackage(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, structure_name
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                raise ForbiddenLanguageInReviewPackage(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, structure_name
                    )
                )


def run_toy_dry_run(
    fixture_path,
    fixture_sha256,
    config_path,
    registered_config,
    deterministic_seed,
    contract_checks=None,
    manifest_path=None,
    expected_manifest_id=None,
    snapshot_output_path=None,
    payload_path=None,
    expected_fixture_class=None,
):
    """Run the toy end-to-end dry-run and return a human review package.

    Halt behavior:
    - Incomplete manifest parameters (exactly one of `manifest_path` /
      `expected_manifest_id` provided) raises IncompleteManifestParameters
      before any fixture or configuration loading. The EventLog records
      a `manifest_parameters_incomplete` halt event.
    - Incomplete payload parameters (exactly one of `payload_path` /
      `expected_fixture_class` provided) raises IncompletePayloadParameters
      before any fixture, configuration, or manifest loading. The
      EventLog records a `payload_parameters_incomplete` halt event.
    - Fixture hash mismatch raises FixtureHashMismatch (no package
      returned; adapter is not invoked).
    - Configuration drift raises ConfigurationDrift (no package returned;
      adapter is not invoked).
    - Manifest loader rejection paths raise the named exceptions from
      `harness/manifest_loader.py` (`MalformedManifestJSON`,
      `NonObjectManifest`, `MissingManifestScaffoldMarker`,
      `MissingRequiredManifestField`, `ManifestIdMismatch`,
      `ManifestDeclaresSelection`, `ForbiddenLanguageInManifest`). The
      adapter is not invoked when any of these are raised.
    - Payload loader rejection paths raise the named exceptions from
      `harness/payload_loader.py` (`MalformedPayloadJSON`,
      `NonObjectPayload`, `MissingPayloadMarker`, `InvalidPayloadMarker`,
      `PayloadFixtureClassMismatch`, `MissingPayloadFixtureVersion`,
      `EmptyOrMissingPayloadEntries`, `MissingEntryFixtureId`,
      `DuplicateEntryFixtureId`, `MissingEntrySyntheticMarker`,
      `MissingPlaneSeparationMarkers`, `ForbiddenLanguageInPayload`,
      `VendorMentionInPayload`, `ForbiddenClaimInPayload`,
      `UnknownPlaneNameInPayload`, `PlaneOverlapInPayload`). The adapter
      is not invoked when any of these are raised. The payload loader
      runs after manifest / registered-configuration observation (when
      manifest mode is active) and before the mock adapter.
    - Contract failure disqualifies the configuration; the package is
      assembled and records the disqualification. Adapter output evidence
      (and manifest evidence, registered configuration observation, and
      payload evidence when their respective inputs were supplied) are
      attached to the package regardless of contract outcome because
      they are produced before contract checks run.

    The optional `contract_checks` parameter accepts a list of
    `(name, callable)` pairs and is intended for scaffold tests that need
    to exercise the contract failure path. When omitted, the
    scaffold-internal default toy checks are used.

    The optional `manifest_path` and `expected_manifest_id` parameters
    enable scaffold-internal manifest loading. Both must be provided
    together, or neither (both-or-neither). When provided, the
    scaffold-internal manifest loader is invoked after reproducibility
    capture and before the mock adapter is invoked; the loaded manifest's
    identifiers are surfaced in the assembled review package as
    `manifest_evidence`. The manifest is consumed as observation only.

    The optional `snapshot_output_path` parameter enables scaffold-internal
    artifact snapshot writing. When provided, after package assembly and
    all evidence attachment, the scaffold-internal artifact snapshot
    writer writes a deterministic UTF-8 JSON snapshot of the assembled
    package to the caller-provided path; the returned snapshot metadata
    is attached to the package as `snapshot_evidence`. When omitted, no
    file is written and no `snapshot_evidence` key is attached.

    The optional `payload_path` and `expected_fixture_class` parameters
    enable scaffold-internal fixture payload loading per WO-32 / DC-035.
    Both must be provided together, or neither (both-or-neither). When
    provided, the scaffold-internal payload loader is invoked after
    manifest / registered-configuration observation (when manifest mode
    is active) and before the mock adapter is invoked; the loaded
    payload's identifiers are surfaced in the assembled review package
    as `payload_evidence`. The payload is consumed as observation only;
    loader rejection halts before adapter invocation.
    """
    event_log = EventLog()

    payload_path_provided = payload_path is not None
    expected_fixture_class_provided = expected_fixture_class is not None
    if payload_path_provided != expected_fixture_class_provided:
        event_log.halt(
            "payload_parameters_incomplete",
            payload_path_provided=payload_path_provided,
            expected_fixture_class_provided=expected_fixture_class_provided,
        )
        raise IncompletePayloadParameters(
            "run_toy_dry_run requires both payload_path and "
            "expected_fixture_class, or neither; received only one."
        )

    manifest_path_provided = manifest_path is not None
    expected_manifest_id_provided = expected_manifest_id is not None
    if manifest_path_provided != expected_manifest_id_provided:
        event_log.halt(
            "manifest_parameters_incomplete",
            manifest_path_provided=manifest_path_provided,
            expected_manifest_id_provided=expected_manifest_id_provided,
        )
        raise IncompleteManifestParameters(
            "run_toy_dry_run requires both manifest_path and "
            "expected_manifest_id, or neither; received only one."
        )

    fixture = load_fixture(fixture_path, fixture_sha256, event_log)
    configuration = load_configuration(config_path, registered_config, event_log)

    environment = capture_environment(deterministic_seed)
    add_fixture_hash(environment, os.path.basename(fixture_path), fixture_sha256)
    configuration_id = None
    if isinstance(configuration, dict):
        configuration_id = configuration.get("id")
    if configuration_id is not None:
        add_configuration_identifier(environment, configuration_id)

    manifest = None
    registered_observation = None
    payload = None
    if manifest_path_provided and expected_manifest_id_provided:
        manifest = load_manifest(manifest_path, expected_manifest_id, event_log)
        if manifest["configuration_id"] != configuration_id:
            event_log.halt(
                "manifest_configuration_mismatch",
                loaded_configuration_id=configuration_id,
                manifest_configuration_id=manifest["configuration_id"],
                manifest_id=manifest["manifest_id"],
            )
            raise ManifestConfigurationMismatch(
                "Manifest {0!r} names configuration_id {1!r}; loaded "
                "configuration_id is {2!r}".format(
                    manifest["manifest_id"],
                    manifest["configuration_id"],
                    configuration_id,
                )
            )
        registered_observation = _registered_configuration_observation(
            configuration_id, manifest
        )
        event_log.append(
            "registered_configuration_observed",
            configuration_id=registered_observation["configuration_id"],
            manifest_id=registered_observation["manifest_id"],
            adapter_kind=registered_observation["adapter_kind"],
            planes_declared=list(registered_observation["planes_declared"]),
            selection_made=registered_observation["selection_made"],
            registration_authority_decided=registered_observation[
                "registration_authority_decided"
            ],
            production_registration=registered_observation["production_registration"],
        )

    if payload_path_provided and expected_fixture_class_provided:
        payload = load_fixture_payload(
            payload_path, expected_fixture_class, event_log
        )

    adapter_output = run_mock_adapter(fixture, configuration)
    event_log.append(
        "mock_adapter_invoked",
        adapter_kind=adapter_output["adapter_kind"],
        selection_made=adapter_output["selection_made"],
        empty_planes=list(adapter_output["empty_planes"]),
        plane_entry_counts={
            plane: len(adapter_output[plane]) for plane in PLANE_NAMES
        },
    )
    for plane in PLANE_NAMES:
        event_log.append(
            "adapter_plane_present",
            plane=plane,
            entry_count=len(adapter_output[plane]),
            is_empty=plane in adapter_output["empty_planes"],
        )

    runner = ContractRunner(event_log)
    checks = (
        contract_checks if contract_checks is not None else _default_toy_contract_checks()
    )
    for name, check_fn in checks:
        runner.add_check(name, check_fn)

    response = _derive_toy_response(fixture, configuration, adapter_output)
    runner.run(configuration_id or "toy-dry-run-configuration", response)

    package = assemble(event_log, runner, environment)
    adapter_evidence = _adapter_output_evidence(adapter_output)
    _assert_no_forbidden_language(adapter_evidence, "adapter-output evidence")
    package["adapter_output_evidence"] = adapter_evidence
    if manifest is not None:
        manifest_evidence = _manifest_evidence(manifest)
        _assert_no_forbidden_language(manifest_evidence, "manifest evidence")
        package["manifest_evidence"] = manifest_evidence
    if registered_observation is not None:
        _assert_no_forbidden_language(
            registered_observation, "registered configuration observation"
        )
        package["registered_configuration_observation"] = registered_observation
    if payload is not None:
        payload_evidence = _payload_evidence(payload)
        _assert_no_forbidden_language(payload_evidence, "payload evidence")
        package["payload_evidence"] = payload_evidence
    if snapshot_output_path is not None:
        snapshot_metadata = write_scaffold_snapshot(
            package, snapshot_output_path, event_log=event_log
        )
        package["snapshot_evidence"] = snapshot_metadata
        package["all_events"] = event_log.events
        package["event_count"] = len(package["all_events"])
    return package
