#!/usr/bin/env python3
"""ℛenova Press: verificador técnico conservador de PDF.
Requiere PyMuPDF. No sustituye revisión ortotipográfica, visual, científica, legal o de imprenta.
Uso: python renova_press_preflight.py ruta1.pdf ruta2.pdf --out qa.json
"""
import argparse
import json
import re
from pathlib import Path
import fitz

TERMS = [
    ("Tucidides", "Tucídides"),
    ("geopolitica", "geopolítica"),
    ("Edicion", "Edición"),
    ("Mexico", "México"),
    ("Bibliografia", "Bibliografía"),
    ("Titulo", "Título"),
    ("Colofon", "Colofón"),
    ("Apendice", "Apéndice"),
    ("Indice", "Índice"),
    ("Filosofia", "Filosofía"),
]

def inspect(path):
    doc = fitz.open(str(path))
    possible = []
    escaped = []
    for number, page in enumerate(doc, 1):
        text = page.get_text()
        for bad, replacement in TERMS:
            count = len(list(re.finditer(r"\b" + re.escape(bad) + r"\b", text)))
            if count:
                possible.append({
                    "page": number, "candidate": bad,
                    "suggestion": replacement, "count": count,
                })
        for block in page.get_text("dict")["blocks"]:
            if block.get("type") != 0:
                continue
            for line in block["lines"]:
                for span in line["spans"]:
                    box = fitz.Rect(span["bbox"])
                    if (box.x0 < -0.1 or box.y0 < -0.1 or
                        box.x1 > page.rect.width + 0.1 or
                        box.y1 > page.rect.height + 0.1):
                        escaped.append({
                            "page": number,
                            "text_excerpt": span["text"][:80],
                            "bbox": list(box),
                        })
    return {
        "file": path.name,
        "pages": len(doc),
        "page_sizes_pt": sorted(set(
            (round(p.rect.width, 2), round(p.rect.height, 2))
            for p in doc
        )),
        "possible_unaccented_terms": possible,
        "off_page_text_spans": escaped,
        "disclaimer": "Matches need contextual verification; no substantive, legal or printer compliance test.",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="+")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    report = {
        "tool": "renova_press_preflight",
        "version": "0.1.0",
        "results": [inspect(Path(f)) for f in args.files],
    }
    Path(args.out).write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for result in report["results"]:
        print(result["file"], "pages", result["pages"],
              "orthography_candidates", sum(x["count"] for x in result["possible_unaccented_terms"]),
              "off_page", len(result["off_page_text_spans"]))

if __name__ == "__main__":
    main()
