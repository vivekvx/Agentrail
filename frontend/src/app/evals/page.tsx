"use client";

import { useEffect, useState } from "react";
import { PlayCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EvalScoreCard } from "@/components/eval-score-card";
import { getEvalScenarios, runEvals, getEvalResults } from "@/lib/api";
import type { EvalResult, EvalScenario } from "@/lib/types";

export default function EvalsPage() {
  const [scenarios, setScenarios] = useState<EvalScenario[]>([]);
  const [results, setResults] = useState<EvalResult[]>([]);
  const [running, setRunning] = useState(false);
  const [loadingResults, setLoadingResults] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void loadData();
  }, []);

  async function loadData() {
    setLoadingResults(true);
    setError(null);
    try {
      const [s, r] = await Promise.all([getEvalScenarios(), getEvalResults()]);
      setScenarios(s);
      setResults(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load eval data");
    } finally {
      setLoadingResults(false);
    }
  }

  async function handleRunAll() {
    setRunning(true);
    setError(null);
    try {
      const newResults = await runEvals();
      setResults((prev) => [...newResults, ...prev]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Eval run failed");
    } finally {
      setRunning(false);
    }
  }

  const passCount = results.filter((r) => r.passed).length;
  const totalCount = results.length;

  return (
    <div className="flex flex-col gap-8 py-8">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-xl font-semibold tracking-tight text-zinc-100">
            Eval Dashboard
          </h1>
          <p className="text-sm text-zinc-500">
            Run quality checks against defined scenarios and track pass rates over time.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => void loadData()}
            disabled={loadingResults || running}
            title="Refresh"
          >
            <RefreshCw className={`size-3.5 ${loadingResults ? "animate-spin" : ""}`} />
          </Button>
          <Button
            variant="accent"
            size="sm"
            onClick={() => void handleRunAll()}
            disabled={running || loadingResults}
          >
            <PlayCircle className="size-3.5" />
            {running ? "Running…" : "Run All Evals"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="rounded-md border border-[var(--danger-border)] bg-[var(--danger-bg)] px-4 py-3 text-sm text-[var(--danger-text)]">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        {/* Scenarios sidebar */}
        <div className="flex flex-col gap-3">
          <h2 className="font-mono text-[11px] uppercase tracking-[0.14em] text-zinc-500">
            Scenarios ({scenarios.length})
          </h2>
          {scenarios.length === 0 && !loadingResults ? (
            <p className="text-sm text-zinc-500">No scenarios registered.</p>
          ) : (
            scenarios.map((s) => (
              <Card key={s.id}>
                <CardContent className="py-3">
                  <p className="text-sm font-medium text-zinc-200">{s.name}</p>
                  {s.description && (
                    <p className="mt-0.5 text-xs text-zinc-500 leading-relaxed">
                      {s.description}
                    </p>
                  )}
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Results */}
        <div className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h2 className="font-mono text-[11px] uppercase tracking-[0.14em] text-zinc-500">
              Recent Results ({totalCount})
            </h2>
            {totalCount > 0 && (
              <Badge variant={passCount === totalCount ? "success" : "warning"}>
                {passCount}/{totalCount} passed
              </Badge>
            )}
          </div>

          {loadingResults ? (
            <div className="flex items-center gap-2 text-sm text-zinc-500">
              <RefreshCw className="size-3.5 animate-spin" />
              Loading…
            </div>
          ) : results.length === 0 ? (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-sm text-zinc-500">No results yet. Run evals to see results here.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="flex flex-col gap-2">
              {results.map((r) => (
                <EvalScoreCard key={r.id} result={r} />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
