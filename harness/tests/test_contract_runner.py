"""Tests for harness.contract_runner.

Covers:
- contract pass
- contract failure halts measurement for that configuration
- attempting to record a measurement after disqualification raises
"""

import unittest

from harness.contract_runner import ContractRunner, MeasurementAfterDisqualification
from harness.event_log import EventLog


def _no_raw_internet(response):
    return "raw_internet_content" not in response


def _has_route_id(response):
    return "route_id" in response


class ContractRunnerTest(unittest.TestCase):
    def test_contract_pass(self):
        log = EventLog()
        runner = ContractRunner(log)
        runner.add_check("no_raw_internet", _no_raw_internet)
        runner.add_check("has_route_id", _has_route_id)
        passed = runner.run("cfg-A", {"route_id": "rt-1"})
        self.assertTrue(passed)
        self.assertFalse(runner.is_disqualified("cfg-A"))
        pass_events = [event for event in log.events if event["type"] == "contract_check_pass"]
        self.assertEqual(len(pass_events), 2)
        self.assertFalse(log.has_halt())

    def test_contract_failure_halts_measurement(self):
        log = EventLog()
        runner = ContractRunner(log)
        runner.add_check("no_raw_internet", _no_raw_internet)
        passed = runner.run(
            "cfg-A", {"raw_internet_content": "should not appear here"}
        )
        self.assertFalse(passed)
        self.assertTrue(runner.is_disqualified("cfg-A"))
        self.assertTrue(log.has_halt())
        halt = next(event for event in log.events if event["type"] == "halt")
        self.assertEqual(halt["reason"], "contract_check_failed")
        with self.assertRaises(MeasurementAfterDisqualification):
            runner.record_measurement("cfg-A", "quality", {"score": 0.9})

    def test_subsequent_run_against_disqualified_configuration_raises(self):
        log = EventLog()
        runner = ContractRunner(log)
        runner.add_check("no_raw_internet", _no_raw_internet)
        runner.run("cfg-A", {"raw_internet_content": "x"})
        self.assertTrue(runner.is_disqualified("cfg-A"))
        with self.assertRaises(MeasurementAfterDisqualification):
            runner.run("cfg-A", {"route_id": "rt-2"})


if __name__ == "__main__":
    unittest.main()
