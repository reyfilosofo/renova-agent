# Renova Agent

Renova Agent is the public AI-oriented layer of Renova.

The current implementation is intentionally local and dependency-free. It does not call external model providers by default. Its purpose is to provide a transparent scaffold that can later be connected to retrieval, a corpus, or a model API after proper governance and configuration.

## Current functions

- Receives a user prompt.
- Searches the initial ontology for matching concepts.
- Produces a structured Markdown answer.
- Adds cautions when the prompt touches specialized domains.
- Suggests practical next actions.

## Example

```bash
python -m renova_core.cli agent "How can Renova help a school?"
```

## Architecture

```text
prompt -> local scaffold -> ontology lookup -> structured response -> Markdown
```

## Future extensions

- Retrieval over Renova Open Corpus.
- Human review queue.
- Citation-aware answers.
- Public demo interface.
- Evaluation set for philosophical consistency.
