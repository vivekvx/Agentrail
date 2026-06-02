import type { Edge, Node } from "@xyflow/react";

import type { JsonObject, RunDetail, RunEvent } from "@/lib/types";

export type WorkflowNodeStatus =
  | "pending"
  | "running"
  | "completed"
  | "approved"
  | "rejected"
  | "failed";

export type WorkflowGraphVariant = "compact" | "full";

export interface WorkflowNodeDefinition {
  id: string;
  order: number;
  title: string;
  shortTitle: string;
  purpose: string;
  eventTypes: string[];
  backendNodes?: string[];
}

export type WorkflowGraphNodeData = Record<string, unknown> & {
  id: string;
  title: string;
  order: number;
  status: WorkflowNodeStatus;
  subtitle: string;
  isSelected: boolean;
  isSkipped: boolean;
  variant: WorkflowGraphVariant;
};

export interface WorkflowNodeView {
  id: string;
  order: number;
  title: string;
  shortTitle: string;
  purpose: string;
  status: WorkflowNodeStatus;
  timestamp: string | null;
  summary: string;
  eventIds: number[];
  isSkipped: boolean;
}

export const EVENT_TYPE_TO_NODE_ID: Record<string, string> = {
  run_created: "planner",
  run_started: "planner",
  repo_scanned: "repo_scanner",
  code_searched: "code_search",
  evidence_read: "evidence_reader",
  root_cause_generated: "root_cause",
  patch_generated: "patch_generator",
  pending_approval: "approval",
  approved: "approval",
  rejected: "approval",
  tests_run: "test_runner",
  verified: "verifier",
  risk_scored: "risk_scorer",
  report_generated: "reporter",
  run_completed: "reporter",
  run_failed: "reporter",
};

const FULL_HORIZONTAL_GAP = 204;
const FULL_VERTICAL_GAP = 196;
const COMPACT_HORIZONTAL_GAP = 186;
const COMPACT_VERTICAL_GAP = 146;
const COMPACT_COLUMNS = 4;
const ROW_BREAK_ORDER = 6;

export const WORKFLOW_DEFINITIONS: WorkflowNodeDefinition[] = [
  {
    id: "planner",
    order: 1,
    title: "Planner",
    shortTitle: "Plan",
    purpose: "Builds the initial investigation plan and establishes the run path.",
    eventTypes: ["run_created", "run_started"],
    backendNodes: ["planner"],
  },
  {
    id: "repo_scanner",
    order: 2,
    title: "Repo Scanner",
    shortTitle: "Scan",
    purpose: "Detects stack, entry points, and likely repo structure.",
    eventTypes: ["repo_scanned"],
    backendNodes: ["repo_scanner"],
  },
  {
    id: "code_search",
    order: 3,
    title: "Code Search",
    shortTitle: "Search",
    purpose: "Searches the repository for evidence-bearing symbols and files.",
    eventTypes: ["code_searched"],
    backendNodes: ["code_search"],
  },
  {
    id: "evidence_reader",
    order: 4,
    title: "Evidence Reader",
    shortTitle: "Evidence",
    purpose: "Reads supporting files and snippets into structured evidence.",
    eventTypes: ["evidence_read"],
    backendNodes: ["evidence_reader"],
  },
  {
    id: "root_cause",
    order: 5,
    title: "Root Cause",
    shortTitle: "Cause",
    purpose: "Produces the deterministic root-cause statement from evidence.",
    eventTypes: ["root_cause_generated"],
    backendNodes: ["root_cause"],
  },
  {
    id: "patch_generator",
    order: 6,
    title: "Patch Generator",
    shortTitle: "Patch",
    purpose: "Builds a minimal unified diff preview for review.",
    eventTypes: ["patch_generated"],
    backendNodes: ["patch_generator"],
  },
  {
    id: "approval",
    order: 7,
    title: "Approval",
    shortTitle: "Approve",
    purpose: "Pauses the run for a human decision before verification proceeds.",
    eventTypes: ["pending_approval", "approved", "rejected"],
    backendNodes: ["approval_node"],
  },
  {
    id: "test_runner",
    order: 8,
    title: "Test Runner",
    shortTitle: "Test",
    purpose: "Runs the safe local verification command after approval.",
    eventTypes: ["tests_run"],
    backendNodes: ["test_runner"],
  },
  {
    id: "verifier",
    order: 9,
    title: "Verifier",
    shortTitle: "Verify",
    purpose: "Interprets approval, evidence, and test outcomes into verification state.",
    eventTypes: ["verified"],
    backendNodes: ["verifier"],
  },
  {
    id: "risk_scorer",
    order: 10,
    title: "Risk Scorer",
    shortTitle: "Risk",
    purpose: "Computes residual deployment risk from verification and patch scope.",
    eventTypes: ["risk_scored"],
    backendNodes: ["risk_scorer"],
  },
  {
    id: "reporter",
    order: 11,
    title: "Reporter",
    shortTitle: "Report",
    purpose: "Produces the final report artifact for review and handoff.",
    eventTypes: ["report_generated", "run_completed", "run_failed"],
    backendNodes: ["reporter"],
  },
];

export function getWorkflowNodeIdForEventType(eventType: string): string | null {
  return EVENT_TYPE_TO_NODE_ID[eventType] ?? null;
}

function mapBackendNodeToWorkflow(run: RunDetail): string | null {
  const currentNode = run.current_node;
  if (!currentNode) {
    if (run.status === "completed" || run.status === "rejected" || run.status === "failed") {
      return "reporter";
    }
    return null;
  }

  const found = WORKFLOW_DEFINITIONS.find((definition) =>
    definition.backendNodes?.includes(currentNode),
  );
  return found?.id ?? null;
}

function collectLatestEvents(events: RunEvent[]) {
  const latestByType = new Map<string, RunEvent>();

  for (const event of events) {
    latestByType.set(event.event_type, event);
  }

  return latestByType;
}

function collectEventIdsByNode(events: RunEvent[]) {
  const eventIdsByNode = new Map<string, number[]>();

  for (const event of events) {
    const nodeId = getWorkflowNodeIdForEventType(event.event_type);
    if (!nodeId) {
      continue;
    }

    const existing = eventIdsByNode.get(nodeId) ?? [];
    existing.push(event.id);
    eventIdsByNode.set(nodeId, existing);
  }

  return eventIdsByNode;
}

function inferFailedNodeId(
  run: RunDetail,
  events: RunEvent[],
  currentWorkflowNode: string | null,
): string | null {
  if (run.status !== "failed") {
    return null;
  }

  if (currentWorkflowNode) {
    return currentWorkflowNode;
  }

  for (let index = events.length - 1; index >= 0; index -= 1) {
    const nodeId = getWorkflowNodeIdForEventType(events[index].event_type);
    if (nodeId) {
      return nodeId;
    }
  }

  return "reporter";
}

function nodeTimestamp(definition: WorkflowNodeDefinition, latestByType: Map<string, RunEvent>) {
  const relevantEvents = definition.eventTypes
    .map((eventType) => latestByType.get(eventType))
    .filter((event): event is RunEvent => Boolean(event));

  if (relevantEvents.length === 0) {
    return null;
  }

  return relevantEvents[relevantEvents.length - 1].created_at;
}

function summarizeStack(payload: JsonObject | null) {
  const detected = Array.isArray(payload?.detected_stack)
    ? payload.detected_stack.filter((item): item is string => typeof item === "string")
    : [];

  if (detected.length === 0) {
    return "Stack detection completed.";
  }

  return `Detected ${detected.join(", ")}.`;
}

function summarizeNode(
  definition: WorkflowNodeDefinition,
  run: RunDetail,
  event: RunEvent | null,
  isSkipped: boolean,
): string {
  const payload = event?.payload ?? null;

  if (isSkipped) {
    return "Skipped after rejection.";
  }

  switch (definition.id) {
    case "planner":
      return "Investigation plan prepared.";
    case "repo_scanner":
      return summarizeStack(payload);
    case "code_search":
      return typeof payload?.match_count === "number"
        ? `${payload.match_count} search matches found.`
        : "Search completed.";
    case "evidence_reader":
      return typeof payload?.evidence_count === "number"
        ? `${payload.evidence_count} evidence item(s) captured.`
        : "Evidence captured.";
    case "root_cause":
      return event?.message ?? "Root cause generated.";
    case "patch_generator":
      return run.patch_diff ? "Patch preview generated." : "Patch preview pending.";
    case "approval":
      if (run.status === "rejected" || run.approval_status === "rejected") {
        return "Patch was rejected.";
      }
      if (run.approval_status === "approved") {
        return "Patch was approved.";
      }
      return "Waiting for approval.";
    case "test_runner":
      return typeof payload?.status === "string"
        ? `Verification command ${payload.status}.`
        : "Waiting for verification command.";
    case "verifier":
      return typeof payload?.summary === "string"
        ? payload.summary
        : "Verification has not run yet.";
    case "risk_scorer":
      if (typeof payload?.score === "number" && typeof payload?.level === "string") {
        return `Risk ${payload.level} (${payload.score}/100).`;
      }
      return "Risk score appears after verification.";
    case "reporter":
      if (run.status === "rejected" && run.final_report) {
        return "Rejection report generated.";
      }
      return run.final_report ? "Final report generated." : "Report pending.";
    default:
      return definition.purpose;
  }
}

function statusForNode(
  definition: WorkflowNodeDefinition,
  run: RunDetail,
  latestByType: Map<string, RunEvent>,
  currentWorkflowNode: string | null,
  failedNodeId: string | null,
  isSkipped: boolean,
): WorkflowNodeStatus {
  if (failedNodeId === definition.id) {
    return "failed";
  }

  if (definition.id === "approval") {
    if (
      run.status === "rejected" ||
      run.approval_status === "rejected" ||
      latestByType.has("rejected")
    ) {
      return "rejected";
    }
    if (run.approval_status === "approved" || latestByType.has("approved")) {
      return "approved";
    }
    if (
      run.status === "pending_approval" ||
      currentWorkflowNode === "approval" ||
      latestByType.has("pending_approval")
    ) {
      return "running";
    }
  }

  if (definition.id === "reporter") {
    if (
      run.final_report ||
      latestByType.has("report_generated") ||
      latestByType.has("run_completed") ||
      latestByType.has("run_failed")
    ) {
      return "completed";
    }
  }

  if (definition.id === "planner") {
    if (currentWorkflowNode === "planner" && latestByType.size === 0 && run.status === "running") {
      return "running";
    }

    if (latestByType.has("run_created") || latestByType.has("run_started") || currentWorkflowNode) {
      return "completed";
    }
  }

  if (definition.eventTypes.some((eventType) => latestByType.has(eventType))) {
    return "completed";
  }

  if (isSkipped) {
    return "pending";
  }

  if (currentWorkflowNode === definition.id && run.status !== "failed") {
    return "running";
  }

  return "pending";
}

function isSkippedAfterRejection(run: RunDetail, definition: WorkflowNodeDefinition) {
  if (run.status !== "rejected" && run.approval_status !== "rejected") {
    return false;
  }

  return (
    definition.order > 7 &&
    definition.id !== "reporter"
  );
}

export function getPreferredWorkflowNodeId(views: WorkflowNodeView[]) {
  return (
    views.find((view) => view.status === "running" || view.status === "failed")?.id ??
    [...views]
      .reverse()
      .find((view) =>
        ["completed", "approved", "rejected"].includes(view.status),
      )?.id ??
    views[0]?.id ??
    ""
  );
}

export function buildWorkflowViews(run: RunDetail, events: RunEvent[]): WorkflowNodeView[] {
  const latestByType = collectLatestEvents(events);
  const eventIdsByNode = collectEventIdsByNode(events);
  const currentWorkflowNode = mapBackendNodeToWorkflow(run);
  const failedNodeId = inferFailedNodeId(run, events, currentWorkflowNode);

  return WORKFLOW_DEFINITIONS.map((definition) => {
    const relevantEvent =
      definition.id === "approval"
        ? latestByType.get("rejected") ??
          latestByType.get("approved") ??
          latestByType.get("pending_approval") ??
          null
        : definition.id === "reporter"
          ? latestByType.get("report_generated") ??
            latestByType.get("run_completed") ??
            latestByType.get("run_failed") ??
            null
          : definition.eventTypes
              .map((eventType) => latestByType.get(eventType))
              .filter((event): event is RunEvent => Boolean(event))
              .at(-1) ?? null;

    const isSkipped = isSkippedAfterRejection(run, definition);

    return {
      id: definition.id,
      order: definition.order,
      title: definition.title,
      shortTitle: definition.shortTitle,
      purpose: definition.purpose,
      status: statusForNode(
        definition,
        run,
        latestByType,
        currentWorkflowNode,
        failedNodeId,
        isSkipped,
      ),
      timestamp: nodeTimestamp(definition, latestByType),
      summary: summarizeNode(definition, run, relevantEvent, isSkipped),
      eventIds: eventIdsByNode.get(definition.id) ?? [],
      isSkipped,
    };
  });
}

function nodePosition(order: number, variant: WorkflowGraphVariant) {
  if (variant === "compact") {
    const compactIndex = order - 1;
    return {
      x: (compactIndex % COMPACT_COLUMNS) * COMPACT_HORIZONTAL_GAP,
      y: Math.floor(compactIndex / COMPACT_COLUMNS) * COMPACT_VERTICAL_GAP,
    };
  }

  const row = order > ROW_BREAK_ORDER ? 1 : 0;
  const column = row === 0 ? order - 1 : order - (ROW_BREAK_ORDER + 1);

  return {
    x: column * FULL_HORIZONTAL_GAP,
    y: row * FULL_VERTICAL_GAP,
  };
}

export function buildReactFlowNodes(
  views: WorkflowNodeView[],
  selectedNodeId: string,
  variant: WorkflowGraphVariant,
): Node<WorkflowGraphNodeData>[] {
  return views.map((view) => ({
    id: view.id,
    type: "workflowNode",
    position: nodePosition(view.order, variant),
    draggable: false,
    selectable: true,
    data: {
      id: view.id,
      title: view.title,
      order: view.order,
      status: view.status,
      subtitle: view.id.replaceAll("_", " "),
      isSelected: view.id === selectedNodeId,
      isSkipped: view.isSkipped,
      variant,
    },
  }));
}

export function buildReactFlowEdges(views: WorkflowNodeView[]): Edge[] {
  return views.slice(0, -1).map((view, index) => {
    const next = views[index + 1];
    const sourceActive =
      view.status === "completed" ||
      view.status === "approved" ||
      view.status === "rejected";
    const edgeSkipped = view.isSkipped || next.isSkipped;

    return {
      id: `${view.id}-${next.id}`,
      source: view.id,
      target: next.id,
      animated: false,
      selectable: false,
      focusable: false,
      style: {
        stroke: edgeSkipped ? "#1f1f1f" : sourceActive ? "#52525b" : "#232323",
        strokeDasharray: edgeSkipped ? "4 6" : undefined,
        strokeWidth: sourceActive ? 1.6 : 1,
      },
    };
  });
}
