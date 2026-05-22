"""Tests for harness.reproducibility.

Covers:
- reproducibility capture includes required scaffold fields
- fixture hashes accumulate as expected
- configuration identifiers deduplicate by appearance
"""

import unittest

from harness.reproducibility import (
    REQUIRED_FIELDS,
    add_configuration_identifier,
    add_fixture_hash,
    capture_environment,
)


class ReproducibilityTest(unittest.TestCase):
    def test_capture_includes_required_fields(self):
        env = capture_environment(deterministic_seed=42)
        for field in REQUIRED_FIELDS:
            self.assertIn(field, env, "missing required field: {0}".format(field))
        self.assertEqual(env["deterministic_seed"], 42)
        self.assertIsInstance(env["python_version"], str)
        self.assertIsInstance(env["platform"], str)
        self.assertIsInstance(env["scaffold_version"], str)
        self.assertIsInstance(env["fixture_hashes"], dict)
        self.assertIsInstance(env["configuration_identifiers"], list)

    def test_add_fixture_hash(self):
        env = capture_environment(deterministic_seed=1)
        sample_hash = "abcd" * 16
        add_fixture_hash(env, "f.json", sample_hash)
        self.assertEqual(env["fixture_hashes"]["f.json"], sample_hash)

    def test_add_configuration_identifier_dedup(self):
        env = capture_environment(deterministic_seed=1)
        add_configuration_identifier(env, "cfg-A")
        add_configuration_identifier(env, "cfg-A")
        add_configuration_identifier(env, "cfg-B")
        self.assertEqual(env["configuration_identifiers"], ["cfg-A", "cfg-B"])


if __name__ == "__main__":
    unittest.main()
