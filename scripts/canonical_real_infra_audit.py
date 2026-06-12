#!/usr/bin/env python3
"""Answer whether the canonical factory is implemented in real infrastructure.

This audit intentionally separates "traceable to an artifact" from
"implemented as executable factory infrastructure". A schema, template or
document can be useful, but it is not the same as a runtime gate, adapter,
automation or tested enforcement path.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TRACE = ROOT / "validation" / "canonical-linear-traceability" / "canonical-linear-traceability.json"
DEFAULT_OUT_JSON = ROOT / "validation" / "canonical-real-infra" / "canonical-real-infra-audit.json"
DEFAULT_OUT_MD = ROOT / "docs" / "validation" / "canonical-real-infra-audit.md"
SCHEMA = "https://overkill-factory.dev/schemas/canonical-real-infra-audit.schema.json"
RUNTIME_ENFORCEMENT_PATH = ROOT / "scripts" / "canonical_runtime_enforcement.py"

STATUS_MAP = {
    "implemented_by_runtime": "runtime_enforced",
    "implemented_by_contract": "contract_only",
    "bounded_public_proof": "bounded_proof_only",
    "foundational_text_tracked": "not_runtime_process",
    "partial_requires_live_pilot": "not_runtime_implemented",
}
REAL_INFRA_STATUS = {"runtime_enforced"}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_runtime_enforcement() -> Any:
    spec = importlib.util.spec_from_file_location("canonical_runtime_enforcement_for_audit", RUNTIME_ENFORCEMENT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load runtime enforcement from {RUNTIME_ENFORCEMENT_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def classify_checkpoint(record: dict[str, Any], runtime_rule_index: dict[str, dict[str, Any]]) -> dict[str, Any]:
    implementation_status = str(record.get("implementation_status") or "")
    checkpoint_id = str(record.get("checkpoint_id") or "")
    runtime_rule = runtime_rule_index.get(checkpoint_id)
    real_status = "runtime_enforced" if runtime_rule else STATUS_MAP.get(implementation_status, "unknown")
    refs = record.get("implementation_refs") if isinstance(record.get("implementation_refs"), list) else []
    ref_kinds = sorted({str(item.get("kind")) for item in refs if isinstance(item, dict)})
    has_runtime_ref = bool(runtime_rule) or any(kind in {"script", "runtime_adapter"} for kind in ref_kinds)
    has_test_ref = "test" in ref_kinds

    if runtime_rule:
        reason = "Canonical runtime rule exists and is enforced through factoryctl/Hermes transition gating."
    elif real_status == "runtime_enforced":
        reason = "Runtime or executable enforcement is present and tracked by the linear audit."
    elif real_status == "contract_only":
        reason = "Mapped to contracts, schemas, templates, workers or tests, but not proven as a runtime-enforced process."
    elif real_status == "bounded_proof_only":
        reason = "There is bounded public-safe proof, not general real-factory enforcement for every matching case."
    elif real_status == "not_runtime_process":
        reason = "This is canonical framing or vocabulary; it is traceable but not an executable process."
    elif real_status == "not_runtime_implemented":
        reason = "The linear audit itself marks this checkpoint as requiring further readiness proof."
    else:
        reason = "The linear audit status is unknown to this runtime implementation classifier."

    return {
        "sequence": record.get("sequence"),
        "canonical_line": record.get("canonical_line"),
        "checkpoint_type": record.get("checkpoint_type"),
        "canonical_heading": record.get("canonical_heading"),
        "linear_status": implementation_status,
        "real_infra_status": real_status,
        "has_runtime_ref": has_runtime_ref,
        "has_test_ref": has_test_ref,
        "ref_kinds": ref_kinds,
        "runtime_rule_ref": runtime_rule.get("rule_id") if runtime_rule else None,
        "reason": reason,
        "next_action": record.get("next_action"),
    }


def build_audit(trace_path: Path = DEFAULT_TRACE) -> dict[str, Any]:
    trace = load_json(trace_path)
    runtime_enforcement = load_runtime_enforcement()
    rulebook = runtime_enforcement.build_rulebook(trace)
    runtime_rule_index = {
        str(rule.get("checkpoint_id")): rule
        for rule in rulebook.get("rules", [])
        if isinstance(rule, dict) and rule.get("checkpoint_id")
    }
    checkpoints = [classify_checkpoint(record, runtime_rule_index) for record in trace.get("checkpoints", [])]
    status_counts: dict[str, int] = {}
    for checkpoint in checkpoints:
        status = str(checkpoint["real_infra_status"])
        status_counts[status] = status_counts.get(status, 0) + 1

    runtime_enforced = status_counts.get("runtime_enforced", 0)
    non_runtime_processes = status_counts.get("not_runtime_process", 0)
    total = len(checkpoints)
    not_runtime_enforced = total - runtime_enforced - non_runtime_processes
    all_actionable_runtime = total > 0 and not_runtime_enforced == 0 and not rulebook["summary"]["unmapped_actionable_checkpoints"]

    return {
        "$schema": SCHEMA,
        "record_type": "canonical_real_infra_audit",
        "source_trace_ref": str(trace_path.relative_to(ROOT)).replace("\\", "/"),
        "canonical_doc_ref": trace.get("canonical_doc_ref"),
        "canonical_sha256": trace.get("canonical_sha256"),
        "question_answered": "Are all canonical stages, rules and processes implemented as real factory infrastructure?",
        "result": "PASS" if all_actionable_runtime else "FAIL",
        "all_canonical_steps_rules_processes_runtime_implemented": all_actionable_runtime,
        "all_actionable_canonical_processes_runtime_implemented": all_actionable_runtime,
        "answer": "yes" if all_actionable_runtime else "no",
        "classification_rule": (
            "A checkpoint counts as runtime implemented only when it has a canonical runtime rule enforced "
            "through factoryctl/Hermes transition gating, or is explicitly a non-runtime canonical definition."
        ),
        "summary": {
            "checkpoints_checked": total,
            "runtime_enforced": runtime_enforced,
            "non_runtime_processes": non_runtime_processes,
            "not_runtime_enforced": not_runtime_enforced,
            "runtime_rules": rulebook["summary"]["runtime_rules"],
            "unmapped_actionable_checkpoints": rulebook["summary"]["unmapped_actionable_checkpoints"],
            "real_infra_status_counts": status_counts,
        },
        "blocking_summary": [
            "The canonical document is not fully implemented as real runtime infrastructure.",
            "Most checkpoints are still contract-only, bounded proof only, or foundational text.",
            "This audit does not require a pilot; it answers from repo/runtime infrastructure evidence.",
        ]
        if not all_actionable_runtime
        else [],
        "checkpoints": checkpoints,
    }


def validate_audit(audit: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if audit.get("record_type") != "canonical_real_infra_audit":
        errors.append("record_type must be canonical_real_infra_audit")
    checkpoints = audit.get("checkpoints")
    if not isinstance(checkpoints, list) or not checkpoints:
        errors.append("checkpoints must be a non-empty array")
        return errors

    runtime_enforced = 0
    non_runtime_processes = 0
    for index, checkpoint in enumerate(checkpoints):
        if not isinstance(checkpoint, dict):
            errors.append(f"checkpoints[{index}] must be an object")
            continue
        status = checkpoint.get("real_infra_status")
        if status not in set(STATUS_MAP.values()) | {"unknown"}:
            errors.append(f"checkpoints[{index}]: unsupported real_infra_status {status!r}")
        if status in REAL_INFRA_STATUS:
            runtime_enforced += 1
        if status == "not_runtime_process":
            non_runtime_processes += 1

    summary = audit.get("summary") if isinstance(audit.get("summary"), dict) else {}
    if summary.get("runtime_enforced") != runtime_enforced:
        errors.append("summary.runtime_enforced does not match checkpoints")
    if summary.get("non_runtime_processes") != non_runtime_processes:
        errors.append("summary.non_runtime_processes does not match checkpoints")
    not_runtime_enforced = len(checkpoints) - runtime_enforced - non_runtime_processes
    expected_all_runtime = not_runtime_enforced == 0
    if audit.get("all_canonical_steps_rules_processes_runtime_implemented") != expected_all_runtime:
        errors.append("all_canonical_steps_rules_processes_runtime_implemented does not match checkpoint statuses")
    if audit.get("all_actionable_canonical_processes_runtime_implemented") != expected_all_runtime:
        errors.append("all_actionable_canonical_processes_runtime_implemented does not match checkpoint statuses")
    if audit.get("answer") != ("yes" if expected_all_runtime else "no"):
        errors.append("answer does not match runtime implementation verdict")
    if audit.get("result") != ("PASS" if expected_all_runtime else "FAIL"):
        errors.append("result does not match runtime implementation verdict")
    return errors


def write_json(path: Path, audit: dict[str, Any], errors: list[str]) -> None:
    output = dict(audit)
    output["validation_errors"] = errors
    if errors:
        output["result"] = "FAIL"
        output["answer"] = "no"
        output["all_canonical_steps_rules_processes_runtime_implemented"] = False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown(path: Path, audit: dict[str, Any], errors: list[str]) -> None:
    summary = audit["summary"]
    lines = [
        "# Canonical Real Infra Audit",
        "",
        "> Document status: CURRENT RUNTIME EVIDENCE.",
        "> Current authority: `scripts/factoryctl.py` and `validation/canonical-real-infra/canonical-real-infra-audit.json`.",
        "> Runtime boundary: This proves actionable canonical process enforcement in the factory; it does not approve a product-specific release.",
        "",
        f"Question: {audit['question_answered']}",
        f"Answer: `{audit['answer']}`",
        f"Result: `{audit['result']}`",
        f"All runtime implemented: `{audit['all_canonical_steps_rules_processes_runtime_implemented']}`",
        f"All actionable runtime implemented: `{audit['all_actionable_canonical_processes_runtime_implemented']}`",
        "",
        "This audit does not use a pilot as proof. It classifies the existing repo/runtime infrastructure.",
        "",
        "## Summary",
        "",
        f"- Checkpoints checked: `{summary['checkpoints_checked']}`",
        f"- Runtime enforced: `{summary['runtime_enforced']}`",
        f"- Non-runtime canonical definitions: `{summary['non_runtime_processes']}`",
        f"- Not runtime enforced: `{summary['not_runtime_enforced']}`",
        f"- Runtime rules: `{summary['runtime_rules']}`",
        f"- Unmapped actionable checkpoints: `{summary['unmapped_actionable_checkpoints']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(summary["real_infra_status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")

    lines.extend(["", "## Blocking Summary", ""])
    if audit["blocking_summary"]:
        lines.extend(f"- {item}" for item in audit["blocking_summary"])
    else:
        lines.append("- None.")

    lines.extend(["", "## Validation Errors", ""])
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- None.")

    lines.extend(
        [
            "",
            "## Checkpoints",
            "",
            "| # | Line | Checkpoint | Linear status | Real infra status | Runtime rule | Reason |",
            "| ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for checkpoint in audit["checkpoints"]:
        lines.append(
            "| {sequence} | {line} | {heading} | `{linear}` | `{real}` | {rule} | {reason} |".format(
                sequence=checkpoint["sequence"],
                line=checkpoint["canonical_line"],
                heading=escape_md(checkpoint["canonical_heading"]),
                linear=escape_md(checkpoint["linear_status"]),
                real=escape_md(checkpoint["real_infra_status"]),
                rule=escape_md(checkpoint.get("runtime_rule_ref") or ""),
                reason=escape_md(checkpoint["reason"]),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit whether canonical checkpoints are implemented in real infra.")
    parser.add_argument("--trace", type=Path, default=DEFAULT_TRACE)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args(argv)

    audit = build_audit(args.trace)
    errors = validate_audit(audit)
    write_json(args.out_json, audit, errors)
    write_markdown(args.out_md, audit, errors)
    print(
        json.dumps(
            {
                "result": "FAIL" if errors else audit["result"],
                "answer": "no" if errors else audit["answer"],
                "checkpoints_checked": audit["summary"]["checkpoints_checked"],
                "runtime_enforced": audit["summary"]["runtime_enforced"],
                "non_runtime_processes": audit["summary"]["non_runtime_processes"],
                "not_runtime_enforced": audit["summary"]["not_runtime_enforced"],
                "runtime_rules": audit["summary"]["runtime_rules"],
                "errors": len(errors),
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
