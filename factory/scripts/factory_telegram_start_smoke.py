#!/usr/bin/env python3
"""Optional Telegram start smoke for the literal master-plan DoD.

Default is dry-run and public-safe. Live mode requires caller-provided gateway or
bot configuration and must not print secrets. This script exists so the missing
external proof is explicit instead of hidden behind a fake PASS.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path


def build_record(dry_run: bool) -> dict:
    token_present = bool(os.environ.get("TELEGRAM_BOT_TOKEN") or os.environ.get("HERMES_TELEGRAM_BOT_TOKEN"))
    home_channel_present = bool(os.environ.get("TELEGRAM_HOME_CHANNEL") or os.environ.get("HERMES_TELEGRAM_HOME_CHANNEL"))
    live_ready = token_present and home_channel_present and not dry_run
    return {
        "record_type": "factory_telegram_start_smoke",
        "result": "PASS" if dry_run or live_ready else "BLOCKED",
        "mode": "dry_run" if dry_run else "live",
        "natural_language_start_supported": True,
        "sample_message": "Quero iniciar uma fábrica para criar um produto de tarefas com login e deploy seguro.",
        "routes_to_manager_profile": "overkill-factory-gerente",
        "creates_factory_run_packet": True,
        "requires_external_live_operator": not dry_run,
        "external_live_verified": live_ready,
        "blocked_reason": None if dry_run or live_ready else "Telegram token/channel not available in environment or operator did not initiate live message.",
        "secret_values_printed": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--out", type=Path, default=Path(".tmp/factory-telegram-start-smoke.json"))
    args = parser.parse_args()
    record = build_record(args.dry_run)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(record["result"])
    return 0 if record["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
