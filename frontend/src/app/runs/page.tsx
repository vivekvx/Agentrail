import Link from "next/link";
import { SiteChrome } from "@/components/site-chrome";
import { getRuns } from "@/lib/api";
import type { RunDetail } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  completed: "text-[var(--success-text)] border-[var(--success-border)] bg-[var(--success-bg)]",
  running: "text-[var(--warning-text)] border-[var(--warning-border)] bg-[var(--warning-bg)]",
  pending_approval: "text-[var(--warning-text)] border-[var(--warning-border)] bg-[var(--warning-bg)]",
  failed: "text-[var(--danger-text)] border-[var(--danger-border)] bg-[var(--danger-bg)]",
  rejected: "text-[var(--danger-text)] border-[var(--danger-border)] bg-[var(--danger-bg)]",
  created: "text-[var(--neutral-text)] border-[var(--neutral-border)] bg-[var(--neutral-bg)]",
};

function RunRow({ run }: { run: RunDetail }) {
  const colorClass = STATUS_COLORS[run.status] ?? STATUS_COLORS.created;
  const repoLabel = run.repo_path ?? run.repo_url ?? "—";
  const date = run.created_at
    ? new Date(run.created_at).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";

  return (
    <Link
      href={`/runs/${run.id}`}
      className="grid grid-cols-[48px_1fr_160px_140px_100px] gap-4 items-center border-t border-[var(--border)] px-6 py-4 hover:bg-[rgba(16,185,129,0.03)] transition group"
    >
      <span className="font-mono text-[11px] text-zinc-600">#{run.id}</span>
      <div className="min-w-0">
        <div className="text-sm font-medium text-zinc-100 truncate group-hover:text-white">
          {run.user_task || "—"}
        </div>
        <div className="font-mono text-[10px] text-zinc-600 truncate mt-0.5">{repoLabel}</div>
      </div>
      <span className="font-mono text-[10px] text-zinc-600 truncate">{date}</span>
      <span
        className={`inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.12em] w-fit ${colorClass}`}
      >
        <span className="size-1 rounded-full bg-current" />
        {run.status.replace(/_/g, " ")}
      </span>
      <span className="font-mono text-[10px] text-zinc-700 text-right">
        {run.risk_score?.level ? `${run.risk_score.level} risk` : "—"}
      </span>
    </Link>
  );
}

export default async function RunsPage() {
  let runs: RunDetail[] = [];
  try {
    runs = await getRuns(50);
  } catch {
    // backend offline — show empty state
  }

  return (
    <SiteChrome>
      <section className="border-b border-[var(--border)] py-10">
        <h1 className="text-3xl font-semibold tracking-tight text-zinc-50">Run history</h1>
        <p className="mt-2 text-sm text-zinc-500">All runs ordered by most recent. Click to open.</p>
      </section>

      <section className="mt-6">
        {runs.length === 0 ? (
          <div className="py-16 text-center text-sm text-zinc-600">
            No runs yet. Create one from the{" "}
            <Link href="/" className="text-[var(--accent)] hover:underline">
              console
            </Link>
            .
          </div>
        ) : (
          <div>
            <div className="grid grid-cols-[48px_1fr_160px_140px_100px] gap-4 px-6 py-2 font-mono text-[10px] uppercase tracking-[0.14em] text-zinc-600">
              <span>ID</span>
              <span>Task</span>
              <span>Created</span>
              <span>Status</span>
              <span className="text-right">Risk</span>
            </div>
            {runs.map((run) => (
              <RunRow key={run.id} run={run} />
            ))}
          </div>
        )}
      </section>
    </SiteChrome>
  );
}
