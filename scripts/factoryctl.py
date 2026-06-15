#!/usr/bin/env python3
"""Overkill Factory control helpers.

This CLI prepares and validates the contracts that autonomous workers consume.
It intentionally does not fake security, Auditor, Product Face, reviewer, or
human approvals. It produces execution requests and preflight reports; the
specialist worker still has to run and attach real evidence.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import sysconfig
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any


CODE_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from public_refs import contains_private_kanban_task_marker, public_safe_kanban_ref, sanitize_public_refs  # noqa: E402


def installed_asset_root() -> Path | None:
    candidates = [
        Path(sysconfig.get_path("data") or "") / "share" / "overkill-factory",
        CODE_ROOT / "share" / "overkill-factory",
    ]
    for candidate in candidates:
        if (
            (candidate / "agents" / "hermes-profile-bindings.public.json").exists()
            and (candidate / "examples" / "minimal-hermes-project" / "card.md").exists()
        ):
            return candidate
    return None


def default_work_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "agents" / "hermes-profile-bindings.public.json").exists() and (
        cwd / "examples" / "minimal-hermes-project" / "card.md"
    ).exists():
        return cwd
    installed_root = installed_asset_root()
    if installed_root is not None:
        return installed_root
    return CODE_ROOT


ROOT = default_work_root()
PROFILE_BINDINGS_PATH = ROOT / "agents" / "hermes-profile-bindings.public.json"
PROFILE_READINESS_PATH = ROOT / "agents" / "worker-profile-readiness.public.json"
PROFILE_READINESS_REF = "agents/worker-profile-readiness.public.json"
CAPABILITY_PACKS_PATH = ROOT / "agents" / "capability-packs.public.json"
DEFAULT_WORKFLOW_CATALOG = ROOT / "docs" / "factory-workflow.catalog.json"
CANONICAL_RUNTIME_ENFORCEMENT_PATH = CODE_ROOT / "scripts" / "canonical_runtime_enforcement.py"
DEFAULT_MINIMAL_CARD = ROOT / "examples" / "minimal-hermes-project" / "card.md"
DEFAULT_QUICKSTART_OUT = Path.cwd() / ".tmp" / "quickstart-result.json"
DEFAULT_PACKETS_OUT = Path.cwd() / ".tmp" / "minimal-worker-packets"
PYPROJECT_PATH = ROOT / "pyproject.toml"
DEFAULT_TRUTH_OUT = ROOT / ".tmp" / "factory-runs" / "truth" / "truth-packet.json"
DEFAULT_EVIDENCE_GRAPH_OUT = ROOT / ".tmp" / "factory-runs" / "evidence" / "evidence-graph.json"
DEFAULT_READINESS_LEDGER_OUT = ROOT / ".tmp" / "factory-runs" / "readiness" / "readiness-truth-ledger.json"
DEFAULT_HERMES_EVIDENCE_OUT = ROOT / ".tmp" / "factory-runs" / "hermes-evidence" / "sanitized-package.json"
DEFAULT_PREPILOT_CHECKLIST_OUT = ROOT / ".tmp" / "factory-runs" / "prepilot" / "loose-end-checklist.json"
PRIVATE_RUNTIME_REF_RE = re.compile(
    r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|/var/|discord(app)?\.com|webhook|token|secret|guild[_-]?id|channel[_-]?id|message[_-]?id)",
    re.IGNORECASE,
)
CONTRACT_DIGEST_ALGORITHM = "sha256"
VOLATILE_CONTRACT_KEYS = {
    "checked_at",
    "created_at",
    "generated_at",
    "last_checked_at",
    "timestamp",
    "updated_at",
}

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

PRODUCT_SCOPE_INTENTS = {"full_product", "child_slice"}
PRODUCT_PLANNING_PHASES = {"F11", "F12", "F13", "F14", "F15", "F16", "F17"}
PRODUCTION_SURFACES = {
    "production",
    "release",
    "deploy",
    "mainnet",
    "staging",
    "customers",
    "customer-ready",
    "monitoring",
    "rollback",
}
COMPLETION_SOT_STATUSES = {"DONE", "BLOCKED", "DEFERRED_WITH_OWNER", "OUT_OF_SCOPE"}
COMPLETION_METHOD_STATUSES = {"EXECUTED", "WAIVED", "BLOCKED"}
USER_QUESTION_CLASSES = {"discoverable", "preference", "authority_required", "access_required", "risk_acceptance", "blocked"}
ALLOWED_USER_QUESTION_CLASSES = USER_QUESTION_CLASSES - {"discoverable"}
INTERNAL_COORDINATION_TERMS = {
    "worker packet",
    "worker packets",
    "internal worker",
    "internal workers",
    "schema",
    "schemas",
    "evidence graph",
    "source ledger",
    "method router",
    "gate report",
    "receipt five",
    "hermes card",
    "kanban card",
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
SECRET_DELIVERY_SAFE_MODES = {
    "none",
    "placeholder",
    "simulator",
    "user-mediated",
    "jit_broker",
    "vault_jit",
    "hardware_signer",
    "external_service",
}
SECRET_DELIVERY_EXCEPTION_MODES = {"startup_env", "runtime_file"}
SECRET_DELIVERY_FORBIDDEN_MODES = {"prompt_context"}
SECRET_POLICY_FORBIDDEN_KEYS = {
    "secret",
    "secret_value",
    "raw_secret",
    "credential_value",
    "private_key",
    "env_dump",
    "runtime_file_path",
    "local_secret_path",
}
HARDENING_REQUIRED_EXECUTION_MODES = {"bounded_execution", "material_execution", "production_operation"}
TOOL_USING_SURFACES = {
    "shell",
    "browser",
    "filesystem",
    "network",
    "mcp",
    "git",
    "github",
    "cloud",
    "database",
    "wallet",
    "messaging",
}
WIDE_FILESYSTEM_SCOPES = {"workspace_wide", "external_mount"}
WIDE_NETWORK_SCOPES = {"unrestricted"}
PARALLEL_EDIT_LANE_KINDS = {"write", "execution"}
V2_APPROVAL_KEYS = [
    "qa",
    "independent_review",
    "security_review",
    "cybersecurity_review",
    "cto_gate",
    "human_gate",
]

PRODUCT_FACE_SURFACES = {"ux", "frontend", "mobile", "wallet-ui", "product-face"}
PRODUCT_EXPERIENCE_SURFACES = PRODUCT_FACE_SURFACES | {
    "web",
    "web-app",
    "web_app",
    "website",
    "site",
    "landing",
    "landing-page",
    "screen",
    "component",
    "desktop",
    "desktop-app",
    "cli",
    "tui",
    "extension",
    "browser-extension",
    "ai-interface",
    "ai_interface",
    "chat-ui",
    "agentic-interface",
    "agentic_interface",
    "design-system",
    "design_system",
    "docs",
    "documentation",
    "onboarding",
    "game",
    "gameplay",
    "2d",
    "3d",
}
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
    "source_ref",
    "source_head_expected",
    "source_head",
    "source_head_matches",
    "container_image",
    "solana_release",
    "solana_install_url",
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
CAPABILITY_ACTIVE_LIFECYCLE_STATES = {"activated"}
CAPABILITY_AMBIGUOUS_SURFACE_GUIDANCE = {
    "mobile": "use responsive/mobile-web for browser UI or ios/android/react-native for native mobile work"
}
CAPABILITY_CONTRACT_TEXT_FIELDS = (
    "lifecycle_state",
    "permission_class",
    "local_smoke_path",
    "eval_path",
    "smoke_evidence_ref",
    "eval_evidence_ref",
)
PRODUCT_EXPERIENCE_REQUIRED_FIELDS = (
    "surface_type",
    "surface_pack",
    "experience_sot",
    "user",
    "job_to_be_done",
    "main_flows",
    "required_states",
    "design_direction",
    "visual_quality_bar",
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
    "visual_quality_bar",
    "proof_required",
    "reviewers_required",
    "done_definition",
    "human_gate",
)
REFERENCE_QUALITY_REQUIRED_FIELDS = (
    "record_type",
    "experience_category",
    "quality_bar",
    "anti_generic_criteria",
    "references",
    "design_rationale",
    "reuse_policy",
    "accessibility_constraints",
    "performance_constraints",
    "acceptance_criteria",
)
PROFESSIONAL_DESIGN_PROCESS_REQUIRED_FIELDS = (
    "record_type",
    "surface_type",
    "mode",
    "design_brief",
    "task_map",
    "reference_research",
    "ux_architecture",
    "wireframe_gate",
    "visual_direction",
    "prototype_gate",
    "design_qa_plan",
    "comparative_review_gate",
    "handoff_requirements",
)
PRODUCT_DELIVERY_QUALITY_PROFILE_REQUIRED_FIELDS = (
    "record_type",
    "profile_id",
    "archetype",
    "applies_to_surfaces",
    "quality_dimensions",
    "required_proofs",
    "waiver_policy",
    "evidence_refs",
)
REASONING_POLICY_REQUIRED_FIELDS = (
    "record_type",
    "reasoning_class",
    "allowed_profile_classes",
    "review_intensity",
    "evidence_policy",
    "private_reasoning_policy",
    "block_when",
)
REASONING_CLASSES = {"light", "standard", "deep", "adversarial", "human_decision"}
REASONING_REVIEW_INTENSITIES = {"none", "self_check", "independent_review", "specialist_matrix", "human_gate"}
PRODUCT_FACE_RESULT_ALIGNMENT_FIELDS = (
    "packet_comparison",
    "source_promise_coverage",
    "design_fit_review",
    "professional_design_process_comparison",
    "reference_quality_comparison",
)
VISUAL_QUALITY_ALLOWED_RESULTS = {"PASS", "PASS_WITH_RESIDUALS", "BLOCK"}
DOMAIN_PROOF_ALLOWED_STATUSES = {"PASS", "WARN", "FAIL", "WAIVED"}
REFERENCE_RESEARCH_SOURCE_TYPES = {
    "component_registry",
    "design_library",
    "design_system",
    "product_reference",
    "site_gallery",
    "user_flow_library",
}
REFERENCE_RESEARCH_LIBRARY_TYPES = {
    "component_registry",
    "design_library",
    "site_gallery",
    "user_flow_library",
}
REFERENCE_COMPARISON_DIMENSIONS = (
    "layout_hierarchy",
    "interaction_model",
    "state_coverage",
    "visual_language",
    "density_spacing",
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
        timing="after product_face_packet and professional_design_process, before product-facing done",
        blocking_policy=(
            "Frontend, UX, mobile, wallet UI, or visible product work cannot be "
            "declared complete without screen/state/mobile/a11y evidence."
        ),
        required_inputs=("product_face_packet", "professional_design_process", "target_repo_paths", "acceptance_criteria"),
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
        required_inputs=("product_face_packet", "professional_design_process", "scope_in", "scope_out", "done_definition"),
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
        raise ValueError(f"{public_path_ref(path)} must contain a JSON object")
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


def load_profile_readiness_rows() -> dict[str, dict[str, Any]]:
    if not PROFILE_READINESS_PATH.exists():
        return {}
    data = json.loads(PROFILE_READINESS_PATH.read_text(encoding="utf-8"))
    default_record = data.get("default_record", {})
    worker_rows = data.get("worker_readiness", {})
    if not isinstance(default_record, dict) or not isinstance(worker_rows, dict):
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for worker_id, row in worker_rows.items():
        if isinstance(row, dict):
            rows[str(worker_id)] = {**default_record, **row, "worker_id": str(worker_id)}
    return rows


def profile_readiness_summary(worker_id: str) -> dict[str, Any]:
    row = load_profile_readiness_rows().get(worker_id)
    if not row:
        return {
            "ledger_ref": PROFILE_READINESS_REF,
            "readiness_state": "blocked_missing_readiness_ledger",
            "current_runtime_claim": False,
            "next_required_action": "publish a public-safe worker profile readiness ledger before claiming profile readiness",
        }
    freshness = row.get("freshness_policy") if isinstance(row.get("freshness_policy"), dict) else {}
    current_claim = freshness.get("current_runtime_claim") is True
    readiness_state = str(row.get("readiness_state") or "blocked")
    if readiness_state == "current_profile_ready":
        next_action = "dispatch may use current profile readiness evidence"
    else:
        next_action = "run a fresh smoke and eval ledger before treating this profile as current runtime readiness"
    return {
        "ledger_ref": PROFILE_READINESS_REF,
        "readiness_state": readiness_state,
        "current_runtime_claim": current_claim,
        "smoke_result": row.get("smoke_result"),
        "eval_result": row.get("eval_result"),
        "checked_at": row.get("checked_at"),
        "producer": row.get("producer"),
        "packet_fixture_ref": row.get("packet_fixture_ref"),
        "next_required_action": next_action,
    }


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


def _pack_structured_proof_ids(pack: dict[str, Any]) -> list[str]:
    return sorted({item for item in _list_items(pack.get("structured_proofs_required")) if item})


def validate_activated_capability_contract(
    contract: Any,
    *,
    candidate_pack_ids: set[str],
    requested_surfaces: set[str],
) -> list[str]:
    if not isinstance(contract, dict):
        return ["capability_pack_contract object is required to activate a template capability pack"]

    errors: list[str] = []
    status = str(contract.get("status") or "").strip().lower()
    lifecycle_state = str(contract.get("lifecycle_state") or "").strip().lower()
    contract_pack_ids = _activated_capability_pack_ids(contract)
    covered_surfaces = {item.lower() for item in _list_items(contract.get("covered_surfaces"))}
    specialist_workers = _list_items(contract.get("specialist_workers"))
    activation_refs = _list_items(contract.get("activation_evidence_refs"))
    tool_refs = _list_items(contract.get("tool_refs"))
    missing_capabilities = _list_items(contract.get("missing_capabilities"))
    contract_structured_proofs = _list_items(contract.get("structured_proofs_required"))

    if status not in CAPABILITY_ACTIVATED_STATES:
        errors.append("capability_pack_contract.status must be ready or activated")
    if lifecycle_state not in CAPABILITY_ACTIVE_LIFECYCLE_STATES:
        errors.append("capability_pack_contract.lifecycle_state must be activated before material execution")
    if not contract_pack_ids.intersection(candidate_pack_ids):
        candidates = ", ".join(sorted(candidate_pack_ids))
        errors.append(f"capability_pack_contract.pack_id must match one of the required packs: {candidates}")

    missing_surfaces = sorted(requested_surfaces - covered_surfaces)
    for surface in missing_surfaces:
        errors.append(f"capability_pack_contract.covered_surfaces missing required surface {surface!r}")

    for field in CAPABILITY_CONTRACT_TEXT_FIELDS:
        if not _non_empty_text(contract.get(field)):
            errors.append(f"capability_pack_contract.{field} is required for activated packs")
    if not specialist_workers:
        errors.append("capability_pack_contract.specialist_workers must name activated specialist workers")
    if not activation_refs:
        errors.append("capability_pack_contract.activation_evidence_refs must include public-safe activation evidence refs")
    if not tool_refs:
        errors.append("capability_pack_contract.tool_refs must name the activated tools or commands")
    if missing_capabilities:
        errors.append("capability_pack_contract.missing_capabilities must be empty before material execution")
    packs = load_capability_packs()
    required_pack_proofs: set[str] = set()
    for pack_id in contract_pack_ids.intersection(candidate_pack_ids):
        required_pack_proofs.update(_pack_structured_proof_ids(packs.get(pack_id, {})))
    if required_pack_proofs:
        if not contract_structured_proofs:
            errors.append("capability_pack_contract.structured_proofs_required must mirror activated registry proof ids")
        missing_proofs = sorted(required_pack_proofs - set(contract_structured_proofs))
        if missing_proofs:
            errors.append(
                "capability_pack_contract.structured_proofs_required missing registry proof ids: "
                + ", ".join(missing_proofs)
            )

    profile_binding_refs = contract.get("profile_binding_refs")
    if not isinstance(profile_binding_refs, dict) or not profile_binding_refs:
        errors.append("capability_pack_contract.profile_binding_refs must map each specialist worker to a profile binding ref")
    else:
        for worker_id in specialist_workers:
            if not _non_empty_text(profile_binding_refs.get(worker_id)):
                errors.append(f"capability_pack_contract.profile_binding_refs missing {worker_id!r}")

    worker_mapping = contract.get("worker_mapping")
    if isinstance(worker_mapping, dict) and specialist_workers:
        worker_set = set(specialist_workers)
        for lane, workers in worker_mapping.items():
            for worker_id in _list_items(workers):
                if worker_id not in worker_set:
                    errors.append(
                        f"capability_pack_contract.worker_mapping.{lane} references worker {worker_id!r} "
                        "outside specialist_workers"
                    )

    return errors


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
    activation_required_surfaces: set[str] = set()
    activation_candidate_pack_ids: set[str] = set()

    for surface in sorted(surfaces):
        if surface in CAPABILITY_AMBIGUOUS_SURFACE_GUIDANCE:
            errors.append(
                f"ambiguous capability surface {surface!r}; {CAPABILITY_AMBIGUOUS_SURFACE_GUIDANCE[surface]}"
            )
            continue
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
        if ready:
            continue
        if activated:
            activation_required_surfaces.add(surface)
            activation_candidate_pack_ids.update(pack_id for pack_id, _ in matching)
        else:
            pack_ids = ", ".join(pack_id for pack_id, _ in matching)
            errors.append(
                f"capability_pack_contract ready/activated is required for surface {surface!r}; candidate packs: {pack_ids}"
            )

    if activation_required_surfaces:
        errors.extend(
            validate_activated_capability_contract(
                card.get("capability_pack_contract"),
                candidate_pack_ids=activation_candidate_pack_ids,
                requested_surfaces=activation_required_surfaces,
            )
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
    print(f"Wrote {public_path_ref(path)}")


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


def public_path_ref(path: Path, fallback: str = "artifact") -> str:
    raw = str(path)
    windows_path = PureWindowsPath(raw)
    if windows_path.is_absolute() or (len(raw) >= 2 and raw[1] == ":"):
        return f"external:{windows_path.name or fallback}"
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        name = path.name or fallback
        return f"external:{name}"


def classify_artifact_ref(ref: Any) -> dict[str, Any]:
    value = str(ref or "").strip()
    normalized = value.replace("\\", "/")
    if not value:
        return {"ref": value, "artifact_class": "invalid", "public_safe": False, "reason": "empty artifact ref"}
    if contains_private_kanban_task_marker(value):
        return {"ref": value, "artifact_class": "private_run_evidence", "public_safe": False, "reason": "raw private Kanban task id"}
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


def public_safe_text(value: Any) -> bool:
    text = str(value or "")
    return PRIVATE_RUNTIME_REF_RE.search(text) is None and not contains_private_kanban_task_marker(text)


def sanitize_slug(value: Any, *, fallback: str = "item") -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value or "").strip()).strip("-._")
    return cleaned[:80] or fallback


def redact_private_text(value: Any) -> str:
    text = str(value or "")
    text = re.sub(r"(?<![A-Za-z])[A-Za-z]:[\\/][^ \];,\"]+", "[redacted-private-ref]", text)
    text = re.sub(r"/(?:home|Users|srv|var)/[^ \];,\"]+", "[redacted-private-ref]", text)
    text = PRIVATE_RUNTIME_REF_RE.sub("[redacted-private-marker]", text)
    text = public_safe_kanban_ref(text) or ""
    return text


def sanitize_public_ref(ref: Any) -> tuple[str, dict[str, Any] | None]:
    value = str(ref or "").strip()
    classification = classify_artifact_ref(value)
    trusted_external_prefixes = (
        "external:sanitized",
        "external:operator",
        "external:public",
        "external:maintainer",
        "external:source-card",
        "external:memory",
    )
    if value.startswith("external:") and not value.startswith(trusted_external_prefixes):
        classification = {**classification, "public_safe": False, "reason": "untrusted external ref requires explicit sanitized/operator/public prefix"}
    if classification.get("public_safe") and public_safe_text(value):
        return value, None
    redacted = {
        "ref": "redacted:private-runtime-ref",
        "artifact_class": classification.get("artifact_class") or "private_run_evidence",
        "reason": classification.get("reason") or "private runtime marker",
    }
    return redacted["ref"], {"raw_ref_redacted": True, **redacted}


def blocker_economics_entry(
    *,
    blocker_id: str,
    owner: str,
    risk_controlled: str,
    cost_time_class: str,
    dependency: str,
    smallest_safe_next_action: str,
    mutation_risk: str,
    route: str,
    status: str = "blocked",
    expiry: str = "until evidence changes",
) -> dict[str, str]:
    return {
        "blocker_id": sanitize_slug(blocker_id, fallback="blocker"),
        "owner": owner,
        "risk_controlled": risk_controlled,
        "cost_time_class": cost_time_class,
        "dependency": dependency,
        "smallest_safe_next_action": smallest_safe_next_action,
        "mutation_risk": mutation_risk,
        "route": route,
        "expiry": expiry,
        "status": status,
    }


def worker_blocker_economics(worker_id: str, status: str, reason: str) -> dict[str, str]:
    worker = WORKERS[worker_id]
    route = "human_approval" if worker_id == "human-gate-clerk" else "hermes"
    action = f"run {worker_id} and attach {worker.output_field}"
    if status.startswith("blocked_"):
        action = f"provide missing inputs for {worker_id}, then rerun gate-report"
    return blocker_economics_entry(
        blocker_id=f"worker:{worker_id}:{status}",
        owner=worker_id,
        risk_controlled=reason or "required worker evidence",
        cost_time_class="bounded_worker_run",
        dependency=worker.output_field,
        smallest_safe_next_action=action,
        mutation_risk="none_without_explicit_worker_execution",
        route=route,
        status="blocked" if status.startswith("blocked_") else "actionable",
    )


def blocker_type_for_worker(worker_id: str) -> str:
    if worker_id == "human-gate-clerk":
        return "human_gate"
    if worker_id in {
        "codex-security",
        "solana-quasar-auditor",
        "security-orchestrator",
        "appsec-owasp-specialist",
        "agentic-ai-security-specialist",
        "cloud-infra-security-specialist",
        "crypto-key-management-specialist",
        "public-safety-gate",
        "supply-chain-gate",
        "detection-monitoring-worker",
    }:
        return "security"
    if worker_id in {"source-ledger-worker", "product-sot-planner"}:
        return "source"
    if worker_id in {"factory-orchestrator", "evidence-reconciler", "independent-reviewer", "autoreview-gate"}:
        return "orchestration"
    if worker_id in {"agent-runtime-builder", "infra-devops-builder", "remote-proof-runner"}:
        return "runtime"
    return "dependency"


def recovery_runtime_boundary() -> dict[str, Any]:
    return {
        "runtime_authority": "hermes_kanban",
        "uses_native_kanban_primitives": True,
        "native_primitives": [
            "kanban_task",
            "parent_link",
            "blocked_state",
            "comment_metadata",
            "run_history",
            "reclaim_reassign",
        ],
        "local_state_authority": False,
    }


def recovery_retry_policy(*, attempt_number: int = 1, base: dict[str, Any] | None = None) -> dict[str, Any]:
    policy = dict(base or {})
    policy.setdefault("max_attempts", 10)
    policy.setdefault("attempt_number", attempt_number)
    policy.setdefault(
        "stop_classes",
        [
            "human_gate",
            "secret_or_access_required",
            "external_mutation_required",
            "ambiguous_product_decision",
            "repeated_failed_recovery",
        ],
    )
    policy.setdefault("escalation_reason", "Escalate only when the blocker leaves factory-owned safe repair scope.")
    policy["attempt_number_role"] = "planner_seed_not_runtime_counter"
    policy["runtime_attempt_source"] = "hermes_task_history"
    policy["runtime_attempt_marker"] = "factory_recovery_attempt"
    policy["runtime_authority"] = "hermes_kanban"
    policy["local_state_authority"] = False
    return policy


def is_human_gate_recovery(*, blocker_type: str, repair_owner_worker: str) -> bool:
    return blocker_type == "human_gate" or repair_owner_worker == "human-gate-clerk"


def recovery_recommendation_for_worker(
    *,
    worker_id: str,
    card: dict[str, Any],
    reason: str,
    attempt_number: int = 1,
) -> dict[str, Any]:
    card_id = sanitize_slug(card.get("card_id") or "factory-card", fallback="factory-card")
    blocker_type = blocker_type_for_worker(worker_id)
    human_gate_required = blocker_type == "human_gate"
    route_id = f"recovery:{card_id}:{sanitize_slug(worker_id, fallback='worker')}"
    output_field = WORKERS.get(worker_id, WORKERS["factory-orchestrator"]).output_field
    return {
        "blocker_type": blocker_type,
        "factory_owned_repair_allowed": not human_gate_required,
        "human_gate_required": human_gate_required,
        "recovery_route_id": route_id,
        "repair_owner_worker": worker_id,
        "repair_task_ref": f"hermes:intent:{route_id}",
        "repair_inputs": [reason or f"{worker_id} blocked"],
        "expected_repair_outputs": [output_field],
        "commands_or_worker_routes": [f"route {worker_id} through Hermes Kanban"],
        "invalidates_refs": [f"worker-result:{output_field}:blocking-or-stale"],
        "supersedes_refs": [f"worker-result:{output_field}:fresh-pass-required"],
        "dependency_edge_patch": {
            "old_edges": [f"blocked:{output_field}"],
            "new_edges": [f"fresh-review:{output_field}"],
            "patch_authority": "fresh review PASS recorded in Hermes before unblock",
        },
        "downstream_freeze_scope": ["next worker", "done promotion", "Receipt Five closure"],
        "fresh_review_required": not human_gate_required,
        "fresh_review_result_ref": f"worker-result:{output_field}:fresh-review",
        "unblock_authority_ref": "Hermes blocked event plus fresh review PASS" if not human_gate_required else "human_gate_record",
        "retry_policy": recovery_retry_policy(attempt_number=attempt_number),
        "hermes_runtime_boundary": recovery_runtime_boundary(),
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
        raise ValueError(f"{public_path_ref(target, fallback='workspace')} is not empty; use --force to write into it")
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


def _has_contract(data: dict[str, Any], field: str) -> bool:
    value = data.get(field)
    if isinstance(value, dict) and value:
        return True
    return _non_empty_text(data.get(f"{field}_ref"))


def _has_ref_or_object(data: dict[str, Any], field: str) -> bool:
    return _has_contract(data, field)


def _repo_local_json_ref_path(ref: Any) -> Path | None:
    if not _non_empty_text(ref):
        return None
    value = str(ref).strip().split("#", 1)[0].strip()
    if not value:
        return None
    normalized = value.replace("\\", "/")
    if normalized.startswith(("external:", "repo://", "http://", "https://", "file://")):
        return None
    if Path(value).is_absolute() or ":" in normalized.split("/", 1)[0]:
        return None
    candidate = (ROOT / normalized).resolve()
    try:
        candidate.relative_to(ROOT.resolve())
    except ValueError:
        return None
    return candidate


def _load_repo_local_json_ref(ref: Any) -> dict[str, Any]:
    path = _repo_local_json_ref_path(ref)
    if path is None or not path.is_file():
        return {}
    try:
        return load_json_like(path)
    except Exception:
        return {}


def _product_planning_required(card: dict[str, Any]) -> bool:
    request_type = str(card.get("request_type") or "").strip()
    scope_intent = str(card.get("scope_intent") or "").strip()
    method = card.get("method_contract") if isinstance(card.get("method_contract"), dict) else {}
    method_scope = str(method.get("scope_intent") or "").strip()
    return (
        card.get("complete_product_required") is True
        or request_type == "product_new"
        or scope_intent in PRODUCT_SCOPE_INTENTS
        or method_scope in PRODUCT_SCOPE_INTENTS
    )


def _production_ladder_required(card: dict[str, Any]) -> bool:
    phase = str(card.get("phase") or "").upper()
    surfaces = normalized_surfaces(card)
    method = card.get("method_contract") if isinstance(card.get("method_contract"), dict) else {}
    route = " ".join(
        str(value or "")
        for value in (
            method.get("factory_route"),
            method.get("production_route_decision"),
            card.get("authority_max"),
        )
    ).lower()
    return (
        bool(surfaces & PRODUCTION_SURFACES)
        or phase in {"F16", "F17"}
        or "production" in route
        or "mainnet" in route
        or card.get("complete_product_required") is True
    )


def _research_required(card: dict[str, Any]) -> bool:
    outcome = card.get("outcome_contract") if isinstance(card.get("outcome_contract"), dict) else {}
    if outcome.get("discovery_depth") == "research_required":
        return True
    for lane in card_parallel_lane_contracts(card):
        if str(lane.get("lane_kind") or "").strip().lower() == "research":
            return True
    return False


def _selected_engineering_methods(method_contract: dict[str, Any]) -> set[str]:
    methods = set(_list_items(method_contract.get("selected_methods")))
    matrix = method_contract.get("engineering_method_matrix")
    if isinstance(matrix, list):
        for row in matrix:
            if isinstance(row, dict):
                methods.update(_list_items(row.get("methods")))
    selected = str(method_contract.get("selected_method") or "").strip()
    if selected:
        methods.add(selected)
    return methods


def validate_product_scope_planning_contract(card: dict[str, Any]) -> list[str]:
    if card.get("factory_method_version") != "OVERKILL_VFINAL":
        return []
    if not _product_planning_required(card):
        return []

    errors: list[str] = []
    product_sot = card.get("product_sot") if isinstance(card.get("product_sot"), dict) else {}
    method = card.get("method_contract") if isinstance(card.get("method_contract"), dict) else {}
    software_plan = card.get("software_development_plan") if isinstance(card.get("software_development_plan"), dict) else {}

    if not _has_ref_or_object(card, "full_product_sot_scope_coverage"):
        errors.append("full_product_sot_scope_coverage or full_product_sot_scope_coverage_ref is required for complete Product SOT planning")
    if not _non_empty_text(product_sot.get("full_product_sot_scope_coverage_ref")):
        errors.append("product_sot.full_product_sot_scope_coverage_ref is required")
    if str(method.get("canonical_scope_source") or "").strip().lower() not in {"approved product sot", "product_sot", "product sot"}:
        errors.append("method_contract.canonical_scope_source must be approved Product SOT")
    if str(method.get("scope_intent") or "").strip() not in PRODUCT_SCOPE_INTENTS:
        errors.append("method_contract.scope_intent must be full_product or child_slice")
    if not _non_empty_text(method.get("factory_route")):
        errors.append("method_contract.factory_route is required")
    required_artifacts = set(_list_items(method.get("required_factory_artifacts")))
    for artifact in ("full_product_sot_scope_coverage", "product_creation_plan", "product_implementation_readiness"):
        if artifact not in required_artifacts:
            errors.append(f"method_contract.required_factory_artifacts must include {artifact}")
    matrix = method.get("engineering_method_matrix")
    if not isinstance(matrix, list) or not matrix:
        errors.append("method_contract.engineering_method_matrix is required")
    else:
        for index, row in enumerate(matrix):
            row = row if isinstance(row, dict) else {}
            for field in ("surface_or_component", "reason"):
                if not _non_empty_text(row.get(field)):
                    errors.append(f"method_contract.engineering_method_matrix[{index}].{field} is required")
            for field in ("methods", "required_artifacts", "evidence_required"):
                if not _non_empty_string_list(row.get(field)):
                    errors.append(f"method_contract.engineering_method_matrix[{index}].{field} must be non-empty")
    slice_policy = method.get("slice_execution_policy") if isinstance(method.get("slice_execution_policy"), dict) else {}
    if slice_policy.get("slices_are_execution_units_only") is not True:
        errors.append("method_contract.slice_execution_policy.slices_are_execution_units_only must be true")
    if slice_policy.get("canonical_scope_must_not_shrink") is not True:
        errors.append("method_contract.slice_execution_policy.canonical_scope_must_not_shrink must be true")
    if not _non_empty_text(method.get("production_route_decision")):
        errors.append("method_contract.production_route_decision is required")
    if not _non_empty_string_list(software_plan.get("full_product_plan")):
        errors.append("software_development_plan.full_product_plan is required before slice execution")
    if not _non_empty_string_list(software_plan.get("slice_execution_plan")):
        errors.append("software_development_plan.slice_execution_plan is required")
    if _non_empty_string_list(software_plan.get("slice_plan")) and not _non_empty_string_list(software_plan.get("full_product_plan")):
        errors.append("software_development_plan.slice_plan cannot stand in for full_product_plan")
    return errors


def validate_specialist_research_contract(card: dict[str, Any]) -> list[str]:
    if card.get("factory_method_version") != "OVERKILL_VFINAL":
        return []
    errors: list[str] = []
    if _research_required(card) and not _has_ref_or_object(card, "specialist_research_plan"):
        errors.append("specialist_research_plan or specialist_research_plan_ref is required when research_required is active")
    decision = card.get("specialist_decision_packet") if isinstance(card.get("specialist_decision_packet"), dict) else {}
    if decision:
        if not _non_empty_string_list(decision.get("resolutions")):
            errors.append("specialist_decision_packet.resolutions must turn research into an operational factory decision")
        impacts = decision.get("impacts") if isinstance(decision.get("impacts"), dict) else {}
        for field in ("sot", "architecture", "method_router", "gates", "proof"):
            if field not in impacts:
                errors.append(f"specialist_decision_packet.impacts.{field} is required")
    return errors


def validate_product_creation_readiness_contract(card: dict[str, Any]) -> list[str]:
    if card.get("factory_method_version") != "OVERKILL_VFINAL":
        return []
    if not _product_planning_required(card):
        return []
    errors: list[str] = []
    if not _has_ref_or_object(card, "product_creation_plan"):
        errors.append("product_creation_plan or product_creation_plan_ref is required before material product implementation")
    if not _has_ref_or_object(card, "product_context_packet"):
        errors.append("product_context_packet or product_context_packet_ref is required for product-specific implementation workers")
    if not _has_ref_or_object(card, "product_implementation_readiness"):
        errors.append("product_implementation_readiness or product_implementation_readiness_ref is required before material product implementation")

    plan = card.get("product_creation_plan") if isinstance(card.get("product_creation_plan"), dict) else {}
    if plan:
        if plan.get("complete_product_required") is not True:
            errors.append("product_creation_plan.complete_product_required must be true for complete-product planning")
        if not _non_empty_text(plan.get("product_delivery_quality_profile_ref")) and not isinstance(
            plan.get("product_delivery_quality_profile"), dict
        ):
            errors.append("product_creation_plan.product_delivery_quality_profile_ref is required")
        if not _non_empty_string_list(plan.get("complete_product_scope")):
            errors.append("product_creation_plan.complete_product_scope is required")
        if not _non_empty_string_list(plan.get("release_promotion_ladder_refs")):
            errors.append("product_creation_plan.release_promotion_ladder_refs is required")
        work_units = plan.get("work_units")
        if not isinstance(work_units, list) or not work_units:
            errors.append("product_creation_plan.work_units must be non-empty")
        else:
            for index, unit in enumerate(work_units):
                unit = unit if isinstance(unit, dict) else {}
                for field in ("product_sot_requirement_refs", "scope_in", "scope_out", "verification", "stop_conditions"):
                    if not _non_empty_string_list(unit.get(field)):
                        errors.append(f"product_creation_plan.work_units[{index}].{field} must be non-empty")
                if not _non_empty_text(unit.get("expected_result")):
                    errors.append(f"product_creation_plan.work_units[{index}].expected_result is required")
    errors.extend(_product_delivery_quality_profile_ref_errors(card))
    profile = _product_delivery_quality_profile(card)
    if profile:
        errors.extend(validate_product_delivery_quality_profile(profile))
    context = card.get("product_context_packet") if isinstance(card.get("product_context_packet"), dict) else {}
    if context and context.get("stale") is True:
        errors.append("product_context_packet is stale and must be refreshed before implementation")
    readiness = card.get("product_implementation_readiness") if isinstance(card.get("product_implementation_readiness"), dict) else {}
    if readiness:
        result = str(readiness.get("artifact_alignment_result") or "").strip().upper()
        if result in {"FAIL", "BLOCKED"}:
            errors.append("product_implementation_readiness.artifact_alignment_result blocks material implementation")
        if result == "PASS" and not _non_empty_string_list(readiness.get("ready_work_units")):
            errors.append("product_implementation_readiness PASS requires ready_work_units")
        required_readiness_proofs = _required_domain_proof_ids(card, "before_implementation")
        if required_readiness_proofs:
            proof_profile = profile or {
                "waiver_policy": {
                    "allowed": True,
                    "requires_owner": True,
                    "requires_reason": True,
                    "cannot_claim_full_acceptance": True,
                }
            }
            if not _non_empty_string_list(readiness.get("product_delivery_quality_profile_trace")):
                errors.append("product_implementation_readiness.product_delivery_quality_profile_trace must be non-empty")
            errors.extend(
                _validate_delivery_profile_proof_coverage(
                    readiness.get("delivery_profile_proof_coverage"),
                    required_readiness_proofs,
                    at="product_implementation_readiness.delivery_profile_proof_coverage",
                    profile=proof_profile,
                    full_acceptance=False,
                )
            )
    return errors


def validate_production_promotion_ladder_contract(card: dict[str, Any]) -> list[str]:
    if card.get("factory_method_version") != "OVERKILL_VFINAL":
        return []
    if not _production_ladder_required(card):
        return []
    errors: list[str] = []
    if not _has_ref_or_object(card, "production_promotion_ladder"):
        errors.append("production_promotion_ladder or production_promotion_ladder_ref is required for production-intent products")
    readiness = card.get("production_readiness_plan") if isinstance(card.get("production_readiness_plan"), dict) else {}
    if readiness and not _non_empty_text(readiness.get("production_promotion_ladder_ref")):
        errors.append("production_readiness_plan.production_promotion_ladder_ref is required")

    ladder = card.get("production_promotion_ladder") if isinstance(card.get("production_promotion_ladder"), dict) else {}
    if ladder:
        environments = ladder.get("environments")
        if not isinstance(environments, list) or not environments:
            errors.append("production_promotion_ladder.environments must be non-empty")
        else:
            env_names = {str(item.get("environment") or "").strip().lower() for item in environments if isinstance(item, dict)}
            if "production" in env_names and "local" not in env_names:
                errors.append("production_promotion_ladder must include local proof before production")
            if normalized_surfaces(card) & ONCHAIN_SURFACES:
                for required_env in ("local", "devnet", "mainnet"):
                    if required_env not in env_names:
                        errors.append(f"onchain production ladder must include {required_env}")
                policy = ladder.get("onchain_policy") if isinstance(ladder.get("onchain_policy"), dict) else {}
                if policy.get("mainnet_authority_requires_human_gate") is not True:
                    errors.append("onchain production ladder requires human mainnet authority policy")
                if policy.get("post_mainnet_smoke_required") is not True:
                    errors.append("onchain production ladder requires post-mainnet smoke policy")
        promotion_policy = ladder.get("promotion_policy") if isinstance(ladder.get("promotion_policy"), dict) else {}
        if promotion_policy.get("preproduction_proof_cannot_claim_production") is not True:
            errors.append("production_promotion_ladder must forbid preproduction proof from claiming production readiness")
        if promotion_policy.get("retest_after_promotion") is not True:
            errors.append("production_promotion_ladder must require retest_after_promotion")
    return errors


def _contains_internal_coordination_request(text: Any) -> bool:
    normalized = str(text or "").strip().lower()
    return any(term in normalized for term in INTERNAL_COORDINATION_TERMS)


def validate_user_facing_autonomy_contract(card: dict[str, Any]) -> list[str]:
    contract = card.get("user_facing_autonomy_contract")
    if not isinstance(contract, dict):
        return []

    errors: list[str] = []
    if contract.get("record_type") not in (None, "user_facing_autonomy_contract"):
        errors.append("user_facing_autonomy_contract.record_type must be user_facing_autonomy_contract")

    allowed_classes = set(_list_items(contract.get("allowed_user_question_classes")))
    if "discoverable" in allowed_classes:
        errors.append("user_facing_autonomy_contract.allowed_user_question_classes must not include discoverable")
    unknown_classes = allowed_classes - ALLOWED_USER_QUESTION_CLASSES
    if unknown_classes:
        errors.append("user_facing_autonomy_contract.allowed_user_question_classes contains unknown classes: " + ", ".join(sorted(unknown_classes)))

    factory_owns = " ".join(_list_items(contract.get("factory_owns"))).lower()
    for required in ("source resolution", "method routing", "execution routing", "verification"):
        if required not in factory_owns:
            errors.append(f"user_facing_autonomy_contract.factory_owns must include {required}")

    user_must_not_do = " ".join(_list_items(contract.get("user_must_not_do"))).lower()
    if "worker" not in user_must_not_do or "schema" not in user_must_not_do:
        errors.append("user_facing_autonomy_contract.user_must_not_do must keep worker/schema coordination inside the factory")

    for index, question in enumerate(contract.get("user_questions", []) if isinstance(contract.get("user_questions"), list) else []):
        if not isinstance(question, dict):
            errors.append(f"user_facing_autonomy_contract.user_questions[{index}] must be an object")
            continue
        question_class = str(question.get("class") or "").strip()
        if question_class not in USER_QUESTION_CLASSES:
            errors.append(f"user_facing_autonomy_contract.user_questions[{index}].class is unknown")
        if question_class == "discoverable":
            errors.append(f"user_facing_autonomy_contract.user_questions[{index}] is discoverable and must be resolved by the factory before asking the user")
        if _contains_internal_coordination_request(question.get("question")):
            errors.append(f"user_facing_autonomy_contract.user_questions[{index}] asks the user to perform internal factory coordination")
        if not _non_empty_text(question.get("factory_resolution_path")):
            errors.append(f"user_facing_autonomy_contract.user_questions[{index}].factory_resolution_path is required")

    return errors


def _status_value(value: Any) -> str:
    if isinstance(value, dict):
        return str(value.get("status") or "").strip().lower()
    return str(value or "").strip().lower()


def _execution_mode(card: dict[str, Any]) -> str:
    autonomy = card.get("autonomy_readiness_packet") if isinstance(card.get("autonomy_readiness_packet"), dict) else {}
    hardening = card.get("agent_runtime_hardening_profile") if isinstance(card.get("agent_runtime_hardening_profile"), dict) else {}
    runtime = card.get("runtime_contract") if isinstance(card.get("runtime_contract"), dict) else {}
    for source in (autonomy, hardening, runtime):
        value = str(source.get("execution_mode") or source.get("mode") or "").strip()
        if value:
            return value
    return ""


def _tool_surfaces_from(card: dict[str, Any]) -> set[str]:
    surfaces: set[str] = set()
    for source_name in ("agent_runtime_hardening_profile", "runtime_contract"):
        source = card.get(source_name) if isinstance(card.get(source_name), dict) else {}
        for key in ("tool_surface", "tool_surfaces"):
            value = source.get(key)
            if isinstance(value, list):
                surfaces.update(item.lower() for item in _list_items(value))
            elif _non_empty_text(value):
                surfaces.add(str(value).strip().lower())
    return surfaces


def _has_human_gate_ref(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_non_empty_text(value.get(field)) for field in ("gate_ref", "reviewer_or_human_gate_ref"))
    if isinstance(value, list):
        return bool(_list_items(value))
    return _non_empty_text(value)


def _contains_forbidden_secret_key(value: Any) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            if str(key).strip().lower() in SECRET_POLICY_FORBIDDEN_KEYS:
                return True
            if _contains_forbidden_secret_key(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_forbidden_secret_key(item) for item in value)
    return False


def validate_secret_delivery_policy(policy: Any, *, material_execution: bool) -> list[str]:
    if not isinstance(policy, dict):
        if material_execution:
            return ["secret_delivery_policy is required for material autonomous execution"]
        return []

    errors: list[str] = []
    mode = str(policy.get("delivery_mode") or "").strip()
    sensitivity = str(policy.get("sensitivity") or "").strip()
    environment = str(policy.get("environment") or "").strip()

    for field in (
        "secret_type",
        "sensitivity",
        "environment",
        "delivery_mode",
        "scope",
        "ttl_or_expiry",
        "rotation_policy",
        "audit_log_ref",
        "redaction_policy",
        "revocation_path",
    ):
        if not _non_empty_text(policy.get(field)):
            errors.append(f"secret_delivery_policy.{field} is required")
    if not isinstance(policy.get("allowed_worker_ids"), list) or not _list_items(policy.get("allowed_worker_ids")):
        errors.append("secret_delivery_policy.allowed_worker_ids must name scoped workers")
    if not isinstance(policy.get("forbidden_exposure"), list) or not _list_items(policy.get("forbidden_exposure")):
        errors.append("secret_delivery_policy.forbidden_exposure must name forbidden exposure channels")
    if not isinstance(policy.get("evidence_refs"), list) or not _list_items(policy.get("evidence_refs")):
        errors.append("secret_delivery_policy.evidence_refs must include public-safe refs")
    if _contains_forbidden_secret_key(policy):
        errors.append("secret_delivery_policy must contain refs and policy only, never raw secret values or private secret paths")

    if mode in SECRET_DELIVERY_FORBIDDEN_MODES:
        errors.append("secret_delivery_policy.delivery_mode prompt_context is always forbidden")
    elif mode in SECRET_DELIVERY_EXCEPTION_MODES:
        waiver = policy.get("human_gated_waiver")
        has_waiver = isinstance(waiver, dict) and _has_human_gate_ref(waiver) and bool(_list_items(waiver.get("compensating_controls")))
        if not has_waiver:
            errors.append(
                f"secret_delivery_policy.delivery_mode {mode} requires explicit human-gated waiver with compensating controls"
            )
    elif mode not in SECRET_DELIVERY_SAFE_MODES:
        errors.append("secret_delivery_policy.delivery_mode is not recognized")

    if material_execution and sensitivity in {"high", "critical"} and environment in {"production", "mainnet"}:
        if mode in {"none", "placeholder", "simulator"}:
            errors.append("real production/mainnet secrets cannot use none, placeholder or simulator mode")
        if policy.get("human_gate_required") is not True and mode not in {"jit_broker", "vault_jit", "hardware_signer", "external_service", "user-mediated"}:
            errors.append("sensitive production/mainnet secret use requires a human gate or safe delegated delivery mode")
    return errors


def validate_agent_runtime_hardening_profile(card: dict[str, Any]) -> list[str]:
    execution_mode = _execution_mode(card)
    material_execution = execution_mode in HARDENING_REQUIRED_EXECUTION_MODES
    tool_surfaces = _tool_surfaces_from(card)
    profile = card.get("agent_runtime_hardening_profile")
    autonomy = card.get("autonomy_readiness_packet") if isinstance(card.get("autonomy_readiness_packet"), dict) else {}
    secret_policy = card.get("secret_delivery_policy")
    errors: list[str] = []

    if not material_execution and not tool_surfaces:
        return validate_secret_delivery_policy(secret_policy, material_execution=False)

    if not isinstance(profile, dict):
        if material_execution or tool_surfaces & TOOL_USING_SURFACES:
            errors.append("agent_runtime_hardening_profile required for tool-using material execution")
        errors.extend(validate_secret_delivery_policy(secret_policy, material_execution=material_execution))
        return errors

    required_text_fields = (
        "worker_id",
        "runtime_kind",
        "execution_mode",
        "filesystem_scope",
        "network_scope",
        "credential_exposure",
        "secret_delivery_policy_ref",
        "side_effect_policy",
        "sandbox_boundary",
        "identity_boundary",
        "log_policy",
        "egress_policy",
        "mutation_policy",
        "rollback_or_kill_switch",
    )
    for field in required_text_fields:
        if not _non_empty_text(profile.get(field)):
            errors.append(f"agent_runtime_hardening_profile.{field} is required")
    for field in ("tool_surface", "human_gate_triggers", "validation_commands", "evidence_refs"):
        if not isinstance(profile.get(field), list) or not _list_items(profile.get(field)):
            errors.append(f"agent_runtime_hardening_profile.{field} must be a non-empty array")
    if not isinstance(profile.get("resource_limits"), dict) or not profile.get("resource_limits"):
        errors.append("agent_runtime_hardening_profile.resource_limits must be a non-empty object")

    profile_mode = str(profile.get("execution_mode") or "").strip()
    if material_execution and profile_mode != execution_mode:
        errors.append("agent_runtime_hardening_profile.execution_mode must match autonomy readiness execution_mode")

    filesystem_scope = str(profile.get("filesystem_scope") or "").strip()
    network_scope = str(profile.get("network_scope") or "").strip()
    human_gate_triggers = _list_items(profile.get("human_gate_triggers"))
    if filesystem_scope in WIDE_FILESYSTEM_SCOPES and not human_gate_triggers:
        errors.append("agent_runtime_hardening_profile wide filesystem scope requires human_gate_triggers")
    if network_scope in WIDE_NETWORK_SCOPES and not human_gate_triggers:
        errors.append("agent_runtime_hardening_profile unrestricted network requires human_gate_triggers")

    profile_tools = {item.lower() for item in _list_items(profile.get("tool_surface"))}
    if profile_tools & TOOL_USING_SURFACES and not _list_items(profile.get("blocked_abuse_evidence_refs")):
        errors.append("agent_runtime_hardening_profile.blocked_abuse_evidence_refs required for tool-using workers")

    if material_execution:
        if not _non_empty_text(autonomy.get("runtime_hardening_profile_ref")):
            errors.append("autonomy_readiness_packet.runtime_hardening_profile_ref required for material execution")
        if not _non_empty_text(autonomy.get("secret_delivery_policy_ref")):
            errors.append("autonomy_readiness_packet.secret_delivery_policy_ref required for material execution")
        if not _non_empty_text(autonomy.get("secret_delivery_mode")):
            errors.append("autonomy_readiness_packet.secret_delivery_mode required for material execution")
        if not isinstance(autonomy.get("runtime_hardening_evidence_refs"), list) or not _list_items(autonomy.get("runtime_hardening_evidence_refs")):
            errors.append("autonomy_readiness_packet.runtime_hardening_evidence_refs required for material execution")

    errors.extend(validate_secret_delivery_policy(secret_policy, material_execution=material_execution))
    return errors


def _card_parallel_execution_requested(card: dict[str, Any]) -> bool:
    runtime_contract = card.get("runtime_contract") if isinstance(card.get("runtime_contract"), dict) else {}
    loop_plan = card.get("loop_plan") if isinstance(card.get("loop_plan"), dict) else {}
    return any(
        value is True
        for value in (
            card.get("parallel_execution_requested"),
            runtime_contract.get("parallel_execution_requested"),
            runtime_contract.get("parallel_execution"),
            loop_plan.get("parallel_execution_requested"),
        )
    )


def _lane_write_scope(lane: dict[str, Any]) -> list[str]:
    scope = _list_items(lane.get("write_scope"))
    if scope:
        return scope
    return _list_items(lane.get("intended_write_scope"))


def _lane_is_editing(lane: dict[str, Any]) -> bool:
    lane_kind = str(lane.get("lane_kind") or "").strip().lower()
    write_scope = [item.lower() for item in _lane_write_scope(lane)]
    return lane_kind in PARALLEL_EDIT_LANE_KINDS or any(item not in {"none", "read-only", "readonly"} for item in write_scope)


def validate_parallel_lane_contract(lane: dict[str, Any], *, at: str = "parallel_lane_contract") -> list[str]:
    errors: list[str] = []
    required_fields = [
        "lane_id",
        "objective",
        "read_scope",
        "write_scope",
        "worktree_ref",
        "owner_agent",
        "reviewer_or_synthesizer",
        "expected_artifact",
        "timeout",
        "budget",
        "stop_condition",
        "conflict_risk",
        "merge_reconciliation_policy",
        "cleanup_policy",
    ]
    for field in required_fields:
        value = lane.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"{at}.{field} must be a non-empty array")
        elif isinstance(value, dict):
            if not value:
                errors.append(f"{at}.{field} must be a non-empty object")
        elif not _non_empty_text(value):
            errors.append(f"{at}.{field} is required")

    if _lane_is_editing(lane):
        worktree_ref = str(lane.get("worktree_ref") or "").strip()
        base_ref = str(lane.get("base_ref") or "").strip()
        if not worktree_ref:
            errors.append(f"{at}.worktree_ref is required for editing lanes")
        if worktree_ref and base_ref and worktree_ref == base_ref:
            errors.append(f"{at}.worktree_ref must differ from base_ref for editing lanes")
        if not _lane_write_scope(lane):
            errors.append(f"{at}.write_scope is required for editing lanes")

    budget = lane.get("budget") if isinstance(lane.get("budget"), dict) else {}
    if budget:
        if not isinstance(budget.get("token_budget"), int) or budget.get("token_budget", 0) <= 0:
            errors.append(f"{at}.budget.token_budget must be a positive integer")
        if not _non_empty_text(budget.get("cost_budget")):
            errors.append(f"{at}.budget.cost_budget is required")
        if budget.get("approval_required_above_budget") is not True:
            errors.append(f"{at}.budget.approval_required_above_budget must be true")

    merge_policy = lane.get("merge_reconciliation_policy") if isinstance(lane.get("merge_reconciliation_policy"), dict) else {}
    if merge_policy and merge_policy.get("no_self_promotion") is not True:
        errors.append(f"{at}.merge_reconciliation_policy.no_self_promotion must be true")
    if merge_policy and not _non_empty_text(merge_policy.get("synthesizer")):
        errors.append(f"{at}.merge_reconciliation_policy.synthesizer is required")

    return errors


def parallel_lane_warnings(lanes: list[dict[str, Any]]) -> list[str]:
    warnings: list[str] = []
    write_owners: dict[str, str] = {}
    for lane in lanes:
        lane_id = str(lane.get("lane_id") or "unknown-lane")
        for scope in _lane_write_scope(lane):
            normalized = scope.strip().replace("\\", "/").rstrip("/")
            if not normalized or normalized.lower() in {"none", "read-only", "readonly"}:
                continue
            previous = write_owners.get(normalized)
            if previous and previous != lane_id:
                warnings.append(f"parallel lane write scope overlap: {previous} and {lane_id} both write {normalized}")
            else:
                write_owners[normalized] = lane_id
    return warnings


def card_parallel_lane_contracts(card: dict[str, Any]) -> list[dict[str, Any]]:
    raw = card.get("parallel_lane_contracts")
    if not isinstance(raw, list):
        return []
    return [item for item in raw if isinstance(item, dict)]


def normalized_surfaces(card: dict[str, Any]) -> set[str]:
    raw = card.get("surfaces", [])
    if not isinstance(raw, list):
        return set()
    return {str(value).strip().lower() for value in raw if str(value).strip()}


def risk(card: dict[str, Any]) -> str:
    return str(card.get("risk_effective", "")).strip().upper()


def strict_product_experience_required(card: dict[str, Any]) -> bool:
    return card.get("factory_method_version") == "OVERKILL_VFINAL" or isinstance(card.get("product_experience_plan"), dict)


def product_experience_surface_required(card: dict[str, Any]) -> bool:
    surfaces = normalized_surfaces(card)
    if surfaces & PRODUCT_FACE_SURFACES:
        return True
    if card.get("factory_method_version") == "OVERKILL_VFINAL" and surfaces & PRODUCT_EXPERIENCE_SURFACES:
        return True
    return card.get("product_face_result_required") is True


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


def validate_product_delivery_quality_profile(profile: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in PRODUCT_DELIVERY_QUALITY_PROFILE_REQUIRED_FIELDS:
        value = profile.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"product_delivery_quality_profile.{field} must be a non-empty array")
        elif isinstance(value, dict):
            if not value:
                errors.append(f"product_delivery_quality_profile.{field} must be a non-empty object")
        elif not _non_empty_text(value):
            errors.append(f"product_delivery_quality_profile.{field} is required")

    if profile.get("record_type") not in (None, "product_delivery_quality_profile"):
        errors.append("product_delivery_quality_profile.record_type must be product_delivery_quality_profile")

    seen_proofs: set[str] = set()
    for index, proof in enumerate(profile.get("required_proofs", []) if isinstance(profile.get("required_proofs"), list) else []):
        if not isinstance(proof, dict):
            errors.append(f"product_delivery_quality_profile.required_proofs[{index}] must be an object")
            continue
        proof_id = str(proof.get("proof_id") or "").strip()
        if not proof_id:
            errors.append(f"product_delivery_quality_profile.required_proofs[{index}].proof_id is required")
        elif proof_id in seen_proofs:
            errors.append(f"product_delivery_quality_profile.required_proofs[{index}].proof_id duplicates {proof_id!r}")
        seen_proofs.add(proof_id)
        for field in ("name", "owner_worker", "reviewer_role", "evidence_kind"):
            if not _non_empty_text(proof.get(field)):
                errors.append(f"product_delivery_quality_profile.required_proofs[{index}].{field} is required")
        required_at = _list_items(proof.get("required_at"))
        if not required_at:
            errors.append(f"product_delivery_quality_profile.required_proofs[{index}].required_at must be non-empty")
        for phase in required_at:
            if phase not in {"before_implementation", "before_completion", "before_promotion"}:
                errors.append(f"product_delivery_quality_profile.required_proofs[{index}].required_at has unknown phase {phase!r}")

    for index, dimension in enumerate(profile.get("quality_dimensions", []) if isinstance(profile.get("quality_dimensions"), list) else []):
        if not isinstance(dimension, dict):
            errors.append(f"product_delivery_quality_profile.quality_dimensions[{index}] must be an object")
            continue
        for field in ("dimension_id", "bar"):
            if not _non_empty_text(dimension.get(field)):
                errors.append(f"product_delivery_quality_profile.quality_dimensions[{index}].{field} is required")
        if not _non_empty_string_list(dimension.get("block_when")):
            errors.append(f"product_delivery_quality_profile.quality_dimensions[{index}].block_when must be non-empty")

    waiver = profile.get("waiver_policy") if isinstance(profile.get("waiver_policy"), dict) else {}
    if waiver:
        for field in ("allowed", "requires_owner", "requires_reason", "cannot_claim_full_acceptance"):
            if field not in waiver:
                errors.append(f"product_delivery_quality_profile.waiver_policy.{field} is required")
    return errors


def _product_delivery_quality_profile(card: dict[str, Any]) -> dict[str, Any]:
    containers: list[dict[str, Any]] = [card]
    for field in (
        "product_creation_plan",
        "product_implementation_readiness",
        "product_experience_plan",
        "product_face_packet",
    ):
        value = card.get(field)
        if isinstance(value, dict):
            containers.append(value)
    for container in containers:
        profile = container.get("product_delivery_quality_profile")
        if isinstance(profile, dict):
            return profile
    for container in containers:
        profile = _load_repo_local_json_ref(container.get("product_delivery_quality_profile_ref"))
        if profile:
            return profile
    return {}


def _product_delivery_quality_profile_ref_errors(card: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    refs: list[tuple[str, str]] = []
    containers: list[tuple[str, dict[str, Any]]] = [("card", card)]
    for field in (
        "product_creation_plan",
        "product_implementation_readiness",
        "product_experience_plan",
        "product_face_packet",
    ):
        value = card.get(field)
        if isinstance(value, dict):
            containers.append((field, value))
    for label, container in containers:
        ref = container.get("product_delivery_quality_profile_ref")
        if _non_empty_text(ref):
            refs.append((label, str(ref).strip()))

    seen: set[str] = set()
    for label, ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        path = _repo_local_json_ref_path(ref)
        if path is None:
            continue
        if not path.is_file():
            errors.append(f"{label}.product_delivery_quality_profile_ref does not resolve to a repo-local file: {ref}")
            continue
        try:
            profile = load_json_like(path)
        except Exception as exc:
            errors.append(
                f"{label}.product_delivery_quality_profile_ref could not be loaded as JSON object: {type(exc).__name__}"
            )
            continue
        errors.extend(validate_product_delivery_quality_profile(profile))
    return errors


def _delivery_profile_required_proof_ids(profile: dict[str, Any], phase: str) -> list[str]:
    proof_ids: list[str] = []
    for proof in profile.get("required_proofs", []) if isinstance(profile.get("required_proofs"), list) else []:
        if not isinstance(proof, dict):
            continue
        if phase in _list_items(proof.get("required_at")) and _non_empty_text(proof.get("proof_id")):
            proof_ids.append(str(proof["proof_id"]).strip())
    return sorted(set(proof_ids))


def _activated_capability_pack_structured_proof_ids(card: dict[str, Any]) -> list[str]:
    contract = card.get("capability_pack_contract")
    if not isinstance(contract, dict):
        return []
    if str(contract.get("status") or "").strip().lower() != "activated":
        return []

    proof_ids: set[str] = set(_list_items(contract.get("structured_proofs_required")))
    packs = load_capability_packs()
    for pack_id in _activated_capability_pack_ids(contract):
        proof_ids.update(_pack_structured_proof_ids(packs.get(pack_id, {})))
    return sorted(proof_id for proof_id in proof_ids if proof_id)


def _required_domain_proof_ids(card: dict[str, Any], phase: str) -> list[str]:
    proof_ids: list[str] = []
    profile = _product_delivery_quality_profile(card)
    if profile:
        proof_ids.extend(_delivery_profile_required_proof_ids(profile, phase))
    if phase in {"before_implementation", "before_completion", "before_promotion"}:
        proof_ids.extend(_activated_capability_pack_structured_proof_ids(card))
    plan = card.get("product_experience_plan") if isinstance(card.get("product_experience_plan"), dict) else {}
    packet = card.get("product_face_packet") if isinstance(card.get("product_face_packet"), dict) else {}
    if phase == "before_completion":
        proof_ids.extend(_list_items(plan.get("domain_proof_required")))
        proof_ids.extend(_list_items(packet.get("domain_proof_required")))
    return sorted({proof_id for proof_id in proof_ids if proof_id})


def _validate_delivery_profile_proof_coverage(
    coverage: Any,
    required_proof_ids: list[str],
    *,
    at: str,
    profile: dict[str, Any],
    full_acceptance: bool,
) -> list[str]:
    errors: list[str] = []
    if not required_proof_ids:
        return errors
    if not isinstance(coverage, list) or not coverage:
        errors.append(f"{at} missing product delivery proof coverage for required proof ids: " + ", ".join(required_proof_ids))
        return errors

    by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(coverage):
        if not isinstance(item, dict):
            errors.append(f"{at}[{index}] must be an object")
            continue
        proof_id = str(item.get("proof_id") or "").strip()
        if not proof_id:
            errors.append(f"{at}[{index}].proof_id is required")
            continue
        by_id[proof_id] = item
        status = str(item.get("status") or "").strip().upper()
        if status not in DOMAIN_PROOF_ALLOWED_STATUSES:
            errors.append(f"{at}[{index}].status must be PASS, WARN, FAIL or WAIVED")
        if not _non_empty_string_list(item.get("evidence_refs")):
            errors.append(f"{at}[{index}].evidence_refs must be non-empty")
        if not _non_empty_text(item.get("basis")):
            errors.append(f"{at}[{index}].basis is required")
        if status == "WAIVED":
            waiver = profile.get("waiver_policy") if isinstance(profile.get("waiver_policy"), dict) else {}
            if waiver.get("allowed") is not True:
                errors.append(f"{at}[{index}] cannot waive proof {proof_id!r}; profile waiver_policy.allowed is not true")
            if waiver.get("requires_owner") is True and not _non_empty_text(item.get("waiver_owner")):
                errors.append(f"{at}[{index}].waiver_owner is required for WAIVED proof")
            if waiver.get("requires_reason") is True and not _non_empty_text(item.get("waiver_reason")):
                errors.append(f"{at}[{index}].waiver_reason is required for WAIVED proof")
            if full_acceptance and waiver.get("cannot_claim_full_acceptance") is True:
                errors.append(f"{at}[{index}] WAIVED proof cannot support full product acceptance")
        elif status != "PASS":
            errors.append(f"{at}[{index}] required proof {proof_id!r} must PASS before this gate")

    missing = [proof_id for proof_id in required_proof_ids if proof_id not in by_id]
    if missing:
        errors.append(f"{at} missing required product delivery proof ids: " + ", ".join(missing))
    return errors


def validate_reference_quality_packet(packet: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REFERENCE_QUALITY_REQUIRED_FIELDS:
        value = packet.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"reference_quality_packet.{field} must be a non-empty array")
        elif isinstance(value, dict):
            if not value:
                errors.append(f"reference_quality_packet.{field} must be a non-empty object")
        elif not _non_empty_text(value):
            errors.append(f"reference_quality_packet.{field} is required")

    if packet.get("record_type") not in (None, "reference_quality_packet"):
        errors.append("reference_quality_packet.record_type must be reference_quality_packet")

    for idx, ref in enumerate(packet.get("references", []) if isinstance(packet.get("references"), list) else []):
        if not isinstance(ref, dict):
            errors.append(f"reference_quality_packet.references[{idx}] must be an object")
            continue
        for field in ("source_id", "source_url_or_ref", "use_type", "what_to_learn", "copy_policy"):
            value = ref.get(field)
            if isinstance(value, list):
                if not _list_items(value):
                    errors.append(f"reference_quality_packet.references[{idx}].{field} must be a non-empty array")
            elif not _non_empty_text(value):
                errors.append(f"reference_quality_packet.references[{idx}].{field} is required")
        if ref.get("copy_policy") == "copy_only_with_license_recorded" and not _non_empty_text(ref.get("license_or_terms_ref")):
            errors.append(f"reference_quality_packet.references[{idx}].license_or_terms_ref is required for copied code/assets")
        if str(ref.get("copy_policy") or "").strip().lower() in {"copy", "blind_copy"}:
            errors.append(f"reference_quality_packet.references[{idx}].copy_policy must not allow blind copying")

    reuse = packet.get("reuse_policy") if isinstance(packet.get("reuse_policy"), dict) else {}
    forbidden = " ".join(_list_items(reuse.get("forbidden"))).lower()
    if "blind copy" not in forbidden and "unlicensed" not in forbidden:
        errors.append("reference_quality_packet.reuse_policy.forbidden must ban blind copy or unlicensed reuse")
    if reuse and reuse.get("license_required_for_code_or_assets") is not True:
        errors.append("reference_quality_packet.reuse_policy.license_required_for_code_or_assets must be true")
    return errors


def validate_professional_design_process(process: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in PROFESSIONAL_DESIGN_PROCESS_REQUIRED_FIELDS:
        value = process.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"professional_design_process.{field} must be a non-empty array")
        elif isinstance(value, dict):
            if not value:
                errors.append(f"professional_design_process.{field} must be a non-empty object")
        elif not _non_empty_text(value):
            errors.append(f"professional_design_process.{field} is required")

    if process.get("record_type") not in (None, "professional_design_process"):
        errors.append("professional_design_process.record_type must be professional_design_process")

    brief = process.get("design_brief") if isinstance(process.get("design_brief"), dict) else {}
    for field in ("user", "job_to_be_done", "decision_surface", "success_signal"):
        if not _non_empty_text(brief.get(field)):
            errors.append(f"professional_design_process.design_brief.{field} is required")
    if len(_list_items(brief.get("failure_risks"))) < 2:
        errors.append("professional_design_process.design_brief.failure_risks requires at least 2 risks")

    tasks = process.get("task_map") if isinstance(process.get("task_map"), list) else []
    if len(tasks) < 3:
        errors.append("professional_design_process.task_map requires at least 3 user/system tasks")
    for index, task in enumerate(tasks):
        if not isinstance(task, dict):
            errors.append(f"professional_design_process.task_map[{index}] must be an object")
            continue
        for field in ("task_id", "user_goal", "trigger", "success_signal", "failure_state"):
            if not _non_empty_text(task.get(field)):
                errors.append(f"professional_design_process.task_map[{index}].{field} is required")

    research = process.get("reference_research") if isinstance(process.get("reference_research"), dict) else {}
    sources = research.get("sources") if isinstance(research.get("sources"), list) else []
    library_searches = research.get("library_searches") if isinstance(research.get("library_searches"), list) else []
    rejected_references = (
        research.get("rejected_references") if isinstance(research.get("rejected_references"), list) else []
    )
    if len(sources) < 3:
        errors.append("professional_design_process.reference_research.sources requires at least 3 sources")
    if len(_list_items(research.get("registry_refs"))) < 2:
        errors.append("professional_design_process.reference_research.registry_refs requires at least 2 registry refs")
    if not _non_empty_text(research.get("selection_rationale")):
        errors.append("professional_design_process.reference_research.selection_rationale is required")
    if len(library_searches) < 2:
        errors.append("professional_design_process.reference_research.library_searches requires at least 2 library searches")
    for index, search in enumerate(library_searches):
        if not isinstance(search, dict):
            errors.append(f"professional_design_process.reference_research.library_searches[{index}] must be an object")
            continue
        for field in ("library", "library_url", "query_or_category", "searched_at"):
            if not _non_empty_text(search.get(field)):
                errors.append(f"professional_design_process.reference_research.library_searches[{index}].{field} is required")
        if len(_list_items(search.get("selection_criteria"))) < 2:
            errors.append(
                f"professional_design_process.reference_research.library_searches[{index}].selection_criteria requires at least 2 items"
            )
        candidate_count = search.get("candidate_count")
        if not isinstance(candidate_count, int) or candidate_count < 3:
            errors.append(
                f"professional_design_process.reference_research.library_searches[{index}].candidate_count must be at least 3"
            )
        if not _list_items(search.get("selected_source_ids")):
            errors.append(
                f"professional_design_process.reference_research.library_searches[{index}].selected_source_ids is required"
            )
        if not _list_items(search.get("rejected_candidate_ids")):
            errors.append(
                f"professional_design_process.reference_research.library_searches[{index}].rejected_candidate_ids is required"
            )

    source_types: set[str] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"professional_design_process.reference_research.sources[{index}] must be an object")
            continue
        for field in (
            "source_id",
            "source_url_or_ref",
            "source_type",
            "library_source",
            "use_type",
            "candidate_reason",
            "copy_policy",
            "license_or_terms_ref",
        ):
            if not _non_empty_text(source.get(field)):
                errors.append(f"professional_design_process.reference_research.sources[{index}].{field} is required")
        source_type = str(source.get("source_type") or "").strip()
        if source_type:
            source_types.add(source_type)
            if source_type not in REFERENCE_RESEARCH_SOURCE_TYPES:
                errors.append(
                    f"professional_design_process.reference_research.sources[{index}].source_type must be a known design reference type"
                )
        if len(_list_items(source.get("what_to_learn"))) < 2:
            errors.append(f"professional_design_process.reference_research.sources[{index}].what_to_learn requires at least 2 items")
        if len(_list_items(source.get("extracted_patterns"))) < 2:
            errors.append(f"professional_design_process.reference_research.sources[{index}].extracted_patterns requires at least 2 items")
        if len(_list_items(source.get("selected_patterns"))) < 2:
            errors.append(
                f"professional_design_process.reference_research.sources[{index}].selected_patterns requires at least 2 items"
            )
        if len(_list_items(source.get("visual_dimensions_covered"))) < 3:
            errors.append(
                f"professional_design_process.reference_research.sources[{index}].visual_dimensions_covered requires at least 3 items"
            )
        if str(source.get("copy_policy") or "").strip().lower() in {"copy", "blind_copy"}:
            errors.append(f"professional_design_process.reference_research.sources[{index}].copy_policy must not allow blind copying")
    if not source_types & REFERENCE_RESEARCH_LIBRARY_TYPES:
        errors.append("professional_design_process.reference_research.sources requires at least one design library, component registry, site gallery or user-flow library source")
    if len(source_types) < 2:
        errors.append("professional_design_process.reference_research.sources requires at least 2 distinct source types")

    if len(rejected_references) < 2:
        errors.append("professional_design_process.reference_research.rejected_references requires at least 2 rejected candidates")
    for index, rejected in enumerate(rejected_references):
        if not isinstance(rejected, dict):
            errors.append(f"professional_design_process.reference_research.rejected_references[{index}] must be an object")
            continue
        for field in ("source_id", "source_url_or_ref", "rejection_reason"):
            if not _non_empty_text(rejected.get(field)):
                errors.append(f"professional_design_process.reference_research.rejected_references[{index}].{field} is required")

    synthesis = research.get("pattern_synthesis") if isinstance(research.get("pattern_synthesis"), dict) else {}
    for field in REFERENCE_COMPARISON_DIMENSIONS:
        if not _non_empty_text(synthesis.get(field)):
            errors.append(f"professional_design_process.reference_research.pattern_synthesis.{field} is required")

    evidence_policy = (
        research.get("reference_evidence_policy") if isinstance(research.get("reference_evidence_policy"), dict) else {}
    )
    for field in (
        "capture_required_before_implementation",
        "side_by_side_comparison_required_before_pass",
        "public_refs_only",
        "no_private_screenshots_in_repo",
    ):
        if evidence_policy.get(field) is not True:
            errors.append(f"professional_design_process.reference_research.reference_evidence_policy.{field} must be true")

    architecture = process.get("ux_architecture") if isinstance(process.get("ux_architecture"), dict) else {}
    for field in ("information_hierarchy", "navigation_model", "state_model", "density_rationale"):
        value = architecture.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"professional_design_process.ux_architecture.{field} must be a non-empty array")
        elif not _non_empty_text(value):
            errors.append(f"professional_design_process.ux_architecture.{field} is required")

    for field in ("wireframe_gate", "prototype_gate"):
        gate = process.get(field) if isinstance(process.get(field), dict) else {}
        if gate.get("status") != "PASS":
            errors.append(f"professional_design_process.{field}.status must be PASS before product-facing implementation")
        if not _non_empty_text(gate.get("reviewer")):
            errors.append(f"professional_design_process.{field}.reviewer is required")
        if not _list_items(gate.get("artifact_refs")):
            errors.append(f"professional_design_process.{field}.artifact_refs must be a non-empty array")
        if not _non_empty_text(gate.get("basis")):
            errors.append(f"professional_design_process.{field}.basis is required")

    visual_direction = process.get("visual_direction") if isinstance(process.get("visual_direction"), dict) else {}
    for field in ("typography", "spacing", "color_semantics", "component_model", "anti_generic_commitments"):
        value = visual_direction.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"professional_design_process.visual_direction.{field} must be a non-empty array")
        elif not _non_empty_text(value):
            errors.append(f"professional_design_process.visual_direction.{field} is required")

    qa_plan = process.get("design_qa_plan") if isinstance(process.get("design_qa_plan"), dict) else {}
    for field in ("viewports", "accessibility_checks", "performance_checks", "screenshot_requirements"):
        if not _list_items(qa_plan.get(field)):
            errors.append(f"professional_design_process.design_qa_plan.{field} must be a non-empty array")
    for field in ("console_check_required", "overlap_check_required"):
        if qa_plan.get(field) is not True:
            errors.append(f"professional_design_process.design_qa_plan.{field} must be true")

    comparative = process.get("comparative_review_gate") if isinstance(process.get("comparative_review_gate"), dict) else {}
    if comparative.get("status") != "PASS":
        errors.append("professional_design_process.comparative_review_gate.status must be PASS")
    if comparative.get("must_compare_to_reference_packet") is not True:
        errors.append("professional_design_process.comparative_review_gate.must_compare_to_reference_packet must be true")
    if not _non_empty_text(comparative.get("reviewer_role")):
        errors.append("professional_design_process.comparative_review_gate.reviewer_role is required")
    elif "independent" not in str(comparative.get("reviewer_role") or "").strip().lower():
        errors.append("professional_design_process.comparative_review_gate.reviewer_role must identify an independent design/Product Face reviewer")
    if not _non_empty_text(comparative.get("basis")):
        errors.append("professional_design_process.comparative_review_gate.basis is required")
    if not _list_items(comparative.get("block_when")):
        errors.append("professional_design_process.comparative_review_gate.block_when must be a non-empty array")

    return errors


def validate_reasoning_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in REASONING_POLICY_REQUIRED_FIELDS:
        value = policy.get(field)
        if isinstance(value, list):
            if not _list_items(value):
                errors.append(f"reasoning_policy.{field} must be a non-empty array")
        elif isinstance(value, dict):
            if not value:
                errors.append(f"reasoning_policy.{field} must be a non-empty object")
        elif not _non_empty_text(value):
            errors.append(f"reasoning_policy.{field} is required")

    if policy.get("record_type") not in (None, "reasoning_policy"):
        errors.append("reasoning_policy.record_type must be reasoning_policy")
    reasoning_class = str(policy.get("reasoning_class") or "").strip()
    if reasoning_class and reasoning_class not in REASONING_CLASSES:
        errors.append("reasoning_policy.reasoning_class must be one of " + ", ".join(sorted(REASONING_CLASSES)))
    review_intensity = str(policy.get("review_intensity") or "").strip()
    if review_intensity and review_intensity not in REASONING_REVIEW_INTENSITIES:
        errors.append("reasoning_policy.review_intensity must be one of " + ", ".join(sorted(REASONING_REVIEW_INTENSITIES)))
    evidence = policy.get("evidence_policy") if isinstance(policy.get("evidence_policy"), dict) else {}
    if evidence:
        if evidence.get("raw_chain_of_thought_forbidden") is not True:
            errors.append("reasoning_policy.evidence_policy.raw_chain_of_thought_forbidden must be true")
        if reasoning_class in {"deep", "adversarial", "human_decision"} and evidence.get("durable_summary_required") is not True:
            errors.append("reasoning_policy.evidence_policy.durable_summary_required must be true for high reasoning classes")
        if reasoning_class in {"deep", "adversarial", "human_decision"} and evidence.get("evidence_refs_required") is not True:
            errors.append("reasoning_policy.evidence_policy.evidence_refs_required must be true for high reasoning classes")
    if policy.get("private_reasoning_policy") not in (None, "never_store_raw", "summarize_only", "tool_internal_only"):
        errors.append("reasoning_policy.private_reasoning_policy must be never_store_raw, summarize_only or tool_internal_only")
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

    errors.extend(validate_product_scope_planning_contract(data))
    errors.extend(validate_specialist_research_contract(data))
    errors.extend(validate_product_creation_readiness_contract(data))
    errors.extend(validate_production_promotion_ladder_contract(data))
    errors.extend(validate_user_facing_autonomy_contract(data))
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
    errors.extend(validate_agent_runtime_hardening_profile(data))
    if data.get("factory_method_version") == "OVERKILL_VFINAL":
        if not isinstance(data.get("reasoning_policy"), dict):
            errors.append("reasoning_policy required for OVERKILL_VFINAL cards")
        else:
            errors.extend(validate_reasoning_policy(data["reasoning_policy"]))
    lane_contracts = card_parallel_lane_contracts(data)
    if _card_parallel_execution_requested(data) and not lane_contracts:
        errors.append("parallel execution requested but parallel_lane_contracts is missing")
    for index, lane in enumerate(lane_contracts):
        errors.extend(validate_parallel_lane_contract(lane, at=f"parallel_lane_contracts[{index}]"))
    if data.get("executor_identity") == data.get("reviewer_identity"):
        errors.append("executor_identity and reviewer_identity must differ")
    product_facing = product_experience_surface_required(data)
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
            reference_waiver = data["product_experience_plan"].get("reference_quality_waiver")
            if not isinstance(data.get("reference_quality_packet"), dict):
                if not isinstance(reference_waiver, dict):
                    errors.append("reference_quality_packet required for vFinal product-facing surfaces")
                elif not _non_empty_text(reference_waiver.get("owner")) or not _non_empty_text(reference_waiver.get("reason")):
                    errors.append("product_experience_plan.reference_quality_waiver requires owner and reason")
            else:
                errors.extend(validate_reference_quality_packet(data["reference_quality_packet"]))
            if not isinstance(data.get("professional_design_process"), dict):
                errors.append("professional_design_process required for vFinal product-facing surfaces")
            else:
                errors.extend(validate_professional_design_process(data["professional_design_process"]))
    phase = str(data.get("phase", "")).upper()
    if product_experience_surface_required(data) and phase in {"F11", "F16", "F17"}:
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


def validate_reference_quality_comparison(comparison: Any, *, is_pass: bool) -> list[str]:
    errors: list[str] = []
    if not isinstance(comparison, dict) or not comparison:
        if is_pass:
            errors.append("product_face_result.reference_quality_comparison is required for PASS")
        return errors
    if is_pass and _status_value(comparison) != "pass":
        errors.append("product_face_result.reference_quality_comparison.status must be pass")
    if not _non_empty_text(comparison.get("basis")):
        errors.append("product_face_result.reference_quality_comparison.basis is required")
    if not _non_empty_text(comparison.get("reference_set_ref")):
        errors.append("product_face_result.reference_quality_comparison.reference_set_ref is required")
    if is_pass and len(_list_items(comparison.get("compared_source_ids"))) < 3:
        errors.append("product_face_result.reference_quality_comparison.compared_source_ids requires at least 3 references")
    if is_pass and comparison.get("reviewer_independent_from_implementation") is not True:
        errors.append("product_face_result.reference_quality_comparison.reviewer_independent_from_implementation must be true")
    dimensions = comparison.get("dimensions") if isinstance(comparison.get("dimensions"), dict) else {}
    for dimension in REFERENCE_COMPARISON_DIMENSIONS:
        verdict = dimensions.get(dimension)
        if not isinstance(verdict, dict):
            errors.append(f"product_face_result.reference_quality_comparison.dimensions.{dimension} is required")
            continue
        if is_pass and _status_value(verdict) != "pass":
            errors.append(f"product_face_result.reference_quality_comparison.dimensions.{dimension}.status must be pass")
        if not _non_empty_text(verdict.get("basis")):
            errors.append(f"product_face_result.reference_quality_comparison.dimensions.{dimension}.basis is required")
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
    visual_quality = result.get("visual_quality_result") if isinstance(result.get("visual_quality_result"), dict) else {}
    if not visual_quality:
        errors.append("product_face_result.visual_quality_result is required")
    else:
        visual_status = str(visual_quality.get("status") or "").strip().upper()
        if visual_status not in VISUAL_QUALITY_ALLOWED_RESULTS:
            errors.append("product_face_result.visual_quality_result.status must be PASS, PASS_WITH_RESIDUALS or BLOCK")
        if not _non_empty_text(visual_quality.get("reviewer")):
            errors.append("product_face_result.visual_quality_result.reviewer is required")
        elif is_pass and str(visual_quality.get("reviewer") or "").strip() == str(result.get("executed_by") or "").strip():
            errors.append("product_face_result.visual_quality_result.reviewer must differ from executed_by")
        if not _non_empty_text(visual_quality.get("basis")):
            errors.append("product_face_result.visual_quality_result.basis is required")
        if visual_status in {"PASS", "PASS_WITH_RESIDUALS"} and visual_quality.get("reference_quality_bar_checked") is not True:
            errors.append("product_face_result.visual_quality_result.reference_quality_bar_checked must be true")
        if is_pass and visual_status == "BLOCK":
            errors.append("product_face_result visual_quality_result BLOCK prevents Product Face PASS")
        if is_pass and visual_status not in {"PASS", "PASS_WITH_RESIDUALS"}:
            errors.append("product_face_result PASS requires visual_quality_result.status PASS or PASS_WITH_RESIDUALS")
        if is_pass and visual_status == "PASS_WITH_RESIDUALS" and not _list_items(visual_quality.get("residuals")):
            errors.append("product_face_result PASS_WITH_RESIDUALS requires residuals")
    professional_comparison = result.get("professional_design_process_comparison")
    if is_pass:
        if not _non_empty_text(result.get("professional_design_process_ref")):
            errors.append("product_face_result.professional_design_process_ref is required for PASS")
        if not isinstance(professional_comparison, dict) or not professional_comparison:
            errors.append("product_face_result.professional_design_process_comparison is required for PASS")
        elif _status_value(professional_comparison) != "pass":
            errors.append("product_face_result.professional_design_process_comparison.status must be pass")
        elif not _non_empty_text(professional_comparison.get("basis")):
            errors.append("product_face_result.professional_design_process_comparison.basis is required")
    errors.extend(validate_reference_quality_comparison(result.get("reference_quality_comparison"), is_pass=is_pass))
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
    errors.extend(_product_delivery_quality_profile_ref_errors(card))
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
    professional_ref = str(result.get("professional_design_process_ref") or "").strip()
    if strict_product_experience_required(card) and not professional_ref:
        errors.append("product_face_result.professional_design_process_ref is required for vFinal product-facing completion")

    required_domain_proofs = _required_domain_proof_ids(card, "before_completion")
    if required_domain_proofs:
        profile = _product_delivery_quality_profile(card) or {
            "waiver_policy": {
                "allowed": True,
                "requires_owner": True,
                "requires_reason": True,
                "cannot_claim_full_acceptance": True,
            }
        }
        errors.extend(
            _validate_delivery_profile_proof_coverage(
                result.get("domain_proof_coverage"),
                required_domain_proofs,
                at="product_face_result.domain_proof_coverage",
                profile=profile,
                full_acceptance=True,
            )
        )

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
    source_head_expected = str(proof.get("source_head_expected") or "").strip()
    container_image = str(proof.get("container_image") or "").strip()
    solana_install_url = str(proof.get("solana_install_url") or "").strip().lower()
    if "crates.io" in install_source and not source_head:
        errors.append("auditor_result quasar_toolchain_proof cannot rely on crates.io quasar-cli without a source_head pin")
    if source_head and len(source_head) < 7:
        errors.append("auditor_result quasar_toolchain_proof source_head must be a commit-like pin")
    if source_head_expected and len(source_head_expected) < 7:
        errors.append("auditor_result quasar_toolchain_proof source_head_expected must be a commit-like pin")
    if source_head and source_head_expected and source_head != source_head_expected:
        errors.append("auditor_result quasar_toolchain_proof source_head must match source_head_expected")
    if proof.get("source_head_matches") is not True:
        errors.append("auditor_result quasar_toolchain_proof source_head_matches must be true")
    if container_image:
        if ":latest" in container_image:
            errors.append("auditor_result quasar_toolchain_proof container_image must not use latest")
        if "@sha256:" not in container_image:
            errors.append("auditor_result quasar_toolchain_proof container_image must be digest-pinned")
    if solana_install_url:
        if "/stable/" in solana_install_url:
            errors.append("auditor_result quasar_toolchain_proof solana_install_url must not use stable")
        if not re.search(r"/v\d+\.\d+\.\d+(?:[-._a-z0-9]+)?/install$", solana_install_url):
            errors.append("auditor_result quasar_toolchain_proof solana_install_url must use an explicit release")
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
    phase = str(card.get("phase", "")).upper()
    return product_experience_surface_required(card) and (
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


def validate_completion_audit_contract(card: dict[str, Any], audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    decision = str(audit.get("decision") or "").strip().lower()
    if decision not in {"done", "block", "done_with_owner"}:
        errors.append("completion_audit.decision must be done, block or done_with_owner")
    claim_results = audit.get("sot_claim_results")
    sot_statuses: list[str] = []
    if not isinstance(claim_results, list) or not claim_results:
        errors.append("completion_audit.sot_claim_results is required")
    else:
        for index, item in enumerate(claim_results):
            item = item if isinstance(item, dict) else {}
            status = str(item.get("status") or "").strip().upper()
            sot_statuses.append(status)
            if not _non_empty_text(item.get("claim_ref")):
                errors.append(f"completion_audit.sot_claim_results[{index}].claim_ref is required")
            if status not in COMPLETION_SOT_STATUSES:
                errors.append(
                    f"completion_audit.sot_claim_results[{index}].status must be DONE, BLOCKED, DEFERRED_WITH_OWNER or OUT_OF_SCOPE"
                )
            if status in {"BLOCKED", "DEFERRED_WITH_OWNER", "OUT_OF_SCOPE"} and not _non_empty_text(item.get("owner")):
                errors.append(f"completion_audit.sot_claim_results[{index}].owner is required for non-DONE status")
        if "BLOCKED" in sot_statuses and decision != "block":
            errors.append("completion_audit.decision must be block when any SOT claim is BLOCKED")
        elif "DEFERRED_WITH_OWNER" in sot_statuses and decision != "done_with_owner":
            errors.append("completion_audit.decision must be done_with_owner when any SOT claim is DEFERRED_WITH_OWNER")
        elif decision == "done":
            incomplete = sorted(set(sot_statuses) - {"DONE", "OUT_OF_SCOPE"})
            if incomplete:
                errors.append("completion_audit.decision=done requires SOT claims to be DONE or OUT_OF_SCOPE, found " + ", ".join(incomplete))

    method_results = audit.get("method_execution_results")
    if not isinstance(method_results, list) or not method_results:
        errors.append("completion_audit.method_execution_results is required")
    else:
        result_by_method = {
            str(item.get("method") or "").strip(): str(item.get("status") or "").strip().upper()
            for item in method_results
            if isinstance(item, dict)
        }
        for index, item in enumerate(method_results):
            item = item if isinstance(item, dict) else {}
            status = str(item.get("status") or "").strip().upper()
            if not _non_empty_text(item.get("method")):
                errors.append(f"completion_audit.method_execution_results[{index}].method is required")
            if status not in COMPLETION_METHOD_STATUSES:
                errors.append(f"completion_audit.method_execution_results[{index}].status must be EXECUTED, WAIVED or BLOCKED")
            if status == "BLOCKED":
                errors.append(f"completion_audit method {item.get('method') or index} is still BLOCKED")

        method_contract = card.get("method_contract") if isinstance(card.get("method_contract"), dict) else {}
        for method in sorted(_selected_engineering_methods(method_contract)):
            if method not in result_by_method:
                errors.append(f"completion_audit missing method_execution_result for selected method {method}")
    return errors


def validate_completion(
    card: dict[str, Any],
    metadata: dict[str, Any],
    *,
    from_status: str | None = None,
    to_status: str | None = None,
) -> list[str]:
    errors = validate_receipt(metadata)
    errors.extend(done_promotion_errors(metadata, from_status=from_status, to_status=to_status))
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
    audit = metadata.get("completion_audit")
    if isinstance(audit, dict):
        errors.extend(validate_completion_audit_contract(card, audit))
    elif _product_planning_required(card):
        errors.append("completion_audit is required for complete-product done promotion")
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
        required = product_experience_surface_required(card)
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
            "discord",
            "discord-control-tower",
            "discord-bridge",
            "discord-approval",
            "discord-access",
            "discord-blocker",
            "discord-health",
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
    lane_contracts = card_parallel_lane_contracts(card)
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
            "parallel_lane_contracts": lane_contracts,
            "reasoning_policy": card.get("reasoning_policy"),
            "reference_quality_packet": card.get("reference_quality_packet"),
            "professional_design_process": card.get("professional_design_process"),
            "learning_proposal_refs": card.get("learning_proposal_refs", []),
            "canonical_product_sot_ref": card.get("canonical_product_sot_ref") or "card.product_sot",
            "product_creation_plan_ref": card.get("product_creation_plan_ref")
            or ("card.product_creation_plan" if isinstance(card.get("product_creation_plan"), dict) else None),
            "product_context_packet_ref": card.get("product_context_packet_ref")
            or ("card.product_context_packet" if isinstance(card.get("product_context_packet"), dict) else None),
            "product_implementation_readiness_ref": card.get("product_implementation_readiness_ref")
            or (
                "card.product_implementation_readiness"
                if isinstance(card.get("product_implementation_readiness"), dict)
                else None
            ),
            "required_structured_proofs": _activated_capability_pack_structured_proof_ids(card),
            "required_completion_proofs": _required_domain_proof_ids(card, "before_completion"),
            "specialist_research_plan_ref": card.get("specialist_research_plan_ref")
            or ("card.specialist_research_plan" if isinstance(card.get("specialist_research_plan"), dict) else None),
            "specialist_decision_packet_ref": card.get("specialist_decision_packet_ref")
            or (
                "card.specialist_decision_packet"
                if isinstance(card.get("specialist_decision_packet"), dict)
                else None
            ),
        },
        "agent_runtime_hardening_profile": card.get("agent_runtime_hardening_profile"),
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
            "factory_gate_timing_policy": profile_binding.get("factory_gate_timing_policy"),
            "gate_timing_source": "worker_task.gate_timing_class",
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
            "profile_readiness": profile_readiness_summary(worker_id),
        }
    return packet


def build_gate_report(card: dict[str, Any]) -> dict[str, Any]:
    validation_errors = validate_card(card)
    validation_warnings = parallel_lane_warnings(card_parallel_lane_contracts(card))
    worker_rows: dict[str, dict[str, Any]] = {}
    required_workers: list[str] = []
    blocked_workers: list[str] = []
    blocker_economics: list[dict[str, str]] = []
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
            if status == "requires_execution" or str(status).startswith("blocked_"):
                blocker_economics.append(worker_blocker_economics(worker_id, str(status), reason))
        if str(status).startswith("blocked_"):
            blocked_workers.append(worker_id)
    for index, error in enumerate(validation_errors, start=1):
        blocker_economics.append(
            blocker_economics_entry(
                blocker_id=f"card-validation:{index}",
                owner="operator",
                risk_controlled="canonical card contract integrity",
                cost_time_class="local_edit",
                dependency="card_contract",
                smallest_safe_next_action=error,
                mutation_risk="local_repo_only",
                route="local",
            )
        )
    if validation_errors or blocked_workers:
        gate_status = "blocked"
    elif required_workers:
        gate_status = "ready_for_worker_execution"
    else:
        gate_status = "pass_no_workers_required"
    next_safe_actions: list[dict[str, str]] = []
    seen_actions: set[tuple[str, str, str]] = set()
    for worker_id, row in worker_rows.items():
        if not row.get("required"):
            continue
        status = str(row.get("status") or "")
        if status not in {"requires_execution"} and not status.startswith("blocked_"):
            continue
        guidance_items = list(row.get("unblock_guidance", []))
        if status == "requires_execution" and not guidance_items:
            guidance_items.append(
                {
                    "field": WORKERS[worker_id].output_field,
                    "action": f"execute {worker_id} and attach a valid {WORKERS[worker_id].output_field}",
                    "authority": "assigned worker must produce evidence; operator may only route or approve where explicitly required",
                }
            )
        for guidance in guidance_items:
            key = (worker_id, str(guidance.get("field") or ""), str(guidance.get("action") or ""))
            if key in seen_actions:
                continue
            seen_actions.add(key)
            next_safe_actions.append({"worker_id": worker_id, **guidance})
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
        "card_validation_warnings": validation_warnings,
        "blocker_economics": blocker_economics,
        "next_safe_actions": next_safe_actions,
        "workers": worker_rows,
    }


def recovery_route_from_action(card: dict[str, Any], action: dict[str, Any], index: int) -> dict[str, Any]:
    worker_id = str(action.get("worker_id") or "factory-orchestrator").strip() or "factory-orchestrator"
    worker = WORKERS.get(worker_id, WORKERS["factory-orchestrator"])
    card_id = sanitize_slug(card.get("card_id") or "factory-card", fallback="factory-card")
    blocker_type = blocker_type_for_worker(worker_id)
    human_gate_required = blocker_type == "human_gate"
    route_id = f"recovery:{card_id}:{index}:{sanitize_slug(worker_id, fallback='worker')}"
    action_text = str(action.get("action") or "run required worker and attach evidence").strip()
    field = str(action.get("field") or worker.output_field).strip()
    return {
        "recovery_route_id": route_id,
        "blocker_type": blocker_type,
        "factory_owned_repair_allowed": not human_gate_required,
        "human_gate_required": human_gate_required,
        "repair_owner_worker": worker_id,
        "repair_task_ref": f"hermes:intent:{route_id}",
        "repair_inputs": [
            f"card:{card_id}",
            f"blocked-field:{field}",
            action_text,
        ],
        "expected_repair_outputs": [field],
        "commands_or_worker_routes": [f"route {worker_id} through Hermes Kanban"],
        "invalidates_refs": [f"worker-result:{field}:blocking-or-stale"],
        "supersedes_refs": [f"worker-result:{field}:fresh-pass-required"],
        "dependency_edge_patch": {
            "old_edges": [f"blocked:{field}"],
            "new_edges": [f"fresh-review:{field}"],
            "patch_authority": "fresh review PASS recorded in Hermes before unblock",
        },
        "downstream_freeze_scope": [
            "next worker",
            "done promotion",
            "Receipt Five closure",
        ],
        "fresh_review_required": not human_gate_required,
        "fresh_review_result_ref": f"worker-result:{field}:fresh-review",
        "unblock_authority_ref": "Hermes blocked event plus fresh review PASS" if not human_gate_required else "human_gate_record",
        "retry_policy": recovery_retry_policy(),
        "audit_trail_refs": [
            "factoryctl:gate-report",
            f"worker:{worker_id}",
        ],
        "hermes_materialization": {
            "runtime_authority": "hermes_kanban",
            "native_primitives": [
                "kanban_task",
                "parent_link",
                "blocked_state",
                "comment_metadata",
                "run_history",
                "reclaim_reassign",
            ],
            "task_intent": "Create or route a Hermes repair task; do not mutate a local task lifecycle.",
            "parent_link_policy": "Repair task remains linked to the blocked parent and downstream work stays blocked until fresh review passes.",
            "comments_metadata_policy": "Store blocker type, invalidation refs, retry attempt and unblock authority in Hermes comments/metadata.",
            "local_state_authority": False,
        },
    }


def recovery_route_from_validation_error(card: dict[str, Any], error: str, index: int) -> dict[str, Any]:
    return recovery_route_from_action(
        card,
        {
            "worker_id": "factory-orchestrator",
            "field": "card_contract",
            "action": error,
            "authority": "factory-orchestrator emits a repaired card contract; Hermes records the repair task and review.",
        },
        index,
    )


def recovery_materialization_contract(route_id: str) -> dict[str, Any]:
    return {
        "runtime_authority": "hermes_kanban",
        "native_primitives": [
            "kanban_task",
            "parent_link",
            "blocked_state",
            "comment_metadata",
            "run_history",
            "reclaim_reassign",
        ],
        "task_intent": "Create or route a Hermes repair task; do not mutate a local task lifecycle.",
        "parent_link_policy": (
            "Repair task remains linked to the blocked parent and downstream work stays blocked until fresh review passes."
        ),
        "comments_metadata_policy": (
            "Store blocker type, invalidation refs, retry attempt and unblock authority in Hermes comments/metadata."
        ),
        "local_state_authority": False,
        "semantic_route_ref": route_id,
    }


def recovery_route_from_recommendation(
    card: dict[str, Any],
    *,
    worker_id: str,
    field: str,
    evidence_ref: str | None,
    recommendation: dict[str, Any],
    index: int,
) -> dict[str, Any]:
    worker = WORKERS.get(worker_id, WORKERS["factory-orchestrator"])
    card_id = sanitize_slug(card.get("card_id") or "factory-card", fallback="factory-card")
    route_id = str(recommendation.get("recovery_route_id") or "").strip()
    if not route_id:
        route_id = f"recovery:{card_id}:{index}:{sanitize_slug(worker.worker_id, fallback='worker')}"
    blocker_type = str(recommendation.get("blocker_type") or blocker_type_for_worker(worker.worker_id)).strip()
    repair_owner_worker = str(recommendation.get("repair_owner_worker") or worker.worker_id)
    human_gate_required = recommendation.get("human_gate_required") is True or is_human_gate_recovery(
        blocker_type=blocker_type,
        repair_owner_worker=repair_owner_worker,
    )
    audit_refs = ["factoryctl:worker-result-recovery", f"worker:{worker.worker_id}"]
    if evidence_ref:
        audit_refs.append(evidence_ref)
    return {
        "recovery_route_id": route_id,
        "blocker_type": blocker_type,
        "factory_owned_repair_allowed": False if human_gate_required else recommendation.get("factory_owned_repair_allowed") is not False,
        "human_gate_required": human_gate_required,
        "repair_owner_worker": repair_owner_worker,
        "repair_task_ref": str(recommendation.get("repair_task_ref") or f"hermes:intent:{route_id}"),
        "repair_inputs": string_list(recommendation.get("repair_inputs"))
        or [
            f"card:{card_id}",
            f"blocked-field:{field}",
            "blocked worker result requires factory-owned repair",
        ],
        "expected_repair_outputs": string_list(recommendation.get("expected_repair_outputs")) or [field],
        "commands_or_worker_routes": string_list(recommendation.get("commands_or_worker_routes"))
        or [f"route {worker.worker_id} through Hermes Kanban"],
        "invalidates_refs": string_list(recommendation.get("invalidates_refs"))
        or [f"worker-result:{field}:blocking-or-stale"],
        "supersedes_refs": string_list(recommendation.get("supersedes_refs"))
        or [f"worker-result:{field}:fresh-pass-required"],
        "dependency_edge_patch": recommendation.get("dependency_edge_patch")
        if isinstance(recommendation.get("dependency_edge_patch"), dict)
        else {
            "old_edges": [f"blocked:{field}"],
            "new_edges": [f"fresh-review:{field}"],
            "patch_authority": "fresh review PASS recorded in Hermes before unblock",
        },
        "downstream_freeze_scope": string_list(recommendation.get("downstream_freeze_scope"))
        or ["next worker", "done promotion", "Receipt Five closure"],
        "fresh_review_required": recommendation.get("fresh_review_required") is not False and not human_gate_required,
        "fresh_review_result_ref": str(recommendation.get("fresh_review_result_ref") or f"worker-result:{field}:fresh-review"),
        "unblock_authority_ref": str(
            "human_gate_record" if human_gate_required else recommendation.get("unblock_authority_ref")
            or ("human_gate_record" if human_gate_required else "Hermes blocked event plus fresh review PASS")
        ),
        "retry_policy": recovery_retry_policy(
            base=recommendation.get("retry_policy") if isinstance(recommendation.get("retry_policy"), dict) else None
        ),
        "audit_trail_refs": audit_refs,
        "hermes_materialization": recovery_materialization_contract(route_id),
    }


def recovery_routes_from_worker_records(
    card: dict[str, Any],
    worker_records: dict[str, dict[str, Any]],
    *,
    start_index: int = 1,
) -> list[dict[str, Any]]:
    routes: list[dict[str, Any]] = []
    route_index = start_index
    requirements_by_id: dict[str, dict[str, Any]] = {}
    for record in worker_records.values():
        for requirement in record.get("graph_requirements", []):
            requirement_id = str(requirement.get("requirement_id") or "").strip()
            if requirement_id:
                requirements_by_id[requirement_id] = requirement
    for field, record in sorted(worker_records.items()):
        if str(record.get("result") or "").strip().upper() != "BLOCKED":
            continue
        recovery = record.get("recovery_recommendation")
        if not isinstance(recovery, dict):
            continue
        matched_requirements = [
            requirements_by_id[ref]
            for ref in (
                string_list(record.get("graph_requirement_refs"))
                + string_list(record.get("review_requirement_refs"))
                + string_list(record.get("reviewed_requirement_refs"))
            )
            if ref in requirements_by_id
        ]
        review_block_routed = False
        for requirement in matched_requirements:
            if str(requirement.get("required_review_field") or "") != field:
                continue
            producer_field = str(requirement.get("producer_field") or "").strip()
            producer_worker = _worker_id_for_output_field(producer_field)
            if not producer_field or not producer_worker:
                continue
            requirement_id = str(requirement.get("requirement_id") or "").strip()
            producer_ref = str(requirement.get("producer_ref") or f"worker-result:{producer_field}").strip()
            route_id = (
                f"recovery:{sanitize_slug(card.get('card_id') or 'factory-card', fallback='factory-card')}:"
                f"review-block:{sanitize_slug(requirement_id, fallback=producer_field)}"
            )
            recommendation_override = {
                **recovery,
                "blocker_type": blocker_type_for_worker(producer_worker),
                "factory_owned_repair_allowed": recovery.get("factory_owned_repair_allowed") is not False,
                "human_gate_required": False,
                "recovery_route_id": route_id,
                "repair_owner_worker": producer_worker,
                "repair_task_ref": f"hermes:intent:{route_id}",
                "repair_inputs": [
                    producer_ref,
                    record.get("evidence_ref") or f"worker-result:{field}:blocked-review",
                    requirement_id,
                    str(record.get("findings_summary") or record.get("next_action") or "review blocked the producer handoff"),
                ],
                "expected_repair_outputs": [producer_field, field],
                "invalidates_refs": [producer_ref, f"worker-result:{field}:blocked-review"],
                "supersedes_refs": [
                    f"worker-result:{producer_field}:fresh-repair",
                    f"worker-result:{field}:fresh-review-pass",
                ],
                "dependency_edge_patch": {
                    "old_edges": [requirement_id, f"blocked-review:{field}"],
                    "new_edges": [f"fresh-repair:{producer_field}", f"fresh-review:{field}:PASS"],
                    "patch_authority": "fresh reviewer PASS linked to the original graph requirement before downstream unblock",
                },
                "downstream_freeze_scope": ["producer consumption", "next worker", "done promotion", "Receipt Five closure"],
                "fresh_review_required": True,
                "fresh_review_result_ref": f"worker-result:{field}:fresh-review-pass",
                "unblock_authority_ref": f"graph-requirement:{requirement_id}:fresh-review-pass",
            }
            routes.append(
                recovery_route_from_recommendation(
                    card,
                    worker_id=producer_worker,
                    field=producer_field,
                    evidence_ref=producer_ref,
                    recommendation=recommendation_override,
                    index=route_index,
                )
            )
            route_index += 1
            review_block_routed = True
        if review_block_routed:
            continue
        worker_id = _worker_id_for_output_field(field) or str(recovery.get("repair_owner_worker") or "factory-orchestrator")
        routes.append(
            recovery_route_from_recommendation(
                card,
                worker_id=worker_id,
                field=field,
                evidence_ref=record.get("evidence_ref"),
                recommendation=recovery,
                index=route_index,
            )
        )
        route_index += 1
    return routes


def build_factory_recovery_plan(
    card: dict[str, Any],
    worker_results_dir: Path | None = None,
    receipt: dict[str, Any] | None = None,
) -> dict[str, Any]:
    report = build_gate_report(card)
    routes: list[dict[str, Any]] = []
    route_index = 1
    if report.get("gate_predicate_result") == "BLOCK":
        for error in report.get("card_validation_errors", []):
            routes.append(recovery_route_from_validation_error(card, str(error), route_index))
            route_index += 1
        for action in report.get("next_safe_actions", []):
            if not isinstance(action, dict):
                continue
            routes.append(recovery_route_from_action(card, action, route_index))
            route_index += 1
    worker_completion = (
        build_worker_closure(card, receipt or {}, worker_results_dir)
        if worker_results_dir is not None or receipt is not None
        else None
    )
    worker_routes = list(worker_completion.get("recovery_routes", [])) if worker_completion else []
    routes.extend(worker_routes)
    blocked_worker_ids = list(report.get("blocked_workers", []))
    for route in worker_routes:
        worker_id = str(route.get("repair_owner_worker") or "").strip()
        if worker_id and worker_id not in blocked_worker_ids:
            blocked_worker_ids.append(worker_id)
    gate_predicate_result = "BLOCK" if routes else report.get("gate_predicate_result")
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-recovery-plan.schema.json",
        "record_type": "factory_recovery_plan",
        "created_at": utc_now(),
        "card_id": report.get("card_id"),
        "gate_predicate_result": gate_predicate_result,
        "blocked_workers": blocked_worker_ids,
        "next_safe_actions": report.get("next_safe_actions", []),
        "recovery_routes": routes,
        "hermes_runtime_boundary": {
            "runtime_authority": "hermes_kanban",
            "factory_output": "semantic_recovery_contract",
            "no_shadow_scheduler": True,
            "no_shadow_dispatcher": True,
            "no_shadow_dependency_engine": True,
            "local_state_authority": False,
        },
        "public_private_boundary": {
            "no_raw_logs": True,
            "no_private_paths": True,
            "no_private_ids": True,
        },
        "limits": [
            "This plan does not execute workers, approve gates, unblock Hermes tasks, or bypass missing evidence.",
            "Recovery routes are semantic contracts; Hermes Kanban remains the runtime authority for tasks, links, block/unblock, comments, runs and audit history.",
            "Human/security/release/deployment/GitHub/funds/secrets/mainnet approval is never implied by a recovery route.",
        ],
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


def worker_gate_timing_class(worker_id: str, card: dict[str, Any]) -> str:
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


def worker_queue_class(worker_id: str, card: dict[str, Any]) -> str:
    """Compatibility alias: this is gate timing policy, not runtime queue authority."""
    return worker_gate_timing_class(worker_id, card)


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item.strip()]


def stable_contract_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): stable_contract_value(item)
            for key, item in sorted(value.items(), key=lambda entry: str(entry[0]))
            if str(key) not in VOLATILE_CONTRACT_KEYS
        }
    if isinstance(value, list):
        return [stable_contract_value(item) for item in value]
    return value


def contract_digest(value: Any) -> str:
    stable_value = stable_contract_value(value)
    if isinstance(stable_value, str):
        payload = stable_value
    else:
        payload = json.dumps(stable_value, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def recovery_route_digest(route: dict[str, Any]) -> str:
    return f"{CONTRACT_DIGEST_ALGORITHM}:{contract_digest(route)}"


def recovery_route_digest_list(value: Any) -> list[str]:
    digests: list[str] = []
    for item in string_list(value):
        digest = item.strip()
        if re.fullmatch(r"sha256:[0-9a-f]{64}", digest) and digest not in digests:
            digests.append(digest)
    return digests


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
        if result == "BLOCKED":
            recovery = data.get("recovery_recommendation")
            if not isinstance(recovery, dict):
                errors.append("BLOCKED worker result requires recovery_recommendation")
            else:
                boundary = recovery.get("hermes_runtime_boundary") if isinstance(recovery.get("hermes_runtime_boundary"), dict) else {}
                if boundary.get("runtime_authority") != "hermes_kanban":
                    errors.append("recovery_recommendation.hermes_runtime_boundary.runtime_authority must be hermes_kanban")
                if boundary.get("local_state_authority") is not False:
                    errors.append("recovery_recommendation must not claim local runtime state authority")
                if not str(recovery.get("recovery_route_id") or "").strip():
                    errors.append("recovery_recommendation.recovery_route_id is required")
                blocker_type = str(recovery.get("blocker_type") or "").strip()
                repair_owner_worker = str(recovery.get("repair_owner_worker") or "").strip()
                if is_human_gate_recovery(blocker_type=blocker_type, repair_owner_worker=repair_owner_worker):
                    if recovery.get("human_gate_required") is not True:
                        errors.append("human_gate recovery requires human_gate_required=true")
                    if recovery.get("factory_owned_repair_allowed") is not False:
                        errors.append("human_gate recovery must not allow factory-owned repair")
                    if recovery.get("fresh_review_required") is not False:
                        errors.append("human_gate recovery must not route through fresh review")
                    if recovery.get("unblock_authority_ref") != "human_gate_record":
                        errors.append("human_gate recovery unblock_authority_ref must be human_gate_record")
                retry_policy = recovery.get("retry_policy") if isinstance(recovery.get("retry_policy"), dict) else None
                if not isinstance(retry_policy, dict):
                    errors.append("recovery_recommendation.retry_policy is required")
                else:
                    if retry_policy.get("attempt_number_role") != "planner_seed_not_runtime_counter":
                        errors.append("recovery_recommendation.retry_policy.attempt_number_role must be planner_seed_not_runtime_counter")
                    if retry_policy.get("runtime_attempt_source") != "hermes_task_history":
                        errors.append("recovery_recommendation.retry_policy.runtime_attempt_source must be hermes_task_history")
                    if retry_policy.get("runtime_attempt_marker") != "factory_recovery_attempt":
                        errors.append("recovery_recommendation.retry_policy.runtime_attempt_marker must be factory_recovery_attempt")
                    if retry_policy.get("runtime_authority") != "hermes_kanban":
                        errors.append("recovery_recommendation.retry_policy.runtime_authority must be hermes_kanban")
                    if retry_policy.get("local_state_authority") is not False:
                        errors.append("recovery_recommendation.retry_policy must not claim local runtime state authority")
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
            review_declared = worker_result_declares_review(data)
            if authority.get("active") is False:
                errors.append("superseded worker result cannot satisfy promotion")
            if str(authority.get("result") or "").strip().upper() != "PASS":
                errors.append("promotion_authority.result must be PASS")
            scopes = [scope.lower() for scope in string_list(authority.get("allowed_transition_scopes"))]
            if review_declared:
                if "review" not in scopes:
                    errors.append("review-required handoff authority must include review scope")
                forbidden_scopes = {
                    "done",
                    "release",
                    "deployment",
                    "github_mutation",
                    "issue_completion",
                    "product_acceptance",
                }
                leaked = sorted(forbidden_scopes & set(scopes))
                if leaked:
                    errors.append("review-required handoff authority must not include " + ", ".join(leaked))
            elif "done" not in scopes:
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


def worker_result_is_active(data: dict[str, Any]) -> bool:
    authority = data.get("promotion_authority") if isinstance(data.get("promotion_authority"), dict) else {}
    return (
        data.get("active", True) is not False
        and authority.get("active", True) is not False
        and not data.get("superseded_by")
        and not authority.get("superseded_by")
    )


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
        evidence_ref = source_card_ref(path)
        review_declared = worker_result_declares_review(data)
        graph_requirements = declared_graph_requirements(record_type, data, evidence_ref=evidence_ref) if not errors else []
        record = {
            "evidence_ref": evidence_ref,
            "created_at": data.get("created_at") or data.get("decision_at"),
            "result": data.get("result") or data.get("decision"),
            "findings_summary": data.get("findings_summary"),
            "next_action": data.get("next_action"),
            "active": worker_result_is_active(data),
            "valid": not errors,
            "consumable": not errors,
            "review_declared": review_declared,
            "graph_requirements": graph_requirements,
            "graph_requirement_refs": string_list(data.get("graph_requirement_refs")),
            "review_requirement_refs": string_list(data.get("review_requirement_refs")),
            "reviewed_requirement_refs": string_list(data.get("reviewed_requirement_refs")),
            "reviewed_producer_refs": string_list(data.get("reviewed_producer_refs")),
            "producer_refs_reviewed": string_list(data.get("producer_refs_reviewed")),
            "recovery_route_refs": string_list(data.get("recovery_route_refs")),
            "recovery_route_digests": recovery_route_digest_list(data.get("recovery_route_digests")),
            "reviewed_recovery_route_refs": string_list(
                data.get("reviewed_recovery_route_refs") or data.get("recovery_route_refs_reviewed")
            ),
            "reviewed_recovery_route_digests": recovery_route_digest_list(
                data.get("reviewed_recovery_route_digests") or data.get("recovery_route_digests_reviewed")
            ),
            "authorized_downstream_worker_ids": registered_nonhuman_worker_ids(
                data.get("authorized_downstream_worker_ids")
                or data.get("authorized_next_worker_ids")
                or data.get("downstream_worker_ids")
            ),
            "review_task_authorizations": [
                item for item in data.get("review_task_authorizations", []) if isinstance(item, dict)
            ],
            "recovery_recommendation": data.get("recovery_recommendation")
            if isinstance(data.get("recovery_recommendation"), dict)
            else None,
            "validation_errors": errors,
        }
        apply_record_consumption_state(record)
        records_by_type.setdefault(record_type, []).append(
            record
        )
    records: dict[str, dict[str, Any]] = {}
    for record_type, candidates in records_by_type.items():
        active = [candidate for candidate in candidates if candidate.get("active")]
        ordered = sorted(active or candidates, key=_worker_record_sort_key, reverse=True)
        if ordered:
            selected = dict(ordered[0])
            selected["candidate_records"] = ordered
            records[record_type] = selected
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
            review_declared = worker_result_declares_review(value)
            graph_requirements = (
                declared_graph_requirements(
                    worker.output_field,
                    value,
                    evidence_ref=f"receipt:{worker.output_field}",
                )
                if not errors
                else []
            )
            record = {
                "evidence_ref": None,
                "result": value.get("result") or value.get("decision"),
                "findings_summary": value.get("findings_summary"),
                "next_action": value.get("next_action"),
                "active": worker_result_is_active(value),
                "valid": not errors,
                "consumable": not errors,
                "review_declared": review_declared,
                "graph_requirements": graph_requirements,
                "graph_requirement_refs": string_list(value.get("graph_requirement_refs")),
                "review_requirement_refs": string_list(value.get("review_requirement_refs")),
                "reviewed_requirement_refs": string_list(value.get("reviewed_requirement_refs")),
                "reviewed_producer_refs": string_list(value.get("reviewed_producer_refs")),
                "producer_refs_reviewed": string_list(value.get("producer_refs_reviewed")),
                "recovery_route_refs": string_list(value.get("recovery_route_refs")),
                "recovery_route_digests": recovery_route_digest_list(value.get("recovery_route_digests")),
                "reviewed_recovery_route_refs": string_list(
                    value.get("reviewed_recovery_route_refs") or value.get("recovery_route_refs_reviewed")
                ),
                "reviewed_recovery_route_digests": recovery_route_digest_list(
                    value.get("reviewed_recovery_route_digests") or value.get("recovery_route_digests_reviewed")
                ),
                "authorized_downstream_worker_ids": registered_nonhuman_worker_ids(
                    value.get("authorized_downstream_worker_ids")
                    or value.get("authorized_next_worker_ids")
                    or value.get("downstream_worker_ids")
                ),
                "review_task_authorizations": [
                    item for item in value.get("review_task_authorizations", []) if isinstance(item, dict)
                ],
                "recovery_recommendation": value.get("recovery_recommendation")
                if isinstance(value.get("recovery_recommendation"), dict)
                else None,
                "validation_errors": errors,
            }
            apply_record_consumption_state(record)
            fields[worker.output_field] = record
    return fields


def _review_required_by_handoff_metadata(data: dict[str, Any]) -> bool:
    for key in ("handoff", "handoff_gate", "gate_handoff", "review_gate", "handoff_metadata", "review_required_handoff"):
        value = data.get(key)
        if not isinstance(value, dict):
            continue
        if value.get("reviewer_required") is True or value.get("requires_review") is True:
            return True
        if value.get("review_required") is True or value.get("enabled") is True:
            return True
    return False


def worker_result_declares_review(data: dict[str, Any]) -> bool:
    return (
        data.get("reviewer_required") is True
        or data.get("handoff_requires_review") is True
        or data.get("review_declared") is True
        or data.get("review_ready") is True
        or str(data.get("handoff_state") or "").strip() == "implementation_ready_for_review"
        or _review_required_by_handoff_metadata(data)
    )


def _declared_review_worker_id(data: dict[str, Any]) -> str:
    nested = data.get("review_required_handoff") if isinstance(data.get("review_required_handoff"), dict) else {}
    worker_id = str(
        data.get("review_worker_id")
        or data.get("reviewer_worker_id")
        or nested.get("review_worker_id")
        or nested.get("reviewer_worker_id")
        or ""
    ).strip()
    return worker_id if worker_id in WORKERS else "independent-reviewer"


def registered_nonhuman_worker_ids(value: Any) -> list[str]:
    worker_ids: list[str] = []
    for worker_id in string_list(value):
        if worker_id in WORKERS and worker_id != "human-gate-clerk" and worker_id not in worker_ids:
            worker_ids.append(worker_id)
    return worker_ids


def declared_graph_requirements(record_type: str, data: dict[str, Any], *, evidence_ref: str | None) -> list[dict[str, Any]]:
    if not worker_result_declares_review(data):
        return []
    review_worker_id = _declared_review_worker_id(data)
    required_review_field = WORKERS[review_worker_id].output_field
    reviewer_result = str(data.get("reviewer_result") or "").strip().upper()
    status = "pending"
    requirement_ref = evidence_ref or f"external:{record_type}"
    recovery_route_refs = string_list(data.get("recovery_route_refs"))
    recovery_route_digests = recovery_route_digest_list(data.get("recovery_route_digests"))
    requirement = {
        "requirement_type": "review_before_consumption",
        "requirement_id": (
            f"review-before-consumption:{sanitize_slug(record_type, fallback='record')}:"
            f"{sanitize_slug(requirement_ref, fallback='evidence')}"
        ),
        "producer_field": record_type,
        "producer_ref": requirement_ref,
        "review_worker_id": review_worker_id,
        "required_review_field": required_review_field,
        "required_result": "PASS",
        "status": status,
        "reviewer_result": reviewer_result or "missing",
        "downstream_scope": ["implementation", "done", "release"],
        "review_authorized_scope": ["review"],
        "producer_handoff_state": "implementation_ready_for_review",
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
    }
    if recovery_route_refs:
        requirement["recovery_route_refs"] = recovery_route_refs
    if recovery_route_digests:
        requirement["recovery_route_digests"] = recovery_route_digests
    return [
        requirement
    ]


def review_task_authorization(requirement: dict[str, Any]) -> dict[str, Any]:
    return {
        "authorization_type": "review_task_only",
        "authorization_state": "review_task_ready",
        "requirement_id": requirement.get("requirement_id"),
        "producer_field": requirement.get("producer_field"),
        "producer_ref": requirement.get("producer_ref"),
        "authorized_worker_id": requirement.get("review_worker_id"),
        "authorized_receipt_field": requirement.get("required_review_field"),
        "authorized_scope": ["review"],
        "forbidden_scope_until_review_pass": [
            "release",
            "deployment",
            "github_mutation",
            "issue_completion",
            "product_acceptance",
        ],
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
    }


def review_record_matches_requirement(review_record: dict[str, Any], requirement: dict[str, Any]) -> bool:
    requirement_id = str(requirement.get("requirement_id") or "").strip()
    producer_ref = str(requirement.get("producer_ref") or "").strip()
    required_route_refs = set(string_list(requirement.get("recovery_route_refs")))
    required_route_digests = set(recovery_route_digest_list(requirement.get("recovery_route_digests")))
    if required_route_refs:
        reviewed_route_refs = set(
            string_list(review_record.get("reviewed_recovery_route_refs"))
            + string_list(review_record.get("recovery_route_refs_reviewed"))
        )
        if not required_route_refs.issubset(reviewed_route_refs):
            return False
    if required_route_digests:
        reviewed_route_digests = set(
            recovery_route_digest_list(review_record.get("reviewed_recovery_route_digests"))
            + recovery_route_digest_list(review_record.get("recovery_route_digests_reviewed"))
        )
        if not required_route_digests.issubset(reviewed_route_digests):
            return False
    explicit_refs = set(string_list(review_record.get("graph_requirement_refs")))
    explicit_refs.update(string_list(review_record.get("review_requirement_refs")))
    explicit_refs.update(string_list(review_record.get("reviewed_requirement_refs")))
    if requirement_id and requirement_id in explicit_refs:
        return True
    producer_refs = set(string_list(review_record.get("reviewed_producer_refs")))
    producer_refs.update(string_list(review_record.get("producer_refs_reviewed")))
    if producer_ref and producer_ref in producer_refs:
        return True
    for authorization in review_record.get("review_task_authorizations", []):
        if not isinstance(authorization, dict):
            continue
        if requirement_id and authorization.get("requirement_id") == requirement_id:
            return True
        if producer_ref and authorization.get("producer_ref") == producer_ref:
            return True
    return False


def apply_record_consumption_state(record: dict[str, Any]) -> None:
    valid = bool(record.get("valid"))
    requirements = [dict(item) for item in record.get("graph_requirements", [])]
    pending = [requirement for requirement in requirements if requirement.get("status") != "satisfied"]
    review_declared = bool(record.get("review_declared") or requirements)

    if not valid:
        handoff_state = "blocked" if review_declared else "invalid"
        consumable = False
        authorized_scope: list[str] = []
    elif pending:
        handoff_state = "implementation_ready_for_review"
        consumable = False
        authorized_scope = ["review"]
    else:
        handoff_state = "consumable"
        consumable = True
        authorized_scope = ["implementation", "done", "release"]

    record["handoff_state"] = handoff_state
    record["review_ready"] = handoff_state == "implementation_ready_for_review"
    record["consumable"] = consumable
    record["authorized_downstream_scope"] = authorized_scope
    record["review_task_authorizations"] = [review_task_authorization(requirement) for requirement in pending]


def candidate_records_for_field(fields: dict[str, dict[str, Any]], field: str) -> list[dict[str, Any]]:
    record = fields.get(field)
    if not isinstance(record, dict):
        return []
    candidates = [record]
    for candidate in record.get("candidate_records", []):
        if isinstance(candidate, dict):
            candidates.append(candidate)
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for candidate in candidates:
        key = (
            str(candidate.get("created_at") or ""),
            str(candidate.get("evidence_ref") or ""),
        )
        if key not in seen:
            deduped.append(candidate)
            seen.add(key)
    return deduped


def resolve_graph_requirements(fields: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    requirements: list[dict[str, Any]] = []
    for record in fields.values():
        for requirement in record.get("graph_requirements", []):
            requirement = dict(requirement)
            review_candidates = candidate_records_for_field(
                fields,
                str(requirement.get("required_review_field") or ""),
            )
            if requirement.get("status") != "satisfied" and review_candidates:
                matching_review = next(
                    (
                        candidate
                        for candidate in review_candidates
                        if candidate.get("valid")
                        and str(candidate.get("result") or "").strip().upper() == "PASS"
                        and review_record_matches_requirement(candidate, requirement)
                    ),
                    None,
                )
                if matching_review:
                    requirement["status"] = "satisfied"
                    requirement["reviewer_result"] = "PASS"
                    requirement["review_evidence_ref"] = matching_review.get("evidence_ref") or "receipt:review"
                    authorized_worker_ids = registered_nonhuman_worker_ids(
                        matching_review.get("authorized_downstream_worker_ids")
                        or matching_review.get("authorized_next_worker_ids")
                        or matching_review.get("downstream_worker_ids")
                    )
                    if authorized_worker_ids:
                        requirement["authorized_downstream_worker_ids"] = authorized_worker_ids
            requirements.append(requirement)
    for record in fields.values():
        graph_requirements = [dict(item) for item in record.get("graph_requirements", [])]
        resolved_for_record = [
            requirement
            for requirement in requirements
            if requirement.get("producer_field") in {item.get("producer_field") for item in graph_requirements}
        ]
        record["graph_requirements"] = resolved_for_record
        apply_record_consumption_state(record)
    return requirements


def downstream_task_authorization(requirement: dict[str, Any], worker_tasks: list[dict[str, Any]]) -> dict[str, Any] | None:
    if requirement.get("status") != "satisfied":
        return None
    review_evidence_ref = str(requirement.get("review_evidence_ref") or "").strip()
    if not review_evidence_ref:
        return None
    available_workers = {
        str(task.get("worker_id") or "")
        for task in worker_tasks
        if task.get("status") == "requires_execution"
    }
    producer_worker = _worker_id_for_output_field(str(requirement.get("producer_field") or ""))
    review_worker = str(requirement.get("review_worker_id") or "")
    forbidden_worker_ids = sorted(
        worker_id
        for worker_id in {"human-gate-clerk", producer_worker or "", review_worker}
        if worker_id
    )
    authorized_worker_ids = [
        worker_id
        for worker_id in registered_nonhuman_worker_ids(requirement.get("authorized_downstream_worker_ids"))
        if worker_id in available_workers and worker_id not in forbidden_worker_ids
    ]
    if not authorized_worker_ids:
        return None
    requirement_id = str(requirement.get("requirement_id") or "").strip()
    recovery_route_refs = string_list(requirement.get("recovery_route_refs"))
    recovery_route_digests = recovery_route_digest_list(requirement.get("recovery_route_digests"))
    authorization = {
        "authorization_type": "fresh_review_downstream_task",
        "authorization_state": "worker_task_ready",
        "requirement_id": requirement_id,
        "producer_field": requirement.get("producer_field"),
        "producer_ref": requirement.get("producer_ref"),
        "review_evidence_ref": review_evidence_ref,
        "authorized_worker_ids": authorized_worker_ids,
        "forbidden_worker_ids": forbidden_worker_ids,
        "unblock_reason": (
            f"Fresh PASS review {review_evidence_ref} satisfied {requirement_id}; "
            f"authorized next worker(s): {', '.join(authorized_worker_ids)}"
        ),
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
    }
    if recovery_route_refs:
        authorization["recovery_route_refs"] = recovery_route_refs
    if recovery_route_digests:
        authorization["recovery_route_digests"] = recovery_route_digests
    return authorization


def downstream_task_authorizations(
    graph_requirements: list[dict[str, Any]],
    worker_tasks: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    authorizations: list[dict[str, Any]] = []
    for requirement in graph_requirements:
        authorization = downstream_task_authorization(requirement, worker_tasks)
        if authorization:
            authorizations.append(authorization)
    return authorizations


def graph_requirement_block_reason(requirement: dict[str, Any]) -> str:
    producer = str(requirement.get("producer_field") or "worker result")
    review_worker = str(requirement.get("review_worker_id") or "independent-reviewer")
    return f"{producer} requires {review_worker} PASS before downstream consumption"


def transition_consumes_graph_requirements(normalized_to: str) -> bool:
    return normalized_to in {
        "ready",
        "in_progress",
        "doing",
        "review",
        "review-ready",
        "ready_for_review",
        "implementation-ready-for-review",
        "implementation_ready_for_review",
        "done",
        "closed",
        "complete",
    }


def transition_is_review_ready(normalized_to: str) -> bool:
    return normalized_to in {
        "review",
        "review-ready",
        "ready_for_review",
        "implementation-ready-for-review",
        "implementation_ready_for_review",
    }


def build_graph_requirement_review_task(
    requirement: dict[str, Any],
    card: dict[str, Any],
    source_path: Path,
) -> dict[str, Any]:
    worker_id = str(requirement.get("review_worker_id") or "independent-reviewer")
    worker = WORKERS.get(worker_id, WORKERS["independent-reviewer"])
    task = build_worker_task(worker.worker_id, card, source_path)
    packet = dict(task.get("packet") or {})
    missing_inputs = missing_required_inputs(worker, card)
    status = "blocked_missing_inputs" if missing_inputs else "requires_execution"
    queue_class = worker_queue_class(worker.worker_id, card)
    requirement_id = str(requirement.get("requirement_id") or "")
    authorization = review_task_authorization(requirement)

    packet["status"] = status
    packet["trigger"] = {
        **dict(packet.get("trigger") or {}),
        "required": True,
        "reason": graph_requirement_block_reason(requirement),
        "timing": "after producer evidence exists and before downstream consumption",
        "blocking_policy": "Declared handoff reviews must PASS before the producer result can be consumed downstream.",
    }
    input_contract = dict(packet.get("input_contract") or {})
    input_contract["missing_fields"] = missing_inputs
    input_contract["graph_requirement_ref"] = requirement_id
    input_contract["review_task_authorizations"] = [authorization]
    packet["input_contract"] = input_contract
    packet["review_task_authorizations"] = [authorization]

    task.update(
        {
            "gate_timing_class": queue_class,
            "queue_class": queue_class,
            "required_before": "ready" if queue_class == "blocking-before-ready" else "done",
            "status": status,
            "packet": packet,
            "graph_requirement_refs": [requirement_id],
            "dependency_authorization_state": "review_ready",
            "review_task_authorizations": [authorization],
        }
    )
    return task


def attach_graph_requirement_tasks(
    worker_tasks: list[dict[str, Any]],
    graph_requirements: list[dict[str, Any]],
    card: dict[str, Any],
    source_path: Path,
) -> None:
    tasks_by_worker = {str(task.get("worker_id") or ""): task for task in worker_tasks}
    for requirement in graph_requirements:
        if requirement.get("status") == "satisfied":
            continue
        worker_id = str(requirement.get("review_worker_id") or "independent-reviewer")
        requirement_id = str(requirement.get("requirement_id") or "")
        existing = tasks_by_worker.get(worker_id)
        authorization = review_task_authorization(requirement)
        if existing:
            refs = list(existing.get("graph_requirement_refs") or [])
            if requirement_id and requirement_id not in refs:
                refs.append(requirement_id)
            existing["graph_requirement_refs"] = refs
            authorizations = list(existing.get("review_task_authorizations") or [])
            if authorization not in authorizations:
                authorizations.append(authorization)
            existing["dependency_authorization_state"] = "review_ready"
            existing["review_task_authorizations"] = authorizations
            packet = existing.get("packet") if isinstance(existing.get("packet"), dict) else {}
            packet["graph_requirement_refs"] = refs
            packet["review_task_authorizations"] = authorizations
            input_contract = dict(packet.get("input_contract") or {})
            input_contract["review_task_authorizations"] = authorizations
            packet["input_contract"] = input_contract
            existing["packet"] = packet
            continue
        task = build_graph_requirement_review_task(requirement, card, source_path)
        worker_tasks.append(task)
        tasks_by_worker[worker_id] = task


def attach_recovery_routes_to_tasks(
    worker_tasks: list[dict[str, Any]],
    recovery_routes: list[dict[str, Any]],
    card: dict[str, Any],
    source_path: Path,
) -> None:
    tasks_by_worker = {str(task.get("worker_id") or ""): task for task in worker_tasks}
    for route in recovery_routes:
        worker_id = str(route.get("repair_owner_worker") or "").strip()
        if worker_id not in WORKERS:
            continue
        task = tasks_by_worker.get(worker_id)
        if task is None:
            task = build_worker_task(worker_id, card, source_path)
            worker_tasks.append(task)
            tasks_by_worker[worker_id] = task
        route_id = str(route.get("recovery_route_id") or "").strip()
        refs = list(task.get("recovery_route_refs") or [])
        if route_id and route_id not in refs:
            refs.append(route_id)
        task["recovery_route_refs"] = refs
        packet = task.get("packet") if isinstance(task.get("packet"), dict) else {}
        packet["recovery_route_refs"] = refs
        input_contract = dict(packet.get("input_contract") or {})
        route_payloads = [item for item in input_contract.get("recovery_routes", []) if isinstance(item, dict)]
        if route not in route_payloads:
            route_payloads.append(route)
        input_contract["recovery_routes"] = route_payloads
        input_contract["recovery_route_refs"] = refs
        packet["input_contract"] = input_contract
        task["packet"] = packet


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
        "gate_timing_class": queue_class,
        "queue_class": queue_class,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
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
    graph_requirements = resolve_graph_requirements(present_fields)
    rows: dict[str, dict[str, Any]] = {}
    missing_blocking: list[str] = []
    invalid_blocking: list[str] = []
    unconsumable_blocking: list[str] = []

    for worker_id in required_worker_ids(card):
        worker = WORKERS[worker_id]
        queue_class = worker_queue_class(worker_id, card)
        required_for_done = queue_class == "blocking-before-done"
        record = present_fields.get(worker.output_field)
        active = bool(record and record.get("active", True))
        valid = bool(record and record.get("valid"))
        consumable = bool(record and record.get("consumable", True))
        satisfied = bool(active and valid and consumable)
        rows[worker_id] = {
            "queue_class": queue_class,
            "required_for_done": required_for_done,
            "output_field": worker.output_field,
            "active": active,
            "valid": valid,
            "consumable": consumable,
            "satisfied": satisfied,
            "evidence_ref": record.get("evidence_ref") if record else None,
            "result": record.get("result") if record else None,
            "review_declared": record.get("review_declared", False) if record else False,
            "handoff_state": record.get("handoff_state") if record else None,
            "review_ready": record.get("review_ready", False) if record else False,
            "authorized_downstream_scope": record.get("authorized_downstream_scope", []) if record else [],
            "review_task_authorizations": record.get("review_task_authorizations", []) if record else [],
            "graph_requirements": record.get("graph_requirements", []) if record else [],
            "validation_errors": record.get("validation_errors", []) if record else [],
        }
        if required_for_done and not satisfied:
            if record and not active:
                unconsumable_blocking.append(worker_id)
            elif record and valid:
                unconsumable_blocking.append(worker_id)
            elif record:
                invalid_blocking.append(worker_id)
            else:
                missing_blocking.append(worker_id)
    unsatisfied_graph_requirements = [
        requirement for requirement in graph_requirements if requirement.get("status") != "satisfied"
    ]
    recovery_routes = recovery_routes_from_worker_records(card, present_fields)

    return {
        "closure_type": "worker_result_reconciliation",
        "required_workers": required_worker_ids(card),
        "missing_blocking_workers": missing_blocking,
        "invalid_blocking_workers": invalid_blocking,
        "unconsumable_blocking_workers": unconsumable_blocking,
        "graph_requirements": graph_requirements,
        "unsatisfied_graph_requirements": unsatisfied_graph_requirements,
        "recovery_routes": recovery_routes,
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


def done_promotion_errors(
    metadata: dict[str, Any] | None,
    *,
    from_status: str | None = None,
    to_status: str | None = None,
) -> list[str]:
    errors = receipt_reconciliation_errors(metadata)
    if from_status is not None and to_status is not None and isinstance(metadata, dict):
        errors.extend(
            validate_transition_event_matches(
                metadata,
                from_status=from_status,
                to_status=to_status,
            )
        )
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
    graph_completion = (
        build_worker_closure(card, receipt or {}, worker_results_dir)
        if transition_consumes_graph_requirements(normalized_to)
        else None
    )
    graph_requirements = graph_completion.get("graph_requirements", []) if graph_completion else []
    unsatisfied_graph_requirements = (
        graph_completion.get("unsatisfied_graph_requirements", []) if graph_completion else []
    )
    recovery_routes = graph_completion.get("recovery_routes", []) if graph_completion else []
    review_ready_handoffs: list[dict[str, Any]] = []
    review_task_authorizations: list[dict[str, Any]] = []
    if graph_completion:
        for worker_id, row in graph_completion.get("workers", {}).items():
            if not row.get("review_ready"):
                continue
            row_authorizations = list(row.get("review_task_authorizations", []))
            review_ready_handoffs.append(
                {
                    "worker_id": worker_id,
                    "output_field": row.get("output_field"),
                    "handoff_state": row.get("handoff_state"),
                    "evidence_ref": row.get("evidence_ref"),
                    "authorized_downstream_scope": row.get("authorized_downstream_scope", []),
                    "review_task_authorization_refs": [
                        authorization.get("requirement_id") for authorization in row_authorizations
                    ],
                }
            )
            review_task_authorizations.extend(row_authorizations)
    if graph_requirements:
        attach_graph_requirement_tasks(worker_tasks, graph_requirements, card, source_path)
    if recovery_routes:
        attach_recovery_routes_to_tasks(worker_tasks, recovery_routes, card, source_path)
    downstream_authorizations = downstream_task_authorizations(graph_requirements, worker_tasks)

    def append_unsatisfied_graph_requirement_blocks() -> None:
        for requirement in unsatisfied_graph_requirements:
            reason = graph_requirement_block_reason(requirement)
            if reason not in blocked_reasons:
                blocked_reasons.append(reason)

    def worker_result_satisfied(worker_id: str) -> bool:
        if not graph_completion:
            return False
        row = graph_completion.get("workers", {}).get(worker_id, {})
        return bool(row.get("satisfied") or row.get("review_ready"))

    def append_invalid_review_handoff_blocks() -> None:
        if not graph_completion:
            return
        for row in graph_completion.get("workers", {}).values():
            if row.get("review_declared") and not row.get("valid"):
                field = str(row.get("output_field") or "worker result")
                reason = f"{field} cannot authorize review because result is invalid"
                if reason not in blocked_reasons:
                    blocked_reasons.append(reason)

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
            if not worker_result_satisfied(worker_id):
                blocked_reasons.append(f"{worker_id} result is required before ready")
        append_unsatisfied_graph_requirement_blocks()
        if blocked_reasons and before_ready:
            transition_action = "block_and_create_before_ready_tasks"
        else:
            transition_action = "block_transition" if blocked_reasons else "allow_and_create_worker_tasks"
        completion = graph_completion
    elif transition_is_review_ready(normalized_to):
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
            if not worker_result_satisfied(worker_id):
                blocked_reasons.append(f"{worker_id} result is required before review-ready")
        append_invalid_review_handoff_blocks()
        transition_action = "block_transition" if blocked_reasons else "allow_review_ready"
        completion = graph_completion
    elif normalized_to in {"done", "closed", "complete"}:
        blocked_reasons.extend(gate["card_validation_errors"])
        for worker_id in gate["blocked_workers"]:
            blocked_reasons.append(f"{worker_id} missing inputs before done")
        if receipt is None:
            blocked_reasons.append("receipt metadata is required for done transition")
            completion = graph_completion
            append_unsatisfied_graph_requirement_blocks()
        else:
            blocked_reasons.extend(
                validate_completion(
                    card,
                    receipt,
                    from_status=from_status,
                    to_status=to_status,
                )
            )
            completion = graph_completion
            for worker_id in completion["missing_blocking_workers"]:
                blocked_reasons.append(f"{worker_id} result is required before done")
            for worker_id in completion.get("invalid_blocking_workers", []):
                blocked_reasons.append(f"{worker_id} result is invalid before done")
            for worker_id in completion.get("unconsumable_blocking_workers", []):
                worker = WORKERS[worker_id]
                record = completion.get("workers", {}).get(worker_id, {})
                requirements = record.get("graph_requirements", [])
                if requirements:
                    for requirement in requirements:
                        if requirement.get("status") != "satisfied":
                            reason = graph_requirement_block_reason(requirement)
                            if reason not in blocked_reasons:
                                blocked_reasons.append(reason)
                else:
                    blocked_reasons.append(f"{worker_id} result is not consumable before done")
            append_unsatisfied_graph_requirement_blocks()
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
        "graph_requirements": graph_requirements,
        "recovery_routes": recovery_routes,
        "review_ready_handoffs": review_ready_handoffs,
        "review_task_authorizations": review_task_authorizations,
        "downstream_task_authorizations": downstream_authorizations,
        "completion_reconciliation": completion,
    }


def card_ref(card: dict[str, Any]) -> dict[str, Any]:
    return sanitize_public_refs({
        "card_id": card.get("card_id"),
        "slice_id": card.get("slice_id"),
        "phase": card.get("phase"),
        "risk_effective": card.get("risk_effective"),
        "surfaces": card.get("surfaces", []),
        "executor_identity": card.get("executor_identity"),
        "reviewer_identity": card.get("reviewer_identity"),
    })


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
    reviewer_required: bool = False,
    review_worker_id: str | None = None,
    reviewer_result: str | None = None,
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
    review_worker = review_worker_id if review_worker_id in WORKERS else "independent-reviewer"
    allowed_transition_scopes = ["review"] if reviewer_required and positive_authority else ["done"] if positive_authority else []
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
            "predicate": (
                "worker result is valid and authorizes only the required review child"
                if reviewer_required and positive_authority
                else "worker result is PASS/WAIVED, valid, scoped to the current card, and has blocking_findings=false"
            ),
            "allowed_transition_scopes": allowed_transition_scopes,
            "active": True,
        },
    }
    if reviewer_required:
        payload.update(
            {
                "reviewer_required": True,
                "review_worker_id": review_worker,
                "reviewer_result": reviewer_result or "PENDING",
                "handoff_state": "implementation_ready_for_review" if positive_authority else "blocked",
                "review_declared": True,
                "review_ready": positive_authority,
                "authorized_downstream_scope": ["review"] if positive_authority else [],
                "review_required_handoff": {
                    "review_required": True,
                    "review_worker_id": review_worker,
                    "required_review_field": WORKERS[review_worker].output_field,
                    "authorized_scope": ["review"],
                    "forbidden_scope_until_review_pass": [
                        "release",
                        "deployment",
                        "github_mutation",
                        "issue_completion",
                        "product_acceptance",
                    ],
                },
            }
        )
    if result == "BLOCKED":
        payload["recovery_recommendation"] = recovery_recommendation_for_worker(
            worker_id=worker_id,
            card=card,
            reason=findings_summary or next_action or "blocked worker result",
        )
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
                "professional_design_process_ref": "card.professional_design_process",
                "professional_design_process_comparison": {
                    "status": "pass" if not blocking_findings else "fail",
                    "basis": "Product Face evidence is explicitly compared to the professional design process.",
                },
                "reference_quality_comparison": {
                    "status": "pass" if not blocking_findings else "fail",
                    "basis": "Product Face evidence is compared against the selected design/reference library packet.",
                    "reference_set_ref": "card.professional_design_process.reference_research",
                    "compared_source_ids": ["design-library-reference", "component-registry-reference", "product-flow-reference"],
                    "reviewer_independent_from_implementation": not blocking_findings,
                    "dimensions": {
                        dimension: {
                            "status": "pass" if not blocking_findings else "fail",
                            "basis": f"{dimension} compared against selected reference patterns.",
                        }
                        for dimension in REFERENCE_COMPARISON_DIMENSIONS
                    },
                },
                "visual_quality_result": {
                    "status": "PASS" if not blocking_findings else "BLOCK",
                    "reviewer": "independent-product-face-reviewer",
                    "basis": (
                        "Professional visual quality bar reviewed for this bounded card."
                        if not blocking_findings
                        else "Product Face result is blocked; professional visual quality approval was not granted."
                    ),
                    "reference_quality_bar_checked": not blocking_findings,
                    "ai_generic_symptoms": [] if not blocking_findings else ["visual quality approval blocked"],
                    "residuals": [],
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


def _snapshot_state_from_gate(card: dict[str, Any], gate_report: dict[str, Any]) -> str:
    explicit_state = str(card.get("status") or "").strip().lower()
    if explicit_state in {
        "planning",
        "blocked",
        "ready",
        "executing",
        "reviewing",
        "human_gate",
        "release_candidate",
        "released",
        "archived",
        "superseded",
    }:
        return explicit_state
    if card.get("superseded_by"):
        return "superseded"
    gate_status = str(gate_report.get("gate_status") or "").strip()
    if gate_status == "blocked":
        return "blocked"
    if gate_status == "ready_for_worker_execution":
        return "ready"
    return "planning"


def _snapshot_blockers(gate_report: dict[str, Any]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for error in _list_items(gate_report.get("card_validation_errors")):
        blockers.append(
            {
                "kind": "card_validation",
                "owner": "operator",
                "summary": error,
                "unblock_condition": "Fix the canonical card contract and rerun gate-report.",
            }
        )
    for worker_id in _list_items(gate_report.get("blocked_workers")):
        blockers.append(
            {
                "kind": "worker_input",
                "owner": worker_id,
                "summary": f"{worker_id} is blocked by missing inputs",
                "unblock_condition": "Attach required source fields or worker evidence before dispatch.",
            }
        )
    return blockers


def build_status_snapshot(
    card: dict[str, Any],
    card_path: Path,
    *,
    gate_report: dict[str, Any] | None = None,
    lane_contracts: list[dict[str, Any]] | None = None,
    evidence_refs: list[str] | None = None,
) -> dict[str, Any]:
    effective_gate_report = gate_report or build_gate_report(card)
    effective_lanes = lane_contracts if lane_contracts is not None else card_parallel_lane_contracts(card)
    blockers = _snapshot_blockers(effective_gate_report)
    current_state = _snapshot_state_from_gate(card, effective_gate_report)
    evidence = sorted(set(evidence_refs or _list_items(card.get("evidence_refs"))))
    source_refs = [
        {"claim": "card", "ref": source_card_ref(card_path)},
        {"claim": "gate_report", "ref": "factoryctl:gate-report"},
    ]
    if effective_lanes:
        source_refs.append({"claim": "parallel_lanes", "ref": "card.parallel_lane_contracts"})
    if evidence:
        source_refs.append({"claim": "evidence", "ref": "operator-provided-evidence-refs"})

    lane_rows = [
        {
            "lane_id": lane.get("lane_id"),
            "status": lane.get("status"),
            "owner_agent": lane.get("owner_agent"),
            "worktree_ref": lane.get("worktree_ref"),
            "write_scope": _lane_write_scope(lane),
            "expected_artifact": lane.get("expected_artifact"),
            "reviewer_or_synthesizer": lane.get("reviewer_or_synthesizer"),
            "conflict_risk": lane.get("conflict_risk"),
        }
        for lane in effective_lanes
    ]

    gate_status = str(effective_gate_report.get("gate_status") or "not_run")
    validation_passed = gate_status in {"ready_for_worker_execution", "pass_no_workers_required"} and not blockers
    state_flags = {
        "implemented": bool(card.get("implementation_result") or card.get("changed_paths")),
        "validated": validation_passed,
        "integrated": bool(card.get("integrated_ref")),
        "released": current_state == "released" or bool(card.get("release_ref")),
        "blocked": current_state == "blocked" or bool(blockers),
        "superseded": current_state == "superseded",
    }

    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-status-snapshot.schema.json",
        "record_type": "factory_status_snapshot",
        "created_at": utc_now(),
        "card": {
            "id": str(card.get("card_id") or card.get("id") or "unknown-card"),
            "title": str(card.get("title") or card.get("card_id") or "Untitled factory card"),
            "ref": source_card_ref(card_path),
        },
        "current_state": current_state,
        "phase": str(card.get("phase") or "unknown"),
        "risk_effective": str(card.get("risk_effective") or "unknown"),
        "source_refs": source_refs,
        "staleness": {
            "status": "manual_estimate" if gate_report is None else "fresh",
            "last_updated_ref": source_card_ref(card_path),
            "warning": (
                "Snapshot was built from local card data and a generated gate report; Hermes remains source of truth."
                if gate_report is None
                else "Snapshot was built from caller-provided gate report; verify it is current."
            ),
        },
        "workers": {
            "required": effective_gate_report.get("required_workers", []),
            "blocked": effective_gate_report.get("blocked_workers", []),
            "rows": effective_gate_report.get("workers", {}),
        },
        "lanes": lane_rows,
        "gates": {
            "gate_status": gate_status,
            "gate_predicate_result": effective_gate_report.get("gate_predicate_result"),
            "warnings": effective_gate_report.get("card_validation_warnings", []),
        },
        "blockers": blockers,
        "blocker_economics": effective_gate_report.get("blocker_economics", []),
        "evidence": {
            "receipt_five_status": "attached" if isinstance(card.get("receipt_five"), dict) else "not_attached",
            "evidence_refs": evidence,
        },
        "state_flags": state_flags,
        "next_safe_actions": [
            str(item.get("action") if isinstance(item, dict) else item)
            for item in effective_gate_report.get("next_safe_actions", [])
            if str(item.get("action") if isinstance(item, dict) else item).strip()
        ],
        "forbidden_actions": _list_items(card.get("forbidden_actions")) + ["treat-snapshot-as-source-of-truth"],
        "public_private_boundary": {
            "projection_not_source_of_truth": True,
            "no_raw_logs": True,
            "no_private_paths": True,
            "no_private_ids": True,
            "note": "Link to canonical evidence; do not embed private runtime logs or screenshots.",
        },
        "continuation": "Continue from the canonical card, gate report, lane contracts and worker results; do not use this snapshot as authority.",
    }


def load_workflow_catalog(path: Path | None = None) -> dict[str, Any]:
    catalog_path = path or DEFAULT_WORKFLOW_CATALOG
    if not catalog_path.exists():
        return {
            "record_type": "factory_workflow_catalog",
            "factory_method_version": "OVERKILL_VFINAL",
            "catalog_version": "missing",
            "phases": [],
        }
    return load_json_like(catalog_path)


def workflow_phase_for_card(card: dict[str, Any], catalog: dict[str, Any]) -> dict[str, Any]:
    phase = str(card.get("phase") or "unknown").strip()
    for row in catalog.get("phases", []) if isinstance(catalog.get("phases"), list) else []:
        if isinstance(row, dict) and str(row.get("phase_id") or "").strip().upper() == phase.upper():
            return row
    return {
        "phase_id": phase or "unknown",
        "phase_name": "Unknown phase",
        "operator_visible_summary": "Factory phase is not present in the workflow catalog.",
        "blocked_actions": ["advance without a cataloged gate"],
        "required_artifacts": [],
        "required_gates": [],
        "required_workers": [],
        "related_command_refs": ["factoryctl gate-report"],
    }


def truth_scope_for_card(card: dict[str, Any]) -> str:
    if card.get("release_ref") or card.get("production_release_ref"):
        return "production_ready"
    receipt = card.get("receipt_five") if isinstance(card.get("receipt_five"), dict) else {}
    completion = card.get("completion_audit") if isinstance(card.get("completion_audit"), dict) else {}
    if str(receipt.get("verification_result") or "").strip().upper() in {"PASS", "WAIVED"}:
        return "bounded_proof"
    if str(completion.get("result") or "").strip().upper() == "PASS":
        return "bounded_proof"
    runtime_contract = card.get("runtime_contract") if isinstance(card.get("runtime_contract"), dict) else {}
    if runtime_contract.get("hermes_backed") is True or runtime_contract.get("runtime_state_ref"):
        return "runtime_backed"
    return "repo_only"


def help_action_from_gate(card: dict[str, Any], gate_report: dict[str, Any], phase_row: dict[str, Any]) -> dict[str, Any]:
    errors = _list_items(gate_report.get("card_validation_errors"))
    blocked_workers = _list_items(gate_report.get("blocked_workers"))
    command_refs = _list_items(phase_row.get("related_command_refs")) or ["factoryctl gate-report"]

    if any("product_sot" in error.lower() for error in errors):
        return {
            "owner": "factory",
            "action": "create or attach the Product SOT and scope coverage before any implementation routing",
            "why": "The product source of truth is the canonical scope; the input paper is source material, not execution authority.",
            "command_refs": command_refs,
        }
    if any("product_creation_plan" in error.lower() for error in errors):
        return {
            "owner": "factory",
            "action": "create or attach the Product Creation Plan before implementation",
            "why": "Execution slices cannot replace the complete production-ready product plan.",
            "command_refs": command_refs,
        }
    if any("product_implementation_readiness" in error.lower() for error in errors):
        return {
            "owner": "factory",
            "action": "produce Product Implementation Readiness before dispatching material work",
            "why": "The factory must prove the plan, context and work units are aligned before execution.",
            "command_refs": command_refs,
        }
    if any("specialist_research_plan" in error.lower() for error in errors):
        return {
            "owner": "factory",
            "action": "run Specialist Research OS and resolve it into operational decisions",
            "why": "Research only counts when it changes or confirms SOT, method, gates or proof.",
            "command_refs": command_refs,
        }
    if any("method_contract" in error.lower() for error in errors):
        return {
            "owner": "factory",
            "action": "record the Method Contract before creating execution work",
            "why": "The user should not choose internal method machinery; the factory records the route.",
            "command_refs": command_refs,
        }
    if errors:
        return {
            "owner": "factory",
            "action": "repair the canonical factory card contract before asking the user for decisions",
            "why": errors[0],
            "command_refs": ["factoryctl validate-card", "factoryctl gate-report"],
        }
    if blocked_workers:
        return {
            "owner": "factory",
            "action": "prepare the missing worker inputs or evidence for the blocked workers",
            "why": "Blocked worker inputs are factory coordination work, not open-ended user labor.",
            "command_refs": ["factoryctl worker-packet", "factoryctl gate-report"],
        }
    if gate_report.get("gate_predicate_result") == "PASS" and _list_items(gate_report.get("required_workers")):
        return {
            "owner": "factory",
            "action": "generate required worker packets and dispatch through the selected runtime gate",
            "why": "The current card is ready for worker execution within its authority limits.",
            "command_refs": ["factoryctl worker-packet", "factoryctl transition-plan"],
        }
    return {
        "owner": "factory",
        "action": "continue the cataloged workflow from the current phase",
        "why": str(phase_row.get("operator_visible_summary") or "No blocking gate is present."),
        "command_refs": command_refs,
    }


def user_decisions_for_card(card: dict[str, Any], gate_report: dict[str, Any]) -> list[dict[str, str]]:
    decisions: list[dict[str, str]] = []
    contract = card.get("user_facing_autonomy_contract") if isinstance(card.get("user_facing_autonomy_contract"), dict) else {}
    for question in contract.get("user_questions", []) if isinstance(contract.get("user_questions"), list) else []:
        if not isinstance(question, dict):
            continue
        question_class = str(question.get("class") or "").strip()
        if question_class in ALLOWED_USER_QUESTION_CLASSES and not _contains_internal_coordination_request(question.get("question")):
            decisions.append(
                {
                    "decision_type": question_class,
                    "reason": str(question.get("question") or "User decision is required."),
                    "user_action": "answer, approve, reject or defer this bounded question",
                    "factory_prepares": str(question.get("factory_resolution_path") or "decision packet"),
                }
            )

    review = card.get("review") if isinstance(card.get("review"), dict) else {}
    if review.get("human_gate_required") is True or "human-gate-clerk" in _list_items(gate_report.get("required_workers")):
        decisions.append(
            {
                "decision_type": "authority_required",
                "reason": "Human gate is required by risk, authority or release policy.",
                "user_action": "approve, reject or request changes on the bounded gate packet",
                "factory_prepares": "human gate packet with scope, risk, evidence and forbidden actions",
            }
        )

    access = card.get("access_capability") if isinstance(card.get("access_capability"), dict) else {}
    if card.get("requires_access") is True or _list_items(access.get("missing_capabilities")):
        decisions.append(
            {
                "decision_type": "access_required",
                "reason": "Material execution needs access or capability that the factory cannot grant by itself.",
                "user_action": "grant, deny or defer the named access",
                "factory_prepares": "access request with scope, least privilege and stop conditions",
            }
        )

    return decisions


def build_factory_help(card: dict[str, Any], card_path: Path, *, catalog_path: Path | None = None) -> dict[str, Any]:
    catalog = load_workflow_catalog(catalog_path)
    phase_row = workflow_phase_for_card(card, catalog)
    gate_report = build_gate_report(card)
    factory_action = help_action_from_gate(card, gate_report, phase_row)
    blocked_workers = _list_items(gate_report.get("blocked_workers"))
    validation_errors = _list_items(gate_report.get("card_validation_errors"))
    next_actions: list[str] = []
    for item in gate_report.get("next_safe_actions", []):
        next_action_text = str(item.get("action") if isinstance(item, dict) else item).strip()
        if next_action_text and next_action_text not in next_actions:
            next_actions.append(next_action_text)

    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-help.schema.json",
        "record_type": "factory_help_next_action",
        "created_at": utc_now(),
        "card_id": str(card.get("card_id") or "unknown-card"),
        "phase": str(card.get("phase") or "unknown"),
        "workflow_phase": {
            "phase_id": str(phase_row.get("phase_id") or card.get("phase") or "unknown"),
            "phase_name": str(phase_row.get("phase_name") or "Unknown phase"),
            "operator_visible_summary": str(phase_row.get("operator_visible_summary") or ""),
        },
        "gate_status": str(gate_report.get("gate_status") or "not_run"),
        "truth_scope": truth_scope_for_card(card),
        "factory_next_action": factory_action,
        "user_decision_required": user_decisions_for_card(card, gate_report),
        "blocked_because": validation_errors + [f"{worker_id} is blocked by missing inputs" for worker_id in blocked_workers],
        "blocked_actions": sorted(set(_list_items(phase_row.get("blocked_actions")) + _list_items(card.get("forbidden_actions")))),
        "evidence_needed": next_actions or _list_items(phase_row.get("required_artifacts")) + _list_items(phase_row.get("required_gates")),
        "required_workers": _list_items(gate_report.get("required_workers")),
        "blocked_workers": blocked_workers,
        "source_refs": [
            {"claim": "card", "ref": source_card_ref(card_path)},
            {"claim": "workflow_catalog", "ref": source_card_ref(catalog_path or DEFAULT_WORKFLOW_CATALOG)},
            {"claim": "gate_report", "ref": "factoryctl:gate-report"},
        ],
        "public_private_boundary": {
            "no_raw_logs": True,
            "no_private_paths": True,
            "no_private_ids": True,
            "projection_not_source_of_truth": True,
        },
        "limits": [
            "This help output does not execute workers, approve gates, or replace Hermes/runtime truth.",
            "The operator/user should see bounded decisions, blockers and proof, not internal worker coordination.",
        ],
    }


def validate_status_snapshot(snapshot: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(snapshot.get("source_refs"), list) or not snapshot.get("source_refs"):
        errors.append("factory_status_snapshot.source_refs is required")
    staleness = snapshot.get("staleness") if isinstance(snapshot.get("staleness"), dict) else {}
    if staleness.get("status") == "stale" and snapshot.get("current_state") in {"ready", "released"}:
        errors.append("stale snapshot cannot claim ready or released")
    gates = snapshot.get("gates") if isinstance(snapshot.get("gates"), dict) else {}
    blockers = snapshot.get("blockers") if isinstance(snapshot.get("blockers"), list) else []
    flags = snapshot.get("state_flags") if isinstance(snapshot.get("state_flags"), dict) else {}
    if gates.get("gate_status") == "blocked" and not blockers:
        errors.append("blocked gate state requires blockers")
    if flags.get("blocked") is True and not blockers:
        errors.append("state_flags.blocked=true requires blockers")
    if not _list_items(snapshot.get("next_safe_actions")):
        errors.append("factory_status_snapshot.next_safe_actions is required")
    boundary = snapshot.get("public_private_boundary") if isinstance(snapshot.get("public_private_boundary"), dict) else {}
    for field in ("projection_not_source_of_truth", "no_raw_logs", "no_private_paths", "no_private_ids"):
        if boundary.get(field) is not True:
            errors.append(f"factory_status_snapshot.public_private_boundary.{field} must be true")
    return errors


def load_optional_json(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    try:
        data = load_json_like(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def collect_worker_result_records(worker_results_dir: Path | None) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if worker_results_dir is None or not worker_results_dir.exists():
        return records
    for path in sorted(worker_results_dir.glob("*.json")):
        data = load_optional_json(path)
        if not data:
            continue
        record_type = str(data.get("record_type") or "").strip()
        if not record_type:
            continue
        current = records.get(record_type)
        if current is None or str(data.get("created_at") or "") >= str(current.get("created_at") or ""):
            records[record_type] = {**data, "_public_ref": source_card_ref(path)}
    return records


def graph_add_node(nodes: dict[str, dict[str, Any]], node: dict[str, Any]) -> None:
    nodes[str(node["id"])] = node


def graph_add_edge(edges: list[dict[str, str]], source: str, target: str, relation: str) -> None:
    edges.append({"source": source, "target": target, "relation": relation})


def build_evidence_graph(
    card: dict[str, Any],
    card_path: Path,
    *,
    gate_report: dict[str, Any] | None = None,
    worker_results_dir: Path | None = None,
    receipt_path: Path | None = None,
    hermes_evidence_path: Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    effective_gate = gate_report or build_gate_report(card)
    worker_results = collect_worker_result_records(worker_results_dir)
    worker_closure = build_worker_closure(card, {}, worker_results_dir) if worker_results_dir else None
    closure_by_field = {
        str(row.get("output_field") or ""): row
        for row in (worker_closure or {}).get("workers", {}).values()
        if isinstance(row, dict)
    }
    receipt = load_optional_json(receipt_path)
    hermes_package = load_optional_json(hermes_evidence_path)
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    findings: list[dict[str, str]] = []

    card_id = str(card.get("card_id") or card.get("id") or "unknown-card")
    graph_add_node(
        nodes,
        {
            "id": "card",
            "node_type": "factory_card",
            "ref": source_card_ref(card_path),
            "status": "PASS" if not validate_card(card) else "BLOCKED",
            "evidence_level": "contract_exists",
        },
    )
    for index, source in enumerate(_list_items(card.get("source_refs")), start=1):
        safe_ref, finding = sanitize_public_ref(source)
        node_id = f"source:{index}"
        graph_add_node(
            nodes,
            {
                "id": node_id,
                "node_type": "source_input",
                "ref": safe_ref,
                "status": "PASS" if finding is None else "BLOCKED",
                "evidence_level": "source_ref",
            },
        )
        graph_add_edge(edges, node_id, "card", "defines")
        if finding:
            findings.append({"severity": "BLOCKED", "node_id": node_id, "message": redact_private_text(finding["reason"])})

    gate_status = str(effective_gate.get("gate_status") or "missing")
    graph_add_node(
        nodes,
        {
            "id": "gate-report",
            "node_type": "gate_report",
            "ref": "factoryctl:gate-report",
            "status": "PASS" if gate_status != "blocked" else "BLOCKED",
            "evidence_level": "runtime_enforced",
        },
    )
    graph_add_edge(edges, "card", "gate-report", "validated_by")

    for worker_id in _list_items(effective_gate.get("required_workers")):
        worker = WORKERS[worker_id]
        packet_id = f"worker-packet:{worker_id}"
        result_id = f"worker-result:{worker.output_field}"
        graph_add_node(
            nodes,
            {
                "id": packet_id,
                "node_type": "worker_packet",
                "ref": f"factoryctl:worker-packet:{worker_id}",
                "status": "PASS",
                "worker_id": worker_id,
                "evidence_level": "runtime_enforced",
            },
        )
        graph_add_edge(edges, "gate-report", packet_id, "requires")
        result = worker_results.get(worker.output_field)
        if result is None:
            graph_add_node(
                nodes,
                {
                    "id": result_id,
                    "node_type": "worker_result",
                    "ref": f"missing:{worker.output_field}",
                    "status": "MISSING",
                    "worker_id": worker_id,
                    "evidence_level": "blocked_missing_evidence",
                    "staleness": "missing",
                },
            )
            findings.append(
                {
                    "severity": "BLOCKED",
                    "node_id": result_id,
                    "message": f"{worker.output_field} is missing",
                }
            )
        else:
            validation_errors = validate_worker_result_record(
                result,
                expected_field=worker.output_field,
                expected_worker_id=worker_id,
                card=card,
                evidence_root=ROOT,
            )
            safe_validation_errors = [redact_private_text(error) for error in validation_errors]
            result_status = str(result.get("result") or result.get("decision") or "UNKNOWN")
            stale = bool(result.get("superseded_by") or result.get("active") is False)
            closure_row = closure_by_field.get(worker.output_field, {})
            review_ready = bool(closure_row.get("review_ready"))
            graph_add_node(
                nodes,
                {
                    "id": result_id,
                    "node_type": "worker_result",
                    "ref": str(result.get("_public_ref") or f"external:{worker.output_field}"),
                    "status": "BLOCKED" if validation_errors or stale or result_status not in PROMOTION_PASS_RESULTS else "PASS",
                    "worker_id": worker_id,
                    "handoff_state": closure_row.get("handoff_state"),
                    "review_ready": review_ready,
                    "authorized_downstream_scope": closure_row.get("authorized_downstream_scope", []),
                    "graph_requirements": closure_row.get("graph_requirements", []),
                    "evidence_level": "worker_result",
                    "staleness": "stale" if stale else "current",
                    "validation_errors": safe_validation_errors,
                },
            )
            if review_ready:
                findings.append(
                    {
                        "severity": "BLOCKED",
                        "node_id": result_id,
                        "message": (
                            f"{worker.output_field} is implementation_ready_for_review; "
                            "only the matching review task may consume it until review PASS"
                        ),
                    }
                )
            for ref_index, ref in enumerate(_list_items(result.get("evidence_refs")), start=1):
                safe_ref, finding = sanitize_public_ref(ref)
                artifact_id = f"artifact:{worker.output_field}:{ref_index}"
                graph_add_node(
                    nodes,
                    {
                        "id": artifact_id,
                        "node_type": "artifact_ref",
                        "ref": safe_ref,
                        "status": "PASS" if finding is None else "BLOCKED",
                        "evidence_level": "artifact_ref",
                    },
                )
                graph_add_edge(edges, result_id, artifact_id, "cites")
                if finding:
                    findings.append({"severity": "BLOCKED", "node_id": artifact_id, "message": redact_private_text(finding["reason"])})
            if validation_errors:
                findings.append(
                    {
                        "severity": "BLOCKED",
                        "node_id": result_id,
                        "message": "; ".join(safe_validation_errors),
                    }
                )
        graph_add_edge(edges, packet_id, result_id, "expects")

    if receipt_path is not None:
        receipt_errors = validate_completion(card, receipt or {})
        graph_add_node(
            nodes,
            {
                "id": "receipt-five",
                "node_type": "receipt_five",
                "ref": source_card_ref(receipt_path),
                "status": "PASS" if receipt and not receipt_errors else "BLOCKED",
                "evidence_level": "receipt_five",
                "validation_errors": receipt_errors,
            },
        )
        graph_add_edge(edges, "gate-report", "receipt-five", "closed_by")
        if receipt_errors:
            findings.append({"severity": "BLOCKED", "node_id": "receipt-five", "message": "; ".join(receipt_errors)})

    if hermes_evidence_path is not None:
        package_result = str((hermes_package or {}).get("result") or "MISSING")
        graph_add_node(
            nodes,
            {
                "id": "hermes-evidence",
                "node_type": "hermes_evidence_package",
                "ref": source_card_ref(hermes_evidence_path),
                "status": "PASS" if package_result == "PASS" else "BLOCKED",
                "evidence_level": "live_hermes_summary",
            },
        )
        graph_add_edge(edges, "gate-report", "hermes-evidence", "summarized_by")
        if package_result != "PASS":
            findings.append({"severity": "BLOCKED", "node_id": "hermes-evidence", "message": "Hermes evidence package is missing or blocked"})

    blocked = any(item["severity"] == "BLOCKED" for item in findings)
    return {
        "$schema": "https://overkill-factory.dev/schemas/evidence-graph.schema.json",
        "record_type": "evidence_graph",
        "created_at": created_at or utc_now(),
        "target": {"card_id": card_id, "card_ref": source_card_ref(card_path)},
        "result": "BLOCKED" if blocked else "PASS",
        "nodes": list(nodes.values()),
        "edges": edges,
        "findings": findings,
        "public_private_boundary": {
            "public_safe_summary_only": True,
            "no_raw_logs": True,
            "no_private_paths": True,
            "no_private_ids": True,
        },
        "limits": [
            "Graph existence is not completion proof.",
            "Private Hermes evidence remains operator-owned and is represented only by sanitized summaries.",
        ],
    }


TRUTH_LEVEL_ORDER = [
    "contract_exists",
    "runtime_enforced",
    "bounded_public_proof",
    "live_hermes_proof",
    "product_specific_proof",
    "production_ready",
]


def readiness_component(
    capability_id: str,
    truth_level: str,
    result: str,
    evidence_refs: list[str],
    next_required_action: str,
) -> dict[str, Any]:
    return {
        "capability_id": capability_id,
        "truth_level": truth_level,
        "result": result,
        "evidence_refs": evidence_refs,
        "next_required_action": next_required_action,
        "blocker_economics": []
        if result == "PASS"
        else [
            blocker_economics_entry(
                blocker_id=f"truth:{capability_id}",
                owner="operator",
                risk_controlled=f"{capability_id} cannot be over-claimed as a stronger truth layer",
                cost_time_class="bounded_followup",
                dependency=capability_id,
                smallest_safe_next_action=next_required_action,
                mutation_risk="none_without_operator_action",
                route="local",
            )
        ],
    }


def build_readiness_truth_ledger(
    card: dict[str, Any],
    card_path: Path,
    *,
    evidence_graph: dict[str, Any] | None = None,
    production_readiness: dict[str, Any] | None = None,
    hermes_evidence: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    gate = build_gate_report(card)
    card_ok = not validate_card(card)
    graph_ok = bool(evidence_graph and evidence_graph.get("result") == "PASS")
    hermes_ok = bool(hermes_evidence and hermes_evidence.get("result") == "PASS")
    receipt_ok = bool(evidence_graph and any(node.get("id") == "receipt-five" and node.get("status") == "PASS" for node in evidence_graph.get("nodes", [])))
    production_ok = bool(production_readiness and production_readiness.get("result") == "PASS")
    components = [
        readiness_component(
            "card_contract",
            "contract_exists",
            "PASS" if card_ok else "BLOCKED",
            [source_card_ref(card_path)],
            "fix card contract and rerun factoryctl validate-card",
        ),
        readiness_component(
            "gate_report",
            "runtime_enforced",
            "PASS" if gate.get("gate_status") != "blocked" else "BLOCKED",
            ["factoryctl:gate-report"],
            "fix blocked gate inputs and rerun factoryctl gate-report",
        ),
        readiness_component(
            "evidence_graph",
            "bounded_public_proof",
            "PASS" if graph_ok else "BLOCKED",
            ["factoryctl:evidence-graph"],
            "supply missing worker results, receipts or sanitized Hermes evidence and rebuild the graph",
        ),
        readiness_component(
            "hermes_evidence_package",
            "live_hermes_proof",
            "PASS" if hermes_ok else "BLOCKED",
            ["factoryctl:export-hermes-evidence"],
            "export a sanitized local Hermes evidence package from the operator-owned runtime",
        ),
        readiness_component(
            "receipt_five",
            "product_specific_proof",
            "PASS" if receipt_ok else "BLOCKED",
            ["receipt-five"],
            "reconcile worker results and attach a valid Receipt Five",
        ),
        readiness_component(
            "production_readiness",
            "production_ready",
            "PASS" if production_ok else "BLOCKED",
            ["scripts/factory_production_readiness.py"],
            "pass production readiness only after product-specific and live proof receipts exist",
        ),
    ]
    passed_levels = [item["truth_level"] for item in components if item["result"] == "PASS"]
    overall = passed_levels[-1] if passed_levels else "blocked_missing_evidence"
    blockers = [item for component in components for item in component["blocker_economics"]]
    return {
        "$schema": "https://overkill-factory.dev/schemas/readiness-truth-ledger.schema.json",
        "record_type": "readiness_truth_ledger",
        "created_at": created_at or utc_now(),
        "target": {"card_id": card.get("card_id"), "card_ref": source_card_ref(card_path)},
        "overall_truth_level": overall,
        "production_ready": overall == "production_ready",
        "classification_order": TRUTH_LEVEL_ORDER,
        "components": components,
        "blocker_economics": blockers,
        "limits": [
            "A PASS in one truth layer never implies PASS in a stronger layer.",
            "Public-safe summaries do not replace private runtime evidence or human approval.",
        ],
    }


def build_hermes_evidence_package(
    *,
    board: str,
    workspace: Path,
    created_at: str | None = None,
) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    redactions: list[dict[str, str]] = []
    if workspace.exists():
        for index, path in enumerate(sorted(workspace.rglob("*.json")), start=1):
            data = load_optional_json(path)
            if not data:
                continue
            evidence_refs: list[str] = []
            for ref in _list_items(data.get("evidence_refs")):
                safe_ref, finding = sanitize_public_ref(ref)
                evidence_refs.append(safe_ref)
                if finding:
                    redactions.append({"record_ref": f"external:hermes-record-{index}", "reason": finding["reason"]})
            worker = data.get("worker") if isinstance(data.get("worker"), dict) else {}
            card_ref_value = data.get("card_ref") if isinstance(data.get("card_ref"), dict) else {}
            records.append(
                {
                    "record_ref": f"external:hermes-record-{index}",
                    "record_type": str(data.get("record_type") or "unknown"),
                    "card_id": str(card_ref_value.get("card_id") or data.get("card_id") or ""),
                    "worker_id": str(worker.get("id") or data.get("worker_id") or ""),
                    "result": str(data.get("result") or data.get("decision") or "UNKNOWN"),
                    "created_at": str(data.get("created_at") or data.get("decision_at") or ""),
                    "evidence_refs": evidence_refs,
                }
            )
    state = "blocked"
    if records:
        record_types = {record["record_type"] for record in records}
        if "release_ops_result" in record_types:
            state = "release-ready"
        elif any("receipt" in item for item in record_types):
            state = "done"
        elif any(record["worker_id"] or record["record_type"] != "unknown" for record in records):
            state = "partially_executed"
        else:
            state = "planning"
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-evidence-package.schema.json",
        "record_type": "hermes_evidence_package",
        "created_at": created_at or utc_now(),
        "result": "PASS" if workspace.exists() and records and not redactions else "BLOCKED",
        "board_ref": f"board:{sanitize_slug(board, fallback='operator-board')}",
        "workspace_ref": "external:operator-owned-hermes-workspace",
        "evidence_level": "live_hermes_summary" if records else "missing",
        "state": state,
        "records": records,
        "redaction_findings": redactions,
        "missing_or_stale": [] if records else ["no JSON evidence records found in workspace"],
        "public_private_boundary": {
            "sanitized_summary_only": True,
            "no_raw_logs": True,
            "no_private_paths": True,
            "no_private_ids": True,
        },
    }


def build_prepilot_loose_end_checklist(
    *,
    evidence_graph: dict[str, Any] | None,
    readiness_ledger: dict[str, Any] | None,
    hermes_evidence: dict[str, Any] | None,
    created_at: str | None = None,
) -> dict[str, Any]:
    graph_ok = bool(evidence_graph)
    ledger_ok = bool(readiness_ledger)
    hermes_path_ok = bool(hermes_evidence)
    items = [
        {
            "id": "evidence_graph_path",
            "status": "closed" if graph_ok else "blocking",
            "evidence_ref": "factoryctl:evidence-graph",
            "next_action": "build evidence graph before pilot execution",
        },
        {
            "id": "readiness_truth_levels",
            "status": "closed" if ledger_ok else "blocking",
            "evidence_ref": "factoryctl:readiness-ledger",
            "next_action": "build readiness truth ledger before pilot execution",
        },
        {
            "id": "hermes_evidence_import_path",
            "status": "closed" if hermes_path_ok else "deferred",
            "evidence_ref": "factoryctl:export-hermes-evidence",
            "next_action": "export sanitized Hermes package when operator runtime exists",
        },
        {
            "id": "tests_hermetic_against_tmp",
            "status": "deferred",
            "evidence_ref": "PR-121",
            "next_action": "land the foundation hermeticity PR before claiming pilot completion",
        },
        {
            "id": "blockers_next_smallest_safe_action",
            "status": "closed" if readiness_ledger and readiness_ledger.get("blocker_economics") is not None else "blocking",
            "evidence_ref": "readiness_ledger.blocker_economics",
            "next_action": "include blocker economics in gate, readiness and completion reports",
        },
        {
            "id": "production_evidence_expectations_known",
            "status": "closed",
            "evidence_ref": "factoryctl:truth",
            "next_action": "keep Product Face, security, remote proof, human gate and release evidence explicit in the truth packet",
        },
        {
            "id": "pilot_success_definition",
            "status": "closed",
            "evidence_ref": "readiness_ledger.overall_truth_level",
            "next_action": "state whether the pilot proves repo-only, Hermes-backed, bounded product proof or production readiness",
        },
    ]
    blocking = [item["id"] for item in items if item["status"] == "blocking"]
    return {
        "$schema": "https://overkill-factory.dev/schemas/prepilot-loose-end-checklist.schema.json",
        "record_type": "prepilot_loose_end_checklist",
        "created_at": created_at or utc_now(),
        "result": "BLOCKED" if blocking else "PASS_WITH_DEFERRED_ITEMS",
        "items": items,
        "blocking_items": blocking,
        "pilot_completion_claim_allowed": not blocking and bool(evidence_graph and evidence_graph.get("result") == "PASS"),
        "public_private_boundary": {
            "no_private_product_evidence": True,
            "no_raw_logs": True,
            "no_private_paths": True,
        },
    }


def run_json_command(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=20)  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": exc.__class__.__name__}
    if result.returncode != 0:
        return {"available": False, "error": "command_failed"}
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return {"available": False, "error": "invalid_json"}
    return {"available": True, "data": data}


def run_text_command(command: list[str]) -> dict[str, Any]:
    try:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, timeout=20)  # nosec B603
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"available": False, "error": exc.__class__.__name__, "text": ""}
    return {
        "available": result.returncode == 0,
        "error": None if result.returncode == 0 else "command_failed",
        "text": result.stdout.strip(),
    }


def build_truth_packet(
    *,
    target: str,
    card: dict[str, Any],
    card_path: Path,
    issue: str | None = None,
    pr: str | None = None,
    worker_results_dir: Path | None = None,
    hermes_evidence_path: Path | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    branch = run_text_command(["git", "branch", "--show-current"])
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True)  # nosec B603
    issue_state = run_json_command(["gh", "issue", "view", issue, "--json", "number,title,state"]) if issue else {"available": False}
    pr_state = run_json_command(["gh", "pr", "view", pr, "--json", "number,title,state,isDraft"]) if pr else {"available": False}
    hermes_package = load_optional_json(hermes_evidence_path)
    graph = build_evidence_graph(card, card_path, worker_results_dir=worker_results_dir, hermes_evidence_path=hermes_evidence_path)
    ledger = build_readiness_truth_ledger(card, card_path, evidence_graph=graph, hermes_evidence=hermes_package)
    blockers = ledger.get("blocker_economics", [])
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-truth-packet.schema.json",
        "record_type": "factory_truth_packet",
        "created_at": created_at or utc_now(),
        "target": sanitize_slug(target, fallback="factory-target"),
        "repo": {
            "branch": branch.get("text") or "unknown",
            "dirty": bool(dirty.stdout.strip()),
            "dirty_file_count": len([line for line in dirty.stdout.splitlines() if line.strip()]),
        },
        "github": {
            "issue": issue_state,
            "pr": pr_state,
        },
        "hermes": {
            "mode": "sanitized_package" if hermes_package else "repo_only_degraded",
            "status": (hermes_package or {}).get("result") or "DEGRADED",
        },
        "evidence_graph": graph,
        "readiness_ledger": ledger,
        "current_blockers": blockers,
        "next_smallest_safe_action": blockers[0]["smallest_safe_next_action"] if blockers else "review and approve only after stronger evidence remains current",
        "truth_level": ledger["overall_truth_level"],
        "production_ready": ledger["production_ready"],
        "public_private_boundary": {
            "json_first": True,
            "no_raw_logs": True,
            "no_private_paths": True,
            "no_private_ids": True,
        },
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
    receipt = load_json_like(args.receipt) if args.receipt else None
    plan = build_factory_recovery_plan(load_json_like(args.card), worker_results_dir=args.worker_results_dir, receipt=receipt)
    write_json(args.out, plan)
    return 1 if plan.get("gate_predicate_result") == "BLOCK" else 0


def command_recovery_plan(args: argparse.Namespace) -> int:
    receipt = load_json_like(args.receipt) if args.receipt else None
    plan = build_factory_recovery_plan(load_json_like(args.card), worker_results_dir=args.worker_results_dir, receipt=receipt)
    write_json(args.out, plan)
    return 1 if plan.get("gate_predicate_result") == "BLOCK" else 0


def command_help_next(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    payload = build_factory_help(card, args.card, catalog_path=args.catalog)
    write_json(args.out, payload)
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
            reviewer_required=args.reviewer_required,
            review_worker_id=args.review_worker_id,
            reviewer_result=args.reviewer_result,
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


def command_status_snapshot(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    gate_report = load_json_like(args.gate_report) if args.gate_report else None
    lane_contracts = [load_json_like(path) for path in args.lane_contract or []]
    if not lane_contracts:
        lane_contracts = card_parallel_lane_contracts(card)
    snapshot = build_status_snapshot(
        card,
        args.card,
        gate_report=gate_report,
        lane_contracts=lane_contracts,
        evidence_refs=args.evidence_ref or [],
    )
    errors = validate_status_snapshot(snapshot)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    write_json(args.out, snapshot)
    return 0


def command_evidence_graph(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    graph = build_evidence_graph(
        card,
        args.card,
        gate_report=load_optional_json(args.gate_report),
        worker_results_dir=args.worker_results_dir,
        receipt_path=args.receipt,
        hermes_evidence_path=args.hermes_evidence,
    )
    write_json(args.out, graph)
    return 0 if graph["result"] == "PASS" else 1


def command_readiness_ledger(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    graph = load_optional_json(args.evidence_graph)
    readiness = load_optional_json(args.production_readiness)
    hermes = load_optional_json(args.hermes_evidence)
    ledger = build_readiness_truth_ledger(
        card,
        args.card,
        evidence_graph=graph,
        production_readiness=readiness,
        hermes_evidence=hermes,
    )
    write_json(args.out, ledger)
    return 0 if ledger["production_ready"] else 1


def command_export_hermes_evidence(args: argparse.Namespace) -> int:
    package = build_hermes_evidence_package(board=args.board, workspace=args.workspace)
    write_json(args.out, package)
    if args.md_out:
        lines = [
            "# Hermes Evidence Package",
            "",
            f"Result: `{package['result']}`",
            f"State: `{package['state']}`",
            f"Records: `{len(package['records'])}`",
            "",
            "This is a sanitized operator-owned summary. Raw Hermes evidence stays local.",
            "",
        ]
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines), encoding="utf-8")
    return 0 if package["result"] == "PASS" else 1


def command_prepilot_checklist(args: argparse.Namespace) -> int:
    checklist = build_prepilot_loose_end_checklist(
        evidence_graph=load_optional_json(args.evidence_graph),
        readiness_ledger=load_optional_json(args.readiness_ledger),
        hermes_evidence=load_optional_json(args.hermes_evidence),
    )
    write_json(args.out, checklist)
    return 0 if checklist["pilot_completion_claim_allowed"] else 1


def command_truth(args: argparse.Namespace) -> int:
    card = load_json_like(args.card)
    packet = build_truth_packet(
        target=args.target,
        card=card,
        card_path=args.card,
        issue=args.issue,
        pr=args.pr,
        worker_results_dir=args.worker_results_dir,
        hermes_evidence_path=args.hermes_evidence,
    )
    write_json(args.out, packet)
    if args.md_out:
        lines = [
            "# Factory Truth Packet",
            "",
            f"Target: `{packet['target']}`",
            f"Truth level: `{packet['truth_level']}`",
            f"Production ready: `{str(packet['production_ready']).lower()}`",
            "",
            f"Next action: {packet['next_smallest_safe_action']}",
            "",
        ]
        args.md_out.parent.mkdir(parents=True, exist_ok=True)
        args.md_out.write_text("\n".join(lines), encoding="utf-8")
    return 0 if packet["production_ready"] else 1


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
    print(f"Initialized Overkill Factory workspace at {public_path_ref(args.out, fallback='workspace')}")
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
    unblock_plan_parser.add_argument("--receipt", type=Path)
    unblock_plan_parser.add_argument("--worker-results-dir", type=Path)
    unblock_plan_parser.add_argument("--out", type=Path)
    unblock_plan_parser.set_defaults(func=command_unblock_plan)

    recovery_plan_parser = sub.add_parser("recovery-plan", help="Emit semantic recovery routes without replacing Hermes runtime state.")
    recovery_plan_parser.add_argument("--card", type=Path, required=True)
    recovery_plan_parser.add_argument("--receipt", type=Path)
    recovery_plan_parser.add_argument("--worker-results-dir", type=Path)
    recovery_plan_parser.add_argument("--out", type=Path)
    recovery_plan_parser.set_defaults(func=command_recovery_plan)

    help_next_parser = sub.add_parser("help-next", help="Show the next safe action without making the user operate internal factory machinery.")
    help_next_parser.add_argument("--card", type=Path, required=True)
    help_next_parser.add_argument("--catalog", type=Path)
    help_next_parser.add_argument("--out", type=Path)
    help_next_parser.set_defaults(func=command_help_next)

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
    evidence_record_parser.add_argument("--reviewer-required", action="store_true")
    evidence_record_parser.add_argument("--review-worker-id")
    evidence_record_parser.add_argument("--reviewer-result")
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

    status_snapshot_parser = sub.add_parser("status-snapshot")
    status_snapshot_parser.add_argument("--card", type=Path, required=True)
    status_snapshot_parser.add_argument("--gate-report", type=Path)
    status_snapshot_parser.add_argument("--lane-contract", type=Path, action="append")
    status_snapshot_parser.add_argument("--evidence-ref", action="append")
    status_snapshot_parser.add_argument("--out", type=Path)
    status_snapshot_parser.set_defaults(func=command_status_snapshot)

    evidence_graph_parser = sub.add_parser("evidence-graph")
    evidence_graph_parser.add_argument("--card", type=Path, required=True)
    evidence_graph_parser.add_argument("--gate-report", type=Path)
    evidence_graph_parser.add_argument("--worker-results-dir", type=Path)
    evidence_graph_parser.add_argument("--receipt", type=Path)
    evidence_graph_parser.add_argument("--hermes-evidence", type=Path)
    evidence_graph_parser.add_argument("--out", type=Path, default=DEFAULT_EVIDENCE_GRAPH_OUT)
    evidence_graph_parser.set_defaults(func=command_evidence_graph)

    readiness_ledger_parser = sub.add_parser("readiness-ledger")
    readiness_ledger_parser.add_argument("--card", type=Path, required=True)
    readiness_ledger_parser.add_argument("--evidence-graph", type=Path)
    readiness_ledger_parser.add_argument("--production-readiness", type=Path)
    readiness_ledger_parser.add_argument("--hermes-evidence", type=Path)
    readiness_ledger_parser.add_argument("--out", type=Path, default=DEFAULT_READINESS_LEDGER_OUT)
    readiness_ledger_parser.set_defaults(func=command_readiness_ledger)

    export_hermes_parser = sub.add_parser("export-hermes-evidence")
    export_hermes_parser.add_argument("--board", required=True)
    export_hermes_parser.add_argument("--workspace", type=Path, required=True)
    export_hermes_parser.add_argument("--out", type=Path, default=DEFAULT_HERMES_EVIDENCE_OUT)
    export_hermes_parser.add_argument("--md-out", type=Path)
    export_hermes_parser.set_defaults(func=command_export_hermes_evidence)

    prepilot_parser = sub.add_parser("prepilot-checklist")
    prepilot_parser.add_argument("--evidence-graph", type=Path)
    prepilot_parser.add_argument("--readiness-ledger", type=Path)
    prepilot_parser.add_argument("--hermes-evidence", type=Path)
    prepilot_parser.add_argument("--out", type=Path, default=DEFAULT_PREPILOT_CHECKLIST_OUT)
    prepilot_parser.set_defaults(func=command_prepilot_checklist)

    truth_parser = sub.add_parser("truth")
    truth_parser.add_argument("--target", required=True)
    truth_parser.add_argument("--card", type=Path, required=True)
    truth_parser.add_argument("--issue")
    truth_parser.add_argument("--pr")
    truth_parser.add_argument("--worker-results-dir", type=Path)
    truth_parser.add_argument("--hermes-evidence", type=Path)
    truth_parser.add_argument("--out", type=Path, default=DEFAULT_TRUTH_OUT)
    truth_parser.add_argument("--md-out", type=Path)
    truth_parser.set_defaults(func=command_truth)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return int(args.func(args))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(redact_private_text(str(exc)), file=sys.stderr)
        return 1


def main_with_args_for_test(argv: list[str]) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
