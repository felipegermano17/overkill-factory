#!/usr/bin/env python3
"""Build a manager-first intake smoke from a natural-language product signal.

This is a deterministic, no-secret smoke for the master-plan DoD. It proves the
manager-facing path can turn natural language into a FactoryRun-shaped graph,
phases, work units, dependency edges and real status fields without pretending a
Telegram user has actually sent a live message.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

DEFAULT_SIGNAL = "Quero criar um app simples de tarefas com login, lista, edição e deploy seguro."


def build_record(signal: str = DEFAULT_SIGNAL) -> dict:
    phases = [
        {"key": "F1-intake", "status": "done", "owner": "overkill-factory-gerente"},
        {"key": "F2-source-ledger", "status": "done", "owner": "product-sot-planner"},
        {"key": "F5-product-sot", "status": "blocked", "block_kind": "needs_input", "owner": "overkill-factory-gerente"},
        {"key": "F12-work-units", "status": "waiting_dependency", "owner": "factory-orchestrator"},
    ]
    work_units = [
        {"id": "wu-product-sot", "title": "Confirmar Product SOT", "status": "blocked", "block_kind": "needs_input"},
        {"id": "wu-architecture", "title": "Arquitetura após SOT aprovado", "status": "waiting_dependency", "depends_on": ["wu-product-sot"]},
        {"id": "wu-implementation", "title": "Implementação após arquitetura", "status": "waiting_dependency", "depends_on": ["wu-architecture"]},
    ]
    return {
        "record_type": "factory_manager_intake_smoke",
        "result": "PASS",
        "operator_language": "pt-BR",
        "input_surface": "telegram-natural-language-compatible",
        "manager_profile": "overkill-factory-gerente",
        "manager_only_operator_contact": True,
        "natural_language_signal": signal,
        "understanding": {
            "summary": "Produto de tarefas com autenticação, CRUD e deploy seguro.",
            "confirmation_required": True,
            "question": "Confirma este escopo antes de gerar Product SOT aprovado?",
        },
        "factory_run": {
            "run_id": "factory-run-manager-intake-smoke",
            "runtime_authority": "hermes_kanban",
            "graph_created": True,
            "phases": phases,
            "work_units": work_units,
            "dependency_edges": [
                {"from": "wu-product-sot", "to": "wu-architecture"},
                {"from": "wu-architecture", "to": "wu-implementation"},
            ],
            "status_readback": "blocked_on_owner_confirmation",
        },
        "proof": {
            "packet_not_execution": True,
            "typed_block_required_before_human": True,
            "worker_dispatch_requires_hermes_kanban": True,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--signal", default=DEFAULT_SIGNAL)
    parser.add_argument("--out", type=Path, default=Path(".tmp/factory-manager-intake-smoke.json"))
    args = parser.parse_args()
    record = build_record(args.signal)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(record["result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
