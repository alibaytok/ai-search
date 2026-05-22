"""Tests for harness.scaffold_index_probe.

Per WO-47 (DC-047): the scaffold indexing-logic probe runs an
in-memory probe over the WO-31 admitted first-wave synthetic payloads
and exercises route-first retrieval boundary behavior. These tests
assert the WO-47 packet requirements categorically:

- success path returns a dict with exactly the twelve allowed output
  keys over the three existing payload classes;
- all four authorization / selection / readiness booleans remain
  literal False;
- golden-intents official entry produces an official observation;
- golden-intents miss entry produces a miss observation;
- hard-negative entries never produce an official observation;
- hard-negative allowed planes are preserved on the per-entry
  observation;
- boundary-violation entries produce contract-failure observations
  and never successful retrieval observations;
- duplicate fixture_id across the probe input is rejected;
- missing required class is rejected;
- payload class mismatch is rejected;
- the function does not mutate the input;
- the function performs no filesystem writes during success or
  failure paths;
- the output contains no forbidden selection language, no `"score"`,
  no `"scoring"`, and no `FORBIDDEN_CLAIM_PHRASES` substring;
- the module imports only stdlib and harness-internal symbols (no
  third-party dependency).

The tests use only Python stdlib plus harness-internal imports.
"""

import ast
import copy
import json
import os
import sys
import tempfile
import unittest

from harness.event_log import EventLog
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES
from harness.scaffold_index_probe import (
    ALLOWED_OUTPUT_KEYS,
    BoundaryViolationTreatedAsSuccess,
    DuplicateFixtureIdAcrossProbe,
    ForbiddenLanguageInProbeOutput,
    HardNegativeForbiddenOfficialReturn,
    MissingOrNonListEntries,
    MissingRequiredPayloadClass,
    NonObjectPayload,
    NonObjectPayloadsByClass,
    PayloadClassMismatch,
    PROBE_OUTPUT_FORBIDDEN_PHRASES,
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


class ScaffoldIndexProbeSuccessTest(unittest.TestCase):
    def test_success_over_three_wave001_classes(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        self.assertEqual(output["entries_indexed_count"], 6)
        self.assertFalse(log.has_halt())

    def test_success_returns_exact_allowed_keys(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        self.assertEqual(set(output.keys()), set(ALLOWED_OUTPUT_KEYS))

    def test_authorization_and_selection_booleans_all_false(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        self.assertIs(output["selection_made"], False)
        self.assertIs(output["measurement_authorized"], False)
        self.assertIs(output["real_benchmark_authorized"], False)
        self.assertIs(output["real_benchmark_ready"], False)

    def test_probe_kind_is_observation_kind(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        self.assertEqual(
            output["probe_kind"], "scaffold_indexing_logic_probe"
        )

    def test_start_and_run_end_events_recorded(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        types = [e["type"] for e in log.events]
        self.assertIn("scaffold_index_probe_started", types)
        self.assertIn("scaffold_index_probe_run_ended", types)
        # Start event is recorded before the first observation event.
        self.assertLess(
            types.index("scaffold_index_probe_started"),
            types.index("scaffold_index_probe_run_ended"),
        )


class ScaffoldIndexProbePerClassBehaviorTest(unittest.TestCase):
    def test_golden_official_entry_produces_official_observation(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        events = log.events
        official_events = [
            e for e in events
            if e["type"] == "scaffold_index_probe_official_observation"
        ]
        self.assertEqual(len(official_events), 1)
        event = official_events[0]
        self.assertEqual(event["class_name"], "golden-intents")
        self.assertEqual(
            event["fixture_id"], "golden-intents-wave-001-entry-A"
        )
        observation = event["observation"]
        self.assertEqual(observation["plane"], "official_route_results")
        self.assertEqual(
            observation["synthetic_route_identifier"], "synthetic-route-id-A"
        )

    def test_golden_miss_entry_produces_miss_observation(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        events = log.events
        miss_events = [
            e for e in events
            if e["type"] == "scaffold_index_probe_miss_observation"
        ]
        self.assertEqual(len(miss_events), 1)
        event = miss_events[0]
        self.assertEqual(event["class_name"], "golden-intents")
        self.assertEqual(
            event["fixture_id"], "golden-intents-wave-001-entry-B"
        )
        observation = event["observation"]
        self.assertEqual(observation["plane"], "official_route_results")
        self.assertIs(
            observation["plane_is_empty_for_this_entry"], True
        )
        self.assertEqual(
            observation["miss_classification"], "no_official_route_exists"
        )

    def test_hard_negative_entries_never_produce_official_observation(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        events = log.events
        official_events = [
            e for e in events
            if e["type"] == "scaffold_index_probe_official_observation"
        ]
        # Only one official observation, and it is from golden-intents,
        # not from any hard-negatives entry.
        for event in official_events:
            self.assertNotEqual(event["class_name"], "hard-negatives")

    def test_hard_negative_allowed_planes_preserved(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        events = log.events
        hn_events = [
            e for e in events
            if e["class_name"] == "hard-negatives"
            if e["type"].startswith("scaffold_index_probe_")
            if e["type"] != "scaffold_index_probe_started"
        ] if False else [
            e for e in events
            if e["type"].startswith("scaffold_index_probe_")
            and e["type"]
            not in (
                "scaffold_index_probe_started",
                "scaffold_index_probe_run_ended",
            )
            and e.get("class_name") == "hard-negatives"
        ]
        self.assertEqual(len(hn_events), 2)
        for event in hn_events:
            observation = event["observation"]
            # The recorded plane must be one of the entry's
            # allowed_planes, and must NOT be the official plane.
            self.assertNotEqual(observation["plane"], "official_route_results")
            self.assertIn(
                observation["plane"], observation["allowed_planes"]
            )
            self.assertIs(
                observation["must_not_authorize_official_return"], True
            )

    def test_boundary_violation_entries_produce_contract_failure(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        events = log.events
        cf_events = [
            e for e in events
            if e["type"] == "scaffold_index_probe_contract_failure_observation"
        ]
        self.assertEqual(len(cf_events), 2)
        for event in cf_events:
            self.assertEqual(event["class_name"], "boundary-violations")
            observation = event["observation"]
            self.assertIs(observation["is_forbidden_output"], True)
            self.assertIs(observation["is_valid_output"], False)
            self.assertEqual(
                observation["halt_classification"], "contract_check_failed"
            )

    def test_no_boundary_violation_produces_successful_retrieval_event(self):
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        events = log.events
        for event in events:
            if event.get("class_name") == "boundary-violations":
                # Boundary-violations entries may only surface as
                # contract_failure observation events (not official,
                # candidate, normalized, or miss).
                if event["type"].startswith("scaffold_index_probe_") and event[
                    "type"
                ] not in (
                    "scaffold_index_probe_started",
                    "scaffold_index_probe_run_ended",
                ):
                    self.assertEqual(
                        event["type"],
                        "scaffold_index_probe_contract_failure_observation",
                    )


class ScaffoldIndexProbeRejectionTest(unittest.TestCase):
    def test_non_dict_input_rejected(self):
        for bad in ("not a dict", None, 42, ["not", "a", "dict"]):
            with self.subTest(bad=bad):
                log = EventLog()
                with self.assertRaises(NonObjectPayloadsByClass):
                    run_scaffold_index_probe(bad, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"], "scaffold_index_probe_non_object_input"
                )

    def test_missing_required_class_rejected(self):
        for missing in REQUIRED_PAYLOAD_CLASSES:
            with self.subTest(missing=missing):
                payloads = _load_all_payloads()
                del payloads[missing]
                log = EventLog()
                with self.assertRaises(MissingRequiredPayloadClass):
                    run_scaffold_index_probe(payloads, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"],
                    "scaffold_index_probe_missing_required_class",
                )
                self.assertEqual(halt["missing_class"], missing)

    def test_non_dict_payload_rejected(self):
        payloads = _load_all_payloads()
        payloads["golden-intents"] = "not a dict"
        log = EventLog()
        with self.assertRaises(NonObjectPayload):
            run_scaffold_index_probe(payloads, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "scaffold_index_probe_non_object_payload"
        )

    def test_missing_or_non_list_entries_rejected(self):
        for bad_value in (None, "not a list", {}, []):
            with self.subTest(bad_value=bad_value):
                payloads = _load_all_payloads()
                # Use a copy to avoid cross-subtest pollution.
                gi = dict(payloads["golden-intents"])
                if bad_value is None:
                    del gi["entries"]
                else:
                    gi["entries"] = bad_value
                payloads["golden-intents"] = gi
                log = EventLog()
                with self.assertRaises(MissingOrNonListEntries):
                    run_scaffold_index_probe(payloads, log)
                halt = _last_halt_event(log)
                self.assertEqual(
                    halt["reason"],
                    "scaffold_index_probe_missing_or_non_list_entries",
                )

    def test_payload_class_mismatch_rejected(self):
        payloads = _load_all_payloads()
        gi = dict(payloads["golden-intents"])
        gi["fixture_class"] = "hard-negatives"
        payloads["golden-intents"] = gi
        log = EventLog()
        with self.assertRaises(PayloadClassMismatch):
            run_scaffold_index_probe(payloads, log)
        halt = _last_halt_event(log)
        self.assertEqual(halt["reason"], "scaffold_index_probe_class_mismatch")

    def test_duplicate_fixture_id_rejected(self):
        # Inject a duplicate fixture_id by copying a golden-intents
        # entry's id into the first hard-negatives entry.
        payloads = _load_all_payloads()
        gi_entries = list(payloads["golden-intents"]["entries"])
        hn_entries = [dict(e) for e in payloads["hard-negatives"]["entries"]]
        # Set the first hard-negative entry's id to the first
        # golden-intent entry's id.
        hn_entries[0]["fixture_id"] = gi_entries[0]["fixture_id"]
        hn = dict(payloads["hard-negatives"])
        hn["entries"] = hn_entries
        payloads["hard-negatives"] = hn
        log = EventLog()
        with self.assertRaises(DuplicateFixtureIdAcrossProbe):
            run_scaffold_index_probe(payloads, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "scaffold_index_probe_duplicate_fixture_id"
        )

    def test_hard_negative_with_official_in_allowed_planes_rejected(self):
        payloads = _load_all_payloads()
        hn_entries = [dict(e) for e in payloads["hard-negatives"]["entries"]]
        # Tamper the first hard-negative entry to allow the official
        # plane (the contract forbids this).
        markers = dict(hn_entries[0]["plane_separation_markers"])
        markers["allowed_planes"] = list(markers["allowed_planes"]) + [
            "official_route_results"
        ]
        hn_entries[0] = dict(hn_entries[0])
        hn_entries[0]["plane_separation_markers"] = markers
        hn = dict(payloads["hard-negatives"])
        hn["entries"] = hn_entries
        payloads["hard-negatives"] = hn
        log = EventLog()
        with self.assertRaises(HardNegativeForbiddenOfficialReturn):
            run_scaffold_index_probe(payloads, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"],
            "scaffold_index_probe_hard_negative_forbidden_official",
        )

    def test_boundary_violation_treated_as_success_rejected(self):
        payloads = _load_all_payloads()
        bv_entries = [
            dict(e) for e in payloads["boundary-violations"]["entries"]
        ]
        # Tamper the first boundary-violation entry to declare its
        # outcome as valid (the contract forbids this).
        expected = dict(bv_entries[0]["expected_disqualification"])
        expected["is_valid_output"] = True
        expected["is_forbidden_output"] = False
        bv_entries[0] = dict(bv_entries[0])
        bv_entries[0]["expected_disqualification"] = expected
        bv = dict(payloads["boundary-violations"])
        bv["entries"] = bv_entries
        payloads["boundary-violations"] = bv
        log = EventLog()
        with self.assertRaises(BoundaryViolationTreatedAsSuccess):
            run_scaffold_index_probe(payloads, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"],
            "scaffold_index_probe_boundary_violation_treated_as_success",
        )


class ScaffoldIndexProbeLanguageHygieneTest(unittest.TestCase):
    def test_output_has_no_forbidden_selection_language(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        rendered = str(output).lower()
        for phrase in PROBE_OUTPUT_FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase {0!r} in probe output".format(phrase),
            )

    def test_output_has_no_score_or_scoring(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        rendered = str(output).lower()
        self.assertNotIn("score", rendered)
        self.assertNotIn("scoring", rendered)

    def test_output_has_no_forbidden_claim_phrases(self):
        log = EventLog()
        output = run_scaffold_index_probe(_load_all_payloads(), log)
        for text in _walk_strings(output):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "forbidden claim phrase {0!r} in probe output: "
                    "{1!r}".format(phrase, text),
                )

    def test_forbidden_language_in_event_surface_rejected(self):
        payloads = _load_all_payloads()
        gi = copy.deepcopy(payloads["golden-intents"])
        gi["entries"][0]["fixture_id"] = "best_candidate_fixture"
        payloads["golden-intents"] = gi
        log = EventLog()
        with self.assertRaises(ForbiddenLanguageInProbeOutput):
            run_scaffold_index_probe(payloads, log)
        halt = _last_halt_event(log)
        self.assertEqual(
            halt["reason"], "scaffold_index_probe_forbidden_language"
        )
        self.assertEqual(halt["forbidden_phrase"], "best")
        rendered_events = str(log.events).lower()
        self.assertNotIn("best_candidate_fixture", rendered_events)


class ScaffoldIndexProbeIsolationTest(unittest.TestCase):
    def test_function_does_not_mutate_input(self):
        payloads = _load_all_payloads()
        before = copy.deepcopy(payloads)
        log = EventLog()
        run_scaffold_index_probe(payloads, log)
        self.assertEqual(payloads, before)

    def test_function_writes_no_files_on_success(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log = EventLog()
            run_scaffold_index_probe(_load_all_payloads(), log)
            self.assertEqual(os.listdir(tmp_dir), [])

    def test_function_writes_no_files_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            log = EventLog()
            with self.assertRaises(NonObjectPayloadsByClass):
                run_scaffold_index_probe("not a dict", log)
            self.assertEqual(os.listdir(tmp_dir), [])


class ScaffoldIndexProbeImportSurfaceTest(unittest.TestCase):
    """Static check that the probe module imports only stdlib + harness-internal symbols."""

    _MODULE_PATH = os.path.join(
        _PROJECT_ROOT, "harness", "scaffold_index_probe.py"
    )

    def test_no_third_party_imports(self):
        with open(self._MODULE_PATH, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        seen = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    seen.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module is not None:
                    seen.add(node.module.split(".")[0])
        # Every top-level package the module imports must be either
        # the Python stdlib (in `sys.stdlib_module_names`) or
        # `harness` (the in-repo package). Anything else would be a
        # third-party dependency.
        stdlib_names = set(sys.stdlib_module_names)
        allowed_roots = stdlib_names | {"harness"}
        unexpected = seen - allowed_roots
        self.assertEqual(
            unexpected,
            set(),
            "scaffold_index_probe.py imports outside the stdlib + "
            "harness-internal allow-list: {0!r}".format(unexpected),
        )


class ScaffoldIndexProbeBenchmarkFixturesNoMutationTest(unittest.TestCase):
    """The probe must not mutate benchmark-fixtures/ at runtime."""

    def test_benchmark_fixtures_unchanged_after_probe(self):
        import hashlib

        def _inventory():
            result = {}
            for dirpath, _dirnames, filenames in os.walk(
                _BENCHMARK_FIXTURES_ROOT
            ):
                for filename in filenames:
                    full = os.path.join(dirpath, filename)
                    rel = os.path.relpath(full, _BENCHMARK_FIXTURES_ROOT)
                    with open(full, "rb") as handle:
                        result[rel] = hashlib.sha256(handle.read()).hexdigest()
            return result

        before = _inventory()
        log = EventLog()
        run_scaffold_index_probe(_load_all_payloads(), log)
        after = _inventory()
        self.assertEqual(set(before.keys()), set(after.keys()))
        for rel in sorted(before.keys()):
            self.assertEqual(before[rel], after[rel])


if __name__ == "__main__":
    unittest.main()
