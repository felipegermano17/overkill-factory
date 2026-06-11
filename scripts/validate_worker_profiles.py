#!/usr/bin/env python3
"""Validate worker profiles and Hermes dispatch bindings.

The public worker registry names the factory workers. This validator makes sure
each worker also has an executable agent profile and a Hermes binding. Without
that layer, a worker is only a process role, not an operable agent.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "agents" / "worker-registry.public.json"
PROFILES_PATH = ROOT / "agents" / "worker-profiles.public.json"
BINDINGS_PATH = ROOT / "agents" / "hermes-profile-bindings.public.json"
SECURITY_MATRIX_PATH = ROOT / "docs" / "agents" / "security-specialist-matrix.md"
PROFILE_SMOKE_PATH = ROOT / "validation" / "hermes-live" / "factory12-agent-profile-smoke.json"


SECURITY_DOMAINS = {
    "networking": "Networking",
    "linux-systems": "Linux/Systems",
    "web-security": "Web Security",
    "ethical-hacking": "Ethical Hacking",
    "security-tools": "Security Tools",
    "cloud-security": "Cloud Security",
    "detection-monitoring": "Detection & Monitoring",
    "cryptography": "Cryptography",
    "security-operations": "Security Operations",
    "future-security": "Future of Security",
    "supply-chain": "Supply Chain",
    "onchain-solana-quasar": "Solana/Quasar/Auditor",
}

SECURITY_CRITICAL_WORKERS = {
    "security-orchestrator",
    "codex-security",
    "appsec-owasp-specialist",
    "agentic-ai-security-specialist",
    "cloud-infra-security-specialist",
    "crypto-key-management-specialist",
    "solana-quasar-auditor",
    "public-safety-gate",
    "supply-chain-gate",
    "detection-monitoring-worker",
}

ALLOWED_PHASES = {f"F{index}" for index in range(30)}
ALLOWED_RISKS = {"R0", "R1", "R2", "R3", "R4"}

EARLY_SECURITY_WORKERS = {
    "security-orchestrator",
    "appsec-owasp-specialist",
    "agentic-ai-security-specialist",
    "cloud-infra-security-specialist",
    "crypto-key-management-specialist",
    "solana-quasar-auditor",
    "detection-monitoring-worker",
}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def combined_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(combined_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(combined_text(item) for item in value)
    return str(value)


def validate() -> list[str]:
    findings: list[str] = []
    registry = load_json(REGISTRY_PATH)
    profiles_doc = load_json(PROFILES_PATH)
    bindings_doc = load_json(BINDINGS_PATH)
    smoke_doc = load_json(PROFILE_SMOKE_PATH) if PROFILE_SMOKE_PATH.exists() else {}

    workers = {str(worker["worker_id"]): worker for worker in registry.get("workers", [])}
    profiles = profiles_doc.get("profiles", {})
    bindings = bindings_doc.get("bindings", {})
    if not isinstance(profiles, dict):
        findings.append("profiles must be an object keyed by worker_id")
        profiles = {}
    if not isinstance(bindings, dict):
        findings.append("bindings must be an object keyed by worker_id")
        bindings = {}
    smoke_rows = smoke_doc.get("rows", []) if isinstance(smoke_doc, dict) else []
    if not isinstance(smoke_rows, list):
        findings.append("profile smoke rows must be an array")
        smoke_rows = []
    smoke_by_worker = {
        str(row.get("worker_id")): row
        for row in smoke_rows
        if isinstance(row, dict) and row.get("worker_id")
    }

    worker_ids = set(workers)
    profile_ids = set(profiles)
    binding_ids = set(bindings)
    for missing in sorted(worker_ids - profile_ids):
        findings.append(f"{missing}: missing worker profile")
    for extra in sorted(profile_ids - worker_ids):
        findings.append(f"{extra}: profile has no registered worker")
    for missing in sorted(worker_ids - binding_ids):
        findings.append(f"{missing}: missing Hermes profile binding")
    for extra in sorted(binding_ids - worker_ids):
        findings.append(f"{extra}: binding has no registered worker")
    smoke_ids = set(smoke_by_worker)
    for missing in sorted(worker_ids - smoke_ids):
        findings.append(f"{missing}: missing Hermes profile smoke row")
    for extra in sorted(smoke_ids - worker_ids):
        findings.append(f"{extra}: smoke row has no registered worker")

    for worker_id in sorted(worker_ids & profile_ids):
        worker = workers[worker_id]
        profile = profiles[worker_id]
        binding = bindings.get(worker_id, {})
        if profile.get("worker_id") != worker_id:
            findings.append(f"{worker_id}: profile.worker_id mismatch")
        if profile.get("topology") != worker.get("mode"):
            findings.append(f"{worker_id}: topology must match registry mode")
        if profile.get("output_contract", {}).get("receipt_field") != worker.get("output_contract"):
            findings.append(f"{worker_id}: profile receipt field must match worker output_contract")
        if binding:
            if binding.get("worker_id") != worker_id:
                findings.append(f"{worker_id}: binding.worker_id mismatch")
            if binding.get("profile_id") != profile.get("profile_id"):
                findings.append(f"{worker_id}: binding.profile_id must match profile")
            if binding.get("receipt_field") != worker.get("output_contract"):
                findings.append(f"{worker_id}: binding receipt_field must match worker output_contract")
            if "overkill-factory" not in binding.get("skill_refs", []):
                findings.append(f"{worker_id}: binding must include overkill-factory skill")
            if "hermes-kanban" not in binding.get("skill_refs", []):
                findings.append(f"{worker_id}: binding must include hermes-kanban skill")
            if binding.get("can_mutate_card_state") is not False:
                findings.append(f"{worker_id}: worker profile must not directly mutate card state")
            policy = binding.get("dispatch_queue_policy")
            if not isinstance(policy, dict):
                findings.append(f"{worker_id}: binding missing dispatch_queue_policy")
            else:
                if policy.get("source_of_truth") != "factoryctl.worker_queue_class":
                    findings.append(f"{worker_id}: dispatch queue source must be factoryctl.worker_queue_class")
                if not policy.get("default_queue"):
                    findings.append(f"{worker_id}: dispatch_queue_policy missing default_queue")
                if not policy.get("allowed_effective_queues"):
                    findings.append(f"{worker_id}: dispatch_queue_policy missing allowed_effective_queues")
            for field in (
                "profile_manifest_ref",
                "profile_description_ref",
                "skill_install_ref",
                "last_hermes_smoke_ref",
            ):
                ref = str(binding.get(field) or "").strip()
                if not ref:
                    findings.append(f"{worker_id}: binding missing {field}")
                elif ref.startswith(("http://", "https://", "external:")):
                    pass
                elif not (ROOT / ref).exists():
                    findings.append(f"{worker_id}: binding {field} does not exist: {ref}")
            if not str(binding.get("toolset_policy") or "").strip():
                findings.append(f"{worker_id}: binding missing toolset_policy")
            result_schema = str(binding.get("result_schema") or "").strip()
            if not result_schema:
                findings.append(f"{worker_id}: binding missing result_schema")
            elif not (ROOT / result_schema).exists():
                findings.append(f"{worker_id}: binding result_schema does not exist: {result_schema}")
        smoke = smoke_by_worker.get(worker_id, {})
        if smoke:
            if smoke.get("status") != "PASS":
                findings.append(f"{worker_id}: profile smoke status must be PASS")
            if smoke.get("hermes_profile_name") != binding.get("hermes_profile_name"):
                findings.append(f"{worker_id}: smoke profile name must match binding")
            if smoke.get("result_schema") != binding.get("result_schema"):
                findings.append(f"{worker_id}: smoke result_schema must match binding")
            for field in ("profile_manifest_ref", "profile_description_ref", "skill_install_ref"):
                if smoke.get(field) != binding.get(field):
                    findings.append(f"{worker_id}: smoke {field} must match binding")
            checks = smoke.get("checks", {})
            if not isinstance(checks, dict):
                findings.append(f"{worker_id}: smoke checks must be an object")
            else:
                for check in (
                    "profile_exists",
                    "profile_yaml_present",
                    "soul_md_present",
                    "profile_description_strong",
                    "binding_present",
                    "queue_source_verified",
                    "result_schema_verified",
                    "skills_verified",
                ):
                    if checks.get(check) is not True:
                        findings.append(f"{worker_id}: smoke check {check} must be true")
                if worker_id in SECURITY_CRITICAL_WORKERS:
                    for check in ("domain_contract_verified", "waiver_contract_verified"):
                        if checks.get(check) is not True:
                            findings.append(f"{worker_id}: smoke check {check} must be true")

        if "human_gate_required_when" not in profile.get("authority", {}):
            findings.append(f"{worker_id}: missing human gate authority conditions")
        if profile.get("failure_contract", {}).get("retry_limit") is None:
            findings.append(f"{worker_id}: missing bounded failure contract")
        if len(profile.get("understanding_contract", {}).get("must_record", [])) < 3:
            findings.append(f"{worker_id}: missing operator understanding contract")
        phases = set(profile.get("activation", {}).get("phases", []))
        unknown_phases = phases - ALLOWED_PHASES
        if unknown_phases:
            findings.append(f"{worker_id}: unknown activation phases {sorted(unknown_phases)}")
        risk_floor = profile.get("activation", {}).get("risk_floor")
        if risk_floor not in ALLOWED_RISKS:
            findings.append(f"{worker_id}: invalid risk_floor {risk_floor!r}")
        retry_limit = profile.get("failure_contract", {}).get("retry_limit")
        if not isinstance(retry_limit, int) or retry_limit < 1 or retry_limit > 3:
            findings.append(f"{worker_id}: retry_limit must be between 1 and 3")

        if worker_id in SECURITY_CRITICAL_WORKERS:
            domain_contract = profile.get("domain_contract")
            waiver_contract = profile.get("waiver_contract")
            if not isinstance(domain_contract, dict):
                findings.append(f"{worker_id}: missing machine-checkable domain_contract")
            else:
                domain_slugs = set(domain_contract.get("domain_slugs", []))
                unknown_domains = domain_slugs - set(SECURITY_DOMAINS)
                if unknown_domains:
                    findings.append(f"{worker_id}: unknown security domains {sorted(unknown_domains)}")
                if len(domain_contract.get("required_controls", [])) < 2:
                    findings.append(f"{worker_id}: domain_contract needs at least two controls")
                if len(domain_contract.get("minimum_evidence", [])) < 2:
                    findings.append(f"{worker_id}: domain_contract needs at least two evidence refs")
                routing_moments = set(domain_contract.get("routing_moments", []))
                if worker_id in EARLY_SECURITY_WORKERS and "architecture-pre-decomposition" not in routing_moments:
                    findings.append(f"{worker_id}: security domain must route before decomposition")
            if not isinstance(waiver_contract, dict):
                findings.append(f"{worker_id}: missing structured waiver_contract")
            else:
                for field in ("requires_owner", "requires_scope", "requires_expiry_or_review"):
                    if waiver_contract.get(field) is not True:
                        findings.append(f"{worker_id}: waiver_contract.{field} must be true")
                if not waiver_contract.get("requires_human_gate_for"):
                    findings.append(f"{worker_id}: waiver_contract must name human-gated waiver cases")
                if not waiver_contract.get("forbidden"):
                    findings.append(f"{worker_id}: waiver_contract must name forbidden waivers")
            if binding:
                routing_moments = set(binding.get("routing_moments", []))
                if not routing_moments:
                    findings.append(f"{worker_id}: Hermes binding missing routing_moments")
                if worker_id in EARLY_SECURITY_WORKERS and "architecture-pre-decomposition" not in routing_moments:
                    findings.append(f"{worker_id}: Hermes binding routes security too late")
            if profile.get("review_contract", {}).get("reviewer_mode") == "self_check_only":
                findings.append(f"{worker_id}: security-critical workers cannot rely on self_check_only review")

    domain_owners: dict[str, list[str]] = {slug: [] for slug in SECURITY_DOMAINS}
    for worker_id, profile in profiles.items():
        domain_contract = profile.get("domain_contract", {})
        if isinstance(domain_contract, dict):
            for slug in domain_contract.get("domain_slugs", []):
                if slug in domain_owners:
                    domain_owners[slug].append(worker_id)
    for slug, label in SECURITY_DOMAINS.items():
        if not domain_owners[slug]:
            findings.append(f"security domain {label} ({slug}) has no machine-checkable owner")

    def require_text(worker_id: str, fragments: list[str]) -> None:
        text = combined_text(profiles.get(worker_id, {})).lower()
        for fragment in fragments:
            if fragment.lower() not in text:
                findings.append(f"{worker_id}: missing required fragment {fragment!r}")

    require_text("solana-quasar-auditor", ["Quasar", "Auditor", "Anchor", "upgrade authority", "multisig", "timelock", "oracle", "MEV", "RPC", "finality"])
    require_text("codex-security", ["Codex Security", "scope", "findings", "attack path", "authorized scope", "pre-release"])
    require_text("appsec-owasp-specialist", ["OWASP", "ASVS", "API Top 10", "IDOR", "rate limit", "SSRF", "CSRF", "XSS"])
    require_text("agentic-ai-security-specialist", ["prompt injection", "tool", "memory", "OWASP LLM", "exfiltration", "agent-to-agent", "autonomy budget"])
    require_text("cloud-infra-security-specialist", ["firewall", "container", "Kubernetes", "systemd", "runtime user"])
    require_text("crypto-key-management-specialist", ["key", "custody", "never", "KMS", "HSM", "break-glass", "separation of duties"])
    require_text("supply-chain-gate", ["SLSA", "provenance", "attestation", "OIDC", "lockfiles", "container image", "branch protection"])
    require_text("detection-monitoring-worker", ["security telemetry", "alert test", "severity", "runbook", "incident drill"])
    require_text("public-safety-gate", ["raw study", "public", "scan"])
    require_text("human-gate-clerk", ["invent", "human", "approval"])

    for reviewer_id in ("independent-reviewer", "autoreview-gate"):
        text = combined_text(profiles.get(reviewer_id, {})).lower()
        if "report-only" not in text and "report only" not in text:
            findings.append(f"{reviewer_id}: reviewer must be report-only")
        if "modify implementation artifacts" not in text and "edits code" not in text:
            findings.append(f"{reviewer_id}: reviewer must not modify implementation artifacts")

    if not SECURITY_MATRIX_PATH.exists():
        findings.append("docs/agents/security-specialist-matrix.md is missing")
    else:
        matrix = SECURITY_MATRIX_PATH.read_text(encoding="utf-8").lower()
        for slug, label in SECURITY_DOMAINS.items():
            if slug not in matrix:
                findings.append(f"security matrix missing {label} ({slug})")

    return findings


def main() -> int:
    findings = validate()
    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
