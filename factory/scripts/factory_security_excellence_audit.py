#!/usr/bin/env python3
"""Executable audit for Overkill Factory security excellence.

Security is treated as product culture and architecture, not as a late checklist.
The audit intentionally avoids false "perfect security" claims and requires
best-possible security with evidence, gates and residual-risk ownership.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "templates" / "factory-security-excellence-registry.json"
PRIVATE_REF_RE = re.compile(r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|/var/|file://)", re.I)
NOT_STRONG = {"partial", "missing", "needs_upgrade"}
REQUIRED_PILLARS = {
    "secure_by_design_culture",
    "security_architecture_first",
    "threat_modeling_abuse_cases",
    "trust_boundaries_data_flow",
    "identity_authorization_access",
    "secrets_keys_signing",
    "data_privacy_governance",
    "secure_coding_app_api",
    "supply_chain_build_integrity",
    "cloud_infra_network_hardening",
    "ai_agentic_security",
    "solana_onchain_security",
    "testing_fuzzing_negative_security",
    "observability_detection_incident",
    "release_residual_risk_acceptance",
    "vulnerability_management_learnback",
    "public_private_evidence_safety",
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


def private_ref_errors(value: Any, at: str = "$") -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if PRIVATE_REF_RE.search(value):
            errors.append(f"{at}: private/local refs are forbidden in public security registry")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(private_ref_errors(item, f"{at}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(private_ref_errors(item, f"{at}.{key}"))
    return errors


def validate_security_registry(registry: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if registry.get("record_type") != "factory_security_excellence_registry":
        errors.append("$.record_type must be factory_security_excellence_registry")

    policy = dict_field(registry, "security_culture_policy")
    for key in (
        "security_is_culture_not_checklist",
        "security_before_implementation",
        "architecture_first_for_greenfield",
        "applies_to_all_change_types",
        "fail_closed_on_missing_security_evidence",
        "forbid_unqualified_perfection_claims",
        "residual_risk_record_required",
    ):
        if policy.get(key) is not True:
            errors.append(f"$.security_culture_policy.{key} must be true")

    allowed_claim = str(policy.get("allowed_security_claim_language") or "").lower()
    if "perfect" in allowed_claim or "perfection" in allowed_claim:
        errors.append("security registry must not make an unqualified perfection claim")
    if "best possible" not in allowed_claim or "evidence" not in allowed_claim:
        errors.append("allowed security claim language must be best possible with evidence")

    for section, keys in {
        "greenfield_security_policy": (
            "secure_architecture_before_build",
            "threat_model_before_build",
            "trust_boundaries_before_build",
            "privacy_before_data",
            "secrets_before_integration",
            "observability_before_release",
        ),
        "change_security_policy": (
            "bug_fixes_can_trigger_security_review",
            "refactors_can_trigger_security_review",
            "dependency_changes_trigger_supply_chain_review",
            "ai_or_agent_changes_trigger_ai_security_review",
            "solana_changes_trigger_solana_ai_kit",
        ),
    }.items():
        section_data = dict_field(registry, section)
        for key in keys:
            if section_data.get(key) is not True:
                errors.append(f"$.{section}.{key} must be true")

    pillars = [item for item in list_field(registry, "pillar_coverage") if isinstance(item, dict)]
    by_key = {str(item.get("pillar_key")): item for item in pillars}
    missing = sorted(REQUIRED_PILLARS - set(by_key))
    if missing:
        errors.append("missing required security pillars: " + ", ".join(missing))

    partial_or_missing = 0
    architecture_first_found = False
    for index, pillar in enumerate(pillars):
        prefix = f"$.pillar_coverage[{index}:{pillar.get('pillar_key')}]"
        status = str(pillar.get("coverage_status") or "")
        if status in NOT_STRONG:
            partial_or_missing += 1
        if not list_field(pillar, "required_artifacts"):
            errors.append(f"{prefix}.required_artifacts must be non-empty")
        if not list_field(pillar, "required_evidence"):
            errors.append(f"{prefix}.required_evidence must be non-empty")
        joined = " ".join(str(v) for v in (
            pillar.get("display_name"),
            pillar.get("security_goal"),
            pillar.get("gap_or_upgrade"),
            pillar.get("shape"),
        )).lower()
        if "architecture" in joined or pillar.get("shape") == "architecture_gate":
            architecture_first_found = True

    if partial_or_missing < 6:
        errors.append("registry must honestly expose partial/missing security coverage; do not claim everything is already strong")
    if not architecture_first_found:
        errors.append("registry must include architecture-first security coverage")

    solana = by_key.get("solana_onchain_security")
    if solana:
        solana_controls = " ".join(str(item) for item in list_field(solana, "existing_controls"))
        solana_artifacts = " ".join(str(item) for item in list_field(solana, "required_artifacts"))
        solana_text = json.dumps(solana, sort_keys=True)
        if ("Solana AI Kit" not in solana_controls and "solana-ai-kit" not in solana_controls and "Solana AI Kit" not in solana_artifacts and "solana-ai-kit" not in solana_artifacts):
            errors.append("solana_onchain_security must require Solana AI Kit")
        if "Auditor" not in solana_text:
            errors.append("solana_onchain_security must require Auditor evidence")
        if "signer" not in solana_text.lower():
            errors.append("solana_onchain_security must require signer boundary")
    else:
        errors.append("solana_onchain_security pillar is required")

    ai = by_key.get("ai_agentic_security")
    if ai:
        ai_text = json.dumps(ai, sort_keys=True).lower()
        for term in ("prompt injection", "tool", "memory", "eval"):
            if term not in ai_text:
                errors.append(f"ai_agentic_security must cover {term}")

    non_goals = " ".join(str(item).lower() for item in list_field(registry, "non_goals"))
    if "perfect security" not in non_goals:
        errors.append("$.non_goals must reject perfect security claims")
    if "late checklist" not in non_goals:
        errors.append("$.non_goals must reject late-checklist security")

    errors.extend(private_ref_errors(registry))
    return errors


def build_security_excellence_audit(registry_path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    registry = load_json(registry_path)
    errors = validate_security_registry(registry)
    pillars = [item for item in list_field(registry, "pillar_coverage") if isinstance(item, dict)]
    partial_or_missing = [item for item in pillars if item.get("coverage_status") in NOT_STRONG]
    strong = [item for item in pillars if item.get("coverage_status") == "strong"]
    result = "PASS" if not errors else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/factory-security-excellence-audit.schema.json",
        "record_type": "factory_security_excellence_audit",
        "audit_id": "factory-security-excellence-audit-v1",
        "result": result,
        "score": max(0, 100 - len(errors) * 10),
        "thesis": "Security is culture and architecture-first product design: best possible with evidence, gates and explicit residual-risk ownership.",
        "registry_ref": str(registry_path.relative_to(ROOT) if registry_path.is_relative_to(ROOT) else registry_path),
        "security_culture_policy": dict_field(registry, "security_culture_policy"),
        "pillar_coverage": pillars,
        "summary": {
            "pillar_count": len(pillars),
            "strong_count": len(strong),
            "partial_or_missing_count": len(partial_or_missing),
            "errors": len(errors),
        },
        "partial_or_missing_pillars": [str(item.get("pillar_key")) for item in partial_or_missing],
        "errors": errors,
    }


def audit_to_markdown(audit: dict[str, Any]) -> str:
    lines = [
        "# Factory Security Excellence Audit",
        "",
        f"Result: {audit['result']}",
        f"Score: {audit['score']}",
        "",
        "Security posture: security is culture, architecture-first, and best possible with evidence, gates and residual-risk records. The factory must not claim perfect security.",
        "",
        "## Pillar Coverage",
        "",
    ]
    for item in audit["pillar_coverage"]:
        lines.append(f"- {item['display_name']} (`{item['pillar_key']}`): {item['coverage_status']}")
        lines.append(f"  - goal: {item['security_goal']}")
        lines.append(f"  - gap/upgrade: {item['gap_or_upgrade']}")
    if audit["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {error}" for error in audit["errors"])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Factory security excellence audit")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--markdown", type=Path)
    args = parser.parse_args(argv)

    audit = build_security_excellence_audit(args.registry)
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
