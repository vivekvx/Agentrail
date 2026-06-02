from __future__ import annotations

from app.agents.state import AgentRunState
from app.tools.test_tools import run_test_command_asdict


def test_runner_node(state: AgentRunState) -> dict[str, object]:
    if state.get("approval_status") != "approved":
        return {}

    test_command = state.get("test_command")
    result = run_test_command_asdict(
        state["repo_path"],
        test_command if isinstance(test_command, str) else None,
    )
    return {"test_result": result}
