from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import asdict, dataclass

from app.tools.path_policy import validate_repo_directory


ALLOWED_COMMANDS = {
    "pytest": ["pytest"],
    "python -m pytest": ["python", "-m", "pytest"],
    "npm test": ["npm", "test"],
    "npm run test": ["npm", "run", "test"],
    "npm run lint": ["npm", "run", "lint"],
    "npm run build": ["npm", "run", "build"],
    "pnpm test": ["pnpm", "test"],
    "yarn test": ["yarn", "test"],
}
BLOCKED_PATTERNS = (
    "rm -rf",
    "sudo",
    "curl | bash",
    "wget | bash",
    "chmod -r",
    "chown -r",
    "dd",
    "mkfs",
    "shutdown",
    "reboot",
    "kill",
)
DEFAULT_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class TestCommandResult:
    command: str | None
    status: str
    stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: int


def run_test_command(
    repo_path: str,
    test_command: str | None,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> TestCommandResult:
    if test_command is None or not test_command.strip():
        return TestCommandResult(
            command=test_command,
            status="skipped",
            stdout="",
            stderr="No test_command provided.",
            exit_code=None,
            duration_ms=0,
        )

    command = _normalize_command(test_command)
    _validate_command(command)
    cwd = validate_repo_directory(repo_path)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            ALLOWED_COMMANDS[command],
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return TestCommandResult(
            command=command,
            status="timeout",
            stdout=_safe_text(exc.stdout),
            stderr=_safe_text(exc.stderr) or f"Command timed out after {timeout_seconds}s.",
            exit_code=None,
            duration_ms=_duration_ms(started),
        )

    return TestCommandResult(
        command=command,
        status="passed" if completed.returncode == 0 else "failed",
        stdout=completed.stdout,
        stderr=completed.stderr,
        exit_code=completed.returncode,
        duration_ms=_duration_ms(started),
    )


def run_test_command_asdict(
    repo_path: str,
    test_command: str | None,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> dict[str, object]:
    return asdict(
        run_test_command(
            repo_path,
            test_command,
            timeout_seconds=timeout_seconds,
        ),
    )


def _validate_command(command: str) -> None:
    lowered = command.lower()
    if any(pattern in lowered for pattern in BLOCKED_PATTERNS):
        raise ValueError(f"Blocked unsafe test command: {command}")
    if command not in ALLOWED_COMMANDS:
        raise ValueError(f"Test command is not allowed: {command}")


def _normalize_command(command: str) -> str:
    return " ".join(shlex.split(command))


def _duration_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _safe_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
