import { Badge } from "@/components/ui/badge";
import type { RunStatus } from "@/lib/types";

const variantByStatus: Record<RunStatus, "neutral" | "success" | "warning" | "danger"> = {
  created: "neutral",
  running: "warning",
  pending_approval: "warning",
  completed: "success",
  rejected: "danger",
  failed: "danger",
};

export function StatusBadge({ status }: { status: RunStatus }) {
  return <Badge variant={variantByStatus[status]}>{status.replace("_", " ")}</Badge>;
}
