import type { RunDetail } from "@/lib/types";

export function RunOverviewCard({ run }: { run: RunDetail }) {
  return (
    <section className="border border-border bg-surface p-5">
      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
        Run context
      </div>

      <div className="mt-5 space-y-5">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
            Repository
          </div>
          <p className="mt-2 break-all text-sm leading-7 text-zinc-200">
            {run.repo_path}
          </p>
        </div>

        <div className="border-t border-border pt-5">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
            User task
          </div>
          <p className="mt-2 text-sm leading-7 text-zinc-200">{run.user_task}</p>
        </div>

        {run.expected_behavior ? (
          <div className="border-t border-border pt-5">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
              Expected behavior
            </div>
            <p className="mt-2 text-sm leading-7 text-zinc-300">
              {run.expected_behavior}
            </p>
          </div>
        ) : null}

        {run.test_command ? (
          <div className="border-t border-border pt-5">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
              Test command
            </div>
            <code className="mt-2 block bg-[#0d0d0d] p-3 font-mono text-xs text-zinc-300">
              {run.test_command}
            </code>
          </div>
        ) : null}
      </div>
    </section>
  );
}
