from __future__ import annotations

from typing import Any
from unittest.mock import patch
from uuid import uuid4

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from app.agents.graph import build_agent_graph
from app.agents.nodes.reporter import reporter_node
from app.agents.nodes.risk_scorer import risk_scorer_node
from app.agents.nodes.verifier import verifier_node
from app.core.config import Settings
from app.evals.metrics import EvalResult, score_eval_run
from app.evals.report import render_eval_report
from app.evals.scenarios import EvalScenario, load_default_scenarios


def run_eval_scenario(scenario: EvalScenario) -> EvalResult:
    run_state = execute_eval_scenario(scenario)
    return score_eval_run(scenario, run_state)


def execute_eval_scenario(scenario: EvalScenario) -> dict[str, Any]:
    graph = build_agent_graph(checkpointer=InMemorySaver())
    config = {"configurable": {"thread_id": f"eval-{scenario.id}-{uuid4()}"}}
    initial_state = {
        "repo_path": str(scenario.resolved_repo_path),
        "user_task": scenario.user_task,
        "expected_behavior": scenario.expected_behavior,
        "test_command": scenario.test_command,
    }
    deterministic_settings = Settings(
        llm_root_cause_enabled=False,
        llm_fix_strategy_enabled=False,
        e2b_enabled=False,
        e2b_api_key=None,
        sandbox_runner_provider="local",
    )

    with _deterministic_settings_patch(deterministic_settings):
        try:
            interrupted = graph.invoke(initial_state, config=config)
            approval_required = _has_interrupt(interrupted)
            if approval_required:
                result = graph.invoke(Command(resume="approve"), config=config)
            else:
                result = interrupted
        except ValueError as exc:
            result = dict(graph.get_state(config).values)
            result["test_result"] = {
                "provider": "local",
                "command": scenario.test_command,
                "status": "blocked" if "unsafe test command" in str(exc).lower() else "error",
                "stdout": "",
                "stderr": str(exc),
                "exit_code": None,
                "duration_ms": 0,
                "sandbox_id": None,
                "error_message": str(exc),
            }
            result.update(verifier_node(result))
            result.update(risk_scorer_node(result))
            result.update(reporter_node(result))
            approval_required = True

    result["__eval_approval_required"] = approval_required
    return result


def run_default_scenarios() -> list[EvalResult]:
    return [run_eval_scenario(scenario) for scenario in load_default_scenarios()]


def main() -> None:
    scenarios = load_default_scenarios()
    results = [run_eval_scenario(scenario) for scenario in scenarios]
    for scenario, result in zip(scenarios, results, strict=True):
        failed = [check["name"] for check in result.checks if not check["passed"]]
        status = "PASS" if result.passed else "FAIL"
        print(f"{status} {scenario.name}: {result.score}/100")
        if failed:
            print(f"  failed checks: {', '.join(str(item) for item in failed)}")
    print()
    print(render_eval_report(scenarios, results))


def _has_interrupt(result: dict[str, object]) -> bool:
    interrupts = result.get("__interrupt__")
    return isinstance(interrupts, list) and bool(interrupts)


def _deterministic_settings_patch(settings: Settings):
    return _MultiPatch(
        [
            patch("app.agents.nodes.root_cause.get_settings", lambda: settings),
            patch("app.agents.nodes.fix_strategy.get_settings", lambda: settings),
            patch("app.agents.nodes.test_runner.get_settings", lambda: settings),
        ],
    )


class _MultiPatch:
    def __init__(self, patches: list[Any]) -> None:
        self._patches = patches

    def __enter__(self) -> None:
        for item in self._patches:
            item.__enter__()

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        for item in reversed(self._patches):
            item.__exit__(exc_type, exc, traceback)


if __name__ == "__main__":
    main()
