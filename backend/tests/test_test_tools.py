from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.agents.nodes import test_runner as test_runner_module
from app.agents.nodes.test_runner import test_runner_node as run_test_runner_node
from app.core.config import Settings
from app.tools.test_tools import SandboxTestResult
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
    assert test_result["provider"] == "local"
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


def test_test_runner_uses_e2b_when_enabled_with_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(e2b_enabled=True, e2b_api_key="sk-test-secret")

    def fake_e2b(repo_path: str, command: str, timeout_seconds: int, **kwargs: object):
        assert repo_path == str(tmp_path)
        assert command == "python -m pytest"
        assert timeout_seconds == 120
        assert kwargs["settings"] is settings
        return SandboxTestResult(
            provider="e2b",
            command=command,
            status="passed",
            stdout="1 passed",
            stderr="",
            exit_code=0,
            duration_ms=25,
            sandbox_id="sandbox-123",
        )

    def fail_local(*_args: object, **_kwargs: object) -> dict[str, object]:
        raise AssertionError("local runner should not run")

    monkeypatch.setattr(test_runner_module, "get_settings", lambda: settings)
    monkeypatch.setattr(test_runner_module, "run_tests_in_e2b", fake_e2b)
    monkeypatch.setattr(test_runner_module, "run_test_command_asdict", fail_local)

    result = run_test_runner_node(
        {
            "repo_path": str(tmp_path),
            "approval_status": "approved",
            "test_command": "python -m pytest",
        },
    )

    assert result["test_result"]["provider"] == "e2b"
    assert result["test_result"]["sandbox_id"] == "sandbox-123"


def test_test_runner_uses_local_when_e2b_enabled_without_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = Settings(e2b_enabled=True, e2b_api_key=None)

    def fake_local(repo_path: str, command: str | None) -> dict[str, object]:
        assert repo_path == str(tmp_path)
        assert command == "python -m pytest"
        return {
            "provider": "local",
            "command": command,
            "status": "skipped",
            "stdout": "",
            "stderr": "local",
            "exit_code": None,
            "duration_ms": 0,
            "sandbox_id": None,
            "error_message": None,
        }

    def fail_e2b(*_args: object, **_kwargs: object) -> SandboxTestResult:
        raise AssertionError("e2b runner should not run")

    monkeypatch.setattr(test_runner_module, "get_settings", lambda: settings)
    monkeypatch.setattr(test_runner_module, "run_test_command_asdict", fake_local)
    monkeypatch.setattr(test_runner_module, "run_tests_in_e2b", fail_e2b)

    result = run_test_runner_node(
        {
            "repo_path": str(tmp_path),
            "approval_status": "approved",
            "test_command": "python -m pytest",
        },
    )

    assert result["test_result"]["provider"] == "local"


def test_blocked_test_command_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Blocked unsafe test command"):
        run_test_command(str(tmp_path), "pytest && rm -rf /")


def test_missing_test_command_returns_skipped(tmp_path: Path) -> None:
    result = run_test_command(str(tmp_path), None)

    assert result.provider == "local"
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
