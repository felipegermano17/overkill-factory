#!/usr/bin/env python3
"""Check that the public Hermes adapter package still carries core contracts."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "adapters" / "hermes" / "patches" / "0001-add-overkill-factory-10-kanban-gates.patch"
FACTORYCTL = ROOT / "scripts" / "factoryctl.py"
TRANSITION_HOOK = ROOT / "adapters" / "hermes" / "transition_hook.py"

REQUIRED_PATCH_MARKERS = [
    "_overkill_is_v35_card",
    "_overkill_validate_v35_card",
    "_overkill_validate_v35_completion",
    "OVERKILL_V3_5_FACTORY_10",
    "receipt_five",
    "kanban_transition_event",
    "security_scan_packet",
    "security_scan_result",
]

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


def main() -> int:
    failures = []
    failures.extend(f"patch missing marker: {m}" for m in missing_markers(PATCH, REQUIRED_PATCH_MARKERS))
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
