"""Configuration loader for harness-internal JSON configuration manifests.

Per `ai-search/16-benchmark-harness-scope.md` Section 7: configurations are
read-only and verified against their registered manifest record before
admission. Drift between the active configuration and the registered
record records a halt event and raises ConfigurationDrift. The scaffold
does not silently register new configurations; registration is a
Codex-authorized activity outside the harness.
"""

import json


class ConfigurationDrift(Exception):
    """Raised when an active configuration differs from its registered record."""


def _configuration_identifier(configuration):
    """Return the configuration's identifier if present, otherwise None."""
    if isinstance(configuration, dict):
        return configuration.get("id")
    return None


def load_configuration(active_path, registered_record, event_log):
    """Load a JSON configuration from `active_path` and verify it matches.

    `registered_record` is the previously-registered configuration content
    (typically a dict). On drift, records a halt event in `event_log` and
    raises ConfigurationDrift. On success, records a `configuration_loaded`
    event and returns the parsed configuration. The active configuration
    file is opened read-only.
    """
    with open(active_path, "r", encoding="utf-8") as text_file:
        active = json.load(text_file)
    if active != registered_record:
        event_log.halt(
            "configuration_drift",
            path=active_path,
            configuration_id=_configuration_identifier(active),
        )
        raise ConfigurationDrift(
            "Configuration drift detected at {0}".format(active_path)
        )
    event_log.append(
        "configuration_loaded",
        path=active_path,
        configuration_id=_configuration_identifier(active),
    )
    return active
