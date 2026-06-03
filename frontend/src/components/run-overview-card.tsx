import type { RunDetail } from "@/lib/types";

function textValue(value: unknown) {
  return typeof value === "string" && value.trim().length > 0 ? value : null;
}

function listValue(value: unknown) {
  return Array.isArray(value)
    ? value.filter((item): item is string => typeof item === "string")
    : [];
}

export function RunOverviewCard({ run }: { run: RunDetail }) {
  const issueTitle = textValue(run.issue_context?.title);
  const issueState = textValue(run.issue_context?.state);
  const issueAuthor = textValue(run.issue_context?.author);
  const issueLabels = listValue(run.issue_context?.labels);

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
            {run.repo_url ?? run.repo_path ?? "Repository path pending import"}
          </p>
        </div>

        {run.repo_url ? (
          <div className="border-t border-border pt-5">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
              GitHub URL
            </div>
            <p className="mt-2 break-all text-sm leading-7 text-zinc-300">
              {run.repo_url}
            </p>
          </div>
        ) : null}

        {run.issue_url ? (
          <div className="border-t border-border pt-5">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
              GitHub issue
            </div>
            <a
              className="mt-2 block break-all text-sm leading-7 text-zinc-300 underline-offset-4 hover:text-zinc-100 hover:underline"
              href={run.issue_url}
              rel="noreferrer"
              target="_blank"
            >
              {issueTitle ?? run.issue_url}
            </a>
            <div className="mt-3 flex flex-wrap gap-2">
              {issueState ? (
                <span className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-zinc-500">
                  {issueState}
                </span>
              ) : null}
              {issueAuthor ? (
                <span className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-zinc-500">
                  {issueAuthor}
                </span>
              ) : null}
              {issueLabels.map((label) => (
                <span
                  className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-zinc-500"
                  key={label}
                >
                  {label}
                </span>
              ))}
            </div>
          </div>
        ) : null}

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
