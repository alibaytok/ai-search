# 70. Level 0B Workshop SignalEvidence Layer (WO-L0-WORKSHOP-FRAME-B)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-WORKSHOP-FRAME-B

## Authority

This boundary document records the scaffold surface of
`harness/level0_workshop_signal_evidence.py`. It does NOT modify
canonical authority. Canonical authority remains with
`ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. On conflict, canonical wins.

The Mandatory Priority-Miss Check from
`ai-search/00-claude-scope-prompt-template.md` precedes Section L
on every new scope prompt in this project; it was applied at the
top of this packet and recorded no higher-priority missed scope.

## Scope and Boundary

WO-L0-WORKSHOP-FRAME-B is Stage B of the Level 0B Intent Core. It
consumes an already-loaded FRAME-A NormalizedPromptView dict and
emits a fixed-shape `signal_evidence_ledger` listing every
contributing signal as a typed record with citation span,
language alias tag, edit-budget tag, and `contributes_to` list.

Pipeline position:

```
PromptText
  -> FRAME-A NormalizedPromptView
  -> FRAME-B SignalEvidenceLedger    <-- this module
  -> FRAME-C CanonicalIntentFrame + ShapeTouchPlan
```

FRAME-B does NOT classify a frame, does NOT synthesize a
CanonicalIntentFrame, does NOT compute a ShapeTouchPlan, does NOT
emit a `workshop_prompt_record`, does NOT create or select route
objects, does NOT qualify a source, does NOT admit a corpus, does
NOT retrieve / embed / vectorize / call any provider or external
API, and does NOT claim universal intent understanding,
production readiness, completeness, or benchmark readiness. Those
concerns belong to FRAME-C and a future RK-058 closure packet.

WO-L0-WORKSHOP-FRAME-B does NOT close RK-058. RK-058 is
acknowledged and remains OPEN; closure requires FRAME-C + a
follow-up Codex-authorized packet. Real-benchmark-ready remains
NO.

## Public Surface

```
extract_workshop_signal_evidence(normalized_view, event_log) -> dict
```

The module imports only:

- `re` (Python standard library)
- `unicodedata` (Python standard library)
- `collections.namedtuple` (Python standard library)
- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`

The module invokes NO prior-WO public function (verified by
static-scan test). FRAME-A's `build_level0_workshop_normalized_prompt_view`
appears in tests only as a test-layer fixture builder; the module
under test does not call it.

## Inputs

- `normalized_view`: already-loaded clean-pass dict from FRAME-A
  with exactly eighteen keys per FRAME-A's contract.
- `event_log`: an `EventLog` instance from `harness.event_log`.

## ASCII Fold

FRAME-B applies FRAME-A's hardened fold per token:

- **Turkish dotless i (U+0131) is mapped to `"i"` before NFKD.**

Rationale: U+0131 is the only character in the Turkish alphabet
that does not decompose under NFKD. Every other Turkish character
(`U+015F`, `U+00E7`, `U+011F`, `U+00F6`, `U+00FC` and the
uppercase forms; `U+0130` casefolds to `i` + `U+0307` and
decomposes from there) folds correctly through pure NFKD +
ASCII-ignore. The single-character pre-fold restores U+0131 to
its ASCII base so Turkish prompts containing `U+0131` match the
family alias `"is akisi"` instead of collapsing to `"is aks"`.

The rule is deterministic, locale-independent, and limited to one
code point before NFKD folding. FRAME-B re-applies the same fold
per token so token matching is consistent with FRAME-A's
whole-text `ascii_folded_text`. The module source remains
ASCII-only (the U+0131 code point is referenced by Python escape
sequence in the module source, never as a literal character).

## Tokenization For Matching

FRAME-A's `tokens` and `token_spans` are reused verbatim. Each
folded token is additionally edge-punctuation-stripped (chars in
`.,!?;:"'()[]{}`) before family matching, so a tokenized form
like `"readme."` matches the family canonical term `"readme"`.
The recorded `observed_span` is derived from FRAME-A's
`token_spans` into the original `trimmed_text` and therefore
retains the punctuation; only the comparison form is stripped.

## Signal Family Model

Bounded ASCII-only signal families declared as a module-level
constant `SIGNAL_FAMILIES`. Each entry is a `LexicalFamily`
namedtuple with seven fields:

| Field | Type | Notes |
|-------|------|-------|
| `family_id` | str | dotted id like `"action.set_up"` |
| `family_kind` | str | one of the bounded eight FAMILY_KINDS |
| `canonical_terms` | tuple of str | English canonical forms |
| `tr_aliases` | tuple of str | ASCII-folded Turkish aliases |
| `edit_distance_budget` | str | one of `"none"`, `"short_token_1"`, `"long_token_2"` |
| `exclusion_terms` | tuple of str | tokens whose presence suppresses a match |
| `contributes_to` | tuple of str | future CIF field names this family informs |

The bounded eight `FAMILY_KINDS` are: `action`, `object`,
`domain`, `constraint`, `output_shape`, `repo_meta_near_miss`,
`out_of_scope`, `negation`.

## Edit-Budget Predicate

Typo tolerance is a deterministic Boolean predicate. No numeric
edit count appears in any output record; only the categorical
budget tag is emitted.

The integer edit limit per match is derived from the canonical
term length so short canonical terms cannot grant
disproportionately large tolerance:

| Budget tag | canonical len < 4 | 4 <= len < 6 | len >= 6 |
|------------|-------------------|--------------|----------|
| `none` | 0 | 0 | 0 |
| `short_token_1` | 0 | 1 | 1 |
| `long_token_2` | 0 | 1 | 2 |

This prevents noise matches such as `"me"` -> `"yml"` at
Damerau distance 2 or `"xxx"` -> `"fix"` at distance 2; both
canonical terms are shorter than the `_SHORT_CANONICAL_MIN_LEN`
of 4 and therefore force an exact match regardless of the
family's declared budget tag.

The bounded Damerau-Levenshtein predicate counts insertion,
deletion, substitution, and adjacent transposition.

## Signal Record Shape

Each signal record has exactly eleven fields, no extras:

| Field | Type |
|-------|------|
| `signal_id` | str (`"SIG-NNN"` 1-based 3-digit index, unique per ledger) |
| `signal_family` | str (e.g. `"action.set_up"`) |
| `family_kind` | str (one of `FAMILY_KINDS`) |
| `observed_span` | str (verbatim from `trimmed_text`) |
| `span_start` | int |
| `span_end` | int |
| `normalized_value` | str (the canonical term that matched) |
| `source_view` | str literal `"ascii_folded_text"` |
| `language_alias_tag` | str (`"en"`, `"tr"`, or `"none"`) |
| `edit_budget_tag` | str (one of `BUDGET_TAGS`) |
| `contributes_to` | list of str |

No record carries any of the eleven forbidden route-status fields
(`official`, `is_route`, `is_official_route`,
`selected_as_official`, `official_route_authorized`,
`route_authorized`, `production_route`, `selected_route`,
`executable`, `route_state`, `plane`). No record carries any
forbidden output field name (`ranking_performed`,
`scoring_performed`, `confidence`, `score`, `distance`,
`best_match`, `threshold`, `similarity`). A defensive output check
verifies this before return.

## Output Shape

Clean-pass output dict has exactly twenty-two keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `signal_evidence_ledger_kind` | str | `"level0_workshop_signal_evidence_ledger"` |
| `input_prompt_observed` | str | mirrored from `normalized_view["raw_text"]` |
| `normalized_prompt_view_kind` | str | mirrored from input |
| `signal_evidence` | list of dict | per-family-hit records |
| `signal_count` | int | `len(signal_evidence)` |
| `action_signal_count` | int | per-kind tally |
| `object_signal_count` | int | per-kind tally |
| `domain_signal_count` | int | per-kind tally |
| `constraint_signal_count` | int | per-kind tally |
| `output_shape_signal_count` | int | per-kind tally |
| `repo_meta_near_miss_signal_count` | int | per-kind tally |
| `out_of_scope_signal_count` | int | per-kind tally |
| `negation_signal_count` | int | per-kind tally |
| `no_signal_observed` | bool | True iff `signal_count == 0` |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `source_qualification_authorized` | bool | literal False |
| `corpus_admission_authorized` | bool | literal False |
| `route_created` | bool | literal False |
| `ledger_note` | str | bounded non-claim note literal |

## Validation Order (halt-before-raise)

1. `normalized_view` is a dict; else `NonDictNormalizedView`.
2. Required key presence; else `MissingNormalizedViewKey`.
3. Unknown key rejection; else `UnknownNormalizedViewKey`.
4. `normalized_prompt_view_kind` literal check; else
   `InvalidNormalizedPromptViewKind`.
5. All seven FRAME-A gating booleans literal False; else
   `FrameAGatingBooleanFlipped`.
6. String-shape checks on `raw_text`, `trimmed_text`,
   `casefolded_text`, `ascii_folded_text`; list-shape on
   `tokens` / `token_spans`; per-token string check; else
   `NormalizedViewFieldShapeMismatch`.
7. `token_count == len(tokens)` and
   `len(token_spans) == len(tokens)`; else `TokenCountMismatch`.
8. Per-span checks: two-element list of ints, in-bounds, matching
   the corresponding token in `trimmed_text`; else
   `InvalidTokenSpanShape`.
9. Module-authored input metadata forbidden-language scan. Raw
   prompt text, folded prompt text, tokens, and spans remain
   user-authored evidence and are not treated as project claims.
10. Signal extraction over every family x term x window.
11. Defensive route-status-field absence check on the result and
    every signal record; else
    `SignalEvidenceRouteStatusFieldPresent`.
12. Module-authored output string forbidden-language scan. The raw
    prompt mirror and per-signal `observed_span` values remain
    user-authored evidence and are not treated as project claims.

Every halt path records an `event_log.halt(reason=..., ...)`
event before raising.

## Required Events

- `level0_workshop_signal_evidence_started`
- `level0_workshop_signal_family_observed` (one per signal)
- `level0_workshop_signal_evidence_recorded`
- `level0_workshop_signal_evidence_passed`
- `halt` events with bounded reason names for every invalid input
  class

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
- `ranking_performed`, `scoring_performed`

The module file contains no name of any prior-WO public function
including `build_level0_workshop_normalized_prompt_view`,
`run_level0_workshop_derived_trace`, `run_level0_workshop_trace_review`,
`map_level0_workshop_user_intent`, and every WO-50 through WO-62
plus four manual-seed L0 public functions. Module file non-ASCII
byte count is 0.

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
- Does NOT synthesize a CanonicalIntentFrame, ShapeTouchPlan, or
  WorkshopPromptRecord (those belong to FRAME-C).
- Does NOT create or select route objects.
- Does NOT qualify sources.
- Does NOT admit corpus.
- Does NOT compute any similarity / distance / ranking / metric
  output field; bounded Damerau-Levenshtein integers are local to
  the predicate function and never emitted.
- Does NOT call any LLM / provider / external API / embedding /
  vector / ANN backend / reranker.
- Does NOT flip any of the seven gating booleans.
- Does NOT mutate input.
- Does NOT claim universal intent understanding, production
  readiness, completeness, or benchmark readiness.
- Does NOT close RK-058.

## Test Surface

`harness/tests/test_level0_workshop_signal_evidence.py` contains
97 tests across the following test classes:

- `CleanPassTest` (21) - output shape; fixed key set; literal
  kind; observed input mirror; per-kind count consistency; all
  seven literal-False gating booleans; ledger_note non-empty;
  started/recorded/passed events; no halt; no route-status field;
  no forbidden output field name.
- `SignalRecordShapeTest` (10) - per-record eleven-field shape;
  family_kind in bounded set; language_alias_tag in bounded set;
  edit_budget_tag in bounded set; source_view literal; per-record
  contributes_to list-of-strings; signal_id uniqueness and
  prefix; no route-status field per record; no forbidden output
  field name per record.
- `SpanVerifiabilityTest` (2) - every observed_span is a
  substring of trimmed_text by its recorded span; spans bounded
  by trimmed_text.
- `EnglishFamilyFireTest` (10) - canonical English phrasings
  fire the expected families.
- `VerbObjectDomainSentenceTest` (2) - full sentence fires
  action+object+domain together; multiple actions co-fire.
- `TurkishAliasFireTest` (3) - Turkish prompts fire action and
  object families with `language_alias_tag: "tr"` via FRAME-B's
  documented U+0131 pre-fold rule.
- `TypoToleranceTest` (5) - typos within budget fire; typos
  outside budget do not; no numeric distance leaks; budget tag
  recorded.
- `NoSignalPromptTest` (1) - unrecognizable prompt emits
  `no_signal_observed: True` and empty signal list.
- `CountFieldConsistencyTest` (5) - per-kind counts match
  per-record counts.
- `NegationContributesToConstraintsTest` (1) - negation records
  contribute to `constraints`.
- `DeterminismTest` (2) - same input yields same output (ids,
  families, counts); signal ids are 1-indexed and sequential.
- `InputValidationHaltTest` (14) - non-dict, missing key,
  unknown key, invalid view_kind, two boolean flips, non-string
  raw_text, non-list tokens, non-string token, token_count
  mismatch, token_spans length mismatch, span-text mismatch,
  out-of-bounds span, malformed span.
- `ForbiddenLanguageHaltTest` (4) - user-authored forbidden phrase /
  claim phrase text is preserved as evidence, while the same phrase
  classes in module-authored input metadata halt.
- `InputIsolationTest` (1) - input dict not mutated.
- `SignalFamilyConstantTest` (4) - every family has a known
  kind; every family has a known budget tag; family ids are
  unique; the minimum required families are all present.
- `StaticScanTest` (12) - absence of file-IO, network,
  HTTP-library, subprocess / shell, hashlib, retrieval-verb,
  scoring, forbidden output field name, embedding / vector /
  ANN / reranker, external-integration tokens; absence of any
  prior-WO public function name; module file is ASCII.

## Non-Claim Constraints

WO-L0-WORKSHOP-FRAME-B does not claim any signal, span, family,
alias tag, count, or budget tag is sufficient, necessary,
superior, best, complete, production-ready, recommended, or
selected. The bounded `SIGNAL_FAMILIES` tuple (30 families
covering the minimum required IDs), the bounded `FAMILY_KINDS`
(8 entries), the bounded `BUDGET_TAGS` (3 entries), the bounded
`LANGUAGE_TAGS` (3 entries), the bounded eleven-field signal
record shape, the bounded twenty-two `ALLOWED_OUTPUT_KEYS`, the
documented U+0131 pre-fold rule, and the canonical-length-
aware edit-budget table are bounded by WO-L0-WORKSHOP-FRAME-B
and are NOT claimed exhaustive.

All DC-020 through DC-071 boundary invariants carry forward.
WO-L0-WORKSHOP-FRAME-B does not amend or broaden DC-003 through
DC-071. RK-058 is acknowledged and remains OPEN. RK-039 remains
active and is not duplicated. Real-benchmark-ready remains NO.
OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057,
OQ-070, OQ-075, OQ-076 remain OPEN.
