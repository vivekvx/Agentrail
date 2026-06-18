from __future__ import annotations

from collections import Counter

# How many directory levels of the tree become graph nodes. Beyond this the
# files still count toward an ancestor's totals, they just aren't drawn.
_MAX_DEPTH = 2


def _summarize(node: dict) -> tuple[int, Counter]:
    """Recursively count files and tally languages under a tree node."""
    files = 0
    langs: Counter[str] = Counter()
    for child in node.get("children", []):
        if child["type"] == "file":
            files += 1
            if child.get("lang"):
                langs[child["lang"]] += 1
        else:
            sub_files, sub_langs = _summarize(child)
            files += sub_files
            langs.update(sub_langs)
    return files, langs


def build_module_graph(tree: dict | None) -> dict:
    """Derive a module graph (nodes + containment edges) from a scan tree.

    Nodes are directories down to _MAX_DEPTH, each carrying a recursive file
    count and dominant language. Edges encode parent -> child containment.
    """
    nodes: list[dict] = []
    edges: list[dict] = []
    if not tree:
        return {"nodes": nodes, "edges": edges}

    root_files, root_langs = _summarize(tree)
    root_id = tree["name"] or "root"
    nodes.append(
        {
            "id": root_id,
            "label": tree["name"] or "root",
            "files": root_files,
            "lang": root_langs.most_common(1)[0][0] if root_langs else None,
            "depth": 0,
        }
    )

    def walk(node: dict, parent_id: str, depth: int) -> None:
        if depth >= _MAX_DEPTH:
            return
        for child in node.get("children", []):
            if child["type"] != "dir":
                continue
            files, langs = _summarize(child)
            node_id = f"{parent_id}/{child['name']}"
            nodes.append(
                {
                    "id": node_id,
                    "label": child["name"],
                    "files": files,
                    "lang": langs.most_common(1)[0][0] if langs else None,
                    "depth": depth + 1,
                }
            )
            edges.append({"source": parent_id, "target": node_id})
            walk(child, node_id, depth + 1)

    walk(tree, root_id, 0)
    return {"nodes": nodes, "edges": edges}
