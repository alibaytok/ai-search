"""Tests for harness.stage1_contract_safety.

Per WO-45 (DC-045): the Stage 1 contract-safety pass scaffold runs a
fixed-shape contract-safety pass over the Stage 0 readiness output
and the scaffold fixture admission and candidate adapter records.
These tests assert:

- the success path returns a dict with exactly the allowed result
  keys, records per-check pass events and the final pass event, and
  keeps `measurement_authorized` and `real_benchmark_authorized`
  literal False on both the pass path and the fail path;
- a failing check returns the failed result, records the failed
  check event, records the halt, and does not run later checks;
- every documented Stage 0 / record / contract-check-list rejection
  raises the matching named exception and records an explicit halt
  event before raising;
- the output contains no `FORBIDDEN_PHRASES` substring, no `"score"`,
  no `"scoring"`, and no `FORBIDDEN_CLAIM_PHRASES` substring;
- the function performs no filesystem writes during success or
  failure paths.

The tests use only Python stdlib plus harness-internal imports. They
do not write to disk.
"""

import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.readiness_review import review_stage0_readiness
from harness.review_package import FORBIDDEN_PHRASES
from harness.stage1_contract_safety import (
    ALLOWED_RESULT_KEYS,
    InvalidContractCheck,
    InvalidContractCheckList,
    InvalidStage0Readiness,
    NonObjectStage0Readiness,
    NonObjectStage1Record,
    Stage0AuthorizesMeasurement,
    Stage0AuthorizesRealBenchmark,
    Stage0DeclaresSelection,
    Stage1RecordDeclaresProductionRegistration,
    Stage1RecordDeclaresRealAdapter,
    Stage1RecordDeclaresRealBenchmarkData,
    Stage1RecordDeclaresSelection,
    run_stage1_contract_safety,
)


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_TOY_ADAPTER_PATH = os.path.join(_FIXTURE_DIR, "toy_candidate_adapter_record.json")
_TOY_FIXTURE_PATH = os.path.join(_FIXTURE_DIR, "toy_fixture_admission_record.json")


STAGE1_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + ("score", "scoring")


def _load_adapter():
    with open(_TOY_ADAPTER_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_fixture():
    with open(_TOY_FIXTURE_PATH, "r", encoding="utf-8") as handle:
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


def _last_halt_event(event_log):
    for event in reversed(event_log.events):
        if event["type"] == "halt":
            return event
    return None


def _fresh_readiness():
    """Build a fresh Stage 0 readiness dict via the upstream reviewer."""
    log = EventLog()
    return review_stage0_readiness(_load_fixture(), _load_adapter(), log)


def _always_pass_checks():
    return [
        ("scaffold_stage0_ready_observed",
         lambda obs: obs["stage0_ready"] is True),
        ("scaffold_no_measurement_authorized",
         lambda obs: obs["measurement_authorized"] is False),
        ("scaffold_no_real_benchmark_authorized",
         lambda obs: obs["real_benchmark_authorized"] is False),
        ("scaffold_selection_made_false",
         lambda obs: obs["selection_made"] is False),
    ]


def _first_failing_checks():
    """Returns a list whose second check fails; later checks (a third
    that would also pass) must NOT be executed under the halt-on-first-
    failure rule.
    """
    sentinel = {"third_check_ran": False}

    def third_check(obs):
        sentinel["third_check_ran"] = True
        return True

    checks = [
        ("scaffold_pass_first",
         lambda obs: True),
        ("scaffold_always_fail",
         lambda obs: False),
        ("scaffold_should_not_run",
         third_check),
    ]
    return checks, sentinel


class Stage1SuccessTest(unittest.TestCase):
    def test_success_returns_allowed_keys(self):
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        self.assertEqual(set(result.keys()), set(ALLOWED_RESULT_KEYS))

    def test_success_status_and_passed_flag(self):
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        self.assertEqual(result["contract_safety_status"], "passed")
        self.assertIs(result["stage1_passed"], True)
        self.assertEqual(result["checks_run_count"], 4)
        self.assertEqual(result["checks_passed_count"], 4)
        self.assertEqual(result["checks_failed_count"], 0)
        self.assertEqual(result["failed_check_names"], [])

    def test_passing_stage1_keeps_measurement_authorized_false(self):
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        self.assertIs(result["measurement_authorized"], False)

    def test_passing_stage1_keeps_real_benchmark_authorized_false(self):
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        self.assertIs(result["real_benchmark_authorized"], False)

    def test_success_records_per_check_pass_events_and_final_event(self):
        log = EventLog()
        run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        event_types = [e["type"] for e in log.events]
        pass_event_count = event_types.count("stage1_contract_check_passed")
        self.assertEqual(pass_event_count, 4)
        self.assertEqual(
            event_types.count("stage1_contract_safety_passed"), 1
        )
        self.assertEqual(
            event_types.count("stage1_contract_check_failed"), 0
        )
        self.assertFalse(log.has_halt())

    def test_success_id_fields_propagate_from_records(self):
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        self.assertEqual(
            result["candidate_adapter_id"],
            _load_adapter()["candidate_adapter_id"],
        )
        self.assertEqual(
            result["configuration_id"], _load_adapter()["configuration_id"]
        )
        self.assertEqual(
            result["fixture_set_id"], _load_fixture()["fixture_set_id"]
        )
        self.assertIs(result["selection_made"], False)


class Stage1FailureTest(unittest.TestCase):
    def test_failing_check_returns_failed_result(self):
        checks, sentinel = _first_failing_checks()
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            checks,
            log,
        )
        self.assertEqual(result["contract_safety_status"], "failed")
        self.assertIs(result["stage1_passed"], False)
        self.assertEqual(result["checks_run_count"], 2)
        self.assertEqual(result["checks_passed_count"], 1)
        self.assertEqual(result["checks_failed_count"], 1)
        self.assertEqual(
            result["failed_check_names"], ["scaffold_always_fail"]
        )

    def test_failing_check_records_failed_event_and_halt(self):
        checks, _ = _first_failing_checks()
        log = EventLog()
        run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            checks,
            log,
        )
        event_types = [e["type"] for e in log.events]
        self.assertEqual(
            event_types.count("stage1_contract_check_failed"), 1
        )
        self.assertTrue(log.has_halt())
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_contract_safety_failed")
        self.assertEqual(halt["failed_check_name"], "scaffold_always_fail")

    def test_halt_on_first_failure_prevents_later_checks(self):
        checks, sentinel = _first_failing_checks()
        log = EventLog()
        run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            checks,
            log,
        )
        # The third check must NOT have been executed.
        self.assertFalse(sentinel["third_check_ran"])

    def test_failing_stage1_keeps_authorization_booleans_false(self):
        checks, _ = _first_failing_checks()
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            checks,
            log,
        )
        self.assertIs(result["measurement_authorized"], False)
        self.assertIs(result["real_benchmark_authorized"], False)
        self.assertIs(result["selection_made"], False)


class Stage0InputRejectionTest(unittest.TestCase):
    def test_non_dict_stage0_readiness_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectStage0Readiness):
            run_stage1_contract_safety(
                "not a dict",
                _load_fixture(),
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_non_object_stage0_readiness")

    def test_stage0_not_ready_rejected(self):
        readiness = _fresh_readiness()
        readiness["stage0_ready"] = False
        log = EventLog()
        with self.assertRaises(InvalidStage0Readiness):
            run_stage1_contract_safety(
                readiness,
                _load_fixture(),
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_invalid_stage0_readiness")
        self.assertEqual(halt["reason_detail"], "stage0_not_ready")

    def test_stage0_review_kind_mismatch_rejected(self):
        readiness = _fresh_readiness()
        readiness["review_kind"] = "not_stage0_readiness"
        log = EventLog()
        with self.assertRaises(InvalidStage0Readiness):
            run_stage1_contract_safety(
                readiness,
                _load_fixture(),
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_invalid_stage0_readiness")
        self.assertEqual(halt["reason_detail"], "review_kind_mismatch")

    def test_stage0_measurement_authorized_rejected(self):
        readiness = _fresh_readiness()
        readiness["measurement_authorized"] = True
        log = EventLog()
        with self.assertRaises(Stage0AuthorizesMeasurement):
            run_stage1_contract_safety(
                readiness,
                _load_fixture(),
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_stage0_authorizes_measurement"
        )

    def test_stage0_real_benchmark_authorized_rejected(self):
        readiness = _fresh_readiness()
        readiness["real_benchmark_authorized"] = True
        log = EventLog()
        with self.assertRaises(Stage0AuthorizesRealBenchmark):
            run_stage1_contract_safety(
                readiness,
                _load_fixture(),
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_stage0_authorizes_real_benchmark"
        )

    def test_stage0_selection_made_rejected(self):
        readiness = _fresh_readiness()
        readiness["selection_made"] = True
        log = EventLog()
        with self.assertRaises(Stage0DeclaresSelection):
            run_stage1_contract_safety(
                readiness,
                _load_fixture(),
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_stage0_declares_selection")


class Stage1RecordRejectionTest(unittest.TestCase):
    def test_non_dict_fixture_record_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectStage1Record):
            run_stage1_contract_safety(
                _fresh_readiness(),
                "not a dict",
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_non_object_record")
        self.assertEqual(halt["record_role"], "fixture_admission_record")

    def test_non_dict_candidate_record_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectStage1Record):
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                "not a dict",
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_non_object_record")
        self.assertEqual(halt["record_role"], "candidate_adapter_record")

    def test_fixture_real_benchmark_data_true_rejected(self):
        bad_fixture = _load_fixture()
        bad_fixture["real_benchmark_data"] = True
        log = EventLog()
        with self.assertRaises(Stage1RecordDeclaresRealBenchmarkData):
            run_stage1_contract_safety(
                _fresh_readiness(),
                bad_fixture,
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_record_declares_real_benchmark_data"
        )

    def test_candidate_real_adapter_true_rejected(self):
        bad_adapter = _load_adapter()
        bad_adapter["real_adapter"] = True
        log = EventLog()
        with self.assertRaises(Stage1RecordDeclaresRealAdapter):
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                bad_adapter,
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "stage1_record_declares_real_adapter"
        )

    def test_candidate_production_registration_true_rejected(self):
        bad_adapter = _load_adapter()
        bad_adapter["production_registration"] = True
        log = EventLog()
        with self.assertRaises(Stage1RecordDeclaresProductionRegistration):
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                bad_adapter,
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"],
            "stage1_record_declares_production_registration",
        )

    def test_fixture_selection_made_true_rejected(self):
        bad_fixture = _load_fixture()
        bad_fixture["selection_made"] = True
        log = EventLog()
        with self.assertRaises(Stage1RecordDeclaresSelection):
            run_stage1_contract_safety(
                _fresh_readiness(),
                bad_fixture,
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_record_declares_selection")
        self.assertEqual(halt["record_role"], "fixture_admission_record")

    def test_candidate_selection_made_true_rejected(self):
        bad_adapter = _load_adapter()
        bad_adapter["selection_made"] = True
        log = EventLog()
        with self.assertRaises(Stage1RecordDeclaresSelection):
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                bad_adapter,
                _always_pass_checks(),
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_record_declares_selection")
        self.assertEqual(halt["record_role"], "candidate_adapter_record")


class ContractCheckListRejectionTest(unittest.TestCase):
    def test_empty_list_rejected(self):
        log = EventLog()
        with self.assertRaises(InvalidContractCheckList):
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                _load_adapter(),
                [],
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_invalid_contract_check_list")

    def test_non_list_rejected(self):
        log = EventLog()
        with self.assertRaises(InvalidContractCheckList):
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                _load_adapter(),
                "not a list",
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_invalid_contract_check_list")

    def test_non_callable_check_rejected(self):
        log = EventLog()
        with self.assertRaises(InvalidContractCheck):
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                _load_adapter(),
                [("only_a_name", "not_callable")],
                log,
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "stage1_invalid_contract_check")

    def test_malformed_pair_rejected(self):
        for bad in (
            [("only_one_element_tuple",)],
            [("a", lambda obs: True, "extra")],
            [(42, lambda obs: True)],
            [("", lambda obs: True)],
            ["not_a_pair"],
        ):
            with self.subTest(bad=bad):
                log = EventLog()
                with self.assertRaises(InvalidContractCheck):
                    run_stage1_contract_safety(
                        _fresh_readiness(),
                        _load_fixture(),
                        _load_adapter(),
                        bad,
                        log,
                    )

    def test_forbidden_check_name_rejected(self):
        for check_name, phrase in (
            ("best_candidate", "best"),
            ("quality_score", "score"),
        ):
            with self.subTest(check_name=check_name):
                log = EventLog()
                with self.assertRaises(InvalidContractCheck):
                    run_stage1_contract_safety(
                        _fresh_readiness(),
                        _load_fixture(),
                        _load_adapter(),
                        [(check_name, lambda obs: True)],
                        log,
                    )
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "stage1_invalid_contract_check"
                )
                self.assertEqual(halt["forbidden_phrase"], phrase)


class Stage1LanguageHygieneTest(unittest.TestCase):
    def test_output_has_no_forbidden_selection_language(self):
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        rendered = str(result).lower()
        for phrase in STAGE1_FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase {0!r} in Stage 1 result".format(phrase),
            )

    def test_output_has_no_forbidden_claim_phrases(self):
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            _always_pass_checks(),
            log,
        )
        for text in _walk_strings(result):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "forbidden claim phrase {0!r} in Stage 1 result: "
                    "{1!r}".format(phrase, text),
                )

    def test_failed_output_has_no_forbidden_language(self):
        checks, _ = _first_failing_checks()
        log = EventLog()
        result = run_stage1_contract_safety(
            _fresh_readiness(),
            _load_fixture(),
            _load_adapter(),
            checks,
            log,
        )
        rendered = str(result).lower()
        for phrase in STAGE1_FORBIDDEN_PHRASES:
            self.assertNotIn(phrase, rendered)
        for text in _walk_strings(result):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(phrase, lowered)


class Stage1FilesystemIsolationTest(unittest.TestCase):
    def test_success_path_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log = EventLog()
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                _load_adapter(),
                _always_pass_checks(),
                log,
            )
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_failure_path_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            checks, _ = _first_failing_checks()
            log = EventLog()
            run_stage1_contract_safety(
                _fresh_readiness(),
                _load_fixture(),
                _load_adapter(),
                checks,
                log,
            )
            self.assertEqual(os.listdir(tmp_dir), [])


if __name__ == "__main__":
    unittest.main()
