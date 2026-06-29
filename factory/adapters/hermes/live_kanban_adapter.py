#!/usr/bin/env python3
"""Materialize Overkill Factory worker gates in a real Hermes Kanban board."""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import os
import re
import sqlite3
import subprocess  # nosec B404
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from transition_hook import ACTION_BLOCK_TRANSITION, build_hook_result, write_json


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = ROOT / "scripts"
FACTORYCTL_PATH = SCRIPTS_DIR / "factoryctl.py"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from public_refs import (  # noqa: E402
    PRIVATE_KANBAN_TASK_MARKER_RE,
    PUBLIC_SAFE_KANBAN_REF,
    sanitize_public_refs,
)

TASK_ID_RE = PRIVATE_KANBAN_TASK_MARKER_RE
LIVE_ADAPTER_SCHEMA = "https://overkill-factory.dev/schemas/hermes-live-adapter-result.schema.json"
ROUTE_READINESS_SCHEMA = "https://overkill-factory.dev/schemas/hermes-worker-route-readiness.schema.json"
Runner = Callable[[list[str]], subprocess.CompletedProcess[str]]
HERMES_TYPED_BLOCK_KINDS = {"dependency", "needs_input", "capability", "transient"}
DEFAULT_RUNTIME_GATE_BLOCK_KIND = "transient"
RECOVERY_ATTEMPT_MARKER = "factory_recovery_attempt"
ACTIVE_OR_TERMINAL_STATUSES = {"ready", "running", "done", "complete", "completed"}
READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES = {"done", "complete", "completed"}
READY_WORK_UNIT_RELEASE_QUERY_STATUSES = ["blocked", "ready", "running", "done"]
HISTORY_SOURCE_KEYS = ("events", "history", "timeline", "comments", "runs")
CONTRACT_DIGEST_ALGORITHM = "sha256"
IDEMPOTENCY_DIGEST_LENGTH = 16
VOLATILE_CONTRACT_KEYS = {
    "checked_at",
    "created_at",
    "generated_at",
    "last_checked_at",
    "timestamp",
    "updated_at",
}
CANONICALIZATION_VERSION = "v1"
IDEMPOTENCY_LINEAGE_POLICY = "base_identity_is_logical_lineage_contract_key_is_runtime_identity"
READY_WORK_UNIT_DIRECT_BODY_LIMIT = 12000
READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE = "hermes_comment_chunks.v1"
READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR = "overkill-factory-context"
READY_WORK_UNIT_CONTEXT_CHUNK_SIZE = 5000
READY_WORK_UNIT_SUPERSESSION_MARKER = "ready_work_unit_superseded"
READY_WORK_UNIT_RECOVERY_AUTHOR = "overkill-factory-recovery"
READY_WORK_UNIT_RECONCILIATION_AUTHOR = "overkill-factory-reconciliation"
NO_IDLE_AUTHOR = "overkill-factory-no-idle"
NO_IDLE_REMEDIATION_MARKER = "factory_no_idle_remediation"
NO_IDLE_REVIEW_REPAIR_MARKER = "factory_no_idle_review_repair"
NO_IDLE_POST_REVIEW_GATE_MARKER = "factory_no_idle_post_review_gate_package"
NO_IDLE_RUNNING_RESULT_CLOSEOUT_MARKER = "factory_no_idle_running_result_closeout"
NO_IDLE_CANONICAL_FRONTIER_RESUME_MARKER = "factory_no_idle_canonical_frontier_resume"
NO_IDLE_RUNNING_RESULT_CLOSEOUT_TIMEOUT_SECONDS = 5 * 60
FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID = "overkill-vfinal"
FACTORY_KANBAN_DEFAULT_STEP_KEY = "F1-intake"
FACTORY_RUN_GRAPH_RECORD_TYPE = "factory_run_graph"
FACTORY_RUN_GRAPH_NODE_PACKET_TYPE = "factory_run_graph_node"
FACTORY_RUN_GRAPH_RUNTIME_SHAPE = "hermes_kanban_backbone_with_bounded_expanders"
FACTORY_RUNTIME_MANTRA = (
    "less mirabolante, more Kanban-native, more Hermes-native, "
    "more deterministic and easier to trust"
)
FACTORY_RUN_GRAPH_NO_IDLE_ROLE = "integrity_auditor_not_route_authority"
FACTORY_WORKFLOW_CATALOG_PATH = ROOT / "docs" / "factory-workflow.catalog.json"
FACTORY_RUN_GRAPH_DEFAULT_ASSIGNEE = "factory-orchestrator"
DEFAULT_OPERATOR_LANGUAGE = "pt-BR"
V3_PRODUCTION_ACTIVATION_VERSION = "v3.0.0-master-plan-100"
V3_MASTER_PLAN_COMPLETION_REF = ROOT / "templates" / "factory-master-plan-completion.json"
V3_FACTORY_PERFECT_RUN_SCRIPT = ROOT / "scripts" / "factory_perfect_run.py"


def _load_json_if_present(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text())


def v3_production_activation_guard(
    root: Path = ROOT,
    *,
    worker_profiles: dict[str, Any] | None = None,
    hermes_bindings: dict[str, Any] | None = None,
    worker_registry: dict[str, Any] | None = None,
    runtime_truth: dict[str, Any] | None = None,
    canonical_frontier: dict[str, Any] | None = None,
    freshness_policy: dict[str, Any] | None = None,
    release_readiness: dict[str, Any] | None = None,
    human_gate_package: dict[str, Any] | None = None,
    receipt_five: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return PASS only when the live adapter can rely on V3 activation material.

    The adapter must not silently run a stale factory. It must check the same
    runtime contracts the factory claims: Hermes/Kanban remains the runtime,
    no-idle is recovery only, human gates are artifact-first, Receipt Five uses
    durable readback and manager/agent bindings are fresh.
    """
    root = Path(root)
    profiles = worker_profiles or _load_json_if_present(root / "agents" / "worker-profiles.public.json")
    bindings = hermes_bindings or _load_json_if_present(root / "agents" / "hermes-profile-bindings.public.json")
    registry = worker_registry or _load_json_if_present(root / "agents" / "worker-registry.public.json")
    runtime = runtime_truth or _load_json_if_present(root / "templates" / "factory-runtime-truth-spine.json")
    frontier = canonical_frontier or _load_json_if_present(root / "templates" / "factory-canonical-frontier-policy.json")
    freshness = freshness_policy or _load_json_if_present(root / "templates" / "factory-manager-agent-freshness-policy.json")
    readiness = release_readiness or _load_json_if_present(root / "templates" / "factory-v3-release-readiness.json")
    gate_package = human_gate_package or _load_json_if_present(root / "templates" / "human-gate-decision-package.json")
    receipt = receipt_five or _load_json_if_present(root / "templates" / "receipt-five.json")

    blockers: list[str] = []
    checks = {
        "master_plan_completion": (root / "templates" / "factory-master-plan-completion.json").exists(),
        "factory_perfect_run_script": (root / "scripts" / "factory_perfect_run.py").exists(),
        "agent_activation": True,
        "runtime_truth_spine": True,
        "canonical_frontier": True,
        "manager_agent_freshness_policy": True,
        "human_gate_artifact_first": True,
        "receipt_five_readback": True,
    }

    def fail(check: str, message: str) -> None:
        checks[check] = False
        blockers.append(message)

    if not checks["master_plan_completion"]:
        blockers.append("missing master plan completion record")
    if not checks["factory_perfect_run_script"]:
        blockers.append("missing Factory Perfect Run script")

    authority = runtime.get("runtime_authority") or {}
    runtime_acceptance = runtime.get("acceptance") or {}
    if not (
        authority.get("hermes_kanban_owns_runtime") is True
        and authority.get("factory_owns_scheduler") is False
        and authority.get("factory_owns_queue") is False
        and authority.get("factory_owns_dispatch") is False
        and authority.get("factory_owns_task_lifecycle") is False
        and runtime_acceptance.get("no_mini_hermes") is True
        and runtime_acceptance.get("dependency_edges_required") is True
        and runtime_acceptance.get("hermes_state_readback_required") is True
    ):
        fail("runtime_truth_spine", "runtime truth spine does not enforce Hermes/Kanban runtime authority")

    frontier_authority = frontier.get("authority_model") or {}
    frontier_repair = frontier.get("recoverable_gap_policy") or {}
    frontier_acceptance = frontier.get("acceptance") or {}
    if not (
        frontier_authority.get("hermes_kanban_state_required") is True
        and frontier_authority.get("no_idle_is_scheduler") is False
        and frontier_repair.get("repair_before_needs_input") is True
        and frontier_acceptance.get("safe_next_action_required") is True
        and frontier_acceptance.get("repair_before_human") is True
        and frontier_acceptance.get("no_scheduler_overlap") is True
        and frontier_acceptance.get("typed_stop_required") is True
    ):
        fail("canonical_frontier", "canonical frontier does not keep no-idle as repair/recovery only")

    freshness_gate = freshness.get("freshness_gate") or {}
    freshness_manager = freshness.get("manager_contract") or {}
    freshness_bridge = freshness.get("operator_bridge_policy") or {}
    freshness_acceptance = freshness.get("acceptance") or {}
    if not (
        freshness_gate.get("required_for_every_factory_change") is True
        and freshness_manager.get("manager_may_replace_factory_code") is False
        and freshness_manager.get("must_call_current_factory_contracts") is True
        and freshness_bridge.get("direct_worker_operator_contact_allowed") is False
        and freshness_acceptance.get("manager_current") is True
        and freshness_acceptance.get("agents_current") is True
        and freshness_acceptance.get("manager_uses_factory_code") is True
        and freshness_acceptance.get("manager_only_bridge") is True
    ):
        fail("manager_agent_freshness_policy", "manager/agent freshness policy is missing or stale")

    human_gate = readiness.get("human_gate_package") or {}
    gate_required_fields = set(human_gate.get("required_fields") or [])
    package_required_fields = {
        "executive_summary",
        "decision_needed",
        "options_and_consequences",
        "evidence_refs",
        "next_safe_action",
    }
    if not (
        human_gate.get("artifact_first") is True
        and human_gate.get("pdf_or_plain_text_fallback_required") is True
        and human_gate.get("delivery_receipt_required") is True
        and human_gate.get("raw_json_primary_surface_allowed") is False
        and human_gate.get("fake_human_gate_allowed") is False
        and package_required_fields.issubset(gate_required_fields)
        and gate_package.get("record_type") == "human_gate_decision_package"
    ):
        fail("human_gate_artifact_first", "human gate is not artifact-first with operator-readable fallback")

    receipt_policy = readiness.get("receipt_five_policy") or {}
    receipt_body = receipt.get("receipt_five") or {}
    if not (
        receipt_policy.get("readback_required") is True
        and receipt_policy.get("contract_pass_means_done") is False
        and receipt_policy.get("scaffold_or_template_counts_as_evidence") is False
        and receipt_policy.get("stale_review_counts_as_current_authority") is False
        and receipt_body.get("verification_result") == "PASS"
        and bool(receipt_body.get("artifact_readback"))
        and bool(receipt_body.get("runtime_proof"))
        and bool(receipt_body.get("release_proof"))
        and "template-only" in set(receipt_body.get("not_valid_evidence") or [])
    ):
        fail("receipt_five_readback", "Receipt Five readback/anti-overclaim policy is not enforced")

    if profiles.get("production_activation_version") != V3_PRODUCTION_ACTIVATION_VERSION:
        checks["agent_activation"] = False
        blockers.append("worker profiles activation version missing or stale")
    if bindings.get("production_activation_version") != V3_PRODUCTION_ACTIVATION_VERSION:
        checks["agent_activation"] = False
        blockers.append("Hermes bindings activation version missing or stale")
    if registry.get("production_activation_version") != V3_PRODUCTION_ACTIVATION_VERSION:
        checks["agent_activation"] = False
        blockers.append("worker registry activation version missing or stale")
    for worker_id, profile in (profiles.get("profiles") or {}).items():
        activation = profile.get("v3_master_plan_activation") or {}
        if activation.get("manager_only_operator_contact") is not True:
            checks["agent_activation"] = False
            blockers.append(f"{worker_id} does not enforce manager-only operator contact")
        if activation.get("uses_factory_code_not_prompt_runtime") is not True:
            checks["agent_activation"] = False
            blockers.append(f"{worker_id} does not enforce factory-code runtime use")

    result = "PASS" if not blockers else "BLOCKED"
    return {
        "record_type": "v3_production_activation_guard",
        "result": result,
        "runtime_authority": "hermes_kanban",
        "checks": checks,
        "blockers": blockers,
    }

PHASE_TITLES_BY_LANGUAGE = {
    "pt-BR": {
        "F0": "Pre-inicio / envelope de fontes selado",
        "F1": "Entrada",
        "F2": "Registro de fontes",
        "F3": "Resolucao de fontes",
        "F4": "Outcome do produto e descoberta",
        "F5": "SOT do produto",
        "F6": "Roteador de metodo agentic",
        "F7": "Contrato de metodo",
        "F8": "Selecao de packs e experiencia do produto",
        "F9": "Riscos e limites de autoridade",
        "F10": "Arquitetura de seguranca",
        "F11": "Planos executaveis",
        "F12": "Prontidao de autonomia",
        "F13": "Gate de prontidao",
        "F15": "Execucao em runtime",
        "F16": "Resultados dos workers",
        "F17": "Verificacao",
        "F18": "Revisao independente",
        "F20": "Resumo de fechamento",
        "F21": "Receipt Five",
        "F22": "Auditoria de conclusao",
        "F23": "Operacoes de producao",
        "F24": "Release ou bloqueio",
        "F25": "Suporte de monitoramento",
        "F26": "Learnback",
        "F27": "Auditoria de maturidade da fabrica",
    }
}


def explicit_operator_language(value: Any) -> str:
    return str(value or "").strip()


def operator_language_policy(primary_language: str) -> dict[str, Any]:
    return {
        "primary_language": primary_language,
        "user_facing_surfaces_follow_primary_language": True,
        "kanban_cards_follow_primary_language": True,
        "decision_packages_follow_primary_language": True,
        "internal_factory_surfaces_may_use_english": True,
    }


def operator_language_from_start(
    start_request: dict[str, Any],
    source_envelope: dict[str, Any] | None,
) -> str:
    for source in (start_request, source_envelope or {}):
        policy = source.get("operator_language_policy") if isinstance(source.get("operator_language_policy"), dict) else {}
        language = explicit_operator_language(policy.get("primary_language") or source.get("primary_language"))
        if language:
            return language
    return DEFAULT_OPERATOR_LANGUAGE


def localized_phase_name(phase_id: str, fallback: str, language: str) -> str:
    return PHASE_TITLES_BY_LANGUAGE.get(language, {}).get(phase_id, fallback)


def localized_phase_title(phase_id: str, fallback: str, language: str) -> str:
    return f"{phase_id} - {localized_phase_name(phase_id, fallback, language)}"


def factory_start_title(run_id: str, language: str) -> str:
    if language == "pt-BR":
        return f"F1 - Inicio da fabrica: {run_id}"
    return f"Factory start: {run_id}"


def slugify_phase_node(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").strip().lower()).strip("-")
    return slug or "phase"


def load_factory_run_graph_backbone_from_catalog(
    path: Path = FACTORY_WORKFLOW_CATALOG_PATH,
    *,
    language: str = "en-US",
) -> tuple[dict[str, Any], ...]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    phases = catalog.get("phases")
    if not isinstance(phases, list) or not phases:
        raise RuntimeError(f"Factory workflow catalog has no phases: {path}")

    nodes: list[dict[str, Any]] = []
    previous_node_id = "F1-intake"
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        phase_id = str(phase.get("phase_id") or "").strip()
        if phase_id in {"F0", "F1"}:
            continue
        phase_name = str(phase.get("phase_name") or phase_id).strip()
        display_phase_name = localized_phase_name(phase_id, phase_name, language)
        node_id = f"{phase_id}-{slugify_phase_node(phase_name)}"
        required_artifacts = phase.get("required_artifacts") if isinstance(phase.get("required_artifacts"), list) else []
        required_workers = phase.get("required_workers") if isinstance(phase.get("required_workers"), list) else []
        required_output = str(required_artifacts[0] if required_artifacts else f"{phase_id.lower()}_phase_output").strip()
        assignee = str(required_workers[0] if required_workers else FACTORY_RUN_GRAPH_DEFAULT_ASSIGNEE).strip()
        node = {
            "node_id": node_id,
            "phase_id": phase_id,
            "step_key": node_id,
            "title": f"{phase_id} - {display_phase_name}",
            "assignee": assignee or FACTORY_RUN_GRAPH_DEFAULT_ASSIGNEE,
            "required_output": required_output,
            "activation_rule": f"{previous_node_id} done",
        }
        if phase_id == "F15":
            node["node_kind"] = "bounded_expander"
        nodes.append(node)
        previous_node_id = node_id
    return tuple(nodes)


FACTORY_RUN_GRAPH_BACKBONE = load_factory_run_graph_backbone_from_catalog()
COMPLETION_ARTIFACT_PROJECTION_MARKER = "completion_artifact_projection"
KANBAN_ARTIFACT_REF_PREFIXES = ("kanban-artifact:", "external:kanban-artifact:", "kanban-attachment:")
PRIVATE_HERMES_RUNTIME_TOKEN = "/srv/" + "hermes"
PRIVATE_WINDOWS_USER_TOKEN = "C:" + "\\" + "Users"
PRIVATE_WINDOWS_ESCAPED_USER_TOKEN = "C:" + "\\\\" + "Users"
PRIVATE_SYNC_ROOT_TOKEN = "One" + "Drive"
COMPLETION_ARTIFACT_PRIVATE_TEXT_RE = re.compile(
    "("
    + "|".join(
        re.escape(token)
        for token in (
            PRIVATE_WINDOWS_USER_TOKEN,
            PRIVATE_WINDOWS_ESCAPED_USER_TOKEN,
            PRIVATE_HERMES_RUNTIME_TOKEN,
            PRIVATE_SYNC_ROOT_TOKEN,
        )
    )
    + r"|discord(app)?\.com|webhook|guild[_-]?id|channel[_-]?id|message[_-]?id)",
    re.IGNORECASE,
)
COMPLETION_ARTIFACT_SECRET_RE = re.compile(
    r"(-----BEGIN (?:RSA |DSA |EC |OPENSSH |PGP )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9_]{30,}\b|\bsk-[A-Za-z0-9_-]{20,}\b|\bxox[baprs]-[A-Za-z0-9-]{20,}\b|\bAKIA[0-9A-Z]{16}\b|\b(?:api[_-]?key|secret|token|password|passwd)\b\s*(?::(?!:)|=)\s*['\"]?[^'\"\s]{16,})",
    re.IGNORECASE,
)
READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS = [
    "runtime_gate=blocked_event_verified_for_each_task",
    "release_scope=ready_work_units_only",
    "dispatch_separate=true",
]
BRIDGE_START_BLOCK_REASON = (
    "factory_bridge_start_request materialized by factory start path; "
    "verified blocked event before first factory dispatch."
)
BRIDGE_START_RELEASE_REASON = (
    "factory_bridge_start_release source_resolution product_sot_candidate: "
    "start request validated; release factory-orchestrator for source resolution "
    "and Product SOT candidate. Normal factory start is not a human gate."
)
BRIDGE_START_RELEASE_READBACK_MARKERS = [
    "factory_bridge_start_release",
    "source_resolution",
    "product_sot_candidate",
]
READY_WORK_UNIT_REPAIR_COMPLETED_MARKERS = ["ready_work_unit_repair_completed", "repair completed"]
READY_WORK_UNIT_REPAIR_COMPLETED_INFERRED_MARKERS = [
    "review-required",
    "review required",
    "review_required",
    "reviewer required",
]
READY_WORK_UNIT_REPAIR_REVIEW_PASSED_MARKERS = ["ready_work_unit_repair_review_passed"]
READY_WORK_UNIT_RETRY_AUTHORIZED_MARKERS = ["ready_work_unit_retry_authorized"]
READY_WORK_UNIT_DONE_AUTHORIZED_MARKERS = ["ready_work_unit_done_authorized"]
READY_WORK_UNIT_DONE_DEFINITION_SATISFIED_MARKERS = ["ready_work_unit_done_definition_satisfied"]
READY_WORK_UNIT_HUMAN_GATE_MARKERS = ["human_gate_required", "human-gate-required"]
READY_WORK_UNIT_RECONCILIATION_RETRY_READBACK_MARKERS = [
    "ready_work_unit_retry_authorized",
    "post_release_ready_work_unit",
]
READY_WORK_UNIT_RECONCILIATION_DONE_READBACK_MARKERS = [
    "ready_work_unit_done_authorized",
    "post_release_ready_work_unit",
]
READY_WORK_UNIT_POST_REPAIR_REVIEW_REQUIRED_MARKER = "ready_work_unit_post_repair_review_required"
READY_WORK_UNIT_POST_REPAIR_REVIEW_CREATED_MARKER = "ready_work_unit_post_repair_review_task_created"
READY_WORK_UNIT_POST_REPAIR_REVIEW_RESULT_MARKER = "ready_work_unit_post_repair_review_result"
READY_WORK_UNIT_POST_REPAIR_AUTHORITY_REQUIRED_MARKER = "ready_work_unit_post_repair_authority_required"
READY_WORK_UNIT_POST_REPAIR_AUTHORITY_CREATED_MARKER = "ready_work_unit_post_repair_authority_task_created"
READY_WORK_UNIT_POST_REPAIR_AUTHORITY_RESULT_MARKER = "ready_work_unit_post_repair_authority_result"
READY_WORK_UNIT_SUPERSEDED_PARENT_UNLINKED_MARKER = "ready_work_unit_superseded_parent_unlinked"
READY_WORK_UNIT_REVIEW_CLOSEOUT_MARKER = "ready_work_unit_review_closeout"
READY_WORK_UNIT_REVIEW_PASSED_MARKER = "ready_work_unit_review_passed"
READY_WORK_UNIT_REVIEW_CLOSEOUT_READBACK_MARKERS = [
    READY_WORK_UNIT_REVIEW_CLOSEOUT_MARKER,
    READY_WORK_UNIT_REVIEW_PASSED_MARKER,
]
PRODUCT_CREATION_CLOSEOUT_MARKER = "product_creation_run_closeout"
PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER = "product_creation_closeout_next_route"
PRODUCT_CREATION_CLOSEOUT_READBACK_MARKERS = [
    PRODUCT_CREATION_CLOSEOUT_MARKER,
    PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
]
RELEASE_READINESS_REVIEW_CLOSEOUT_MARKER = "release_readiness_review_closeout"
RELEASE_READINESS_REVIEW_PASSED_MARKER = "release_readiness_review_passed"
RELEASE_READINESS_REVIEW_BLOCKED_MARKER = "release_readiness_review_blocked"
RELEASE_READINESS_REVIEW_PARENT_EDGE_REPAIRED_MARKER = "release_readiness_review_parent_edge_repaired"
RELEASE_READINESS_REVIEW_CLOSEOUT_READBACK_MARKERS = [
    RELEASE_READINESS_REVIEW_CLOSEOUT_MARKER,
    RELEASE_READINESS_REVIEW_PASSED_MARKER,
]
BRIDGE_START_RECORD_TYPE = "factory_bridge_start_request"
BRIDGE_START_ROOT_TASK_TYPE = "factory_bridge_start_root"
BRIDGE_START_DEFAULT_ASSIGNEE = "factory-orchestrator"
BRIDGE_START_FORBIDDEN_BOARD_SLUGS = {"default"}
ANSI_ESCAPE_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
WORKER_MATERIALIZATION_CONTRACT_FIELDS = (
    "task_type",
    "worker_id",
    "gate_timing_class",
    "queue_class",
    "runtime_authority",
    "local_state_authority",
    "required_before",
    "expected_receipt_field",
    "status",
    "dependency_authorization_state",
    "review_task_authorizations",
    "recovery_route_refs",
    "packet",
)


def default_runner(argv: list[str]) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("HOME", str(Path.home()))
    return subprocess.run(  # nosec B603
        argv,
        text=True,
        capture_output=True,
        env=env,
        encoding="utf-8",
        errors="replace",
    )


def safe_command_for_error(argv: list[str]) -> str:
    redacted: list[str] = []
    redact_next = False
    for arg in argv:
        if redact_next:
            digest = hashlib.sha256(str(arg).encode("utf-8", errors="replace")).hexdigest()[:12]
            redacted.append(f"<redacted len={len(str(arg))} sha256={digest}>")
            redact_next = False
            continue
        redacted.append(str(arg))
        if arg == "--body":
            redact_next = True
            continue
        if len(str(arg)) > 500:
            digest = hashlib.sha256(str(arg).encode("utf-8", errors="replace")).hexdigest()[:12]
            redacted[-1] = f"<redacted-long-arg len={len(str(arg))} sha256={digest}>"
    return " ".join(redacted)


def run_checked(argv: list[str], runner: Runner = default_runner) -> subprocess.CompletedProcess[str]:
    completed = runner(argv)
    if completed.returncode != 0:
        raise RuntimeError(
            "command failed: "
            + safe_command_for_error(argv)
            + "\nstdout:\n"
            + (completed.stdout or "")
            + "\nstderr:\n"
            + (completed.stderr or "")
        )
    return completed


def parse_json_output(output: str, *, command: str) -> Any:
    try:
        return json.loads(output or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{command} did not return JSON") from exc


def hermes_home_path() -> Path:
    raw = os.environ.get("HERMES_HOME") or os.environ.get("HOME")
    if raw:
        return Path(raw).expanduser()
    return Path.home()


def local_kanban_db_path(board: str) -> Path | None:
    slug = str(board or "").strip()
    if not slug or not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", slug):
        return None
    home = hermes_home_path()
    if slug == "default":
        return home / "kanban.db"
    return home / "kanban" / "boards" / slug / "kanban.db"


def apply_native_workflow_state(
    *,
    board: str,
    task_id: str,
    workflow_template_id: str | None,
    current_step_key: str | None,
) -> bool:
    if not workflow_template_id or not current_step_key:
        return False
    db_path = local_kanban_db_path(board)
    if db_path is None or not db_path.exists():
        return False
    conn = sqlite3.connect(str(db_path))
    try:
        cols = {
            str(row[1])
            for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
            if len(row) > 1
        }
        if {"workflow_template_id", "current_step_key"} - cols:
            return False
        conn.execute(
            "UPDATE tasks SET workflow_template_id = ?, current_step_key = ? WHERE id = ?",
            (workflow_template_id, current_step_key, task_id),
        )
        conn.commit()
        return conn.total_changes > 0
    finally:
        conn.close()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_factoryctl() -> Any:
    spec = importlib.util.spec_from_file_location("overkill_factoryctl_live_adapter", FACTORYCTL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factoryctl from {FACTORYCTL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["overkill_factoryctl_live_adapter"] = module
    spec.loader.exec_module(module)
    return module


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


def compact_json_argument(value: Any) -> str:
    return json.dumps(value, ensure_ascii=True, separators=(",", ":"))


def idempotency_digest_fragment(digest: str) -> str:
    return digest[:IDEMPOTENCY_DIGEST_LENGTH]


def main_base_idempotency_key(card_id: str) -> str:
    return f"overkill:{card_id}:main"


def worker_base_idempotency_key(card_id: str, worker_id: str) -> str:
    return f"overkill:{card_id}:{worker_id}"


def main_task_idempotency_key(card_id: str, card_body: str) -> str:
    return f"{main_base_idempotency_key(card_id)}:{idempotency_digest_fragment(contract_digest(card_body))}"


def worker_materialization_contract(task: dict[str, Any]) -> dict[str, Any]:
    return {field: task[field] for field in WORKER_MATERIALIZATION_CONTRACT_FIELDS if field in task}


def worker_task_idempotency_key(card_id: str, worker_id: str, task_contract: dict[str, Any]) -> str:
    return f"{worker_base_idempotency_key(card_id, worker_id)}:{idempotency_digest_fragment(contract_digest(task_contract))}"


def recovery_route_digest(route: dict[str, Any]) -> str:
    return f"{CONTRACT_DIGEST_ALGORITHM}:{contract_digest(route)}"


def parse_task_id(output: str) -> str:
    text = (output or "").strip()
    if text:
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            for key in ("id", "task_id"):
                value = data.get(key)
                if isinstance(value, str) and value:
                    return value
        match = TASK_ID_RE.search(text)
        if match:
            return match.group(0)
    raise RuntimeError(f"could not parse Hermes task id from output: {text!r}")


def find_task_id_by_idempotency_key(
    *,
    hermes_bin: str,
    board: str,
    idempotency_key: str,
    runner: Runner = default_runner,
) -> str | None:
    key = str(idempotency_key or "").strip()
    if not key:
        return None
    db_path = local_kanban_db_path(board)
    if db_path is not None and db_path.exists():
        conn = sqlite3.connect(str(db_path))
        try:
            cols = {
                str(row[1])
                for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
                if len(row) > 1
            }
            if "idempotency_key" in cols:
                row = conn.execute(
                    "SELECT id FROM tasks WHERE idempotency_key = ? ORDER BY created_at DESC LIMIT 1",
                    (key,),
                ).fetchone()
                if row and row[0]:
                    return str(row[0])
        finally:
            conn.close()
    for status in ("ready", "running", "todo", "blocked", "triage", "done", "archived"):
        try:
            rows = list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner)
        except RuntimeError:
            continue
        for task in rows:
            if str(task.get("idempotency_key") or "").strip() == key:
                task_id = str(task.get("id") or task.get("task_id") or "").strip()
                if task_id:
                    return task_id
    return None


def parse_task_id_or_find_idempotent(
    *,
    output: str,
    hermes_bin: str,
    board: str,
    idempotency_key: str,
    runner: Runner = default_runner,
) -> str:
    try:
        return parse_task_id(output)
    except RuntimeError:
        task_id = find_task_id_by_idempotency_key(
            hermes_bin=hermes_bin,
            board=board,
            idempotency_key=idempotency_key,
            runner=runner,
        )
        if task_id:
            return task_id
        raise


def hermes_kanban(hermes_bin: str, board: str, *args: str) -> list[str]:
    return [hermes_bin, "kanban", "--board", board, *args]


def public_safe_workspace_ref(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    normalized = text.replace("\\", "/")
    if normalized.lower().startswith("dir:"):
        normalized = normalized[4:]
    if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("/"):
        return "redacted:absolute-hermes-workspace"
    return text


def hermes_workspace_arg(value: str) -> str:
    text = str(value or "").strip()
    if not text:
        return "scratch"
    normalized = text.replace("\\", "/")
    if normalized in {"scratch", "worktree"} or normalized.startswith(("dir:", "worktree:")):
        return text
    if re.match(r"^[A-Za-z]:/", normalized) or normalized.startswith("/"):
        return "dir:" + text
    return text


def normalize_task_record(record: dict[str, Any]) -> dict[str, Any]:
    task_id = str(record.get("task_id") or record.get("id") or "")
    normalized: dict[str, Any] = {"task_id": task_id}
    assignee = record.get("assignee") or record.get("profile")
    if assignee:
        normalized["assignee"] = str(assignee)
    workspace = record.get("workspace") or record.get("workspace_path")
    if workspace:
        normalized["workspace"] = public_safe_workspace_ref(workspace)
    for source_key, target_key in (
        ("current_run_id", "run_id"),
        ("run_id", "run_id"),
        ("worker_pid", "worker_pid"),
        ("pid", "worker_pid"),
    ):
        value = record.get(source_key)
        if value is not None and target_key not in normalized:
            normalized[target_key] = value
    return normalized


def list_tasks_by_status(
    *,
    hermes_bin: str,
    board: str,
    status: str,
    runner: Runner = default_runner,
) -> list[dict[str, Any]]:
    completed = run_checked(hermes_kanban(hermes_bin, board, "list", "--status", status, "--json"), runner)
    payload = parse_json_output(completed.stdout, command=f"hermes kanban list --status {status} --json")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        for key in ("tasks", "items", status):
            items = payload.get(key)
            if isinstance(items, list):
                return [item for item in items if isinstance(item, dict)]
    return []


def show_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    runner: Runner = default_runner,
) -> dict[str, Any]:
    completed = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    payload = parse_json_output(completed.stdout, command="hermes kanban show --json")
    return payload if isinstance(payload, dict) else {}


def task_run_records(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    runner: Runner = default_runner,
) -> list[dict[str, Any]]:
    completed = run_checked(hermes_kanban(hermes_bin, board, "runs", task_id, "--json"), runner)
    payload = parse_json_output(completed.stdout, command="hermes kanban runs --json")
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        runs = payload.get("runs")
        if isinstance(runs, list):
            return [item for item in runs if isinstance(item, dict)]
    return []


def task_log_text(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    runner: Runner = default_runner,
    tail_bytes: int = 500_000,
) -> str:
    completed = run_checked(
        hermes_kanban(hermes_bin, board, "log", task_id, "--tail", str(tail_bytes)),
        runner,
    )
    return completed.stdout or ""


def task_status(payload: dict[str, Any]) -> str:
    return str(payload.get("status") or "").strip().lower()


def enrich_dispatch_task(
    *,
    hermes_bin: str,
    board: str,
    record: dict[str, Any],
    after_running_by_id: dict[str, dict[str, Any]],
    runner: Runner = default_runner,
) -> dict[str, Any]:
    task_id = str(record.get("task_id") or record.get("id") or "")
    merged: dict[str, Any] = {}
    if task_id:
        merged.update(after_running_by_id.get(task_id) or {})
    merged.update(record)
    normalized = normalize_task_record(merged)
    if task_id and ("run_id" not in normalized or "worker_pid" not in normalized):
        shown = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
        shown_normalized = normalize_task_record(shown)
        for key in ("run_id", "worker_pid", "assignee", "workspace"):
            if key not in normalized and key in shown_normalized:
                normalized[key] = shown_normalized[key]
    return normalized


def normalize_native_spawned(payload: dict[str, Any]) -> list[dict[str, Any]]:
    records = payload.get("spawned")
    if not isinstance(records, list):
        return []
    normalized: list[dict[str, Any]] = []
    for item in records:
        if isinstance(item, dict):
            record = normalize_task_record(item)
            if record.get("task_id"):
                normalized.append(record)
    return normalized


def public_safe_slug(value: Any, *, fallback: str = "item") -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value or "").strip()).strip(".-")
    return (slug or fallback)[:120]


def task_record_id(record: dict[str, Any]) -> str:
    return str(record.get("task_id") or record.get("id") or "").strip()


def evidence_like_key(key: Any) -> bool:
    normalized = str(key or "").strip().lower()
    return normalized in {
        "evidence_ref",
        "evidence_refs",
        "evidence_path",
        "evidence_paths",
        "artifact",
        "artifacts",
        "artifact_ref",
        "artifact_refs",
        "artifact_path",
        "artifact_paths",
        "result_artifact",
        "result_artifacts",
    }


def collect_evidence_ref_strings(value: Any, *, active: bool = False) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            refs.extend(collect_evidence_ref_strings(item, active=active or evidence_like_key(key)))
        return refs
    if isinstance(value, list):
        for item in value:
            refs.extend(collect_evidence_ref_strings(item, active=active))
        return refs
    if active and isinstance(value, str) and value.strip():
        refs.append(value.strip())
    return refs


def is_kanban_artifact_ref(ref: str) -> bool:
    return ref.strip().startswith(KANBAN_ARTIFACT_REF_PREFIXES)


def is_local_or_scratch_artifact_ref(ref: str) -> bool:
    text = ref.strip()
    normalized = text.replace("\\", "/")
    if normalized.startswith(("file://", ".tmp/", "tmp/", "scratch/", "workspace:")):
        return True
    if re.match(r"^[A-Za-z]:/", normalized):
        return True
    return Path(text).is_absolute()


def collect_artifact_readback_records(value: Any) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    if isinstance(value, dict):
        proof = value.get("artifact_readback")
        if isinstance(proof, dict) and str(proof.get("status") or "").strip().upper() == "PASS":
            refs = proof.get("refs")
            if isinstance(refs, list):
                for item in refs:
                    if not isinstance(item, dict):
                        continue
                    ref = str(item.get("ref") or "").strip()
                    if ref:
                        records[ref] = item
        for item in value.values():
            records.update(collect_artifact_readback_records(item))
    elif isinstance(value, list):
        for item in value:
            records.update(collect_artifact_readback_records(item))
    return records


def artifact_readback_record_errors(ref: str, item: dict[str, Any] | None) -> list[str]:
    at = f"artifact_readback.refs[{ref}]"
    if not isinstance(item, dict):
        return [f"{at} is required"]
    errors: list[str] = []
    if item.get("readable") is not True:
        errors.append(f"{at}.readable must be true")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(item.get("sha256") or "")):
        errors.append(f"{at}.sha256 must be sha256:<64 lowercase hex chars>")
    if ref.startswith("kanban-attachment:"):
        for field in ("attachment_row_seen", "blob_exists", "schema_valid"):
            if item.get(field) is not True:
                errors.append(f"{at}.{field} must be true")
        if not isinstance(item.get("size_bytes"), int) or item.get("size_bytes") <= 0:
            errors.append(f"{at}.size_bytes must be a positive integer")
        if str(item.get("json_parse_status") or "").strip().upper() not in {"PASS", "NOT_JSON"}:
            errors.append(f"{at}.json_parse_status must be PASS or NOT_JSON")
        if str(item.get("public_safety_scan") or "").strip().upper() != "PASS":
            errors.append(f"{at}.public_safety_scan must be PASS")
        if str(item.get("secret_safety_scan") or "").strip().upper() != "PASS":
            errors.append(f"{at}.secret_safety_scan must be PASS")
    return errors


def completion_artifact_readback_blockers(receipt: dict[str, Any]) -> list[str]:
    refs = sorted({ref for ref in collect_evidence_ref_strings(receipt) if is_kanban_artifact_ref(ref)})
    readback = collect_artifact_readback_records(receipt)
    blockers: list[str] = []
    for ref in refs:
        blockers.extend(artifact_readback_record_errors(ref, readback.get(ref)))
    return blockers


def projected_artifact_filename(path: Path, digest: str, used_names: set[str]) -> str:
    base = public_safe_slug(path.name, fallback="artifact")
    candidate = base
    if candidate in used_names:
        stem = public_safe_slug(path.stem, fallback="artifact")
        suffix = path.suffix if re.fullmatch(r"\.[A-Za-z0-9]{1,12}", path.suffix) else ""
        candidate = f"{stem}-{digest[:12]}{suffix}"
    used_names.add(candidate)
    return candidate


def json_parse_status_for_bytes(data: bytes) -> str:
    try:
        json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return "NOT_JSON"
    return "PASS"


def assert_completion_artifact_public_safe(data: bytes, *, source: Path) -> None:
    text = data.decode("utf-8", errors="replace")
    if COMPLETION_ARTIFACT_PRIVATE_TEXT_RE.search(text):
        raise RuntimeError(f"completion artifact contains private runtime residue and cannot be projected: {source.name}")
    if COMPLETION_ARTIFACT_SECRET_RE.search(text):
        raise RuntimeError(f"completion artifact contains secret-like material and cannot be projected: {source.name}")


def project_completion_artifacts(
    *,
    artifact_paths: list[Path],
    attachment_root: Path | None,
    board: str,
    task_id: str,
) -> dict[str, Any] | None:
    if not artifact_paths:
        return None
    if attachment_root is None:
        raise RuntimeError("completion artifact paths require --attachment-root before completing the Hermes task")

    target_dir = (
        attachment_root.resolve()
        / public_safe_slug(board, fallback="board")
        / public_safe_slug(task_id, fallback="task")
        / "artifacts"
    )
    target_dir.mkdir(parents=True, exist_ok=True)
    used_names: set[str] = set()
    projected_refs: list[dict[str, Any]] = []
    rewrite_map: dict[str, str] = {}
    for raw_path in artifact_paths:
        source = raw_path.resolve()
        if not source.is_file():
            raise RuntimeError(f"completion artifact path is not a readable file: {raw_path}")
        data = source.read_bytes()
        assert_completion_artifact_public_safe(data, source=source)
        digest = hashlib.sha256(data).hexdigest()
        name = projected_artifact_filename(source, digest, used_names)
        destination = target_dir / name
        destination.write_bytes(data)
        copied = destination.read_bytes()
        copied_digest = hashlib.sha256(copied).hexdigest()
        if copied_digest != digest:
            raise RuntimeError(f"completion artifact copy hash mismatch for {raw_path}")
        durable_ref = f"kanban-attachment:{task_id}/artifacts/{name}"
        rewrite_map[source.name] = durable_ref
        projected_refs.append(
            {
                "ref": durable_ref,
                "readable": True,
                "attachment_row_seen": True,
                "blob_exists": True,
                "size_bytes": len(copied),
                "sha256": f"sha256:{digest}",
                "json_parse_status": json_parse_status_for_bytes(copied),
                "schema_valid": True,
                "public_safety_scan": "PASS",
                "secret_safety_scan": "PASS",
                "source_ref": public_safe_workspace_ref(str(source)),
                "storage_ref": public_safe_workspace_ref(str(destination)),
            }
        )
    return {
        "marker": COMPLETION_ARTIFACT_PROJECTION_MARKER,
        "status": "PASS",
        "transport": "adapter_durable_copy_before_hermes_complete",
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "artifact_root_ref": public_safe_workspace_ref(str(target_dir)),
        "refs": projected_refs,
        "rewrite_map_by_filename": rewrite_map,
    }


def durable_ref_for_local_artifact(ref: str, rewrite_map: dict[str, str]) -> str | None:
    normalized = ref.strip().replace("\\", "/")
    name = public_safe_slug(Path(normalized).name, fallback="")
    if name and name in rewrite_map:
        return rewrite_map[name]
    return None


def rewrite_local_artifact_refs(value: Any, rewrite_map: dict[str, str], *, active: bool = False) -> Any:
    if isinstance(value, dict):
        rewritten: dict[str, Any] = {}
        for key, item in value.items():
            rewritten[key] = rewrite_local_artifact_refs(item, rewrite_map, active=active or evidence_like_key(key))
        return rewritten
    if isinstance(value, list):
        return [rewrite_local_artifact_refs(item, rewrite_map, active=active) for item in value]
    if active and isinstance(value, str) and is_local_or_scratch_artifact_ref(value):
        durable_ref = durable_ref_for_local_artifact(value, rewrite_map)
        if durable_ref:
            return durable_ref
    return value


def apply_completion_artifact_policy(
    *,
    receipt: dict[str, Any],
    artifact_paths: list[Path],
    attachment_root: Path | None,
    board: str,
    task_id: str,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    local_refs = sorted({ref for ref in collect_evidence_ref_strings(receipt) if is_local_or_scratch_artifact_ref(ref)})
    projection = project_completion_artifacts(
        artifact_paths=artifact_paths,
        attachment_root=attachment_root,
        board=board,
        task_id=task_id,
    )
    if local_refs and not projection:
        raise RuntimeError(
            "completion receipt references local/scratch artifacts without durable projection: "
            + ", ".join(local_refs)
        )

    receipt_payload = copy.deepcopy(receipt)
    if projection:
        rewrite_map = projection.get("rewrite_map_by_filename")
        if isinstance(rewrite_map, dict):
            missing = [ref for ref in local_refs if durable_ref_for_local_artifact(ref, rewrite_map) is None]
            if missing:
                raise RuntimeError(
                    "completion artifact projection cannot rewrite local/scratch refs: " + ", ".join(missing)
                )
            receipt_payload = rewrite_local_artifact_refs(receipt_payload, rewrite_map)
        receipt_payload["_overkill_completion_artifact_projection"] = projection
        existing_readback = receipt_payload.get("artifact_readback")
        existing_refs = (
            existing_readback.get("refs")
            if isinstance(existing_readback, dict) and isinstance(existing_readback.get("refs"), list)
            else []
        )
        receipt_payload["artifact_readback"] = {
            "status": "PASS",
            "checked_from": "adapter_completion_projection",
            "refs": [*existing_refs, *(projection.get("refs") or [])],
        }

    blockers = completion_artifact_readback_blockers(receipt_payload)
    if blockers:
        raise RuntimeError("completion artifact readback blocked live completion: " + "; ".join(blockers))
    return receipt_payload, projection


def task_record_text(record: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in (
        "title",
        "name",
        "summary",
        "latest_summary",
        "assignee",
        "status",
        "reason",
        "blocked_reason",
        "body",
    ):
        value = record.get(key)
        if value is not None:
            parts.append(str(value))
    for item in record.get("comments") or []:
        if isinstance(item, dict):
            parts.append(str(item.get("body") or item.get("summary") or item.get("reason") or ""))
        else:
            parts.append(str(item))
    for item in record.get("events") or []:
        if isinstance(item, dict):
            parts.append(str(item.get("reason") or item.get("payload") or item.get("type") or item.get("kind") or ""))
        else:
            parts.append(str(item))
    return " ".join(parts).lower()


def is_human_gate_blocker(record: dict[str, Any]) -> bool:
    text = task_record_text(record)
    return any(
        marker in text
        for marker in (
            "human_gate",
            "human-gate",
            "human gate",
            "human decision",
            "human approval",
            "approval_required",
            "requires_human",
            "requires human",
            "awaiting human",
            "operator decision",
        )
    )


def human_gate_packet_from_record(record: dict[str, Any]) -> dict[str, Any]:
    body = task_body_json_object(record)
    packet = body.get("human_gate_packet") if isinstance(body.get("human_gate_packet"), dict) else body
    return packet if isinstance(packet, dict) else {}


def human_gate_decision_package_complete(record: dict[str, Any]) -> bool:
    packet = human_gate_packet_from_record(record)
    if not packet:
        return False
    try:
        factoryctl = load_factoryctl()
        return not factoryctl.validate_human_gate_packet(packet, require_decision_package=True)
    except Exception:
        return False


def is_human_gate_decision_ready_blocker(record: dict[str, Any]) -> bool:
    if not is_human_gate_blocker(record):
        return False
    if is_operator_input_blocker(record):
        return False
    if not human_gate_decision_package_complete(record):
        return False
    text = task_record_text(record)
    return any(
        marker in text
        for marker in (
            "awaiting human decision",
            "awaiting human approval",
            "pending explicit human decision",
            "decision-ready",
            "decision ready",
            "operator briefing delivered",
            "approval request delivered",
            "owner review delivered",
            "pdf delivered",
            "package prepared and delivered",
            "decision package prepared and delivered",
            "owner decision package prepared and delivered",
            "product sot owner decision package prepared and delivered",
            "after delivered product sot package",
            "after reading package",
            "ready for owner decision",
            "ready for operator decision",
        )
    )


def is_human_gate_package_blocker(record: dict[str, Any]) -> bool:
    return is_human_gate_blocker(record) and not is_human_gate_decision_ready_blocker(record)


def is_factory_owned_package_blocker(record: dict[str, Any]) -> bool:
    text = task_record_text(record)
    package_markers = (
        "missing operator briefing package",
        "operator briefing package missing",
        "missing operator_briefing_package",
        "operator_briefing_package missing",
        "missing approval_request",
        "approval_request missing",
        "missing approval request",
        "approval request missing",
        "missing evidence_index",
        "evidence_index missing",
        "missing evidence index",
        "evidence index missing",
        "missing owner_review",
        "owner_review missing",
        "missing owner review",
        "owner review missing",
        "missing decision package",
        "decision package missing",
        "incomplete decision package",
        "summary-only",
        "summary only",
        "markdown only",
        "pdf missing",
        "no pdf",
        "no material",
        "owner-readable",
        "owner readable",
        "readable package",
        "readable artifact",
        "package quality",
        "artifact quality failure",
        "material package",
        "gate package",
        "decision assets",
        "attachment missing",
        "missing attachment",
        "artifact readback",
        "missing readback",
        "delivery assets",
    )
    return any(marker in text for marker in package_markers)


def is_factory_owned_repair_task(record: dict[str, Any]) -> bool:
    text = task_record_text(record)
    markers = (
        "factory-owned repair",
        "factory owned repair",
        "factory_deterministic_reconcile",
        "factory_no_idle_remediation",
        "factory_no_idle_review_repair",
        "factory_no_idle_post_review_gate_package",
        "repair human gate decision package",
        "repair package",
        "rebuild the package",
        "owner-facing artifact quality failure",
        "no renewed decision request",
        "readable artifact is ready",
    )
    return any(marker in text for marker in markers)


def task_body_json_object(record: dict[str, Any]) -> dict[str, Any]:
    body = record.get("body")
    if isinstance(body, dict):
        return body
    if isinstance(body, str) and body.strip():
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            return {}
        return data if isinstance(data, dict) else {}
    return {}


def is_review_failed_factory_repair_blocker(record: dict[str, Any]) -> bool:
    if is_human_gate_decision_ready_blocker(record):
        return False
    text = task_record_text(record)
    review_failed = any(
        marker in text
        for marker in (
            "review-failed",
            "review failed",
            "independent review result: fail",
            "independent review result: block",
            "fail / block",
        )
    )
    if not review_failed:
        return False
    return any(
        marker in text
        for marker in (
            "factoryctl validators fail",
            "validator failure",
            "validators fail",
            "handoff sequencing is inconsistent",
            "schema-valid",
            "required fixes",
            "rerun independent review",
            "rerun review",
            "repair before owner",
            "repair before human",
        )
    )


def superseded_review_blocker_refs(done: list[dict[str, Any]]) -> set[str]:
    refs: set[str] = set()
    for item in done:
        if str(item.get("status") or "").strip().lower() not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
            continue
        body = task_body_json_object(item)
        if body.get("marker") != NO_IDLE_REVIEW_REPAIR_MARKER:
            continue
        for ref in body.get("blocked_review_task_refs") or []:
            if isinstance(ref, str) and ref.strip():
                refs.add(ref.strip())
    return refs


def done_review_targets_product_sot_candidate(record: dict[str, Any]) -> bool:
    text = task_record_text(record)
    non_product_sot_review_markers = (
        "not a reviewed product sot candidate",
        "not product sot owner-review material",
        "not product sot owner review material",
        "runtime/code patch only",
        "factory runtime code patch",
        "factory no-idle runtime",
        "no-idle da fábrica",
        "correção no-idle",
        "patch da correção no-idle",
        "revisar o patch da correção no-idle",
        "no-idle runtime classifier patch",
        "no-idle code",
        "classifier patch",
        "live_kanban_adapter.py",
        "classify_no_idle_state",
        "done_review_requires_owner_product_sot_gate",
    )
    if any(marker in text for marker in non_product_sot_review_markers):
        return False
    product_sot_artifact_markers = (
        "repaired product sot candidate",
        "product sot candidate package",
        "product sot candidate",
        "repaired product sot package",
        "product sot package",
        "canonical product sot",
        "owner-facing product sot",
        "owner facing product sot",
        "reviewed product sot",
        "review product sot package",
        "review repaired product sot package",
    )
    return any(marker in text for marker in product_sot_artifact_markers)


def done_product_sot_candidate_requires_owner_review(record: dict[str, Any]) -> bool:
    if str(record.get("status") or "").strip().lower() not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        return False
    texts = [task_record_text(record)]
    for run in record.get("runs") or []:
        if not isinstance(run, dict):
            continue
        metadata = parse_json_object(run.get("metadata"))
        if metadata:
            texts.append(json.dumps(metadata, sort_keys=True, ensure_ascii=False).lower())
        if run.get("summary") is not None:
            texts.append(str(run.get("summary")).lower())
    haystack = " ".join(texts)
    non_product_sot_markers = (
        "not a reviewed product sot candidate",
        "not product sot owner-review material",
        "not product sot owner review material",
        "runtime/code patch only",
        "factory runtime code patch",
        "factory no-idle runtime",
        "no-idle runtime classifier patch",
        "live_kanban_adapter.py",
        "classify_no_idle_state",
        "done_review_requires_owner_product_sot_gate",
    )
    if any(marker in haystack for marker in non_product_sot_markers):
        return False
    product_sot_markers = (
        "product_sot_result",
        "product_sot_candidate",
        "product sot candidate",
        "f5",
    )
    review_required_markers = (
        "candidate_owner_review_required_not_approved",
        "owner review required",
        "product sot owner review",
        "next required gate",
        "before method contract",
        "before method-contract",
    )
    approved_markers = (
        "owner approved product sot",
        "operator approved product sot",
        "product sot approved",
        '"decision": "approved',
        "decision: approved",
    )
    if any(marker in haystack for marker in approved_markers):
        return False
    return any(marker in haystack for marker in product_sot_markers) and any(
        marker in haystack for marker in review_required_markers
    )


def done_review_requires_owner_product_sot_gate(record: dict[str, Any]) -> bool:
    if str(record.get("status") or "").strip().lower() not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        return False
    if done_product_sot_candidate_requires_owner_review(record):
        return True
    text = task_record_text(record)
    review_pass = any(
        marker in text
        for marker in (
            "independent review pass",
            "verdict': 'pass",
            '"verdict": "pass',
            "result': 'pass",
            '"result": "pass',
        )
    )
    if not review_pass:
        return False
    if not done_review_targets_product_sot_candidate(record):
        return False
    return any(
        marker in text
        for marker in (
            "owner/product sot approval",
            "product sot approval or rebaseline",
            "product sot approval/rebaseline",
            "owner product sot approval",
            "before method-contract planning",
            "before method contract planning",
        )
    )


def done_post_review_owner_gate_closed(record: dict[str, Any]) -> bool:
    if str(record.get("status") or "").strip().lower() not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        return False
    body = task_body_json_object(record)
    text = task_record_text(record)
    has_post_review_gate_marker = (
        body.get("marker") == NO_IDLE_POST_REVIEW_GATE_MARKER
        or NO_IDLE_POST_REVIEW_GATE_MARKER in text
        or "prepare product sot owner decision package" in text
    )
    if not has_post_review_gate_marker:
        return False
    still_open_markers = (
        "no human decision has been recorded",
        "no owner decision has been recorded",
        "human decision required",
        "awaiting human decision",
        "awaiting owner decision",
        "choose approve",
        "request exact changes",
    )
    if any(marker in text for marker in still_open_markers):
        return False
    closed_markers = (
        "owner decision recorded",
        "human decision recorded",
        "operator decision recorded",
        "approval recorded",
        "human gate closed",
        "owner gate closed",
        "decision: approved",
        "decision': 'approved",
        '"decision": "approved',
        "approved product sot",
        "owner approved product sot",
        "operator approved product sot",
        "product sot approved",
        "decision: rejected",
        "decision': 'rejected",
        '"decision": "rejected',
        "rejected product sot",
        "rebaseline requested",
        "changes requested",
        "requested changes recorded",
    )
    return any(marker in text for marker in closed_markers)


def closed_post_review_owner_gate_refs(done: list[dict[str, Any]]) -> list[str]:
    return sorted(
        task_record_id(item)
        for item in done
        if task_record_id(item) and done_post_review_owner_gate_closed(item)
    )


def is_operator_understanding_confirmation_blocker(record: dict[str, Any]) -> bool:
    text = task_record_text(record)
    markers = (
        "operator_understanding_confirmation",
        "operator understanding confirmation",
        "pending_operator_confirmation",
        "operator_response_ref",
        "required_before_product_sot",
        "product_sot_blocked_until_operator_understanding_confirmed",
        "confirm/correct",
        "confirm or correct",
        "confirmar/corrigir",
        "confirmar ou corrigir",
        "confirme/corrija",
        "owner-readable understanding confirmation",
        "understanding confirmation is pending",
    )
    return any(marker in text for marker in markers)


def is_operator_input_blocker(record: dict[str, Any]) -> bool:
    text = task_record_text(record)
    external_input_markers = (
        "missing input",
        "missing inputs",
        "missing exact",
        "missing target",
        "missing public-safe",
        "required input",
        "required inputs",
        "needed input",
        "needed inputs",
        "provide exact",
        "provide requested",
        "target_repo_paths",
        "target url",
        "target_url",
        "prototype artifact",
        "package manifests",
        "scan scope",
        "authority/custody policy",
        "custody/signing policy",
        "mint address",
        "token program id",
    )
    return is_operator_understanding_confirmation_blocker(record) or any(
        marker in text for marker in external_input_markers
    )


def operator_input_request_for_blockers(blockers: list[dict[str, Any]]) -> dict[str, Any]:
    if any(is_operator_understanding_confirmation_blocker(item) for item in blockers):
        return {
            "request_type": "operator_understanding_confirmation",
            "reason": (
                "The factory produced an owner-readable understanding packet and Product SOT "
                "must remain blocked until the operator confirms or corrects it."
            ),
            "required_response": (
                "confirm the understanding, or send the exact correction to apply before Product SOT"
            ),
        }
    return {
        "request_type": "factory_blocker_input_or_decision_package",
        "reason": (
            "All unfinished visible work is blocked on missing inputs or an unfinished "
            "human-gate decision package. This is not approval-ready."
        ),
        "required_response": (
            "deliver the missing decision package/materials first, or ask for the exact "
            "missing source inputs; do not ask the operator to approve a summary-only gate"
        ),
    }


def dependency_operator_input_request_for_blockers(blockers: list[dict[str, Any]]) -> dict[str, Any]:
    if any(is_operator_understanding_confirmation_blocker(item) for item in blockers):
        return {
            "request_type": "operator_understanding_confirmation",
            "reason": (
                "Visible work is dependency-gated by an owner-readable understanding packet "
                "that needs operator confirmation or correction before Product SOT."
            ),
            "required_response": (
                "confirm the understanding, or provide the exact correction before Product SOT continues"
            ),
        }
    return {
        "request_type": "factory_blocker_input_or_decision_package",
        "reason": (
            "Visible todo work is dependency-gated while at least one blocker still "
            "needs exact inputs or a complete decision package. Asking for approval now "
            "would be a false human gate."
        ),
        "required_response": (
            "provide the exact missing inputs, or have the factory deliver the markdown, "
            "PDF and structured evidence package before requesting a decision"
        ),
    }


def no_idle_parent_refs(record: dict[str, Any]) -> list[str]:
    raw_parents = record.get("parents") or record.get("parent_ids") or []
    if not isinstance(raw_parents, list):
        return []
    refs: list[str] = []
    for parent in raw_parents:
        if isinstance(parent, dict):
            ref = str(parent.get("id") or parent.get("task_id") or parent.get("parent_id") or "").strip()
        else:
            ref = str(parent or "").strip()
        if ref:
            refs.append(ref)
    return refs


def no_idle_status_by_task_id(rows: dict[str, list[dict[str, Any]]]) -> dict[str, str]:
    status_by_id: dict[str, str] = {}
    for status, items in rows.items():
        for item in items:
            task_id = task_record_id(item)
            if task_id:
                status_by_id[task_id] = str(item.get("status") or status).strip().lower() or status
    return status_by_id


def no_idle_parent_map(rows: dict[str, list[dict[str, Any]]]) -> dict[str, list[str]]:
    parent_map: dict[str, list[str]] = {}
    for items in rows.values():
        for item in items:
            task_id = task_record_id(item)
            if task_id:
                parent_map[task_id] = no_idle_parent_refs(item)
    return parent_map


def canonical_frontier_resume_target(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any] | None:
    factoryctl = load_factoryctl()
    selector = getattr(factoryctl, "select_reconciled_canonical_frontier_task", None)
    if not callable(selector):
        return None
    normalized_rows = factoryctl.board_rows_from_snapshot({"rows": rows})
    task, selected_ref, reasons = selector(normalized_rows)
    if not isinstance(task, dict):
        return None
    task_id = task_record_id(task)
    if not task_id:
        return None
    return {
        "task_id": task_id,
        "task": task,
        "selected_ref": selected_ref if isinstance(selected_ref, dict) else None,
        "blocked_reasons": reasons if isinstance(reasons, list) else [],
    }


def blocked_ancestor_refs(
    task_id: str,
    *,
    parent_map: dict[str, list[str]],
    status_by_id: dict[str, str],
    seen: set[str] | None = None,
) -> set[str]:
    if seen is None:
        seen = set()
    if task_id in seen:
        return set()
    seen.add(task_id)
    blockers: set[str] = set()
    for parent_id in parent_map.get(task_id, []):
        parent_status = status_by_id.get(parent_id)
        if parent_status == "blocked":
            blockers.add(parent_id)
            continue
        if parent_status in {"todo", "ready", "running"}:
            blockers.update(
                blocked_ancestor_refs(
                    parent_id,
                    parent_map=parent_map,
                    status_by_id=status_by_id,
                    seen=seen,
                )
            )
    return blockers


def dependency_gated_todo_blockers(
    todo: list[dict[str, Any]],
    rows: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    status_by_id = no_idle_status_by_task_id(rows)
    parent_map = no_idle_parent_map(rows)
    blockers_by_todo: dict[str, list[str]] = {}
    for item in todo:
        task_id = task_record_id(item)
        if not task_id:
            continue
        blockers = sorted(
            blocked_ancestor_refs(
                task_id,
                parent_map=parent_map,
                status_by_id=status_by_id,
            )
        )
        if blockers:
            blockers_by_todo[task_id] = blockers
    return blockers_by_todo


def event_type_name(event: Any) -> str:
    if isinstance(event, dict):
        return str(event.get("type") or event.get("event") or event.get("action") or event.get("kind") or "").strip().lower()
    return str(event or "").strip().lower()


def event_payload_dict(event: Any) -> dict[str, Any]:
    if not isinstance(event, dict):
        return {}
    payload = event.get("payload")
    return payload if isinstance(payload, dict) else {}


def task_has_event_type(record: dict[str, Any], event_types: set[str]) -> bool:
    return any(event_type_name(event) in event_types for event in record.get("events") or [])


def task_block_event_kind(record: dict[str, Any]) -> str | None:
    for event in reversed(record.get("events") or []):
        if event_type_name(event) not in {"block", "blocked", "dependency_wait", "block_loop_detected"}:
            continue
        payload = event_payload_dict(event)
        raw_kind = event.get("block_kind") if isinstance(event, dict) else None
        if raw_kind is None:
            raw_kind = payload.get("kind") or payload.get("block_kind")
        kind = str(raw_kind or "").strip().lower()
        if kind:
            return kind
    return None


def native_dependency_wait_todo_blockers(
    todo: list[dict[str, Any]],
    rows: dict[str, list[dict[str, Any]]],
) -> dict[str, list[str]]:
    status_by_id = no_idle_status_by_task_id(rows)
    parent_map = no_idle_parent_map(rows)
    blockers_by_todo: dict[str, list[str]] = {}
    for item in todo:
        if not task_has_event_type(item, {"dependency_wait"}):
            continue
        task_id = task_record_id(item)
        if not task_id:
            continue
        blockers = sorted(
            parent_id
            for parent_id in parent_map.get(task_id, [])
            if status_by_id.get(parent_id) not in {None, "", "done"}
        )
        if task_block_event_kind(item) == "dependency":
            blockers_by_todo[task_id] = blockers
    return blockers_by_todo


def block_loop_detected_refs(rows: dict[str, list[dict[str, Any]]]) -> list[str]:
    refs: list[str] = []
    for items in rows.values():
        for item in items:
            if task_has_event_type(item, {"block_loop_detected"}):
                ref = task_record_id(item)
                if ref:
                    refs.append(ref)
    return sorted(set(refs))


def parse_timestamp_seconds(value: Any) -> float | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit():
        return float(text)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def json_object_from_maybe_string(value: Any) -> dict[str, Any] | None:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def iter_mapping_values(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, dict):
        found.append(value)
        for item in value.values():
            found.extend(iter_mapping_values(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(iter_mapping_values(item))
    return found


def worker_result_candidate_payloads(record: dict[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for source in [record, *(record.get("runs") or [])]:
        if not isinstance(source, dict):
            continue
        for key in ("metadata", "result_metadata", "output", "payload"):
            metadata = json_object_from_maybe_string(source.get(key))
            if metadata is not None:
                candidates.extend(iter_mapping_values(metadata))
        if str(source.get("record_type") or "").endswith("_result"):
            candidates.append(source)
    unique: list[dict[str, Any]] = []
    fingerprints: set[str] = set()
    for candidate in candidates:
        fingerprint = json.dumps(candidate, sort_keys=True, ensure_ascii=True, default=str)
        if fingerprint in fingerprints:
            continue
        fingerprints.add(fingerprint)
        unique.append(candidate)
    return unique


def validate_terminal_worker_result_candidate(
    candidate: dict[str, Any],
    *,
    expected_worker_id: str | None,
) -> tuple[bool, list[str]]:
    record_type = str(candidate.get("record_type") or "").strip()
    if not record_type.endswith("_result"):
        return False, ["record_type is not a worker result"]
    result = str(candidate.get("result") or "").strip().upper()
    if result not in {"PASS", "WAIVED"}:
        return False, [f"result {result or '<missing>'} does not authorize deterministic closeout"]
    factoryctl = load_factoryctl()
    expected_field = record_type
    worker_id = expected_worker_id if expected_worker_id in getattr(factoryctl, "WORKERS", {}) else None
    errors = factoryctl.validate_worker_result_record(
        candidate,
        expected_field=expected_field,
        expected_worker_id=worker_id,
        evidence_root=ROOT,
    )
    return not errors, [str(error) for error in errors]


def running_task_result_closeout_candidate(
    record: dict[str, Any],
    *,
    now_seconds: float | None = None,
    timeout_seconds: int = NO_IDLE_RUNNING_RESULT_CLOSEOUT_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
    task_id = task_record_id(record)
    if not task_id:
        return None
    factoryctl = load_factoryctl()
    if not factoryctl.task_has_structured_runtime_contract(record):
        return None
    runs = [item for item in record.get("runs") or [] if isinstance(item, dict)]
    running_runs = [item for item in runs if str(item.get("status") or "").strip().lower() == "running"]
    timestamps = [
        parse_timestamp_seconds(source.get(key))
        for source in [record, *running_runs, *runs]
        for key in ("started_at", "claimed_at", "created_at", "updated_at")
    ]
    started_at = min(value for value in timestamps if value is not None) if any(value is not None for value in timestamps) else None
    if started_at is None:
        return None
    now = now_seconds if now_seconds is not None else datetime.now(timezone.utc).timestamp()
    age_seconds = max(0.0, now - started_at)
    if age_seconds < timeout_seconds:
        return None
    validation_errors_by_candidate: list[list[str]] = []
    expected_worker_id = str(record.get("assignee") or "").strip() or None
    for candidate in worker_result_candidate_payloads(record):
        valid, errors = validate_terminal_worker_result_candidate(candidate, expected_worker_id=expected_worker_id)
        if valid:
            return {
                "task_ref": task_id,
                "title": str(record.get("title") or ""),
                "assignee": expected_worker_id,
                "age_seconds": int(age_seconds),
                "timeout_seconds": timeout_seconds,
                "worker_result": candidate,
                "worker_result_record_type": str(candidate.get("record_type") or ""),
                "worker_result_result": str(candidate.get("result") or "").strip().upper(),
                "worker_result_created_at": candidate.get("created_at"),
            }
        validation_errors_by_candidate.append(errors)
    return None


def running_result_closeout_candidates(rows: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    return [
        candidate
        for record in rows.get("running", [])
        for candidate in [running_task_result_closeout_candidate(record)]
        if candidate is not None
    ]


def enrich_no_idle_rows(
    *,
    hermes_bin: str,
    board: str,
    rows: dict[str, list[dict[str, Any]]],
    runner: Runner,
) -> dict[str, list[dict[str, Any]]]:
    enriched: dict[str, list[dict[str, Any]]] = {status: list(items) for status, items in rows.items()}
    if rows.get("ready"):
        return enriched
    for status in ("running", "todo", "blocked", "triage", "done"):
        next_items: list[dict[str, Any]] = []
        for item in rows.get(status, []):
            task_id = task_record_id(item)
            if not task_id:
                next_items.append(item)
                continue
            shown = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            task = task_readback_task(shown)
            merged = dict(item)
            for key in (
                "id",
                "task_id",
                "title",
                "body",
                "assignee",
                "status",
                "priority",
                "result",
                "summary",
                "workspace_path",
            ):
                if task.get(key) is not None and merged.get(key) is None:
                    merged[key] = task.get(key)
            if shown.get("latest_summary") is not None:
                merged["latest_summary"] = shown.get("latest_summary")
            merged["parents"] = task_readback_parents(shown)
            merged["comments"] = task_readback_comments(shown)[-3:]
            merged["events"] = task_readback_events(shown)[-5:]
            if status in {"running", "done"}:
                runs = task_run_records(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
                if runs:
                    merged["runs"] = runs[-3:]
            if status == "done":
                missing = missing_declared_local_artifacts(merged)
                if missing:
                    merged["missing_declared_artifacts"] = missing
            next_items.append(merged)
        enriched[status] = next_items
    return enriched


def declared_artifact_refs_from_mapping(mapping: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("artifacts", "artifact_paths", "artifact_refs", "evidence_refs"):
        value = mapping.get(key)
        if isinstance(value, list):
            refs.extend(str(item).strip() for item in value if str(item or "").strip())
        elif isinstance(value, str) and value.strip():
            refs.append(value.strip())
    for key in ("artifact_file", "review_packet_file", "source_file", "output_file"):
        value = str(mapping.get(key) or "").strip()
        if value:
            refs.append(value)
    for value in mapping.values():
        if isinstance(value, dict):
            refs.extend(declared_artifact_refs_from_mapping(value))
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    refs.extend(declared_artifact_refs_from_mapping(item))
    return refs


def declared_artifact_refs_from_task_record(record: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for event in record.get("events") or []:
        if not isinstance(event, dict):
            continue
        payload = event.get("payload")
        payload_obj = parse_json_object(payload)
        if payload_obj:
            refs.extend(declared_artifact_refs_from_mapping(payload_obj))
    for run in record.get("runs") or []:
        if not isinstance(run, dict):
            continue
        refs.extend(declared_artifact_refs_from_mapping(run))
        metadata_obj = parse_json_object(run.get("metadata"))
        if metadata_obj:
            refs.extend(declared_artifact_refs_from_mapping(metadata_obj))
    return sorted(set(refs))


def completed_declared_artifact_readback_repair_is_self_evidenced(record: dict[str, Any]) -> bool:
    body = parse_json_object(record.get("body")) or {}
    if str(body.get("plan_action") or "").strip() != "repair_declared_artifacts":
        return False
    if str(body.get("required_output") or "").strip() != "declared_artifact_readback_repair":
        return False
    for run in record.get("runs") or []:
        if not isinstance(run, dict):
            continue
        if str(run.get("status") or "").strip().lower() not in {"done", "complete", "completed"}:
            continue
        metadata = parse_json_object(run.get("metadata")) or {}
        if str(metadata.get("repair_status") or "").strip().upper() == "PASS":
            return True
        if (
            str(metadata.get("repair_type") or "").strip() == "declared_artifact_readback_repair"
            and str(metadata.get("result") or "").strip().upper() == "PASS"
        ):
            return True
        verification = metadata.get("verification") if isinstance(metadata.get("verification"), dict) else {}
        if str(verification.get("file_readback") or "").strip().upper() == "PASS":
            return True
    return False


def missing_declared_local_artifacts(record: dict[str, Any]) -> list[dict[str, Any]]:
    missing: list[dict[str, Any]] = []
    suppress_self_evidenced_repair_refs = completed_declared_artifact_readback_repair_is_self_evidenced(record)
    for ref in declared_artifact_refs_from_task_record(record):
        path = Path(ref)
        if not path.is_absolute():
            continue
        if suppress_self_evidenced_repair_refs and path.name in {
            "declared-artifact-readback-repair.json",
            "declared-artifact-readback-repair.md",
        }:
            continue
        valid_path = declared_local_artifact_valid_path(record, path)
        if valid_path is not None:
            continue
        reason = "worker declared a local artifact path but the file is absent from the Hermes runtime"
        if path.exists() and path.suffix.lower() == ".json":
            reason = "worker declared a JSON artifact path but the runtime file fails JSON readback"
        missing.append(
            {
                "artifact_name": path.name or "declared-artifact",
                "artifact_ref": "local-absolute-path:redacted",
                "local_path": str(path),
                "task_id": task_record_id(record),
                "reason": reason,
            }
        )
    return missing


def declared_local_artifact_exists(record: dict[str, Any], path: Path) -> bool:
    return declared_local_artifact_valid_path(record, path) is not None


def declared_local_artifact_valid_path(record: dict[str, Any], path: Path) -> Path | None:
    if path.exists():
        return path if declared_local_artifact_file_is_valid(path) else None
    if not path.name:
        return None
    workspace = Path(str(record.get("workspace_path") or ""))
    if not workspace.is_absolute() or not workspace.exists():
        return None
    candidates = [
        workspace / path.name,
        workspace / "decision-package" / path.name,
        workspace / "artifacts" / path.name,
        workspace / "artifact" / path.name,
        workspace / "outputs" / path.name,
        workspace / "output" / path.name,
    ]
    for candidate in candidates:
        if candidate.exists() and declared_local_artifact_file_is_valid(candidate):
            return candidate
    try:
        for candidate in workspace.rglob(path.name):
            if candidate.is_file() and declared_local_artifact_file_is_valid(candidate):
                return candidate
    except OSError:
        return None
    return None


def declared_local_artifact_file_is_valid(path: Path) -> bool:
    if not path.exists():
        return False
    if path.suffix.lower() != ".json":
        return True
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return False
    return True


def normalized_artifact_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def metadata_payload_candidate_keys(metadata: dict[str, Any], artifact_name: str) -> list[str]:
    artifact_token = normalized_artifact_token(Path(artifact_name).stem)
    preferred_keys = []
    if "orchestration" in artifact_token:
        preferred_keys.append("orchestration_result")
    if "methodcontract" in artifact_token or "planningresult" in artifact_token:
        preferred_keys.append("architecture_result")
    if "productface" in artifact_token:
        preferred_keys.append("product_face_packet")
    if "independentreview" in artifact_token:
        preferred_keys.append("independent_review_result")
    if "sourceledger" in artifact_token:
        preferred_keys.append("source_ledger_result")
    if "productsot" in artifact_token:
        preferred_keys.append("product_sot_result")

    dict_keys = [
        key for key, value in metadata.items()
        if isinstance(value, dict)
        and key not in {"hashes", "validation", "decision", "delivery_evidence"}
    ]
    for key in dict_keys:
        key_token = normalized_artifact_token(key)
        if key_token and (key_token in artifact_token or artifact_token in key_token):
            preferred_keys.append(key)
    if len(dict_keys) == 1:
        preferred_keys.append(dict_keys[0])
    return list(dict.fromkeys(key for key in preferred_keys if key in metadata and isinstance(metadata.get(key), dict)))


def human_gate_record_payload_for_declared_artifact(metadata: dict[str, Any], artifact_name: str) -> str | None:
    artifact_token = normalized_artifact_token(artifact_name)
    if "humangaterecord" not in artifact_token or "approved" not in artifact_token:
        return None
    decision = metadata.get("decision")
    if not isinstance(decision, dict) or decision.get("value") != "approved":
        return None
    record = {
        "artifact_file": artifact_name,
        "record_type": "human_gate_record",
        "decision_state": "approved",
        "decision": decision,
        "approval_scope": metadata.get("approval_scope") or [],
        "forbidden_scope": metadata.get("forbidden_scope") or [],
        "delivery_evidence": metadata.get("delivery_evidence") or [],
        "validation": metadata.get("validation") or {},
        "hashes": metadata.get("hashes") or {},
        "next_child_task": metadata.get("next_child_task"),
        "next_frontier": metadata.get("next_frontier") or [],
        "reconstructed_from": "task_runs.metadata",
    }
    return json.dumps({"human_gate_record": record}, indent=2, ensure_ascii=False) + "\n"


def metadata_payload_for_declared_artifact(record: dict[str, Any], artifact_name: str) -> str | None:
    for run in record.get("runs") or []:
        if not isinstance(run, dict):
            continue
        metadata = parse_json_object(run.get("metadata"))
        if not isinstance(metadata, dict):
            continue
        human_gate_payload = human_gate_record_payload_for_declared_artifact(metadata, artifact_name)
        if human_gate_payload is not None:
            return human_gate_payload
        for key, value in metadata.items():
            if not isinstance(value, dict):
                continue
            names = {
                str(value.get(name_key) or "").strip()
                for name_key in ("artifact_file", "review_packet_file", "source_file", "output_file")
            }
            names.discard("")
            if artifact_name in names:
                return json.dumps({key: value}, indent=2, ensure_ascii=False) + "\n"
        for key in metadata_payload_candidate_keys(metadata, artifact_name):
            return json.dumps({key: metadata[key]}, indent=2, ensure_ascii=False) + "\n"
    return None


def metadata_markdown_payload_for_declared_artifact(record: dict[str, Any], artifact_name: str) -> str | None:
    if Path(artifact_name).suffix.lower() not in {".md", ".markdown"}:
        return None
    artifact_token = normalized_artifact_token(artifact_name)
    for run in record.get("runs") or []:
        if not isinstance(run, dict):
            continue
        metadata = parse_json_object(run.get("metadata"))
        if not isinstance(metadata, dict):
            continue
        for key, value in metadata.items():
            if not isinstance(value, dict):
                continue
            refs = [
                str(item)
                for ref_key in ("artifact_paths", "artifacts", "artifact_files")
                for item in (value.get(ref_key) if isinstance(value.get(ref_key), list) else [])
            ]
            for ref_key in ("artifacts", "artifact_files"):
                ref_map = value.get(ref_key)
                if isinstance(ref_map, dict):
                    refs.extend(str(item) for item in ref_map.values() if isinstance(item, str))
            names = {Path(ref).name for ref in refs}
            key_token = normalized_artifact_token(key)
            if artifact_name not in names and not (
                key_token and (key_token in artifact_token or artifact_token in key_token)
            ):
                continue
            lines = [
                f"# {artifact_name}",
                "",
                "Reconstructed Markdown readback from structured Hermes run metadata.",
                "",
                f"- Source metadata key: `{key}`",
                f"- Source status: `{value.get('status') or 'unknown'}`",
                f"- Source task: `{value.get('task_id') or task_record_id(record) or 'unknown'}`",
                "",
            ]
            for section_key, title in (
                ("candidate_decisions", "Candidate Decisions"),
                ("review_requirements", "Review Requirements"),
                ("downstream_frozen", "Downstream Frozen"),
            ):
                items = value.get(section_key)
                if isinstance(items, list) and items:
                    lines.extend([f"## {title}", ""])
                    lines.extend(f"- {str(item)}" for item in items)
                    lines.append("")
            validation = value.get("validation")
            if isinstance(validation, dict) and validation:
                lines.extend(["## Validation", ""])
                lines.extend(f"- `{k}`: `{v}`" for k, v in sorted(validation.items()))
                lines.append("")
            hashes = value.get("artifact_sha256")
            if not isinstance(hashes, dict):
                hashes = value.get("sha256")
            if isinstance(hashes, dict) and hashes:
                lines.extend(["## Artifact Hashes", ""])
                lines.extend(f"- `{k}`: `{v}`" for k, v in sorted(hashes.items()))
                lines.append("")
            lines.extend(
                [
                    "## Boundary",
                    "",
                    "This reconstructed Markdown is a readback artifact. Hermes run metadata remains the structured source of truth.",
                    "",
                ]
            )
            return "\n".join(lines)
    return None


def declared_artifact_prefers_metadata(artifact_name: str) -> bool:
    return Path(artifact_name).suffix.lower() == ".json"


def artifact_payload_is_valid(artifact_name: str, payload: str) -> bool:
    if Path(artifact_name).suffix.lower() != ".json":
        return True
    try:
        json.loads(payload)
    except json.JSONDecodeError:
        return False
    return True


def log_diff_payload_for_declared_artifact(log_text: str, artifact_name: str) -> str | None:
    lines = log_text.splitlines()
    candidates = [
        index
        for index, line in enumerate(lines)
        if artifact_name in line and (
            ("a/" in line and "b/" in line)
            or "→" in line
            or "->" in line
        )
    ]
    for marker_index in reversed(candidates):
        start_index = None
        for index in range(marker_index + 1, min(len(lines), marker_index + 20)):
            if lines[index].startswith("@@"):
                start_index = index + 1
                break
        if start_index is None:
            continue
        recovered: list[str] = []
        for line in lines[start_index:]:
            if recovered and (line.startswith("  ┊") or line.startswith("┌") or line.startswith("╭")):
                break
            if line.startswith("+++"):
                continue
            if line.startswith("+"):
                recovered.append(line[1:])
                continue
            if line.startswith("@@") or line.startswith("-") or line.startswith(" "):
                continue
            if recovered and not line:
                break
        if recovered:
            return "\n".join(recovered) + "\n"
    return None


def materialize_missing_declared_artifacts(
    *,
    hermes_bin: str,
    board: str,
    rows: dict[str, list[dict[str, Any]]],
    runner: Runner,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    log_cache: dict[str, str] = {}
    for task in rows.get("done", []):
        missing = task.get("missing_declared_artifacts")
        if not isinstance(missing, list) or not missing:
            continue
        task_id = task_record_id(task)
        if not task_id:
            continue
        for item in missing:
            if not isinstance(item, dict):
                continue
            artifact_name = str(item.get("artifact_name") or "").strip()
            local_path = str(item.get("local_path") or "").strip()
            if not artifact_name or not local_path:
                continue
            path = Path(local_path)
            if not path.is_absolute():
                continue
            if declared_local_artifact_file_is_valid(path):
                continue
            source = "worker_log_diff"
            if task_id not in log_cache:
                log_cache[task_id] = task_log_text(
                    hermes_bin=hermes_bin,
                    board=board,
                    task_id=task_id,
                    runner=runner,
                )
            payload = log_diff_payload_for_declared_artifact(log_cache[task_id], artifact_name)
            if payload is not None and not artifact_payload_is_valid(artifact_name, payload):
                payload = None
            if payload is None and declared_artifact_prefers_metadata(artifact_name):
                source = "task_runs.metadata"
                payload = metadata_payload_for_declared_artifact(task, artifact_name)
                if payload is not None and not artifact_payload_is_valid(artifact_name, payload):
                    payload = None
            elif payload is None:
                source = "task_runs.metadata_markdown"
                payload = metadata_markdown_payload_for_declared_artifact(task, artifact_name)
                if payload is None:
                    source = "worker_log_diff"
            if payload is None:
                records.append(
                    {
                        "task_ref": PUBLIC_SAFE_KANBAN_REF,
                        "artifact_name": artifact_name,
                        "materialized": False,
                        "reason": "no recoverable metadata payload or worker log diff found",
                    }
                )
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(payload, encoding="utf-8")
            data = path.read_bytes()
            records.append(
                {
                    "task_ref": PUBLIC_SAFE_KANBAN_REF,
                    "artifact_name": artifact_name,
                    "materialized": True,
                    "recovery_source": source,
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "artifact_ref": "local-absolute-path:redacted",
                }
            )
    return records


def summarize_no_idle_rows(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    return {
        status: {
            "count": len(items),
            "task_refs": [task_record_id(item) for item in items if task_record_id(item)],
        }
        for status, items in rows.items()
    }


def classify_no_idle_state(rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    ready = rows.get("ready", [])
    running = rows.get("running", [])
    todo = rows.get("todo", [])
    raw_blocked = rows.get("blocked", [])
    done = rows.get("done", [])
    superseded_blocked_refs = superseded_review_blocker_refs(done)
    blocked = [
        item for item in raw_blocked
        if task_record_id(item) not in superseded_blocked_refs
    ]
    ignored_superseded_blocked_refs = sorted(
        task_record_id(item)
        for item in raw_blocked
        if task_record_id(item) in superseded_blocked_refs
    )
    state = summarize_no_idle_rows(rows)
    loop_refs = block_loop_detected_refs(rows)
    if loop_refs:
        return {
            "status": "remediation_required",
            "classification": "hermes_typed_block_loop_detected",
            "typed_block_kind": "transient",
            "block_loop_detected": True,
            "block_loop_task_refs": loop_refs,
            "blocked": True,
            "remediation_required": True,
            "human_gate_required": False,
            "operator_input_required": False,
            "next_action": (
                "route the loop to deterministic triage/repair; do not re-block the same task "
                "and do not ask the operator unless a delivered needs_input decision package exists"
            ),
            "state": state,
        }
    post_review_gate_candidates = [
        item for item in done
        if done_review_requires_owner_product_sot_gate(item)
    ]
    post_review_gate_refs = sorted(task_record_id(item) for item in post_review_gate_candidates if task_record_id(item))
    closed_post_review_gate_refs = closed_post_review_owner_gate_refs(done)
    if running:
        return {
            "status": "active",
            "classification": "running_work_exists",
            "blocked": False,
            "remediation_required": False,
            "human_gate_required": False,
            "next_action": "observe running Hermes tasks",
            "state": state,
        }
    if ready:
        return {
            "status": "dispatch_available",
            "classification": "ready_work_exists",
            "blocked": False,
            "remediation_required": False,
            "human_gate_required": False,
            "native_dispatch_required_next": True,
            "next_action": "run native Hermes dispatch",
            "state": state,
        }
    if not todo and not blocked and post_review_gate_candidates and closed_post_review_gate_refs:
        return {
            "status": "empty_or_complete",
            "classification": "post_review_owner_product_sot_gate_already_closed",
            "blocked": False,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "operator_input_task_refs": [],
            "human_gate_task_refs": [],
            "closed_human_gate_task_refs": closed_post_review_gate_refs,
            "post_review_task_refs": post_review_gate_refs,
            "ignored_superseded_blocked_task_refs": ignored_superseded_blocked_refs,
            "next_action": (
                "do not create another Product SOT owner decision package; the prior owner gate "
                "is closed, so continuation must come from an explicit live next-phase task or "
                "a precise blocker rather than duplicate gate verification"
            ),
            "state": state,
        }
    if not todo and not blocked and post_review_gate_candidates:
        return {
            "status": "remediation_required",
            "classification": "post_review_owner_product_sot_gate_package_missing",
            "blocked": True,
            "remediation_required": True,
            "human_gate_required": False,
            "operator_input_required": False,
            "operator_input_task_refs": [],
            "human_gate_task_refs": [],
            "post_review_task_refs": post_review_gate_refs,
            "ignored_superseded_blocked_task_refs": ignored_superseded_blocked_refs,
            "remediation_strategy": "create_post_review_owner_gate_package_task",
            "remediation_reason": (
                "A completed Product SOT candidate or Product SOT review requires owner approval "
                "or rebaseline before method-contract planning, but no live gate package task exists. "
                "The factory must prepare and deliver the decision package before asking the operator."
            ),
            "next_action": (
                "create a Product SOT owner decision package task, then let native Hermes dispatch "
                "deliver the materials and request the bounded decision"
            ),
            "state": state,
        }
    if not todo and not blocked:
        return {
            "status": "empty_or_complete",
            "classification": "no_unfinished_work_seen",
            "blocked": False,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "ignored_superseded_blocked_task_refs": ignored_superseded_blocked_refs,
            "next_action": "no no-idle action required",
            "state": state,
        }
    human_gate_blockers = [item for item in blocked if is_human_gate_decision_ready_blocker(item)]
    human_gate_refs = sorted(task_record_id(item) for item in human_gate_blockers if task_record_id(item))
    operator_input_blockers = [
        item
        for item in blocked
        if is_operator_input_blocker(item)
    ]
    operator_input_refs = sorted(task_record_id(item) for item in operator_input_blockers if task_record_id(item))
    review_repair_blockers = [
        item
        for item in blocked
        if is_review_failed_factory_repair_blocker(item)
    ]
    review_repair_refs = sorted(task_record_id(item) for item in review_repair_blockers if task_record_id(item))
    if blocked and len(operator_input_blockers) == len(blocked) and not todo:
        return {
            "status": "input_required",
            "classification": "only_operator_input_blockers_seen",
            "blocked": True,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": True,
            "operator_input_task_refs": operator_input_refs,
            "human_gate_task_refs": human_gate_refs,
            "operator_input_request": operator_input_request_for_blockers(operator_input_blockers),
            "next_action": "ask the operator for the exact confirmation, correction, or missing input before creating another remediation card",
            "state": state,
        }
    if blocked and len(human_gate_blockers) == len(blocked) and not todo:
        return {
            "status": "human_gate_required",
            "classification": "only_human_gate_blockers_seen",
            "blocked": True,
            "remediation_required": False,
            "human_gate_required": True,
            "operator_input_required": bool(operator_input_refs),
            "human_gate_task_refs": human_gate_refs,
            "operator_input_task_refs": operator_input_refs,
            "ignored_superseded_blocked_task_refs": ignored_superseded_blocked_refs,
            "human_decision_request": {
                "request_type": "factory_human_gate_decision",
                "reason": "All unfinished visible work is blocked on explicit human-gate tasks.",
                "required_response": "approve, reject, waive, revise scope, or provide requested input in the human-gate artifact",
            },
            "next_action": "ask the operator for the human-gate decision",
            "state": state,
        }
    if blocked and review_repair_blockers and len(review_repair_blockers) == len(blocked) and not todo:
        return {
            "status": "remediation_required",
            "classification": "only_factory_review_repair_blockers_seen",
            "blocked": True,
            "remediation_required": True,
            "human_gate_required": False,
            "operator_input_required": False,
            "operator_input_task_refs": [],
            "human_gate_task_refs": human_gate_refs,
            "factory_owned_package_task_refs": review_repair_refs,
            "review_repair_task_refs": review_repair_refs,
            "remediation_strategy": "create_targeted_review_repair_task",
            "remediation_reason": (
                "All unfinished visible work is blocked by an independent review failure "
                "with internal validator, artifact or handoff repair instructions. This is "
                "factory-owned repair, not operator input and not a human gate."
            ),
            "next_action": (
                "create a targeted repair task from the blocked review report, then let native "
                "Hermes dispatch run it before any human-gate question"
            ),
            "state": state,
        }
    factory_package_blockers = [
        item
        for item in blocked
        if not is_human_gate_decision_ready_blocker(item)
        and (is_factory_owned_package_blocker(item) or is_human_gate_package_blocker(item))
    ]
    factory_package_refs = sorted(task_record_id(item) for item in factory_package_blockers if task_record_id(item))
    if blocked and factory_package_blockers and len(factory_package_blockers) == len(blocked) and not todo:
        return {
            "status": "remediation_required",
            "classification": "only_factory_owned_package_blockers_seen",
            "blocked": True,
            "remediation_required": True,
            "human_gate_required": False,
            "operator_input_required": False,
            "operator_input_task_refs": [],
            "human_gate_task_refs": human_gate_refs,
            "factory_owned_package_task_refs": factory_package_refs,
            "remediation_reason": (
                "All unfinished visible work is blocked on a factory-owned decision package, "
                "owner-readable material, PDF, evidence index, owner review or artifact readback. "
                "This is internal factory repair, not operator input."
            ),
            "next_action": "create a factory-owned package/readback repair task before any human-gate question",
            "state": state,
        }
    dependency_blockers = dependency_gated_todo_blockers(todo, rows)
    native_dependency_blockers = native_dependency_wait_todo_blockers(todo, rows)
    if todo and native_dependency_blockers:
        return {
            "status": "dependency_gated",
            "classification": "hermes_native_dependency_wait",
            "typed_block_kind": "dependency",
            "hermes_native_dependency_wait": True,
            "blocked": True,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "human_gate_task_refs": human_gate_refs,
            "dependency_gated_task_refs": sorted(native_dependency_blockers),
            "dependency_blocker_task_refs": sorted({ref for refs in native_dependency_blockers.values() for ref in refs}),
            "next_action": "wait for Hermes native dependency handling or parent auto-resume; do not page the operator",
            "state": state,
        }
    identified_todo = [item for item in todo if task_record_id(item)]
    if todo and len(identified_todo) == len(todo) and len(dependency_blockers) == len(identified_todo):
        blocked_by_task_id = {task_record_id(item): item for item in blocked if task_record_id(item)}
        blocker_refs = sorted({ref for refs in dependency_blockers.values() for ref in refs})
        human_gate_dependency_refs = [
            ref for ref in blocker_refs if is_human_gate_blocker(blocked_by_task_id.get(ref, {}))
        ]
        input_dependency_refs = [
            ref for ref in blocker_refs if is_operator_input_blocker(blocked_by_task_id.get(ref, {}))
        ]
        factory_package_dependency_refs = [
            ref
            for ref in blocker_refs
            if is_factory_owned_package_blocker(blocked_by_task_id.get(ref, {}))
            or is_human_gate_package_blocker(blocked_by_task_id.get(ref, {}))
        ]
        repair_todo_refs = [
            task_record_id(item)
            for item in todo
            if task_record_id(item) and is_factory_owned_repair_task(item)
        ]
        if repair_todo_refs and (human_gate_dependency_refs or factory_package_dependency_refs):
            return {
                "status": "remediation_required",
                "classification": "factory_repair_task_dependency_gated_by_blocker_it_repairs",
                "blocked": True,
                "remediation_required": True,
                "human_gate_required": False,
                "operator_input_required": False,
                "human_gate_task_refs": sorted(set(human_gate_dependency_refs + human_gate_refs)),
                "operator_input_task_refs": [],
                "factory_owned_package_task_refs": sorted(set(factory_package_dependency_refs + factory_package_refs)),
                "dependency_gated_task_refs": sorted(dependency_blockers),
                "dependency_blocker_task_refs": blocker_refs,
                "repair_task_refs": sorted(repair_todo_refs),
                "remediation_reason": (
                    "A factory-owned repair task is dependency-gated by a blocked gate/package "
                    "that it is supposed to repair. The repair must be re-created or unlinked as "
                    "an independent ready work unit with a repairs_task_ref, not as a child of the blocker."
                ),
                "next_action": "repair the Kanban dependency graph, then let native Hermes dispatch run the factory-owned repair",
                "state": state,
            }
        if factory_package_dependency_refs or factory_package_refs:
            return {
                "status": "remediation_required",
                "classification": "todo_dependency_gated_by_factory_owned_package_blocker",
                "blocked": True,
                "remediation_required": True,
                "human_gate_required": False,
                "operator_input_required": False,
                "human_gate_task_refs": sorted(set(human_gate_dependency_refs + human_gate_refs)),
                "operator_input_task_refs": [],
                "factory_owned_package_task_refs": sorted(set(factory_package_dependency_refs + factory_package_refs)),
                "dependency_gated_task_refs": sorted(dependency_blockers),
                "dependency_blocker_task_refs": blocker_refs,
                "remediation_reason": (
                    "Visible todo work is dependency-gated behind factory-owned package/readback work. "
                    "The factory must repair the package or dependency graph before asking the operator."
                ),
                "next_action": "create targeted factory-owned package/dependency remediation; do not ask for a human-gate decision",
                "state": state,
            }
        if input_dependency_refs or operator_input_refs:
            return {
                "status": "input_required",
                "classification": (
                    "todo_dependency_gated_by_missing_operator_inputs"
                    if input_dependency_refs and not human_gate_refs
                    else "todo_dependency_gated_by_inputs_before_human_gate"
                ),
                "blocked": True,
                "remediation_required": False,
                "human_gate_required": False,
                "operator_input_required": True,
                "human_gate_task_refs": sorted(set(human_gate_dependency_refs + human_gate_refs)),
                "operator_input_task_refs": sorted(set(input_dependency_refs + operator_input_refs)),
                "dependency_gated_task_refs": sorted(dependency_blockers),
                "dependency_blocker_task_refs": blocker_refs,
                "operator_input_request": dependency_operator_input_request_for_blockers(
                    [
                        blocked_by_task_id[ref]
                        for ref in set(input_dependency_refs + operator_input_refs)
                        if ref in blocked_by_task_id
                    ]
                ),
                "next_action": "resolve missing inputs or deliver the decision package before asking for a human-gate decision",
                "state": state,
            }
        if human_gate_dependency_refs or human_gate_refs:
            return {
                "status": "human_gate_required",
                "classification": (
                    "todo_dependency_gated_by_human_gate_blocker"
                    if human_gate_dependency_refs
                    else "todo_dependency_gated_with_parallel_human_gate_blocker"
                ),
                "blocked": True,
                "remediation_required": False,
                "human_gate_required": True,
                "operator_input_required": bool(input_dependency_refs or operator_input_refs),
                "human_gate_task_refs": sorted(set(human_gate_dependency_refs + human_gate_refs)),
                "operator_input_task_refs": sorted(set(input_dependency_refs + operator_input_refs)),
                "dependency_gated_task_refs": sorted(dependency_blockers),
                "dependency_blocker_task_refs": blocker_refs,
                "human_decision_request": {
                    "request_type": "factory_human_gate_decision",
                    "reason": (
                        "The board has an explicit human-gate blocker while visible todo work is "
                        "dependency-gated; generic no-idle remediation would only create churn."
                    ),
                    "required_response": (
                        "approve, reject, request changes, or provide the exact scoped input "
                        "requested by the human-gate artifact"
                    ),
                },
                "operator_input_request": {
                    "request_type": "factory_blocker_input",
                    "reason": "At least one dependency blocker also appears to require exact operator/source input.",
                    "required_response": "provide the exact missing inputs, or ask the factory to re-read a named source artifact",
                }
                if input_dependency_refs or operator_input_refs
                else None,
                "next_action": "ask the operator for the current human-gate decision and any exact missing blocker inputs; do not create another generic remediation card",
                "state": state,
            }
        return {
            "status": "dependency_gated",
            "classification": "todo_dependency_gated_by_blocked_ancestors",
            "blocked": True,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "human_gate_task_refs": human_gate_refs,
            "dependency_gated_task_refs": sorted(dependency_blockers),
            "dependency_blocker_task_refs": blocker_refs,
            "next_action": "surface the specific blocker chain or route a targeted blocker repair; do not create generic no-idle remediation",
            "state": state,
        }
    return {
        "status": "remediation_required",
        "classification": "unfinished_work_without_ready_running_or_human_gate_only_block",
        "blocked": True,
        "remediation_required": True,
        "human_gate_required": False,
        "operator_input_required": bool(operator_input_refs),
        "operator_input_task_refs": operator_input_refs,
        "human_gate_task_refs": human_gate_refs,
        "remediation_reason": (
            "The board has unfinished work but native dispatch has no ready task to spawn "
            "and the idle state is not explained solely by explicit human gates."
        ),
        "next_action": "create a safe factory-owned remediation card, then let native Hermes dispatch pick it up",
        "state": state,
    }


def no_idle_remediation_body(*, board: str, classification: dict[str, Any]) -> dict[str, Any]:
    return {
        "packet_type": "factory_no_idle_remediation_request",
        "marker": NO_IDLE_REMEDIATION_MARKER,
        "board": board,
        "objective": "Restore autonomous factory progress without bypassing gates.",
        "observed_no_idle_state": classification,
        "deterministic_phase_contract": {
            "route_authority": "factory_phase_engine",
            "agent_may_choose_phase": False,
            "next_action_source": "phase_engine.next_required_artifact",
            "generic_frontier_selection_forbidden": True,
        },
        "allowed_actions": [
            "inspect Hermes board state",
            "compute deterministic phase engine state for the latest canonical card or start package",
            "create or repair only the artifact named by phase_engine.next_required_artifact",
            "promote only a card whose phase and frontier match the computed phase engine state",
            "emit a structured human decision request only when phase_engine.human_gate_allowed is true",
        ],
        "forbidden_actions": [
            "complete product work",
            "decide the next factory phase from prose, memory, title, comments or declared card phase alone",
            "approve or waive human gates",
            "deploy, release, spend funds or touch production",
            "execute material implementation without the normal factory gates",
        ],
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "dispatch_allowed_by_this_step": False,
        "native_dispatch_required_next": True,
    }


def create_no_idle_remediation_task(
    *,
    hermes_bin: str,
    board: str,
    workspace: str,
    assignee: str,
    classification: dict[str, Any],
    runner: Runner,
) -> str:
    body = no_idle_remediation_body(board=board, classification=classification)
    digest = idempotency_digest_fragment(contract_digest(body))
    return create_task(
        hermes_bin=hermes_bin,
        board=board,
        title="Restore autonomous factory progress",
        body=compact_json_argument(body),
        assignee=assignee,
        idempotency_key=f"overkill:no-idle:{public_safe_slug(board, fallback='board')}:{digest}",
        created_by=NO_IDLE_AUTHOR,
        workspace=workspace,
        blocked=False,
        workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
        current_step_key=FACTORY_KANBAN_DEFAULT_STEP_KEY,
        runner=runner,
    )


def create_factory_package_dependency_remediation_task(
    *,
    hermes_bin: str,
    board: str,
    workspace: str,
    assignee: str,
    classification: dict[str, Any],
    runner: Runner,
) -> str:
    body = no_idle_remediation_body(board=board, classification=classification)
    body["objective"] = (
        "Repair factory-owned package/readback or dependency blockers so native Hermes dependencies can resume."
    )
    body["targeted_remediation"] = {
        "plan_action": "repair_factory_owned_package_dependency_blocker",
        "factory_owned_package_task_refs": classification.get("factory_owned_package_task_refs") or [],
        "dependency_gated_task_refs": classification.get("dependency_gated_task_refs") or [],
        "dependency_blocker_task_refs": classification.get("dependency_blocker_task_refs") or [],
        "create_new_canonical_card": False,
        "human_gate_required": False,
        "operator_input_required": False,
        "repair_task_must_not_be_child_of_blocker_it_repairs": True,
    }
    body["allowed_actions"] = [
        "inspect blocked package/readback tasks and their typed block reasons",
        "repair missing package fields, readback artifacts, or dependency graph links",
        "complete or unblock only factory-owned blockers after structured evidence exists",
        "leave human gates untouched unless a complete decision package already exists",
    ]
    body["forbidden_actions"].extend(
        [
            "create a new canonical factory card just because a structured phase work card is blocked",
            "ask the operator to approve an internal package/dependency repair",
            "make the repair task a child of the blocker it is supposed to repair",
        ]
    )
    digest = idempotency_digest_fragment(contract_digest(body))
    return create_task(
        hermes_bin=hermes_bin,
        board=board,
        title="Repair factory package/dependency blockers",
        body=compact_json_argument(body),
        assignee=assignee,
        idempotency_key=f"overkill:no-idle-package-repair:{public_safe_slug(board, fallback='board')}:{digest}",
        created_by=NO_IDLE_AUTHOR,
        workspace=workspace,
        blocked=False,
        workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
        current_step_key=FACTORY_KANBAN_DEFAULT_STEP_KEY,
        runner=runner,
    )


def no_idle_review_repair_assignee(blockers: list[dict[str, Any]], fallback: str) -> str:
    text = " ".join(task_record_text(item) for item in blockers)
    if any(
        marker in text
        for marker in (
            "product sot",
            "product_sot",
            "outcome_contract",
            "full_product_sot_scope_coverage",
            "scope_in",
            "scope_out",
        )
    ):
        return "product-sot-planner"
    if any(marker in text for marker in ("method_contract", "method contract", "architecture")):
        return "factory-orchestrator"
    return fallback or "factory-orchestrator"


def no_idle_review_repair_body(
    *,
    board: str,
    classification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "packet_type": "factory_no_idle_review_repair_request",
        "marker": NO_IDLE_REVIEW_REPAIR_MARKER,
        "board": board,
        "objective": (
            "Repair the factory-owned package rejected by independent review and "
            "route it back to review without asking the operator."
        ),
        "blocked_review_task_refs": classification.get("review_repair_task_refs") or [],
        "observed_no_idle_state": classification,
        "kanban_workflow_binding": {
            "workflow_template_id": FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
            "current_step_key": "F5-product-sot",
            "runtime_field_required": True,
            "fallback_body_binding": True,
            "route_authority": "factory_phase_engine",
        },
        "required_actions": [
            "inspect the blocked independent review task, comments and report artifact",
            "repair the exact validator, public-safety, artifact or handoff failures named by the review",
            "rerun the relevant factoryctl validators before returning the package",
            "route a fresh independent-reviewer task or unblock the reviewed path only after evidence passes",
        ],
        "forbidden_actions": [
            "ask the operator for approval or input for internal validator repair",
            "treat review repair as a human gate",
            "approve Product SOT, method, architecture, release, funds, secrets or production",
            "advance downstream phases while the reviewed package still fails validators",
            "create another generic board reconcile card instead of the targeted repair",
        ],
        "human_gate_required": False,
        "operator_input_required": False,
        "native_dispatch_required_next": True,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
    }


def create_no_idle_review_repair_task(
    *,
    hermes_bin: str,
    board: str,
    workspace: str,
    assignee: str,
    classification: dict[str, Any],
    blockers: list[dict[str, Any]],
    runner: Runner,
) -> str:
    body = no_idle_review_repair_body(board=board, classification=classification)
    digest = idempotency_digest_fragment(contract_digest(body))
    repair_assignee = no_idle_review_repair_assignee(blockers, assignee)
    return create_task(
        hermes_bin=hermes_bin,
        board=board,
        title="Repair failed independent review package",
        body=compact_json_argument(body),
        assignee=repair_assignee,
        idempotency_key=f"overkill:no-idle-review-repair:{public_safe_slug(board, fallback='board')}:{digest}",
        created_by=NO_IDLE_AUTHOR,
        workspace=workspace,
        blocked=False,
        workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
        current_step_key="F5-product-sot",
        runner=runner,
    )


def no_idle_post_review_gate_body(
    *,
    board: str,
    classification: dict[str, Any],
) -> dict[str, Any]:
    return {
        "packet_type": "factory_no_idle_post_review_gate_package_request",
        "marker": NO_IDLE_POST_REVIEW_GATE_MARKER,
        "board": board,
        "objective": (
            "Prepare and deliver the owner/Product SOT decision package after a repaired "
            "independent review PASS, without approving the decision."
        ),
        "post_review_task_refs": classification.get("post_review_task_refs") or [],
        "ignored_superseded_blocked_task_refs": classification.get("ignored_superseded_blocked_task_refs") or [],
        "observed_no_idle_state": classification,
        "kanban_workflow_binding": {
            "workflow_template_id": FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
            "current_step_key": "F5-product-sot",
            "runtime_field_required": True,
            "fallback_body_binding": True,
            "route_authority": "factory_phase_engine",
        },
        "required_actions": [
            "inspect the PASS independent review report and the reviewed Product SOT artifacts",
            "prepare a canonical owner-facing Product SOT document in the operator locale as the primary human artifact",
            "keep APPROVAL_REQUEST, EVIDENCE_INDEX, OWNER_REVIEW, hashes, schemas and validation receipts as supporting evidence, not as the SOT body",
            "prepare the canonical Product SOT in markdown and PDF before asking for a decision",
            "attach or reference the canonical Product SOT markdown/PDF decision material available to the Telegram-facing manager",
            "when a primary operator channel such as Telegram is configured, deliver a short plain-text decision message and the Product SOT markdown/PDF as standard file attachments through the manager/operator-facing profile; do not use Telegram rich cards, rich drafts, media groups or table-rendered bot messages",
            "ask only the bounded Product SOT approve / rebaseline / request changes decision",
        ],
        "forbidden_actions": [
            "approve Product SOT on behalf of the operator",
            "start method-contract planning before the owner decision is recorded",
            "start architecture, implementation, repo cleanup, deployment, cloud mutation, DevNet/Mainnet material action, funds, custody, signing or release",
            "ask for a decision from a chat summary without the decision package material",
            "deliver an operational receipt, approval JSON, evidence index, hash list or worker log as if it were the Product SOT",
            "send Telegram rich cards, rich drafts, media groups or table-rendered bot messages as the primary decision package",
            "deliver an English-only Product SOT when the operator-facing language is Portuguese",
            "treat a Kanban comment alone as delivered material when a primary operator channel is configured",
            "send the operator-facing gate from a non-manager profile when a manager/operator-facing profile is configured",
            "treat a superseded failed review blocker as a live blocker",
        ],
        "human_gate_required": True,
        "operator_input_required": False,
        "native_dispatch_required_next": True,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
    }


def create_no_idle_post_review_gate_task(
    *,
    hermes_bin: str,
    board: str,
    workspace: str,
    classification: dict[str, Any],
    runner: Runner,
) -> str:
    body = no_idle_post_review_gate_body(board=board, classification=classification)
    digest = idempotency_digest_fragment(contract_digest(body))
    return create_task(
        hermes_bin=hermes_bin,
        board=board,
        title="Prepare Product SOT owner decision package",
        body=compact_json_argument(body),
        assignee="human-gate-clerk",
        idempotency_key=f"overkill:no-idle-post-review-gate:{public_safe_slug(board, fallback='board')}:{digest}",
        created_by=NO_IDLE_AUTHOR,
        workspace=workspace,
        blocked=False,
        workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
        current_step_key="F5-product-sot",
        runner=runner,
    )


def remediation_task_runtime_metadata(
    *,
    hermes_bin: str,
    board: str,
    task_id: str | None,
    runner: Runner,
) -> dict[str, Any]:
    if not task_id:
        return {
            "remediation_task_created": False,
            "remediation_task_status": None,
            "remediation_task_stale": False,
            "native_dispatch_required_next": False,
        }
    try:
        payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
        status = task_readback_status(payload)
    except RuntimeError:
        status = ""
    stale = status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
    return {
        "remediation_task_created": not stale,
        "remediation_task_status": status or "unknown",
        "remediation_task_stale": stale,
        "native_dispatch_required_next": status in {"ready", "unknown", ""},
    }


def close_running_tasks_with_valid_worker_results(
    *,
    hermes_bin: str,
    board: str,
    candidates: list[dict[str, Any]],
    runner: Runner,
) -> list[dict[str, Any]]:
    closed: list[dict[str, Any]] = []
    for candidate in candidates:
        task_id = str(candidate.get("task_ref") or "").strip()
        worker_result = candidate.get("worker_result") if isinstance(candidate.get("worker_result"), dict) else {}
        if not task_id or not worker_result:
            continue
        metadata = {
            "marker": NO_IDLE_RUNNING_RESULT_CLOSEOUT_MARKER,
            "record_type": "factory_no_idle_running_result_closeout",
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "task_ref": task_id,
            "closed_from_worker_result": {
                "record_type": worker_result.get("record_type"),
                "result": worker_result.get("result"),
                "created_at": worker_result.get("created_at"),
                "worker": worker_result.get("worker"),
                "promotion_authority": worker_result.get("promotion_authority"),
            },
            "age_seconds": candidate.get("age_seconds"),
            "timeout_seconds": candidate.get("timeout_seconds"),
            "complete_product_claim_allowed": False,
            "reason": (
                "Running Hermes task exceeded the no-idle closeout timeout after producing a valid "
                "terminal worker result; deterministic runtime closeout prevents a stuck running loop."
            ),
        }
        complete_task(
            hermes_bin=hermes_bin,
            board=board,
            task_id=task_id,
            result="DONE",
            summary="Closed by no-idle after validating terminal worker result evidence.",
            metadata=metadata,
            required_readback_markers=[NO_IDLE_RUNNING_RESULT_CLOSEOUT_MARKER],
            runner=runner,
        )
        closed.append(
            {
                "task_ref": task_id,
                "worker_result_record_type": candidate.get("worker_result_record_type"),
                "worker_result_result": candidate.get("worker_result_result"),
                "age_seconds": candidate.get("age_seconds"),
            }
        )
    return closed


def build_board_reconcile_plan_from_rows(*, board: str, rows: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    factoryctl = load_factoryctl()
    plan = factoryctl.build_board_reconcile_plan({"rows": rows}, board=board)
    errors = factoryctl.validate_board_reconcile_plan(plan)
    if errors:
        raise RuntimeError("factory board reconcile plan is invalid: " + "; ".join(errors))
    return plan


def deterministic_reconcile_task_body(
    *,
    plan: dict[str, Any],
    stale_remediation_task_refs: list[str] | None = None,
) -> dict[str, Any] | None:
    contract = plan.get("create_task_contract")
    if not isinstance(contract, dict):
        return None
    body = contract.get("body")
    if not isinstance(body, dict):
        return None
    task_body = copy.deepcopy(body)
    stale_refs = [str(ref).strip() for ref in (stale_remediation_task_refs or []) if str(ref).strip()]
    if stale_refs:
        task_body["runtime_lineage"] = {
            "lineage_type": "stale_terminal_remediation_replacement",
            "supersedes_runtime_task_refs": stale_refs,
            "reason": (
                "previous idempotent no-idle remediation task is terminal while the board still "
                "has no runnable safe frontier"
            ),
            "native_dispatch_required_next": True,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
        }
        task_body["stale_terminal_remediation_replacement"] = True
        task_body["supersedes_runtime_task_refs"] = stale_refs
    return task_body


def create_deterministic_reconcile_task(
    *,
    hermes_bin: str,
    board: str,
    workspace: str,
    plan: dict[str, Any],
    runner: Runner,
    stale_remediation_task_refs: list[str] | None = None,
) -> str | None:
    contract = plan.get("create_task_contract")
    if not isinstance(contract, dict):
        return None
    body = deterministic_reconcile_task_body(
        plan=plan,
        stale_remediation_task_refs=stale_remediation_task_refs,
    )
    if body is None:
        return None
    digest = idempotency_digest_fragment(contract_digest(body))
    return create_task(
        hermes_bin=hermes_bin,
        board=board,
        title=str(contract.get("title") or "Factory deterministic reconcile"),
        body=compact_json_argument(body),
        assignee=str(contract.get("assignee") or "factory-orchestrator"),
        idempotency_key=f"overkill:reconcile:{public_safe_slug(board, fallback='board')}:{digest}",
        created_by=NO_IDLE_AUTHOR,
        workspace=workspace,
        blocked=False,
        workflow_template_id=str(contract.get("workflow_template_id") or FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID),
        current_step_key=str(contract.get("current_step_key") or FACTORY_KANBAN_DEFAULT_STEP_KEY),
        runner=runner,
    )


def route_readiness_blockers(path: Path | None, required_worker_ids: list[str]) -> list[str]:
    if path is None:
        return ["route readiness manifest is required before live Hermes dispatch"]
    data = load_json(path)
    blockers: list[str] = []
    official_manifest = data.get("$schema") == ROUTE_READINESS_SCHEMA or "checks" in data
    if official_manifest:
        if data.get("$schema") != ROUTE_READINESS_SCHEMA:
            blockers.append("route readiness manifest must declare the official hermes-worker-route-readiness schema")
        if data.get("result") != "PASS":
            blockers.append(f"route readiness result is {data.get('result')!r}, expected PASS")
        if data.get("blocked_worker_count") not in {0, None}:
            blockers.append(f"route readiness has {data.get('blocked_worker_count')} blocked worker(s)")
        for worker_id in data.get("blocked_workers") or []:
            blockers.append(f"{worker_id}: route readiness reports worker blocked")
        raw_routes = data.get("checks") or []
    else:
        raw_routes = data.get("routes") or data.get("workers") or {}
    if isinstance(raw_routes, list):
        routes = {
            str(route.get("worker_id") or route.get("worker") or ""): route
            for route in raw_routes
            if isinstance(route, dict)
        }
    elif isinstance(raw_routes, dict):
        routes = {str(worker_id): route for worker_id, route in raw_routes.items() if isinstance(route, dict)}
    else:
        routes = {}
    for worker_id in sorted(set(required_worker_ids)):
        route = routes.get(worker_id)
        if not route:
            blockers.append(f"{worker_id}: missing route readiness record")
            continue
        checks = {
            "status_ready": str(route.get("status") or "ready").strip().lower() == "ready",
            "profile_exists": route.get("profile_exists") is True,
            "provider_configured": route.get("provider_configured", route.get("provider_status")) in {True, "pass", "PASS"},
            "model_configured": route.get("model_configured", route.get("model_status")) in {True, "pass", "PASS"},
            "credential_status": str(route.get("credential_status") or "").strip().lower() == "pass",
        }
        if not official_manifest:
            checks["capability_manifest"] = route.get("capability_manifest_ok", route.get("capability_status")) in {True, "pass", "PASS"}
        if route.get("blocked_reasons"):
            checks["blocked_reasons_empty"] = False
        failed = [name for name, ok in checks.items() if not ok]
        if failed:
            blockers.append(f"{worker_id}: route readiness failed ({', '.join(failed)})")
    return blockers


def strip_terminal_markup(value: str) -> str:
    return ANSI_ESCAPE_RE.sub("", value or "").replace("\r", "")


def parse_profile_list(output: str) -> dict[str, dict[str, str]]:
    profiles: dict[str, dict[str, str]] = {}
    for raw_line in strip_terminal_markup(output).splitlines():
        line = raw_line.strip()
        if not line:
            continue
        while line and not (line[0].isalnum() or line[0] in {"_", "-", "."}):
            line = line[1:].lstrip()
        if not line:
            continue
        columns = line.split()
        if len(columns) < 2:
            continue
        profile = columns[0]
        if profile.lower() in {"profile", "profiles"}:
            continue
        if profile.lower().startswith("profile "):
            continue
        profiles[profile] = {
            "model": columns[1],
            "gateway": columns[2] if len(columns) > 2 else "",
            "alias": columns[3] if len(columns) > 3 else "",
        }
    return profiles


def status_has_provider_auth(status_output: str, provider_name: str) -> bool:
    target = " ".join(str(provider_name or "").split()).lower()
    if not target:
        return False
    for raw_line in strip_terminal_markup(status_output).splitlines():
        normalized = " ".join(raw_line.split()).lower()
        if target in normalized and "logged in" in normalized and "not logged in" not in normalized:
            return True
    return False


def required_workers_from_ready_plan(path: Path | None) -> list[str]:
    if path is None:
        return []
    plan = load_ready_work_unit_materialization_plan(path.resolve())
    workers: list[str] = []
    for task in plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        for field in ("owner_worker", "reviewer_role"):
            worker_id = str(task.get(field) or "").strip()
            if worker_id and worker_id not in workers:
                workers.append(worker_id)
    return workers


def build_route_readiness_manifest(
    *,
    required_workers: list[str],
    profiles: dict[str, dict[str, str]],
    auth_ready: bool,
    ledger_ref: str,
    credential_evidence_ref: str,
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    blocked_workers: list[str] = []
    for worker_id in required_workers:
        profile = profiles.get(worker_id)
        profile_exists = profile is not None
        model = str((profile or {}).get("model") or "").strip()
        model_configured = bool(model and model not in {"-", "\u2014"})
        provider_configured = bool(auth_ready)
        credential_status = "pass" if auth_ready else "fail"
        blocked_reasons: list[str] = []
        if not profile_exists:
            blocked_reasons.append("profile_missing")
        if not model_configured:
            blocked_reasons.append("model_missing")
        if not provider_configured:
            blocked_reasons.append("provider_auth_not_proven")
        if credential_status != "pass":
            blocked_reasons.append("credential_not_proven")
        status = "ready" if not blocked_reasons else "blocked"
        if status == "blocked":
            blocked_workers.append(worker_id)
        checks.append(
            {
                "worker_id": worker_id,
                "task_id": f"route:{worker_id}",
                "required_before": "materialize-ready-work-units",
                "queue_class": "runtime-readiness-before-materialization",
                "status": status,
                "profile_exists": profile_exists,
                "config_ref": f"hermes-profile:{worker_id}" if profile_exists else None,
                "model_configured": model_configured,
                "provider_configured": provider_configured,
                "credential_status": credential_status,
                "credential_evidence": [credential_evidence_ref] if credential_status == "pass" else [],
                "blocked_reasons": blocked_reasons,
            }
        )
    return {
        "$schema": ROUTE_READINESS_SCHEMA,
        "schema": "overkill_factory_hermes_worker_route_readiness.v1",
        "ledger_ref": ledger_ref,
        "hermes_home_ref": "redacted-hermes-home",
        "result": "PASS" if not blocked_workers else "BLOCKED",
        "worker_count": len(required_workers),
        "blocked_worker_count": len(blocked_workers),
        "blocked_workers": blocked_workers,
        "checks": checks,
        "production_rule": (
            "Route readiness is collected from read-only Hermes profile/status readback; "
            "blocked workers must be repaired before live materialization or dispatch."
        ),
    }


def collect_route_readiness(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    required_workers: list[str] = []
    for worker_id in required_workers_from_ready_plan(args.plan):
        if worker_id not in required_workers:
            required_workers.append(worker_id)
    for worker_id in args.worker or []:
        normalized = str(worker_id or "").strip()
        if normalized and normalized not in required_workers:
            required_workers.append(normalized)
    if not required_workers:
        raise RuntimeError("route readiness collection requires --plan or at least one --worker")

    profile_output = run_checked([args.hermes_bin, "profile", "list"], runner).stdout
    status_output = run_checked([args.hermes_bin, "status"], runner).stdout
    profiles = parse_profile_list(profile_output)
    auth_ready = status_has_provider_auth(status_output, args.required_auth_provider)
    manifest = build_route_readiness_manifest(
        required_workers=required_workers,
        profiles=profiles,
        auth_ready=auth_ready,
        ledger_ref=args.ledger_ref,
        credential_evidence_ref=args.credential_evidence_ref,
    )
    if args.out:
        write_json(args.out, manifest)
    return manifest


def ensure_non_empty_body(body: str) -> None:
    if not str(body or "").strip():
        raise RuntimeError("Hermes task body must be non-empty before dispatch")


def task_readback_status(payload: dict[str, Any]) -> str:
    status = str(payload.get("status") or "").strip().lower()
    task = payload.get("task")
    if not status and isinstance(task, dict):
        status = str(task.get("status") or "").strip().lower()
    return status


def task_readback_task(payload: dict[str, Any]) -> dict[str, Any]:
    task = payload.get("task")
    if isinstance(task, dict):
        return task
    return payload


def task_readback_id(payload: dict[str, Any]) -> str:
    task = task_readback_task(payload)
    return str(task.get("id") or task.get("task_id") or payload.get("id") or payload.get("task_id") or "").strip()


def task_readback_events(payload: dict[str, Any]) -> list[Any]:
    events = payload.get("events") or payload.get("history") or payload.get("timeline") or []
    if isinstance(events, list):
        return events
    task = payload.get("task")
    if isinstance(task, dict):
        nested_events = task.get("events") or task.get("history") or task.get("timeline") or []
        if isinstance(nested_events, list):
            return nested_events
    return []


def task_readback_assignee(payload: dict[str, Any]) -> str:
    return str(task_readback_task(payload).get("assignee") or "").strip()


def task_readback_body(payload: dict[str, Any]) -> str:
    return str(task_readback_task(payload).get("body") or "")


def task_readback_comments(payload: dict[str, Any]) -> list[dict[str, Any]]:
    comments = payload.get("comments")
    if isinstance(comments, list):
        return [comment for comment in comments if isinstance(comment, dict)]
    task = payload.get("task")
    if isinstance(task, dict):
        nested = task.get("comments")
        if isinstance(nested, list):
            return [comment for comment in nested if isinstance(comment, dict)]
    return []


def task_has_active_idempotency_replay_evidence(payload: dict[str, Any]) -> bool:
    task = task_readback_task(payload)
    if task_readback_assignee(payload):
        return True
    if task.get("current_run_id") or task.get("run_id") or task.get("worker_pid"):
        return True
    if task_readback_comments(payload):
        return True
    runs = payload.get("runs")
    if not isinstance(runs, list):
        runs = task.get("runs")
    if isinstance(runs, list) and runs:
        return True
    replay_event_kinds = {
        "assigned",
        "claimed",
        "completed",
        "done",
        "running",
        "spawned",
        "unblocked",
    }
    for event in task_readback_events(payload):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind") or event.get("type") or event.get("event") or event.get("action") or "")
        if kind.strip().lower() in replay_event_kinds:
            return True
    return False


def task_readback_parents(payload: dict[str, Any]) -> list[str]:
    raw_parents = payload.get("parents")
    if not isinstance(raw_parents, list):
        task = payload.get("task")
        raw_parents = task.get("parents") if isinstance(task, dict) else []
    parents: list[str] = []
    for parent in raw_parents if isinstance(raw_parents, list) else []:
        if isinstance(parent, dict):
            parent_id = str(parent.get("id") or parent.get("task_id") or "").strip()
        else:
            parent_id = str(parent or "").strip()
        if parent_id:
            parents.append(parent_id)
    return parents


def task_readback_children(payload: dict[str, Any]) -> list[str]:
    raw_children = payload.get("children")
    if not isinstance(raw_children, list):
        task = payload.get("task")
        raw_children = task.get("children") if isinstance(task, dict) else []
    children: list[str] = []
    for child in raw_children if isinstance(raw_children, list) else []:
        if isinstance(child, dict):
            child_id = str(child.get("id") or child.get("task_id") or "").strip()
        else:
            child_id = str(child or "").strip()
        if child_id:
            children.append(child_id)
    return children


def task_dispatcher_workspace_ref(payload: dict[str, Any]) -> str:
    task = task_readback_task(payload)
    kind = str(task.get("workspace_kind") or task.get("workspace") or "").strip()
    path = str(task.get("workspace_path") or "").strip()
    if kind == "dir" and path:
        return f"dir:{path}"
    if kind:
        return kind
    return path


def ensure_dispatcher_visible_workspace(payload: dict[str, Any], *, task_id: str) -> None:
    workspace_ref = task_dispatcher_workspace_ref(payload)
    if not workspace_ref:
        raise RuntimeError(f"Hermes task {task_id} has no dispatcher workspace ref before release")
    normalized = workspace_ref.replace("\\", "/")
    if re.search(r"\b[A-Za-z]:/", normalized):
        raise RuntimeError(f"Hermes task {task_id} workspace is local to the adapter, not dispatcher-visible")


def pre_dispatch_activity_markers(payload: dict[str, Any]) -> list[str]:
    markers: list[str] = []
    task = task_readback_task(payload)
    if task.get("current_run_id") or task.get("run_id"):
        markers.append("current_run_id")
    if task.get("worker_pid"):
        markers.append("worker_pid")
    for event in task_readback_events(payload):
        if not isinstance(event, dict):
            continue
        kind = str(event.get("kind") or event.get("type") or event.get("event") or event.get("action") or "").strip().lower()
        if kind in {"claimed", "spawned", "spawn_failed", "running"}:
            markers.append(kind)
    runs = payload.get("runs")
    if isinstance(runs, list):
        for run in runs:
            if isinstance(run, dict):
                status = str(run.get("status") or run.get("outcome") or "").strip().lower()
                if status and status != "blocked":
                    markers.append(f"run:{status}")
    return markers


def task_has_ready_work_unit_supersession(payload: dict[str, Any]) -> bool:
    for comment in task_readback_comments(payload):
        if str(comment.get("author") or "").strip() != READY_WORK_UNIT_RECOVERY_AUTHOR:
            continue
        raw_body = str(comment.get("body") or comment.get("text") or comment.get("content") or "")
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            continue
        if isinstance(body, dict) and body.get("marker") == READY_WORK_UNIT_SUPERSESSION_MARKER:
            return True
    for event in task_readback_events(payload):
        if not isinstance(event, dict):
            continue
        event_body = event.get("payload")
        if isinstance(event_body, dict) and event_body.get("marker") == READY_WORK_UNIT_SUPERSESSION_MARKER:
            return True
    return False


def ready_work_unit_contamination_markers(payload: dict[str, Any]) -> list[str]:
    status = task_readback_status(payload)
    if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        return []
    if task_has_ready_work_unit_supersession(payload):
        return []
    return pre_dispatch_activity_markers(payload)


def ensure_no_pre_dispatch_activity(payload: dict[str, Any], *, task_id: str) -> None:
    markers = pre_dispatch_activity_markers(payload)
    if markers:
        raise RuntimeError(f"Hermes task {task_id} had pre-dispatch activity: {', '.join(markers)}")


def ensure_ready_work_unit_readback_contract(
    *,
    payload: dict[str, Any],
    task_id: str,
    expected_assignee: str,
    expected_packet_id: str,
) -> None:
    if task_readback_status(payload) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked after ready work-unit materialization")
    if task_readback_assignee(payload) != expected_assignee:
        raise RuntimeError(f"Hermes task {task_id} assignee readback does not match target profile")
    body = ready_work_unit_body(payload, task_id=task_id)
    if str(body.get("packet_id") or "").strip() != expected_packet_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit packet")
    ensure_no_pre_dispatch_activity(payload, task_id=task_id)


def ready_work_unit_readback_contract_error(
    *,
    payload: dict[str, Any],
    task_id: str,
    expected_assignee: str,
    expected_packet_id: str,
) -> str | None:
    try:
        ensure_ready_work_unit_readback_contract(
            payload=payload,
            task_id=task_id,
            expected_assignee=expected_assignee,
            expected_packet_id=expected_packet_id,
        )
    except RuntimeError as exc:
        return str(exc)
    return None


def ready_work_unit_body_transport_comments(*, payload: dict[str, Any], task_id: str, manifest: dict[str, Any]) -> list[str]:
    transport = manifest.get("context_transport")
    if not isinstance(transport, dict):
        raise RuntimeError(f"Hermes task {task_id} body transport manifest is missing")
    chunk_count = int(transport.get("chunk_count") or 0)
    expected_digest = str(transport.get("sha256") or "").strip()
    if chunk_count <= 0 or not expected_digest:
        raise RuntimeError(f"Hermes task {task_id} body transport manifest is incomplete")

    chunks_by_index: dict[int, str] = {}
    for comment in task_readback_comments(payload):
        if str(comment.get("author") or "").strip() != READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR:
            continue
        raw_body = str(comment.get("body") or comment.get("text") or comment.get("content") or "")
        try:
            body = json.loads(raw_body)
        except json.JSONDecodeError:
            continue
        if not isinstance(body, dict):
            continue
        if body.get("context_transport") != READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE:
            continue
        if str(body.get("packet_id") or "").strip() != str(manifest.get("packet_id") or "").strip():
            continue
        if str(body.get("sha256") or "").strip() != expected_digest:
            continue
        raw_index = body.get("chunk_index")
        index = int(raw_index) if raw_index is not None else -1
        if index < 0 or index >= chunk_count:
            raise RuntimeError(f"Hermes task {task_id} body transport chunk index is out of range")
        if index in chunks_by_index:
            raise RuntimeError(f"Hermes task {task_id} body transport has duplicate chunk {index}")
        chunks_by_index[index] = str(body.get("data") or "")

    missing = [index for index in range(chunk_count) if index not in chunks_by_index]
    if missing:
        raise RuntimeError(f"Hermes task {task_id} body transport is missing chunks: {missing}")
    chunks = [chunks_by_index[index] for index in range(chunk_count)]
    joined = "".join(chunks)
    actual_digest = hashlib.sha256(joined.encode("utf-8")).hexdigest()
    if actual_digest != expected_digest:
        raise RuntimeError(f"Hermes task {task_id} body transport sha256 does not match manifest")
    return chunks


def ready_work_unit_body_from_transport(*, payload: dict[str, Any], task_id: str, manifest: dict[str, Any]) -> dict[str, Any]:
    chunks = ready_work_unit_body_transport_comments(payload=payload, task_id=task_id, manifest=manifest)
    try:
        body = json.loads("".join(chunks))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes task {task_id} reconstructed ready work-unit body is not valid JSON") from exc
    if not isinstance(body, dict):
        raise RuntimeError(f"Hermes task {task_id} reconstructed ready work-unit body is not a JSON object")
    return body


def ready_work_unit_body(payload: dict[str, Any], *, task_id: str) -> dict[str, Any]:
    try:
        body = json.loads(task_readback_body(payload))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Hermes task {task_id} body readback is not valid JSON") from exc
    if not isinstance(body, dict):
        raise RuntimeError(f"Hermes task {task_id} body readback is not a JSON object")
    transport = body.get("context_transport")
    if isinstance(transport, dict):
        mode = str(transport.get("mode") or "").strip()
        if mode == READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE:
            return ready_work_unit_body_from_transport(payload=payload, task_id=task_id, manifest=body)
        raise RuntimeError(f"Hermes task {task_id} has unsupported ready work-unit body transport: {mode}")
    return body


def task_has_blocked_event(payload: dict[str, Any]) -> bool:
    if task_readback_status(payload) == "blocked":
        for event in task_readback_events(payload):
            if isinstance(event, dict):
                event_type = str(
                    event.get("type") or event.get("event") or event.get("action") or event.get("kind") or ""
                ).strip().lower()
                if event_type in {"block", "blocked"}:
                    return True
                continue
            text = str(event).lower()
            if re.search(r"\bblocked\b", text) and not re.search(r"\bunblocked\b", text):
                return True
    return False


def task_blocked_event_kinds(payload: dict[str, Any]) -> list[str]:
    kinds: list[str] = []
    for event in task_readback_events(payload):
        if not isinstance(event, dict):
            continue
        event_type = str(
            event.get("type") or event.get("event") or event.get("action") or event.get("kind") or ""
        ).strip().lower()
        if event_type not in {"block", "blocked"}:
            continue
        raw_kind = event.get("block_kind")
        payload_body = event.get("payload")
        if raw_kind is None and isinstance(payload_body, dict):
            raw_kind = payload_body.get("kind") or payload_body.get("block_kind")
        kind = str(raw_kind or "").strip().lower()
        if kind:
            kinds.append(kind)
    return kinds


def task_has_typed_blocked_event(payload: dict[str, Any], *, expected_kind: str) -> bool:
    expected = str(expected_kind or "").strip().lower()
    if expected not in HERMES_TYPED_BLOCK_KINDS:
        raise RuntimeError(f"unsupported Hermes block kind: {expected_kind}")
    kinds = task_blocked_event_kinds(payload)
    return expected in kinds if kinds else task_has_blocked_event(payload)


def task_has_unblocked_event(payload: dict[str, Any], required_markers: list[str] | None = None) -> bool:
    if task_readback_status(payload) == "blocked":
        return False
    markers = [marker.strip().lower() for marker in (required_markers or []) if marker.strip()]
    unblocked_event_seen = False
    for event in task_readback_events(payload):
        if isinstance(event, dict):
            event_type = str(
                event.get("type") or event.get("event") or event.get("action") or event.get("kind") or ""
            ).strip().lower()
            if event_type in {"unblock", "unblocked"}:
                unblocked_event_seen = True
                if not markers or all(marker in str(event).lower() for marker in markers):
                    return True
            continue
        text = str(event).lower()
        if "unblock" not in text:
            continue
        if all(marker in text for marker in markers):
            return True
    return unblocked_event_seen and history_contains_markers(payload, markers)


def history_contains_markers(payload: dict[str, Any], markers: list[str]) -> bool:
    if not markers:
        return True
    for key, _index, item in history_items(payload):
        if key == "runs":
            continue
        text = json.dumps(item, ensure_ascii=True, sort_keys=True).lower() if isinstance(item, dict) else str(item).lower()
        if all(marker in text for marker in markers):
            return True
    return False


def history_contains_any_marker(payload: dict[str, Any], markers: list[str]) -> bool:
    return any(history_contains_markers(payload, [marker]) for marker in markers if marker.strip())


def history_contains_all_markers_anywhere(payload: dict[str, Any], markers: list[str]) -> bool:
    return all(history_contains_any_marker(payload, [marker]) for marker in markers if marker.strip())


def task_has_ready_work_unit_release_record(payload: dict[str, Any]) -> bool:
    return history_contains_markers(
        payload,
        READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
    ) or task_has_unblocked_event(
        payload,
        required_markers=READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
    )


def worker_satisfied_by_reconciliation(plan: dict[str, Any], worker_id: str) -> bool:
    reconciliation = plan.get("completion_reconciliation")
    if not isinstance(reconciliation, dict):
        return False
    workers = reconciliation.get("workers")
    if not isinstance(workers, dict):
        return False
    row = workers.get(worker_id)
    return isinstance(row, dict) and row.get("satisfied") is True


def downstream_authorizations_by_worker(plan: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    by_worker: dict[str, list[dict[str, Any]]] = {}
    for authorization in plan.get("downstream_task_authorizations") or []:
        if not isinstance(authorization, dict):
            continue
        if (
            authorization.get("authorization_type") != "fresh_review_downstream_task"
            or authorization.get("authorization_state") != "worker_task_ready"
            or authorization.get("runtime_authority") != "hermes_kanban"
            or authorization.get("local_state_authority") is not False
        ):
            continue
        for worker_id in authorization.get("authorized_worker_ids") or []:
            worker_id = str(worker_id or "").strip()
            if worker_id and worker_id != "human-gate-clerk":
                by_worker.setdefault(worker_id, []).append(authorization)
    return by_worker


def downstream_worker_ready_after_fresh_review(
    plan: dict[str, Any],
    task: dict[str, Any],
    authorizations: dict[str, list[dict[str, Any]]],
) -> bool:
    if plan.get("transition_action") != "allow_and_create_worker_tasks":
        return False
    worker_id = str(task.get("worker_id") or "").strip()
    if not worker_id or worker_id == "human-gate-clerk":
        return False
    if worker_id not in authorizations:
        return False
    if task.get("status") != "requires_execution":
        return False
    if task.get("required_before") != "done":
        return False
    if task.get("dependency_authorization_state") == "review_ready":
        return False
    if worker_satisfied_by_reconciliation(plan, worker_id):
        return False
    return True


def history_items(payload: dict[str, Any]) -> list[tuple[str, int, Any]]:
    items: list[tuple[str, int, Any]] = []
    for key in HISTORY_SOURCE_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            items.extend((key, index, item) for index, item in enumerate(value))
    return items


def has_history_source(payload: dict[str, Any]) -> bool:
    return any(isinstance(payload.get(key), list) for key in HISTORY_SOURCE_KEYS)


def recovery_attempt_history_refs(payload: dict[str, Any], route_id: str, route_digest: str) -> list[str]:
    route = route_id.strip().lower()
    digest = route_digest.strip().lower()
    if not route or not digest:
        return []
    refs: list[str] = []
    for key, index, item in history_items(payload):
        text = json.dumps(item, ensure_ascii=True, sort_keys=True).lower() if isinstance(item, dict) else str(item).lower()
        if route in text and digest in text and RECOVERY_ATTEMPT_MARKER in text:
            refs.append(f"{key}:{index}")
    return refs


def retry_policy_max_attempts(route: dict[str, Any]) -> int:
    policy = route.get("retry_policy")
    value = policy.get("max_attempts") if isinstance(policy, dict) else None
    if isinstance(value, int) and value >= 1:
        return value
    return 1


def ensure_blocked_event(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    reason: str,
    kind: str = DEFAULT_RUNTIME_GATE_BLOCK_KIND,
    runner: Runner = default_runner,
) -> None:
    block_kind = str(kind or "").strip().lower()
    if block_kind not in HERMES_TYPED_BLOCK_KINDS:
        raise RuntimeError(f"Hermes block kind must be one of {sorted(HERMES_TYPED_BLOCK_KINDS)}")
    run_checked(
        hermes_kanban(hermes_bin, board, "block", "--kind", block_kind, task_id, reason),
        runner,
    )
    shown = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    try:
        payload = json.loads(shown.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hermes show --json did not return JSON while verifying blocked event") from exc
    if not isinstance(payload, dict) or not task_has_typed_blocked_event(payload, expected_kind=block_kind):
        raise RuntimeError(f"Hermes task {task_id} is not durably blocked after block command")


def unblock_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    reason: str,
    required_readback_markers: list[str] | None = None,
    runner: Runner = default_runner,
) -> None:
    if required_readback_markers:
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "comment",
                "--author",
                "overkill-factory",
                task_id,
                reason,
            ),
            runner,
        )
    run_checked(hermes_kanban(hermes_bin, board, "unblock", task_id, "--reason", reason), runner)
    shown = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    try:
        payload = json.loads(shown.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hermes show --json did not return JSON while verifying unblock event") from exc
    if not isinstance(payload, dict) or not task_has_unblocked_event(payload, required_readback_markers):
        raise RuntimeError(f"Hermes task {task_id} is not durably unblocked after unblock command")


def promote_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    reason: str,
    required_readback_markers: list[str] | None = None,
    runner: Runner = default_runner,
) -> None:
    if required_readback_markers:
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "comment",
                "--author",
                "overkill-factory",
                task_id,
                reason,
            ),
            runner,
        )
    run_checked(hermes_kanban(hermes_bin, board, "promote", task_id, reason), runner)
    shown = run_checked(hermes_kanban(hermes_bin, board, "show", task_id, "--json"), runner)
    try:
        payload = json.loads(shown.stdout or "{}")
    except json.JSONDecodeError as exc:
        raise RuntimeError("Hermes show --json did not return JSON while verifying promote event") from exc
    if not isinstance(payload, dict):
        raise RuntimeError("Hermes show --json did not return an object while verifying promote event")
    status = task_readback_status(payload)
    if status not in {"ready", "running", "done"}:
        raise RuntimeError(f"Hermes task {task_id} was not promoted into an executable state")
    if required_readback_markers and not history_contains_all_markers_anywhere(payload, required_readback_markers):
        raise RuntimeError(f"Hermes task {task_id} promote readback is missing required retry markers")


def link_task_dependency(
    *,
    hermes_bin: str,
    board: str,
    parent_task_id: str,
    child_task_id: str,
    runner: Runner = default_runner,
) -> None:
    run_checked(hermes_kanban(hermes_bin, board, "link", parent_task_id, child_task_id), runner)
    child_payload = show_task(hermes_bin=hermes_bin, board=board, task_id=child_task_id, runner=runner)
    child_task = task_readback_task(child_payload)
    parent_ids = {str(item) for item in child_task.get("parents", []) if str(item).strip()}
    if parent_task_id not in parent_ids:
        raise RuntimeError(f"Hermes dependency link {parent_task_id} -> {child_task_id} did not persist")


def unlink_task_dependency(
    *,
    hermes_bin: str,
    board: str,
    parent_task_id: str,
    child_task_id: str,
    work_unit_id: str,
    authority_task_ref: str | None,
    runner: Runner = default_runner,
) -> bool:
    child_payload = show_task(hermes_bin=hermes_bin, board=board, task_id=child_task_id, runner=runner)
    if parent_task_id not in task_readback_parents(child_payload):
        return False
    run_checked(hermes_kanban(hermes_bin, board, "unlink", parent_task_id, child_task_id), runner)
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            child_task_id,
            compact_json_argument(
                {
                    "marker": READY_WORK_UNIT_SUPERSEDED_PARENT_UNLINKED_MARKER,
                    "work_unit_id": work_unit_id,
                    "superseded_parent_ref": parent_task_id,
                    "authority_task_ref": authority_task_ref,
                    "reason": "newer post-repair authority selected retry/done path; stale blocked review parent no longer owns execution gating",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    readback = show_task(hermes_bin=hermes_bin, board=board, task_id=child_task_id, runner=runner)
    if parent_task_id in task_readback_parents(readback):
        raise RuntimeError(f"Hermes task {child_task_id} still has superseded parent {parent_task_id} after unlink")
    return True


def complete_task(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    result: str,
    summary: str,
    metadata: dict[str, Any],
    required_readback_markers: list[str] | None = None,
    runner: Runner = default_runner,
) -> None:
    if required_readback_markers:
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "comment",
                "--author",
                READY_WORK_UNIT_RECONCILIATION_AUTHOR,
                task_id,
                compact_json_argument(metadata),
            ),
            runner,
        )
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "complete",
            task_id,
            "--result",
            result,
            "--summary",
            summary,
            "--metadata",
            compact_json_argument(metadata),
        ),
        runner,
    )
    payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    if task_readback_status(payload) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        raise RuntimeError(f"Hermes task {task_id} is not durably completed after complete command")
    if required_readback_markers and not history_contains_all_markers_anywhere(payload, required_readback_markers):
        raise RuntimeError(f"Hermes task {task_id} completion readback lacks required reconciliation markers")


def record_live_binding(
    *,
    ledger_path: Path,
    card_id: str,
    board: str,
    main_task_id: str,
    worker_task_ids: dict[str, str],
    idempotency_contract: dict[str, Any] | None = None,
) -> None:
    ledger = load_json(ledger_path)
    tasks = ledger.setdefault("tasks", {})
    for task in tasks.values():
        if not isinstance(task, dict):
            continue
        worker_id = str(task.get("worker_id") or "")
        hermes_task_id = worker_task_ids.get(worker_id)
        if str(task.get("card_id") or "") != card_id or not hermes_task_id:
            continue
        task["materialization_state"] = "materialized_in_hermes"
        task["runtime_refs"] = {
            "hermes_board_ref": f"hermes:{board}",
            "hermes_task_ref": hermes_task_id,
            "hermes_run_ref": "external:pending-hermes-run",
        }
        task["local_record_role"] = "idempotency_projection"
    bindings = ledger.setdefault("live_bindings", {})
    bindings[card_id] = {
        "card_id": card_id,
        "binding_role": "hermes_ref_projection",
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "board": board,
        "main_task_id": main_task_id,
        "worker_task_ids": worker_task_ids,
    }
    if idempotency_contract:
        bindings[card_id]["idempotency_contract"] = idempotency_contract
    write_json(ledger_path, ledger)


def validate_live_binding(*, ledger_path: Path, card_id: str, board: str, main_task_id: str) -> None:
    ledger = load_json(ledger_path)
    if ledger.get("runtime_authority") != "hermes_kanban" or ledger.get("local_state_authority") is not False:
        raise RuntimeError("ledger is not a Hermes-authoritative projection; refuse to complete arbitrary Hermes task")
    binding = (ledger.get("live_bindings") or {}).get(card_id)
    if not isinstance(binding, dict):
        raise RuntimeError(f"missing live binding for card {card_id}; refuse to complete arbitrary Hermes task")
    if binding.get("runtime_authority") != "hermes_kanban" or binding.get("local_state_authority") is not False:
        raise RuntimeError("live binding is not a Hermes-authoritative projection; refuse to complete arbitrary Hermes task")
    if binding.get("binding_role") != "hermes_ref_projection":
        raise RuntimeError("live binding must be a Hermes ref projection")
    if binding.get("board") != board or binding.get("main_task_id") != main_task_id:
        raise RuntimeError("main task id does not match the live binding for this card and board")


def ensure_board(
    *,
    hermes_bin: str,
    board: str,
    default_workdir: str | None,
    name: str = "Overkill Factory Live Smoke",
    description: str = "Isolated board for Overkill Factory adapter validation.",
    icon: str = "O",
    color: str = "#0f766e",
    runner: Runner = default_runner,
) -> bool:
    listed = run_checked([hermes_bin, "kanban", "boards", "list", "--json"], runner)
    boards = json.loads(listed.stdout or "[]")
    if any(isinstance(item, dict) and item.get("slug") == board for item in boards):
        return False
    args = [
        hermes_bin,
        "kanban",
        "boards",
        "create",
        board,
        "--name",
        name,
        "--description",
        description,
        "--icon",
        icon,
        "--color",
        color,
    ]
    if default_workdir:
        args.extend(["--default-workdir", default_workdir])
    run_checked(args, runner)
    return True


def create_task(
    *,
    hermes_bin: str,
    board: str,
    title: str,
    body: str,
    assignee: str,
    idempotency_key: str,
    created_by: str,
    workspace: str,
    blocked: bool,
    workflow_template_id: str | None = None,
    current_step_key: str | None = None,
    parent_task_ids: list[str] | None = None,
    runner: Runner = default_runner,
) -> str:
    ensure_non_empty_body(body)
    if blocked:
        return create_blocked_task_before_assignment(
            hermes_bin=hermes_bin,
            board=board,
            title=title,
            body=body,
            assignee=assignee,
            idempotency_key=idempotency_key,
            created_by=created_by,
            workspace=workspace,
            blocked_reason="Overkill Factory gate starts blocked until required authority evidence passes.",
            workflow_template_id=workflow_template_id,
            current_step_key=current_step_key,
            runner=runner,
        )
    workspace_arg = hermes_workspace_arg(workspace)
    args = hermes_kanban(
        hermes_bin,
        board,
        "create",
        title,
        "--body",
        body,
        "--assignee",
        assignee,
        "--idempotency-key",
        idempotency_key,
        "--created-by",
        created_by,
        "--workspace",
        workspace_arg,
    )
    for parent_task_id in parent_task_ids or []:
        parent_ref = str(parent_task_id or "").strip()
        if parent_ref:
            args.extend(["--parent", parent_ref])
    args.append("--json")
    task_id = parse_task_id_or_find_idempotent(
        output=run_checked(args, runner).stdout,
        hermes_bin=hermes_bin,
        board=board,
        idempotency_key=idempotency_key,
        runner=runner,
    )
    apply_native_workflow_state(
        board=board,
        task_id=task_id,
        workflow_template_id=workflow_template_id,
        current_step_key=current_step_key,
    )
    if parent_task_ids:
        readback = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
        parent_refs = {str(item).strip() for item in parent_task_ids if str(item or "").strip()}
        persisted_refs = set(task_readback_parents(readback))
        missing_refs = sorted(parent_refs - persisted_refs)
        if missing_refs:
            raise RuntimeError(
                f"Hermes parent dependency edge did not persist for task {task_id}: {', '.join(missing_refs)}"
            )
    return task_id


def create_native_dependency_wait_task(
    *,
    hermes_bin: str,
    board: str,
    title: str,
    body: str,
    assignee: str,
    parent_task_id: str,
    idempotency_key: str,
    created_by: str,
    workspace: str,
    workflow_template_id: str | None = None,
    current_step_key: str | None = None,
    runner: Runner = default_runner,
) -> str:
    task_id = create_task(
        hermes_bin=hermes_bin,
        board=board,
        title=title,
        body=body,
        assignee=assignee,
        idempotency_key=idempotency_key,
        created_by=created_by,
        workspace=workspace,
        blocked=False,
        workflow_template_id=workflow_template_id,
        current_step_key=current_step_key,
        parent_task_ids=[parent_task_id],
        runner=runner,
    )
    readback = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    status = task_readback_status(readback)
    if status not in {"todo", "ready", "running", "done"}:
        raise RuntimeError(f"Hermes native dependency task {task_id} has unexpected status {status!r}")
    if status != "todo":
        ensure_no_pre_dispatch_activity(readback, task_id=task_id)
    if parent_task_id not in task_readback_parents(readback):
        raise RuntimeError(f"Hermes native dependency task {task_id} lost parent {parent_task_id}")
    return task_id


def create_blocked_task_before_assignment(
    *,
    hermes_bin: str,
    board: str,
    title: str,
    body: str,
    assignee: str,
    idempotency_key: str,
    created_by: str,
    workspace: str,
    blocked_reason: str,
    block_kind: str = DEFAULT_RUNTIME_GATE_BLOCK_KIND,
    workflow_template_id: str | None = None,
    current_step_key: str | None = None,
    runner: Runner = default_runner,
) -> str:
    ensure_non_empty_body(body)
    task_id = parse_task_id_or_find_idempotent(
        output=run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "create",
                title,
                "--body",
                body,
                "--idempotency-key",
                idempotency_key,
                "--created-by",
                created_by,
                "--workspace",
                hermes_workspace_arg(workspace),
                "--json",
            ),
            runner,
        ).stdout,
        hermes_bin=hermes_bin,
        board=board,
        idempotency_key=idempotency_key,
        runner=runner,
    )
    apply_native_workflow_state(
        board=board,
        task_id=task_id,
        workflow_template_id=workflow_template_id,
        current_step_key=current_step_key,
    )
    created_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    if (
        task_readback_status(created_task) in ACTIVE_OR_TERMINAL_STATUSES
        and task_has_active_idempotency_replay_evidence(created_task)
    ):
        return task_id
    ensure_blocked_event(
        hermes_bin=hermes_bin,
        board=board,
        task_id=task_id,
        reason=blocked_reason,
        kind=block_kind,
        runner=runner,
    )
    blocked_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    ensure_no_pre_dispatch_activity(blocked_task, task_id=task_id)
    if task_readback_status(blocked_task) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked before assignment")
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "assign",
            task_id,
            assignee,
        ),
        runner,
    )
    assigned_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    ensure_no_pre_dispatch_activity(assigned_task, task_id=task_id)
    if task_readback_status(assigned_task) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked after assignment")
    if task_readback_assignee(assigned_task) != assignee:
        raise RuntimeError(f"Hermes task {task_id} assignee readback does not match target profile")
    return task_id


def bridge_start_board_slug(run_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(run_id or "").strip().lower()).strip("-")
    if len(slug) < 3:
        slug = "factory-start"
    return slug[:80].strip("-") or "factory-start"


def load_bridge_start_request(path: Path) -> dict[str, Any]:
    request = load_json(path)
    if request.get("record_type") != BRIDGE_START_RECORD_TYPE:
        raise RuntimeError(f"bridge start request must have record_type={BRIDGE_START_RECORD_TYPE}")
    run_id = str(request.get("run_id") or "").strip()
    if not run_id:
        raise RuntimeError("bridge start request requires run_id")
    recipient = request.get("handoff_to_factory")
    if not isinstance(recipient, dict):
        raise RuntimeError("bridge start request requires handoff_to_factory")
    if recipient.get("orchestrator_worker") != BRIDGE_START_DEFAULT_ASSIGNEE:
        raise RuntimeError("bridge start request must be addressed to factory-orchestrator")
    limits = request.get("bridge_limits") if isinstance(request.get("bridge_limits"), dict) else {}
    for field in ("bridge_must_not_create_hermes_board", "bridge_must_not_create_hermes_cards", "bridge_must_not_dispatch_workers"):
        if limits.get(field) is not True:
            raise RuntimeError(f"bridge start request must keep {field}=true")
    action = request.get("requested_factory_action") if isinstance(request.get("requested_factory_action"), dict) else {}
    if action.get("action") != "start_factory_run":
        raise RuntimeError("bridge start request must request start_factory_run")
    return request


def load_optional_source_envelope(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    envelope = load_json(path)
    if envelope.get("record_type") != "factory_bridge_source_envelope":
        raise RuntimeError("source envelope must have record_type=factory_bridge_source_envelope")
    return envelope


def build_factory_run_graph(
    *,
    start_request: dict[str, Any],
    source_envelope: dict[str, Any] | None,
    start_request_ref: str,
    source_envelope_ref: str | None,
) -> dict[str, Any]:
    run_id = str(start_request["run_id"])
    operator_language = operator_language_from_start(start_request, source_envelope)
    language_policy = operator_language_policy(operator_language)
    backbone = load_factory_run_graph_backbone_from_catalog(language=operator_language)
    graph_seed = {
        "run_id": run_id,
        "start_request_digest": contract_digest(start_request),
        "source_envelope_digest": contract_digest(source_envelope or {}),
        "operator_language": operator_language,
        "operator_language_policy": language_policy,
        "backbone": backbone,
    }
    graph_id = f"factory-run-graph:{bridge_start_board_slug(run_id)}:{idempotency_digest_fragment(contract_digest(graph_seed))}"
    root_node = {
        "node_id": "F1-intake",
        "phase_id": "F1",
        "step_key": FACTORY_KANBAN_DEFAULT_STEP_KEY,
        "title": localized_phase_title("F1", "Intake", operator_language),
        "assignee": BRIDGE_START_DEFAULT_ASSIGNEE,
        "required_output": "universal_signal_intake",
        "activation_rule": "factory_bridge_start_request validated",
        "node_kind": "root",
        "task_role": BRIDGE_START_ROOT_TASK_TYPE,
    }
    backbone_nodes: list[dict[str, Any]] = []
    for node in backbone:
        materialized_node = dict(node)
        materialized_node.setdefault("node_kind", "backbone")
        materialized_node["task_role"] = FACTORY_RUN_GRAPH_NODE_PACKET_TYPE
        backbone_nodes.append(materialized_node)
    all_nodes = [root_node, *backbone_nodes]
    edges = [
        {"from": all_nodes[index]["node_id"], "to": all_nodes[index + 1]["node_id"], "kind": "dependency"}
        for index in range(len(all_nodes) - 1)
    ]
    return {
        "record_type": FACTORY_RUN_GRAPH_RECORD_TYPE,
        "graph_id": graph_id,
        "run_id": run_id,
        "runtime_shape": FACTORY_RUN_GRAPH_RUNTIME_SHAPE,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "operating_mantra": FACTORY_RUNTIME_MANTRA,
        "route_authority": "factory_run_graph_and_phase_engine",
        "agent_may_choose_phase": False,
        "no_idle_role": FACTORY_RUN_GRAPH_NO_IDLE_ROLE,
        "watchdog_role": "guardrail_not_primary_scheduler",
        "operator_language": operator_language,
        "operator_language_policy": language_policy,
        "start_request_ref": start_request_ref,
        "source_envelope_ref": source_envelope_ref or start_request.get("source_envelope_ref"),
        "nodes": all_nodes,
        "edges": edges,
    }


def factory_run_graph_node_body(
    *,
    graph: dict[str, Any],
    node: dict[str, Any],
    parent_node_id: str,
) -> str:
    body = {
        "task_type": FACTORY_RUN_GRAPH_NODE_PACKET_TYPE,
        "packet_type": FACTORY_RUN_GRAPH_NODE_PACKET_TYPE,
        "graph_id": graph["graph_id"],
        "run_id": graph["run_id"],
        "node_id": node["node_id"],
        "phase_id": node["phase_id"],
        "current_step_key": node["step_key"],
        "node_kind": node.get("node_kind", "backbone"),
        "required_output": node["required_output"],
        "activation_rule": node["activation_rule"],
        "parent_node_id": parent_node_id,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "route_authority": graph["route_authority"],
        "agent_may_choose_phase": False,
        "dependency_mechanism": "hermes_task_links_parent_child",
        "dependency_semantics": "native Hermes todo dependency wait; dispatcher promotes to ready when parent is done; never page human",
        "no_idle_role": graph["no_idle_role"],
        "operating_mantra": graph["operating_mantra"],
        "operator_language": graph.get("operator_language", DEFAULT_OPERATOR_LANGUAGE),
        "operator_language_policy": graph.get(
            "operator_language_policy",
            operator_language_policy(DEFAULT_OPERATOR_LANGUAGE),
        ),
    }
    if node.get("node_kind") == "bounded_expander":
        body["expander_policy"] = {
            "may_create_child_cards": True,
            "child_cards_require_parent_edges": True,
            "child_cards_must_have_ready_work_unit_packets": True,
            "human_gate_required_for_expansion": False,
        }
    return compact_json_argument(body)


def materialize_factory_run_graph(
    *,
    hermes_bin: str,
    board: str,
    graph: dict[str, Any],
    root_task_id: str,
    workspace: str,
    runner: Runner = default_runner,
) -> dict[str, str]:
    task_ids: dict[str, str] = {"F1-intake": root_task_id}
    previous_node_id = "F1-intake"
    previous_task_id = root_task_id
    for node in graph["nodes"][1:]:
        node_id = str(node["node_id"])
        body = factory_run_graph_node_body(graph=graph, node=node, parent_node_id=previous_node_id)
        task_id = create_native_dependency_wait_task(
            hermes_bin=hermes_bin,
            board=board,
            title=str(node["title"]),
            body=body,
            assignee=str(node["assignee"]),
            idempotency_key=(
                f"overkill:factory-run-graph:{bridge_start_board_slug(str(graph['run_id']))}:"
                f"{node_id}:{idempotency_digest_fragment(contract_digest(body))}"
            ),
            created_by="overkill-factory",
            workspace=workspace,
            parent_task_id=previous_task_id,
            workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
            current_step_key=str(node["step_key"]),
            runner=runner,
        )
        task_ids[node_id] = task_id
        previous_node_id = node_id
        previous_task_id = task_id
    return task_ids


def bridge_start_root_body(
    *,
    start_request: dict[str, Any],
    source_envelope: dict[str, Any] | None,
    start_request_ref: str,
    source_envelope_ref: str | None,
    factory_run_graph: dict[str, Any],
) -> str:
    body = {
        "task_type": BRIDGE_START_ROOT_TASK_TYPE,
        "packet_type": BRIDGE_START_ROOT_TASK_TYPE,
        "run_id": start_request["run_id"],
        "project_mode": start_request.get("project_mode"),
        "operator_goal": start_request.get("operator_goal"),
        "factory_bridge_start_request_ref": start_request_ref,
        "factory_bridge_source_envelope_ref": source_envelope_ref or start_request.get("source_envelope_ref"),
        "factory_bridge_start_request": start_request,
        "source_envelope": source_envelope,
        "factory_run_graph": factory_run_graph,
        "operator_language": factory_run_graph.get("operator_language", DEFAULT_OPERATOR_LANGUAGE),
        "operator_language_policy": factory_run_graph.get(
            "operator_language_policy",
            operator_language_policy(DEFAULT_OPERATOR_LANGUAGE),
        ),
        "runtime_boundary": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "materialized_by": "overkill_factory_hermes_live_adapter",
            "bridge_authority_preserved": True,
        },
        "bridge_boundary": {
            "bridge_created_hermes_board": False,
            "bridge_created_hermes_cards": False,
            "bridge_dispatched_workers": False,
            "factory_start_path_created_runtime_state": True,
        },
        "initial_gate": {
            "status": "blocked_then_released_by_default",
            "block_event_required_before_release": True,
            "release_after_start_validation": True,
            "dispatch_factory_orchestrator_by_default": True,
            "human_gate_required_for_normal_start": False,
            "dispatch_allowed_without_source_resolution": False,
            "complete_product_claim_allowed": False,
        },
        "current_step_key": FACTORY_KANBAN_DEFAULT_STEP_KEY,
        "kanban_workflow_binding": {
            "workflow_template_id": FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
            "current_step_key": FACTORY_KANBAN_DEFAULT_STEP_KEY,
            "runtime_field_required": True,
            "fallback_body_binding": True,
            "route_authority": "factory_run_graph_and_phase_engine",
        },
        "deterministic_phase_contract": {
            "route_authority": "factory_run_graph_and_phase_engine",
            "agent_may_choose_phase": False,
            "initial_phase_id": "F1",
            "initial_frontier": "intake",
            "initial_required_artifact": "universal_signal_intake",
            "promotion_rule": "materialize the next required artifact computed by the phase engine; do not promote from prose, memory, card title or declared phase alone",
            "human_gate_rule": "human gate is allowed only when the phase engine says human_gate_allowed=true and a full decision package has been delivered first",
        },
        "no_idle_contract": {
            "role": FACTORY_RUN_GRAPH_NO_IDLE_ROLE,
            "normal_route_authority": "factory_run_graph_and_phase_engine",
            "may_invent_next_phase": False,
            "may_repair_missing_or_stale_graph": True,
        },
        "next_factory_actions": [
            "compute deterministic phase engine state from materialized artifacts",
            "read sealed source envelope only as source input",
            "materialize the current frontier artifact before moving to the next frontier",
            "prepare Product SOT candidate only after source and understanding artifacts allow it",
            "ask the human only for explicit phase-engine-allowed gates",
        ],
    }
    return compact_json_argument(body)


def materialize_bridge_start(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    start_path = args.start_request.resolve()
    source_path = args.source_envelope.resolve() if args.source_envelope else None
    start_request = load_bridge_start_request(start_path)
    source_envelope = load_optional_source_envelope(source_path)
    run_id = str(start_request["run_id"])
    project_mode = str(start_request.get("project_mode") or "").strip()
    board = str(args.board or bridge_start_board_slug(run_id)).strip()
    if not board:
        raise RuntimeError("bridge start materialization requires a board")
    if project_mode == "new_project" and board in BRIDGE_START_FORBIDDEN_BOARD_SLUGS:
        raise RuntimeError("new_project bridge start must materialize into a fresh non-default board")
    if project_mode == "new_project" and args.no_ensure_board and not args.dry_run:
        raise RuntimeError("new_project bridge start must ensure a fresh Hermes board; --no-ensure-board is diagnostic only")
    if project_mode == "existing_project" and not args.board:
        raise RuntimeError("existing_project bridge start requires an explicit --board")
    hold_start = bool(getattr(args, "hold_start", False))
    no_dispatch = bool(getattr(args, "no_dispatch", False))

    start_request_ref = public_safe_workspace_ref(str(start_path))
    source_envelope_ref = public_safe_workspace_ref(str(source_path)) if source_path else None
    factory_run_graph = build_factory_run_graph(
        start_request=start_request,
        source_envelope=source_envelope,
        start_request_ref=start_request_ref,
        source_envelope_ref=source_envelope_ref,
    )
    body = bridge_start_root_body(
        start_request=start_request,
        source_envelope=source_envelope,
        start_request_ref=start_request_ref,
        source_envelope_ref=source_envelope_ref,
        factory_run_graph=factory_run_graph,
    )
    idempotency_key = f"overkill:bridge-start:{bridge_start_board_slug(run_id)}:{idempotency_digest_fragment(contract_digest(start_request))}"
    title = str(args.title or factory_start_title(run_id, str(factory_run_graph.get("operator_language") or DEFAULT_OPERATOR_LANGUAGE))).strip()
    board_created = False
    main_task_id: str | None = None
    factory_run_graph_task_ids: dict[str, str] = {}
    start_released = False
    dispatch_requested = False
    dispatch_result: dict[str, Any] | None = None
    if not args.dry_run:
        if not args.no_ensure_board:
            board_created = ensure_board(
                hermes_bin=args.hermes_bin,
                board=board,
                default_workdir=args.default_workdir,
                name=str(args.board_name or title),
                description="Factory start board materialized from a factory_bridge_start_request.",
                icon="F",
                color="#047857",
                runner=runner,
            )
        main_task_id = create_blocked_task_before_assignment(
            hermes_bin=args.hermes_bin,
            board=board,
            title=title,
            body=body,
            assignee=args.assignee,
            idempotency_key=idempotency_key,
            created_by="overkill-factory",
            workspace=args.workspace,
            blocked_reason=BRIDGE_START_BLOCK_REASON,
            workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
            current_step_key=FACTORY_KANBAN_DEFAULT_STEP_KEY,
            runner=runner,
        )
        factory_run_graph_task_ids = materialize_factory_run_graph(
            hermes_bin=args.hermes_bin,
            board=board,
            graph=factory_run_graph,
            root_task_id=main_task_id,
            workspace=args.workspace,
            runner=runner,
        )
        if not hold_start:
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task_id=main_task_id,
                reason=BRIDGE_START_RELEASE_REASON,
                required_readback_markers=BRIDGE_START_RELEASE_READBACK_MARKERS,
                runner=runner,
            )
            start_released = True
            if not no_dispatch:
                dispatch_args = argparse.Namespace(
                    board=board,
                    hermes_bin=args.hermes_bin,
                    dry_run=False,
                    max=1,
                    failure_limit=None,
                    out=None,
                )
                dispatch_result = dispatch(dispatch_args, runner=runner)
                dispatch_requested = True

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "materialize-bridge-start",
        "dry_run": bool(args.dry_run),
        "board": board,
        "board_created": board_created,
        "main_task_id": main_task_id,
        "worker_task_ids": {},
        "factory_run_graph": factory_run_graph,
        "factory_run_graph_task_ids": factory_run_graph_task_ids,
        "bridge_start": {
            "run_id": run_id,
            "project_mode": project_mode,
            "start_request_ref": start_request_ref,
            "source_envelope_ref": source_envelope_ref,
            "target_assignee": args.assignee,
            "idempotency_key": idempotency_key,
        },
        "runtime_gate": {
            "initial_status": "blocked_then_released" if start_released else "blocked",
            "blocked_event_verified": main_task_id is not None and not args.dry_run,
            "start_release_verified": start_released,
            "hold_start": hold_start,
            "dispatch_requested": dispatch_requested,
            "dispatch_allowed_without_runtime_gate": False,
            "complete_product_claim_allowed": False,
            "bridge_mutated_hermes": False,
            "factory_start_path_mutated_hermes": not args.dry_run,
            "factory_run_graph_materialized": bool(factory_run_graph_task_ids) or bool(args.dry_run),
            "factory_run_graph_future_cards_native_dependency_wait": True,
            "factory_run_graph_dependency_mechanism": "hermes_create_parent_task_links",
        },
        "start_release": {
            "held": hold_start,
            "released": start_released,
            "no_dispatch": no_dispatch,
            "dispatch_requested": dispatch_requested,
            "dispatch_max": 1 if dispatch_requested else 0,
            "release_reason": BRIDGE_START_RELEASE_REASON,
            "dispatch_result": dispatch_result,
        },
        "hook": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "factory_start_path": True,
            "bridge_boundary_preserved": True,
            "next_action": (
                "factory-orchestrator dispatched for source resolution from the sealed source envelope"
                if dispatch_requested
                else "factory-orchestrator awaits dispatch for source resolution from the sealed source envelope"
            ),
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def ready_work_unit_create_body_and_chunks(body_contract: dict[str, Any]) -> tuple[str, list[str]]:
    full_body = compact_json_argument(body_contract)
    if len(full_body) <= READY_WORK_UNIT_DIRECT_BODY_LIMIT:
        return full_body, []

    digest = hashlib.sha256(full_body.encode("utf-8")).hexdigest()
    chunks = [
        full_body[index : index + READY_WORK_UNIT_CONTEXT_CHUNK_SIZE]
        for index in range(0, len(full_body), READY_WORK_UNIT_CONTEXT_CHUNK_SIZE)
    ]
    manifest = {
        "packet_id": body_contract.get("packet_id"),
        "packet_type": body_contract.get("packet_type"),
        "work_unit_id": body_contract.get("work_unit_id"),
        "context_transport": {
            "mode": READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE,
            "author": READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR,
            "encoding": "utf-8-json-chunks",
            "chunk_count": len(chunks),
            "sha256": digest,
            "payload_type": "ready_work_unit_execution_request",
            "instruction": (
                "Reconstruct the full ready work-unit packet from durable Hermes comments "
                "before execution; block if chunks are missing or digest mismatches."
            ),
        },
    }
    comment_bodies = [
        compact_json_argument(
            {
                "context_transport": READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE,
                "packet_id": body_contract.get("packet_id"),
                "work_unit_id": body_contract.get("work_unit_id"),
                "chunk_index": index,
                "chunk_count": len(chunks),
                "sha256": digest,
                "data": chunk,
            }
        )
        for index, chunk in enumerate(chunks)
    ]
    return compact_json_argument(manifest), comment_bodies


def post_ready_work_unit_context_chunks(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    chunks: list[str],
    runner: Runner = default_runner,
) -> None:
    for chunk in chunks:
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "comment",
                "--author",
                READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR,
                task_id,
                chunk,
            ),
            runner,
        )


def load_ready_work_unit_materialization_plan(path: Path) -> dict[str, Any]:
    plan = load_json(path)
    factoryctl = load_factoryctl()
    errors = factoryctl.validate_ready_work_unit_hermes_materialization_plan(plan)
    if errors:
        raise RuntimeError("invalid ready work-unit Hermes materialization plan: " + "; ".join(errors))
    return plan


def load_product_creation_plan(path: Path) -> dict[str, Any]:
    plan = load_json(path)
    factoryctl = load_factoryctl()
    errors = factoryctl.validate_product_creation_plan(plan)
    if errors:
        raise RuntimeError("invalid product creation plan: " + "; ".join(errors))
    return plan


def ensure_public_safe_optional_ref(value: str | None, *, field: str) -> str | None:
    ref = str(value or "").strip()
    if not ref:
        return None
    factoryctl = load_factoryctl()
    _sanitized, redaction = factoryctl.sanitize_public_ref(ref)
    if redaction is not None:
        raise RuntimeError(f"{field} must be public-safe")
    return ref


def create_ready_work_unit_task(
    *,
    hermes_bin: str,
    board: str,
    task: dict[str, Any],
    worker_assignee_prefix: str,
    workspace_ref: str,
    runner: Runner = default_runner,
) -> str:
    create_policy = task.get("create_policy") if isinstance(task.get("create_policy"), dict) else {}
    block_policy = task.get("block_policy") if isinstance(task.get("block_policy"), dict) else {}
    if create_policy.get("create_with_assignee") is not False:
        raise RuntimeError("ready work-unit task create_policy must create without assignee before the blocked event")
    if create_policy.get("assign_after_block_event_verified") is not True:
        raise RuntimeError("ready work-unit task create_policy must assign only after the blocked event is verified")
    if create_policy.get("no_spawn_protocol") != "create-unassigned-default-block-assign-v2":
        raise RuntimeError("ready work-unit task create_policy must use the no-spawn create-unassigned-block-assign protocol")
    if block_policy.get("block_event_required_before_dispatch") is not True:
        raise RuntimeError("ready work-unit task must require a blocked event before dispatch")
    if block_policy.get("final_status_required") != "blocked":
        raise RuntimeError("ready work-unit task must require final blocked status before dispatch")

    body_contract = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
    create_body, context_chunks = ready_work_unit_create_body_and_chunks(body_contract)
    ensure_non_empty_body(create_body)
    target_assignee = str(create_policy.get("target_assignee_profile") or task.get("owner_worker") or "").strip()
    if not target_assignee:
        raise RuntimeError("ready work-unit task requires target_assignee_profile")
    task_id = parse_task_id(
        run_checked(
            hermes_kanban(
                hermes_bin,
                board,
                "create",
                str(task.get("title") or f"OF ready work unit {task.get('work_unit_id') or 'work-unit'}"),
                "--body",
                create_body,
                "--idempotency-key",
                str(task.get("idempotency_key") or ""),
                "--created-by",
                "overkill-factory",
                "--workspace",
                workspace_ref,
                "--json",
            ),
            runner,
        ).stdout
    )
    apply_native_workflow_state(
        board=board,
        task_id=task_id,
        workflow_template_id=str(task.get("workflow_template_id") or FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID),
        current_step_key=str(task.get("current_step_key") or "F15-runtime-execution"),
    )
    ensure_blocked_event(
        hermes_bin=hermes_bin,
        board=board,
        task_id=task_id,
        reason=str(
            block_policy.get("blocked_reason")
            or "Overkill Factory ready work-unit runtime gate starts blocked until evidence passes."
        ),
        kind=str(block_policy.get("block_kind") or DEFAULT_RUNTIME_GATE_BLOCK_KIND),
        runner=runner,
    )
    post_ready_work_unit_context_chunks(
        hermes_bin=hermes_bin,
        board=board,
        task_id=task_id,
        chunks=context_chunks,
        runner=runner,
    )
    blocked_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    ensure_no_pre_dispatch_activity(blocked_task, task_id=task_id)
    if not task_has_blocked_event(blocked_task):
        raise RuntimeError(f"Hermes task {task_id} lacks verified blocked event after materialization")
    if task_readback_status(blocked_task) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked before assignment")
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "assign",
            task_id,
            worker_assignee_prefix + target_assignee,
        ),
        runner,
    )
    final_task = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    try:
        ensure_ready_work_unit_readback_contract(
            payload=final_task,
            task_id=task_id,
            expected_assignee=worker_assignee_prefix + target_assignee,
            expected_packet_id=str(task.get("packet_id") or "").strip(),
        )
    except RuntimeError:
        if task_readback_status(final_task) != "blocked":
            ensure_blocked_event(
                hermes_bin=hermes_bin,
                board=board,
                task_id=task_id,
                reason="Ready work-unit assignment triggered unsafe non-blocked state; re-blocking before failing closed.",
                kind=DEFAULT_RUNTIME_GATE_BLOCK_KIND,
                runner=runner,
            )
        raise
    return task_id


def phase_id_from_step_key(step_key: Any) -> str:
    text = str(step_key or "").strip()
    if not text or "-" not in text:
        return text
    return text.split("-", 1)[0]


def next_backbone_phase_id(phase_id: str) -> str | None:
    phase_ids = [str(node.get("phase_id") or "").strip() for node in FACTORY_RUN_GRAPH_BACKBONE]
    phase_ids = [item for item in phase_ids if item]
    try:
        index = phase_ids.index(str(phase_id or "").strip())
    except ValueError:
        return None
    if index + 1 >= len(phase_ids):
        return None
    return phase_ids[index + 1]


def find_factory_run_graph_phase_task(
    *,
    hermes_bin: str,
    board: str,
    phase_id: str,
    runner: Runner = default_runner,
) -> tuple[str, str] | None:
    target_phase_id = str(phase_id or "").strip()
    if not target_phase_id:
        return None
    for status in ("todo", "ready", "blocked", "running", "done"):
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id:
                continue
            body = task_body_json_object(record)
            payload: dict[str, Any] | None = None
            if body.get("packet_type") != FACTORY_RUN_GRAPH_NODE_PACKET_TYPE:
                payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
                body = parse_json_object(task_readback_body(payload))
            if body.get("packet_type") != FACTORY_RUN_GRAPH_NODE_PACKET_TYPE:
                continue
            if str(body.get("phase_id") or "").strip() != target_phase_id:
                continue
            if payload is None:
                payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            return task_id, task_readback_status(payload) or status
    return None


def link_ready_work_units_to_next_phase_closure(
    *,
    hermes_bin: str,
    board: str,
    plan_tasks: list[dict[str, Any]],
    ready_work_unit_task_ids: dict[str, str],
    runner: Runner = default_runner,
) -> dict[str, Any]:
    phase_parent_task_ids: dict[str, list[str]] = {}
    for task in plan_tasks:
        work_unit_id = str(task.get("work_unit_id") or "").strip()
        task_id = ready_work_unit_task_ids.get(work_unit_id)
        if not work_unit_id or not task_id:
            continue
        phase_id = phase_id_from_step_key(task.get("current_step_key"))
        next_phase_id = next_backbone_phase_id(phase_id)
        if not next_phase_id:
            continue
        phase_parent_task_ids.setdefault(next_phase_id, []).append(task_id)

    linked: dict[str, list[str]] = {}
    skipped: dict[str, str] = {}
    for next_phase_id, parent_task_ids in sorted(phase_parent_task_ids.items()):
        next_phase_task = find_factory_run_graph_phase_task(
            hermes_bin=hermes_bin,
            board=board,
            phase_id=next_phase_id,
            runner=runner,
        )
        if next_phase_task is None:
            skipped[next_phase_id] = "next phase backbone card not present on this board"
            continue
        next_phase_task_id, next_phase_status = next_phase_task
        if next_phase_status != "todo":
            raise RuntimeError(
                f"next phase {next_phase_id} is already {next_phase_status}; cannot attach newly materialized work-unit closure dependencies"
            )
        next_phase_payload = show_task(
            hermes_bin=hermes_bin,
            board=board,
            task_id=next_phase_task_id,
            runner=runner,
        )
        existing_parents = set(task_readback_parents(next_phase_payload))
        for parent_task_id in parent_task_ids:
            if parent_task_id in existing_parents:
                continue
            link_task_dependency(
                hermes_bin=hermes_bin,
                board=board,
                parent_task_id=parent_task_id,
                child_task_id=next_phase_task_id,
                runner=runner,
            )
            linked.setdefault(next_phase_id, []).append(parent_task_id)
    return {
        "strategy": "native_hermes_phase_closure_dependencies",
        "linked_parent_task_ids_by_next_phase": linked,
        "skipped_next_phase_ids": skipped,
    }


def materialize_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit materialization requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")

    if args.dry_run:
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "materialize-ready-work-units",
            "dry_run": True,
            "board": board,
            "board_created": False,
            "board_create_requested": bool(args.ensure_board),
            "board_create_checked": False,
            "materialization_plan_id": plan.get("plan_id"),
            "ready_work_unit_task_ids": {},
            "packet_task_ids": {},
            "runtime_gate": plan.get("runtime_gate", {}),
            "hook": {"plan": plan},
        }
        if args.out:
            write_json(args.out, envelope)
        return envelope

    required_workers = [
        str(task.get("owner_worker") or "").strip()
        for task in plan.get("tasks", [])
        if isinstance(task, dict) and str(task.get("owner_worker") or "").strip()
    ]
    readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
    if readiness_blockers:
        raise RuntimeError("pre-dispatch route readiness blocked ready work-unit materialization: " + "; ".join(readiness_blockers))

    board_created = False
    if args.ensure_board:
        board_created = ensure_board(
            hermes_bin=args.hermes_bin,
            board=board,
            default_workdir=str(ROOT),
            runner=runner,
        )

    ready_work_unit_task_ids: dict[str, str] = {}
    packet_task_ids: dict[str, str] = {}
    plan_tasks = [task for task in plan.get("tasks", []) if isinstance(task, dict)]
    for task in plan_tasks:
        task_id = create_ready_work_unit_task(
            hermes_bin=args.hermes_bin,
            board=board,
            task=task,
            worker_assignee_prefix=args.worker_assignee_prefix,
            workspace_ref=str(args.workspace or f"dir:{ROOT}"),
            runner=runner,
        )
        work_unit_id = str(task.get("work_unit_id") or "").strip()
        packet_id = str(task.get("packet_id") or "").strip()
        if work_unit_id:
            ready_work_unit_task_ids[work_unit_id] = task_id
        if packet_id:
            packet_task_ids[packet_id] = task_id
    phase_closure_links = link_ready_work_units_to_next_phase_closure(
        hermes_bin=args.hermes_bin,
        board=board,
        plan_tasks=plan_tasks,
        ready_work_unit_task_ids=ready_work_unit_task_ids,
        runner=runner,
    )

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "materialize-ready-work-units",
        "dry_run": False,
        "board": board,
        "board_created": board_created,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": ready_work_unit_task_ids,
        "packet_task_ids": packet_task_ids,
        "phase_closure_dependency_links": phase_closure_links,
        "runtime_gate": {
            **(plan.get("runtime_gate") if isinstance(plan.get("runtime_gate"), dict) else {}),
            "blocked_event_verified_task_ids": ready_work_unit_task_ids,
            "phase_closure_dependencies_attached": bool(phase_closure_links["linked_parent_task_ids_by_next_phase"]),
            "dispatch_allowed_by_this_step": False,
            "live_hermes_mutated": True,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
        },
        "hook": {"plan": plan},
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def load_ready_work_unit_materialization_result(path: Path, *, plan: dict[str, Any], board: str) -> dict[str, Any]:
    result = load_json(path)
    if result.get("mode") != "materialize-ready-work-units":
        raise RuntimeError("ready work-unit release requires a materialize-ready-work-units result")
    if result.get("dry_run") is True:
        raise RuntimeError("ready work-unit release requires a real materialization result, not dry-run output")
    result_board = str(result.get("board") or "").strip()
    if result_board and result_board != board:
        raise RuntimeError("materialization result board does not match ready work-unit release board")
    plan_id = str(plan.get("plan_id") or "").strip()
    if plan_id and str(result.get("materialization_plan_id") or "").strip() != plan_id:
        raise RuntimeError("materialization result does not match the ready work-unit materialization plan")
    runtime_gate = result.get("runtime_gate")
    if not isinstance(runtime_gate, dict) or runtime_gate.get("live_hermes_mutated") is not True:
        raise RuntimeError("materialization result does not prove live Hermes materialization")
    if runtime_gate.get("dispatch_allowed_by_this_step") is not False:
        raise RuntimeError("materialization result must keep dispatch separated from materialization")
    work_unit_ids = {
        str(task.get("work_unit_id") or "").strip()
        for task in plan.get("tasks", [])
        if isinstance(task, dict) and str(task.get("work_unit_id") or "").strip()
    }
    packet_ids = {
        str(task.get("packet_id") or "").strip()
        for task in plan.get("tasks", [])
        if isinstance(task, dict) and str(task.get("packet_id") or "").strip()
    }
    result_work_units = set((result.get("ready_work_unit_task_ids") or {}).keys())
    result_packets = set((result.get("packet_task_ids") or {}).keys())
    missing_work_units = sorted(work_unit_ids - result_work_units)
    missing_packets = sorted(packet_ids - result_packets)
    if missing_work_units:
        raise RuntimeError("materialization result is missing work unit ids: " + ", ".join(missing_work_units))
    if missing_packets:
        raise RuntimeError("materialization result is missing packet ids: " + ", ".join(missing_packets))
    return result


def expected_ready_work_unit_tasks(plan: dict[str, Any]) -> list[dict[str, Any]]:
    tasks = [task for task in plan.get("tasks", []) if isinstance(task, dict)]
    if not tasks:
        raise RuntimeError("ready work-unit release requires at least one task in the plan")
    return tasks


def expected_ready_work_unit_key(task: dict[str, Any]) -> tuple[str, str]:
    packet_id = str(task.get("packet_id") or "").strip()
    work_unit_id = str(task.get("work_unit_id") or "").strip()
    if not packet_id or not work_unit_id:
        raise RuntimeError("ready work-unit release requires packet_id and work_unit_id for every plan task")
    return packet_id, work_unit_id


def ready_work_unit_release_assignee(task: dict[str, Any], worker_assignee_prefix: str) -> str:
    create_policy = task.get("create_policy") if isinstance(task.get("create_policy"), dict) else {}
    assignee = str(create_policy.get("target_assignee_profile") or task.get("owner_worker") or "").strip()
    if not assignee:
        raise RuntimeError("ready work-unit release requires target_assignee_profile")
    return worker_assignee_prefix + assignee


def verify_ready_work_unit_release_candidate(
    *,
    payload: dict[str, Any],
    plan_task: dict[str, Any],
    worker_assignee_prefix: str,
) -> tuple[str, str, str]:
    task_id = task_readback_id(payload)
    if not task_id:
        raise RuntimeError("Hermes task readback has no task id")
    packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
    expected_assignee = ready_work_unit_release_assignee(plan_task, worker_assignee_prefix)
    if task_readback_status(payload) != "blocked":
        raise RuntimeError(f"Hermes task {task_id} is not blocked before ready work-unit release")
    if task_readback_assignee(payload) != expected_assignee:
        raise RuntimeError(f"Hermes task {task_id} assignee readback does not match target profile")
    body = ready_work_unit_body(payload, task_id=task_id)
    if str(body.get("packet_id") or "").strip() != packet_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit packet")
    if str(body.get("work_unit_id") or "").strip() != work_unit_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit id")
    if str(body.get("packet_type") or "").strip() != "ready_work_unit_execution_request":
        raise RuntimeError(f"Hermes task {task_id} body readback is not a ready work-unit execution request")
    if not task_has_blocked_event(payload):
        raise RuntimeError(f"Hermes task {task_id} lacks verified blocked event before release")
    ensure_no_pre_dispatch_activity(payload, task_id=task_id)
    ensure_dispatcher_visible_workspace(payload, task_id=task_id)
    return task_id, packet_id, work_unit_id


def verify_ready_work_unit_identity(
    *,
    payload: dict[str, Any],
    plan_task: dict[str, Any],
    worker_assignee_prefix: str,
) -> tuple[str, str, str]:
    task_id = task_readback_id(payload)
    if not task_id:
        raise RuntimeError("Hermes task readback has no task id")
    packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
    expected_assignee = ready_work_unit_release_assignee(plan_task, worker_assignee_prefix)
    if task_readback_assignee(payload) != expected_assignee:
        raise RuntimeError(f"Hermes task {task_id} assignee readback does not match target profile")
    body = ready_work_unit_body(payload, task_id=task_id)
    if str(body.get("packet_id") or "").strip() != packet_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit packet")
    if str(body.get("work_unit_id") or "").strip() != work_unit_id:
        raise RuntimeError(f"Hermes task {task_id} body readback does not match ready work-unit id")
    if str(body.get("packet_type") or "").strip() != "ready_work_unit_execution_request":
        raise RuntimeError(f"Hermes task {task_id} body readback is not a ready work-unit execution request")
    return task_id, packet_id, work_unit_id


def ready_work_unit_dependencies(tasks: list[dict[str, Any]]) -> dict[str, list[str]]:
    work_unit_ids = {
        str(task.get("work_unit_id") or "").strip()
        for task in tasks
        if str(task.get("work_unit_id") or "").strip()
    }
    dependencies: dict[str, set[str]] = {work_unit_id: set() for work_unit_id in work_unit_ids}
    for task in tasks:
        body = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
        context_packet = body.get("work_unit_context_packet") if isinstance(body.get("work_unit_context_packet"), dict) else {}
        embedded = context_packet.get("embedded_payloads") if isinstance(context_packet.get("embedded_payloads"), dict) else {}
        product_plan = embedded.get("product_creation_plan") if isinstance(embedded.get("product_creation_plan"), dict) else {}
        graph = product_plan.get("dependency_graph") if isinstance(product_plan.get("dependency_graph"), list) else []
        for edge in graph:
            if not isinstance(edge, dict):
                continue
            source = str(edge.get("from") or "").strip()
            target = str(edge.get("to") or "").strip()
            if source in work_unit_ids and target in work_unit_ids:
                dependencies.setdefault(target, set()).add(source)
    if any(dependencies.values()):
        return {work_unit_id: sorted(deps) for work_unit_id, deps in sorted(dependencies.items())}

    for task in tasks:
        work_unit_id = str(task.get("work_unit_id") or "").strip()
        body = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
        refs = body.get("dependency_refs") if isinstance(body.get("dependency_refs"), list) else []
        for ref in refs:
            dep = str(ref or "").strip()
            if dep in work_unit_ids and dep != work_unit_id:
                dependencies.setdefault(work_unit_id, set()).add(dep)
    return {work_unit_id: sorted(deps) for work_unit_id, deps in sorted(dependencies.items())}


def ready_work_unit_readbacks_by_status(
    *,
    hermes_bin: str,
    board: str,
    statuses: list[str],
    include_superseded: bool = False,
    runner: Runner = default_runner,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    candidates: dict[tuple[str, str], list[dict[str, Any]]] = {}
    seen_task_ids: set[str] = set()
    for status in statuses:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            try:
                body = ready_work_unit_body(payload, task_id=task_id)
            except RuntimeError:
                continue
            if not include_superseded and task_has_ready_work_unit_supersession(payload):
                continue
            if str(body.get("packet_type") or "").strip() != "ready_work_unit_execution_request":
                continue
            packet_id = str(body.get("packet_id") or "").strip()
            work_unit_id = str(body.get("work_unit_id") or "").strip()
            if packet_id and work_unit_id:
                candidates.setdefault((packet_id, work_unit_id), []).append(payload)
    return candidates


def release_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit release requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=plan,
        board=board,
    )
    tasks = expected_ready_work_unit_tasks(plan)
    required_workers = [
        ready_work_unit_release_assignee(task, args.worker_assignee_prefix)
        for task in tasks
    ]
    readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
    if readiness_blockers:
        raise RuntimeError("pre-dispatch route readiness blocked ready work-unit release: " + "; ".join(readiness_blockers))

    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=READY_WORK_UNIT_RELEASE_QUERY_STATUSES,
        runner=runner,
    )
    verified: list[tuple[dict[str, Any], str, str, str, str]] = []
    post_release_blocked: dict[str, str] = {}
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        if len(matches) != 1:
            raise RuntimeError(
                f"ready work-unit release expected exactly one blocked or completed Hermes task for packet {key[0]} / work unit {key[1]}, found {len(matches)}"
            )
        status = task_readback_status(matches[0])
        if status == "blocked":
            if task_has_ready_work_unit_release_record(matches[0]):
                task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
                    payload=matches[0],
                    plan_task=task,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                )
                if not task_has_blocked_event(matches[0]):
                    raise RuntimeError(f"Hermes task {task_id} is post-release blocked but lacks a blocked event")
                status = "blocked_after_release"
                post_release_blocked[work_unit_id] = task_id
            else:
                task_id, packet_id, work_unit_id = verify_ready_work_unit_release_candidate(
                    payload=matches[0],
                    plan_task=task,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                )
        elif status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
            task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
                payload=matches[0],
                plan_task=task,
                worker_assignee_prefix=args.worker_assignee_prefix,
            )
        elif status in {"ready", "running"}:
            task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
                payload=matches[0],
                plan_task=task,
                worker_assignee_prefix=args.worker_assignee_prefix,
            )
        else:
            raise RuntimeError(f"Hermes task for ready work unit {key[1]} is not releasable or satisfied: {status}")
        verified.append((task, task_id, packet_id, work_unit_id, status))

    dependencies = ready_work_unit_dependencies(tasks)
    status_by_work_unit = {work_unit_id: status for _task, _task_id, _packet_id, work_unit_id, status in verified}
    satisfied_work_unit_ids = sorted(
        work_unit_id
        for work_unit_id, status in status_by_work_unit.items()
        if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
    )
    dependency_blockers: dict[str, list[str]] = {}
    eligible: list[tuple[dict[str, Any], str, str, str, str]] = []
    for item in verified:
        _task, _task_id, _packet_id, work_unit_id, status = item
        if status != "blocked":
            continue
        blockers = [
            dep
            for dep in dependencies.get(work_unit_id, [])
            if status_by_work_unit.get(dep) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
        ]
        if blockers:
            dependency_blockers[work_unit_id] = blockers
            continue
        eligible.append(item)

    released_ready_work_unit_task_ids: dict[str, str] = {}
    released_packet_task_ids: dict[str, str] = {}
    release_reason = str(
        args.reason
        or "runtime_gate=blocked_event_verified_for_each_task; release_scope=ready_work_units_only; dispatch_separate=true"
    )
    required_markers = READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS
    if not args.dry_run:
        for _task, task_id, packet_id, work_unit_id, _status in eligible:
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task_id=task_id,
                reason=release_reason,
                required_readback_markers=required_markers,
                runner=runner,
            )
            released_ready_work_unit_task_ids[work_unit_id] = task_id
            released_packet_task_ids[packet_id] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "release-ready-work-units",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": {
            work_unit_id: task_id
            for _task, task_id, _packet_id, work_unit_id, _status in verified
        },
        "packet_task_ids": {
            packet_id: task_id
            for _task, task_id, packet_id, _work_unit_id, _status in verified
        },
        "released_ready_work_unit_task_ids": released_ready_work_unit_task_ids,
        "released_packet_task_ids": released_packet_task_ids,
        "release_wave": {
            "eligible_work_unit_ids": sorted(work_unit_id for _task, _task_id, _packet_id, work_unit_id, _status in eligible),
            "held_work_unit_ids": sorted(dependency_blockers.keys()),
            "satisfied_work_unit_ids": satisfied_work_unit_ids,
            "post_release_blocked_work_unit_ids": sorted(post_release_blocked.keys()),
            "post_release_reconciliation_required_next": bool(post_release_blocked),
            "post_release_reconciliation_command": "reconcile-ready-work-units",
            "dependency_blockers": {key: dependency_blockers[key] for key in sorted(dependency_blockers)},
        },
        "runtime_gate": {
            **(plan.get("runtime_gate") if isinstance(plan.get("runtime_gate"), dict) else {}),
            "release_verified_task_count": len(verified),
            "release_eligible_task_count": len(eligible),
            "release_held_task_count": len(dependency_blockers) + len(post_release_blocked),
            "release_satisfied_task_count": len(satisfied_work_unit_ids),
            "post_release_blocked_task_count": len(post_release_blocked),
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": bool(released_ready_work_unit_task_ids),
            "complete_product_claim_allowed": False,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "release_reason": release_reason,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def ready_work_unit_reviewer_role(plan_task: dict[str, Any]) -> str:
    body_contract = plan_task.get("body_contract") if isinstance(plan_task.get("body_contract"), dict) else {}
    done_definition = body_contract.get("done_definition") if isinstance(body_contract.get("done_definition"), dict) else {}
    context_packet = body_contract.get("work_unit_context_packet")
    context_packet = context_packet if isinstance(context_packet, dict) else {}
    embedded_payloads = context_packet.get("embedded_payloads")
    embedded_payloads = embedded_payloads if isinstance(embedded_payloads, dict) else {}
    current_work_unit = embedded_payloads.get("current_work_unit")
    current_work_unit = current_work_unit if isinstance(current_work_unit, dict) else {}
    current_done_definition = (
        current_work_unit.get("done_definition")
        if isinstance(current_work_unit.get("done_definition"), dict)
        else {}
    )

    for source in (done_definition, body_contract, current_done_definition, current_work_unit, plan_task):
        role = str(source.get("reviewer_role") or "").strip() if isinstance(source, dict) else ""
        if role:
            return role
    return "independent-reviewer"


def ready_work_unit_reviewer_assignee(plan_task: dict[str, Any], worker_assignee_prefix: str) -> str:
    return worker_assignee_prefix + ready_work_unit_reviewer_role(plan_task)


def ready_work_unit_inferred_repair_completed(payload: dict[str, Any]) -> bool:
    text = " ".join(
        part
        for part in (
            task_record_text(payload),
            task_record_text(task_readback_task(payload)),
        )
        if part
    )
    if not any(marker in text for marker in READY_WORK_UNIT_REPAIR_COMPLETED_INFERRED_MARKERS):
        return False
    if not any(signal in text for signal in ("receipt", "evidence", "artifact", "proof", "implemented", "completed", "pass")):
        return False
    if any(marker in text for marker in READY_WORK_UNIT_HUMAN_GATE_MARKERS):
        return False
    return True


def ready_work_unit_post_release_reconciliation_flags(payload: dict[str, Any]) -> dict[str, bool]:
    explicit_repair_completed = history_contains_any_marker(payload, READY_WORK_UNIT_REPAIR_COMPLETED_MARKERS)
    inferred_repair_completed = ready_work_unit_inferred_repair_completed(payload)
    repair_completed = explicit_repair_completed or inferred_repair_completed
    repair_review_passed = history_contains_all_markers_anywhere(payload, READY_WORK_UNIT_REPAIR_REVIEW_PASSED_MARKERS)
    retry_authorized = history_contains_all_markers_anywhere(payload, READY_WORK_UNIT_RETRY_AUTHORIZED_MARKERS)
    done_authorized = history_contains_all_markers_anywhere(payload, READY_WORK_UNIT_DONE_AUTHORIZED_MARKERS)
    done_definition_satisfied = history_contains_all_markers_anywhere(
        payload,
        READY_WORK_UNIT_DONE_DEFINITION_SATISFIED_MARKERS,
    )
    human_gate_required = history_contains_any_marker(payload, READY_WORK_UNIT_HUMAN_GATE_MARKERS)
    return {
        "repair_completed": repair_completed,
        "repair_completed_explicit": explicit_repair_completed,
        "repair_completed_inferred_from_review_required": inferred_repair_completed,
        "repair_review_passed": repair_review_passed,
        "retry_authorized": retry_authorized,
        "done_authorized": done_authorized,
        "done_definition_satisfied": done_definition_satisfied,
        "human_gate_required": human_gate_required,
    }


def classify_ready_work_unit_post_release_reconciliation(payload: dict[str, Any]) -> dict[str, Any]:
    status = task_readback_status(payload)
    release_record_seen = task_has_ready_work_unit_release_record(payload)
    flags = ready_work_unit_post_release_reconciliation_flags(payload)
    decision = "not_post_release_blocked"
    next_action = "release-ready-work-units must release the ready work unit before post-release reconciliation"
    actionable = False

    if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        decision = "already_satisfied"
        next_action = "no reconciliation needed"
    elif status != "blocked":
        decision = "wait_for_runtime_state"
        next_action = f"task is {status or 'unknown'}, not blocked"
    elif not release_record_seen:
        decision = "not_released_yet"
        next_action = "run release-ready-work-units when dependency blockers are satisfied"
    elif not task_has_blocked_event(payload):
        decision = "invalid_blocked_readback"
        next_action = "preserve task and repair missing Hermes blocked-event evidence before retry"
    elif flags["human_gate_required"]:
        decision = "human_gate_required"
        next_action = "wait for explicit human gate; no automatic retry or completion"
    elif flags["repair_completed"] and flags["repair_review_passed"] and flags["done_authorized"] and flags["done_definition_satisfied"]:
        decision = "complete_parent"
        next_action = "complete the parent ready work unit through Hermes complete"
        actionable = True
    elif flags["repair_completed"] and flags["repair_review_passed"] and flags["retry_authorized"]:
        decision = "retry_parent"
        next_action = "unblock parent ready work unit for another Hermes worker attempt"
        actionable = True
    elif flags["repair_completed"] and flags["repair_review_passed"]:
        decision = "awaiting_retry_or_done_authority"
        next_action = "repair review passed, but no explicit retry or done authority marker exists"
    elif flags["repair_completed"]:
        decision = "awaiting_repair_review"
        next_action = "repair evidence exists, but independent repair review is not complete"
    else:
        decision = "awaiting_repair"
        next_action = "create or wait for factory repair and independent review evidence"

    return {
        "status": status,
        "release_record_seen": release_record_seen,
        "decision": decision,
        "next_action": next_action,
        "actionable_by_adapter": actionable,
        "complete_product_claim_allowed": False,
        **flags,
    }


def ready_work_unit_post_repair_review_idempotency_key(*, plan_task: dict[str, Any], parent_task_id: str) -> str:
    base = str(plan_task.get("idempotency_key") or "").strip()
    if not base:
        _packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
        base = f"overkill:ready-work-unit:{work_unit_id}"
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "base_idempotency_key": base,
                "parent_task_id": parent_task_id,
                "route": "post_repair_review",
                "version": "v1",
            }
        )
    )
    return f"{base}:post-repair-review:{digest}"


def ready_work_unit_route_repair_scope_contract(plan_task: dict[str, Any]) -> dict[str, Any]:
    body_contract = plan_task.get("body_contract") if isinstance(plan_task.get("body_contract"), dict) else {}
    context_packet = body_contract.get("work_unit_context_packet")
    context_packet = context_packet if isinstance(context_packet, dict) else {}
    embedded_payloads = context_packet.get("embedded_payloads")
    embedded_payloads = embedded_payloads if isinstance(embedded_payloads, dict) else {}
    current_work_unit = embedded_payloads.get("current_work_unit")
    current_work_unit = current_work_unit if isinstance(current_work_unit, dict) else {}

    def first_text(field: str) -> str:
        for source in (body_contract, current_work_unit, plan_task):
            value = source.get(field) if isinstance(source, dict) else None
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def first_list(field: str) -> list[str]:
        for source in (body_contract, current_work_unit, plan_task):
            value = source.get(field) if isinstance(source, dict) else None
            if isinstance(value, list):
                items = [str(item).strip() for item in value if str(item or "").strip()]
                if items:
                    return items
        return []

    runtime_phase = phase_id_from_step_key(first_text("current_step_key"))
    phase = runtime_phase or first_text("phase")
    risk_effective = first_text("risk_effective")
    surfaces = first_list("surfaces")
    missing = [
        field
        for field, present in (
            ("phase", bool(phase)),
            ("risk_effective", bool(risk_effective)),
            ("surfaces", bool(surfaces)),
        )
        if not present
    ]
    return {
        "phase": phase,
        "risk_effective": risk_effective,
        "surfaces": surfaces,
        "route_repair_contract": {
            "required_card_fields": ["phase", "risk_effective", "surfaces"],
            "phase": phase,
            "risk_effective": risk_effective,
            "surfaces": surfaces,
            "source_contract_missing": missing,
            "source_contract_status": "PASS" if not missing else "BLOCK",
            "block_if_missing": True,
            "authority_boundary": "route repair only; no product completion, release, deployment, customer-ready status, security waiver or human gate approval",
        },
    }


def ready_work_unit_post_repair_review_body(
    *,
    plan_task: dict[str, Any],
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
) -> dict[str, Any]:
    done_definition = {}
    body_contract = plan_task.get("body_contract") if isinstance(plan_task.get("body_contract"), dict) else {}
    if isinstance(body_contract.get("done_definition"), dict):
        done_definition = body_contract["done_definition"]
    elif isinstance(body_contract.get("work_unit_context_packet"), dict):
        embedded_payloads = body_contract["work_unit_context_packet"].get("embedded_payloads", {})
        embedded_payloads = embedded_payloads if isinstance(embedded_payloads, dict) else {}
        current = embedded_payloads.get("current_work_unit", {})
        if isinstance(current, dict) and isinstance(current.get("done_definition"), dict):
            done_definition = current["done_definition"]
    return {
        "packet_type": "ready_work_unit_post_repair_review_request",
        "marker": READY_WORK_UNIT_POST_REPAIR_REVIEW_REQUIRED_MARKER,
        "current_step_key": "F18-independent-review",
        "kanban_workflow_binding": {
            "workflow_template_id": FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
            "current_step_key": "F18-independent-review",
            "runtime_field_required": True,
            "fallback_body_binding": True,
            "route_authority": "factory_phase_engine",
        },
        **ready_work_unit_route_repair_scope_contract(plan_task),
        "parent_packet_id": packet_id,
        "parent_work_unit_id": work_unit_id,
        "parent_task_ref": parent_task_id,
        "reviewer_role": ready_work_unit_reviewer_role(plan_task),
        "review_scope": "post_repair_result_only",
        "review_must_not_approve": [
            "complete_product",
            "release",
            "deployment",
            "customer_ready",
            "security_gate",
            "human_gate",
        ],
        "required_positive_outcomes": [
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_retry_authorized",
                ],
                "meaning": "repair is accepted and parent may be retried by Hermes reconciliation",
            },
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_done_authorized",
                    "ready_work_unit_done_definition_satisfied",
                ],
                "meaning": "parent ready work unit may be completed, not the whole product",
            },
            {
                "markers": ["human_gate_required"],
                "meaning": "stop automatic mutation until explicit human authority exists",
            },
        ],
        "blocked_outcome_required_fields": [
            "owner",
            "reason",
            "next_repair_action",
        ],
        "done_definition": done_definition,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "complete_product_claim_allowed": False,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }


def create_post_repair_review_task(
    *,
    hermes_bin: str,
    board: str,
    plan_task: dict[str, Any],
    parent_payload: dict[str, Any],
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
    worker_assignee_prefix: str,
    workspace_ref: str,
    runner: Runner = default_runner,
) -> str:
    body = ready_work_unit_post_repair_review_body(
        plan_task=plan_task,
        parent_task_id=parent_task_id,
        packet_id=packet_id,
        work_unit_id=work_unit_id,
    )
    task_id = create_task(
        hermes_bin=hermes_bin,
        board=board,
        title=f"OF post-repair review for ready work unit {work_unit_id}",
        body=compact_json_argument(body),
        assignee=ready_work_unit_reviewer_assignee(plan_task, worker_assignee_prefix),
        idempotency_key=ready_work_unit_post_repair_review_idempotency_key(
            plan_task=plan_task,
            parent_task_id=parent_task_id,
        ),
        created_by="overkill-factory",
        workspace=workspace_ref or task_dispatcher_workspace_ref(parent_payload) or "scratch",
        blocked=False,
        workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
        current_step_key="F18-independent-review",
        runner=runner,
    )
    run_checked(hermes_kanban(hermes_bin, board, "link", task_id, parent_task_id), runner)
    parent_readback = show_task(hermes_bin=hermes_bin, board=board, task_id=parent_task_id, runner=runner)
    review_readback = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    edge_present = (
        task_id in task_readback_parents(parent_readback)
        or task_id in task_readback_children(parent_readback)
        or parent_task_id in task_readback_parents(review_readback)
        or parent_task_id in task_readback_children(review_readback)
    )
    if not edge_present:
        raise RuntimeError(
            f"Hermes review dependency edge missing after link: review {task_id} must hold parent {parent_task_id}"
        )
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            parent_task_id,
            compact_json_argument(
                {
                    "marker": READY_WORK_UNIT_POST_REPAIR_REVIEW_CREATED_MARKER,
                    "work_unit_id": work_unit_id,
                    "review_task_ref": task_id,
                    "reviewer_role": ready_work_unit_reviewer_role(plan_task),
                    "reconciliation_scope": "post_release_ready_work_unit",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    return task_id


def parse_json_object(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if not isinstance(value, str):
        return {}
    text = value.strip()
    if not text.startswith("{"):
        return {}
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return parsed if isinstance(parsed, dict) else {}


def task_payload_objects(task: dict[str, Any]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for key in ("body", "metadata", "result"):
        payload = parse_json_object(task.get(key))
        if payload:
            payloads.append(payload)
    for run in task.get("runs") or []:
        if not isinstance(run, dict):
            continue
        payload = parse_json_object(run.get("metadata"))
        if payload:
            payloads.append(payload)
    return payloads


def task_has_ready_work_unit_execution_request(task: dict[str, Any]) -> bool:
    for payload in task_payload_objects(task):
        if payload.get("packet_type") == "ready_work_unit_execution_request":
            return True
        body_contract = payload.get("body_contract")
        if isinstance(body_contract, dict) and body_contract.get("packet_type") == "ready_work_unit_execution_request":
            return True
    return False


def task_has_ready_work_unit_materialization_plan(task: dict[str, Any]) -> bool:
    title = str(task.get("title") or task.get("name") or "").lower()
    if "ready_work_unit_hermes_materialization_plan" in title:
        return True
    for payload in task_payload_objects(task):
        if payload.get("record_type") == "ready_work_unit_hermes_materialization_plan":
            return True
        if (
            str(payload.get("required_output") or payload.get("artifact") or "").strip()
            == "ready_work_unit_hermes_materialization_plan"
        ):
            return True
        if isinstance(payload.get("ready_work_unit_hermes_materialization_plan"), dict):
            return True
    return False


def safe_repo_relative_path(path_ref: Any) -> Path | None:
    text = str(path_ref or "").strip()
    if not text:
        return None
    candidate = Path(text)
    if not candidate.is_absolute():
        candidate = ROOT / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(ROOT.resolve())
    except (OSError, ValueError):
        return None
    return resolved


def ready_work_unit_materialization_plan_path_from_task(task: dict[str, Any]) -> Path | None:
    for payload in task_payload_objects(task):
        if payload.get("record_type") == "ready_work_unit_hermes_materialization_plan":
            return None
        artifacts = payload.get("artifacts")
        if isinstance(artifacts, dict):
            plan_artifact = artifacts.get("plan")
            if isinstance(plan_artifact, dict):
                path = safe_repo_relative_path(plan_artifact.get("path_ref") or plan_artifact.get("path"))
                if path is not None and path.exists():
                    return path
        orchestration_result = payload.get("orchestration_result")
        if isinstance(orchestration_result, dict):
            for ref in orchestration_result.get("evidence_refs") or []:
                path = safe_repo_relative_path(ref)
                if path is not None and path.exists() and "READY_WORK_UNIT_HERMES_MATERIALIZATION_PLAN" in path.name:
                    return path
    return None


def latest_ready_work_unit_materialization_plan_path(rows: dict[str, list[dict[str, Any]]]) -> Path | None:
    candidates: list[tuple[int, Path]] = []
    for index, task in enumerate(rows.get("done", [])):
        if not task_has_ready_work_unit_materialization_plan(task):
            continue
        path = ready_work_unit_materialization_plan_path_from_task(task)
        if path is not None:
            completed = int(task.get("completed_at") or task.get("created_at") or index)
            candidates.append((completed, path))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[-1][1]


def board_has_ready_work_unit_execution_requests(rows: dict[str, list[dict[str, Any]]]) -> bool:
    return any(
        task_has_ready_work_unit_execution_request(task)
        for tasks in rows.values()
        for task in tasks
    )


def auto_materialize_ready_work_units_from_plan(
    *,
    hermes_bin: str,
    board: str,
    plan_path: Path,
    worker_assignee_prefix: str,
    workspace: str,
    runner: Runner,
) -> dict[str, Any]:
    out_dir = ROOT / ".tmp" / "factory-runs"
    out_dir.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(str(plan_path).encode("utf-8")).hexdigest()[:12]
    route_readiness_path = out_dir / f"ready-work-unit-route-readiness-{board}-{digest}.json"
    materialization_result_path = out_dir / f"ready-work-unit-materialization-{board}-{digest}.json"
    release_result_path = out_dir / f"ready-work-unit-release-{board}-{digest}.json"

    route_readiness = collect_route_readiness(
        argparse.Namespace(
            plan=plan_path,
            worker=[],
            hermes_bin=hermes_bin,
            required_auth_provider="OpenAI Codex",
            credential_evidence_ref="external:hermes-status-auth-provider-ready",
            ledger_ref="external:hermes-worker-route-readiness-ledger",
            out=route_readiness_path,
        ),
        runner=runner,
    )
    materialization = materialize_ready_work_units(
        argparse.Namespace(
            plan=plan_path,
            board=board,
            hermes_bin=hermes_bin,
            worker_assignee_prefix=worker_assignee_prefix,
            workspace=workspace,
            ensure_board=False,
            dry_run=False,
            route_readiness=route_readiness_path,
            out=materialization_result_path,
        ),
        runner=runner,
    )
    release = release_ready_work_units(
        argparse.Namespace(
            plan=plan_path,
            materialization_result=materialization_result_path,
            board=board,
            hermes_bin=hermes_bin,
            worker_assignee_prefix=worker_assignee_prefix,
            route_readiness=route_readiness_path,
            reason=None,
            dry_run=False,
            out=release_result_path,
        ),
        runner=runner,
    )
    return {
        "plan_path": str(plan_path.relative_to(ROOT)),
        "route_readiness_path": str(route_readiness_path.relative_to(ROOT)),
        "materialization_result_path": str(materialization_result_path.relative_to(ROOT)),
        "release_result_path": str(release_result_path.relative_to(ROOT)),
        "route_readiness": route_readiness,
        "materialization": materialization,
        "release": release,
    }


def string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def existing_post_repair_review_task_ref(payload: dict[str, Any], *, work_unit_id: str) -> str:
    for comment in reversed(task_readback_comments(payload)):
        marker = parse_json_object(comment.get("body") or comment.get("text") or comment.get("payload"))
        if marker.get("marker") != READY_WORK_UNIT_POST_REPAIR_REVIEW_CREATED_MARKER:
            continue
        if str(marker.get("work_unit_id") or "").strip() != work_unit_id:
            continue
        review_task_ref = str(marker.get("review_task_ref") or "").strip()
        if review_task_ref:
            return review_task_ref
    return ""


def existing_post_repair_authority_task_ref(
    payload: dict[str, Any],
    *,
    work_unit_id: str,
    review_task_ref: str | None = None,
) -> str:
    expected_review_task_ref = str(review_task_ref or "").strip()
    for comment in reversed(task_readback_comments(payload)):
        marker = parse_json_object(comment.get("body") or comment.get("text") or comment.get("payload"))
        if marker.get("marker") != READY_WORK_UNIT_POST_REPAIR_AUTHORITY_CREATED_MARKER:
            continue
        if str(marker.get("work_unit_id") or "").strip() != work_unit_id:
            continue
        marker_review_task_ref = str(marker.get("review_task_ref") or "").strip()
        if expected_review_task_ref and marker_review_task_ref != expected_review_task_ref:
            continue
        authority_task_ref = str(marker.get("authority_task_ref") or "").strip()
        if authority_task_ref:
            return authority_task_ref
    return ""


def ready_work_unit_post_repair_authority_idempotency_key(
    *,
    plan_task: dict[str, Any],
    parent_task_id: str,
    review_task_ref: str,
) -> str:
    base = str(plan_task.get("idempotency_key") or "").strip()
    if not base:
        _packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
        base = f"overkill:ready-work-unit:{work_unit_id}"
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "base_idempotency_key": base,
                "parent_task_id": parent_task_id,
                "review_task_ref": review_task_ref,
                "route": "post_repair_authority",
                "version": "v1",
            }
        )
    )
    return f"{base}:post-repair-authority:{digest}"


def ready_work_unit_post_repair_authority_body(
    *,
    plan_task: dict[str, Any],
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
    review_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "packet_type": "ready_work_unit_post_repair_authority_request",
        "marker": READY_WORK_UNIT_POST_REPAIR_AUTHORITY_REQUIRED_MARKER,
        "current_step_key": "F18-independent-review",
        "kanban_workflow_binding": {
            "workflow_template_id": FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
            "current_step_key": "F18-independent-review",
            "runtime_field_required": True,
            "fallback_body_binding": True,
            "route_authority": "factory_phase_engine",
        },
        **ready_work_unit_route_repair_scope_contract(plan_task),
        "parent_packet_id": packet_id,
        "parent_work_unit_id": work_unit_id,
        "parent_task_ref": parent_task_id,
        "review_task_ref": review_result.get("review_task_ref"),
        "repair_task_ref": review_result.get("repair_task_ref"),
        "review_result_marker": review_result.get("marker"),
        "review_result_status": review_result.get("status"),
        "authority_scope": "post_repair_retry_or_done_only",
        "authority_must_choose_one": [
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_retry_authorized",
                ],
                "meaning": "parent ready work unit may be retried by Hermes reconciliation",
            },
            {
                "markers": [
                    "ready_work_unit_repair_review_passed",
                    "ready_work_unit_done_authorized",
                    "ready_work_unit_done_definition_satisfied",
                ],
                "meaning": "parent ready work unit may be completed, not the whole product",
            },
            {
                "markers": ["human_gate_required"],
                "meaning": "stop automatic mutation until explicit human authority exists",
            },
            {
                "markers": ["structured_block"],
                "required_fields": ["owner", "reason", "next_authority_action"],
                "meaning": "authority cannot be granted yet; route the next non-human action",
            },
        ],
        "review_must_not_approve": [
            "complete_product",
            "release",
            "deployment",
            "customer_ready",
            "security_gate",
            "human_gate",
        ],
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "complete_product_claim_allowed": False,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }


def create_post_repair_authority_task(
    *,
    hermes_bin: str,
    board: str,
    plan_task: dict[str, Any],
    parent_payload: dict[str, Any],
    parent_task_id: str,
    packet_id: str,
    work_unit_id: str,
    review_result: dict[str, Any],
    worker_assignee_prefix: str,
    workspace_ref: str,
    runner: Runner = default_runner,
) -> str:
    body = ready_work_unit_post_repair_authority_body(
        plan_task=plan_task,
        parent_task_id=parent_task_id,
        packet_id=packet_id,
        work_unit_id=work_unit_id,
        review_result=review_result,
    )
    task_id = create_task(
        hermes_bin=hermes_bin,
        board=board,
        title=f"OF post-repair authority decision for ready work unit {work_unit_id}",
        body=compact_json_argument(body),
        assignee=worker_assignee_prefix + "independent-reviewer",
        idempotency_key=ready_work_unit_post_repair_authority_idempotency_key(
            plan_task=plan_task,
            parent_task_id=parent_task_id,
            review_task_ref=str(review_result.get("review_task_ref") or ""),
        ),
        created_by="overkill-factory",
        workspace=workspace_ref or task_dispatcher_workspace_ref(parent_payload) or "scratch",
        blocked=False,
        workflow_template_id=FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID,
        current_step_key="F18-independent-review",
        runner=runner,
    )
    run_checked(hermes_kanban(hermes_bin, board, "link", task_id, parent_task_id), runner)
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            parent_task_id,
            compact_json_argument(
                {
                    "marker": READY_WORK_UNIT_POST_REPAIR_AUTHORITY_CREATED_MARKER,
                    "work_unit_id": work_unit_id,
                    "authority_task_ref": task_id,
                    "review_task_ref": review_result.get("review_task_ref"),
                    "repair_task_ref": review_result.get("repair_task_ref"),
                    "authority_scope": "post_repair_retry_or_done_only",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    return task_id


def no_forbidden_approvals_claimed(metadata: dict[str, Any]) -> bool:
    approvals = metadata.get("no_forbidden_approvals")
    if not isinstance(approvals, dict):
        return False
    return all(value is False for value in approvals.values())


def post_repair_review_result_from_run(
    *,
    run: dict[str, Any],
    parent_task_id: str,
    work_unit_id: str,
    review_task_id: str,
    expected_assignee: str = "independent-reviewer",
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None

    parent_ref = str(metadata.get("parent_task_ref") or metadata.get("parent_ref") or "").strip()
    live_readback = metadata.get("live_readback")
    if not parent_ref and isinstance(live_readback, dict):
        parent = live_readback.get("parent")
        if isinstance(parent, dict):
            parent_ref = str(parent.get("id") or parent.get("task_id") or "").strip()
    if parent_ref and parent_ref != parent_task_id:
        return None

    metadata_work_unit = str(metadata.get("parent_work_unit_id") or metadata.get("work_unit_id") or "").strip()
    if metadata_work_unit and metadata_work_unit != work_unit_id:
        return None

    nested_review = metadata.get("independent_review_result")
    nested_review = nested_review if isinstance(nested_review, dict) else {}
    nested_review_target = str(
        nested_review.get("review_target")
        or nested_review.get("reviewed_parent_card_id")
        or nested_review.get("parent_task_ref")
        or ""
    ).strip()
    nested_verdict = str(nested_review.get("verdict") or "").strip().upper()
    explicit_marker = metadata.get("marker") == READY_WORK_UNIT_POST_REPAIR_REVIEW_RESULT_MARKER
    reviewed_repair_card = str(metadata.get("reviewed_repair_card") or metadata.get("repair_task_ref") or "").strip()
    review_scope = str(metadata.get("review_scope") or "").strip().lower()
    run_profile = str(run.get("profile") or run.get("assignee") or "").strip()
    if not explicit_marker and not reviewed_repair_card and "repair" not in review_scope and not nested_review_target:
        return None
    allowed_profiles = {"independent-reviewer", expected_assignee}
    if run_profile and run_profile not in allowed_profiles:
        return None

    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    validation_result = str(metadata.get("validation_result") or metadata.get("result") or "").strip().upper()
    blocking_findings = metadata.get("blocking_findings")
    if blocking_findings is None:
        blocking_findings = nested_review.get("blocking_findings")
    human_gate_required = metadata.get("human_gate_required") is True or nested_review.get("human_gate_required") is True

    explicit_pass = metadata.get("ready_work_unit_repair_review_passed") is True
    nested_pass = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed"}
        and nested_verdict.startswith("PASS")
        and blocking_findings is False
        and nested_review_target == parent_task_id
    )
    legacy_pass = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed"}
        and validation_result == "PASS"
        and blocking_findings is False
        and no_forbidden_approvals_claimed(metadata)
        and bool(parent_ref)
        and bool(reviewed_repair_card)
    )
    blocked = (
        metadata.get("review_blocked") is True
        or blocking_findings is True
        or status == "blocked"
        or outcome == "blocked"
    )
    repair_review_passed = explicit_pass or legacy_pass or nested_pass
    if not repair_review_passed and not blocked and not human_gate_required:
        return None

    retry_authorized = metadata.get("ready_work_unit_retry_authorized") is True
    done_authorized = metadata.get("ready_work_unit_done_authorized") is True
    done_definition_satisfied = metadata.get("ready_work_unit_done_definition_satisfied") is True
    return {
        "marker": READY_WORK_UNIT_POST_REPAIR_REVIEW_RESULT_MARKER,
        "review_task_ref": review_task_id,
        "repair_task_ref": reviewed_repair_card or None,
        "parent_task_ref": parent_task_id,
        "work_unit_id": work_unit_id,
        "source": "hermes_run_metadata",
        "status": "human_gate_required" if human_gate_required else "passed" if repair_review_passed else "blocked",
        "repair_review_passed": repair_review_passed,
        "retry_authorized": retry_authorized,
        "done_authorized": done_authorized,
        "done_definition_satisfied": done_definition_satisfied,
        "human_gate_required": human_gate_required,
        "blocked": blocked and not repair_review_passed,
        "complete_product_claim_allowed": False,
    }


def apply_post_repair_review_result(row: dict[str, Any], result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return row
    merged = dict(row)
    merged["post_repair_review_result"] = result
    merged["repair_review_passed"] = result.get("repair_review_passed") is True
    merged["retry_authorized"] = result.get("retry_authorized") is True
    merged["done_authorized"] = result.get("done_authorized") is True
    merged["done_definition_satisfied"] = result.get("done_definition_satisfied") is True
    merged["human_gate_required"] = result.get("human_gate_required") is True

    if row.get("decision") == "already_satisfied":
        return merged
    if merged["human_gate_required"]:
        merged["decision"] = "human_gate_required"
        merged["next_action"] = "wait for explicit human gate; no automatic retry or completion"
        merged["actionable_by_adapter"] = False
    elif result.get("blocked") is True:
        merged["decision"] = "repair_review_blocked"
        merged["next_action"] = "post-repair review blocked; route a factory-owned repair attempt before retry"
        merged["actionable_by_adapter"] = False
    elif (
        merged.get("repair_completed")
        and merged["repair_review_passed"]
        and merged["done_authorized"]
        and merged["done_definition_satisfied"]
    ):
        merged["decision"] = "complete_parent"
        merged["next_action"] = "complete the parent ready work unit through Hermes complete"
        merged["actionable_by_adapter"] = True
    elif merged.get("repair_completed") and merged["repair_review_passed"] and merged["retry_authorized"]:
        merged["decision"] = "retry_parent"
        merged["next_action"] = "unblock parent ready work unit for another Hermes worker attempt"
        merged["actionable_by_adapter"] = True
    elif merged["repair_completed"] and merged["repair_review_passed"]:
        merged["decision"] = "awaiting_retry_or_done_authority"
        merged["next_action"] = "repair review passed, but no explicit retry or done authority marker exists"
        merged["actionable_by_adapter"] = False
    return merged


def post_repair_review_results_by_work_unit(
    *,
    hermes_bin: str,
    board: str,
    parent_task_ids_by_work_unit: dict[str, str],
    reviewer_assignees_by_work_unit: dict[str, str] | None = None,
    worker_assignee_prefix: str,
    runner: Runner = default_runner,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    latest_sort_key: dict[str, tuple[int, int]] = {}
    seen_task_ids: set[str] = set()
    expected_assignees = set((reviewer_assignees_by_work_unit or {}).values())
    expected_assignees.add(worker_assignee_prefix + "independent-reviewer")
    for status in ["done", "blocked", "running"]:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            assignee = str(record.get("assignee") or record.get("profile") or "").strip()
            if assignee and assignee not in expected_assignees:
                continue
            try:
                runs = task_run_records(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            except RuntimeError:
                continue
            for run in runs:
                for work_unit_id, parent_task_id in parent_task_ids_by_work_unit.items():
                    result = post_repair_review_result_from_run(
                        run=run,
                        parent_task_id=parent_task_id,
                        work_unit_id=work_unit_id,
                        review_task_id=task_id,
                        expected_assignee=(reviewer_assignees_by_work_unit or {}).get(
                            work_unit_id,
                            worker_assignee_prefix + "independent-reviewer",
                        ),
                    )
                    if not result:
                        continue
                    run_id = int(run.get("id") or run.get("run_id") or 0)
                    ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
                    sort_key = (ended_at, run_id)
                    if sort_key >= latest_sort_key.get(work_unit_id, (0, 0)):
                        latest_sort_key[work_unit_id] = sort_key
                        results[work_unit_id] = result
    return results


def post_repair_authority_result_from_run(
    *,
    run: dict[str, Any],
    authority_task_id: str,
    parent_task_id: str,
    work_unit_id: str,
    review_task_ref: str,
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    authority_decision = review_result.get("authority_decision")
    authority_decision = authority_decision if isinstance(authority_decision, dict) else {}
    selected_markers = metadata.get("selected_markers")
    if not isinstance(selected_markers, list):
        selected_markers = review_result.get("selected_markers")
    if not isinstance(selected_markers, list):
        selected_markers = authority_decision.get("selected_markers")
    markers = {str(marker or "").strip() for marker in (selected_markers or []) if str(marker or "").strip()}
    if not markers:
        for marker_key in (
            "ready_work_unit_repair_review_passed",
            "ready_work_unit_retry_authorized",
            "ready_work_unit_done_authorized",
            "ready_work_unit_done_definition_satisfied",
            "human_gate_required",
        ):
            if metadata.get(marker_key) is True or review_result.get(marker_key) is True:
                markers.add(marker_key)
    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    blocked = status == "blocked" or outcome == "blocked" or "structured_block" in markers
    if not markers and not blocked:
        return None
    repair_review_passed = "ready_work_unit_repair_review_passed" in markers
    retry_authorized = "ready_work_unit_retry_authorized" in markers
    done_authorized = "ready_work_unit_done_authorized" in markers
    done_definition_satisfied = "ready_work_unit_done_definition_satisfied" in markers
    authority_verdict = str(review_result.get("verdict") or "").strip().upper()
    if authority_verdict.startswith("PASS") and (retry_authorized or done_authorized or done_definition_satisfied):
        repair_review_passed = True
    human_gate_required = "human_gate_required" in markers or metadata.get("human_gate_required") is True
    return {
        "marker": READY_WORK_UNIT_POST_REPAIR_AUTHORITY_RESULT_MARKER,
        "authority_task_ref": authority_task_id,
        "review_task_ref": review_task_ref or None,
        "parent_task_ref": parent_task_id,
        "work_unit_id": work_unit_id,
        "source": "hermes_run_metadata",
        "status": "human_gate_required" if human_gate_required else "passed" if repair_review_passed else "blocked",
        "repair_review_passed": repair_review_passed,
        "retry_authorized": retry_authorized,
        "done_authorized": done_authorized,
        "done_definition_satisfied": done_definition_satisfied,
        "human_gate_required": human_gate_required,
        "blocked": blocked and not repair_review_passed,
        "complete_product_claim_allowed": False,
    }


def apply_post_repair_authority_result(row: dict[str, Any], result: dict[str, Any] | None) -> dict[str, Any]:
    if not result:
        return row
    merged = dict(row)
    merged["post_repair_authority_result"] = result
    merged["repair_review_passed"] = bool(merged.get("repair_review_passed")) or result.get("repair_review_passed") is True
    merged["retry_authorized"] = bool(merged.get("retry_authorized")) or result.get("retry_authorized") is True
    merged["done_authorized"] = bool(merged.get("done_authorized")) or result.get("done_authorized") is True
    merged["done_definition_satisfied"] = (
        bool(merged.get("done_definition_satisfied")) or result.get("done_definition_satisfied") is True
    )
    merged["human_gate_required"] = bool(merged.get("human_gate_required")) or result.get("human_gate_required") is True
    if merged["human_gate_required"]:
        merged["decision"] = "human_gate_required"
        merged["next_action"] = "wait for explicit human gate; no automatic retry or completion"
        merged["actionable_by_adapter"] = False
    elif result.get("blocked") is True:
        merged["decision"] = "authority_blocked"
        merged["next_action"] = "post-repair authority task blocked; route the declared next action before retry"
        merged["actionable_by_adapter"] = False
    elif (
        merged.get("repair_completed")
        and merged["repair_review_passed"]
        and merged["done_authorized"]
        and merged["done_definition_satisfied"]
    ):
        merged["decision"] = "complete_parent"
        merged["next_action"] = "complete the parent ready work unit through Hermes complete"
        merged["actionable_by_adapter"] = True
    elif merged.get("repair_completed") and merged["repair_review_passed"] and merged["retry_authorized"]:
        merged["decision"] = "retry_parent"
        merged["next_action"] = "unblock parent ready work unit for another Hermes worker attempt"
        merged["actionable_by_adapter"] = True
    return merged


def post_repair_authority_results_by_work_unit(
    *,
    hermes_bin: str,
    board: str,
    parent_task_ids_by_work_unit: dict[str, str],
    review_task_refs_by_work_unit: dict[str, str] | None = None,
    worker_assignee_prefix: str,
    runner: Runner = default_runner,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    latest_sort_key: dict[str, tuple[int, int]] = {}
    seen_task_ids: set[str] = set()
    expected_assignee = worker_assignee_prefix + "independent-reviewer"
    for status in ["done", "blocked", "running"]:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            assignee = str(record.get("assignee") or record.get("profile") or "").strip()
            if assignee and assignee != expected_assignee:
                continue
            try:
                payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
                body = parse_json_object(task_readback_body(payload))
            except RuntimeError:
                continue
            if body.get("packet_type") != "ready_work_unit_post_repair_authority_request":
                continue
            work_unit_id = str(body.get("parent_work_unit_id") or "").strip()
            parent_task_id = str(body.get("parent_task_ref") or "").strip()
            if not work_unit_id or parent_task_ids_by_work_unit.get(work_unit_id) != parent_task_id:
                continue
            review_task_ref = str(body.get("review_task_ref") or "").strip()
            expected_review_task_ref = str((review_task_refs_by_work_unit or {}).get(work_unit_id) or "").strip()
            if expected_review_task_ref and review_task_ref != expected_review_task_ref:
                continue
            try:
                runs = task_run_records(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            except RuntimeError:
                continue
            for run in runs:
                result = post_repair_authority_result_from_run(
                    run=run,
                    authority_task_id=task_id,
                    parent_task_id=parent_task_id,
                    work_unit_id=work_unit_id,
                    review_task_ref=review_task_ref,
                )
                if not result:
                    continue
                run_id = int(run.get("id") or run.get("run_id") or 0)
                ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
                sort_key = (ended_at, run_id)
                if sort_key >= latest_sort_key.get(work_unit_id, (0, 0)):
                    latest_sort_key[work_unit_id] = sort_key
                    results[work_unit_id] = result
    return results


def nested_string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for item in value.values():
            values.extend(nested_string_values(item))
        return values
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(nested_string_values(item))
        return values
    return []


def string_targets_task_ref(value: str, task_id: str) -> bool:
    text = str(value or "").strip()
    if not text or not task_id:
        return False
    exact_refs = {
        task_id,
        f"kanban:{task_id}",
        f"workspace:{task_id}",
    }
    if text in exact_refs:
        return True
    return (
        f"kanban:{task_id}" in text
        or f"workspace:{task_id}" in text
        or f"workspaces/{task_id}/" in text
        or f"task_id={task_id}" in text
    )


def review_metadata_targets_task(metadata: dict[str, Any], *, task_id: str) -> bool:
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    explicit_fields = (
        metadata.get("review_target"),
        metadata.get("review_comment_task_id"),
        metadata.get("parent_task_ref"),
        review_result.get("review_target"),
        review_result.get("review_comment_task_id"),
        review_result.get("parent_task_ref"),
        review_result.get("reviewed_parent_card_id"),
    )
    if any(string_targets_task_ref(str(value or ""), task_id) for value in explicit_fields):
        return True
    return any(string_targets_task_ref(value, task_id) for value in nested_string_values(metadata))


def ready_work_unit_review_result_from_run(
    *,
    run: dict[str, Any],
    review_task_id: str,
    parent_task_id: str,
    work_unit_id: str,
    expected_assignee: str = "independent-reviewer",
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None
    run_profile = str(run.get("profile") or run.get("assignee") or "").strip()
    if run_profile and run_profile not in {"independent-reviewer", expected_assignee}:
        return None
    if not review_metadata_targets_task(metadata, task_id=parent_task_id):
        return None
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    verdict = str(review_result.get("verdict") or metadata.get("verdict") or "").strip().upper()
    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    required_fixes = review_result.get("required_fixes")
    required_fixes = required_fixes if isinstance(required_fixes, list) else []
    blocking_findings = metadata.get("blocking_findings")
    if blocking_findings is None:
        blocking_findings = review_result.get("blocking_findings")
    human_gate_required = (
        metadata.get("human_gate_required") is True
        or review_result.get("human_gate_required") is True
        or metadata.get("production_promotion_approved") == "human_gate_required"
    )
    pass_result = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed", "success", "succeeded"}
        and verdict.startswith("PASS")
        and blocking_findings is not True
    )
    blocked = (
        blocking_findings is True
        or status == "blocked"
        or outcome == "blocked"
        or verdict.startswith("BLOCK")
        or bool(required_fixes)
    )
    if not pass_result and not blocked and not human_gate_required:
        return None
    return {
        "marker": "ready_work_unit_review_result",
        "review_task_ref": review_task_id,
        "parent_task_ref": parent_task_id,
        "work_unit_id": work_unit_id,
        "source": "hermes_run_metadata",
        "status": "human_gate_required" if human_gate_required else "passed" if pass_result else "blocked",
        "verdict": verdict or None,
        "review_passed": pass_result,
        "blocked": blocked and not pass_result,
        "human_gate_required": human_gate_required,
        "required_fix_count": len(required_fixes),
        "complete_product_claim_allowed": False,
    }


def ready_work_unit_review_results_by_work_unit(
    *,
    hermes_bin: str,
    board: str,
    parent_task_ids_by_work_unit: dict[str, str],
    worker_assignee_prefix: str,
    runner: Runner = default_runner,
) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    latest_sort_key: dict[str, tuple[int, int]] = {}
    seen_task_ids: set[str] = set()
    expected_assignee = worker_assignee_prefix + "independent-reviewer"
    for status in ["done", "blocked", "running"]:
        for record in list_tasks_by_status(hermes_bin=hermes_bin, board=board, status=status, runner=runner):
            task_id = str(record.get("task_id") or record.get("id") or "").strip()
            if not task_id or task_id in seen_task_ids:
                continue
            seen_task_ids.add(task_id)
            assignee = str(record.get("assignee") or record.get("profile") or "").strip()
            if assignee and assignee != expected_assignee:
                continue
            try:
                runs = task_run_records(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
            except RuntimeError:
                continue
            for run in runs:
                for work_unit_id, parent_task_id in parent_task_ids_by_work_unit.items():
                    result = ready_work_unit_review_result_from_run(
                        run=run,
                        review_task_id=task_id,
                        parent_task_id=parent_task_id,
                        work_unit_id=work_unit_id,
                        expected_assignee=expected_assignee,
                    )
                    if not result:
                        continue
                    run_id = int(run.get("id") or run.get("run_id") or 0)
                    ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
                    sort_key = (ended_at, run_id)
                    if sort_key >= latest_sort_key.get(work_unit_id, (0, 0)):
                        latest_sort_key[work_unit_id] = sort_key
                        results[work_unit_id] = result
    return results


def superseded_post_repair_review_parent_ids(
    *,
    hermes_bin: str,
    board: str,
    parent_payload: dict[str, Any],
    parent_task_id: str,
    work_unit_id: str,
    authority_result: dict[str, Any] | None,
    runner: Runner = default_runner,
) -> list[str]:
    if not authority_result:
        return []
    if not (authority_result.get("retry_authorized") is True or authority_result.get("done_authorized") is True):
        return []
    authority_task_ref = str(authority_result.get("authority_task_ref") or "").strip()
    stale_parent_ids: list[str] = []
    for candidate_parent_id in task_readback_parents(parent_payload):
        if not candidate_parent_id or candidate_parent_id == authority_task_ref:
            continue
        try:
            candidate_payload = show_task(
                hermes_bin=hermes_bin,
                board=board,
                task_id=candidate_parent_id,
                runner=runner,
            )
            candidate_body = parse_json_object(task_readback_body(candidate_payload))
        except RuntimeError:
            continue
        if candidate_body.get("packet_type") != "ready_work_unit_post_repair_review_request":
            continue
        if str(candidate_body.get("parent_work_unit_id") or "").strip() != work_unit_id:
            continue
        if str(candidate_body.get("parent_task_ref") or "").strip() != parent_task_id:
            continue
        if task_readback_status(candidate_payload) != "blocked":
            continue
        stale_parent_ids.append(candidate_parent_id)
    return stale_parent_ids


def reconcile_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit reconciliation requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=plan,
        board=board,
    )
    tasks = expected_ready_work_unit_tasks(plan)
    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["todo", "blocked", "ready", "running", "done"],
        runner=runner,
    )

    verified: list[tuple[dict[str, Any], dict[str, Any], str, str, str, str]] = []
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        if len(matches) != 1:
            raise RuntimeError(
                f"ready work-unit reconciliation expected exactly one active Hermes task for packet {key[0]} / work unit {key[1]}, found {len(matches)}"
            )
        task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
            payload=matches[0],
            plan_task=task,
            worker_assignee_prefix=args.worker_assignee_prefix,
        )
        verified.append((task, matches[0], task_id, packet_id, work_unit_id, task_readback_status(matches[0])))

    reviewer_assignees_by_work_unit = {
        work_unit_id: ready_work_unit_reviewer_assignee(task, args.worker_assignee_prefix)
        for task, _payload, _task_id, _packet_id, work_unit_id, _status in verified
    }
    review_results = post_repair_review_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit={
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        reviewer_assignees_by_work_unit=reviewer_assignees_by_work_unit,
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )
    authority_results = post_repair_authority_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit={
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        review_task_refs_by_work_unit={
            work_unit_id: str(result.get("review_task_ref") or "").strip()
            for work_unit_id, result in review_results.items()
            if str(result.get("review_task_ref") or "").strip()
        },
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )

    dependencies = ready_work_unit_dependencies(tasks)
    status_by_work_unit = {work_unit_id: status for _task, _payload, _task_id, _packet_id, work_unit_id, status in verified}
    dependency_blockers: dict[str, list[str]] = {}
    for _task, _payload, _task_id, _packet_id, work_unit_id, status in verified:
        if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
            continue
        blockers = [
            dep
            for dep in dependencies.get(work_unit_id, [])
            if status_by_work_unit.get(dep) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
        ]
        if blockers:
            dependency_blockers[work_unit_id] = blockers

    reconciliation: dict[str, dict[str, Any]] = {}
    retry_candidates: list[tuple[dict[str, Any], dict[str, Any], str, str, str, str]] = []
    complete_candidates: list[tuple[dict[str, Any], str, str, str]] = []
    post_repair_review_candidates: list[tuple[dict[str, Any], dict[str, Any], str, str, str]] = []
    post_repair_authority_candidates: list[tuple[dict[str, Any], dict[str, Any], str, str, str, dict[str, Any]]] = []
    superseded_parent_candidates: dict[str, list[str]] = {}
    post_repair_review_required_work_unit_ids: set[str] = set()
    existing_post_repair_review_task_ids: dict[str, str] = {}
    post_repair_authority_required_work_unit_ids: set[str] = set()
    existing_post_repair_authority_task_ids: dict[str, str] = {}
    post_release_blocked_count = 0
    human_gate_count = 0
    incomplete_count = 0
    post_repair_review_result_count = 0
    post_repair_authority_result_count = 0
    for task, payload, task_id, packet_id, work_unit_id, status in verified:
        row = classify_ready_work_unit_post_release_reconciliation(payload)
        row["task_ref"] = task_id
        row["packet_id"] = packet_id
        row["dependency_blockers"] = dependency_blockers.get(work_unit_id, [])
        review_result = review_results.get(work_unit_id)
        if review_result:
            row = apply_post_repair_review_result(row, review_result)
            post_repair_review_result_count += 1
        authority_result = authority_results.get(work_unit_id)
        if authority_result:
            row = apply_post_repair_authority_result(row, authority_result)
            post_repair_authority_result_count += 1
        row["post_repair_review_required"] = row["decision"] == "awaiting_repair_review"
        existing_review_task_id = ""
        if row["post_repair_review_required"]:
            post_repair_review_required_work_unit_ids.add(work_unit_id)
            existing_review_task_id = existing_post_repair_review_task_ref(payload, work_unit_id=work_unit_id)
            if existing_review_task_id:
                existing_post_repair_review_task_ids[work_unit_id] = existing_review_task_id
        elif review_result and review_result.get("review_task_ref"):
            existing_review_task_id = str(review_result["review_task_ref"])
            existing_post_repair_review_task_ids[work_unit_id] = existing_review_task_id
        row["post_repair_review_task_ref"] = existing_review_task_id or None
        row["post_repair_review_task_exists"] = bool(existing_review_task_id)
        existing_authority_task_id = ""
        if row["decision"] == "awaiting_retry_or_done_authority":
            post_repair_authority_required_work_unit_ids.add(work_unit_id)
            existing_authority_task_id = existing_post_repair_authority_task_ref(
                payload,
                work_unit_id=work_unit_id,
                review_task_ref=str((review_result or {}).get("review_task_ref") or "").strip(),
            )
            if existing_authority_task_id:
                existing_post_repair_authority_task_ids[work_unit_id] = existing_authority_task_id
        elif authority_result and authority_result.get("authority_task_ref"):
            existing_authority_task_id = str(authority_result["authority_task_ref"])
            existing_post_repair_authority_task_ids[work_unit_id] = existing_authority_task_id
        row["post_repair_authority_required"] = row["decision"] == "awaiting_retry_or_done_authority"
        row["post_repair_authority_task_ref"] = existing_authority_task_id or None
        row["post_repair_authority_task_exists"] = bool(existing_authority_task_id)
        superseded_parent_ids = []
        if row["decision"] in {"retry_parent", "complete_parent"}:
            superseded_parent_ids = superseded_post_repair_review_parent_ids(
                hermes_bin=args.hermes_bin,
                board=board,
                parent_payload=payload,
                parent_task_id=task_id,
                work_unit_id=work_unit_id,
                authority_result=authority_result,
                runner=runner,
            )
            if superseded_parent_ids:
                superseded_parent_candidates[work_unit_id] = superseded_parent_ids
        row["superseded_post_repair_review_parent_refs"] = superseded_parent_ids
        reconciliation[work_unit_id] = row
        if status == "blocked" and row["release_record_seen"]:
            post_release_blocked_count += 1
        if row["decision"] == "human_gate_required":
            human_gate_count += 1
        if row["decision"] in {
            "awaiting_repair",
            "awaiting_repair_review",
            "awaiting_retry_or_done_authority",
            "invalid_blocked_readback",
        }:
            incomplete_count += 1
        if row["decision"] == "retry_parent":
            retry_candidates.append((task, payload, task_id, packet_id, work_unit_id, status))
        elif row["decision"] == "complete_parent":
            complete_candidates.append((task, task_id, packet_id, work_unit_id))
        elif row["decision"] == "awaiting_repair_review" and not existing_review_task_id:
            post_repair_review_candidates.append((task, payload, task_id, packet_id, work_unit_id))
        elif row["decision"] == "awaiting_retry_or_done_authority" and not existing_authority_task_id:
            review_result = row.get("post_repair_review_result")
            if isinstance(review_result, dict):
                post_repair_authority_candidates.append((task, payload, task_id, packet_id, work_unit_id, review_result))

    if not args.dry_run and retry_candidates:
        required_workers = [
            ready_work_unit_release_assignee(task, args.worker_assignee_prefix)
            for task, _payload, _task_id, _packet_id, _work_unit_id, _status in retry_candidates
        ]
        readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
        if readiness_blockers:
            raise RuntimeError("pre-retry route readiness blocked ready work-unit reconciliation: " + "; ".join(readiness_blockers))
    if not args.dry_run and args.create_post_repair_review_tasks and post_repair_review_candidates:
        readiness_blockers = route_readiness_blockers(
            args.route_readiness,
            sorted(
                {
                    ready_work_unit_reviewer_assignee(task, args.worker_assignee_prefix)
                    for task, _payload, _task_id, _packet_id, _work_unit_id in post_repair_review_candidates
                }
            ),
        )
        if readiness_blockers:
            raise RuntimeError("post-repair review route readiness blocked ready work-unit reconciliation: " + "; ".join(readiness_blockers))
    if not args.dry_run and args.create_post_repair_authority_tasks and post_repair_authority_candidates:
        readiness_blockers = route_readiness_blockers(
            args.route_readiness,
            [args.worker_assignee_prefix + "independent-reviewer"],
        )
        if readiness_blockers:
            raise RuntimeError(
                "post-repair authority route readiness blocked ready work-unit reconciliation: " + "; ".join(readiness_blockers)
            )

    retry_ready_work_unit_task_ids: dict[str, str] = {}
    unblocked_ready_work_unit_task_ids: dict[str, str] = {}
    completed_ready_work_unit_task_ids: dict[str, str] = {}
    created_post_repair_review_task_ids: dict[str, str] = {}
    post_repair_review_task_ids: dict[str, str] = dict(existing_post_repair_review_task_ids)
    created_post_repair_authority_task_ids: dict[str, str] = {}
    post_repair_authority_task_ids: dict[str, str] = dict(existing_post_repair_authority_task_ids)
    unlinked_superseded_parent_task_ids: dict[str, list[str]] = {}
    promoted_ready_work_unit_task_ids: dict[str, str] = {}
    followup_release_result: dict[str, Any] | None = None
    retry_reason = str(
        args.reason
        or "ready_work_unit_retry_authorized; ready_work_unit_repair_review_passed; reconciliation_scope=post_release_ready_work_unit; dispatch_separate=true"
    )
    if not args.dry_run:
        if args.create_post_repair_review_tasks:
            workspace_ref = str(args.post_repair_review_workspace or "").strip()
            for task, payload, task_id, packet_id, work_unit_id in post_repair_review_candidates:
                review_task_id = create_post_repair_review_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    plan_task=task,
                    parent_payload=payload,
                    parent_task_id=task_id,
                    packet_id=packet_id,
                    work_unit_id=work_unit_id,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                    workspace_ref=workspace_ref,
                    runner=runner,
                )
                post_repair_review_task_ids[work_unit_id] = review_task_id
                created_post_repair_review_task_ids[work_unit_id] = review_task_id
        if args.create_post_repair_authority_tasks:
            workspace_ref = str(args.post_repair_authority_workspace or "").strip()
            for task, payload, task_id, packet_id, work_unit_id, review_result in post_repair_authority_candidates:
                authority_task_id = create_post_repair_authority_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    plan_task=task,
                    parent_payload=payload,
                    parent_task_id=task_id,
                    packet_id=packet_id,
                    work_unit_id=work_unit_id,
                    review_result=review_result,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                    workspace_ref=workspace_ref,
                    runner=runner,
                )
                post_repair_authority_task_ids[work_unit_id] = authority_task_id
                created_post_repair_authority_task_ids[work_unit_id] = authority_task_id
        for _task, _payload, task_id, _packet_id, work_unit_id, _status in retry_candidates:
            unlinked_parent_ids: list[str] = []
            authority_result = authority_results.get(work_unit_id)
            authority_task_ref = None
            if isinstance(authority_result, dict):
                authority_task_ref = str(authority_result.get("authority_task_ref") or "").strip() or None
            for superseded_parent_id in superseded_parent_candidates.get(work_unit_id, []):
                if unlink_task_dependency(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    parent_task_id=superseded_parent_id,
                    child_task_id=task_id,
                    work_unit_id=work_unit_id,
                    authority_task_ref=authority_task_ref,
                    runner=runner,
                ):
                    unlinked_parent_ids.append(superseded_parent_id)
            if unlinked_parent_ids:
                unlinked_superseded_parent_task_ids[work_unit_id] = unlinked_parent_ids
            current_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=task_id, runner=runner)
            current_status = task_readback_status(current_payload)
            if current_status == "blocked":
                unblock_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    task_id=task_id,
                    reason=retry_reason,
                    required_readback_markers=READY_WORK_UNIT_RECONCILIATION_RETRY_READBACK_MARKERS,
                    runner=runner,
                )
                unblocked_ready_work_unit_task_ids[work_unit_id] = task_id
                retry_ready_work_unit_task_ids[work_unit_id] = task_id
            elif current_status == "todo":
                promote_task(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    task_id=task_id,
                    reason=retry_reason,
                    required_readback_markers=READY_WORK_UNIT_RECONCILIATION_RETRY_READBACK_MARKERS,
                    runner=runner,
                )
                promoted_ready_work_unit_task_ids[work_unit_id] = task_id
                retry_ready_work_unit_task_ids[work_unit_id] = task_id
            elif current_status in {"ready", "running", "done"}:
                retry_ready_work_unit_task_ids[work_unit_id] = task_id
            else:
                raise RuntimeError(f"ready work-unit {work_unit_id} is not in a retryable state after supersession cleanup")
        for _task, task_id, packet_id, work_unit_id in complete_candidates:
            unlinked_parent_ids = []
            authority_result = authority_results.get(work_unit_id)
            authority_task_ref = None
            if isinstance(authority_result, dict):
                authority_task_ref = str(authority_result.get("authority_task_ref") or "").strip() or None
            for superseded_parent_id in superseded_parent_candidates.get(work_unit_id, []):
                if unlink_task_dependency(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    parent_task_id=superseded_parent_id,
                    child_task_id=task_id,
                    work_unit_id=work_unit_id,
                    authority_task_ref=authority_task_ref,
                    runner=runner,
                ):
                    unlinked_parent_ids.append(superseded_parent_id)
            if unlinked_parent_ids:
                unlinked_superseded_parent_task_ids[work_unit_id] = unlinked_parent_ids
            metadata = {
                "marker": "ready_work_unit_post_release_reconciliation",
                "work_unit_id": work_unit_id,
                "packet_id": packet_id,
                "ready_work_unit_done_authorized": True,
                "ready_work_unit_done_definition_satisfied": True,
                "ready_work_unit_repair_review_passed": True,
                "reconciliation_scope": "post_release_ready_work_unit",
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "complete_product_claim_allowed": False,
            }
            complete_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task_id=task_id,
                result=args.completion_result,
                summary=args.completion_summary,
                metadata=metadata,
                required_readback_markers=READY_WORK_UNIT_RECONCILIATION_DONE_READBACK_MARKERS,
                runner=runner,
            )
            completed_ready_work_unit_task_ids[work_unit_id] = task_id
        if (
            not args.dry_run
            and args.route_readiness is not None
            and not post_repair_review_candidates
            and not post_repair_authority_candidates
            and human_gate_count == 0
            and incomplete_count == 0
        ):
            followup_release_result = release_ready_work_units(
                argparse.Namespace(
                    plan=args.plan,
                    materialization_result=args.materialization_result,
                    board=board,
                    hermes_bin=args.hermes_bin,
                    worker_assignee_prefix=args.worker_assignee_prefix,
                    route_readiness=args.route_readiness,
                    reason=None,
                    dry_run=False,
                    out=None,
                ),
                runner=runner,
            )

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "reconcile-ready-work-units",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": {
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        "packet_task_ids": {
            packet_id: task_id
            for _task, _payload, task_id, packet_id, _work_unit_id, _status in verified
        },
        "retry_ready_work_unit_task_ids": retry_ready_work_unit_task_ids,
        "unblocked_ready_work_unit_task_ids": unblocked_ready_work_unit_task_ids,
        "completed_ready_work_unit_task_ids": completed_ready_work_unit_task_ids,
        "post_repair_review_task_ids": post_repair_review_task_ids,
        "existing_post_repair_review_task_ids": existing_post_repair_review_task_ids,
        "created_post_repair_review_task_ids": created_post_repair_review_task_ids,
        "post_repair_review_required_work_unit_ids": sorted(
            post_repair_review_required_work_unit_ids
        ),
        "post_repair_authority_task_ids": post_repair_authority_task_ids,
        "existing_post_repair_authority_task_ids": existing_post_repair_authority_task_ids,
        "created_post_repair_authority_task_ids": created_post_repair_authority_task_ids,
        "superseded_post_repair_review_parent_task_ids": superseded_parent_candidates,
        "unlinked_superseded_post_repair_review_parent_task_ids": unlinked_superseded_parent_task_ids,
        "post_repair_authority_required_work_unit_ids": sorted(
            post_repair_authority_required_work_unit_ids
        ),
        "promoted_ready_work_unit_task_ids": promoted_ready_work_unit_task_ids,
        "followup_release_result": followup_release_result,
        "post_release_reconciliation": reconciliation,
        "release_wave": {
            "held_work_unit_ids": sorted(dependency_blockers.keys()),
            "dependency_blockers": {key: dependency_blockers[key] for key in sorted(dependency_blockers)},
            "release_ready_work_units_required_next": bool(
                (retry_ready_work_unit_task_ids or completed_ready_work_unit_task_ids)
                and not (
                    isinstance(followup_release_result, dict)
                    and followup_release_result.get("released_ready_work_unit_task_ids")
                )
            ),
        },
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "reconciliation_verified_task_count": len(verified),
            "post_release_blocked_task_count": post_release_blocked_count,
            "retry_candidate_count": len(retry_candidates),
            "complete_candidate_count": len(complete_candidates),
            "post_repair_review_required_count": len(post_repair_review_required_work_unit_ids),
            "post_repair_review_missing_task_count": len(post_repair_review_candidates),
            "post_repair_review_existing_task_count": len(existing_post_repair_review_task_ids),
            "post_repair_review_result_count": post_repair_review_result_count,
            "post_repair_review_task_created_count": len(created_post_repair_review_task_ids),
            "post_repair_authority_required_count": len(post_repair_authority_required_work_unit_ids),
            "post_repair_authority_missing_task_count": len(post_repair_authority_candidates),
            "post_repair_authority_existing_task_count": len(existing_post_repair_authority_task_ids),
            "post_repair_authority_result_count": post_repair_authority_result_count,
            "post_repair_authority_task_created_count": len(created_post_repair_authority_task_ids),
            "superseded_post_repair_review_parent_count": sum(
                len(parent_ids) for parent_ids in superseded_parent_candidates.values()
            ),
            "superseded_post_repair_review_parent_unlinked_count": sum(
                len(parent_ids) for parent_ids in unlinked_superseded_parent_task_ids.values()
            ),
            "retry_unblocked_task_count": len(unblocked_ready_work_unit_task_ids),
            "retry_promoted_task_count": len(promoted_ready_work_unit_task_ids),
            "completed_task_count": len(completed_ready_work_unit_task_ids),
            "followup_release_task_count": len(
                (followup_release_result or {}).get("released_ready_work_unit_task_ids") or {}
            ),
            "human_gate_required_count": human_gate_count,
            "incomplete_repair_or_review_count": incomplete_count,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": bool(
                retry_ready_work_unit_task_ids
                or ((followup_release_result or {}).get("released_ready_work_unit_task_ids") or {})
            ),
            "complete_product_claim_allowed": False,
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "retry_reason": retry_reason,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def close_reviewed_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("reviewed ready work-unit closeout requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=plan,
        board=board,
    )
    tasks = expected_ready_work_unit_tasks(plan)
    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["blocked", "done"],
        runner=runner,
    )

    verified: list[tuple[dict[str, Any], dict[str, Any], str, str, str, str]] = []
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        if len(matches) != 1:
            raise RuntimeError(
                f"reviewed ready work-unit closeout expected exactly one active Hermes task for packet {key[0]} / work unit {key[1]}, found {len(matches)}"
            )
        task_id, packet_id, work_unit_id = verify_ready_work_unit_identity(
            payload=matches[0],
            plan_task=task,
            worker_assignee_prefix=args.worker_assignee_prefix,
        )
        verified.append((task, matches[0], task_id, packet_id, work_unit_id, task_readback_status(matches[0])))

    review_results = ready_work_unit_review_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit={
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )

    closeout: dict[str, dict[str, Any]] = {}
    complete_candidates: list[tuple[dict[str, Any], str, str, str, dict[str, Any]]] = []
    human_gate_count = 0
    blocked_review_count = 0
    awaiting_review_count = 0
    already_satisfied_count = 0
    for task, payload, task_id, packet_id, work_unit_id, status in verified:
        review_result = review_results.get(work_unit_id)
        row: dict[str, Any] = {
            "status": status,
            "task_ref": task_id,
            "packet_id": packet_id,
            "work_unit_id": work_unit_id,
            "release_record_seen": task_has_ready_work_unit_release_record(payload),
            "complete_product_claim_allowed": False,
            "review_result": review_result,
            "decision": "awaiting_review",
            "actionable_by_adapter": False,
            "next_action": "wait for independent-reviewer PASS/BLOCK for this exact ready work unit",
        }
        if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
            already_satisfied_count += 1
            row["decision"] = "already_satisfied"
            row["next_action"] = "no closeout needed"
        elif status != "blocked":
            row["decision"] = "wait_for_runtime_state"
            row["next_action"] = f"task is {status or 'unknown'}, not blocked"
        elif not row["release_record_seen"]:
            row["decision"] = "not_released_yet"
            row["next_action"] = "release-ready-work-units must release the task before review closeout"
        elif not review_result:
            awaiting_review_count += 1
        elif review_result.get("human_gate_required") is True:
            human_gate_count += 1
            row["decision"] = "human_gate_required"
            row["next_action"] = "wait for explicit human gate; no automatic closeout"
        elif review_result.get("blocked") is True:
            blocked_review_count += 1
            row["decision"] = "review_blocked"
            row["next_action"] = "route the independent-reviewer findings to the owning worker for repair"
        elif review_result.get("review_passed") is True:
            row["decision"] = "complete_parent"
            row["actionable_by_adapter"] = True
            row["next_action"] = "complete only this ready work unit through Hermes complete"
            complete_candidates.append((task, task_id, packet_id, work_unit_id, review_result))
        closeout[work_unit_id] = row

    completed_ready_work_unit_task_ids: dict[str, str] = {}
    if not args.dry_run:
        for _task, task_id, packet_id, work_unit_id, review_result in complete_candidates:
            metadata = {
                "marker": READY_WORK_UNIT_REVIEW_CLOSEOUT_MARKER,
                "work_unit_id": work_unit_id,
                "packet_id": packet_id,
                "ready_work_unit_review_passed": True,
                "review_task_ref": review_result.get("review_task_ref"),
                "review_verdict": review_result.get("verdict"),
                "reconciliation_scope": "reviewed_ready_work_unit",
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "complete_product_claim_allowed": False,
                "dispatch_allowed_by_this_step": False,
            }
            result = (
                args.completion_result
                or f"{READY_WORK_UNIT_REVIEW_PASSED_MARKER};work_unit_id={work_unit_id};scope=work_unit_only"
            )
            summary = (
                args.completion_summary
                or (
                    f"Ready work unit {work_unit_id} completed after independent review "
                    f"{review_result.get('review_task_ref') or 'review'} PASS; this grants no product/release/security/customer-ready/human-gate approval."
                )
            )
            complete_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task_id=task_id,
                result=result,
                summary=summary,
                metadata=metadata,
                required_readback_markers=READY_WORK_UNIT_REVIEW_CLOSEOUT_READBACK_MARKERS,
                runner=runner,
            )
            completed_ready_work_unit_task_ids[work_unit_id] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "close-reviewed-ready-work-units",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": {
            work_unit_id: task_id
            for _task, _payload, task_id, _packet_id, work_unit_id, _status in verified
        },
        "packet_task_ids": {
            packet_id: task_id
            for _task, _payload, task_id, packet_id, _work_unit_id, _status in verified
        },
        "completed_ready_work_unit_task_ids": completed_ready_work_unit_task_ids,
        "reviewed_ready_work_unit_closeout": closeout,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "reviewed_task_count": len(verified),
            "review_result_count": len(review_results),
            "complete_candidate_count": len(complete_candidates),
            "completed_task_count": len(completed_ready_work_unit_task_ids),
            "already_satisfied_count": already_satisfied_count,
            "awaiting_review_count": awaiting_review_count,
            "blocked_review_count": blocked_review_count,
            "human_gate_required_count": human_gate_count,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": False,
            "complete_product_claim_allowed": False,
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
            "closeout_scope": "ready_work_unit_only",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def release_readiness_review_has_parent_edge(
    *,
    parent_payload: dict[str, Any],
    review_payload: dict[str, Any],
    parent_task_id: str,
    review_task_id: str,
) -> bool:
    return (
        review_task_id in task_readback_parents(parent_payload)
        or review_task_id in task_readback_children(parent_payload)
        or parent_task_id in task_readback_parents(review_payload)
        or parent_task_id in task_readback_children(review_payload)
    )


def release_readiness_review_result_from_run(
    *,
    run: dict[str, Any],
    parent_task_id: str,
    review_task_id: str,
    expected_assignee: str = "independent-reviewer",
) -> dict[str, Any] | None:
    metadata = run.get("metadata")
    if not isinstance(metadata, dict):
        return None
    run_profile = str(run.get("profile") or run.get("assignee") or "").strip()
    if run_profile and run_profile not in {"independent-reviewer", expected_assignee}:
        return None
    if not review_metadata_targets_task(metadata, task_id=parent_task_id):
        return None
    review_result = metadata.get("independent_review_result")
    review_result = review_result if isinstance(review_result, dict) else {}
    verdict = str(review_result.get("verdict") or metadata.get("verdict") or "").strip().upper()
    status = str(run.get("status") or "").strip().lower()
    outcome = str(run.get("outcome") or "").strip().lower()
    required_fixes = review_result.get("required_fixes")
    required_fixes = required_fixes if isinstance(required_fixes, list) else []
    blocking_findings = metadata.get("blocking_findings")
    if blocking_findings is None:
        blocking_findings = review_result.get("blocking_findings")
    production_promotion_allowed = (
        metadata.get("production_promotion_allowed") is True
        or metadata.get("production_promotion_approved") is True
        or review_result.get("production_promotion_allowed") is True
        or review_result.get("production_promotion_approved") is True
    )
    complete_product_claim_allowed = (
        metadata.get("complete_product_claim_allowed") is True
        or review_result.get("complete_product_claim_allowed") is True
    )
    human_gate_required = (
        metadata.get("human_gate_required") is True
        or review_result.get("human_gate_required") is True
        or metadata.get("production_promotion_approved") == "human_gate_required"
        or review_result.get("production_promotion_approved") == "human_gate_required"
    )
    pass_result = (
        status in {"done", "complete", "completed"}
        and outcome in {"", "completed", "done", "pass", "passed", "success", "succeeded"}
        and verdict.startswith("PASS")
        and blocking_findings is not True
        and not required_fixes
    )
    blocked = (
        blocking_findings is True
        or status == "blocked"
        or outcome == "blocked"
        or verdict.startswith("BLOCK")
        or bool(required_fixes)
    )
    if not pass_result and not blocked and not human_gate_required and not production_promotion_allowed and not complete_product_claim_allowed:
        return None
    return {
        "marker": "release_readiness_review_result",
        "review_task_ref": review_task_id,
        "parent_task_ref": parent_task_id,
        "source": "hermes_run_metadata",
        "status": (
            "forbidden_approval_claim"
            if production_promotion_allowed or complete_product_claim_allowed
            else "human_gate_required"
            if human_gate_required
            else "passed"
            if pass_result
            else "blocked"
        ),
        "verdict": verdict or None,
        "review_passed": pass_result,
        "blocked": blocked and not pass_result,
        "human_gate_required": human_gate_required,
        "required_fix_count": len(required_fixes),
        "production_promotion_allowed": False,
        "complete_product_claim_allowed": False,
        "forbidden_approval_claim": production_promotion_allowed or complete_product_claim_allowed,
    }


def repair_release_readiness_review_parent_edge(
    *,
    hermes_bin: str,
    board: str,
    parent_task_id: str,
    review_task_id: str,
    runner: Runner = default_runner,
) -> bool:
    run_checked(hermes_kanban(hermes_bin, board, "link", review_task_id, parent_task_id), runner)
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            parent_task_id,
            compact_json_argument(
                {
                    "marker": RELEASE_READINESS_REVIEW_PARENT_EDGE_REPAIRED_MARKER,
                    "review_task_ref": review_task_id,
                    "parent_task_ref": parent_task_id,
                    "reason": "release-readiness review relationship was explicit in review metadata but missing as a durable Hermes edge",
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "production_promotion_allowed": False,
                    "complete_product_claim_allowed": False,
                }
            ),
        ),
        runner,
    )
    return True


def close_release_readiness_review(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    board = str(args.board or "").strip()
    parent_task_id = str(args.parent_task or "").strip()
    review_task_id = str(args.review_task or "").strip()
    if not board:
        raise RuntimeError("release readiness review closeout requires a board")
    if not parent_task_id:
        raise RuntimeError("release readiness review closeout requires --parent-task")
    if not review_task_id:
        raise RuntimeError("release readiness review closeout requires --review-task")

    parent_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=parent_task_id, runner=runner)
    review_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=review_task_id, runner=runner)
    parent_body = parse_json_object(task_readback_body(parent_payload))
    if parent_body.get("next_action") != "release_readiness_required":
        raise RuntimeError("parent task is not a release_readiness_required next-route task")

    parent_edge_present = release_readiness_review_has_parent_edge(
        parent_payload=parent_payload,
        review_payload=review_payload,
        parent_task_id=parent_task_id,
        review_task_id=review_task_id,
    )
    review_runs = task_run_records(
        hermes_bin=args.hermes_bin,
        board=board,
        task_id=review_task_id,
        runner=runner,
    )
    expected_assignee = str(args.worker_assignee_prefix or "") + "independent-reviewer"
    review_result: dict[str, Any] | None = None
    latest_sort_key = (0, 0)
    for run in review_runs:
        candidate = release_readiness_review_result_from_run(
            run=run,
            parent_task_id=parent_task_id,
            review_task_id=review_task_id,
            expected_assignee=expected_assignee,
        )
        if not candidate:
            continue
        run_id = int(run.get("id") or run.get("run_id") or 0)
        ended_at = int(run.get("ended_at") or run.get("finished_at") or run.get("started_at") or 0)
        sort_key = (ended_at, run_id)
        if sort_key >= latest_sort_key:
            latest_sort_key = sort_key
            review_result = candidate

    parent_edge_repaired = False
    if not parent_edge_present and review_result and args.repair_missing_parent_edge and not args.dry_run:
        repair_release_readiness_review_parent_edge(
            hermes_bin=args.hermes_bin,
            board=board,
            parent_task_id=parent_task_id,
            review_task_id=review_task_id,
            runner=runner,
        )
        parent_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=parent_task_id, runner=runner)
        review_payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=review_task_id, runner=runner)
        parent_edge_present = release_readiness_review_has_parent_edge(
            parent_payload=parent_payload,
            review_payload=review_payload,
            parent_task_id=parent_task_id,
            review_task_id=review_task_id,
        )
        parent_edge_repaired = parent_edge_present

    parent_status = task_readback_status(parent_payload)
    decision = "awaiting_review"
    next_action = "wait for independent-reviewer PASS/BLOCK for this exact release-readiness packet"
    actionable = False
    blocked_review_count = 0
    human_gate_count = 0
    if parent_status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
        decision = "already_satisfied"
        next_action = "no closeout needed"
    elif not parent_edge_present:
        decision = "missing_durable_parent_edge"
        next_action = "repair durable Hermes parent/dependency edge before consuming review result"
    elif not review_result:
        decision = "awaiting_review"
    elif review_result.get("forbidden_approval_claim") is True:
        decision = "forbidden_approval_claim"
        next_action = "reject review result that claims product completion or production promotion"
        blocked_review_count = 1
    elif review_result.get("human_gate_required") is True:
        decision = "human_gate_required"
        next_action = "wait for explicit human promotion gate; no automatic release closeout"
        human_gate_count = 1
    elif review_result.get("blocked") is True:
        decision = "repair_required"
        next_action = "route release-readiness packet back to release-ops-worker repair/retry"
        blocked_review_count = 1
    elif review_result.get("review_passed") is True:
        decision = "release_readiness_review_passed"
        next_action = "complete release-readiness packet only; production promotion remains separately blocked"
        actionable = parent_status == "blocked"

    completed_release_readiness_task_ids: dict[str, str] = {}
    if actionable and not args.dry_run:
        metadata = {
            "marker": RELEASE_READINESS_REVIEW_CLOSEOUT_MARKER,
            RELEASE_READINESS_REVIEW_PASSED_MARKER: True,
            "review_task_ref": review_task_id,
            "parent_task_ref": parent_task_id,
            "review_result": review_result,
            "release_readiness_scope": "packet_only",
            "production_promotion_allowed": False,
            "complete_product_claim_allowed": False,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "dispatch_allowed_by_this_step": False,
        }
        complete_task(
            hermes_bin=args.hermes_bin,
            board=board,
            task_id=parent_task_id,
            result=f"{RELEASE_READINESS_REVIEW_PASSED_MARKER};scope=release_readiness_packet_only",
            summary=(
                "Release readiness packet accepted after independent-reviewer PASS; "
                "production/customer/mainnet promotion remains blocked and unapproved."
            ),
            metadata=metadata,
            required_readback_markers=RELEASE_READINESS_REVIEW_CLOSEOUT_READBACK_MARKERS,
            runner=runner,
        )
        completed_release_readiness_task_ids["release_readiness"] = parent_task_id

    closeout = {
        "$schema": "https://overkill-factory.dev/schemas/release-readiness-review-closeout.schema.json",
        "record_type": "release_readiness_review_closeout",
        "parent_task_ref": parent_task_id,
        "review_task_ref": review_task_id,
        "decision": decision,
        "next_action": next_action,
        "parent_status": parent_status,
        "review_status": task_readback_status(review_payload),
        "parent_edge_present": parent_edge_present,
        "parent_edge_repaired": parent_edge_repaired,
        "review_result": review_result,
        "production_promotion_allowed": False,
        "complete_product_claim_allowed": False,
        "dispatch_allowed_by_this_step": False,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }
    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "close-release-readiness-review",
        "dry_run": bool(args.dry_run),
        "board": board,
        "release_readiness_review_closeout": closeout,
        "completed_release_readiness_task_ids": completed_release_readiness_task_ids,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "review_result_count": 1 if review_result else 0,
            "complete_candidate_count": 1 if actionable else 0,
            "completed_task_count": len(completed_release_readiness_task_ids),
            "blocked_review_count": blocked_review_count,
            "human_gate_required_count": human_gate_count,
            "parent_edge_present": parent_edge_present,
            "parent_edge_repaired": parent_edge_repaired,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": False,
            "production_promotion_allowed": False,
            "complete_product_claim_allowed": False,
        },
        "hook": {
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
            "closeout_scope": "release_readiness_review_only",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def active_product_creation_work_units(product_creation_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    active: dict[str, dict[str, Any]] = {}
    for unit in product_creation_plan.get("work_units", []):
        if not isinstance(unit, dict):
            continue
        unit_id = str(unit.get("unit_id") or "").strip()
        status = str(unit.get("status") or "").strip().lower()
        if not unit_id or status in {"rejected", "superseded"}:
            continue
        active[unit_id] = unit
    return active


def work_unit_materialization_tasks_by_id(materialization_plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    tasks: dict[str, dict[str, Any]] = {}
    for task in materialization_plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        work_unit_id = str(task.get("work_unit_id") or "").strip()
        if work_unit_id:
            tasks[work_unit_id] = task
    return tasks


def product_creation_embedded_plan_ids(materialization_plan: dict[str, Any]) -> set[str]:
    plan_ids: set[str] = set()
    for task in materialization_plan.get("tasks", []):
        if not isinstance(task, dict):
            continue
        body = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
        packet = body.get("work_unit_context_packet") if isinstance(body.get("work_unit_context_packet"), dict) else {}
        embedded = packet.get("embedded_payloads") if isinstance(packet.get("embedded_payloads"), dict) else {}
        product_plan = embedded.get("product_creation_plan") if isinstance(embedded.get("product_creation_plan"), dict) else {}
        plan_id = str(product_plan.get("plan_id") or "").strip()
        if plan_id:
            plan_ids.add(plan_id)
    return plan_ids


def product_creation_closeout_next_action(
    *,
    product_creation_plan: dict[str, Any],
    release_readiness_ref: str | None,
    product_delivery_ref: str | None,
    product_promotion_gate_ref: str | None,
    learnback_ref: str | None,
    blocker_decisions: list[str],
) -> str:
    if any(decision == "human_gate_required" for decision in blocker_decisions):
        return "human_gate_required"
    if any(decision == "repair_required" for decision in blocker_decisions):
        return "repair_required"
    if blocker_decisions:
        return "blocked_with_owner"
    if not release_readiness_ref and product_creation_plan.get("production_readiness_scope"):
        return "release_readiness_required"
    if product_creation_plan.get("complete_product_required") is True and not product_delivery_ref:
        return "material_product_execution_required"
    if not learnback_ref:
        return "learnback_required"
    if product_promotion_gate_ref:
        return "product_closeout_ready"
    return "product_promotion_gate_required"


def product_creation_closeout_next_assignee(next_action: str, override: str | None) -> str:
    explicit = str(override or "").strip()
    if explicit:
        return explicit
    if next_action == "release_readiness_required":
        return "release-ops-worker"
    if next_action == "learnback_required":
        return "skill-eval-distiller"
    return "factory-orchestrator"


def product_creation_closeout_idempotency_key(
    *,
    product_creation_plan_id: str,
    materialization_plan_id: str,
    next_action: str,
) -> str:
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "product_creation_plan_id": product_creation_plan_id,
                "materialization_plan_id": materialization_plan_id,
                "next_action": next_action,
                "marker": PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
                "no_spawn_protocol": "create-unassigned-block-assign-v3",
                "next_task_contract_version": "worker-consumable-v1",
                "idempotency_version": "v3",
            }
        )
    )
    return f"overkill:product-creation-closeout:{product_creation_plan_id}:{next_action}:{digest}"


def product_creation_next_route_contract(next_action: str, closeout: dict[str, Any]) -> dict[str, Any]:
    product_creation_plan_id = str(closeout.get("product_creation_plan_id") or "product-creation-plan")
    materialization_plan_id = str(closeout.get("materialization_plan_id") or "ready-work-unit-plan")
    common = {
        "source_refs": [
            f"product-creation-plan:{product_creation_plan_id}",
            f"ready-work-unit-materialization:{materialization_plan_id}",
            f"product-creation-closeout:{next_action}",
        ],
        "forbidden_actions": [
            "complete_product_claim",
            "production_release_approval",
            "customer_ready_claim",
            "deploy",
            "infrastructure_mutation",
            "secret_access",
            "private_evidence_publication",
            "raw_self_validation_log_publication",
            "local_path_publication",
        ],
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
            "private_runtime_refs_must_be_summarized": True,
        },
    }
    if next_action == "learnback_required":
        return {
            **common,
            "done_definition": [
                "classify self-validation outcomes into public-safe factory learnings",
                "identify systemic gaps, rejected non-gaps, and already-fixed gaps",
                "create or update public-safe improvement issues only when a real factory gap remains",
                "leave product completion, production promotion, deploy, and customer-ready claims forbidden",
                "complete only when learnback result includes owner, decision, evidence class, and next action",
            ],
            "evidence_expected": [
                "product creation closeout summary",
                "release readiness closeout summary",
                "work-unit aggregate coverage",
                "blocker and repair history classification",
                "worker feedback and runtime contract gaps",
                "public-safe issue/proposal refs for remaining factory improvements",
            ],
            "output_contract": {
                "receipt_field": "learnback_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": [
                    "public-safe learnback summary",
                    "gap classification",
                    "remaining issue refs or explicit no-new-gap rationale",
                    "no private evidence embedded",
                ],
                "block_requires": ["owner", "reason", "missing_contract_fields", "next_repair_action"],
                "may_create_public_safe_issue": True,
            },
        }
    if next_action == "release_readiness_required":
        return {
            **common,
            "done_definition": [
                "prepare release readiness packet",
                "state smoke, rollback, monitoring, support, human gate and promotion blockers",
                "create independent review route when review is required",
                "do not approve production promotion",
            ],
            "evidence_expected": [
                "release plan",
                "smoke result or reason blocked",
                "rollback plan",
                "monitoring/support plan",
                "human promotion gate status",
                "visible blockers with owner and next action",
            ],
            "output_contract": {
                "receipt_field": "release_ops_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": ["release readiness packet", "promotion blockers remain explicit"],
                "block_requires": ["owner", "reason", "next_repair_action"],
                "production_promotion_allowed": False,
            },
        }
    if next_action == "material_product_execution_required":
        return {
            **common,
            "forbidden_actions": common["forbidden_actions"]
            + [
                "create_loose_material_product_tasks",
                "create_todo_or_ready_material_product_tasks",
                "dispatch_material_product_workers_without_blocked_graph",
                "route_material_product_execution_without_dependency_edges",
            ],
            "material_product_execution_graph_contract": {
                "materialization_protocol": "create-unassigned-default-block-assign-v2",
                "deterministic_graph_required": True,
                "blocked_event_required_before_any_worker_dispatch": True,
                "create_sequence": [
                    "create_task_without_assignee",
                    "block_task_with_durable_event",
                    "verify_blocked_event_in_show_json",
                    "assign_target_worker_after_block_readback",
                    "link_dependency_edges_before_release",
                    "keep_each_material_task_blocked_until_runtime_gate",
                ],
                "required_nodes": [
                    "execution_packet",
                    "implementation",
                    "product_face_result",
                    "qa_verification",
                    "public_safety_gate",
                    "appsec_gate",
                    "independent_review",
                    "delivery_handoff",
                    "post_handoff_closeout_reconciliation",
                ],
                "required_edges": [
                    {"from": "execution_packet", "to": "implementation"},
                    {"from": "implementation", "to": "product_face_result"},
                    {"from": "implementation", "to": "qa_verification"},
                    {"from": "implementation", "to": "public_safety_gate"},
                    {"from": "implementation", "to": "appsec_gate"},
                    {"from": "product_face_result", "to": "qa_verification"},
                    {"from": "product_face_result", "to": "public_safety_gate"},
                    {"from": "product_face_result", "to": "appsec_gate"},
                    {"from": "qa_verification", "to": "independent_review"},
                    {"from": "public_safety_gate", "to": "independent_review"},
                    {"from": "appsec_gate", "to": "independent_review"},
                    {"from": "independent_review", "to": "delivery_handoff"},
                    {"from": "delivery_handoff", "to": "post_handoff_closeout_reconciliation"},
                ],
                "node_authority_rules": {
                    "implementation": {
                        "allowed_after_runtime_gate": ["build_or_repair_scoped_artifact"],
                        "forbidden_actions_must_not_include": ["implement_product"],
                        "replacement_for_broad_implementation_forbid": "implement_product_outside_scope",
                        "forbidden_actions_still_required": [
                            "complete_product_claim",
                            "production_release_approval",
                            "customer_ready_claim",
                            "deploy",
                            "infrastructure_mutation",
                            "secret_access",
                            "private_evidence_publication",
                            "raw_self_validation_log_publication",
                            "local_path_publication",
                        ],
                    }
                },
                "pass_requires": [
                    "blocked_dependency_graph_ref",
                    "no_spawn_readback_evidence",
                    "task_ids_by_required_node",
                    "dependency_edges_readback",
                    "each_task_has_blocked_event_before_assignment_or_dispatch",
                ],
                "block_requires": [
                    "owner",
                    "reason",
                    "missing_graph_node_or_edge",
                    "next_repair_action",
                ],
            },
            "done_definition": [
                "route material product implementation before any promotion gate",
                "create the material execution graph with verified blocked/no-spawn readback before any worker dispatch",
                "create or repair executable product work units instead of treating planning readiness as product completion",
                "require product delivery proof before learnback or product promotion can close the product",
                "after material delivery handoff PASS, emit an explicit closeout next route",
                "do not claim complete product, production release, deploy, or customer-ready status",
            ],
            "evidence_expected": [
                "executable product artifact or product delivery proof bundle",
                "Product Face Result for visible surfaces with states, journeys, screenshots and viewport evidence",
                "implementation verification commands and results",
                "public-safe evidence refs for product delivery proof",
            ],
            "output_contract": {
                "receipt_field": "material_product_execution_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": [
                    "product_delivery_ref",
                    "executable product proof",
                    "Product Face Result when visible surface exists",
                    "verification evidence refs",
                    "blocked_dependency_graph_ref",
                    "no_spawn_readback_evidence",
                    "post_material_handoff_closeout_route_ref",
                    "remaining release/promotion blockers acknowledged",
                ],
                "block_requires": ["owner", "reason", "next_repair_action"],
                "complete_product_claim_allowed": False,
                "production_promotion_allowed": False,
            },
        }
    if next_action == "product_promotion_gate_required":
        return {
            **common,
            "done_definition": [
                "obtain or record an explicit product promotion human gate",
                "verify release readiness and learnback refs are present before asking for promotion",
                "block with owner, reason, and next action if the human gate is absent or denied",
                "do not claim complete product, production release, deploy, or customer-ready status",
            ],
            "evidence_expected": [
                "product creation closeout summary",
                "release readiness reviewed ref",
                "learnback reviewed ref",
                "explicit product promotion human gate decision",
            ],
            "output_contract": {
                "receipt_field": "product_promotion_gate_result",
                "allowed_results": ["PASS", "BLOCK"],
                "pass_requires": [
                    "product_promotion_gate_ref",
                    "public-safe gate decision",
                    "decision authority",
                    "promotion scope",
                    "remaining forbidden actions acknowledged",
                ],
                "block_requires": ["owner", "reason", "next_repair_action"],
                "complete_product_claim_allowed": False,
                "production_promotion_allowed": False,
            },
        }
    return {
        **common,
        "done_definition": [
            "consume the product creation closeout next action",
            "produce a public-safe result or block with owner, reason and next action",
        ],
        "evidence_expected": ["product creation closeout summary", "blocker inventory", "next action decision"],
        "output_contract": {
            "allowed_results": ["PASS", "BLOCK"],
            "block_requires": ["owner", "reason", "next_repair_action"],
        },
    }


def create_product_creation_closeout_next_task(
    *,
    args: argparse.Namespace,
    board: str,
    closeout: dict[str, Any],
    runner: Runner,
) -> str:
    next_action = str(closeout.get("next_action") or "blocked_with_owner")
    assignee = product_creation_closeout_next_assignee(next_action, args.next_assignee)
    product_creation_plan_id = str(closeout.get("product_creation_plan_id") or "product-creation-plan")
    materialization_plan_id = str(closeout.get("materialization_plan_id") or "ready-work-unit-plan")
    body = compact_json_argument(
        {
            "packet_type": "product_creation_run_closeout_next_action",
            "marker": PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
            "product_creation_plan_id": product_creation_plan_id,
            "materialization_plan_id": materialization_plan_id,
            "next_action": next_action,
            "decision": closeout.get("decision"),
            "work_unit_count": closeout.get("work_unit_count"),
            "terminal_work_unit_count": closeout.get("terminal_work_unit_count"),
            "review_passed_work_unit_count": closeout.get("review_passed_work_unit_count"),
            "blocker_count": len(closeout.get("blockers") or []),
            "blockers": closeout.get("blockers") or [],
            "proof_id_coverage": closeout.get("proof_id_coverage") or {},
            "requirement_coverage": closeout.get("requirement_coverage") or {},
            "complete_product_claim_allowed": False,
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "dispatch_allowed_by_this_step": False,
            **product_creation_next_route_contract(next_action, closeout),
        }
    )
    task_id = create_blocked_task_before_assignment(
        hermes_bin=args.hermes_bin,
        board=board,
        title=f"OF product creation closeout next gate: {next_action}",
        body=body,
        assignee=assignee,
        idempotency_key=product_creation_closeout_idempotency_key(
            product_creation_plan_id=product_creation_plan_id,
            materialization_plan_id=materialization_plan_id,
            next_action=next_action,
        ),
        created_by="overkill-factory",
        workspace=str(args.workspace or "scratch"),
        blocked_reason=(
            "Product creation closeout next-route task starts blocked; "
            "dispatch is forbidden until the next gate has explicit authority."
        ),
        runner=runner,
    )
    run_checked(
        hermes_kanban(
            args.hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECONCILIATION_AUTHOR,
            task_id,
            compact_json_argument(
                {
                    "marker": PRODUCT_CREATION_CLOSEOUT_MARKER,
                    "next_route_marker": PRODUCT_CREATION_CLOSEOUT_NEXT_ROUTE_MARKER,
                    "product_creation_plan_id": product_creation_plan_id,
                    "materialization_plan_id": materialization_plan_id,
                    "next_action": next_action,
                    "complete_product_claim_allowed": False,
                    "dispatch_allowed_by_this_step": False,
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                }
            ),
        ),
        runner,
    )
    payload = show_task(hermes_bin=args.hermes_bin, board=board, task_id=task_id, runner=runner)
    if task_readback_status(payload) != "blocked":
        raise RuntimeError(f"product creation closeout next-route task {task_id} is not durably blocked")
    if not history_contains_all_markers_anywhere(payload, PRODUCT_CREATION_CLOSEOUT_READBACK_MARKERS):
        raise RuntimeError(f"product creation closeout next-route task {task_id} lacks closeout readback markers")
    return task_id


def close_product_creation_run(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    product_creation_plan = load_product_creation_plan(args.product_creation_plan.resolve())
    materialization_plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or materialization_plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("product creation closeout requires a board")
    if str(materialization_plan.get("board") or "").strip() and board != str(materialization_plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=materialization_plan,
        board=board,
    )
    release_readiness_ref = ensure_public_safe_optional_ref(args.release_readiness_ref, field="release_readiness_ref")
    product_delivery_ref = ensure_public_safe_optional_ref(args.product_delivery_ref, field="product_delivery_ref")
    product_promotion_gate_ref = ensure_public_safe_optional_ref(
        args.product_promotion_gate_ref,
        field="product_promotion_gate_ref",
    )
    learnback_ref = ensure_public_safe_optional_ref(args.learnback_ref, field="learnback_ref")

    product_creation_plan_id = str(product_creation_plan.get("plan_id") or "").strip()
    materialization_plan_id = str(materialization_plan.get("plan_id") or "").strip()
    embedded_plan_ids = product_creation_embedded_plan_ids(materialization_plan)
    active_units = active_product_creation_work_units(product_creation_plan)
    materialized_tasks = work_unit_materialization_tasks_by_id(materialization_plan)
    expected_unit_ids = set(active_units)
    materialized_unit_ids = set(materialized_tasks)

    closeout_blockers: list[dict[str, Any]] = []
    if embedded_plan_ids and product_creation_plan_id not in embedded_plan_ids:
        closeout_blockers.append(
            {
                "blocker_id": "product_creation_plan_mismatch",
                "owner": "factory-orchestrator",
                "reason": "materialized ready work units embed a different Product Creation Plan id",
                "next_repair_action": "refresh ready work-unit packets from the canonical Product Creation Plan",
            }
        )
    missing_materialized_units = sorted(expected_unit_ids - materialized_unit_ids)
    extra_materialized_units = sorted(materialized_unit_ids - expected_unit_ids)
    if missing_materialized_units:
        closeout_blockers.append(
            {
                "blocker_id": "missing_materialized_work_units",
                "owner": "factory-orchestrator",
                "reason": "not every active Product Creation Plan work unit was materialized",
                "work_unit_ids": missing_materialized_units,
                "next_repair_action": "materialize missing ready work units or refresh the Product Creation Plan",
            }
        )
    if extra_materialized_units:
        closeout_blockers.append(
            {
                "blocker_id": "extra_materialized_work_units",
                "owner": "factory-orchestrator",
                "reason": "materialization plan contains work units outside the active Product Creation Plan",
                "work_unit_ids": extra_materialized_units,
                "next_repair_action": "supersede stale runtime tasks or refresh the canonical Product Creation Plan",
            }
        )

    all_candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["blocked", "ready", "running", "todo", "done"],
        include_superseded=True,
        runner=runner,
    )

    unit_rows: dict[str, dict[str, Any]] = {}
    verified_parent_task_ids: dict[str, str] = {}
    for work_unit_id in sorted(expected_unit_ids):
        unit = active_units[work_unit_id]
        task = materialized_tasks.get(work_unit_id)
        packet_id = str((task or {}).get("packet_id") or "").strip()
        matches = all_candidates.get((packet_id, work_unit_id), []) if packet_id else []
        active_matches = [payload for payload in matches if not task_has_ready_work_unit_supersession(payload)]
        superseded_count = len(matches) - len(active_matches)
        row: dict[str, Any] = {
            "work_unit_id": work_unit_id,
            "packet_id": packet_id,
            "proof_ids_required": string_list(unit.get("proof_ids_required")),
            "product_sot_requirement_refs": string_list(unit.get("product_sot_requirement_refs")),
            "active_task_count": len(active_matches),
            "superseded_task_count": superseded_count,
            "status": "missing_runtime_task",
            "review_passed": False,
            "terminal": False,
            "decision": "blocked_with_owner",
            "next_action": "repair runtime materialization for this work unit",
        }
        if not task:
            row["blocker_id"] = "not_in_materialization_plan"
        elif len(active_matches) != 1:
            row["blocker_id"] = "ambiguous_or_missing_active_ready_work_unit"
            row["next_action"] = "ensure exactly one non-superseded Hermes task represents this work unit"
        else:
            payload = active_matches[0]
            task_id, _packet_id, _work_unit_id = verify_ready_work_unit_identity(
                payload=payload,
                plan_task=task,
                worker_assignee_prefix=args.worker_assignee_prefix,
            )
            status = task_readback_status(payload)
            release_record_seen = task_has_ready_work_unit_release_record(payload)
            row.update(
                {
                    "task_ref": task_id,
                    "status": status,
                    "release_record_seen": release_record_seen,
                    "terminal": status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES,
                }
            )
            if not release_record_seen:
                row["blocker_id"] = "missing_release_record"
                row["decision"] = "blocked_with_owner"
                row["next_action"] = "route through release-ready-work-units before product closeout"
            else:
                verified_parent_task_ids[work_unit_id] = task_id
                if status in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES:
                    row["decision"] = "awaiting_review_readback"
                    row["next_action"] = "verify exact independent-reviewer PASS metadata"
                elif history_contains_any_marker(payload, READY_WORK_UNIT_HUMAN_GATE_MARKERS):
                    row["decision"] = "human_gate_required"
                    row["blocker_id"] = "human_gate_required"
                    row["next_action"] = "wait for explicit human gate"
                elif status == "blocked":
                    row["decision"] = "repair_required"
                    row["blocker_id"] = "work_unit_blocked"
                    row["next_action"] = "route blocker to owner worker for repair/retry"
                else:
                    row["decision"] = "blocked_with_owner"
                    row["blocker_id"] = "work_unit_not_terminal"
                    row["next_action"] = "wait for Hermes terminal state or route repair"
        unit_rows[work_unit_id] = row

    review_results = ready_work_unit_review_results_by_work_unit(
        hermes_bin=args.hermes_bin,
        board=board,
        parent_task_ids_by_work_unit=verified_parent_task_ids,
        worker_assignee_prefix=args.worker_assignee_prefix,
        runner=runner,
    )
    for work_unit_id, review_result in review_results.items():
        row = unit_rows.get(work_unit_id)
        if not row:
            continue
        row["review_result"] = review_result
        if review_result.get("human_gate_required") is True:
            row["decision"] = "human_gate_required"
            row["blocker_id"] = "human_gate_required"
            row["next_action"] = "wait for explicit human gate"
        elif review_result.get("blocked") is True:
            row["decision"] = "repair_required"
            row["blocker_id"] = "review_blocked"
            row["next_action"] = "route independent-reviewer findings to owner worker"
        elif row.get("terminal") is True and review_result.get("review_passed") is True:
            row["review_passed"] = True
            row["decision"] = "work_unit_closed"
            row["next_action"] = "aggregate into product-level closeout only"

    blocker_decisions: list[str] = []
    proof_id_coverage: dict[str, dict[str, Any]] = {}
    requirement_coverage: dict[str, dict[str, Any]] = {}
    for work_unit_id, row in unit_rows.items():
        decision = str(row.get("decision") or "")
        if decision != "work_unit_closed":
            blocker_decisions.append(decision or "blocked_with_owner")
            closeout_blockers.append(
                {
                    "blocker_id": str(row.get("blocker_id") or f"{work_unit_id}_not_closed"),
                    "owner": str(active_units.get(work_unit_id, {}).get("owner_worker") or "factory-orchestrator"),
                    "work_unit_id": work_unit_id,
                    "reason": str(row.get("next_action") or "work unit is not ready for product-level closeout"),
                    "next_repair_action": str(row.get("next_action") or "route repair"),
                }
            )
        for proof_id in row.get("proof_ids_required") or []:
            proof_row = proof_id_coverage.setdefault(
                proof_id,
                {"proof_id": proof_id, "work_unit_ids": [], "status": "covered_by_review_pass"},
            )
            proof_row["work_unit_ids"].append(work_unit_id)
            if decision != "work_unit_closed":
                proof_row["status"] = "blocked_or_unproven"
        for requirement_ref in row.get("product_sot_requirement_refs") or []:
            req_row = requirement_coverage.setdefault(
                requirement_ref,
                {"requirement_ref": requirement_ref, "work_unit_ids": [], "status": "covered_by_closed_work_unit"},
            )
            req_row["work_unit_ids"].append(work_unit_id)
            if decision != "work_unit_closed":
                req_row["status"] = "blocked_or_unproven"

    next_action = product_creation_closeout_next_action(
        product_creation_plan=product_creation_plan,
        release_readiness_ref=release_readiness_ref,
        product_delivery_ref=product_delivery_ref,
        product_promotion_gate_ref=product_promotion_gate_ref,
        learnback_ref=learnback_ref,
        blocker_decisions=blocker_decisions,
    )
    terminal_count = sum(1 for row in unit_rows.values() if row.get("terminal") is True)
    review_passed_count = sum(1 for row in unit_rows.values() if row.get("review_passed") is True)
    closeout = {
        "$schema": "https://overkill-factory.dev/schemas/product-creation-run-closeout.schema.json",
        "record_type": "product_creation_run_closeout",
        "product_creation_plan_id": product_creation_plan_id,
        "materialization_plan_id": materialization_plan_id,
        "decision": next_action,
        "next_action": next_action,
        "complete_product_claim_allowed": False,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "dispatch_allowed_by_this_step": False,
        "work_unit_count": len(unit_rows),
        "terminal_work_unit_count": terminal_count,
        "review_passed_work_unit_count": review_passed_count,
        "blockers": closeout_blockers,
        "work_units": unit_rows,
        "proof_id_coverage": proof_id_coverage,
        "requirement_coverage": requirement_coverage,
        "release_readiness_ref": release_readiness_ref,
        "product_delivery_ref": product_delivery_ref,
        "product_promotion_gate_ref": product_promotion_gate_ref,
        "learnback_ref": learnback_ref,
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
        },
    }

    next_route_task_ids: dict[str, str] = {}
    if not args.dry_run:
        task_id = create_product_creation_closeout_next_task(
            args=args,
            board=board,
            closeout=closeout,
            runner=runner,
        )
        next_route_task_ids[next_action] = task_id

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "close-product-creation-run",
        "dry_run": bool(args.dry_run),
        "board": board,
        "materialization_plan_id": materialization_plan_id,
        "product_creation_plan_id": product_creation_plan_id,
        "ready_work_unit_task_ids": {
            work_unit_id: str(row.get("task_ref") or "")
            for work_unit_id, row in unit_rows.items()
            if row.get("task_ref")
        },
        "product_creation_run_closeout": closeout,
        "product_creation_next_route_task_ids": next_route_task_ids,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "work_unit_count": len(unit_rows),
            "terminal_work_unit_count": terminal_count,
            "review_passed_work_unit_count": review_passed_count,
            "blocker_count": len(closeout_blockers),
            "next_action": next_action,
            "dispatch_allowed_by_this_step": False,
            "native_dispatch_required_next": False,
            "complete_product_claim_allowed": False,
            "next_route_task_created_count": len(next_route_task_ids),
        },
        "hook": {
            "product_creation_plan": product_creation_plan,
            "materialization_plan": materialization_plan,
            "materialization_result": materialization_result,
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
            "closeout_scope": "product_creation_run",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def ready_work_unit_replacement_idempotency_key(
    *, plan_task: dict[str, Any], contaminated_task_ids: list[str]
) -> str:
    base = str(plan_task.get("idempotency_key") or "").strip()
    if not base:
        _packet_id, work_unit_id = expected_ready_work_unit_key(plan_task)
        base = f"overkill:ready-work-unit:{work_unit_id}"
    digest = idempotency_digest_fragment(
        contract_digest(
            {
                "base_idempotency_key": base,
                "contaminated_task_ids": sorted(contaminated_task_ids),
                "recovery_marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
                "version": "v1",
            }
        )
    )
    return f"{base}:supersedes:{digest}"


def replacement_ready_work_unit_task(
    *,
    plan_task: dict[str, Any],
    contaminated_task_ids: list[str],
    contamination_markers: list[str],
) -> dict[str, Any]:
    replacement = copy.deepcopy(plan_task)
    replacement["idempotency_key"] = ready_work_unit_replacement_idempotency_key(
        plan_task=plan_task,
        contaminated_task_ids=contaminated_task_ids,
    )
    title = str(replacement.get("title") or "").strip()
    if title and " clean replacement" not in title:
        replacement["title"] = f"{title} clean replacement"
    body = replacement.get("body_contract") if isinstance(replacement.get("body_contract"), dict) else {}
    body["runtime_lineage"] = {
        "lineage_type": "ready_work_unit_supersession",
        "supersedes_runtime_task_refs": sorted(contaminated_task_ids),
        "supersession_marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
        "contamination_markers": sorted(set(contamination_markers)),
        "complete_product_claim_allowed": False,
    }
    body["supersedes_runtime_task_refs"] = sorted(contaminated_task_ids)
    body["complete_product_claim_allowed"] = False
    replacement["body_contract"] = body
    replacement["work_unit_context_packet"] = body.get("work_unit_context_packet")
    return replacement


def mark_ready_work_unit_superseded(
    *,
    hermes_bin: str,
    board: str,
    task_id: str,
    replacement_task_id: str | None,
    work_unit_id: str,
    contamination_markers: list[str],
    runner: Runner = default_runner,
) -> None:
    payload = show_task(hermes_bin=hermes_bin, board=board, task_id=task_id, runner=runner)
    if task_readback_status(payload) != "blocked":
        ensure_blocked_event(
            hermes_bin=hermes_bin,
            board=board,
            task_id=task_id,
            reason=(
                "Ready work-unit superseded after pre-dispatch runtime activity; "
                "preserve history and use the clean replacement lineage."
            ),
            kind=DEFAULT_RUNTIME_GATE_BLOCK_KIND,
            runner=runner,
        )
    comment = compact_json_argument(
        {
            "marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
            "work_unit_id": work_unit_id,
            "replacement_task_ref": replacement_task_id or "planned-clean-replacement",
            "contamination_markers": sorted(set(contamination_markers)),
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "complete_product_claim_allowed": False,
            "reason": "superseded contaminated ready work-unit runtime lineage; clean replacement required",
        }
    )
    run_checked(
        hermes_kanban(
            hermes_bin,
            board,
            "comment",
            "--author",
            READY_WORK_UNIT_RECOVERY_AUTHOR,
            task_id,
            comment,
        ),
        runner,
    )


def recover_ready_work_units(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    plan = load_ready_work_unit_materialization_plan(args.plan.resolve())
    board = str(args.board or plan.get("board") or "").strip()
    if not board:
        raise RuntimeError("ready work-unit recovery requires a board")
    if str(plan.get("board") or "").strip() and board != str(plan.get("board") or "").strip():
        raise RuntimeError("provided board does not match the ready work-unit materialization plan")
    materialization_result = load_ready_work_unit_materialization_result(
        args.materialization_result.resolve(),
        plan=plan,
        board=board,
    )
    tasks = expected_ready_work_unit_tasks(plan)
    required_workers = [
        ready_work_unit_release_assignee(task, args.worker_assignee_prefix)
        for task in tasks
    ]
    if args.create_replacements:
        readiness_blockers = route_readiness_blockers(args.route_readiness, required_workers)
        if readiness_blockers:
            raise RuntimeError(
                "pre-dispatch route readiness blocked ready work-unit recovery: " + "; ".join(readiness_blockers)
            )

    candidates = ready_work_unit_readbacks_by_status(
        hermes_bin=args.hermes_bin,
        board=board,
        statuses=["blocked", "ready", "running", "todo", "triage"],
        include_superseded=True,
        runner=runner,
    )
    dependencies = ready_work_unit_dependencies(tasks)
    active_status_by_work_unit: dict[str, str] = {}
    for task in tasks:
        key = expected_ready_work_unit_key(task)
        matches = candidates.get(key) or []
        active_matches = [
            payload for payload in matches if not task_has_ready_work_unit_supersession(payload)
        ]
        if active_matches:
            active_status_by_work_unit[key[1]] = task_readback_status(active_matches[0])
    recovery_plan: dict[str, Any] = {}
    replacement_ready_work_unit_task_ids: dict[str, str] = {}
    superseded_ready_work_unit_task_ids: dict[str, list[str]] = {}
    existing_clean_replacement_task_ids: dict[str, str] = {}
    missing_work_unit_ids: list[str] = []
    clean_work_unit_ids: list[str] = []

    for task in tasks:
        key = expected_ready_work_unit_key(task)
        packet_id, work_unit_id = key
        matches = candidates.get(key) or []
        active_matches = [
            payload for payload in matches if not task_has_ready_work_unit_supersession(payload)
        ]
        if not active_matches:
            missing_work_unit_ids.append(work_unit_id)
            recovery_plan[work_unit_id] = {
                "packet_id": packet_id,
                "status": "missing_active_runtime_task",
                "next_action": "materialize a clean ready work-unit task before release",
            }
            continue

        contaminated: list[tuple[dict[str, Any], list[str]]] = []
        clean_blocked: list[dict[str, Any]] = []
        dependency_blockers = [
            dep
            for dep in dependencies.get(work_unit_id, [])
            if active_status_by_work_unit.get(dep) not in READY_WORK_UNIT_DEPENDENCY_SATISFIED_STATUSES
        ]
        for payload in active_matches:
            markers = ready_work_unit_contamination_markers(payload)
            legal_release_seen = history_contains_markers(
                payload,
                READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
            ) or task_has_unblocked_event(
                payload,
                required_markers=READY_WORK_UNIT_RELEASE_REQUIRED_MARKERS,
            )
            if markers:
                if dependency_blockers or not legal_release_seen:
                    contaminated.append((payload, markers))
                continue
            if task_readback_status(payload) == "blocked":
                contract_error = ready_work_unit_readback_contract_error(
                    payload=payload,
                    task_id=task_readback_id(payload),
                    expected_assignee=ready_work_unit_release_assignee(task, args.worker_assignee_prefix),
                    expected_packet_id=packet_id,
                )
                if contract_error:
                    contaminated.append((payload, ["invalid_blocked_replacement_contract"]))
                else:
                    clean_blocked.append(payload)

        if not contaminated:
            clean_work_unit_ids.append(work_unit_id)
            recovery_plan[work_unit_id] = {
                "packet_id": packet_id,
                "status": "clean_no_recovery_needed",
                "active_task_count": len(active_matches),
                "dependency_blockers": dependency_blockers,
            }
            continue

        contaminated_task_ids = [task_readback_id(payload) for payload, _markers in contaminated]
        contamination_markers = sorted({marker for _payload, markers in contaminated for marker in markers})
        replacement_task_id: str | None = None
        replacement_task = replacement_ready_work_unit_task(
            plan_task=task,
            contaminated_task_ids=contaminated_task_ids,
            contamination_markers=contamination_markers,
        )
        if clean_blocked:
            replacement_task_id = task_readback_id(clean_blocked[0])
            existing_clean_replacement_task_ids[work_unit_id] = replacement_task_id
        elif args.create_replacements:
            workspace_ref = str(args.workspace or "scratch").strip() or "scratch"
            replacement_task_id = create_ready_work_unit_task(
                hermes_bin=args.hermes_bin,
                board=board,
                task=replacement_task,
                worker_assignee_prefix=args.worker_assignee_prefix,
                workspace_ref=workspace_ref,
                runner=runner,
            )
            replacement_ready_work_unit_task_ids[work_unit_id] = replacement_task_id

        superseded_task_ids_for_plan = [
            task_id
            for task_id in contaminated_task_ids
            if not replacement_task_id or task_id != replacement_task_id
        ]
        if args.create_replacements or clean_blocked:
            for payload, markers in contaminated:
                if task_readback_id(payload) == replacement_task_id:
                    continue
                mark_ready_work_unit_superseded(
                    hermes_bin=args.hermes_bin,
                    board=board,
                    task_id=task_readback_id(payload),
                    replacement_task_id=replacement_task_id,
                    work_unit_id=work_unit_id,
                    contamination_markers=markers,
                    runner=runner,
                )
        superseded_ready_work_unit_task_ids[work_unit_id] = superseded_task_ids_for_plan
        recovery_plan[work_unit_id] = {
            "packet_id": packet_id,
            "status": "replacement_created" if replacement_task_id and args.create_replacements else "replacement_planned",
            "contaminated_task_refs": superseded_task_ids_for_plan,
            "contamination_markers": contamination_markers,
            "replacement_task_ref": replacement_task_id,
            "replacement_idempotency_key": replacement_task["idempotency_key"],
            "preserve_history": True,
            "complete_product_claim_allowed": False,
        }

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "recover-ready-work-units",
        "dry_run": not bool(args.create_replacements),
        "board": board,
        "materialization_plan_id": plan.get("plan_id"),
        "ready_work_unit_task_ids": materialization_result.get("ready_work_unit_task_ids") or {},
        "replacement_ready_work_unit_task_ids": replacement_ready_work_unit_task_ids,
        "superseded_ready_work_unit_task_ids": superseded_ready_work_unit_task_ids,
        "existing_clean_replacement_task_ids": existing_clean_replacement_task_ids,
        "recovery_plan": recovery_plan,
        "runtime_gate": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "complete_product_claim_allowed": False,
            "recovery_required_before_product_completion": bool(superseded_ready_work_unit_task_ids),
            "replacement_created_count": len(replacement_ready_work_unit_task_ids),
            "superseded_task_count": sum(len(ids) for ids in superseded_ready_work_unit_task_ids.values()),
            "missing_active_task_count": len(missing_work_unit_ids),
            "clean_task_count": len(clean_work_unit_ids),
        },
        "hook": {
            "plan": plan,
            "materialization_result": materialization_result,
            "supersession_marker": READY_WORK_UNIT_SUPERSESSION_MARKER,
            "create_replacements": bool(args.create_replacements),
            "no_shadow_dispatcher": True,
            "local_state_authority": False,
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def materialize(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    card_path = args.card.resolve()
    ledger_path = args.ledger.resolve()
    result = build_hook_result(
        card_path=card_path,
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=args.receipt,
        worker_results_dir=args.worker_results_dir,
        ledger_path=ledger_path,
    )
    plan = result["plan"]
    card_id = str(plan.get("event", {}).get("card_id") or card_path.stem)
    if args.dry_run:
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "materialize",
            "dry_run": True,
            "board": args.board,
            "board_created": False,
            "board_create_requested": bool(args.ensure_board),
            "board_create_checked": False,
            "main_task_id": None,
            "worker_task_ids": {},
            "hook": result,
        }
        if args.out:
            write_json(args.out, envelope)
        return envelope

    board_created = False
    if args.ensure_board:
        board_created = ensure_board(
            hermes_bin=args.hermes_bin,
            board=args.board,
            default_workdir=str(ROOT),
            runner=runner,
        )

    readiness_blockers = route_readiness_blockers(
        args.route_readiness,
        [
            str(task.get("worker_id"))
            for task in plan.get("worker_tasks", [])
            if str(task.get("worker_id") or "").strip() and task.get("status") != "not_required_by_current_card"
        ],
    )
    if readiness_blockers:
        raise RuntimeError("pre-dispatch route readiness blocked live materialization: " + "; ".join(readiness_blockers))

    card_body = card_path.read_text(encoding="utf-8")
    workflow_template_id = FACTORY_KANBAN_WORKFLOW_TEMPLATE_ID
    current_step_key = FACTORY_KANBAN_DEFAULT_STEP_KEY
    try:
        factoryctl = load_factoryctl()
        card_data = factoryctl.load_json_like(card_path)
        phase_engine = factoryctl.factory_phase_engine_state(card_data)
        current_step_key = factoryctl.factory_workflow_step_key(phase_engine)
    except Exception:
        current_step_key = FACTORY_KANBAN_DEFAULT_STEP_KEY
    main_contract_digest = contract_digest(card_body)
    idempotency_contract: dict[str, Any] = {
        "digest_algorithm": CONTRACT_DIGEST_ALGORITHM,
        "canonicalization_version": CANONICALIZATION_VERSION,
        "volatile_fields_ignored": sorted(VOLATILE_CONTRACT_KEYS),
        "digest_scope": "main_card_body_and_stable_worker_packet_contract",
        "lineage_policy": IDEMPOTENCY_LINEAGE_POLICY,
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "main_task": {
            "idempotency_identity": {
                "card_id": card_id,
                "task_role": "main",
                "base_idempotency_key": main_base_idempotency_key(card_id),
            },
            "contract_digest": main_contract_digest,
            "idempotency_key": main_task_idempotency_key(card_id, card_body),
            "runtime_history_query_keys": [
                main_base_idempotency_key(card_id),
                main_task_idempotency_key(card_id, card_body),
            ],
            "previous_runtime_task_refs": [],
            "supersedes_idempotency_keys": [],
        },
        "worker_tasks": {},
    }

    main_task_id = create_task(
        hermes_bin=args.hermes_bin,
        board=args.board,
        title=f"OF {card_id} main gate",
        body=card_body,
        assignee=args.main_assignee,
        idempotency_key=idempotency_contract["main_task"]["idempotency_key"],
        created_by="overkill-factory",
        workspace=f"dir:{ROOT}",
        blocked=True,
        workflow_template_id=workflow_template_id,
        current_step_key=current_step_key,
        runner=runner,
    )
    worker_task_ids: dict[str, str] = {}
    review_promoted_worker_task_ids: dict[str, str] = {}
    recovery_promoted_worker_task_ids: dict[str, str] = {}
    recovery_retry_blocked_worker_task_ids: dict[str, str] = {}
    recovery_attempts: dict[str, dict[str, Any]] = {}
    downstream_promoted_worker_task_ids: dict[str, str] = {}
    downstream_authorizations = downstream_authorizations_by_worker(plan)
    for task in plan.get("worker_tasks", []):
        worker_id = str(task.get("worker_id") or "").strip()
        if not worker_id or task.get("status") == "not_required_by_current_card":
            continue
        packet = task.get("packet") or {}
        worker_task_contract = worker_materialization_contract(task)
        worker_idempotency_key = worker_task_idempotency_key(card_id, worker_id, worker_task_contract)
        worker_contract_digest = contract_digest(worker_task_contract)
        idempotency_contract["worker_tasks"][worker_id] = {
            "idempotency_identity": {
                "card_id": card_id,
                "worker_id": worker_id,
                "task_role": "worker",
                "base_idempotency_key": worker_base_idempotency_key(card_id, worker_id),
            },
            "contract_scope": "worker_task_materialization_contract",
            "contract_digest": worker_contract_digest,
            "idempotency_key": worker_idempotency_key,
            "runtime_history_query_keys": [
                worker_base_idempotency_key(card_id, worker_id),
                worker_idempotency_key,
            ],
            "previous_runtime_task_refs": [],
            "supersedes_idempotency_keys": [],
        }
        task_id = create_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            title=str(task.get("title") or f"OF {card_id} {worker_id}"),
            body=compact_json_argument(packet),
            assignee=args.worker_assignee_prefix + worker_id,
            idempotency_key=worker_idempotency_key,
            created_by="overkill-factory",
            workspace=f"dir:{ROOT}",
            blocked=not args.worker_ready,
            workflow_template_id=workflow_template_id,
            current_step_key=current_step_key,
            runner=runner,
        )
        worker_task_ids[worker_id] = task_id
        run_checked(hermes_kanban(args.hermes_bin, args.board, "link", task_id, main_task_id), runner)
        review_authorized = (
            task.get("dependency_authorization_state") == "review_ready"
            and task.get("status") == "requires_execution"
            and bool(task.get("review_task_authorizations"))
        )
        if review_authorized and not args.worker_ready:
            auth = task["review_task_authorizations"][0]
            requirement_id = str(auth.get("requirement_id") or "review-required-handoff")
            producer_ref = str(auth.get("producer_ref") or "producer-handoff")
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                reason=(
                    "Review task authorized by valid review-required handoff "
                    f"{requirement_id} from {producer_ref}; non-review downstream remains gated."
                ),
                runner=runner,
            )
            review_promoted_worker_task_ids[worker_id] = task_id
        recovery_routes = [
            route
            for route in (packet.get("input_contract") or {}).get("recovery_routes", [])
            if isinstance(route, dict)
        ]
        authorized_recovery_routes = [
            route
            for route in recovery_routes
            if route.get("factory_owned_repair_allowed") is True and route.get("human_gate_required") is False
        ]
        recovery_authorized = bool(authorized_recovery_routes)
        if recovery_authorized and not args.worker_ready:
            route = authorized_recovery_routes[0]
            route_id = str(route.get("recovery_route_id") or "factory-recovery-route")
            route_digest = recovery_route_digest(route)
            fresh_review_ref = str(route.get("fresh_review_result_ref") or "fresh-review-required")
            shown_task = show_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                runner=runner,
            )
            task_status_value = task_status(shown_task)
            history_refs = recovery_attempt_history_refs(shown_task, route_id, route_digest)
            previous_attempts = len(history_refs)
            attempt_number = previous_attempts + 1
            max_attempts = retry_policy_max_attempts(route)
            recovery_attempts[worker_id] = {
                "recovery_route_id": route_id,
                "recovery_route_digest": route_digest,
                "worker_id": worker_id,
                "hermes_task_ref": task_id,
                "previous_attempts": previous_attempts,
                "attempt_number": attempt_number,
                "max_attempts": max_attempts,
                "attempt_source": "hermes_task_history",
                "history_refs": history_refs,
                "history_ref_count": len(history_refs),
                "task_status": task_status_value or "unknown",
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "attempted_this_run": False,
            }
            if task_status_value in ACTIVE_OR_TERMINAL_STATUSES:
                recovery_attempts[worker_id]["status"] = "already_active_no_new_attempt"
                continue
            if not has_history_source(shown_task):
                recovery_attempts[worker_id]["status"] = "history_unavailable"
                recovery_retry_blocked_worker_task_ids[worker_id] = task_id
                continue
            if attempt_number > max_attempts:
                recovery_attempts[worker_id]["status"] = "retry_limit_exceeded"
                recovery_retry_blocked_worker_task_ids[worker_id] = task_id
                continue
            recovery_attempts[worker_id]["status"] = "attempt_authorized"
            recovery_attempts[worker_id]["attempted_this_run"] = True
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                reason=(
                    f"{RECOVERY_ATTEMPT_MARKER} route_id={route_id} "
                    f"route_digest={route_digest} "
                    f"attempt_number={attempt_number} max_attempts={max_attempts}; "
                    "Factory-owned recovery route authorized repair task; downstream remains gated until "
                    f"{fresh_review_ref} passes."
                ),
                required_readback_markers=[
                    RECOVERY_ATTEMPT_MARKER,
                    f"route_id={route_id}",
                    f"route_digest={route_digest}",
                    f"attempt_number={attempt_number}",
                    f"max_attempts={max_attempts}",
                ],
                runner=runner,
            )
            recovery_promoted_worker_task_ids[worker_id] = task_id
        downstream_authorized = (
            downstream_worker_ready_after_fresh_review(plan, task, downstream_authorizations)
            and worker_id not in review_promoted_worker_task_ids
            and worker_id not in recovery_promoted_worker_task_ids
        )
        if downstream_authorized and not args.worker_ready:
            auths = downstream_authorizations[worker_id]
            requirement_ids = [
                str(auth.get("requirement_id") or "").strip()
                for auth in auths
                if str(auth.get("requirement_id") or "").strip()
            ]
            review_refs = [
                str(auth.get("review_evidence_ref") or "").strip()
                for auth in auths
                if str(auth.get("review_evidence_ref") or "").strip()
            ]
            recovery_route_refs = [
                str(route_ref or "").strip()
                for auth in auths
                for route_ref in auth.get("recovery_route_refs") or []
                if str(route_ref or "").strip()
            ]
            recovery_route_digests = [
                str(route_digest or "").strip()
                for auth in auths
                for route_digest in auth.get("recovery_route_digests") or []
                if str(route_digest or "").strip()
            ]
            readback_markers = [
                f"authorized_worker_id={worker_id}",
                *[f"requirement_id={requirement_id}" for requirement_id in requirement_ids],
                *[f"review_evidence_ref={review_ref}" for review_ref in review_refs],
                *[f"recovery_route_ref={route_ref}" for route_ref in recovery_route_refs],
                *[f"recovery_route_digest={route_digest}" for route_digest in recovery_route_digests],
            ]
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=task_id,
                reason=(
                    "Fresh PASS review authorized exact downstream worker "
                    f"{worker_id}; requirement(s): {', '.join(requirement_ids)}; "
                    f"review ref(s): {', '.join(review_refs)}; "
                    f"readback_markers: {' '.join(readback_markers)}; "
                    "main gate remains blocked."
                ),
                required_readback_markers=readback_markers,
                runner=runner,
            )
            downstream_promoted_worker_task_ids[worker_id] = task_id

    record_live_binding(
        ledger_path=ledger_path,
        card_id=card_id,
        board=args.board,
        main_task_id=main_task_id,
        worker_task_ids=worker_task_ids,
        idempotency_contract=idempotency_contract,
    )

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "materialize",
        "dry_run": False,
        "board": args.board,
        "board_created": board_created,
        "main_task_id": main_task_id,
        "worker_task_ids": worker_task_ids,
        "review_promoted_worker_task_ids": review_promoted_worker_task_ids,
        "recovery_promoted_worker_task_ids": recovery_promoted_worker_task_ids,
        "recovery_retry_blocked_worker_task_ids": recovery_retry_blocked_worker_task_ids,
        "recovery_attempts": recovery_attempts,
        "downstream_promoted_worker_task_ids": downstream_promoted_worker_task_ids,
        "idempotency_contract": idempotency_contract,
        "hook": result,
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def enforce_done(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    result = build_hook_result(
        card_path=args.card.resolve(),
        from_status=args.from_status,
        to_status=args.to_status,
        receipt_path=args.receipt.resolve(),
        worker_results_dir=args.worker_results_dir.resolve(),
        ledger_path=args.ledger.resolve(),
    )
    blocked = result["transition_action"] == ACTION_BLOCK_TRANSITION
    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "enforce-done",
        "blocked": blocked,
        "board": args.board,
        "main_task_id": args.main_task_id,
        "hook": result,
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    if blocked:
        return public_envelope
    readiness_blockers = route_readiness_blockers(args.route_readiness, ["evidence-reconciler"])
    if readiness_blockers:
        raise RuntimeError("pre-completion route readiness blocked live completion: " + "; ".join(readiness_blockers))
    if args.complete_main:
        card_id = str(result.get("plan", {}).get("event", {}).get("card_id") or args.card.stem)
        validate_live_binding(
            ledger_path=args.ledger.resolve(),
            card_id=card_id,
            board=args.board,
            main_task_id=args.main_task_id,
        )
        receipt_payload, artifact_projection = apply_completion_artifact_policy(
            receipt=load_json(args.receipt.resolve()),
            artifact_paths=[path.resolve() for path in args.artifact_path],
            attachment_root=args.attachment_root.resolve() if args.attachment_root else None,
            board=args.board,
            task_id=args.main_task_id,
        )
        complete_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            task_id=args.main_task_id,
            result=args.result,
            summary=args.summary,
            metadata=receipt_payload,
            required_readback_markers=[COMPLETION_ARTIFACT_PROJECTION_MARKER] if artifact_projection else None,
            runner=runner,
        )
    return public_envelope


def dispatch(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    before_ready = list_tasks_by_status(
        hermes_bin=args.hermes_bin,
        board=args.board,
        status="ready",
        runner=runner,
    )
    before_running = list_tasks_by_status(
        hermes_bin=args.hermes_bin,
        board=args.board,
        status="running",
        runner=runner,
    )
    before_ready_ids = {
        str(task.get("task_id") or task.get("id") or "")
        for task in before_ready
        if str(task.get("task_id") or task.get("id") or "").strip()
    }
    before_running_ids = {
        str(task.get("task_id") or task.get("id") or "")
        for task in before_running
        if str(task.get("task_id") or task.get("id") or "").strip()
    }
    preflight_rows = {
        "ready": before_ready,
        "running": before_running,
        "todo": list_tasks_by_status(
            hermes_bin=args.hermes_bin,
            board=args.board,
            status="todo",
            runner=runner,
        ),
        "blocked": list_tasks_by_status(
            hermes_bin=args.hermes_bin,
            board=args.board,
            status="blocked",
            runner=runner,
        ),
        "done": list_tasks_by_status(
            hermes_bin=args.hermes_bin,
            board=args.board,
            status="done",
            runner=runner,
        ),
    }
    reconcile_plan = build_board_reconcile_plan_from_rows(board=args.board, rows=preflight_rows)
    if reconcile_plan.get("plan_action") != "dispatch_ready":
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "dispatch",
            "dry_run": bool(args.dry_run),
            "board": args.board,
            "blocked": True,
            "dispatch_skipped": True,
            "spawned": [],
            "spawned_by_this_command": [],
            "already_running_after_dispatch": [],
            "native_dispatch": None,
            "board_reconcile_plan": reconcile_plan,
            "dispatch_observed_state": {
                "ready_before_count": len(before_ready_ids),
                "running_before_count": len(before_running_ids),
                "running_after_count": len(before_running_ids),
            },
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "Native Hermes dispatch was not called because the deterministic board reconciler "
                    "did not return dispatch_ready."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope

    dispatch_args = ["dispatch", "--json"]
    if args.dry_run:
        dispatch_args.append("--dry-run")
    if args.max is not None:
        dispatch_args.extend(["--max", str(args.max)])
    if args.failure_limit is not None:
        dispatch_args.extend(["--failure-limit", str(args.failure_limit)])
    completed = run_checked(hermes_kanban(args.hermes_bin, args.board, *dispatch_args), runner)
    native_payload = parse_json_output(completed.stdout, command="hermes kanban dispatch --json")
    if not isinstance(native_payload, dict):
        raise RuntimeError("hermes kanban dispatch --json returned a non-object payload")

    after_running = [] if args.dry_run else list_tasks_by_status(
        hermes_bin=args.hermes_bin,
        board=args.board,
        status="running",
        runner=runner,
    )
    after_running_by_id = {
        str(task.get("task_id") or task.get("id") or ""): task
        for task in after_running
        if str(task.get("task_id") or task.get("id") or "").strip()
    }

    spawned_by_this_command = [
        enrich_dispatch_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            record=record,
            after_running_by_id=after_running_by_id,
            runner=runner,
        )
        for record in normalize_native_spawned(native_payload)
    ]
    spawned_ids = {record["task_id"] for record in spawned_by_this_command if record.get("task_id")}
    observed_ids = sorted((set(after_running_by_id) - before_running_ids) & before_ready_ids)
    already_running_after_dispatch = [
        enrich_dispatch_task(
            hermes_bin=args.hermes_bin,
            board=args.board,
            record={"task_id": task_id, "observed_source": "ready_before_running_after_dispatch"},
            after_running_by_id=after_running_by_id,
            runner=runner,
        )
        for task_id in observed_ids
        if task_id not in spawned_ids
    ]
    for record in spawned_by_this_command:
        record["dispatch_observation"] = "native_dispatch_spawned"
    for record in already_running_after_dispatch:
        record["dispatch_observation"] = "already_running_after_native_dispatch"

    combined_spawned = [*spawned_by_this_command, *already_running_after_dispatch]
    native_sanitized = dict(native_payload)
    native_sanitized["spawned"] = normalize_native_spawned(native_payload)

    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "dispatch",
        "dry_run": bool(args.dry_run),
        "board": args.board,
        "spawned": combined_spawned,
        "spawned_by_this_command": spawned_by_this_command,
        "already_running_after_dispatch": already_running_after_dispatch,
        "native_dispatch": native_sanitized,
        "board_reconcile_plan": reconcile_plan,
        "dispatch_observed_state": {
            "ready_before_count": len(before_ready_ids),
            "running_before_count": len(before_running_ids),
            "running_after_count": len(after_running_by_id),
        },
        "hook": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "no_shadow_dispatcher": True,
            "reporting_policy": "Hermes dispatch remains authoritative; this adapter only enriches the returned report from Hermes state.",
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def no_idle(args: argparse.Namespace, runner: Runner = default_runner) -> dict[str, Any]:
    rows = {
        status: list_tasks_by_status(
            hermes_bin=args.hermes_bin,
            board=args.board,
            status=status,
            runner=runner,
        )
        for status in ("ready", "running", "todo", "blocked", "triage", "done")
    }
    rows = enrich_no_idle_rows(hermes_bin=args.hermes_bin, board=args.board, rows=rows, runner=runner)
    initial_reconcile_plan = build_board_reconcile_plan_from_rows(board=args.board, rows=rows)
    if initial_reconcile_plan.get("plan_action") == "block_invariant_violation":
        classification = {
            "status": "blocked",
            "classification": "factory_phase_invariant_violation",
            "blocked": True,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "native_dispatch_required_next": False,
            "next_action": "repair the Kanban invariant violation before no-idle may close out, materialize or remediate work",
            "state": summarize_no_idle_rows(rows),
        }
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": True,
            "no_idle_state": classification,
            "board_reconcile_plan": initial_reconcile_plan,
            "artifact_materialization": [],
            "targeted_remediation_plan": None,
            "remediation_task_id": None,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle is an integrity auditor first. It refuses to mutate Hermes while "
                    "the board reconciler reports a deterministic phase/dependency invariant violation."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    artifact_materialization: list[dict[str, Any]] = []
    running_closeout_candidates = running_result_closeout_candidates(rows)
    if running_closeout_candidates:
        if not args.create_remediation:
            classification = {
                "status": "remediation_required",
                "classification": "running_worker_result_closeout_required",
                "blocked": True,
                "remediation_required": True,
                "human_gate_required": False,
                "operator_input_required": False,
                "native_dispatch_required_next": False,
                "running_result_closeout_candidates": [
                    {
                        "task_ref": item.get("task_ref"),
                        "worker_result_record_type": item.get("worker_result_record_type"),
                        "worker_result_result": item.get("worker_result_result"),
                        "age_seconds": item.get("age_seconds"),
                        "timeout_seconds": item.get("timeout_seconds"),
                    }
                    for item in running_closeout_candidates
                ],
                "next_action": (
                    "run no-idle with create-remediation so the runtime adapter completes running tasks "
                    "that already produced valid terminal worker results"
                ),
                "state": summarize_no_idle_rows(rows),
            }
            envelope = {
                "$schema": LIVE_ADAPTER_SCHEMA,
                "mode": "no-idle",
                "board": args.board,
                "blocked": True,
                "no_idle_state": classification,
                "board_reconcile_plan": None,
                "artifact_materialization": artifact_materialization,
                "targeted_remediation_plan": {
                    "record_type": "factory_no_idle_running_result_closeout_plan",
                    "plan_action": "complete_running_tasks_with_valid_worker_results",
                    "native_dispatch_required_next": False,
                    "human_gate_required": False,
                    "operator_input_required": False,
                },
                "remediation_task_id": None,
                "hook": {
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "no_shadow_dispatcher": True,
                    "dispatch_called_by_this_command": False,
                    "reporting_policy": (
                        "No-idle found over-time running tasks with valid terminal worker results. "
                        "Live closeout requires create-remediation because it mutates Hermes task state."
                    ),
                },
            }
            public_envelope = sanitize_public_refs(envelope)
            if args.out:
                write_json(args.out, public_envelope)
            return public_envelope
        closed_running_tasks = close_running_tasks_with_valid_worker_results(
            hermes_bin=args.hermes_bin,
            board=args.board,
            candidates=running_closeout_candidates,
            runner=runner,
        )
        rows = {
            status: list_tasks_by_status(
                hermes_bin=args.hermes_bin,
                board=args.board,
                status=status,
                runner=runner,
            )
            for status in ("ready", "running", "todo", "blocked", "triage", "done")
        }
        rows = enrich_no_idle_rows(hermes_bin=args.hermes_bin, board=args.board, rows=rows, runner=runner)
        classification = {
            "status": "remediated",
            "classification": "running_worker_result_closeout_completed",
            "blocked": False,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "native_dispatch_required_next": bool(rows.get("ready")),
            "closed_running_tasks": closed_running_tasks,
            "next_action": (
                "run native Hermes dispatch for ready work"
                if rows.get("ready")
                else "continue no-idle reconciliation from refreshed Hermes state"
            ),
            "state": summarize_no_idle_rows(rows),
        }
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": False,
            "no_idle_state": classification,
            "board_reconcile_plan": None,
            "artifact_materialization": artifact_materialization,
            "targeted_remediation_plan": {
                "record_type": "factory_no_idle_running_result_closeout_plan",
                "plan_action": "complete_running_tasks_with_valid_worker_results",
                "native_dispatch_required_next": bool(rows.get("ready")),
                "human_gate_required": False,
                "operator_input_required": False,
            },
            "remediation_task_id": None,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle completed over-time running tasks only after validating terminal worker-result metadata."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    plan_path = latest_ready_work_unit_materialization_plan_path(rows)
    if plan_path is not None and not board_has_ready_work_unit_execution_requests(rows):
        if not args.create_remediation:
            classification = {
                "status": "remediation_required",
                "classification": "ready_work_unit_runtime_materialization_required",
                "blocked": True,
                "remediation_required": True,
                "human_gate_required": False,
                "operator_input_required": False,
                "native_dispatch_required_next": False,
                "ready_work_unit_hermes_materialization_plan_ref": str(plan_path.relative_to(ROOT)),
                "next_action": (
                    "run no-idle with create-remediation so the runtime adapter materializes blocked-first "
                    "Hermes ready work-unit execution cards from the validated plan"
                ),
                "state": summarize_no_idle_rows(rows),
            }
            envelope = {
                "$schema": LIVE_ADAPTER_SCHEMA,
                "mode": "no-idle",
                "board": args.board,
                "blocked": True,
                "no_idle_state": classification,
                "board_reconcile_plan": None,
                "artifact_materialization": artifact_materialization,
                "targeted_remediation_plan": None,
                "remediation_task_id": None,
                "hook": {
                    "runtime_authority": "hermes_kanban",
                    "local_state_authority": False,
                    "no_shadow_dispatcher": True,
                    "dispatch_called_by_this_command": False,
                    "reporting_policy": (
                        "No-idle found a validated ready work-unit Hermes plan; live materialization "
                        "requires create-remediation so the adapter, not a worker, performs the runtime mutation."
                    ),
                },
            }
            public_envelope = sanitize_public_refs(envelope)
            if args.out:
                write_json(args.out, public_envelope)
            return public_envelope
        ready_work_unit_runtime_materialization = auto_materialize_ready_work_units_from_plan(
            hermes_bin=args.hermes_bin,
            board=args.board,
            plan_path=plan_path,
            worker_assignee_prefix="",
            workspace=args.workspace,
            runner=runner,
        )
        rows = {
            status: list_tasks_by_status(
                hermes_bin=args.hermes_bin,
                board=args.board,
                status=status,
                runner=runner,
            )
            for status in ("ready", "running", "todo", "blocked", "triage", "done")
        }
        rows = enrich_no_idle_rows(hermes_bin=args.hermes_bin, board=args.board, rows=rows, runner=runner)
        ready_after = rows.get("ready", [])
        classification = {
            "status": "dispatch_available" if ready_after else "runtime_materialized",
            "classification": "ready_work_unit_runtime_materialized",
            "blocked": False,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "native_dispatch_required_next": bool(ready_after),
            "ready_work_unit_hermes_materialization_plan_ref": str(plan_path.relative_to(ROOT)),
            "runtime_materialization": ready_work_unit_runtime_materialization,
            "next_action": (
                "run native Hermes dispatch for released ready work-unit cards"
                if ready_after
                else "observe materialized ready work-unit cards and dependencies"
            ),
            "state": summarize_no_idle_rows(rows),
        }
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": False,
            "no_idle_state": classification,
            "board_reconcile_plan": None,
            "artifact_materialization": artifact_materialization,
            "targeted_remediation_plan": None,
            "remediation_task_id": None,
            "ready_work_unit_runtime_materialization": ready_work_unit_runtime_materialization,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle used the runtime adapter to materialize validated ready work-unit plan "
                    "into blocked-first Hermes cards and release the eligible first wave; native dispatch remains separate."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    if plan_path is not None and board_has_ready_work_unit_execution_requests(rows):
        out_dir = ROOT / ".tmp" / "factory-runs"
        digest = hashlib.sha256(str(plan_path).encode("utf-8")).hexdigest()[:12]
        route_readiness_path = out_dir / f"ready-work-unit-route-readiness-{args.board}-{digest}.json"
        materialization_result_path = out_dir / f"ready-work-unit-materialization-{args.board}-{digest}.json"
        if route_readiness_path.exists() and materialization_result_path.exists():
            ready_reconciliation = reconcile_ready_work_units(
                argparse.Namespace(
                    plan=plan_path,
                    materialization_result=materialization_result_path,
                    board=args.board,
                    hermes_bin=args.hermes_bin,
                    worker_assignee_prefix="",
                    route_readiness=route_readiness_path,
                    reason=(
                        "no_idle_ready_work_unit_reconciliation; post_release_ready_work_unit; "
                        "review_required_or_authority_required; dispatch_separate=true"
                    ),
                    create_post_repair_review_tasks=bool(args.create_remediation),
                    create_post_repair_authority_tasks=bool(args.create_remediation),
                    post_repair_review_workspace=args.workspace,
                    post_repair_authority_workspace=args.workspace,
                    completion_result="Ready work-unit no-idle reconciliation satisfied.",
                    completion_summary="No-idle reconciled post-release ready work-unit evidence.",
                    dry_run=not bool(args.create_remediation),
                    out=None,
                ),
                runner=runner,
            )
            runtime_gate = ready_reconciliation.get("runtime_gate") if isinstance(ready_reconciliation, dict) else {}
            task_created = int(runtime_gate.get("post_repair_review_task_created_count") or 0) + int(
                runtime_gate.get("post_repair_authority_task_created_count") or 0
            )
            actionable = bool(ready_reconciliation.get("retry_ready_work_unit_task_ids")) or bool(
                ready_reconciliation.get("completed_ready_work_unit_task_ids")
            )
            followup_release = ready_reconciliation.get("followup_release_result")
            followup_released = (
                (followup_release or {}).get("released_ready_work_unit_task_ids")
                if isinstance(followup_release, dict)
                else {}
            )
            actionable = actionable or bool(followup_released)
            incomplete = int(runtime_gate.get("incomplete_repair_or_review_count") or 0)
            post_release_blocked = int(runtime_gate.get("post_release_blocked_count") or 0)
            if task_created or actionable or post_release_blocked:
                classification = {
                    "status": "remediation_required" if task_created else "blocked" if incomplete else "observed",
                    "classification": "ready_work_unit_reconciliation",
                    "blocked": incomplete > 0 and not task_created and not actionable,
                    "remediation_required": task_created > 0,
                    "human_gate_required": int(runtime_gate.get("human_gate_required_count") or 0) > 0,
                    "operator_input_required": False,
                    "native_dispatch_required_next": task_created > 0 or bool(followup_released),
                    "ready_work_unit_hermes_materialization_plan_ref": str(plan_path.relative_to(ROOT)),
                    "materialization_result_ref": str(materialization_result_path.relative_to(ROOT)),
                    "ready_work_unit_reconciliation": ready_reconciliation,
                    "blocked_reasons": [],
                    "next_action": (
                        "dispatch Hermes for newly created review/authority or newly released ready work-unit tasks"
                        if task_created or followup_released
                        else "continue ready work-unit reconciliation"
                    ),
                    "state": summarize_no_idle_rows(rows),
                }
                envelope = {
                    "$schema": LIVE_ADAPTER_SCHEMA,
                    "mode": "no-idle",
                    "board": args.board,
                    "blocked": bool(classification.get("blocked")),
                    "no_idle_state": classification,
                    "board_reconcile_plan": None,
                    "artifact_materialization": artifact_materialization,
                    "targeted_remediation_plan": {
                        "record_type": "factory_no_idle_ready_work_unit_reconciliation",
                        "plan_action": "reconcile_ready_work_units",
                        "native_dispatch_required_next": task_created > 0 or bool(followup_released),
                        "human_gate_required": classification["human_gate_required"],
                    },
                    "remediation_task_id": None,
                    "hook": {
                        "runtime_authority": "hermes_kanban",
                        "local_state_authority": False,
                        "no_shadow_dispatcher": True,
                        "dispatch_called_by_this_command": False,
                        "reporting_policy": (
                            "No-idle used the ready-work-unit reconciler instead of generic board remediation."
                        ),
                    },
                }
                public_envelope = sanitize_public_refs(envelope)
                if args.out:
                    write_json(args.out, public_envelope)
                return public_envelope
    if args.create_remediation:
        artifact_materialization = materialize_missing_declared_artifacts(
            hermes_bin=args.hermes_bin,
            board=args.board,
            rows=rows,
            runner=runner,
        )
        if any(item.get("materialized") is True for item in artifact_materialization):
            rows = {
                status: list_tasks_by_status(
                    hermes_bin=args.hermes_bin,
                    board=args.board,
                    status=status,
                    runner=runner,
                )
                for status in ("ready", "running", "todo", "blocked", "triage", "done")
            }
            rows = enrich_no_idle_rows(hermes_bin=args.hermes_bin, board=args.board, rows=rows, runner=runner)
    reconcile_plan: dict[str, Any] | None = build_board_reconcile_plan_from_rows(board=args.board, rows=rows)
    if reconcile_plan.get("plan_action") == "block_invariant_violation":
        classification = {
            "status": "blocked",
            "classification": "factory_phase_invariant_violation",
            "blocked": True,
            "remediation_required": False,
            "human_gate_required": False,
            "operator_input_required": False,
            "native_dispatch_required_next": False,
            "board_reconcile_plan": reconcile_plan,
            "blocked_reasons": reconcile_plan.get("blocked_reasons") or [],
            "next_action": "stop dispatch and repair the earlier blocked factory phase before future-phase work continues",
            "state": summarize_no_idle_rows(rows),
        }
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": True,
            "no_idle_state": classification,
            "board_reconcile_plan": reconcile_plan,
            "artifact_materialization": artifact_materialization,
            "targeted_remediation_plan": None,
            "remediation_task_id": None,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle stopped because the deterministic board reconciler found a phase invariant violation."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    if reconcile_plan.get("plan_action") == "resume_canonical_frontier_task":
        target = canonical_frontier_resume_target(rows)
        target_task_id = str((target or {}).get("task_id") or "").strip()
        resumed = False
        if target_task_id and args.create_remediation:
            reason = (
                f"{NO_IDLE_CANONICAL_FRONTIER_RESUME_MARKER}; "
                "terminal frontier reconciliation selected this single canonical Hermes task; "
                "resume existing task for native dispatch; create_new_card=false; "
                "human_gate_required=false; dispatch_separate=true"
            )
            unblock_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=target_task_id,
                reason=reason,
                required_readback_markers=[NO_IDLE_CANONICAL_FRONTIER_RESUME_MARKER],
                runner=runner,
            )
            resumed = True
        classification = {
            "status": "dispatch_available" if resumed else "remediation_required",
            "classification": (
                "canonical_frontier_task_resumed"
                if resumed
                else "canonical_frontier_task_resume_required"
            ),
            "blocked": not resumed,
            "remediation_required": not resumed,
            "human_gate_required": False,
            "operator_input_required": False,
            "native_dispatch_required_next": resumed,
            "board_reconcile_plan": reconcile_plan,
            "selected_frontier_task_ref": target_task_id if target_task_id else None,
            "blocked_reasons": reconcile_plan.get("blocked_reasons") or [],
            "next_action": (
                "run native Hermes dispatch after the canonical frontier task was resumed"
                if resumed
                else "run no-idle with create-remediation so the adapter resumes the canonical frontier task"
            ),
            "state": summarize_no_idle_rows(rows),
        }
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": not resumed,
            "no_idle_state": classification,
            "board_reconcile_plan": reconcile_plan,
            "artifact_materialization": artifact_materialization,
            "targeted_remediation_plan": {
                "record_type": "factory_no_idle_targeted_repair_plan",
                "plan_action": "resume_canonical_frontier_task",
                "board": args.board,
                "target_task_ref": target_task_id if target_task_id else None,
                "create_new_card": False,
                "native_dispatch_required_next": resumed,
                "human_gate_required": False,
                "operator_input_required": False,
            },
            "remediation_task_id": target_task_id if resumed else None,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle consumed a deterministic frontier reconciliation by resuming the "
                    "existing Hermes task instead of materializing a parallel board card."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    legacy_classification = classify_no_idle_state(rows)
    if legacy_classification.get("classification") in {
        "hermes_native_dependency_wait",
        "hermes_typed_block_loop_detected",
    }:
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": bool(legacy_classification.get("blocked")),
            "no_idle_state": legacy_classification,
            "board_reconcile_plan": reconcile_plan,
            "artifact_materialization": artifact_materialization,
            "targeted_remediation_plan": None,
            "remediation_task_id": None,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle preserved native Hermes typed block state before phase-engine "
                    "repair planning; current dependency_wait states stay native and block_loop_detected "
                    "routes deterministic triage without a generic human gate."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    if (
        legacy_classification.get("remediation_required") is not True
        and (
            legacy_classification.get("human_gate_required") is True
            or legacy_classification.get("operator_input_required") is True
        )
    ):
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": bool(legacy_classification.get("blocked")),
            "no_idle_state": legacy_classification,
            "board_reconcile_plan": reconcile_plan,
            "artifact_materialization": artifact_materialization,
            "targeted_remediation_plan": None,
            "remediation_task_id": None,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle preserved the complete operator/human gate request; "
                    "the deterministic reconciler remains attached for audit."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    reconcile_blockers = [str(item) for item in (reconcile_plan.get("blocked_reasons") or [])]
    legacy_remediation_strategy = str(legacy_classification.get("remediation_strategy") or "")
    targeted_legacy_repair_available = legacy_remediation_strategy in {
        "create_targeted_review_repair_task",
        "create_post_review_owner_gate_package_task",
    }
    runtime_contract_repair_required = (
        not targeted_legacy_repair_available
        and reconcile_plan.get("plan_action") == "repair_board_contract"
        and any(
            "bypassed Kanban-first adapter" in item
            or "no native phase children" in item
            or "skill(s) not allowed" in item
            or "has no public profile binding" in item
            for item in reconcile_blockers
        )
    )
    reducer_preempts_legacy_classifier = (
        bool(rows.get("ready"))
        or runtime_contract_repair_required
        or reconcile_plan.get("plan_action") in {
            "repair_domain_brain_route",
            "repair_declared_artifacts",
            "repair_human_gate_packet",
            "create_next_artifact_task",
            "request_operator_input",
            "request_human_gate_decision",
        }
    )
    if (
        reducer_preempts_legacy_classifier
        and reconcile_plan.get("plan_action") not in {"dispatch_ready", "observe_running", "no_unfinished_work"}
    ):
        remediation_task_id: str | None = None
        task_runtime: dict[str, Any] = {}
        create_allowed = reconcile_plan.get("create_task_allowed") is True
        stale_remediation_task_refs: list[str] = []
        remediation_replacement_attempts = 0
        if create_allowed and args.create_remediation:
            for _attempt in range(3):
                remediation_task_id = create_deterministic_reconcile_task(
                    hermes_bin=args.hermes_bin,
                    board=args.board,
                    workspace=args.workspace,
                    plan=reconcile_plan,
                    runner=runner,
                    stale_remediation_task_refs=stale_remediation_task_refs,
                )
                task_runtime = remediation_task_runtime_metadata(
                    hermes_bin=args.hermes_bin,
                    board=args.board,
                    task_id=remediation_task_id,
                    runner=runner,
                )
                if not (remediation_task_id and task_runtime.get("remediation_task_stale")):
                    break
                if remediation_task_id in stale_remediation_task_refs:
                    break
                stale_remediation_task_refs.append(remediation_task_id)
                remediation_replacement_attempts += 1
        classification_name = str(reconcile_plan.get("plan_action") or "board_reconcile_action_required")
        if stale_remediation_task_refs and remediation_task_id and not task_runtime.get("remediation_task_stale"):
            classification_name = "deterministic_board_reconcile_task_created_after_stale_terminal_replacement"
        classification = {
            "status": "remediation_required" if create_allowed else "blocked",
            "classification": classification_name,
            "blocked": True,
            "remediation_required": create_allowed,
            "human_gate_required": reconcile_plan.get("human_gate_required") is True,
            "operator_input_required": reconcile_plan.get("operator_input_required") is True,
            "native_dispatch_required_next": bool(
                remediation_task_id
                and reconcile_plan.get("native_dispatch_required_next") is True
                and task_runtime.get("native_dispatch_required_next")
            ),
            "board_reconcile_plan": reconcile_plan,
            "blocked_reasons": reconcile_plan.get("blocked_reasons") or [],
            "remediation_task_ref": remediation_task_id,
            "next_action": reconcile_plan.get("reason"),
            "state": summarize_no_idle_rows(rows),
        }
        if stale_remediation_task_refs:
            classification["stale_remediation_task_refs"] = stale_remediation_task_refs
            classification["remediation_replacement_attempts"] = remediation_replacement_attempts
            classification["remediation_replacement_strategy"] = (
                "create_fresh_reconcile_task_after_terminal_idempotency_replay"
            )
        classification.update(task_runtime)
        envelope = {
            "$schema": LIVE_ADAPTER_SCHEMA,
            "mode": "no-idle",
            "board": args.board,
            "blocked": True,
            "no_idle_state": classification,
            "board_reconcile_plan": reconcile_plan,
            "artifact_materialization": artifact_materialization,
            "targeted_remediation_plan": None,
            "remediation_task_id": remediation_task_id,
            "hook": {
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "no_shadow_dispatcher": True,
                "dispatch_called_by_this_command": False,
                "reporting_policy": (
                    "No-idle followed the deterministic board reconciler instead of the legacy classifier."
                ),
            },
        }
        public_envelope = sanitize_public_refs(envelope)
        if args.out:
            write_json(args.out, public_envelope)
        return public_envelope
    classification = legacy_classification
    remediation_task_id: str | None = None
    targeted_remediation_plan: dict[str, Any] | None = None
    if classification.get("remediation_required") and args.create_remediation:
        classification = dict(classification)
        if classification.get("classification") in {
            "only_factory_owned_package_blockers_seen",
            "todo_dependency_gated_by_factory_owned_package_blocker",
            "factory_repair_task_dependency_gated_by_blocker_it_repairs",
        }:
            targeted_remediation_plan = {
                "record_type": "factory_no_idle_targeted_repair_plan",
                "plan_action": "repair_factory_owned_package_dependency_blocker",
                "board": args.board,
                "factory_owned_package_task_refs": classification.get("factory_owned_package_task_refs") or [],
                "dependency_gated_task_refs": classification.get("dependency_gated_task_refs") or [],
                "dependency_blocker_task_refs": classification.get("dependency_blocker_task_refs") or [],
                "assignee": args.assignee,
                "native_dispatch_required_next": True,
                "human_gate_required": False,
                "operator_input_required": False,
            }
            remediation_task_id = create_factory_package_dependency_remediation_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                workspace=args.workspace,
                assignee=args.assignee,
                classification=classification,
                runner=runner,
            )
            task_runtime = remediation_task_runtime_metadata(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=remediation_task_id,
                runner=runner,
            )
            classification["targeted_remediation_plan"] = targeted_remediation_plan
            classification["remediation_task_ref"] = remediation_task_id
            classification.update(task_runtime)
            classification["native_dispatch_required_next"] = bool(
                remediation_task_id
                and targeted_remediation_plan.get("native_dispatch_required_next") is True
                and task_runtime.get("native_dispatch_required_next") is True
            )
            classification["classification"] = (
                "deterministic_factory_package_dependency_repair_task_created"
                if remediation_task_id and not classification.get("remediation_task_stale")
                else "factory_package_dependency_repair_task_not_created"
            )
        elif classification.get("remediation_strategy") == "create_targeted_review_repair_task":
            blockers = [
                item for item in rows.get("blocked", [])
                if is_review_failed_factory_repair_blocker(item)
            ]
            targeted_remediation_plan = {
                "record_type": "factory_no_idle_targeted_repair_plan",
                "plan_action": "repair_failed_independent_review_package",
                "board": args.board,
                "blocked_review_task_refs": classification.get("review_repair_task_refs") or [],
                "assignee": no_idle_review_repair_assignee(blockers, args.assignee),
                "native_dispatch_required_next": True,
                "human_gate_required": False,
                "operator_input_required": False,
            }
            remediation_task_id = create_no_idle_review_repair_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                workspace=args.workspace,
                assignee=args.assignee,
                classification=classification,
                blockers=blockers,
                runner=runner,
            )
            task_runtime = remediation_task_runtime_metadata(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=remediation_task_id,
                runner=runner,
            )
            classification["targeted_remediation_plan"] = targeted_remediation_plan
            classification["remediation_task_ref"] = remediation_task_id
            classification.update(task_runtime)
            classification["native_dispatch_required_next"] = bool(
                remediation_task_id
                and targeted_remediation_plan.get("native_dispatch_required_next") is True
                and task_runtime.get("native_dispatch_required_next") is True
            )
            classification["classification"] = (
                "deterministic_targeted_review_repair_task_created"
                if remediation_task_id and not classification.get("remediation_task_stale")
                else "targeted_review_repair_task_not_created"
            )
        elif classification.get("remediation_strategy") == "create_post_review_owner_gate_package_task":
            targeted_remediation_plan = {
                "record_type": "factory_no_idle_targeted_repair_plan",
                "plan_action": "prepare_post_review_owner_product_sot_gate_package",
                "board": args.board,
                "post_review_task_refs": classification.get("post_review_task_refs") or [],
                "ignored_superseded_blocked_task_refs": classification.get("ignored_superseded_blocked_task_refs") or [],
                "assignee": "human-gate-clerk",
                "native_dispatch_required_next": True,
                "human_gate_required": True,
                "operator_input_required": False,
            }
            remediation_task_id = create_no_idle_post_review_gate_task(
                hermes_bin=args.hermes_bin,
                board=args.board,
                workspace=args.workspace,
                classification=classification,
                runner=runner,
            )
            task_runtime = remediation_task_runtime_metadata(
                hermes_bin=args.hermes_bin,
                board=args.board,
                task_id=remediation_task_id,
                runner=runner,
            )
            classification["targeted_remediation_plan"] = targeted_remediation_plan
            classification["remediation_task_ref"] = remediation_task_id
            classification.update(task_runtime)
            classification["native_dispatch_required_next"] = bool(
                remediation_task_id
                and targeted_remediation_plan.get("native_dispatch_required_next") is True
                and task_runtime.get("native_dispatch_required_next") is True
            )
            classification["classification"] = (
                "deterministic_post_review_owner_gate_package_task_created"
                if remediation_task_id and not classification.get("remediation_task_stale")
                else "post_review_owner_gate_package_task_not_created"
            )
        else:
            reconcile_plan = build_board_reconcile_plan_from_rows(board=args.board, rows=rows)
            stale_remediation_task_refs: list[str] = []
            remediation_replacement_attempts = 0
            task_runtime: dict[str, Any] = {}
            for _attempt in range(3):
                remediation_task_id = create_deterministic_reconcile_task(
                    hermes_bin=args.hermes_bin,
                    board=args.board,
                    workspace=args.workspace,
                    plan=reconcile_plan,
                    runner=runner,
                    stale_remediation_task_refs=stale_remediation_task_refs,
                )
                task_runtime = remediation_task_runtime_metadata(
                    hermes_bin=args.hermes_bin,
                    board=args.board,
                    task_id=remediation_task_id,
                    runner=runner,
                )
                if not (remediation_task_id and task_runtime.get("remediation_task_stale")):
                    break
                if remediation_task_id in stale_remediation_task_refs:
                    break
                stale_remediation_task_refs.append(remediation_task_id)
                remediation_replacement_attempts += 1
            classification["board_reconcile_plan"] = reconcile_plan
            classification["remediation_task_ref"] = remediation_task_id
            if stale_remediation_task_refs:
                classification["stale_remediation_task_refs"] = stale_remediation_task_refs
                classification["remediation_replacement_attempts"] = remediation_replacement_attempts
                classification["remediation_replacement_strategy"] = (
                    "create_fresh_reconcile_task_after_terminal_idempotency_replay"
                )
            classification.update(task_runtime)
            classification["native_dispatch_required_next"] = bool(
                remediation_task_id
                and reconcile_plan.get("native_dispatch_required_next") is True
                and task_runtime.get("native_dispatch_required_next") is True
            )
            classification["classification"] = (
                "deterministic_board_reconcile_task_created_after_stale_terminal_replacement"
                if stale_remediation_task_refs and remediation_task_id and not classification.get("remediation_task_stale")
                else (
                    "deterministic_board_reconcile_task_created"
                    if remediation_task_id and not classification.get("remediation_task_stale")
                    else str(reconcile_plan.get("plan_action") or classification.get("classification"))
                )
            )
    envelope = {
        "$schema": LIVE_ADAPTER_SCHEMA,
        "mode": "no-idle",
        "board": args.board,
        "blocked": bool(classification.get("blocked")),
        "no_idle_state": classification,
        "board_reconcile_plan": reconcile_plan,
        "artifact_materialization": artifact_materialization,
        "targeted_remediation_plan": targeted_remediation_plan,
        "remediation_task_id": remediation_task_id,
        "hook": {
            "runtime_authority": "hermes_kanban",
            "local_state_authority": False,
            "no_shadow_dispatcher": True,
            "dispatch_called_by_this_command": False,
            "reporting_policy": (
                "No-idle observes Hermes state and may create a safe remediation card; "
                "native Hermes dispatch remains the only worker scheduler."
            ),
        },
    }
    public_envelope = sanitize_public_refs(envelope)
    if args.out:
        write_json(args.out, public_envelope)
    return public_envelope


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate Overkill Factory gates on Hermes Kanban.")
    sub = parser.add_subparsers(dest="command", required=True)

    p_mat = sub.add_parser("materialize", help="Create the main card and required worker cards.")
    p_mat.add_argument("--card", type=Path, required=True)
    p_mat.add_argument("--board", required=True)
    p_mat.add_argument("--ledger", type=Path, required=True)
    p_mat.add_argument("--receipt", type=Path)
    p_mat.add_argument("--worker-results-dir", type=Path)
    p_mat.add_argument("--from-status", default="blocked")
    p_mat.add_argument("--to-status", default="ready")
    p_mat.add_argument("--hermes-bin", default="hermes")
    p_mat.add_argument("--main-assignee", default="factory-orchestrator")
    p_mat.add_argument("--worker-assignee-prefix", default="")
    p_mat.add_argument("--worker-ready", action="store_true")
    p_mat.add_argument("--ensure-board", action="store_true")
    p_mat.add_argument("--dry-run", action="store_true")
    p_mat.add_argument("--route-readiness", type=Path)
    p_mat.add_argument("--out", type=Path)

    p_bridge_start = sub.add_parser(
        "materialize-bridge-start",
        help="Create the fresh blocked Hermes start board/card from a factory_bridge_start_request.",
    )
    p_bridge_start.add_argument("--start-request", type=Path, required=True)
    p_bridge_start.add_argument("--source-envelope", type=Path)
    p_bridge_start.add_argument("--board")
    p_bridge_start.add_argument("--board-name")
    p_bridge_start.add_argument("--title")
    p_bridge_start.add_argument("--assignee", default=BRIDGE_START_DEFAULT_ASSIGNEE)
    p_bridge_start.add_argument("--workspace", default="scratch")
    p_bridge_start.add_argument("--default-workdir")
    p_bridge_start.add_argument("--hermes-bin", default="hermes")
    p_bridge_start.add_argument("--dry-run", action="store_true")
    p_bridge_start.add_argument("--no-ensure-board", action="store_true")
    p_bridge_start.add_argument(
        "--hold-start",
        action="store_true",
        help="Create and verify the blocked root card but intentionally do not release the factory start.",
    )
    p_bridge_start.add_argument(
        "--no-dispatch",
        action="store_true",
        help="Release the start root card to ready but do not invoke native Hermes dispatch.",
    )
    p_bridge_start.add_argument("--out", type=Path)

    p_ready = sub.add_parser(
        "materialize-ready-work-units",
        help="Create blocked Hermes tasks from a ready work-unit materialization plan.",
    )
    p_ready.add_argument("--plan", type=Path, required=True)
    p_ready.add_argument("--board")
    p_ready.add_argument("--hermes-bin", default="hermes")
    p_ready.add_argument("--worker-assignee-prefix", default="")
    p_ready.add_argument("--workspace")
    p_ready.add_argument("--ensure-board", action="store_true")
    p_ready.add_argument("--dry-run", action="store_true")
    p_ready.add_argument("--route-readiness", type=Path)
    p_ready.add_argument("--out", type=Path)

    p_release = sub.add_parser(
        "release-ready-work-units",
        help="Release verified blocked ready work-unit tasks to ready without dispatching workers.",
    )
    p_release.add_argument("--plan", type=Path, required=True)
    p_release.add_argument("--materialization-result", type=Path, required=True)
    p_release.add_argument("--board")
    p_release.add_argument("--hermes-bin", default="hermes")
    p_release.add_argument("--worker-assignee-prefix", default="")
    p_release.add_argument("--route-readiness", type=Path, required=True)
    p_release.add_argument("--reason")
    p_release.add_argument("--dry-run", action="store_true")
    p_release.add_argument("--out", type=Path)

    p_recover_ready = sub.add_parser(
        "recover-ready-work-units",
        help="Plan or create clean replacements for contaminated ready work-unit runtime tasks.",
    )
    p_recover_ready.add_argument("--plan", type=Path, required=True)
    p_recover_ready.add_argument("--materialization-result", type=Path, required=True)
    p_recover_ready.add_argument("--board")
    p_recover_ready.add_argument("--hermes-bin", default="hermes")
    p_recover_ready.add_argument("--worker-assignee-prefix", default="")
    p_recover_ready.add_argument("--route-readiness", type=Path)
    p_recover_ready.add_argument("--workspace")
    p_recover_ready.add_argument("--create-replacements", action="store_true")
    p_recover_ready.add_argument("--out", type=Path)

    p_reconcile_ready = sub.add_parser(
        "reconcile-ready-work-units",
        help="Reconcile post-release blocked ready work units after repair/review evidence.",
    )
    p_reconcile_ready.add_argument("--plan", type=Path, required=True)
    p_reconcile_ready.add_argument("--materialization-result", type=Path, required=True)
    p_reconcile_ready.add_argument("--board")
    p_reconcile_ready.add_argument("--hermes-bin", default="hermes")
    p_reconcile_ready.add_argument("--worker-assignee-prefix", default="")
    p_reconcile_ready.add_argument("--route-readiness", type=Path)
    p_reconcile_ready.add_argument("--reason")
    p_reconcile_ready.add_argument("--create-post-repair-review-tasks", action="store_true")
    p_reconcile_ready.add_argument("--create-post-repair-authority-tasks", action="store_true")
    p_reconcile_ready.add_argument("--post-repair-review-workspace")
    p_reconcile_ready.add_argument("--post-repair-authority-workspace")
    p_reconcile_ready.add_argument("--completion-result", default="Ready work-unit reconciliation satisfied.")
    p_reconcile_ready.add_argument(
        "--completion-summary",
        default="Post-release repair/review evidence reconciled by Overkill Factory.",
    )
    p_reconcile_ready.add_argument("--dry-run", action="store_true")
    p_reconcile_ready.add_argument("--out", type=Path)

    p_close_reviewed_ready = sub.add_parser(
        "close-reviewed-ready-work-units",
        help="Complete blocked ready work units only after exact independent-reviewer PASS evidence.",
    )
    p_close_reviewed_ready.add_argument("--plan", type=Path, required=True)
    p_close_reviewed_ready.add_argument("--materialization-result", type=Path, required=True)
    p_close_reviewed_ready.add_argument("--board")
    p_close_reviewed_ready.add_argument("--hermes-bin", default="hermes")
    p_close_reviewed_ready.add_argument("--worker-assignee-prefix", default="")
    p_close_reviewed_ready.add_argument("--completion-result")
    p_close_reviewed_ready.add_argument("--completion-summary")
    p_close_reviewed_ready.add_argument("--dry-run", action="store_true")
    p_close_reviewed_ready.add_argument("--out", type=Path)

    p_close_product_run = sub.add_parser(
        "close-product-creation-run",
        help="Aggregate terminal reviewed ready work units into the next product-level gate without dispatching.",
    )
    p_close_product_run.add_argument("--product-creation-plan", type=Path, required=True)
    p_close_product_run.add_argument("--plan", type=Path, required=True)
    p_close_product_run.add_argument("--materialization-result", type=Path, required=True)
    p_close_product_run.add_argument("--board")
    p_close_product_run.add_argument("--hermes-bin", default="hermes")
    p_close_product_run.add_argument("--worker-assignee-prefix", default="")
    p_close_product_run.add_argument("--release-readiness-ref")
    p_close_product_run.add_argument("--product-delivery-ref")
    p_close_product_run.add_argument("--product-promotion-gate-ref")
    p_close_product_run.add_argument("--learnback-ref")
    p_close_product_run.add_argument("--next-assignee")
    p_close_product_run.add_argument("--workspace", default="scratch")
    p_close_product_run.add_argument("--dry-run", action="store_true")
    p_close_product_run.add_argument("--out", type=Path)

    p_close_release_readiness_review = sub.add_parser(
        "close-release-readiness-review",
        help="Consume an independent-reviewer release-readiness PASS/BLOCK without approving production release.",
    )
    p_close_release_readiness_review.add_argument("--board", required=True)
    p_close_release_readiness_review.add_argument("--parent-task", required=True)
    p_close_release_readiness_review.add_argument("--review-task", required=True)
    p_close_release_readiness_review.add_argument("--hermes-bin", default="hermes")
    p_close_release_readiness_review.add_argument("--worker-assignee-prefix", default="")
    p_close_release_readiness_review.add_argument("--repair-missing-parent-edge", action="store_true")
    p_close_release_readiness_review.add_argument("--dry-run", action="store_true")
    p_close_release_readiness_review.add_argument("--out", type=Path)

    p_route = sub.add_parser(
        "collect-route-readiness",
        help="Collect the public-safe Hermes worker route readiness manifest from read-only Hermes state.",
    )
    p_route.add_argument("--plan", type=Path)
    p_route.add_argument("--worker", action="append", default=[])
    p_route.add_argument("--hermes-bin", default="hermes")
    p_route.add_argument("--required-auth-provider", default="OpenAI Codex")
    p_route.add_argument("--credential-evidence-ref", default="external:hermes-status-auth-provider-ready")
    p_route.add_argument("--ledger-ref", default="external:hermes-worker-route-readiness-ledger")
    p_route.add_argument("--out", type=Path)

    p_done = sub.add_parser("enforce-done", help="Validate worker results before completing the main card.")
    p_done.add_argument("--card", type=Path, required=True)
    p_done.add_argument("--board", required=True)
    p_done.add_argument("--main-task-id", required=True)
    p_done.add_argument("--receipt", type=Path, required=True)
    p_done.add_argument("--worker-results-dir", type=Path, required=True)
    p_done.add_argument("--ledger", type=Path, required=True)
    p_done.add_argument("--from-status", default="ready")
    p_done.add_argument("--to-status", default="done")
    p_done.add_argument("--hermes-bin", default="hermes")
    p_done.add_argument("--complete-main", action="store_true")
    p_done.add_argument("--route-readiness", type=Path)
    p_done.add_argument("--artifact-path", type=Path, action="append", default=[])
    p_done.add_argument("--attachment-root", type=Path)
    p_done.add_argument("--result", default="Overkill Factory gate satisfied.")
    p_done.add_argument("--summary", default="Worker evidence reconciled by Overkill Factory.")
    p_done.add_argument("--out", type=Path)

    p_dispatch = sub.add_parser("dispatch", help="Run native Hermes dispatch and enrich the public-safe result.")
    p_dispatch.add_argument("--board", required=True)
    p_dispatch.add_argument("--hermes-bin", default="hermes")
    p_dispatch.add_argument("--dry-run", action="store_true")
    p_dispatch.add_argument("--max", type=int)
    p_dispatch.add_argument("--failure-limit", type=int)
    p_dispatch.add_argument("--out", type=Path)

    p_no_idle = sub.add_parser("no-idle", help="Enforce the no-idle invariant without replacing native Hermes dispatch.")
    p_no_idle.add_argument("--board", required=True)
    p_no_idle.add_argument("--hermes-bin", default="hermes")
    p_no_idle.add_argument("--create-remediation", action="store_true")
    p_no_idle.add_argument("--workspace", default="scratch")
    p_no_idle.add_argument("--assignee", default="factory-orchestrator")
    p_no_idle.add_argument("--out", type=Path)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        if args.command == "materialize":
            envelope = materialize(args)
        elif args.command == "materialize-bridge-start":
            envelope = materialize_bridge_start(args)
        elif args.command == "materialize-ready-work-units":
            envelope = materialize_ready_work_units(args)
        elif args.command == "release-ready-work-units":
            envelope = release_ready_work_units(args)
        elif args.command == "recover-ready-work-units":
            envelope = recover_ready_work_units(args)
        elif args.command == "reconcile-ready-work-units":
            envelope = reconcile_ready_work_units(args)
        elif args.command == "close-reviewed-ready-work-units":
            envelope = close_reviewed_ready_work_units(args)
        elif args.command == "close-product-creation-run":
            envelope = close_product_creation_run(args)
        elif args.command == "close-release-readiness-review":
            envelope = close_release_readiness_review(args)
        elif args.command == "collect-route-readiness":
            envelope = collect_route_readiness(args)
        elif args.command == "enforce-done":
            envelope = enforce_done(args)
        elif args.command == "dispatch":
            envelope = dispatch(args)
        elif args.command == "no-idle":
            envelope = no_idle(args)
        else:
            raise RuntimeError(f"unsupported command: {args.command}")
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if not args.out:
        print(json.dumps(envelope, indent=2, ensure_ascii=True))
    if args.command == "enforce-done" and envelope.get("blocked"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
