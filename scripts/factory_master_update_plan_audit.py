#!/usr/bin/env python3
"""Audit the public V3 master update plan for the Overkill Factory.

This is the execution bridge from the private master planning conversation to a
public, validated product artifact. It intentionally validates principles rather
than implementing runtime behavior: Hermes/Kanban remain the runtime owner; the
factory owns method, gates, rules, audits and contracts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-master-update-plan.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-master-update-plan-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-master-update-plan-audit.md"

REQUIRED_AUDITS = {
    "swiss_watch_audit",
    "method_excellence_audit",
    "world_class_process_gap_audit",
    "executor_skill_ecosystem_audit",
    "security_excellence_audit",
    "operator_ui_ux_excellence_audit",
    "os_excellence_audit",
    "github_issue_pattern_audit",
}

REQUIRED_WORKSTREAMS = {
    "W00-master-plan-registry",
    "W01-runtime-truth-spine",
    "W02-autonomy-no-idle",
    "W03-manager-agent-freshness",
    "W04-operator-experience",
    "W05-human-gate-package",
    "W06-receipt-five-anti-overclaim",
    "W07-product-method-architecture",
    "W08-capability-security-release-authority",
    "W09-public-github-v3",
    "W10-factory-perfect-run",
}

REQUIRED_PENDING = {
    "PENDING-branch-publication",
    "PENDING-skill-approval",
    "PENDING-open-issues",
    "PENDING-gerente-smoke",
    "PENDING-public-map",
}

RUNTIME_FORBIDDEN_TERMS = ("scheduler", "queue", "board", "dispatch", "task lifecycle", "parallel runtime", "mini Hermes")
FACTORY_ALLOWED_TERMS = ("method", "gate", "rule", "audit", "contract")
PUBLIC_V3_TERMS = ("readme", "public map", "first-value", "release notes", "open source")
MANAGER_TERMS = ("gerente", "skills", "profiles", "bindings")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def audit(registry: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    _require(registry.get("record_type") == "factory_master_update_plan", errors, "$.record_type must be factory_master_update_plan")
    _require(registry.get("release_target") == "V3", errors, "$.release_target must be V3")

    principles = registry.get("principles", {}) if isinstance(registry.get("principles"), dict) else {}
    for key in ("hermes_first", "kanban_first", "no_mini_hermes", "manager_agent_freshness_required", "public_github_v3_required"):
        _require(principles.get(key) is True, errors, f"$.principles.{key} must be true")

    boundary = registry.get("runtime_boundary", {}) if isinstance(registry.get("runtime_boundary"), dict) else {}
    forbidden_text = "\n".join(str(item) for item in _as_list(boundary.get("factory_must_not_own"))).lower()
    allowed_text = "\n".join(str(item) for item in _as_list(boundary.get("factory_may_own"))).lower()
    for term in RUNTIME_FORBIDDEN_TERMS:
        _require(term.lower() in forbidden_text, errors, f"$.runtime_boundary.factory_must_not_own missing {term}")
    for term in FACTORY_ALLOWED_TERMS:
        _require(term.lower() in allowed_text, errors, f"$.runtime_boundary.factory_may_own missing {term}")

    audit_inputs = _as_list(registry.get("audit_inputs"))
    audit_ids = {str(item.get("id")) for item in audit_inputs if isinstance(item, dict)}
    missing_audits = sorted(REQUIRED_AUDITS - audit_ids)
    _require(not missing_audits, errors, "$.audit_inputs missing required audit(s): " + ", ".join(missing_audits))
    for item in audit_inputs:
        if isinstance(item, dict):
            _require(len(_as_list(item.get("feeds_workstreams"))) >= 1, errors, f"audit {item.get('id')} must feed at least one workstream")

    pending_items = _as_list(registry.get("immediate_pending_items"))
    pending_ids = {str(item.get("id")) for item in pending_items if isinstance(item, dict)}
    missing_pending = sorted(REQUIRED_PENDING - pending_ids)
    _require(not missing_pending, errors, "$.immediate_pending_items missing required pending item(s): " + ", ".join(missing_pending))

    workstreams = _as_list(registry.get("workstreams"))
    workstream_ids = {str(item.get("id")) for item in workstreams if isinstance(item, dict)}
    missing_workstreams = sorted(REQUIRED_WORKSTREAMS - workstream_ids)
    _require(not missing_workstreams, errors, "$.workstreams missing required workstream(s): " + ", ".join(missing_workstreams))
    _require(len(workstreams) >= 10, errors, "$.workstreams must include at least 10 workstreams")

    by_id = {str(item.get("id")): item for item in workstreams if isinstance(item, dict)}
    runtime = by_id.get("W01-runtime-truth-spine", {})
    runtime_must_not = "\n".join(str(item) for item in _as_list(runtime.get("must_not_build"))).lower()
    for term in ("scheduler", "queue", "board", "dispatcher", "task lifecycle"):
        _require(term in runtime_must_not, errors, f"W01-runtime-truth-spine must_not_build missing {term}")

    manager = by_id.get("W03-manager-agent-freshness", {})
    manager_req = "\n".join(str(item) for item in _as_list(manager.get("requirements"))).lower()
    manager_evidence = "\n".join(str(item) for item in _as_list(manager.get("required_evidence"))).lower()
    for term in MANAGER_TERMS:
        _require(term in manager_req, errors, f"W03-manager-agent-freshness requirements missing {term}")
    _require("smoke" in manager_evidence and "factory code" in manager_evidence, errors, "W03-manager-agent-freshness evidence must prove gerente uses factory code")

    public_v3 = by_id.get("W09-public-github-v3", {})
    public_req = "\n".join(str(item) for item in _as_list(public_v3.get("requirements"))).lower()
    for term in PUBLIC_V3_TERMS:
        _require(term in public_req, errors, f"W09-public-github-v3 requirements missing {term}")

    perfect = by_id.get("W10-factory-perfect-run", {})
    _require("W09-public-github-v3" in _as_list(perfect.get("depends_on")), errors, "Factory Perfect Run must depend on public GitHub V3 readiness")

    # Every dependency must point to a known workstream.
    for ws in workstreams:
        if not isinstance(ws, dict):
            continue
        for dep in _as_list(ws.get("depends_on")):
            _require(dep in workstream_ids, errors, f"{ws.get('id')} depends on unknown workstream {dep}")
        for audit_id in _as_list(ws.get("source_audits")):
            _require(audit_id in audit_ids, errors, f"{ws.get('id')} references unknown audit {audit_id}")

    acceptance = registry.get("acceptance", {}) if isinstance(registry.get("acceptance"), dict) else {}
    for key in ("all_audits_mapped", "no_mini_hermes_guard", "manager_agent_freshness_guard", "v3_public_surface_guard", "factory_perfect_run_required"):
        _require(acceptance.get(key) is True, errors, f"$.acceptance.{key} must be true")

    p0_count = sum(1 for item in workstreams if isinstance(item, dict) and item.get("priority") == "P0")
    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_master_update_plan_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "release_target": registry.get("release_target"),
        "principles": {
            "hermes_first": principles.get("hermes_first") is True,
            "kanban_first": principles.get("kanban_first") is True,
            "no_mini_hermes": principles.get("no_mini_hermes") is True,
        },
        "summary": {
            "errors": len(errors),
            "audit_input_count": len(audit_inputs),
            "pending_item_count": len(pending_items),
            "workstream_count": len(workstreams),
            "p0_workstream_count": p0_count,
        },
        "audit_ids": sorted(audit_ids),
        "workstream_ids": sorted(workstream_ids),
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory Master Update Plan Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append(f"Release target: {report['release_target']}")
    lines.append("")
    lines.append("## Principles")
    lines.append("")
    lines.append("- Hermes-first")
    lines.append("- Kanban-first")
    lines.append("- No mini-Hermes")
    lines.append("- Gerente and agent freshness required")
    lines.append("- Public GitHub V3 surface required")
    lines.append("")
    lines.append("## Workstreams")
    lines.append("")
    for ws in registry.get("workstreams", []):
        lines.append(f"- {ws['id']} — {ws['name']} ({ws['priority']}, wave {ws['wave']})")
        lines.append(f"  - done: {ws['done_when']}")
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
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    registry = load_json(args.registry)
    report = audit(registry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, registry, args.markdown)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.markdown}")
    print(report["result"])
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
