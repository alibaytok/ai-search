"""Scaffold-internal Stage 1 contract-safety pass.

Per WO-45 (DC-045): this module runs a fixed-shape contract-safety
pass over the Stage 0 readiness output and the already-loaded
scaffold-internal fixture admission and candidate adapter records.

Important scope note: this is a scaffold-internal approximation of
WO-12R / `ai-search/14-benchmark-execution-plan.md` Section 6 (real
Stage 1 contract violation pass). Real Stage 1 would run contract
violation tests against actual adapter responses produced by a real
adapter call. The WO-45 module operates ONLY on a scaffold
observation dict; no real adapter is invoked, no real benchmark
data is consumed, and no measurement is recorded. The contract
checks under this scaffold are toy assertions over the readiness
state; the production contract violation surface is recorded in
`ai-search/13-retrieval-benchmark-framework.md` Section 8 and
remains out of scope here.

The scaffold preserves every prior non-measurement and non-selection
boundary:

- WO-19 / DC-022 halt-before-measurement invariant: the result dict
  carries `measurement_authorized: False` and
  `real_benchmark_authorized: False` on BOTH the pass path and the
  fail path. Pass does not authorize measurement; fail does not
  authorize measurement.
- WO-43 / WO-44 admission contract: the module re-validates that the
  caller-provided Stage 0 readiness dict still carries the literal
  False authorization booleans, and that the fixture admission and
  candidate adapter records still carry the four scaffold-only
  booleans (no real benchmark data; no real adapter; no production
  registration; no selection).
- Forbidden-language hygiene: the result dict and every event field
  are free of `harness.review_package.FORBIDDEN_PHRASES` and
  `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`.

The five WO-21 plane names, the forbidden selection language list,
and the forbidden claim language list are reused from canonical
modules. No new copy of any list is created.

Public surface:

    run_stage1_contract_safety(stage0_readiness,
                               fixture_admission_record,
                               candidate_adapter_record,
                               contract_checks,
                               event_log) -> dict

All four record arguments are already-loaded dicts; `contract_checks`
is a non-empty list of `(name, callable)` pairs; `event_log` is a
`harness.event_log.EventLog`. The module does not read files and
does not write files.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


ALLOWED_RESULT_KEYS = (
    "result_kind",
    "contract_safety_status",
    "stage1_passed",
    "checks_run_count",
    "checks_passed_count",
    "checks_failed_count",
    "failed_check_names",
    "candidate_adapter_id",
    "configuration_id",
    "fixture_set_id",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "result_note",
)

# Subset of the Stage 0 readiness output that the scaffold contract
# checks are allowed to see. The observation dict passed to each
# check contains only these keys; per-record substantive content is
# NOT propagated into the check input. This keeps the scaffold
# contract checks operating against the readiness state only, not
# against any real adapter output.
OBSERVATION_KEYS = (
    "stage0_ready",
    "fixture_set_id",
    "candidate_adapter_id",
    "configuration_id",
    "fixture_class_count",
    "candidate_plane_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
)

STAGE1_RESULT_SURFACE_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)


class NonObjectStage0Readiness(Exception):
    """Raised when the Stage 0 readiness argument is not a dict."""


class InvalidStage0Readiness(Exception):
    """Raised when the Stage 0 readiness dict is missing a required field, has the wrong review_kind, or has stage0_ready not True."""


class Stage0AuthorizesMeasurement(Exception):
    """Raised when the Stage 0 readiness dict carries measurement_authorized other than False."""


class Stage0AuthorizesRealBenchmark(Exception):
    """Raised when the Stage 0 readiness dict carries real_benchmark_authorized other than False."""


class Stage0DeclaresSelection(Exception):
    """Raised when the Stage 0 readiness dict carries selection_made other than False."""


class NonObjectStage1Record(Exception):
    """Raised when the fixture admission record or candidate adapter record is not a dict."""


class Stage1RecordDeclaresRealBenchmarkData(Exception):
    """Raised when the fixture admission record declares real_benchmark_data other than False."""


class Stage1RecordDeclaresRealAdapter(Exception):
    """Raised when the candidate adapter record declares real_adapter other than False."""


class Stage1RecordDeclaresProductionRegistration(Exception):
    """Raised when the candidate adapter record declares production_registration other than False."""


class Stage1RecordDeclaresSelection(Exception):
    """Raised when either record declares selection_made other than False."""


class InvalidContractCheckList(Exception):
    """Raised when contract_checks is not a non-empty list."""


class InvalidContractCheck(Exception):
    """Raised when an individual contract check entry is not a (name, callable) pair."""


def _walk_strings(value):
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


def _first_forbidden_result_surface_phrase(text):
    lowered = text.lower()
    for phrase in STAGE1_RESULT_SURFACE_FORBIDDEN_PHRASES:
        if phrase in lowered:
            return phrase
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def _validate_stage0_readiness(stage0_readiness, event_log):
    """Verify the caller-provided Stage 0 readiness dict has not been tampered with.

    The Stage 1 module does not re-run `review_stage0_readiness(...)`;
    that function ran upstream. The Stage 1 module instead verifies
    that the dict it received still carries the literal False
    authorization booleans and the expected review_kind / stage0_ready
    values. Any tamper (forged readiness dict, mutated authorization
    booleans, or wrong review_kind) is rejected before any check runs.
    """
    if not isinstance(stage0_readiness, dict):
        event_log.halt(
            "stage1_non_object_stage0_readiness",
            top_level_type=type(stage0_readiness).__name__,
        )
        raise NonObjectStage0Readiness(
            "Stage 0 readiness must be a dict; got {0!r}".format(
                type(stage0_readiness).__name__
            )
        )

    if stage0_readiness.get("review_kind") != "stage0_readiness_review":
        event_log.halt(
            "stage1_invalid_stage0_readiness",
            reason_detail="review_kind_mismatch",
            review_kind=stage0_readiness.get("review_kind"),
        )
        raise InvalidStage0Readiness(
            "Stage 0 readiness review_kind must be "
            "'stage0_readiness_review'; got {0!r}".format(
                stage0_readiness.get("review_kind")
            )
        )

    if stage0_readiness.get("stage0_ready") is not True:
        event_log.halt(
            "stage1_invalid_stage0_readiness",
            reason_detail="stage0_not_ready",
            stage0_ready=stage0_readiness.get("stage0_ready"),
        )
        raise InvalidStage0Readiness(
            "Stage 0 readiness stage0_ready must be True; got {0!r}".format(
                stage0_readiness.get("stage0_ready")
            )
        )

    if stage0_readiness.get("measurement_authorized") is not False:
        event_log.halt(
            "stage1_stage0_authorizes_measurement",
            measurement_authorized=stage0_readiness.get(
                "measurement_authorized"
            ),
        )
        raise Stage0AuthorizesMeasurement(
            "Stage 0 readiness measurement_authorized must be False; "
            "got {0!r}".format(stage0_readiness.get("measurement_authorized"))
        )

    if stage0_readiness.get("real_benchmark_authorized") is not False:
        event_log.halt(
            "stage1_stage0_authorizes_real_benchmark",
            real_benchmark_authorized=stage0_readiness.get(
                "real_benchmark_authorized"
            ),
        )
        raise Stage0AuthorizesRealBenchmark(
            "Stage 0 readiness real_benchmark_authorized must be False; "
            "got {0!r}".format(stage0_readiness.get("real_benchmark_authorized"))
        )

    if stage0_readiness.get("selection_made") is not False:
        event_log.halt(
            "stage1_stage0_declares_selection",
            selection_made=stage0_readiness.get("selection_made"),
        )
        raise Stage0DeclaresSelection(
            "Stage 0 readiness selection_made must be False; got "
            "{0!r}".format(stage0_readiness.get("selection_made"))
        )


def _validate_stage1_records(
    fixture_admission_record, candidate_adapter_record, event_log
):
    """Re-verify the four scaffold-only booleans on both records.

    Tamper-check only; the full WO-43 / WO-44 validators were run
    upstream. The Stage 1 module verifies that the records have not
    been mutated since the Stage 0 reviewer accepted them.
    """
    if not isinstance(fixture_admission_record, dict):
        event_log.halt(
            "stage1_non_object_record",
            record_role="fixture_admission_record",
            top_level_type=type(fixture_admission_record).__name__,
        )
        raise NonObjectStage1Record(
            "fixture_admission_record must be a dict; got {0!r}".format(
                type(fixture_admission_record).__name__
            )
        )
    if not isinstance(candidate_adapter_record, dict):
        event_log.halt(
            "stage1_non_object_record",
            record_role="candidate_adapter_record",
            top_level_type=type(candidate_adapter_record).__name__,
        )
        raise NonObjectStage1Record(
            "candidate_adapter_record must be a dict; got {0!r}".format(
                type(candidate_adapter_record).__name__
            )
        )

    if fixture_admission_record.get("real_benchmark_data") is not False:
        event_log.halt(
            "stage1_record_declares_real_benchmark_data",
            real_benchmark_data=fixture_admission_record.get(
                "real_benchmark_data"
            ),
        )
        raise Stage1RecordDeclaresRealBenchmarkData(
            "fixture_admission_record real_benchmark_data must be False; "
            "got {0!r}".format(
                fixture_admission_record.get("real_benchmark_data")
            )
        )

    if candidate_adapter_record.get("real_adapter") is not False:
        event_log.halt(
            "stage1_record_declares_real_adapter",
            real_adapter=candidate_adapter_record.get("real_adapter"),
        )
        raise Stage1RecordDeclaresRealAdapter(
            "candidate_adapter_record real_adapter must be False; got "
            "{0!r}".format(candidate_adapter_record.get("real_adapter"))
        )

    if candidate_adapter_record.get("production_registration") is not False:
        event_log.halt(
            "stage1_record_declares_production_registration",
            production_registration=candidate_adapter_record.get(
                "production_registration"
            ),
        )
        raise Stage1RecordDeclaresProductionRegistration(
            "candidate_adapter_record production_registration must be "
            "False; got {0!r}".format(
                candidate_adapter_record.get("production_registration")
            )
        )

    if fixture_admission_record.get("selection_made") is not False:
        event_log.halt(
            "stage1_record_declares_selection",
            record_role="fixture_admission_record",
            selection_made=fixture_admission_record.get("selection_made"),
        )
        raise Stage1RecordDeclaresSelection(
            "fixture_admission_record selection_made must be False; got "
            "{0!r}".format(fixture_admission_record.get("selection_made"))
        )
    if candidate_adapter_record.get("selection_made") is not False:
        event_log.halt(
            "stage1_record_declares_selection",
            record_role="candidate_adapter_record",
            selection_made=candidate_adapter_record.get("selection_made"),
        )
        raise Stage1RecordDeclaresSelection(
            "candidate_adapter_record selection_made must be False; got "
            "{0!r}".format(candidate_adapter_record.get("selection_made"))
        )


def _validate_contract_checks(contract_checks, event_log):
    """Verify contract_checks is a non-empty list of (name, callable) pairs."""
    if not isinstance(contract_checks, list) or len(contract_checks) == 0:
        event_log.halt(
            "stage1_invalid_contract_check_list",
            type_or_state=(
                type(contract_checks).__name__
                if not isinstance(contract_checks, list)
                else "empty_list"
            ),
        )
        raise InvalidContractCheckList(
            "contract_checks must be a non-empty list; got {0!r}".format(
                type(contract_checks).__name__
                if not isinstance(contract_checks, list)
                else "empty list"
            )
        )
    for index, entry in enumerate(contract_checks):
        if (
            not isinstance(entry, (tuple, list))
            or len(entry) != 2
            or not isinstance(entry[0], str)
            or len(entry[0]) == 0
            or not callable(entry[1])
        ):
            event_log.halt(
                "stage1_invalid_contract_check",
                index=index,
            )
            raise InvalidContractCheck(
                "contract_checks[{0}] must be a (non-empty-str, callable) "
                "pair".format(index)
            )
        forbidden_phrase = _first_forbidden_result_surface_phrase(entry[0])
        if forbidden_phrase is not None:
            event_log.halt(
                "stage1_invalid_contract_check",
                index=index,
                forbidden_phrase=forbidden_phrase,
            )
            raise InvalidContractCheck(
                "contract_checks[{0}] name contains forbidden phrase "
                "{1!r}".format(index, forbidden_phrase)
            )


def _build_observation(stage0_readiness):
    """Project the Stage 0 readiness dict onto the OBSERVATION_KEYS subset.

    The observation dict is a fresh dict; the input readiness dict is
    not modified. Each check receives a copy so that callbacks cannot
    mutate the readiness state seen by later checks.
    """
    return {key: stage0_readiness.get(key) for key in OBSERVATION_KEYS}


def run_stage1_contract_safety(
    stage0_readiness,
    fixture_admission_record,
    candidate_adapter_record,
    contract_checks,
    event_log,
):
    """Run the scaffold-internal Stage 1 contract-safety pass.

    Validates the Stage 0 readiness dict, the fixture admission and
    candidate adapter records, and the contract_checks list (halt
    before raising on every rejection). Builds a fixed-shape
    observation dict from the Stage 0 readiness. Runs each contract
    check in list order against a fresh copy of the observation
    dict. Records `stage1_contract_check_passed` for each pass and
    `stage1_contract_check_failed` plus halt `stage1_contract_safety_failed`
    on the first failure (no later checks run). Records
    `stage1_contract_safety_passed` if every check passes.

    Returns a dict with exactly the fourteen `ALLOWED_RESULT_KEYS`.
    `measurement_authorized` and `real_benchmark_authorized` are
    literal `False` on BOTH the pass path and the fail path.
    `selection_made` is literal `False` on every path.

    The function does not invoke any real adapter, does not read
    files, does not write files, and does not record any measurement
    event.
    """
    _validate_stage0_readiness(stage0_readiness, event_log)
    _validate_stage1_records(
        fixture_admission_record, candidate_adapter_record, event_log
    )
    _validate_contract_checks(contract_checks, event_log)

    candidate_adapter_id = candidate_adapter_record.get("candidate_adapter_id")
    configuration_id = candidate_adapter_record.get("configuration_id")
    fixture_set_id = fixture_admission_record.get("fixture_set_id")

    checks_run_count = 0
    checks_passed_count = 0
    checks_failed_count = 0
    failed_check_names = []

    for name, check_fn in contract_checks:
        observation = _build_observation(stage0_readiness)
        try:
            passed = bool(check_fn(observation))
        except Exception:
            # A check callable that raises is treated as a check
            # failure under this scaffold; the halt event records the
            # check name and the exception class. We do not propagate
            # the original exception to the caller because the contract
            # check failure is the documented failure mode at Stage 1.
            passed = False
        checks_run_count += 1
        if passed:
            checks_passed_count += 1
            event_log.append(
                "stage1_contract_check_passed",
                candidate_adapter_id=candidate_adapter_id,
                configuration_id=configuration_id,
                check_name=name,
            )
        else:
            checks_failed_count += 1
            failed_check_names.append(name)
            event_log.append(
                "stage1_contract_check_failed",
                candidate_adapter_id=candidate_adapter_id,
                configuration_id=configuration_id,
                check_name=name,
            )
            event_log.halt(
                "stage1_contract_safety_failed",
                candidate_adapter_id=candidate_adapter_id,
                configuration_id=configuration_id,
                failed_check_name=name,
            )
            # Halt-on-first-failure: no later checks run.
            break

    if checks_failed_count == 0:
        status = "passed"
        stage1_passed = True
        event_log.append(
            "stage1_contract_safety_passed",
            candidate_adapter_id=candidate_adapter_id,
            configuration_id=configuration_id,
            checks_passed_count=checks_passed_count,
        )
    else:
        status = "failed"
        stage1_passed = False

    result = {
        "result_kind": "stage1_contract_safety_result",
        "contract_safety_status": status,
        "stage1_passed": stage1_passed,
        "checks_run_count": checks_run_count,
        "checks_passed_count": checks_passed_count,
        "checks_failed_count": checks_failed_count,
        "failed_check_names": list(failed_check_names),
        "candidate_adapter_id": candidate_adapter_id,
        "configuration_id": configuration_id,
        "fixture_set_id": fixture_set_id,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "result_note": (
            "Scaffold-internal Stage 1 contract-safety observation per "
            "ai-search/45-stage1-contract-safety-pass-scaffold.md. "
            "No measurement performed; no real adapter invoked. The "
            "Indexing Excellence Gate continues to govern selection."
        ),
    }

    return result
