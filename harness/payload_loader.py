"""Scaffold-internal fixture payload loader for first-wave payloads.

Per WO-32 (DC-035): this is a scaffold-internal loader that reads and
validates the first synthetic fixture payload wave authored under
WO-31 / DC-034 at `benchmark-fixtures/<class>/wave-001.json` for the
three admitted classes (`golden-intents`, `hard-negatives`,
`boundary-violations`). The loader performs admission validation only.
It does not execute benchmarks, does not score, does not select an
architecture, and does not convert payloads into validation evidence.

Boundary recap (per WO-29 / DC-032, WO-30 / DC-033, WO-31 / DC-034):

- The loader admits scaffold-internal synthetic payloads only. Real
  benchmark data, production data, user data, production logs, recent
  intent traces, internet-derived examples, real vendor/model/index/
  vector-db/ANN/re-scorer/backend names, and selection language are all
  rejected.
- The loader enforces the WO-30 / DC-033 file-level and entry-level
  conceptual shape (marker + fixture_class + fixture_version + non-empty
  entries; per-entry fixture_id, synthetic marker, plane-separation
  markers using only the five WO-21 plane names without collapse).
- The loader records a `fixture_payload_loaded` event into the EventLog
  on success. Every rejection path records an explicit halt event before
  raising.
- The loader does not write files, does not mutate payloads, does not
  execute retrieval, does not invoke the mock adapter, does not call
  the dry-run, does not collect metrics, does not infer benchmark
  readiness, and does not infer architecture selection.

This module performs no retrieval, no indexing, no ranking, no real
retrieval call, no network call, no third-party import, and no
architecture selection. It is Python standard library only.
"""

import json
import re

from harness.review_package import FORBIDDEN_PHRASES


PAYLOAD_MARKER_KEY = "_fixture_payload_marker"

REQUIRED_TOP_LEVEL_FIELDS = (
    "fixture_class",
    "fixture_version",
    "entries",
)

REQUIRED_MARKER_SUBSTRINGS = (
    "harness-internal",
    "synthetic",
    "not benchmark evidence",
)

WO_21_PLANE_NAMES = frozenset((
    "official_route_results",
    "candidate_route_results",
    "normalized_material_support_results",
    "source_quality_constraint_observations",
    "trace_outcome_signal_observations",
))

# Word-boundary denylist of obvious vendor / model / index / vector-db /
# ANN / re-scorer / backend names. The list MUST match the list in
# `harness/tests/test_fixture_payloads.py`; drift between the two
# copies is a known risk recorded under WO-32 (a future Codex packet
# may move this constant into a shared module).
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

# Substring tripwire phrases that would constitute a positive claim of
# validation evidence, route trust, benchmark result, production
# readiness, or architecture selection in a payload string. The list
# MUST match `FORBIDDEN_CLAIM_PHRASES` in
# `harness/tests/test_fixture_payloads.py`; drift between the two
# copies is a known risk recorded under WO-32.
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

# Keys whose values name "expected / allowed / correct" planes for the
# loader's plane-overlap detection. The loader collects plane names from
# these keys and from `EXPECTED_PLANE_LIST_KEYS` and unions them as the
# entry's "positive" plane set.
EXPECTED_PLANE_SCALAR_KEYS = (
    "expected_plane",
    "correct_plane_for_this_content",
)
EXPECTED_PLANE_LIST_KEYS = (
    "allowed_planes",
)

# Keys whose values name "forbidden" planes for the loader's
# plane-overlap detection. The loader collects plane names from these
# keys and from `FORBIDDEN_PLANE_LIST_KEYS` and unions them as the
# entry's "negative" plane set.
FORBIDDEN_PLANE_SCALAR_KEYS = (
    "violation_plane_in_observed_output",
    "forbidden_plane_collapse",
)
FORBIDDEN_PLANE_LIST_KEYS = (
    "forbidden_planes",
)


class MalformedPayloadJSON(Exception):
    """Raised when the payload file does not parse as JSON."""


class NonObjectPayload(Exception):
    """Raised when the top-level payload JSON value is not an object (dict)."""


class MissingPayloadMarker(Exception):
    """Raised when the payload marker is missing entirely."""


class InvalidPayloadMarker(Exception):
    """Raised when the payload marker is present but does not satisfy the substring rules."""


class PayloadFixtureClassMismatch(Exception):
    """Raised when payload `fixture_class` does not match the expected value."""


class MissingPayloadFixtureVersion(Exception):
    """Raised when payload is missing `fixture_version`."""


class EmptyOrMissingPayloadEntries(Exception):
    """Raised when payload `entries` is missing, not a list, or empty."""


class MissingEntryFixtureId(Exception):
    """Raised when a payload entry is missing `fixture_id`."""


class DuplicateEntryFixtureId(Exception):
    """Raised when two or more payload entries share the same `fixture_id`."""


class MissingEntrySyntheticMarker(Exception):
    """Raised when a payload entry is missing both `synthetic_only` and `no_production_user_data` markers."""


class MissingPlaneSeparationMarkers(Exception):
    """Raised when a payload entry is missing a plane_separation_markers object."""


class ForbiddenLanguageInPayload(Exception):
    """Raised when a phrase from `FORBIDDEN_PHRASES` appears anywhere in payload strings."""


class VendorMentionInPayload(Exception):
    """Raised when a word-boundary match against `VENDOR_DENYLIST` is found in payload strings."""


class ForbiddenClaimInPayload(Exception):
    """Raised when a payload string contains a positive claim from `FORBIDDEN_CLAIM_PHRASES`."""


class UnknownPlaneNameInPayload(Exception):
    """Raised when a plane name in a plane-separation marker is not in the WO-21 plane set."""


class PlaneOverlapInPayload(Exception):
    """Raised when a plane appears as both expected/allowed/correct and forbidden in the same entry."""


def _walk_strings(value):
    """Yield every string scalar inside a nested payload value."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for key, sub in value.items():
            for inner in _walk_strings(key):
                yield inner
            for inner in _walk_strings(sub):
                yield inner
    elif isinstance(value, (list, tuple)):
        for sub in value:
            for inner in _walk_strings(sub):
                yield inner


def _entry_id_or_index(entry, index):
    """Return the entry's fixture_id when present, else its index for diagnostics."""
    if isinstance(entry, dict) and isinstance(entry.get("fixture_id"), str):
        return entry["fixture_id"]
    return "<entry-index-{0}>".format(index)


def load_fixture_payload(payload_path, expected_fixture_class, event_log):
    """Load and validate a scaffold-internal fixture payload file.

    Reads JSON from `payload_path`. Verifies, in order: top-level is a
    JSON object; `_fixture_payload_marker` is a string and contains all
    three required substrings (`harness-internal`, `synthetic`,
    `not benchmark evidence`); `fixture_class` equals
    `expected_fixture_class`; `fixture_version` is present;
    `entries` is a non-empty list; every entry has a `fixture_id`
    string; fixture_ids are unique within the file; every entry carries
    `synthetic_only is True` or `no_production_user_data is True`; no
    string scalar anywhere in the payload contains any phrase from
    `harness.review_package.FORBIDDEN_PHRASES`; no string scalar
    contains a word-boundary match against `VENDOR_DENYLIST`; no string
    scalar contains a phrase from `FORBIDDEN_CLAIM_PHRASES`; every
    plane name in any plane-separation marker is one of the five WO-21
    plane names; no plane appears in both the expected/allowed/correct
    set and the forbidden set of the same entry.

    On success, records exactly one `fixture_payload_loaded` event into
    `event_log` and returns the parsed payload object.

    Every rejection path records an explicit halt event into
    `event_log` before raising. The loader writes no file and does not
    mutate the payload object.
    """
    # Step 1: parse JSON.
    try:
        with open(payload_path, "r", encoding="utf-8") as text_file:
            payload = json.load(text_file)
    except ValueError as parse_error:
        event_log.halt(
            "payload_malformed_json",
            path=payload_path,
            parse_error=str(parse_error),
        )
        raise MalformedPayloadJSON(
            "Payload at {0} is not valid JSON: {1}".format(
                payload_path, parse_error
            )
        )

    # Step 2: top-level must be an object.
    if not isinstance(payload, dict):
        event_log.halt(
            "payload_non_object",
            path=payload_path,
            top_level_type=type(payload).__name__,
        )
        raise NonObjectPayload(
            "Payload at {0} must be a JSON object; got {1}".format(
                payload_path, type(payload).__name__
            )
        )

    # Step 3: marker present.
    if PAYLOAD_MARKER_KEY not in payload:
        event_log.halt(
            "payload_missing_marker",
            path=payload_path,
            expected_marker_key=PAYLOAD_MARKER_KEY,
        )
        raise MissingPayloadMarker(
            "Payload at {0} is missing the marker key '{1}'".format(
                payload_path, PAYLOAD_MARKER_KEY
            )
        )

    # Step 4: marker is a string containing all three required substrings.
    marker = payload[PAYLOAD_MARKER_KEY]
    if not isinstance(marker, str):
        event_log.halt(
            "payload_invalid_marker",
            path=payload_path,
            marker_type=type(marker).__name__,
        )
        raise InvalidPayloadMarker(
            "Payload at {0} marker must be a string; got {1}".format(
                payload_path, type(marker).__name__
            )
        )
    lowered_marker = marker.lower()
    for required in REQUIRED_MARKER_SUBSTRINGS:
        if required not in lowered_marker:
            event_log.halt(
                "payload_invalid_marker",
                path=payload_path,
                missing_required_substring=required,
            )
            raise InvalidPayloadMarker(
                "Payload at {0} marker missing required substring '{1}'".format(
                    payload_path, required
                )
            )

    # Step 5: fixture_class matches expected.
    if "fixture_class" not in payload:
        event_log.halt(
            "payload_fixture_class_mismatch",
            path=payload_path,
            expected_fixture_class=expected_fixture_class,
            actual_fixture_class=None,
        )
        raise PayloadFixtureClassMismatch(
            "Payload at {0} is missing 'fixture_class'; expected {1!r}".format(
                payload_path, expected_fixture_class
            )
        )
    if payload["fixture_class"] != expected_fixture_class:
        event_log.halt(
            "payload_fixture_class_mismatch",
            path=payload_path,
            expected_fixture_class=expected_fixture_class,
            actual_fixture_class=payload["fixture_class"],
        )
        raise PayloadFixtureClassMismatch(
            "Payload at {0} fixture_class is {1!r}; expected {2!r}".format(
                payload_path, payload["fixture_class"], expected_fixture_class
            )
        )

    # Step 6: fixture_version present.
    if "fixture_version" not in payload:
        event_log.halt(
            "payload_missing_fixture_version",
            path=payload_path,
        )
        raise MissingPayloadFixtureVersion(
            "Payload at {0} is missing 'fixture_version'".format(payload_path)
        )

    # Step 7: entries is a non-empty list.
    entries = payload.get("entries")
    if not isinstance(entries, list) or len(entries) == 0:
        event_log.halt(
            "payload_empty_or_missing_entries",
            path=payload_path,
            entries_type=type(entries).__name__ if entries is not None else "NoneType",
            entries_length=len(entries) if isinstance(entries, list) else None,
        )
        raise EmptyOrMissingPayloadEntries(
            "Payload at {0} must carry a non-empty 'entries' list".format(payload_path)
        )

    # Step 8: every entry has fixture_id; ids are unique.
    seen_ids = {}
    for index, entry in enumerate(entries):
        if (
            not isinstance(entry, dict)
            or not isinstance(entry.get("fixture_id"), str)
            or not entry.get("fixture_id").strip()
        ):
            event_log.halt(
                "payload_missing_entry_fixture_id",
                path=payload_path,
                entry_index=index,
            )
            raise MissingEntryFixtureId(
                "Payload at {0} entry index {1} is missing a string 'fixture_id'".format(
                    payload_path, index
                )
            )
        fixture_id = entry["fixture_id"]
        if fixture_id in seen_ids:
            event_log.halt(
                "payload_duplicate_entry_fixture_id",
                path=payload_path,
                duplicate_fixture_id=fixture_id,
                first_index=seen_ids[fixture_id],
                duplicate_index=index,
            )
            raise DuplicateEntryFixtureId(
                "Payload at {0} duplicate fixture_id {1!r} at indices {2} and {3}".format(
                    payload_path, fixture_id, seen_ids[fixture_id], index
                )
            )
        seen_ids[fixture_id] = index

    # Step 9: every entry has synthetic / no-production marker.
    for index, entry in enumerate(entries):
        synthetic_only = entry.get("synthetic_only") is True
        no_prod_user = entry.get("no_production_user_data") is True
        if not (synthetic_only or no_prod_user):
            event_log.halt(
                "payload_missing_entry_synthetic_marker",
                path=payload_path,
                entry_fixture_id=_entry_id_or_index(entry, index),
            )
            raise MissingEntrySyntheticMarker(
                "Payload at {0} entry {1!r} missing synthetic_only=True or no_production_user_data=True".format(
                    payload_path, _entry_id_or_index(entry, index)
                )
            )

    # Step 10: every entry has an explicit plane-separation marker object.
    for index, entry in enumerate(entries):
        markers = entry.get("plane_separation_markers")
        if not isinstance(markers, dict):
            event_log.halt(
                "payload_missing_plane_separation_markers",
                path=payload_path,
                entry_fixture_id=_entry_id_or_index(entry, index),
                marker_type=type(markers).__name__ if markers is not None else "NoneType",
            )
            raise MissingPlaneSeparationMarkers(
                "Payload at {0} entry {1!r} must carry a plane_separation_markers object".format(
                    payload_path, _entry_id_or_index(entry, index)
                )
            )

    # Step 11: FORBIDDEN_PHRASES absent (substring scan).
    for text in _walk_strings(payload):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    "payload_forbidden_language",
                    path=payload_path,
                    forbidden_phrase=phrase,
                )
                raise ForbiddenLanguageInPayload(
                    "Payload at {0}: forbidden phrase {1!r} found".format(
                        payload_path, phrase
                    )
                )

    # Step 12: VENDOR_DENYLIST absent (word-boundary regex).
    for text in _walk_strings(payload):
        lowered = text.lower()
        for name in VENDOR_DENYLIST:
            pattern = r"\b" + re.escape(name) + r"\b"
            if re.search(pattern, lowered) is not None:
                event_log.halt(
                    "payload_vendor_mention",
                    path=payload_path,
                    vendor_name=name,
                )
                raise VendorMentionInPayload(
                    "Payload at {0}: denylisted vendor/model term {1!r} found".format(
                        payload_path, name
                    )
                )

    # Step 13: FORBIDDEN_CLAIM_PHRASES absent (substring scan).
    for text in _walk_strings(payload):
        lowered = text.lower()
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    "payload_forbidden_claim",
                    path=payload_path,
                    forbidden_claim_phrase=phrase,
                )
                raise ForbiddenClaimInPayload(
                    "Payload at {0}: forbidden claim phrase {1!r} found".format(
                        payload_path, phrase
                    )
                )

    # Step 14 + 15: plane separation markers - all plane names must be in
    # the WO-21 plane set; no plane may appear in both the
    # expected/allowed/correct set and the forbidden set of the same entry.
    for index, entry in enumerate(entries):
        markers = entry.get("plane_separation_markers")
        expected_planes = set()
        forbidden_planes = set()
        for key in EXPECTED_PLANE_SCALAR_KEYS:
            value = markers.get(key)
            if isinstance(value, str):
                expected_planes.add(value)
        for key in EXPECTED_PLANE_LIST_KEYS:
            value = markers.get(key)
            if isinstance(value, list):
                for plane in value:
                    if isinstance(plane, str):
                        expected_planes.add(plane)
        for key in FORBIDDEN_PLANE_SCALAR_KEYS:
            value = markers.get(key)
            if isinstance(value, str):
                forbidden_planes.add(value)
        for key in FORBIDDEN_PLANE_LIST_KEYS:
            value = markers.get(key)
            if isinstance(value, list):
                for plane in value:
                    if isinstance(plane, str):
                        forbidden_planes.add(plane)
        all_planes = expected_planes | forbidden_planes
        for plane in all_planes:
            if plane not in WO_21_PLANE_NAMES:
                event_log.halt(
                    "payload_unknown_plane_name",
                    path=payload_path,
                    entry_fixture_id=_entry_id_or_index(entry, index),
                    unknown_plane=plane,
                )
                raise UnknownPlaneNameInPayload(
                    "Payload at {0} entry {1!r}: plane name {2!r} is not in the WO-21 plane set".format(
                        payload_path, _entry_id_or_index(entry, index), plane
                    )
                )
        overlap = expected_planes & forbidden_planes
        if overlap:
            event_log.halt(
                "payload_plane_overlap",
                path=payload_path,
                entry_fixture_id=_entry_id_or_index(entry, index),
                overlapping_planes=sorted(overlap),
            )
            raise PlaneOverlapInPayload(
                "Payload at {0} entry {1!r}: plane(s) {2!r} appear in both expected and forbidden roles".format(
                    payload_path, _entry_id_or_index(entry, index), sorted(overlap)
                )
            )

    # Step 16: success - record event and return.
    event_log.append(
        "fixture_payload_loaded",
        path=payload_path,
        fixture_class=payload["fixture_class"],
        fixture_version=payload["fixture_version"],
        entry_count=len(entries),
        entry_fixture_ids=list(seen_ids.keys()),
    )
    return payload
