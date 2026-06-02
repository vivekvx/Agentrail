from __future__ import annotations

from app.agents.state import AgentRunState


def reporter_node(state: AgentRunState) -> dict[str, object]:
    return {
        "final_report": "\n\n".join(
            [
                "# DevPilot Verify Report",
                _task_section(state),
                _detected_stack_section(state),
                _investigation_plan_section(state),
                _files_found_section(state),
                _evidence_section(state),
                _root_cause_section(state),
                _patch_diff_section(state),
                _approval_section(state),
                _next_step_section(),
            ],
        ),
    }


def _task_section(state: AgentRunState) -> str:
    return f"## Task\n{state.get('user_task', 'No task provided.')}"


def _detected_stack_section(state: AgentRunState) -> str:
    repo_scan = state.get("repo_scan", {})
    detected_stack = repo_scan.get("detected_stack", [])
    if not isinstance(detected_stack, list) or not detected_stack:
        return "## Detected Stack\nNo stack detected."
    return "## Detected Stack\n" + "\n".join(
        f"- {item}" for item in detected_stack if isinstance(item, str)
    )


def _investigation_plan_section(state: AgentRunState) -> str:
    plan = state.get("plan", {})
    summary = plan.get("summary", "No investigation plan generated.")
    search_queries = plan.get("search_queries", [])
    lines = ["## Investigation Plan", str(summary)]
    if isinstance(search_queries, list) and search_queries:
        lines.append("Search queries:")
        lines.extend(f"- {query}" for query in search_queries if isinstance(query, str))
    return "\n".join(lines)


def _files_found_section(state: AgentRunState) -> str:
    search_results = state.get("search_results", [])
    files: list[str] = []
    for result in search_results:
        file_path = result.get("file_path")
        if isinstance(file_path, str) and file_path not in files:
            files.append(file_path)
    if not files:
        return "## Files Found\nNo files found from code search."
    return "## Files Found\n" + "\n".join(f"- {file_path}" for file_path in files)


def _evidence_section(state: AgentRunState) -> str:
    evidence = state.get("evidence", [])
    lines = ["## Evidence"]
    if not evidence:
        lines.append("No evidence collected.")
        return "\n".join(lines)

    for item in evidence:
        file_path = item.get("file_path")
        start_line = item.get("start_line")
        end_line = item.get("end_line")
        snippet = item.get("snippet")
        reason = item.get("reason")
        if not isinstance(file_path, str):
            continue
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            continue
        lines.append(f"### {file_path}:{start_line}-{end_line}")
        if isinstance(reason, str):
            lines.append(f"Reason: {reason}")
        if isinstance(snippet, str):
            lines.append("```text")
            lines.append(snippet)
            lines.append("```")

    if len(lines) == 1:
        lines.append("No evidence collected.")
    return "\n".join(lines)


def _root_cause_section(state: AgentRunState) -> str:
    root_cause = state.get("root_cause", "No root cause generated.")
    return f"## Root Cause\n{root_cause}"


def _patch_diff_section(state: AgentRunState) -> str:
    patch_diff = state.get("patch_diff")
    if not isinstance(patch_diff, str) or not patch_diff:
        return ""
    return f"## Patch Diff\n```diff\n{patch_diff.rstrip()}\n```"


def _approval_section(state: AgentRunState) -> str:
    approval_status = state.get("approval_status")
    if approval_status == "approved":
        return "## Approval\nPatch approved by user."
    if approval_status == "rejected":
        reason = state.get("rejection_reason", "Patch rejected by user.")
        return f"## Approval\nPatch rejected by user.\n\nReason: {reason}"
    return ""


def _next_step_section() -> str:
    return (
        "## Next Step\n"
        "Review the evidence, root cause, and patch diff before applying changes. "
        "No tests were run by this reporter node."
    )
