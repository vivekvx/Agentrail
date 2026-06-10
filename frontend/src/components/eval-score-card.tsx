import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import type { EvalResult } from "@/lib/types";

function formatDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function ScoreBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const color =
    pct >= 80
      ? "bg-emerald-500"
      : pct >= 50
        ? "bg-yellow-500"
        : "bg-red-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-24 rounded-full bg-zinc-800 overflow-hidden">
        <div
          className={`h-full rounded-full ${color} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="font-mono text-xs text-zinc-400">{pct}%</span>
    </div>
  );
}

export function EvalScoreCard({ result }: { result: EvalResult }) {
  return (
    <Card className="hover:border-zinc-700 transition-colors">
      <CardContent className="flex items-start justify-between gap-4 py-3">
        <div className="flex flex-col gap-1 min-w-0">
          <span className="text-sm font-medium text-zinc-200 truncate">
            {result.scenario_name}
          </span>
          <ScoreBar score={result.score} />
        </div>
        <div className="flex flex-col items-end gap-1 shrink-0">
          <Badge variant={result.passed ? "success" : "danger"} dot>
            {result.passed ? "Pass" : "Fail"}
          </Badge>
          <span className="font-mono text-[10px] text-zinc-500">
            {formatDate(result.run_at)}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
