"""Canonical operating-system registry for Overkill Factory."""

from __future__ import annotations

import json
import re
import sysconfig
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OPERATING_SYSTEM_REGISTRY_PATH = ROOT / "templates" / "factory-operating-system-registry.json"

REQUIRED_OS_IDS = {
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
    "quality_verification_os",
    "operator_experience_os",
    "release_operations_os",
    "velocity_cost_throughput_os",
    "factory_learning_os",
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

EXPECTED_ISSUES = {
    "deterministic_control_plane_os": 400,
    "product_truth_research_os": 401,
    "method_os": 402,
    "product_architecture_os": 403,
    "product_experience_design_brand_os": 404,
    "work_unit_execution_dispatch_os": 405,
    "authority_autonomy_os": 406,
    "hermes_worker_runtime_os": 407,
    "evidence_receipt_os": 408,
    "capability_provider_os": 409,
    "agent_profile_authority_os": 410,
    "security_os": 411,
    "quality_verification_os": 412,
    "operator_experience_os": 413,
    "release_operations_os": 414,
    "velocity_cost_throughput_os": 415,
    "factory_learning_os": 416,
}

FACTORYCTL_COMMANDS = {
    "briefing-package",
    "compile-workflow",
    "evidence-graph",
    "evidence-record",
    "export-hermes-evidence",
    "full-scope-coverage",
    "gate-report",
    "help-next",
    "human-gate-record",
    "intake",
    "method-contract",
    "method-engines",
    "operator-interface",
    "operating-system-scorecard",
    "operating-systems",
    "outcome-contract",
    "product-implementation-readiness",
    "product-creation-plan",
    "product-sot",
    "ready-work-unit-hermes-plan",
    "ready-work-unit-packets",
    "route-registry",
    "source-ledger",
    "source-resolution",
    "start-conversation",
    "status-snapshot",
    "understanding-confirmation",
    "validate-card",
    "validate-capability-acquisition-contract",
    "validate-completion",
    "validate-evidence-bundle",
    "validate-factory-command",
    "validate-factory-event-log",
    "validate-factory-run",
    "validate-hermes-reducer-mutation-proof",
    "validate-method-contract",
    "validate-operating-systems",
    "validate-phase-graph",
    "validate-product-experience-control-plane",
    "validate-v2-study-traceability",
    "validate-worker-authority-contract",
    "validate-promotion-packet",
    "validate-readiness-claim",
    "validate-receipt",
    "validate-ready-work-unit-packets",
    "validate-workflow-compiled-plan",
    "worker-packet",
}

REPO_REF_PREFIXES = (
    "adapters/",
    "agents/",
    "docs/",
    "schemas/",
    "scripts/",
    "templates/",
    "tests/",
)

PRIVATE_REF_RE = re.compile(
    r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|/var/|guild[_-]?id|channel[_-]?id|message[_-]?id)",
    re.I,
)


def operating_system_registry_candidates() -> list[Path]:
    data_root = Path(sysconfig.get_path("data") or "")
    return [
        DEFAULT_OPERATING_SYSTEM_REGISTRY_PATH,
        ROOT / "share" / "overkill-factory" / "templates" / "factory-operating-system-registry.json",
        data_root / "share" / "overkill-factory" / "templates" / "factory-operating-system-registry.json",
    ]


def load_operating_system_registry(path: Path | None = None) -> dict[str, Any]:
    if path is not None:
        registry_path = path
    else:
        registry_path = next(
            (candidate for candidate in operating_system_registry_candidates() if candidate.exists()),
            DEFAULT_OPERATING_SYSTEM_REGISTRY_PATH,
        )
    return json.loads(registry_path.read_text(encoding="utf-8"))


def operating_system_entries(registry: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = registry or load_operating_system_registry()
    entries = data.get("entries") if isinstance(data.get("entries"), list) else []
    return {
        str(entry.get("os_id")): entry
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("os_id") or "").strip()
    }


def _list_items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _contains_text(value: Any, text: str) -> bool:
    needle = text.lower()
    if isinstance(value, str):
        return needle in value.lower()
    if isinstance(value, list):
        return any(_contains_text(item, text) for item in value)
    if isinstance(value, dict):
        return any(_contains_text(item, text) for item in value.values())
    return False


def _private_ref_errors(value: Any, at: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if PRIVATE_REF_RE.search(value):
            errors.append(f"{at}: operating-system registry must not publish private/local refs")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_private_ref_errors(item, f"{at}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_private_ref_errors(item, f"{at}.{key}"))
    return errors


def _repo_ref_path(ref: str) -> Path | None:
    clean = ref.split("#", 1)[0].strip()
    if not clean:
        return None
    if clean.startswith(REPO_REF_PREFIXES):
        return ROOT / clean
    return None


def _repo_ref_errors(refs: Any, at: str) -> list[str]:
    errors: list[str] = []
    for index, raw_ref in enumerate(_list_items(refs)):
        ref = str(raw_ref or "").strip()
        path = _repo_ref_path(ref)
        if path is not None and not path.exists():
            errors.append(f"{at}[{index}] points to missing repo ref: {ref}")
    return errors


def _enforcement_command_errors(refs: Any, at: str) -> list[str]:
    errors: list[str] = []
    for index, raw_ref in enumerate(_list_items(refs)):
        ref = str(raw_ref or "").strip()
        if ref.startswith("factoryctl "):
            parts = ref.split()
            command = parts[1] if len(parts) > 1 else ""
            if command not in FACTORYCTL_COMMANDS:
                errors.append(f"{at}[{index}] points to unknown factoryctl command: {ref}")
            continue
        if ref.startswith("python "):
            parts = ref.split()
            script = next((part for part in parts[1:] if part.startswith("scripts/")), "")
            if not script:
                errors.append(f"{at}[{index}] python command must reference a scripts/ path: {ref}")
                continue
            if not (ROOT / script).exists():
                errors.append(f"{at}[{index}] points to missing script: {script}")
            continue
        errors.append(f"{at}[{index}] must reference factoryctl or a repo script command: {ref}")
    return errors


def validate_operating_system_registry_semantics(registry: dict[str, Any], at: str = "$") -> list[str]:
    errors: list[str] = []
    entries = operating_system_entries(registry)
    missing = sorted(REQUIRED_OS_IDS - set(entries))
    if missing:
        errors.append(f"{at}.entries: missing required operating systems: " + ", ".join(missing))
    extra = sorted(set(entries) - REQUIRED_OS_IDS)
    if extra:
        errors.append(f"{at}.entries: unknown operating systems: " + ", ".join(extra))

    coverage = registry.get("coverage_policy") if isinstance(registry.get("coverage_policy"), dict) else {}
    required_policy_flags = {
        "all_p0_systems_have_issue": True,
        "all_systems_have_runtime_boundary": True,
        "all_systems_have_fail_closed_rules": True,
        "all_systems_separate_contract_from_runtime_proof": True,
    }
    for field, expected in required_policy_flags.items():
        if coverage.get(field) is not expected:
            errors.append(f"{at}.coverage_policy.{field}: expected {expected!r}")

    claim_policy = registry.get("completion_claim_policy") if isinstance(registry.get("completion_claim_policy"), dict) else {}
    if claim_policy.get("registry_alone_allows_completion_claim") is not False:
        errors.append(f"{at}.completion_claim_policy.registry_alone_allows_completion_claim must be false")
    if claim_policy.get("product_specific_production_claim_allowed") is not False:
        errors.append(f"{at}.completion_claim_policy.product_specific_production_claim_allowed must be false")
    if claim_policy.get("runtime_proof_required_before_production_claim") is not True:
        errors.append(f"{at}.completion_claim_policy.runtime_proof_required_before_production_claim must be true")

    boundary = registry.get("public_private_boundary") if isinstance(registry.get("public_private_boundary"), dict) else {}
    if boundary.get("public_safe_refs_only") is not True:
        errors.append(f"{at}.public_private_boundary.public_safe_refs_only must be true")
    if boundary.get("raw_private_evidence_embedded") is not False:
        errors.append(f"{at}.public_private_boundary.raw_private_evidence_embedded must be false")
    if boundary.get("private_context_retained_outside_public_repo") is not True:
        errors.append(f"{at}.public_private_boundary.private_context_retained_outside_public_repo must be true")

    seen_issue_numbers: set[int] = set()
    for os_id, entry in entries.items():
        entry_at = f"{at}.entries[{os_id}]"
        expected_issue = EXPECTED_ISSUES.get(os_id)
        issue_number = entry.get("issue_number")
        issue_url = str(entry.get("issue_url") or "")
        if expected_issue is not None and issue_number != expected_issue:
            errors.append(f"{entry_at}.issue_number must be {expected_issue}")
        if expected_issue is not None and not issue_url.endswith(f"/issues/{expected_issue}"):
            errors.append(f"{entry_at}.issue_url must point to issue #{expected_issue}")
        if isinstance(issue_number, int):
            if issue_number in seen_issue_numbers:
                errors.append(f"{entry_at}.issue_number duplicates another OS issue")
            seen_issue_numbers.add(issue_number)
        if os_id in P0_OS_IDS and entry.get("priority") != "P0":
            errors.append(f"{entry_at}.priority must be P0")

        errors.extend(_repo_ref_errors(entry.get("primary_contract_refs"), f"{entry_at}.primary_contract_refs"))
        errors.extend(_repo_ref_errors(entry.get("source_of_truth_refs"), f"{entry_at}.source_of_truth_refs"))
        errors.extend(_repo_ref_errors(entry.get("mapped_docs"), f"{entry_at}.mapped_docs"))
        errors.extend(_repo_ref_errors(entry.get("validation_test_refs"), f"{entry_at}.validation_test_refs"))
        errors.extend(_enforcement_command_errors(entry.get("enforcement_command_refs"), f"{entry_at}.enforcement_command_refs"))

        for test_index, raw_ref in enumerate(_list_items(entry.get("validation_test_refs"))):
            test_ref = str(raw_ref or "").strip()
            if not test_ref.startswith("tests/"):
                errors.append(f"{entry_at}.validation_test_refs[{test_index}] must live under tests/: {test_ref}")

        if entry.get("status") in {"active", "hardened_existing"}:
            if not _list_items(entry.get("enforcement_command_refs")):
                errors.append(f"{entry_at}.enforcement_command_refs must be non-empty for active OS")
            if not _list_items(entry.get("validation_test_refs")):
                errors.append(f"{entry_at}.validation_test_refs must be non-empty for active OS")

        runtime_boundary = entry.get("runtime_boundary") if isinstance(entry.get("runtime_boundary"), dict) else {}
        expected_boundary = {
            "hermes_source_of_truth": True,
            "worker_results_required": True,
            "receipt_five_required": True,
            "bridge_may_execute_factory_work": False,
            "human_gate_can_be_auto_approved": False,
            "local_validation_is_production_proof": False,
        }
        for field, expected in expected_boundary.items():
            if runtime_boundary.get(field) is not expected:
                errors.append(f"{entry_at}.runtime_boundary.{field}: expected {expected!r}")

        if not _list_items(entry.get("fail_closed_rules")):
            errors.append(f"{entry_at}.fail_closed_rules must be non-empty")
        if not _list_items(entry.get("required_runtime_proofs")):
            errors.append(f"{entry_at}.required_runtime_proofs must be non-empty")
        if entry.get("production_claim_state") == "production_claim_allowed":
            errors.append(f"{entry_at}.production_claim_state cannot allow production claim from registry alone")

    if "hermes_worker_runtime_os" in entries and not _contains_text(
        entries["hermes_worker_runtime_os"].get("required_runtime_proofs"),
        "live_hermes_worker_orchestration",
    ):
        errors.append(f"{at}.entries[hermes_worker_runtime_os]: missing live_hermes_worker_orchestration proof")
    if "capability_provider_os" in entries and not _contains_text(entries["capability_provider_os"], "solana-ai-kit-core"):
        errors.append(f"{at}.entries[capability_provider_os]: must mention solana-ai-kit-core")
    if "operator_experience_os" in entries and not _contains_text(entries["operator_experience_os"], "telegram"):
        errors.append(f"{at}.entries[operator_experience_os]: must mention Telegram-first operation")
    if "product_truth_research_os" in entries and not _contains_text(entries["product_truth_research_os"], "Product SOT"):
        errors.append(f"{at}.entries[product_truth_research_os]: must protect Product SOT promotion")

    errors.extend(_private_ref_errors(registry, at))
    return errors


def _completion_audit_blocking_ids(completion_audit: dict[str, Any] | None) -> set[str]:
    if not completion_audit:
        return set()
    requirements = completion_audit.get("requirements") if isinstance(completion_audit.get("requirements"), list) else []
    blocking_ids: set[str] = set()
    for item in requirements:
        if not isinstance(item, dict):
            continue
        if item.get("blocking") is True and str(item.get("status") or "").upper() != "ACHIEVED":
            requirement_id = str(item.get("id") or "").strip()
            if requirement_id:
                blocking_ids.add(requirement_id)
    return blocking_ids


def _hermes_runtime_proof_ready(proof: dict[str, Any]) -> bool:
    if proof.get("record_type") != "hermes_production_proof":
        return False
    if proof.get("proof_type") != "non_stub_worker_execution":
        return False
    if proof.get("result") != "PASS":
        return False
    summary = proof.get("runtime_summary") if isinstance(proof.get("runtime_summary"), dict) else {}
    gate = proof.get("operator_gate_boundary") if isinstance(proof.get("operator_gate_boundary"), dict) else {}
    required_summary_flags = (
        "gateway_running",
        "openai_codex_logged_in",
        "telegram_configured",
        "manager_profile_running",
        "current_board_detected",
        "live_worker_orchestration_proven",
        "human_gate_block_event_detected",
    )
    return (
        all(summary.get(flag) is True for flag in required_summary_flags)
        and int(summary.get("profile_count") or 0) >= 5
        and int(summary.get("current_board_total_tasks") or 0) >= 1
        and gate.get("human_gate_auto_approved") is False
        and gate.get("bridge_or_manager_executed_gate") is False
    )


def build_operating_system_scorecard(
    registry: dict[str, Any],
    *,
    registry_ref: str = "templates/factory-operating-system-registry.json",
    completion_audit: dict[str, Any] | None = None,
    completion_audit_ref: str | None = None,
    runtime_proofs: list[dict[str, Any]] | None = None,
    runtime_proof_refs: list[str] | None = None,
) -> dict[str, Any]:
    blocking_ids = _completion_audit_blocking_ids(completion_audit)
    runtime_proofs = runtime_proofs or []
    runtime_proof_refs = runtime_proof_refs or []
    hermes_runtime_proven = any(_hermes_runtime_proof_ready(proof) for proof in runtime_proofs)
    os_results: list[dict[str, Any]] = []
    for os_id, entry in sorted(operating_system_entries(registry).items()):
        owned_blockers = [
            str(blocker)
            for blocker in _list_items(entry.get("completion_audit_blockers_owned"))
            if str(blocker).strip()
        ]
        active_blockers = sorted(set(owned_blockers) & blocking_ids)
        findings: list[str] = []
        status = str(entry.get("status") or "")
        if status == "planned":
            findings.append("OS is tracked but not implemented as a complete operating layer yet.")
        runtime_proof_state = "NOT_REQUIRED"
        os_runtime_proof_refs: list[str] = []
        if os_id == "hermes_worker_runtime_os":
            os_runtime_proof_refs = runtime_proof_refs
            runtime_proof_state = "PROVEN" if hermes_runtime_proven else "MISSING"
        if status == "blocked_pending_runtime_proof" and runtime_proof_state != "PROVEN":
            findings.append("OS requires live runtime proof before production use.")
        if active_blockers:
            findings.append("Completion audit has active blockers owned by this OS: " + ", ".join(active_blockers))
        if str(entry.get("priority") or "") == "P0" and findings:
            readiness_state = "BLOCKED"
        elif findings:
            readiness_state = "ATTENTION"
        else:
            readiness_state = "READY_BY_CONTRACT"
        os_results.append(
            {
                "os_id": os_id,
                "display_name": str(entry.get("display_name") or os_id),
                "priority": str(entry.get("priority") or "P1"),
                "issue_url": str(entry.get("issue_url") or ""),
                "registry_status": status,
                "readiness_state": readiness_state,
                "completion_audit_blockers_owned": owned_blockers,
                "active_completion_audit_blockers": active_blockers,
                "runtime_proof_state": runtime_proof_state,
                "runtime_proof_refs": os_runtime_proof_refs,
                "blocking_findings": findings,
                "next_action": (
                    "close the linked issue with contract, runtime proof and validation evidence"
                    if findings
                    else "keep validation fresh when related surfaces change"
                ),
            }
        )

    p0_blocked = [
        item["os_id"]
        for item in os_results
        if item["priority"] == "P0" and item["readiness_state"] != "READY_BY_CONTRACT"
    ]
    result = "BLOCKED" if p0_blocked else "PASS"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-operating-system-scorecard.schema.json",
        "record_type": "factory_operating_system_scorecard",
        "scorecard_id": "factory-operating-system-scorecard-v1",
        "registry_ref": registry_ref,
        "completion_audit_ref": completion_audit_ref,
        "runtime_proof_refs": runtime_proof_refs,
        "result": result,
        "p0_total": len(P0_OS_IDS),
        "p0_blocked": p0_blocked,
        "os_results": os_results,
        "completion_claim_policy": {
            "scorecard_alone_allows_completion_claim": False,
            "product_specific_production_claim_allowed": False,
            "blocked_until_p0_ready_and_runtime_proven": bool(p0_blocked),
        },
        "public_private_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
            "private_context_retained_outside_public_repo": True,
        },
    }


def validate_operating_system_scorecard_semantics(scorecard: dict[str, Any], at: str = "$") -> list[str]:
    errors: list[str] = []
    if scorecard.get("result") == "PASS" and scorecard.get("p0_blocked"):
        errors.append(f"{at}: PASS cannot include blocked P0 operating systems")
    claim_policy = scorecard.get("completion_claim_policy") if isinstance(scorecard.get("completion_claim_policy"), dict) else {}
    if claim_policy.get("scorecard_alone_allows_completion_claim") is not False:
        errors.append(f"{at}.completion_claim_policy.scorecard_alone_allows_completion_claim must be false")
    if claim_policy.get("product_specific_production_claim_allowed") is not False:
        errors.append(f"{at}.completion_claim_policy.product_specific_production_claim_allowed must be false")
    boundary = scorecard.get("public_private_boundary") if isinstance(scorecard.get("public_private_boundary"), dict) else {}
    if boundary.get("public_safe_refs_only") is not True:
        errors.append(f"{at}.public_private_boundary.public_safe_refs_only must be true")
    if boundary.get("raw_private_evidence_embedded") is not False:
        errors.append(f"{at}.public_private_boundary.raw_private_evidence_embedded must be false")
    errors.extend(_private_ref_errors(scorecard, at))
    return errors
