#!/usr/bin/env python3
"""Probe managed remote-proof readiness without exposing credentials."""

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
DEFAULT_OUT = ROOT / ".tmp" / "factory-runs" / "remote-proof" / "managed-remote-proof-probe.json"
DEFAULT_MD_OUT = ROOT / ".tmp" / "factory-runs" / "remote-proof" / "managed-remote-proof-probe.md"

SOURCE_REFS = [
    "https://github.com/openclaw/crabbox",
    "https://crabbox.sh/getting-started.html",
    "https://crabbox.sh/providers/blacksmith-testbox.html",
]

BROKER_ENV = [
    "CRABBOX_COORDINATOR",
    "CRABBOX_BROKER_URL",
    "CRABBOX_BROKER_TOKEN",
    "CRABBOX_PROVIDER",
]

BLACKSMITH_ENV = [
    "CRABBOX_BLACKSMITH_ORG",
    "CRABBOX_BLACKSMITH_WORKFLOW",
    "CRABBOX_BLACKSMITH_JOB",
    "CRABBOX_BLACKSMITH_REF",
]

SECRETISH_RE = re.compile(r"(?i)(token|secret|password|bearer|gho_[A-Za-z0-9_]+|[A-Za-z0-9+/]{32,}=*)")
URL_RE = re.compile(r"https?://[^\s\"']+")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_ref(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def redact(text: str) -> str:
    text = URL_RE.sub("<url-redacted>", text)
    return SECRETISH_RE.sub("<redacted>", text)


def run_probe_command(argv: list[str], timeout: int = 20) -> dict[str, Any]:
    binary = shutil.which(argv[0])
    if not binary:
        return {
            "command": argv[0],
            "available": False,
            "exit_code": None,
            "stdout_tail": "",
            "stderr_tail": "",
        }
    try:
        completed = subprocess.run(
            argv,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "command": argv[0],
            "available": True,
            "exit_code": None,
            "timed_out": True,
            "stdout_tail": redact((exc.stdout or "")[-500:]),
            "stderr_tail": redact((exc.stderr or "")[-500:]),
        }
    return {
        "command": " ".join(argv[:2]),
        "available": True,
        "exit_code": completed.returncode,
        "stdout_tail": redact(completed.stdout[-500:]),
        "stderr_tail": redact(completed.stderr[-500:]),
    }


def env_presence(names: list[str]) -> dict[str, bool]:
    return {name: bool(os.environ.get(name)) for name in names}


def crabbox_config_presence() -> dict[str, bool]:
    candidates = [
        Path.home() / ".config" / "crabbox" / "config.yaml",
        Path.home() / ".crabbox" / "config.yaml",
    ]
    present = [path for path in candidates if path.exists()]
    text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in present)
    return {
        "user_config_present": bool(present),
        "broker_url_present": "broker:" in text and "url:" in text,
        "broker_token_present": "token:" in text,
        "provider_present": "provider:" in text,
        "blacksmith_config_present": "blacksmith:" in text,
    }


def build_probe() -> dict[str, Any]:
    crabbox_version = run_probe_command(["crabbox", "--version"])
    crabbox_doctor = run_probe_command(["crabbox", "doctor"], timeout=30)
    blacksmith_version = run_probe_command(["blacksmith", "--version"])
    config = crabbox_config_presence()
    broker_env = env_presence(BROKER_ENV)
    blacksmith_env = env_presence(BLACKSMITH_ENV)

    broker_configured = config["broker_url_present"] or broker_env["CRABBOX_COORDINATOR"] or broker_env["CRABBOX_BROKER_URL"]
    broker_auth_hint = config["broker_token_present"] or broker_env["CRABBOX_BROKER_TOKEN"]
    provider_hint = config["provider_present"] or broker_env["CRABBOX_PROVIDER"]
    blacksmith_configured = (
        config["blacksmith_config_present"]
        or all(blacksmith_env[name] for name in ("CRABBOX_BLACKSMITH_ORG", "CRABBOX_BLACKSMITH_WORKFLOW", "CRABBOX_BLACKSMITH_JOB"))
    )

    managed_ready = bool(
        crabbox_version["available"]
        and (
            (broker_configured and broker_auth_hint and provider_hint)
            or (blacksmith_version["available"] and blacksmith_configured)
        )
    )
    missing = []
    if not crabbox_version["available"]:
        missing.append("crabbox CLI is not available on PATH")
    if not (broker_configured and broker_auth_hint and provider_hint):
        missing.append("Crabbox broker/provider credentials are not configured for aws/azure/gcp/hetzner")
    if not (blacksmith_version["available"] and blacksmith_configured):
        missing.append("Blacksmith Testbox CLI/config is not ready")

    result = "PASS" if managed_ready else "PENDING"
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
            "card_id": "MANAGED-REMOTE-PROOF-PROBE",
            "slice_id": "PUBLIC_FACTORY_MANAGED_REMOTE_PROOF",
            "phase": "F16",
            "risk_effective": "R3",
            "surfaces": ["remote-proof", "provider", "crabbox", "testbox", "public"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": result,
        "blocking_findings": not managed_ready,
        "findings_summary": (
            "Managed remote proof prerequisites are configured."
            if managed_ready
            else "Managed remote proof is not ready: " + "; ".join(missing)
        ),
        "tool_or_profile": "crabbox-managed-provider-probe",
        "executed_by": "remote-proof-runner",
        "evidence_refs": SOURCE_REFS,
        "evidence_kind": "real",
        "reusable_for_product": False,
        "next_action": (
            "Run a managed Crabbox broker or Blacksmith Testbox proof and emit a PASS remote_proof_result with cleanup evidence."
            if not managed_ready
            else "Run the actual managed remote proof command for the product target; this probe alone is not execution evidence."
        ),
        "managed_remote_proof_ready": managed_ready,
        "provider_capabilities_from_sources": {
            "brokered_cloud_providers": ["aws", "azure", "gcp", "hetzner"],
            "delegated_testbox_provider": "blacksmith-testbox",
            "static_ssh_is_not_managed": True,
        },
        "probe": {
            "crabbox_version": crabbox_version,
            "crabbox_doctor": crabbox_doctor,
            "blacksmith_version": blacksmith_version,
            "config_presence": config,
            "env_presence": {
                **broker_env,
                **blacksmith_env,
            },
        },
        "production_boundary": "This probe does not lease a managed runner, run product tests, collect provider cleanup evidence, or satisfy managed_remote_proof.",
        "required_for_completion": [
            "crabbox broker or blacksmith-testbox credentials",
            "provider-backed run handle",
            "remote command transcript",
            "artifact refs",
            "cleanup or stop evidence",
            "public-safe PASS remote_proof_result reusable only for the product target",
        ],
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: Path, probe: dict[str, Any]) -> None:
    lines = [
        "# Managed Remote Proof Probe",
        "",
        f"Result: `{probe['result']}`",
        f"Managed remote proof ready: `{str(probe['managed_remote_proof_ready']).lower()}`",
        f"Reusable for product approval: `{str(probe['reusable_for_product']).lower()}`",
        "",
        "## Findings",
        "",
        probe["findings_summary"],
        "",
        "## Required For Completion",
        "",
    ]
    for item in probe["required_for_completion"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Boundary", "", probe["production_boundary"], ""])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--md-out", type=Path, default=DEFAULT_MD_OUT)
    parser.add_argument("--no-write", action="store_true")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)

    probe = build_probe()
    if not args.no_write:
        write_json(args.out, probe)
        write_markdown(args.md_out, probe)
        print(f"Wrote {repo_ref(args.out)}")
        print(f"Wrote {repo_ref(args.md_out)}")
    print(probe["result"])
    if args.require_ready and not probe["managed_remote_proof_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
