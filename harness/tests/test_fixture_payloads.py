"""Tests for first-wave synthetic fixture payloads.

Per WO-31 / DC-034: the three admitted first-wave classes
(`golden-intents`, `hard-negatives`, `boundary-violations`) carry small
synthetic JSON payload files at `benchmark-fixtures/<class>/*.json`. The
other three classes (`latency-profiles`, `update-profiles`, `adversarial`)
remain empty. These tests verify payload-level invariants that the
skeleton test does not cover (the skeleton test scopes only the
directory shape; this file scopes payload content).

Coverage:
- Only the three admitted classes contain JSON payload files.
- Excluded classes contain exactly `.gitkeep`.
- Every admitted JSON payload parses as JSON.
- Every payload has the scaffold-internal marker containing the three
  required substrings (`harness-internal`, `synthetic`, `not benchmark
  evidence`).
- Every payload declares its `fixture_class` consistently with its
  directory.
- Every payload has a non-empty `entries` list.
- Every entry has a synthetic-only marker.
- No `harness.review_package.FORBIDDEN_PHRASES` substring appears
  anywhere in payload strings (file-level or entry-level, walked
  recursively).
- No obvious vendor / model / index / vector-db / ANN / reranker /
  backend term appears anywhere in payload strings (word-boundary
  match against an explicit denylist).
- No payload claims validation evidence, route trust, benchmark result,
  production readiness, or architecture selection.
- Plane-separation markers stay explicit and use the WO-21 plane names
  without collapsing official / candidate / normalized-material /
  source-quality / trace-outcome roles.
- Hard-negative entries do not authorize official route return.
- Boundary-violation entries describe forbidden outcomes as expected
  rejection conditions, not as valid outputs.
- Golden-intent entries do not imply production validation evidence.

The tests do not invoke any harness retrieval, indexing, or ranking
implementation, and do not perform benchmark execution. They read
payload files only and write nothing.
"""

import json
import os
import re
import unittest

from harness.review_package import FORBIDDEN_PHRASES


_PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
_FIXTURE_ROOT = os.path.join(_PROJECT_ROOT, "benchmark-fixtures")

ADMITTED_FIRST_WAVE_CLASSES = (
    "golden-intents",
    "hard-negatives",
    "boundary-violations",
)

EXCLUDED_FIRST_WAVE_CLASSES = (
    "latency-profiles",
    "update-profiles",
    "adversarial",
)

WO_21_PLANES = (
    "official_route_results",
    "candidate_route_results",
    "normalized_material_support_results",
    "source_quality_constraint_observations",
    "trace_outcome_signal_observations",
)

REQUIRED_MARKER_SUBSTRINGS = (
    "harness-internal",
    "synthetic",
    "not benchmark evidence",
)

# Word-boundary denylist of obvious vendor / model / index / vector-db /
# ANN / reranker / backend names. The list is a tripwire, not a proof of
# absence: it covers the most common public names whose accidental
# inclusion in a synthetic scaffold-internal payload would constitute an
# implicit architecture lean. Word-boundary regex avoids substring false
# positives (e.g. "ada" inside "adapter_kind").
VENDOR_DENYLIST = (
    "faiss",
    "hnsw",
    "scann",
    "annoy",
    "milvus",
    "qdrant",
    "weaviate",
    "pinecone",
    "chroma",
    "vespa",
    "elasticsearch",
    "opensearch",
    "lucene",
    "tantivy",
    "whoosh",
    "solr",
    "redisearch",
    "bm25",
    "colbert",
    "sbert",
    "openai",
    "cohere",
    "anthropic",
    "bge",
    "ada",
    "voyage",
    "nomic",
    "gemini",
    "mistral",
    "llama",
    "gpt",
    "claude",
)

# Phrases that would constitute a claim of validation evidence, route
# trust, benchmark result, production readiness, or architecture
# selection if they appeared in a synthetic scaffold-internal payload.
# These are word-boundary tripwires.
FORBIDDEN_CLAIM_PHRASES = (
    "validation evidence",
    "validated route",
    "route trust",
    "benchmark result",
    "benchmark output",
    "architecture selection",
    "architecture choice",
    "selected architecture",
    "production-grade",
)


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


def _admitted_payload_paths():
    paths = []
    for category in ADMITTED_FIRST_WAVE_CLASSES:
        cat_dir = os.path.join(_FIXTURE_ROOT, category)
        for entry in sorted(os.listdir(cat_dir)):
            if entry == ".gitkeep":
                continue
            full = os.path.join(cat_dir, entry)
            if os.path.isfile(full) and entry.lower().endswith(".json"):
                paths.append((category, full))
    return paths


class FirstWavePayloadStructureTest(unittest.TestCase):
    def test_only_admitted_classes_contain_json_payloads(self):
        for category in ADMITTED_FIRST_WAVE_CLASSES:
            cat_dir = os.path.join(_FIXTURE_ROOT, category)
            json_files = [
                e for e in os.listdir(cat_dir)
                if e.lower().endswith(".json")
            ]
            self.assertGreaterEqual(
                len(json_files),
                1,
                "admitted class {0} must contain at least one JSON payload".format(category),
            )

    def test_excluded_classes_contain_only_gitkeep(self):
        for category in EXCLUDED_FIRST_WAVE_CLASSES:
            cat_dir = os.path.join(_FIXTURE_ROOT, category)
            entries = sorted(os.listdir(cat_dir))
            self.assertEqual(
                entries,
                [".gitkeep"],
                "excluded class {0} must contain only .gitkeep; got: {1}".format(
                    category, entries
                ),
            )

    def test_every_admitted_payload_parses_as_json(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                self.assertIsInstance(
                    obj, dict, "payload top-level must be JSON object: {0}".format(path)
                )


class FirstWavePayloadMarkerTest(unittest.TestCase):
    def test_payload_marker_contains_all_required_substrings(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                marker = obj.get("_fixture_payload_marker")
                self.assertIsInstance(
                    marker,
                    str,
                    "_fixture_payload_marker must be a string in {0}".format(path),
                )
                lowered = marker.lower()
                for required in REQUIRED_MARKER_SUBSTRINGS:
                    self.assertIn(
                        required,
                        lowered,
                        "_fixture_payload_marker missing required substring '{0}' in {1}".format(
                            required, path
                        ),
                    )

    def test_fixture_class_matches_directory(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                self.assertEqual(
                    obj.get("fixture_class"),
                    category,
                    "fixture_class in {0} must equal directory name {1!r}; got {2!r}".format(
                        path, category, obj.get("fixture_class")
                    ),
                )

    def test_entries_collection_is_present_and_non_empty(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                entries = obj.get("entries")
                self.assertIsInstance(
                    entries, list, "entries must be a list in {0}".format(path)
                )
                self.assertGreater(
                    len(entries), 0, "entries must be non-empty in {0}".format(path)
                )

    def test_every_entry_has_synthetic_only_marker(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for entry in obj["entries"]:
                    self.assertTrue(
                        entry.get("synthetic_only") is True
                        or entry.get("no_production_user_data") is True,
                        "entry {0!r} in {1} must declare synthetic_only or no_production_user_data".format(
                            entry.get("fixture_id"), path
                        ),
                    )


class FirstWavePayloadForbiddenLanguageTest(unittest.TestCase):
    def test_no_forbidden_selection_phrase_in_payload_strings(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for text in _walk_strings(obj):
                    lowered = text.lower()
                    for phrase in FORBIDDEN_PHRASES:
                        self.assertNotIn(
                            phrase,
                            lowered,
                            "forbidden phrase {0!r} in {1}: {2!r}".format(
                                phrase, path, text
                            ),
                        )

    def test_no_obvious_vendor_or_model_term_in_payload_strings(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for text in _walk_strings(obj):
                    lowered = text.lower()
                    for name in VENDOR_DENYLIST:
                        pattern = r"\b" + re.escape(name) + r"\b"
                        match = re.search(pattern, lowered)
                        self.assertIsNone(
                            match,
                            "denylisted vendor/model term {0!r} in {1}: {2!r}".format(
                                name, path, text
                            ),
                        )

    def test_no_validation_or_selection_claim_in_payload_strings(self):
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for text in _walk_strings(obj):
                    lowered = text.lower()
                    for phrase in FORBIDDEN_CLAIM_PHRASES:
                        self.assertNotIn(
                            phrase,
                            lowered,
                            "forbidden claim phrase {0!r} in {1}: {2!r}".format(
                                phrase, path, text
                            ),
                        )


class FirstWavePayloadPlaneSeparationTest(unittest.TestCase):
    def test_plane_separation_markers_use_wo21_plane_names(self):
        # Every entry that carries plane_separation_markers must reference
        # only the five WO-21 plane names. Cross-plane collapse is
        # forbidden: no entry may name the same plane in both
        # `expected_plane`/`allowed_planes`/`correct_plane_for_this_content`
        # and `forbidden_planes`.
        for category, path in _admitted_payload_paths():
            with self.subTest(category=category, path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for entry in obj["entries"]:
                    markers = entry.get("plane_separation_markers")
                    if markers is None:
                        continue
                    expected_planes = set()
                    if isinstance(markers.get("expected_plane"), str):
                        expected_planes.add(markers["expected_plane"])
                    if isinstance(markers.get("allowed_planes"), list):
                        expected_planes.update(markers["allowed_planes"])
                    if isinstance(markers.get("correct_plane_for_this_content"), str):
                        expected_planes.add(markers["correct_plane_for_this_content"])
                    forbidden_planes = set()
                    if isinstance(markers.get("forbidden_planes"), list):
                        forbidden_planes.update(markers["forbidden_planes"])
                    # Every named plane must be a WO-21 plane name.
                    for plane in expected_planes | forbidden_planes:
                        self.assertIn(
                            plane,
                            WO_21_PLANES,
                            "plane {0!r} in {1} is not a WO-21 plane name".format(
                                plane, path
                            ),
                        )
                    # No plane may appear in both expected and forbidden.
                    overlap = expected_planes & forbidden_planes
                    self.assertEqual(
                        overlap,
                        set(),
                        "plane(s) {0!r} appear in both expected and forbidden in {1}".format(
                            overlap, path
                        ),
                    )


class HardNegativeEntryTest(unittest.TestCase):
    def test_hard_negative_entries_forbid_official_route_return(self):
        cat_dir = os.path.join(_FIXTURE_ROOT, "hard-negatives")
        paths = [
            os.path.join(cat_dir, e) for e in sorted(os.listdir(cat_dir))
            if e.lower().endswith(".json")
        ]
        self.assertGreaterEqual(
            len(paths),
            1,
            "hard-negatives must contain at least one JSON payload",
        )
        for path in paths:
            with self.subTest(path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for entry in obj["entries"]:
                    self.assertTrue(
                        entry.get("must_not_authorize_official_return") is True,
                        "hard-negative entry {0!r} must carry must_not_authorize_official_return=True".format(
                            entry.get("fixture_id")
                        ),
                    )
                    markers = entry.get("plane_separation_markers", {})
                    forbidden = markers.get("forbidden_planes", [])
                    self.assertIn(
                        "official_route_results",
                        forbidden,
                        "hard-negative entry {0!r} must list official_route_results as forbidden".format(
                            entry.get("fixture_id")
                        ),
                    )


class BoundaryViolationEntryTest(unittest.TestCase):
    def test_boundary_violation_entries_describe_forbidden_outcomes(self):
        cat_dir = os.path.join(_FIXTURE_ROOT, "boundary-violations")
        paths = [
            os.path.join(cat_dir, e) for e in sorted(os.listdir(cat_dir))
            if e.lower().endswith(".json")
        ]
        self.assertGreaterEqual(
            len(paths),
            1,
            "boundary-violations must contain at least one JSON payload",
        )
        for path in paths:
            with self.subTest(path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for entry in obj["entries"]:
                    disq = entry.get("expected_disqualification")
                    self.assertIsInstance(
                        disq,
                        dict,
                        "boundary-violation entry {0!r} must carry expected_disqualification dict".format(
                            entry.get("fixture_id")
                        ),
                    )
                    self.assertTrue(
                        disq.get("expected_halt") is True,
                        "boundary-violation entry {0!r}: expected_halt must be True".format(
                            entry.get("fixture_id")
                        ),
                    )
                    self.assertEqual(
                        disq.get("halt_classification"),
                        "contract_check_failed",
                        "boundary-violation entry {0!r}: halt_classification must be contract_check_failed".format(
                            entry.get("fixture_id")
                        ),
                    )
                    self.assertTrue(
                        disq.get("is_valid_output") is False,
                        "boundary-violation entry {0!r}: is_valid_output must be False".format(
                            entry.get("fixture_id")
                        ),
                    )
                    self.assertTrue(
                        disq.get("is_forbidden_output") is True,
                        "boundary-violation entry {0!r}: is_forbidden_output must be True".format(
                            entry.get("fixture_id")
                        ),
                    )
                    self.assertIsInstance(
                        entry.get("target_contract_assertion"),
                        str,
                        "boundary-violation entry {0!r} must name a target_contract_assertion".format(
                            entry.get("fixture_id")
                        ),
                    )


class GoldenIntentEntryTest(unittest.TestCase):
    def test_golden_intent_entries_do_not_imply_production_validation_evidence(self):
        cat_dir = os.path.join(_FIXTURE_ROOT, "golden-intents")
        paths = [
            os.path.join(cat_dir, e) for e in sorted(os.listdir(cat_dir))
            if e.lower().endswith(".json")
        ]
        self.assertGreaterEqual(
            len(paths),
            1,
            "golden-intents must contain at least one JSON payload",
        )
        for path in paths:
            with self.subTest(path=path):
                with open(path, "r", encoding="utf-8") as handle:
                    obj = json.load(handle)
                for entry in obj["entries"]:
                    ref = entry.get("expected_official_route_reference")
                    if ref is not None:
                        # When an entry names a synthetic route reference,
                        # it must explicitly disclaim validation evidence
                        # and promotion-trigger status.
                        self.assertIs(
                            ref.get("is_validation_evidence"),
                            False,
                            "golden-intent entry {0!r}: expected_official_route_reference must disclaim validation evidence".format(
                                entry.get("fixture_id")
                            ),
                        )
                        self.assertIs(
                            ref.get("is_promotion_trigger"),
                            False,
                            "golden-intent entry {0!r}: expected_official_route_reference must disclaim promotion-trigger".format(
                                entry.get("fixture_id")
                            ),
                        )


if __name__ == "__main__":
    unittest.main()
