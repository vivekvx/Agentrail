from __future__ import annotations

from pathlib import Path

from app.agents.graph import build_agent_graph


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_agent_graph_runs_planner_repo_scanner_and_code_search(tmp_path: Path) -> None:
    write_file(tmp_path / "requirements.txt", "fastapi\npytest\n")
    write_file(
        tmp_path / "app" / "main.py",
        "from fastapi import FastAPI\napp = FastAPI()\n",
    )

    graph = build_agent_graph()
    result = graph.invoke(
        {
            "repo_path": str(tmp_path),
            "user_task": "Find FastAPI app setup",
        },
    )

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
    assert "Find FastAPI app setup" in result["root_cause"]
    assert "app/main.py:1-2" in result["root_cause"]
    assert "from fastapi import FastAPI" in result["root_cause"]
    report = result["final_report"]
    assert report.startswith("# DevPilot Verify Report")
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

    graph = build_agent_graph()
    result = graph.invoke(
        {
            "repo_path": str(tmp_path),
            "user_task": "Investigate database timeout",
        },
    )

    assert result["plan"]["search_queries"] == [
        "investigate",
        "database",
        "timeout",
    ]
    assert result["repo_scan"]["detected_stack"] == []
    assert result["search_results"] == []
    assert result["evidence"] == []
    assert result["root_cause"] == (
        "No root cause identified yet for task 'Investigate database timeout'. "
        "No evidence was collected from code search results."
    )
    assert "No evidence collected." in result["final_report"]


def test_agent_graph_skips_secret_files_when_reading_evidence(tmp_path: Path) -> None:
    write_file(tmp_path / ".env", "database_url=postgres://secret\n")
    write_file(tmp_path / "app.py", "database_url = 'sqlite:///local.db'\n")

    graph = build_agent_graph()
    result = graph.invoke(
        {
            "repo_path": str(tmp_path),
            "user_task": "Find DATABASE_URL",
        },
    )

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

    graph = build_agent_graph()
    result = graph.invoke(
        {
            "repo_path": str(tmp_path),
            "user_task": "Fix AuthContext localStorage token persistence on refresh",
        },
    )

    patch_diff = result["patch_diff"]
    assert "diff --git a/src/AuthContext.tsx b/src/AuthContext.tsx" in patch_diff
    assert "localStorage.getItem(\"token\")" in patch_diff
    assert "useState<string | null>(() => {" in patch_diff
    assert result["final_report"].startswith("# DevPilot Verify Report")
    assert "## Patch Diff" in result["final_report"]
    assert "src/AuthContext.tsx" in result["final_report"]
