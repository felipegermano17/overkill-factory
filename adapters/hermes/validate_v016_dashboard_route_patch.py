#!/usr/bin/env python3
"""Validate the public Hermes v0.16 dashboard/API ready-route patch."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PATCH = ROOT / "adapters" / "hermes" / "patches" / "0004-guard-overkill-vfinal-dashboard-ready-route.patch"

REQUIRED_MARKERS = [
    "diff --git a/plugins/kanban/dashboard/plugin_api.py b/plugins/kanban/dashboard/plugin_api.py",
    "def _is_overkill_factory_card(",
    "def _set_ready_status(",
    "kanban_db.promote_task(",
    "actor=\"dashboard\"",
    "actor=\"dashboard-bulk\"",
    "ready_error",
    "Overkill Factory cards cannot move directly to 'ready'",
    "use a gated promote/unblock path",
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
    missing = []
    forbidden = []
    if not PATCH.exists():
        missing.append(f"missing file: {_repo_relative(PATCH)}")
    else:
        text = PATCH.read_text(encoding="utf-8", errors="replace")
        missing.extend(marker for marker in REQUIRED_MARKERS if marker not in text)
        forbidden.extend(marker for marker in FORBIDDEN_MARKERS if marker in text)
    return {
        "result": "PASS" if not missing and not forbidden else "FAIL",
        "checked_patch": _repo_relative(PATCH),
        "missing_markers": missing,
        "forbidden_markers": forbidden,
    }


def resolve_source_plugin_api(source: Path) -> Path:
    source = source.expanduser().resolve()
    if source.is_dir():
        source = source / "plugins" / "kanban" / "dashboard" / "plugin_api.py"
    if not source.exists() or not source.is_file():
        raise FileNotFoundError("source plugin_api.py was not found")
    return source


def apply_validation(source_plugin_api: Path) -> dict:
    source = resolve_source_plugin_api(source_plugin_api)
    with tempfile.TemporaryDirectory(prefix="overkill-hermes-v016-dashboard-patch-") as tmp:
        tmp_path = Path(tmp)
        package_dir = tmp_path / "plugins" / "kanban" / "dashboard"
        package_dir.mkdir(parents=True, exist_ok=True)
        target = package_dir / "plugin_api.py"
        shutil.copy2(source, target)

        check_status, check_detail = _run(["git", "apply", "--check", str(PATCH.resolve())], tmp_path)
        apply_status = "SKIPPED"
        apply_detail = ""
        compile_status = "SKIPPED"
        compile_detail = ""
        if check_status == "PASS":
            apply_status, apply_detail = _run(["git", "apply", str(PATCH.resolve())], tmp_path)
            if apply_status == "PASS":
                compile_status, compile_detail = _run(
                    [sys.executable, "-m", "py_compile", str(target)],
                    tmp_path,
                )

        return {
            "result": "PASS" if check_status == "PASS" and apply_status == "PASS" and compile_status == "PASS" else "FAIL",
            "source": "redacted-plugin-api.py",
            "git_apply_check": check_status,
            "git_apply_check_detail": check_detail,
            "git_apply": apply_status,
            "git_apply_detail": apply_detail,
            "py_compile": compile_status,
            "py_compile_detail": compile_detail,
        }


def build_receipt(source_plugin_api: Path | None) -> dict:
    static = static_validation()
    apply_result = {"result": "SKIPPED"}
    if source_plugin_api is not None:
        try:
            apply_result = apply_validation(source_plugin_api)
        except Exception as exc:  # pragma: no cover - defensive CLI boundary
            apply_result = {"result": "FAIL", "error": str(exc)}

    result = "PASS" if static["result"] == "PASS" and apply_result["result"] in {"PASS", "SKIPPED"} else "FAIL"
    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-v016-dashboard-route-patch-validation.schema.json",
        "schema": "overkill_factory_hermes_v016_dashboard_route_patch_validation.v1",
        "patch": _repo_relative(PATCH),
        "result": result,
        "static_validation": static,
        "apply_validation": apply_result,
        "scope": [
            "This validates the dashboard/API ready-route patch artifact.",
            "The patch is intended to be applied after the vFinal kanban_db patches that provide promote_task and the Overkill transition gate.",
            "A production decision still requires disposable installed-Hermes smoke evidence before any real runtime update.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-plugin-api",
        type=Path,
        help="Path to a clean Hermes v0.16 plugin_api.py file or Hermes checkout.",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional public-safe JSON receipt path.",
    )
    args = parser.parse_args(argv)

    receipt = build_receipt(args.source_plugin_api)
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
