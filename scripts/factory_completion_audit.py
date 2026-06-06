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
    if not reusable_product_scope_is_valid(data, record_type=record_type):
        return False
    return True


def production_cu_svm_economic_result(rel_path: str) -> bool:
    path = ROOT / rel_path
    if not path.exists():
        return False
    try:
        data = load_json(path)
    except json.JSONDecodeError:
        return False
    if not production_worker_result(rel_path):
        return False
    return cu_svm_economic_scope_is_valid(data)


def cu_svm_economic_scope_is_valid(data: dict[str, Any]) -> bool:
    if data.get("record_type") != "cu_svm_economic_proof":
        return False
    if data.get("proof_kind") != "production_quasar_cu_svm_economic":
        return False
    if data.get("blocking_findings") is True:
        return False

    target = data.get("product_target")
    if not isinstance(target, dict):
        return False
    source_ref = str(target.get("source_ref") or "")
    source_sha256 = str(target.get("source_sha256") or "")
    if not source_ref.startswith("products/") or len(source_sha256) != 64:
        return False
    if data.get("source_target") != source_ref or data.get("source_sha256") != source_sha256:
        return False
    if target.get("environment_class") not in {"production-validation-quasar-svm", "production-quasar-svm"}:
        return False

    compute = data.get("compute_unit_profile")
    if not isinstance(compute, dict):
        return False
    if compute.get("profile_kind") != "runtime_svm_measurement" or compute.get("real_solana_cu_measured") is not True:
        return False
    budget = compute.get("compute_budget_units")
    if not isinstance(budget, int) or budget <= 0:
        return False
    instruction_profile = compute.get("instruction_profile")
    if not isinstance(instruction_profile, dict):
        return False
    required_instructions = {"review_vault_instruction", "record_audit_receipt", "block_instruction"}
    if not required_instructions.issubset(instruction_profile):
        return False
    for name in required_instructions:
        item = instruction_profile.get(name)
        if not isinstance(item, dict):
            return False
        cu = item.get("compute_units_consumed")
        if not isinstance(cu, int) or cu <= 0 or cu >= budget:
            return False
        if item.get("within_budget") is not True or item.get("status") != "PASS":
            return False

    flow = data.get("svm_or_client_flow_coverage")
    if not isinstance(flow, dict):
        return False
    if flow.get("real_svm_transaction_harness") is not True or flow.get("quasar_test_passed") is not True:
        return False
    flow_names = {str(item.get("name") or "") for item in flow.get("flows") or [] if isinstance(item, dict)}
    required_flows = required_instructions | {"sequential_review_record_block"}
    if not required_flows.issubset(flow_names):
        return False

    negative = data.get("negative_case_coverage")
    if not isinstance(negative, dict):
        return False
    for name in ("review_zero_hash", "record_zero_hash", "block_zero_reason"):
        item = negative.get(name)
        if not isinstance(item, dict) or item.get("status") != "PASS":
            return False

    economic = data.get("economic_safety")
    if not isinstance(economic, dict):
        return False
    if economic.get("overall_verdict") != "PASS":
        return False
    if economic.get("funds_movement") is not False:
        return False
    if economic.get("persistent_state_writes") is not False:
        return False
    if economic.get("authority_changes") is not False:
        return False
    if economic.get("cpi_calls") != 0:
        return False
    observed = economic.get("svm_observed")
    if not isinstance(observed, dict):
        return False
    for name in ("lamports_unchanged", "pda_data_unchanged"):
        item = observed.get(name)
        if not isinstance(item, dict) or item.get("status") != "PASS":
            return False

    properties = data.get("property_fuzz_coverage")
    if not isinstance(properties, dict) or int(properties.get("total_cases") or 0) < 518:
        return False

    return True


def reusable_product_scope_is_valid(data: dict[str, Any], *, record_type: str | None = None) -> bool:
    target = data.get("product_target")
    if not isinstance(target, dict):
        return False
    product_id = str(target.get("product_id") or "").strip()
    approval_scope = str(target.get("approval_scope") or "").strip()
    if len(product_id) < 3 or len(approval_scope) < 10:
        return False

    if record_type == "product_face_result":
        return bool(target.get("target_sha256") or target.get("deployed_production"))

    if record_type == "auditor_result":
        if data.get("audit_mode") != "code_audit" or data.get("preflight_only") is True:
            return False
        environment_class = str(target.get("environment_class") or "")
        if environment_class not in {"production-validation-quasar-source", "production-quasar-source"}:
            return False
        source_ref = str(target.get("source_ref") or "")
        source_sha256 = str(target.get("source_sha256") or "")
        if not source_ref.startswith("products/") or len(source_sha256) != 64:
            return False
        toolchain = data.get("quasar_toolchain_proof") or {}
        if toolchain.get("source_target") != source_ref:
            return False
        if toolchain.get("source_sha256") != source_sha256:
            return False
        if toolchain.get("build_status") != "PASS" or toolchain.get("test_status") != "PASS":
            return False
        vectors = data.get("known_vectors_coverage") or {}
        if int(vectors.get("total") or 0) < 100:
            return False
        checklist = data.get("checklist_coverage") or {}
        required_prefixes = ("01", "02", "03", "04", "05", "06", "07")
        covered = {str(key)[:2] for key, value in checklist.items() if isinstance(value, dict) and value.get("status") == "done"}
        return all(prefix in covered for prefix in required_prefixes)

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

    if production_cu_svm_economic_result("validation/production/quasar/cu-svm-economic-proof.json"):
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
                [
                    "validation/remote-proof/crabbox-static-ssh-proof-2026-06-06.json",
                    "validation/remote-proof/managed-remote-proof-probe.json",
                ],
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
    elif public_proof("validation/product-specific/qvg-full-product-worker-graph.json"):
        requirements.append(
            bounded_requirement(
                "full_product_specific_worker_graph",
                "Full product-specific multi-specialist execution",
                ["validation/product-specific/qvg-full-product-worker-graph.json"],
                "The goal is a factory that carries a real product through all required workers, not isolated prooflets.",
                "Rerun the same graph on a production product target and require every critical lane to be reusable_for_product=true before practical 10/10 completion.",
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
    score_estimate = "10/10"
    if status != "COMPLETE":
        if len(blocking) <= 4 and len(achieved) >= 5:
            score_estimate = "9.996/10"
        elif len(blocking) <= 5 and len(achieved) >= 4:
            score_estimate = "9.994/10"
        else:
            score_estimate = "9.992/10"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-completion-audit.schema.json",
        "created_at": now_iso(),
        "audit_kind": "factory_10_practical_completion",
        "status": status,
        "completion_claim_allowed": status == "COMPLETE",
        "score_estimate": score_estimate,
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
