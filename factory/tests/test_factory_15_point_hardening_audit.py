from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "factory_15_point_hardening_audit.py"
TEMPLATE_PATH = ROOT / "templates" / "factory-15-point-hardening-program.json"


def load_module():
    spec = importlib.util.spec_from_file_location("factory_15_point_hardening_audit", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_template() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def test_template_is_complete_scope_lock_and_all_points_done() -> None:
    module = load_module()
    result = module.audit_program(load_template())

    assert result["result"] == "PASS_COMPLETE"
    assert result["point_count"] == 15
    assert result["incomplete_point_ids"] == []
    assert not result["errors"]


def test_missing_point_fails_loud() -> None:
    module = load_module()
    program = load_template()
    program["points"] = program["points"][:-1]

    result = module.audit_program(program)

    assert result["result"] == "FAIL"
    assert any("exactly 15" in error for error in result["errors"])


def test_complete_status_is_rejected_until_every_point_is_complete() -> None:
    module = load_module()
    program = load_template()
    program["points"][0].pop("implementation_status", None)

    result = module.audit_program(program)

    assert result["result"] == "FAIL"
    assert any("cannot be complete" in error for error in result["errors"])


def test_require_complete_fails_until_each_point_has_complete_status() -> None:
    module = load_module()
    program = load_template()
    program["status"] = "active"
    program["points"][0]["implementation_status"] = "partial"

    result = module.audit_program(program, require_complete=True)

    assert result["result"] == "FAIL"
    assert any("require-complete failed" in error for error in result["errors"])


def test_complete_program_passes_when_all_points_are_marked_complete() -> None:
    module = load_module()
    program = load_template()
    program["status"] = "complete"
    for point in program["points"]:
        point["implementation_status"] = "complete"

    result = module.audit_program(program, require_complete=True)

    assert result["result"] == "PASS_COMPLETE"
    assert result["incomplete_point_ids"] == []
    assert result["errors"] == []


def test_point_order_is_enforced() -> None:
    module = load_module()
    program = load_template()
    program["points"] = copy.deepcopy(program["points"])
    program["points"][0], program["points"][1] = program["points"][1], program["points"][0]

    result = module.audit_program(program)

    assert result["result"] == "FAIL"
    assert any("ordered exactly" in error for error in result["errors"])
