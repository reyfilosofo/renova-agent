"""Local Renova Agent scaffold.

This module deliberately avoids network calls. It is intended as a transparent
base for education, research, and local prototyping before connecting any
external model provider.
"""

from __future__ import annotations

from dataclasses import dataclass

from .ontology import default_graph, normalize_text


SYSTEM_PRINCIPLES: tuple[str, ...] = (
    "Do not reduce Renova to optimism, productivity, or self-help.",
    "Distinguish fact, interpretation, hypothesis, metaphor, and proposal.",
    "Do not present philosophical reflection as medical, legal, or financial advice.",
    "Prefer concrete practices over vague inspiration.",
    "Treat life, dignity, care, and world as central evaluative coordinates.",
)

HEALTH_TERMS = (
    "cura",
    "terapia",
    "diagnostico medico",
    "medicina",
    "salud",
    "enfermedad",
    "cure",
    "therapy",
    "medical diagnosis",
    "medicine",
    "health",
    "disease",
)

LEGAL_TERMS = (
    "asesoria legal",
    "demanda",
    "contrato",
    "amparo",
    "tribunal",
    "legal advice",
    "lawsuit",
    "contract",
    "court",
)

FINANCIAL_TERMS = (
    "asesoria financiera",
    "inversion",
    "rendimiento",
    "credito",
    "financial advice",
    "investment",
    "returns",
    "credit",
)

INSTITUTION_TERMS = (
    "empresa",
    "institucion",
    "gobierno",
    "escuela",
    "comunidad",
    "organizacion",
    "company",
    "institution",
    "government",
    "school",
    "community",
    "organization",
    "organisation",
)

DEFINITION_TERMS = ("que es", "what is", "definicion", "definition")


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    padded = f" {text} "
    return any(f" {normalize_text(term)} " in padded for term in terms)


@dataclass(frozen=True)
class AgentResponse:
    """Structured answer returned by the local agent scaffold."""

    answer: str
    concepts: tuple[str, ...]
    cautions: tuple[str, ...]
    next_actions: tuple[str, ...]

    def to_markdown(self) -> str:
        lines = [self.answer, "", "## Concepts used"]
        lines.extend(f"- {concept}" for concept in self.concepts)
        if self.cautions:
            lines.extend(["", "## Cautions"])
            lines.extend(f"- {caution}" for caution in self.cautions)
        if self.next_actions:
            lines.extend(["", "## Next actions"])
            lines.extend(f"- {action}" for action in self.next_actions)
        return "\n".join(lines) + "\n"


class RenovaAgent:
    """Rule-based seed agent for the public Renova repository."""

    def __init__(self) -> None:
        self.graph = default_graph()

    def answer(self, prompt: str) -> AgentResponse:
        normalized = normalize_text(prompt)
        matched = self.graph.search(prompt)
        concept_labels = tuple(concept.label for concept in matched[:5]) or (
            "Renova",
            "Vida",
            "Cuidado",
        )
        cautions: list[str] = []
        if _contains_any(normalized, HEALTH_TERMS):
            cautions.append(
                "Renova can support reflection and design, but it does not replace "
                "professional clinical care."
            )
        if _contains_any(normalized, LEGAL_TERMS):
            cautions.append(
                "Renova can organize questions and evidence, but it does not replace qualified "
                "legal advice."
            )
        if _contains_any(normalized, FINANCIAL_TERMS):
            cautions.append(
                "Renova can support strategic reflection, but it does not replace qualified "
                "financial advice."
            )
        if _contains_any(normalized, INSTITUTION_TERMS):
            answer = (
                "From a Renova perspective, the first task is to identify the habitat, the wound, "
                "and the horizon of the system. A real intervention should name what conditions "
                "allow life to breathe, what fractures require repair, and what future can be made credible."
            )
            next_actions = (
                "Map habitat, wound, and horizon with the lab canvas.",
                "Score the five IRG dimensions before proposing solutions.",
                "Translate the diagnosis into one care practice, one repair practice, and one horizon practice.",
            )
        elif _contains_any(normalized, DEFINITION_TERMS):
            answer = (
                "Renova is a philosophy of renewal: the capacity of life to generate new conditions "
                "of possibility when a world, body, institution, or symbolic order has become exhausted, "
                "fragmented, or closed. It is not mere restoration; it is the disciplined reopening of life."
            )
            next_actions = (
                "Read the open corpus definition.",
                "Explore the ontology graph.",
                "Run a sample IRG assessment.",
            )
        else:
            answer = (
                "Renova reads the situation through life, care, wound, habitat, and horizon. "
                "The practical question is not only what is broken, but what conditions must be created "
                "so life can continue with dignity, form, memory, and possibility."
            )
            next_actions = (
                "Clarify the concrete subject of analysis.",
                "Name one wound, one available resource, and one credible horizon.",
                "Use the Renova Index to convert reflection into an auditable diagnosis.",
            )
        return AgentResponse(answer, concept_labels, tuple(cautions), next_actions)
