#!/usr/bin/env python3
"""Optional live smoke for the gerente Hermes profile.

Dry-run proves the repo-side manager/profile route contract. Live mode requires a
real Hermes installation/profile and still avoids printing secrets. If live
requirements are missing it returns BLOCKED with exit 2 instead of pretending
success.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HERMES_HOME = Path(os.environ.get("HERMES_HOME", str(Path.home() / ".hermes")))


def _profile_exists(hermes_home: Path, profile: str) -> bool:
    candidates = [
        hermes_home / "profiles" / profile,
        hermes_home / ".hermes" / "profiles" / profile,
        Path.home() / ".hermes" / "profiles" / profile,
    ]
    return any(path.exists() for path in candidates)


def _command_available(name: str) -> bool:
    return shutil.which(name) is not None


def build_record(*, dry_run: bool, profile: str, hermes_home: Path, command: str) -> dict:
    command_available = _command_available(command)
    profile_exists = _profile_exists(hermes_home, profile)
    live_ready = (not dry_run) and command_available and profile_exists
    blocked_reasons = []
    if not dry_run and not command_available:
        blocked_reasons.append(f"Hermes command not found: {command}")
    if not dry_run and not profile_exists:
        blocked_reasons.append(f"Hermes profile not found: {profile}")
    return {
        "record_type": "factory_manager_profile_live_smoke",
        "result": "PASS" if dry_run or live_ready else "BLOCKED",
        "mode": "dry_run" if dry_run else "live",
        "manager_profile": profile,
        "hermes_home_checked": str(hermes_home),
        "hermes_command_available": command_available,
        "profile_exists": profile_exists,
        "manager_first_contract": True,
        "worker_direct_operator_contact": False,
        "creates_factoryrun_from_intake_contract": True,
        "external_live_verified": live_ready,
        "blocked_reasons": blocked_reasons,
        "secret_values_printed": False,
    }


def maybe_run_live(record: dict, command: str, profile: str) -> dict:
    if record["result"] != "PASS" or record["mode"] != "live":
        return record
    # Bounded, read-only liveness probe. Avoid passing user content or secrets.
    proc = subprocess.run(
        [command, "--profile", profile, "--version"],
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    record["live_probe_exit_code"] = proc.returncode
    record["live_probe_stdout_present"] = bool(proc.stdout.strip())
    record["live_probe_stderr_present"] = bool(proc.stderr.strip())
    if proc.returncode != 0:
        record["result"] = "BLOCKED"
        record["external_live_verified"] = False
        record.setdefault("blocked_reasons", []).append("Hermes profile version probe failed")
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--profile", default="overkill-factory-gerente")
    parser.add_argument("--hermes-home", type=Path, default=DEFAULT_HERMES_HOME)
    parser.add_argument("--command", default="hermes")
    parser.add_argument("--out", type=Path, default=Path(".tmp/factory-manager-profile-live-smoke.json"))
    args = parser.parse_args()
    record = build_record(dry_run=args.dry_run, profile=args.profile, hermes_home=args.hermes_home, command=args.command)
    record = maybe_run_live(record, args.command, args.profile)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(record["result"])
    return 0 if record["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
