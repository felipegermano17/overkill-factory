#!/usr/bin/env python3
"""Run the real-process local-stub smoke across all vFinal workers.

This aggregate smoke reuses `worker_real_process_local_stub_smoke.run_smoke`
for each worker listed in the public worker ledger. It proves broad disposable
worker-route parity for real Hermes child process spawn, `kanban_complete`, and
parent ingestion against a deterministic local OpenAI-compatible stub.

It still does not prove non-stub model quality, real tool authentication,
specialist reasoning quality, production deploy, or real-runtime rollback.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from worker_real_process_local_stub_smoke import DEFAULT_MODEL, ROOT, run_smoke


DEFAULT_LEDGER = ROOT / "validation" / "hermes-disposable-runtime" / "worker-ledger.json"
DEFAULT_OUT = ROOT / "validation" / "hermes-installed-runtime-smoke" / "worker-real-process-matrix-local-stub-smoke.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_ref(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return f"external:{path.name}"


def _load_workers(ledger_path: Path) -> list[str]:
    data = json.loads(ledger_path.read_text(encoding="utf-8"))
    raw = data.get("tasks")
    tasks = raw.values() if isinstance(raw, dict) else raw if isinstance(raw, list) else []
    workers = sorted(
        {
            str(task.get("worker_id") or "").strip()
            for task in tasks
            if isinstance(task, dict) and str(task.get("worker_id") or "").strip()
        }
    )
    return workers


def run_matrix(
    *,
    hermes_checkout: Path,
    hermes_home: Path,
    ledger_path: Path,
    workers: list[str] | None = None,
    model: str = DEFAULT_MODEL,
    timeout_seconds: int = 60,
    allow_non_disposable: bool = False,
) -> dict[str, Any]:
    selected_workers = workers or _load_workers(ledger_path)
    worker_results: list[dict[str, Any]] = []

    for worker_id in selected_workers:
        receipt = run_smoke(
            hermes_checkout=hermes_checkout,
            hermes_home=hermes_home,
            worker_id=worker_id,
            model=model,
            timeout_seconds=timeout_seconds,
            allow_non_disposable=allow_non_disposable,
        )
        evidence = receipt.get("disposable_task_evidence") or {}
        worker_results.append(
            {
                "worker_id": worker_id,
                "result": receipt.get("result"),
                "record_type": evidence.get("record_type"),
                "final_child_status": evidence.get("final_child_status"),
                "checks": receipt.get("checks"),
                "worker_result_files": evidence.get("worker_result_files", []),
            }
        )

    passed_workers = [item for item in worker_results if item.get("result") == "PASS"]
    failed_workers = [item for item in worker_results if item.get("result") != "PASS"]
    passed = not failed_workers and len(passed_workers) == len(selected_workers)

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
            "card_id": "VFINAL-HERMES-WORKER-REAL-PROCESS-MATRIX-LOCAL-STUB-SMOKE",
            "slice_id": "VFINAL_HERMES_WORKER_REAL_PROCESS_MATRIX_LOCAL_STUB",
            "phase": "F13",
            "risk_effective": "R3",
            "surfaces": ["hermes", "kanban", "adapter", "vfinal", "worker-routing", "worker-results"],
            "executor_identity": "remote-proof-runner",
            "reviewer_identity": "independent-reviewer",
        },
        "result": "PASS" if passed else "FAIL",
        "blocking_findings": not passed,
        "findings_summary": (
            f"Disposable installed Hermes matrix smoke passed for {len(passed_workers)}/{len(selected_workers)} workers through real child process local-stub completion."
            if passed
            else f"Disposable installed Hermes matrix smoke failed for {len(failed_workers)}/{len(selected_workers)} workers."
        ),
        "tool_or_profile": "Hermes disposable installed runtime; real dispatcher spawn matrix; local OpenAI-compatible tool-call stub",
        "executed_by": "remote-proof-runner",
        "runtime_scope": (
            "Disposable installed Hermes checkout and isolated HERMES_HOME/HOME; "
            "no production board, secrets, deploy, external model endpoint or real Hermes runtime mutation."
        ),
        "worker_count": len(selected_workers),
        "passed_worker_count": len(passed_workers),
        "failed_worker_count": len(failed_workers),
        "failed_workers": [item.get("worker_id") for item in failed_workers],
        "worker_results": worker_results,
        "important_limitations": [
            "This proves broad real Hermes child-process/tool-loop parity against a deterministic local stub.",
            "It does not prove non-stub model quality, real tool authentication, cloud access, repository mutation, deployment, rollback or production readiness.",
            "This does not authorize updating a real Hermes runtime.",
        ],
        "evidence_refs": [
            repo_ref(ledger_path),
            "validation/hermes-installed-runtime-smoke/worker-real-process-matrix-local-stub-smoke.json",
            "validation/hermes-installed-runtime-smoke/worker-real-process-local-stub-smoke.json",
            "validation/hermes-installed-runtime-smoke/worker-profile-readiness-local-stub-smoke.json",
        ],
        "next_action": (
            "Run a bounded non-stub model/tool-auth worker proof and then a receipt-backed production service-manager rollback/monitoring drill before production update."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hermes-checkout", type=Path, required=True)
    parser.add_argument("--hermes-home", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--worker", action="append", dest="workers")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--allow-non-disposable", action="store_true")
    args = parser.parse_args(argv)

    workers = args.workers
    if workers is None and args.limit and args.limit > 0:
        workers = _load_workers(args.ledger.expanduser().resolve())[: args.limit]

    receipt = run_matrix(
        hermes_checkout=args.hermes_checkout.expanduser().resolve(),
        hermes_home=args.hermes_home.expanduser().resolve(),
        ledger_path=args.ledger.expanduser().resolve(),
        workers=workers,
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
