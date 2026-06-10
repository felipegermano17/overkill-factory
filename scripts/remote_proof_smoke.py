#!/usr/bin/env python3
"""Run a clean local fallback proof and write a Remote Proof receipt."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import shlex
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def run_command(command: str, cwd: Path, timeout: int) -> dict[str, object]:
    argv = shlex.split(command)
    completed = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout_tail": redact_output(completed.stdout[-4000:]),
        "stderr_tail": redact_output(completed.stderr[-4000:]),
    }


def redact_output(text: str) -> str:
    redacted = text.replace(str(Path.home()), "<home>").replace(str(Path.home()).replace("\\", "\\\\"), "<home>")
    redacted = re.sub(r"<home>\\AppData\\Local\\Temp\\[^\s\\]+", "<temp>", redacted)
    redacted = re.sub(r"/tmp/[^\s/]+", "<temp>", redacted)
    return redacted


def copy_repo_subset(destination: Path) -> None:
    ignore = shutil.ignore_patterns(
        ".git",
        "__pycache__",
        "*.pyc",
        "remote-proof",
        ".pytest_cache",
    )
    for name in [
        "agents",
        "scripts",
        "tests",
        "schemas",
        "examples",
        "validation",
        "adapters",
        "pilots",
    ]:
        source = ROOT / name
        if source.exists():
            shutil.copytree(source, destination / name, ignore=ignore)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local clean-environment remote proof fallback.")
    parser.add_argument("--out", type=Path, default=ROOT / "validation" / "remote-proof" / "local-clean-smoke.json")
    parser.add_argument("--ttl-minutes", type=int, default=30)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument(
        "--command",
        action="append",
        default=[
            "python -m unittest discover -s tests -p \"test_*.py\" -q",
            "python adapters/hermes/compatibility-check.py",
            "python adapters/hermes/vfinal-smoke.py",
            "python scripts/validate_public_json_artifacts.py",
            "python scripts/secret_safety_scan.py",
            "python scripts/public_safety_scan.py",
        ],
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="overkill-remote-proof-") as tmp:
        work = Path(tmp) / "repo"
        work.mkdir()
        copy_repo_subset(work)
        results = [run_command(command, work, args.timeout_seconds) for command in args.command]
        passed = all(result["returncode"] == 0 for result in results)
        receipt = {
            "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
            "record_type": "remote_proof_result",
            "created_at": utc_now(),
            "worker": {
                "id": "remote-proof-runner",
                "name": "Remote Proof Runner",
                "factory_phase": "F13-F16",
            },
            "card_ref": {
                "card_id": "REMOTE-PROOF-SMOKE",
                "slice_id": "LOCAL_CLEAN_SMOKE",
                "phase": "F13",
                "risk_effective": "R2",
                "surfaces": ["code", "ci", "public", "remote-proof"],
                "executor_identity": "remote-proof-runner",
                "reviewer_identity": "independent-reviewer",
            },
            "result": "PASS" if passed else "FAIL",
            "blocking_findings": not passed,
            "findings_summary": (
                "Local clean-environment fallback proof passed."
                if passed
                else "Local clean-environment fallback proof failed."
            ),
            "tool_or_profile": "local-tempdir-clean-proof-fallback",
            "executed_by": "remote-proof-runner",
            "environment": {
                "provider": "local-tempdir",
                "secrets_allowed": False,
                "ttl_minutes": args.ttl_minutes,
                "cost_owner": "repo-maintainer",
                "cleanup": "temporary directory removed by context manager",
            },
            "commands": results,
            "evidence_refs": [repo_ref(args.out)],
            "next_action": "Use Crabbox/Testbox for provider-backed remote proof when available.",
        }
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
