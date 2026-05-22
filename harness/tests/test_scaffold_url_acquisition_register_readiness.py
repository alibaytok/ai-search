"""Tests for the WO-62 scaffold URL acquisition register-readiness diagnostic.

The tests exercise the diagnostic that asserts a WO-61 URL
acquisition observation is NOT sufficient to produce WO-55-compatible
source reference records. The same boundary as WO-50 through WO-61
applies: no real retrieval call, no adapter invocation, no network
call, no file IO inside the module, no hash computation, no metrics,
no ranking, no architecture choice, and no benchmark readiness
change.
"""

import ast
import copy
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_url_acquisition_register_readiness import (
    ALLOWED_OUTPUT_KEYS,
    ForbiddenLanguageInRegisterReadinessDiagnostic,
    ForbiddenRegisterProjectionFieldPresent,
    InvalidAcquiredReferences,
    InvalidUrlAcquisitionKind,
    MissingAcquiredReferenceField,
    MissingUrlAcquisitionObservationField,
    NonObjectAcquiredReference,
    NonObjectUrlAcquisitionObservation,
    READINESS_OUTPUT_FORBIDDEN_PHRASES,
    REQUIRED_ACQUIRED_REFERENCE_FIELDS,
    REQUIRED_OBSERVATION_FIELDS,
    UnsafeAdmissionClaimInUrlAcquisitionObservation,
    run_scaffold_url_acquisition_register_readiness,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT,
    "harness",
    "scaffold_url_acquisition_register_readiness.py",
)


def _acquired_reference(suffix="001"):
    return {
        "request_id": "req-{0}".format(suffix),
        "declared_kind": "prompt_collection",
        "origin_locator_observed": True,
        "origin_locator_length": 64,
        "content_available": True,
        "content_byte_length": 4096,
        "content_hash_prefix": "deadbeef0123",
        "content_type": "text/plain",
        "fetched_at": "2026-05-20T00:00:01Z",
        "corpus_admitted": False,
        "qualified": False,
        "source_material_extracted": False,
        "route_object_created": False,
    }


def _url_acquisition_observation(references=None):
    refs = references if references is not None else [_acquired_reference("001")]
    return {
        "url_acquisition_kind": "scaffold_url_acquisition_executor",
        "request_count": len(refs),
        "fetched_count": len(refs),
        "acquired_references": list(refs),
        "total_content_byte_length": sum(
            r.get("content_byte_length", 0) if isinstance(r, dict) else 0
            for r in refs
        ),
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "source_material_extracted_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "url_acquisition_note": "synthetic WO-61 observation for WO-62 tests",
    }


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


class RegisterReadinessCleanPassTest(unittest.TestCase):
    def test_clean_observation_returns_fixed_shape(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 15)
        self.assertEqual(
            output["readiness_kind"],
            "scaffold_url_acquisition_register_readiness",
        )
        self.assertEqual(output["url_acquisition_reference_count"], 1)

    def test_register_projection_ready_is_literal_false(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        self.assertIs(output["register_projection_ready"], False)

    def test_blocked_reasons_include_origin_and_full_hash_missing(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        self.assertIn(
            "origin_not_available_for_wo55_register",
            output["register_projection_blocked_reasons"],
        )
        self.assertIn(
            "full_hash_not_available_for_wo55_register",
            output["register_projection_blocked_reasons"],
        )
        self.assertEqual(
            output["register_projection_blocked_reason_count"], 2
        )

    def test_missing_register_fields_lists_origin_and_hash(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        self.assertEqual(
            list(output["missing_register_fields"]), ["origin", "hash"]
        )

    def test_safe_to_invent_missing_identity_literal_false(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        self.assertIs(output["safe_to_invent_missing_identity"], False)

    def test_source_register_invocation_not_authorized(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        self.assertIs(output["source_register_invocation_authorized"], False)

    def test_all_authorization_booleans_literal_false(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
        ):
            self.assertIs(output[key], False)

    def test_admission_counts_literal_zero(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)

    def test_empty_acquired_references_still_returns_blocked_diagnostic(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(references=[]), log
        )
        self.assertIs(output["register_projection_ready"], False)
        self.assertEqual(output["url_acquisition_reference_count"], 0)
        # blocked reasons still recorded because the diagnostic asserts a
        # structural gap that does not depend on having any reference.
        self.assertEqual(
            output["register_projection_blocked_reason_count"], 2
        )

    def test_blocked_event_emitted_with_counts(self):
        log = EventLog()
        run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        blocked = [
            e
            for e in log.events
            if e["type"]
            == "scaffold_url_acquisition_register_readiness_blocked"
        ]
        self.assertEqual(len(blocked), 1)
        self.assertEqual(
            blocked[0]["register_projection_blocked_reason_count"], 2
        )

    def test_reference_observed_event_per_reference(self):
        log = EventLog()
        observation = _url_acquisition_observation(
            references=[_acquired_reference("a"), _acquired_reference("b")]
        )
        run_scaffold_url_acquisition_register_readiness(observation, log)
        observed = [
            e
            for e in log.events
            if e["type"]
            == "scaffold_url_acquisition_register_readiness_reference_observed"
        ]
        self.assertEqual(len(observed), 2)


class RegisterReadinessTopLevelRejectionTest(unittest.TestCase):
    def test_non_dict_observation_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness("not a dict", log)

    def test_wrong_url_acquisition_kind_rejected(self):
        observation = _url_acquisition_observation()
        observation["url_acquisition_kind"] = "synthetic_other_kind"
        log = EventLog()
        with self.assertRaises(InvalidUrlAcquisitionKind):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_each_missing_top_level_field_rejected(self):
        for field in REQUIRED_OBSERVATION_FIELDS:
            observation = _url_acquisition_observation()
            del observation[field]
            log = EventLog()
            with self.assertRaises(MissingUrlAcquisitionObservationField):
                run_scaffold_url_acquisition_register_readiness(
                    observation, log
                )

    def test_acquired_references_not_list_rejected(self):
        observation = _url_acquisition_observation()
        observation["acquired_references"] = "not a list"
        log = EventLog()
        with self.assertRaises(InvalidAcquiredReferences):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_selection_made_true_rejected(self):
        observation = _url_acquisition_observation()
        observation["selection_made"] = True
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_measurement_authorized_true_rejected(self):
        observation = _url_acquisition_observation()
        observation["measurement_authorized"] = True
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_real_benchmark_authorized_true_rejected(self):
        observation = _url_acquisition_observation()
        observation["real_benchmark_authorized"] = True
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_real_benchmark_ready_true_rejected(self):
        observation = _url_acquisition_observation()
        observation["real_benchmark_ready"] = True
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_corpus_admitted_count_nonzero_rejected(self):
        observation = _url_acquisition_observation()
        observation["corpus_admitted_count"] = 1
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_qualified_count_nonzero_rejected(self):
        observation = _url_acquisition_observation()
        observation["qualified_count"] = 1
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_source_material_extracted_count_nonzero_rejected(self):
        observation = _url_acquisition_observation()
        observation["source_material_extracted_count"] = 1
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)


class RegisterReadinessReferenceRejectionTest(unittest.TestCase):
    def test_non_dict_reference_rejected(self):
        observation = _url_acquisition_observation(references=["not a dict"])
        log = EventLog()
        with self.assertRaises(NonObjectAcquiredReference):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_each_missing_reference_field_rejected(self):
        for field in REQUIRED_ACQUIRED_REFERENCE_FIELDS:
            reference = _acquired_reference("u1")
            del reference[field]
            observation = _url_acquisition_observation(references=[reference])
            log = EventLog()
            with self.assertRaises(MissingAcquiredReferenceField):
                run_scaffold_url_acquisition_register_readiness(
                    observation, log
                )

    def test_per_reference_corpus_admitted_true_rejected(self):
        reference = _acquired_reference("u1")
        reference["corpus_admitted"] = True
        observation = _url_acquisition_observation(references=[reference])
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_per_reference_qualified_true_rejected(self):
        reference = _acquired_reference("u1")
        reference["qualified"] = True
        observation = _url_acquisition_observation(references=[reference])
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_per_reference_source_material_extracted_true_rejected(self):
        reference = _acquired_reference("u1")
        reference["source_material_extracted"] = True
        observation = _url_acquisition_observation(references=[reference])
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_per_reference_route_object_created_true_rejected(self):
        reference = _acquired_reference("u1")
        reference["route_object_created"] = True
        observation = _url_acquisition_observation(references=[reference])
        log = EventLog()
        with self.assertRaises(UnsafeAdmissionClaimInUrlAcquisitionObservation):
            run_scaffold_url_acquisition_register_readiness(observation, log)


class RegisterReadinessForbiddenFieldTest(unittest.TestCase):
    def _expect_forbidden_field_rejection(self, observation):
        log = EventLog()
        with self.assertRaises(ForbiddenRegisterProjectionFieldPresent):
            run_scaffold_url_acquisition_register_readiness(observation, log)

    def test_top_level_raw_origin_locator_rejected(self):
        observation = _url_acquisition_observation()
        observation["origin_locator"] = "https://leaked.invalid/raw"
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_raw_content_bytes_rejected(self):
        observation = _url_acquisition_observation()
        observation["content_bytes"] = b"raw bytes"
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_full_content_hash_rejected(self):
        observation = _url_acquisition_observation()
        observation["content_hash"] = "full-hash-leaked"
        self._expect_forbidden_field_rejection(observation)

    def test_per_reference_raw_origin_locator_rejected(self):
        reference = _acquired_reference("u1")
        reference["origin_locator"] = "https://leaked.invalid/raw"
        observation = _url_acquisition_observation(references=[reference])
        self._expect_forbidden_field_rejection(observation)

    def test_per_reference_full_content_hash_rejected(self):
        reference = _acquired_reference("u1")
        reference["content_hash"] = "full-hash-leaked"
        observation = _url_acquisition_observation(references=[reference])
        self._expect_forbidden_field_rejection(observation)

    def test_per_reference_raw_content_bytes_rejected(self):
        reference = _acquired_reference("u1")
        reference["content_bytes"] = b"raw bytes"
        observation = _url_acquisition_observation(references=[reference])
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_extracted_material_rejected(self):
        observation = _url_acquisition_observation()
        observation["extracted_material"] = {"x": 1}
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_normalized_material_rejected(self):
        observation = _url_acquisition_observation()
        observation["normalized_material"] = {"x": 1}
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_candidate_fragments_rejected(self):
        observation = _url_acquisition_observation()
        observation["candidate_fragments"] = []
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_candidate_route_fragments_rejected(self):
        observation = _url_acquisition_observation()
        observation["candidate_route_fragments"] = []
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_candidate_workflow_fragments_rejected(self):
        observation = _url_acquisition_observation()
        observation["candidate_workflow_fragments"] = []
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_route_field_rejected(self):
        observation = _url_acquisition_observation()
        observation["route"] = "x"
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_route_state_rejected(self):
        observation = _url_acquisition_observation()
        observation["route_state"] = "x"
        self._expect_forbidden_field_rejection(observation)

    def test_per_reference_source_card_rejected(self):
        reference = _acquired_reference("u1")
        reference["source_card"] = {}
        observation = _url_acquisition_observation(references=[reference])
        self._expect_forbidden_field_rejection(observation)

    def test_per_reference_authority_rejected(self):
        reference = _acquired_reference("u1")
        reference["authority"] = "some"
        observation = _url_acquisition_observation(references=[reference])
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_validation_evidence_field_rejected(self):
        observation = _url_acquisition_observation()
        observation["validation_evidence"] = "x"
        self._expect_forbidden_field_rejection(observation)

    def test_top_level_benchmark_fixture_class_field_rejected(self):
        observation = _url_acquisition_observation()
        observation["benchmark_fixture_class"] = "golden-intents"
        self._expect_forbidden_field_rejection(observation)


class RegisterReadinessLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), log
        )
        forbidden = (
            READINESS_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        )
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)

    def test_forbidden_language_in_url_acquisition_note_halts(self):
        observation = _url_acquisition_observation()
        observation["url_acquisition_note"] = (
            "synthetic note carrying validation evidence sentinel"
        )
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInRegisterReadinessDiagnostic):
            run_scaffold_url_acquisition_register_readiness(observation, log)


class RegisterReadinessIsolationTest(unittest.TestCase):
    def test_does_not_mutate_input(self):
        observation = _url_acquisition_observation()
        before = copy.deepcopy(observation)
        run_scaffold_url_acquisition_register_readiness(
            observation, EventLog()
        )
        self.assertEqual(observation, before)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_url_acquisition_register_readiness(
                    _url_acquisition_observation(), EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class RegisterReadinessImportSurfaceTest(unittest.TestCase):
    def test_no_third_party_imports(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)
        for module_name in imports:
            self.assertTrue(
                module_name.startswith("harness."),
                "unexpected import in register-readiness diagnostic: "
                "{0}".format(module_name),
            )

    def test_module_has_no_file_io_network_or_hash_tokens(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for token in (
            "open(",
            "pathlib",
            "urllib",
            "http.client",
            "socket",
            "subprocess",
            "os.system",
            "shutil",
            "hashlib",
            ".hexdigest",
            ".sha256",
        ):
            self.assertNotIn(
                token,
                source_text,
                "unexpected IO / network / hash token: {0}".format(token),
            )
        for forbidden_use in (
            "import requests",
            "from requests",
            "requests.",
        ):
            self.assertNotIn(
                forbidden_use,
                source_text,
                "unexpected requests-library use: {0}".format(forbidden_use),
            )

    def test_module_does_not_invoke_wo55_or_wo61_public_functions(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for func in (
            "run_scaffold_source_intake_register",
            "run_scaffold_url_acquisition_executor",
        ):
            self.assertNotIn(
                func,
                source_text,
                "register-readiness module must not invoke {0}".format(func),
            )


class RegisterReadinessFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_readiness(self):
        def inventory():
            output = {}
            for root, _, filenames in os.walk(_BENCHMARK_FIXTURES_ROOT):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    rel = os.path.relpath(path, _BENCHMARK_FIXTURES_ROOT)
                    with open(path, "rb") as handle:
                        output[rel] = handle.read()
            return output

        before = inventory()
        run_scaffold_url_acquisition_register_readiness(
            _url_acquisition_observation(), EventLog()
        )
        after = inventory()
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
