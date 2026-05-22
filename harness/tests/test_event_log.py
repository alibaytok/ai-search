"""Tests for harness.event_log."""

import unittest

from harness.event_log import EventLog


class EventLogTest(unittest.TestCase):
    def test_events_property_does_not_expose_mutable_entries(self):
        log = EventLog()
        log.append("fixture_loaded", path="fixture.json")

        copied_events = log.events
        copied_events[0]["type"] = "halt"
        copied_events[0]["path"] = "mutated.json"

        stored_event = log.events[0]
        self.assertEqual(stored_event["type"], "fixture_loaded")
        self.assertEqual(stored_event["path"], "fixture.json")
        self.assertFalse(log.has_halt())


if __name__ == "__main__":
    unittest.main()
