#!/usr/bin/env python3
"""Codex hook wrapper for the Overkill Factory bridge."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any


ROOT = Path(os.environ.get("PLUGIN_ROOT") or Path(__file__).resolve().parents[1])
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


def workspace_root(cwd: str | None) -> Path | None:
    if not cwd:
        return None
    current = Path(cwd).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / ".tmp").exists():
            return candidate
    return current


def default_inbox_dir(payload: dict[str, Any]) -> Path:
    env_inbox = os.environ.get("OVERKILL_FACTORY_INBOX")
    if env_inbox:
        return Path(env_inbox)
    root = workspace_root(payload.get("cwd"))
    if root is not None:
        return root / ".tmp" / "factory-runs" / "operator-inbox"
    plugin_data = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data) / "operator-inbox"
    return ROOT / ".tmp" / "factory-runs" / "operator-inbox"


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Overkill Factory bridge Codex hook.")
    parser.add_argument("--inbox-dir", type=Path)
    args = parser.parse_args()
    payload = read_payload()
    inbox_dir = args.inbox_dir or default_inbox_dir(payload)
    bridge = load_bridge()
    response = bridge.codex_hook_response(payload, inbox_dir=inbox_dir)
    print(json.dumps(response, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
