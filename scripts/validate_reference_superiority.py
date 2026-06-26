#!/usr/bin/env python3
"""Validate reference-derived negative fixtures for Factory V2 claims."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_public_json_artifacts import load_schemas, validate_node  # noqa: E402


REQUIRED_REFERENCE_PROJECTS = {"aiox-core", "tess", "orca", "superpowers", "solana-ai-kit"}


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate_reference_superiority(path: Path) -> list[str]:
    errors: list[str] = []
    data = load_json(path)
    schemas = load_schemas()
    schema = schemas.get("reference-derived-negative-fixture.schema.json")
    if not isinstance(schema, dict):
        return ["reference-derived-negative-fixture schema is not bundled"]
    errors.extend(
        validate_node(schema, data, "reference_derived_negative_fixtures", schemas=schemas, root_schema=schema)
    )

    fixtures = [item for item in data.get("fixtures", []) if isinstance(item, dict)]
    projects = {str(item.get("reference_project") or "") for item in fixtures}
    missing_projects = sorted(REQUIRED_REFERENCE_PROJECTS - projects)
    if missing_projects:
        errors.append("reference fixture corpus missing projects: " + ", ".join(missing_projects))

    seen_ids: set[str] = set()
    for index, fixture in enumerate(fixtures):
        fixture_id = str(fixture.get("fixture_id") or "")
        if fixture_id in seen_ids:
            errors.append(f"fixtures[{index}].fixture_id duplicates {fixture_id}")
        seen_ids.add(fixture_id)
        if fixture.get("expected_factory_result") != "BLOCKED":
            errors.append(f"{fixture_id}: negative reference fixture must expect BLOCKED")
        if len(fixture.get("overkill_controls", [])) < 2:
            errors.append(f"{fixture_id}: requires at least two Overkill controls")
        if not fixture.get("regression_test_ref"):
            errors.append(f"{fixture_id}: requires regression_test_ref")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, nargs="?", default=ROOT / "fixtures" / "v2" / "reference-derived-negative-fixtures.json")
    args = parser.parse_args(argv)
    errors = validate_reference_superiority(args.path)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
