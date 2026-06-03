# Agentrail Safety Model

## Scope

Agentrail is a local/portfolio MVP with production-minded safety design. It is intended to make AI-assisted bug fixing more inspectable and reviewable, not to replace code review or CI.

## Threat Model

Agentrail treats these inputs as untrusted:

- Repository contents
- User tasks
- Model output
- Test command output
- GitHub repository URLs
- GitHub issue URLs and issue bodies
- Files copied into optional sandbox execution

Primary risks:

- Running dangerous commands from a repository.
- Leaking tokens or secrets through logs, reports, or API payloads.
- Trusting unsupported AI claims.
- Applying changes without human review.
- Uploading sensitive files to a sandbox.
- Confusing a patch preview with an applied fix.

## What the Agent Can Do

- Accept a local repository path or public GitHub repository URL.
- Accept a public GitHub issue URL and import issue context read-only.
- Scan repository structure.
- Search code and gather line-numbered evidence.
- Produce root-cause analysis.
- Produce a fix strategy.
- Generate a patch preview.
- Pause for approval.
- Run allowlisted verification commands after approval.
- Produce verification, risk scoring, timeline events, and final reports.

## What the Agent Cannot Do

- It cannot apply patches to the original repository.
- It cannot create commits.
- It cannot open pull requests.
- It cannot comment on GitHub issues.
- It cannot close or edit GitHub issues.
- It cannot run arbitrary shell commands.
- It cannot safely handle private GitHub repositories as part of the MVP.
- It cannot claim production readiness.
- It cannot prove correctness without evidence and verification.

## Patch Preview Policy

- Patch generation produces reviewable diffs only.
- The original repository is not modified.
- Patch preview and approval state are persisted for review.
- Rejected patches are reported as rejected and should not be trusted.

## Approval Policy

- The LangGraph workflow pauses at the approval node.
- The user must approve or reject before the workflow resumes.
- Approved runs may proceed to test execution.
- Rejected runs skip test execution and produce a report explaining rejection.

## Command Execution Policy

Allowed commands:

- `pytest`
- `python -m pytest`
- `npm test`
- `npm run test`
- `npm run lint`
- `npm run build`
- `pnpm test`
- `yarn test`

Blocked patterns include:

- `rm -rf`
- `sudo`
- `curl | bash`
- `wget | bash`
- `chmod -R`
- `chown -R`
- `dd`
- `mkfs`
- `shutdown`
- `reboot`
- `kill`

Local command execution uses `shell=False`, validates repository paths, captures stdout/stderr, and returns structured results.

## GitHub Import Safety

- Public GitHub repository URLs are validated.
- Import is read-only.
- Imported repositories are cloned into a controlled workspace.
- No commits, pushes, or pull requests are created.
- Optional GitHub token values must not appear in API responses, timeline events, or reports.
- Private repository support is not part of the MVP.

## GitHub Issue Import Safety

- Public GitHub issue URLs are validated.
- Pull request URLs are rejected for now.
- Issue import is read-only.
- Agentrail does not comment on issues.
- Agentrail does not close, reopen, label, assign, or edit issues.
- Agentrail does not create pull requests.
- GitHub token use is optional for public issues and must not be logged.
- Issue body content is truncated before entering run context.
- Timeline payloads include issue metadata only: owner, repo, issue number, issue URL, labels, and state.

## E2B Sandbox Safety

- Local safe runner remains the default.
- E2B is optional and requires explicit configuration.
- The E2B SDK is imported lazily so local development does not require it.
- Missing SDK or missing API key returns a clean error.
- Commands still use the same allowlist.
- Sandbox archives exclude known secret-like files and heavy generated folders.
- Sandbox ID may be reported; API keys are never reported.

Excluded upload paths include:

- `.git`
- `node_modules`
- `.venv`
- `venv`
- `__pycache__`
- `dist`
- `build`
- `.next`
- `coverage`
- `.env`
- `.env.*`
- `secrets.*`
- `*.pem`
- `*.key`

## Secret Handling

- `.env` style files are excluded from evidence reading and sandbox upload paths.
- API keys are configuration-only and should not be printed.
- Error sanitization masks absolute paths and token-like strings in API-facing errors.
- Final reports should summarize results without exposing private filesystem internals or tokens.

## Error Sanitization

Sanitization goals:

- Replace absolute private paths where appropriate.
- Remove raw traceback markers from public error messages.
- Mask GitHub token-like strings.
- Replace E2B API key values with `[secret]` in sandbox errors.

## Known Limitations

- This is not a production security boundary.
- The local runner still executes allowed commands on the host machine.
- E2B isolation depends on correct configuration and available SDK/API access.
- The system does not apply patches, so verification may validate the current repository state rather than an applied patch.
- Private GitHub repository support is not included.
- Evaluation benchmarks are planned but not yet implemented.
- Durable LangGraph checkpointing beyond the current local memory setup is planned for later.
