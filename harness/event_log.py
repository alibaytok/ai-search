"""Event log for harness runs (harness-internal; not a production contract).

Per `ai-search/16-benchmark-harness-scope.md` Section 13 and DC-020 halt
behavior: events are append-only and timestamped; halt events are explicit
and recorded with a reason and any relevant fields. The log format is
scaffold-internal and may not be treated as a production artifact schema.
"""

from datetime import datetime, timezone


class EventLog:
    """Append-only event log for a single harness run."""

    def __init__(self):
        self._events = []

    def append(self, event_type, **fields):
        """Append an event with the given type and fields.

        Timestamps are ISO 8601 UTC strings derived at append time. Fields
        are stored verbatim and not interpreted by the log itself.
        """
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": event_type,
        }
        entry.update(fields)
        self._events.append(entry)

    def halt(self, reason, **fields):
        """Append an explicit halt event with the given reason and fields."""
        self.append("halt", reason=reason, **fields)

    @property
    def events(self):
        """Return a shallow copy of the event list for inspection.

        Returning a copy preserves append-only semantics from the caller's
        perspective: callers cannot mutate the underlying list or the
        stored event dictionaries.
        """
        return [dict(event) for event in self._events]

    def has_halt(self):
        """Return True if any halt event has been recorded."""
        return any(event["type"] == "halt" for event in self._events)
