#!/usr/bin/env python3
"""Runtime enforcement rules for canonical Overkill Factory checkpoints."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACE = ROOT / ".tmp" / "factory-runs" / "canonical-linear-traceability" / "canonical-linear-traceability.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "canonical-runtime-enforcement" / "canonical-runtime-rulebook.json"
SCHEMA = "https://overkill-factory.dev/schemas/canonical-runtime-rulebook.schema.json"
FALLBACK_SOURCE_TRACE_REF = "generated:fallback-vfinal-runtime-rulebook"

NON_RUNTIME_LINEAR_STATUSES = {"foundational_text_tracked"}
CORE_RUNTIME_FIELDS = (
    "factory_method_version",
    "phase",
    "runtime_contract",
    "done_definition",
    "transition_event_required",
    "kanban_transition_event_ref",
)
VFINAL_FALLBACK_FIELDS = (
    *CORE_RUNTIME_FIELDS,
    "source_refs",
    "source_state",
    "outcome_contract",
    "product_sot",
    "method_contract",
    "capability_pack_contract",
    "software_development_plan",
    "spec_graph",
    "loop_plan",
    "product_experience_plan",
    "product_face_packet",
    "data_metrics_plan",
    "agent_eval_plan",
    "dependency_map",
    "access_capability",
    "autonomy_readiness_packet",
    "budget_contract",
    "privacy_compliance_plan",
    "security_contract",
    "security_architecture_plan",
    "review",
    "reviewer_selection_plan",
    "project_projection",
    "production_readiness_plan",
    "incident_support_plan",
    "user_docs_onboarding_plan",
    "factory_maturity_scorecard",
    "verification_plan",
    "receipt_five",
    "completion_audit",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(value: str) -> str:
    lowered = value.lower().replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _fields(*fields: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(field for field in fields if field))


def infer_required_fields(record: dict[str, Any]) -> tuple[str, ...]:
    text = normalize(
        " ".join(
            str(value or "")
            for value in (
                record.get("canonical_heading"),
                record.get("parent_heading"),
                record.get("canonical_obligation"),
            )
        )
    )
    refs = " ".join(
        str(ref.get("path") or "")
        for ref in record.get("implementation_refs", [])
        if isinstance(ref, dict)
    ).lower()
    fields: list[str] = list(CORE_RUNTIME_FIELDS)

    if "source" in text or "source" in refs or "fonte" in text:
        fields.extend(["source_refs", "source_state"])
    if "outcome" in text or "discovery" in text or "resultado" in text:
        fields.append("outcome_contract")
    if "product sot" in text:
        fields.append("product_sot")
    if "method" in text or "metodo" in text:
        fields.append("method_contract")
    if "pack" in text or "capability-pack" in refs:
        fields.append("capability_pack_contract")
    if "software" in text or "spec graph" in text or "loop plan" in text:
        fields.extend(["software_development_plan", "spec_graph", "loop_plan"])
    if "product experience" in text or "product face" in text or "experience" in text:
        fields.extend(["product_experience_plan", "product_face_packet"])
    if "data" in text or "metrics" in text or "analytics" in text:
        fields.append("data_metrics_plan")
    if "agent eval" in text or "evals" in text or "quality" in text:
        fields.append("agent_eval_plan")
    if "dependency" in text or "dependencias" in text:
        fields.append("dependency_map")
    if "access" in text or "capability" in text or "autonomy readiness" in text or "acessos" in text:
        fields.extend(["access_capability", "autonomy_readiness_packet"])
    if "budget" in text or "cost" in text or "custo" in text:
        fields.append("budget_contract")
    if "compliance" in text or "privacy" in text or "privacidade" in text or "repo publico" in text:
        fields.append("privacy_compliance_plan")
    if "security" in text or "seguranca" in text or "authority" in text or "autoridade" in text:
        fields.extend(["security_contract", "security_architecture_plan"])
    if "review" in text or "human gate" in text or "humano" in text or "aprovacao" in text:
        fields.extend(["review", "reviewer_selection_plan"])
    if "runtime adapter" in text or "hermes" in text:
        fields.append("runtime_contract")
    if "control tower" in text or "discord" in text or "owner interface" in text:
        fields.append("project_projection")
    if "production" in text or "release" in text or "monitoring" in text or "incident" in text or "support" in text:
        fields.extend(["production_readiness_plan", "incident_support_plan"])
    if "documentation" in text or "docs" in text or "onboarding" in text:
        fields.append("user_docs_onboarding_plan")
    if "learnback" in text or "learning" in text or "maturity" in text or "auditoria" in text:
        fields.append("factory_maturity_scorecard")
    if "closure summary" in text:
        fields.append("closure_summary")
    if "receipt" in text or "completion audit" in text or "done gate" in text or "evidence" in text:
        fields.extend(["verification_plan", "receipt_five", "completion_audit"])

    if len(fields) == len(CORE_RUNTIME_FIELDS):
        fields.extend(["spec_graph", "loop_plan"])
    return _fields(*fields)


def is_non_empty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def build_rule(record: dict[str, Any]) -> dict[str, Any]:
    checkpoint_id = str(record.get("checkpoint_id") or "")
    return {
        "rule_id": f"canonical-runtime::{checkpoint_id}",
        "checkpoint_id": checkpoint_id,
        "sequence": record.get("sequence"),
        "canonical_line": record.get("canonical_line"),
        "canonical_heading": record.get("canonical_heading"),
        "linear_status": record.get("implementation_status"),
        "enforcement_points": [
            "scripts/canonical_runtime_enforcement.py",
            "scripts/factoryctl.py validate-card",
            "adapters/hermes/transition_hook.py",
        ],
        "required_fields": list(infer_required_fields(record)),
        "block_policy": "missing_required_fields_blocks_vfinal_runtime_gate",
    }


def build_rulebook(trace: dict[str, Any]) -> dict[str, Any]:
    rules: list[dict[str, Any]] = []
    non_runtime: list[dict[str, Any]] = []
    unmapped: list[dict[str, Any]] = []
    for record in trace.get("checkpoints", []):
        if not isinstance(record, dict):
            continue
        if record.get("implementation_status") in NON_RUNTIME_LINEAR_STATUSES:
            non_runtime.append(
                {
                    "checkpoint_id": record.get("checkpoint_id"),
                    "sequence": record.get("sequence"),
                    "canonical_line": record.get("canonical_line"),
                    "canonical_heading": record.get("canonical_heading"),
                    "reason": "Canonical framing or vocabulary; not an executable factory process.",
                }
            )
            continue
        rule = build_rule(record)
        if not rule["required_fields"]:
            unmapped.append(record)
        else:
            rules.append(rule)

    return {
        "$schema": SCHEMA,
        "record_type": "canonical_runtime_rulebook",
        "source_trace_ref": ".tmp/factory-runs/canonical-linear-traceability/canonical-linear-traceability.json",
        "summary": {
            "checkpoints_checked": len(trace.get("checkpoints", [])),
            "runtime_rules": len(rules),
            "non_runtime_processes": len(non_runtime),
            "unmapped_actionable_checkpoints": len(unmapped),
        },
        "rules": rules,
        "non_runtime_processes": non_runtime,
        "unmapped_actionable_checkpoints": [
            {
                "checkpoint_id": record.get("checkpoint_id"),
                "sequence": record.get("sequence"),
                "canonical_heading": record.get("canonical_heading"),
            }
            for record in unmapped
        ],
    }


def fallback_rulebook() -> dict[str, Any]:
    return {
        "$schema": SCHEMA,
        "record_type": "canonical_runtime_rulebook",
        "source_trace_ref": FALLBACK_SOURCE_TRACE_REF,
        "summary": {
            "checkpoints_checked": 1,
            "runtime_rules": 1,
            "non_runtime_processes": 0,
            "unmapped_actionable_checkpoints": 0,
        },
        "rules": [
            {
                "rule_id": "canonical-runtime::vfinal-core-contract",
                "checkpoint_id": "vfinal-core-contract",
                "sequence": 1,
                "canonical_line": None,
                "canonical_heading": "vFinal core runtime contract",
                "linear_status": "implemented_by_runtime",
                "enforcement_points": [
                    "scripts/canonical_runtime_enforcement.py",
                    "scripts/factoryctl.py validate-card",
                    "adapters/hermes/transition_hook.py",
                ],
                "required_fields": list(VFINAL_FALLBACK_FIELDS),
                "block_policy": "missing_required_fields_blocks_vfinal_runtime_gate",
            }
        ],
        "non_runtime_processes": [],
        "unmapped_actionable_checkpoints": [],
    }


def default_rulebook(trace_path: Path | None = None) -> dict[str, Any]:
    if trace_path is None:
        return fallback_rulebook()
    if not trace_path.exists():
        raise FileNotFoundError(f"canonical trace does not exist: {trace_path}")
    return build_rulebook(load_json(trace_path))


def validate_card_runtime_rules(card: dict[str, Any], rulebook: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    if card.get("factory_method_version") != "OVERKILL_VFINAL":
        return []
    active_rulebook = rulebook or default_rulebook()
    blockers: list[dict[str, Any]] = []
    for rule in active_rulebook.get("rules", []):
        if not isinstance(rule, dict):
            continue
        missing = [field for field in rule.get("required_fields", []) if not is_non_empty(card.get(field))]
        if missing:
            blockers.append(
                {
                    "rule_id": rule.get("rule_id"),
                    "checkpoint_id": rule.get("checkpoint_id"),
                    "canonical_line": rule.get("canonical_line"),
                    "canonical_heading": rule.get("canonical_heading"),
                    "missing_fields": missing,
                    "block_policy": rule.get("block_policy"),
                }
            )
    return blockers


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build or run canonical runtime enforcement.")
    parser.add_argument("--trace", type=Path)
    parser.add_argument("--card", type=Path)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    rulebook = default_rulebook(args.trace)
    if args.card:
        card = load_json(args.card)
        blockers = validate_card_runtime_rules(card, rulebook)
        result = {
            "$schema": SCHEMA,
            "record_type": "canonical_runtime_gate_report",
            "rulebook_summary": rulebook["summary"],
            "result": "PASS" if not blockers else "FAIL",
            "blockers": blockers,
        }
        write_json(args.out, result)
        print(json.dumps({"result": result["result"], "blockers": len(blockers)}, indent=2))
        return 1 if blockers else 0
    write_json(args.out, rulebook)
    print(json.dumps(rulebook["summary"], indent=2))
    return 1 if rulebook["summary"]["unmapped_actionable_checkpoints"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
