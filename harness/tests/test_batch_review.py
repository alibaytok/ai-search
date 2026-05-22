"""Tests for harness.batch_review.

Per WO-39 / WO-40 (DC-042): the batch review summary is a
scaffold-internal observation-only assembler over the existing
`harness.batch_runner.run_payload_batch(...)` summary. These tests
assert:

- a clean batch summary (the default toy contract checks, all three
  admitted first-wave classes) produces a well-formed review summary
  with exactly the eight allowed top-level keys;
- contract status counts, snapshot counts, and measurement-recorded
  count are computed from the per-run summaries (default = all
  passed, three snapshots written, zero measurements);
- the failing-contract batch summary produces failed > 0 with
  measurement_recorded_count == 0 (the WO-19 / DC-022 invariant
  ratified at WO-36 review continues to hold);
- every documented rejection path raises the matching named
  exception before any aggregation;
- the assembled review summary contains no `FORBIDDEN_PHRASES`
  substring, no `"score"`, no `"scoring"`, and no
  `FORBIDDEN_CLAIM_PHRASES` substring;
- assembling the review summary does not mutate
  `benchmark-fixtures/`.

The tests use only Python stdlib plus harness-internal imports. They
write only inside a `tempfile.TemporaryDirectory()` when invoking the
batch runner; the review summary assembler itself does not write to
disk.
"""

import hashlib
import json
import os
import tempfile
import unittest

from harness.batch_review import (
    ALLOWED_REVIEW_KEYS,
    ForbiddenClaimInBatchSummary,
    ForbiddenLanguageInBatchSummary,
    MissingPerRunSummaries,
    NonDictBatchSummary,
    NonListPerRunSummaries,
    SelectionMadeInBatchSummary,
    assemble_batch_review_summary,
)
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
_BENCHMARK_FIXTURES_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")

ADMITTED_CLASSES = (
    "golden-intents",
    "hard-negatives",
    "boundary-violations",
)

REVIEW_SUMMARY_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
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


def _always_fail_check():
    return [("scaffold_always_fail", lambda response: False)]


class BatchReviewCleanBatchTest(unittest.TestCase):
    def test_clean_batch_summary_produces_review_summary(self):
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        self.assertIsInstance(review, dict)
        self.assertEqual(review["review_kind"], "scaffold_batch_review_summary")
        self.assertEqual(review["run_count"], 3)
        self.assertEqual(review["fixture_classes"], list(ADMITTED_CLASSES))

    def test_review_summary_has_exactly_allowed_top_level_keys(self):
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        self.assertEqual(set(review.keys()), set(ALLOWED_REVIEW_KEYS))

    def test_default_batch_contract_status_counts_all_passed(self):
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        self.assertEqual(
            review["contract_status_counts"],
            {"passed": 3, "failed": 0},
        )

    def test_default_batch_snapshot_counts_match_per_run_status(self):
        # Without snapshot_dir: every per-run summary records
        # snapshot_written False; the review summary surfaces this.
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        self.assertEqual(
            review["snapshot_counts"],
            {"written": 0, "not_written": 3},
        )

    def test_snapshot_dir_batch_snapshot_counts_match_per_run_status(self):
        # With snapshot_dir: every per-run summary records
        # snapshot_written True; the review summary surfaces this.
        with tempfile.TemporaryDirectory() as tmp_dir:
            batch_summary = run_payload_batch(
                _admitted_specs(),
                _common_inputs(),
                snapshot_dir=tmp_dir,
            )
        review = assemble_batch_review_summary(batch_summary)
        self.assertEqual(
            review["snapshot_counts"],
            {"written": 3, "not_written": 0},
        )

    def test_default_batch_measurement_recorded_count_is_zero(self):
        # WO-19 / DC-022 invariant ratified at WO-36 review: the
        # dry-run never calls record_measurement(), so the review
        # summary's count is zero under the clean-run path.
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        self.assertEqual(review["measurement_recorded_count"], 0)


class BatchReviewFailingContractTest(unittest.TestCase):
    def _failing_inputs(self):
        inputs = _common_inputs()
        inputs["contract_checks"] = _always_fail_check()
        return inputs

    def test_failing_contract_batch_review_surfaces_failed_count(self):
        batch_summary = run_payload_batch(
            _admitted_specs(), self._failing_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        self.assertEqual(
            review["contract_status_counts"],
            {"passed": 0, "failed": 3},
        )

    def test_failing_contract_batch_review_measurement_recorded_count_is_zero(self):
        # WO-19 / DC-022 invariant: even under contract failure the
        # dry-run does not call record_measurement(); the review
        # summary's count remains zero. WO-36 review ratified this
        # observation; WO-39 / WO-40 surfaces it at the batch-review
        # level.
        batch_summary = run_payload_batch(
            _admitted_specs(), self._failing_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        self.assertEqual(review["measurement_recorded_count"], 0)


class BatchReviewRejectionTest(unittest.TestCase):
    def test_non_dict_input_rejected(self):
        with self.assertRaises(NonDictBatchSummary):
            assemble_batch_review_summary("not a dict")
        with self.assertRaises(NonDictBatchSummary):
            assemble_batch_review_summary(None)
        with self.assertRaises(NonDictBatchSummary):
            assemble_batch_review_summary(42)
        with self.assertRaises(NonDictBatchSummary):
            assemble_batch_review_summary(["not", "a", "dict"])

    def test_missing_per_run_summaries_rejected(self):
        with self.assertRaises(MissingPerRunSummaries):
            assemble_batch_review_summary(
                {"batch_kind": "scaffold_payload_batch"}
            )

    def test_non_list_per_run_summaries_rejected(self):
        with self.assertRaises(NonListPerRunSummaries):
            assemble_batch_review_summary(
                {"per_run_summaries": "not a list"}
            )
        with self.assertRaises(NonListPerRunSummaries):
            assemble_batch_review_summary(
                {"per_run_summaries": {"not": "a list"}}
            )

    def test_selection_made_true_rejected(self):
        with self.assertRaises(SelectionMadeInBatchSummary):
            assemble_batch_review_summary(
                {
                    "per_run_summaries": [],
                    "selection_made": True,
                }
            )

    def test_forbidden_selection_language_rejected(self):
        # Any phrase from FORBIDDEN_PHRASES, or "score" / "scoring",
        # anywhere in any string scalar of the input must be rejected.
        for phrase in REVIEW_SUMMARY_FORBIDDEN_PHRASES:
            with self.subTest(phrase=phrase):
                bad = {
                    "per_run_summaries": [],
                    "selection_made": False,
                    "batch_note": "this note contains the word {0}".format(
                        phrase
                    ),
                }
                with self.assertRaises(ForbiddenLanguageInBatchSummary):
                    assemble_batch_review_summary(bad)

    def test_forbidden_claim_phrase_rejected(self):
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            with self.subTest(phrase=phrase):
                bad = {
                    "per_run_summaries": [],
                    "selection_made": False,
                    "batch_note": "this note contains the phrase {0}".format(
                        phrase
                    ),
                }
                with self.assertRaises(ForbiddenClaimInBatchSummary):
                    assemble_batch_review_summary(bad)


class BatchReviewSummaryLanguageHygieneTest(unittest.TestCase):
    def test_review_summary_has_no_forbidden_selection_language(self):
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        rendered = str(review).lower()
        for phrase in REVIEW_SUMMARY_FORBIDDEN_PHRASES:
            self.assertNotIn(
                phrase,
                rendered,
                "forbidden phrase {0!r} in review summary".format(phrase),
            )

    def test_review_summary_has_no_forbidden_claim_phrases(self):
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        for text in _walk_strings(review):
            lowered = text.lower()
            for phrase in FORBIDDEN_CLAIM_PHRASES:
                self.assertNotIn(
                    phrase,
                    lowered,
                    "forbidden claim phrase {0!r} in review summary: "
                    "{1!r}".format(phrase, text),
                )


class BatchReviewNoMutationTest(unittest.TestCase):
    def test_assembling_review_summary_does_not_mutate_benchmark_fixtures(self):
        before = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        batch_summary = run_payload_batch(
            _admitted_specs(), _common_inputs()
        )
        review = assemble_batch_review_summary(batch_summary)
        # The review summary is a fresh dict; the batch summary was
        # not modified to acquire a review field.
        self.assertNotIn("review", batch_summary)
        self.assertEqual(review["selection_made"], False)
        after = _inventory_and_hashes(_BENCHMARK_FIXTURES_ROOT)
        self.assertEqual(set(before.keys()), set(after.keys()))
        for rel in sorted(before.keys()):
            self.assertEqual(before[rel], after[rel])


if __name__ == "__main__":
    unittest.main()
