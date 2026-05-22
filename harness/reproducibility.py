"""Reproducibility evidence capture for harness runs.

Per `ai-search/16-benchmark-harness-scope.md` Section 10 and DC-020: the
scaffold records deterministic seeds, runtime and platform identification,
its own scaffold version, fixture content hashes, and configuration
identifiers consumed by the run. The substantive content of an
environment snapshot for production use is owned by Codex (OQ-070); the
fields captured here satisfy the first-scaffold minimum.
"""

import platform
import sys

from harness import __version__ as _scaffold_version


REQUIRED_FIELDS = (
    "python_version",
    "platform",
    "deterministic_seed",
    "scaffold_version",
    "fixture_hashes",
    "configuration_identifiers",
)


def capture_environment(deterministic_seed):
    """Return the base environment snapshot for a harness run.

    The returned dict carries the required fields named in REQUIRED_FIELDS.
    Fixture hashes and configuration identifiers are empty at capture time
    and are populated through add_fixture_hash and add_configuration_identifier.
    """
    return {
        "python_version": sys.version,
        "platform": platform.platform(),
        "deterministic_seed": deterministic_seed,
        "scaffold_version": _scaffold_version,
        "fixture_hashes": {},
        "configuration_identifiers": [],
    }


def add_fixture_hash(environment, fixture_name, sha256_hex):
    """Record a loaded fixture's SHA-256 hash in the environment snapshot."""
    environment["fixture_hashes"][fixture_name] = sha256_hex


def add_configuration_identifier(environment, configuration_id):
    """Record a loaded configuration identifier; deduplicated by appearance."""
    if configuration_id not in environment["configuration_identifiers"]:
        environment["configuration_identifiers"].append(configuration_id)
