"""Practical lab-kit primitives for Renova workshops."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LabPrompt:
    title: str
    question: str
    output: str
    duration_minutes: int


FOUNDATIONAL_PROMPTS: tuple[LabPrompt, ...] = (
    LabPrompt(
        title="Habitat",
        question="What conditions currently help or obstruct this life-system?",
        output="List three enabling conditions and three obstructive conditions.",
        duration_minutes=15,
    ),
    LabPrompt(
        title="Fracture",
        question="What rupture or overload must be named with precision?",
        output="Write one precise statement and one evidence note.",
        duration_minutes=20,
    ),
    LabPrompt(
        title="Horizon",
        question="What future is credible enough to orient action within the next cycle?",
        output="Define one 30-day horizon and one 180-day horizon.",
        duration_minutes=20,
    ),
    LabPrompt(
        title="Care Practice",
        question="What concrete practice would protect fragile value immediately?",
        output="Define owner, rhythm, resource, and review date.",
        duration_minutes=15,
    ),
)


def render_canvas(subject: str) -> str:
    lines = [f"# Renova Lab Canvas: {subject}", ""]
    for prompt in FOUNDATIONAL_PROMPTS:
        lines.extend([
            f"## {prompt.title} ({prompt.duration_minutes} min)",
            f"**Question:** {prompt.question}",
            f"**Expected output:** {prompt.output}",
            "",
            "Notes:",
            "",
            "- ",
            "",
        ])
    lines.extend([
        "## Minimum viable renovative action",
        "",
        "- Action:",
        "- Owner:",
        "- First date:",
        "- Evidence of completion:",
        "- Follow-up:",
        "",
    ])
    return "\n".join(lines)
