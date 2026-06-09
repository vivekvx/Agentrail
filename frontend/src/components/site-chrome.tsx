"use client";

import { GitBranch, LogOut, User } from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { clearToken, isAuthenticated } from "@/lib/auth";

const navItems = [
  { href: "/", label: "Console" },
  { href: "/runs", label: "Runs" },
  { href: "/workflow", label: "Workflow" },
  { href: "/safety", label: "Safety" },
  { href: "/evals", label: "Evals" },
  { href: "/roadmap", label: "Roadmap" },
];

function NavLink({ href, label }: { href: string; label: string }) {
  const pathname = usePathname();
  const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
  return (
    <Link
      className={`px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.14em] transition rounded-sm ${
        active
          ? "text-zinc-100 bg-[rgba(16,185,129,0.08)] border border-[rgba(16,185,129,0.18)]"
          : "text-zinc-500 border border-transparent hover:bg-zinc-900 hover:text-zinc-200"
      }`}
      href={href}
    >
      {label}
    </Link>
  );
}

export function SiteChrome({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [authed, setAuthed] = useState(false);

  useEffect(() => {
    const authenticated = isAuthenticated();
    setAuthed(authenticated);
    if (!authenticated) {
      router.replace("/login");
    }
  }, [router]);

  function handleLogout() {
    clearToken();
    setAuthed(false);
    router.replace("/login");
  }

  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-5 py-5 sm:px-8">
        <header className="sticky top-0 z-20 -mx-5 border-b border-[var(--border)] bg-[rgba(8,8,8,0.94)] px-5 py-3 backdrop-blur sm:-mx-8 sm:px-8">
          <div className="flex items-center justify-between gap-4">
            <Link className="flex items-center gap-3 group" href="/">
              <span className="flex size-8 items-center justify-center border border-[var(--accent-border)] bg-[var(--accent-dim)] font-mono text-xs font-bold text-[var(--accent)] rounded-sm group-hover:bg-[rgba(16,185,129,0.15)] transition">
                AR
              </span>
              <span className="text-sm font-semibold tracking-tight text-zinc-100">
                Agentrail
              </span>
            </Link>

            <nav className="flex items-center gap-0.5">
              {navItems.map((item) => (
                <NavLink href={item.href} key={item.href} label={item.label} />
              ))}
            </nav>

            <div className="flex items-center gap-2">
              <Link
                className="inline-flex h-8 items-center justify-center gap-1.5 rounded-sm border border-[var(--border)] px-3 font-mono text-[11px] uppercase tracking-[0.12em] text-zinc-500 hover:border-zinc-600 hover:text-zinc-200 transition"
                href="https://github.com/vivekvx/Agentrail"
                target="_blank"
              >
                <GitBranch className="size-3.5" />
                GitHub
              </Link>

              {authed ? (
                <button
                  onClick={handleLogout}
                  className="inline-flex h-8 items-center justify-center gap-1.5 rounded-sm border border-[var(--border)] px-3 font-mono text-[11px] uppercase tracking-[0.12em] text-zinc-500 hover:border-zinc-600 hover:text-zinc-200 transition"
                  title="Sign out"
                >
                  <User className="size-3.5" />
                  <LogOut className="size-3.5" />
                </button>
              ) : (
                <Link
                  href="/login"
                  className="inline-flex h-8 items-center justify-center gap-1.5 rounded-sm border border-[var(--border)] px-3 font-mono text-[11px] uppercase tracking-[0.12em] text-zinc-500 hover:border-zinc-600 hover:text-zinc-200 transition"
                >
                  Sign in
                </Link>
              )}
            </div>
          </div>
        </header>

        {children}
      </div>
    </main>
  );
}
