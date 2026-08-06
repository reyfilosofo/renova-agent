"""Corpus utilities for Renova Open Corpus."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .ontology import normalize_text


@dataclass(frozen=True)
class CorpusEntry:
    """One public corpus entry."""

    identifier: str
    title: str
    kind: str
    body: str
    tags: tuple[str, ...]


def load_json(path: str | Path) -> Any:
    """Load a UTF-8 JSON file."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_glossary(path: str | Path) -> dict[str, str]:
    """Load glossary JSON into a term-definition dictionary."""

    data = load_json(path)
    if not isinstance(data, dict) or not isinstance(data.get("terms"), list):
        raise ValueError("Glossary must be an object containing a 'terms' list.")

    glossary: dict[str, str] = {}
    normalized_terms: set[str] = set()
    for index, item in enumerate(data["terms"]):
        if not isinstance(item, dict):
            raise ValueError(f"Glossary entry {index} must be an object.")
        term = item.get("term")
        definition = item.get("definition")
        if not isinstance(term, str) or not term.strip():
            raise ValueError(f"Glossary entry {index} has an invalid term.")
        if not isinstance(definition, str) or not definition.strip():
            raise ValueError(f"Glossary entry {index} has an invalid definition.")
        normalized_term = normalize_text(term)
        if normalized_term in normalized_terms:
            raise ValueError(f"Duplicate glossary term: {term!r}.")
        normalized_terms.add(normalized_term)
        glossary[term] = definition
    return glossary


def search_glossary(glossary: dict[str, str], query: str) -> dict[str, str]:
    """Search glossary terms and definitions using a simple local match."""

    needle = normalize_text(query)
    if not needle:
        return {}
    return {
        term: definition
        for term, definition in glossary.items()
        if needle in normalize_text(term) or needle in normalize_text(definition)
    }
