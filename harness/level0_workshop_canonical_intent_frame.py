"""Level 0B workshop CanonicalIntentFrame + ShapeTouchPlan +
WorkshopPromptRecordAdapter (FRAME-C).

WO-L0-WORKSHOP-FRAME-C builds Stage C of the Level 0B Intent Core:
a deterministic frame synthesizer that consumes an already-loaded
FRAME-B SignalEvidenceLedger dict and produces three artifacts
inside one fixed-shape output dict:

1. CanonicalIntentFrame (CIF) - primary_action, secondary_actions,
   target_object, domain, constraints, requested_output_shape,
   source_shape_affinity, ambiguity_level, ambiguity_reasons,
   no_route_reason, near_miss_reason, evidence_band,
   signal_evidence (echoed from FRAME-B, citation-preserving).
2. ShapeTouchPlan - embedded inside the CIF as
   `source_shape_affinity`, a list of `{item_kind,
   affinity_basis: list[signal_id], affinity_grade}` entries with
   categorical `affinity_grade` (`direct` | `indirect` |
   `ambiguous`).
3. WorkshopPromptRecordAdapter - emits `workshop_prompt_record`
   shaped to satisfy the existing workshop derived-trace
   per-record contract: `workshop_prompt_id`, `category` (one of
   the bounded nine workshop categories), `prompt_text`,
   `expected_item_kinds_touched`, `expected_candidate_surface`,
   `expected_rejection_surface`, `boundary_note`.

Pipeline position:

    PromptText
      -> FRAME-A NormalizedPromptView
      -> FRAME-B SignalEvidenceLedger
      -> FRAME-C CanonicalIntentFrame + ShapeTouchPlan       <-- this module
         + WorkshopPromptRecordAdapter

This module does NOT classify a route, does NOT create or select
route objects, does NOT emit any numeric metric output field, does
NOT call any LLM / provider /
external API / embedding / vector / ANN backend / reranker, does
NOT qualify a source, does NOT admit a corpus, and does NOT claim
universal intent understanding, production readiness, completeness,
or benchmark readiness. Those concerns belong to FRAME-D and a
future RK-058 closure packet.

This module performs no file IO, no network call, no URL fetch /
download / crawl / browser automation, no PDF text extraction, no
hash computation, no external process spawning, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools. It uses only the Python standard
library.

This module invokes NO prior-WO public function (verified by
static-scan test). FRAME-A's view-builder and FRAME-B's
extractor appear in tests only as fixture builders.

The Constraints v1 non-claim constraint carries forward: this
module does not claim any synthesized frame field, affinity
entry, evidence-band classification, or workshop-prompt-record
category is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected. The bounded enums,
the bounded mapping rules, and the fixed output key set are
bounded by WO-L0-WORKSHOP-FRAME-C and are NOT claimed exhaustive.

Public surface:

    build_canonical_intent_frame(
        signal_evidence_ledger, workshop_prompt_id, event_log
    ) -> dict
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


FRAME_C_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


FRAME_KIND = "level0_workshop_canonical_intent_frame"


EXPECTED_LEDGER_KIND = "level0_workshop_signal_evidence_ledger"


# Mirrors the FRAME-B clean-pass twenty-two-key shape contract.
# Declared locally so FRAME-B and FRAME-C stay import-isolated
# (FRAME-C does not invoke any FRAME-B public function).
FRAME_B_REQUIRED_KEYS = (
    "signal_evidence_ledger_kind",
    "input_prompt_observed",
    "normalized_prompt_view_kind",
    "signal_evidence",
    "signal_count",
    "action_signal_count",
    "object_signal_count",
    "domain_signal_count",
    "constraint_signal_count",
    "output_shape_signal_count",
    "repo_meta_near_miss_signal_count",
    "out_of_scope_signal_count",
    "negation_signal_count",
    "no_signal_observed",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
    "ledger_note",
)
_FRAME_B_REQUIRED_KEY_SET = frozenset(FRAME_B_REQUIRED_KEYS)


FRAME_B_GATING_BOOLEANS = (
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)


ALLOWED_OUTPUT_KEYS = (
    "intent_frame_kind",
    "input_prompt_observed",
    "source_signal_ledger_kind",
    "workshop_prompt_id",
    "primary_action",
    "secondary_actions",
    "target_object",
    "domain",
    "constraints",
    "requested_output_shape",
    "source_shape_affinity",
    "ambiguity_level",
    "ambiguity_reasons",
    "no_route_reason",
    "near_miss_reason",
    "evidence_band",
    "signal_evidence",
    "workshop_prompt_record",
    "route_created",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "frame_note",
)


EVIDENCE_BANDS = (
    "single_signal",
    "converging_signals",
    "conflicting_signals",
    "no_signal",
)
_EVIDENCE_BAND_SET = frozenset(EVIDENCE_BANDS)


AMBIGUITY_LEVELS = ("none", "low", "high")
_AMBIGUITY_LEVEL_SET = frozenset(AMBIGUITY_LEVELS)


AFFINITY_GRADES = ("direct", "indirect", "ambiguous")
_AFFINITY_GRADE_SET = frozenset(AFFINITY_GRADES)


# Bounded eight workshop item kinds, matching the workshop trace
# contract. `prompt` and `vendor_pattern` are deliberately excluded
# (workshop repo has zero `*.prompt.md` files; vendor-pattern shape
# is absent). Item-kind namespace collision with the requested-
# output-shape enum is avoided by naming that enum value
# `prompt_collection_request`, not `prompt`.
WORKSHOP_ITEM_KINDS = (
    "skill",
    "instruction",
    "agent",
    "workflow_file",
    "hook",
    "plugin",
    "cookbook_entry",
    "repo_meta_section",
)
_WORKSHOP_ITEM_KIND_SET = frozenset(WORKSHOP_ITEM_KINDS)


REQUESTED_OUTPUT_SHAPES = (
    "recipe",
    "configuration_file",
    "prompt_collection_request",
    "none",
)
_REQUESTED_OUTPUT_SHAPE_SET = frozenset(REQUESTED_OUTPUT_SHAPES)


# Bounded mapping from family_id to CIF semantic role. Used by the
# synthesizer. Bounded by WO-L0-WORKSHOP-FRAME-C and NOT claimed
# exhaustive.
_ACTION_TO_PRIMARY = {
    "action.create": "create",
    "action.configure": "configure",
    "action.set_up": "set_up",
    "action.improve": "improve",
    "action.review": "review",
    "action.explain": "explain",
    "action.deploy": "deploy",
}


_OBJECT_TO_TARGET = {
    "object.workflow": "workflow",
    "object.skill": "skill_capability",
    "object.agent": "persona",
    "object.instruction": "instruction_set",
    "object.hook": "hook",
    "object.plugin": "plugin",
    "object.cookbook_entry": "recipe",
    "object.repository": "repository",
    "object.algorithm": "algorithm",
}


_DOMAIN_TO_TAG = {
    "domain.ci": "ci",
    "domain.deployment": "deployment",
    "domain.code_review": "code_review",
    "domain.security": "security",
    "domain.documentation": "docs",
}


_CONSTRAINT_TO_TAG = {
    "constraint.event_triggered": "event_triggered",
    "constraint.on_push": "on_push",
    "constraint.on_pull_request": "on_pull_request",
    "negation.not_requested": "negated_requested",
}


_OUTPUT_SHAPE_TO_TAG = {
    "output_shape.recipe": "recipe",
    "output_shape.configuration_file": "configuration_file",
    "output_shape.prompt_collection_request": "prompt_collection_request",
}


# Shape-touch mapping from CIF synthesis (NOT directly from raw
# prompt) to bounded workshop item kinds. Each entry is a predicate
# function from CIF to (matched, item_kind, affinity_grade,
# basis_signal_kinds). Predicates run in declared order; multiple
# can fire and contribute to ambiguity. The bare-ambiguity rule
# (added by WO-L0-WORKSHOP-FRAME-C-HARDEN-01) short-circuits when
# the signal set is action-only with no informative
# target/domain/output_shape/constraint and emits a bounded
# three-entry ambiguous list; the workflow_file co-fire rule
# (added by WO-L0-WORKSHOP-FRAME-C-HARDEN-01) appends workflow_file
# as a co-occurring candidate when an action.deploy verb is present
# alongside another candidate kind without a workflow domain /
# workflow target / event-triggered constraint already firing the
# primary workflow_file rule.
_SHAPE_TOUCH_RULES_DOC = (
    "bare_ambiguity: action signal present AND no target_object "
    "AND no informative domain AND no requested_output_shape AND "
    "no constraint AND no repo_meta_near_miss AND no out_of_scope "
    "-> emit ambiguous entries for skill / instruction / "
    "workflow_file with affinity_basis from action signals\n"
    "workflow_file: action in (set_up, configure, deploy) AND "
    "(domain ci/deployment OR constraint event_triggered/on_push/"
    "on_pull_request)\n"
    "workflow_file co-fire: primary_action == deploy AND no "
    "workflow domain AND no event-triggered constraint AND no "
    "workflow target AND another candidate kind already fires "
    "-> append workflow_file with affinity_grade 'ambiguous'\n"
    "skill: action in (create, review, improve, explain) AND "
    "target_object in (skill_capability, algorithm, repository) "
    "AND no event-triggered constraint\n"
    "instruction: action == configure AND no event-triggered "
    "constraint AND requested_output_shape != recipe\n"
    "agent: target_object == persona\n"
    "hook: target_object == hook OR (constraint event_triggered "
    "AND not full workflow_file context)\n"
    "plugin: target_object == plugin\n"
    "cookbook_entry: requested_output_shape in (recipe, "
    "prompt_collection_request) OR target_object == recipe\n"
    "repo_meta_section: any near_miss signal fires\n"
    "none: out_of_scope signal fires OR no synthesized action AND "
    "no synthesized target"
)


# Bare-ambiguity emission kinds. Bounded by
# WO-L0-WORKSHOP-FRAME-C-HARDEN-01 and NOT claimed exhaustive.
# Order is stable so the deduped `expected_item_kinds_touched`
# list at the result level is deterministic.
_BARE_AMBIGUITY_KINDS = ("skill", "instruction", "workflow_file")


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


# Workshop prompt categories (bounded nine, mirroring the
# `EXPECTED_PROMPT_CATEGORIES` in `level0_workshop_derived_trace`).
_WORKSHOP_CATEGORY_CLEAR_SINGLE = "A. clear single-intent"
_WORKSHOP_CATEGORY_WORKFLOW = "B. workflow intent"
_WORKSHOP_CATEGORY_SKILL = "C. skill intent"
_WORKSHOP_CATEGORY_AGENT = "D. agent/persona confusion"
_WORKSHOP_CATEGORY_INSTRUCTION = "E. instruction confusion"
_WORKSHOP_CATEGORY_PROMPT_SEARCH = "F. prompt-search-shaped but workflow-intent"
_WORKSHOP_CATEGORY_AMBIGUOUS = "G. ambiguous"
_WORKSHOP_CATEGORY_NO_ROUTE = "H. no-route"
_WORKSHOP_CATEGORY_NEAR_MISS = "I. near-miss/rejection"


WORKSHOP_PROMPT_CATEGORIES = (
    _WORKSHOP_CATEGORY_CLEAR_SINGLE,
    _WORKSHOP_CATEGORY_WORKFLOW,
    _WORKSHOP_CATEGORY_SKILL,
    _WORKSHOP_CATEGORY_AGENT,
    _WORKSHOP_CATEGORY_INSTRUCTION,
    _WORKSHOP_CATEGORY_PROMPT_SEARCH,
    _WORKSHOP_CATEGORY_AMBIGUOUS,
    _WORKSHOP_CATEGORY_NO_ROUTE,
    _WORKSHOP_CATEGORY_NEAR_MISS,
)


WORKSHOP_BOUNDARY_NOTE_LITERAL = (
    "not admitted; not qualified; workshop metadata only"
)


_NO_ROUTE_REASON = "prompt_out_of_repo_scope"
_NEAR_MISS_REASON = "repo_meta_section_near_miss"
_NO_FORCED_SELECTION = "no_forced_selection"


_FRAME_NOTE = (
    "level0_workshop_canonical_intent_frame: a deterministic "
    "scaffold-only synthesis pass over an already-loaded FRAME-B "
    "SignalEvidenceLedger; emits a Canonical Intent Frame, a "
    "Shape Touch Plan (via source_shape_affinity), and a "
    "WorkshopPromptRecord adapter output shaped for the existing "
    "workshop derived-trace contract; this frame is NOT corpus "
    "admission, NOT source qualification, NOT a route object, NOT "
    "a Source Card, NOT permission to flip any authorization / "
    "readiness boolean, and NOT a benchmark-ready flip; RK-058 "
    "remains OPEN; OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, "
    "OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN; "
    "no real adapter; no benchmark execution; no measurement "
    "authorization."
)


class NonDictSignalEvidenceLedger(Exception):
    """Raised when `signal_evidence_ledger` is not a dict."""


class MissingSignalEvidenceLedgerKey(Exception):
    """Raised when the ledger is missing a required key."""


class UnknownSignalEvidenceLedgerKey(Exception):
    """Raised when the ledger contains an unknown key."""


class InvalidSignalEvidenceLedgerKind(Exception):
    """Raised when `signal_evidence_ledger_kind` is not the expected
    literal."""


class FrameBGatingBooleanFlipped(Exception):
    """Raised when any FRAME-B gating boolean is not literal False."""


class InvalidSignalEvidenceShape(Exception):
    """Raised when `signal_evidence` is not a list or any record has
    the wrong shape."""


class InvalidWorkshopPromptId(Exception):
    """Raised when `workshop_prompt_id` is not a non-empty string."""


class FrameCRouteStatusFieldPresent(Exception):
    """Raised when any output record carries a forbidden route-status
    field."""


class ForbiddenLanguageInLevel0WorkshopCanonicalIntentFrame(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in module-authored ledger
    metadata or frame strings. User-authored prompt text and
    observed spans remain evidence, not project claims."""


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


def _assert_no_forbidden_language_strings(strings, event_log, location):
    """Halt and raise if any forbidden phrase appears in strings."""
    for text in strings:
        lowered = text.lower()
        for phrase in FRAME_C_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_canonical_intent_frame_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopCanonicalIntentFrame(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_canonical_intent_frame_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopCanonicalIntentFrame(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _module_authored_signal_strings(record):
    for key in (
        "signal_id", "signal_family", "family_kind",
        "normalized_value", "source_view", "language_alias_tag",
        "edit_budget_tag",
    ):
        value = record.get(key)
        if isinstance(value, str):
            yield value
    for value in record.get("contributes_to", []):
        if isinstance(value, str):
            yield value


def _module_authored_ledger_strings(ledger):
    for key in (
        "signal_evidence_ledger_kind", "normalized_prompt_view_kind",
        "ledger_note",
    ):
        value = ledger.get(key)
        if isinstance(value, str):
            yield value
    for record in ledger.get("signal_evidence", []):
        if isinstance(record, dict):
            for value in _module_authored_signal_strings(record):
                yield value


def _module_authored_workshop_record_strings(record):
    for key, value in record.items():
        if key == "prompt_text":
            continue
        for text in _walk_strings(value):
            yield text


def _module_authored_result_strings(result):
    for key, value in result.items():
        if key == "input_prompt_observed":
            continue
        if key == "signal_evidence":
            for record in value:
                if isinstance(record, dict):
                    for text in _module_authored_signal_strings(record):
                        yield text
            continue
        if key == "workshop_prompt_record":
            for text in _module_authored_workshop_record_strings(value):
                yield text
            continue
        for text in _walk_strings(value):
            yield text


_REQUIRED_SIGNAL_FIELDS = (
    "signal_id",
    "signal_family",
    "family_kind",
    "observed_span",
    "span_start",
    "span_end",
    "normalized_value",
    "source_view",
    "language_alias_tag",
    "edit_budget_tag",
    "contributes_to",
)


def _validate_signal_evidence_ledger(ledger, event_log):
    """Validate the FRAME-B ledger dict shape; halt-before-raise on
    every failure path."""
    if not isinstance(ledger, dict):
        event_log.halt(
            reason="level0_workshop_canonical_intent_frame_non_dict_ledger",
        )
        raise NonDictSignalEvidenceLedger(
            "signal_evidence_ledger must be a dict"
        )

    observed_keys = set(ledger.keys())
    missing = _FRAME_B_REQUIRED_KEY_SET - observed_keys
    if missing:
        event_log.halt(
            reason="level0_workshop_canonical_intent_frame_missing_ledger_key",
            missing=sorted(missing),
        )
        raise MissingSignalEvidenceLedgerKey(
            "signal_evidence_ledger missing required keys: {0}".format(
                sorted(missing)
            )
        )
    unknown = observed_keys - _FRAME_B_REQUIRED_KEY_SET
    if unknown:
        event_log.halt(
            reason="level0_workshop_canonical_intent_frame_unknown_ledger_key",
            unknown=sorted(unknown),
        )
        raise UnknownSignalEvidenceLedgerKey(
            "signal_evidence_ledger contains unknown keys: {0}".format(
                sorted(unknown)
            )
        )

    if ledger["signal_evidence_ledger_kind"] != EXPECTED_LEDGER_KIND:
        event_log.halt(
            reason="level0_workshop_canonical_intent_frame_invalid_ledger_kind",
            observed=ledger["signal_evidence_ledger_kind"],
        )
        raise InvalidSignalEvidenceLedgerKind(
            "signal_evidence_ledger_kind must be '{0}'".format(
                EXPECTED_LEDGER_KIND
            )
        )

    for key in FRAME_B_GATING_BOOLEANS:
        if ledger[key] is not False:
            event_log.halt(
                reason="level0_workshop_canonical_intent_frame_frame_b_gating_boolean_flipped",
                key=key,
            )
            raise FrameBGatingBooleanFlipped(
                "signal_evidence_ledger[{0!r}] must be literal False".format(
                    key
                )
            )

    if not isinstance(ledger["signal_evidence"], list):
        event_log.halt(
            reason="level0_workshop_canonical_intent_frame_non_list_signal_evidence",
        )
        raise InvalidSignalEvidenceShape(
            "signal_evidence must be a list"
        )

    required = frozenset(_REQUIRED_SIGNAL_FIELDS)
    for i, rec in enumerate(ledger["signal_evidence"]):
        if not isinstance(rec, dict):
            event_log.halt(
                reason="level0_workshop_canonical_intent_frame_non_dict_signal_record",
                index=i,
            )
            raise InvalidSignalEvidenceShape(
                "signal_evidence[{0}] must be a dict".format(i)
            )
        observed = set(rec.keys())
        if observed != required:
            event_log.halt(
                reason="level0_workshop_canonical_intent_frame_invalid_signal_record_fields",
                index=i,
                observed=sorted(observed),
                required=sorted(required),
            )
            raise InvalidSignalEvidenceShape(
                "signal_evidence[{0}] field set mismatch".format(i)
            )


def _validate_workshop_prompt_id(workshop_prompt_id, event_log):
    if not isinstance(workshop_prompt_id, str) or len(workshop_prompt_id) == 0:
        event_log.halt(
            reason="level0_workshop_canonical_intent_frame_invalid_workshop_prompt_id",
        )
        raise InvalidWorkshopPromptId(
            "workshop_prompt_id must be a non-empty string"
        )


def _partition_signals(signals):
    """Group signals by family_kind."""
    by_kind = {
        "action": [],
        "object": [],
        "domain": [],
        "constraint": [],
        "output_shape": [],
        "repo_meta_near_miss": [],
        "out_of_scope": [],
        "negation": [],
    }
    for sig in signals:
        by_kind.setdefault(sig["family_kind"], []).append(sig)
    return by_kind


def _select_primary_action(action_signals):
    """Choose primary_action from action signals. Primary is the
    first action signal (ledger order is signal_id order); secondary
    actions are the distinct remainder."""
    if not action_signals:
        return None, []
    primary_family = action_signals[0]["signal_family"]
    primary = _ACTION_TO_PRIMARY.get(primary_family)
    secondary_seen = []
    for sig in action_signals[1:]:
        mapped = _ACTION_TO_PRIMARY.get(sig["signal_family"])
        if mapped is None:
            continue
        if mapped == primary:
            continue
        if mapped not in secondary_seen:
            secondary_seen.append(mapped)
    return primary, secondary_seen


def _select_target_object(object_signals):
    """Choose target_object from object signals. First object wins;
    multiple distinct objects mark the frame as ambiguous (handled by
    the synthesizer)."""
    if not object_signals:
        return None, []
    distinct_targets = []
    for sig in object_signals:
        mapped = _OBJECT_TO_TARGET.get(sig["signal_family"])
        if mapped is None:
            continue
        if mapped not in distinct_targets:
            distinct_targets.append(mapped)
    primary = distinct_targets[0] if distinct_targets else None
    return primary, distinct_targets


def _collect_domain_tags(domain_signals):
    tags = []
    for sig in domain_signals:
        mapped = _DOMAIN_TO_TAG.get(sig["signal_family"])
        if mapped is not None and mapped not in tags:
            tags.append(mapped)
    return tags


def _collect_constraint_tags(constraint_signals, negation_signals):
    tags = []
    for sig in constraint_signals:
        mapped = _CONSTRAINT_TO_TAG.get(sig["signal_family"])
        if mapped is not None and mapped not in tags:
            tags.append(mapped)
    for sig in negation_signals:
        mapped = _CONSTRAINT_TO_TAG.get(sig["signal_family"])
        if mapped is not None and mapped not in tags:
            tags.append(mapped)
    return tags


def _select_requested_output_shape(output_shape_signals):
    if not output_shape_signals:
        return None
    first = output_shape_signals[0]["signal_family"]
    return _OUTPUT_SHAPE_TO_TAG.get(first)


def _is_bare_ambiguity_signal_set(
    by_kind, distinct_target_objects, domain_tags,
    requested_output_shape, constraint_tags,
):
    """Bare-ambiguity rule (WO-L0-WORKSHOP-FRAME-C-HARDEN-01,
    closing RK-059 gap 3): the FRAME-B ledger contains at least
    one action signal but no informative target_object, no
    informative domain, no requested_output_shape, no constraint
    or negation signal, no repo_meta_near_miss, and no
    out_of_scope. This pattern matches free-text bare-ambiguity
    inputs like 'make this better', 'fix this', 'improve the
    code', or 'make it work' which the FRAME-B `action.create` /
    `action.improve` families partially capture (one action
    signal, no other informative signals).

    The rule is FRAME-C-internal: it consumes only the FRAME-B
    ledger that the FRAME-C public function already accepts and
    does NOT re-scan the raw prompt text. Inputs that FRAME-B
    cannot extract any action signal from (for example
    'help with my project', which contains no FRAME-B canonical
    or alias term) still classify as H. no-route via the
    no-signal path; that residual coverage limitation is a
    FRAME-B coverage concern, not a FRAME-C synthesis concern.
    """
    if not by_kind.get("action"):
        return False
    if distinct_target_objects:
        return False
    if domain_tags:
        return False
    if requested_output_shape is not None:
        return False
    if constraint_tags:
        return False
    if by_kind.get("repo_meta_near_miss"):
        return False
    if by_kind.get("out_of_scope"):
        return False
    return True


def _compute_shape_touch_plan(
    primary_action, distinct_target_objects, domain_tags,
    constraint_tags, requested_output_shape, by_kind,
    bare_ambiguity=False,
):
    """Apply the bounded shape-touch rules and return a list of
    `{item_kind, affinity_basis, affinity_grade}` entries. Multiple
    matches yield ambiguity."""
    affinity = []
    has_event_constraint = any(
        c in ("event_triggered", "on_push", "on_pull_request")
        for c in constraint_tags
    )
    has_repo_meta = bool(by_kind.get("repo_meta_near_miss"))
    has_out_of_scope = bool(by_kind.get("out_of_scope"))

    def _ids_for(*family_kinds):
        ids = []
        for fk in family_kinds:
            for sig in by_kind.get(fk, []):
                ids.append(sig["signal_id"])
        return ids

    # repo_meta_near_miss is rejection-only; cleanly precedes other
    # candidate decisions.
    if has_repo_meta:
        affinity.append({
            "item_kind": "repo_meta_section",
            "affinity_basis": _ids_for("repo_meta_near_miss"),
            "affinity_grade": "direct",
        })

    # out_of_scope is no-route; cleanly precedes any candidate kind.
    if has_out_of_scope:
        affinity.append({
            "item_kind": "none",
            "affinity_basis": _ids_for("out_of_scope"),
            "affinity_grade": "direct",
        })

    # If repo-meta or out-of-scope fired, do NOT add candidate kinds.
    if has_repo_meta or has_out_of_scope:
        return affinity

    # Bare-ambiguity short-circuit (closes RK-059 gap 3). When the
    # signal set is action-only with no informative target / domain /
    # output_shape / constraint, emit a bounded three-entry
    # ambiguous list so the result is G with multiple plausible
    # kinds rather than H no-route.
    if bare_ambiguity:
        action_basis = _ids_for("action")
        for kind in _BARE_AMBIGUITY_KINDS:
            affinity.append({
                "item_kind": kind,
                "affinity_basis": list(action_basis),
                "affinity_grade": "ambiguous",
            })
        return affinity

    workflow_actions = {"set_up", "configure", "deploy"}
    skill_actions = {"create", "review", "improve", "explain"}
    workflow_domains = {"ci", "deployment"}

    def _is_workflow_intent():
        if primary_action in workflow_actions and (
            any(d in workflow_domains for d in domain_tags)
            or has_event_constraint
        ):
            return True
        if "workflow" in distinct_target_objects:
            return True
        return False

    def _is_skill_intent():
        if primary_action not in skill_actions:
            return False
        if has_event_constraint:
            return False
        if not distinct_target_objects:
            # action-only with no object can still suggest skill if
            # domain is code_review or security
            return any(d in ("code_review", "security") for d in domain_tags)
        return any(
            t in ("skill_capability", "algorithm", "repository")
            for t in distinct_target_objects
        )

    def _is_instruction_intent():
        if has_event_constraint:
            return False
        if requested_output_shape == "recipe":
            return False
        if "instruction_set" in distinct_target_objects:
            return True
        if primary_action == "configure" and not _is_workflow_intent():
            return True
        return False

    def _is_agent_intent():
        return "persona" in distinct_target_objects

    def _is_hook_intent():
        if "hook" in distinct_target_objects:
            return True
        if has_event_constraint and not _is_workflow_intent():
            return True
        return False

    def _is_plugin_intent():
        return "plugin" in distinct_target_objects

    def _is_cookbook_intent():
        # WO-L0-WORKSHOP-FRAME-C-HARDEN-01 closes RK-059 gap 2 by
        # treating `prompt_collection_request` as a cookbook-shaped
        # request (in addition to the original `recipe` shape).
        # A prompt that asks for a prompt example is shape-touching
        # the cookbook surface; combined with a deploy verb, the
        # downstream workflow_file co-fire then raises ambiguity
        # to surface category F (prompt-search-shaped but
        # workflow-intent).
        if requested_output_shape in ("recipe", "prompt_collection_request"):
            return True
        if "recipe" in distinct_target_objects:
            return True
        return False

    def _grade_for(direct_condition, contributing_kinds):
        # `direct` if exactly one contributing family kind drives the
        # match; `indirect` if multiple contributing kinds; the
        # `ambiguous` value is reserved for entries that are pulled
        # in only by ambiguity-resolution (not implemented here as a
        # separate path - multiple shape candidates surface as
        # ambiguity at the CIF level, not as an `ambiguous` grade
        # per entry).
        if len(contributing_kinds) <= 1:
            return "direct"
        return "indirect"

    candidate_entries = []
    if _is_workflow_intent():
        contributing = []
        if primary_action in workflow_actions:
            contributing.append("action")
        if any(d in workflow_domains for d in domain_tags):
            contributing.append("domain")
        if has_event_constraint:
            contributing.append("constraint")
        if "workflow" in distinct_target_objects:
            contributing.append("object")
        candidate_entries.append({
            "item_kind": "workflow_file",
            "affinity_basis": _ids_for(
                *[k for k in (
                    "action", "domain", "constraint", "object"
                ) if k in contributing]
            ),
            "affinity_grade": _grade_for(True, contributing),
        })
    if _is_skill_intent():
        contributing = ["action"]
        if distinct_target_objects:
            contributing.append("object")
        if any(d in ("code_review", "security") for d in domain_tags):
            contributing.append("domain")
        candidate_entries.append({
            "item_kind": "skill",
            "affinity_basis": _ids_for(*contributing),
            "affinity_grade": _grade_for(True, contributing),
        })
    if _is_instruction_intent():
        contributing = []
        if "instruction_set" in distinct_target_objects:
            contributing.append("object")
        if primary_action == "configure":
            contributing.append("action")
        candidate_entries.append({
            "item_kind": "instruction",
            "affinity_basis": _ids_for(*contributing),
            "affinity_grade": _grade_for(True, contributing),
        })
    if _is_agent_intent():
        candidate_entries.append({
            "item_kind": "agent",
            "affinity_basis": _ids_for("object"),
            "affinity_grade": "direct",
        })
    if _is_hook_intent():
        contributing = []
        if "hook" in distinct_target_objects:
            contributing.append("object")
        if has_event_constraint:
            contributing.append("constraint")
        candidate_entries.append({
            "item_kind": "hook",
            "affinity_basis": _ids_for(*contributing),
            "affinity_grade": _grade_for(True, contributing),
        })
    if _is_plugin_intent():
        candidate_entries.append({
            "item_kind": "plugin",
            "affinity_basis": _ids_for("object"),
            "affinity_grade": "direct",
        })
    if _is_cookbook_intent():
        contributing = []
        if requested_output_shape in (
            "recipe", "prompt_collection_request"
        ):
            contributing.append("output_shape")
        if "recipe" in distinct_target_objects:
            contributing.append("object")
        candidate_entries.append({
            "item_kind": "cookbook_entry",
            "affinity_basis": _ids_for(*contributing),
            "affinity_grade": _grade_for(True, contributing),
        })

    # workflow_file co-fire rule (WO-L0-WORKSHOP-FRAME-C-HARDEN-01
    # closing RK-059 gaps 1 and 2). When `action.deploy` is present
    # (`primary_action == "deploy"`, which covers the deploy /
    # publish / release / ship / dagit / yayinla family aliases)
    # and the primary `_is_workflow_intent` rule did NOT fire (no
    # workflow domain, no event-triggered constraint, no
    # `workflow` target), but at least one non-workflow candidate
    # kind already fires, append `workflow_file` as an ambiguous
    # co-fire so the downstream ambiguity classification surfaces
    # the workflow/non-workflow tension and the category selector
    # can return D (agent + workflow) or F (cookbook + workflow)
    # rather than collapsing to a clear single-intent.
    if (
        primary_action == "deploy"
        and not any(d in workflow_domains for d in domain_tags)
        and not has_event_constraint
        and "workflow" not in distinct_target_objects
        and candidate_entries
        and not any(
            e["item_kind"] == "workflow_file" for e in candidate_entries
        )
    ):
        candidate_entries.append({
            "item_kind": "workflow_file",
            "affinity_basis": _ids_for("action"),
            "affinity_grade": "ambiguous",
        })

    # If multiple candidate item kinds fire, downgrade each entry's
    # grade to `ambiguous` to surface multi-shape ambiguity at the
    # entry level.
    if len(candidate_entries) >= 2:
        for entry in candidate_entries:
            entry["affinity_grade"] = "ambiguous"

    affinity.extend(candidate_entries)

    if not affinity:
        affinity.append({
            "item_kind": "none",
            "affinity_basis": [],
            "affinity_grade": "direct",
        })

    return affinity


def _classify_evidence_band(by_kind, total_count):
    if total_count == 0:
        return "no_signal"
    informative_kinds = sum(
        1 for k in ("action", "object", "domain", "constraint",
                    "output_shape", "repo_meta_near_miss",
                    "out_of_scope")
        if by_kind.get(k)
    )
    has_repo_meta = bool(by_kind.get("repo_meta_near_miss"))
    has_out_of_scope = bool(by_kind.get("out_of_scope"))
    has_candidate_kinds = any(
        by_kind.get(k) for k in (
            "action", "object", "domain", "constraint", "output_shape"
        )
    )
    if (has_repo_meta or has_out_of_scope) and has_candidate_kinds:
        return "conflicting_signals"
    if informative_kinds == 1:
        return "single_signal"
    return "converging_signals"


def _classify_ambiguity(distinct_target_objects, candidate_count,
                        has_repo_meta, has_out_of_scope,
                        has_candidate_kinds, bare_ambiguity=False):
    reasons = []
    # bare_ambiguity (WO-L0-WORKSHOP-FRAME-C-HARDEN-01 closing
    # RK-059 gap 3) is the action-only signal pattern and is
    # surfaced as a high-ambiguity reason so the category selector
    # short-circuits to G regardless of which kinds the
    # bare-ambiguity shape-touch entries populate.
    if bare_ambiguity:
        reasons.append("bare_ambiguity_action_only")
    if has_repo_meta and has_candidate_kinds:
        reasons.append("repo_meta_collides_with_candidate")
    if has_out_of_scope and has_candidate_kinds:
        reasons.append("out_of_scope_collides_with_candidate")
    if len(distinct_target_objects) >= 2:
        reasons.append("multiple_target_objects")
    if candidate_count >= 2:
        reasons.append("multiple_candidate_item_kinds")

    if reasons:
        return "high", reasons
    if len(distinct_target_objects) == 1 and candidate_count == 1:
        return "none", []
    if candidate_count == 0 and not has_repo_meta and not has_out_of_scope:
        return "none", []
    return "low", reasons


def _select_workshop_category(
    candidate_kinds, has_repo_meta, has_out_of_scope, ambiguity_level,
    requested_output_shape, by_kind, bare_ambiguity=False,
):
    """Map CIF -> bounded workshop category. Returns one of the
    nine bounded workshop categories."""
    if has_out_of_scope:
        return _WORKSHOP_CATEGORY_NO_ROUTE
    if has_repo_meta:
        return _WORKSHOP_CATEGORY_NEAR_MISS
    # bare_ambiguity (WO-L0-WORKSHOP-FRAME-C-HARDEN-01 closing
    # RK-059 gap 3) deterministically resolves to G regardless of
    # which kinds the bare-ambiguity shape-touch entries populate.
    # This is required because the bare-ambiguity entries include
    # `instruction` and `workflow_file` which would otherwise
    # trigger the instruction+workflow special-case category E.
    if bare_ambiguity:
        return _WORKSHOP_CATEGORY_AMBIGUOUS
    candidate_set = set(candidate_kinds)
    if ambiguity_level == "high" and len(candidate_set) >= 2:
        # Prompt-search-shaped + workflow-intent is a specific
        # category; agent + workflow combination is a separate
        # category; instruction + workflow is a separate category.
        if "cookbook_entry" in candidate_set and "workflow_file" in candidate_set:
            return _WORKSHOP_CATEGORY_PROMPT_SEARCH
        if "agent" in candidate_set and "workflow_file" in candidate_set:
            return _WORKSHOP_CATEGORY_AGENT
        if "instruction" in candidate_set and "workflow_file" in candidate_set:
            return _WORKSHOP_CATEGORY_INSTRUCTION
        return _WORKSHOP_CATEGORY_AMBIGUOUS
    if candidate_set == {"workflow_file"} or candidate_set == {"workflow_file", "hook"}:
        return _WORKSHOP_CATEGORY_WORKFLOW
    if candidate_set == {"skill"}:
        return _WORKSHOP_CATEGORY_SKILL
    if candidate_set == {"agent"}:
        return _WORKSHOP_CATEGORY_CLEAR_SINGLE
    if candidate_set == {"instruction"}:
        return _WORKSHOP_CATEGORY_CLEAR_SINGLE
    if candidate_set == {"plugin"}:
        return _WORKSHOP_CATEGORY_CLEAR_SINGLE
    if candidate_set == {"cookbook_entry"}:
        return _WORKSHOP_CATEGORY_CLEAR_SINGLE
    if len(candidate_set) >= 2:
        return _WORKSHOP_CATEGORY_AMBIGUOUS
    # No candidates and no rejection -> no-route fallback.
    return _WORKSHOP_CATEGORY_NO_ROUTE


def _build_workshop_prompt_record(
    workshop_prompt_id, prompt_text, category,
    expected_item_kinds_touched, has_repo_meta, has_out_of_scope,
    ambiguity_observed,
):
    if has_out_of_scope:
        candidate_surface = "no candidate surface expected"
        rejection_surface = _NO_ROUTE_REASON
    elif has_repo_meta:
        candidate_surface = "no candidate surface expected"
        rejection_surface = _NEAR_MISS_REASON
    elif ambiguity_observed:
        candidate_surface = "multiple candidate surfaces expected"
        rejection_surface = _NO_FORCED_SELECTION
    else:
        candidate_surface = "candidate fragment of declared shape"
        rejection_surface = _NO_FORCED_SELECTION

    return {
        "workshop_prompt_id": workshop_prompt_id,
        "category": category,
        "prompt_text": prompt_text,
        "expected_item_kinds_touched": list(expected_item_kinds_touched),
        "expected_candidate_surface": candidate_surface,
        "expected_rejection_surface": rejection_surface,
        "boundary_note": WORKSHOP_BOUNDARY_NOTE_LITERAL,
    }


def _assert_no_route_status_fields(result, event_log):
    """Defensive: no result key, signal record key, or affinity entry
    key may be in the bounded forbidden route-status field list."""
    def _check_dict(d, location):
        if not isinstance(d, dict):
            return
        for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
            if field in d:
                event_log.halt(
                    reason="level0_workshop_canonical_intent_frame_route_status_field_present",
                    location=location,
                    field=field,
                )
                raise FrameCRouteStatusFieldPresent(
                    "Route-status field '{0}' present in {1}".format(
                        field, location
                    )
                )

    _check_dict(result, "result")
    _check_dict(result.get("workshop_prompt_record"), "workshop_prompt_record")
    for entry in result.get("source_shape_affinity", []):
        _check_dict(entry, "source_shape_affinity")
    for rec in result.get("signal_evidence", []):
        _check_dict(rec, "signal_evidence")


def build_canonical_intent_frame(
    signal_evidence_ledger, workshop_prompt_id, event_log,
):
    """Validate the FRAME-B ledger, synthesize a Canonical Intent
    Frame, compute a Shape Touch Plan, and emit a workshop prompt
    record adapter output.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_workshop_canonical_intent_frame_started")

    _validate_workshop_prompt_id(workshop_prompt_id, event_log)
    _validate_signal_evidence_ledger(signal_evidence_ledger, event_log)
    _assert_no_forbidden_language_strings(
        _module_authored_ledger_strings(signal_evidence_ledger),
        event_log,
        location="signal_evidence_ledger",
    )

    signals = signal_evidence_ledger["signal_evidence"]
    by_kind = _partition_signals(signals)

    primary_action, secondary_actions = _select_primary_action(
        by_kind["action"]
    )
    target_object, distinct_target_objects = _select_target_object(
        by_kind["object"]
    )
    domain_tags = _collect_domain_tags(by_kind["domain"])
    constraint_tags = _collect_constraint_tags(
        by_kind["constraint"], by_kind["negation"]
    )
    requested_output_shape = _select_requested_output_shape(
        by_kind["output_shape"]
    )

    bare_ambiguity = _is_bare_ambiguity_signal_set(
        by_kind, distinct_target_objects, domain_tags,
        requested_output_shape, constraint_tags,
    )

    affinity = _compute_shape_touch_plan(
        primary_action, distinct_target_objects, domain_tags,
        constraint_tags, requested_output_shape, by_kind,
        bare_ambiguity=bare_ambiguity,
    )

    candidate_kinds = [
        entry["item_kind"] for entry in affinity
        if entry["item_kind"] not in ("none", "repo_meta_section")
    ]
    has_repo_meta = any(
        entry["item_kind"] == "repo_meta_section" for entry in affinity
    )
    has_out_of_scope = any(
        entry["item_kind"] == "none" and entry["affinity_basis"] for entry in affinity
    )
    has_candidate_kinds = len(candidate_kinds) > 0

    ambiguity_level, ambiguity_reasons = _classify_ambiguity(
        distinct_target_objects, len(set(candidate_kinds)),
        has_repo_meta, has_out_of_scope, has_candidate_kinds,
        bare_ambiguity=bare_ambiguity,
    )

    evidence_band = _classify_evidence_band(by_kind, len(signals))

    no_route_reason = None
    near_miss_reason = None
    if has_out_of_scope:
        no_route_reason = _NO_ROUTE_REASON
    if has_repo_meta:
        near_miss_reason = _NEAR_MISS_REASON
    if not has_repo_meta and not has_out_of_scope and len(signals) == 0:
        no_route_reason = _NO_ROUTE_REASON

    ambiguity_observed = (ambiguity_level == "high")
    category = _select_workshop_category(
        candidate_kinds, has_repo_meta, has_out_of_scope,
        ambiguity_level, requested_output_shape, by_kind,
        bare_ambiguity=bare_ambiguity,
    )

    if has_out_of_scope or (
        not has_repo_meta and not has_candidate_kinds
    ):
        expected_item_kinds_touched = ["none"]
    elif has_repo_meta:
        expected_item_kinds_touched = ["repo_meta_section"]
    else:
        # Deduplicate while preserving order.
        seen = set()
        expected_item_kinds_touched = []
        for k in candidate_kinds:
            if k not in seen:
                expected_item_kinds_touched.append(k)
                seen.add(k)

    prompt_text = signal_evidence_ledger["input_prompt_observed"]

    workshop_prompt_record = _build_workshop_prompt_record(
        workshop_prompt_id, prompt_text, category,
        expected_item_kinds_touched, has_repo_meta, has_out_of_scope,
        ambiguity_observed,
    )

    result = {
        "intent_frame_kind": FRAME_KIND,
        "input_prompt_observed": prompt_text,
        "source_signal_ledger_kind": (
            signal_evidence_ledger["signal_evidence_ledger_kind"]
        ),
        "workshop_prompt_id": workshop_prompt_id,
        "primary_action": primary_action,
        "secondary_actions": secondary_actions,
        "target_object": target_object,
        "domain": domain_tags,
        "constraints": constraint_tags,
        "requested_output_shape": requested_output_shape,
        "source_shape_affinity": affinity,
        "ambiguity_level": ambiguity_level,
        "ambiguity_reasons": ambiguity_reasons,
        "no_route_reason": no_route_reason,
        "near_miss_reason": near_miss_reason,
        "evidence_band": evidence_band,
        "signal_evidence": signals,
        "workshop_prompt_record": workshop_prompt_record,
        "route_created": False,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "frame_note": _FRAME_NOTE,
    }

    _assert_no_route_status_fields(result, event_log)
    _assert_no_forbidden_language_strings(
        _module_authored_result_strings(result), event_log, location="result"
    )

    event_log.append(
        "level0_workshop_canonical_intent_frame_passed",
        category=category,
        ambiguity_level=ambiguity_level,
        evidence_band=evidence_band,
    )
    return result
