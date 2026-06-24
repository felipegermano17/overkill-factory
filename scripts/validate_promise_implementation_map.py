#!/usr/bin/env python3
"""Validate the public promise-to-implementation map."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_public_json_artifacts import load_schemas, schema_name, validate_node  # noqa: E402


DEFAULT_MAP = ROOT / "docs" / "promise-implementation-map.public.json"
REQUIRED_CLAIM_IDS = {
    "hermes-runtime-floor",
    "external-operator-first-run",
    "start-understanding-before-sot",
    "fast-autonomy-with-guardrails",
    "human-gates-evidence-backed",
    "modular-capability-routing",
    "solana-ai-kit-routing",
    "product-face-design-gate",
    "bridge-operator-only",
    "self-improvement-bounded",
    "public-release-readiness",
    "no-idle-watchdog",
}

REF_FIELDS = (
    "documentation_refs",
    "implementation_refs",
    "proof_refs",
    "boundary_refs",
)

OVERCLAIM_PATTERNS = [
    re.compile(r"\bguarantees?\s+production\b", re.IGNORECASE),
    re.compile(r"\bproves?\s+production\b", re.IGNORECASE),
    re.compile(r"\b100%\s+(ready|complete|autonomous|safe)\b", re.IGNORECASE),
    re.compile(r"\bfully\s+autonomous\b", re.IGNORECASE),
    re.compile(r"\bno\s+human\s+gate\s+needed\b", re.IGNORECASE),
]

BOUNDARY_WORDS = (
    "does not",
    "cannot",
    "must not",
    "not ",
    "requires",
    "still requires",
)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def repo_path(ref: str) -> Path | None:
    if ref.startswith(("http://", "https://", "external:", "factoryctl:")):
        return None
    path = ROOT / ref
    root = ROOT.resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"ref escapes repository: {ref}") from exc
    return path


def has_overclaim(text: str) -> bool:
    return any(pattern.search(text) for pattern in OVERCLAIM_PATTERNS)


def validate_map(path: Path = DEFAULT_MAP) -> list[str]:
    findings: list[str] = []
    try:
        data = load_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [f"{path.relative_to(ROOT).as_posix()}: {exc}"]

    schemas = load_schemas()
    schema_ref = str(data.get("$schema") or "")
    schema = schemas.get(schema_name(schema_ref))
    if not schema:
        findings.append(f"{path.relative_to(ROOT).as_posix()}: schema not found for {schema_ref}")
    else:
        for error in validate_node(schema, data, "$", schemas=schemas, root_schema=schema):
            findings.append(f"{path.relative_to(ROOT).as_posix()}: {error}")

    claims = data.get("claims")
    if not isinstance(claims, list):
        return findings

    claim_ids: list[str] = []
    for index, claim in enumerate(claims):
        if not isinstance(claim, dict):
            findings.append(f"claims[{index}]: must be an object")
            continue
        claim_id = str(claim.get("claim_id") or f"claims[{index}]")
        claim_ids.append(claim_id)

        public_promise = str(claim.get("public_promise") or "")
        boundary = str(claim.get("boundary") or "")
        if has_overclaim(public_promise):
            findings.append(f"{claim_id}: public_promise uses an overclaim pattern")
        if has_overclaim(boundary):
            findings.append(f"{claim_id}: boundary uses an overclaim pattern")
        if not any(word in boundary.lower() for word in BOUNDARY_WORDS):
            findings.append(f"{claim_id}: boundary must plainly state a limit")

        implementation_refs = claim.get("implementation_refs")
        if isinstance(implementation_refs, list):
            if not any(str(ref).startswith(("scripts/", "adapters/", "agents/", "schemas/", "templates/", "plugins/")) for ref in implementation_refs):
                findings.append(f"{claim_id}: implementation_refs must include code, schema, template, registry or plugin ref")

        proof_refs = claim.get("proof_refs")
        if isinstance(proof_refs, list):
            if not any(str(ref).startswith(("tests/", "scripts/")) for ref in proof_refs):
                findings.append(f"{claim_id}: proof_refs must include a test or validator ref")

        for field in REF_FIELDS:
            refs = claim.get(field)
            if not isinstance(refs, list):
                continue
            for ref in refs:
                ref_text = str(ref)
                try:
                    target = repo_path(ref_text)
                except ValueError as exc:
                    findings.append(f"{claim_id}.{field}: {exc}")
                    continue
                if target is not None and not target.exists():
                    findings.append(f"{claim_id}.{field}: missing ref {ref_text}")

    duplicate_ids = sorted({claim_id for claim_id in claim_ids if claim_ids.count(claim_id) > 1})
    for claim_id in duplicate_ids:
        findings.append(f"{claim_id}: duplicate claim_id")

    missing_required = sorted(REQUIRED_CLAIM_IDS - set(claim_ids))
    if missing_required:
        findings.append(f"missing required claim ids: {', '.join(missing_required)}")

    return findings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = validate_map(args.map)
    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
