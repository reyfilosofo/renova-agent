"""Ontology utilities for Renovagrama and Renova Agent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Concept:
    """A conceptual node in the Renova ontology."""

    identifier: str
    label: str
    definition: str
    domain: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class Relation:
    """Directed conceptual relation between two nodes."""

    source: str
    target: str
    predicate: str
    note: str = ""


CORE_CONCEPTS: tuple[Concept, ...] = (
    Concept("life", "Vida", "The living field that seeks continuity, meaning, form, and renewal.", "root", ("vida",)),
    Concept("renova", "Renova", "Capacity of life to generate new conditions of possibility after fracture, exhaustion, or closure.", "root", ("renovacion", "renewal")),
    Concept("foundational_sensibility", "Sensibilidad fundante", "Primary orientation through which life perceives value, wound, dignity, and horizon before formal theory.", "epistemology", ("sensibilidad",)),
    Concept("habitat", "Habitat", "Material, symbolic, relational, and informational condition that lets life breathe.", "diagnostic", ("casa", "territorio", "environment")),
    Concept("wound", "Herida", "Trace of damage, loss, rupture, or denied dignity that demands interpretation and repair.", "diagnostic", ("fractura", "ruptura")),
    Concept("horizon", "Horizonte", "Field of credible possibility that gives direction to action and continuity.", "diagnostic", ("futuro", "posibilidad")),
    Concept("care", "Cuidado", "Practical intelligence that protects fragile life and organizes conditions for flourishing.", "ethics", ("cura", "atencion")),
    Concept("memory", "Memoria", "Living continuity of what must not be erased, repeated blindly, or abandoned.", "time", ("recuerdo",)),
    Concept("work", "Obra", "Stabilized form through which meaning becomes shareable and durable.", "culture", ("forma", "creacion")),
    Concept("world", "Mundo", "Shared horizon of relations where life appears, acts, suffers, and renews itself.", "root", ("cosmos", "comunidad")),
)

CORE_RELATIONS: tuple[Relation, ...] = (
    Relation("renova", "life", "serves", "Renova exists as a life-oriented paradigm."),
    Relation("foundational_sensibility", "renova", "grounds", "Renova begins from sensitivity before measurement."),
    Relation("habitat", "life", "conditions", "Life requires conditions before it can flourish."),
    Relation("wound", "care", "calls_for", "A wound ethically calls for care and repair."),
    Relation("horizon", "renova", "orients", "Renewal requires a future that can be inhabited."),
    Relation("memory", "horizon", "tempers", "Future without memory becomes abstraction."),
    Relation("work", "memory", "stabilizes", "Works preserve and transform memory."),
    Relation("care", "world", "repairs", "Care repairs the shared world in concrete practices."),
    Relation("renova", "world", "reopens", "Renewal reopens world where closure had dominated."),
)


class OntologyGraph:
    """Small dependency-free graph abstraction for concepts and relations."""

    def __init__(self, concepts: Iterable[Concept], relations: Iterable[Relation]) -> None:
        self.concepts = {concept.identifier: concept for concept in concepts}
        self.relations = tuple(relations)
        missing = {
            node
            for relation in self.relations
            for node in (relation.source, relation.target)
            if node not in self.concepts
        }
        if missing:
            raise ValueError(f"Relations refer to unknown concepts: {sorted(missing)}")

    def neighbors(self, concept_id: str) -> list[Relation]:
        if concept_id not in self.concepts:
            raise KeyError(concept_id)
        return [r for r in self.relations if r.source == concept_id or r.target == concept_id]

    def search(self, query: str) -> list[Concept]:
        normalized = query.casefold().strip()
        if not normalized:
            return []
        results: list[Concept] = []
        for concept in self.concepts.values():
            haystack = " ".join((concept.identifier, concept.label, concept.definition, *concept.aliases)).casefold()
            if normalized in haystack:
                results.append(concept)
        return results

    def to_json_dict(self) -> dict[str, list[dict[str, str]]]:
        return {
            "nodes": [
                {
                    "id": c.identifier,
                    "label": c.label,
                    "definition": c.definition,
                    "domain": c.domain,
                }
                for c in self.concepts.values()
            ],
            "edges": [
                {
                    "source": r.source,
                    "target": r.target,
                    "predicate": r.predicate,
                    "note": r.note,
                }
                for r in self.relations
            ],
        }


def default_graph() -> OntologyGraph:
    """Return the initial public Renova ontology graph."""

    return OntologyGraph(CORE_CONCEPTS, CORE_RELATIONS)
