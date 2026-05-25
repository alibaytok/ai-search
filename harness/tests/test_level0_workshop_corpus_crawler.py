"""Tests for local-only Level 0 raw candidate crawling."""

import json
import os
import tempfile
import unittest

from harness import level0_workshop_corpus_crawler as crawler


def _write_temp_ascii(suffix, content):
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="L0WS_CRAWLER_TEST_")
    with os.fdopen(fd, "w", encoding="ascii") as handle:
        handle.write(content)
    return path


class Level0WorkshopCorpusCrawlerTest(unittest.TestCase):
    def test_extracts_markdown_and_matrix_candidates(self):
        markdown_path = _write_temp_ascii(
            ".md",
            "\n".join(
                [
                    "# Local prompts",
                    "| id | prompt |",
                    "| 1 | Build a workflow for issue triage. |",
                    "| 2 | Build a workflow for issue triage. |",
                    "- ordinary prose, not a prompt",
                    "Explain the docs release process.",
                ]
            ),
        )
        matrix_path = _write_temp_ascii(
            ".intent.matrix.json",
            json.dumps(
                {
                    "cases": [
                        {"case_id": "A", "prompt_text": "Create an agent."},
                        {"case_id": "B", "prompt_text": "Run repo setup."},
                    ]
                },
                ensure_ascii=True,
            ),
        )
        try:
            report = crawler.crawl_level0_raw_candidates(
                [markdown_path, matrix_path]
            )
        finally:
            os.remove(markdown_path)
            os.remove(matrix_path)

        self.assertEqual(tuple(report), crawler.RAW_CANDIDATE_REPORT_FIELDS)
        self.assertEqual(report["candidate_count"], 4)
        self.assertEqual(
            [item["candidate_id"] for item in report["candidates"]],
            ["RC-00001", "RC-00002", "RC-00003", "RC-00004"],
        )
        self.assertEqual(
            [item["prompt_text_normalized"] for item in report["candidates"]],
            [
                "Build a workflow for issue triage.",
                "Explain the docs release process.",
                "Create an agent.",
                "Run repo setup.",
            ],
        )

    def test_candidate_metadata_is_bounded_and_raw_only(self):
        path = _write_temp_ascii(".md", "Write an instruction for release notes.\n")
        try:
            report = crawler.crawl_level0_raw_candidates([path])
        finally:
            os.remove(path)

        self.assertFalse(report["corpus_admission_authorized"])
        self.assertFalse(report["expected_fields_generated"])
        self.assertFalse(report["parser_invocation_performed"])
        self.assertFalse(report["network_access_performed"])
        candidate = report["candidates"][0]
        self.assertEqual(tuple(candidate), crawler.RAW_CANDIDATE_FIELDS)
        self.assertEqual(candidate["admission_status"], "raw")
        self.assertEqual(candidate["admission_reason"], "pending_human_review")
        self.assertNotIn("expected", candidate)
        self.assertRegex(candidate["source_sha256"], r"^[0-9a-f]{64}$")

    def test_rejects_non_local_or_missing_sources(self):
        with self.assertRaises(crawler.CorpusCrawlerMalformedSource):
            crawler.crawl_level0_raw_candidates(["https://example.com/prompts.md"])
        with self.assertRaises(crawler.CorpusCrawlerMalformedSource):
            crawler.crawl_level0_raw_candidates(["missing-local-prompts.md"])

    def test_rejects_non_ascii_sources(self):
        fd, path = tempfile.mkstemp(suffix=".md", prefix="L0WS_CRAWLER_TEST_")
        with os.fdopen(fd, "wb") as handle:
            handle.write("Create a Turkce ajan icin ozet.".encode("utf-8"))
            handle.write(b" \xc3\xbc")
        try:
            with self.assertRaises(UnicodeDecodeError):
                crawler.crawl_level0_raw_candidates([path])
        finally:
            os.remove(path)

    def test_raw_candidate_cap_is_enforced(self):
        lines = [
            "Create workflow candidate {0}.".format(index)
            for index in range(crawler.MAX_RAW_CANDIDATES + 1)
        ]
        path = _write_temp_ascii(".md", "\n".join(lines))
        try:
            with self.assertRaises(crawler.CorpusCrawlerTooManyCandidates):
                crawler.crawl_level0_raw_candidates([path])
        finally:
            os.remove(path)

    def test_repeated_runs_are_deterministic(self):
        path = _write_temp_ascii(
            ".md",
            "Build a workflow for triage.\nExplain the docs workflow.\n",
        )
        try:
            first = crawler.crawl_level0_raw_candidates([path])
            second = crawler.crawl_level0_raw_candidates([path])
        finally:
            os.remove(path)
        self.assertEqual(first, second)

    def test_default_sources_are_local_and_existing(self):
        for path in crawler.DEFAULT_LOCAL_SOURCE_PATHS:
            self.assertNotIn("://", path)
            self.assertTrue(os.path.exists(path), path)

    def test_static_scan_has_no_parser_or_process_imports(self):
        path = os.path.join("harness", "level0_workshop_corpus_crawler.py")
        with open(path, "r", encoding="ascii") as handle:
            source = handle.read()
        forbidden = (
            "import subprocess",
            "from subprocess",
            "import socket",
            "from socket",
            "import urllib",
            "from urllib",
            "import http",
            "from http",
            "import requests",
            "from requests",
            "os.environ",
            "run_intent_test_matrix",
            "level0_workshop_signal_evidence",
            "level0_workshop_canonical_intent_frame",
            "level0_workshop_user_intent_mapper",
            "level0_workshop_normalized_prompt_view",
        )
        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
