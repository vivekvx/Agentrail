# Agentrail — PRODUCT.md

## Register
product — app UI (dashboard, run detail, diff review, auth, evals). Design serves the workflow.

## Users & Purpose
Developers debugging a repository. They import a repo/issue, watch an agent pipeline collect evidence and propose a patch, review the diff, and approve or reject at a human-in-the-loop gate. Context: focused desk work, often dark IDE next to the browser. Primary task per screen: read evidence/diffs fast, decide approve/reject confidently.

## Brand Personality
Engineered, restrained, trustworthy. A lab instrument, not a marketing site. Three words: precise, calm, verifiable.

## Anti-references
- SaaS gradient dashboards, glassmorphism, hero metrics.
- Bouncy motion, decorative illustration.
- Anything that distracts from diff/evidence reading.

## Strategic Design Principles
1. Diff and evidence panels are the hero surfaces — maximum legibility (mono, contrast ≥4.5:1).
2. The approval gate is the most important interaction; its primary action is the one filled element on the screen.
3. Dark canvas only (#0a0a0a), hairline borders carry elevation, no shadows.
4. Mode honesty: heuristic vs LLM runs are visibly labeled.

## Accessibility
WCAG AA contrast; keyboard reachable approve/reject; reduced-motion alternatives.
