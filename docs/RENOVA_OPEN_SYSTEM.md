# Renova Open System

Renova Open System is the public technical layer of Renova: an open-source ecosystem that turns a philosophical project into reusable cultural technology.

The system has five deliverables:

1. Renova Open Corpus: canonical definitions, glossary, axioms, bibliography, and public documentation.
2. Renova Agent: a local and transparent agent scaffold for reflection, education, and cultural strategy.
3. Renova Index: a measurable renewal index for communities, institutions, schools, and projects.
4. Renovagrama: a visual ontology graph for concepts and relations.
5. Renova Lab Kit: workshop canvases and facilitation tools for real-world use.

## Design principles

- Human-readable first: Markdown, JSON, and plain Python.
- No hidden dependencies in the core layer.
- No external API calls by default.
- Clear difference between philosophy, data, interpretation, and action.
- Useful in education, culture, territory, organizational work, and research.

## Current technical state

This repository now includes a Python package called `renova_core` with:

- IRG calculation engine.
- Ontology graph model.
- Local Renova Agent scaffold.
- Lab canvas generator.
- Corpus utilities.
- Sample assessment data.
- Pytest tests for the index engine.

## Example

```bash
python -m renova_core.cli index data/sample_assessment.json
python -m renova_core.cli agent "What is Renova?"
python -m renova_core.cli ontology
python -m renova_core.cli canvas "Community cultural lab"
```
