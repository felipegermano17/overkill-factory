#!/usr/bin/env python3
"""Validate that canonical promises are backed by enforceable artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MATRIX = ROOT / ".tmp" / "factory-runs" / "canonical-enforcement" / "canonical-enforcement-matrix.json"
ALLOWED_STATUS = {"enforced", "bounded_public_proof"}
ALLOWED_KINDS = {
    "schema",
    "template",
    "script",
    "test",
    "worker_registry",
    "worker_profile",
    "profile_binding",
    "runtime_adapter",
    "validation_artifact",
}


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def repo_path(path: str) -> Path | None:
    if path.startswith("external:"):
        return None
    return ROOT / path.split("#", 1)[0]


def validate_matrix(matrix: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    if matrix.get("record_type") != "canonical_enforcement_matrix":
        errors.append("record_type must be canonical_enforcement_matrix")

    seen_ids: set[str] = set()
    requirements = matrix.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        return [*errors, "requirements must be a non-empty array"]

    for index, requirement in enumerate(requirements):
        if not isinstance(requirement, dict):
            errors.append(f"requirements[{index}] must be an object")
            continue
        req_id = str(requirement.get("id") or f"#{index}")
        if req_id in seen_ids:
            errors.append(f"{req_id}: duplicate requirement id")
        seen_ids.add(req_id)

        status = requirement.get("status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{req_id}: status must be enforced or bounded_public_proof")

        required_layers = set(requirement.get("required_layers") or [])
        refs = requirement.get("enforcement_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{req_id}: enforcement_refs must be non-empty")
            continue
        actual_layers = {str(ref.get("layer")) for ref in refs if isinstance(ref, dict)}
        missing_layers = sorted(required_layers - actual_layers)
        if missing_layers:
            errors.append(f"{req_id}: missing enforcement layer(s): {', '.join(missing_layers)}")

        for ref in refs:
            if not isinstance(ref, dict):
                errors.append(f"{req_id}: enforcement ref must be an object")
                continue
            kind = ref.get("kind")
            if kind not in ALLOWED_KINDS:
                errors.append(f"{req_id}: unsupported enforcement kind {kind!r}")
            path_value = str(ref.get("path") or "").strip()
            if not path_value:
                errors.append(f"{req_id}: enforcement ref path is required")
                continue
            target = repo_path(path_value)
            if target is None:
                errors.append(f"{req_id}: enforcement ref cannot be external-only: {path_value}")
                continue
            if not target.exists():
                errors.append(f"{req_id}: enforcement ref does not exist: {path_value}")
                continue
            tokens = ref.get("must_contain") or []
            if tokens:
                text = target.read_text(encoding="utf-8", errors="replace")
                for token in tokens:
                    if str(token) not in text:
                        errors.append(f"{req_id}: {path_value} does not contain required token {token!r}")

    return errors


def build_summary(matrix: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    requirements = matrix.get("requirements") if isinstance(matrix.get("requirements"), list) else []
    by_status: dict[str, int] = {}
    for requirement in requirements:
        if isinstance(requirement, dict):
            status = str(requirement.get("status") or "missing")
            by_status[status] = by_status.get(status, 0) + 1
    return {
        "$schema": "https://overkill-factory.dev/schemas/canonical-enforcement-audit-result.schema.json",
        "record_type": "canonical_enforcement_audit_result",
        "matrix_ref": ".tmp/factory-runs/canonical-enforcement/canonical-enforcement-matrix.json",
        "result": "PASS" if not errors else "FAIL",
        "requirements_checked": len(requirements),
        "status_counts": by_status,
        "errors": errors,
    }


def write_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Canonical Enforcement Audit",
        "",
        f"Result: `{summary['result']}`",
        f"Requirements checked: `{summary['requirements_checked']}`",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(summary["status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(["", "## Errors", ""])
    if summary["errors"]:
        lines.extend(f"- {error}" for error in summary["errors"])
    else:
        lines.append("- None.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit canonical documentation enforcement refs.")
    parser.add_argument("--matrix", type=Path, default=DEFAULT_MATRIX)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-md", type=Path)
    args = parser.parse_args(argv)

    matrix = load_json(args.matrix)
    errors = validate_matrix(matrix)
    summary = build_summary(matrix, errors)

    if args.out_json:
        args.out_json.parent.mkdir(parents=True, exist_ok=True)
        args.out_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if args.out_md:
        write_markdown(args.out_md, summary)
    print(json.dumps({"result": summary["result"], "requirements_checked": summary["requirements_checked"], "errors": len(errors)}, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
