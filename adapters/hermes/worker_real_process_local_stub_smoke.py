#!/usr/bin/env python3
"""Prove one real Hermes worker process can complete through kanban_complete.

This smoke runs only against a disposable installed Hermes checkout/home. It
starts a local OpenAI-compatible stub, points one disposable worker profile at
that stub, lets the real Hermes dispatcher spawn a real child process, and makes
the stub return a `kanban_complete` tool call with structured Overkill worker
result metadata.

It does not prove real model quality, real specialist reasoning, external tool
auth, or production readiness.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
READY_CARD = ROOT / "validation" / "cards" / "vfinal-r3-ready.md"
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "worker-real-process-local-stub-smoke.json"
DEFAULT_MODEL = "overkill-local-tool-smoke-model"
DEFAULT_WORKER_ID = "software-development-planner"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def _assert_disposable_home(path: Path, *, allow_non_disposable: bool) -> None:
    if allow_non_disposable:
        return
    lowered = str(path.resolve()).lower()
    if "\\.tmp\\" in lowered or "/.tmp/" in lowered or lowered.endswith("\\.tmp") or lowered.endswith("/.tmp"):
        return
    raise SystemExit(
        "--hermes-home must point to a disposable .tmp runtime, or pass "
        "--allow-non-disposable after an explicit operator decision."
    )


def _venv_scripts_dir(hermes_checkout: Path) -> Path:
    return hermes_checkout / ".venv" / ("Scripts" if os.name == "nt" else "bin")


def _hermes_bin(hermes_checkout: Path) -> Path | None:
    scripts = _venv_scripts_dir(hermes_checkout)
    candidates = [
        scripts / "hermes.exe",
        scripts / "hermes",
        scripts / "hermes.cmd",
        scripts / "hermes.bat",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _load_kanban_db(hermes_checkout: Path, hermes_home: Path, board: str) -> Any:
    scripts = _venv_scripts_dir(hermes_checkout)
    os.environ["HERMES_HOME"] = str(hermes_home)
    os.environ["HOME"] = str(hermes_home)
    os.environ["HERMES_KANBAN_BOARD"] = board
    os.environ["OVERKILL_FACTORY_KANBAN_GATE"] = "1"
    os.environ["OVERKILL_FACTORY_ADAPTER_ROOT"] = str(ROOT)
    os.environ["OVERKILL_FACTORY_CREATE_WORKER_TASKS"] = "1"
    os.environ["OVERKILL_FACTORY_WORKER_TASK_STATUS"] = "ready"
    os.environ["OVERKILL_FACTORY_RUNTIME_DIR"] = str(hermes_home / "overkill-factory")
    os.environ["PYTHONPATH"] = str(hermes_checkout) + os.pathsep + os.environ.get("PYTHONPATH", "")
    os.environ["PATH"] = str(scripts) + os.pathsep + os.environ.get("PATH", "")
    resolved_bin = _hermes_bin(hermes_checkout)
    if resolved_bin is not None:
        os.environ["HERMES_BIN"] = str(resolved_bin)
    sys.path.insert(0, str(hermes_checkout))
    from hermes_cli import kanban_db  # type: ignore

    return kanban_db


def _profile_dir(hermes_home: Path, worker_id: str) -> Path:
    if worker_id == "default":
        return hermes_home
    return hermes_home / "profiles" / worker_id


def _write_profile_config(
    *,
    hermes_home: Path,
    worker_id: str,
    model: str,
    base_url: str,
) -> None:
    profile_dir = _profile_dir(hermes_home, worker_id)
    profile_dir.mkdir(parents=True, exist_ok=True)
    (profile_dir / "config.yaml").write_text(
        "\n".join(
            [
                "model:",
                f"  default: {model}",
                "  provider: lmstudio",
                f"  base_url: {base_url}",
                "agent:",
                "  max_turns: 3",
                "streaming:",
                "  enabled: false",
                "display:",
                "  interface: cli",
                "toolsets:",
                "  - hermes-cli",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _result_files(hermes_home: Path, parent_task_id: str) -> list[str]:
    result_dir = hermes_home / "overkill-factory" / parent_task_id / "worker-results"
    if not result_dir.is_dir():
        return []
    return sorted(path.name for path in result_dir.glob("*.json"))


def _terminate_pid_tree(pid: int) -> str:
    if pid <= 0:
        return "no-pid"
    try:
        if os.name == "nt":
            completed = subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"],
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=10,
                check=False,
            )
            return f"taskkill-exit-{completed.returncode}"
        os.kill(pid, 15)
        return "sigterm-sent"
    except Exception as exc:  # pragma: no cover - platform cleanup best effort
        return f"cleanup-failed:{type(exc).__name__}"


class _ToolCallStubState:
    def __init__(
        self,
        *,
        model: str,
        task_id: str,
        worker_id: str,
        record_type: str,
    ) -> None:
        self.model = model
        self.task_id = task_id
        self.worker_id = worker_id
        self.record_type = record_type
        self.lock = threading.Lock()
        self.chat_requests: list[dict[str, Any]] = []
        self.tool_call_sent = False

    def remember_request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        tools = payload.get("tools") if isinstance(payload, dict) else None
        tool_names: list[str] = []
        if isinstance(tools, list):
            for tool in tools:
                if not isinstance(tool, dict):
                    continue
                fn = tool.get("function") if isinstance(tool.get("function"), dict) else {}
                name = fn.get("name") or tool.get("name")
                if isinstance(name, str) and name:
                    tool_names.append(name)
        summary = {
            "path": path,
            "model": str(payload.get("model") or ""),
            "message_count": len(payload.get("messages") or []) if isinstance(payload.get("messages"), list) else 0,
            "tool_count": len(tool_names),
            "has_kanban_complete": "kanban_complete" in tool_names,
        }
        with self.lock:
            self.chat_requests.append(summary)
        return summary

    def build_tool_call_response(self) -> dict[str, Any]:
        args = {
            "task_id": self.task_id,
            "summary": f"Real Hermes child process completed local stub proof for {self.worker_id}.",
            "result": "PASS",
            "metadata": {
                "overkill_worker_result": {
                    "record_type": self.record_type,
                    "result": "PASS",
                    "blocking_findings": False,
                    "findings_summary": (
                        f"Real Hermes child process called kanban_complete through a local "
                        f"OpenAI-compatible stub for {self.worker_id}."
                    ),
                    "tool_or_profile": f"real-hermes-process-local-stub:{self.worker_id}",
                    "executed_by": "hermes-child-process-local-stub",
                    "evidence_refs": [
                        "validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json"
                    ],
                    "next_action": (
                        "Treat as bounded process/tool-loop proof only; run real model/tool "
                        "quality proof before production."
                    ),
                }
            },
        }
        with self.lock:
            self.tool_call_sent = True
        return {
            "id": "chatcmpl-overkill-local-tool-stub",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [
                            {
                                "id": "call_overkill_kanban_complete",
                                "type": "function",
                                "function": {
                                    "name": "kanban_complete",
                                    "arguments": json.dumps(args, separators=(",", ":")),
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    def build_final_response(self) -> dict[str, Any]:
        return {
            "id": "chatcmpl-overkill-local-tool-stub-final",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self.model,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "Local stub worker completion finished.",
                    },
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }


class _ToolCallStubHandler(BaseHTTPRequestHandler):
    state: _ToolCallStubState

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_sse(self, events: list[dict[str, Any]]) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self.end_headers()
        for event in events:
            data = json.dumps(event, separators=(",", ":")).encode("utf-8")
            self.wfile.write(b"data: " + data + b"\n\n")
            self.wfile.flush()
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _tool_call_stream_events(self) -> list[dict[str, Any]]:
        response = self.state.build_tool_call_response()
        choice = response["choices"][0]
        tool_call = choice["message"]["tool_calls"][0]
        arguments = tool_call["function"]["arguments"]
        created = int(time.time())
        return [
            {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.state.model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            },
            {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.state.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "id": tool_call["id"],
                                    "type": "function",
                                    "function": {
                                        "name": "kanban_complete",
                                        "arguments": "",
                                    },
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.state.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {
                            "tool_calls": [
                                {
                                    "index": 0,
                                    "function": {"arguments": arguments},
                                }
                            ]
                        },
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.state.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "tool_calls"}],
            },
        ]

    def _final_stream_events(self) -> list[dict[str, Any]]:
        response = self.state.build_final_response()
        created = int(time.time())
        return [
            {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.state.model,
                "choices": [{"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}],
            },
            {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.state.model,
                "choices": [
                    {
                        "index": 0,
                        "delta": {"content": "Local stub worker completion finished."},
                        "finish_reason": None,
                    }
                ],
            },
            {
                "id": response["id"],
                "object": "chat.completion.chunk",
                "created": created,
                "model": self.state.model,
                "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
            },
        ]

    def do_GET(self) -> None:
        path = self.path.split("?", 1)[0].rstrip("/")
        if path in {"/v1/models", "/models", "/api/v1/models"}:
            self._send_json(
                {
                    "object": "list",
                    "data": [
                        {
                            "id": self.state.model,
                            "object": "model",
                            "created": 0,
                            "owned_by": "overkill-local-tool-stub",
                        }
                    ],
                }
            )
            return
        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            payload = {}
        path = self.path.split("?", 1)[0].rstrip("/")
        if path in {"/v1/chat/completions", "/chat/completions"}:
            summary = self.state.remember_request(path, payload if isinstance(payload, dict) else {})
            if summary.get("has_kanban_complete") and not self.state.tool_call_sent:
                if isinstance(payload, dict) and payload.get("stream"):
                    self._send_sse(self._tool_call_stream_events())
                    return
                self._send_json(self.state.build_tool_call_response())
                return
            if isinstance(payload, dict) and payload.get("stream"):
                self._send_sse(self._final_stream_events())
                return
            self._send_json(self.state.build_final_response())
            return
        self.send_error(404)


class LocalToolCallStub:
    def __init__(
        self,
        *,
        model: str,
        task_id: str,
        worker_id: str,
        record_type: str,
    ) -> None:
        self.state = _ToolCallStubState(
            model=model,
            task_id=task_id,
            worker_id=worker_id,
            record_type=record_type,
        )
        handler = type("ToolCallStubHandler", (_ToolCallStubHandler,), {"state": self.state})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1"

    def __enter__(self) -> "LocalToolCallStub":
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def _parse_subtask(body: str) -> dict[str, Any]:
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _task_event_kinds(kb: Any, board: str, task_id: str) -> list[str]:
    with kb.connect_closing(board=board) as conn:
        return [
            row["kind"]
            for row in conn.execute(
                "SELECT kind FROM task_events WHERE task_id = ? ORDER BY id",
                (task_id,),
            ).fetchall()
        ]


def _task_status(kb: Any, board: str, task_id: str) -> tuple[str | None, int | None]:
    with kb.connect_closing(board=board) as conn:
        row = conn.execute(
            "SELECT status, worker_pid FROM tasks WHERE id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            return None, None
        return row["status"], row["worker_pid"]


def run_smoke(
    *,
    hermes_checkout: Path,
    hermes_home: Path,
    worker_id: str = DEFAULT_WORKER_ID,
    model: str = DEFAULT_MODEL,
    timeout_seconds: int = 45,
    allow_non_disposable: bool = False,
) -> dict[str, Any]:
    _assert_disposable_home(hermes_home, allow_non_disposable=allow_non_disposable)
    if not (hermes_checkout / "hermes_cli" / "kanban_db.py").is_file():
        raise SystemExit(f"missing Hermes kanban_db.py under {hermes_checkout}")
    if not READY_CARD.is_file():
        raise SystemExit(f"missing ready card fixture: {READY_CARD}")

    board = f"of-real-worker-stub-{int(time.time())}"
    kb = _load_kanban_db(hermes_checkout, hermes_home, board)
    kb.create_board(
        board,
        name="Overkill real process local stub smoke",
        default_workdir=str(ROOT),
    )

    parent_task_id = ""
    child_task_id = ""
    record_type = ""
    worker_pid: int | None = None
    cleanup_result = "not-needed"
    dispatch_spawned_count = 0
    poll_statuses: list[str] = []
    child_event_kinds: list[str] = []
    parent_event_kinds: list[str] = []
    result_files: list[str] = []

    with kb.connect_closing(board=board) as conn:
        parent_task_id = kb.create_task(
            conn,
            title="VFINAL real Hermes process local stub smoke",
            body=READY_CARD.read_text(encoding="utf-8"),
            assignee="factory-orchestrator",
            created_by="worker-real-process-local-stub-smoke",
            workspace_kind="dir",
            workspace_path=str(ROOT),
            max_retries=1,
            board=board,
        )
        chosen = conn.execute(
            "SELECT id, body FROM tasks WHERE id != ? AND assignee = ? ORDER BY created_at, id LIMIT 1",
            (parent_task_id, worker_id),
        ).fetchone()
        if chosen is None:
            raise RuntimeError(f"worker subtask not materialized for {worker_id}")
        child_task_id = chosen["id"]
        subtask = _parse_subtask(chosen["body"])
        record_type = str(subtask.get("expected_receipt_field") or "worker-result")
        conn.execute(
            "UPDATE tasks SET status = 'todo' WHERE id != ? AND id != ?",
            (parent_task_id, child_task_id),
        )
        conn.execute(
            "UPDATE tasks SET status = 'ready', priority = 100, max_runtime_seconds = 30, max_retries = 1 WHERE id = ?",
            (child_task_id,),
        )
        conn.commit()

    with LocalToolCallStub(
        model=model,
        task_id=child_task_id,
        worker_id=worker_id,
        record_type=record_type,
    ) as stub:
        _write_profile_config(
            hermes_home=hermes_home,
            worker_id=worker_id,
            model=model,
            base_url=stub.base_url,
        )
        with kb.connect_closing(board=board) as conn:
            dispatch_result = kb.dispatch_once(
                conn,
                max_spawn=1,
                failure_limit=1,
                board=board,
            )
            dispatch_spawned_count = len(dispatch_result.spawned)
            row = conn.execute(
                "SELECT worker_pid FROM tasks WHERE id = ?",
                (child_task_id,),
            ).fetchone()
            worker_pid = int(row["worker_pid"]) if row and row["worker_pid"] else None

        deadline = time.time() + timeout_seconds
        while time.time() < deadline:
            status, current_pid = _task_status(kb, board, child_task_id)
            if status:
                poll_statuses.append(status)
            if current_pid and not worker_pid:
                worker_pid = int(current_pid)
            if status in {"done", "blocked", "failed", "review"}:
                break
            time.sleep(1)

        final_status, current_pid = _task_status(kb, board, child_task_id)
        if current_pid and not worker_pid:
            worker_pid = int(current_pid)
        if final_status != "done" and worker_pid:
            cleanup_result = _terminate_pid_tree(worker_pid)

        child_event_kinds = _task_event_kinds(kb, board, child_task_id)
        parent_event_kinds = _task_event_kinds(kb, board, parent_task_id)
        result_files = _result_files(hermes_home, parent_task_id)
        stub_requests = list(stub.state.chat_requests)
        tool_call_sent = bool(stub.state.tool_call_sent)

    checks = {
        "dispatcher_spawned_real_process": "PASS" if dispatch_spawned_count == 1 and worker_pid else "FAIL",
        "stub_received_chat_request": "PASS" if stub_requests else "FAIL",
        "stub_saw_kanban_complete_tool": "PASS"
        if any(req.get("has_kanban_complete") for req in stub_requests)
        else "FAIL",
        "stub_sent_kanban_complete_tool_call": "PASS" if tool_call_sent else "FAIL",
        "worker_completed_task": "PASS" if final_status == "done" else "FAIL",
        "worker_result_ingested": "PASS" if result_files else "FAIL",
        "child_events_written": "PASS"
        if {"claimed", "completed", "overkill_worker_result_ingested"}.issubset(set(child_event_kinds))
        else "FAIL",
        "parent_event_written": "PASS"
        if "overkill_worker_result_ingested" in parent_event_kinds
        else "FAIL",
    }
    passed = all(value == "PASS" for value in checks.values())

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
            "card_id": "VFINAL-HERMES-WORKER-REAL-PROCESS-LOCAL-STUB-SMOKE",
            "slice_id": "VFINAL_HERMES_WORKER_REAL_PROCESS_LOCAL_STUB",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "worker-routing", "worker-results"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            "Disposable installed Hermes smoke passed for real child process spawn, local stub tool-call completion and parent worker-result ingestion."
            if passed
            else "Disposable installed Hermes real-process local-stub smoke failed or timed out."
        ),
        "tool_or_profile": "Hermes disposable installed runtime; real dispatcher spawn; local OpenAI-compatible tool-call stub",
        "executed_by": "remote-proof-runner",
        "runtime_scope": (
            "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; "
            "no production board, secrets, deploy, external model endpoint or real Hermes runtime mutation."
        ),
        "checks": checks,
        "disposable_task_evidence": {
            "board_slug": board,
            "parent_task_ref": "redacted-disposable-parent",
            "child_task_ref": "redacted-disposable-child",
            "worker_id": worker_id,
            "record_type": record_type,
            "dispatch_spawned_count": dispatch_spawned_count,
            "worker_pid_observed": bool(worker_pid),
            "final_child_status": final_status,
            "poll_statuses": poll_statuses[-10:],
            "cleanup_result": cleanup_result,
            "stub_request_summaries": stub_requests,
            "child_event_kinds": child_event_kinds,
            "parent_event_kinds": parent_event_kinds,
            "worker_result_files": result_files,
        },
        "important_limitations": [
            "This proves the real Hermes child process can receive the kanban tool surface and call kanban_complete through a local stub.",
            "The model was a deterministic local OpenAI-compatible stub, not a real reasoning model.",
            "This does not prove specialist output quality, external tool authentication, cloud access, repository mutation, deployment, rollback or production readiness.",
            "This does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            repo_ref(READY_CARD),
            "validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json",
            "validation/hermes-installed-runtime-smoke/worker-dispatch-completion-smoke.json",
            "validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json",
        ],
        "next_action": (
            "Run a bounded real-model worker proof with provisioned profile, tool auth, "
            "structured worker_result evidence and rollback receipt before production update."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-checkout", type=Path, required=True)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--worker-id", default=DEFAULT_WORKER_ID)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout-seconds", type=int, default=45)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-non-disposable", action="store_true")
    args = parser.parse_args(argv)

    receipt = run_smoke(
        hermes_checkout=args.hermes_checkout.expanduser().resolve(),
        hermes_home=args.hermes_home.expanduser().resolve(),
        worker_id=args.worker_id,
        model=args.model,
        timeout_seconds=args.timeout_seconds,
        allow_non_disposable=args.allow_non_disposable,
    )
    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    print(json.dumps({"result": receipt["result"], "out": repo_ref(out)}, indent=2))
    return 0 if receipt["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
