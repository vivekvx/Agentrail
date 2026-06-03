from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.agents.nodes import reporter, root_cause
from app.core.config import Settings
from app.services import llm_provider
from app.services.llm_provider import RootCauseAnalysis


def make_settings(**overrides: object) -> Settings:
    values = {
        "database_url": "sqlite:///./test_agentrail.db",
        "openai_api_key": None,
        "openai_model": "gpt-4.1-mini",
        "llm_root_cause_enabled": False,
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
            "snippet": "2: const [token, setToken] = useState<string | null>(null);\n3: localStorage.setItem('token', token ?? '');",
            "reason": "Search matched token persistence logic.",
        }
    ]


def test_root_cause_deterministic_fallback_when_llm_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        root_cause,
        "get_settings",
        lambda: make_settings(llm_root_cause_enabled=False),
    )

    result = root_cause.root_cause_node(
        {
            "user_task": "Fix auth refresh bug",
            "evidence": sample_evidence(),
        }
    )

    assert "Potential root cause for task 'Fix auth refresh bug'" in result["root_cause"]
    assert "src/AuthContext.tsx:2-4" in result["root_cause"]
    assert "root_cause_analysis" not in result


def test_llm_disabled_does_not_require_openai_api_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        root_cause,
        "get_settings",
        lambda: make_settings(
            llm_root_cause_enabled=False,
            openai_api_key=None,
        ),
    )

    result = root_cause.root_cause_node(
        {
            "user_task": "Find root cause",
            "evidence": [],
        }
    )

    assert result["root_cause"] == (
        "No root cause identified yet for task 'Find root cause'. "
        "No evidence was collected from code search results."
    )


def test_root_cause_node_uses_mocked_llm_analysis(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        root_cause,
        "get_settings",
        lambda: make_settings(
            llm_root_cause_enabled=True,
            openai_api_key="test-key",
        ),
    )
    monkeypatch.setattr(
        root_cause,
        "analyze_root_cause",
        lambda *args, **kwargs: RootCauseAnalysis(
            summary="Token restoration is missing during initialization.",
            root_cause="AuthContext initializes token state to null instead of restoring localStorage.",
            confidence="medium",
            evidence_refs=["src/AuthContext.tsx:2-4"],
            suspected_files=["src/AuthContext.tsx"],
            fix_strategy="Restore initial token state from localStorage during provider setup.",
            uncertainty=["The session refresh path is inferred from one file."],
            manual_checks=["Reload the page while authenticated."],
        ),
    )

    result = root_cause.root_cause_node(
        {
            "user_task": "Fix auth refresh bug",
            "expected_behavior": "User remains signed in after refresh.",
            "repo_scan": {"detected_stack": ["React"]},
            "evidence": sample_evidence(),
        }
    )

    assert result["root_cause"] == (
        "AuthContext initializes token state to null instead of restoring localStorage."
    )
    assert result["root_cause_analysis"]["confidence"] == "medium"
    assert result["root_cause_analysis"]["suspected_files"] == ["src/AuthContext.tsx"]


def test_invalid_llm_result_falls_back_safely(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        root_cause,
        "get_settings",
        lambda: make_settings(
            llm_root_cause_enabled=True,
            openai_api_key="test-key",
        ),
    )
    monkeypatch.setattr(root_cause, "analyze_root_cause", lambda *args, **kwargs: None)

    result = root_cause.root_cause_node(
        {
            "user_task": "Fix auth refresh bug",
            "evidence": sample_evidence(),
        }
    )

    assert "Potential root cause for task 'Fix auth refresh bug'" in result["root_cause"]
    assert "used deterministic fallback" in result["root_cause"]
    assert "root_cause_analysis" not in result


def test_reporter_includes_root_cause_analysis_fields() -> None:
    report = reporter.reporter_node(
        {
            "user_task": "Fix auth refresh bug",
            "root_cause": "legacy root cause",
            "root_cause_analysis": {
                "summary": "Token restoration is missing during initialization.",
                "root_cause": "AuthContext initializes token state to null instead of restoring localStorage.",
                "confidence": "medium",
                "evidence_refs": ["src/AuthContext.tsx:2-4"],
                "suspected_files": ["src/AuthContext.tsx"],
                "fix_strategy": "Restore token from localStorage at initialization.",
                "uncertainty": ["Only one evidence file was reviewed."],
                "manual_checks": ["Reload the page while signed in."],
            },
        }
    )["final_report"]

    assert "## Root Cause" in report
    assert "Summary: Token restoration is missing during initialization." in report
    assert "Confidence: medium" in report
    assert "Evidence References:" in report
    assert "- src/AuthContext.tsx:2-4" in report
    assert "Suspected Files:" in report
    assert "Fix Strategy: Restore token from localStorage at initialization." in report
    assert "Manual Checks:" in report


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


def test_service_filters_unknown_evidence_refs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    response_text = json.dumps(
        {
            "summary": "The token is not restored on load.",
            "root_cause": "AuthContext initializes token state to null.",
            "confidence": "medium",
            "evidence_refs": [
                "src/AuthContext.tsx:2-4",
                "src/Unknown.tsx:1-9",
            ],
            "suspected_files": [
                "src/AuthContext.tsx",
                "src/Unknown.tsx",
            ],
            "fix_strategy": "Restore token state from localStorage.",
            "uncertainty": [],
            "manual_checks": ["Reload while signed in."],
        }
    )
    monkeypatch.setattr(
        llm_provider,
        "_get_openai_client",
        lambda api_key, timeout_seconds: FakeClient(response_text),
    )

    result = llm_provider.analyze_root_cause(
        sample_evidence(),
        "Fix auth refresh bug",
        "User remains signed in after refresh.",
        "Detected stack: React",
        settings=make_settings(
            llm_root_cause_enabled=True,
            openai_api_key="test-key",
        ),
    )

    assert result is not None
    assert result.evidence_refs == ["src/AuthContext.tsx:2-4"]
    assert result.suspected_files == ["src/AuthContext.tsx"]


def test_service_invalid_output_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        llm_provider,
        "_get_openai_client",
        lambda api_key, timeout_seconds: FakeClient("{\"summary\": \"missing fields\"}"),
    )

    result = llm_provider.analyze_root_cause(
        sample_evidence(),
        "Fix auth refresh bug",
        "User remains signed in after refresh.",
        "Detected stack: React",
        settings=make_settings(
            llm_root_cause_enabled=True,
            openai_api_key="test-key",
        ),
    )

    assert result is None


def test_service_excludes_secret_like_snippets_from_prompt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capture: dict[str, object] = {}
    response_text = json.dumps(
        {
            "summary": "The token is not restored on load.",
            "root_cause": "AuthContext initializes token state to null.",
            "confidence": "medium",
            "evidence_refs": ["src/AuthContext.tsx:2-4"],
            "suspected_files": ["src/AuthContext.tsx"],
            "fix_strategy": "Restore token state from localStorage.",
            "uncertainty": [],
            "manual_checks": ["Reload while signed in."],
        }
    )
    monkeypatch.setattr(
        llm_provider,
        "_get_openai_client",
        lambda api_key, timeout_seconds: FakeClient(response_text, capture),
    )

    llm_provider.analyze_root_cause(
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
                "file_path": "config.py",
                "start_line": 1,
                "end_line": 1,
                "snippet": 'api_key = "super-secret"',
                "reason": "Should be excluded.",
            },
        ],
        "Fix auth refresh bug",
        "User remains signed in after refresh.",
        "Detected stack: React",
        settings=make_settings(
            llm_root_cause_enabled=True,
            openai_api_key="test-key",
        ),
    )

    messages = capture["messages"]
    assert isinstance(messages, list)
    prompt_payload = json.loads(messages[1]["content"])
    evidence_payload = prompt_payload["evidence"]
    assert len(evidence_payload) == 1
    assert evidence_payload[0]["file_path"] == "src/AuthContext.tsx"
    assert ".env" not in messages[1]["content"]
    assert "super-secret" not in messages[1]["content"]
