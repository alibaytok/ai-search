# 76. Level 0 Raw Candidate Snapshot

## Goal

Record the first versioned raw candidate pool emitted by the local
Level 0 corpus crawler. This packet makes the crawler output auditable
before any Mini-V2 admission decision is made.

The snapshot is a raw candidate artifact only. It does not admit corpus
cases, create holdout cases, generate expected fields, run the parser,
authorize parser-core promotion, or make any benchmark, source, route,
or production-readiness claim.

## Snapshot

Artifact:

- `harness/raw_candidate_pools/L0-WS-RAW-CANDIDATES-v1.raw_candidates.json`

The snapshot is generated from the crawler's default local sources and
is pinned by tests to match the current deterministic crawler output.

Current shape:

- 69 raw candidates
- 4 local sources
- all candidates have `admission_status="raw"`
- all candidates have `admission_reason="pending_human_review"`
- no expected fields
- no parser invocation
- no network access
- no corpus admission

## Admission Boundary

Mini-V2 admission is a separate future packet. That packet must select
from this raw pool with explicit per-case human rationale and must not
copy parser observations into expected fields.

Mini-V1 prompt duplicates are present in this raw pool because Mini-V1
is one of the crawler's default local sources. A future admission packet
must de-duplicate against Mini-V1 before selecting admitted or holdout
cases.

## Non-Claims

This snapshot is not a corpus, benchmark, holdout, training dataset,
source qualifier, route validator, production input, or parser-quality
claim. It is a deterministic raw candidate pool for later human review.
