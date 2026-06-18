"use client";

import { use, useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  ChevronRight,
  File,
  Folder,
  GitBranch,
  Loader2,
  TriangleAlert,
} from "lucide-react";
import { SiteChrome } from "@/components/site-chrome";
import { CodebaseMap } from "@/components/codebase-map";
import { CodebaseTour } from "@/components/codebase-tour";
import { CodebaseChat } from "@/components/codebase-chat";
import { getRepo, type RepoDetail, type TreeNode } from "@/lib/api";

const POLL_MS = 1500;

function TreeView({ node, depth = 0 }: { node: TreeNode; depth?: number }) {
  const [open, setOpen] = useState(depth < 1);
  const isDir = node.type === "dir";
  const pad = { paddingLeft: `${depth * 14}px` };

  if (!isDir) {
    return (
      <div
        style={pad}
        className="flex items-center gap-2 py-1 font-mono text-[12.5px] text-[var(--body)]"
      >
        <File className="size-3.5 shrink-0 text-[var(--muted-soft)]" strokeWidth={1.5} />
        {node.name}
      </div>
    );
  }

  const children = node.children ?? [];
  return (
    <div>
      <button
        style={pad}
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center gap-1.5 py-1 font-mono text-[12.5px] text-[var(--ink)] hover:text-[var(--accent)]"
      >
        <ChevronRight
          className={`size-3.5 shrink-0 text-[var(--muted)] transition-transform ${open ? "rotate-90" : ""}`}
          strokeWidth={2}
        />
        <Folder className="size-3.5 shrink-0 text-[var(--accent)]" strokeWidth={1.5} />
        {node.name}
      </button>
      {open &&
        children.map((c, i) => (
          <TreeView key={`${c.name}-${i}`} node={c} depth={depth + 1} />
        ))}
    </div>
  );
}

export default function RepoPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [repo, setRepo] = useState<RepoDetail | null>(null);
  const [fatal, setFatal] = useState<string | null>(null);
  const [view, setView] = useState<"map" | "tour" | "chat" | "tree">("map");
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    let active = true;
    async function poll() {
      try {
        const data = await getRepo(id);
        if (!active) return;
        setRepo(data);
        if (data.status === "ready" || data.status === "error") return;
        timer.current = setTimeout(poll, POLL_MS);
      } catch (err) {
        if (active) setFatal(err instanceof Error ? err.message : "Failed to load repo");
      }
    }
    poll();
    return () => {
      active = false;
      if (timer.current) clearTimeout(timer.current);
    };
  }, [id]);

  const scanning = repo && (repo.status === "pending" || repo.status === "scanning");

  return (
    <SiteChrome>
      <section className="mx-auto w-full max-w-[1000px] px-6 py-14">
        <Link
          href="/explore"
          className="font-mono text-[12px] text-[var(--muted)] hover:text-[var(--ink)]"
        >
          ← back to import
        </Link>

        {fatal && (
          <div className="mt-8 rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-6 font-mono text-[13px] text-[#f87171]">
            {fatal}
          </div>
        )}

        {repo && (
          <>
            <div className="mt-6 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <GitBranch className="size-5 text-[var(--accent)]" strokeWidth={1.75} />
                <h1 className="display text-[clamp(1.6rem,3vw,2.2rem)]">
                  {repo.name}
                </h1>
              </div>
              <span
                className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 font-mono text-[11px] ${
                  repo.status === "ready"
                    ? "border-[var(--accent-border)] bg-[var(--accent-soft)] text-[var(--accent)]"
                    : repo.status === "error"
                      ? "border-[rgba(248,113,113,0.3)] text-[#f87171]"
                      : "border-[var(--hairline)] text-[var(--muted)]"
                }`}
              >
                {scanning && <Loader2 className="size-3 animate-spin" strokeWidth={2} />}
                {repo.status}
              </span>
            </div>

            {repo.status === "error" && (
              <div className="mt-8 flex items-start gap-3 rounded-xl border border-[rgba(248,113,113,0.3)] bg-[var(--surface-card)] p-5">
                <TriangleAlert className="mt-0.5 size-4 shrink-0 text-[#f87171]" strokeWidth={1.75} />
                <p className="font-mono text-[13px] leading-6 text-[var(--body)]">
                  {repo.error_message ?? "Scan failed."}
                </p>
              </div>
            )}

            {scanning && (
              <div className="mt-10 rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-8 text-center">
                <Loader2 className="mx-auto size-6 animate-spin text-[var(--accent)]" strokeWidth={2} />
                <p className="mt-4 font-mono text-[13px] text-[var(--muted)]">
                  Cloning and scanning {repo.name}…
                </p>
              </div>
            )}

            {repo.status === "ready" && (
              <>
                {/* Stats */}
                <div className="mt-8 grid grid-cols-2 gap-4 sm:grid-cols-3">
                  <Stat label="Files" value={repo.file_count.toLocaleString()} />
                  <Stat label="Branch" value={repo.default_branch ?? "—"} />
                  <Stat label="Languages" value={String(repo.languages.length)} />
                </div>

                {/* Stack */}
                {repo.languages.length > 0 && (
                  <div className="mt-10">
                    <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                      Detected stack
                    </h2>
                    <div className="mt-4 flex flex-wrap gap-2">
                      {repo.languages.map((l) => (
                        <span
                          key={l.name}
                          className="inline-flex items-center gap-2 rounded-full border border-[var(--hairline)] bg-[var(--surface-card)] px-3 py-1.5 text-[13px] text-[var(--ink)]"
                        >
                          {l.name}
                          <span className="font-mono text-[11px] text-[var(--muted)]">
                            {l.count}
                          </span>
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Map / Tree */}
                {repo.tree && (
                  <div className="mt-10">
                    <div className="flex items-center justify-between">
                      <h2 className="font-mono text-[11px] uppercase tracking-[0.18em] text-[var(--muted)]">
                        Codebase
                      </h2>
                      <div className="flex gap-1 rounded-lg border border-[var(--hairline)] bg-[var(--surface-card)] p-1">
                        {(["map", "tour", "chat", "tree"] as const).map((v) => (
                          <button
                            key={v}
                            onClick={() => setView(v)}
                            className={`rounded-md px-3 py-1 font-mono text-[11px] uppercase tracking-[0.12em] transition ${
                              view === v
                                ? "bg-[var(--canvas)] text-[var(--ink)]"
                                : "text-[var(--muted)] hover:text-[var(--ink)]"
                            }`}
                          >
                            {v}
                          </button>
                        ))}
                      </div>
                    </div>
                    <div className="mt-4">
                      {view === "map" && <CodebaseMap repoId={id} />}
                      {view === "tour" && <CodebaseTour repoId={id} />}
                      {view === "chat" && <CodebaseChat repoId={id} />}
                      {view === "tree" && (
                        <div className="max-h-[520px] overflow-auto rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-4 scrollbar-thin">
                          <TreeView node={repo.tree} />
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </>
            )}
          </>
        )}

        {!repo && !fatal && (
          <div className="mt-10 flex items-center gap-3 font-mono text-[13px] text-[var(--muted)]">
            <Loader2 className="size-4 animate-spin" strokeWidth={2} />
            loading…
          </div>
        )}
      </section>
    </SiteChrome>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-5">
      <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-[var(--muted)]">
        {label}
      </div>
      <div className="display mt-2 text-[24px] tracking-[-0.02em]">{value}</div>
    </div>
  );
}
