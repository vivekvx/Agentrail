import { notFound } from "next/navigation";

import { RunGraphShell } from "@/components/run-graph-shell";

export default async function RunGraphPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const runId = Number(id);

  if (!Number.isInteger(runId) || runId <= 0) {
    notFound();
  }

  return <RunGraphShell runId={runId} />;
}
