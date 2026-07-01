#!/usr/bin/env python3
"""Validate worker profiles and Hermes dispatch bindings.

The public worker registry names the factory workers. This validator makes sure
each worker also has an executable agent profile and a Hermes binding. Without
that layer, a worker is only a process role, not an operable agent.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent if (ROOT.parent / ".github").exists() else ROOT
REGISTRY_PATH = ROOT / "agents" / "worker-registry.public.json"
PROFILES_PATH = ROOT / "agents" / "worker-profiles.public.json"
BINDINGS_PATH = ROOT / "agents" / "hermes-profile-bindings.public.json"
PROFILE_ALIASES_PATH = ROOT / "agents" / "profile-compatibility-aliases.public.json"
WORKFLOW_CATALOG_PATH = REPO_ROOT / "docs" / "factory-workflow.catalog.json"
SECURITY_MATRIX_PATH = REPO_ROOT / "docs" / "pt-BR" / "linha-de-producao.md"
PROFILE_SMOKE_PATH = ROOT / ".tmp" / "factory-runs" / "hermes-live" / "factory12-agent-profile-smoke.json"
PROFILE_READINESS_PATH = ROOT / "agents" / "worker-profile-readiness.public.json"
PROFILE_READINESS_REF = "agents/worker-profile-readiness.public.json"


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

ALLOWED_PHASES = {
    "F0",
    "F1",
    "F2",
    "F3",
    "F4",
    "F5",
    "F6",
    "F7",
    "F8",
    "F9",
    "F10",
    "F11",
    "F12",
    "F13",
    "F15",
    "F16",
    "F17",
    "F18",
    "F20",
    "F21",
    "F22",
    "F23",
    "F24",
    "F25",
    "F26",
    "F27",
    "projection:operator_projection",
    "gate_event:human_gate_event",
}
ALLOWED_RISKS = {"R0", "R1", "R2", "R3", "R4"}
READINESS_STATES = {
    "contract_only",
    "degraded_without_current_runtime_ledger",
    "blocked",
    "current_profile_ready",
}
SMOKE_RESULTS = {"PASS", "BLOCKED", "NOT_RUN"}
EVAL_RESULTS = {"PASS", "BLOCKED", "NOT_RUN", "WAIVED"}

EARLY_SECURITY_WORKERS = {
    "security-orchestrator",
    "appsec-owasp-specialist",
    "agentic-ai-security-specialist",
    "cloud-infra-security-specialist",
    "crypto-key-management-specialist",
    "solana-quasar-auditor",
    "detection-monitoring-worker",
}

PROCESS_AUTHORITY_FORBIDDEN_PATTERNS = [
    ("choose_route", re.compile(r"\b(choose|decide|select|pick)\s+(the\s+)?(factory\s+)?route\b", re.I)),
    ("choose_phase", re.compile(r"\b(choose|decide|select|pick)\s+(the\s+)?(factory\s+)?phase\b", re.I)),
    ("choose_specialist", re.compile(r"\b(choose|decide|select|pick)\s+(the\s+)?specialist\b", re.I)),
    ("approve_gate", re.compile(r"\bapprove\s+(the\s+)?(human\s+|release\s+|architecture\s+|factory\s+)?gates?\b", re.I)),
    ("waive_findings", re.compile(r"\bwaive\s+(blocking\s+)?findings?\b", re.I)),
    ("bypass_gate", re.compile(r"\bbypass\s+(human\s+|release\s+|factory\s+)?gates?\b", re.I)),
    ("mutate_state", re.compile(r"\bmutate\s+(card\s+|factory\s+|runtime\s+)?state\b", re.I)),
]
PROCESS_AUTHORITY_NEGATIONS = (
    "cannot",
    "can't",
    "must not",
    "mustn't",
    "never",
    "not ",
    "no ",
    "sem ",
    "não ",
    "nao ",
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def load_profile_aliases(path: Path = PROFILE_ALIASES_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    aliases_doc = load_json(path)
    aliases: dict[str, str] = {}
    for index, item in enumerate(aliases_doc.get("aliases", [])):
        if not isinstance(item, dict):
            continue
        legacy_id = str(item.get("legacy_id") or "").strip()
        target_worker_id = str(item.get("target_worker_id") or "").strip()
        if legacy_id and target_worker_id:
            aliases[legacy_id] = target_worker_id
    return aliases


def resolve_worker_alias(worker_id: str, aliases: dict[str, str]) -> str:
    return aliases.get(worker_id, worker_id)


def combined_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(combined_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(combined_text(item) for item in value)
    return str(value)


def _iter_strings(value: Any, path: str) -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(path, value)]
    if isinstance(value, list):
        items: list[tuple[str, str]] = []
        for index, item in enumerate(value):
            items.extend(_iter_strings(item, f"{path}[{index}]"))
        return items
    if isinstance(value, dict):
        items: list[tuple[str, str]] = []
        for key, item in value.items():
            items.extend(_iter_strings(item, f"{path}.{key}"))
        return items
    return []


def _is_negated(text: str, match_start: int) -> bool:
    prefix = text[max(0, match_start - 160) : match_start].lower()
    return any(marker in prefix for marker in PROCESS_AUTHORITY_NEGATIONS)


def process_authority_leakage_errors(worker_id: str, profile: dict[str, Any], worker: dict[str, Any]) -> list[str]:
    """Reject agent/profile text that turns deterministic process authority into agent authority."""

    errors: list[str] = []
    positive_authority_fields: list[tuple[str, str]] = []
    positive_authority_fields.extend(_iter_strings(profile.get("authority", {}).get("may", []), "profile.authority.may"))
    positive_authority_fields.extend(_iter_strings(worker.get("authority_max", ""), "registry.authority_max"))
    positive_authority_fields.extend(_iter_strings(profile.get("mission", ""), "profile.mission"))

    for path, text in positive_authority_fields:
        for pattern_name, pattern in PROCESS_AUTHORITY_FORBIDDEN_PATTERNS:
            for match in pattern.finditer(text):
                if not _is_negated(text, match.start()):
                    errors.append(
                        f"{worker_id}: process authority leak in {path}: {pattern_name} must be reducer/registry authority, not profile authority"
                    )

    if any(word in combined_text(profile.get("activation", {})).lower() for word in ("route", "phase", "gate", "specialist")):
        must_not = combined_text(profile.get("authority", {}).get("must_not", [])).lower()
        required_fragments = ("approve", "phase", "route")
        for fragment in required_fragments:
            if fragment not in must_not:
                errors.append(f"{worker_id}: route/phase/gate profile must explicitly forbid {fragment} authority")

    return errors


def parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        normalized = value.strip().replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def effective_readiness_rows(ledger: dict[str, Any]) -> dict[str, dict[str, Any]]:
    default_record = ledger.get("default_record", {})
    worker_rows = ledger.get("worker_readiness", {})
    if not isinstance(default_record, dict) or not isinstance(worker_rows, dict):
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for worker_id, row in worker_rows.items():
        if isinstance(row, dict):
            rows[str(worker_id)] = {**default_record, **row, "worker_id": str(worker_id)}
    return rows


def validate_readiness_ledger(
    worker_ids: set[str],
    profiles: dict[str, Any],
    bindings: dict[str, Any],
    *,
    ledger_path: Path,
    now: datetime,
) -> tuple[list[str], dict[str, dict[str, Any]]]:
    findings: list[str] = []
    if not ledger_path.exists():
        return [f"{PROFILE_READINESS_REF}: missing worker profile readiness ledger"], {}

    try:
        ledger = load_json(ledger_path)
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"{PROFILE_READINESS_REF}: invalid worker profile readiness ledger: {exc}"], {}

    rows = effective_readiness_rows(ledger)
    if not rows:
        findings.append(f"{PROFILE_READINESS_REF}: worker_readiness must contain public-safe readiness rows")
        return findings, {}

    row_ids = set(rows)
    for missing in sorted(worker_ids - row_ids):
        findings.append(f"{missing}: missing worker profile readiness row")
    for extra in sorted(row_ids - worker_ids):
        findings.append(f"{extra}: readiness row has no registered worker")

    for worker_id in sorted(worker_ids & row_ids):
        row = rows[worker_id]
        profile = profiles.get(worker_id, {}) if isinstance(profiles.get(worker_id), dict) else {}
        binding = bindings.get(worker_id, {}) if isinstance(bindings.get(worker_id), dict) else {}

        if row.get("profile_id") != profile.get("profile_id"):
            findings.append(f"{worker_id}: readiness ledger profile_id must match profile")
        if row.get("hermes_profile_name") != binding.get("hermes_profile_name"):
            findings.append(f"{worker_id}: readiness ledger hermes_profile_name must match binding")

        for field in ("packet_fixture_ref", "checked_at", "producer"):
            if not str(row.get(field) or "").strip():
                findings.append(f"{worker_id}: readiness ledger missing {field}")

        smoke_result = str(row.get("smoke_result") or "")
        eval_result = str(row.get("eval_result") or "")
        readiness_state = str(row.get("readiness_state") or "")
        if smoke_result not in SMOKE_RESULTS:
            findings.append(f"{worker_id}: readiness smoke_result must be one of {sorted(SMOKE_RESULTS)}")
        if eval_result not in EVAL_RESULTS:
            findings.append(f"{worker_id}: readiness eval_result must be one of {sorted(EVAL_RESULTS)}")
        if readiness_state not in READINESS_STATES:
            findings.append(f"{worker_id}: readiness_state must be one of {sorted(READINESS_STATES)}")

        freshness = row.get("freshness_policy")
        if not isinstance(freshness, dict):
            findings.append(f"{worker_id}: readiness ledger missing freshness_policy")
            freshness = {}
        current_claim = freshness.get("current_runtime_claim") is True
        checked_at = parse_datetime(row.get("checked_at"))
        if checked_at is None:
            findings.append(f"{worker_id}: readiness checked_at must be an ISO timestamp")

        if readiness_state == "current_profile_ready":
            if not current_claim:
                findings.append(f"{worker_id}: current_profile_ready requires freshness_policy.current_runtime_claim=true")
            if smoke_result != "PASS":
                findings.append(f"{worker_id}: current_profile_ready requires smoke_result=PASS")
            if eval_result != "PASS":
                findings.append(f"{worker_id}: current_profile_ready requires eval_result=PASS")
            max_age_days = freshness.get("max_age_days_for_current_claim")
            if not isinstance(max_age_days, int):
                findings.append(f"{worker_id}: current_profile_ready requires integer max_age_days_for_current_claim")
            elif checked_at and (now - checked_at).total_seconds() > max_age_days * 86400:
                findings.append(f"{worker_id}: current_profile_ready evidence is stale")
        elif current_claim:
            findings.append(f"{worker_id}: degraded readiness rows must not claim current runtime readiness")

    return findings, rows


def validate_workflow_catalog_alignment(
    workers: dict[str, dict[str, Any]],
    profiles: dict[str, Any],
    bindings: dict[str, Any],
    aliases: dict[str, str],
) -> list[str]:
    findings: list[str] = []
    if not WORKFLOW_CATALOG_PATH.exists():
        return ["docs/factory-workflow.catalog.json is missing"]

    try:
        workflow = load_json(WORKFLOW_CATALOG_PATH)
    except (json.JSONDecodeError, ValueError) as exc:
        return [f"docs/factory-workflow.catalog.json is invalid: {exc}"]

    phases = workflow.get("phases", [])
    if not isinstance(phases, list):
        return ["docs/factory-workflow.catalog.json phases must be an array"]

    for alias, target in sorted(aliases.items()):
        if target not in workers:
            findings.append(f"{alias}: profile alias target has no registered worker: {target}")
        if target not in profiles:
            findings.append(f"{alias}: profile alias target has no worker profile: {target}")
        if target not in bindings:
            findings.append(f"{alias}: profile alias target has no Hermes binding: {target}")

    for phase in phases:
        if not isinstance(phase, dict):
            findings.append("workflow phase rows must be objects")
            continue
        phase_id = str(phase.get("phase_id") or "").strip()
        if phase_id not in ALLOWED_PHASES:
            findings.append(f"workflow phase has unknown phase_id {phase_id!r}")
            continue

        required_workers_raw = phase.get("required_workers", [])
        if not isinstance(required_workers_raw, list):
            findings.append(f"{phase_id}: required_workers must be an array")
            required_workers_raw = []
        required_workers = [resolve_worker_alias(str(worker_id), aliases) for worker_id in required_workers_raw]

        for raw_worker_id, worker_id in zip(required_workers_raw, required_workers):
            raw_worker_id = str(raw_worker_id)
            if worker_id not in workers:
                findings.append(f"{phase_id}: required worker {raw_worker_id} resolves to missing registry worker {worker_id}")
                continue
            if worker_id not in profiles:
                findings.append(f"{phase_id}: required worker {raw_worker_id} resolves to missing profile {worker_id}")
                continue
            if worker_id not in bindings:
                findings.append(f"{phase_id}: required worker {raw_worker_id} resolves to missing Hermes binding {worker_id}")
                continue

            registry_phases = set(workers[worker_id].get("phase", []))
            profile_phases = set(profiles[worker_id].get("activation", {}).get("phases", []))
            if phase_id not in registry_phases:
                findings.append(f"{phase_id}: required worker {worker_id} missing registry phase coverage")
            if phase_id not in profile_phases:
                findings.append(f"{phase_id}: required worker {worker_id} missing profile activation phase")

        required_artifacts = set(phase.get("required_artifacts", []))
        worker_set = set(required_workers)
        if "product_creation_plan" in required_artifacts and "decomposition-planner" not in worker_set:
            findings.append(f"{phase_id}: product_creation_plan requires decomposition-planner as required worker")
        if "decomposition_coverage_review" in required_artifacts and "independent-reviewer" not in worker_set:
            findings.append(f"{phase_id}: decomposition_coverage_review requires independent-reviewer as required worker")
        if "product_implementation_readiness" in required_artifacts:
            if "decomposition_coverage_review" not in required_artifacts:
                findings.append(
                    f"{phase_id}: product_implementation_readiness must require decomposition_coverage_review in the same phase"
                )
            if "factory-orchestrator" not in worker_set:
                findings.append(f"{phase_id}: product_implementation_readiness requires factory-orchestrator as required worker")
        if phase_id == "F11" and "decomposition_coverage_review" in required_artifacts:
            findings.append("F11 must hand off to decomposition_coverage_review; it must not self-require the review it creates inputs for")
        if phase_id == "F12" and not {"decomposition_coverage_review", "product_implementation_readiness"} <= required_artifacts:
            findings.append("F12 must be the decomposition coverage and implementation readiness phase")

    return findings


def validate(
    *,
    readiness_ledger_path: Path = PROFILE_READINESS_PATH,
    now: datetime | None = None,
) -> list[str]:
    findings: list[str] = []
    registry = load_json(REGISTRY_PATH)
    profiles_doc = load_json(PROFILES_PATH)
    bindings_doc = load_json(BINDINGS_PATH)
    aliases = load_profile_aliases()
    smoke_doc_present = PROFILE_SMOKE_PATH.exists()
    smoke_doc = load_json(PROFILE_SMOKE_PATH) if smoke_doc_present else {}

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
    findings.extend(validate_workflow_catalog_alignment(workers, profiles, bindings, aliases))
    readiness_findings, _ = validate_readiness_ledger(
        worker_ids,
        profiles,
        bindings,
        ledger_path=readiness_ledger_path,
        now=(now or datetime.now(timezone.utc)),
    )
    findings.extend(readiness_findings)

    for missing in sorted(worker_ids - profile_ids):
        findings.append(f"{missing}: missing worker profile")
    for extra in sorted(profile_ids - worker_ids):
        findings.append(f"{extra}: profile has no registered worker")
    for missing in sorted(worker_ids - binding_ids):
        findings.append(f"{missing}: missing Hermes profile binding")
    for extra in sorted(binding_ids - worker_ids):
        findings.append(f"{extra}: binding has no registered worker")
    smoke_ids = set(smoke_by_worker)
    if smoke_doc_present:
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
            if "dispatch_queue_policy" in binding:
                findings.append(f"{worker_id}: binding must use factory_gate_timing_policy, not dispatch_queue_policy")
            policy = binding.get("factory_gate_timing_policy")
            if not isinstance(policy, dict):
                findings.append(f"{worker_id}: binding missing factory_gate_timing_policy")
            else:
                if "source_of_truth" in policy:
                    findings.append(f"{worker_id}: factory_gate_timing_policy must not claim source_of_truth")
                if policy.get("policy_kind") != "factory_gate_timing_policy":
                    findings.append(f"{worker_id}: factory_gate_timing_policy.policy_kind must be factory_gate_timing_policy")
                if policy.get("policy_basis") != "factoryctl.worker_gate_timing_class":
                    findings.append(f"{worker_id}: gate timing policy basis must be factoryctl.worker_gate_timing_class")
                if policy.get("runtime_authority") != "hermes_kanban":
                    findings.append(f"{worker_id}: gate timing runtime authority must be hermes_kanban")
                if not policy.get("default_queue"):
                    findings.append(f"{worker_id}: factory_gate_timing_policy missing default_queue")
                if not policy.get("allowed_effective_queues"):
                    findings.append(f"{worker_id}: factory_gate_timing_policy missing allowed_effective_queues")
            for field in (
                "profile_manifest_ref",
                "profile_description_ref",
                "skill_install_ref",
            ):
                ref = str(binding.get(field) or "").strip()
                if not ref:
                    findings.append(f"{worker_id}: binding missing {field}")
                elif ref.startswith(("http://", "https://", "external:")):
                    pass
                elif not ((ROOT / ref).exists() or (REPO_ROOT / ref).exists()):
                    findings.append(f"{worker_id}: binding {field} does not exist: {ref}")
            smoke_ref = str(binding.get("last_hermes_smoke_ref") or "").strip()
            if not smoke_ref:
                findings.append(f"{worker_id}: binding missing last_hermes_smoke_ref")
            elif not smoke_ref.startswith((".tmp/", "external:", "http://", "https://")):
                findings.append(f"{worker_id}: last_hermes_smoke_ref must point to generated .tmp output or an external runtime ref")
            if not str(binding.get("toolset_policy") or "").strip():
                findings.append(f"{worker_id}: binding missing toolset_policy")
            result_schema = str(binding.get("result_schema") or "").strip()
            if not result_schema:
                findings.append(f"{worker_id}: binding missing result_schema")
            elif not ((ROOT / result_schema).exists() or (REPO_ROOT / result_schema).exists()):
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
        findings.extend(process_authority_leakage_errors(worker_id, profile, worker))
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
        findings.append("docs/pt-BR/linha-de-producao.md is missing")
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
