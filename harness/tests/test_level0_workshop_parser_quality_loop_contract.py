"""Contract tests for parser-quality feedback and variant comparison.

These tests intentionally specify the next layer after the intent matrix
runner. They do not optimize parser behavior and they do not implement a
vocabulary corrector. The contract is: matrix failures must become bounded
feedback / upgrade-plan rows, and two parser result sets must be comparable
without modifying FRAME-A / FRAME-B / FRAME-C / FRAME-D code.
"""

import importlib
import os
import unittest


try:
    quality_loop = importlib.import_module(
        "harness.level0_workshop_parser_quality_loop"
    )
except ModuleNotFoundError:
    quality_loop = None


def _require_quality_loop(test_case):
    test_case.assertIsNotNone(
        quality_loop,
        "Missing target module: harness.level0_workshop_parser_quality_loop",
    )
    return quality_loop


def _case_result(
    case_id,
    match,
    classified_as,
    tags=None,
    differing_fields=None,
    expected_category="B. workflow intent",
    observed_category="H. no-route",
    expected_kinds=None,
    observed_kinds=None,
    expected_ambiguity=False,
    observed_ambiguity=False,
):
    return {
        "case_id": case_id,
        "match": match,
        "classified_as": classified_as,
        "observed_category": observed_category,
        "expected_category": expected_category,
        "observed_kinds": observed_kinds or ["none"],
        "expected_kinds": expected_kinds or ["workflow_file"],
        "observed_ambiguity": observed_ambiguity,
        "expected_ambiguity": expected_ambiguity,
        "observed_normalized_intent": "no_route",
        "expected_normalized_intent": "workflow_intent",
        "observed_candidate_surface": "no candidate surface expected",
        "expected_candidate_surface": "candidate fragment of declared shape",
        "observed_rejection_surface": "prompt_out_of_repo_scope",
        "expected_rejection_surface": "no_forced_selection",
        "differing_fields": differing_fields or ["category"],
        "tags": tags or ["contract"],
        "rationale": "synthetic contract fixture",
    }


def _matrix_result(case_results):
    passed_count = sum(1 for case in case_results if case["match"])
    failed_count = len(case_results) - passed_count
    return {
        "intent_test_matrix_runner_kind": (
            "level0_workshop_intent_test_matrix_runner"
        ),
        "matrix_id": "CONTRACT",
        "case_count": len(case_results),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "case_results": case_results,
        "per_failure_class_counts": {},
        "per_tag_counts": {},
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
        "runner_note": "synthetic contract fixture",
    }


class FeedbackPlannerContractTest(unittest.TestCase):
    """A failed matrix case must map to a bounded upgrade plan."""

    def test_upgrade_plan_field_contract(self):
        module = _require_quality_loop(self)
        expected = (
            "case_id",
            "failure_class",
            "likely_layer",
            "observed_fields",
            "expected_fields",
            "affected_tags",
            "suggested_upgrade_type",
            "suggested_next_packet_type",
            "patch_surface",
            "safety_tier",
            "risk_note",
            "precedent_dc_reference",
        )
        self.assertEqual(module.UPGRADE_PLAN_FIELDS, expected)

    def test_suggested_upgrade_type_contract_excludes_vocabulary(self):
        module = _require_quality_loop(self)
        self.assertIn("add_frame_b_canonical", module.SUGGESTED_UPGRADE_TYPES)
        self.assertIn("add_frame_c_shape_rule", module.SUGGESTED_UPGRADE_TYPES)
        self.assertIn(
            "add_ambiguity_clarification", module.SUGGESTED_UPGRADE_TYPES
        )
        self.assertIn("update_expected_case", module.SUGGESTED_UPGRADE_TYPES)
        self.assertNotIn("add_vocabulary_typo", module.SUGGESTED_UPGRADE_TYPES)
        self.assertNotIn(
            "vocabulary_correction_miss", module.SUGGESTED_UPGRADE_TYPES
        )

    def test_safety_tiers_are_proposal_only_or_forbidden(self):
        module = _require_quality_loop(self)
        self.assertEqual(module.SAFETY_TIERS, ("proposal_only", "forbidden"))

    def test_frame_b_canonical_gap_maps_to_frame_b_upgrade_plan(self):
        module = _require_quality_loop(self)
        plan = module.plan_upgrade_for_case_result(
            _case_result("C-FB", False, "frame_b_canonical_set_gap")
        )
        self.assertEqual(plan["case_id"], "C-FB")
        self.assertEqual(plan["likely_layer"], "FRAME-B")
        self.assertEqual(plan["suggested_upgrade_type"], "add_frame_b_canonical")
        self.assertEqual(plan["safety_tier"], "proposal_only")
        self.assertIn("SIGNAL_FAMILIES", plan["patch_surface"])

    def test_frame_c_synthesis_gap_maps_to_shape_rule_plan(self):
        module = _require_quality_loop(self)
        plan = module.plan_upgrade_for_case_result(
            _case_result("C-FC", False, "frame_c_synthesis_rule_gap")
        )
        self.assertEqual(plan["likely_layer"], "FRAME-C")
        self.assertEqual(plan["suggested_upgrade_type"], "add_frame_c_shape_rule")
        self.assertEqual(plan["safety_tier"], "proposal_only")

    def test_category_selector_gap_maps_to_category_rule_plan(self):
        module = _require_quality_loop(self)
        plan = module.plan_upgrade_for_case_result(
            _case_result("C-CAT", False, "frame_c_category_selector_gap")
        )
        self.assertEqual(plan["likely_layer"], "FRAME-C")
        self.assertEqual(
            plan["suggested_upgrade_type"], "add_frame_c_category_rule"
        )
        self.assertEqual(plan["safety_tier"], "proposal_only")

    def test_ambiguity_misreport_maps_to_clarification_plan(self):
        module = _require_quality_loop(self)
        plan = module.plan_upgrade_for_case_result(
            _case_result(
                "C-AMB",
                False,
                "frame_c_ambiguity_misreport",
                differing_fields=["ambiguity_observed"],
                expected_ambiguity=True,
                observed_ambiguity=False,
            )
        )
        self.assertEqual(plan["likely_layer"], "FRAME-C")
        self.assertEqual(
            plan["suggested_upgrade_type"], "add_ambiguity_clarification"
        )
        self.assertEqual(plan["safety_tier"], "proposal_only")
        self.assertEqual(plan["ambiguity_direction"], "underreport")

    def test_ambiguity_overreport_direction_is_bounded(self):
        module = _require_quality_loop(self)
        plan = module.plan_upgrade_for_case_result(
            _case_result(
                "C-AMB-OVER",
                False,
                "frame_c_ambiguity_misreport",
                differing_fields=["ambiguity_observed"],
                expected_ambiguity=False,
                observed_ambiguity=True,
            )
        )
        self.assertEqual(module.AMBIGUITY_DIRECTIONS, (
            "underreport", "overreport", "none",
        ))
        self.assertEqual(plan["ambiguity_direction"], "overreport")

    def test_expected_field_drift_maps_to_expected_case_update_plan(self):
        module = _require_quality_loop(self)
        plan = module.plan_upgrade_for_case_result(
            _case_result("C-DRIFT", False, "expected_field_drift")
        )
        self.assertEqual(plan["likely_layer"], "MATRIX")
        self.assertEqual(plan["suggested_upgrade_type"], "update_expected_case")
        self.assertEqual(plan["safety_tier"], "proposal_only")

    def test_forbidden_surface_maps_to_forbidden_tier(self):
        module = _require_quality_loop(self)
        plan = module.plan_upgrade_for_case_result(
            _case_result("C-FORBID", False, "unknown", tags=["route_selection"])
        )
        self.assertEqual(plan["safety_tier"], "forbidden")
        self.assertEqual(plan["suggested_upgrade_type"], "unknown")


class FeedbackReportContractTest(unittest.TestCase):
    """A matrix result must produce one upgrade plan per failed case."""

    def test_build_feedback_report_contains_failed_case_plans(self):
        module = _require_quality_loop(self)
        result = _matrix_result([
            _case_result("PASS", True, "match"),
            _case_result("FAIL-A", False, "frame_b_canonical_set_gap"),
            _case_result("FAIL-B", False, "frame_c_synthesis_rule_gap"),
        ])
        report = module.build_feedback_report(result)
        self.assertEqual(report["case_count"], 3)
        self.assertEqual(report["failed_count"], 2)
        self.assertEqual(
            [plan["case_id"] for plan in report["upgrade_plans"]],
            ["FAIL-A", "FAIL-B"],
        )
        self.assertEqual(
            report["per_upgrade_type_counts"]["add_frame_b_canonical"], 1
        )
        self.assertEqual(
            report["per_upgrade_type_counts"]["add_frame_c_shape_rule"], 1
        )
        self.assertIn("report_note", report)
        self.assertIs(report["real_benchmark_ready"], False)

    def test_build_feedback_report_rejects_missing_runner_kind(self):
        module = _require_quality_loop(self)
        result = _matrix_result([])
        del result["intent_test_matrix_runner_kind"]
        with self.assertRaises(module.ParserQualityLoopMalformedMatrixResult):
            module.build_feedback_report(result)

    def test_build_feedback_report_rejects_non_list_case_results(self):
        module = _require_quality_loop(self)
        result = _matrix_result([])
        result["case_results"] = "nope"
        with self.assertRaises(module.ParserQualityLoopMalformedMatrixResult):
            module.build_feedback_report(result)

    def test_plan_upgrade_rejects_unknown_failure_class(self):
        module = _require_quality_loop(self)
        with self.assertRaises(module.ParserQualityLoopUnknownFailureClass):
            module.plan_upgrade_for_case_result(
                _case_result("BAD", False, "not_a_failure_class")
            )

    def test_plan_upgrade_rejects_malformed_case_result(self):
        module = _require_quality_loop(self)
        malformed = _case_result("BAD", False, "unknown")
        del malformed["differing_fields"]
        with self.assertRaises(module.ParserQualityLoopMalformedCaseResult):
            module.plan_upgrade_for_case_result(malformed)


class VariantComparisonContractTest(unittest.TestCase):
    """Baseline and candidate parser result sets must be comparable."""

    def test_compare_result_sets_tracks_improvements_and_regressions(self):
        module = _require_quality_loop(self)
        baseline = _matrix_result([
            _case_result("IMPROVED", False, "frame_b_canonical_set_gap"),
            _case_result("REGRESSED", True, "match"),
            _case_result("UNCHANGED", False, "frame_c_synthesis_rule_gap"),
            _case_result("STABLE", True, "match"),
        ])
        candidate = _matrix_result([
            _case_result("IMPROVED", True, "match"),
            _case_result("REGRESSED", False, "frame_c_category_selector_gap"),
            _case_result("UNCHANGED", False, "frame_c_synthesis_rule_gap"),
            _case_result("STABLE", True, "match"),
        ])
        comparison = module.compare_parser_result_sets(baseline, candidate)
        self.assertEqual(comparison["improved_cases"], ["IMPROVED"])
        self.assertEqual(comparison["regressed_cases"], ["REGRESSED"])
        self.assertEqual(comparison["newly_failed_cases"], ["REGRESSED"])
        self.assertEqual(comparison["unchanged_failures"], ["UNCHANGED"])
        self.assertEqual(comparison["baseline_passed_count"], 2)
        self.assertEqual(comparison["candidate_passed_count"], 2)
        self.assertEqual(
            comparison["per_failure_class_delta"][
                "frame_b_canonical_set_gap"
            ],
            {"baseline": 1, "candidate": 0, "delta": -1},
        )
        self.assertEqual(
            comparison["per_failure_class_delta"][
                "frame_c_category_selector_gap"
            ],
            {"baseline": 0, "candidate": 1, "delta": 1},
        )
        self.assertEqual(
            comparison["per_tag_delta"]["contract"],
            {"baseline": 2, "candidate": 2, "delta": 0},
        )

    def test_compare_result_sets_preserves_baseline_order(self):
        module = _require_quality_loop(self)
        baseline = _matrix_result([
            _case_result("Z-FIRST", False, "frame_b_canonical_set_gap"),
            _case_result("A-SECOND", False, "frame_b_canonical_set_gap"),
        ])
        candidate = _matrix_result([
            _case_result("Z-FIRST", True, "match"),
            _case_result("A-SECOND", True, "match"),
        ])
        comparison = module.compare_parser_result_sets(baseline, candidate)
        self.assertEqual(
            comparison["improved_cases"], ["Z-FIRST", "A-SECOND"]
        )

    def test_compare_result_sets_rejects_case_id_mismatch(self):
        module = _require_quality_loop(self)
        baseline = _matrix_result([_case_result("A", True, "match")])
        candidate = _matrix_result([_case_result("B", True, "match")])
        with self.assertRaises(module.ParserVariantCaseSetMismatch):
            module.compare_parser_result_sets(baseline, candidate)


class StaticScanTest(unittest.TestCase):
    """The quality-loop module stays isolated from parser internals."""

    def _source(self):
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "harness",
            "level0_workshop_parser_quality_loop.py",
        )
        with open(path, "r", encoding="ascii") as handle:
            return handle.read()

    def test_module_does_not_import_parser_layers(self):
        source = self._source()
        self.assertNotIn("level0_workshop_normalized_prompt_view", source)
        self.assertNotIn("level0_workshop_signal_evidence", source)
        self.assertNotIn("level0_workshop_canonical_intent_frame", source)
        self.assertNotIn("level0_workshop_user_intent_mapper", source)

    def test_module_has_no_network_or_subprocess_imports(self):
        source = self._source()
        forbidden = ("subprocess", "socket", "urllib", "http.client")
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_module_imports_runner_bounded_constants(self):
        source = self._source()
        self.assertIn("from harness.level0_workshop_intent_test_matrix_runner", source)
        self.assertIn("FAILURE_CLASSES", source)
        self.assertIn("FORBIDDEN_CLAIM_PHRASES", source)


try:
    matrix_runner = importlib.import_module(
        "harness.level0_workshop_intent_test_matrix_runner"
    )
except ModuleNotFoundError:
    matrix_runner = None


try:
    event_log_module = importlib.import_module("harness.event_log")
except ModuleNotFoundError:
    event_log_module = None


_MINI_V1_MATRIX_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "harness",
    "intent_test_matrices",
    "L0-WS-PARSER-QUALITY-MINI-V1.intent.matrix.json",
)


class ParserQualityMiniV1EndToEndTest(unittest.TestCase):
    """Mini-V1 matrix flows through runner + quality loop end-to-end.

    Failures are expected and desired. The assertions verify only that
    the loop produces a well-shaped feedback report whose upgrade plans
    cover every failed case with bounded enum values. No parser pass-rate
    is asserted; this is review evidence, not a benchmark.
    """

    @classmethod
    def setUpClass(cls):
        if matrix_runner is None or quality_loop is None or event_log_module is None:
            cls.matrix_result = None
            cls.feedback_report = None
            return
        log = event_log_module.EventLog()
        cls.matrix_result = matrix_runner.run_intent_test_matrix(
            _MINI_V1_MATRIX_PATH, log
        )
        cls.feedback_report = quality_loop.build_feedback_report(
            cls.matrix_result
        )

    def _require_loaded(self):
        self.assertIsNotNone(matrix_runner, "matrix runner module missing")
        self.assertIsNotNone(quality_loop, "quality loop module missing")
        self.assertIsNotNone(event_log_module, "event_log module missing")
        self.assertIsNotNone(self.matrix_result, "matrix did not load")
        self.assertIsNotNone(self.feedback_report, "feedback report missing")

    def test_matrix_loads_with_expected_case_count(self):
        self._require_loaded()
        self.assertEqual(self.matrix_result["matrix_id"], "L0-WS-PARSER-QUALITY-MINI-V1")
        self.assertEqual(self.matrix_result["case_count"], 35)
        self.assertEqual(
            self.matrix_result["passed_count"]
            + self.matrix_result["failed_count"],
            self.matrix_result["case_count"],
        )

    def test_matrix_runner_gating_booleans_remain_false(self):
        self._require_loaded()
        for key in matrix_runner.GATING_BOOLEANS:
            self.assertIs(self.matrix_result[key], False)

    def test_feedback_report_covers_every_failed_case(self):
        self._require_loaded()
        failed_case_ids = [
            cr["case_id"]
            for cr in self.matrix_result["case_results"]
            if not cr["match"]
        ]
        plan_case_ids = [
            plan["case_id"]
            for plan in self.feedback_report["upgrade_plans"]
        ]
        self.assertEqual(failed_case_ids, plan_case_ids)
        self.assertEqual(
            len(self.feedback_report["upgrade_plans"]),
            self.matrix_result["failed_count"],
        )

    def test_upgrade_plan_fields_are_bounded_enum_values(self):
        self._require_loaded()
        for plan in self.feedback_report["upgrade_plans"]:
            self.assertIn(
                plan["failure_class"],
                set(matrix_runner.FAILURE_CLASSES) | {"unknown"},
            )
            self.assertIn(
                plan["likely_layer"], quality_loop.LIKELY_LAYERS
            )
            self.assertIn(
                plan["suggested_upgrade_type"],
                quality_loop.SUGGESTED_UPGRADE_TYPES,
            )
            self.assertIn(
                plan["suggested_next_packet_type"],
                quality_loop.SUGGESTED_NEXT_PACKET_TYPES,
            )
            self.assertIn(plan["safety_tier"], quality_loop.SAFETY_TIERS)
            for field in quality_loop.UPGRADE_PLAN_FIELDS:
                self.assertIn(field, plan)

    def test_feedback_report_excludes_vocabulary_upgrade_types(self):
        self._require_loaded()
        for upgrade_type in self.feedback_report["per_upgrade_type_counts"]:
            self.assertNotIn("vocabulary", upgrade_type)

    def test_per_upgrade_type_counts_keys_are_bounded(self):
        self._require_loaded()
        allowed = set(quality_loop.SUGGESTED_UPGRADE_TYPES)
        for upgrade_type in self.feedback_report["per_upgrade_type_counts"]:
            self.assertIn(upgrade_type, allowed)

    def test_failed_cases_classified_within_bounded_enum(self):
        self._require_loaded()
        allowed = set(matrix_runner.FAILURE_CLASSES) | {"match"}
        for cr in self.matrix_result["case_results"]:
            self.assertIn(cr["classified_as"], allowed)

    def test_feedback_report_gating_booleans_remain_false(self):
        self._require_loaded()
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
        ):
            self.assertIs(self.feedback_report[key], False)

    def test_mini_v1_epoch_3_all_cases_match(self):
        """Mini-V1 is now closed; new failures must re-enter through a
        bounded feedback candidate rather than silently changing shape."""
        self._require_loaded()
        self.assertEqual(self.matrix_result["passed_count"], 35)
        self.assertEqual(self.matrix_result["failed_count"], 0)

    def test_mini_v1_frame_c_synthesis_bucket_is_closed(self):
        self._require_loaded()
        self.assertEqual(
            self.matrix_result["per_failure_class_counts"][
                "frame_c_synthesis_rule_gap"
            ],
            0,
        )

    def test_no_forbidden_classifier_overrides_used(self):
        """The matrix relies on natural classifier behavior; no case may
        carry a `force_*` override tag that would bypass the heuristic."""
        self._require_loaded()
        override_tags = set(
            matrix_runner._TAG_CLASSIFIER_OVERRIDES.keys()
        )
        for cr in self.matrix_result["case_results"]:
            for tag in cr["tags"]:
                self.assertNotIn(tag, override_tags)


class UpgradeCandidatePlannerTest(unittest.TestCase):
    """Feedback reports must collapse into bounded review candidates."""

    @classmethod
    def setUpClass(cls):
        if matrix_runner is None or quality_loop is None or event_log_module is None:
            cls.matrix_result = None
            cls.feedback_report = None
            cls.candidates_result = None
            return
        log = event_log_module.EventLog()
        cls.matrix_result = matrix_runner.run_intent_test_matrix(
            _MINI_V1_MATRIX_PATH, log
        )
        cls.feedback_report = quality_loop.build_feedback_report(
            cls.matrix_result
        )
        cls.candidates_result = quality_loop.build_upgrade_candidates(
            cls.feedback_report
        )

    def _require_loaded(self):
        self.assertIsNotNone(matrix_runner, "matrix runner module missing")
        self.assertIsNotNone(quality_loop, "quality loop module missing")
        self.assertIsNotNone(event_log_module, "event_log module missing")
        self.assertIsNotNone(self.matrix_result, "matrix did not load")
        self.assertIsNotNone(self.feedback_report, "feedback report missing")
        self.assertIsNotNone(self.candidates_result, "planner result missing")

    def _candidate(self, failure_class, upgrade_type):
        self._require_loaded()
        for candidate in self.candidates_result["upgrade_candidates"]:
            if (
                candidate["failure_class"] == failure_class
                and candidate["suggested_upgrade_type"] == upgrade_type
            ):
                return candidate
        self.fail("candidate not found: {0}/{1}".format(
            failure_class, upgrade_type
        ))

    def test_upgrade_candidate_shape_and_gating_booleans(self):
        self._require_loaded()
        result = self.candidates_result
        expected_keys = {
            "upgrade_candidates_kind",
            "matrix_id",
            "case_count",
            "failed_count",
            "upgrade_candidates",
            "candidate_count",
            "execution_log",
            "planner_note",
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
            "variant_execution_authorized",
        }
        self.assertEqual(set(result), expected_keys)
        self.assertEqual(
            result["upgrade_candidates_kind"],
            "level0_workshop_upgrade_candidates",
        )
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
            "variant_execution_authorized",
        ):
            self.assertIs(result[key], False)

    def test_candidate_constants_are_bounded(self):
        module = _require_quality_loop(self)
        self.assertEqual(module.CANDIDATE_SAFETY_TIERS, (
            "proposal_only",
            "requires_reserved_layer",
            "forbidden",
        ))
        self.assertEqual(module.CANDIDATE_INTENTS, (
            "parser_improvement",
            "matrix_reconciliation",
            "reserved_layer_design_proposal",
            "requires_triage",
        ))
        self.assertEqual(module.EXPECTATION_DRIFT_RISKS, (
            "low", "medium", "high",
        ))
        self.assertEqual(module.PLANNER_EXECUTION_LOG_FIELDS, (
            "event_index",
            "step_index",
            "iteration",
            "stage",
            "status",
            "case_id",
            "candidate_id",
            "failure_class",
            "suggested_upgrade_type",
            "detail",
        ))
        self.assertEqual(module.CASE_REVIEW_LABELS, (
            "likely_matrix_expectation_drift",
            "likely_negation_gap",
            "likely_synthesis_gap",
            "needs_human_review",
        ))
        self.assertIn(
            ("FRAME-B", "add_frame_b_canonical"),
            module.PATCH_PLAN_TEMPLATES,
        )
        self.assertIn(
            "FRAME-B-COVERAGE", module.REQUIRED_TESTS_BY_NEXT_PACKET
        )

    def test_mini_v1_has_no_remaining_upgrade_candidates(self):
        self._require_loaded()
        self.assertEqual(self.candidates_result["candidate_count"], 0)
        self.assertEqual(self.candidates_result["upgrade_candidates"], [])

    def test_mini_v1_has_no_frame_b_canonical_candidate_after_materialization(self):
        self._require_loaded()
        candidate_keys = {
            (candidate["failure_class"], candidate["suggested_upgrade_type"])
            for candidate in self.candidates_result["upgrade_candidates"]
        }
        self.assertNotIn(
            ("frame_b_canonical_set_gap", "add_frame_b_canonical"),
            candidate_keys,
        )

    def test_mini_v1_has_no_matrix_drift_candidate_after_materialization(self):
        self._require_loaded()
        candidate_keys = {
            (candidate["failure_class"], candidate["suggested_upgrade_type"])
            for candidate in self.candidates_result["upgrade_candidates"]
        }
        self.assertNotIn(
            ("expected_field_drift", "update_expected_case"),
            candidate_keys,
        )

    def test_epoch_3_has_no_remaining_next_packet_type(self):
        """Epoch 3 closes Mini-V1; any future packet type must appear
        through a new failing case and an explicit contract update.

        The autonomous materializers are bounded to FRAME-B canonical table
        additions, matrix expected-field updates, and their composite. The
        authorized FRAME-C and clarification-semantics hardening passes have
        closed the remaining Mini-V1 buckets.
        """
        self._require_loaded()
        closed_next_packets = {
            "FRAME-B-COVERAGE",
            "MATRIX-RECONCILE",
            "FRAME-C-HARDEN",
            "CLARIFICATION-DESIGN",
        }
        remaining_next_packets = {
            candidate["suggested_next_packet_type"]
            for candidate in self.candidates_result["upgrade_candidates"]
        }
        self.assertEqual(remaining_next_packets, set())
        self.assertTrue(remaining_next_packets.isdisjoint(closed_next_packets))

    def test_candidate_order_and_ids_are_deterministic(self):
        self._require_loaded()
        candidates = self.candidates_result["upgrade_candidates"]
        self.assertEqual(
            [candidate["affected_count"] for candidate in candidates],
            [],
        )
        self.assertEqual(
            [candidate["candidate_id"] for candidate in candidates],
            [],
        )
        self.assertEqual(
            [candidate["failure_class"] for candidate in candidates],
            [],
        )

    def test_execution_log_is_ordered_by_step_and_iteration(self):
        self._require_loaded()
        log = self.candidates_result["execution_log"]
        self.assertEqual(
            [entry["event_index"] for entry in log],
            list(range(1, len(log) + 1)),
        )
        self.assertEqual(log[0]["stage"], "validate_feedback_report")
        self.assertEqual(log[0]["step_index"], 1)
        group_events = [
            entry for entry in log if entry["stage"] == "group_upgrade_plan"
        ]
        self.assertEqual(len(group_events), self.matrix_result["failed_count"])
        self.assertEqual(
            [entry["iteration"] for entry in group_events],
            list(range(1, self.matrix_result["failed_count"] + 1)),
        )
        build_events = [
            entry for entry in log if entry["stage"] == "build_upgrade_candidate"
        ]
        self.assertEqual(len(build_events), self.candidates_result["candidate_count"])
        assign_events = [
            entry for entry in log if entry["stage"] == "assign_candidate_id"
        ]
        self.assertEqual(
            [entry["candidate_id"] for entry in assign_events],
            [],
        )
        self.assertEqual(log[-1]["stage"], "scan_planner_output")

    def test_execution_log_entries_match_constant_fields(self):
        self._require_loaded()
        for entry in self.candidates_result["execution_log"]:
            self.assertEqual(
                tuple(entry), quality_loop.PLANNER_EXECUTION_LOG_FIELDS
            )

    def test_candidate_fields_match_constant_order(self):
        self._require_loaded()
        for candidate in self.candidates_result["upgrade_candidates"]:
            self.assertEqual(
                tuple(candidate), quality_loop.UPGRADE_CANDIDATE_FIELDS
            )

    def test_patch_plan_and_required_tests_are_constant_backed(self):
        self._require_loaded()
        for candidate in self.candidates_result["upgrade_candidates"]:
            key = (
                candidate["likely_layer"],
                candidate["suggested_upgrade_type"],
            )
            fallback = ("UNKNOWN", "unknown")
            self.assertIn(
                candidate["patch_plan_skeleton"],
                quality_loop.PATCH_PLAN_TEMPLATES.values(),
            )
            self.assertEqual(
                candidate["patch_plan_skeleton"],
                quality_loop.PATCH_PLAN_TEMPLATES.get(
                    key, quality_loop.PATCH_PLAN_TEMPLATES[fallback]
                ),
            )
            self.assertEqual(
                candidate["required_tests"],
                list(quality_loop.REQUIRED_TESTS_BY_NEXT_PACKET[
                    candidate["suggested_next_packet_type"]
                ]),
            )

    def test_build_upgrade_candidates_rejects_malformed_input(self):
        module = _require_quality_loop(self)
        with self.assertRaises(module.ParserQualityLoopMalformedFeedbackReport):
            module.build_upgrade_candidates("nope")
        report = {"parser_quality_feedback_kind": "wrong", "upgrade_plans": []}
        with self.assertRaises(module.ParserQualityLoopMalformedFeedbackReport):
            module.build_upgrade_candidates(report)
        report = {"parser_quality_feedback_kind": "level0_workshop_parser_quality_feedback"}
        with self.assertRaises(module.ParserQualityLoopMalformedFeedbackReport):
            module.build_upgrade_candidates(report)

    def test_planner_forbidden_phrase_scan_runs_before_return(self):
        module = _require_quality_loop(self)
        original = module.PLANNER_REPORT_NOTE
        try:
            module.PLANNER_REPORT_NOTE = "production-grade"
            with self.assertRaises(module.ParserQualityLoopForbiddenClaimPhrase):
                module.build_upgrade_candidates(self.feedback_report)
        finally:
            module.PLANNER_REPORT_NOTE = original

    def test_static_scan_has_no_new_parser_layer_imports(self):
        module = _require_quality_loop(self)
        path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "harness",
            "level0_workshop_parser_quality_loop.py",
        )
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        self.assertNotIn("level0_workshop_normalized_prompt_view", source)
        self.assertNotIn("level0_workshop_signal_evidence", source)
        self.assertNotIn("level0_workshop_canonical_intent_frame", source)
        self.assertNotIn("level0_workshop_user_intent_mapper", source)
        self.assertIn("build_upgrade_candidates", source)


class CandidateCaseReviewReporterTest(unittest.TestCase):
    """Upgrade candidates must split into bounded case-review labels."""

    @classmethod
    def setUpClass(cls):
        if matrix_runner is None or quality_loop is None or event_log_module is None:
            cls.matrix_result = None
            cls.feedback_report = None
            cls.planner_result = None
            cls.summary = None
            return
        log = event_log_module.EventLog()
        cls.matrix_result = matrix_runner.run_intent_test_matrix(
            _MINI_V1_MATRIX_PATH, log
        )
        cls.feedback_report = quality_loop.build_feedback_report(
            cls.matrix_result
        )
        cls.planner_result = quality_loop.build_upgrade_candidates(
            cls.feedback_report
        )
        cls.summary = quality_loop.build_candidate_review_summary(
            cls.planner_result, cls.matrix_result
        )

    def _require_loaded(self):
        self.assertIsNotNone(matrix_runner, "matrix runner module missing")
        self.assertIsNotNone(quality_loop, "quality loop module missing")
        self.assertIsNotNone(event_log_module, "event_log module missing")
        self.assertIsNotNone(self.matrix_result, "matrix did not load")
        self.assertIsNotNone(self.planner_result, "planner result missing")
        self.assertIsNotNone(self.summary, "review summary missing")

    def _candidate(self, candidate_id):
        self._require_loaded()
        for candidate in self.planner_result["upgrade_candidates"]:
            if candidate["candidate_id"] == candidate_id:
                return candidate
        self.fail("candidate not found: {0}".format(candidate_id))

    def _synthetic_candidate(self):
        self._require_loaded()
        return {
            "candidate_id": "UPG-TEST",
            "failure_class": "frame_c_ambiguity_misreport",
            "suggested_upgrade_type": "add_ambiguity_clarification",
            "suggested_next_packet_type": "CLARIFICATION-DESIGN",
            "candidate_intent": "reserved_layer_design_proposal",
            "likely_layer": "FRAME-C",
            "safety_tier": "requires_reserved_layer",
            "expectation_drift_risk": "low",
            "affected_case_ids": ["QM-001"],
            "affected_tags": ["mini_v1"],
            "affected_count": 1,
            "patch_plan_skeleton": (
                quality_loop.PATCH_PLAN_TEMPLATES[
                    ("FRAME-C", "add_ambiguity_clarification")
                ]
            ),
            "required_tests": list(
                quality_loop.REQUIRED_TESTS_BY_NEXT_PACKET[
                    "CLARIFICATION-DESIGN"
                ]
            ),
            "risk_notes": (
                quality_loop.RISK_NOTES_BY_LAYER_AND_TYPE[
                    ("FRAME-C", "add_ambiguity_clarification")
                ]
            ),
            "precedent_dc_reference": "DC-TEST",
        }

    def _review(self, candidate_id):
        self._require_loaded()
        for review in self.summary["candidate_case_reviews"]:
            if review["candidate_id"] == candidate_id:
                return review
        self.fail("candidate review not found: {0}".format(candidate_id))

    def _label_by_case(self, candidate_id):
        review = self._review(candidate_id)
        return {
            row["case_id"]: row["review_label"]
            for row in review["case_reviews"]
        }

    def test_candidate_case_review_shape_and_gating_booleans(self):
        self._require_loaded()
        review = quality_loop.build_candidate_case_review(
            self._synthetic_candidate(), self.matrix_result
        )
        expected_keys = {
            "candidate_case_review_kind",
            "candidate_id",
            "failure_class",
            "affected_count",
            "case_reviews",
            "per_review_label_counts",
            "review_note",
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
        }
        self.assertEqual(set(review), expected_keys)
        for key in (
            "selection_made",
            "measurement_authorized",
            "real_benchmark_authorized",
            "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized",
            "route_created",
        ):
            self.assertIs(review[key], False)

    def test_synthetic_case_review_keeps_bounded_label_counts(self):
        review = quality_loop.build_candidate_case_review(
            self._synthetic_candidate(), self.matrix_result
        )
        self.assertEqual(review["affected_count"], 1)
        self.assertEqual(review["per_review_label_counts"], {
            "likely_matrix_expectation_drift": 0,
            "likely_negation_gap": 0,
            "likely_synthesis_gap": 0,
            "needs_human_review": 1,
        })
        self.assertEqual(
            review["case_reviews"][0]["review_label"],
            "needs_human_review",
        )

    def test_candidate_review_summary_covers_all_candidates(self):
        self._require_loaded()
        summary = self.summary
        self.assertEqual(
            summary["candidate_review_summary_kind"],
            "level0_workshop_candidate_review_summary",
        )
        self.assertEqual(summary["candidate_count"], 0)
        self.assertEqual(
            [review["candidate_id"] for review in summary["candidate_case_reviews"]],
            [],
        )
        self.assertEqual(summary["overall_review_label_counts"], {
            "likely_matrix_expectation_drift": 0,
            "likely_negation_gap": 0,
            "likely_synthesis_gap": 0,
            "needs_human_review": 0,
        })

    def test_review_rows_carry_observed_expected_fields(self):
        review = quality_loop.build_candidate_case_review(
            self._synthetic_candidate(), self.matrix_result
        )
        row = review["case_reviews"][0]
        self.assertEqual(row["case_id"], "QM-001")
        self.assertEqual(row["expected_kinds"], row["observed_kinds"])
        self.assertEqual(row["expected_category"], row["observed_category"])
        self.assertEqual(row["differing_fields"], [])

    def test_case_review_rejects_missing_candidate_case(self):
        module = _require_quality_loop(self)
        candidate = dict(self._synthetic_candidate())
        candidate["affected_case_ids"] = ["NO-SUCH-CASE"]
        with self.assertRaises(module.ParserQualityLoopMalformedUpgradeCandidate):
            module.build_candidate_case_review(candidate, self.matrix_result)

    def test_case_review_rejects_malformed_candidate(self):
        module = _require_quality_loop(self)
        candidate = dict(self._synthetic_candidate())
        del candidate["affected_case_ids"]
        with self.assertRaises(module.ParserQualityLoopMalformedUpgradeCandidate):
            module.build_candidate_case_review(candidate, self.matrix_result)


if __name__ == "__main__":
    unittest.main()
