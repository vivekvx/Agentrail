from __future__ import annotations

from dataclasses import asdict

from app.agents.state import AgentRunState
from app.tools.search_tools import SearchResult, search_code


MAX_RESULTS_PER_QUERY = 5
MAX_TOTAL_RESULTS = 10


def code_search_node(state: AgentRunState) -> dict[str, object]:
    repo_path = state["repo_path"]
    plan = state.get("plan", {})
    search_queries = plan.get("search_queries", [])
    results: list[SearchResult] = []
    seen_locations: set[tuple[str, int, str]] = set()

    for query in search_queries:
        if not isinstance(query, str) or not query:
            continue
        for result in search_code(repo_path, query, max_results=MAX_RESULTS_PER_QUERY):
            key = (result.file_path, result.line_number, result.matched_line)
            if key in seen_locations:
                continue
            seen_locations.add(key)
            results.append(result)
            if len(results) >= MAX_TOTAL_RESULTS:
                return {"search_results": [asdict(item) for item in results]}

    return {
        "search_results": [asdict(item) for item in results],
    }
