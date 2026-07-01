#!/usr/bin/env python3
"""Render a gerente/operator progress card from product gates, artifacts and readiness.

The progress percent is intentionally not a raw Kanban done/total count.  The
operator-facing card reports material product progress: weighted gates backed by
artifacts, readiness, critical-path blockers and uncertainty.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


READINESS_SCORES = {
    "complete": 1.0,
    "completed": 1.0,
    "approved": 1.0,
    "ready": 1.0,
    "usable": 1.0,
    "pass": 1.0,
    "partial": 0.5,
    "in_progress": 0.5,
    "draft": 0.5,
    "needs_review": 0.5,
    "blocked": 0.0,
    "not_started": 0.0,
    "missing": 0.0,
    "failed": 0.0,
    "fail": 0.0,
    "unknown": 0.0,
}


def _score(value: Any) -> float:
    return READINESS_SCORES.get(str(value or "unknown").strip().lower(), 0.0)


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _round_percent(value: float) -> int:
    return max(0, min(100, int(round(value))))


def _process_done_percent(process_counts: dict[str, Any]) -> int | None:
    done = process_counts.get("done")
    total = process_counts.get("total")
    if not isinstance(done, (int, float)) or not isinstance(total, (int, float)) or total <= 0:
        return None
    return _round_percent((float(done) / float(total)) * 100.0)


def _gate_score(gate: dict[str, Any]) -> tuple[float, float | None]:
    readiness_score = _score(gate.get("readiness"))
    artifacts = [item for item in _as_list(gate.get("artifacts")) if isinstance(item, dict)]
    if not artifacts:
        return readiness_score, None
    artifact_score = sum(_score(item.get("status")) for item in artifacts) / len(artifacts)
    # A gate is only as real as both its declared readiness and its artifacts.
    # This prevents a ready-looking gate with missing proof from counting as
    # product progress.
    return min(readiness_score, artifact_score), artifact_score


def _normalize_uncertainty(model: dict[str, Any], progress_percent: int, incomplete_weight: float, total_weight: float) -> dict[str, Any]:
    supplied = _as_dict(model.get("uncertainty"))
    confidence = supplied.get("confidence")
    if not isinstance(confidence, (int, float)):
        unresolved_ratio = incomplete_weight / total_weight if total_weight else 1.0
        confidence = max(0.2, min(0.95, 1.0 - (unresolved_ratio * 0.6)))
    range_percent = supplied.get("range_percent")
    if not (
        isinstance(range_percent, list)
        and len(range_percent) == 2
        and all(isinstance(item, (int, float)) for item in range_percent)
    ):
        spread = max(5, _round_percent((1.0 - float(confidence)) * 20))
        range_percent = [max(0, progress_percent - spread), min(100, progress_percent + spread)]
    unknowns = [str(item) for item in _as_list(supplied.get("unknowns"))]
    return {
        "confidence": round(float(confidence), 2),
        "range_percent": [int(range_percent[0]), int(range_percent[1])],
        "unknowns": unknowns,
    }


def build_card_from_model(model: dict[str, Any]) -> dict[str, Any]:
    """Build an operator progress card from weighted gates/artifacts/readiness."""
    gates = [item for item in _as_list(model.get("gates")) if isinstance(item, dict)]
    if not gates:
        raise ValueError("progress model requires at least one gate")

    gate_progress: dict[str, dict[str, Any]] = {}
    critical_path: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    weighted_complete = 0.0
    total_weight = 0.0
    incomplete_weight = 0.0

    for index, gate in enumerate(gates):
        gate_id = str(gate.get("id") or f"gate-{index + 1}")
        label = str(gate.get("label") or gate_id)
        weight_value = gate.get("weight", 1)
        weight = float(weight_value) if isinstance(weight_value, (int, float)) and weight_value > 0 else 1.0
        score, artifact_score = _gate_score(gate)
        percent = _round_percent(score * 100.0)
        total_weight += weight
        weighted_complete += score * weight
        if score < 1.0:
            incomplete_weight += weight

        gate_blockers = [item for item in _as_list(gate.get("blockers")) if isinstance(item, dict)]
        for blocker in gate_blockers:
            normalized = dict(blocker)
            normalized.setdefault("gate_id", gate_id)
            normalized.setdefault("gate_label", label)
            blockers.append(normalized)

        gate_progress[gate_id] = {
            "label": label,
            "weight": weight,
            "readiness": str(gate.get("readiness") or "unknown"),
            "artifact_percent": None if artifact_score is None else _round_percent(artifact_score * 100.0),
            "percent": percent,
            "gate_ref": gate.get("gate_ref"),
            "evidence_refs": [str(item) for item in _as_list(gate.get("evidence_refs"))],
            "artifacts": _as_list(gate.get("artifacts")),
            "blocked": bool(gate_blockers) or str(gate.get("readiness") or "").lower() == "blocked",
        }

        if score < 1.0 and (gate.get("critical") is True or not any(item.get("critical") is True for item in gates)):
            critical_path.append(
                {
                    "gate_id": gate_id,
                    "label": label,
                    "percent": percent,
                    "readiness": str(gate.get("readiness") or "unknown"),
                    "gate_ref": gate.get("gate_ref"),
                    "blocked": bool(gate_blockers) or str(gate.get("readiness") or "").lower() == "blocked",
                }
            )

    progress_percent = _round_percent((weighted_complete / total_weight) * 100.0) if total_weight else 0
    process_counts = _as_dict(model.get("process_counts"))
    process_done_percent = _process_done_percent(process_counts)
    uncertainty = _normalize_uncertainty(model, progress_percent, incomplete_weight, total_weight)
    next_critical_gate = critical_path[0]["gate_id"] if critical_path else None
    current_phase = critical_path[0]["label"] if critical_path else "Product gates complete"
    status = "blocked" if blockers else "running" if critical_path else "ready_for_next_gate"

    card = {
        "record_type": "operator_progress_card",
        "result": "PASS",
        "language": str(model.get("language") or "pt-BR"),
        "manager_profile": str(model.get("manager_profile") or "overkill-factory-gerente"),
        "kanban_dump_required": False,
        "progress_basis": "weighted_gates_artifacts_readiness",
        "progress_percent": progress_percent,
        "process_counts": process_counts,
        "process_done_percent": process_done_percent,
        "process_counts_used_for_product_percent": False,
        "current_phase": current_phase,
        "status": status,
        "next_critical_gate": next_critical_gate,
        "next_safe_action": str(model.get("next_safe_action") or _default_next_action(status)),
        "next_possible_gate": next_critical_gate or str(model.get("next_possible_gate") or "receipt-five"),
        "worker_visibility_policy": "workers never contact the operator directly",
        "gate_progress": gate_progress,
        "critical_path": critical_path,
        "blockers": blockers,
        "uncertainty": uncertainty,
    }
    card["human_text"] = render_model_text(card)
    return card


def _default_next_action(status: str) -> str:
    if status == "blocked":
        return "Gerente resolve ou encaminha o bloqueio do caminho crítico antes de contar progresso novo."
    if status == "ready_for_next_gate":
        return "Gerente prepara o próximo gate com evidências e incerteza residual."
    return "Gerente continua o caminho crítico e atualiza evidências de produto."


def build_card(percent: int = 42, phase: str = "F5 Product SOT", blocker: str = "aguardando confirmação do escopo") -> dict:
    return {
        "record_type": "operator_progress_card",
        "result": "PASS",
        "language": "pt-BR",
        "manager_profile": "overkill-factory-gerente",
        "kanban_dump_required": False,
        "progress_basis": "legacy_explicit_percent",
        "progress_percent": percent,
        "current_phase": phase,
        "status": "blocked_needs_input" if blocker else "running",
        "blocker": blocker,
        "next_safe_action": "Gerente envia pacote de entendimento e aguarda confirmação do operador.",
        "next_possible_gate": "owner_approved_product_sot",
        "worker_visibility_policy": "workers never contact the operator directly",
        "human_text": render_text(percent, phase, blocker),
    }


def render_model_text(card: dict[str, Any]) -> str:
    lines = [
        "Progresso da fábrica",
        f"Progresso de produto: {card['progress_percent']}%",
        "Base: gates ponderados por artefatos e prontidão; contagem bruta de tarefas não muda este percentual.",
    ]
    if card.get("process_done_percent") is not None:
        lines.append(f"Contagem operacional observada: {card['process_done_percent']}% (não usada como progresso de produto).")
    lines.append("")
    lines.append("Gates / artefatos / prontidão:")
    for gate in card.get("gate_progress", {}).values():
        artifact = gate.get("artifact_percent")
        artifact_text = "sem artefatos declarados" if artifact is None else f"artefatos {artifact}%"
        lines.append(f"- {gate['label']}: {gate['percent']}% ({gate['readiness']}, {artifact_text})")
    lines.append("")
    if card.get("critical_path"):
        path = " -> ".join(str(item["label"]) for item in card["critical_path"])
        lines.append(f"Caminho crítico: {path}")
    else:
        lines.append("Caminho crítico: nenhum gate crítico pendente")
    if card.get("blockers"):
        lines.append("Bloqueadores:")
        for blocker in card["blockers"]:
            lines.append(f"- {blocker.get('summary', blocker.get('id', 'bloqueio sem resumo'))}")
    else:
        lines.append("Bloqueadores: nenhum bloqueio real no momento")
    uncertainty = card.get("uncertainty", {})
    lines.append(
        "Incerteza: "
        f"confiança {uncertainty.get('confidence')}, intervalo {uncertainty.get('range_percent')}"
    )
    unknowns = uncertainty.get("unknowns") if isinstance(uncertainty, dict) else []
    if unknowns:
        lines.append("Desconhecidos:")
        for unknown in unknowns:
            lines.append(f"- {unknown}")
    lines.append(f"Próxima ação: {card['next_safe_action']}")
    return "\n".join(lines) + "\n"


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
    parser.add_argument("--model", type=Path, help="Progress model JSON with weighted gates/artifacts/readiness.")
    parser.add_argument("--percent", type=int, default=42)
    parser.add_argument("--phase", default="F5 Product SOT")
    parser.add_argument("--blocker", default="aguardando confirmação do escopo")
    parser.add_argument("--out", type=Path, default=Path(".tmp/operator-progress-card.json"))
    parser.add_argument("--text-out", type=Path, default=Path(".tmp/operator-progress-card.txt"))
    args = parser.parse_args()
    if args.model:
        card = build_card_from_model(json.loads(args.model.read_text(encoding="utf-8")))
    else:
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
