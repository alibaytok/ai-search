"""Scaffold-internal payload batch dry-run runner.

Per WO-35 (DC-038): this is a thin scaffold-internal orchestrator over
`harness.dry_run.run_toy_dry_run(...)`. It invokes the existing dry-run
once per caller-provided payload spec and returns a batch summary.

Per WO-36 (DC-039): per-run summaries now surface contract pass/fail/
disqualification status. The summary adds six observation-only fields
(`contract_status`, `contract_checks_passed_count`,
`contract_checks_failed_count`, `halt_count`,
`disqualified_configuration_count`, `measurement_recorded`) derived
directly from the assembled review package's existing fields and event
log. The runner also accepts an optional `contract_checks` key inside
`common_inputs` and passes it through to `run_toy_dry_run(...)`; the
key is intentionally a scaffold-internal test surface that exists only
so contract-failure status can be exercised.

Per WO-37 (DC-040): the runner accepts an optional
`batch_summary_output_path` keyword. When provided, the batch summary
is persisted via `harness.artifact_snapshot.write_scaffold_snapshot`
to the caller-provided path, and the returned in-memory summary is
augmented with a `batch_snapshot_evidence` field carrying the
writer's returned metadata (`output_path`, `sha256`, `byte_length`).
The on-disk JSON file does not contain `batch_snapshot_evidence`; the
metadata is attached to the in-memory dict only after the file is
written. This is scaffold-only persistence. It is not a retention /
storage / immutability policy, not a production artifact contract,
not a production registration mechanism, and not architecture
selection.

The runner is scaffold-internal only. It does not perform real
benchmark execution, does not collect metrics, does not score, does
not rank, does not declare winners, and does not select any
architecture. It does not auto-discover payload files; it consumes
only caller-provided specs. Contract-status counts are observation
only and are not quality / performance metrics.

Public surface:

    run_payload_batch(payload_specs, common_inputs, snapshot_dir=None,
                      batch_summary_output_path=None)
        -> dict (batch summary)

`payload_specs` is a non-empty list of dicts. Each dict must contain a
string `fixture_class` and a string `payload_path`.

`common_inputs` is a dict of values shared across every dry-run
invocation in the batch. It must contain every key in
`REQUIRED_COMMON_INPUT_KEYS` (the seven inputs that the existing
`run_toy_dry_run(...)` requires aside from the per-spec payload
parameters). It may additionally carry an optional `contract_checks`
key (scaffold-internal test surface only; see WO-36).

When `snapshot_dir` is provided, each per-spec dry-run writes its
snapshot under that directory using the deterministic filename
`"{fixture_class}-batch-snapshot.json"`. When `snapshot_dir` is `None`,
no snapshot is written.

The runner does not mutate payload files, fixture files, docs, or any
production-like state. It does not walk `benchmark-fixtures/` or any
other directory.
"""

import os

from harness.artifact_snapshot import write_scaffold_snapshot
from harness.dry_run import run_toy_dry_run


REQUIRED_SPEC_KEYS = ("fixture_class", "payload_path")

REQUIRED_COMMON_INPUT_KEYS = (
    "fixture_path",
    "fixture_sha256",
    "config_path",
    "registered_config",
    "deterministic_seed",
    "manifest_path",
    "expected_manifest_id",
)


class EmptyPayloadSpecs(Exception):
    """Raised when `payload_specs` is not a non-empty list."""


class MalformedPayloadSpec(Exception):
    """Raised when a payload spec is missing a required key or has a non-string value."""


class MissingCommonInput(Exception):
    """Raised when `common_inputs` is missing a required key."""


def _validate_specs(payload_specs):
    if not isinstance(payload_specs, list) or len(payload_specs) == 0:
        raise EmptyPayloadSpecs(
            "payload_specs must be a non-empty list; got {0!r}".format(
                type(payload_specs).__name__
                if not isinstance(payload_specs, list)
                else "empty list"
            )
        )
    for index, spec in enumerate(payload_specs):
        if not isinstance(spec, dict):
            raise MalformedPayloadSpec(
                "payload_specs[{0}] must be a dict; got {1!r}".format(
                    index, type(spec).__name__
                )
            )
        for key in REQUIRED_SPEC_KEYS:
            if key not in spec:
                raise MalformedPayloadSpec(
                    "payload_specs[{0}] is missing required key {1!r}".format(
                        index, key
                    )
                )
            if not isinstance(spec[key], str) or len(spec[key]) == 0:
                raise MalformedPayloadSpec(
                    "payload_specs[{0}][{1!r}] must be a non-empty string".format(
                        index, key
                    )
                )


def _validate_common_inputs(common_inputs):
    if not isinstance(common_inputs, dict):
        raise MissingCommonInput(
            "common_inputs must be a dict; got {0!r}".format(
                type(common_inputs).__name__
            )
        )
    for key in REQUIRED_COMMON_INPUT_KEYS:
        if key not in common_inputs:
            raise MissingCommonInput(
                "common_inputs is missing required key {0!r}".format(key)
            )


def _snapshot_path_for(snapshot_dir, fixture_class):
    """Build the deterministic per-class snapshot path under snapshot_dir.

    The filename is `"{fixture_class}-batch-snapshot.json"`. The caller
    owns the directory; the runner does not create parent directories.
    """
    return os.path.join(snapshot_dir, "{0}-batch-snapshot.json".format(fixture_class))


def _per_run_summary(fixture_class, package, snapshot_written):
    """Derive the scaffold-internal per-run summary entry.

    The summary records only observation-level fields; it does not
    propagate adapter / manifest / payload evidence content beyond a
    small set of counts and identifiers.

    Per WO-36 (DC-039), six contract-status observation fields are
    surfaced from the package's existing `contract_checks_passed`,
    `contract_checks_failed`, `halt_events`,
    `disqualified_configurations`, and `all_events` fields:

    - `contract_status`: `"passed"` when failed count is 0 AND
      disqualified count is 0; `"failed"` otherwise.
    - `contract_checks_passed_count`: integer count.
    - `contract_checks_failed_count`: integer count.
    - `halt_count`: integer count of halt events recorded by the
      dry-run.
    - `disqualified_configuration_count`: integer count of
      configurations disqualified by the contract runner.
    - `measurement_recorded`: boolean; True if any
      `measurement_recorded` event appears in `all_events`. This is
      observation only and is not a quality or performance metric.
    """
    payload_evidence = package.get("payload_evidence")
    payload_entry_count = (
        payload_evidence["entry_count"]
        if isinstance(payload_evidence, dict)
        and isinstance(payload_evidence.get("entry_count"), int)
        else None
    )
    events = package.get("all_events", [])
    event_count = (
        package.get("event_count")
        if isinstance(package.get("event_count"), int)
        else len(events) if isinstance(events, list) else None
    )
    selection_made = package.get("selection_made")

    passed = package.get("contract_checks_passed") or []
    failed = package.get("contract_checks_failed") or []
    halts = package.get("halt_events") or []
    disqualified = package.get("disqualified_configurations") or []
    passed_count = len(passed) if isinstance(passed, list) else 0
    failed_count = len(failed) if isinstance(failed, list) else 0
    halt_count = len(halts) if isinstance(halts, list) else 0
    disqualified_count = len(disqualified) if isinstance(disqualified, list) else 0

    contract_status = (
        "passed" if failed_count == 0 and disqualified_count == 0 else "failed"
    )

    measurement_recorded = False
    if isinstance(events, list):
        for event in events:
            if isinstance(event, dict) and event.get("type") == "measurement_recorded":
                measurement_recorded = True
                break

    return {
        "fixture_class": fixture_class,
        "payload_entry_count": payload_entry_count,
        "event_count": event_count,
        "selection_made": selection_made,
        "snapshot_written": snapshot_written,
        "contract_status": contract_status,
        "contract_checks_passed_count": passed_count,
        "contract_checks_failed_count": failed_count,
        "halt_count": halt_count,
        "disqualified_configuration_count": disqualified_count,
        "measurement_recorded": measurement_recorded,
    }


def run_payload_batch(
    payload_specs,
    common_inputs,
    snapshot_dir=None,
    batch_summary_output_path=None,
):
    """Run the scaffold-internal payload batch dry-run.

    Validates the caller-provided specs and common inputs, invokes
    `run_toy_dry_run(...)` once per spec, and returns a batch summary
    dict.

    The batch summary uses neutral observation-only language and
    contains no evaluation, rank, winner, best, or production-ready claim.

    When `batch_summary_output_path` is provided (WO-37 / DC-040), the
    completed batch summary is persisted to that caller-provided path
    via `harness.artifact_snapshot.write_scaffold_snapshot(...)`. The
    in-memory returned summary then gains a `batch_snapshot_evidence`
    field carrying the writer's `{output_path, sha256, byte_length}`
    metadata. The on-disk JSON file is the pre-attachment summary and
    does not contain `batch_snapshot_evidence`; the metadata is
    attached only to the in-memory dict after the file has been
    written. When `batch_summary_output_path is None`, no file is
    written and the returned summary does not contain
    `batch_snapshot_evidence`.
    """
    _validate_specs(payload_specs)
    _validate_common_inputs(common_inputs)

    # Optional scaffold-internal `contract_checks` pass-through (WO-36 /
    # DC-039). When present in `common_inputs`, it is forwarded to
    # `run_toy_dry_run(...)` unchanged. When absent, the dry-run uses its
    # own scaffold-internal default toy contract checks. This key is a
    # test surface only; production contract checks remain Codex-owned.
    contract_checks_override = common_inputs.get("contract_checks")

    per_run_summaries = []
    for spec in payload_specs:
        fixture_class = spec["fixture_class"]
        payload_path = spec["payload_path"]
        if snapshot_dir is None:
            snapshot_output_path = None
            snapshot_written = False
        else:
            snapshot_output_path = _snapshot_path_for(snapshot_dir, fixture_class)
            snapshot_written = True
        package = run_toy_dry_run(
            fixture_path=common_inputs["fixture_path"],
            fixture_sha256=common_inputs["fixture_sha256"],
            config_path=common_inputs["config_path"],
            registered_config=common_inputs["registered_config"],
            deterministic_seed=common_inputs["deterministic_seed"],
            manifest_path=common_inputs["manifest_path"],
            expected_manifest_id=common_inputs["expected_manifest_id"],
            payload_path=payload_path,
            expected_fixture_class=fixture_class,
            snapshot_output_path=snapshot_output_path,
            contract_checks=contract_checks_override,
        )
        per_run_summaries.append(
            _per_run_summary(fixture_class, package, snapshot_written)
        )

    summary = {
        "batch_kind": "scaffold_payload_batch",
        "run_count": len(per_run_summaries),
        "fixture_classes": [s["fixture_class"] for s in per_run_summaries],
        "per_run_summaries": per_run_summaries,
        "selection_made": False,
        "batch_note": (
            "Scaffold-internal payload batch observation per "
            "ai-search/35-scaffold-payload-batch-runner.md. Each per-run "
            "summary records observation-only fields; the batch as a "
            "whole proposes no configuration and records only scaffold "
            "counts and booleans."
        ),
    }

    # WO-37 / DC-040: optional scaffold-internal batch summary snapshot.
    # When `batch_summary_output_path` is provided, persist the batch
    # summary to the caller-provided path via the existing artifact
    # snapshot writer, then attach the writer's returned metadata to
    # the in-memory summary as `batch_snapshot_evidence`. The on-disk
    # file is the pre-attachment summary; the metadata is added only
    # to the returned in-memory dict.
    if batch_summary_output_path is not None:
        snapshot_evidence = write_scaffold_snapshot(
            summary, batch_summary_output_path
        )
        summary["batch_snapshot_evidence"] = snapshot_evidence

    return summary
