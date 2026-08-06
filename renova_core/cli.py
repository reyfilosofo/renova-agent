"""Command line interface for Renova Core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from collections.abc import Mapping, Sequence
from numbers import Real
from typing import Any

from .agent import RenovaAgent
from .index import DimensionScore, RenovaAssessment, assessment_report
from .lab import render_canvas
from .ontology import default_graph


def load_assessment(path: Path) -> RenovaAssessment:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Assessment root must be a JSON object.")

    subject = _required_string(data.get("subject"), "subject")
    notes = data.get("notes", "")
    if not isinstance(notes, str):
        raise ValueError("Assessment field 'notes' must be a string.")

    raw_dimensions = data.get("dimensions")
    if not isinstance(raw_dimensions, Mapping) or not raw_dimensions:
        raise ValueError("Assessment field 'dimensions' must be a non-empty object.")

    dimensions: dict[str, DimensionScore] = {}
    for name, payload in raw_dimensions.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Dimension names must be non-empty strings.")
        if not isinstance(payload, Mapping):
            raise ValueError(f"Dimension {name!r} must be an object.")
        if "value" not in payload:
            raise ValueError(f"Dimension {name!r} is missing field 'value'.")
        evidence = payload.get("evidence", "")
        if not isinstance(evidence, str):
            raise ValueError(f"Evidence for dimension {name!r} must be a string.")
        dimensions[name] = DimensionScore(
            name=name,
            value=_required_number(payload["value"], f"dimensions.{name}.value"),
            evidence=evidence,
        )

    raw_weights = data.get("weights")
    if raw_weights is None:
        assessment = RenovaAssessment(subject=subject, dimensions=dimensions, notes=notes)
    else:
        if not isinstance(raw_weights, Mapping) or not raw_weights:
            raise ValueError("Assessment field 'weights' must be a non-empty object.")
        weights: dict[str, float] = {}
        for name, value in raw_weights.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Weight names must be non-empty strings.")
            weights[name] = _required_number(value, f"weights.{name}")
        assessment = RenovaAssessment(
            subject=subject,
            dimensions=dimensions,
            weights=weights,
            notes=notes,
        )

    assessment.normalized_weights()
    return assessment


def _required_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Assessment field {field_name!r} must be a non-empty string.")
    return value


def _required_number(value: Any, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"Assessment field {field_name!r} must be numeric.")
    return float(value)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="renova")
    sub = parser.add_subparsers(dest="command", required=True)
    p_index = sub.add_parser("index")
    p_index.add_argument("file")
    p_agent = sub.add_parser("agent")
    p_agent.add_argument("prompt")
    sub.add_parser("ontology")
    p_canvas = sub.add_parser("canvas")
    p_canvas.add_argument("subject")
    args = parser.parse_args(argv)

    try:
        if args.command == "index":
            assessment = load_assessment(Path(args.file))
            print(assessment_report(assessment), end="")
        elif args.command == "agent":
            print(RenovaAgent().answer(args.prompt).to_markdown(), end="")
        elif args.command == "ontology":
            print(json.dumps(default_graph().to_json_dict(), ensure_ascii=False, indent=2))
        elif args.command == "canvas":
            print(render_canvas(args.subject))
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as error:
        print(f"renova: error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
