#!/usr/bin/env python3
"""Small public smoke for a fresh Overkill Factory checkout."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any


CODE_ROOT = Path(__file__).resolve().parents[1]
FACTORYCTL_PATH = CODE_ROOT / "scripts" / "factoryctl.py"


def default_work_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "examples" / "minimal-hermes-project" / "card.md").exists():
        return cwd
    return CODE_ROOT


WORK_ROOT = default_work_root()
DEFAULT_CARD = WORK_ROOT / "examples" / "minimal-hermes-project" / "card.md"
DEFAULT_OUT = WORK_ROOT / ".tmp" / "quickstart-result.json"
DEFAULT_PACKETS_OUT = WORK_ROOT / ".tmp" / "minimal-worker-packets"


def load_factoryctl() -> Any:
    spec = importlib.util.spec_from_file_location("overkill_factoryctl", FACTORYCTL_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load factoryctl from {FACTORYCTL_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["overkill_factoryctl"] = module
    spec.loader.exec_module(module)
    return module


def repo_ref(path: Path) -> str:
    for root in (WORK_ROOT, CODE_ROOT):
        try:
            return path.resolve().relative_to(root).as_posix()
        except (OSError, ValueError):
            continue
    return f"external:{path.name or 'artifact'}"


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def build_result(card_path: Path, packets_out: Path) -> dict[str, Any]:
    factoryctl = load_factoryctl()
    card = factoryctl.load_json_like(card_path)
    validation_errors = factoryctl.validate_card(card)
    gate_report = factoryctl.build_gate_report(card)
    required_workers = list(gate_report.get("required_workers", []))

    packets_out.mkdir(parents=True, exist_ok=True)
    packet_paths: list[str] = []
    for worker_id in required_workers:
        packet = factoryctl.build_worker_packet(worker_id, card, card_path)
        packet_path = packets_out / f"{worker_id}.json"
        write_json(packet_path, packet)
        packet_paths.append(repo_ref(packet_path))

    checks = [
        {
            "id": "card_contract",
            "result": "PASS" if not validation_errors else "FAIL",
            "details": validation_errors,
        },
        {
            "id": "gate_report",
            "result": "PASS" if gate_report.get("gate_status") == "ready_for_worker_execution" else "FAIL",
            "details": [str(gate_report.get("gate_status"))],
        },
        {
            "id": "worker_packets",
            "result": "PASS" if packet_paths else "FAIL",
            "details": packet_paths,
        },
    ]
    result = "PASS" if all(check["result"] == "PASS" for check in checks) else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/quickstart-smoke-result.schema.json",
        "result_type": "quickstart_smoke_result",
        "created_at": factoryctl.utc_now(),
        "result": result,
        "card": repo_ref(card_path),
        "gate_status": gate_report.get("gate_status"),
        "required_workers": required_workers,
        "worker_packet_count": len(packet_paths),
        "worker_packet_dir": repo_ref(packets_out),
        "checks": checks,
        "next_step": "Connect these packets to Hermes only after reviewing the required workers and authority limits.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Overkill Factory public quickstart smoke.")
    parser.add_argument("--card", type=Path, default=DEFAULT_CARD)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--packets-out", type=Path, default=DEFAULT_PACKETS_OUT)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = build_result(args.card, args.packets_out)
    write_json(args.out, result)
    print(f"{result['result']}: wrote {repo_ref(args.out)}")
    return 0 if result["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
