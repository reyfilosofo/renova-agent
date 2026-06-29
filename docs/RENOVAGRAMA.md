# Renovagrama

Renovagrama is the visual ontology layer of Renova.

Its purpose is to turn the philosophical system into a navigable graph of concepts and relations. The first implementation is data-first: the repository exposes a Python ontology model that can export nodes and edges as JSON.

## Core nodes

- Vida.
- Renova.
- Sensibilidad fundante.
- Habitat.
- Herida.
- Horizonte.
- Cuidado.
- Memoria.
- Obra.
- Mundo.

## Core relation examples

- Sensibility grounds Renova.
- Habitat conditions life.
- Horizon orients renewal.
- Memory tempers horizon.
- Work stabilizes memory.
- Care supports world.

## Usage

```bash
python -m renova_core.cli ontology
```

This output can be consumed by a web interface using D3, Cytoscape, React Flow, Sigma, or another graph visualization library.
