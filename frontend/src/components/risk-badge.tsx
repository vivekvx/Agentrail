import { Badge } from "@/components/ui/badge";

type RiskLevel = "low" | "medium" | "high";

const variantByLevel: Record<RiskLevel, "neutral" | "success" | "warning" | "danger"> = {
  low: "success",
  medium: "warning",
  high: "danger",
};

export function RiskBadge({ level }: { level?: string | null }) {
  const normalized =
    level === "low" || level === "medium" || level === "high" ? level : "low";
  return <Badge variant={variantByLevel[normalized]}>{normalized} risk</Badge>;
}
