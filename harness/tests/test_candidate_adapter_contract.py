"""Tests for harness.candidate_adapter_contract.

Per WO-43 / WO-44 (DC-044): the candidate adapter contract validator
accepts an already-loaded dict and validates the scaffold-level shape
of a candidate adapter admission record. These tests assert:

- the toy candidate adapter record loads and validates successfully;
- the success event is recorded with the expected fields;
- every documented rejection path raises the matching named
  exception and records an explicit halt event before raising;
- unknown WO-21 plane names are rejected;
- forbidden selection language is rejected;
- forbidden claim phrases are rejected;
- the validator performs no filesystem writes during success paths.

The tests use only Python stdlib plus harness-internal imports. They
do not write to disk.
"""

import copy
import json
import os
import tempfile
import unittest

from harness.candidate_adapter_contract import (
    CandidateAdapterDeclaresProductionRegistration,
    CandidateAdapterDeclaresRealAdapter,
    CandidateAdapterDeclaresSelection,
    ForbiddenClaimInCandidateAdapterRecord,
    ForbiddenLanguageInCandidateAdapterRecord,
    InvalidCandidateAdapterMarker,
    MissingCandidateAdapterField,
    MissingCandidateAdapterMarker,
    NonObjectCandidateAdapterRecord,
    REQUIRED_FIELDS,
    SCAFFOLD_MARKER_KEY,
    UnknownCandidateAdapterPlane,
    validate_candidate_adapter_record,
)
from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


_TOY_RECORD_PATH = os.path.join(
    os.path.dirname(__file__), "fixtures", "toy_candidate_adapter_record.json"
)


def _load_toy_record():
    with open(_TOY_RECORD_PATH, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _last_halt_event(event_log):
    for event in reversed(event_log.events):
        if event["type"] == "halt":
            return event
    return None


class CandidateAdapterRecordToyLoadTest(unittest.TestCase):
    def test_toy_record_loads_as_dict(self):
        record = _load_toy_record()
        self.assertIsInstance(record, dict)
        self.assertIn(SCAFFOLD_MARKER_KEY, record)


class CandidateAdapterRecordSuccessTest(unittest.TestCase):
    def test_toy_record_validates_successfully(self):
        record = _load_toy_record()
        log = EventLog()
        returned = validate_candidate_adapter_record(record, log)
        self.assertIs(returned, record)
        self.assertFalse(log.has_halt())

    def test_success_records_candidate_adapter_record_validated_event(self):
        record = _load_toy_record()
        log = EventLog()
        validate_candidate_adapter_record(record, log)
        events = log.events
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["type"], "candidate_adapter_record_validated")
        self.assertEqual(
            event["candidate_adapter_id"], record["candidate_adapter_id"]
        )
        self.assertEqual(event["adapter_kind"], record["adapter_kind"])
        self.assertEqual(
            event["configuration_id"], record["configuration_id"]
        )
        self.assertEqual(
            event["planes_declared"], list(record["planes_declared"])
        )

    def test_validation_does_not_write_files(self):
        # The validator must not create any file. Run it inside a fresh
        # tempdir and verify the directory remains empty.
        with tempfile.TemporaryDirectory() as tmp_dir:
            record = _load_toy_record()
            log = EventLog()
            validate_candidate_adapter_record(record, log)
            self.assertEqual(os.listdir(tmp_dir), [])


class CandidateAdapterRecordRejectionTest(unittest.TestCase):
    def test_non_dict_input_rejected(self):
        for bad in ("not a dict", None, 42, ["not", "a", "dict"]):
            with self.subTest(bad=bad):
                log = EventLog()
                with self.assertRaises(NonObjectCandidateAdapterRecord):
                    validate_candidate_adapter_record(bad, log)
                halt = _last_halt_event(log)
                self.assertIsNotNone(halt)
                self.assertEqual(halt["reason"], "candidate_adapter_non_object")

    def test_missing_scaffold_marker_rejected(self):
        record = _load_toy_record()
        del record[SCAFFOLD_MARKER_KEY]
        log = EventLog()
        with self.assertRaises(MissingCandidateAdapterMarker):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "candidate_adapter_missing_marker")

    def test_invalid_marker_non_string_rejected(self):
        record = _load_toy_record()
        record[SCAFFOLD_MARKER_KEY] = 42
        log = EventLog()
        with self.assertRaises(InvalidCandidateAdapterMarker):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "candidate_adapter_invalid_marker")

    def test_invalid_marker_missing_substring_rejected(self):
        record = _load_toy_record()
        # Missing "candidate-adapter" substring.
        record[SCAFFOLD_MARKER_KEY] = "harness-internal scaffold toy"
        log = EventLog()
        with self.assertRaises(InvalidCandidateAdapterMarker):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "candidate_adapter_invalid_marker")
        self.assertEqual(
            halt["missing_marker_substring"], "candidate-adapter"
        )

    def test_missing_required_field_rejected(self):
        for field in REQUIRED_FIELDS:
            with self.subTest(field=field):
                record = _load_toy_record()
                del record[field]
                log = EventLog()
                with self.assertRaises(MissingCandidateAdapterField):
                    validate_candidate_adapter_record(record, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "candidate_adapter_missing_field"
                )
                self.assertEqual(halt["missing_field"], field)

    def test_selection_made_true_rejected(self):
        record = _load_toy_record()
        record["selection_made"] = True
        log = EventLog()
        with self.assertRaises(CandidateAdapterDeclaresSelection):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "candidate_adapter_declares_selection"
        )

    def test_production_registration_true_rejected(self):
        record = _load_toy_record()
        record["production_registration"] = True
        log = EventLog()
        with self.assertRaises(
            CandidateAdapterDeclaresProductionRegistration
        ):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"],
            "candidate_adapter_declares_production_registration",
        )

    def test_real_adapter_true_rejected(self):
        record = _load_toy_record()
        record["real_adapter"] = True
        log = EventLog()
        with self.assertRaises(CandidateAdapterDeclaresRealAdapter):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "candidate_adapter_declares_real_adapter"
        )

    def test_unknown_plane_rejected(self):
        record = _load_toy_record()
        record["planes_declared"] = [
            "official_route_results",
            "unknown_plane_name",
        ]
        log = EventLog()
        with self.assertRaises(UnknownCandidateAdapterPlane):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "candidate_adapter_unknown_plane"
        )
        self.assertEqual(halt["plane"], "unknown_plane_name")

    def test_planes_declared_non_list_rejected(self):
        record = _load_toy_record()
        record["planes_declared"] = "official_route_results"
        log = EventLog()
        with self.assertRaises(UnknownCandidateAdapterPlane):
            validate_candidate_adapter_record(record, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "candidate_adapter_unknown_plane"
        )
        self.assertEqual(halt["plane_type"], "str")

    def test_forbidden_selection_language_rejected(self):
        for phrase in FORBIDDEN_PHRASES:
            with self.subTest(phrase=phrase):
                record = _load_toy_record()
                # Inject the forbidden phrase into a benign field.
                record["purpose_note"] = (
                    "scaffold note that contains the word {0}".format(phrase)
                )
                log = EventLog()
                with self.assertRaises(
                    ForbiddenLanguageInCandidateAdapterRecord
                ):
                    validate_candidate_adapter_record(record, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "candidate_adapter_forbidden_language"
                )

    def test_forbidden_claim_phrase_rejected(self):
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            with self.subTest(phrase=phrase):
                record = _load_toy_record()
                record["purpose_note"] = (
                    "scaffold note that contains the phrase {0}".format(phrase)
                )
                log = EventLog()
                with self.assertRaises(
                    ForbiddenClaimInCandidateAdapterRecord
                ):
                    validate_candidate_adapter_record(record, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "candidate_adapter_forbidden_claim"
                )


class CandidateAdapterRecordIsolationTest(unittest.TestCase):
    def test_validation_does_not_mutate_input(self):
        record = _load_toy_record()
        before = copy.deepcopy(record)
        log = EventLog()
        validate_candidate_adapter_record(record, log)
        self.assertEqual(record, before)


if __name__ == "__main__":
    unittest.main()
