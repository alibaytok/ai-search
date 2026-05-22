"""Tests for the WO-56 scaffold source register-to-trace admission bridge.

The tests exercise the pre-trace admission boundary between WO-55
(inert source reference quarantine register) and WO-54 (read-only
source-intake trace). The bridge consumes the WO-55 clean-pass output
shape plus a list of source record dicts and verifies cross-references
without admitting, qualifying, extracting, normalizing, or authorizing
any source. The bridge does not invoke either the WO-54 trace or the
WO-55 register; it operates on already-loaded values only.

The same boundary as WO-50 / WO-51 / WO-52 / WO-53 / WO-54 / WO-55
applies: no real retrieval call, no adapter invocation, no network
call, no file IO inside the module, no hash computation, no metrics,
no ranking, no architecture choice, and no benchmark readiness change.
"""

import ast
import copy
import json
import os
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_source_trace_admission_bridge import (
    ALLOWED_OUTPUT_KEYS,
    ALLOWED_SOURCE_ORIGIN,
    BRIDGE_OUTPUT_FORBIDDEN_PHRASES,
    DuplicateRegisterSourceId,
    DuplicateSourceId,
    EXPECTED_REGISTER_KIND,
    ForbiddenLanguageInSourceTraceAdmissionBridge,
    InvalidRegisterObservationShape,
    MissingSourceRecordField,
    NonListSourceRecords,
    NonObjectRegisterObservation,
    NonObjectSourceRecord,
    REGISTER_ENTRY_REQUIRED_FIELDS,
    ROUTE_STATUS_FIELDS,
    RegisterObservationDeclaresAuthorization,
    RegisterObservationDeclaresCorpusAdmission,
    RegisterObservationDeclaresQualification,
    SOURCE_RECORD_REQUIRED_FIELDS,
    SourceCardShapedFieldRejected,
    SourceKindRegisterKindMismatch,
    SourceOriginNotExternal,
    SourceRecordCarriesDerivedMaterial,
    SourceRecordCarriesQualificationRef,
    SourceRecordClaimsRouteStatus,
    SourceRecordDeclaresQualification,
    UnknownSourceRegisterRef,
    run_scaffold_source_trace_admission_bridge,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT, "harness", "scaffold_source_trace_admission_bridge.py"
)


def _register_entry(suffix="001", declared_kind="prompt_collection"):
    return {
        "source_id": "source-{0}".format(suffix),
        "declared_kind": declared_kind,
        "hash_prefix": "deadbeef{0}".format(suffix),
        "byte_length": 2048,
        "observed_at": "2026-05-20T00:00:00Z",
        "corpus_admitted": False,
        "qualified": False,
    }


def _register_observation(entries=None):
    if entries is None:
        entries = [_register_entry("001")]
    return {
        "register_kind": EXPECTED_REGISTER_KIND,
        "references_observed_count": len(entries),
        "unique_origin_count": len(entries),
        "register_entries": list(entries),
        "corpus_admitted_count": 0,
        "qualified_count": 0,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "intake_note": "synthetic register observation for WO-56 tests",
    }


def _source_record(suffix="001", declared_kind="prompt_collection"):
    return {
        "source_id": "source-{0}".format(suffix),
        "source_kind": declared_kind,
        "source_origin": "external",
        "source_register_ref": "source-{0}".format(suffix),
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


def _halt_came_before_raise(event_log, halt_reason):
    halt = _last_halt_event(event_log)
    return halt is not None and halt["reason"] == halt_reason


class BridgeCleanPassTest(unittest.TestCase):
    def test_clean_pass_with_prompt_skill_document_source_records(self):
        entries = [
            _register_entry("001", "prompt_collection"),
            _register_entry("002", "skill_collection"),
            _register_entry("003", "document_collection"),
        ]
        sources = [
            _source_record("001", "prompt_collection"),
            _source_record("002", "skill_collection"),
            _source_record("003", "document_collection"),
        ]
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(entries), sources, log
        )

        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 15)
        self.assertEqual(
            output["bridge_kind"], "scaffold_source_trace_admission_bridge"
        )
        self.assertEqual(output["register_entry_count"], 3)
        self.assertEqual(output["source_records_checked_count"], 3)
        self.assertEqual(output["linked_source_count"], 3)
        self.assertEqual(len(output["linked_sources"]), 3)
        self.assertFalse(log.has_halt())

    def test_all_authorization_readiness_selection_booleans_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], log
        )
        self.assertIs(output["extraction_authorized"], False)
        self.assertIs(output["normalization_authorized"], False)
        self.assertIs(output["candidate_derivation_authorized"], False)
        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)

    def test_corpus_admitted_and_qualified_counts_literal_zero(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], log
        )
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)

    def test_every_linked_source_has_corpus_admitted_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], log
        )
        for linked in output["linked_sources"]:
            self.assertIs(linked["corpus_admitted"], False)

    def test_every_linked_source_has_qualified_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], log
        )
        for linked in output["linked_sources"]:
            self.assertIs(linked["qualified"], False)

    def test_every_linked_source_has_authorization_booleans_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], log
        )
        for linked in output["linked_sources"]:
            self.assertIs(linked["extraction_authorized"], False)
            self.assertIs(linked["normalization_authorized"], False)
            self.assertIs(linked["candidate_derivation_authorized"], False)

    def test_empty_source_records_allowed_when_register_has_entries(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(
                [_register_entry("001"), _register_entry("002")]
            ),
            [],
            log,
        )
        self.assertEqual(output["register_entry_count"], 2)
        self.assertEqual(output["source_records_checked_count"], 0)
        self.assertEqual(output["linked_source_count"], 0)
        self.assertEqual(output["linked_sources"], [])
        self.assertFalse(log.has_halt())

    def test_empty_register_with_empty_source_records_allowed(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation([]), [], log
        )
        self.assertEqual(output["register_entry_count"], 0)
        self.assertEqual(output["source_records_checked_count"], 0)
        self.assertEqual(output["linked_source_count"], 0)
        self.assertFalse(log.has_halt())

    def test_passed_event_records_clean_counts(self):
        log = EventLog()
        run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], log
        )
        passed = [
            e
            for e in log.events
            if e["type"] == "scaffold_source_trace_admission_bridge_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["corpus_admitted_count"], 0)
        self.assertEqual(passed[0]["qualified_count"], 0)


class BridgeRegisterObservationRejectionTest(unittest.TestCase):
    def test_non_object_register_observation_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectRegisterObservation):
            run_scaffold_source_trace_admission_bridge("not a dict", [], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_trace_admission_bridge_non_object_register_observation",
            )
        )

    def test_invalid_register_kind_rejected(self):
        obs = _register_observation()
        obs["register_kind"] = "something-else"
        log = EventLog()
        with self.assertRaises(InvalidRegisterObservationShape):
            run_scaffold_source_trace_admission_bridge(obs, [], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_trace_admission_bridge_invalid_register_kind",
            )
        )

    def test_missing_register_entries_rejected(self):
        obs = _register_observation()
        del obs["register_entries"]
        log = EventLog()
        with self.assertRaises(InvalidRegisterObservationShape):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_entry_corpus_admitted_true_rejected(self):
        entry = _register_entry("001")
        entry["corpus_admitted"] = True
        obs = _register_observation([entry])
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresCorpusAdmission):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_entry_qualified_true_rejected(self):
        entry = _register_entry("001")
        entry["qualified"] = True
        obs = _register_observation([entry])
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresQualification):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_corpus_admitted_count_nonzero_rejected(self):
        obs = _register_observation()
        obs["corpus_admitted_count"] = 1
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresCorpusAdmission):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_qualified_count_nonzero_rejected(self):
        obs = _register_observation()
        obs["qualified_count"] = 1
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresQualification):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_selection_made_true_rejected(self):
        obs = _register_observation()
        obs["selection_made"] = True
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresAuthorization):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_measurement_authorized_true_rejected(self):
        obs = _register_observation()
        obs["measurement_authorized"] = True
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresAuthorization):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_real_benchmark_authorized_true_rejected(self):
        obs = _register_observation()
        obs["real_benchmark_authorized"] = True
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresAuthorization):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_real_benchmark_ready_true_rejected(self):
        obs = _register_observation()
        obs["real_benchmark_ready"] = True
        log = EventLog()
        with self.assertRaises(RegisterObservationDeclaresAuthorization):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_register_entry_missing_field_rejected(self):
        entry = _register_entry("001")
        del entry["declared_kind"]
        obs = _register_observation([entry])
        log = EventLog()
        with self.assertRaises(InvalidRegisterObservationShape):
            run_scaffold_source_trace_admission_bridge(obs, [], log)

    def test_duplicate_register_source_id_rejected(self):
        obs = _register_observation(
            [
                _register_entry("001", declared_kind="prompt_collection"),
                _register_entry("001", declared_kind="skill_collection"),
            ]
        )
        log = EventLog()
        with self.assertRaises(DuplicateRegisterSourceId):
            run_scaffold_source_trace_admission_bridge(obs, [], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_trace_admission_bridge_duplicate_register_source_id",
            )
        )


class BridgeSourceRecordShapeRejectionTest(unittest.TestCase):
    def test_non_list_source_records_rejected(self):
        log = EventLog()
        with self.assertRaises(NonListSourceRecords):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), "not a list", log
            )
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_trace_admission_bridge_non_list_source_records",
            )
        )

    def test_non_object_source_record_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectSourceRecord):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), ["not a dict"], log
            )

    def test_missing_source_id_rejected(self):
        src = _source_record()
        del src["source_id"]
        log = EventLog()
        with self.assertRaises(MissingSourceRecordField):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_missing_source_kind_rejected(self):
        src = _source_record()
        del src["source_kind"]
        log = EventLog()
        with self.assertRaises(MissingSourceRecordField):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_missing_source_origin_rejected(self):
        src = _source_record()
        del src["source_origin"]
        log = EventLog()
        with self.assertRaises(MissingSourceRecordField):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_missing_source_register_ref_rejected(self):
        src = _source_record()
        del src["source_register_ref"]
        log = EventLog()
        with self.assertRaises(MissingSourceRecordField):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_origin_not_external_rejected(self):
        src = _source_record()
        src["source_origin"] = "internal"
        log = EventLog()
        with self.assertRaises(SourceOriginNotExternal):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_duplicate_source_id_rejected(self):
        sources = [_source_record("001"), _source_record("001")]
        log = EventLog()
        with self.assertRaises(DuplicateSourceId):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), sources, log
            )

    def test_unknown_source_register_ref_rejected(self):
        src = _source_record("001")
        src["source_register_ref"] = "source-unknown"
        log = EventLog()
        with self.assertRaises(UnknownSourceRegisterRef):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_kind_register_kind_mismatch_rejected(self):
        src = _source_record("001", declared_kind="skill_collection")
        log = EventLog()
        with self.assertRaises(SourceKindRegisterKindMismatch):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(
                    [_register_entry("001", declared_kind="prompt_collection")]
                ),
                [src],
                log,
            )


class BridgeSourceRecordForbiddenFieldsTest(unittest.TestCase):
    def test_source_qualified_true_rejected(self):
        src = _source_record()
        src["qualified"] = True
        log = EventLog()
        with self.assertRaises(SourceRecordDeclaresQualification):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_qualified_false_also_rejected(self):
        src = _source_record()
        src["qualified"] = False
        log = EventLog()
        with self.assertRaises(SourceRecordDeclaresQualification):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_qualification_ref_rejected(self):
        src = _source_record()
        src["qualification_ref"] = "qual-001"
        log = EventLog()
        with self.assertRaises(SourceRecordCarriesQualificationRef):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_extracted_material_rejected(self):
        src = _source_record()
        src["extracted_material"] = {"text": "x"}
        log = EventLog()
        with self.assertRaises(SourceRecordCarriesDerivedMaterial):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_normalized_material_rejected(self):
        src = _source_record()
        src["normalized_material"] = {"normalized_id": "n"}
        log = EventLog()
        with self.assertRaises(SourceRecordCarriesDerivedMaterial):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_candidate_fragments_rejected(self):
        src = _source_record()
        src["candidate_fragments"] = []
        log = EventLog()
        with self.assertRaises(SourceRecordCarriesDerivedMaterial):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_route_id_rejected(self):
        src = _source_record()
        src["route_id"] = "route-abc"
        log = EventLog()
        with self.assertRaises(SourceRecordClaimsRouteStatus):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_official_true_rejected(self):
        src = _source_record()
        src["official"] = True
        log = EventLog()
        with self.assertRaises(SourceRecordClaimsRouteStatus):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_executable_field_rejected(self):
        src = _source_record()
        src["executable"] = False
        log = EventLog()
        with self.assertRaises(SourceRecordClaimsRouteStatus):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_route_state_rejected(self):
        src = _source_record()
        src["route_state"] = "official"
        log = EventLog()
        with self.assertRaises(SourceRecordClaimsRouteStatus):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_plane_rejected(self):
        src = _source_record()
        src["plane"] = "official_route_results"
        log = EventLog()
        with self.assertRaises(SourceRecordClaimsRouteStatus):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_is_route_true_rejected(self):
        src = _source_record()
        src["is_route"] = True
        log = EventLog()
        with self.assertRaises(SourceRecordClaimsRouteStatus):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_authority_rejected(self):
        src = _source_record()
        src["authority"] = "some-authority"
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_trust_rejected(self):
        src = _source_record()
        src["trust"] = 0.9
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )

    def test_source_validation_evidence_rejected(self):
        src = _source_record()
        src["validation_evidence"] = "x"
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_trace_admission_bridge(
                _register_observation(), [src], log
            )


class BridgeLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], log
        )
        forbidden = BRIDGE_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)


class BridgeIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_inputs(self):
        obs = _register_observation()
        sources = [_source_record()]
        before_obs = copy.deepcopy(obs)
        before_sources = copy.deepcopy(sources)

        run_scaffold_source_trace_admission_bridge(obs, sources, EventLog())

        self.assertEqual(obs, before_obs)
        self.assertEqual(sources, before_sources)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_source_trace_admission_bridge(
                    _register_observation(), [_source_record()], EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class BridgeImportSurfaceTest(unittest.TestCase):
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
                "unexpected import in admission bridge: {0}".format(module_name),
            )

    def test_module_makes_no_file_io_network_or_hash_call(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for forbidden_token in (
            "open(",
            "pathlib",
            "urllib",
            "requests",
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
                forbidden_token,
                source_text,
                "unexpected IO / network / hash token in admission bridge: "
                "{0}".format(forbidden_token),
            )

    def test_module_does_not_invoke_wo54_or_wo55_public_functions(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        self.assertNotIn(
            "run_scaffold_source_intake_trace",
            source_text,
            "admission bridge must not reference the WO-54 public function",
        )
        self.assertNotIn(
            "run_scaffold_source_intake_register",
            source_text,
            "admission bridge must not reference the WO-55 public function",
        )

    def test_module_does_not_use_retrieval_or_search_verbs_in_public_surface(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for verb in ("def query", "def search", "def retrieve", "def rank"):
            self.assertNotIn(
                verb,
                source_text,
                "unexpected retrieval/search verb in public surface: {0}".format(
                    verb
                ),
            )


class BridgeFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_bridge(self):
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
        run_scaffold_source_trace_admission_bridge(
            _register_observation(), [_source_record()], EventLog()
        )
        after = inventory()
        self.assertEqual(after, before)


class BridgeConstantsTest(unittest.TestCase):
    def test_expected_register_kind_matches_wo55(self):
        self.assertEqual(EXPECTED_REGISTER_KIND, "scaffold_source_intake_register")

    def test_register_entry_required_fields_match_packet(self):
        expected = (
            "source_id",
            "declared_kind",
            "hash_prefix",
            "byte_length",
            "observed_at",
            "corpus_admitted",
            "qualified",
        )
        self.assertEqual(REGISTER_ENTRY_REQUIRED_FIELDS, expected)

    def test_source_record_required_fields_match_packet(self):
        expected = (
            "source_id",
            "source_kind",
            "source_origin",
            "source_register_ref",
        )
        self.assertEqual(SOURCE_RECORD_REQUIRED_FIELDS, expected)

    def test_allowed_source_origin_is_external(self):
        self.assertEqual(ALLOWED_SOURCE_ORIGIN, "external")

    def test_route_status_fields_include_packet_required_markers(self):
        for required in (
            "route",
            "route_id",
            "route_state",
            "plane",
            "official",
            "executable",
            "is_route",
            "is_official_route",
            "selected_as_official",
            "official_route_authorized",
            "route_authorized",
            "production_route",
            "selected_route",
        ):
            self.assertIn(required, ROUTE_STATUS_FIELDS)


if __name__ == "__main__":
    unittest.main()
