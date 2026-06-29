#!/usr/bin/env python3
"""Materialize public-safe receipts consumed by production readiness.

This helper does not approve production. It makes missing gates explicit by
writing schema-valid PASS/BLOCKED receipts that the aggregate readiness checker
can consume.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

PRIVATE_WINDOWS_PATH = "C:" + "\\\\" + "Users"
PRIVATE_SYNC_ROOT = "One" + "Drive"
PRIVATE_RE = re.compile(
    re.escape(PRIVATE_WINDOWS_PATH)
    + r"|"
    + PRIVATE_SYNC_ROOT
    + r"|token|password|secret|webhook|DISCORD_[A-Z_]*TOKEN|auth\.json",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class GatePaths:
    prepilot_master: Path = ROOT / ".tmp" / "factory-runs" / "prepilot" / "master-task-readiness.json"
    runtime_status: Path = ROOT / ".tmp" / "factory-runs" / "hermes-live" / "factory-vfinal-runtime-status-check.json"
    update_preflight: Path = ROOT / ".tmp" / "factory-runs" / "hermes-production-update-preflight" / "real-runtime-update-preflight.json"
    control_tower: Path = ROOT / ".tmp" / "factory-runs" / "control-tower" / "operator-control-tower-production-readiness.json"
    control_tower_doctor: Path = ROOT / ".tmp" / "factory-runs" / "control-tower" / "operator-control-tower-private-evidence-doctor.json"
    release_preflight: Path = ROOT / ".tmp" / "factory-runs" / "release" / "release-integration-preflight.json"
    public_safety_worktree: Path = ROOT / ".tmp" / "factory-runs" / "public-safety" / "worktree-summary.json"
    public_safety_head: Path = ROOT / ".tmp" / "factory-runs" / "public-safety" / "head-summary.json"
    public_safety_origin: Path = ROOT / ".tmp" / "factory-runs" / "public-safety" / "origin-main-summary.json"


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


def public_safe(payload: dict[str, Any]) -> bool:
    return PRIVATE_RE.search(json.dumps(payload, ensure_ascii=False, sort_keys=True)) is None


def evidence_bool(evidence_payload: dict[str, Any] | None, key: str) -> bool:
    if evidence_payload is None:
        return False
    return evidence_payload.get(key) is True


def receipt_result(path: Path) -> str:
    data = load_json(path)
    if data is None:
        return "MISSING"
    result = str(data.get("result") or data.get("decision") or "MISSING").upper()
    return result if result in {"PASS", "ATTENTION", "BLOCKED", "FAIL"} else "BLOCKED"


def proof_status(path: Path) -> str:
    return "PASS" if receipt_result(path) == "PASS" else "BLOCKED"


def evidence(kind: str, path: str, covers: str) -> dict[str, str]:
    return {"kind": kind, "path": path, "covers": covers}


def task(
    number: int,
    task_id: str,
    plain_goal: str,
    status: str,
    summary: str,
    evidence_refs: list[dict[str, str]],
    remaining_limit: str,
) -> dict[str, Any]:
    return {
        "task_number": number,
        "task_id": task_id,
        "plain_goal": plain_goal,
        "status": status,
        "implementation_summary": summary,
        "evidence_refs": evidence_refs,
        "remaining_limit": remaining_limit,
    }


def status_from_result(result: str, pass_status: str) -> str:
    if result == "PASS":
        return pass_status
    if result == "ATTENTION":
        return "ATTENTION"
    return "BLOCKED"


def build_runtime_status(
    *,
    created_at: str | None = None,
    live_evidence: dict[str, Any] | None = None,
) -> dict[str, Any]:
    worker_registry_present = (ROOT / "agents" / "worker-registry.public.json").is_file()
    worker_profiles_present = (ROOT / "docs" / "agents" / "worker-profiles.md").is_file()
    evidence_is_public_safe = live_evidence is None or public_safe(live_evidence)
    checks = {
        "hermes_status_readonly_passed": evidence_bool(live_evidence, "hermes_status_readonly_passed"),
        "profile_list_readonly_passed": evidence_bool(live_evidence, "profile_list_readonly_passed"),
        "gateway_service_running": evidence_bool(live_evidence, "gateway_service_running"),
        "discord_configured": evidence_bool(live_evidence, "discord_configured"),
        "dedicated_gerente_gateway_running": evidence_bool(live_evidence, "dedicated_gerente_gateway_running"),
        "private_product_profile_not_factory_gateway": evidence_bool(
            live_evidence,
            "private_product_profile_not_factory_gateway",
        ),
        "factory_worker_profiles_present": worker_registry_present and worker_profiles_present,
        "factory_profile_set_has_no_conceptual_duplicates": evidence_bool(
            live_evidence,
            "factory_profile_set_has_no_conceptual_duplicates",
        ),
        "raw_private_values_omitted": True
        if live_evidence is None
        else evidence_is_public_safe and evidence_bool(live_evidence, "raw_private_values_omitted"),
    }
    evidence_refs = [
        "agents/worker-registry.public.json",
        "docs/agents/worker-profiles.md",
        "docs/architecture/hermes-integration.md",
    ]
    if live_evidence is not None:
        evidence_refs.extend(
            str(ref)
            for ref in live_evidence.get("evidence_refs", [])
            if isinstance(ref, str) and ref.strip()
        )
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-vfinal-runtime-status-check.schema.json",
        "record_type": "hermes_vfinal_runtime_status_check",
        "created_at": created_at or utc_now(),
        "result": "PASS" if all(checks.values()) else "BLOCKED",
        "scope": "public-safe read-only Hermes vFinal runtime status",
        "checks": checks,
        "evidence_refs": sorted(set(evidence_refs)),
        "limits": [
            "This receipt is public-safe and intentionally omits raw Hermes status, profile, Discord and gateway values.",
            "The default materializer fails closed until a real read-only Hermes status and profile proof is supplied.",
            "Public worker profile files prove local profile definitions only; they do not prove a live Hermes gateway.",
        ],
    }


def required_proof(proof_id: str, path: Path, description: str) -> dict[str, Any]:
    result = receipt_result(path)
    status = "PASS" if result == "PASS" else "BLOCKED"
    reason = None if status == "PASS" else f"{repo_ref(path)} result is {result}"
    return {
        "id": proof_id,
        "status": status,
        "proof_ref": repo_ref(path) if path.exists() else None,
        "description": description,
        "reason": reason,
    }


def build_update_preflight(paths: GatePaths, *, created_at: str | None = None) -> dict[str, Any]:
    proofs = [
        required_proof(
            "hermes_vfinal_runtime_status_check",
            paths.runtime_status,
            "Read-only Hermes status, profile list, gateway and Discord configuration proof.",
        ),
        required_proof(
            "operator_control_tower_private_evidence_doctor",
            paths.control_tower_doctor,
            "Public-safe doctor report for private Control Tower mapping, approval event and bridge health evidence.",
        ),
        required_proof(
            "operator_control_tower_production_readiness",
            paths.control_tower,
            "Redacted production Control Tower proof for operator-facing status and approval registration.",
        ),
        required_proof(
            "release_integration_preflight",
            paths.release_preflight,
            "Release integration preflight from the current committed release candidate state.",
        ),
    ]
    blocking_items = [proof["id"] for proof in proofs if proof["status"] != "PASS"]
    result = "PASS" if not blocking_items else "BLOCKED"
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-production-update-preflight.schema.json",
        "record_type": "hermes_production_update_preflight",
        "created_at": created_at or utc_now(),
        "target": "real-hermes-runtime-update",
        "result": result,
        "required_proofs": proofs,
        "blocking_items": blocking_items,
        "decision": {
            "real_runtime_update": "allowed_for_explicit_operator_gate" if result == "PASS" else "blocked",
            "worker_task_status": "ready_requires_operator_gate" if result == "PASS" else "keep_blocked",
        },
        "evidence_refs": sorted(
            {
                repo_ref(path)
                for path in (
                    paths.runtime_status,
                    paths.control_tower_doctor,
                    paths.control_tower,
                    paths.release_preflight,
                )
                if path.exists()
            }
        ),
        "limits": [
            "This preflight does not run a real Hermes update.",
            "PASS only allows a separately explicit operator gate to perform the real runtime update.",
            "BLOCKED keeps worker tasks blocked and preserves the current runtime.",
        ],
    }


def build_prepilot_master(paths: GatePaths, *, created_at: str | None = None) -> dict[str, Any]:
    release_result = receipt_result(paths.release_preflight)
    runtime_result = receipt_result(paths.runtime_status)
    control_tower_result = receipt_result(paths.control_tower)
    doctor_result = receipt_result(paths.control_tower_doctor)
    update_result = receipt_result(paths.update_preflight)
    public_safety_results = [
        receipt_result(paths.public_safety_worktree),
        receipt_result(paths.public_safety_head),
        receipt_result(paths.public_safety_origin),
    ]
    public_safety_passed = all(result == "PASS" for result in public_safety_results)
    control_tower_ready = control_tower_result == "PASS" and doctor_result == "PASS"

    tasks = [
        task(
            1,
            "public-entrypoint",
            "Keep the external operator entrypoint understandable and public-safe.",
            "PASS_PUBLIC_CONTRACT",
            "README, Portuguese README and validation docs expose the public operator path without private workspace history.",
            [
                evidence("documentation", "README.md", "external operator entrypoint"),
                evidence("documentation", "README.pt-BR.md", "Portuguese public entrypoint"),
                evidence("documentation", "docs/operations/validation-and-release.md", "release validation path"),
            ],
            "Docs do not prove live runtime readiness.",
        ),
        task(
            2,
            "schema-template-contracts",
            "Keep public contracts and templates machine-checkable.",
            "PASS_PUBLIC_CONTRACT",
            "Public schemas and templates are validated by the JSON artifact validator.",
            [
                evidence("script", "scripts/validate_public_json_artifacts.py", "schema and template validation"),
                evidence("schema", "schemas/factory-production-readiness.schema.json", "aggregate readiness contract"),
                evidence("template", "templates/product-sot.json", "public template coverage"),
            ],
            "Schema validity does not imply real execution happened.",
        ),
        task(
            3,
            "worker-surface",
            "Keep worker registry, profiles and permission surfaces aligned.",
            "PASS_PUBLIC_CONTRACT",
            "Worker registry and profiles are present as public source-of-truth docs for external operators.",
            [
                evidence("worker_registry", "agents/worker-registry.public.json", "registered worker ids"),
                evidence("worker_profile", "docs/agents/worker-profiles.md", "worker responsibilities and boundaries"),
                evidence("permission_matrix", "docs/agents/permission-model.md", "authority boundaries"),
            ],
            "Public worker definitions do not prove profiles are installed in Hermes.",
        ),
        task(
            4,
            "operator-bridge",
            "Expose an operator start bridge that observes and relays operator-facing gates without taking factory authority.",
            "PASS_PUBLIC_CONTRACT",
            "The bridge CLI and schemas are present and covered by focused tests; plugin/hook packaging is not part of V3.",
            [
                evidence("script", "scripts/factory_bridge.py", "operator bridge command surface"),
                evidence("schema", "schemas/factory-bridge-run.schema.json", "bridge run contract"),
                evidence("test", "tests/test_factory_bridge.py", "bridge behavior tests"),
            ],
            "The bridge is not the factory and cannot approve gates.",
        ),
        task(
            5,
            "public-safety",
            "Keep the current worktree, HEAD and origin/main public-safe.",
            "PASS_VALIDATION_BATTERY" if public_safety_passed else "BLOCKED",
            "Public-safety summaries are current when their receipt results are PASS.",
            [
                evidence("validation_artifact", repo_ref(paths.public_safety_worktree), "dirty worktree public-safety scan"),
                evidence("validation_artifact", repo_ref(paths.public_safety_head), "HEAD public-safety scan"),
                evidence("validation_artifact", repo_ref(paths.public_safety_origin), "origin/main public-safety scan"),
            ],
            "Regenerate scans after changing public files or release refs.",
        ),
        task(
            6,
            "release-integration",
            "Prove the current release candidate is integrated and not just a dirty worktree.",
            status_from_result(release_result, "PASS_VALIDATION_BATTERY"),
            f"Release integration preflight currently reports {release_result}.",
            [
                evidence("script", "scripts/release_integration_preflight.py", "release integration gate"),
                evidence("validation_artifact", repo_ref(paths.release_preflight), "current release integration receipt"),
            ],
            "Commit and rerun release preflight before release claims.",
        ),
        task(
            7,
            "hermes-runtime-status",
            "Prove Hermes vFinal runtime status through public-safe read-only evidence.",
            status_from_result(runtime_result, "PASS_PUBLIC_RUNTIME"),
            f"Hermes runtime status receipt currently reports {runtime_result}.",
            [
                evidence("schema", "schemas/hermes-vfinal-runtime-status-check.schema.json", "runtime status contract"),
                evidence("validation_artifact", repo_ref(paths.runtime_status), "current runtime status receipt"),
            ],
            "Requires real read-only Hermes status, profile, gateway and Discord evidence.",
        ),
        task(
            8,
            "operator-control-tower-proof",
            "Prove the operator Control Tower with redacted private evidence.",
            "PASS_PRIVATE_PROOF_REDACTED" if control_tower_ready else "BLOCKED",
            f"Control Tower proof reports {control_tower_result}; private evidence doctor reports {doctor_result}.",
            [
                evidence("script", "scripts/operator_control_tower_proof.py", "Control Tower production proof"),
                evidence("validation_artifact", repo_ref(paths.control_tower), "current Control Tower readiness receipt"),
                evidence("validation_artifact", repo_ref(paths.control_tower_doctor), "private evidence doctor receipt"),
            ],
            "Requires real private mapping, approval event and bridge health evidence outside the public repo.",
        ),
        task(
            9,
            "real-runtime-update-preflight",
            "Block real Hermes runtime updates unless every required proof passes.",
            status_from_result(update_result, "PASS_PRIVATE_PROOF_REDACTED"),
            f"Hermes production update preflight currently reports {update_result}.",
            [
                evidence("script", "scripts/factory_production_gate_receipts.py", "update preflight materializer"),
                evidence("schema", "schemas/hermes-production-update-preflight.schema.json", "runtime update preflight contract"),
                evidence("validation_artifact", repo_ref(paths.update_preflight), "current update preflight receipt"),
            ],
            "PASS still requires a separate explicit operator gate before any real update.",
        ),
    ]

    blocked = any(item["status"] == "BLOCKED" for item in tasks)
    attention = any(item["status"] == "ATTENTION" for item in tasks)
    result = "BLOCKED" if blocked else "ATTENTION" if attention else "PASS"
    readiness_level = (
        "BLOCKED"
        if result == "BLOCKED"
        else "ATTENTION_PUBLIC_CONTRACT_READY_PRIVATE_REVIEW_NEEDED"
        if result == "ATTENTION"
        else "PASS_PREPILOT_READY_WITH_REDACTED_PRIVATE_PROOF"
    )
    return {
        "$schema": "https://overkill-factory.dev/schemas/prepilot-master-task-readiness.schema.json",
        "record_type": "prepilot_master_task_readiness",
        "created_at": created_at or utc_now(),
        "result": result,
        "readiness_level": readiness_level,
        "source_plan": "docs/operations/validation-and-release.md",
        "coverage_rule": "All nine prepilot readiness tasks must be PASS or explicitly blocked before production readiness can be claimed.",
        "tasks": tasks,
        "limits": [
            "This receipt is public-safe and does not embed raw private runtime, Discord, board, gateway or credential values.",
            "PASS means prepilot readiness evidence is present; it is not customer production approval.",
            "Any BLOCKED task must remain blocked until its underlying proof receipt changes.",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def materialize(
    paths: GatePaths,
    *,
    no_write: bool = False,
    runtime_status_evidence: Path | None = None,
) -> dict[str, Any]:
    runtime_evidence = load_json(runtime_status_evidence) if runtime_status_evidence else None
    runtime = build_runtime_status(live_evidence=runtime_evidence)
    if not no_write:
        write_json(paths.runtime_status, runtime)

    update = build_update_preflight(paths)
    if not no_write:
        write_json(paths.update_preflight, update)

    prepilot = build_prepilot_master(paths)
    if not no_write:
        write_json(paths.prepilot_master, prepilot)

    return {
        "record_type": "factory_production_gate_receipt_materialization",
        "result": "PASS",
        "receipts": [
            {"id": "hermes_vfinal_runtime_status_check", "result": runtime["result"], "out": repo_ref(paths.runtime_status)},
            {"id": "hermes_production_update_preflight", "result": update["result"], "out": repo_ref(paths.update_preflight)},
            {"id": "prepilot_master_task_readiness", "result": prepilot["result"], "out": repo_ref(paths.prepilot_master)},
        ],
        "limits": [
            "Materialization PASS means receipts were built successfully, not that production gates passed.",
            "Use scripts/factory_production_readiness.py for the aggregate gate verdict.",
        ],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--runtime-status-evidence", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = materialize(
        GatePaths(),
        no_write=args.no_write,
        runtime_status_evidence=args.runtime_status_evidence,
    )
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
