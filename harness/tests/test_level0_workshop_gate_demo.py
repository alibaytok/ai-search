"""Tests for the Level 0 workshop gate demo."""

import io
import json
import os
import tempfile
import unittest

from harness import level0_workshop_gate_demo as demo


FIXED_TS = "2026-05-26T00:00:00Z"
HOLDOUT_NAME = "L0-WS-PARSER-QUALITY-MINI-V2-HOLDOUT.intent.matrix.json"


def _temp_log_path():
    root = os.path.join(os.getcwd(), "harness", "demo_audit_logs")
    os.makedirs(root, exist_ok=True)
    tmp = tempfile.NamedTemporaryFile(
        prefix="test-demo-", suffix=".jsonl", dir=root, delete=False
    )
    tmp.close()
    os.unlink(tmp.name)
    return tmp.name


class Level0WorkshopGateDemoTest(unittest.TestCase):

    def tearDown(self):
        root = os.path.join(os.getcwd(), "harness", "demo_audit_logs")
        if os.path.isdir(root):
            for name in os.listdir(root):
                if name.startswith("test-demo-"):
                    os.unlink(os.path.join(root, name))

    def test_clear_branch_records_route_preview_without_action(self):
        path = _temp_log_path()
        record = demo.run_gate_demo(
            "Set up CI for a Python project.",
            audit_log_path=path,
            timestamp_iso=FIXED_TS,
        )
        self.assertEqual(record["branch_taken"], demo.BRANCH_CLEAR)
        self.assertEqual(
            record["gate_output_summary"]["expected_item_kinds_touched"],
            ["workflow_file"],
        )
        self.assertFalse(record["downstream_action_performed"])
        self.assertFalse(record["model_invocation_performed"])
        lines = demo.format_gate_demo_output(record)
        self.assertIn("Branch: clear", lines)

    def test_gate_reported_ambiguity_prompts_for_clarification(self):
        path = _temp_log_path()
        record = demo.run_gate_demo(
            "Make this better.",
            user_choice="skill",
            audit_log_path=path,
            timestamp_iso=FIXED_TS,
        )
        self.assertEqual(record["branch_taken"], demo.BRANCH_CLARIFY)
        self.assertEqual(record["clarification_reason"], "gate_reported_ambiguity")
        self.assertEqual(record["user_choice_if_any"], "skill")
        self.assertIn("skill", record["clarification_choices"])
        self.assertFalse(record["parser_update_performed"])

    def test_unresolved_deploy_notify_uses_product_clarification(self):
        record = demo.build_gate_demo_record(
            "Deploy this to staging and notify the team in Slack.",
            user_choice="workflow",
            timestamp_iso=FIXED_TS,
        )
        self.assertEqual(record["branch_taken"], demo.BRANCH_CLARIFY)
        self.assertEqual(
            record["clarification_reason"],
            "unresolved_deploy_notify_surface",
        )
        self.assertEqual(
            record["clarification_choices"],
            ["workflow_file", "skill", "instruction"],
        )
        self.assertEqual(record["user_choice_if_any"], "workflow_file")

    def test_refusal_branch_records_no_route_without_action(self):
        record = demo.build_gate_demo_record(
            "What year did World War II end?",
            timestamp_iso=FIXED_TS,
        )
        self.assertEqual(record["branch_taken"], demo.BRANCH_REFUSE)
        self.assertEqual(
            record["gate_output_summary"]["category"], "H. no-route"
        )
        self.assertFalse(record["downstream_action_performed"])
        self.assertFalse(record["holdout_read"])

    def test_invalid_choice_raises_without_audit_write(self):
        path = _temp_log_path()
        with self.assertRaises(demo.InvalidDemoChoice):
            demo.run_gate_demo(
                "Make this better.",
                user_choice="plugin",
                audit_log_path=path,
                timestamp_iso=FIXED_TS,
            )
        self.assertFalse(os.path.exists(path))

    def test_audit_log_appends_bounded_json_records(self):
        path = _temp_log_path()
        first = demo.run_gate_demo(
            "Set up CI for a Python project.",
            audit_log_path=path,
            timestamp_iso=FIXED_TS,
        )
        second = demo.run_gate_demo(
            "What year did World War II end?",
            audit_log_path=path,
            timestamp_iso=FIXED_TS,
        )
        with open(path, "r", encoding="ascii") as handle:
            lines = handle.readlines()
        self.assertEqual(len(lines), 2)
        loaded = [json.loads(line) for line in lines]
        self.assertEqual(loaded[0], first)
        self.assertEqual(loaded[1], second)
        for record in loaded:
            self.assertEqual(tuple(record), demo.AUDIT_RECORD_FIELDS)
            self.assertEqual(
                tuple(record["gate_output_summary"]),
                demo.GATE_OUTPUT_SUMMARY_FIELDS,
            )

    def test_idempotent_gate_output_summary(self):
        summaries = []
        for _ in range(10):
            record = demo.build_gate_demo_record(
                "Deploy this to staging and notify the team in Slack.",
                timestamp_iso=FIXED_TS,
            )
            summaries.append(record["gate_output_summary"])
        self.assertEqual(summaries, [summaries[0]] * 10)

    def test_cli_prompts_for_clarification_and_writes_audit(self):
        path = _temp_log_path()
        output = io.StringIO()
        exit_code = demo.main(
            [
                "Deploy this to staging and notify the team in Slack.",
                "--audit-log",
                path,
            ],
            input_fn=lambda _: "instruction",
            output_stream=output,
        )
        self.assertEqual(exit_code, 0)
        self.assertIn("Branch: clarify", output.getvalue())
        self.assertIn("Chosen kind: instruction", output.getvalue())
        with open(path, "r", encoding="ascii") as handle:
            record = json.loads(handle.readline())
        self.assertEqual(record["user_choice_if_any"], "instruction")

    def test_demo_module_static_boundaries(self):
        with open(
            os.path.join("harness", "level0_workshop_gate_demo.py"),
            "r",
            encoding="ascii",
        ) as handle:
            source = handle.read()
        forbidden = (
            "level0_workshop_parser_quality_loop",
            "level0_workshop_mini_v2_autonomous_run",
            "level0_workshop_matrix_delta_autonomy",
            "level0_workshop_frame_b_overlay_autonomy",
            "level0_workshop_composite_patch_autonomy",
            "materialize_accepted",
            HOLDOUT_NAME,
            "import subprocess",
            "from subprocess",
            "import socket",
            "from socket",
            "import urllib",
            "from urllib",
            "import requests",
            "from requests",
            "os.environ",
        )
        for token in forbidden:
            self.assertNotIn(token, source)

    def test_demo_audit_log_not_referenced_by_autonomous_paths(self):
        audit_name = os.path.basename(demo.DEFAULT_AUDIT_LOG_PATH)
        scanned_paths = [
            os.path.join("harness", "level0_workshop_mini_v2_autonomous_run.py"),
            os.path.join("harness", "level0_workshop_matrix_delta_autonomy.py"),
            os.path.join("harness", "level0_workshop_frame_b_overlay_autonomy.py"),
            os.path.join("harness", "level0_workshop_composite_patch_autonomy.py"),
            os.path.join("harness", "level0_workshop_parser_quality_loop.py"),
        ]
        for path in scanned_paths:
            with open(path, "r", encoding="ascii") as handle:
                self.assertNotIn(audit_name, handle.read())

    def test_demo_source_and_records_are_ascii(self):
        with open(
            os.path.join("harness", "level0_workshop_gate_demo.py"),
            "rb",
        ) as handle:
            handle.read().decode("ascii")
        record = demo.build_gate_demo_record(
            "Make this better.",
            user_choice="skill",
            timestamp_iso=FIXED_TS,
        )
        json.dumps(record, ensure_ascii=True).encode("ascii")


if __name__ == "__main__":
    unittest.main()
