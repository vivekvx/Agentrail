from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import Settings, get_settings


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
MAX_EVIDENCE_ITEMS = 6
MAX_SNIPPET_CHARS = 500
MAX_TOTAL_SNIPPET_CHARS = 2_400
SECRET_FILE_PATTERN = re.compile(r"(^|/)(\.env(\..+)?|secrets\..+|.+\.(pem|key))$", re.IGNORECASE)
SECRET_SNIPPET_PATTERNS = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\bapi[_-]?key\s*[:=]", re.IGNORECASE),
    re.compile(r"\bsecret(_key)?\s*[:=]", re.IGNORECASE),
    re.compile(r"\bpassword\s*[:=]", re.IGNORECASE),
    re.compile(r"\bauthorization\s*:\s*bearer\b", re.IGNORECASE),
)


class RootCauseAnalysis(BaseModel):
    summary: str = Field(min_length=1, max_length=1_000)
    root_cause: str = Field(min_length=1, max_length=4_000)
    confidence: Literal["low", "medium", "high"]
    evidence_refs: list[str] = Field(default_factory=list, max_length=12)
    suspected_files: list[str] = Field(default_factory=list, max_length=12)
    fix_strategy: str = Field(min_length=1, max_length=1_500)
    uncertainty: list[str] = Field(default_factory=list, max_length=12)
    manual_checks: list[str] = Field(default_factory=list, max_length=12)

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class FixStrategy(BaseModel):
    summary: str = Field(min_length=1, max_length=1_000)
    target_files: list[str] = Field(default_factory=list, max_length=12)
    change_plan: list[str] = Field(default_factory=list, max_length=12)
    test_plan: list[str] = Field(default_factory=list, max_length=12)
    risks: list[str] = Field(default_factory=list, max_length=12)
    non_goals: list[str] = Field(default_factory=list, max_length=12)
    confidence: Literal["low", "medium", "high"]

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


@lru_cache(maxsize=4)
def _get_openai_client(
    api_key: str,
    timeout_seconds: int,
    base_url: str = "",
) -> object | None:
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    kwargs: dict[str, object] = {"api_key": api_key, "timeout": timeout_seconds}
    if base_url:
        # OpenRouter / any OpenAI-compatible endpoint.
        kwargs["base_url"] = base_url

    return OpenAI(**kwargs)


def _extract_json(content: str) -> str:
    """Best-effort extract a JSON object from model output.

    Free models often wrap JSON in markdown fences or add prose. Strip the
    fences and slice the outermost object so validation can succeed.
    """
    text = content.strip()
    if text.startswith("```"):
        # Drop the opening fence line (``` or ```json) and the closing fence.
        text = text.split("\n", 1)[-1] if "\n" in text else text
        if text.endswith("```"):
            text = text[: -3]
        text = text.strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text


def _complete_with_fallback(
    client: object,
    model: str,
    messages: list[dict[str, str]],
    schema_name: str,
    schema: dict[str, object],
) -> str:
    """Call the model, degrading response_format for wider model support.

    Order: strict json_schema -> json_object -> no format. Each step is tried
    on API error so models that reject a given format still produce output.
    """
    strict_format = {
        "type": "json_schema",
        "json_schema": {"name": schema_name, "strict": True, "schema": schema},
    }
    json_object_messages = messages + [
        {
            "role": "system",
            "content": (
                "Respond with a single valid JSON object only. No markdown, "
                "no prose, no code fences. It must match this JSON schema: "
                + json.dumps(schema, ensure_ascii=True)
            ),
        }
    ]

    attempts = (
        (messages, strict_format),
        (json_object_messages, {"type": "json_object"}),
        (json_object_messages, None),
    )

    for attempt_messages, response_format in attempts:
        try:
            kwargs: dict[str, object] = {
                "model": model,
                "messages": attempt_messages,
            }
            if response_format is not None:
                kwargs["response_format"] = response_format
            response = client.chat.completions.create(**kwargs)
            content = _response_text(response)
            if content:
                return content
        except (AttributeError, TypeError):
            # Stubbed/invalid client shape — no point retrying other formats.
            raise
        except Exception:
            continue

    return ""


def analyze_root_cause(
    evidence: list[dict[str, object]],
    user_task: str,
    expected_behavior: str,
    repo_summary: str,
    *,
    settings: Settings | None = None,
) -> RootCauseAnalysis | None:
    active_settings = settings or get_settings()
    if not active_settings.llm_root_cause_enabled:
        return None

    client = _get_openai_client(
        (active_settings.openai_api_key or "").strip(),
        active_settings.llm_timeout_seconds,
        (active_settings.openai_base_url or "").strip(),
    )
    if client is None:
        return None

    prepared = prepare_evidence_for_llm(evidence)
    messages = _messages(
        evidence=prepared["evidence"],
        user_task=user_task,
        expected_behavior=expected_behavior,
        repo_summary=repo_summary,
    )
    model = (
        active_settings.openai_model or DEFAULT_OPENAI_MODEL
    ).strip() or DEFAULT_OPENAI_MODEL

    try:
        content = _complete_with_fallback(
            client,
            model,
            messages,
            "root_cause_analysis",
            RootCauseAnalysis.model_json_schema(),
        )
        if not content:
            return None
        parsed = RootCauseAnalysis.model_validate_json(_extract_json(content))
    except (AttributeError, TypeError, ValidationError, json.JSONDecodeError, ValueError):
        return None
    except Exception:
        return None

    return _filter_analysis(parsed, prepared["allowed_refs"], prepared["allowed_files"])


def propose_fix_strategy(
    evidence: list[dict[str, object]],
    user_task: str,
    expected_behavior: str,
    repo_summary: str,
    root_cause: str,
    root_cause_analysis: dict[str, object] | None = None,
    *,
    settings: Settings | None = None,
) -> FixStrategy | None:
    active_settings = settings or get_settings()
    if not active_settings.llm_fix_strategy_enabled:
        return None

    client = _get_openai_client(
        (active_settings.openai_api_key or "").strip(),
        active_settings.llm_timeout_seconds,
        (active_settings.openai_base_url or "").strip(),
    )
    if client is None:
        return None

    prepared = prepare_evidence_for_llm(evidence)
    if not prepared["evidence"]:
        return None

    messages = _fix_strategy_messages(
        evidence=prepared["evidence"],
        user_task=user_task,
        expected_behavior=expected_behavior,
        repo_summary=repo_summary,
        root_cause=root_cause,
        root_cause_analysis=root_cause_analysis,
    )
    model = (
        active_settings.openai_model or DEFAULT_OPENAI_MODEL
    ).strip() or DEFAULT_OPENAI_MODEL

    try:
        content = _complete_with_fallback(
            client,
            model,
            messages,
            "fix_strategy",
            FixStrategy.model_json_schema(),
        )
        if not content:
            return None
        parsed = FixStrategy.model_validate_json(_extract_json(content))
    except (AttributeError, TypeError, ValidationError, json.JSONDecodeError, ValueError):
        return None
    except Exception:
        return None

    return _filter_fix_strategy(parsed, prepared["allowed_files"])


def prepare_evidence_for_llm(
    evidence: list[dict[str, object]],
) -> dict[str, list[object] | set[str]]:
    prepared: list[dict[str, str]] = []
    allowed_refs: set[str] = set()
    allowed_files: set[str] = set()
    total_snippet_chars = 0

    for item in evidence:
        if len(prepared) >= MAX_EVIDENCE_ITEMS:
            break

        file_path = item.get("file_path")
        start_line = item.get("start_line")
        end_line = item.get("end_line")
        snippet = item.get("snippet")
        reason = item.get("reason")

        if not isinstance(file_path, str) or not file_path:
            continue
        if not isinstance(start_line, int) or not isinstance(end_line, int):
            continue
        if not isinstance(snippet, str) or not snippet.strip():
            continue
        if SECRET_FILE_PATTERN.search(file_path):
            continue

        normalized_snippet = _truncate(snippet.strip(), MAX_SNIPPET_CHARS)
        if _looks_secret(normalized_snippet):
            continue
        normalized_reason = (
            str(reason).strip()
            if isinstance(reason, str) and reason.strip()
            else ""
        )
        if normalized_reason and _looks_secret(normalized_reason):
            normalized_reason = ""

        if total_snippet_chars >= MAX_TOTAL_SNIPPET_CHARS:
            break

        available_chars = MAX_TOTAL_SNIPPET_CHARS - total_snippet_chars
        normalized_snippet = _truncate(normalized_snippet, available_chars)
        if not normalized_snippet:
            break

        total_snippet_chars += len(normalized_snippet)
        reference = f"{file_path}:{start_line}-{end_line}"
        prepared_item = {
            "reference": reference,
            "file_path": file_path,
            "reason": normalized_reason,
            "snippet": normalized_snippet,
        }
        prepared.append(prepared_item)
        allowed_refs.add(reference)
        allowed_files.add(file_path)

    return {
        "evidence": prepared,
        "allowed_refs": allowed_refs,
        "allowed_files": allowed_files,
    }


def _messages(
    *,
    evidence: list[dict[str, str]],
    user_task: str,
    expected_behavior: str,
    repo_summary: str,
) -> list[dict[str, str]]:
    instructions = (
        "You are Agentrail's root cause analyzer. "
        "Use only the provided evidence. "
        "Do not invent file paths, evidence references, test outcomes, or patch correctness. "
        "If the evidence is insufficient, say so explicitly in summary, uncertainty, and manual checks. "
        "Do not request command execution. "
        "Do not include or infer secrets."
    )
    payload = {
        "user_task": user_task,
        "expected_behavior": expected_behavior,
        "repo_summary": repo_summary,
        "evidence": evidence,
    }
    return [
        {"role": "system", "content": instructions},
        {
            "role": "user",
            "content": json.dumps(payload, ensure_ascii=True),
        },
    ]


def _fix_strategy_messages(
    *,
    evidence: list[dict[str, str]],
    user_task: str,
    expected_behavior: str,
    repo_summary: str,
    root_cause: str,
    root_cause_analysis: dict[str, object] | None,
) -> list[dict[str, str]]:
    instructions = (
        "You are Agentrail's fix strategy advisor. "
        "Use only the provided evidence and root cause context. "
        "Do not invent file paths. target_files must be selected only from evidence file paths. "
        "Do not write code. Do not generate a diff. "
        "Do not claim the patch is correct. Do not claim tests passed. "
        "If evidence is weak, say so. Include practical manual checks in test_plan when confidence is low. "
        "Treat auth, token, session, password, JWT, permission, CORS, secret, and config changes as sensitive."
    )
    payload = {
        "user_task": user_task,
        "expected_behavior": expected_behavior,
        "repo_summary": repo_summary,
        "root_cause": root_cause,
        "root_cause_analysis": root_cause_analysis,
        "evidence": evidence,
    }
    return [
        {"role": "system", "content": instructions},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=True)},
    ]


def _response_text(response: object) -> str:
    output_text = getattr(response, "output_text", None)
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    choices = getattr(response, "choices", None)
    if not isinstance(choices, list) or not choices:
        return ""

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            text = getattr(item, "text", None)
            if isinstance(text, str):
                parts.append(text)
                continue
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        return "".join(parts)
    return ""


def _filter_analysis(
    analysis: RootCauseAnalysis,
    allowed_refs: set[str],
    allowed_files: set[str],
) -> RootCauseAnalysis:
    filtered = analysis.model_copy(
        update={
            "evidence_refs": [
                reference
                for reference in analysis.evidence_refs
                if reference in allowed_refs
            ],
            "suspected_files": [
                file_path
                for file_path in analysis.suspected_files
                if file_path in allowed_files
            ],
        },
    )
    return filtered


def _filter_fix_strategy(
    strategy: FixStrategy,
    allowed_files: set[str],
) -> FixStrategy:
    return strategy.model_copy(
        update={
            "target_files": [
                file_path
                for file_path in strategy.target_files
                if file_path in allowed_files
            ]
        }
    )


def _truncate(value: str, limit: int) -> str:
    if limit <= 0:
        return ""
    if len(value) <= limit:
        return value
    if limit <= 16:
        return value[:limit]
    return value[: limit - 12].rstrip() + " [truncated]"


def _looks_secret(snippet: str) -> bool:
    return any(pattern.search(snippet) for pattern in SECRET_SNIPPET_PATTERNS)
