from __future__ import annotations

from app.agents.state import AgentRunState
from app.core.config import get_settings
from app.services.llm_provider import propose_fix_strategy


def fix_strategy_node(state: AgentRunState) -> dict[str, object]:
    settings = get_settings()
    if not settings.llm_fix_strategy_enabled:
        return {}
    if not settings.openai_api_key:
        return {}

    evidence = _valid_evidence_items(state.get("evidence", []))
    root_cause_analysis = state.get("root_cause_analysis")
    if not evidence and not isinstance(root_cause_analysis, dict):
        return {}

    strategy = propose_fix_strategy(
        evidence,
        state.get("user_task", ""),
        state.get("expected_behavior", ""),
        _repo_summary(state),
        state.get("root_cause", ""),
        root_cause_analysis if isinstance(root_cause_analysis, dict) else None,
        settings=settings,
    )
    if strategy is None:
        return {}

    return {"fix_strategy": strategy.model_dump(mode="json")}


def _repo_summary(state: AgentRunState) -> str:
    repo_scan = state.get("repo_scan", {})
    if not isinstance(repo_scan, dict):
        return ""

    parts: list[str] = []
    detected_stack = repo_scan.get("detected_stack", [])
    if isinstance(detected_stack, list):
        stack_items = [item for item in detected_stack if isinstance(item, str)]
        if stack_items:
            parts.append(f"Detected stack: {', '.join(stack_items)}")
    probable_backend = repo_scan.get("probable_backend_directory")
    if isinstance(probable_backend, str) and probable_backend:
        parts.append(f"Backend directory: {probable_backend}")
    probable_frontend = repo_scan.get("probable_frontend_directory")
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
