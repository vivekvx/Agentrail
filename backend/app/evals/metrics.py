from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel

from app.evals.scenarios import EvalScenario


class EvalResult(BaseModel):
    scenario_id: str
    passed: bool
    score: int
    checks: list[dict[str, object]]
    summary: str


CHECK_WEIGHTS = {
    "repo_scanned": 8,
    "relevant_files_found": 10,
    "evidence_found": 12,
    "root_cause_grounded": 10,
    "fix_strategy_grounded": 8,
    "patch_file_valid": 12,
    "approval_required": 8,
    "test_result_valid": 8,
    "verification_status_valid": 8,
    "risk_level_valid": 8,
    "report_sections_present": 8,
}


def score_eval_run(scenario: EvalScenario, run_state: dict[str, Any]) -> EvalResult:
    checks = [
        _repo_scanned(run_state),
        _relevant_files_found(scenario, run_state),
        _evidence_found(scenario, run_state),
        _root_cause_grounded(scenario, run_state),
        _fix_strategy_grounded(run_state),
        _patch_file_valid(scenario, run_state),
        _approval_required(scenario, run_state),
        _test_result_valid(scenario, run_state),
        _verification_status_valid(scenario, run_state),
        _risk_level_valid(scenario, run_state),
        _report_sections_present(scenario, run_state),
    ]
    score = sum(int(check["score"]) for check in checks)
    passed = all(bool(check["passed"]) for check in checks)
    failed_names = [str(check["name"]) for check in checks if not check["passed"]]
    summary = (
        f"{scenario.name}: {score}/100"
        if passed
        else f"{scenario.name}: {score}/100; failed {', '.join(failed_names)}"
    )
    return EvalResult(
        scenario_id=scenario.id,
        passed=passed,
        score=score,
        checks=checks,
        summary=summary,
    )


def _repo_scanned(run_state: dict[str, Any]) -> dict[str, object]:
    repo_scan = run_state.get("repo_scan")
    passed = isinstance(repo_scan, dict) and bool(repo_scan)
    return _check("repo_scanned", passed, "Repository scan output is present.")


def _relevant_files_found(
    scenario: EvalScenario,
    run_state: dict[str, Any],
) -> dict[str, object]:
    found_files = _search_files(run_state) | _evidence_files(run_state)
    missing = [file for file in scenario.expected_files if file not in found_files]
    return _check(
        "relevant_files_found",
        not missing,
        f"Missing expected files: {', '.join(missing)}" if missing else "Expected files found.",
    )


def _evidence_found(scenario: EvalScenario, run_state: dict[str, Any]) -> dict[str, object]:
    evidence = _evidence_items(run_state)
    evidence_text = _joined_text(evidence).lower()
    has_line_numbers = all(
        isinstance(item.get("start_line"), int)
        and isinstance(item.get("end_line"), int)
        and isinstance(item.get("snippet"), str)
        for item in evidence
    )
    missing_keywords = [
        keyword
        for keyword in scenario.expected_evidence_keywords
        if keyword.lower() not in evidence_text
    ]
    passed = bool(evidence) and has_line_numbers and not missing_keywords
    details = (
        f"Missing evidence keywords: {', '.join(missing_keywords)}"
        if missing_keywords
        else "Evidence includes line-numbered snippets and expected keywords."
    )
    return _check("evidence_found", passed, details)


def _root_cause_grounded(
    scenario: EvalScenario,
    run_state: dict[str, Any],
) -> dict[str, object]:
    root_cause = _string(run_state.get("root_cause"))
    text = root_cause.lower()
    missing_keywords = [
        keyword
        for keyword in scenario.expected_root_cause_keywords
        if keyword.lower() not in text
    ]
    evidence_files = _evidence_files(run_state)
    references_evidence = not evidence_files or any(file.lower() in text for file in evidence_files)
    passed = bool(root_cause) and not missing_keywords and references_evidence
    details = (
        f"Missing root cause keywords: {', '.join(missing_keywords)}"
        if missing_keywords
        else "Root cause references expected evidence."
    )
    if not references_evidence:
        details = "Root cause does not reference an evidence-backed file."
    return _check("root_cause_grounded", passed, details)


def _fix_strategy_grounded(run_state: dict[str, Any]) -> dict[str, object]:
    fix_strategy = run_state.get("fix_strategy")
    if not isinstance(fix_strategy, dict):
        return _check("fix_strategy_grounded", True, "Fix strategy not present; optional path.")

    target_files = [
        item
        for item in fix_strategy.get("target_files", [])
        if isinstance(item, str) and item
    ]
    if not target_files:
        return _check("fix_strategy_grounded", True, "Fix strategy has no target files.")

    evidence_files = _evidence_files(run_state)
    ungrounded = [file for file in target_files if file not in evidence_files]
    return _check(
        "fix_strategy_grounded",
        not ungrounded,
        f"Ungrounded fix strategy files: {', '.join(ungrounded)}"
        if ungrounded
        else "Fix strategy target files are evidence-backed.",
    )


def _patch_file_valid(
    scenario: EvalScenario,
    run_state: dict[str, Any],
) -> dict[str, object]:
    patch_diff = _string(run_state.get("patch_diff"))
    patch_files = _patch_files(patch_diff)
    if not scenario.should_generate_patch:
        return _check(
            "patch_file_valid",
            not patch_files,
            "No patch expected and no patch files found."
            if not patch_files
            else f"Unexpected patch files: {', '.join(sorted(patch_files))}",
        )

    evidence_files = _evidence_files(run_state)
    missing_expected = [
        file for file in scenario.expected_patch_files if file not in patch_files
    ]
    ungrounded = [file for file in patch_files if file not in evidence_files]
    passed = bool(patch_files) and not missing_expected and not ungrounded
    details = "Patch files match expected evidence-backed files."
    if missing_expected:
        details = f"Missing expected patch files: {', '.join(missing_expected)}"
    elif ungrounded:
        details = f"Patch files not backed by evidence: {', '.join(ungrounded)}"
    return _check("patch_file_valid", passed, details)


def _approval_required(
    scenario: EvalScenario,
    run_state: dict[str, Any],
) -> dict[str, object]:
    approval_seen = bool(run_state.get("__eval_approval_required")) or run_state.get(
        "approval_status",
    ) in {"approved", "rejected"}
    passed = approval_seen if scenario.should_require_approval else not approval_seen
    return _check(
        "approval_required",
        passed,
        "Approval interrupt observed."
        if approval_seen
        else "Approval interrupt was not observed.",
    )


def _test_result_valid(
    scenario: EvalScenario,
    run_state: dict[str, Any],
) -> dict[str, object]:
    test_result = run_state.get("test_result")
    if not isinstance(test_result, dict):
        return _check("test_result_valid", scenario.test_command is None, "No test result present.")

    status = test_result.get("status")
    command = test_result.get("command")
    if scenario.test_command is None:
        passed = status == "skipped"
    elif _unsafe_command(scenario.test_command):
        passed = status == "blocked"
    else:
        passed = status in {"passed", "failed", "timeout", "error"}
    return _check(
        "test_result_valid",
        passed,
        f"Test result status={status}, command={command}.",
    )


def _verification_status_valid(
    scenario: EvalScenario,
    run_state: dict[str, Any],
) -> dict[str, object]:
    if scenario.expected_verification_status is None:
        return _check("verification_status_valid", True, "No verification status expected.")
    verification = run_state.get("verification_result")
    status = verification.get("status") if isinstance(verification, dict) else None
    return _check(
        "verification_status_valid",
        status == scenario.expected_verification_status,
        f"Expected {scenario.expected_verification_status}, got {status}.",
    )


def _risk_level_valid(scenario: EvalScenario, run_state: dict[str, Any]) -> dict[str, object]:
    if scenario.expected_risk_level is None:
        return _check("risk_level_valid", True, "No risk level expected.")
    risk_score = run_state.get("risk_score")
    level = risk_score.get("level") if isinstance(risk_score, dict) else None
    expected = scenario.expected_risk_level
    passed = level == expected or (expected == "medium" and level in {"medium", "high"})
    return _check("risk_level_valid", passed, f"Expected {expected}, got {level}.")


def _report_sections_present(
    scenario: EvalScenario,
    run_state: dict[str, Any],
) -> dict[str, object]:
    report = _string(run_state.get("final_report"))
    required = [
        "## Task",
        "## Evidence",
        "## Root Cause",
        "## Approval",
        "## Verification",
        "## Risk Score",
        "## Next Step",
    ]
    if scenario.should_generate_patch:
        required.append("## Patch Diff")
    if scenario.test_command is not None:
        required.append("## Test Results")
    missing = [section for section in required if section not in report]
    return _check(
        "report_sections_present",
        not missing,
        f"Missing report sections: {', '.join(missing)}" if missing else "Required sections present.",
    )


def _check(name: str, passed: bool, details: str) -> dict[str, object]:
    weight = CHECK_WEIGHTS[name]
    return {
        "name": name,
        "passed": passed,
        "score": weight if passed else 0,
        "max_score": weight,
        "details": details,
    }


def _search_files(run_state: dict[str, Any]) -> set[str]:
    results = run_state.get("search_results", [])
    if not isinstance(results, list):
        return set()
    return {
        item["file_path"]
        for item in results
        if isinstance(item, dict) and isinstance(item.get("file_path"), str)
    }


def _evidence_items(run_state: dict[str, Any]) -> list[dict[str, Any]]:
    evidence = run_state.get("evidence", [])
    if not isinstance(evidence, list):
        return []
    return [item for item in evidence if isinstance(item, dict)]


def _evidence_files(run_state: dict[str, Any]) -> set[str]:
    return {
        item["file_path"]
        for item in _evidence_items(run_state)
        if isinstance(item.get("file_path"), str)
    }


def _joined_text(items: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for item in items:
        for value in item.values():
            if isinstance(value, str):
                parts.append(value)
    return " ".join(parts)


def _patch_files(patch_diff: str) -> set[str]:
    files: set[str] = set()
    for match in re.finditer(r"^diff --git a/(.*?) b/(.*?)$", patch_diff, flags=re.MULTILINE):
        files.add(match.group(1))
        files.add(match.group(2))
    return files


def _unsafe_command(command: str) -> bool:
    lowered = command.lower()
    return any(pattern in lowered for pattern in ("rm -rf", "sudo", "curl | bash", "wget | bash"))


def _string(value: object) -> str:
    return value if isinstance(value, str) else ""
