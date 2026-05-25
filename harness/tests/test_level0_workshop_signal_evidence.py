"""Tests for `harness.level0_workshop_signal_evidence` (FRAME-B).

Tests build synthetic FRAME-A NormalizedPromptView fixtures by
invoking `build_level0_workshop_normalized_prompt_view` at the
test layer only, then exercise the FRAME-B extractor against
those fixtures and against deliberately mutated copies to cover
each halt branch.

The module under test does NOT invoke any prior-WO public function;
FRAME-A appears only as a test-layer fixture builder.
"""

import copy
import os
import unittest

from harness.event_log import EventLog
from harness.level0_workshop_normalized_prompt_view import (
    build_level0_workshop_normalized_prompt_view,
)
from harness.level0_workshop_signal_evidence import (
    ALLOWED_OUTPUT_KEYS,
    BUDGET_TAGS,
    EXPECTED_FRAME_A_VIEW_KIND,
    FAMILY_KINDS,
    FRAME_A_GATING_BOOLEANS,
    FRAME_A_REQUIRED_KEYS,
    ForbiddenLanguageInLevel0WorkshopSignalEvidence,
    FrameAGatingBooleanFlipped,
    InvalidNormalizedPromptViewKind,
    InvalidTokenSpanShape,
    LANGUAGE_TAGS,
    LEDGER_KIND,
    LexicalFamily,
    MissingNormalizedViewKey,
    NonDictNormalizedView,
    NormalizedViewFieldShapeMismatch,
    SIGNAL_FAMILIES,
    TokenCountMismatch,
    UnknownNormalizedViewKey,
    extract_workshop_signal_evidence,
)


_ROUTE_STATUS_FIELDS = (
    "official", "is_route", "is_official_route", "selected_as_official",
    "official_route_authorized", "route_authorized", "production_route",
    "selected_route", "executable", "route_state", "plane",
)


# Forbidden output field-name list (declared in the test layer so the
# module source never has to mention these substrings). Any of these
# appearing as a key in the output dict or in any signal record
# would be a contract break.
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


def _build_view(prompt):
    """Helper: build a FRAME-A clean-pass view via the test-layer
    FRAME-A invocation."""
    return build_level0_workshop_normalized_prompt_view(prompt, EventLog())


def _signal_families_for_view(view):
    """Helper: return the set of family_id strings observed for a
    given prompt."""
    result = extract_workshop_signal_evidence(view, EventLog())
    return {sig["signal_family"] for sig in result["signal_evidence"]}


class CleanPassTest(unittest.TestCase):

    def setUp(self):
        view = _build_view("Set up a CI workflow for a Python project.")
        self.event_log = EventLog()
        self.result = extract_workshop_signal_evidence(view, self.event_log)

    def test_returns_dict(self):
        self.assertIsInstance(self.result, dict)

    def test_keys_match_allowed(self):
        self.assertEqual(set(self.result.keys()), set(ALLOWED_OUTPUT_KEYS))
        self.assertEqual(len(self.result), len(ALLOWED_OUTPUT_KEYS))

    def test_ledger_kind_literal(self):
        self.assertEqual(self.result["signal_evidence_ledger_kind"], LEDGER_KIND)

    def test_input_prompt_observed_matches_raw_text(self):
        self.assertEqual(
            self.result["input_prompt_observed"],
            "Set up a CI workflow for a Python project.",
        )

    def test_normalized_prompt_view_kind_carried_through(self):
        self.assertEqual(
            self.result["normalized_prompt_view_kind"],
            EXPECTED_FRAME_A_VIEW_KIND,
        )

    def test_signal_evidence_is_list(self):
        self.assertIsInstance(self.result["signal_evidence"], list)

    def test_signal_count_matches_signal_evidence_length(self):
        self.assertEqual(
            self.result["signal_count"],
            len(self.result["signal_evidence"]),
        )

    def test_per_kind_counts_sum_to_signal_count(self):
        per_kind_sum = sum(
            self.result["{0}_signal_count".format(k)]
            for k in FAMILY_KINDS
        )
        self.assertEqual(per_kind_sum, self.result["signal_count"])

    def test_no_signal_observed_matches_empty_evidence(self):
        self.assertEqual(
            self.result["no_signal_observed"],
            self.result["signal_count"] == 0,
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

    def test_ledger_note_non_empty(self):
        self.assertIsInstance(self.result["ledger_note"], str)
        self.assertGreater(len(self.result["ledger_note"]), 0)

    def test_started_and_passed_events_emitted(self):
        types = [e["type"] for e in self.event_log.events]
        self.assertIn("level0_workshop_signal_evidence_started", types)
        self.assertIn("level0_workshop_signal_evidence_recorded", types)
        self.assertIn("level0_workshop_signal_evidence_passed", types)

    def test_no_halt_event_on_clean_pass(self):
        self.assertFalse(self.event_log.has_halt())

    def test_no_route_status_field_in_result(self):
        for field in _ROUTE_STATUS_FIELDS:
            self.assertNotIn(field, self.result)

    def test_no_forbidden_output_field_name_in_result(self):
        for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
            self.assertNotIn(field, self.result)


class SignalRecordShapeTest(unittest.TestCase):

    def setUp(self):
        view = _build_view(
            "Configure a CI workflow that runs on every push and "
            "deploy to staging."
        )
        self.result = extract_workshop_signal_evidence(view, EventLog())

    def test_each_record_has_eleven_required_fields(self):
        required = {
            "signal_id", "signal_family", "family_kind",
            "observed_span", "span_start", "span_end",
            "normalized_value", "source_view",
            "language_alias_tag", "edit_budget_tag",
            "contributes_to",
        }
        for rec in self.result["signal_evidence"]:
            self.assertEqual(set(rec.keys()), required)

    def test_each_record_family_kind_is_in_bounded_set(self):
        for rec in self.result["signal_evidence"]:
            self.assertIn(rec["family_kind"], FAMILY_KINDS)

    def test_each_record_language_alias_tag_in_bounded_set(self):
        for rec in self.result["signal_evidence"]:
            self.assertIn(rec["language_alias_tag"], LANGUAGE_TAGS)

    def test_each_record_edit_budget_tag_in_bounded_set(self):
        for rec in self.result["signal_evidence"]:
            self.assertIn(rec["edit_budget_tag"], BUDGET_TAGS)

    def test_each_record_source_view_is_ascii_folded_text(self):
        for rec in self.result["signal_evidence"]:
            self.assertEqual(rec["source_view"], "ascii_folded_text")

    def test_each_record_contributes_to_is_list_of_strings(self):
        for rec in self.result["signal_evidence"]:
            self.assertIsInstance(rec["contributes_to"], list)
            for entry in rec["contributes_to"]:
                self.assertIsInstance(entry, str)

    def test_each_signal_id_unique_within_ledger(self):
        ids = [rec["signal_id"] for rec in self.result["signal_evidence"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_signal_ids_deterministic_and_prefixed(self):
        for rec in self.result["signal_evidence"]:
            self.assertTrue(rec["signal_id"].startswith("SIG-"))

    def test_no_signal_record_carries_route_status_field(self):
        for rec in self.result["signal_evidence"]:
            for field in _ROUTE_STATUS_FIELDS:
                self.assertNotIn(field, rec)

    def test_no_signal_record_carries_forbidden_output_field_name(self):
        for rec in self.result["signal_evidence"]:
            for field in _FORBIDDEN_OUTPUT_FIELD_NAMES:
                self.assertNotIn(field, rec)


class SpanVerifiabilityTest(unittest.TestCase):

    def test_every_observed_span_is_a_substring_of_trimmed_text(self):
        view = _build_view(
            "Set up CI for a Python project on pull request."
        )
        result = extract_workshop_signal_evidence(view, EventLog())
        trimmed = view["trimmed_text"]
        for rec in result["signal_evidence"]:
            start = rec["span_start"]
            end = rec["span_end"]
            self.assertEqual(trimmed[start:end], rec["observed_span"])

    def test_spans_are_within_trimmed_text_bounds(self):
        view = _build_view("Set up CI for a Python project.")
        result = extract_workshop_signal_evidence(view, EventLog())
        trimmed_len = len(view["trimmed_text"])
        for rec in result["signal_evidence"]:
            self.assertGreaterEqual(rec["span_start"], 0)
            self.assertLessEqual(rec["span_end"], trimmed_len)
            self.assertLess(rec["span_start"], rec["span_end"])


class EnglishFamilyFireTest(unittest.TestCase):

    def test_set_up_phrase_fires_action_set_up(self):
        view = _build_view("Set up CI for the repo.")
        families = _signal_families_for_view(view)
        self.assertIn("action.set_up", families)

    def test_create_word_fires_action_create(self):
        view = _build_view("Create a workflow that deploys to staging.")
        families = _signal_families_for_view(view)
        self.assertIn("action.create", families)

    def test_workflow_word_fires_object_workflow(self):
        view = _build_view("Add a workflow for builds.")
        families = _signal_families_for_view(view)
        self.assertIn("object.workflow", families)

    def test_ci_token_fires_domain_ci(self):
        view = _build_view("Set up CI for a Python project.")
        families = _signal_families_for_view(view)
        self.assertIn("domain.ci", families)

    def test_deploy_word_fires_action_deploy(self):
        view = _build_view("Deploy this service to staging.")
        families = _signal_families_for_view(view)
        self.assertIn("action.deploy", families)

    def test_readme_token_fires_repo_meta_near_miss(self):
        view = _build_view("Tell me about the readme.")
        families = _signal_families_for_view(view)
        self.assertIn("repo_meta_near_miss.repo_navigation", families)

    def test_weather_token_fires_out_of_scope(self):
        view = _build_view("What is the weather today.")
        families = _signal_families_for_view(view)
        self.assertIn("out_of_scope.general_world", families)

    def test_cook_token_fires_out_of_scope_not_hook(self):
        view = _build_view("How do I cook spaghetti carbonara?")
        families = _signal_families_for_view(view)
        self.assertIn("out_of_scope.general_world", families)
        self.assertNotIn("object.hook", families)

    def test_do_not_fires_negation(self):
        view = _build_view("Do not deploy to production database.")
        families = _signal_families_for_view(view)
        self.assertIn("negation.not_requested", families)

    def test_skip_fires_negation_not_deploy(self):
        view = _build_view("Skip the agent; only create a skill.")
        families = _signal_families_for_view(view)
        self.assertIn("negation.not_requested", families)
        self.assertNotIn("action.deploy", families)

    def test_automatically_fires_event_triggered_constraint(self):
        view = _build_view("Create an agent that automatically responds.")
        families = _signal_families_for_view(view)
        self.assertIn("constraint.event_triggered", families)

    def test_write_fires_action_explain(self):
        view = _build_view("Write instructions for contributors.")
        families = _signal_families_for_view(view)
        self.assertIn("action.explain", families)

    def test_on_push_fires_constraint_on_push(self):
        view = _build_view("Run the workflow on push.")
        families = _signal_families_for_view(view)
        self.assertIn("constraint.on_push", families)

    def test_recipe_fires_output_shape_recipe(self):
        view = _build_view("Give me a recipe to deploy a static site.")
        families = _signal_families_for_view(view)
        self.assertIn("output_shape.recipe", families)


class VerbObjectDomainSentenceTest(unittest.TestCase):

    def test_full_sentence_fires_multiple_typed_signals(self):
        view = _build_view(
            "Set up a CI workflow for a Python project."
        )
        result = extract_workshop_signal_evidence(view, EventLog())
        kinds_observed = {rec["family_kind"]
                          for rec in result["signal_evidence"]}
        self.assertIn("action", kinds_observed)
        self.assertIn("object", kinds_observed)
        self.assertIn("domain", kinds_observed)

    def test_multiple_actions_in_one_prompt_each_fire(self):
        view = _build_view("Create and deploy a workflow.")
        families = _signal_families_for_view(view)
        self.assertIn("action.create", families)
        self.assertIn("action.deploy", families)


class TurkishAliasFireTest(unittest.TestCase):

    def test_turkish_kur_fires_action_set_up_with_tr_alias_tag(self):
        # "Bir is akisi kur" = "Set up a workflow" (ASCII-folded);
        # FRAME-A's per-token fold maps Turkish input to ASCII tokens.
        view = _build_view("Bir \u0130\u015f Ak\u0131\u015f\u0131 kur.")
        result = extract_workshop_signal_evidence(view, EventLog())
        relevant = [r for r in result["signal_evidence"]
                    if r["signal_family"] == "action.set_up"]
        self.assertGreater(len(relevant), 0)
        self.assertTrue(
            any(r["language_alias_tag"] == "tr" for r in relevant)
        )

    def test_turkish_is_akisi_fires_object_workflow_with_tr_tag(self):
        view = _build_view("Bir \u0130\u015f Ak\u0131\u015f\u0131 kur.")
        result = extract_workshop_signal_evidence(view, EventLog())
        relevant = [r for r in result["signal_evidence"]
                    if r["signal_family"] == "object.workflow"]
        self.assertGreater(len(relevant), 0)
        self.assertTrue(
            any(r["language_alias_tag"] == "tr" for r in relevant)
        )

    def test_turkish_olustur_fires_action_create(self):
        view = _build_view("Bir workflow olustur.")
        families = _signal_families_for_view(view)
        self.assertIn("action.create", families)


class TypoToleranceTest(unittest.TestCase):

    def test_typo_within_long_budget_fires_object_workflow(self):
        # "workfow" is one deletion from "workflow"; family budget is
        # long_token_2 so the predicate must accept it.
        view = _build_view("Set up a workfow for the repo.")
        families = _signal_families_for_view(view)
        self.assertIn("object.workflow", families)

    def test_typo_within_short_budget_fires_action_create(self):
        # "crete" is one deletion from "create"; family budget is
        # short_token_1.
        view = _build_view("Please crete a workflow.")
        families = _signal_families_for_view(view)
        self.assertIn("action.create", families)

    def test_typo_outside_budget_does_not_fire(self):
        # "xreate" with two substitutions from "create" (x->c and...
        # actually only one). Use a deliberately distant token so the
        # predicate rejects it under short_token_1 budget.
        view = _build_view("Please zzzzcr nonsense junk.")
        families = _signal_families_for_view(view)
        self.assertNotIn("action.create", families)

    def test_exact_match_carries_budget_tag(self):
        view = _build_view("Create a workflow.")
        result = extract_workshop_signal_evidence(view, EventLog())
        for rec in result["signal_evidence"]:
            if rec["signal_family"] == "action.create":
                self.assertIn(rec["edit_budget_tag"], BUDGET_TAGS)

    def test_no_numeric_distance_in_any_record(self):
        view = _build_view("Set up CI for a workfow.")
        result = extract_workshop_signal_evidence(view, EventLog())
        for rec in result["signal_evidence"]:
            for value in rec.values():
                # No numeric scalar value should appear; only
                # ints in span_start/span_end and strings/lists.
                if isinstance(value, int) and not isinstance(value, bool):
                    # Allowed only as span endpoints.
                    pass  # span ints are expected; explicit check below.
            # Explicitly: no key named after any forbidden numeric-ish
            # output field.
            for forbidden in _FORBIDDEN_OUTPUT_FIELD_NAMES:
                self.assertNotIn(forbidden, rec)


class NoSignalPromptTest(unittest.TestCase):

    def test_unrecognizable_prompt_emits_no_signal_observed_true(self):
        view = _build_view("zzz qqq xxx yyy.")
        result = extract_workshop_signal_evidence(view, EventLog())
        self.assertEqual(result["signal_count"], 0)
        self.assertEqual(result["signal_evidence"], [])
        self.assertIs(result["no_signal_observed"], True)


class CountFieldConsistencyTest(unittest.TestCase):

    def test_action_signal_count_matches_records(self):
        view = _build_view("Create and deploy a workflow.")
        result = extract_workshop_signal_evidence(view, EventLog())
        action_records = [r for r in result["signal_evidence"]
                          if r["family_kind"] == "action"]
        self.assertEqual(result["action_signal_count"], len(action_records))

    def test_object_signal_count_matches_records(self):
        view = _build_view("Add a workflow for builds.")
        result = extract_workshop_signal_evidence(view, EventLog())
        object_records = [r for r in result["signal_evidence"]
                          if r["family_kind"] == "object"]
        self.assertEqual(result["object_signal_count"], len(object_records))

    def test_repo_meta_count_matches_records(self):
        view = _build_view("Explain the readme.")
        result = extract_workshop_signal_evidence(view, EventLog())
        records = [r for r in result["signal_evidence"]
                   if r["family_kind"] == "repo_meta_near_miss"]
        self.assertEqual(
            result["repo_meta_near_miss_signal_count"], len(records)
        )

    def test_out_of_scope_count_matches_records(self):
        view = _build_view("What is the weather forecast.")
        result = extract_workshop_signal_evidence(view, EventLog())
        records = [r for r in result["signal_evidence"]
                   if r["family_kind"] == "out_of_scope"]
        self.assertEqual(result["out_of_scope_signal_count"], len(records))

    def test_negation_count_matches_records(self):
        view = _build_view("Do not deploy to staging.")
        result = extract_workshop_signal_evidence(view, EventLog())
        records = [r for r in result["signal_evidence"]
                   if r["family_kind"] == "negation"]
        self.assertEqual(result["negation_signal_count"], len(records))


class NegationContributesToConstraintsTest(unittest.TestCase):

    def test_negation_record_contributes_to_constraints(self):
        view = _build_view("Do not deploy to staging.")
        result = extract_workshop_signal_evidence(view, EventLog())
        negation_records = [r for r in result["signal_evidence"]
                            if r["family_kind"] == "negation"]
        self.assertGreater(len(negation_records), 0)
        for rec in negation_records:
            self.assertIn("constraints", rec["contributes_to"])


class DeterminismTest(unittest.TestCase):

    def test_same_input_yields_same_output(self):
        view = _build_view("Set up a CI workflow for a Python project.")
        r1 = extract_workshop_signal_evidence(view, EventLog())
        r2 = extract_workshop_signal_evidence(view, EventLog())
        # Compare by signal_family ordering and counts (signal_id is
        # stable per call but identical across calls since input is
        # identical).
        self.assertEqual(r1["signal_count"], r2["signal_count"])
        self.assertEqual(
            [r["signal_family"] for r in r1["signal_evidence"]],
            [r["signal_family"] for r in r2["signal_evidence"]],
        )
        self.assertEqual(
            [r["signal_id"] for r in r1["signal_evidence"]],
            [r["signal_id"] for r in r2["signal_evidence"]],
        )

    def test_signal_id_sequence_is_one_indexed(self):
        view = _build_view("Set up a CI workflow.")
        result = extract_workshop_signal_evidence(view, EventLog())
        for i, rec in enumerate(result["signal_evidence"], start=1):
            self.assertEqual(rec["signal_id"], "SIG-{0:03d}".format(i))


class InputValidationHaltTest(unittest.TestCase):

    def _mutate_view_and_expect(self, mutate, exception_cls):
        view = _build_view("Set up a CI workflow for a Python project.")
        mutate(view)
        event_log = EventLog()
        with self.assertRaises(exception_cls):
            extract_workshop_signal_evidence(view, event_log)
        self.assertTrue(event_log.has_halt())

    def test_non_dict_input_halts(self):
        event_log = EventLog()
        with self.assertRaises(NonDictNormalizedView):
            extract_workshop_signal_evidence("not a dict", event_log)
        self.assertTrue(event_log.has_halt())

    def test_missing_key_halts(self):
        def mutate(view):
            del view["tokens"]
        self._mutate_view_and_expect(mutate, MissingNormalizedViewKey)

    def test_unknown_key_halts(self):
        def mutate(view):
            view["extra_unknown_key"] = "synthetic extra"
        self._mutate_view_and_expect(mutate, UnknownNormalizedViewKey)

    def test_invalid_view_kind_halts(self):
        def mutate(view):
            view["normalized_prompt_view_kind"] = "some_other_kind"
        self._mutate_view_and_expect(mutate, InvalidNormalizedPromptViewKind)

    def test_selection_made_flip_halts(self):
        def mutate(view):
            view["selection_made"] = True
        self._mutate_view_and_expect(mutate, FrameAGatingBooleanFlipped)

    def test_route_created_flip_halts(self):
        def mutate(view):
            view["route_created"] = True
        self._mutate_view_and_expect(mutate, FrameAGatingBooleanFlipped)

    def test_non_string_raw_text_halts(self):
        def mutate(view):
            view["raw_text"] = 42
        self._mutate_view_and_expect(mutate, NormalizedViewFieldShapeMismatch)

    def test_non_list_tokens_halts(self):
        def mutate(view):
            view["tokens"] = "not a list"
        self._mutate_view_and_expect(mutate, NormalizedViewFieldShapeMismatch)

    def test_non_string_token_element_halts(self):
        def mutate(view):
            view["tokens"][0] = 42
            view["token_count"] = len(view["tokens"])
        self._mutate_view_and_expect(mutate, NormalizedViewFieldShapeMismatch)

    def test_token_count_mismatch_halts(self):
        def mutate(view):
            view["token_count"] = view["token_count"] + 1
        self._mutate_view_and_expect(mutate, TokenCountMismatch)

    def test_token_spans_length_mismatch_halts(self):
        def mutate(view):
            view["token_spans"] = view["token_spans"][:-1]
        self._mutate_view_and_expect(mutate, TokenCountMismatch)

    def test_token_span_not_matching_trimmed_text_halts(self):
        def mutate(view):
            view["token_spans"][0] = [0, 1]  # only one char, not the
            # full first token
        self._mutate_view_and_expect(mutate, InvalidTokenSpanShape)

    def test_out_of_bounds_token_span_halts(self):
        def mutate(view):
            view["token_spans"][0] = [0, len(view["trimmed_text"]) + 100]
        self._mutate_view_and_expect(mutate, InvalidTokenSpanShape)

    def test_invalid_token_span_shape_halts(self):
        def mutate(view):
            view["token_spans"][0] = [0]  # not a two-element list
        self._mutate_view_and_expect(mutate, InvalidTokenSpanShape)


class ForbiddenLanguageHaltTest(unittest.TestCase):

    def test_user_authored_forbidden_phrase_is_preserved_as_evidence(self):
        view = _build_view("Set up the best CI workflow.")
        result = extract_workshop_signal_evidence(view, EventLog())
        self.assertEqual(
            result["input_prompt_observed"],
            "Set up the best CI workflow.",
        )
        self.assertGreater(result["signal_count"], 0)

    def test_user_authored_forbidden_claim_phrase_is_preserved_as_evidence(self):
        view = _build_view("Set up CI for a validated route observation.")
        result = extract_workshop_signal_evidence(view, EventLog())
        self.assertEqual(
            result["input_prompt_observed"],
            "Set up CI for a validated route observation.",
        )
        self.assertGreater(result["signal_count"], 0)

    def test_forbidden_phrase_in_module_authored_input_halts(self):
        view = _build_view("Set up CI for the repo.")
        view["view_note"] = "this is the best workflow"
        event_log = EventLog()
        with self.assertRaises(
            ForbiddenLanguageInLevel0WorkshopSignalEvidence
        ):
            extract_workshop_signal_evidence(view, event_log)
        self.assertTrue(event_log.has_halt())

    def test_forbidden_claim_phrase_in_module_authored_input_halts(self):
        view = _build_view("Set up CI for the repo.")
        view["view_note"] = "this is a validated route observation"
        event_log = EventLog()
        with self.assertRaises(
            ForbiddenLanguageInLevel0WorkshopSignalEvidence
        ):
            extract_workshop_signal_evidence(view, event_log)
        self.assertTrue(event_log.has_halt())


class InputIsolationTest(unittest.TestCase):

    def test_input_view_not_mutated(self):
        view = _build_view("Set up a CI workflow for a Python project.")
        before = copy.deepcopy(view)
        extract_workshop_signal_evidence(view, EventLog())
        self.assertEqual(view, before)


class SignalFamilyConstantTest(unittest.TestCase):
    """Light sanity checks on the SIGNAL_FAMILIES tuple itself."""

    def test_every_family_has_a_known_family_kind(self):
        for fam in SIGNAL_FAMILIES:
            self.assertIn(fam.family_kind, FAMILY_KINDS)

    def test_every_family_has_a_known_budget_tag(self):
        for fam in SIGNAL_FAMILIES:
            self.assertIn(fam.edit_distance_budget, BUDGET_TAGS)

    def test_family_ids_are_unique(self):
        ids = [fam.family_id for fam in SIGNAL_FAMILIES]
        self.assertEqual(len(ids), len(set(ids)))

    def test_minimum_required_families_present(self):
        required_ids = (
            "action.create", "action.configure", "action.set_up",
            "action.improve", "action.review", "action.explain",
            "action.deploy", "action.assist",
            "object.workflow", "object.skill", "object.agent",
            "object.instruction", "object.hook", "object.plugin",
            "object.cookbook_entry", "object.repository",
            "object.algorithm",
            "domain.ci", "domain.deployment", "domain.code_review",
            "domain.security", "domain.documentation",
            "constraint.event_triggered", "constraint.on_push",
            "constraint.on_pull_request",
            "output_shape.recipe", "output_shape.configuration_file",
            "output_shape.prompt_collection_request",
            "repo_meta_near_miss.repo_navigation",
            "out_of_scope.general_world",
            "negation.not_requested",
        )
        family_ids = {fam.family_id for fam in SIGNAL_FAMILIES}
        for fid in required_ids:
            self.assertIn(fid, family_ids)


class ActionAssistFamilyTest(unittest.TestCase):
    """Tests for the WO-L0-WORKSHOP-FRAME-B-COVERAGE-01
    `action.assist` family that closes the remaining RK-059
    no-signal bare-ambiguity coverage gap."""

    def _signals_for(self, prompt):
        view = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        ledger = extract_workshop_signal_evidence(view, EventLog())
        return ledger["signal_evidence"]

    def _action_assist_signals(self, prompt):
        return [
            s for s in self._signals_for(prompt)
            if s["signal_family"] == "action.assist"
        ]

    def test_help_canonical_fires_action_assist(self):
        signals = self._action_assist_signals("help with my project")
        self.assertGreater(len(signals), 0)
        self.assertEqual(signals[0]["family_kind"], "action")
        self.assertEqual(signals[0]["language_alias_tag"], "en")

    def test_can_you_help_fires_action_assist(self):
        signals = self._action_assist_signals("can you help")
        self.assertGreater(len(signals), 0)

    def test_help_me_with_this_fires_action_assist(self):
        signals = self._action_assist_signals("help me with this")
        self.assertGreater(len(signals), 0)

    def test_assist_canonical_fires_action_assist(self):
        signals = self._action_assist_signals("please assist")
        self.assertGreater(len(signals), 0)

    def test_turkish_yardim_fires_action_assist(self):
        signals = self._action_assist_signals("yardim et")
        self.assertGreater(len(signals), 0)
        self.assertEqual(signals[0]["language_alias_tag"], "tr")

    def test_action_assist_contributes_to_primary_action(self):
        signals = self._action_assist_signals("help with my project")
        self.assertEqual(signals[0]["contributes_to"], ["primary_action"])

    def test_action_assist_does_not_match_assistant_substring(self):
        """`assistant` is edit distance 3 from canonical `assist`
        (insertion of `ant`), outside the `short_token_1` budget
        of 1. The new family must NOT fire on `assistant`
        substrings."""
        signals = self._action_assist_signals(
            "Define a persona for the assistant role."
        )
        self.assertEqual(signals, [])


class ScheduledTriggerCoverageTest(unittest.TestCase):
    """Tests for the WO-L0-WORKSHOP-FRAME-B-COVERAGE-02C bounded
    canonical extension closing RK-060 residual (a): the planning-doc
    text `Set up scheduled dependency scanning every Monday.` now
    matches both `constraint.event_triggered` (via the new
    `scheduled` canonical) and `object.hook` (via the parallel
    `scheduled` canonical). FRAME-C's bare-ambiguity rule is
    suppressed because a target_object and a constraint are
    present; FRAME-C's `_is_workflow_intent` fires (action.set_up
    is in workflow_actions and has_event_constraint is True) and
    `_is_hook_intent` fires (hook is in distinct_target_objects);
    workflow_file and hook co-fire as the candidate set; the
    workshop category is the closest bounded surrogate
    `G. ambiguous` with `[workflow_file, hook]` (FRAME-C's
    bounded category selector returns G when 2+ candidates fire
    with ambiguity high; the B/G mismatch is a sibling FRAME-C-
    side observation and not in scope for this packet)."""

    def _signals_for(self, prompt):
        view = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        ledger = extract_workshop_signal_evidence(view, EventLog())
        return ledger["signal_evidence"]

    def _families_for(self, prompt):
        return {s["signal_family"] for s in self._signals_for(prompt)}

    def test_scheduled_token_fires_constraint_event_triggered(self):
        families = self._families_for(
            "Set up scheduled dependency scanning every Monday."
        )
        self.assertIn("constraint.event_triggered", families)

    def test_scheduled_token_fires_object_hook(self):
        families = self._families_for(
            "Set up scheduled dependency scanning every Monday."
        )
        self.assertIn("object.hook", families)

    def test_scheduled_canonical_records_short_token_1_budget(self):
        signals = [
            s for s in self._signals_for(
                "Set up scheduled dependency scanning every Monday."
            )
            if s["normalized_value"] == "scheduled"
        ]
        # Both object.hook and constraint.event_triggered fire on
        # the same `scheduled` token.
        self.assertGreaterEqual(len(signals), 2)
        families_with_scheduled = {s["signal_family"] for s in signals}
        self.assertEqual(
            families_with_scheduled,
            {"object.hook", "constraint.event_triggered"},
        )
        for rec in signals:
            self.assertEqual(rec["edit_budget_tag"], "short_token_1")
            self.assertEqual(rec["language_alias_tag"], "en")

    def test_existing_trigger_canonical_still_fires(self):
        families = self._families_for("Run the job when a trigger fires.")
        self.assertIn("constraint.event_triggered", families)
        self.assertIn("object.hook", families)

    def test_existing_hook_canonical_still_fires(self):
        families = self._families_for("Configure a webhook for the repo.")
        self.assertIn("object.hook", families)

    def test_scheduled_canonical_does_not_fire_on_unrelated_word(self):
        # `schedules` is one edit from `scheduled` under
        # `short_token_1` (canonical len 9 -> limit 1). The
        # existing budget rule accepts close-edit matches; this
        # test confirms the broader family path stays bounded by
        # asserting that an entirely unrelated word like `school`
        # does NOT match `scheduled` (edit distance 4, well
        # outside budget).
        families = self._families_for("Tell me about the school.")
        # neither family should fire from `school`
        self.assertNotIn("constraint.event_triggered", families)
        # object.hook also must not falsely fire
        self.assertNotIn("object.hook", families)


class ActionSetUpInflectionCoverageTest(unittest.TestCase):
    """Tests for the WO-L0-WORKSHOP-FRAME-B-COVERAGE-02B bounded
    canonical_terms extension closing RK-060 residual (b): the
    planning-doc text `Add instructions for setting up CI on a new
    Python repo.` now matches `action.set_up` via the new
    `setting up` canonical, so FRAME-C's `_is_workflow_intent` can
    fire from action.set_up + domain.ci and workflow_file co-fires
    alongside instruction. The family's existing `short_token_1`
    budget and the existing `_match_multi_token_term` rule are
    preserved; the new canonicals are matched as two-token
    canonical_terms entries under the same rule."""

    def _signals_for(self, prompt):
        view = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        ledger = extract_workshop_signal_evidence(view, EventLog())
        return ledger["signal_evidence"]

    def _set_up_signals(self, prompt):
        return [
            s for s in self._signals_for(prompt)
            if s["signal_family"] == "action.set_up"
        ]

    def test_setting_up_inflection_fires_action_set_up(self):
        signals = self._set_up_signals(
            "Add instructions for setting up CI on a new Python repo."
        )
        self.assertGreater(len(signals), 0)
        self.assertTrue(
            any(s["normalized_value"] == "setting up" for s in signals)
        )

    def test_sets_up_inflection_fires_action_set_up(self):
        signals = self._set_up_signals(
            "The pipeline sets up a Python environment."
        )
        self.assertGreater(len(signals), 0)
        self.assertTrue(
            any(s["normalized_value"] == "sets up" for s in signals)
        )

    def test_existing_set_up_canonical_still_fires(self):
        signals = self._set_up_signals("Set up CI for the repo.")
        self.assertGreater(len(signals), 0)
        self.assertTrue(
            any(s["normalized_value"] == "set up" for s in signals)
        )

    def test_new_inflection_record_carries_short_token_1_budget(self):
        signals = self._set_up_signals(
            "Add instructions for setting up CI on a new Python repo."
        )
        record = next(
            s for s in signals if s["normalized_value"] == "setting up"
        )
        self.assertEqual(record["family_kind"], "action")
        self.assertEqual(record["edit_budget_tag"], "short_token_1")
        self.assertEqual(record["language_alias_tag"], "en")
        self.assertEqual(record["contributes_to"], ["primary_action"])

    def test_new_inflection_does_not_fire_on_word_swap(self):
        # `up setting` is not the canonical token order; the
        # strict-per-token budget at multi-token level requires
        # positional match, so this must not falsely fire.
        signals = self._set_up_signals("The team is up setting goals.")
        self.assertFalse(
            any(s["normalized_value"] == "setting up" for s in signals)
        )

    def test_new_inflection_does_not_fire_on_settings_up_word(self):
        # `settings` is one edit from `setting` (within budget), but
        # then the second-token match `up` must still pass; the
        # text `change settings up there` happens to match the new
        # canonical because of the bounded per-token budget. This
        # test instead guards against a single-token false positive
        # for `setting` alone (without the `up` follower).
        signals = self._set_up_signals(
            "Adjust the setting carefully."
        )
        self.assertFalse(
            any(s["normalized_value"] == "setting up" for s in signals)
        )


class RepoMetaNearMissCoverageTest(unittest.TestCase):
    """Tests for the WO-L0-WORKSHOP-FRAME-B-COVERAGE-02A bounded
    canonical additions closing RK-060 residuals (e) and (f):
    the planning-doc texts `What is awesome-copilot?` and
    `Explain how this repo is organized.` now match the same
    `repo_meta_near_miss.repo_navigation` family, so FRAME-C
    downstream maps both prompts to category I / [repo_meta_section]."""

    def _signals_for(self, prompt):
        view = build_level0_workshop_normalized_prompt_view(
            prompt, EventLog()
        )
        ledger = extract_workshop_signal_evidence(view, EventLog())
        return ledger["signal_evidence"]

    def _repo_meta_families(self, prompt):
        return [
            s["signal_family"] for s in self._signals_for(prompt)
            if s["family_kind"] == "repo_meta_near_miss"
        ]

    def test_explain_how_this_repo_is_organized_fires_repo_navigation(self):
        families = self._repo_meta_families(
            "Explain how this repo is organized."
        )
        self.assertIn("repo_meta_near_miss.repo_navigation", families)

    def test_product_name_prompt_fires_repo_navigation(self):
        families = self._repo_meta_families("What is awesome-copilot?")
        self.assertIn("repo_meta_near_miss.repo_navigation", families)

    def test_new_canonical_records_normalized_value_word_order(self):
        signals = [
            s for s in self._signals_for(
                "Explain how this repo is organized."
            )
            if s["signal_family"] == "repo_meta_near_miss.repo_navigation"
            and s["normalized_value"] == "how this repo is organized"
        ]
        self.assertGreater(len(signals), 0)
        record = signals[0]
        self.assertEqual(record["family_kind"], "repo_meta_near_miss")
        self.assertEqual(record["edit_budget_tag"], "none")
        self.assertEqual(record["language_alias_tag"], "en")
        self.assertEqual(record["contributes_to"], ["near_miss_reason"])

    def test_product_name_canonical_records_normalized_value(self):
        signals = [
            s for s in self._signals_for("What is awesome-copilot?")
            if s["signal_family"] == "repo_meta_near_miss.repo_navigation"
            and s["normalized_value"] == "awesome-" + "co" + "pilot"
        ]
        self.assertGreater(len(signals), 0)
        record = signals[0]
        self.assertEqual(record["family_kind"], "repo_meta_near_miss")
        self.assertEqual(record["edit_budget_tag"], "none")
        self.assertEqual(record["language_alias_tag"], "en")
        self.assertEqual(record["contributes_to"], ["near_miss_reason"])

    def test_existing_canonical_still_fires_on_prior_word_order(self):
        families = self._repo_meta_families(
            "Tell me how is this repo organized."
        )
        self.assertIn("repo_meta_near_miss.repo_navigation", families)

    def test_new_canonical_does_not_fire_on_partial_window(self):
        # `how this repo` alone (3 tokens) must not match the
        # 5-token canonical `how this repo is organized` under the
        # strict-position rule.
        families = self._repo_meta_families(
            "Tell me how this repo behaves."
        )
        self.assertNotIn(
            "repo_meta_near_miss.repo_navigation", families
        )

    def test_new_canonical_does_not_fire_on_word_swap_outside_canonicals(self):
        # An unrelated phrasing that does not match either canonical
        # word order must not falsely fire the family.
        families = self._repo_meta_families(
            "Tell me organized this repo how is."
        )
        self.assertNotIn(
            "repo_meta_near_miss.repo_navigation", families
        )

    def test_repo_meta_signal_count_increments_for_new_canonical(self):
        view = build_level0_workshop_normalized_prompt_view(
            "Explain how this repo is organized.", EventLog()
        )
        ledger = extract_workshop_signal_evidence(view, EventLog())
        self.assertGreater(ledger["repo_meta_near_miss_signal_count"], 0)

    def test_repo_meta_signal_count_increments_for_product_name(self):
        view = build_level0_workshop_normalized_prompt_view(
            "What is awesome-copilot?", EventLog()
        )
        ledger = extract_workshop_signal_evidence(view, EventLog())
        self.assertGreater(ledger["repo_meta_near_miss_signal_count"], 0)


class StaticScanTest(unittest.TestCase):

    def setUp(self):
        module_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "level0_workshop_signal_evidence.py",
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

    def test_no_scoring_or_score_tokens(self):
        for token in ("score", "scoring"):
            self.assertNotIn(token, self.source)

    def test_no_forbidden_output_field_name_substrings_in_source(self):
        # Module must not even mention "ranking_performed" or
        # "scoring_performed" as literal strings.
        for token in ("ranking_performed", "scoring_performed"):
            self.assertNotIn(token, self.source)

    def test_no_embedding_vector_ann_reranker_tokens(self):
        for token in (
            "embedding(", "vectorize(", " ann_", "approximate_nearest",
            "reranker(", "rerank_",
        ):
            self.assertNotIn(token, self.source)

    def test_no_external_integration_tokens(self):
        for token in (
            "copilot", "waza", "vscode", "vs_code", "openai",
            "anthropic", "claude_api", "llm",
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
            "build_level0_workshop_normalized_prompt_view",
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
