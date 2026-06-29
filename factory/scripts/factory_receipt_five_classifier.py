#!/usr/bin/env python3
"""Classify Receipt Five evidence without overclaiming.

The classifier separates contract_pass, runtime_pass, product_pass and
release_pass. It fails closed when evidence is scaffold/template/stale or lacks
readback.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RECEIPT = ROOT / "templates" / "receipt-five.json"
DEFAULT_OUT = ROOT / ".tmp" / "receipt-five-classification.json"

BAD_EVIDENCE_TERMS = ("scaffold", "template-only", "stale review", "chat summary")


def _strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for item in value:
            out.extend(_strings(item))
        return out
    if isinstance(value, dict):
        out: list[str] = []
        for item in value.values():
            out.extend(_strings(item))
        return out
    return []


def _without_policy_fields(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _without_policy_fields(item) for key, item in value.items() if key not in {"not_valid_evidence", "blocked_claims"}}
    if isinstance(value, list):
        return [_without_policy_fields(item) for item in value]
    return value


def classify(receipt: dict[str, Any]) -> dict[str, Any]:
    policy_free_receipt = _without_policy_fields(receipt)
    text = "\n".join(_strings(policy_free_receipt)).lower()
    refs = [item for item in _strings(receipt) if item.startswith(("templates/", "schemas/", "scripts/", "docs/", "examples/", ".tmp/", "external:"))]
    has_readback = "readback" in text or "artifact readback" in text
    has_runtime = "runtime" in text or "hermes" in text or "kanban" in text
    has_product = "product" in text or "sot" in text or "product-specific" in text
    has_release = "release" in text or "promotion" in text
    bad_terms = [term for term in BAD_EVIDENCE_TERMS if term in text]
    levels = []
    if refs and not bad_terms:
        levels.append("contract_pass")
    if has_readback and has_runtime and not bad_terms:
        levels.append("runtime_pass")
    if has_readback and has_runtime and has_product and not bad_terms:
        levels.append("product_pass")
    if has_readback and has_runtime and has_product and has_release and not bad_terms:
        levels.append("release_pass")
    result = "PASS" if {"contract_pass", "runtime_pass", "product_pass", "release_pass"}.issubset(levels) else "BLOCKED"
    return {
        "record_type": "receipt_five_classification",
        "result": result,
        "levels": levels,
        "has_readback": has_readback,
        "has_runtime_proof": has_runtime,
        "has_product_specific_proof": has_product,
        "has_release_proof": has_release,
        "bad_evidence_terms": bad_terms,
        "evidence_ref_count": len(refs),
        "summary": "Receipt Five has release-grade proof" if result == "PASS" else "Receipt Five is not enough to claim done",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)
    receipt = json.loads(args.receipt.read_text())
    report = classify(receipt)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(f"Wrote {args.out}")
    print(report["result"])
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
