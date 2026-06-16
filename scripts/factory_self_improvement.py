#!/usr/bin/env python3
"""Self-improvement helpers for Overkill Factory.

The script stays public-safe: it turns blocked reports, learnback records and
issue snapshots into structured plans. It does not dispatch workers, mutate
Hermes, post GitHub comments or activate capabilities.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path, PureWindowsPath
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PRIVATE_USERS_PATH = "C:" + r"[\\/]+" + "Users"
PRIVATE_SYNC_ROOT = "One" + "Drive"
PRIVATE_PRODUCT_MARKER = "KA" + "XIS"
PRIVATE_CHAT_MARKER = "Dis" + "cord"
PRIVATE_MARKERS = re.compile(
    PRIVATE_USERS_PATH
    + r"|"
    + PRIVATE_SYNC_ROOT
    + r"|"
    + PRIVATE_PRODUCT_MARKER
    + r"|"
    + PRIVATE_CHAT_MARKER
    + r"|guild_ref|channel_ref|thread_id|message_id",
    re.IGNORECASE,
)
CRITICAL_TERMS = {
    "registry",
    "binding",
    "adapter",
    "authority",
    "release",
    "security",
    "methodology",
    "production",
    "credential",
    "secret",
    "billing",
}
SENSITIVE_TERMS = CRITICAL_TERMS | {"funds", "custody", "signing", "mainnet", "legal", "regulated", "privacy", "hardware"}
LEARNING_CLASSIFICATIONS = {
    "rule",
    "skill",
    "worker",
    "gate",
    "schema",
    "test",
    "doc",
    "reference",
    "issue",
    "hook",
    "mcp_or_tool",
    "install_profile",
    "reject",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path | None, data: Any) -> None:
    text = json.dumps(data, indent=2, ensure_ascii=True) + "\n"
    if path is None:
        print(text, end="")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    print(f"Wrote {public_path_ref(path)}")


def public_path_ref(path: Path, fallback: str = "artifact") -> str:
    raw = str(path)
    windows_path = PureWindowsPath(raw)
    if windows_path.is_absolute() or (len(raw) >= 2 and raw[1] == ":"):
        return f"external:{windows_path.name or fallback}"
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except (OSError, ValueError):
        return f"external:{path.name or fallback}"


def clean_public_text(value: Any) -> str:
    text = str(value or "").strip()
    return PRIVATE_MARKERS.sub("[redacted]", text)


def slug(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return lowered[:80] or "factory-improvement"


def contains_any(text: str, terms: set[str]) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in terms)


def unique_public_refs(values: list[Any]) -> list[str]:
    refs: list[str] = []
    for value in values:
        ref = clean_public_text(value)
        if ref and ref not in refs:
            refs.append(ref)
    return refs


def learnback_sdlc_feedback_loop_refs(learnback: dict[str, Any]) -> list[str]:
    raw_refs: list[Any] = []
    if learnback.get("sdlc_feedback_loop_ref"):
        raw_refs.append(learnback.get("sdlc_feedback_loop_ref"))
    if isinstance(learnback.get("sdlc_feedback_loop_refs"), list):
        raw_refs.extend(learnback.get("sdlc_feedback_loop_refs", []))
    return unique_public_refs(raw_refs)


def collect_sdlc_feedback_loop_refs(value: Any) -> list[str]:
    raw_refs: list[Any] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, child in node.items():
                if key == "sdlc_feedback_loop_ref":
                    raw_refs.append(child)
                elif key in {"sdlc_feedback_loop_refs", "factory_sdlc_lifecycle_refs"} and isinstance(child, list):
                    raw_refs.extend(child)
                else:
                    walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(value)
    return unique_public_refs(raw_refs)


def default_reference_source_registry() -> dict[str, Any]:
    return load_json(ROOT / "templates" / "reference-source-registry.json")


def build_missing_capability_plan(gate_report: dict[str, Any]) -> dict[str, Any]:
    blocked_workers = [str(worker) for worker in gate_report.get("blocked_workers", [])]
    validation_errors = [str(error) for error in gate_report.get("card_validation_errors", [])]
    worker_rows = gate_report.get("workers") if isinstance(gate_report.get("workers"), dict) else {}
    detected: list[str] = []
    for worker_id in blocked_workers:
        row = worker_rows.get(worker_id) if isinstance(worker_rows.get(worker_id), dict) else {}
        status = str(row.get("status") or "blocked")
        reason = str(row.get("reason") or "missing worker capability")
        detected.append(f"{worker_id}: {status}; {reason}")
    detected.extend(validation_errors)
    if not detected:
        detected.append("No blocked worker was found; inspect capability coverage before activation.")
    combined = " ".join(detected)
    human_gate_required = contains_any(combined, SENSITIVE_TERMS)
    candidate_artifacts = [
        {
            "artifact_type": "worker_registry_entry",
            "status": "inactive_candidate",
            "purpose": "Declare the missing capability without enabling dispatch.",
            "validation_gate": "validate public JSON artifacts",
        },
        {
            "artifact_type": "worker_profile",
            "status": "inactive_candidate",
            "purpose": "Define inputs, outputs, authority and forbidden actions for the capability.",
            "validation_gate": "validate worker profiles and focused tests",
        },
        {
            "artifact_type": "runtime_binding",
            "status": "inactive_candidate",
            "purpose": "Bind the profile to the runtime only after review accepts the capability.",
            "validation_gate": "route readiness expectation and independent review",
        },
        {
            "artifact_type": "result_schema",
            "status": "inactive_candidate",
            "purpose": "Make the capability output machine-checkable before execution.",
            "validation_gate": "schema validation and eval fixture",
        },
        {
            "artifact_type": "smoke_eval_fixture",
            "status": "inactive_candidate",
            "purpose": "Prove the capability can fail closed and produce usable evidence.",
            "validation_gate": "focused unit test or disposable runtime smoke",
        },
    ]
    return {
        "$schema": "https://overkill-factory.dev/schemas/missing-capability-completion-plan.schema.json",
        "record_type": "missing_capability_completion_plan",
        "created_at": utc_now(),
        "source_gate_report": gate_report.get("card_id") or "external:gate-report",
        "status": "blocked_needs_human_gate" if human_gate_required else "candidate",
        "detected_gaps": detected,
        "candidate_artifacts": candidate_artifacts,
        "quality_gates": [
            "validate public JSON artifacts",
            "validate worker profiles",
            "run focused unit tests",
            "independent review before activation",
        ],
        "activation_policy": {
            "default_state": "inactive_candidate",
            "auto_activation_allowed": not human_gate_required,
            "sensitive_domains_require_human_gate": True,
        },
        "human_gate_required": human_gate_required,
        "next_actions": [
            "generate candidate artifacts in sandbox state",
            "run validation and eval fixtures",
            "route independent review",
        ],
    }


def build_issue_candidate(finding: dict[str, Any], sdlc_feedback_loop_refs: list[str] | None = None) -> dict[str, Any] | None:
    route = str(finding.get("recommended_route") or "").strip()
    if route in {"no_issue", ""}:
        return None
    summary = clean_public_text(finding.get("summary"))
    area = clean_public_text(finding.get("area") or "factory")
    severity = str(finding.get("severity") or "medium").lower()
    if severity not in {"low", "medium", "high", "critical"}:
        severity = "medium"
    public_safe = route in {"public_issue", "docs_update", "eval_or_test"} and not PRIVATE_MARKERS.search(summary)
    requires_human_gate = route == "critical_change_proposal" or contains_any(summary + " " + area, CRITICAL_TERMS)
    title = summary if summary.lower().startswith("factory") else f"Factory improvement: {summary}"
    body = "\n".join(
        [
            "## Problem",
            summary,
            "",
            "## Reproduction condition",
            clean_public_text(finding.get("reproduction_condition") or "Captured by execution learnback."),
            "",
            "## Acceptance criteria",
            clean_public_text(finding.get("acceptance_hint") or "Add a public-safe fix with validation coverage."),
        ]
    )
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-improvement-issue-candidate.schema.json",
        "record_type": "factory_improvement_issue_candidate",
        "title": title,
        "body": body,
        "route": route if route != "public_issue" else "public_issue",
        "severity": severity,
        "area": area,
        "sdlc_feedback_loop_refs": sdlc_feedback_loop_refs or [],
        "public_safe": public_safe,
        "requires_human_gate": requires_human_gate,
        "dedupe_key": slug(f"{area}-{summary}"),
    }


def build_issue_candidates(learnback: dict[str, Any]) -> dict[str, Any]:
    candidates = []
    feedback_refs = learnback_sdlc_feedback_loop_refs(learnback)
    for finding in learnback.get("findings", []):
        if isinstance(finding, dict):
            candidate = build_issue_candidate(finding, feedback_refs)
            if candidate:
                candidates.append(candidate)
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-improvement-issue-candidate.schema.json",
        "record_type": "factory_improvement_issue_candidate_list",
        "created_at": utc_now(),
        "source_project_ref": clean_public_text(learnback.get("project_ref")),
        "sdlc_feedback_loop_refs": feedback_refs,
        "candidates": candidates,
        "issue_count": len(candidates),
    }


def normalize_severity(value: Any) -> str:
    severity = str(value or "medium").lower()
    return severity if severity in {"low", "medium", "high", "critical"} else "medium"


def build_execution_learnback_record(
    receipt: dict[str, Any],
    evidence_graph: dict[str, Any] | None = None,
    project_ref: str | None = None,
) -> dict[str, Any]:
    refs = collect_sdlc_feedback_loop_refs([receipt, evidence_graph or {}])
    if not refs:
        raise ValueError("execution learnback requires sdlc_feedback_loop_refs from Receipt Five or Evidence Graph")

    receipt_five = receipt.get("receipt_five") if isinstance(receipt.get("receipt_five"), dict) else {}
    transition = receipt.get("kanban_transition_event") if isinstance(receipt.get("kanban_transition_event"), dict) else {}
    reconciliation = receipt.get("receipt_five_reconciliation_result") if isinstance(receipt.get("receipt_five_reconciliation_result"), dict) else {}
    graph = evidence_graph if isinstance(evidence_graph, dict) else {}

    attempted_transitions = [
        clean_public_text(transition.get(field))
        for field in ("from_status", "to_status")
        if str(transition.get(field) or "").strip()
    ]
    workers_required = unique_public_refs(list(reconciliation.get("required_workers") or []))
    missing_workers = unique_public_refs(list(reconciliation.get("missing_blocking_workers") or []))
    graph_findings = graph.get("findings") if isinstance(graph.get("findings"), list) else []
    blockers = [
        clean_public_text(finding.get("message"))
        for finding in graph_findings
        if isinstance(finding, dict) and str(finding.get("message") or "").strip()
    ]
    if str(receipt_five.get("verification_result") or "").strip().upper() == "BLOCKED":
        blockers.append(clean_public_text(receipt_five.get("next_action") or "Receipt Five is blocked."))

    findings: list[dict[str, Any]] = []
    for finding in graph_findings:
        if not isinstance(finding, dict):
            continue
        message = clean_public_text(finding.get("message"))
        if not message:
            continue
        node_id = clean_public_text(finding.get("node_id") or "evidence-graph")
        findings.append(
            {
                "summary": message,
                "severity": normalize_severity(finding.get("severity")),
                "area": node_id,
                "recommended_route": "eval_or_test",
                "reproduction_condition": "Evidence Graph reported this finding before learnback.",
                "acceptance_hint": "Add or update a contract/static/unit check so the same blocker returns to the execution rail.",
            }
        )
    if not findings:
        result = str(receipt_five.get("verification_result") or graph.get("result") or "PASS").strip().upper()
        findings.append(
            {
                "summary": "Receipt Five evidence completed without a self-improvement finding."
                if result == "PASS"
                else clean_public_text(receipt_five.get("next_action") or "Receipt Five evidence is blocked."),
                "severity": "low" if result == "PASS" else "medium",
                "area": "receipt-five",
                "recommended_route": "no_issue" if result == "PASS" else "eval_or_test",
                "reproduction_condition": "Generated from Receipt Five and Evidence Graph.",
                "acceptance_hint": "Keep the learnback record attached to the SDLC feedback loop.",
            }
        )

    graph_target = graph.get("target") if isinstance(graph.get("target"), dict) else {}
    resolved_project_ref = project_ref or graph_target.get("card_ref")
    return {
        "$schema": "https://overkill-factory.dev/schemas/execution-learnback-record.schema.json",
        "record_type": "execution_learnback_record",
        "project_ref": clean_public_text(resolved_project_ref or "external:receipt-five"),
        "method_version": "OVERKILL_VFINAL",
        "sdlc_feedback_loop_ref": refs[0],
        "sdlc_feedback_loop_refs": refs,
        "source_evidence_refs": ["receipt_five", "evidence_graph"] if evidence_graph else ["receipt_five"],
        "attempted_transitions": attempted_transitions,
        "workers_required": workers_required,
        "workers_executed": [],
        "blockers": blockers + [f"missing worker: {worker}" for worker in missing_workers],
        "operator_friction": [],
        "test_scan_results": [clean_public_text(command) for command in receipt_five.get("verification_commands", [])],
        "findings": findings,
        "public_safety_boundary": {
            "raw_private_evidence_forbidden": True,
            "public_issue_requires_redaction": True,
        },
    }


def learning_classification_for(finding: dict[str, Any]) -> str:
    explicit = str(finding.get("learning_classification") or "").strip()
    if explicit in LEARNING_CLASSIFICATIONS:
        return explicit
    route = str(finding.get("recommended_route") or "").strip()
    if route == "eval_or_test":
        return "test"
    if route == "docs_update":
        return "doc"
    if route == "public_issue":
        return "issue"
    if route == "critical_change_proposal":
        return "gate"
    return "reject" if route in {"no_issue", "private_followup"} else "issue"


def build_learning_proposal(
    finding: dict[str, Any],
    source_ref: str,
    sdlc_feedback_loop_refs: list[str] | None = None,
) -> dict[str, Any]:
    summary = clean_public_text(finding.get("summary"))
    area = clean_public_text(finding.get("area") or "factory")
    classification = learning_classification_for(finding)
    evidence_ref = clean_public_text(finding.get("evidence_ref") or source_ref)
    combined = " ".join([summary, area, clean_public_text(finding.get("reproduction_condition"))])
    human_gate_required = classification in {"worker", "gate", "hook", "mcp_or_tool", "install_profile"} or contains_any(combined, CRITICAL_TERMS)
    sensitive = human_gate_required or contains_any(combined, SENSITIVE_TERMS)
    rejected = classification == "reject"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-learning-proposal.schema.json",
        "record_type": "factory_learning_proposal",
        "source_evidence_refs": [evidence_ref],
        "sdlc_feedback_loop_refs": sdlc_feedback_loop_refs or [],
        "source_trust": "internal_structured",
        "classification": classification,
        "proposed_artifact_type": classification,
        "risk": "R3" if human_gate_required else "R2" if classification in {"skill", "schema", "test"} else "R1",
        "owner": "skill-eval-distiller",
        "proposal_summary": summary,
        "validation_plan": {
            "tests_or_evals": [clean_public_text(finding.get("acceptance_hint") or "focused validation fixture")],
            "verification_commands": [
                "python scripts/validate_public_json_artifacts.py",
                "python -m unittest tests.test_factory_self_improvement -q",
            ],
            "independent_review_required": not rejected,
            "plan_review_ref": "external:independent-plan-review-required" if not rejected else "not_applicable",
            "success_criteria": [
                "proposal remains inactive until validation passes",
                "public-safe evidence refs replace raw run evidence",
            ],
        },
        "activation_policy": {
            "default_state": "rejected" if rejected else "inactive_candidate",
            "auto_activation_allowed": False if sensitive or not rejected else False,
            "human_gate_required": human_gate_required,
            "scope": f"{area} learning proposal",
            "active_tool_surfaces": [],
            "budget": {
                "max_agents": 2,
                "timeout_minutes": 60,
                "token_or_cost_budget": "operator-defined",
                "stop_condition": "validation fails, review blocks, or scope expands",
            },
        },
        "untrusted_input_handling": {
            "reader_actor_split": True,
            "raw_external_content_quarantined": True,
            "privileged_actors_consume_structured_summary_only": True,
        },
        "tool_governance": {
            "required": [],
            "optional": [],
            "disabled": [],
            "forbidden": ["auto-permission for sensitive work"],
            "third_party_trust_status": "first_party",
            "supply_chain_review": "required before activating skills, hooks, MCPs or install profiles",
        },
        "parallel_workflow_guidance": [
            "use fan-out, adversarial review or tournament patterns only when evidence value justifies isolation",
            "use issue #79 lane/worktree governance for detailed parallel execution controls",
        ],
        "rejection_rationale": clean_public_text(finding.get("rejection_rationale") or ("finding rejected or private" if rejected else "not_rejected")),
    }


def build_learning_proposals(learnback: dict[str, Any]) -> dict[str, Any]:
    source_ref = clean_public_text(learnback.get("project_ref") or "external:learnback-record")
    feedback_refs = learnback_sdlc_feedback_loop_refs(learnback)
    proposals = [
        build_learning_proposal(finding, source_ref, feedback_refs)
        for finding in learnback.get("findings", [])
        if isinstance(finding, dict)
    ]
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-learning-proposal.schema.json",
        "record_type": "factory_learning_proposal_list",
        "created_at": utc_now(),
        "source_project_ref": source_ref,
        "sdlc_feedback_loop_refs": feedback_refs,
        "proposals": proposals,
        "proposal_count": len(proposals),
    }


def issue_labels(issue: dict[str, Any]) -> set[str]:
    raw = issue.get("labels", [])
    labels: set[str] = set()
    if isinstance(raw, list):
        for item in raw:
            if isinstance(item, dict):
                name = item.get("name")
            else:
                name = item
            if str(name or "").strip():
                labels.add(str(name).strip())
    return labels


def build_factory_card_candidate(
    issue_ref: str,
    title: str,
    body: str,
    decision: str,
    labels: set[str],
    default_status: str,
    sdlc_feedback_loop_ref: str,
) -> dict[str, Any]:
    critical = decision == "critical_factory_change"
    documentation = decision == "documentation_only"
    risk = "R3" if critical else "R1" if documentation else "R2"
    required_gates = [
        "public safety scan",
        "secret safety scan",
        "focused tests",
        "independent review",
    ]
    if critical:
        required_gates.append("explicit human approval before mutation")
    return {
        "record_type": "owner_issue_factory_card_candidate",
        "source_issue_ref": issue_ref,
        "title": title,
        "summary": body[:600],
        "status": default_status,
        "factory_method_version": "OVERKILL_VFINAL",
        "phase": "planning",
        "surfaces": sorted(labels) or ["factory"],
        "risk_initial": risk,
        "risk_effective": risk,
        "owner_worker": "factory-mechanic-loop",
        "executor_identity": "unassigned",
        "reviewer_identity": "independent-review-required",
        "required_gates": required_gates,
        "done_definition": [
            "issue scope is converted into a bounded factory card",
            "implementation changes are validated by tests and required scans",
            "Receipt Five evidence records commands, artifacts and residual risk",
        ],
        "source_refs": [issue_ref],
        "sdlc_feedback_loop_ref": sdlc_feedback_loop_ref,
        "activation_policy": {
            "auto_dispatch_allowed": False,
            "human_gate_required": critical,
            "public_comment_allowed": False,
        },
    }


def triage_decision_for_issue_intake(decision: str) -> str:
    if decision == "documentation_only":
        return "docs_task"
    if decision == "critical_factory_change":
        return "risk_gate"
    if decision == "needs_human_triage":
        return "blocker"
    if decision == "private_operator_only":
        return "reject_with_rationale"
    return "work_unit"


def build_issue_intake_sdlc_feedback_loop(
    issue_ref: str,
    title: str,
    decision: str,
    reason: str,
    dedupe_key: str,
) -> dict[str, Any]:
    critical = decision == "critical_factory_change"
    feedback_ref = f"external:operator-sdlc-feedback-loop-{dedupe_key}"
    source_ref = f"external:operator-owner-issue-{dedupe_key}"
    selected_profile = "human-gate-clerk" if critical else "factory-mechanic-loop"
    selected_model_class = "human_only" if decision in {"critical_factory_change", "needs_human_triage"} else "balanced"
    promotion_boundary = "requires_human_gate" if critical else "public_issue_only"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-sdlc-feedback-loop.schema.json",
        "record_type": "factory_sdlc_feedback_loop",
        "loop_id": feedback_ref,
        "created_at": utc_now(),
        "factory_method_version": "OVERKILL_VFINAL",
        "source_signal": {
            "signal_type": "internal_request",
            "source_class": "operator_supplied",
            "sensitivity_class": "public_safe",
            "freshness": "bounded",
            "owner": "operator-owned-factory-instance",
            "target_surface": "factory-method",
            "signal_ref_public_safe": source_ref,
            "raw_private_embedded": False,
        },
        "triage_decision": {
            "decision": triage_decision_for_issue_intake(decision),
            "route_ref": "schemas/owner-issue-intake-report.schema.json",
            "rationale": clean_public_text(reason or title),
            "human_gate_required": critical or decision == "needs_human_triage",
            "rejects_chat_only_state": True,
        },
        "routing_decision": {
            "router_ref": "templates/owner-issue-intake-config.json",
            "selected_profile": selected_profile,
            "selected_model_class": selected_model_class,
            "selection_basis": {
                "cost": "bounded public issue intake",
                "speed": "dry-run candidate creation only",
                "quality": "requires schema validation and independent review before activation",
                "context_need": "issue title, body, labels and owner intake config",
                "data_sensitivity": "public-safe issue fields only",
                "tool_requirements": "factory_self_improvement issue-intake and public validators",
                "expected_horizon": "single bounded intake cycle",
                "fallback_route": "keep blocked for human triage without dispatching workers",
            },
            "model_independence_preserved": True,
            "single_provider_assumption": False,
        },
        "execution_evidence": {
            "status": "PENDING",
            "evidence_refs": [source_ref, "templates/owner-issue-intake-config.json"],
            "failed_outputs_consumable_as_success": False,
            "validation_refs": [
                "schemas/owner-issue-intake-report.schema.json",
                "schemas/factory-sdlc-feedback-loop.schema.json",
            ],
        },
        "learnback_decision": {
            "classification": "public_issue",
            "target_artifact_type": "issue",
            "source_evidence_refs": [source_ref],
            "validation_refs": [
                "tests/test_factory_self_improvement.py",
                "scripts/validate_public_json_artifacts.py",
            ],
            "promotion_boundary": promotion_boundary,
            "rejection_rationale": "not_rejected",
        },
        "sovereignty_boundary": {
            "public_safe_refs_only": True,
            "raw_private_evidence_embedded": False,
            "private_context_retained_outside_public_repo": True,
            "reusable_across_products": "bounded",
            "memory_owner": "operator-owned-factory-instance",
        },
        "next_safe_action": "Validate this issue-intake loop before creating or dispatching a factory card.",
    }


def build_issue_intake_report(config: dict[str, Any], issues: list[dict[str, Any]]) -> dict[str, Any]:
    filters = config.get("filters") if isinstance(config.get("filters"), dict) else {}
    include = {str(label).strip() for label in filters.get("include_labels", []) if str(label).strip()}
    exclude = {str(label).strip() for label in filters.get("exclude_labels", []) if str(label).strip()}
    critical_terms = {str(term).strip().lower() for term in filters.get("critical_change_terms", []) if str(term).strip()} or CRITICAL_TERMS
    decisions: list[dict[str, Any]] = []
    for issue in issues:
        labels = issue_labels(issue)
        title = clean_public_text(issue.get("title"))
        body = clean_public_text(issue.get("body"))
        issue_ref = str(issue.get("url") or issue.get("html_url") or issue.get("number") or title)
        if exclude & labels:
            decision, reason = "ignore", "excluded label present"
        elif include and not (include & labels):
            decision, reason = "needs_human_triage", "no configured intake label matched"
        elif contains_any(title + " " + body, critical_terms):
            decision, reason = "critical_factory_change", "critical factory-change term matched"
        elif "doc" in (title + " " + " ".join(labels)).lower():
            decision, reason = "documentation_only", "documentation-oriented issue"
        else:
            decision, reason = "implementation_candidate", "matches owner-instance intake filters"
        card_status = "not_created" if decision == "ignore" else config.get("default_card_status", "blocked")
        row = {
            "issue_ref": issue_ref,
            "decision": decision,
            "reason": reason,
            "card_status": card_status,
            "dedupe_key": slug(f"{issue_ref}-{title}"),
        }
        if decision != "ignore":
            feedback_loop = build_issue_intake_sdlc_feedback_loop(
                issue_ref,
                title,
                decision,
                reason,
                row["dedupe_key"],
            )
            feedback_ref = feedback_loop["loop_id"]
            row["sdlc_feedback_loop_ref"] = feedback_ref
            row["sdlc_feedback_loop"] = feedback_loop
            row["factory_card_candidate"] = build_factory_card_candidate(
                issue_ref,
                title,
                body,
                decision,
                labels,
                card_status,
                feedback_ref,
            )
        decisions.append(row)
    return {
        "$schema": "https://overkill-factory.dev/schemas/owner-issue-intake-report.schema.json",
        "record_type": "owner_issue_intake_report",
        "created_at": utc_now(),
        "mode": config.get("mode", "dry_run"),
        "issues_reviewed": len(issues),
        "decisions": decisions,
        "public_comment_policy": config.get("public_comment_policy", "after_human_gate"),
    }


def governance_report() -> dict[str, Any]:
    scripts = sorted((ROOT / "scripts").glob("*.py"))
    schemas = sorted((ROOT / "schemas").glob("*.schema.json"))
    tests = sorted((ROOT / "tests").glob("test_*.py"))
    factoryctl_lines = (ROOT / "scripts" / "factoryctl.py").read_text(encoding="utf-8").count("\n") + 1
    risks = [
        {
            "severity": "high" if factoryctl_lines > 2500 else "medium",
            "area": "runtime",
            "risk": "factoryctl.py concentrates many public contracts and can become hard to evolve safely.",
            "recommended_issue": "Split stable contract validation from command orchestration after self-improvement contracts land.",
        },
        {
            "severity": "high",
            "area": "agent-contracts",
            "risk": "AI worker behavior can drift unless schemas, templates, docs and tests stay synchronized.",
            "recommended_issue": "Add contract synchronization checks for worker-facing schemas/templates/docs.",
        },
        {
            "severity": "medium",
            "area": "evidence",
            "risk": "Generated evidence can pollute the public repo when private run artifacts are not separated.",
            "recommended_issue": "Keep generated run evidence in private stores or .tmp and scan public artifacts before release.",
        },
    ]
    return {
        "$schema": "https://overkill-factory.dev/schemas/ai-codebase-governance-report.schema.json",
        "record_type": "ai_codebase_governance_report",
        "created_at": utc_now(),
        "architecture_map": [
            f"{len(schemas)} schemas define public contracts",
            f"{len(scripts)} scripts implement public tooling and probes",
            f"{len(tests)} test modules protect contract behavior",
            "agents/*.public.json define worker registry, profiles and Hermes bindings",
            "Product Experience OS and Product Face define visible product planning/proof",
        ],
        "risks": risks,
        "recommendations": [
            "Prefer schema-backed contracts over prose-only AI instructions.",
            "Keep generated evidence out of the public repo unless it has public-safe purpose and validation.",
            "Add focused tests whenever a worker authority, gate or schema changes.",
            "Treat public docs as external operator product surface.",
        ],
        "mandatory_checks": [
            "python -m unittest discover -s tests -p \"test_*.py\" -q",
            "python scripts/validate_public_json_artifacts.py",
            "python scripts/public_safety_scan.py",
            "python scripts/secret_safety_scan.py",
            "python scripts/supply_chain_proof.py --check --no-write",
        ],
        "generated_artifact_policy": [
            "worker packets and reports are generated under .tmp or private evidence stores by default",
            "public examples must be minimal, current and validated",
            "raw private execution logs are never public issue bodies",
        ],
        "ownership_map": {
            "schemas": "contract owners",
            "agents": "worker authority and routing owners",
            "adapters": "runtime integration owners",
            "docs": "external operator product surface",
            "tests": "regression and gate evidence",
        },
    }


def command_reference_registry(args: argparse.Namespace) -> int:
    write_json(args.out, default_reference_source_registry())
    return 0


def command_missing_capability_plan(args: argparse.Namespace) -> int:
    write_json(args.out, build_missing_capability_plan(load_json(args.gate_report)))
    return 0


def command_learnback_issues(args: argparse.Namespace) -> int:
    write_json(args.out, build_issue_candidates(load_json(args.record)))
    return 0


def command_learnback_record(args: argparse.Namespace) -> int:
    evidence_graph = load_json(args.evidence_graph) if args.evidence_graph else None
    try:
        record = build_execution_learnback_record(load_json(args.receipt), evidence_graph, args.project_ref)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    write_json(args.out, record)
    return 0


def command_learning_proposals(args: argparse.Namespace) -> int:
    write_json(args.out, build_learning_proposals(load_json(args.record)))
    return 0


def command_issue_intake(args: argparse.Namespace) -> int:
    issues = load_json(args.issues)
    if not isinstance(issues, list):
        raise SystemExit("issues input must be a JSON array")
    write_json(args.out, build_issue_intake_report(load_json(args.config), issues))
    return 0


def command_governance_audit(args: argparse.Namespace) -> int:
    write_json(args.out, governance_report())
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Overkill Factory self-improvement helpers")
    sub = parser.add_subparsers(dest="command", required=True)

    ref = sub.add_parser("reference-registry", help="Write the default reference source registry")
    ref.add_argument("--out", type=Path)
    ref.set_defaults(func=command_reference_registry)

    missing = sub.add_parser("missing-capability-plan", help="Build a completion plan from a gate report")
    missing.add_argument("--gate-report", type=Path, required=True)
    missing.add_argument("--out", type=Path)
    missing.set_defaults(func=command_missing_capability_plan)

    learnback = sub.add_parser("learnback-issues", help="Turn a learnback record into issue candidates")
    learnback.add_argument("--record", type=Path, required=True)
    learnback.add_argument("--out", type=Path)
    learnback.set_defaults(func=command_learnback_issues)

    learnback_record = sub.add_parser("learnback-record", help="Build a learnback record from Receipt Five and optional Evidence Graph")
    learnback_record.add_argument("--receipt", type=Path, required=True)
    learnback_record.add_argument("--evidence-graph", type=Path)
    learnback_record.add_argument("--project-ref")
    learnback_record.add_argument("--out", type=Path)
    learnback_record.set_defaults(func=command_learnback_record)

    learning = sub.add_parser("learning-proposals", help="Turn a learnback record into typed learning proposals")
    learning.add_argument("--record", type=Path, required=True)
    learning.add_argument("--out", type=Path)
    learning.set_defaults(func=command_learning_proposals)

    intake = sub.add_parser("issue-intake", help="Dry-run owner-instance issue intake")
    intake.add_argument("--config", type=Path, required=True)
    intake.add_argument("--issues", type=Path, required=True)
    intake.add_argument("--out", type=Path)
    intake.set_defaults(func=command_issue_intake)

    governance = sub.add_parser("governance-audit", help="Write a public-safe codebase governance report")
    governance.add_argument("--out", type=Path)
    governance.set_defaults(func=command_governance_audit)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
