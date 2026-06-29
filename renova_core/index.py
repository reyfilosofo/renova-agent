"""Renova Index engine.

The IRG is not a clinical, financial, or legal score. It is a transparent
participatory index for cultural, educational, territorial, and organizational
reflection. The default model follows five dimensions:

- habitat: material and relational conditions that let life breathe.
- repair: capacity to name, hold, and transform wounds without glorifying them.
- horizon: credible future, imagination, purpose, and possibility.
- sensitivity: perception, attention, dignity, beauty, and care.
- equilibrium: continuity, rhythm, boundaries, and sustainable action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import fmean
from typing import Mapping, Sequence

DEFAULT_WEIGHTS: dict[str, float] = {
    "habitat": 0.35,
    "repair": 0.25,
    "horizon": 0.20,
    "sensitivity": 0.10,
    "equilibrium": 0.10,
}

LEVELS: tuple[tuple[float, str], ...] = (
    (85.0, "renovacion excelente"),
    (70.0, "renovacion activa"),
    (55.0, "renovacion vulnerable"),
    (40.0, "renovacion critica"),
    (0.0, "renovacion bloqueada"),
)


@dataclass(frozen=True)
class DimensionScore:
    """Normalized score for one Renova dimension."""

    name: str
    value: float
    evidence: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.value <= 100:
            msg = f"Dimension {self.name!r} must be between 0 and 100; got {self.value}."
            raise ValueError(msg)


@dataclass(frozen=True)
class RenovaAssessment:
    """Complete assessment with dimensions, optional metadata, and weights."""

    subject: str
    dimensions: Mapping[str, DimensionScore]
    weights: Mapping[str, float] = field(default_factory=lambda: DEFAULT_WEIGHTS.copy())
    notes: str = ""

    def normalized_weights(self) -> dict[str, float]:
        missing = set(self.dimensions) - set(self.weights)
        if missing:
            raise ValueError(f"Missing weights for dimensions: {sorted(missing)}")
        total = sum(self.weights[name] for name in self.dimensions)
        if total <= 0:
            raise ValueError("At least one dimension weight must be positive.")
        return {name: self.weights[name] / total for name in self.dimensions}


def calculate_irg(assessment: RenovaAssessment) -> float:
    """Calculate the weighted Renova Global Index on a 0-100 scale."""

    weights = assessment.normalized_weights()
    score = sum(
        assessment.dimensions[name].value * weights[name]
        for name in assessment.dimensions
    )
    return round(score, 2)


def classify_irg(score: float) -> str:
    """Return a qualitative level for an IRG value."""

    if not 0 <= score <= 100:
        raise ValueError("IRG score must be between 0 and 100.")
    for threshold, label in LEVELS:
        if score >= threshold:
            return label
    return LEVELS[-1][1]


def dimension_average(items: Sequence[float]) -> float:
    """Average raw questionnaire items and round to two decimals."""

    if not items:
        raise ValueError("At least one item is required.")
    for item in items:
        if not 0 <= item <= 100:
            raise ValueError(f"Questionnaire item must be between 0 and 100; got {item}.")
    return round(fmean(items), 2)


def strengths_and_risks(assessment: RenovaAssessment) -> dict[str, list[str]]:
    """Separate dimensions into practical strengths, watchlist, and risks."""

    result = {"strengths": [], "watchlist": [], "risks": []}
    for name, dimension in assessment.dimensions.items():
        if dimension.value >= 75:
            result["strengths"].append(name)
        elif dimension.value >= 55:
            result["watchlist"].append(name)
        else:
            result["risks"].append(name)
    return result


def recommendation_for_dimension(name: str, score: float) -> str:
    """Produce a concise action recommendation for one dimension."""

    low = score < 55
    if name == "habitat":
        return "Improve material, relational, and informational conditions." if low else "Protect the conditions that allow daily life to breathe."
    if name == "repair":
        return "Create explicit practices for memory, recognition, and repair." if low else "Keep repair practices visible and non-punitive."
    if name == "horizon":
        return "Build credible next steps, symbolic direction, and future narratives." if low else "Translate horizon into shared commitments."
    if name == "sensitivity":
        return "Strengthen listening, attention, dignity, and aesthetic perception." if low else "Use sensitivity as an early-warning system."
    if name == "equilibrium":
        return "Reduce overload and define rhythms, limits, and continuity." if low else "Maintain sustainable cadence without immobilizing change."
    return "Define one concrete action for this dimension."


def assessment_report(assessment: RenovaAssessment) -> str:
    """Render a Markdown report for human review."""

    score = calculate_irg(assessment)
    level = classify_irg(score)
    buckets = strengths_and_risks(assessment)
    lines = [
        f"# Renova Assessment: {assessment.subject}",
        "",
        f"IRG: **{score}/100**",
        f"Level: **{level}**",
        "",
        "## Dimensions",
    ]
    for name, dimension in assessment.dimensions.items():
        lines.append(f"- **{name}**: {dimension.value}/100 — {dimension.evidence}".rstrip())
    lines.extend([
        "",
        "## Diagnostic buckets",
        f"- Strengths: {', '.join(buckets['strengths']) or 'none'}",
        f"- Watchlist: {', '.join(buckets['watchlist']) or 'none'}",
        f"- Risks: {', '.join(buckets['risks']) or 'none'}",
        "",
        "## Recommended next actions",
    ])
    for name, dimension in assessment.dimensions.items():
        lines.append(f"- **{name}**: {recommendation_for_dimension(name, dimension.value)}")
    if assessment.notes:
        lines.extend(["", "## Notes", assessment.notes])
    return "\n".join(lines) + "\n"
