#!/usr/bin/env python3
"""Build and validate worker accountability routing ledgers.

This module turns repeated bad output, failures, rework, and shallow artifacts
into deterministic routing consequences. It does not mutate Hermes Kanban. The
ledger is a public-safe reducer input/output: Hermes remains the runtime
authority, while the factory reducer can consume the consequence to route the
next worker task to normal, review, demoted, or escalated handling.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

RAW_KANBAN_TASK_RE = re.compile(r"\bt_[0-9a-f]{6,}\b", re.IGNORECASE)
PRIVATE_REF_RE = re.compile(
    r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|token|secret|webhook|guild[_-]?id|channel[_-]?id|message[_-]?id)",
    re.IGNORECASE,
)

NEGATIVE_EVENT_TYPES = {
    "bad_output",
    "failure",
    "failed_run",
    "rework_required",
    "shallow_artifact",
    "review_fail",
    "repair_loop",
}
POSITIVE_EVENT_TYPES = {"positive_review", "repair_pass", "quality_pass"}
EVENT_TYPES = NEGATIVE_EVENT_TYPES | POSITIVE_EVENT_TYPES
COUNT_FIELDS = {
    "bad_output": "bad_output_count",
    "failure": "failure_count",
    "failed_run": "failure_count",
    "rework_required": "rework_count",
    "shallow_artifact": "shallow_artifact_count",
    "review_fail": "review_fail_count",
    "repair_loop": "repair_loop_count",
}
CONSEQUENCE_ORDER = {
    "normal_route": 0,
    "watch": 1,
    "mandatory_independent_review": 2,
    "demote_to_review_queue": 3,
    "escalate_for_profile_review": 4,
}


@dataclass
class WorkerCounters:
    worker_id: str
    bad_output_count: int = 0
    failure_count: int = 0
    rework_count: int = 0
    shallow_artifact_count: int = 0
    review_fail_count: int = 0
    repair_loop_count: int = 0
    positive_signal_count: int = 0
    event_refs: list[str] = field(default_factory=list)

    @property
    def negative_total(self) -> int:
        return (
            self.bad_output_count
            + self.failure_count
            + self.rework_count
            + self.shallow_artifact_count
            + self.review_fail_count
            + self.repair_loop_count
        )


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if value is None:
        return []
    return [value]


def _clean_string(value: Any) -> str:
    return str(value or "").strip()


def _safe_ref(ref: Any) -> bool:
    value = _clean_string(ref)
    if not value:
        return False
    if RAW_KANBAN_TASK_RE.search(value) or PRIVATE_REF_RE.search(value):
        return False
    if value.startswith(("http://", "https://", "file://")):
        return False
    return True


def event_validation_errors(events: Iterable[Mapping[str, Any]]) -> list[str]:
    errors: list[str] = []
    for index, event in enumerate(events):
        worker_id = _clean_string(event.get("worker_id"))
        event_type = _clean_string(event.get("event_type"))
        if not worker_id:
            errors.append(f"events[{index}].worker_id is required")
        if event_type not in EVENT_TYPES:
            errors.append(f"events[{index}].event_type must be one of {sorted(EVENT_TYPES)}")
        refs = _list(event.get("evidence_refs") or event.get("event_ref"))
        if not refs:
            errors.append(f"events[{index}].evidence_refs is required")
        for ref_index, ref in enumerate(refs):
            if not _safe_ref(ref):
                errors.append(f"events[{index}].evidence_refs[{ref_index}] must be a public-safe sanitized ref")
    return errors


def aggregate_worker_events(events: Iterable[Mapping[str, Any]]) -> dict[str, WorkerCounters]:
    workers: dict[str, WorkerCounters] = {}
    for event in events:
        worker_id = _clean_string(event.get("worker_id"))
        event_type = _clean_string(event.get("event_type"))
        if not worker_id or event_type not in EVENT_TYPES:
            continue
        counters = workers.setdefault(worker_id, WorkerCounters(worker_id=worker_id))
        for ref in _list(event.get("evidence_refs") or event.get("event_ref")):
            ref_text = _clean_string(ref)
            if ref_text and ref_text not in counters.event_refs:
                counters.event_refs.append(ref_text)
        if event_type in POSITIVE_EVENT_TYPES:
            counters.positive_signal_count += 1
            continue
        count_field = COUNT_FIELDS[event_type]
        setattr(counters, count_field, getattr(counters, count_field) + 1)
    return workers


def consequence_for_counters(counters: WorkerCounters) -> dict[str, Any]:
    reasons: list[str] = []
    action = "normal_route"
    accountability_state = "healthy"
    queue_class = "normal"
    allowed_actions = ["dispatch_normally"]
    required_reviewer = None

    if counters.negative_total >= 1:
        action = "watch"
        accountability_state = "watch"
        queue_class = "normal_with_accountability_watch"
        allowed_actions = ["dispatch_normally", "attach_accountability_context"]
        reasons.append("negative accountability signal recorded")

    if counters.rework_count >= 2 or counters.shallow_artifact_count >= 2 or counters.review_fail_count >= 1:
        action = "mandatory_independent_review"
        accountability_state = "review_required"
        queue_class = "review-before-consumption"
        allowed_actions = ["route_output_to_independent_review", "block_downstream_consumption_until_review_pass"]
        required_reviewer = "independent-reviewer"
        reasons.append("repeated rework/shallow output or review failure requires independent review")

    if counters.bad_output_count >= 2 or counters.failure_count >= 2 or counters.repair_loop_count >= 2:
        action = "demote_to_review_queue"
        accountability_state = "demoted"
        queue_class = "demoted-review-queue"
        allowed_actions = ["route_output_to_independent_review", "prefer_alternate_worker_when_available"]
        required_reviewer = "independent-reviewer"
        reasons.append("repeated bad output/failures/repair loops demote worker routing")

    if counters.negative_total >= 5 or (
        counters.bad_output_count >= 3
        or counters.failure_count >= 3
        or counters.shallow_artifact_count >= 3
        or counters.rework_count >= 3
    ):
        action = "escalate_for_profile_review"
        accountability_state = "escalated"
        queue_class = "blocked-profile-review"
        allowed_actions = ["block_new_sensitive_assignments", "open_profile_eval_review", "prefer_alternate_worker_when_available"]
        required_reviewer = "skill-eval-distiller"
        reasons.append("high repeated negative count requires profile eval review before further sensitive routing")

    if not reasons:
        reasons.append("no repeated negative accountability pattern")

    return {
        "action": action,
        "accountability_state": accountability_state,
        "queue_class": queue_class,
        "required_reviewer": required_reviewer,
        "allowed_actions": allowed_actions,
        "reason": "; ".join(reasons),
    }


def merge_consequences(worker_rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    strongest = "normal_route"
    affected_workers: list[str] = []
    for row in worker_rows:
        consequence = row.get("routing_consequence") if isinstance(row.get("routing_consequence"), Mapping) else {}
        action = _clean_string(consequence.get("action")) or "normal_route"
        if CONSEQUENCE_ORDER.get(action, -1) > CONSEQUENCE_ORDER.get(strongest, -1):
            strongest = action
        if action != "normal_route":
            affected_workers.append(_clean_string(row.get("worker_id")))
    return {
        "strongest_action": strongest,
        "affected_workers": [worker for worker in affected_workers if worker],
        "routing_authority": "factory_reducer_consumes_this_ledger_hermes_kanban_executes_state",
    }


def build_accountability_ledger(
    events: Iterable[Mapping[str, Any]],
    *,
    generated_at: str | None = None,
    source_refs: list[str] | None = None,
) -> dict[str, Any]:
    event_list = [dict(event) for event in events]
    workers = aggregate_worker_events(event_list)
    worker_rows: dict[str, Any] = {}
    for worker_id, counters in sorted(workers.items()):
        consequence = consequence_for_counters(counters)
        worker_rows[worker_id] = {
            "worker_id": worker_id,
            "bad_output_count": counters.bad_output_count,
            "failure_count": counters.failure_count,
            "rework_count": counters.rework_count,
            "shallow_artifact_count": counters.shallow_artifact_count,
            "review_fail_count": counters.review_fail_count,
            "repair_loop_count": counters.repair_loop_count,
            "positive_signal_count": counters.positive_signal_count,
            "negative_total": counters.negative_total,
            "event_refs": counters.event_refs,
            "routing_consequence": consequence,
        }

    return {
        "$schema": "https://overkill-factory.dev/schemas/worker-accountability-ledger.schema.json",
        "record_type": "worker_accountability_ledger",
        "ledger_version": "factory-15-p13-worker-accountability-v1",
        "generated_at": generated_at or utc_now(),
        "scope": "public-safe-routing-consequence-ledger",
        "runtime_authority": "hermes_kanban",
        "local_state_authority": False,
        "routing_authority": "factory_reducer",
        "source_refs": source_refs or ["issues/595#point-13-worker-accountability"],
        "consequence_policy": {
            "watch_after_negative_events": 1,
            "mandatory_review_after_rework_or_shallow_events": 2,
            "demote_after_bad_output_failure_or_repair_loop_events": 2,
            "escalate_after_total_negative_events": 5,
            "positive_events_do_not_erase_negative_accountability_without_review": True,
        },
        "worker_accountability": worker_rows,
        "routing_summary": merge_consequences(worker_rows.values()),
        "limits": [
            "Ledger refs must be public-safe sanitized refs, not raw Hermes task ids or private paths.",
            "The ledger recommends routing consequences only; Hermes Kanban remains runtime state authority.",
            "Demotion or escalation does not approve, reject, or waive a human/product/security gate.",
        ],
    }


def validate_ledger(ledger: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if ledger.get("record_type") != "worker_accountability_ledger":
        errors.append("record_type must be worker_accountability_ledger")
    if ledger.get("runtime_authority") != "hermes_kanban":
        errors.append("runtime_authority must be hermes_kanban")
    if ledger.get("local_state_authority") is not False:
        errors.append("local_state_authority must be false")
    if ledger.get("routing_authority") != "factory_reducer":
        errors.append("routing_authority must be factory_reducer")
    for ref_index, ref in enumerate(_list(ledger.get("source_refs"))):
        if not _safe_ref(ref):
            errors.append(f"source_refs[{ref_index}] must be public-safe")
    workers = ledger.get("worker_accountability")
    if not isinstance(workers, Mapping) or not workers:
        errors.append("worker_accountability must contain at least one worker row")
        return errors
    for worker_id, row in workers.items():
        if not isinstance(row, Mapping):
            errors.append(f"worker_accountability.{worker_id} must be an object")
            continue
        if row.get("worker_id") != worker_id:
            errors.append(f"worker_accountability.{worker_id}.worker_id must match row key")
        for field_name in (
            "bad_output_count",
            "failure_count",
            "rework_count",
            "shallow_artifact_count",
            "review_fail_count",
            "repair_loop_count",
            "negative_total",
        ):
            value = row.get(field_name)
            if not isinstance(value, int) or value < 0:
                errors.append(f"worker_accountability.{worker_id}.{field_name} must be a non-negative integer")
        for ref_index, ref in enumerate(_list(row.get("event_refs"))):
            if not _safe_ref(ref):
                errors.append(f"worker_accountability.{worker_id}.event_refs[{ref_index}] must be public-safe")
        consequence = row.get("routing_consequence") if isinstance(row.get("routing_consequence"), Mapping) else {}
        action = consequence.get("action")
        if action not in CONSEQUENCE_ORDER:
            errors.append(f"worker_accountability.{worker_id}.routing_consequence.action is invalid")
        if action in {"mandatory_independent_review", "demote_to_review_queue", "escalate_for_profile_review"}:
            if not consequence.get("required_reviewer"):
                errors.append(f"worker_accountability.{worker_id}.routing_consequence.required_reviewer is required for {action}")
    return errors


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/validate worker accountability ledger routing consequences.")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build", help="Build a ledger from a JSON event list or object with events[]")
    build.add_argument("events", type=Path)
    build.add_argument("--out", type=Path)
    build.add_argument("--source-ref", action="append", dest="source_refs")
    validate = sub.add_parser("validate", help="Validate an existing worker accountability ledger")
    validate.add_argument("ledger", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "build":
        payload = load_json(args.events)
        events = payload.get("events") if isinstance(payload, Mapping) else payload
        if not isinstance(events, list):
            print("events input must be a list or object with events[]", file=sys.stderr)
            return 2
        event_errors = event_validation_errors(events)
        if event_errors:
            print(json.dumps({"result": "BLOCKED", "errors": event_errors}, indent=2), file=sys.stderr)
            return 1
        ledger = build_accountability_ledger(events, source_refs=args.source_refs)
        errors = validate_ledger(ledger)
        if errors:
            print(json.dumps({"result": "BLOCKED", "errors": errors}, indent=2), file=sys.stderr)
            return 1
        text = json.dumps(ledger, indent=2, ensure_ascii=False) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
        return 0
    if args.command == "validate":
        ledger = load_json(args.ledger)
        if not isinstance(ledger, Mapping):
            print(json.dumps({"result": "BLOCKED", "errors": ["ledger must be a JSON object"]}, indent=2), file=sys.stderr)
            return 1
        errors = validate_ledger(ledger)
        result = "PASS" if not errors else "BLOCKED"
        print(json.dumps({"result": result, "errors": errors}, indent=2))
        return 0 if not errors else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
