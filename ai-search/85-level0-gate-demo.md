# 85. Level 0 Gate Demo

## Goal

Add the first user-visible surface for the deterministic Level 0 workshop
intent gate. The demo lets a user enter one prompt, see the gate branch, and
record a bounded local audit line.

This packet is product-surface work, not parser hardening.

## Scope

The demo entry point is:

```powershell
python -m harness.level0_workshop_gate_demo "Set up CI for a Python project."
```

It calls `map_level0_workshop_user_intent` and exposes three branches:

- `clear`: display the category and item kinds, then stop.
- `clarify`: display bounded choices and optionally record the user's choice.
- `refuse`: display that the prompt has no supported Level 0 route, then stop.

The demo writes JSON-lines audit records to:

```text
harness/demo_audit_logs/L0-WS-GATE-DEMO-v1.audit.jsonl
```

The audit log is local and append-only. It is not committed by this packet.

## QV2-006 Product Surface

QV2-006 remains the single Mini-V2 admitted failure. The parser currently
routes `Deploy this to staging and notify the team in Slack.` as workflow. The
demo handles that product-surface concern without changing parser code: the
bounded `unresolved_deploy_notify_surface` branch asks the user to choose among
`workflow_file`, `skill`, and `instruction`.

This is intentionally a demo clarification policy, not a parser update.

## Audit Rules

Each audit record includes:

- prompt text
- workshop prompt id
- gate output summary
- branch taken
- clarification choices, if any
- user choice, if any
- literal false booleans proving no downstream action, model invocation,
  autonomous-loop invocation, holdout read, or parser update occurred

Clarification choices are records only. They do not update the parser, admit
corpus data, create routes, or train anything.

## Non-Claims

This packet does not authorize downstream model/action execution, route
creation, source qualification, benchmark claims, holdout measurement, corpus
admission, crawler expansion, overlay storage, confidence decay, parser-core
updates, or autonomous-loop materialization.
