"use client";

import { Check, Clipboard, ExternalLink, FileText, Loader2 } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { createPR } from "@/lib/api";
import type { PRDraft } from "@/lib/types";

export function PRDraftCard({
  draft,
  disabled,
  onGenerate,
  runId,
}: {
  draft: PRDraft | null;
  disabled: boolean;
  onGenerate: () => void;
  runId?: number;
}) {
  const [copied, setCopied] = useState(false);
  const [prLoading, setPrLoading] = useState(false);
  const [prUrl, setPrUrl] = useState<string | null>(null);
  const [prError, setPrError] = useState<string | null>(null);

  async function copyDraft() {
    if (!draft) {
      return;
    }
    await navigator.clipboard.writeText(
      `# ${draft.title}\n\n${draft.body_markdown}`,
    );
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  async function openPR() {
    if (!draft || runId == null) return;
    setPrLoading(true);
    setPrError(null);
    try {
      const result = await createPR(runId);
      setPrUrl(result.pr_url);
      window.open(result.pr_url, "_blank", "noopener,noreferrer");
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to create PR";
      if (msg.includes("GITHUB_TOKEN not configured")) {
        setPrError("GITHUB_TOKEN is not configured on the server. Set it in your .env file.");
      } else {
        setPrError(msg);
      }
    } finally {
      setPrLoading(false);
    }
  }

  return (
    <section className="border-t border-border pt-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            PR draft
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#fafafa]">
            Pull request export
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-zinc-500">
            Copy this into your PR description, or open a PR on GitHub directly.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Button disabled={disabled} onClick={onGenerate} variant="secondary">
            <FileText className="size-4" />
            Generate PR Draft
          </Button>
          <Button disabled={!draft} onClick={copyDraft} variant="ghost">
            {copied ? <Check className="size-4" /> : <Clipboard className="size-4" />}
            {copied ? "Copied" : "Copy"}
          </Button>
          {runId != null && (
            prUrl ? (
              <a
                href={prUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-zinc-300 hover:bg-zinc-800 transition-colors"
              >
                <ExternalLink className="size-4" />
                View PR
              </a>
            ) : (
              <Button
                disabled={!draft || prLoading}
                onClick={openPR}
                variant="secondary"
              >
                {prLoading ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <ExternalLink className="size-4" />
                )}
                {prLoading ? "Opening PR..." : "Open PR on GitHub"}
              </Button>
            )
          )}
        </div>
      </div>
      {prError && (
        <p className="mb-4 text-sm text-red-400">{prError}</p>
      )}

      {draft ? (
        <div className="grid gap-4">
          <div className="border border-border bg-surface p-4">
            <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
              Title
            </div>
            <p className="mt-2 text-sm text-zinc-100">{draft.title}</p>
          </div>
          <pre className="scrollbar-thin max-h-[560px] overflow-auto bg-[#0d0d0d] p-5 font-mono text-xs leading-6 text-zinc-300">
            <code>{draft.body_markdown}</code>
          </pre>
        </div>
      ) : (
        <div className="py-6 text-sm text-zinc-500">
          Generate a draft after enough run context exists.
        </div>
      )}
    </section>
  );
}
