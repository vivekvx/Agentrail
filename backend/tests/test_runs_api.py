from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.api import routes_runs
from app.db.models import AgentRun
from app.db.session import SessionLocal


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_create_run_rejects_invalid_repo_path(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path / "missing"),
            "user_task": "Find FastAPI app setup",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Repository path does not exist."


def test_create_run_returns_initial_fields(client: TestClient, tmp_path: Path) -> None:
    response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix auth refresh bug",
            "expected_behavior": "Token should persist across refresh.",
            "test_command": "python -m pytest",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["repo_path"] == str(tmp_path.resolve())
    assert created["repo_url"] is None
    assert created["user_task"] == "Fix auth refresh bug"
    assert created["expected_behavior"] == "Token should persist across refresh."
    assert created["test_command"] == "python -m pytest"
    assert created["status"] == "created"
    assert created["current_node"] is None
    assert created["approval_payload"] is None
    assert created["approval_status"] is None
    assert created["fix_strategy"] is None
    assert created["patch_diff"] is None
    assert created["test_result"] is None
    assert created["verification_result"] is None
    assert created["risk_score"] is None
    assert created["final_report"] is None
    assert created["error_message"] is None

    events_response = client.get(f"/api/runs/{created['id']}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert [event["event_type"] for event in events] == ["run_created"]
    assert events[0]["payload"]["status"] == "created"


def test_create_run_with_repo_url_only(client: TestClient) -> None:
    response = client.post(
        "/api/runs",
        json={
            "repo_url": "https://github.com/fastapi/fastapi",
            "user_task": "Inspect startup flow",
        },
    )

    assert response.status_code == 201
    created = response.json()
    assert created["repo_path"] is None
    assert created["repo_url"] == "https://github.com/fastapi/fastapi"
    assert created["status"] == "created"


def test_create_run_with_issue_url_sets_repo_url_and_user_task(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class IssueContext:
        owner = "openai"
        repo = "codex"
        issue_number = 123
        issue_url = "https://github.com/openai/codex/issues/123"
        repo_url = "https://github.com/openai/codex"
        title = "Auth refresh loses token"
        body = "Expected: user should stay signed in after refresh."
        labels = ["bug", "auth"]
        state = "open"
        author = "octocat"
        created_at = "2026-01-01T00:00:00Z"
        updated_at = "2026-01-02T00:00:00Z"

        def model_dump(self, mode: str = "json") -> dict[str, object]:
            assert mode == "json"
            return {
                "owner": self.owner,
                "repo": self.repo,
                "issue_number": self.issue_number,
                "issue_url": self.issue_url,
                "repo_url": self.repo_url,
                "title": self.title,
                "body": self.body,
                "labels": self.labels,
                "state": self.state,
                "author": self.author,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }

    def fake_fetch(issue_url: str) -> IssueContext:
        assert issue_url == "https://github.com/openai/codex/issues/123"
        return IssueContext()

    monkeypatch.setattr(routes_runs, "fetch_github_issue_context", fake_fetch)

    response = client.post(
        "/api/runs",
        json={"issue_url": "https://github.com/openai/codex/issues/123"},
    )

    assert response.status_code == 201
    created = response.json()
    assert created["repo_url"] == "https://github.com/openai/codex"
    assert created["issue_context"]["title"] == "Auth refresh loses token"
    assert created["issue_context"]["labels"] == ["bug", "auth"]
    assert "Auth refresh loses token" in created["user_task"]
    assert "Expected: user should stay signed in" in (created["expected_behavior"] or "")


def test_create_run_with_issue_url_logs_import_events(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class IssueContext:
        owner = "openai"
        repo = "codex"
        issue_number = 123
        issue_url = "https://github.com/openai/codex/issues/123"
        repo_url = "https://github.com/openai/codex"
        title = "Auth refresh loses token"
        body = None
        labels = ["bug"]
        state = "open"
        author = "octocat"
        created_at = None
        updated_at = None

        def model_dump(self, mode: str = "json") -> dict[str, object]:
            return {
                "owner": self.owner,
                "repo": self.repo,
                "issue_number": self.issue_number,
                "issue_url": self.issue_url,
                "repo_url": self.repo_url,
                "title": self.title,
                "body": self.body,
                "labels": self.labels,
                "state": self.state,
                "author": self.author,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }

    monkeypatch.setattr(
        routes_runs,
        "fetch_github_issue_context",
        lambda _issue_url: IssueContext(),
    )

    created = client.post(
        "/api/runs",
        json={"issue_url": "https://github.com/openai/codex/issues/123"},
    ).json()

    events = client.get(f"/api/runs/{created['id']}/events").json()
    event_types = [event["event_type"] for event in events]
    assert "issue_import_started" in event_types
    assert "issue_import_completed" in event_types
    completed = next(event for event in events if event["event_type"] == "issue_import_completed")
    assert completed["payload"]["labels"] == ["bug"]
    assert "token" not in str(completed["payload"]).lower()


def test_create_run_rejects_both_repo_path_and_repo_url(
    client: TestClient,
    tmp_path: Path,
) -> None:
    response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "repo_url": "https://github.com/fastapi/fastapi",
            "user_task": "Inspect startup flow",
        },
    )

    assert response.status_code == 422


def test_start_run_failure_sets_failed_status_and_sanitized_error_message(
    client: TestClient,
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(repo),
            "user_task": "Find FastAPI app setup",
        },
    )
    run_id = create_response.json()["id"]
    repo.rmdir()

    start_response = client.post(f"/api/runs/{run_id}/start")

    assert start_response.status_code == 500
    assert start_response.json()["detail"] == "Graph execution failed."

    get_response = client.get(f"/api/runs/{run_id}")
    retrieved = get_response.json()
    assert retrieved["status"] == "failed"
    assert retrieved["final_report"] is None
    assert retrieved["error_message"] == "Repository path does not exist."
    assert str(repo.resolve()) not in retrieved["error_message"]

    with SessionLocal() as db:
        run = db.get(AgentRun, run_id)
        assert run is not None
        assert run.status == "failed"
        assert run.error_message is not None


def test_start_run_persists_pending_approval_patch_diff_and_payload(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    get_response = client.get(f"/api/runs/{run_id}")

    assert start_response.status_code == 200
    started = start_response.json()
    assert started["status"] == "pending_approval"
    assert started["current_node"] == "approval_node"
    assert started["approval_payload"]["question"] == "Approve this patch?"
    assert "AuthContext.tsx" in started["patch_diff"]

    assert get_response.status_code == 200
    run = get_response.json()
    assert run["status"] == "pending_approval"
    assert run["approval_payload"]["question"] == "Approve this patch?"
    assert run["approval_payload"]["root_cause"]
    assert "AuthContext.tsx" in run["patch_diff"]

    events_response = client.get(f"/api/runs/{run_id}/events")
    event_types = [event["event_type"] for event in events_response.json()]
    assert "run_started" in event_types
    assert "pending_approval" in event_types


def test_start_run_with_repo_url_imports_repository_and_logs_events(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    imported_repo = (tmp_path / "data" / "repos" / "fastapi__fastapi").resolve()
    settings = routes_runs.get_settings().model_copy(
        update={"repo_workspace_dir": str((tmp_path / "data" / "repos").resolve())}
    )

    class ImportResult:
        owner = "fastapi"
        repo = "fastapi"
        clone_url = "https://github.com/fastapi/fastapi.git"
        repo_url = "https://github.com/fastapi/fastapi"
        repo_key = "fastapi__fastapi"
        workspace_relative_path = "fastapi__fastapi"
        used_cache = False
        repo_path = imported_repo

    def fake_import(repo_url: str) -> ImportResult:
        assert repo_url == "https://github.com/fastapi/fastapi"
        return ImportResult()

    class FinishedGraph:
        def invoke(self, input_state: dict[str, object], **_kwargs: object) -> dict[str, object]:
            assert input_state["repo_path"] == str(imported_repo)
            return {
                "repo_scan": {"detected_stack": ["FastAPI"]},
                "search_results": [],
                "evidence": [],
                "root_cause": "No root cause identified yet for task 'Inspect startup flow'. No evidence was collected from code search results.",
                "final_report": "# Agentrail Report\n\n## Task\nInspect startup flow",
            }

    monkeypatch.setattr(routes_runs, "import_github_repository", fake_import)
    monkeypatch.setattr(routes_runs, "build_agent_graph", lambda: FinishedGraph())
    monkeypatch.setattr(routes_runs, "get_settings", lambda: settings)

    create_response = client.post(
        "/api/runs",
        json={
            "repo_url": "https://github.com/fastapi/fastapi",
            "user_task": "Inspect startup flow",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    assert start_response.status_code == 200
    started = start_response.json()
    assert started["status"] == "completed"
    assert started["repo_url"] == "https://github.com/fastapi/fastapi"
    assert started["repo_path"] is None

    events_response = client.get(f"/api/runs/{run_id}/events")
    events = events_response.json()
    event_types = [event["event_type"] for event in events]
    assert "repo_import_started" in event_types
    assert "repo_import_completed" in event_types
    import_started = next(event for event in events if event["event_type"] == "repo_import_started")
    import_completed = next(event for event in events if event["event_type"] == "repo_import_completed")
    assert import_started["payload"]["clone_url"] == "https://github.com/fastapi/fastapi.git"
    assert import_completed["payload"]["workspace_relative_path"] == "fastapi__fastapi"


def test_start_run_with_repo_url_import_failure_is_sanitized(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_import(_repo_url: str) -> object:
        raise RuntimeError("Git clone failed: authentication failed. ghp_secret_token")

    monkeypatch.setattr(routes_runs, "import_github_repository", fake_import)

    create_response = client.post(
        "/api/runs",
        json={
            "repo_url": "https://github.com/fastapi/fastapi",
            "user_task": "Inspect startup flow",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    assert start_response.status_code == 500
    assert start_response.json()["detail"] == "Graph execution failed."

    run_response = client.get(f"/api/runs/{run_id}")
    run = run_response.json()
    assert run["status"] == "failed"
    assert "ghp_secret_token" not in (run["error_message"] or "")

    events = client.get(f"/api/runs/{run_id}/events").json()
    import_failed = next(event for event in events if event["event_type"] == "repo_import_failed")
    assert "ghp_secret_token" not in (import_failed["message"] or "")


def test_get_run_returns_patch_diff_and_approval_payload(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    created = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
        },
    ).json()

    client.post(f"/api/runs/{created['id']}/start")
    response = client.get(f"/api/runs/{created['id']}")

    assert response.status_code == 200
    run = response.json()
    assert run["approval_payload"]["question"] == "Approve this patch?"
    assert "diff --git" in run["patch_diff"]

    events_response = client.get(f"/api/runs/{created['id']}/events")
    events = events_response.json()
    assert events[0]["event_type"] == "run_created"
    assert events[1]["event_type"] == "run_started"
    assert any(event["event_type"] == "pending_approval" for event in events)


def test_approve_run_persists_final_report_test_result_verification_and_risk(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    write_file(tmp_path / "test_sample.py", "def test_sample():\n    assert True\n")
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
            "test_command": "python -m pytest",
        },
    )
    run_id = create_response.json()["id"]
    client.post(f"/api/runs/{run_id}/start")

    approve_response = client.post(f"/api/runs/{run_id}/approve")

    assert approve_response.status_code == 200
    approved = approve_response.json()
    assert approved["status"] == "completed"
    assert approved["approval_status"] == "approved"
    assert approved["current_node"] == "reporter"
    assert approved["has_final_report"] is True
    assert approved["test_result"]["status"] == "passed"
    assert approved["test_result"]["provider"] == "local"
    assert approved["verification_result"]["status"] == "verified"
    assert approved["risk_score"]["level"] in {"medium", "high"}
    assert "## Patch Diff" in approved["final_report"]
    assert "Provider: Local Runner" in approved["final_report"]
    assert "## Verification" in approved["final_report"]
    assert "## Risk Score" in approved["final_report"]

    get_response = client.get(f"/api/runs/{run_id}")
    persisted = get_response.json()
    assert persisted["final_report"] == approved["final_report"]
    assert persisted["test_result"]["status"] == "passed"
    assert persisted["verification_result"]["status"] == "verified"
    assert persisted["risk_score"]["level"] in {"medium", "high"}

    events_response = client.get(f"/api/runs/{run_id}/events")
    events = events_response.json()
    event_types = [event["event_type"] for event in events]
    assert "approved" in event_types
    assert "tests_run" in event_types
    assert "verified" in event_types
    assert "risk_scored" in event_types
    assert "report_generated" in event_types
    assert "run_completed" in event_types
    tests_run = next(event for event in events if event["event_type"] == "tests_run")
    assert tests_run["payload"]["provider"] == "local"


def test_reject_run_persists_final_report_and_approval_status(
    client: TestClient,
    tmp_path: Path,
) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "export function AuthProvider() {",
                "  const [token, setToken] = useState<string | null>(null);",
                "  // token persistence should restore localStorage on refresh",
                "  localStorage.setItem('token', token ?? '');",
                "  return null;",
                "}",
                "",
            ],
        ),
    )
    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
        },
    )
    run_id = create_response.json()["id"]
    client.post(f"/api/runs/{run_id}/start")

    reject_response = client.post(f"/api/runs/{run_id}/reject")

    assert reject_response.status_code == 200
    rejected = reject_response.json()
    assert rejected["status"] == "rejected"
    assert rejected["approval_status"] == "rejected"
    assert rejected["has_final_report"] is True
    assert rejected["verification_result"]["status"] == "rejected"
    assert rejected["risk_score"]["level"] == "high"
    assert "## Approval\nPatch rejected by user." in rejected["final_report"]
    assert "Reason: Patch rejected by user." in rejected["final_report"]

    get_response = client.get(f"/api/runs/{run_id}")
    persisted = get_response.json()
    assert persisted["approval_status"] == "rejected"
    assert persisted["final_report"] == rejected["final_report"]

    events_response = client.get(f"/api/runs/{run_id}/events")
    event_types = [event["event_type"] for event in events_response.json()]
    assert "rejected" in event_types
    assert "report_generated" in event_types


def test_get_run_does_not_expose_raw_tracebacks(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class BrokenGraph:
        def invoke(self, *_args: object, **_kwargs: object) -> dict[str, object]:
            raise RuntimeError(
                f"Traceback: failure while reading {tmp_path / 'secret.py'}\nextra traceback line",
            )

    monkeypatch.setattr(routes_runs, "build_agent_graph", lambda: BrokenGraph())

    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Cause graph failure",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    assert start_response.status_code == 500
    assert start_response.json()["detail"] == "Graph execution failed."

    get_response = client.get(f"/api/runs/{run_id}")
    run = get_response.json()
    assert run["status"] == "failed"
    assert "Traceback" not in run["error_message"]
    assert str(tmp_path.resolve()) not in run["error_message"]

    events_response = client.get(f"/api/runs/{run_id}/events")
    event_types = [event["event_type"] for event in events_response.json()]
    assert "run_failed" in event_types


def test_start_run_persists_fix_strategy_when_graph_returns_it(
    client: TestClient,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FinishedGraph:
        def invoke(self, *_args: object, **_kwargs: object) -> dict[str, object]:
            return {
                "repo_scan": {"detected_stack": ["React"]},
                "search_results": [],
                "evidence": [],
                "root_cause": "Auth state is not restored.",
                "fix_strategy": {
                    "summary": "Restore token state during provider initialization.",
                    "target_files": ["src/AuthContext.tsx"],
                    "change_plan": ["Read persisted token before first render."],
                    "test_plan": ["Reload while authenticated."],
                    "risks": ["Auth initialization is sensitive."],
                    "non_goals": ["Do not change logout behavior."],
                    "confidence": "medium",
                },
                "final_report": "# Agentrail Report\n\n## Task\nDone",
            }

    monkeypatch.setattr(routes_runs, "build_agent_graph", lambda: FinishedGraph())

    create_response = client.post(
        "/api/runs",
        json={
            "repo_path": str(tmp_path),
            "user_task": "Cause fix strategy persistence",
        },
    )
    run_id = create_response.json()["id"]

    start_response = client.post(f"/api/runs/{run_id}/start")
    assert start_response.status_code == 200
    assert start_response.json()["fix_strategy"]["target_files"] == ["src/AuthContext.tsx"]

    get_response = client.get(f"/api/runs/{run_id}")
    assert get_response.status_code == 200
    assert get_response.json()["fix_strategy"]["summary"] == (
        "Restore token state during provider initialization."
    )
