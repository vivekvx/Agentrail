from __future__ import annotations

import io
import tarfile
import time
from pathlib import Path
from typing import Any

from app.core.config import Settings, get_settings
from app.tools.path_policy import is_excluded_secret_file, validate_repo_directory
from app.tools.test_tools import (
    SandboxTestResult,
    TestStatus,
    normalize_test_command,
    validate_test_command,
)


SANDBOX_WORKDIR = "/home/user/devpilot-workspace"
SANDBOX_ARCHIVE_PATH = "/tmp/devpilot-repo.tar.gz"
EXCLUDED_DIRS = {
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    "dist",
    "build",
    ".next",
    "coverage",
}


def run_tests_in_e2b(
    repo_path: str,
    command: str,
    timeout_seconds: int,
    *,
    settings: Settings | None = None,
) -> SandboxTestResult:
    settings = settings or get_settings()
    started = time.monotonic()
    sandbox: Any | None = None
    normalized_command: str | None = None
    sandbox_id: str | None = None

    try:
        normalized_command = normalize_test_command(command)
        validate_test_command(normalized_command)
    except ValueError as exc:
        return _result(
            command=normalized_command or command,
            status="blocked",
            stderr=str(exc),
            duration_ms=_duration_ms(started),
            error_message=str(exc),
        )

    if not settings.e2b_enabled:
        return _result(
            command=normalized_command,
            status="skipped",
            stderr="E2B sandbox runner is disabled.",
            duration_ms=_duration_ms(started),
            error_message="E2B sandbox runner is disabled.",
        )

    if not settings.e2b_api_key:
        return _result(
            command=normalized_command,
            status="error",
            stderr="E2B API key is required when E2B sandbox runner is enabled.",
            duration_ms=_duration_ms(started),
            error_message="E2B API key is required when E2B sandbox runner is enabled.",
        )

    try:
        repo = validate_repo_directory(repo_path)
        archive = create_sandbox_upload_archive(
            str(repo),
            max_upload_mb=settings.max_sandbox_upload_mb,
        )
        sandbox_cls = _load_sandbox_class()
        sandbox = _create_sandbox(
            sandbox_cls,
            settings=settings,
            timeout_seconds=timeout_seconds,
        )
        sandbox_id = _sandbox_id(sandbox)
        sandbox.commands.run(f"mkdir -p {SANDBOX_WORKDIR}", timeout=timeout_seconds)
        sandbox.files.write(SANDBOX_ARCHIVE_PATH, archive)
        sandbox.commands.run(
            f"tar -xzf {SANDBOX_ARCHIVE_PATH} -C {SANDBOX_WORKDIR}",
            timeout=timeout_seconds,
        )
        completed = sandbox.commands.run(
            normalized_command,
            cwd=SANDBOX_WORKDIR,
            timeout=timeout_seconds,
        )
    except ImportError:
        message = "E2B SDK is not installed. Install the optional e2b package to use sandbox tests."
        return _result(
            command=normalized_command,
            status="error",
            stderr=message,
            duration_ms=_duration_ms(started),
            sandbox_id=sandbox_id,
            error_message=message,
        )
    except Exception as exc:
        message = _sanitize_error(str(exc), settings)
        return _result(
            command=normalized_command,
            status="error",
            stderr=message,
            duration_ms=_duration_ms(started),
            sandbox_id=sandbox_id,
            error_message=message,
        )
    finally:
        _terminate_sandbox(sandbox)

    exit_code = _exit_code(completed)
    return _result(
        command=normalized_command,
        status="passed" if exit_code == 0 else "failed",
        stdout=_text_attr(completed, "stdout"),
        stderr=_text_attr(completed, "stderr"),
        exit_code=exit_code,
        duration_ms=_duration_ms(started),
        sandbox_id=sandbox_id,
    )


def create_sandbox_upload_archive(repo_path: str, *, max_upload_mb: int) -> bytes:
    repo = validate_repo_directory(repo_path)
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for path in _iter_upload_paths(repo):
            tar.add(path, arcname=str(path.relative_to(repo)), recursive=False)

    data = buffer.getvalue()
    max_bytes = max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise ValueError(f"Sandbox upload archive exceeds {max_upload_mb} MB limit.")
    return data


def _iter_upload_paths(repo: Path) -> list[Path]:
    paths: list[Path] = []
    for path in sorted(repo.rglob("*")):
        relative_parts = path.relative_to(repo).parts
        if any(part in EXCLUDED_DIRS for part in relative_parts):
            continue
        if path.is_dir():
            continue
        if is_excluded_secret_file(path):
            continue
        paths.append(path)
    return paths


def _load_sandbox_class() -> object:
    from e2b import Sandbox

    return Sandbox


def _create_sandbox(
    sandbox_cls: object,
    *,
    settings: Settings,
    timeout_seconds: int,
) -> object:
    kwargs: dict[str, object] = {
        "api_key": settings.e2b_api_key,
        "timeout": timeout_seconds,
    }
    if settings.e2b_template:
        kwargs["template"] = settings.e2b_template
    create = getattr(sandbox_cls, "create")
    return create(**kwargs)


def _terminate_sandbox(sandbox: object | None) -> None:
    if sandbox is None:
        return
    for method_name in ("kill", "close"):
        method = getattr(sandbox, method_name, None)
        if callable(method):
            try:
                method()
            except Exception:
                return
            return


def _exit_code(result: object) -> int | None:
    for attr in ("exit_code", "returncode"):
        value = getattr(result, attr, None)
        if isinstance(value, int):
            return value
    return None


def _text_attr(result: object, attr: str) -> str:
    value = getattr(result, attr, "")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value if isinstance(value, str) else ""


def _sandbox_id(sandbox: object) -> str | None:
    for attr in ("sandbox_id", "id"):
        value = getattr(sandbox, attr, None)
        if isinstance(value, str):
            return value
    return None


def _sanitize_error(message: str, settings: Settings) -> str:
    sanitized = message.strip().splitlines()[0]
    if settings.e2b_api_key:
        sanitized = sanitized.replace(settings.e2b_api_key, "[secret]")
    sanitized = sanitized.replace("Traceback", "").strip()
    return sanitized or "E2B sandbox runner failed."


def _result(
    *,
    command: str | None,
    status: TestStatus,
    duration_ms: int,
    stdout: str = "",
    stderr: str = "",
    exit_code: int | None = None,
    sandbox_id: str | None = None,
    error_message: str | None = None,
) -> SandboxTestResult:
    return SandboxTestResult(
        provider="e2b",
        command=command,
        status=status,
        stdout=stdout,
        stderr=stderr,
        exit_code=exit_code,
        duration_ms=duration_ms,
        sandbox_id=sandbox_id,
        error_message=error_message,
    )


def _duration_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)
