import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { buildWorkflowViews } from "@/lib/agent-graph";
import type { RunDetail, RunEvent } from "@/lib/types";

function previewClass(status: string, isSkipped: boolean) {
  if (isSkipped) {
    return "border-[#1f1f1f] bg-[#0f0f0f] text-zinc-500";
  }

  switch (status) {
    case "running":
      return "border-zinc-400 bg-[#171717] text-zinc-100";
    case "completed":
    case "approved":
      return "border-zinc-600 bg-[#141414] text-zinc-200";
    case "rejected":
    case "failed":
      return "border-zinc-500 bg-[#151515] text-zinc-100";
    default:
      return "border-border bg-[#0f0f0f] text-zinc-500";
  }
}

export function RunGraphPreview({
  run,
  events,
}: {
  run: RunDetail;
  events: RunEvent[];
}) {
  const views = buildWorkflowViews(run, events);
  const visible = [
    views.find((view) => view.id === "planner"),
    views.find((view) => view.id === "code_search"),
    views.find((view) => view.id === "patch_generator"),
    views.find((view) => view.id === "approval"),
    views.find((view) => view.id === "reporter"),
  ].filter((view): view is NonNullable<(typeof views)[number]> => Boolean(view));

  return (
    <Link
      className="mt-4 block border border-border bg-[#0d0d0d] p-3 hover:bg-[#111111]"
      href={`/runs/${run.id}/graph`}
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          Open execution graph
        </span>
        <ArrowUpRight className="size-3.5 text-zinc-500" />
      </div>

      <div className="grid grid-cols-5 gap-2">
        {visible.map((view) => (
          <div
            className={`border px-2 py-2 ${previewClass(view.status, view.isSkipped)}`}
            key={view.id}
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.18em]">
              {view.shortTitle}
            </div>
          </div>
        ))}
      </div>
    </Link>
  );
}
