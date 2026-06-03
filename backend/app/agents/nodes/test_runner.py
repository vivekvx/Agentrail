from __future__ import annotations

from app.agents.state import AgentRunState
from app.core.config import Settings, get_settings
from app.services.e2b_service import run_tests_in_e2b
from app.tools.test_tools import run_test_command_asdict, sandbox_result_asdict


def test_runner_node(state: AgentRunState) -> dict[str, object]:
    if state.get("approval_status") != "approved":
        return {}

    test_command = state.get("test_command")
    command = test_command if isinstance(test_command, str) else None
    settings = get_settings()
    if command and _should_use_e2b(settings):
        result = run_tests_in_e2b(
            state["repo_path"],
            command,
            settings.e2b_timeout_seconds,
            settings=settings,
        )
        return {"test_result": sandbox_result_asdict(result)}

    result = run_test_command_asdict(
        state["repo_path"],
        command,
    )
    return {"test_result": result}


def _should_use_e2b(settings: Settings) -> bool:
    provider = settings.sandbox_runner_provider.lower().strip()
    return provider == "e2b" or (settings.e2b_enabled and bool(settings.e2b_api_key))
