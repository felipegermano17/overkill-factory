#!/usr/bin/env python3
"""Validate the public Hermes v0.16 Kanban transition-gate patch."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "adapters" / "hermes" / "patches" / "0002-add-overkill-vfinal-kanban-transition-hook.patch"
WORKER_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0003-materialize-overkill-vfinal-worker-subtasks.patch"
WORKER_RESULT_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0005-ingest-overkill-worker-results-from-subtasks.patch"
WORKER_DEPENDENCY_PATCH = ROOT / "adapters" / "hermes" / "patches" / "0006-fix-overkill-worker-subtask-dependency-direction.patch"
PATCHES = [PATCH, WORKER_PATCH, WORKER_RESULT_PATCH, WORKER_DEPENDENCY_PATCH]

REQUIRED_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "OverkillFactoryTransitionBlocked",
    "OVERKILL_FACTORY_KANBAN_GATE",
    "OVERKILL_FACTORY_ADAPTER_ROOT",
    "kanban_event_bridge.py",
    "overkill_factory_transition_gate",
    "overkill_factory_transition_blocked",
    "to_status=\"ready\"",
    "to_status=\"done\"",
    "from_status=\"created\"",
    "allowed direct ready creation",
    "allowed automatic ready recompute",
    "allowed unblock to ready",
    "def create_task(",
    "def recompute_ready(",
    "def unblock_task(",
    "def complete_task(",
    "def promote_task(",
]

REQUIRED_WORKER_PATCH_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "OVERKILL_FACTORY_CREATE_WORKER_TASKS",
    "OVERKILL_FACTORY_WORKER_TASK_STATUS",
    "record_type\": \"overkill_factory_worker_subtask",
    "overkill_worker_tasks_materialized",
    "materialized_worker_tasks",
    "_overkill_materialize_worker_tasks_in_txn",
    "allow_and_create_worker_tasks",
    "INSERT OR IGNORE INTO task_links",
    "worker-route parity is proven",
]

REQUIRED_WORKER_RESULT_PATCH_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "record_type\") != \"overkill_factory_worker_subtask",
    "_overkill_worker_results_dir",
    "_overkill_worker_result_from_completion",
    "_overkill_persist_worker_result_from_subtask",
    "overkill_worker_result",
    "overkill_worker_result_ingested",
    "Use this worker result during parent done reconciliation.",
    "worker-results",
]

REQUIRED_WORKER_DEPENDENCY_PATCH_MARKERS = [
    "diff --git a/hermes_cli/kanban_db.py b/hermes_cli/kanban_db.py",
    "Worker subtasks are prerequisites for the parent Factory card.",
    "Linking worker -> parent lets the dispatcher run the worker",
    "(worker_task_id, parent_task_id)",
    "Preserve worker -> parent on idempotent updates too.",
]

FORBIDDEN_MARKERS = [
    "_tmp_hermes",
    "C:" + "\\" + "Users",
    "One" + "Drive",
    "fe" + "lip",
    "hermes-" + "ka" + "xis" + "-vm",
    "zap--" + "advogado",
]


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return path.name


def _run(command: list[str], cwd: Path) -> tuple[str, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )
    status = "PASS" if completed.returncode == 0 else "FAIL"
    detail = completed.stdout.strip() or completed.stderr.strip()
    return status, detail


def static_validation() -> dict:
    patch_requirements = [
        (PATCH, REQUIRED_MARKERS),
        (WORKER_PATCH, REQUIRED_WORKER_PATCH_MARKERS),
        (WORKER_RESULT_PATCH, REQUIRED_WORKER_RESULT_PATCH_MARKERS),
        (WORKER_DEPENDENCY_PATCH, REQUIRED_WORKER_DEPENDENCY_PATCH_MARKERS),
    ]
    missing = []
    forbidden = []
    checked_patches = []
    for patch, markers in patch_requirements:
        checked_patches.append(_repo_relative(patch))
        if not patch.exists():
            missing.append(f"missing file: {_repo_relative(patch)}")
            continue
        text = patch.read_text(encoding="utf-8", errors="replace")
        missing.extend(f"{_repo_relative(patch)}: {marker}" for marker in markers if marker not in text)
        forbidden.extend(f"{_repo_relative(patch)}: {marker}" for marker in FORBIDDEN_MARKERS if marker in text)
    return {
        "result": "PASS" if not missing and not forbidden else "FAIL",
        "checked_patches": checked_patches,
        "missing_markers": missing,
        "forbidden_markers": forbidden,
    }


def resolve_source_kanban_db(source: Path) -> Path:
    source = source.expanduser().resolve()
    if source.is_dir():
        source = source / "hermes_cli" / "kanban_db.py"
    if not source.exists() or not source.is_file():
        raise FileNotFoundError("source kanban_db.py was not found")
    return source


def apply_validation(source_kanban_db: Path) -> dict:
    source = resolve_source_kanban_db(source_kanban_db)
    with tempfile.TemporaryDirectory(prefix="overkill-hermes-v016-patch-") as tmp:
        tmp_path = Path(tmp)
        package_dir = tmp_path / "hermes_cli"
        package_dir.mkdir(parents=True, exist_ok=True)
        target = package_dir / "kanban_db.py"
        shutil.copy2(source, target)

        patch_steps = []
        aggregate_check = "PASS"
        aggregate_apply = "PASS"
        for patch in PATCHES:
            check_status, check_detail = _run(["git", "apply", "--check", str(patch.resolve())], tmp_path)
            patch_step = {
                "patch": _repo_relative(patch),
                "git_apply_check": check_status,
                "git_apply_check_detail": check_detail,
                "git_apply": "SKIPPED",
                "git_apply_detail": "",
            }
            if check_status != "PASS":
                aggregate_check = "FAIL"
                patch_steps.append(patch_step)
                return {
                    "result": "FAIL",
                    "source": "redacted-kanban-db.py",
                    "git_apply_check": aggregate_check,
                    "git_apply_check_detail": check_detail,
                    "git_apply": "SKIPPED",
                    "py_compile": "SKIPPED",
                    "patch_steps": patch_steps,
                }

            apply_status, apply_detail = _run(["git", "apply", str(patch.resolve())], tmp_path)
            patch_step["git_apply"] = apply_status
            patch_step["git_apply_detail"] = apply_detail
            patch_steps.append(patch_step)
            if apply_status != "PASS":
                aggregate_apply = "FAIL"
                break

        compile_status = "SKIPPED"
        compile_detail = ""
        if aggregate_apply == "PASS":
            compile_status, compile_detail = _run(
                [sys.executable, "-m", "py_compile", str(target)],
                tmp_path,
            )

        return {
            "result": "PASS" if aggregate_apply == "PASS" and compile_status == "PASS" else "FAIL",
            "source": "redacted-kanban-db.py",
            "git_apply_check": aggregate_check,
            "git_apply_check_detail": "",
            "git_apply": aggregate_apply,
            "git_apply_detail": "",
            "patch_steps": patch_steps,
            "py_compile": compile_status,
            "py_compile_detail": compile_detail,
        }


def build_receipt(source_kanban_db: Path | None) -> dict:
    static = static_validation()
    apply_result = {"result": "SKIPPED"}
    if source_kanban_db is not None:
        try:
            apply_result = apply_validation(source_kanban_db)
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            apply_result = {"result": "FAIL", "error": str(exc)}

    result = "PASS" if static["result"] == "PASS" and apply_result["result"] in {"PASS", "SKIPPED"} else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-v016-transition-patch-validation.schema.json",
        "schema": "overkill_factory_hermes_v016_transition_patch_validation.v1",
        "patch": _repo_relative(PATCH),
        "patches": [_repo_relative(patch) for patch in PATCHES],
        "result": result,
        "static_validation": static,
        "apply_validation": apply_result,
        "remaining_runtime_scope": [
            "This validates the candidate patch artifact only.",
            "A production decision still requires a disposable installed-Hermes smoke through real Kanban state.",
            "Dashboard/API ready-route, worker-result ingestion and stubbed worker dispatch have separate disposable proofs; real profile/model execution, wider route parity and rollback still need proof before production use.",
            "The patch now covers direct ready creation, automatic ready recompute, manual promote, unblock-to-ready and done transitions.",
            "The worker-subtask patch materializes ledger rows as real blocked Hermes tasks only when explicitly enabled.",
            "The worker-result patch ingests completed worker subtasks into parent worker-result artifacts for done reconciliation.",
            "The worker-dependency patch links worker subtasks as prerequisites of the parent Factory card, so workers can dispatch before the parent closes.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-kanban-db",
        type=Path,
        help="Path to a clean Hermes v0.16 kanban_db.py file or Hermes checkout.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional public-safe JSON receipt path.",
    )
    args = parser.parse_args(argv)

    receipt = build_receipt(args.source_kanban_db)
    if args.out:
        out = args.out
        if not out.is_absolute():
            out = ROOT / out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
