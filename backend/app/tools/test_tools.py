from __future__ import annotations

import shlex
import subprocess
import time
from dataclasses import asdict, dataclass
from typing import Literal

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
TestProvider = Literal["local", "e2b"]
TestStatus = Literal["passed", "failed", "skipped", "blocked", "error", "timeout"]


@dataclass(frozen=True)
class SandboxTestResult:
    provider: TestProvider
    command: str | None
    status: TestStatus
    stdout: str
    stderr: str
    exit_code: int | None
    duration_ms: int
    sandbox_id: str | None = None
    error_message: str | None = None


TestCommandResult = SandboxTestResult


def run_test_command(
    repo_path: str,
    test_command: str | None,
    *,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> TestCommandResult:
    if test_command is None or not test_command.strip():
        return TestCommandResult(
            provider="local",
            command=test_command,
            status="skipped",
            stdout="",
            stderr="No test_command provided.",
            exit_code=None,
            duration_ms=0,
        )

    command = normalize_test_command(test_command)
    validate_test_command(command)
    cwd = validate_repo_directory(repo_path)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            command_args(command),
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return TestCommandResult(
            provider="local",
            command=command,
            status="timeout",
            stdout=_safe_text(exc.stdout),
            stderr=_safe_text(exc.stderr) or f"Command timed out after {timeout_seconds}s.",
            exit_code=None,
            duration_ms=_duration_ms(started),
        )

    return TestCommandResult(
        provider="local",
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


PYTEST_PREFIXES = (
    "pytest",
    "python -m pytest",
)


def validate_test_command(command: str) -> None:
    import re
    # Strip accidental surrounding quotes.
    cmd = command.strip()
    if len(cmd) >= 2 and cmd[0] == cmd[-1] and cmd[0] in ("'", '"'):
        command = cmd[1:-1].strip()
    lowered = command.lower()
    if any(pattern in lowered for pattern in BLOCKED_PATTERNS):
        raise ValueError(f"Blocked unsafe test command: {command}")
    # Exact match.
    if command in ALLOWED_COMMANDS:
        return
    # Allow pytest / python -m pytest with safe path and flag args.
    for prefix in PYTEST_PREFIXES:
        if command.startswith(prefix):
            tail = command[len(prefix):].strip()
            if re.fullmatch(r"[\w\-\.\/\s]*", tail):
                return
    raise ValueError(f"Test command is not allowed: {command}")


def normalize_test_command(command: str) -> str:
    cmd = command.strip()
    # Strip surrounding quotes users accidentally type in the form.
    if len(cmd) >= 2 and cmd[0] == cmd[-1] and cmd[0] in ("'", '"'):
        cmd = cmd[1:-1].strip()
    return " ".join(shlex.split(cmd))


def command_args(command: str) -> list[str]:
    validate_test_command(command)
    if command in ALLOWED_COMMANDS:
        return ALLOWED_COMMANDS[command]
    # Pytest with extra path/flag args.
    return shlex.split(command)


def sandbox_result_asdict(result: SandboxTestResult) -> dict[str, object]:
    return asdict(result)


def _duration_ms(started: float) -> int:
    return int((time.monotonic() - started) * 1000)


def _safe_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
