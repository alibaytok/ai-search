"""Deterministic Level 0B workshop user-intent mapper.

This scaffold fills the upstream gap before
`level0_workshop_derived_trace`: it maps a single free-text user prompt
to a bounded workshop prompt-record shape. It does not inspect source
content, does not query an index, does not retrieve, rank, qualify,
admit, or select anything.
"""

from harness.level0_workshop_derived_trace import WORKSHOP_BOUNDARY_NOTE


_MAPPER_KIND = "level0_workshop_user_intent_mapper"

_OUTPUT_KEYS = (
    "intent_mapper_kind",
    "workshop_prompt_record",
    "normalized_intent_observation",
    "expected_item_kinds_touched",
    "candidate_surface_expected",
    "rejection_surface_expected",
    "ambiguity_observed",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "mapper_note",
)

_NO_ROUTE_TERMS = (
    "world war",
    "wwii",
    "water boil",
    "boiling point",
    "capital of",
    "weather",
    "stock price",
)

_REPO_META_TERMS = (
    "readme",
    "contributing",
    "license",
    "badge",
    "navigation",
    "repo meta",
    "repository meta",
    "docs section",
)

_WORKFLOW_TERMS = (
    "workflow",
    "is akisi",
    "ci",
    "pipeline",
    "deploy",
    "deployment",
    "dagit",
    "yayinla",
    "staging",
    "build",
    "kur",
    "github pages",
    "docker",
    "release",
    "automation",
)

_HOOK_TERMS = (
    "hook",
    "pre-commit",
    "precommit",
    "on push",
    "trigger",
    "webhook",
)

_SKILL_TERMS = (
    "skill",
    "beceri",
    "code review",
    "kod inceleme",
    "review skill",
    "test skill",
    "refactor skill",
)

_AGENT_TERMS = (
    "agent",
    "ajan",
    "persona",
    "act as",
    "reviewer persona",
)

_INSTRUCTION_TERMS = (
    "instruction",
    "instructions",
    "talimat",
    "yonerge",
    "guideline",
    "guidelines",
    "coding standard",
    "rules",
    "convention",
)

_PLUGIN_TERMS = (
    "plugin",
    "eklenti",
    "integration",
    "tool integration",
)

_COOKBOOK_TERMS = (
    "prompt",
    "recipe",
    "example",
    "ornek",
    "how to",
    "nasil",
)

_AMBIGUOUS_TERMS = (
    "make this better",
    "bunu daha iyi yap",
    "yardim et",
    "help with my project",
    "improve the code",
    "kodu iyilestir",
    "fix this",
    "make it work",
)


class NonStringUserPrompt(Exception):
    """Raised when the user prompt is not a string."""


class EmptyUserPrompt(Exception):
    """Raised when the user prompt is empty after trimming."""


class InvalidWorkshopPromptId(Exception):
    """Raised when the workshop prompt id is not a non-empty string."""


def _halt(event_log, reason, message):
    event_log.halt(reason=reason, message=message)


def _contains_any(text, terms):
    return any(term in text for term in terms)


def _dedupe(items):
    result = []
    for item in items:
        if item not in result:
            result.append(item)
    return result


def _classify_prompt(prompt_text):
    lowered = prompt_text.strip().lower()

    if _contains_any(lowered, _NO_ROUTE_TERMS):
        return (
            "H. no-route",
            ["none"],
            "no_route",
            "no candidate surface expected",
            "prompt_out_of_repo_scope",
            False,
        )

    if _contains_any(lowered, _REPO_META_TERMS):
        return (
            "I. near-miss/rejection",
            ["repo_meta_section"],
            "near_miss_rejection",
            "no candidate surface expected",
            "repo_meta_section_near_miss",
            False,
        )

    if _contains_any(lowered, _AMBIGUOUS_TERMS):
        return (
            "G. ambiguous",
            ["skill", "instruction", "workflow_file"],
            "ambiguous_user_intent",
            "multiple candidate surfaces expected",
            "no forced selection",
            True,
        )

    kinds = []
    if _contains_any(lowered, _SKILL_TERMS):
        kinds.append("skill")
    if _contains_any(lowered, _INSTRUCTION_TERMS):
        kinds.append("instruction")
    if _contains_any(lowered, _AGENT_TERMS):
        kinds.append("agent")
    if _contains_any(lowered, _WORKFLOW_TERMS):
        kinds.append("workflow_file")
    if _contains_any(lowered, _HOOK_TERMS):
        kinds.append("hook")
    if _contains_any(lowered, _PLUGIN_TERMS):
        kinds.append("plugin")
    if _contains_any(lowered, _COOKBOOK_TERMS):
        kinds.append("cookbook_entry")

    kinds = _dedupe(kinds)

    if "cookbook_entry" in kinds and "workflow_file" in kinds:
        return (
            "F. prompt-search-shaped but workflow-intent",
            ["cookbook_entry", "workflow_file"],
            "prompt_surface_workflow_intent",
            "candidate route and workflow surfaces expected",
            "no forced selection",
            False,
        )

    if "agent" in kinds and "workflow_file" in kinds:
        return (
            "D. agent/persona confusion",
            ["agent", "workflow_file"],
            "agent_surface_workflow_intent",
            "candidate route and workflow surfaces expected",
            "no forced selection",
            False,
        )

    if "instruction" in kinds and "workflow_file" in kinds:
        return (
            "E. instruction confusion",
            ["instruction", "workflow_file"],
            "instruction_surface_workflow_intent",
            "candidate route and workflow surfaces expected",
            "no forced selection",
            False,
        )

    if len(kinds) > 1:
        return (
            "G. ambiguous",
            kinds,
            "ambiguous_user_intent",
            "multiple candidate surfaces expected",
            "no forced selection",
            True,
        )

    if kinds == ["workflow_file"] or kinds == ["hook"]:
        return (
            "B. workflow intent",
            kinds,
            "workflow_intent",
            "candidate workflow surface expected",
            "no forced selection",
            False,
        )

    if kinds == ["skill"]:
        return (
            "C. skill intent",
            kinds,
            "skill_intent",
            "candidate route surface expected",
            "no forced selection",
            False,
        )

    if kinds:
        return (
            "A. clear single-intent",
            kinds,
            "clear_single_intent",
            "candidate route surface expected",
            "no forced selection",
            False,
        )

    return (
        "H. no-route",
        ["none"],
        "no_route",
        "no candidate surface expected",
        "prompt_out_of_repo_scope",
        False,
    )


def map_level0_workshop_user_intent(input_prompt, workshop_prompt_id, event_log):
    """Map one free-text prompt to a workshop prompt record.

    The mapping is intentionally deterministic and bounded. It is a
    scaffold-visible user-intent layer, not semantic retrieval.
    """
    event_log.append(
        "level0_workshop_user_intent_mapper_started",
        intent_mapper_kind=_MAPPER_KIND,
    )

    if not isinstance(input_prompt, str):
        _halt(
            event_log,
            "level0_workshop_user_intent_mapper_non_string_prompt",
            "input_prompt must be a string",
        )
        raise NonStringUserPrompt("input_prompt must be a string")

    stripped = input_prompt.strip()
    if not stripped:
        _halt(
            event_log,
            "level0_workshop_user_intent_mapper_empty_prompt",
            "input_prompt must be non-empty",
        )
        raise EmptyUserPrompt("input_prompt must be non-empty")

    if not isinstance(workshop_prompt_id, str) or not workshop_prompt_id.strip():
        _halt(
            event_log,
            "level0_workshop_user_intent_mapper_invalid_prompt_id",
            "workshop_prompt_id must be a non-empty string",
        )
        raise InvalidWorkshopPromptId(
            "workshop_prompt_id must be a non-empty string"
        )

    (
        category,
        touched_kinds,
        normalized_intent,
        candidate_surface,
        rejection_surface,
        ambiguity_observed,
    ) = _classify_prompt(stripped)

    prompt_record = {
        "workshop_prompt_id": workshop_prompt_id,
        "category": category,
        "prompt_text": stripped,
        "expected_item_kinds_touched": list(touched_kinds),
        "expected_candidate_surface": candidate_surface,
        "expected_rejection_surface": rejection_surface,
        "boundary_note": WORKSHOP_BOUNDARY_NOTE,
    }

    output = {
        "intent_mapper_kind": _MAPPER_KIND,
        "workshop_prompt_record": prompt_record,
        "normalized_intent_observation": normalized_intent,
        "expected_item_kinds_touched": list(touched_kinds),
        "candidate_surface_expected": candidate_surface,
        "rejection_surface_expected": rejection_surface,
        "ambiguity_observed": ambiguity_observed,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "mapper_note": (
            "deterministic Level 0B workshop user-intent mapping only; "
            "candidate fragments remain downstream observations and no "
            "route selection is authorized"
        ),
    }

    event_log.append(
        "level0_workshop_user_intent_mapper_completed",
        category=category,
        normalized_intent_observation=normalized_intent,
        expected_item_kinds_touched=list(touched_kinds),
    )

    if set(output.keys()) != set(_OUTPUT_KEYS):
        raise AssertionError("mapper output shape drift")

    return output
