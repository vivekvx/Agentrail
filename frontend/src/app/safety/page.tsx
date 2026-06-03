import { ShieldCheck } from "lucide-react";

import { SiteChrome } from "@/components/site-chrome";

const boundaries = [
  "Patch preview only",
  "Human approval gate",
  "Command allowlist",
  "Read-only GitHub issue import",
  "Secret-like file filtering",
  "Copy-only PR draft export",
];

export default function SafetyPage() {
  return (
    <SiteChrome>
      <section className="grid gap-10 border-b border-border py-14 lg:grid-cols-[minmax(0,1fr)_360px] lg:items-end">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
            Safety model
          </p>
          <h1 className="mt-4 max-w-4xl text-5xl font-semibold tracking-tight text-zinc-100 sm:text-6xl">
            Designed for review control, not invisible repository writes.
          </h1>
        </div>
        <div className="border border-border bg-[#0d0d0d] p-5">
          <ShieldCheck className="size-6 text-zinc-200" />
          <p className="mt-5 text-sm leading-7 text-zinc-500">
            Agentrail keeps risky actions explicit: generated patches stay as
            previews, PR drafts stay copy-only, and verification commands stay
            constrained.
          </p>
        </div>
      </section>

      <section className="grid gap-px bg-border py-px sm:grid-cols-2 lg:grid-cols-3">
        {boundaries.map((item) => (
          <div className="bg-background p-6" key={item}>
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
              Boundary
            </div>
            <h2 className="mt-4 text-xl font-semibold tracking-tight text-zinc-100">
              {item}
            </h2>
          </div>
        ))}
      </section>
    </SiteChrome>
  );
}
