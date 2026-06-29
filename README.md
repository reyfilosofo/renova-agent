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

## Run the virtual desktop

```bash
python3 server.py
```

Open `http://localhost:8000`.

## Run Renova Core

```bash
python3 -m renova_core.cli index data/sample_assessment.json
python3 -m renova_core.cli agent "What is Renova?"
python3 -m renova_core.cli ontology
python3 -m renova_core.cli canvas "Community cultural lab"
```

## Verification

```bash
npm run check
python3 -m pytest
```

## Notes

The local agent scaffold does not call external APIs by default. The core Python layer is dependency-free, transparent, and designed for extension.
