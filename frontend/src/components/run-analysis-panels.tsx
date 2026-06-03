import type { JsonObject } from "@/lib/types";

function asRecord(value: JsonObject | null) {
  return value ?? null;
}

function summaryText(value: unknown) {
  return typeof value === "string" && value.length > 0 ? value : "";
}

function listFromUnknown(value: unknown) {
  return Array.isArray(value) ? value : [];
}

function RawDetails({ value }: { value: JsonObject | null }) {
  if (!value) {
    return null;
  }

  return (
    <details className="mt-4 border-t border-border pt-4">
      <summary className="cursor-pointer font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
        Raw detail
      </summary>
      <pre className="scrollbar-thin mt-4 max-h-64 overflow-auto bg-[#0d0d0d] p-4 font-mono text-xs leading-6 text-zinc-300">
        <code>{JSON.stringify(value, null, 2)}</code>
      </pre>
    </details>
  );
}

export function VerificationPanel({
  verificationResult,
}: {
  verificationResult: JsonObject | null;
}) {
  const result = asRecord(verificationResult);
  const checks = listFromUnknown(result?.checks);

  return (
    <section className="border-t border-border pt-6">
      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
        Verification
      </div>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <h2 className="text-2xl font-semibold tracking-tight text-[#fafafa]">
          Verification outcome
        </h2>
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          {summaryText(result?.confidence)
            ? `${summaryText(result?.confidence)} confidence`
            : "Waiting for verification"}
        </div>
      </div>
      <p className="mt-2 text-sm leading-7 text-zinc-500">
        {summaryText(result?.summary) || "Verification has not run yet."}
      </p>

      <div className="mt-5 grid gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border pb-3">
          <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Status
          </span>
          <span className="text-sm text-zinc-100">
            {summaryText(result?.status) || "Waiting"}
          </span>
        </div>

        {checks.length > 0 ? (
          <div className="space-y-3">
            {checks.map((check, index) => {
              const item =
                typeof check === "object" && check !== null
                  ? (check as Record<string, unknown>)
                  : null;

              return (
                <div className="border-b border-border pb-3" key={index}>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <span className="text-sm text-zinc-100">
                      {summaryText(item?.name)}
                    </span>
                    <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                      {summaryText(item?.status)}
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-zinc-500">
                    {summaryText(item?.details)}
                  </p>
                </div>
              );
            })}
          </div>
        ) : (
          <div className="border-b border-border pb-3 text-sm text-zinc-500">
            Verification has not run yet.
          </div>
        )}
      </div>

      <RawDetails value={verificationResult} />
    </section>
  );
}

export function RiskPanel({ riskScore }: { riskScore: JsonObject | null }) {
  const result = asRecord(riskScore);
  const factors = listFromUnknown(result?.factors);

  return (
    <section className="border-t border-border pt-6">
      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
        Risk score
      </div>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <h2 className="text-2xl font-semibold tracking-tight text-[#fafafa]">
          Residual risk
        </h2>
        <div className="text-right">
          <div className="text-3xl font-semibold tracking-tight text-[#fafafa]">
            {typeof result?.score === "number" ? result.score : "--"}
          </div>
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            {summaryText(result?.level) || "Waiting"}
          </div>
        </div>
      </div>
      <p className="mt-2 text-sm leading-7 text-zinc-500">
        {summaryText(result?.summary) || "Risk score appears after verification."}
      </p>

      <div className="mt-5 space-y-3">
        {factors.length > 0 ? (
          factors.map((factor, index) => {
            const item =
              typeof factor === "object" && factor !== null
                ? (factor as Record<string, unknown>)
                : null;

            return (
              <div className="border-b border-border pb-3" key={index}>
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <span className="text-sm text-zinc-100">
                    {summaryText(item?.name)}
                  </span>
                  <span className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                    {summaryText(item?.impact)}
                  </span>
                </div>
                <p className="mt-2 text-sm leading-6 text-zinc-500">
                  {summaryText(item?.details)}
                </p>
              </div>
            );
          })
        ) : (
          <div className="border-b border-border pb-3 text-sm text-zinc-500">
            Risk score appears after verification.
          </div>
        )}
      </div>

      {typeof result?.recommended_action === "string" ? (
        <p className="mt-4 text-sm leading-7 text-zinc-300">
          {result.recommended_action}
        </p>
      ) : null}

      <RawDetails value={riskScore} />
    </section>
  );
}

export function TestResultPanel({ testResult }: { testResult: JsonObject | null }) {
  const result = asRecord(testResult);
  const stdout =
    typeof result?.stdout === "string" && result.stdout.length > 0
      ? result.stdout
      : null;
  const stderr =
    typeof result?.stderr === "string" && result.stderr.length > 0
      ? result.stderr
      : null;
  const provider =
    result?.provider === "e2b"
      ? "E2B Sandbox"
      : result?.provider === "local"
        ? "Local Runner"
        : "Waiting";

  return (
    <section className="border-t border-border pt-6">
      <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
        Test result
      </div>
      <div className="mt-3 flex flex-wrap items-end justify-between gap-4">
        <h2 className="text-2xl font-semibold tracking-tight text-[#fafafa]">
          Verification command
        </h2>
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          {summaryText(result?.status) || "Waiting"}
        </div>
      </div>

      <div className="mt-5 grid gap-3 md:grid-cols-4">
        <div className="border-b border-border pb-3">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Runner
          </div>
          <div className="mt-2 text-sm text-zinc-100">{provider}</div>
        </div>
        <div className="border-b border-border pb-3">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Exit code
          </div>
          <div className="mt-2 text-sm text-zinc-100">
            {typeof result?.exit_code === "number" ? result.exit_code : "Pending"}
          </div>
        </div>
        <div className="border-b border-border pb-3">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Duration
          </div>
          <div className="mt-2 text-sm text-zinc-100">
            {typeof result?.duration_ms === "number"
              ? `${result.duration_ms} ms`
              : "Pending"}
          </div>
        </div>
        <div className="border-b border-border pb-3">
          <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
            Status
          </div>
          <div className="mt-2 text-sm text-zinc-100">
            {summaryText(result?.status) || "Waiting"}
          </div>
        </div>
      </div>

      {stdout || stderr ? (
        <div className="mt-4 grid gap-4">
          {stdout ? (
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                stdout
              </div>
              <pre className="scrollbar-thin mt-3 max-h-48 overflow-auto bg-[#0d0d0d] p-4 font-mono text-xs leading-6 text-zinc-300">
                <code>{stdout}</code>
              </pre>
            </div>
          ) : null}

          {stderr ? (
            <div>
              <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
                stderr
              </div>
              <pre className="scrollbar-thin mt-3 max-h-48 overflow-auto bg-[#0d0d0d] p-4 font-mono text-xs leading-6 text-zinc-300">
                <code>{stderr}</code>
              </pre>
            </div>
          ) : null}
        </div>
      ) : (
        <p className="mt-4 text-sm text-zinc-500">
          Waiting for verification command output.
        </p>
      )}

      <RawDetails value={testResult} />
    </section>
  );
}
