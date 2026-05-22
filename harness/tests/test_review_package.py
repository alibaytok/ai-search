"""Tests for harness.review_package.

Covers:
- review package does not recommend or rank (clean assembly path)
- review package marks selection_made as False
- the assembler rejects forbidden language anywhere in the package
"""

import unittest

from harness.contract_runner import ContractRunner
from harness.event_log import EventLog
from harness.reproducibility import capture_environment
from harness.review_package import (
    FORBIDDEN_PHRASES,
    ForbiddenLanguageInReviewPackage,
    assemble,
)


class ReviewPackageTest(unittest.TestCase):
    def test_clean_assembly(self):
        log = EventLog()
        runner = ContractRunner(log)
        env = capture_environment(deterministic_seed=7)
        package = assemble(log, runner, env)
        rendered = str(package).lower()
        for phrase in FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase '{0}' found in package".format(phrase),
            )
        self.assertFalse(package["selection_made"])
        self.assertEqual(package["disqualified_configurations"], [])
        self.assertEqual(package["event_count"], 0)

    def test_disqualified_configurations_surface(self):
        log = EventLog()
        runner = ContractRunner(log)
        runner.add_check("always_fail", lambda response: False)
        runner.run("cfg-A", {})
        env = capture_environment(deterministic_seed=1)
        package = assemble(log, runner, env)
        self.assertEqual(package["disqualified_configurations"], ["cfg-A"])
        self.assertFalse(package["selection_made"])

    def test_forbidden_language_rejected(self):
        log = EventLog()
        # Intentionally inject a forbidden phrase via the event log to
        # exercise the safety net. "best" is a forbidden phrase.
        log.append("note", text="best path observed")
        runner = ContractRunner(log)
        env = capture_environment(deterministic_seed=1)
        with self.assertRaises(ForbiddenLanguageInReviewPackage):
            assemble(log, runner, env)


if __name__ == "__main__":
    unittest.main()
