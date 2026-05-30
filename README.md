# RENOVA Agent

RENOVA Agent is the first technical scaffold for an AI-facing interface around the philosophy of **la ℛenova**: an ontological, existential and renewative framework oriented toward life, meaning, repair, transformation and applied intelligence.

The project is deliberately minimal, professional and extensible. It is designed to be opened in Codex, edited by an AI coding agent, reviewed in GitHub, and deployed as a public landing page or prototype dashboard.

## Authorial identity

**Rey Filósofo by SERESARTE**  
Carlos Jonathan González Rodríguez  
SERESARTE / ℛENOVA PRESS

## Stack

- Next.js
- TypeScript
- React
- CSS without unnecessary UI dependencies
- Static SVG assets generated for the first brand layer
- Documentation designed for Codex, GitHub and future agentic development

## Quick start

```bash
npm install
npm run dev
```

Open `http://localhost:3000`.

## Build

```bash
npm run build
npm run start
```

## Project structure

```text
renova-agent/
├── .codex/
│   └── codex-task-master.md
├── .github/workflows/
│   └── ci.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CODEX_MOBILE_SETUP.md
│   ├── CODEX_PROMPT_MASTER.md
│   ├── DEPLOYMENT.md
│   ├── GITHUB_SETUP.md
│   ├── IMAGE_PROMPTS.md
│   ├── RENOVA_AGENT_SPEC.md
│   └── ROADMAP.md
├── public/assets/
│   ├── architecture.svg
│   ├── hero-renova.svg
│   ├── logo-renova.svg
│   └── social-card.svg
├── scripts/
│   └── check-project.mjs
└── src/
    ├── app/
    ├── components/
    ├── data/
    └── lib/
```

## What Codex should do next

1. Install dependencies.
2. Run `npm run check:structure`.
3. Run `npm run build`.
4. If errors appear, fix them without changing the philosophical content.
5. Create a branch named `codex/bootstrap-renova-agent`.
6. Open a pull request with a precise summary.

## License

All philosophical, brand, narrative and conceptual material belongs to Carlos Jonathan González Rodríguez / Rey Filósofo by SERESARTE unless a separate license is explicitly granted.
