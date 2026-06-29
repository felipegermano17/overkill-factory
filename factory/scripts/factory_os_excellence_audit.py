#!/usr/bin/env python3
"""Executable audit for the Overkill Factory Operating System layer.

This audit is the consolidation pass before the master update plan. It inspects
all existing OS entries from the canonical operating-system registry and checks
that the OS layer is complete as an audit map while remaining honest about
runtime and product-specific proof gaps.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-os-excellence-audit-registry.json"
DEFAULT_OS_REGISTRY = ROOT / "templates" / "factory-operating-system-registry.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-os-excellence-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-os-excellence-audit.md"

REQUIRED_PRIOR_AUDITS = {
    "swiss_watch_reliability_audit",
    "method_excellence_audit",
    "world_class_process_gap_audit",
    "executor_skill_ecosystem_audit",
    "solana_ai_kit_mandatory_routing",
    "security_excellence_audit",
    "operator_ui_ux_excellence_audit",
}
P0_OS_IDS = {
    "deterministic_control_plane_os",
    "product_truth_research_os",
    "method_os",
    "product_architecture_os",
    "product_experience_design_brand_os",
    "work_unit_execution_dispatch_os",
    "authority_autonomy_os",
    "hermes_worker_runtime_os",
    "evidence_receipt_os",
    "capability_provider_os",
    "agent_profile_authority_os",
    "security_os",
    "operator_experience_os",
    "release_operations_os",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _os_entries(os_registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["os_id"]: entry for entry in _list(os_registry.get("entries")) if isinstance(entry, dict) and entry.get("os_id")}


def _findings(audit_registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {entry["os_id"]: entry for entry in _list(audit_registry.get("os_findings")) if isinstance(entry, dict) and entry.get("os_id")}


def _require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def audit(audit_registry: dict[str, Any], os_registry: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    _require(audit_registry.get("record_type") == "factory_os_excellence_audit_registry", errors, "$.record_type must be factory_os_excellence_audit_registry")
    _require(os_registry.get("record_type") == "factory_operating_system_registry", errors, "os_registry.record_type must be factory_operating_system_registry")

    scope = audit_registry.get("audit_scope", {}) if isinstance(audit_registry.get("audit_scope"), dict) else {}
    _require(scope.get("all_existing_os_required") is True, errors, "$.audit_scope.all_existing_os_required must be true")
    _require(scope.get("new_os_creation_allowed") is False, errors, "$.audit_scope.new_os_creation_allowed must be false")
    _require(scope.get("master_plan_allowed") is False, errors, "$.audit_scope.master_plan_allowed must be false during audit")
    _require(scope.get("runtime_migration_allowed") is False, errors, "$.audit_scope.runtime_migration_allowed must be false during audit")

    source_os = _os_entries(os_registry)
    findings = _findings(audit_registry)
    missing = sorted(set(source_os) - set(findings))
    extra = sorted(set(findings) - set(source_os))
    _require(not missing, errors, "$.os_findings missing existing OS: " + ", ".join(missing))
    _require(not extra, errors, "$.os_findings includes unknown OS: " + ", ".join(extra))

    for os_id, source in source_os.items():
        finding = findings.get(os_id)
        if not finding:
            continue
        _require(finding.get("display_name") == source.get("display_name"), errors, f"$.os_findings[{os_id}].display_name must match source OS registry")
        _require(finding.get("priority") == source.get("priority"), errors, f"$.os_findings[{os_id}].priority must match source OS registry")
        _require(finding.get("owner_worker") == source.get("owner_worker"), errors, f"$.os_findings[{os_id}].owner_worker must match source OS registry")
        _require(bool(finding.get("missing_or_partial_proofs")), errors, f"$.os_findings[{os_id}].missing_or_partial_proofs must not be empty")
        _require("OS is implementation-complete from registry alone" in _list(finding.get("must_not_claim")), errors, f"$.os_findings[{os_id}].must_not_claim must forbid registry-only implementation complete claims")
        if os_id == "hermes_worker_runtime_os":
            _require(finding.get("audit_state") == "runtime_blocked", errors, "hermes_worker_runtime_os must remain runtime_blocked without real Hermes proof")
            _require("live_hermes_worker_orchestration" in _list(finding.get("missing_or_partial_proofs")), errors, "hermes_worker_runtime_os must require live_hermes_worker_orchestration")
        elif source.get("production_claim_state") == "blocked_pending_product_specific_proof":
            _require(finding.get("audit_state") in {"contract_active_product_proof_needed", "hardened_existing_runtime_review_needed"}, errors, f"$.os_findings[{os_id}].audit_state must not overclaim readiness")
            _require(finding.get("product_specific_proof_maturity") in {"partial", "blocked", "not_claimed"}, errors, f"$.os_findings[{os_id}].product_specific_proof_maturity must not be proven")

    policy = audit_registry.get("completion_claim_policy", {}) if isinstance(audit_registry.get("completion_claim_policy"), dict) else {}
    if policy.get("audit_allows_master_plan_to_claim_implementation_complete") is not False:
        errors.append("$.completion_claim_policy.audit_allows_master_plan_to_claim_implementation_complete must be false; audit cannot claim implementation_complete")
    if policy.get("registry_alone_allows_os_ready_claim") is not False:
        errors.append("$.completion_claim_policy.registry_alone_allows_os_ready_claim must be false")
    if policy.get("runtime_proof_required") is not True:
        errors.append("$.completion_claim_policy.runtime_proof_required must be true")
    if policy.get("product_specific_proof_required") is not True:
        errors.append("$.completion_claim_policy.product_specific_proof_required must be true")

    prior_mapping = audit_registry.get("prior_audit_mapping", {}) if isinstance(audit_registry.get("prior_audit_mapping"), dict) else {}
    missing_prior = sorted(REQUIRED_PRIOR_AUDITS - set(prior_mapping))
    _require(not missing_prior, errors, "$.prior_audit_mapping missing prior audits: " + ", ".join(missing_prior))
    for audit_name, mapping in prior_mapping.items():
        for key in ("primary_os", "secondary_os"):
            for os_id in _list(mapping.get(key)):
                _require(os_id in source_os, errors, f"$.prior_audit_mapping[{audit_name}].{key} references unknown OS {os_id}")

    p0_count = sum(1 for entry in source_os.values() if entry.get("priority") == "P0")
    partial_or_blocked = [
        os_id
        for os_id, finding in findings.items()
        if finding.get("runtime_maturity") != "proven" or finding.get("product_specific_proof_maturity") != "proven" or finding.get("audit_state") == "runtime_blocked"
    ]
    if len(partial_or_blocked) < 12:
        warnings.append("OS audit is unexpectedly optimistic; verify real runtime/product proof before reducing partial count")

    os_results: list[dict[str, Any]] = []
    for os_id in sorted(source_os):
        source = source_os[os_id]
        finding = findings.get(os_id, {})
        os_results.append({
            "os_id": os_id,
            "display_name": source.get("display_name"),
            "priority": source.get("priority"),
            "owner_worker": source.get("owner_worker"),
            "source_status": source.get("status"),
            "audit_state": finding.get("audit_state"),
            "contract_maturity": finding.get("contract_maturity"),
            "runtime_maturity": finding.get("runtime_maturity"),
            "product_specific_proof_maturity": finding.get("product_specific_proof_maturity"),
            "integration_maturity": finding.get("integration_maturity"),
            "missing_or_partial_proofs": finding.get("missing_or_partial_proofs", []),
            "master_plan_implication": finding.get("master_plan_implication"),
            "linked_prior_audits": finding.get("linked_prior_audits", []),
        })

    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_os_excellence_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "summary": {
            "errors": len(errors),
            "os_count": len(source_os),
            "p0_count": p0_count,
            "p1_count": len(source_os) - p0_count,
            "partial_or_blocked_count": len(partial_or_blocked),
            "prior_audit_mapping_count": len(prior_mapping),
        },
        "os_results": os_results,
        "partial_or_blocked_os": sorted(partial_or_blocked),
        "errors": errors,
        "warnings": warnings,
        "next_step": "master plan after audit rounds; do not treat this audit as implementation complete",
    }


def write_markdown(report: dict[str, Any], audit_registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory OS Excellence Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append("")
    lines.append(audit_registry.get("audit_scope", {}).get("thesis", ""))
    lines.append("")
    lines.append("This audit prepares the master plan. It does not claim implementation complete.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    summary = report["summary"]
    lines.append(f"- OS count: {summary['os_count']}")
    lines.append(f"- P0 OS: {summary['p0_count']}")
    lines.append(f"- P1 OS: {summary['p1_count']}")
    lines.append(f"- Partial or blocked: {summary['partial_or_blocked_count']}")
    lines.append("")
    lines.append("## OS Results")
    lines.append("")
    for entry in report["os_results"]:
        lines.append(f"- {entry['display_name']} (`{entry['os_id']}`): {entry['audit_state']}")
        lines.append(f"  - owner: {entry['owner_worker']} / {entry['priority']}")
        lines.append(f"  - contract/runtime/product proof: {entry['contract_maturity']}/{entry['runtime_maturity']}/{entry['product_specific_proof_maturity']}")
        lines.append(f"  - missing/partial proofs: {', '.join(entry['missing_or_partial_proofs'])}")
        lines.append(f"  - master plan implication: {entry['master_plan_implication']}")
    lines.append("")
    lines.append("## Prior Audit Mapping")
    lines.append("")
    for audit_name, mapping in audit_registry.get("prior_audit_mapping", {}).items():
        lines.append(f"- {audit_name}")
        lines.append(f"  - primary OS: {', '.join(mapping['primary_os'])}")
        lines.append(f"  - secondary OS: {', '.join(mapping['secondary_os'])}")
        lines.append(f"  - why: {mapping['why_it_matters']}")
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for error in report["errors"]:
            lines.append(f"- {error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--os-registry", type=Path, default=DEFAULT_OS_REGISTRY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    audit_registry = load_json(args.registry)
    os_registry = load_json(args.os_registry)
    report = audit(audit_registry, os_registry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, audit_registry, args.markdown)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.markdown}")
    print(report["result"])
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
