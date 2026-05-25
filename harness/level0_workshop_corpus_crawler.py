"""Local-only raw prompt candidate crawler for Level 0 workshop coverage."""

import hashlib
import json
import os
import re


RAW_CANDIDATE_REPORT_KIND = "level0_workshop_raw_candidate_report"

MAX_RAW_CANDIDATES = 500

SOURCE_KINDS = (
    "planning_doc",
    "workshop_seed",
    "matrix_file",
)

EXTRACTION_METHODS = (
    "markdown_prompt_line_v1",
    "matrix_prompt_text_v1",
)

ADMISSION_STATUSES = ("raw",)

RAW_CANDIDATE_FIELDS = (
    "candidate_id",
    "source_kind",
    "source_path",
    "source_line",
    "extraction_method",
    "source_sha256",
    "prompt_text_original",
    "prompt_text_normalized",
    "language_tag",
    "admission_status",
    "admission_reason",
)

RAW_CANDIDATE_REPORT_FIELDS = (
    "raw_candidate_report_kind",
    "source_count",
    "source_paths",
    "candidate_count",
    "max_candidate_count",
    "candidates",
    "corpus_admission_authorized",
    "expected_fields_generated",
    "parser_invocation_performed",
    "network_access_performed",
)

DEFAULT_LOCAL_SOURCE_PATHS = (
    os.path.join("ai-search", "00-level0-awesome-copilot-workshop-seed.md"),
    os.path.join("ai-search", "00-level0-prompt-set.md"),
    os.path.join("ai-search", "00-level0-item-selection.md"),
    os.path.join(
        "harness",
        "intent_test_matrices",
        "L0-WS-PARSER-QUALITY-MINI-V1.intent.matrix.json",
    ),
)

_PROMPT_STARTERS = (
    "add",
    "author",
    "build",
    "configure",
    "cook",
    "create",
    "define",
    "deploy",
    "explain",
    "generate",
    "how",
    "make",
    "review",
    "run",
    "set up",
    "skip",
    "summarize",
    "triage",
    "what",
    "write",
)


class CorpusCrawlerMalformedSource(Exception):
    """Raised when a local source path is outside the crawler contract."""


class CorpusCrawlerTooManyCandidates(Exception):
    """Raised when extraction exceeds the bounded raw-candidate cap."""


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _read_ascii_source(path):
    with open(path, "rb") as handle:
        payload = handle.read()
    payload.decode("ascii")
    return payload


def _display_path(path, repo_root):
    absolute = os.path.abspath(path)
    root = os.path.abspath(repo_root)
    try:
        relative = os.path.relpath(absolute, root)
    except ValueError:
        relative = absolute
    if relative.startswith(".."):
        return absolute.replace(os.sep, "/")
    return relative.replace(os.sep, "/")


def _validate_source_path(path):
    if not isinstance(path, str) or not path:
        raise CorpusCrawlerMalformedSource("source path must be a non-empty string")
    if "://" in path or path.startswith("\\\\"):
        raise CorpusCrawlerMalformedSource("crawler sources must be local files")
    if not os.path.exists(path):
        raise CorpusCrawlerMalformedSource("source path does not exist")
    if not os.path.isfile(path):
        raise CorpusCrawlerMalformedSource("source path must be a file")


def _source_kind(path):
    normalized = path.replace("\\", "/")
    name = os.path.basename(normalized)
    if name.endswith(".intent.matrix.json"):
        return "matrix_file"
    if "workshop" in normalized or "prompt" in normalized:
        return "workshop_seed"
    return "planning_doc"


def _normalize_prompt(text):
    text = text.strip().strip("|").strip()
    text = text.strip("`").strip('"').strip("'").strip()
    text = re.sub(r"\s+", " ", text)
    return text


def _looks_like_prompt(text):
    normalized = _normalize_prompt(text)
    if len(normalized) < 10 or len(normalized) > 240:
        return False
    if normalized.startswith("#"):
        return False
    if normalized.startswith("- ["):
        return False
    if re.match(r"^[A-Z][A-Za-z ]{1,40}:", normalized):
        return False
    lowered = normalized.lower()
    if lowered.startswith(("http", "www.")):
        return False
    return any(
        lowered == starter or lowered.startswith(starter + " ")
        for starter in _PROMPT_STARTERS
    )


def _line_cells(line):
    if "|" not in line:
        return [line]
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _extract_markdown_candidates(payload):
    text = payload.decode("ascii")
    extracted = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        for cell in _line_cells(line):
            normalized = _normalize_prompt(cell)
            if _looks_like_prompt(normalized):
                extracted.append(
                    {
                        "line": line_number,
                        "method": "markdown_prompt_line_v1",
                        "original": cell,
                        "normalized": normalized,
                    }
                )
    return extracted


def _extract_matrix_candidates(payload):
    matrix = json.loads(payload.decode("ascii"))
    cases = matrix.get("cases", [])
    extracted = []
    for index, case in enumerate(cases, start=1):
        prompt = case.get("prompt_text")
        if isinstance(prompt, str) and prompt.strip():
            extracted.append(
                {
                    "line": index,
                    "method": "matrix_prompt_text_v1",
                    "original": prompt,
                    "normalized": _normalize_prompt(prompt),
                }
            )
    return extracted


def _language_tag(text):
    try:
        text.encode("ascii")
    except UnicodeEncodeError:
        return "non_ascii"
    return "en"


def _candidate(candidate_index, source_kind, source_path, source_sha256, item):
    candidate = {
        "candidate_id": "RC-{0:05d}".format(candidate_index),
        "source_kind": source_kind,
        "source_path": source_path,
        "source_line": item["line"],
        "extraction_method": item["method"],
        "source_sha256": source_sha256,
        "prompt_text_original": item["original"],
        "prompt_text_normalized": item["normalized"],
        "language_tag": _language_tag(item["normalized"]),
        "admission_status": "raw",
        "admission_reason": "pending_human_review",
    }
    if tuple(candidate) != RAW_CANDIDATE_FIELDS:
        raise AssertionError("raw candidate fields drifted")
    if candidate["source_kind"] not in SOURCE_KINDS:
        raise AssertionError("unknown source kind")
    if candidate["extraction_method"] not in EXTRACTION_METHODS:
        raise AssertionError("unknown extraction method")
    if candidate["admission_status"] not in ADMISSION_STATUSES:
        raise AssertionError("unknown admission status")
    return candidate


def crawl_level0_raw_candidates(source_paths=None, repo_root=None):
    """Extract deterministic raw prompt candidates from local ASCII sources."""
    if source_paths is None:
        source_paths = DEFAULT_LOCAL_SOURCE_PATHS
    if repo_root is None:
        repo_root = os.getcwd()
    if not isinstance(source_paths, (list, tuple)):
        raise CorpusCrawlerMalformedSource("source_paths must be a list or tuple")

    candidates = []
    seen = set()
    display_paths = []
    for path in source_paths:
        _validate_source_path(path)
        payload = _read_ascii_source(path)
        display_path = _display_path(path, repo_root)
        display_paths.append(display_path)
        source_sha256 = _sha256_bytes(payload)
        source_kind = _source_kind(display_path)
        if source_kind == "matrix_file":
            extracted = _extract_matrix_candidates(payload)
        else:
            extracted = _extract_markdown_candidates(payload)
        for item in extracted:
            normalized = item["normalized"]
            dedupe_key = normalized.lower()
            if dedupe_key in seen:
                continue
            seen.add(dedupe_key)
            candidates.append(
                _candidate(
                    len(candidates) + 1,
                    source_kind,
                    display_path,
                    source_sha256,
                    item,
                )
            )
            if len(candidates) > MAX_RAW_CANDIDATES:
                raise CorpusCrawlerTooManyCandidates(
                    "raw candidate cap exceeded"
                )

    report = {
        "raw_candidate_report_kind": RAW_CANDIDATE_REPORT_KIND,
        "source_count": len(source_paths),
        "source_paths": display_paths,
        "candidate_count": len(candidates),
        "max_candidate_count": MAX_RAW_CANDIDATES,
        "candidates": candidates,
        "corpus_admission_authorized": False,
        "expected_fields_generated": False,
        "parser_invocation_performed": False,
        "network_access_performed": False,
    }
    if tuple(report) != RAW_CANDIDATE_REPORT_FIELDS:
        raise AssertionError("raw candidate report fields drifted")
    return report
