"""Scaffold-internal run artifact snapshot writer for toy dry-run packages.

Per WO-27 (DC-030): this is a scaffold-only artifact snapshot for toy
dry-run review packages. It is not a production artifact contract, not a
run artifact retention / storage policy decision (OQ-056 remains open),
not a production artifact schema (OQ-076 remains open), not benchmark
execution, and not architecture selection.

The writer is intentionally minimal:

- Input is an already-assembled dry-run review package (a Python dict).
- Output is a deterministic UTF-8 JSON file at the caller-provided
  `output_path`. Determinism is preserved by `sort_keys=True` and a fixed
  encoding; for the same input package the snapshot file is
  byte-for-byte identical.
- No directory policy is invented: the writer uses the caller-provided
  `output_path` verbatim. It does not create parent directories, choose
  filenames, derive paths from the package contents, or enforce any
  prefix.
- Forbidden selection / recommendation language anywhere in the package
  (as defined by `harness.review_package.FORBIDDEN_PHRASES`) is rejected
  before any file write occurs.
- A non-dict package is rejected before any file write occurs.
- An optional `event_log` records explicit success and halt events.

The writer does not perform retrieval, indexing, ranking, network calls,
or any architecture decision. It is Python standard library only.
"""

import hashlib
import json

from harness.review_package import FORBIDDEN_PHRASES


class NonObjectSnapshotPackage(Exception):
    """Raised when the package passed to write_scaffold_snapshot is not a dict."""


class ForbiddenLanguageInSnapshotPackage(Exception):
    """Raised when forbidden selection/recommendation language appears in the package."""


class SnapshotWriteError(Exception):
    """Raised when serializing or writing the snapshot to output_path fails."""


def _walk_strings(value):
    """Yield every string scalar inside a nested package value."""
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


def _assert_no_forbidden_language(package, output_path, event_log):
    """Raise ForbiddenLanguageInSnapshotPackage if any forbidden phrase appears."""
    for text in _walk_strings(package):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                if event_log is not None:
                    event_log.halt(
                        "snapshot_forbidden_language",
                        output_path=output_path,
                        forbidden_phrase=phrase,
                    )
                raise ForbiddenLanguageInSnapshotPackage(
                    "Forbidden phrase '{0}' found in package for snapshot "
                    "at {1}".format(phrase, output_path)
                )


def write_scaffold_snapshot(package, output_path, event_log=None):
    """Write a deterministic scaffold-internal JSON snapshot of `package`.

    Writes UTF-8 JSON with sorted keys to `output_path`. Returns a minimal
    metadata dict carrying `output_path`, the SHA-256 hex digest of the
    written file's bytes, and the byte length. When `event_log` is
    provided, records a `snapshot_written` event on success and an
    explicit halt event before any rejection.

    Rejection order:
      1. Non-dict package -> NonObjectSnapshotPackage (halt event
         `snapshot_non_object_package`).
      2. Forbidden language anywhere in package strings ->
         ForbiddenLanguageInSnapshotPackage (halt event
         `snapshot_forbidden_language`).
      3. Serialization or write failure -> SnapshotWriteError (halt
         event `snapshot_write_error`).

    The writer does not create parent directories, choose filenames,
    derive paths from package contents, or enforce any directory policy.
    The caller is responsible for the `output_path`.
    """
    if not isinstance(package, dict):
        if event_log is not None:
            event_log.halt(
                "snapshot_non_object_package",
                output_path=output_path,
                package_type=type(package).__name__,
            )
        raise NonObjectSnapshotPackage(
            "Snapshot package must be a dict; got {0}".format(
                type(package).__name__
            )
        )

    _assert_no_forbidden_language(package, output_path, event_log)

    try:
        serialized = json.dumps(package, sort_keys=True, ensure_ascii=True)
    except (TypeError, ValueError) as serialization_error:
        if event_log is not None:
            event_log.halt(
                "snapshot_write_error",
                output_path=output_path,
                error=str(serialization_error),
            )
        raise SnapshotWriteError(
            "Failed to serialize package for snapshot at {0}: {1}".format(
                output_path, serialization_error
            )
        )

    encoded = serialized.encode("utf-8")

    try:
        with open(output_path, "wb") as handle:
            handle.write(encoded)
    except OSError as write_error:
        if event_log is not None:
            event_log.halt(
                "snapshot_write_error",
                output_path=output_path,
                error=str(write_error),
            )
        raise SnapshotWriteError(
            "Failed to write snapshot at {0}: {1}".format(
                output_path, write_error
            )
        )

    sha256 = hashlib.sha256(encoded).hexdigest()

    if event_log is not None:
        event_log.append(
            "snapshot_written",
            output_path=output_path,
            sha256=sha256,
            byte_length=len(encoded),
        )

    return {
        "output_path": output_path,
        "sha256": sha256,
        "byte_length": len(encoded),
    }
