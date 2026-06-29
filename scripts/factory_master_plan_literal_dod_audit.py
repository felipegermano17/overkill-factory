#!/usr/bin/env python3
"""Audit the literal 17-item Definition of Done from the master plan.

This guard deliberately separates local implementation support from external live
proof. It returns PARTIAL_EXTERNAL when everything possible in the repo is wired
but Telegram/operator-live criteria still need a real external run.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / "templates" / "factory-master-plan-literal-dod.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-master-plan-literal-dod-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-master-plan-literal-dod-audit.md"

REQUIRED_IDS = {
    "01-telegram-natural-language-start",
    "02-manager-intake-factoryrun",
    "03-factoryrun-real-graph",
    "04-hermes-dispatch-or-typed-block",
    "05-packet-not-execution",
    "06-no-idle-safe-resume",
    "07-user-progress-without-kanban",
    "08-human-decision-readable-package",
    "09-human-gate-exception",
    "10-done-receipt-five-product-proof",
    "11-product-face-screenshots-ux-proof",
    "12-explicit-authority-sensitive-actions",
    "13-solana-ai-kit-required",
    "14-learnback-reviewable-proposal",
    "15-manager-agent-freshness",
    "16-public-github-v3-surface",
    "17-final-validation-agent-manager-e2e",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _exists(root: Path, ref: str) -> bool:
    if ref.startswith(("command:", "external:", "release:", "github:", "http://", "https://")):
        return True
    return (root / ref).exists()


def audit(matrix: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []
    criteria_report: dict[str, Any] = {}
    raw_criteria = matrix.get("criteria")
    criteria: list[Any] = raw_criteria if isinstance(raw_criteria, list) else []
    ids = {str(item.get("id")) for item in criteria if isinstance(item, dict)}
    missing = REQUIRED_IDS - ids
    extra = ids - REQUIRED_IDS
    if matrix.get("record_type") != "factory_master_plan_literal_dod":
        errors.append("record_type must be factory_master_plan_literal_dod")
    if missing:
        errors.append("missing literal DoD criteria: " + ", ".join(sorted(missing)))
    if extra:
        errors.append("unknown literal DoD criteria: " + ", ".join(sorted(extra)))

    locally_implemented = 0
    external_live_pending = 0
    external_live_verified = 0
    for item in criteria:
        if not isinstance(item, dict):
            errors.append("criteria entry must be object")
            continue
        cid = str(item.get("id"))
        item_errors: list[str] = []
        evidence_refs = item.get("evidence_refs") if isinstance(item.get("evidence_refs"), list) else []
        command_refs = item.get("command_refs") if isinstance(item.get("command_refs"), list) else []
        if item.get("local_support") is not True:
            item_errors.append("local_support must be true")
        if item.get("operator_safe") is not True:
            item_errors.append("operator_safe must be true")
        if not evidence_refs:
            item_errors.append("evidence_refs must be non-empty")
        if not command_refs:
            item_errors.append("command_refs must be non-empty")
        for ref in [*evidence_refs, *command_refs]:
            if not isinstance(ref, str) or not ref.strip():
                item_errors.append("invalid empty ref")
            elif not _exists(root, ref):
                item_errors.append(f"missing ref: {ref}")
        external_required = item.get("external_live_required") is True
        external_status = item.get("external_live_status")
        if external_required and external_status == "verified":
            external_live_verified += 1
        elif external_required:
            external_live_pending += 1
        elif external_status != "not_required":
            item_errors.append("external_live_status must be not_required when external_live_required is false")
        if not item_errors:
            locally_implemented += 1
        criteria_report[cid] = {
            "result": "PASS" if not item_errors else "FAIL",
            "local_support": item.get("local_support") is True and not item_errors,
            "external_live_required": external_required,
            "external_live_status": external_status,
            "evidence_refs": evidence_refs,
            "command_refs": command_refs,
            "errors": item_errors,
        }
        errors.extend(f"{cid}: {err}" for err in item_errors)

    if errors:
        result = "FAIL"
    elif external_live_pending:
        result = "PARTIAL_EXTERNAL"
        warnings.append("External live criteria remain pending; do not claim literal 100% until they are verified.")
    else:
        result = "PASS"
    return {
        "schema": "factory_master_plan_literal_dod_audit.v1",
        "result": result,
        "score_local_possible": 100 if not errors and locally_implemented == 17 else max(0, int(100 * locally_implemented / 17)),
        "score_literal_live": 100 if result == "PASS" else max(0, int(100 * (17 - external_live_pending) / 17)) if not errors else 0,
        "criteria": criteria_report,
        "summary": {
            "criterion_count": len(criteria),
            "locally_implemented": locally_implemented,
            "external_live_pending": external_live_pending,
            "external_live_verified": external_live_verified,
            "errors": len(errors),
        },
        "errors": errors,
        "warnings": warnings,
    }


def write_markdown(report: dict[str, Any], path: Path) -> None:
    lines = [
        "# Definition of Done literal audit",
        "",
        f"Result: {report['result']}",
        f"Local possible score: {report['score_local_possible']}",
        f"Literal live score: {report['score_literal_live']}",
        "",
        "## Criteria",
        "",
    ]
    for cid in sorted(report["criteria"]):
        c = report["criteria"][cid]
        lines.append(f"- {cid}: {c['result']} / external={c['external_live_status']}")
        for error in c.get("errors", []):
            lines.append(f"  - {error}")
    if report["warnings"]:
        lines.extend(["", "## Warnings", ""])
        lines.extend(f"- {w}" for w in report["warnings"])
    if report["errors"]:
        lines.extend(["", "## Errors", ""])
        lines.extend(f"- {e}" for e in report["errors"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)
    matrix = load_json(args.matrix)
    report = audit(matrix, root=ROOT)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(report, args.markdown)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.markdown}")
    print(report["result"])
    if report["result"] == "PASS":
        return 0
    if report["result"] == "PARTIAL_EXTERNAL":
        return 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
