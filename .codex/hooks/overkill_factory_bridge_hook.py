#!/usr/bin/env python3
"""Codex hook wrapper for the Overkill Factory bridge."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
BRIDGE_PATH = ROOT / "scripts" / "factory_bridge.py"


def load_bridge() -> Any:
    spec = importlib.util.spec_from_file_location("factory_bridge", BRIDGE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factory bridge from {BRIDGE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["factory_bridge"] = module
    spec.loader.exec_module(module)
    return module


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    return json.loads(raw)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Overkill Factory bridge Codex hook.")
    parser.add_argument("--inbox-dir", type=Path, default=ROOT / ".tmp" / "factory-runs" / "operator-inbox")
    args = parser.parse_args()
    bridge = load_bridge()
    response = bridge.codex_hook_response(read_payload(), inbox_dir=args.inbox_dir)
    print(json.dumps(response, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
