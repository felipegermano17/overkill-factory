#!/usr/bin/env python3
"""Lightweight secret scanner for public CI.

This is not a replacement for Gitleaks or TruffleHog. It catches obvious token
formats, private key blocks and high-entropy assignments in public artifacts.
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".tgz", ".zip"}
SKIP_PARTS = {".git", "__pycache__"}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(
        r"\b(?:api[_-]?key|secret|token|password|passwd)\b\s*(?::(?!:)|=)\s*['\"]?[^'\"\s]{16,}",
        re.IGNORECASE,
    ),
]

ASSIGNMENT_RE = re.compile(
    r"\b(?:api[_-]?key|secret|token|password|passwd|private[_-]?key)\b\s*(?::(?!:)|=)\s*['\"]?([A-Za-z0-9_./+=-]{24,})",
    re.IGNORECASE,
)

ALLOW_HINTS = (
    "example",
    "placeholder",
    "not-a-secret",
    "fake",
    "dummy",
    "redacted",
    "test fixture",
)


def entropy(value: str) -> float:
    if not value:
        return 0.0
    counts = {char: value.count(char) for char in set(value)}
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in counts.values())


def should_scan(path: Path) -> bool:
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    return not any(part in SKIP_PARTS for part in path.parts)


def allowed_fixture_line(line: str) -> bool:
    lowered = line.lower()
    return any(hint in lowered for hint in ALLOW_HINTS)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_summary(findings: list[str]) -> dict[str, object]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/secret-safety-scan-summary.schema.json",
        "record_type": "secret_safety_scan_summary",
        "created_at": utc_now(),
        "result": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "artifact_classes_checked": ["public_repository_tree", "publication_candidate"],
        "limits": [
            "This summary intentionally omits raw secret-like values and exact matching lines.",
            "Use stderr in a private operator context for remediation paths.",
        ],
    }


def scan() -> list[str]:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or not should_scan(path):
            continue
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append(f"{rel}:{lineno}: secret-like pattern")
                    break
            if allowed_fixture_line(line):
                continue
            for match in ASSIGNMENT_RE.finditer(line):
                candidate = match.group(1)
                if len(candidate) >= 32 and entropy(candidate) >= 4.2:
                    findings.append(f"{rel}:{lineno}: high-entropy secret-like assignment")
                    break
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-json", type=Path, help="Write public-safe JSON summary without raw secret material.")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = scan()
    if args.summary_json:
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(build_summary(findings), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK")
    return 0


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
