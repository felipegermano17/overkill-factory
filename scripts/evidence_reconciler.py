#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import factoryctl  # noqa: E402


def parse_timestamp(value: Any) -> datetime:
    if not isinstance(value, str) or not value.strip():
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def evidence_root_for(path: Path) -> Path:
    parent = path.parent
    if parent.name == "reports" and ((parent.parent / "cards").exists() or (parent.parent / "sources").exists()):
        return parent.parent
    return ROOT


def result_entry(card: dict[str, Any], path: Path, data: dict[str, Any]) -> dict[str, Any]:
    normalized = factoryctl.normalize_worker_result_record(data, card=card)
    record_type = str(normalized.get("record_type") or "").strip()
    worker_ref = normalized.get("worker") if isinstance(normalized.get("worker"), dict) else {}
    expected_worker_id = factoryctl._worker_id_for_output_field(record_type)
    validation_errors = factoryctl.validate_worker_result_record(
        normalized,
        expected_field=record_type or None,
        expected_worker_id=expected_worker_id,
        card=card,
        evidence_root=evidence_root_for(path),
    )
    return {
        "record_type": record_type,
        "worker_id": worker_ref.get("id"),
        "result": normalized.get("result") or normalized.get("decision"),
        "blocking_findings": normalized.get("blocking_findings"),
        "created_at": normalized.get("created_at") or normalized.get("decision_at"),
        "evidence_ref": factoryctl.source_card_ref(path),
        "valid_for_closure": not validation_errors,
        "validation_errors": validation_errors,
        "normalized_from_worker_envelope": bool(normalized.get("normalized_from_worker_envelope")),
    }


def add_result_path(
    grouped: dict[str, list[dict[str, Any]]],
    card: dict[str, Any],
    path: Path,
) -> None:
    try:
        data = factoryctl.load_json_like(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return
    if not isinstance(data, dict):
        return
    normalized = factoryctl.normalize_worker_result_record(data, card=card)
    record_type = str(normalized.get("record_type") or "").strip()
    if not record_type:
        return
    grouped.setdefault(record_type, []).append(result_entry(card, path, normalized))


def load_worker_results(
    card: dict[str, Any],
    results_dir: Path,
    extra_results: list[Path] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    if results_dir.exists():
        for path in sorted(results_dir.glob("*.json")):
            add_result_path(grouped, card, path)
    for path in extra_results or []:
        add_result_path(grouped, card, path)
    return grouped


def sort_result_entries(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        entries,
        key=lambda item: (
            parse_timestamp(item.get("created_at")),
            str(item.get("evidence_ref") or ""),
        ),
        reverse=True,
    )


def required_receipt_fields(card: dict[str, Any]) -> list[str]:
    fields: list[str] = []
    for worker_id in factoryctl.required_worker_ids(card):
        if worker_id == "evidence-reconciler":
            continue
        if factoryctl.worker_queue_class(worker_id, card) != "blocking-before-done":
            continue
        fields.append(factoryctl.WORKERS[worker_id].output_field)
    return sorted(set(fields))


def reconcile(
    card: dict[str, Any],
    results_dir: Path,
    extra_results: list[Path] | None = None,
) -> dict[str, Any]:
    grouped = load_worker_results(card, results_dir, extra_results)
    effective_results: dict[str, dict[str, Any]] = {}
    superseded_results: list[dict[str, Any]] = []

    for record_type, entries in grouped.items():
        ordered = sort_result_entries(entries)
        if not ordered:
            continue
        effective_results[record_type] = ordered[0]
        for superseded in ordered[1:]:
            superseded_results.append(
                {
                    **superseded,
                    "superseded_by": ordered[0]["evidence_ref"],
                    "supersession_reason": "newer result for same receipt field",
                }
            )

    required_fields = required_receipt_fields(card)
    missing_required_fields = [
        field for field in required_fields if field not in effective_results
    ]
    blocking_current_results: list[dict[str, Any]] = []
    for field in required_fields:
        current = effective_results.get(field)
        if not current:
            continue
        if not current.get("valid_for_closure"):
            blocking_current_results.append(current)

    receipt_five_ready = not missing_required_fields and not blocking_current_results
    return {
        "record_type": "receipt_five_reconciliation_index",
        "created_at": factoryctl.utc_now(),
        "card_ref": factoryctl.card_ref(card),
        "results_dir": factoryctl.source_card_ref(results_dir),
        "extra_results": [
            factoryctl.source_card_ref(path) for path in extra_results or []
        ],
        "required_receipt_fields": required_fields,
        "effective_results": effective_results,
        "superseded_results": sorted(
            superseded_results,
            key=lambda item: (
                str(item.get("record_type") or ""),
                str(item.get("created_at") or ""),
                str(item.get("evidence_ref") or ""),
            ),
        ),
        "missing_required_fields": missing_required_fields,
        "blocking_current_results": blocking_current_results,
        "receipt_five_ready": receipt_five_ready,
    }


def build_reconciler_result(card: dict[str, Any], index_ref: str, index: dict[str, Any]) -> dict[str, Any]:
    blockers = []
    if index["missing_required_fields"]:
        blockers.append("missing required fields: " + ", ".join(index["missing_required_fields"]))
    if index["blocking_current_results"]:
        blockers.append(
            "blocking current results: "
            + ", ".join(
                sorted(
                    str(item.get("record_type") or "unknown")
                    for item in index["blocking_current_results"]
                )
            )
        )
    ready = bool(index["receipt_five_ready"])
    payload = factoryctl.build_worker_result(
        "evidence-reconciler",
        card,
        result="PASS" if ready else "FAIL",
        tool_or_profile="scripts/evidence_reconciler.py",
        executed_by="evidence-reconciler",
        evidence_refs=[index_ref],
        blocking_findings=not ready,
        findings_summary="Receipt Five evidence is reconciled and ready." if ready else "; ".join(blockers),
        next_action="prepare Receipt Five closure" if ready else "rerun or supply the missing/blocking worker evidence",
    )
    payload.update(
        {
            "receipt_five_ready": ready,
            "required_receipt_fields": index["required_receipt_fields"],
            "missing_required_fields": index["missing_required_fields"],
            "blocking_current_result_fields": [
                item.get("record_type") for item in index["blocking_current_results"]
            ],
            "superseded_result_count": len(index["superseded_results"]),
        }
    )
    return payload


def build_receipt_draft(
    card: dict[str, Any],
    index_ref: str,
    result_ref: str,
    index: dict[str, Any],
    *,
    from_status: str,
    to_status: str,
) -> dict[str, Any]:
    verification_result = "PASS" if index["receipt_five_ready"] else "BLOCKED"
    artifact_paths = sorted(
        {
            index_ref,
            result_ref,
            *[
                str(item.get("evidence_ref"))
                for item in index["effective_results"].values()
                if item.get("evidence_ref")
            ],
        }
    )
    return {
        "receipt_five": {
            "changed": card.get("done_definition") or "Reconciled worker evidence for done promotion.",
            "artifact_paths": artifact_paths,
            "verification_commands": [
                "python scripts/evidence_reconciler.py --card <card> --worker-results-dir <worker-results-dir>"
            ],
            "verification_result": verification_result,
            "reviewer_required": True,
            "reviewer_result": "PASS" if index["receipt_five_ready"] else "BLOCKED",
            "next_action": "promote to done" if index["receipt_five_ready"] else "rerun or repair blocking worker evidence",
            "known_limits": index["missing_required_fields"]
            + [
                str(item.get("record_type") or "unknown")
                for item in index["blocking_current_results"]
            ],
            "agent_notes": "Generated by evidence-reconciler before done promotion.",
        },
        "receipt_five_reconciliation_result": {
            "evidence_ref": result_ref,
            "result": "PASS" if index["receipt_five_ready"] else "FAIL",
            "valid": bool(index["receipt_five_ready"]),
        },
        "worker_result_index": index_ref,
        "kanban_transition_event": {
            "from_status": from_status,
            "to_status": to_status if index["receipt_five_ready"] else "blocked",
            "actor": "evidence-reconciler",
            "worker": "evidence-reconciler",
            "receipt_refs": [
                "receipt_five",
                "receipt_five_reconciliation_result",
                "worker_result_index",
            ],
            "artifact_refs": artifact_paths,
            "allowed": bool(index["receipt_five_ready"]),
            "reason": "Receipt Five ready" if index["receipt_five_ready"] else "Receipt Five blocked by evidence reconciliation",
        },
    }


def command_reconcile(args: argparse.Namespace) -> int:
    card = factoryctl.load_json_like(args.card)
    if not isinstance(card, dict):
        raise SystemExit("card must be a JSON-like object")
    index = reconcile(card, args.worker_results_dir, args.extra_result)
    write_json(args.out_index, index)

    index_ref = factoryctl.source_card_ref(args.out_index)
    result = build_reconciler_result(card, index_ref, index)
    write_json(args.out_result, result)

    if args.out_receipt_draft:
        receipt = build_receipt_draft(
            card,
            index_ref,
            factoryctl.source_card_ref(args.out_result),
            index,
            from_status=args.from_status,
            to_status=args.to_status,
        )
        write_json(args.out_receipt_draft, receipt)

    print(
        json.dumps(
            {
                "receipt_five_ready": index["receipt_five_ready"],
                "missing_required_fields": index["missing_required_fields"],
                "blocking_current_result_fields": [
                    item.get("record_type") for item in index["blocking_current_results"]
                ],
                "superseded_result_count": len(index["superseded_results"]),
                "index_ref": index_ref,
                "result_ref": factoryctl.source_card_ref(args.out_result),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if index["receipt_five_ready"] else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Reconcile worker evidence before Receipt Five closure.")
    parser.add_argument("--card", type=Path, required=True)
    parser.add_argument("--worker-results-dir", type=Path, required=True)
    parser.add_argument("--extra-result", type=Path, action="append", default=[])
    parser.add_argument("--out-index", type=Path, required=True)
    parser.add_argument("--out-result", type=Path, required=True)
    parser.add_argument("--out-receipt-draft", type=Path)
    parser.add_argument("--from-status", default="ready")
    parser.add_argument("--to-status", default="done")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return command_reconcile(args)


if __name__ == "__main__":
    raise SystemExit(main())
