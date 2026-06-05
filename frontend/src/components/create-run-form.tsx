"use client";

import { ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import { createRun } from "@/lib/api";
import { saveRecentRunId } from "@/lib/recent-runs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

const DEFAULT_TEST_COMMAND = "python -m pytest";

function Field({
  label,
  description,
  children,
}: {
  label: string;
  description: string;
  children: React.ReactNode;
}) {
  return (
    <div className="grid gap-3 border-t border-border py-5 md:grid-cols-[180px_minmax(0,1fr)] md:gap-8">
      <div>
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          {label}
        </div>
        <p className="mt-2 text-sm leading-6 text-zinc-500">{description}</p>
      </div>
      <div>{children}</div>
    </div>
  );
}

export function CreateRunForm() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [repoPath, setRepoPath] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [issueUrl, setIssueUrl] = useState("");
  const [userTask, setUserTask] = useState("");
  const [expectedBehavior, setExpectedBehavior] = useState("");
  const [testCommand, setTestCommand] = useState(DEFAULT_TEST_COMMAND);

  function onSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    if (repoPath.trim() && repoUrl.trim()) {
      setError("Use either a local repo path or a repo URL, not both.");
      return;
    }
    if (!repoPath.trim() && !repoUrl.trim() && !issueUrl.trim()) {
      setError("Repo path, repo URL, or GitHub issue URL is required.");
      return;
    }
    if (!issueUrl.trim() && !userTask.trim()) {
      setError("User task is required unless a GitHub issue URL is provided.");
      return;
    }

    startTransition(async () => {
      try {
        const run = await createRun({
          repo_path: repoPath.trim() || undefined,
          repo_url: repoUrl.trim() || undefined,
          issue_url: issueUrl.trim() || undefined,
          user_task: userTask.trim() || undefined,
          expected_behavior: expectedBehavior || undefined,
          test_command: testCommand || undefined,
        });
        saveRecentRunId(run.id);
        router.push(`/runs/${run.id}`);
      } catch (submissionError) {
        const message =
          submissionError instanceof Error
            ? submissionError.message
            : "Unable to create run.";
        setError(message);
      }
    });
  }

  return (
    <section className="min-w-0">
      <div className="mb-6 max-w-2xl">
        <div className="font-mono text-[11px] uppercase tracking-[0.18em] text-zinc-500">
          Create run
        </div>
        <h2 className="mt-3 text-2xl font-semibold tracking-tight text-[#fafafa]">
          Open a repository investigation.
        </h2>
        <p className="mt-3 max-w-xl text-sm leading-7 text-[#a1a1aa]">
          Start from a local repository path, public repository URL, or GitHub
          issue URL. The timeline keeps evidence, approval, verification, and
          risk in one place.
        </p>
      </div>

      <form onSubmit={onSubmit}>
        <Field
          description="Absolute local path for the repository you want the agent to inspect."
          label="Repo path"
        >
          <Input
            placeholder="/path/to/your-repo"
            value={repoPath}
            onChange={(event) => {
              setRepoPath(event.target.value);
              if (event.target.value.trim()) setRepoUrl("");
            }}
          />
        </Field>

        <Field
          description="Paste a public GitHub repository URL or use a local repo path."
          label="Repo URL"
        >
          <Input
            placeholder="https://github.com/owner/repo"
            value={repoUrl}
            onChange={(event) => {
              setRepoUrl(event.target.value);
              if (event.target.value.trim()) setRepoPath("");
            }}
          />
        </Field>

        <Field
          description="Paste a GitHub issue URL to prefill repo and task context."
          label="Issue URL"
        >
          <Input
            placeholder="https://github.com/owner/repo/issues/123"
            value={issueUrl}
            onChange={(event) => setIssueUrl(event.target.value)}
          />
        </Field>

        <Field
          description="Describe the issue, investigation goal, or behavior to verify. Optional when using issue URL."
          label="User task"
        >
          <Textarea
            placeholder="Fix auth refresh bug after token reload."
            value={userTask}
            onChange={(event) => setUserTask(event.target.value)}
          />
        </Field>

        <Field
          description="Define the outcome you expect after the issue is resolved."
          label="Expected behavior"
        >
          <Textarea
            placeholder="User should stay signed in after page refresh."
            value={expectedBehavior}
            onChange={(event) => setExpectedBehavior(event.target.value)}
          />
        </Field>

        <Field
          description="Safe local command used after approval for verification."
          label="Test command"
        >
          <Input
            placeholder="python -m pytest"
            value={testCommand}
            onChange={(event) => setTestCommand(event.target.value)}
          />
        </Field>

        {error ? (
          <div className="border-t border-border py-5">
            <div className="rounded-sm border border-border bg-surface px-4 py-3 text-sm text-zinc-300">
              {error}
            </div>
          </div>
        ) : null}

        <div className="flex flex-wrap items-center justify-between gap-4 border-t border-border py-6">
          <p className="max-w-md text-sm leading-6 text-zinc-500">
            Creating a run takes you straight into the activity timeline. Patch
            previews still stop at approval.
          </p>
          <Button className="min-w-44" disabled={isPending} size="lg" type="submit">
            {isPending ? "Creating Run..." : "Create Run"}
            <ArrowRight className="size-4" />
          </Button>
        </div>
      </form>
    </section>
  );
}
