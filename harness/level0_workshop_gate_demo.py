"""CLI demo for the Level 0 workshop intent gate.

The demo exposes the existing FRAME-D mapper as a user-visible gate
surface. It does not call a model, create routes, run the autonomous loop,
or update parser behavior. It maps one prompt, prints the branch taken,
and appends a bounded audit record.
"""

import argparse
import datetime
import json
import os
import sys

from harness.event_log import EventLog
from harness.level0_workshop_user_intent_mapper import (
    map_level0_workshop_user_intent,
)


DEMO_KIND = "level0_workshop_gate_demo_v1"
AUDIT_RECORD_KIND = "level0_workshop_gate_demo_audit_record_v1"
DEFAULT_WORKSHOP_PROMPT_ID = "W-DEMO-001"
DEFAULT_AUDIT_LOG_PATH = os.path.join(
    "harness", "demo_audit_logs", "L0-WS-GATE-DEMO-v1.audit.jsonl"
)

BRANCH_CLEAR = "clear"
BRANCH_CLARIFY = "clarify"
BRANCH_REFUSE = "refuse"

REFUSAL_CATEGORIES = ("H. no-route", "I. near-miss/rejection")
SUPPORTED_CHOICES = (
    "workflow_file",
    "skill",
    "agent",
    "instruction",
    "cookbook_entry",
    "plugin",
    "hook",
)
CHOICE_ALIASES = {
    "w": "workflow_file",
    "workflow": "workflow_file",
    "workflow_file": "workflow_file",
    "s": "skill",
    "skill": "skill",
    "a": "agent",
    "agent": "agent",
    "persona": "agent",
    "i": "instruction",
    "instruction": "instruction",
    "instructions": "instruction",
    "c": "cookbook_entry",
    "cookbook": "cookbook_entry",
    "cookbook_entry": "cookbook_entry",
    "p": "plugin",
    "plugin": "plugin",
    "h": "hook",
    "hook": "hook",
}

GATE_OUTPUT_SUMMARY_FIELDS = (
    "category",
    "normalized_intent_observation",
    "expected_item_kinds_touched",
    "candidate_surface_expected",
    "rejection_surface_expected",
    "ambiguity_observed",
)
AUDIT_RECORD_FIELDS = (
    "audit_record_kind",
    "demo_kind",
    "timestamp_iso",
    "prompt_text",
    "workshop_prompt_id",
    "gate_output_summary",
    "branch_taken",
    "clarification_reason",
    "clarification_choices",
    "user_choice_if_any",
    "downstream_action_performed",
    "model_invocation_performed",
    "autonomous_loop_invoked",
    "holdout_read",
    "parser_update_performed",
    "audit_note",
)


class InvalidDemoChoice(Exception):
    """Raised when a clarification choice is not one of the offered kinds."""


class GateDemoShapeDrift(Exception):
    """Raised when a demo record drifts from the bounded schema."""


def _utc_timestamp_iso():
    return (
        datetime.datetime.now(datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _gate_output_summary(mapper_output):
    summary = {
        "category": mapper_output["workshop_prompt_record"]["category"],
        "normalized_intent_observation": (
            mapper_output["normalized_intent_observation"]
        ),
        "expected_item_kinds_touched": list(
            mapper_output["expected_item_kinds_touched"]
        ),
        "candidate_surface_expected": (
            mapper_output["candidate_surface_expected"]
        ),
        "rejection_surface_expected": (
            mapper_output["rejection_surface_expected"]
        ),
        "ambiguity_observed": mapper_output["ambiguity_observed"],
    }
    if tuple(summary) != GATE_OUTPUT_SUMMARY_FIELDS:
        raise GateDemoShapeDrift("gate output summary fields drifted")
    return summary


def _is_unresolved_deploy_notify(prompt_text, mapper_output):
    """Bounded product-surface clarification for the QV2-006 shape."""
    summary = _gate_output_summary(mapper_output)
    text = prompt_text.lower()
    return (
        summary["category"] == "B. workflow intent"
        and "deploy this" in text
        and "notify" in text
    )


def _clarification_choices(prompt_text, mapper_output):
    summary = _gate_output_summary(mapper_output)
    if summary["category"] in REFUSAL_CATEGORIES:
        return (), None
    if summary["ambiguity_observed"] or summary["category"] == "G. ambiguous":
        choices = tuple(
            kind for kind in summary["expected_item_kinds_touched"]
            if kind in SUPPORTED_CHOICES
        )
        return choices, "gate_reported_ambiguity"
    if _is_unresolved_deploy_notify(prompt_text, mapper_output):
        return (
            "workflow_file",
            "skill",
            "instruction",
        ), "unresolved_deploy_notify_surface"
    return (), None


def _branch_for(prompt_text, mapper_output):
    summary = _gate_output_summary(mapper_output)
    if summary["category"] in REFUSAL_CATEGORIES:
        return BRANCH_REFUSE
    choices, _ = _clarification_choices(prompt_text, mapper_output)
    if choices:
        return BRANCH_CLARIFY
    return BRANCH_CLEAR


def _normalize_choice(user_choice, offered_choices):
    if user_choice is None:
        return None
    normalized = CHOICE_ALIASES.get(user_choice.strip().lower())
    if normalized not in offered_choices:
        raise InvalidDemoChoice("choice is not available for this prompt")
    return normalized


def build_gate_demo_record(
    prompt_text,
    user_choice=None,
    timestamp_iso=None,
    workshop_prompt_id=DEFAULT_WORKSHOP_PROMPT_ID,
):
    """Map one prompt and build a bounded audit record."""
    mapper_output = map_level0_workshop_user_intent(
        prompt_text, workshop_prompt_id, EventLog()
    )
    summary = _gate_output_summary(mapper_output)
    choices, clarification_reason = _clarification_choices(
        prompt_text, mapper_output
    )
    branch = _branch_for(prompt_text, mapper_output)
    chosen = _normalize_choice(user_choice, choices)
    record = {
        "audit_record_kind": AUDIT_RECORD_KIND,
        "demo_kind": DEMO_KIND,
        "timestamp_iso": timestamp_iso or _utc_timestamp_iso(),
        "prompt_text": prompt_text,
        "workshop_prompt_id": workshop_prompt_id,
        "gate_output_summary": summary,
        "branch_taken": branch,
        "clarification_reason": clarification_reason,
        "clarification_choices": list(choices),
        "user_choice_if_any": chosen,
        "downstream_action_performed": False,
        "model_invocation_performed": False,
        "autonomous_loop_invoked": False,
        "holdout_read": False,
        "parser_update_performed": False,
        "audit_note": (
            "demo audit record only; user choices are not admission data "
            "and do not update parser behavior"
        ),
    }
    if tuple(record) != AUDIT_RECORD_FIELDS:
        raise GateDemoShapeDrift("audit record fields drifted")
    return record


def append_audit_record(record, audit_log_path=DEFAULT_AUDIT_LOG_PATH):
    """Append one JSON-lines audit record."""
    parent = os.path.dirname(audit_log_path)
    if parent and not os.path.isdir(parent):
        os.makedirs(parent)
    with open(audit_log_path, "a", encoding="ascii") as handle:
        json.dump(record, handle, ensure_ascii=True, separators=(",", ":"))
        handle.write("\n")


def format_gate_demo_output(record):
    """Return human-readable demo output lines."""
    summary = record["gate_output_summary"]
    lines = [
        "Level 0 gate demo",
        "Branch: {0}".format(record["branch_taken"]),
        "Category: {0}".format(summary["category"]),
        "Item kinds: {0}".format(", ".join(
            summary["expected_item_kinds_touched"]
        )),
    ]
    if record["branch_taken"] == BRANCH_CLARIFY:
        lines.append("Clarification: Did you mean one of these?")
        lines.append("Choices: {0}".format(", ".join(
            record["clarification_choices"]
        )))
        if record["user_choice_if_any"] is not None:
            lines.append("Chosen kind: {0}".format(
                record["user_choice_if_any"]
            ))
    elif record["branch_taken"] == BRANCH_REFUSE:
        lines.append("Refusal: no supported Level 0 route for this prompt.")
    else:
        lines.append("Gate preview: {0}".format(
            summary["normalized_intent_observation"]
        ))
    return lines


def run_gate_demo(
    prompt_text,
    user_choice=None,
    audit_log_path=DEFAULT_AUDIT_LOG_PATH,
    timestamp_iso=None,
):
    """Run the demo and append its audit record."""
    record = build_gate_demo_record(
        prompt_text,
        user_choice=user_choice,
        timestamp_iso=timestamp_iso,
    )
    append_audit_record(record, audit_log_path=audit_log_path)
    return record


def main(argv=None, input_fn=input, output_stream=None):
    parser = argparse.ArgumentParser(
        description="Run the Level 0 workshop intent gate demo."
    )
    parser.add_argument("prompt", nargs="?", help="Prompt text to map.")
    parser.add_argument("--choice", help="Clarification choice, if needed.")
    parser.add_argument(
        "--audit-log",
        default=DEFAULT_AUDIT_LOG_PATH,
        help="JSON-lines audit log path.",
    )
    args = parser.parse_args(argv)
    output_stream = output_stream or sys.stdout
    prompt_text = args.prompt if args.prompt is not None else sys.stdin.read()
    prompt_text = prompt_text.strip()
    choice = args.choice
    preview = build_gate_demo_record(prompt_text, user_choice=choice)
    if preview["branch_taken"] == BRANCH_CLARIFY and choice is None:
        output_stream.write("Choices: {0}\n".format(", ".join(
            preview["clarification_choices"]
        )))
        choice = input_fn("Did you mean? ")
    record = run_gate_demo(
        prompt_text,
        user_choice=choice,
        audit_log_path=args.audit_log,
    )
    for line in format_gate_demo_output(record):
        output_stream.write(line + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
