"""Tests for `harness.level0_workshop_normalized_prompt_view`.

Tests construct synthetic in-memory free-text prompts (ASCII and
Turkish/non-ASCII), invoke the view-builder, and verify the
emitted view dict's shape, raw/trimmed/casefolded/ascii-folded
fields, deterministic tokenization with spans, halt-before-raise
on malformed input, fixed-False gating booleans, absence of
forbidden route-status fields, input immutability, and
static-scan absence of forbidden tokens / prior-WO public
function names.

These tests do not read any planning document at runtime. They do
not perform file IO, network calls, URL fetches, PDF reads, or
hash computation outside reading the module-under-test source for
the static-scan checks.
"""

import os
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_normalized_prompt_view import (
    ALLOWED_OUTPUT_KEYS,
    EmptyInputPrompt,
    InputPromptExceedsMaxLength,
    MAX_PROMPT_LENGTH,
    NORMALIZATION_STEPS,
    NonStringInputPrompt,
    WhitespaceOnlyInputPrompt,
    build_level0_workshop_normalized_prompt_view,
)


_ROUTE_STATUS_FIELDS = (
    "official", "is_route", "is_official_route", "selected_as_official",
    "official_route_authorized", "route_authorized", "production_route",
    "selected_route", "executable", "route_state", "plane",
)


class CleanAsciiPromptTest(unittest.TestCase):

    def setUp(self):
        self.event_log = EventLog()
        self.result = build_level0_workshop_normalized_prompt_view(
            "Set up a CI workflow for a Python project.", self.event_log
        )

    def test_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_view_kind_literal(self):
        self.assertEqual(
            self.result["normalized_prompt_view_kind"],
            "level0_workshop_normalized_prompt_view",
        )

    def test_raw_text_preserved(self):
        self.assertEqual(
            self.result["raw_text"],
            "Set up a CI workflow for a Python project.",
        )

    def test_trimmed_text_equals_raw_when_no_outer_whitespace(self):
        self.assertEqual(self.result["trimmed_text"], self.result["raw_text"])

    def test_casefolded_text_lowercased(self):
        self.assertEqual(
            self.result["casefolded_text"],
            "set up a ci workflow for a python project.",
        )

    def test_ascii_folded_text_ascii_clean(self):
        text = self.result["ascii_folded_text"]
        self.assertTrue(all(ord(c) < 128 for c in text))

    def test_tokens_split_on_whitespace(self):
        self.assertEqual(
            self.result["tokens"],
            ["Set", "up", "a", "CI", "workflow", "for", "a",
             "Python", "project."],
        )

    def test_token_count_matches_tokens(self):
        self.assertEqual(
            self.result["token_count"], len(self.result["tokens"])
        )

    def test_token_spans_match_trimmed_text(self):
        for token, span in zip(self.result["tokens"],
                                self.result["token_spans"]):
            start, end = span
            self.assertEqual(self.result["trimmed_text"][start:end], token)

    def test_max_prompt_length_literal(self):
        self.assertEqual(self.result["max_prompt_length"], MAX_PROMPT_LENGTH)

    def test_normalization_steps_match_constant(self):
        self.assertEqual(
            self.result["normalization_steps"], list(NORMALIZATION_STEPS)
        )

    def test_selection_made_literal_false(self):
        self.assertIs(self.result["selection_made"], False)

    def test_measurement_authorized_literal_false(self):
        self.assertIs(self.result["measurement_authorized"], False)

    def test_real_benchmark_authorized_literal_false(self):
        self.assertIs(self.result["real_benchmark_authorized"], False)

    def test_real_benchmark_ready_literal_false(self):
        self.assertIs(self.result["real_benchmark_ready"], False)

    def test_source_qualification_authorized_literal_false(self):
        self.assertIs(self.result["source_qualification_authorized"], False)

    def test_corpus_admission_authorized_literal_false(self):
        self.assertIs(self.result["corpus_admission_authorized"], False)

    def test_route_created_literal_false(self):
        self.assertIs(self.result["route_created"], False)

    def test_view_note_non_empty(self):
        self.assertIsInstance(self.result["view_note"], str)
        self.assertGreater(len(self.result["view_note"]), 0)

    def test_started_and_completed_events_emitted(self):
        types = [event["type"] for event in self.event_log.events]
        self.assertIn(
            "level0_workshop_normalized_prompt_view_started", types
        )
        self.assertIn(
            "level0_workshop_normalized_prompt_view_completed", types
        )

    def test_no_halt_event(self):
        self.assertFalse(self.event_log.has_halt())

    def test_no_route_status_field_in_result(self):
        for field in _ROUTE_STATUS_FIELDS:
            self.assertNotIn(field, self.result)


class TurkishPromptTest(unittest.TestCase):

    def test_turkish_prompt_accepted_and_raw_preserved(self):
        # Turkish: "Bir is akisi kur."  with a dotted-I and accented chars
        prompt = "Bir \u0130\u015f Ak\u0131\u015f\u0131 kur."
        result = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        self.assertEqual(result["raw_text"], prompt)

    def test_turkish_prompt_ascii_folded_is_ascii_clean(self):
        prompt = "Bir \u0130\u015f Ak\u0131\u015f\u0131 kur."
        result = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        ascii_text = result["ascii_folded_text"]
        self.assertTrue(all(ord(c) < 128 for c in ascii_text))

    def test_turkish_prompt_ascii_fold_deterministic(self):
        prompt = "Bir \u0130\u015f Ak\u0131\u015f\u0131 kur."
        r1 = build_level0_workshop_normalized_prompt_view(prompt, EventLog())
        r2 = build_level0_workshop_normalized_prompt_view(prompt, EventLog())
        self.assertEqual(r1["ascii_folded_text"], r2["ascii_folded_text"])

    def test_turkish_dotless_i_preserved_as_ascii_i(self):
        prompt = "Bir \u0130\u015f Ak\u0131\u015f\u0131 kur."
        result = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        self.assertEqual(result["ascii_folded_text"], "bir is akisi kur.")

    def test_turkish_prompt_token_count_positive(self):
        prompt = "Bir \u0130\u015f Ak\u0131\u015f\u0131 kur."
        result = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        self.assertGreater(result["token_count"], 0)

    def test_turkish_casefold_lowercases_dotted_capital_I(self):
        # U+0130 (Turkish capital I with dot) casefolds via the Unicode
        # Default Case Folding rules; the result is locale-independent.
        prompt = "\u0130stanbul"
        result = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        # Must not contain U+0130 after casefolding
        self.assertNotIn("\u0130", result["casefolded_text"])


class TrimmingAndWhitespaceTest(unittest.TestCase):

    def test_outer_whitespace_stripped(self):
        result = build_level0_workshop_normalized_prompt_view(
            "   hello world   ", EventLog()
        )
        self.assertEqual(result["trimmed_text"], "hello world")
        self.assertEqual(result["raw_text"], "   hello world   ")

    def test_inner_multiple_spaces_do_not_create_empty_tokens(self):
        result = build_level0_workshop_normalized_prompt_view(
            "a   b\tc\nd", EventLog()
        )
        self.assertEqual(result["tokens"], ["a", "b", "c", "d"])
        self.assertNotIn("", result["tokens"])

    def test_single_token_prompt_yields_one_token_one_span(self):
        result = build_level0_workshop_normalized_prompt_view(
            "deploy", EventLog()
        )
        self.assertEqual(result["tokens"], ["deploy"])
        self.assertEqual(result["token_spans"], [[0, len("deploy")]])

    def test_punctuation_kept_attached_to_token(self):
        result = build_level0_workshop_normalized_prompt_view(
            "deploy this, please.", EventLog()
        )
        self.assertEqual(result["tokens"], ["deploy", "this,", "please."])


class TokenSpanTest(unittest.TestCase):

    def test_every_span_points_into_trimmed_text(self):
        result = build_level0_workshop_normalized_prompt_view(
            "  alpha  beta  gamma  ", EventLog()
        )
        trimmed = result["trimmed_text"]
        for token, span in zip(result["tokens"], result["token_spans"]):
            start, end = span
            self.assertEqual(trimmed[start:end], token)

    def test_spans_are_non_overlapping_and_ordered(self):
        result = build_level0_workshop_normalized_prompt_view(
            "one two three four", EventLog()
        )
        prev_end = -1
        for span in result["token_spans"]:
            start, end = span
            self.assertGreaterEqual(start, prev_end)
            self.assertLess(start, end)
            prev_end = end

    def test_spans_length_matches_tokens_length(self):
        result = build_level0_workshop_normalized_prompt_view(
            "alpha beta gamma", EventLog()
        )
        self.assertEqual(len(result["token_spans"]), len(result["tokens"]))


class MaxLengthBoundaryTest(unittest.TestCase):

    def test_prompt_at_max_length_accepted(self):
        prompt = "a" * MAX_PROMPT_LENGTH
        result = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        self.assertEqual(len(result["raw_text"]), MAX_PROMPT_LENGTH)

    def test_prompt_exceeding_max_length_halts_before_raise(self):
        prompt = "a" * (MAX_PROMPT_LENGTH + 1)
        event_log = EventLog()
        with self.assertRaises(InputPromptExceedsMaxLength):
            build_level0_workshop_normalized_prompt_view(prompt, event_log)
        self.assertTrue(event_log.has_halt())


class MalformedInputHaltTest(unittest.TestCase):

    def test_non_string_input_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonStringInputPrompt):
            build_level0_workshop_normalized_prompt_view(42, event_log)
        self.assertTrue(event_log.has_halt())

    def test_none_input_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonStringInputPrompt):
            build_level0_workshop_normalized_prompt_view(None, event_log)
        self.assertTrue(event_log.has_halt())

    def test_list_input_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonStringInputPrompt):
            build_level0_workshop_normalized_prompt_view(
                ["not", "a", "string"], event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_empty_string_input_halts(self):
        event_log = EventLog()
        with self.assertRaises(EmptyInputPrompt):
            build_level0_workshop_normalized_prompt_view("", event_log)
        self.assertTrue(event_log.has_halt())

    def test_whitespace_only_input_halts(self):
        event_log = EventLog()
        with self.assertRaises(WhitespaceOnlyInputPrompt):
            build_level0_workshop_normalized_prompt_view(
                "   \t\n  ", event_log
            )
        self.assertTrue(event_log.has_halt())

    def test_halt_recorded_before_exception(self):
        event_log = EventLog()
        try:
            build_level0_workshop_normalized_prompt_view("", event_log)
        except EmptyInputPrompt:
            pass
        # Halt event must exist
        halt_events = [
            e for e in event_log.events if e["type"] == "halt"
        ]
        self.assertGreater(len(halt_events), 0)


class UserAuthoredInputPhraseTest(unittest.TestCase):

    def test_user_authored_forbidden_phrase_is_preserved_not_claimed(self):
        event_log = EventLog()
        result = build_level0_workshop_normalized_prompt_view(
            "this is the best deployment", event_log
        )
        self.assertEqual(result["raw_text"], "this is the best deployment")
        self.assertFalse(event_log.has_halt())


class InputImmutabilityTest(unittest.TestCase):

    def test_input_string_object_identity_preserved_in_raw_text(self):
        prompt = "deploy this service"
        result = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        # String is immutable in Python, but we verify the raw_text
        # field matches the input bit-for-bit.
        self.assertEqual(result["raw_text"], prompt)
        self.assertEqual(prompt, "deploy this service")


class FixedShapeTest(unittest.TestCase):

    def test_output_has_exactly_eighteen_keys(self):
        result = build_level0_workshop_normalized_prompt_view(
            "deploy", EventLog()
        )
        self.assertEqual(len(result), 18)

    def test_all_gating_booleans_literal_false(self):
        result = build_level0_workshop_normalized_prompt_view(
            "deploy", EventLog()
        )
        booleans = (
            "selection_made", "measurement_authorized",
            "real_benchmark_authorized", "real_benchmark_ready",
            "source_qualification_authorized",
            "corpus_admission_authorized", "route_created",
        )
        for key in booleans:
            self.assertIs(result[key], False)


class StaticScanTest(unittest.TestCase):

    def setUp(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_normalized_prompt_view.py",
        )
        with open(module_path, "r", encoding="ascii") as handle:
            self.source = handle.read()
        self.module_path = module_path

    def test_no_file_io_calls(self):
        for token in ("open(", "pathlib"):
            self.assertNotIn(token, self.source)

    def test_no_network_or_http_tokens(self):
        for token in ("urllib", "http.client", "socket"):
            self.assertNotIn(token, self.source)

    def test_no_requests_library_token(self):
        for token in ("import requests", "from requests", "requests."):
            self.assertNotIn(token, self.source)

    def test_no_subprocess_or_shell_tokens(self):
        for token in ("subprocess", "os.system", "shutil"):
            self.assertNotIn(token, self.source)

    def test_no_hash_tokens(self):
        for token in ("hashlib", ".hexdigest", ".sha256"):
            self.assertNotIn(token, self.source)

    def test_no_retrieval_verb_definitions(self):
        for token in ("def query", "def search", "def retrieve",
                      "def rank"):
            self.assertNotIn(token, self.source)

    def test_no_scoring_tokens(self):
        for token in ("score", "scoring"):
            self.assertNotIn(token, self.source)

    def test_no_external_integration_tokens(self):
        for token in (
            "copilot", "waza", "vscode", "vs_code", "openai",
            "anthropic", "claude_api", "llm",
        ):
            self.assertNotIn(token, self.source)

    def test_no_embedding_or_vector_tokens(self):
        for token in (
            "embedding(", "vectorize(", " ann_", "approximate_nearest",
            "reranker(", "rerank_",
        ):
            self.assertNotIn(token, self.source)

    def test_no_prior_wo_public_function_invoked(self):
        prior_public_functions = (
            "run_scaffold_route_query_probe",
            "run_scaffold_route_query_ambiguity_probe",
            "run_scaffold_conflicting_evidence_guard",
            "run_scaffold_source_intake_trace",
            "run_scaffold_source_intake_register",
            "run_scaffold_source_trace_admission_bridge",
            "run_scaffold_source_intake_smoke_package",
            "run_scaffold_route_invariant_diagnostic_reporter",
            "run_scaffold_source_intake_visible_report",
            "run_scaffold_external_source_acquisition_boundary",
            "run_scaffold_url_acquisition_executor",
            "run_scaffold_url_acquisition_register_readiness",
            "run_level0_manual_seed_visible_report",
            "run_level0_manual_seed_trace_execution",
            "run_level0_manual_seed_materialization",
            "run_level0_manual_seed_end_to_end_trace",
            "run_level0_workshop_derived_trace",
            "run_level0_workshop_trace_review",
            "map_level0_workshop_user_intent",
        )
        for name in prior_public_functions:
            self.assertNotIn(name, self.source)

    def test_module_file_is_ascii(self):
        with open(self.module_path, "rb") as handle:
            raw = handle.read()
        non_ascii = sum(1 for b in raw if b > 127)
        self.assertEqual(non_ascii, 0)


if __name__ == "__main__":
    unittest.main()
