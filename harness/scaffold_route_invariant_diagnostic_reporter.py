"""Scaffold route-invariant diagnostic reporter.

WO-58 adds a scaffold-only deterministic diagnostic reporter that
inspects already-loaded in-memory observation dicts and emits review
diagnostics for ai-search contract risks.

Diagnostics are review evidence only. They do NOT validate routes,
qualify sources, admit corpus, authorize extraction, authorize
normalization, authorize candidate derivation, authorize
measurement, authorize benchmark execution, prove benchmark
readiness, select architecture, select route / workflow /
candidate, or promote anything to official.

This module performs no file IO, no network call, no hash
computation, no real or mock adapter invocation, no real benchmark
execution, no metric / quality / performance measurement, no
similarity / ranking / scoring of any kind, no model judgment, no
fuzzy semantic analysis, no thresholds, no weights, no
architecture / vendor / library / index family / production system
choice, no shell execution, and no external integration.

It uses only Python standard library plus `harness.payload_loader`
and `harness.review_package` constants. It does not invoke any
existing scaffold-layer public function; it operates on
already-loaded output dicts.

The WO-47 through WO-57 explicit non-claim constraint carries
forward: this module does not claim that any diagnostic, category,
severity, or invariant reference is sufficient, necessary, superior,
best, complete, production-ready, recommended, or selected. The
diagnostic categories enumerated here are bounded by WO-58 and are
not claimed exhaustive.

See `ai-search/58-scaffold-route-invariant-diagnostic-reporter.md`
for the full boundary document including explicit disclaimers about
IDE extensions, model integrations, and evaluation systems.

Public surface:

    run_scaffold_route_invariant_diagnostic_reporter(
        observations, event_log
    ) -> dict

The clean-pass output dict has exactly thirteen allowed keys in
`ALLOWED_OUTPUT_KEYS`. The four authorization / readiness /
selection booleans are literal False on every emitted path,
regardless of how many error diagnostics with `halt_required: True`
are emitted. The `halt_required` field on a diagnostic record is
advisory metadata about what the caller should do; it does NOT
cause the reporter itself to raise.

The reporter halts (records an explicit halt event and raises the
matching named exception) only on:

- non-list `observations`
- non-dict observation item
- observation item missing a non-empty string `observation_kind`
- forbidden language on any surfaced input or output value
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


REPORTER_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
    "reporter_kind",
    "observations_checked_count",
    "diagnostics_count",
    "error_count",
    "warning_count",
    "info_count",
    "halt_required_count",
    "diagnostics",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "reporter_note",
)


DIAGNOSTIC_CATEGORIES = (
    "route_first_violation",
    "source_quarantine_violation",
    "route_status_claim",
    "benchmark_readiness_claim",
    "architecture_selection_claim",
    "authorization_boolean_true",
    "admission_or_qualification_count_nonzero",
    "missing_literal_false_authorization_boolean",
    "missing_non_claim_note",
    "diagnostic_input_shape",
)


ALLOWED_SEVERITIES = ("info", "warning", "error")


_DIAGNOSTIC_REQUIRED_FIELDS = (
    "diagnostic_id",
    "category",
    "severity",
    "target_observation_kind",
    "target_path",
    "invariant_ref",
    "message",
    "halt_required",
)


_STANDARD_AUTHORIZATION_BOOLEAN_KEYS = (
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
)


_EXTENDED_AUTHORIZATION_BOOLEAN_KEYS = (
    "extraction_authorized",
    "normalization_authorized",
    "candidate_derivation_authorized",
)


_ALL_AUTHORIZATION_BOOLEAN_KEYS = (
    _STANDARD_AUTHORIZATION_BOOLEAN_KEYS + _EXTENDED_AUTHORIZATION_BOOLEAN_KEYS
)


_ADMISSION_QUALIFICATION_COUNT_KEYS = (
    "corpus_admitted_count",
    "qualified_count",
)


ROUTE_STATUS_FIELDS = (
    "route",
    "route_id",
    "route_state",
    "plane",
    "official",
    "executable",
    "selected_route",
    "production_route",
    "selected_as_official",
    "route_authorized",
    "official_route_authorized",
)


ARCHITECTURE_SELECTION_FIELDS = (
    "architecture",
    "vendor",
    "library",
    "index_family",
    "ann_backend",
    "reranker",
    "retrieval_family",
    "production_system",
    "architecture_selected",
    "selected_architecture",
    "architecture_choice",
)


_NON_CLAIM_NOTE_FIELDS = (
    "trace_note",
    "intake_note",
    "bridge_note",
    "package_note",
    "guard_note",
    "probe_note",
    "reporter_note",
)


_KNOWN_SCAFFOLD_OBSERVATION_KINDS = frozenset((
    "scaffold_source_intake_trace",
    "scaffold_source_intake_register",
    "scaffold_source_trace_admission_bridge",
    "scaffold_source_intake_smoke_package",
    "scaffold_conflicting_evidence_guard",
    "scaffold_route_query_probe",
    "scaffold_route_query_ambiguity_probe",
    "scaffold_index_probe",
))


_REPORTER_NOTE = (
    "scaffold_route_invariant_diagnostic_reporter: emits "
    "deterministic diagnostics over already-loaded scaffold "
    "observation dicts as review evidence only; diagnostics do NOT "
    "validate routes, qualify sources, admit corpus, authorize "
    "extraction, authorize normalization, authorize candidate "
    "derivation, authorize measurement, authorize benchmark "
    "execution, prove benchmark readiness, select architecture, "
    "select route / workflow / candidate, or promote anything to "
    "official; OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, "
    "OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN; no real "
    "adapter, no benchmark execution, and no measurement "
    "authorization."
)


class NonListDiagnosticObservations(Exception):
    """Raised when `observations` is not a list."""


class NonObjectDiagnosticObservation(Exception):
    """Raised when an entry of `observations` is not a dict."""


class MissingObservationKind(Exception):
    """Raised when an observation is missing a non-empty string
    `observation_kind`."""


class ForbiddenLanguageInRouteInvariantDiagnostics(Exception):
    """Raised when forbidden language appears on a surfaced input or
    output value."""


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


def _first_forbidden_phrase(text):
    lowered = text.lower()
    for phrase in REPORTER_OUTPUT_FORBIDDEN_PHRASES:
        if phrase in lowered:
            return phrase
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def _assert_no_forbidden_language(value, event_log):
    for text in _walk_strings(value):
        offending = _first_forbidden_phrase(text)
        if offending is not None:
            event_log.halt(
                "scaffold_route_invariant_diagnostic_reporter_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInRouteInvariantDiagnostics(
                "Forbidden phrase {0!r} found in diagnostic reporter "
                "surface".format(offending)
            )


def _new_diagnostic(
    diagnostic_id,
    category,
    severity,
    target_observation_kind,
    target_path,
    invariant_ref,
    message,
    halt_required,
):
    return {
        "diagnostic_id": diagnostic_id,
        "category": category,
        "severity": severity,
        "target_observation_kind": target_observation_kind,
        "target_path": target_path,
        "invariant_ref": invariant_ref,
        "message": message,
        "halt_required": halt_required,
    }


class _Recorder(object):
    def __init__(self):
        self.diagnostics = []
        self._next_id = 1

    def add(
        self,
        category,
        severity,
        target_observation_kind,
        target_path,
        invariant_ref,
        message,
        halt_required,
    ):
        diagnostic = _new_diagnostic(
            diagnostic_id="diag-{0:06d}".format(self._next_id),
            category=category,
            severity=severity,
            target_observation_kind=target_observation_kind,
            target_path=target_path,
            invariant_ref=invariant_ref,
            message=message,
            halt_required=halt_required,
        )
        self._next_id += 1
        self.diagnostics.append(diagnostic)
        return diagnostic


def _path_inside_diagnostics(path):
    return path == "diagnostics" or path.startswith("diagnostics/")


def _walk_with_path(value, path):
    yield path, value
    if isinstance(value, dict):
        for key, sub_value in value.items():
            sub_path = path + "/" + key if path else key
            for inner in _walk_with_path(sub_value, sub_path):
                yield inner
    elif isinstance(value, (list, tuple)):
        for index, sub_value in enumerate(value):
            sub_path = path + "/" + str(index) if path else str(index)
            for inner in _walk_with_path(sub_value, sub_path):
                yield inner


def _inspect_observation(observation, recorder, event_log):
    kind = observation["observation_kind"]
    event_log.append(
        "scaffold_route_invariant_diagnostic_observed",
        observation_kind=kind,
    )

    if kind in _KNOWN_SCAFFOLD_OBSERVATION_KINDS:
        for boolean_key in _STANDARD_AUTHORIZATION_BOOLEAN_KEYS:
            if boolean_key not in observation:
                recorder.add(
                    category="missing_literal_false_authorization_boolean",
                    severity="info",
                    target_observation_kind=kind,
                    target_path=boolean_key,
                    invariant_ref=(
                        "every scaffold-layer observation should declare "
                        + boolean_key
                        + " literal False"
                    ),
                    message=(
                        "observation does not declare a literal False "
                        + boolean_key
                        + " key"
                    ),
                    halt_required=False,
                )
        carries_a_note = any(
            note_key in observation for note_key in _NON_CLAIM_NOTE_FIELDS
        )
        if not carries_a_note:
            recorder.add(
                category="missing_non_claim_note",
                severity="info",
                target_observation_kind=kind,
                target_path="",
                invariant_ref="scaffold-layer non-claim note convention",
                message=(
                    "observation does not declare any of the recognized "
                    "non-claim note fields"
                ),
                halt_required=False,
            )
    else:
        recorder.add(
            category="diagnostic_input_shape",
            severity="info",
            target_observation_kind=kind,
            target_path="observation_kind",
            invariant_ref=(
                "WO-58 reporter recognizes a bounded set of "
                "observation_kind values"
            ),
            message=(
                "observation_kind {0!r} is not among the recognized "
                "scaffold-layer kinds".format(kind)
            ),
            halt_required=False,
        )

    for path, value in _walk_with_path(observation, ""):
        if _path_inside_diagnostics(path):
            continue
        leaf_name = path.rsplit("/", 1)[-1] if path else ""

        if (
            leaf_name in _ALL_AUTHORIZATION_BOOLEAN_KEYS
            and value is True
        ):
            recorder.add(
                category="authorization_boolean_true",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "WO-47 through WO-57 require every authorization / "
                    "readiness / selection boolean to be literal False"
                ),
                message=(
                    "{0} is literal True; authorization / readiness / "
                    "selection booleans must be literal False at every "
                    "scaffold layer".format(leaf_name)
                ),
                halt_required=True,
            )
        if leaf_name == "real_benchmark_ready" and value is True:
            recorder.add(
                category="benchmark_readiness_claim",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "WO-39 / WO-40 readiness gate keeps "
                    "real_benchmark_ready literal False until "
                    "Codex-authorized real benchmark execution"
                ),
                message="real_benchmark_ready declared True at observation layer",
                halt_required=True,
            )
        if (
            leaf_name in _ADMISSION_QUALIFICATION_COUNT_KEYS
            and isinstance(value, int)
            and not isinstance(value, bool)
            and value != 0
        ):
            recorder.add(
                category="admission_or_qualification_count_nonzero",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "scaffold layers carry corpus_admitted_count and "
                    "qualified_count as literal 0"
                ),
                message=(
                    "{0} is {1!r}; scaffold layers must carry literal "
                    "0 for this count".format(leaf_name, value)
                ),
                halt_required=True,
            )
        if (
            leaf_name == "qualified"
            and value is True
        ):
            recorder.add(
                category="source_quarantine_violation",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "WO-55 register and WO-56 bridge keep per-entry "
                    "qualified literal False"
                ),
                message="per-entry qualified declared True at observation layer",
                halt_required=True,
            )
        if (
            leaf_name == "corpus_admitted"
            and value is True
        ):
            recorder.add(
                category="source_quarantine_violation",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "WO-55 register and WO-56 bridge keep per-entry "
                    "corpus_admitted literal False"
                ),
                message=(
                    "per-entry corpus_admitted declared True at "
                    "observation layer"
                ),
                halt_required=True,
            )
        if leaf_name in ROUTE_STATUS_FIELDS:
            recorder.add(
                category="route_status_claim",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "WO-54 / WO-55 / WO-56 forbid route-status fields at "
                    "scaffold layers"
                ),
                message=(
                    "route-status field {0!r} present at observation "
                    "layer".format(leaf_name)
                ),
                halt_required=True,
            )
            recorder.add(
                category="route_first_violation",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref="route-first invariant",
                message=(
                    "route-shaped field {0!r} present in an observation "
                    "that is not authorized to declare route status".format(
                        leaf_name
                    )
                ),
                halt_required=True,
            )
        if leaf_name in ARCHITECTURE_SELECTION_FIELDS:
            recorder.add(
                category="architecture_selection_claim",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "no architecture / vendor / library / index family "
                    "/ ANN backend / retrieval family / production system "
                    "is selected"
                ),
                message=(
                    "architecture-shaped field {0!r} present at "
                    "observation layer".format(leaf_name)
                ),
                halt_required=True,
            )
        if isinstance(value, str) and value in ARCHITECTURE_SELECTION_FIELDS:
            recorder.add(
                category="architecture_selection_claim",
                severity="error",
                target_observation_kind=kind,
                target_path=path,
                invariant_ref=(
                    "no architecture / vendor / library / index family "
                    "/ ANN backend / retrieval family / production system "
                    "is selected"
                ),
                message=(
                    "architecture-shaped string value present at "
                    "observation layer"
                ),
                halt_required=True,
            )


def run_scaffold_route_invariant_diagnostic_reporter(observations, event_log):
    """Inspect already-loaded scaffold observation dicts and emit
    deterministic review diagnostics.

    Returns a fresh dict with exactly the thirteen allowed keys in
    `ALLOWED_OUTPUT_KEYS` on clean pass. Raises only on malformed
    input or forbidden language on input or output surfaces;
    advisory diagnostics with `halt_required: True` are recorded as
    fields inside the report and do NOT cause the reporter to
    raise.
    """
    if not isinstance(observations, list):
        event_log.halt(
            "scaffold_route_invariant_diagnostic_reporter_non_list_observations",
            observations_type=type(observations).__name__,
        )
        raise NonListDiagnosticObservations("observations must be a list")

    _assert_no_forbidden_language(observations, event_log)

    event_log.append(
        "scaffold_route_invariant_diagnostic_reporter_started",
        observations_count=len(observations),
    )

    recorder = _Recorder()

    for observation in observations:
        if not isinstance(observation, dict):
            event_log.halt(
                "scaffold_route_invariant_diagnostic_reporter_non_object_observation",
                observation_type=type(observation).__name__,
            )
            raise NonObjectDiagnosticObservation(
                "each observation must be a dict"
            )
        kind = observation.get("observation_kind")
        if not isinstance(kind, str) or not kind:
            event_log.halt(
                "scaffold_route_invariant_diagnostic_reporter_missing_observation_kind",
            )
            raise MissingObservationKind(
                "observation must declare a non-empty string observation_kind"
            )
        _inspect_observation(observation, recorder, event_log)

    diagnostics = list(recorder.diagnostics)
    error_count = sum(1 for d in diagnostics if d["severity"] == "error")
    warning_count = sum(1 for d in diagnostics if d["severity"] == "warning")
    info_count = sum(1 for d in diagnostics if d["severity"] == "info")
    halt_required_count = sum(1 for d in diagnostics if d["halt_required"])

    output = {
        "reporter_kind": "scaffold_route_invariant_diagnostic_reporter",
        "observations_checked_count": len(observations),
        "diagnostics_count": len(diagnostics),
        "error_count": error_count,
        "warning_count": warning_count,
        "info_count": info_count,
        "halt_required_count": halt_required_count,
        "diagnostics": diagnostics,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "reporter_note": _REPORTER_NOTE,
    }
    _assert_no_forbidden_language(output, event_log)

    event_log.append(
        "scaffold_route_invariant_diagnostic_reporter_passed",
        observations_checked_count=len(observations),
        diagnostics_count=len(diagnostics),
        error_count=error_count,
        warning_count=warning_count,
        info_count=info_count,
        halt_required_count=halt_required_count,
    )
    return output
