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
