"""Tests for harness.artifact_snapshot.

Per WO-27 (DC-030): the snapshot writer is scaffold-internal and toy-only.
These tests assert deterministic writing, hash correctness, the named
rejection paths (non-object package and forbidden selection language), and
event-log behavior. No retrieval system, no production artifact contract,
no architecture selection.
"""

import hashlib
import json
import os
import tempfile
import unittest

from harness.artifact_snapshot import (
    ForbiddenLanguageInSnapshotPackage,
    NonObjectSnapshotPackage,
    SnapshotWriteError,
    write_scaffold_snapshot,
)
from harness.event_log import EventLog


def _baseline_package():
    return {
        "summary": "Harness run summary for Codex review.",
        "selection_made": False,
        "selection_note": (
            "Toy package used by harness/tests/test_artifact_snapshot.py; "
            "no configuration is proposed."
        ),
        "adapter_output_evidence": {
            "adapter_kind": "mock_scaffold_internal",
            "selection_made": False,
        },
        "manifest_evidence": {
            "manifest_id": "toy-scaffold-manifest",
            "adapter_kind": "mock_scaffold_internal",
            "selection_made": False,
        },
        "registered_configuration_observation": {
            "configuration_id": "toy-scaffold-config",
            "manifest_id": "toy-scaffold-manifest",
            "registration_authority_decided": False,
            "production_registration": False,
        },
    }


class ArtifactSnapshotTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = self._tmp.name

    def _path(self, name):
        return os.path.join(self.dir, name)

    def test_snapshot_writes_deterministic_json(self):
        package = _baseline_package()
        first_path = self._path("first.json")
        second_path = self._path("second.json")
        write_scaffold_snapshot(package, first_path)
        write_scaffold_snapshot(package, second_path)
        with open(first_path, "rb") as handle:
            first_bytes = handle.read()
        with open(second_path, "rb") as handle:
            second_bytes = handle.read()
        # Byte-for-byte identical for the same logical input.
        self.assertEqual(first_bytes, second_bytes)
        # Keys are JSON-sorted.
        round_trip = json.loads(first_bytes.decode("utf-8"))
        self.assertEqual(round_trip, package)
        decoded_keys = json.loads(first_bytes.decode("utf-8")).keys()
        self.assertEqual(list(decoded_keys), sorted(round_trip.keys()))

    def test_returned_hash_matches_file_content(self):
        package = _baseline_package()
        path = self._path("snapshot.json")
        metadata = write_scaffold_snapshot(package, path)
        with open(path, "rb") as handle:
            file_bytes = handle.read()
        self.assertEqual(metadata["output_path"], path)
        self.assertEqual(metadata["sha256"], hashlib.sha256(file_bytes).hexdigest())
        self.assertEqual(metadata["byte_length"], len(file_bytes))

    def test_event_log_records_snapshot_written_on_success(self):
        package = _baseline_package()
        path = self._path("snapshot.json")
        event_log = EventLog()
        metadata = write_scaffold_snapshot(package, path, event_log=event_log)
        events = [e for e in event_log.events if e["type"] == "snapshot_written"]
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["output_path"], path)
        self.assertEqual(event["sha256"], metadata["sha256"])
        self.assertEqual(event["byte_length"], metadata["byte_length"])
        self.assertFalse(event_log.has_halt())

    def test_forbidden_language_in_package_rejected(self):
        package = _baseline_package()
        # 'best' is a member of FORBIDDEN_PHRASES in harness/review_package.py.
        package["operator_note"] = "This is the best configuration to ship."
        path = self._path("forbidden.json")
        event_log = EventLog()
        with self.assertRaises(ForbiddenLanguageInSnapshotPackage):
            write_scaffold_snapshot(package, path, event_log=event_log)
        # No file written.
        self.assertFalse(os.path.exists(path))
        # Halt event recorded.
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "snapshot_forbidden_language"
                for e in event_log.events
            )
        )

    def test_non_object_package_rejected(self):
        path = self._path("non_object.json")
        event_log = EventLog()
        with self.assertRaises(NonObjectSnapshotPackage):
            write_scaffold_snapshot(["this", "is", "a", "list"], path, event_log=event_log)
        self.assertFalse(os.path.exists(path))
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "snapshot_non_object_package"
                for e in event_log.events
            )
        )

    def test_unwritable_path_raises_snapshot_write_error(self):
        # An output path inside a non-existent directory cannot be written
        # because the writer does not create parent directories. This
        # exercises the SnapshotWriteError path without any directory
        # policy assumption.
        bad_path = os.path.join(self.dir, "nonexistent_subdir", "snapshot.json")
        event_log = EventLog()
        with self.assertRaises(SnapshotWriteError):
            write_scaffold_snapshot(_baseline_package(), bad_path, event_log=event_log)
        self.assertTrue(
            any(
                e["type"] == "halt" and e.get("reason") == "snapshot_write_error"
                for e in event_log.events
            )
        )


if __name__ == "__main__":
    unittest.main()
