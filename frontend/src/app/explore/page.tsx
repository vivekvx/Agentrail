"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowRight, GitBranch, Loader2 } from "lucide-react";
import { SiteChrome } from "@/components/site-chrome";
import { importRepo, listRepos, type RepoSummary } from "@/lib/api";
import { useHeroIntro } from "@/lib/motion";

const SAMPLES = [
  "https://github.com/pallets/flask",
  "https://github.com/tiangolo/fastapi",
  "https://github.com/vivekvx/Agentrail",
];

const STATUS_LABEL: Record<RepoSummary["status"], string> = {
  pending: "queued",
  scanning: "scanning",
  ready: "ready",
  error: "failed",
};

export default function ExplorePage() {
  const router = useRouter();
  const heroRef = useRef<HTMLElement>(null);
  useHeroIntro(heroRef);

  const [url, setUrl] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [recent, setRecent] = useState<RepoSummary[]>([]);

  useEffect(() => {
    listRepos(8).then(setRecent).catch(() => setRecent([]));
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const repo = await importRepo(url.trim());
      router.push(`/repo/${repo.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Import failed");
      setLoading(false);
    }
  }

  return (
    <SiteChrome>
      <section ref={heroRef} className="mx-auto w-full max-w-[760px] px-6 py-20">
        <span data-hero className="eyebrow">
          Import a repository
        </span>
        <h1 data-hero className="display mt-5 text-[clamp(2.1rem,4vw,3.2rem)]">
          Point Agentrail at a codebase.
        </h1>
        <p data-hero className="mt-4 max-w-lg text-[16px] leading-7 text-[var(--body)]">
          Paste a public GitHub URL. Agentrail clones it, walks the file tree,
          and detects the stack, then hands you a map to explore.
        </p>

        <form data-hero onSubmit={submit} className="mt-9">
          <div className="flex flex-col gap-3 sm:flex-row">
            <div className="flex h-12 flex-1 items-center gap-2.5 rounded-md border border-[var(--hairline)] bg-[var(--surface-card)] px-3.5 focus-within:border-[var(--accent-border)]">
              <GitBranch className="size-4 shrink-0 text-[var(--muted)]" strokeWidth={1.75} />
              <input
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                placeholder="https://github.com/owner/repo"
                className="h-full w-full bg-transparent font-mono text-[14px] text-[var(--ink)] outline-none placeholder:text-[var(--muted-soft)]"
                autoComplete="off"
                spellCheck={false}
              />
            </div>
            <button
              type="submit"
              disabled={loading || !url.trim()}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[var(--primary)] px-5 text-sm font-semibold text-[var(--on-primary)] hover:bg-[var(--primary-active)] disabled:opacity-50 active:translate-y-px"
            >
              {loading ? (
                <Loader2 className="size-4 animate-spin" strokeWidth={2} />
              ) : (
                <>
                  Import
                  <ArrowRight className="size-4" strokeWidth={2} />
                </>
              )}
            </button>
          </div>
          {error && (
            <p className="mt-3 font-mono text-[12px] text-[#f87171]">{error}</p>
          )}
        </form>

        <div data-hero className="mt-5 flex flex-wrap items-center gap-2">
          <span className="font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">
            try
          </span>
          {SAMPLES.map((s) => (
            <button
              key={s}
              onClick={() => setUrl(s)}
              className="rounded-full border border-[var(--hairline)] bg-[var(--surface-card)] px-3 py-1 font-mono text-[11px] text-[var(--body)] hover:border-[var(--accent-border)] hover:text-[var(--ink)]"
            >
              {s.replace("https://github.com/", "")}
            </button>
          ))}
        </div>

        {recent.length > 0 && (
          <div className="mt-14">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
              Recent imports
            </h2>
            <div className="mt-4 divide-y divide-[var(--hairline)] overflow-hidden rounded-xl border border-[var(--hairline)]">
              {recent.map((r) => (
                <Link
                  key={r.id}
                  href={`/repo/${r.id}`}
                  className="flex items-center justify-between px-4 py-3.5 hover:bg-[var(--surface-card)]"
                >
                  <span className="font-mono text-[13px] text-[var(--ink)]">
                    {r.name}
                  </span>
                  <span
                    className={`font-mono text-[11px] ${
                      r.status === "ready"
                        ? "text-[var(--accent)]"
                        : r.status === "error"
                          ? "text-[#f87171]"
                          : "text-[var(--muted)]"
                    }`}
                  >
                    {STATUS_LABEL[r.status]}
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </section>
    </SiteChrome>
  );
}
