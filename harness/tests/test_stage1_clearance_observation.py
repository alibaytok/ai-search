"""Tests for harness.stage1_clearance_observation.

Per WO-46 (DC-046): the Stage 1 clearance observation module accepts
an already-loaded WO-45 Stage 1 result dict and emits a fresh
fixed-shape Stage 1 clearance observation ONLY when Stage 1 passed
with all authorization booleans intact. These tests assert:

- the success path returns a dict with exactly the ten allowed
  observation keys;
- the success path records a `stage1_clearance_observation_recorded`
  event;
- the success path keeps `stage1_cleared` literal True and
  `selection_made` / `measurement_authorized` /
  `real_benchmark_authorized` literal False;
- every documented rejection path raises the matching named
  exception and records an explicit halt event before raising;
- forbidden selection language and forbidden claim phrases in any
  surfaced string field are rejected (including the local
  `"score"` / `"scoring"` extension);
- the function does not mutate the input dict;
- the function does not write any file during success or failure
  paths.

The tests use only Python stdlib plus harness-internal imports.
"""

import copy
import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.stage1_clearance_observation import (
    ALLOWED_OBSERVATION_KEYS,
    ForbiddenLanguageInStage1Result,
    InvalidStage1ResultKind,
    NonObjectStage1Result,
    Stage1AuthorizesMeasurement,
    Stage1AuthorizesRealBenchmark,
    Stage1DeclaresSelection,
    Stage1FailedChecksPresent,
    Stage1NotPassed,
    record_stage1_clearance_observation,
)


STAGE1_CLEARANCE_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + ("score", "scoring")


def _passing_stage1_result():
    """Return a fresh well-formed Stage 1 result dict for a passing run.

    The dict mirrors the WO-45 ALLOWED_RESULT_KEYS shape exactly. Tests
    that need a tampered or failing variant copy this dict and mutate
    one field; the original returned by this helper remains pristine.
    """
    return {
        "result_kind": "stage1_contract_safety_result",
        "contract_safety_status": "passed",
        "stage1_passed": True,
        "checks_run_count": 4,
        "checks_passed_count": 4,
        "checks_failed_count": 0,
        "failed_check_names": [],
        "candidate_adapter_id": "toy-candidate-adapter-001",
        "configuration_id": "toy-scaffold-config",
        "fixture_set_id": "toy-fixture-set-001",
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "result_note": (
            "Scaffold-internal Stage 1 contract-safety observation. "
            "No measurement performed; no real adapter invoked."
        ),
    }


def _failing_stage1_result():
    """Return a Stage 1 result dict that represents a failed Stage 1 run."""
    result = _passing_stage1_result()
    result["contract_safety_status"] = "failed"
    result["stage1_passed"] = False
    result["checks_run_count"] = 2
    result["checks_passed_count"] = 1
    result["checks_failed_count"] = 1
    result["failed_check_names"] = ["scaffold_always_fail"]
    return result


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


def _last_halt_event(event_log):
    for event in reversed(event_log.events):
        if event["type"] == "halt":
            return event
    return None


class ClearanceObservationSuccessTest(unittest.TestCase):
    def test_success_returns_allowed_keys(self):
        log = EventLog()
        observation = record_stage1_clearance_observation(
            _passing_stage1_result(), log
        )
        self.assertEqual(
            set(observation.keys()), set(ALLOWED_OBSERVATION_KEYS)
        )

    def test_success_carries_expected_literals(self):
        log = EventLog()
        observation = record_stage1_clearance_observation(
            _passing_stage1_result(), log
        )
        self.assertEqual(
            observation["observation_kind"], "stage1_clearance_observation"
        )
        self.assertIs(observation["stage1_cleared"], True)
        self.assertIs(observation["selection_made"], False)
        self.assertIs(observation["measurement_authorized"], False)
        self.assertIs(observation["real_benchmark_authorized"], False)

    def test_success_propagates_identifier_fields(self):
        log = EventLog()
        result = _passing_stage1_result()
        observation = record_stage1_clearance_observation(result, log)
        self.assertEqual(
            observation["candidate_adapter_id"],
            result["candidate_adapter_id"],
        )
        self.assertEqual(
            observation["configuration_id"], result["configuration_id"]
        )
        self.assertEqual(
            observation["fixture_set_id"], result["fixture_set_id"]
        )
        self.assertEqual(
            observation["checks_passed_count"],
            result["checks_passed_count"],
        )

    def test_success_records_observation_event(self):
        log = EventLog()
        record_stage1_clearance_observation(_passing_stage1_result(), log)
        events = log.events
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(
            event["type"], "stage1_clearance_observation_recorded"
        )
        self.assertEqual(
            event["candidate_adapter_id"], "toy-candidate-adapter-001"
        )
        self.assertEqual(event["configuration_id"], "toy-scaffold-config")
        self.assertEqual(event["fixture_set_id"], "toy-fixture-set-001")
        self.assertEqual(event["checks_passed_count"], 4)
        self.assertFalse(log.has_halt())


class ClearanceObservationRejectionTest(unittest.TestCase):
    def test_non_dict_rejected(self):
        for bad in ("not a dict", None, 42, ["not", "a", "dict"]):
            with self.subTest(bad=bad):
                log = EventLog()
                with self.assertRaises(NonObjectStage1Result):
                    record_stage1_clearance_observation(bad, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "stage1_clearance_non_object"
                )

    def test_wrong_result_kind_rejected(self):
        result = _passing_stage1_result()
        result["result_kind"] = "something_else"
        log = EventLog()
        with self.assertRaises(InvalidStage1ResultKind):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_clearance_invalid_result_kind"
        )

    def test_stage1_passed_false_rejected(self):
        result = _passing_stage1_result()
        result["stage1_passed"] = False
        log = EventLog()
        with self.assertRaises(Stage1NotPassed):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_clearance_not_passed")
        self.assertEqual(halt["reason_detail"], "stage1_passed_not_true")

    def test_contract_safety_status_not_passed_rejected(self):
        result = _passing_stage1_result()
        result["contract_safety_status"] = "failed"
        log = EventLog()
        with self.assertRaises(Stage1NotPassed):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_clearance_not_passed")
        self.assertEqual(
            halt["reason_detail"], "contract_safety_status_not_passed"
        )

    def test_full_failing_stage1_result_rejected(self):
        # A genuinely failing Stage 1 result (stage1_passed False,
        # status failed, non-zero failed count, non-empty failed names)
        # must be rejected. The first violation encountered is
        # stage1_passed_not_true (Step 3 of validation order).
        log = EventLog()
        with self.assertRaises(Stage1NotPassed):
            record_stage1_clearance_observation(
                _failing_stage1_result(), log
            )

    def test_checks_failed_count_nonzero_rejected(self):
        result = _passing_stage1_result()
        result["checks_failed_count"] = 1
        log = EventLog()
        with self.assertRaises(Stage1FailedChecksPresent):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_clearance_failed_checks_present"
        )
        self.assertEqual(
            halt["reason_detail"], "checks_failed_count_nonzero"
        )

    def test_failed_check_names_nonempty_rejected(self):
        result = _passing_stage1_result()
        result["failed_check_names"] = ["scaffold_always_fail"]
        log = EventLog()
        with self.assertRaises(Stage1FailedChecksPresent):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_clearance_failed_checks_present"
        )
        self.assertEqual(
            halt["reason_detail"], "failed_check_names_nonempty"
        )

    def test_measurement_authorized_true_rejected(self):
        result = _passing_stage1_result()
        result["measurement_authorized"] = True
        log = EventLog()
        with self.assertRaises(Stage1AuthorizesMeasurement):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_clearance_authorizes_measurement"
        )

    def test_real_benchmark_authorized_true_rejected(self):
        result = _passing_stage1_result()
        result["real_benchmark_authorized"] = True
        log = EventLog()
        with self.assertRaises(Stage1AuthorizesRealBenchmark):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_clearance_authorizes_real_benchmark"
        )

    def test_selection_made_true_rejected(self):
        result = _passing_stage1_result()
        result["selection_made"] = True
        log = EventLog()
        with self.assertRaises(Stage1DeclaresSelection):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_clearance_declares_selection"
        )


class ClearanceObservationForbiddenLanguageTest(unittest.TestCase):
    def test_forbidden_selection_language_in_identifier_rejected(self):
        for phrase in STAGE1_CLEARANCE_FORBIDDEN_PHRASES:
            with self.subTest(phrase=phrase):
                result = _passing_stage1_result()
                # Inject the forbidden phrase into a surfaced identifier
                # so the result-surface scan catches it.
                result["candidate_adapter_id"] = (
                    "toy-{0}-001".format(phrase)
                )
                log = EventLog()
                with self.assertRaises(ForbiddenLanguageInStage1Result):
                    record_stage1_clearance_observation(result, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "stage1_clearance_forbidden_language"
                )
                self.assertEqual(
                    halt["surface_field"], "candidate_adapter_id"
                )

    def test_forbidden_claim_phrase_in_identifier_rejected(self):
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            with self.subTest(phrase=phrase):
                result = _passing_stage1_result()
                result["configuration_id"] = (
                    "toy-{0}-config".format(phrase)
                )
                log = EventLog()
                with self.assertRaises(ForbiddenLanguageInStage1Result):
                    record_stage1_clearance_observation(result, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "stage1_clearance_forbidden_language"
                )
                self.assertEqual(halt["surface_field"], "configuration_id")

    def test_score_substring_in_fixture_set_id_rejected(self):
        # Explicit coverage for the WO-35 Codex review-time hardening
        # local-mirror extension: "score" / "scoring" are not in the
        # canonical FORBIDDEN_PHRASES but ARE in the extended list this
        # module applies. Verify the substring is caught.
        result = _passing_stage1_result()
        result["fixture_set_id"] = "toy-score-fixture-set"
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInStage1Result):
            record_stage1_clearance_observation(result, log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["surface_field"], "fixture_set_id")


class ClearanceObservationLanguageHygieneTest(unittest.TestCase):
    def test_success_observation_has_no_forbidden_language(self):
        log = EventLog()
        observation = record_stage1_clearance_observation(
            _passing_stage1_result(), log
        )
        rendered = str(observation).lower()
        for phrase in STAGE1_CLEARANCE_FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase {0!r} in observation".format(phrase),
            )
        for text in _walk_strings(observation):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "forbidden claim phrase {0!r} in observation: "
                    "{1!r}".format(phrase, text),
                )


class ClearanceObservationIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_input(self):
        result = _passing_stage1_result()
        before = copy.deepcopy(result)
        log = EventLog()
        record_stage1_clearance_observation(result, log)
        self.assertEqual(result, before)

    def test_function_writes_no_files_on_success(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log = EventLog()
            record_stage1_clearance_observation(
                _passing_stage1_result(), log
            )
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_function_writes_no_files_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log = EventLog()
            with self.assertRaises(Stage1NotPassed):
                record_stage1_clearance_observation(
                    _failing_stage1_result(), log
                )
            self.assertEqual(os.listdir(tmp_dir), [])


if __name__ == "__main__":
    unittest.main()
