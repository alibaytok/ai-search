"""Scaffold-internal retrieval configuration manifest loader.

Per WO-24 (DC-027): this is a scaffold-internal, toy-only manifest loader
authorized so future adapter and dry-run work can consume registered
configuration manifests without authoring a production manifest schema
and without selecting any architecture. The loader does not author the
substantive contents of a production manifest (manifest authority remains
under OQ-057 and production artifact contracts remain under OQ-076); it
only enforces the scaffold-level shape and boundary required to make
manifest consumption observable.

Boundary recap (per `21-retrieval-adapter-contract.md` Section 9 and
DC-027):

- Manifests admitted by this loader are toy, harness-internal data. They
  carry an explicit scaffold marker proving harness-internal origin.
- Manifests carry a `manifest_id`, `adapter_kind`, `configuration_id`,
  `planes_declared`, and an explicit non-selection posture
  (`selection_made == False`).
- The loader rejects forbidden selection language anywhere in manifest
  string values using `harness.review_package.FORBIDDEN_PHRASES`. Manifest
  language drift cannot smuggle a selection claim into the scaffold.
- The loader records a `manifest_loaded` event into the EventLog on
  success. Every rejection path records an explicit halt event.

This module performs no retrieval, no indexing, no ranking, no real
retrieval call, no network call, no third-party import, and no
architecture selection. It is Python standard library only.
"""

import json

from harness.review_package import FORBIDDEN_PHRASES


REQUIRED_FIELDS = (
    "manifest_id",
    "adapter_kind",
    "configuration_id",
    "planes_declared",
    "selection_made",
)

SCAFFOLD_MARKER_KEY = "_manifest_marker"


class MalformedManifestJSON(Exception):
    """Raised when the manifest file does not parse as JSON."""


class NonObjectManifest(Exception):
    """Raised when the top-level manifest JSON value is not an object (dict)."""


class MissingRequiredManifestField(Exception):
    """Raised when a required scaffold-level field is missing from the manifest."""


class ManifestIdMismatch(Exception):
    """Raised when the manifest's manifest_id does not match the expected value."""


class MissingManifestScaffoldMarker(Exception):
    """Raised when the manifest is missing the scaffold-internal marker."""


class ForbiddenLanguageInManifest(Exception):
    """Raised when forbidden selection language is found in the manifest."""


class ManifestDeclaresSelection(Exception):
    """Raised when the manifest declares `selection_made` other than False."""


def _walk_strings(value):
    """Yield every string scalar inside a nested manifest value."""
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


def _assert_no_forbidden_language(manifest, event_log, path):
    """Raise ForbiddenLanguageInManifest if any forbidden phrase appears."""
    for text in _walk_strings(manifest):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    "manifest_forbidden_language",
                    path=path,
                    forbidden_phrase=phrase,
                )
                raise ForbiddenLanguageInManifest(
                    "Forbidden phrase '{0}' found in manifest at {1}".format(
                        phrase, path
                    )
                )


def load_manifest(manifest_path, expected_manifest_id, event_log):
    """Load and validate a scaffold-internal retrieval configuration manifest.

    Reads JSON from `manifest_path`; verifies the top-level value is a JSON
    object; verifies the scaffold marker is present; verifies every
    required field is present; verifies `manifest_id` matches
    `expected_manifest_id`; verifies `selection_made` is exactly `False`;
    verifies no forbidden selection language appears anywhere in manifest
    string values.

    On success, records a `manifest_loaded` event into `event_log` and
    returns the parsed manifest object.

    Every rejection path records an explicit halt event into `event_log`
    before raising.
    """
    try:
        with open(manifest_path, "r", encoding="utf-8") as text_file:
            manifest = json.load(text_file)
    except ValueError as parse_error:
        event_log.halt(
            "manifest_malformed_json",
            path=manifest_path,
            parse_error=str(parse_error),
        )
        raise MalformedManifestJSON(
            "Manifest at {0} is not valid JSON: {1}".format(
                manifest_path, parse_error
            )
        )

    if not isinstance(manifest, dict):
        event_log.halt(
            "manifest_non_object",
            path=manifest_path,
            top_level_type=type(manifest).__name__,
        )
        raise NonObjectManifest(
            "Manifest at {0} must be a JSON object; got {1}".format(
                manifest_path, type(manifest).__name__
            )
        )

    marker = manifest.get(SCAFFOLD_MARKER_KEY)
    if (
        SCAFFOLD_MARKER_KEY not in manifest
        or not isinstance(marker, str)
        or "harness-internal" not in marker.lower()
    ):
        event_log.halt(
            "manifest_missing_scaffold_marker",
            path=manifest_path,
            expected_marker_key=SCAFFOLD_MARKER_KEY,
        )
        raise MissingManifestScaffoldMarker(
            "Manifest at {0} is missing a valid scaffold marker '{1}'".format(
                manifest_path, SCAFFOLD_MARKER_KEY
            )
        )

    for field in REQUIRED_FIELDS:
        if field not in manifest:
            event_log.halt(
                "manifest_missing_required_field",
                path=manifest_path,
                missing_field=field,
            )
            raise MissingRequiredManifestField(
                "Manifest at {0} is missing required field '{1}'".format(
                    manifest_path, field
                )
            )

    if manifest["manifest_id"] != expected_manifest_id:
        event_log.halt(
            "manifest_id_mismatch",
            path=manifest_path,
            expected_manifest_id=expected_manifest_id,
            actual_manifest_id=manifest["manifest_id"],
        )
        raise ManifestIdMismatch(
            "Manifest at {0} has manifest_id {1!r}; expected {2!r}".format(
                manifest_path, manifest["manifest_id"], expected_manifest_id
            )
        )

    if manifest["selection_made"] is not False:
        event_log.halt(
            "manifest_declares_selection",
            path=manifest_path,
            selection_made=manifest["selection_made"],
        )
        raise ManifestDeclaresSelection(
            "Manifest at {0} declares selection_made={1!r}; must be False".format(
                manifest_path, manifest["selection_made"]
            )
        )

    _assert_no_forbidden_language(manifest, event_log, manifest_path)

    event_log.append(
        "manifest_loaded",
        path=manifest_path,
        manifest_id=manifest["manifest_id"],
        adapter_kind=manifest["adapter_kind"],
        configuration_id=manifest["configuration_id"],
        planes_declared=list(manifest["planes_declared"]),
    )
    return manifest
