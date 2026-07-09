# SERESARTE V-OS + Renova Agent

This repository contains the SERESARTE virtual desktop and the Renova Agent project.

## Renova Open System v0.2.0

The repository now includes a public technical layer for Renova as cultural technology.

### Five deliverables

1. Renova Open Corpus: glossary, definitions, documentation, and corpus utilities.
2. Renova Agent: local agent scaffold for education and cultural strategy.
3. Renova Index: IRG calculation engine for renewal diagnostics.
4. Renovagrama: ontology graph model for concepts and relations.
5. Renova Lab Kit: workshop canvas generator for real-world sessions.

### New files

```text
renova_core/__init__.py
renova_core/agent.py
renova_core/corpus.py
renova_core/cli.py
renova_core/index.py
renova_core/lab.py
renova_core/ontology.py
data/sample_assessment.json
data/glossary_min.json
docs/RENOVA_OPEN_SYSTEM.md
docs/RENOVA_INDEX.md
docs/RENOVA_AGENT.md
docs/RENOVAGRAMA.md
docs/RENOVA_LAB_KIT.md
docs/OPEN_CORPUS.md
tests/test_index.py
pyproject.toml
RENOVA_OPEN_SYSTEM_PLAN.md
```

## Page Agent integration

The virtual desktop includes an optional client-side Page Agent bridge.

Page Agent is loaded from the official demo IIFE bundle and exposed through `page-agent-bridge.js` as a floating panel inside SERESARTE V-OS. The bridge lets the user send natural-language GUI instructions such as:

```text
Open the terminal and run help
Open the files app and inspect the home folder
Open the system app and explain the current state
```

Technical notes:

- The integration uses the public demo bundle: `page-agent@1.11.0/dist/iife/page-agent.demo.js`.
- The demo bundle is for technical evaluation, not production secrets.
- The bridge does not store API keys.
- For production, replace the demo configuration with a backend-proxied LLM endpoint or install the package with `npm install page-agent` and configure a private model endpoint.
- Page Agent is designed as a client-side web enhancement, not as a server-side automation layer.

## Run the virtual desktop

```bash
python3 server.py
```

Open `http://localhost:8000`.

## Run Renova Core

Install the Python package locally, then use the `renova` command exposed by `pyproject.toml`.

```bash
renova index data/sample_assessment.json
renova agent "What is Renova?"
renova ontology
renova canvas "Community cultural lab"
```

## Verification

```bash
npm run check
python3 -m pytest
```

## Notes

The local agent scaffold does not call external APIs by default. The core Python layer is dependency-free, transparent, and designed for extension.
