from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.core.config import Settings
from app.services import repo_importer


def make_settings(tmp_path: Path, **overrides: object) -> Settings:
    values = {
        "database_url": "sqlite:///./test_devpilot_verify.db",
        "openai_api_key": None,
        "openai_model": "gpt-4.1-mini",
        "llm_root_cause_enabled": False,
        "llm_fix_strategy_enabled": False,
        "llm_timeout_seconds": 30,
        "repo_workspace_dir": str(tmp_path / "repos"),
        "github_import_enabled": True,
        "git_clone_timeout_seconds": 60,
        "max_repo_size_mb": 100,
        "github_token": "ghp_secret_token",
    }
    values.update(overrides)
    return Settings.model_construct(**values)


def test_repo_importer_calls_git_clone_with_shell_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        captured["kwargs"] = kwargs
        destination = Path(command[-1])
        (destination / ".git").mkdir(parents=True, exist_ok=True)
        (destination / "README.md").write_text("hello\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_importer.subprocess, "run", fake_run)

    result = repo_importer.import_github_repository(
        "https://github.com/fastapi/fastapi",
        settings=make_settings(tmp_path),
    )

    assert captured["command"][:3] == ["git", "clone", "--depth=1"]
    assert captured["kwargs"]["shell"] is False
    assert result.repo_path.parent == (tmp_path / "repos").resolve()


def test_repo_importer_respects_workspace_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        destination = Path(command[-1])
        assert str(destination).startswith(str((tmp_path / "repos").resolve()))
        (destination / ".git").mkdir(parents=True, exist_ok=True)
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    monkeypatch.setattr(repo_importer.subprocess, "run", fake_run)

    result = repo_importer.import_github_repository(
        "https://github.com/encode/starlette",
        settings=make_settings(tmp_path),
    )

    assert result.workspace_relative_path == "encode__starlette"


def test_repo_importer_handles_clone_failure_with_sanitized_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            command,
            128,
            stdout="",
            stderr="fatal: could not read Username for 'https://github.com': terminal prompts disabled",
        )

    monkeypatch.setattr(repo_importer.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError) as exc_info:
        repo_importer.import_github_repository(
            "https://github.com/fastapi/fastapi",
            settings=make_settings(tmp_path),
        )

    assert str(exc_info.value) == "Git clone failed: authentication failed."
    assert "ghp_secret_token" not in str(exc_info.value)


def test_repo_importer_uses_cached_repo_when_present(tmp_path: Path) -> None:
    settings = make_settings(tmp_path)
    destination = (tmp_path / "repos" / "fastapi__fastapi").resolve()
    (destination / ".git").mkdir(parents=True, exist_ok=True)
    (destination / "README.md").write_text("cached\n", encoding="utf-8")

    result = repo_importer.import_github_repository(
        "https://github.com/fastapi/fastapi",
        settings=settings,
    )

    assert result.used_cache is True
    assert result.repo_path == destination
