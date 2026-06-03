import { ArrowUpRight, GitBranch } from "lucide-react";
import Link from "next/link";

const navItems = [
  { href: "/", label: "Console" },
  { href: "/workflow", label: "Workflow" },
  { href: "/safety", label: "Safety" },
  { href: "/roadmap", label: "Roadmap" },
];

export function SiteChrome({ children }: { children: React.ReactNode }) {
  return (
    <main className="min-h-screen bg-background">
      <div className="mx-auto flex min-h-screen w-full max-w-[1440px] flex-col px-5 py-5 sm:px-8">
        <header className="sticky top-0 z-20 -mx-5 border-b border-border bg-background/92 px-5 py-4 backdrop-blur sm:-mx-8 sm:px-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <Link className="flex items-center gap-3" href="/">
              <span className="flex size-8 items-center justify-center border border-zinc-700 bg-[#f5f5f5] font-mono text-xs font-semibold text-black">
                AR
              </span>
              <span>
                <span className="block text-sm font-semibold tracking-tight text-zinc-100">
                  Agentrail
                </span>
                <span className="block font-mono text-[10px] uppercase tracking-[0.18em] text-zinc-600">
                  Verification-first agent
                </span>
              </span>
            </Link>

            <nav className="flex flex-wrap items-center gap-1 border border-border bg-[#0d0d0d] p-1">
              {navItems.map((item) => (
                <Link
                  className="px-3 py-2 font-mono text-[11px] uppercase tracking-[0.14em] text-zinc-500 hover:bg-zinc-900 hover:text-zinc-100"
                  href={item.href}
                  key={item.href}
                >
                  {item.label}
                </Link>
              ))}
            </nav>

            <Link
              className="inline-flex h-10 items-center justify-center gap-2 border border-transparent px-4 py-2 text-sm font-medium tracking-tight text-zinc-300 hover:border-border hover:bg-[#111111] hover:text-white"
              href="https://github.com/vivekvx/Agentrail"
              target="_blank"
            >
              <GitBranch className="size-4" />
              GitHub
              <ArrowUpRight className="size-4" />
            </Link>
          </div>
        </header>

        {children}
      </div>
    </main>
  );
}
