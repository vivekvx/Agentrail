from __future__ import annotations

from app.services.repo_map import build_module_graph

TREE = {
    "name": "demo",
    "type": "dir",
    "children": [
        {
            "name": "app",
            "type": "dir",
            "children": [
                {"name": "main.py", "type": "file", "lang": "Python"},
                {
                    "name": "api",
                    "type": "dir",
                    "children": [
                        {"name": "routes.py", "type": "file", "lang": "Python"},
                    ],
                },
            ],
        },
        {"name": "README.md", "type": "file", "lang": "Markdown"},
    ],
}


def test_build_module_graph_empty_tree_returns_empty() -> None:
    g = build_module_graph(None)
    assert g == {"nodes": [], "edges": []}


def test_root_node_aggregates_all_files_and_dominant_lang() -> None:
    g = build_module_graph(TREE)
    root = next(n for n in g["nodes"] if n["depth"] == 0)
    assert root["label"] == "demo"
    assert root["files"] == 3  # main.py + routes.py + README.md
    assert root["lang"] == "Python"  # 2 Python vs 1 Markdown


def test_directories_become_nodes_with_containment_edges() -> None:
    g = build_module_graph(TREE)
    ids = {n["id"] for n in g["nodes"]}
    assert "demo" in ids
    assert "demo/app" in ids
    assert "demo/app/api" in ids
    assert {"source": "demo", "target": "demo/app"} in g["edges"]
    assert {"source": "demo/app", "target": "demo/app/api"} in g["edges"]


def test_files_never_become_nodes() -> None:
    g = build_module_graph(TREE)
    labels = {n["label"] for n in g["nodes"]}
    assert "main.py" not in labels
    assert "routes.py" not in labels
    assert "README.md" not in labels


def test_module_file_count_is_recursive() -> None:
    g = build_module_graph(TREE)
    app_node = next(n for n in g["nodes"] if n["id"] == "demo/app")
    assert app_node["files"] == 2  # main.py + api/routes.py
