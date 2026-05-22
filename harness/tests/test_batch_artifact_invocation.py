"""Scaffold-internal combined batch artifact invocation protocol.

Per WO-38 (DC-041): this test exercises the full batch artifact path
end-to-end against `harness.batch_runner.run_payload_batch(...)` with
both the WO-35 / WO-36 per-run `snapshot_dir` and the WO-37
`batch_summary_output_path` provided simultaneously, across all three
admitted first-wave payload classes (`golden-intents`,
`hard-negatives`, `boundary-violations`). It is an invocation protocol
only: it does not modify any harness implementation module, does not
introduce a CLI, does not perform real benchmark execution, does not
collect metrics, does not score, does not rank, and does not select
any architecture.

The test writes only under a `tempfile.TemporaryDirectory()`. It
asserts:

- exactly three per-run snapshot files exist under the per-run dir;
- exactly one batch summary snapshot file exists at the caller-provided
  batch-summary path;
- the returned summary contains `batch_snapshot_evidence` with the
  three expected keys, and the SHA-256 / byte_length match the
  on-disk file;
- the on-disk batch summary file does not contain
  `batch_snapshot_evidence`;
- every per-run summary has `snapshot_written is True`, the six WO-36
  contract-status fields, `contract_status == "passed"` under default
  toy checks, and `measurement_recorded is False`;
- every artifact path lives inside the temp directory and none
  inside `benchmark-fixtures/`;
- the `benchmark-fixtures/` inventory and per-file SHA-256 are
  byte-identical before vs. after the invocation;
- the harness implementation modules under `harness/*.py` and the
  scaffold toy fixtures under `harness/tests/fixtures/*` are
  byte-identical before vs. after the invocation (no harness file
  is mutated by the invocation protocol);
- no string in the returned summary or the on-disk batch summary
  contains any phrase from `BATCH_SUMMARY_FORBIDDEN_PHRASES`
  (`FORBIDDEN_PHRASES` extended with `"score"` and `"scoring"` per
  the WO-35 Codex review-time hardening) or from
  `FORBIDDEN_CLAIM_PHRASES`.

This test uses only Python stdlib plus harness-internal imports.
"""

import hashlib
import json
import os
import tempfile
import unittest

from harness.batch_runner import run_payload_batch
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
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
_HARNESS_ROOT = os.path.join(_PROJECT_ROOT, "harness")
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
            # Skip any __pycache__ noise so the invariant is robust against
            # the bytecode cache; the test runs `python -B` so this set is
            # empty in normal use, but the safety net keeps the assertion
            # focused on source files.
            if "__pycache__" in dirpath:
                continue
            full = os.path.join(dirpath, filename)
            rel = os.path.relpath(full, root)
            result[rel] = _sha256_of_file(full)
    return result


class CombinedBatchArtifactInvocationTest(unittest.TestCase):
    def test_full_batch_artifact_invocation_writes_all_artifacts(self):
        # Capture before-state inventories so the no-mutation invariants
        # can be asserted at the end of the test.
        benchmark_fixtures_before = _inventory_and_hashes(
            _BENCHMARK_FIXTURES_ROOT
        )
        harness_before = _inventory_and_hashes(_HARNESS_ROOT)

        with tempfile.TemporaryDirectory() as tmp_dir:
            per_run_dir = os.path.join(tmp_dir, "per-run")
            os.makedirs(per_run_dir)
            batch_summary_output_path = os.path.join(
                tmp_dir, "batch-summary.json"
            )

            summary = run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                snapshot_dir=per_run_dir,
                batch_summary_output_path=batch_summary_output_path,
            )

            # (2) Exactly three per-run snapshot files written.
            per_run_files = sorted(os.listdir(per_run_dir))
            expected_per_run = sorted(
                "{0}-batch-snapshot.json".format(fc) for fc in ADMITTED_CLASSES
            )
            self.assertEqual(per_run_files, expected_per_run)

            # (3) Exactly one batch summary snapshot file written.
            self.assertTrue(os.path.isfile(batch_summary_output_path))
            tmp_top_entries = sorted(os.listdir(tmp_dir))
            self.assertIn("batch-summary.json", tmp_top_entries)
            self.assertIn("per-run", tmp_top_entries)
            # No other batch-summary-like JSON at the top of tmp_dir.
            json_at_top = [
                name for name in tmp_top_entries if name.endswith(".json")
            ]
            self.assertEqual(json_at_top, ["batch-summary.json"])

            # (4) Returned summary contains `batch_snapshot_evidence`.
            self.assertIn("batch_snapshot_evidence", summary)
            evidence = summary["batch_snapshot_evidence"]
            self.assertIn("output_path", evidence)
            self.assertIn("sha256", evidence)
            self.assertIn("byte_length", evidence)
            self.assertEqual(
                evidence["output_path"], batch_summary_output_path
            )

            # (5) Batch summary file on disk does NOT contain
            # `batch_snapshot_evidence`.
            on_disk = _load_json(batch_summary_output_path)
            self.assertNotIn("batch_snapshot_evidence", on_disk)

            # (6) Every per-run summary has snapshot_written True.
            self.assertEqual(len(summary["per_run_summaries"]), 3)
            for run in summary["per_run_summaries"]:
                self.assertIs(run["snapshot_written"], True)

            # (7) Every per-run summary contains the WO-36 contract-status
            # fields.
            wo36_fields = (
                "contract_status",
                "contract_checks_passed_count",
                "contract_checks_failed_count",
                "halt_count",
                "disqualified_configuration_count",
                "measurement_recorded",
            )
            for run in summary["per_run_summaries"]:
                for field in wo36_fields:
                    self.assertIn(field, run)
            # The persisted on-disk summary carries the same fields.
            for run in on_disk["per_run_summaries"]:
                for field in wo36_fields:
                    self.assertIn(field, run)

            # (8) Default contract statuses are all "passed".
            for run in summary["per_run_summaries"]:
                self.assertEqual(run["contract_status"], "passed")
            for run in on_disk["per_run_summaries"]:
                self.assertEqual(run["contract_status"], "passed")

            # (9) measurement_recorded is False everywhere.
            for run in summary["per_run_summaries"]:
                self.assertIs(run["measurement_recorded"], False)
            for run in on_disk["per_run_summaries"]:
                self.assertIs(run["measurement_recorded"], False)

            # (10) Batch summary snapshot SHA-256 and byte_length match
            # the returned `batch_snapshot_evidence`.
            with open(batch_summary_output_path, "rb") as handle:
                file_bytes = handle.read()
            file_sha256 = hashlib.sha256(file_bytes).hexdigest()
            self.assertEqual(evidence["sha256"], file_sha256)
            self.assertEqual(evidence["byte_length"], len(file_bytes))
            self.assertEqual(
                evidence["byte_length"],
                os.path.getsize(batch_summary_output_path),
            )

            # (11) All artifact paths are inside the temp directory and
            # none inside benchmark-fixtures/.
            tmp_dir_abs = os.path.abspath(tmp_dir)
            bench_abs = os.path.abspath(_BENCHMARK_FIXTURES_ROOT)
            artifact_paths = [batch_summary_output_path] + [
                os.path.join(per_run_dir, name)
                for name in os.listdir(per_run_dir)
            ]
            for path in artifact_paths:
                abs_path = os.path.abspath(path)
                self.assertTrue(
                    abs_path.startswith(tmp_dir_abs),
                    "artifact path {0!r} is not under tmp dir {1!r}".format(
                        abs_path, tmp_dir_abs
                    ),
                )
                self.assertFalse(
                    abs_path.startswith(bench_abs),
                    "artifact path {0!r} is under benchmark-fixtures/".format(
                        abs_path
                    ),
                )

            # (13) Returned summary and on-disk batch summary contain no
            # forbidden selection language and no forbidden claim phrase.
            for label, candidate in (
                ("returned summary", summary),
                ("on-disk summary", on_disk),
            ):
                rendered = str(candidate).lower()
                for phrase in BATCH_SUMMARY_FORBIDDEN_PHRASES:
                    self.assertNotIn(
                        phrase,
                        rendered,
                        "forbidden phrase {0!r} in {1}".format(phrase, label),
                    )
                for text in _walk_strings(candidate):
                    lowered = text.lower()
                    for phrase in FORBIDDEN_CLAIM_PHRASES:
                        self.assertNotIn(
                            phrase,
                            lowered,
                            "forbidden claim phrase {0!r} in {1}: {2!r}".format(
                                phrase, label, text
                            ),
                        )

        # (12) benchmark-fixtures/ inventory and SHA-256s unchanged.
        benchmark_fixtures_after = _inventory_and_hashes(
            _BENCHMARK_FIXTURES_ROOT
        )
        self.assertEqual(
            set(benchmark_fixtures_before.keys()),
            set(benchmark_fixtures_after.keys()),
        )
        for rel in sorted(benchmark_fixtures_before.keys()):
            self.assertEqual(
                benchmark_fixtures_before[rel],
                benchmark_fixtures_after[rel],
                "benchmark-fixtures/{0} SHA-256 changed".format(rel),
            )

        # (14) Harness implementation files (under harness/, excluding
        # __pycache__) are byte-identical before vs. after. The WO-38
        # invocation protocol must not mutate any harness file.
        harness_after = _inventory_and_hashes(_HARNESS_ROOT)
        self.assertEqual(
            set(harness_before.keys()),
            set(harness_after.keys()),
            "harness/ file set changed across the invocation",
        )
        for rel in sorted(harness_before.keys()):
            self.assertEqual(
                harness_before[rel],
                harness_after[rel],
                "harness/{0} SHA-256 changed across the invocation".format(
                    rel
                ),
            )


if __name__ == "__main__":
    unittest.main()
