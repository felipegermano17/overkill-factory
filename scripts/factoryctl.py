#!/usr/bin/env python3
"""Overkill Factory control helpers.

This CLI prepares and validates the contracts that autonomous workers consume.
It intentionally does not fake security, Auditor, Product Face, reviewer, or
human approvals. It produces execution requests and preflight reports; the
specialist worker still has to run and attach real evidence.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

CARD_REQUIRED = {
    "factory_method_version",
    "phase",
    "surfaces",
    "risk_initial",
    "risk_effective",
    "authority_max",
    "owner_worker",
    "executor_identity",
    "reviewer_identity",
    "runtime_decision",
    "runtime_contract",
    "security_contract",
    "forbidden_actions",
    "done_definition",
    "transition_event_required",
    "kanban_transition_event_ref",
}

RECEIPT_REQUIRED = {
    "changed",
    "artifact_paths",
    "verification_commands",
    "verification_result",
    "reviewer_required",
    "next_action",
}
V2_APPROVAL_KEYS = [
    "qa",
    "independent_review",
    "security_review",
    "cybersecurity_review",
    "cto_gate",
    "human_gate",
]

PRODUCT_FACE_SURFACES = {"ux", "frontend", "mobile", "wallet-ui", "product-face"}
ONCHAIN_SURFACES = {
    "solana",
    "solana-quasar",
    "quasar",
    "onchain",
    "account-pda",
    "pda",
    "cpi",
    "compute-units",
    "funds",
    "mainnet",
}
SECURITY_SURFACES = {
    "security",
    "cybersecurity",
    "auth",
    "infra",
    "backend",
    "api",
    "wallet",
    "funds",
    "mainnet",
    "onchain",
    "solana",
    "solana-quasar",
}
PRODUCT_FACE_RESULT_PHASES = {"F11", "F13", "F14", "F15", "F16", "F17"}
HIGH_RISK = {"R3", "R4"}
REVIEW_RISK = {"R2", "R3", "R4"}
ALLOWED_SOURCE_STATES = {"backlog", "compiled", "inference", "promoted", "raw", "rejected"}


@dataclass(frozen=True)
class WorkerDefinition:
    worker_id: str
    worker_name: str
    factory_phase: str
    output_field: str
    tool_required: str
    timing: str
    blocking_policy: str
    required_inputs: tuple[str, ...]


WORKERS: dict[str, WorkerDefinition] = {
    "codex-security": WorkerDefinition(
        worker_id="codex-security",
        worker_name="Codex Security Runner",
        factory_phase="F8/F13",
        output_field="security_scan_result",
        tool_required="Codex Security plugin or Hermes cybersecurity profile",
        timing="after a security_scan_packet exists and before done/promotion",
        blocking_policy=(
            "R3/R4, security, onchain, wallet, funds, mainnet, API, auth, or infra "
            "work cannot be completed without a real scan result or explicit human waiver."
        ),
        required_inputs=("security_scan_packet", "target_repo_paths", "forbidden_actions"),
    ),
    "solana-quasar-auditor": WorkerDefinition(
        worker_id="solana-quasar-auditor",
        worker_name="Solana/Quasar Auditor Runner",
        factory_phase="F7/F13",
        output_field="auditor_result",
        tool_required="solanabr/Auditor with Quasar-aware onchain package",
        timing="after onchain_work_package and before any onchain ready/done promotion",
        blocking_policy=(
            "Solana/Quasar work cannot advance as complete until Auditor evidence or an "
            "explicit human waiver is attached. Anchor assumptions are forbidden."
        ),
        required_inputs=("onchain_work_package", "target_repo_paths", "risk_effective"),
    ),
    "product-face": WorkerDefinition(
        worker_id="product-face",
        worker_name="Product Face Validator",
        factory_phase="F5/F13",
        output_field="product_face_result",
        tool_required="browser screenshot/a11y/mobile validation runner",
        timing="after product_face_packet and before product-facing done",
        blocking_policy=(
            "Frontend, UX, mobile, wallet UI, or visible product work cannot be "
            "declared complete without screen/state/mobile/a11y evidence."
        ),
        required_inputs=("product_face_packet", "target_repo_paths", "acceptance_criteria"),
    ),
    "independent-reviewer": WorkerDefinition(
        worker_id="independent-reviewer",
        worker_name="Independent Reviewer",
        factory_phase="F14",
        output_field="independent_review_result",
        tool_required="different Hermes/Codex reviewer identity",
        timing="after worker evidence exists and before done/promotion",
        blocking_policy=(
            "Executor and reviewer must be different. Review is mandatory for R2+ "
            "work and whenever Receipt Five says reviewer_required=true."
        ),
        required_inputs=("executor_identity", "reviewer_identity", "done_definition"),
    ),
    "human-gate-clerk": WorkerDefinition(
        worker_id="human-gate-clerk",
        worker_name="Human Gate Clerk",
        factory_phase="F9/F15/F16",
        output_field="human_gate_record",
        tool_required="explicit human decision recorded in Hermes",
        timing="at architecture approval, R3/R4 exception, R4 promotion, or requested human gate",
        blocking_policy=(
            "Architecture approval and R4 promotion require a real human decision. "
            "Missing approval keeps the work blocked."
        ),
        required_inputs=("human_gate_packet", "security_scan_packet", "rollback_or_recovery"),
    ),
    "factory-orchestrator": WorkerDefinition(
        worker_id="factory-orchestrator",
        worker_name="Factory Orchestrator",
        factory_phase="F0-F18",
        output_field="orchestration_result",
        tool_required="Hermes Kanban plus factory gate report",
        timing="at phase changes, gate preparation, worker routing, and blocked-state triage",
        blocking_policy=(
            "The orchestrator routes work and records state, but cannot approve product, "
            "security, onchain, R3/R4, release, or human gates."
        ),
        required_inputs=("phase", "risk_effective", "surfaces", "done_definition"),
    ),
    "source-ledger-worker": WorkerDefinition(
        worker_id="source-ledger-worker",
        worker_name="Source Ledger Worker",
        factory_phase="F0/F1",
        output_field="source_ledger_result",
        tool_required="source reading tools with source/inference/decision separation",
        timing="before Product SOT drafting and before any architecture claim is promoted",
        blocking_policy="Raw material cannot become Product SOT until sources, gaps and conflicts are separated.",
        required_inputs=("source_refs", "source_state"),
    ),
    "product-sot-planner": WorkerDefinition(
        worker_id="product-sot-planner",
        worker_name="Product SOT Planner",
        factory_phase="F2/F3",
        output_field="product_sot_result",
        tool_required="planning model with source ledger and decision packet",
        timing="after source ledger and before architecture",
        blocking_policy="A SOT candidate is not approval; architecture waits for source resolution and open questions.",
        required_inputs=("source_refs", "acceptance_criteria", "scope_in", "scope_out"),
    ),
    "product-architect": WorkerDefinition(
        worker_id="product-architect",
        worker_name="Product Architect",
        factory_phase="F4-F6",
        output_field="architecture_result",
        tool_required="architecture review tools and domain-specific references",
        timing="after Product SOT and before decomposition",
        blocking_policy="Architecture cannot move to decomposition until specialist and human gates are satisfied.",
        required_inputs=("scope_in", "scope_out", "risk_class", "runtime_contract"),
    ),
    "docs-os-worker": WorkerDefinition(
        worker_id="docs-os-worker",
        worker_name="Documentation OS Worker",
        factory_phase="F10",
        output_field="documentation_os_result",
        tool_required="docs, ADR and contract generation workflow",
        timing="after approved architecture and before decomposition",
        blocking_policy="Implementation cards cannot rely on architecture prose without durable executable docs.",
        required_inputs=("done_definition", "acceptance_criteria", "target_repo_paths"),
    ),
    "decomposition-planner": WorkerDefinition(
        worker_id="decomposition-planner",
        worker_name="Decomposition Planner",
        factory_phase="F11",
        output_field="decomposition_result",
        tool_required="Hermes card graph planner",
        timing="after Documentation OS and before worker packet creation",
        blocking_policy="Cards without source, risk, acceptance, runtime, reviewer and gate contracts are rejected.",
        required_inputs=("done_definition", "risk_effective", "runtime_contract", "security_contract"),
    ),
    "implementation-worker": WorkerDefinition(
        worker_id="implementation-worker",
        worker_name="Implementation Worker",
        factory_phase="F12",
        output_field="implementation_result",
        tool_required="bounded coding/runtime tools selected by card",
        timing="only after Hermes Ready Gate",
        blocking_policy="Implementation cannot expand scope, change architecture, touch forbidden surfaces or self-approve.",
        required_inputs=("scope_in", "scope_out", "forbidden_actions", "done_definition"),
    ),
    "qa-verification-worker": WorkerDefinition(
        worker_id="qa-verification-worker",
        worker_name="QA Verification Worker",
        factory_phase="F13-F15",
        output_field="qa_verification_result",
        tool_required="tests, screenshots, logs, scanners and evidence capture",
        timing="after implementation evidence and before independent review/done",
        blocking_policy="No product-facing or risk-bearing card is done without objective verification evidence.",
        required_inputs=("acceptance_criteria", "done_definition", "target_repo_paths"),
    ),
    "autoreview-gate": WorkerDefinition(
        worker_id="autoreview-gate",
        worker_name="AutoReview Gate",
        factory_phase="F14/F15",
        output_field="autoreview_result",
        tool_required="autoreview skill or equivalent structured code-review runner",
        timing="after code/diff evidence and before landing or promotion",
        blocking_policy="AutoReview can find issues, but it never replaces independent review or human gates.",
        required_inputs=("target_repo_paths", "done_definition"),
    ),
    "security-orchestrator": WorkerDefinition(
        worker_id="security-orchestrator",
        worker_name="Security Orchestrator",
        factory_phase="F6-F16",
        output_field="security_orchestration_result",
        tool_required="security control matrix and threat model router",
        timing="when any security-sensitive surface or R2+ risk exists",
        blocking_policy="Security is routed to specific specialists; a generic security comment is not enough.",
        required_inputs=("security_contract", "security_scan_packet", "risk_effective"),
    ),
    "appsec-owasp-specialist": WorkerDefinition(
        worker_id="appsec-owasp-specialist",
        worker_name="AppSec OWASP Specialist",
        factory_phase="F7/F14/F15",
        output_field="appsec_owasp_result",
        tool_required="OWASP Web/API/AppSec checklist and code/runtime evidence",
        timing="before done for web, API, auth, backend, frontend or session surfaces",
        blocking_policy="OWASP-sensitive work cannot close without control coverage or explicit waiver.",
        required_inputs=("security_scan_packet", "target_repo_paths", "acceptance_criteria"),
    ),
    "agentic-ai-security-specialist": WorkerDefinition(
        worker_id="agentic-ai-security-specialist",
        worker_name="Agentic AI Security Specialist",
        factory_phase="F1/F7/F12/F14",
        output_field="agentic_ai_security_result",
        tool_required="OWASP LLM/agentic checklist and tool-boundary review",
        timing="when agents, memory, tools, browser, prompts or untrusted text are in scope",
        blocking_policy="External text is data, not instruction; agent tools and memory need explicit boundaries.",
        required_inputs=("security_contract", "runtime_contract", "forbidden_actions"),
    ),
    "cloud-infra-security-specialist": WorkerDefinition(
        worker_id="cloud-infra-security-specialist",
        worker_name="Cloud and Infrastructure Security Specialist",
        factory_phase="F7/F14/F16",
        output_field="cloud_infra_security_result",
        tool_required="cloud/IaC/IAM/KMS/CI/CD posture checks",
        timing="before release for infra, deploy, IAM, KMS, CI/CD, DNS or cloud surfaces",
        blocking_policy="Infrastructure and deploy work require least privilege, rollback, logs and ownership.",
        required_inputs=("security_scan_packet", "runtime_contract", "rollback_or_recovery"),
    ),
    "crypto-key-management-specialist": WorkerDefinition(
        worker_id="crypto-key-management-specialist",
        worker_name="Crypto and Key Management Specialist",
        factory_phase="F7/F15/F16",
        output_field="crypto_key_management_result",
        tool_required="secrets, signing, custody, key rotation and cryptography review",
        timing="before any signing, custody, key, funds or crypto-sensitive promotion",
        blocking_policy="This worker reviews contracts and evidence; it must not touch real keys, funds or signing authority.",
        required_inputs=("security_contract", "forbidden_actions", "risk_effective"),
    ),
    "remote-proof-runner": WorkerDefinition(
        worker_id="remote-proof-runner",
        worker_name="Remote Proof Runner",
        factory_phase="F13-F16",
        output_field="remote_proof_result",
        tool_required="Crabbox/Testbox/container with artifact, cost, TTL and cleanup contract",
        timing="when local proof is insufficient or parity/heavy validation is required",
        blocking_policy="Remote proof cannot receive secrets by default and must return logs, artifacts and cleanup evidence.",
        required_inputs=("runtime_contract", "target_repo_paths", "done_definition"),
    ),
    "release-ops-worker": WorkerDefinition(
        worker_id="release-ops-worker",
        worker_name="Release Operations Worker",
        factory_phase="F16-F17",
        output_field="release_ops_result",
        tool_required="promotion packet, smoke, rollback and monitoring workflow",
        timing="after done gate and before release/promotion",
        blocking_policy="Release cannot proceed with open blocking findings, missing rollback or missing monitoring owner.",
        required_inputs=("done_definition", "rollback_or_recovery", "human_gate_packet"),
    ),
    "handoff-packer": WorkerDefinition(
        worker_id="handoff-packer",
        worker_name="Handoff Packer",
        factory_phase="F9-F15",
        output_field="handoff_packet_result",
        tool_required="path-free handoff workflow with state, constraints, evidence and replay notes",
        timing="at worker transfer, context compaction, pause, phase change or R2+ handoff",
        blocking_policy="Handoff is not a pretty summary; it must preserve constraints, evidence, decisions and next action.",
        required_inputs=("target_repo_paths", "done_definition"),
    ),
    "memory-steward": WorkerDefinition(
        worker_id="memory-steward",
        worker_name="Memory Steward",
        factory_phase="F0/F1/F18",
        output_field="memory_steward_result",
        tool_required="memory trust-tier and poisoning-control review",
        timing="when persistent context, memory, source reuse or learning-loop updates are proposed",
        blocking_policy="Memory cannot become truth without source, freshness, trust tier and poisoning controls.",
        required_inputs=("source_refs", "source_state", "security_contract"),
    ),
    "skill-eval-distiller": WorkerDefinition(
        worker_id="skill-eval-distiller",
        worker_name="Skill Eval Distiller",
        factory_phase="F18",
        output_field="skill_eval_result",
        tool_required="skill compactness, eval and held-out regression workflow",
        timing="after repeated workflow failures or successful repetition",
        blocking_policy="A closed specialist or skill update needs repetition, predictable input and verifiable output.",
        required_inputs=("evidence_expected", "done_definition", "source_refs"),
    ),
    "public-safety-gate": WorkerDefinition(
        worker_id="public-safety-gate",
        worker_name="Public Safety Gate",
        factory_phase="F16/F17",
        output_field="public_safety_result",
        tool_required="public repository redaction and forbidden-term scan",
        timing="before publishing, release, PR or public artifact generation",
        blocking_policy="Public artifacts cannot contain private paths, internal names, raw study extraction or private board links.",
        required_inputs=("target_repo_paths", "forbidden_actions", "done_definition"),
    ),
    "supply-chain-gate": WorkerDefinition(
        worker_id="supply-chain-gate",
        worker_name="Supply Chain Gate",
        factory_phase="F11/F13/F16",
        output_field="supply_chain_result",
        tool_required="dependency, CI, secret, SBOM and provenance checks",
        timing="before ready/done/release for code, dependency, CI or package work",
        blocking_policy="Code and dependency work needs reproducible tests, secret scan and dependency risk checks.",
        required_inputs=("target_repo_paths", "runtime_contract", "security_scan_packet"),
    ),
    "detection-monitoring-worker": WorkerDefinition(
        worker_id="detection-monitoring-worker",
        worker_name="Detection and Monitoring Worker",
        factory_phase="F16-F17",
        output_field="detection_monitoring_result",
        tool_required="logs, metrics, alerting, incident and rollback evidence",
        timing="before production promotion and after release smoke",
        blocking_policy="Stable production requires observability, alerting, incident owner and rollback evidence.",
        required_inputs=("rollback_or_recovery", "security_contract", "done_definition"),
    ),
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json_like(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def write_json(path: Path | None, data: dict[str, Any]) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    if path is None:
        print(text, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {path}")


def source_card_ref(source_path: Path) -> str:
    raw = str(source_path)
    if raw.startswith("<") and raw.endswith(">"):
        label = raw[1:-1].strip().replace("\\", "/")
        if not label or "/" in label or ":" in label:
            return "external:source-card"
        return f"external:{label}"
    raw_normalized = raw.replace("\\", "/")
    windows_path = PureWindowsPath(raw)
    if windows_path.is_absolute() and not source_path.is_absolute():
        return f"external:{windows_path.name or 'source-card'}"
    try:
        resolved = source_path.resolve()
        return resolved.relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        if windows_path.is_absolute() or (len(raw_normalized) >= 2 and raw_normalized[1] == ":"):
            return f"external:{windows_path.name or 'source-card'}"
        return f"external:{source_path.name or 'source-card'}"


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def normalized_surfaces(card: dict[str, Any]) -> set[str]:
    raw = card.get("surfaces", [])
    if not isinstance(raw, list):
        return set()
    return {str(value).strip().lower() for value in raw if str(value).strip()}


def risk(card: dict[str, Any]) -> str:
    return str(card.get("risk_effective", "")).strip().upper()


def validate_card(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = sorted(CARD_REQUIRED - set(data))
    if missing:
        errors.append("missing card fields: " + ", ".join(missing))

    surfaces = normalized_surfaces(data)
    effective_risk = risk(data)
    review = data.get("review", {}) if isinstance(data.get("review"), dict) else {}
    risk_class = str(data.get("risk_class", "")).strip()

    source_state = str(data.get("source_state", "")).strip()
    if source_state and source_state not in ALLOWED_SOURCE_STATES:
        errors.append("source_state must be one of " + ", ".join(sorted(ALLOWED_SOURCE_STATES)))
    if data.get("executor_identity") == data.get("reviewer_identity"):
        errors.append("executor_identity and reviewer_identity must differ")
    if surfaces & PRODUCT_FACE_SURFACES and not isinstance(data.get("product_face_packet"), dict):
        errors.append("product_face_packet required for product-facing surfaces")
    phase = str(data.get("phase", "")).upper()
    if surfaces & PRODUCT_FACE_SURFACES and phase in {"F11", "F16", "F17"}:
        if not isinstance(data.get("product_face_result"), dict) and not str(data.get("product_face_result_ref") or "").strip():
            errors.append("product_face_result or product_face_result_ref required before decomposition/release")
    runtime_contract = data.get("runtime_contract", {}) if isinstance(data.get("runtime_contract"), dict) else {}
    if runtime_contract.get("remote_proof_required") is True:
        required_remote = ["ttl", "cost_owner", "cleanup_plan", "secret_policy", "artifact_policy"]
        missing_remote = [field for field in required_remote if not str(runtime_contract.get(field) or "").strip()]
        if missing_remote:
            errors.append("runtime_contract remote proof missing " + ", ".join(missing_remote))
    if surfaces & ONCHAIN_SURFACES:
        package = data.get("onchain_work_package")
        if not isinstance(package, dict):
            errors.append("onchain_work_package required for onchain surfaces")
        else:
            if not package.get("quasar_source_ref"):
                errors.append("quasar_source_ref required for onchain work")
            if package.get("runtime") and str(package["runtime"]).lower() == "anchor":
                errors.append("Anchor runtime is forbidden for Overkill Solana work; use Quasar")
            elif package.get("quasar_required") is False:
                errors.append("quasar_required=false is not allowed for Overkill Solana work")
    if effective_risk in HIGH_RISK and not isinstance(data.get("security_scan_packet"), dict):
        errors.append("security_scan_packet required for R3/R4 work")
    if effective_risk in HIGH_RISK and not isinstance(data.get("human_gate_packet"), dict):
        errors.append("human_gate_packet required for R3/R4 work")
    if risk_class == "R3-financial-critical" and review.get("CTO_gate_required") is not True:
        errors.append("review.CTO_gate_required=true required for R3-financial-critical work")
    if effective_risk in HIGH_RISK and surfaces & SECURITY_SURFACES:
        if data.get("security_role_separation") is not True and not data.get("security_role_separation_exception"):
            errors.append("security_role_separation=true or security_role_separation_exception required for R3/R4 security-sensitive work")
    if effective_risk == "R4" and not isinstance(data.get("r4_gate"), dict):
        errors.append("r4_gate required for R4 work")
    return errors


def validate_product_face_result(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required_string = ["result", "tool_or_profile", "executed_by", "performance_note", "next_action"]
    missing_string = [field for field in required_string if not str(result.get(field) or "").strip()]
    if missing_string:
        errors.append("product_face_result missing " + ", ".join(missing_string))
    if str(result.get("result") or "").upper() not in {"PASS", "WAIVED"}:
        errors.append("product_face_result result must be PASS or WAIVED")
    for field in ("screenshots", "viewports", "checked_states", "user_journeys_checked", "evidence_refs"):
        if not _non_empty_string_list(result.get(field)):
            errors.append(f"product_face_result {field} must be a non-empty string array")
    for field in ("a11y", "overlap_check"):
        if not isinstance(result.get(field), dict) or not result.get(field):
            errors.append(f"product_face_result {field} must be an object")
    if result.get("blocking_findings") is True and not str(result.get("next_action") or "").strip():
        errors.append("product_face_result blocking findings require next_action")
    return errors


def validate_auditor_result(result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    audit_mode = str(result.get("audit_mode") or "").strip()
    if audit_mode not in {"preflight", "code_audit"}:
        errors.append("auditor_result audit_mode must be preflight or code_audit")
        return errors
    if not _non_empty_string_list(result.get("evidence_refs")):
        errors.append("auditor_result evidence_refs must be a non-empty string array")
    if audit_mode == "preflight":
        if str(result.get("result") or "").upper() == "PASS":
            errors.append("auditor_result preflight must not use PASS; use WAIVED or PENDING with explicit boundary")
        if result.get("preflight_only") is not True:
            errors.append("auditor_result preflight requires preflight_only=true")
        if "code audit" not in str(result.get("findings_summary") or "").lower():
            errors.append("auditor_result preflight summary must state that no code audit is claimed")
        return errors
    required_code_audit_fields = [
        "auditor_head",
        "corpus_files_loaded",
        "checklist_coverage",
        "known_vectors_coverage",
        "instruction_matrix",
        "state_model",
        "findings",
        "waivers",
    ]
    missing = [field for field in required_code_audit_fields if result.get(field) in (None, "", [], {})]
    if missing:
        errors.append("auditor_result code_audit missing " + ", ".join(missing))
    return errors


def product_face_result_required(card: dict[str, Any]) -> bool:
    surfaces = normalized_surfaces(card)
    phase = str(card.get("phase", "")).upper()
    return bool(surfaces & PRODUCT_FACE_SURFACES) and (
        phase in PRODUCT_FACE_RESULT_PHASES or card.get("product_face_result_required") is True
    )


def validate_receipt(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    receipt = data.get("receipt_five")
    if not isinstance(receipt, dict):
        return ["receipt_five object is required"]
    missing = sorted(RECEIPT_REQUIRED - set(receipt))
    if missing:
        errors.append("missing receipt_five fields: " + ", ".join(missing))
    if receipt.get("reviewer_required") is True and not receipt.get("reviewer_result"):
        errors.append("reviewer_result required when reviewer_required=true")
    if not isinstance(data.get("kanban_transition_event"), dict):
        errors.append("kanban_transition_event object is required")
    scan = data.get("security_scan_result")
    if isinstance(scan, dict):
        required = ["scanner_agent", "tool", "result", "findings_summary"]
        missing = [field for field in required if not str(scan.get(field) or "").strip()]
        if missing:
            errors.append("security_scan_result missing " + ", ".join(missing))
        if not _non_empty_string_list(scan.get("scope")):
            errors.append("security_scan_result scope must be a non-empty string array")
        if not _non_empty_string_list(scan.get("evidence_refs")):
            errors.append("security_scan_result evidence_refs must be a non-empty string array")
        security_ref = " ".join(str(scan.get(field) or "") for field in ("scanner_agent", "tool")).lower()
        if "codex-security" not in security_ref and "cybersecurity" not in security_ref:
            errors.append("security_scan_result must reference Codex Security or cybersecurity")
        if str(scan.get("result") or "").upper() not in {"PASS", "WAIVED"}:
            errors.append("security_scan_result result must be PASS or WAIVED")
        if scan.get("blocking_findings") is True and not isinstance(data.get("security_exception"), dict):
            errors.append("security_scan_result blocking findings require security_exception")
    product_face = data.get("product_face_result")
    if isinstance(product_face, dict):
        errors.extend(validate_product_face_result(product_face))
    auditor = data.get("auditor_result")
    if isinstance(auditor, dict):
        errors.extend(validate_auditor_result(auditor))
    if data.get("hermes_legacy_completion_required") is True:
        if not any(_non_empty_string_list(data.get(field)) for field in ("evidence_paths", "evidence", "artifacts")):
            errors.append("Hermes V2 metadata requires evidence_paths, evidence or artifacts")
        verification = data.get("verification")
        if not isinstance(verification, dict) or verification.get("passed") is not True or not _non_empty_string_list(
            verification.get("commands") or verification.get("verify_commands") or verification.get("tests")
        ):
            errors.append("Hermes V2 metadata requires verification.passed=true with commands")
        sandbox = data.get("sandbox")
        if not isinstance(sandbox, dict) or sandbox.get("passed") is not True or not _non_empty_string_list(
            sandbox.get("invariants") or sandbox.get("invariant_results")
        ):
            errors.append("Hermes V2 metadata requires sandbox.passed=true with invariants")
        rollback = data.get("rollback")
        if not isinstance(rollback, dict) or rollback.get("verified") is not True or not str(
            rollback.get("evidence") or rollback.get("evidence_path") or ""
        ).strip():
            errors.append("Hermes V2 metadata requires rollback.verified=true with evidence")
        approvals = data.get("approvals")
        if not isinstance(approvals, dict):
            errors.append("Hermes V2 metadata requires approvals object")
        else:
            missing_approvals: list[str] = []
            for key in V2_APPROVAL_KEYS:
                approval = approvals.get(key)
                if (
                    not isinstance(approval, dict)
                    or approval.get("approved") is not True
                    or not str(approval.get("actor") or approval.get("by") or approval.get("profile") or "").strip()
                    or not str(approval.get("at") or approval.get("timestamp") or approval.get("time") or "").strip()
                ):
                    missing_approvals.append(key)
            if missing_approvals:
                errors.append("Hermes V2 metadata missing approval records: " + ", ".join(missing_approvals))
    return errors


def validate_completion(card: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    errors = validate_receipt(metadata)
    if product_face_result_required(card):
        product_face = metadata.get("product_face_result")
        if not isinstance(product_face, dict):
            errors.append("product_face_result metadata is required for product-facing completion")
        else:
            errors.extend(validate_product_face_result(product_face))
    return errors


def worker_required(worker_id: str, card: dict[str, Any]) -> tuple[bool, str]:
    surfaces = normalized_surfaces(card)
    effective_risk = risk(card)
    phase = str(card.get("phase", "")).upper()
    review = card.get("review", {}) if isinstance(card.get("review"), dict) else {}
    runtime_contract = card.get("runtime_contract", {}) if isinstance(card.get("runtime_contract"), dict) else {}
    security_contract = card.get("security_contract", {}) if isinstance(card.get("security_contract"), dict) else {}

    if worker_id == "codex-security":
        code_security_surfaces = {"code", "ci", "cd", "cicd", "workflow", "supply-chain", "public", "repo-public", "opensource", "open-source"}
        agentic_security_surfaces = {"agent", "agents", "llm", "prompt", "memory", "browser", "tools", "mcp", "autonomous"}
        required = (
            effective_risk in HIGH_RISK
            or bool(surfaces & SECURITY_SURFACES)
            or bool(surfaces & code_security_surfaces)
            or bool(surfaces & agentic_security_surfaces)
        )
        reason = "risk, code, public, agentic or sensitive surface requires security evidence" if required else "no R3/R4, code, public, agentic or sensitive surface detected"
        return required, reason
    if worker_id == "solana-quasar-auditor":
        required = bool(surfaces & ONCHAIN_SURFACES)
        reason = "onchain/Solana/Quasar surface detected" if required else "no onchain surface detected"
        return required, reason
    if worker_id == "product-face":
        required = bool(surfaces & PRODUCT_FACE_SURFACES)
        reason = "visible product surface detected" if required else "no visible product surface detected"
        return required, reason
    if worker_id == "independent-reviewer":
        required = effective_risk in REVIEW_RISK or review.get("independent_review_required") is True
        reason = "R2+ or explicit independent review required" if required else "low-risk card without explicit independent review"
        return required, reason
    if worker_id == "human-gate-clerk":
        required = (
            effective_risk in HIGH_RISK
            or phase in {"F4", "F9", "F15", "F16"}
            or review.get("human_gate_required") is True
            or review.get("CTO_gate_required") is True
        )
        reason = "architecture/high-risk/human gate detected" if required else "no human gate trigger detected"
        return required, reason
    if worker_id == "factory-orchestrator":
        required = bool(phase or surfaces or effective_risk)
        reason = "factory card needs routing and state control" if required else "card lacks enough factory metadata to route"
        return required, reason
    if worker_id == "source-ledger-worker":
        required = phase in {"F0", "F1"} or str(card.get("source_state", "")).lower() in {"raw", "backlog", "compiled"}
        reason = "raw or early source state detected" if required else "source ledger already past early intake"
        return required, reason
    if worker_id == "product-sot-planner":
        required = phase in {"F2", "F3"} or "sot" in surfaces
        reason = "Product SOT phase detected" if required else "not a Product SOT phase"
        return required, reason
    if worker_id == "product-architect":
        required = phase in {"F4", "F5", "F6"} or "architecture" in surfaces
        reason = "architecture/specialist review phase detected" if required else "not an architecture phase"
        return required, reason
    if worker_id == "docs-os-worker":
        required = phase == "F10" or "docs" in surfaces or "documentation" in surfaces
        reason = "Documentation OS phase detected" if required else "documentation OS not required by current card"
        return required, reason
    if worker_id == "decomposition-planner":
        required = phase == "F11" or "decomposition" in surfaces or "kanban-card-graph" in surfaces
        reason = "decomposition/card-graph phase detected" if required else "not a decomposition phase"
        return required, reason
    if worker_id == "implementation-worker":
        required = phase == "F12" or "implementation" in surfaces or "code" in surfaces
        reason = "implementation surface detected" if required else "not an implementation card"
        return required, reason
    if worker_id == "qa-verification-worker":
        required = phase in {"F13", "F14", "F15"} or effective_risk in REVIEW_RISK
        reason = "verification/review risk detected" if required else "low-risk card without verification trigger"
        return required, reason
    if worker_id == "autoreview-gate":
        code_surfaces = {"code", "frontend", "backend", "api", "infra", "onchain", "solana", "solana-quasar"}
        required = phase in {"F14", "F15"} or bool(surfaces & code_surfaces) or review.get("autoreview_required") is True
        reason = "code or pre-landing review surface detected" if required else "no code/pre-landing trigger"
        return required, reason
    if worker_id == "security-orchestrator":
        required = effective_risk in REVIEW_RISK or bool(surfaces & SECURITY_SURFACES)
        reason = "security-sensitive or R2+ card needs routed controls" if required else "no routed security trigger"
        return required, reason
    if worker_id == "appsec-owasp-specialist":
        appsec_surfaces = {"web", "api", "backend", "frontend", "auth", "session", "browser", "wallet-ui"}
        required = bool(surfaces & appsec_surfaces)
        reason = "OWASP Web/API/AppSec surface detected" if required else "no OWASP AppSec surface detected"
        return required, reason
    if worker_id == "agentic-ai-security-specialist":
        agentic_surfaces = {"agent", "agents", "llm", "prompt", "memory", "browser", "tools", "mcp", "autonomous"}
        required = bool(surfaces & agentic_surfaces) or security_contract.get("agentic_ai_security_required") is True
        reason = "agentic AI/tool/memory surface detected" if required else "no agentic AI security trigger"
        return required, reason
    if worker_id == "cloud-infra-security-specialist":
        infra_surfaces = {"cloud", "infra", "iac", "deploy", "ci", "cd", "cicd", "iam", "kms", "dns", "secrets"}
        required = bool(surfaces & infra_surfaces)
        reason = "cloud/infra/IaC/deploy surface detected" if required else "no cloud/infra trigger"
        return required, reason
    if worker_id == "crypto-key-management-specialist":
        crypto_surfaces = {"crypto", "key", "keys", "secrets", "signing", "custody", "funds", "wallet", "kms"}
        required = bool(surfaces & crypto_surfaces)
        reason = "crypto/key/custody surface detected" if required else "no crypto/key trigger"
        return required, reason
    if worker_id == "remote-proof-runner":
        required = effective_risk in HIGH_RISK or runtime_contract.get("remote_proof_required") is True
        reason = "high-risk or explicit remote proof required" if required else "local proof is sufficient by current card"
        return required, reason
    if worker_id == "release-ops-worker":
        release_surfaces = {"release", "production", "deploy", "monitoring", "rollback"}
        required = phase in {"F16", "F17"} or bool(surfaces & release_surfaces)
        reason = "release/promotion surface detected" if required else "not a release/promotion card"
        return required, reason
    if worker_id == "handoff-packer":
        required = phase in {"F9", "F10", "F11", "F12", "F13", "F14", "F15"} or effective_risk in REVIEW_RISK
        reason = "phase or risk requires portable handoff" if required else "handoff not required by current card"
        return required, reason
    if worker_id == "memory-steward":
        memory_surfaces = {"memory", "context", "learning-loop", "source-reuse"}
        required = phase in {"F0", "F1", "F18"} or bool(surfaces & memory_surfaces)
        reason = "memory/source/learning-loop surface detected" if required else "no memory stewardship trigger"
        return required, reason
    if worker_id == "skill-eval-distiller":
        required = phase == "F18" or "skill" in surfaces or "eval" in surfaces
        reason = "skill/eval/learning loop detected" if required else "no skill evolution trigger"
        return required, reason
    if worker_id == "public-safety-gate":
        public_surfaces = {"public", "opensource", "open-source", "repo-public", "release", "docs"}
        required = phase in {"F16", "F17"} or bool(surfaces & public_surfaces)
        reason = "public artifact or release surface detected" if required else "not a public/release artifact"
        return required, reason
    if worker_id == "supply-chain-gate":
        supply_surfaces = {"dependency", "dependencies", "package", "ci", "cd", "cicd", "supply-chain", "workflow"}
        required = bool(surfaces & supply_surfaces) or "code" in surfaces or effective_risk in HIGH_RISK
        reason = "code/dependency/high-risk supply-chain trigger detected" if required else "no supply-chain trigger"
        return required, reason
    if worker_id == "detection-monitoring-worker":
        detection_surfaces = {"logs", "logging", "monitoring", "alerting", "incident", "production", "observability"}
        required = phase in {"F16", "F17"} or bool(surfaces & detection_surfaces)
        reason = "monitoring/incident/release trigger detected" if required else "no detection/monitoring trigger"
        return required, reason
    raise KeyError(worker_id)


def missing_required_inputs(worker: WorkerDefinition, card: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in worker.required_inputs:
        if field in {"security_scan_result", "rollback_plan"}:
            continue
        value = card.get(field)
        if value in (None, "", [], {}):
            missing.append(field)
    return missing


def required_worker_ids(card: dict[str, Any]) -> list[str]:
    return [worker_id for worker_id in WORKERS if worker_required(worker_id, card)[0]]


def build_worker_packet(worker_id: str, card: dict[str, Any], source_path: Path) -> dict[str, Any]:
    worker = WORKERS[worker_id]
    required, reason = worker_required(worker_id, card)
    missing_inputs = missing_required_inputs(worker, card)
    status = "requires_execution" if required else "not_required_by_current_card"
    if required and missing_inputs:
        status = "blocked_missing_inputs"

    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-packet.schema.json",
        "packet_type": "worker_execution_request",
        "created_at": utc_now(),
        "source_card_path": source_card_ref(source_path),
        "worker": {
            "id": worker.worker_id,
            "name": worker.worker_name,
            "factory_phase": worker.factory_phase,
            "tool_required": worker.tool_required,
        },
        "trigger": {
            "required": required,
            "reason": reason,
            "timing": worker.timing,
            "blocking_policy": worker.blocking_policy,
        },
        "card_ref": {
            "card_id": card.get("card_id"),
            "slice_id": card.get("slice_id"),
            "phase": card.get("phase"),
            "risk_effective": card.get("risk_effective"),
            "surfaces": card.get("surfaces", []),
            "executor_identity": card.get("executor_identity"),
            "reviewer_identity": card.get("reviewer_identity"),
        },
        "input_contract": {
            "required_fields": list(worker.required_inputs),
            "missing_fields": missing_inputs,
            "target_repo_paths": card.get("target_repo_paths", []),
            "authority_max": card.get("authority_max"),
            "forbidden_actions": card.get("forbidden_actions", []),
        },
        "output_contract": {
            "receipt_field": worker.output_field,
            "must_attach_artifact_refs": True,
            "must_state_blocking_findings": True,
            "must_record_tool_or_profile": True,
            "human_approval_must_be_real": worker_id == "human-gate-clerk",
        },
        "status": status,
    }


def build_gate_report(card: dict[str, Any]) -> dict[str, Any]:
    validation_errors = validate_card(card)
    worker_rows: dict[str, dict[str, Any]] = {}
    required_workers: list[str] = []
    blocked_workers: list[str] = []
    for worker_id in WORKERS:
        required, reason = worker_required(worker_id, card)
        status = build_worker_packet(worker_id, card, Path("<memory>"))["status"]
        worker_rows[worker_id] = {"required": required, "reason": reason, "status": status}
        if required:
            required_workers.append(worker_id)
        if status == "blocked_missing_inputs":
            blocked_workers.append(worker_id)
    if validation_errors or blocked_workers:
        gate_status = "blocked"
    elif required_workers:
        gate_status = "ready_for_worker_execution"
    else:
        gate_status = "pass_no_workers_required"
    return {
        "$schema": "https://overkill-factory.dev/schemas/gate-report.schema.json",
        "report_type": "factory_gate_preflight",
        "created_at": utc_now(),
        "card_id": card.get("card_id"),
        "risk_effective": card.get("risk_effective"),
        "surfaces": card.get("surfaces", []),
        "gate_status": gate_status,
        "required_workers": required_workers,
        "blocked_workers": blocked_workers,
        "card_validation_errors": validation_errors,
        "workers": worker_rows,
    }


BEFORE_READY_WORKERS = {
    "factory-orchestrator",
    "source-ledger-worker",
    "product-sot-planner",
    "product-architect",
    "docs-os-worker",
    "decomposition-planner",
    "supply-chain-gate",
}

BEFORE_DONE_WORKERS = {
    "codex-security",
    "solana-quasar-auditor",
    "product-face",
    "independent-reviewer",
    "human-gate-clerk",
    "implementation-worker",
    "qa-verification-worker",
    "autoreview-gate",
    "security-orchestrator",
    "appsec-owasp-specialist",
    "agentic-ai-security-specialist",
    "cloud-infra-security-specialist",
    "crypto-key-management-specialist",
    "remote-proof-runner",
    "release-ops-worker",
    "public-safety-gate",
    "detection-monitoring-worker",
}


def worker_queue_class(worker_id: str, card: dict[str, Any]) -> str:
    phase = str(card.get("phase", "")).upper()
    effective_risk = risk(card)
    if worker_id == "human-gate-clerk" and phase in {"F4", "F9"}:
        return "blocking-before-ready"
    if worker_id in BEFORE_READY_WORKERS:
        return "blocking-before-ready"
    if worker_id in BEFORE_DONE_WORKERS:
        return "blocking-before-done"
    if worker_id == "memory-steward" and phase in {"F0", "F1"}:
        return "blocking-before-ready"
    if worker_id == "handoff-packer" and effective_risk in REVIEW_RISK:
        return "blocking-before-done"
    return "advisory-review"


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def _worker_id_for_output_field(output_field: str) -> str | None:
    for worker_id, worker in WORKERS.items():
        if worker.output_field == output_field:
            return worker_id
    return "human-gate-clerk" if output_field == "human_gate_record" else None


def _field_mismatch_errors(data: dict[str, Any], card: dict[str, Any] | None) -> list[str]:
    if card is None:
        return []
    errors: list[str] = []
    card_ref_value = data.get("card_ref")
    card_ref = card_ref_value if isinstance(card_ref_value, dict) else {}
    if data.get("record_type") == "human_gate_record" and data.get("card_id") != card.get("card_id"):
        errors.append("card_id must match current card")
    if card_ref.get("card_id") != card.get("card_id"):
        errors.append("card_ref.card_id must match current card")
    expected_slice = card.get("slice_id")
    if expected_slice and card_ref.get("slice_id") != expected_slice:
        errors.append("card_ref.slice_id must match current card")
    return errors


def _evidence_ref_errors(refs: list[str], evidence_root: Path | None) -> list[str]:
    errors: list[str] = []
    for ref in refs:
        normalized = ref.strip().replace("\\", "/")
        if normalized.startswith(("http://", "https://", "external:", "repo://")):
            continue
        if normalized.startswith("file://") or Path(ref).is_absolute() or ":" in normalized.split("/", 1)[0]:
            errors.append(f"evidence ref must be public-relative or explicit external ref: {ref}")
            continue
        if evidence_root is not None:
            candidate = (evidence_root / normalized).resolve()
            try:
                candidate.relative_to(evidence_root.resolve())
            except ValueError:
                errors.append(f"evidence ref escapes evidence root: {ref}")
                continue
            if not candidate.exists():
                errors.append(f"evidence ref does not exist: {ref}")
    return errors


def _waiver_errors(data: dict[str, Any]) -> list[str]:
    if str(data.get("result") or "").strip() != "WAIVED":
        return []
    waiver = data.get("waiver")
    if not isinstance(waiver, dict):
        return ["WAIVED result requires waiver object"]
    errors: list[str] = []
    for field in ("owner", "reason", "expires_at", "reviewer_or_human_gate_ref"):
        if not str(waiver.get(field) or "").strip():
            errors.append(f"waiver.{field} is required")
    if not string_list(waiver.get("compensating_controls")):
        errors.append("waiver.compensating_controls must contain at least one item")
    if not string_list(waiver.get("evidence_refs")):
        errors.append("waiver.evidence_refs must contain at least one item")
    return errors


def _record_specific_errors(data: dict[str, Any], evidence_kind: str) -> list[str]:
    record_type = str(data.get("record_type") or "").strip()
    errors: list[str] = []
    if record_type == "security_scan_result":
        for field in ("scanner_agent", "tool"):
            if not str(data.get(field) or "").strip():
                errors.append(f"{field} is required for security_scan_result")
        if not string_list(data.get("scope")):
            errors.append("scope must contain at least one item for security_scan_result")
    if record_type == "auditor_result":
        audit_mode = str(data.get("audit_mode") or "").strip()
        if not audit_mode:
            errors.append("audit_mode is required for auditor_result")
        if data.get("preflight_only") is True and data.get("result") == "PASS" and evidence_kind != "synthetic":
            errors.append("preflight_only auditor_result cannot be real PASS")
    if record_type == "product_face_result":
        for field in ("screenshots", "viewports", "checked_states", "journeys", "accessibility", "overlap", "performance_note"):
            if data.get(field) in (None, "", [], {}):
                errors.append(f"{field} is required for product_face_result")
    if record_type == "remote_proof_result":
        for field in ("runtime", "ttl", "cleanup", "artifact_refs"):
            if data.get(field) in (None, "", [], {}):
                errors.append(f"{field} is required for remote_proof_result")
    if record_type == "autoreview_result":
        if data.get("reviewed_diff") in (None, "", [], {}):
            errors.append("reviewed_diff is required for autoreview_result")
    if record_type == "handoff_packet_result":
        if data.get("handoff_packet_ref") in (None, "", [], {}):
            errors.append("handoff_packet_ref is required for handoff_packet_result")
    return errors


def validate_worker_result_record(
    data: dict[str, Any],
    expected_field: str | None = None,
    *,
    expected_worker_id: str | None = None,
    card: dict[str, Any] | None = None,
    evidence_root: Path | None = None,
) -> list[str]:
    errors: list[str] = []
    record_type = str(data.get("record_type") or "").strip()
    if expected_field is not None and record_type != expected_field:
        errors.append(f"record_type must be {expected_field}")
    if not record_type:
        errors.append("record_type is required")

    if record_type == "human_gate_record":
        if data.get("decision") != "approved":
            errors.append("human gate decision must be approved")
        if not str(data.get("human_actor") or "").strip():
            errors.append("human_actor is required")
        for field in ("approved_scope", "forbidden_scope"):
            if not string_list(data.get(field)):
                errors.append(f"{field} must contain at least one item")
        for field in ("risk_owner", "security_owner", "rollback_owner"):
            if not str(data.get(field) or "").strip() or str(data.get(field)).strip().upper() == "TBD":
                errors.append(f"{field} must be explicit")
    else:
        result = str(data.get("result") or "").strip()
        if result not in {"PASS", "WAIVED"}:
            errors.append("result must be PASS or WAIVED to satisfy a required worker")
        if data.get("blocking_findings") is not False:
            errors.append("blocking_findings must be false")
        for field in ("worker", "card_ref", "findings_summary", "tool_or_profile", "executed_by", "next_action"):
            if field not in data:
                errors.append(f"{field} is required")
        worker_ref = data.get("worker") if isinstance(data.get("worker"), dict) else {}
        if expected_worker_id and worker_ref.get("id") != expected_worker_id:
            errors.append(f"worker.id must be {expected_worker_id}")

    evidence_refs = string_list(data.get("evidence_refs"))
    if not evidence_refs:
        errors.append("evidence_refs must contain at least one artifact ref")
    else:
        errors.extend(_evidence_ref_errors(evidence_refs, evidence_root))
    errors.extend(_field_mismatch_errors(data, card))

    evidence_kind = str(data.get("evidence_kind") or "").strip()
    if evidence_kind not in {"real", "synthetic", "waiver"}:
        errors.append("evidence_kind must be real, synthetic or waiver")
    reusable = data.get("reusable_for_product")
    if not isinstance(reusable, bool):
        errors.append("reusable_for_product must be boolean")
    elif evidence_kind == "synthetic" and reusable is not False:
        errors.append("synthetic evidence must set reusable_for_product=false")
    if evidence_kind == "synthetic" and card is not None:
        source_text = " ".join(str(item).lower() for item in card.get("source_refs", []))
        if "synthetic" not in source_text and "validation" not in source_text:
            errors.append("synthetic evidence can only satisfy synthetic/validation cards")
    errors.extend(_waiver_errors(data))
    errors.extend(_record_specific_errors(data, evidence_kind))
    return errors


def collect_worker_result_fields(card: dict[str, Any], results_dir: Path | None) -> dict[str, dict[str, Any]]:
    if results_dir is None or not results_dir.exists():
        return {}
    records: dict[str, dict[str, Any]] = {}
    for path in sorted(results_dir.glob("*.json")):
        try:
            data = load_json_like(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        record_type = str(data.get("record_type") or "").strip()
        if record_type:
            expected_worker_id = _worker_id_for_output_field(record_type)
            errors = validate_worker_result_record(
                data,
                expected_field=record_type,
                expected_worker_id=expected_worker_id,
                card=card,
                evidence_root=ROOT,
            )
            records[record_type] = {
                "evidence_ref": source_card_ref(path),
                "result": data.get("result") or data.get("decision"),
                "valid": not errors,
                "validation_errors": errors,
            }
    return records


def receipt_result_fields(card: dict[str, Any], metadata: dict[str, Any]) -> dict[str, dict[str, Any]]:
    fields: dict[str, dict[str, Any]] = {}
    for worker_id, worker in WORKERS.items():
        value = metadata.get(worker.output_field)
        if isinstance(value, dict):
            errors = validate_worker_result_record(
                value,
                expected_field=worker.output_field,
                expected_worker_id=worker_id,
                card=card,
            )
            fields[worker.output_field] = {
                "evidence_ref": None,
                "result": value.get("result") or value.get("decision"),
                "valid": not errors,
                "validation_errors": errors,
            }
    return fields


def build_worker_task(worker_id: str, card: dict[str, Any], source_path: Path) -> dict[str, Any]:
    worker = WORKERS[worker_id]
    packet = build_worker_packet(worker_id, card, source_path)
    queue_class = worker_queue_class(worker_id, card)
    return {
        "task_type": "worker_subtask",
        "worker_id": worker_id,
        "title": f"{worker.worker_name}: {card.get('card_id') or 'factory-card'}",
        "queue_class": queue_class,
        "required_before": "ready" if queue_class == "blocking-before-ready" else "done",
        "packet": packet,
        "expected_receipt_field": worker.output_field,
        "status": packet["status"],
    }


def build_worker_closure(
    card: dict[str, Any],
    metadata: dict[str, Any] | None,
    results_dir: Path | None,
) -> dict[str, Any]:
    metadata = metadata or {}
    present_fields = receipt_result_fields(card, metadata)
    result_files = collect_worker_result_fields(card, results_dir)
    present_fields.update(result_files)
    rows: dict[str, dict[str, Any]] = {}
    missing_blocking: list[str] = []
    invalid_blocking: list[str] = []

    for worker_id in required_worker_ids(card):
        worker = WORKERS[worker_id]
        queue_class = worker_queue_class(worker_id, card)
        required_for_done = queue_class == "blocking-before-done"
        record = present_fields.get(worker.output_field)
        satisfied = bool(record and record.get("valid"))
        rows[worker_id] = {
            "queue_class": queue_class,
            "required_for_done": required_for_done,
            "output_field": worker.output_field,
            "satisfied": satisfied,
            "evidence_ref": record.get("evidence_ref") if record else None,
            "result": record.get("result") if record else None,
            "validation_errors": record.get("validation_errors", []) if record else [],
        }
        if required_for_done and not satisfied:
            if record:
                invalid_blocking.append(worker_id)
            else:
                missing_blocking.append(worker_id)

    return {
        "closure_type": "worker_result_reconciliation",
        "required_workers": required_worker_ids(card),
        "missing_blocking_workers": missing_blocking,
        "invalid_blocking_workers": invalid_blocking,
        "workers": rows,
    }


def build_transition_plan(
    card: dict[str, Any],
    source_path: Path,
    *,
    from_status: str,
    to_status: str,
    receipt: dict[str, Any] | None = None,
    worker_results_dir: Path | None = None,
) -> dict[str, Any]:
    gate = build_gate_report(card)
    normalized_to = to_status.strip().lower()
    blocked_reasons: list[str] = []
    worker_tasks = [
        build_worker_task(worker_id, card, source_path)
        for worker_id in gate["required_workers"]
        if gate["workers"][worker_id]["status"] != "not_required_by_current_card"
    ]

    if normalized_to in {"ready", "in_progress", "doing"}:
        blocked_reasons.extend(gate["card_validation_errors"])
        for worker_id in gate["blocked_workers"]:
            queue_class = worker_queue_class(worker_id, card)
            blocked_reasons.append(f"{worker_id} missing inputs for {queue_class}")
        before_ready = [
            task["worker_id"]
            for task in worker_tasks
            if task["queue_class"] == "blocking-before-ready"
        ]
        for worker_id in before_ready:
            blocked_reasons.append(f"{worker_id} result is required before ready")
        if blocked_reasons and before_ready:
            transition_action = "block_and_create_before_ready_tasks"
        else:
            transition_action = "block_transition" if blocked_reasons else "allow_and_create_worker_tasks"
        completion = None
    elif normalized_to in {"done", "closed", "complete"}:
        blocked_reasons.extend(gate["card_validation_errors"])
        for worker_id in gate["blocked_workers"]:
            blocked_reasons.append(f"{worker_id} missing inputs before done")
        if receipt is None:
            blocked_reasons.append("receipt metadata is required for done transition")
            completion = build_worker_closure(card, {}, worker_results_dir)
        else:
            blocked_reasons.extend(validate_completion(card, receipt))
            completion = build_worker_closure(card, receipt, worker_results_dir)
            for worker_id in completion["missing_blocking_workers"]:
                blocked_reasons.append(f"{worker_id} result is required before done")
            for worker_id in completion.get("invalid_blocking_workers", []):
                blocked_reasons.append(f"{worker_id} result is invalid before done")
        transition_action = "block_transition" if blocked_reasons else "allow_done"
    else:
        blocked_reasons.extend(gate["card_validation_errors"])
        transition_action = "block_transition" if blocked_reasons else "allow"
        completion = None

    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-transition-plan.schema.json",
        "plan_type": "hermes_kanban_transition_plan",
        "created_at": utc_now(),
        "source_card_path": source_card_ref(source_path),
        "event": {
            "from_status": from_status,
            "to_status": to_status,
            "card_id": card.get("card_id"),
        },
        "transition_action": transition_action,
        "blocked_reasons": blocked_reasons,
        "gate_report": gate,
        "worker_tasks": worker_tasks,
        "completion_reconciliation": completion,
    }


def card_ref(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "card_id": card.get("card_id"),
        "slice_id": card.get("slice_id"),
        "phase": card.get("phase"),
        "risk_effective": card.get("risk_effective"),
        "surfaces": card.get("surfaces", []),
        "executor_identity": card.get("executor_identity"),
        "reviewer_identity": card.get("reviewer_identity"),
    }


def build_worker_result(
    worker_id: str,
    card: dict[str, Any],
    *,
    result: str,
    tool_or_profile: str,
    executed_by: str,
    evidence_refs: list[str],
    blocking_findings: bool,
    findings_summary: str,
    next_action: str,
    evidence_kind: str = "real",
    reusable_for_product: bool = True,
) -> dict[str, Any]:
    if worker_id == "human-gate-clerk":
        raise ValueError("use human-gate-record for human decisions")
    if result in {"PASS", "WAIVED"} and not evidence_refs:
        raise ValueError("PASS/WAIVED worker results require at least one evidence ref")
    if result == "PASS" and blocking_findings:
        raise ValueError("PASS cannot have blocking_findings=true")

    worker = WORKERS[worker_id]
    payload = {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": worker.output_field,
        "created_at": utc_now(),
        "worker": {
            "id": worker.worker_id,
            "name": worker.worker_name,
            "factory_phase": worker.factory_phase,
        },
        "card_ref": card_ref(card),
        "result": result,
        "blocking_findings": blocking_findings,
        "findings_summary": findings_summary,
        "tool_or_profile": tool_or_profile,
        "executed_by": executed_by,
        "evidence_refs": evidence_refs,
        "evidence_kind": evidence_kind,
        "reusable_for_product": reusable_for_product,
        "next_action": next_action,
    }
    if worker_id == "codex-security":
        scan_packet = card.get("security_scan_packet", {}) if isinstance(card.get("security_scan_packet"), dict) else {}
        scope = scan_packet.get("scan_scope") or card.get("surfaces", [])
        if isinstance(scope, str):
            scope = [scope]
        payload.update(
            {
                "scanner_agent": scan_packet.get("scanner_agent") or executed_by,
                "tool": tool_or_profile,
                "scope": [str(item) for item in scope if str(item).strip()],
            }
        )
    if worker_id == "solana-quasar-auditor":
        payload.update(
            {
                "audit_mode": "synthetic-smoke" if evidence_kind == "synthetic" else "code-audit",
                "preflight_only": evidence_kind == "synthetic",
            }
        )
    if worker_id == "product-face":
        payload.update(
            {
                "screenshots": evidence_refs,
                "viewports": ["synthetic-desktop", "synthetic-mobile"] if evidence_kind == "synthetic" else [],
                "checked_states": ["default", "empty", "loading", "error", "success"],
                "journeys": ["open target", "inspect states"],
                "accessibility": {"checked": True, "mode": evidence_kind},
                "overlap": {"checked": True, "mode": evidence_kind},
                "performance_note": "Synthetic smoke only." if evidence_kind == "synthetic" else "See Product Face report.",
            }
        )
    if worker_id == "remote-proof-runner":
        payload.update(
            {
                "runtime": "synthetic-smoke" if evidence_kind == "synthetic" else "remote-proof",
                "ttl": "synthetic",
                "cleanup": {"status": "not_applicable" if evidence_kind == "synthetic" else "required"},
                "artifact_refs": evidence_refs,
            }
        )
    if worker_id == "autoreview-gate":
        payload["reviewed_diff"] = "synthetic-smoke" if evidence_kind == "synthetic" else "attached-diff"
    if worker_id == "handoff-packer":
        payload["handoff_packet_ref"] = evidence_refs[0] if evidence_refs else "external:missing"
    return payload


def infer_gate_type(card: dict[str, Any]) -> str:
    effective_risk = risk(card)
    phase = str(card.get("phase", "")).upper()
    if effective_risk == "R4":
        return "R4"
    if effective_risk == "R3":
        return "R3"
    if phase in {"F4", "F9"}:
        return "architecture"
    return "promotion"


def build_human_gate_record(
    card: dict[str, Any],
    *,
    gate_type: str | None,
    decision: str,
    human_actor: str,
    approved_scope: list[str],
    forbidden_scope: list[str],
    required_changes: list[str],
    risk_owner: str | None,
    security_owner: str | None,
    rollback_owner: str | None,
    evidence_refs: list[str],
    notes: str,
    evidence_kind: str = "real",
    reusable_for_product: bool = True,
) -> dict[str, Any]:
    if decision == "approved" and not evidence_refs:
        raise ValueError("approved human gates require at least one evidence ref")

    packet = card.get("human_gate_packet", {}) if isinstance(card.get("human_gate_packet"), dict) else {}
    r4_gate = card.get("r4_gate", {}) if isinstance(card.get("r4_gate"), dict) else {}
    scan_packet = card.get("security_scan_packet", {}) if isinstance(card.get("security_scan_packet"), dict) else {}

    return {
        "$schema": "https://overkill-factory.dev/schemas/human-gate-record.schema.json",
        "record_type": "human_gate_record",
        "gate_type": gate_type or infer_gate_type(card),
        "card_id": card.get("card_id"),
        "card_ref": card_ref(card),
        "decision": decision,
        "human_actor": human_actor,
        "decision_at": utc_now(),
        "approved_scope": approved_scope,
        "forbidden_scope": forbidden_scope or card.get("forbidden_actions", []),
        "required_changes": required_changes,
        "risk_owner": risk_owner or packet.get("risk_owner") or r4_gate.get("risk_owner") or "TBD",
        "security_owner": (
            security_owner
            or packet.get("security_owner")
            or r4_gate.get("security_owner")
            or scan_packet.get("security_owner")
            or "TBD"
        ),
        "rollback_owner": rollback_owner or packet.get("rollback_owner") or r4_gate.get("rollback_owner") or "TBD",
        "evidence_refs": evidence_refs,
        "evidence_kind": evidence_kind,
        "reusable_for_product": reusable_for_product,
        "notes": notes,
    }


def command_validate_card(args: argparse.Namespace) -> int:
    errors = validate_card(load_json_like(args.path))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


def command_validate_receipt(args: argparse.Namespace) -> int:
    errors = validate_receipt(load_json_like(args.path))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


def command_validate_completion(args: argparse.Namespace) -> int:
    errors = validate_completion(load_json_like(args.card), load_json_like(args.receipt))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


def command_worker_packet(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    if args.required_only and args.worker != "all":
        raise SystemExit("--required-only can only be used with --worker all")
    if args.worker == "all":
        output_dir = args.out
        if output_dir is None:
            raise SystemExit("--out directory is required when --worker all")
        output_dir.mkdir(parents=True, exist_ok=True)
        worker_ids = required_worker_ids(card) if args.required_only else list(WORKERS)
        for worker_id in worker_ids:
            packet = build_worker_packet(worker_id, card, args.card)
            write_json(output_dir / f"{worker_id}-request.json", packet)
        return 0
    packet = build_worker_packet(args.worker, card, args.card)
    write_json(args.out, packet)
    return 0


def command_gate_report(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    write_json(args.out, build_gate_report(card))
    return 0


def command_evidence_record(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    try:
        record = build_worker_result(
            args.worker,
            card,
            result=args.result,
            tool_or_profile=args.tool,
            executed_by=args.actor,
            evidence_refs=args.evidence_ref or [],
            blocking_findings=args.blocking_findings,
            findings_summary=args.summary,
            next_action=args.next_action,
            evidence_kind=args.evidence_kind,
            reusable_for_product=not args.not_reusable_for_product,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    write_json(args.out, record)
    return 0


def command_human_gate_record(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    try:
        record = build_human_gate_record(
            card,
            gate_type=args.gate_type,
            decision=args.decision,
            human_actor=args.human_actor,
            approved_scope=args.approved_scope or [],
            forbidden_scope=args.forbidden_scope or [],
            required_changes=args.required_change or [],
            risk_owner=args.risk_owner,
            security_owner=args.security_owner,
            rollback_owner=args.rollback_owner,
            evidence_refs=args.evidence_ref or [],
            notes=args.notes,
            evidence_kind=args.evidence_kind,
            reusable_for_product=not args.not_reusable_for_product,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    write_json(args.out, record)
    return 0


def command_transition_plan(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    receipt = load_json_like(args.receipt) if args.receipt else None
    plan = build_transition_plan(
        card,
        args.card,
        from_status=args.from_status,
        to_status=args.to_status,
        receipt=receipt,
        worker_results_dir=args.worker_results_dir,
    )
    write_json(args.out, plan)
    return 1 if plan["transition_action"] == "block_transition" and args.enforce else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Overkill Factory control helper")
    sub = parser.add_subparsers(dest="command", required=True)

    validate_card_parser = sub.add_parser("validate-card")
    validate_card_parser.add_argument("path", type=Path)
    validate_card_parser.set_defaults(func=command_validate_card)

    validate_receipt_parser = sub.add_parser("validate-receipt")
    validate_receipt_parser.add_argument("path", type=Path)
    validate_receipt_parser.set_defaults(func=command_validate_receipt)

    validate_completion_parser = sub.add_parser("validate-completion")
    validate_completion_parser.add_argument("--card", type=Path, required=True)
    validate_completion_parser.add_argument("--receipt", type=Path, required=True)
    validate_completion_parser.set_defaults(func=command_validate_completion)

    worker_packet_parser = sub.add_parser("worker-packet")
    worker_packet_parser.add_argument("--worker", choices=[*WORKERS.keys(), "all"], required=True)
    worker_packet_parser.add_argument("--card", type=Path, required=True)
    worker_packet_parser.add_argument("--out", type=Path)
    worker_packet_parser.add_argument("--required-only", action="store_true")
    worker_packet_parser.set_defaults(func=command_worker_packet)

    gate_report_parser = sub.add_parser("gate-report")
    gate_report_parser.add_argument("--card", type=Path, required=True)
    gate_report_parser.add_argument("--out", type=Path)
    gate_report_parser.set_defaults(func=command_gate_report)

    evidence_record_parser = sub.add_parser("evidence-record")
    evidence_record_parser.add_argument(
        "--worker",
        choices=[worker_id for worker_id in WORKERS if worker_id != "human-gate-clerk"],
        required=True,
    )
    evidence_record_parser.add_argument("--card", type=Path, required=True)
    evidence_record_parser.add_argument("--result", choices=["PASS", "FAIL", "WAIVED", "PENDING"], required=True)
    evidence_record_parser.add_argument("--tool", required=True)
    evidence_record_parser.add_argument("--actor", required=True)
    evidence_record_parser.add_argument("--evidence-ref", action="append")
    evidence_record_parser.add_argument("--blocking-findings", action="store_true")
    evidence_record_parser.add_argument("--summary", default="")
    evidence_record_parser.add_argument("--next-action", default="")
    evidence_record_parser.add_argument("--evidence-kind", choices=["real", "synthetic", "waiver"], default="real")
    evidence_record_parser.add_argument("--not-reusable-for-product", action="store_true")
    evidence_record_parser.add_argument("--out", type=Path)
    evidence_record_parser.set_defaults(func=command_evidence_record)

    human_gate_record_parser = sub.add_parser("human-gate-record")
    human_gate_record_parser.add_argument("--card", type=Path, required=True)
    human_gate_record_parser.add_argument("--gate-type", choices=["architecture", "R3", "R4", "promotion"])
    human_gate_record_parser.add_argument("--decision", choices=["approved", "rejected", "changes_requested"], required=True)
    human_gate_record_parser.add_argument("--human-actor", required=True)
    human_gate_record_parser.add_argument("--approved-scope", action="append")
    human_gate_record_parser.add_argument("--forbidden-scope", action="append")
    human_gate_record_parser.add_argument("--required-change", action="append")
    human_gate_record_parser.add_argument("--risk-owner")
    human_gate_record_parser.add_argument("--security-owner")
    human_gate_record_parser.add_argument("--rollback-owner")
    human_gate_record_parser.add_argument("--evidence-ref", action="append")
    human_gate_record_parser.add_argument("--notes", default="")
    human_gate_record_parser.add_argument("--evidence-kind", choices=["real", "synthetic", "waiver"], default="real")
    human_gate_record_parser.add_argument("--not-reusable-for-product", action="store_true")
    human_gate_record_parser.add_argument("--out", type=Path)
    human_gate_record_parser.set_defaults(func=command_human_gate_record)

    transition_plan_parser = sub.add_parser("transition-plan")
    transition_plan_parser.add_argument("--card", type=Path, required=True)
    transition_plan_parser.add_argument("--from-status", required=True)
    transition_plan_parser.add_argument("--to-status", required=True)
    transition_plan_parser.add_argument("--receipt", type=Path)
    transition_plan_parser.add_argument("--worker-results-dir", type=Path)
    transition_plan_parser.add_argument("--enforce", action="store_true")
    transition_plan_parser.add_argument("--out", type=Path)
    transition_plan_parser.set_defaults(func=command_transition_plan)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
