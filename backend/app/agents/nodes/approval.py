from __future__ import annotations

from langgraph.types import interrupt

from app.agents.state import AgentRunState


def approval_node(state: AgentRunState) -> dict[str, object]:
    decision = interrupt(_approval_payload(state))
    if decision == "approve":
        return {"approval_status": "approved"}
    return {
        "approval_status": "rejected",
        "rejection_reason": "Patch rejected by user.",
    }


def _approval_payload(state: AgentRunState) -> dict[str, object]:
    evidence = state.get("evidence", [])
    return {
        "question": "Approve this patch?",
        "patch_diff": state.get("patch_diff", ""),
        "root_cause": state.get("root_cause", ""),
        "evidence_count": len(evidence),
        "evidence_summary": _evidence_summary(evidence),
    }


def _evidence_summary(evidence: list[dict[str, object]]) -> list[str]:
    summary: list[str] = []
    for item in evidence:
        file_path = item.get("file_path")
        start_line = item.get("start_line")
        end_line = item.get("end_line")
        if (
            isinstance(file_path, str)
            and isinstance(start_line, int)
            and isinstance(end_line, int)
        ):
            summary.append(f"{file_path}:{start_line}-{end_line}")
    return summary
