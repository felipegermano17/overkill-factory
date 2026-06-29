#!/usr/bin/env python3
"""Audit the V3 release readiness bar for Overkill Factory.

This is the consolidated guard for waves 4-9 of the master plan. It does not
create a runtime. It validates method/gate/process contracts that keep human
gates useful, completion evidence honest, release authority explicit and the
public GitHub surface ready for V3.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-v3-release-readiness.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-v3-release-readiness-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-v3-release-readiness-audit.md"

REQUIRED_TRACKS = {
    "W04-human-gate-package",
    "W05-receipt-five-anti-overclaim",
    "W06-product-method-architecture",
    "W07-capability-security-release-authority",
    "W08-public-github-v3",
    "W09-factory-perfect-run",
}
REQUIRED_COMPLETION_CLASSES = {"contract_pass", "runtime_pass", "product_pass", "release_pass"}
REQUIRED_AUTHORITY = {"R3", "R4", "mainnet", "funds", "secrets", "production", "release"}
REQUIRED_PERFECT_RUN_COMMANDS = {
    "command:factoryctl factory-perfect-run",
    "command:factoryctl master-plan-completion",
    "command:factoryctl literal-dod-audit",
    "command:factoryctl v3-production-activation-check --live-hermes",
}
REQUIRED_HUMAN_FIELDS = {
    "executive_summary",
    "decision_needed",
    "options_and_consequences",
    "approved_scope",
    "forbidden_scope",
    "evidence_refs",
    "next_safe_action",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def _ref_exists(ref: str) -> bool:
    if ref.startswith(("command:", "http://", "https://", "external:")):
        return True
    return (ROOT / ref).exists()


def audit(registry: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    _require(registry.get("record_type") == "factory_v3_release_readiness", errors, "$.record_type must be factory_v3_release_readiness")
    _require(registry.get("release_target") == "V3", errors, "release_target must be V3")

    tracks = _as_list(registry.get("readiness_tracks"))
    track_ids = {str(item.get("id")) for item in tracks if isinstance(item, dict)}
    missing_tracks = sorted(REQUIRED_TRACKS - track_ids)
    _require(not missing_tracks, errors, "readiness_tracks missing: " + ", ".join(missing_tracks))
    missing_refs: list[str] = []
    for track in tracks:
        if not isinstance(track, dict):
            continue
        refs = [str(ref) for ref in _as_list(track.get("evidence_refs"))]
        _require(len(refs) > 0, errors, f"{track.get('id')} must include evidence_refs")
        for ref in refs:
            if not _ref_exists(ref):
                missing_refs.append(f"{track.get('id')}:{ref}")
    _require(not missing_refs, errors, "missing evidence ref(s): " + ", ".join(missing_refs))

    human_gate = registry.get("human_gate_package", {}) if isinstance(registry.get("human_gate_package"), dict) else {}
    _require(human_gate.get("artifact_first") is True, errors, "human gate must be artifact-first")
    _require(human_gate.get("pdf_or_plain_text_fallback_required") is True, errors, "human gate must require PDF or plain-text fallback")
    _require(human_gate.get("delivery_receipt_required") is True, errors, "human gate must require delivery receipt")
    _require(human_gate.get("raw_json_primary_surface_allowed") is False, errors, "raw JSON must not be primary human gate surface")
    _require(human_gate.get("fake_human_gate_allowed") is False, errors, "fake human gate must not be allowed")
    human_fields = set(str(item) for item in _as_list(human_gate.get("required_fields")))
    missing_fields = sorted(REQUIRED_HUMAN_FIELDS - human_fields)
    _require(not missing_fields, errors, "human gate required_fields missing: " + ", ".join(missing_fields))

    receipt = registry.get("receipt_five_policy", {}) if isinstance(registry.get("receipt_five_policy"), dict) else {}
    _require(receipt.get("readback_required") is True, errors, "Receipt Five readback required")
    _require(receipt.get("contract_pass_means_done") is False, errors, "contract_pass must not mean done")
    _require(receipt.get("scaffold_or_template_counts_as_evidence") is False, errors, "scaffold/template must not count as evidence")
    _require(receipt.get("stale_review_counts_as_current_authority") is False, errors, "stale review must not count as current authority")
    classes = set(str(item) for item in _as_list(receipt.get("completion_classes")))
    missing_classes = sorted(REQUIRED_COMPLETION_CLASSES - classes)
    _require(not missing_classes, errors, "completion_classes missing: " + ", ".join(missing_classes))

    product = registry.get("product_truth_policy", {}) if isinstance(registry.get("product_truth_policy"), dict) else {}
    for key in ("owner_approved_product_sot_required", "source_ledger_sot_method_architecture_distinct", "architecture_repair_not_readback_loop", "downstream_requires_product_context_packet"):
        _require(product.get(key) is True, errors, f"product_truth_policy.{key} must be true")
    _require(product.get("planning_review_is_architecture_review") is False, errors, "planning review must not be architecture review")

    authority = registry.get("authority_policy", {}) if isinstance(registry.get("authority_policy"), dict) else {}
    _require(authority.get("solana_ai_kit_required_for_solana") is True, errors, "Solana AI Kit must be required for Solana")
    _require(authority.get("security_architecture_before_material_security_work") is True, errors, "security architecture required before material security work")
    _require(authority.get("release_gate_separate_from_tests") is True, errors, "release gate must be separate from tests")
    _require(authority.get("low_risk_does_not_default_to_human_gate") is True, errors, "low risk must not default to human gate")
    explicit = set(str(item) for item in _as_list(authority.get("explicit_authority_required_for")))
    missing_authority = sorted(REQUIRED_AUTHORITY - explicit)
    _require(not missing_authority, errors, "explicit_authority_required_for missing: " + ", ".join(missing_authority))

    public = registry.get("public_github_policy", {}) if isinstance(registry.get("public_github_policy"), dict) else {}
    _require(public.get("release_label") == "V3", errors, "Public GitHub release label must be V3")
    _require(public.get("open_source_surface_required") is True, errors, "open source public surface required")
    _require(public.get("public_map_must_be_simplified") is True, errors, "public map must be simplified")
    _require(public.get("first_value_path_required") is True, errors, "first-value path required")
    _require(public.get("private_context_allowed") is False, errors, "private context must not be allowed in public GitHub surface")
    _require(public.get("hype_claims_allowed") is False, errors, "hype claims must not replace demonstrated quality")

    perfect = registry.get("factory_perfect_run_policy", {}) if isinstance(registry.get("factory_perfect_run_policy"), dict) else {}
    for key in ("requires_manager_agent_freshness", "requires_runtime_truth_spine", "requires_canonical_frontier", "requires_receipt_five_readback", "requires_public_github_v3_surface", "operator_does_not_interpret_kanban", "no_mini_hermes", "release_blocks_without_factory_perfect_run"):
        _require(perfect.get(key) is True, errors, f"factory_perfect_run_policy.{key} must be true")
    perfect_commands = set(str(item) for item in _as_list(perfect.get("required_commands")))
    missing_perfect_commands = sorted(REQUIRED_PERFECT_RUN_COMMANDS - perfect_commands)
    _require(not missing_perfect_commands, errors, "factory_perfect_run_policy.required_commands missing: " + ", ".join(missing_perfect_commands))

    acceptance = registry.get("acceptance", {}) if isinstance(registry.get("acceptance"), dict) else {}
    for key in ("waves_4_to_9_covered", "v3_release_required", "human_gates_artifact_first", "overclaim_blocked", "public_github_product_surface_required", "factory_perfect_run_required"):
        _require(acceptance.get(key) is True, errors, f"$.acceptance.{key} must be true")

    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_v3_release_readiness_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "release_target": registry.get("release_target"),
        "summary": {
            "errors": len(errors),
            "readiness_track_count": len(tracks),
            "evidence_ref_count": sum(len(_as_list(t.get("evidence_refs"))) for t in tracks if isinstance(t, dict)),
            "completion_class_count": len(classes),
        },
        "track_ids": sorted(track_ids),
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory V3 Release Readiness Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append(f"Release target: {report['release_target']}")
    lines.append("")
    lines.append("## Readiness tracks")
    lines.append("")
    for track in registry.get("readiness_tracks", []):
        lines.append(f"- {track['id']} — {track['name']}")
    lines.append("")
    lines.append("## Public GitHub V3")
    lines.append("")
    lines.append("The public repository must be simple, professional, open-source ready and first-value oriented. The release label is V3.")
    lines.append("")
    lines.append("## Factory Perfect Run")
    lines.append("")
    lines.append("The final proof depends on gerente freshness, runtime truth spine, canonical frontier, Receipt Five readback and public GitHub V3 readiness.")
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
