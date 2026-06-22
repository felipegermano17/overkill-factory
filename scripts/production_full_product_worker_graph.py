#!/usr/bin/env python3
"""Build a production-scoped full-product worker graph from a product contract."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "production" / "full-product-worker-graph.json"
DEFAULT_MD_OUT = ROOT / ".tmp" / "factory-runs" / "production" / "full-product-worker-graph.md"
DEFAULT_GRAPH_CONTRACT = ROOT / "templates" / "production-full-product-graph-qvg.contract.json"
DEFAULT_PRODUCT_ID = "qvg-public-validation-product"
DEFAULT_PRODUCT_SOURCE_REF = "fixtures/product-validation/qvg-public-validation-product"
DEFAULT_RELEASE_GATE_UPSTREAM_EXCLUDED_LANES = {"human_gate", "release_ops"}


LANES: tuple[dict[str, Any], ...] = (
    {
        "lane_id": "hermes_orchestration",
        "worker_id": "factory-orchestrator",
        "path": ".tmp/factory-runs/hermes-live/multi-profile-dispatch-summary.md",
        "kind": "file",
        "scope": "supporting",
        "reusable_policy": "supporting",
    },
    {
        "lane_id": "product_face",
        "worker_id": "product-face",
        "path": ".tmp/factory-runs/production/product-face/product-face-result.json",
        "record_type": "product_face_result",
        "scope": "product",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "security",
        "worker_id": "codex-security",
        "path": ".tmp/factory-runs/security/codex-security-full-scan-2026-06-06.md",
        "kind": "file",
        "scope": "supporting",
        "reusable_policy": "supporting",
    },
    {
        "lane_id": "quasar_auditor",
        "worker_id": "solana-quasar-auditor",
        "path": ".tmp/factory-runs/production/quasar/auditor-result.json",
        "record_type": "auditor_result",
        "scope": "product",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "cu_svm_economic",
        "worker_id": "solana-quasar-auditor",
        "path": ".tmp/factory-runs/production/quasar/cu-svm-economic-proof.json",
        "record_type": "cu_svm_economic_proof",
        "proof_kind": "production_quasar_cu_svm_economic",
        "scope": "product",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "remote_proof",
        "worker_id": "remote-proof-runner",
        "path": ".tmp/factory-runs/production/remote-proof/managed-testbox-result.json",
        "record_type": "remote_proof_result",
        "scope": "supporting",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "human_gate",
        "worker_id": "human-gate-clerk",
        "path": ".tmp/factory-runs/production/release/human-gate-record.json",
        "record_type": "human_gate_record",
        "scope": "supporting",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "release_ops",
        "worker_id": "release-ops-worker",
        "path": ".tmp/factory-runs/production/release/release-ops-result.json",
        "record_type": "release_ops_result",
        "scope": "supporting",
        "reusable_policy": "strict",
    },
    {
        "lane_id": "supply_chain",
        "worker_id": "supply-chain-gate",
        "path": ".tmp/factory-runs/supply-chain/supply-chain-proof.json",
        "record_type": "supply_chain_result",
        "scope": "supporting",
        "reusable_policy": "supporting",
    },
)


def default_contract() -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/production-full-product-graph-contract.schema.json",
        "record_type": "production_full_product_graph_contract",
        "product_id": DEFAULT_PRODUCT_ID,
        "product_name": "QVG product-shaped validation fixture",
        "source_ref": DEFAULT_PRODUCT_SOURCE_REF,
        "product_sot_ref": "fixtures/product-validation/qvg-public-validation-product/README.md",
        "selected_capability_pack_refs": [
            "capability-packs/product-face.json",
            "capability-packs/solana-quasar.json",
            "capability-packs/production-release.json",
        ],
        "product_delivery_quality_profile_ref": "quality-profiles/production-public-validation.json",
        "risk_class": "R4",
        "promotion_ladder_ref": "promotion-ladders/public-repository-production.json",
        "approval_scope": "Full reusable worker graph for the QVG product-shaped validation fixture.",
        "environment_class": "public-production-validation-graph",
        "graph_kind": "production_full_product_worker_graph",
        "release_gate_upstream_excluded_lanes": sorted(DEFAULT_RELEASE_GATE_UPSTREAM_EXCLUDED_LANES),
        "lanes": [dict(lane) for lane in LANES],
    }


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def source_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_dir():
        return None
    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def repo_ref(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def load_json(rel_path: str) -> dict[str, Any]:
    return json.loads((ROOT / rel_path).read_text(encoding="utf-8"))


def load_graph_contract(path: Path | None = None) -> dict[str, Any]:
    if path is None:
        path = DEFAULT_GRAPH_CONTRACT
    if path.exists():
        contract = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(contract, dict):
            raise ValueError("production graph contract must be a JSON object")
        return contract
    if path.resolve() != DEFAULT_GRAPH_CONTRACT.resolve():
        raise FileNotFoundError(f"production graph contract not found: {repo_ref(path)}")
    return default_contract()


def validate_graph_contract(contract: dict[str, Any]) -> None:
    if contract.get("record_type") != "production_full_product_graph_contract":
        raise ValueError("production graph contract record_type must be production_full_product_graph_contract")
    required = (
        "product_id",
        "product_name",
        "source_ref",
        "product_sot_ref",
        "selected_capability_pack_refs",
        "product_delivery_quality_profile_ref",
        "risk_class",
        "promotion_ladder_ref",
        "approval_scope",
        "environment_class",
        "lanes",
    )
    for field in required:
        if contract.get(field) in (None, "", [], {}):
            raise ValueError(f"production graph contract requires {field}")
    if not isinstance(contract.get("lanes"), list) or not contract["lanes"]:
        raise ValueError("production graph contract requires at least one lane")


def contract_source_sha256(contract: dict[str, Any]) -> str | None:
    source_ref = str(contract.get("source_ref") or "").strip()
    if not source_ref or source_ref.startswith(("external:", "http://", "https://")):
        return None
    return source_sha256(ROOT / source_ref)


def product_target(contract: dict[str, Any]) -> dict[str, Any]:
    target: dict[str, Any] = {
        "product_id": str(contract["product_id"]),
        "source_ref": str(contract["source_ref"]),
        "approval_scope": str(contract["approval_scope"]),
        "environment_class": str(contract["environment_class"]),
    }
    source_hash = contract_source_sha256(contract)
    if source_hash:
        target["source_sha256"] = source_hash
    return target


def graph_lanes(contract: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    return tuple(dict(lane) for lane in contract.get("lanes", []))


def release_gate_excluded_lanes(contract: dict[str, Any]) -> set[str]:
    values = contract.get("release_gate_upstream_excluded_lanes", sorted(DEFAULT_RELEASE_GATE_UPSTREAM_EXCLUDED_LANES))
    if not isinstance(values, list):
        return set(DEFAULT_RELEASE_GATE_UPSTREAM_EXCLUDED_LANES)
    return {str(value) for value in values if str(value).strip()}


def contract_ref(path: Path | None) -> str:
    if path is None:
        return repo_ref(DEFAULT_GRAPH_CONTRACT) if DEFAULT_GRAPH_CONTRACT.exists() else "builtin:qvg-production-graph-contract"
    return repo_ref(path)


def legacy_product_target() -> dict[str, Any]:
    return {
        "product_id": DEFAULT_PRODUCT_ID,
        "source_ref": DEFAULT_PRODUCT_SOURCE_REF,
        "source_sha256": source_sha256(ROOT / DEFAULT_PRODUCT_SOURCE_REF),
        "approval_scope": "Full reusable worker graph for the QVG product-shaped validation fixture.",
        "environment_class": "public-production-validation-graph",
    }


def validate_lane(lane: dict[str, Any], contract: dict[str, Any] | None = None) -> dict[str, Any]:
    contract = contract or default_contract()
    expected_product_id = str(contract["product_id"])
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
        if lane.get("record_type") == "product_face_result" and lane.get("reusable_policy") == "strict":
            for field in (
                "packet_comparison",
                "source_promise_coverage",
                "design_fit_review",
                "project_design_system_comparison",
                "professional_design_process_comparison",
                "reference_quality_comparison",
            ):
                value = data.get(field)
                if not isinstance(value, dict) or value.get("status") != "pass":
                    errors.append(f"strict Product Face lane requires {field}.status=pass")
            if not str(data.get("packet_ref") or "").strip():
                errors.append("strict Product Face lane requires packet_ref")
            if not str(data.get("project_design_system_ref") or "").strip():
                errors.append("strict Product Face lane requires project_design_system_ref")
            if not str(data.get("professional_design_process_ref") or "").strip():
                errors.append("strict Product Face lane requires professional_design_process_ref")
        target = data.get("product_target")
        if lane.get("reusable_policy") == "strict":
            if not isinstance(target, dict):
                errors.append("strict lane product_target is missing")
            elif target.get("product_id") != expected_product_id:
                errors.append("strict lane product_id does not match")
    provenance: dict[str, Any] = {
        "ref": rel_path,
        "exists": path.exists(),
        "loaded_at": utc_now(),
        "record_type": data.get("record_type") or lane.get("record_type") or lane.get("kind", "file"),
        "$schema": data.get("$schema"),
        "product_id": (data.get("product_target") or {}).get("product_id") if isinstance(data.get("product_target"), dict) else None,
    }
    if path.exists():
        provenance["size_bytes"] = path.stat().st_size
        provenance["sha256"] = file_sha256(path)

    return {
        "lane_id": lane["lane_id"],
        "scope": lane["scope"],
        "worker_id": lane.get("worker_id"),
        "record_type": lane.get("record_type"),
        "proof_kind": lane.get("proof_kind"),
        "receipt_type": None,
        "evidence_ref": rel_path,
        "card_id": str(data.get("card_ref", {}).get("card_id") or lane["lane_id"]) if data else lane["lane_id"],
        "result": data.get("result") if data else ("PASS" if path.exists() else "FAIL"),
        "evidence_kind": data.get("evidence_kind") if data else "real",
        "reusable_for_product": bool(data.get("reusable_for_product")) if data else lane.get("reusable_policy") == "supporting",
        "evidence_ref_count": len(data.get("evidence_refs") or []) if data else 1 if path.exists() else 0,
        "stale_evidence_refs": [],
        "evidence_provenance": provenance,
        "status": "PASS" if not errors else "FAIL",
        "validation_errors": errors,
    }


def filter_lanes_for_mode(
    lanes: tuple[dict[str, Any], ...],
    graph_mode: str,
    excluded_lanes: set[str] | None = None,
) -> tuple[tuple[dict[str, Any], ...], list[str]]:
    if graph_mode != "release_gate_upstream":
        return lanes, []
    excluded_lanes = excluded_lanes or DEFAULT_RELEASE_GATE_UPSTREAM_EXCLUDED_LANES
    selected = tuple(lane for lane in lanes if lane["lane_id"] not in excluded_lanes)
    omitted = [lane["lane_id"] for lane in lanes if lane["lane_id"] in excluded_lanes]
    return selected, omitted


def build_graph(
    lanes: tuple[dict[str, Any], ...] | None = None,
    *,
    contract: dict[str, Any] | None = None,
    graph_mode: str = "full_product",
    contract_path: Path | None = None,
) -> dict[str, Any]:
    contract = contract or default_contract()
    validate_graph_contract(contract)
    lanes = lanes or graph_lanes(contract)
    selected_lanes, omitted_lanes = filter_lanes_for_mode(lanes, graph_mode, release_gate_excluded_lanes(contract))
    lane_results = [validate_lane(lane, contract) for lane in selected_lanes]
    blocking = [
        f"{lane['lane_id']}: " + "; ".join(lane["validation_errors"])
        for lane in lane_results
        if lane["validation_errors"]
    ]
    passed = not blocking
    return {
        "$schema": "https://overkill-factory.dev/schemas/full-product-worker-graph.schema.json",
        "record_type": "full_product_worker_graph",
        "created_at": utc_now(),
        "graph_kind": str(contract.get("graph_kind") or "production_full_product_worker_graph"),
        "graph_mode": graph_mode,
        "contract_ref": contract_ref(contract_path),
        "product_id": str(contract["product_id"]),
        "product_name": str(contract["product_name"]),
        "product_target": product_target(contract),
        "product_sot_ref": str(contract["product_sot_ref"]),
        "selected_capability_pack_refs": [str(ref) for ref in contract["selected_capability_pack_refs"]],
        "product_delivery_quality_profile_ref": str(contract["product_delivery_quality_profile_ref"]),
        "risk_class": str(contract["risk_class"]),
        "promotion_ladder_ref": str(contract["promotion_ladder_ref"]),
        "environment_class": str(contract["environment_class"]),
        "approval_scope": str(contract["approval_scope"]),
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "evidence_kind": "real",
        "reusable_for_product": passed,
        "completion_claim_allowed": passed and not omitted_lanes,
        "omitted_lanes": omitted_lanes,
        "lanes_total": len(lane_results),
        "lanes_passed": sum(1 for lane in lane_results if lane["status"] == "PASS"),
        "product_lanes_total": sum(1 for lane in lane_results if lane["scope"] == "product"),
        "supporting_lanes_total": sum(1 for lane in lane_results if lane["scope"] == "supporting"),
        "reusable_for_product_lanes": sum(1 for lane in lane_results if lane["reusable_for_product"]),
        "lanes": lane_results,
        "blocking_summary": blocking,
        "production_blockers": blocking or ["none"],
        "evidence_refs": [str(lane["path"]) for lane in selected_lanes],
        "policy_decision": (
            f"{contract['product_id']} has a reconciled production-scoped worker graph."
            if passed and not omitted_lanes
            else "The release gate upstream graph is reusable for release validation; run the full graph after release-ops evidence is written."
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
    parser.add_argument("--release-gate-upstream", action="store_true")
    parser.add_argument("--graph-contract", type=Path, default=DEFAULT_GRAPH_CONTRACT)
    args = parser.parse_args(argv)

    graph_mode = "release_gate_upstream" if args.release_gate_upstream else "full_product"
    contract = load_graph_contract(args.graph_contract)
    graph = build_graph(contract=contract, graph_mode=graph_mode, contract_path=args.graph_contract)
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
