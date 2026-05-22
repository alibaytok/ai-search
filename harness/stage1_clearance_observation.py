"""Scaffold-internal Stage 1 clearance observation.

Per WO-46 (DC-046): this module accepts an already-loaded WO-45 Stage 1
contract-safety result dict and emits a fresh fixed-shape Stage 1
clearance observation dict ONLY when Stage 1 passed with all
authorization booleans intact.

The module is the smallest useful bridge artifact between WO-45 Stage 1
contract-safety and a future Stage 2 packet. It is pre-measurement
only. It does not invoke a real adapter, does not run a real
benchmark, does not collect quality / performance metrics, does not
score, does not rank, and does not select any architecture / vendor /
library / index family / ANN backend / neural re-scorer / retrieval
family / ablation cell / multi-stage variant / production system.
OQ-035, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, and OQ-076 all remain
OPEN. RK-039 continues to apply unchanged. Real-benchmark-ready
remains NO.

Per the WO-46 packet preamble, this module does NOT call any
WO-43 / WO-44 or WO-45 module. It imports only the canonical
forbidden-language lists from `harness.review_package` and
`harness.payload_loader`. This keeps the clearance observation
structurally separate from the upstream Stage 1 module so that a
tamper of the WO-45 module cannot silently leak through.

Public surface:

    record_stage1_clearance_observation(stage1_result, event_log)
        -> dict

The function:

- Accepts an already-loaded dict only. Does not read files. Does not
  write files. Does not invoke any real adapter. Does not record any
  measurement event.
- Validates the eight documented constraints on the Stage 1 result
  dict in order (see Section 3 of the boundary doc).
- On success records a `stage1_clearance_observation_recorded` event
  and returns a fresh dict with exactly the ten allowed top-level
  keys (`ALLOWED_OBSERVATION_KEYS`).
- On any rejection records an explicit halt event before raising the
  matching named exception.

The result and every event field are free of
`harness.review_package.FORBIDDEN_PHRASES`, the local
`"score"` / `"scoring"` extension, and
`harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`. The local-mirror
forbidden-language extension matches the pattern applied in
`harness/stage1_contract_safety.py` after Codex review-time
hardening; consolidation into `harness/review_package.py` remains
deferred to a future Codex packet.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


# Local mirror of the WO-35 review-time forbidden-language extension,
# applied at module scope so the clearance observation's result
# surface and event fields are scanned against the extended set. No
# new copy of FORBIDDEN_PHRASES is created; the tuple is extended at
# import time. Future Codex consolidation may resolve the local-mirror
# drift surface.
STAGE1_CLEARANCE_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_OBSERVATION_KEYS = (
    "observation_kind",
    "stage1_cleared",
    "candidate_adapter_id",
    "configuration_id",
    "fixture_set_id",
    "checks_passed_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "observation_note",
)

# Identifier fields that pass through from the Stage 1 result onto
# the clearance observation. Their string values are scanned for
# forbidden language before the observation is assembled so a
# tampered upstream record cannot leak forbidden surface through
# the clearance dict.
SURFACED_STRING_FIELDS = (
    "candidate_adapter_id",
    "configuration_id",
    "fixture_set_id",
)


class NonObjectStage1Result(Exception):
    """Raised when the Stage 1 result argument is not a dict."""


class InvalidStage1ResultKind(Exception):
    """Raised when `result_kind` is not the literal `stage1_contract_safety_result`."""


class Stage1NotPassed(Exception):
    """Raised when `stage1_passed is not True` or `contract_safety_status != "passed"`."""


class Stage1FailedChecksPresent(Exception):
    """Raised when `checks_failed_count != 0` or `failed_check_names` is non-empty."""


class Stage1AuthorizesMeasurement(Exception):
    """Raised when the Stage 1 result carries `measurement_authorized` other than False."""


class Stage1AuthorizesRealBenchmark(Exception):
    """Raised when the Stage 1 result carries `real_benchmark_authorized` other than False."""


class Stage1DeclaresSelection(Exception):
    """Raised when the Stage 1 result carries `selection_made` other than False."""


class ForbiddenLanguageInStage1Result(Exception):
    """Raised when a phrase from the extended forbidden-language sets appears in a surfaced field."""


def _first_forbidden_phrase(text):
    """Return the first forbidden phrase found in `text`, or None.

    The scan covers `STAGE1_CLEARANCE_FORBIDDEN_PHRASES` (which extends
    `FORBIDDEN_PHRASES` with the local `"score"` / `"scoring"` mirror)
    and `FORBIDDEN_CLAIM_PHRASES`. The first match wins; the caller
    raises with the offending phrase identified in the exception
    message.
    """
    if not isinstance(text, str):
        return None
    lowered = text.lower()
    for phrase in STAGE1_CLEARANCE_FORBIDDEN_PHRASES:
        if phrase in lowered:
            return phrase
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def _assert_no_forbidden_language_in_surface(stage1_result, event_log):
    """Scan the identifier fields and the failed-check-names list.

    These are the fields that pass through onto the clearance
    observation's result surface. A tampered upstream record could
    inject forbidden language into an identifier or a check name; the
    scan catches the leak before the observation dict is assembled.
    """
    for field in SURFACED_STRING_FIELDS:
        value = stage1_result.get(field)
        if isinstance(value, str):
            offending = _first_forbidden_phrase(value)
            if offending is not None:
                event_log.halt(
                    "stage1_clearance_forbidden_language",
                    surface_field=field,
                    forbidden_phrase=offending,
                )
                raise ForbiddenLanguageInStage1Result(
                    "Forbidden phrase {0!r} found in Stage 1 result "
                    "field {1!r}: {2!r}".format(offending, field, value)
                )
    failed_names = stage1_result.get("failed_check_names")
    if isinstance(failed_names, list):
        for index, name in enumerate(failed_names):
            if isinstance(name, str):
                offending = _first_forbidden_phrase(name)
                if offending is not None:
                    event_log.halt(
                        "stage1_clearance_forbidden_language",
                        surface_field="failed_check_names",
                        index=index,
                        forbidden_phrase=offending,
                    )
                    raise ForbiddenLanguageInStage1Result(
                        "Forbidden phrase {0!r} found in failed_check_names"
                        "[{1}]: {2!r}".format(offending, index, name)
                    )


def record_stage1_clearance_observation(stage1_result, event_log):
    """Validate and record a scaffold-internal Stage 1 clearance observation.

    Validation order (each rejection records an explicit halt event
    into `event_log` before raising the matching named exception):

      1. Top-level value is a dict.
      2. `result_kind == "stage1_contract_safety_result"`.
      3. `stage1_passed is True` and `contract_safety_status == "passed"`.
      4. `checks_failed_count == 0` and `failed_check_names == []`.
      5. `measurement_authorized is False`.
      6. `real_benchmark_authorized is False`.
      7. `selection_made is False`.
      8. No forbidden phrase appears in any surfaced string field.

    On success records a `stage1_clearance_observation_recorded`
    event and returns a fresh dict with exactly the ten allowed
    top-level keys in `ALLOWED_OBSERVATION_KEYS`. The returned dict
    carries `stage1_cleared: True`, `selection_made: False`,
    `measurement_authorized: False`, and
    `real_benchmark_authorized: False`. The observation is
    pre-measurement; it does not authorize measurement or real
    benchmark execution.

    The input dict is not modified.
    """
    # 1. Top-level value must be a dict.
    if not isinstance(stage1_result, dict):
        event_log.halt(
            "stage1_clearance_non_object",
            top_level_type=type(stage1_result).__name__,
        )
        raise NonObjectStage1Result(
            "stage1_result must be a dict; got {0!r}".format(
                type(stage1_result).__name__
            )
        )

    # 2. result_kind must match the literal Stage 1 result kind.
    if stage1_result.get("result_kind") != "stage1_contract_safety_result":
        event_log.halt(
            "stage1_clearance_invalid_result_kind",
            result_kind=stage1_result.get("result_kind"),
        )
        raise InvalidStage1ResultKind(
            "Stage 1 result_kind must be 'stage1_contract_safety_result'; "
            "got {0!r}".format(stage1_result.get("result_kind"))
        )

    # 3. Stage 1 must have passed. Both stage1_passed and
    # contract_safety_status must agree; either disagreement triggers
    # rejection. (The WO-45 module guarantees the two agree on
    # well-formed outputs; rejecting either-or independently keeps
    # the clearance module robust against upstream tamper.)
    if stage1_result.get("stage1_passed") is not True:
        event_log.halt(
            "stage1_clearance_not_passed",
            reason_detail="stage1_passed_not_true",
            stage1_passed=stage1_result.get("stage1_passed"),
        )
        raise Stage1NotPassed(
            "Stage 1 result stage1_passed must be True; got {0!r}".format(
                stage1_result.get("stage1_passed")
            )
        )
    if stage1_result.get("contract_safety_status") != "passed":
        event_log.halt(
            "stage1_clearance_not_passed",
            reason_detail="contract_safety_status_not_passed",
            contract_safety_status=stage1_result.get(
                "contract_safety_status"
            ),
        )
        raise Stage1NotPassed(
            "Stage 1 result contract_safety_status must be 'passed'; got "
            "{0!r}".format(stage1_result.get("contract_safety_status"))
        )

    # 4. No failed checks may be present.
    checks_failed_count = stage1_result.get("checks_failed_count")
    if checks_failed_count != 0:
        event_log.halt(
            "stage1_clearance_failed_checks_present",
            reason_detail="checks_failed_count_nonzero",
            checks_failed_count=checks_failed_count,
        )
        raise Stage1FailedChecksPresent(
            "Stage 1 result checks_failed_count must be 0; got "
            "{0!r}".format(checks_failed_count)
        )
    failed_check_names = stage1_result.get("failed_check_names")
    if failed_check_names != []:
        event_log.halt(
            "stage1_clearance_failed_checks_present",
            reason_detail="failed_check_names_nonempty",
            failed_check_names=failed_check_names,
        )
        raise Stage1FailedChecksPresent(
            "Stage 1 result failed_check_names must be []; got "
            "{0!r}".format(failed_check_names)
        )

    # 5. measurement_authorized must be False.
    if stage1_result.get("measurement_authorized") is not False:
        event_log.halt(
            "stage1_clearance_authorizes_measurement",
            measurement_authorized=stage1_result.get(
                "measurement_authorized"
            ),
        )
        raise Stage1AuthorizesMeasurement(
            "Stage 1 result measurement_authorized must be False; got "
            "{0!r}".format(stage1_result.get("measurement_authorized"))
        )

    # 6. real_benchmark_authorized must be False.
    if stage1_result.get("real_benchmark_authorized") is not False:
        event_log.halt(
            "stage1_clearance_authorizes_real_benchmark",
            real_benchmark_authorized=stage1_result.get(
                "real_benchmark_authorized"
            ),
        )
        raise Stage1AuthorizesRealBenchmark(
            "Stage 1 result real_benchmark_authorized must be False; got "
            "{0!r}".format(stage1_result.get("real_benchmark_authorized"))
        )

    # 7. selection_made must be False.
    if stage1_result.get("selection_made") is not False:
        event_log.halt(
            "stage1_clearance_declares_selection",
            selection_made=stage1_result.get("selection_made"),
        )
        raise Stage1DeclaresSelection(
            "Stage 1 result selection_made must be False; got {0!r}".format(
                stage1_result.get("selection_made")
            )
        )

    # 8. Forbidden-language scan on surfaced fields. The scan covers
    # the three identifier fields that pass through onto the
    # observation and the failed_check_names list (defensive: even
    # though we already required it to be empty, scan in case any
    # exotic value slipped through).
    _assert_no_forbidden_language_in_surface(stage1_result, event_log)

    candidate_adapter_id = stage1_result.get("candidate_adapter_id")
    configuration_id = stage1_result.get("configuration_id")
    fixture_set_id = stage1_result.get("fixture_set_id")
    checks_passed_count = stage1_result.get("checks_passed_count")

    observation = {
        "observation_kind": "stage1_clearance_observation",
        "stage1_cleared": True,
        "candidate_adapter_id": candidate_adapter_id,
        "configuration_id": configuration_id,
        "fixture_set_id": fixture_set_id,
        "checks_passed_count": checks_passed_count,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "observation_note": (
            "Scaffold-internal Stage 1 clearance observation per "
            "ai-search/46-stage1-clearance-observation.md. Pre-measurement "
            "bridge between WO-45 Stage 1 contract-safety and a future "
            "Stage 2 packet. Does not authorize measurement; does not "
            "authorize benchmark execution; the Indexing Excellence Gate "
            "continues to govern selection."
        ),
    }

    event_log.append(
        "stage1_clearance_observation_recorded",
        candidate_adapter_id=candidate_adapter_id,
        configuration_id=configuration_id,
        fixture_set_id=fixture_set_id,
        checks_passed_count=checks_passed_count,
    )

    return observation
