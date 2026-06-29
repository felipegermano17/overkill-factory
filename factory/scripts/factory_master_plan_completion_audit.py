#!/usr/bin/env python3
"""Audit 100% implementation of the private master plan waves.

This guard is intentionally stricter than the earlier V3 readiness audit. It is
not allowed to pass only because contracts or docs exist. Every wave must name
operational code, tests, command path, runtime/e2e evidence, agent/operator
activation evidence and durable proof refs.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

ROOT = Path(os.environ.get("OVERKILL_FACTORY_ASSET_ROOT") or Path(__file__).resolve().parents[1])
REPO_ROOT = ROOT.parent if (ROOT.parent / ".github").exists() else ROOT
DEFAULT_RECORD = ROOT / "templates" / "factory-master-plan-completion.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-master-plan-completion-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-master-plan-completion-audit.md"
REQUIRED_WAVES = set(range(10))
REQUIRED_CATEGORIES = {
    "code_refs",
    "test_refs",
    "command_refs",
    "runtime_refs",
    "agent_refs",
    "operator_refs",
    "evidence_refs",
}
FORBIDDEN_FAKE_DONE = {
    "contract_only",
    "docs_only",
    "audit_only",
    "chat_summary",
    "manual_claim",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _path_exists(root: Path, ref: str) -> bool:
    if ref.startswith(("command:", "github:", "release:", "issue:", "tag:", "external:")):
        return True
    candidates = [REPO_ROOT / ref, root / ref] if REPO_ROOT != root else [root / ref]
    repo_root = REPO_ROOT.resolve()
    for path in candidates:
        resolved = path.resolve()
        if not resolved.is_relative_to(repo_root):
            return False
        if path.exists():
            return True
    return False


def _audit_agent_activation(root: Path, errors: list[str]) -> None:
    expected_version = "v3.0.0-master-plan-100"
    profile_path = root / "agents" / "worker-profiles.public.json"
    binding_path = root / "agents" / "hermes-profile-bindings.public.json"
    registry_path = root / "agents" / "worker-registry.public.json"
    for path in (profile_path, binding_path, registry_path):
        if not path.exists():
            errors.append(f"missing agent activation artifact: {path.relative_to(root)}")
            return
    profiles = load_json(profile_path)
    bindings = load_json(binding_path)
    registry = load_json(registry_path)
    if profiles.get("production_activation_version") != expected_version:
        errors.append("worker profiles missing v3 production activation version")
    if bindings.get("production_activation_version") != expected_version:
        errors.append("Hermes bindings missing v3 production activation version")
    if registry.get("production_activation_version") != expected_version:
        errors.append("worker registry missing v3 production activation version")
    for worker_id, profile in profiles.get("profiles", {}).items():
        activation = profile.get("v3_master_plan_activation") or {}
        if activation.get("manager_only_operator_contact") is not True:
            errors.append(f"{worker_id} profile does not enforce manager-only operator contact")
        if activation.get("uses_factory_code_not_prompt_runtime") is not True:
            errors.append(f"{worker_id} profile does not enforce factory-code use")
        if "factory_perfect_run" not in activation.get("required_checks", []):
            errors.append(f"{worker_id} profile missing factory_perfect_run check")
        if "receipt_five_readback" not in activation.get("evidence_policy", []):
            errors.append(f"{worker_id} profile missing receipt_five_readback policy")
    for worker_id, binding in bindings.get("bindings", {}).items():
        activation = binding.get("v3_production_activation") or {}
        if activation.get("runtime_authority") != "hermes_kanban":
            errors.append(f"{worker_id} binding runtime authority is not Hermes/Kanban")
        if activation.get("can_contact_operator_directly") is not False:
            errors.append(f"{worker_id} binding allows direct operator contact")
        if "factory-master-plan-completion" not in activation.get("required_release_checks", []):
            errors.append(f"{worker_id} binding missing master plan completion release check")


def audit(record: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    waves_report: dict[str, dict[str, Any]] = {}

    if record.get("record_type") != "factory_master_plan_completion":
        errors.append("$.record_type must be factory_master_plan_completion")
    if record.get("completion_version") != "v3.0.0-master-plan-100":
        errors.append("$.completion_version must be v3.0.0-master-plan-100")
    if record.get("source_plan_ref") != "private-overkill-studies/20260629-021900-overkill-factory-master-plan/PLANO_MESTRE_OVERKILL_FACTORY.md":
        errors.append("$.source_plan_ref must point to the private master plan path marker")

    waves = _as_list(record.get("waves"))
    wave_ids: set[int] = set()
    for item in waves:
        if isinstance(item, dict):
            raw_wave = item.get("wave")
            if isinstance(raw_wave, int):
                wave_ids.add(raw_wave)
            elif isinstance(raw_wave, str) and raw_wave.isdigit():
                wave_ids.add(int(raw_wave))
    missing = REQUIRED_WAVES - wave_ids
    extra = wave_ids - REQUIRED_WAVES
    if missing:
        errors.append("missing wave(s): " + ", ".join(str(item) for item in sorted(missing)))
    if extra:
        errors.append("unknown wave(s): " + ", ".join(str(item) for item in sorted(extra)))

    for wave in waves:
        if not isinstance(wave, dict):
            errors.append("wave entry must be object")
            continue
        raw_wave_id = wave.get("wave")
        wave_id = str(raw_wave_id)
        wave_errors: list[str] = []
        evidence = wave.get("evidence", {}) if isinstance(wave.get("evidence"), dict) else {}
        categories = set(evidence.keys())
        missing_categories = REQUIRED_CATEGORIES - categories
        if wave.get("status") != "implemented":
            wave_errors.append("status must be implemented")
        if wave.get("score") != 100:
            wave_errors.append("score must be 100")
        if missing_categories:
            wave_errors.append("missing evidence categories: " + ", ".join(sorted(missing_categories)))
        implementation_kinds = set(_as_list(wave.get("implementation_kinds")))
        if implementation_kinds & FORBIDDEN_FAKE_DONE:
            wave_errors.append("implementation kinds include fake-done category")
        for required_kind in ("runtime_activation", "agent_activation", "operator_activation", "test_enforced"):
            if required_kind not in implementation_kinds:
                wave_errors.append(f"missing implementation kind {required_kind}")
        evidence_count = 0
        for category, refs in evidence.items():
            if not isinstance(refs, list) or not refs:
                wave_errors.append(f"{category} must be non-empty list")
                continue
            for ref in refs:
                evidence_count += 1
                if not isinstance(ref, str) or not ref.strip():
                    wave_errors.append(f"{category} contains invalid ref")
                    continue
                if not _path_exists(root, ref):
                    wave_errors.append(f"missing evidence ref: {ref}")
        if evidence_count < 5:
            wave_errors.append("wave must carry at least five evidence refs")
        waves_report[wave_id] = {
            "result": "PASS" if not wave_errors else "FAIL",
            "score": 100 if not wave_errors else max(0, 100 - 10 * len(wave_errors)),
            "evidence_categories": sorted(categories),
            "evidence_ref_count": evidence_count,
            "errors": wave_errors,
        }
        errors.extend(f"wave {wave_id}: {item}" for item in wave_errors)

    _audit_agent_activation(root, errors)

    final_checks = record.get("final_checks", {}) if isinstance(record.get("final_checks"), dict) else {}
    for key in (
        "all_waves_score_100",
        "factory_perfect_run_passed",
        "agents_and_bindings_updated",
        "factoryctl_commands_exposed",
        "adapter_runtime_enforced",
        "human_gate_artifact_first",
        "receipt_five_anti_overclaim",
    ):
        if final_checks.get(key) is not True:
            errors.append(f"$.final_checks.{key} must be true")

    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_master_plan_completion_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - min(100, 5 * len(errors))),
        "waves": waves_report,
        "summary": {
            "wave_count": len(waves),
            "passed_waves": sum(1 for item in waves_report.values() if item["result"] == "PASS"),
            "errors": len(errors),
        },
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = ["# Factory Master Plan Completion Audit", "", f"Result: {report['result']}", f"Score: {report['score']}", ""]
    lines.append("## Waves")
    lines.append("")
    for wave_id in sorted(report["waves"], key=lambda item: int(item)):
        wave = report["waves"][wave_id]
        lines.append(f"- Wave {wave_id}: {wave['result']} / {wave['score']} ({wave['evidence_ref_count']} refs)")
        for error in wave.get("errors", []):
            lines.append(f"  - {error}")
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        for error in report["errors"]:
            lines.append(f"- {error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--record", type=Path, default=DEFAULT_RECORD)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    record = load_json(args.record)
    report = audit(record, root=ROOT)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, args.markdown)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.markdown}")
    print(report["result"])
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
