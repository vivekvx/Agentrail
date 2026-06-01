from __future__ import annotations

from dataclasses import asdict

from app.agents.state import AgentRunState
from app.tools.repo_scanner import scan_repository


def repo_scanner_node(state: AgentRunState) -> dict[str, object]:
    repo_path = state["repo_path"]
    return {
        "repo_scan": asdict(scan_repository(repo_path)),
    }
