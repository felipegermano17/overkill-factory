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
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "production" / "release"
VALIDATION_COMMANDS = [
    [sys.executable, "scripts/validate_public_json_artifacts.py"],
    [sys.executable, "scripts/secret_safety_scan.py"],
    [sys.executable, "scripts/public_safety_scan.py"],
    [
        sys.executable,
        "scripts/production_full_product_worker_graph.py",
        "--release-gate-upstream",
        "--require-pass",
        "--out",
        ".tmp/factory-runs/production/release/upstream-worker-graph.json",
        "--md-out",
        ".tmp/factory-runs/production/release/upstream-worker-graph.md",
    ],
]
GENERATED_APPROVAL_MARKERS = ("fixture", "synthetic", "generated:", "placeholder", "todo", "example")


def validation_commands(*, no_write: bool = False) -> list[list[str]]:
    commands = [list(command) for command in VALIDATION_COMMANDS]
    if no_write:
        for command in commands:
            if "scripts/production_full_product_worker_graph.py" in command:
                command.append("--no-write")
    return commands


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


def evidence_provenance(*, created_at: str, producer: str, artifact_refs: list[str]) -> dict[str, Any]:
    return {
        "producer": producer,
        "captured_at": created_at,
        "source_refs": ["products/qvg-public-validation-product"],
        "artifact_refs": artifact_refs,
        "integrity": {
            "product_source_sha256": source_sha256(),
            "git_head": git_value("rev-parse", "HEAD"),
        },
    }


def human_gate_errors(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if record.get("record_type") != "human_gate_record":
        errors.append("human gate record_type must be human_gate_record")
    if record.get("decision") not in {"approved", "approved_with_boundaries"}:
        errors.append("human gate decision must be approved")
    if record.get("evidence_kind") != "real":
        errors.append("production human gate requires evidence_kind=real")
    if record.get("reusable_for_product") is not True:
        errors.append("production human gate requires reusable_for_product=true")
    target = record.get("product_target") if isinstance(record.get("product_target"), dict) else {}
    if target.get("product_id") != "qvg-public-validation-product":
        errors.append("production human gate product_target.product_id must match")
    approval_ref = str(record.get("approval_event_id") or record.get("approval_event_ref") or record.get("decision_source") or "").strip()
    if not approval_ref:
        errors.append("production human gate requires approval_event_id or approval_event_ref")
    elif any(marker in approval_ref.lower() for marker in GENERATED_APPROVAL_MARKERS):
        errors.append("production human gate cannot use generated, fixture, synthetic or placeholder approval evidence")
    for field in ("human_actor", "decision_at", "risk_owner", "security_owner", "rollback_owner"):
        if not str(record.get(field) or "").strip():
            errors.append(f"production human gate requires {field}")
    provenance = record.get("evidence_provenance") if isinstance(record.get("evidence_provenance"), dict) else {}
    if not provenance:
        errors.append("production human gate requires evidence_provenance")
    else:
        for field in ("producer", "captured_at", "artifact_refs", "integrity"):
            if provenance.get(field) in (None, "", [], {}):
                errors.append(f"production human gate evidence_provenance.{field} is required")
    return errors


def load_human_gate_record(path: Path) -> dict[str, Any]:
    record = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(record, dict):
        raise ValueError("human gate record must be a JSON object")
    errors = human_gate_errors(record)
    if errors:
        raise ValueError("; ".join(errors))
    return record


def build_release_ops(*, created_at: str, validation: list[dict[str, Any]], human_gate_ref: str = ".tmp/factory-runs/production/release/human-gate-record.json") -> dict[str, Any]:
    head = git_value("rev-parse", "HEAD")
    branch = git_value("branch", "--show-current")
    remote_ref = git_value("ls-remote", "origin", branch)
    validation_passed = all(item["exit_code"] == 0 for item in validation)
    evidence_refs = [
        ".tmp/factory-runs/production/release/release-ops-result.md",
        human_gate_ref,
        ".tmp/factory-runs/production/remote-proof/managed-testbox-result.json",
        ".tmp/factory-runs/production/release/upstream-worker-graph.json",
    ]
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
        "evidence_refs": evidence_refs,
        "evidence_provenance": evidence_provenance(
            created_at=created_at,
            producer="release-ops-worker",
            artifact_refs=evidence_refs,
        ),
        "next_action": "Repeat this gate whenever the release target, product source, branch or authority boundary changes.",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, title: str, payload: dict[str, Any]) -> None:
    lines = [
        f"# {title}",
        "",
        f"Result: `{payload.get('result') or payload.get('decision')}`",
        f"Reusable for product: `{str(payload.get('reusable_for_product')).lower()}`",
        f"Product: `{payload.get('product_target', {}).get('product_id')}`",
        "",
        "## Summary",
        "",
        payload.get("findings_summary") or payload.get("public_redaction_policy") or "Structured human gate record.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--human-gate-record", type=Path, required=True)
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    created_at = utc_now()
    try:
        human_gate = load_human_gate_record(args.human_gate_record)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"human gate record rejected: {exc}", file=sys.stderr)
        return 1
    validation = [run_command(command) for command in validation_commands(no_write=args.no_write)]
    release_ops = build_release_ops(
        created_at=created_at,
        validation=validation,
        human_gate_ref=repo_ref(args.human_gate_record.resolve()),
    )

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
