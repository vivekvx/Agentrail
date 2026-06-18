"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  ReactFlow,
  type Edge,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { getRepoMap, type RepoMap } from "@/lib/api";

const LANG_COLOR: Record<string, string> = {
  Python: "#3b82f6",
  TypeScript: "#0ea5e9",
  JavaScript: "#eab308",
  Go: "#22d3ee",
  Rust: "#f97316",
  Java: "#ef4444",
  Ruby: "#e11d48",
  CSS: "#a855f7",
  HTML: "#fb7185",
  Markdown: "#64748b",
};

function colorFor(lang: string | null): string {
  return (lang && LANG_COLOR[lang]) || "#34d399";
}

function layout(map: RepoMap): { nodes: Node[]; edges: Edge[] } {
  // Column per depth; stack nodes within a depth vertically.
  const byDepth = new Map<number, string[]>();
  for (const n of map.nodes) {
    const arr = byDepth.get(n.depth) ?? [];
    arr.push(n.id);
    byDepth.set(n.depth, arr);
  }

  const nodes: Node[] = map.nodes.map((n) => {
    const col = byDepth.get(n.depth) ?? [];
    const row = col.indexOf(n.id);
    const color = colorFor(n.lang);
    return {
      id: n.id,
      position: { x: n.depth * 300, y: row * 96 },
      data: {
        label: `${n.label}  ·  ${n.files} files${n.lang ? `  ·  ${n.lang}` : ""}`,
      },
      style: {
        background: "var(--surface-card)",
        color: "var(--ink)",
        border: `1px solid ${color}`,
        borderLeft: `3px solid ${color}`,
        borderRadius: 10,
        padding: "8px 14px",
        fontSize: 13,
        fontFamily: "var(--font-mono)",
        width: 220,
      },
    };
  });

  const edges: Edge[] = map.edges.map((e, i) => ({
    id: `e${i}`,
    source: e.source,
    target: e.target,
    style: { stroke: "var(--hairline)" },
  }));

  return { nodes, edges };
}

export function CodebaseMap({ repoId }: { repoId: string }) {
  const [map, setMap] = useState<RepoMap | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getRepoMap(repoId)
      .then(setMap)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load map"));
  }, [repoId]);

  const flow = useMemo(() => (map ? layout(map) : null), [map]);

  if (error) {
    return (
      <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-6 font-mono text-[13px] text-[#f87171]">
        {error}
      </div>
    );
  }
  if (!flow) {
    return (
      <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-6 font-mono text-[13px] text-[var(--muted)]">
        building map…
      </div>
    );
  }
  if (flow.nodes.length === 0) {
    return (
      <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-6 font-mono text-[13px] text-[var(--muted)]">
        No modules to map.
      </div>
    );
  }

  return (
    <div className="h-[520px] overflow-hidden rounded-xl border border-[var(--hairline)] bg-[var(--canvas)]">
      <ReactFlow
        nodes={flow.nodes}
        edges={flow.edges}
        fitView
        proOptions={{ hideAttribution: true }}
        nodesConnectable={false}
      >
        <Background color="var(--hairline)" gap={20} />
        <Controls showInteractive={false} />
      </ReactFlow>
    </div>
  );
}
