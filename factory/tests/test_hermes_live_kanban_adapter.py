from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ADAPTER_DIR = ROOT / "adapters" / "hermes"
MODULE_PATH = ADAPTER_DIR / "live_kanban_adapter.py"
FACTORYCTL_PATH = ROOT / "scripts" / "factoryctl.py"
VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
TEST_BOARD = "overkill-" + "factory-live-smoke"
MAIN_TASK_ID = "t_" + "00000001"
READY_TASK_ID = "t_" + "ready0001"
RELEASE_PARENT_TASK_ID = "t_" + "aaaabbbb"
RELEASE_REVIEW_PASS_TASK_ID = "t_" + "bbbb0001"
RELEASE_REVIEW_ORPHAN_TASK_ID = "t_" + "bbbb0002"
RELEASE_REVIEW_REPAIR_EDGE_TASK_ID = "t_" + "bbbb0003"
RELEASE_REVIEW_BLOCK_TASK_ID = "t_" + "bbbb0004"
sys.path.insert(0, str(ADAPTER_DIR))
SPEC = importlib.util.spec_from_file_location("live_kanban_adapter", MODULE_PATH)
assert SPEC is not None
adapter = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["live_kanban_adapter"] = adapter
SPEC.loader.exec_module(adapter)
FACTORYCTL_SPEC = importlib.util.spec_from_file_location("factoryctl_live_test", FACTORYCTL_PATH)
assert FACTORYCTL_SPEC is not None
factoryctl = importlib.util.module_from_spec(FACTORYCTL_SPEC)
assert FACTORYCTL_SPEC.loader is not None
sys.modules["factoryctl_live_test"] = factoryctl
FACTORYCTL_SPEC.loader.exec_module(factoryctl)
VALIDATOR_SPEC = importlib.util.spec_from_file_location("public_json_validator_live_test", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["public_json_validator_live_test"] = validator
VALIDATOR_SPEC.loader.exec_module(validator)


def solana_ai_kit_usage_receipt() -> dict:
    return {
        "provider_id": "solana-ai-kit",
        "source": "https://github.com/solanabr/solana-ai-kit",
        "pinned_ref": "v2.0.2",
        "loaded": True,
        "loaded_components": ["agents", "skills", "commands"],
        "evidence_refs": ["README.md"],
    }


def human_gate_packet_fixture() -> dict:
    return {
        "gate_type": "product_sot_owner_decision",
        "required_approvers": ["product-owner"],
        "decision_state": "pending",
        "risk_owner": "product-owner",
        "security_owner": "security-reviewer",
        "rollback_owner": "factory-orchestrator",
        "waiver_policy": "no waiver without explicit human record",
        "operator_briefing_package_ref": "reports/product-alpha/operator-briefing-package.md",
        "approval_request_ref": "reports/product-alpha/APPROVAL_REQUEST.json",
        "evidence_index_ref": "reports/product-alpha/EVIDENCE_INDEX.json",
        "owner_review_ref": "reports/product-alpha/OWNER_REVIEW.md",
        "required_decision_assets": [
            "markdown_document",
            "pdf_document",
            "approval_request_json",
            "evidence_index_json",
            "owner_review_markdown",
        ],
        "optional_explainer_assets": ["diagram"],
        "decision_package_delivery": {
            "operator_interface": "telegram",
            "primary_language": "pt-BR",
            "push_required": True,
            "summary_only_forbidden": True,
            "material_before_question": True,
            "attachment_order": [
                "markdown_document",
                "pdf_document",
                "approval_request_json",
                "evidence_index_json",
                "owner_review_markdown",
            ],
            "delivery_receipt_ref": "reports/product-alpha/DELIVERY_RECEIPT.json",
            "question_after_material_delivery": True,
        },
    }


def materialize_product_sot_frontier(card: dict) -> dict:
    card["universal_signal_intake"] = {
        "record_type": "universal_signal_intake",
        "intake_id": "runtime-intake-001",
        "source_ref_public_safe": "external:operator:source-envelope",
    }
    card["product_source_ledger"] = {
        "record_type": "product_source_ledger",
        "ledger_id": "runtime-source-ledger-001",
        "claim_table": [
            {
                "claim_id": "claim-001",
                "claim": "Product Alpha is an operations product with web and admin surfaces.",
                "claim_class": "fact",
                "status": "promoted",
                "source_refs": ["external:operator:source-envelope"],
            }
        ],
    }
    card["outcome_contract"] = {
        "record_type": "outcome_contract",
        "outcome": "Produce the complete product planning baseline before architecture.",
        "users_or_actors": ["Brazilian web3 user", "operator"],
        "success_signals": ["scope is covered", "open risks are named"],
    }
    card["product_sot"] = {
        "record_type": "product_sot",
        "what_it_is": "Product Alpha is an operations product with onboarding and operator surfaces.",
        "scope_in": ["onboarding", "operator administration"],
        "scope_out": ["production deploy", "credential transfer"],
        "evidence_refs": ["external:operator:source-envelope"],
    }
    card["full_product_sot_scope_coverage"] = {
        "record_type": "full_product_sot_scope_coverage",
        "coverage_state": "covered_for_owner_review",
        "covered_requirement_ids": ["REQ-001", "REQ-002"],
        "evidence_refs": ["external:operator:source-envelope"],
    }
    return card


class FakeHermes:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.counter = 0
        self.tasks: dict[str, dict[str, object]] = {}
        self.idempotent_task_ids: dict[str, str] = {}
        self.logs: dict[str, str] = {}

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if argv == ["hermes", "profile", "list"]:
            rows = [
                " Profile          Model                        Gateway      Alias        Distribution",
                " factory-orchestrator gpt-5.5                      stopped      factory-orchestrator -",
                " product-face gpt-5.5                      stopped      product-face -",
                " frontend-builder gpt-5.5                      stopped      frontend-builder -",
                " data-persistence-builder gpt-5.5                      stopped      data-persistence-builder -",
                " security-orchestrator gpt-5.5                      stopped      security-orchestrator -",
                " qa-verification-worker gpt-5.5                      stopped      qa-verification-worker -",
                " evidence-reconciler gpt-5.5                      stopped      evidence-reconciler -",
                " independent-reviewer gpt-5.5                      stopped      independent-reviewer -",
                " decomposition-planner gpt-5.5                      stopped      decomposition-planner -",
                " implementation-worker gpt-5.5                      stopped      implementation-worker -",
                " release-ops-worker gpt-5.5                      stopped      release-ops-worker -",
            ]
            return subprocess.CompletedProcess(argv, 0, stdout="\n".join(rows), stderr="")
        if argv == ["hermes", "status"]:
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout="OpenAI Codex  \u2713 logged in\nGateway Service  \u2713 running\n",
                stderr="",
            )
        if argv == ["hermes", "kanban", "boards", "list", "--json"]:
            return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")
        if argv[:4] == ["hermes", "kanban", "boards", "create"]:
            return subprocess.CompletedProcess(argv, 0, stdout="created", stderr="")
        if len(argv) >= 8 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "list":
            status = argv[argv.index("--status") + 1] if "--status" in argv else ""
            rows = [
                {"id": task_id, **task}
                for task_id, task in self.tasks.items()
                if not status or str(task.get("status") or "") == status
            ]
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(rows), stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "create":
            idempotency_key = argv[argv.index("--idempotency-key") + 1] if "--idempotency-key" in argv else ""
            if idempotency_key and idempotency_key in self.idempotent_task_ids:
                task_id = self.idempotent_task_ids[idempotency_key]
                self.tasks.setdefault(task_id, {"status": "blocked", "events": []})
                return subprocess.CompletedProcess(argv, 0, stdout=f'{{"id":"{task_id}"}}', stderr="")
            self.counter += 1
            task_id = "t_" + f"{self.counter:08x}"
            parent_ids = [
                argv[index + 1]
                for index, value in enumerate(argv)
                if value == "--parent" and index + 1 < len(argv)
            ]
            initial_status = "todo" if parent_ids else "blocked" if "--initial-status" in argv and "blocked" in argv else "ready"
            body = argv[argv.index("--body") + 1] if "--body" in argv else "{}"
            assignee = argv[argv.index("--assignee") + 1] if "--assignee" in argv else None
            workspace_ref = argv[argv.index("--workspace") + 1] if "--workspace" in argv else "scratch"
            title = argv[5] if len(argv) > 5 else ""
            task = {
                "id": task_id,
                "title": title,
                "status": initial_status,
                "events": [],
                "body": body,
                "assignee": assignee,
                "idempotency_key": idempotency_key,
            }
            if parent_ids:
                task["parents"] = list(parent_ids)
            if workspace_ref.startswith("dir:"):
                task["workspace_kind"] = "dir"
                task["workspace_path"] = workspace_ref[4:]
            else:
                task["workspace_kind"] = workspace_ref
            self.tasks[task_id] = task
            for parent_id in parent_ids:
                parent = self.tasks.setdefault(parent_id, {"status": "blocked", "events": [], "body": "{}", "assignee": None})
                parent.setdefault("children", [])
                if task_id not in parent["children"]:
                    parent["children"].append(task_id)
            if idempotency_key:
                self.idempotent_task_ids[idempotency_key] = task_id
            return subprocess.CompletedProcess(argv, 0, stdout=f'{{"id":"{task_id}"}}', stderr="")
        if len(argv) == 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "assign":
            task = self.tasks.setdefault(argv[5], {"status": "blocked", "events": [], "body": "{}", "assignee": None})
            task["assignee"] = argv[6]
            task.setdefault("events", []).append({"type": "assigned", "profile": argv[6]})
            return subprocess.CompletedProcess(argv, 0, stdout="assigned", stderr="")
        if len(argv) == 9 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "block":
            if argv[5] != "--kind" or argv[6] not in adapter.HERMES_TYPED_BLOCK_KINDS:
                return subprocess.CompletedProcess(argv, 2, stdout="", stderr="typed block kind required")
            task = self.tasks.setdefault(argv[7], {"status": "ready", "events": []})
            if argv[6] == "dependency":
                task["status"] = "todo"
                task.setdefault("events", []).append({"type": "dependency_wait", "payload": {"kind": argv[6], "reason": argv[8]}})
                return subprocess.CompletedProcess(argv, 0, stdout='{"status":"todo"}', stderr="")
            task["status"] = "blocked"
            task.setdefault("events", []).append({"type": "blocked", "payload": {"kind": argv[6], "reason": argv[8]}})
            return subprocess.CompletedProcess(argv, 0, stdout='{"status":"blocked"}', stderr="")
        if len(argv) >= 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "comment":
            if argv[5] == "--author":
                author = argv[6]
                task_id = argv[7]
                body = " ".join(argv[8:])
            else:
                author = "default"
                task_id = argv[5]
                body = " ".join(argv[6:])
            task = self.tasks.setdefault(task_id, {"status": "blocked", "events": [], "comments": []})
            task.setdefault("comments", []).append({"author": author, "body": body})
            task.setdefault("events", []).append({"type": "commented", "author": author})
            return subprocess.CompletedProcess(argv, 0, stdout="commented", stderr="")
        if len(argv) >= 6 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "unblock":
            task = self.tasks.setdefault(argv[5], {"status": "blocked", "events": []})
            task["status"] = "ready"
            task.setdefault("events", []).append({"type": "unblocked", "payload": None})
            return subprocess.CompletedProcess(argv, 0, stdout='{"status":"ready"}', stderr="")
        if len(argv) >= 6 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "dispatch":
            max_count = int(argv[argv.index("--max") + 1]) if "--max" in argv else len(self.tasks)
            spawned = []
            for task_id, task in self.tasks.items():
                if len(spawned) >= max_count:
                    break
                if task.get("status") != "ready":
                    continue
                task["status"] = "running"
                task["current_run_id"] = len(spawned) + 1
                task["worker_pid"] = 10000 + len(spawned)
                spawned.append(
                    {
                        "task_id": task_id,
                        "assignee": task.get("assignee"),
                        "workspace": task.get("workspace_kind") or "scratch",
                    }
                )
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(
                    {
                        "reclaimed": 0,
                        "crashed": [],
                        "timed_out": [],
                        "stale": [],
                        "auto_blocked": [],
                        "promoted": 0,
                        "spawned": spawned,
                    }
                ),
                stderr="",
            )
        if len(argv) >= 6 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "promote":
            task = self.tasks.setdefault(argv[5], {"status": "todo", "events": []})
            parents = [str(parent_id) for parent_id in task.get("parents", [])]
            blocked_parents = [
                parent_id
                for parent_id in parents
                if str(self.tasks.get(parent_id, {}).get("status") or "") not in {"done", "archived"}
            ]
            if blocked_parents and "--force" not in argv:
                return subprocess.CompletedProcess(argv, 1, stdout="", stderr="parents not satisfied")
            task["status"] = "ready"
            task.setdefault("events", []).append({"type": "promoted", "reason": " ".join(argv[6:])})
            return subprocess.CompletedProcess(argv, 0, stdout='{"status":"ready"}', stderr="")
        if len(argv) >= 6 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "complete":
            task = self.tasks.setdefault(argv[5], {"status": "ready", "events": []})
            task["status"] = "done"
            if "--result" in argv:
                task["result"] = argv[argv.index("--result") + 1]
            if "--summary" in argv:
                task["summary"] = argv[argv.index("--summary") + 1]
            if "--metadata" in argv:
                task["metadata"] = argv[argv.index("--metadata") + 1]
            task.setdefault("events", []).append({"type": "completed"})
            return subprocess.CompletedProcess(argv, 0, stdout='{"status":"done"}', stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "show":
            payload = self.tasks.get(argv[5], {"status": "blocked", "events": [{"type": "blocked", "reason": "gate"}]})
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload), stderr="")
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "runs":
            payload = self.tasks.get(argv[5], {})
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(payload.get("runs") or []), stderr="")
        if len(argv) >= 6 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "log":
            return subprocess.CompletedProcess(argv, 0, stdout=self.logs.get(argv[5], ""), stderr="")
        if len(argv) >= 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "link":
            parent_id = argv[5]
            child_id = argv[6]
            parent = self.tasks.setdefault(parent_id, {"status": "blocked", "events": [], "body": "{}", "assignee": None})
            child = self.tasks.setdefault(child_id, {"status": "todo", "events": [], "body": "{}", "assignee": None})
            parent.setdefault("children", [])
            child.setdefault("parents", [])
            if child_id not in parent["children"]:
                parent["children"].append(child_id)
            if parent_id not in child["parents"]:
                child["parents"].append(parent_id)
            return subprocess.CompletedProcess(argv, 0, stdout="linked", stderr="")
        if len(argv) >= 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "unlink":
            parent_id = argv[5]
            child_id = argv[6]
            parent = self.tasks.setdefault(parent_id, {"status": "blocked", "events": [], "body": "{}", "assignee": None})
            child = self.tasks.setdefault(child_id, {"status": "todo", "events": [], "body": "{}", "assignee": None})
            parent["children"] = [item for item in parent.get("children", []) if item != child_id]
            child["parents"] = [item for item in child.get("parents", []) if item != parent_id]
            child.setdefault("events", []).append({"type": "unlinked", "parent": parent_id})
            return subprocess.CompletedProcess(argv, 0, stdout="unlinked", stderr="")
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


class UnsafePromotionHermes(FakeHermes):
    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "show":
            task = self.tasks.setdefault(argv[5], {"status": "blocked", "events": [], "body": "{}", "assignee": None})
            task.setdefault("events", []).append({"kind": "promoted"})
            task.setdefault("events", []).append({"kind": "claimed"})
            return subprocess.CompletedProcess(argv, 0, stdout=json.dumps(task), stderr="")
        return super().__call__(argv)


class EmptyStdoutIdempotentHermes(FakeHermes):
    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "create":
            idempotency_key = argv[argv.index("--idempotency-key") + 1] if "--idempotency-key" in argv else ""
            if idempotency_key and idempotency_key in self.idempotent_task_ids:
                task_id = self.idempotent_task_ids[idempotency_key]
                self.tasks.setdefault(
                    task_id,
                    {"id": task_id, "status": "done", "events": [], "idempotency_key": idempotency_key},
                )
                return subprocess.CompletedProcess(argv, 0, stdout="", stderr="")
        return super().__call__(argv)


class StaleThenFreshReconcileHermes(FakeHermes):
    def __init__(self, *, stale_creates: int) -> None:
        super().__init__()
        self.stale_creates = stale_creates
        self.create_count = 0

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        if len(argv) >= 5 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "create":
            self.create_count += 1
            result = super().__call__(argv)
            try:
                task_id = json.loads(result.stdout).get("id")
            except Exception:
                task_id = None
            if task_id and self.create_count <= self.stale_creates:
                self.tasks[task_id]["status"] = "done"
                self.tasks[task_id]["events"] = [{"kind": "completed"}]
            return result
        return super().__call__(argv)


class BrokenLinkHermes(FakeHermes):
    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        if len(argv) >= 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "link":
            return subprocess.CompletedProcess(argv, 0, stdout="linked", stderr="")
        return super().__call__(argv)


class FakeRouteReadinessHermes:
    def __init__(self, *, include_implementation_worker: bool = True, auth_ready: bool = True) -> None:
        self.calls: list[list[str]] = []
        self.include_implementation_worker = include_implementation_worker
        self.auth_ready = auth_ready

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if argv == ["hermes", "profile", "list"]:
            rows = [
                " Profile          Model                        Gateway      Alias        Distribution",
                " default          gpt-5.5                      stopped      -            -",
                " factory-orchestrator gpt-5.5                      stopped      factory-orchestrator -",
                " decomposition-planner gpt-5.5                      stopped      decomposition-planner -",
                " release-ops-worker gpt-5.5                      stopped      release-ops-worker -",
            ]
            if self.include_implementation_worker:
                rows.append(
                    " implementation-worker gpt-5.5                      stopped      implementation-worker -"
                )
            rows.append(
                " independent-reviewer gpt-5.5                      stopped      independent-reviewer -"
            )
            return subprocess.CompletedProcess(argv, 0, stdout="\n".join(rows), stderr="")
        if argv == ["hermes", "status"]:
            marker = "\u2713 logged in" if self.auth_ready else "x not logged in"
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=f"OpenAI Codex  {marker}\nGateway Service  \u2713 running\n",
                stderr="",
            )
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


def private_windows_workspace_ref() -> str:
    return "dir:" + "C" + ":" + "\\private-workspace"


class FakeDispatchHermes:
    def __init__(self, *, native_spawned: bool = False, ready_step_key: str | None = "F15-runtime-execution") -> None:
        self.calls: list[list[str]] = []
        self.native_spawned = native_spawned
        self.ready_step_key = ready_step_key
        self.running_list_calls = 0

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
        if len(argv) >= 8 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "list":
            status = argv[argv.index("--status") + 1]
            if status == "ready":
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=json.dumps(
                        [
                            {
                                "id": READY_TASK_ID,
                                "assignee": "implementation-worker",
                                "workspace": private_windows_workspace_ref(),
                                **({"current_step_key": self.ready_step_key} if self.ready_step_key else {}),
                            }
                        ]
                    ),
                    stderr="",
                )
            if status in {"todo", "blocked", "done"}:
                return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")
            if status == "running":
                self.running_list_calls += 1
                if self.running_list_calls == 1:
                    return subprocess.CompletedProcess(argv, 0, stdout="[]", stderr="")
                return subprocess.CompletedProcess(
                    argv,
                    0,
                    stdout=json.dumps(
                        [
                            {
                                "id": READY_TASK_ID,
                                "assignee": "implementation-worker",
                                "current_run_id": 42,
                                "current_step_key": "F15-runtime-execution",
                                "worker_pid": 12345,
                                "workspace": private_windows_workspace_ref(),
                            }
                        ]
                    ),
                    stderr="",
                )
        if len(argv) >= 6 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "dispatch":
            spawned = (
                [
                    {
                        "task_id": READY_TASK_ID,
                        "assignee": "implementation-worker",
                        "current_step_key": "F15-runtime-execution",
                        "workspace": private_windows_workspace_ref(),
                    }
                ]
                if self.native_spawned
                else []
            )
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(
                    {
                        "reclaimed": 0,
                        "crashed": [],
                        "timed_out": [],
                        "stale": [],
                        "auto_blocked": [],
                        "promoted": 0,
                        "spawned": spawned,
                    }
                ),
                stderr="",
            )
        if len(argv) >= 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "show":
            return subprocess.CompletedProcess(
                argv,
                0,
                stdout=json.dumps(
                    {
                        "id": argv[5],
                        "status": "running",
                        "assignee": "implementation-worker",
                        "current_step_key": "F15-runtime-execution",
                        "current_run_id": 42,
                        "worker_pid": 12345,
                        "workspace": private_windows_workspace_ref(),
                    }
                ),
                stderr="",
            )
        return subprocess.CompletedProcess(argv, 1, stdout="", stderr="unexpected command")


def write_route_readiness(path: Path, extra_workers: list[str] | None = None) -> None:
    workers = [
        "codex-security",
        "solana-quasar-auditor",
        "independent-reviewer",
        "evidence-reconciler",
        "human-gate-clerk",
        "factory-orchestrator",
        "decomposition-planner",
        "source-ledger-worker",
        "implementation-worker",
        "release-ops-worker",
        "qa-verification-worker",
        "autoreview-gate",
        "security-orchestrator",
        "remote-proof-runner",
        "handoff-packer",
        "supply-chain-gate",
    ]
    for worker in extra_workers or []:
        if worker not in workers:
            workers.append(worker)
    path.write_text(
        json.dumps(
            {
                "$schema": "https://overkill-factory.dev/schemas/hermes-worker-route-readiness.schema.json",
                "schema": "overkill_factory_hermes_worker_route_readiness.v1",
                "ledger_ref": "external:test-route-ledger",
                "hermes_home_ref": "redacted-hermes-home",
                "result": "PASS",
                "worker_count": len(workers),
                "blocked_worker_count": 0,
                "blocked_workers": [],
                "checks": [
                    {
                        "worker_id": worker,
                        "task_id": f"route:{worker}",
                        "required_before": "done",
                        "queue_class": "blocking-before-done",
                        "status": "ready",
                        "profile_exists": True,
                        "provider_configured": True,
                        "model_configured": True,
                        "credential_status": "pass",
                        "credential_evidence": ["external:test-credential-evidence"],
                        "blocked_reasons": [],
                    }
                    for worker in workers
                ],
                "production_rule": "Do not dispatch unless every required worker route is ready.",
            }
        ),
        encoding="utf-8",
    )


def _replace_nested_text(value: object, replacements: dict[str, str]) -> object:
    if isinstance(value, str):
        result = value
        for old, new in replacements.items():
            result = result.replace(old, new)
        return result
    if isinstance(value, list):
        return [_replace_nested_text(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _replace_nested_text(item, replacements) for key, item in value.items()}
    return value


def single_ready_work_unit_plan() -> dict[str, object]:
    plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
    source_task = next(
        (
            task
            for task in plan.get("tasks", [])
            if isinstance(task, dict) and task.get("owner_worker") == "implementation-worker"
        ),
        plan["tasks"][0],
    )
    old_work_unit_id = str(source_task.get("work_unit_id") or "work-unit-001")
    old_packet_id = str(source_task.get("packet_id") or f"ready-work-unit-packet-{old_work_unit_id}")
    task = _replace_nested_text(
        copy.deepcopy(source_task),
        {
            old_work_unit_id: "work-unit-001",
            old_packet_id: "ready-work-unit-packet-work-unit-001",
        },
    )
    task["work_unit_id"] = "work-unit-001"
    task["packet_id"] = "ready-work-unit-packet-work-unit-001"
    task["idempotency_key"] = "overkill:test:work-unit-001"
    task["title"] = "OF ready work unit work-unit-001"
    task["dependency_refs"] = []
    body_contract = task.get("body_contract") if isinstance(task.get("body_contract"), dict) else {}
    body_contract["work_unit_id"] = "work-unit-001"
    body_contract["packet_id"] = "ready-work-unit-packet-work-unit-001"
    body_contract["dependency_refs"] = []
    context_packet = body_contract.get("work_unit_context_packet") if isinstance(body_contract.get("work_unit_context_packet"), dict) else {}
    context_packet["work_unit_id"] = "work-unit-001"
    embedded = context_packet.get("embedded_payloads") if isinstance(context_packet.get("embedded_payloads"), dict) else {}
    current = embedded.get("current_work_unit") if isinstance(embedded.get("current_work_unit"), dict) else {}
    current["unit_id"] = "work-unit-001"
    current["dependency_refs"] = []
    product_plan = embedded.get("product_creation_plan") if isinstance(embedded.get("product_creation_plan"), dict) else {}
    product_plan["execution_order"] = ["work-unit-001"]
    product_plan["dependency_graph"] = []
    task["work_unit_context_packet"] = body_contract["work_unit_context_packet"]
    plan["tasks"] = [task]
    plan["acceptance"]["task_count"] = 1
    return plan


def single_product_creation_plan() -> dict[str, object]:
    product_plan = factoryctl.load_json_like(ROOT / "templates" / "product-creation-plan.json")
    source_unit = next(
        (
            unit
            for unit in product_plan.get("work_units", [])
            if isinstance(unit, dict) and unit.get("owner_worker") == "implementation-worker"
        ),
        product_plan["work_units"][0],
    )
    old_work_unit_id = str(source_unit.get("unit_id") or "work-unit-001")
    rewritten = _replace_nested_text(copy.deepcopy(product_plan), {old_work_unit_id: "work-unit-001"})
    unit = _replace_nested_text(copy.deepcopy(source_unit), {old_work_unit_id: "work-unit-001"})
    rewritten["work_units"] = [unit]
    rewritten["execution_order"] = ["work-unit-001"]
    rewritten["dependency_graph"] = [
        {"from": "method-contract-public-template", "to": "work-unit-001"},
        {"from": "decomposition_coverage_review", "to": "product_implementation_readiness"},
    ]
    for row in rewritten.get("requirement_execution_coverage") or []:
        if isinstance(row, dict):
            row["work_unit_refs"] = ["work-unit-001"]
    rewritten["acceptance"]["work_units_accounted"] = 1
    return rewritten


def write_single_product_creation_plan(path: Path) -> None:
    path.write_text(json.dumps(single_product_creation_plan()), encoding="utf-8")


def task_comment_bodies(task: dict[str, object]) -> list[str]:
    return [
        str(comment.get("body") or "")
        for comment in task.get("comments", []) or []
        if isinstance(comment, dict)
    ]


def two_step_ready_work_unit_plan() -> dict[str, object]:
    plan = single_ready_work_unit_plan()
    first = copy.deepcopy(plan["tasks"][0])
    second = copy.deepcopy(plan["tasks"][0])

    first["work_unit_id"] = "work-unit-001"
    first["packet_id"] = "ready-work-unit-packet-work-unit-001"
    first["idempotency_key"] = "overkill:test:work-unit-001"
    first["body_contract"]["work_unit_id"] = "work-unit-001"
    first["body_contract"]["packet_id"] = "ready-work-unit-packet-work-unit-001"
    first["body_contract"]["dependency_refs"] = []
    first["body_contract"]["work_unit_context_packet"]["work_unit_id"] = "work-unit-001"
    first["body_contract"]["work_unit_context_packet"]["embedded_payloads"]["current_work_unit"]["unit_id"] = "work-unit-001"

    second["work_unit_id"] = "work-unit-002"
    second["packet_id"] = "ready-work-unit-packet-work-unit-002"
    second["idempotency_key"] = "overkill:test:work-unit-002"
    second["title"] = "OF ready work unit work-unit-002"
    second["body_contract"]["work_unit_id"] = "work-unit-002"
    second["body_contract"]["packet_id"] = "ready-work-unit-packet-work-unit-002"
    second["body_contract"]["dependency_refs"] = ["work-unit-001"]
    second["body_contract"]["work_unit_context_packet"]["work_unit_id"] = "work-unit-002"
    second["body_contract"]["work_unit_context_packet"]["embedded_payloads"]["current_work_unit"]["unit_id"] = "work-unit-002"

    for task in (first, second):
        product_plan = task["body_contract"]["work_unit_context_packet"]["embedded_payloads"]["product_creation_plan"]
        product_plan["execution_order"] = ["work-unit-001", "work-unit-002"]
        product_plan["dependency_graph"] = [{"from": "work-unit-001", "to": "work-unit-002"}]
        task["body_contract"]["work_unit_context_packet"]["embedded_payloads"]["current_work_unit"][
            "dependency_refs"
        ] = list(task["body_contract"].get("dependency_refs") or [])
        task["work_unit_context_packet"] = task["body_contract"]["work_unit_context_packet"]

    plan["tasks"] = [first, second]
    plan["acceptance"]["task_count"] = 2
    return plan


def materialize_template_ready_work_unit(
    *,
    fake: FakeHermes,
    tmp_path: Path,
    workspace: str = "scratch",
) -> tuple[dict[str, object], Path, Path, Path]:
    plan = single_ready_work_unit_plan()
    plan_path = tmp_path / "plan.json"
    readiness_path = tmp_path / "route-readiness.json"
    materialization_result_path = tmp_path / "materialization-result.json"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    write_route_readiness(readiness_path, extra_workers=["implementation-worker"])
    materialize_args = adapter.build_parser().parse_args(
        [
            "materialize-ready-work-units",
            "--plan",
            str(plan_path),
            "--route-readiness",
            str(readiness_path),
            "--workspace",
            workspace,
        ]
    )
    materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
    materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
    return plan, plan_path, readiness_path, materialization_result_path


def assert_live_adapter_result_schema(testcase: unittest.TestCase, result: dict[str, object]) -> None:
    schema = json.loads((ROOT / "schemas" / "hermes-live-adapter-result.schema.json").read_text(encoding="utf-8"))
    errors = validator.validate_node(schema, result, "$", schemas={"hermes-live-adapter-result.schema.json": schema}, root_schema=schema)
    testcase.assertEqual(errors, [])


def assert_route_readiness_schema(testcase: unittest.TestCase, result: dict[str, object]) -> None:
    schema = json.loads((ROOT / "schemas" / "hermes-worker-route-readiness.schema.json").read_text(encoding="utf-8"))
    errors = validator.validate_node(schema, result, "$", schemas={"hermes-worker-route-readiness.schema.json": schema}, root_schema=schema)
    testcase.assertEqual(errors, [])


def assert_product_creation_closeout_schema(testcase: unittest.TestCase, result: dict[str, object]) -> None:
    schema = json.loads((ROOT / "schemas" / "product-creation-run-closeout.schema.json").read_text(encoding="utf-8"))
    closeout = result["product_creation_run_closeout"]
    errors = validator.validate_node(
        schema,
        closeout,
        "$",
        schemas={"product-creation-run-closeout.schema.json": schema},
        root_schema=schema,
    )
    testcase.assertEqual(errors, [])


def assert_release_readiness_closeout_schema(testcase: unittest.TestCase, result: dict[str, object]) -> None:
    schema = json.loads((ROOT / "schemas" / "release-readiness-review-closeout.schema.json").read_text(encoding="utf-8"))
    closeout = result["release_readiness_review_closeout"]
    errors = validator.validate_node(
        schema,
        closeout,
        "$",
        schemas={"release-readiness-review-closeout.schema.json": schema},
        root_schema=schema,
    )
    testcase.assertEqual(errors, [])


def ready_work_unit_task_ids(fake: FakeHermes) -> list[str]:
    task_ids: list[str] = []
    for task_id, task in fake.tasks.items():
        try:
            body = json.loads(str(task.get("body") or "{}"))
        except json.JSONDecodeError:
            continue
        if body.get("packet_type") == "ready_work_unit_execution_request":
            task_ids.append(task_id)
    return task_ids


def block_ready_work_unit_after_release(fake: FakeHermes, task_id: str) -> None:
    task = fake.tasks[task_id]
    task["status"] = "blocked"
    task.setdefault("events", []).append({"type": "blocked", "reason": "review-required"})


def add_ready_work_unit_review_run(
    fake: FakeHermes,
    *,
    review_task_id: str,
    parent_task_id: str,
    verdict: str = "PASS",
    blocking_findings: bool = False,
    human_gate_required: bool = False,
    target_override: str | None = None,
) -> None:
    review_result = {
        "verdict": verdict,
        "review_comment_task_id": target_override or parent_task_id,
        "blocking_findings": blocking_findings,
        "required_fixes": ["fix required"] if blocking_findings else [],
        "human_gate_required": human_gate_required,
    }
    fake.tasks[review_task_id] = {
        "id": review_task_id,
        "status": "done",
        "assignee": "independent-reviewer",
        "body": "{}",
        "events": [],
        "runs": [
            {
                "id": 1,
                "status": "done",
                "outcome": "completed",
                "profile": "independent-reviewer",
                "metadata": {
                    "independent_review_result": review_result,
                    "blocking_findings": blocking_findings,
                    "human_gate_required": human_gate_required,
                },
            }
        ],
    }


def add_release_readiness_parent(fake: FakeHermes, task_id: str = RELEASE_PARENT_TASK_ID) -> str:
    fake.tasks[task_id] = {
        "id": task_id,
        "status": "blocked",
        "assignee": "release-ops-worker",
        "body": json.dumps(
            {
                "packet_type": "product_creation_run_closeout_next_action",
                "marker": "product_creation_closeout_next_route",
                "next_action": "release_readiness_required",
                "decision": "release_readiness_required",
                "complete_product_claim_allowed": False,
                "production_promotion_allowed": False,
                "dispatch_allowed_by_this_step": False,
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
            }
        ),
        "events": [{"type": "blocked", "reason": "review-required"}],
        "comments": [
            {
                "author": "release-ops-worker",
                "body": json.dumps(
                    {
                        "marker": "release_readiness_packet_prepared",
                        "review_required": True,
                        "production_promotion_allowed": False,
                        "complete_product_claim_allowed": False,
                    }
                ),
            }
        ],
        "runs": [
            {
                "id": 1,
                "status": "blocked",
                "outcome": "blocked",
                "profile": "release-ops-worker",
                "metadata": {
                    "release_ops_result": {
                        "result": "PASS",
                        "blocking_findings": False,
                        "production_promotion_allowed": False,
                        "complete_product_claim_allowed": False,
                    }
                },
            }
        ],
    }
    return task_id


def add_release_readiness_review_run(
    fake: FakeHermes,
    *,
    review_task_id: str,
    parent_task_id: str,
    verdict: str = "PASS",
    blocking_findings: bool = False,
    durable_edge: bool = True,
) -> None:
    fake.tasks[review_task_id] = {
        "id": review_task_id,
        "status": "done",
        "title": f"Independent review: release readiness packet for {parent_task_id}",
        "assignee": "independent-reviewer",
        "body": f"Review release readiness packet for parent task {parent_task_id}",
        "events": [],
        "comments": [],
        "runs": [
            {
                "id": 2,
                "status": "done" if not blocking_findings else "blocked",
                "outcome": "completed" if not blocking_findings else "blocked",
                "profile": "independent-reviewer",
                "ended_at": 20,
                "metadata": {
                    "independent_review_result": {
                        "verdict": verdict,
                        "review_target": parent_task_id,
                        "blocking_findings": blocking_findings,
                        "required_fixes": ["repair release readiness packet"] if blocking_findings else [],
                        "production_promotion_approved": False,
                        "complete_product_claim_allowed": False,
                    },
                    "blocking_findings": blocking_findings,
                    "production_promotion_approved": False,
                    "complete_product_claim_allowed": False,
                },
            }
        ],
    }
    if durable_edge:
        fake.tasks[parent_task_id].setdefault("parents", []).append(review_task_id)
        fake.tasks[review_task_id].setdefault("children", []).append(parent_task_id)


class HermesLiveKanbanAdapterTest(unittest.TestCase):
    def test_default_runner_decodes_utf8_terminal_output(self) -> None:
        script = (
            "import sys; "
            "sys.stdout.buffer.write('OpenAI Codex  \u2713 logged in\\n'.encode('utf-8'))"
        )
        result = adapter.default_runner([sys.executable, "-c", script])

        self.assertEqual(result.returncode, 0)
        self.assertIn("OpenAI Codex", result.stdout)
        self.assertIn("\u2713 logged in", result.stdout)

    def test_safe_command_for_error_redacts_body_and_large_args(self) -> None:
        unsafe_body = '{"private":"secret"}'
        unsafe_comment = "x" * 600
        text = adapter.safe_command_for_error(["hermes", "kanban", "create", "--body", unsafe_body, unsafe_comment])

        self.assertNotIn(unsafe_body, text)
        self.assertNotIn(unsafe_comment, text)
        self.assertIn("<redacted", text)

    def test_collect_route_readiness_derives_workers_from_ready_plan(self) -> None:
        fake = FakeRouteReadinessHermes()
        plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            out_path = tmp_path / "route-readiness.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "collect-route-readiness",
                    "--plan",
                    str(plan_path),
                    "--out",
                    str(out_path),
                    "--ledger-ref",
                    "external:test-route-ledger",
                    "--credential-evidence-ref",
                    "external:test-auth",
                ]
            )
            result = adapter.collect_route_readiness(args, runner=fake)
            wrote_output = out_path.exists()

        assert_route_readiness_schema(self, result)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["blocked_worker_count"], 0)
        self.assertEqual(
            [check["worker_id"] for check in result["checks"]],
            [
                "decomposition-planner",
                "independent-reviewer",
                "implementation-worker",
                "factory-orchestrator",
                "release-ops-worker",
            ],
        )
        self.assertEqual(result["checks"][0]["credential_evidence"], ["external:test-auth"])
        self.assertTrue(wrote_output)
        self.assertEqual(fake.calls, [["hermes", "profile", "list"], ["hermes", "status"]])

    def test_collect_route_readiness_blocks_missing_profile(self) -> None:
        fake = FakeRouteReadinessHermes(include_implementation_worker=False)
        args = adapter.build_parser().parse_args(
            [
                "collect-route-readiness",
                "--worker",
                "implementation-worker",
                "--ledger-ref",
                "external:test-route-ledger",
            ]
        )
        result = adapter.collect_route_readiness(args, runner=fake)

        assert_route_readiness_schema(self, result)
        self.assertEqual(result["result"], "BLOCKED")
        self.assertEqual(result["blocked_workers"], ["implementation-worker"])
        self.assertIn("profile_missing", result["checks"][0]["blocked_reasons"])

    def test_collect_route_readiness_blocks_unproven_auth(self) -> None:
        fake = FakeRouteReadinessHermes(auth_ready=False)
        args = adapter.build_parser().parse_args(
            [
                "collect-route-readiness",
                "--worker",
                "implementation-worker",
                "--ledger-ref",
                "external:test-route-ledger",
            ]
        )
        result = adapter.collect_route_readiness(args, runner=fake)

        assert_route_readiness_schema(self, result)
        self.assertEqual(result["result"], "BLOCKED")
        self.assertIn("credential_not_proven", result["checks"][0]["blocked_reasons"])

    def test_factory_run_graph_backbone_is_derived_from_workflow_catalog(self) -> None:
        catalog_path = adapter.resolve_factory_workflow_catalog_path(ROOT / "docs" / "factory-workflow.catalog.json")
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
        expected_phase_ids = [
            phase["phase_id"]
            for phase in catalog["phases"]
            if phase["phase_id"] not in {"F0", "F1"}
        ]
        expected_names = [
            phase["phase_name"]
            for phase in catalog["phases"]
            if phase["phase_id"] not in {"F0", "F1"}
        ]

        self.assertEqual([node["phase_id"] for node in adapter.FACTORY_RUN_GRAPH_BACKBONE], expected_phase_ids)
        self.assertEqual(
            [node["title"] for node in adapter.FACTORY_RUN_GRAPH_BACKBONE],
            [f"{phase_id} - {name}" for phase_id, name in zip(expected_phase_ids, expected_names)],
        )
        self.assertEqual(adapter.FACTORY_RUN_GRAPH_BACKBONE[0]["node_id"], "F2-source-ledger")
        self.assertTrue(
            any(node["phase_id"] == "F9" and "Risk And Authority Gates" in node["title"] for node in adapter.FACTORY_RUN_GRAPH_BACKBONE)
        )
        self.assertTrue(
            any(node["phase_id"] == "F10" and "Security Architecture" in node["title"] for node in adapter.FACTORY_RUN_GRAPH_BACKBONE)
        )

    def test_factory_run_graph_backbone_localizes_user_facing_card_titles(self) -> None:
        backbone = adapter.load_factory_run_graph_backbone_from_catalog(language="pt-BR")

        self.assertEqual(backbone[0]["node_id"], "F2-source-ledger")
        self.assertEqual(backbone[0]["title"], "F2 - Registro de fontes")
        self.assertTrue(any(node["phase_id"] == "F10" and node["title"] == "F10 - Arquitetura de seguranca" for node in backbone))
        self.assertTrue(any(node["phase_id"] == "F18" and node["title"] == "F18 - Revisao independente" for node in backbone))

    def test_materialize_bridge_start_releases_and_dispatches_root_by_default(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            start_path = tmp_path / "start-request.json"
            envelope_path = tmp_path / "source-envelope.json"
            start_path.write_text(
                json.dumps(
                    {
                        "record_type": "factory_bridge_start_request",
                        "run_id": "sample-new-project-20260622-161302",
                        "operator_goal": "Start a new sample product project.",
                        "project_mode": "new_project",
                        "source_envelope_ref": "external:operator:source-envelope",
                        "operator_language_policy": {
                            "primary_language": "pt-BR",
                            "user_facing_surfaces_follow_primary_language": True,
                            "kanban_cards_follow_primary_language": True,
                            "decision_packages_follow_primary_language": True,
                            "internal_factory_surfaces_may_use_english": True,
                        },
                        "handoff_to_factory": {
                            "gateway_profile": "overkill-factory-gerente",
                            "orchestrator_worker": "factory-orchestrator",
                            "handoff_contract": "factory_bridge_start_request",
                            "bridge_may_execute_recipient_work": False,
                            "bridge_may_create_hermes_board": False,
                            "factory_start_path_required": True,
                        },
                        "target_board_policy": {
                            "policy": "factory_must_create_new_board",
                            "requires_new_hermes_board": True,
                            "existing_board_ref": None,
                            "requires_explicit_existing_board_ref": False,
                            "board_creation_owner": "factory_start_path",
                            "factory_start_path_required": True,
                            "bridge_may_select_existing_board": False,
                            "bridge_may_mutate_board": False,
                        },
                        "bridge_limits": {
                            "bridge_must_not_create_hermes_board": True,
                            "bridge_must_not_create_hermes_cards": True,
                            "bridge_must_not_dispatch_workers": True,
                            "bridge_must_not_choose_runtime_board": True,
                            "bridge_only_registers_operator_intent": True,
                        },
                        "requested_factory_action": {
                            "action": "start_factory_run",
                            "owner": "factory-orchestrator",
                            "gateway_profile": "overkill-factory-gerente",
                            "factory_must_materialize_runtime_state": True,
                        },
                    }
                ),
                encoding="utf-8",
            )
            envelope_path.write_text(
                json.dumps(
                    {
                        "record_type": "factory_bridge_source_envelope",
                        "run_id": "sample-new-project-20260622-161302",
                        "operator_language_policy": {
                            "primary_language": "pt-BR",
                            "user_facing_surfaces_follow_primary_language": True,
                            "kanban_cards_follow_primary_language": True,
                            "decision_packages_follow_primary_language": True,
                            "internal_factory_surfaces_may_use_english": True,
                        },
                        "source_items": [
                            {
                                "source_ref": "external:operator:sample-brief",
                                "source_role": "operator_supplied_material",
                                "received_as": "opaque_ref",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            args = adapter.build_parser().parse_args(
                [
                    "materialize-bridge-start",
                    "--start-request",
                    str(start_path),
                    "--source-envelope",
                    str(envelope_path),
                ]
            )
            result = adapter.materialize_bridge_start(args, runner=fake)
            hold_fake = FakeHermes()
            hold_args = adapter.build_parser().parse_args(
                [
                    "materialize-bridge-start",
                    "--start-request",
                    str(start_path),
                    "--source-envelope",
                    str(envelope_path),
                    "--hold-start",
                ]
            )
            hold_result = adapter.materialize_bridge_start(hold_args, runner=hold_fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["mode"], "materialize-bridge-start")
        self.assertEqual(result["board"], "sample-new-project-20260622-161302")
        self.assertTrue(result["board_created"])
        self.assertEqual(result["main_task_id"], "kanban:<redacted>")
        self.assertEqual(result["runtime_gate"]["initial_status"], "blocked_then_released")
        self.assertTrue(result["runtime_gate"]["blocked_event_verified"])
        self.assertTrue(result["runtime_gate"]["start_release_verified"])
        self.assertTrue(result["runtime_gate"]["dispatch_requested"])
        self.assertTrue(any(call[4] == "dispatch" for call in fake.calls if len(call) > 4))
        self.assertIn(["hermes", "kanban", "boards", "create", "sample-new-project-20260622-161302"], [call[:5] for call in fake.calls])
        task = fake.tasks["t_" + "00000001"]
        self.assertEqual(task["title"], "F1 - Inicio da fabrica: sample-new-project-20260622-161302")
        self.assertEqual(task["status"], "running")
        self.assertEqual(task["assignee"], "factory-orchestrator")
        body = json.loads(str(task["body"]))
        self.assertEqual(body["task_type"], "factory_bridge_start_root")
        self.assertEqual(body["initial_gate"]["status"], "blocked_then_released_by_default")
        self.assertFalse(body["initial_gate"]["human_gate_required_for_normal_start"])
        self.assertEqual(body["deterministic_phase_contract"]["route_authority"], "factory_run_graph_and_phase_engine")
        self.assertFalse(body["deterministic_phase_contract"]["agent_may_choose_phase"])
        self.assertEqual(body["deterministic_phase_contract"]["initial_frontier"], "intake")
        self.assertEqual(body["factory_run_graph"]["record_type"], "factory_run_graph")
        self.assertEqual(body["operator_language_policy"]["primary_language"], "pt-BR")
        self.assertEqual(body["factory_run_graph"]["operator_language"], "pt-BR")
        self.assertTrue(body["factory_run_graph"]["operator_language_policy"]["kanban_cards_follow_primary_language"])
        self.assertEqual(body["factory_run_graph"]["runtime_shape"], adapter.FACTORY_RUN_GRAPH_RUNTIME_SHAPE)
        self.assertEqual(body["factory_run_graph"]["no_idle_role"], adapter.FACTORY_RUN_GRAPH_NO_IDLE_ROLE)
        self.assertFalse(body["factory_run_graph"]["agent_may_choose_phase"])
        self.assertIn("less mirabolante", body["factory_run_graph"]["operating_mantra"])
        self.assertEqual(result["factory_run_graph"]["record_type"], "factory_run_graph")
        self.assertEqual(result["factory_run_graph"]["no_idle_role"], adapter.FACTORY_RUN_GRAPH_NO_IDLE_ROLE)
        self.assertEqual(result["factory_run_graph_task_ids"]["F1-intake"], "kanban:<redacted>")
        self.assertEqual(set(result["factory_run_graph_task_ids"]), {node["node_id"] for node in body["factory_run_graph"]["nodes"]})
        root_task_id = "t" + "_00000001"
        first_backbone_task_id = "t" + "_00000002"
        graph_tasks = {task_id: task for task_id, task in fake.tasks.items() if task_id != root_task_id}
        self.assertEqual(len(graph_tasks), len(adapter.FACTORY_RUN_GRAPH_BACKBONE))
        first_graph_task = fake.tasks[first_backbone_task_id]
        self.assertEqual(first_graph_task["title"], "F2 - Registro de fontes")
        self.assertEqual(first_graph_task["status"], "todo")
        self.assertEqual(first_graph_task["parents"], [root_task_id])
        first_graph_body = json.loads(str(first_graph_task["body"]))
        self.assertEqual(first_graph_body["packet_type"], adapter.FACTORY_RUN_GRAPH_NODE_PACKET_TYPE)
        self.assertEqual(first_graph_body["node_id"], "F2-source-ledger")
        self.assertEqual(first_graph_body["operator_language_policy"]["primary_language"], "pt-BR")
        self.assertEqual(first_graph_body["dependency_mechanism"], "hermes_task_links_parent_child")
        self.assertFalse(first_graph_body["agent_may_choose_phase"])
        self.assertEqual(first_graph_body["no_idle_role"], adapter.FACTORY_RUN_GRAPH_NO_IDLE_ROLE)
        self.assertTrue(all(task["status"] == "todo" for task in graph_tasks.values()))
        self.assertTrue(all(task.get("parents") for task in graph_tasks.values()))
        self.assertFalse(
            any(
                any(event.get("payload", {}).get("kind") == "dependency" for event in task.get("events", []))
                for task in graph_tasks.values()
            )
        )
        self.assertFalse(body["bridge_boundary"]["bridge_created_hermes_board"])
        self.assertTrue(body["bridge_boundary"]["factory_start_path_created_runtime_state"])
        assert_live_adapter_result_schema(self, hold_result)
        self.assertEqual(hold_result["runtime_gate"]["initial_status"], "blocked")
        self.assertTrue(hold_result["runtime_gate"]["hold_start"])
        self.assertFalse(hold_result["runtime_gate"]["start_release_verified"])
        self.assertFalse(hold_result["runtime_gate"]["dispatch_requested"])
        self.assertFalse(any(call[4] == "dispatch" for call in hold_fake.calls if len(call) > 4))
        hold_task = hold_fake.tasks["t_" + "00000001"]
        self.assertEqual(hold_task["status"], "blocked")
        self.assertEqual(hold_task["assignee"], "factory-orchestrator")
        self.assertEqual(len(hold_fake.tasks), 1 + len(adapter.FACTORY_RUN_GRAPH_BACKBONE))

    def test_materialize_bridge_start_refuses_default_board_for_new_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            start_path = Path(tmp) / "start-request.json"
            start_path.write_text(
                json.dumps(
                    {
                        "record_type": "factory_bridge_start_request",
                        "run_id": "run-alpha",
                        "project_mode": "new_project",
                        "handoff_to_factory": {
                            "gateway_profile": "overkill-factory-gerente",
                            "orchestrator_worker": "factory-orchestrator",
                        },
                        "bridge_limits": {
                            "bridge_must_not_create_hermes_board": True,
                            "bridge_must_not_create_hermes_cards": True,
                            "bridge_must_not_dispatch_workers": True,
                        },
                        "requested_factory_action": {"action": "start_factory_run"},
                    }
                ),
                encoding="utf-8",
            )
            args = adapter.build_parser().parse_args(
                ["materialize-bridge-start", "--start-request", str(start_path), "--board", "default"]
            )
            with self.assertRaisesRegex(RuntimeError, "fresh non-default board"):
                adapter.materialize_bridge_start(args, runner=FakeHermes())

    def test_materialize_ready_work_units_creates_blocked_tasks_without_dispatch(self) -> None:
        fake = FakeHermes()
        plan = single_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness = tmp_path / "route-readiness.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness, extra_workers=["implementation-worker"])
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness),
                    "--workspace",
                    "scratch",
                ]
            )
            result = adapter.materialize_ready_work_units(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["mode"], "materialize-ready-work-units")
        self.assertFalse(result["dry_run"])
        self.assertEqual(result["ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        create_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "create"]
        block_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "block"]
        assign_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "assign"]
        dispatch_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "dispatch"]
        self.assertEqual(len(create_calls), 1)
        self.assertNotIn("--assignee", create_calls[0])
        self.assertNotIn("--initial-status", create_calls[0])
        self.assertEqual(create_calls[0][create_calls[0].index("--workspace") + 1], "scratch")
        self.assertEqual(len(block_calls), 1)
        self.assertEqual(len(assign_calls), 1)
        self.assertEqual(assign_calls[0][-1], "implementation-worker")
        self.assertEqual(dispatch_calls, [])
        materialized_task_id = next(iter(fake.tasks))
        self.assertEqual(fake.tasks[materialized_task_id]["status"], "blocked")
        self.assertEqual(fake.tasks[materialized_task_id]["assignee"], "implementation-worker")
        self.assertTrue(fake.tasks[materialized_task_id]["events"])

    def test_materialized_work_units_become_native_parents_of_next_phase_card(self) -> None:
        fake = FakeHermes()
        fake.tasks["phase-f16-node"] = {
            "status": "todo",
            "body": json.dumps(
                {
                    "packet_type": adapter.FACTORY_RUN_GRAPH_NODE_PACKET_TYPE,
                    "phase_id": "F16",
                    "node_id": "F16-worker-results",
                }
            ),
            "parents": [],
            "events": [],
        }
        plan = single_ready_work_unit_plan()
        plan["board"] = TEST_BOARD
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness = tmp_path / "route-readiness.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness, extra_workers=["implementation-worker"])
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness),
                    "--workspace",
                    "scratch",
                ]
            )
            result = adapter.materialize_ready_work_units(args, runner=fake)

        work_unit_task_id = ready_work_unit_task_ids(fake)[0]
        self.assertIn(work_unit_task_id, fake.tasks["phase-f16-node"]["parents"])
        link_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "link"]
        self.assertEqual(link_calls, [["hermes", "kanban", "--board", TEST_BOARD, "link", work_unit_task_id, "phase-f16-node"]])
        self.assertTrue(result["runtime_gate"]["phase_closure_dependencies_attached"])
        blocked_promote = fake(["hermes", "kanban", "--board", TEST_BOARD, "promote", "phase-f16-node"])
        self.assertNotEqual(blocked_promote.returncode, 0)
        self.assertIn("parents not satisfied", blocked_promote.stderr)
        fake.tasks[work_unit_task_id]["status"] = "done"
        allowed_promote = fake(["hermes", "kanban", "--board", TEST_BOARD, "promote", "phase-f16-node"])
        self.assertEqual(allowed_promote.returncode, 0)
        self.assertEqual(fake.tasks["phase-f16-node"]["status"], "ready")

    def test_materialized_work_units_refuse_late_phase_closure_links(self) -> None:
        for phase_status in ("ready", "running", "done"):
            with self.subTest(phase_status=phase_status):
                fake = FakeHermes()
                fake.tasks["phase-f16-node"] = {
                    "status": phase_status,
                    "body": json.dumps(
                        {
                            "packet_type": adapter.FACTORY_RUN_GRAPH_NODE_PACKET_TYPE,
                            "phase_id": "F16",
                            "node_id": "F16-worker-results",
                        }
                    ),
                    "parents": [],
                    "events": [],
                }
                plan = single_ready_work_unit_plan()
                plan["board"] = TEST_BOARD
                with tempfile.TemporaryDirectory() as tmp:
                    tmp_path = Path(tmp)
                    plan_path = tmp_path / "plan.json"
                    readiness = tmp_path / "route-readiness.json"
                    plan_path.write_text(json.dumps(plan), encoding="utf-8")
                    write_route_readiness(readiness, extra_workers=["implementation-worker"])
                    args = adapter.build_parser().parse_args(
                        [
                            "materialize-ready-work-units",
                            "--plan",
                            str(plan_path),
                            "--route-readiness",
                            str(readiness),
                            "--workspace",
                            "scratch",
                        ]
                    )
                    with self.assertRaisesRegex(RuntimeError, f"next phase F16 is already {phase_status}"):
                        adapter.materialize_ready_work_units(args, runner=fake)

    def test_materialize_ready_work_units_chunks_large_body_without_losing_context(self) -> None:
        fake = FakeHermes()
        plan = single_ready_work_unit_plan()
        body_contract = plan["tasks"][0]["body_contract"]
        body_contract["work_unit_context_packet"]["embedded_payloads"]["large_context"] = "x" * 40000
        plan["tasks"][0]["work_unit_context_packet"] = body_contract["work_unit_context_packet"]
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness = tmp_path / "route-readiness.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness, extra_workers=["implementation-worker"])
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness),
                    "--workspace",
                    "scratch",
                ]
            )
            result = adapter.materialize_ready_work_units(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        create_call = next(call for call in fake.calls if len(call) >= 5 and call[4] == "create")
        create_body = create_call[create_call.index("--body") + 1]
        self.assertLess(len(create_body), adapter.READY_WORK_UNIT_DIRECT_BODY_LIMIT)
        create_body_manifest = json.loads(create_body)
        self.assertEqual(create_body_manifest["context_transport"]["mode"], adapter.READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE)

        comment_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "comment"]
        self.assertGreater(len(comment_calls), 1)
        materialized_task_id = next(iter(fake.tasks))
        reconstructed = adapter.ready_work_unit_body(fake.tasks[materialized_task_id], task_id=materialized_task_id)
        self.assertEqual(reconstructed["packet_id"], body_contract["packet_id"])
        self.assertEqual(
            reconstructed["work_unit_context_packet"]["embedded_payloads"]["large_context"],
            "x" * 40000,
        )

    def test_materialize_ready_work_units_dry_run_does_not_touch_hermes(self) -> None:
        fake = FakeHermes()
        plan = single_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--dry-run",
                    "--ensure-board",
                ]
            )
            result = adapter.materialize_ready_work_units(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertTrue(result["board_create_requested"])
        self.assertFalse(result["board_create_checked"])
        self.assertEqual(fake.calls, [])

    def test_materialize_ready_work_units_rejects_unsafe_plan(self) -> None:
        fake = FakeHermes()
        plan = single_ready_work_unit_plan()
        plan["tasks"][0]["dispatch_policy"]["dispatch_allowed_without_runtime_gate"] = True
        with tempfile.TemporaryDirectory() as tmp:
            plan_path = Path(tmp) / "plan.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--dry-run",
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "invalid ready work-unit Hermes materialization plan"):
                adapter.materialize_ready_work_units(args, runner=fake)

        self.assertEqual(fake.calls, [])

    def test_materialize_ready_work_units_rejects_pre_dispatch_activity(self) -> None:
        fake = UnsafePromotionHermes()
        plan = single_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness = tmp_path / "route-readiness.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness, extra_workers=["implementation-worker"])
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness),
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "pre-dispatch activity"):
                adapter.materialize_ready_work_units(args, runner=fake)

        dispatch_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "dispatch"]
        self.assertEqual(dispatch_calls, [])

    def test_release_ready_work_units_unblocks_verified_tasks_without_dispatch(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            result = adapter.release_ready_work_units(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["mode"], "release-ready-work-units")
        self.assertFalse(result["dry_run"])
        self.assertEqual(result["released_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        task_id = next(iter(fake.tasks))
        self.assertEqual(fake.tasks[task_id]["status"], "ready")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        dispatch_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "dispatch"]
        self.assertEqual(len(unblock_calls), 1)
        self.assertIn("runtime_gate=blocked_event_verified_for_each_task", unblock_calls[0][-1])
        self.assertEqual(dispatch_calls, [])
        self.assertFalse(result["runtime_gate"]["dispatch_allowed_by_this_step"])
        self.assertTrue(result["runtime_gate"]["native_dispatch_required_next"])

    def test_release_ready_work_units_dry_run_verifies_without_unblock(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--dry-run",
                ]
            )
            result = adapter.release_ready_work_units(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertEqual(result["released_ready_work_unit_task_ids"], {})
        task_id = next(iter(fake.tasks))
        self.assertEqual(fake.tasks[task_id]["status"], "blocked")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(unblock_calls, [])

    def test_close_reviewed_ready_work_units_completes_passed_reviewed_unit(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_pass",
                parent_task_id=parent_task_id,
            )

            dry_run_args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--dry-run",
                ]
            )
            dry_run = adapter.close_reviewed_ready_work_units(dry_run_args, runner=fake)
            close_args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            result = adapter.close_reviewed_ready_work_units(close_args, runner=fake)

        assert_live_adapter_result_schema(self, dry_run)
        assert_live_adapter_result_schema(self, result)
        self.assertTrue(dry_run["dry_run"])
        self.assertEqual(dry_run["runtime_gate"]["complete_candidate_count"], 1)
        self.assertEqual(dry_run["completed_ready_work_unit_task_ids"], {})
        self.assertEqual(result["mode"], "close-reviewed-ready-work-units")
        self.assertEqual(result["completed_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(fake.tasks[parent_task_id]["status"], "done")
        self.assertFalse(result["runtime_gate"]["dispatch_allowed_by_this_step"])
        self.assertFalse(result["runtime_gate"]["complete_product_claim_allowed"])
        complete_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "complete"]
        dispatch_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "dispatch"]
        self.assertEqual(len(complete_calls), 1)
        self.assertEqual(dispatch_calls, [])

    def test_close_reviewed_ready_work_units_ignores_stale_or_mismatched_review(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_stale",
                parent_task_id=parent_task_id,
                target_override="t_other_parent",
            )

            args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--dry-run",
                ]
            )
            result = adapter.close_reviewed_ready_work_units(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["runtime_gate"]["complete_candidate_count"], 0)
        self.assertEqual(result["runtime_gate"]["awaiting_review_count"], 1)
        self.assertEqual(result["reviewed_ready_work_unit_closeout"]["work-unit-001"]["decision"], "awaiting_review")
        self.assertEqual(fake.tasks[parent_task_id]["status"], "blocked")

    def test_close_reviewed_ready_work_units_keeps_block_or_human_gate_blocked(self) -> None:
        for review_task_id, verdict, blocking, human_gate, expected_count in [
            ("t_review_block", "BLOCK", True, False, "blocked_review_count"),
            ("t_review_human", "PASS", False, True, "human_gate_required_count"),
        ]:
            fake = FakeHermes()
            with tempfile.TemporaryDirectory() as tmp:
                tmp_path = Path(tmp)
                _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                    fake=fake,
                    tmp_path=tmp_path,
                )
                release_args = adapter.build_parser().parse_args(
                    [
                        "release-ready-work-units",
                        "--plan",
                        str(plan_path),
                        "--materialization-result",
                        str(materialization_result_path),
                        "--route-readiness",
                        str(readiness_path),
                    ]
                )
                adapter.release_ready_work_units(release_args, runner=fake)
                parent_task_id = ready_work_unit_task_ids(fake)[0]
                block_ready_work_unit_after_release(fake, parent_task_id)
                add_ready_work_unit_review_run(
                    fake,
                    review_task_id=review_task_id,
                    parent_task_id=parent_task_id,
                    verdict=verdict,
                    blocking_findings=blocking,
                    human_gate_required=human_gate,
                )

                args = adapter.build_parser().parse_args(
                    [
                        "close-reviewed-ready-work-units",
                        "--plan",
                        str(plan_path),
                        "--materialization-result",
                        str(materialization_result_path),
                        "--dry-run",
                    ]
                )
                result = adapter.close_reviewed_ready_work_units(args, runner=fake)

            assert_live_adapter_result_schema(self, result)
            self.assertEqual(result["runtime_gate"]["complete_candidate_count"], 0)
            self.assertEqual(result["runtime_gate"][expected_count], 1)
            self.assertEqual(result["completed_ready_work_unit_task_ids"], {})
            self.assertEqual(fake.tasks[parent_task_id]["status"], "blocked")

    def test_close_product_creation_run_routes_release_readiness_without_product_claim(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_pass",
                parent_task_id=parent_task_id,
            )
            close_reviewed_args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            adapter.close_reviewed_ready_work_units(close_reviewed_args, runner=fake)

            dry_run_args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--dry-run",
                ]
            )
            dry_run = adapter.close_product_creation_run(dry_run_args, runner=fake)
            close_args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            result = adapter.close_product_creation_run(close_args, runner=fake)

        assert_live_adapter_result_schema(self, dry_run)
        assert_product_creation_closeout_schema(self, dry_run)
        assert_live_adapter_result_schema(self, result)
        assert_product_creation_closeout_schema(self, result)
        self.assertEqual(dry_run["product_creation_run_closeout"]["next_action"], "release_readiness_required")
        self.assertFalse(dry_run["product_creation_run_closeout"]["complete_product_claim_allowed"])
        self.assertEqual(dry_run["product_creation_next_route_task_ids"], {})
        self.assertEqual(result["product_creation_next_route_task_ids"], {"release_readiness_required": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["runtime_gate"]["next_route_task_created_count"], 1)
        self.assertFalse(result["runtime_gate"]["dispatch_allowed_by_this_step"])
        self.assertFalse(result["runtime_gate"]["complete_product_claim_allowed"])
        route_tasks = [
            task
            for task in fake.tasks.values()
            if "product_creation_run_closeout_next_action" in str(task.get("body") or "")
        ]
        self.assertEqual(len(route_tasks), 1)
        self.assertEqual(route_tasks[0]["status"], "blocked")
        closeout_create_calls = [
            call
            for call in fake.calls
            if len(call) >= 5
            and call[4] == "create"
            and "OF product creation closeout next gate" in call[5]
        ]
        self.assertEqual(len(closeout_create_calls), 1)
        self.assertNotIn("--assignee", closeout_create_calls[0])
        closeout_assign_calls = [
            call
            for call in fake.calls
            if len(call) >= 7 and call[4] == "assign" and call[6] == "release-ops-worker"
        ]
        self.assertEqual(len(closeout_assign_calls), 1)
        dispatch_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "dispatch"]
        self.assertEqual(dispatch_calls, [])

    def test_close_product_creation_run_routes_learnback_with_worker_contract(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_pass",
                parent_task_id=parent_task_id,
            )
            close_reviewed_args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            adapter.close_reviewed_ready_work_units(close_reviewed_args, runner=fake)
            close_args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--release-readiness-ref",
                    "external:public-release-readiness-reviewed",
                    "--product-delivery-ref",
                    "external:public-product-delivery-reviewed",
                ]
            )
            result = adapter.close_product_creation_run(close_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_product_creation_closeout_schema(self, result)
        self.assertEqual(result["product_creation_run_closeout"]["next_action"], "learnback_required")
        route_tasks = [
            task
            for task in fake.tasks.values()
            if "product_creation_run_closeout_next_action" in str(task.get("body") or "")
        ]
        self.assertEqual(len(route_tasks), 1)
        body = json.loads(str(route_tasks[0]["body"]))
        self.assertEqual(body["next_action"], "learnback_required")
        self.assertEqual(route_tasks[0]["assignee"], "skill-eval-distiller")
        self.assertIn("done_definition", body)
        self.assertIn("source_refs", body)
        self.assertIn("evidence_expected", body)
        self.assertIn("forbidden_actions", body)
        self.assertIn("output_contract", body)
        self.assertEqual(body["public_private_boundary"]["raw_private_evidence_embedded"], False)
        self.assertFalse(body["complete_product_claim_allowed"])
        self.assertFalse(body["dispatch_allowed_by_this_step"])

    def test_close_product_creation_run_routes_missing_product_promotion_gate_explicitly(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_pass",
                parent_task_id=parent_task_id,
            )
            close_reviewed_args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            adapter.close_reviewed_ready_work_units(close_reviewed_args, runner=fake)
            close_args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--release-readiness-ref",
                    "external:public-release-readiness-reviewed",
                    "--learnback-ref",
                    "external:public-learnback-reviewed",
                    "--product-delivery-ref",
                    "external:public-product-delivery-reviewed",
                ]
            )
            result = adapter.close_product_creation_run(close_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_product_creation_closeout_schema(self, result)
        self.assertEqual(result["product_creation_run_closeout"]["next_action"], "product_promotion_gate_required")
        self.assertEqual(
            result["product_creation_next_route_task_ids"],
            {"product_promotion_gate_required": adapter.PUBLIC_SAFE_KANBAN_REF},
        )
        route_tasks = [
            task
            for task in fake.tasks.values()
            if "product_creation_run_closeout_next_action" in str(task.get("body") or "")
        ]
        self.assertEqual(len(route_tasks), 1)
        body = json.loads(str(route_tasks[0]["body"]))
        self.assertEqual(body["next_action"], "product_promotion_gate_required")
        self.assertEqual(route_tasks[0]["assignee"], "factory-orchestrator")
        self.assertIn("explicit product promotion human gate", " ".join(body["done_definition"]))
        self.assertIn("product_promotion_gate_ref", body["output_contract"]["pass_requires"])
        self.assertFalse(body["complete_product_claim_allowed"])
        self.assertFalse(body["dispatch_allowed_by_this_step"])

    def test_close_product_creation_run_requires_material_product_proof_before_promotion_gate(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_pass",
                parent_task_id=parent_task_id,
            )
            close_reviewed_args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            adapter.close_reviewed_ready_work_units(close_reviewed_args, runner=fake)
            close_args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--release-readiness-ref",
                    "external:public-release-readiness-reviewed",
                    "--learnback-ref",
                    "external:public-learnback-reviewed",
                ]
            )
            result = adapter.close_product_creation_run(close_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_product_creation_closeout_schema(self, result)
        self.assertEqual(result["product_creation_run_closeout"]["next_action"], "material_product_execution_required")
        route_tasks = [
            task
            for task in fake.tasks.values()
            if "product_creation_run_closeout_next_action" in str(task.get("body") or "")
        ]
        self.assertEqual(len(route_tasks), 1)
        body = json.loads(str(route_tasks[0]["body"]))
        self.assertEqual(body["next_action"], "material_product_execution_required")
        self.assertEqual(route_tasks[0]["assignee"], "factory-orchestrator")
        self.assertIn("product_delivery_ref", body["output_contract"]["pass_requires"])
        self.assertIn("Product Face Result", " ".join(body["evidence_expected"]))
        self.assertFalse(body["complete_product_claim_allowed"])
        graph_contract = body["material_product_execution_graph_contract"]
        self.assertEqual(graph_contract["materialization_protocol"], "create-unassigned-default-block-assign-v2")
        self.assertTrue(graph_contract["deterministic_graph_required"])
        self.assertTrue(graph_contract["blocked_event_required_before_any_worker_dispatch"])
        self.assertEqual(
            graph_contract["required_nodes"],
            [
                "execution_packet",
                "implementation",
                "product_face_result",
                "qa_verification",
                "public_safety_gate",
                "appsec_gate",
                "independent_review",
                "delivery_handoff",
                "post_handoff_closeout_reconciliation",
            ],
        )
        self.assertIn(
            {"from": "execution_packet", "to": "implementation"},
            graph_contract["required_edges"],
        )
        self.assertIn(
            {"from": "independent_review", "to": "delivery_handoff"},
            graph_contract["required_edges"],
        )
        self.assertIn(
            {"from": "delivery_handoff", "to": "post_handoff_closeout_reconciliation"},
            graph_contract["required_edges"],
        )
        implementation_authority = graph_contract["node_authority_rules"]["implementation"]
        self.assertIn("build_or_repair_scoped_artifact", implementation_authority["allowed_after_runtime_gate"])
        self.assertIn("implement_product", implementation_authority["forbidden_actions_must_not_include"])
        self.assertEqual(
            implementation_authority["replacement_for_broad_implementation_forbid"],
            "implement_product_outside_scope",
        )
        self.assertIn("blocked_dependency_graph_ref", body["output_contract"]["pass_requires"])
        self.assertIn("no_spawn_readback_evidence", body["output_contract"]["pass_requires"])
        self.assertIn("create_loose_material_product_tasks", body["forbidden_actions"])
        self.assertIn("create_todo_or_ready_material_product_tasks", body["forbidden_actions"])

    def test_material_product_execution_graph_requires_post_handoff_closeout_route(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_pass",
                parent_task_id=parent_task_id,
            )
            close_reviewed_args = adapter.build_parser().parse_args(
                [
                    "close-reviewed-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            adapter.close_reviewed_ready_work_units(close_reviewed_args, runner=fake)
            close_args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--release-readiness-ref",
                    "external:public-release-readiness-reviewed",
                    "--learnback-ref",
                    "external:public-learnback-reviewed",
                ]
            )
            result = adapter.close_product_creation_run(close_args, runner=fake)

        self.assertEqual(result["product_creation_run_closeout"]["next_action"], "material_product_execution_required")
        route_task = next(
            task
            for task in fake.tasks.values()
            if "product_creation_run_closeout_next_action" in str(task.get("body") or "")
        )
        body = json.loads(str(route_task["body"]))
        graph_contract = body["material_product_execution_graph_contract"]
        self.assertIn("post_handoff_closeout_reconciliation", graph_contract["required_nodes"])
        self.assertIn(
            {"from": "delivery_handoff", "to": "post_handoff_closeout_reconciliation"},
            graph_contract["required_edges"],
        )
        self.assertIn(
            "post_material_handoff_closeout_route_ref",
            body["output_contract"]["pass_requires"],
        )
        self.assertIn(
            "after material delivery handoff PASS, emit an explicit closeout next route",
            body["done_definition"],
        )

    def test_close_product_creation_run_blocks_when_work_unit_review_blocks(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            parent_task_id = ready_work_unit_task_ids(fake)[0]
            block_ready_work_unit_after_release(fake, parent_task_id)
            add_ready_work_unit_review_run(
                fake,
                review_task_id="t_review_block",
                parent_task_id=parent_task_id,
                verdict="BLOCK",
                blocking_findings=True,
            )

            args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--dry-run",
                ]
            )
            result = adapter.close_product_creation_run(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_product_creation_closeout_schema(self, result)
        self.assertEqual(result["product_creation_run_closeout"]["next_action"], "repair_required")
        self.assertEqual(result["runtime_gate"]["blocker_count"], 1)
        self.assertEqual(result["product_creation_run_closeout"]["work_units"]["work-unit-001"]["decision"], "repair_required")
        self.assertEqual(result["product_creation_next_route_task_ids"], {})

    def test_close_product_creation_run_fails_closed_on_ambiguous_duplicate_task(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, _readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            original_task_id = ready_work_unit_task_ids(fake)[0]
            duplicate = copy.deepcopy(fake.tasks[original_task_id])
            duplicate["id"] = "t_duplicate"
            duplicate["status"] = "done"
            fake.tasks["t_duplicate"] = duplicate

            args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--dry-run",
                ]
            )
            result = adapter.close_product_creation_run(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_product_creation_closeout_schema(self, result)
        row = result["product_creation_run_closeout"]["work_units"]["work-unit-001"]
        self.assertEqual(row["decision"], "blocked_with_owner")
        self.assertEqual(row["active_task_count"], 2)
        self.assertEqual(result["product_creation_run_closeout"]["next_action"], "blocked_with_owner")

    def test_close_product_creation_run_rejects_private_release_ref(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, _readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            write_single_product_creation_plan(product_creation_plan_path)
            private_ref = "C:" + "\\private\\release-readiness.json"
            args = adapter.build_parser().parse_args(
                [
                    "close-product-creation-run",
                    "--product-creation-plan",
                    str(product_creation_plan_path),
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--release-readiness-ref",
                    private_ref,
                    "--dry-run",
                ]
            )
            with self.assertRaisesRegex(RuntimeError, "release_readiness_ref must be public-safe"):
                adapter.close_product_creation_run(args, runner=fake)

    def test_close_release_readiness_review_pass_completes_parent_without_promotion(self) -> None:
        fake = FakeHermes()
        parent_id = add_release_readiness_parent(fake)
        review_id = RELEASE_REVIEW_PASS_TASK_ID
        add_release_readiness_review_run(fake, review_task_id=review_id, parent_task_id=parent_id)

        dry_run_args = adapter.build_parser().parse_args(
            [
                "close-release-readiness-review",
                "--board",
                TEST_BOARD,
                "--parent-task",
                parent_id,
                "--review-task",
                review_id,
                "--dry-run",
            ]
        )
        dry_run = adapter.close_release_readiness_review(dry_run_args, runner=fake)
        args = adapter.build_parser().parse_args(
            [
                "close-release-readiness-review",
                "--board",
                TEST_BOARD,
                "--parent-task",
                parent_id,
                "--review-task",
                review_id,
            ]
        )
        result = adapter.close_release_readiness_review(args, runner=fake)

        assert_live_adapter_result_schema(self, dry_run)
        assert_live_adapter_result_schema(self, result)
        assert_release_readiness_closeout_schema(self, dry_run)
        assert_release_readiness_closeout_schema(self, result)
        self.assertEqual(dry_run["release_readiness_review_closeout"]["decision"], "release_readiness_review_passed")
        self.assertEqual(dry_run["completed_release_readiness_task_ids"], {})
        self.assertEqual(result["completed_release_readiness_task_ids"], {"release_readiness": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(fake.tasks[parent_id]["status"], "done")
        self.assertFalse(result["release_readiness_review_closeout"]["production_promotion_allowed"])
        self.assertFalse(result["release_readiness_review_closeout"]["complete_product_claim_allowed"])
        self.assertFalse(result["runtime_gate"]["dispatch_allowed_by_this_step"])

    def test_close_release_readiness_review_missing_parent_edge_fails_closed_by_default(self) -> None:
        fake = FakeHermes()
        parent_id = add_release_readiness_parent(fake)
        review_id = RELEASE_REVIEW_ORPHAN_TASK_ID
        add_release_readiness_review_run(
            fake,
            review_task_id=review_id,
            parent_task_id=parent_id,
            durable_edge=False,
        )
        args = adapter.build_parser().parse_args(
            [
                "close-release-readiness-review",
                "--board",
                TEST_BOARD,
                "--parent-task",
                parent_id,
                "--review-task",
                review_id,
            ]
        )
        result = adapter.close_release_readiness_review(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_release_readiness_closeout_schema(self, result)
        self.assertEqual(result["release_readiness_review_closeout"]["decision"], "missing_durable_parent_edge")
        self.assertEqual(result["completed_release_readiness_task_ids"], {})
        self.assertEqual(fake.tasks[parent_id]["status"], "blocked")

    def test_close_release_readiness_review_can_repair_missing_parent_edge_before_complete(self) -> None:
        fake = FakeHermes()
        parent_id = add_release_readiness_parent(fake)
        review_id = RELEASE_REVIEW_REPAIR_EDGE_TASK_ID
        add_release_readiness_review_run(
            fake,
            review_task_id=review_id,
            parent_task_id=parent_id,
            durable_edge=False,
        )
        args = adapter.build_parser().parse_args(
            [
                "close-release-readiness-review",
                "--board",
                TEST_BOARD,
                "--parent-task",
                parent_id,
                "--review-task",
                review_id,
                "--repair-missing-parent-edge",
            ]
        )
        result = adapter.close_release_readiness_review(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_release_readiness_closeout_schema(self, result)
        self.assertEqual(result["release_readiness_review_closeout"]["decision"], "release_readiness_review_passed")
        self.assertTrue(result["release_readiness_review_closeout"]["parent_edge_repaired"])
        self.assertIn(review_id, fake.tasks[parent_id].get("parents", []))
        self.assertEqual(fake.tasks[parent_id]["status"], "done")

    def test_close_release_readiness_review_block_keeps_parent_blocked_with_repair_route(self) -> None:
        fake = FakeHermes()
        parent_id = add_release_readiness_parent(fake)
        review_id = RELEASE_REVIEW_BLOCK_TASK_ID
        add_release_readiness_review_run(
            fake,
            review_task_id=review_id,
            parent_task_id=parent_id,
            verdict="BLOCK",
            blocking_findings=True,
        )
        args = adapter.build_parser().parse_args(
            [
                "close-release-readiness-review",
                "--board",
                TEST_BOARD,
                "--parent-task",
                parent_id,
                "--review-task",
                review_id,
            ]
        )
        result = adapter.close_release_readiness_review(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        assert_release_readiness_closeout_schema(self, result)
        self.assertEqual(result["release_readiness_review_closeout"]["decision"], "repair_required")
        self.assertEqual(result["runtime_gate"]["blocked_review_count"], 1)
        self.assertEqual(result["completed_release_readiness_task_ids"], {})
        self.assertEqual(fake.tasks[parent_id]["status"], "blocked")

    def test_release_ready_work_units_rejects_pre_dispatch_activity(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            task_id = next(iter(fake.tasks))
            fake.tasks[task_id].setdefault("events", []).append({"kind": "claimed"})
            args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "pre-dispatch activity"):
                adapter.release_ready_work_units(args, runner=fake)

        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(unblock_calls, [])

    def test_recover_ready_work_units_plans_replacement_for_contaminated_task(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, _readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            task_id = next(iter(fake.tasks))
            fake.tasks[task_id].setdefault("events", []).append({"kind": "claimed"})
            create_call_count = len([call for call in fake.calls if len(call) >= 5 and call[4] == "create"])
            args = adapter.build_parser().parse_args(
                [
                    "recover-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            result = adapter.recover_ready_work_units(args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["mode"], "recover-ready-work-units")
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["runtime_gate"]["replacement_created_count"], 0)
        self.assertEqual(result["runtime_gate"]["superseded_task_count"], 1)
        self.assertEqual(result["recovery_plan"]["work-unit-001"]["status"], "replacement_planned")
        self.assertFalse(result["recovery_plan"]["work-unit-001"]["complete_product_claim_allowed"])
        self.assertEqual(len([call for call in fake.calls if len(call) >= 5 and call[4] == "create"]), create_call_count)
        self.assertFalse(any(adapter.READY_WORK_UNIT_SUPERSESSION_MARKER in body for body in task_comment_bodies(fake.tasks[task_id])))

    def test_recover_ready_work_units_creates_replacement_and_release_ignores_superseded_task(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            contaminated_task_id = next(iter(fake.tasks))
            fake.tasks[contaminated_task_id].setdefault("runs", []).append({"status": "reclaimed"})
            recover_args = adapter.build_parser().parse_args(
                [
                    "recover-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                    "--create-replacements",
                ]
            )
            recovery = adapter.recover_ready_work_units(recover_args, runner=fake)
            replacement_task_ids = [task_id for task_id in fake.tasks if task_id != contaminated_task_id]
            self.assertEqual(len(replacement_task_ids), 1)
            replacement_task_id = replacement_task_ids[0]

            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            release = adapter.release_ready_work_units(release_args, runner=fake)

        assert_live_adapter_result_schema(self, recovery)
        assert_live_adapter_result_schema(self, release)
        self.assertFalse(recovery["dry_run"])
        self.assertEqual(recovery["runtime_gate"]["replacement_created_count"], 1)
        self.assertEqual(recovery["runtime_gate"]["superseded_task_count"], 1)
        self.assertTrue(
            any(
                adapter.READY_WORK_UNIT_SUPERSESSION_MARKER in body
                for body in task_comment_bodies(fake.tasks[contaminated_task_id])
            )
        )
        self.assertEqual(fake.tasks[contaminated_task_id]["status"], "blocked")
        self.assertEqual(fake.tasks[replacement_task_id]["status"], "ready")
        self.assertEqual(release["released_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(len(unblock_calls), 1)

    def test_ready_work_unit_supersession_ignores_replacement_lineage_context(self) -> None:
        payload = {
            "comments": [
                {
                    "author": adapter.READY_WORK_UNIT_CONTEXT_CHUNK_AUTHOR,
                    "body": json.dumps(
                        {
                            "context_transport": adapter.READY_WORK_UNIT_CONTEXT_TRANSPORT_MODE,
                            "data": json.dumps(
                                {
                                    "runtime_lineage": {
                                        "lineage_type": "ready_work_unit_supersession",
                                        "supersession_marker": adapter.READY_WORK_UNIT_SUPERSESSION_MARKER,
                                    }
                                }
                            ),
                        }
                    ),
                }
            ]
        }
        self.assertFalse(adapter.task_has_ready_work_unit_supersession(payload))

        payload["comments"].append(
            {
                "author": adapter.READY_WORK_UNIT_RECOVERY_AUTHOR,
                "body": json.dumps({"marker": adapter.READY_WORK_UNIT_SUPERSESSION_MARKER}),
            }
        )
        self.assertTrue(adapter.task_has_ready_work_unit_supersession(payload))

    def test_recover_ready_work_units_repairs_incomplete_existing_replacement(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            contaminated_task_id = next(iter(fake.tasks))
            fake.tasks[contaminated_task_id].setdefault("runs", []).append({"status": "reclaimed"})
            replacement_task = adapter.replacement_ready_work_unit_task(
                plan_task=plan["tasks"][0],
                contaminated_task_ids=[contaminated_task_id],
                contamination_markers=["run:reclaimed"],
            )
            partial_replacement_task_id = adapter.create_ready_work_unit_task(
                hermes_bin="hermes",
                board=TEST_BOARD,
                task=replacement_task,
                worker_assignee_prefix="",
                workspace_ref="scratch",
                runner=fake,
            )
            fake.tasks[partial_replacement_task_id]["assignee"] = None
            recover_args = adapter.build_parser().parse_args(
                [
                    "recover-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                    "--create-replacements",
                ]
            )
            recovery = adapter.recover_ready_work_units(recover_args, runner=fake)

        assert_live_adapter_result_schema(self, recovery)
        self.assertEqual(recovery["runtime_gate"]["replacement_created_count"], 1)
        self.assertTrue(
            any(
                adapter.READY_WORK_UNIT_SUPERSESSION_MARKER in body
                for body in task_comment_bodies(fake.tasks[contaminated_task_id])
            )
        )
        partial_comments = fake.tasks[partial_replacement_task_id].get("comments", [])
        partial_repaired_or_superseded = (
            fake.tasks[partial_replacement_task_id]["assignee"] == "implementation-worker"
            or any(adapter.READY_WORK_UNIT_SUPERSESSION_MARKER in str(comment.get("body") or "") for comment in partial_comments)
        )
        self.assertTrue(partial_repaired_or_superseded)
        self.assertTrue(
            any(
                task_id != contaminated_task_id
                and str(task.get("assignee") or "") == "implementation-worker"
                and not adapter.task_has_ready_work_unit_supersession(task)
                for task_id, task in fake.tasks.items()
            )
        )

    def test_recover_ready_work_units_does_not_supersede_legally_released_blocked_first_wave(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            task_id = next(iter(fake.tasks))
            fake.tasks[task_id]["status"] = "blocked"
            fake.tasks[task_id].setdefault("events", []).append({"kind": "claimed"})
            fake.tasks[task_id].setdefault("runs", []).append({"status": "blocked", "outcome": "blocked"})
            recover_args = adapter.build_parser().parse_args(
                [
                    "recover-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            recovery = adapter.recover_ready_work_units(recover_args, runner=fake)

        assert_live_adapter_result_schema(self, recovery)
        self.assertEqual(recovery["runtime_gate"]["superseded_task_count"], 0)
        self.assertEqual(recovery["runtime_gate"]["clean_task_count"], 1)
        self.assertEqual(recovery["recovery_plan"]["work-unit-001"]["status"], "clean_no_recovery_needed")
        self.assertFalse(
            any(
                adapter.READY_WORK_UNIT_SUPERSESSION_MARKER in str(comment.get("body") or "")
                for comment in fake.tasks[task_id].get("comments", [])
            )
        )

    def test_release_ready_work_units_releases_only_first_dependency_wave(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            result = adapter.release_ready_work_units(release_args, runner=fake)

        self.assertEqual(result["released_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["release_wave"]["eligible_work_unit_ids"], ["work-unit-001"])
        self.assertEqual(result["release_wave"]["held_work_unit_ids"], ["work-unit-002"])
        self.assertEqual(result["release_wave"]["dependency_blockers"], {"work-unit-002": ["work-unit-001"]})
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(len(unblock_calls), 1)
        released_task = next(task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001")
        held_task = next(task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-002")
        self.assertEqual(released_task["status"], "ready")
        self.assertEqual(held_task["status"], "blocked")

    def test_release_ready_work_units_releases_downstream_after_dependency_done(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "done"
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            result = adapter.release_ready_work_units(release_args, runner=fake)

        self.assertEqual(result["released_ready_work_unit_task_ids"], {"work-unit-002": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["release_wave"]["eligible_work_unit_ids"], ["work-unit-002"])
        self.assertEqual(result["release_wave"]["satisfied_work_unit_ids"], ["work-unit-001"])
        self.assertEqual(result["release_wave"]["held_work_unit_ids"], [])
        queried_statuses = [
            call[call.index("--status") + 1]
            for call in fake.calls
            if len(call) >= 5 and call[4] == "list" and "--status" in call
        ]
        self.assertEqual(sorted(set(queried_statuses)), ["blocked", "done", "ready", "running", "todo"])
        self.assertNotIn("triage", queried_statuses)
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(len(unblock_calls), 1)
        released_task = next(task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-002")
        self.assertEqual(released_task["status"], "ready")

    def test_release_ready_work_units_reports_post_release_blocked_dependency(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_first_wave_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_first_wave_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "spawned"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            dry_run_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--dry-run",
                ]
            )
            result = adapter.release_ready_work_units(dry_run_args, runner=fake)

        self.assertEqual(result["released_ready_work_unit_task_ids"], {})
        self.assertEqual(result["release_wave"]["eligible_work_unit_ids"], [])
        self.assertEqual(result["release_wave"]["post_release_blocked_work_unit_ids"], ["work-unit-001"])
        self.assertEqual(result["release_wave"]["held_work_unit_ids"], ["work-unit-002"])
        self.assertEqual(result["release_wave"]["dependency_blockers"], {"work-unit-002": ["work-unit-001"]})
        self.assertEqual(result["runtime_gate"]["post_release_blocked_task_count"], 1)
        self.assertTrue(result["release_wave"]["post_release_reconciliation_required_next"])
        self.assertEqual(result["release_wave"]["post_release_reconciliation_command"], "reconcile-ready-work-units")

    def test_reconcile_ready_work_units_keeps_incomplete_repair_blocked(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            unblock_calls_before = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--dry-run",
                ]
            )
            result = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["mode"], "reconcile-ready-work-units")
        self.assertEqual(result["retry_ready_work_unit_task_ids"], {})
        self.assertEqual(result["completed_ready_work_unit_task_ids"], {})
        self.assertEqual(
            result["post_release_reconciliation"]["work-unit-001"]["decision"],
            "awaiting_repair_review",
        )
        self.assertEqual(result["release_wave"]["held_work_unit_ids"], ["work-unit-002"])
        self.assertEqual(result["release_wave"]["dependency_blockers"], {"work-unit-002": ["work-unit-001"]})
        self.assertEqual(result["runtime_gate"]["incomplete_repair_or_review_count"], 1)
        self.assertEqual(result["post_repair_review_required_work_unit_ids"], ["work-unit-001"])
        self.assertEqual(result["post_repair_review_task_ids"], {})
        self.assertTrue(result["post_release_reconciliation"]["work-unit-001"]["post_repair_review_required"])
        self.assertEqual(result["runtime_gate"]["post_repair_review_required_count"], 1)
        self.assertEqual(result["runtime_gate"]["post_repair_review_task_created_count"], 0)
        unblock_calls_after = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(unblock_calls_after, unblock_calls_before)

    def test_reconcile_ready_work_units_creates_post_repair_review_task(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--create-post-repair-review-tasks",
                ]
            )
            result = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["post_repair_review_required_work_unit_ids"], ["work-unit-001"])
        self.assertEqual(result["post_repair_review_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["runtime_gate"]["post_repair_review_task_created_count"], 1)
        review_tasks = [
            task
            for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("packet_type")
            == "ready_work_unit_post_repair_review_request"
        ]
        self.assertEqual(len(review_tasks), 1)
        self.assertEqual(review_tasks[0]["assignee"], "independent-reviewer")
        self.assertEqual(review_tasks[0]["status"], "ready")
        review_body = json.loads(str(review_tasks[0]["body"]))
        self.assertEqual(review_body["marker"], "ready_work_unit_post_repair_review_required")
        self.assertEqual(review_body["review_scope"], "post_repair_result_only")
        link_calls = [call for call in fake.calls if len(call) >= 7 and call[4] == "link"]
        self.assertTrue(link_calls)
        parent_comments = upstream_task.get("comments") or []
        self.assertTrue(
            any("ready_work_unit_post_repair_review_task_created" in str(comment.get("body")) for comment in parent_comments)
        )

    def test_reconcile_ready_work_units_fails_closed_when_review_dependency_edge_is_missing(self) -> None:
        fake = BrokenLinkHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--create-post-repair-review-tasks",
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "review dependency edge missing"):
                adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

    def test_reconcile_ready_work_units_infers_review_required_as_review_ready(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        plan["tasks"][0]["reviewer_role"] = "qa-verification-worker"
        plan["tasks"][0]["body_contract"]["reviewer_role"] = "qa-verification-worker"
        plan["tasks"][0]["body_contract"]["done_definition"]["reviewer_role"] = "qa-verification-worker"
        plan["tasks"][0]["body_contract"]["worker_input_contract"]["inputs"]["done_definition"][
            "reviewer_role"
        ] = "qa-verification-worker"
        plan["tasks"][0]["body_contract"]["work_unit_context_packet"]["worker_input_contract"]["inputs"][
            "done_definition"
        ]["reviewer_role"] = "qa-verification-worker"
        plan["tasks"][0]["body_contract"]["receipt_five_contract"]["reviewer_role"] = "qa-verification-worker"
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task["latest_summary"] = (
                "review-required: implementation completed with evidence refs and passing proof; "
                "qa-verification-worker must independently review before done."
            )
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "review-required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "implementation-worker",
                    "body": "Receipt Five: evidence refs PASS; artifacts implemented; review-required before completion.",
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--create-post-repair-review-tasks",
                ]
            )
            result = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        row = result["post_release_reconciliation"]["work-unit-001"]
        self.assertEqual(row["decision"], "awaiting_repair_review")
        self.assertTrue(row["repair_completed_inferred_from_review_required"])
        self.assertFalse(row["repair_completed_explicit"])
        self.assertEqual(result["post_repair_review_required_work_unit_ids"], ["work-unit-001"])
        self.assertEqual(result["runtime_gate"]["post_repair_review_task_created_count"], 1)
        review_tasks = [
            task
            for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("packet_type")
            == "ready_work_unit_post_repair_review_request"
        ]
        self.assertEqual(len(review_tasks), 1)
        self.assertEqual(review_tasks[0]["assignee"], "qa-verification-worker")
        review_body = json.loads(str(review_tasks[0]["body"]))
        self.assertEqual(review_body["reviewer_role"], "qa-verification-worker")

    def test_reconcile_ready_work_units_releases_next_wave_after_completion(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_id, upstream_task = next(
                (task_id, task)
                for task_id, task in fake.tasks.items()
                if json.loads(str(task["body"]))["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "review-required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "implementation-worker",
                    "body": "ready_work_unit_repair_completed with Receipt Five evidence and proof PASS.",
                }
            )
            fake.tasks["review-fixture-complete"] = {
                "id": "review-fixture-complete",
                "status": "done",
                "title": "OF independent review: complete parent",
                "assignee": "independent-reviewer",
                "events": [],
                "comments": [],
                "runs": [
                    {
                        "id": 2,
                        "profile": "independent-reviewer",
                        "status": "done",
                        "outcome": "completed",
                        "ended_at": 20,
                        "metadata": {
                            "marker": adapter.READY_WORK_UNIT_POST_REPAIR_REVIEW_RESULT_MARKER,
                            "parent_task_ref": upstream_id,
                            "parent_work_unit_id": "work-unit-001",
                            "reviewed_repair_card": "repair-fixture-complete",
                            "review_scope": "post_repair_result_only",
                            "validation_result": "PASS",
                            "blocking_findings": False,
                            "ready_work_unit_repair_review_passed": True,
                            "ready_work_unit_done_authorized": True,
                            "ready_work_unit_done_definition_satisfied": True,
                            "no_forbidden_approvals": {
                                "implementation": False,
                                "release": False,
                                "deploy": False,
                                "complete_product": False,
                                "product_face": False,
                                "security_onchain_waiver": False,
                                "customer_ready": False,
                                "mainnet_irreversible": False,
                                "human_gate": False,
                            },
                        },
                    }
                ],
            }
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            result = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)
            downstream_task = next(
                task
                for task in fake.tasks.values()
                if json.loads(str(task["body"]))["work_unit_id"] == "work-unit-002"
            )

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["completed_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(
            result["followup_release_result"]["released_ready_work_unit_task_ids"],
            {"work-unit-002": adapter.PUBLIC_SAFE_KANBAN_REF},
        )
        self.assertEqual(result["runtime_gate"]["followup_release_task_count"], 1)
        self.assertTrue(result["runtime_gate"]["native_dispatch_required_next"])
        self.assertEqual(downstream_task["status"], "ready")

    def test_post_repair_tasks_include_explicit_phase_risk_and_surfaces_contract(self) -> None:
        plan = two_step_ready_work_unit_plan()
        plan_task = plan["tasks"][0]

        review_body = adapter.ready_work_unit_post_repair_review_body(
            plan_task=plan_task,
            parent_task_id="t_parent",
            packet_id="ready-work-unit-packet-work-unit-001",
            work_unit_id="work-unit-001",
        )
        authority_body = adapter.ready_work_unit_post_repair_authority_body(
            parent_task_id="t_parent",
            packet_id="ready-work-unit-packet-work-unit-001",
            work_unit_id="work-unit-001",
            review_result={
                "review_task_ref": "t_review",
                "repair_task_ref": "t_repair",
                "marker": "ready_work_unit_repair_review_passed",
                "status": "PASS",
            },
            plan_task=plan_task,
        )

        for body in (review_body, authority_body):
            self.assertEqual(body["phase"], "F15")
            self.assertEqual(body["risk_effective"], "R2")
            self.assertEqual(
                body["surfaces"],
                ["complete product scope", "release path", "rollback", "monitoring", "support", "customer readiness"],
            )
            self.assertEqual(body["route_repair_contract"]["phase"], "F15")
            self.assertEqual(body["route_repair_contract"]["risk_effective"], "R2")
            self.assertIn("phase", body["route_repair_contract"]["required_card_fields"])
            self.assertIn("risk_effective", body["route_repair_contract"]["required_card_fields"])
            self.assertIn("surfaces", body["route_repair_contract"]["required_card_fields"])

    def test_reconcile_ready_work_units_reuses_existing_post_repair_review_task(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--create-post-repair-review-tasks",
                ]
            )
            first = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)
            second = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        assert_live_adapter_result_schema(self, second)
        self.assertEqual(first["runtime_gate"]["post_repair_review_task_created_count"], 1)
        self.assertEqual(second["post_repair_review_required_work_unit_ids"], ["work-unit-001"])
        self.assertEqual(second["post_repair_review_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(second["existing_post_repair_review_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(second["created_post_repair_review_task_ids"], {})
        self.assertEqual(second["runtime_gate"]["post_repair_review_required_count"], 1)
        self.assertEqual(second["runtime_gate"]["post_repair_review_missing_task_count"], 0)
        self.assertEqual(second["runtime_gate"]["post_repair_review_existing_task_count"], 1)
        self.assertEqual(second["runtime_gate"]["post_repair_review_task_created_count"], 0)
        review_tasks = [
            task
            for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("packet_type")
            == "ready_work_unit_post_repair_review_request"
        ]
        self.assertEqual(len(review_tasks), 1)

    def test_reconcile_ready_work_units_consumes_versioned_post_repair_review_run_metadata(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_id, upstream_task = next(
                (task_id, task)
                for task_id, task in fake.tasks.items()
                if json.loads(str(task["body"]))["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--create-post-repair-review-tasks",
                ]
            )
            first = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)
            stale_review_task_id = next(
                task_id
                for task_id, task in fake.tasks.items()
                if json.loads(str(task.get("body") or "{}")).get("packet_type")
                == "ready_work_unit_post_repair_review_request"
            )
            fake.tasks[stale_review_task_id]["status"] = "blocked"
            fake.tasks["review-fixture-v2"] = {
                "id": "review-fixture-v2",
                "status": "done",
                "title": "OF independent review: versioned repair result",
                "assignee": "independent-reviewer",
                "events": [],
                "comments": [],
                "runs": [
                    {
                        "id": 2,
                        "profile": "independent-reviewer",
                        "status": "done",
                        "outcome": "completed",
                        "ended_at": 20,
                        "metadata": {
                            "validation_result": "PASS",
                            "blocking_findings": False,
                            "reviewed_repair_card": "repair-fixture-v2",
                            "review_scope": "graph-repair evidence and live Kanban readback only",
                            "live_readback": {
                                "parent": {"id": upstream_id, "status": "blocked"},
                                "clean_replacements": [],
                            },
                            "no_forbidden_approvals": {
                                "implementation": False,
                                "release": False,
                                "deploy": False,
                                "complete_product": False,
                                "product_face": False,
                                "security_onchain_waiver": False,
                                "customer_ready": False,
                                "mainnet_irreversible": False,
                                "human_gate": False,
                            },
                        },
                    }
                ],
            }
            second = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)
            authority_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--create-post-repair-authority-tasks",
                ]
            )
            third = adapter.reconcile_ready_work_units(authority_args, runner=fake)
            fourth = adapter.reconcile_ready_work_units(authority_args, runner=fake)
            authority_task_id, authority_task = next(
                (task_id, task)
                for task_id, task in fake.tasks.items()
                if json.loads(str(task.get("body") or "{}")).get("packet_type")
                == "ready_work_unit_post_repair_authority_request"
            )
            authority_task["status"] = "done"
            authority_task["runs"] = [
                {
                    "id": 3,
                    "profile": "independent-reviewer",
                    "status": "done",
                    "outcome": "completed",
                    "ended_at": 30,
                    "metadata": {
                        "independent_review_result": {
                            "verdict": "PASS_REPAIR_REVIEW_ACCEPTED_RETRY_AUTHORIZED_ONLY",
                            "selected_markers": [
                                "ready_work_unit_repair_review_passed",
                                "ready_work_unit_retry_authorized",
                            ],
                            "not_authorized": [
                                "ready_work_unit_done_authorized",
                                "ready_work_unit_done_definition_satisfied",
                                "complete_product_done",
                                "implementation",
                                "release",
                                "deploy",
                                "product_face",
                                "security_onchain_waiver",
                                "customer_ready",
                                "mainnet_irreversible",
                                "human_gate",
                            ],
                        }
                    },
                }
            ]
            upstream_task["status"] = "todo"
            fifth = adapter.reconcile_ready_work_units(authority_args, runner=fake)
            upstream_status_after_retry = str(fake.tasks[upstream_id].get("status") or "")
            upstream_parents_after_retry = [str(parent_id) for parent_id in fake.tasks[upstream_id].get("parents", [])]
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "post-retry review required"})
            fake.tasks["review-fixture-v3"] = {
                "id": "review-fixture-v3",
                "status": "done",
                "title": "OF independent review: post-retry owner result",
                "assignee": "independent-reviewer",
                "events": [],
                "comments": [],
                "runs": [
                    {
                        "id": 4,
                        "profile": "independent-reviewer",
                        "status": "done",
                        "outcome": "completed",
                        "ended_at": 40,
                        "metadata": {
                            "independent_review_result": {
                                "verdict": "PASS_ACCEPT_WU1_POST_REPAIR_DECOMPOSITION_EVIDENCE_ONLY",
                                "review_target": upstream_id,
                                "blocking_findings": False,
                                "remaining_risk": [
                                    "review accepts owner evidence only",
                                    "downstream execution still needs a fresh authority decision",
                                ],
                            },
                        },
                    }
                ],
            }
            observe_after_new_review_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            sixth = adapter.reconcile_ready_work_units(observe_after_new_review_args, runner=fake)
            seventh = adapter.reconcile_ready_work_units(authority_args, runner=fake)
            _fresh_authority_task_id, fresh_authority_task = next(
                (task_id, task)
                for task_id, task in fake.tasks.items()
                if json.loads(str(task.get("body") or "{}")).get("packet_type")
                == "ready_work_unit_post_repair_authority_request"
                and json.loads(str(task.get("body") or "{}")).get("review_task_ref") == "review-fixture-v3"
            )
            fresh_authority_task["status"] = "done"
            fresh_authority_task["runs"] = [
                {
                    "id": 5,
                    "profile": "independent-reviewer",
                    "status": "done",
                    "outcome": "completed",
                    "ended_at": 50,
                    "metadata": {
                        "independent_review_result": {
                            "verdict": "PASS_WU1_DONE_DEFINITION_SATISFIED_AUTHORITY_DONE_ONLY",
                            "authority_decision": {
                                "selected_markers": [
                                    "ready_work_unit_done_authorized",
                                    "ready_work_unit_done_definition_satisfied",
                                ],
                                "rejected_markers": [
                                    "ready_work_unit_retry_authorized",
                                    "human_gate_required",
                                    "structured_block",
                                ],
                            },
                        }
                    },
                }
            ]
            dry_after_fresh_authority_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--dry-run",
                ]
            )
            eighth = adapter.reconcile_ready_work_units(dry_after_fresh_authority_args, runner=fake)

        assert_live_adapter_result_schema(self, second)
        assert_live_adapter_result_schema(self, third)
        assert_live_adapter_result_schema(self, fourth)
        assert_live_adapter_result_schema(self, fifth)
        assert_live_adapter_result_schema(self, sixth)
        assert_live_adapter_result_schema(self, seventh)
        assert_live_adapter_result_schema(self, eighth)
        self.assertEqual(first["runtime_gate"]["post_repair_review_task_created_count"], 1)
        row = second["post_release_reconciliation"]["work-unit-001"]
        self.assertEqual(row["decision"], "awaiting_retry_or_done_authority")
        self.assertTrue(row["repair_review_passed"])
        self.assertFalse(row["retry_authorized"])
        self.assertFalse(row["done_authorized"])
        self.assertEqual(row["post_repair_review_result"]["source"], "hermes_run_metadata")
        self.assertEqual(row["post_repair_review_task_ref"], "review-fixture-v2")
        self.assertEqual(second["post_repair_review_required_work_unit_ids"], [])
        self.assertEqual(second["created_post_repair_review_task_ids"], {})
        self.assertEqual(second["runtime_gate"]["post_repair_review_result_count"], 1)
        self.assertEqual(second["runtime_gate"]["post_repair_review_missing_task_count"], 0)
        self.assertEqual(second["runtime_gate"]["post_repair_authority_required_count"], 1)
        self.assertEqual(second["runtime_gate"]["post_repair_authority_missing_task_count"], 1)
        self.assertEqual(second["runtime_gate"]["post_repair_authority_task_created_count"], 0)
        self.assertEqual(third["created_post_repair_authority_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(third["runtime_gate"]["post_repair_authority_task_created_count"], 1)
        self.assertEqual(fourth["created_post_repair_authority_task_ids"], {})
        self.assertEqual(fourth["existing_post_repair_authority_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(fourth["runtime_gate"]["post_repair_authority_existing_task_count"], 1)
        self.assertEqual(fourth["runtime_gate"]["post_repair_authority_missing_task_count"], 0)
        retry_row = fifth["post_release_reconciliation"]["work-unit-001"]
        self.assertEqual(retry_row["decision"], "retry_parent")
        self.assertEqual(retry_row["post_repair_authority_result"]["source"], "hermes_run_metadata")
        self.assertTrue(retry_row["repair_review_passed"])
        self.assertTrue(retry_row["retry_authorized"])
        self.assertFalse(retry_row["done_authorized"])
        self.assertEqual(retry_row["post_repair_authority_task_ref"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(fifth["existing_post_repair_authority_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(fifth["runtime_gate"]["post_repair_authority_result_count"], 1)
        self.assertEqual(fifth["runtime_gate"]["post_repair_authority_required_count"], 0)
        self.assertEqual(fifth["runtime_gate"]["superseded_post_repair_review_parent_count"], 1)
        self.assertEqual(fifth["runtime_gate"]["superseded_post_repair_review_parent_unlinked_count"], 1)
        self.assertEqual(fifth["runtime_gate"]["retry_candidate_count"], 1)
        self.assertEqual(fifth["runtime_gate"]["retry_unblocked_task_count"], 0)
        self.assertEqual(fifth["runtime_gate"]["retry_promoted_task_count"], 1)
        self.assertEqual(fifth["retry_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(fifth["unblocked_ready_work_unit_task_ids"], {})
        self.assertEqual(fifth["promoted_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(
            fifth["unlinked_superseded_post_repair_review_parent_task_ids"],
            {"work-unit-001": [adapter.PUBLIC_SAFE_KANBAN_REF]},
        )
        self.assertEqual(upstream_status_after_retry, "ready")
        self.assertNotIn(stale_review_task_id, upstream_parents_after_retry)
        self.assertIn(authority_task_id, upstream_parents_after_retry)
        self.assertEqual(second["retry_ready_work_unit_task_ids"], {})
        self.assertEqual(second["completed_ready_work_unit_task_ids"], {})
        self.assertEqual(fifth["completed_ready_work_unit_task_ids"], {})
        fresh_review_row = sixth["post_release_reconciliation"]["work-unit-001"]
        self.assertEqual(fresh_review_row["decision"], "awaiting_retry_or_done_authority")
        self.assertEqual(fresh_review_row["post_repair_review_task_ref"], "review-fixture-v3")
        self.assertIsNone(fresh_review_row["post_repair_authority_task_ref"])
        self.assertFalse(fresh_review_row["retry_authorized"])
        self.assertFalse(fresh_review_row["done_authorized"])
        self.assertEqual(sixth["retry_ready_work_unit_task_ids"], {})
        self.assertEqual(sixth["completed_ready_work_unit_task_ids"], {})
        self.assertEqual(sixth["existing_post_repair_authority_task_ids"], {})
        self.assertEqual(sixth["runtime_gate"]["post_repair_authority_required_count"], 1)
        self.assertEqual(sixth["runtime_gate"]["post_repair_authority_missing_task_count"], 1)
        self.assertEqual(sixth["runtime_gate"]["post_repair_authority_result_count"], 0)
        self.assertEqual(seventh["created_post_repair_authority_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        complete_row = eighth["post_release_reconciliation"]["work-unit-001"]
        self.assertEqual(complete_row["decision"], "complete_parent")
        self.assertTrue(complete_row["done_authorized"])
        self.assertTrue(complete_row["done_definition_satisfied"])
        self.assertEqual(complete_row["post_repair_authority_task_ref"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(eighth["runtime_gate"]["post_repair_authority_result_count"], 1)
        self.assertEqual(eighth["runtime_gate"]["complete_candidate_count"], 1)
        self.assertEqual(eighth["completed_ready_work_unit_task_ids"], {})
        review_tasks = [
            task
            for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("packet_type")
            == "ready_work_unit_post_repair_review_request"
        ]
        self.assertEqual(len(review_tasks), 1)
        authority_tasks = [
            task
            for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("packet_type")
            == "ready_work_unit_post_repair_authority_request"
        ]
        self.assertEqual(len(authority_tasks), 2)
        old_authority_tasks = [
            task
            for task in authority_tasks
            if json.loads(str(task.get("body") or "{}")).get("review_task_ref") == "review-fixture-v2"
        ]
        self.assertEqual(len(old_authority_tasks), 1)
        self.assertEqual(old_authority_tasks[0]["assignee"], "independent-reviewer")
        authority_body = json.loads(str(old_authority_tasks[0]["body"]))
        self.assertEqual(authority_body["marker"], "ready_work_unit_post_repair_authority_required")
        self.assertEqual(authority_body["authority_scope"], "post_repair_retry_or_done_only")
        fresh_authority_tasks = [
            task
            for task in authority_tasks
            if json.loads(str(task.get("body") or "{}")).get("review_task_ref") == "review-fixture-v3"
        ]
        self.assertEqual(len(fresh_authority_tasks), 1)

    def test_reconcile_ready_work_units_requires_route_readiness_before_post_repair_review_task(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            create_calls_before = [call for call in fake.calls if len(call) >= 5 and call[4] == "create"]
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--create-post-repair-review-tasks",
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "post-repair review route readiness blocked"):
                adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        create_calls_after = [call for call in fake.calls if len(call) >= 5 and call[4] == "create"]
        self.assertEqual(create_calls_after, create_calls_before)

    def test_reconcile_ready_work_units_unblocks_retry_when_review_authorizes(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "independent-reviewer",
                    "body": json.dumps(
                        {
                            "marker": "ready_work_unit_repair_review_passed",
                            "ready_work_unit_retry_authorized": True,
                        }
                    ),
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            result = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["retry_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["completed_ready_work_unit_task_ids"], {})
        self.assertEqual(result["post_release_reconciliation"]["work-unit-001"]["decision"], "retry_parent")
        self.assertEqual(result["runtime_gate"]["retry_unblocked_task_count"], 1)
        released_task = next(task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001")
        self.assertEqual(released_task["status"], "ready")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(len(unblock_calls), 2)

    def test_reconcile_ready_work_units_completes_when_done_definition_authorized(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "factory-orchestrator",
                    "body": json.dumps({"marker": "ready_work_unit_repair_completed"}),
                }
            )
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "independent-reviewer",
                    "body": json.dumps(
                        {
                            "marker": "ready_work_unit_repair_review_passed",
                            "ready_work_unit_done_authorized": True,
                            "ready_work_unit_done_definition_satisfied": True,
                        }
                    ),
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                ]
            )
            result = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["retry_ready_work_unit_task_ids"], {})
        self.assertEqual(result["completed_ready_work_unit_task_ids"], {"work-unit-001": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["post_release_reconciliation"]["work-unit-001"]["decision"], "complete_parent")
        self.assertEqual(result["runtime_gate"]["completed_task_count"], 1)
        completed_task = next(task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001")
        self.assertEqual(completed_task["status"], "done")
        complete_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "complete"]
        self.assertEqual(len(complete_calls), 1)

    def test_reconcile_ready_work_units_human_gate_marker_blocks_automatic_mutation(self) -> None:
        fake = FakeHermes()
        plan = two_step_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            materialization_result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["decomposition-planner", "implementation-worker"])
            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--workspace",
                    "scratch",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )
            adapter.release_ready_work_units(release_args, runner=fake)
            upstream_task = next(
                task for task in fake.tasks.values() if json.loads(task["body"])["work_unit_id"] == "work-unit-001"
            )
            upstream_task["status"] = "blocked"
            upstream_task.setdefault("events", []).append({"kind": "claimed"})
            upstream_task.setdefault("events", []).append({"kind": "blocked", "reason": "repair required"})
            upstream_task.setdefault("comments", []).append(
                {
                    "author": "independent-reviewer",
                    "body": json.dumps({"marker": "human_gate_required"}),
                }
            )
            reconcile_args = adapter.build_parser().parse_args(
                [
                    "reconcile-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                    "--create-post-repair-review-tasks",
                ]
            )
            result = adapter.reconcile_ready_work_units(reconcile_args, runner=fake)

        assert_live_adapter_result_schema(self, result)
        self.assertEqual(result["post_release_reconciliation"]["work-unit-001"]["decision"], "human_gate_required")
        self.assertEqual(result["runtime_gate"]["human_gate_required_count"], 1)
        self.assertEqual(result["post_repair_review_task_ids"], {})
        self.assertEqual(result["retry_ready_work_unit_task_ids"], {})
        self.assertEqual(result["completed_ready_work_unit_task_ids"], {})

    def test_release_ready_work_units_rejects_ambiguous_matching_tasks(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            existing = next(iter(fake.tasks.values())).copy()
            fake.tasks["t_duplicate"] = {**existing, "id": "t_duplicate"}
            args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "expected exactly one blocked or completed Hermes task"):
                adapter.release_ready_work_units(args, runner=fake)

        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(unblock_calls, [])

    def test_release_ready_work_units_rejects_adapter_local_workspace(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
                workspace="dir:C:/Users/operator/repo",
            )
            args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "not dispatcher-visible"):
                adapter.release_ready_work_units(args, runner=fake)

        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(unblock_calls, [])

    def test_release_ready_work_units_requires_real_materialization_result(self) -> None:
        fake = FakeHermes()
        plan = single_ready_work_unit_plan()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            plan_path = tmp_path / "plan.json"
            readiness_path = tmp_path / "route-readiness.json"
            result_path = tmp_path / "materialization-result.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            write_route_readiness(readiness_path, extra_workers=["implementation-worker"])
            result_path.write_text(
                json.dumps(
                    {
                        "$schema": "https://overkill-factory.dev/schemas/hermes-live-adapter-result.schema.json",
                        "mode": "materialize-ready-work-units",
                        "dry_run": True,
                        "board": "overkill-factory-live",
                        "hook": {},
                    }
                ),
                encoding="utf-8",
            )
            args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(result_path),
                    "--route-readiness",
                    str(readiness_path),
                ]
            )

            with self.assertRaisesRegex(RuntimeError, "real materialization result"):
                adapter.release_ready_work_units(args, runner=fake)

        self.assertEqual(fake.calls, [])

    def test_materialize_schema_requires_recovery_and_idempotency_fields_for_real_run(self) -> None:
        schema = json.loads((ROOT / "schemas" / "hermes-live-adapter-result.schema.json").read_text(encoding="utf-8"))
        result = {
            "$schema": "https://overkill-factory.dev/schemas/hermes-live-adapter-result.schema.json",
            "mode": "materialize",
            "dry_run": False,
            "board": TEST_BOARD,
            "hook": {},
            "idempotency_contract": {
                "digest_algorithm": "sha256",
                "canonicalization_version": "v1",
                "volatile_fields_ignored": ["created_at"],
                "digest_scope": "main_card_body_and_stable_worker_packet_contract",
                "lineage_policy": "base_identity_is_logical_lineage_contract_key_is_runtime_identity",
                "runtime_authority": "hermes_kanban",
                "local_state_authority": False,
                "main_task": {
                    "idempotency_identity": {
                        "card_id": "CARD-001",
                        "task_role": "main",
                        "base_idempotency_key": "overkill:CARD-001:main",
                    },
                    "contract_digest": "a" * 64,
                    "idempotency_key": "overkill:CARD-001:main:aaaaaaaaaaaaaaaa",
                    "runtime_history_query_keys": ["overkill:CARD-001:main", "CARD-001"],
                    "previous_runtime_task_refs": [],
                    "supersedes_idempotency_keys": [],
                },
                "worker_tasks": {},
            },
        }

        errors = validator.validate_node(schema, result, "$", schemas={"hermes-live-adapter-result.schema.json": schema}, root_schema=schema)

        self.assertIn("$.allOf[0]: missing required field main_task_id", errors)
        self.assertIn("$.allOf[0]: missing required field worker_task_ids", errors)
        self.assertIn("$.allOf[0]: missing required field recovery_promoted_worker_task_ids", errors)
        self.assertIn("$.allOf[0]: missing required field recovery_retry_blocked_worker_task_ids", errors)
        self.assertIn("$.allOf[0]: missing required field recovery_attempts", errors)

    def test_worker_idempotency_key_is_contract_bound_and_ignores_volatile_metadata(self) -> None:
        task_contract = {
            "worker_id": "codex-security",
            "queue_class": "blocking-before-done",
            "gate_timing_class": "blocking-before-done",
            "required_before": "done",
            "expected_receipt_field": "security_scan_result",
            "packet": {
                "created_at": "2026-06-15T00:00:00Z",
                "worker": {"id": "codex-security"},
                "input_contract": {"required_fields": ["security_scan_packet"]},
            },
        }
        same_contract = {
            **task_contract,
            "packet": {
                **task_contract["packet"],
                "created_at": "2026-06-16T00:00:00Z",
                "checked_at": "2026-06-16T01:00:00Z",
            },
        }
        changed_contract = {
            **task_contract,
            "queue_class": "blocking-before-ready",
        }

        key = adapter.worker_task_idempotency_key("CARD-1", "codex-security", task_contract)

        self.assertEqual(key, adapter.worker_task_idempotency_key("CARD-1", "codex-security", same_contract))
        self.assertNotEqual(key, adapter.worker_task_idempotency_key("CARD-1", "codex-security", changed_contract))
        self.assertRegex(key, r"^overkill:CARD-1:codex-security:[0-9a-f]{16}$")

    def test_recovery_attempt_count_requires_stable_marker(self) -> None:
        route_id = "recovery:card-001:handoff-packer"
        route_digest = adapter.recovery_route_digest(
            {
                "recovery_route_id": route_id,
                "retry_policy": {"max_attempts": 10},
                "fresh_review_result_ref": "worker-result:independent-reviewer:fresh-review",
                "factory_owned_repair_allowed": True,
                "human_gate_required": False,
            }
        )

        refs = adapter.recovery_attempt_history_refs(
            {
                "events": [
                    {"type": "comment", "reason": f"{route_id} recovery attempt wording only"},
                    {
                        "type": "unblocked",
                        "reason": (
                            "factory_recovery_attempt "
                            f"route_id={route_id} route_digest=sha256:0000 "
                            "attempt_number=1 max_attempts=10"
                        ),
                    },
                    {
                        "type": "unblocked",
                        "reason": (
                            "factory_recovery_attempt "
                            f"route_id={route_id} route_digest={route_digest} "
                            "attempt_number=1 max_attempts=10"
                        ),
                    },
                ],
                "comments": [
                    {
                        "body": (
                            "factory_recovery_attempt "
                            f"route_id={route_id} route_digest={route_digest} "
                            "attempt_number=2 max_attempts=10"
                        )
                    }
                ],
            },
            route_id,
            route_digest,
        )

        self.assertEqual(refs, ["events:2", "comments:0"])

    def test_blocked_event_detection_does_not_treat_unblocked_as_blocked(self) -> None:
        self.assertFalse(
            adapter.task_has_blocked_event(
                {
                    "status": "blocked",
                    "events": [{"type": "unblocked", "reason": "previous unblock"}],
                }
            )
        )
        self.assertFalse(
            adapter.task_has_blocked_event(
                {
                    "task": {"status": "blocked"},
                    "events": [{"kind": "created", "payload": {"status": "blocked"}}],
                }
            )
        )
        self.assertTrue(
            adapter.task_has_blocked_event(
                {
                    "status": "blocked",
                    "events": [{"type": "blocked", "reason": "current gate"}],
                }
            )
        )
        self.assertTrue(
            adapter.task_has_blocked_event(
                {
                    "task": {"status": "blocked"},
                    "events": [{"kind": "blocked", "payload": {"reason": "current gate"}}],
                }
            )
        )
        self.assertTrue(
            adapter.task_has_unblocked_event(
                {
                    "task": {"status": "ready"},
                    "events": [{"kind": "unblocked", "payload": {"reason": "factory_recovery_attempt"}}],
                },
                required_markers=["factory_recovery_attempt"],
            )
        )
        self.assertTrue(
            adapter.task_has_unblocked_event(
                {
                    "task": {"status": "ready"},
                    "events": [{"kind": "unblocked", "payload": None}],
                    "comments": [
                        {
                            "author": "overkill-factory",
                            "body": "runtime_gate=blocked_event_verified_for_each_task release_scope=ready_work_units_only dispatch_separate=true",
                        }
                    ],
                },
                required_markers=[
                    "runtime_gate=blocked_event_verified_for_each_task",
                    "release_scope=ready_work_units_only",
                    "dispatch_separate=true",
                ],
            )
        )

    def test_unblock_task_requires_readback_markers_when_provided(self) -> None:
        fake = FakeHermes()
        task_id = "t_" + "marker01"
        fake.tasks[task_id] = {"status": "blocked", "events": []}

        with self.assertRaisesRegex(RuntimeError, "not durably unblocked"):
            adapter.unblock_task(
                hermes_bin="hermes",
                board=TEST_BOARD,
                task_id=task_id,
                reason="unblock without required marker",
                required_readback_markers=["route_id=recovery:card:worker"],
                runner=fake,
            )

        fake.tasks[task_id] = {"status": "blocked", "events": []}
        adapter.unblock_task(
            hermes_bin="hermes",
            board=TEST_BOARD,
            task_id=task_id,
            reason="factory_recovery_attempt route_id=recovery:card:worker",
            required_readback_markers=["factory_recovery_attempt", "route_id=recovery:card:worker"],
            runner=fake,
        )

        self.assertEqual(fake.tasks[task_id]["status"], "ready")

    def test_recovery_route_digest_matches_factoryctl_contract(self) -> None:
        route = {
            "recovery_route_id": "recovery:card:review-block",
            "created_at": "2026-06-06T00:00:00+00:00",
            "repair_owner_worker": "handoff-packer",
            "fresh_review_required": True,
        }

        self.assertEqual(adapter.recovery_route_digest(route), factoryctl.recovery_route_digest(route))

    def test_dispatch_reports_tasks_that_entered_running_even_when_native_spawned_is_empty(self) -> None:
        fake = FakeDispatchHermes(native_spawned=False)
        args = adapter.build_parser().parse_args(["dispatch", "--board", TEST_BOARD])

        result = adapter.dispatch(args, runner=fake)

        self.assertEqual(result["mode"], "dispatch")
        self.assertEqual(result["spawned"][0]["task_id"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(result["spawned"][0]["run_id"], 42)
        self.assertEqual(result["spawned"][0]["worker_pid"], 12345)
        self.assertEqual(result["spawned"][0]["workspace"], "redacted:absolute-hermes-workspace")
        self.assertEqual(
            result["spawned"][0]["dispatch_observation"],
            "already_running_after_native_dispatch",
        )
        self.assertEqual(result["spawned_by_this_command"], [])
        self.assertEqual(len(result["already_running_after_dispatch"]), 1)
        self.assertEqual(result["native_dispatch"]["spawned"], [])
        self.assertTrue(result["hook"]["no_shadow_dispatcher"])
        self.assertFalse(result["hook"]["local_state_authority"])

    def test_dispatch_enriches_native_spawned_with_run_id_and_pid(self) -> None:
        fake = FakeDispatchHermes(native_spawned=True)
        args = adapter.build_parser().parse_args(["dispatch", "--board", TEST_BOARD])

        result = adapter.dispatch(args, runner=fake)

        self.assertEqual(len(result["spawned_by_this_command"]), 1)
        spawned = result["spawned_by_this_command"][0]
        self.assertEqual(spawned["task_id"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(spawned["run_id"], 42)
        self.assertEqual(spawned["worker_pid"], 12345)
        self.assertEqual(spawned["dispatch_observation"], "native_dispatch_spawned")
        self.assertEqual(spawned["workspace"], "redacted:absolute-hermes-workspace")
        self.assertEqual(result["already_running_after_dispatch"], [])

    def test_dispatch_skips_native_dispatch_when_ready_task_lacks_phase_binding(self) -> None:
        fake = FakeDispatchHermes(ready_step_key=None)
        args = adapter.build_parser().parse_args(["dispatch", "--board", TEST_BOARD])

        result = adapter.dispatch(args, runner=fake)

        self.assertTrue(result["dispatch_skipped"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "repair_board_contract")
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_reports_ready_work_without_creating_or_dispatching(self) -> None:
        fake = FakeHermes()
        fake.tasks[READY_TASK_ID] = {
            "id": READY_TASK_ID,
            "status": "ready",
            "assignee": "implementation-worker",
            "current_step_key": "F15-runtime-execution",
            "body": "{}",
            "events": [],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["mode"], "no-idle")
        self.assertEqual(result["no_idle_state"]["status"], "dispatch_available")
        self.assertTrue(result["no_idle_state"]["native_dispatch_required_next"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))

    def test_no_idle_resumes_reconciled_canonical_frontier_without_creating_parallel_card(self) -> None:
        fake = FakeHermes()
        frontier_task_id = "fixture-frontier-canonical"
        fake.tasks[frontier_task_id] = {
            "id": frontier_task_id,
            "status": "blocked",
            "title": "F8 - Product Experience / Capability Pack selection",
            "assignee": "factory-orchestrator",
            "current_step_key": "F8-capability-and-product-experience-selection",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F8-capability-and-product-experience-selection",
                        "runtime_field_required": True,
                    },
                    "blocked_until_reducer_adapter_authorizes_resume_or_rerun": True,
                }
            ),
            "comments": [
                {
                    "body": (
                        "FRONTIER_RECONCILIATION_RESULT: single canonical frontier; "
                        "resume_or_rerun through reducer/adapter."
                    )
                }
            ],
            "events": [{"type": "blocked", "payload": {"kind": "transient", "reason": "adapter authorizes resume"}}],
        }
        fake.tasks["fixture-old-f7"] = {
            "id": "fixture-old-f7",
            "status": "blocked",
            "title": "F7 - superseded stale branch",
            "current_step_key": "F7-method-contract",
            "body": json.dumps({"stale_non_consumable": True}),
            "events": [{"type": "blocked"}],
        }
        fake.tasks["t_reconcile"] = {
            "id": "t_reconcile",
            "status": "done",
            "title": "F7/F8 deterministic frontier reconciliation",
            "completed_at": "2026-06-28T18:00:00Z",
            "metadata": json.dumps(
                {
                    "orchestration_result": {
                        "frontier_reconciliation_result": "selected_single_canonical_frontier",
                        "canonical_frontier_task_id": frontier_task_id,
                        "canonical_frontier_status": "blocked_until_reducer_adapter_authorizes_resume_or_rerun",
                        "stale_non_consumable_tasks": ["fixture-old-f7"],
                    }
                }
            ),
            "events": [{"type": "completed"}],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "resume_canonical_frontier_task")
        self.assertEqual(state["classification"], "canonical_frontier_task_resumed")
        self.assertFalse(result["blocked"])
        self.assertFalse(state["human_gate_required"])
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertEqual(fake.tasks[frontier_task_id]["status"], "ready")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertEqual(len(unblock_calls), 1)
        self.assertEqual(unblock_calls[0][5], frontier_task_id)
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_creates_targeted_package_dependency_repair(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_packageblock"
        child_id = "t_childtodo"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "title": "F8 - Product Face material package missing readback",
            "assignee": "product-face",
            "current_step_key": "F8-capability-and-product-experience-selection",
            "body": json.dumps(
                {
                    "packet_type": "factory_phase_work_card",
                    "phase": "F8_product_face_consumption",
                    "done_definition": "Produce product_face_result or typed blockers.",
                    "blocker": "material package missing readback",
                }
            ),
            "events": [
                {
                    "kind": "blocked",
                    "payload": {"kind": "needs_input", "reason": "material package missing readback"},
                }
            ],
        }
        fake.tasks[child_id] = {
            "id": child_id,
            "status": "todo",
            "title": "F9 - downstream architecture boundary",
            "current_step_key": "F9-architecture-boundary",
            "body": json.dumps({"packet_type": "factory_phase_work_card", "phase": "F9"}),
            "parents": [blocker_id],
            "events": [{"kind": "created"}],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(
            state["classification"],
            "deterministic_factory_package_dependency_repair_task_created",
        )
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertFalse(state["human_gate_required"])
        create_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "create"]
        self.assertEqual(len(create_calls), 1)
        created_task = next(
            task
            for task in fake.tasks.values()
            if task.get("title") == "Repair factory package/dependency blockers"
        )
        created_body = json.loads(created_task["body"])
        self.assertEqual(
            created_body["targeted_remediation"]["plan_action"],
            "repair_factory_owned_package_dependency_blocker",
        )
        self.assertFalse(created_body["targeted_remediation"]["create_new_canonical_card"])
        self.assertNotIn("parents", created_task)

    def test_no_idle_replaces_more_than_three_stale_reconcile_tasks(self) -> None:
        fake = StaleThenFreshReconcileHermes(stale_creates=3)
        todo_id = "t_staletodo"
        fake.tasks[todo_id] = {
            "id": todo_id,
            "status": "todo",
            "title": "F15/WU-08 - Downstream payment work without binding",
            "assignee": "integration-builder",
            "body": "{}",
            "events": [{"kind": "created"}],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(fake.create_count, 4)
        self.assertEqual(
            state["classification"],
            "deterministic_board_reconcile_task_created_after_stale_terminal_replacement",
        )
        self.assertEqual(state.get("remediation_replacement_attempts"), 3)
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertFalse(state["remediation_task_stale"])
        fresh_tasks = [
            task
            for task in fake.tasks.values()
            if task.get("title") == "Materialize canonical factory card for board" and task.get("status") == "ready"
        ]
        self.assertEqual(len(fresh_tasks), 1)

    def test_no_idle_creates_materialization_contract_repair_for_internal_missing_inputs(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_materialdefect"
        downstream_id = "t_downstreamtodo"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "title": "F15/WU-07 - Ledger, reconciliation and audit data model",
            "assignee": "data-persistence-builder",
            "current_step_key": "F15-runtime-execution",
            "body": json.dumps(
                {
                    "work_unit_id": "WU-07",
                    "source_packet_artifact": "f15_worker_packets.json#WU-07",
                    "done_definition": "Produce traceable ledger model from parent artifacts.",
                }
            ),
            "latest_summary": (
                "Factory integration/input defect: missing runtime_contract and source_packet_artifact; "
                "parent artifacts absent, so values cannot be traced."
            ),
            "events": [
                {
                    "kind": "blocked",
                    "payload": {
                        "kind": "capability",
                        "reason": "missing runtime_contract and source_packet_artifact; repair materialization",
                    },
                }
            ],
            "comments": [
                {
                    "author": "data-persistence-builder",
                    "body": (
                        "No safe data-persistence work can proceed: runtime_contract, target_repo_paths, "
                        "source_packet_artifact and parent artifacts are missing. This should be repaired by "
                        "the factory adapter/materializer, not by asking the operator."
                    ),
                }
            ],
        }
        fake.tasks[downstream_id] = {
            "id": downstream_id,
            "status": "todo",
            "title": "F15/WU-17 - Test automation and remote proof harness",
            "current_step_key": "F15-runtime-execution",
            "body": json.dumps({"work_unit_id": "WU-17"}),
            "parents": [blocker_id],
            "events": [{"kind": "created"}],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(
            state["classification"],
            "deterministic_materialization_contract_repair_task_created",
        )
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertEqual(state["materialization_contract_task_refs"], [blocker_id])
        created_tasks = [
            task
            for task_id, task in fake.tasks.items()
            if task_id not in {blocker_id, downstream_id}
        ]
        self.assertEqual(len(created_tasks), 1)
        created_body = json.loads(str(created_tasks[0]["body"]))
        self.assertEqual(
            created_body["targeted_remediation"]["plan_action"],
            "repair_materialization_contract_inputs",
        )
        self.assertEqual(created_body["targeted_remediation"]["materialization_contract_task_refs"], [blocker_id])
        self.assertFalse(created_body["operator_input_required"])
        self.assertNotIn("parents", created_tasks[0])

    def test_no_idle_reports_dispatch_available_when_ready_exists_alongside_running(self) -> None:
        running_id = "t_" + "runalive"
        ready_id = "t_" + "readywork"
        rows = {
            "running": [
                {
                    "id": running_id,
                    "status": "running",
                    "assignee": "worker-a",
                    "title": "Long running work",
                }
            ],
            "ready": [
                {
                    "id": ready_id,
                    "status": "ready",
                    "assignee": "worker-b",
                    "title": "Ready parallel work",
                }
            ],
            "blocked": [],
            "todo": [],
            "done": [],
        }

        state = adapter.classify_no_idle_state(rows)

        self.assertEqual(state["classification"], "running_work_exists")
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertEqual(state["ready_task_refs"], [ready_id])
        self.assertEqual(state["running_task_refs"], [running_id])

    def test_no_idle_external_api_key_not_materialization_contract_repair(self) -> None:
        blocker_id = "t_" + "externalkey"
        rows = {
            "blocked": [
                {
                    "id": blocker_id,
                    "status": "blocked",
                    "assignee": "cloud-infra-security-specialist",
                    "title": "F15/WU-15 - Cloud source packet blocked on external API key",
                    "body": (
                        "source_packet_artifact and worker packet are present, but this route requires "
                        "external API key / private key material from the operator before execution."
                    ),
                    "events": [
                        {
                            "type": "blocked",
                            "payload": {
                                "kind": "needs_input",
                                "reason": "requires external API key before runtime_contract can be used",
                            },
                        }
                    ],
                }
            ],
            "todo": [],
            "ready": [],
            "running": [],
            "done": [],
        }

        state = adapter.classify_no_idle_state(rows)

        self.assertEqual(state["classification"], "only_operator_input_blockers_seen")
        self.assertTrue(state["operator_input_required"])
        self.assertFalse(state["remediation_required"])
        self.assertEqual(state["operator_input_task_refs"], [blocker_id])
        self.assertNotIn(blocker_id, state.get("materialization_contract_task_refs") or [])

    def test_no_idle_human_gate_packet_complete_wins_over_contextual_target_repo_paths(self) -> None:
        blocker_id = "t_" + "humangatepaths"
        rows = {
            "blocked": [
                {
                    "id": blocker_id,
                    "status": "blocked",
                    "assignee": "human-gate-clerk",
                    "title": "Owner decision package ready",
                    "body": json.dumps(
                        {
                            "human_gate_packet": human_gate_packet_fixture(),
                            "status": "ready for operator decision",
                            "context_note": "target_repo_paths and scan scope are listed only as evidence context, not as requested operator material.",
                        }
                    ),
                    "latest_summary": "Decision package prepared and delivered; ready for operator decision.",
                    "events": [
                        {
                            "type": "blocked",
                            "payload": {
                                "kind": "human_gate",
                                "reason": "awaiting human decision after delivered package",
                            },
                        }
                    ],
                }
            ],
            "todo": [],
            "ready": [],
            "running": [],
            "done": [],
        }

        state = adapter.classify_no_idle_state(rows)

        self.assertEqual(state["classification"], "only_human_gate_blockers_seen")
        self.assertTrue(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertEqual(state["human_gate_task_refs"], [blocker_id])

    def test_no_idle_replaces_stale_materialization_contract_repair_task(self) -> None:
        fake = StaleThenFreshReconcileHermes(stale_creates=1)
        blocker_id = "t_" + "matstale"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "solana-quasar-builder",
            "title": "F15/WU-12 - Onchain Work Package",
            "body": "Onchain Work Package/source packet is missing; WU-07 has no traceable ledger artifact.",
            "events": [
                {
                    "type": "blocked",
                    "payload": {
                        "kind": "capability",
                        "reason": "source_packet_artifact missing for onchain work package",
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "deterministic_materialization_contract_repair_task_created")
        self.assertEqual(state["stale_remediation_task_refs"], ["kanban:<redacted>"])
        self.assertEqual(state["remediation_replacement_attempts"], 1)
        self.assertFalse(state["remediation_task_stale"])
        self.assertTrue(state["native_dispatch_required_next"])
        ready_repairs = [
            task for task in fake.tasks.values()
            if adapter.task_body_json_object(task).get("marker") == adapter.NO_IDLE_MATERIALIZATION_CONTRACT_REPAIR_MARKER
            and task.get("status") == "ready"
        ]
        self.assertEqual(len(ready_repairs), 1)

    def test_no_idle_creates_materialization_repair_for_missing_source_packet_and_traceability_artifact(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "wu12block"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "title": "F15/WU-12 - Onchain Work Package: Solana/Quasar accounts, PDAs, authority and DevNet-only validation plan",
            "assignee": "solana-quasar-builder",
            "current_step_key": "F15-runtime-execution",
            "body": (
                "work_unit_id: WU-12\n"
                "source_packet_artifact: /workspace/f15_worker_packets.json#WU-12\n"
                "dependencies: WU-07=" + "t_" + "6a427946\n"
                "stop_rules:\n- Onchain Work Package missing\n- Auditor unavailable\n"
            ),
            "events": [
                {
                    "kind": "blocked",
                    "payload": {
                        "kind": "capability",
                        "reason": (
                            "WU-12 stop rule fired: required Onchain Work Package/source packet is missing "
                            "and WU-07 has no traceable ledger/reconciliation artifact; cannot construct "
                            "PDA/signer map without inventing authority boundaries."
                        ),
                    },
                }
            ],
            "comments": [
                {
                    "author": "solana-quasar-builder",
                    "body": (
                        "Required unblock: materialize/attach the WU-12 Onchain Work Package/source packet "
                        "and traceable WU-07 ledger/event artifact. No Mainnet/funds/signing action was performed."
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(
            state["classification"],
            "deterministic_materialization_contract_repair_task_created",
        )
        self.assertEqual(state["materialization_contract_task_refs"], ["kanban:<redacted>"])
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        created_tasks = [task for task_id, task in fake.tasks.items() if task_id != blocker_id]
        self.assertEqual(len(created_tasks), 1)
        created_body = json.loads(str(created_tasks[0]["body"]))
        self.assertEqual(
            created_body["targeted_remediation"]["plan_action"],
            "repair_materialization_contract_inputs",
        )
        self.assertIn(blocker_id, created_body["targeted_remediation"]["materialization_contract_task_refs"])

    def test_no_idle_prioritizes_materialization_blocker_over_board_contract_with_unrelated_todo(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "wu12block2"
        todo_id = "t_" + "unrelatedtodo"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "title": "F15/WU-12 - Onchain Work Package: Solana/Quasar accounts, PDAs, authority and DevNet-only validation plan",
            "assignee": "solana-quasar-builder",
            "current_step_key": "F15-runtime-execution",
            "body": (
                "work_unit_id: WU-12\n"
                "source_packet_artifact: /workspace/f15_worker_packets.json#WU-12\n"
                "dependencies: WU-07=" + "t_" + "6a427946\n"
            ),
            "events": [
                {
                    "kind": "blocked",
                    "payload": {
                        "kind": "capability",
                        "reason": (
                            "WU-12 stop rule fired: required Onchain Work Package/source packet is missing "
                            "and WU-07 has no traceable ledger/reconciliation artifact."
                        ),
                    },
                }
            ],
            "comments": [
                {
                    "author": "solana-quasar-builder",
                    "body": "Required unblock: materialize/attach the WU-12 source packet and traceable WU-07 ledger/event artifact.",
                }
            ],
        }
        fake.tasks[todo_id] = {
            "id": todo_id,
            "status": "todo",
            "title": "F15/WU-99 - unrelated backlog item",
            "assignee": "implementation-worker",
            "body": "Not ready yet; unrelated todo backlog should not mask materialization blocker.",
            "events": [{"kind": "created"}],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(
            state["classification"],
            "deterministic_materialization_contract_repair_task_created",
        )
        self.assertEqual(state["materialization_contract_task_refs"], ["kanban:<redacted>"])
        self.assertTrue(state["native_dispatch_required_next"])
        created_tasks = [task for task_id, task in fake.tasks.items() if task_id not in {blocker_id, todo_id}]
        self.assertEqual(len(created_tasks), 1)

    def test_no_idle_creates_owner_gate_package_after_product_sot_candidate_done(self) -> None:
        fake = FakeHermes()
        sot_task_id = "t_" + "sotdone1"
        fake.tasks[sot_task_id] = {
            "id": sot_task_id,
            "title": "F5 - Prepare Product SOT candidate",
            "status": "done",
            "body": "Product SOT candidate only; no owner approval recorded.",
            "latest_summary": (
                "Prepared the Product SOT candidate and named Product SOT owner review "
                "as the next required gate before Method Contract."
            ),
            "events": [{"kind": "completed"}],
            "runs": [
                {
                    "status": "done",
                    "summary": "Prepared Product SOT candidate; downstream frozen.",
                    "metadata": {
                        "product_sot_result": {
                            "artifact_file": "product-sot-result.json",
                            "review_packet_file": "product-sot-candidate.md",
                            "status": "candidate_owner_review_required_not_approved",
                            "next_required_gate": (
                                "Product SOT owner review before Method Contract / "
                                "Product Experience / architecture / implementation routing"
                            ),
                            "downstream_frozen": [
                                "Method Contract",
                                "Product Experience/Product Face",
                                "architecture",
                                "implementation",
                            ],
                        }
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(
            state["classification"],
            "deterministic_post_review_owner_gate_package_task_created",
        )
        self.assertTrue(state["remediation_required"])
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertEqual(state["post_review_task_refs"], ["kanban:<redacted>"])
        created_tasks = [
            task
            for task_id, task in fake.tasks.items()
            if task_id != sot_task_id and task.get("assignee") == "human-gate-clerk"
        ]
        self.assertEqual(len(created_tasks), 1)
        created_body = json.loads(str(created_tasks[0]["body"]))
        self.assertEqual(created_body["marker"], adapter.NO_IDLE_POST_REVIEW_GATE_MARKER)
        self.assertIn("markdown/PDF", " ".join(created_body["required_actions"]))
        self.assertIn("rich cards", " ".join(created_body["forbidden_actions"]))

    def test_no_idle_blocks_ready_work_without_structured_phase_binding(self) -> None:
        fake = FakeHermes()
        fake.tasks[READY_TASK_ID] = {
            "id": READY_TASK_ID,
            "status": "ready",
            "assignee": "implementation-worker",
            "body": "{}",
            "events": [],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["mode"], "no-idle")
        self.assertEqual(result["no_idle_state"]["classification"], "repair_board_contract")
        self.assertTrue(result["no_idle_state"]["blocked"])
        self.assertFalse(result["no_idle_state"]["native_dispatch_required_next"])
        self.assertIsNone(result["remediation_task_id"])

    def test_no_idle_checks_board_invariants_before_any_remediation(self) -> None:
        fake = FakeHermes()
        fake.tasks["blocked-f3-card"] = {
            "id": "blocked-f3-card",
            "status": "blocked",
            "assignee": "source-ledger-worker",
            "title": "F3 source resolution blocked",
            "current_step_key": "F3-source-resolution",
            "body": json.dumps(
                {
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F3-source-resolution",
                        "runtime_field_required": True,
                    }
                }
            ),
            "events": [{"kind": "blocked", "payload": {"kind": "transient"}}],
        }
        fake.tasks["running-f4-card"] = {
            "id": "running-f4-card",
            "status": "running",
            "assignee": "product-sot-planner",
            "title": "F4 outcome contract running",
            "current_step_key": "F4-product-outcome-and-discovery",
            "body": json.dumps(
                {
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F4-product-outcome-and-discovery",
                        "runtime_field_required": True,
                    }
                }
            ),
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["mode"], "no-idle")
        self.assertEqual(result["no_idle_state"]["classification"], "factory_phase_invariant_violation")
        self.assertTrue(result["no_idle_state"]["blocked"])
        self.assertFalse(result["no_idle_state"]["native_dispatch_required_next"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "block_invariant_violation")
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_reads_hermes_triage_block_loop_detected(self) -> None:
        fake = FakeHermes()
        fake.tasks[MAIN_TASK_ID] = {
            "id": MAIN_TASK_ID,
            "status": "triage",
            "assignee": None,
            "body": "{}",
            "events": [
                {"kind": "block_loop_detected", "payload": {"kind": "transient", "recurrences": 2}},
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD])

        result = adapter.no_idle(args, runner=fake)

        queried_statuses = [
            call[call.index("--status") + 1]
            for call in fake.calls
            if len(call) >= 5 and call[4] == "list" and "--status" in call
        ]
        self.assertIn("triage", queried_statuses)
        self.assertEqual(result["mode"], "no-idle")
        self.assertEqual(result["no_idle_state"]["classification"], "hermes_typed_block_loop_detected")
        self.assertTrue(result["no_idle_state"]["block_loop_detected"])
        self.assertFalse(result["no_idle_state"]["human_gate_required"])

    def test_no_idle_preserves_todo_dependency_wait_before_phase_reconcile(self) -> None:
        fake = FakeHermes()
        fake.tasks[MAIN_TASK_ID] = {
            "id": MAIN_TASK_ID,
            "status": "todo",
            "assignee": "factory-orchestrator",
            "current_step_key": "F13-runtime-execution",
            "body": json.dumps(
                {
                    "factory_method_version": "OVERKILL_VFINAL",
                    "card_id": "KFP-DEP-WAIT",
                    "phase": "F13",
                    "risk_effective": "R2",
                    "surfaces": ["backend"],
                }
            ),
            "events": [
                {"kind": "dependency_wait", "payload": {"kind": "dependency"}},
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["mode"], "no-idle")
        self.assertEqual(result["no_idle_state"]["classification"], "hermes_native_dependency_wait")
        self.assertEqual(result["no_idle_state"]["typed_block_kind"], "dependency")
        self.assertFalse(result["no_idle_state"]["human_gate_required"])
        self.assertFalse(result["no_idle_state"]["operator_input_required"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")

    def test_no_idle_ready_dependency_wait_history_is_not_current_dependency_wait(self) -> None:
        fake = FakeHermes()
        fake.tasks[MAIN_TASK_ID] = {
            "id": MAIN_TASK_ID,
            "status": "ready",
            "assignee": "factory-orchestrator",
            "body": "{}",
            "events": [
                {"kind": "dependency_wait", "payload": {"kind": "dependency"}},
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["mode"], "no-idle")
        self.assertNotEqual(result["no_idle_state"]["classification"], "hermes_native_dependency_wait")
        self.assertFalse(result["no_idle_state"]["human_gate_required"])

    def test_no_idle_preserves_block_loop_before_phase_reconcile(self) -> None:
        fake = FakeHermes()
        fake.tasks[MAIN_TASK_ID] = {
            "id": MAIN_TASK_ID,
            "status": "triage",
            "assignee": "factory-orchestrator",
            "current_step_key": "F13-runtime-execution",
            "body": json.dumps(
                {
                    "factory_method_version": "OVERKILL_VFINAL",
                    "card_id": "KFP-BLOCK-LOOP",
                    "phase": "F13",
                    "risk_effective": "R2",
                    "surfaces": ["backend"],
                }
            ),
            "events": [
                {"kind": "block_loop_detected", "payload": {"kind": "transient", "recurrences": 2}},
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["mode"], "no-idle")
        self.assertEqual(result["no_idle_state"]["classification"], "hermes_typed_block_loop_detected")
        self.assertTrue(result["no_idle_state"]["block_loop_detected"])
        self.assertFalse(result["no_idle_state"]["human_gate_required"])
        self.assertFalse(result["no_idle_state"]["operator_input_required"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")

    def test_native_workflow_state_updates_hermes_sqlite_columns(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            board_dir = home / "kanban" / "boards" / TEST_BOARD
            board_dir.mkdir(parents=True)
            db_path = board_dir / "kanban.db"
            conn = adapter.sqlite3.connect(str(db_path))
            try:
                conn.execute(
                    "CREATE TABLE tasks (id TEXT PRIMARY KEY, workflow_template_id TEXT, current_step_key TEXT)"
                )
                conn.execute("INSERT INTO tasks (id) VALUES (?)", (MAIN_TASK_ID,))
                conn.commit()
            finally:
                conn.close()

            with mock.patch.dict(adapter.os.environ, {"HERMES_HOME": str(home)}, clear=False):
                changed = adapter.apply_native_workflow_state(
                    board=TEST_BOARD,
                    task_id=MAIN_TASK_ID,
                    workflow_template_id="overkill-vfinal",
                    current_step_key="F5-product-sot",
                )

            self.assertTrue(changed)
            conn = adapter.sqlite3.connect(str(db_path))
            try:
                row = conn.execute(
                    "SELECT workflow_template_id, current_step_key FROM tasks WHERE id = ?",
                    (MAIN_TASK_ID,),
                ).fetchone()
            finally:
                conn.close()
            self.assertEqual(tuple(row), ("overkill-vfinal", "F5-product-sot"))

    def test_create_task_blocked_uses_unassigned_block_assign_protocol(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            home = Path(tmp)
            board_dir = home / "kanban" / "boards" / TEST_BOARD
            board_dir.mkdir(parents=True)
            db_path = board_dir / "kanban.db"
            conn = adapter.sqlite3.connect(str(db_path))
            try:
                conn.execute(
                    "CREATE TABLE tasks (id TEXT PRIMARY KEY, workflow_template_id TEXT, current_step_key TEXT)"
                )
                conn.execute("INSERT INTO tasks (id) VALUES (?)", ("t_" + "00000001",))
                conn.commit()
            finally:
                conn.close()

            with mock.patch.dict(adapter.os.environ, {"HERMES_HOME": str(home)}, clear=False):
                task_id = adapter.create_task(
                    hermes_bin="hermes",
                    board=TEST_BOARD,
                    title="Blocked gate",
                    body=json.dumps({"task_type": "human_gate_package"}),
                    assignee="factory-orchestrator",
                    idempotency_key="blocked-create-race",
                    created_by="test",
                    workspace="scratch",
                    blocked=True,
                    workflow_template_id="overkill-vfinal",
                    current_step_key="F5-product-sot",
                    runner=fake,
                )

            conn = adapter.sqlite3.connect(str(db_path))
            try:
                row = conn.execute(
                    "SELECT workflow_template_id, current_step_key FROM tasks WHERE id = ?",
                    (task_id,),
                ).fetchone()
            finally:
                conn.close()

        create_call = next(call for call in fake.calls if len(call) >= 5 and call[4] == "create")
        block_call = next(call for call in fake.calls if len(call) >= 5 and call[4] == "block")
        assign_call = next(call for call in fake.calls if len(call) >= 5 and call[4] == "assign")
        self.assertNotIn("--assignee", create_call)
        self.assertNotIn("--initial-status", create_call)
        self.assertLess(fake.calls.index(create_call), fake.calls.index(block_call))
        self.assertLess(fake.calls.index(block_call), fake.calls.index(assign_call))
        self.assertEqual(fake.tasks[task_id]["status"], "blocked")
        self.assertEqual(fake.tasks[task_id]["assignee"], "factory-orchestrator")
        self.assertEqual(tuple(row), ("overkill-vfinal", "F5-product-sot"))

    def test_no_idle_creates_deterministic_reconcile_card_when_board_is_silent(self) -> None:
        fake = FakeHermes()
        fake.tasks["t_" + "todo0001"] = {
            "id": "t_" + "todo0001",
            "status": "todo",
            "assignee": "factory-orchestrator",
            "body": json.dumps({"objective": "continue planning"}),
            "events": [],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["no_idle_state"]["status"], "remediation_required")
        self.assertEqual(result["no_idle_state"]["classification"], "deterministic_board_reconcile_task_created")
        self.assertTrue(result["no_idle_state"]["remediation_task_created"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "repair_board_contract")
        self.assertEqual(result["remediation_task_id"], adapter.PUBLIC_SAFE_KANBAN_REF)
        created_task = next(
            task for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("marker") == "factory_deterministic_reconcile"
        )
        self.assertEqual(created_task["status"], "ready")
        body = json.loads(str(created_task["body"]))
        self.assertEqual(body["plan_action"], "repair_board_contract")
        self.assertTrue(body["native_dispatch_required_next"])
        self.assertFalse(body["agent_may_choose_phase"])
        self.assertIn("approve or waive human gates", body["forbidden_actions"])
        self.assertIn(
            "choose a later phase from title, chat, memory, prose or declared phase alone",
            body["forbidden_actions"],
        )
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_repairs_manual_factory_start_bypass(self) -> None:
        fake = FakeHermes()
        fake.tasks["t_" + "manual001"] = {
            "id": "t_" + "manual001",
            "status": "blocked",
            "title": "F1 - Product Alpha source resolution + Product SOT start",
            "assignee": "factory-orchestrator",
            "created_by": "overkill-factory-gerente",
            "skills": ["overkill-factory-product-intake"],
            "parents": [],
            "children": [],
            "body": json.dumps({"objective": "manual start card"}),
            "events": [],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "repair_board_contract")
        self.assertTrue(state["remediation_task_created"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "repair_board_contract")
        self.assertTrue(any("bypassed Kanban-first adapter" in item for item in state["blocked_reasons"]))
        self.assertTrue(any("overkill-factory-product-intake" in item for item in state["blocked_reasons"]))
        created_task = next(
            task for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("marker") == "factory_deterministic_reconcile"
        )
        self.assertEqual(created_task["status"], "ready")
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_creates_fresh_reconcile_card_when_idempotent_card_is_terminal_stale(self) -> None:
        fake = FakeHermes()
        todo_id = "t_" + "todo0001"
        stale_id = "t_" + "stale001"
        fake.tasks[todo_id] = {
            "id": todo_id,
            "status": "todo",
            "assignee": "factory-orchestrator",
            "body": json.dumps({"objective": "continue planning"}),
            "events": [],
        }
        fake.tasks[stale_id] = {
            "id": stale_id,
            "status": "done",
            "assignee": "factory-orchestrator",
            "body": json.dumps({"marker": "factory_deterministic_reconcile"}),
            "events": [{"type": "completed"}],
        }
        rows = {
            "ready": [],
            "running": [],
            "todo": [{"id": todo_id, **fake.tasks[todo_id]}],
            "blocked": [],
            "done": [{"id": stale_id, **fake.tasks[stale_id]}],
        }
        rows = adapter.enrich_no_idle_rows(hermes_bin="hermes", board=TEST_BOARD, rows=rows, runner=fake)
        plan = adapter.build_board_reconcile_plan_from_rows(board=TEST_BOARD, rows=rows)
        body = adapter.deterministic_reconcile_task_body(plan=plan)
        self.assertIsNotNone(body)
        digest = adapter.idempotency_digest_fragment(adapter.contract_digest(body))
        fake.idempotent_task_ids[f"overkill:reconcile:{adapter.public_safe_slug(TEST_BOARD, fallback='board')}:{digest}"] = stale_id
        fake.calls.clear()
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(
            state["classification"],
            "deterministic_board_reconcile_task_created_after_stale_terminal_replacement",
        )
        self.assertTrue(state["remediation_task_created"])
        self.assertFalse(state["remediation_task_stale"])
        self.assertEqual(state["remediation_task_status"], "ready")
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertEqual(state["stale_remediation_task_refs"], ["kanban:<redacted>"])
        self.assertEqual(state["remediation_replacement_attempts"], 1)
        ready_replacements = [
            task for task in fake.tasks.values()
            if task.get("status") == "ready"
            and adapter.parse_json_object(str(task.get("body") or "{}")).get("stale_terminal_remediation_replacement") is True
        ]
        self.assertEqual(len(ready_replacements), 1)
        replacement_body = adapter.parse_json_object(str(ready_replacements[0].get("body") or "{}"))
        self.assertEqual(
            replacement_body["runtime_lineage"]["lineage_type"],
            "stale_terminal_remediation_replacement",
        )
        self.assertEqual(replacement_body["supersedes_runtime_task_refs"], [stale_id])
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_repairs_done_task_with_missing_declared_artifacts(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "done0001"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "product-sot-result.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "product-sot-planner",
                "title": "F5 - Product SOT candidate",
                "body": json.dumps({"objective": "prepare Product SOT"}),
                "events": [
                    {
                        "type": "completed",
                        "payload": {
                            "summary": "declared artifact but did not persist it",
                            "artifacts": [str(missing_artifact)],
                        },
                    }
                ],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(missing_artifact)]}),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "repair_declared_artifacts")
        self.assertTrue(state["remediation_task_created"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "repair_declared_artifacts")
        self.assertTrue(any("product-sot-result.json" in reason for reason in state["blocked_reasons"]))
        created_task = next(
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("plan_action") == "repair_declared_artifacts"
        )
        self.assertEqual(created_task["status"], "ready")
        body = adapter.parse_json_object(str(created_task.get("body") or "{}"))
        self.assertEqual(body["required_output"], "declared_artifact_readback_repair")
        self.assertEqual(body["repair_target"]["task_ref"], "kanban:<redacted>")
        self.assertRegex(body["repair_target"]["target_fingerprint"], r"^[0-9a-f]{64}$")
        self.assertTrue(any("product-sot-result.json" in reason for reason in body["repair_blocked_reasons"]))
        self.assertEqual(body["idempotency_scope"]["scope_type"], "declared_artifact_readback_repair_target")
        self.assertEqual(
            body["idempotency_scope"]["target_fingerprint"],
            body["repair_target"]["target_fingerprint"],
        )
        self.assertFalse(body["agent_may_choose_phase"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_creates_owner_rerun_after_declared_artifact_readback_repair_blocks(self) -> None:
        fake = FakeHermes()
        target_id = "t_" + "wu04rdone"
        repair_id = "t_" + "readbackblock"
        missing_artifact = "/tmp/missing/wu04r_v1_safe_public_copy_spec.json"
        fake.tasks[target_id] = {
            "id": target_id,
            "status": "done",
            "assignee": "product-face",
            "title": "F15/WU-04R - V1-safe public copy remediation packet",
            "body": json.dumps({"objective": "produce WU-04R packet/spec/ledger"}),
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps({"artifacts": [missing_artifact]}),
                }
            ],
        }
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "blocked",
            "assignee": "factory-orchestrator",
            "title": "Repair missing declared artifacts for board",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "marker": "factory_deterministic_reconcile",
                    "plan_action": "repair_declared_artifacts",
                    "required_output": "declared_artifact_readback_repair",
                    "repair_target": {
                        "task_ref": target_id,
                        "title": "F15/WU-04R - V1-safe public copy remediation packet",
                        "assignee": "product-face",
                        "missing_artifact_names": ["wu04r_v1_safe_public_copy_spec.json"],
                    },
                }
            ),
            "runs": [
                {
                    "status": "blocked",
                    "outcome": "blocked",
                    "metadata": json.dumps(
                        {
                            "orchestration_result": {
                                "receipt_type": "declared_artifact_readback_repair",
                                "repair_target_task": target_id,
                                "repair_target_title": "F15/WU-04R - V1-safe public copy remediation packet",
                                "status": "blocked_exact_artifact_repair_not_possible_from_runtime_readback",
                                "route_registry_resolution": {
                                    "target_worker_declared": "product-face",
                                    "review_worker_declared": "independent-reviewer",
                                },
                                "declared_artifact_readback_repair": {
                                    "missing_artifact_names": ["wu04r_v1_safe_public_copy_spec.json"],
                                    "repair_verdict": "BLOCKED",
                                },
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "declared_artifact_owner_rerun_task_created")
        self.assertTrue(state["native_dispatch_required_next"])
        rerun_tasks = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("packet_type")
            == "factory_declared_artifact_owner_rerun_request"
        ]
        self.assertEqual(len(rerun_tasks), 1)
        self.assertEqual(rerun_tasks[0]["status"], "ready")
        self.assertEqual(rerun_tasks[0]["assignee"], "product-face")
        body = adapter.parse_json_object(str(rerun_tasks[0].get("body") or "{}"))
        self.assertEqual(body["target_task_ref"], target_id)
        self.assertEqual(body["review_worker"], "independent-reviewer")
        self.assertEqual(body["missing_artifact_names"], ["wu04r_v1_safe_public_copy_spec.json"])
        self.assertFalse(body["human_gate_required"])
        self.assertFalse(body["operator_input_required"])

    def test_no_idle_closes_superseded_declared_artifact_repair_after_owner_rerun_review_pass(self) -> None:
        fake = FakeHermes()
        repair_id = "t_" + "readbackblock"
        owner_id = "t_" + "ownerrerun"
        review_id = "t_" + "readbackpass"
        target_id = "t_" + "wu04rdone"
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "blocked",
            "assignee": "factory-orchestrator",
            "title": "Repair missing declared artifacts for board",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "marker": "factory_deterministic_reconcile",
                    "plan_action": "repair_declared_artifacts",
                    "required_output": "declared_artifact_readback_repair",
                    "repair_target": {
                        "task_ref": target_id,
                        "title": "F15/WU-04R - V1-safe public copy remediation packet",
                        "assignee": "product-face",
                        "missing_artifact_names": ["wu04r_v1_safe_public_copy_spec.json"],
                    },
                }
            ),
            "comments": [
                {
                    "body": "declared-artifact repair blocked: cannot be reconstructed safely; rerun product-face repair for `" + target_id + "`."
                }
            ],
        }
        fake.tasks[owner_id] = {
            "id": owner_id,
            "status": "done",
            "assignee": "product-face",
            "title": "Rerun owner worker for missing artifacts in " + target_id,
            "body": json.dumps(
                {
                    "packet_type": "factory_declared_artifact_owner_rerun_request",
                    "target_task_ref": target_id,
                    "owner_worker": "product-face",
                }
            ),
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "declared_artifact_owner_rerun_result": {
                                "status": "RERUN_ARTIFACTS_WRITTEN_REVIEW_REQUIRED",
                                "target_task_id": target_id,
                                "created_independent_readback_task": review_id,
                            }
                        }
                    ),
                }
            ],
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Independent readback: WU-04R owner-rerun repaired artifacts",
            "body": "review runtime readback only",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "independent_review_result": {
                                "verdict": "PASS_RUNTIME_READBACK_ONLY",
                                "target_task_id": target_id,
                                "owner_rerun_task_id": owner_id,
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "declared_artifact_repair_superseded_by_owner_readback_pass")
        self.assertEqual(fake.tasks[repair_id]["status"], "done")
        self.assertFalse(state["remediation_required"])
        self.assertFalse(state["native_dispatch_required_next"])
        self.assertFalse(
            any(
                adapter.parse_json_object(str(task.get("body") or "{}")).get("packet_type")
                == "factory_declared_artifact_owner_rerun_request"
                and task.get("id") not in {owner_id}
                for task in fake.tasks.values()
            )
        )

    def test_no_idle_closes_superseded_declared_artifact_repair_when_review_verdict_pass_has_readback_context(self) -> None:
        fake = FakeHermes()
        repair_id = "t_" + "readbackblock2"
        owner_id = "t_" + "ownerrerun2"
        review_id = "t_" + "readbackpass2"
        target_id = "t_" + "wu03done"
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "blocked",
            "assignee": "factory-orchestrator",
            "title": "Repair missing declared artifacts for board",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "plan_action": "repair_declared_artifacts",
                    "required_output": "declared_artifact_readback_repair",
                    "repair_target": {"task_ref": target_id, "assignee": "product-sot-planner"},
                }
            ),
            "comments": [{"body": "declared-artifact repair blocked: rerun product-sot-planner for `" + target_id + "`."}],
        }
        fake.tasks[owner_id] = {
            "id": owner_id,
            "status": "done",
            "assignee": "product-sot-planner",
            "title": "Rerun owner worker for missing artifacts in " + target_id,
            "body": json.dumps(
                {"packet_type": "factory_declared_artifact_owner_rerun_request", "target_task_ref": target_id}
            ),
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "declared_artifact_owner_rerun_result": {
                                "status": "RERUN_ARTIFACTS_WRITTEN_REVIEW_REQUIRED",
                                "target_task_id": target_id,
                                "created_independent_readback_task": review_id,
                            }
                        }
                    ),
                }
            ],
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Independent readback review for repaired WU-03 artifacts",
            "body": "Read back artifacts from owner rerun task " + owner_id + " for target task " + target_id + ". runtime readback review",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "summary": "Independent runtime readback PASS for repaired WU-03 artifacts.",
                    "metadata": json.dumps(
                        {
                            "independent_review_result": {
                                "verdict": "PASS",
                                "review_coverage": {"artifact_existence_stat_read_hash": "covered"},
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "declared_artifact_repair_superseded_by_owner_readback_pass")
        self.assertEqual(fake.tasks[repair_id]["status"], "done")

    def test_no_idle_creates_owner_rerun_from_hyphenated_readback_block_summary(self) -> None:
        fake = FakeHermes()
        repair_id = "t_" + "readbackblock3"
        target_id = "t_" + "wu05done"
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "blocked",
            "assignee": "factory-orchestrator",
            "title": "Repair missing declared artifacts for board",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "plan_action": "repair_declared_artifacts",
                    "required_output": "declared_artifact_readback_repair",
                    "repair_target": {
                        "task_ref": "kanban:<redacted>",
                        "title": "F15/WU-05 - System architecture",
                        "missing_artifact_names": ["wu05_system_architecture_packet.md"],
                    },
                }
            ),
            "summary": "declared-artifact-readback BLOCKED: WU-05 packet bytes are missing; requires authoritative artifact restore or product-architect rerun plus fresh security review/readback.",
            "comments": [{"body": "Declared artifact readback repair receipt written for WU-05 target " + target_id + "."}],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "declared_artifact_owner_rerun_task_created")
        self.assertEqual(state["owner_rerun_candidate"]["target_worker"], "product-architect")
        rerun_task = next(
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("packet_type")
            == "factory_declared_artifact_owner_rerun_request"
        )
        self.assertEqual(rerun_task["assignee"], "product-architect")
        body = adapter.parse_json_object(str(rerun_task.get("body") or "{}"))
        self.assertEqual(body["target_task_ref"], target_id)
        self.assertNotIn("redacted", body["target_task_ref"])

    def test_no_idle_closes_routed_repair_after_independent_readback_pass(self) -> None:
        fake = FakeHermes()
        blocked_id = "t_" + "blockedrepair"
        route_id = "t_" + "routerepair"
        owner_repair_id = "t_" + "ownerfix"
        pass_review_id = "t_" + "passreview"
        failed_review_id = "t_" + "failreview"
        fake.tasks[blocked_id] = {
            "id": blocked_id,
            "status": "blocked",
            "assignee": "factory-orchestrator",
            "title": "Repair missing declared artifacts for board",
            "body": json.dumps({"plan_action": "repair_declared_artifacts"}),
        }
        fake.tasks[failed_review_id] = {
            "id": failed_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Readback review failed",
            "body": "review FAIL for " + blocked_id,
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {"independent_review_result": {"result": "FAIL", "reviewed_task_ref": blocked_id}}
                    ),
                }
            ],
        }
        fake.tasks[route_id] = {
            "id": route_id,
            "status": "done",
            "assignee": "factory-orchestrator",
            "title": "Repair " + blocked_id + " after internal review FAIL",
            "body": "{}",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "orchestration_result": {
                                "result": "ROUTED_REPAIR_TO_OWNER_AND_REVIEW",
                                "target_repair_task_ref": blocked_id,
                                "created_product_architect_repair": owner_repair_id,
                                "created_independent_readback_review": pass_review_id,
                            }
                        }
                    ),
                }
            ],
        }
        fake.tasks[owner_repair_id] = {
            "id": owner_repair_id,
            "status": "done",
            "assignee": "product-architect",
            "title": "Owner repair",
            "body": "{}",
        }
        fake.tasks[pass_review_id] = {
            "id": pass_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Readback review PASS",
            "body": "bounded readback review pass",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "independent_review_result": {
                                "result": "PASS",
                                "owner_repair_task_ref": owner_repair_id,
                                "repair_target_task_ref": "t_" + "targetwu05",
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_pass_reduced_blockers")
        self.assertEqual(fake.tasks[blocked_id]["status"], "done")
        self.assertFalse(
            any(
                str(task.get("title") or "").startswith("Repair " + blocked_id + " after internal review FAIL")
                and task.get("id") not in {route_id}
                for task in fake.tasks.values()
            )
        )

    def test_declared_artifact_repair_idempotency_is_scoped_to_missing_target(self) -> None:
        def plan_for_missing(task_id: str, artifact_name: str) -> dict[str, Any]:
            fake = FakeHermes()
            with tempfile.TemporaryDirectory() as tmpdir:
                missing_artifact = Path(tmpdir) / artifact_name
                fake.tasks[task_id] = {
                    "id": task_id,
                    "status": "done",
                    "assignee": "independent-reviewer",
                    "title": "Materialize architecture_review_packet for board",
                    "body": "{}",
                    "workspace_path": str(Path(tmpdir)),
                    "runs": [
                        {
                            "status": "done",
                            "outcome": "completed",
                            "metadata": json.dumps({"artifacts": [str(missing_artifact)]}),
                        }
                    ],
                }
                rows = {
                    "ready": [],
                    "running": [],
                    "todo": [],
                    "blocked": [],
                    "triage": [],
                    "done": [{"id": task_id, **fake.tasks[task_id]}],
                }
                rows = adapter.enrich_no_idle_rows(hermes_bin="hermes", board=TEST_BOARD, rows=rows, runner=fake)
                return adapter.build_board_reconcile_plan_from_rows(board=TEST_BOARD, rows=rows)

        first = plan_for_missing("t_" + "archrev1", "architecture_review_packet.first.json")
        second = plan_for_missing("t_" + "archrev2", "architecture_review_packet.second.json")

        first_body = adapter.deterministic_reconcile_task_body(plan=first)
        second_body = adapter.deterministic_reconcile_task_body(plan=second)

        self.assertIsNotNone(first_body)
        self.assertIsNotNone(second_body)
        self.assertNotEqual(adapter.contract_digest(first_body), adapter.contract_digest(second_body))
        self.assertNotEqual(
            first_body["idempotency_scope"]["target_fingerprint"],
            second_body["idempotency_scope"]["target_fingerprint"],
        )
        self.assertIn("architecture_review_packet", first_body["repair_blocked_reasons"][0])
        self.assertIn("architecture_review_packet", second_body["repair_blocked_reasons"][0])

    def test_no_idle_does_not_loop_on_self_evidenced_declared_artifact_repair(self) -> None:
        fake = FakeHermes()
        repair_id = "t_" + "repair01"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_json = Path(tmpdir) / "declared-artifact-readback-repair.json"
            missing_md = Path(tmpdir) / "declared-artifact-readback-repair.md"
            fake.tasks[repair_id] = {
                "id": repair_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Repair missing declared artifacts for board",
                "body": json.dumps(
                    {
                        "packet_type": "factory_deterministic_reconcile_task",
                        "plan_action": "repair_declared_artifacts",
                        "required_output": "declared_artifact_readback_repair",
                        "agent_may_choose_phase": False,
                        "kanban_workflow_binding": {
                            "workflow_template_id": "overkill-vfinal",
                            "current_step_key": "F1-intake",
                            "runtime_field_required": True,
                        },
                    }
                ),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "repair_status": "PASS",
                                "verification": {"file_readback": "PASS"},
                                "artifacts": [str(missing_json), str(missing_md)],
                            }
                        ),
                    }
                ],
                "events": [
                    {
                        "type": "completed",
                        "payload": {
                            "summary": "repair PASS",
                            "artifacts": [str(missing_json), str(missing_md)],
                        },
                    }
                ],
            }
            args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

            result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertNotEqual(state["classification"], "repair_declared_artifacts")
        self.assertFalse(
            any(
                adapter.parse_json_object(str(task.get("body") or "{}")).get("plan_action")
                == "repair_declared_artifacts"
                for task in fake.tasks.values()
                if task.get("id") != repair_id
            )
        )
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_does_not_loop_on_result_pass_declared_artifact_repair(self) -> None:
        fake = FakeHermes()
        repair_id = "t_" + "repair02"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_json = Path(tmpdir) / "declared-artifact-readback-repair.json"
            missing_md = Path(tmpdir) / "declared-artifact-readback-repair.md"
            fake.tasks[repair_id] = {
                "id": repair_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Repair missing declared artifacts for board",
                "body": json.dumps(
                    {
                        "packet_type": "factory_deterministic_reconcile_task",
                        "plan_action": "repair_declared_artifacts",
                        "required_output": "declared_artifact_readback_repair",
                        "agent_may_choose_phase": False,
                        "kanban_workflow_binding": {
                            "workflow_template_id": "overkill-vfinal",
                            "current_step_key": "F1-intake",
                            "runtime_field_required": True,
                        },
                    }
                ),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "result": "PASS",
                                "repair_type": "declared_artifact_readback_repair",
                                "current_repair_artifacts": [str(missing_json), str(missing_md)],
                                "verification": {"json_parse": "PASS", "sha256sum": "PASS"},
                                "artifacts": [str(missing_json), str(missing_md)],
                            }
                        ),
                    }
                ],
                "events": [
                    {
                        "type": "completed",
                        "payload": {
                            "summary": "repair PASS",
                            "artifacts": [str(missing_json), str(missing_md)],
                        },
                    }
                ],
            }
            args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

            result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertNotEqual(state["classification"], "repair_declared_artifacts")
        self.assertFalse(
            any(
                adapter.parse_json_object(str(task.get("body") or "{}")).get("plan_action")
                == "repair_declared_artifacts"
                for task in fake.tasks.values()
                if task.get("id") != repair_id
            )
        )
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_normalizes_absolute_workspace_for_remediation_create(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "doneabs1"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "VALIDATION_RECEIPT.final.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Prepare validation receipt",
                "body": "{}",
                "workspace_path": str(Path(tmpdir)),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(missing_artifact)]}),
                    }
                ],
            }
            absolute_workspace = str(Path(tmpdir) / "no-idle-workspace")
            args = adapter.build_parser().parse_args(
                [
                    "no-idle",
                    "--board",
                    TEST_BOARD,
                    "--create-remediation",
                    "--workspace",
                    absolute_workspace,
                ]
            )

            result = adapter.no_idle(args, runner=fake)

        self.assertIsNotNone(result["remediation_task_id"])
        create_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "create"]
        self.assertTrue(create_calls)
        workspace_value = create_calls[-1][create_calls[-1].index("--workspace") + 1]
        self.assertTrue(workspace_value.startswith("dir:"))

    def test_no_idle_routes_blocked_readback_repair_to_architecture_regeneration(self) -> None:
        fake = FakeHermes()
        stale_arch_id = "t_" + "archstale"
        repair_id = "t_" + "readback"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "ARCHITECTURE_PACKET.example.md"
            fake.tasks[stale_arch_id] = {
                "id": stale_arch_id,
                "status": "done",
                "assignee": "product-architect",
                "title": "Materialize architecture_packet for board",
                "body": "{}",
                "workspace_path": str(Path(tmpdir)),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(missing_artifact)]}),
                    }
                ],
            }
            fake.tasks[repair_id] = {
                "id": repair_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Repair missing declared artifacts for board",
                "body": json.dumps({"required_output": "declared_artifact_readback_repair"}),
                "completed_at": "2026-06-27T09:10:00+00:00",
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "orchestration_result": {
                                    "required_output": "declared_artifact_readback_repair",
                                    "readback_status": "runtime_artifact_integrity_blocked",
                                    "next_worker_actions": [
                                        "product-architect: regenerate/repair architecture_packet artifacts again"
                                    ],
                                }
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

        plan = result["board_reconcile_plan"]
        self.assertEqual(plan["plan_action"], "create_next_artifact_task")
        self.assertEqual(plan["create_task_contract"]["body"]["required_output"], "architecture_packet")
        self.assertEqual(plan["create_task_contract"]["assignee"], "product-architect")
        created_architecture_repairs = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_packet"
        ]
        self.assertEqual(len(created_architecture_repairs), 1)

    def test_no_idle_replaces_stale_declared_artifact_repair_task(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "doneart1"
        stale_id = "t_" + "5a1eaa11"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "VALIDATION_RECEIPT.final.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "human-gate-clerk",
                "title": "Prepare Product SOT owner decision package",
                "body": "{}",
                "workspace_path": str(Path(tmpdir)),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(missing_artifact)]}),
                    }
                ],
            }
            fake.tasks[stale_id] = {
                "id": stale_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Repair missing declared artifacts for board",
                "body": json.dumps({"marker": "factory_deterministic_reconcile"}),
                "events": [{"type": "completed"}],
            }
            rows = {
                "ready": [],
                "running": [],
                "todo": [],
                "blocked": [],
                "triage": [],
                "done": [{"id": done_id, **fake.tasks[done_id]}, {"id": stale_id, **fake.tasks[stale_id]}],
            }
            rows = adapter.enrich_no_idle_rows(hermes_bin="hermes", board=TEST_BOARD, rows=rows, runner=fake)
            plan = adapter.build_board_reconcile_plan_from_rows(board=TEST_BOARD, rows=rows)
            body = adapter.deterministic_reconcile_task_body(plan=plan)
            self.assertIsNotNone(body)
            digest = adapter.idempotency_digest_fragment(adapter.contract_digest(body))
            fake.idempotent_task_ids[f"overkill:reconcile:{adapter.public_safe_slug(TEST_BOARD, fallback='board')}:{digest}"] = stale_id
            fake.calls.clear()
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(
            state["classification"],
            "deterministic_board_reconcile_task_created_after_stale_terminal_replacement",
        )
        self.assertEqual(state["stale_remediation_task_refs"], ["kanban:<redacted>"])
        self.assertEqual(state["remediation_replacement_attempts"], 1)
        self.assertTrue(state["native_dispatch_required_next"])
        replacements = [
            task for task in fake.tasks.values()
            if task.get("status") == "ready"
            and adapter.parse_json_object(str(task.get("body") or "{}")).get("stale_terminal_remediation_replacement") is True
        ]
        self.assertEqual(len(replacements), 1)
        replacement_body = adapter.parse_json_object(str(replacements[0].get("body") or "{}"))
        self.assertEqual(replacement_body["plan_action"], "repair_declared_artifacts")

    def test_no_idle_recovers_empty_stdout_idempotency_replay_before_replacement(self) -> None:
        fake = EmptyStdoutIdempotentHermes()
        done_id = "t_" + "doneart2"
        stale_id = "t_" + "5a1eaa12"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "ARCHITECTURE_PACKET.example.md"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "product-architect",
                "title": "Materialize architecture_packet for board",
                "body": "{}",
                "workspace_path": str(Path(tmpdir)),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(missing_artifact)]}),
                    }
                ],
            }
            rows = {
                "ready": [],
                "running": [],
                "todo": [],
                "blocked": [],
                "triage": [],
                "done": [{"id": done_id, **fake.tasks[done_id]}],
            }
            rows = adapter.enrich_no_idle_rows(hermes_bin="hermes", board=TEST_BOARD, rows=rows, runner=fake)
            plan = adapter.build_board_reconcile_plan_from_rows(board=TEST_BOARD, rows=rows)
            body = adapter.deterministic_reconcile_task_body(plan=plan)
            self.assertIsNotNone(body)
            digest = adapter.idempotency_digest_fragment(adapter.contract_digest(body))
            replay_key = f"overkill:reconcile:{adapter.public_safe_slug(TEST_BOARD, fallback='board')}:{digest}"
            fake.idempotent_task_ids[replay_key] = stale_id
            fake.tasks[stale_id] = {
                "id": stale_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Repair missing declared artifacts for board",
                "body": json.dumps(body),
                "idempotency_key": replay_key,
                "events": [{"type": "completed"}],
            }
            fake.calls.clear()
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(
            state["classification"],
            "deterministic_board_reconcile_task_created_after_stale_terminal_replacement",
        )
        self.assertEqual(state["stale_remediation_task_refs"], ["kanban:<redacted>"])
        replacements = [
            task for task in fake.tasks.values()
            if task.get("status") == "ready"
            and adapter.parse_json_object(str(task.get("body") or "{}")).get("stale_terminal_remediation_replacement") is True
        ]
        self.assertEqual(len(replacements), 1)

    def test_missing_declared_artifacts_accepts_decision_package_basename_match(self) -> None:
        done_id = "t_" + "donepkg1"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            declared_root_path = workspace / "HUMAN_GATE_RECORD.approved.json"
            actual_package_path = workspace / "decision-package" / "HUMAN_GATE_RECORD.approved.json"
            actual_package_path.parent.mkdir(parents=True, exist_ok=True)
            actual_package_path.write_text(json.dumps({"decision": "approved"}), encoding="utf-8")
            record = {
                "id": done_id,
                "status": "done",
                "workspace_path": str(workspace),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(declared_root_path)]}),
                    }
                ],
            }

            missing = adapter.missing_declared_local_artifacts(record)

        self.assertEqual(missing, [])

    def test_no_idle_does_not_repair_declared_artifact_present_in_decision_package(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "donepkg2"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            declared_root_path = workspace / "VALIDATION_RECEIPT.final.json"
            actual_package_path = workspace / "decision-package" / "VALIDATION_RECEIPT.final.json"
            actual_package_path.parent.mkdir(parents=True, exist_ok=True)
            actual_package_path.write_text(json.dumps({"status": "valid"}), encoding="utf-8")
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "human-gate-clerk",
                "title": "Prepare Product SOT owner decision package",
                "body": "{}",
                "workspace_path": str(workspace),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(declared_root_path)]}),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertNotEqual(state["classification"], "repair_declared_artifacts")
        self.assertFalse(any(
            adapter.parse_json_object(str(task.get("body") or "{}")).get("plan_action") == "repair_declared_artifacts"
            for task in fake.tasks.values()
        ))

    def test_no_idle_materializes_invalid_declared_json_from_metadata(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "donebad1"
        with tempfile.TemporaryDirectory() as tmpdir:
            artifact = Path(tmpdir) / "orchestration_result.result.json"
            artifact.write_text('{"orchestration_result": {"truncated": true}', encoding="utf-8")
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Route approved Product SOT to planning",
                "body": "{}",
                "workspace_path": str(Path(tmpdir)),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "orchestration_result": {"status": "completed", "task_id": done_id},
                                "artifacts": [str(artifact)],
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)
            recovered = json.loads(artifact.read_text(encoding="utf-8"))

        self.assertEqual(recovered["orchestration_result"]["status"], "completed")
        self.assertTrue(any(
            item.get("materialized") is True
            and item.get("artifact_name") == "orchestration_result.result.json"
            for item in result["artifact_materialization"]
        ))

    def test_log_diff_payload_recovers_artifact_inside_decision_package(self) -> None:
        log_text = "\n".join(
            [
                "  ┊ review diff",
                "a/decision-package/HUMAN_GATE_RECORD.approved.json → b/decision-package/HUMAN_GATE_RECORD.approved.json",
                "@@ -0,0 +1,4 @@",
                "+{",
                "+  \"decision\": \"approved\"",
                "+}",
                "  ┊ next tool",
            ]
        )

        payload = adapter.log_diff_payload_for_declared_artifact(log_text, "HUMAN_GATE_RECORD.approved.json")

        self.assertEqual(json.loads(payload or "{}")["decision"], "approved")

    def test_no_idle_materializes_missing_declared_json_from_run_metadata_before_repair(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "done0002"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "product-sot-result.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "product-sot-planner",
                "title": "F5 - Product SOT candidate",
                "body": "{}",
                "events": [
                    {
                        "type": "completed",
                        "payload": {"artifacts": [str(missing_artifact)]},
                    }
                ],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "product_sot_result": {
                                    "artifact_file": "product-sot-result.json",
                                    "status": "candidate_owner_review_required_not_approved",
                                    "next_required_gate": "Product SOT owner review",
                                },
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

            self.assertTrue(missing_artifact.exists())
            recovered = json.loads(missing_artifact.read_text(encoding="utf-8"))
            self.assertEqual(
                recovered["product_sot_result"]["status"],
                "candidate_owner_review_required_not_approved",
            )
            self.assertEqual(result["board_reconcile_plan"]["plan_action"], "no_unfinished_work")
            self.assertIsNotNone(result["remediation_task_id"])
            self.assertEqual(
                result["no_idle_state"]["classification"],
                "deterministic_post_review_owner_gate_package_task_created",
            )
            self.assertEqual(result["artifact_materialization"][0]["materialized"], True)
            self.assertEqual(result["artifact_materialization"][0]["recovery_source"], "task_runs.metadata")
            self.assertFalse(
                any(
                    adapter.parse_json_object(str(task.get("body") or "{}")).get("plan_action")
                    == "repair_declared_artifacts"
                    for task in fake.tasks.values()
                )
            )

    def test_no_idle_prefers_worker_log_diff_over_summary_metadata_for_json(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "done0004"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "source-ledger-result.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "source-ledger-worker",
                "title": "F2 - Source ledger",
                "body": "{}",
                "events": [{"type": "completed", "payload": {"artifacts": [str(missing_artifact)]}}],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "source_ledger_result": {
                                    "artifact_file": "source-ledger-result.json",
                                    "summary_only": True,
                                },
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            fake.logs[done_id] = "\n".join(
                [
                    "  ┊ review diff",
                    "a/source-ledger-result.json -> b/source-ledger-result.json",
                    "@@ -0,0 +1,7 @@",
                    "+{",
                    "+  \"source_ledger_result\": {",
                    "+    \"artifact_file\": \"source-ledger-result.json\",",
                    "+    \"full_payload_from_log\": true",
                    "+  }",
                    "+}",
                    "  ┊ ⚡ kanban_complete",
                ]
            )
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

            recovered = json.loads(missing_artifact.read_text(encoding="utf-8"))
            self.assertTrue(recovered["source_ledger_result"]["full_payload_from_log"])
            self.assertNotIn("summary_only", recovered["source_ledger_result"])
            self.assertEqual(result["artifact_materialization"][0]["materialized"], True)
            self.assertEqual(result["artifact_materialization"][0]["recovery_source"], "worker_log_diff")

    def test_no_idle_rejects_invalid_log_diff_json_and_falls_back_to_metadata(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "done0005"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "source-ledger-result.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "source-ledger-worker",
                "title": "F2 - Source ledger",
                "body": "{}",
                "events": [{"type": "completed", "payload": {"artifacts": [str(missing_artifact)]}}],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "source_ledger_result": {
                                    "artifact_file": "source-ledger-result.json",
                                    "valid_payload_from_metadata": True,
                                },
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            fake.logs[done_id] = "\n".join(
                [
                    "  ┊ review diff",
                    "a/source-ledger-result.json -> b/source-ledger-result.json",
                    "@@ -0,0 +1,5 @@",
                    "+{",
                    "+  \"source_ledger_result\": {",
                    "+    \"broken\": true",
                    "  ┊ ⚡ kanban_complete",
                ]
            )
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

            recovered = json.loads(missing_artifact.read_text(encoding="utf-8"))
            self.assertTrue(recovered["source_ledger_result"]["valid_payload_from_metadata"])
            self.assertEqual(result["artifact_materialization"][0]["materialized"], True)
            self.assertEqual(result["artifact_materialization"][0]["recovery_source"], "task_runs.metadata")

    def test_no_idle_reconstructs_human_gate_record_from_run_metadata(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "gate0001"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "decision-package" / "HUMAN_GATE_RECORD.approved.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "human-gate-clerk",
                "title": "Prepare Product SOT owner decision package",
                "body": "{}",
                "events": [{"type": "completed", "payload": {"artifacts": [str(missing_artifact)]}}],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "decision": {
                                    "actor_role": "Factory Owner",
                                    "captured_at": "2026-06-27T04:21:22Z",
                                    "code": "APPROVE_PRODUCT_SOT",
                                    "recorded_at": "2026-06-27T04:23:36Z",
                                    "value": "approved",
                                },
                                "approval_scope": ["Product SOT boundary only"],
                                "forbidden_scope": ["implementation", "deployment"],
                                "delivery_evidence": ["telegram_delivery:message_ref:1139"],
                                "validation": {"json_valid": True},
                                "hashes": {"HUMAN_GATE_RECORD.approved.md": "abc123"},
                                "next_child_task": "task:next-planning",
                                "next_frontier": ["Method Contract planning"],
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

            recovered = json.loads(missing_artifact.read_text(encoding="utf-8"))
            record = recovered["human_gate_record"]
            self.assertEqual(record["decision"]["code"], "APPROVE_PRODUCT_SOT")
            self.assertEqual(record["decision_state"], "approved")
            self.assertIn("Product SOT boundary only", record["approval_scope"])
            self.assertEqual(record["reconstructed_from"], "task_runs.metadata")
            self.assertEqual(result["artifact_materialization"][0]["materialized"], True)
            self.assertEqual(result["artifact_materialization"][0]["recovery_source"], "task_runs.metadata")

    def test_no_idle_materializes_missing_markdown_from_worker_log_diff_before_repair(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "done0003"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "product-sot-candidate.md"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "product-sot-planner",
                "title": "F5 - Product SOT candidate",
                "body": "{}",
                "events": [
                    {
                        "type": "completed",
                        "payload": {"artifacts": [str(missing_artifact)]},
                    }
                ],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "product_sot_result": {
                                    "artifact_file": "product-sot-result.json",
                                    "review_packet_file": "product-sot-candidate.md",
                                    "status": "candidate_owner_review_required_not_approved",
                                },
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            fake.logs[done_id] = "\n".join(
                [
                    "  ┊ review diff",
                    "a/product-sot-candidate.md -> b/product-sot-candidate.md",
                    "@@ -0,0 +1,4 @@",
                    "+# Product SOT candidate - Todo Web Local",
                    "+",
                    "+Status: candidate for owner review only.",
                    "+Next gate: Product SOT owner review.",
                    "  ┊ ⚡ kanban_complete",
                ]
            )
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

            self.assertEqual(
                missing_artifact.read_text(encoding="utf-8"),
                "# Product SOT candidate - Todo Web Local\n\n"
                "Status: candidate for owner review only.\n"
                "Next gate: Product SOT owner review.\n",
            )
            self.assertEqual(result["board_reconcile_plan"]["plan_action"], "no_unfinished_work")
            self.assertIsNotNone(result["remediation_task_id"])
            self.assertEqual(
                result["no_idle_state"]["classification"],
                "deterministic_post_review_owner_gate_package_task_created",
            )
            self.assertEqual(result["artifact_materialization"][0]["materialized"], True)
            self.assertEqual(result["artifact_materialization"][0]["recovery_source"], "worker_log_diff")

    def test_no_idle_reconstructs_missing_markdown_from_structured_metadata(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "arch0001"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "ARCHITECTURE_PACKET_Todo_Web_Local.md"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "product-architect",
                "title": "Materialize architecture_packet",
                "body": "{}",
                "events": [{"type": "completed", "payload": {"artifacts": [str(missing_artifact)]}}],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "architecture_result": {
                                    "status": "candidate_architecture_packet_ready_for_independent_review_not_closed",
                                    "task_id": done_id,
                                    "artifact_paths": [str(missing_artifact)],
                                    "artifact_sha256": {"ARCHITECTURE_PACKET_Todo_Web_Local.md": "abc123"},
                                    "validation": {"required_md_sections_missing": []},
                                    "candidate_decisions": ["client-only local browser runtime"],
                                    "review_requirements": ["independent architecture review"],
                                    "downstream_frozen": ["implementation"],
                                },
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

            recovered = missing_artifact.read_text(encoding="utf-8")
            self.assertIn("Reconstructed Markdown readback", recovered)
            self.assertIn("client-only local browser runtime", recovered)
            self.assertIn("independent architecture review", recovered)
            self.assertEqual(result["artifact_materialization"][0]["materialized"], True)
            self.assertEqual(
                result["artifact_materialization"][0]["recovery_source"],
                "task_runs.metadata_markdown",
            )

    def test_no_idle_reconstructs_architecture_markdown_from_artifacts_dict_metadata(self) -> None:
        fake = FakeHermes()
        done_id = "t_" + "arch0004"
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            missing_artifact = workspace / f"ARCHITECTURE_PACKET_Todo_Web_Local.{done_id}.md"
            json_artifact = workspace / f"architecture_packet.{done_id}.json"
            manifest_artifact = workspace / f"architecture_packet_manifest.{done_id}.json"
            fake.tasks[done_id] = {
                "id": done_id,
                "status": "done",
                "assignee": "product-architect",
                "title": "Materialize architecture_packet",
                "body": "{}",
                "events": [{"type": "completed", "payload": {"artifacts": [str(missing_artifact)]}}],
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "architecture_result": {
                                    "status": "candidate_architecture_packet_ready_for_independent_review_not_closed",
                                    "task_id": done_id,
                                    "artifacts": {
                                        "json": str(json_artifact),
                                        "markdown": str(missing_artifact),
                                        "manifest": str(manifest_artifact),
                                    },
                                    "sha256": {
                                        json_artifact.name: "a" * 64,
                                        missing_artifact.name: "b" * 64,
                                        manifest_artifact.name: "c" * 64,
                                    },
                                    "validation": {"missing_required_markdown_sections": []},
                                    "candidate_decisions": ["local-first browser Todo"],
                                    "review_requirements": ["independent architecture review rerun"],
                                    "downstream_frozen": ["implementation", "decomposition"],
                                },
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

            recovered = missing_artifact.read_text(encoding="utf-8")
            self.assertIn("Reconstructed Markdown readback", recovered)
            self.assertIn("local-first browser Todo", recovered)
            self.assertIn(missing_artifact.name, recovered)
            self.assertIn("b" * 64, recovered)
            self.assertEqual(result["artifact_materialization"][0]["materialized"], True)
            self.assertEqual(result["artifact_materialization"][0]["recovery_source"], "task_runs.metadata_markdown")

    def test_no_idle_reconciles_declared_f9_to_f5_owner_package_before_gate(self) -> None:
        fake = FakeHermes()
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        materialize_product_sot_frontier(card)
        card["phase"] = "F9"
        card["surfaces"] = ["architecture", "planning"]
        card["autonomy_mode"] = "planning_only"
        card["risk_initial"] = "R2"
        card["risk_effective"] = "R2"
        card.pop("factory_phase_lock", None)
        card.pop("operator_briefing_package_ref", None)
        card["review"]["human_gate_required"] = False
        card["review"]["CTO_gate_required"] = False
        fake.tasks["t_" + "phasejump1"] = {
            "id": "t_" + "phasejump1",
            "status": "todo",
            "assignee": "human-gate-clerk",
            "title": "Human architecture gate",
            "body": json.dumps(card),
            "events": [],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        plan = result["board_reconcile_plan"]
        self.assertEqual(plan["plan_action"], "create_next_artifact_task")
        self.assertEqual(plan["phase_engine"]["computed_phase_id"], "F5")
        self.assertEqual(plan["phase_engine"]["next_required_artifact"], "operator_briefing_package")
        self.assertFalse(plan["human_gate_required"])
        created_task = next(
            task for task in fake.tasks.values()
            if json.loads(str(task.get("body") or "{}")).get("marker") == "factory_deterministic_reconcile"
        )
        body = json.loads(str(created_task["body"]))
        self.assertEqual(body["required_output"], "operator_briefing_package")
        self.assertEqual(body["plan_action"], "create_next_artifact_task")
        self.assertFalse(body["agent_may_choose_phase"])

    def test_no_idle_reports_human_gate_without_remediation(self) -> None:
        fake = FakeHermes()
        fake.tasks["t_" + "gate0001"] = {
            "id": "t_" + "gate0001",
            "status": "blocked",
            "assignee": "human-gate-clerk",
            "body": json.dumps(
                {
                    "marker": "human_gate",
                    "reason": "awaiting human approval",
                    "human_gate_packet": human_gate_packet_fixture(),
                }
            ),
            "events": [{"type": "blocked", "reason": "human gate"}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["no_idle_state"]["status"], "human_gate_required")
        self.assertTrue(result["no_idle_state"]["human_gate_required"])
        self.assertIn("human_decision_request", result["no_idle_state"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_treats_incomplete_human_gate_package_as_factory_repair(self) -> None:
        fake = FakeHermes()
        fake.tasks["t_" + "gate0001"] = {
            "id": "t_" + "gate0001",
            "status": "blocked",
            "assignee": "human-gate-clerk",
            "body": (
                "human gate packet is not approval-ready: missing operator briefing package, "
                "APPROVAL_REQUEST, EVIDENCE_INDEX, OWNER_REVIEW and pdf"
            ),
            "events": [{"type": "blocked", "reason": "missing decision package"}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "deterministic_factory_package_dependency_repair_task_created")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertIn("factory-owned", state["remediation_reason"])
        self.assertIsNotNone(result["remediation_task_id"])
        self.assertTrue(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_creates_targeted_repair_for_failed_independent_review(self) -> None:
        fake = FakeHermes()
        review_id = "t_" + "review01"
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "blocked",
            "assignee": "independent-reviewer",
            "title": "F3 - Independent review of Product SOT candidate",
            "latest_summary": (
                "review-failed: Product SOT package source meaning is aligned, but "
                "required factoryctl validators fail and handoff sequencing is inconsistent."
            ),
            "body": "review Product SOT, outcome_contract and full_product_sot_scope_coverage",
            "comments": [
                {
                    "author": "independent-reviewer",
                    "body": (
                        "Independent review result: FAIL / BLOCK. Required fixes: repair "
                        "factoryctl validators fail, preserve candidate-only, rerun independent review."
                    ),
                }
            ],
            "events": [
                {
                    "type": "blocked",
                    "reason": "review-failed: validators fail; rerun independent review after repair",
                }
            ],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "deterministic_targeted_review_repair_task_created")
        self.assertEqual(state["remediation_strategy"], "create_targeted_review_repair_task")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertTrue(state["remediation_task_created"])
        self.assertEqual(state["remediation_task_status"], "ready")
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "repair_board_contract")
        self.assertIsNotNone(result["targeted_remediation_plan"])
        created_task = next(
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("marker") == "factory_no_idle_review_repair"
        )
        self.assertEqual(created_task["status"], "ready")
        self.assertEqual(created_task["assignee"], "product-sot-planner")
        body = json.loads(str(created_task["body"]))
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F5-product-sot")
        self.assertIn("ask the operator for approval or input for internal validator repair", body["forbidden_actions"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_advances_repaired_review_pass_to_owner_gate_package(self) -> None:
        fake = FakeHermes()
        failed_review_id = "t_" + "review01"
        repair_id = "t_" + "repair01"
        pass_review_id = "t_" + "review02"
        fake.tasks[failed_review_id] = {
            "id": failed_review_id,
            "status": "blocked",
            "assignee": "independent-reviewer",
            "title": "F3 - Independent review of Product SOT candidate",
            "latest_summary": "review-failed: required factoryctl validators fail and handoff sequencing is inconsistent.",
            "body": "review Product SOT package",
            "events": [{"type": "blocked", "reason": "review-failed: validators fail"}],
        }
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "done",
            "assignee": "product-sot-planner",
            "title": "Repair failed independent review package",
            "body": json.dumps(
                {
                    "marker": "factory_no_idle_review_repair",
                    "blocked_review_task_refs": [failed_review_id],
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "repair complete"}}],
        }
        fake.tasks[pass_review_id] = {
            "id": pass_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "F3 - Independent review of repaired Product SOT candidate",
            "latest_summary": (
                "Independent review PASS for the repaired Product SOT candidate package; "
                "next gate is owner/Product SOT approval or rebaseline before method-contract planning."
            ),
            "body": "review repaired Product SOT package",
            "parents": [repair_id],
            "events": [
                {
                    "type": "completed",
                    "payload": {
                        "summary": (
                            "Independent review PASS; owner/Product SOT approval or rebaseline "
                            "is still required before method-contract planning."
                        )
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(
            ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
        )

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "deterministic_post_review_owner_gate_package_task_created")
        self.assertEqual(state["remediation_strategy"], "create_post_review_owner_gate_package_task")
        self.assertEqual(state["ignored_superseded_blocked_task_refs"], ["kanban:<redacted>"])
        self.assertEqual(state["post_review_task_refs"], ["kanban:<redacted>"])
        self.assertTrue(state["remediation_task_created"])
        self.assertEqual(state["remediation_task_status"], "ready")
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertIsNotNone(result["targeted_remediation_plan"])
        created_task = next(
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("marker")
            == "factory_no_idle_post_review_gate_package"
        )
        self.assertEqual(created_task["status"], "ready")
        self.assertEqual(created_task["assignee"], "human-gate-clerk")
        body = json.loads(str(created_task["body"]))
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F5-product-sot")
        self.assertTrue(body["human_gate_required"])
        self.assertIn(
            "prepare a canonical owner-facing Product SOT document in the operator locale as the primary human artifact",
            body["required_actions"],
        )
        self.assertIn(
            "keep APPROVAL_REQUEST, EVIDENCE_INDEX, OWNER_REVIEW, hashes, schemas and validation receipts as supporting evidence, not as the SOT body",
            body["required_actions"],
        )
        self.assertIn(
            "when a primary operator channel such as Telegram is configured, deliver a short plain-text decision message and the Product SOT markdown/PDF as standard file attachments through the manager/operator-facing profile; do not use Telegram rich cards, rich drafts, media groups or table-rendered bot messages",
            body["required_actions"],
        )
        self.assertIn("ask for a decision from a chat summary without the decision package material", body["forbidden_actions"])
        self.assertIn(
            "deliver an operational receipt, approval JSON, evidence index, hash list or worker log as if it were the Product SOT",
            body["forbidden_actions"],
        )
        self.assertIn(
            "send Telegram rich cards, rich drafts, media groups or table-rendered bot messages as the primary decision package",
            body["forbidden_actions"],
        )
        self.assertIn(
            "deliver an English-only Product SOT when the operator-facing language is Portuguese",
            body["forbidden_actions"],
        )
        self.assertIn(
            "treat a Kanban comment alone as delivered material when a primary operator channel is configured",
            body["forbidden_actions"],
        )
        self.assertIn(
            "send the operator-facing gate from a non-manager profile when a manager/operator-facing profile is configured",
            body["forbidden_actions"],
        )
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_blocks_ready_future_phase_when_prior_phase_is_blocked(self) -> None:
        fake = FakeHermes()
        fake.tasks["t_" + "f3block"] = {
            "id": "t_" + "f3block",
            "status": "blocked",
            "title": "F3 source resolution blocked",
            "current_step_key": "F3-source-resolution",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F3-source-resolution",
                    },
                }
            ),
        }
        fake.tasks["t_" + "f4ready"] = {
            "id": "t_" + "f4ready",
            "status": "ready",
            "title": "F4 outcome work",
            "current_step_key": "F4-product-outcome-and-discovery",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F4-product-outcome-and-discovery",
                    },
                }
            ),
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["classification"], "factory_phase_invariant_violation")
        self.assertFalse(state["native_dispatch_required_next"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "block_invariant_violation")
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_blocks_active_task_without_deterministic_runtime_contract(self) -> None:
        fake = FakeHermes()
        fake.tasks["t_" + "freef10"] = {
            "id": "t_" + "freef10",
            "status": "running",
            "assignee": "product-architect",
            "title": "F10 repair/rerun architecture_packet artifacts for Todo Web Local",
            "body": (
                "Factory bounded repair route. Phase: F10 architecture. "
                "Required output: repaired architecture_packet."
            ),
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "blocked")
        self.assertEqual(state["classification"], "factory_phase_invariant_violation")
        self.assertFalse(state["native_dispatch_required_next"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "block_invariant_violation")
        self.assertEqual(
            result["board_reconcile_plan"]["reason"],
            "active Hermes work is missing deterministic runtime contract",
        )
        self.assertTrue(
            any(
                "cannot proceed without deterministic runtime contract" in reason
                for reason in result["board_reconcile_plan"]["blocked_reasons"]
            )
        )
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_closes_over_time_running_task_with_valid_worker_result(self) -> None:
        fake = FakeHermes()
        running_id = "t_" + "runclose1"
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        worker_result = factoryctl.build_worker_result(
            "implementation-worker",
            card,
            result="PASS",
            tool_or_profile="implementation-worker",
            executed_by="implementation-worker",
            evidence_refs=["external:test:todo-implementation"],
            blocking_findings=False,
            findings_summary="Todo implementation completed with local tests.",
            next_action="ready for Receipt Five reconciliation",
        )
        fake.tasks[running_id] = {
            "id": running_id,
            "status": "running",
            "assignee": "implementation-worker",
            "title": "F15 implement Todo Web Local",
            "current_step_key": "F15-runtime-execution",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "plan_action": "execute_ready_work_unit",
                    "agent_may_choose_phase": False,
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F15-runtime-execution",
                        "runtime_field_required": True,
                    },
                }
            ),
            "runs": [
                {
                    "status": "running",
                    "started_at": "2020-01-01T00:00:00Z",
                    "metadata": json.dumps({"implementation_result": worker_result}),
                }
            ],
            "events": [{"type": "claimed", "payload": {"run_id": 1}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "running_worker_result_closeout_completed")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertEqual(fake.tasks[running_id]["status"], "done")
        self.assertEqual(fake.tasks[running_id]["result"], "DONE")
        metadata = json.loads(str(fake.tasks[running_id]["metadata"]))
        self.assertEqual(metadata["marker"], adapter.NO_IDLE_RUNNING_RESULT_CLOSEOUT_MARKER)
        self.assertEqual(metadata["closed_from_worker_result"]["record_type"], "implementation_result")
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_creates_internal_review_task_without_operator_status_ping(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "reviewme"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "evidence-reconciler",
            "title": "F15/WU-00 - Freeze/replay source and gate evidence index",
            "body": (
                "review-required: evidence index PASS; independent-reviewer must review before this card is treated as done. "
                "Stop rule mentions operator input/approval only as forbidden escalation, not as the current blocker."
            ),
            "events": [
                {
                    "type": "blocked",
                    "payload": {
                        "kind": "needs_input",
                        "reason": "review-required: independent-reviewer must review before this card is treated as done",
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_task_created")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertTrue(state["native_dispatch_required_next"])
        review_tasks = [
            task for task in fake.tasks.values()
            if adapter.task_body_json_object(task).get("marker") == adapter.NO_IDLE_INTERNAL_REVIEW_REQUEST_MARKER
        ]
        self.assertEqual(len(review_tasks), 1)
        self.assertEqual(review_tasks[0]["status"], "ready")
        self.assertEqual(review_tasks[0]["assignee"], "independent-reviewer")
        self.assertEqual(json.loads(str(review_tasks[0]["body"]))["target_task_ref"], blocker_id)
        parents = review_tasks[0].get("parents")
        self.assertNotIn(blocker_id, parents if isinstance(parents, list) else [])

        second = adapter.no_idle(args, runner=fake)
        self.assertEqual(second["no_idle_state"]["classification"], "internal_review_task_already_exists")
        review_tasks_after = [
            task for task in fake.tasks.values()
            if adapter.task_body_json_object(task).get("marker") == adapter.NO_IDLE_INTERNAL_REVIEW_REQUEST_MARKER
        ]
        self.assertEqual(len(review_tasks_after), 1)

    def test_no_idle_reduces_internal_review_pass_to_original_blocked_task(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "block001"
        review_id = "t_" + "review01"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "evidence-reconciler",
            "title": "F15/WU-00 - Freeze/replay source and gate evidence index",
            "body": "review-required: independent-reviewer must review before this card is treated as done",
            "events": [
                {
                    "type": "blocked",
                    "payload": {
                        "kind": "needs_input",
                        "reason": "review-required: independent-reviewer must review before this card is treated as done",
                    },
                }
            ],
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "F15/WU-00R - Independent review of WU-00 evidence index",
            "body": json.dumps(
                {
                    "record_type": "factory_internal_review_result",
                    "result": "PASS",
                    "reviewed_task_ref": blocker_id,
                    "human_gate_required": False,
                    "operator_input_required": False,
                }
            ),
            "latest_summary": "Independent review PASS for reviewed task; reducer should close the reviewed task.",
            "events": [{"type": "completed", "payload": {"summary": "PASS"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_pass_reduced_blockers")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertEqual(fake.tasks[blocker_id]["status"], "done")
        self.assertEqual(fake.tasks[blocker_id]["result"], "DONE")
        metadata = json.loads(str(fake.tasks[blocker_id]["metadata"]))
        self.assertEqual(metadata["marker"], adapter.NO_IDLE_REVIEW_PASS_REDUCER_MARKER)
        self.assertEqual(metadata["review_task_ref"], review_id)
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_creates_repair_task_for_internal_review_fail(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "blockfail"
        review_id = "t_" + "reviewfail"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "product-architect",
            "title": "F15/WU-01 - 20apy predecessor study",
            "body": "review-required: independent-reviewer must review before this card is done",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "F15/WU-01R - Independent review of WU-01",
            "body": json.dumps(
                {
                    "record_type": "factory_internal_review_result",
                    "result": "FAIL",
                    "reviewed_task_ref": blocker_id,
                    "blocking_findings": ["missing source traceability"],
                    "human_gate_required": False,
                    "operator_input_required": False,
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "FAIL"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_fail_repair_task_created")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertTrue(state["native_dispatch_required_next"])
        repairs = [
            task for task in fake.tasks.values()
            if adapter.task_body_json_object(task).get("marker") == adapter.NO_IDLE_REVIEW_FAIL_REPAIR_MARKER
        ]
        self.assertEqual(len(repairs), 1)
        self.assertEqual(repairs[0]["status"], "ready")
        self.assertEqual(repairs[0]["assignee"], "product-architect")
        repair_body = adapter.task_body_json_object(repairs[0])
        self.assertEqual(repair_body["target_task_ref"], blocker_id)
        self.assertEqual(repair_body["review_task_ref"], review_id)
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_ignores_no_repair_required_duplicate_repair_readback_as_review_fail(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "blockfail"
        repair_id = "t_" + "repairdone"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "cloud-infra-security-specialist",
            "title": "F15/WU-15 - Cloud/IAM/KMS/Secret Manager/budget non-material readiness packet",
            "body": "review-required: independent-reviewer must review before this card is done",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "done",
            "assignee": "cloud-infra-security-specialist",
            "title": "Repair t_blockfail after internal review FAIL",
            "body": json.dumps(
                {
                    "packet_type": "factory_internal_review_fail_repair_request",
                    "marker": adapter.NO_IDLE_REVIEW_FAIL_REPAIR_MARKER,
                    "target_task_ref": blocker_id,
                    "review_task_ref": "t_stale_duplicate",
                }
            ),
            "latest_summary": (
                "NO_REPAIR_REQUIRED. The referenced review task was a completed duplicate/stale "
                "repair readback, not a current independent REVIEW FAIL. Actual independent review already PASS."
            ),
            "events": [{"type": "completed", "payload": {"summary": "NO_REPAIR_REQUIRED not a current independent REVIEW FAIL"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertNotEqual(state["classification"], "internal_review_fail_repair_task_created")
        repairs = [
            task for task in fake.tasks.values()
            if adapter.task_body_json_object(task).get("marker") == adapter.NO_IDLE_REVIEW_FAIL_REPAIR_MARKER
            and task.get("status") == "ready"
        ]
        self.assertEqual(repairs, [])

    def test_no_idle_ignores_done_review_fail_repair_as_existing_active_work(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "blockfail"
        review_id = "t_" + "reviewfail"
        repair_id = "t_" + "repairdone"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "cloud-infra-security-specialist",
            "title": "F15/WU-15 - Cloud/IAM/KMS/Secret Manager/budget non-material readiness packet",
            "body": "review-required: independent-reviewer must review before this card is done",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "F15/WU-15R - Independent review of WU-15",
            "body": json.dumps(
                {
                    "record_type": "factory_internal_review_result",
                    "result": "FAIL",
                    "reviewed_task_ref": blocker_id,
                    "blocking_findings": ["missing route readback"],
                    "human_gate_required": False,
                    "operator_input_required": False,
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "FAIL"}}],
        }
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "done",
            "assignee": "cloud-infra-security-specialist",
            "title": "Repair t_blockfail after internal review FAIL",
            "body": json.dumps(
                {
                    "packet_type": "factory_internal_review_fail_repair_request",
                    "marker": adapter.NO_IDLE_REVIEW_FAIL_REPAIR_MARKER,
                    "target_task_ref": blocker_id,
                    "review_task_ref": review_id,
                }
            ),
            "latest_summary": "NO_REPAIR_REQUIRED stale readback; did not mutate target.",
            "events": [{"type": "completed", "payload": {"summary": "NO_REPAIR_REQUIRED"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertNotEqual(state["classification"], "internal_review_fail_repair_task_already_exists")
        self.assertNotIn(repair_id, state.get("existing_repair_task_refs") or [])

    def test_no_idle_ignores_review_fail_repair_title_even_when_body_marker_missing(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "blockfail"
        repair_id = "t_" + "repairtitle"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "cloud-infra-security-specialist",
            "title": "F15/WU-15 - Cloud/IAM/KMS/Secret Manager/budget non-material readiness packet",
            "body": "review-required: independent-reviewer must review before this card is done",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "done",
            "assignee": "cloud-infra-security-specialist",
            "title": "Repair t_blockfail after internal review FAIL",
            "body": "{}",
            "latest_summary": "NO_REPAIR_REQUIRED not a current independent REVIEW FAIL; stale duplicate readback.",
            "events": [{"type": "completed", "payload": {"summary": "NO_REPAIR_REQUIRED not a current independent REVIEW FAIL"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertNotEqual(state["classification"], "internal_review_fail_repair_task_created")
        self.assertNotEqual(state["classification"], "internal_review_fail_repair_task_already_exists")

    def test_no_idle_review_pass_completion_overrides_instructional_review_fail_text(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "blockpass"
        review_id = "t_" + "reviewpass"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "cloud-infra-security-specialist",
            "title": "F15/WU-15 - Cloud readiness",
            "body": "review-required",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "security-orchestrator",
            "title": "Internal review: accept repaired WU-15 cloud readiness packet",
            "body": (
                f"Target repaired task: {blocker_id}. Completion must use wording: "
                "REVIEW PASS or REVIEW FAIL."
            ),
            "events": [{"type": "completed", "payload": {"summary": f"REVIEW PASS for target {blocker_id}"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_pass_reduced_blockers")
        self.assertEqual(fake.tasks[blocker_id]["status"], "done")

    def test_no_idle_does_not_reduce_internal_review_fail_that_mentions_pass_evidence(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "failpassword"
        review_id = "t_" + "failpassreview"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "evidence-reconciler",
            "title": "F15/WU-00 - Evidence package",
            "body": "review-required: independent-reviewer must review before this card is done",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "F15/WU-00R - Independent review of evidence package",
            "completed_at": 200,
            "body": json.dumps(
                {
                    "record_type": "factory_internal_review_result",
                    "result": "FAIL",
                    "reviewed_task_ref": blocker_id,
                    "blocking_findings": ["missing PASS evidence readback"],
                    "human_gate_required": False,
                    "operator_input_required": False,
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "FAIL: missing PASS evidence readback"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_fail_repair_task_created")
        self.assertEqual(fake.tasks[blocker_id]["status"], "blocked")
        self.assertNotEqual(fake.tasks[blocker_id].get("result"), "DONE")

    def test_no_idle_latest_internal_review_pass_preempts_older_fail(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "latestpass"
        old_fail_id = "t_" + "oldfail"
        new_pass_id = "t_" + "newpass"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "product-architect",
            "title": "F15/WU-01 - Planning packet",
            "body": "review-required: independent-reviewer must review before this card is done",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[old_fail_id] = {
            "id": old_fail_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Old independent review FAIL",
            "completed_at": 100,
            "body": json.dumps(
                {
                    "record_type": "factory_internal_review_result",
                    "result": "FAIL",
                    "reviewed_task_ref": blocker_id,
                    "blocking_findings": ["old missing evidence"],
                    "human_gate_required": False,
                    "operator_input_required": False,
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "FAIL"}}],
        }
        fake.tasks[new_pass_id] = {
            "id": new_pass_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "New independent review PASS",
            "completed_at": 200,
            "body": json.dumps(
                {
                    "record_type": "factory_internal_review_result",
                    "result": "PASS",
                    "reviewed_task_ref": blocker_id,
                    "blocking_findings": [],
                    "human_gate_required": False,
                    "operator_input_required": False,
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "PASS"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_pass_reduced_blockers")
        self.assertEqual(fake.tasks[blocker_id]["status"], "done")
        repairs = [
            task for task in fake.tasks.values()
            if adapter.task_body_json_object(task).get("marker") == adapter.NO_IDLE_REVIEW_FAIL_REPAIR_MARKER
        ]
        self.assertEqual(repairs, [])

    def test_no_idle_replaces_done_internal_review_request_without_result(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "reviewstale"
        old_review_id = "t_" + "oldreviewrequest"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "evidence-reconciler",
            "title": "F15/WU-00 - Evidence package",
            "body": "review-required: independent-reviewer must review before this card is done",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "review-required"}}],
        }
        fake.tasks[old_review_id] = {
            "id": old_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Old malformed internal review request",
            "body": json.dumps(
                {
                    "packet_type": "factory_internal_review_request",
                    "marker": adapter.NO_IDLE_INTERNAL_REVIEW_REQUEST_MARKER,
                    "target_task_ref": blocker_id,
                    "reviewer_role": "independent-reviewer",
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "completed without PASS/FAIL result"}}],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "internal_review_task_created")
        review_tasks = [
            task for task in fake.tasks.values()
            if adapter.task_body_json_object(task).get("marker") == adapter.NO_IDLE_INTERNAL_REVIEW_REQUEST_MARKER
            and task.get("status") == "ready"
        ]
        self.assertEqual(len(review_tasks), 1)
        self.assertNotEqual(review_tasks[0]["id"], old_review_id)

    def test_latest_ready_work_unit_materialization_plan_accepts_iso_completed_at(self) -> None:
        test_dir = ROOT / ".tmp" / "test-ready-work-unit-iso"
        test_dir.mkdir(parents=True, exist_ok=True)
        plan_path = test_dir / "READY_WORK_UNIT_HERMES_MATERIALIZATION_PLAN.json"
        plan_path.write_text(json.dumps({"record_type": "ready_work_unit_hermes_materialization_plan"}), encoding="utf-8")
        try:
            rows = {
                "done": [
                    {
                        "id": "t_" + "planiso",
                        "status": "done",
                        "completed_at": "2026-06-28T18:00:00Z",
                        "body": json.dumps(
                            {
                                "required_output": "ready_work_unit_hermes_materialization_plan",
                                "artifacts": {
                                    "plan": {
                                        "path_ref": str(plan_path.relative_to(ROOT)),
                                    }
                                }
                            }
                        ),
                    }
                ]
            }

            result = adapter.latest_ready_work_unit_materialization_plan_path(rows)
        finally:
            plan_path.unlink(missing_ok=True)

        self.assertEqual(result, plan_path)

    def test_no_idle_reports_running_closeout_without_mutation_when_not_remediating(self) -> None:
        fake = FakeHermes()
        running_id = "t_" + "runclose2"
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        worker_result = factoryctl.build_worker_result(
            "implementation-worker",
            card,
            result="PASS",
            tool_or_profile="implementation-worker",
            executed_by="implementation-worker",
            evidence_refs=["external:test:todo-implementation"],
            blocking_findings=False,
            findings_summary="Todo implementation completed with local tests.",
            next_action="ready for Receipt Five reconciliation",
        )
        fake.tasks[running_id] = {
            "id": running_id,
            "status": "running",
            "assignee": "implementation-worker",
            "title": "F15 implement Todo Web Local",
            "current_step_key": "F15-runtime-execution",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "plan_action": "execute_ready_work_unit",
                    "agent_may_choose_phase": False,
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F15-runtime-execution",
                        "runtime_field_required": True,
                    },
                }
            ),
            "runs": [
                {
                    "status": "running",
                    "started_at": "2020-01-01T00:00:00Z",
                    "metadata": json.dumps({"implementation_result": worker_result}),
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "running_worker_result_closeout_required")
        self.assertTrue(state["remediation_required"])
        self.assertEqual(fake.tasks[running_id]["status"], "running")
        self.assertFalse(any(len(call) >= 5 and call[4] == "complete" for call in fake.calls))

    def test_no_idle_treats_delivered_product_sot_package_as_human_gate(self) -> None:
        fake = FakeHermes()
        failed_review_id = "t_" + "review01"
        repair_id = "t_" + "repair01"
        pass_review_id = "t_" + "review02"
        gate_id = "t_" + "gate0001"
        fake.tasks[failed_review_id] = {
            "id": failed_review_id,
            "status": "blocked",
            "assignee": "independent-reviewer",
            "title": "F3 - Independent review of Product SOT candidate",
            "latest_summary": "review-failed: required factoryctl validators fail",
            "body": "review Product SOT package",
            "events": [{"type": "blocked", "reason": "review-failed: validators fail"}],
        }
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "done",
            "assignee": "product-sot-planner",
            "title": "Repair failed independent review package",
            "body": json.dumps(
                {
                    "marker": "factory_no_idle_review_repair",
                    "blocked_review_task_refs": [failed_review_id],
                }
            ),
            "events": [{"type": "completed", "payload": {"summary": "repair complete"}}],
        }
        fake.tasks[pass_review_id] = {
            "id": pass_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "F3 - Independent review of repaired Product SOT candidate",
            "latest_summary": (
                "Independent review PASS for the repaired Product SOT candidate package; "
                "next gate is owner/Product SOT approval or rebaseline before method-contract planning."
            ),
            "body": "review repaired Product SOT package",
            "parents": [repair_id],
            "events": [
                {
                    "type": "completed",
                    "payload": {
                        "summary": (
                            "Independent review PASS; owner/Product SOT approval or rebaseline "
                            "is still required before method-contract planning."
                        )
                    },
                }
            ],
        }
        fake.tasks[gate_id] = {
            "id": gate_id,
            "status": "blocked",
            "assignee": "human-gate-clerk",
            "title": "Prepare Product SOT owner decision package",
            "body": json.dumps(
                {
                    "marker": "factory_no_idle_post_review_gate_package",
                    "human_gate_packet": human_gate_packet_fixture(),
                }
            ),
            "latest_summary": (
                "Human decision required after delivered Product SOT package: choose approve "
                "Product SOT candidate for method-contract planning only, request exact changes, or rebaseline."
            ),
            "comments": [
                {
                    "author": "human-gate-clerk",
                    "body": (
                        "Product SOT owner decision package prepared and delivered before the decision question. "
                        "Decision package refs include Markdown, PDF, APPROVAL_REQUEST, EVIDENCE_INDEX, OWNER_REVIEW "
                        "and validation receipt. No human decision has been recorded by this worker."
                    ),
                }
            ],
            "events": [
                {
                    "kind": "blocked",
                    "payload": {
                        "reason": (
                            "Human decision required after delivered Product SOT package: choose approve "
                            "Product SOT candidate for method-contract planning only, request exact changes, or rebaseline."
                        )
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "human_gate_required")
        self.assertEqual(state["classification"], "only_human_gate_blockers_seen")
        self.assertTrue(state["human_gate_required"])
        self.assertFalse(state["remediation_required"])
        self.assertEqual(state["human_gate_task_refs"], ["kanban:<redacted>"])
        self.assertEqual(state["ignored_superseded_blocked_task_refs"], ["kanban:<redacted>"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_ignores_factory_runtime_code_review_pass_that_mentions_product_sot_gate(self) -> None:
        fake = FakeHermes()
        code_review_id = "t_" + "review03"
        fake.tasks[code_review_id] = {
            "id": code_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Independent review of factory no-idle runtime classifier patch",
            "latest_summary": (
                "Independent review PASS for adapters/hermes/live_kanban_adapter.py no-idle code. "
                "The patch mentions owner/Product SOT approval, Product SOT approval or rebaseline, "
                "and before method-contract planning because it prevents duplicate gate-package tasks."
            ),
            "body": (
                "Review factory runtime code patch for classify_no_idle_state and "
                "done_review_requires_owner_product_sot_gate; this is not a reviewed Product SOT candidate."
            ),
            "events": [
                {
                    "type": "completed",
                    "payload": {
                        "summary": (
                            "Independent review PASS: factory no-idle runtime/code patch only; "
                            "not Product SOT owner-review material."
                        )
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "empty_or_complete")
        self.assertEqual(state["classification"], "no_unfinished_work_seen")
        self.assertFalse(state["remediation_required"])
        self.assertFalse(state["human_gate_required"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_does_not_recreate_post_review_gate_after_owner_gate_closed(self) -> None:
        fake = FakeHermes()
        pass_review_id = "t_" + "review02"
        gate_id = "t_" + "gate0001"
        fake.tasks[pass_review_id] = {
            "id": pass_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "F3 - Independent review of repaired Product SOT candidate",
            "latest_summary": (
                "Independent review PASS for the repaired Product SOT candidate package; "
                "next gate is owner/Product SOT approval or rebaseline before method-contract planning."
            ),
            "body": "review repaired Product SOT package",
            "events": [
                {
                    "type": "completed",
                    "payload": {
                        "summary": (
                            "Independent review PASS; owner/Product SOT approval or rebaseline "
                            "is still required before method-contract planning."
                        )
                    },
                }
            ],
        }
        fake.tasks[gate_id] = {
            "id": gate_id,
            "status": "done",
            "assignee": "human-gate-clerk",
            "title": "Prepare Product SOT owner decision package",
            "body": json.dumps({"marker": "factory_no_idle_post_review_gate_package"}),
            "latest_summary": (
                "Owner decision recorded: approved Product SOT for method-contract planning only. "
                "Human gate closed; do not recreate a duplicate gate verification task."
            ),
            "comments": [
                {
                    "author": "human-gate-clerk",
                    "body": "Operator decision recorded and Product SOT approved for method-contract planning only.",
                }
            ],
            "events": [
                {
                    "type": "completed",
                    "payload": {
                        "summary": "Owner decision recorded: approved Product SOT; human gate closed."
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "empty_or_complete")
        self.assertEqual(state["classification"], "post_review_owner_product_sot_gate_already_closed")
        self.assertFalse(state["remediation_required"])
        self.assertFalse(state["human_gate_required"])
        self.assertEqual(state["closed_human_gate_task_refs"], ["kanban:<redacted>"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_continues_from_terminal_planning_to_architecture(self) -> None:
        fake = FakeHermes()
        gate_id = "t_" + "gate0002"
        method_id = "t_" + "method01"
        face_id = "t_" + "face0001"
        review_id = "t_" + "review03"
        fake.tasks[gate_id] = {
            "id": gate_id,
            "status": "done",
            "assignee": "human-gate-clerk",
            "title": "Prepare Product SOT owner decision package",
            "body": json.dumps({"marker": "factory_no_idle_post_review_gate_package"}),
            "latest_summary": "Owner decision recorded: approved Product SOT for method-contract planning only.",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "decision": {
                                "code": "APPROVE_PRODUCT_SOT",
                                "value": "approved",
                                "actor_role": "Factory Owner",
                            }
                        }
                    ),
                }
            ],
        }
        fake.tasks[method_id] = {
            "id": method_id,
            "status": "done",
            "assignee": "product-architect",
            "title": "F7 - Draft Method Contract planning packet",
            "latest_summary": "Method Contract planning packet completed for architecture use.",
        }
        fake.tasks[face_id] = {
            "id": face_id,
            "status": "done",
            "assignee": "product-face",
            "title": "F8 - Draft Product Experience/Product Face planning packet",
            "latest_summary": "Product Face and Product Experience planning packet completed for architecture use.",
        }
        fake.tasks[review_id] = {
            "id": review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Review Method Contract and Product Face planning packets",
            "latest_summary": "PASS_FOR_PLANNING_USE_ONLY: Method Contract and Product Face planning may proceed to architecture.",
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "create_next_artifact_task")
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertIsNotNone(result["remediation_task_id"])
        created_tasks = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_packet"
        ]
        self.assertEqual(len(created_tasks), 1)
        created = created_tasks[0]
        body = adapter.parse_json_object(str(created["body"]))
        self.assertEqual(created["assignee"], "product-architect")
        self.assertEqual(created["status"], "ready")
        self.assertEqual(body["required_output"], "architecture_packet")
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F10-security-architecture")
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])
        self.assertTrue(state["native_dispatch_required_next"])

    def test_no_idle_continues_from_terminal_architecture_to_review(self) -> None:
        fake = FakeHermes()
        arch_id = "t_" + "arch0002"
        fake.tasks[arch_id] = {
            "id": arch_id,
            "status": "done",
            "assignee": "product-architect",
            "title": "Materialize architecture_packet for board",
            "latest_summary": "Architecture candidate packet is ready for independent review.",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "architecture_result": {
                                "status": "candidate_architecture_packet_ready_for_independent_review_not_closed",
                                "task_id": arch_id,
                                "review_requirements": ["independent architecture review"],
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "create_next_artifact_task")
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        created_tasks = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_review_packet"
        ]
        self.assertEqual(len(created_tasks), 1)
        created = created_tasks[0]
        body = adapter.parse_json_object(str(created["body"]))
        self.assertEqual(created["assignee"], "independent-reviewer")
        self.assertEqual(created["status"], "ready")
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F10-security-architecture")
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])
        self.assertTrue(state["native_dispatch_required_next"])

    def test_no_idle_detects_terminal_architecture_from_hermes_list_title(self) -> None:
        fake = FakeHermes()
        arch_id = "t_" + "arch0003"
        fake.tasks[arch_id] = {
            "id": arch_id,
            "status": "done",
            "assignee": "product-architect",
            "title": "Materialize architecture_packet for board",
            "body": "{}",
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        created_tasks = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_review_packet"
        ]
        self.assertEqual(len(created_tasks), 1)
        self.assertEqual(created_tasks[0]["assignee"], "independent-reviewer")

    def test_no_idle_routes_failed_architecture_review_to_architecture_repair(self) -> None:
        fake = FakeHermes()
        review_id = "t_" + "archrev3"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / "architecture_review_packet.final.json"
            fake.tasks[review_id] = {
                "id": review_id,
                "status": "done",
                "assignee": "independent-reviewer",
                "title": "Materialize architecture_review_packet for board",
                "latest_summary": (
                    "Blocking FAIL: architecture candidate is not reviewable; "
                    "repair/rerun architecture_packet is required before decomposition."
                ),
                "workspace_path": str(Path(tmpdir)),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps({"artifacts": [str(missing_artifact)]}),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

            result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"], "architecture_packet")
        created_tasks = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_packet"
        ]
        self.assertEqual(len(created_tasks), 1)
        self.assertEqual(created_tasks[0]["assignee"], "product-architect")
        body = adapter.parse_json_object(str(created_tasks[0].get("body") or "{}"))
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])
        self.assertIn("blocking FAIL", body["reason"])

    def test_no_idle_supersedes_old_failed_architecture_review_after_pass_rerun(self) -> None:
        fake = FakeHermes()
        arch_id = "t_" + "archfix1"
        failed_review_id = "t_" + "archfail"
        passed_review_id = "t_" + "archpass"
        fake.tasks[arch_id] = {
            "id": arch_id,
            "status": "done",
            "assignee": "product-architect",
            "title": "Materialize architecture_packet for board",
            "latest_summary": "Repaired architecture candidate packet is ready for independent review.",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "architecture_result": {
                                "status": "candidate_architecture_packet_ready_for_independent_review_not_closed",
                                "task_id": arch_id,
                            }
                        }
                    ),
                }
            ],
        }
        fake.tasks[failed_review_id] = {
            "id": failed_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Materialize architecture_review_packet for board",
            "completed_at": "2026-06-27T01:00:00+00:00",
            "latest_summary": (
                "Blocking FAIL: original architecture candidate is not reviewable; "
                "repair/rerun architecture_packet is required before decomposition."
            ),
        }
        fake.tasks[passed_review_id] = {
            "id": passed_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Independent architecture review rerun",
            "completed_at": "2026-06-27T01:05:00+00:00",
            "latest_summary": (
                "PASS_FOR_ARCHITECTURE_REVIEW_RERUN: repaired architecture candidate "
                "is reviewable for Product Creation Plan planning."
            ),
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "architecture_review_result": {
                                "status": "PASS_FOR_ARCHITECTURE_REVIEW_RERUN",
                                "target_task_id": arch_id,
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(
            result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"],
            "product_creation_plan",
        )
        created_architecture_repairs = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_packet"
        ]
        self.assertEqual(created_architecture_repairs, [])
        created_product_plans = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "product_creation_plan"
        ]
        self.assertEqual(len(created_product_plans), 1)
        body = adapter.parse_json_object(str(created_product_plans[0].get("body") or "{}"))
        self.assertEqual(created_product_plans[0]["assignee"], "decomposition-planner")
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F11-product-creation-plan")
        self.assertEqual(body["phase_engine"]["computed_phase_id"], "F11")
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])
        self.assertIn("Product Creation Plan", body["reason"])

    def test_no_idle_does_not_repair_architecture_artifact_after_newer_independent_pass(self) -> None:
        fake = FakeHermes()
        arch_id = "t_" + "archpasssrc"
        passed_review_id = "t_" + "archinputpass"
        with tempfile.TemporaryDirectory() as tmpdir:
            missing_artifact = Path(tmpdir) / f"ARCHITECTURE_PACKET_Todo_Web_Local.{arch_id}.md"
            fake.tasks[arch_id] = {
                "id": arch_id,
                "status": "done",
                "assignee": "product-architect",
                "title": "Materialize architecture_packet for board",
                "created_at": "2026-06-27T10:00:00+00:00",
                "latest_summary": "Architecture candidate packet is ready for independent review.",
                "workspace_path": str(Path(tmpdir)),
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "architecture_result": {
                                    "status": "candidate_architecture_packet_ready_for_independent_review_not_closed",
                                    "task_id": arch_id,
                                    "artifact_paths": [str(missing_artifact)],
                                },
                                "artifacts": [str(missing_artifact)],
                            }
                        ),
                    }
                ],
            }
            fake.tasks[passed_review_id] = {
                "id": passed_review_id,
                "status": "done",
                "assignee": "independent-reviewer",
                "title": "Independent review — repaired architecture_packet for Todo Web Local",
                "completed_at": "2026-06-27T10:05:00+00:00",
                "latest_summary": "PASS_FOR_REVIEW_INPUT_READINESS_ONLY_NOT_ARCHITECTURE_CLOSURE.",
                "runs": [
                    {
                        "status": "done",
                        "outcome": "completed",
                        "metadata": json.dumps(
                            {
                                "independent_review_result": {
                                    "verdict": "PASS_FOR_REVIEW_INPUT_READINESS_ONLY_NOT_ARCHITECTURE_CLOSURE",
                                    "reviewed_task_id": arch_id,
                                    "reviewed_artifact_type": "architecture_packet",
                                    "blocking_findings": [],
                                }
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                ["no-idle", "--board", TEST_BOARD, "--create-remediation", "--workspace", "scratch"]
            )

            result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(
            result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"],
            "product_creation_plan",
        )
        created_repairs = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("plan_action")
            == "repair_declared_artifacts"
        ]
        self.assertEqual(created_repairs, [])
        created_product_plans = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "product_creation_plan"
        ]
        self.assertEqual(len(created_product_plans), 1)

    def test_no_idle_routes_product_creation_plan_to_decomposition_coverage_review(self) -> None:
        fake = FakeHermes()
        product_plan_id = "t_" + "prodplan1"
        fake.tasks[product_plan_id] = {
            "id": product_plan_id,
            "status": "done",
            "assignee": "decomposition-planner",
            "title": "Materialize product_creation_plan for board",
            "latest_summary": "Product Creation Plan created; decomposition coverage review is required next.",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "product_creation_plan": {
                                "record_type": "product_creation_plan",
                                "plan_id": "todo-web-local-product-creation-plan",
                                "handoff": {
                                    "factory_owned_next_step": True,
                                    "next_artifact": "decomposition_coverage_review",
                                    "next_worker": "independent-reviewer",
                                },
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(
            result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"],
            "decomposition_coverage_review",
        )
        created_review_tasks = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "decomposition_coverage_review"
        ]
        self.assertEqual(len(created_review_tasks), 1)
        created = created_review_tasks[0]
        self.assertEqual(created["assignee"], "independent-reviewer")
        body = adapter.parse_json_object(str(created.get("body") or "{}"))
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F12-decomposition-coverage-review")
        self.assertEqual(body["phase_engine"]["computed_phase_id"], "F12")
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])

    def test_no_idle_routes_implementation_readiness_to_ready_gate_report(self) -> None:
        fake = FakeHermes()
        readiness_id = "t_" + "ready001"
        fake.tasks[readiness_id] = {
            "id": readiness_id,
            "status": "done",
            "assignee": "factory-orchestrator",
            "title": "Materialize product_implementation_readiness for board",
            "latest_summary": "Product Implementation Readiness exists; Ready Gate is required next.",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "product_implementation_readiness": {
                                "record_type": "product_implementation_readiness",
                                "readiness_id": "todo-web-local-readiness",
                                "handoff": {
                                    "factory_owned_next_step": True,
                                    "next_artifact": "gate_report",
                                    "next_worker": "factory-orchestrator",
                                },
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(
            result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"],
            "gate_report",
        )
        created_gate_reports = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "gate_report"
        ]
        self.assertEqual(len(created_gate_reports), 1)
        created = created_gate_reports[0]
        self.assertEqual(created["assignee"], "factory-orchestrator")
        body = adapter.parse_json_object(str(created.get("body") or "{}"))
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F13-ready-gate")
        self.assertEqual(body["phase_engine"]["computed_phase_id"], "F13")
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])

    def test_no_idle_routes_passed_ready_gate_to_worker_packet(self) -> None:
        fake = FakeHermes()
        gate_id = "t_" + "gate001"
        fake.tasks[gate_id] = {
            "id": gate_id,
            "status": "done",
            "assignee": "factory-orchestrator",
            "title": "Materialize gate_report for board",
            "latest_summary": (
                "gate_status=ready_for_worker_execution; "
                "verdict=PASS_FOR_NATIVE_DISPATCH_ONLY_NOT_IMPLEMENTATION_AUTHORIZATION"
            ),
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "gate_report": {
                                "record_type": "gate_report",
                                "gate_status": "ready_for_worker_execution",
                                "gate_predicate_result": "PASS_FOR_NATIVE_DISPATCH_ONLY_NOT_IMPLEMENTATION_AUTHORIZATION",
                                "blocked_workers": [],
                            }
                        }
                    ),
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(
            result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"],
            "worker_packet",
        )
        created_worker_packets = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "worker_packet"
        ]
        self.assertEqual(len(created_worker_packets), 1)
        created = created_worker_packets[0]
        self.assertEqual(created["assignee"], "factory-orchestrator")
        body = adapter.parse_json_object(str(created.get("body") or "{}"))
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F15-runtime-execution")
        self.assertEqual(body["phase_engine"]["computed_phase_id"], "F15")
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])

    def test_no_idle_routes_worker_packet_to_ready_work_unit_hermes_plan(self) -> None:
        fake = FakeHermes()
        worker_packet_id = "t_" + "workerpkt"
        fake.tasks[worker_packet_id] = {
            "id": worker_packet_id,
            "status": "done",
            "assignee": "factory-orchestrator",
            "title": "Materialize worker_packet for board",
            "body": json.dumps(
                {
                    "packet_type": "factory_deterministic_reconcile_task",
                    "required_output": "worker_packet",
                    "kanban_workflow_binding": {
                        "workflow_template_id": "overkill-vfinal",
                        "current_step_key": "F15-runtime-execution",
                        "runtime_field_required": True,
                    },
                    "phase_engine": {
                        "computed_phase_id": "F15",
                        "computed_frontier": "execution",
                        "next_required_artifact": "worker_packet",
                        "human_gate_allowed": False,
                    },
                }
            ),
            "latest_summary": (
                "Validated worker_packet manifest exists; next step is Hermes ready work-unit materialization."
            ),
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(
            result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"],
            "ready_work_unit_hermes_materialization_plan",
        )
        created_plans = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "ready_work_unit_hermes_materialization_plan"
        ]
        self.assertEqual(len(created_plans), 1)
        created = created_plans[0]
        self.assertEqual(created["assignee"], "factory-orchestrator")
        body = adapter.parse_json_object(str(created.get("body") or "{}"))
        self.assertEqual(body["kanban_workflow_binding"]["current_step_key"], "F15-runtime-execution")
        self.assertEqual(body["phase_engine"]["computed_phase_id"], "F15")
        self.assertFalse(body["phase_engine"]["human_gate_allowed"])
        self.assertIn("blocked-first Kanban execution cards", body["phase_engine"]["decision_basis"])

    def test_no_idle_materializes_ready_work_unit_plan_to_native_cards(self) -> None:
        fake = FakeHermes()
        tmp_root = ROOT / ".tmp" / "tests"
        tmp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as tmp:
            tmp_path = Path(tmp)
            plan = two_step_ready_work_unit_plan()
            plan["board"] = TEST_BOARD
            plan_path = tmp_path / "READY_WORK_UNIT_HERMES_MATERIALIZATION_PLAN_test.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            relative_plan = plan_path.relative_to(ROOT)
            plan_task_id = "t_" + "plan001"
            fake.tasks[plan_task_id] = {
                "id": plan_task_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Materialize ready_work_unit_hermes_materialization_plan for board",
                "body": json.dumps(
                    {
                        "packet_type": "factory_deterministic_reconcile_task",
                        "required_output": "ready_work_unit_hermes_materialization_plan",
                        "kanban_workflow_binding": {
                            "workflow_template_id": "overkill-vfinal",
                            "current_step_key": "F15-runtime-execution",
                            "runtime_field_required": True,
                        },
                    }
                ),
                "runs": [
                    {
                        "status": "done",
                        "metadata": json.dumps(
                            {
                                "artifacts": {
                                    "plan": {
                                        "path_ref": str(relative_plan),
                                    }
                                },
                                "orchestration_result": {
                                    "evidence_refs": [str(relative_plan)],
                                },
                            }
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

            result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["no_idle_state"]["classification"], "ready_work_unit_runtime_materialized")
        self.assertTrue(result["no_idle_state"]["native_dispatch_required_next"])
        self.assertEqual(result["ready_work_unit_runtime_materialization"]["materialization"]["mode"], "materialize-ready-work-units")
        self.assertEqual(result["ready_work_unit_runtime_materialization"]["release"]["mode"], "release-ready-work-units")
        created_work_unit_ids = ready_work_unit_task_ids(fake)
        self.assertEqual(len(created_work_unit_ids), 2)
        statuses = {task_id: fake.tasks[task_id]["status"] for task_id in created_work_unit_ids}
        self.assertIn("ready", statuses.values())
        self.assertIn("blocked", statuses.values())
        ready_task = next(task for task_id, task in fake.tasks.items() if task_id in created_work_unit_ids and task["status"] == "ready")
        self.assertEqual(ready_task["assignee"], "implementation-worker")

    def test_no_idle_prioritizes_ready_work_unit_reconciliation_over_generic_artifact_repair(self) -> None:
        fake = FakeHermes()
        tmp_root = ROOT / ".tmp" / "tests"
        tmp_root.mkdir(parents=True, exist_ok=True)
        run_root = ROOT / ".tmp" / "factory-runs"
        run_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=tmp_root) as tmp:
            tmp_path = Path(tmp)
            plan = two_step_ready_work_unit_plan()
            plan["board"] = TEST_BOARD
            plan_path = tmp_path / "READY_WORK_UNIT_HERMES_MATERIALIZATION_PLAN_test.json"
            plan_path.write_text(json.dumps(plan), encoding="utf-8")
            digest = hashlib.sha256(str(plan_path).encode("utf-8")).hexdigest()[:12]
            route_readiness_path = run_root / f"ready-work-unit-route-readiness-{TEST_BOARD}-{digest}.json"
            materialization_result_path = run_root / f"ready-work-unit-materialization-{TEST_BOARD}-{digest}.json"
            write_route_readiness(route_readiness_path, extra_workers=["implementation-worker", "independent-reviewer"])

            materialize_args = adapter.build_parser().parse_args(
                [
                    "materialize-ready-work-units",
                    "--board",
                    TEST_BOARD,
                    "--plan",
                    str(plan_path),
                    "--route-readiness",
                    str(route_readiness_path),
                    "--workspace",
                    "dir:/tmp/overkill-factory-test",
                ]
            )
            materialization_result = adapter.materialize_ready_work_units(materialize_args, runner=fake)
            materialization_result_path.write_text(json.dumps(materialization_result), encoding="utf-8")
            release_args = adapter.build_parser().parse_args(
                [
                    "release-ready-work-units",
                    "--board",
                    TEST_BOARD,
                    "--plan",
                    str(plan_path),
                    "--materialization-result",
                    str(materialization_result_path),
                    "--route-readiness",
                    str(route_readiness_path),
                ]
            )
            release = adapter.release_ready_work_units(release_args, runner=fake)
            self.assertIn("work-unit-001", release["released_ready_work_unit_task_ids"])
            released_id = next(
                task_id
                for task_id in ready_work_unit_task_ids(fake)
                if adapter.parse_json_object(str(fake.tasks[task_id].get("body") or "{}")).get("work_unit_id")
                == "work-unit-001"
            )
            block_ready_work_unit_after_release(fake, released_id)
            fake.tasks[released_id].setdefault("comments", []).append(
                {
                    "author": "implementation-worker",
                    "body": "review-required: implementation evidence prepared for deterministic post-repair review",
                }
            )
            relative_plan = plan_path.relative_to(ROOT)
            plan_task_id = "t" + "_plan001"
            fake.tasks[plan_task_id] = {
                "id": plan_task_id,
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Materialize ready_work_unit_hermes_materialization_plan for board",
                "body": json.dumps(
                    {
                        "packet_type": "factory_deterministic_reconcile_task",
                        "required_output": "ready_work_unit_hermes_materialization_plan",
                    }
                ),
                "runs": [
                    {
                        "status": "done",
                        "metadata": json.dumps(
                            {
                                "artifacts": {"plan": {"path_ref": str(relative_plan)}},
                                "orchestration_result": {"evidence_refs": [str(relative_plan)]},
                            }
                        ),
                    }
                ],
            }
            fake.tasks["t_workerpkt"] = {
                "id": "t_workerpkt",
                "status": "done",
                "assignee": "factory-orchestrator",
                "title": "Materialize worker_packet for board",
                "body": json.dumps({"packet_type": "factory_deterministic_reconcile_task", "required_output": "worker_packet"}),
                "latest_summary": "Validated worker_packet manifest exists; next step is Hermes ready work-unit materialization.",
            }
            args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

            result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["no_idle_state"]["classification"], "ready_work_unit_reconciliation")
        self.assertIsNone(result["board_reconcile_plan"])
        self.assertEqual(result["targeted_remediation_plan"]["plan_action"], "reconcile_ready_work_units")
        self.assertEqual(
            [
                task
                for task in fake.tasks.values()
                if adapter.parse_json_object(str(task.get("body") or "{}")).get("plan_action")
                == "create_next_artifact_task"
            ],
            [],
        )
        review_tasks = [
            task
            for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("packet_type")
            == "ready_work_unit_post_repair_review_request"
        ]
        self.assertEqual(len(review_tasks), 1)

    def test_no_idle_keeps_newer_failed_architecture_review_active_after_older_pass(self) -> None:
        fake = FakeHermes()
        arch_id = "t_" + "archfix2"
        passed_review_id = "t_" + "archpass"
        failed_review_id = "t_" + "archfail"
        fake.tasks[arch_id] = {
            "id": arch_id,
            "status": "done",
            "assignee": "product-architect",
            "title": "Materialize architecture_packet for board",
            "latest_summary": "Architecture candidate packet is ready for independent review.",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "architecture_result": {
                                "status": "candidate_architecture_packet_ready_for_independent_review_not_closed",
                                "task_id": arch_id,
                            }
                        }
                    ),
                }
            ],
        }
        fake.tasks[passed_review_id] = {
            "id": passed_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Independent architecture review",
            "completed_at": "2026-06-27T01:00:00+00:00",
            "latest_summary": "PASS_FOR_ARCHITECTURE_REVIEW: architecture candidate was reviewable.",
        }
        fake.tasks[failed_review_id] = {
            "id": failed_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Independent architecture review rerun",
            "completed_at": "2026-06-27T01:10:00+00:00",
            "latest_summary": (
                "Blocking FAIL: later architecture review found the packet is not reviewable; "
                "repair/rerun architecture_packet is required."
            ),
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        self.assertEqual(
            result["board_reconcile_plan"]["create_task_contract"]["body"]["required_output"],
            "architecture_packet",
        )
        created_architecture_repairs = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_packet"
        ]
        self.assertEqual(len(created_architecture_repairs), 1)
        self.assertEqual(created_architecture_repairs[0]["assignee"], "product-architect")

    def test_no_idle_does_not_mistake_planning_review_for_architecture_review(self) -> None:
        fake = FakeHermes()
        gate_id = "t_" + "gate0003"
        planning_review_id = "t_" + "review04"
        arch_id = "t_" + "arch0004"
        fake.tasks[gate_id] = {
            "id": gate_id,
            "status": "done",
            "assignee": "human-gate-clerk",
            "title": "Prepare Product SOT owner decision package",
            "body": json.dumps({"marker": "factory_no_idle_post_review_gate_package"}),
            "latest_summary": "Owner decision recorded: approved Product SOT for method-contract planning only.",
            "runs": [
                {
                    "status": "done",
                    "outcome": "completed",
                    "metadata": json.dumps(
                        {
                            "decision": {
                                "code": "APPROVE_PRODUCT_SOT",
                                "value": "approved",
                                "actor_role": "Factory Owner",
                            }
                        }
                    ),
                }
            ],
        }
        fake.tasks[planning_review_id] = {
            "id": planning_review_id,
            "status": "done",
            "assignee": "independent-reviewer",
            "title": "Review Method Contract and Product Face planning packets",
            "latest_summary": (
                "PASS_FOR_PLANNING_USE_ONLY: Method Contract and Product Face planning "
                "may proceed to architecture."
            ),
        }
        fake.tasks[arch_id] = {
            "id": arch_id,
            "status": "done",
            "assignee": "product-architect",
            "title": "Materialize architecture_packet for board",
            "body": "{}",
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "create_next_artifact_task")
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "create_next_artifact_task")
        created_tasks = [
            task for task in fake.tasks.values()
            if adapter.parse_json_object(str(task.get("body") or "{}")).get("required_output")
            == "architecture_review_packet"
        ]
        self.assertEqual(len(created_tasks), 1)
        self.assertEqual(created_tasks[0]["assignee"], "independent-reviewer")

    def test_no_idle_does_not_treat_text_only_human_gate_as_decision_ready(self) -> None:
        fake = FakeHermes()
        gate_id = "t_" + "gate0001"
        fake.tasks[gate_id] = {
            "id": gate_id,
            "status": "blocked",
            "assignee": "human-gate-clerk",
            "title": "Human gate awaiting owner approval",
            "body": json.dumps({"marker": "human_gate", "reason": "awaiting human decision"}),
            "latest_summary": (
                "Decision package prepared and delivered. Awaiting human approval."
            ),
            "comments": [
                {
                    "author": "human-gate-clerk",
                    "body": "PDF delivered, approval request delivered, ready for operator decision.",
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "deterministic_factory_package_dependency_repair_task_created")
        self.assertFalse(state["human_gate_required"])
        self.assertTrue(state["remediation_required"])
        self.assertTrue(state["native_dispatch_required_next"])
        self.assertEqual(result["board_reconcile_plan"]["plan_action"], "repair_board_contract")
        self.assertIsNotNone(result["remediation_task_id"])

    def test_no_idle_reports_dependency_gated_todo_behind_human_gate_without_remediation(self) -> None:
        fake = FakeHermes()
        gate_id = "t_" + "gate0001"
        mid_id = "t_" + "todo0001"
        child_id = "t_" + "todo0002"
        fake.tasks[gate_id] = {
            "id": gate_id,
            "status": "blocked",
            "assignee": "human-gate-clerk",
            "title": "Human architecture gate",
            "body": json.dumps(
                {
                    "marker": "human_gate",
                    "reason": "awaiting human decision",
                    "human_gate_packet": human_gate_packet_fixture(),
                }
            ),
            "events": [{"kind": "blocked", "payload": {"reason": "human gate"}}],
        }
        fake.tasks[mid_id] = {
            "id": mid_id,
            "status": "todo",
            "assignee": "handoff-packer",
            "title": "Prepare gate packet after human gate",
            "body": "{}",
            "parents": [gate_id],
            "events": [],
        }
        fake.tasks[child_id] = {
            "id": child_id,
            "status": "todo",
            "assignee": "independent-reviewer",
            "title": "Review packet after preparation",
            "body": "{}",
            "parents": [mid_id],
            "events": [],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "human_gate_required")
        self.assertEqual(state["classification"], "todo_dependency_gated_by_human_gate_blocker")
        self.assertTrue(state["human_gate_required"])
        self.assertFalse(state["remediation_required"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_repairs_repair_task_gated_by_the_gate_it_repairs(self) -> None:
        gate_id = "t_" + "gate0001"
        repair_id = "t_" + "repair01"

        state = adapter.classify_no_idle_state(
            {
                "ready": [],
                "running": [],
                "todo": [
                    {
                        "id": repair_id,
                        "status": "todo",
                        "assignee": "factory-orchestrator",
                        "title": "Repair owner-readable human gate package",
                        "body": (
                            "factory-owned repair: rebuild the package; no renewed decision "
                            "request until readable artifact is ready"
                        ),
                        "parents": [gate_id],
                    }
                ],
                "blocked": [
                    {
                        "id": gate_id,
                        "status": "blocked",
                        "assignee": "human-gate-clerk",
                        "title": "Human architecture gate",
                        "body": (
                            "human gate packet is not approval-ready: missing operator briefing package, "
                            "APPROVAL_REQUEST, EVIDENCE_INDEX, OWNER_REVIEW and pdf"
                        ),
                    }
                ],
            }
        )

        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "factory_repair_task_dependency_gated_by_blocker_it_repairs")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertEqual(state["repair_task_refs"], [repair_id])
        self.assertEqual(state["factory_owned_package_task_refs"], [gate_id])
        self.assertIn("re-created or unlinked", state["remediation_reason"])

    def test_no_idle_repairs_factory_repair_task_gated_by_needs_input_parent_it_repairs(self) -> None:
        blocker_id = "t_" + "block001"
        repair_id = "t_" + "repair01"

        state = adapter.classify_no_idle_state(
            {
                "ready": [],
                "running": [],
                "todo": [
                    {
                        "id": repair_id,
                        "status": "todo",
                        "assignee": "security-orchestrator",
                        "title": "F15/WU-01S - Security triage for 20apy sanitized inventory",
                        "body": json.dumps(
                            {
                                "marker": "factory_no_idle_remediation",
                                "plan_action": "repair_internal_needs_input_blocker",
                                "repairs_task_ref": blocker_id,
                                "objective": "Internal remediation for WU-01, not a human gate.",
                            }
                        ),
                        "parents": [blocker_id],
                    }
                ],
                "blocked": [
                    {
                        "id": blocker_id,
                        "status": "blocked",
                        "assignee": "product-architect",
                        "title": "F15/WU-01 - 20apy predecessor study",
                        "body": "Worker produced a needs_input block after tool safety denied repo preflight; internal remediation exists.",
                        "events": [
                            {
                                "kind": "blocked",
                                "payload": {
                                    "kind": "needs_input",
                                    "reason": "authorize sanitized inventory/secret-safe scan path or provide sanitized export",
                                },
                            }
                        ],
                    }
                ],
            }
        )

        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "factory_repair_task_dependency_gated_by_blocker_it_repairs")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["operator_input_required"])
        self.assertEqual(state["repair_task_refs"], [repair_id])
        self.assertEqual(state["operator_input_task_refs"], [])
        self.assertEqual(state["dependency_blocker_task_refs"], [blocker_id])
        self.assertIn("re-created or unlinked", state["remediation_reason"])

    def test_no_idle_unlinks_and_promotes_repair_task_gated_by_parent_it_repairs(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "block001"
        repair_id = "t_" + "repair01"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "product-architect",
            "title": "F15/WU-01 - 20apy predecessor study",
            "body": "needs_input after denied preflight; internal factory_no_idle_remediation exists",
            "events": [{"type": "blocked", "payload": {"kind": "needs_input", "reason": "needs sanitized export"}}],
            "children": [repair_id],
        }
        fake.tasks[repair_id] = {
            "id": repair_id,
            "status": "todo",
            "assignee": "security-orchestrator",
            "title": "F15/WU-01X - Build sanitized 20apy content export",
            "body": json.dumps({"marker": "factory_no_idle_remediation", "repairs_task_ref": blocker_id}),
            "parents": [blocker_id],
            "events": [],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["classification"], "factory_repair_task_unlinked_and_promoted")
        self.assertEqual(fake.tasks[repair_id]["status"], "ready")
        self.assertEqual(fake.tasks[repair_id]["parents"], [])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))

    def test_no_idle_reports_dependency_gated_todo_without_generic_remediation(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "block001"
        todo_id = "t_" + "todo0001"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "supply-chain-gate",
            "title": "Supply-chain target path blocker",
            "body": "blocked by unresolved upstream worker result",
            "events": [{"kind": "blocked", "payload": {"reason": "upstream worker result is still blocked"}}],
        }
        fake.tasks[todo_id] = {
            "id": todo_id,
            "status": "todo",
            "assignee": "handoff-packer",
            "title": "Packet that depends on blocked supply-chain evidence",
            "body": "{}",
            "parents": [blocker_id],
            "events": [],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "dependency_gated")
        self.assertEqual(state["classification"], "todo_dependency_gated_by_blocked_ancestors")
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["remediation_required"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_reports_input_required_without_generic_remediation(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "block001"
        todo_id = "t_" + "todo0001"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "supply-chain-gate",
            "title": "Supply-chain target path blocker",
            "body": "missing target_repo_paths and bounded scan scope",
            "events": [{"kind": "blocked", "payload": {"reason": "missing exact target inputs"}}],
        }
        fake.tasks[todo_id] = {
            "id": todo_id,
            "status": "todo",
            "assignee": "handoff-packer",
            "title": "Packet that depends on blocked supply-chain evidence",
            "body": "{}",
            "parents": [blocker_id],
            "events": [],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "input_required")
        self.assertEqual(state["classification"], "todo_dependency_gated_by_missing_operator_inputs")
        self.assertFalse(state["human_gate_required"])
        self.assertTrue(state["operator_input_required"])
        self.assertFalse(state["remediation_required"])
        self.assertEqual(state["operator_input_task_refs"], ["kanban:<redacted>"])
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_reports_operator_understanding_confirmation_as_input_not_remediation(self) -> None:
        fake = FakeHermes()
        blocker_id = "t_" + "under01"
        fake.tasks[blocker_id] = {
            "id": blocker_id,
            "status": "blocked",
            "assignee": "factory-orchestrator",
            "title": "Product Alpha source resolution",
            "latest_summary": (
                "review-required: source-resolution artifacts are materialized, but owner-readable "
                "operator_understanding_confirmation is pending. Confirm/correct it before Product SOT."
            ),
            "body": json.dumps(
                {
                    "record_type": "operator_understanding_confirmation",
                    "confirmation_state": {"status": "pending_operator_confirmation"},
                    "operator_response_ref": "pending:kanban-human-unblock-or-comment",
                    "blocking_rules": {
                        "product_sot_blocked_until_operator_understanding_confirmed": True,
                    },
                }
            ),
            "events": [
                {
                    "kind": "blocked",
                    "payload": {
                        "reason": "understanding confirmation is pending before Product SOT",
                    },
                }
            ],
        }
        args = adapter.build_parser().parse_args(["no-idle", "--board", TEST_BOARD, "--create-remediation"])

        result = adapter.no_idle(args, runner=fake)

        state = result["no_idle_state"]
        self.assertEqual(state["status"], "input_required")
        self.assertEqual(state["classification"], "only_operator_input_blockers_seen")
        self.assertTrue(state["operator_input_required"])
        self.assertFalse(state["human_gate_required"])
        self.assertFalse(state["remediation_required"])
        self.assertEqual(state["operator_input_request"]["request_type"], "operator_understanding_confirmation")
        self.assertIsNone(result["remediation_task_id"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))
        self.assertFalse(any(len(call) >= 5 and call[4] == "dispatch" for call in fake.calls))

    def test_no_idle_reports_parallel_human_gate_and_input_blockers(self) -> None:
        gate_id = "t_" + "gate0001"
        blocker_id = "t_" + "block001"
        todo_id = "t_" + "todo0001"
        state = adapter.classify_no_idle_state(
            {
                "ready": [],
                "running": [],
                "todo": [
                    {
                        "id": todo_id,
                        "status": "todo",
                        "parents": [blocker_id],
                    }
                ],
                "blocked": [
                    {
                        "id": gate_id,
                        "status": "blocked",
                        "assignee": "human-gate-clerk",
                        "body": json.dumps(
                            {
                                "marker": "human_gate",
                                "reason": "awaiting human decision",
                                "human_gate_packet": human_gate_packet_fixture(),
                            }
                        ),
                    },
                    {
                        "id": blocker_id,
                        "status": "blocked",
                        "assignee": "supply-chain-gate",
                        "body": "missing target_repo_paths and bounded scan scope",
                    },
                ],
            }
        )

        self.assertEqual(state["status"], "input_required")
        self.assertEqual(state["classification"], "todo_dependency_gated_by_inputs_before_human_gate")
        self.assertFalse(state["human_gate_required"])
        self.assertTrue(state["operator_input_required"])
        self.assertEqual(state["human_gate_task_refs"], [gate_id])
        self.assertEqual(state["operator_input_task_refs"], [blocker_id])
        self.assertFalse(state["remediation_required"])

    def test_no_idle_dependency_graph_accepts_parent_id_shape(self) -> None:
        blocker_id = "t_" + "block001"
        todo_id = "t_" + "todo0001"
        state = adapter.classify_no_idle_state(
            {
                "ready": [],
                "running": [],
                "todo": [
                    {
                        "id": todo_id,
                        "status": "todo",
                        "parents": [{"parent_id": blocker_id}],
                    }
                ],
                "blocked": [
                    {
                        "id": blocker_id,
                        "status": "blocked",
                        "assignee": "supply-chain-gate",
                        "body": "blocked by unresolved upstream worker result",
                    }
                ],
            }
        )

        self.assertEqual(state["status"], "dependency_gated")
        self.assertEqual(state["dependency_blocker_task_refs"], [blocker_id])

    def test_no_idle_does_not_hide_unidentified_todo_as_dependency_gated(self) -> None:
        blocker_id = "t_" + "block001"
        state = adapter.classify_no_idle_state(
            {
                "ready": [],
                "running": [],
                "todo": [
                    {
                        "status": "todo",
                        "parents": [blocker_id],
                    }
                ],
                "blocked": [
                    {
                        "id": blocker_id,
                        "status": "blocked",
                        "assignee": "supply-chain-gate",
                        "body": "missing exact target inputs",
                    }
                ],
            }
        )

        self.assertEqual(state["status"], "remediation_required")
        self.assertTrue(state["remediation_required"])

    def test_enforce_done_projects_completion_artifact_before_main_complete(self) -> None:
        fake = FakeHermes()
        fake.tasks[MAIN_TASK_ID] = {"id": MAIN_TASK_ID, "status": "ready", "events": [], "comments": []}
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            card = tmp_path / "CARD-001.md"
            receipt = tmp_path / "receipt.json"
            ledger = tmp_path / "ledger.json"
            worker_results = tmp_path / "worker-results"
            route_readiness = tmp_path / "route-readiness.json"
            attachment_root = tmp_path / "attachments"
            artifact = tmp_path / "proof.json"
            worker_results.mkdir()
            card.write_text("{}", encoding="utf-8")
            artifact.write_text(json.dumps({"ok": True}), encoding="utf-8")
            receipt.write_text(
                json.dumps({"evidence_refs": [".tmp/factory-runs/proof.json"]}),
                encoding="utf-8",
            )
            ledger.write_text(
                json.dumps(
                    {
                        "runtime_authority": "hermes_kanban",
                        "local_state_authority": False,
                        "tasks": {},
                        "live_bindings": {
                            "CARD-001": {
                                "binding_role": "hermes_ref_projection",
                                "runtime_authority": "hermes_kanban",
                                "local_state_authority": False,
                                "board": TEST_BOARD,
                                "main_task_id": MAIN_TASK_ID,
                                "worker_task_ids": {},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            write_route_readiness(route_readiness)
            args = adapter.build_parser().parse_args(
                [
                    "enforce-done",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--main-task-id",
                    MAIN_TASK_ID,
                    "--receipt",
                    str(receipt),
                    "--worker-results-dir",
                    str(worker_results),
                    "--ledger",
                    str(ledger),
                    "--route-readiness",
                    str(route_readiness),
                    "--complete-main",
                    "--artifact-path",
                    str(artifact),
                    "--attachment-root",
                    str(attachment_root),
                ]
            )
            original_build_hook_result = adapter.build_hook_result
            adapter.build_hook_result = lambda **_: {
                "transition_action": "allow_done",
                "plan": {"event": {"card_id": "CARD-001"}},
            }
            try:
                adapter.enforce_done(args, runner=fake)
            finally:
                adapter.build_hook_result = original_build_hook_result

            expected_copy = attachment_root / TEST_BOARD / MAIN_TASK_ID / "artifacts" / "proof.json"
            copy_exists = expected_copy.is_file()
            metadata = json.loads(str(fake.tasks[MAIN_TASK_ID]["metadata"]))

        self.assertTrue(copy_exists)
        self.assertEqual(metadata["evidence_refs"], [f"kanban-attachment:{MAIN_TASK_ID}/artifacts/proof.json"])
        projection = metadata["_overkill_completion_artifact_projection"]
        self.assertEqual(projection["status"], "PASS")
        self.assertEqual(
            projection["refs"][0]["sha256"],
            "sha256:" + hashlib.sha256(json.dumps({"ok": True}).encode("utf-8")).hexdigest(),
        )
        complete_index = next(index for index, call in enumerate(fake.calls) if len(call) >= 5 and call[4] == "complete")
        comment_index = next(index for index, call in enumerate(fake.calls) if len(call) >= 5 and call[4] == "comment")
        self.assertLess(comment_index, complete_index)

    def test_completion_blocks_kanban_attachment_ref_without_readback(self) -> None:
        with self.assertRaisesRegex(RuntimeError, "completion artifact readback blocked"):
            adapter.apply_completion_artifact_policy(
                receipt={"evidence_refs": ["kanban-attachment:t_fixture/artifacts/proof.json"]},
                artifact_paths=[],
                attachment_root=None,
                board=TEST_BOARD,
                task_id=MAIN_TASK_ID,
            )

    def test_materialize_creates_workers_as_parents_of_main_card(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        with tempfile.TemporaryDirectory() as tmp:
            readiness = Path(tmp) / "route-readiness.json"
            write_route_readiness(readiness)
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--route-readiness",
                    str(readiness),
                    "--ensure-board",
                    "--worker-ready",
                ]
            )
            result = adapter.materialize(args, runner=fake)
            ledger_data = json.loads((Path(tmp) / "ledger.json").read_text(encoding="utf-8"))

        self.assertEqual(result["main_task_id"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertIn("codex-security", result["worker_task_ids"])
        self.assertEqual(result["worker_task_ids"]["codex-security"], adapter.PUBLIC_SAFE_KANBAN_REF)
        binding = ledger_data["live_bindings"]["KFP-V35-POS-ONCHAIN-AUDITOR"]
        self.assertEqual(binding["binding_role"], "hermes_ref_projection")
        self.assertEqual(binding["runtime_authority"], "hermes_kanban")
        self.assertFalse(binding["local_state_authority"])
        self.assertEqual(binding["idempotency_contract"], result["idempotency_contract"])
        self.assertEqual(result["idempotency_contract"]["digest_algorithm"], "sha256")
        self.assertEqual(result["idempotency_contract"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(result["idempotency_contract"]["local_state_authority"])
        self.assertRegex(result["idempotency_contract"]["main_task"]["contract_digest"], r"^[0-9a-f]{64}$")
        self.assertRegex(
            result["idempotency_contract"]["main_task"]["idempotency_key"],
            rf"^overkill:{binding['card_id']}:main:[0-9a-f]{{16}}$",
        )
        self.assertRegex(
            result["idempotency_contract"]["worker_tasks"]["codex-security"]["idempotency_key"],
            rf"^overkill:{binding['card_id']}:codex-security:[0-9a-f]{{16}}$",
        )
        create_keys = [call[call.index("--idempotency-key") + 1] for call in fake.calls if "--idempotency-key" in call]
        self.assertIn(result["idempotency_contract"]["main_task"]["idempotency_key"], create_keys)
        self.assertIn(result["idempotency_contract"]["worker_tasks"]["codex-security"]["idempotency_key"], create_keys)
        self.assertNotIn(f"overkill:{binding['card_id']}:main", create_keys)
        self.assertNotIn(f"overkill:{binding['card_id']}:codex-security", create_keys)
        materialized_tasks = [
            task for task in ledger_data["tasks"].values()
            if task["worker_id"] == "codex-security" and task["materialization_state"] == "materialized_in_hermes"
        ]
        self.assertEqual(len(materialized_tasks), 1)
        self.assertEqual(materialized_tasks[0]["runtime_refs"]["hermes_board_ref"], f"hermes:{TEST_BOARD}")
        self.assertTrue(materialized_tasks[0]["runtime_refs"]["hermes_task_ref"].startswith("t_"))
        link_calls = [call for call in fake.calls if len(call) >= 7 and call[4] == "link"]
        self.assertTrue(link_calls)
        for call in link_calls:
            self.assertEqual(call[-1], MAIN_TASK_ID)
            self.assertNotEqual(call[-2], MAIN_TASK_ID)

    def test_materialize_promotes_only_authorized_review_child(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="continue after review",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        receipt_payload = {
            "handoff_packet_result": handoff,
            "orchestration_result": factoryctl.build_worker_result(
                "factory-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="orchestration-smoke",
                executed_by="factory-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Orchestration precondition passed.",
                next_action="continue",
            ),
            "source_ledger_result": factoryctl.build_worker_result(
                "source-ledger-worker",
                card_data,
                result="PASS",
                tool_or_profile="source-ledger-smoke",
                executed_by="source-ledger-worker",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Source ledger precondition passed.",
                next_action="continue",
            ),
            "security_orchestration_result": factoryctl.build_worker_result(
                "security-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="security-orchestration-smoke",
                executed_by="security-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Security orchestration precondition passed.",
                next_action="continue",
            ),
            "supply_chain_result": factoryctl.build_worker_result(
                "supply-chain-gate",
                card_data,
                result="PASS",
                tool_or_profile="supply-chain-smoke",
                executed_by="supply-chain-gate",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Supply chain precondition passed.",
                next_action="continue",
            ),
        }
        receipt_payload["security_orchestration_result"]["solana_ai_kit_usage_receipt"] = solana_ai_kit_usage_receipt()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "route-readiness.json"
            receipt = tmp_path / "receipt.json"
            ledger = tmp_path / "ledger.json"
            write_route_readiness(readiness)
            receipt.write_text(json.dumps(receipt_payload), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(ledger),
                    "--receipt",
                    str(receipt),
                    "--from-status",
                    "doing",
                    "--to-status",
                    "implementation-ready-for-review",
                    "--route-readiness",
                    str(readiness),
                ]
            )
            result = adapter.materialize(args, runner=fake)
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        review_tasks = [
            task for task in ledger_data["tasks"].values()
            if task["worker_id"] == "independent-reviewer" and task["materialization_state"] == "materialized_in_hermes"
        ]
        self.assertEqual(len(review_tasks), 1)
        review_task_id = review_tasks[0]["runtime_refs"]["hermes_task_ref"]
        self.assertEqual(len(unblock_calls), 1)
        self.assertEqual(unblock_calls[0][5], review_task_id)
        self.assertEqual(result["worker_task_ids"]["independent-reviewer"], adapter.PUBLIC_SAFE_KANBAN_REF)
        self.assertEqual(
            result["review_promoted_worker_task_ids"],
            {"independent-reviewer": adapter.PUBLIC_SAFE_KANBAN_REF},
        )
        self.assertNotIn("handoff-packer", result["review_promoted_worker_task_ids"])

    def test_materialize_promotes_factory_owned_recovery_repair_task(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="continue after review",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "route-readiness.json"
            worker_results = tmp_path / "worker-results"
            worker_results.mkdir()
            ledger = tmp_path / "ledger.json"
            handoff_path = worker_results / "handoff.json"
            review_path = worker_results / "review.json"
            write_route_readiness(readiness)
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]
            blocked_review = factoryctl.build_worker_result(
                "independent-reviewer",
                card_data,
                result="BLOCKED",
                tool_or_profile="independent-review-smoke",
                executed_by="independent-reviewer",
                evidence_refs=["README.md"],
                blocking_findings=True,
                findings_summary="Review found the handoff packet incomplete.",
                next_action="repair handoff packet and rerun independent review",
                reusable_for_product=False,
            )
            blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]
            review_path.write_text(json.dumps(blocked_review), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(ledger),
                    "--worker-results-dir",
                    str(worker_results),
                    "--route-readiness",
                    str(readiness),
                ]
            )
            result = adapter.materialize(args, runner=fake)
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        self.assertEqual(result["recovery_promoted_worker_task_ids"], {"handoff-packer": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["review_promoted_worker_task_ids"], {"independent-reviewer": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["attempt_number"], 1)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["attempt_source"], "hermes_task_history")
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["history_ref_count"], 0)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["status"], "attempt_authorized")
        self.assertTrue(result["recovery_attempts"]["handoff-packer"]["attempted_this_run"])
        assert_live_adapter_result_schema(self, result)
        handoff_task = next(task for task in ledger_data["tasks"].values() if task["worker_id"] == "handoff-packer")
        handoff_task_id = handoff_task["runtime_refs"]["hermes_task_ref"]
        self.assertTrue(handoff_task["recovery_route_refs"])
        self.assertEqual(fake.tasks[handoff_task_id]["status"], "ready")
        self.assertEqual(fake.tasks[MAIN_TASK_ID]["status"], "blocked")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertTrue(any(call[5] == handoff_task_id and "downstream remains gated" in call[-1] for call in unblock_calls))
        self.assertTrue(any(call[5] == handoff_task_id and "factory_recovery_attempt" in call[-1] for call in unblock_calls))
        self.assertTrue(any(call[5] == handoff_task_id and "attempt_number=1 max_attempts=10" in call[-1] for call in unblock_calls))

    def test_materialize_keeps_recovery_task_blocked_after_retry_limit(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="continue after review",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "route-readiness.json"
            worker_results = tmp_path / "worker-results"
            worker_results.mkdir()
            ledger = tmp_path / "ledger.json"
            handoff_path = worker_results / "handoff.json"
            review_path = worker_results / "review.json"
            write_route_readiness(readiness)
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]
            blocked_review = factoryctl.build_worker_result(
                "independent-reviewer",
                card_data,
                result="BLOCKED",
                tool_or_profile="independent-review-smoke",
                executed_by="independent-reviewer",
                evidence_refs=["README.md"],
                blocking_findings=True,
                findings_summary="Review found the handoff packet incomplete.",
                next_action="repair handoff packet and rerun independent review",
                reusable_for_product=False,
            )
            blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]
            review_path.write_text(json.dumps(blocked_review), encoding="utf-8")
            plan = factoryctl.build_transition_plan(
                card_data,
                card,
                from_status="blocked",
                to_status="ready",
                worker_results_dir=worker_results,
            )
            route = plan["recovery_routes"][0]
            route_id = route["recovery_route_id"]
            route_digest = adapter.recovery_route_digest(route)
            handoff_task = next(task for task in plan["worker_tasks"] if task["worker_id"] == "handoff-packer")
            existing_task_id = "t_" + "retry0001"
            fake.idempotent_task_ids[
                adapter.worker_task_idempotency_key(
                    card_data["card_id"],
                    "handoff-packer",
                    adapter.worker_materialization_contract(handoff_task),
                )
            ] = existing_task_id
            fake.tasks[existing_task_id] = {
                "status": "blocked",
                "events": [
                    {
                        "type": "comment",
                        "reason": f"{route_id} mentions recovery but is not a stable attempt marker",
                    },
                    *[
                        {
                            "type": "unblocked",
                            "reason": (
                                "factory_recovery_attempt "
                                f"route_id={route_id} route_digest={route_digest} "
                                f"attempt_number={index} max_attempts=10"
                            ),
                        }
                        for index in range(1, 11)
                    ],
                ],
            }
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(ledger),
                    "--worker-results-dir",
                    str(worker_results),
                    "--route-readiness",
                    str(readiness),
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertEqual(result["recovery_promoted_worker_task_ids"], {})
        self.assertEqual(result["recovery_retry_blocked_worker_task_ids"], {"handoff-packer": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["previous_attempts"], 10)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["attempt_number"], 11)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["max_attempts"], 10)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["history_ref_count"], 10)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["status"], "retry_limit_exceeded")
        self.assertFalse(result["recovery_attempts"]["handoff-packer"]["attempted_this_run"])
        assert_live_adapter_result_schema(self, result)
        self.assertEqual(fake.tasks[existing_task_id]["status"], "blocked")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertFalse(any(call[5] == existing_task_id for call in unblock_calls))

    def test_materialize_does_not_reblock_or_unblock_active_recovery_task_on_rerun(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="continue after review",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "route-readiness.json"
            worker_results = tmp_path / "worker-results"
            worker_results.mkdir()
            ledger = tmp_path / "ledger.json"
            handoff_path = worker_results / "handoff.json"
            review_path = worker_results / "review.json"
            write_route_readiness(readiness)
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]
            blocked_review = factoryctl.build_worker_result(
                "independent-reviewer",
                card_data,
                result="BLOCKED",
                tool_or_profile="independent-review-smoke",
                executed_by="independent-reviewer",
                evidence_refs=["README.md"],
                blocking_findings=True,
                findings_summary="Review found the handoff packet incomplete.",
                next_action="repair handoff packet and rerun independent review",
                reusable_for_product=False,
            )
            blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]
            review_path.write_text(json.dumps(blocked_review), encoding="utf-8")
            plan = factoryctl.build_transition_plan(
                card_data,
                card,
                from_status="blocked",
                to_status="ready",
                worker_results_dir=worker_results,
            )
            route = plan["recovery_routes"][0]
            route_id = route["recovery_route_id"]
            route_digest = adapter.recovery_route_digest(route)
            handoff_task = next(task for task in plan["worker_tasks"] if task["worker_id"] == "handoff-packer")
            existing_task_id = "t_" + "ready1111"
            fake.idempotent_task_ids[
                adapter.worker_task_idempotency_key(
                    card_data["card_id"],
                    "handoff-packer",
                    adapter.worker_materialization_contract(handoff_task),
                )
            ] = existing_task_id
            fake.tasks[existing_task_id] = {
                "status": "ready",
                "events": [
                    {
                        "type": "unblocked",
                        "reason": (
                            "factory_recovery_attempt "
                            f"route_id={route_id} route_digest={route_digest} "
                            "attempt_number=1 max_attempts=10"
                        ),
                    }
                ],
            }
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(ledger),
                    "--worker-results-dir",
                    str(worker_results),
                    "--route-readiness",
                    str(readiness),
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertEqual(result["recovery_promoted_worker_task_ids"], {})
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["previous_attempts"], 1)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["attempt_number"], 2)
        self.assertEqual(result["recovery_attempts"]["handoff-packer"]["status"], "already_active_no_new_attempt")
        self.assertFalse(result["recovery_attempts"]["handoff-packer"]["attempted_this_run"])
        assert_live_adapter_result_schema(self, result)
        block_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "block"]
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertFalse(any(call[5] == existing_task_id for call in block_calls))
        self.assertFalse(any(call[5] == existing_task_id for call in unblock_calls))
        self.assertEqual(fake.tasks[existing_task_id]["status"], "ready")

    def test_materialize_promotes_downstream_workers_after_fresh_review_pass(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card_data = factoryctl.load_json_like(card)
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card_data,
            result="PASS",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Handoff packet declares an independent review gate.",
            next_action="continue after review",
            reviewer_required=True,
            reviewer_result="PENDING",
        )
        route_ref = "recovery:val-solana-quasar-r3:review-block:handoff"
        route_digest = "sha256:" + ("2" * 64)
        handoff["recovery_route_refs"] = [route_ref]
        handoff["recovery_route_digests"] = [route_digest]
        requirement = factoryctl.declared_graph_requirements(
            "handoff_packet_result",
            handoff,
            evidence_ref="receipt:handoff_packet_result",
        )[0]
        review = factoryctl.build_worker_result(
            "independent-reviewer",
            card_data,
            result="PASS",
            tool_or_profile="independent-review-smoke",
            executed_by="independent-reviewer",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Fresh review passed the repaired handoff packet.",
            next_action="continue downstream",
        )
        review["graph_requirement_refs"] = [requirement["requirement_id"]]
        review["reviewed_recovery_route_refs"] = [route_ref]
        review["reviewed_recovery_route_digests"] = [route_digest]
        review["authorized_downstream_worker_ids"] = [
            "qa-verification-worker",
            "human-gate-clerk",
            "handoff-packer",
            "unknown-worker",
        ]
        receipt_payload = {
            "handoff_packet_result": handoff,
            "independent_review_result": review,
            "orchestration_result": factoryctl.build_worker_result(
                "factory-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="orchestration-smoke",
                executed_by="factory-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Orchestration precondition passed.",
                next_action="continue",
            ),
            "source_ledger_result": factoryctl.build_worker_result(
                "source-ledger-worker",
                card_data,
                result="PASS",
                tool_or_profile="source-ledger-smoke",
                executed_by="source-ledger-worker",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Source ledger precondition passed.",
                next_action="continue",
            ),
            "security_orchestration_result": factoryctl.build_worker_result(
                "security-orchestrator",
                card_data,
                result="PASS",
                tool_or_profile="security-orchestration-smoke",
                executed_by="security-orchestrator",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Security orchestration precondition passed.",
                next_action="continue",
            ),
            "supply_chain_result": factoryctl.build_worker_result(
                "supply-chain-gate",
                card_data,
                result="PASS",
                tool_or_profile="supply-chain-smoke",
                executed_by="supply-chain-gate",
                evidence_refs=["README.md"],
                blocking_findings=False,
                findings_summary="Supply chain precondition passed.",
                next_action="continue",
            ),
        }
        receipt_payload["security_orchestration_result"]["solana_ai_kit_usage_receipt"] = solana_ai_kit_usage_receipt()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            readiness = tmp_path / "route-readiness.json"
            receipt = tmp_path / "receipt.json"
            ledger = tmp_path / "ledger.json"
            write_route_readiness(readiness)
            receipt.write_text(json.dumps(receipt_payload), encoding="utf-8")
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(ledger),
                    "--receipt",
                    str(receipt),
                    "--from-status",
                    "review",
                    "--to-status",
                    "ready",
                    "--route-readiness",
                    str(readiness),
                ]
            )
            result = adapter.materialize(args, runner=fake)
            ledger_data = json.loads(ledger.read_text(encoding="utf-8"))

        promoted = result["downstream_promoted_worker_task_ids"]
        self.assertEqual(promoted, {"qa-verification-worker": adapter.PUBLIC_SAFE_KANBAN_REF})
        self.assertNotIn("codex-security", promoted)
        self.assertNotIn("human-gate-clerk", promoted)
        self.assertNotIn("handoff-packer", promoted)
        self.assertNotIn("independent-reviewer", promoted)
        qa_task = next(task for task in ledger_data["tasks"].values() if task["worker_id"] == "qa-verification-worker")
        codex_security_task = next(task for task in ledger_data["tasks"].values() if task["worker_id"] == "codex-security")
        human_gate_task = next(task for task in ledger_data["tasks"].values() if task["worker_id"] == "human-gate-clerk")
        self.assertEqual(fake.tasks[qa_task["runtime_refs"]["hermes_task_ref"]]["status"], "ready")
        self.assertEqual(fake.tasks[codex_security_task["runtime_refs"]["hermes_task_ref"]]["status"], "blocked")
        self.assertEqual(fake.tasks[human_gate_task["runtime_refs"]["hermes_task_ref"]]["status"], "blocked")
        self.assertEqual(fake.tasks[MAIN_TASK_ID]["status"], "blocked")
        unblock_calls = [call for call in fake.calls if len(call) >= 5 and call[4] == "unblock"]
        self.assertTrue(
            any(
                call[5] == qa_task["runtime_refs"]["hermes_task_ref"]
                and "Fresh PASS review authorized exact downstream worker" in call[-1]
                and "authorized_worker_id=qa-verification-worker" in call[-1]
                and f"requirement_id={requirement['requirement_id']}" in call[-1]
                and "review_evidence_ref=receipt:review" in call[-1]
                and f"recovery_route_ref={route_ref}" in call[-1]
                and f"recovery_route_digest={route_digest}" in call[-1]
                for call in unblock_calls
            )
        )

    def test_materialize_dry_run_does_not_call_hermes_create(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        with tempfile.TemporaryDirectory() as tmp:
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--dry-run",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertFalse(any(len(call) >= 5 and call[4] == "create" for call in fake.calls))

    def test_materialize_dry_run_with_ensure_board_does_not_touch_hermes(self) -> None:
        fake = FakeHermes()
        card = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        with tempfile.TemporaryDirectory() as tmp:
            args = adapter.build_parser().parse_args(
                [
                    "materialize",
                    "--card",
                    str(card),
                    "--board",
                    TEST_BOARD,
                    "--ledger",
                    str(Path(tmp) / "ledger.json"),
                    "--dry-run",
                    "--ensure-board",
                ]
            )
            result = adapter.materialize(args, runner=fake)

        self.assertTrue(result["dry_run"])
        self.assertTrue(result["board_create_requested"])
        self.assertFalse(result["board_create_checked"])
        self.assertEqual(fake.calls, [])

    def test_block_command_matches_real_hermes_cli_shape(self) -> None:
        fake = FakeHermes()

        adapter.ensure_blocked_event(
            hermes_bin="hermes",
            board=TEST_BOARD,
            task_id=MAIN_TASK_ID,
            reason="gate",
            runner=fake,
        )

        self.assertEqual(
            fake.calls[0],
            ["hermes", "kanban", "--board", TEST_BOARD, "block", "--kind", "transient", MAIN_TASK_ID, "gate"],
        )
        self.assertIn("--kind", fake.calls[0])
        self.assertNotIn("--reason", fake.calls[0])
        self.assertNotIn("--json", fake.calls[0])

    def test_no_idle_classifies_native_dependency_wait_without_human_gate(self) -> None:
        state = adapter.classify_no_idle_state(
            {
                "todo": [
                    {"id": "t_parent", "status": "todo", "events": []},
                    {
                        "id": "t_child",
                        "status": "todo",
                        "parents": [{"id": "t_parent"}],
                        "events": [{"type": "dependency_wait", "payload": {"kind": "dependency"}}],
                    },
                ],
                "blocked": [],
                "ready": [],
                "running": [],
                "done": [],
            }
        )

        self.assertEqual(state["status"], "dependency_gated")
        self.assertEqual(state["classification"], "hermes_native_dependency_wait")
        self.assertEqual(state["typed_block_kind"], "dependency")
        self.assertFalse(state["human_gate_required"])

    def test_no_idle_classifies_block_loop_detected_as_internal_triage(self) -> None:
        state = adapter.classify_no_idle_state(
            {
                "todo": [],
                "blocked": [],
                "triage": [
                    {
                        "id": "t_loop",
                        "status": "triage",
                        "events": [{"kind": "block_loop_detected", "payload": {"kind": "transient", "recurrences": 2}}],
                    }
                ],
                "ready": [],
                "running": [],
                "done": [],
            }
        )

        self.assertEqual(state["status"], "remediation_required")
        self.assertEqual(state["classification"], "hermes_typed_block_loop_detected")
        self.assertTrue(state["block_loop_detected"])
        self.assertFalse(state["human_gate_required"])

    def test_complete_main_requires_materialized_live_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "ledger_type": "overkill_factory_hermes_worker_ledger",
                        "ledger_scope": "projection_idempotency_only",
                        "runtime_authority": "hermes_kanban",
                        "local_state_authority": False,
                        "tasks": {},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "missing live binding"):
                adapter.validate_live_binding(
                    ledger_path=ledger,
                    card_id="CARD-001",
                    board=TEST_BOARD,
                    main_task_id="fixture-main-task",
                )

    def test_complete_main_rejects_local_authority_live_binding(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            ledger.write_text(
                json.dumps(
                    {
                        "ledger_type": "overkill_factory_hermes_worker_ledger",
                        "ledger_scope": "projection_idempotency_only",
                        "runtime_authority": "hermes_kanban",
                        "local_state_authority": False,
                        "tasks": {},
                        "live_bindings": {
                            "CARD-001": {
                                "binding_role": "local_state",
                                "runtime_authority": "local-file",
                                "local_state_authority": True,
                                "board": TEST_BOARD,
                                "main_task_id": "fixture-main-task",
                                "worker_task_ids": {},
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(RuntimeError, "not a Hermes-authoritative projection"):
                adapter.validate_live_binding(
                    ledger_path=ledger,
                    card_id="CARD-001",
                    board=TEST_BOARD,
                    main_task_id="fixture-main-task",
                )


if __name__ == "__main__":
    unittest.main()
