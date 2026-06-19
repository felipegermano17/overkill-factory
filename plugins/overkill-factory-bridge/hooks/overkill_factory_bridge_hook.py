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
INBOX_REL = Path(".tmp") / "factory-runs" / "operator-inbox"
MARKETPLACE_REL = Path(".agents") / "plugins" / "marketplace.json"
FACTORY_MARKETPLACE_NAME = "overkill-factory"


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


def has_operator_inbox(root: Path) -> bool:
    inbox = root / INBOX_REL
    return inbox.exists() or any((inbox / name).exists() for name in ("pending.jsonl", "events.jsonl", "acks.jsonl"))


def has_factory_marketplace(root: Path) -> bool:
    manifest = root / MARKETPLACE_REL
    if not manifest.exists():
        return False
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return data.get("name") == FACTORY_MARKETPLACE_NAME


def is_likely_factory_checkout(root: Path) -> bool:
    return (
        has_factory_marketplace(root)
        or (root / "scripts" / "factory_bridge.py").exists()
        or (root / "plugins" / "overkill-factory-bridge").exists()
    )


def nearby_factory_roots(root: Path) -> list[Path]:
    if not root.exists() or not root.is_dir():
        return []
    matches: list[Path] = []
    for child in root.iterdir():
        if not child.is_dir():
            continue
        if has_operator_inbox(child) and is_likely_factory_checkout(child):
            matches.append(child)
    return sorted(matches)


def workspace_root(cwd: str | None) -> Path | None:
    if not cwd:
        return None
    current = Path(cwd).resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists() or (candidate / ".tmp").exists():
            return candidate
    return current


def factory_root(cwd: str | None) -> Path | None:
    env_root = os.environ.get("OVERKILL_FACTORY_ROOT")
    if env_root:
        return Path(env_root).resolve()

    root = workspace_root(cwd)
    if root is None:
        return None

    if has_operator_inbox(root) or is_likely_factory_checkout(root):
        return root

    nearby = nearby_factory_roots(root)
    if len(nearby) == 1:
        return nearby[0]

    return root


def default_inbox_dir(payload: dict[str, Any]) -> Path:
    env_inbox = os.environ.get("OVERKILL_FACTORY_INBOX")
    if env_inbox:
        return Path(env_inbox)
    root = factory_root(payload.get("cwd"))
    if root is not None:
        return root / INBOX_REL
    plugin_data = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data) / "operator-inbox"
    return ROOT / INBOX_REL


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
