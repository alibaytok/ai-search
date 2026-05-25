"""Immutable FRAME-B signal-family overlay builder."""


SIGNAL_FAMILIES_OVERLAY_PATCH_KINDS = ("frame_b_canonical_addition",)


class SignalFamiliesOverlayMalformedDelta(Exception):
    """Raised when a signal-family overlay delta is outside schema."""


class SignalFamiliesOverlayUnknownFamily(Exception):
    """Raised when a delta references a missing family_id."""


def _halt(event_log, reason, **payload):
    if event_log is not None and hasattr(event_log, "halt"):
        event_log.halt(reason=reason, **payload)


def _validate_term(term):
    if not isinstance(term, str) or not term.strip():
        raise SignalFamiliesOverlayMalformedDelta(
            "canonical addition terms must be non-empty strings"
        )
    try:
        term.encode("ascii")
    except UnicodeEncodeError as exc:
        raise SignalFamiliesOverlayMalformedDelta(
            "canonical addition terms must be ASCII"
        ) from exc
    if term != term.lower():
        raise SignalFamiliesOverlayMalformedDelta(
            "canonical addition terms must be lowercase"
        )
    if term != term.strip():
        raise SignalFamiliesOverlayMalformedDelta(
            "canonical addition terms must be trimmed"
        )


def validate_signal_families_delta(delta, event_log=None):
    if not isinstance(delta, dict):
        _halt(event_log, "signal_families_overlay_non_dict_delta")
        raise SignalFamiliesOverlayMalformedDelta("delta must be a dict")
    if delta.get("patch_kind") not in SIGNAL_FAMILIES_OVERLAY_PATCH_KINDS:
        _halt(event_log, "signal_families_overlay_unknown_patch_kind")
        raise SignalFamiliesOverlayMalformedDelta("unknown patch_kind")
    additions = delta.get("canonical_additions")
    if not isinstance(additions, dict) or not additions:
        _halt(event_log, "signal_families_overlay_invalid_additions")
        raise SignalFamiliesOverlayMalformedDelta(
            "canonical_additions must be a non-empty dict"
        )
    for family_id, terms in additions.items():
        if not isinstance(family_id, str) or not family_id:
            raise SignalFamiliesOverlayMalformedDelta(
                "family_id must be non-empty string"
            )
        if not isinstance(terms, list) or not terms:
            raise SignalFamiliesOverlayMalformedDelta(
                "canonical additions must be non-empty lists"
            )
        for term in terms:
            _validate_term(term)


def build_signal_families_overlay(base_signal_families, delta, event_log=None):
    """Return an immutable tuple with canonical additions applied."""
    validate_signal_families_delta(delta, event_log=event_log)
    by_id = {family.family_id: family for family in base_signal_families}
    overlay = []
    for family in base_signal_families:
        additions = delta["canonical_additions"].get(family.family_id, [])
        if not additions:
            overlay.append(family)
            continue
        existing = set(family.canonical_terms)
        next_terms = list(family.canonical_terms)
        for term in additions:
            if term not in existing:
                next_terms.append(term)
                existing.add(term)
        overlay.append(family._replace(canonical_terms=tuple(next_terms)))
    unknown = set(delta["canonical_additions"]) - set(by_id)
    if unknown:
        _halt(
            event_log,
            "signal_families_overlay_unknown_family",
            unknown=sorted(unknown),
        )
        raise SignalFamiliesOverlayUnknownFamily(
            "unknown family_id: {0}".format(sorted(unknown))
        )
    return tuple(overlay)
