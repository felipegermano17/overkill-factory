#!/usr/bin/env python3
"""Audit the Hermes/Kanban-first runtime truth spine.

This audit is intentionally anti-runtime: it proves the factory did not create a
mini-Hermes. The factory may define contracts, gates and validation; Hermes and
Kanban own runtime state, queues, dispatch and task lifecycle.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-runtime-truth-spine.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-runtime-truth-spine-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-runtime-truth-spine-audit.md"

REQUIRED_STATES = {
    "worker_packet_created",
    "hermes_dispatch_requested",
    "hermes_task_running",
    "worker_result_consumable",
}
FORBIDDEN_FACTORY_RUNTIME_FLAGS = {
    "factory_owns_scheduler": "scheduler",
    "factory_owns_queue": "queue",
    "factory_owns_dispatch": "dispatch",
    "factory_owns_task_lifecycle": "task lifecycle",
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

    _require(registry.get("record_type") == "factory_runtime_truth_spine", errors, "$.record_type must be factory_runtime_truth_spine")

    authority = registry.get("runtime_authority", {}) if isinstance(registry.get("runtime_authority"), dict) else {}
    _require(authority.get("hermes_kanban_owns_runtime") is True, errors, "Hermes/Kanban must own runtime")
    for key, label in FORBIDDEN_FACTORY_RUNTIME_FLAGS.items():
        _require(authority.get(key) is False, errors, f"Factory must not own {label}; mini-Hermes boundary violated")

    allowed_scope = "\n".join(str(item) for item in _as_list(authority.get("factory_allowed_scope"))).lower()
    for term in ("method", "gate", "rule", "audit", "schema", "quality"):
        _require(term in allowed_scope, errors, f"factory_allowed_scope missing {term}")

    states = _as_list(registry.get("worker_lifecycle_states"))
    state_ids = {str(state.get("id")) for state in states if isinstance(state, dict)}
    missing_states = sorted(REQUIRED_STATES - state_ids)
    _require(not missing_states, errors, "missing worker lifecycle state(s): " + ", ".join(missing_states))

    eq = registry.get("state_equivalence_policy", {}) if isinstance(registry.get("state_equivalence_policy"), dict) else {}
    _require(eq.get("worker_packet_created") != eq.get("hermes_dispatch_requested"), errors, "worker packet must not equal dispatch")
    _require(eq.get("worker_packet_created") != eq.get("hermes_task_running"), errors, "worker packet must not equal execution")
    _require(eq.get("worker_packet_created") != eq.get("worker_result_consumable"), errors, "worker packet must not equal consumable result")
    _require(eq.get("worker_packet_created") != "worker_result_consumable", errors, "worker packet policy must not alias worker_result_consumable")
    _require(eq.get("worker_packet_created") == "contract_artifact_only", errors, "worker packet policy must remain contract_artifact_only")
    _require(eq.get("hermes_dispatch_requested") != eq.get("worker_result_consumable"), errors, "dispatch request must not equal consumable result")

    by_state = {str(state.get("id")): state for state in states if isinstance(state, dict)}
    _require(by_state.get("worker_packet_created", {}).get("authority") == "factory_contract", errors, "worker_packet_created authority must be factory_contract")
    _require(by_state.get("hermes_dispatch_requested", {}).get("authority") == "hermes_kanban", errors, "hermes_dispatch_requested authority must be hermes_kanban")
    _require(by_state.get("hermes_task_running", {}).get("authority") == "hermes_kanban", errors, "hermes_task_running authority must be hermes_kanban")
    _require(by_state.get("worker_result_consumable", {}).get("authority") == "worker_result", errors, "worker_result_consumable authority must be worker_result")

    resume = registry.get("parent_resume_policy", {}) if isinstance(registry.get("parent_resume_policy"), dict) else {}
    _require(resume.get("requires_durable_dependency_edges") is True, errors, "parent resume must require durable dependency edges")
    _require(resume.get("requires_child_result_consumable") is True, errors, "parent resume must require child result consumable")
    readback_text = "\n".join(str(item) for item in _as_list(resume.get("required_readbacks"))).lower()
    _require("hermes/kanban dependency edge readback" in readback_text, errors, "parent resume must read back Hermes/Kanban dependency edge")
    forbidden_resume = "\n".join(str(item) for item in _as_list(resume.get("forbidden_parent_resume_conditions"))).lower()
    _require("worker packet exists" in forbidden_resume, errors, "forbidden resume conditions must include packet-only state")

    links = set(str(item) for item in _as_list(registry.get("factory_run_links")))
    for required_ref in ("templates/factory-run.json", "schemas/factory-run.schema.json", "schemas/worker-packet.schema.json"):
        _require(required_ref in links, errors, f"factory_run_links missing {required_ref}")

    acceptance = registry.get("acceptance", {}) if isinstance(registry.get("acceptance"), dict) else {}
    for key in ("packet_not_execution", "no_mini_hermes", "dependency_edges_required", "hermes_state_readback_required"):
        _require(acceptance.get(key) is True, errors, f"$.acceptance.{key} must be true")

    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_runtime_truth_spine_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "runtime_authority": {
            "hermes_kanban_owns_runtime": authority.get("hermes_kanban_owns_runtime") is True,
            "factory_owns_scheduler": authority.get("factory_owns_scheduler") is True,
            "factory_owns_queue": authority.get("factory_owns_queue") is True,
            "factory_owns_dispatch": authority.get("factory_owns_dispatch") is True,
            "factory_owns_task_lifecycle": authority.get("factory_owns_task_lifecycle") is True,
        },
        "summary": {
            "errors": len(errors),
            "state_count": len(states),
            "factory_run_link_count": len(links),
        },
        "state_ids": sorted(state_ids),
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory Runtime Truth Spine Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append("")
    lines.append("Hermes/Kanban owns runtime state, queues, board graph, dispatch and task lifecycle.")
    lines.append("The factory owns method, gates, rules, audits, contracts and validations.")
    lines.append("")
    lines.append("## Worker lifecycle states")
    lines.append("")
    for state in registry.get("worker_lifecycle_states", []):
        lines.append(f"- {state['id']} ({state['authority']}): {state['meaning']}")
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
