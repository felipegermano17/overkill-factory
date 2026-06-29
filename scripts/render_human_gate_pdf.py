#!/usr/bin/env python3
"""Render a human gate decision package to an operator-readable fallback.

The production path may attach a PDF renderer later, but this script already
creates the required Telegram/Desktop-safe artifact-first fallback from the same
schema-backed package. It refuses raw JSON-only gates.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKAGE = ROOT / "templates" / "human-gate-decision-package.json"
DEFAULT_OUT = ROOT / ".tmp" / "human-gate-decision-package.txt"


def render(package: dict) -> str:
    options = package.get("options", [])
    lines = [
        "DECISÃO HUMANA NECESSÁRIA",
        "",
        package["executive_summary"],
        "",
        "Contexto:",
        package["context"],
        "",
        "Decisão pedida:",
        package["decision_requested"],
        "",
        "Opções:",
    ]
    for option in options:
        lines.append(f"- {option['label']}: {option['consequence']} Próximo passo: {option['next_action']}")
    lines.extend([
        "",
        "Escopo aprovado:",
        *[f"- {item}" for item in package.get("approved_scope", [])],
        "",
        "Escopo proibido:",
        *[f"- {item}" for item in package.get("forbidden_scope", [])],
        "",
        "Próxima ação segura:",
        package["next_safe_action"],
        "",
        "Fallback Telegram:",
        package["telegram_fallback"],
    ])
    return "\n".join(lines) + "\n"


def validate(package: dict) -> list[str]:
    errors: list[str] = []
    if package.get("record_type") != "human_gate_decision_package":
        errors.append("record_type must be human_gate_decision_package")
    if package.get("operator_language") != "pt-BR-simple":
        errors.append("operator language must be pt-BR-simple")
    if len(package.get("options", [])) < 2:
        errors.append("at least two options are required")
    for key in ("executive_summary", "context", "decision_requested", "next_safe_action", "telegram_fallback"):
        if len(str(package.get(key, "")).strip()) < 10:
            errors.append(f"{key} is missing or too short")
    if package.get("delivery_receipt_required") is not True:
        errors.append("delivery receipt is required")
    raw = json.dumps(package, ensure_ascii=False).lower()
    if "approve?" in raw or "aprova?" in raw:
        errors.append("approval-first prompt detected")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package", type=Path, default=DEFAULT_PACKAGE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    package = json.loads(args.package.read_text())
    errors = validate(package)
    if errors:
        for error in errors:
            print(error)
        print("FAIL")
        return 1
    if not args.check:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(render(package))
        print(f"Wrote {args.out}")
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
