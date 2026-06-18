"use client";

import { useSyncExternalStore } from "react";
import { Moon, Sun } from "lucide-react";

type Theme = "dark" | "light";

const KEY = "agentrail-theme";
const listeners = new Set<() => void>();

function getTheme(): Theme {
  return (localStorage.getItem(KEY) as Theme) ?? "dark";
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function setTheme(next: Theme): void {
  localStorage.setItem(KEY, next);
  document.documentElement.setAttribute("data-theme", next);
  listeners.forEach((l) => l());
}

export function ThemeToggle() {
  // Server + first client render agree on "dark", then the store reconciles
  // to the persisted value — no hydration mismatch, no setState-in-effect.
  const theme = useSyncExternalStore(subscribe, getTheme, () => "dark" as Theme);

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      aria-label={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className="flex size-9 items-center justify-center rounded-full border border-[var(--hairline)] bg-[var(--surface-card)] text-[var(--ink)] hover:bg-[var(--surface-strong)] active:scale-95"
    >
      {theme === "dark" ? (
        <Sun className="size-4" strokeWidth={1.75} />
      ) : (
        <Moon className="size-4" strokeWidth={1.75} />
      )}
    </button>
  );
}
