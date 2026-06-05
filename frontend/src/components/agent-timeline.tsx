"use client";

import {
  Activity,
  CheckCircle2,
  Clock3,
  ShieldAlert,
  TestTube2,
} from "lucide-react";
import { useEffect, useMemo, useRef } from "react";

import { getWorkflowNodeIdForEventType } from "@/lib/agent-graph";
import type { RunEvent } from "@/lib/types";

function eventIcon(eventType: string) {
  if (eventType.includes("risk")) {
    return ShieldAlert;
  }
  if (eventType.includes("test")) {
    return TestTube2;
  }
  if (
    eventType.includes("completed") ||
    eventType.includes("verified") ||
    eventType.includes("approved")
  ) {
    return CheckCircle2;
  }
  if (
    eventType.includes("approval") ||
    eventType.includes("started") ||
    eventType.includes("created")
  ) {
    return Clock3;
  }
  return Activity;
}

function payloadEntries(payload: RunEvent["payload"]) {
  if (!payload) {
    return [];
  }

  return Object.entries(payload).slice(0, 4);
}

function formatTimestamp(value: string) {
  return new Date(value).toLocaleString([], {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function AgentTimeline({
  events,
  selectedNodeId,
  selectionOrigin,
  selectionVersion,
  onEventSelect,
}: {
  events: RunEvent[];
  selectedNodeId?: string;
  selectionOrigin?: "graph" | "timeline" | null;
  selectionVersion?: number;
  onEventSelect?: (event: RunEvent, nodeId: string) => void;
}) {
  const eventRefs = useRef<Map<number, HTMLButtonElement>>(new Map());

  const highlightedEventIds = useMemo(() => {
    if (!selectedNodeId) {
      return new Set<number>();
    }

    return new Set(
      events
        .filter((event) => getWorkflowNodeIdForEventType(event.event_type) === selectedNodeId)
        .map((event) => event.id),
    );
  }, [events, selectedNodeId]);

  useEffect(() => {
    if (selectionOrigin !== "graph" || highlightedEventIds.size === 0) {
      return;
    }

    const firstId = [...highlightedEventIds][0];
    const element = eventRefs.current.get(firstId);
    element?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [highlightedEventIds, selectionOrigin, selectionVersion]);

  return (
    <section className="border-t border-border pt-5">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Timeline
          </div>
          <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#fafafa]">
            Activity ledger
          </h2>
        </div>
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          {events.length} events
        </div>
      </div>

      {events.length === 0 ? (
        <div className="py-10 text-sm text-zinc-500">Waiting for run events.</div>
      ) : (
        <div className="scrollbar-thin max-h-[calc(100vh-13rem)] overflow-y-auto pr-2">
          {events.map((event, index) => {
            const Icon = eventIcon(event.event_type);
            const entries = payloadEntries(event.payload);
            const isLast = index === events.length - 1;
            const nodeId = getWorkflowNodeIdForEventType(event.event_type);
            const isHighlighted = highlightedEventIds.has(event.id);

            return (
              <button
                className={`grid w-full grid-cols-[36px_minmax(0,1fr)] gap-4 border-b py-5 text-left transition-colors ${
                  isHighlighted
                    ? "border-zinc-500 bg-[#111111]"
                    : "border-border hover:bg-[#101010]"
                }`}
                key={event.id}
                onClick={() => {
                  if (nodeId && onEventSelect) {
                    onEventSelect(event, nodeId);
                  }
                }}
                ref={(element) => {
                  if (element) {
                    eventRefs.current.set(event.id, element);
                  } else {
                    eventRefs.current.delete(event.id);
                  }
                }}
                type="button"
              >
                <div className="relative flex flex-col items-center">
                  <div
                    className={`flex size-8 items-center justify-center rounded-full border ${
                      isHighlighted
                        ? "border-zinc-400 bg-[#151515]"
                        : "border-border bg-surface"
                    }`}
                  >
                    <Icon className="size-4 text-zinc-300" />
                  </div>
                  {!isLast ? (
                    <div className="mt-2 h-full w-px flex-1 bg-border" />
                  ) : null}
                </div>

                <div className="min-w-0">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-3">
                        <h3 className="text-sm font-medium text-zinc-100">
                          {event.title}
                        </h3>
                        <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-600">
                          {event.event_type}
                        </span>
                      </div>
                    </div>
                    <time className="shrink-0 font-mono text-[11px] text-zinc-500">
                      {formatTimestamp(event.created_at)}
                    </time>
                  </div>

                  {event.message ? (
                    <p className="mt-3 max-w-3xl text-sm leading-7 text-zinc-300">
                      {event.message}
                    </p>
                  ) : null}

                  {event.event_type === "evidence_read" &&
                  Array.isArray(event.payload?.evidence) &&
                  (event.payload.evidence as Array<{file_path?: string; snippet?: string; reason?: string}>).length > 0 ? (
                    <div className="mt-4 space-y-2">
                      {(event.payload.evidence as Array<{file_path?: string; snippet?: string; reason?: string}>)
                        .slice(0, 4)
                        .map((item, i) => (
                          <div
                            key={i}
                            className="border border-[var(--border)] bg-[#0a0a0a] rounded-sm p-3"
                          >
                            <div className="font-mono text-[10px] text-[var(--accent)] mb-1 truncate">
                              {item.file_path ?? "unknown"}
                            </div>
                            {item.reason ? (
                              <div className="text-[11px] text-zinc-500 mb-1 truncate">{item.reason}</div>
                            ) : null}
                            {item.snippet ? (
                              <pre className="font-mono text-[10px] text-zinc-400 leading-5 overflow-x-auto max-h-20 scrollbar-thin whitespace-pre-wrap break-all">
                                {item.snippet.slice(0, 300)}
                              </pre>
                            ) : null}
                          </div>
                        ))}
                    </div>
                  ) : entries.length > 0 ? (
                    <div className="mt-4 flex flex-wrap gap-2">
                      {entries.map(([key, value]) => (
                        <span
                          className="font-mono text-[11px] leading-5 text-zinc-500"
                          key={key}
                        >
                          <span className="text-zinc-700">{key}</span>
                          {" = "}
                          {typeof value === "string"
                            ? value
                            : JSON.stringify(value)}
                        </span>
                      ))}
                    </div>
                  ) : null}
                </div>
              </button>
            );
          })}
        </div>
      )}
    </section>
  );
}
