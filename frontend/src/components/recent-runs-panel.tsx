"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ArrowUpRight, RefreshCcw } from "lucide-react";

import { getRun, getRunEvents } from "@/lib/api";
import { loadRecentRunIds, saveRecentRunId } from "@/lib/recent-runs";
import type { RunDetail, RunEvent } from "@/lib/types";
import { RunGraphPreview } from "@/components/run-graph-preview";
import { RiskBadge } from "@/components/risk-badge";
import { StatusBadge } from "@/components/status-badge";
import { Button } from "@/components/ui/button";

function summaryLine(run: RunDetail) {
  const verification =
    typeof run.verification_result?.status === "string"
      ? run.verification_result.status
      : "awaiting verification";

  return `${run.status.replaceAll("_", " ")} · ${verification}`;
}

interface RecentRunItem {
  run: RunDetail;
  events: RunEvent[];
}

export function RecentRunsPanel() {
  const [runs, setRuns] = useState<RecentRunItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  async function loadRuns() {
    setIsLoading(true);
    const ids = loadRecentRunIds();
    const hydrated = await Promise.all(
      ids.map(async (id) => {
        try {
          const [run, events] = await Promise.all([getRun(id), getRunEvents(id)]);
          saveRecentRunId(run.id);
          return { run, events };
        } catch {
          return null;
        }
      }),
    );
    setRuns(
      hydrated.filter((item): item is RecentRunItem => item !== null),
    );
    setIsLoading(false);
  }

  useEffect(() => {
    queueMicrotask(() => {
      void loadRuns();
    });
  }, []);

  return (
    <aside className="border-l border-border pl-0 lg:pl-8">
      <div className="mb-6 flex items-start justify-between gap-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Recent runs
          </div>
          <p className="mt-3 max-w-xs text-sm leading-7 text-zinc-500">
            Runs opened in this browser, hydrated from the current API and kept
            close for quick re-entry.
          </p>
        </div>
        <Button
          aria-label="Refresh recent runs"
          onClick={() => void loadRuns()}
          size="sm"
          variant="ghost"
        >
          <RefreshCcw className="size-4" />
        </Button>
      </div>

      {isLoading ? (
        <div className="border-t border-border py-6 text-sm text-zinc-500">
          Loading recent runs...
        </div>
      ) : runs.length === 0 ? (
        <div className="border-t border-border py-6 text-sm leading-7 text-zinc-500">
          No recent runs yet. Create one and it will appear here for quick
          return access.
        </div>
      ) : (
        <div className="border-t border-border">
          {runs.map(({ run, events }) => (
            <div className="border-b border-border py-5" key={run.id}>
              <Link className="group block" href={`/runs/${run.id}`}>
                <div className="mb-3 flex flex-wrap items-center gap-2">
                  <span className="font-mono text-[11px] uppercase tracking-[0.16em] text-zinc-500">
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

                <div className="flex items-start justify-between gap-4">
                  <div className="min-w-0">
                    <p className="line-clamp-2 text-sm leading-6 text-zinc-100">
                      {run.user_task}
                    </p>
                    <p className="mt-3 truncate font-mono text-[11px] text-zinc-600">
                      {run.repo_path}
                    </p>
                    <p className="mt-2 text-xs text-zinc-500">{summaryLine(run)}</p>
                  </div>
                  <ArrowUpRight className="mt-1 size-4 shrink-0 text-zinc-700 transition-colors group-hover:text-zinc-300" />
                </div>
              </Link>

              <RunGraphPreview run={run} events={events} />
            </div>
          ))}
        </div>
      )}
    </aside>
  );
}
