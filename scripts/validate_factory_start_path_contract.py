#!/usr/bin/env python3
"""Validate that the public operator skill requires deterministic factory start."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "codex" / "overkill-factory" / "SKILL.md"


REQUIRED_PHRASES = [
    "Mandatory Factory Start",
    "factory_bridge_source_envelope",
    "factory_bridge_start_request",
    "project_mode=new_project",
    "materialize-bridge-start",
    "must not create a",
    "Hermes board or first phase card by hand",
    "Direct `hermes kanban boards create`, `hermes kanban create`, or",
    "factory_start_path=true",
    "phase graph/reconciler",
]


def main() -> int:
    text = SKILL.read_text(encoding="utf-8")
    missing = [phrase for phrase in REQUIRED_PHRASES if phrase not in text]
    if missing:
        print("Factory start path contract is incomplete:")
        for phrase in missing:
            print(f"- missing: {phrase}")
        return 1
    print("Factory start path contract OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
