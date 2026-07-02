#!/usr/bin/env python3
"""Validate that narrative docs cannot masquerade as current runtime authority."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent if (ROOT.parent / ".github").exists() else ROOT
DOC_ROOT = REPO_ROOT / "docs"
GOVERNED_DIRS = [
    DOC_ROOT / "risks",
]
REQUIRED_MARKERS = (
    "Document status:",
    "Current authority:",
    "Runtime boundary:",
)
KNOWN_STATUSES = (
    "CURRENT SUPPORTING GUIDE",
    "CURRENT RUNTIME EVIDENCE",
    "ACTIVE BACKLOG",
    "ACTIVE RISK REGISTER",
    "ACTIVE PILOT GUIDE",
    "HISTORICAL EVIDENCE",
    "LEGACY METHOD",
)
CURRENT_AUTHORITY_REFS = (
    "README.md",
    "docs/en/factory-manual.md",
    "docs/en/technical-reference.md",
    "factory/scripts/factoryctl.py",
    "factory/schemas/",
    "factory/tests/",
)
PUBLIC_DOC_FORBIDDEN_DIRS = (
    DOC_ROOT / "methodology",
    DOC_ROOT / "roadmap",
    DOC_ROOT / "reviews",
    DOC_ROOT / "planning",
    DOC_ROOT / "pilots",
    DOC_ROOT / "validation",
    DOC_ROOT / "research",
    DOC_ROOT / "maps",
    DOC_ROOT / "illustrations",
)
AMBIGUITY_TERMS = (
    "still open",
    "remaining",
    "not yet",
    "future",
    "reserved for next",
    "current remaining",
    "still needed",
    "this does not claim",
    "does not prove",
    "not enough",
    "todo",
    "tbd",
)
CANONICAL_PUBLIC_DOCS = {
    "index.md",
    "en/factory-manual.md",
    "en/technical-reference.md",
    "pt-BR/factory-manual.md",
    "pt-BR/technical-reference.md",
}


def governed_markdown_files() -> list[Path]:
    paths: list[Path] = []
    for directory in GOVERNED_DIRS:
        if directory.exists():
            paths.extend(sorted(directory.glob("*.md")))
    return paths


def front_matter(path: Path) -> str:
    lines = path.read_text(encoding="utf-8").splitlines()
    return "\n".join(lines[:12])


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    rel = path.relative_to(REPO_ROOT).as_posix()
    head = front_matter(path)
    for marker in REQUIRED_MARKERS:
        if marker not in head:
            errors.append(f"{rel}: missing governance marker {marker}")
    if "Document status:" in head and not any(status in head for status in KNOWN_STATUSES):
        errors.append(f"{rel}: unknown document status")
    if "Current authority:" in head and not any(ref in head for ref in CURRENT_AUTHORITY_REFS):
        errors.append(f"{rel}: current authority does not point to a current runtime/user-path artifact")
    if ("HISTORICAL EVIDENCE" in head or "LEGACY METHOD" in head) and "not the current" not in head.lower():
        errors.append(f"{rel}: historical/legacy document must explicitly say it is not the current rule")
    if ("ACTIVE BACKLOG" in head or "ACTIVE RISK REGISTER" in head) and "not a runtime" not in head.lower():
        errors.append(f"{rel}: backlog/risk document must explicitly say it is not a runtime gate")
    return errors


def validate_ambiguous_docs_have_status() -> list[str]:
    errors: list[str] = []
    for path in sorted((DOC_ROOT).rglob("*.md")):
        rel_path = path.relative_to(DOC_ROOT).as_posix()
        if rel_path.startswith("reference/") or rel_path in CANONICAL_PUBLIC_DOCS:
            continue
        head = front_matter(path)
        if "Document status:" in head:
            continue
        text = path.read_text(encoding="utf-8").lower()
        hits = [term for term in AMBIGUITY_TERMS if term in text]
        if hits:
            rel = path.relative_to(REPO_ROOT).as_posix()
            errors.append(f"{rel}: contains ambiguous planning/status language without governance banner: {', '.join(hits)}")
    return errors


def validate_forbidden_public_doc_dirs_absent() -> list[str]:
    errors: list[str] = []
    for directory in PUBLIC_DOC_FORBIDDEN_DIRS:
        if directory.exists() and any(directory.rglob("*")):
            rel = directory.relative_to(ROOT).as_posix()
            errors.append(f"{rel}: historical/narrative public doc directory must not be committed")
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(validate_forbidden_public_doc_dirs_absent())
    for path in governed_markdown_files():
        errors.extend(validate(path))
    errors.extend(validate_ambiguous_docs_have_status())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
