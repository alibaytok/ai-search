# 69. Level 0B Workshop Normalized Prompt View (WO-L0-WORKSHOP-FRAME-A)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-WORKSHOP-FRAME-A

## Authority

This boundary document records the scaffold surface of
`harness/level0_workshop_normalized_prompt_view.py`. It does NOT
modify canonical authority. Canonical authority remains with
`ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. On conflict, canonical wins.

The Mandatory Priority-Miss Check from
`ai-search/00-claude-scope-prompt-template.md` precedes Section L
on every new scope prompt in this project; it was applied at the
top of this packet and recorded no higher-priority missed scope.

## Scope and Boundary

WO-L0-WORKSHOP-FRAME-A added the first stage of the Level 0B
Intent Core: a deterministic NormalizedPromptView + InputGuard
that accepts one free-text user prompt and emits a fixed-shape
dict containing raw / trimmed / casefolded / ascii-folded views
plus a token list and per-token spans into the trimmed text.

This is the upstream foundation for the future Evidence-Traced
Intent Frame Parser (FRAME-B = SignalEvidence layer; FRAME-C =
CanonicalIntentFrame + ShapeTouchPlan + WorkshopPromptRecordAdapter).
FRAME-A does NOT extract signals, synthesize a frame, build a
shape-touch plan, create route or workflow candidates, qualify a
source, admit a corpus, retrieve, embed, vectorize, call any
provider or external API, or claim universal intent
understanding / production readiness / completeness / benchmark
readiness.

The module performs no file IO, no network call, no URL fetch /
download / crawl / browser automation, no PDF text extraction, no
hash computation, no external process spawning, and no
integration with editor extensions, chat plugins, third-party
model APIs, or external collaborator tools. It uses only the
Python standard library (`unicodedata` and `re`).

WO-L0-WORKSHOP-FRAME-A does NOT close RK-058. RK-058 names the
upstream gap (declared touched-kind fixtures masking absence of
durable prompt-text-to-intent capture); FRAME-A is Stage A of
three that addresses the gap. Full closure requires the FRAME-B
and FRAME-C packets plus signal-evidence tests, well beyond this
packet's scope. RK-058 is acknowledged here and remains OPEN.

Real-benchmark-ready remains NO.

## Public Surface

```
build_level0_workshop_normalized_prompt_view(
    input_prompt, event_log
) -> dict
```

The module imports only:

- `re` (Python standard library)
- `unicodedata` (Python standard library)
- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`

The module invokes NO prior-WO public function (verified by
static-scan test).

## Input

- `input_prompt`: a single free-text user prompt string. Non-ASCII
  input (Turkish, etc.) is accepted; ASCII folding produces the
  ascii-only view.
- `event_log`: an `EventLog` instance from `harness.event_log`.

## Constants

| Constant | Value |
|----------|-------|
| `MAX_PROMPT_LENGTH` | `2048` |
| `NORMALIZATION_STEPS` | `("outer_whitespace_trim", "unicode_casefold", "turkish_dotless_i_then_nfkd_ascii_ignore_fold", "whitespace_split_tokenization_with_spans")` |

`MAX_PROMPT_LENGTH` is bounded by WO-L0-WORKSHOP-FRAME-A and is
NOT claimed sufficient or recommended for any downstream
real-benchmark use.

## ASCII Folding Rule (deterministic, documented)

The ASCII fold first maps Turkish dotless-i (`U+0131`) to ASCII
`i`, then applies NFKD plus ASCII-ignore:

```python
ascii_folded_text = (
    unicodedata.normalize("NFKD", casefolded_text.translate(...))
    .encode("ascii", "ignore")
    .decode("ascii")
)
```

NFKD decomposes each combined character into its base plus
combining marks; ASCII-encoding with `errors="ignore"` then drops
the non-ASCII combining marks while preserving the base ASCII
letter. Turkish dotless-i has no ASCII base under NFKD, so
FRAME-A maps it explicitly before NFKD. Characters with no ASCII
base and no explicit mapping are dropped. The fold is
locale-independent and reproducible across Python 3
implementations.

Examples:

| Casefolded input | ASCII-folded output |
|------------------|---------------------|
| `"istanbul"` | `"istanbul"` |
| `"i" + U+0307 + "stanbul"` (casefold of U+0130 + `"stanbul"`; U+0130 = Turkish capital I with dot above; U+0307 = combining dot above) | `"istanbul"` |
| `"is akisi"` (already ASCII) | `"is akisi"` |
| casefolded Turkish `"Bir Is Akisi kur."` with escaped non-ASCII source characters | `"bir is akisi kur."` |

The fold is intentionally lossy for characters with no ASCII
base and no explicit mapping; this is documented as a known
limitation, not as a claim of correctness for any non-Latin
script. This packet does NOT claim the fold is sufficient for any
real benchmark use.

## Tokenization Rule

The trimmed text is split on runs of whitespace (Python regex
`\s+`). Punctuation characters at token boundaries are kept
attached to the token they abut. Multiple-whitespace runs do NOT
produce empty tokens. Each token has an exact `(start, end)` span
into `trimmed_text` such that
`trimmed_text[start:end] == token`. Spans are returned as
two-element lists for JSON-friendly serialization.

## Output Shape

Clean-pass output dict has exactly eighteen keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `normalized_prompt_view_kind` | str | `"level0_workshop_normalized_prompt_view"` |
| `raw_text` | str | input verbatim |
| `trimmed_text` | str | input with outer whitespace stripped |
| `casefolded_text` | str | `trimmed_text.casefold()` |
| `ascii_folded_text` | str | Turkish dotless-i mapping plus NFKD then ASCII-ignore fold of `casefolded_text` |
| `tokens` | list of str | whitespace-split tokens of `trimmed_text` |
| `token_spans` | list of `[start, end]` | spans into `trimmed_text` |
| `token_count` | int | `len(tokens)` |
| `max_prompt_length` | int | literal `2048` |
| `normalization_steps` | list of str | 4-entry bounded list |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `source_qualification_authorized` | bool | literal False |
| `corpus_admission_authorized` | bool | literal False |
| `route_created` | bool | literal False |
| `view_note` | str | bounded non-claim note literal |

## Validation Order (halt-before-raise)

1. `input_prompt` must be a string; else `NonStringInputPrompt`.
2. `input_prompt` must be non-empty (length > 0); else
   `EmptyInputPrompt`.
3. `len(input_prompt) <= MAX_PROMPT_LENGTH`; else
   `InputPromptExceedsMaxLength`.
4. `input_prompt.strip()` must be non-empty; else
   `WhitespaceOnlyInputPrompt`.
5. Build casefolded text, ASCII-folded text, tokens, spans.
6. Preserve user-authored prompt text in `raw_text`, `trimmed_text`,
   `casefolded_text`, `ascii_folded_text`, and `tokens` without
   treating user words as project claims.
7. Defensive route-status-field absence check on the result dict.
8. Forbidden-language scan over module-authored result strings only
   (`normalized_prompt_view_kind`, `normalization_steps`, and
   `view_note`); user-authored prompt fields are evidence input,
   not project-authored claims.

Every halt path records an `event_log.halt(reason=..., ...)`
event before raising.

## Forbidden Route-Status Fields

The result dict is checked for the eleven forbidden route-status
fields (`official`, `is_route`, `is_official_route`,
`selected_as_official`, `official_route_authorized`,
`route_authorized`, `production_route`, `selected_route`,
`executable`, `route_state`, `plane`). The module never emits
any of these; the defensive check protects against future
refactors.

## Static Scan

The module file contains none of:

- `open(`, `pathlib`
- `urllib`, `http.client`, `socket`
- `import requests`, `from requests`, `requests.`
- `subprocess`, `os.system`, `shutil`
- `hashlib`, `.hexdigest`, `.sha256`
- `def query`, `def search`, `def retrieve`, `def rank`
- `score`, `scoring`
- `copilot`, `waza`, `vscode`, `vs_code`, `openai`, `anthropic`,
  `claude_api`, `llm`
- `embedding(`, `vectorize(`, ` ann_`, `approximate_nearest`,
  `reranker(`, `rerank_`

The module file contains no name of any prior-WO public function
(WO-50 through WO-62 plus the four manual-seed L0 modules plus
the workshop derived-trace, workshop trace review, and existing
workshop user-intent mapper public functions). Module file
non-ASCII byte count is 0.

## What This Scaffold Does NOT Do

- Does NOT read any planning document at runtime.
- Does NOT fetch any URL, download any content, or crawl any
  source.
- Does NOT read any local file.
- Does NOT extract PDF text.
- Does NOT compute any hash via `hashlib` or any other library.
- Does NOT spawn external processes or shells.
- Does NOT integrate with editor extensions, chat plugins,
  third-party model APIs, or external collaborator tools.
- Does NOT invoke any prior-WO public function.
- Does NOT extract signals, synthesize a CanonicalIntentFrame,
  build a ShapeTouchPlan, or map to item-kind affinity. Those
  belong to FRAME-B and FRAME-C.
- Does NOT create or select route objects.
- Does NOT qualify sources.
- Does NOT admit corpus.
- Does NOT compute any similarity / distance / ranking / metric.
- Does NOT call any LLM / provider / external API / embedding /
  vector / ANN backend / reranker.
- Does NOT flip any of the seven gating booleans.
- Does NOT mutate input.
- Does NOT claim universal intent understanding, production
  readiness, completeness, or benchmark readiness.

## Test Surface

`harness/tests/test_level0_workshop_normalized_prompt_view.py`
contains 59 tests across the following test classes:

- `CleanAsciiPromptTest` (21) - output shape, fixed key set,
  literal kind / count / token / span fields, all seven literal-
  False gating booleans, view_note non-empty, started / completed
  events, no halt, no route-status fields in result.
- `TurkishPromptTest` (6) - non-ASCII input accepted; raw_text
  preserves the original; ascii_folded_text is ASCII-clean;
  deterministic across repeated calls; token count is positive;
  Turkish dotted capital I casefolds away; Turkish dotless-i
  folds to ASCII `i`.
- `TrimmingAndWhitespaceTest` (4) - outer whitespace stripped;
  multiple inner whitespace does not produce empty tokens;
  single-token prompt yields one span; punctuation kept attached.
- `TokenSpanTest` (3) - every span points into `trimmed_text`;
  spans are non-overlapping and ordered; spans length matches
  tokens length.
- `MaxLengthBoundaryTest` (2) - prompt at `MAX_PROMPT_LENGTH`
  accepted; prompt over `MAX_PROMPT_LENGTH` halts.
- `MalformedInputHaltTest` (6) - non-string halts; `None` halts;
  list halts; empty string halts; whitespace-only halts; halt
  event recorded before exception.
- `UserAuthoredInputPhraseTest` (1) - user-authored prompt text
  carrying project-forbidden claim language is preserved as input
  evidence and is not treated as a module-authored project claim.
- `InputImmutabilityTest` (1) - input string preserved verbatim
  in `raw_text`.
- `FixedShapeTest` (2) - exactly 18 output keys; all seven
  gating booleans literal False.
- `StaticScanTest` (13) - absence of file-IO, network, HTTP-
  library, subprocess / shell, hashlib, retrieval-verb, scoring,
  external-integration, embedding / vector / ANN / reranker
  tokens; absence of any prior-WO public function name including
  the existing workshop user-intent mapper public function;
  module file is ASCII.

## Non-Claim Constraints

WO-L0-WORKSHOP-FRAME-A does not claim any observed token, span,
fold, count, normalization step, or computed view is sufficient,
necessary, superior, best, complete, production-ready,
recommended, or selected. The bounded eighteen `ALLOWED_OUTPUT_KEYS`,
the bounded four-entry `NORMALIZATION_STEPS`, the bounded
`MAX_PROMPT_LENGTH` (2048), the deterministic Turkish-dotless-i
plus NFKD-then-ASCII-ignore folding rule, and the
whitespace-split tokenization rule are bounded by
WO-L0-WORKSHOP-FRAME-A and are NOT claimed exhaustive.

All DC-020 through DC-070 boundary invariants carry forward.
WO-L0-WORKSHOP-FRAME-A does not amend or broaden DC-003 through
DC-070. RK-058 is acknowledged and remains OPEN. RK-039 remains
active and is not duplicated. Real-benchmark-ready remains NO.
OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057,
OQ-070, OQ-075, OQ-076 remain OPEN.
