"""Tests for harness.fixture_loader.

Covers:
- fixture hash success (in-memory temp file)
- fixture hash mismatch halt (in-memory temp file)
- on-disk toy fixture load (uses harness/tests/fixtures/toy_scaffold_fixture.json)
"""

import hashlib
import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.fixture_loader import FixtureHashMismatch, load_fixture


def _write_temp_json(content):
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(content, handle)
    return path


def _sha256_of_file(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        hasher.update(handle.read())
    return hasher.hexdigest()


class FixtureLoaderTest(unittest.TestCase):
    def test_hash_success(self):
        path = _write_temp_json({"_fixture_marker": "test", "k": "v"})
        try:
            expected = _sha256_of_file(path)
            log = EventLog()
            data = load_fixture(path, expected, log)
            self.assertEqual(data["k"], "v")
            self.assertFalse(log.has_halt())
            self.assertTrue(any(event["type"] == "fixture_loaded" for event in log.events))
        finally:
            os.unlink(path)

    def test_hash_mismatch_halt(self):
        path = _write_temp_json({"_fixture_marker": "test", "k": "v"})
        try:
            wrong_hash = "0" * 64
            log = EventLog()
            with self.assertRaises(FixtureHashMismatch):
                load_fixture(path, wrong_hash, log)
            self.assertTrue(log.has_halt())
            halt = next(event for event in log.events if event["type"] == "halt")
            self.assertEqual(halt["reason"], "fixture_hash_mismatch")
        finally:
            os.unlink(path)

    def test_on_disk_toy_fixture_loads(self):
        fixture_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "toy_scaffold_fixture.json"
        )
        expected = _sha256_of_file(fixture_path)
        log = EventLog()
        data = load_fixture(fixture_path, expected, log)
        self.assertIn("_fixture_marker", data)
        self.assertFalse(log.has_halt())


if __name__ == "__main__":
    unittest.main()
