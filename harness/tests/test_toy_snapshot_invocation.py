"""Toy dry-run snapshot invocation protocol test.

Per WO-28 (DC-031): this test exercises `run_toy_dry_run(...)` with the
scaffold-internal toy fixture, toy configuration, toy manifest, and a
temporary snapshot output path, and verifies the assembled package and
the on-disk snapshot file. It is not real benchmark execution, not real
dataset use, not production artifact policy (OQ-056 and OQ-076 remain
OPEN), and not architecture selection.

The test reads only the existing scaffold-internal toy fixtures under
`harness/tests/fixtures/` and writes only to a temporary directory
managed via `tempfile.TemporaryDirectory()`. It reads only
`benchmark-fixtures/` inventory metadata to verify no mutation occurred;
it never consumes fixture payloads or writes under `benchmark-fixtures/`.
It modifies no harness module.
"""

import hashlib
import json
import os
import tempfile
import unittest

from harness.dry_run import run_toy_dry_run
from harness.review_package import FORBIDDEN_PHRASES


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_FIXTURE_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_fixture.json")
_CONFIG_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_config.json")
_MANIFEST_PATH = os.path.join(_FIXTURE_DIR, "toy_retrieval_manifest.json")
_MANIFEST_ID = "toy-scaffold-manifest"
_DETERMINISTIC_SEED = 42


# Project root is two levels above this file: ../../.
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")


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


def _snapshot_inventory(root):
    """Return the sorted list of relative paths under `root` for diffing."""
    if not os.path.isdir(root):
        return []
    entries = []
    for dirpath, dirnames, filenames in os.walk(root):
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            entries.append(os.path.relpath(full, root))
    entries.sort()
    return entries


class ToyDryRunSnapshotInvocationTest(unittest.TestCase):
    def test_toy_dry_run_with_snapshot_writes_expected_artifacts(self):
        fixture_sha256 = _sha256_of_file(_FIXTURE_PATH)
        registered_config = _load_json(_CONFIG_PATH)

        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_output_path = os.path.join(tmp_dir, "toy_snapshot.json")
            package = run_toy_dry_run(
                fixture_path=_FIXTURE_PATH,
                fixture_sha256=fixture_sha256,
                config_path=_CONFIG_PATH,
                registered_config=registered_config,
                deterministic_seed=_DETERMINISTIC_SEED,
                manifest_path=_MANIFEST_PATH,
                expected_manifest_id=_MANIFEST_ID,
                snapshot_output_path=snapshot_output_path,
            )

            # Returned package carries the four evidence keys.
            self.assertIn("adapter_output_evidence", package)
            self.assertIn("manifest_evidence", package)
            self.assertIn("registered_configuration_observation", package)
            self.assertIn("snapshot_evidence", package)

            # Snapshot file exists at the requested path.
            self.assertTrue(
                os.path.isfile(snapshot_output_path),
                "snapshot file must exist at the requested output path",
            )

            with open(snapshot_output_path, "rb") as handle:
                snapshot_bytes = handle.read()

            # snapshot_evidence hash and byte_length match the file content.
            snapshot_evidence = package["snapshot_evidence"]
            self.assertEqual(snapshot_evidence["output_path"], snapshot_output_path)
            self.assertEqual(
                snapshot_evidence["sha256"],
                hashlib.sha256(snapshot_bytes).hexdigest(),
            )
            self.assertEqual(snapshot_evidence["byte_length"], len(snapshot_bytes))

            # all_events contains the expected events.
            event_types = [event["type"] for event in package["all_events"]]
            for required_type in (
                "fixture_loaded",
                "configuration_loaded",
                "manifest_loaded",
                "registered_configuration_observed",
                "mock_adapter_invoked",
                "snapshot_written",
            ):
                self.assertIn(
                    required_type,
                    event_types,
                    "expected '{0}' in package all_events".format(required_type),
                )

            # Event order is the WO-28 expected sequence.
            def _first_index(event_type):
                for index, event in enumerate(package["all_events"]):
                    if event["type"] == event_type:
                        return index
                self.fail("expected event '{0}' in package all_events".format(event_type))

            fixture_idx = _first_index("fixture_loaded")
            configuration_idx = _first_index("configuration_loaded")
            manifest_idx = _first_index("manifest_loaded")
            observation_idx = _first_index("registered_configuration_observed")
            adapter_idx = _first_index("mock_adapter_invoked")
            snapshot_idx = _first_index("snapshot_written")

            self.assertLess(fixture_idx, configuration_idx)
            self.assertLess(configuration_idx, manifest_idx)
            self.assertLess(manifest_idx, observation_idx)
            self.assertLess(observation_idx, adapter_idx)
            self.assertLess(adapter_idx, snapshot_idx)

            # No measurement_recorded event (the toy default checks pass; no
            # disqualification occurs).
            self.assertFalse(
                any(event["type"] == "measurement_recorded" for event in package["all_events"]),
                "scaffold dry-run must not record measurement after a clean run",
            )

            # Package does not select, recommend, rank, declare winner, declare
            # best, or declare production-ready.
            self.assertFalse(package["selection_made"])
            rendered = str(package).lower()
            for phrase in FORBIDDEN_PHRASES:
                self.assertNotIn(
                    phrase,
                    rendered,
                    "forbidden phrase '{0}' found in returned package".format(phrase),
                )

            # The snapshot file on disk does not contain `snapshot_evidence`
            # (that key is attached after the file is written) but the
            # returned in-memory package does.
            snapshotted = json.loads(snapshot_bytes.decode("utf-8"))
            self.assertNotIn("snapshot_evidence", snapshotted)
            self.assertIn("snapshot_evidence", package)

            # The snapshot file does contain adapter, manifest, and registered
            # configuration observation evidence (all attached before the
            # snapshot was written).
            self.assertIn("adapter_output_evidence", snapshotted)
            self.assertIn("manifest_evidence", snapshotted)
            self.assertIn("registered_configuration_observation", snapshotted)

            # Snapshot file contents have no forbidden language either.
            for text in _walk_strings(snapshotted):
                lowered = text.lower()
                for phrase in FORBIDDEN_PHRASES:
                    self.assertNotIn(
                        phrase,
                        lowered,
                        "forbidden phrase '{0}' found in snapshot file: {1!r}".format(
                            phrase, text
                        ),
                    )

    def test_invocation_writes_only_to_temporary_output(self):
        # Capture the benchmark-fixtures inventory before the invocation,
        # invoke the toy dry-run with a tempfile snapshot path, and assert
        # benchmark-fixtures is unchanged afterwards.
        fixture_sha256 = _sha256_of_file(_FIXTURE_PATH)
        registered_config = _load_json(_CONFIG_PATH)

        before_inventory = _snapshot_inventory(_BENCHMARK_FIXTURES_ROOT)

        with tempfile.TemporaryDirectory() as tmp_dir:
            snapshot_output_path = os.path.join(tmp_dir, "toy_snapshot.json")
            run_toy_dry_run(
                fixture_path=_FIXTURE_PATH,
                fixture_sha256=fixture_sha256,
                config_path=_CONFIG_PATH,
                registered_config=registered_config,
                deterministic_seed=_DETERMINISTIC_SEED,
                manifest_path=_MANIFEST_PATH,
                expected_manifest_id=_MANIFEST_ID,
                snapshot_output_path=snapshot_output_path,
            )

            # The snapshot was written under tmp_dir, not under the project's
            # benchmark-fixtures/ directory.
            self.assertTrue(os.path.isfile(snapshot_output_path))
            self.assertTrue(snapshot_output_path.startswith(tmp_dir))
            self.assertFalse(
                snapshot_output_path.startswith(_BENCHMARK_FIXTURES_ROOT),
                "snapshot must not be written under benchmark-fixtures/",
            )

        # tmp_dir is now cleaned up by TemporaryDirectory.__exit__.
        # benchmark-fixtures inventory is unchanged before vs. after.
        after_inventory = _snapshot_inventory(_BENCHMARK_FIXTURES_ROOT)
        self.assertEqual(
            before_inventory,
            after_inventory,
            "benchmark-fixtures/ inventory must be unchanged by the invocation",
        )


if __name__ == "__main__":
    unittest.main()
