#!/usr/bin/env python3
"""Check whether the public-safe worktree is ready to become a release ref."""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "release" / "release-integration-preflight.json"
DEFAULT_INVENTORY = ROOT / ".tmp" / "factory-runs" / "release" / "worktree-release-inventory.json"
DEFAULT_PUBLIC_WORKTREE = ROOT / ".tmp" / "factory-runs" / "public-safety" / "worktree-summary.json"
DEFAULT_PUBLIC_HEAD = ROOT / ".tmp" / "factory-runs" / "public-safety" / "head-summary.json"
DEFAULT_PUBLIC_ORIGIN = ROOT / ".tmp" / "factory-runs" / "public-safety" / "origin-main-summary.json"
GENERATED_RECEIPT_PATHS = {
    ".tmp/factory-runs/factory-production-readiness/current-readiness.json",
    ".tmp/factory-runs/public-safety/head-summary.json",
    ".tmp/factory-runs/public-safety/origin-main-summary.json",
    ".tmp/factory-runs/public-safety/worktree-summary.json",
    ".tmp/factory-runs/release/release-integration-preflight.json",
    ".tmp/factory-runs/release/worktree-release-inventory.json",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def git_text(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout.strip()


def status_entry_counts() -> tuple[int, int]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    chunks = result.stdout.decode("utf-8", errors="replace").split("\0")
    total = 0
    generated_receipts = 0
    index = 0
    while index < len(chunks):
        chunk = chunks[index]
        index += 1
        if not chunk:
            continue
        total += 1
        status = chunk[:2]
        path = chunk[3:].replace("\\", "/")
        if path in GENERATED_RECEIPT_PATHS:
            generated_receipts += 1
        if status.startswith("R") or status.startswith("C"):
            if index < len(chunks):
                index += 1
    return total, generated_receipts


def build_preflight(
    *,
    inventory_path: Path = DEFAULT_INVENTORY,
    public_worktree_path: Path = DEFAULT_PUBLIC_WORKTREE,
    public_head_path: Path = DEFAULT_PUBLIC_HEAD,
    public_origin_path: Path = DEFAULT_PUBLIC_ORIGIN,
    created_at: str | None = None,
    branch_name: str | None = None,
    status_entries: int | None = None,
    generated_status_entries: int | None = None,
) -> dict[str, Any]:
    inventory = load_json(inventory_path)
    public_worktree = load_json(public_worktree_path)
    public_head = load_json(public_head_path)
    public_origin = load_json(public_origin_path)

    branch = branch_name if branch_name is not None else git_text("branch", "--show-current")
    actual_status_entries = actual_generated_entries = 0
    if status_entries is None or generated_status_entries is None:
        actual_status_entries, actual_generated_entries = status_entry_counts()
    entries = status_entries if status_entries is not None else actual_status_entries
    generated_from_status = (
        generated_status_entries if generated_status_entries is not None else actual_generated_entries
    )
    cleanup_policy = inventory.get("cleanup_policy") if isinstance(inventory.get("cleanup_policy"), dict) else {}
    release_candidate_entries = int(cleanup_policy.get("release_candidate_entries") or 0)
    generated_receipt_entries = max(int(cleanup_policy.get("generated_receipt_entries") or 0), generated_from_status)
    needs_human_review_entries = int(cleanup_policy.get("needs_human_review_entries") or 0)
    safe_cleanup_candidates = int(cleanup_policy.get("safe_cleanup_candidates") or 0)
    unintegrated_release_entries = max(entries - generated_from_status, 0)

    checks = {
        "worktree_public_safety_passed": public_worktree.get("result") == "PASS",
        "head_public_safety_passed": public_head.get("result") == "PASS",
        "origin_main_public_safety_passed": public_origin.get("result") == "PASS",
        "worktree_inventory_has_no_unknown_entries": needs_human_review_entries == 0,
        "worktree_inventory_has_no_cleanup_candidates": safe_cleanup_candidates == 0,
        "worktree_has_release_candidate_material": release_candidate_entries > 0,
        "release_ref_has_no_unintegrated_worktree_entries": unintegrated_release_entries == 0,
        "current_branch_is_not_dirty_main": not (branch == "main" and unintegrated_release_entries > 0),
    }
    release_candidate_safe_to_prepare = (
        checks["worktree_public_safety_passed"]
        and checks["worktree_inventory_has_no_unknown_entries"]
        and checks["worktree_inventory_has_no_cleanup_candidates"]
        and checks["worktree_has_release_candidate_material"]
    )

    blocking_items = [key for key, value in checks.items() if not value and key != "worktree_has_release_candidate_material"]
    attention_items: list[str] = []
    if checks["worktree_has_release_candidate_material"] and unintegrated_release_entries > 0:
        attention_items.append("release_candidate_material_waiting_for_integration")

    if blocking_items:
        result = "BLOCKED"
    elif attention_items:
        result = "ATTENTION"
    else:
        result = "PASS"

    next_required_actions = []
    if not checks["current_branch_is_not_dirty_main"]:
        next_required_actions.append("move release-candidate work off dirty main or commit through an explicit release branch")
    if not checks["release_ref_has_no_unintegrated_worktree_entries"]:
        next_required_actions.append("integrate the public-safe worktree into the target release ref")
    if not checks["head_public_safety_passed"] or not checks["origin_main_public_safety_passed"]:
        next_required_actions.append("rerun exact public-safety scans after the release ref is updated")
    if not next_required_actions:
        next_required_actions.append("release ref is ready for final production gate review")

    return {
        "$schema": "https://overkill-factory.dev/schemas/release-integration-preflight.schema.json",
        "record_type": "release_integration_preflight",
        "created_at": created_at or utc_now(),
        "result": result,
        "branch": {
            "current": branch,
            "is_main": branch == "main",
        },
        "counts": {
            "status_entries": entries,
            "generated_status_entries": generated_from_status,
            "unintegrated_release_entries": unintegrated_release_entries,
            "release_candidate_entries": release_candidate_entries,
            "generated_receipt_entries": generated_receipt_entries,
            "needs_human_review_entries": needs_human_review_entries,
            "safe_cleanup_candidates": safe_cleanup_candidates,
        },
        "checks": checks,
        "release_candidate_plan": {
            "safe_to_prepare_candidate_branch": release_candidate_safe_to_prepare,
            "recommended_branch": "codex/vfinal-release-candidate",
            "why": (
                "The dirty worktree is public-safe and classified as release-candidate material."
                if release_candidate_safe_to_prepare
                else "Do not prepare a release candidate branch until worktree safety and inventory checks pass."
            ),
            "steps": [
                "create or switch to a dedicated codex/vfinal-release-candidate branch",
                "stage only the public-safe release-candidate worktree",
                "commit the release candidate with validation evidence",
                "rerun public-safety and secret-safety scans on the committed HEAD",
                "push or merge only after the production gate owner accepts the release path",
            ],
            "must_not_do": [
                "do not run broad cleanup against untracked vFinal artifacts",
                "do not publish origin/main while exact HEAD and origin/main scans fail",
                "do not treat a release candidate branch as production readiness",
            ],
        },
        "blocking_items": sorted(blocking_items),
        "attention_items": sorted(attention_items),
        "evidence_refs": [
            repo_ref(inventory_path),
            repo_ref(public_worktree_path),
            repo_ref(public_head_path),
            repo_ref(public_origin_path),
        ],
        "next_required_actions": next_required_actions,
        "limits": [
            "This preflight is public-safe and intentionally omits raw file paths.",
            "It does not stage, commit, push or mutate the release ref.",
            "A PASS result only means the release ref is ready for the final production gate review.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    receipt = build_preflight()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
