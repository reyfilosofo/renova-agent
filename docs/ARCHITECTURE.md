# Architecture

## Layer 1 — Conceptual core

Files:

- `src/lib/renova.ts`
- `docs/RENOVA_AGENT_SPEC.md`

Purpose: preserve the thesis, terms, principles and authorial constraints of la ℛenova.

## Layer 2 — Agent logic

Files:

- `src/lib/agent.ts`
- `src/app/api/agent/route.ts`

Purpose: convert a topic into a structured initial plan. In the current version this is deterministic and local. Future versions may add LLM integration, retrieval, citations and scoring.

## Layer 3 — Interface

Files:

- `src/app/page.tsx`
- `src/components/*`
- `src/app/globals.css`
- `public/assets/*`

Purpose: provide a deployable public face for the project.

## Layer 4 — Repository operations

Files:

- `AGENTS.md`
- `.codex/codex-task-master.md`
- `.github/workflows/ci.yml`
- `scripts/check-project.mjs`

Purpose: make the repository friendly to Codex, GitHub review and CI.
