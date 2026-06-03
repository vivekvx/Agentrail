from __future__ import annotations

import json

from fastapi.testclient import TestClient

from app.db.models import AgentRun
from app.db.session import SessionLocal
from app.services.pr_draft import generate_pr_draft


def test_pr_draft_generation_with_completed_verified_run() -> None:
    draft = generate_pr_draft(_run_state())

    assert draft.title == "Fix AuthContext localStorage token persistence"
    assert "patch preview" in draft.summary.lower()
    assert draft.files_changed == ["src/AuthContext.tsx"]
    assert draft.verification_status == "verified"
    assert draft.risk_level == "medium"
    assert "## Summary" in draft.body_markdown
    assert "Status: verified" in draft.body_markdown


def test_pr_draft_generation_with_rejected_run() -> None:
    state = _run_state(approval_status="rejected")

    draft = generate_pr_draft(state)

    assert "rejected" in draft.summary.lower()
    assert "not merge" in draft.body_markdown.lower()


def test_pr_draft_generation_with_skipped_tests() -> None:
    state = _run_state(
        test_result={
            "provider": "local",
            "command": None,
            "status": "skipped",
            "stdout": "",
            "stderr": "No test_command provided.",
            "exit_code": None,
            "duration_ms": 0,
        },
        verification_result={"status": "needs_manual_review", "summary": "Tests skipped."},
    )

    draft = generate_pr_draft(state)

    assert "Tests skipped" in draft.body_markdown
    assert "manual verification required" in draft.body_markdown.lower()


def test_pr_draft_generation_with_high_risk_warns_against_merge() -> None:
    state = _run_state(risk_score={"level": "high", "score": 90, "summary": "High risk."})

    draft = generate_pr_draft(state)

    assert draft.risk_level == "high"
    assert "do not merge" in draft.body_markdown.lower()


def test_pr_draft_includes_issue_link_when_issue_context_exists() -> None:
    draft = generate_pr_draft(_run_state())

    assert draft.linked_issue == "https://github.com/openai/codex/issues/123"
    assert "Relates to: https://github.com/openai/codex/issues/123" in draft.body_markdown


def test_pr_draft_does_not_say_closes_automatically() -> None:
    draft = generate_pr_draft(_run_state())

    assert "Closes" not in draft.body_markdown


def test_pr_draft_does_not_claim_patch_was_applied() -> None:
    draft = generate_pr_draft(_run_state())

    assert "applied" not in draft.summary.lower()
    assert "Patch preview" in draft.body_markdown


def test_pr_draft_includes_manual_review_checklist() -> None:
    draft = generate_pr_draft(_run_state())

    assert "- [ ] Review patch diff" in draft.body_markdown
    assert len(draft.manual_review_checklist) >= 5


def test_no_secrets_appear_in_pr_draft() -> None:
    state = _run_state(root_cause="Token OPENAI_API_KEY=super-secret was logged.")

    draft = generate_pr_draft(state)

    assert "super-secret" not in draft.body_markdown
    assert "OPENAI_API_KEY" not in draft.body_markdown


def test_api_endpoint_returns_pr_draft(client: TestClient) -> None:
    run_id = _insert_run()

    response = client.get(f"/api/runs/{run_id}/pr-draft")

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Fix AuthContext localStorage token persistence"
    assert body["verification_status"] == "verified"
    assert "body_markdown" in body


def test_pr_draft_generated_event_is_logged(client: TestClient) -> None:
    run_id = _insert_run()

    response = client.get(f"/api/runs/{run_id}/pr-draft")
    assert response.status_code == 200

    events = client.get(f"/api/runs/{run_id}/events").json()
    event = next(item for item in events if item["event_type"] == "pr_draft_generated")
    assert event["payload"]["title"] == "Fix AuthContext localStorage token persistence"
    assert event["payload"]["risk_level"] == "medium"
    assert event["payload"]["verification_status"] == "verified"
    assert event["payload"]["has_issue"] is True
    assert event["payload"]["files_changed_count"] == 1
    assert "body_markdown" not in event["payload"]


def _insert_run() -> int:
    with SessionLocal() as db:
        run = AgentRun(
            repo_path="/tmp/repo",
            repo_url="https://github.com/openai/codex",
            issue_url="https://github.com/openai/codex/issues/123",
            issue_context=json.dumps(_issue_context()),
            user_task="Fix AuthContext localStorage token persistence",
            expected_behavior="Token persists after refresh.",
            test_command="python -m pytest",
            status="completed",
            approval_status="approved",
            approval_payload=json.dumps({"root_cause": _root_cause()}),
            patch_diff=_patch_diff(),
            test_result=json.dumps(_test_result()),
            verification_result=json.dumps({"status": "verified", "summary": "Tests passed."}),
            risk_score=json.dumps({"level": "medium", "score": 45, "summary": "Medium risk."}),
            final_report="# Agentrail Report",
            thread_id="test-pr-draft",
        )
        db.add(run)
        db.commit()
        db.refresh(run)
        return run.id


def _run_state(
    *,
    approval_status: str = "approved",
    test_result: dict[str, object] | None = None,
    verification_result: dict[str, object] | None = None,
    risk_score: dict[str, object] | None = None,
    root_cause: str | None = None,
) -> dict[str, object]:
    return {
        "user_task": "Fix AuthContext localStorage token persistence",
        "expected_behavior": "Token persists after refresh.",
        "issue_context": _issue_context(),
        "approval_status": approval_status,
        "root_cause": root_cause or _root_cause(),
        "fix_strategy": {"summary": "Restore token state from localStorage before first render."},
        "patch_diff": _patch_diff(),
        "test_result": test_result or _test_result(),
        "verification_result": verification_result
        or {"status": "verified", "summary": "Tests passed."},
        "risk_score": risk_score or {"level": "medium", "score": 45, "summary": "Medium risk."},
        "final_report": "# Agentrail Report",
    }


def _issue_context() -> dict[str, object]:
    return {
        "issue_url": "https://github.com/openai/codex/issues/123",
        "title": "Auth refresh loses token",
        "labels": ["bug"],
        "state": "open",
    }


def _root_cause() -> str:
    return "AuthContext does not restore token from localStorage on refresh."


def _patch_diff() -> str:
    return "\n".join(
        [
            "diff --git a/src/AuthContext.tsx b/src/AuthContext.tsx",
            "--- a/src/AuthContext.tsx",
            "+++ b/src/AuthContext.tsx",
            "@@",
            "-  const [token, setToken] = useState<string | null>(null);",
            "+  const [token, setToken] = useState<string | null>(() => localStorage.getItem(\"token\"));",
        ],
    )


def _test_result() -> dict[str, object]:
    return {
        "provider": "local",
        "command": "python -m pytest",
        "status": "passed",
        "stdout": "1 passed",
        "stderr": "",
        "exit_code": 0,
        "duration_ms": 10,
    }
