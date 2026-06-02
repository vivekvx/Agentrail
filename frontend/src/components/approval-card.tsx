import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import type { JsonObject } from "@/lib/types";

interface ApprovalCardProps {
  approvalPayload: JsonObject | null;
  approvalStatus: string | null;
  disabled?: boolean;
  onApprove: () => void;
  onReject: () => void;
}

function statusVariant(status: string | null) {
  if (status === "approved") {
    return "success";
  }
  if (status === "rejected") {
    return "danger";
  }
  return "warning";
}

export function ApprovalCard({
  approvalPayload,
  approvalStatus,
  disabled,
  onApprove,
  onReject,
}: ApprovalCardProps) {
  const evidenceCount =
    typeof approvalPayload?.evidence_count === "number"
      ? approvalPayload.evidence_count
      : null;

  return (
    <section className="border border-border bg-surface p-5">
      <div className="mb-5">
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          Approval
        </div>
        <h3 className="mt-3 text-lg font-semibold tracking-tight text-[#fafafa]">
          Decision point
        </h3>
      </div>

      <div className="border-t border-border pt-4">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <Badge variant={statusVariant(approvalStatus)}>
            {approvalStatus ?? "awaiting decision"}
          </Badge>
          {evidenceCount !== null ? (
            <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
              {evidenceCount} evidence item(s)
            </span>
          ) : null}
        </div>

        <p className="text-sm leading-7 text-zinc-200">
          {String(approvalPayload?.question ?? "Waiting for approval")}
        </p>
      </div>

      <div className="mt-5 grid grid-cols-2 gap-3 border-t border-border pt-5">
        <Button disabled={disabled} onClick={onApprove}>
          Approve
        </Button>
        <Button disabled={disabled} onClick={onReject} variant="secondary">
          Reject
        </Button>
      </div>
    </section>
  );
}
