# Ruflo + Codex setup for Renova Agent

## Purpose

This guide prepares `reyfilosofo/renova-agent` to work with Codex as the code executor and Ruflo / Claude-Flow as a multi-agent orchestration, memory, and MCP layer.

The target operating model is:

```text
Carlos / SERESARTE request
  -> Codex task
  -> Ruflo / Claude-Flow orchestration and memory
  -> specialist agents
  -> repository changes
  -> verification
  -> documented decision trail
```

## What was added

The repository now includes npm scripts for:

- local verification;
- Ruflo initialization;
- Claude-Flow Codex initialization;
- MCP registration and inspection.

See `package.json` for the current command surface.

## Local prerequisites

Install locally before using the multi-agent layer:

1. Node.js and npm.
2. Python 3.10+.
3. OpenAI Codex CLI, authenticated locally.
4. Git configured for this repository.
5. Permission to run `npx` packages from the terminal.

## Recommended installation path

From the repository root:

```bash
git pull
npm run verify
npm run codex:init
npm run codex:mcp:list
```

If the MCP server is not listed, add it manually:

```bash
npm run codex:mcp:add
npm run codex:mcp:list
```

Alternative Ruflo wizard path:

```bash
npm run ruflo:init
```

Quick non-interactive path:

```bash
npm run ruflo:init:quick
```

## First serious Codex task

Use this prompt inside Codex after initialization:

```text
Read AGENTS.md and docs/RUFLO_CODEX_SETUP.md first.

Act as the Renova Agent multi-agent team. Before editing files:
1. inventory the repository;
2. identify the relevant project area;
3. propose a short execution plan;
4. state the files you will touch;
5. define acceptance criteria.

Task:
Create a repository map for SERESARTE / Renova Agent and propose the minimum folder and documentation improvements needed for the next release.

Rules:
- Do not delete files.
- Do not invent facts.
- Use Markdown.
- Preserve Obsidian compatibility.
- Run npm run verify if the environment allows it.
```

## Recommended agent roles

For normal repository work, use 3 to 7 roles, not 100 agents. Suggested roles:

| Role | Function |
|---|---|
| `arquitecto-renova` | Ontology, philosophical coherence, conceptual structure. |
| `editor-seresarte` | Editorial polish, institutional voice, publishable clarity. |
| `investigador` | Evidence, source tracing, bibliographic discipline. |
| `estratega-nous` | Commercial framing, diagnostics, pitch, deliverables. |
| `dev-python` | Python CLI, tests, Renova Core utilities. |
| `dev-frontend` | Virtual desktop, interface, HTML, CSS, JavaScript. |
| `qa-seguridad` | Verification, privacy, regression risk, data handling. |

## Safety protocol

Codex and Ruflo must not treat this repository as disposable code. It is a strategic and editorial knowledge system. Therefore:

- No destructive refactors without a backup plan.
- No large rewrites without an inventory.
- No external publication claims without verification.
- No synthetic biography or commercial claims presented as fact.
- No exposure of secrets, private records, contracts, credentials, or sensitive personal data.
- No Wikipedia as a source in project research deliverables.

## Verification commands

Run:

```bash
npm run check
npm run test
npm run verify
```

`npm run verify` is the preferred complete check because it chains syntax checks and Python tests.

## Practical workflow

1. Create or update a task brief.
2. Ask Codex to read `AGENTS.md`.
3. Ask Codex to create a plan before modifying files.
4. Let the multi-agent layer propose role division.
5. Accept only small, reviewable changes.
6. Run verification.
7. Commit with a clear message.
8. Record strategic decisions in the appropriate project document.

## Notes

The Ruflo / Claude-Flow initialization commands create local configuration files and may register MCP servers on the local machine. Those generated files are environment-dependent. Review them before committing any generated artifacts.
