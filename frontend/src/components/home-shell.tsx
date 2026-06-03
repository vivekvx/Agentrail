import { CreateRunForm } from "@/components/create-run-form";
import { RecentRunsPanel } from "@/components/recent-runs-panel";
import { SiteChrome } from "@/components/site-chrome";

const workflowStages = [
  "scan",
  "evidence",
  "patch",
  "approval",
  "verify",
  "risk",
  "report",
];

export function HomeShell() {
  return (
    <SiteChrome>
      <section className="border-b border-border py-14 sm:py-18">
        <div className="grid gap-10 lg:grid-cols-[minmax(0,1.1fr)_420px] lg:items-end">
          <div>
            <div className="mb-5 flex flex-wrap items-center gap-3">
              <span className="border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.22em] text-zinc-400">
                Agentrail
              </span>
              <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                Repository verification system
              </span>
            </div>

            <h1 className="max-w-4xl text-balance text-5xl font-semibold tracking-tight text-[#fafafa] sm:text-6xl lg:text-7xl">
              Review agent code changes like engineering evidence.
            </h1>
            <p className="mt-6 max-w-2xl text-base leading-8 text-[#a1a1aa]">
              Agentrail turns repository analysis into a traceable run:
              evidence, root cause, patch preview, approval, tests, verifier,
              risk score, final report, and PR draft export.
            </p>
          </div>

          <div className="border border-border bg-[#0d0d0d]">
            <div className="border-b border-border p-4 font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
              Live system map
            </div>
            <div className="grid grid-cols-2 gap-px bg-border">
              {workflowStages.map((stage, index) => (
                <div className="bg-[#101010] p-4" key={stage}>
                  <div className="font-mono text-[11px] text-zinc-600">
                    0{index + 1}
                  </div>
                  <div className="mt-2 font-mono text-xs uppercase tracking-[0.16em] text-zinc-200">
                    {stage}
                  </div>
                </div>
              ))}
              <div className="bg-[#f5f5f5] p-4 text-black">
                <div className="font-mono text-[11px] text-zinc-500">08</div>
                <div className="mt-2 font-mono text-xs uppercase tracking-[0.16em]">
                  draft
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-px bg-border lg:grid-cols-3">
        {[
          ["Patch preview only", "No direct repository mutation."],
          ["Approval gate", "Human decision before verification."],
          ["Copy-ready PR draft", "Manual export, no hidden GitHub writes."],
        ].map(([title, body]) => (
          <div className="bg-background py-6 lg:p-6" key={title}>
            <h2 className="text-lg font-semibold tracking-tight text-zinc-100">
              {title}
            </h2>
            <p className="mt-2 text-sm leading-6 text-zinc-500">{body}</p>
          </div>
        ))}
      </section>

      <section className="grid flex-1 gap-10 py-10 lg:grid-cols-[minmax(0,1.1fr)_360px]">
        <CreateRunForm />
        <RecentRunsPanel />
      </section>
    </SiteChrome>
  );
}
