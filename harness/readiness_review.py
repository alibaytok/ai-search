"""Scaffold-internal Stage 0 readiness review.

Per WO-43 / WO-44 (DC-044): this module performs a scaffold-level
Stage 0 readiness review against an already-loaded fixture admission
record and an already-loaded candidate adapter record. It is a
pre-measurement boundary; it does not author a real adapter, does not
authorize real benchmark execution, does not collect metrics, does not
score, does not rank, and does not select any architecture.

The review approximates the WO-12R Section 5 Stage 0 readiness review
at toy-record level. It does NOT verify every WO-12R Section 4 field
(retrieval family, rerank mode, dependency version pins, operational
profile); the scaffold consumes only the minimum scaffold-level
record shape documented in
`ai-search/43-44-stage0-readiness-and-adapter-admission.md`.

The reviewer accepts already-loaded dicts only. It does not read
files and does not write files. It records `stage0_readiness_reviewed`
on success and explicit halt events before raising on every rejection
of the fixture admission record. It delegates candidate-adapter
record validation to
`harness.candidate_adapter_contract.validate_candidate_adapter_record(...)`,
which performs its own halt-and-raise rejection ordering.

The reviewer's returned dict carries fixed observation-only keys
(see Section 5 of the WO-43 / WO-44 boundary document) plus the
explicit non-authorization booleans `measurement_authorized: False`
and `real_benchmark_authorized: False` to make the absence of
measurement / benchmark authorization observable in the returned
result.

The five WO-21 plane names, the forbidden selection language list,
and the forbidden claim language list are reused from the canonical
modules; no new copy is created. The WO-32 drift-risk policy holds.
"""

from harness.candidate_adapter_contract import (
    validate_candidate_adapter_record,
)
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY = "_fixture_admission_marker"

REQUIRED_FIXTURE_ADMISSION_MARKER_SUBSTRINGS = (
    "harness-internal",
    "fixture-admission",
)

REQUIRED_FIXTURE_ADMISSION_FIELDS = (
    "fixture_set_id",
    "fixture_classes",
    "content_hashes",
    "synthetic_only",
    "real_benchmark_data",
    "admission_authority_decided",
    "selection_made",
)

ALLOWED_READINESS_KEYS = (
    "review_kind",
    "stage0_ready",
    "fixture_set_id",
    "candidate_adapter_id",
    "configuration_id",
    "fixture_class_count",
    "candidate_plane_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "readiness_note",
)


class NonObjectFixtureAdmissionRecord(Exception):
    """Raised when the fixture admission record is not a dict."""


class MissingFixtureAdmissionMarker(Exception):
    """Raised when the fixture admission record is missing the scaffold marker."""


class InvalidFixtureAdmissionMarker(Exception):
    """Raised when the fixture admission marker is not a string containing both required substrings."""


class MissingFixtureAdmissionField(Exception):
    """Raised when a required scaffold-level field is missing from the fixture admission record."""


class FixtureAdmissionDeclaresRealBenchmarkData(Exception):
    """Raised when the record declares `real_benchmark_data` other than False (forbidden under this scaffold)."""


class FixtureAdmissionDeclaresAuthorityDecision(Exception):
    """Raised when the record declares `admission_authority_decided` other than False (OQ-057 OPEN)."""


class FixtureAdmissionDeclaresSelection(Exception):
    """Raised when the record declares `selection_made` other than False."""


class ForbiddenLanguageInFixtureAdmissionRecord(Exception):
    """Raised when a phrase from `FORBIDDEN_PHRASES` appears anywhere in fixture admission record strings."""


class ForbiddenClaimInFixtureAdmissionRecord(Exception):
    """Raised when a phrase from `FORBIDDEN_CLAIM_PHRASES` appears anywhere in fixture admission record strings."""


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


def _assert_no_forbidden_fixture_language(record, event_log):
    """Raise on the first forbidden phrase found anywhere in fixture admission record strings."""
    for text in _walk_strings(record):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    "fixture_admission_forbidden_language",
                    forbidden_phrase=phrase,
                )
                raise ForbiddenLanguageInFixtureAdmissionRecord(
                    "Forbidden phrase {0!r} found in fixture admission "
                    "record string: {1!r}".format(phrase, text)
                )
    for text in _walk_strings(record):
        lowered = text.lower()
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    "fixture_admission_forbidden_claim",
                    forbidden_phrase=phrase,
                )
                raise ForbiddenClaimInFixtureAdmissionRecord(
                    "Forbidden claim phrase {0!r} found in fixture "
                    "admission record string: {1!r}".format(phrase, text)
                )


def _validate_fixture_admission_record(record, event_log):
    """Validate the scaffold-level fixture admission record shape.

    Validation order:
      1. Top-level value is a dict.
      2. Scaffold marker key is present.
      3. Marker is a non-empty string containing every substring in
         `REQUIRED_FIXTURE_ADMISSION_MARKER_SUBSTRINGS`.
      4. Every field in `REQUIRED_FIXTURE_ADMISSION_FIELDS` is present.
      5. `synthetic_only is True`.
      6. `real_benchmark_data is False`.
      7. `admission_authority_decided is False`.
      8. `selection_made is False`.
      9. No phrase from `FORBIDDEN_PHRASES` appears in any record string.
      10. No phrase from `FORBIDDEN_CLAIM_PHRASES` appears in any record
          string.

    Records explicit halt events before raising on every rejection.
    """
    if not isinstance(record, dict):
        event_log.halt(
            "fixture_admission_non_object",
            top_level_type=type(record).__name__,
        )
        raise NonObjectFixtureAdmissionRecord(
            "Fixture admission record must be a dict; got {0!r}".format(
                type(record).__name__
            )
        )

    if FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY not in record:
        event_log.halt(
            "fixture_admission_missing_marker",
            expected_marker_key=FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY,
        )
        raise MissingFixtureAdmissionMarker(
            "Fixture admission record is missing scaffold marker key "
            "{0!r}".format(FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY)
        )

    marker = record[FIXTURE_ADMISSION_SCAFFOLD_MARKER_KEY]
    if not isinstance(marker, str) or len(marker) == 0:
        event_log.halt(
            "fixture_admission_invalid_marker",
            marker_type=type(marker).__name__,
        )
        raise InvalidFixtureAdmissionMarker(
            "Fixture admission marker must be a non-empty string; got "
            "{0!r}".format(type(marker).__name__)
        )
    lowered_marker = marker.lower()
    for required_substring in REQUIRED_FIXTURE_ADMISSION_MARKER_SUBSTRINGS:
        if required_substring not in lowered_marker:
            event_log.halt(
                "fixture_admission_invalid_marker",
                missing_marker_substring=required_substring,
            )
            raise InvalidFixtureAdmissionMarker(
                "Fixture admission marker {0!r} must contain substring "
                "{1!r}".format(marker, required_substring)
            )

    for field in REQUIRED_FIXTURE_ADMISSION_FIELDS:
        if field not in record:
            event_log.halt(
                "fixture_admission_missing_field",
                missing_field=field,
            )
            raise MissingFixtureAdmissionField(
                "Fixture admission record is missing required field "
                "{0!r}".format(field)
            )

    # 5. synthetic_only must be True. This is the scaffold-level
    # equivalent of "no real benchmark data in this admission record".
    if record["synthetic_only"] is not True:
        event_log.halt(
            "fixture_admission_not_synthetic_only",
            synthetic_only=record["synthetic_only"],
        )
        raise FixtureAdmissionDeclaresRealBenchmarkData(
            "Fixture admission record declares synthetic_only={0!r}; must "
            "be True under this scaffold".format(record["synthetic_only"])
        )

    # 6. real_benchmark_data must be False.
    if record["real_benchmark_data"] is not False:
        event_log.halt(
            "fixture_admission_declares_real_benchmark_data",
            real_benchmark_data=record["real_benchmark_data"],
        )
        raise FixtureAdmissionDeclaresRealBenchmarkData(
            "Fixture admission record declares real_benchmark_data="
            "{0!r}; must be False under this scaffold".format(
                record["real_benchmark_data"]
            )
        )

    # 7. admission_authority_decided must be False (OQ-057 OPEN).
    if record["admission_authority_decided"] is not False:
        event_log.halt(
            "fixture_admission_declares_authority_decision",
            admission_authority_decided=record["admission_authority_decided"],
        )
        raise FixtureAdmissionDeclaresAuthorityDecision(
            "Fixture admission record declares admission_authority_decided="
            "{0!r}; must be False (OQ-057 OPEN)".format(
                record["admission_authority_decided"]
            )
        )

    # 8. selection_made must be False.
    if record["selection_made"] is not False:
        event_log.halt(
            "fixture_admission_declares_selection",
            selection_made=record["selection_made"],
        )
        raise FixtureAdmissionDeclaresSelection(
            "Fixture admission record declares selection_made={0!r}; must "
            "be False".format(record["selection_made"])
        )

    # 9 + 10. Forbidden-language scans.
    _assert_no_forbidden_fixture_language(record, event_log)


def review_stage0_readiness(
    fixture_admission_record,
    candidate_adapter_record,
    event_log,
):
    """Perform a scaffold-internal Stage 0 readiness review.

    Accepts already-loaded dicts only. Does not read or write files.

    Order of operations:
      1. Validate the fixture admission record shape (halt + raise on
         the first rejection).
      2. Validate the candidate adapter record by delegating to
         `harness.candidate_adapter_contract.validate_candidate_adapter_record(...)`.
         That function performs its own halt-and-raise rejection ordering.
      3. On success, record a `stage0_readiness_reviewed` event and
         return a fresh dict with exactly the keys in
         `ALLOWED_READINESS_KEYS`.

    Any validation failure halts before any readiness dict is
    returned. The returned readiness dict's `measurement_authorized`
    and `real_benchmark_authorized` are both fixed to False; this
    scaffold does not authorize either, and Stage 0 readiness alone
    does not promote the system to either authorization state.
    """
    # Step 1: validate the fixture admission record. Halts before raising
    # on every rejection path.
    _validate_fixture_admission_record(fixture_admission_record, event_log)

    # Step 2: validate the candidate adapter record. Delegates to the
    # candidate adapter contract validator; that function halts before
    # raising on every rejection path. If a candidate adapter rejection
    # occurs, this function propagates the exception and no readiness
    # dict is returned.
    validate_candidate_adapter_record(candidate_adapter_record, event_log)

    # Step 3: assemble the readiness dict. Counts are derived from the
    # validated records; no measurement is computed.
    fixture_classes = fixture_admission_record["fixture_classes"]
    fixture_class_count = (
        len(fixture_classes) if isinstance(fixture_classes, list) else 0
    )
    planes_declared = candidate_adapter_record["planes_declared"]
    candidate_plane_count = (
        len(planes_declared) if isinstance(planes_declared, list) else 0
    )

    readiness = {
        "review_kind": "stage0_readiness_review",
        "stage0_ready": True,
        "fixture_set_id": fixture_admission_record["fixture_set_id"],
        "candidate_adapter_id": candidate_adapter_record["candidate_adapter_id"],
        "configuration_id": candidate_adapter_record["configuration_id"],
        "fixture_class_count": fixture_class_count,
        "candidate_plane_count": candidate_plane_count,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "readiness_note": (
            "Scaffold-internal Stage 0 readiness review per "
            "ai-search/43-44-stage0-readiness-and-adapter-admission.md. "
            "Pre-measurement observation only; this record does not "
            "authorize measurement and does not authorize benchmark "
            "execution. The Indexing Excellence Gate continues to "
            "govern selection."
        ),
    }

    event_log.append(
        "stage0_readiness_reviewed",
        fixture_set_id=readiness["fixture_set_id"],
        candidate_adapter_id=readiness["candidate_adapter_id"],
        configuration_id=readiness["configuration_id"],
        fixture_class_count=readiness["fixture_class_count"],
        candidate_plane_count=readiness["candidate_plane_count"],
    )

    return readiness
