"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { loginUser } from "@/lib/api";
import { saveToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const { access_token } = await loginUser(email, password);
      saveToken(access_token);
      router.replace("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link
            href="/"
            className="inline-flex items-center gap-2 mb-6 group"
          >
            <span className="flex size-8 items-center justify-center border border-[var(--accent-border)] bg-[var(--accent-dim)] font-mono text-xs font-bold text-[var(--accent)] rounded-sm group-hover:bg-[rgba(16,185,129,0.15)] transition">
              AR
            </span>
            <span className="text-sm font-semibold tracking-tight text-zinc-100">
              Agentrail
            </span>
          </Link>
          <h1 className="text-xl font-semibold text-zinc-100">Sign in</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Enter your credentials to continue
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label
              htmlFor="email"
              className="block font-mono text-[11px] uppercase tracking-[0.12em] text-zinc-500"
            >
              Email
            </label>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              required
              placeholder="you@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <label
              htmlFor="password"
              className="block font-mono text-[11px] uppercase tracking-[0.12em] text-zinc-500"
            >
              Password
            </label>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {error && (
            <p className="rounded-sm border border-[var(--danger-border)] bg-[var(--danger-bg)] px-3 py-2 font-mono text-[11px] text-[var(--danger-text)]">
              {error}
            </p>
          )}

          <Button
            type="submit"
            variant="accent"
            className="w-full"
            disabled={loading}
          >
            {loading ? "Signing in…" : "Sign in"}
          </Button>
        </form>

        <p className="mt-6 text-center font-mono text-[11px] text-zinc-500">
          No account?{" "}
          <Link
            href="/register"
            className="text-[var(--accent)] hover:text-emerald-400 transition"
          >
            Register
          </Link>
        </p>
      </div>
    </main>
  );
}
