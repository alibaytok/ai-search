# 00 - RK-060 Triage Plan

Document type: Triage plan (descriptive only)
Originating Work Order: WO-L0-WORKSHOP-RK060-TRIAGE-01
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Status: Triage authored; pending Codex authorization of follow-up
packets.

## Authority and non-claim envelope

This document is a triage plan. It enumerates, categorizes, and
proposes Codex-authorizable follow-up packets that would close the
six residuals recorded in RK-060. It does NOT itself authorize any
follow-up packet. It does NOT modify any FRAME-A / FRAME-B /
FRAME-C / FRAME-D module or test. It does NOT close RK-060,
RK-058, RK-059, or any OQ. It does NOT add a new DC row, a new
RK, or amend the controller checklist. It does NOT authorize real
indexing, retrieval, ranking, scoring, similarity, distance,
embedding, vector, ANN backend, reranker, provider call, LLM call,
route object creation, route selection, source qualification,
corpus admission, real benchmark execution, architecture / vendor
/ library / index-family / production-system selection, Source
Card or Route Card creation, production artifact contracts,
third-party dependencies, CLI introduction, or subprocess / shell
execution. Real-benchmark-ready remains NO. All seven FRAME-A /
B / C / D gating booleans remain literal False on every emitted
path.

Canonical authority remains with `00-controller-checklist.md`,
`00-open-questions.md`, the active Work Order packet, and
`00-claude-task-ledger.md`. On conflict, canonical wins and this
triage plan must be corrected.

Each proposed packet below is a Codex authorization candidate, not
an authorization. Codex must explicitly issue the proposed packet
for any implementation to proceed.

## RK-060 residuals (quoted from `00-open-questions.md`)

The six residuals recorded under RK-060 are:

- **(a) W-PRM-007** "Set up scheduled dependency scanning every
  Monday." Planning intent B/[workflow_file, hook]; FRAME-D actual
  G/[skill, instruction, workflow_file] because FRAME-B canonical-
  set lacks cron/scheduled/hook tokens and FRAME-C bare-ambiguity
  fires on `action.set_up` alone.
- **(b) W-PRM-015** "Add instructions for setting up CI on a new
  Python repo." Planning intent E/[instruction, workflow_file];
  FRAME-D actual A/[instruction] because FRAME-B `action.set_up`
  does not match `setting up` via short_token_1 budget (canonical
  `setup` len 5 -> limit 1; the gerund inflection is out of
  budget) so workflow_file does not co-fire.
- **(c) W-PRM-020** original text "Improve the way we handle code
  reviews." Planning intent G/[skill, instruction, agent]; FRAME-D
  actual C/[skill] because `action.improve` + `domain.code_review`
  fires `_is_skill_intent` (single skill candidate) rather than
  bare-ambiguity (bare-ambiguity requires no informative domain).
- **(d) W-PRM-021** Planning intent G/[workflow_file, instruction,
  cookbook_entry]; FRAME-C bare-ambiguity emission set is bounded
  to (skill, instruction, workflow_file), so the specific kinds
  set differs even though category G is preserved.
- **(e) W-PRM-025** original "What is awesome-copilot?" Planning
  intent I; FRAME-D actual H because `awesome-copilot` is not a
  FRAME-B canonical or alias.
- **(f) W-PRM-026** original "Explain how this repo is organized."
  Planning intent I; FRAME-D actual C because the multi-token
  canonical `how is this repo organized` requires exact-order
  positional match and the planning text has `how this repo is
  organized` (different word order).

## Categorization by upstream layer

| residual | upstream layer | concrete artifact to change |
|---|---|---|
| (a) W-PRM-007 | FRAME-B canonical-set extension | new family or family-alias additions for cron/scheduled/hook tokens; primary surface is FRAME-B's `SIGNAL_FAMILIES` |
| (b) W-PRM-015 | FRAME-B inflection / budget policy | either (b1) widen `action.set_up` canonical_terms with `setting up` / `sets up` inflections, (b2) raise that family's edit-budget tag, or (b3) introduce gerund-aware folding; primary surface is FRAME-B's per-family budget table |
| (c) W-PRM-020 | FRAME-C synthesis-rule refinement | `_is_skill_intent` should not collapse single-skill resolution when the only informative-domain signal is `code_review` alongside `action.improve`; primary surface is FRAME-C's bare-ambiguity pre-check or a new "vague-improve-with-soft-domain" rule |
| (d) W-PRM-021 | FRAME-C synthesis-rule refinement | bare-ambiguity emission set is currently the bounded triple (skill, instruction, workflow_file); the rule could be extended to vary the emission set by primary-action subfamily (e.g., emit cookbook_entry when `action.deploy` is the bare-ambiguity action); primary surface is `_BARE_AMBIGUITY_KINDS` and `_compute_shape_touch_plan` |
| (e) W-PRM-025 | FRAME-B canonical-set extension | `repo_meta_near_miss.repo_navigation` canonical-set needs product-name / workshop-name tokens (or a new `repo_meta_near_miss.product_name` family); primary surface is FRAME-B's `SIGNAL_FAMILIES` |
| (f) W-PRM-026 | FRAME-B multi-token-window matching policy | either (f1) introduce a permuted-window match for `repo_meta_near_miss` canonicals, (f2) add the observed phrasing as an additional bounded canonical (`how this repo is organized`), or (f3) document the strict-order rule as the deliberate matching policy and rewrite the prompt instead; primary surface is FRAME-B's `_match_multi_token_term` or the canonical list |

Layer summary:
- FRAME-B canonical-set extension: residuals (a), (e).
- FRAME-B inflection / budget policy: residual (b).
- FRAME-B multi-token-window matching policy: residual (f).
- FRAME-C synthesis-rule refinement: residuals (c), (d).

## Proposed Codex-authorizable follow-up packets

### Proposed packet 1 - WO-L0-WORKSHOP-FRAME-B-COVERAGE-02

**Scope.** Extend FRAME-B's `SIGNAL_FAMILIES` with bounded
canonical / alias additions for the three FRAME-B coverage-side
residuals (a), (e), (f). Optionally also address residual (b)
inside the same packet if Codex prefers consolidated FRAME-B
coverage work; otherwise split (b) into a sibling packet.

**Residuals closed.** (a), (e), (f), and optionally (b).

**Allowed-files sketch (proposal, not authorization).**

- `harness/level0_workshop_signal_evidence.py` (extend
  `SIGNAL_FAMILIES`; possibly add a new
  `_match_multi_token_term` window policy if (f) is closed via
  permuted-window matching rather than canonical addition).
- `harness/tests/test_level0_workshop_signal_evidence.py` (add
  family-presence tests for each new canonical / alias; add a
  static-scan that the new canonicals do not noise-match
  unrelated tokens).
- `harness/tests/test_level0_workshop_canonical_intent_frame.py`
  (extend `HardenedSynthesisTest` to cover the W-PRM-007 /
  W-PRM-025 / W-PRM-026 end-to-end behaviour through FRAME-C).
- `harness/tests/test_level0_workshop_user_intent_mapper.py`
  (extend `LegacyContractParityTest` with the same three
  end-to-end behaviour assertions through the FRAME-D shim).
- `harness/tests/test_level0_workshop_derived_trace.py` (if the
  closure changes the FRAME-D-derived category for any of
  W-PRM-007 / W-PRM-025 / W-PRM-026 in a way that perturbs the
  validator's per-category distribution invariant, the planning
  doc rewrites for these three prompts in
  `00-level0-awesome-copilot-workshop-seed.md` would need to be
  revisited; the proposed packet's allowed-files set should
  include the derived-trace test only if such re-distribution is
  required).
- `ai-search/70-level0-workshop-signal-evidence.md` (Non-Claim
  Constraints / addendum: SIGNAL_FAMILIES count update; new
  family or canonical descriptions).
- `ai-search/71-level0-workshop-canonical-intent-frame.md` (no
  expected change unless the multi-token-window policy is
  centralised in FRAME-C, which it currently is not).
- `ai-search/00-level0-awesome-copilot-workshop-seed.md` (per-
  prompt closure-evidence table: update the (a), (e), (f) rows;
  remove their RK-060 reference; document the original-text
  recovery for (e) and (f)).
- `ai-search/00-open-questions.md` (DC-078 row recording the
  decision; RK-060 row update marking residuals (a) / (e) / (f)
  closed; Status / chronology refresh).
- `ai-search/00-claude-task-ledger.md` (append entry).

**Expected test additions sketch.**

- 1-2 FRAME-B family-presence tests per new canonical or alias
  (e.g., `cron` / `scheduled` matches a new `constraint.scheduled`
  or `object.hook` extension for residual (a); `awesome-copilot`
  matches a `repo_meta_near_miss.product_name` family for
  residual (e); permuted-window or new canonical for residual
  (f)).
- 1 FRAME-B negative test per new canonical to verify it does NOT
  noise-match unrelated tokens.
- 1 FRAME-C end-to-end test per residual that the new signal
  shifts the prompt's category to the planning intent.
- 1 mapper end-to-end test per residual that the FRAME-D shim
  surfaces the same category through the legacy contract.

**Expected behavior change per residual.**

- (a) W-PRM-007: FRAME-D output shifts from G/[skill, instruction,
  workflow_file] back toward B/[workflow_file, hook] or G with a
  hook kind included; planning doc and trace test must be re-
  reconciled if the per-category-count invariant is perturbed.
- (e) W-PRM-025: FRAME-D output shifts from H/[none] to
  I/[repo_meta_section] for the original `What is awesome-copilot?`
  text.
- (f) W-PRM-026: FRAME-D output shifts from C/[skill] to
  I/[repo_meta_section] for the original `Explain how this repo
  is organized.` text.

**Explicit non-authorization list (carries forward).** No real
indexing, retrieval, ranking, scoring, similarity, distance,
embedding, vector, ANN backend, reranker, provider call, LLM
call, route object creation, route selection, source
qualification, corpus admission, real benchmark execution,
architecture / vendor / library / index-family / production-
system selection, Source Card or Route Card creation, production
artifact contracts, third-party dependencies, CLI introduction,
or subprocess / shell execution. No `00-controller-checklist.md`
modification. No `benchmark-fixtures/` mutation. No FRAME-A
module or test modification. No FRAME-C or FRAME-D module
modification (the proposed packet only touches FRAME-B and the
boundary docs / planning doc / open-questions / ledger, plus the
downstream FRAME-C / FRAME-D / derived-trace TESTS to record the
end-to-end behaviour change). No closure of OQ-003, OQ-015,
OQ-031, OQ-035, OQ-048, OQ-049, OQ-056, OQ-057, OQ-070, OQ-075,
OQ-076. No closure of RK-058 or RK-059 (already RESOLVED). No
duplication of RK-039. No new bounded enum value in
`EVIDENCE_BANDS`, `AMBIGUITY_LEVELS`, `AFFINITY_GRADES`,
`REQUESTED_OUTPUT_SHAPES`, `WORKSHOP_ITEM_KINDS`, or
`WORKSHOP_PROMPT_CATEGORIES`. No new exception class unless
strictly necessary. No forbidden output field names
(`ranking_performed`, `scoring_performed`, `confidence`,
`score`, `distance`, `best_match`, `threshold`, `similarity`).

**Estimated risk surface.**

- New `SIGNAL_FAMILIES` entries are bounded by Codex; FRAME-B's
  family count would grow from 31 to roughly 32-34 depending on
  whether (a) / (e) / (f) consolidate.
- Permuted-window matching policy (if chosen for (f)) would
  widen the FRAME-B matching API; a more conservative
  alternative is to add the observed canonical as-is.
- Backward compatibility: existing FRAME-B / FRAME-C / mapper /
  trace tests must continue to pass. If a new canonical noise-
  matches an existing prompt and shifts its category, the
  planning doc rewrites in `00-level0-awesome-copilot-workshop-
  seed.md` must be re-reconciled to keep the trace validator's
  per-category-count invariant satisfied. The proposed packet's
  Q6 review must check this explicitly.
- No new bounded enum is needed; no new exception is needed; no
  forbidden output field is added.

### Proposed packet 2 - WO-L0-WORKSHOP-FRAME-C-HARDEN-02

**Scope.** Refine FRAME-C synthesis rules to close the two
FRAME-C-side residuals (c) and (d).

**Residuals closed.** (c), (d).

**Allowed-files sketch (proposal, not authorization).**

- `harness/level0_workshop_canonical_intent_frame.py` (refine
  `_is_bare_ambiguity_signal_set` and / or `_compute_shape_touch_plan`
  to handle the (c) and (d) cases).
- `harness/tests/test_level0_workshop_canonical_intent_frame.py`
  (extend `HardenedSynthesisTest` with the (c) and (d) end-to-end
  behaviour assertions).
- `harness/tests/test_level0_workshop_user_intent_mapper.py`
  (extend `LegacyContractParityTest` with the same).
- `harness/tests/test_level0_workshop_derived_trace.py` (if the
  closure shifts W-PRM-020 or W-PRM-021 in a way that perturbs
  the validator's per-category distribution invariant, the
  planning doc rewrites for those prompts would need to be
  revisited).
- `ai-search/71-level0-workshop-canonical-intent-frame.md` (Shape
  Touch Plan / Ambiguity classification / Workshop category
  mapping addendums for the new rules).
- `ai-search/72-level0-workshop-intent-mapper-compatibility-shim.md`
  (no expected change; FRAME-D remains a thin translator).
- `ai-search/00-level0-awesome-copilot-workshop-seed.md` (per-
  prompt closure-evidence table: update (c) and (d) rows; remove
  their RK-060 reference; document the original-text recovery
  for (c) and the kind-set recovery for (d)).
- `ai-search/00-open-questions.md` (DC-079 row recording the
  decision; RK-060 row update marking residuals (c) / (d)
  closed; Status / chronology refresh).
- `ai-search/00-claude-task-ledger.md` (append entry).

**Expected test additions sketch.**

- 1 FRAME-C synthesis test per residual that the new rule
  produces the planning intent (e.g.,
  `test_improve_plus_code_review_yields_bare_ambiguity_G` for
  (c); `test_bare_ambiguity_emission_set_for_action_deploy_includes_cookbook`
  for (d) or whatever the chosen approach implies).
- 1 mapper end-to-end test per residual that the FRAME-D shim
  surfaces the same category through the legacy contract.
- 1 negative test per new rule to confirm it does not over-fire
  on adjacent prompt shapes (e.g., `action.improve` + a strong
  target object must still produce a single-intent rather than
  bare-ambiguity).

**Expected behavior change per residual.**

- (c) W-PRM-020 original text "Improve the way we handle code
  reviews.": FRAME-D output shifts from C/[skill] to G with at
  least two kinds (per the new rule).
- (d) W-PRM-021 "Help with my release process.": FRAME-D output
  kinds shift from (skill, instruction, workflow_file) to the
  planning-intent (workflow_file, instruction, cookbook_entry)
  when `action.deploy` is the primary bare-ambiguity action; the
  G category is preserved.

**Explicit non-authorization list (carries forward).** Same as
Proposed packet 1's non-authorization list, with the additional
note that the proposed packet must NOT reintroduce a parallel
keyword classifier in FRAME-D (the prior FRAME-D-R rework
forbade that) and must NOT add categorization rules in FRAME-D
that re-derive what FRAME-C should synthesize.

**Estimated risk surface.**

- The bare-ambiguity rule is currently the simplest of FRAME-C's
  synthesis rules; widening it for (c) risks over-firing on
  legitimate single-skill prompts. The Q6 review must include a
  negative-test grid covering the existing C-category prompts to
  confirm no regression.
- Varying the bare-ambiguity emission set by primary-action
  subfamily (for (d)) raises the question of whether the bounded
  three-entry tuple `_BARE_AMBIGUITY_KINDS` becomes a per-
  subfamily table; that is a small bounded change but should be
  recorded as a new DC.
- No new bounded enum value is needed; no new exception is
  needed; no forbidden output field is added.

## Per-residual closure map

| residual | proposed packet | residual rationale |
|---|---|---|
| (a) W-PRM-007 | Packet 1 (FRAME-B-COVERAGE-02) | canonical-set extension for cron/scheduled/hook |
| (b) W-PRM-015 | Packet 1 (FRAME-B-COVERAGE-02), or split into a sibling FRAME-B-COVERAGE-02b | inflection / budget policy adjustment for `action.set_up` |
| (c) W-PRM-020 | Packet 2 (FRAME-C-HARDEN-02) | synthesis-rule refinement for `improve` + `code_review` |
| (d) W-PRM-021 | Packet 2 (FRAME-C-HARDEN-02) | bare-ambiguity emission-set widening per primary-action subfamily |
| (e) W-PRM-025 | Packet 1 (FRAME-B-COVERAGE-02) | canonical-set extension for product / workshop names |
| (f) W-PRM-026 | Packet 1 (FRAME-B-COVERAGE-02) | multi-token-window policy or additional canonical |

## Recommended sequencing

1. **Packet 1 - FRAME-B-COVERAGE-02 first.** FRAME-B is the
   upstream layer; closing FRAME-B residuals first reduces the
   risk that FRAME-C-HARDEN-02 ends up papering over what is
   actually a missing FRAME-B signal. Packet 1's tests will also
   surface any unexpected category drift in the rest of the
   trace fixture before FRAME-C is touched.
2. **Re-reconcile the planning doc and the trace fixture after
   Packet 1.** If Packet 1 shifts W-PRM-007 / W-PRM-025 / W-PRM-026
   in a way that breaks the per-category distribution invariant,
   either rewrite the corresponding planning-doc prompts (the same
   pattern WO-L0-WORKSHOP-RK058-CLOSURE-01 used) or absorb the
   drift into Packet 1's own scope. This re-reconciliation is
   part of Packet 1, not a separate packet.
3. **Packet 2 - FRAME-C-HARDEN-02 second.** FRAME-C synthesis
   refinement consumes FRAME-B's settled signal surface. Running
   FRAME-C second avoids two packets fighting over the same
   prompts. Packet 2 should also re-reconcile the planning doc
   and trace fixture if W-PRM-020 / W-PRM-021 categorisation
   shifts.
4. **Optional sub-split.** If Codex prefers smaller packets,
   residual (b) (inflection / budget) can split out of Packet 1
   into a sibling packet (`WO-L0-WORKSHOP-FRAME-B-COVERAGE-02b`).
   The trade-off is two smaller reviews vs one consolidated
   FRAME-B review; the technical change for (b) is independent of
   (a) / (e) / (f) and could be authored separately without
   coupling.
5. **Optional alternative for (f).** Codex may choose to close
   (f) by documenting the strict-word-order policy as the
   deliberate matching contract and rewriting the planning text
   for W-PRM-026 to match an existing canonical (the path
   WO-L0-WORKSHOP-RK058-CLOSURE-01 already used in part). This
   would leave the FRAME-B matching policy unchanged and resolve
   (f) entirely inside the planning doc; the triage records the
   choice so Codex can authorize either path.

## What this triage authorizes (nothing)

This triage plan does not authorize:

- any FRAME-A / FRAME-B / FRAME-C / FRAME-D module modification.
- any FRAME-A / FRAME-B / FRAME-C / FRAME-D test modification.
- any boundary doc modification beyond this triage plan, the
  RK-060 row note in `00-open-questions.md`, and this ledger
  entry.
- any benchmark-fixtures mutation.
- any controller-checklist modification.
- any new RK or new DC row.
- any RK-058, RK-059, or RK-060 closure.
- any OQ closure.
- any real indexing, retrieval, ranking, scoring, similarity,
  distance, embedding, vector, ANN backend, reranker, provider
  call, LLM call, route object creation, route selection, source
  qualification, corpus admission, real benchmark execution,
  architecture / vendor / library / index-family / production-
  system selection, Source Card or Route Card creation,
  production artifact contracts, third-party dependencies, CLI
  introduction, or subprocess / shell execution.

Each proposed packet above must receive an explicit Codex
authorization (its own DC row and its own Work Order packet)
before implementation can proceed.

## Non-claim envelope

WO-L0-WORKSHOP-RK060-TRIAGE-01 does not claim that the proposed
categorisation, the proposed packets, the proposed allowed-files
sketches, the proposed test additions, the expected behaviour
changes, or the recommended sequencing are sufficient,
necessary, superior, best, complete, production-ready,
recommended, selected, or benchmark-ready. The triage is bounded
descriptive content authored to help Codex author follow-up
packets; the actual closure decisions, scopes, allowed files,
test surfaces, and behaviour changes remain Codex's authority.
The bounded six-residual list mirrors RK-060 exactly and is
bounded by `00-open-questions.md`. Real-benchmark-ready remains
NO. All DC-020 through DC-077 boundary invariants carry forward.
RK-058 stays RESOLVED. RK-059 stays RESOLVED. RK-060 stays OPEN
pending Codex-authorized follow-up packets.
