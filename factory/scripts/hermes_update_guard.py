#!/usr/bin/env python3
"""Public-safe Hermes update guard for Overkill Factory operators.

The guard does not update Hermes. It classifies pre/post-update evidence and
prints the command plan that keeps the real factory runtime from drifting while
Hermes changes underneath it.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


SCHEMA = "overkill_factory_hermes_update_guard.v1"
DEFAULT_HERMES_BIN = "hermes"
DEFAULT_HERMES_AGENT = "<hermes-agent-checkout>"
DEFAULT_ENV = 'export HOME="${HERMES_HOME:-$HOME}" HERMES_HOME="${HERMES_HOME:-$HOME}"'


def read_text(path: str | None) -> str:
    if not path:
        return ""
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8", errors="replace")


def status_count(stats_text: str, status: str) -> int:
    pattern = rf"^\s*{re.escape(status)}\s+(\d+)\s*$"
    match = re.search(pattern, stats_text, flags=re.MULTILINE)
    if not match:
        return 0
    return int(match.group(1))


def has_update_process(process_text: str) -> bool:
    if not process_text.strip():
        return False
    pattern = re.compile(r"\b(hermes\s+update|git\s+(pull|fetch|checkout|apply)|pip|uv)\b", re.IGNORECASE)
    for line in process_text.splitlines():
        lowered = line.lower()
        if "grep" in lowered or "hermes_update_guard" in lowered:
            continue
        if pattern.search(line):
            return True
    return False


def build_command_plan(
    *,
    board: str | None,
    hermes_bin: str = DEFAULT_HERMES_BIN,
    hermes_agent: str = DEFAULT_HERMES_AGENT,
) -> dict[str, list[str]]:
    board_commands: list[str] = [
        f"{DEFAULT_ENV}; {hermes_bin} kanban boards list",
    ]
    if board:
        board_commands.extend(
            [
                f"{DEFAULT_ENV}; {hermes_bin} kanban --board {board} stats",
                f"{DEFAULT_ENV}; {hermes_bin} kanban --board {board} list",
            ]
        )

    return {
        "pre_update_readonly": [
            f"{DEFAULT_ENV}; {hermes_bin} --version",
            f"cd {hermes_agent} && git status --short --branch && git rev-parse HEAD",
            f"{DEFAULT_ENV}; {hermes_bin} doctor",
            f"{DEFAULT_ENV}; {hermes_bin} gateway status",
            *board_commands,
            "ps -eo pid,ppid,etimes,cmd | grep -E 'hermes|git|pip|uv|python|update' | grep -v grep",
        ],
        "post_update_readonly": [
            f"{DEFAULT_ENV}; {hermes_bin} --version",
            f"cd {hermes_agent} && git status --short --branch && git rev-parse HEAD",
            f"{DEFAULT_ENV}; {hermes_bin} doctor",
            f"{DEFAULT_ENV}; {hermes_bin} gateway status",
            *board_commands,
        ],
        "operator_actions_when_clean": [
            "snapshot /etc/systemd/system/hermes-gateway.service and drop-ins before service changes",
            f"{DEFAULT_ENV}; {hermes_bin} doctor --fix  # only after config backup when doctor reports config migration",
            f"sudo {hermes_bin} gateway restart --system",
            f"{DEFAULT_ENV}; {hermes_bin} gateway status",
        ],
        "factory_validation": [
            "python adapters/hermes/compatibility-check.py",
            "python scripts/factoryctl.py doctor",
            "python scripts/quickstart_smoke.py",
            "python scripts/public_safety_scan.py",
            "python scripts/secret_safety_scan.py",
        ],
    }


def evaluate_snapshot(
    *,
    doctor_text: str = "",
    gateway_status_text: str = "",
    kanban_stats_text: str = "",
    process_text: str = "",
    sudo_check_text: str = "",
    board: str | None = None,
) -> dict[str, Any]:
    running_tasks = status_count(kanban_stats_text, "running")
    update_running = has_update_process(process_text)
    config_outdated = "Config version outdated" in doctor_text
    gateway_unit_outdated = "Installed gateway service definition is outdated" in gateway_status_text
    gateway_running = "System gateway service is running" in gateway_status_text or "active (running)" in gateway_status_text
    sudo_needs_password = "sudo-needs-password" in sudo_check_text or "password is required" in sudo_check_text

    blocking_items: list[str] = []
    attention_items: list[str] = []
    next_required_actions: list[str] = []

    if update_running:
        blocking_items.append("hermes_update_process_still_running")
        next_required_actions.append("wait for the Hermes update process to finish before restarting gateway or dispatching work")
    if running_tasks > 0:
        blocking_items.append("kanban_running_tasks_present")
        next_required_actions.append("do not restart the gateway until running Kanban tasks finish, are intentionally parked, or are recovered")
    if config_outdated:
        attention_items.append("hermes_config_version_outdated")
        next_required_actions.append("back up Hermes config, then run hermes doctor --fix before the final gateway restart")
    if gateway_unit_outdated:
        attention_items.append("gateway_service_definition_outdated")
        next_required_actions.append("snapshot systemd unit/drop-ins, then run sudo hermes gateway restart --system")
    if sudo_needs_password:
        attention_items.append("operator_sudo_required")
        next_required_actions.append("a human operator must run the sudo gateway restart command in an interactive terminal")
    if not gateway_running and gateway_status_text.strip():
        blocking_items.append("gateway_not_running")
        next_required_actions.append("restore the Hermes gateway service before allowing factory dispatch")

    if not next_required_actions:
        next_required_actions.append("no Hermes update guard action required; run the factory validation bundle")

    result = "BLOCKED" if blocking_items else "ATTENTION" if attention_items else "PASS"
    return {
        "schema": SCHEMA,
        "result": result,
        "checks": {
            "no_update_process_running": not update_running,
            "no_kanban_running_tasks": running_tasks == 0,
            "gateway_running": gateway_running or not gateway_status_text.strip(),
            "gateway_service_definition_current": not gateway_unit_outdated,
            "hermes_config_current": not config_outdated,
            "operator_sudo_available_noninteractive": not sudo_needs_password if sudo_check_text.strip() else None,
        },
        "counts": {"kanban_running_tasks": running_tasks},
        "blocking_items": blocking_items,
        "attention_items": attention_items,
        "next_required_actions": next_required_actions,
        "command_plan": build_command_plan(board=board),
    }


def print_plan(args: argparse.Namespace) -> int:
    payload = {
        "schema": SCHEMA,
        "mode": "plan",
        "command_plan": build_command_plan(board=args.board, hermes_bin=args.hermes_bin, hermes_agent=args.hermes_agent),
    }
    print(json.dumps(payload, indent=2))
    return 0


def evaluate(args: argparse.Namespace) -> int:
    payload = evaluate_snapshot(
        doctor_text=read_text(args.doctor),
        gateway_status_text=read_text(args.gateway_status),
        kanban_stats_text=read_text(args.kanban_stats),
        process_text=read_text(args.processes),
        sudo_check_text=read_text(args.sudo_check),
        board=args.board,
    )
    output = json.dumps(payload, indent=2)
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(output + "\n", encoding="utf-8")
    print(output)
    return 1 if payload["result"] == "BLOCKED" else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Classify Hermes update safety evidence.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    plan = subparsers.add_parser("plan", help="Print the public-safe Hermes update command plan.")
    plan.add_argument("--board", help="Hermes Kanban board slug to include in read-only checks.")
    plan.add_argument("--hermes-bin", default=DEFAULT_HERMES_BIN)
    plan.add_argument("--hermes-agent", default=DEFAULT_HERMES_AGENT)
    plan.set_defaults(func=print_plan)

    eval_parser = subparsers.add_parser("evaluate", help="Evaluate captured read-only Hermes evidence.")
    eval_parser.add_argument("--doctor", help="Path to captured `hermes doctor` output.")
    eval_parser.add_argument("--gateway-status", help="Path to captured `hermes gateway status` output.")
    eval_parser.add_argument("--kanban-stats", help="Path to captured `hermes kanban --board <board> stats` output.")
    eval_parser.add_argument("--processes", help="Path to captured process list output.")
    eval_parser.add_argument("--sudo-check", help="Path to captured sudo availability check output.")
    eval_parser.add_argument("--board", help="Hermes Kanban board slug used for the snapshot.")
    eval_parser.add_argument("--out", help="Optional JSON receipt path.")
    eval_parser.set_defaults(func=evaluate)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
