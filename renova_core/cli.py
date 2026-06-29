"""Command line interface for Renova Core."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .agent import RenovaAgent
from .index import DimensionScore, RenovaAssessment, assessment_report
from .lab import render_canvas
from .ontology import default_graph


def load_assessment(path: Path) -> RenovaAssessment:
    data = json.loads(path.read_text(encoding="utf-8"))
    dimensions = {}
    for name, payload in data["dimensions"].items():
        dimensions[name] = DimensionScore(
            name=name,
            value=float(payload["value"]),
            evidence=str(payload.get("evidence", "")),
        )
    return RenovaAssessment(
        subject=str(data["subject"]),
        dimensions=dimensions,
        notes=str(data.get("notes", "")),
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="renova")
    sub = parser.add_subparsers(dest="command", required=True)
    p_index = sub.add_parser("index")
    p_index.add_argument("file")
    p_agent = sub.add_parser("agent")
    p_agent.add_argument("prompt")
    sub.add_parser("ontology")
    p_canvas = sub.add_parser("canvas")
    p_canvas.add_argument("subject")
    args = parser.parse_args()

    if args.command == "index":
        assessment = load_assessment(Path(args.file))
        print(assessment_report(assessment))
    elif args.command == "agent":
        print(RenovaAgent().answer(args.prompt).to_markdown())
    elif args.command == "ontology":
        print(json.dumps(default_graph().to_json_dict(), ensure_ascii=False, indent=2))
    elif args.command == "canvas":
        print(render_canvas(args.subject))
    return 0
