#!/usr/bin/env python3
"""Fail when public artifacts contain private/internal project residue."""

from __future__ import annotations

import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".tgz", ".zip"}

PATTERNS = [
    re.compile(r"KAXIS|Kaxis|kaxis"),
    re.compile(r"\bVM\b"),
    re.compile(r"Felipe|felipe"),
    re.compile(r"hermes_kaxis_v2_completion_required"),
    re.compile(r"Felipe_gate_required|felipe_gate"),
    re.compile(r"/srv/hermes"),
    re.compile(r"\bt_[a-f0-9]{8}\b"),
    re.compile(r"\boverkill-factory-live-smoke\b"),
    re.compile(r"\bHermes task:\s*t_[a-f0-9]{8}\b", re.IGNORECASE),
    re.compile(r"\bWhimsical primary board:\s*[A-Za-z0-9_-]{4,}\b"),
    re.compile(r"--board-id\s+(?!<)[A-Za-z0-9_-]{4,}\b"),
    re.compile(r"C:\\Users"),
    re.compile(r"C:\\\\Users"),
    re.compile(r"OneDrive"),
    re.compile(r"felipe-s-workspace"),
]

BYTE_PATTERNS = [
    b"KAXIS",
    b"Kaxis",
    b"kaxis",
    b"Felipe",
    b"felipe",
    b"OneDrive",
    b"C:\\Users",
    b"C:\\\\Users",
    b"/srv/hermes",
    b"overkill-factory-live-smoke",
    b"felipe-s-workspace",
]


def is_negative_test_guard(path: Path, line: str) -> bool:
    """Allow tests to name forbidden markers only when asserting absence."""
    if "tests" not in path.parts:
        return False
    guard_markers = ("assertNotIn", "assertNotRegex", "assertIsNone")
    return any(marker in line for marker in guard_markers)


def is_text_file(path: Path) -> bool:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    if ".git" in path.parts or "__pycache__" in path.parts:
        return False
    if path == Path(__file__).resolve():
        return False
    return True


def is_binary_asset(path: Path) -> bool:
    if ".git" in path.parts or "__pycache__" in path.parts:
        return False
    return path.suffix.lower() in SKIP_SUFFIXES


def main() -> int:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if is_text_file(path):
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if is_negative_test_guard(path, line):
                    continue
                for pattern in PATTERNS:
                    if pattern.search(line):
                        rel = path.relative_to(ROOT).as_posix()
                        findings.append(f"{rel}:{lineno}: {pattern.pattern}")
                        break
        elif is_binary_asset(path):
            data = path.read_bytes()
            for pattern in BYTE_PATTERNS:
                if pattern in data:
                    rel = path.relative_to(ROOT).as_posix()
                    findings.append(f"{rel}:binary: {pattern.decode('ascii', errors='replace')}")
                    break

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
