from __future__ import annotations

from pathlib import Path

from app.agents.nodes import patch_generator as pg
from app.core.config import Settings
from app.services.llm_provider import PatchProposal


def _settings(**overrides: object) -> Settings:
    return Settings(_env_file=None, **overrides)


def test_valid_syntax_accepts_good_python() -> None:
    assert pg._valid_syntax("a.py", "def f():\n    return 1\n")


def test_valid_syntax_rejects_broken_python() -> None:
    assert not pg._valid_syntax("a.py", "def f(:\n")


def test_valid_syntax_rejects_unbalanced_braces_in_ts() -> None:
    assert not pg._valid_syntax("a.ts", "function f() { return 1;\n")


def test_valid_syntax_passes_unknown_extensions() -> None:
    assert pg._valid_syntax("notes.txt", "anything {{{ goes")


def test_llm_patch_disabled_returns_empty(monkeypatch) -> None:
    monkeypatch.setattr(pg, "get_settings", lambda: _settings())
    result = pg._llm_diff_from_fix_strategy(
        {"target_files": ["a.py"]}, [], None, {}
    )
    assert result == ""


def test_llm_patch_produces_real_diff(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "calc.py"
    source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")

    monkeypatch.setattr(
        pg, "get_settings", lambda: _settings(llm_patch_enabled=True)
    )
    monkeypatch.setattr(
        pg,
        "generate_patch_code",
        lambda *args, **kwargs: PatchProposal(
            new_code="def add(a, b):\n    return a + b\n",
            explanation="Use addition instead of subtraction.",
            confidence="high",
        ),
    )

    evidence = [
        {"file_path": "calc.py", "start_line": 1, "end_line": 2, "snippet": "return a - b"}
    ]
    diff = pg._llm_diff_from_fix_strategy(
        {"target_files": ["calc.py"]},
        evidence,
        str(tmp_path),
        {"user_task": "fix add", "root_cause": "subtraction bug"},
    )

    assert "--- a/calc.py" in diff
    assert "+++ b/calc.py" in diff
    assert "-    return a - b" in diff
    assert "+    return a + b" in diff


def test_llm_patch_rejects_invalid_syntax(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "calc.py"
    source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")

    monkeypatch.setattr(
        pg, "get_settings", lambda: _settings(llm_patch_enabled=True)
    )
    monkeypatch.setattr(
        pg,
        "generate_patch_code",
        lambda *args, **kwargs: PatchProposal(
            new_code="def add(a, b:\n    return a + b\n",
            explanation="broken output",
            confidence="low",
        ),
    )

    evidence = [
        {"file_path": "calc.py", "start_line": 1, "end_line": 2, "snippet": "return a - b"}
    ]
    diff = pg._llm_diff_from_fix_strategy(
        {"target_files": ["calc.py"]},
        evidence,
        str(tmp_path),
        {"user_task": "fix add", "root_cause": "subtraction bug"},
    )
    assert diff == ""


def test_node_reports_patch_mode_llm(tmp_path: Path, monkeypatch) -> None:
    source = tmp_path / "calc.py"
    source.write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")

    monkeypatch.setattr(
        pg, "get_settings", lambda: _settings(llm_patch_enabled=True)
    )
    monkeypatch.setattr(
        pg,
        "generate_patch_code",
        lambda *args, **kwargs: PatchProposal(
            new_code="def add(a, b):\n    return a + b\n",
            explanation="fix",
            confidence="high",
        ),
    )

    state = {
        "repo_path": str(tmp_path),
        "user_task": "fix add",
        "root_cause": "subtraction bug",
        "fix_strategy": {"target_files": ["calc.py"], "change_plan": ["use +"]},
        "evidence": [
            {
                "file_path": "calc.py",
                "start_line": 1,
                "end_line": 2,
                "snippet": "return a - b",
            }
        ],
    }
    result = pg.patch_generator_node(state)
    assert result["patch_mode"] == "llm"
    assert "+    return a + b" in result["patch_diff"]


def test_auto_enable_llm_flags_when_key_present() -> None:
    s = Settings(_env_file=None, openai_api_key="sk-test-123")
    assert s.llm_root_cause_enabled
    assert s.llm_fix_strategy_enabled
    assert s.llm_patch_enabled


def test_explicit_false_wins_over_auto_enable() -> None:
    s = Settings(
        _env_file=None,
        openai_api_key="sk-test-123",
        llm_patch_enabled=False,
    )
    assert not s.llm_patch_enabled
    assert s.llm_root_cause_enabled


def test_no_key_keeps_llm_disabled() -> None:
    s = Settings(_env_file=None)
    assert not s.llm_root_cause_enabled
    assert not s.llm_patch_enabled
