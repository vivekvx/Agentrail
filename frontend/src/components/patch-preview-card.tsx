import { useState } from "react";
import { applyPatch } from "@/lib/api";

function diffStats(patchDiff: string | null) {
  if (!patchDiff) {
    return { files: 0, additions: 0, deletions: 0 };
  }

  return patchDiff.split("\n").reduce(
    (stats, line) => {
      if (line.startsWith("diff --git ")) {
        stats.files += 1;
      } else if (line.startsWith("+") && !line.startsWith("+++")) {
        stats.additions += 1;
      } else if (line.startsWith("-") && !line.startsWith("---")) {
        stats.deletions += 1;
      }
      return stats;
    },
    { files: 0, additions: 0, deletions: 0 },
  );
}

export function PatchPreviewCard({
  patchDiff,
  runId,
  approvalStatus,
  repoPath,
}: {
  patchDiff: string | null;
  runId?: number;
  approvalStatus?: string | null;
  repoPath?: string | null;
}) {
  const stats = diffStats(patchDiff);
  const [applying, setApplying] = useState(false);
  const [applyResult, setApplyResult] = useState<{ applied: boolean; output?: string; error?: string } | null>(null);

  async function handleApply() {
    if (!runId) return;
    setApplying(true);
    setApplyResult(null);
    try {
      const result = await applyPatch(runId) as { applied: boolean; output?: string; error?: string };
      setApplyResult(result);
    } catch (e) {
      setApplyResult({ applied: false, error: e instanceof Error ? e.message : "Apply failed." });
    } finally {
      setApplying(false);
    }
  }

  return (
    <section className="border-t border-border pt-6">
      <div className="mb-5 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Patch preview
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#fafafa]">
            Proposed diff
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-zinc-500">
            Unified diff preview only. No patch application happens in this UI.
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex flex-wrap gap-4 font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            <span>{stats.files} file</span>
            <span className="text-emerald-500">+{stats.additions}</span>
            <span className="text-red-500">-{stats.deletions}</span>
          </div>
          {repoPath && approvalStatus === "approved" && patchDiff ? (
            <button
              onClick={handleApply}
              disabled={applying}
              className="inline-flex h-8 items-center gap-1.5 rounded-sm border border-[var(--accent-border)] bg-[var(--accent-dim)] px-3 font-mono text-[10.5px] uppercase tracking-[0.12em] text-[var(--accent)] hover:bg-[rgba(16,185,129,0.15)] disabled:opacity-50 transition"
            >
              {applying ? "Applying..." : "Apply patch"}
            </button>
          ) : null}
        </div>
      </div>

      <div className="overflow-hidden border border-border bg-[#0d0d0d]">
        {patchDiff ? (
          <pre className="scrollbar-thin max-h-[34rem] overflow-auto p-5 font-mono text-xs leading-6">
            {patchDiff.split("\n").map((line, i) => {
              let cls = "text-zinc-400";
              if (line.startsWith("+++") || line.startsWith("---")) cls = "text-zinc-500";
              else if (line.startsWith("+")) cls = "text-emerald-400";
              else if (line.startsWith("-")) cls = "text-red-400";
              else if (line.startsWith("@@")) cls = "text-sky-400";
              else if (line.startsWith("diff ") || line.startsWith("index ")) cls = "text-zinc-500";
              return (
                <span key={i} className={`block ${cls}`}>
                  {line || " "}
                </span>
              );
            })}
          </pre>
        ) : (
          <pre className="scrollbar-thin max-h-[34rem] overflow-auto p-5 font-mono text-xs leading-6 text-zinc-500">
            No patch preview available.
          </pre>
        )}
      </div>
      {applyResult ? (
        <div className={`mt-3 rounded-sm border px-4 py-3 font-mono text-xs ${applyResult.applied ? "border-[var(--success-border)] bg-[var(--success-bg)] text-[var(--success-text)]" : "border-[var(--danger-border)] bg-[var(--danger-bg)] text-[var(--danger-text)]"}`}>
          {applyResult.applied ? "Patch applied successfully." : (applyResult.error ?? "Patch apply failed.")}
          {applyResult.output ? <pre className="mt-2 whitespace-pre-wrap opacity-70">{applyResult.output}</pre> : null}
        </div>
      ) : null}
    </section>
  );
}
