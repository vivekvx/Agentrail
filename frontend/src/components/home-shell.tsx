"use client";

import { useRef } from "react";
import Link from "next/link";
import {
  ArrowRight,
  GitBranch,
  Map,
  MessageSquare,
  Compass,
  GaugeCircle,
  FileText,
} from "lucide-react";
import { useHeroIntro, useRevealOnScroll } from "@/lib/motion";

const langs = ["python", "typescript", "go", "rust", "react", "kubernetes"];

const features = [
  {
    icon: Map,
    title: "Interactive codebase map",
    body: "A live graph of modules, dependencies, and data flow. Click any node to open its files, exports, and key functions.",
    wide: true,
  },
  {
    icon: Compass,
    title: "Guided tours",
    body: "An ordered walkthrough that explains where to start and why, linked to real files and line numbers.",
  },
  {
    icon: MessageSquare,
    title: "Grounded Q&A",
    body: "Ask anything in plain language. Every answer cites the actual code it came from.",
  },
  {
    icon: GaugeCircle,
    title: "Progress tracking",
    body: "See which modules each engineer has explored and what is still uncharted.",
  },
  {
    icon: FileText,
    title: "Living documentation",
    body: "Architecture notes that regenerate as the code changes, so they never go stale.",
    wide: true,
  },
];

const steps = [
  { label: "Connect", body: "Paste a GitHub URL or point at a local repo." },
  { label: "Scan", body: "Agentrail indexes the tree, dependencies, and entry points." },
  { label: "Explore", body: "Walk the tour, open the map, ask questions in chat." },
];

export function HomeShell() {
  const heroRef = useRef<HTMLElement>(null);
  const pageRef = useRef<HTMLDivElement>(null);
  useHeroIntro(heroRef);
  useRevealOnScroll(pageRef);

  return (
    <main className="mx-auto w-full max-w-[1200px] px-6">
      {/* Hero — asymmetric split */}
      <section
        ref={heroRef}
        className="grid items-center gap-14 py-16 lg:grid-cols-[1.15fr_0.85fr] lg:py-24"
      >
        <div>
          <span data-hero className="eyebrow">
            Codebase onboarding agent
          </span>
          <h1
            data-hero
            className="display mt-5 text-[clamp(2.3rem,4.2vw,3.5rem)]"
          >
            Onboard to any codebase in minutes, not weeks.
          </h1>
          <p
            data-hero
            className="mt-6 max-w-md text-[17px] leading-7 text-[var(--body)]"
          >
            Agentrail maps the architecture, writes a guided tour, and answers
            your questions, all grounded in the actual code.
          </p>
          <div data-hero className="mt-8 flex flex-wrap items-center gap-3">
            <Link
              href="/explore"
              className="inline-flex h-11 items-center gap-2 rounded-md bg-[var(--primary)] px-5 text-sm font-semibold text-[var(--on-primary)] hover:bg-[var(--primary-active)] active:translate-y-px"
            >
              Start exploring
              <ArrowRight className="size-4" strokeWidth={2} />
            </Link>
            <a
              href="#how"
              className="inline-flex h-11 items-center rounded-md border border-[var(--hairline)] px-5 text-sm font-semibold text-[var(--ink)] hover:bg-[var(--surface-card)]"
            >
              How it works
            </a>
          </div>
        </div>

        {/* Product-chrome card: module map fragment */}
        <div
          data-hero
          className="rounded-2xl border border-[var(--hairline)] bg-[var(--surface-card)] p-3 shadow-[0_24px_60px_rgba(0,0,0,0.12)]"
        >
          <div className="rounded-xl border border-[var(--hairline)] bg-[var(--canvas)] p-5">
            <div className="flex items-center justify-between">
              <span className="font-mono text-[11px] text-[var(--muted)]">
                api · service · db
              </span>
              <span className="inline-flex items-center gap-1.5 font-mono text-[11px] text-[var(--accent)]">
                <span className="size-1.5 rounded-full bg-[var(--accent)]" />
                indexed
              </span>
            </div>
            <div className="mt-5 grid grid-cols-3 gap-2.5">
              {[
                "routes",
                "auth",
                "models",
                "services",
                "db",
                "tools",
              ].map((n, i) => (
                <div
                  key={n}
                  className="rounded-lg border border-[var(--hairline)] bg-[var(--surface-soft)] px-3 py-4"
                  style={{ opacity: 1 - i * 0.06 }}
                >
                  <div className="size-1.5 rounded-full bg-[var(--accent)]" />
                  <div className="mt-2 font-mono text-[12px] text-[var(--ink)]">
                    {n}
                  </div>
                  <div className="mt-0.5 font-mono text-[10px] text-[var(--muted)]">
                    {3 + i} files
                  </div>
                </div>
              ))}
            </div>
            <div className="mt-5 rounded-lg bg-[var(--surface-soft)] p-3 font-mono text-[12px] leading-6 text-[var(--body)]">
              <span className="text-[var(--muted)]">you</span> where is auth
              handled?
              <br />
              <span className="text-[var(--accent)]">agentrail</span> JWT issued
              in{" "}
              <span className="text-[var(--ink)]">core/security.py:19</span>,
              verified in <span className="text-[var(--ink)]">api/deps.py:14</span>.
            </div>
          </div>
        </div>
      </section>

      {/* Language strip */}
      <section className="border-y border-[var(--hairline)] py-8">
        <p className="text-center font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
          Understands the stacks you already run
        </p>
        <div className="mt-6 flex flex-wrap items-center justify-center gap-x-12 gap-y-6">
          {langs.map((slug) => (
            <span
              key={slug}
              aria-label={slug}
              className="block size-7 bg-[var(--muted)] opacity-70 transition hover:opacity-100"
              style={{
                WebkitMaskImage: `url(https://cdn.simpleicons.org/${slug})`,
                maskImage: `url(https://cdn.simpleicons.org/${slug})`,
                WebkitMaskRepeat: "no-repeat",
                maskRepeat: "no-repeat",
                WebkitMaskSize: "contain",
                maskSize: "contain",
              }}
            />
          ))}
        </div>
      </section>

      <div ref={pageRef}>
        {/* Bento features */}
        <section className="py-24">
          <h2
            data-reveal
            className="display max-w-2xl text-[clamp(2rem,3.5vw,2.8rem)]"
          >
            Everything a new engineer needs to feel at home.
          </h2>
          <div className="mt-12 grid auto-rows-[1fr] grid-cols-1 gap-4 md:grid-cols-2">
            {features.map((f) => {
              const Icon = f.icon;
              return (
                <div
                  data-reveal
                  key={f.title}
                  className={`group rounded-2xl border border-[var(--hairline)] bg-[var(--surface-card)] p-8 transition hover:border-[var(--accent-border)] ${
                    f.wide ? "md:col-span-2" : ""
                  }`}
                >
                  <Icon
                    className="size-6 text-[var(--accent)]"
                    strokeWidth={1.75}
                  />
                  <h3 className="display mt-5 text-[20px] tracking-[-0.02em]">
                    {f.title}
                  </h3>
                  <p className="mt-2 max-w-md text-[15px] leading-6 text-[var(--body)]">
                    {f.body}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* How it works — 3 step columns */}
        <section id="how" className="border-t border-[var(--hairline)] py-24">
          <span data-reveal className="eyebrow">
            Three steps
          </span>
          <h2
            data-reveal
            className="display mt-4 max-w-xl text-[clamp(2rem,3.5vw,2.8rem)]"
          >
            From repository URL to a guided trail.
          </h2>
          <div className="mt-14 grid gap-10 md:grid-cols-3">
            {steps.map((s, i) => (
              <div data-reveal key={s.label}>
                <div className="flex size-10 items-center justify-center rounded-full border border-[var(--hairline)] font-mono text-sm text-[var(--ink)]">
                  {i + 1}
                </div>
                <h3 className="display mt-5 text-[22px] tracking-[-0.02em]">
                  {s.label}
                </h3>
                <p className="mt-2 text-[15px] leading-6 text-[var(--body)]">
                  {s.body}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA band */}
        <section className="py-24">
          <div
            data-reveal
            className="rounded-3xl border border-[var(--hairline)] bg-[var(--surface-card)] px-8 py-16 text-center"
          >
            <h2 className="display mx-auto max-w-xl text-[clamp(1.9rem,3.2vw,2.6rem)]">
              Point it at a repo. Start the tour.
            </h2>
            <p className="mx-auto mt-4 max-w-md text-[15px] leading-6 text-[var(--body)]">
              The fastest way to understand a codebase you did not write.
            </p>
            <Link
              href="/explore"
              className="mt-8 inline-flex h-11 items-center gap-2 rounded-md bg-[var(--primary)] px-6 text-sm font-semibold text-[var(--on-primary)] hover:bg-[var(--primary-active)] active:translate-y-px"
            >
              Start exploring
              <ArrowRight className="size-4" strokeWidth={2} />
            </Link>
          </div>
        </section>
      </div>

      {/* Footer — always dark, closes the page */}
      <footer
        data-theme="dark"
        className="-mx-6 mt-8 rounded-t-3xl bg-[var(--surface-soft)] px-6 py-14"
      >
        <div className="mx-auto flex max-w-[1200px] flex-col items-start justify-between gap-8 sm:flex-row sm:items-center">
          <div className="flex items-center gap-2.5">
            <span className="flex size-7 items-center justify-center rounded-md bg-[var(--surface-invert)] font-mono text-xs font-bold text-[var(--on-invert)]">
              A
            </span>
            <span className="display text-[15px] tracking-[-0.02em]">
              Agentrail
            </span>
          </div>
          <div className="flex items-center gap-6 text-[13px] text-[var(--muted)]">
            <a
              href="https://github.com/vivekvx/Agentrail"
              target="_blank"
              className="inline-flex items-center gap-1.5 hover:text-[var(--ink)]"
            >
              <GitBranch className="size-3.5" strokeWidth={1.75} />
              GitHub
            </a>
            <span>Agent + trail through code</span>
          </div>
        </div>
      </footer>
    </main>
  );
}
