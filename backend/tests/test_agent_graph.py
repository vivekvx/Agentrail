from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agents.graph import build_agent_graph


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def invoke_to_approval(input_state: dict[str, str]) -> tuple[object, dict[str, object]]:
    graph = build_agent_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": str(uuid4())}}
    interrupted = graph.invoke(input_state, config=config)
    assert "__interrupt__" in interrupted
    return graph, config


def test_agent_graph_runs_planner_repo_scanner_and_code_search(tmp_path: Path) -> None:
    write_file(tmp_path / "requirements.txt", "fastapi\npytest\n")
    write_file(
        tmp_path / "app" / "main.py",
        "from fastapi import FastAPI\napp = FastAPI()\n",
    )

    graph, config = invoke_to_approval(
        {
            "repo_path": str(tmp_path),
            "user_task": "Find FastAPI app setup",
        },
    )
    result = graph.invoke(Command(resume="approve"), config=config)

    assert result["plan"] == {
        "summary": "Inspect the repository, identify relevant files, then search for task terms.",
        "search_queries": ["find", "fastapi", "app", "setup"],
    }
    assert result["repo_scan"]["detected_stack"] == [
        "FastAPI",
        "requirements.txt",
        "pytest",
    ]
    assert result["repo_scan"]["probable_backend_directory"] == "app"
    assert {
        "file_path": "app/main.py",
        "line_number": 1,
        "matched_line": "from fastapi import FastAPI",
        "score": 2,
    } in result["search_results"]
    assert {
        "file_path": "app/main.py",
        "start_line": 1,
        "end_line": 2,
        "snippet": "1: from fastapi import FastAPI\n2: app = FastAPI()",
        "reason": "Search matched line 1: from fastapi import FastAPI",
    } in result["evidence"]
    assert "FastAPI" in result["root_cause"]
    assert "app/main.py" in result["root_cause"] or "from fastapi import FastAPI" in result["root_cause"]
    report = result["final_report"]
    assert report.startswith("# Agentrail Report")
    assert "## Task\nFind FastAPI app setup" in report
    assert "## Detected Stack\n- FastAPI\n- requirements.txt\n- pytest" in report
    assert "## Investigation Plan" in report
    assert "## Files Found" in report
    assert "app/main.py:1-2" in report
    assert "from fastapi import FastAPI" in report
    assert "## Root Cause" in report
    assert result["root_cause"] in report
    assert "## Next Step" in report


def test_agent_graph_handles_tasks_without_search_hits(tmp_path: Path) -> None:
    write_file(tmp_path / "README.md", "hello\n")

    graph, config = invoke_to_approval(
        {
            "repo_path": str(tmp_path),
            "user_task": "Investigate database timeout",
        },
    )
    result = graph.invoke(Command(resume="approve"), config=config)

    assert result["plan"]["search_queries"] == [
        "investigate",
        "database",
        "timeout",
    ]
    assert result["repo_scan"]["detected_stack"] == []
    assert result["search_results"] == []
    assert result["evidence"] == []
    assert result["root_cause"] is not None
    assert isinstance(result["root_cause"], str)
    assert "No evidence collected." in result["final_report"]


def test_agent_graph_skips_secret_files_when_reading_evidence(tmp_path: Path) -> None:
    write_file(tmp_path / ".env", "database_url=postgres://secret\n")
    write_file(tmp_path / "app.py", "database_url = 'sqlite:///local.db'\n")

    graph, config = invoke_to_approval(
        {
            "repo_path": str(tmp_path),
            "user_task": "Find DATABASE_URL",
        },
    )
    result = graph.invoke(Command(resume="approve"), config=config)

    evidence_paths = [item["file_path"] for item in result["evidence"]]
    assert ".env" not in evidence_paths
    assert "app.py" in evidence_paths
    assert ".env" not in result["root_cause"]


def test_agent_graph_generates_auth_refresh_patch_preview(tmp_path: Path) -> None:
    write_file(
        tmp_path / "src" / "AuthContext.tsx",
        "\n".join(
            [
                "import { useState } from 'react';",
                "",
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

    graph, config = invoke_to_approval(
        {
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence on refresh",
        },
    )
    interrupted = graph.get_state(config).interrupts[0].value
    assert interrupted["question"] == "Approve this patch?"
    assert "src/AuthContext.tsx" in interrupted["patch_diff"]

    result = graph.invoke(Command(resume="approve"), config=config)

    patch_diff = result["patch_diff"]
    assert "diff --git a/src/AuthContext.tsx b/src/AuthContext.tsx" in patch_diff
    assert "localStorage.getItem(\"token\")" in patch_diff
    assert "useState<string | null>(() => {" in patch_diff
    assert result["final_report"].startswith("# Agentrail Report")
    assert "## Patch Diff" in result["final_report"]
    assert "## Approval\nPatch approved by user." in result["final_report"]
    assert "src/AuthContext.tsx" in result["final_report"]


def test_agent_graph_rejects_patch_and_reports_reason(tmp_path: Path) -> None:
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

    graph, config = invoke_to_approval(
        {
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence",
        },
    )
    result = graph.invoke(Command(resume="reject"), config=config)

    assert result["approval_status"] == "rejected"
    assert result["rejection_reason"] == "Patch rejected by user."
    assert "test_result" not in result
    assert "## Approval\nPatch rejected by user." in result["final_report"]
    assert "Reason: Patch rejected by user." in result["final_report"]


def test_agent_graph_runs_tests_after_approval(tmp_path: Path) -> None:
    write_file(tmp_path / "target.py", "value = 'target'\n")
    write_file(tmp_path / "test_sample.py", "def test_sample():\n    assert True\n")

    graph, config = invoke_to_approval(
        {
            "repo_path": str(tmp_path),
            "user_task": "Find target",
            "test_command": "python -m pytest",
        },
    )
    result = graph.invoke(Command(resume="approve"), config=config)

    assert result["approval_status"] == "approved"
    assert result["test_result"]["status"] == "passed"
    assert result["test_result"]["command"] == "python -m pytest"
    assert "## Test Results" in result["final_report"]
    assert "Status: passed" in result["final_report"]
    assert result["verification_result"]["status"] in {
        "needs_manual_review",
        "verified",
    }
    assert "## Verification" in result["final_report"]
    assert "Confidence:" in result["final_report"]
    assert result["risk_score"]["level"] in {"low", "medium", "high"}
    assert "## Risk Score" in result["final_report"]
