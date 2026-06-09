#!/usr/bin/env python3
"""Check that the public Hermes adapter package still carries core contracts."""

from __future__ import annotations

import sys
import os
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCHES = [
    ROOT / "adapters" / "hermes" / "patches" / "0001-overkill-factory-v35-gates-official-main.patch",
]
FACTORYCTL = ROOT / "scripts" / "factoryctl.py"
TRANSITION_HOOK = ROOT / "adapters" / "hermes" / "transition_hook.py"

REQUIRED_PATCH_MARKERS = {
    "0001-overkill-factory-v35-gates-official-main.patch": [
        "OVERKILL_FACTORY_VERSION",
        "OVERKILL_V3_5_FACTORY_10",
        "_overkill_ready_gate_error",
        "_overkill_completion_gate_error",
        "overkill_ready_gate_error",
        "completion_blocked_overkill_gate",
        "receipt_five",
        "kanban_transition_event",
        "product_face_packet",
        "product_face_result",
        "security_scan_packet",
        "security_scan_result",
        "auditor_result.audit_mode=code_audit",
        "human_gate_record",
        "cannot complete {tid}: {exc}",
        "HTTPException(status_code=409",
        "test_overkill_ready_gate_blocks_missing_product_face_packet",
        "test_overkill_dashboard_done_move_returns_409",
    ],
}

REQUIRED_FACTORYCTL_MARKERS = [
    "public-safety-gate",
    "autoreview-gate",
    "handoff-packer",
    "remote-proof-runner",
    "agentic-ai-security-specialist",
    "supply-chain-gate",
]

REQUIRED_TRANSITION_HOOK_MARKERS = [
    "overkill_factory_hermes_transition_hook",
    "persist_worker_tasks",
    "allow_and_create_worker_tasks",
    "block_transition",
    "worker-ledger",
    "completion_reconciliation",
]


def missing_markers(path: Path, markers: list[str]) -> list[str]:
    if not path.exists():
        return [f"missing file: {path}"]
    text = path.read_text(encoding="utf-8", errors="replace")
    return [marker for marker in markers if marker not in text]


def patch_syntax_failures() -> list[str]:
    failures = []
    for patch in PATCHES:
        if not patch.exists():
            continue
        result = subprocess.run(
            ["git", "apply", "--numstat", str(patch)],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            failures.append(
                f"{patch.name} is not parseable by git apply: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )
    return failures


def hermes_checkout_failures() -> list[str]:
    checkout = os.environ.get("OVERKILL_HERMES_CHECKOUT", "").strip()
    if not checkout:
        return []
    root = Path(checkout)
    failures = []
    if not root.exists():
        return [f"OVERKILL_HERMES_CHECKOUT does not exist: {root}"]
    for patch in PATCHES:
        result = subprocess.run(
            ["git", "apply", "--check", str(patch)],
            cwd=root,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            failures.append(
                f"{patch.name} does not apply to {root}: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )
    return failures


def main() -> int:
    failures = []
    for patch in PATCHES:
        markers = REQUIRED_PATCH_MARKERS.get(patch.name, [])
        failures.extend(
            f"{patch.name} missing marker: {m}"
            for m in missing_markers(patch, markers)
        )
    failures.extend(patch_syntax_failures())
    failures.extend(hermes_checkout_failures())
    failures.extend(f"factoryctl missing marker: {m}" for m in missing_markers(FACTORYCTL, REQUIRED_FACTORYCTL_MARKERS))
    failures.extend(f"transition hook missing marker: {m}" for m in missing_markers(TRANSITION_HOOK, REQUIRED_TRANSITION_HOOK_MARKERS))

    if failures:
        for failure in failures:
            print(failure, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
