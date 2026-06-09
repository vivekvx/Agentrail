import type {
  EvalResult,
  EvalScenario,
  PRDraft,
  RunCreatePayload,
  RunDetail,
  RunEvent,
  RunStartResponse,
} from "@/lib/types";

const API_PREFIX = "/api/agentrail";

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

export function getRuns(limit = 50) {
  return request<RunDetail[]>(`/runs?limit=${limit}`);
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

export function createPR(runId: number, baseBranch = "main"): Promise<{ pr_url: string }> {
  return request<{ pr_url: string }>(`/runs/${runId}/create-pr`, {
    method: "POST",
    body: JSON.stringify({ base_branch: baseBranch }),
  });
}

export function applyPatch(runId: number) {
  return request<{ applied: boolean; output?: string; error?: string }>(
    `/runs/${runId}/apply-patch`,
    { method: "POST" },
  );
}

export function streamRunEvents(
  runId: number,
  onEvent: (event: RunEvent) => void,
  onEnd: () => void,
  onError: (err: Event) => void,
): EventSource {
  const url = `${API_PREFIX}/runs/${runId}/stream`;
  const source = new EventSource(url);

  source.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data as string) as { event_type?: string } & RunEvent;
      if (data.event_type === "stream_end") {
        onEnd();
        source.close();
        return;
      }
      onEvent(data as RunEvent);
    } catch {
      // ignore parse errors
    }
  };

  source.onerror = (err) => {
    onError(err);
    source.close();
  };

  return source;
}

export function getEvalScenarios(): Promise<EvalScenario[]> {
  return request<EvalScenario[]>("/evals/scenarios");
}

export function runEvals(scenarioId?: string): Promise<EvalResult[]> {
  const url = scenarioId
    ? `/evals/run?scenario_id=${encodeURIComponent(scenarioId)}`
    : "/evals/run";
  return request<EvalResult[]>(url, { method: "POST" });
}

export function getEvalResults(limit = 50): Promise<EvalResult[]> {
  return request<EvalResult[]>(`/evals/results?limit=${limit}`);
}

export async function register(
  email: string,
  password: string,
): Promise<{ access_token: string }> {
  const res = await fetch(`${API_PREFIX}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? "Registration failed");
  }
  return res.json() as Promise<{ access_token: string }>;
}

export async function loginUser(
  email: string,
  password: string,
): Promise<{ access_token: string }> {
  const res = await fetch(`${API_PREFIX}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({})) as { detail?: string };
    throw new Error(err.detail ?? "Login failed");
  }
  return res.json() as Promise<{ access_token: string }>;
}
