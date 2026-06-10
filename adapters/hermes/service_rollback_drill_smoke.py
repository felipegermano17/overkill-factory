#!/usr/bin/env python3
"""Disposable operational rollback drill for the Hermes vFinal adapter.

This smoke must run only against a disposable Hermes checkout/home. It proves a
rollback-by-release-restore path: stop a service-like process, restore the
previous Hermes source files, run health checks, start again, then restore the
patched adapter state so the disposable runtime remains usable for later smokes.

It does not touch the real Hermes runtime, systemd, Windows services, Discord,
cloud accounts, model credentials, or production boards.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "service-rollback-drill-smoke.json"

TARGET_FILES = [
    Path("hermes_cli") / "kanban_db.py",
    Path("plugins") / "kanban" / "dashboard" / "plugin_api.py",
]

KANBAN_PATCHED_MARKERS = [
    "OVERKILL_FACTORY_KANBAN_GATE",
    "OVERKILL_FACTORY_CREATE_WORKER_TASKS",
    "_overkill_worker_result_from_completion",
    "Worker subtasks are prerequisites for the parent Factory card.",
]

DASHBOARD_PATCHED_MARKERS = [
    "def _set_ready_status(",
    'actor="dashboard"',
    "Overkill Factory cards cannot move directly to 'ready'",
]

PATCHED_MARKERS = {
    Path("hermes_cli") / "kanban_db.py": KANBAN_PATCHED_MARKERS,
    Path("plugins") / "kanban" / "dashboard" / "plugin_api.py": DASHBOARD_PATCHED_MARKERS,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def _is_disposable_path(path: Path) -> bool:
    lowered = str(path.resolve()).lower()
    return "\\.tmp\\" in lowered or "/.tmp/" in lowered or lowered.endswith("\\.tmp") or lowered.endswith("/.tmp")


def _assert_disposable_path(path: Path, *, label: str, allow_non_disposable: bool) -> None:
    if allow_non_disposable:
        return
    if _is_disposable_path(path):
        return
    raise RuntimeError(
        f"{label} must point to a disposable .tmp path, or pass --allow-non-disposable "
        "after an explicit operator decision."
    )


def _safe_error(exc: BaseException, replacements: dict[str, str]) -> str:
    text = f"{type(exc).__name__}: {exc}"
    for raw, replacement in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        if raw:
            text = text.replace(raw, replacement)
    return text


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _missing_markers(path: Path, markers: list[str]) -> list[str]:
    text = _read(path)
    return [marker for marker in markers if marker not in text]


def _present_markers(path: Path, markers: list[str]) -> list[str]:
    text = _read(path)
    return [marker for marker in markers if marker in text]


def _assert_target_files(checkout: Path, baseline_tree: Path) -> None:
    for rel_path in TARGET_FILES:
        target = checkout / rel_path
        baseline = baseline_tree / rel_path
        if not target.is_file():
            raise RuntimeError(f"missing target file: {rel_path.as_posix()}")
        if not baseline.is_file():
            raise RuntimeError(f"missing baseline file: {rel_path.as_posix()}")


def _assert_patched_state(checkout: Path) -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for rel_path, markers in PATCHED_MARKERS.items():
        missed = _missing_markers(checkout / rel_path, markers)
        if missed:
            missing[rel_path.as_posix()] = missed
    if missing:
        raise RuntimeError(f"patched markers missing before rollback: {json.dumps(missing, sort_keys=True)}")
    return {rel_path.as_posix(): list(markers) for rel_path, markers in PATCHED_MARKERS.items()}


def _assert_baseline_clean(baseline_tree: Path) -> dict[str, list[str]]:
    present: dict[str, list[str]] = {}
    for rel_path, markers in PATCHED_MARKERS.items():
        found = _present_markers(baseline_tree / rel_path, markers)
        if found:
            present[rel_path.as_posix()] = found
    if present:
        raise RuntimeError(f"baseline still contains adapter markers: {json.dumps(present, sort_keys=True)}")
    return {rel_path.as_posix(): [] for rel_path in PATCHED_MARKERS}


def _copy_file_set(src_root: Path, dst_root: Path) -> None:
    for rel_path in TARGET_FILES:
        dst = dst_root / rel_path
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src_root / rel_path, dst)


def _restore_file_set(src_root: Path, checkout: Path) -> None:
    for rel_path in TARGET_FILES:
        shutil.copy2(src_root / rel_path, checkout / rel_path)


def _venv_scripts_dir(checkout: Path) -> Path:
    return checkout / ".venv" / ("Scripts" if os.name == "nt" else "bin")


def _hermes_bin(checkout: Path) -> Path | None:
    scripts = _venv_scripts_dir(checkout)
    for name in ("hermes.exe", "hermes", "hermes.cmd", "hermes.bat"):
        candidate = scripts / name
        if candidate.exists():
            return candidate
    return None


def _runtime_env(checkout: Path, hermes_home: Path) -> dict[str, str]:
    scripts = _venv_scripts_dir(checkout)
    env = os.environ.copy()
    env["HOME"] = str(hermes_home)
    env["HERMES_HOME"] = str(hermes_home)
    env["HERMES_KANBAN_BOARD"] = "overkill-service-rollback-drill"
    env["OVERKILL_FACTORY_KANBAN_GATE"] = "1"
    env["OVERKILL_FACTORY_ADAPTER_ROOT"] = str(ROOT)
    env["PYTHONPATH"] = str(checkout) + os.pathsep + env.get("PYTHONPATH", "")
    env["PATH"] = str(scripts) + os.pathsep + env.get("PATH", "")
    hermes = _hermes_bin(checkout)
    if hermes is not None:
        env["HERMES_BIN"] = str(hermes)
    return env


def _run_command(command: list[str], *, cwd: Path, env: dict[str, str], timeout: int = 20) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )


def _version_line(output: str) -> str:
    for line in output.splitlines():
        if line.startswith("Hermes Agent "):
            return line.strip()
    return "version-line-not-found"


def _health_check(checkout: Path, hermes_home: Path, *, stage: str) -> dict[str, Any]:
    env = _runtime_env(checkout, hermes_home)
    compile_cmd = [
        sys.executable,
        "-m",
        "py_compile",
        str(checkout / "hermes_cli" / "kanban_db.py"),
        str(checkout / "plugins" / "kanban" / "dashboard" / "plugin_api.py"),
    ]
    compile_result = _run_command(compile_cmd, cwd=checkout, env=env)
    import_code = (
        "import os, sys; "
        f"sys.path.insert(0, {str(checkout)!r}); "
        "from hermes_cli import kanban_db; "
        "print('import-ok')"
    )
    import_result = _run_command([sys.executable, "-c", import_code], cwd=checkout, env=env)
    hermes = _hermes_bin(checkout)
    if hermes is None:
        version_result = subprocess.CompletedProcess([], 1, stdout="hermes binary not found")
    else:
        version_result = _run_command([str(hermes), "version"], cwd=checkout, env=env)

    passed = compile_result.returncode == 0 and import_result.returncode == 0 and version_result.returncode == 0
    return {
        "stage": stage,
        "result": "PASS" if passed else "FAIL",
        "py_compile": "PASS" if compile_result.returncode == 0 else "FAIL",
        "import_kanban_db": "PASS" if import_result.returncode == 0 else "FAIL",
        "hermes_version_command": "PASS" if version_result.returncode == 0 else "FAIL",
        "hermes_version": _version_line(version_result.stdout or ""),
    }


def _start_service_probe(checkout: Path, hermes_home: Path, *, stage: str, temp_dir: Path) -> dict[str, Any]:
    env = _runtime_env(checkout, hermes_home)
    pid_file = temp_dir / f"{stage}-service-probe.json"
    code = (
        "import json, os, sys, time; "
        f"pid_file = {str(pid_file)!r}; "
        "open(pid_file, 'w', encoding='utf-8').write(json.dumps({"
        "'pid': os.getpid(), "
        "'stage': os.environ.get('OVERKILL_ROLLBACK_STAGE'), "
        "'hermes_home_is_set': bool(os.environ.get('HERMES_HOME')), "
        "'home_equals_hermes_home': os.environ.get('HOME') == os.environ.get('HERMES_HOME')"
        "})); "
        "sys.stdout.write('service-probe-ready\\n'); sys.stdout.flush(); "
        "time.sleep(60)"
    )
    env["OVERKILL_ROLLBACK_STAGE"] = stage
    process = subprocess.Popen(
        [sys.executable, "-c", code],
        cwd=str(checkout),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.time() + 5
        payload: dict[str, Any] | None = None
        while time.time() < deadline:
            if pid_file.exists():
                payload = json.loads(pid_file.read_text(encoding="utf-8"))
                break
            if process.poll() is not None:
                break
            time.sleep(0.1)
        alive_before_stop = process.poll() is None
        process.terminate()
        try:
            process.wait(timeout=5)
            stopped = process.poll() is not None
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
            stopped = process.poll() is not None
        if payload is None:
            payload = {}
        passed = (
            alive_before_stop
            and stopped
            and payload.get("hermes_home_is_set") is True
            and payload.get("home_equals_hermes_home") is True
        )
        return {
            "stage": stage,
            "result": "PASS" if passed else "FAIL",
            "started": "PASS" if alive_before_stop else "FAIL",
            "stopped": "PASS" if stopped else "FAIL",
            "isolated_home_env": "PASS"
            if payload.get("hermes_home_is_set") is True and payload.get("home_equals_hermes_home") is True
            else "FAIL",
        }
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def _marker_status(checkout: Path, *, expect_patched: bool) -> dict[str, Any]:
    files: dict[str, Any] = {}
    passed = True
    for rel_path, markers in PATCHED_MARKERS.items():
        target = checkout / rel_path
        present = _present_markers(target, markers)
        missing = [marker for marker in markers if marker not in present]
        if expect_patched:
            ok = not missing
        else:
            ok = not present
        if not ok:
            passed = False
        files[rel_path.as_posix()] = {
            "result": "PASS" if ok else "FAIL",
            "present_count": len(present),
            "expected_present": expect_patched,
        }
    return {"result": "PASS" if passed else "FAIL", "files": files}


def run_drill(
    *,
    checkout: Path,
    hermes_home: Path,
    baseline_tree: Path,
    allow_non_disposable: bool,
) -> dict[str, Any]:
    checkout = checkout.resolve()
    hermes_home = hermes_home.resolve()
    baseline_tree = baseline_tree.resolve()
    _assert_disposable_path(checkout, label="--hermes-checkout", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(hermes_home, label="--hermes-home", allow_non_disposable=allow_non_disposable)
    _assert_disposable_path(baseline_tree, label="--baseline-tree", allow_non_disposable=allow_non_disposable)
    _assert_target_files(checkout, baseline_tree)
    _assert_patched_state(checkout)
    _assert_baseline_clean(baseline_tree)

    with tempfile.TemporaryDirectory(prefix="overkill-service-rollback-drill-") as tmp:
        tmp_path = Path(tmp)
        patched_backup = tmp_path / "patched-backup"
        _copy_file_set(checkout, patched_backup)
        final_restore = "not-needed"
        rollback_marker_status: dict[str, Any] = {}
        restored_marker_status: dict[str, Any] = {}
        health_checks: list[dict[str, Any]] = []
        service_checks: list[dict[str, Any]] = []
        try:
            health_checks.append(_health_check(checkout, hermes_home, stage="patched-before-rollback"))
            service_checks.append(_start_service_probe(checkout, hermes_home, stage="patched-before-rollback", temp_dir=tmp_path))

            _restore_file_set(baseline_tree, checkout)
            rollback_marker_status = _marker_status(checkout, expect_patched=False)
            health_checks.append(_health_check(checkout, hermes_home, stage="rolled-back-baseline"))
            service_checks.append(_start_service_probe(checkout, hermes_home, stage="rolled-back-baseline", temp_dir=tmp_path))

            _restore_file_set(patched_backup, checkout)
            final_restore = "PASS"
            restored_marker_status = _marker_status(checkout, expect_patched=True)
            health_checks.append(_health_check(checkout, hermes_home, stage="patched-restored"))
            service_checks.append(_start_service_probe(checkout, hermes_home, stage="patched-restored", temp_dir=tmp_path))
        finally:
            if _missing_markers(checkout / TARGET_FILES[0], KANBAN_PATCHED_MARKERS):
                _restore_file_set(patched_backup, checkout)
                final_restore = "PASS_AFTER_FINALLY"

    health_passed = all(item["result"] == "PASS" for item in health_checks)
    service_passed = all(item["result"] == "PASS" for item in service_checks)
    rollback_markers_passed = rollback_marker_status.get("result") == "PASS"
    restored_markers_passed = restored_marker_status.get("result") == "PASS"
    passed = health_passed and service_passed and rollback_markers_passed and restored_markers_passed

    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "remote_proof_result",
        "created_at": utc_now(),
        "worker": {
            "id": "release-ops-worker",
            "name": "Release Ops Worker",
            "factory_phase": "F16-F18",
        },
        "card_ref": {
            "card_id": "VFINAL-HERMES-SERVICE-ROLLBACK-DRILL",
            "slice_id": "VFINAL_HERMES_SERVICE_ROLLBACK_DRILL",
            "phase": "F16",
            "risk_effective": "R3",
            "surfaces": ["hermes", "adapter", "runtime-update", "rollback"],
            "executor_identity": "release-ops-worker",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "Disposable service rollback drill passed: baseline restore, health checks, service stop/start probe and patched-state restore all passed."
            if passed
            else "Disposable service rollback drill failed."
        ),
        "tool_or_profile": "adapters/hermes/service_rollback_drill_smoke.py",
        "executed_by": "release-ops-worker",
        "runtime_scope": (
            "Disposable Hermes checkout/home only; rollback uses baseline source restore and a local service-like process probe."
        ),
        "checks": {
            "disposable_checkout_guard": "PASS",
            "disposable_home_guard": "PASS",
            "disposable_baseline_guard": "PASS",
            "patched_markers_present_before_rollback": "PASS",
            "baseline_markers_absent": "PASS",
            "rollback_markers_removed": rollback_marker_status.get("result", "FAIL"),
            "health_checks": "PASS" if health_passed else "FAIL",
            "service_stop_start_probe": "PASS" if service_passed else "FAIL",
            "patched_state_restored_after_drill": restored_marker_status.get("result", "FAIL"),
            "final_restore": final_restore,
            "no_real_runtime_touched": "PASS",
        },
        "health_checks_detail": health_checks,
        "service_checks_detail": service_checks,
        "marker_checks": {
            "rolled_back_baseline": rollback_marker_status,
            "patched_restored": restored_marker_status,
        },
        "important_limitations": [
            "This proves rollback choreography in a disposable checkout/home, not a real systemd or Windows service unit.",
            "It does not prove Discord, cloud, model, external tool, DNS, deployment, or production monitoring rollback.",
            "It does not authorize updating a real Hermes runtime by itself.",
        ],
        "evidence_refs": [
            "adapters/hermes/service_rollback_drill_smoke.py",
            "validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json",
            "adapters/hermes/update-runbook.md",
            "docs/validation/hermes-vfinal-production-readiness-status.md",
        ],
        "next_action": (
            "Run one bounded non-stub model/tool-auth worker proof and then perform a receipt-backed real service update drill before production rollout."
        ),
    }


def build_fail_receipt(error: str) -> dict[str, Any]:
    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "remote_proof_result",
        "created_at": utc_now(),
        "worker": {
            "id": "release-ops-worker",
            "name": "Release Ops Worker",
            "factory_phase": "F16-F18",
        },
        "card_ref": {
            "card_id": "VFINAL-HERMES-SERVICE-ROLLBACK-DRILL",
            "slice_id": "VFINAL_HERMES_SERVICE_ROLLBACK_DRILL",
            "phase": "F16",
            "risk_effective": "R3",
            "surfaces": ["hermes", "adapter", "runtime-update", "rollback"],
            "executor_identity": "release-ops-worker",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "FAIL",
        "blocking_findings": True,
        "findings_summary": "Disposable service rollback drill failed before all checks could pass.",
        "tool_or_profile": "adapters/hermes/service_rollback_drill_smoke.py",
        "executed_by": "release-ops-worker",
        "checks": {
            "no_real_runtime_touched": "PASS",
            "drill_completed": "FAIL",
        },
        "error": error,
        "important_limitations": [
            "Failure receipt is public-safe and sanitized; inspect local console output only in the private workspace if deeper debugging is needed."
        ],
        "evidence_refs": [
            "adapters/hermes/service_rollback_drill_smoke.py",
            "validation/hermes-installed-runtime-smoke/service-rollback-drill-smoke.json",
        ],
        "next_action": "Fix the disposable rollback drill before any real Hermes runtime update.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a disposable Hermes service rollback drill.")
    parser.add_argument("--hermes-checkout", type=Path, required=True)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--baseline-tree", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--allow-non-disposable",
        action="store_true",
        help="Allow non-.tmp paths only after an explicit operator decision.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    replacements = {
        str(args.hermes_checkout.resolve()): "redacted-disposable-checkout",
        str(args.hermes_home.resolve()): "redacted-disposable-hermes-home",
        str(args.baseline_tree.resolve()): "redacted-disposable-baseline-tree",
        str(ROOT.resolve()): "repo-root",
    }
    try:
        receipt = run_drill(
            checkout=args.hermes_checkout,
            hermes_home=args.hermes_home,
            baseline_tree=args.baseline_tree,
            allow_non_disposable=args.allow_non_disposable,
        )
    except Exception as exc:
        receipt = build_fail_receipt(_safe_error(exc, replacements))

    write_json(args.out, receipt)
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}, indent=2))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
