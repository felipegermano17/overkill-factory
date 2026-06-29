#!/usr/bin/env python3
"""Render an operator progress card so users do not need to inspect Kanban."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_card(percent: int = 42, phase: str = "F5 Product SOT", blocker: str = "aguardando confirmação do escopo") -> dict:
    return {
        "record_type": "operator_progress_card",
        "result": "PASS",
        "language": "pt-BR",
        "manager_profile": "overkill-factory-gerente",
        "kanban_dump_required": False,
        "progress_percent": percent,
        "current_phase": phase,
        "status": "blocked_needs_input" if blocker else "running",
        "blocker": blocker,
        "next_safe_action": "Gerente envia pacote de entendimento e aguarda confirmação do operador.",
        "next_possible_gate": "owner_approved_product_sot",
        "worker_visibility_policy": "workers never contact the operator directly",
        "human_text": render_text(percent, phase, blocker),
    }


def render_text(percent: int, phase: str, blocker: str) -> str:
    blocker_text = blocker or "nenhum bloqueio real no momento"
    return (
        "Progresso da fábrica\n"
        f"Progresso: {percent}%\n"
        f"Fase atual: {phase}\n"
        f"Bloqueador: {blocker_text}\n"
        "Próxima ação: Gerente envia o pacote certo; o operador não precisa abrir Kanban.\n"
        "Próximo gate possível: owner-approved Product SOT\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--percent", type=int, default=42)
    parser.add_argument("--phase", default="F5 Product SOT")
    parser.add_argument("--blocker", default="aguardando confirmação do escopo")
    parser.add_argument("--out", type=Path, default=Path(".tmp/operator-progress-card.json"))
    parser.add_argument("--text-out", type=Path, default=Path(".tmp/operator-progress-card.txt"))
    args = parser.parse_args()
    card = build_card(args.percent, args.phase, args.blocker)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.text_out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(card, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.text_out.write_text(card["human_text"], encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.text_out}")
    print(card["result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
