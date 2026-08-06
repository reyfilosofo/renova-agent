"""Fail CI when tracked files contain common credential material."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
MAX_SCAN_BYTES = 5_000_000

SECRET_PATTERNS = {
    "AWS access key": re.compile(rb"AKIA[0-9A-Z]{16}"),
    "GitHub token": re.compile(rb"gh[pousr]_[A-Za-z0-9_]{20,}"),
    "OpenAI-style secret": re.compile(rb"sk-[A-Za-z0-9_-]{20,}"),
    "private key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}

FORBIDDEN_SUFFIXES = {".key", ".pem", ".p12", ".pfx"}
FORBIDDEN_PARTS = {"credentials", "secrets"}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / entry.decode("utf-8") for entry in result.stdout.split(b"\0") if entry]


def forbidden_path(path: Path) -> str | None:
    relative = path.relative_to(ROOT)
    lowered_parts = {part.casefold() for part in relative.parts}
    if path.suffix.casefold() in FORBIDDEN_SUFFIXES:
        return "credential file extension"
    if lowered_parts & FORBIDDEN_PARTS:
        return "credential directory"
    if path.name == ".env" or (path.name.startswith(".env.") and path.name != ".env.example"):
        return "environment file"
    return None


def scan() -> list[str]:
    findings: list[str] = []
    for path in tracked_files():
        path_problem = forbidden_path(path)
        if path_problem:
            findings.append(f"{path.relative_to(ROOT)}: {path_problem}")
            continue
        try:
            if path.stat().st_size > MAX_SCAN_BYTES:
                continue
            content = path.read_bytes()
        except (OSError, UnicodeError):
            continue
        for label, pattern in SECRET_PATTERNS.items():
            if pattern.search(content):
                findings.append(f"{path.relative_to(ROOT)}: possible {label}")
    return findings


def main() -> int:
    findings = scan()
    if findings:
        print("Repository safety check failed:")
        for finding in findings:
            print(f"- {finding}")
        return 1
    print("Repository safety check passed: no tracked credential patterns found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
