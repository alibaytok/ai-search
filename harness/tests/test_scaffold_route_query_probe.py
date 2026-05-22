"""Tests for the WO-50 scaffold route-query probe.

The tests exercise query-shaped observations over the admitted synthetic
payloads while keeping the same boundary as WO-47 / WO-48: no real
retrieval call, no adapter invocation, no metrics, no ranking, no
architecture choice, and no benchmark readiness change.
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
from harness.scaffold_route_query_probe import (
    ALLOWED_OUTPUT_KEYS,
    BoundaryViolationTreatedAsSuccess,
    DuplicateQueryId,
    DuplicateSyntheticIntentText,
    ForbiddenLanguageInRouteQueryProbe,
    HardNegativeForbiddenOfficialReturn,
    MissingQueryField,
    NonListQueries,
    NonObjectPayloadsByClass,
    PROBE_OUTPUT_FORBIDDEN_PHRASES,
    REQUIRED_PAYLOAD_CLASSES,
    run_scaffold_route_query_probe,
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


def _intent_text(payload, entry_index):
    return payload["entries"][entry_index]["intent_surface"]["synthetic_intent_text"]


def _query(query_id, text):
    return {
        "query_id": query_id,
        "synthetic_intent_text": text,
    }


def _standard_queries(payloads):
    return [
        _query(
            "wo50-query-golden-official",
            _intent_text(payloads["golden-intents"], 0),
        ),
        _query(
            "wo50-query-golden-miss",
            _intent_text(payloads["golden-intents"], 1),
        ),
        _query(
            "wo50-query-hard-negative",
            _intent_text(payloads["hard-negatives"], 0),
        ),
        _query(
            "wo50-query-boundary-violation",
            _intent_text(payloads["boundary-violations"], 0),
        ),
        _query(
            "wo50-query-unknown",
            "How does the synthetic WO-50 query behave when no route text is present?",
        ),
    ]


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


class ScaffoldRouteQueryProbeSuccessTest(unittest.TestCase):
    def test_standard_queries_observe_expected_counts(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_route_query_probe(
            payloads, _standard_queries(payloads), log
        )

        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(output["indexed_entry_count"], 6)
        self.assertEqual(output["queries_observed_count"], 5)
        self.assertEqual(output["official_observation_count"], 1)
        self.assertEqual(output["candidate_observation_count"], 1)
        self.assertEqual(output["normalized_observation_count"], 0)
        self.assertEqual(output["miss_observation_count"], 2)
        self.assertEqual(output["contract_failure_observation_count"], 1)
        self.assertFalse(log.has_halt())

    def test_authorization_booleans_remain_false(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_route_query_probe(
            payloads, _standard_queries(payloads), log
        )

        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)

    def test_run_end_event_counts_match_output(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_route_query_probe(
            payloads, _standard_queries(payloads), log
        )
        end_events = [
            event
            for event in log.events
            if event["type"] == "scaffold_route_query_probe_run_ended"
        ]
        self.assertEqual(len(end_events), 1)
        end_event = end_events[0]
        for key in (
            "indexed_entry_count",
            "queries_observed_count",
            "official_observation_count",
            "candidate_observation_count",
            "normalized_observation_count",
            "miss_observation_count",
            "contract_failure_observation_count",
        ):
            self.assertEqual(end_event[key], output[key])


class ScaffoldRouteQueryProbeBehaviorTest(unittest.TestCase):
    def test_official_query_surfaces_official_route_identifier(self):
        payloads = _load_all_payloads()
        log = EventLog()
        run_scaffold_route_query_probe(
            payloads,
            [_query("wo50-official", _intent_text(payloads["golden-intents"], 0))],
            log,
        )

        events = [
            event
            for event in log.events
            if event["type"] == "scaffold_route_query_probe_official_observation"
        ]
        self.assertEqual(len(events), 1)
        self.assertEqual(
            events[0]["observation"]["synthetic_route_identifier"],
            "synthetic-route-id-A",
        )
        self.assertEqual(events[0]["observation"]["plane"], "official_route_results")

    def test_hard_negative_query_does_not_emit_official_observation(self):
        payloads = _load_all_payloads()
        log = EventLog()
        run_scaffold_route_query_probe(
            payloads,
            [
                _query(
                    "wo50-hard-negative",
                    _intent_text(payloads["hard-negatives"], 0),
                )
            ],
            log,
        )

        self.assertFalse(
            any(
                event["type"] == "scaffold_route_query_probe_official_observation"
                for event in log.events
            )
        )
        candidate_events = [
            event
            for event in log.events
            if event["type"] == "scaffold_route_query_probe_candidate_observation"
        ]
        self.assertEqual(len(candidate_events), 1)
        self.assertEqual(
            candidate_events[0]["observation"]["plane"],
            "candidate_route_results",
        )

    def test_normalized_only_hard_negative_query_observes_normalized_plane(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"]["entries"][0]["plane_separation_markers"][
            "allowed_planes"
        ] = ["normalized_material_support_results"]
        log = EventLog()
        run_scaffold_route_query_probe(
            payloads,
            [
                _query(
                    "wo50-normalized-only",
                    _intent_text(payloads["hard-negatives"], 0),
                )
            ],
            log,
        )

        normalized_events = [
            event
            for event in log.events
            if event["type"] == "scaffold_route_query_probe_normalized_observation"
        ]
        self.assertEqual(len(normalized_events), 1)
        self.assertEqual(
            normalized_events[0]["observation"]["plane"],
            "normalized_material_support_results",
        )

    def test_boundary_violation_query_observes_contract_failure(self):
        payloads = _load_all_payloads()
        log = EventLog()
        run_scaffold_route_query_probe(
            payloads,
            [
                _query(
                    "wo50-boundary",
                    _intent_text(payloads["boundary-violations"], 0),
                )
            ],
            log,
        )

        events = [
            event
            for event in log.events
            if event["type"]
            == "scaffold_route_query_probe_contract_failure_observation"
        ]
        self.assertEqual(len(events), 1)
        self.assertIs(events[0]["observation"]["is_forbidden_output"], True)
        self.assertIs(events[0]["observation"]["is_valid_output"], False)

    def test_unknown_query_observes_miss(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_route_query_probe(
            payloads,
            [
                _query(
                    "wo50-unknown",
                    "How does this synthetic query behave without a matching entry?",
                )
            ],
            log,
        )

        self.assertEqual(output["miss_observation_count"], 1)
        events = [
            event
            for event in log.events
            if event["type"] == "scaffold_route_query_probe_miss_observation"
        ]
        self.assertEqual(len(events), 1)
        self.assertIs(events[0]["observation"]["matched"], False)


class ScaffoldRouteQueryProbeRejectionTest(unittest.TestCase):
    def test_non_object_payloads_rejected(self):
        log = EventLog()
        with self.assertRaises(NonObjectPayloadsByClass):
            run_scaffold_route_query_probe("not a dict", [], log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_route_query_probe_non_object_input",
        )

    def test_non_list_queries_rejected(self):
        log = EventLog()
        with self.assertRaises(NonListQueries):
            run_scaffold_route_query_probe(_load_all_payloads(), {}, log)
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_route_query_probe_non_list_queries",
        )

    def test_missing_query_field_rejected(self):
        log = EventLog()
        with self.assertRaises(MissingQueryField):
            run_scaffold_route_query_probe(
                _load_all_payloads(),
                [{"query_id": "wo50-missing-text"}],
                log,
            )
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_route_query_probe_missing_query_field",
        )

    def test_duplicate_query_id_rejected(self):
        payloads = _load_all_payloads()
        text = _intent_text(payloads["golden-intents"], 0)
        log = EventLog()
        with self.assertRaises(DuplicateQueryId):
            run_scaffold_route_query_probe(
                payloads,
                [_query("wo50-duplicate", text), _query("wo50-duplicate", text)],
                log,
            )
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_route_query_probe_duplicate_query_id",
        )

    def test_duplicate_intent_text_rejected(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"]["entries"][0]["intent_surface"][
            "synthetic_intent_text"
        ] = _intent_text(payloads["golden-intents"], 0)
        log = EventLog()
        with self.assertRaises(DuplicateSyntheticIntentText):
            run_scaffold_route_query_probe(
                payloads,
                [
                    _query(
                        "wo50-duplicate-intent",
                        _intent_text(payloads["golden-intents"], 0),
                    )
                ],
                log,
            )
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_route_query_probe_duplicate_intent_text",
        )

    def test_hard_negative_official_plane_rejected(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"]["entries"][0]["plane_separation_markers"][
            "allowed_planes"
        ] = ["official_route_results"]
        log = EventLog()
        with self.assertRaises(HardNegativeForbiddenOfficialReturn):
            run_scaffold_route_query_probe(
                payloads,
                [
                    _query(
                        "wo50-hard-negative-official",
                        _intent_text(payloads["hard-negatives"], 0),
                    )
                ],
                log,
            )
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_route_query_probe_hard_negative_forbidden_official",
        )

    def test_boundary_violation_valid_output_rejected(self):
        payloads = _load_all_payloads()
        payloads["boundary-violations"]["entries"][0]["expected_disqualification"][
            "is_valid_output"
        ] = True
        log = EventLog()
        with self.assertRaises(BoundaryViolationTreatedAsSuccess):
            run_scaffold_route_query_probe(
                payloads,
                [
                    _query(
                        "wo50-boundary-valid",
                        _intent_text(payloads["boundary-violations"], 0),
                    )
                ],
                log,
            )
        self.assertEqual(
            _last_halt_event(log)["reason"],
            "scaffold_route_query_probe_boundary_violation_treated_as_success",
        )


class ScaffoldRouteQueryProbeLanguageTest(unittest.TestCase):
    def test_output_has_no_forbidden_language(self):
        payloads = _load_all_payloads()
        log = EventLog()
        output = run_scaffold_route_query_probe(
            payloads, _standard_queries(payloads), log
        )
        forbidden = PROBE_OUTPUT_FORBIDDEN_PHRASES + FORBIDDEN_CLAIM_PHRASES
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in forbidden:
                self.assertNotIn(phrase, lowered)

    def test_forbidden_query_surface_rejected_without_leaking_text(self):
        payloads = _load_all_payloads()
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInRouteQueryProbe):
            run_scaffold_route_query_probe(
                payloads,
                [
                    _query(
                        "best_query",
                        _intent_text(payloads["golden-intents"], 0),
                    )
                ],
                log,
            )

        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "scaffold_route_query_probe_forbidden_language"
        )
        rendered_events = json.dumps(log.events, sort_keys=True)
        self.assertNotIn("best_query", rendered_events)


class ScaffoldRouteQueryProbeIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_inputs(self):
        payloads = _load_all_payloads()
        queries = _standard_queries(payloads)
        before_payloads = copy.deepcopy(payloads)
        before_queries = copy.deepcopy(queries)

        run_scaffold_route_query_probe(payloads, queries, EventLog())

        self.assertEqual(payloads, before_payloads)
        self.assertEqual(queries, before_queries)

    def test_function_writes_no_files(self):
        payloads = _load_all_payloads()
        queries = _standard_queries(payloads)
        with tempfile.TemporaryDirectory() as tmpdir:
            before = set(os.listdir(tmpdir))
            cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                run_scaffold_route_query_probe(payloads, queries, EventLog())
                after = set(os.listdir(tmpdir))
            finally:
                os.chdir(cwd)
        self.assertEqual(before, after)


class ScaffoldRouteQueryProbeImportSurfaceTest(unittest.TestCase):
    def test_no_third_party_imports(self):
        path = os.path.join(_PROJECT_ROOT, "harness", "scaffold_route_query_probe.py")
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
                "unexpected import in route-query probe: {0}".format(module_name),
            )


class ScaffoldRouteQueryProbeFixtureMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_probe(self):
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
        run_scaffold_route_query_probe(
            payloads, _standard_queries(payloads), EventLog()
        )
        after = inventory()
        self.assertEqual(after, before)
