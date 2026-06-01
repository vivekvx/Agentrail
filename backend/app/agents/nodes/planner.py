from __future__ import annotations

import re

from app.agents.state import AgentRunState


MAX_SEARCH_QUERIES = 5


def planner_node(state: AgentRunState) -> dict[str, object]:
    user_task = state.get("user_task", "")
    search_queries = _search_queries(user_task)
    return {
        "plan": {
            "summary": "Inspect the repository, identify relevant files, then search for task terms.",
            "search_queries": search_queries,
        },
    }


def _search_queries(user_task: str) -> list[str]:
    terms = re.findall(r"[A-Za-z0-9_]+", user_task.lower())
    unique_terms: list[str] = []
    for term in terms:
        if term not in unique_terms:
            unique_terms.append(term)
        if len(unique_terms) >= MAX_SEARCH_QUERIES:
            break
    return unique_terms
