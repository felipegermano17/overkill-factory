#!/usr/bin/env python3
"""Validate public planning bundles without treating them as runtime proof."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "planning-bundles" / "manifest.json"

REQUIRED_TEXT_MARKERS = (
    "candidate_only",
    "not runtime proof",
    "not human approval",
    "not production readiness",
    "Do not paste secrets",
)
INCLUDED_FILE_SUFFIXES = {".md"}
FORBIDDEN_REF_FRAGMENTS = (
    "capability",
    "control-tower",
    "operator",
    "runtime",
    "worker-packet",
    "worker-result",
)
FORBIDDEN_COMMAND_FRAGMENTS = (
    ".tmp/",
    "adapters/",
    "examples/",
    "gate-report",
    "templates/",
    "transition-plan",
    "worker-packet",
)


def load_manifest(path: Path = MANIFEST_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def repo_path(root: Path, rel: str) -> Path:
    path = root / rel
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"planning bundle path escapes repository: {rel}")
    return path


def normalized_ref(value: str) -> str:
    return value.replace("\\", "/").replace("_", "-").lower()


def contains_forbidden_fragment(value: str, fragments: tuple[str, ...]) -> str | None:
    normalized = normalized_ref(value)
    for fragment in fragments:
        if fragment in normalized:
            return fragment
    return None


def validate_manifest_data(manifest: dict[str, Any], *, root: Path = ROOT) -> list[str]:
    findings: list[str] = []
    bundles = manifest.get("bundles", [])
    if not isinstance(bundles, list) or not bundles:
        return ["planning-bundles/manifest.json: bundles must be a non-empty array"]

    seen_ids: set[str] = set()
    for bundle in bundles:
        if not isinstance(bundle, dict):
            findings.append("planning-bundles/manifest.json: bundle entry must be an object")
            continue
        bundle_id = str(bundle.get("bundle_id") or "")
        if not bundle_id:
            findings.append("planning-bundles/manifest.json: bundle missing bundle_id")
            continue
        if bundle_id in seen_ids:
            findings.append(f"{bundle_id}: duplicate bundle_id")
        seen_ids.add(bundle_id)

        if bundle.get("bundle_kind") != "planning_protocol":
            findings.append(f"{bundle_id}: bundle_kind must be planning_protocol")
        if "capability" in bundle_id.lower():
            findings.append(f"{bundle_id}: planning bundles must not duplicate capability packs")
        if "OVERKILL_VFINAL" not in bundle.get("compatible_factory_method_versions", []):
            findings.append(f"{bundle_id}: missing OVERKILL_VFINAL compatibility")

        entrypoint = str(bundle.get("entrypoint") or "")
        bundle_root = repo_path(root, entrypoint).parent if entrypoint else root / "planning-bundles" / bundle_id
        if entrypoint and entrypoint not in bundle.get("included_files", []):
            findings.append(f"{bundle_id}: entrypoint must be listed in included_files")
        if not entrypoint.startswith("planning-bundles/"):
            findings.append(f"{bundle_id}: entrypoint must live under planning-bundles/")

        included_text = ""
        for rel in bundle.get("included_files", []):
            path = repo_path(root, str(rel))
            if not normalized_ref(str(rel)).startswith("planning-bundles/"):
                findings.append(f"{bundle_id}: included file must live under planning-bundles/: {rel}")
            if not path.resolve().is_relative_to(bundle_root.resolve()):
                findings.append(f"{bundle_id}: included file must stay under the bundle entrypoint directory: {rel}")
            if path.suffix not in INCLUDED_FILE_SUFFIXES:
                findings.append(f"{bundle_id}: included file must be markdown: {rel}")
            forbidden = contains_forbidden_fragment(str(rel), FORBIDDEN_REF_FRAGMENTS)
            if forbidden:
                findings.append(f"{bundle_id}: included file crosses into non-planning surface {forbidden!r}: {rel}")
            if not path.exists():
                findings.append(f"{bundle_id}: included file does not exist: {rel}")
                continue
            included_text += "\n" + path.read_text(encoding="utf-8")

        for ref in bundle.get("compatible_schema_refs", []):
            forbidden = contains_forbidden_fragment(str(ref), FORBIDDEN_REF_FRAGMENTS)
            if forbidden:
                findings.append(f"{bundle_id}: compatible schema crosses into execution surface {forbidden!r}: {ref}")
            if not repo_path(root, str(ref)).exists():
                findings.append(f"{bundle_id}: compatible schema does not exist: {ref}")

        for output in bundle.get("expected_outputs", []):
            if not isinstance(output, dict):
                findings.append(f"{bundle_id}: expected output entry must be an object")
                continue
            if output.get("authority") != "candidate_only":
                findings.append(f"{bundle_id}: expected output {output.get('output_id')} must be candidate_only")
            schema_ref = str(output.get("candidate_schema_ref") or "")
            forbidden = contains_forbidden_fragment(schema_ref, FORBIDDEN_REF_FRAGMENTS)
            if forbidden:
                findings.append(f"{bundle_id}: candidate schema crosses into execution surface {forbidden!r}: {schema_ref}")
            if schema_ref and not repo_path(root, schema_ref).exists():
                findings.append(f"{bundle_id}: candidate schema does not exist: {schema_ref}")

        import_validation = bundle.get("import_validation")
        if not isinstance(import_validation, dict) or not import_validation.get("commands"):
            findings.append(f"{bundle_id}: import_validation.commands is required")
        elif isinstance(import_validation.get("commands"), list):
            for command in import_validation["commands"]:
                forbidden = contains_forbidden_fragment(str(command), FORBIDDEN_COMMAND_FRAGMENTS)
                if forbidden:
                    findings.append(f"{bundle_id}: import validation command must not target fixed runtime/example artifacts {forbidden!r}: {command}")

        combined_policy = "\n".join(
            [included_text, *[str(item) for item in bundle.get("safety_rules", [])], *[str(item) for item in bundle.get("non_authority_rules", [])]]
        )
        for marker in REQUIRED_TEXT_MARKERS:
            if marker not in combined_policy:
                findings.append(f"{bundle_id}: missing required safety marker {marker!r}")

    return findings


def validate(path: Path = MANIFEST_PATH) -> list[str]:
    return validate_manifest_data(load_manifest(path))


def main() -> int:
    findings = validate()
    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
