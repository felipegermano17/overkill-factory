#!/usr/bin/env python3
"""Assert Issue #84 StatusSnapshot v0 negative states fail closed."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import status_snapshot_contract as contract

CASE_ALIASES = {
    "stale": {"stale"},
    "missing": {"missing"},
    "contradictory": {"contradictory"},
    "private_unavailable": {"private_unavailable"},
    "missing-gate": {"missing-gate"},
    "manual_estimate": {"manual_estimate"},
    "superseded": {"superseded"},
    "blocked": {"blocked"},
    "error": {"error"},
}


def parse_cases(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def snapshot_matches_case(data: dict[str, Any], case: str) -> bool:
    aliases = CASE_ALIASES.get(case, {case})
    if data.get("current_state") in aliases or data.get("freshness_state") in aliases:
        return True
    if case == "missing-gate":
        for gate in data.get("gate_states") or []:
            if isinstance(gate, dict) and gate.get("state") == "missing":
                return True
    if case == "private_unavailable":
        for evidence in data.get("evidence_refs") or []:
            if isinstance(evidence, dict) and evidence.get("public_safety_state") == "private_redacted":
                return True
    return False


def validate_directory(directory: Path, cases: list[str]) -> list[str]:
    errors: list[str] = []
    matched: dict[str, int] = {case: 0 for case in cases}
    for path, data in contract.load_fixtures(directory):
        fixture_id = str(data.get("fixture_id") or path.stem)
        for case in cases:
            if snapshot_matches_case(data, case):
                matched[case] += 1
                for error in contract.fail_closed_errors(data):
                    errors.append(f"{fixture_id}/{case}: {error}")
    for case, count in matched.items():
        if count == 0:
            errors.append(f"missing fail-closed fixture for case {case}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--cases", required=True, help="Comma-separated cases to assert")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = validate_directory(args.directory, parse_cases(args.cases))
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"OK: fail-closed semantics hold for {args.cases}")
    return 0


def main_with_args_for_test(argv: list[str]) -> int:
    return main_with_args(argv)


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
