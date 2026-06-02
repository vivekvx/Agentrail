import { notFound } from "next/navigation";

import { RunDetailShell } from "@/components/run-detail-shell";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const runId = Number(id);

  if (!Number.isInteger(runId) || runId <= 0) {
    notFound();
  }

  return <RunDetailShell runId={runId} />;
}
