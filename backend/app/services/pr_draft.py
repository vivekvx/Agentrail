from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel


class PRDraft(BaseModel):
    title: str
    summary: str
    linked_issue: str | None
    root_cause: str
    fix_strategy_summary: str | None
    files_changed: list[str]
    patch_summary: str
    test_evidence: list[str]
    verification_status: str
    risk_level: str
    rollback_plan: str
    manual_review_checklist: list[str]
    body_markdown: str


def generate_pr_draft(run_state_or_model: object) -> PRDraft:
    state = _state_dict(run_state_or_model)
    title = _title(state)
    linked_issue = _linked_issue(state)
    root_cause = _sanitize(_root_cause(state))
    fix_strategy_summary = _sanitize(_fix_strategy_summary(state))
    files_changed = _patch_files(_string(state.get("patch_diff")))
    patch_summary = _patch_summary(files_changed, state)
    test_evidence = _test_evidence(state)
    verification_status = _verification_status(state)
    risk_level = _risk_level(state)
    summary = _summary(state, files_changed, verification_status, risk_level)
    rollback_plan = _rollback_plan(files_changed)
    checklist = _manual_review_checklist(risk_level)
    body_markdown = _body_markdown(
        summary=summary,
        linked_issue=linked_issue,
        root_cause=root_cause,
        fix_strategy_summary=fix_strategy_summary,
        files_changed=files_changed,
        patch_summary=patch_summary,
        test_evidence=test_evidence,
        verification_status=verification_status,
        risk_level=risk_level,
        risk_summary=_risk_summary(state),
        rollback_plan=rollback_plan,
        checklist=checklist,
    )
    return PRDraft(
        title=title,
        summary=summary,
        linked_issue=linked_issue,
        root_cause=root_cause,
        fix_strategy_summary=fix_strategy_summary,
        files_changed=files_changed,
        patch_summary=patch_summary,
        test_evidence=test_evidence,
        verification_status=verification_status,
        risk_level=risk_level,
        rollback_plan=rollback_plan,
        manual_review_checklist=checklist,
        body_markdown=body_markdown,
    )


def _state_dict(value: object) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    state: dict[str, Any] = {}
    for name in (
        "user_task",
        "expected_behavior",
        "issue_context",
        "root_cause",
        "root_cause_analysis",
        "fix_strategy",
        "patch_diff",
        "approval_status",
        "test_result",
        "verification_result",
        "risk_score",
        "final_report",
    ):
        if hasattr(value, name):
            state[name] = getattr(value, name)
    return state


def _title(state: dict[str, Any]) -> str:
    task = _sanitize(_string(state.get("user_task"))).strip()
    first_line = task.splitlines()[0].strip() if task else "Prepare Agentrail patch"
    first_line = first_line.rstrip(".")
    if not first_line.lower().startswith(("fix ", "add ", "update ", "remove ", "restore ")):
        first_line = f"Fix {first_line[0].lower()}{first_line[1:]}" if first_line else "Prepare patch preview"
    return first_line[:96]


def _linked_issue(state: dict[str, Any]) -> str | None:
    issue_context = _dict(state.get("issue_context"))
    issue_url = issue_context.get("issue_url")
    return issue_url if isinstance(issue_url, str) and issue_url else None


def _root_cause(state: dict[str, Any]) -> str:
    analysis = _dict(state.get("root_cause_analysis"))
    analysis_cause = analysis.get("root_cause")
    if isinstance(analysis_cause, str) and analysis_cause.strip():
        return analysis_cause.strip()
    root_cause = state.get("root_cause")
    if isinstance(root_cause, str) and root_cause.strip():
        return root_cause.strip()
    return "Root cause was not captured in structured state. Review the final report before opening a PR."


def _fix_strategy_summary(state: dict[str, Any]) -> str | None:
    strategy = _dict(state.get("fix_strategy"))
    summary = strategy.get("summary")
    return summary if isinstance(summary, str) and summary.strip() else None


def _patch_files(patch_diff: str) -> list[str]:
    files: set[str] = set()
    for match in re.finditer(r"^diff --git a/(.*?) b/(.*?)$", patch_diff, flags=re.MULTILINE):
        files.add(match.group(1))
    return sorted(files)


def _patch_summary(files_changed: list[str], state: dict[str, Any]) -> str:
    if not files_changed:
        return "No patch preview was generated. Use this draft as investigation context only."
    approval_status = _string(state.get("approval_status")) or "unknown"
    return (
        "Patch preview only. It has not been applied by Agentrail. "
        f"Approval status: {approval_status}. Files in preview: {', '.join(files_changed)}."
    )


def _test_evidence(state: dict[str, Any]) -> list[str]:
    test_result = _dict(state.get("test_result"))
    if not test_result:
        return ["No test result was recorded. Manual verification required."]
    status = _string(test_result.get("status")) or "unknown"
    command = _string(test_result.get("command"))
    provider = _string(test_result.get("provider")) or "local"
    exit_code = test_result.get("exit_code")
    provider_label = "E2B sandbox" if provider == "e2b" else "local safe runner"
    if status == "skipped":
        return ["Tests skipped. Manual verification required."]
    detail = f"{provider_label}:"
    if command:
        detail += f" `{command}`"
    detail += f" {status}"
    if isinstance(exit_code, int):
        detail += f" with exit code {exit_code}"
    return [detail + "."]


def _verification_status(state: dict[str, Any]) -> str:
    verification = _dict(state.get("verification_result"))
    return _string(verification.get("status")) or "unknown"


def _risk_level(state: dict[str, Any]) -> str:
    risk = _dict(state.get("risk_score"))
    return _string(risk.get("level")) or "unknown"


def _risk_summary(state: dict[str, Any]) -> str:
    risk = _dict(state.get("risk_score"))
    return _sanitize(_string(risk.get("summary")) or "Risk summary was not recorded.")


def _summary(
    state: dict[str, Any],
    files_changed: list[str],
    verification_status: str,
    risk_level: str,
) -> str:
    file_text = f"{len(files_changed)} file(s)" if files_changed else "no files"
    approval_status = _string(state.get("approval_status")) or "unknown"
    if approval_status == "rejected":
        return (
            f"Draft generated from a rejected Agentrail run. Patch preview covers {file_text}; "
            "do not merge unless a human prepares and approves a revised patch."
        )
    return (
        f"Draft generated from an Agentrail patch preview covering {file_text}. "
        f"Verification status: {verification_status}. Risk level: {risk_level}. "
        "Agentrail did not apply these changes."
    )


def _rollback_plan(files_changed: list[str]) -> str:
    if not files_changed:
        return "No code change is represented in this draft. No rollback action exists yet."
    return (
        "If this patch is manually applied and causes regressions, revert the commit containing these "
        "changes and rerun the verification command before retrying."
    )


def _manual_review_checklist(risk_level: str) -> list[str]:
    checklist = [
        "Review patch diff",
        "Confirm acceptance criteria",
        "Confirm tests pass in CI",
        "Review sensitive files",
        "Confirm no secrets or config changes were introduced",
    ]
    if risk_level == "high":
        checklist.append("Resolve high-risk findings before merge")
    return checklist


def _body_markdown(
    *,
    summary: str,
    linked_issue: str | None,
    root_cause: str,
    fix_strategy_summary: str | None,
    files_changed: list[str],
    patch_summary: str,
    test_evidence: list[str],
    verification_status: str,
    risk_level: str,
    risk_summary: str,
    rollback_plan: str,
    checklist: list[str],
) -> str:
    issue_text = f"Relates to: {linked_issue}" if linked_issue else "No linked GitHub issue."
    files_text = "\n".join(f"- `{file}`" for file in files_changed) or "- No files in patch preview."
    tests_text = "\n".join(f"- {item}" for item in test_evidence)
    checklist_text = "\n".join(f"- [ ] {item}" for item in checklist)
    warnings: list[str] = []
    if verification_status != "verified":
        warnings.append("Verification is not verified; manual verification required before merge.")
    if risk_level == "high":
        warnings.append("Risk is high; do not merge until reviewed and mitigated.")
    warning_text = "\n\n".join(warnings)
    sections = [
        "## Summary",
        summary,
        "## Linked Issue",
        issue_text,
        "## Root Cause",
        root_cause,
        "## Fix Strategy",
        fix_strategy_summary or "No structured fix strategy was recorded.",
        "## Patch Preview",
        f"{patch_summary}\n\nFiles changed:\n{files_text}",
        "## Verification",
        f"Status: {verification_status}\n\nTests:\n{tests_text}",
        "## Risk",
        f"Level: {risk_level}\n\nReason: {risk_summary}",
        "## Rollback Plan",
        rollback_plan,
        "## Manual Review Checklist",
        checklist_text,
    ]
    if warning_text:
        sections.extend(["## Merge Warning", warning_text])
    return "\n\n".join(_sanitize(section) for section in sections)


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""


def _sanitize(value: str | None) -> str:
    if not value:
        return ""
    sanitized = value
    sanitized = re.sub(r"\b[A-Z0-9_]*API_KEY\s*=\s*\S+", "[secret]", sanitized)
    sanitized = re.sub(r"\b(?:ghp_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+)\b", "[token]", sanitized)
    sanitized = re.sub(r"\bsk-[A-Za-z0-9_-]+\b", "[secret]", sanitized)
    return sanitized
