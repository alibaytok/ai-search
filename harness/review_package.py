"""Human review package assembler for harness runs.

Per `ai-search/16-benchmark-harness-scope.md` Section 12: the package
summarizes a run for Codex review. It does not recommend a winner, rank
configurations, or describe anything as best or production-ready. The
assembler enforces this at construction time by scanning the assembled
package for forbidden phrases and raising if any is found.
"""


FORBIDDEN_PHRASES = (
    "recommend",
    "recommended",
    "best",
    "winner",
    "winning",
    "production-ready",
    "production ready",
    "rank",
    "ranked",
    "ranking",
)


class ForbiddenLanguageInReviewPackage(Exception):
    """Raised when an assembled package contains a forbidden phrase."""


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
    # Other scalar types (int, float, bool, None) carry no forbidden language.


def _assert_no_forbidden_language(package):
    """Raise ForbiddenLanguageInReviewPackage if any forbidden phrase appears."""
    for text in _walk_strings(package):
        lowered = text.lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in lowered:
                raise ForbiddenLanguageInReviewPackage(
                    "Forbidden phrase '{0}' found in review package".format(phrase)
                )


def assemble(event_log, contract_runner, reproducibility_record):
    """Assemble a human review package summarizing the run.

    The package is harness-internal and intended for Codex review. It does
    not propose a configuration; selection is a Codex decision. The
    assembler raises ForbiddenLanguageInReviewPackage if any forbidden
    phrase appears anywhere in the assembled package.
    """
    events = event_log.events
    halts = [event for event in events if event["type"] == "halt"]
    contract_pass = [event for event in events if event["type"] == "contract_check_pass"]
    # Contract failures are recorded by ContractRunner as halt events with
    # reason "contract_check_failed" (see harness/contract_runner.py); the
    # filter matches that emission pattern. (WO-19 review-time fix to
    # `review_package.py`: the prior filter looked for type
    # "contract_check_failed" and never matched any actual failure.)
    contract_fail = [
        event
        for event in events
        if event["type"] == "halt"
        and event.get("reason") == "contract_check_failed"
    ]
    package = {
        "summary": "Harness run summary for Codex review.",
        "event_count": len(events),
        "all_events": events,
        "halt_events": halts,
        "contract_checks_passed": contract_pass,
        "contract_checks_failed": contract_fail,
        "disqualified_configurations": contract_runner.disqualified_configurations(),
        "reproducibility": reproducibility_record,
        "selection_made": False,
        "selection_note": (
            "Selection is a Codex decision; this package summarizes the run only "
            "and does not propose any configuration."
        ),
    }
    _assert_no_forbidden_language(package)
    return package
