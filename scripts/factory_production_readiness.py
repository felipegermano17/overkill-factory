#!/usr/bin/env python3
"""Aggregate vFinal production readiness into one public-safe receipt."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "validation" / "factory-production-readiness" / "current-readiness.json"

DEFAULT_PREPILOT_MASTER = ROOT / "validation" / "prepilot" / "master-task-readiness.json"
DEFAULT_RUNTIME_STATUS = ROOT / "validation" / "hermes-live" / "factory-vfinal-runtime-status-check.json"
DEFAULT_PREFLIGHT = ROOT / "validation" / "hermes-production-update-preflight" / "real-runtime-update-blocked.json"
DEFAULT_CONTROL_TOWER = ROOT / "validation" / "control-tower" / "operator-control-tower-production-readiness.json"
DEFAULT_CONTROL_TOWER_DOCTOR = ROOT / "validation" / "control-tower" / "operator-control-tower-private-evidence-doctor.json"
DEFAULT_WORKTREE_INVENTORY = ROOT / "validation" / "release" / "worktree-release-inventory.json"
DEFAULT_RELEASE_INTEGRATION = ROOT / "validation" / "release" / "release-integration-preflight.json"
DEFAULT_PUBLIC_WORKTREE = ROOT / "validation" / "public-safety" / "worktree-summary.json"
DEFAULT_PUBLIC_HEAD = ROOT / "validation" / "public-safety" / "head-summary.json"
DEFAULT_PUBLIC_ORIGIN = ROOT / "validation" / "public-safety" / "origin-main-summary.json"


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def component(component_id: str, path: Path, expected_pass: bool = True) -> dict[str, Any]:
    data = load_json(path)
    if data is None:
        return {
            "id": component_id,
            "status": "MISSING",
            "raw_result": "MISSING",
            "evidence_ref": repo_ref(path),
            "reason": "receipt missing or invalid JSON",
        }
    result = str(data.get("result") or "MISSING")
    status = result if result in {"PASS", "ATTENTION", "BLOCKED"} else "BLOCKED"
    if expected_pass and status != "PASS":
        reason = f"result is {result}, expected PASS"
    else:
        reason = None
    return {
        "id": component_id,
        "status": status,
        "raw_result": result,
        "evidence_ref": repo_ref(path),
        "reason": reason,
    }


def build_readiness(
    *,
    prepilot_master_path: Path = DEFAULT_PREPILOT_MASTER,
    runtime_status_path: Path = DEFAULT_RUNTIME_STATUS,
    preflight_path: Path = DEFAULT_PREFLIGHT,
    control_tower_path: Path = DEFAULT_CONTROL_TOWER,
    control_tower_doctor_path: Path = DEFAULT_CONTROL_TOWER_DOCTOR,
    worktree_inventory_path: Path = DEFAULT_WORKTREE_INVENTORY,
    release_integration_path: Path = DEFAULT_RELEASE_INTEGRATION,
    public_worktree_path: Path = DEFAULT_PUBLIC_WORKTREE,
    public_head_path: Path = DEFAULT_PUBLIC_HEAD,
    public_origin_path: Path = DEFAULT_PUBLIC_ORIGIN,
    created_at: str | None = None,
) -> dict[str, Any]:
    components = [
        component("prepilot_master_task_readiness", prepilot_master_path),
        component("hermes_vfinal_runtime_status_check", runtime_status_path),
        component("hermes_real_runtime_update_preflight", preflight_path),
        component("operator_control_tower_production_readiness", control_tower_path),
        component("operator_control_tower_private_evidence_doctor", control_tower_doctor_path),
        component("worktree_release_inventory", worktree_inventory_path, expected_pass=False),
        component("release_integration_preflight", release_integration_path),
        component("public_safety_worktree", public_worktree_path),
        component("public_safety_head", public_head_path),
        component("public_safety_origin_main", public_origin_path),
    ]

    blocking_items: list[str] = []
    attention_items: list[str] = []
    for item in components:
        if item["status"] in {"BLOCKED", "MISSING"}:
            blocking_items.append(item["id"])
        elif item["status"] == "ATTENTION":
            attention_items.append(item["id"])

    preflight = load_json(preflight_path) or {}
    for blocker in preflight.get("blocking_items", []):
        if isinstance(blocker, str):
            blocking_items.append(f"preflight:{blocker}")

    if blocking_items:
        result = "BLOCKED"
        summary = "Factory vFinal is not production-ready; required production gates are still blocked."
    elif attention_items:
        result = "ATTENTION"
        summary = "Factory vFinal has no blocking production gate, but release attention items remain."
    else:
        result = "PASS"
        summary = (
            "Factory vFinal prepilot readiness evidence is complete for the current public-safe setup. "
            "This is not a claim that every canonical promise is fully implemented end-to-end for every product."
        )

    component_status = {item["id"]: item["status"] for item in components}
    next_required_actions: list[str] = []
    if component_status.get("operator_control_tower_private_evidence_doctor") != "PASS":
        next_required_actions.append("replace private Control Tower placeholders with real cockpit/runtime evidence")
        next_required_actions.append("rerun operator_control_tower_private_evidence_doctor.py until it passes")
    if component_status.get("prepilot_master_task_readiness") != "PASS":
        next_required_actions.append("complete the 9-task prepilot readiness receipt")
    if component_status.get("hermes_vfinal_runtime_status_check") != "PASS":
        next_required_actions.append("rerun and pass the public-safe read-only Hermes runtime status check")
    if component_status.get("operator_control_tower_production_readiness") != "PASS":
        next_required_actions.append("run operator_control_tower_proof.py to create the production proof")
    if component_status.get("hermes_real_runtime_update_preflight") != "PASS":
        next_required_actions.append("regenerate the complete Hermes update receipt and rerun the real-runtime update preflight")
    if component_status.get("release_integration_preflight") != "PASS":
        next_required_actions.append("pass the release integration preflight")
    if component_status.get("public_safety_origin_main") != "PASS":
        next_required_actions.append("integrate the public-safe worktree into the release ref and rerun public-safety scans for HEAD and origin/main")
    if not next_required_actions and attention_items:
        next_required_actions.append("review attention items before final production approval")
    if not blocking_items:
        next_required_actions = [
            "perform final operator review",
            "apply the explicit real-runtime update gate only after human approval",
        ]

    evidence_refs = sorted({item["evidence_ref"] for item in components})
    readiness = {
        "$schema": "https://overkill-factory.dev/schemas/factory-production-readiness.schema.json",
        "record_type": "factory_production_readiness",
        "created_at": created_at or utc_now(),
        "result": result,
        "summary": summary,
        "components": components,
        "blocking_items": sorted(set(blocking_items)),
        "attention_items": sorted(set(attention_items)),
        "evidence_refs": evidence_refs,
        "next_required_actions": next_required_actions,
        "limits": [
            "This aggregate receipt is public-safe and intentionally omits raw private evidence.",
            "It summarizes existing receipts; it does not replace the underlying gate receipts.",
            "PASS here means the current prepilot setup has required receipts; it does not convert contract-backed canonical stages into universal live production proof.",
            "A PASS result still requires explicit operator approval before any real runtime update.",
        ],
    }
    return readiness


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    receipt = build_readiness()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
