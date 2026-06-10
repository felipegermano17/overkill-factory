#!/usr/bin/env python3
"""Fail when public artifacts contain private/internal project residue."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]

SKIP_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".ico", ".pdf", ".tgz", ".zip"}

PATTERN_SPECS = [
    ("private_product_marker", re.compile(r"KAXIS|Kaxis|kaxis")),
    ("private_environment_marker", re.compile(r"\bVM\b")),
    ("private_owner_marker", re.compile(r"Felipe|felipe")),
    ("private_gate_marker", re.compile(r"hermes_kaxis_v2_completion_required")),
    ("private_gate_marker", re.compile(r"Felipe_gate_required|felipe_gate")),
    ("private_runtime_path", re.compile(r"/srv/hermes")),
    ("private_windows_path", re.compile(r"C:\\Users")),
    ("private_windows_path", re.compile(r"C:\\\\Users")),
    ("private_sync_root", re.compile(r"OneDrive")),
    ("private_workspace_marker", re.compile(r"felipe-s-workspace")),
]

BYTE_PATTERN_SPECS = [
    ("private_product_marker", b"KAXIS"),
    ("private_product_marker", b"Kaxis"),
    ("private_product_marker", b"kaxis"),
    ("private_owner_marker", b"Felipe"),
    ("private_owner_marker", b"felipe"),
    ("private_sync_root", b"OneDrive"),
    ("private_windows_path", b"C:\\Users"),
    ("private_windows_path", b"C:\\\\Users"),
    ("private_runtime_path", b"/srv/hermes"),
    ("private_workspace_marker", b"felipe-s-workspace"),
]


def is_negative_test_guard(path_parts: tuple[str, ...], line: str) -> bool:
    """Allow tests to name forbidden markers only when asserting absence."""
    if "tests" not in path_parts:
        return False
    guard_markers = ("assertNotIn", "assertNotRegex", "assertIsNone")
    return any(marker in line for marker in guard_markers)


def rel_parts(rel: str) -> tuple[str, ...]:
    return PurePosixPath(rel).parts


def is_text_rel(rel: str) -> bool:
    path = PurePosixPath(rel)
    if path.suffix.lower() in SKIP_SUFFIXES:
        return False
    if ".git" in path.parts or "__pycache__" in path.parts:
        return False
    if rel == "scripts/public_safety_scan.py":
        return False
    return True


def is_binary_asset_rel(rel: str) -> bool:
    path = PurePosixPath(rel)
    if ".git" in path.parts or "__pycache__" in path.parts:
        return False
    return path.suffix.lower() in SKIP_SUFFIXES


def scan_text(rel: str, text: str) -> list[str]:
    findings: list[str] = []
    parts = rel_parts(rel)
    for lineno, line in enumerate(text.splitlines(), start=1):
        if is_negative_test_guard(parts, line):
            continue
        for category, pattern in PATTERN_SPECS:
            if pattern.search(line):
                findings.append(f"{rel}:{lineno}: {category}")
                break
    return findings


def scan_binary(rel: str, data: bytes) -> list[str]:
    findings: list[str] = []
    for category, pattern in BYTE_PATTERN_SPECS:
        if pattern in data:
            findings.append(f"{rel}:binary: {category}")
            break
    return findings


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def finding_category(finding: str) -> str:
    return finding.rsplit(": ", 1)[-1] if ": " in finding else "unknown"


def safe_ref(value: str | None) -> str | None:
    if value is None:
        return None
    for _, pattern in PATTERN_SPECS:
        if pattern.search(value):
            return "redacted-ref"
    return value


def build_summary(findings: list[str], *, git_ref: str | None = None, created_at: str | None = None) -> dict[str, object]:
    categories = Counter(finding_category(finding) for finding in findings)
    target = {"kind": "git_ref", "ref": safe_ref(git_ref)} if git_ref else {"kind": "worktree"}
    return {
        "$schema": "https://overkill-factory.dev/schemas/public-safety-scan-summary.schema.json",
        "record_type": "public_safety_scan_summary",
        "created_at": created_at or utc_now(),
        "target": target,
        "result": "PASS" if not findings else "FAIL",
        "finding_count": len(findings),
        "categories": [
            {"id": category, "count": count}
            for category, count in sorted(categories.items())
        ],
        "limits": [
            "This summary is public-safe and intentionally omits raw matching lines and raw private markers.",
            "Use the scanner stderr output in a private operator context for exact remediation paths.",
        ],
    }


def scan_worktree(root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    scanner_path = Path(__file__).resolve()
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if path.resolve() == scanner_path:
            continue
        rel = path.relative_to(root).as_posix()
        if is_text_rel(rel):
            text = path.read_text(encoding="utf-8", errors="replace")
            findings.extend(scan_text(rel, text))
        elif is_binary_asset_rel(rel):
            findings.extend(scan_binary(rel, path.read_bytes()))
    return findings


def git_bytes(args: list[str]) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(ROOT), *args],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout


def git_tree_files(git_ref: str) -> list[str]:
    raw = git_bytes(["ls-tree", "-r", "-z", "--name-only", git_ref])
    return [part.decode("utf-8", errors="replace") for part in raw.split(b"\0") if part]


def git_blob(git_ref: str, rel: str) -> bytes:
    return git_bytes(["show", f"{git_ref}:{rel}"])


def scan_git_ref(git_ref: str) -> list[str]:
    findings: list[str] = []
    for rel in git_tree_files(git_ref):
        if is_text_rel(rel):
            data = git_blob(git_ref, rel)
            findings.extend(scan_text(rel, data.decode("utf-8", errors="replace")))
        elif is_binary_asset_rel(rel):
            findings.extend(scan_binary(rel, git_blob(git_ref, rel)))
    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--git-ref",
        help="Scan a committed tree, such as HEAD, origin/main, or a release branch, instead of the dirty worktree.",
    )
    parser.add_argument(
        "--summary-json",
        type=Path,
        help="Write a public-safe JSON summary without raw matching lines or private markers.",
    )
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        findings = scan_git_ref(args.git_ref) if args.git_ref else scan_worktree(ROOT)
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        print(f"git scan failed: {stderr or exc}", file=sys.stderr)
        return 2

    if args.summary_json:
        summary = build_summary(findings, git_ref=args.git_ref)
        args.summary_json.parent.mkdir(parents=True, exist_ok=True)
        args.summary_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK")
    return 0


def main_with_args_for_test(argv: list[str]) -> int:
    return main_with_args(argv)


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
