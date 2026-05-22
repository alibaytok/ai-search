"""WO-48: additional route-first coverage tests for the WO-47 scaffold indexing-logic probe.

These tests extend coverage of `harness.scaffold_index_probe` without
modifying the probe module. They focus on:

- evidence consistency between the returned output dict's counts and
  the per-event-type counts emitted into the event log;
- the `normalized` observation kind (not exercised by the WO-31 wave
  because every WO-31 hard-negative entry allows the candidate plane);
- the empty-`allowed_planes` fallback path for hard-negatives;
- per-entry observation event ordering (class order then within-class
  entry order);
- cross-class identity integrity (each event's `class_name` correctly
  pairs with its `fixture_id`);
- the `forbidden_plane_collapse` field preserved on contract-failure
  observations;
- idempotency of the probe under deep-copied identical inputs.

The tests are scaffold-only. They do not invoke any real or mock
adapter, do not perform real benchmark execution, do not collect
metrics, do not score, do not rank, do not select any architecture,
and do not authorize measurement. The probe module is NOT modified
under WO-48.

Per WO-47 / WO-48 explicit non-claim constraint: no test docstring,
class name, or method name asserts the probe or any indexing
approach is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected.
"""

import copy
import json
import os
import unittest

from harness.event_log import EventLog
from harness.scaffold_index_probe import (
    ALLOWED_OUTPUT_KEYS,
    REQUIRED_PAYLOAD_CLASSES,
    run_scaffold_index_probe,
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


def _observation_event_types():
    """Return the five per-entry observation event type strings."""
    return (
        "scaffold_index_probe_official_observation",
        "scaffold_index_probe_candidate_observation",
        "scaffold_index_probe_normalized_observation",
        "scaffold_index_probe_miss_observation",
        "scaffold_index_probe_contract_failure_observation",
    )


def _custom_hard_negatives_payload(allowed_planes, fixture_id):
    """Build an in-memory hard-negatives payload with caller-chosen allowed_planes.

    The returned payload mirrors the WO-31 / WO-30 hard-negatives entry
    shape closely enough to drive the probe's hard-negatives dispatcher.
    The payload is in-memory only; no file is created.
    """
    return {
        "_fixture_payload_marker": (
            "harness-internal synthetic in-memory payload for WO-48 "
            "coverage tests; not benchmark evidence; scaffold-internal "
            "observation only"
        ),
        "fixture_class": "hard-negatives",
        "fixture_version": "wo48-coverage-in-memory",
        "synthetic_only": True,
        "no_production_data": True,
        "no_user_data": True,
        "not_benchmark_evidence": True,
        "not_validation_evidence": True,
        "entries": [
            {
                "fixture_id": fixture_id,
                "purpose": (
                    "Synthetic hard-negatives entry for WO-48 coverage "
                    "testing of the probe's plane-allowed dispatcher."
                ),
                "synthetic_only": True,
                "no_production_user_data": True,
                "non_selection_posture": (
                    "This entry is observation only; it does not propose "
                    "any retrieval implementation choice, configuration, "
                    "or production system."
                ),
                "intent_surface": {
                    "synthetic_intent_text": (
                        "How does the WO-48 coverage entry get observed "
                        "on a chosen plane?"
                    ),
                    "synthetic_only": True,
                },
                "near_match_classification": "coverage_synthetic",
                "near_match_reason_class": "wo48_coverage",
                "plane_separation_markers": {
                    "allowed_planes": list(allowed_planes),
                    "forbidden_planes": [
                        "official_route_results",
                    ],
                    "forbidden_plane_collapse": "official_route_results",
                },
                "must_not_authorize_official_return": True,
                "entry_version": "wo48-coverage-in-memory-rev1",
            }
        ],
    }


class EventCountConsistencyTest(unittest.TestCase):
    """Output dict counts and event log counts must agree."""

    def test_output_counts_equal_event_log_counts(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        types = [e["type"] for e in log.events]
        for output_key, event_type in (
            ("official_observation_count",
             "scaffold_index_probe_official_observation"),
            ("candidate_observation_count",
             "scaffold_index_probe_candidate_observation"),
            ("normalized_observation_count",
             "scaffold_index_probe_normalized_observation"),
            ("miss_observation_count",
             "scaffold_index_probe_miss_observation"),
            ("contract_failure_observation_count",
             "scaffold_index_probe_contract_failure_observation"),
        ):
            self.assertEqual(
                output[output_key],
                types.count(event_type),
                "output[{0!r}] ({1}) does not equal events of type "
                "{2!r} ({3})".format(
                    output_key,
                    output[output_key],
                    event_type,
                    types.count(event_type),
                ),
            )

    def test_entries_indexed_count_equals_observation_event_total(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        observation_total = sum(
            1 for e in log.events
            if e["type"] in _observation_event_types()
        )
        self.assertEqual(output["entries_indexed_count"], observation_total)

    def test_run_ended_event_counts_match_output_dict(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        run_ended_events = [
            e for e in log.events
            if e["type"] == "scaffold_index_probe_run_ended"
        ]
        self.assertEqual(len(run_ended_events), 1)
        run_ended = run_ended_events[0]
        for key in (
            "entries_indexed_count",
            "official_observation_count",
            "candidate_observation_count",
            "normalized_observation_count",
            "miss_observation_count",
            "contract_failure_observation_count",
        ):
            self.assertEqual(
                run_ended[key],
                output[key],
                "run_ended event field {0!r} ({1!r}) does not equal "
                "output[{0!r}] ({2!r})".format(key, run_ended[key], output[key]),
            )


class HardNegativeNormalizedFallbackTest(unittest.TestCase):
    """A hard-negatives entry that allows only the normalized plane must
    land there, exercising the `normalized` observation kind that the
    WO-31 wave does not reach.
    """

    def test_normalized_plane_only_produces_normalized_observation(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"] = _custom_hard_negatives_payload(
            allowed_planes=["normalized_material_support_results"],
            fixture_id="wo48-hn-normalized-only",
        )
        log = EventLog()
        output = run_scaffold_index_probe(payloads, log)
        normalized_events = [
            e for e in log.events
            if e["type"] == "scaffold_index_probe_normalized_observation"
        ]
        self.assertEqual(len(normalized_events), 1)
        event = normalized_events[0]
        self.assertEqual(event["class_name"], "hard-negatives")
        self.assertEqual(event["fixture_id"], "wo48-hn-normalized-only")
        self.assertEqual(
            event["observation"]["plane"],
            "normalized_material_support_results",
        )
        # The output count reflects the kind too.
        self.assertEqual(output["normalized_observation_count"], 1)
        # And no candidate observation was emitted from the
        # normalized-only hard-negatives entry.
        candidate_events = [
            e for e in log.events
            if e["type"] == "scaffold_index_probe_candidate_observation"
            and e.get("class_name") == "hard-negatives"
        ]
        self.assertEqual(len(candidate_events), 0)


class HardNegativeEmptyAllowedPlanesFallbackTest(unittest.TestCase):
    """A hard-negatives entry with an empty `allowed_planes` list falls
    back to the candidate plane (per the probe module docstring); the
    official plane is never chosen.
    """

    def test_empty_allowed_planes_falls_back_to_candidate(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"] = _custom_hard_negatives_payload(
            allowed_planes=[],
            fixture_id="wo48-hn-empty-allowed-planes",
        )
        log = EventLog()
        output = run_scaffold_index_probe(payloads, log)
        # Locate the event for the custom entry.
        hn_events = [
            e for e in log.events
            if e.get("fixture_id") == "wo48-hn-empty-allowed-planes"
        ]
        self.assertEqual(len(hn_events), 1)
        event = hn_events[0]
        # The fallback path emits a candidate-kind observation event.
        self.assertEqual(
            event["type"],
            "scaffold_index_probe_candidate_observation",
        )
        # The observation's plane is `candidate_route_results`, never
        # `official_route_results`.
        self.assertEqual(
            event["observation"]["plane"], "candidate_route_results"
        )
        self.assertNotEqual(
            event["observation"]["plane"], "official_route_results"
        )

    def test_empty_allowed_planes_does_not_authorize_official(self):
        payloads = _load_all_payloads()
        payloads["hard-negatives"] = _custom_hard_negatives_payload(
            allowed_planes=[],
            fixture_id="wo48-hn-empty-allowed-planes-official-check",
        )
        log = EventLog()
        run_scaffold_index_probe(payloads, log)
        # No official observation was emitted from the custom
        # hard-negatives entry.
        for event in log.events:
            if event.get("fixture_id") == (
                "wo48-hn-empty-allowed-planes-official-check"
            ):
                self.assertNotEqual(
                    event["type"],
                    "scaffold_index_probe_official_observation",
                )


class EntryOrderPreservationTest(unittest.TestCase):
    """Per-entry observation events appear in (class-order, within-class
    entry-order). Class order is `REQUIRED_PAYLOAD_CLASSES`; within-class
    order matches the input list order.
    """

    def test_event_order_follows_class_order(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        # Extract the class_name of each per-entry observation event in
        # log order.
        per_entry_class_names = [
            e["class_name"]
            for e in log.events
            if e["type"] in _observation_event_types()
        ]
        # The expected class-name sequence follows REQUIRED_PAYLOAD_CLASSES
        # (each class contributes its entries in input order).
        expected_sequence = []
        payloads = _load_all_payloads()
        for class_name in REQUIRED_PAYLOAD_CLASSES:
            entry_count = len(payloads[class_name]["entries"])
            expected_sequence.extend([class_name] * entry_count)
        self.assertEqual(per_entry_class_names, expected_sequence)

    def test_within_class_entry_order_preserved(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        payloads = _load_all_payloads()
        for class_name in REQUIRED_PAYLOAD_CLASSES:
            expected_ids = [
                entry["fixture_id"]
                for entry in payloads[class_name]["entries"]
            ]
            observed_ids = [
                e["fixture_id"]
                for e in log.events
                if e["type"] in _observation_event_types()
                and e["class_name"] == class_name
            ]
            self.assertEqual(observed_ids, expected_ids)


class CrossClassIdentityIntegrityTest(unittest.TestCase):
    """Each per-entry observation event correctly pairs its `class_name`
    with the `fixture_id` from the corresponding input entry. No event
    is allowed to record a `fixture_id` under the wrong `class_name`.
    """

    def test_each_event_class_name_matches_source_class(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        payloads = _load_all_payloads()
        # Build the source-of-truth mapping fixture_id -> class_name.
        truth = {}
        for class_name in REQUIRED_PAYLOAD_CLASSES:
            for entry in payloads[class_name]["entries"]:
                truth[entry["fixture_id"]] = class_name
        # Verify every per-entry observation event agrees.
        for event in log.events:
            if event["type"] not in _observation_event_types():
                continue
            fixture_id = event["fixture_id"]
            self.assertIn(
                fixture_id,
                truth,
                "event fixture_id {0!r} is not in the input set".format(
                    fixture_id
                ),
            )
            self.assertEqual(
                event["class_name"],
                truth[fixture_id],
                "event for fixture_id {0!r} carries class_name {1!r}; "
                "the input source class is {2!r}".format(
                    fixture_id, event["class_name"], truth[fixture_id]
                ),
            )


class ForbiddenPlaneCollapseFieldPreservedTest(unittest.TestCase):
    """A boundary-violations entry's `forbidden_plane_collapse` marker
    is surfaced verbatim onto the contract-failure observation. Plane
    separation evidence must be visible at the observation surface.
    """

    def test_forbidden_plane_collapse_field_preserved_on_observation(self):
        payloads = _load_all_payloads()
        log = EventLog()
        run_scaffold_index_probe(payloads, log)
        # Build the source-of-truth mapping fixture_id ->
        # forbidden_plane_collapse from the boundary-violations payload.
        truth = {}
        for entry in payloads["boundary-violations"]["entries"]:
            truth[entry["fixture_id"]] = entry[
                "plane_separation_markers"
            ]["forbidden_plane_collapse"]
        # Locate every contract-failure observation event and verify it
        # carries the same forbidden_plane_collapse value.
        cf_events = [
            e for e in log.events
            if e["type"]
            == "scaffold_index_probe_contract_failure_observation"
        ]
        self.assertEqual(len(cf_events), len(truth))
        for event in cf_events:
            fixture_id = event["fixture_id"]
            self.assertIn(fixture_id, truth)
            self.assertEqual(
                event["observation"]["forbidden_plane_collapse"],
                truth[fixture_id],
            )


class ProbeIdempotencyTest(unittest.TestCase):
    """Calling the probe twice with deep-copied identical inputs produces
    equal output dicts. The probe is a deterministic scaffold function;
    no per-call state, no warm cache, no cross-call side effect.
    """

    def test_two_invocations_produce_equal_output_dicts(self):
        payloads_first = _load_all_payloads()
        payloads_second = copy.deepcopy(payloads_first)
        log_first = EventLog()
        log_second = EventLog()
        output_first = run_scaffold_index_probe(payloads_first, log_first)
        output_second = run_scaffold_index_probe(
            payloads_second, log_second
        )
        # The output dicts must compare equal.
        self.assertEqual(output_first, output_second)
        # And both must carry exactly the allowed output keys.
        self.assertEqual(set(output_first.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(set(output_second.keys()), set(ALLOWED_OUTPUT_KEYS))

    def test_two_invocations_produce_equal_per_entry_observation_payloads(self):
        # The event log timestamps will differ (the log is append-only
        # and timestamps are derived at append time, per
        # `harness.event_log.EventLog`). But the per-entry observation
        # payloads themselves must be identical across invocations.
        payloads_first = _load_all_payloads()
        payloads_second = copy.deepcopy(payloads_first)
        log_first = EventLog()
        log_second = EventLog()
        run_scaffold_index_probe(payloads_first, log_first)
        run_scaffold_index_probe(payloads_second, log_second)

        def _observation_signatures(log):
            return [
                (e["type"], e["class_name"], e["fixture_id"], e["observation"])
                for e in log.events
                if e["type"] in _observation_event_types()
            ]

        self.assertEqual(
            _observation_signatures(log_first),
            _observation_signatures(log_second),
        )


if __name__ == "__main__":
    unittest.main()
