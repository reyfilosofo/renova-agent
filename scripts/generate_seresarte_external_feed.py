#!/usr/bin/env python3
"""Generate a public SERESARTE dispatch, archive and RSS feed without secrets."""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "content" / "seresarte_institutional_post_series.md"
DEFAULT_OUTPUT = ROOT / "public" / "seresarte-agent"
DEFAULT_BASE_URL = "https://reyfilosofo.github.io/renova-agent/seresarte-agent/"
EPOCH = dt.date(2026, 8, 6)
CONFIDENTIAL_TERMS = (
    "".join(("Fundación para el ", "Emprendimiento Cultural, ", "Artístico y Creativo")),
    "".join(("Emprendimiento Cultural, ", "Artístico y Creativo, A.C.")),
)
PRIORITY_TITLES = (
    "SERESARTE: arte, comunidad y creación colectiva",
    "What SERESARTE means by cultural work",
    "Português: arte relacional e memória pública",
    "Français: une archive culturelle doit garder les relations",
    "中文: 文化项目需要留下可核查的记忆",
    "Русский: искусство как связь, а не только как объект",
    "بالعربية: الفن والعلاقة والذاكرة",
    "SERESARTE x ℛenova: del archivo al protocolo",
    "A cultural pilot must publish its null result",
    "¿Puede una fotografía ser evidencia sin convertir a alguien en dato?",
    "Photovoice no es una etiqueta automática",
    "An invitation to adversarial collaboration",
    "Same construct, different modality?",
    "Audit v1.1 before recruitment",
)


def ensure_public_safe(text: str) -> None:
    found = [term for term in CONFIDENTIAL_TERMS if term.casefold() in text.casefold()]
    if found:
        raise ValueError("Confidential legal identity found in public SERESARTE output.")


def parse_series(path: Path) -> list[dict[str, str | int]]:
    source = path.read_text(encoding="utf-8")
    ensure_public_safe(source)
    matches = list(re.finditer(r"^## Post (\d+):\s*(.+)$", source, flags=re.MULTILINE))
    posts: list[dict[str, str | int]] = []
    for index, match in enumerate(matches):
        body_start = match.end()
        body_end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        posts.append({
            "number": int(match.group(1)),
            "title": match.group(2).strip(),
            "body": source[body_start:body_end].strip(),
        })
    if not posts:
        raise ValueError("SERESARTE source contains no posts.")
    return posts


def ordered_posts(posts: list[dict[str, str | int]]) -> list[dict[str, str | int]]:
    by_title = {str(post["title"]): post for post in posts}
    preferred = [by_title[title] for title in PRIORITY_TITLES if title in by_title]
    preferred_titles = {str(post["title"]) for post in preferred}
    return preferred + [post for post in posts if str(post["title"]) not in preferred_titles]


def infer_language(title: str) -> str:
    prefixes = {
        "Português": "pt",
        "Français": "fr",
        "中文": "zh",
        "Русский": "ru",
        "بالعربية": "ar",
        "English": "en",
    }
    for prefix, language in prefixes.items():
        if title.startswith(prefix):
            return language
    english_markers = ("What ", "A cultural ", "An invitation", "Same construct", "Audit ")
    return "en" if title.startswith(english_markers) else "es"


def publication_for_day(posts: list[dict[str, str | int]], day: dt.date) -> dict[str, str | int]:
    offset = max(0, (day - EPOCH).days)
    post = dict(posts[offset % len(posts)])
    post["date"] = day.isoformat()
    post["language"] = infer_language(str(post["title"]))
    return post


def body_html(body: str) -> str:
    blocks = []
    for block in re.split(r"\n\s*\n", body.strip()):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if lines and all(line.startswith("- ") for line in lines):
            items = "".join(f"<li>{html.escape(line[2:])}</li>" for line in lines)
            blocks.append(f"<ul>{items}</ul>")
        else:
            blocks.append(f"<p>{'<br>'.join(html.escape(line) for line in lines)}</p>")
    return "\n".join(blocks)


def page_html(publication: dict[str, str | int], base_url: str) -> str:
    title = str(publication["title"])
    body = str(publication["body"])
    language = str(publication["language"])
    date = str(publication["date"])
    canonical = f"{base_url.rstrip('/')}/archive/{date}.html"
    description = re.sub(r"\s+", " ", body)[:190]
    return f"""<!doctype html>
<html lang="{language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{html.escape(title)} | SERESARTE Agent</title>
  <meta name="description" content="{html.escape(description, quote=True)}">
  <link rel="canonical" href="{html.escape(canonical, quote=True)}">
  <link rel="alternate" type="application/rss+xml" title="SERESARTE Agent" href="{html.escape(base_url.rstrip('/') + '/feed.xml', quote=True)}">
  <style>
    :root {{ color-scheme: light; --ink:#151515; --paper:#fff; --red:#d52b37; --teal:#007f78; --yellow:#f2c94c; --line:#d9d9d9; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:17px/1.65 system-ui,-apple-system,sans-serif; letter-spacing:0; }}
    header,main,footer {{ width:min(760px,calc(100% - 32px)); margin:auto; }} header {{ padding:28px 0 18px; border-bottom:3px solid var(--red); }}
    .brand {{ font-weight:800; font-size:1.05rem; }} .date {{ color:#555; }} h1 {{ font-size:clamp(2rem,7vw,3.8rem); line-height:1.04; margin:44px 0 22px; }}
    article {{ padding-bottom:40px; }} a {{ color:var(--teal); }} .method {{ display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:4px; margin:36px 0; }}
    .method span {{ min-height:72px; padding:10px 6px; border-top:5px solid var(--yellow); font-size:.76rem; overflow-wrap:anywhere; }}
    footer {{ border-top:1px solid var(--line); padding:24px 0 48px; color:#555; }} @media(max-width:620px) {{ .method {{ grid-template-columns:1fr 1fr; }} }}
  </style>
</head>
<body>
  <header><div class="brand">SERESARTE Agent</div><div class="date">{html.escape(date)} · {html.escape(language.upper())}</div></header>
  <main>
    <h1>{html.escape(title)}</h1>
    <div class="method" aria-label="SERESARTE public framework"><span>Comunidad</span><span>Experiencias</span><span>Qualia</span><span>Habilidades blandas</span><span>Capacidades renovativas</span></div>
    <article>{body_html(body)}</article>
  </main>
  <footer>Agente de SERESARTE, creado por Carlos Jonathan González Rodríguez / Rey Filósofo. <a href="../feed.xml">RSS</a></footer>
</body>
</html>
"""


def build(output_dir: Path, source: Path, day: dt.date, base_url: str) -> dict[str, object]:
    posts = ordered_posts(parse_series(source))
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_dir = output_dir / "archive"
    archive_dir.mkdir(parents=True, exist_ok=True)
    first_day = EPOCH
    days = [first_day + dt.timedelta(days=i) for i in range((day - first_day).days + 1)] if day >= first_day else [first_day]
    publications = [publication_for_day(posts, item_day) for item_day in days]
    for publication in publications:
        archive_path = archive_dir / f"{publication['date']}.html"
        archive_path.write_text(page_html(publication, base_url), encoding="utf-8")

    latest = publications[-1]
    (output_dir / "index.html").write_text(page_html(latest, base_url), encoding="utf-8")
    (output_dir / "latest.json").write_text(json.dumps(latest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "latest.md").write_text(
        f"# {latest['title']}\n\nDate: {latest['date']} · Language: {latest['language']}\n\n{latest['body']}\n",
        encoding="utf-8",
    )

    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "SERESARTE Agent"
    ET.SubElement(channel, "link").text = base_url
    ET.SubElement(channel, "description").text = "Daily multilingual, source-backed cultural dispatches from SERESARTE Agent."
    ET.SubElement(channel, "language").text = "es-MX"
    for publication in reversed(publications[-14:]):
        item = ET.SubElement(channel, "item")
        item_url = f"{base_url.rstrip('/')}/archive/{publication['date']}.html"
        ET.SubElement(item, "title").text = str(publication["title"])
        ET.SubElement(item, "link").text = item_url
        ET.SubElement(item, "guid").text = item_url
        ET.SubElement(item, "pubDate").text = dt.datetime.combine(
            dt.date.fromisoformat(str(publication["date"])), dt.time(17, 20), tzinfo=dt.timezone.utc
        ).strftime("%a, %d %b %Y %H:%M:%S %z")
        ET.SubElement(item, "description").text = str(publication["body"])
    ET.ElementTree(rss).write(output_dir / "feed.xml", encoding="utf-8", xml_declaration=True)

    generated = "\n".join(path.read_text(encoding="utf-8") for path in output_dir.rglob("*") if path.is_file())
    ensure_public_safe(generated)
    return {"date": latest["date"], "title": latest["title"], "language": latest["language"], "posts": len(posts)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the public SERESARTE Agent web and RSS feed.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--date", type=dt.date.fromisoformat, default=dt.datetime.now(dt.timezone.utc).date())
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    args = parser.parse_args()
    result = build(args.output_dir, args.source, args.date, args.base_url)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
