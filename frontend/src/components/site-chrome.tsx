"use client";

import { GitBranch } from "lucide-react";
import Link from "next/link";
import { ThemeToggle } from "@/components/theme-toggle";

export function SiteChrome({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-[100dvh] bg-[var(--canvas)]">
      <header className="sticky top-0 z-30 border-b border-[var(--hairline)] bg-[color-mix(in_srgb,var(--canvas)_88%,transparent)] backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-[1200px] items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-2.5">
            <span className="flex size-7 items-center justify-center rounded-md bg-[var(--surface-invert)] font-mono text-xs font-bold text-[var(--on-invert)]">
              A
            </span>
            <span className="display text-[15px] tracking-[-0.02em]">Agentrail</span>
          </Link>

          <div className="flex items-center gap-2.5">
            <Link
              href="https://github.com/vivekvx/Agentrail"
              target="_blank"
              className="hidden h-9 items-center gap-1.5 rounded-md border border-[var(--hairline)] px-3.5 text-[13px] font-medium text-[var(--body)] hover:bg-[var(--surface-card)] sm:inline-flex"
            >
              <GitBranch className="size-3.5" strokeWidth={1.75} />
              GitHub
            </Link>
            <ThemeToggle />
            <Link
              href="https://github.com/vivekvx/Agentrail"
              target="_blank"
              className="inline-flex h-9 items-center rounded-md bg-[var(--primary)] px-4 text-[13px] font-semibold text-[var(--on-primary)] hover:bg-[var(--primary-active)] active:translate-y-px"
            >
              Get started
            </Link>
          </div>
        </div>
      </header>

      {children}
    </div>
  );
}
