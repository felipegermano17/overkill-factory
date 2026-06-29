#!/usr/bin/env python3
"""Audit the Hermes/Kanban-first canonical frontier policy.

The frontier chooses the next safe factory action from durable Hermes/Kanban and
FactoryRun state. It must not become a scheduler, queue, dispatch system, or
chat-memory route authority. No-idle remains an integrity auditor and recovery
path.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-canonical-frontier-policy.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-canonical-frontier-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-canonical-frontier-audit.md"

REQUIRED_GAPS = {
    "missing_declared_artifact",
    "recoverable_readback_failure",
    "stale_review_superseded_by_new_pass",
    "invalid_json_reconstructable_from_worker_diff",
    "missing_markdown_reconstructable_from_structured_metadata",
    "missing_dependency_edge_repairable",
}
REQUIRED_STATE_SOURCES = {
    "Hermes/Kanban board state readback",
    "FactoryRun event log",
    "typed block state",
    "worker result consumability state",
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

    _require(registry.get("record_type") == "factory_canonical_frontier_policy", errors, "$.record_type must be factory_canonical_frontier_policy")

    authority = registry.get("authority_model", {}) if isinstance(registry.get("authority_model"), dict) else {}
    _require(authority.get("hermes_kanban_state_required") is True, errors, "canonical frontier must require Hermes/Kanban state readback")
    _require(authority.get("no_idle_role") == "integrity_auditor_and_recovery_path", errors, "no-idle role must be integrity_auditor_and_recovery_path")
    _require(authority.get("no_idle_is_scheduler") is False, errors, "no-idle must not become a scheduler")
    sources = set(str(item) for item in _as_list(authority.get("state_sources")))
    missing_sources = sorted(REQUIRED_STATE_SOURCES - sources)
    _require(not missing_sources, errors, "authority_model.state_sources missing: " + ", ".join(missing_sources))

    gap_policy = registry.get("recoverable_gap_policy", {}) if isinstance(registry.get("recoverable_gap_policy"), dict) else {}
    _require(gap_policy.get("repair_before_needs_input") is True, errors, "recoverable gaps must route to repair before needs_input")
    gaps = set(str(item) for item in _as_list(gap_policy.get("recoverable_gap_types")))
    missing_gaps = sorted(REQUIRED_GAPS - gaps)
    _require(not missing_gaps, errors, "recoverable_gap_types missing: " + ", ".join(missing_gaps))
    needs_input = "\n".join(str(item) for item in _as_list(gap_policy.get("needs_input_only_when"))).lower()
    for term in ("authority", "risk", "ambiguous", "capability"):
        _require(term in needs_input, errors, f"needs_input_only_when must include {term}-based stop")

    budget = registry.get("budget_policy", {}) if isinstance(registry.get("budget_policy"), dict) else {}
    _require(budget.get("budgets_schedule_work") is False, errors, "budgets must not schedule work")
    for key in ("retry_budget", "repair_budget", "worker_budget"):
        item = budget.get(key, {}) if isinstance(budget.get(key), dict) else {}
        _require(item.get("authority") == "gate_rule", errors, f"{key}.authority must be gate_rule")
        _require(bool(item.get("on_exhaustion")), errors, f"{key}.on_exhaustion is required")

    action_order = [str(item).lower() for item in _as_list(registry.get("next_action_order"))]
    joined_order = "\n".join(action_order)
    _require(bool(action_order) and "hermes/kanban" in action_order[0], errors, "next_action_order must begin by reading Hermes/Kanban state")
    _require("repair" in joined_order, errors, "next_action_order must include repair lane")
    _require("needs_input" in joined_order or "typed block" in joined_order, errors, "next_action_order must include typed block/needs_input fallback")

    acceptance = registry.get("acceptance", {}) if isinstance(registry.get("acceptance"), dict) else {}
    for key in ("safe_next_action_required", "repair_before_human", "no_scheduler_overlap", "typed_stop_required"):
        _require(acceptance.get(key) is True, errors, f"$.acceptance.{key} must be true")

    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_canonical_frontier_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "summary": {
            "errors": len(errors),
            "state_source_count": len(sources),
            "recoverable_gap_count": len(gaps),
            "next_action_count": len(action_order),
        },
        "authority": {
            "hermes_kanban_state_required": authority.get("hermes_kanban_state_required") is True,
            "no_idle_role": authority.get("no_idle_role"),
            "no_idle_is_scheduler": authority.get("no_idle_is_scheduler") is True,
        },
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory Canonical Frontier Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append("")
    lines.append("The canonical frontier is Hermes/Kanban-first and no-idle remains recovery, not runtime.")
    lines.append("")
    lines.append("## Required policy")
    lines.append("")
    lines.append("- repair_before_needs_input")
    lines.append("- budgets are gate_rule, not scheduler")
    lines.append("- typed block or needs_input only when no safe autonomous action remains")
    lines.append("")
    lines.append("## Next action order")
    lines.append("")
    for item in registry.get("next_action_order", []):
        lines.append(f"- {item}")
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
