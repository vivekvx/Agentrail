import type {
  PRDraft,
  RunCreatePayload,
  RunDetail,
  RunEvent,
  RunStartResponse,
} from "@/lib/types";

const API_PREFIX = "/api/devpilot";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = `Request failed with status ${response.status}`;
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) {
        detail = body.detail;
      }
    } catch {
      // Ignore non-JSON error bodies and keep generic detail.
    }
    throw new Error(detail);
  }

  return (await response.json()) as T;
}

export function createRun(payload: RunCreatePayload) {
  return request<RunDetail>("/runs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function getRun(runId: number | string) {
  return request<RunDetail>(`/runs/${runId}`);
}

export function getRunEvents(runId: number | string) {
  return request<RunEvent[]>(`/runs/${runId}/events`);
}

export function getPrDraft(runId: number | string) {
  return request<PRDraft>(`/runs/${runId}/pr-draft`);
}

export function startRun(runId: number | string) {
  return request<RunStartResponse>(`/runs/${runId}/start`, {
    method: "POST",
  });
}

export function approveRun(runId: number | string) {
  return request<RunStartResponse>(`/runs/${runId}/approve`, {
    method: "POST",
  });
}

export function rejectRun(runId: number | string) {
  return request<RunStartResponse>(`/runs/${runId}/reject`, {
    method: "POST",
  });
}
