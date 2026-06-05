import { ShieldCheck, Lock, Eye, FileX, GitBranch, Copy } from "lucide-react";

import { SiteChrome } from "@/components/site-chrome";

const boundaries = [
  {
    icon: Eye,
    title: "Patch preview only",
    body: "Generated patches are previewed as diffs. No file is written to the repository without explicit developer action.",
  },
  {
    icon: Lock,
    title: "Human approval gate",
    body: "LangGraph interrupts the workflow before verification continues. Every approval is explicit.",
  },
  {
    icon: ShieldCheck,
    title: "Command allowlist",
    body: "Test runner uses shell=False and an allowlist. Arbitrary commands cannot execute.",
  },
  {
    icon: GitBranch,
    title: "Read-only GitHub import",
    body: "Issue and repository imports are read-only API calls. No write tokens are used.",
  },
  {
    icon: FileX,
    title: "Secret-file filtering",
    body: "Files matching secret patterns are filtered before any sandbox upload.",
  },
  {
    icon: Copy,
    title: "Copy-only PR draft",
    body: "PR drafts are copy-ready markdown. No GitHub API write calls are made.",
  },
];

export default function SafetyPage() {
  return (
    <SiteChrome>
      <section className="grid gap-10 border-b border-[var(--border)] py-16 lg:grid-cols-[minmax(0,1fr)_340px] lg:items-center">
        <div>
          <h1 className="max-w-3xl text-balance text-5xl font-semibold tracking-tight text-zinc-100 leading-[1.1] sm:text-6xl">
            Designed for review control, not invisible writes.
          </h1>
          <p className="mt-5 max-w-xl text-base leading-8 text-zinc-500">
            Agentrail keeps every risky action explicit. Patches stay as
            previews. PR drafts stay copy-only. Verification commands stay
            constrained.
          </p>
        </div>
        <div className="border border-[var(--accent-border)] bg-[var(--accent-dim)] rounded-sm p-6">
          <ShieldCheck className="size-7 text-[var(--accent)]" />
          <p className="mt-4 text-sm leading-7 text-zinc-400">
            Six hard boundaries enforced by design. Not by convention.
          </p>
          <div className="mt-5 grid grid-cols-3 gap-2">
            {boundaries.map((b) => (
              <div
                key={b.title}
                className="rounded-sm border border-[var(--border)] bg-[rgba(8,8,8,0.6)] px-2 py-2"
              >
                <div className="size-1.5 rounded-full bg-[var(--success-text)] mb-2" />
                <div className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-zinc-500 leading-tight">
                  {b.title}
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid gap-px bg-[var(--border)] sm:grid-cols-2 lg:grid-cols-3">
        {boundaries.map((item) => {
          const Icon = item.icon;
          return (
            <div className="bg-background p-6 group" key={item.title}>
              <Icon className="size-5 text-zinc-600 mb-4 group-hover:text-[var(--accent)] transition" />
              <h2 className="text-sm font-semibold tracking-tight text-zinc-100">
                {item.title}
              </h2>
              <p className="mt-2 text-sm leading-6 text-zinc-600">{item.body}</p>
            </div>
          );
        })}
      </section>
    </SiteChrome>
  );
}
