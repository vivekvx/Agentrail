import { SiteChrome } from "@/components/site-chrome";

const steps = [
  ["01", "Scan", "Detect stack, key files, and verification commands."],
  ["02", "Evidence", "Inspect relevant code before making claims."],
  ["03", "Root cause", "Explain why behavior fails with source-backed context."],
  ["04", "Patch preview", "Generate a reviewable diff without mutating the repo."],
  ["05", "Approval", "Pause until a human approves or rejects the preview."],
  ["06", "Verification", "Run allowlisted tests and record output."],
  ["07", "Risk", "Score residual uncertainty with concrete factors."],
  ["08", "PR draft", "Export title, body, checklist, and rollback plan."],
];

export default function WorkflowPage() {
  return (
    <SiteChrome>
      <section className="border-b border-border py-14">
        <div className="max-w-4xl">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Workflow
          </p>
          <h1 className="mt-4 text-5xl font-semibold tracking-tight text-zinc-100 sm:text-6xl">
            Agent runs with gates, evidence, and visible state.
          </h1>
          <p className="mt-5 max-w-2xl text-base leading-7 text-zinc-400">
            Each run moves from repository intake to review-ready output. The
            system favors traceability over silent autonomy.
          </p>
        </div>
      </section>

      <section className="grid gap-px bg-border py-px lg:grid-cols-4">
        {steps.map(([number, title, body]) => (
          <article className="min-h-56 bg-background p-6" key={title}>
            <div className="font-mono text-[11px] text-zinc-500">{number}</div>
            <h2 className="mt-6 text-xl font-semibold tracking-tight text-zinc-100">
              {title}
            </h2>
            <p className="mt-3 text-sm leading-7 text-zinc-400">{body}</p>
          </article>
        ))}
      </section>
    </SiteChrome>
  );
}
