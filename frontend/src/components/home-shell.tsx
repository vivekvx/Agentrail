import { CreateRunForm } from "@/components/create-run-form";
import { RecentRunsPanel } from "@/components/recent-runs-panel";
import { SiteChrome } from "@/components/site-chrome";

const workflowStages = [
  { id: "scan", label: "Scan", desc: "Stack + files" },
  { id: "evidence", label: "Evidence", desc: "Line-numbered" },
  { id: "root-cause", label: "Root cause", desc: "Structured" },
  { id: "patch", label: "Patch", desc: "Diff preview" },
  { id: "approval", label: "Approval", desc: "Human gate" },
  { id: "verify", label: "Verify", desc: "Test runner" },
  { id: "risk", label: "Risk", desc: "Scored" },
  { id: "report", label: "Report", desc: "PR-ready" },
];

export function HomeShell() {
  return (
    <SiteChrome>
      {/* Hero */}
      <section className="border-b border-[var(--border)] py-16 sm:py-20">
        <div className="grid gap-12 lg:grid-cols-[minmax(0,1.2fr)_400px] lg:items-center">
          <div>
            <h1 className="max-w-3xl text-balance text-[2.75rem] font-semibold tracking-tight text-zinc-50 leading-[1.1] sm:text-5xl lg:text-6xl">
              Evidence-backed bug fixes, with human approval.
            </h1>
            <p className="mt-5 max-w-xl text-base leading-8 text-zinc-500">
              Agentrail traces root cause from repository source, previews a
              patch, pauses for your approval, runs tests, scores risk, and
              exports a PR-ready report.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-3">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--success-border)] bg-[var(--success-bg)] px-3 py-1 font-mono text-[10.5px] uppercase tracking-[0.14em] text-[var(--success-text)]">
                <span className="size-1.5 rounded-full bg-[var(--success-text)]" />
                Patch-preview only
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--neutral-border)] bg-[var(--neutral-bg)] px-3 py-1 font-mono text-[10.5px] uppercase tracking-[0.14em] text-[var(--neutral-text)]">
                Human approval gate
              </span>
              <span className="inline-flex items-center gap-1.5 rounded-full border border-[var(--neutral-border)] bg-[var(--neutral-bg)] px-3 py-1 font-mono text-[10.5px] uppercase tracking-[0.14em] text-[var(--neutral-text)]">
                No repo writes
              </span>
            </div>
          </div>

          {/* Workflow map */}
          <div className="border border-[var(--border)] bg-[var(--panel)] rounded-sm overflow-hidden">
            <div className="border-b border-[var(--border)] px-4 py-3 flex items-center justify-between">
              <span className="font-mono text-[10.5px] uppercase tracking-[0.18em] text-zinc-600">
                Agent workflow
              </span>
              <span className="inline-flex items-center gap-1 font-mono text-[10.5px] text-zinc-700">
                <span className="size-1.5 rounded-full bg-emerald-500" />
                10-stage pipeline
              </span>
            </div>
            <div className="grid grid-cols-2 gap-px bg-[var(--border)]">
              {workflowStages.map((stage) => (
                <div
                  className="bg-[var(--panel)] px-4 py-3 group hover:bg-[rgba(16,185,129,0.04)] transition"
                  key={stage.id}
                >
                  <div className="font-mono text-[10px] text-zinc-700 group-hover:text-emerald-900 transition">
                    {stage.desc}
                  </div>
                  <div className="mt-1 font-mono text-[11.5px] font-semibold uppercase tracking-[0.14em] text-zinc-300 group-hover:text-zinc-100 transition">
                    {stage.label}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Safety guarantees strip */}
      <section className="grid gap-px bg-[var(--border)] sm:grid-cols-3">
        {[
          ["Patch preview only", "No direct repository mutation. Review before applying."],
          ["Approval gate", "LangGraph interrupt pauses before verification continues."],
          ["Copy-ready PR draft", "Manual export only. No hidden GitHub writes."],
        ].map(([title, body]) => (
          <div className="bg-background px-6 py-5" key={title}>
            <div className="size-1.5 rounded-full bg-[var(--accent)] mb-4" />
            <h2 className="text-sm font-semibold tracking-tight text-zinc-100">
              {title}
            </h2>
            <p className="mt-1.5 text-sm leading-6 text-zinc-600">{body}</p>
          </div>
        ))}
      </section>

      {/* Run creation + recent runs */}
      <section className="grid flex-1 gap-10 py-10 lg:grid-cols-[minmax(0,1.1fr)_360px]">
        <CreateRunForm />
        <RecentRunsPanel />
      </section>
    </SiteChrome>
  );
}
