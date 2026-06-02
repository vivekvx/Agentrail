from __future__ import annotations

from app.agents.state import AgentRunState


def verifier_node(state: AgentRunState) -> dict[str, object]:
    return {"verification_result": _verification_result(state)}


def _verification_result(state: AgentRunState) -> dict[str, object]:
    checks = [
        _approval_check(state),
        _patch_check(state),
        _evidence_check(state),
        _test_check(state),
    ]

    if state.get("approval_status") == "rejected":
        return {
            "status": "rejected",
            "summary": "The patch was not approved, so no verification was performed.",
            "checks": checks,
            "confidence": "low",
        }

    if not _has_patch(state):
        return {
            "status": "needs_manual_review",
            "summary": "No patch diff was generated, so the task requires manual review.",
            "checks": checks,
            "confidence": "low",
        }

    if not _has_evidence(state):
        return {
            "status": "needs_manual_review",
            "summary": "A patch exists, but no evidence was collected to support verification.",
            "checks": checks,
            "confidence": "low",
        }

    test_result = state.get("test_result")
    if not isinstance(test_result, dict) or test_result.get("status") == "skipped":
        return {
            "status": "needs_manual_review",
            "summary": "No test command was provided, so manual review is still required.",
            "checks": checks,
            "confidence": "low",
        }

    if _tests_failed(test_result):
        return {
            "status": "not_verified",
            "summary": "Tests did not pass, so the patch is not verified.",
            "checks": checks,
            "confidence": "low",
        }

    if _tests_passed(test_result) and state.get("approval_status") == "approved":
        return {
            "status": "verified",
            "summary": (
                "Tests passed for an approved patch with supporting evidence. "
                "Manual review is still recommended before applying changes."
            ),
            "checks": checks,
            "confidence": "medium",
        }

    return {
        "status": "needs_manual_review",
        "summary": "Verification is inconclusive and requires manual review.",
        "checks": checks,
        "confidence": "low",
    }


def _approval_check(state: AgentRunState) -> dict[str, str]:
    approval_status = state.get("approval_status")
    if approval_status == "approved":
        return {
            "name": "Approval",
            "status": "pass",
            "details": "Patch was approved by the user.",
        }
    if approval_status == "rejected":
        return {
            "name": "Approval",
            "status": "fail",
            "details": "Patch was rejected by the user.",
        }
    return {
        "name": "Approval",
        "status": "warning",
        "details": "Approval status is missing or unknown.",
    }


def _patch_check(state: AgentRunState) -> dict[str, str]:
    if _has_patch(state):
        return {
            "name": "Patch Diff",
            "status": "pass",
            "details": "A patch diff was generated for review.",
        }
    return {
        "name": "Patch Diff",
        "status": "warning",
        "details": "No patch diff was generated.",
    }


def _evidence_check(state: AgentRunState) -> dict[str, str]:
    evidence = state.get("evidence", [])
    if isinstance(evidence, list) and evidence:
        return {
            "name": "Evidence",
            "status": "pass",
            "details": f"{len(evidence)} evidence item(s) support the investigation.",
        }
    return {
        "name": "Evidence",
        "status": "warning",
        "details": "No evidence was collected, so verification cannot be conclusive.",
    }


def _test_check(state: AgentRunState) -> dict[str, str]:
    test_result = state.get("test_result")
    if not isinstance(test_result, dict):
        return {
            "name": "Tests",
            "status": "skipped",
            "details": "No test result was available.",
        }

    status = test_result.get("status")
    exit_code = test_result.get("exit_code")
    if status == "skipped":
        return {
            "name": "Tests",
            "status": "skipped",
            "details": "No test command was provided.",
        }
    if _tests_passed(test_result):
        return {
            "name": "Tests",
            "status": "pass",
            "details": "Tests passed, but this alone does not prove the patch is correct.",
        }
    if status == "timeout":
        return {
            "name": "Tests",
            "status": "fail",
            "details": "Test command timed out.",
        }
    return {
        "name": "Tests",
        "status": "fail",
        "details": f"Tests failed with exit code {exit_code}.",
    }


def _has_patch(state: AgentRunState) -> bool:
    patch_diff = state.get("patch_diff")
    return isinstance(patch_diff, str) and bool(patch_diff.strip())


def _has_evidence(state: AgentRunState) -> bool:
    evidence = state.get("evidence", [])
    return isinstance(evidence, list) and bool(evidence)


def _tests_passed(test_result: dict[str, object]) -> bool:
    return test_result.get("status") == "passed" or test_result.get("exit_code") == 0


def _tests_failed(test_result: dict[str, object]) -> bool:
    return test_result.get("status") in {"failed", "timeout"} or (
        isinstance(test_result.get("exit_code"), int) and test_result.get("exit_code") != 0
    )
