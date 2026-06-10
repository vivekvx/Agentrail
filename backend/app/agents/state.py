from __future__ import annotations

from typing import Any, TypedDict


class AgentRunState(TypedDict, total=False):
    repo_path: str
    user_task: str
    expected_behavior: str
    plan: dict[str, Any]
    repo_scan: dict[str, Any]
    search_results: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    root_cause: str
    root_cause_analysis: dict[str, Any]
    analysis_mode: str  # "llm" | "heuristic"
    fix_strategy: dict[str, Any]
    patch_diff: str
    patch_mode: str  # "llm" | "annotated-diff" | "stub" | "legacy-demo"
    approval_status: str
    rejection_reason: str
    test_command: str
    test_result: dict[str, Any]
    verification_result: dict[str, Any]
    risk_score: dict[str, Any]
    final_report: str
