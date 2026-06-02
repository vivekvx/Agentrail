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

export function PatchPreviewCard({ patchDiff }: { patchDiff: string | null }) {
  const stats = diffStats(patchDiff);

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
        <div className="flex flex-wrap gap-4 font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          <span>{stats.files} file</span>
          <span>+{stats.additions}</span>
          <span>-{stats.deletions}</span>
        </div>
      </div>

      <div className="overflow-hidden border border-border bg-[#0d0d0d]">
        <pre className="scrollbar-thin max-h-[34rem] overflow-auto p-5 font-mono text-xs leading-6 text-zinc-300">
          <code>{patchDiff ?? "No patch preview available."}</code>
        </pre>
      </div>
    </section>
  );
}
