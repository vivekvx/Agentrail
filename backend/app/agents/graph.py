from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.nodes.approval import approval_node
from app.agents.nodes.code_search import code_search_node
from app.agents.nodes.evidence_reader import evidence_reader_node
from app.agents.nodes.patch_generator import patch_generator_node
from app.agents.nodes.planner import planner_node
from app.agents.nodes.reporter import reporter_node
from app.agents.nodes.repo_scanner import repo_scanner_node
from app.agents.nodes.root_cause import root_cause_node
from app.agents.nodes.test_runner import test_runner_node
from app.agents.nodes.verifier import verifier_node
from app.agents.state import AgentRunState


DEFAULT_CHECKPOINTER = InMemorySaver()


def build_agent_graph(checkpointer=DEFAULT_CHECKPOINTER):
    graph = StateGraph(AgentRunState)
    graph.add_node("planner", planner_node)
    graph.add_node("repo_scanner", repo_scanner_node)
    graph.add_node("code_search", code_search_node)
    graph.add_node("evidence_reader", evidence_reader_node)
    graph.add_node("root_cause", root_cause_node)
    graph.add_node("patch_generator", patch_generator_node)
    graph.add_node("approval_node", approval_node)
    graph.add_node("test_runner", test_runner_node)
    graph.add_node("verifier", verifier_node)
    graph.add_node("reporter", reporter_node)
    graph.add_edge(START, "planner")
    graph.add_edge("planner", "repo_scanner")
    graph.add_edge("repo_scanner", "code_search")
    graph.add_edge("code_search", "evidence_reader")
    graph.add_edge("evidence_reader", "root_cause")
    graph.add_edge("root_cause", "patch_generator")
    graph.add_edge("patch_generator", "approval_node")
    graph.add_edge("approval_node", "test_runner")
    graph.add_edge("test_runner", "verifier")
    graph.add_edge("verifier", "reporter")
    graph.add_edge("reporter", END)
    return graph.compile(checkpointer=checkpointer)
