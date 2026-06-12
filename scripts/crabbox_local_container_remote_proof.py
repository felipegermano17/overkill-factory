#!/usr/bin/env python3
"""Run a Crabbox ephemeral-container remote proof for the public product."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "production" / "remote-proof" / "managed-testbox-result.json"
DEFAULT_MD_OUT = ROOT / ".tmp" / "factory-runs" / "production" / "remote-proof" / "managed-testbox-result.md"
PRODUCT_SOURCE = ROOT / "products" / "qvg-public-validation-product"
DEFAULT_COMMAND = (
    "python3 --version && "
    "python3 scripts/validate_public_json_artifacts.py && "
    "python3 scripts/secret_safety_scan.py && "
    "python3 scripts/public_safety_scan.py && "
    "python3 scripts/full_product_worker_graph.py --require-pass"
)
TIMING_RE = re.compile(r"\{.*\"provider\"\s*:\s*\"local-container\".*\}")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_ref(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def source_sha256(path: Path = PRODUCT_SOURCE) -> str:
    import hashlib

    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file():
            digest.update(item.relative_to(path).as_posix().encode("utf-8"))
            digest.update(b"\0")
            digest.update(item.read_bytes())
            digest.update(b"\0")
    return digest.hexdigest()


def tail(text: str, limit: int = 6000) -> str:
    text = text.replace(str(ROOT), "<repo>")
    text = text.replace("/srv/" + "hermes", "<runtime>")
    return text[-limit:]


def sanitize_obj(value: Any) -> Any:
    if isinstance(value, str):
        return tail(value, limit=len(value) + 64)
    if isinstance(value, list):
        return [sanitize_obj(item) for item in value]
    if isinstance(value, dict):
        return {key: sanitize_obj(item) for key, item in value.items()}
    return value


def parse_timing_json(stdout: str, stderr: str) -> dict[str, Any]:
    for line in reversed((stdout + "\n" + stderr).splitlines()):
        candidate = line.strip()
        if not candidate.startswith("{"):
            continue
        if not TIMING_RE.match(candidate):
            continue
        return sanitize_obj(json.loads(candidate))
    raise ValueError("Crabbox timing JSON line was not found")


def command_passed(stdout: str, timing: dict[str, Any], command: str) -> bool:
    required = [
        "python3 scripts/validate_public_json_artifacts.py",
        "python3 scripts/secret_safety_scan.py",
        "python3 scripts/public_safety_scan.py",
        "python3 scripts/full_product_worker_graph.py --require-pass",
    ]
    return (
        timing.get("exitCode") == 0
        and stdout.count("OK") >= 3
        and "PASS" in stdout
        and all(item in command for item in required)
    )


def active_local_container_leases(crabbox_bin: str, env: dict[str, str]) -> tuple[int | None, str]:
    completed = subprocess.run(
        [crabbox_bin, "list", "--provider", "local-container"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
        timeout=60,
    )
    output = completed.stdout + completed.stderr
    if completed.returncode != 0:
        return None, tail(output, 2000)
    non_empty = [line for line in completed.stdout.splitlines() if line.strip()]
    return len(non_empty), tail(output, 2000)


def build_result(
    *,
    crabbox_version: str,
    command: str,
    completed: subprocess.CompletedProcess[str],
    timing: dict[str, Any],
    active_leases_after: int | None,
    lease_list_output: str,
) -> dict[str, Any]:
    pass_status = (
        completed.returncode == 0
        and command_passed(completed.stdout, timing, command)
        and timing.get("leaseStopped") is True
        and active_leases_after in (0, None)
    )
    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "remote_proof_result",
        "created_at": utc_now(),
        "worker": {
            "id": "remote-proof-runner",
            "name": "Remote Proof Runner",
            "factory_phase": "F13-F16",
        },
        "card_ref": {
            "card_id": "QVG-PRODUCTION-REMOTE-PROOF",
            "slice_id": "QVG_PUBLIC_VALIDATION_PRODUCT",
            "phase": "F16",
            "risk_effective": "R3",
            "surfaces": ["remote-proof", "crabbox", "container", "public-product"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "product_target": {
            "product_id": "qvg-public-validation-product",
            "source_ref": "products/qvg-public-validation-product",
            "source_sha256": source_sha256(),
            "approval_scope": "Reusable only for the public Quasar Vault Guard validation product and this repository state.",
            "environment_class": "crabbox-local-container-production-validation",
        },
        "result": "PASS" if pass_status else "FAIL",
        "blocking_findings": not pass_status,
        "findings_summary": (
            "Crabbox created an ephemeral local-container lease, synced the repository, ran product validation commands and stopped the lease."
            if pass_status
            else "Crabbox ephemeral-container proof did not satisfy every required check."
        ),
        "tool_or_profile": "crabbox local-container",
        "executed_by": "remote-proof-runner",
        "evidence_kind": "real",
        "reusable_for_product": pass_status,
        "provider": "local-container",
        "provider_kind": "crabbox_ephemeral_container",
        "brokered_cloud_or_testbox": False,
        "managed_by_crabbox": True,
        "crabbox_version": crabbox_version,
        "remote_command": {
            "command": command,
            "exit_code": completed.returncode,
            "stdout_tail": tail(completed.stdout),
            "stderr_tail": tail(completed.stderr),
        },
        "timing": timing,
        "cleanup_evidence": {
            "lease_stopped": timing.get("leaseStopped") is True,
            "lease_id": timing.get("leaseId"),
            "slug": timing.get("slug"),
            "active_local_container_leases_after": active_leases_after,
            "lease_list_output_tail": lease_list_output,
        },
        "checks_executed": [
            "python3 scripts/validate_public_json_artifacts.py",
            "python3 scripts/secret_safety_scan.py",
            "python3 scripts/public_safety_scan.py",
            "python3 scripts/full_product_worker_graph.py --require-pass",
        ],
        "evidence_refs": [
            ".tmp/factory-runs/production/remote-proof/managed-testbox-result.md",
            ".tmp/factory-runs/product-specific/qvg-full-product-worker-graph.json",
            ".tmp/factory-runs/production/product-face/product-face-result.json",
            ".tmp/factory-runs/production/quasar/auditor-result.json",
            ".tmp/factory-runs/production/quasar/cu-svm-economic-proof.json",
        ],
        "production_boundary": (
            "This is a real Crabbox-managed ephemeral container proof. It is not a brokered cloud lease and not Blacksmith Testbox; "
            "those paths still require their own credentials if a project policy mandates that exact provider."
        ),
        "next_action": (
            "Use this as the product remote-proof lane for the public validation product. "
            "Escalate to brokered cloud or Blacksmith only when the product policy requires provider parity beyond ephemeral container isolation."
        ),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    timing = result.get("timing") or {}
    cleanup = result.get("cleanup_evidence") or {}
    lines = [
        "# Crabbox Ephemeral Container Remote Proof",
        "",
        f"Result: `{result['result']}`",
        f"Provider: `{result['provider']}`",
        f"Reusable for product: `{str(result['reusable_for_product']).lower()}`",
        f"Lease stopped: `{str(cleanup.get('lease_stopped')).lower()}`",
        f"Lease id: `{cleanup.get('lease_id')}`",
        f"Total runtime ms: `{timing.get('totalMs')}`",
        "",
        "## What Ran",
        "",
        f"`{result['remote_command']['command']}`",
        "",
        "## Boundary",
        "",
        result["production_boundary"],
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def run_proof(args: argparse.Namespace) -> dict[str, Any]:
    crabbox_bin = args.crabbox_bin or shutil.which("crabbox")
    if not crabbox_bin:
        raise RuntimeError("crabbox binary was not found on PATH")
    env = os.environ.copy()
    env.setdefault("HOME", str(Path.home()))
    env.setdefault("HERMES_HOME", env["HOME"])
    command = args.command or DEFAULT_COMMAND
    if not args.no_write and not args.no_clean_previous:
        for stale in (args.out, args.md_out):
            if stale.exists():
                stale.unlink()
    version = subprocess.run(
        [crabbox_bin, "--version"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
        timeout=30,
    ).stdout.strip()
    argv = [
        crabbox_bin,
        "run",
        "--provider",
        "local-container",
        "--class",
        "standard",
        "--ttl",
        args.ttl,
        "--idle-timeout",
        args.idle_timeout,
        "--stop-after",
        "always",
        "--timing-json",
        "--label",
        "overkill-qvg-managed-container-proof",
        "--shell",
        "--",
        command,
    ]
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
        check=False,
        timeout=args.timeout_seconds,
    )
    timing = parse_timing_json(completed.stdout, completed.stderr)
    active_leases_after, lease_list_output = active_local_container_leases(crabbox_bin, env)
    return build_result(
        crabbox_version=version,
        command=command,
        completed=completed,
        timing=timing,
        active_leases_after=active_leases_after,
        lease_list_output=lease_list_output,
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--crabbox-bin")
    parser.add_argument("--command")
    parser.add_argument("--ttl", default="20m")
    parser.add_argument("--idle-timeout", default="5m")
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--no-clean-previous", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    result = run_proof(args)
    if not args.no_write:
        write_json(args.out, result)
        write_markdown(args.md_out, result)
        print(f"Wrote {repo_ref(args.out)}")
        print(f"Wrote {repo_ref(args.md_out)}")
    print(result["result"])
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
