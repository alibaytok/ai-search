"""Tests for the WO-54 scaffold source-intake trace.

The tests exercise the read-only path from a captured user prompt
(a non-empty string) through external source records to candidate
route and workflow fragments while preserving the route-first
invariants. The same boundary as WO-47 / WO-48 / WO-50 / WO-51 /
WO-52 / WO-53 applies: no real retrieval call, no adapter
invocation, no metrics, no ranking, no architecture choice, and no
benchmark readiness change.
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
from harness.scaffold_source_intake_trace import (
    ALLOWED_FRAGMENT_KINDS,
    ALLOWED_OUTPUT_KEYS,
    ALLOWED_SOURCE_ORIGIN,
    CandidateFragmentClaimsRouteStatus,
    CandidateFragmentDerivationMismatch,
    CandidateFragmentForbiddenKind,
    CandidateFragmentNotCandidateOnly,
    CandidateFragmentsWithoutNormalization,
    DuplicateSourceId,
    EmptyInputPrompt,
    ExtractedMaterialClaimsRouteStatus,
    ForbiddenLanguageInSourceIntakeTrace,
    MissingFragmentField,
    MissingQualificationRef,
    MissingSourceField,
    MissingSourceId,
    NonListSourceRecords,
    NonObjectCandidateFragment,
    NonObjectSourceRecord,
    NonStringInputPrompt,
    NormalizationClaimsRouteStatus,
    NormalizationWithoutExtraction,
    OFFICIAL_ROUTE_PLANE_VALUE,
    OFFICIAL_ROUTE_STATE_VALUE,
    QualificationGate,
    ROUTE_STATUS_CLAIM_BOOLEAN_KEYS,
    SourceClaimsRouteStatus,
    SourceOriginNotExternal,
    TRACE_OUTPUT_FORBIDDEN_PHRASES,
    run_scaffold_source_intake_trace,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")


_PROMPT = (
    "How does the synthetic WO-54 trace handle a captured prompt against "
    "an external source collection?"
)


def _prompt_source(
    suffix="001",
    fragment_kind="candidate_workflow",
    fragment_id=None,
    normalized_id=None,
    source_kind="prompt_collection",
    extra_text=None,
):
    norm = normalized_id or "norm-{0}".format(suffix)
    frag = fragment_id or "frag-{0}".format(suffix)
    return {
        "source_id": "source-{0}".format(suffix),
        "source_kind": source_kind,
        "source_origin": "external",
        "qualified": True,
        "qualification_ref": "qual-{0}".format(suffix),
        "extracted_material": {
            "material_id": "mat-{0}".format(suffix),
            "raw_artifact_kind": "prompt",
            "text": extra_text or "SYNTHETIC-WO54-RAW-{0}".format(suffix),
        },
        "normalized_material": {
            "normalized_id": norm,
            "intent_family": "repo_review",
            "capability_tags": ["contract_review", "test_review"],
        },
        "candidate_fragments": [
            {
                "fragment_id": frag,
                "fragment_kind": fragment_kind,
                "derived_from_normalized_id": norm,
                "candidate_only": True,
            }
        ],
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
    """The harness records halt events synchronously before raising. This
    helper verifies the most recent halt has the expected reason and is
    the final event in the log."""
    events = event_log.events
    self_halt = None
    for event in reversed(events):
        if event["type"] == "halt":
            self_halt = event
            break
    return self_halt is not None and self_halt["reason"] == halt_reason


class ScaffoldSourceIntakeTraceCleanPassTest(unittest.TestCase):
    def test_clean_pass_with_required_source_mix(self):
        prompt_source = _prompt_source(
            "001",
            fragment_kind="candidate_route_fragment",
            fragment_id="frag-route-001",
            source_kind="prompt_collection",
        )
        skill_source = _prompt_source(
            "002",
            fragment_kind="candidate_workflow",
            fragment_id="frag-workflow-002",
            source_kind="skill_collection",
        )
        log = EventLog()
        output = run_scaffold_source_intake_trace(
            _PROMPT, [prompt_source, skill_source], log
        )

        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 15)
        self.assertEqual(output["trace_kind"], "scaffold_source_intake_trace")
        self.assertEqual(output["sources_touched_count"], 2)
        self.assertEqual(output["qualified_sources_count"], 2)
        self.assertEqual(len(output["normalized_material_refs"]), 2)
        self.assertEqual(len(output["candidate_route_fragments"]), 1)
        self.assertEqual(len(output["candidate_workflow_fragments"]), 1)
        self.assertEqual(output["rejected_source_count"], 0)
        self.assertEqual(output["rejection_reasons"], [])
        self.assertFalse(log.has_halt())

    def test_authorization_booleans_remain_false(self):
        log = EventLog()
        output = run_scaffold_source_intake_trace(
            _PROMPT, [_prompt_source("001")], log
        )
        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)

    def test_empty_source_records_allowed(self):
        log = EventLog()
        output = run_scaffold_source_intake_trace(_PROMPT, [], log)
        self.assertEqual(output["sources_touched_count"], 0)
        self.assertEqual(output["qualified_sources_count"], 0)
        self.assertEqual(output["normalized_material_refs"], [])
        self.assertEqual(output["candidate_route_fragments"], [])
        self.assertEqual(output["candidate_workflow_fragments"], [])
        self.assertFalse(log.has_halt())

    def test_input_prompt_observed_is_structural_only(self):
        log = EventLog()
        output = run_scaffold_source_intake_trace(
            _PROMPT, [_prompt_source("001")], log
        )
        observed = output["input_prompt_observed"]
        self.assertIsInstance(observed, dict)
        self.assertIs(observed["observed"], True)
        self.assertEqual(
            observed["captured_intent_text_length"], len(_PROMPT)
        )
        rendered = json.dumps(output, sort_keys=True)
        self.assertNotIn(_PROMPT, rendered)

    def test_trace_passed_event_records_clean_counts(self):
        log = EventLog()
        output = run_scaffold_source_intake_trace(
            _PROMPT,
            [
                _prompt_source(
                    "001", fragment_kind="candidate_route_fragment",
                ),
                _prompt_source("002", fragment_kind="candidate_workflow"),
            ],
            log,
        )
        passed = [
            event
            for event in log.events
            if event["type"] == "scaffold_source_intake_trace_passed"
        ]
        self.assertEqual(len(passed), 1)
        self.assertEqual(passed[0]["sources_touched_count"], 2)
        self.assertEqual(
            passed[0]["candidate_route_fragments_count"],
            len(output["candidate_route_fragments"]),
        )
        self.assertEqual(
            passed[0]["candidate_workflow_fragments_count"],
            len(output["candidate_workflow_fragments"]),
        )


class ScaffoldSourceIntakeTraceRawTextLeakageTest(unittest.TestCase):
    def test_raw_extracted_text_not_in_route_or_workflow_fields(self):
        sentinel_a = "SYNTHETIC-WO54-RAW-SENTINEL-AAA-DO-NOT-LEAK"
        sentinel_b = "SYNTHETIC-WO54-RAW-SENTINEL-BBB-DO-NOT-LEAK"
        prompt_source = _prompt_source(
            "001",
            fragment_kind="candidate_route_fragment",
            extra_text=sentinel_a,
        )
        skill_source = _prompt_source(
            "002",
            fragment_kind="candidate_workflow",
            source_kind="skill_collection",
            extra_text=sentinel_b,
        )
        log = EventLog()
        output = run_scaffold_source_intake_trace(
            _PROMPT, [prompt_source, skill_source], log
        )

        for field_key in (
            "normalized_material_refs",
            "candidate_route_fragments",
            "candidate_workflow_fragments",
        ):
            rendered = json.dumps(output[field_key], sort_keys=True)
            self.assertNotIn(sentinel_a, rendered)
            self.assertNotIn(sentinel_b, rendered)

        full = json.dumps(output, sort_keys=True)
        self.assertNotIn(sentinel_a, full)
        self.assertNotIn(sentinel_b, full)


class ScaffoldSourceIntakeTraceInputPromptRejectionTest(unittest.TestCase):
    def test_non_string_input_prompt_rejected(self):
        log = EventLog()
        with self.assertRaises(NonStringInputPrompt):
            run_scaffold_source_intake_trace({"prompt": "x"}, [], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_non_string_input_prompt"
            )
        )

    def test_empty_input_prompt_rejected(self):
        log = EventLog()
        with self.assertRaises(EmptyInputPrompt):
            run_scaffold_source_intake_trace("", [], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_empty_input_prompt"
            )
        )


class ScaffoldSourceIntakeTraceSourceRejectionTest(unittest.TestCase):
    def test_non_list_source_records_rejected(self):
        log = EventLog()
        with self.assertRaises(NonListSourceRecords):
            run_scaffold_source_intake_trace(_PROMPT, "not a list", log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_non_list_source_records",
            )
        )

    def test_non_object_source_record_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectSourceRecord):
            run_scaffold_source_intake_trace(_PROMPT, ["not a dict"], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_non_object_source_record",
            )
        )

    def test_missing_source_id_rejected(self):
        source = _prompt_source("001")
        del source["source_id"]
        log = EventLog()
        with self.assertRaises(MissingSourceId):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_missing_source_id"
            )
        )

    def test_missing_other_source_field_rejected(self):
        source = _prompt_source("001")
        del source["source_origin"]
        log = EventLog()
        with self.assertRaises(MissingSourceField):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_missing_source_field"
            )
        )

    def test_source_origin_not_external_rejected(self):
        source = _prompt_source("001")
        source["source_origin"] = "internal"
        log = EventLog()
        with self.assertRaises(SourceOriginNotExternal):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_source_origin_not_external",
            )
        )

    def test_duplicate_source_id_rejected(self):
        log = EventLog()
        with self.assertRaises(DuplicateSourceId):
            run_scaffold_source_intake_trace(
                _PROMPT,
                [_prompt_source("dup"), _prompt_source("dup")],
                log,
            )
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_duplicate_source_id"
            )
        )

    def test_source_claims_route_status_rejected(self):
        source = _prompt_source("001")
        source["selected_as_official"] = True
        log = EventLog()
        with self.assertRaises(SourceClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_source_claims_route_status",
            )
        )


class ScaffoldSourceIntakeTraceQualificationGateTest(unittest.TestCase):
    def test_extracted_without_qualified_rejected(self):
        source = _prompt_source("001")
        source["qualified"] = False
        del source["normalized_material"]
        del source["candidate_fragments"]
        log = EventLog()
        with self.assertRaises(QualificationGate):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_qualification_gate"
            )
        )

    def test_normalized_without_qualified_rejected(self):
        source = _prompt_source("001")
        source["qualified"] = False
        del source["extracted_material"]
        del source["candidate_fragments"]
        log = EventLog()
        with self.assertRaises(QualificationGate):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_qualification_gate"
            )
        )

    def test_candidate_fragments_without_qualified_rejected(self):
        source = _prompt_source("001")
        source["qualified"] = False
        del source["extracted_material"]
        del source["normalized_material"]
        log = EventLog()
        with self.assertRaises(QualificationGate):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log, "scaffold_source_intake_trace_qualification_gate"
            )
        )

    def test_qualified_missing_qualification_ref_rejected(self):
        source = _prompt_source("001")
        source["qualification_ref"] = ""
        log = EventLog()
        with self.assertRaises(MissingQualificationRef):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_missing_qualification_ref",
            )
        )

    def test_bare_qualified_missing_qualification_ref_rejected(self):
        source = {
            "source_id": "source-bare-qualified",
            "source_kind": "prompt_collection",
            "source_origin": "external",
            "qualified": True,
        }
        log = EventLog()
        with self.assertRaises(MissingQualificationRef):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_missing_qualification_ref",
            )
        )

    def test_bare_unqualified_source_admitted(self):
        source = {
            "source_id": "source-bare",
            "source_kind": "document_collection",
            "source_origin": "external",
        }
        log = EventLog()
        output = run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertEqual(output["sources_touched_count"], 1)
        self.assertEqual(output["qualified_sources_count"], 0)
        self.assertEqual(output["normalized_material_refs"], [])


class ScaffoldSourceIntakeTraceLayeringRejectionTest(unittest.TestCase):
    def test_normalized_without_extraction_rejected(self):
        source = _prompt_source("001")
        del source["extracted_material"]
        log = EventLog()
        with self.assertRaises(NormalizationWithoutExtraction):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_normalization_without_extraction",
            )
        )

    def test_candidate_fragments_without_normalization_rejected(self):
        source = _prompt_source("001")
        del source["normalized_material"]
        log = EventLog()
        with self.assertRaises(CandidateFragmentsWithoutNormalization):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_candidate_fragments_without_normalization",
            )
        )


class ScaffoldSourceIntakeTraceExtractedMaterialClaimsRouteStatusTest(
    unittest.TestCase
):
    def test_extracted_material_route_state_official_rejected(self):
        source = _prompt_source("001")
        source["extracted_material"]["route_state"] = OFFICIAL_ROUTE_STATE_VALUE
        log = EventLog()
        with self.assertRaises(ExtractedMaterialClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_extracted_material_claims_route_status",
            )
        )

    def test_extracted_material_plane_official_results_rejected(self):
        source = _prompt_source("001")
        source["extracted_material"]["plane"] = OFFICIAL_ROUTE_PLANE_VALUE
        log = EventLog()
        with self.assertRaises(ExtractedMaterialClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_extracted_material_claims_route_status",
            )
        )

    def test_extracted_material_executable_true_rejected(self):
        source = _prompt_source("001")
        source["extracted_material"]["executable"] = True
        log = EventLog()
        with self.assertRaises(ExtractedMaterialClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_extracted_material_claims_route_status",
            )
        )


class ScaffoldSourceIntakeTraceNormalizationClaimsRouteStatusTest(
    unittest.TestCase
):
    def test_normalization_claims_route_status_rejected(self):
        source = _prompt_source("001")
        source["normalized_material"]["is_route"] = True
        log = EventLog()
        with self.assertRaises(NormalizationClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_normalization_claims_route_status",
            )
        )


class ScaffoldSourceIntakeTraceCandidateFragmentRejectionTest(unittest.TestCase):
    def test_non_object_candidate_fragment_rejected(self):
        source = _prompt_source("001")
        source["candidate_fragments"] = ["not a dict"]
        log = EventLog()
        with self.assertRaises(NonObjectCandidateFragment):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_non_object_candidate_fragment",
            )
        )

    def test_missing_fragment_field_rejected(self):
        source = _prompt_source("001")
        del source["candidate_fragments"][0]["fragment_kind"]
        log = EventLog()
        with self.assertRaises(MissingFragmentField):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_missing_fragment_field",
            )
        )

    def test_candidate_fragment_not_candidate_only_rejected(self):
        source = _prompt_source("001")
        source["candidate_fragments"][0]["candidate_only"] = False
        log = EventLog()
        with self.assertRaises(CandidateFragmentNotCandidateOnly):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_fragment_not_candidate_only",
            )
        )

    def test_candidate_fragment_forbidden_kind_rejected(self):
        source = _prompt_source("001")
        source["candidate_fragments"][0]["fragment_kind"] = "official_route"
        log = EventLog()
        with self.assertRaises(CandidateFragmentForbiddenKind):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_fragment_forbidden_kind",
            )
        )

    def test_candidate_fragment_derivation_mismatch_rejected(self):
        source = _prompt_source("001")
        source["candidate_fragments"][0][
            "derived_from_normalized_id"
        ] = "norm-mismatched"
        log = EventLog()
        with self.assertRaises(CandidateFragmentDerivationMismatch):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_fragment_derivation_mismatch",
            )
        )

    def test_candidate_fragment_official_boolean_rejected(self):
        source = _prompt_source("001")
        source["candidate_fragments"][0]["official"] = True
        log = EventLog()
        with self.assertRaises(CandidateFragmentClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_fragment_claims_route_status",
            )
        )

    def test_candidate_fragment_route_state_official_rejected(self):
        source = _prompt_source("001")
        source["candidate_fragments"][0][
            "route_state"
        ] = OFFICIAL_ROUTE_STATE_VALUE
        log = EventLog()
        with self.assertRaises(CandidateFragmentClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_fragment_claims_route_status",
            )
        )

    def test_candidate_fragment_plane_official_results_rejected(self):
        source = _prompt_source("001")
        source["candidate_fragments"][0]["plane"] = OFFICIAL_ROUTE_PLANE_VALUE
        log = EventLog()
        with self.assertRaises(CandidateFragmentClaimsRouteStatus):
            run_scaffold_source_intake_trace(_PROMPT, [source], log)
        self.assertTrue(
            _halt_came_before_raise(
                log,
                "scaffold_source_intake_trace_fragment_claims_route_status",
            )
        )


class ScaffoldSourceIntakeTraceLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        log = EventLog()
        output = run_scaffold_source_intake_trace(
            _PROMPT, [_prompt_source("001")], log
        )
        forbidden = TRACE_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)


class ScaffoldSourceIntakeTraceIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_inputs(self):
        sources = [_prompt_source("001"), _prompt_source("002")]
        before_sources = copy.deepcopy(sources)
        run_scaffold_source_intake_trace(_PROMPT, sources, EventLog())
        self.assertEqual(sources, before_sources)

    def test_function_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_source_intake_trace(
                    _PROMPT, [_prompt_source("001")], EventLog()
                )
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class ScaffoldSourceIntakeTraceImportSurfaceTest(unittest.TestCase):
    def test_no_third_party_imports(self):
        path = os.path.join(
            _PROJECT_ROOT, "harness", "scaffold_source_intake_trace.py"
        )
        with open(path, "r", encoding="utf-8") as handle:
            source_text = handle.read()
            tree = ast.parse(source_text)

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module)

        for module_name in imports:
            self.assertTrue(
                module_name.startswith("harness."),
                "unexpected import in source-intake trace: {0}".format(
                    module_name
                ),
            )

    def test_module_makes_no_file_io_or_network_call(self):
        path = os.path.join(
            _PROJECT_ROOT, "harness", "scaffold_source_intake_trace.py"
        )
        with open(path, "r", encoding="utf-8") as handle:
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
                "unexpected IO / network token in source-intake trace: "
                "{0}".format(forbidden_token),
            )


class ScaffoldSourceIntakeTraceFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_trace(self):
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
        run_scaffold_source_intake_trace(
            _PROMPT,
            [_prompt_source("001"), _prompt_source("002")],
            EventLog(),
        )
        after = inventory()
        self.assertEqual(after, before)


class ScaffoldSourceIntakeTraceConstantsTest(unittest.TestCase):
    def test_route_status_boolean_keys_include_packet_required_markers(self):
        for required_key in ("official", "executable"):
            self.assertIn(required_key, ROUTE_STATUS_CLAIM_BOOLEAN_KEYS)

    def test_official_route_state_value_matches_packet(self):
        self.assertEqual(OFFICIAL_ROUTE_STATE_VALUE, "official")

    def test_official_route_plane_value_matches_packet(self):
        self.assertEqual(OFFICIAL_ROUTE_PLANE_VALUE, "official_route_results")

    def test_allowed_source_origin_is_external(self):
        self.assertEqual(ALLOWED_SOURCE_ORIGIN, "external")

    def test_allowed_fragment_kinds_are_packet_required_pair(self):
        self.assertEqual(
            set(ALLOWED_FRAGMENT_KINDS),
            {"candidate_route_fragment", "candidate_workflow"},
        )


if __name__ == "__main__":
    unittest.main()
