from __future__ import annotations

from app.agents.state import AgentRunState


MAX_EVIDENCE_REFERENCES = 3


def root_cause_node(state: AgentRunState) -> dict[str, object]:
    user_task = state.get("user_task", "")
    evidence = _valid_evidence_items(state.get("evidence", []))
    if not evidence:
        return {
            "root_cause": (
                f"No root cause identified yet for task '{user_task}'. "
                "No evidence was collected from code search results."
            ),
        }

    references = [_reference(item) for item in evidence[:MAX_EVIDENCE_REFERENCES]]
    snippets = [_first_snippet_line(item) for item in evidence[:MAX_EVIDENCE_REFERENCES]]
    root_cause = (
        f"Potential root cause for task '{user_task}' is located in "
        f"{'; '.join(references)}. Evidence snippets: {' | '.join(snippets)}."
    )
    return {"root_cause": root_cause}


def _valid_evidence_items(evidence: list[dict[str, object]]) -> list[dict[str, object]]:
    valid_items: list[dict[str, object]] = []
    for item in evidence:
        if not isinstance(item.get("file_path"), str):
            continue
        if not isinstance(item.get("start_line"), int):
            continue
        if not isinstance(item.get("end_line"), int):
            continue
        if not isinstance(item.get("snippet"), str):
            continue
        valid_items.append(item)
    return valid_items


def _reference(evidence_item: dict[str, object]) -> str:
    return (
        f"{evidence_item['file_path']}:"
        f"{evidence_item['start_line']}-{evidence_item['end_line']}"
    )


def _first_snippet_line(evidence_item: dict[str, object]) -> str:
    snippet = str(evidence_item["snippet"])
    first_line = snippet.splitlines()[0] if snippet else ""
    return first_line.strip()
