#!/usr/bin/env python3
"""Validate Issue #84 StatusSnapshot v0 fixture inventory."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import status_snapshot_contract as contract


def parse_required_cases(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {part.strip() for part in raw.split(",") if part.strip()}


def validate_schema_file(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"schema not found: {path}"]
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"schema invalid JSON: {exc}"]
    if schema.get("$id") != contract.SCHEMA_URL:
        errors.append(f"schema $id expected {contract.SCHEMA_URL}")
    required = set(schema.get("required") or [])
    missing_schema_fields = set(contract.REQUIRED_TOP_LEVEL) - required
    if missing_schema_fields:
        errors.append(f"schema missing required declarations: {sorted(missing_schema_fields)}")
    return errors


def validate_directory(directory: Path, *, schema_path: Path | None = None, required_cases: set[str] | None = None, fail_closed: bool = False) -> list[str]:
    errors: list[str] = []
    if schema_path is not None:
        errors.extend(validate_schema_file(schema_path))
    if not directory.exists():
        return [f"fixture directory not found: {directory}"]

    seen: set[str] = set()
    paths = contract.fixture_paths(directory)
    if not paths:
        return [f"no FX*.json fixtures found in {directory}"]

    for path in paths:
        try:
            data = contract.load_json(path)
        except (ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: invalid JSON object: {exc}")
            continue
        fixture_id = str(data.get("fixture_id") or path.stem.split("-", 1)[0])
        if fixture_id in seen:
            errors.append(f"{path.name}: duplicate fixture_id {fixture_id}")
        seen.add(fixture_id)
        for error in contract.validate_snapshot(data):
            errors.append(f"{path.name}: {error}")
        if fail_closed:
            for error in contract.fail_closed_errors(data):
                errors.append(f"{path.name}: {error}")

    required_cases = required_cases or set()
    missing = sorted(required_cases - seen)
    if missing:
        errors.append(f"missing required fixture cases: {', '.join(missing)}")
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--schema", type=Path, required=True)
    parser.add_argument("--require-cases", help="Comma-separated fixture ids, e.g. FX01,FX02")
    parser.add_argument("--fail-closed", action="store_true", help="Require fail-closed states to block/review/refresh/fix only")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    errors = validate_directory(
        args.directory,
        schema_path=args.schema,
        required_cases=parse_required_cases(args.require_cases),
        fail_closed=args.fail_closed,
    )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print(f"OK: {args.directory} satisfies StatusSnapshot v0 fixture inventory")
    return 0


def main_with_args_for_test(argv: list[str]) -> int:
    return main_with_args(argv)


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
