"""Tests for the benchmark fixture skeleton.

Per WO-20 / DC-023 the skeleton was originally empty-only across all six
category subdirectories. Per WO-31 / DC-034 the skeleton transitions to a
"first synthetic payload wave" state: three classes admit `*.json` payload
files alongside their `.gitkeep`; the other three classes remain empty.

Covers:
- the `benchmark-fixtures/` root and all required category subdirectories
  exist (WO-20 invariant, preserved)
- the three excluded classes (`latency-profiles`, `update-profiles`,
  `adversarial`) still contain exactly `.gitkeep` (WO-20 invariant,
  scoped to excluded classes under WO-31)
- the three admitted classes (`golden-intents`, `hard-negatives`,
  `boundary-violations`) contain `.gitkeep` plus only `*.json` payload
  files; no other entry is admitted (WO-31 transition)
- no non-JSON payload file (`.csv`, `.txt`, etc.) exists anywhere under
  `benchmark-fixtures/` (WO-20 invariant, preserved)
- payload-content validation for admitted JSON files is delegated to
  `harness/tests/test_fixture_payloads.py` (WO-31)
- `benchmark-fixtures/README.md` documents the post-first-wave state
  while preserving the WO-20 literal phrases (`"no real benchmark data"`
  and `"future codex packet"`) and adds the WO-31 scoping language
"""

import os
import unittest


_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_FIXTURE_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")

REQUIRED_CATEGORIES = (
    "golden-intents",
    "hard-negatives",
    "boundary-violations",
    "latency-profiles",
    "update-profiles",
    "adversarial",
)

# Classes that may carry `*.json` payload files under WO-31 / DC-034.
ADMITTED_FIRST_WAVE_CLASSES = (
    "golden-intents",
    "hard-negatives",
    "boundary-violations",
)

# Classes that must still contain exactly `.gitkeep` under WO-31 / DC-034.
EXCLUDED_FIRST_WAVE_CLASSES = (
    "latency-profiles",
    "update-profiles",
    "adversarial",
)

# Non-JSON payload extensions remain forbidden anywhere under
# `benchmark-fixtures/`. JSON files are admitted only under the three
# first-wave classes and are validated by `test_fixture_payloads.py`.
FORBIDDEN_NON_JSON_PAYLOAD_EXTENSIONS = (".csv", ".txt")


class FixtureSkeletonTest(unittest.TestCase):
    def test_fixture_root_exists(self):
        self.assertTrue(
            os.path.isdir(_FIXTURE_ROOT),
            "benchmark-fixtures/ directory does not exist",
        )

    def test_all_required_categories_exist(self):
        for category in REQUIRED_CATEGORIES:
            path = os.path.join(_FIXTURE_ROOT, category)
            self.assertTrue(
                os.path.isdir(path),
                "missing required category directory: {0}".format(category),
            )

    def test_excluded_classes_contain_only_gitkeep(self):
        # The three excluded classes must still match the WO-20 / DC-023
        # invariant exactly.
        for category in EXCLUDED_FIRST_WAVE_CLASSES:
            path = os.path.join(_FIXTURE_ROOT, category)
            entries = sorted(os.listdir(path))
            self.assertEqual(
                entries,
                [".gitkeep"],
                "excluded class {0} must contain only .gitkeep; got: {1}".format(
                    category, entries
                ),
            )

    def test_admitted_classes_contain_gitkeep_and_only_json_payloads(self):
        # The three admitted classes may contain `.gitkeep` plus zero or
        # more `*.json` payload files; no other entry is admitted at the
        # skeleton level. Per-payload content is checked by
        # `test_fixture_payloads.py`.
        for category in ADMITTED_FIRST_WAVE_CLASSES:
            path = os.path.join(_FIXTURE_ROOT, category)
            entries = sorted(os.listdir(path))
            self.assertIn(
                ".gitkeep",
                entries,
                "admitted class {0} must still contain .gitkeep".format(category),
            )
            for entry in entries:
                if entry == ".gitkeep":
                    continue
                self.assertTrue(
                    entry.lower().endswith(".json"),
                    "admitted class {0} contains a non-JSON entry: {1}".format(
                        category, entry
                    ),
                )
                full_path = os.path.join(path, entry)
                self.assertTrue(
                    os.path.isfile(full_path),
                    "admitted class {0} entry must be a file: {1}".format(
                        category, entry
                    ),
                )

    def test_no_non_json_payload_files_under_fixture_root(self):
        # Non-JSON payload extensions remain forbidden anywhere under
        # `benchmark-fixtures/`. (JSON files are validated by
        # `test_fixture_payloads.py` for admitted classes and rejected by
        # `test_excluded_classes_contain_only_gitkeep` for excluded ones.)
        for dirpath, _dirnames, filenames in os.walk(_FIXTURE_ROOT):
            for filename in filenames:
                lowered = filename.lower()
                for extension in FORBIDDEN_NON_JSON_PAYLOAD_EXTENSIONS:
                    if lowered.endswith(extension):
                        self.fail(
                            "forbidden non-JSON payload file under benchmark-fixtures/: {0}".format(
                                os.path.join(dirpath, filename)
                            )
                        )

    def test_readme_documents_post_first_wave_status(self):
        readme_path = os.path.join(_FIXTURE_ROOT, "README.md")
        self.assertTrue(
            os.path.isfile(readme_path),
            "benchmark-fixtures/README.md does not exist",
        )
        with open(readme_path, "r", encoding="utf-8") as handle:
            content = handle.read()
        lowered = content.lower()
        # WO-20 literal phrases must still be present.
        self.assertIn(
            "no real benchmark data",
            lowered,
            "README must still contain 'no real benchmark data' language",
        )
        self.assertIn(
            "future codex packet",
            lowered,
            "README must still contain 'future Codex packet' language",
        )
        # WO-31 scoping language is required.
        self.assertIn(
            "scaffold-internal",
            lowered,
            "README must state the first-wave payloads are scaffold-internal",
        )
        self.assertIn(
            "synthetic",
            lowered,
            "README must mark first-wave payloads as synthetic",
        )
        # The README must name both the admitted and excluded class
        # partitions so the empty-skeleton invariant for the excluded
        # classes remains documented.
        for admitted in ADMITTED_FIRST_WAVE_CLASSES:
            self.assertIn(
                admitted,
                lowered,
                "README must name admitted first-wave class '{0}'".format(admitted),
            )
        for excluded in EXCLUDED_FIRST_WAVE_CLASSES:
            self.assertIn(
                excluded,
                lowered,
                "README must name excluded first-wave class '{0}'".format(excluded),
            )


if __name__ == "__main__":
    unittest.main()
