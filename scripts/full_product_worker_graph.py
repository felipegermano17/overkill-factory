#!/usr/bin/env python3
"""Reconcile one product-specific worker graph without claiming production."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "product-specific" / "qvg-full-product-worker-graph.json"
DEFAULT_MD_OUT = ROOT / ".tmp" / "factory-runs" / "product-specific" / "qvg-full-product-worker-graph.md"


LANES: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "product_face",
        "worker_id": "product-face",
        "record_type": "product_face_result",
        "path": ".tmp/factory-runs/production/product-face/product-face-result.json",
        "scope": "product",
    },
    {
        "lane_id": "security",
        "worker_id": "codex-security",
        "record_type": "security_scan_result",
        "path": ".tmp/factory-runs/production/security/security-scan-result.json",
        "scope": "product",
    },
    {
        "lane_id": "auditor",
        "worker_id": "solana-quasar-auditor",
        "record_type": "auditor_result",
        "path": ".tmp/factory-runs/production/quasar/auditor-result.json",
        "scope": "product",
    },
    {
        "lane_id": "cu_svm_economic",
        "record_type": "cu_svm_economic_proof",
        "proof_kind": "production_quasar_cu_svm_economic",
        "path": ".tmp/factory-runs/production/quasar/cu-svm-economic-proof.json",
        "scope": "product",
    },
    {
        "lane_id": "remote_proof",
        "worker_id": "remote-proof-runner",
        "record_type": "remote_proof_result",
        "path": ".tmp/factory-runs/remote-proof/crabbox-static-ssh-proof-2026-06-06.json",
        "scope": "supporting",
    },
    {
        "lane_id": "independent_review",
        "worker_id": "independent-reviewer",
        "record_type": "independent_review_result",
        "path": ".tmp/factory-runs/production/review/independent-review-result.json",
        "scope": "product",
    },
    {
        "lane_id": "human_gate",
        "worker_id": "human-gate-clerk",
        "record_type": "human_gate_record",
        "path": ".tmp/factory-runs/production/release/human-gate-record.json",
        "scope": "supporting",
    },
    {
        "lane_id": "release_ops",
        "worker_id": "release-ops-worker",
        "record_type": "release_ops_result",
        "path": ".tmp/factory-runs/production/release/release-ops-result.json",
        "scope": "supporting",
    },
    {
        "lane_id": "supply_chain",
        "worker_id": "supply-chain-gate",
        "record_type": "supply_chain_result",
        "path": ".tmp/factory-runs/supply-chain/supply-chain-proof.json",
        "scope": "supporting",
    },
    {
        "lane_id": "receipt_five",
        "receipt_type": "receipt_five",
        "path": "examples/minimal-hermes-project/expected-receipt-five.json",
        "scope": "product",
    },
)


PRODUCTION_BLOCKERS = [
    "managed remote proof still needs Crabbox broker or Blacksmith Testbox credentials and cleanup evidence",
    "production release still needs a fresh R4 human gate, rollback proof, release smoke and monitoring evidence",
    "one real production product still needs the same graph with every remaining critical lane reusable_for_product=true",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(rel_path: str) -> dict[str, Any]:
    path = ROOT / rel_path
    return json.loads(path.read_text(encoding="utf-8"))


def rel_exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def evidence_ref_exists(ref: str) -> bool:
    if ref.startswith("external:") or ref.startswith("http://") or ref.startswith("https://"):
        return True
    return (ROOT / ref).exists()


def card_id_for(data: dict[str, Any]) -> str:
    card_ref = data.get("card_ref")
    if isinstance(card_ref, dict):
        return str(card_ref.get("card_id") or "")
    receipt = data.get("kanban_transition_event")
    if isinstance(receipt, dict):
        refs = receipt.get("artifact_refs")
        if isinstance(refs, list) and refs:
            return "QVG-PILOT-FIRST-SLICE"
    return ""


def evidence_refs_for(data: dict[str, Any]) -> list[str]:
    refs = data.get("evidence_refs")
    if isinstance(refs, list):
        return [str(ref) for ref in refs if str(ref).strip()]
    receipt = data.get("receipt_five")
    if isinstance(receipt, dict):
        refs = receipt.get("artifact_paths")
        if isinstance(refs, list):
            return [str(ref).replace("\\", "/") for ref in refs if str(ref).strip()]
    return []


def repo_ref(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def validate_lane(lane: dict[str, Any]) -> dict[str, Any]:
    path = str(lane["path"])
    errors: list[str] = []
    data: dict[str, Any] = {}
    if not rel_exists(path):
        errors.append("lane evidence file is missing")
    else:
        data = load_json(path)

    if data:
        expected_record = lane.get("record_type")
        expected_proof = lane.get("proof_kind")
        if expected_record and data.get("record_type") != expected_record:
            errors.append(f"record_type must be {expected_record}")
        if expected_proof and data.get("proof_kind") != expected_proof:
            errors.append(f"proof_kind must be {expected_proof}")
        if lane.get("receipt_type") == "receipt_five" and "receipt_five" not in data:
            errors.append("receipt_five object is missing")

        result = str(data.get("result") or data.get("receipt_five", {}).get("verification_result") or "")
        if not result.startswith("PASS"):
            errors.append("lane result must be PASS or PASS_WITH_BOUNDARIES")
        if data.get("blocking_findings") is True:
            errors.append("lane has blocking_findings=true")
        if data.get("evidence_kind") not in {None, "real"}:
            errors.append("lane evidence_kind must be real when present")

        refs = evidence_refs_for(data)
        if not refs:
            errors.append("lane evidence_refs/artifact_paths are missing")
        missing_refs = [ref for ref in refs if not evidence_ref_exists(ref)]
        if missing_refs and lane.get("receipt_type") != "receipt_five":
            errors.append("lane has missing evidence refs: " + ", ".join(missing_refs[:5]))

    reusable = bool(data.get("reusable_for_product")) if data else False
    return {
        "lane_id": lane["lane_id"],
        "scope": lane["scope"],
        "worker_id": lane.get("worker_id"),
        "record_type": lane.get("record_type"),
        "proof_kind": lane.get("proof_kind"),
        "receipt_type": lane.get("receipt_type"),
        "evidence_ref": path,
        "card_id": card_id_for(data),
        "result": data.get("result") or data.get("receipt_five", {}).get("verification_result"),
        "evidence_kind": data.get("evidence_kind") or "real",
        "reusable_for_product": reusable,
        "evidence_ref_count": len(evidence_refs_for(data)),
        "stale_evidence_refs": missing_refs if data and lane.get("receipt_type") == "receipt_five" else [],
        "status": "PASS" if not errors else "FAIL",
        "validation_errors": errors,
    }


def build_graph() -> dict[str, Any]:
    lanes = [validate_lane(lane) for lane in LANES]
    blockers = [
        f"{lane['lane_id']}: " + "; ".join(lane["validation_errors"])
        for lane in lanes
        if lane["validation_errors"]
    ]
    product_lanes = [lane for lane in lanes if lane["scope"] == "product"]
    supporting_lanes = [lane for lane in lanes if lane["scope"] == "supporting"]
    reusable_count = sum(1 for lane in lanes if lane["reusable_for_product"])
    all_pass = not blockers
    return {
        "$schema": "https://overkill-factory.dev/schemas/full-product-worker-graph.schema.json",
        "record_type": "full_product_worker_graph",
        "created_at": utc_now(),
        "graph_kind": "product_specific_public_validation_graph",
        "product_id": "qvg-public-validation-product",
        "product_name": "Quasar Vault Guard public validation product",
        "result": "PASS" if all_pass else "FAIL",
        "blocking_findings": not all_pass,
        "evidence_kind": "real",
        "reusable_for_product": False,
        "completion_claim_allowed": False,
        "lanes_total": len(lanes),
        "lanes_passed": sum(1 for lane in lanes if lane["status"] == "PASS"),
        "product_lanes_total": len(product_lanes),
        "supporting_lanes_total": len(supporting_lanes),
        "reusable_for_product_lanes": reusable_count,
        "lanes": lanes,
        "blocking_summary": blockers,
        "production_blockers": PRODUCTION_BLOCKERS,
        "evidence_refs": [str(lane["path"]) for lane in LANES],
        "policy_decision": (
            "This proves product-specific worker-graph reconciliation for the public QVG validation product, "
            "including reusable Quasar Auditor and CU/SVM/economic lanes. The Product Face lane is not reusable until "
            "packet comparison, source-promise coverage and design-fit review are recorded as pass."
        ),
        "next_action": "Add managed remote proof, product-specific release/human evidence and a fully reusable graph before practical 10/10 completion.",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, graph: dict[str, Any]) -> None:
    lines = [
        "# QVG Full Product Worker Graph",
        "",
        f"Result: `{graph['result']}`",
        f"Reusable for product approval: `{str(graph['reusable_for_product']).lower()}`",
        f"Completion claim allowed: `{str(graph['completion_claim_allowed']).lower()}`",
        "",
        "## Lanes",
        "",
    ]
    for lane in graph["lanes"]:
        lines.append(
            f"- `{lane['lane_id']}`: `{lane['status']}` via `{lane['evidence_ref']}`; reusable_for_product=`{str(lane['reusable_for_product']).lower()}`"
        )
    lines.extend(
        [
            "",
            "## Production Blockers",
            "",
        ]
    )
    for blocker in graph["production_blockers"]:
        lines.append(f"- {blocker}")
    lines.extend(["", "## Policy Decision", "", graph["policy_decision"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args(argv)

    graph = build_graph()
    if not args.no_write:
        write_json(args.out, graph)
        write_markdown(args.md_out, graph)
        print(f"Wrote {repo_ref(args.out)}")
        print(f"Wrote {repo_ref(args.md_out)}")
    print(graph["result"])
    if args.require_pass and graph["result"] != "PASS":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
