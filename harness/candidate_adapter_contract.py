"""Scaffold-internal candidate adapter admission contract validator.

Per WO-43 / WO-44 (DC-044): this module validates the scaffold-level
shape of a candidate adapter admission record. It is a pre-measurement
boundary; it does not author a real adapter, does not authorize real
benchmark execution, does not collect metrics, does not score, does
not rank, and does not select any architecture / vendor / library /
index family / ANN backend / neural re-scorer / retrieval family /
ablation cell / multi-stage variant / production system.

The validator accepts an already-loaded dict only. It does not read
files and does not write files. It records a
`candidate_adapter_record_validated` event on success and an explicit
halt event before raising on every rejection.

The five WO-21 plane names are imported from
`harness.payload_loader.WO_21_PLANE_NAMES`; no new copy of the list is
created (the WO-32 drift-risk policy holds). The forbidden selection
language list is imported from `harness.review_package.FORBIDDEN_PHRASES`
and the forbidden claim language list from
`harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`; no new copy of either
list is created.

The record contract is documented in
`ai-search/43-44-stage0-readiness-and-adapter-admission.md` Section 3.
"""

from harness.payload_loader import (
    FORBIDDEN_CLAIM_PHRASES,
    WO_21_PLANE_NAMES,
)
from harness.review_package import FORBIDDEN_PHRASES


SCAFFOLD_MARKER_KEY = "_candidate_adapter_marker"

REQUIRED_MARKER_SUBSTRINGS = (
    "harness-internal",
    "candidate-adapter",
)

REQUIRED_FIELDS = (
    "candidate_adapter_id",
    "adapter_kind",
    "configuration_id",
    "planes_declared",
    "selection_made",
    "production_registration",
    "real_adapter",
    "dependencies_declared",
)


class NonObjectCandidateAdapterRecord(Exception):
    """Raised when the candidate adapter record is not a dict."""


class MissingCandidateAdapterMarker(Exception):
    """Raised when the candidate adapter record is missing the scaffold marker."""


class InvalidCandidateAdapterMarker(Exception):
    """Raised when the candidate adapter marker is not a string containing both required substrings."""


class MissingCandidateAdapterField(Exception):
    """Raised when a required scaffold-level field is missing from the record."""


class CandidateAdapterDeclaresSelection(Exception):
    """Raised when the record declares `selection_made` other than False."""


class CandidateAdapterDeclaresProductionRegistration(Exception):
    """Raised when the record declares `production_registration` other than False."""


class CandidateAdapterDeclaresRealAdapter(Exception):
    """Raised when the record declares `real_adapter` other than False (forbidden under this scaffold)."""


class UnknownCandidateAdapterPlane(Exception):
    """Raised when a plane name in `planes_declared` is not in the WO-21 plane set."""


class ForbiddenLanguageInCandidateAdapterRecord(Exception):
    """Raised when a phrase from `FORBIDDEN_PHRASES` appears anywhere in record strings."""


class ForbiddenClaimInCandidateAdapterRecord(Exception):
    """Raised when a phrase from `FORBIDDEN_CLAIM_PHRASES` appears anywhere in record strings."""


def _walk_strings(value):
    """Yield every string scalar inside a nested record value."""
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


def _assert_no_forbidden_language(record, event_log):
    """Raise on the first forbidden phrase found anywhere in record strings.

    Two scans are applied. The `FORBIDDEN_PHRASES` scan is applied first
    because it catches selection / recommendation / winner / best /
    production-ready / rank language. The `FORBIDDEN_CLAIM_PHRASES` scan
    is applied second because it catches positive claim phrases like
    "validation evidence", "validated route", "benchmark result", and
    "architecture selection".
    """
    for text in _walk_strings(record):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    "candidate_adapter_forbidden_language",
                    forbidden_phrase=phrase,
                )
                raise ForbiddenLanguageInCandidateAdapterRecord(
                    "Forbidden phrase {0!r} found in candidate adapter "
                    "record string: {1!r}".format(phrase, text)
                )
    for text in _walk_strings(record):
        lowered = text.lower()
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    "candidate_adapter_forbidden_claim",
                    forbidden_phrase=phrase,
                )
                raise ForbiddenClaimInCandidateAdapterRecord(
                    "Forbidden claim phrase {0!r} found in candidate "
                    "adapter record string: {1!r}".format(phrase, text)
                )


def validate_candidate_adapter_record(record, event_log):
    """Validate a scaffold-internal candidate adapter admission record.

    Accepts an already-loaded dict. Does not read or write files.
    Records `candidate_adapter_record_validated` on success and an
    explicit halt event before raising on every rejection.

    Validation order:
      1. Top-level value is a dict.
      2. Scaffold marker key is present.
      3. Marker is a non-empty string containing every substring in
         `REQUIRED_MARKER_SUBSTRINGS`.
      4. Every field in `REQUIRED_FIELDS` is present.
      5. `selection_made is False`.
      6. `production_registration is False`.
      7. `real_adapter is False`.
      8. `planes_declared` is a list and every entry is a WO-21 plane name.
      9. No phrase from `FORBIDDEN_PHRASES` appears in any record string.
      10. No phrase from `FORBIDDEN_CLAIM_PHRASES` appears in any record
          string.

    On success returns the record dict unchanged.
    """
    # 1. Top-level value must be a dict.
    if not isinstance(record, dict):
        event_log.halt(
            "candidate_adapter_non_object",
            top_level_type=type(record).__name__,
        )
        raise NonObjectCandidateAdapterRecord(
            "Candidate adapter record must be a dict; got {0!r}".format(
                type(record).__name__
            )
        )

    # 2. Scaffold marker key must be present.
    if SCAFFOLD_MARKER_KEY not in record:
        event_log.halt(
            "candidate_adapter_missing_marker",
            expected_marker_key=SCAFFOLD_MARKER_KEY,
        )
        raise MissingCandidateAdapterMarker(
            "Candidate adapter record is missing scaffold marker key "
            "{0!r}".format(SCAFFOLD_MARKER_KEY)
        )

    # 3. Marker must be a non-empty string containing every required substring.
    marker = record[SCAFFOLD_MARKER_KEY]
    if not isinstance(marker, str) or len(marker) == 0:
        event_log.halt(
            "candidate_adapter_invalid_marker",
            marker_type=type(marker).__name__,
        )
        raise InvalidCandidateAdapterMarker(
            "Candidate adapter marker must be a non-empty string; got "
            "{0!r}".format(type(marker).__name__)
        )
    lowered_marker = marker.lower()
    for required_substring in REQUIRED_MARKER_SUBSTRINGS:
        if required_substring not in lowered_marker:
            event_log.halt(
                "candidate_adapter_invalid_marker",
                missing_marker_substring=required_substring,
            )
            raise InvalidCandidateAdapterMarker(
                "Candidate adapter marker {0!r} must contain substring "
                "{1!r}".format(marker, required_substring)
            )

    # 4. Every required field must be present.
    for field in REQUIRED_FIELDS:
        if field not in record:
            event_log.halt(
                "candidate_adapter_missing_field",
                missing_field=field,
            )
            raise MissingCandidateAdapterField(
                "Candidate adapter record is missing required field "
                "{0!r}".format(field)
            )

    # 5. selection_made must be False.
    if record["selection_made"] is not False:
        event_log.halt(
            "candidate_adapter_declares_selection",
            selection_made=record["selection_made"],
        )
        raise CandidateAdapterDeclaresSelection(
            "Candidate adapter record declares selection_made={0!r}; must "
            "be False".format(record["selection_made"])
        )

    # 6. production_registration must be False.
    if record["production_registration"] is not False:
        event_log.halt(
            "candidate_adapter_declares_production_registration",
            production_registration=record["production_registration"],
        )
        raise CandidateAdapterDeclaresProductionRegistration(
            "Candidate adapter record declares production_registration="
            "{0!r}; must be False".format(record["production_registration"])
        )

    # 7. real_adapter must be False under this scaffold.
    if record["real_adapter"] is not False:
        event_log.halt(
            "candidate_adapter_declares_real_adapter",
            real_adapter=record["real_adapter"],
        )
        raise CandidateAdapterDeclaresRealAdapter(
            "Candidate adapter record declares real_adapter={0!r}; must "
            "be False under this scaffold (no real adapter authorized)".format(
                record["real_adapter"]
            )
        )

    # 8. planes_declared must be a list and every entry must be a
    # WO-21 plane name. A scalar string would otherwise be silently
    # accepted without checking the declared plane set.
    planes = record["planes_declared"]
    if not isinstance(planes, list):
        event_log.halt(
            "candidate_adapter_unknown_plane",
            plane_type=type(planes).__name__,
        )
        raise UnknownCandidateAdapterPlane(
            "Candidate adapter record planes_declared must be a list; got "
            "{0!r}".format(type(planes).__name__)
        )
    for plane in planes:
        if plane not in WO_21_PLANE_NAMES:
            event_log.halt(
                "candidate_adapter_unknown_plane",
                plane=plane,
            )
            raise UnknownCandidateAdapterPlane(
                "Candidate adapter record plane name {0!r} is not in "
                "the WO-21 plane set".format(plane)
            )

    # 9 + 10. Forbidden-language scans (selection list, then claim list).
    _assert_no_forbidden_language(record, event_log)

    # Success. Record the validation event.
    event_log.append(
        "candidate_adapter_record_validated",
        candidate_adapter_id=record["candidate_adapter_id"],
        adapter_kind=record["adapter_kind"],
        configuration_id=record["configuration_id"],
        planes_declared=list(record["planes_declared"]) if isinstance(
            record["planes_declared"], list
        ) else record["planes_declared"],
    )

    return record
