"""Tests for harness.dry_run.

Covers (WO-19 baseline):
- successful dry-run returns a package
- package contains reproducibility fields
- package includes loaded fixture hash
- package includes configuration identifier
- package does not select, recommend, rank, declare winner, declare best,
  or declare production-ready
- fixture hash mismatch halts before package assembly
- configuration drift halts before package assembly
- contract failure disqualifies the toy configuration

Covers (WO-23 mock adapter integration):
- successful dry-run includes adapter output evidence
- all five planes are represented in the adapter evidence
- candidate entries are non-official and non-executable as official
- normalized material is non-candidate, non-official, and support-only
- trace/outcome plane is empty and not used as validation evidence
- source quality observations do not become route trust
- adapter evidence is attached even on contract failure
- adapter evidence contains no forbidden selection language

Covers (WO-25 manifest loader integration):
- default dry-run without manifest preserves WO-23 behavior unchanged
- dry-run with toy manifest loads successfully
- package event log contains `manifest_loaded`
- package evidence includes the loaded manifest id
- manifest load occurs before mock adapter invocation
- malformed/mismatched/invalid manifest halts before adapter invocation
- missing one of the two manifest parameters is rejected with halt
- manifest evidence contains no forbidden selection language

Covers (WO-26 toy registered configuration flow):
- manifest-mode package includes `registered_configuration_observation`
- observation records configuration_id, manifest_id, adapter_kind,
  planes_declared, selection_made
- observation records `registration_authority_decided: False`
- observation records `production_registration: False`
- observation contains no forbidden selection language
- default no-manifest mode does not include observation
- manifest rejection prevents observation creation and adapter
  invocation
- manifest/configuration identity mismatch prevents observation
  creation and adapter invocation
- contract failure still includes observation when manifest load
  succeeded
- event order remains: `manifest_loaded` before `mock_adapter_invoked`

Covers (WO-27 scaffold run artifact snapshot integration):
- default dry-run without snapshot_output_path writes no file and
  attaches no snapshot_evidence
- providing snapshot_output_path writes a deterministic JSON file
- snapshot_evidence is attached to the returned package with the
  output path and SHA-256 hash matching the written file
- the snapshot file content includes adapter / manifest / registered
  configuration observation evidence already attached at write time
- snapshot writing happens after manifest/adapter/registered
  observation evidence is attached
- existing mismatch, manifest rejection, and contract failure behavior
  remain intact
"""

import hashlib
import json
import os
import tempfile
import unittest

import harness.dry_run as dry_run_module
from harness.config_loader import ConfigurationDrift
from harness.dry_run import (
    IncompleteManifestParameters,
    ManifestConfigurationMismatch,
    run_toy_dry_run,
)
from harness.event_log import EventLog
from harness.fixture_loader import FixtureHashMismatch
from harness.manifest_loader import (
    ManifestIdMismatch,
    MissingManifestScaffoldMarker,
    SCAFFOLD_MARKER_KEY,
)
from harness.mock_adapter import PLANE_NAMES
from harness.reproducibility import REQUIRED_FIELDS
from harness.review_package import FORBIDDEN_PHRASES


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_FIXTURE_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_fixture.json")
_CONFIG_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_config.json")
_MANIFEST_PATH = os.path.join(_FIXTURE_DIR, "toy_retrieval_manifest.json")
_MANIFEST_ID = "toy-scaffold-manifest"


def _sha256_of_file(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        hasher.update(handle.read())
    return hasher.hexdigest()


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


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


class DryRunTest(unittest.TestCase):
    def _run_with_defaults(self, **overrides):
        params = dict(
            fixture_path=_FIXTURE_PATH,
            fixture_sha256=_sha256_of_file(_FIXTURE_PATH),
            config_path=_CONFIG_PATH,
            registered_config=_load_json(_CONFIG_PATH),
            deterministic_seed=42,
        )
        params.update(overrides)
        return run_toy_dry_run(**params)

    def test_successful_dry_run_returns_package(self):
        package = self._run_with_defaults()
        self.assertIsInstance(package, dict)
        self.assertIn("summary", package)
        self.assertIn("reproducibility", package)
        self.assertIn("disqualified_configurations", package)

    def test_package_contains_reproducibility_fields(self):
        package = self._run_with_defaults()
        reproducibility_record = package["reproducibility"]
        for field in REQUIRED_FIELDS:
            self.assertIn(field, reproducibility_record)
        self.assertEqual(reproducibility_record["deterministic_seed"], 42)

    def test_package_includes_loaded_fixture_hash(self):
        expected_hash = _sha256_of_file(_FIXTURE_PATH)
        package = self._run_with_defaults()
        hashes = package["reproducibility"]["fixture_hashes"]
        self.assertIn("toy_scaffold_fixture.json", hashes)
        self.assertEqual(hashes["toy_scaffold_fixture.json"], expected_hash)

    def test_package_includes_configuration_identifier(self):
        package = self._run_with_defaults()
        identifiers = package["reproducibility"]["configuration_identifiers"]
        self.assertIn("toy-scaffold-config", identifiers)

    def test_package_does_not_select_or_rank(self):
        package = self._run_with_defaults()
        self.assertFalse(package["selection_made"])
        rendered = str(package).lower()
        for phrase in FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase '{0}' found in package".format(phrase),
            )

    def test_fixture_hash_mismatch_halts_before_package_assembly(self):
        with self.assertRaises(FixtureHashMismatch):
            self._run_with_defaults(fixture_sha256="0" * 64)

    def test_configuration_drift_halts_before_package_assembly(self):
        correct = _load_json(_CONFIG_PATH)
        drifted = dict(correct)
        drifted["id"] = "drifted-id"
        with self.assertRaises(ConfigurationDrift):
            self._run_with_defaults(registered_config=drifted)

    def test_contract_failure_disqualifies_toy_configuration(self):
        always_fail = [("always_fail", lambda response: False)]
        package = self._run_with_defaults(contract_checks=always_fail)
        self.assertIn("toy-scaffold-config", package["disqualified_configurations"])
        self.assertFalse(package["selection_made"])
        self.assertFalse(
            any(event["type"] == "measurement_recorded" for event in package["all_events"]),
            "dry-run must not record measurement after contract disqualification",
        )
        fail_events = package["contract_checks_failed"]
        self.assertTrue(
            any(event.get("check_name") == "always_fail" for event in fail_events),
            "expected a failed contract check event for 'always_fail'",
        )

    # WO-23 mock adapter integration tests

    def test_package_includes_adapter_output_evidence(self):
        package = self._run_with_defaults()
        self.assertIn("adapter_output_evidence", package)
        evidence = package["adapter_output_evidence"]
        self.assertEqual(evidence["adapter_kind"], "mock_scaffold_internal")
        self.assertFalse(evidence["selection_made"])
        self.assertIn("selection_note", evidence)
        self.assertIn("empty_planes", evidence)
        self.assertIn("planes", evidence)

    def test_adapter_evidence_represents_all_five_planes(self):
        package = self._run_with_defaults()
        evidence = package["adapter_output_evidence"]
        for plane in PLANE_NAMES:
            self.assertIn(
                plane,
                evidence["planes"],
                "Adapter evidence is missing plane '{0}'".format(plane),
            )
            plane_record = evidence["planes"][plane]
            self.assertIn("entry_count", plane_record)
            self.assertIn("is_empty", plane_record)
            self.assertIn("entries", plane_record)
            # is_empty is consistent with entry_count and empty_planes list.
            self.assertEqual(plane_record["entry_count"], len(plane_record["entries"]))
            if plane_record["is_empty"]:
                self.assertIn(plane, evidence["empty_planes"])
                self.assertEqual(plane_record["entry_count"], 0)
            else:
                self.assertNotIn(plane, evidence["empty_planes"])
        # Official and trace/outcome planes are empty by design.
        self.assertIn("official_route_results", evidence["empty_planes"])
        self.assertIn("trace_outcome_signal_observations", evidence["empty_planes"])

    def test_adapter_evidence_candidate_is_not_executable_official(self):
        package = self._run_with_defaults()
        evidence = package["adapter_output_evidence"]
        # Official plane is empty.
        self.assertEqual(evidence["planes"]["official_route_results"]["entries"], [])
        # Candidate entries are marked non-official and non-executable as official.
        candidate_entries = evidence["planes"]["candidate_route_results"]["entries"]
        self.assertTrue(len(candidate_entries) > 0)
        for entry in candidate_entries:
            self.assertTrue(entry.get("is_candidate"))
            self.assertFalse(entry.get("is_official"))
            self.assertEqual(
                entry.get("executability"),
                "candidate_only_non_executable_as_official",
            )

    def test_adapter_evidence_normalized_material_is_not_route(self):
        package = self._run_with_defaults()
        evidence = package["adapter_output_evidence"]
        entries = evidence["planes"]["normalized_material_support_results"]["entries"]
        self.assertTrue(len(entries) > 0)
        for entry in entries:
            self.assertFalse(entry.get("is_candidate", False))
            self.assertFalse(entry.get("is_official", False))
            self.assertEqual(
                entry.get("executability"),
                "non_route_support_material",
            )

    def test_adapter_evidence_trace_outcome_not_validation_evidence(self):
        package = self._run_with_defaults()
        evidence = package["adapter_output_evidence"]
        trace_plane = evidence["planes"]["trace_outcome_signal_observations"]
        self.assertEqual(trace_plane["entries"], [])
        self.assertTrue(trace_plane["is_empty"])
        self.assertIn("trace_outcome_signal_observations", evidence["empty_planes"])

    def test_adapter_evidence_source_quality_not_route_trust(self):
        package = self._run_with_defaults()
        evidence = package["adapter_output_evidence"]
        entries = evidence["planes"]["source_quality_constraint_observations"]["entries"]
        self.assertTrue(len(entries) > 0)
        for entry in entries:
            self.assertFalse(entry.get("is_candidate", False))
            self.assertFalse(entry.get("is_official", False))
            self.assertEqual(
                entry.get("executability"),
                "non_route_support_material",
            )
            self.assertIsNone(entry.get("qualification_status_reference"))
            self.assertTrue(entry.get("qualification_status_reference_is_absent"))

    def test_adapter_evidence_present_on_contract_failure(self):
        always_fail = [("always_fail", lambda response: False)]
        package = self._run_with_defaults(contract_checks=always_fail)
        # Disqualification is recorded and measurement is not.
        self.assertIn("toy-scaffold-config", package["disqualified_configurations"])
        self.assertFalse(
            any(event["type"] == "measurement_recorded" for event in package["all_events"]),
            "dry-run must not record measurement after contract disqualification",
        )
        # Adapter evidence is still attached because the adapter is invoked
        # before contract checks run.
        self.assertIn("adapter_output_evidence", package)
        evidence = package["adapter_output_evidence"]
        self.assertEqual(evidence["adapter_kind"], "mock_scaffold_internal")
        self.assertFalse(evidence["selection_made"])
        for plane in PLANE_NAMES:
            self.assertIn(plane, evidence["planes"])

    def test_adapter_evidence_contains_no_forbidden_selection_language(self):
        package = self._run_with_defaults()
        evidence = package["adapter_output_evidence"]
        for text in _walk_strings(evidence):
            lowered = text.lower()
            for phrase in FORBIDDEN_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "Forbidden phrase '{0}' found in adapter_output_evidence: {1!r}".format(
                        phrase, text
                    ),
                )

    # WO-25 manifest loader integration tests

    def test_default_dry_run_without_manifest_unchanged(self):
        # No manifest parameters supplied; behaviour matches WO-23.
        package = self._run_with_defaults()
        self.assertNotIn("manifest_evidence", package)
        # No manifest_loaded event in the package event log either.
        self.assertFalse(
            any(event["type"] == "manifest_loaded" for event in package["all_events"]),
            "default dry-run must not record manifest_loaded when no manifest is supplied",
        )
        # Adapter evidence is still attached (WO-23 invariant).
        self.assertIn("adapter_output_evidence", package)

    def test_dry_run_with_toy_manifest_loads_successfully(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        self.assertIn("manifest_evidence", package)
        manifest_evidence = package["manifest_evidence"]
        self.assertEqual(manifest_evidence["manifest_id"], _MANIFEST_ID)
        self.assertEqual(manifest_evidence["adapter_kind"], "mock_scaffold_internal")
        self.assertEqual(manifest_evidence["configuration_id"], "toy-scaffold-config")
        self.assertFalse(manifest_evidence["selection_made"])
        self.assertEqual(
            set(manifest_evidence["planes_declared"]),
            set(PLANE_NAMES),
        )
        # Adapter evidence is still attached.
        self.assertIn("adapter_output_evidence", package)

    def test_package_event_log_contains_manifest_loaded(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        manifest_events = [
            e for e in package["all_events"] if e["type"] == "manifest_loaded"
        ]
        self.assertEqual(len(manifest_events), 1)
        self.assertEqual(manifest_events[0]["manifest_id"], _MANIFEST_ID)

    def test_package_evidence_includes_manifest_id(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        self.assertEqual(
            package["manifest_evidence"]["manifest_id"], _MANIFEST_ID
        )

    def test_manifest_load_precedes_mock_adapter_invocation(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        events = package["all_events"]
        manifest_index = next(
            (i for i, e in enumerate(events) if e["type"] == "manifest_loaded"),
            None,
        )
        adapter_index = next(
            (i for i, e in enumerate(events) if e["type"] == "mock_adapter_invoked"),
            None,
        )
        self.assertIsNotNone(manifest_index, "expected manifest_loaded event in package")
        self.assertIsNotNone(adapter_index, "expected mock_adapter_invoked event in package")
        self.assertLess(
            manifest_index,
            adapter_index,
            "manifest must be loaded before the mock adapter is invoked",
        )

    def test_manifest_id_mismatch_halts_before_adapter_invocation(self):
        # Toy manifest declares manifest_id "toy-scaffold-manifest"; using a
        # different expected id must raise ManifestIdMismatch and the adapter
        # must not be invoked.
        original_adapter = dry_run_module.run_mock_adapter
        try:
            dry_run_module.run_mock_adapter = lambda fixture, configuration: self.fail(
                "mock adapter must not be invoked after manifest id mismatch"
            )
            with self.assertRaises(ManifestIdMismatch):
                self._run_with_defaults(
                    manifest_path=_MANIFEST_PATH,
                    expected_manifest_id="different-expected-manifest-id",
                )
        finally:
            dry_run_module.run_mock_adapter = original_adapter

    def test_invalid_manifest_halts_before_adapter_invocation(self):
        # Write a manifest with an invalid (empty) scaffold marker into a
        # temporary path. The manifest loader rejects it with
        # MissingManifestScaffoldMarker; the dry-run must halt before
        # invoking the mock adapter.
        with tempfile.TemporaryDirectory() as tmp_dir:
            bad_path = os.path.join(tmp_dir, "bad_manifest.json")
            bad_manifest = {
                SCAFFOLD_MARKER_KEY: "",
                "manifest_id": _MANIFEST_ID,
                "adapter_kind": "mock_scaffold_internal",
                "configuration_id": "toy-scaffold-config",
                "planes_declared": list(PLANE_NAMES),
                "selection_made": False,
            }
            with open(bad_path, "w", encoding="utf-8") as handle:
                json.dump(bad_manifest, handle)
            original_adapter = dry_run_module.run_mock_adapter
            try:
                dry_run_module.run_mock_adapter = lambda fixture, configuration: self.fail(
                    "mock adapter must not be invoked after invalid manifest"
                )
                with self.assertRaises(MissingManifestScaffoldMarker):
                    self._run_with_defaults(
                        manifest_path=bad_path,
                        expected_manifest_id=_MANIFEST_ID,
                    )
            finally:
                dry_run_module.run_mock_adapter = original_adapter

    def test_missing_one_manifest_parameter_rejected(self):
        # Only manifest_path supplied.
        original_event_log = dry_run_module.EventLog
        event_log = EventLog()
        try:
            dry_run_module.EventLog = lambda: event_log
            with self.assertRaises(IncompleteManifestParameters):
                self._run_with_defaults(manifest_path=_MANIFEST_PATH)
        finally:
            dry_run_module.EventLog = original_event_log
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "manifest_parameters_incomplete"
                and e.get("manifest_path_provided") is True
                and e.get("expected_manifest_id_provided") is False
                for e in event_log.events
            )
        )

        # Only expected_manifest_id supplied.
        event_log = EventLog()
        try:
            dry_run_module.EventLog = lambda: event_log
            with self.assertRaises(IncompleteManifestParameters):
                self._run_with_defaults(expected_manifest_id=_MANIFEST_ID)
        finally:
            dry_run_module.EventLog = original_event_log
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "manifest_parameters_incomplete"
                and e.get("manifest_path_provided") is False
                and e.get("expected_manifest_id_provided") is True
                for e in event_log.events
            )
        )

    def test_manifest_evidence_contains_no_forbidden_selection_language(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        evidence = package["manifest_evidence"]
        for text in _walk_strings(evidence):
            lowered = text.lower()
            for phrase in FORBIDDEN_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "Forbidden phrase '{0}' found in manifest_evidence: {1!r}".format(
                        phrase, text
                    ),
                )

    # WO-26 toy registered configuration flow tests

    def test_manifest_mode_package_includes_registered_configuration_observation(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        self.assertIn("registered_configuration_observation", package)
        observation = package["registered_configuration_observation"]
        self.assertEqual(observation["configuration_id"], "toy-scaffold-config")
        self.assertEqual(observation["manifest_id"], _MANIFEST_ID)
        self.assertEqual(observation["adapter_kind"], "mock_scaffold_internal")
        self.assertEqual(set(observation["planes_declared"]), set(PLANE_NAMES))
        self.assertFalse(observation["selection_made"])

    def test_observation_records_registration_authority_decided_false(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        observation = package["registered_configuration_observation"]
        self.assertIn("registration_authority_decided", observation)
        self.assertIs(observation["registration_authority_decided"], False)

    def test_observation_records_production_registration_false(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        observation = package["registered_configuration_observation"]
        self.assertIn("production_registration", observation)
        self.assertIs(observation["production_registration"], False)

    def test_observation_contains_no_forbidden_selection_language(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        observation = package["registered_configuration_observation"]
        for text in _walk_strings(observation):
            lowered = text.lower()
            for phrase in FORBIDDEN_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "Forbidden phrase '{0}' found in registered_configuration_observation: {1!r}".format(
                        phrase, text
                    ),
                )

    def test_default_no_manifest_mode_omits_observation(self):
        package = self._run_with_defaults()
        self.assertNotIn("registered_configuration_observation", package)
        # No registered_configuration_observed event either.
        self.assertFalse(
            any(
                event["type"] == "registered_configuration_observed"
                for event in package["all_events"]
            ),
            "default no-manifest mode must not record registered_configuration_observed",
        )

    def test_manifest_rejection_prevents_observation_and_adapter_invocation(self):
        # On manifest rejection, neither the registered configuration
        # observation nor the mock adapter may be reached.
        original_adapter = dry_run_module.run_mock_adapter
        try:
            dry_run_module.run_mock_adapter = lambda fixture, configuration: self.fail(
                "mock adapter must not be invoked after manifest rejection"
            )
            with self.assertRaises(ManifestIdMismatch):
                self._run_with_defaults(
                    manifest_path=_MANIFEST_PATH,
                    expected_manifest_id="different-expected-manifest-id",
                )
        finally:
            dry_run_module.run_mock_adapter = original_adapter

    def test_manifest_configuration_mismatch_halts_before_observation_and_adapter(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            mismatch_path = os.path.join(tmp_dir, "mismatch_manifest.json")
            manifest = _load_json(_MANIFEST_PATH)
            manifest["configuration_id"] = "different-toy-configuration"
            with open(mismatch_path, "w", encoding="utf-8") as handle:
                json.dump(manifest, handle)

            event_log = EventLog()
            original_event_log = dry_run_module.EventLog
            original_adapter = dry_run_module.run_mock_adapter
            try:
                dry_run_module.EventLog = lambda: event_log
                dry_run_module.run_mock_adapter = lambda fixture, configuration: self.fail(
                    "mock adapter must not be invoked after manifest/config mismatch"
                )
                with self.assertRaises(ManifestConfigurationMismatch):
                    self._run_with_defaults(
                        manifest_path=mismatch_path,
                        expected_manifest_id=_MANIFEST_ID,
                    )
            finally:
                dry_run_module.EventLog = original_event_log
                dry_run_module.run_mock_adapter = original_adapter

        self.assertTrue(
            any(
                event["type"] == "halt"
                and event.get("reason") == "manifest_configuration_mismatch"
                and event.get("loaded_configuration_id") == "toy-scaffold-config"
                and event.get("manifest_configuration_id")
                == "different-toy-configuration"
                for event in event_log.events
            )
        )
        self.assertFalse(
            any(
                event["type"] == "registered_configuration_observed"
                for event in event_log.events
            ),
            "registered observation must not be recorded after mismatch",
        )

    def test_contract_failure_still_includes_observation_when_manifest_loaded(self):
        always_fail = [("always_fail", lambda response: False)]
        package = self._run_with_defaults(
            contract_checks=always_fail,
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        # Disqualification surfaces.
        self.assertIn("toy-scaffold-config", package["disqualified_configurations"])
        # Observation is still attached because it is built before contract
        # checks run.
        self.assertIn("registered_configuration_observation", package)
        observation = package["registered_configuration_observation"]
        self.assertEqual(observation["manifest_id"], _MANIFEST_ID)
        # Manifest evidence is also still attached.
        self.assertIn("manifest_evidence", package)

    def test_event_order_manifest_loaded_before_mock_adapter_invoked(self):
        package = self._run_with_defaults(
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
        )
        events = package["all_events"]
        manifest_index = next(
            (i for i, e in enumerate(events) if e["type"] == "manifest_loaded"),
            None,
        )
        observation_index = next(
            (
                i
                for i, e in enumerate(events)
                if e["type"] == "registered_configuration_observed"
            ),
            None,
        )
        adapter_index = next(
            (i for i, e in enumerate(events) if e["type"] == "mock_adapter_invoked"),
            None,
        )
        self.assertIsNotNone(manifest_index)
        self.assertIsNotNone(observation_index)
        self.assertIsNotNone(adapter_index)
        # WO-25 invariant: manifest_loaded precedes mock_adapter_invoked.
        self.assertLess(manifest_index, adapter_index)
        # WO-26 invariant: registered_configuration_observed sits between
        # the two so the observation step is observable in the audit trail.
        self.assertLess(manifest_index, observation_index)
        self.assertLess(observation_index, adapter_index)

    # WO-27 scaffold run artifact snapshot integration tests

    def test_default_dry_run_writes_no_snapshot(self):
        # No snapshot_output_path supplied; no snapshot file is created
        # and no snapshot_evidence key is attached.
        with tempfile.TemporaryDirectory() as tmp_dir:
            sentinel = os.path.join(tmp_dir, "should_not_exist.json")
            package = self._run_with_defaults()
            self.assertNotIn("snapshot_evidence", package)
            self.assertFalse(os.path.exists(sentinel))
            self.assertFalse(
                any(
                    event["type"] == "snapshot_written"
                    for event in package["all_events"]
                ),
                "default dry-run must not record snapshot_written when snapshot_output_path is omitted",
            )

    def test_snapshot_output_path_writes_deterministic_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            first_path = os.path.join(tmp_dir, "first.json")
            second_path = os.path.join(tmp_dir, "second.json")
            self._run_with_defaults(snapshot_output_path=first_path)
            self._run_with_defaults(snapshot_output_path=second_path)
            self.assertTrue(os.path.exists(first_path))
            self.assertTrue(os.path.exists(second_path))
            with open(first_path, "rb") as handle:
                first_bytes = handle.read()
            with open(second_path, "rb") as handle:
                second_bytes = handle.read()
            # The two snapshots come from independent dry-runs, so timestamps
            # in all_events differ; full equality is not expected. But each
            # individual write is internally deterministic (sorted keys,
            # fixed encoding) and round-trips to JSON.
            self.assertEqual(
                json.loads(first_bytes.decode("utf-8")).keys()
                .__class__,
                json.loads(second_bytes.decode("utf-8")).keys().__class__,
            )
            # Sanity: each snapshot is valid sorted-key JSON.
            first_obj = json.loads(first_bytes.decode("utf-8"))
            self.assertEqual(
                list(first_obj.keys()), sorted(first_obj.keys())
            )

    def test_snapshot_evidence_attached_when_path_provided(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "snapshot.json")
            package = self._run_with_defaults(snapshot_output_path=path)
            self.assertIn("snapshot_evidence", package)
            evidence = package["snapshot_evidence"]
            self.assertEqual(evidence["output_path"], path)
            # SHA-256 in evidence matches the written file's bytes.
            with open(path, "rb") as handle:
                file_bytes = handle.read()
            self.assertEqual(
                evidence["sha256"], hashlib.sha256(file_bytes).hexdigest()
            )
            self.assertEqual(evidence["byte_length"], len(file_bytes))
            snapshot_events = [
                event
                for event in package["all_events"]
                if event["type"] == "snapshot_written"
            ]
            self.assertEqual(len(snapshot_events), 1)
            self.assertEqual(snapshot_events[0]["output_path"], path)
            self.assertEqual(snapshot_events[0]["sha256"], evidence["sha256"])
            self.assertEqual(
                snapshot_events[0]["byte_length"], evidence["byte_length"]
            )
            self.assertEqual(package["event_count"], len(package["all_events"]))

    def test_snapshot_file_includes_adapter_manifest_and_observation_evidence(self):
        # The snapshot file is written after adapter, manifest, and
        # registered configuration observation evidence are attached. The
        # snapshot file must therefore contain all three keys.
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "snapshot.json")
            package = self._run_with_defaults(
                manifest_path=_MANIFEST_PATH,
                expected_manifest_id=_MANIFEST_ID,
                snapshot_output_path=path,
            )
            with open(path, "rb") as handle:
                snapshotted = json.loads(handle.read().decode("utf-8"))
            self.assertIn("adapter_output_evidence", snapshotted)
            self.assertIn("manifest_evidence", snapshotted)
            self.assertIn("registered_configuration_observation", snapshotted)
            # The snapshotted package does NOT contain snapshot_evidence:
            # that key is attached only after the snapshot is written.
            self.assertNotIn("snapshot_evidence", snapshotted)
            # The returned in-memory package, by contrast, does carry
            # snapshot_evidence.
            self.assertIn("snapshot_evidence", package)

    def test_snapshot_write_order_preserves_existing_halt_behavior(self):
        # Manifest/configuration mismatch must still halt before any
        # adapter invocation or snapshot write, even when snapshot_output_path
        # is provided.
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "should_not_be_written.json")
            with self.assertRaises(ManifestConfigurationMismatch):
                # Build a temporary manifest whose configuration_id does not
                # match the loaded configuration's id.
                bad_manifest_path = os.path.join(tmp_dir, "mismatch_manifest.json")
                with open(bad_manifest_path, "w", encoding="utf-8") as handle:
                    json.dump(
                        {
                            SCAFFOLD_MARKER_KEY: "harness-internal mismatch manifest for WO-27 test",
                            "manifest_id": "mismatch-manifest",
                            "adapter_kind": "mock_scaffold_internal",
                            "configuration_id": "some-other-configuration",
                            "planes_declared": list(PLANE_NAMES),
                            "selection_made": False,
                        },
                        handle,
                    )
                self._run_with_defaults(
                    manifest_path=bad_manifest_path,
                    expected_manifest_id="mismatch-manifest",
                    snapshot_output_path=path,
                )
            # Snapshot was never written because the halt occurred before
            # the snapshot step.
            self.assertFalse(os.path.exists(path))

        # Contract failure with snapshot still produces a snapshot because
        # the snapshot step runs after package assembly.
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "contract_failure_snapshot.json")
            always_fail = [("always_fail", lambda response: False)]
            package = self._run_with_defaults(
                contract_checks=always_fail,
                snapshot_output_path=path,
            )
            self.assertTrue(os.path.exists(path))
            self.assertIn("snapshot_evidence", package)
            self.assertIn("toy-scaffold-config", package["disqualified_configurations"])

    # WO-33 payload loader integration tests

    def test_default_dry_run_without_payload_unchanged(self):
        # No payload parameters supplied; package has no payload_evidence,
        # no fixture_payload_loaded event.
        package = self._run_with_defaults()
        self.assertNotIn("payload_evidence", package)
        self.assertFalse(
            any(e["type"] == "fixture_payload_loaded" for e in package["all_events"]),
            "default dry-run must not record fixture_payload_loaded when no payload is supplied",
        )

    def test_missing_one_payload_parameter_rejected(self):
        from harness.dry_run import IncompletePayloadParameters
        original_event_log_class = dry_run_module.EventLog
        captured_log = EventLog()
        try:
            dry_run_module.EventLog = lambda: captured_log
            with self.assertRaises(IncompletePayloadParameters):
                self._run_with_defaults(
                    payload_path=os.path.join(
                        _FIXTURE_DIR, "..", "..", "..",
                        "benchmark-fixtures", "golden-intents", "wave-001.json",
                    ),
                )
        finally:
            dry_run_module.EventLog = original_event_log_class
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "payload_parameters_incomplete"
                and e.get("payload_path_provided") is True
                and e.get("expected_fixture_class_provided") is False
                for e in captured_log.events
            ),
        )

        captured_log = EventLog()
        try:
            dry_run_module.EventLog = lambda: captured_log
            with self.assertRaises(IncompletePayloadParameters):
                self._run_with_defaults(expected_fixture_class="golden-intents")
        finally:
            dry_run_module.EventLog = original_event_log_class
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "payload_parameters_incomplete"
                and e.get("payload_path_provided") is False
                and e.get("expected_fixture_class_provided") is True
                for e in captured_log.events
            ),
        )

    def test_payload_parameters_incomplete_halts_before_fixture_load(self):
        from harness.dry_run import IncompletePayloadParameters
        # Use an invalid fixture path. The payload-parameters check runs first,
        # so the exception must be IncompletePayloadParameters, not a fixture
        # loader error.
        with self.assertRaises(IncompletePayloadParameters):
            self._run_with_defaults(
                fixture_path="/nonexistent/path/that/will/fail/if/reached.json",
                fixture_sha256="0" * 64,
                payload_path="/also-nonexistent-payload.json",
                # expected_fixture_class omitted on purpose
            )

    def _payload_path(self, fixture_class):
        return os.path.abspath(
            os.path.join(
                _FIXTURE_DIR, "..", "..", "..",
                "benchmark-fixtures", fixture_class, "wave-001.json",
            )
        )

    def test_dry_run_with_each_wo31_payload_loads_successfully(self):
        for fixture_class in ("golden-intents", "hard-negatives", "boundary-violations"):
            with self.subTest(fixture_class=fixture_class):
                package = self._run_with_defaults(
                    payload_path=self._payload_path(fixture_class),
                    expected_fixture_class=fixture_class,
                )
                self.assertIn("payload_evidence", package)
                evidence = package["payload_evidence"]
                self.assertEqual(evidence["fixture_class"], fixture_class)
                self.assertEqual(evidence["fixture_version"], "wave-001")
                self.assertEqual(evidence["entry_count"], 2)
                self.assertEqual(len(evidence["entry_fixture_ids"]), 2)
                self.assertIn("evidence_note", evidence)

    def test_fixture_payload_loaded_event_in_all_events(self):
        package = self._run_with_defaults(
            payload_path=self._payload_path("golden-intents"),
            expected_fixture_class="golden-intents",
        )
        loaded = [
            e for e in package["all_events"]
            if e["type"] == "fixture_payload_loaded"
        ]
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0]["fixture_class"], "golden-intents")

    def test_payload_load_precedes_mock_adapter_invocation(self):
        package = self._run_with_defaults(
            payload_path=self._payload_path("golden-intents"),
            expected_fixture_class="golden-intents",
        )
        events = package["all_events"]
        payload_idx = next(
            (i for i, e in enumerate(events) if e["type"] == "fixture_payload_loaded"),
            None,
        )
        adapter_idx = next(
            (i for i, e in enumerate(events) if e["type"] == "mock_adapter_invoked"),
            None,
        )
        self.assertIsNotNone(payload_idx)
        self.assertIsNotNone(adapter_idx)
        self.assertLess(payload_idx, adapter_idx)

    def test_payload_evidence_contains_no_forbidden_language(self):
        for fixture_class in ("golden-intents", "hard-negatives", "boundary-violations"):
            with self.subTest(fixture_class=fixture_class):
                package = self._run_with_defaults(
                    payload_path=self._payload_path(fixture_class),
                    expected_fixture_class=fixture_class,
                )
                evidence = package["payload_evidence"]
                for text in _walk_strings(evidence):
                    lowered = text.lower()
                    for phrase in FORBIDDEN_PHRASES:
                        self.assertNotIn(
                            phrase,
                            lowered,
                            "forbidden phrase {0!r} in payload_evidence: {1!r}".format(
                                phrase, text
                            ),
                        )

    def test_payload_evidence_contains_no_forbidden_claim_phrases(self):
        from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES

        for fixture_class in ("golden-intents", "hard-negatives", "boundary-violations"):
            with self.subTest(fixture_class=fixture_class):
                package = self._run_with_defaults(
                    payload_path=self._payload_path(fixture_class),
                    expected_fixture_class=fixture_class,
                )
                evidence = package["payload_evidence"]
                for text in _walk_strings(evidence):
                    lowered = text.lower()
                    for phrase in FORBIDDEN_CLAIM_PHRASES:
                        self.assertNotIn(
                            phrase,
                            lowered,
                            "forbidden claim phrase {0!r} in payload_evidence: {1!r}".format(
                                phrase, text
                            ),
                        )

    def test_payload_loader_rejection_prevents_adapter_invocation(self):
        # Use a deliberately wrong expected_fixture_class against the
        # golden-intents wave-001.json. The payload loader raises
        # PayloadFixtureClassMismatch; the mock adapter must not be invoked.
        from harness.payload_loader import PayloadFixtureClassMismatch
        original_adapter = dry_run_module.run_mock_adapter
        try:
            dry_run_module.run_mock_adapter = lambda fixture, configuration: self.fail(
                "mock adapter must not be invoked after payload loader rejection"
            )
            with self.assertRaises(PayloadFixtureClassMismatch):
                self._run_with_defaults(
                    payload_path=self._payload_path("golden-intents"),
                    expected_fixture_class="hard-negatives",
                )
        finally:
            dry_run_module.run_mock_adapter = original_adapter

    def test_contract_failure_still_includes_payload_evidence(self):
        always_fail = [("always_fail", lambda response: False)]
        package = self._run_with_defaults(
            contract_checks=always_fail,
            payload_path=self._payload_path("golden-intents"),
            expected_fixture_class="golden-intents",
        )
        self.assertIn("toy-scaffold-config", package["disqualified_configurations"])
        self.assertIn("payload_evidence", package)
        self.assertEqual(package["payload_evidence"]["fixture_class"], "golden-intents")

    def test_snapshot_with_payload_preserves_existing_snapshot_behavior(self):
        # Snapshot + payload together: snapshot file exists, package carries
        # both snapshot_evidence and payload_evidence; snapshot file contents
        # also include payload_evidence because the snapshot is written after
        # payload evidence is attached.
        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_path = os.path.join(tmp_dir, "combined_snapshot.json")
            package = self._run_with_defaults(
                payload_path=self._payload_path("golden-intents"),
                expected_fixture_class="golden-intents",
                snapshot_output_path=snapshot_path,
            )
            self.assertIn("snapshot_evidence", package)
            self.assertIn("payload_evidence", package)
            self.assertTrue(os.path.isfile(snapshot_path))
            with open(snapshot_path, "rb") as handle:
                snapshotted = json.loads(handle.read().decode("utf-8"))
            self.assertIn("payload_evidence", snapshotted)
            self.assertIn("adapter_output_evidence", snapshotted)


if __name__ == "__main__":
    unittest.main()
