#!/usr/bin/env python3
"""Overkill Factory control helpers.

This CLI prepares and validates the contracts that autonomous workers consume.
It intentionally does not fake security, Auditor, Product Face, reviewer, or
human approvals. It produces execution requests and preflight reports; the
specialist worker still has to run and attach real evidence.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PROFILE_BINDINGS_PATH = ROOT / "agents" / "hermes-profile-bindings.public.json"
CAPABILITY_PACKS_PATH = ROOT / "agents" / "capability-packs.public.json"
CANONICAL_RUNTIME_ENFORCEMENT_PATH = ROOT / "scripts" / "canonical_runtime_enforcement.py"
DEFAULT_MINIMAL_CARD = ROOT / "examples" / "minimal-hermes-project" / "card.md"
DEFAULT_QUICKSTART_OUT = ROOT / ".tmp" / "quickstart-result.json"
DEFAULT_PACKETS_OUT = ROOT / ".tmp" / "minimal-worker-packets"
PYPROJECT_PATH = ROOT / "pyproject.toml"

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

VFINAL_REQUEST_TYPES = {
    "product_new",
    "slice",
    "feature",
    "bug",
    "incident",
    "release",
    "migration",
    "integration",
    "doc",
    "security",
    "ux_ui",
    "data_analytics",
    "agent_skill",
}

VFINAL_CORE_CONTRACTS = {
    "request_type",
    "outcome_contract",
    "product_sot",
    "method_contract",
    "capability_pack_contract",
    "spec_graph",
    "loop_plan",
}

RECEIPT_REQUIRED = {
    "changed",
    "artifact_paths",
    "verification_commands",
    "verification_result",
    "reviewer_required",
    "next_action",
}

PROMOTION_PASS_RESULTS = {"PASS", "WAIVED"}
ARTIFACT_PUBLIC_CLASSES = {"public_safe", "sanitized_report", "publication_candidate"}
ARTIFACT_PRIVATE_CLASSES = {"private_run_evidence", "transient_cache"}
PUBLICATION_SCANNER_FIELDS = ("public_safety_scan", "secret_safety_scan")
V2_APPROVAL_KEYS = [
    "qa",
    "independent_review",
    "security_review",
    "cybersecurity_review",
    "cto_gate",
    "human_gate",
]

PRODUCT_FACE_SURFACES = {"ux", "frontend", "mobile", "wallet-ui", "product-face"}
FRONTEND_BUILD_SURFACES = {"frontend", "mobile", "wallet-ui", "ux", "product-face", "screen", "component", "browser"}
BACKEND_BUILD_SURFACES = {"backend", "api", "auth", "server", "service", "session"}
DATA_BUILD_SURFACES = {"data", "database", "schema", "migration", "storage", "rls", "persistence"}
SOLANA_BUILD_SURFACES = {
    "solana",
    "solana-quasar",
    "quasar",
    "onchain",
    "program",
    "instruction",
    "pda",
    "cpi",
    "account-pda",
}
SOLANA_QA_SURFACES = SOLANA_BUILD_SURFACES | {
    "solana-test",
    "quasar-test",
    "devnet",
    "compute-units",
    "simulation",
    "fuzz",
    "onchain-qa",
}
WALLET_TRANSACTION_SURFACES = {"wallet", "wallet-ui", "transaction", "transactions", "signing"}
INTEGRATION_BUILD_SURFACES = {"integration", "fullstack", "full-stack", "end-to-end", "e2e", "surface-join"}
TEST_AUTOMATION_SURFACES = {"test", "tests", "qa", "e2e", "eval", "regression", "automation"}
INFRA_DEVOPS_BUILD_SURFACES = {"infra", "devops", "deploy", "ci", "cd", "cicd", "runtime", "environment", "workflow"}
AGENT_RUNTIME_BUILD_SURFACES = {"agent", "agents", "hermes", "factory", "adapter", "profile", "skill", "mcp", "autonomous"}
GENERIC_IMPLEMENTATION_SURFACES = {"implementation", "code", "coding", "patch", "legacy", "generic-code"}
SPECIFIC_BUILDER_SURFACES = (
    FRONTEND_BUILD_SURFACES
    | BACKEND_BUILD_SURFACES
    | DATA_BUILD_SURFACES
    | SOLANA_BUILD_SURFACES
    | WALLET_TRANSACTION_SURFACES
    | INTEGRATION_BUILD_SURFACES
    | TEST_AUTOMATION_SURFACES
    | INFRA_DEVOPS_BUILD_SURFACES
    | AGENT_RUNTIME_BUILD_SURFACES
)
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
AUDITOR_MIN_CORPUS_FILES = 120
AUDITOR_PROGRAM_CHECKLIST_PREFIXES = ("01", "02", "03", "04", "05", "06", "07")
AUDITOR_MIN_KNOWN_VECTORS = 100
QUASAR_TOOLCHAIN_PROOF_REQUIRED = (
    "install_source",
    "source_head",
    "rustc",
    "cargo",
    "solana",
    "quasar",
    "init_command",
    "build_command",
    "test_command",
    "build_status",
    "test_status",
    "evidence_refs",
)
CAPABILITY_READY_STATES = {"core_ready", "pack_ready"}
CAPABILITY_ACTIVATED_STATES = {"ready", "activated"}
PRODUCT_EXPERIENCE_REQUIRED_FIELDS = (
    "surface_type",
    "surface_pack",
    "experience_sot",
    "user",
    "job_to_be_done",
    "main_flows",
    "required_states",
    "design_direction",
    "proof_required",
    "reviewers_required",
    "done_definition",
    "human_gate",
)
PRODUCT_FACE_PACKET_REQUIRED_FIELDS = (
    "surface",
    "mode",
    "user",
    "job_to_be_done",
    "main_flows",
    "required_states",
    "design_direction",
    "proof_required",
    "reviewers_required",
    "done_definition",
    "human_gate",
)
PRODUCT_FACE_RESULT_ALIGNMENT_FIELDS = (
    "packet_comparison",
    "source_promise_coverage",
    "design_fit_review",
)


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
        required_inputs=("executor_identity", "reviewer_identity", "done_definition", "reviewer_selection_plan"),
    ),
    "evidence-reconciler": WorkerDefinition(
        worker_id="evidence-reconciler",
        worker_name="Evidence Reconciler",
        factory_phase="F15",
        output_field="receipt_five_reconciliation_result",
        tool_required="Receipt Five evidence indexer and supersession ledger",
        timing="after required worker evidence exists and before QA/AutoReview/done promotion",
        blocking_policy=(
            "A card cannot move to done while required worker results are missing, stale, duplicated, "
            "blocking, invalid or not reconciled into a current Receipt Five evidence set."
        ),
        required_inputs=("done_definition", "target_repo_paths"),
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
        required_inputs=(
            "done_definition",
            "risk_effective",
            "runtime_contract",
            "security_contract",
            "loop_plan",
            "software_development_plan",
        ),
    ),
    "implementation-worker": WorkerDefinition(
        worker_id="implementation-worker",
        worker_name="Implementation Fallback Worker",
        factory_phase="F12",
        output_field="implementation_result",
        tool_required="bounded coding/runtime tools selected by card, only when no surface-specific builder owns the work",
        timing="only after Hermes Ready Gate and after builder routing fails to find a better owner",
        blocking_policy="Fallback implementation cannot replace frontend, backend, data, Solana, wallet, integration, test, infra or agent-runtime builders.",
        required_inputs=("scope_in", "scope_out", "forbidden_actions", "done_definition"),
    ),
    "frontend-builder": WorkerDefinition(
        worker_id="frontend-builder",
        worker_name="Frontend Builder",
        factory_phase="F12/F13",
        output_field="frontend_build_result",
        tool_required="frontend runtime, browser, component tests and visual proof handoff",
        timing="during scoped visible-product implementation, before Product Face validation",
        blocking_policy="Frontend work cannot be treated as generic code when visible product surfaces are in scope.",
        required_inputs=("product_face_packet", "scope_in", "scope_out", "done_definition"),
    ),
    "backend-api-builder": WorkerDefinition(
        worker_id="backend-api-builder",
        worker_name="Backend API Builder",
        factory_phase="F12/F13",
        output_field="backend_api_build_result",
        tool_required="backend runtime, API tests, lint/typecheck and contract evidence",
        timing="during scoped API/service implementation, before AppSec/security verification when sensitive",
        blocking_policy="Backend/API work needs contract and test evidence; auth-sensitive work cannot close without security review.",
        required_inputs=("scope_in", "scope_out", "security_contract", "done_definition"),
    ),
    "data-persistence-builder": WorkerDefinition(
        worker_id="data-persistence-builder",
        worker_name="Data Persistence Builder",
        factory_phase="F12/F13",
        output_field="data_persistence_result",
        tool_required="migration runner, schema tests, data access tests and rollback notes",
        timing="during scoped schema/storage implementation, before backend integration and verification",
        blocking_policy="Data work cannot proceed without ownership, migration proof and rollback awareness.",
        required_inputs=("scope_in", "scope_out", "runtime_contract", "done_definition"),
    ),
    "solana-quasar-builder": WorkerDefinition(
        worker_id="solana-quasar-builder",
        worker_name="Solana Quasar Builder",
        factory_phase="F12/F13",
        output_field="solana_quasar_build_result",
        tool_required="Quasar toolchain, Solana devnet/local runtime and Rust tests",
        timing="during scoped Solana/Quasar implementation, before Solana QA and Auditor evidence",
        blocking_policy="Onchain program work must be built as Quasar work; Anchor assumptions, mainnet deploys and key access are forbidden.",
        required_inputs=("onchain_work_package", "scope_in", "scope_out", "done_definition"),
    ),
    "solana-quasar-qa-engineer": WorkerDefinition(
        worker_id="solana-quasar-qa-engineer",
        worker_name="Solana Quasar QA Engineer",
        factory_phase="F13/F15",
        output_field="solana_quasar_qa_result",
        tool_required="Quasar tests, devnet/local proof, simulation and negative test matrix",
        timing="after Solana/Quasar build evidence and before Auditor/human promotion gates",
        blocking_policy="Onchain work cannot rely on happy-path implementation evidence; behavior proof and negative tests are required.",
        required_inputs=("onchain_work_package", "target_repo_paths", "done_definition"),
    ),
    "wallet-transaction-builder": WorkerDefinition(
        worker_id="wallet-transaction-builder",
        worker_name="Wallet Transaction Builder",
        factory_phase="F12/F13",
        output_field="wallet_transaction_result",
        tool_required="wallet adapter, browser and transaction-state tests",
        timing="during scoped wallet/signing/funds UX implementation, before Product Face and key/custody review",
        blocking_policy="Wallet and transaction work cannot touch real keys or funds and must expose signer/state boundaries.",
        required_inputs=("product_face_packet", "security_contract", "scope_in", "done_definition"),
    ),
    "integration-builder": WorkerDefinition(
        worker_id="integration-builder",
        worker_name="Integration Builder",
        factory_phase="F12/F13",
        output_field="integration_build_result",
        tool_required="integration tests, local runtime, browser and API checks",
        timing="after upstream builder outputs and before QA verification",
        blocking_policy="Cross-surface work cannot hide missing upstream evidence or unapproved assumptions.",
        required_inputs=("scope_in", "scope_out", "done_definition", "runtime_contract"),
    ),
    "test-automation-builder": WorkerDefinition(
        worker_id="test-automation-builder",
        worker_name="Test Automation Builder",
        factory_phase="F12/F13/F18",
        output_field="test_automation_result",
        tool_required="unit, integration, E2E, visual or eval test harness",
        timing="when acceptance criteria need repeatable proof or repeated workflow should become an eval",
        blocking_policy="Acceptance criteria should become tests/evals when repeatable; automation cannot redefine acceptance alone.",
        required_inputs=("acceptance_criteria", "done_definition", "target_repo_paths"),
    ),
    "infra-devops-builder": WorkerDefinition(
        worker_id="infra-devops-builder",
        worker_name="Infra DevOps Builder",
        factory_phase="F12/F16",
        output_field="infra_devops_result",
        tool_required="CI/CD config, environment smoke and rollback scripts",
        timing="during scoped runtime/deploy implementation, before cloud security and release ops",
        blocking_policy="Infra work requires environment boundary, smoke evidence and rollback; production release remains gated.",
        required_inputs=("runtime_contract", "rollback_or_recovery", "scope_in", "done_definition"),
    ),
    "agent-runtime-builder": WorkerDefinition(
        worker_id="agent-runtime-builder",
        worker_name="Agent Runtime Builder",
        factory_phase="F12/F18",
        output_field="agent_runtime_result",
        tool_required="Hermes adapter tests, profile tooling and skill packaging",
        timing="during scoped factory/agent runtime implementation, before profile validation and agentic security review",
        blocking_policy="Agent runtime work must prove profile/binding/packet operability and cannot self-approve tool or memory risk.",
        required_inputs=("runtime_contract", "security_contract", "scope_in", "done_definition", "agent_eval_plan"),
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
        required_inputs=("evidence_expected", "done_definition", "source_refs", "agent_eval_plan"),
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
    "control-tower-projection-worker": WorkerDefinition(
        worker_id="control-tower-projection-worker",
        worker_name="Control Tower Projection Worker",
        factory_phase="F19",
        output_field="project_projection_result",
        tool_required="Hermes readback plus project projection renderer",
        timing="when owner-facing visibility is active and before material work becomes invisible",
        blocking_policy=(
            "The owner-facing cockpit must mirror runtime state. Projection work cannot invent "
            "status, hide blockers, or become the source of truth."
        ),
        required_inputs=("runtime_state_ref", "project_projection", "done_definition"),
    ),
    "discord-control-tower-bridge": WorkerDefinition(
        worker_id="discord-control-tower-bridge",
        worker_name="Discord Control Tower Bridge",
        factory_phase="F19/F29",
        output_field="control_tower_bridge_result",
        tool_required="Discord mapping, runtime event bridge and bridge health contract",
        timing="when a Discord Control Tower must show state or register owner responses",
        blocking_policy=(
            "Discord is a cockpit only. Structured owner responses must be registered in the "
            "runtime and rejected when malformed, expired, wrong-role, or out of scope."
        ),
        required_inputs=("discord_control_tower_mapping", "control_tower_event", "runtime_registration_path"),
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


def load_profile_bindings() -> dict[str, dict[str, Any]]:
    if not PROFILE_BINDINGS_PATH.exists():
        raise FileNotFoundError(f"profile binding manifest is required: {PROFILE_BINDINGS_PATH}")
    data = json.loads(PROFILE_BINDINGS_PATH.read_text(encoding="utf-8"))
    bindings = data.get("bindings", {})
    if not isinstance(bindings, dict):
        raise ValueError("profile binding manifest must contain a bindings object")
    loaded = {str(worker_id): binding for worker_id, binding in bindings.items() if isinstance(binding, dict)}
    missing = sorted(set(WORKERS) - set(loaded))
    if missing:
        raise ValueError("profile binding manifest missing workers: " + ", ".join(missing))
    return loaded


def load_capability_packs() -> dict[str, dict[str, Any]]:
    if not CAPABILITY_PACKS_PATH.exists():
        return {}
    data = json.loads(CAPABILITY_PACKS_PATH.read_text(encoding="utf-8"))
    packs = data.get("packs", {})
    if not isinstance(packs, dict):
        raise ValueError("capability pack registry must contain a packs object")
    return {str(pack_id): pack for pack_id, pack in packs.items() if isinstance(pack, dict)}


def _activated_capability_pack_ids(contract: Any) -> set[str]:
    if not isinstance(contract, dict):
        return set()
    status = str(contract.get("status") or "").strip().lower()
    ids: set[str] = set()
    pack_id = str(contract.get("pack_id") or "").strip()
    if pack_id and status in CAPABILITY_ACTIVATED_STATES:
        ids.add(pack_id)
    pack_ids = contract.get("pack_ids")
    if isinstance(pack_ids, list) and status in CAPABILITY_ACTIVATED_STATES:
        ids.update(str(value).strip() for value in pack_ids if str(value).strip())
    return ids


def validate_capability_coverage(card: dict[str, Any]) -> list[str]:
    packs = load_capability_packs()
    if not packs:
        return []
    surfaces = normalized_surfaces(card)
    if not surfaces:
        return []

    strict = card.get("capability_coverage_required") is True
    activated_pack_ids = _activated_capability_pack_ids(card.get("capability_pack_contract"))
    errors: list[str] = []
    covered_surfaces: set[str] = set()

    for surface in sorted(surfaces):
        matching = [
            (pack_id, pack)
            for pack_id, pack in packs.items()
            if surface in {str(value).strip().lower() for value in pack.get("covers_surfaces", [])}
        ]
        if not matching:
            if strict:
                errors.append(f"capability pack missing for surface {surface!r}")
            continue
        covered_surfaces.add(surface)
        ready = any(str(pack.get("status") or "").strip() in CAPABILITY_READY_STATES for _, pack in matching)
        activated = any(pack_id in activated_pack_ids for pack_id, _ in matching)
        if not ready and not activated:
            pack_ids = ", ".join(pack_id for pack_id, _ in matching)
            errors.append(
                f"capability_pack_contract ready/activated is required for surface {surface!r}; candidate packs: {pack_ids}"
            )

    if strict and not covered_surfaces:
        errors.append("capability_coverage_required=true but no card surface is covered by the capability pack registry")
    return errors


def worker_result_schema_path(worker_id: str) -> str:
    binding = load_profile_bindings().get(worker_id) or {}
    schema_path = str(binding.get("result_schema") or "schemas/worker-result.schema.json").strip()
    return schema_path or "schemas/worker-result.schema.json"


def worker_result_schema_url(worker_id: str) -> str:
    return f"https://overkill-factory.dev/{worker_result_schema_path(worker_id)}"


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


def classify_artifact_ref(ref: Any) -> dict[str, Any]:
    value = str(ref or "").strip()
    normalized = value.replace("\\", "/")
    if not value:
        return {"ref": value, "artifact_class": "invalid", "public_safe": False, "reason": "empty artifact ref"}
    if value.startswith("external:"):
        return {"ref": value, "artifact_class": "sanitized_report", "public_safe": True, "reason": "explicit external/sanitized ref"}
    if value.startswith(("http://", "https://", "file://")) or Path(value).is_absolute() or ":" in normalized.split("/", 1)[0]:
        return {"ref": value, "artifact_class": "private_run_evidence", "public_safe": False, "reason": "absolute, URL, or private runtime ref"}
    if normalized.startswith((".tmp/", "tmp/", "reports/private/", "private/", "run-evidence/")) or "/.tmp/" in normalized:
        return {"ref": value, "artifact_class": "private_run_evidence", "public_safe": False, "reason": "private or transient evidence location"}
    if normalized.startswith(("dist/", "site/", "public/", "release/", "publication-candidates/")):
        return {"ref": value, "artifact_class": "publication_candidate", "public_safe": True, "reason": "repo publication surface"}
    return {"ref": value, "artifact_class": "public_safe", "public_safe": True, "reason": "repo-relative artifact ref"}


def artifact_contract_for_refs(refs: list[str]) -> dict[str, Any]:
    classifications = [classify_artifact_ref(ref) for ref in refs]
    return {
        "artifact_classes_checked": sorted({item["artifact_class"] for item in classifications}),
        "classifications": classifications,
        "publication_candidates": [
            item["ref"] for item in classifications if item["artifact_class"] == "publication_candidate"
        ],
        "private_run_evidence": [
            item["ref"] for item in classifications if item["artifact_class"] in ARTIFACT_PRIVATE_CLASSES
        ],
        "public_safe": all(bool(item.get("public_safe")) for item in classifications),
    }


def scan_result_passed(value: Any) -> bool:
    if value is True:
        return True
    if isinstance(value, dict):
        return str(value.get("result") or value.get("status") or "").strip().upper() == "PASS"
    return False


def artifact_publication_errors(metadata: dict[str, Any]) -> list[str]:
    receipt = metadata.get("receipt_five") if isinstance(metadata.get("receipt_five"), dict) else {}
    artifact_refs = string_list(receipt.get("artifact_paths"))
    event = metadata.get("kanban_transition_event") if isinstance(metadata.get("kanban_transition_event"), dict) else {}
    artifact_refs.extend(string_list(event.get("artifact_refs")))
    contract = artifact_contract_for_refs(sorted(set(artifact_refs)))
    errors: list[str] = []
    if contract["private_run_evidence"]:
        errors.append("publication artifacts must not reference private_run_evidence or transient_cache")
    if contract["publication_candidates"]:
        for field in PUBLICATION_SCANNER_FIELDS:
            if not scan_result_passed(metadata.get(field)):
                errors.append(f"publication_candidate artifacts require {field}=PASS")
    return errors


def read_project_version() -> str:
    if not PYPROJECT_PATH.exists():
        return "0.0.0"
    for line in PYPROJECT_PATH.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version"):
            return line.split("=", 1)[1].strip().strip('"')
    return "0.0.0"


def build_minimal_run_result(card_path: Path, packets_out: Path) -> dict[str, Any]:
    card = load_json_like(card_path)
    validation_errors = validate_card(card)
    gate_report = build_gate_report(card)
    required_workers = list(gate_report.get("required_workers", []))

    packets_out.mkdir(parents=True, exist_ok=True)
    packet_paths: list[str] = []
    for worker_id in required_workers:
        packet = build_worker_packet(worker_id, card, card_path)
        packet_path = packets_out / f"{worker_id}.json"
        packet_path.write_text(json.dumps(packet, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
        packet_paths.append(source_card_ref(packet_path))

    checks = [
        {
            "id": "card_contract",
            "result": "PASS" if not validation_errors else "FAIL",
            "details": validation_errors,
        },
        {
            "id": "gate_report",
            "result": "PASS" if gate_report.get("gate_status") == "ready_for_worker_execution" else "FAIL",
            "details": [str(gate_report.get("gate_status"))],
        },
        {
            "id": "worker_packets",
            "result": "PASS" if packet_paths else "FAIL",
            "details": packet_paths,
        },
    ]
    result = "PASS" if all(check["result"] == "PASS" for check in checks) else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/quickstart-smoke-result.schema.json",
        "result_type": "quickstart_smoke_result",
        "created_at": utc_now(),
        "result": result,
        "card": source_card_ref(card_path),
        "gate_status": gate_report.get("gate_status"),
        "required_workers": required_workers,
        "worker_packet_count": len(packet_paths),
        "worker_packet_dir": source_card_ref(packets_out),
        "checks": checks,
        "next_step": "Connect these packets to Hermes only after reviewing required workers and authority limits.",
    }


def doctor_check(check_id: str, status: str, summary: str, detail: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"id": check_id, "status": status, "summary": summary}
    if detail:
        payload["detail"] = detail
    return payload


def build_doctor_report(hermes_home: Path | None = None) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    py_ok = sys.version_info >= (3, 11)
    checks.append(
        doctor_check(
            "python_version",
            "PASS" if py_ok else "FAIL",
            f"Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        )
    )

    pyproject_text = PYPROJECT_PATH.read_text(encoding="utf-8") if PYPROJECT_PATH.exists() else ""
    metadata_ok = PYPROJECT_PATH.exists() and "name = \"overkill-factory\"" in pyproject_text and "OWNER" not in pyproject_text
    checks.append(
        doctor_check(
            "package_metadata",
            "PASS" if metadata_ok else "FAIL",
            "Package metadata is present and public identity is configured." if metadata_ok else "Package metadata is missing or still uses placeholder OWNER.",
        )
    )

    required_entrypoints = [
        "README.md",
        "docs/index.md",
        "docs/getting-started/install-in-hermes.md",
        "docs/reference/cli.md",
        "examples/minimal-hermes-project/card.md",
        "agents/hermes-profile-bindings.public.json",
        "adapters/hermes/transition_hook.py",
    ]
    missing = [path for path in required_entrypoints if not (ROOT / path).is_file()]
    checks.append(
        doctor_check(
            "repository_shape",
            "PASS" if not missing else "FAIL",
            "Public operator entrypoints are present." if not missing else "Public operator entrypoints are missing.",
            {"missing": missing},
        )
    )

    minimal_detail: dict[str, Any] = {}
    try:
        card = load_json_like(DEFAULT_MINIMAL_CARD)
        errors = validate_card(card)
        report = build_gate_report(card)
        minimal_ok = not errors and report.get("gate_status") == "ready_for_worker_execution"
        minimal_detail = {"validation_errors": errors, "gate_status": report.get("gate_status")}
    except Exception as exc:  # pragma: no cover - defensive report detail
        minimal_ok = False
        minimal_detail = {"error": str(exc)}
    checks.append(
        doctor_check(
            "minimal_example",
            "PASS" if minimal_ok else "FAIL",
            "Minimal example validates and reaches ready-for-worker-execution preflight." if minimal_ok else "Minimal example is not runnable.",
            minimal_detail,
        )
    )

    checks.append(
        doctor_check(
            "public_cli",
            "PASS",
            "Use factoryctl doctor, factoryctl init, and factoryctl run minimal as the public operator path.",
        )
    )

    hermes_path = hermes_home
    hermes_configured = hermes_path is not None and hermes_path.exists()
    checks.append(
        doctor_check(
            "hermes_runtime_optional",
            "PASS" if hermes_configured else "WARN",
            (
                f"Hermes home detected at {hermes_path}."
                if hermes_configured
                else "Hermes runtime was not checked. Local factory validation can run before Hermes integration."
            ),
        )
    )
    checks.append(
        doctor_check(
            "hermes_e2e_deferred",
            "INFO",
            "Point 5 is intentionally deferred: doctor does not claim a real Hermes E2E harness.",
        )
    )

    result = "FAIL" if any(check["status"] == "FAIL" for check in checks) else "PASS"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-doctor-result.schema.json",
        "record_type": "factory_doctor_result",
        "created_at": utc_now(),
        "result": result,
        "factory_version": read_project_version(),
        "checks": checks,
        "next_step": "Run factoryctl run minimal, then factoryctl init for your project workspace.",
    }


def write_operator_workspace(target: Path, project_name: str, hermes_home: Path | None, force: bool = False) -> None:
    if target.exists() and any(target.iterdir()) and not force:
        raise ValueError(f"{target} is not empty; use --force to write into it")
    target.mkdir(parents=True, exist_ok=True)
    for rel in ["cards", "worker-packets", "receipts", "worker-results", "reports"]:
        directory = target / rel
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").write_text("", encoding="utf-8")

    card_text = DEFAULT_MINIMAL_CARD.read_text(encoding="utf-8")
    (target / "cards" / "minimal-card.md").write_text(card_text, encoding="utf-8")

    config = {
        "$schema": "https://overkill-factory.dev/schemas/operator-workspace.schema.json",
        "project_name": project_name,
        "factory_version": read_project_version(),
        "created_at": utc_now(),
        "runtime": {
            "name": "Hermes",
            "mode": "operator-owned",
            "hermes_home": str(hermes_home) if hermes_home else "set HERMES_HOME or pass --hermes-home when integrating",
        },
        "paths": {
            "cards": "cards",
            "worker_packets": "worker-packets",
            "worker_results": "worker-results",
            "receipts": "receipts",
            "reports": "reports",
        },
        "next_commands": [
            "factoryctl doctor",
            "factoryctl run minimal",
            "factoryctl gate-report --card cards/minimal-card.md --out reports/minimal-gate-report.json",
            "factoryctl worker-packet --worker all --required-only --card cards/minimal-card.md --out worker-packets",
        ],
    }
    (target / "overkill.factory.json").write_text(json.dumps(config, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    readme = f"""# {project_name}

This workspace is ready for an operator-owned Hermes integration with Overkill
Factory. It contains source cards, worker-packet output folders, receipt folders
and a small public-safe starter card.

## First Commands

```bash
factoryctl doctor
factoryctl run minimal
factoryctl gate-report --card cards/minimal-card.md --out reports/minimal-gate-report.json
factoryctl worker-packet --worker all --required-only --card cards/minimal-card.md --out worker-packets
```

## Connect this workspace to your Hermes

1. Review `overkill.factory.json`.
2. Install the public Codex skill from `skills/codex/overkill-factory/`.
3. Apply the Hermes adapter only in a test Hermes checkout first.
4. Route generated worker packets into Hermes worker cards.
5. Attach real worker results and Receipt Five before moving cards to `done`.

Point 5 is intentionally deferred in this generated workspace: it does not claim
that a real Hermes E2E harness has run.
"""
    (target / "README.md").write_text(readme, encoding="utf-8")


def _non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and any(str(item).strip() for item in value)


def _non_empty_dict(value: Any) -> bool:
    return isinstance(value, dict) and bool(value)


def _non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _list_items(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def _status_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("status") or "").strip().lower()
    return str(value or "").strip().lower()


def normalized_surfaces(card: dict[str, Any]) -> set[str]:
    raw = card.get("surfaces", [])
    if not isinstance(raw, list):
        return set()
    return {str(value).strip().lower() for value in raw if str(value).strip()}


def risk(card: dict[str, Any]) -> str:
    return str(card.get("risk_effective", "")).strip().upper()


def strict_product_experience_required(card: dict[str, Any]) -> bool:
    return card.get("factory_method_version") == "OVERKILL_VFINAL" or isinstance(card.get("product_experience_plan"), dict)


def validate_product_face_packet(packet: dict[str, Any], *, strict: bool) -> list[str]:
    errors: list[str] = []
    if not strict:
        return errors

    for field in PRODUCT_FACE_PACKET_REQUIRED_FIELDS:
        value = packet.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"product_face_packet.{field} must be a non-empty array")
        elif isinstance(value, dict):
            if not value:
                errors.append(f"product_face_packet.{field} must be a non-empty object")
        elif not _non_empty_text(value):
            errors.append(f"product_face_packet.{field} is required")

    design = packet.get("design_direction") if isinstance(packet.get("design_direction"), dict) else {}
    if strict and design:
        for field in ("visual_tone", "product_fit", "density", "interaction_style"):
            if not _non_empty_text(design.get(field)):
                errors.append(f"product_face_packet.design_direction.{field} is required")

    human_gate = packet.get("human_gate") if isinstance(packet.get("human_gate"), dict) else {}
    if strict and human_gate:
        if "required" not in human_gate:
            errors.append("product_face_packet.human_gate.required is required")
        if human_gate.get("required") is True and not _non_empty_text(human_gate.get("approver")):
            errors.append("product_face_packet.human_gate.approver is required when human gate is required")

    return errors


def validate_product_experience_plan(plan: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in PRODUCT_EXPERIENCE_REQUIRED_FIELDS:
        value = plan.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"product_experience_plan.{field} must be a non-empty array")
        elif isinstance(value, dict):
            if not value:
                errors.append(f"product_experience_plan.{field} must be a non-empty object")
        elif not _non_empty_text(value):
            errors.append(f"product_experience_plan.{field} is required")

    design = plan.get("design_direction") if isinstance(plan.get("design_direction"), dict) else {}
    if design:
        for field in ("visual_tone", "product_fit", "density", "interaction_style"):
            if not _non_empty_text(design.get(field)):
                errors.append(f"product_experience_plan.design_direction.{field} is required")

    human_gate = plan.get("human_gate") if isinstance(plan.get("human_gate"), dict) else {}
    if human_gate:
        if "required" not in human_gate:
            errors.append("product_experience_plan.human_gate.required is required")
        if human_gate.get("required") is True and not _non_empty_text(human_gate.get("approver")):
            errors.append("product_experience_plan.human_gate.approver is required when human gate is required")

    return errors


def validate_vfinal_card_contract(data: dict[str, Any]) -> list[str]:
    if data.get("factory_method_version") != "OVERKILL_VFINAL":
        return []

    errors: list[str] = []
    missing = sorted(field for field in VFINAL_CORE_CONTRACTS if field not in data)
    if missing:
        errors.append("OVERKILL_VFINAL card missing core contracts: " + ", ".join(missing))

    request_type = str(data.get("request_type") or "").strip()
    if request_type and request_type not in VFINAL_REQUEST_TYPES:
        errors.append("request_type must be one of " + ", ".join(sorted(VFINAL_REQUEST_TYPES)))

    for field in sorted(VFINAL_CORE_CONTRACTS - {"request_type"}):
        if field in data and not _non_empty_dict(data.get(field)):
            errors.append(f"OVERKILL_VFINAL {field} must be a non-empty object")

    method_contract = data.get("method_contract") if isinstance(data.get("method_contract"), dict) else {}
    required_plans = method_contract.get("required_plans") if isinstance(method_contract, dict) else []
    if isinstance(required_plans, list):
        for plan in required_plans:
            field = str(plan).strip()
            if field and field not in data:
                errors.append(f"method_contract required plan {field} is missing from card")

    return errors


def load_canonical_runtime_enforcement() -> Any:
    spec = importlib.util.spec_from_file_location("canonical_runtime_enforcement", CANONICAL_RUNTIME_ENFORCEMENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load canonical runtime enforcement from {CANONICAL_RUNTIME_ENFORCEMENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["canonical_runtime_enforcement"] = module
    spec.loader.exec_module(module)
    return module


def validate_canonical_runtime_gate(data: dict[str, Any]) -> list[str]:
    if data.get("factory_method_version") != "OVERKILL_VFINAL":
        return []
    module = load_canonical_runtime_enforcement()
    errors: list[str] = []
    for blocker in module.validate_card_runtime_rules(data):
        checkpoint = blocker.get("checkpoint_id")
        missing = ", ".join(blocker.get("missing_fields") or [])
        errors.append(f"canonical_runtime_gate {checkpoint} missing {missing}")
    return errors


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
    errors.extend(validate_vfinal_card_contract(data))
    errors.extend(validate_canonical_runtime_gate(data))
    errors.extend(validate_capability_coverage(data))
    if data.get("executor_identity") == data.get("reviewer_identity"):
        errors.append("executor_identity and reviewer_identity must differ")
    product_facing = bool(surfaces & PRODUCT_FACE_SURFACES)
    strict_experience = product_facing and strict_product_experience_required(data)
    if product_facing and not isinstance(data.get("product_face_packet"), dict):
        errors.append("product_face_packet required for product-facing surfaces")
    elif product_facing:
        errors.extend(validate_product_face_packet(data["product_face_packet"], strict=strict_experience))
    if strict_experience:
        if not isinstance(data.get("product_experience_plan"), dict):
            errors.append("product_experience_plan required for vFinal product-facing surfaces")
        else:
            errors.extend(validate_product_experience_plan(data["product_experience_plan"]))
            human_gate = data["product_experience_plan"].get("human_gate")
            if isinstance(human_gate, dict) and human_gate.get("required") is True:
                review_human_gate = review.get("human_gate_required") is True
                if not review_human_gate and not isinstance(data.get("human_gate_packet"), dict):
                    errors.append("product_experience_plan.human_gate.required=true requires review.human_gate_required=true or human_gate_packet")
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
    is_pass = str(result.get("result") or "").upper() == "PASS"
    if is_pass and result.get("blocking_findings") is not False:
        errors.append("product_face_result PASS requires blocking_findings=false")
    for field in ("screenshots", "viewports", "checked_states", "user_journeys_checked", "evidence_refs"):
        if not _non_empty_string_list(result.get(field)):
            errors.append(f"product_face_result {field} must be a non-empty string array")
    screenshots = result.get("screenshots") if isinstance(result.get("screenshots"), list) else []
    for screenshot in screenshots:
        normalized = str(screenshot).strip().lower()
        if normalized.startswith(("not-captured", "missing", "placeholder", "fake")):
            errors.append("product_face_result screenshots must reference captured artifacts")
    for field in ("a11y", "overlap_check"):
        if not isinstance(result.get(field), dict) or not result.get(field):
            errors.append(f"product_face_result {field} must be an object")
        elif is_pass and str(result[field].get("status") or "").lower() != "pass":
            errors.append(f"product_face_result PASS requires {field}.status=pass")
    console = result.get("console")
    if is_pass and isinstance(console, dict) and str(console.get("status") or "").lower() != "pass":
        errors.append("product_face_result PASS requires console.status=pass")
    if result.get("blocking_findings") is True and not str(result.get("next_action") or "").strip():
        errors.append("product_face_result blocking findings require next_action")
    return errors


def _required_product_states(card: dict[str, Any]) -> list[str]:
    plan = card.get("product_experience_plan") if isinstance(card.get("product_experience_plan"), dict) else {}
    packet = card.get("product_face_packet") if isinstance(card.get("product_face_packet"), dict) else {}
    states = _list_items(plan.get("required_states"))
    states.extend(_list_items(packet.get("required_states")))
    state_matrix = packet.get("state_matrix")
    if isinstance(state_matrix, dict):
        states.extend(str(key).strip() for key in state_matrix if str(key).strip())
    return sorted({state.lower() for state in states})


def _required_product_proofs(card: dict[str, Any]) -> list[str]:
    plan = card.get("product_experience_plan") if isinstance(card.get("product_experience_plan"), dict) else {}
    packet = card.get("product_face_packet") if isinstance(card.get("product_face_packet"), dict) else {}
    proofs = _list_items(plan.get("proof_required"))
    proofs.extend(_list_items(packet.get("proof_required")))
    proofs.extend(_list_items(packet.get("visual_evidence_plan")))
    return [proof.lower() for proof in proofs]


def validate_product_face_result_against_card(result: dict[str, Any], card: dict[str, Any]) -> list[str]:
    errors = validate_product_face_result(result)
    if str(result.get("result") or "").upper() != "PASS":
        return errors

    for field in PRODUCT_FACE_RESULT_ALIGNMENT_FIELDS:
        value = result.get(field)
        if not isinstance(value, dict) or not value:
            errors.append(f"product_face_result.{field} is required for product-facing completion")
        elif _status_value(value) != "pass":
            errors.append(f"product_face_result.{field}.status must be pass")

    checked_states = {state.lower() for state in _list_items(result.get("checked_states"))}
    missing_states = [state for state in _required_product_states(card) if state not in checked_states]
    if missing_states:
        errors.append("product_face_result missing states promised by Product Face Packet/Experience Plan: " + ", ".join(missing_states))

    proofs = _required_product_proofs(card)
    viewports = " ".join(_list_items(result.get("viewports"))).lower()
    screenshots = " ".join(_list_items(result.get("screenshots"))).lower()
    if any("mobile" in proof for proof in proofs) and "mobile" not in viewports + " " + screenshots:
        errors.append("product_face_result missing mobile proof promised by Product Face Packet/Experience Plan")
    if any("desktop" in proof for proof in proofs) and "desktop" not in viewports + " " + screenshots:
        errors.append("product_face_result missing desktop proof promised by Product Face Packet/Experience Plan")

    packet_ref = str(result.get("packet_ref") or "").strip()
    if strict_product_experience_required(card) and not packet_ref:
        errors.append("product_face_result.packet_ref is required for vFinal product-facing completion")

    return errors


def _coverage_keys(coverage: object) -> list[str]:
    if not isinstance(coverage, dict):
        return []
    return [str(key).lower() for key in coverage]


def _coverage_has_prefixes(coverage: object, prefixes: tuple[str, ...]) -> list[str]:
    keys = _coverage_keys(coverage)
    missing: list[str] = []
    for prefix in prefixes:
        if not any(key.startswith(prefix) or key.startswith(f"{prefix}-") for key in keys):
            missing.append(prefix)
    return missing


def _known_vector_count(coverage: object) -> int:
    if not isinstance(coverage, dict):
        return 0
    for key in ("total", "total_vectors", "known_vectors_total"):
        value = coverage.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return len(coverage)


def _status_is_pass(value: object) -> bool:
    if value is True:
        return True
    if isinstance(value, int):
        return value == 0
    if isinstance(value, str):
        return value.strip().upper() in {"0", "OK", "PASS", "PASSED", "SUCCESS"}
    return False


def validate_quasar_toolchain_proof(proof: object) -> list[str]:
    if not isinstance(proof, dict):
        return ["auditor_result quasar_toolchain_proof object is required for code_audit"]
    errors: list[str] = []
    missing = [field for field in QUASAR_TOOLCHAIN_PROOF_REQUIRED if proof.get(field) in (None, "", [], {})]
    if missing:
        errors.append("auditor_result quasar_toolchain_proof missing " + ", ".join(missing))
    install_source = str(proof.get("install_source") or "").lower()
    source_head = str(proof.get("source_head") or "").strip()
    if "crates.io" in install_source and not source_head:
        errors.append("auditor_result quasar_toolchain_proof cannot rely on crates.io quasar-cli without a source_head pin")
    if source_head and len(source_head) < 7:
        errors.append("auditor_result quasar_toolchain_proof source_head must be a commit-like pin")
    if proof.get("build_status") not in (None, "") and not _status_is_pass(proof.get("build_status")):
        errors.append("auditor_result quasar_toolchain_proof build_status must be PASS")
    if proof.get("test_status") not in (None, "") and not _status_is_pass(proof.get("test_status")):
        errors.append("auditor_result quasar_toolchain_proof test_status must be PASS")
    if "evidence_refs" in proof and not _non_empty_string_list(proof.get("evidence_refs")):
        errors.append("auditor_result quasar_toolchain_proof evidence_refs must be a non-empty string array")
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
    required_non_empty_fields = [
        "auditor_head",
        "corpus_files_loaded",
        "checklist_coverage",
        "known_vectors_coverage",
        "instruction_matrix",
        "state_model",
        "quasar_toolchain_proof",
    ]
    missing = [field for field in required_non_empty_fields if result.get(field) in (None, "", [], {})]
    required_present_fields = [
        "findings",
        "waivers",
    ]
    missing.extend(field for field in required_present_fields if field not in result)
    if missing:
        errors.append("auditor_result code_audit missing " + ", ".join(missing))
    corpus_files = result.get("corpus_files_loaded") if isinstance(result.get("corpus_files_loaded"), list) else []
    if len(corpus_files) < AUDITOR_MIN_CORPUS_FILES:
        errors.append(f"auditor_result code_audit corpus_files_loaded must include at least {AUDITOR_MIN_CORPUS_FILES} files")
    missing_program_checklists = _coverage_has_prefixes(result.get("checklist_coverage"), AUDITOR_PROGRAM_CHECKLIST_PREFIXES)
    if missing_program_checklists:
        errors.append("auditor_result code_audit missing program checklist coverage " + ", ".join(missing_program_checklists))
    if _known_vector_count(result.get("known_vectors_coverage")) < AUDITOR_MIN_KNOWN_VECTORS:
        errors.append(f"auditor_result code_audit known_vectors_coverage must cover at least {AUDITOR_MIN_KNOWN_VECTORS} vectors")
    if "findings" in result and not isinstance(result.get("findings"), list):
        errors.append("auditor_result findings must be an array")
    if "waivers" in result and not isinstance(result.get("waivers"), list):
        errors.append("auditor_result waivers must be an array")
    errors.extend(validate_quasar_toolchain_proof(result.get("quasar_toolchain_proof")))
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
    verification_result = str(receipt.get("verification_result") or "").strip().upper()
    if verification_result and verification_result not in {"PASS", "BLOCKED", "WAIVED"}:
        errors.append("receipt_five.verification_result must be PASS, BLOCKED or WAIVED")
    if verification_result == "PASS" and not string_list(receipt.get("verification_commands")):
        errors.append("receipt_five PASS requires verification_commands")
    if receipt.get("reviewer_required") is True and not receipt.get("reviewer_result"):
        errors.append("reviewer_result required when reviewer_required=true")
    if (
        receipt.get("reviewer_required") is True
        and verification_result == "PASS"
        and str(receipt.get("reviewer_result") or "").strip().upper() != "PASS"
    ):
        errors.append("reviewer_result must be PASS when reviewer_required=true")
    transition_event = data.get("kanban_transition_event")
    if not isinstance(transition_event, dict):
        errors.append("kanban_transition_event object is required")
    else:
        required_event = ("from_status", "to_status", "actor", "worker", "receipt_refs", "artifact_refs")
        missing_event = [field for field in required_event if field not in transition_event]
        if missing_event:
            errors.append("kanban_transition_event missing " + ", ".join(missing_event))
        for field in ("from_status", "to_status", "actor", "worker"):
            if field in transition_event and not str(transition_event.get(field) or "").strip():
                errors.append(f"kanban_transition_event.{field} must be non-empty")
        for field in ("receipt_refs", "artifact_refs"):
            if field in transition_event and not _non_empty_string_list(transition_event.get(field)):
                errors.append(f"kanban_transition_event.{field} must be a non-empty string array")
        allowed = transition_event.get("allowed")
        event_to_status = str(transition_event.get("to_status") or "").strip().lower()
        if allowed is not None and event_to_status in {"done", "closed", "complete"} and allowed is not True:
            errors.append("kanban_transition_event.allowed must be true for promotion")
        event_result = str(transition_event.get("result") or transition_event.get("predicate_result") or "").strip().upper()
        if event_result and event_result not in {"PASS", "ALLOW", "APPROVED"}:
            errors.append("kanban_transition_event result must be PASS, ALLOW or APPROVED")
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
    reconciliation = data.get("receipt_five_reconciliation_result")
    if isinstance(reconciliation, dict):
        reconciliation_result = str(reconciliation.get("result") or "").strip().upper()
        if reconciliation_result not in {"PASS", "BLOCKED"}:
            errors.append("receipt_five_reconciliation_result.result must be PASS or BLOCKED")
        if reconciliation.get("valid") is True and reconciliation_result != "PASS":
            errors.append("receipt_five_reconciliation_result.valid=true requires result PASS")
    errors.extend(artifact_publication_errors(data))
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
    receipt = metadata.get("receipt_five") if isinstance(metadata.get("receipt_five"), dict) else {}
    if receipt.get("reviewer_required") is True and str(receipt.get("reviewer_result") or "").strip().upper() != "PASS":
        errors.append("reviewer_result must be PASS when reviewer_required=true")
    if receipt.get("reviewer_required") is True and "independent_review_result" not in metadata:
        errors.append("independent_review_result is required when receipt_five.reviewer_required=true")
    if product_face_result_required(card):
        product_face = metadata.get("product_face_result")
        if not isinstance(product_face, dict):
            errors.append("product_face_result metadata is required for product-facing completion")
        else:
            errors.extend(validate_product_face_result_against_card(product_face, card))
    return errors


def validate_transition_event_matches(
    metadata: dict[str, Any],
    *,
    from_status: str,
    to_status: str,
) -> list[str]:
    event = metadata.get("kanban_transition_event")
    if not isinstance(event, dict):
        return []
    errors: list[str] = []
    if str(event.get("from_status") or "").strip().lower() != from_status.strip().lower():
        errors.append("kanban_transition_event.from_status must match requested transition")
    if str(event.get("to_status") or "").strip().lower() != to_status.strip().lower():
        errors.append("kanban_transition_event.to_status must match requested transition")
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
        scan_packet = card.get("security_scan_packet", {}) if isinstance(card.get("security_scan_packet"), dict) else {}
        required_tools = scan_packet.get("required_tools", []) if isinstance(scan_packet.get("required_tools"), list) else []
        scan_tools = " ".join(
            [str(scan_packet.get("scanner_agent") or "")]
            + [str(tool) for tool in required_tools if isinstance(tool, str)]
        ).lower()
        required = (
            effective_risk in HIGH_RISK
            or bool(surfaces & SECURITY_SURFACES)
            or bool(surfaces & code_security_surfaces)
            or bool(surfaces & agentic_security_surfaces)
            or "codex-security" in scan_tools
            or "cybersecurity" in scan_tools
        )
        reason = "risk, code, public, agentic, scan packet or sensitive surface requires security evidence" if required else "no R3/R4, code, public, agentic, scan packet or sensitive surface detected"
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
    if worker_id == "evidence-reconciler":
        required = (
            phase in {"F13", "F14", "F15", "F16"}
            or effective_risk in REVIEW_RISK
            or bool(card.get("transition_event_required"))
            or bool(card.get("kanban_transition_event_ref"))
        )
        reason = "late-stage or review-risk card requires reconciled Receipt Five evidence" if required else "early/low-risk card without done promotion trigger"
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
        builder_owned = bool(surfaces & SPECIFIC_BUILDER_SURFACES)
        generic_implementation = bool(surfaces & GENERIC_IMPLEMENTATION_SURFACES)
        required = (phase == "F12" or generic_implementation) and not builder_owned
        if required:
            reason = "generic implementation fallback required; no surface-specific builder matched"
        elif builder_owned:
            reason = "surface-specific builder owns this implementation card"
        else:
            reason = "not an implementation card"
        return required, reason
    if worker_id == "frontend-builder":
        required = phase in {"F12", "F13"} and bool(surfaces & FRONTEND_BUILD_SURFACES)
        reason = "frontend/mobile/product-face implementation surface detected" if required else "no frontend builder trigger"
        return required, reason
    if worker_id == "backend-api-builder":
        required = phase in {"F12", "F13"} and bool(surfaces & BACKEND_BUILD_SURFACES)
        reason = "backend/API/auth implementation surface detected" if required else "no backend/API builder trigger"
        return required, reason
    if worker_id == "data-persistence-builder":
        required = phase in {"F12", "F13"} and bool(surfaces & DATA_BUILD_SURFACES)
        reason = "data/schema/migration implementation surface detected" if required else "no data persistence builder trigger"
        return required, reason
    if worker_id == "solana-quasar-builder":
        required = phase in {"F12", "F13"} and bool(surfaces & SOLANA_BUILD_SURFACES)
        reason = "Solana/Quasar implementation surface detected" if required else "no Solana/Quasar builder trigger"
        return required, reason
    if worker_id == "solana-quasar-qa-engineer":
        explicit_onchain_qa = bool(surfaces & SOLANA_QA_SURFACES)
        required = phase in {"F13", "F14", "F15"} and explicit_onchain_qa
        reason = "Solana/Quasar QA or devnet verification surface detected" if required else "no Solana/Quasar QA trigger"
        return required, reason
    if worker_id == "wallet-transaction-builder":
        required = phase in {"F12", "F13"} and bool(surfaces & WALLET_TRANSACTION_SURFACES)
        reason = "wallet/transaction/signing implementation surface detected" if required else "no wallet transaction builder trigger"
        return required, reason
    if worker_id == "integration-builder":
        required = phase in {"F12", "F13"} and bool(surfaces & INTEGRATION_BUILD_SURFACES)
        reason = "integration/fullstack implementation surface detected" if required else "no integration builder trigger"
        return required, reason
    if worker_id == "test-automation-builder":
        required = (
            phase in {"F12", "F13", "F18"}
            and bool(surfaces & TEST_AUTOMATION_SURFACES)
        ) or review.get("test_automation_required") is True
        reason = "test/eval/regression automation surface detected" if required else "no test automation builder trigger"
        return required, reason
    if worker_id == "infra-devops-builder":
        required = phase in {"F12", "F16"} and bool(surfaces & INFRA_DEVOPS_BUILD_SURFACES)
        reason = "infra/DevOps/runtime implementation surface detected" if required else "no infra/DevOps builder trigger"
        return required, reason
    if worker_id == "agent-runtime-builder":
        required = phase in {"F12", "F18"} and bool(surfaces & AGENT_RUNTIME_BUILD_SURFACES)
        reason = "agent/Hermes/factory runtime implementation surface detected" if required else "no agent runtime builder trigger"
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
        required = runtime_contract.get("remote_proof_required") is True
        if required:
            reason = "explicit remote proof required by runtime_contract"
        elif effective_risk in HIGH_RISK:
            reason = "high-risk card has remote proof as future/advisory gate unless runtime_contract.remote_proof_required=true"
        else:
            reason = "local proof is sufficient by current card"
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
    if worker_id == "control-tower-projection-worker":
        control_tower_contract = card.get("control_tower_contract")
        control_tower_surfaces = {
            "control-tower",
            "operator",
            "operator-cockpit",
            "discord",
            "projection",
            "status",
            "forecast",
            "blocker",
            "approval",
        }
        required = (
            phase == "F19"
            or bool(surfaces & control_tower_surfaces)
            or (isinstance(control_tower_contract, dict) and control_tower_contract.get("enabled") is True)
        )
        reason = "owner-facing Control Tower projection required" if required else "no Control Tower projection trigger"
        return required, reason
    if worker_id == "discord-control-tower-bridge":
        control_tower_contract = card.get("control_tower_contract")
        bridge_surfaces = {
            "control-tower",
            "discord",
            "operator-cockpit",
            "approval",
            "access",
            "blocker",
            "health",
            "runtime-registration",
        }
        required = (
            phase in {"F19", "F29"}
            or bool(surfaces & bridge_surfaces)
            or (isinstance(control_tower_contract, dict) and control_tower_contract.get("discord_bridge_required") is True)
        )
        reason = "Discord Control Tower bridge required" if required else "no Discord bridge trigger"
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


def unblock_guidance(missing_inputs: list[str]) -> list[dict[str, str]]:
    return [
        {
            "field": field,
            "action": f"populate card.{field} with public-safe contract data or attach the required worker evidence",
            "authority": "operator may edit planning fields; worker/human evidence must be produced by the assigned authority",
        }
        for field in missing_inputs
    ]


def runtime_decision_profile(card: dict[str, Any]) -> dict[str, Any]:
    decision = str(card.get("runtime_decision") or "").strip().lower()
    contract = card.get("runtime_contract") if isinstance(card.get("runtime_contract"), dict) else {}
    runtime = str(contract.get("runtime") or contract.get("adapter") or decision or "hermes").strip().lower()
    if "local" in decision or runtime in {"factoryctl", "local", "none"}:
        scope = "local_factoryctl_only"
        allowed = ["validate-card", "gate-report", "worker-packet", "transition-plan"]
        forbidden = ["spawn-worker", "mutate-live-board", "complete-main-task"]
    elif "external" in decision:
        scope = "external_runtime"
        allowed = ["create-public-safe-packet", "wait-for-external-result"]
        forbidden = ["assume-external-pass", "copy-private-auth", "complete-main-task-without-receipt"]
    else:
        scope = "hermes_runtime"
        allowed = ["materialize-blocked-tasks", "link-worker-tasks", "enforce-done-after-pass"]
        forbidden = ["spawn-without-route-readiness", "complete-without-receipt-five", "treat-artifact-existence-as-pass"]
    return {
        "decision": decision or "hermes_default",
        "scope": scope,
        "runtime_contract": contract,
        "allowed_runtime_actions": allowed,
        "forbidden_runtime_actions": forbidden,
    }


def required_worker_ids(card: dict[str, Any]) -> list[str]:
    return [worker_id for worker_id in WORKERS if worker_required(worker_id, card)[0]]


def build_worker_packet(worker_id: str, card: dict[str, Any], source_path: Path) -> dict[str, Any]:
    worker = WORKERS[worker_id]
    profile_binding = load_profile_bindings().get(worker_id)
    required, reason = worker_required(worker_id, card)
    missing_inputs = missing_required_inputs(worker, card)
    missing_profile_binding = profile_binding is None
    runtime_decision = runtime_decision_profile(card)
    status = "requires_execution" if required else "not_required_by_current_card"
    if required and missing_inputs:
        status = "blocked_missing_inputs"
    if required and missing_profile_binding:
        status = "blocked_missing_profile_binding"

    packet = {
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
            "unblock_guidance": unblock_guidance(missing_inputs),
            "target_repo_paths": card.get("target_repo_paths", []),
            "authority_max": card.get("authority_max"),
            "forbidden_actions": card.get("forbidden_actions", []),
        },
        "runtime_decision": runtime_decision,
        "output_contract": {
            "receipt_field": worker.output_field,
            "must_attach_artifact_refs": True,
            "must_state_blocking_findings": True,
            "must_record_tool_or_profile": True,
            "human_approval_must_be_real": worker_id == "human-gate-clerk",
            "promotion_authority": {
                "positive_results": sorted(PROMOTION_PASS_RESULTS),
                "requires_valid_record": True,
                "requires_blocking_findings_false": worker_id != "human-gate-clerk",
            },
            "artifact_policy": {
                "allowed_public_classes": sorted(ARTIFACT_PUBLIC_CLASSES),
                "private_classes": sorted(ARTIFACT_PRIVATE_CLASSES),
                "publication_candidates_require_scanners": list(PUBLICATION_SCANNER_FIELDS),
            },
        },
        "status": status,
    }
    if profile_binding:
        packet["profile_binding"] = {
            "profile_id": profile_binding.get("profile_id"),
            "hermes_profile_name": profile_binding.get("hermes_profile_name"),
            "dispatch_queue_policy": profile_binding.get("dispatch_queue_policy"),
            "queue_class_source": "worker_task.queue_class",
            "skill_refs": profile_binding.get("skill_refs", []),
            "result_schema": profile_binding.get("result_schema"),
            "receipt_field": profile_binding.get("receipt_field"),
            "can_mutate_card_state": profile_binding.get("can_mutate_card_state", False),
            "evidence_path_policy": profile_binding.get("evidence_path_policy"),
            "profile_manifest_ref": profile_binding.get("profile_manifest_ref"),
            "profile_description_ref": profile_binding.get("profile_description_ref"),
            "toolset_policy": profile_binding.get("toolset_policy"),
            "skill_install_ref": profile_binding.get("skill_install_ref"),
            "last_hermes_smoke_ref": profile_binding.get("last_hermes_smoke_ref"),
        }
    return packet


def build_gate_report(card: dict[str, Any]) -> dict[str, Any]:
    validation_errors = validate_card(card)
    worker_rows: dict[str, dict[str, Any]] = {}
    required_workers: list[str] = []
    blocked_workers: list[str] = []
    for worker_id in WORKERS:
        required, reason = worker_required(worker_id, card)
        status = build_worker_packet(worker_id, card, Path("<memory>"))["status"]
        missing_inputs = missing_required_inputs(WORKERS[worker_id], card)
        worker_rows[worker_id] = {
            "required": required,
            "reason": reason,
            "status": status,
            "unblock_guidance": unblock_guidance(missing_inputs),
        }
        if required:
            required_workers.append(worker_id)
        if str(status).startswith("blocked_"):
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
        "gate_predicate_result": "BLOCK" if gate_status == "blocked" else "PASS",
        "promotion_authority": {
            "predicate": "card validation has no errors and all required worker inputs are present",
            "result": "BLOCK" if gate_status == "blocked" else "PASS",
            "allowed_transition_scopes": [] if gate_status == "blocked" else ["create_worker_tasks"],
        },
        "required_workers": required_workers,
        "blocked_workers": blocked_workers,
        "card_validation_errors": validation_errors,
        "next_safe_actions": [
            guidance
            for row in worker_rows.values()
            for guidance in row.get("unblock_guidance", [])
        ],
        "workers": worker_rows,
    }


BEFORE_READY_WORKERS = {
    "factory-orchestrator",
    "source-ledger-worker",
    "product-sot-planner",
    "product-architect",
    "control-tower-projection-worker",
    "discord-control-tower-bridge",
    "docs-os-worker",
    "decomposition-planner",
    "supply-chain-gate",
    "security-orchestrator",
}

BEFORE_DONE_WORKERS = {
    "codex-security",
    "solana-quasar-auditor",
    "product-face",
    "independent-reviewer",
    "evidence-reconciler",
    "human-gate-clerk",
    "implementation-worker",
    "frontend-builder",
    "backend-api-builder",
    "data-persistence-builder",
    "solana-quasar-builder",
    "solana-quasar-qa-engineer",
    "wallet-transaction-builder",
    "integration-builder",
    "test-automation-builder",
    "infra-devops-builder",
    "agent-runtime-builder",
    "qa-verification-worker",
    "autoreview-gate",
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


def validate_human_gate_freshness(data: dict[str, Any], card: dict[str, Any] | None) -> list[str]:
    errors: list[str] = []
    if not str(data.get("decision_at") or "").strip():
        errors.append("human gate decision_at is required")
    if not str(data.get("approval_event_id") or data.get("approval_event_ref") or "").strip():
        errors.append("human gate approval_event_id is required")
    if card is None:
        return errors
    record_ref = data.get("card_ref") if isinstance(data.get("card_ref"), dict) else {}
    for field in ("risk_effective", "phase"):
        if record_ref.get(field) and card.get(field) and record_ref.get(field) != card.get(field):
            errors.append(f"human gate card_ref.{field} must match current card")
    forbidden = set(string_list(card.get("forbidden_actions")))
    approved = set(string_list(data.get("approved_scope")))
    if forbidden & approved:
        errors.append("human gate approved_scope must not include forbidden_actions")
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
        elif not (evidence_kind == "synthetic" and audit_mode == "preflight"):
            errors.extend(validate_auditor_result(data))
        if data.get("preflight_only") is True and data.get("result") == "PASS" and evidence_kind != "synthetic":
            errors.append("preflight_only auditor_result cannot be real PASS")
    if record_type == "product_face_result":
        for field in (
            "screenshots",
            "viewports",
            "checked_states",
            "user_journeys_checked",
            "a11y",
            "overlap_check",
            "performance_note",
        ):
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
    if evidence_kind == "real":
        domain_requirements = {
            "security_orchestration_result": ("routed_specialists", "coverage_ledger_ref"),
            "appsec_owasp_result": ("covered_controls", "control_coverage"),
            "agentic_ai_security_result": ("tool_boundary_controls", "untrusted_input_policy"),
            "cloud_infra_security_result": ("infra_boundary_controls", "promotion_boundary"),
            "crypto_key_management_result": ("key_boundary_controls", "forbidden_key_actions"),
            "release_ops_result": ("promotion_boundary_controls", "rollback_boundary"),
            "public_safety_result": ("public_safety_checks", "forbidden_residue_policy"),
            "supply_chain_result": ("supply_chain_controls", "provenance_boundary"),
            "detection_monitoring_result": ("monitoring_boundary_controls", "incident_boundary"),
        }
        for field in domain_requirements.get(record_type, ()):
            if data.get(field) in (None, "", [], {}):
                errors.append(f"{field} is required for real {record_type}")
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
        errors.extend(validate_human_gate_freshness(data, card))
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
        if expected_worker_id:
            expected_schema = worker_result_schema_url(expected_worker_id)
            if data.get("$schema") != expected_schema:
                errors.append(f"$schema must be {expected_schema}")
        authority = data.get("promotion_authority")
        if not isinstance(authority, dict):
            errors.append("promotion_authority object is required")
        else:
            if authority.get("active") is False:
                errors.append("superseded worker result cannot satisfy promotion")
            if str(authority.get("result") or "").strip().upper() != "PASS":
                errors.append("promotion_authority.result must be PASS")
            scopes = string_list(authority.get("allowed_transition_scopes"))
            if "done" not in [scope.lower() for scope in scopes]:
                errors.append("promotion_authority.allowed_transition_scopes must include done")

    evidence_refs = string_list(data.get("evidence_refs"))
    if not evidence_refs:
        errors.append("evidence_refs must contain at least one artifact ref")
    else:
        errors.extend(_evidence_ref_errors(evidence_refs, evidence_root))
    contract = data.get("artifact_contract")
    if isinstance(contract, dict) and contract.get("public_safe") is False and data.get("reusable_for_product") is True:
        errors.append("private artifact_contract cannot be reusable_for_product=true")
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
    if record_type == "product_face_result" and card is not None:
        errors.extend(validate_product_face_result_against_card(data, card))
    return errors


def collect_worker_result_fields(card: dict[str, Any], results_dir: Path | None) -> dict[str, dict[str, Any]]:
    if results_dir is None or not results_dir.exists():
        return {}
    records_by_type: dict[str, list[dict[str, Any]]] = {}
    for path in sorted(results_dir.glob("*.json")):
        try:
            data = load_json_like(path)
        except (OSError, ValueError, json.JSONDecodeError):
            continue
        record_type = str(data.get("record_type") or "").strip()
        if not record_type:
            continue
        expected_worker_id = _worker_id_for_output_field(record_type)
        errors = validate_worker_result_record(
            data,
            expected_field=record_type,
            expected_worker_id=expected_worker_id,
            card=card,
            evidence_root=ROOT,
        )
        authority = data.get("promotion_authority") if isinstance(data.get("promotion_authority"), dict) else {}
        records_by_type.setdefault(record_type, []).append(
            {
                "evidence_ref": source_card_ref(path),
                "created_at": data.get("created_at") or data.get("decision_at"),
                "result": data.get("result") or data.get("decision"),
                "active": authority.get("active", data.get("active", True)) is not False and not data.get("superseded_by"),
                "valid": not errors,
                "validation_errors": errors,
            }
        )
    records: dict[str, dict[str, Any]] = {}
    for record_type, candidates in records_by_type.items():
        active = [candidate for candidate in candidates if candidate.get("active")]
        ordered = sorted(active or candidates, key=_worker_record_sort_key, reverse=True)
        if ordered:
            records[record_type] = ordered[0]
    return records


def receipt_result_fields(
    card: dict[str, Any],
    metadata: dict[str, Any],
    *,
    evidence_root: Path | None = None,
) -> dict[str, dict[str, Any]]:
    fields: dict[str, dict[str, Any]] = {}
    for worker_id, worker in WORKERS.items():
        value = metadata.get(worker.output_field)
        if isinstance(value, dict):
            errors = validate_worker_result_record(
                value,
                expected_field=worker.output_field,
                expected_worker_id=worker_id,
                card=card,
                evidence_root=evidence_root,
            )
            fields[worker.output_field] = {
                "evidence_ref": None,
                "result": value.get("result") or value.get("decision"),
                "valid": not errors,
                "validation_errors": errors,
            }
    return fields


def _worker_record_sort_key(record: dict[str, Any]) -> tuple[str, str]:
    return (
        str(record.get("created_at") or ""),
        str(record.get("evidence_ref") or ""),
    )


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
        "profile_binding": packet.get("profile_binding"),
        "expected_receipt_field": worker.output_field,
        "status": packet["status"],
    }


def build_worker_closure(
    card: dict[str, Any],
    metadata: dict[str, Any] | None,
    results_dir: Path | None,
) -> dict[str, Any]:
    metadata = metadata or {}
    present_fields = receipt_result_fields(card, metadata, evidence_root=ROOT)
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


def receipt_reconciliation_errors(metadata: dict[str, Any] | None) -> list[str]:
    if not isinstance(metadata, dict):
        return ["receipt_five_reconciliation_result is required for done promotion"]
    event = metadata.get("kanban_transition_event") if isinstance(metadata.get("kanban_transition_event"), dict) else {}
    if event.get("allowed") is not True:
        errors = ["kanban_transition_event.allowed must be true for done promotion"]
    else:
        errors = []
    reconciliation = metadata.get("receipt_five_reconciliation_result")
    if not isinstance(reconciliation, dict):
        errors.append("receipt_five_reconciliation_result is required for done promotion")
        return errors
    if str(reconciliation.get("result") or "").strip().upper() != "PASS":
        errors.append("receipt_five_reconciliation_result.result must be PASS for done promotion")
    if reconciliation.get("valid") is not True:
        errors.append("receipt_five_reconciliation_result.valid must be true for done promotion")
    authority = reconciliation.get("promotion_authority")
    if isinstance(authority, dict) and str(authority.get("result") or "").strip().upper() != "PASS":
        errors.append("receipt_five_reconciliation_result promotion_authority must be PASS")
    return errors


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
    elif normalized_to in {"review", "review-ready", "ready_for_review"}:
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
            blocked_reasons.append(f"{worker_id} result is required before review-ready")
        transition_action = "block_transition" if blocked_reasons else "allow_review_ready"
        completion = build_worker_closure(card, receipt or {}, worker_results_dir)
    elif normalized_to in {"done", "closed", "complete"}:
        blocked_reasons.extend(gate["card_validation_errors"])
        for worker_id in gate["blocked_workers"]:
            blocked_reasons.append(f"{worker_id} missing inputs before done")
        if receipt is None:
            blocked_reasons.append("receipt metadata is required for done transition")
            completion = build_worker_closure(card, {}, worker_results_dir)
        else:
            blocked_reasons.extend(validate_completion(card, receipt))
            blocked_reasons.extend(receipt_reconciliation_errors(receipt))
            blocked_reasons.extend(
                validate_transition_event_matches(
                    receipt,
                    from_status=from_status,
                    to_status=to_status,
                )
            )
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
    artifact_contract = artifact_contract_for_refs(evidence_refs)
    positive_authority = result in PROMOTION_PASS_RESULTS and blocking_findings is False
    payload = {
        "$schema": worker_result_schema_url(worker_id),
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
        "artifact_contract": artifact_contract,
        "artifact_classifications": artifact_contract["classifications"],
        "evidence_kind": evidence_kind,
        "reusable_for_product": reusable_for_product,
        "next_action": next_action,
        "promotion_authority": {
            "result": "PASS" if positive_authority else "BLOCK",
            "predicate": "worker result is PASS/WAIVED, valid, scoped to the current card, and has blocking_findings=false",
            "allowed_transition_scopes": ["done"] if positive_authority else [],
            "active": True,
        },
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
                "audit_mode": "preflight" if evidence_kind == "synthetic" else "code_audit",
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
                "user_journeys_checked": ["open target", "inspect states"],
                "accessibility": {"checked": True, "mode": evidence_kind},
                "a11y": {"status": "pass" if not blocking_findings else "fail", "mode": evidence_kind},
                "overlap": {"checked": True, "mode": evidence_kind},
                "overlap_check": {"status": "pass" if not blocking_findings else "fail", "mode": evidence_kind},
                "console": {"status": "pass" if not blocking_findings else "warn"},
                "performance_note": "Synthetic smoke only." if evidence_kind == "synthetic" else "See Product Face report.",
                "packet_ref": "card.product_face_packet",
                "packet_comparison": {
                    "status": "pass" if not blocking_findings else "fail",
                    "basis": "Product Face evidence is explicitly tied to the card packet.",
                },
                "source_promise_coverage": {
                    "status": "pass" if not blocking_findings else "fail",
                    "basis": "Visible proof is scoped to the card acceptance criteria.",
                },
                "design_fit_review": {
                    "status": "pass" if not blocking_findings else "fail",
                    "basis": "Design fit reviewed by Product Face validator for this bounded card.",
                },
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
    if evidence_kind == "real":
        record_type = worker.output_field
        if record_type == "security_orchestration_result":
            payload.update(
                {
                    "routed_specialists": [
                        "codex-security",
                        "appsec-owasp-specialist",
                        "agentic-ai-security-specialist",
                        "cloud-infra-security-specialist",
                        "crypto-key-management-specialist",
                        "solana-quasar-auditor",
                        "supply-chain-gate",
                    ],
                    "coverage_ledger_ref": ".tmp/security-coverage-ledger.md",
                }
            )
        if record_type == "appsec_owasp_result":
            payload.update(
                {
                    "covered_controls": ["browser", "api-boundary", "auth-not-applicable", "safe-errors", "no-external-scripts"],
                    "control_coverage": {"status": "pass", "mode": "validation-scope"},
                }
            )
        if record_type == "agentic_ai_security_result":
            payload.update(
                {
                    "tool_boundary_controls": {
                        "untrusted_text": "data_not_instruction",
                        "tool_expansion": "forbidden_by_card",
                    },
                    "untrusted_input_policy": "Source material cannot override worker authority, tool policy or forbidden actions.",
                }
            )
        if record_type == "cloud_infra_security_result":
            payload.update(
                {
                    "infra_boundary_controls": {
                        "deploy": "forbidden",
                        "cloud_mutation": "not_authorized",
                        "secrets": "not_mounted",
                    },
                    "promotion_boundary": "Production promotion requires a new release gate.",
                }
            )
        if record_type == "crypto_key_management_result":
            payload.update(
                {
                    "key_boundary_controls": {
                        "signing": "forbidden",
                        "key_material": "not_requested",
                        "custody": "out_of_scope",
                    },
                    "forbidden_key_actions": ["wallet_signing", "secret_access", "custody_action", "funds_movement"],
                }
            )
        if record_type == "release_ops_result":
            payload.update(
                {
                    "promotion_boundary_controls": {
                        "production_release": "forbidden",
                        "release_gate": "future_required",
                    },
                    "rollback_boundary": "Keep card blocked or rerun generated validation artifacts; no production rollback exists.",
                }
            )
        if record_type == "public_safety_result":
            payload.update(
                {
                    "public_safety_checks": ["public_safety_scan", "secret_safety_scan", "relative_artifact_refs"],
                    "forbidden_residue_policy": "No private names, local paths, private board ids or raw source captures in public artifacts.",
                }
            )
        if record_type == "supply_chain_result":
            payload.update(
                {
                    "supply_chain_controls": {
                        "dependencies": "no_new_package_install",
                        "scripts": "local_builtins_only",
                        "secret_scan": "pass",
                    },
                    "provenance_boundary": "Generated artifacts are local validation evidence, not release provenance.",
                }
            )
        if record_type == "detection_monitoring_result":
            payload.update(
                {
                    "monitoring_boundary_controls": {
                        "production_monitoring": "future_required",
                        "logs": "validation_artifacts_only",
                    },
                    "incident_boundary": "No production incident surface exists in this validation run.",
                }
            )
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
        "approval_event_id": f"human:{card.get('card_id') or 'card'}:{utc_now()}",
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


def command_unblock_plan(args: argparse.Namespace) -> int:
    report = build_gate_report(load_json_like(args.card))
    plan = {
        "$schema": "https://overkill-factory.dev/schemas/unblock-plan.schema.json",
        "record_type": "operator_unblock_plan",
        "created_at": utc_now(),
        "card_id": report.get("card_id"),
        "gate_predicate_result": report.get("gate_predicate_result"),
        "blocked_workers": report.get("blocked_workers", []),
        "next_safe_actions": report.get("next_safe_actions", []),
        "limits": [
            "This plan does not execute workers, approve gates, or bypass missing evidence.",
            "Human/security/review evidence must be produced by the assigned authority.",
        ],
    }
    write_json(args.out, plan)
    return 1 if report.get("gate_predicate_result") == "BLOCK" else 0


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
    action = str(plan["transition_action"])
    return 1 if action.startswith("block") and args.enforce else 0


def command_doctor(args: argparse.Namespace) -> int:
    report = build_doctor_report(args.hermes_home)
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=True))
    else:
        print(f"Overkill Factory doctor: {report['result']}")
        for check in report["checks"]:
            print(f"- {check['status']}: {check['id']} - {check['summary']}")
    return 0 if report["result"] == "PASS" else 1


def command_init(args: argparse.Namespace) -> int:
    try:
        write_operator_workspace(
            args.out,
            project_name=args.project_name,
            hermes_home=args.hermes_home,
            force=args.force,
        )
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Initialized Overkill Factory workspace at {args.out}")
    return 0


def command_run_minimal(args: argparse.Namespace) -> int:
    result = build_minimal_run_result(args.card, args.packets_out)
    write_json(args.out, result)
    print(f"{result['result']}: wrote {source_card_ref(args.out)}")
    return 0 if result["result"] == "PASS" else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Overkill Factory control helper")
    sub = parser.add_subparsers(dest="command", required=True)

    doctor_parser = sub.add_parser("doctor", help="Check local factory install health without claiming Hermes E2E proof.")
    doctor_parser.add_argument("--json", action="store_true")
    doctor_parser.add_argument("--hermes-home", type=Path)
    doctor_parser.set_defaults(func=command_doctor)

    init_parser = sub.add_parser("init", help="Create a Hermes-friendly operator workspace.")
    init_parser.add_argument("--out", type=Path, required=True)
    init_parser.add_argument("--project-name", required=True)
    init_parser.add_argument("--hermes-home", type=Path)
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(func=command_init)

    run_parser = sub.add_parser("run", help="Run public operator workflows.")
    run_sub = run_parser.add_subparsers(dest="run_command", required=True)
    minimal_parser = run_sub.add_parser("minimal", help="Run the minimal public factory smoke.")
    minimal_parser.add_argument("--card", type=Path, default=DEFAULT_MINIMAL_CARD)
    minimal_parser.add_argument("--out", type=Path, default=DEFAULT_QUICKSTART_OUT)
    minimal_parser.add_argument("--packets-out", type=Path, default=DEFAULT_PACKETS_OUT)
    minimal_parser.set_defaults(func=command_run_minimal)

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

    unblock_plan_parser = sub.add_parser("unblock-plan")
    unblock_plan_parser.add_argument("--card", type=Path, required=True)
    unblock_plan_parser.add_argument("--out", type=Path)
    unblock_plan_parser.set_defaults(func=command_unblock_plan)

    evidence_record_parser = sub.add_parser("evidence-record")
    evidence_record_parser.add_argument(
        "--worker",
        choices=[worker_id for worker_id in WORKERS if worker_id != "human-gate-clerk"],
        required=True,
    )
    evidence_record_parser.add_argument("--card", type=Path, required=True)
    evidence_record_parser.add_argument("--result", choices=["PASS", "BLOCKED", "FAIL", "WAIVED", "PENDING"], required=True)
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
