"""Tests for harness.mock_adapter.

Per WO-22 (DC-025): the mock adapter is a scaffold-internal, deterministic,
toy-only conformance scaffold against the WO-21 retrieval adapter contract
boundary. These tests assert plane presence, plane separation, explicit
absence recording, non-selection language, determinism, and absence of any
filesystem effect.
"""

import builtins
import copy
import unittest

from harness.mock_adapter import PLANE_NAMES, run_mock_adapter
from harness.review_package import FORBIDDEN_PHRASES


_TOY_FIXTURE = {
    "_fixture_marker": "harness-internal test fixture; not a real benchmark dataset",
    "sample_record": {
        "id": "toy-1",
        "field": "value",
    },
}

_TOY_CONFIGURATION = {
    "_fixture_marker": "harness-internal test fixture; not a real configuration manifest",
    "id": "toy-scaffold-config",
    "params": {"noop": True},
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


class MockAdapterTest(unittest.TestCase):

    def test_output_contains_all_five_planes(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        for plane in PLANE_NAMES:
            self.assertIn(
                plane,
                output,
                "Plane '{0}' is missing from adapter output".format(plane),
            )

    def test_empty_planes_are_explicit(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        self.assertIn("empty_planes", output)
        empty_planes = output["empty_planes"]
        self.assertIsInstance(empty_planes, list)
        # Every plane key listed in empty_planes corresponds to an empty plane,
        # and every empty plane is listed in empty_planes.
        for plane in PLANE_NAMES:
            if output[plane]:
                self.assertNotIn(plane, empty_planes)
            else:
                self.assertIn(plane, empty_planes)
        # Official and trace/outcome planes are empty by design.
        self.assertIn("official_route_results", empty_planes)
        self.assertIn("trace_outcome_signal_observations", empty_planes)

    def test_planes_remain_separate(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        # Every entry under a plane key carries a `plane` marker that
        # matches the plane key it appears under (no cross-plane drift).
        for plane in PLANE_NAMES:
            for entry in output[plane]:
                self.assertEqual(
                    entry.get("plane"),
                    plane,
                    "Entry under '{0}' is missing or has mismatched plane marker".format(plane),
                )

    def test_normalized_material_is_not_returned_as_route(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        for entry in output["normalized_material_support_results"]:
            self.assertFalse(entry.get("is_candidate", False))
            self.assertFalse(entry.get("is_official", False))
            self.assertEqual(
                entry.get("executability"),
                "non_route_support_material",
            )

    def test_candidate_is_not_executable_official(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        # The official plane is empty by design.
        self.assertEqual(output["official_route_results"], [])
        # Candidate entries are marked candidate, non-official, and explicitly
        # non-executable as official.
        self.assertTrue(len(output["candidate_route_results"]) > 0)
        for entry in output["candidate_route_results"]:
            self.assertTrue(entry.get("is_candidate"))
            self.assertFalse(entry.get("is_official"))
            self.assertEqual(
                entry.get("executability"),
                "candidate_only_non_executable_as_official",
            )

    def test_source_quality_observations_do_not_become_route_trust(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        self.assertTrue(len(output["source_quality_constraint_observations"]) > 0)
        for entry in output["source_quality_constraint_observations"]:
            # Source quality observations are not routes in any state.
            self.assertFalse(entry.get("is_candidate", False))
            self.assertFalse(entry.get("is_official", False))
            self.assertEqual(
                entry.get("executability"),
                "non_route_support_material",
            )
            # Absence of qualification reference is recorded explicitly.
            self.assertIsNone(entry.get("qualification_status_reference"))
            self.assertTrue(entry.get("qualification_status_reference_is_absent"))

    def test_trace_outcome_observations_do_not_become_validation_evidence(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        # The trace/outcome plane is empty under the mock adapter; no entry
        # can be promoted into validation evidence because none exists, and
        # the plane is recorded as empty rather than silently collapsed.
        self.assertEqual(output["trace_outcome_signal_observations"], [])
        self.assertIn("trace_outcome_signal_observations", output["empty_planes"])

    def test_output_contains_no_selection_or_recommendation_language(self):
        output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        # The output must not propose a selection of any kind.
        self.assertIn("selection_made", output)
        self.assertFalse(output["selection_made"])
        # No string in the output (keys or values) contains any forbidden
        # phrase from the review-package vocabulary.
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in FORBIDDEN_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "Forbidden phrase '{0}' found in mock adapter output text: {1!r}".format(
                        phrase, text
                    ),
                )

    def test_function_is_deterministic_for_same_input(self):
        first = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        second = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        self.assertEqual(first, second)
        # Inputs are not mutated across calls.
        third = run_mock_adapter(
            copy.deepcopy(_TOY_FIXTURE),
            copy.deepcopy(_TOY_CONFIGURATION),
        )
        self.assertEqual(first, third)

    def test_function_performs_no_filesystem_write(self):
        original_open = builtins.open
        call_log = []

        def _guarded_open(*args, **kwargs):
            call_log.append((args, kwargs))
            raise AssertionError(
                "Mock adapter must not open any file; got open({0!r}, {1!r})".format(
                    args, kwargs
                )
            )

        builtins.open = _guarded_open
        try:
            output = run_mock_adapter(_TOY_FIXTURE, _TOY_CONFIGURATION)
        finally:
            builtins.open = original_open

        self.assertEqual(call_log, [])
        self.assertIsInstance(output, dict)


if __name__ == "__main__":
    unittest.main()
