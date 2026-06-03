from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.agents.nodes import fix_strategy as fix_strategy_node_module
from app.agents.nodes.patch_generator import patch_generator_node
from app.agents.nodes.reporter import reporter_node
from app.core.config import Settings
from app.services import llm_provider
from app.services.llm_provider import FixStrategy


def make_settings(**overrides: object) -> Settings:
    values = {
        "database_url": "sqlite:///./test_agentrail.db",
        "openai_api_key": None,
        "openai_model": "gpt-4.1-mini",
        "llm_root_cause_enabled": False,
        "llm_fix_strategy_enabled": False,
        "llm_timeout_seconds": 30,
    }
    values.update(overrides)
    return Settings.model_construct(**values)


def sample_evidence() -> list[dict[str, object]]:
    return [
        {
            "file_path": "src/AuthContext.tsx",
            "start_line": 2,
            "end_line": 4,
            "snippet": (
                "2: const [token, setToken] = useState<string | null>(null);\n"
                "3: localStorage.setItem('token', token ?? '');"
            ),
            "reason": "Search matched token persistence logic.",
        }
    ]


class FakeCompletions:
    def __init__(self, response_text: str, capture: dict[str, object] | None = None) -> None:
        self.response_text = response_text
        self.capture = capture

    def create(self, **kwargs: object) -> object:
        if self.capture is not None:
            self.capture.update(kwargs)
        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(content=self.response_text),
                )
            ]
        )


class FakeClient:
    def __init__(self, response_text: str, capture: dict[str, object] | None = None) -> None:
        self.chat = SimpleNamespace(
            completions=FakeCompletions(response_text, capture),
        )


def test_fix_strategy_disabled_by_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        fix_strategy_node_module,
        "get_settings",
        lambda: make_settings(llm_fix_strategy_enabled=False),
    )

    result = fix_strategy_node_module.fix_strategy_node(
        {
            "user_task": "Fix auth refresh bug",
            "evidence": sample_evidence(),
            "root_cause": "AuthContext initializes token state to null.",
        }
    )

    assert result == {}


def test_missing_openai_key_skips_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        fix_strategy_node_module,
        "get_settings",
        lambda: make_settings(
            llm_fix_strategy_enabled=True,
            openai_api_key=None,
        ),
    )

    result = fix_strategy_node_module.fix_strategy_node(
        {
            "user_task": "Fix auth refresh bug",
            "evidence": sample_evidence(),
            "root_cause": "AuthContext initializes token state to null.",
        }
    )

    assert result == {}


def test_mocked_llm_returns_valid_fix_strategy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        fix_strategy_node_module,
        "get_settings",
        lambda: make_settings(
            llm_fix_strategy_enabled=True,
            openai_api_key="test-key",
        ),
    )
    monkeypatch.setattr(
        fix_strategy_node_module,
        "propose_fix_strategy",
        lambda *args, **kwargs: FixStrategy(
            summary="Restore token state during provider initialization.",
            target_files=["src/AuthContext.tsx"],
            change_plan=[
                "Update the provider initialization path to read persisted auth state."
            ],
            test_plan=["Reload the app while signed in and confirm the session remains active."],
            risks=["Auth state initialization is a sensitive path."],
            non_goals=["Do not change unrelated auth flows or logout logic."],
            confidence="medium",
        ),
    )

    result = fix_strategy_node_module.fix_strategy_node(
        {
            "user_task": "Fix auth refresh bug",
            "expected_behavior": "User remains signed in after refresh.",
            "evidence": sample_evidence(),
            "root_cause": "AuthContext initializes token state to null.",
        }
    )

    assert result["fix_strategy"]["summary"] == (
        "Restore token state during provider initialization."
    )
    assert result["fix_strategy"]["target_files"] == ["src/AuthContext.tsx"]


def test_invalid_llm_output_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        fix_strategy_node_module,
        "get_settings",
        lambda: make_settings(
            llm_fix_strategy_enabled=True,
            openai_api_key="test-key",
        ),
    )
    monkeypatch.setattr(
        fix_strategy_node_module,
        "propose_fix_strategy",
        lambda *args, **kwargs: None,
    )

    result = fix_strategy_node_module.fix_strategy_node(
        {
            "user_task": "Fix auth refresh bug",
            "evidence": sample_evidence(),
            "root_cause": "AuthContext initializes token state to null.",
        }
    )

    assert result == {}


def test_target_files_not_in_evidence_are_filtered(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response_text = json.dumps(
        {
            "summary": "Focus on the auth context initialization path.",
            "target_files": ["src/AuthContext.tsx", "src/Other.tsx"],
            "change_plan": ["Restore persisted auth state before render."],
            "test_plan": ["Reload after signing in."],
            "risks": ["Auth state is sensitive."],
            "non_goals": ["Do not change token format."],
            "confidence": "medium",
        }
    )
    monkeypatch.setattr(
        llm_provider,
        "_get_openai_client",
        lambda api_key, timeout_seconds: FakeClient(response_text),
    )

    result = llm_provider.propose_fix_strategy(
        sample_evidence(),
        "Fix auth refresh bug",
        "User remains signed in after refresh.",
        "Detected stack: React",
        "AuthContext initializes token state to null.",
        settings=make_settings(
            llm_fix_strategy_enabled=True,
            openai_api_key="test-key",
        ),
    )

    assert result is not None
    assert result.target_files == ["src/AuthContext.tsx"]


def test_reporter_includes_fix_strategy_section_when_present() -> None:
    report = reporter_node(
        {
            "user_task": "Fix auth refresh bug",
            "root_cause": "AuthContext initializes token state to null.",
            "fix_strategy": {
                "summary": "Restore token state during provider initialization.",
                "target_files": ["src/AuthContext.tsx"],
                "change_plan": ["Read localStorage during provider boot."],
                "test_plan": ["Reload while authenticated."],
                "risks": ["Auth initialization is sensitive."],
                "non_goals": ["Do not change logout behavior."],
                "confidence": "medium",
            },
        }
    )["final_report"]

    assert "## Fix Strategy" in report
    assert "Summary: Restore token state during provider initialization." in report
    assert "Target Files:" in report
    assert "Change Plan:" in report
    assert "Test Plan:" in report
    assert "Risks:" in report
    assert "Non-Goals:" in report
    assert "Confidence: medium" in report


def test_reporter_omits_fix_strategy_section_when_absent() -> None:
    report = reporter_node(
        {
            "user_task": "Fix auth refresh bug",
            "root_cause": "AuthContext initializes token state to null.",
        }
    )["final_report"]

    assert "## Fix Strategy" not in report


def test_patch_generator_still_works_without_fix_strategy() -> None:
    result = patch_generator_node(
        {
            "user_task": "Fix auth refresh",
            "root_cause": "Token persistence is not restored.",
            "evidence": [
                {
                    "file_path": "src/AuthContext.tsx",
                    "start_line": 4,
                    "end_line": 6,
                    "snippet": (
                        "4: const [token, setToken] = useState<string | null>(null);\n"
                        "5: // token persistence should restore localStorage on refresh\n"
                        "6: localStorage.setItem('token', token ?? '')"
                    ),
                    "reason": "Search matched localStorage token persistence.",
                },
            ],
        }
    )

    assert "patch_diff" in result


def test_patch_generator_does_not_generate_patch_from_fix_strategy_only() -> None:
    result = patch_generator_node(
        {
            "user_task": "Fix auth refresh",
            "root_cause": "Token persistence is not restored.",
            "fix_strategy": {
                "summary": "Use localStorage on startup.",
                "target_files": ["src/AuthContext.tsx"],
                "change_plan": ["Read localStorage on startup."],
                "test_plan": ["Reload app."],
                "risks": ["Auth path is sensitive."],
                "non_goals": ["Do not touch unrelated files."],
                "confidence": "medium",
            },
            "evidence": [],
        }
    )

    assert "patch_diff" not in result


def test_no_secret_like_snippets_are_sent_to_fix_strategy_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture: dict[str, object] = {}
    response_text = json.dumps(
        {
            "summary": "Restore token state during provider initialization.",
            "target_files": ["src/AuthContext.tsx"],
            "change_plan": ["Read persisted token before first render."],
            "test_plan": ["Reload while authenticated."],
            "risks": ["Auth initialization is sensitive."],
            "non_goals": ["Do not change unrelated auth flows."],
            "confidence": "medium",
        }
    )
    monkeypatch.setattr(
        llm_provider,
        "_get_openai_client",
        lambda api_key, timeout_seconds: FakeClient(response_text, capture),
    )

    llm_provider.propose_fix_strategy(
        [
            *sample_evidence(),
            {
                "file_path": ".env",
                "start_line": 1,
                "end_line": 1,
                "snippet": "OPENAI_API_KEY=super-secret",
                "reason": "Should be excluded.",
            },
            {
                "file_path": "settings.py",
                "start_line": 1,
                "end_line": 1,
                "snippet": "token = load_token()",
                "reason": 'api_key = "super-secret"',
            },
        ],
        "Fix auth refresh bug",
        "User remains signed in after refresh.",
        "Detected stack: React",
        "AuthContext initializes token state to null.",
        settings=make_settings(
            llm_fix_strategy_enabled=True,
            openai_api_key="test-key",
        ),
    )

    messages = capture["messages"]
    assert isinstance(messages, list)
    prompt_payload = json.loads(messages[1]["content"])
    evidence_payload = prompt_payload["evidence"]
    assert len(evidence_payload) == 2
    assert ".env" not in messages[1]["content"]
    assert "super-secret" not in messages[1]["content"]
