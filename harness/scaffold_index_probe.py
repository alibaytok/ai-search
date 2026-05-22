"""Scaffold-internal indexing-logic probe over admitted synthetic payloads.

Per WO-47 (DC-047): this module builds a small in-memory probe over the
WO-31 admitted first-wave synthetic payloads (`golden-intents`,
`hard-negatives`, `boundary-violations`) and exercises route-first
retrieval boundary behavior at the scaffold level. It does NOT
perform real benchmark execution, does NOT invoke a real or mock
adapter, does NOT collect quality / performance metrics, does NOT
score, does NOT rank, and does NOT select any architecture / vendor /
library / index family / ANN backend / neural re-scorer / retrieval
family / ablation cell / multi-stage variant / production system.

The probe index is scaffold-only. It is NOT a selected index
architecture. The output dict carries `selection_made: False`,
`measurement_authorized: False`, `real_benchmark_authorized: False`,
and `real_benchmark_ready: False` as literal constants in every
emitted path.

Why this is an indexing-logic probe and not a real benchmark:
- No real retrieval call.
- No external corpus.
- No metric, no score, no aggregation, no ranking.
- Each entry's expected outcome is read from the payload itself
  (per the WO-30 / DC-033 entry-level shape and the WO-31 / DC-034
  payload contract). The probe verifies that the route-first
  boundary rules HOLD across the entries; it does not test which
  retrieval architecture would best discover the entries.

The five WO-21 plane names, the canonical forbidden selection
language list, and the canonical forbidden claim language list are
reused from `harness.payload_loader` and `harness.review_package`.
No new copy of any list is created (the WO-32 drift-risk policy
holds). The local-mirror `"score"` / `"scoring"` extension is
applied at module scope, matching the WO-45 post-Codex-hardening
pattern.

Public surface:

    run_scaffold_index_probe(payloads_by_class, event_log) -> dict

The function:

- Accepts a dict whose keys are admitted fixture-class strings and
  whose values are already-loaded payload dicts (the JSON values
  authored under WO-31, parsed by the caller).
- Does not read files. Does not write files.
- Does not call any adapter (real or mock).
- Imports only stdlib + harness-internal symbols.
- Validates the input in documented order.
- Builds a small in-memory probe index from the payload entries.
- Produces a per-entry observation event of one of five kinds:
  `official`, `candidate`, `normalized`, `miss`,
  `contract_failure`.
- Returns a fresh dict with exactly the twelve allowed top-level
  keys (`ALLOWED_OUTPUT_KEYS`).
"""

from harness.payload_loader import (
    FORBIDDEN_CLAIM_PHRASES,
    WO_21_PLANE_NAMES,
)
from harness.review_package import FORBIDDEN_PHRASES


REQUIRED_PAYLOAD_CLASSES = (
    "golden-intents",
    "hard-negatives",
    "boundary-violations",
)

# Local mirror of the WO-35 review-time forbidden-language extension,
# applied at module scope. Consolidation into
# `harness.review_package.FORBIDDEN_PHRASES` remains deferred to a
# future Codex packet (file outside WO-47 allowed-files list).
PROBE_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_OUTPUT_KEYS = (
    "probe_kind",
    "entries_indexed_count",
    "official_observation_count",
    "candidate_observation_count",
    "normalized_observation_count",
    "miss_observation_count",
    "contract_failure_observation_count",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "probe_note",
)

OFFICIAL_PLANE = "official_route_results"
CANDIDATE_PLANE = "candidate_route_results"
NORMALIZED_PLANE = "normalized_material_support_results"


class NonObjectPayloadsByClass(Exception):
    """Raised when `payloads_by_class` is not a dict."""


class MissingRequiredPayloadClass(Exception):
    """Raised when `payloads_by_class` is missing a required admitted class key."""


class NonObjectPayload(Exception):
    """Raised when a per-class payload value is not a dict."""


class MissingOrNonListEntries(Exception):
    """Raised when a payload's `entries` is missing or not a list."""


class PayloadClassMismatch(Exception):
    """Raised when a payload's `fixture_class` does not match its key in `payloads_by_class`."""


class DuplicateFixtureIdAcrossProbe(Exception):
    """Raised when the same `fixture_id` appears in more than one entry across the probe input."""


class HardNegativeForbiddenOfficialReturn(Exception):
    """Raised when a `hard-negatives` entry would land on the official_route_results plane."""


class BoundaryViolationTreatedAsSuccess(Exception):
    """Raised when a `boundary-violations` entry's shape does not declare the violation outcome as forbidden."""


class ForbiddenLanguageInProbeOutput(Exception):
    """Raised when a phrase from the extended forbidden-language sets appears in the probe output or a surfaced field."""


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


def _first_forbidden_phrase(text):
    """Return the first forbidden phrase found in `text`, or None."""
    if not isinstance(text, str):
        return None
    lowered = text.lower()
    for phrase in PROBE_OUTPUT_FORBIDDEN_PHRASES:
        if phrase in lowered:
            return phrase
    for phrase in FORBIDDEN_CLAIM_PHRASES:
        if phrase in lowered:
            return phrase
    return None


def _validate_input_shape(payloads_by_class, event_log):
    """Validate the top-level input shape and per-class structure.

    Validation order:
      1. Top-level value is a dict.
      2. Every required admitted class key is present.
      3. Each per-class value is a dict.
      4. Each payload's `fixture_class` matches its key.
      5. Each payload's `entries` is a non-empty list.

    Each violation records an explicit halt event before raising.
    """
    if not isinstance(payloads_by_class, dict):
        event_log.halt(
            "scaffold_index_probe_non_object_input",
            top_level_type=type(payloads_by_class).__name__,
        )
        raise NonObjectPayloadsByClass(
            "payloads_by_class must be a dict; got {0!r}".format(
                type(payloads_by_class).__name__
            )
        )

    for required_class in REQUIRED_PAYLOAD_CLASSES:
        if required_class not in payloads_by_class:
            event_log.halt(
                "scaffold_index_probe_missing_required_class",
                missing_class=required_class,
            )
            raise MissingRequiredPayloadClass(
                "payloads_by_class is missing required class {0!r}".format(
                    required_class
                )
            )

    for class_name, payload in payloads_by_class.items():
        if not isinstance(payload, dict):
            event_log.halt(
                "scaffold_index_probe_non_object_payload",
                class_name=class_name,
                payload_type=type(payload).__name__,
            )
            raise NonObjectPayload(
                "payload for class {0!r} must be a dict; got {1!r}".format(
                    class_name, type(payload).__name__
                )
            )
        if payload.get("fixture_class") != class_name:
            event_log.halt(
                "scaffold_index_probe_class_mismatch",
                class_name=class_name,
                declared_class=payload.get("fixture_class"),
            )
            raise PayloadClassMismatch(
                "payload for class {0!r} declares fixture_class={1!r}".format(
                    class_name, payload.get("fixture_class")
                )
            )
        entries = payload.get("entries")
        if not isinstance(entries, list) or len(entries) == 0:
            event_log.halt(
                "scaffold_index_probe_missing_or_non_list_entries",
                class_name=class_name,
                entries_type=type(entries).__name__,
            )
            raise MissingOrNonListEntries(
                "payload for class {0!r} has missing or non-list entries".format(
                    class_name
                )
            )


def _build_probe_index(payloads_by_class, event_log):
    """Build the in-memory probe index keyed by fixture_id.

    The probe index is scaffold-only. It is NOT a selected index
    architecture. It is a flat mapping from fixture_id to
    (class_name, entry) used to detect duplicates and to drive
    per-entry observation in a deterministic order (class-order then
    entry-order within each class).

    Duplicate fixture_ids across the probe input are rejected; a
    duplicate would either mean two different entries sharing an id
    (a content-integrity error) or the same entry surfacing twice
    (a probe-input error). Either way, ambiguous identity is
    rejected.
    """
    index = {}
    order = []
    for class_name in REQUIRED_PAYLOAD_CLASSES:
        payload = payloads_by_class[class_name]
        for entry in payload["entries"]:
            if not isinstance(entry, dict):
                # Defensive; the WO-32 loader would normally reject
                # non-dict entries upstream. Treat as a probe-input
                # error here too.
                event_log.halt(
                    "scaffold_index_probe_non_object_entry",
                    class_name=class_name,
                    entry_type=type(entry).__name__,
                )
                raise NonObjectPayload(
                    "entry in class {0!r} must be a dict; got {1!r}".format(
                        class_name, type(entry).__name__
                    )
                )
            fixture_id = entry.get("fixture_id")
            if fixture_id in index:
                event_log.halt(
                    "scaffold_index_probe_duplicate_fixture_id",
                    fixture_id=fixture_id,
                    first_class=index[fixture_id][0],
                    second_class=class_name,
                )
                raise DuplicateFixtureIdAcrossProbe(
                    "fixture_id {0!r} appears more than once in the probe "
                    "input (first in class {1!r}, second in class "
                    "{2!r})".format(
                        fixture_id, index[fixture_id][0], class_name
                    )
                )
            index[fixture_id] = (class_name, entry)
            order.append(fixture_id)
    return index, order


def _observe_golden_intents_entry(entry, event_log):
    """Return (observation_kind, observation_dict) for a golden-intents entry."""
    expected = entry.get("expected_outcome_class")
    fixture_id = entry.get("fixture_id")
    if expected == "official_route_expected":
        ref = entry.get("expected_official_route_reference") or {}
        observation = {
            "plane": OFFICIAL_PLANE,
            "synthetic_route_identifier": ref.get("synthetic_route_identifier"),
            # Mirror the entry's explicit non-validation disclaimers.
            "is_promotion_trigger": False,
        }
        return "official", observation
    # miss_expected (or any non-official outcome class) is treated
    # as a miss. The golden-intents payload schema documents exactly
    # two expected_outcome_class values; both are handled.
    miss_classification = entry.get("miss_classification")
    observation = {
        "plane": OFFICIAL_PLANE,
        "plane_is_empty_for_this_entry": True,
        "miss_classification": miss_classification,
        "fixture_id": fixture_id,
    }
    return "miss", observation


def _observe_hard_negatives_entry(entry, event_log):
    """Return (observation_kind, observation_dict) for a hard-negatives entry.

    The hard-negatives contract requires that the entry never land on
    the official plane. If `allowed_planes` includes the official
    plane (a tampered payload) the probe halts with
    HardNegativeForbiddenOfficialReturn. The
    `must_not_authorize_official_return` field is also checked
    defensively.
    """
    markers = entry.get("plane_separation_markers") or {}
    allowed_planes = markers.get("allowed_planes") or []
    if not isinstance(allowed_planes, list):
        allowed_planes = []

    if OFFICIAL_PLANE in allowed_planes:
        event_log.halt(
            "scaffold_index_probe_hard_negative_forbidden_official",
            fixture_id=entry.get("fixture_id"),
            allowed_planes=list(allowed_planes),
        )
        raise HardNegativeForbiddenOfficialReturn(
            "hard-negatives entry {0!r} would land on the official plane; "
            "allowed_planes={1!r}".format(
                entry.get("fixture_id"), allowed_planes
            )
        )
    if entry.get("must_not_authorize_official_return") is False:
        event_log.halt(
            "scaffold_index_probe_hard_negative_forbidden_official",
            fixture_id=entry.get("fixture_id"),
            reason_detail="must_not_authorize_official_return_false",
        )
        raise HardNegativeForbiddenOfficialReturn(
            "hard-negatives entry {0!r} declares "
            "must_not_authorize_official_return is False".format(
                entry.get("fixture_id")
            )
        )

    # Decide which non-official plane to land on. Prefer the candidate
    # plane when allowed; otherwise the normalized-material plane.
    # Both are valid scaffold observations under the hard-negatives
    # contract (per WO-31 entry shapes).
    if CANDIDATE_PLANE in allowed_planes:
        plane = CANDIDATE_PLANE
        kind = "candidate"
    elif NORMALIZED_PLANE in allowed_planes:
        plane = NORMALIZED_PLANE
        kind = "normalized"
    else:
        # Fallback: even with no candidate or normalized plane
        # explicitly allowed, the hard-negatives contract still
        # forbids the official plane. Emit a candidate observation
        # with the empty-allowed-planes posture recorded.
        plane = CANDIDATE_PLANE
        kind = "candidate"

    observation = {
        "plane": plane,
        "fixture_id": entry.get("fixture_id"),
        "near_match_classification": entry.get("near_match_classification"),
        "allowed_planes": list(allowed_planes),
        "must_not_authorize_official_return": True,
    }
    return kind, observation


def _observe_boundary_violations_entry(entry, event_log):
    """Return ("contract_failure", observation_dict) for a boundary-violations entry.

    The boundary-violations contract requires the entry to declare its
    violation outcome as forbidden. A tampered entry that declares
    the violation outcome as a valid output is rejected with
    BoundaryViolationTreatedAsSuccess. The probe ALWAYS emits a
    contract-failure observation for a well-formed boundary-violations
    entry; it never emits a successful retrieval observation.
    """
    expected = entry.get("expected_disqualification") or {}
    if not isinstance(expected, dict):
        expected = {}
    if expected.get("expected_halt") is not True:
        event_log.halt(
            "scaffold_index_probe_boundary_violation_treated_as_success",
            fixture_id=entry.get("fixture_id"),
            reason_detail="expected_halt_not_true",
        )
        raise BoundaryViolationTreatedAsSuccess(
            "boundary-violations entry {0!r} does not declare "
            "expected_halt is True".format(entry.get("fixture_id"))
        )
    if expected.get("is_forbidden_output") is not True:
        event_log.halt(
            "scaffold_index_probe_boundary_violation_treated_as_success",
            fixture_id=entry.get("fixture_id"),
            reason_detail="is_forbidden_output_not_true",
        )
        raise BoundaryViolationTreatedAsSuccess(
            "boundary-violations entry {0!r} does not declare "
            "is_forbidden_output is True".format(entry.get("fixture_id"))
        )
    if expected.get("is_valid_output") is True:
        event_log.halt(
            "scaffold_index_probe_boundary_violation_treated_as_success",
            fixture_id=entry.get("fixture_id"),
            reason_detail="is_valid_output_true",
        )
        raise BoundaryViolationTreatedAsSuccess(
            "boundary-violations entry {0!r} declares is_valid_output is "
            "True; boundary violations are not valid outputs".format(
                entry.get("fixture_id")
            )
        )

    markers = entry.get("plane_separation_markers") or {}
    observation = {
        "fixture_id": entry.get("fixture_id"),
        "target_contract_assertion": entry.get("target_contract_assertion"),
        "violation_plane_in_observed_output": markers.get(
            "violation_plane_in_observed_output"
        ),
        "forbidden_plane_collapse": markers.get("forbidden_plane_collapse"),
        "halt_classification": expected.get("halt_classification"),
        "is_forbidden_output": True,
        "is_valid_output": False,
    }
    return "contract_failure", observation


def _assert_no_forbidden_language_in_surface(value, event_log):
    """Scan every string scalar before it can reach probe output or events."""
    for text in _walk_strings(value):
        offending = _first_forbidden_phrase(text)
        if offending is not None:
            event_log.halt(
                "scaffold_index_probe_forbidden_language",
                forbidden_phrase=offending,
            )
            raise ForbiddenLanguageInProbeOutput(
                "Forbidden phrase {0!r} found in probe surface string: "
                "{1!r}".format(offending, text)
            )


def run_scaffold_index_probe(payloads_by_class, event_log):
    """Run the scaffold-internal indexing-logic probe.

    Validates the input, builds a small in-memory probe index, runs
    per-entry observation according to each entry's class semantics,
    and returns a fresh dict with exactly the twelve allowed
    top-level keys. The probe does NOT invoke any adapter (real or
    mock), does NOT compute any metric, does NOT score, does NOT
    rank, and does NOT select any architecture. The output's
    `selection_made`, `measurement_authorized`,
    `real_benchmark_authorized`, and `real_benchmark_ready` are all
    literal `False` on every emitted path.

    Events recorded:
      - `scaffold_index_probe_started` at the start of per-entry
        observation.
      - One per-entry observation event per entry; type is one of
        `scaffold_index_probe_official_observation`,
        `scaffold_index_probe_candidate_observation`,
        `scaffold_index_probe_normalized_observation`,
        `scaffold_index_probe_miss_observation`, or
        `scaffold_index_probe_contract_failure_observation`.
      - `scaffold_index_probe_run_ended` after all entries have been
        observed.

    Halt-before-raise on every rejection path. The function does not
    read or write any file. The input dict is not modified.
    """
    # Step 1: input shape validation.
    _validate_input_shape(payloads_by_class, event_log)

    # Step 2: scan the accepted payload surface before any entry values
    # are copied into observation events. The halt event records only the
    # offending phrase, not the source text, so forbidden language cannot
    # leak through the rejection event itself.
    _assert_no_forbidden_language_in_surface(payloads_by_class, event_log)

    # Step 3: build the probe index (also catches duplicate fixture_ids).
    index, order = _build_probe_index(payloads_by_class, event_log)

    # Step 4: per-entry observation.
    event_log.append(
        "scaffold_index_probe_started",
        entries_indexed_count=len(order),
        class_count=len(REQUIRED_PAYLOAD_CLASSES),
    )

    official_count = 0
    candidate_count = 0
    normalized_count = 0
    miss_count = 0
    contract_failure_count = 0

    for fixture_id in order:
        class_name, entry = index[fixture_id]
        if class_name == "golden-intents":
            kind, observation = _observe_golden_intents_entry(entry, event_log)
        elif class_name == "hard-negatives":
            kind, observation = _observe_hard_negatives_entry(entry, event_log)
        elif class_name == "boundary-violations":
            kind, observation = _observe_boundary_violations_entry(
                entry, event_log
            )
        else:
            # Unreachable: _validate_input_shape verified every
            # required class is present and the per-class iteration
            # above iterates only over REQUIRED_PAYLOAD_CLASSES. The
            # branch exists to fail loudly if REQUIRED_PAYLOAD_CLASSES
            # is ever extended without updating the dispatcher.
            event_log.halt(
                "scaffold_index_probe_unknown_class",
                class_name=class_name,
                fixture_id=fixture_id,
            )
            raise MissingRequiredPayloadClass(
                "Unknown class {0!r} in probe dispatcher; required "
                "classes are {1!r}".format(
                    class_name, REQUIRED_PAYLOAD_CLASSES
                )
            )

        if kind == "official":
            official_count += 1
            event_type = "scaffold_index_probe_official_observation"
        elif kind == "candidate":
            candidate_count += 1
            event_type = "scaffold_index_probe_candidate_observation"
        elif kind == "normalized":
            normalized_count += 1
            event_type = "scaffold_index_probe_normalized_observation"
        elif kind == "miss":
            miss_count += 1
            event_type = "scaffold_index_probe_miss_observation"
        else:
            # kind == "contract_failure"
            contract_failure_count += 1
            event_type = "scaffold_index_probe_contract_failure_observation"

        event_log.append(
            event_type,
            class_name=class_name,
            fixture_id=fixture_id,
            observation=observation,
        )

    # Step 5: assemble the output dict.
    output = {
        "probe_kind": "scaffold_indexing_logic_probe",
        "entries_indexed_count": len(order),
        "official_observation_count": official_count,
        "candidate_observation_count": candidate_count,
        "normalized_observation_count": normalized_count,
        "miss_observation_count": miss_count,
        "contract_failure_observation_count": contract_failure_count,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "probe_note": (
            "Scaffold-internal indexing-logic probe per "
            "ai-search/47-scaffold-indexing-logic-probe.md. In-memory "
            "probe over WO-31 admitted synthetic payloads; not real "
            "benchmark execution; not real retrieval; not a selected "
            "index architecture. The Indexing Excellence Gate "
            "continues to govern selection."
        ),
    }

    # Step 6: forbidden-language hygiene on the assembled output. The
    # scan covers every string scalar emitted on the output surface
    # (counts and booleans are not strings; identifier values inside
    # observation events are not part of the output dict).
    _assert_no_forbidden_language_in_surface(output, event_log)

    event_log.append(
        "scaffold_index_probe_run_ended",
        entries_indexed_count=len(order),
        official_observation_count=official_count,
        candidate_observation_count=candidate_count,
        normalized_observation_count=normalized_count,
        miss_observation_count=miss_count,
        contract_failure_observation_count=contract_failure_count,
    )

    return output
