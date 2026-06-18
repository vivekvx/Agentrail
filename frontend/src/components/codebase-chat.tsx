"use client";

import { useState } from "react";
import { ArrowUp, Loader2 } from "lucide-react";
import { askRepo, type ChatAnswer } from "@/lib/api";

type Turn = { q: string; a: ChatAnswer | null; error?: string };

export function CodebaseChat({ repoId }: { repoId: string }) {
  const [turns, setTurns] = useState<Turn[]>([]);
  const [q, setQ] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const question = q.trim();
    if (!question || busy) return;
    setQ("");
    setBusy(true);
    setTurns((t) => [...t, { q: question, a: null }]);
    try {
      const a = await askRepo(repoId, question);
      setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, a } : turn)));
    } catch (err) {
      const error = err instanceof Error ? err.message : "Chat failed";
      setTurns((t) => t.map((turn, i) => (i === t.length - 1 ? { ...turn, error } : turn)));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="rounded-xl border border-[var(--hairline)] bg-[var(--surface-card)]">
      <div className="max-h-[460px] space-y-5 overflow-auto p-5">
        {turns.length === 0 && (
          <p className="font-mono text-[13px] text-[var(--muted)]">
            Ask anything about this codebase — answers cite the files they come
            from. Needs Ollama running and the repo indexed on import.
          </p>
        )}
        {turns.map((t, i) => (
          <div key={i} className="space-y-2">
            <div className="text-[14px] font-semibold text-[var(--ink)]">{t.q}</div>
            {t.a === null && !t.error && (
              <div className="flex items-center gap-2 font-mono text-[12px] text-[var(--muted)]">
                <Loader2 className="size-3.5 animate-spin" strokeWidth={2} />
                thinking…
              </div>
            )}
            {t.error && (
              <div className="font-mono text-[12px] text-[#f87171]">{t.error}</div>
            )}
            {t.a && (
              <div>
                <p className="whitespace-pre-wrap text-[14px] leading-6 text-[var(--body)]">
                  {t.a.answer}
                </p>
                {t.a.sources.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {t.a.sources.map((s) => (
                      <span
                        key={s}
                        className="rounded-full border border-[var(--hairline)] px-2.5 py-0.5 font-mono text-[11px] text-[var(--muted)]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      <form onSubmit={submit} className="flex gap-2 border-t border-[var(--hairline)] p-3">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          placeholder="where is auth handled?"
          className="h-10 flex-1 rounded-md border border-[var(--hairline)] bg-[var(--canvas)] px-3 text-[14px] text-[var(--ink)] outline-none focus:border-[var(--accent-border)]"
        />
        <button
          type="submit"
          disabled={busy || !q.trim()}
          className="flex size-10 items-center justify-center rounded-md bg-[var(--primary)] text-[var(--on-primary)] hover:bg-[var(--primary-active)] disabled:opacity-50"
        >
          <ArrowUp className="size-4" strokeWidth={2.5} />
        </button>
      </form>
    </div>
  );
}
