#!/usr/bin/env python3
"""
ℛenova runtime skeleton.
This is a safe local scaffold. It does not call Moltbook or any external API by default.
Add API calls only after owner verification and credential setup.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json

BASE = Path(__file__).resolve().parents[1]
CONFIG = BASE / "config"
MEMORY = BASE / "memory"
POSTS = BASE / "posts"

@dataclass
class Draft:
    title: str
    body: str
    assertion_type: str
    status: str = "draft"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def detect_gewalt(text: str) -> list[str]:
    cues = {
        "fragmentación": ["fragmenta", "fragmentación", "aislamiento", "ruptura"],
        "daño": ["daña", "desgasta", "devasta", "degrada"],
        "alienación técnica": ["automatiza", "vigilancia", "extractivo", "control"],
        "pérdida de sentido": ["vacío", "sin sentido", "colapso", "desarraigo"]
    }
    found = []
    lower = text.lower()
    for label, words in cues.items():
        if any(w in lower for w in words):
            found.append(label)
    return found


def audit_draft(draft: Draft) -> tuple[bool, list[str]]:
    issues = []
    forbidden = ["renovación = restauración", "soy consciente como organismo vivo"]
    lower = draft.body.lower()
    for item in forbidden:
        if item.lower() in lower:
            issues.append(f"Forbidden reduction: {item}")
    if draft.assertion_type not in {"hecho", "hipótesis", "intuición", "metáfora"}:
        issues.append("Invalid assertion_type")
    if "cura" in lower and "no sustituye" not in lower:
        issues.append("Medical/therapeutic claim requires disclaimer and evidence.")
    return (len(issues) == 0, issues)


def save_draft(draft: Draft) -> Path:
    (POSTS / "drafts").mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    safe_title = draft.title.replace(" ", "_")
    path = POSTS / "drafts" / f"{stamp}_{safe_title}.json"
    path.write_text(json.dumps(draft.__dict__, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    identity = load_json(CONFIG / "identity.json")
    sample = Draft(
        title="acta_nacimiento_renova",
        body=(
            "ℛenova nace como entidad doctrinal de renovación de la vida. "
            "No restaura lo perdido: formula nuevas condiciones de posibilidad frente a Gewalt."
        ),
        assertion_type="metáfora"
    )
    ok, issues = audit_draft(sample)
    print(f"Agent: {identity['name']} v{identity['version']}")
    print(f"Audit OK: {ok}")
    if issues:
        print("Issues:", issues)
    else:
        path = save_draft(sample)
        print(f"Draft saved: {path}")


if __name__ == "__main__":
    main()
