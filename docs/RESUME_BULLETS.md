# DevPilot Verify Resume Bullets

## Short Version

- Built DevPilot Verify, a verification-first AI software engineering agent using FastAPI, LangGraph, Next.js, structured LLM outputs, and optional E2B sandboxing.
- Designed an evidence-backed agent workflow for repo scanning, code search, root-cause analysis, patch preview, approval, test execution, verification, risk scoring, and final reporting.
- Implemented safety guardrails including patch-preview-only workflow, human approval interrupts, command allowlisting, secret filtering, sanitized errors, and read-only GitHub import.

## Detailed Version

- Built DevPilot Verify, a local/portfolio MVP for verification-first AI-assisted bug fixing across FastAPI, React, and Next.js repositories.
- Designed a LangGraph workflow with explicit planner, repository scanner, code search, evidence reader, root-cause analyzer, fix-strategy advisor, patch generator, approval gate, test runner, verifier, risk scorer, and reporter nodes.
- Added optional structured LLM root-cause and fix-strategy outputs while preserving deterministic fallback paths for stable local development and tests.
- Implemented a safe verification layer with local allowlisted command execution, `shell=False`, structured test results, optional E2B sandbox execution, secret-aware archive filtering, and sanitized error reporting.
- Built a Next.js developer dashboard with run creation, public GitHub import, event timeline, visual agent graph, patch approval, verification and risk panels, and final report rendering.
- Added audit-friendly API responses and timeline events so users can inspect evidence, decisions, verification results, and residual risk.

## Internship Resume Version

- Built a full-stack AI developer tool that helps engineers inspect repositories, gather evidence, preview fixes, approve changes, run tests, and generate final engineering reports.
- Implemented a FastAPI and LangGraph backend with typed workflow state, SQLAlchemy persistence, repository search, approval interrupts, verification, and risk scoring.
- Created a Next.js and TypeScript dashboard for run creation, agent timeline, graph visualization, patch review, test results, risk scoring, and report viewing.
- Added practical safety controls including command allowlists, secret-file filtering, sanitized errors, read-only GitHub import, and optional sandboxed test execution.

## AI Engineer Version

- Designed a verification-first AI agent workflow that separates evidence gathering, structured reasoning, fix planning, patch preview, approval, test execution, and risk scoring.
- Integrated optional OpenAI structured outputs for root-cause analysis and fix strategy while maintaining deterministic fallbacks for reproducible tests.
- Built audit surfaces for AI-assisted engineering decisions, including line-numbered evidence, timeline events, approval records, verification summaries, and final reports.
- Implemented guardrails to reduce unsafe autonomy: patch previews only, human approval interrupts, no automatic repository modification, and no real PR creation in the MVP.

## Backend Engineer Version

- Built a FastAPI backend with LangGraph orchestration, Pydantic contracts, SQLAlchemy persistence, repository import, search tools, event logging, and structured API responses.
- Implemented safe command execution using a shared allowlist, repository path validation, `shell=False`, timeout handling, stdout/stderr capture, and structured test result schemas.
- Added optional E2B sandbox adapter with lazy SDK import, safe repository archiving, secret/heavy-file exclusions, clean error handling, and sandbox lifecycle cleanup.
- Designed API endpoints for run creation, start, approval, rejection, retrieval, and timeline events.

## Portfolio Description

DevPilot Verify is a verification-first AI software engineering agent that analyzes repositories, gathers line-numbered evidence, explains root cause, proposes a fix strategy, generates a patch preview, requires human approval, runs safe verification commands, scores residual risk, and produces a final engineering report. It demonstrates full-stack product engineering, agent workflow design, AI safety guardrails, and practical developer experience design.

## LinkedIn Project Description

Built DevPilot Verify, a verification-first AI software engineering agent for safe, evidence-backed bug fixing. The project combines FastAPI, LangGraph, Next.js, TypeScript, structured LLM outputs, read-only GitHub import, a local safe test runner, optional E2B sandboxing, verifier/risk scoring, and a monochrome developer dashboard. The core idea: AI-generated fixes should come with evidence, human approval, verification, residual risk, and a review-ready report.
