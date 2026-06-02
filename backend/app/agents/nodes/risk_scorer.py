from __future__ import annotations

from app.agents.state import AgentRunState


AUTH_SECURITY_KEYWORDS = (
    "auth",
    "token",
    "jwt",
    "password",
    "session",
    "permission",
    "role",
    "cors",
    "secret",
)
CONFIG_FILES = (
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "dockerfile",
    "docker-compose.yml",
    ".env",
    "settings.py",
    "config.py",
)


def risk_scorer_node(state: AgentRunState) -> dict[str, object]:
    return {"risk_score": _risk_score(state)}


def _risk_score(state: AgentRunState) -> dict[str, object]:
    verification_result = state.get("verification_result", {})
    verification_status = (
        verification_result.get("status")
        if isinstance(verification_result, dict)
        else None
    )
    approval_status = state.get("approval_status")
    factors: list[dict[str, str]] = []

    if approval_status == "rejected":
        factors.append(
            _factor(
                "Approval Status",
                "high",
                "The patch was rejected by the user and should not be trusted.",
            ),
        )
        return _result(
            score=85,
            factors=factors,
            summary="The patch was rejected and should not be trusted without a new review.",
            recommended_action="Do not apply the patch. Reassess the root cause and prepare a revised proposal.",
        )

    if verification_status == "not_verified":
        factors.append(
            _factor(
                "Verification Status",
                "high",
                "Verification failed, so the patch remains high risk.",
            ),
        )
        score = 80
        score = _apply_risk_modifiers(state, score, factors)
        return _result(
            score=max(score, 70),
            factors=factors,
            summary="Verification did not succeed, so the patch remains high risk.",
            recommended_action="Fix the failing checks before considering the patch for application.",
        )

    if verification_status == "needs_manual_review":
        factors.append(
            _factor(
                "Verification Status",
                "medium",
                "Verification is incomplete and still needs manual review.",
            ),
        )
        score = 50
        score = _apply_risk_modifiers(state, score, factors)
        score = min(max(score, 40), 69)
        return _result(
            score=score,
            factors=factors,
            summary="Manual review is still required before the patch can be trusted.",
            recommended_action="Review the patch and supporting evidence manually, then rerun verification if needed.",
        )

    if verification_status == "verified":
        factors.append(
            _factor(
                "Verification Status",
                "low",
                "Verification checks passed with supporting evidence, but residual risk remains.",
            ),
        )
        score = 25
        score = _apply_risk_modifiers(state, score, factors)
        if _touches_auth_or_security(state):
            score = max(score, 45)
        return _result(
            score=max(score, 20),
            factors=factors,
            summary="The patch is verified, but residual risk depends on patch scope and sensitivity.",
            recommended_action=(
                "Proceed with a normal code review. Pay extra attention to sensitive files and regression coverage."
            ),
        )

    factors.append(
        _factor(
            "Verification Status",
            "medium",
            "Verification state is missing, so the patch cannot be fully assessed.",
        ),
    )
    score = _apply_risk_modifiers(state, 55, factors)
    score = min(max(score, 40), 69)
    return _result(
        score=score,
        factors=factors,
        summary="Risk could not be fully assessed because verification data is incomplete.",
        recommended_action="Review the verification state and rerun the workflow before trusting the patch.",
    )


def _apply_risk_modifiers(
    state: AgentRunState,
    score: int,
    factors: list[dict[str, str]],
) -> int:
    test_result = state.get("test_result")
    if isinstance(test_result, dict) and test_result.get("status") == "skipped":
        score += 10
        factors.append(
            _factor(
                "Test Coverage",
                "medium",
                "Tests were skipped, which increases uncertainty.",
            ),
        )

    patch_size = _patch_size(state)
    if patch_size == "medium":
        score += 10
        factors.append(
            _factor(
                "Patch Size",
                "medium",
                "The patch changes a moderate number of lines.",
            ),
        )
    elif patch_size == "large":
        score += 25
        factors.append(
            _factor(
                "Patch Size",
                "high",
                "The patch changes more than 50 lines and has a broader blast radius.",
            ),
        )

    if _touches_auth_or_security(state):
        score += 15
        factors.append(
            _factor(
                "Sensitive Surface",
                "high",
                "The patch touches auth or security-related code paths.",
            ),
        )

    if _touches_config_or_dependency_files(state):
        score += 15
        factors.append(
            _factor(
                "Config Or Dependency Files",
                "high",
                "The patch or evidence references dependency or configuration files.",
            ),
        )

    return score


def _touches_auth_or_security(state: AgentRunState) -> bool:
    haystack = " ".join(
        part
        for part in (
            _string_value(state.get("patch_diff")),
            _evidence_paths_text(state),
            _string_value(state.get("root_cause")),
        )
        if part
    ).lower()
    return any(keyword in haystack for keyword in AUTH_SECURITY_KEYWORDS)


def _touches_config_or_dependency_files(state: AgentRunState) -> bool:
    haystack = " ".join(
        part
        for part in (
            _string_value(state.get("patch_diff")),
            _evidence_paths_text(state),
        )
        if part
    ).lower()
    return any(file_name in haystack for file_name in CONFIG_FILES)


def _patch_size(state: AgentRunState) -> str:
    patch_diff = state.get("patch_diff")
    if not isinstance(patch_diff, str):
        return "small"

    changed_lines = 0
    for line in patch_diff.splitlines():
        if line.startswith(("+++", "---", "@@", "diff --git")):
            continue
        if line.startswith("+") or line.startswith("-"):
            changed_lines += 1

    if changed_lines > 50:
        return "large"
    if changed_lines > 10:
        return "medium"
    return "small"


def _evidence_paths_text(state: AgentRunState) -> str:
    evidence = state.get("evidence", [])
    if not isinstance(evidence, list):
        return ""
    return " ".join(
        item["file_path"]
        for item in evidence
        if isinstance(item, dict) and isinstance(item.get("file_path"), str)
    )


def _string_value(value: object) -> str:
    return value if isinstance(value, str) else ""


def _factor(name: str, impact: str, details: str) -> dict[str, str]:
    return {
        "name": name,
        "impact": impact,
        "details": details,
    }


def _result(
    *,
    score: int,
    factors: list[dict[str, str]],
    summary: str,
    recommended_action: str,
) -> dict[str, object]:
    bounded_score = max(0, min(score, 100))
    if bounded_score >= 70:
        level = "high"
    elif bounded_score >= 40:
        level = "medium"
    else:
        level = "low"
    return {
        "level": level,
        "score": bounded_score,
        "summary": summary,
        "factors": factors,
        "recommended_action": recommended_action,
    }
