"""Corpus utilities for Renova Open Corpus."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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
    return {item["term"]: item["definition"] for item in data["terms"]}


def search_glossary(glossary: dict[str, str], query: str) -> dict[str, str]:
    """Search glossary terms and definitions using a simple local match."""

    needle = query.casefold().strip()
    if not needle:
        return {}
    return {
        term: definition
        for term, definition in glossary.items()
        if needle in term.casefold() or needle in definition.casefold()
    }
