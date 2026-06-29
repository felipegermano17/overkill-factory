#!/usr/bin/env python3
"""Executable Factory Method Excellence audit.

Hermes owns the factory floor. This audit validates the Overkill Factory method
layer: method families, contracts, gates, proof requirements, anti-mediocrity
rules and learnback hooks.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "templates" / "factory-method-excellence-registry.json"
DEFAULT_METHOD_ENGINE_REGISTRY_PATH = ROOT / "templates" / "method-engine-registry.json"

REQUIRED_METHOD_FAMILY_IDS = {
    "product_strategy_direction",
    "discovery_research",
    "product_definition_requirements",
    "ux_product_experience_design_systems",
    "architecture_systems_design",
    "engineering_execution_quality",
    "security_privacy_safety",
    "reliability_operations_release",
    "data_ai_evaluation",
    "product_quality_excellence",
    "domain_specific_method_packs",
}

REQUIRED_LEGACY_ENGINE_IDS = {
    "spec_first_sdd",
    "test_first_tdd",
    "behavior_first_bdd",
    "discovery_research",
    "security_first_threat_model",
    "design_first_product_experience",
    "legacy_diagnosis",
    "incident_first",
}

PRIVATE_REF_RE = re.compile(r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|/var/)", re.I)
REQUIRED_LIST_FIELDS = (
    "reference_methods",
    "route_triggers",
    "surface_triggers",
    "required_artifacts",
    "required_gates",
    "required_workers",
    "proof_requirements",
    "forbidden_shortcuts",
    "learnback_hooks",
)


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def list_items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def private_ref_errors(value: Any, at: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if PRIVATE_REF_RE.search(value):
            errors.append(f"{at}: private/local refs are forbidden in method excellence registry")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(private_ref_errors(item, f"{at}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(private_ref_errors(item, f"{at}.{key}"))
    return errors


def method_families(registry: dict[str, Any]) -> list[dict[str, Any]]:
    families = registry.get("method_families")
    return families if isinstance(families, list) else []


def method_family_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(family.get("family_id")): family
        for family in method_families(registry)
        if isinstance(family, dict) and str(family.get("family_id") or "").strip()
    }


def dict_field(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    return cast(dict[str, Any], value) if isinstance(value, dict) else {}


def existing_engine_ids(path: Path = DEFAULT_METHOD_ENGINE_REGISTRY_PATH) -> set[str]:
    if not path.exists():
        return set(REQUIRED_LEGACY_ENGINE_IDS)
    data = load_json(path)
    engines = data.get("engines") if isinstance(data.get("engines"), list) else []
    return {
        str(engine.get("engine_id"))
        for engine in engines
        if isinstance(engine, dict) and str(engine.get("engine_id") or "").strip()
    }


def covered_legacy_engine_ids(registry: dict[str, Any]) -> set[str]:
    covered: set[str] = set()
    for family in method_families(registry):
        for engine_id in list_items(family.get("legacy_method_engine_ids")):
            covered.add(str(engine_id))
    return covered


def validate_registry(registry: dict[str, Any], method_engine_registry_path: Path = DEFAULT_METHOD_ENGINE_REGISTRY_PATH) -> list[str]:
    errors: list[str] = []
    if registry.get("record_type") != "factory_method_excellence_registry":
        errors.append("$.record_type must be factory_method_excellence_registry")

    runtime_boundary = dict_field(registry, "runtime_boundary")
    if runtime_boundary.get("hermes_owns_runtime_floor") is not True:
        errors.append("$.runtime_boundary.hermes_owns_runtime_floor must be true")
    if runtime_boundary.get("overkill_owns_method_contracts_and_gates") is not True:
        errors.append("$.runtime_boundary.overkill_owns_method_contracts_and_gates must be true")
    if runtime_boundary.get("no_mini_hermes_runtime") is not True:
        errors.append("$.runtime_boundary.no_mini_hermes_runtime must be true")
    if runtime_boundary.get("use_hermes_native_kanban_typed_blocks_dependencies_dispatch_first") is not True:
        errors.append("$.runtime_boundary.use_hermes_native_kanban_typed_blocks_dependencies_dispatch_first must be true")

    coverage = dict_field(registry, "coverage_policy")
    for key in (
        "method_label_cannot_authorize_execution",
        "operator_does_not_choose_internal_method_by_taste",
        "all_method_families_require_artifacts_gates_workers_proof_and_forbidden_shortcuts",
        "anti_mediocrity_quality_floor_required",
        "learnback_required_for_method_failures",
    ):
        if coverage.get(key) is not True:
            errors.append(f"$.coverage_policy.{key} must be true")

    boundary = dict_field(registry, "public_private_boundary")
    if boundary.get("public_safe_refs_only") is not True:
        errors.append("$.public_private_boundary.public_safe_refs_only must be true")
    if boundary.get("raw_private_evidence_embedded") is not False:
        errors.append("$.public_private_boundary.raw_private_evidence_embedded must be false")

    family_by_id = method_family_map(registry)
    missing_families = sorted(REQUIRED_METHOD_FAMILY_IDS - set(family_by_id))
    if missing_families:
        errors.append("$.method_families missing required families: " + ", ".join(missing_families))

    for family_id, family in family_by_id.items():
        at = f"$.method_families[{family_id}]"
        for field in REQUIRED_LIST_FIELDS:
            values = list_items(family.get(field))
            if not values:
                errors.append(f"{at}.{field} must be non-empty")
        if len(list_items(family.get("reference_methods"))) < 3:
            errors.append(f"{at}.reference_methods must include at least three serious reference methods")
        if len(list_items(family.get("proof_requirements"))) < 3:
            errors.append(f"{at}.proof_requirements must include product-specific evidence requirements")
        if len(list_items(family.get("forbidden_shortcuts"))) < 2:
            errors.append(f"{at}.forbidden_shortcuts must reject shallow method application")
        if len(list_items(family.get("learnback_hooks"))) < 1:
            errors.append(f"{at}.learnback_hooks must keep method failures improving the factory")

    expected_engine_ids = existing_engine_ids(method_engine_registry_path) | REQUIRED_LEGACY_ENGINE_IDS
    missing_engine_coverage = sorted(expected_engine_ids - covered_legacy_engine_ids(registry))
    if missing_engine_coverage:
        errors.append("$.method_families legacy method engine coverage missing: " + ", ".join(missing_engine_coverage))

    errors.extend(private_ref_errors(registry))
    return errors


def build_method_excellence_audit(
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    method_engine_registry_path: Path = DEFAULT_METHOD_ENGINE_REGISTRY_PATH,
) -> dict[str, Any]:
    registry = load_json(registry_path)
    errors = validate_registry(registry, method_engine_registry_path=method_engine_registry_path)
    families = method_families(registry)
    family_summaries = []
    for family in families:
        family_summaries.append(
            {
                "family_id": family.get("family_id"),
                "display_name": family.get("display_name"),
                "reference_method_count": len(list_items(family.get("reference_methods"))),
                "artifact_count": len(list_items(family.get("required_artifacts"))),
                "gate_count": len(list_items(family.get("required_gates"))),
                "worker_count": len(list_items(family.get("required_workers"))),
                "proof_count": len(list_items(family.get("proof_requirements"))),
                "forbidden_shortcut_count": len(list_items(family.get("forbidden_shortcuts"))),
                "learnback_count": len(list_items(family.get("learnback_hooks"))),
                "legacy_method_engine_ids": list_items(family.get("legacy_method_engine_ids")),
            }
        )

    total_required_checks = len(REQUIRED_METHOD_FAMILY_IDS) + len(REQUIRED_LEGACY_ENGINE_IDS) + 5 + 4
    score = max(0, round(100 - (len(errors) * 100 / max(total_required_checks, 1))))
    result = "PASS" if not errors else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-method-excellence-audit.schema.json",
        "record_type": "factory_method_excellence_audit",
        "audit_id": "factory-method-excellence-audit-v1",
        "result": result,
        "score": score,
        "registry_ref": str(registry_path.relative_to(ROOT) if registry_path.is_relative_to(ROOT) else registry_path),
        "runtime_boundary": "Hermes owns runtime floor: Kanban, typed blocks, dependencies, dispatch, runs and worker execution.",
        "method_boundary": "Overkill Factory owns reference-quality product methodology, contracts, gates and evidence requirements.",
        "operator_thesis": "The factory method layer must be world-class; otherwise the factory automates mediocrity.",
        "method_label_policy": "method labels cannot authorize execution; artifacts, gates, workers and proof are required",
        "covered_method_engine_ids": sorted(covered_legacy_engine_ids(registry)),
        "required_method_engine_ids": sorted(existing_engine_ids(method_engine_registry_path) | REQUIRED_LEGACY_ENGINE_IDS),
        "method_families": family_summaries,
        "summary": {
            "required_family_count": len(REQUIRED_METHOD_FAMILY_IDS),
            "actual_family_count": len(families),
            "errors": len(errors),
            "anti_mediocrity_quality_floor": registry.get("coverage_policy", {}).get("anti_mediocrity_quality_floor_required") is True,
            "no_mini_hermes_runtime": registry.get("runtime_boundary", {}).get("no_mini_hermes_runtime") is True,
        },
        "errors": errors,
    }


def audit_to_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Factory Method Excellence Audit",
        "",
        f"Result: {audit['result']}",
        f"Score: {audit['score']}",
        "",
        "This audit exists because Overkill Factory is the method layer and Hermes is the runtime floor.",
        "It must preserve reference-quality product methodology and remain not a mini-Hermes.",
        "The factory cannot be allowed to automate mediocrity.",
        "",
        "Core policy: method labels cannot authorize execution; artifacts, gates, workers and proof are required.",
        "",
        "## Method Families",
        "",
    ]
    for family in audit["method_families"]:
        lines.extend(
            [
                f"- {family['family_id']}: {family.get('display_name')}",
                f"  - references: {family['reference_method_count']}",
                f"  - artifacts/gates/workers/proof: {family['artifact_count']}/{family['gate_count']}/{family['worker_count']}/{family['proof_count']}",
                f"  - forbidden shortcuts: {family['forbidden_shortcut_count']}",
                f"  - learnback hooks: {family['learnback_count']}",
            ]
        )
    if audit["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in audit["errors"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Factory Method Excellence audit")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--method-engine-registry", type=Path, default=DEFAULT_METHOD_ENGINE_REGISTRY_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)

    audit = build_method_excellence_audit(args.registry, args.method_engine_registry)
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
