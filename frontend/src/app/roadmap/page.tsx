import { SiteChrome } from "@/components/site-chrome";

const completed = [
  "Repo scanner",
  "Evidence reader",
  "Patch preview",
  "Approval interrupt",
  "Local and E2B test runners",
  "Verifier and risk scorer",
  "GitHub issue import",
  "Evaluation suite",
  "PR draft export",
];

const next = [
  "Authenticated GitHub PR creation",
  "CI provider integration",
  "Durable LangGraph checkpointing",
  "Benchmark dashboard",
  "Multi-language framework coverage",
];

export default function RoadmapPage() {
  return (
    <SiteChrome>
      <section className="border-b border-border py-14">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
          Roadmap
        </p>
        <h1 className="mt-4 max-w-4xl text-5xl font-semibold tracking-tight text-zinc-100 sm:text-6xl">
          Portfolio MVP complete. Production work stays explicit.
        </h1>
      </section>

      <section className="grid gap-px bg-border py-px lg:grid-cols-2">
        <RoadmapColumn items={completed} label="Complete" />
        <RoadmapColumn items={next} label="Post-MVP" />
      </section>
    </SiteChrome>
  );
}

function RoadmapColumn({ items, label }: { items: string[]; label: string }) {
  return (
    <div className="bg-background p-6">
      <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
        {label}
      </h2>
      <div className="mt-6 divide-y divide-border">
        {items.map((item) => (
          <div className="flex items-center justify-between gap-4 py-4" key={item}>
            <span className="text-sm text-zinc-200">{item}</span>
            <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-zinc-600">
              {label}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
