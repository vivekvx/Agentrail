"use client";

import {
  ReactFlow,
  ReactFlowProvider,
  type NodeMouseHandler,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import { ArrowLeft, RefreshCcw } from "lucide-react";

import { getRun, getRunEvents } from "@/lib/api";
import {
  buildReactFlowEdges,
  buildReactFlowNodes,
  buildWorkflowViews,
} from "@/lib/agent-graph";
import { saveRecentRunId } from "@/lib/recent-runs";
import type { RunDetail, RunEvent } from "@/lib/types";
import { AgentGraphNode } from "@/components/agent-graph-node";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";

const nodeTypes: NodeTypes = {
  workflowNode: AgentGraphNode,
};

async function loadRunGraph(runId: number) {
  const [run, events] = await Promise.all([getRun(runId), getRunEvents(runId)]);
  saveRecentRunId(run.id);
  return { run, events };
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "No timestamp";
  }

  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function RunGraphShellInner({ runId }: { runId: number }) {
  const [run, setRun] = useState<RunDetail | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const next = await loadRunGraph(runId);
      setRun(next.run);
      setEvents(next.events);
    } catch (refreshError) {
      const message =
        refreshError instanceof Error
          ? refreshError.message
          : "Unable to load graph.";
      setError(message);
    }
  }, [runId]);

  useEffect(() => {
    queueMicrotask(() => {
      void refresh();
    });
  }, [refresh]);

  useEffect(() => {
    if (!run) {
      return;
    }

    if (run.status !== "running" && run.status !== "pending_approval") {
      return;
    }

    const interval = window.setInterval(() => {
      void refresh();
    }, 5000);

    return () => window.clearInterval(interval);
  }, [refresh, run]);

  const views = useMemo(() => {
    if (!run) {
      return [];
    }
    return buildWorkflowViews(run, events);
  }, [events, run]);

  const preferredView = useMemo(
    () =>
      views.find((view) => view.status === "running" || view.status === "failed") ??
      [...views].reverse().find((view) =>
        ["completed", "approved", "rejected"].includes(view.status),
      ) ??
      views[0] ??
      null,
    [views],
  );

  const highlightedNodeId = selectedNodeId || preferredView?.id || "";

  const nodes = useMemo(
    () => buildReactFlowNodes(views, highlightedNodeId),
    [highlightedNodeId, views],
  );
  const edges = useMemo(() => buildReactFlowEdges(views), [views]);

  const selectedView =
    views.find((view) => view.id === highlightedNodeId) ?? preferredView;

  const onNodeClick: NodeMouseHandler = useCallback((_, node) => {
    setSelectedNodeId(node.id);
  }, []);

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen w-full max-w-[1600px] flex-col px-5 py-6 sm:px-8">
        <header className="border-b border-border pb-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <Link
              className="inline-flex items-center gap-2 font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500 hover:text-zinc-200"
              href={run ? `/runs/${run.id}` : "/"}
            >
              <ArrowLeft className="size-3.5" />
              Back to run
            </Link>

            <Button onClick={() => void refresh()} variant="ghost">
              <RefreshCcw className="size-4" />
              Refresh
            </Button>
          </div>

          {run ? (
            <>
              <div className="mb-5 flex flex-wrap items-center gap-2">
                <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                  Run {run.id}
                </span>
                <StatusBadge status={run.status} />
                <RiskBadge
                  level={
                    typeof run.risk_score?.level === "string"
                      ? run.risk_score.level
                      : null
                  }
                />
              </div>

              <h1 className="max-w-4xl text-balance text-4xl font-semibold tracking-tight text-[#fafafa] sm:text-5xl">
                Agent execution graph
              </h1>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-zinc-500">
                A read-only visualizer for the LangGraph workflow. This is the
                execution artifact, not a workflow editor.
              </p>
            </>
          ) : (
            <h1 className="text-4xl font-semibold tracking-tight text-[#fafafa] sm:text-5xl">
              Agent execution graph
            </h1>
          )}
        </header>

        {error ? (
          <div className="mt-4 border border-border bg-surface px-4 py-3 text-sm text-zinc-300">
            {error}
          </div>
        ) : null}

        {!run || views.length === 0 ? (
          <div className="py-10 text-sm text-zinc-500">Loading graph…</div>
        ) : (
          <section className="grid flex-1 gap-8 pt-8 xl:grid-cols-[minmax(0,1fr)_320px]">
            <div className="min-w-0 border border-border bg-surface">
              <div className="border-b border-border px-5 py-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                  Execution graph
                </div>
                <p className="mt-2 text-sm leading-6 text-zinc-500">
                  The active node is highlighted. Completed nodes retain their
                  place as a historical record.
                </p>
              </div>

              <div className="h-[520px] w-full">
                <ReactFlow
                  defaultEdgeOptions={{ selectable: false, focusable: false }}
                  edges={edges}
                  fitView
                  fitViewOptions={{ padding: 0.16 }}
                  maxZoom={1}
                  minZoom={0.3}
                  nodes={nodes}
                  nodesConnectable={false}
                  nodesDraggable={false}
                  nodeTypes={nodeTypes}
                  onNodeClick={onNodeClick}
                  panOnDrag
                  proOptions={{ hideAttribution: true }}
                  selectionOnDrag={false}
                  zoomOnDoubleClick={false}
                />
              </div>
            </div>

            <aside className="border border-border bg-surface p-5 xl:sticky xl:top-6 xl:self-start">
              {selectedView ? (
                <>
                  <div className="mb-4 flex items-center justify-between gap-3">
                    <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                      Node {String(selectedView.order).padStart(2, "0")}
                    </div>
                    <div className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-zinc-300">
                      {selectedView.status}
                    </div>
                  </div>

                  <h2 className="text-xl font-semibold tracking-tight text-[#fafafa]">
                    {selectedView.title}
                  </h2>

                  <div className="mt-5 space-y-5">
                    <div className="border-t border-border pt-5">
                      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Node name
                      </div>
                      <p className="mt-2 font-mono text-xs uppercase tracking-[0.16em] text-zinc-300">
                        {selectedView.id}
                      </p>
                    </div>

                    <div className="border-t border-border pt-5">
                      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Purpose
                      </div>
                      <p className="mt-2 text-sm leading-7 text-zinc-300">
                        {selectedView.purpose}
                      </p>
                    </div>

                    <div className="border-t border-border pt-5">
                      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Output summary
                      </div>
                      <p className="mt-2 text-sm leading-7 text-zinc-300">
                        {selectedView.summary}
                      </p>
                    </div>

                    <div className="border-t border-border pt-5">
                      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                        Timestamp
                      </div>
                      <p className="mt-2 text-sm text-zinc-300">
                        {formatTimestamp(selectedView.timestamp)}
                      </p>
                    </div>
                  </div>
                </>
              ) : (
                <p className="text-sm text-zinc-500">Select a node to inspect it.</p>
              )}
            </aside>
          </section>
        )}
      </div>
    </main>
  );
}

export function RunGraphShell({ runId }: { runId: number }) {
  return (
    <ReactFlowProvider>
      <RunGraphShellInner runId={runId} />
    </ReactFlowProvider>
  );
}
