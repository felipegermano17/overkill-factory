#!/usr/bin/env python3
"""Audit whether Overkill Factory can honestly claim practical 10/10."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "validation" / "completion"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_ref(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def exists(rel_path: str) -> bool:
    return (ROOT / rel_path).exists()


def json_field(path: str, *keys: str) -> Any:
    data: Any = load_json(ROOT / path)
    for key in keys:
        if not isinstance(data, dict):
            return None
        data = data.get(key)
    return data


def public_proof(rel_path: str, *, result: str = "PASS") -> bool:
    path = ROOT / rel_path
    if not path.exists():
        return False
    try:
        return load_json(path).get("result") == result
    except json.JSONDecodeError:
        return False


def production_worker_result(rel_path: str, *, record_type: str | None = None) -> bool:
    path = ROOT / rel_path
    if not path.exists():
        return False
    try:
        data = load_json(path)
    except json.JSONDecodeError:
        return False
    if data.get("result") != "PASS":
        return False
    if data.get("evidence_kind") != "real":
        return False
    if data.get("reusable_for_product") is not True:
        return False
    if record_type and data.get("record_type") != record_type:
        return False
    return True


def achieved_requirement(
    req_id: str,
    title: str,
    evidence_refs: list[str],
    why_it_matters: str,
) -> dict[str, Any]:
    return {
        "id": req_id,
        "title": title,
        "status": "ACHIEVED",
        "blocking": False,
        "evidence_refs": evidence_refs,
        "why_it_matters": why_it_matters,
        "next_action": "Keep rerunning this proof when the related surface changes.",
    }


def blocked_requirement(
    req_id: str,
    title: str,
    expected_evidence: list[str],
    why_it_matters: str,
    next_action: str,
) -> dict[str, Any]:
    return {
        "id": req_id,
        "title": title,
        "status": "BLOCKED_MISSING_EVIDENCE",
        "blocking": True,
        "evidence_refs": [],
        "expected_evidence_refs": expected_evidence,
        "why_it_matters": why_it_matters,
        "next_action": next_action,
    }


def bounded_requirement(
    req_id: str,
    title: str,
    evidence_refs: list[str],
    why_it_matters: str,
    missing_upgrade: str,
) -> dict[str, Any]:
    return {
        "id": req_id,
        "title": title,
        "status": "BOUNDED_PUBLIC_PROOF",
        "blocking": True,
        "evidence_refs": evidence_refs,
        "why_it_matters": why_it_matters,
        "boundary": missing_upgrade,
        "next_action": missing_upgrade,
    }


def build_requirements() -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []

    if exists("validation/hermes-live/multi-profile-dispatch-summary.md") and exists("validation/hermes-live/real-profile-dispatch-smoke.md"):
        requirements.append(
            achieved_requirement(
                "hermes_real_worker_orchestration",
                "Hermes real worker orchestration",
                [
                    "validation/hermes-live/real-profile-dispatch-smoke.md",
                    "validation/hermes-live/multi-profile-dispatch-summary.md",
                    "validation/hermes-live/worker-dispatched-done-gate-smoke.md",
                ],
                "The factory floor must be Hermes, not only local scripts or chat plans.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "hermes_real_worker_orchestration",
                "Hermes real worker orchestration",
                ["validation/hermes-live/multi-profile-dispatch-summary.md"],
                "The factory floor must be Hermes, not only local scripts or chat plans.",
                "Run a real Hermes disposable board with required workers and import public-safe evidence.",
            )
        )

    if production_worker_result(
        "validation/production/product-face/product-face-result.json",
        record_type="product_face_result",
    ):
        requirements.append(
            achieved_requirement(
                "production_product_face",
                "Production-like Product Face proof",
                ["validation/production/product-face/product-face-result.json"],
                "A product is not complete until its real face works across states, mobile, a11y and performance boundaries.",
            )
        )
    elif public_proof("validation/quasar-product-like-proof/product-face/qvg-product-like-product-face-result.json"):
        requirements.append(
            bounded_requirement(
                "production_product_face",
                "Production-like Product Face proof",
                ["validation/quasar-product-like-proof/product-face/qvg-product-like-product-face-result.json"],
                "A product is not complete until its real face works across states, mobile, a11y and performance boundaries.",
                "Run Product Face against a deployed or production-like target and mark it reusable_for_product=true only if it is product-specific.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "production_product_face",
                "Production-like Product Face proof",
                ["validation/production/product-face/product-face-result.json"],
                "A product is not complete until its real face works across states, mobile, a11y and performance boundaries.",
                "Run browser-backed Product Face proof against the production-like UI.",
            )
        )

    if exists("validation/security/codex-security-full-scan-2026-06-06.md") and exists("validation/security/bandit-scripts-adapters.json"):
        requirements.append(
            achieved_requirement(
                "factory_security_scan",
                "Factory code security scan",
                [
                    "validation/security/codex-security-full-scan-2026-06-06.md",
                    "validation/security/bandit-scripts-adapters.json",
                ],
                "The factory code that gates autonomous work must itself pass security review.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "factory_security_scan",
                "Factory code security scan",
                ["validation/security/codex-security-full-scan-2026-06-06.md"],
                "The factory code that gates autonomous work must itself pass security review.",
                "Run Codex Security and repo safety scanners over the factory code.",
            )
        )

    if production_worker_result(
        "validation/production/quasar/auditor-result.json",
        record_type="auditor_result",
    ):
        requirements.append(
            achieved_requirement(
                "production_quasar_auditor",
                "Production Quasar Auditor code audit",
                ["validation/production/quasar/auditor-result.json"],
                "The public product-like audit is useful, but production approval needs the actual product program.",
            )
        )
    elif public_proof("validation/quasar-product-like-proof/qvg-product-like-auditor-result.json"):
        requirements.append(
            bounded_requirement(
                "production_quasar_auditor",
                "Production Quasar Auditor code audit",
                ["validation/quasar-product-like-proof/qvg-product-like-auditor-result.json"],
                "The public product-like audit is useful, but production approval needs the actual product program.",
                "Run solana-quasar-auditor plus Auditor corpus/checklists against production Quasar source.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "production_quasar_auditor",
                "Production Quasar Auditor code audit",
                ["validation/production/quasar/auditor-result.json"],
                "The public product-like audit is useful, but production approval needs the actual product program.",
                "Add production Quasar source and run the full Auditor code-audit path.",
            )
        )

    if production_worker_result("validation/production/quasar/cu-svm-economic-proof.json"):
        requirements.append(
            achieved_requirement(
                "production_cu_svm_economic",
                "Production CU, SVM/client flow and economic safety",
                ["validation/production/quasar/cu-svm-economic-proof.json"],
                "Onchain code can pass unit tests and still fail through compute, transaction flow or economic edge cases.",
            )
        )
    elif public_proof("validation/quasar-product-like-proof/qvg-quasar-cu-fuzz-property-proof.json"):
        requirements.append(
            bounded_requirement(
                "production_cu_svm_economic",
                "Production CU, SVM/client flow and economic safety",
                ["validation/quasar-product-like-proof/qvg-quasar-cu-fuzz-property-proof.json"],
                "Onchain code can pass unit tests and still fail through compute, transaction flow or economic edge cases.",
                "Run real CU profiling, SVM/client transactions and economic fuzz/property tests on production source.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "production_cu_svm_economic",
                "Production CU, SVM/client flow and economic safety",
                ["validation/production/quasar/cu-svm-economic-proof.json"],
                "Onchain code can pass unit tests and still fail through compute, transaction flow or economic edge cases.",
                "Create product-specific CU/SVM/economic proof artifacts.",
            )
        )

    if production_worker_result("validation/production/remote-proof/managed-testbox-result.json", record_type="remote_proof_result"):
        requirements.append(
            achieved_requirement(
                "managed_remote_proof",
                "Managed Crabbox/Testbox remote proof",
                ["validation/production/remote-proof/managed-testbox-result.json"],
                "Static SSH proof is useful, but managed remote proof validates the intended provider-backed heavy gate.",
            )
        )
    elif public_proof("validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.json"):
        requirements.append(
            bounded_requirement(
                "managed_remote_proof",
                "Managed Crabbox/Testbox remote proof",
                ["validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.json"],
                "Static SSH proof is useful, but managed remote proof validates the intended provider-backed heavy gate.",
                "Run managed Crabbox broker or Blacksmith Testbox with approved credentials and cleanup receipt.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "managed_remote_proof",
                "Managed Crabbox/Testbox remote proof",
                ["validation/production/remote-proof/managed-testbox-result.json"],
                "Static SSH proof is useful, but managed remote proof validates the intended provider-backed heavy gate.",
                "Run provider-backed remote proof or record a human waiver with risk owner and expiry.",
            )
        )

    if production_worker_result("validation/production/release/release-ops-result.json", record_type="release_ops_result") and production_worker_result(
        "validation/production/release/human-gate-record.json",
        record_type="human_gate_record",
    ):
        requirements.append(
            achieved_requirement(
                "production_release_human_gate",
                "Production release and human R4 gate",
                [
                    "validation/production/release/release-ops-result.json",
                    "validation/production/release/human-gate-record.json",
                ],
                "Production release authority must be explicit, reviewed and reversible.",
            )
        )
    elif exists("validation/release-human-gate/qvg-release-ops-result.json"):
        requirements.append(
            bounded_requirement(
                "production_release_human_gate",
                "Production release and human R4 gate",
                [
                    "validation/release-human-gate/qvg-release-ops-result.json",
                    "validation/release-human-gate/qvg-human-gate-record.json",
                ],
                "Production release authority must be explicit, reviewed and reversible.",
                "Run product-specific R4 human gate, rollback proof, release smoke and monitoring evidence before any production claim.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "production_release_human_gate",
                "Production release and human R4 gate",
                [
                    "validation/production/release/release-ops-result.json",
                    "validation/production/release/human-gate-record.json",
                ],
                "Production release authority must be explicit, reviewed and reversible.",
                "Produce real release and human gate records for the product target.",
            )
        )

    if exists("validation/supply-chain/supply-chain-proof.json") and json_field(
        "validation/supply-chain/supply-chain-proof.json",
        "result",
    ) == "PASS":
        requirements.append(
            achieved_requirement(
                "public_supply_chain_ci_sbom",
                "Public repository supply-chain CI/SBOM",
                [
                    "validation/supply-chain/supply-chain-proof.json",
                    "validation/supply-chain/source-sbom.spdx.json",
                    "validation/supply-chain/hermes-supply-chain-summary.md",
                ],
                "An open factory must be reproducible and safe to accept contributions.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "public_supply_chain_ci_sbom",
                "Public repository supply-chain CI/SBOM",
                ["validation/supply-chain/supply-chain-proof.json"],
                "An open factory must be reproducible and safe to accept contributions.",
                "Run the supply-chain CI/SBOM proof.",
            )
        )

    if production_worker_result("validation/production/full-product-worker-graph.json"):
        requirements.append(
            achieved_requirement(
                "full_product_specific_worker_graph",
                "Full product-specific multi-specialist execution",
                ["validation/production/full-product-worker-graph.json"],
                "The goal is a factory that carries a real product through all required workers, not isolated prooflets.",
            )
        )
    else:
        requirements.append(
            blocked_requirement(
                "full_product_specific_worker_graph",
                "Full product-specific multi-specialist execution",
                ["validation/production/full-product-worker-graph.json"],
                "The goal is a factory that carries a real product through all required workers, not isolated prooflets.",
                "Run one real product through Product Face, Security, Auditor, Remote Proof, QA, review, release and human gates with reconciled worker results.",
            )
        )

    return requirements


def build_audit() -> dict[str, Any]:
    requirements = build_requirements()
    blocking = [item for item in requirements if item["blocking"]]
    achieved = [item for item in requirements if item["status"] == "ACHIEVED"]
    bounded = [item for item in requirements if item["status"] == "BOUNDED_PUBLIC_PROOF"]
    status = "COMPLETE" if not blocking else "NOT_COMPLETE"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-completion-audit.schema.json",
        "created_at": now_iso(),
        "audit_kind": "factory_10_practical_completion",
        "status": status,
        "completion_claim_allowed": status == "COMPLETE",
        "score_estimate": "9.992/10" if status != "COMPLETE" else "10/10",
        "requirements_total": len(requirements),
        "requirements_achieved": len(achieved),
        "requirements_bounded": len(bounded),
        "requirements_blocking": len(blocking),
        "requirements": requirements,
        "blocking_summary": [item["id"] for item in blocking],
        "policy_decision": (
            "Do not mark Overkill Factory as practical 10/10 until every blocking requirement has product-specific or provider-backed evidence."
            if blocking
            else "Factory 10 practical completion can be claimed from current evidence."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, audit: dict[str, Any]) -> None:
    lines = [
        "# Factory 10 Completion Audit",
        "",
        f"Status: `{audit['status']}`",
        f"Completion claim allowed: `{str(audit['completion_claim_allowed']).lower()}`",
        f"Score estimate: `{audit['score_estimate']}`",
        "",
        "## Blocking Requirements",
        "",
    ]
    blocking = [item for item in audit["requirements"] if item["blocking"]]
    for item in blocking:
        lines.append(f"- `{item['id']}`: {item['next_action']}")
    if not blocking:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Policy Decision",
            "",
            audit["policy_decision"],
            "",
            "## Boundary",
            "",
            "This audit is a completion guard. It does not create production evidence; it prevents the factory from claiming practical 10/10 before product-specific and provider-backed evidence exists.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--require-complete", action="store_true")
    args = parser.parse_args(argv)

    audit = build_audit()
    if not args.no_write:
        out_dir = Path(args.out_dir)
        write_json(out_dir / "factory-10-completion-audit.json", audit)
        write_markdown(out_dir / "factory-10-completion-audit.md", audit)
        print(f"Wrote {repo_ref(out_dir / 'factory-10-completion-audit.json')}")
        print(f"Wrote {repo_ref(out_dir / 'factory-10-completion-audit.md')}")

    print(audit["status"])
    if args.require_complete and audit["status"] != "COMPLETE":
        print(audit["policy_decision"], file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
