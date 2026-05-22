"""Tests for the WO-52 scaffold conflicting-evidence guard.

The tests exercise structural contradiction detection inside the
admitted WO-31 synthetic fixture entries. The same boundary as
WO-47 / WO-48 / WO-50 / WO-51 applies: no real retrieval call, no
adapter invocation, no metrics, no ranking, no architecture choice,
and no benchmark readiness change. The five declared conflict kinds
are not a claim of completeness.
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
from harness.scaffold_conflicting_evidence_guard import (
    ALLOWED_OUTPUT_KEYS,
    BoundaryViolationBothValidAndForbidden,
    BoundaryViolationExpectedHaltWithoutClassification,
    BoundaryViolationOfficialPlaneWithoutCollapse,
    DECLARED_CONFLICT_KINDS,
    ForbiddenLanguageInConflictingEvidenceGuard,
    GUARD_OUTPUT_FORBIDDEN_PHRASES,
    GoldenMissWithOfficialRouteReference,
    GoldenOfficialReferenceWithMissClassification,
    GoldenOfficialWithExpectedHalt,
    HardNegativeAllowsOfficialDespiteGuard,
    HardNegativeCandidateOnlyWithoutCandidateOrNormalizedPlane,
    MissingOrNonListEntries,
    MissingRequiredPayloadClass,
    NonObjectPayloadsByClass,
    PayloadClassMismatch,
    REQUIRED_PAYLOAD_CLASSES,
    run_scaffold_conflicting_evidence_guard,
)


_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")


def _load_payload(class_name):
    path = os.path.join(
        _BENCHMARK_FIXTURES_ROOT, class_name, "wave-001.json"
    )
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_all_payloads():
    return {cls: _load_payload(cls) for cls in REQUIRED_PAYLOAD_CLASSES}


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


class ScaffoldConflictingEvidenceGuardSuccessTest(unittest.TestCase):
    def test_baseline_payloads_pass_with_expected_observation_shape(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_conflicting_evidence_guard(payloads, log)

        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(ALLOWED_OUTPUT_KEYS), 9)
        self.assertEqual(output["guard_kind"], "scaffold_conflicting_evidence_guard")
        self.assertEqual(output["inspected_entry_count"], 6)
        self.assertEqual(
            output["inspected_class_counts"],
            {"golden-intents": 2, "hard-negatives": 2, "boundary-violations": 2},
        )
        self.assertEqual(
            tuple(output["declared_conflict_kinds_checked"]),
            DECLARED_CONFLICT_KINDS,
        )
        self.assertFalse(log.has_halt())

    def test_authorization_booleans_remain_false(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_conflicting_evidence_guard(payloads, log)

        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)

    def test_run_end_event_records_expected_kinds_checked(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_conflicting_evidence_guard(payloads, log)

        end_events = [
            event
            for event in log.events
            if event["type"] == "scaffold_conflicting_evidence_guard_run_ended"
        ]
        self.assertEqual(len(end_events), 1)
        end_event = end_events[0]
        self.assertEqual(
            end_event["inspected_entry_count"], output["inspected_entry_count"]
        )
        self.assertEqual(
            end_event["inspected_class_counts"], output["inspected_class_counts"]
        )
        self.assertEqual(
            tuple(end_event["declared_conflict_kinds_checked"]),
            DECLARED_CONFLICT_KINDS,
        )

    def test_per_entry_inspected_events_recorded_in_class_then_entry_order(self):
        payloads = _load_all_payloads()
        log = EventLog()
        run_scaffold_conflicting_evidence_guard(payloads, log)

        inspected = [
            event
            for event in log.events
            if event["type"]
            == "scaffold_conflicting_evidence_guard_entry_inspected"
        ]
        self.assertEqual(len(inspected), 6)

        expected_order = []
        for class_name in REQUIRED_PAYLOAD_CLASSES:
            for entry in payloads[class_name]["entries"]:
                expected_order.append((class_name, entry["fixture_id"]))

        actual_order = [(e["class_name"], e["fixture_id"]) for e in inspected]
        self.assertEqual(actual_order, expected_order)


class ScaffoldConflictingEvidenceGuardConflictTest(unittest.TestCase):
    def test_golden_official_with_expected_halt_rejected(self):
        payloads = _load_all_payloads()
        payloads["golden-intents"]["entries"][0]["expected_disqualification"] = {
            "expected_halt": True,
            "halt_classification": "contract_check_failed",
        }
        log = EventLog()
        with self.assertRaises(GoldenOfficialWithExpectedHalt):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_golden_official_with_expected_halt",
        )

    def test_golden_official_reference_with_miss_classification_rejected(self):
        payloads = _load_all_payloads()
        payloads["golden-intents"]["entries"][0][
            "miss_classification"
        ] = "no_official_route_exists"
        log = EventLog()
        with self.assertRaises(GoldenOfficialReferenceWithMissClassification):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_golden_official_reference_with_miss_classification",
        )

    def test_hard_negative_allows_official_despite_guard_rejected(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"]["entries"][0]["plane_separation_markers"][
            "allowed_planes"
        ] = [
            "candidate_route_results",
            "normalized_material_support_results",
            "official_route_results",
        ]
        log = EventLog()
        with self.assertRaises(HardNegativeAllowsOfficialDespiteGuard):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_hard_negative_allows_official_despite_guard",
        )

    def test_boundary_violation_both_valid_and_forbidden_rejected(self):
        payloads = _load_all_payloads()
        payloads["boundary-violations"]["entries"][0]["expected_disqualification"][
            "is_valid_output"
        ] = True
        log = EventLog()
        with self.assertRaises(BoundaryViolationBothValidAndForbidden):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_boundary_violation_both_valid_and_forbidden",
        )

    def test_boundary_violation_official_plane_without_collapse_rejected(self):
        payloads = _load_all_payloads()
        del payloads["boundary-violations"]["entries"][0][
            "plane_separation_markers"
        ]["forbidden_plane_collapse"]
        log = EventLog()
        with self.assertRaises(BoundaryViolationOfficialPlaneWithoutCollapse):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_boundary_violation_official_plane_without_collapse",
        )

    def test_golden_miss_with_official_route_reference_rejected(self):
        payloads = _load_all_payloads()
        payloads["golden-intents"]["entries"][1][
            "expected_official_route_reference"
        ] = {
            "synthetic_route_identifier": "synthetic-route-id-B",
            "is_validation_evidence": False,
            "is_promotion_trigger": False,
        }
        del payloads["golden-intents"]["entries"][1]["miss_classification"]
        log = EventLog()
        with self.assertRaises(GoldenMissWithOfficialRouteReference):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_golden_miss_with_official_route_reference",
        )

    def test_hard_negative_candidate_only_without_candidate_or_normalized_plane_rejected(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"]["entries"][0]["plane_separation_markers"][
            "allowed_planes"
        ] = ["source_quality_constraint_observations"]
        log = EventLog()
        with self.assertRaises(
            HardNegativeCandidateOnlyWithoutCandidateOrNormalizedPlane
        ):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_hard_negative_candidate_only_without_candidate_or_normalized_plane",
        )

    def test_boundary_violation_expected_halt_without_classification_rejected(self):
        payloads = _load_all_payloads()
        del payloads["boundary-violations"]["entries"][0][
            "expected_disqualification"
        ]["halt_classification"]
        log = EventLog()
        with self.assertRaises(BoundaryViolationExpectedHaltWithoutClassification):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_boundary_violation_expected_halt_without_classification",
        )


class ScaffoldConflictingEvidenceGuardInputRejectionTest(unittest.TestCase):
    def test_non_object_payloads_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectPayloadsByClass):
            run_scaffold_conflicting_evidence_guard("not a dict", log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_non_object_input",
        )

    def test_missing_required_class_rejected(self):
        payloads = _load_all_payloads()
        del payloads["hard-negatives"]
        log = EventLog()
        with self.assertRaises(MissingRequiredPayloadClass):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_missing_required_class",
        )

    def test_payload_class_mismatch_rejected(self):
        payloads = _load_all_payloads()
        payloads["golden-intents"]["fixture_class"] = "hard-negatives"
        log = EventLog()
        with self.assertRaises(PayloadClassMismatch):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_class_mismatch",
        )

    def test_non_list_entries_rejected(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"]["entries"] = "not a list"
        log = EventLog()
        with self.assertRaises(MissingOrNonListEntries):
            run_scaffold_conflicting_evidence_guard(payloads, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_conflicting_evidence_guard_missing_or_non_list_entries",
        )


class ScaffoldConflictingEvidenceGuardLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_conflicting_evidence_guard(payloads, log)

        forbidden = GUARD_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)

    def test_forbidden_payload_surface_rejected_without_leaking_text(self):
        payloads = _load_all_payloads()
        payloads["golden-intents"]["entries"][0]["non_selection_posture"] = (
            "This entry is the best example among synthetic fixtures."
        )
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInConflictingEvidenceGuard):
            run_scaffold_conflicting_evidence_guard(payloads, log)

        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"],
            "scaffold_conflicting_evidence_guard_forbidden_language",
        )
        rendered_events = json.dumps(log.events, sort_keys=True)
        self.assertNotIn("best example among synthetic fixtures", rendered_events)


class ScaffoldConflictingEvidenceGuardIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_inputs(self):
        payloads = _load_all_payloads()
        before = copy.deepcopy(payloads)
        run_scaffold_conflicting_evidence_guard(payloads, EventLog())
        self.assertEqual(payloads, before)

    def test_function_writes_no_files(self):
        payloads = _load_all_payloads()
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_conflicting_evidence_guard(payloads, EventLog())
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class ScaffoldConflictingEvidenceGuardImportSurfaceTest(unittest.TestCase):
    def test_no_third_party_imports(self):
        path = os.path.join(
            _PROJECT_ROOT, "harness", "scaffold_conflicting_evidence_guard.py"
        )
        with open(path, "r", encoding="utf-8") as handle:
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
                "unexpected import in conflicting-evidence guard: {0}".format(
                    module_name
                ),
            )


class ScaffoldConflictingEvidenceGuardFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_guard(self):
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
        payloads = _load_all_payloads()
        run_scaffold_conflicting_evidence_guard(payloads, EventLog())
        after = inventory()
        self.assertEqual(after, before)
