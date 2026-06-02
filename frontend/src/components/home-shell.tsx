import { CreateRunForm } from "@/components/create-run-form";
import { RecentRunsPanel } from "@/components/recent-runs-panel";

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
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen w-full max-w-[1400px] flex-col px-5 py-6 sm:px-8">
        <header className="border-b border-border pb-8">
          <div className="mb-5 flex flex-wrap items-center gap-3">
            <span className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.22em] text-zinc-400">
              DevPilot Verify
            </span>
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
              Repository verification system
            </span>
          </div>

          <div className="grid gap-8 lg:grid-cols-[minmax(0,1.15fr)_320px] lg:items-end">
            <div className="max-w-4xl">
              <h1 className="max-w-3xl text-balance text-4xl font-semibold tracking-tight text-[#fafafa] sm:text-5xl">
                Review an agent run like an engineering artifact, not a chat.
              </h1>
              <p className="mt-4 max-w-2xl text-base leading-8 text-[#a1a1aa]">
                DevPilot Verify inspects a repository, builds evidence, proposes
                a patch, pauses for approval, verifies the result, scores the
                residual risk, and leaves an auditable trail behind.
              </p>
            </div>

            <div className="space-y-3">
              <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                Workflow
              </div>
              <div className="flex flex-wrap gap-2">
                {workflowStages.map((stage) => (
                  <span
                    className="rounded-sm border border-border px-2 py-1 font-mono text-[11px] uppercase tracking-[0.16em] text-zinc-400"
                    key={stage}
                  >
                    {stage}
                  </span>
                ))}
              </div>
            </div>
          </div>
        </header>

        <section className="grid flex-1 gap-10 pt-8 lg:grid-cols-[minmax(0,1.1fr)_360px]">
          <CreateRunForm />
          <RecentRunsPanel />
        </section>
      </div>
    </main>
  );
}
