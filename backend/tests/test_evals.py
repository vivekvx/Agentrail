from __future__ import annotations

import os
from pathlib import Path

from app.evals.metrics import score_eval_run
from app.evals.report import render_eval_report
from app.evals.runner import run_eval_scenario
from app.evals.scenarios import EvalScenario, load_default_scenarios


def test_eval_scenario_model_validation() -> None:
    scenario = EvalScenario(
        id="sample",
        name="Sample",
        description="Small validation scenario.",
        repo_path="examples/eval_scenarios/auth-refresh-bug",
        user_task="Fix auth token refresh",
        expected_behavior="Token should persist after refresh.",
        test_command="python -m pytest",
        expected_files=["src/AuthContext.tsx"],
        expected_evidence_keywords=["localStorage", "token"],
        expected_root_cause_keywords=["AuthContext", "localStorage"],
        expected_patch_files=["src/AuthContext.tsx"],
        expected_verification_status="verified",
        expected_risk_level="medium",
        should_generate_patch=True,
        should_require_approval=True,
    )

    assert scenario.id == "sample"
    assert scenario.expected_files == ["src/AuthContext.tsx"]


def test_eval_runner_executes_fixture_scenario() -> None:
    scenario = load_default_scenarios()[0]

    result = run_eval_scenario(scenario)

    assert result.scenario_id == scenario.id
    assert result.score >= 80
    assert result.passed is True
    assert any(check["name"] == "evidence_found" for check in result.checks)


def test_metrics_score_successful_run_correctly() -> None:
    scenario = _scenario()
    run_state = _successful_state()

    result = score_eval_run(scenario, run_state)

    assert result.passed is True
    assert result.score == 100


def test_metrics_detect_missing_evidence() -> None:
    scenario = _scenario()
    run_state = _successful_state()
    run_state["evidence"] = []

    result = score_eval_run(scenario, run_state)

    failed = [check["name"] for check in result.checks if not check["passed"]]
    assert "evidence_found" in failed
    assert result.passed is False


def test_metrics_detect_patch_file_not_backed_by_evidence() -> None:
    scenario = _scenario()
    run_state = _successful_state()
    run_state["patch_diff"] = "diff --git a/src/Other.tsx b/src/Other.tsx\n"

    result = score_eval_run(scenario, run_state)

    failed = [check["name"] for check in result.checks if not check["passed"]]
    assert "patch_file_valid" in failed
    assert result.passed is False


def test_metrics_detect_skipped_tests_correctly() -> None:
    scenario = _scenario(test_command=None, expected_verification_status="needs_manual_review")
    run_state = _successful_state()
    run_state["test_result"] = {
        "provider": "local",
        "command": None,
        "status": "skipped",
        "stdout": "",
        "stderr": "No test_command provided.",
        "exit_code": None,
        "duration_ms": 0,
        "sandbox_id": None,
        "error_message": None,
    }
    run_state["verification_result"] = {
        "status": "needs_manual_review",
        "confidence": "low",
        "summary": "No test command was provided.",
        "checks": [],
    }
    run_state["risk_score"] = {"level": "medium", "score": 60, "factors": []}

    result = score_eval_run(scenario, run_state)

    checks = {check["name"]: check for check in result.checks}
    assert checks["test_result_valid"]["passed"] is True
    assert checks["verification_status_valid"]["passed"] is True


def test_eval_report_generation_does_not_require_external_services() -> None:
    scenario = _scenario()
    result = score_eval_run(scenario, _successful_state())

    report = render_eval_report([scenario], [result])

    assert "# Agentrail Evaluation Report" in report
    assert "Sample scenario" in report
    assert "No LLM-as-judge" in report


def test_evals_do_not_require_external_credentials(monkeypatch) -> None:
    for key in ("OPENAI_API_KEY", "GITHUB_TOKEN", "E2B_API_KEY"):
        monkeypatch.delenv(key, raising=False)

    scenario = load_default_scenarios()[0]
    result = run_eval_scenario(scenario)

    assert os.getenv("OPENAI_API_KEY") is None
    assert os.getenv("GITHUB_TOKEN") is None
    assert os.getenv("E2B_API_KEY") is None
    assert result.score >= 80


def _scenario(
    *,
    test_command: str | None = "python -m pytest",
    expected_verification_status: str | None = "verified",
) -> EvalScenario:
    return EvalScenario(
        id="sample",
        name="Sample scenario",
        description="Synthetic successful state.",
        repo_path="examples/eval_scenarios/auth-refresh-bug",
        user_task="Fix AuthContext localStorage token persistence",
        expected_behavior="Token should persist after refresh.",
        test_command=test_command,
        expected_files=["src/AuthContext.tsx"],
        expected_evidence_keywords=["localStorage", "token"],
        expected_root_cause_keywords=["AuthContext", "localStorage"],
        expected_patch_files=["src/AuthContext.tsx"],
        expected_verification_status=expected_verification_status,
        expected_risk_level="medium",
        should_generate_patch=True,
        should_require_approval=True,
    )


def _successful_state() -> dict[str, object]:
    return {
        "repo_scan": {"detected_stack": ["React"]},
        "search_results": [{"file_path": "src/AuthContext.tsx"}],
        "evidence": [
            {
                "file_path": "src/AuthContext.tsx",
                "start_line": 1,
                "end_line": 4,
                "snippet": "1: localStorage.setItem('token', token ?? '')",
                "reason": "Token persistence uses localStorage.",
            },
        ],
        "root_cause": "src/AuthContext.tsx localStorage token persistence is not restored.",
        "fix_strategy": {"target_files": ["src/AuthContext.tsx"]},
        "patch_diff": "diff --git a/src/AuthContext.tsx b/src/AuthContext.tsx\n",
        "approval_status": "approved",
        "__eval_approval_required": True,
        "test_result": {
            "provider": "local",
            "command": "python -m pytest",
            "status": "passed",
            "stdout": "1 passed",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 10,
            "sandbox_id": None,
            "error_message": None,
        },
        "verification_result": {
            "status": "verified",
            "confidence": "medium",
            "summary": "Tests passed.",
            "checks": [],
        },
        "risk_score": {"level": "medium", "score": 45, "factors": []},
        "final_report": "\n\n".join(
            [
                "# Agentrail Report",
                "## Task",
                "## Evidence",
                "## Root Cause",
                "## Patch Diff",
                "## Approval",
                "## Test Results",
                "## Verification",
                "## Risk Score",
                "## Next Step",
            ],
        ),
    }
