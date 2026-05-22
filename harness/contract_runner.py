"""Contract test runner for harness-internal scaffold contract checks.

Per `ai-search/16-benchmark-harness-scope.md` Section 8 and DC-020 halt
behavior: each contract check is pass/fail. A failure disqualifies the
configuration for the run. No quality, performance, or operational
measurement against the disqualified configuration is permitted afterward
in the same run. The contract check set registered here is scaffold-
internal and illustrative; real benchmark contract checks are
Codex-authorized and outside WO-18's scope.
"""


class MeasurementAfterDisqualification(Exception):
    """Raised when measurement is attempted against a disqualified configuration."""


class ContractRunner:
    """Run a set of contract checks against configuration responses.

    A check is a callable `check_fn(response)` returning True for pass or
    False for failure. Checks are run in registration order; on the first
    failure, the configuration is marked disqualified and the runner
    records a halt event without running the remaining checks.
    """

    def __init__(self, event_log):
        self._event_log = event_log
        self._checks = []
        self._disqualified = set()

    def add_check(self, name, check_fn):
        """Register a contract check."""
        self._checks.append((name, check_fn))

    def run(self, configuration_id, response):
        """Run all checks against `response` for `configuration_id`.

        Returns True if all registered checks pass. On the first failure,
        records a halt event, marks the configuration disqualified, and
        returns False without running the remaining checks. Raises
        MeasurementAfterDisqualification if `configuration_id` was already
        disqualified before this call.
        """
        if configuration_id in self._disqualified:
            self._event_log.halt(
                "measurement_after_disqualification",
                configuration_id=configuration_id,
            )
            raise MeasurementAfterDisqualification(
                "Configuration {0} is already disqualified".format(configuration_id)
            )
        for name, check_fn in self._checks:
            passed = bool(check_fn(response))
            if passed:
                self._event_log.append(
                    "contract_check_pass",
                    configuration_id=configuration_id,
                    check_name=name,
                )
            else:
                self._event_log.halt(
                    "contract_check_failed",
                    configuration_id=configuration_id,
                    check_name=name,
                )
                self._disqualified.add(configuration_id)
                return False
        return True

    def is_disqualified(self, configuration_id):
        """Return True if `configuration_id` is disqualified for the run."""
        return configuration_id in self._disqualified

    def disqualified_configurations(self):
        """Return a sorted list of disqualified configuration identifiers."""
        return sorted(self._disqualified)

    def record_measurement(self, configuration_id, measurement_kind, payload):
        """Record a measurement event against a configuration.

        Raises MeasurementAfterDisqualification if the configuration was
        previously disqualified by a contract failure in the same run.
        """
        if configuration_id in self._disqualified:
            self._event_log.halt(
                "measurement_after_disqualification",
                configuration_id=configuration_id,
                measurement_kind=measurement_kind,
            )
            raise MeasurementAfterDisqualification(
                "Configuration {0} is disqualified; measurement not permitted".format(
                    configuration_id
                )
            )
        self._event_log.append(
            "measurement_recorded",
            configuration_id=configuration_id,
            measurement_kind=measurement_kind,
            payload=payload,
        )
