#!/usr/bin/env python3
"""Provision disposable worker profiles and prove readiness against a local stub.

This smoke is intentionally bounded. It proves profile/config/model/provider
shape plus OpenAI-compatible `/models` reachability. It does not prove real
model quality, tool auth, worker completion, or production readiness.
"""

from __future__ import annotations

import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from worker_route_readiness import check_readiness


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MODEL = "overkill-local-smoke-model"
DEFAULT_PROVIDER = "lmstudio"


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _extract_tasks(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    raw_tasks = ledger.get("tasks")
    if isinstance(raw_tasks, dict):
        return [task for task in raw_tasks.values() if isinstance(task, dict)]
    if isinstance(raw_tasks, list):
        return [task for task in raw_tasks if isinstance(task, dict)]
    return []


def _profile_dir(hermes_home: Path, worker_id: str) -> Path:
    if worker_id == "default":
        return hermes_home
    return hermes_home / "profiles" / worker_id


class _OpenAIStubHandler(BaseHTTPRequestHandler):
    model = DEFAULT_MODEL

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _send_json(self, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path.rstrip("/") in {"/v1/models", "/models"}:
            self._send_json(
                {
                    "object": "list",
                    "data": [
                        {
                            "id": self.model,
                            "object": "model",
                            "created": 0,
                            "owned_by": "overkill-local-stub",
                        }
                    ],
                }
            )
            return
        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        if self.path.rstrip("/") in {"/v1/chat/completions", "/chat/completions"}:
            self._send_json(
                {
                    "id": "chatcmpl-overkill-local-stub",
                    "object": "chat.completion",
                    "created": int(time.time()),
                    "model": self.model,
                    "choices": [
                        {
                            "index": 0,
                            "message": {
                                "role": "assistant",
                                "content": "OVERKILL_LOCAL_STUB_OK",
                            },
                            "finish_reason": "stop",
                        }
                    ],
                    "usage": {
                        "prompt_tokens": 1,
                        "completion_tokens": 1,
                        "total_tokens": 2,
                    },
                }
            )
            return
        if self.path.rstrip("/") in {"/v1/responses", "/responses"}:
            self._send_json(
                {
                    "id": "resp-overkill-local-stub",
                    "object": "response",
                    "created_at": int(time.time()),
                    "status": "completed",
                    "model": self.model,
                    "output": [
                        {
                            "type": "message",
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "output_text",
                                    "text": "OVERKILL_LOCAL_STUB_OK",
                                }
                            ],
                        }
                    ],
                    "output_text": "OVERKILL_LOCAL_STUB_OK",
                }
            )
            return
        self.send_error(404)


class LocalOpenAIStub:
    def __init__(self, model: str) -> None:
        handler = type("OpenAIStubHandler", (_OpenAIStubHandler,), {"model": model})
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def base_url(self) -> str:
        host, port = self.server.server_address
        return f"http://{host}:{port}/v1"

    def __enter__(self) -> "LocalOpenAIStub":
        self.thread.start()
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def _write_profile_config(
    *,
    profile_dir: Path,
    provider: str,
    model: str,
    base_url: str,
    overwrite: bool,
) -> str:
    profile_dir.mkdir(parents=True, exist_ok=True)
    config_path = profile_dir / "config.yaml"
    existed = config_path.exists()
    if existed and not overwrite:
        return "kept_existing"
    config_path.write_text(
        "\n".join(
            [
                "model:",
                f"  default: {model}",
                f"  provider: {provider}",
                f"  base_url: {base_url}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return "updated_existing" if existed else "created"


def run_smoke(
    *,
    ledger_path: Path,
    hermes_home: Path,
    overwrite: bool = False,
    model: str = DEFAULT_MODEL,
    provider: str = DEFAULT_PROVIDER,
) -> dict[str, Any]:
    ledger = _load_json(ledger_path)
    workers = sorted({str(task.get("worker_id") or "").strip() for task in _extract_tasks(ledger)})
    workers = [worker for worker in workers if worker]

    profile_actions: dict[str, str] = {}
    with LocalOpenAIStub(model) as stub:
        for worker_id in workers:
            profile_actions[worker_id] = _write_profile_config(
                profile_dir=_profile_dir(hermes_home, worker_id),
                provider=provider,
                model=model,
                base_url=stub.base_url,
                overwrite=overwrite,
            )
        readiness = check_readiness(
            ledger_path=ledger_path,
            hermes_home=hermes_home,
            require_credentials=True,
        )

    action_counts: dict[str, int] = {}
    for action in profile_actions.values():
        action_counts[action] = action_counts.get(action, 0) + 1

    return {
        "$schema": "https://overkill-factory.dev/schemas/hermes-worker-profile-readiness-smoke.schema.json",
        "schema": "overkill_factory_hermes_worker_profile_readiness_smoke.v1",
        "result": "PASS" if readiness["result"] == "PASS" else "BLOCKED",
        "scope": "disposable-local-openai-stub-only",
        "ledger_ref": "validation/hermes-disposable-runtime/worker-ledger.json"
        if ledger_path.name == "worker-ledger.json"
        else ledger_path.name,
        "hermes_home_ref": "redacted-hermes-home",
        "provider": provider,
        "model_ref": model,
        "endpoint_ref": "local-loopback-openai-compatible-stub",
        "worker_count": len(workers),
        "profile_action_counts": action_counts,
        "readiness_result": readiness["result"],
        "blocked_worker_count": int(readiness["blocked_worker_count"]),
        "blocked_workers": readiness["blocked_workers"],
        "production_limits": [
            "This proves disposable profile/config/model/provider shape and local OpenAI-compatible /models reachability only.",
            "It does not prove real model quality, real specialist output, tool authentication, autonomous completion, or production readiness.",
            "A real Hermes update still requires provisioned real profiles, worker execution, evidence reconciliation and rollback proof.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ledger", type=Path, required=True)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--provider", default=DEFAULT_PROVIDER)
    args = parser.parse_args(argv)

    receipt = run_smoke(
        ledger_path=args.ledger.expanduser().resolve(),
        hermes_home=args.hermes_home.expanduser().resolve(),
        overwrite=args.overwrite,
        model=args.model,
        provider=args.provider,
    )
    if args.out:
        out = args.out if args.out.is_absolute() else ROOT / args.out
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, ensure_ascii=False))
    return 0 if receipt["result"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
