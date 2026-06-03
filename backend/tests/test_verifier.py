from __future__ import annotations

from app.agents.nodes.verifier import verifier_node


def _base_state() -> dict[str, object]:
    return {
        "user_task": "Fix auth refresh",
        "approval_status": "approved",
        "patch_diff": "diff --git a/src/AuthContext.tsx b/src/AuthContext.tsx\n",
        "root_cause": "Token state is not restored from localStorage.",
        "evidence": [
            {
                "file_path": "src/AuthContext.tsx",
                "start_line": 4,
                "end_line": 6,
                "snippet": "4: const [token, setToken] = useState<string | null>(null);",
                "reason": "Token persistence evidence.",
            },
        ],
        "test_result": {
            "command": "python -m pytest",
            "status": "passed",
            "stdout": "1 passed",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 10,
        },
    }


def test_verifier_rejected_approval_returns_rejected() -> None:
    state = _base_state()
    state["approval_status"] = "rejected"
    state["rejection_reason"] = "Patch rejected by user."
    state.pop("test_result")

    result = verifier_node(state)["verification_result"]

    assert result["status"] == "rejected"
    assert result["confidence"] == "low"
    assert "not approved" in result["summary"]


def test_verifier_approved_patch_evidence_and_passing_tests_is_verified_medium() -> None:
    result = verifier_node(_base_state())["verification_result"]

    assert result["status"] == "verified"
    assert result["confidence"] == "medium"
    assert any(
        check["name"] == "Tests" and check["status"] == "pass"
        for check in result["checks"]
    )
    assert "Manual review is still recommended" in result["summary"]


def test_verifier_accepts_e2b_shaped_test_result() -> None:
    state = _base_state()
    state["test_result"] = {
        "provider": "e2b",
        "command": "python -m pytest",
        "status": "passed",
        "stdout": "1 passed",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 25,
        "sandbox_id": "sandbox-123",
        "error_message": None,
    }

    result = verifier_node(state)["verification_result"]

    assert result["status"] == "verified"
    assert any(
        check["name"] == "Tests" and check["status"] == "pass"
        for check in result["checks"]
    )


def test_verifier_approved_with_skipped_tests_needs_manual_review() -> None:
    state = _base_state()
    state["test_result"] = {
        "command": None,
        "status": "skipped",
        "stdout": "",
        "stderr": "No test_command provided.",
        "exit_code": None,
        "duration_ms": 0,
    }

    result = verifier_node(state)["verification_result"]

    assert result["status"] == "needs_manual_review"
    assert result["confidence"] == "low"
    assert "No test command was provided" in result["summary"]


def test_verifier_approved_with_failing_tests_is_not_verified() -> None:
    state = _base_state()
    state["test_result"] = {
        "command": "python -m pytest",
        "status": "failed",
        "stdout": "",
        "stderr": "failure",
        "exit_code": 1,
        "duration_ms": 10,
    }

    result = verifier_node(state)["verification_result"]

    assert result["status"] == "not_verified"
    assert result["confidence"] == "low"
    assert any("exit code 1" in check["details"] for check in result["checks"])


def test_verifier_without_patch_diff_needs_manual_review() -> None:
    state = _base_state()
    state.pop("patch_diff")

    result = verifier_node(state)["verification_result"]

    assert result["status"] == "needs_manual_review"
    assert result["confidence"] == "low"
    assert any(
        check["name"] == "Patch Diff" and check["status"] == "warning"
        for check in result["checks"]
    )


def test_verifier_without_evidence_cannot_be_verified() -> None:
    state = _base_state()
    state["evidence"] = []

    result = verifier_node(state)["verification_result"]

    assert result["status"] == "needs_manual_review"
    assert result["confidence"] == "low"
