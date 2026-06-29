#!/usr/bin/env python3
"""Executable audit for Overkill Factory executor and skill ecosystem.

World-class methods do not matter if the factory lacks good executors, skills,
provider acquisition, readiness, and promotion/demotion policy. This audit
checks that the modular adaptive executor/skill layer exposes gaps instead of
hiding them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "templates" / "factory-executor-skill-ecosystem-registry.json"
DEFAULT_WORKER_REGISTRY_PATH = ROOT / "agents" / "worker-registry.public.json"
DEFAULT_SKILL_PROVIDER_REGISTRY_PATH = ROOT / "agents" / "skill-provider-registry.public.json"
PRIVATE_REF_RE = re.compile(r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|/var/|file://)", re.I)
NOT_READY = {"partial", "missing", "stale", "needs_upgrade", "duplicate_or_ambiguous"}
REQUIRED_DEMAND_KEYS = {
    "prd_grade_requirements",
    "system_design_review",
    "product_analytics",
    "go_to_market_distribution",
    "ai_eval_model_risk",
    "capability_acquisition_system",
    "solana_domain_execution",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def list_field(data: dict[str, Any], key: str) -> list[Any]:
    value = data.get(key)
    return value if isinstance(value, list) else []


def dict_field(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def worker_ids(worker_registry: dict[str, Any]) -> set[str]:
    return {
        str(worker.get("worker_id"))
        for worker in list_field(worker_registry, "workers")
        if isinstance(worker, dict) and str(worker.get("worker_id") or "").strip()
    }


def provider_ids(skill_provider_registry: dict[str, Any]) -> set[str]:
    return {
        str(provider.get("provider_id"))
        for provider in list_field(skill_provider_registry, "providers")
        if isinstance(provider, dict) and str(provider.get("provider_id") or "").strip()
    }


def private_ref_errors(value: Any, at: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if PRIVATE_REF_RE.search(value):
            errors.append(f"{at}: private/local refs are forbidden in public executor/skill registry")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(private_ref_errors(item, f"{at}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(private_ref_errors(item, f"{at}.{key}"))
    return errors


def validate_executor_skill_registry(
    registry: dict[str, Any],
    worker_registry: dict[str, Any],
    skill_provider_registry: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    if registry.get("record_type") != "factory_executor_skill_ecosystem_registry":
        errors.append("$.record_type must be factory_executor_skill_ecosystem_registry")

    acquisition = dict_field(registry, "adaptive_capability_acquisition")
    for key in (
        "enabled",
        "trusted_provider_search_required",
        "agent_and_skill_symmetry_required",
        "candidate_eval_required",
        "promotion_requires_smoke_and_eval",
        "demotion_required_on_repeated_failure",
        "modular_adaptive_demand_routing_preserved",
    ):
        if acquisition.get(key) is not True:
            errors.append(f"$.adaptive_capability_acquisition.{key} must be true")

    executor_policy = dict_field(registry, "executor_policy")
    for key in ("agents_from_operational_contracts_not_vibes", "reviewer_executor_separation", "fresh_readiness_required", "least_privilege_tools"):
        if executor_policy.get(key) is not True:
            errors.append(f"$.executor_policy.{key} must be true")

    skill_policy = dict_field(registry, "skill_policy")
    for key in ("skills_are_capability_not_authority", "trusted_reference_repos_only", "eval_before_promotion", "skill_ref_resolution_required"):
        if skill_policy.get(key) is not True:
            errors.append(f"$.skill_policy.{key} must be true")

    known_workers = worker_ids(worker_registry)
    known_providers = provider_ids(skill_provider_registry)
    demands = [item for item in list_field(registry, "demand_coverage") if isinstance(item, dict)]
    by_key = {str(item.get("demand_key")): item for item in demands}
    missing_demands = sorted(REQUIRED_DEMAND_KEYS - set(by_key))
    if missing_demands:
        errors.append("missing required demand coverage keys: " + ", ".join(missing_demands))

    missing_or_partial_executors = 0
    missing_or_partial_skills = 0
    acquisition_entries = 0
    for index, demand in enumerate(demands):
        prefix = f"$.demand_coverage[{index}:{demand.get('demand_key')}]"
        executor_status = str(demand.get("executor_coverage_status") or "")
        skill_status = str(demand.get("skill_coverage_status") or "")
        if executor_status in NOT_READY:
            missing_or_partial_executors += 1
        if skill_status in NOT_READY:
            missing_or_partial_skills += 1
        if demand.get("factory_shape") == "capability_acquisition_lane":
            acquisition_entries += 1
        if not list_field(demand, "evidence_or_eval_required"):
            errors.append(f"{prefix}.evidence_or_eval_required must be non-empty")
        for worker_ref in list_field(demand, "current_worker_refs"):
            if worker_ref not in known_workers:
                errors.append(f"{prefix}.current_worker_refs unknown worker ref: {worker_ref}")
        for provider_ref in list_field(demand, "current_skill_provider_refs"):
            if provider_ref not in known_providers:
                errors.append(f"{prefix}.current_skill_provider_refs unknown skill/provider ref: {provider_ref}")
        if executor_status == "ready" and not list_field(demand, "current_worker_refs"):
            errors.append(f"{prefix} cannot claim executor ready with no worker refs")
        if skill_status == "ready" and not list_field(demand, "current_skill_provider_refs"):
            errors.append(f"{prefix} cannot claim skill ready with no provider refs")

    if missing_or_partial_executors < 5:
        errors.append("registry must expose missing or partial executor coverage instead of claiming the worker set is already sufficient")
    if missing_or_partial_skills < 5:
        errors.append("registry must expose missing or partial skill/provider coverage instead of claiming the skill set is already sufficient")
    if acquisition_entries < 2:
        errors.append("registry must include capability acquisition lane entries for modular adaptive gaps")

    solana_entry = by_key.get("solana_domain_execution")
    if not solana_entry:
        errors.append("registry must include solana_domain_execution coverage")
    else:
        solana_providers = set(list_field(solana_entry, "current_skill_provider_refs"))
        if "solana-ai-kit" not in solana_providers:
            errors.append("solana_domain_execution must require solana-ai-kit as mandatory provider")
        recommendation = str(solana_entry.get("recommendation") or "").lower()
        capability_text = " ".join([
            str(solana_entry.get("needed_executor_capability") or ""),
            str(solana_entry.get("needed_skill_capability") or ""),
            recommendation,
        ]).lower()
        if "mandatory" not in capability_text or "domain brain" not in capability_text:
            errors.append("solana_domain_execution must say Solana AI Kit is the mandatory domain brain")
        if "external non-solana-ai-kit" not in recommendation and "non-solana-ai-kit" not in recommendation:
            errors.append("solana_domain_execution must reject external non-Solana-AI-Kit execution routes")

    non_goals = [str(item).lower() for item in list_field(registry, "non_goals")]
    if not any("vibes" in item for item in non_goals):
        errors.append("$.non_goals must reject agents from vibes")
    if not any("modular adaptive" in item for item in non_goals):
        errors.append("$.non_goals must preserve modular adaptive routing")

    errors.extend(private_ref_errors(registry))
    return errors


def build_executor_skill_ecosystem_audit(
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    worker_registry_path: Path = DEFAULT_WORKER_REGISTRY_PATH,
    skill_provider_registry_path: Path = DEFAULT_SKILL_PROVIDER_REGISTRY_PATH,
) -> dict[str, Any]:
    registry = load_json(registry_path)
    worker_registry = load_json(worker_registry_path)
    skill_provider_registry = load_json(skill_provider_registry_path)
    errors = validate_executor_skill_registry(registry, worker_registry, skill_provider_registry)
    demands = [item for item in list_field(registry, "demand_coverage") if isinstance(item, dict)]
    missing_or_partial_executors = [item for item in demands if item.get("executor_coverage_status") in NOT_READY]
    missing_or_partial_skills = [item for item in demands if item.get("skill_coverage_status") in NOT_READY]
    result = "PASS" if not errors else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-executor-skill-ecosystem-audit.schema.json",
        "record_type": "factory_executor_skill_ecosystem_audit",
        "audit_id": "factory-executor-skill-ecosystem-audit-v1",
        "result": result,
        "score": max(0, 100 - len(errors) * 10),
        "thesis": "World-class methods require world-class executors, skills, readiness and modular adaptive capability acquisition.",
        "registry_ref": str(registry_path.relative_to(ROOT) if registry_path.is_relative_to(ROOT) else registry_path),
        "worker_registry_ref": str(worker_registry_path.relative_to(ROOT) if worker_registry_path.is_relative_to(ROOT) else worker_registry_path),
        "skill_provider_registry_ref": str(skill_provider_registry_path.relative_to(ROOT) if skill_provider_registry_path.is_relative_to(ROOT) else skill_provider_registry_path),
        "adaptive_capability_acquisition": dict_field(registry, "adaptive_capability_acquisition"),
        "demand_coverage": demands,
        "summary": {
            "demand_count": len(demands),
            "known_worker_count": len(worker_ids(worker_registry)),
            "known_skill_provider_count": len(provider_ids(skill_provider_registry)),
            "missing_or_partial_executor_count": len(missing_or_partial_executors),
            "missing_or_partial_skill_count": len(missing_or_partial_skills),
            "capability_acquisition_lane_count": sum(1 for item in demands if item.get("factory_shape") == "capability_acquisition_lane"),
            "errors": len(errors),
        },
        "executor_gap_keys": [str(item.get("demand_key")) for item in missing_or_partial_executors],
        "skill_gap_keys": [str(item.get("demand_key")) for item in missing_or_partial_skills],
        "errors": errors,
    }


def audit_to_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Executor and Skill Ecosystem Audit",
        "",
        f"Result: {audit['result']}",
        f"Score: {audit['score']}",
        "",
        "This audit preserves the factory as a modular adaptive system: when a demand lacks a good executor or skill, the factory must use trusted provider search, candidate evals, and promotion/demotion rules.",
        "",
        "## Demand Coverage",
        "",
    ]
    for item in audit["demand_coverage"]:
        lines.append(f"- {item['display_name']} (`{item['demand_key']}`)")
        lines.append(f"  - executors: {item['executor_coverage_status']} via {', '.join(item['current_worker_refs']) or 'none'}")
        lines.append(f"  - skills/providers: {item['skill_coverage_status']} via {', '.join(item['current_skill_provider_refs']) or 'none'}")
        lines.append(f"  - recommendation: {item['recommendation']}")
    lines.extend(["", "## Capability Acquisition", "", "- trusted provider search: required", "- candidate eval: required", "- promotion/demotion: required"])
    if audit["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in audit["errors"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Factory executor and skill ecosystem audit")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--worker-registry", type=Path, default=DEFAULT_WORKER_REGISTRY_PATH)
    parser.add_argument("--skill-provider-registry", type=Path, default=DEFAULT_SKILL_PROVIDER_REGISTRY_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)

    audit = build_executor_skill_ecosystem_audit(args.registry, args.worker_registry, args.skill_provider_registry)
    if args.out:
        write_json(args.out, audit)
        print(f"Wrote {args.out}")
    else:
        print(json.dumps(audit, indent=2, sort_keys=True))
    if args.markdown:
        args.markdown.parent.mkdir(parents=True, exist_ok=True)
        args.markdown.write_text(audit_to_markdown(audit), encoding="utf-8")
        print(f"Wrote {args.markdown}")
    if audit["errors"]:
        for error in audit["errors"]:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
