"""Tests for harness.batch_runner.

Per WO-35 (DC-038): the batch runner is a thin scaffold-internal
orchestrator over `run_toy_dry_run(...)`. These tests assert: a
successful batch across all three admitted first-wave classes returns
a correct summary; the summary contains no forbidden selection language
and no forbidden claim phrases; snapshot writing is opt-in via
`snapshot_dir`; the runner does not mutate any file under
`benchmark-fixtures/`; the runner uses only caller-provided specs (no
auto-discovery); every named rejection path raises before any dry-run
invocation; and payload-loader rejection during one spec stops the
batch before subsequent specs run.

The tests use only Python stdlib plus harness-internal imports. They
write only inside a `tempfile.TemporaryDirectory()` and modify no
existing file.
"""

import hashlib
import json
import os
import tempfile
import unittest

import harness.batch_runner as batch_runner_module
from harness.batch_runner import (
    EmptyPayloadSpecs,
    MalformedPayloadSpec,
    MissingCommonInput,
    REQUIRED_COMMON_INPUT_KEYS,
    REQUIRED_SPEC_KEYS,
    run_payload_batch,
)
from harness.payload_loader import (
    FORBIDDEN_CLAIM_PHRASES,
    PayloadFixtureClassMismatch,
)
from harness.review_package import FORBIDDEN_PHRASES


_FIXTURE_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
_FIXTURE_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_fixture.json")
_CONFIG_PATH = os.path.join(_FIXTURE_DIR, "toy_scaffold_config.json")
_MANIFEST_PATH = os.path.join(_FIXTURE_DIR, "toy_retrieval_manifest.json")
_MANIFEST_ID = "toy-scaffold-manifest"
_DETERMINISTIC_SEED = 42

_PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.pardir, os.pardir)
)
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")

ADMITTED_CLASSES = (
    "golden-intents",
    "hard-negatives",
    "boundary-violations",
)

BATCH_SUMMARY_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)


def _sha256_of_file(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        hasher.update(handle.read())
    return hasher.hexdigest()


def _load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


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


def _payload_path_for(fixture_class):
    return os.path.join(_BENCHMARK_FIXTURES_ROOT, fixture_class, "wave-001.json")


def _common_inputs():
    return {
        "fixture_path": _FIXTURE_PATH,
        "fixture_sha256": _sha256_of_file(_FIXTURE_PATH),
        "config_path": _CONFIG_PATH,
        "registered_config": _load_json(_CONFIG_PATH),
        "deterministic_seed": _DETERMINISTIC_SEED,
        "manifest_path": _MANIFEST_PATH,
        "expected_manifest_id": _MANIFEST_ID,
    }


def _admitted_specs():
    return [
        {"fixture_class": fc, "payload_path": _payload_path_for(fc)}
        for fc in ADMITTED_CLASSES
    ]


def _inventory_and_hashes(root):
    if not os.path.isdir(root):
        return {}
    result = {}
    for dirpath, _dirnames, filenames in os.walk(root):
        for filename in filenames:
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, root)
            result[rel] = _sha256_of_file(full)
    return result


class BatchRunnerSuccessTest(unittest.TestCase):
    def test_successful_batch_across_three_classes(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        self.assertEqual(summary["batch_kind"], "scaffold_payload_batch")
        self.assertEqual(summary["run_count"], 3)
        self.assertEqual(summary["fixture_classes"], list(ADMITTED_CLASSES))
        self.assertEqual(len(summary["per_run_summaries"]), 3)

    def test_each_class_appears_exactly_once(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        classes = [s["fixture_class"] for s in summary["per_run_summaries"]]
        self.assertEqual(sorted(classes), sorted(ADMITTED_CLASSES))
        self.assertEqual(len(set(classes)), 3)

    def test_summary_records_no_selection(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        self.assertIs(summary["selection_made"], False)
        for run in summary["per_run_summaries"]:
            self.assertIs(run["selection_made"], False)

    def test_summary_has_no_forbidden_selection_language(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        rendered = str(summary).lower()
        for phrase in BATCH_SUMMARY_FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden summary phrase {0!r} in batch summary".format(phrase),
            )

    def test_summary_has_no_forbidden_claim_phrases(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        for text in _walk_strings(summary):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "forbidden claim phrase {0!r} in batch summary: {1!r}".format(
                        phrase, text
                    ),
                )

    def test_per_run_summary_contains_expected_fields(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        for run in summary["per_run_summaries"]:
            self.assertIn("fixture_class", run)
            self.assertIn("payload_entry_count", run)
            self.assertIn("event_count", run)
            self.assertIn("selection_made", run)
            self.assertIn("snapshot_written", run)
            self.assertEqual(run["payload_entry_count"], 2)
            self.assertGreater(run["event_count"], 0)


class BatchRunnerSnapshotTest(unittest.TestCase):
    def test_no_snapshot_dir_writes_no_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sentinel = os.path.join(tmp_dir, "should_be_empty")
            os.mkdir(sentinel)
            summary = run_payload_batch(
                _admitted_specs(), _common_inputs(), snapshot_dir=None
            )
            self.assertEqual(os.listdir(sentinel), [])
            for run in summary["per_run_summaries"]:
                self.assertIs(run["snapshot_written"], False)

    def test_snapshot_dir_writes_three_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            summary = run_payload_batch(
                _admitted_specs(), _common_inputs(), snapshot_dir=tmp_dir
            )
            files = sorted(os.listdir(tmp_dir))
            expected_files = sorted(
                "{0}-batch-snapshot.json".format(fc) for fc in ADMITTED_CLASSES
            )
            self.assertEqual(files, expected_files)
            for run in summary["per_run_summaries"]:
                self.assertIs(run["snapshot_written"], True)

    def test_snapshot_files_not_written_under_benchmark_fixtures(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_payload_batch(_admitted_specs(), _common_inputs(), snapshot_dir=tmp_dir)
            # Sanity: every written file path is under tmp_dir, not under
            # benchmark-fixtures/.
            for fc in ADMITTED_CLASSES:
                written = os.path.join(tmp_dir, "{0}-batch-snapshot.json".format(fc))
                self.assertTrue(os.path.isfile(written))
                self.assertTrue(written.startswith(tmp_dir))
                self.assertFalse(written.startswith(_BENCHMARK_FIXTURES_ROOT))


class BatchRunnerNoMutationTest(unittest.TestCase):
    def test_benchmark_fixtures_unchanged_after_batch(self):
        before = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        with tempfile.TemporaryDirectory() as tmp_dir:
            run_payload_batch(_admitted_specs(), _common_inputs(), snapshot_dir=tmp_dir)
        after = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        self.assertEqual(set(before.keys()), set(after.keys()))
        for rel in sorted(before.keys()):
            self.assertEqual(before[rel], after[rel])

    def test_runner_does_not_auto_discover_from_benchmark_fixtures(self):
        # The runner must NOT walk benchmark-fixtures/ to discover payloads.
        # Proof: provide specs that copy payload content into a tempdir and
        # point payload_path at the tempdir. The batch must succeed using
        # only those caller-provided paths.
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Copy the three WO-31 payloads into the tempdir so caller-provided
            # paths point outside benchmark-fixtures/.
            staged_specs = []
            for fc in ADMITTED_CLASSES:
                src = _payload_path_for(fc)
                dst = os.path.join(tmp_dir, "{0}.json".format(fc))
                with open(src, "rb") as in_f, open(dst, "wb") as out_f:
                    out_f.write(in_f.read())
                staged_specs.append({"fixture_class": fc, "payload_path": dst})
            # No snapshot dir; just verify the batch reads from the staged
            # paths and succeeds without touching benchmark-fixtures/.
            bf_inventory_before = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
            summary = run_payload_batch(staged_specs, _common_inputs())
            bf_inventory_after = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
            self.assertEqual(summary["run_count"], 3)
            self.assertEqual(bf_inventory_before, bf_inventory_after)


class BatchRunnerRejectionTest(unittest.TestCase):
    def test_empty_payload_specs_rejected(self):
        with self.assertRaises(EmptyPayloadSpecs):
            run_payload_batch([], _common_inputs())

    def test_non_list_payload_specs_rejected(self):
        with self.assertRaises(EmptyPayloadSpecs):
            run_payload_batch("not a list", _common_inputs())

    def test_malformed_spec_missing_fixture_class_rejected(self):
        specs = [{"payload_path": _payload_path_for("golden-intents")}]
        with self.assertRaises(MalformedPayloadSpec):
            run_payload_batch(specs, _common_inputs())

    def test_malformed_spec_missing_payload_path_rejected(self):
        specs = [{"fixture_class": "golden-intents"}]
        with self.assertRaises(MalformedPayloadSpec):
            run_payload_batch(specs, _common_inputs())

    def test_malformed_spec_non_string_value_rejected(self):
        specs = [{"fixture_class": 42, "payload_path": "x"}]
        with self.assertRaises(MalformedPayloadSpec):
            run_payload_batch(specs, _common_inputs())

    def test_missing_common_input_key_rejected(self):
        for missing_key in REQUIRED_COMMON_INPUT_KEYS:
            with self.subTest(missing_key=missing_key):
                inputs = _common_inputs()
                del inputs[missing_key]
                with self.assertRaises(MissingCommonInput):
                    run_payload_batch(_admitted_specs(), inputs)

    def test_non_dict_common_inputs_rejected(self):
        with self.assertRaises(MissingCommonInput):
            run_payload_batch(_admitted_specs(), "not a dict")

    def test_validation_runs_before_any_dry_run_invocation(self):
        # Patch run_toy_dry_run inside the batch_runner module to fail the
        # test if invoked, then submit an invalid spec set. The exception
        # must come from validation, not from dry-run.
        original_dry_run = batch_runner_module.run_toy_dry_run
        try:
            batch_runner_module.run_toy_dry_run = lambda **kwargs: self.fail(
                "run_toy_dry_run must not be invoked when validation fails"
            )
            with self.assertRaises(EmptyPayloadSpecs):
                run_payload_batch([], _common_inputs())
            with self.assertRaises(MalformedPayloadSpec):
                run_payload_batch([{"fixture_class": "x"}], _common_inputs())
            with self.assertRaises(MissingCommonInput):
                run_payload_batch(_admitted_specs(), {})
        finally:
            batch_runner_module.run_toy_dry_run = original_dry_run

    def test_payload_loader_rejection_stops_batch_before_later_specs(self):
        # Build a spec list where the first spec has mismatched fixture_class
        # vs. payload contents. The dry-run / payload loader will raise
        # PayloadFixtureClassMismatch on the first invocation; the batch
        # must abort before the second spec is invoked.
        invocation_count = {"value": 0}
        original_dry_run = batch_runner_module.run_toy_dry_run

        def _counting_dry_run(**kwargs):
            invocation_count["value"] += 1
            return original_dry_run(**kwargs)

        try:
            batch_runner_module.run_toy_dry_run = _counting_dry_run
            bad_first = [
                # First spec: golden-intents payload but claim it's hard-negatives.
                {
                    "fixture_class": "hard-negatives",
                    "payload_path": _payload_path_for("golden-intents"),
                },
                # Second spec: would succeed if reached.
                {
                    "fixture_class": "golden-intents",
                    "payload_path": _payload_path_for("golden-intents"),
                },
            ]
            with self.assertRaises(PayloadFixtureClassMismatch):
                run_payload_batch(bad_first, _common_inputs())
            # Exactly one invocation (the bad first spec); the loop must
            # have aborted before the second spec ran.
            self.assertEqual(invocation_count["value"], 1)
        finally:
            batch_runner_module.run_toy_dry_run = original_dry_run


# WO-36 contract-status surface phrases. Mirror BATCH_SUMMARY_FORBIDDEN_PHRASES
# plus extra contract-status hygiene (`rank`, `winner`, `best`,
# `production-ready`, `recommend`, `recommended`, `architecture`) are already
# covered by FORBIDDEN_PHRASES; this set adds nothing beyond the existing list.
WO36_BATCH_SUMMARY_FORBIDDEN_PHRASES = BATCH_SUMMARY_FORBIDDEN_PHRASES


def _always_fail_check():
    """Return a contract_checks override that fails every response."""
    return [("scaffold_always_fail", lambda response: False)]


class BatchRunnerContractStatusDefaultTest(unittest.TestCase):
    def test_default_batch_marks_every_run_passed(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        for run in summary["per_run_summaries"]:
            self.assertEqual(run["contract_status"], "passed")

    def test_default_batch_has_zero_failed_count(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        for run in summary["per_run_summaries"]:
            self.assertEqual(run["contract_checks_failed_count"], 0)

    def test_default_batch_has_zero_disqualified_count(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        for run in summary["per_run_summaries"]:
            self.assertEqual(run["disqualified_configuration_count"], 0)

    def test_default_batch_records_no_measurement(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        for run in summary["per_run_summaries"]:
            self.assertIs(run["measurement_recorded"], False)

    def test_default_batch_per_run_summary_has_new_fields(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        for run in summary["per_run_summaries"]:
            self.assertIn("contract_status", run)
            self.assertIn("contract_checks_passed_count", run)
            self.assertIn("contract_checks_failed_count", run)
            self.assertIn("halt_count", run)
            self.assertIn("disqualified_configuration_count", run)
            self.assertIn("measurement_recorded", run)
            # The scaffold toy contract checks pass for every default
            # invocation; passed_count is the count produced by the
            # dry-run's default toy check list.
            self.assertGreater(run["contract_checks_passed_count"], 0)


class BatchRunnerContractStatusFailureTest(unittest.TestCase):
    def _failing_inputs(self):
        inputs = _common_inputs()
        inputs["contract_checks"] = _always_fail_check()
        return inputs

    def test_failing_contract_check_marks_run_failed(self):
        summary = run_payload_batch(_admitted_specs(), self._failing_inputs())
        for run in summary["per_run_summaries"]:
            self.assertEqual(run["contract_status"], "failed")

    def test_failing_contract_check_surfaces_failed_count(self):
        summary = run_payload_batch(_admitted_specs(), self._failing_inputs())
        for run in summary["per_run_summaries"]:
            self.assertGreater(run["contract_checks_failed_count"], 0)

    def test_failing_contract_check_surfaces_disqualified_count(self):
        summary = run_payload_batch(_admitted_specs(), self._failing_inputs())
        for run in summary["per_run_summaries"]:
            self.assertGreater(run["disqualified_configuration_count"], 0)

    def test_failing_contract_check_surfaces_measurement_recorded_field(self):
        # WO-36 review-discipline note: the WO-36 packet asks that an
        # injected failing contract check surface
        # `measurement_recorded is True` in the per-run summary. The
        # repository's existing WO-19 / DC-022 invariant explicitly
        # forbids the dry-run from emitting any `measurement_recorded`
        # event after a contract disqualification (asserted by
        # `test_contract_failure_disqualifies_toy_configuration` in
        # `test_dry_run.py`). The contract runner only emits
        # `measurement_recorded` from `record_measurement(...)`, which
        # `run_toy_dry_run(...)` never calls. Per the field-semantics
        # spec in packet item #3 ("`measurement_recorded` must be `True`
        # only if a `measurement_recorded` event exists in the package
        # events") the field accurately reports `False` in both the
        # clean-run and the contract-failure paths, because no
        # `measurement_recorded` event is emitted by the scaffold at
        # all. This test therefore asserts the field surfaces and
        # accurately reflects the WO-19 halt-before-measurement
        # invariant (i.e., `False` under failure). The conflict between
        # packet item #8 and the existing WO-19 invariant is flagged in
        # the WO-36 evidence report.
        summary = run_payload_batch(_admitted_specs(), self._failing_inputs())
        for run in summary["per_run_summaries"]:
            self.assertIn("measurement_recorded", run)
            # Per WO-19 / DC-022: the dry-run halts measurement after
            # contract disqualification, so no measurement_recorded
            # event is emitted and the field accurately reports False.
            self.assertIs(run["measurement_recorded"], False)


class BatchRunnerFailingContractNoForbiddenLanguageTest(unittest.TestCase):
    def test_failing_batch_summary_has_no_forbidden_selection_language(self):
        inputs = _common_inputs()
        inputs["contract_checks"] = _always_fail_check()
        summary = run_payload_batch(_admitted_specs(), inputs)
        rendered = str(summary).lower()
        for phrase in WO36_BATCH_SUMMARY_FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase {0!r} in failing batch summary".format(phrase),
            )

    def test_failing_batch_summary_has_no_forbidden_claim_phrases(self):
        inputs = _common_inputs()
        inputs["contract_checks"] = _always_fail_check()
        summary = run_payload_batch(_admitted_specs(), inputs)
        for text in _walk_strings(summary):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "forbidden claim phrase {0!r} in failing batch summary: {1!r}".format(
                        phrase, text
                    ),
                )


class BatchRunnerFailingContractNoMutationTest(unittest.TestCase):
    def test_failing_contract_check_does_not_mutate_benchmark_fixtures(self):
        before = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        inputs = _common_inputs()
        inputs["contract_checks"] = _always_fail_check()
        run_payload_batch(_admitted_specs(), inputs)
        after = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        self.assertEqual(set(before.keys()), set(after.keys()))
        for rel in sorted(before.keys()):
            self.assertEqual(before[rel], after[rel])


# --------------------------------------------------------------------
# WO-37 / DC-040: scaffold batch summary snapshot boundary.
#
# The runner accepts an optional `batch_summary_output_path` kwarg.
# When provided, the batch summary is persisted via the existing
# `harness.artifact_snapshot.write_scaffold_snapshot(...)` writer
# and the returned in-memory summary is augmented with a
# `batch_snapshot_evidence` field carrying `{output_path, sha256,
# byte_length}`. The on-disk JSON file does not contain
# `batch_snapshot_evidence`. These tests assert the documented
# boundary: default no-write path, deterministic write path, integrity
# of sha256 and byte_length, presence of contract-status fields in the
# on-disk file, absence of `batch_snapshot_evidence` on disk, presence
# of `batch_snapshot_evidence` in the returned dict, failing-contract
# write path, no mutation of `benchmark-fixtures/`, and forbidden
# language hygiene of the persisted summary.
# --------------------------------------------------------------------


class BatchRunnerBatchSummarySnapshotDefaultTest(unittest.TestCase):
    def test_default_call_attaches_no_batch_snapshot_evidence(self):
        summary = run_payload_batch(_admitted_specs(), _common_inputs())
        self.assertNotIn("batch_snapshot_evidence", summary)

    def test_default_call_writes_no_batch_summary_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            sentinel = os.path.join(tmp_dir, "should_be_empty")
            os.mkdir(sentinel)
            run_payload_batch(_admitted_specs(), _common_inputs())
            # The runner did not receive `batch_summary_output_path`, so
            # the caller-provided sentinel directory must remain empty.
            self.assertEqual(os.listdir(sentinel), [])

    def test_explicit_none_output_path_attaches_no_evidence(self):
        summary = run_payload_batch(
            _admitted_specs(),
            _common_inputs(),
            batch_summary_output_path=None,
        )
        self.assertNotIn("batch_snapshot_evidence", summary)


class BatchRunnerBatchSummarySnapshotWriteTest(unittest.TestCase):
    def test_provided_output_path_writes_one_deterministic_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            files = sorted(os.listdir(tmp_dir))
            self.assertEqual(files, ["batch-summary.json"])
            self.assertTrue(os.path.isfile(output_path))

    def test_batch_snapshot_evidence_sha256_matches_written_bytes(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            summary = run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            self.assertIn("batch_snapshot_evidence", summary)
            evidence = summary["batch_snapshot_evidence"]
            with open(output_path, "rb") as handle:
                file_bytes = handle.read()
            file_sha256 = hashlib.sha256(file_bytes).hexdigest()
            self.assertEqual(evidence["sha256"], file_sha256)

    def test_batch_snapshot_evidence_byte_length_matches_written_file(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            summary = run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            evidence = summary["batch_snapshot_evidence"]
            on_disk_length = os.path.getsize(output_path)
            self.assertEqual(evidence["byte_length"], on_disk_length)

    def test_batch_snapshot_evidence_output_path_matches_caller_value(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            summary = run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            evidence = summary["batch_snapshot_evidence"]
            self.assertEqual(evidence["output_path"], output_path)

    def test_on_disk_summary_contains_per_run_contract_status_fields(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            on_disk = _load_json(output_path)
            self.assertIn("per_run_summaries", on_disk)
            self.assertEqual(len(on_disk["per_run_summaries"]), 3)
            for run in on_disk["per_run_summaries"]:
                for field in (
                    "contract_status",
                    "contract_checks_passed_count",
                    "contract_checks_failed_count",
                    "halt_count",
                    "disqualified_configuration_count",
                    "measurement_recorded",
                ):
                    self.assertIn(field, run)
                self.assertEqual(run["contract_status"], "passed")

    def test_on_disk_summary_omits_batch_snapshot_evidence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            on_disk = _load_json(output_path)
            self.assertNotIn("batch_snapshot_evidence", on_disk)

    def test_in_memory_summary_contains_batch_snapshot_evidence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            summary = run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            self.assertIn("batch_snapshot_evidence", summary)
            evidence = summary["batch_snapshot_evidence"]
            self.assertIn("output_path", evidence)
            self.assertIn("sha256", evidence)
            self.assertIn("byte_length", evidence)


class BatchRunnerBatchSummarySnapshotFailingContractTest(unittest.TestCase):
    def test_failing_contract_batch_still_writes_summary_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            inputs = _common_inputs()
            inputs["contract_checks"] = _always_fail_check()
            summary = run_payload_batch(
                _admitted_specs(),
                inputs,
                batch_summary_output_path=output_path,
            )
            # The failing-contract batch must still produce the snapshot.
            self.assertTrue(os.path.isfile(output_path))
            self.assertIn("batch_snapshot_evidence", summary)
            on_disk = _load_json(output_path)
            for run in on_disk["per_run_summaries"]:
                self.assertEqual(run["contract_status"], "failed")
                # WO-19 / DC-022 invariant: even under contract failure,
                # the dry-run never calls `record_measurement(...)`, so
                # the boolean accurately reports False on disk too.
                self.assertIs(run["measurement_recorded"], False)


class BatchRunnerBatchSummarySnapshotNoMutationTest(unittest.TestCase):
    def test_batch_summary_snapshot_does_not_mutate_benchmark_fixtures(self):
        before = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
        after = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        self.assertEqual(set(before.keys()), set(after.keys()))
        for rel in sorted(before.keys()):
            self.assertEqual(before[rel], after[rel])


class BatchRunnerBatchSummarySnapshotForbiddenLanguageTest(unittest.TestCase):
    def test_persisted_summary_has_no_forbidden_selection_language(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            with open(output_path, "r", encoding="utf-8") as handle:
                rendered = handle.read().lower()
            for phrase in BATCH_SUMMARY_FORBIDDEN_PHRASES:
                self.assertNotIn(
                    phrase,
                    rendered,
                    "forbidden phrase {0!r} in persisted batch summary".format(
                        phrase
                    ),
                )

    def test_persisted_summary_has_no_forbidden_claim_phrases(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = os.path.join(tmp_dir, "batch-summary.json")
            run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                batch_summary_output_path=output_path,
            )
            on_disk = _load_json(output_path)
            for text in _walk_strings(on_disk):
                lowered = text.lower()
                for phrase in FORBIDDEN_CLAIM_PHRASES:
                    self.assertNotIn(
                        phrase,
                        lowered,
                        "forbidden claim phrase {0!r} in persisted batch "
                        "summary: {1!r}".format(phrase, text),
                    )


if __name__ == "__main__":
    unittest.main()
