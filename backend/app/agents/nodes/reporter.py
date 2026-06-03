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
                _fix_strategy_section(state),
                _patch_diff_section(state),
                _approval_section(state),
                _test_results_section(state),
                _verification_section(state),
                _risk_score_section(state),
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
    root_cause_analysis = state.get("root_cause_analysis")
    if isinstance(root_cause_analysis, dict):
        lines = ["## Root Cause"]
        summary = root_cause_analysis.get("summary")
        confidence = root_cause_analysis.get("confidence")
        root_cause = root_cause_analysis.get("root_cause")
        fix_strategy = root_cause_analysis.get("fix_strategy")
        evidence_refs = root_cause_analysis.get("evidence_refs")
        suspected_files = root_cause_analysis.get("suspected_files")
        uncertainty = root_cause_analysis.get("uncertainty")
        manual_checks = root_cause_analysis.get("manual_checks")

        if isinstance(summary, str) and summary:
            lines.append(f"Summary: {summary}")
        if isinstance(confidence, str) and confidence:
            lines.append(f"Confidence: {confidence}")
        if isinstance(root_cause, str) and root_cause:
            lines.append(f"Root Cause: {root_cause}")
        if isinstance(evidence_refs, list) and evidence_refs:
            lines.append("Evidence References:")
            lines.extend(
                f"- {reference}"
                for reference in evidence_refs
                if isinstance(reference, str) and reference
            )
        if isinstance(suspected_files, list) and suspected_files:
            lines.append("Suspected Files:")
            lines.extend(
                f"- {file_path}"
                for file_path in suspected_files
                if isinstance(file_path, str) and file_path
            )
        if isinstance(fix_strategy, str) and fix_strategy:
            lines.append(f"Fix Strategy: {fix_strategy}")
        if isinstance(uncertainty, list) and uncertainty:
            lines.append("Uncertainty:")
            lines.extend(
                f"- {item}"
                for item in uncertainty
                if isinstance(item, str) and item
            )
        if isinstance(manual_checks, list) and manual_checks:
            lines.append("Manual Checks:")
            lines.extend(
                f"- {item}"
                for item in manual_checks
                if isinstance(item, str) and item
            )
        return "\n".join(lines)

    root_cause = state.get("root_cause", "No root cause generated.")
    return f"## Root Cause\n{root_cause}"


def _patch_diff_section(state: AgentRunState) -> str:
    patch_diff = state.get("patch_diff")
    if not isinstance(patch_diff, str) or not patch_diff:
        return ""
    return f"## Patch Diff\n```diff\n{patch_diff.rstrip()}\n```"


def _fix_strategy_section(state: AgentRunState) -> str:
    fix_strategy = state.get("fix_strategy")
    if not isinstance(fix_strategy, dict):
        return ""

    lines = ["## Fix Strategy"]
    summary = fix_strategy.get("summary")
    confidence = fix_strategy.get("confidence")
    target_files = fix_strategy.get("target_files")
    change_plan = fix_strategy.get("change_plan")
    test_plan = fix_strategy.get("test_plan")
    risks = fix_strategy.get("risks")
    non_goals = fix_strategy.get("non_goals")

    if isinstance(summary, str) and summary:
        lines.append(f"Summary: {summary}")
    if isinstance(confidence, str) and confidence:
        lines.append(f"Confidence: {confidence}")
    if isinstance(target_files, list) and target_files:
        lines.append("Target Files:")
        lines.extend(
            f"- {file_path}"
            for file_path in target_files
            if isinstance(file_path, str) and file_path
        )
    if isinstance(change_plan, list) and change_plan:
        lines.append("Change Plan:")
        lines.extend(
            f"- {item}"
            for item in change_plan
            if isinstance(item, str) and item
        )
    if isinstance(test_plan, list) and test_plan:
        lines.append("Test Plan:")
        lines.extend(
            f"- {item}"
            for item in test_plan
            if isinstance(item, str) and item
        )
    if isinstance(risks, list) and risks:
        lines.append("Risks:")
        lines.extend(
            f"- {item}"
            for item in risks
            if isinstance(item, str) and item
        )
    if isinstance(non_goals, list) and non_goals:
        lines.append("Non-Goals:")
        lines.extend(
            f"- {item}"
            for item in non_goals
            if isinstance(item, str) and item
        )
    return "\n".join(lines)


def _approval_section(state: AgentRunState) -> str:
    approval_status = state.get("approval_status")
    if approval_status == "approved":
        return "## Approval\nPatch approved by user."
    if approval_status == "rejected":
        reason = state.get("rejection_reason", "Patch rejected by user.")
        return f"## Approval\nPatch rejected by user.\n\nReason: {reason}"
    return ""


def _test_results_section(state: AgentRunState) -> str:
    test_result = state.get("test_result")
    if not isinstance(test_result, dict):
        return ""

    command = test_result.get("command")
    provider = test_result.get("provider", "local")
    status = test_result.get("status", "unknown")
    exit_code = test_result.get("exit_code")
    duration_ms = test_result.get("duration_ms")
    stdout = test_result.get("stdout", "")
    stderr = test_result.get("stderr", "")

    lines = ["## Test Results", f"Status: {status}"]
    if isinstance(provider, str):
        label = "E2B Sandbox" if provider == "e2b" else "Local Runner"
        lines.append(f"Provider: {label}")
    if command:
        lines.append(f"Command: `{command}`")
    if exit_code is not None:
        lines.append(f"Exit Code: {exit_code}")
    if duration_ms is not None:
        lines.append(f"Duration: {duration_ms}ms")
    if isinstance(stdout, str) and stdout:
        lines.extend(["Stdout:", "```text", stdout.rstrip(), "```"])
    if isinstance(stderr, str) and stderr:
        lines.extend(["Stderr:", "```text", stderr.rstrip(), "```"])
    return "\n".join(lines)


def _verification_section(state: AgentRunState) -> str:
    verification_result = state.get("verification_result")
    if not isinstance(verification_result, dict):
        return ""

    lines = [
        "## Verification",
        f"Status: {verification_result.get('status', 'unknown')}",
        f"Confidence: {verification_result.get('confidence', 'low')}",
        f"Summary: {verification_result.get('summary', '')}",
    ]
    checks = verification_result.get("checks", [])
    if isinstance(checks, list) and checks:
        lines.append("Checklist:")
        for check in checks:
            if not isinstance(check, dict):
                continue
            name = check.get("name", "Check")
            status = check.get("status", "unknown")
            details = check.get("details", "")
            lines.append(f"- {name}: {status} - {details}")
    return "\n".join(lines)


def _risk_score_section(state: AgentRunState) -> str:
    risk_score = state.get("risk_score")
    if not isinstance(risk_score, dict):
        return ""

    lines = [
        "## Risk Score",
        f"Level: {risk_score.get('level', 'unknown')}",
        f"Score: {risk_score.get('score', 0)}",
        f"Summary: {risk_score.get('summary', '')}",
    ]
    factors = risk_score.get("factors", [])
    if isinstance(factors, list) and factors:
        lines.append("Factors:")
        for factor in factors:
            if not isinstance(factor, dict):
                continue
            name = factor.get("name", "Factor")
            impact = factor.get("impact", "unknown")
            details = factor.get("details", "")
            lines.append(f"- {name}: {impact} - {details}")
    lines.append(
        f"Recommended Action: {risk_score.get('recommended_action', 'Review manually before proceeding.')}",
    )
    return "\n".join(lines)


def _next_step_section() -> str:
    return (
        "## Next Step\n"
        "Review the evidence, root cause, patch diff, verification, and risk score before applying changes."
    )
