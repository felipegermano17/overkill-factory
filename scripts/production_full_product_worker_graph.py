#!/usr/bin/env python3
"""Build the production-scoped worker graph for the public validation product."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "validation" / "production" / "full-product-worker-graph.json"
DEFAULT_MD_OUT = ROOT / "validation" / "production" / "full-product-worker-graph.md"
PRODUCT_SOURCE = ROOT / "products" / "qvg-public-validation-product"


LANES: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "hermes_orchestration",
        "worker_id": "factory-orchestrator",
        "path": "validation/hermes-live/multi-profile-dispatch-summary.md",
        "kind": "file",
        "reusable_policy": "supporting",
    },
    {
        "lane_id": "product_face",
        "worker_id": "product-face",
        "path": "validation/production/product-face/product-face-result.json",
        "record_type": "product_face_result",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "security",
        "worker_id": "codex-security",
        "path": "validation/security/codex-security-full-scan-2026-06-06.md",
        "kind": "file",
        "reusable_policy": "supporting",
    },
    {
        "lane_id": "quasar_auditor",
        "worker_id": "solana-quasar-auditor",
        "path": "validation/production/quasar/auditor-result.json",
        "record_type": "auditor_result",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "cu_svm_economic",
        "worker_id": "solana-quasar-auditor",
        "path": "validation/production/quasar/cu-svm-economic-proof.json",
        "record_type": "cu_svm_economic_proof",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "remote_proof",
        "worker_id": "remote-proof-runner",
        "path": "validation/production/remote-proof/managed-testbox-result.json",
        "record_type": "remote_proof_result",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "human_gate",
        "worker_id": "human-gate-clerk",
        "path": "validation/production/release/human-gate-record.json",
        "record_type": "human_gate_record",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "release_ops",
        "worker_id": "release-ops-worker",
        "path": "validation/production/release/release-ops-result.json",
        "record_type": "release_ops_result",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "supply_chain",
        "worker_id": "supply-chain-gate",
        "path": "validation/supply-chain/supply-chain-proof.json",
        "record_type": "supply_chain_result",
        "reusable_policy": "supporting",
    },
)


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


def load_json(rel_path: str) -> dict[str, Any]:
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def product_target() -> dict[str, str]:
    return {
        "product_id": "qvg-public-validation-product",
        "source_ref": "products/qvg-public-validation-product",
        "source_sha256": source_sha256(),
        "approval_scope": "Full reusable worker graph for the public Quasar Vault Guard validation product.",
        "environment_class": "public-production-validation-graph",
    }


def validate_lane(lane: dict[str, Any]) -> dict[str, Any]:
    rel_path = str(lane["path"])
    path = ROOT / rel_path
    errors: list[str] = []
    data: dict[str, Any] = {}
    if not path.exists():
        errors.append("evidence file is missing")
    elif lane.get("kind") != "file":
        data = load_json(rel_path)
        if data.get("result") != "PASS":
            errors.append("result must be PASS")
        if data.get("evidence_kind") != "real":
            errors.append("evidence_kind must be real")
        if lane.get("record_type") and data.get("record_type") != lane["record_type"]:
            errors.append(f"record_type must be {lane['record_type']}")
        if lane.get("reusable_policy") == "strict" and data.get("reusable_for_product") is not True:
            errors.append("strict lane must be reusable_for_product=true")
        target = data.get("product_target")
        if lane.get("reusable_policy") == "strict":
            if not isinstance(target, dict):
                errors.append("strict lane product_target is missing")
            elif target.get("product_id") != "qvg-public-validation-product":
                errors.append("strict lane product_id does not match")

    return {
        "lane_id": lane["lane_id"],
        "worker_id": lane.get("worker_id"),
        "record_type": lane.get("record_type"),
        "evidence_ref": rel_path,
        "reusable_policy": lane.get("reusable_policy"),
        "result": data.get("result") if data else ("PASS" if path.exists() else "FAIL"),
        "reusable_for_product": bool(data.get("reusable_for_product")) if data else lane.get("reusable_policy") == "supporting",
        "status": "PASS" if not errors else "FAIL",
        "validation_errors": errors,
    }


def build_graph() -> dict[str, Any]:
    lanes = [validate_lane(lane) for lane in LANES]
    blocking = [
        f"{lane['lane_id']}: " + "; ".join(lane["validation_errors"])
        for lane in lanes
        if lane["validation_errors"]
    ]
    passed = not blocking
    return {
        "$schema": "https://overkill-factory.dev/schemas/full-product-worker-graph.schema.json",
        "record_type": "full_product_worker_graph",
        "created_at": utc_now(),
        "graph_kind": "production_public_validation_product_graph",
        "product_id": "qvg-public-validation-product",
        "product_name": "Quasar Vault Guard public validation product",
        "product_target": product_target(),
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "evidence_kind": "real",
        "reusable_for_product": passed,
        "completion_claim_allowed": passed,
        "lanes_total": len(lanes),
        "lanes_passed": sum(1 for lane in lanes if lane["status"] == "PASS"),
        "lanes": lanes,
        "blocking_summary": blocking,
        "evidence_refs": [str(lane["path"]) for lane in LANES],
        "policy_decision": (
            "The public validation product has a reconciled production-scoped worker graph."
            if passed
            else "Do not claim full product graph completion until every strict lane has reusable product evidence."
        ),
        "next_action": "Repeat this graph when any evidence lane or product source changes.",
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, graph: dict[str, Any]) -> None:
    lines = [
        "# Production Full Product Worker Graph",
        "",
        f"Result: `{graph['result']}`",
        f"Reusable for product: `{str(graph['reusable_for_product']).lower()}`",
        "",
        "## Lanes",
        "",
    ]
    for lane in graph["lanes"]:
        lines.append(f"- `{lane['lane_id']}`: `{lane['status']}` via `{lane['evidence_ref']}`")
    if graph["blocking_summary"]:
        lines.extend(["", "## Blocking", ""])
        for item in graph["blocking_summary"]:
            lines.append(f"- {item}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


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
