from __future__ import annotations

import io
import tarfile
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.services import e2b_service
from app.services.e2b_service import create_sandbox_upload_archive, run_tests_in_e2b


def write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _settings(**updates: object) -> Settings:
    values = {
        "e2b_enabled": True,
        "e2b_api_key": "sk-test-secret",
        "e2b_timeout_seconds": 120,
        **updates,
    }
    return Settings(**values)


def test_e2b_enabled_without_api_key_returns_clean_error(tmp_path: Path) -> None:
    result = run_tests_in_e2b(
        str(tmp_path),
        "python -m pytest",
        120,
        settings=_settings(e2b_api_key=None),
    )

    assert result.provider == "e2b"
    assert result.status == "error"
    assert result.exit_code is None
    assert "API key" in (result.error_message or "")


def test_e2b_sdk_import_is_lazy_and_missing_sdk_returns_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_sdk() -> object:
        raise ImportError("No module named 'e2b'")

    monkeypatch.setattr(e2b_service, "_load_sandbox_class", missing_sdk)

    result = run_tests_in_e2b(
        str(tmp_path),
        "python -m pytest",
        120,
        settings=_settings(),
    )

    assert result.status == "error"
    assert result.provider == "e2b"
    assert "E2B SDK is not installed" in (result.error_message or "")


def test_e2b_runner_rejects_blocked_command_before_creating_sandbox(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_if_loaded() -> object:
        raise AssertionError("sandbox loader should not run")

    monkeypatch.setattr(e2b_service, "_load_sandbox_class", fail_if_loaded)

    result = run_tests_in_e2b(
        str(tmp_path),
        "pytest && rm -rf /",
        120,
        settings=_settings(),
    )

    assert result.status == "blocked"
    assert "Blocked unsafe test command" in (result.error_message or "")


def test_sandbox_upload_archive_excludes_secret_and_heavy_paths(tmp_path: Path) -> None:
    write_file(tmp_path / "app.py", "print('safe')\n")
    write_file(tmp_path / ".env", "E2B_API_KEY=secret\n")
    write_file(tmp_path / ".env.local", "TOKEN=secret\n")
    write_file(tmp_path / "secrets.json", "{}\n")
    write_file(tmp_path / "cert.pem", "secret\n")
    write_file(tmp_path / "node_modules" / "pkg" / "index.js", "heavy\n")
    write_file(tmp_path / ".next" / "cache" / "file", "heavy\n")

    archive = create_sandbox_upload_archive(str(tmp_path), max_upload_mb=50)
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        names = tar.getnames()

    assert "app.py" in names
    assert ".env" not in names
    assert ".env.local" not in names
    assert "secrets.json" not in names
    assert "cert.pem" not in names
    assert all(not name.startswith("node_modules/") for name in names)
    assert all(not name.startswith(".next/") for name in names)


def test_e2b_runner_uploads_archive_and_runs_allowed_command(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_file(tmp_path / "test_sample.py", "def test_sample():\n    assert True\n")
    commands: list[str] = []
    writes: list[tuple[str, bytes]] = []

    class FakeCommands:
        def run(self, cmd: str, **kwargs: object) -> SimpleNamespace:
            commands.append(cmd)
            if cmd == "python -m pytest":
                assert kwargs["cwd"] == "/home/user/agentrail-workspace"
                assert kwargs["timeout"] == 120
                return SimpleNamespace(
                    stdout="1 passed",
                    stderr="",
                    exit_code=0,
                    returncode=0,
                )
            return SimpleNamespace(stdout="", stderr="", exit_code=0, returncode=0)

    class FakeFiles:
        def write(self, path: str, data: bytes) -> None:
            writes.append((path, data))

    class FakeSandbox:
        sandbox_id = "sandbox-123"
        commands = FakeCommands()
        files = FakeFiles()

        def kill(self) -> None:
            commands.append("kill")

    class FakeSandboxClass:
        @classmethod
        def create(cls, **kwargs: object) -> FakeSandbox:
            assert kwargs["api_key"] == "sk-test-secret"
            return FakeSandbox()

    monkeypatch.setattr(e2b_service, "_load_sandbox_class", lambda: FakeSandboxClass)

    result = run_tests_in_e2b(
        str(tmp_path),
        "python -m pytest",
        120,
        settings=_settings(),
    )

    assert result.provider == "e2b"
    assert result.status == "passed"
    assert result.stdout == "1 passed"
    assert result.exit_code == 0
    assert result.sandbox_id == "sandbox-123"
    assert commands[:3] == [
        "mkdir -p /home/user/agentrail-workspace",
        "tar -xzf /tmp/agentrail-repo.tar.gz -C /home/user/agentrail-workspace",
        "python -m pytest",
    ]
    assert writes[0][0] == "/tmp/agentrail-repo.tar.gz"


def test_e2b_error_sanitization_does_not_leak_api_key(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def boom() -> object:
        raise RuntimeError("bad auth sk-test-secret traceback")

    monkeypatch.setattr(e2b_service, "_load_sandbox_class", boom)

    result = run_tests_in_e2b(
        str(tmp_path),
        "python -m pytest",
        120,
        settings=_settings(),
    )

    assert result.status == "error"
    assert "sk-test-secret" not in (result.error_message or "")
