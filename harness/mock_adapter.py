"""Scaffold-internal mock retrieval adapter.

Per WO-22 (DC-025): this is a deterministic, toy-only mock adapter that
conforms to the WO-21 adapter contract boundary recorded in
`ai-search/21-retrieval-adapter-contract.md`. It is not a real retrieval
implementation and not architecture selection. The adapter performs no
file I/O, no network calls, no third-party imports, and uses no
retrieval/indexing/ranking library. It reads only the already-loaded toy
fixture and configuration objects passed to it.

Output is a deterministic observation dictionary with the five planes
named in `21-retrieval-adapter-contract.md` Section 3:

  - official_route_results
  - candidate_route_results
  - normalized_material_support_results
  - source_quality_constraint_observations
  - trace_outcome_signal_observations

Empty planes are recorded explicitly via the `empty_planes` field. The
adapter does not select, recommend, rank, declare winner, or declare
best/production-ready. The adapter does not consume `benchmark-fixtures/`
content; it operates on already-loaded objects passed in by the caller.
"""


PLANE_NAMES = (
    "official_route_results",
    "candidate_route_results",
    "normalized_material_support_results",
    "source_quality_constraint_observations",
    "trace_outcome_signal_observations",
)


def _fixture_record_id(fixture):
    """Return a stable identifier from the toy fixture, or None."""
    if isinstance(fixture, dict):
        sample = fixture.get("sample_record")
        if isinstance(sample, dict):
            return sample.get("id")
    return None


def _configuration_id(configuration):
    """Return the configuration identifier, or None."""
    if isinstance(configuration, dict):
        return configuration.get("id")
    return None


def run_mock_adapter(fixture, configuration):
    """Run the scaffold-internal mock adapter and return benchmark observations only.

    `fixture` and `configuration` are already-loaded objects (typically
    dicts produced upstream by `harness/fixture_loader.py` and
    `harness/config_loader.py`). The adapter does not open, read, write,
    or otherwise touch any file or network resource. It derives a
    deterministic observation dictionary from the inputs and returns it.

    Output contract (per `21-retrieval-adapter-contract.md` Section 3):
    five planes are present at every call, with empty planes marked in
    `empty_planes`. Plane separation is preserved: each entry carries a
    `plane` marker matching the plane key it appears under, and
    route-bearing entries carry an explicit `is_candidate` / `is_official`
    pair and an `executability` indicator from the set
    {"executable_official", "candidate_only_non_executable_as_official",
    "non_route_support_material"}.
    """
    fixture_record_id = _fixture_record_id(fixture)
    configuration_id = _configuration_id(configuration)

    # Official plane: empty by design. The mock adapter does not produce
    # validated official routes; no fixture-derived entry crosses the
    # validation/promotion boundary.
    official_route_results = []

    # Candidate plane: one deterministic toy candidate when both fixture
    # and configuration identifiers are available. The candidate is
    # explicitly marked non-official, non-executable as official, and
    # carries explicit absence markers for source/lifecycle/policy refs.
    candidate_route_results = []
    if fixture_record_id is not None and configuration_id is not None:
        candidate_route_results.append(
            {
                "plane": "candidate_route_results",
                "is_candidate": True,
                "is_official": False,
                "executability": "candidate_only_non_executable_as_official",
                "source_provenance_reference": None,
                "source_provenance_reference_is_absent": True,
                "lifecycle_state_reference": None,
                "lifecycle_state_reference_is_absent": True,
                "policy_risk_disposition_reference": None,
                "policy_risk_disposition_reference_is_absent": True,
                "fixture_record_id_observed": fixture_record_id,
                "configuration_id_observed": configuration_id,
            }
        )

    # Normalized material support plane: one deterministic toy observation
    # when a fixture record is available. The entry is explicitly marked
    # non-route support material and never as a candidate or official route.
    normalized_material_support_results = []
    if fixture_record_id is not None:
        normalized_material_support_results.append(
            {
                "plane": "normalized_material_support_results",
                "is_candidate": False,
                "is_official": False,
                "executability": "non_route_support_material",
                "source_provenance_reference": None,
                "source_provenance_reference_is_absent": True,
                "fixture_record_id_observed": fixture_record_id,
            }
        )

    # Source quality constraint observations: one explicit absence record.
    # The mock adapter does not consult any qualified source; the absence is
    # recorded rather than treated as presence.
    source_quality_constraint_observations = [
        {
            "plane": "source_quality_constraint_observations",
            "is_candidate": False,
            "is_official": False,
            "executability": "non_route_support_material",
            "qualification_status_reference": None,
            "qualification_status_reference_is_absent": True,
            "observation_note": (
                "Mock adapter consulted no qualified source; absence is recorded."
            ),
        }
    ]

    # Trace and outcome signal observations: empty by design. The plane is
    # reserved for future Codex-authorized admission of bounded signals.
    # The mock adapter does not admit any such signal.
    trace_outcome_signal_observations = []

    plane_results = {
        "official_route_results": official_route_results,
        "candidate_route_results": candidate_route_results,
        "normalized_material_support_results": normalized_material_support_results,
        "source_quality_constraint_observations": source_quality_constraint_observations,
        "trace_outcome_signal_observations": trace_outcome_signal_observations,
    }

    empty_planes = [plane for plane in PLANE_NAMES if not plane_results[plane]]

    output = {
        "adapter_kind": "mock_scaffold_internal",
        "official_route_results": official_route_results,
        "candidate_route_results": candidate_route_results,
        "normalized_material_support_results": normalized_material_support_results,
        "source_quality_constraint_observations": source_quality_constraint_observations,
        "trace_outcome_signal_observations": trace_outcome_signal_observations,
        "empty_planes": empty_planes,
        "selection_made": False,
        "selection_note": (
            "Mock adapter does not propose any configuration. Selection authority "
            "remains with Codex under the Indexing Excellence Gate."
        ),
    }
    return output
