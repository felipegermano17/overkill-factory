"""Build a public-safe Hermes runtime proof from read-only Hermes evidence."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _status_count(tasks: list[Any], status: str) -> int:
    return sum(1 for task in tasks if isinstance(task, dict) and str(task.get("status") or "") == status)


def _running_profiles(profile_list_text: str) -> list[str]:
    running: list[str] = []
    for raw_line in profile_list_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line or " running " not in f" {line} ":
            continue
        parts = line.replace("◆", "").split()
        if parts:
            running.append(parts[0])
    return sorted(set(running))


def _profile_names(profile_list_text: str) -> list[str]:
    names: list[str] = []
    for raw_line in profile_list_text.splitlines():
        line = re.sub(r"\s+", " ", raw_line.strip())
        if not line or line.startswith("Profile ") or "gpt-" not in line:
            continue
        parts = line.replace("◆", "").split()
        if parts:
            names.append(parts[0])
    return sorted(set(names))


def _gateway_running(status_text: str) -> bool:
    return bool(re.search(r"Gateway Service\s+.*running", status_text, flags=re.I | re.S))


def _telegram_configured(status_text: str) -> bool:
    return bool(re.search(r"Telegram\s+.*configured", status_text, flags=re.I))


def _openai_codex_logged_in(status_text: str) -> bool:
    return bool(re.search(r"OpenAI Codex\s+.*logged in", status_text, flags=re.I | re.S))


def _current_board(boards: list[Any]) -> dict[str, Any]:
    for board in boards:
        if isinstance(board, dict) and board.get("is_current") is True:
            return board
    return {}


def _human_gate_block_detected(blocked_task_show: dict[str, Any] | None) -> bool:
    if not blocked_task_show:
        return False
    events = _list(blocked_task_show.get("events"))
    task = _dict(blocked_task_show.get("task"))
    if task.get("status") != "blocked":
        return False
    for event in events:
        if not isinstance(event, dict) or event.get("kind") != "blocked":
            continue
        payload = _dict(event.get("payload"))
        reason = str(payload.get("reason") or "").lower()
        if "human" in reason or "decision" in reason or "gate" in reason:
            return True
    return False


def _done_run_profiles(done_task_runs: list[Any]) -> list[str]:
    profiles: list[str] = []
    for run in done_task_runs:
        if not isinstance(run, dict):
            continue
        if str(run.get("status") or "") != "done":
            continue
        if str(run.get("outcome") or "") not in {"completed", "done", "success"}:
            continue
        profile = str(run.get("profile") or "").strip()
        if profile:
            profiles.append(profile)
    return sorted(set(profiles))


def build_hermes_runtime_proof(
    *,
    boards: list[Any],
    profile_list_text: str,
    status_text: str,
    task_list: list[Any],
    done_task_runs: list[Any],
    blocked_task_show: dict[str, Any] | None = None,
    created_at: str | None = None,
    environment_ref: str = "external:redacted-hermes-runtime",
) -> dict[str, Any]:
    current = _current_board(boards)
    profile_names = _profile_names(profile_list_text)
    running_profiles = _running_profiles(profile_list_text)
    run_profiles = _done_run_profiles(done_task_runs)
    blocked_human_gate = _human_gate_block_detected(blocked_task_show)

    runtime_summary = {
        "gateway_running": _gateway_running(status_text),
        "openai_codex_logged_in": _openai_codex_logged_in(status_text),
        "telegram_configured": _telegram_configured(status_text),
        "profile_count": len(profile_names),
        "running_profile_count": len(running_profiles),
        "manager_profile_running": "overkill-factory-gerente" in running_profiles,
        "current_board_detected": bool(current),
        "current_board_total_tasks": int(current.get("total") or len(task_list) or 0),
        "task_list_total": len(task_list),
        "done_task_count": _status_count(task_list, "done"),
        "blocked_task_count": _status_count(task_list, "blocked"),
        "representative_done_run_count": len(_list(done_task_runs)),
        "representative_done_run_profiles": run_profiles,
        "live_worker_orchestration_proven": bool(run_profiles),
        "human_gate_block_event_detected": blocked_human_gate,
    }
    operator_gate_boundary = {
        "human_gate_auto_approved": False,
        "human_gate_blocked_until_owner_decision": blocked_human_gate,
        "bridge_or_manager_executed_gate": False,
    }
    failures = []
    if not runtime_summary["gateway_running"]:
        failures.append("gateway is not running")
    if not runtime_summary["openai_codex_logged_in"]:
        failures.append("OpenAI Codex auth is not active")
    if not runtime_summary["telegram_configured"]:
        failures.append("Telegram is not configured")
    if not runtime_summary["manager_profile_running"]:
        failures.append("overkill-factory-gerente is not running")
    if runtime_summary["profile_count"] < 5:
        failures.append("profile layer is too small to prove worker routing")
    if not runtime_summary["current_board_detected"]:
        failures.append("no current Hermes board detected")
    if runtime_summary["current_board_total_tasks"] < 1:
        failures.append("current board has no tasks")
    if not runtime_summary["live_worker_orchestration_proven"]:
        failures.append("no representative done worker run found")
    if not runtime_summary["human_gate_block_event_detected"]:
        failures.append("no human-gate blocked event detected")
    if failures:
        raise ValueError("; ".join(failures))

    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-production-proof.schema.json",
        "record_type": "hermes_production_proof",
        "created_at": created_at or utc_now(),
        "proof_type": "non_stub_worker_execution",
        "result": "PASS",
        "summary": (
            "Read-only Hermes runtime proof: gateway, Codex auth, Telegram, manager profile, "
            "worker run completion and human-gate blocking were observed without publishing private runtime payloads."
        ),
        "scope": "current operator-owned Hermes runtime, redacted to counts and public-safe state flags",
        "environment_ref": environment_ref,
        "evidence_refs": [
            "external:redacted-hermes-status",
            "external:redacted-hermes-profile-list",
            "external:redacted-hermes-board-summary",
            "external:redacted-representative-worker-run",
            "external:redacted-human-gate-block-event",
        ],
        "runtime_summary": runtime_summary,
        "operator_gate_boundary": operator_gate_boundary,
        "limits": [
            "This proof is read-only and public-safe; it does not include raw board bodies, private paths or product source data.",
            "This proof demonstrates current Hermes runtime operability, not product-specific production completion.",
            "Human gates remain blocked until a real owner decision is recorded.",
        ],
        "decision": {
            "real_runtime_update": "not_applicable"
        },
    }


def validate_hermes_runtime_proof(proof: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "$schema",
        "record_type",
        "created_at",
        "proof_type",
        "result",
        "summary",
        "scope",
        "environment_ref",
        "evidence_refs",
        "runtime_summary",
        "operator_gate_boundary",
        "limits",
    ]
    for field in required:
        if field not in proof:
            errors.append(f"hermes_runtime_proof missing {field}")
    if proof.get("record_type") != "hermes_production_proof":
        errors.append("hermes_runtime_proof.record_type must be hermes_production_proof")
    if proof.get("proof_type") != "non_stub_worker_execution":
        errors.append("hermes_runtime_proof.proof_type must be non_stub_worker_execution")
    if proof.get("result") != "PASS":
        errors.append("hermes_runtime_proof.result must be PASS")
    summary = _dict(proof.get("runtime_summary"))
    required_true = [
        "gateway_running",
        "openai_codex_logged_in",
        "telegram_configured",
        "manager_profile_running",
        "current_board_detected",
        "live_worker_orchestration_proven",
        "human_gate_block_event_detected",
    ]
    for field in required_true:
        if summary.get(field) is not True:
            errors.append(f"hermes_runtime_proof.runtime_summary.{field} must be true")
    if int(summary.get("profile_count") or 0) < 5:
        errors.append("hermes_runtime_proof.runtime_summary.profile_count must be >= 5")
    if int(summary.get("current_board_total_tasks") or 0) < 1:
        errors.append("hermes_runtime_proof.runtime_summary.current_board_total_tasks must be >= 1")
    gate = _dict(proof.get("operator_gate_boundary"))
    if gate.get("human_gate_auto_approved") is not False:
        errors.append("hermes_runtime_proof must not auto-approve human gates")
    if gate.get("bridge_or_manager_executed_gate") is not False:
        errors.append("hermes_runtime_proof bridge/manager must not execute human gate")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a public-safe Hermes runtime proof from read-only evidence.")
    parser.add_argument("--boards-json", type=Path, required=True)
    parser.add_argument("--profile-list-text", type=Path, required=True)
    parser.add_argument("--status-text", type=Path, required=True)
    parser.add_argument("--task-list-json", type=Path, required=True)
    parser.add_argument("--done-task-runs-json", type=Path, required=True)
    parser.add_argument("--blocked-task-show-json", type=Path)
    parser.add_argument("--environment-ref", default="external:redacted-hermes-runtime")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    proof = build_hermes_runtime_proof(
        boards=load_json(args.boards_json),
        profile_list_text=load_text(args.profile_list_text),
        status_text=load_text(args.status_text),
        task_list=load_json(args.task_list_json),
        done_task_runs=load_json(args.done_task_runs_json),
        blocked_task_show=load_json(args.blocked_task_show_json) if args.blocked_task_show_json else None,
        environment_ref=args.environment_ref,
    )
    errors = validate_hermes_runtime_proof(proof)
    if errors:
        for error in errors:
            print(error)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(proof, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
