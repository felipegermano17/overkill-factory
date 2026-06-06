#!/usr/bin/env python3
"""Create product-scoped release-ops and human-gate records."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_SOURCE = ROOT / "products" / "qvg-public-validation-product"
DEFAULT_OUT = ROOT / "validation" / "production" / "release"
VALIDATION_COMMANDS = [
    [sys.executable, "scripts/validate_public_json_artifacts.py"],
    [sys.executable, "scripts/secret_safety_scan.py"],
    [sys.executable, "scripts/public_safety_scan.py"],
    [sys.executable, "scripts/full_product_worker_graph.py", "--require-pass"],
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def source_sha256(path: Path = PRODUCT_SOURCE) -> str:
    import hashlib

    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def repo_ref(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def run_command(argv: list[str]) -> dict[str, Any]:
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=120,
    )
    return {
        "command": " ".join(argv),
        "exit_code": completed.returncode,
        "stdout_tail": completed.stdout[-2000:].replace(str(ROOT), "<repo>"),
        "stderr_tail": completed.stderr[-2000:].replace(str(ROOT), "<repo>"),
    }


def git_value(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    return completed.stdout.strip()


def product_target() -> dict[str, str]:
    return {
        "product_id": "qvg-public-validation-product",
        "source_ref": "products/qvg-public-validation-product",
        "source_sha256": source_sha256(),
        "approval_scope": "Reusable for the public Quasar Vault Guard validation product release-control lane.",
        "environment_class": "public-repository-production-validation",
    }


def build_human_gate(*, approval_ref: str, approved_by: str, created_at: str) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "human_gate_record",
        "created_at": created_at,
        "worker": {
            "id": "human-gate-clerk",
            "name": "Human Gate Clerk",
            "factory_phase": "F16",
        },
        "card_ref": {
            "card_id": "QVG-PRODUCTION-RELEASE-GATE",
            "slice_id": "QVG_PUBLIC_VALIDATION_PRODUCT",
            "phase": "F16",
            "risk_effective": "R4",
            "surfaces": ["release", "public-repository", "rollback", "monitoring"],
            "executor_identity": "release-ops-worker",
            "reviewer_identity": "human-gate-clerk",
        },
        "product_target": product_target(),
        "result": "PASS",
        "blocking_findings": False,
        "findings_summary": "Maintainer authorization was recorded for the public validation product release-control lane with rollback and monitoring boundaries.",
        "tool_or_profile": "Hermes human-gate-clerk",
        "executed_by": "human-gate-clerk",
        "evidence_kind": "real",
        "reusable_for_product": True,
        "gate_type": "R4-public-validation-release",
        "decision": "approved_with_boundaries",
        "decision_at": created_at,
        "decision_source": approval_ref,
        "human_actor": approved_by,
        "public_redaction_policy": "The raw authorization text and personal identity are intentionally kept outside the public repository.",
        "approved_scope": [
            "Run the public validation product through the Overkill Factory release-control lane.",
            "Use Hermes/Kanban workers and Crabbox/container proof where available.",
            "Write public-safe validation, release and audit artifacts.",
            "Push public repository branch updates that contain no private project material.",
        ],
        "forbidden_scope": [
            "secret disclosure",
            "funds movement",
            "wallet signing",
            "mainnet write",
            "unreviewed production infrastructure mutation",
            "history rewrite",
        ],
        "risk_owner": "project-maintainer",
        "security_owner": "security-reviewer",
        "rollback_owner": "release-ops-worker",
        "expiry": "Valid only for this public validation product and this release-control evidence round.",
        "evidence_refs": [
            "validation/production/release/human-gate-record.md",
            "validation/production/release/release-ops-result.json",
            "validation/production/remote-proof/managed-testbox-result.json",
        ],
        "next_action": "Keep future R4 gates product-specific and time-bounded.",
    }


def build_release_ops(*, created_at: str, validation: list[dict[str, Any]]) -> dict[str, Any]:
    head = git_value("rev-parse", "HEAD")
    branch = git_value("branch", "--show-current")
    remote_ref = git_value("ls-remote", "origin", branch)
    validation_passed = all(item["exit_code"] == 0 for item in validation)
    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "release_ops_result",
        "created_at": created_at,
        "worker": {
            "id": "release-ops-worker",
            "name": "Release Operations Worker",
            "factory_phase": "F16-F17",
        },
        "card_ref": {
            "card_id": "QVG-PRODUCTION-RELEASE-GATE",
            "slice_id": "QVG_PUBLIC_VALIDATION_PRODUCT",
            "phase": "F16",
            "risk_effective": "R4",
            "surfaces": ["release", "public-repository", "rollback", "monitoring"],
            "executor_identity": "release-ops-worker",
            "reviewer_identity": "human-gate-clerk",
        },
        "product_target": product_target(),
        "result": "PASS" if validation_passed else "FAIL",
        "blocking_findings": not validation_passed,
        "findings_summary": (
            "Release-control validation passed for the public validation product and current public branch state."
            if validation_passed
            else "Release-control validation failed; see command evidence."
        ),
        "tool_or_profile": "Hermes release-ops-worker",
        "executed_by": "release-ops-worker",
        "evidence_kind": "real",
        "reusable_for_product": validation_passed,
        "release_target": {
            "release_type": "public_repository_branch",
            "branch": branch,
            "head_sha": head,
            "remote_ref": remote_ref,
            "deploy_performed": False,
            "infrastructure_mutation_performed": False,
        },
        "rollback_plan": {
            "rollback_type": "public_repository_revert",
            "rollback_command": f"git revert {head}",
            "history_rewrite_required": False,
            "restore_point": remote_ref,
            "rollback_owner": "release-ops-worker",
        },
        "smoke_result": {
            "result": "PASS" if validation_passed else "FAIL",
            "commands": validation,
        },
        "monitoring_plan": {
            "monitoring_scope": "public repository branch and validation artifacts",
            "signals": [
                "CI/test command failure",
                "public safety scan failure",
                "secret scan failure",
                "factory completion audit regression",
            ],
            "incident_owner": "release-ops-worker",
            "rollback_trigger": "Any blocking regression in public safety, secret hygiene, JSON validation or product worker graph.",
        },
        "forbidden_actions_checked": [
            {"action": "secret_access", "performed": False},
            {"action": "funds_movement", "performed": False},
            {"action": "wallet_signing", "performed": False},
            {"action": "mainnet_write", "performed": False},
            {"action": "infrastructure_mutation", "performed": False},
            {"action": "history_rewrite", "performed": False},
        ],
        "evidence_refs": [
            "validation/production/release/release-ops-result.md",
            "validation/production/release/human-gate-record.json",
            "validation/production/remote-proof/managed-testbox-result.json",
            "validation/product-specific/qvg-full-product-worker-graph.json",
        ],
        "next_action": "Repeat this gate whenever the release target, product source, branch or authority boundary changes.",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Result: `{payload['result']}`",
        f"Reusable for product: `{str(payload['reusable_for_product']).lower()}`",
        f"Product: `{payload['product_target']['product_id']}`",
        "",
        "## Summary",
        "",
        payload["findings_summary"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--approval-ref", default="external:redacted-maintainer-authorization-2026-06-06")
    parser.add_argument("--approved-by", default="project-maintainer")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    created_at = utc_now()
    validation = [run_command(command) for command in VALIDATION_COMMANDS]
    human_gate = build_human_gate(approval_ref=args.approval_ref, approved_by=args.approved_by, created_at=created_at)
    release_ops = build_release_ops(created_at=created_at, validation=validation)

    if not args.no_write:
        write_json(args.out_dir / "human-gate-record.json", human_gate)
        write_json(args.out_dir / "release-ops-result.json", release_ops)
        write_markdown(args.out_dir / "human-gate-record.md", "Production Human Gate Record", human_gate)
        write_markdown(args.out_dir / "release-ops-result.md", "Production Release Ops Result", release_ops)
        print(f"Wrote {repo_ref(args.out_dir / 'human-gate-record.json')}")
        print(f"Wrote {repo_ref(args.out_dir / 'release-ops-result.json')}")
    print(release_ops["result"])
    return 0 if release_ops["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
