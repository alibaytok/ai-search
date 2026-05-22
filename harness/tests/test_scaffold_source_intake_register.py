"""Tests for the WO-55 scaffold external-source reference quarantine register.

The tests exercise the upstream quarantine boundary that admits
already-loaded source reference dicts into an in-memory intake layer
while explicitly recording non-admission, non-qualification, and
non-route status. The same boundary as WO-50 / WO-51 / WO-52 / WO-53
/ WO-54 applies: no real retrieval call, no adapter invocation, no
network call, no file IO inside the module, no metrics, no ranking,
no architecture choice, and no benchmark readiness change. Hash is
identity / integrity only; it is never qualification.
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
from harness.scaffold_source_intake_register import (
    ALLOWED_DECLARED_KINDS,
    ALLOWED_OUTPUT_KEYS,
    ALLOWED_REFERENCE_FIELDS,
    BenchmarkFixtureFieldRejected,
    CorpusAdmissionFieldForbiddenAtRegisterLayer,
    DeclaredKindNotAllowed,
    DerivedMaterialForbiddenAtRegisterLayer,
    DuplicateSourceId,
    ForbiddenLanguageInSourceIntakeRegister,
    InvalidByteLength,
    InvalidHashField,
    MissingReferenceField,
    NonListSourceReferences,
    NonObjectSourceReference,
    QualificationRefFieldForbiddenAtRegisterLayer,
    QualifiedFieldForbiddenAtRegisterLayer,
    REGISTER_OUTPUT_FORBIDDEN_PHRASES,
    ROUTE_STATUS_BOOLEAN_KEYS,
    RouteFieldForbiddenAtRegisterLayer,
    RouteStatusClaimAtRegisterLayer,
    SourceCardShapedFieldRejected,
    UnknownReferenceField,
    run_scaffold_source_intake_register,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")
_MODULE_PATH = os.path.join(
    _PROJECT_ROOT, "harness", "scaffold_source_intake_register.py"
)


def _reference(
    suffix="001",
    declared_kind="prompt_collection",
    origin=None,
    hash_value=None,
    byte_length=2048,
    observed_at="2026-05-20T00:00:00Z",
):
    return {
        "source_id": "source-{0}".format(suffix),
        "origin": "synthetic-origin-{0}".format(suffix) if origin is None else origin,
        "declared_kind": declared_kind,
        "hash": "a" * 16 + "-{0}".format(suffix) if hash_value is None else hash_value,
        "byte_length": byte_length,
        "observed_at": observed_at,
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


class ScaffoldSourceIntakeRegisterCleanPassTest(unittest.TestCase):
    def test_clean_pass_with_prompt_skill_document_mix(self):
        refs = [
            _reference("001", declared_kind="prompt_collection"),
            _reference("002", declared_kind="skill_collection"),
            _reference("003", declared_kind="document_collection"),
        ]
        log = EventLog()
        output = run_scaffold_source_intake_register(refs, log)

        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 11)
        self.assertEqual(output["register_kind"], "scaffold_source_intake_register")
        self.assertEqual(output["references_observed_count"], 3)
        self.assertEqual(output["unique_origin_count"], 3)
        self.assertEqual(len(output["register_entries"]), 3)
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        self.assertFalse(log.has_halt())

    def test_authorization_readiness_selection_booleans_all_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_intake_register([_reference("001")], log)
        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)

    def test_empty_reference_list_allowed(self):
        log = EventLog()
        output = run_scaffold_source_intake_register([], log)
        self.assertEqual(output["references_observed_count"], 0)
        self.assertEqual(output["unique_origin_count"], 0)
        self.assertEqual(output["register_entries"], [])
        self.assertEqual(output["corpus_admitted_count"], 0)
        self.assertEqual(output["qualified_count"], 0)
        self.assertFalse(log.has_halt())

    def test_each_register_entry_has_corpus_admitted_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_intake_register(
            [_reference("001"), _reference("002")], log
        )
        for entry in output["register_entries"]:
            self.assertIs(entry["corpus_admitted"], False)

    def test_each_register_entry_has_qualified_literal_false(self):
        log = EventLog()
        output = run_scaffold_source_intake_register(
            [_reference("001"), _reference("002")], log
        )
        for entry in output["register_entries"]:
            self.assertIs(entry["qualified"], False)

    def test_register_entries_carry_hash_prefix_not_full_hash(self):
        ref = _reference("001", hash_value="abcdef0123456789-FULL-HASH-CONTENT")
        log = EventLog()
        output = run_scaffold_source_intake_register([ref], log)
        entry = output["register_entries"][0]
        self.assertIn("hash_prefix", entry)
        self.assertNotIn("hash", entry)
        self.assertTrue(len(entry["hash_prefix"]) <= 16)
        rendered = json.dumps(output, sort_keys=True)
        self.assertNotIn("FULL-HASH-CONTENT", rendered)

    def test_register_passed_event_emitted_with_clean_counts(self):
        log = EventLog()
        output = run_scaffold_source_intake_register(
            [_reference("001"), _reference("002")], log
        )
        passed = [
            e
            for e in log.events
            if e["type"] == "scaffold_source_intake_register_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertEqual(
            passed[0]["references_observed_count"],
            output["references_observed_count"],
        )
        self.assertEqual(passed[0]["corpus_admitted_count"], 0)
        self.assertEqual(passed[0]["qualified_count"], 0)


class ScaffoldSourceIntakeRegisterShapeRejectionTest(unittest.TestCase):
    def test_non_list_source_references_rejected(self):
        log = EventLog()
        with self.assertRaises(NonListSourceReferences):
            run_scaffold_source_intake_register("not a list", log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_register_non_list_source_references",
            )
        )

    def test_non_object_reference_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectSourceReference):
            run_scaffold_source_intake_register(["not a dict"], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_register_non_object_reference"
            )
        )

    def test_missing_source_id_rejected(self):
        ref = _reference("001")
        del ref["source_id"]
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_missing_origin_rejected(self):
        ref = _reference("001")
        del ref["origin"]
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_missing_declared_kind_rejected(self):
        ref = _reference("001")
        del ref["declared_kind"]
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_missing_hash_rejected(self):
        ref = _reference("001")
        del ref["hash"]
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_missing_byte_length_rejected(self):
        ref = _reference("001")
        del ref["byte_length"]
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_missing_observed_at_rejected(self):
        ref = _reference("001")
        del ref["observed_at"]
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_unknown_field_rejected(self):
        ref = _reference("001")
        ref["mystery_field"] = "value"
        log = EventLog()
        with self.assertRaises(UnknownReferenceField):
            run_scaffold_source_intake_register([ref], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_register_unknown_field"
            )
        )

    def test_duplicate_source_id_rejected(self):
        log = EventLog()
        with self.assertRaises(DuplicateSourceId):
            run_scaffold_source_intake_register(
                [_reference("dup"), _reference("dup")], log
            )

    def test_invalid_declared_kind_rejected(self):
        ref = _reference("001", declared_kind="not_in_allowed_set")
        log = EventLog()
        with self.assertRaises(DeclaredKindNotAllowed):
            run_scaffold_source_intake_register([ref], log)

    def test_empty_hash_rejected_as_missing(self):
        ref = _reference("001", hash_value="")
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_invalid_hash_non_string_rejected(self):
        ref = _reference("001")
        ref["hash"] = 12345
        log = EventLog()
        with self.assertRaises(MissingReferenceField):
            run_scaffold_source_intake_register([ref], log)

    def test_negative_byte_length_rejected(self):
        ref = _reference("001", byte_length=-1)
        log = EventLog()
        with self.assertRaises(InvalidByteLength):
            run_scaffold_source_intake_register([ref], log)

    def test_non_int_byte_length_rejected(self):
        ref = _reference("001")
        ref["byte_length"] = "1024"
        log = EventLog()
        with self.assertRaises(InvalidByteLength):
            run_scaffold_source_intake_register([ref], log)

    def test_bool_byte_length_rejected(self):
        ref = _reference("001")
        ref["byte_length"] = True
        log = EventLog()
        with self.assertRaises(InvalidByteLength):
            run_scaffold_source_intake_register([ref], log)


class ScaffoldSourceIntakeRegisterForbiddenFieldTest(unittest.TestCase):
    def test_qualified_field_rejected(self):
        ref = _reference("001")
        ref["qualified"] = True
        log = EventLog()
        with self.assertRaises(QualifiedFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_qualified_false_field_rejected_too(self):
        ref = _reference("001")
        ref["qualified"] = False
        log = EventLog()
        with self.assertRaises(QualifiedFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_qualification_ref_field_rejected(self):
        ref = _reference("001")
        ref["qualification_ref"] = "qual-001"
        log = EventLog()
        with self.assertRaises(QualificationRefFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_corpus_admitted_field_rejected(self):
        ref = _reference("001")
        ref["corpus_admitted"] = False
        log = EventLog()
        with self.assertRaises(CorpusAdmissionFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_extracted_material_field_rejected(self):
        ref = _reference("001")
        ref["extracted_material"] = {"text": "x"}
        log = EventLog()
        with self.assertRaises(DerivedMaterialForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_normalized_material_field_rejected(self):
        ref = _reference("001")
        ref["normalized_material"] = {"normalized_id": "n"}
        log = EventLog()
        with self.assertRaises(DerivedMaterialForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_candidate_fragments_field_rejected(self):
        ref = _reference("001")
        ref["candidate_fragments"] = []
        log = EventLog()
        with self.assertRaises(DerivedMaterialForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_candidate_route_fragments_field_rejected(self):
        ref = _reference("001")
        ref["candidate_route_fragments"] = []
        log = EventLog()
        with self.assertRaises(DerivedMaterialForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_candidate_workflow_fragments_field_rejected(self):
        ref = _reference("001")
        ref["candidate_workflow_fragments"] = []
        log = EventLog()
        with self.assertRaises(DerivedMaterialForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_route_field_rejected(self):
        ref = _reference("001")
        ref["route"] = "anything"
        log = EventLog()
        with self.assertRaises(RouteFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_route_id_field_rejected(self):
        ref = _reference("001")
        ref["route_id"] = "route-abc"
        log = EventLog()
        with self.assertRaises(RouteFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_route_state_field_rejected(self):
        ref = _reference("001")
        ref["route_state"] = "official"
        log = EventLog()
        with self.assertRaises(RouteFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_plane_field_rejected(self):
        ref = _reference("001")
        ref["plane"] = "official_route_results"
        log = EventLog()
        with self.assertRaises(RouteFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_official_field_rejected_regardless_of_value(self):
        ref = _reference("001")
        ref["official"] = False
        log = EventLog()
        with self.assertRaises(RouteFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_executable_field_rejected_regardless_of_value(self):
        ref = _reference("001")
        ref["executable"] = False
        log = EventLog()
        with self.assertRaises(RouteFieldForbiddenAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)


class ScaffoldSourceIntakeRegisterRouteStatusGuardTest(unittest.TestCase):
    def test_is_route_true_rejected_as_route_status_claim(self):
        ref = _reference("001")
        ref["is_route"] = True
        log = EventLog()
        with self.assertRaises(RouteStatusClaimAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_register_route_status_claim"
            )
        )

    def test_is_official_route_true_rejected(self):
        ref = _reference("001")
        ref["is_official_route"] = True
        log = EventLog()
        with self.assertRaises(RouteStatusClaimAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_selected_as_official_true_rejected(self):
        ref = _reference("001")
        ref["selected_as_official"] = True
        log = EventLog()
        with self.assertRaises(RouteStatusClaimAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_route_authorized_true_rejected(self):
        ref = _reference("001")
        ref["route_authorized"] = True
        log = EventLog()
        with self.assertRaises(RouteStatusClaimAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_production_route_true_rejected(self):
        ref = _reference("001")
        ref["production_route"] = True
        log = EventLog()
        with self.assertRaises(RouteStatusClaimAtRegisterLayer):
            run_scaffold_source_intake_register([ref], log)

    def test_is_route_false_falls_through_to_unknown_field(self):
        ref = _reference("001")
        ref["is_route"] = False
        log = EventLog()
        with self.assertRaises(UnknownReferenceField):
            run_scaffold_source_intake_register([ref], log)


class ScaffoldSourceIntakeRegisterSourceCardShapedTest(unittest.TestCase):
    def test_authority_field_rejected(self):
        ref = _reference("001")
        ref["authority"] = "anything"
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_trust_field_rejected(self):
        ref = _reference("001")
        ref["trust"] = 0.99
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_freshness_field_rejected(self):
        ref = _reference("001")
        ref["freshness"] = "recent"
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_ownership_field_rejected(self):
        ref = _reference("001")
        ref["ownership"] = "team"
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_source_card_field_rejected(self):
        ref = _reference("001")
        ref["source_card"] = {}
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_route_card_field_rejected(self):
        ref = _reference("001")
        ref["route_card"] = {}
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_qualification_evidence_field_rejected(self):
        ref = _reference("001")
        ref["qualification_evidence"] = "x"
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_validation_evidence_field_rejected(self):
        ref = _reference("001")
        ref["validation_evidence"] = "x"
        log = EventLog()
        with self.assertRaises(SourceCardShapedFieldRejected):
            run_scaffold_source_intake_register([ref], log)


class ScaffoldSourceIntakeRegisterBenchmarkFixtureShapedTest(unittest.TestCase):
    def test_benchmark_fixture_class_field_rejected(self):
        ref = _reference("001")
        ref["benchmark_fixture_class"] = "golden-intents"
        log = EventLog()
        with self.assertRaises(BenchmarkFixtureFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_golden_intent_field_rejected(self):
        ref = _reference("001")
        ref["golden_intent"] = True
        log = EventLog()
        with self.assertRaises(BenchmarkFixtureFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_hard_negative_field_rejected(self):
        ref = _reference("001")
        ref["hard_negative"] = True
        log = EventLog()
        with self.assertRaises(BenchmarkFixtureFieldRejected):
            run_scaffold_source_intake_register([ref], log)

    def test_boundary_violation_field_rejected(self):
        ref = _reference("001")
        ref["boundary_violation"] = True
        log = EventLog()
        with self.assertRaises(BenchmarkFixtureFieldRejected):
            run_scaffold_source_intake_register([ref], log)


class ScaffoldSourceIntakeRegisterHashIsNotQualificationTest(unittest.TestCase):
    def test_hash_presence_does_not_imply_qualification(self):
        ref = _reference("001", hash_value="non-empty-hash")
        log = EventLog()
        output = run_scaffold_source_intake_register([ref], log)
        self.assertEqual(output["qualified_count"], 0)
        for entry in output["register_entries"]:
            self.assertIs(entry["qualified"], False)

    def test_hash_presence_does_not_imply_corpus_admission(self):
        ref = _reference("001", hash_value="non-empty-hash")
        log = EventLog()
        output = run_scaffold_source_intake_register([ref], log)
        self.assertEqual(output["corpus_admitted_count"], 0)
        for entry in output["register_entries"]:
            self.assertIs(entry["corpus_admitted"], False)

    def test_distinct_hashes_do_not_change_booleans(self):
        refs = [
            _reference("001", hash_value="hash-aaa"),
            _reference("002", hash_value="hash-bbb"),
            _reference("003", hash_value="hash-ccc"),
        ]
        log = EventLog()
        output = run_scaffold_source_intake_register(refs, log)
        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)
        self.assertEqual(output["qualified_count"], 0)
        self.assertEqual(output["corpus_admitted_count"], 0)


class ScaffoldSourceIntakeRegisterOriginNotFetchedTest(unittest.TestCase):
    def test_origin_is_not_echoed_into_intake_note(self):
        sentinel = "synthetic-WO55-ORIGIN-SENTINEL-AAA"
        ref = _reference("001", origin=sentinel)
        log = EventLog()
        output = run_scaffold_source_intake_register([ref], log)
        self.assertNotIn(sentinel, output["intake_note"])

    def test_origin_counted_for_uniqueness_only(self):
        refs = [
            _reference("001", origin="origin-shared"),
            _reference("002", origin="origin-shared"),
            _reference("003", origin="origin-distinct"),
        ]
        log = EventLog()
        output = run_scaffold_source_intake_register(refs, log)
        self.assertEqual(output["unique_origin_count"], 2)
        self.assertEqual(output["references_observed_count"], 3)

    def test_origin_not_appearing_in_register_entry_output(self):
        sentinel = "synthetic-WO55-ORIGIN-SENTINEL-BBB"
        ref = _reference("001", origin=sentinel)
        log = EventLog()
        output = run_scaffold_source_intake_register([ref], log)
        rendered = json.dumps(output["register_entries"], sort_keys=True)
        self.assertNotIn(sentinel, rendered)


class ScaffoldSourceIntakeRegisterLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_source_intake_register(
            [_reference("001"), _reference("002")], log
        )
        forbidden = REGISTER_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)


class ScaffoldSourceIntakeRegisterIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_inputs(self):
        refs = [_reference("001"), _reference("002")]
        before = copy.deepcopy(refs)
        run_scaffold_source_intake_register(refs, EventLog())
        self.assertEqual(refs, before)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_source_intake_register(
                    [_reference("001")], EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class ScaffoldSourceIntakeRegisterImportSurfaceTest(unittest.TestCase):
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
                "unexpected import in source-intake register: {0}".format(
                    module_name
                ),
            )

    def test_module_makes_no_file_io_or_network_call(self):
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
        ):
            self.assertNotIn(
                forbidden_token,
                source_text,
                "unexpected IO / network token in source-intake register: "
                "{0}".format(forbidden_token),
            )

    def test_module_does_not_use_hashlib_to_compute_hash(self):
        with open(_MODULE_PATH, "r", encoding="utf-8") as handle:
            source_text = handle.read()
        for forbidden_token in ("hashlib", ".hexdigest", ".sha256"):
            self.assertNotIn(
                forbidden_token,
                source_text,
                "unexpected hash-computation token in source-intake "
                "register: {0}".format(forbidden_token),
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


class ScaffoldSourceIntakeRegisterFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_register(self):
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
        run_scaffold_source_intake_register(
            [_reference("001"), _reference("002")], EventLog()
        )
        after = inventory()
        self.assertEqual(after, before)


class ScaffoldSourceIntakeRegisterConstantsTest(unittest.TestCase):
    def test_allowed_reference_fields_are_exact_six(self):
        self.assertEqual(
            ALLOWED_REFERENCE_FIELDS,
            frozenset(
                (
                    "source_id",
                    "origin",
                    "declared_kind",
                    "hash",
                    "byte_length",
                    "observed_at",
                )
            ),
        )

    def test_allowed_declared_kinds_match_packet(self):
        self.assertEqual(
            ALLOWED_DECLARED_KINDS,
            frozenset(
                (
                    "prompt_collection",
                    "skill_collection",
                    "agent_description_collection",
                    "tool_description_collection",
                    "document_collection",
                )
            ),
        )

    def test_route_status_boolean_keys_include_packet_required_markers(self):
        for required_key in (
            "official",
            "is_route",
            "is_official_route",
            "selected_as_official",
            "official_route_authorized",
            "route_authorized",
            "production_route",
            "selected_route",
            "executable",
        ):
            self.assertIn(required_key, ROUTE_STATUS_BOOLEAN_KEYS)


if __name__ == "__main__":
    unittest.main()
