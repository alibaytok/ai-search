# Level 0B Indexing-Logic Fast Plan / Checklist

Document type: Planning artifact / fast-plan checklist
Owner: Codex (controller)
Author of entries: Claude (builder/documentation agent)
Originating Work Order: WO-L0-FASTPLAN-01

## Authority

This is a planning artifact. It is NOT a project-authority document
and does NOT authorize implementation. Canonical authority remains
with `ai-search/00-controller-checklist.md`,
`ai-search/00-open-questions.md`, the active Work Order packet, and
`ai-search/00-claude-task-ledger.md`. If this file conflicts with
canonical documents, canonical wins.

## 1. Purpose

Level 0B exists to make the prompt-router indexing logic observable
before any real indexing. The visible trace chain we are testing is:

```
prompt -> normalized intent -> touched source / material refs ->
candidate route / workflow fragments -> rejection reasons ->
no forced selection
```

This is NOT prompt search. NOT skill search. NOT generic RAG. NOT
real indexing. NOT architecture / vendor / library / index-family
/ ANN / reranker / retrieval-family / production-system selection.
Real-benchmark-ready remains NO.

## 2. Current Approved Stack

| WO | What it adds | What it still does not do |
|----|--------------|---------------------------|
| WO-L0-ITEMS-01 | Planning artifacts only: 65-row `00-level0-item-selection.md` item-slot table and 23-row `00-level0-prompt-set.md` prompt-set table, both at link / locator / section-heading granularity. | Does not load anything into harness; no scaffold module exists yet. |
| WO-L0-RUN-01 | Validates `item_records` (65) and `prompt_records` (23) shape; bounded source-id and category sets; exact-field rejection; 15-key fixed-shape `manual_seed_ready_for_visible_trace` observation. | Does not produce source content; does not invoke any prior-WO public function; no candidate fragment derivation. |
| WO-L0-TRACE-01 | Executes one WO-59 visible report per trace case; emits 13-key fixed-shape trace-execution observation; short-circuits if seed shape invalid. | Does not materialize source records; trace cases come from caller; candidate fragment counts come solely from WO-59 (zero when source records are empty or carry no derived material). |
| WO-L0-MATERIAL-01 | Generates 65 WO-55-shaped `source_reference_records` and 65 WO-56-shaped `source_records` from metadata only; deliberate omission of `qualified` field per WO-56 contract. | Carries no `extracted_material`, no `normalized_material`, no `candidate_fragments` (WO-56 rejects all three); cannot drive non-zero candidate fragment output by itself. |
| WO-L0-E2E-01 | Consolidated end-to-end visible-trace runner; one call produces materialization observation, 23 trace cases with non-empty source attachments, and trace execution observation; 16-key aggregate output; approved with Codex hardening at 43/43 targeted and 1046/1046 full suite. | `candidate_route_fragment_total` and `candidate_workflow_fragment_total` are zero by construction; no derived-material attachment yet; source-touch filtering is by literal token, not by semantic match. |

## 3. Current Gap

- The end-to-end plumbing is complete: a single call now runs from
  `item_records + prompt_records` to a per-prompt visible-trace
  summary across 23 prompts.
- Candidate fragment totals are zero by construction.
- Reason: `source_records` intentionally carry no
  `extracted_material`, no `normalized_material`, and no
  `candidate_fragments` because the WO-56 bridge contract rejects
  any presence of those fields.
- Consequence: the current Level 0B stack cannot yet test candidate
  or rejection quality. It only proves wiring and contract
  discipline.

## 4. Indexing Logic We Actually Want To Test

Level 0B indexing logic is evidence routing, not search. The
behaviors we want observable in the visible trace:

- Prompt-shaped material must NOT become a route object.
- Skill-shaped material must NOT become a route object.
- Agent-shaped material must NOT become a route object.
- Workflow-shaped material MAY become candidate workflow material
  (with `candidate_only: True`).
- Encyclopedic near-miss material (Wikipedia "Prompt engineering")
  MUST be rejected with an explicit reason.
- Vendor-guide material (Gemini for Workspace) MAY be structured
  but MUST NOT imply authority or promotion.
- Ambiguous prompts MUST NOT force a single candidate; ambiguity
  surfaces in the observation.
- No-route prompts MUST produce an explicit no-selection reason
  and zero candidate fragments.
- Refusal prompts MUST produce an explicit no-selection reason and
  zero candidate fragments.

None of the above requires real retrieval, ranking, scoring, or
similarity. All of it is shape and rejection-reason observation.

## 5. Fast Finish Plan

Three compact future Work Orders. No more than three.

### A. WO-L0-DERIVED-01 - Manual Seed Derived Material Layer

- One scaffold module under `harness/`.
- Input: already-loaded `item_records` + `prompt_records`.
- Delegates shape validation to `run_level0_manual_seed_visible_report`
  (WO-L0-RUN-01).
- Emits `derived_material_records` from metadata only; no external
  content; no URL fetch; no PDF read; no hash library.
- Generates bounded material kinds:
  - `prompt_shaped_material`
  - `skill_shaped_material`
  - `agent_shaped_material`
  - `workflow_shaped_material`
  - `vendor_pattern_material`
  - `near_miss_encyclopedic_material`
- Every record carries `candidate_only: True`.
- No official route markers; no `route_state == "official"`; no
  `plane == "official_route_results"`.
- Includes a per-prompt `rejection_profile` for the near-miss /
  no-route / refusal categories (declared by prompt category, NOT
  by semantic inference).
- Output is observation only; no source qualification, no corpus
  admission, no route selection.

### B. WO-L0-E2E-DERIVED-01 - Derived Material Attached Visible Trace

- One consolidated scaffold under `harness/`.
- Chains: materialization (WO-L0-MATERIAL-01) + derived-material
  layer (WO-L0-DERIVED-01) + trace execution (WO-L0-TRACE-01).
- Builds `trace_case_records` with source records PLUS derived
  material in a WO-59-compatible way.
- If the WO-56 bridge contract blocks derived-material attachment
  on `source_records` (likely), record a formal compatibility halt
  explaining the contract gap and emit an explicit blocker report
  rather than a clean pass. Decision on bridge-extension vs
  bridge-bypass is reserved for the originating packet.
- Goal: produce non-zero candidate / rejection observations where
  the indexing logic in section 4 says they should appear, or
  produce a clear blocker report otherwise.
- No architecture / vendor / library / index-family / ANN /
  reranker / retrieval-family / production-system choice. No
  search, no scoring, no metrics.

### C. WO-L0-REVIEW-01 - Level 0B Trace Quality Review Report

- No new scaffold module. Documentation-only Work Order.
- Runs / inspects the resulting Level 0B end-to-end observation.
- Produces a review report mapping each of the 23 prompts to:
  - `expected_source_touch`
  - `observed_source_touch`
  - `expected_candidate_shape`
  - `observed_candidate_shape`
  - mismatch notes (descriptive only)
- No benchmark score. No ranking. No claim that the trace is
  sufficient, necessary, superior, best, complete,
  production-ready, recommended, or selected.

## 6. Stop Conditions

Hard stops during any of the three proposed Work Orders. If any
condition below is observed, halt the WO and surface to Codex:

- Any of `selection_made`, `measurement_authorized`,
  `real_benchmark_authorized`, `real_benchmark_ready` flips True.
- Any record carries `route_state == "official"` or
  `plane == "official_route_results"`.
- Any prompt-shaped, skill-shaped, or agent-shaped material is
  promoted to a route object.
- Any near-miss encyclopedic material becomes a candidate route
  or candidate workflow fragment.
- Any candidate fragment lacks `candidate_only: True`.
- Any source qualification or corpus admission appears.
- Any real fetch, file read, index, rank, score, or similarity
  operation occurs.

## 7. What Counts As Done For This Side

Level 0B indexing-logic verification is "done" when:

- The Level 0B end-to-end observation shows, for all 23 prompts, a
  visible trace with source touches, candidate-only fragments
  (where authored), and explicit no-selection / rejection reasons
  (where authored).
- The review report (WO-L0-REVIEW-01) identifies expected-vs-
  observed mismatches without claiming production readiness or
  superiority.
- All four standard authorization / readiness / selection booleans
  remain literal False on every emitted observation.
- Real-benchmark-ready remains NO.

Once those are recorded, focus returns to the broader
`00-controller-checklist.md` checklist for the next gate.

## 8. Non-Claims

This plan:

- Does NOT authorize implementation of WO-L0-DERIVED-01,
  WO-L0-E2E-DERIVED-01, or WO-L0-REVIEW-01. Each requires its own
  packet from Codex.
- Does NOT authorize real indexing.
- Does NOT authorize real retrieval.
- Does NOT authorize benchmark execution.
- Does NOT authorize source qualification or corpus admission.
- Does NOT close OQ-003, OQ-015, OQ-031, OQ-035, OQ-048, OQ-049,
  OQ-056, OQ-057, OQ-070, OQ-075, or OQ-076.
- Does NOT duplicate RK-039.
- Does NOT select any architecture, vendor, library, index family,
  ANN backend, reranker, retrieval family, ablation cell,
  multi-stage variant, or production system.
- Does NOT claim any element of the plan, any proposed Work Order,
  any proposed material kind, or any proposed review row is
  sufficient, necessary, superior, best, complete,
  production-ready, recommended, or selected.

All DC-020 through DC-066 boundary invariants carry forward.
WO-L0-FASTPLAN-01 does not amend or broaden DC-003 through DC-066.
Real-benchmark-ready remains NO.
