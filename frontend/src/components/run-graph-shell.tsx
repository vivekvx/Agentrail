"use client";

import { ReactFlowProvider } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowLeft, RefreshCcw } from "lucide-react";

import { getRun, getRunEvents } from "@/lib/api";
import { saveRecentRunId } from "@/lib/recent-runs";
import type { RunDetail, RunEvent } from "@/lib/types";
import { ExecutionGraphPanel } from "@/components/execution-graph-panel";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";

async function loadRunGraph(runId: number) {
  const [run, events] = await Promise.all([getRun(runId), getRunEvents(runId)]);
  saveRecentRunId(run.id);
  return { run, events };
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
                <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
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
                A read-only execution visualizer for the live run.
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

        {!run ? (
          <div className="py-10 text-sm text-zinc-500">Loading graph…</div>
        ) : (
          <div className="flex-1 pt-8">
            <ExecutionGraphPanel
              description="Select a node to inspect its role, output, and most recent timestamp."
              events={events}
              onNodeSelect={setSelectedNodeId}
              run={run}
              selectedNodeId={selectedNodeId}
              title="Workflow state"
              variant="full"
            />
          </div>
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
