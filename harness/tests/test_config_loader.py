"""Tests for harness.config_loader.

Covers:
- configuration match success (in-memory temp file)
- configuration drift halt (in-memory temp file)
- on-disk toy configuration load (uses harness/tests/fixtures/toy_scaffold_config.json)
"""

import json
import os
import tempfile
import unittest

from harness.config_loader import ConfigurationDrift, load_configuration
from harness.event_log import EventLog


def _write_temp_json(content):
    fd, path = tempfile.mkstemp(suffix=".json")
    os.close(fd)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(content, handle)
    return path


class ConfigLoaderTest(unittest.TestCase):
    def test_match_success(self):
        record = {"id": "test-cfg", "params": {"k": 1}}
        path = _write_temp_json(record)
        try:
            log = EventLog()
            loaded = load_configuration(path, record, log)
            self.assertEqual(loaded, record)
            self.assertFalse(log.has_halt())
            self.assertTrue(
                any(event["type"] == "configuration_loaded" for event in log.events)
            )
        finally:
            os.unlink(path)

    def test_drift_halt(self):
        registered = {"id": "test-cfg", "params": {"k": 1}}
        active = {"id": "test-cfg", "params": {"k": 2}}
        path = _write_temp_json(active)
        try:
            log = EventLog()
            with self.assertRaises(ConfigurationDrift):
                load_configuration(path, registered, log)
            self.assertTrue(log.has_halt())
            halt = next(event for event in log.events if event["type"] == "halt")
            self.assertEqual(halt["reason"], "configuration_drift")
        finally:
            os.unlink(path)

    def test_on_disk_toy_configuration_loads(self):
        config_path = os.path.join(
            os.path.dirname(__file__), "fixtures", "toy_scaffold_config.json"
        )
        with open(config_path, "r", encoding="utf-8") as handle:
            registered = json.load(handle)
        log = EventLog()
        loaded = load_configuration(config_path, registered, log)
        self.assertEqual(loaded["id"], "toy-scaffold-config")
        self.assertFalse(log.has_halt())


if __name__ == "__main__":
    unittest.main()
