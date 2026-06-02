import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";

import type { WorkflowGraphNodeData, WorkflowNodeStatus } from "@/lib/agent-graph";

type WorkflowGraphNode = Node<WorkflowGraphNodeData>;

const statusLabel: Record<WorkflowNodeStatus, string> = {
  pending: "Pending",
  running: "Running",
  completed: "Completed",
  approved: "Approved",
  rejected: "Rejected",
  failed: "Failed",
};

const statusClasses: Record<WorkflowNodeStatus, string> = {
  pending: "border-border bg-surface text-zinc-600",
  running: "border-zinc-500 bg-[#151515] text-zinc-100",
  completed: "border-zinc-700 bg-[#131313] text-zinc-200",
  approved: "border-zinc-300 bg-[#141414] text-zinc-100",
  rejected: "border-zinc-400 bg-[#151515] text-zinc-100",
  failed: "border-zinc-500 bg-[#161616] text-zinc-100",
};

export function AgentGraphNode({
  data,
  selected,
}: NodeProps<WorkflowGraphNode>) {
  return (
    <div
      className={`w-[168px] border bg-surface p-3.5 transition-colors ${selected || data.isSelected ? "border-zinc-300" : "border-border"}`}
    >
      <Handle
        id="target"
        isConnectable={false}
        position={Position.Left}
        style={{ opacity: 0 }}
        type="target"
      />

      <div className="mb-3 flex items-start justify-between gap-3">
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
          {String(data.order).padStart(2, "0")}
        </div>
        <div className={`rounded-sm border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] ${statusClasses[data.status]}`}>
          {statusLabel[data.status]}
        </div>
      </div>

      <div>
        <div className="text-sm font-medium text-zinc-100">{data.title}</div>
        <div className="mt-2 font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
          {data.subtitle}
        </div>
      </div>

      <Handle
        id="source"
        isConnectable={false}
        position={Position.Right}
        style={{ opacity: 0 }}
        type="source"
      />
    </div>
  );
}
