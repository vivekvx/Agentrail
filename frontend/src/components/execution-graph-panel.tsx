"use client";

import {
  ReactFlow,
  useNodesInitialized,
  useReactFlow,
  type NodeMouseHandler,
  type NodeTypes,
} from "@xyflow/react";
import { useEffect } from "react";

import {
  buildReactFlowEdges,
  buildReactFlowNodes,
  buildWorkflowViews,
  getPreferredWorkflowNodeId,
  type WorkflowGraphVariant,
} from "@/lib/agent-graph";
import type { RunDetail, RunEvent } from "@/lib/types";
import { AgentGraphNode } from "@/components/agent-graph-node";

const nodeTypes: NodeTypes = {
  workflowNode: AgentGraphNode,
};

function graphZoomBounds(variant: WorkflowGraphVariant) {
  return variant === "full"
    ? { minZoom: 0.45, maxZoom: 1.15, padding: 0.12 }
    : { minZoom: 0.24, maxZoom: 1, padding: 0.14 };
}

function FitWorkflowView({
  variant,
  dependencyKey,
}: {
  variant: WorkflowGraphVariant;
  dependencyKey: string;
}) {
  const { fitView } = useReactFlow();
  const nodesInitialized = useNodesInitialized();
  const zoomBounds = graphZoomBounds(variant);

  useEffect(() => {
    if (!nodesInitialized) {
      return;
    }

    queueMicrotask(() => {
      void fitView({
        duration: 0,
        maxZoom: zoomBounds.maxZoom,
        minZoom: zoomBounds.minZoom,
        padding: zoomBounds.padding,
      });
    });
  }, [dependencyKey, fitView, nodesInitialized, zoomBounds.maxZoom, zoomBounds.minZoom, zoomBounds.padding]);

  return null;
}

function formatTimestamp(value: string | null) {
  if (!value) {
    return "No timestamp yet";
  }

  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function ExecutionGraphPanel({
  run,
  events,
  selectedNodeId,
  onNodeSelect,
  variant,
  title,
  description,
  showInspector = true,
}: {
  run: RunDetail;
  events: RunEvent[];
  selectedNodeId: string;
  onNodeSelect: (nodeId: string) => void;
  variant: WorkflowGraphVariant;
  title: string;
  description?: string;
  showInspector?: boolean;
}) {
  const views = buildWorkflowViews(run, events);
  const highlightedNodeId = selectedNodeId || getPreferredWorkflowNodeId(views);
  const nodes = buildReactFlowNodes(views, highlightedNodeId, variant);
  const edges = buildReactFlowEdges(views);
  const selectedView =
    views.find((view) => view.id === highlightedNodeId) ??
    views.find((view) => view.order === 1) ??
    null;
  const fitDependencyKey = `${variant}:${highlightedNodeId}:${events.length}:${run.status}:${run.approval_status ?? ""}`;
  const zoomBounds = graphZoomBounds(variant);

  const onNodeClick: NodeMouseHandler = (_, node) => {
    onNodeSelect(node.id);
  };

  return (
    <section className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <div className="min-w-0 border border-border bg-surface">
        <div className="border-b border-border px-5 py-4">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Execution graph
          </div>
          <h2 className="mt-3 text-xl font-semibold tracking-tight text-[#fafafa]">
            {title}
          </h2>
          {description ? (
            <p className="mt-2 text-sm leading-6 text-zinc-500">{description}</p>
          ) : null}
        </div>

        <div
          className={variant === "full" ? "h-[540px] w-full" : "h-[360px] w-full"}
        >
          <ReactFlow
            defaultEdgeOptions={{ selectable: false, focusable: false }}
            edges={edges}
            maxZoom={zoomBounds.maxZoom}
            minZoom={zoomBounds.minZoom}
            nodes={nodes}
            nodesConnectable={false}
            nodesDraggable={false}
            nodeTypes={nodeTypes}
            onNodeClick={onNodeClick}
            panOnDrag
            proOptions={{ hideAttribution: true }}
            selectionOnDrag={false}
            zoomOnDoubleClick={false}
          >
            <FitWorkflowView
              dependencyKey={fitDependencyKey}
              variant={variant}
            />
          </ReactFlow>
        </div>
      </div>

      {showInspector ? (
        <aside className="border border-border bg-surface p-5 xl:sticky xl:top-6 xl:self-start">
          {selectedView ? (
            <>
              <div className="mb-4 flex items-center justify-between gap-3">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                  Node {String(selectedView.order).padStart(2, "0")}
                </div>
                <div className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-zinc-300">
                  {selectedView.isSkipped ? "Skipped" : selectedView.status}
                </div>
              </div>

              <h3 className="text-xl font-semibold tracking-tight text-[#fafafa]">
                {selectedView.title}
              </h3>

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
          ) : null}
        </aside>
      ) : null}
    </section>
  );
}
