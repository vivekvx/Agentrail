export const API_PREFIX = "/api/agentrail";

export type TreeNode = {
  name: string;
  type: "dir" | "file";
  lang?: string | null;
  children?: TreeNode[];
};

export type RepoSummary = {
  id: number;
  url: string;
  name: string;
  status: "pending" | "scanning" | "ready" | "error";
  default_branch: string | null;
  file_count: number;
  created_at: string;
};

export type RepoDetail = RepoSummary & {
  languages: { name: string; count: number }[];
  tree: TreeNode | null;
  error_message: string | null;
};

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_PREFIX}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    cache: "no-store",
  });
  if (!res.ok) {
    let detail = `Request failed (${res.status})`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      // keep generic detail
    }
    throw new Error(detail);
  }
  return (await res.json()) as T;
}

export function importRepo(url: string) {
  return request<RepoSummary>("/repos", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export function getRepo(id: number | string) {
  return request<RepoDetail>(`/repos/${id}`);
}

export type MapNode = {
  id: string;
  label: string;
  files: number;
  lang: string | null;
  depth: number;
};

export type RepoMap = {
  nodes: MapNode[];
  edges: { source: string; target: string }[];
};

export function getRepoMap(id: number | string) {
  return request<RepoMap>(`/repos/${id}/map`);
}

export type TourStep = { title: string; path: string; explanation: string };

export function getRepoTour(id: number | string, refresh = false) {
  return request<{ steps: TourStep[] }>(`/repos/${id}/tour?refresh=${refresh}`);
}

export type ChatAnswer = { answer: string; sources: string[] };

export function askRepo(id: number | string, question: string) {
  return request<ChatAnswer>(`/repos/${id}/chat`, {
    method: "POST",
    body: JSON.stringify({ question }),
  });
}

export function listRepos(limit = 20) {
  return request<RepoSummary[]>(`/repos?limit=${limit}`);
}
