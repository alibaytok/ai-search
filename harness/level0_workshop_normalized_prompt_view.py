"""Level 0B workshop normalized-prompt-view + input-guard scaffold.

WO-L0-WORKSHOP-FRAME-A adds the first stage of the Level 0B Intent
Core: a deterministic NormalizedPromptView + InputGuard that
accepts one free-text user prompt and emits a fixed-shape dict
containing the raw text, trimmed text, casefolded text, an
ASCII-folded view, a token list, and per-token spans into the
trimmed text.

This module is the upstream foundation for the future
Evidence-Traced Intent Frame Parser. It does NOT extract signals,
synthesize a CanonicalIntentFrame, build a ShapeTouchPlan, create
route or workflow candidates, qualify a source, admit a corpus,
retrieve, embed, vectorize, call any provider or external API,
and does NOT claim universal intent understanding, production
readiness, completeness, or benchmark readiness. Those concerns
belong to WO-L0-WORKSHOP-FRAME-B and -C.

This module performs no file IO, no network call, no URL fetch /
download / crawl, no PDF text extraction, no hash computation, no
external process or external shell execution, and no integration
with editor extensions, chat plugins, third-party model APIs, or
external collaborator tools. It uses only the Python standard
library (`unicodedata`, `re`).

ASCII folding is deterministic and documented. It first maps the
Turkish dotless-i character to ASCII `i`, then applies the NFKD
ASCII-ignore fold:

    ascii_folded_text = (
        unicodedata.normalize("NFKD", casefolded_text.translate(...))
        .encode("ascii", "ignore")
        .decode("ascii")
    )

NFKD decomposition splits each combined character into its base
plus combining marks; ASCII-encoding with `errors="ignore"` then
drops the non-ASCII combining marks while preserving the base
ASCII letter. Turkish dotless-i (`U+0131`) has no ASCII base
under NFKD, so FRAME-A maps it explicitly before the NFKD pass.
Characters with no ASCII base and no explicit mapping are
dropped. This is a deterministic ASCII signal view for the
intent-mapping use case; it is not a translation and it is not a
lossless text representation.

Tokenization is deterministic: the trimmed text is split on a
single regex `[\\s]+` for whitespace boundaries; punctuation
characters at token boundaries are kept attached to the token they
abut (this packet does NOT strip or reorder punctuation) and are
exposed verbatim in `tokens`. Span positions point into
`trimmed_text` (not into raw_text or casefolded_text).

The Constraints v1 non-claim constraint carries forward: this
module does not claim any observed token, span, fold, or count is
sufficient, necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded output key set, the bounded
normalization-step list, the bounded `MAX_PROMPT_LENGTH`, and the
deterministic ASCII-folding rule are bounded by
WO-L0-WORKSHOP-FRAME-A and are NOT claimed exhaustive.

Public surface:

    build_level0_workshop_normalized_prompt_view(
        input_prompt, event_log
    ) -> dict

All seven gating booleans (`route_created`, `selection_made`,
`measurement_authorized`, `real_benchmark_authorized`,
`real_benchmark_ready`, `source_qualification_authorized`,
`corpus_admission_authorized`) are literal False on every emitted
path. Halt paths raise named exceptions before any output dict is
built.
"""

import re
import unicodedata

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


VIEW_OUTPUT_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES


ALLOWED_OUTPUT_KEYS = (
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


_VIEW_KIND = "level0_workshop_normalized_prompt_view"


MAX_PROMPT_LENGTH = 2048


NORMALIZATION_STEPS = (
    "outer_whitespace_trim",
    "unicode_casefold",
    "turkish_dotless_i_then_nfkd_ascii_ignore_fold",
    "whitespace_split_tokenization_with_spans",
)


_WHITESPACE_PATTERN = re.compile(r"\s+")


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


_VIEW_NOTE = (
    "level0_workshop_normalized_prompt_view: a deterministic "
    "scaffold-only normalization pass over one free-text user "
    "prompt; emits raw / trimmed / casefolded / ascii-folded "
    "views plus a token list and per-token spans into the "
    "trimmed text; this view is NOT signal extraction, NOT a "
    "canonical intent frame, NOT a shape-touch plan, NOT corpus "
    "admission, NOT source qualification, NOT a route object, NOT "
    "a Source Card, NOT permission to flip any authorization / "
    "readiness boolean, and NOT a benchmark-ready flip; RK-058 "
    "remains OPEN; OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, "
    "OQ-049, OQ-056, OQ-057, OQ-070, OQ-075, OQ-076 remain OPEN; "
    "no real adapter; no benchmark execution; no measurement "
    "authorization."
)


class NonStringInputPrompt(Exception):
    """Raised when `input_prompt` is not a string."""


class EmptyInputPrompt(Exception):
    """Raised when `input_prompt` is empty (zero-length) before
    trimming."""


class WhitespaceOnlyInputPrompt(Exception):
    """Raised when `input_prompt` is non-empty but trims to an empty
    string."""


class InputPromptExceedsMaxLength(Exception):
    """Raised when `input_prompt` length exceeds `MAX_PROMPT_LENGTH`."""


class ForbiddenLanguageInLevel0WorkshopNormalizedPromptView(Exception):
    """Raised when a forbidden phrase from `FORBIDDEN_PHRASES` or
    `FORBIDDEN_CLAIM_PHRASES` appears in a module-authored emitted
    string. User-authored prompt text is preserved as input evidence
    and is not treated as a project claim."""


_ASCII_FOLD_TRANSLATION = str.maketrans({
    "\u0131": "i",
})


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
        for phrase in VIEW_OUTPUT_FORBIDDEN_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_normalized_prompt_view_forbidden_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopNormalizedPromptView(
                    "Forbidden phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                event_log.halt(
                    reason="level0_workshop_normalized_prompt_view_forbidden_claim_phrase",
                    location=location,
                    phrase=phrase,
                )
                raise ForbiddenLanguageInLevel0WorkshopNormalizedPromptView(
                    "Forbidden claim phrase '{0}' found in {1}".format(
                        phrase, location
                    )
                )


def _ascii_fold(casefolded_text):
    """Apply the deterministic NFKD-then-ASCII-ignore fold."""
    translated = casefolded_text.translate(_ASCII_FOLD_TRANSLATION)
    decomposed = unicodedata.normalize("NFKD", translated)
    return decomposed.encode("ascii", "ignore").decode("ascii")


def _module_authored_strings(result):
    """Return only module-authored strings for forbidden-language
    scanning. Raw prompt views are user-authored evidence and may
    legitimately contain words that are forbidden for project claims."""
    return {
        "normalized_prompt_view_kind": result[
            "normalized_prompt_view_kind"
        ],
        "normalization_steps": list(result["normalization_steps"]),
        "view_note": result["view_note"],
    }


def _tokenize_with_spans(trimmed_text):
    """Split `trimmed_text` on runs of whitespace and return
    (tokens, spans). Spans are (start, end) into `trimmed_text`;
    multiple-whitespace runs do NOT produce empty tokens.
    """
    tokens = []
    spans = []
    if not trimmed_text:
        return tokens, spans

    pos = 0
    text_length = len(trimmed_text)
    while pos < text_length:
        match = _WHITESPACE_PATTERN.search(trimmed_text, pos)
        if match is None:
            tokens.append(trimmed_text[pos:text_length])
            spans.append((pos, text_length))
            break
        if match.start() > pos:
            tokens.append(trimmed_text[pos:match.start()])
            spans.append((pos, match.start()))
        pos = match.end()
    return tokens, spans


def _assert_no_route_status_fields(result, event_log):
    """Defensive: no result key may be in the bounded forbidden
    route-status field list. The module never emits such keys, but
    this verifies the output before returning."""
    for field in _FORBIDDEN_ROUTE_STATUS_FIELDS:
        if field in result:
            event_log.halt(
                reason="level0_workshop_normalized_prompt_view_route_status_field_present",
                field=field,
            )
            raise ForbiddenLanguageInLevel0WorkshopNormalizedPromptView(
                "Route-status field '{0}' present in result".format(field)
            )


def build_level0_workshop_normalized_prompt_view(input_prompt, event_log):
    """Validate one free-text prompt and emit a fixed-shape
    NormalizedPromptView dict.

    See module docstring for the full non-claim constraint.
    """
    event_log.append("level0_workshop_normalized_prompt_view_started")

    if not isinstance(input_prompt, str):
        event_log.halt(
            reason="level0_workshop_normalized_prompt_view_non_string_input_prompt",
        )
        raise NonStringInputPrompt(
            "input_prompt must be a string"
        )

    if len(input_prompt) == 0:
        event_log.halt(
            reason="level0_workshop_normalized_prompt_view_empty_input_prompt",
        )
        raise EmptyInputPrompt(
            "input_prompt must not be empty"
        )

    if len(input_prompt) > MAX_PROMPT_LENGTH:
        event_log.halt(
            reason="level0_workshop_normalized_prompt_view_input_prompt_exceeds_max_length",
            length=len(input_prompt),
            max_prompt_length=MAX_PROMPT_LENGTH,
        )
        raise InputPromptExceedsMaxLength(
            "input_prompt length {0} exceeds MAX_PROMPT_LENGTH {1}".format(
                len(input_prompt), MAX_PROMPT_LENGTH
            )
        )

    trimmed_text = input_prompt.strip()
    if len(trimmed_text) == 0:
        event_log.halt(
            reason="level0_workshop_normalized_prompt_view_whitespace_only_input_prompt",
        )
        raise WhitespaceOnlyInputPrompt(
            "input_prompt must contain at least one non-whitespace character"
        )

    casefolded_text = trimmed_text.casefold()
    ascii_folded_text = _ascii_fold(casefolded_text)
    tokens, token_spans = _tokenize_with_spans(trimmed_text)

    result = {
        "normalized_prompt_view_kind": _VIEW_KIND,
        "raw_text": input_prompt,
        "trimmed_text": trimmed_text,
        "casefolded_text": casefolded_text,
        "ascii_folded_text": ascii_folded_text,
        "tokens": tokens,
        "token_spans": [list(span) for span in token_spans],
        "token_count": len(tokens),
        "max_prompt_length": MAX_PROMPT_LENGTH,
        "normalization_steps": list(NORMALIZATION_STEPS),
        "selection_made": False,
        "measurement_authorized": False,
        "real_benchmark_authorized": False,
        "real_benchmark_ready": False,
        "source_qualification_authorized": False,
        "corpus_admission_authorized": False,
        "route_created": False,
        "view_note": _VIEW_NOTE,
    }

    _assert_no_route_status_fields(result, event_log)
    _assert_no_forbidden_language(
        _module_authored_strings(result),
        event_log,
        location="module_authored_result_strings",
    )

    event_log.append("level0_workshop_normalized_prompt_view_completed")
    return result
