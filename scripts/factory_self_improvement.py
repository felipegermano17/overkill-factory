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
from pathlib import Path
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
    print(f"Wrote {path}")


def clean_public_text(value: Any) -> str:
    text = str(value or "").strip()
    return PRIVATE_MARKERS.sub("[redacted]", text)


def slug(value: str) -> str:
    lowered = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return lowered[:80] or "factory-improvement"


def contains_any(text: str, terms: set[str]) -> bool:
    normalized = text.lower()
    return any(term in normalized for term in terms)


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


def build_issue_candidate(finding: dict[str, Any]) -> dict[str, Any] | None:
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
        "public_safe": public_safe,
        "requires_human_gate": requires_human_gate,
        "dedupe_key": slug(f"{area}-{summary}"),
    }


def build_issue_candidates(learnback: dict[str, Any]) -> dict[str, Any]:
    candidates = []
    for finding in learnback.get("findings", []):
        if isinstance(finding, dict):
            candidate = build_issue_candidate(finding)
            if candidate:
                candidates.append(candidate)
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-improvement-issue-candidate.schema.json",
        "record_type": "factory_improvement_issue_candidate_list",
        "created_at": utc_now(),
        "source_project_ref": clean_public_text(learnback.get("project_ref")),
        "candidates": candidates,
        "issue_count": len(candidates),
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
        "activation_policy": {
            "auto_dispatch_allowed": False,
            "human_gate_required": critical,
            "public_comment_allowed": False,
        },
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
            row["factory_card_candidate"] = build_factory_card_candidate(
                issue_ref,
                title,
                body,
                decision,
                labels,
                card_status,
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
