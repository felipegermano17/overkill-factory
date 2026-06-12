#!/usr/bin/env python3
"""Generate and validate public supply-chain evidence for Overkill Factory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "supply-chain"

WORKFLOW_DIR = ROOT / ".github" / "workflows"
PINNED_ACTION_RE = re.compile(r"^-?\s*uses:\s*([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@([A-Fa-f0-9]{40})\s*(?:#.*)?$")
USES_RE = re.compile(r"uses:\s*(\S+)")

SKIP_PARTS = {".git", "__pycache__", ".mypy_cache", ".pytest_cache"}
SKIP_OUTPUT_PARTS = {".tmp/factory-runs/supply-chain"}


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_ref(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def iter_repo_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        rel = repo_ref(path)
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        if any(rel == part or rel.startswith(part + "/") for part in SKIP_OUTPUT_PARTS):
            continue
        files.append(path)
    return sorted(files, key=repo_ref)


def extract_block(lines: list[str], key: str) -> list[str]:
    for index, line in enumerate(lines):
        if line.strip() == f"{key}:":
            base_indent = len(line) - len(line.lstrip(" "))
            block: list[str] = []
            for child in lines[index + 1 :]:
                if not child.strip():
                    block.append(child)
                    continue
                indent = len(child) - len(child.lstrip(" "))
                if indent <= base_indent:
                    break
                block.append(child)
            return block
    return []


def validate_workflow(path: Path) -> dict[str, Any]:
    body = text(path)
    lines = body.splitlines()
    findings: list[str] = []
    actions: list[dict[str, str]] = []

    if re.search(r"^\s*pull_request_target\s*:", body, re.MULTILINE):
        findings.append("pull_request_target is forbidden for this public CI gate")

    permissions_block = extract_block(lines, "permissions")
    permissions_text = "\n".join(permissions_block)
    if not permissions_block:
        findings.append("top-level permissions block is missing")
    if not re.search(r"^\s+contents:\s*read\s*$", permissions_text, re.MULTILINE):
        findings.append("top-level permissions must include contents: read")
    if re.search(r":\s*(write|admin)\s*$", permissions_text, re.MULTILINE):
        findings.append("workflow permissions include write/admin scope")

    for line_number, line in enumerate(lines, start=1):
        match = USES_RE.search(line)
        if not match:
            continue
        ref = match.group(1)
        if ref.startswith("./") or ref.startswith("docker://"):
            actions.append({"line": str(line_number), "uses": ref, "pin_status": "local-or-docker"})
            continue
        pinned = PINNED_ACTION_RE.search(line.strip())
        if not pinned:
            findings.append(f"line {line_number}: action is not pinned to a 40-character commit SHA")
            actions.append({"line": str(line_number), "uses": ref, "pin_status": "not-pinned"})
            continue
        actions.append(
            {
                "line": str(line_number),
                "uses": ref,
                "action": pinned.group(1),
                "sha": pinned.group(2),
                "pin_status": "pinned-sha",
            }
        )

    return {
        "workflow": repo_ref(path),
        "result": "PASS" if not findings else "FAIL",
        "findings": findings,
        "actions": actions,
        "permissions_summary": permissions_text.strip(),
    }


def validate_workflows() -> dict[str, Any]:
    workflows = sorted(WORKFLOW_DIR.glob("*.yml")) + sorted(WORKFLOW_DIR.glob("*.yaml"))
    if not workflows:
        return {
            "result": "FAIL",
            "findings": ["no GitHub Actions workflows found"],
            "workflows": [],
        }
    workflow_results = [validate_workflow(path) for path in workflows]
    findings = [
        f"{item['workflow']}: {finding}"
        for item in workflow_results
        for finding in item["findings"]
    ]
    return {
        "result": "PASS" if not findings else "FAIL",
        "findings": findings,
        "workflows": workflow_results,
    }


def dependency_posture() -> dict[str, Any]:
    manifests = [
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "poetry.lock",
        "Pipfile.lock",
        "package.json",
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "Cargo.lock",
    ]
    present = [name for name in manifests if (ROOT / name).exists()]
    runtime_dependency_manifests = list(present)
    if "pyproject.toml" in runtime_dependency_manifests:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        project = pyproject.get("project", {}) if isinstance(pyproject, dict) else {}
        has_runtime_dependencies = bool(project.get("dependencies") or project.get("optional-dependencies"))
        if not has_runtime_dependencies:
            runtime_dependency_manifests.remove("pyproject.toml")
    return {
        "result": "PASS",
        "detected_manifests": present,
        "interpretation": (
            "No package dependency manifest is present; public CI and proof runners rely on "
            "Python standard library plus pinned GitHub Actions. Future runtime dependencies "
            "must add lockfile/audit evidence before release."
            if not present
            else (
                "Only packaging metadata without runtime dependencies is present; no dependency audit follow-up is required."
                if not runtime_dependency_manifests
                else "Dependency manifests with runtime dependencies are present and require the repository-specific audit path."
            )
        ),
        "requires_followup": bool(runtime_dependency_manifests),
    }


def build_spdx_document(created_at: str) -> dict[str, Any]:
    files = iter_repo_files()
    file_entries = []
    for path in files:
        rel = repo_ref(path)
        file_entries.append(
            {
                "SPDXID": "SPDXRef-File-" + re.sub(r"[^A-Za-z0-9.-]", "-", rel),
                "fileName": rel,
                "checksums": [{"algorithm": "SHA256", "checksumValue": sha256_file(path)}],
            }
        )
    package_verification = sha256_bytes(
        "\n".join(f"{item['fileName']} {item['checksums'][0]['checksumValue']}" for item in file_entries).encode("utf-8")
    )
    return {
        "$schema": "https://overkill-factory.dev/schemas/spdx-sbom.schema.json",
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": "overkill-factory-source-sbom",
        "documentNamespace": f"https://overkill-factory.dev/sbom/{package_verification}",
        "creationInfo": {
            "created": created_at,
            "creators": ["Tool: scripts/supply_chain_proof.py"],
        },
        "packages": [
            {
                "SPDXID": "SPDXRef-Package-overkill-factory",
                "name": "overkill-factory",
                "filesAnalyzed": True,
                "packageVerificationCode": {"packageVerificationCodeValue": package_verification},
            }
        ],
        "files": file_entries,
    }


def build_worker_result(
    *,
    created_at: str,
    workflow_result: dict[str, Any],
    dependency_result: dict[str, Any],
    sbom_path: Path,
    sbom_sha256: str,
) -> dict[str, Any]:
    all_findings = list(workflow_result["findings"])
    if dependency_result["requires_followup"]:
        all_findings.append("dependency manifests present without dedicated audit evidence")
    result = "PASS" if not all_findings else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "supply_chain_result",
        "created_at": created_at,
        "worker": {
            "id": "supply-chain-gate",
            "name": "Supply Chain Gate",
            "factory_phase": "F11/F13/F16",
        },
        "card_ref": {
            "card_id": "OVERKILL-PUBLIC-SUPPLY-CHAIN-CI",
            "slice_id": "PUBLIC_FACTORY_SUPPLY_CHAIN",
            "phase": "F16",
            "risk_effective": "R2",
            "surfaces": ["public", "ci", "supply-chain", "opensource"],
            "executor_identity": "factory-maintainer",
            "reviewer_identity": "supply-chain-gate",
        },
        "result": result,
        "blocking_findings": bool(all_findings),
        "findings_summary": (
            "Public supply-chain CI proof passed: workflow permissions are least-privilege, "
            "external actions are commit-pinned, no dependency manifest needs audit yet, "
            "and a source SBOM was generated."
            if result == "PASS"
            else "Public supply-chain CI proof failed: " + "; ".join(all_findings)
        ),
        "tool_or_profile": "scripts/supply_chain_proof.py",
        "executed_by": "supply-chain-gate",
        "evidence_refs": [
            ".github/workflows/ci.yml",
            repo_ref(sbom_path),
            ".tmp/factory-runs/supply-chain/supply-chain-proof.md",
        ],
        "evidence_kind": "real",
        "reusable_for_product": False,
        "reusable_for_public_repo_release": result == "PASS",
        "next_action": (
            "Run this gate in CI and rerun via Hermes supply-chain-gate after workflow or dependency changes."
            if result == "PASS"
            else "Fix the blocking supply-chain findings before release or human promotion."
        ),
        "supply_chain_controls": {
            "workflow_security": workflow_result,
            "dependency_posture": dependency_result,
            "sbom": {
                "path": repo_ref(sbom_path),
                "sha256": sbom_sha256,
                "format": "SPDX-2.3 JSON",
                "scope": "source file inventory excluding generated .tmp/factory-runs/supply-chain outputs",
            },
        },
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    controls = result["supply_chain_controls"]
    workflow = controls["workflow_security"]
    dependency = controls["dependency_posture"]
    sbom = controls["sbom"]
    body = [
        "# Supply Chain Proof",
        "",
        f"Result: `{result['result']}`",
        "",
        "## Controls",
        "",
        f"- Workflow security: `{workflow['result']}`",
        f"- Dependency posture: `{dependency['result']}`",
        f"- SBOM: `{sbom['path']}`",
        f"- SBOM SHA-256: `{sbom['sha256']}`",
        "",
        "## Boundary",
        "",
        "This proof covers the public factory repository CI and source inventory. It is not product-specific deployment, runtime dependency, signing, custody or production approval evidence.",
        "",
        "## Next Action",
        "",
        result["next_action"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")


def build_outputs(out_dir: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    created_at = now_iso()
    workflow_result = validate_workflows()
    dependency_result = dependency_posture()
    sbom = build_spdx_document(created_at)
    temp_sbom_bytes = json.dumps(sbom, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    sbom_sha256 = sha256_bytes(temp_sbom_bytes)
    sbom_path = out_dir / "source-sbom.spdx.json"
    worker_result = build_worker_result(
        created_at=created_at,
        workflow_result=workflow_result,
        dependency_result=dependency_result,
        sbom_path=sbom_path,
        sbom_sha256=sbom_sha256,
    )
    return worker_result, sbom


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT))
    parser.add_argument("--check", action="store_true", help="Validate controls and exit non-zero on failure.")
    parser.add_argument("--no-write", action="store_true", help="Do not write proof artifacts.")
    args = parser.parse_args(argv)

    out_dir = Path(args.out_dir)
    result, sbom = build_outputs(out_dir)
    if not args.no_write:
        sbom_path = out_dir / "source-sbom.spdx.json"
        proof_path = out_dir / "supply-chain-proof.json"
        report_path = out_dir / "supply-chain-proof.md"
        write_json(sbom_path, sbom)
        result["supply_chain_controls"]["sbom"]["sha256"] = sha256_file(sbom_path)
        write_json(proof_path, result)
        write_markdown(report_path, result)
        print(f"Wrote {repo_ref(proof_path)}")
        print(f"Wrote {repo_ref(sbom_path)}")
        print(f"Wrote {repo_ref(report_path)}")

    print(result["result"])
    if result["result"] != "PASS":
        print(result["findings_summary"], file=sys.stderr)
        return 1
    if args.check:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
