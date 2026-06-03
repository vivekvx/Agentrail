const STORAGE_KEY = "agentrail-recent-runs";

export function loadRecentRunIds(): number[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed
      .map((value) => Number(value))
      .filter((value) => Number.isInteger(value) && value > 0);
  } catch {
    return [];
  }
}

export function saveRecentRunId(runId: number) {
  if (typeof window === "undefined") {
    return;
  }

  const next = [runId, ...loadRecentRunIds().filter((id) => id !== runId)].slice(
    0,
    8,
  );
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
}
