"use client";

import { Check, Clipboard, FileText } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { PRDraft } from "@/lib/types";

export function PRDraftCard({
  draft,
  disabled,
  onGenerate,
}: {
  draft: PRDraft | null;
  disabled: boolean;
  onGenerate: () => void;
}) {
  const [copied, setCopied] = useState(false);

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

  return (
    <section className="border-t border-border pt-6">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            PR draft
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#fafafa]">
            Manual pull request export
          </h2>
          <p className="mt-2 max-w-2xl text-sm leading-7 text-zinc-500">
            This does not open a GitHub PR. Copy this into your PR description.
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
        </div>
      </div>

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
