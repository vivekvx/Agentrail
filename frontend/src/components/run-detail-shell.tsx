"use client";

import { ReactFlowProvider } from "@xyflow/react";
import { useCallback, useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { GitBranch, RefreshCcw } from "lucide-react";

import {
  approveRun,
  getRun,
  getRunEvents,
  rejectRun,
  startRun,
} from "@/lib/api";
import { buildWorkflowViews, getPreferredWorkflowNodeId } from "@/lib/agent-graph";
import { saveRecentRunId } from "@/lib/recent-runs";
import type { RunDetail, RunEvent } from "@/lib/types";
import { AgentTimeline } from "@/components/agent-timeline";
import { ApprovalCard } from "@/components/approval-card";
import { ExecutionGraphPanel } from "@/components/execution-graph-panel";
import { FinalReportCard } from "@/components/final-report-card";
import { PatchPreviewCard } from "@/components/patch-preview-card";
import {
  RiskPanel,
  TestResultPanel,
  VerificationPanel,
} from "@/components/run-analysis-panels";
import { RunOverviewCard } from "@/components/run-overview-card";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";

async function loadRunState(runId: number) {
  const [run, events] = await Promise.all([getRun(runId), getRunEvents(runId)]);
  saveRecentRunId(run.id);
  return { run, events };
}

function RunDetailShellInner({ runId }: { runId: number }) {
  const [run, setRun] = useState<RunDetail | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string>("");
  const [selectionOrigin, setSelectionOrigin] = useState<"graph" | "timeline" | null>(null);
  const [selectionVersion, setSelectionVersion] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  const refresh = useCallback(async () => {
    try {
      setError(null);
      const next = await loadRunState(runId);
      setRun(next.run);
      setEvents(next.events);
    } catch (refreshError) {
      const message =
        refreshError instanceof Error
          ? refreshError.message
          : "Unable to load run.";
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

  const activeNodeId =
    run && events.length >= 0
      ? selectedNodeId ||
        getPreferredWorkflowNodeId(buildWorkflowViews(run, events))
      : selectedNodeId;

  function updateSelection(nodeId: string, origin: "graph" | "timeline") {
    setSelectedNodeId(nodeId);
    setSelectionOrigin(origin);
    setSelectionVersion((value) => value + 1);
  }

  function runAction(action: "start" | "approve" | "reject") {
    startTransition(async () => {
      try {
        setError(null);
        if (action === "start") {
          await startRun(runId);
        } else if (action === "approve") {
          await approveRun(runId);
        } else {
          await rejectRun(runId);
        }
        await refresh();
      } catch (actionError) {
        const message =
          actionError instanceof Error
            ? actionError.message
            : "Action failed.";
        setError(message);
      }
    });
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen w-full max-w-[1400px] flex-col px-5 py-6 sm:px-8">
        <header className="border-b border-border pb-8">
          <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
            <Link
              className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500 hover:text-zinc-200"
              href="/"
            >
              Back to command center
            </Link>

            <div className="flex flex-wrap items-center gap-3">
              <Link href={`/runs/${runId}/graph`}>
                <Button variant="ghost">
                  <GitBranch className="size-4" />
                  Full Graph
                </Button>
              </Link>
              <Button
                disabled={isPending}
                onClick={() => void refresh()}
                variant="ghost"
              >
                <RefreshCcw className="size-4" />
                Refresh
              </Button>
              <Button
                disabled={isPending || (!!run && run.status !== "created")}
                onClick={() => runAction("start")}
                variant="secondary"
              >
                Start Run
              </Button>
            </div>
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
                {run.user_task}
              </h1>

              <div className="mt-4 grid gap-3 text-sm text-zinc-500 md:grid-cols-[minmax(0,1fr)_auto_auto]">
                <span className="truncate">{run.repo_path}</span>
                {run.expected_behavior ? <span>{run.expected_behavior}</span> : null}
                {run.test_command ? (
                  <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                    {run.test_command}
                  </span>
                ) : null}
              </div>
            </>
          ) : (
            <>
              <h1 className="text-4xl font-semibold tracking-tight text-[#fafafa] sm:text-5xl">
                Run detail
              </h1>
              <p className="mt-3 text-sm text-zinc-500">Loading run state...</p>
            </>
          )}
        </header>

        {error ? (
          <div className="mt-4 border border-border bg-surface px-4 py-3 text-sm text-zinc-300">
            {error}
          </div>
        ) : null}

        {!run ? (
          <div className="py-10 text-sm text-zinc-500">Loading run state...</div>
        ) : (
          <div className="flex-1 pt-6">
            <ExecutionGraphPanel
              description="Select a step to focus the matching events below."
              events={events}
              onNodeSelect={(nodeId) => updateSelection(nodeId, "graph")}
              run={run}
              selectedNodeId={activeNodeId}
              title="Execution"
              variant="compact"
            />

            <AgentTimeline
              events={events}
              onEventSelect={(_, nodeId) => updateSelection(nodeId, "timeline")}
              selectedNodeId={activeNodeId}
              selectionOrigin={selectionOrigin}
              selectionVersion={selectionVersion}
            />

            <section className="grid gap-10 pt-8 xl:grid-cols-[minmax(0,1fr)_340px]">
              <div className="min-w-0 space-y-8">
                <PatchPreviewCard patchDiff={run.patch_diff} />
                <VerificationPanel verificationResult={run.verification_result} />
                <RiskPanel riskScore={run.risk_score} />
                <FinalReportCard report={run.final_report} />
              </div>

              <aside className="space-y-8 xl:sticky xl:top-6 xl:self-start">
                <ApprovalCard
                  approvalPayload={run.approval_payload}
                  approvalStatus={run.approval_status}
                  disabled={isPending || run.status !== "pending_approval"}
                  onApprove={() => runAction("approve")}
                  onReject={() => runAction("reject")}
                />
                <RunOverviewCard run={run} />
                <TestResultPanel testResult={run.test_result} />
              </aside>
            </section>
          </div>
        )}
      </div>
    </main>
  );
}

export function RunDetailShell({ runId }: { runId: number }) {
  return (
    <ReactFlowProvider>
      <RunDetailShellInner runId={runId} />
    </ReactFlowProvider>
  );
}
