#!/usr/bin/env python3
"""Audit gerente/agent freshness for factory changes.

This guard prevents the historical failure mode where factory contracts were
updated but the gerente or worker profiles kept stale skills/configs and tried
to behave as the factory in prompt space. The gerente is the human bridge; it
must operate current factory code and contracts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-manager-agent-freshness-policy.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-manager-agent-freshness-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-manager-agent-freshness-audit.md"

REQUIRED_LAYERS = {"manager_profile", "agent_profiles", "agent_bindings", "skills", "configs"}
REQUIRED_AUDITS = {
    "factory_master_update_plan_audit",
    "factory_runtime_truth_spine_audit",
    "factory_canonical_frontier_audit",
    "factory_manager_agent_freshness_audit",
}


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

    _require(registry.get("record_type") == "factory_manager_agent_freshness_policy", errors, "$.record_type must be factory_manager_agent_freshness_policy")

    gate = registry.get("freshness_gate", {}) if isinstance(registry.get("freshness_gate"), dict) else {}
    _require(gate.get("required_for_every_factory_change") is True, errors, "freshness gate must be required for every factory change")
    layers = set(str(item) for item in _as_list(gate.get("required_layers")))
    missing_layers = sorted(REQUIRED_LAYERS - layers)
    _require(not missing_layers, errors, "freshness_gate.required_layers missing: " + ", ".join(missing_layers))
    _require("affected" in str(gate.get("affected_agent_policy", "")).lower(), errors, "freshness gate must define affected-agent policy")

    manager = registry.get("manager_contract", {}) if isinstance(registry.get("manager_contract"), dict) else {}
    _require(manager.get("manager_profile") == "overkill-factory-gerente", errors, "manager profile must be overkill-factory-gerente")
    _require(manager.get("manager_may_replace_factory_code") is False, errors, "manager must not replace factory code")
    _require(manager.get("must_call_current_factory_contracts") is True, errors, "manager must call current factory contracts")
    audits = set(str(item) for item in _as_list(manager.get("required_factory_audits")))
    missing_audits = sorted(REQUIRED_AUDITS - audits)
    _require(not missing_audits, errors, "manager_contract.required_factory_audits missing: " + ", ".join(missing_audits))
    forbidden = "\n".join(str(item) for item in _as_list(manager.get("forbidden_patterns"))).lower()
    for term in ("stale", "worker contacts operator", "without profile freshness smoke"):
        _require(term in forbidden, errors, f"manager forbidden patterns must include {term}")

    operator = registry.get("operator_bridge_policy", {}) if isinstance(registry.get("operator_bridge_policy"), dict) else {}
    _require(operator.get("single_human_facing_profile") == "overkill-factory-gerente", errors, "operator bridge must use overkill-factory-gerente")
    _require(operator.get("direct_worker_operator_contact_allowed") is False, errors, "direct worker/operator contact must be forbidden")
    _require(operator.get("operator_polling_kanban_required") is False, errors, "operator must not be required to poll Kanban")

    smoke = registry.get("freshness_smoke", {}) if isinstance(registry.get("freshness_smoke"), dict) else {}
    _require(smoke.get("required") is True, errors, "freshness smoke must be required")
    proves = "\n".join(str(item) for item in _as_list(smoke.get("proves"))).lower()
    for term in ("gerente", "current factory contracts", "worker bindings", "gerente only"):
        _require(term in proves, errors, f"freshness smoke proof must mention {term}")
    commands = "\n".join(str(item) for item in _as_list(smoke.get("commands")))
    for command in ("factory_manager_agent_freshness_audit.py", "validate_worker_profiles.py", "validate_public_json_artifacts.py"):
        _require(command in commands, errors, f"freshness smoke commands missing {command}")

    acceptance = registry.get("acceptance", {}) if isinstance(registry.get("acceptance"), dict) else {}
    for key in ("manager_current", "agents_current", "manager_uses_factory_code", "manager_only_bridge"):
        _require(acceptance.get(key) is True, errors, f"$.acceptance.{key} must be true")

    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_manager_agent_freshness_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "manager_profile": manager.get("manager_profile"),
        "summary": {
            "errors": len(errors),
            "freshness_layer_count": len(layers),
            "required_audit_count": len(audits),
            "smoke_command_count": len(_as_list(smoke.get("commands"))),
        },
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory Manager/Agent Freshness Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append(f"Manager profile: {report['manager_profile']}")
    lines.append("")
    lines.append("The gerente is the single human bridge. It must operate current factory code and contracts; it must never try to be the factory in prompt space.")
    lines.append("")
    lines.append("## Required freshness layers")
    lines.append("")
    for layer in registry.get("freshness_gate", {}).get("required_layers", []):
        lines.append(f"- {layer}")
    lines.append("")
    lines.append("## Smoke commands")
    lines.append("")
    for command in registry.get("freshness_smoke", {}).get("commands", []):
        lines.append(f"- `{command}`")
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
