"""Level 0B workshop intent test matrix runner (WO-L0-WORKSHOP-INTENT-TEST-MATRIX-RUNNER-01).

WO-L0-WORKSHOP-INTENT-TEST-MATRIX-RUNNER-01 builds a deterministic
JSON-driven matrix runner that observes the existing Level 0B Intent
Core parser through its public FRAME-D shim and emits a fixed-shape
result dict listing per-case observed-vs-expected outcomes plus a
bounded failure classification per mismatch. The runner is bounded
review evidence only and is NOT a benchmark, NOT validation evidence,
NOT a golden intent set, NOT an evaluation set, NOT a regression gate,
NOT route validation, NOT source admission, NOT corpus admission, NOT a
parser-quality measurement, and NOT a selection event. The smoke matrix
distributed alongside this runner is the runner's own correctness
fixture and is NOT the parser-quality corpus; corpus design and corpus
authoring are reserved for separate Codex-authorized follow-up packets.

Pipeline position:

    matrix_file (JSON on disk)
      -> _load_matrix
      -> _validate_matrix_shape
      -> for each case: map_level0_workshop_user_intent
      -> _compare_observed_vs_expected
      -> _classify_failure
      -> emit fixed-shape result dict

Dependency direction is one-way: runner imports the FRAME-D public
function `map_level0_workshop_user_intent` and the bounded enum
constants `WORKSHOP_PROMPT_CATEGORIES` and `WORKSHOP_ITEM_KINDS` from
FRAME-C. Parser modules FRAME-A / FRAME-B / FRAME-C / FRAME-D do NOT
import this runner (verified by static-scan test in
`harness/tests/test_level0_workshop_intent_test_matrix_runner.py`).

The matrix loader is module-local and does NOT reuse
`harness/payload_loader.py` (which is benchmark-fixtures territory).
Same forbidden-language scan discipline is applied via a local helper
that pulls the bounded phrase tuples from `harness.payload_loader` and
`harness.review_package` constants only (no logic reuse).

Typo tolerance, ranking, scoring, similarity, distance, embedding,
vector, ANN backend, reranker, LLM / provider call, route object
creation, route selection, source qualification, corpus admission, real
benchmark execution, and architecture / vendor / library / index-family
/ production-system selection are all out of scope; the runner emits
bounded review evidence and does not flip any gating boolean.

All seven runner gating booleans (`selection_made`,
`measurement_authorized`, `real_benchmark_authorized`,
`real_benchmark_ready`, `source_qualification_authorized`,
`corpus_admission_authorized`, `route_created`) remain literal False on
every emitted path. The runner refuses to emit any case result whose
observed FRAME-D output flips any of those booleans True (halt-before-
raise with `IntentTestMatrixRunnerGatingBooleanFlipped`).

The bounded failure taxonomy is fourteen classes (thirteen named plus
`unknown`). Two named classes are RESERVED until the upstream layers
that would justify them land: `vocabulary_correction_miss` (reserved
until a Codex-authorized vocabulary correction packet lands) and
`ambiguity_clarification_gap` (reserved until a Codex-authorized
clarification surface packet lands). The classifier accepts both
classes in the enum but does NOT emit them in this packet; if the
classifier's heuristic resolves to a reserved class, the runner emits
`unknown` instead.

Module source is ASCII-only.

Public surface:

    run_intent_test_matrix(matrix_path, event_log) -> dict
"""

import json
import os
from harness.event_log import EventLog
from harness.level0_workshop_canonical_intent_frame import (
    WORKSHOP_ITEM_KINDS,
    WORKSHOP_PROMPT_CATEGORIES,
)
from harness.level0_workshop_user_intent_mapper import (
    map_level0_workshop_user_intent,
)
from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


# Allowed expected-kind values: the bounded WORKSHOP_ITEM_KINDS plus
# the `none` sentinel that FRAME-C emits for no-route / out-of-scope
# prompts (mirrors `_NO_ROUTE_KIND_LITERAL` in
# `harness/level0_workshop_derived_trace.py`).
_ALLOWED_KIND_VALUES = frozenset(set(WORKSHOP_ITEM_KINDS) | {"none"})


INTENT_TEST_MATRIX_RUNNER_KIND = "level0_workshop_intent_test_matrix_runner"
INTENT_TEST_MATRIX_KIND = "level0_workshop_intent_test_matrix"


# Bounded failure taxonomy. Order is stable; the bounded set is exactly
# fourteen entries (thirteen named plus `unknown`).
FAILURE_CLASSES = (
    "frame_a_normalization_gap",
    "frame_b_canonical_set_gap",
    "frame_b_inflection_gap",
    "frame_b_negation_gap",
    "frame_c_synthesis_rule_gap",
    "frame_c_category_selector_gap",
    "frame_c_ambiguity_misreport",
    "ambiguity_clarification_gap",
    "frame_d_translation_gap",
    "out_of_scope_underdetect",
    "vocabulary_correction_miss",
    "fixture_distribution_drift",
    "expected_field_drift",
    "unknown",
)
_FAILURE_CLASS_SET = frozenset(FAILURE_CLASSES)


# Failure classes that the classifier may emit in this packet.
# `vocabulary_correction_miss` and `ambiguity_clarification_gap` are
# RESERVED in the enum and present in `FAILURE_CLASSES` but the
# classifier never emits them in this packet; if the heuristic resolves
# to either, the classifier emits `unknown` instead. The reservation
# carries forward until the upstream layer that would justify emission
# lands in a separate Codex-authorized packet.
RESERVED_FAILURE_CLASSES = frozenset({
    "vocabulary_correction_miss",
    "ambiguity_clarification_gap",
})


# Bounded enum of expected-field whitelist (six fields).
EXPECTED_FIELDS = (
    "category",
    "expected_item_kinds_touched",
    "ambiguity_observed",
    "normalized_intent_observation",
    "candidate_surface_expected",
    "rejection_surface_expected",
)
_EXPECTED_FIELD_SET = frozenset(EXPECTED_FIELDS)


# Required top-level matrix keys.
_REQUIRED_MATRIX_KEYS = frozenset({
    "intent_test_matrix_kind",
    "matrix_id",
    "matrix_note",
    "cases",
})


# Required per-case keys.
_REQUIRED_CASE_KEYS = frozenset({
    "case_id",
    "prompt_text",
    "expected",
    "tolerated_variants",
    "tags",
    "rationale",
})


# Allowed normalized-intent labels (mirrored from FRAME-D shim).
_ALLOWED_NORMALIZED_INTENTS = (
    "clear_single_intent",
    "workflow_intent",
    "skill_intent",
    "agent_surface_workflow_intent",
    "instruction_surface_workflow_intent",
    "prompt_surface_workflow_intent",
    "ambiguous_user_intent",
    "no_route",
    "near_miss_rejection",
)
_ALLOWED_NORMALIZED_INTENT_SET = frozenset(_ALLOWED_NORMALIZED_INTENTS)


# Allowed candidate-surface and rejection-surface literal strings
# (mirrored from FRAME-C `_build_workshop_prompt_record`).
_ALLOWED_CANDIDATE_SURFACES = (
    "candidate fragment of declared shape",
    "multiple candidate surfaces expected",
    "no candidate surface expected",
)
_ALLOWED_CANDIDATE_SURFACE_SET = frozenset(_ALLOWED_CANDIDATE_SURFACES)


_ALLOWED_REJECTION_SURFACES = (
    "no_forced_selection",
    "prompt_out_of_repo_scope",
    "repo_meta_section_near_miss",
)
_ALLOWED_REJECTION_SURFACE_SET = frozenset(_ALLOWED_REJECTION_SURFACES)


# Allowed top-level output keys.
ALLOWED_OUTPUT_KEYS = (
    "intent_test_matrix_runner_kind",
    "matrix_id",
    "case_count",
    "passed_count",
    "failed_count",
    "case_results",
    "per_failure_class_counts",
    "per_tag_counts",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
    "runner_note",
)


# Bounded list of gating booleans the runner emits in its own result
# dict. The runner forces each to literal False on every emitted path.
GATING_BOOLEANS = (
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)


# Subset of `GATING_BOOLEANS` that the FRAME-D public function actually
# emits on its output dict. The runner refuses to emit any case result
# whose observed FRAME-D output flips any of these True; observed
# `route_created` is not checked here because the FRAME-D shim does
# not emit it (the route_created boolean lives on the FRAME-A /
# FRAME-B / FRAME-C dicts but is not exposed by the FRAME-D shim).
_OBSERVED_GATING_BOOLEANS = (
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
)


# Per-case result key whitelist.
_CASE_RESULT_KEYS = frozenset({
    "case_id",
    "match",
    "classified_as",
    "observed_category",
    "expected_category",
    "observed_kinds",
    "expected_kinds",
    "observed_ambiguity",
    "expected_ambiguity",
    "observed_normalized_intent",
    "expected_normalized_intent",
    "observed_candidate_surface",
    "expected_candidate_surface",
    "observed_rejection_surface",
    "expected_rejection_surface",
    "differing_fields",
    "tags",
    "rationale",
})


# Forbidden route-status field names. The runner must not emit any of
# these in the result or in any per-case_result.
_FORBIDDEN_ROUTE_STATUS_FIELDS = (
    "official",
    "is_route",
    "is_official_route",
    "selected_as_official",
    "official_route_authorized",
    "route_authorized",
    "production_route",
    "selected_route",
    "executable",
    "route_state",
    "plane",
)


# Forbidden output-field names that no result key may equal.
_FORBIDDEN_OUTPUT_FIELD_NAMES = (
    "ranking_performed",
    "scoring_performed",
    "confidence",
    "score",
    "distance",
    "best_match",
    "threshold",
    "similarity",
)


_RUNNER_NOTE = (
    "level0_workshop_intent_test_matrix_runner: a deterministic "
    "JSON-driven runner that invokes only the FRAME-D public function "
    "map_level0_workshop_user_intent and emits bounded per-case "
    "review-only evidence plus a fourteen-class bounded failure "
    "classification; this runner is NOT a benchmark, NOT a "
    "route-validation artifact reserved for OQ-005 / OQ-039 authority, "
    "NOT a golden intent set, NOT an evaluation set, NOT a regression "
    "gate, NOT source admission, NOT corpus admission, NOT a "
    "parser-quality measurement; the smoke matrix is NOT the "
    "parser-quality corpus and the 26 workshop seed prompts are NOT "
    "the system boundary; vocabulary_correction_miss and "
    "ambiguity_clarification_gap are RESERVED failure classes whose "
    "emission requires upstream layers not yet authorized; no "
    "measurement authorization; no benchmark execution authorization; "
    "no real-benchmark-ready flip; no selection event."
)


class NonStringMatrixPath(Exception):
    """Raised when `matrix_path` is not a string."""


class MatrixFileNotFound(Exception):
    """Raised when the matrix file does not exist."""


class InvalidJSONMatrix(Exception):
    """Raised when the matrix file is not valid JSON."""


class NonDictMatrix(Exception):
    """Raised when the loaded matrix is not a dict."""


class MissingMatrixKey(Exception):
    """Raised when the matrix is missing a required key."""


class UnknownMatrixKey(Exception):
    """Raised when the matrix contains an unknown top-level key."""


class InvalidMatrixKind(Exception):
    """Raised when `intent_test_matrix_kind` is not the expected literal."""


class NonStringMatrixId(Exception):
    """Raised when `matrix_id` is not a non-empty string."""


class NonStringMatrixNote(Exception):
    """Raised when `matrix_note` is not a string."""


class NonListCases(Exception):
    """Raised when `cases` is not a list."""


class EmptyCases(Exception):
    """Raised when `cases` is empty."""


class NonObjectCase(Exception):
    """Raised when a case entry is not a dict."""


class MissingCaseKey(Exception):
    """Raised when a case is missing a required key."""


class UnknownCaseKey(Exception):
    """Raised when a case contains an unknown key."""


class NonStringCaseId(Exception):
    """Raised when `case_id` is not a non-empty string."""


class DuplicateCaseId(Exception):
    """Raised when two cases share the same `case_id`."""


class NonStringPromptText(Exception):
    """Raised when `prompt_text` is not a string."""


class EmptyPromptText(Exception):
    """Raised when `prompt_text` is empty after trimming."""


class NonDictExpected(Exception):
    """Raised when `expected` is not a dict."""


class UnknownExpectedKey(Exception):
    """Raised when `expected` contains an unknown key."""


class UnknownCategory(Exception):
    """Raised when an expected category is outside WORKSHOP_PROMPT_CATEGORIES."""


class NonListExpectedKinds(Exception):
    """Raised when `expected_item_kinds_touched` is not a list."""


class UnknownItemKind(Exception):
    """Raised when an expected kind is outside WORKSHOP_ITEM_KINDS."""


class NonBooleanAmbiguity(Exception):
    """Raised when `ambiguity_observed` is not a bool."""


class UnknownNormalizedIntent(Exception):
    """Raised when `normalized_intent_observation` is outside the bounded enum."""


class UnknownCandidateSurface(Exception):
    """Raised when `candidate_surface_expected` is outside the bounded enum."""


class UnknownRejectionSurface(Exception):
    """Raised when `rejection_surface_expected` is outside the bounded enum."""


class NonListToleratedVariants(Exception):
    """Raised when `tolerated_variants` is not a list."""


class NonObjectToleratedVariant(Exception):
    """Raised when a tolerated_variants entry is not a dict."""


class NonListTags(Exception):
    """Raised when `tags` is not a list."""


class NonStringTag(Exception):
    """Raised when a tag entry is not a string."""


class NonStringRationale(Exception):
    """Raised when `rationale` is not a string."""


class IntentTestMatrixRunnerGatingBooleanFlipped(Exception):
    """Raised when an observed FRAME-D output flips any gating boolean True."""


class IntentTestMatrixRunnerRouteStatusFieldPresent(Exception):
    """Raised when any emitted dict carries a forbidden route-status field."""


class ForbiddenLanguageInLevel0WorkshopIntentTestMatrixRunner(Exception):
    """Raised when a forbidden phrase appears in module-authored strings
    inside the matrix or the result."""


def _walk_strings(value):
    """Yield every string scalar inside a nested value."""
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


def _assert_no_forbidden_language(value, event_log, location):
    """Halt and raise if any forbidden phrase appears in `value`."""
    for text in _walk_strings(value):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="intent_test_matrix_runner_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopIntentTestMatrixRunner(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="intent_test_matrix_runner_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopIntentTestMatrixRunner(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _module_authored_matrix_strings(matrix):
    """Return only the matrix's own module-authored strings (not user-
    authored prompt_text or rationale)."""
    return {
        "intent_test_matrix_kind": matrix["intent_test_matrix_kind"],
        "matrix_id": matrix["matrix_id"],
        "matrix_note": matrix["matrix_note"],
    }


def _module_authored_result_strings(result):
    """Return only the result's own module-authored strings."""
    return {
        "intent_test_matrix_runner_kind": result[
            "intent_test_matrix_runner_kind"
        ],
        "matrix_id": result["matrix_id"],
        "runner_note": result["runner_note"],
    }


def _load_matrix(matrix_path, event_log):
    """Local matrix loader. Does NOT reuse `harness/payload_loader.py`
    (which is benchmark-fixtures territory). Opens exactly one file:
    the matrix at `matrix_path`. No network, no subprocess, no
    additional file IO."""
    if not isinstance(matrix_path, str) or not matrix_path:
        event_log.halt(
            reason="intent_test_matrix_runner_non_string_matrix_path",
        )
        raise NonStringMatrixPath("matrix_path must be a non-empty string")
    if not os.path.isfile(matrix_path):
        event_log.halt(
            reason="intent_test_matrix_runner_matrix_file_not_found",
            matrix_path=matrix_path,
        )
        raise MatrixFileNotFound(
            "matrix file not found: {0}".format(matrix_path)
        )
    with open(matrix_path, "r", encoding="ascii") as handle:
        text = handle.read()
    try:
        return json.loads(text)
    except ValueError as exc:
        event_log.halt(
            reason="intent_test_matrix_runner_invalid_json_matrix",
            matrix_path=matrix_path,
            error=str(exc),
        )
        raise InvalidJSONMatrix(
            "matrix file is not valid JSON: {0}".format(exc)
        ) from exc


def _validate_matrix_shape(matrix, event_log):
    """Validate the top-level matrix dict shape; halt-before-raise on
    every failure path."""
    if not isinstance(matrix, dict):
        event_log.halt(reason="intent_test_matrix_runner_non_dict_matrix")
        raise NonDictMatrix("matrix must be a dict")

    observed_keys = set(matrix.keys())
    missing = _REQUIRED_MATRIX_KEYS - observed_keys
    if missing:
        event_log.halt(
            reason="intent_test_matrix_runner_missing_matrix_key",
            missing=sorted(missing),
        )
        raise MissingMatrixKey(
            "matrix missing required keys: {0}".format(sorted(missing))
        )
    unknown = observed_keys - _REQUIRED_MATRIX_KEYS
    if unknown:
        event_log.halt(
            reason="intent_test_matrix_runner_unknown_matrix_key",
            unknown=sorted(unknown),
        )
        raise UnknownMatrixKey(
            "matrix contains unknown keys: {0}".format(sorted(unknown))
        )

    if matrix["intent_test_matrix_kind"] != INTENT_TEST_MATRIX_KIND:
        event_log.halt(
            reason="intent_test_matrix_runner_invalid_matrix_kind",
            observed=matrix["intent_test_matrix_kind"],
        )
        raise InvalidMatrixKind(
            "intent_test_matrix_kind must be '{0}'".format(
                INTENT_TEST_MATRIX_KIND
            )
        )
    if not isinstance(matrix["matrix_id"], str) or not matrix["matrix_id"]:
        event_log.halt(
            reason="intent_test_matrix_runner_non_string_matrix_id",
        )
        raise NonStringMatrixId("matrix_id must be a non-empty string")
    if not isinstance(matrix["matrix_note"], str):
        event_log.halt(
            reason="intent_test_matrix_runner_non_string_matrix_note",
        )
        raise NonStringMatrixNote("matrix_note must be a string")

    if not isinstance(matrix["cases"], list):
        event_log.halt(reason="intent_test_matrix_runner_non_list_cases")
        raise NonListCases("cases must be a list")
    if len(matrix["cases"]) == 0:
        event_log.halt(reason="intent_test_matrix_runner_empty_cases")
        raise EmptyCases("cases must contain at least one case")

    case_ids = set()
    for index, case in enumerate(matrix["cases"]):
        _validate_case_shape(case, index, case_ids, event_log)


def _validate_case_shape(case, index, case_ids, event_log):
    """Validate one case dict's shape; halt-before-raise."""
    if not isinstance(case, dict):
        event_log.halt(
            reason="intent_test_matrix_runner_non_object_case",
            index=index,
        )
        raise NonObjectCase("case at index {0} must be a dict".format(index))

    observed_keys = set(case.keys())
    missing = _REQUIRED_CASE_KEYS - observed_keys
    if missing:
        event_log.halt(
            reason="intent_test_matrix_runner_missing_case_key",
            index=index,
            missing=sorted(missing),
        )
        raise MissingCaseKey(
            "case at index {0} missing required keys: {1}".format(
                index, sorted(missing)
            )
        )
    unknown = observed_keys - _REQUIRED_CASE_KEYS
    if unknown:
        event_log.halt(
            reason="intent_test_matrix_runner_unknown_case_key",
            index=index,
            unknown=sorted(unknown),
        )
        raise UnknownCaseKey(
            "case at index {0} contains unknown keys: {1}".format(
                index, sorted(unknown)
            )
        )

    if not isinstance(case["case_id"], str) or not case["case_id"]:
        event_log.halt(
            reason="intent_test_matrix_runner_non_string_case_id",
            index=index,
        )
        raise NonStringCaseId(
            "case_id at index {0} must be a non-empty string".format(index)
        )
    if case["case_id"] in case_ids:
        event_log.halt(
            reason="intent_test_matrix_runner_duplicate_case_id",
            case_id=case["case_id"],
        )
        raise DuplicateCaseId(
            "duplicate case_id: {0}".format(case["case_id"])
        )
    case_ids.add(case["case_id"])

    if not isinstance(case["prompt_text"], str):
        event_log.halt(
            reason="intent_test_matrix_runner_non_string_prompt_text",
            case_id=case["case_id"],
        )
        raise NonStringPromptText(
            "prompt_text for case {0} must be a string".format(case["case_id"])
        )
    if not case["prompt_text"].strip():
        event_log.halt(
            reason="intent_test_matrix_runner_empty_prompt_text",
            case_id=case["case_id"],
        )
        raise EmptyPromptText(
            "prompt_text for case {0} must be non-empty".format(
                case["case_id"]
            )
        )

    _validate_expected_shape(case["expected"], case["case_id"], event_log)
    _validate_tolerated_variants(
        case["tolerated_variants"], case["case_id"], event_log
    )

    if not isinstance(case["tags"], list):
        event_log.halt(
            reason="intent_test_matrix_runner_non_list_tags",
            case_id=case["case_id"],
        )
        raise NonListTags(
            "tags for case {0} must be a list".format(case["case_id"])
        )
    for tag in case["tags"]:
        if not isinstance(tag, str):
            event_log.halt(
                reason="intent_test_matrix_runner_non_string_tag",
                case_id=case["case_id"],
            )
            raise NonStringTag(
                "tags for case {0} must contain only strings".format(
                    case["case_id"]
                )
            )

    if not isinstance(case["rationale"], str):
        event_log.halt(
            reason="intent_test_matrix_runner_non_string_rationale",
            case_id=case["case_id"],
        )
        raise NonStringRationale(
            "rationale for case {0} must be a string".format(case["case_id"])
        )


def _validate_expected_shape(expected, case_id, event_log):
    """Validate one expected dict's shape; halt-before-raise."""
    if not isinstance(expected, dict):
        event_log.halt(
            reason="intent_test_matrix_runner_non_dict_expected",
            case_id=case_id,
        )
        raise NonDictExpected(
            "expected for case {0} must be a dict".format(case_id)
        )
    observed_keys = set(expected.keys())
    unknown = observed_keys - _EXPECTED_FIELD_SET
    if unknown:
        event_log.halt(
            reason="intent_test_matrix_runner_unknown_expected_key",
            case_id=case_id,
            unknown=sorted(unknown),
        )
        raise UnknownExpectedKey(
            "expected for case {0} contains unknown keys: {1}".format(
                case_id, sorted(unknown)
            )
        )
    if "category" in expected:
        if expected["category"] not in WORKSHOP_PROMPT_CATEGORIES:
            event_log.halt(
                reason="intent_test_matrix_runner_unknown_category",
                case_id=case_id,
                observed=expected["category"],
            )
            raise UnknownCategory(
                "expected.category for case {0} not in WORKSHOP_PROMPT_CATEGORIES".format(
                    case_id
                )
            )
    if "expected_item_kinds_touched" in expected:
        kinds = expected["expected_item_kinds_touched"]
        if not isinstance(kinds, list):
            event_log.halt(
                reason="intent_test_matrix_runner_non_list_expected_kinds",
                case_id=case_id,
            )
            raise NonListExpectedKinds(
                "expected.expected_item_kinds_touched for case {0} must be a list".format(
                    case_id
                )
            )
        for kind in kinds:
            if kind not in _ALLOWED_KIND_VALUES:
                event_log.halt(
                    reason="intent_test_matrix_runner_unknown_item_kind",
                    case_id=case_id,
                    observed=kind,
                )
                raise UnknownItemKind(
                    "expected kind '{0}' for case {1} not in WORKSHOP_ITEM_KINDS".format(
                        kind, case_id
                    )
                )
    if "ambiguity_observed" in expected:
        if not isinstance(expected["ambiguity_observed"], bool):
            event_log.halt(
                reason="intent_test_matrix_runner_non_boolean_ambiguity",
                case_id=case_id,
            )
            raise NonBooleanAmbiguity(
                "expected.ambiguity_observed for case {0} must be a bool".format(
                    case_id
                )
            )
    if "normalized_intent_observation" in expected:
        if (
            expected["normalized_intent_observation"]
            not in _ALLOWED_NORMALIZED_INTENT_SET
        ):
            event_log.halt(
                reason="intent_test_matrix_runner_unknown_normalized_intent",
                case_id=case_id,
                observed=expected["normalized_intent_observation"],
            )
            raise UnknownNormalizedIntent(
                "expected.normalized_intent_observation for case {0} not in bounded enum".format(
                    case_id
                )
            )
    if "candidate_surface_expected" in expected:
        if (
            expected["candidate_surface_expected"]
            not in _ALLOWED_CANDIDATE_SURFACE_SET
        ):
            event_log.halt(
                reason="intent_test_matrix_runner_unknown_candidate_surface",
                case_id=case_id,
                observed=expected["candidate_surface_expected"],
            )
            raise UnknownCandidateSurface(
                "expected.candidate_surface_expected for case {0} not in bounded enum".format(
                    case_id
                )
            )
    if "rejection_surface_expected" in expected:
        if (
            expected["rejection_surface_expected"]
            not in _ALLOWED_REJECTION_SURFACE_SET
        ):
            event_log.halt(
                reason="intent_test_matrix_runner_unknown_rejection_surface",
                case_id=case_id,
                observed=expected["rejection_surface_expected"],
            )
            raise UnknownRejectionSurface(
                "expected.rejection_surface_expected for case {0} not in bounded enum".format(
                    case_id
                )
            )


def _validate_tolerated_variants(variants, case_id, event_log):
    """Validate the per-case tolerated_variants list."""
    if not isinstance(variants, list):
        event_log.halt(
            reason="intent_test_matrix_runner_non_list_tolerated_variants",
            case_id=case_id,
        )
        raise NonListToleratedVariants(
            "tolerated_variants for case {0} must be a list".format(case_id)
        )
    for j, variant in enumerate(variants):
        if not isinstance(variant, dict):
            event_log.halt(
                reason="intent_test_matrix_runner_non_object_tolerated_variant",
                case_id=case_id,
                index=j,
            )
            raise NonObjectToleratedVariant(
                "tolerated_variants[{0}] for case {1} must be a dict".format(
                    j, case_id
                )
            )
        # Each variant may carry any subset of EXPECTED_FIELDS keys
        # plus an optional "rationale" string. Unknown keys are rejected.
        allowed_variant_keys = _EXPECTED_FIELD_SET | {"rationale"}
        unknown = set(variant.keys()) - allowed_variant_keys
        if unknown:
            event_log.halt(
                reason="intent_test_matrix_runner_unknown_tolerated_variant_key",
                case_id=case_id,
                index=j,
                unknown=sorted(unknown),
            )
            raise UnknownExpectedKey(
                "tolerated_variants[{0}] for case {1} contains unknown keys: {2}".format(
                    j, case_id, sorted(unknown)
                )
            )
        if "expected_item_kinds_touched" in variant:
            kinds = variant["expected_item_kinds_touched"]
            if not isinstance(kinds, list):
                event_log.halt(
                    reason="intent_test_matrix_runner_non_list_variant_kinds",
                    case_id=case_id,
                    index=j,
                )
                raise NonListExpectedKinds(
                    "tolerated_variants[{0}].expected_item_kinds_touched for case {1} must be a list".format(
                        j, case_id
                    )
                )
            for kind in kinds:
                if kind not in _ALLOWED_KIND_VALUES:
                    event_log.halt(
                        reason="intent_test_matrix_runner_unknown_variant_item_kind",
                        case_id=case_id,
                        index=j,
                        observed=kind,
                    )
                    raise UnknownItemKind(
                        "tolerated variant kind '{0}' for case {1} not in WORKSHOP_ITEM_KINDS".format(
                            kind, case_id
                        )
                    )


def _kinds_equal(observed_kinds, expected_kinds):
    """Order-sensitive list comparison."""
    return list(observed_kinds) == list(expected_kinds)


def _observed_matches_variant(observed_value, variant_value, field):
    """Compare a single field's observed value against a variant value
    with the same order-sensitive discipline as the primary comparison."""
    if field == "expected_item_kinds_touched":
        return _kinds_equal(observed_value, variant_value)
    return observed_value == variant_value


def _compare_field(observed_value, expected_value, field):
    """Compare a single field; order-sensitive by default."""
    if field == "expected_item_kinds_touched":
        return _kinds_equal(observed_value, expected_value)
    return observed_value == expected_value


def _compare_case(observed, expected, tolerated_variants):
    """Compare every expected field against the observed value. Apply
    `tolerated_variants` only to fields that initially differ. Returns
    a dict {field: bool} of per-field match results."""
    field_results = {}
    for field in EXPECTED_FIELDS:
        if field not in expected:
            continue
        obs_value = observed[field]
        exp_value = expected[field]
        primary_match = _compare_field(obs_value, exp_value, field)
        if primary_match:
            field_results[field] = True
            continue
        variant_match = False
        for variant in tolerated_variants:
            if field in variant and _observed_matches_variant(
                obs_value, variant[field], field
            ):
                variant_match = True
                break
        field_results[field] = variant_match
    return field_results


# Bounded tag-based classifier override table. The matrix author may
# tag a case with one of the below tags to force the classifier to
# emit the corresponding failure class on mismatch. This is the
# explicit override channel for synthetic test fixtures and for
# corpus cases whose failure mode the author already understands.
# The override is only consulted on a mismatch; matches always emit
# `match`.
_TAG_CLASSIFIER_OVERRIDES = {
    "force_frame_a_normalization_gap": "frame_a_normalization_gap",
    "force_frame_b_canonical_set_gap": "frame_b_canonical_set_gap",
    "force_frame_b_inflection_gap": "frame_b_inflection_gap",
    "force_frame_b_negation_gap": "frame_b_negation_gap",
    "force_frame_c_synthesis_rule_gap": "frame_c_synthesis_rule_gap",
    "force_frame_c_category_selector_gap": "frame_c_category_selector_gap",
    "force_frame_c_ambiguity_misreport": "frame_c_ambiguity_misreport",
    "force_frame_d_translation_gap": "frame_d_translation_gap",
    "force_out_of_scope_underdetect": "out_of_scope_underdetect",
    "force_fixture_distribution_drift": "fixture_distribution_drift",
    "force_expected_field_drift": "expected_field_drift",
    "force_ambiguity_clarification_gap": "ambiguity_clarification_gap",
    "force_vocabulary_correction_miss": "vocabulary_correction_miss",
}


def _classify_failure(case, observed, expected, field_results):
    """Deterministic table-driven classifier. Returns one of
    `FAILURE_CLASSES` or `"match"`. Reserved classes (`vocabulary_correction_miss`,
    `ambiguity_clarification_gap`) resolve to `"unknown"` because the
    upstream layers that would justify their emission are not yet
    authorized; the matrix author may still tag a case with the
    corresponding `force_*` override but the classifier substitutes
    `"unknown"` before emission."""
    if all(field_results.values()):
        return "match"

    # Tag-based override path. Highest priority; explicit per-case
    # classifier hint provided by the matrix author.
    case_tags = case.get("tags", [])
    for tag in case_tags:
        if tag in _TAG_CLASSIFIER_OVERRIDES:
            classified = _TAG_CLASSIFIER_OVERRIDES[tag]
            if classified in RESERVED_FAILURE_CLASSES:
                return "unknown"
            return classified

    differing = {f for f, ok in field_results.items() if not ok}

    obs_cat = observed["category"]
    exp_cat = expected.get("category")
    obs_amb = observed["ambiguity_observed"]
    exp_amb = expected.get("ambiguity_observed")

    category_diff = "category" in differing
    kinds_diff = "expected_item_kinds_touched" in differing
    ambig_diff = "ambiguity_observed" in differing
    surf_only = differing and not any(
        f in differing
        for f in ("category", "expected_item_kinds_touched", "ambiguity_observed")
    )

    if category_diff and exp_cat == "H. no-route" and obs_cat != "H. no-route":
        return "out_of_scope_underdetect"

    if category_diff and obs_cat == "H. no-route" and exp_cat != "H. no-route":
        return "frame_b_canonical_set_gap"

    if ambig_diff and not (category_diff or kinds_diff):
        return "frame_c_ambiguity_misreport"
    if ambig_diff:
        return "frame_c_ambiguity_misreport"

    if surf_only:
        return "expected_field_drift"

    if category_diff and not kinds_diff:
        return "frame_c_category_selector_gap"
    if kinds_diff and not category_diff:
        return "frame_c_synthesis_rule_gap"
    if category_diff and kinds_diff:
        return "frame_c_synthesis_rule_gap"

    return "unknown"


def _run_case(case, event_log, signal_families=None):
    """Invoke FRAME-D for one case, compare observed vs expected, and
    return a bounded per-case result dict."""
    case_id = case["case_id"]
    prompt_text = case["prompt_text"]
    expected = case["expected"]
    tolerated_variants = case["tolerated_variants"]
    tags = list(case["tags"])
    rationale = case["rationale"]

    case_event_log = EventLog()
    if signal_families is None:
        observed = map_level0_workshop_user_intent(
            prompt_text, case_id, case_event_log
        )
    else:
        observed = map_level0_workshop_user_intent(
            prompt_text, case_id, case_event_log, signal_families=signal_families
        )

    for key in _OBSERVED_GATING_BOOLEANS:
        if observed.get(key) is not False:
            event_log.halt(
                reason="intent_test_matrix_runner_observed_gating_boolean_flipped",
                case_id=case_id,
                gating_key=key,
                observed_value=observed.get(key),
            )
            raise IntentTestMatrixRunnerGatingBooleanFlipped(
                "observed FRAME-D output for case {0} flipped gating boolean '{1}' to {2!r}".format(
                    case_id, key, observed.get(key)
                )
            )

    observed_comparable = {
        "category": observed["workshop_prompt_record"]["category"],
        "expected_item_kinds_touched": list(
            observed["expected_item_kinds_touched"]
        ),
        "ambiguity_observed": observed["ambiguity_observed"],
        "normalized_intent_observation": observed["normalized_intent_observation"],
        "candidate_surface_expected": observed["candidate_surface_expected"],
        "rejection_surface_expected": observed["rejection_surface_expected"],
    }

    field_results = _compare_case(
        observed_comparable, expected, tolerated_variants
    )
    match = all(field_results.values()) if field_results else True
    differing_fields = sorted(
        [f for f, ok in field_results.items() if not ok]
    )
    classified_as = _classify_failure(
        case, observed_comparable, expected, field_results
    ) if not match else "match"

    return {
        "case_id": case_id,
        "match": match,
        "classified_as": classified_as,
        "observed_category": observed_comparable["category"],
        "expected_category": expected.get("category"),
        "observed_kinds": list(observed_comparable["expected_item_kinds_touched"]),
        "expected_kinds": list(
            expected.get("expected_item_kinds_touched", [])
        ),
        "observed_ambiguity": observed_comparable["ambiguity_observed"],
        "expected_ambiguity": expected.get("ambiguity_observed"),
        "observed_normalized_intent": (
            observed_comparable["normalized_intent_observation"]
        ),
        "expected_normalized_intent": expected.get(
            "normalized_intent_observation"
        ),
        "observed_candidate_surface": (
            observed_comparable["candidate_surface_expected"]
        ),
        "expected_candidate_surface": expected.get(
            "candidate_surface_expected"
        ),
        "observed_rejection_surface": (
            observed_comparable["rejection_surface_expected"]
        ),
        "expected_rejection_surface": expected.get(
            "rejection_surface_expected"
        ),
        "differing_fields": differing_fields,
        "tags": tags,
        "rationale": rationale,
    }


def _aggregate_results(case_results):
    """Aggregate per-case results into per-failure-class and per-tag
    counts."""
    per_failure_class = {fc: 0 for fc in FAILURE_CLASSES}
    per_tag = {}
    for cr in case_results:
        if not cr["match"]:
            classified = cr["classified_as"]
            if classified in per_failure_class:
                per_failure_class[classified] += 1
            else:
                per_failure_class["unknown"] += 1
        for tag in cr["tags"]:
            if tag not in per_tag:
                per_tag[tag] = {"passed": 0, "failed": 0}
            if cr["match"]:
                per_tag[tag]["passed"] += 1
            else:
                per_tag[tag]["failed"] += 1
    return per_failure_class, per_tag


def _assert_no_route_status_fields(result, event_log):
    """Defensive: no result key, no case_result key may equal any of
    the bounded forbidden route-status field names."""
    for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
        if field in result:
            event_log.halt(
                reason="intent_test_matrix_runner_route_status_field_present",
                field=field,
            )
            raise IntentTestMatrixRunnerRouteStatusFieldPresent(
                "Route-status field '{0}' present in result".format(field)
            )
    for cr in result["case_results"]:
        for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
            if field in cr:
                event_log.halt(
                    reason="intent_test_matrix_runner_route_status_field_present_in_case_result",
                    field=field,
                    case_id=cr.get("case_id"),
                )
                raise IntentTestMatrixRunnerRouteStatusFieldPresent(
                    "Route-status field '{0}' present in case_result".format(field)
                )
        for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
            if field in cr:
                event_log.halt(
                    reason="intent_test_matrix_runner_forbidden_output_field_name_in_case_result",
                    field=field,
                    case_id=cr.get("case_id"),
                )
                raise IntentTestMatrixRunnerRouteStatusFieldPresent(
                    "Forbidden output field '{0}' present in case_result".format(
                        field
                    )
                )
    for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
        if field in result:
            event_log.halt(
                reason="intent_test_matrix_runner_forbidden_output_field_name",
                field=field,
            )
            raise IntentTestMatrixRunnerRouteStatusFieldPresent(
                "Forbidden output field '{0}' present in result".format(field)
            )


def run_intent_test_matrix(matrix_path, event_log, signal_families=None):
    """Validate the matrix at `matrix_path`, run FRAME-D per case,
    classify mismatches via the bounded fourteen-class failure taxonomy,
    and emit a fixed-shape result dict.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("intent_test_matrix_runner_started")

    matrix = _load_matrix(matrix_path, event_log)
    _validate_matrix_shape(matrix, event_log)
    _assert_no_forbidden_language(
        _module_authored_matrix_strings(matrix),
        event_log,
        location="module_authored_matrix_strings",
    )

    case_results = []
    for case in matrix["cases"]:
        case_result = _run_case(case, event_log, signal_families=signal_families)
        case_results.append(case_result)
        event_log.append(
            "intent_test_matrix_runner_case_observed",
            case_id=case_result["case_id"],
            match=case_result["match"],
            classified_as=case_result["classified_as"],
        )

    passed_count = sum(1 for cr in case_results if cr["match"])
    failed_count = len(case_results) - passed_count
    per_failure_class, per_tag = _aggregate_results(case_results)

    result = {
        "intent_test_matrix_runner_kind": INTENT_TEST_MATRIX_RUNNER_KIND,
        "matrix_id": matrix["matrix_id"],
        "case_count": len(case_results),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "case_results": case_results,
        "per_failure_class_counts": per_failure_class,
        "per_tag_counts": per_tag,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
        "runner_note": _RUNNER_NOTE,
    }

    _assert_no_route_status_fields(result, event_log)
    _assert_no_forbidden_language(
        _module_authored_result_strings(result),
        event_log,
        location="module_authored_result_strings",
    )

    event_log.append(
        "intent_test_matrix_runner_completed",
        case_count=len(case_results),
        passed_count=passed_count,
        failed_count=failed_count,
    )
    return result
