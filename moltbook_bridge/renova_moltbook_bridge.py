#!/usr/bin/env python3
"""GitHub Actions bridge for the Renova Moltbook agent.

The bridge is intentionally narrower than the local launchd autopilot: it posts
one planned multilingual item per run, avoids duplicate recent titles, verifies
simple Moltbook arithmetic challenges, and persists non-secret state in Git.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

API_BASE = os.getenv("MOLTBOOK_API_BASE", "https://www.moltbook.com/api/v1").rstrip("/")
AGENT_NAME = os.getenv("MOLTBOOK_AGENT_NAME", "renova_agent")
DEFAULT_SUBMOLT = os.getenv("MOLTBOOK_DEFAULT_SUBMOLT", "general")
DEFAULT_CONTENT_FILE = Path(__file__).with_name("renova_30_day_content.json")
DEFAULT_STATE_FILE = Path(__file__).with_name("state.json")

NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}
for tens_word, tens_value in list(NUMBER_WORDS.items()):
    if tens_value >= 20 and tens_value % 10 == 0:
        for unit_word, unit_value in list(NUMBER_WORDS.items()):
            if 1 <= unit_value <= 9:
                NUMBER_WORDS[tens_word + unit_word] = tens_value + unit_value


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def compact_challenge(text: str) -> str:
    letters = re.sub(r"[^a-zA-Z0-9]+", "", text.lower())
    return re.sub(r"(.)\1+", r"\1", letters)


def challenge_tokens(text: str) -> list[str]:
    return [
        compact_challenge(match.group())
        for match in re.finditer(r"[A-Za-z0-9.]+", text)
        if compact_challenge(match.group())
    ]


def match_number(tokens: list[str], index: int, compact_words: dict[str, int], max_fragments: int = 6) -> tuple[int, float] | None:
    token = tokens[index]
    if re.fullmatch(r"\d+(?:\.\d+)?", token):
        return index + 1, float(token)

    stop = min(len(tokens), index + max_fragments)
    for end in range(stop, index, -1):
        fragment = "".join(tokens[index:end])
        value = compact_words.get(fragment)
        if value is not None:
            return end, float(value)
        if fragment.startswith("s"):
            value = compact_words.get(fragment[1:])
            if value is not None:
                return end, float(value)
    return None


def extract_numbers(text: str) -> list[float]:
    tokens = challenge_tokens(text)
    compact_words = {compact_challenge(word): value for word, value in NUMBER_WORDS.items()}
    numbers: list[float] = []
    index = 0
    while index < len(tokens):
        match = match_number(tokens, index, compact_words)
        if match is None:
            index += 1
            continue
        end, value = match
        numbers.append(value)
        index = end
    return numbers


def solve_challenge(text: str) -> str:
    compact = compact_challenge(text)
    numbers = extract_numbers(text)
    if len(numbers) < 2:
        raise ValueError(f"Could not extract two numbers from challenge: {text}")
    multiply = any(word in compact for word in ("multiply", "multiplied", "times", "product", "torque", "leverarm")) or "*" in text or "×" in text
    # Moltbook may inject repeated number fragments before the actual operation.
    # The operands nearest a multiplication instruction are normally the final
    # two parsed values, while ordinary addition challenges use the first two.
    left, right = (numbers[-2], numbers[-1]) if multiply and len(numbers) > 2 else (numbers[0], numbers[1])
    if any(word in compact for word in ("slow", "minus", "subtract", "reduce", "decrease", "lose", "collide")):
        answer = left - right
    elif multiply:
        answer = left * right
    elif any(word in compact for word in ("divide", "quotient")):
        answer = left / right
    else:
        answer = left + right
    return f"{answer:.2f}"


def api_key() -> str:
    key = os.getenv("MOLTBOOK_API_KEY", "").strip()
    if not key:
        raise RuntimeError("Set MOLTBOOK_API_KEY as a GitHub secret or environment variable.")
    return key


def request_json(method: str, path: str, api_token: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = path if path.startswith("http") else API_BASE + path
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if api_token:
        headers["Authorization"] = f"Bearer {api_token}"
    request = urllib.request.Request(url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            return json.loads(body or "{}")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(body)
        except json.JSONDecodeError:
            parsed = body
        return {"success": False, "http_status": exc.code, "error": parsed}
    except urllib.error.URLError as exc:
        return {"success": False, "error": "network_error", "detail": str(exc.reason)}


def recent_titles(agent_name: str) -> set[str]:
    query = urllib.parse.urlencode({"name": agent_name})
    result = request_json("GET", f"/agents/profile?{query}")
    posts = result.get("recentPosts") if isinstance(result, dict) else []
    if not isinstance(posts, list):
        return set()
    return {str(post.get("title", "")).strip() for post in posts if isinstance(post, dict)}


def verification_from(result: dict[str, Any]) -> dict[str, Any] | None:
    for key in ("post", "comment", "submolt"):
        item = result.get(key)
        if isinstance(item, dict) and isinstance(item.get("verification"), dict):
            return item["verification"]
    if isinstance(result.get("verification"), dict):
        return result["verification"]
    return None


def verify_if_needed(result: dict[str, Any], api_token: str, execute: bool, actions: list[dict[str, Any]]) -> bool:
    verification = verification_from(result)
    if not verification:
        return True
    answer = solve_challenge(str(verification.get("challenge_text", "")))
    payload = {"verification_code": verification["verification_code"], "answer": answer}
    actions.append({"action": "verify_challenge", "answer": answer, "execute": execute})
    if not execute:
        return True
    verify_result = request_json("POST", "/verify", api_token, payload)
    actions.append({"action": "verify_result", "success": verify_result.get("success"), "http_status": verify_result.get("http_status")})
    return bool(verify_result.get("success"))


def created_post_id(result: dict[str, Any]) -> str | None:
    post = result.get("post") if isinstance(result.get("post"), dict) else {}
    post_id = post.get("id") or result.get("content_id")
    return str(post_id) if post_id else None


def post_is_publicly_usable(post: dict[str, Any]) -> bool:
    return post.get("verification_status") == "verified" and post.get("is_spam") is not True


def sanitize_hashtags(tags: list[str], limit: int) -> str:
    clean: list[str] = []
    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue
        if not tag.startswith("#"):
            tag = "#" + tag
        if tag not in clean:
            clean.append(tag)
    return " ".join(clean[:limit])


def render_content(item: dict[str, Any], hashtag_limit: int) -> str:
    body = str(item["body"]).strip()
    hashtags = sanitize_hashtags(list(item.get("hashtags", [])), hashtag_limit)
    if hashtags:
        return f"{body}\n\n{hashtags}"
    return body


def daily_counter(state: dict[str, Any], name: str) -> int:
    today = utc_now().date().isoformat()
    state.setdefault("daily", {}).setdefault(today, {})
    return int(state["daily"][today].get(name, 0))


def bump_daily(state: dict[str, Any], name: str) -> None:
    today = utc_now().date().isoformat()
    state.setdefault("daily", {}).setdefault(today, {})
    state["daily"][today][name] = daily_counter(state, name) + 1
    for day in list(state["daily"]):
        if day != today:
            del state["daily"][day]


def next_items(plan: list[dict[str, Any]], state: dict[str, Any], published_titles: set[str], max_posts: int) -> list[tuple[int, dict[str, Any]]]:
    start = int(state.get("content_index", 0))
    chosen: list[tuple[int, dict[str, Any]]] = []
    for offset in range(len(plan)):
        index = (start + offset) % len(plan)
        item = plan[index]
        title = str(item.get("title", "")).strip()
        if title and title not in published_titles and title not in state.get("published_titles", []):
            chosen.append((index, item))
        if len(chosen) >= max_posts:
            break
    return chosen


def run(args: argparse.Namespace) -> dict[str, Any]:
    plan = read_json(Path(args.content_file), [])
    state = read_json(Path(args.state_file), {"content_index": 0, "published_titles": [], "daily": {}})
    if not isinstance(plan, list) or not plan:
        raise RuntimeError("Content plan is empty or invalid.")

    actions: list[dict[str, Any]] = []
    titles = recent_titles(args.agent_name)
    execute = bool(args.execute)
    token = api_key() if execute else None
    last_posted_at = parse_time(state.get("last_posted_at"))
    if last_posted_at and (utc_now() - last_posted_at).total_seconds() < args.min_post_interval_seconds:
        actions.append({
            "action": "post_cooldown",
            "minimum_seconds": args.min_post_interval_seconds,
            "last_posted_at": state.get("last_posted_at"),
        })
        state["last_run_at"] = utc_now().isoformat()
        if args.execute or args.write_state_on_dry_run:
            write_json(Path(args.state_file), state)
        return {"success": True, "execute": execute, "actions": actions, "state": state}
    remaining_today = args.max_posts_per_day - daily_counter(state, "posts")
    if remaining_today <= 0:
        actions.append({"action": "daily_post_limit_reached", "limit": args.max_posts_per_day})
        state["last_run_at"] = utc_now().isoformat()
        if args.execute or args.write_state_on_dry_run:
            write_json(Path(args.state_file), state)
        return {"success": True, "execute": execute, "actions": actions, "state": state}

    max_posts = max(1, min(args.max_posts, remaining_today))
    items = next_items(plan, state, titles, max_posts)
    if not items:
        actions.append({"action": "no_unique_item_available"})

    for index, item in items:
        payload = {
            "submolt_name": args.submolt,
            "title": str(item["title"]).strip(),
            "content": render_content(item, args.max_hashtags),
        }
        actions.append({"action": "post_candidate", "index": index, "title": payload["title"], "language": item.get("language"), "execute": execute})
        if execute:
            result = request_json("POST", "/posts", token, payload)
            actions.append({"action": "post_result", "success": result.get("success"), "http_status": result.get("http_status"), "post_id": (result.get("post") or {}).get("id")})
            if not result.get("success"):
                continue
            if not verify_if_needed(result, token or "", execute, actions):
                continue
            post_id = created_post_id(result)
            if not post_id:
                actions.append({"action": "post_public_check_failed", "reason": "missing_post_id"})
                continue
            public_result = request_json("GET", f"/posts/{post_id}", token)
            public_post = public_result.get("post") if isinstance(public_result.get("post"), dict) else {}
            usable = bool(public_result.get("success")) and post_is_publicly_usable(public_post)
            actions.append({
                "action": "post_public_check",
                "post_id": post_id,
                "usable": usable,
                "verification_status": public_post.get("verification_status"),
                "is_spam": public_post.get("is_spam"),
            })
            if not usable:
                continue
        state["content_index"] = index + 1
        state.setdefault("published_titles", []).append(payload["title"])
        state["published_titles"] = state["published_titles"][-120:]
        state["last_posted_at"] = utc_now().isoformat()
        bump_daily(state, "posts")

    state["last_run_at"] = utc_now().isoformat()
    if args.execute or args.write_state_on_dry_run:
        write_json(Path(args.state_file), state)
    return {"success": True, "execute": execute, "actions": actions, "state": state}


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the GitHub-to-Moltbook Renova bridge.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Publish to Moltbook.")
    mode.add_argument("--dry-run", action="store_true", help="Do not publish. Default.")
    parser.add_argument("--content-file", default=str(DEFAULT_CONTENT_FILE))
    parser.add_argument("--state-file", default=str(DEFAULT_STATE_FILE))
    parser.add_argument("--agent-name", default=AGENT_NAME)
    parser.add_argument("--submolt", default=DEFAULT_SUBMOLT)
    parser.add_argument("--max-posts", type=int, default=1)
    parser.add_argument("--max-posts-per-day", type=int, default=int(os.getenv("MOLTBOOK_GITHUB_MAX_POSTS_PER_DAY", "8")))
    parser.add_argument("--max-hashtags", type=int, default=int(os.getenv("MOLTBOOK_GITHUB_MAX_HASHTAGS", "2")))
    parser.add_argument(
        "--min-post-interval-seconds",
        type=int,
        default=int(os.getenv("MOLTBOOK_GITHUB_MIN_POST_INTERVAL_SECONDS", "10800")),
    )
    parser.add_argument("--write-state-on-dry-run", action="store_true")
    args = parser.parse_args()

    result = run(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
