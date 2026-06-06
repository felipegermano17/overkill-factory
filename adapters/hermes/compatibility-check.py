#!/usr/bin/env python3
"""Check that the public Hermes adapter package still carries core contracts."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCHES = [
    ROOT / "adapters" / "hermes" / "patches" / "0001-add-overkill-factory-10-kanban-gates.patch",
    ROOT / "adapters" / "hermes" / "patches" / "0002-enforce-overkill-ready-gate-in-dashboard-moves.patch",
    ROOT / "adapters" / "hermes" / "patches" / "0003-require-overkill-worker-results-before-done.patch",
]
FACTORYCTL = ROOT / "scripts" / "factoryctl.py"
TRANSITION_HOOK = ROOT / "adapters" / "hermes" / "transition_hook.py"

REQUIRED_PATCH_MARKERS = {
    "0001-add-overkill-factory-10-kanban-gates.patch": [
        "_overkill_is_v35_card",
        "_overkill_validate_v35_card",
        "_overkill_validate_v35_completion",
        "OVERKILL_V3_5_FACTORY_10",
        "receipt_five",
        "kanban_transition_event",
        "security_scan_packet",
        "security_scan_result",
    ],
    "0002-enforce-overkill-ready-gate-in-dashboard-moves.patch": [
        "_block_ready_task_on_overkill_gate_error",
        "_overkill_ready_gate_error",
        "dashboard ready move blocked by Overkill gate",
        "test_patch_ready_uses_overkill_gate_for_direct_dashboard_move",
        "test_patch_body_edit_rechecks_ready_overkill_card",
        "test_bulk_ready_uses_overkill_gate_for_direct_dashboard_move",
    ],
    "0003-require-overkill-worker-results-before-done.patch": [
        "_overkill_v35_validate_worker_result",
        "_overkill_v35_validate_auditor_result",
        "_overkill_v35_validate_product_face_result",
        "_overkill_v35_validate_human_gate_record",
        "auditor_result audit_mode must be code_audit for PASS",
        "product_face_result metadata is required",
        "test_patch_status_done_blocks_overkill_missing_product_face_result",
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


def main() -> int:
    failures = []
    for patch in PATCHES:
        markers = REQUIRED_PATCH_MARKERS.get(patch.name, [])
        failures.extend(
            f"{patch.name} missing marker: {m}"
            for m in missing_markers(patch, markers)
        )
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
