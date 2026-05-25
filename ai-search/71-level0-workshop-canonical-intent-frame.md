# 71. Level 0B Workshop CanonicalIntentFrame + ShapeTouchPlan + WorkshopPromptRecordAdapter (WO-L0-WORKSHOP-FRAME-C)

Document type: Scaffold boundary document
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-WORKSHOP-FRAME-C

## Authority

This boundary document records the scaffold surface of
`harness/level0_workshop_canonical_intent_frame.py`. It does NOT
modify canonical authority. Canonical authority remains with
`ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. On conflict, canonical wins.

The Mandatory Priority-Miss Check from
`ai-search/00-claude-scope-prompt-template.md` precedes Section L
on every new scope prompt in this project; it was applied at the
top of this packet and recorded no higher-priority missed scope.

## Scope and Boundary

WO-L0-WORKSHOP-FRAME-C is Stage C of the Level 0B Intent Core. It
consumes an already-loaded FRAME-B SignalEvidenceLedger dict and
emits three artifacts inside one fixed-shape output dict:

1. **CanonicalIntentFrame (CIF)** with `primary_action`,
   `secondary_actions`, `target_object`, `domain`, `constraints`,
   `requested_output_shape`, `source_shape_affinity`,
   `ambiguity_level`, `ambiguity_reasons`, `no_route_reason`,
   `near_miss_reason`, `evidence_band`, and the FRAME-B
   `signal_evidence` echoed verbatim for citation preservation.

2. **ShapeTouchPlan** embedded as `source_shape_affinity`: a list
   of `{item_kind, affinity_basis, affinity_grade}` entries. Each
   entry's `affinity_basis` is a list of signal ids drawn from
   the input ledger; `affinity_grade` is categorical
   (`direct` | `indirect` | `ambiguous`). Multiple plausible
   candidate item kinds yield ambiguity, not selection.

3. **WorkshopPromptRecordAdapter** producing
   `workshop_prompt_record` shaped to satisfy the existing
   workshop derived-trace per-record contract: exactly the seven
   required
   fields (`workshop_prompt_id`, `category`, `prompt_text`,
   `expected_item_kinds_touched`, `expected_candidate_surface`,
   `expected_rejection_surface`, `boundary_note`). It emits no
   adapter-only extras inside the prompt record.

Pipeline position:

```
PromptText
  -> FRAME-A NormalizedPromptView
  -> FRAME-B SignalEvidenceLedger
  -> FRAME-C CanonicalIntentFrame + ShapeTouchPlan       <-- this module
     + WorkshopPromptRecordAdapter
```

FRAME-C does NOT classify a route, does NOT create or select
route objects, does NOT emit any numeric metric output field
(`ranking_performed`, `scoring_performed`, `confidence`, `score`,
`distance`, `best_match`, `threshold`, `similarity` are all
absent from the output by design and verified by static-scan plus
per-record tests), does NOT call any LLM / provider / external
API / embedding / vector / ANN backend / reranker, does NOT
qualify a source, does NOT admit a corpus, and does NOT claim
universal intent understanding, production readiness, completeness,
or benchmark readiness. Those concerns belong to FRAME-D and a
future RK-058 closure packet.

WO-L0-WORKSHOP-FRAME-C does NOT close RK-058. RK-058 is
acknowledged and remains OPEN; closure requires FRAME-D plus a
follow-up Codex-authorized packet. Real-benchmark-ready remains
NO.

## Public Surface

```
build_canonical_intent_frame(
    signal_evidence_ledger, workshop_prompt_id, event_log
) -> dict
```

The module imports only:

- `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`
- `harness.review_package.FORBIDDEN_PHRASES`

The module invokes NO prior-WO public function (verified by
static-scan test). FRAME-A's view-builder and FRAME-B's extractor
appear in tests only as fixture builders.

## Inputs

- `signal_evidence_ledger`: already-loaded clean-pass dict from
  FRAME-B with exactly twenty-two keys per FRAME-B's contract.
- `workshop_prompt_id`: non-empty string identifier for the
  emitted workshop prompt record.
- `event_log`: an `EventLog` instance.

## Bounded Enums

| Enum | Values |
|------|--------|
| `EVIDENCE_BANDS` | `single_signal`, `converging_signals`, `conflicting_signals`, `no_signal` |
| `AMBIGUITY_LEVELS` | `none`, `low`, `high` |
| `AFFINITY_GRADES` | `direct`, `indirect`, `ambiguous` |
| `REQUESTED_OUTPUT_SHAPES` | `recipe`, `configuration_file`, `prompt_collection_request`, `none` |
| `WORKSHOP_ITEM_KINDS` | `skill`, `instruction`, `agent`, `workflow_file`, `hook`, `plugin`, `cookbook_entry`, `repo_meta_section` |
| `WORKSHOP_PROMPT_CATEGORIES` | the bounded nine workshop trace categories `A. clear single-intent` through `I. near-miss/rejection` |

All enums are categorical; no numeric value is emitted.

The `prompt` value is deliberately absent from
`REQUESTED_OUTPUT_SHAPES`: the workshop item-kind namespace
excludes `prompt` (workshop repo has zero `*.prompt.md` files), so
the requested-output-shape enum uses `prompt_collection_request`
to keep the namespaces disjoint.

## Synthesis Rules (deterministic, citation-preserving)

### Primary action and secondary actions

- First `action.*` signal in ledger order wins; mapped via the
  bounded `_ACTION_TO_PRIMARY` table to a CIF action label.
- Subsequent distinct action signals contribute to
  `secondary_actions` (order-preserving, dedup).

### Target object

- First `object.*` signal in ledger order wins; mapped via the
  bounded `_OBJECT_TO_TARGET` table.
- The synthesizer also records `distinct_target_objects` for
  ambiguity classification; the CIF's `target_object` field shows
  the first one.

### Domain / Constraints / Output shape

- All `domain.*` signals contribute distinct domain tags.
- All `constraint.*` and `negation.*` signals contribute distinct
  constraint tags (negation appears as `negated_requested`).
- First `output_shape.*` signal wins.

### Shape Touch Plan

The `_compute_shape_touch_plan` predicate set runs over the
synthesized CIF (NOT the raw prompt). Each predicate that fires
appends one entry to `source_shape_affinity` with
`affinity_basis` listing the contributing signal ids. Bounded
predicates (with WO-L0-WORKSHOP-FRAME-C-HARDEN-01 additions
marked `[HARDEN-01]`):

- **`bare_ambiguity` short-circuit `[HARDEN-01]`**: at least
  one `action.*` signal fires AND no target object AND no
  informative domain AND no requested_output_shape AND no
  constraint/negation signal AND no `repo_meta_near_miss` AND no
  `out_of_scope`. When this fires, the synthesizer emits a
  bounded three-entry ambiguous list with
  `affinity_grade == "ambiguous"` for `skill`, `instruction`,
  and `workflow_file`, and the ambiguity classifier records the
  reason `"bare_ambiguity_action_only"`; the category selector
  short-circuits to `G. ambiguous` regardless of which kinds
  appear in the entry set. Partially hardens RK-059 gap 3 for
  action-backed bare ambiguity.
- **`workflow_file`**: primary action in (`set_up`, `configure`,
  `deploy`) AND (domain in (`ci`, `deployment`) OR any
  event-triggered constraint OR `target_object == "workflow"`).
- **`workflow_file` co-fire `[HARDEN-01]`**: `primary_action ==
  "deploy"` AND no workflow domain AND no event-triggered
  constraint AND no `workflow` target AND at least one
  non-workflow candidate kind already fires. Appends one
  `workflow_file` entry with `affinity_basis` listing the
  action signal ids and `affinity_grade == "ambiguous"`. The
  rule is intentionally narrower than `_is_workflow_intent`: it
  is gated on `primary_action == "deploy"` (which the
  `_ACTION_TO_PRIMARY` table maps from the deploy / publish /
  release / ship / dagit / yayinla family) and not on
  `set_up` or `configure`, so existing single-intent results
  for prompts like `Configure the instruction set` are
  preserved. Closes RK-059 gaps 1 and 2.
- **`skill`**: primary action in (`create`, `review`, `improve`,
  `explain`) AND no event-triggered constraint AND target in
  (`skill_capability`, `algorithm`, `repository`) OR domain in
  (`code_review`, `security`).
- **`instruction`**: no event-triggered constraint AND
  requested_output_shape != `recipe` AND (target ==
  `instruction_set` OR primary_action == `configure` and not
  workflow_intent).
- **`agent`**: target_object == `persona`.
- **`hook`**: target_object == `hook` OR (event-triggered
  constraint AND not workflow_intent).
- **`plugin`**: target_object == `plugin`.
- **`cookbook_entry`** (extended `[HARDEN-01]`):
  `requested_output_shape in (recipe,
  prompt_collection_request)` OR `target_object == recipe`.
  The extension to include `prompt_collection_request` ensures
  that a prompt asking for a prompt example fires
  `cookbook_entry`, enabling the `workflow_file` co-fire rule
  to raise ambiguity for prompts like `Give me a prompt that
  deploys a static site` and surface category
  `F. prompt-search-shaped but workflow-intent`. Closes
  RK-059 gap 2.
- **`repo_meta_section`**: any `repo_meta_near_miss` signal
  fires (rejection-only; precedes candidate-kind decisions).
- **`none`**: any `out_of_scope` signal fires (no-route;
  precedes candidate-kind decisions).

If `repo_meta_near_miss` or `out_of_scope` fires, candidate
item-kind predicates do NOT add entries; the affinity list
contains only the rejection/no-route entry.

If `bare_ambiguity` fires, only the bounded three-entry
ambiguous list is emitted; candidate item-kind predicates do
NOT add entries.

If two or more candidate item-kinds fire, each entry's
`affinity_grade` is downgraded to `"ambiguous"` to surface
multi-shape ambiguity at the entry level.

### Residual RK-059 / FRAME-B coverage closure

Bare-ambiguity inputs that FRAME-B previously could not extract
any action signal from (for example `help with my project`)
classified as `H. no-route` via the no-signal path until
WO-L0-WORKSHOP-FRAME-B-COVERAGE-01 added the bounded
`action.assist` family (`canonical_terms=("help", "assist")`,
`tr_aliases=("yardim", "yardim et")`,
`edit_distance_budget="short_token_1"`,
`contributes_to=("primary_action",)`) to FRAME-B. The new
family extracts an `action.*` signal for help / assist /
Turkish yardim phrasings; FRAME-C's bare-ambiguity rule then
fires and the result is `G. ambiguous`. RK-059 is RESOLVED via
DC-076 after this packet. FRAME-C's `_ACTION_TO_PRIMARY` table
was not extended by that packet, so an `action.assist`-only
ledger produces `primary_action == None`; this is the desired
behavior because the bare-ambiguity rule checks
`by_kind["action"]` non-emptiness rather than primary_action
specifically.

### Evidence band classification

- 0 signals -> `no_signal`.
- Repo-meta or out-of-scope colliding with any informative
  candidate-kind signal -> `conflicting_signals`.
- Exactly one informative family kind fired -> `single_signal`.
- Otherwise -> `converging_signals`.

### Ambiguity classification

- `high` if any of: `bare_ambiguity_action_only` `[HARDEN-01]`;
  repo-meta collides with candidate; out-of-scope collides with
  candidate; >=2 distinct target objects; >=2 distinct candidate
  item kinds.
- `none` if exactly one target object and one candidate kind, or
  if no candidates and no rejection (and no signals at all).
- Otherwise `low`.

### Workshop category mapping

The adapter maps CIF -> one of the bounded nine workshop
categories via the deterministic table in
`_select_workshop_category`:

- out_of_scope -> `H. no-route`.
- repo_meta_near_miss -> `I. near-miss/rejection`.
- `bare_ambiguity` `[HARDEN-01]` -> `G. ambiguous` (short-
  circuit; the bounded three-entry list emitted by the
  bare-ambiguity shape-touch rule includes `instruction` and
  `workflow_file` which would otherwise trigger the
  instruction+workflow category E; the short-circuit forces G).
- High ambiguity with workflow + cookbook -> `F. prompt-search-shaped but workflow-intent`.
- High ambiguity with workflow + agent -> `D. agent/persona confusion`.
- High ambiguity with workflow + instruction -> `E. instruction confusion`.
- Other high ambiguity -> `G. ambiguous`.
- Candidate set == {workflow_file} or {workflow_file, hook} -> `B. workflow intent`.
- Candidate set == {skill} -> `C. skill intent`.
- Candidate set == {agent} / {instruction} / {plugin} / {cookbook_entry} -> `A. clear single-intent`.
- Multiple distinct candidates -> `G. ambiguous`.
- No candidates and no rejection -> `H. no-route`.

### Adapter output

The adapter emits `workshop_prompt_record` with:

- `expected_item_kinds_touched`:
  - `["none"]` if out_of_scope OR (no repo-meta AND no candidate kinds);
  - `["repo_meta_section"]` if repo-meta;
  - the deduped candidate-kind list otherwise.
- `expected_candidate_surface` / `expected_rejection_surface` /
  rejection-class behavior: boolean literals derived from the
  rejection/no-route class. No `no_selection_reason` field is
  emitted in the prompt record because the existing trace
  validator rejects unknown prompt-record fields.
- `boundary_note`: literal
  `"not admitted; not qualified; workshop metadata only"`.

## Output Shape

Clean-pass output dict has exactly twenty-six keys in
`ALLOWED_OUTPUT_KEYS`:

| Key | Type | Clean-pass value |
|-----|------|------------------|
| `intent_frame_kind` | str | `"level0_workshop_canonical_intent_frame"` |
| `input_prompt_observed` | str | mirrored from ledger's `input_prompt_observed` |
| `source_signal_ledger_kind` | str | mirrored from ledger's `signal_evidence_ledger_kind` |
| `workshop_prompt_id` | str | as passed in |
| `primary_action` | str or `None` | from action signals |
| `secondary_actions` | list of str | distinct secondary actions |
| `target_object` | str or `None` | first object signal mapping |
| `domain` | list of str | distinct domain tags |
| `constraints` | list of str | distinct constraint tags (incl. negation) |
| `requested_output_shape` | str or `None` | first output-shape signal mapping |
| `source_shape_affinity` | list of dict | shape-touch plan entries |
| `ambiguity_level` | str | one of `AMBIGUITY_LEVELS` |
| `ambiguity_reasons` | list of str | bounded reason codes |
| `no_route_reason` | str or `None` | bounded literal |
| `near_miss_reason` | str or `None` | bounded literal |
| `evidence_band` | str | one of `EVIDENCE_BANDS` |
| `signal_evidence` | list of dict | echoed from ledger verbatim |
| `workshop_prompt_record` | dict | adapter output |
| `route_created` | bool | literal False |
| `selection_made` | bool | literal False |
| `measurement_authorized` | bool | literal False |
| `real_benchmark_authorized` | bool | literal False |
| `real_benchmark_ready` | bool | literal False |
| `source_qualification_authorized` | bool | literal False |
| `corpus_admission_authorized` | bool | literal False |
| `frame_note` | str | bounded non-claim note literal |

## Forbidden Field Names (verified absent)

No record (top-level result, affinity entry, signal record,
workshop_prompt_record) carries any of: `official`, `is_route`,
`is_official_route`, `selected_as_official`,
`official_route_authorized`, `route_authorized`,
`production_route`, `selected_route`, `executable`,
`route_state`, `plane`, `ranking_performed`, `scoring_performed`,
`confidence`, `score`, `distance`, `best_match`, `threshold`,
`similarity`. Verified by per-record tests and a defensive
output check (`_assert_no_route_status_fields`).

## Validation Order (halt-before-raise)

1. `workshop_prompt_id` non-empty string; else `InvalidWorkshopPromptId`.
2. `signal_evidence_ledger` is a dict; else `NonDictSignalEvidenceLedger`.
3. Required key presence; else `MissingSignalEvidenceLedgerKey`.
4. Unknown key rejection; else `UnknownSignalEvidenceLedgerKey`.
5. `signal_evidence_ledger_kind` literal; else
   `InvalidSignalEvidenceLedgerKind`.
6. All seven FRAME-B gating booleans literal False; else
   `FrameBGatingBooleanFlipped`.
7. `signal_evidence` is a list; per-record dict; per-record field
   set matches the bounded eleven; else `InvalidSignalEvidenceShape`.
8. Module-authored input metadata forbidden-language scan. User-
   authored prompt text and observed spans are preserved as
   evidence and are not treated as project claims.
9. Synthesis (primary action / target object / domain / constraints
   / output shape / shape-touch plan / ambiguity / evidence band /
   category / adapter).
10. Defensive route-status-field absence check on result +
    workshop_prompt_record + every affinity entry + every signal
    record.
11. Module-authored output metadata forbidden-language scan. User-
    authored prompt text and observed spans are preserved as
    evidence and are not treated as project claims.

## Static Scan

The module file contains none of:

- `open(`, `pathlib`, `urllib`, `http.client`, `socket`,
  `import requests`, `from requests`, `requests.`,
  `subprocess`, `os.system`, `shutil`, `hashlib`, `.hexdigest`,
  `.sha256`
- `def query`, `def search`, `def retrieve`, `def rank`
- `score`, `scoring`, `ranking_performed`, `scoring_performed`,
  `confidence`, `best_match`, `threshold`, `similarity`
- `embedding(`, `vectorize(`, ` ann_`, `approximate_nearest`,
  `reranker(`, `rerank_`
- `copilot`, `waza`, `vscode`, `vs_code`, `openai`, `anthropic`,
  `claude_api`, `llm`

The module file contains no name of any prior-WO public function
including FRAME-A's view-builder, FRAME-B's extractor, the
workshop derived-trace and trace-review public functions, the
mapper, and every WO-50 through WO-62 plus four manual-seed L0
public functions. Module file non-ASCII byte count is 0.

## What This Scaffold Does NOT Do

- Does NOT call any prior-WO public function.
- Does NOT classify a route, create a route object, or select a
  route.
- Does NOT qualify sources or admit a corpus.
- Does NOT emit any numeric metric output.
- Does NOT call any LLM / provider / external API / embedding /
  vector / ANN / reranker.
- Does NOT flip any of the seven gating booleans.
- Does NOT mutate input.
- Does NOT claim universal intent understanding, production
  readiness, completeness, or benchmark readiness.
- Does NOT close RK-058.

## Test Surface

`harness/tests/test_level0_workshop_canonical_intent_frame.py`
contains 77 tests across these test classes:

- `CleanPassTest` (21) - output shape, fixed key set, bounded
  enums, literal-False gating booleans, started/passed events,
  no halt, no forbidden field name.
- `AffinityShapeTest` (4) - per-entry three-field shape; bounded
  item_kind; bounded affinity_grade; list-of-strings
  affinity_basis.
- `WorkflowSignalsTest` (3) - workflow phrasings yield workflow
  affinity and a workflow-shaped category.
- `SkillSignalsTest` (1) - skill phrasings yield skill affinity.
- `InstructionSignalsTest` (1) - instruction phrasings yield
  instruction affinity.
- `AgentSignalsTest` (1) - persona phrasings yield agent
  affinity.
- `RepoMetaNearMissTest` (2) - readme/explain yields
  `["repo_meta_section"]` and category `I. near-miss/rejection`.
- `OutOfScopeTest` (2) - weather/general-world yields `["none"]`
  and category `H. no-route`.
- `NoSignalLedgerTest` (1) - unrecognized prompt yields
  `no_signal` evidence band and `["none"]` adapter output.
- `ConflictingSignalsTest` (1) - repo-meta colliding with
  candidate signals surfaces ambiguity or near-miss category.
- `EvidenceBandTest` (2) - no_signal classification; categorical
  enum only.
- `AdapterRecordShapeTest` (5) - record required fields; category
  in bounded set; boundary_note literal; no route-status field;
  no forbidden output field name.
- `AdapterTraceCompatibilityTest` (1) - full adapter record
  satisfies the existing workshop derived-trace per-record
  contract when passed through the trace validator.
- `InputValidationHaltTest` (11) - eleven distinct mutation
  paths covering non-dict, missing/unknown keys, bad
  ledger_kind, gating-boolean flips, malformed signal evidence,
  empty/non-string workshop_prompt_id.
- `ForbiddenLanguageHaltTest` (4) - module-authored forbidden
  phrase/claim phrase halts; user-authored prompt text and
  observed spans carrying such text remain preserved evidence.
- `InputIsolationTest` (1) - input dict not mutated.
- `RequestedOutputShapeEnumTest` (3) - bounded enum membership;
  `prompt` value absent; `prompt_collection_request` value
  present.
- `SignalEvidenceEchoTest` (2) - ledger's `signal_evidence`
  echoed verbatim; affinity_basis ids reference existing signal
  ids.
- `StaticScanTest` (12) - absence of file-IO / network /
  HTTP-library / subprocess-shell / hashlib / retrieval-verb /
  scoring-or-score / forbidden-output-field-name /
  embedding-vector-ANN-reranker / external-integration tokens;
  absence of every prior-WO public function name; module file is
  ASCII.

## Non-Claim Constraints

WO-L0-WORKSHOP-FRAME-C does not claim any synthesized frame
field, affinity entry, evidence-band classification,
ambiguity-level classification, or workshop-prompt-record
category is sufficient, necessary, superior, best, complete,
production-ready, recommended, or selected. The module does not
claim universal intent understanding. The bounded
`EVIDENCE_BANDS` (4), `AMBIGUITY_LEVELS` (3), `AFFINITY_GRADES`
(3), `REQUESTED_OUTPUT_SHAPES` (4 with `prompt_collection_request`
in place of the namespace-colliding `prompt`),
`WORKSHOP_ITEM_KINDS` (8), `WORKSHOP_PROMPT_CATEGORIES` (9), the
bounded synthesis mapping tables, the bounded shape-touch rules,
the bounded workshop-category selection rules, and the
twenty-six `ALLOWED_OUTPUT_KEYS` are bounded by
WO-L0-WORKSHOP-FRAME-C and are NOT claimed exhaustive.

WO-L0-WORKSHOP-FRAME-C-HARDEN-02 addendum: three bounded
synthesis-rule extensions fully close RK-060 (residuals (c),
(d), and the W-PRM-007 B/G category-selector sibling
observation recorded under DC-080):

1. **Deploy-variant bare-ambiguity emission**. Added the
   module-level constant
   `_BARE_AMBIGUITY_KINDS_DEPLOY = (workflow_file, instruction,
   cookbook_entry)` and the helper
   `_bare_ambiguity_kinds_for_primary_action(primary_action)`
   that returns the deploy-variant emission tuple when
   `primary_action == "deploy"` and the default
   `_BARE_AMBIGUITY_KINDS = (skill, instruction, workflow_file)`
   otherwise. The bare-ambiguity emission block in
   `_compute_shape_touch_plan` now calls the helper instead
   of iterating the default constant directly. This closes
   RK-060 residual (d): `Help with my release process.`
   (action.deploy via `release` + action.assist via `help`,
   no other informative signal) now emits the deploy-variant
   kinds and FRAME-D surfaces `G. ambiguous` with
   `[workflow_file, instruction, cookbook_entry]`.

2. **Vague improve-plus-code-review ambiguity rule**. Added a
   new shape-touch rule block in `_compute_shape_touch_plan`
   (after the workflow_file co-fire block, before the
   multi-candidate ambiguous-grade downgrade). When
   `primary_action == "improve"` AND `domain.code_review`
   fires AND no informative target_object is present AND no
   event-triggered constraint AND no requested_output_shape
   AND `skill` is already a candidate (via the existing
   `_is_skill_intent` action+domain path) AND `instruction`
   and `agent` are not, the rule appends `instruction` and
   `agent` candidates alongside the existing `skill`
   candidate with ambiguous grade. This closes RK-060
   residual (c): `Improve the way we handle code reviews.`
   now surfaces `G. ambiguous` with
   `[skill, instruction, agent]`. The
   `not distinct_target_objects` guard preserves the existing
   single-skill resolution for prompts with an informative
   target (e.g., `Improve our code review skill.` with
   object.skill firing) - covered by a negative regression
   test.

3. **`{workflow_file, hook}` -> B branch under high
   ambiguity**. Extended `_select_workshop_category`'s
   high-ambiguity branch with
   `if candidate_set == {"workflow_file", "hook"}: return
   _WORKSHOP_CATEGORY_WORKFLOW`. This closes the W-PRM-007
   B/G category-selector sibling observation recorded under
   DC-080: `Set up scheduled dependency scanning every
   Monday.` (action.set_up + object.hook +
   constraint.event_triggered via the DC-080 `scheduled`
   canonical) yields candidate set `{workflow_file, hook}`
   under high ambiguity (2 candidates); the new branch
   routes this set to `B. workflow intent` even though the
   generic 2-candidate-ambiguous fallback would otherwise
   return G. The kinds set `[workflow_file, hook]` was
   already matching the planning intent under DC-080; DC-081
   closes the category mismatch.

No bounded enum value was added (`WORKSHOP_PROMPT_CATEGORIES`,
`WORKSHOP_ITEM_KINDS`, `EVIDENCE_BANDS`, `AMBIGUITY_LEVELS`,
`AFFINITY_GRADES`, `REQUESTED_OUTPUT_SHAPES` all unchanged).
No new exception class added. No FRAME-A / FRAME-B / FRAME-D
module change. The bounded twenty-six `ALLOWED_OUTPUT_KEYS`
is unchanged. The planning-doc fixture changes that accompany
this packet (W-PRM-020 original-text restoration; W-PRM-008
distribution-rebalance rewrite) preserve the trace
validator's bounded per-category distribution invariant.

All DC-020 through DC-080 boundary invariants carry forward.
WO-L0-WORKSHOP-FRAME-C, WO-L0-WORKSHOP-FRAME-C-HARDEN-01, and
WO-L0-WORKSHOP-FRAME-C-HARDEN-02 do not amend or broaden
DC-003 through DC-080. RK-058 RESOLVED via DC-077. RK-059
RESOLVED via DC-076. RK-060 fully RESOLVED via DC-078 + DC-079
+ DC-080 + DC-081. RK-039 remains active and is not
duplicated. Real-benchmark-ready remains NO.
OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057,
OQ-070, OQ-075, OQ-076 remain OPEN.
