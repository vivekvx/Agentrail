from __future__ import annotations

from app.agents.state import AgentRunState
from app.core.config import get_settings
from app.services.llm_provider import analyze_root_cause

MAX_EVIDENCE_REFERENCES = 3


def root_cause_node(state: AgentRunState) -> dict[str, object]:
    user_task = state.get("user_task", "")
    evidence = _valid_evidence_items(state.get("evidence", []))
    fallback = _deterministic_root_cause(user_task, evidence)

    settings = get_settings()
    if not settings.llm_root_cause_enabled:
        return fallback

    analysis = analyze_root_cause(
        evidence,
        user_task,
        state.get("expected_behavior", ""),
        _repo_summary(state),
        settings=settings,
    )
    if analysis is None:
        return {
            "root_cause": (
                f"{fallback['root_cause']} "
                "LLM root cause analysis was unavailable; used deterministic fallback."
            ),
        }

    return {
        "root_cause": analysis.root_cause,
        "root_cause_analysis": analysis.model_dump(mode="json"),
    }


def _deterministic_root_cause(
    user_task: str,
    evidence: list[dict[str, object]],
) -> dict[str, object]:
    if not evidence:
        return {
            "root_cause": (
                f"No root cause identified yet for task '{user_task}'. "
                "No evidence was collected from code search results."
            ),
        }

    references = [_reference(item) for item in evidence[:MAX_EVIDENCE_REFERENCES]]
    snippets = [_first_snippet_line(item) for item in evidence[:MAX_EVIDENCE_REFERENCES]]
    root_cause = (
        f"Potential root cause for task '{user_task}' is located in "
        f"{'; '.join(references)}. Evidence snippets: {' | '.join(snippets)}."
    )
    return {"root_cause": root_cause}


def _repo_summary(state: AgentRunState) -> str:
    repo_scan = state.get("repo_scan", {})
    if not isinstance(repo_scan, dict):
        return ""

    detected_stack = repo_scan.get("detected_stack", [])
    probable_backend = repo_scan.get("probable_backend_directory")
    probable_frontend = repo_scan.get("probable_frontend_directory")

    parts: list[str] = []
    if isinstance(detected_stack, list):
        stack_items = [item for item in detected_stack if isinstance(item, str)]
        if stack_items:
            parts.append(f"Detected stack: {', '.join(stack_items)}")
    if isinstance(probable_backend, str) and probable_backend:
        parts.append(f"Backend directory: {probable_backend}")
    if isinstance(probable_frontend, str) and probable_frontend:
        parts.append(f"Frontend directory: {probable_frontend}")
    return ". ".join(parts)


def _valid_evidence_items(evidence: list[dict[str, object]]) -> list[dict[str, object]]:
    valid_items: list[dict[str, object]] = []
    for item in evidence:
        if not isinstance(item.get("file_path"), str):
            continue
        if not isinstance(item.get("start_line"), int):
            continue
        if not isinstance(item.get("end_line"), int):
            continue
        if not isinstance(item.get("snippet"), str):
            continue
        valid_items.append(item)
    return valid_items


def _reference(evidence_item: dict[str, object]) -> str:
    return (
        f"{evidence_item['file_path']}:"
        f"{evidence_item['start_line']}-{evidence_item['end_line']}"
    )


def _first_snippet_line(evidence_item: dict[str, object]) -> str:
    snippet = str(evidence_item["snippet"])
    first_line = snippet.splitlines()[0] if snippet else ""
    return first_line.strip()
