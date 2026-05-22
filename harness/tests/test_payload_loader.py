"""Tests for harness.payload_loader.

Per WO-32 (DC-035): the loader admits scaffold-internal synthetic
payload files from `benchmark-fixtures/<class>/wave-001.json` for the
three admitted classes and validates them at boundary level only. These
tests assert successful load for each of the three WO-31 payload files,
event recording on success, and every named rejection path.

The tests use only Python stdlib (`hashlib`, `json`, `os`, `tempfile`,
`unittest`) plus harness-internal imports (`harness.event_log` and
`harness.payload_loader`). They write only inside a
`tempfile.TemporaryDirectory()` and never modify any existing fixture
payload file.
"""

import hashlib
import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import (
    DuplicateEntryFixtureId,
    EmptyOrMissingPayloadEntries,
    ForbiddenClaimInPayload,
    ForbiddenLanguageInPayload,
    InvalidPayloadMarker,
    MalformedPayloadJSON,
    MissingEntryFixtureId,
    MissingEntrySyntheticMarker,
    MissingPlaneSeparationMarkers,
    MissingPayloadFixtureVersion,
    MissingPayloadMarker,
    NonObjectPayload,
    PAYLOAD_MARKER_KEY,
    PayloadFixtureClassMismatch,
    PlaneOverlapInPayload,
    UnknownPlaneNameInPayload,
    VendorMentionInPayload,
    WO_21_PLANE_NAMES,
    load_fixture_payload,
)


_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_FIXTURE_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")

# The on-disk WO-31 payloads. The loader is exercised against each.
_WAVE_001 = (
    (
        "golden-intents",
        os.path.join(_FIXTURE_ROOT, "golden-intents", "wave-001.json"),
    ),
    (
        "hard-negatives",
        os.path.join(_FIXTURE_ROOT, "hard-negatives", "wave-001.json"),
    ),
    (
        "boundary-violations",
        os.path.join(_FIXTURE_ROOT, "boundary-violations", "wave-001.json"),
    ),
)


def _baseline_synthetic_payload():
    """Return a minimal synthetic payload that satisfies every check.

    Used by rejection tests to inject specific violations into a known-good
    starting point.
    """
    return {
        PAYLOAD_MARKER_KEY: (
            "harness-internal synthetic scaffold-internal test payload; "
            "not benchmark evidence"
        ),
        "fixture_class": "golden-intents",
        "fixture_version": "test-version",
        "entries": [
            {
                "fixture_id": "synthetic-entry-A",
                "synthetic_only": True,
                "no_production_user_data": True,
                "purpose": "scaffold-internal synthetic test entry",
                "plane_separation_markers": {
                    "expected_plane": "official_route_results",
                    "forbidden_planes": ["candidate_route_results"],
                },
            },
            {
                "fixture_id": "synthetic-entry-B",
                "synthetic_only": True,
                "no_production_user_data": True,
                "purpose": "scaffold-internal synthetic test entry",
                "plane_separation_markers": {
                    "expected_plane": "official_route_results",
                    "forbidden_planes": ["candidate_route_results"],
                },
            },
        ],
    }


def _sha256_of_file(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        hasher.update(handle.read())
    return hasher.hexdigest()


class SuccessfulLoadTest(unittest.TestCase):
    def test_each_wave_001_payload_loads_successfully(self):
        for fixture_class, path in _WAVE_001:
            with self.subTest(fixture_class=fixture_class, path=path):
                event_log = EventLog()
                payload = load_fixture_payload(path, fixture_class, event_log)
                self.assertEqual(payload["fixture_class"], fixture_class)
                self.assertFalse(event_log.has_halt())

    def test_success_records_fixture_payload_loaded_event(self):
        for fixture_class, path in _WAVE_001:
            with self.subTest(fixture_class=fixture_class, path=path):
                event_log = EventLog()
                payload = load_fixture_payload(path, fixture_class, event_log)
                events = [e for e in event_log.events if e["type"] == "fixture_payload_loaded"]
                self.assertEqual(len(events), 1)
                event = events[0]
                self.assertEqual(event["path"], path)
                self.assertEqual(event["fixture_class"], fixture_class)
                self.assertEqual(event["fixture_version"], payload["fixture_version"])
                self.assertEqual(event["entry_count"], len(payload["entries"]))
                self.assertEqual(
                    event["entry_fixture_ids"],
                    [entry["fixture_id"] for entry in payload["entries"]],
                )

    def test_success_path_does_not_modify_existing_payload_files(self):
        # Hash each on-disk payload before and after, asserting equality.
        before = {path: _sha256_of_file(path) for _, path in _WAVE_001}
        for fixture_class, path in _WAVE_001:
            event_log = EventLog()
            load_fixture_payload(path, fixture_class, event_log)
        after = {path: _sha256_of_file(path) for _, path in _WAVE_001}
        self.assertEqual(before, after)


class RejectionPathTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = self._tmp.name

    def _write_json(self, name, value):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(value, handle)
        return path

    def _write_text(self, name, text):
        path = os.path.join(self.dir, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(text)
        return path

    def _assert_halt(self, event_log, reason):
        self.assertTrue(
            any(
                e["type"] == "halt" and e.get("reason") == reason
                for e in event_log.events
            ),
            "expected halt event with reason {0!r}; got events: {1!r}".format(
                reason, [(e["type"], e.get("reason")) for e in event_log.events]
            ),
        )

    def test_malformed_json_rejected(self):
        path = self._write_text("bad.json", "{ not valid json")
        event_log = EventLog()
        with self.assertRaises(MalformedPayloadJSON):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_malformed_json")

    def test_non_object_json_rejected(self):
        path = self._write_json("list.json", ["not", "an", "object"])
        event_log = EventLog()
        with self.assertRaises(NonObjectPayload):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_non_object")

    def test_missing_marker_rejected(self):
        payload = _baseline_synthetic_payload()
        del payload[PAYLOAD_MARKER_KEY]
        path = self._write_json("no_marker.json", payload)
        event_log = EventLog()
        with self.assertRaises(MissingPayloadMarker):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_missing_marker")

    def test_invalid_marker_non_string_rejected(self):
        payload = _baseline_synthetic_payload()
        payload[PAYLOAD_MARKER_KEY] = 42
        path = self._write_json("bad_marker_type.json", payload)
        event_log = EventLog()
        with self.assertRaises(InvalidPayloadMarker):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_invalid_marker")

    def test_invalid_marker_missing_substring_rejected(self):
        payload = _baseline_synthetic_payload()
        payload[PAYLOAD_MARKER_KEY] = "this marker is missing required parts"
        path = self._write_json("bad_marker_substr.json", payload)
        event_log = EventLog()
        with self.assertRaises(InvalidPayloadMarker):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_invalid_marker")

    def test_fixture_class_mismatch_rejected(self):
        payload = _baseline_synthetic_payload()
        # baseline declares "golden-intents"; pass a different expected class.
        path = self._write_json("class_mismatch.json", payload)
        event_log = EventLog()
        with self.assertRaises(PayloadFixtureClassMismatch):
            load_fixture_payload(path, "hard-negatives", event_log)
        self._assert_halt(event_log, "payload_fixture_class_mismatch")

    def test_missing_fixture_version_rejected(self):
        payload = _baseline_synthetic_payload()
        del payload["fixture_version"]
        path = self._write_json("no_version.json", payload)
        event_log = EventLog()
        with self.assertRaises(MissingPayloadFixtureVersion):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_missing_fixture_version")

    def test_missing_entries_rejected(self):
        payload = _baseline_synthetic_payload()
        del payload["entries"]
        path = self._write_json("no_entries.json", payload)
        event_log = EventLog()
        with self.assertRaises(EmptyOrMissingPayloadEntries):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_empty_or_missing_entries")

    def test_empty_entries_list_rejected(self):
        payload = _baseline_synthetic_payload()
        payload["entries"] = []
        path = self._write_json("empty_entries.json", payload)
        event_log = EventLog()
        with self.assertRaises(EmptyOrMissingPayloadEntries):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_empty_or_missing_entries")

    def test_missing_entry_fixture_id_rejected(self):
        payload = _baseline_synthetic_payload()
        del payload["entries"][0]["fixture_id"]
        path = self._write_json("no_entry_id.json", payload)
        event_log = EventLog()
        with self.assertRaises(MissingEntryFixtureId):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_missing_entry_fixture_id")

    def test_empty_entry_fixture_id_rejected(self):
        payload = _baseline_synthetic_payload()
        payload["entries"][0]["fixture_id"] = "   "
        path = self._write_json("empty_entry_id.json", payload)
        event_log = EventLog()
        with self.assertRaises(MissingEntryFixtureId):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_missing_entry_fixture_id")

    def test_duplicate_entry_fixture_id_rejected(self):
        payload = _baseline_synthetic_payload()
        payload["entries"][1]["fixture_id"] = payload["entries"][0]["fixture_id"]
        path = self._write_json("dup_entry_id.json", payload)
        event_log = EventLog()
        with self.assertRaises(DuplicateEntryFixtureId):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_duplicate_entry_fixture_id")

    def test_missing_entry_synthetic_marker_rejected(self):
        payload = _baseline_synthetic_payload()
        payload["entries"][0]["synthetic_only"] = False
        payload["entries"][0]["no_production_user_data"] = False
        path = self._write_json("no_synth.json", payload)
        event_log = EventLog()
        with self.assertRaises(MissingEntrySyntheticMarker):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_missing_entry_synthetic_marker")

    def test_missing_plane_separation_markers_rejected(self):
        payload = _baseline_synthetic_payload()
        del payload["entries"][0]["plane_separation_markers"]
        path = self._write_json("missing_plane_markers.json", payload)
        event_log = EventLog()
        with self.assertRaises(MissingPlaneSeparationMarkers):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_missing_plane_separation_markers")

    def test_forbidden_selection_language_rejected(self):
        payload = _baseline_synthetic_payload()
        # "best" is a member of FORBIDDEN_PHRASES in harness/review_package.py.
        payload["entries"][0]["operator_note"] = "this is the best test entry"
        path = self._write_json("forbidden_phrase.json", payload)
        event_log = EventLog()
        with self.assertRaises(ForbiddenLanguageInPayload):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_forbidden_language")

    def test_vendor_mention_rejected(self):
        payload = _baseline_synthetic_payload()
        payload["entries"][0]["operator_note"] = "indexed using FAISS as a tripwire test"
        path = self._write_json("vendor.json", payload)
        event_log = EventLog()
        with self.assertRaises(VendorMentionInPayload):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_vendor_mention")

    def test_forbidden_claim_phrase_rejected(self):
        payload = _baseline_synthetic_payload()
        # "architecture choice" is a positive-claim tripwire phrase.
        payload["entries"][0]["operator_note"] = "this entry encodes an architecture choice"
        path = self._write_json("claim.json", payload)
        event_log = EventLog()
        with self.assertRaises(ForbiddenClaimInPayload):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_forbidden_claim")

    def test_unknown_plane_name_rejected(self):
        payload = _baseline_synthetic_payload()
        payload["entries"][0]["plane_separation_markers"] = {
            "expected_plane": "totally_made_up_plane_name",
            "forbidden_planes": ["official_route_results"],
        }
        path = self._write_json("bad_plane.json", payload)
        event_log = EventLog()
        with self.assertRaises(UnknownPlaneNameInPayload):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_unknown_plane_name")

    def test_plane_overlap_rejected(self):
        payload = _baseline_synthetic_payload()
        payload["entries"][0]["plane_separation_markers"] = {
            "expected_plane": "official_route_results",
            "forbidden_planes": [
                "official_route_results",
                "candidate_route_results",
            ],
        }
        path = self._write_json("plane_overlap.json", payload)
        event_log = EventLog()
        with self.assertRaises(PlaneOverlapInPayload):
            load_fixture_payload(path, "golden-intents", event_log)
        self._assert_halt(event_log, "payload_plane_overlap")


class NoFilesystemWriteOnSuccessTest(unittest.TestCase):
    def test_loader_performs_no_filesystem_writes_during_success(self):
        # Patch builtins.open so any write-mode invocation fails the test.
        import builtins
        original_open = builtins.open

        def _guarded_open(file, mode="r", *args, **kwargs):
            normalized_mode = mode if isinstance(mode, str) else ""
            for forbidden_flag in ("w", "a", "x", "+"):
                if forbidden_flag in normalized_mode:
                    self.fail(
                        "loader must not open files for writing during success path; "
                        "open({0!r}, mode={1!r}) attempted".format(file, mode)
                    )
            return original_open(file, mode, *args, **kwargs)

        builtins.open = _guarded_open
        try:
            for fixture_class, path in _WAVE_001:
                event_log = EventLog()
                load_fixture_payload(path, fixture_class, event_log)
        finally:
            builtins.open = original_open


class PlaneNameSetSanityTest(unittest.TestCase):
    def test_wo21_plane_names_constant_matches_known_five(self):
        # Sanity guard against accidental drift of the loader's plane name set.
        self.assertEqual(
            WO_21_PLANE_NAMES,
            frozenset((
                "official_route_results",
                "candidate_route_results",
                "normalized_material_support_results",
                "source_quality_constraint_observations",
                "trace_outcome_signal_observations",
            )),
        )


if __name__ == "__main__":
    unittest.main()
