from __future__ import annotations

from app.agents.nodes.risk_scorer import risk_scorer_node


def _base_state() -> dict[str, object]:
    return {
        "approval_status": "approved",
        "patch_diff": (
            "diff --git a/src/app.py b/src/app.py\n"
            "--- a/src/app.py\n"
            "+++ b/src/app.py\n"
            "@@\n"
            "-old_value = 1\n"
            "+new_value = 2\n"
        ),
        "verification_result": {
            "status": "verified",
            "summary": "Verified with passing tests.",
            "checks": [],
            "confidence": "medium",
        },
        "test_result": {
            "command": "python -m pytest",
            "status": "passed",
            "stdout": "1 passed",
            "stderr": "",
            "exit_code": 0,
            "duration_ms": 10,
        },
        "evidence": [
            {
                "file_path": "src/app.py",
                "start_line": 1,
                "end_line": 1,
                "snippet": "1: old_value = 1",
                "reason": "Simple evidence.",
            },
        ],
        "root_cause": "A simple non-sensitive issue.",
    }


def test_risk_scorer_rejected_approval_is_high_risk() -> None:
    state = _base_state()
    state["approval_status"] = "rejected"

    result = risk_scorer_node(state)["risk_score"]

    assert result["level"] == "high"
    assert result["score"] >= 70
    assert "rejected" in result["summary"].lower()


def test_risk_scorer_not_verified_is_high_risk() -> None:
    state = _base_state()
    state["verification_result"] = {
        "status": "not_verified",
        "summary": "Tests failed.",
        "checks": [],
        "confidence": "low",
    }
    state["test_result"]["status"] = "failed"
    state["test_result"]["exit_code"] = 1

    result = risk_scorer_node(state)["risk_score"]

    assert result["level"] == "high"
    assert result["score"] >= 70


def test_risk_scorer_skipped_tests_is_medium_risk() -> None:
    state = _base_state()
    state["verification_result"] = {
        "status": "needs_manual_review",
        "summary": "Tests were skipped.",
        "checks": [],
        "confidence": "low",
    }
    state["test_result"] = {
        "command": None,
        "status": "skipped",
        "stdout": "",
        "stderr": "No test command provided.",
        "exit_code": None,
        "duration_ms": 0,
    }

    result = risk_scorer_node(state)["risk_score"]

    assert result["level"] == "medium"
    assert 40 <= result["score"] <= 69


def test_risk_scorer_verified_small_non_sensitive_patch_is_low_risk() -> None:
    result = risk_scorer_node(_base_state())["risk_score"]

    assert result["level"] == "low"
    assert 20 <= result["score"] < 40


def test_risk_scorer_verified_auth_patch_is_at_least_medium_risk() -> None:
    state = _base_state()
    state["patch_diff"] = (
        "diff --git a/src/AuthContext.tsx b/src/AuthContext.tsx\n"
        "--- a/src/AuthContext.tsx\n"
        "+++ b/src/AuthContext.tsx\n"
        "@@\n"
        "-const token = null;\n"
        "+const token = localStorage.getItem('token');\n"
    )
    state["evidence"] = [
        {
            "file_path": "src/AuthContext.tsx",
            "start_line": 4,
            "end_line": 6,
            "snippet": "4: const [token, setToken] = useState<string | null>(null);",
            "reason": "Auth token persistence evidence.",
        },
    ]
    state["root_cause"] = "Auth token state is not restored."

    result = risk_scorer_node(state)["risk_score"]

    assert result["level"] in {"medium", "high"}
    assert result["score"] >= 40


def test_risk_scorer_large_patch_increases_risk() -> None:
    state = _base_state()
    changed_lines = "\n".join(
        [f"+line_{index}" for index in range(30)] + [f"-line_{index}" for index in range(30)]
    )
    state["patch_diff"] = (
        "diff --git a/src/app.py b/src/app.py\n"
        "--- a/src/app.py\n"
        "+++ b/src/app.py\n"
        "@@\n"
        f"{changed_lines}\n"
    )

    result = risk_scorer_node(state)["risk_score"]

    assert result["level"] in {"medium", "high"}
    assert result["score"] >= 40
