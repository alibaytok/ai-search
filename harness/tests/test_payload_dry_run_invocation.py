"""Payload-mode toy dry-run invocation protocol test.

Per WO-34 (DC-037 if needed): this test exercises `run_toy_dry_run(...)`
end-to-end across all three admitted first-wave payload classes
(`golden-intents`, `hard-negatives`, `boundary-violations`) with the
scaffold-internal toy fixture, toy configuration, toy manifest, the
matching `benchmark-fixtures/<class>/wave-001.json` payload, and a
temporary snapshot output path. It verifies the returned review package
and the on-disk snapshot file at every boundary already locked under
WO-19 / WO-23 / WO-25 / WO-26 / WO-27 / WO-33.

This is not real benchmark execution, not metric collection, not
scoring, not validation evidence (OQ-076 remains OPEN), not run
artifact retention or storage policy (OQ-056 remains OPEN), and not
architecture selection.

The test reads only existing files (scaffold-internal toy fixtures
under `harness/tests/fixtures/`, the three WO-31 payload files under
`benchmark-fixtures/`, and `benchmark-fixtures/README.md` for the
inventory baseline). It writes only inside a
`tempfile.TemporaryDirectory()`. It modifies no harness module and no
existing fixture file.
"""

import hashlib
import json
import os
import tempfile
import unittest

from harness.dry_run import run_toy_dry_run
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_FIXTURE_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_fixture.json")
_CONFIG_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_config.json")
_MANIFEST_PATH = os.path.join(_FIXTURE_DIR, "toy_retrieval_manifest.json")
_MANIFEST_ID = "toy-scaffold-manifest"
_DETERMINISTIC_SEED = 42


# Project root is two levels above this file (harness/tests/ -> harness/ ->
# project root).
_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")

ADMITTED_CLASSES = (
    "golden-intents",
    "hard-negatives",
    "boundary-violations",
)


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


def _payload_path_for(fixture_class):
    return os.path.join(_BENCHMARK_FIXTURES_ROOT, fixture_class, "wave-001.json")


def _inventory_and_hashes(root):
    """Return a dict mapping each relative path under `root` to its SHA-256.

    Used to assert that benchmark-fixtures/ contents are unchanged before
    vs. after the WO-34 invocations.
    """
    if not os.path.isdir(root):
        return {}
    result = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, root)
            result[rel] = _sha256_of_file(full)
    return result


def _first_index(events, event_type):
    for index, event in enumerate(events):
        if event["type"] == event_type:
            return index
    return None


class PayloadModeDryRunInvocationTest(unittest.TestCase):
    def _invoke_one_class(self, fixture_class, snapshot_output_path):
        fixture_sha256 = _sha256_of_file(_FIXTURE_PATH)
        registered_config = _load_json(_CONFIG_PATH)
        payload_path = _payload_path_for(fixture_class)
        return run_toy_dry_run(
            fixture_path=_FIXTURE_PATH,
            fixture_sha256=fixture_sha256,
            config_path=_CONFIG_PATH,
            registered_config=registered_config,
            deterministic_seed=_DETERMINISTIC_SEED,
            manifest_path=_MANIFEST_PATH,
            expected_manifest_id=_MANIFEST_ID,
            payload_path=payload_path,
            expected_fixture_class=fixture_class,
            snapshot_output_path=snapshot_output_path,
        )

    def test_payload_mode_invocation_across_admitted_classes(self):
        for fixture_class in ADMITTED_CLASSES:
            with self.subTest(fixture_class=fixture_class):
                with tempfile.TemporaryDirectory() as tmp_dir:
                    snapshot_path = os.path.join(
                        tmp_dir, "{0}-snapshot.json".format(fixture_class)
                    )
                    package = self._invoke_one_class(fixture_class, snapshot_path)

                    # Package carries the five expected evidence keys.
                    self.assertIn("adapter_output_evidence", package)
                    self.assertIn("manifest_evidence", package)
                    self.assertIn("registered_configuration_observation", package)
                    self.assertIn("payload_evidence", package)
                    self.assertIn("snapshot_evidence", package)

                    # payload_evidence identifies the class correctly.
                    payload_evidence = package["payload_evidence"]
                    self.assertEqual(payload_evidence["fixture_class"], fixture_class)
                    self.assertEqual(payload_evidence["entry_count"], 2)
                    self.assertEqual(len(payload_evidence["entry_fixture_ids"]), 2)

                    # all_events contains fixture_payload_loaded.
                    events = package["all_events"]
                    event_types = [e["type"] for e in events]
                    self.assertIn("fixture_payload_loaded", event_types)
                    self.assertIn("registered_configuration_observed", event_types)
                    self.assertIn("mock_adapter_invoked", event_types)
                    self.assertIn("snapshot_written", event_types)

                    # Event ordering: observed < payload-loaded < adapter <
                    # snapshot.
                    observation_idx = _first_index(events, "registered_configuration_observed")
                    payload_idx = _first_index(events, "fixture_payload_loaded")
                    adapter_idx = _first_index(events, "mock_adapter_invoked")
                    snapshot_idx = _first_index(events, "snapshot_written")
                    self.assertIsNotNone(observation_idx)
                    self.assertIsNotNone(payload_idx)
                    self.assertIsNotNone(adapter_idx)
                    self.assertIsNotNone(snapshot_idx)
                    self.assertLess(observation_idx, payload_idx)
                    self.assertLess(payload_idx, adapter_idx)
                    self.assertLess(adapter_idx, snapshot_idx)

                    # No measurement_recorded event (clean run; no contract
                    # disqualification).
                    self.assertFalse(
                        any(e["type"] == "measurement_recorded" for e in events),
                        "payload-mode dry-run must not record measurement on a clean run",
                    )

                    # Package does not contain selection / recommendation /
                    # ranking / winner / best / production-ready claims.
                    self.assertFalse(package["selection_made"])
                    rendered = str(package).lower()
                    for phrase in FORBIDDEN_PHRASES:
                        self.assertNotIn(
                            phrase,
                            rendered,
                            "forbidden phrase '{0}' found in returned package".format(phrase),
                        )

                    # payload_evidence carries no FORBIDDEN_CLAIM_PHRASES
                    # phrase (validation / trust / benchmark-result /
                    # production-readiness / architecture-selection claims).
                    for text in _walk_strings(payload_evidence):
                        lowered = text.lower()
                        for phrase in FORBIDDEN_CLAIM_PHRASES:
                            self.assertNotIn(
                                phrase,
                                lowered,
                                "forbidden claim phrase '{0}' found in payload_evidence: {1!r}".format(
                                    phrase, text
                                ),
                            )

                    # Snapshot file exists; SHA-256 and byte_length match
                    # snapshot_evidence.
                    self.assertTrue(
                        os.path.isfile(snapshot_path),
                        "snapshot file must exist at {0!r}".format(snapshot_path),
                    )
                    with open(snapshot_path, "rb") as handle:
                        snapshot_bytes = handle.read()
                    snapshot_evidence = package["snapshot_evidence"]
                    self.assertEqual(snapshot_evidence["output_path"], snapshot_path)
                    self.assertEqual(
                        snapshot_evidence["sha256"],
                        hashlib.sha256(snapshot_bytes).hexdigest(),
                    )
                    self.assertEqual(
                        snapshot_evidence["byte_length"], len(snapshot_bytes)
                    )

                    # The on-disk snapshot file contains payload_evidence
                    # because payload evidence is attached before snapshot
                    # writing. The snapshot file does not contain
                    # snapshot_evidence because that key is attached only
                    # after the file is written.
                    snapshotted = json.loads(snapshot_bytes.decode("utf-8"))
                    self.assertIn("payload_evidence", snapshotted)
                    self.assertNotIn("snapshot_evidence", snapshotted)


class PayloadModeDryRunNoMutationTest(unittest.TestCase):
    def test_three_invocations_do_not_mutate_benchmark_fixtures(self):
        before = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        for fixture_class in ADMITTED_CLASSES:
            with tempfile.TemporaryDirectory() as tmp_dir:
                snapshot_path = os.path.join(
                    tmp_dir, "{0}-snapshot.json".format(fixture_class)
                )
                fixture_sha256 = _sha256_of_file(_FIXTURE_PATH)
                registered_config = _load_json(_CONFIG_PATH)
                payload_path = _payload_path_for(fixture_class)
                package = run_toy_dry_run(
                    fixture_path=_FIXTURE_PATH,
                    fixture_sha256=fixture_sha256,
                    config_path=_CONFIG_PATH,
                    registered_config=registered_config,
                    deterministic_seed=_DETERMINISTIC_SEED,
                    manifest_path=_MANIFEST_PATH,
                    expected_manifest_id=_MANIFEST_ID,
                    payload_path=payload_path,
                    expected_fixture_class=fixture_class,
                    snapshot_output_path=snapshot_path,
                )
                # Snapshot is written under the temporary directory, not
                # under benchmark-fixtures/.
                self.assertTrue(os.path.isfile(snapshot_path))
                self.assertTrue(snapshot_path.startswith(tmp_dir))
                self.assertFalse(
                    snapshot_path.startswith(_BENCHMARK_FIXTURES_ROOT),
                    "snapshot must not be written under benchmark-fixtures/",
                )
                # Sanity: the returned package's snapshot_evidence path
                # equals the temp path.
                self.assertEqual(
                    package["snapshot_evidence"]["output_path"], snapshot_path
                )
        after = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        # Inventory (relative-path set) is unchanged.
        self.assertEqual(
            set(before.keys()),
            set(after.keys()),
            "benchmark-fixtures/ inventory must be unchanged by the invocations",
        )
        # Each file's SHA-256 is unchanged.
        for rel in sorted(before.keys()):
            self.assertEqual(
                before[rel],
                after[rel],
                "benchmark-fixtures/{0} SHA-256 must be unchanged by the invocations".format(rel),
            )


if __name__ == "__main__":
    unittest.main()
