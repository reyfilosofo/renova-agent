#!/usr/bin/env python3
"""Build a deterministic, auditable NOUS source-delivery archive (stdlib only)."""
from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_NAME = "NOUS_Intelligence_Rooms_MASTER_DELIVERY.zip"
MANIFEST_NAME = "MANIFEST_SHA256.txt"
CHECKSUMS_NAME = "SHA256SUMS.txt"
PREFIX = "nous-intelligence-rooms"
ROOT_FILES = (
    ".env.example", "AGENTS.md", "CODEX_COPY_PASTE_FINAL.txt",
    "Dockerfile", "LICENSE", "README.md", "pyproject.toml", "run.sh",
)
DIRECTORIES = ("app", "deployment", "submission", "tests")
EXCLUDED_PARTS = {"__pycache__", ".git", ".pytest_cache", "dist"}


def files_to_package(root: Path) -> list[Path]:
    """Allowlist sources; never package a credential or a generated artifact tree."""
    paths = [root / name for name in ROOT_FILES]
    for directory in DIRECTORIES:
        paths.extend((root / directory).rglob("*"))
    files = []
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(f"Required delivery source is absent: {path}")
        relative = path.relative_to(root)
        if any(part in EXCLUDED_PARTS for part in relative.parts):
            continue
        if path.is_symlink():
            raise ValueError(f"Refusing symlink in deliverable: {relative}")
        if path.is_dir():
            continue
        # No real .env, secret store, private key, or editor temp files.
        if any(part.startswith(".env") and part != ".env.example" for part in relative.parts):
            raise ValueError(f"Refusing environment file: {relative}")
        if path.name.endswith((".pyc", ".pyo", ".swp", "~")) or path.name in {".DS_Store", "id_rsa"}:
            continue
        files.append(path)
    if not files:
        raise RuntimeError("Nothing selected for packaging")
    return sorted(set(files), key=lambda p: p.relative_to(root).as_posix())


def sha256(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def build_archive(root: Path = ROOT, output_dir: Path | None = None) -> tuple[Path, Path]:
    root = root.resolve()
    destination = output_dir or root / "submission" / "dist"
    destination.mkdir(parents=True, exist_ok=True)
    archive_path = destination / ARCHIVE_NAME
    checksums_path = destination / CHECKSUMS_NAME
    files = files_to_package(root)
    payload = {}
    lines = ["# SHA-256 hashes of files inside the NOUS master archive"]
    for source in files:
        arcname = f"{PREFIX}/{source.relative_to(root).as_posix()}"
        data = source.read_bytes()
        payload[arcname] = data
        lines.append(f"{sha256(data)}  {arcname}")
    manifest = ("\n".join(lines) + "\n").encode("utf-8")
    payload[f"{PREFIX}/{MANIFEST_NAME}"] = manifest

    # Fixed metadata for reproducible byte-identical archives given identical sources.
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in sorted(payload):
            entry = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, payload[name], compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)

    # Verify actual archive content, not merely the source bytes prior to packaging.
    with zipfile.ZipFile(archive_path) as archive:
        if set(archive.namelist()) != set(payload):
            raise RuntimeError("Archive members differ from the selected source files")
        for name, original in payload.items():
            if sha256(archive.read(name)) != sha256(original):
                raise RuntimeError(f"Archive member hash mismatch: {name}")
        if archive.testzip() is not None:
            raise RuntimeError("ZIP CRC verification failed")

    checksums_path.write_text(f"{sha256(archive_path.read_bytes())}  {ARCHIVE_NAME}\n", encoding="utf-8")
    return archive_path, checksums_path


if __name__ == "__main__":
    artifact, sums = build_archive()
    print(f"Archive: {artifact}")
    print(f"SHA-256: {sums.read_text(encoding='utf-8').strip()}")
    print("Integrity: verified (ZIP and internal manifest)")
