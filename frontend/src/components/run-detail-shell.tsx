"use client";

import { useCallback, useEffect, useState, useTransition } from "react";
import Link from "next/link";
import { RefreshCcw } from "lucide-react";

import {
  approveRun,
  getRun,
  getRunEvents,
  rejectRun,
  startRun,
} from "@/lib/api";
import { saveRecentRunId } from "@/lib/recent-runs";
import type { RunDetail, RunEvent } from "@/lib/types";
import { AgentTimeline } from "@/components/agent-timeline";
import { ApprovalCard } from "@/components/approval-card";
import { FinalReportCard } from "@/components/final-report-card";
import { JsonCard } from "@/components/json-card";
import { PatchPreviewCard } from "@/components/patch-preview-card";
import { RunOverviewCard } from "@/components/run-overview-card";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";

async function loadRunState(runId: number) {
  const [run, events] = await Promise.all([getRun(runId), getRunEvents(runId)]);
  saveRecentRunId(run.id);
  return { run, events };
}

function signalValue(run: RunDetail, events: RunEvent[], key: "approval" | "verification" | "events") {
  if (key === "approval") {
    return run.approval_status ?? "waiting";
  }

  if (key === "verification") {
    return typeof run.verification_result?.status === "string"
      ? run.verification_result.status
      : "pending";
  }

  return String(events.length);
}

export function RunDetailShell({ runId }: { runId: number }) {
  const [run, setRun] = useState<RunDetail | null>(null);
  const [events, setEvents] = useState<RunEvent[]>([]);
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
      <div className="mx-auto flex min-h-screen w-full max-w-[1520px] flex-col px-4 py-4 sm:px-6 lg:px-8">
        <header className="mb-4 grid gap-4 border-b border-border pb-4 lg:grid-cols-[minmax(0,1.1fr)_auto]">
          <div className="space-y-3">
            <Link
              className="inline-flex items-center rounded-md border border-border bg-[#0d0d0d] px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500 hover:text-zinc-200"
              href="/"
            >
              Back to command center
            </Link>
            <div className="flex flex-wrap items-start gap-3">
              <div>
                <h1 className="text-2xl font-semibold tracking-tight text-white sm:text-[2rem]">
                  Run detail
                </h1>
                <p className="mt-1 text-sm text-zinc-500">
                  Timeline-led inspection view for evidence, approval,
                  verification, and residual risk.
                </p>
              </div>
              {run ? (
                <div className="flex flex-wrap items-center gap-2">
                  <div className="rounded-md border border-border bg-[#0d0d0d] px-2.5 py-1 font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                    Run {run.id}
                  </div>
                  <StatusBadge status={run.status} />
                  <RiskBadge
                    level={
                      typeof run.risk_score?.level === "string"
                        ? run.risk_score.level
                        : null
                    }
                  />
                </div>
              ) : null}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
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
        </header>

        {error ? (
          <div className="mb-4 rounded-md border border-border bg-[#111111] px-4 py-3 text-sm text-zinc-300">
            {error}
          </div>
        ) : null}

        {!run ? (
          <div className="rounded-md border border-dashed border-border bg-surface px-6 py-10 text-sm text-zinc-500">
            Loading run state...
          </div>
        ) : (
          <>
            <section className="mb-4 grid gap-px overflow-hidden rounded-md border border-border bg-border md:grid-cols-3">
              <div className="bg-[#0d0d0d] px-4 py-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                  Approval
                </div>
                <div className="mt-2 text-sm text-zinc-100">
                  {signalValue(run, events, "approval")}
                </div>
              </div>
              <div className="bg-[#0d0d0d] px-4 py-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                  Verification
                </div>
                <div className="mt-2 text-sm text-zinc-100">
                  {signalValue(run, events, "verification")}
                </div>
              </div>
              <div className="bg-[#0d0d0d] px-4 py-4">
                <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                  Timeline events
                </div>
                <div className="mt-2 text-sm text-zinc-100">
                  {signalValue(run, events, "events")}
                </div>
              </div>
            </section>

            <section className="grid flex-1 gap-4 xl:grid-cols-[minmax(0,1.34fr)_minmax(360px,0.86fr)]">
              <div className="min-w-0">
                <AgentTimeline events={events} />
              </div>

              <div className="space-y-4">
                <RunOverviewCard run={run} />
                <ApprovalCard
                  approvalPayload={run.approval_payload}
                  approvalStatus={run.approval_status}
                  disabled={isPending || run.status !== "pending_approval"}
                  onApprove={() => runAction("approve")}
                  onReject={() => runAction("reject")}
                />
                <PatchPreviewCard patchDiff={run.patch_diff} />
                <JsonCard
                  description="Structured verification outcome from the backend verifier."
                  title="Verification"
                  value={run.verification_result}
                />
                <JsonCard
                  description="Residual risk assessment after verification."
                  title="Risk Score"
                  value={run.risk_score}
                />
                <JsonCard
                  description="Safe local test runner output captured after approval."
                  title="Test Result"
                  value={run.test_result}
                />
                <FinalReportCard report={run.final_report} />
              </div>
            </section>
          </>
        )}
      </div>
    </main>
  );
}
