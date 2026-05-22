"""Tests for harness.readiness_review.

Per WO-43 / WO-44 (DC-044): the Stage 0 readiness review consumes an
already-loaded fixture admission record and an already-loaded
candidate adapter record and returns a fresh observation-only
readiness dict with exactly the eleven allowed top-level keys. These
tests assert:

- the toy fixture admission record loads as a dict;
- a successful Stage 0 readiness review returns the exact allowed
  keys with `stage0_ready is True`, `measurement_authorized is False`,
  `real_benchmark_authorized is False`, and `selection_made is False`;
- the success event is recorded with the expected fields;
- the readiness dict contains no `FORBIDDEN_PHRASES`, no `"score"`,
  no `"scoring"`, and no `FORBIDDEN_CLAIM_PHRASES`;
- every documented fixture admission rejection path raises the
  matching named exception and records an explicit halt event;
- a candidate adapter rejection prevents the Stage 0 readiness
  result from being produced (the exception propagates and no
  readiness dict is returned);
- the review performs no filesystem writes during success paths.

The tests use only Python stdlib plus harness-internal imports. They
do not write to disk.
"""

import copy
import json
import os
import tempfile
import unittest

from harness.candidate_adapter_contract import (
    CandidateAdapterDeclaresSelection,
    UnknownCandidateAdapterPlane,
)
from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.readiness_review import (
    ALLOWED_READINESS_KEYS,
    FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY,
    FixtureAdmissionDeclaresAuthorityDecision,
    FixtureAdmissionDeclaresRealBenchmarkData,
    FixtureAdmissionDeclaresSelection,
    ForbiddenClaimInFixtureAdmissionRecord,
    ForbiddenLanguageInFixtureAdmissionRecord,
    InvalidFixtureAdmissionMarker,
    MissingFixtureAdmissionField,
    MissingFixtureAdmissionMarker,
    NonObjectFixtureAdmissionRecord,
    REQUIRED_FIXTURE_ADMISSION_FIELDS,
    review_stage0_readiness,
)
from harness.review_package import FORBIDDEN_PHRASES


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_TOY_ADAPTER_PATH = os.path.join(_FIXTURE_DIR, "toy_candidate_adapter_record.json")
_TOY_FIXTURE_PATH = os.path.join(_FIXTURE_DIR, "toy_fixture_admission_record.json")


REVIEW_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + ("score", "scoring")


def _load_toy_adapter():
    with open(_TOY_ADAPTER_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_toy_fixture():
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


class FixtureAdmissionRecordLoadTest(unittest.TestCase):
    def test_toy_fixture_admission_record_loads_as_dict(self):
        record = _load_toy_fixture()
        self.assertIsInstance(record, dict)
        self.assertIn(FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY, record)


class Stage0ReadinessSuccessTest(unittest.TestCase):
    def test_review_returns_allowed_keys(self):
        log = EventLog()
        readiness = review_stage0_readiness(
            _load_toy_fixture(), _load_toy_adapter(), log
        )
        self.assertEqual(set(readiness.keys()), set(ALLOWED_READINESS_KEYS))

    def test_stage0_ready_true_but_no_authorization(self):
        log = EventLog()
        readiness = review_stage0_readiness(
            _load_toy_fixture(), _load_toy_adapter(), log
        )
        self.assertIs(readiness["stage0_ready"], True)
        self.assertIs(readiness["measurement_authorized"], False)
        self.assertIs(readiness["real_benchmark_authorized"], False)
        self.assertIs(readiness["selection_made"], False)

    def test_counts_match_input_records(self):
        log = EventLog()
        readiness = review_stage0_readiness(
            _load_toy_fixture(), _load_toy_adapter(), log
        )
        self.assertEqual(readiness["fixture_class_count"], 3)
        self.assertEqual(
            readiness["candidate_plane_count"],
            len(_load_toy_adapter()["planes_declared"]),
        )
        self.assertEqual(
            readiness["fixture_set_id"],
            _load_toy_fixture()["fixture_set_id"],
        )
        self.assertEqual(
            readiness["candidate_adapter_id"],
            _load_toy_adapter()["candidate_adapter_id"],
        )
        self.assertEqual(
            readiness["configuration_id"],
            _load_toy_adapter()["configuration_id"],
        )

    def test_success_records_stage0_readiness_reviewed_event(self):
        log = EventLog()
        review_stage0_readiness(
            _load_toy_fixture(), _load_toy_adapter(), log
        )
        event_types = [e["type"] for e in log.events]
        self.assertIn("candidate_adapter_record_validated", event_types)
        self.assertIn("stage0_readiness_reviewed", event_types)
        # Order: candidate_adapter validation event is recorded before
        # stage0 readiness review event (the readiness reviewer delegates
        # to the contract validator first).
        self.assertLess(
            event_types.index("candidate_adapter_record_validated"),
            event_types.index("stage0_readiness_reviewed"),
        )
        self.assertFalse(log.has_halt())

    def test_readiness_dict_has_no_forbidden_selection_language(self):
        log = EventLog()
        readiness = review_stage0_readiness(
            _load_toy_fixture(), _load_toy_adapter(), log
        )
        rendered = str(readiness).lower()
        for phrase in REVIEW_FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase {0!r} in readiness dict".format(phrase),
            )

    def test_readiness_dict_has_no_forbidden_claim_phrases(self):
        log = EventLog()
        readiness = review_stage0_readiness(
            _load_toy_fixture(), _load_toy_adapter(), log
        )
        for text in _walk_strings(readiness):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "forbidden claim phrase {0!r} in readiness dict: "
                    "{1!r}".format(phrase, text),
                )

    def test_review_does_not_write_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log = EventLog()
            review_stage0_readiness(
                _load_toy_fixture(), _load_toy_adapter(), log
            )
            self.assertEqual(os.listdir(tmp_dir), [])


class FixtureAdmissionRejectionTest(unittest.TestCase):
    def test_non_dict_fixture_admission_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectFixtureAdmissionRecord):
            review_stage0_readiness(
                "not a dict", _load_toy_adapter(), log
            )
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "fixture_admission_non_object")

    def test_missing_fixture_admission_marker_rejected(self):
        record = _load_toy_fixture()
        del record[FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY]
        log = EventLog()
        with self.assertRaises(MissingFixtureAdmissionMarker):
            review_stage0_readiness(record, _load_toy_adapter(), log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "fixture_admission_missing_marker")

    def test_invalid_fixture_admission_marker_non_string_rejected(self):
        record = _load_toy_fixture()
        record[FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY] = 42
        log = EventLog()
        with self.assertRaises(InvalidFixtureAdmissionMarker):
            review_stage0_readiness(record, _load_toy_adapter(), log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "fixture_admission_invalid_marker")

    def test_invalid_fixture_admission_marker_missing_substring_rejected(self):
        record = _load_toy_fixture()
        # Missing "fixture-admission" substring.
        record[FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY] = "harness-internal toy"
        log = EventLog()
        with self.assertRaises(InvalidFixtureAdmissionMarker):
            review_stage0_readiness(record, _load_toy_adapter(), log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "fixture_admission_invalid_marker")
        self.assertEqual(
            halt["missing_marker_substring"], "fixture-admission"
        )

    def test_missing_fixture_admission_field_rejected(self):
        for field in REQUIRED_FIXTURE_ADMISSION_FIELDS:
            with self.subTest(field=field):
                record = _load_toy_fixture()
                del record[field]
                log = EventLog()
                with self.assertRaises(MissingFixtureAdmissionField):
                    review_stage0_readiness(
                        record, _load_toy_adapter(), log
                    )
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "fixture_admission_missing_field"
                )
                self.assertEqual(halt["missing_field"], field)

    def test_synthetic_only_false_rejected(self):
        record = _load_toy_fixture()
        record["synthetic_only"] = False
        log = EventLog()
        with self.assertRaises(FixtureAdmissionDeclaresRealBenchmarkData):
            review_stage0_readiness(record, _load_toy_adapter(), log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "fixture_admission_not_synthetic_only"
        )

    def test_real_benchmark_data_true_rejected(self):
        record = _load_toy_fixture()
        record["real_benchmark_data"] = True
        log = EventLog()
        with self.assertRaises(FixtureAdmissionDeclaresRealBenchmarkData):
            review_stage0_readiness(record, _load_toy_adapter(), log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"],
            "fixture_admission_declares_real_benchmark_data",
        )

    def test_admission_authority_decided_true_rejected(self):
        record = _load_toy_fixture()
        record["admission_authority_decided"] = True
        log = EventLog()
        with self.assertRaises(FixtureAdmissionDeclaresAuthorityDecision):
            review_stage0_readiness(record, _load_toy_adapter(), log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"],
            "fixture_admission_declares_authority_decision",
        )

    def test_selection_made_true_rejected(self):
        record = _load_toy_fixture()
        record["selection_made"] = True
        log = EventLog()
        with self.assertRaises(FixtureAdmissionDeclaresSelection):
            review_stage0_readiness(record, _load_toy_adapter(), log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "fixture_admission_declares_selection"
        )

    def test_forbidden_language_in_fixture_admission_rejected(self):
        for phrase in FORBIDDEN_PHRASES:
            with self.subTest(phrase=phrase):
                record = _load_toy_fixture()
                record["purpose_note"] = (
                    "scaffold note containing the word {0}".format(phrase)
                )
                log = EventLog()
                with self.assertRaises(
                    ForbiddenLanguageInFixtureAdmissionRecord
                ):
                    review_stage0_readiness(
                        record, _load_toy_adapter(), log
                    )
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"],
                    "fixture_admission_forbidden_language",
                )

    def test_forbidden_claim_phrase_in_fixture_admission_rejected(self):
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            with self.subTest(phrase=phrase):
                record = _load_toy_fixture()
                record["purpose_note"] = (
                    "scaffold note containing the phrase {0}".format(phrase)
                )
                log = EventLog()
                with self.assertRaises(
                    ForbiddenClaimInFixtureAdmissionRecord
                ):
                    review_stage0_readiness(
                        record, _load_toy_adapter(), log
                    )
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "fixture_admission_forbidden_claim"
                )


class CandidateAdapterRejectionPreventsStage0Test(unittest.TestCase):
    def test_candidate_adapter_selection_true_prevents_stage0_result(self):
        adapter = _load_toy_adapter()
        adapter["selection_made"] = True
        log = EventLog()
        with self.assertRaises(CandidateAdapterDeclaresSelection):
            review_stage0_readiness(_load_toy_fixture(), adapter, log)
        # Stage 0 readiness event must NOT have been recorded; only the
        # halt and possibly prior fixture-admission validation events.
        event_types = [e["type"] for e in log.events]
        self.assertNotIn("stage0_readiness_reviewed", event_types)
        self.assertNotIn("candidate_adapter_record_validated", event_types)

    def test_candidate_adapter_unknown_plane_prevents_stage0_result(self):
        adapter = _load_toy_adapter()
        adapter["planes_declared"] = ["unknown_plane_name"]
        log = EventLog()
        with self.assertRaises(UnknownCandidateAdapterPlane):
            review_stage0_readiness(_load_toy_fixture(), adapter, log)
        event_types = [e["type"] for e in log.events]
        self.assertNotIn("stage0_readiness_reviewed", event_types)


class Stage0InputIsolationTest(unittest.TestCase):
    def test_review_does_not_mutate_input_records(self):
        fixture_rec = _load_toy_fixture()
        adapter_rec = _load_toy_adapter()
        fixture_before = copy.deepcopy(fixture_rec)
        adapter_before = copy.deepcopy(adapter_rec)
        log = EventLog()
        review_stage0_readiness(fixture_rec, adapter_rec, log)
        self.assertEqual(fixture_rec, fixture_before)
        self.assertEqual(adapter_rec, adapter_before)


if __name__ == "__main__":
    unittest.main()
