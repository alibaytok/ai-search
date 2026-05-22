"""Tests for harness.manifest_loader.

Per WO-24 (DC-027): the manifest loader admits a scaffold-internal toy
manifest only. These tests assert successful load, manifest-loaded event
recording, and every named rejection path (missing scaffold marker,
missing required field, manifest id mismatch, non-object JSON, malformed
JSON, forbidden selection language, and selection_made=true). The
on-disk toy manifest is also exercised to confirm it admits cleanly.
"""

import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.manifest_loader import (
    ForbiddenLanguageInManifest,
    MalformedManifestJSON,
    ManifestDeclaresSelection,
    ManifestIdMismatch,
    MissingManifestScaffoldMarker,
    MissingRequiredManifestField,
    NonObjectManifest,
    REQUIRED_FIELDS,
    SCAFFOLD_MARKER_KEY,
    load_manifest,
)


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_TOY_MANIFEST_PATH = os.path.join(_FIXTURE_DIR, "toy_retrieval_manifest.json")
_TOY_MANIFEST_ID = "toy-scaffold-manifest"


def _baseline_manifest():
    return {
        SCAFFOLD_MARKER_KEY: "harness-internal test manifest; not a real retrieval configuration manifest",
        "manifest_id": "synthetic-toy-manifest",
        "adapter_kind": "mock_scaffold_internal",
        "configuration_id": "synthetic-toy-configuration",
        "planes_declared": [
            "official_route_results",
            "candidate_route_results",
            "normalized_material_support_results",
            "source_quality_constraint_observations",
            "trace_outcome_signal_observations",
        ],
        "selection_made": False,
    }


def _write_json(path, value):
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(value, handle)


def _write_text(path, text):
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


class ManifestLoaderTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = self._tmp.name

    def _path(self, name):
        return os.path.join(self.dir, name)

    def test_successful_load_returns_manifest(self):
        path = self._path("ok.json")
        manifest = _baseline_manifest()
        _write_json(path, manifest)
        event_log = EventLog()
        loaded = load_manifest(path, manifest["manifest_id"], event_log)
        self.assertEqual(loaded, manifest)

    def test_manifest_loaded_event_recorded(self):
        path = self._path("ok.json")
        manifest = _baseline_manifest()
        _write_json(path, manifest)
        event_log = EventLog()
        load_manifest(path, manifest["manifest_id"], event_log)
        events = event_log.events
        loaded_events = [e for e in events if e["type"] == "manifest_loaded"]
        self.assertEqual(len(loaded_events), 1)
        event = loaded_events[0]
        self.assertEqual(event["manifest_id"], manifest["manifest_id"])
        self.assertEqual(event["adapter_kind"], manifest["adapter_kind"])
        self.assertEqual(event["configuration_id"], manifest["configuration_id"])
        self.assertEqual(event["planes_declared"], manifest["planes_declared"])
        # No halt events are recorded on the success path.
        self.assertFalse(event_log.has_halt())

    def test_missing_scaffold_marker_rejected(self):
        path = self._path("no_marker.json")
        manifest = _baseline_manifest()
        del manifest[SCAFFOLD_MARKER_KEY]
        _write_json(path, manifest)
        event_log = EventLog()
        with self.assertRaises(MissingManifestScaffoldMarker):
            load_manifest(path, manifest["manifest_id"], event_log)
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "manifest_missing_scaffold_marker"
                for e in event_log.events
            )
        )

    def test_invalid_scaffold_marker_rejected(self):
        path = self._path("bad_marker.json")
        manifest = _baseline_manifest()
        manifest[SCAFFOLD_MARKER_KEY] = ""
        _write_json(path, manifest)
        event_log = EventLog()
        with self.assertRaises(MissingManifestScaffoldMarker):
            load_manifest(path, manifest["manifest_id"], event_log)
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "manifest_missing_scaffold_marker"
                for e in event_log.events
            )
        )

    def test_missing_required_field_rejected(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(missing=field):
                path = self._path("missing_{0}.json".format(field))
                manifest = _baseline_manifest()
                del manifest[field]
                _write_json(path, manifest)
                event_log = EventLog()
                with self.assertRaises(MissingRequiredManifestField):
                    load_manifest(path, manifest.get("manifest_id", "x"), event_log)
                halts = [e for e in event_log.events if e["type"] == "halt"]
                self.assertTrue(
                    any(
                        h.get("reason") == "manifest_missing_required_field"
                        and h.get("missing_field") == field
                        for h in halts
                    ),
                    "expected halt for missing field '{0}'".format(field),
                )

    def test_manifest_id_mismatch_rejected(self):
        path = self._path("wrong_id.json")
        manifest = _baseline_manifest()
        _write_json(path, manifest)
        event_log = EventLog()
        with self.assertRaises(ManifestIdMismatch):
            load_manifest(path, "different-expected-id", event_log)
        self.assertTrue(
            any(
                e["type"] == "halt" and e.get("reason") == "manifest_id_mismatch"
                for e in event_log.events
            )
        )

    def test_non_object_json_rejected(self):
        path = self._path("list.json")
        _write_json(path, ["this", "is", "a", "list"])
        event_log = EventLog()
        with self.assertRaises(NonObjectManifest):
            load_manifest(path, "x", event_log)
        self.assertTrue(
            any(
                e["type"] == "halt" and e.get("reason") == "manifest_non_object"
                for e in event_log.events
            )
        )

    def test_malformed_json_rejected(self):
        path = self._path("malformed.json")
        _write_text(path, "{ not valid json")
        event_log = EventLog()
        with self.assertRaises(MalformedManifestJSON):
            load_manifest(path, "x", event_log)
        self.assertTrue(
            any(
                e["type"] == "halt" and e.get("reason") == "manifest_malformed_json"
                for e in event_log.events
            )
        )

    def test_forbidden_selection_language_rejected(self):
        path = self._path("forbidden.json")
        manifest = _baseline_manifest()
        # Inject a forbidden phrase into a free-text manifest field. The
        # phrase 'best' is a member of FORBIDDEN_PHRASES in
        # harness/review_package.py.
        manifest["operator_note"] = "This is the best configuration."
        _write_json(path, manifest)
        event_log = EventLog()
        with self.assertRaises(ForbiddenLanguageInManifest):
            load_manifest(path, manifest["manifest_id"], event_log)
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "manifest_forbidden_language"
                for e in event_log.events
            )
        )

    def test_selection_made_true_rejected(self):
        path = self._path("selection_true.json")
        manifest = _baseline_manifest()
        manifest["selection_made"] = True
        _write_json(path, manifest)
        event_log = EventLog()
        with self.assertRaises(ManifestDeclaresSelection):
            load_manifest(path, manifest["manifest_id"], event_log)
        self.assertTrue(
            any(
                e["type"] == "halt"
                and e.get("reason") == "manifest_declares_selection"
                for e in event_log.events
            )
        )

    def test_on_disk_toy_manifest_loads_successfully(self):
        event_log = EventLog()
        loaded = load_manifest(_TOY_MANIFEST_PATH, _TOY_MANIFEST_ID, event_log)
        self.assertEqual(loaded["manifest_id"], _TOY_MANIFEST_ID)
        self.assertEqual(loaded["adapter_kind"], "mock_scaffold_internal")
        self.assertFalse(loaded["selection_made"])
        self.assertIn(SCAFFOLD_MARKER_KEY, loaded)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, loaded)
        # planes_declared lists the five WO-21 planes.
        self.assertEqual(
            set(loaded["planes_declared"]),
            {
                "official_route_results",
                "candidate_route_results",
                "normalized_material_support_results",
                "source_quality_constraint_observations",
                "trace_outcome_signal_observations",
            },
        )
        # Event log records exactly one manifest_loaded event and no halts.
        events = event_log.events
        self.assertEqual(
            sum(1 for e in events if e["type"] == "manifest_loaded"), 1
        )
        self.assertFalse(event_log.has_halt())


if __name__ == "__main__":
    unittest.main()
