#!/usr/bin/env python3
"""Validate public docs and visual maps against canonical factory state."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "docs" / "public-surface.manifest.json"

RISK_TIERS = {"R0", "R1", "R2", "R3", "R4"}
OVERCLAIM_PATTERNS = [
    re.compile(r"visual map\s+(is|becomes|acts as)\s+the\s+source\s+of\s+truth", re.IGNORECASE),
    re.compile(r"public docs\s+(prove|guarantee)\s+runtime", re.IGNORECASE),
    re.compile(r"conceptual map\s+(proves|guarantees)\s+production", re.IGNORECASE),
    re.compile(r"map\s+(proves|guarantees)\s+runtime\s+readiness", re.IGNORECASE),
]


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def normalized(text: str) -> str:
    return " ".join(text.lower().split())


def repo_path(root: Path, rel: str) -> Path:
    path = root / rel
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"public surface path escapes repository: {rel}")
    return path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_worker_count(root: Path) -> int:
    registry = load_json(root / "agents" / "worker-registry.public.json")
    workers = registry.get("workers", [])
    return len(workers) if isinstance(workers, list) else 0


def stage_map_count(root: Path) -> int:
    text = (root / "docs" / "agents" / "factory-stage-agent-map.md").read_text(encoding="utf-8")
    return len(re.findall(r"^\| \d+\.", text, flags=re.MULTILINE))


def html_worker_count(text: str) -> int | None:
    match = re.search(r"expectedCount:\\s*(\\d+)", text)
    return int(match.group(1)) if match else None


def html_stage_count(text: str) -> int | None:
    return len(re.findall(r"\\{ id: \"[^\"]+\", n:", text)) or None


def missing_risk_tiers(text: str) -> set[str]:
    if "R0-R4" in text:
        return set()
    return {tier for tier in RISK_TIERS if tier not in text}


def public_doc_overclaim_findings(path: str, text: str) -> list[str]:
    findings: list[str] = []
    for pattern in OVERCLAIM_PATTERNS:
        if pattern.search(text):
            findings.append(f"{path}: public surface overclaims runtime authority")
    return findings


def has_surface_metadata(surface: dict[str, Any], text: str) -> bool:
    surface_id = str(surface.get("surface_id") or "")
    rel = str(surface.get("path") or "")
    if rel.endswith(".html"):
        return 'id="overkill-public-surface-metadata"' in text and surface_id in text
    if rel.endswith(".svg"):
        return "<metadata" in text and surface_id in text
    return True


def source_ref_exists(root: Path, ref: str) -> bool:
    if ref.startswith(("http://", "https://", "external:", "factoryctl:")):
        return True
    return repo_path(root, ref).exists()


def validate_surface(
    manifest: dict[str, Any],
    surface: dict[str, Any],
    *,
    root: Path,
    check_published: bool,
    fetcher: Callable[[str], bytes] | None,
) -> list[str]:
    findings: list[str] = []
    rel = str(surface.get("path") or "")
    path = repo_path(root, rel)
    if not path.exists():
        return [f"{rel}: public surface file is missing"]
    text = path.read_text(encoding="utf-8")
    checks = set(surface.get("claim_checks", []))

    if "metadata" in checks and not has_surface_metadata(surface, text):
        findings.append(f"{rel}: missing public surface metadata")

    if "source_refs_exist" in checks:
        for ref in surface.get("source_refs", []):
            if not source_ref_exists(root, str(ref)):
                findings.append(f"{rel}: source_ref does not exist: {ref}")

    if "worker_count" in checks:
        expected = int(surface.get("expected_worker_count") or canonical_worker_count(root))
        actual = canonical_worker_count(root)
        if expected != actual:
            findings.append(f"{rel}: manifest worker count {expected} does not match registry count {actual}")
        visual_count = html_worker_count(text)
        if visual_count is not None and visual_count != actual:
            findings.append(f"{rel}: visual worker count {visual_count} does not match registry count {actual}")

    if "stage_count" in checks:
        canonical = stage_map_count(root)
        manifest_canonical = int(surface.get("canonical_stage_count") or canonical)
        if manifest_canonical != canonical:
            findings.append(f"{rel}: manifest canonical stage count {manifest_canonical} does not match stage map {canonical}")
        visual = html_stage_count(text)
        expected_stage_count = surface.get("expected_stage_count")
        if visual is not None and expected_stage_count is not None and int(expected_stage_count) != visual:
            findings.append(f"{rel}: visual stage count {visual} does not match manifest expected_stage_count {expected_stage_count}")
        if visual is not None and visual != canonical and not surface.get("conceptual_exceptions"):
            findings.append(f"{rel}: visual stage count differs from canonical stage map without conceptual_exceptions")

    if "risk_tiers" in checks:
        missing = missing_risk_tiers(text)
        if missing:
            findings.append(f"{rel}: missing risk tier labels {sorted(missing)}")

    if "source_of_truth_disclaimer" in checks:
        required = [str(item) for item in surface.get("required_phrases", [])]
        lower = normalized(text)
        for phrase in required:
            if normalized(phrase) not in lower:
                findings.append(f"{rel}: missing required public-boundary phrase {phrase!r}")

    if "no_runtime_proof_claim" in checks:
        findings.extend(public_doc_overclaim_findings(rel, text))

    if "expected_links" in checks:
        for link in surface.get("expected_links", []):
            if str(link) not in text:
                findings.append(f"{rel}: missing expected public link {link}")

    published_url = surface.get("published_url")
    if check_published and published_url:
        remote = (fetcher or fetch_url)(str(published_url))
        local_sha = sha256_bytes(path.read_bytes())
        remote_sha = sha256_bytes(remote)
        if local_sha != remote_sha:
            findings.append(f"{rel}: published_out_of_sync for {published_url}")

    return findings


def fetch_url(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def validate_manifest_data(
    manifest: dict[str, Any],
    *,
    root: Path = ROOT,
    check_published: bool = False,
    fetcher: Callable[[str], bytes] | None = None,
) -> list[str]:
    findings: list[str] = []
    for ref in manifest.get("canonical_sources", []):
        if not source_ref_exists(root, str(ref)):
            findings.append(f"manifest: canonical source does not exist: {ref}")
    surfaces = manifest.get("surfaces", [])
    if not isinstance(surfaces, list) or not surfaces:
        return ["manifest: surfaces must be a non-empty array"]
    for surface in surfaces:
        if isinstance(surface, dict):
            findings.extend(
                validate_surface(
                    manifest,
                    surface,
                    root=root,
                    check_published=check_published,
                    fetcher=fetcher,
                )
            )
        else:
            findings.append("manifest: surface entry must be an object")
    return findings


def validate_manifest(
    *,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
    check_published: bool = False,
    fetcher: Callable[[str], bytes] | None = None,
) -> list[str]:
    manifest = load_json(manifest_path)
    return validate_manifest_data(manifest, root=root, check_published=check_published, fetcher=fetcher)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--check-published", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    findings = validate_manifest(manifest_path=args.manifest, check_published=args.check_published)
    if findings:
        for finding in findings:
            print(finding, file=sys.stderr)
        return 1
    if args.check_published:
        print("OK")
    else:
        print("OK (published map status: not_checked)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
