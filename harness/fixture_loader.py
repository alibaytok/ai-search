"""Fixture loader for harness-internal JSON fixtures.

Per `ai-search/16-benchmark-harness-scope.md` Section 6 and DC-020: fixtures
are read-only and verified by SHA-256 content hash before admission. Hash
mismatch records a halt event and raises FixtureHashMismatch. The scaffold
never mutates fixture files. Fixtures consumed here are harness-internal
test fixtures only; no real benchmark dataset is loaded by the scaffold.
"""

import hashlib
import json


class FixtureHashMismatch(Exception):
    """Raised when a fixture's SHA-256 hash does not match the expected value."""


def _compute_sha256(path):
    """Compute the SHA-256 hash of the file at the given path."""
    hasher = hashlib.sha256()
    with open(path, "rb") as binary_file:
        for chunk in iter(lambda: binary_file.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def load_fixture(path, expected_sha256, event_log):
    """Load a JSON fixture from `path` after verifying its SHA-256 hash.

    On hash mismatch, records a halt event in `event_log` and raises
    FixtureHashMismatch. On success, records a `fixture_loaded` event and
    returns the parsed JSON content. The fixture file is opened read-only
    and is never mutated by this function.
    """
    actual = _compute_sha256(path)
    if actual != expected_sha256:
        event_log.halt(
            "fixture_hash_mismatch",
            path=path,
            expected_sha256=expected_sha256,
            actual_sha256=actual,
        )
        raise FixtureHashMismatch(
            "Fixture hash mismatch for {0}: expected {1}, got {2}".format(
                path, expected_sha256, actual
            )
        )
    event_log.append("fixture_loaded", path=path, sha256=actual)
    with open(path, "r", encoding="utf-8") as text_file:
        return json.load(text_file)
