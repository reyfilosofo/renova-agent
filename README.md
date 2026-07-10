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

## ℛenova / NOUS Recursive Intelligence Lab

The repository also includes `labs/renova-nous-rsr-lab/`, a documented foundation for the **Recursive Self-Renewal** laboratory connecting ℛenova, SERESARTE, NOUS, LUCEM, ℛenova Press and Codex/GitHub workflows.

Core files:

```text
labs/renova-nous-rsr-lab/README.md
labs/renova-nous-rsr-lab/docs/00-manifiesto.md
labs/renova-nous-rsr-lab/docs/01-arquitectura.md
labs/renova-nous-rsr-lab/docs/02-metodologia-rsr.md
labs/renova-nous-rsr-lab/docs/03-productos.md
labs/renova-nous-rsr-lab/docs/04-lucem-verification-protocol.md
labs/renova-nous-rsr-lab/products/nous-recursive-intelligence-sprint.md
labs/renova-nous-rsr-lab/tasks/codex-ready-tasks.md
```

This lab must be described as an assisted, versioned, auditable and human-governed system. It must not be presented as autonomous self-improvement, AGI, self-help or unsupported technical automation.

## Page Agent integration

The virtual desktop includes an optional client-side Page Agent bridge.

Page Agent is disabled by default. The user must activate it explicitly from the floating panel and accept a privacy notice before the browser loads the official demo IIFE bundle. The bridge then lets the user send natural-language GUI instructions such as:

```text
Open the terminal and run help
Open the files app and inspect the home folder
Open the system app and explain the current state
```

Technical notes:

- The integration uses the public demo bundle: `page-agent@1.11.0/dist/iife/page-agent.demo.js`.
- The bundle is version-pinned and protected with Subresource Integrity (SRI).
- Consent lasts only for the current page session; no external script is loaded before activation.
- The demo bundle is for technical evaluation, not production secrets.
- The bridge does not store API keys.
- Prompts are sent to the public Page Agent test endpoint, and the activated agent can interact with the page and its `localStorage` data.
- For production, replace the demo configuration with a backend-proxied LLM endpoint or install the package with `npm install page-agent` and configure a private model endpoint.
- Page Agent is designed as a client-side web enhancement, not as a server-side automation layer.

## Run the virtual desktop

```bash
python3 server.py
```

Open `http://localhost:8000`.

The development server accepts only loopback hosts and an explicit list of public V-OS assets. Requests for `.env`, `.git`, `config/`, `memory/`, dependencies or any other repository path return an error.

## Run Renova Core

Install the Python package locally, then use the `renova` command exposed by `pyproject.toml`.

```bash
python3 -m pip install -e '.[dev]'
renova index data/sample_assessment.json
renova agent "What is Renova?"
renova ontology
renova canvas "Community cultural lab"
```

## Verification

Install the development tools once:

```bash
python3 -m pip install -e '.[dev]'
npm run verify
```

To include the locked Web3 starter and build the exact GitHub Pages artifact:

```bash
npm run setup:web3
npm run verify:all
```

CI validates Python 3.10, 3.12 and 3.14, JavaScript syntax and calculator behavior, server isolation, repository credential patterns, Python coverage, the packaged wheel, the Web3 contracts and the Pages public boundary.

GitHub Pages publishes only the generated `_site/` allowlist. The repository itself is never used as the deployment artifact.

## Security

Use `.env.example` only as a variable-name template. Never commit real credentials, tokens, API keys, private keys, certificates or screenshots containing secrets. See `docs/security-secrets.md`.

This GitHub repository is public. Every tracked file—including `config/`, `memory/`, clients, people and books—must therefore be treated as publicly disclosed. Before storing private intelligence or client material, move the vault to a private repository or split the public code/corpus from a private knowledge vault. See `SECURITY.md`.

## Notes

The local Renova Agent scaffold does not call external APIs by default. Page Agent is a separate, opt-in browser demo. The Renova Core runtime remains dependency-free, transparent and designed for extension.
