from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.agents.nodes.test_runner import test_runner_node as run_test_runner_node
from app.tools.test_tools import run_test_command


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_approved_test_runner_executes_allowed_test_command(tmp_path: Path) -> None:
    write_file(
        tmp_path / "test_sample.py",
        "def test_sample():\n    assert True\n",
    )

    result = run_test_runner_node(
        {
            "repo_path": str(tmp_path),
            "approval_status": "approved",
            "test_command": "python -m pytest",
        },
    )

    test_result = result["test_result"]
    assert test_result["command"] == "python -m pytest"
    assert test_result["status"] == "passed"
    assert test_result["exit_code"] == 0


def test_rejected_test_runner_skips_without_result(tmp_path: Path) -> None:
    result = run_test_runner_node(
        {
            "repo_path": str(tmp_path),
            "approval_status": "rejected",
            "test_command": "python -m pytest",
        },
    )

    assert result == {}


def test_blocked_test_command_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Blocked unsafe test command"):
        run_test_command(str(tmp_path), "pytest && rm -rf /")


def test_missing_test_command_returns_skipped(tmp_path: Path) -> None:
    result = run_test_command(str(tmp_path), None)

    assert result.status == "skipped"
    assert result.command is None
    assert result.exit_code is None
    assert result.stderr == "No test_command provided."


def test_test_command_timeout_is_handled_safely(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(*args: object, **kwargs: object) -> subprocess.CompletedProcess[str]:
        raise subprocess.TimeoutExpired(
            cmd=["python", "-m", "pytest"],
            timeout=1,
            output="partial stdout",
            stderr="partial stderr",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    result = run_test_command(str(tmp_path), "python -m pytest", timeout_seconds=1)

    assert result.status == "timeout"
    assert result.command == "python -m pytest"
    assert result.exit_code is None
    assert result.stdout == "partial stdout"
    assert result.stderr == "partial stderr"
