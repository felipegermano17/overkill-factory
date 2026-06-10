#!/usr/bin/env python3
"""Inventory Hermes dashboard/API routes for vFinal parity planning.

This script reads a dashboard `plugin_api.py` file from a disposable Hermes
checkout, extracts FastAPI routes, classifies read-only versus mutating routes,
and marks which route families already have vFinal parity evidence.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "dashboard-route-inventory-smoke.json"

ROUTE_RE = re.compile(r"@router\.(get|post|patch|put|delete|websocket)\(\"([^\"]+)\"\)")
DEF_RE = re.compile(r"(?:async\s+)?def\s+([a-zA-Z0-9_]+)\(")
MUTATING_METHODS = {"post", "patch", "put", "delete"}

COVERED_ROUTE_FAMILIES = {
    ("post", "/tasks"): "covered_for_create_before_ready",
    ("post", "/tasks/{task_id}/attachments"): "covered_for_attachment_route_safety",
    ("delete", "/attachments/{attachment_id}"): "covered_for_attachment_route_safety",
    ("patch", "/tasks/{task_id}"): "covered_for_ready_and_done_status",
    ("post", "/tasks/bulk"): "covered_for_ready_done_and_archive_guard",
    ("post", "/dispatch"): "covered_for_dispatch_route_mechanics",
    ("delete", "/tasks/{task_id}"): "covered_for_delete_guard",
    ("post", "/links"): "covered_for_dependency_link_guard",
    ("delete", "/links"): "covered_for_dependency_link_guard",
    ("post", "/tasks/{task_id}/reassign"): "covered_for_reassign_route_guard",
    ("post", "/tasks/{task_id}/reclaim"): "covered_for_reclaim_terminate_guard",
    ("post", "/runs/{run_id}/terminate"): "covered_for_reclaim_terminate_guard",
    ("post", "/tasks/{task_id}/specify"): "covered_for_specify_route_guard",
    ("post", "/tasks/{task_id}/decompose"): "covered_for_decompose_route_guard",
    ("post", "/tasks/{task_id}/comments"): "covered_for_comments_append_only",
    ("post", "/tasks/{task_id}/home-subscribe/{platform}"): "covered_for_home_subscribe_visibility_only",
    ("delete", "/tasks/{task_id}/home-subscribe/{platform}"): "covered_for_home_subscribe_visibility_only",
    ("delete", "/boards/{slug}"): "covered_for_board_delete_guard",
    ("post", "/boards"): "covered_for_board_lifecycle_operational_safety",
    ("patch", "/boards/{slug}"): "covered_for_board_lifecycle_operational_safety",
    ("post", "/boards/{slug}/switch"): "covered_for_board_lifecycle_operational_safety",
    ("patch", "/profiles/{profile_name}"): "covered_for_profile_routes_operational_safety",
    ("post", "/profiles/{profile_name}/describe-auto"): "covered_for_profile_routes_operational_safety",
    ("put", "/orchestration"): "covered_for_orchestration_route_operational_safety",
}


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def extract_routes(source: str) -> list[dict[str, Any]]:
    lines = source.splitlines()
    routes: list[dict[str, Any]] = []
    for index, line in enumerate(lines):
        match = ROUTE_RE.search(line)
        if not match:
            continue
        method, path = match.groups()
        function = "unknown"
        for follow in lines[index + 1 : min(index + 8, len(lines))]:
            def_match = DEF_RE.search(follow)
            if def_match:
                function = def_match.group(1)
                break
        routes.append(
            {
                "method": method.upper(),
                "path": path,
                "function": function,
                "line": index + 1,
                "mutating": method in MUTATING_METHODS,
            }
        )
    return routes


def classify_route(route: dict[str, Any]) -> dict[str, Any]:
    method = str(route["method"]).lower()
    path = str(route["path"])
    family_key = (method, path)
    if family_key in COVERED_ROUTE_FAMILIES:
        parity_status = COVERED_ROUTE_FAMILIES[family_key]
        gate_relevance = "status_transition_gate"
    elif not route["mutating"]:
        parity_status = "not_required_read_only"
        gate_relevance = "read_only"
    elif path.startswith("/tasks") or path.startswith("/dispatch") or path.startswith("/runs"):
        parity_status = "pending_route_parity"
        gate_relevance = "can_affect_task_or_worker_state"
    elif path.startswith("/boards") or path.startswith("/profiles") or path.startswith("/orchestration"):
        parity_status = "pending_operational_safety"
        gate_relevance = "can_affect_runtime_configuration"
    else:
        parity_status = "pending_surface_review"
        gate_relevance = "mutating_dashboard_surface"

    classified = dict(route)
    classified["parity_status"] = parity_status
    classified["gate_relevance"] = gate_relevance
    return classified


def build_receipt(plugin_api: Path) -> dict[str, Any]:
    source = plugin_api.read_text(encoding="utf-8")
    routes = [classify_route(route) for route in extract_routes(source)]
    mutating = [route for route in routes if route["mutating"]]
    read_only = [route for route in routes if not route["mutating"]]
    pending = [route for route in mutating if str(route["parity_status"]).startswith("pending")]
    covered = [route for route in mutating if str(route["parity_status"]).startswith("covered")]

    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": "remote_proof_result",
        "created_at": utc_now(),
        "worker": {
            "id": "remote-proof-runner",
            "name": "Remote Proof Runner",
            "factory_phase": "F13-F16",
        },
        "card_ref": {
            "card_id": "VFINAL-HERMES-DASHBOARD-ROUTE-INVENTORY",
            "slice_id": "VFINAL_HERMES_DASHBOARD_ROUTE_PARITY",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "dashboard-api"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS",
        "blocking_findings": False,
        "findings_summary": (
            "Dashboard/API route inventory generated. Covered and pending mutating route families are listed explicitly."
        ),
        "tool_or_profile": "adapters/hermes/dashboard_route_inventory.py",
        "executed_by": "remote-proof-runner",
        "route_inventory": {
            "source_ref": repo_ref(plugin_api),
            "total_routes": len(routes),
            "read_only_routes": len(read_only),
            "mutating_routes": len(mutating),
            "covered_mutating_route_families": len(covered),
            "pending_mutating_route_families": len(pending),
            "routes": routes,
        },
        "coverage_summary": {
            "covered": [
                {
                    "method": route["method"],
                    "path": route["path"],
                    "function": route["function"],
                    "parity_status": route["parity_status"],
                }
                for route in covered
            ],
            "pending": [
                {
                    "method": route["method"],
                    "path": route["path"],
                    "function": route["function"],
                    "parity_status": route["parity_status"],
                    "gate_relevance": route["gate_relevance"],
                }
                for route in pending
            ],
        },
        "important_limitations": [
            "This is an inventory and classification receipt, not route execution proof.",
            "It does not start a dashboard server or mutate a runtime.",
            "It must be regenerated whenever dashboard/API routes change.",
        ],
        "evidence_refs": [
            "adapters/hermes/dashboard_route_inventory.py",
            "validation/hermes-installed-runtime-smoke/dashboard-create-route-parity-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-route-parity-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-done-route-parity-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-dispatch-route-parity-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-delete-route-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-links-route-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-attachment-route-safety-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-bulk-archive-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-reassign-route-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-reclaim-terminate-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-specify-route-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-decompose-route-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-comments-route-append-only-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-home-subscribe-route-visibility-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-board-delete-route-guard-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-board-lifecycle-operational-safety-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-profile-routes-operational-safety-smoke.json",
            "validation/hermes-installed-runtime-smoke/dashboard-orchestration-route-operational-safety-smoke.json",
        ],
        "next_action": "Keep this inventory at zero pending mutating route families before any real runtime update.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plugin-api", type=Path, required=True)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    receipt = build_receipt(args.plugin_api)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": repo_ref(args.out)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
