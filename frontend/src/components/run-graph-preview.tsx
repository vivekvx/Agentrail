import Link from "next/link";
import { ArrowUpRight } from "lucide-react";

import { buildWorkflowViews } from "@/lib/agent-graph";
import type { RunDetail, RunEvent } from "@/lib/types";

const compactNodes = [
  "planner",
  "code_search",
  "patch_generator",
  "approval",
  "verifier",
  "reporter",
];

function previewClass(status: string) {
  switch (status) {
    case "running":
      return "border-zinc-400 bg-[#181818]";
    case "completed":
    case "approved":
      return "border-zinc-600 bg-[#141414]";
    case "rejected":
    case "failed":
      return "border-zinc-500 bg-[#161616]";
    default:
      return "border-border bg-[#0f0f0f]";
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
  const visible = views.filter((view) => compactNodes.includes(view.id));

  return (
    <Link
      className="mt-4 block border border-border bg-[#0d0d0d] p-3 hover:bg-[#111111]"
      href={`/runs/${run.id}/graph`}
    >
      <div className="mb-3 flex items-center justify-between gap-3">
        <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          Graph view
        </span>
        <ArrowUpRight className="size-3.5 text-zinc-600" />
      </div>

      <div className="flex flex-wrap gap-2">
        {visible.map((view) => (
          <div
            className={`min-w-11 border px-2 py-2 ${previewClass(view.status)}`}
            key={view.id}
          >
            <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-600">
              {String(view.order).padStart(2, "0")}
            </div>
          </div>
        ))}
      </div>
    </Link>
  );
}
