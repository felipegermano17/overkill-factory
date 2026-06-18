from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
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


class FakeHermes:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.counter = 0
        self.tasks: dict[str, dict[str, object]] = {}
        self.idempotent_task_ids: dict[str, str] = {}

    def __call__(self, argv: list[str]) -> subprocess.CompletedProcess[str]:
        self.calls.append(argv)
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
            initial_status = "blocked" if "--initial-status" in argv and "blocked" in argv else "ready"
            body = argv[argv.index("--body") + 1] if "--body" in argv else "{}"
            assignee = argv[argv.index("--assignee") + 1] if "--assignee" in argv else None
            workspace_ref = argv[argv.index("--workspace") + 1] if "--workspace" in argv else "scratch"
            task = {"id": task_id, "status": initial_status, "events": [], "body": body, "assignee": assignee}
            if workspace_ref.startswith("dir:"):
                task["workspace_kind"] = "dir"
                task["workspace_path"] = workspace_ref[4:]
            else:
                task["workspace_kind"] = workspace_ref
            self.tasks[task_id] = task
            if idempotency_key:
                self.idempotent_task_ids[idempotency_key] = task_id
            return subprocess.CompletedProcess(argv, 0, stdout=f'{{"id":"{task_id}"}}', stderr="")
        if len(argv) == 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "assign":
            task = self.tasks.setdefault(argv[5], {"status": "blocked", "events": [], "body": "{}", "assignee": None})
            task["assignee"] = argv[6]
            task.setdefault("events", []).append({"type": "assigned", "profile": argv[6]})
            return subprocess.CompletedProcess(argv, 0, stdout="assigned", stderr="")
        if len(argv) == 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "block":
            task = self.tasks.setdefault(argv[5], {"status": "ready", "events": []})
            task["status"] = "blocked"
            task.setdefault("events", []).append({"type": "blocked", "reason": argv[6]})
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
        if len(argv) == 7 and argv[0:3] == ["hermes", "kanban", "--board"] and argv[4] == "unblock":
            task = self.tasks.setdefault(argv[5], {"status": "blocked", "events": []})
            task["status"] = "ready"
            task.setdefault("events", []).append({"type": "unblocked", "payload": None})
            return subprocess.CompletedProcess(argv, 0, stdout='{"status":"ready"}', stderr="")
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
            ]
            if self.include_implementation_worker:
                rows.append(
                    " implementation-worker gpt-5.5                      stopped      implementation-worker -"
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
    def __init__(self, *, native_spawned: bool = False) -> None:
        self.calls: list[list[str]] = []
        self.native_spawned = native_spawned
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
                            }
                        ]
                    ),
                    stderr="",
                )
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
        "source-ledger-worker",
        "qa-verification-worker",
        "autoreview-gate",
        "security-orchestrator",
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


def two_step_ready_work_unit_plan() -> dict[str, object]:
    plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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
    plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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
        self.assertEqual([check["worker_id"] for check in result["checks"]], ["implementation-worker"])
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

    def test_materialize_ready_work_units_creates_blocked_tasks_without_dispatch(self) -> None:
        fake = FakeHermes()
        plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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

    def test_materialize_ready_work_units_chunks_large_body_without_losing_context(self) -> None:
        fake = FakeHermes()
        plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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
        plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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
        plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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
        plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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
            product_creation_plan_path.write_text(
                (ROOT / "templates" / "product-creation-plan.json").read_text(encoding="utf-8"),
                encoding="utf-8",
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
            product_creation_plan_path.write_text(
                (ROOT / "templates" / "product-creation-plan.json").read_text(encoding="utf-8"),
                encoding="utf-8",
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
            product_creation_plan_path.write_text(
                (ROOT / "templates" / "product-creation-plan.json").read_text(encoding="utf-8"),
                encoding="utf-8",
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
            product_creation_plan_path.write_text(
                (ROOT / "templates" / "product-creation-plan.json").read_text(encoding="utf-8"),
                encoding="utf-8",
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

    def test_close_product_creation_run_blocks_when_work_unit_review_blocks(self) -> None:
        fake = FakeHermes()
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            _plan, plan_path, readiness_path, materialization_result_path = materialize_template_ready_work_unit(
                fake=fake,
                tmp_path=tmp_path,
            )
            product_creation_plan_path = tmp_path / "product-creation-plan.json"
            product_creation_plan_path.write_text(
                (ROOT / "templates" / "product-creation-plan.json").read_text(encoding="utf-8"),
                encoding="utf-8",
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
            product_creation_plan_path.write_text(
                (ROOT / "templates" / "product-creation-plan.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
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
            product_creation_plan_path.write_text(
                (ROOT / "templates" / "product-creation-plan.json").read_text(encoding="utf-8"),
                encoding="utf-8",
            )
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
        self.assertEqual(fake.tasks[task_id].get("comments"), None)

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
        self.assertIn(adapter.READY_WORK_UNIT_SUPERSESSION_MARKER, fake.tasks[contaminated_task_id]["comments"][0]["body"])
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
        self.assertIn(
            adapter.READY_WORK_UNIT_SUPERSESSION_MARKER,
            fake.tasks[contaminated_task_id]["comments"][0]["body"],
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
                and not any(
                    adapter.READY_WORK_UNIT_SUPERSESSION_MARKER in str(comment.get("body") or "")
                    for comment in task.get("comments", [])
                )
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
        self.assertEqual(sorted(set(queried_statuses)), ["blocked", "done"])
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
        plan = factoryctl.load_json_like(ROOT / "templates" / "ready-work-unit-hermes-materialization-plan.json")
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
        self.assertTrue(any(call[5] == handoff_task_id and "downstream remains gated" in call[6] for call in unblock_calls))
        self.assertTrue(any(call[5] == handoff_task_id and "factory_recovery_attempt" in call[6] for call in unblock_calls))
        self.assertTrue(any(call[5] == handoff_task_id and "attempt_number=1 max_attempts=10" in call[6] for call in unblock_calls))

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
                and "Fresh PASS review authorized exact downstream worker" in call[6]
                and "authorized_worker_id=qa-verification-worker" in call[6]
                and f"requirement_id={requirement['requirement_id']}" in call[6]
                and "review_evidence_ref=receipt:review" in call[6]
                and f"recovery_route_ref={route_ref}" in call[6]
                and f"recovery_route_digest={route_digest}" in call[6]
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
            ["hermes", "kanban", "--board", TEST_BOARD, "block", MAIN_TASK_ID, "gate"],
        )
        self.assertNotIn("--reason", fake.calls[0])
        self.assertNotIn("--json", fake.calls[0])

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
