import type { Edge, Node } from "@xyflow/react";

import type { JsonObject, RunDetail, RunEvent } from "@/lib/types";

export type WorkflowNodeStatus =
  | "pending"
  | "running"
  | "completed"
  | "approved"
  | "rejected"
  | "failed";

export interface WorkflowNodeDefinition {
  id: string;
  order: number;
  title: string;
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
};

export interface WorkflowNodeView {
  id: string;
  order: number;
  title: string;
  purpose: string;
  status: WorkflowNodeStatus;
  timestamp: string | null;
  summary: string;
}

const HORIZONTAL_GAP = 196;

export const WORKFLOW_DEFINITIONS: WorkflowNodeDefinition[] = [
  {
    id: "planner",
    order: 1,
    title: "Planner",
    purpose: "Builds the initial investigation plan and establishes the run path.",
    eventTypes: [],
    backendNodes: ["planner"],
  },
  {
    id: "repo_scanner",
    order: 2,
    title: "Repo Scanner",
    purpose: "Detects stack, entry points, and likely repo structure.",
    eventTypes: ["repo_scanned"],
    backendNodes: ["repo_scanner"],
  },
  {
    id: "code_search",
    order: 3,
    title: "Code Search",
    purpose: "Searches the repository for evidence-bearing symbols and files.",
    eventTypes: ["code_searched"],
    backendNodes: ["code_search"],
  },
  {
    id: "evidence_reader",
    order: 4,
    title: "Evidence Reader",
    purpose: "Reads supporting files and snippets into structured evidence.",
    eventTypes: ["evidence_read"],
    backendNodes: ["evidence_reader"],
  },
  {
    id: "root_cause",
    order: 5,
    title: "Root Cause",
    purpose: "Produces the deterministic root-cause statement from evidence.",
    eventTypes: ["root_cause_generated"],
    backendNodes: ["root_cause"],
  },
  {
    id: "patch_generator",
    order: 6,
    title: "Patch Generator",
    purpose: "Builds a minimal unified diff preview for review.",
    eventTypes: ["patch_generated"],
    backendNodes: ["patch_generator"],
  },
  {
    id: "approval",
    order: 7,
    title: "Approval",
    purpose: "Pauses the run for a human decision before verification proceeds.",
    eventTypes: ["pending_approval", "approved", "rejected"],
    backendNodes: ["approval_node"],
  },
  {
    id: "test_runner",
    order: 8,
    title: "Test Runner",
    purpose: "Runs the safe local verification command after approval.",
    eventTypes: ["tests_run"],
    backendNodes: ["test_runner"],
  },
  {
    id: "verifier",
    order: 9,
    title: "Verifier",
    purpose: "Interprets approval, evidence, and test outcomes into verification state.",
    eventTypes: ["verified"],
    backendNodes: ["verifier"],
  },
  {
    id: "risk_scorer",
    order: 10,
    title: "Risk Scorer",
    purpose: "Computes residual deployment risk from verification and patch scope.",
    eventTypes: ["risk_scored"],
    backendNodes: ["risk_scorer"],
  },
  {
    id: "reporter",
    order: 11,
    title: "Reporter",
    purpose: "Produces the final report artifact for review and handoff.",
    eventTypes: ["report_generated", "run_completed"],
    backendNodes: ["reporter"],
  },
];

function mapBackendNodeToWorkflow(run: RunDetail): string | null {
  const currentNode = run.current_node;
  if (!currentNode) {
    if (run.status === "completed") {
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

function firstCompletedIndex(events: RunEvent[], currentWorkflowNode: string | null) {
  if (events.length > 0) {
    return 0;
  }

  if (currentWorkflowNode && currentWorkflowNode !== "planner") {
    return 0;
  }

  return -1;
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

  const latestByType = collectLatestEvents(events);
  for (let index = WORKFLOW_DEFINITIONS.length - 1; index >= 0; index -= 1) {
    const definition = WORKFLOW_DEFINITIONS[index];
    const hasCompletionEvent = definition.eventTypes.some((eventType) =>
      latestByType.has(eventType),
    );
    if (hasCompletionEvent) {
      const next = WORKFLOW_DEFINITIONS[index + 1];
      return next?.id ?? definition.id;
    }
  }

  return "planner";
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
    return "No stack signature recorded.";
  }

  return `Detected ${detected.join(", ")}.`;
}

function summarizeNode(
  definition: WorkflowNodeDefinition,
  run: RunDetail,
  event: RunEvent | null,
): string {
  const payload = event?.payload ?? null;

  switch (definition.id) {
    case "planner":
      return "Plan created for investigation and verification flow.";
    case "repo_scanner":
      return summarizeStack(payload);
    case "code_search":
      return typeof payload?.match_count === "number"
        ? `${payload.match_count} search matches found.`
        : "Search completed.";
    case "evidence_reader":
      return typeof payload?.evidence_count === "number"
        ? `${payload.evidence_count} evidence item(s) captured.`
        : "Evidence reading completed.";
    case "root_cause":
      return event?.message ?? "Root cause generated.";
    case "patch_generator":
      return run.patch_diff ? "Patch preview generated." : "No patch preview available.";
    case "approval":
      if (run.status === "rejected" || run.approval_status === "rejected") {
        return "Patch was rejected by the reviewer.";
      }
      if (run.approval_status === "approved") {
        return "Patch was approved and verification continued.";
      }
      if (payload && typeof payload.question === "string") {
        return payload.question;
      }
      return "Waiting for human approval.";
    case "test_runner":
      return typeof payload?.status === "string"
        ? `Test runner status: ${payload.status}.`
        : "No test result recorded yet.";
    case "verifier":
      return typeof payload?.summary === "string"
        ? payload.summary
        : "Verification result not recorded yet.";
    case "risk_scorer":
      if (typeof payload?.score === "number" && typeof payload?.level === "string") {
        return `Risk ${payload.level} (${payload.score}/100).`;
      }
      return "Risk score not recorded yet.";
    case "reporter":
      return run.final_report
        ? "Final report artifact is available."
        : "Final report not generated yet.";
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
): WorkflowNodeStatus {
  if (failedNodeId === definition.id) {
    return "failed";
  }

  if (definition.id === "approval") {
    if (run.status === "rejected" || run.approval_status === "rejected" || latestByType.has("rejected")) {
      return "rejected";
    }
    if (run.approval_status === "approved" || latestByType.has("approved")) {
      return "approved";
    }
    if (run.status === "pending_approval" || currentWorkflowNode === "approval" || latestByType.has("pending_approval")) {
      return "running";
    }
  }

  if (definition.id === "reporter") {
    if (run.final_report || latestByType.has("report_generated") || latestByType.has("run_completed")) {
      return "completed";
    }
  }

  if (definition.id === "planner") {
    if (currentWorkflowNode === "planner" && latestByType.size === 0 && run.status === "running") {
      return "running";
    }

    if (firstCompletedIndex(Array.from(latestByType.values()), currentWorkflowNode) === 0) {
      return "completed";
    }
  }

  if (definition.eventTypes.some((eventType) => latestByType.has(eventType))) {
    return "completed";
  }

  if (currentWorkflowNode === definition.id && run.status !== "failed") {
    return "running";
  }

  return "pending";
}

export function buildWorkflowViews(run: RunDetail, events: RunEvent[]): WorkflowNodeView[] {
  const latestByType = collectLatestEvents(events);
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
            null
          : definition.eventTypes
              .map((eventType) => latestByType.get(eventType))
              .filter((event): event is RunEvent => Boolean(event))
              .at(-1) ?? null;

    return {
      id: definition.id,
      order: definition.order,
      title: definition.title,
      purpose: definition.purpose,
      status: statusForNode(
        definition,
        run,
        latestByType,
        currentWorkflowNode,
        failedNodeId,
      ),
      timestamp: nodeTimestamp(definition, latestByType),
      summary: summarizeNode(definition, run, relevantEvent),
    };
  });
}

export function buildReactFlowNodes(
  views: WorkflowNodeView[],
  selectedNodeId: string,
): Node<WorkflowGraphNodeData>[] {
  return views.map((view, index) => ({
    id: view.id,
    type: "workflowNode",
    position: { x: index * HORIZONTAL_GAP, y: 120 },
    draggable: false,
    selectable: true,
    data: {
      id: view.id,
      title: view.title,
      order: view.order,
      status: view.status,
      subtitle: view.id.replaceAll("_", " "),
      isSelected: view.id === selectedNodeId,
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

    return {
      id: `${view.id}-${next.id}`,
      source: view.id,
      target: next.id,
      animated: false,
      selectable: false,
      focusable: false,
      style: {
        stroke: sourceActive ? "#4b5563" : "#232323",
        strokeWidth: sourceActive ? 1.5 : 1,
      },
    };
  });
}
