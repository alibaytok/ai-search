"""Scaffold-internal human review summary for scaffold batch outputs.

Per WO-39 / WO-40 (DC-042): this module assembles a minimal,
observation-only human review summary over the existing scaffold
batch summary returned by `harness.batch_runner.run_payload_batch(...)`.
It does not collect quality / performance metrics, does not score,
does not rank, does not declare any winner / best / production-ready /
recommended configuration, does not treat contract pass as validation
evidence, and does not select any architecture.

The module is scaffold-internal only. It is consumed by a human
reviewer (Codex) at review time and surfaces small integer counts
plus literal status strings derived directly from the input batch
summary's existing fields.

Public surface:

    assemble_batch_review_summary(batch_summary) -> dict

The function:

- Accepts the existing scaffold batch summary returned by
  `run_payload_batch(...)` (a dict with `per_run_summaries`).
- Rejects non-dict inputs, missing or non-list `per_run_summaries`,
  any input claiming `selection_made is True`, any input string
  containing a phrase from the WO-35-extended forbidden selection
  list (`harness.review_package.FORBIDDEN_PHRASES + ("score","scoring")`),
  and any input string containing a phrase from
  `harness.payload_loader.FORBIDDEN_CLAIM_PHRASES`.
- On success returns a dict with exactly the eight allowed top-level
  keys: `review_kind`, `run_count`, `fixture_classes`,
  `contract_status_counts`, `snapshot_counts`,
  `measurement_recorded_count`, `selection_made` (always `False`),
  and `review_note`.

The returned review summary contains only observation counts and
literal status strings; it does not synthesize new claims, does not
add quality / performance signals, and does not introduce any field
beyond the eight named here.
"""

from harness.payload_loader import FORBIDDEN_CLAIM_PHRASES
from harness.review_package import FORBIDDEN_PHRASES


# WO-35 / DC-038 Codex review-time hardening added `"score"` and
# `"scoring"` to the local batch-summary forbidden-language scan. The
# WO-39 / WO-40 review module mirrors that extension at module scope
# so the assembled review summary enforces the same boundary at
# construction time. The base list (`FORBIDDEN_PHRASES`) is the
# canonical review-package list defined in `harness.review_package`.
_REVIEW_FORBIDDEN_PHRASES = FORBIDDEN_PHRASES + (
    "score",
    "scoring",
)

ALLOWED_REVIEW_KEYS = (
    "review_kind",
    "run_count",
    "fixture_classes",
    "contract_status_counts",
    "snapshot_counts",
    "measurement_recorded_count",
    "selection_made",
    "review_note",
)


class NonDictBatchSummary(Exception):
    """Raised when the input batch summary is not a dict."""


class MissingPerRunSummaries(Exception):
    """Raised when the input batch summary lacks a `per_run_summaries` key."""


class NonListPerRunSummaries(Exception):
    """Raised when `per_run_summaries` is present but not a list."""


class SelectionMadeInBatchSummary(Exception):
    """Raised when the input batch summary claims `selection_made is True`."""


class ForbiddenLanguageInBatchSummary(Exception):
    """Raised when a phrase from the extended forbidden selection list appears in the input."""


class ForbiddenClaimInBatchSummary(Exception):
    """Raised when a phrase from `FORBIDDEN_CLAIM_PHRASES` appears in the input."""


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


def _assert_no_forbidden_input_language(batch_summary):
    """Raise the appropriate exception if forbidden language appears anywhere."""
    for text in _walk_strings(batch_summary):
        lowered = text.lower()
        for phrase in _REVIEW_FORBIDDEN_PHRASES:
            if phrase in lowered:
                raise ForbiddenLanguageInBatchSummary(
                    "Forbidden selection phrase {0!r} found in input batch "
                    "summary string: {1!r}".format(phrase, text)
                )
        for phrase in FORBIDDEN_CLAIM_PHRASES:
            if phrase in lowered:
                raise ForbiddenClaimInBatchSummary(
                    "Forbidden claim phrase {0!r} found in input batch "
                    "summary string: {1!r}".format(phrase, text)
                )


def _count_contract_statuses(per_run_summaries):
    """Count `"passed"` and `"failed"` contract statuses across per-run entries.

    The returned dict has exactly two keys, `"passed"` and `"failed"`,
    each mapped to a non-negative integer. Per-run entries with any
    other status string are not counted under either key; the runner
    is the authority for emitting either of the two scaffold status
    strings, so any other value would indicate a producer bug rather
    than a reviewer concern. The reviewer module surfaces the two
    canonical counts only.
    """
    passed = 0
    failed = 0
    for run in per_run_summaries:
        if not isinstance(run, dict):
            continue
        status = run.get("contract_status")
        if status == "passed":
            passed += 1
        elif status == "failed":
            failed += 1
    return {"passed": passed, "failed": failed}


def _count_snapshots_written(per_run_summaries):
    """Count `snapshot_written is True` and `snapshot_written is False`."""
    written = 0
    not_written = 0
    for run in per_run_summaries:
        if not isinstance(run, dict):
            continue
        if run.get("snapshot_written") is True:
            written += 1
        elif run.get("snapshot_written") is False:
            not_written += 1
    return {"written": written, "not_written": not_written}


def _count_measurement_recorded(per_run_summaries):
    """Count per-run summaries where `measurement_recorded is True`."""
    count = 0
    for run in per_run_summaries:
        if not isinstance(run, dict):
            continue
        if run.get("measurement_recorded") is True:
            count += 1
    return count


def _fixture_classes(per_run_summaries):
    """Extract the ordered list of `fixture_class` values from per-run entries."""
    classes = []
    for run in per_run_summaries:
        if isinstance(run, dict):
            fc = run.get("fixture_class")
            if isinstance(fc, str):
                classes.append(fc)
    return classes


def assemble_batch_review_summary(batch_summary):
    """Assemble a scaffold-internal human review summary over a batch summary.

    Validates the caller-provided batch summary against the WO-39 /
    WO-40 rejection rules, then returns a dict containing only the
    eight allowed observation-level review fields. The returned dict
    does not propagate any per-run payload content beyond the counts
    and the ordered list of fixture class names.

    The review summary is observation-only. It does not score, rank,
    declare a winner, declare a best configuration, declare a
    production-ready configuration, recommend any architecture, or
    treat contract pass as validation evidence. The `selection_made`
    field is always `False`.
    """
    # 1. Input must be a dict.
    if not isinstance(batch_summary, dict):
        raise NonDictBatchSummary(
            "batch_summary must be a dict; got {0!r}".format(
                type(batch_summary).__name__
            )
        )

    # 2. `per_run_summaries` must be present.
    if "per_run_summaries" not in batch_summary:
        raise MissingPerRunSummaries(
            "batch_summary is missing required key 'per_run_summaries'"
        )

    # 3. `per_run_summaries` must be a list.
    per_run_summaries = batch_summary["per_run_summaries"]
    if not isinstance(per_run_summaries, list):
        raise NonListPerRunSummaries(
            "batch_summary['per_run_summaries'] must be a list; got "
            "{0!r}".format(type(per_run_summaries).__name__)
        )

    # 4. The input must not claim that a selection has been made.
    # The runner emits `selection_made: False` for every scaffold batch
    # under WO-35 / WO-36 / WO-37; a True value would indicate that an
    # upstream producer asserted selection authority that the scaffold
    # explicitly forbids. Reject before any forbidden-language scan so
    # the reviewer sees the structural violation first.
    if batch_summary.get("selection_made") is True:
        raise SelectionMadeInBatchSummary(
            "batch_summary claims selection_made is True; review summary "
            "refuses to assemble for any selection-claiming input. The "
            "Indexing Excellence Gate (`00-controller-checklist.md` "
            "Section K) governs selection; the scaffold does not make "
            "selections."
        )

    # 5. The input must contain no forbidden selection language and no
    # forbidden claim phrase. Both scans run before any aggregation so
    # the reviewer sees the language violation before any count is
    # computed.
    _assert_no_forbidden_input_language(batch_summary)

    # All rejection paths passed. Assemble the observation-only review
    # summary.
    review_summary = {
        "review_kind": "scaffold_batch_review_summary",
        "run_count": len(per_run_summaries),
        "fixture_classes": _fixture_classes(per_run_summaries),
        "contract_status_counts": _count_contract_statuses(
            per_run_summaries
        ),
        "snapshot_counts": _count_snapshots_written(per_run_summaries),
        "measurement_recorded_count": _count_measurement_recorded(
            per_run_summaries
        ),
        "selection_made": False,
        "review_note": (
            "Scaffold-internal human review summary per "
            "ai-search/39-40-batch-review-and-benchmark-readiness.md. "
            "Observation counts only; no quality or performance "
            "signal; no selection claim. The Indexing Excellence "
            "Gate continues to govern selection."
        ),
    }

    return review_summary
