#!/usr/bin/env python3
"""Create a public-safe inventory of the current release worktree.

The inventory intentionally avoids raw file lists. It is meant to answer:
is this worktree mostly product/release material, cleanup junk, or unknown
state that needs human review before staging or deletion?
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "validation" / "release" / "worktree-release-inventory.json"


PRODUCT_TOP_LEVELS = {
    ".github",
    "adapters",
    "agents",
    "docs",
    "examples",
    "pilots",
    "schemas",
    "scripts",
    "skills",
    "templates",
    "tests",
    "validation",
}
SAFE_CLEANUP_SUFFIXES = {".pyc", ".pyo", ".tmp", ".temp", ".log"}
SAFE_CLEANUP_PARTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".coverage"}
GENERATED_RECEIPT_PATHS = {
    "validation/factory-production-readiness/current-readiness.json",
    "validation/public-safety/head-summary.json",
    "validation/public-safety/origin-main-summary.json",
    "validation/public-safety/worktree-summary.json",
    "validation/release/release-integration-preflight.json",
    "validation/release/worktree-release-inventory.json",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_git_status() -> list[tuple[str, str]]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    chunks = result.stdout.decode("utf-8", errors="replace").split("\0")
    entries: list[tuple[str, str]] = []
    index = 0
    while index < len(chunks):
        chunk = chunks[index]
        index += 1
        if not chunk:
            continue
        status = chunk[:2]
        path = chunk[3:]
        if status.startswith("R") or status.startswith("C"):
            if index < len(chunks):
                # In porcelain -z, rename/copy records include the old path in
                # the next NUL chunk. The new path is enough for this summary.
                index += 1
        entries.append((status, path))
    return entries


def top_level(path: str) -> str:
    return path.replace("\\", "/").split("/", 1)[0] or "."


def classify(path: str, status: str) -> str:
    normalized = path.replace("\\", "/")
    name = normalized.rsplit("/", 1)[-1]
    parts = set(normalized.split("/"))
    suffix = Path(name).suffix.lower()
    if normalized in GENERATED_RECEIPT_PATHS:
        return "generated_receipt"
    if suffix in SAFE_CLEANUP_SUFFIXES or parts.intersection(SAFE_CLEANUP_PARTS):
        return "safe_cleanup_candidate"
    if top_level(path) in PRODUCT_TOP_LEVELS or path in {"README.md", "LICENSE", "NOTICE.md", ".env.example"}:
        return "release_candidate_material"
    if status == "??":
        return "needs_human_review"
    return "needs_human_review"


def count_status(entries: Iterable[tuple[str, str]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for status, _ in entries:
        counts[status] += 1
    return dict(sorted(counts.items()))


def broad_counts(entries: list[tuple[str, str]]) -> dict[str, int]:
    counts = {
        "entries": len(entries),
        "modified": 0,
        "added": 0,
        "deleted": 0,
        "renamed": 0,
        "untracked": 0,
    }
    for status, _ in entries:
        if "M" in status:
            counts["modified"] += 1
        if "A" in status:
            counts["added"] += 1
        if "D" in status:
            counts["deleted"] += 1
        if "R" in status:
            counts["renamed"] += 1
        if status == "??":
            counts["untracked"] += 1
    return counts


def build_inventory(entries: list[tuple[str, str]], created_at: str | None = None) -> dict[str, object]:
    top_levels: Counter[str] = Counter()
    classifications: Counter[str] = Counter()
    for status, path in entries:
        top_levels[top_level(path)] += 1
        classifications[classify(path, status)] += 1

    safe_cleanup = classifications.get("safe_cleanup_candidate", 0)
    needs_review = classifications.get("needs_human_review", 0)
    release_material = classifications.get("release_candidate_material", 0)
    generated_receipts = classifications.get("generated_receipt", 0)
    blocking_items: list[str] = []
    if safe_cleanup:
        blocking_items.append("safe_cleanup_candidates_present")
    if needs_review:
        blocking_items.append("needs_human_review_entries_present")

    if needs_review:
        result = "BLOCKED"
    elif safe_cleanup or release_material:
        result = "ATTENTION"
    else:
        result = "PASS"

    inventory = {
        "$schema": "https://overkill-factory.dev/schemas/worktree-release-inventory.schema.json",
        "record_type": "worktree_release_inventory",
        "created_at": created_at or utc_now(),
        "result": result,
        "scope": "current git worktree release hygiene summary",
        "counts": broad_counts(entries),
        "status_counts": count_status(entries),
        "top_level_counts": dict(sorted(top_levels.items())),
        "classification_counts": dict(sorted(classifications.items())),
        "cleanup_policy": {
            "broad_cleanup_allowed": False,
            "safe_cleanup_candidates": safe_cleanup,
            "release_candidate_entries": release_material,
            "generated_receipt_entries": generated_receipts,
            "needs_human_review_entries": needs_review,
        },
        "blocking_items": blocking_items,
        "limits": [
            "This public-safe report intentionally omits raw file paths.",
            "ATTENTION can still mean expected release material is present.",
            "Generated validation receipts are classified separately from release-candidate product changes.",
            "Do not run broad cleanup from this report; inspect and classify exact paths outside the public receipt first.",
        ],
    }
    return inventory


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.out.is_absolute():
        args.out = ROOT / args.out
    inventory = build_inventory(run_git_status())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    try:
        out_ref = str(args.out.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        out_ref = f"external:{args.out.name}"
    print(json.dumps({"result": inventory["result"], "out": out_ref}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
