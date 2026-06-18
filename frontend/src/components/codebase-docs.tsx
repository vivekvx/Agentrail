"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import { Download, Loader2 } from "lucide-react";
import { getRepoMap, getRepoTour, type RepoDetail } from "@/lib/api";

function buildMarkdown(
  repo: RepoDetail,
  modules: { label: string; files: number; lang: string | null }[],
  steps: { title: string; path: string; explanation: string }[],
): string {
  const lines: string[] = [`# ${repo.name}`, ""];

  if (repo.default_branch) lines.push(`Default branch: \`${repo.default_branch}\``, "");
  lines.push(`${repo.file_count.toLocaleString()} files indexed.`, "");

  if (repo.languages.length) {
    lines.push("## Stack", "");
    for (const l of repo.languages) lines.push(`- **${l.name}** — ${l.count} files`);
    lines.push("");
  }

  if (modules.length) {
    lines.push("## Modules", "");
    for (const m of modules)
      lines.push(`- **${m.label}** — ${m.files} files${m.lang ? ` (${m.lang})` : ""}`);
    lines.push("");
  }

  if (steps.length) {
    lines.push("## Guided tour", "");
    steps.forEach((s, i) => {
      lines.push(`### ${String(i + 1).padStart(2, "0")}. ${s.title}`);
      if (s.path) lines.push(`\`${s.path}\``, "");
      if (s.explanation) lines.push(s.explanation, "");
    });
  }

  return lines.join("\n");
}

export function CodebaseDocs({ repo }: { repo: RepoDetail }) {
  const [md, setMd] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      getRepoMap(repo.id),
      getRepoTour(repo.id).catch(() => ({ steps: [] })),
    ])
      .then(([map, tour]) => {
        const modules = map.nodes.filter((n) => n.depth > 0);
        setMd(buildMarkdown(repo, modules, tour.steps));
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to build docs"));
  }, [repo]);

  function download() {
    if (!md) return;
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${repo.name.replace("/", "-")}-docs.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  if (error) {
    return (
      <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-6 font-mono text-[13px] text-[#f87171]">
        {error}
      </div>
    );
  }
  if (!md) {
    return (
      <div className="flex items-center gap-2 rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)] p-6 font-mono text-[13px] text-[var(--muted)]">
        <Loader2 className="size-4 animate-spin" strokeWidth={2} />
        composing docs…
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)]">
      <div className="flex justify-end border-b border-[var(--hairline)] p-3">
        <button
          onClick={download}
          className="inline-flex h-9 items-center gap-2 rounded-md border border-[var(--hairline)] px-3.5 text-[13px] font-semibold text-[var(--ink)] hover:bg-[var(--surface-strong)]"
        >
          <Download className="size-3.5" strokeWidth={2} />
          Download .md
        </button>
      </div>
      <div className="markdown-report max-h-[520px] overflow-auto p-6">
        <ReactMarkdown>{md}</ReactMarkdown>
      </div>
    </div>
  );
}
