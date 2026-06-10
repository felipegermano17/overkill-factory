#!/usr/bin/env python3
"""Block real Hermes updates until production-only proofs are present."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "validation" / "hermes-production-update-preflight" / "real-runtime-update-blocked.json"


@dataclass(frozen=True)
class ProofRequirement:
    key: str
    arg_name: str
    description: str


REQUIRED_PROOFS = [
    ProofRequirement(
        key="non_stub_worker_execution",
        arg_name="non_stub_worker_execution",
        description="One bounded materialized vFinal worker ran against a non-stub model endpoint.",
    ),
    ProofRequirement(
        key="real_tool_auth",
        arg_name="real_tool_auth",
        description="The worker used required real tools/auth and did not rely on local stubs.",
    ),
    ProofRequirement(
        key="specialist_output_quality",
        arg_name="specialist_output_quality",
        description="The worker produced useful specialist output with evidence, not just a successful process exit.",
    ),
    ProofRequirement(
        key="real_worker_done_reconciliation",
        arg_name="real_worker_done_reconciliation",
        description="Parent done reconciliation passed using the real worker result.",
    ),
    ProofRequirement(
        key="production_rollback_monitoring",
        arg_name="production_rollback_monitoring",
        description="The exact production service-manager rollback and monitoring path was proven.",
    ),
    ProofRequirement(
        key="operator_control_tower",
        arg_name="operator_control_tower",
        description="The operator-facing control tower is ready for status, approval and incident visibility.",
    ),
    ProofRequirement(
        key="complete_update_receipt",
        arg_name="complete_update_receipt",
        description="A complete Hermes update receipt exists for the exact target runtime update.",
    ),
]


def public_ref(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{resolved.name}"


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"invalid JSON: {exc}"
    if not isinstance(data, dict):
        return None, "JSON root must be an object"
    return data, None


def resolve_public_ref(ref: str) -> Path | None:
    if not ref or ref.startswith("external:"):
        return None
    candidate = (ROOT / ref).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return None
    return candidate


def proof_status(requirement: ProofRequirement, path: Path | None) -> tuple[str, str | None, str | None]:
    if path is None:
        return "BLOCKED", None, "missing proof ref"
    if not path.exists():
        return "BLOCKED", public_ref(path), "proof file does not exist"
    if path.suffix.lower() != ".json":
        return "BLOCKED", public_ref(path), "proof file must be JSON"

    data, error = load_json(path)
    if error:
        return "BLOCKED", public_ref(path), error
    record_type = data.get("record_type")
    if requirement.key == "complete_update_receipt" and record_type == "hermes_update_receipt":
        return update_receipt_status(data, path)
    return production_proof_status(requirement, data, path)


def production_proof_status(requirement: ProofRequirement, data: dict[str, Any], path: Path) -> tuple[str, str, str | None]:
    if data.get("record_type") != "hermes_production_proof":
        return "BLOCKED", public_ref(path), "record_type must be 'hermes_production_proof'"
    if data.get("proof_type") != requirement.key:
        return "BLOCKED", public_ref(path), f"proof_type must be {requirement.key!r}"
    result = data.get("result")
    if result != "PASS":
        return "BLOCKED", public_ref(path), f"JSON result is {result!r}, expected 'PASS'"
    evidence_refs = data.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        return "BLOCKED", public_ref(path), "evidence_refs must be a non-empty list"
    if not all(isinstance(ref, str) and ref for ref in evidence_refs):
        return "BLOCKED", public_ref(path), "evidence_refs must contain non-empty strings"
    if requirement.key == "operator_control_tower":
        readiness_reason = operator_control_tower_readiness_reason(evidence_refs)
        if readiness_reason:
            return "BLOCKED", public_ref(path), readiness_reason
    limits = data.get("limits")
    if not isinstance(limits, list) or not limits:
        return "BLOCKED", public_ref(path), "limits must be a non-empty list"
    decision = data.get("decision")
    if isinstance(decision, dict):
        real_runtime_update = str(decision.get("real_runtime_update") or "")
        if real_runtime_update.startswith("blocked"):
            return "BLOCKED", public_ref(path), "real_runtime_update decision is blocked"
    return "PASS", public_ref(path), None


def operator_control_tower_readiness_reason(evidence_refs: list[Any]) -> str | None:
    readiness_refs = [
        ref
        for ref in evidence_refs
        if isinstance(ref, str) and ref.endswith("operator-control-tower-production-readiness.json")
    ]
    if not readiness_refs:
        return "operator Control Tower proof must reference production readiness receipt"
    for ref in readiness_refs:
        path = resolve_public_ref(ref)
        if path is None:
            continue
        if not path.exists():
            return f"operator Control Tower readiness receipt missing: {ref}"
        data, error = load_json(path)
        if error:
            return f"operator Control Tower readiness receipt invalid: {error}"
        if data.get("record_type") != "operator_control_tower_production_readiness":
            return "operator Control Tower readiness receipt has wrong record_type"
        if data.get("result") != "PASS":
            return f"operator Control Tower readiness receipt is {data.get('result')!r}, expected 'PASS'"
        blocking_items = data.get("blocking_items")
        if blocking_items:
            return "operator Control Tower readiness receipt still has blocking_items"
        return None
    return "operator Control Tower readiness receipt must be a public repo ref"


def update_receipt_status(data: dict[str, Any], path: Path) -> tuple[str, str, str | None]:
    decision = data.get("decision")
    if not isinstance(decision, dict):
        return "BLOCKED", public_ref(path), "decision must be an object"
    real_runtime_update = str(decision.get("real_runtime_update") or "")
    if not real_runtime_update or real_runtime_update.startswith("blocked"):
        return "BLOCKED", public_ref(path), "real_runtime_update decision is blocked"
    checks = data.get("checks")
    if not isinstance(checks, dict):
        return "BLOCKED", public_ref(path), "checks must be an object"
    pending = [key for key, value in checks.items() if value in {"PENDING", "BLOCKED", "FAIL", None}]
    if pending:
        return "BLOCKED", public_ref(path), f"checks still not passing: {', '.join(sorted(pending))}"
    evidence_refs = data.get("evidence_refs")
    if not isinstance(evidence_refs, list) or not evidence_refs:
        return "BLOCKED", public_ref(path), "evidence_refs must be a non-empty list"
    return "PASS", public_ref(path), None


def evaluate_preflight(
    proof_paths: dict[str, Path | None],
    required_proofs: list[ProofRequirement] = REQUIRED_PROOFS,
    created_at: str | None = None,
) -> dict[str, Any]:
    proof_checks: list[dict[str, Any]] = []
    evidence_refs: list[str] = []
    blocking_items: list[str] = []

    for requirement in required_proofs:
        status, ref, reason = proof_status(requirement, proof_paths.get(requirement.arg_name))
        if ref:
            evidence_refs.append(ref)
        if status == "BLOCKED":
            blocking_items.append(requirement.key)
        proof_checks.append(
            {
                "id": requirement.key,
                "status": status,
                "proof_ref": ref,
                "description": requirement.description,
                "reason": reason,
            }
        )

    result = "PASS" if not blocking_items else "BLOCKED"
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-production-update-preflight.schema.json",
        "record_type": "hermes_production_update_preflight",
        "created_at": created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "target": "real-hermes-runtime-update",
        "result": result,
        "required_proofs": proof_checks,
        "blocking_items": blocking_items,
        "decision": {
            "real_runtime_update": "allowed_for_explicit_operator_gate" if result == "PASS" else "blocked",
            "worker_task_status": "ready_requires_operator_gate" if result == "PASS" else "keep_blocked",
        },
        "evidence_refs": sorted(set(evidence_refs)),
        "limits": [
            "This preflight does not touch real Hermes.",
            "PASS means proof refs exist and are not self-declared blocked; it is still subject to explicit operator approval.",
            "BLOCKED means do not update the real Hermes runtime.",
        ],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    for requirement in REQUIRED_PROOFS:
        parser.add_argument(f"--{requirement.arg_name.replace('_', '-')}", dest=requirement.arg_name, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    proof_paths = {requirement.arg_name: getattr(args, requirement.arg_name) for requirement in REQUIRED_PROOFS}
    receipt = evaluate_preflight(proof_paths)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": public_ref(args.out), "blocking_items": receipt["blocking_items"]}))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
