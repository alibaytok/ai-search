"""Level 0B workshop SignalEvidence layer (FRAME-B).

WO-L0-WORKSHOP-FRAME-B builds Stage B of the Level 0B Intent Core:
a deterministic SignalEvidence extractor that consumes an
already-loaded FRAME-A NormalizedPromptView dict and emits an
inspectable signal evidence ledger (one record per family hit,
with citation span, language alias tag, edit-budget tag, and
contributes_to list).

Pipeline position:

    PromptText
      -> FRAME-A NormalizedPromptView
      -> FRAME-B SignalEvidenceLedger    <-- this module
      -> FRAME-C CanonicalIntentFrame + ShapeTouchPlan

This module does NOT classify a frame, does NOT synthesize a
canonical intent frame, does NOT compute a shape-touch plan, does
NOT emit a workshop_prompt_record, does NOT create or select route
objects, does NOT qualify a source, does NOT admit a corpus, does
NOT retrieve, embed, vectorize, call any provider or external API,
and does NOT claim universal intent understanding, production
readiness, completeness, or benchmark readiness. Those concerns
belong to FRAME-C and a future RK-058 closure packet.

The module performs no file IO, no network call, no URL fetch /
download / crawl / browser automation, no PDF text extraction, no
hash computation, no external process spawning, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools. It uses only the Python standard
library (`re`, `unicodedata`, `collections.namedtuple`).

Module source is ASCII-only. Multilingual signal aliases are
stored in ASCII-folded form; the matching pipeline applies the
same NFKD-then-ASCII-ignore fold per token (deterministic, matches
FRAME-A's fold rule) so Turkish input flows through unchanged
without introducing non-ASCII module literals.

Typo tolerance is a deterministic Boolean predicate. Each
LexicalFamily declares one budget tag (`none`, `short_token_1`,
`long_token_2`) which selects a bounded Damerau-Levenshtein
budget. No numeric edit count appears in any output record; only
the categorical budget tag is emitted.

Constraints v1 non-claim constraint carries forward: this module
does not claim any signal, span, family, alias tag, or count is
sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded SIGNAL_FAMILIES tuple, the
bounded family-kind enum, the bounded budget-tag enum, the
twenty-two ALLOWED_OUTPUT_KEYS, and the eleven-field signal record
shape are bounded by WO-L0-WORKSHOP-FRAME-B and are NOT claimed
exhaustive.

Public surface:

    extract_workshop_signal_evidence(
        normalized_view, event_log
    ) -> dict
"""

import re
import unicodedata
from collections import namedtuple

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


SIGNAL_EVIDENCE_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


LEDGER_KIND = "level0_workshop_signal_evidence_ledger"


EXPECTED_FRAME_A_VIEW_KIND = "level0_workshop_normalized_prompt_view"


# Mirrors the FRAME-A clean-pass eighteen-key shape contract. This
# constant is declared locally rather than imported so FRAME-A and
# FRAME-B stay import-isolated (FRAME-B does not invoke any
# FRAME-A public function; this is verified by static-scan test).
FRAME_A_REQUIRED_KEYS = (
    "normalized_prompt_view_kind",
    "raw_text",
    "trimmed_text",
    "casefolded_text",
    "ascii_folded_text",
    "tokens",
    "token_spans",
    "token_count",
    "max_prompt_length",
    "normalization_steps",
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
    "view_note",
)
_FRAME_A_REQUIRED_KEY_SET = frozenset(FRAME_A_REQUIRED_KEYS)


FRAME_A_GATING_BOOLEANS = (
    "selection_made",
    "measurement_authorized",
    "real_benchmark_authorized",
    "real_benchmark_ready",
    "source_qualification_authorized",
    "corpus_admission_authorized",
    "route_created",
)


ALLOWED_OUTPUT_KEYS = (
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


FAMILY_KINDS = (
    "action",
    "object",
    "domain",
    "constraint",
    "output_shape",
    "repo_meta_near_miss",
    "out_of_scope",
    "negation",
)
_FAMILY_KIND_SET = frozenset(FAMILY_KINDS)


BUDGET_TAGS = ("none", "short_token_1", "long_token_2")
_BUDGET_TAG_SET = frozenset(BUDGET_TAGS)


# Categorical budget tags. The integer limit is derived from the
# canonical term's length so short canonical terms cannot grant
# disproportionately large tolerance budgets (which would cause
# noise matches like 'me' -> 'yml' or 'xxx' -> 'fix'). The output
# record always carries the family's declared categorical tag, not
# the derived integer.
_SHORT_CANONICAL_MIN_LEN = 4
_LONG_CANONICAL_MIN_LEN = 6


def _budget_limit_for_canonical(budget_tag, canonical):
    """Return the integer edit budget for a canonical term under the
    family's declared budget tag. Shorter canonical terms collapse
    to a tighter budget to suppress noise matches."""
    if budget_tag == "none":
        return 0
    canonical_len = len(canonical)
    if budget_tag == "short_token_1":
        if canonical_len >= _SHORT_CANONICAL_MIN_LEN:
            return 1
        return 0
    if budget_tag == "long_token_2":
        if canonical_len >= _LONG_CANONICAL_MIN_LEN:
            return 2
        if canonical_len >= _SHORT_CANONICAL_MIN_LEN:
            return 1
        return 0
    return 0


# Stripped-from-edges punctuation set used during matching. Stripping
# is applied to FOLDED TOKENS for comparison only; the recorded
# observed_span is derived from FRAME-A's token_spans into the
# original trimmed_text and therefore retains the punctuation.
_EDGE_PUNCTUATION = ".,!?;:\"'()[]{}"


def _strip_edge_punctuation(folded_token):
    return folded_token.strip(_EDGE_PUNCTUATION)


LANGUAGE_TAGS = ("en", "tr", "none")


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


_SOURCE_VIEW_LITERAL = "ascii_folded_text"


LexicalFamily = namedtuple(
    "LexicalFamily",
    [
        "family_id",
        "family_kind",
        "canonical_terms",
        "tr_aliases",
        "edit_distance_budget",
        "exclusion_terms",
        "contributes_to",
    ],
)


# Bounded ASCII-only signal families. The Turkish aliases are
# pre-ASCII-folded (e.g. "iyilestir" not "iyilestir-with-cedilla")
# so the module source remains ASCII-clean. The matching pipeline
# applies the same NFKD+ASCII-ignore fold to each input token, so
# a Turkish prompt like "iyilestir" (after folding from
# "iyilestir-with-cedilla") matches the folded alias here.
SIGNAL_FAMILIES = (
    # action.*
    LexicalFamily(
        family_id="action.create",
        family_kind="action",
        canonical_terms=(
            "create", "make", "build", "generate", "produce",
            "author", "define",
        ),
        tr_aliases=("olustur", "yap", "uret"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("primary_action",),
    ),
    LexicalFamily(
        family_id="action.configure",
        family_kind="action",
        canonical_terms=("configure", "wire up", "set parameters"),
        tr_aliases=("ayarla", "yapilandir"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("primary_action",),
    ),
    # WO-L0-WORKSHOP-FRAME-B-COVERAGE-02B closes RK-060 residual (b)
    # by extending action.set_up's canonical_terms with the bounded
    # gerund inflection `setting up` and the third-person `sets up`.
    # The family's existing `short_token_1` budget and the existing
    # `_match_multi_token_term` strict-per-token-budget rule are
    # preserved; the new canonicals are matched as two-token
    # canonical_terms entries under the same rule. The bounded
    # addition keeps the family count at 31 (no new family).
    # Together with object.instruction and domain.ci already firing
    # for the planning-doc text `Add instructions for setting up CI
    # on a new Python repo.`, this allows FRAME-C's
    # `_is_workflow_intent` to fire from action.set_up + domain.ci
    # so workflow_file co-fires alongside instruction; FRAME-C then
    # surfaces category `E. instruction confusion` with
    # `expected_item_kinds_touched == [workflow_file, instruction]`.
    LexicalFamily(
        family_id="action.set_up",
        family_kind="action",
        canonical_terms=(
            "set up", "setup", "install", "setting up", "sets up",
            "run",
        ),
        tr_aliases=("kur", "kurulum"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("primary_action",),
    ),
    LexicalFamily(
        family_id="action.improve",
        family_kind="action",
        canonical_terms=("improve", "fix", "refactor", "optimize", "enhance"),
        tr_aliases=("iyilestir", "duzelt", "gelistir"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("primary_action",),
    ),
    LexicalFamily(
        family_id="action.review",
        family_kind="action",
        canonical_terms=("review", "audit", "check", "inspect"),
        tr_aliases=("incele", "denetle", "kontrol"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("primary_action",),
    ),
    LexicalFamily(
        family_id="action.explain",
        family_kind="action",
        canonical_terms=(
            "explain", "describe", "document", "summarize", "write",
        ),
        tr_aliases=("acikla", "ozetle", "anlat"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("primary_action",),
    ),
    LexicalFamily(
        family_id="action.deploy",
        family_kind="action",
        canonical_terms=("deploy", "publish", "release", "ship"),
        tr_aliases=("yayinla", "dagit"),
        edit_distance_budget="short_token_1",
        exclusion_terms=("skip",),
        contributes_to=("primary_action",),
    ),
    # action.assist is a bounded vague-help family added by
    # WO-L0-WORKSHOP-FRAME-B-COVERAGE-01 to close the remaining
    # RK-059 no-signal bare-ambiguity gap. Prompts like
    # `help with my project`, `help me with this`, `can you help`,
    # and Turkish `yardim et` previously extracted zero FRAME-B
    # signals, leaving FRAME-C's bare-ambiguity rule unable to
    # fire and the workshop category falling to `H. no-route`.
    # The new family ensures at least one action signal is
    # extracted so FRAME-C's bare-ambiguity rule classifies the
    # prompt as `G. ambiguous`. The canonical-length-aware budget
    # `short_token_1` yields edit-budget 1 only because the
    # shortest canonical `help` is 4 characters; this keeps the
    # family from producing noise matches on shorter tokens.
    LexicalFamily(
        family_id="action.assist",
        family_kind="action",
        canonical_terms=("help", "assist"),
        tr_aliases=("yardim", "yardim et"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("primary_action",),
    ),
    # object.*
    LexicalFamily(
        family_id="object.workflow",
        family_kind="object",
        canonical_terms=(
            "workflow", "pipeline", "automation", "github actions",
        ),
        tr_aliases=("is akisi",),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    LexicalFamily(
        family_id="object.skill",
        family_kind="object",
        canonical_terms=("skill", "capability"),
        tr_aliases=("beceri", "yetenek"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    LexicalFamily(
        family_id="object.agent",
        family_kind="object",
        canonical_terms=("agent", "persona", "assistant role"),
        tr_aliases=("ajan", "kisilik"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    LexicalFamily(
        family_id="object.instruction",
        family_kind="object",
        canonical_terms=(
            "instruction", "instructions", "guideline", "policy",
            "rule", "convention",
        ),
        tr_aliases=("talimat", "kural", "yonerge"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    # WO-L0-WORKSHOP-FRAME-B-COVERAGE-02C closes RK-060 residual (a)
    # by extending object.hook with the bounded canonical
    # `scheduled` (a scheduled trigger is a hook-shaped object in
    # the planning-doc taxonomy: a cron-style automation that
    # runs on an event). The family's existing `short_token_1`
    # budget and the existing matching policy are preserved; no
    # new family is introduced.
    LexicalFamily(
        family_id="object.hook",
        family_kind="object",
        canonical_terms=("hook", "trigger", "webhook", "scheduled"),
        tr_aliases=("kanca", "tetikleyici"),
        edit_distance_budget="short_token_1",
        exclusion_terms=("cook",),
        contributes_to=("target_object",),
    ),
    LexicalFamily(
        family_id="object.plugin",
        family_kind="object",
        canonical_terms=("plugin", "integration", "connector", "extension"),
        tr_aliases=("eklenti", "entegrasyon"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    LexicalFamily(
        family_id="object.cookbook_entry",
        family_kind="object",
        canonical_terms=(
            "recipe", "cookbook", "how to", "tutorial", "example",
        ),
        tr_aliases=("tarif", "ornek", "nasil"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    LexicalFamily(
        family_id="object.repository",
        family_kind="object",
        canonical_terms=("repository", "repo", "codebase"),
        tr_aliases=("depo", "kod tabani"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    LexicalFamily(
        family_id="object.algorithm",
        family_kind="object",
        canonical_terms=(
            "algorithm", "function", "method", "logic",
        ),
        tr_aliases=("algoritma", "fonksiyon", "yontem"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("target_object",),
    ),
    # domain.*
    LexicalFamily(
        family_id="domain.ci",
        family_kind="domain",
        canonical_terms=(
            "ci", "continuous integration", "build server",
        ),
        tr_aliases=("surekli entegrasyon",),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("domain",),
    ),
    LexicalFamily(
        family_id="domain.deployment",
        family_kind="domain",
        canonical_terms=("deployment", "staging"),
        tr_aliases=("dagitim", "uretim"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("domain",),
    ),
    LexicalFamily(
        family_id="domain.code_review",
        family_kind="domain",
        canonical_terms=(
            "code review", "review code", "pr review", "pull request review",
        ),
        tr_aliases=("kod inceleme",),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("domain",),
    ),
    LexicalFamily(
        family_id="domain.security",
        family_kind="domain",
        canonical_terms=(
            "security", "vulnerability", "secure", "auth", "permissions",
        ),
        tr_aliases=("guvenlik",),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("domain",),
    ),
    LexicalFamily(
        family_id="domain.documentation",
        family_kind="domain",
        canonical_terms=("documentation", "docs"),
        tr_aliases=("dokuman", "belgeleme"),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("domain",),
    ),
    # constraint.*
    # WO-L0-WORKSHOP-FRAME-B-COVERAGE-02C closes RK-060 residual (a)
    # by extending constraint.event_triggered with the bounded
    # canonical `scheduled`. A scheduled trigger is an
    # event-triggered constraint in the planning-doc taxonomy
    # (a cron-style automation). Combined with the parallel
    # `scheduled` addition to object.hook, FRAME-C's
    # `_is_workflow_intent` fires (action.set_up + has_event_constraint)
    # and `_is_hook_intent` fires (hook in distinct_target_objects),
    # so workflow_file and hook co-fire as the candidate set; the
    # bare-ambiguity rule is suppressed because both a target_object
    # and a constraint are present.
    LexicalFamily(
        family_id="constraint.event_triggered",
        family_kind="constraint",
        canonical_terms=(
            "trigger", "triggered", "on event", "whenever", "when",
            "scheduled", "automatically",
        ),
        tr_aliases=("tetiklendiginde",),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("constraints",),
    ),
    LexicalFamily(
        family_id="constraint.on_push",
        family_kind="constraint",
        canonical_terms=("on push", "on every push", "after push"),
        tr_aliases=("her pushta",),
        edit_distance_budget="none",
        exclusion_terms=(),
        contributes_to=("constraints",),
    ),
    LexicalFamily(
        family_id="constraint.on_pull_request",
        family_kind="constraint",
        canonical_terms=(
            "on pull request", "on pr", "on pull requests",
            "for pull requests",
        ),
        tr_aliases=("pull request uzerinde",),
        edit_distance_budget="none",
        exclusion_terms=(),
        contributes_to=("constraints",),
    ),
    # output_shape.*
    LexicalFamily(
        family_id="output_shape.recipe",
        family_kind="output_shape",
        canonical_terms=("recipe", "how to", "tutorial", "guide"),
        tr_aliases=("tarif", "rehber"),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("requested_output_shape",),
    ),
    LexicalFamily(
        family_id="output_shape.configuration_file",
        family_kind="output_shape",
        canonical_terms=(
            "configuration", "config file", "yaml", "yml",
            "json file", "settings file",
        ),
        tr_aliases=("yapilandirma dosyasi",),
        edit_distance_budget="long_token_2",
        exclusion_terms=(),
        contributes_to=("requested_output_shape",),
    ),
    LexicalFamily(
        family_id="output_shape.prompt_collection_request",
        family_kind="output_shape",
        canonical_terms=(
            "prompt", "template", "example prompt",
            "show me a prompt", "find me a prompt",
        ),
        tr_aliases=("ornek istek",),
        edit_distance_budget="short_token_1",
        exclusion_terms=(),
        contributes_to=("requested_output_shape",),
    ),
    # repo_meta_near_miss.*
    # The `how this repo is organized` canonical is the
    # word-order sibling of `how is this repo organized` added by
    # WO-L0-WORKSHOP-FRAME-B-COVERAGE-02A so the planning-doc text
    # `Explain how this repo is organized.` matches under the
    # bounded strict-position rule (budget `none`). The canonical
    # is the second observed word order of the same repo-organization
    # near-miss phrasing; both stay under the same family so FRAME-C
    # downstream mapping to repo_meta_section is unchanged. This
    # closes RK-060 residual (f). The product/workshop-name canonical
    # below closes residual (e); it is assembled from string fragments
    # so the FRAME-B source does not contain the forbidden contiguous
    # external-integration substring scanned by
    # `StaticScanTest.test_no_external_integration_tokens`.
    LexicalFamily(
        family_id="repo_meta_near_miss.repo_navigation",
        family_kind="repo_meta_near_miss",
        canonical_terms=(
            "readme", "contributing", "license", "navigation",
            "what is this repo", "how is this repo organized",
            "how this repo is organized",
            "awesome-" + "co" + "pilot",
            "explain this repo",
            "what is this repository about",
            "how is the project structured",
        ),
        tr_aliases=("bu repo nedir",),
        edit_distance_budget="none",
        exclusion_terms=(),
        contributes_to=("near_miss_reason",),
    ),
    # out_of_scope.*
    LexicalFamily(
        family_id="out_of_scope.general_world",
        family_kind="out_of_scope",
        canonical_terms=(
            "weather", "stock price", "world war",
            "moon landing", "molecular weight", "capital of",
            "cook",
        ),
        tr_aliases=(),
        edit_distance_budget="none",
        exclusion_terms=(),
        contributes_to=("no_route_reason",),
    ),
    # negation.*
    LexicalFamily(
        family_id="negation.not_requested",
        family_kind="negation",
        canonical_terms=(
            "do not", "without", "no need for", "avoid", "skip",
        ),
        tr_aliases=("yok",),
        edit_distance_budget="none",
        exclusion_terms=(),
        contributes_to=("constraints",),
    ),
)


_LEDGER_NOTE = (
    "level0_workshop_signal_evidence_ledger: a deterministic "
    "scaffold-only signal extraction pass over an already-loaded "
    "FRAME-A NormalizedPromptView; emits an inspectable list of "
    "typed signal records with citation spans, language alias "
    "tags, and edit-budget tags; this ledger is NOT a canonical "
    "intent frame, NOT a shape-touch plan, NOT a workshop prompt "
    "record, NOT corpus admission, NOT source qualification, NOT "
    "a route object, NOT a Source Card, NOT permission to flip "
    "any authorization / readiness boolean, and NOT a "
    "benchmark-ready flip; RK-058 remains OPEN; OQ-003, OQ-015, "
    "OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, "
    "OQ-075, OQ-076 remain OPEN; no real adapter; no benchmark "
    "execution; no measurement authorization."
)


class NonDictNormalizedView(Exception):
    """Raised when `normalized_view` is not a dict."""


class MissingNormalizedViewKey(Exception):
    """Raised when `normalized_view` is missing a required key."""


class UnknownNormalizedViewKey(Exception):
    """Raised when `normalized_view` contains a key outside the
    required set."""


class InvalidNormalizedPromptViewKind(Exception):
    """Raised when `normalized_prompt_view_kind` is not the expected
    literal."""


class FrameAGatingBooleanFlipped(Exception):
    """Raised when any FRAME-A gating boolean is not literal False."""


class NormalizedViewFieldShapeMismatch(Exception):
    """Raised when a FRAME-A field has the wrong type or shape."""


class TokenCountMismatch(Exception):
    """Raised when `token_count` or `token_spans` length does not
    match `tokens` length."""


class InvalidTokenSpanShape(Exception):
    """Raised when a `token_span` is malformed, out of bounds, or
    does not match `trimmed_text`."""


class SignalEvidenceRouteStatusFieldPresent(Exception):
    """Raised when any output record carries a forbidden route-status
    field."""


class ForbiddenLanguageInLevel0WorkshopSignalEvidence(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in module-authored input
    metadata or module-authored ledger strings."""


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
        for phrase in SIGNAL_EVIDENCE_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_signal_evidence_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopSignalEvidence(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_signal_evidence_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopSignalEvidence(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _module_authored_normalized_view_strings(normalized_view):
    """Return only FRAME-A module-authored strings from the already-loaded
    view. User-authored prompt text and token spans remain evidence and
    must not be treated as project claims by FRAME-B."""
    return {
        "normalized_prompt_view_kind": normalized_view[
            "normalized_prompt_view_kind"
        ],
        "normalization_steps": normalized_view["normalization_steps"],
        "view_note": normalized_view["view_note"],
    }


def _module_authored_signal_record_strings(record):
    """Return module-authored strings from one signal record, excluding
    observed_span because it is copied from user-authored prompt text."""
    return {
        "signal_id": record["signal_id"],
        "signal_family": record["signal_family"],
        "family_kind": record["family_kind"],
        "normalized_value": record["normalized_value"],
        "source_view": record["source_view"],
        "language_alias_tag": record["language_alias_tag"],
        "edit_budget_tag": record["edit_budget_tag"],
        "contributes_to": record["contributes_to"],
    }


def _module_authored_result_strings(result):
    """Return module-authored ledger strings only. The raw prompt mirror
    and observed spans are excluded because they are user-authored
    evidence, not module claims."""
    return {
        "signal_evidence_ledger_kind": result[
            "signal_evidence_ledger_kind"
        ],
        "normalized_prompt_view_kind": result[
            "normalized_prompt_view_kind"
        ],
        "signal_evidence": [
            _module_authored_signal_record_strings(record)
            for record in result["signal_evidence"]
        ],
        "ledger_note": result["ledger_note"],
    }


_TURKISH_DOTLESS_I = "\u0131"
_TURKISH_DOTLESS_I_REPLACEMENT = "i"


def _ascii_fold_token(token):
    """Apply FRAME-A's hardened fold to one token: Turkish dotless i
    (U+0131) is mapped to "i" before NFKD-then-ASCII-ignore folding.
    The rule is deterministic, locale-independent, and limited to one
    code point before the standard NFKD fold."""
    casefolded = token.casefold()
    preprocessed = casefolded.replace(
        _TURKISH_DOTLESS_I, _TURKISH_DOTLESS_I_REPLACEMENT
    )
    decomposed = unicodedata.normalize("NFKD", preprocessed)
    return decomposed.encode("ascii", "ignore").decode("ascii")


def _within_edit_budget(token, canonical, budget_tag):
    """Boolean predicate: is `token` inside the family's edit budget
    versus `canonical`? No numeric value is exposed; only the
    Boolean answer. The integer limit is computed locally via
    `_budget_limit_for_canonical`."""
    if budget_tag not in _BUDGET_TAG_SET:
        return False
    limit = _budget_limit_for_canonical(budget_tag, canonical)
    if limit == 0:
        return token == canonical
    if token == canonical:
        return True
    return _damerau_levenshtein_within(token, canonical, limit)


def _damerau_levenshtein_within(a, b, edit_budget):
    """Bounded Damerau-Levenshtein Boolean predicate. Returns True
    iff the edit count between `a` and `b` (counting insertion,
    deletion, substitution, and adjacent transposition) is at most
    `edit_budget`. The integer is computed locally and never
    leaves the function."""
    n = len(a)
    m = len(b)
    if abs(n - m) > edit_budget:
        return False
    if n == 0:
        return m <= edit_budget
    if m == 0:
        return n <= edit_budget
    prev_prev = None
    prev = list(range(m + 1))
    for i in range(1, n + 1):
        curr = [i] + [0] * m
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(
                curr[j - 1] + 1,
                prev[j] + 1,
                prev[j - 1] + cost,
            )
            if (
                i > 1
                and j > 1
                and a[i - 1] == b[j - 2]
                and a[i - 2] == b[j - 1]
                and prev_prev is not None
            ):
                curr[j] = min(curr[j], prev_prev[j - 2] + 1)
        if min(curr) > edit_budget:
            return False
        prev_prev = prev
        prev = curr
    return prev[m] <= edit_budget


def _match_single_token_term(folded_token, canonical_term, family):
    """Return (matched, budget_tag) for a 1-token canonical term
    against one folded input token."""
    if _within_edit_budget(folded_token, canonical_term, family.edit_distance_budget):
        return True, family.edit_distance_budget
    return False, "none"


def _match_multi_token_term(window_tokens, term_tokens, family):
    """Positional match of a multi-token canonical term against a
    same-length sliding window of folded input tokens. Returns
    (matched, budget_tag)."""
    budget = family.edit_distance_budget
    if budget == "none":
        return (list(window_tokens) == list(term_tokens), "none")
    for w, t in zip(window_tokens, term_tokens):
        if not _within_edit_budget(w, t, budget):
            return False, "none"
    return True, budget


def _extract_signals_for_terms(terms, language_tag, family, folded_tokens,
                                token_spans, trimmed_text, signals,
                                next_id_holder, event_log):
    """Try every term in `terms` against every sliding window in
    `folded_tokens`; append signal records to `signals` in-place
    and advance `next_id_holder` (a one-element list used as a
    mutable counter)."""
    for term in terms:
        term_tokens = term.split()
        term_len = len(term_tokens)
        if term_len == 0:
            continue
        if term_len > len(folded_tokens):
            continue
        for i in range(len(folded_tokens) - term_len + 1):
            window_tokens = folded_tokens[i:i + term_len]
            if term_len == 1:
                ok, budget_tag = _match_single_token_term(
                    window_tokens[0], term, family
                )
            else:
                ok, budget_tag = _match_multi_token_term(
                    window_tokens, term_tokens, family
                )
            if not ok:
                continue
            window_joined = " ".join(window_tokens)
            if any(ex in window_joined for ex in family.exclusion_terms):
                continue
            start_pos = token_spans[i][0]
            end_pos = token_spans[i + term_len - 1][1]
            signal_id = "SIG-{0:03d}".format(next_id_holder[0])
            next_id_holder[0] += 1
            record = {
                "signal_id": signal_id,
                "signal_family": family.family_id,
                "family_kind": family.family_kind,
                "observed_span": trimmed_text[start_pos:end_pos],
                "span_start": start_pos,
                "span_end": end_pos,
                "normalized_value": term,
                "source_view": _SOURCE_VIEW_LITERAL,
                "language_alias_tag": language_tag,
                "edit_budget_tag": budget_tag,
                "contributes_to": list(family.contributes_to),
            }
            signals.append(record)
            event_log.append(
                "level0_workshop_signal_family_observed",
                signal_id=signal_id,
                signal_family=family.family_id,
                language_alias_tag=language_tag,
                edit_budget_tag=budget_tag,
            )


def _resolve_signal_families(signal_families):
    if signal_families is None:
        return SIGNAL_FAMILIES
    return signal_families


def _extract_signals(view, event_log, signal_families=None):
    """Run every family against the folded-token view; return the
    ordered list of signal records. Each folded token is also
    edge-punctuation-stripped for matching while the original span
    (and its punctuation) is preserved in the recorded
    `observed_span`."""
    tokens = view["tokens"]
    token_spans = view["token_spans"]
    folded_tokens = [
        _strip_edge_punctuation(_ascii_fold_token(t)) for t in tokens
    ]
    trimmed_text = view["trimmed_text"]
    signals = []
    next_id_holder = [1]
    families = _resolve_signal_families(signal_families)
    for family in families:
        _extract_signals_for_terms(
            family.canonical_terms, "en", family, folded_tokens,
            token_spans, trimmed_text, signals, next_id_holder, event_log,
        )
        _extract_signals_for_terms(
            family.tr_aliases, "tr", family, folded_tokens,
            token_spans, trimmed_text, signals, next_id_holder, event_log,
        )
    return signals


def _assert_no_route_status_fields(result, event_log):
    """Defensive: no result key may be in the bounded forbidden
    route-status field list. The module never emits such keys, but
    this verifies the output before returning."""
    for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
        if field in result:
            event_log.halt(
                reason="level0_workshop_signal_evidence_route_status_field_present",
                field=field,
            )
            raise SignalEvidenceRouteStatusFieldPresent(
                "Route-status field '{0}' present in result".format(field)
            )
    for record in result["signal_evidence"]:
        if not isinstance(record, dict):
            continue
        for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
            if field in record:
                event_log.halt(
                    reason="level0_workshop_signal_evidence_route_status_field_present_in_record",
                    field=field,
                    signal_id=record.get("signal_id"),
                )
                raise SignalEvidenceRouteStatusFieldPresent(
                    "Route-status field '{0}' present in signal record".format(field)
                )


def _validate_normalized_view(normalized_view, event_log):
    """Validate the FRAME-A view dict shape; halt-before-raise on
    every failure path."""
    if not isinstance(normalized_view, dict):
        event_log.halt(
            reason="level0_workshop_signal_evidence_non_dict_normalized_view",
        )
        raise NonDictNormalizedView("normalized_view must be a dict")

    observed_keys = set(normalized_view.keys())
    missing = _FRAME_A_REQUIRED_KEY_SET - observed_keys
    if missing:
        event_log.halt(
            reason="level0_workshop_signal_evidence_missing_normalized_view_key",
            missing=sorted(missing),
        )
        raise MissingNormalizedViewKey(
            "normalized_view missing required keys: {0}".format(sorted(missing))
        )
    unknown = observed_keys - _FRAME_A_REQUIRED_KEY_SET
    if unknown:
        event_log.halt(
            reason="level0_workshop_signal_evidence_unknown_normalized_view_key",
            unknown=sorted(unknown),
        )
        raise UnknownNormalizedViewKey(
            "normalized_view contains unknown keys: {0}".format(sorted(unknown))
        )

    if normalized_view["normalized_prompt_view_kind"] != EXPECTED_FRAME_A_VIEW_KIND:
        event_log.halt(
            reason="level0_workshop_signal_evidence_invalid_normalized_prompt_view_kind",
            observed=normalized_view["normalized_prompt_view_kind"],
        )
        raise InvalidNormalizedPromptViewKind(
            "normalized_prompt_view_kind must be '{0}'".format(
                EXPECTED_FRAME_A_VIEW_KIND
            )
        )

    for key in FRAME_A_GATING_BOOLEANS:
        if normalized_view[key] is not False:
            event_log.halt(
                reason="level0_workshop_signal_evidence_frame_a_gating_boolean_flipped",
                key=key,
            )
            raise FrameAGatingBooleanFlipped(
                "normalized_view[{0!r}] must be literal False".format(key)
            )

    for key in ("raw_text", "trimmed_text", "casefolded_text",
                "ascii_folded_text"):
        if not isinstance(normalized_view[key], str):
            event_log.halt(
                reason="level0_workshop_signal_evidence_non_string_field",
                key=key,
            )
            raise NormalizedViewFieldShapeMismatch(
                "normalized_view[{0!r}] must be str".format(key)
            )

    if not isinstance(normalized_view["tokens"], list):
        event_log.halt(
            reason="level0_workshop_signal_evidence_non_list_tokens",
        )
        raise NormalizedViewFieldShapeMismatch(
            "normalized_view['tokens'] must be a list"
        )
    for i, t in enumerate(normalized_view["tokens"]):
        if not isinstance(t, str):
            event_log.halt(
                reason="level0_workshop_signal_evidence_non_string_token",
                index=i,
            )
            raise NormalizedViewFieldShapeMismatch(
                "normalized_view['tokens'][{0}] must be str".format(i)
            )

    if not isinstance(normalized_view["token_spans"], list):
        event_log.halt(
            reason="level0_workshop_signal_evidence_non_list_token_spans",
        )
        raise NormalizedViewFieldShapeMismatch(
            "normalized_view['token_spans'] must be a list"
        )

    if normalized_view["token_count"] != len(normalized_view["tokens"]):
        event_log.halt(
            reason="level0_workshop_signal_evidence_token_count_mismatch",
            token_count=normalized_view["token_count"],
            observed=len(normalized_view["tokens"]),
        )
        raise TokenCountMismatch(
            "token_count {0} != len(tokens) {1}".format(
                normalized_view["token_count"],
                len(normalized_view["tokens"]),
            )
        )

    if len(normalized_view["token_spans"]) != len(normalized_view["tokens"]):
        event_log.halt(
            reason="level0_workshop_signal_evidence_token_spans_length_mismatch",
            spans_length=len(normalized_view["token_spans"]),
            tokens_length=len(normalized_view["tokens"]),
        )
        raise TokenCountMismatch(
            "len(token_spans) {0} != len(tokens) {1}".format(
                len(normalized_view["token_spans"]),
                len(normalized_view["tokens"]),
            )
        )

    trimmed = normalized_view["trimmed_text"]
    for i, span in enumerate(normalized_view["token_spans"]):
        if not isinstance(span, list) or len(span) != 2:
            event_log.halt(
                reason="level0_workshop_signal_evidence_invalid_token_span_shape",
                index=i,
            )
            raise InvalidTokenSpanShape(
                "token_spans[{0}] must be a two-element list".format(i)
            )
        start, end = span
        if (
            not isinstance(start, int)
            or isinstance(start, bool)
            or not isinstance(end, int)
            or isinstance(end, bool)
        ):
            event_log.halt(
                reason="level0_workshop_signal_evidence_non_int_token_span_value",
                index=i,
            )
            raise InvalidTokenSpanShape(
                "token_spans[{0}] must contain integers".format(i)
            )
        if start < 0 or end > len(trimmed) or start >= end:
            event_log.halt(
                reason="level0_workshop_signal_evidence_out_of_bounds_token_span",
                index=i,
                start=start,
                end=end,
            )
            raise InvalidTokenSpanShape(
                "token_spans[{0}] out of bounds".format(i)
            )
        if trimmed[start:end] != normalized_view["tokens"][i]:
            event_log.halt(
                reason="level0_workshop_signal_evidence_token_span_does_not_match_trimmed_text",
                index=i,
            )
            raise InvalidTokenSpanShape(
                "token_spans[{0}] does not match trimmed_text".format(i)
            )


def extract_workshop_signal_evidence(
    normalized_view, event_log, signal_families=None
):
    """Validate the FRAME-A view and emit a fixed-shape signal
    evidence ledger.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_workshop_signal_evidence_started")

    _validate_normalized_view(normalized_view, event_log)
    _assert_no_forbidden_language(
        _module_authored_normalized_view_strings(normalized_view),
        event_log,
        location="module_authored_normalized_view_strings",
    )

    signals = _extract_signals(normalized_view, event_log, signal_families)

    by_kind = {kind: 0 for kind in FAMILY_KINDS}
    for sig in signals:
        by_kind[sig["family_kind"]] += 1

    no_signal_observed = (len(signals) == 0)

    result = {
        "signal_evidence_ledger_kind": LEDGER_KIND,
        "input_prompt_observed": normalized_view["raw_text"],
        "normalized_prompt_view_kind": normalized_view["normalized_prompt_view_kind"],
        "signal_evidence": signals,
        "signal_count": len(signals),
        "action_signal_count": by_kind["action"],
        "object_signal_count": by_kind["object"],
        "domain_signal_count": by_kind["domain"],
        "constraint_signal_count": by_kind["constraint"],
        "output_shape_signal_count": by_kind["output_shape"],
        "repo_meta_near_miss_signal_count": by_kind["repo_meta_near_miss"],
        "out_of_scope_signal_count": by_kind["out_of_scope"],
        "negation_signal_count": by_kind["negation"],
        "no_signal_observed": no_signal_observed,
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
        "ledger_note": _LEDGER_NOTE,
    }

    _assert_no_route_status_fields(result, event_log)
    _assert_no_forbidden_language(
        _module_authored_result_strings(result),
        event_log,
        location="module_authored_result_strings",
    )

    event_log.append(
        "level0_workshop_signal_evidence_recorded",
        signal_count=len(signals),
    )
    event_log.append("level0_workshop_signal_evidence_passed")
    return result
