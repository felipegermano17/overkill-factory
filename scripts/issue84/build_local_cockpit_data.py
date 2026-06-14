#!/usr/bin/env python3
"""Build public-safe local cockpit data for Issue #84.

The output is a read-only UI data bundle derived from checked-in
StatusSnapshot v0 fixtures and the reviewed adapter/report projections.  It may
also consume a Product Face packet/review file, but only exports a sanitized
summary; raw private/task refs are never copied into the browser payload.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
FIXTURE_DIR = ROOT / "fixtures" / "issue-84" / "status-snapshot-v0"
DEFAULT_OUTPUT = ROOT / "ui" / "issue-84-local-cockpit" / "data" / "status-cockpit.json"

ADAPTER_MODULE_PATH = SCRIPT_DIR / "status_snapshot_readonly_adapter.py"

REQUIRED_PACKET_STATES = [
    "loading_snapshot",
    "empty_no_snapshots",
    "success_current_snapshot",
    "input_error_or_parse_failure",
    "blocked_gate",
    "stale_snapshot",
    "contradictory_state",
    "private_evidence_unavailable",
    "review_pending_failed_passed",
    "long_dense_data",
]

STATE_REGISTRY = [
    {
        "id": "loading_snapshot",
        "label": "Loading snapshot",
        "operator_meaning": "A local snapshot source is being read; no success metrics or approvals are inferred.",
        "matches_current_states": ["loading"],
        "demo_query": "?demo=loading",
    },
    {
        "id": "empty_no_snapshots",
        "label": "Empty / no snapshots",
        "operator_meaning": "No canonical local snapshot is available; next action remains blocked/review.",
        "matches_current_states": ["empty"],
        "demo_query": "?demo=empty",
    },
    {
        "id": "success_current_snapshot",
        "label": "Current success projection",
        "operator_meaning": "A reviewed local projection is current; still separate from release and issue-completion approval.",
        "matches_current_states": ["success"],
        "demo_query": "?state=success_current_snapshot",
    },
    {
        "id": "input_error_or_parse_failure",
        "label": "Input error / parse failure",
        "operator_meaning": "The source could not be parsed or validated; the UI refuses to infer approvals from bad input.",
        "matches_current_states": ["error"],
        "demo_query": "?demo=error",
    },
    {
        "id": "blocked_gate",
        "label": "Blocked gate",
        "operator_meaning": "A gate/reviewer/human/security dependency is blocking progress with an explicit unblock condition.",
        "matches_current_states": ["blocked", "missing-gate", "missing", "manual_estimate", "security_negative"],
        "demo_query": "?state=blocked_gate",
    },
    {
        "id": "stale_snapshot",
        "label": "Stale snapshot",
        "operator_meaning": "Observed data is older than the source or explicitly stale; next safe action is refresh/review.",
        "matches_current_states": ["stale"],
        "demo_query": "?state=stale_snapshot",
    },
    {
        "id": "contradictory_state",
        "label": "Contradictory state",
        "operator_meaning": "Conflicting sources are shown side-by-side and are not collapsed into done/released.",
        "matches_current_states": ["contradictory"],
        "demo_query": "?state=contradictory_state",
    },
    {
        "id": "private_evidence_unavailable",
        "label": "Private evidence unavailable",
        "operator_meaning": "Evidence is known only as redacted/unavailable metadata; raw private payloads are never displayed.",
        "matches_current_states": ["private_unavailable"],
        "demo_query": "?state=private_evidence_unavailable",
    },
    {
        "id": "review_pending_failed_passed",
        "label": "Review pending/failed/passed lane",
        "operator_meaning": "Worker done, reviewer result, human approval and release state are separate lanes.",
        "matches_review_states": ["missing", "pending", "failed", "passed", "blocked"],
        "demo_query": "?lane=review",
    },
    {
        "id": "long_dense_data",
        "label": "Long dense data",
        "operator_meaning": "Long gate/evidence/worker lists stay segmented and searchable without decorative KPIs.",
        "matches_density": "many cards, gates, blockers or evidence refs",
        "demo_query": "?density=long",
    },
]

CURRENT_TO_UI = {
    "success": "success_current_snapshot",
    "empty": "empty_no_snapshots",
    "loading": "loading_snapshot",
    "error": "input_error_or_parse_failure",
    "blocked": "blocked_gate",
    "missing": "blocked_gate",
    "missing-gate": "blocked_gate",
    "manual_estimate": "blocked_gate",
    "security_negative": "blocked_gate",
    "stale": "stale_snapshot",
    "contradictory": "contradictory_state",
    "private_unavailable": "private_evidence_unavailable",
    "superseded": "blocked_gate",
}

FORBIDDEN_ACTIONS = [
    "gate_approval",
    "product_face_result_self_acceptance",
    "runtime_mutation",
    "card_state_mutation",
    "mutation_endpoint",
    "release",
    "deployment",
    "public_promotion",
    "external_mutation",
    "github_push_or_pr",
    "secret_access",
    "discord_runtime_use",
    "raw_private_evidence_publication",
    "public_server_binding",
    "issue_completion_approval",
]

_PRIVATE_RUNTIME_ROOT = "/" + "srv" + "/" + "hermes"
_PRIVATE_PRODUCT_MARKERS = ["K" + "AXIS", "K" + "axis", "k" + "axis"]
_PRIVATE_OWNER_MARKERS = ["Fel" + "ipe", "fel" + "ipe"]
_PRIVATE_WINDOWS_SINGLE = "C:" + "\\" + "Users"
_PRIVATE_WINDOWS_DOUBLE = "C:" + "\\\\" + "Users"

PRIVATE_PATTERNS = [
    re.compile(re.escape(_PRIVATE_RUNTIME_ROOT) + r"[^\s\"']*"),
    re.compile(r"file://[^\s\"']*"),
    re.compile(r"\bt_[a-f0-9]{8}\b"),
    *[re.compile(r"\b" + re.escape(marker) + r"\b") for marker in _PRIVATE_PRODUCT_MARKERS],
    *[re.compile(r"\b" + re.escape(marker) + r"\b") for marker in _PRIVATE_OWNER_MARKERS],
    re.compile(re.escape(_PRIVATE_WINDOWS_DOUBLE) + r"[^\s\"']*"),
    re.compile(re.escape(_PRIVATE_WINDOWS_SINGLE) + r"[^\s\"']*"),
]

MAX_LIST_ITEMS = 12


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def repo_rel(path: Path, root: Path = ROOT) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return None


def load_adapter_module():
    spec = importlib.util.spec_from_file_location("issue84_status_snapshot_readonly_adapter_for_cockpit", ADAPTER_MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load adapter module at {ADAPTER_MODULE_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["issue84_status_snapshot_readonly_adapter_for_cockpit"] = module
    spec.loader.exec_module(module)
    return module


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def redact_text(value: str) -> str:
    text = str(value)
    for pattern in PRIVATE_PATTERNS:
        text = pattern.sub("[redacted]", text)
    return text


def clean(value: Any, *, max_items: int = MAX_LIST_ITEMS) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        return [clean(item, max_items=max_items) for item in value[:max_items]]
    if isinstance(value, dict):
        return {redact_text(str(key)): clean(item, max_items=max_items) for key, item in value.items()}
    return redact_text(str(value))


def clean_ref(value: Any) -> str:
    text = redact_text(str(value or "").strip())
    if not text:
        return "external:unavailable-ref"
    if text.startswith("reports/") or text.startswith("fixtures/") or text.startswith("schemas/") or text.startswith("scripts/") or text.startswith("tests/"):
        return text
    if text.startswith("https://"):
        return text
    if text.startswith("SRC-") or text in {"ISSUE-84", "METHOD-CONTRACT", "DOCS-OS", "HUMAN-GATE", "PRODUCT-SOT"}:
        return text
    if text.startswith("external:"):
        return text
    return "external:redacted-ref"


def first_nonempty(*values: Any, default: str = "") -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return redact_text(text)
    return default


def list_strings(value: Any, *, fallback: list[str] | None = None) -> list[str]:
    if not isinstance(value, list):
        return list(fallback or [])
    items = [redact_text(str(item)) for item in value if str(item or "").strip()]
    return items or list(fallback or [])


def extract_refs(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    refs: list[str] = []
    for item in value:
        if isinstance(item, dict):
            candidate = item.get("ref") or item.get("id") or item.get("source_refs")
            if isinstance(candidate, list):
                refs.extend(clean_ref(part) for part in candidate)
            else:
                refs.append(clean_ref(candidate))
        else:
            refs.append(clean_ref(item))
    return sorted({ref for ref in refs if ref})


def state_ui_for(snapshot: dict[str, Any]) -> str:
    current_state = str(snapshot.get("current_state") or "missing")
    evidence = snapshot.get("evidence_refs") if isinstance(snapshot.get("evidence_refs"), list) else []
    boundary = snapshot.get("public_private_boundary") if isinstance(snapshot.get("public_private_boundary"), dict) else {}
    if current_state == "private_unavailable":
        return "private_evidence_unavailable"
    if any(str(item.get("public_safety_state") or "") == "private_redacted" for item in evidence if isinstance(item, dict)):
        return "private_evidence_unavailable"
    blocked_refs = boundary.get("blocked_refs") if isinstance(boundary, dict) else []
    if current_state not in CURRENT_TO_UI and blocked_refs:
        return "private_evidence_unavailable"
    return CURRENT_TO_UI.get(current_state, "blocked_gate")


def summarize_gate(gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": first_nonempty(gate.get("id"), default="gate"),
        "label": first_nonempty(gate.get("label"), default="Gate"),
        "state": first_nonempty(gate.get("state"), default="pending"),
        "owner": first_nonempty(gate.get("owner"), default="unassigned"),
        "unblock_condition": first_nonempty(gate.get("unblock_condition"), default="Review source refs before changing state."),
        "source_refs": [clean_ref(ref) for ref in gate.get("source_refs") or []],
    }


def summarize_blocker(blocker: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": first_nonempty(blocker.get("id"), default="blocker"),
        "state": first_nonempty(blocker.get("state"), default="blocked"),
        "summary": first_nonempty(blocker.get("summary"), default="Blocked until reviewed evidence is available."),
        "unblock_condition": first_nonempty(blocker.get("unblock_condition"), default="Provide public-safe reviewed evidence."),
        "source_refs": [clean_ref(ref) for ref in blocker.get("source_refs") or []],
    }


def summarize_evidence(evidence: dict[str, Any]) -> dict[str, Any]:
    raw = evidence.get("raw_payload_included")
    return {
        "id": first_nonempty(evidence.get("id"), default="evidence"),
        "kind": first_nonempty(evidence.get("kind"), default="artifact"),
        "ref": clean_ref(evidence.get("ref") or "external:redacted-ref"),
        "freshness_state": first_nonempty(evidence.get("freshness_state"), default="missing"),
        "public_safety_state": first_nonempty(evidence.get("public_safety_state"), default="unverified"),
        "verification_status": first_nonempty(evidence.get("verification_status"), default="unverified"),
        "raw_payload_included": bool(raw) if raw is not None else False,
        "source_refs": [clean_ref(ref) for ref in evidence.get("source_refs") or []],
        "unavailable_reason": first_nonempty(evidence.get("unavailable_reason"), default="") or None,
    }


def summarize_worker(worker: dict[str, Any]) -> dict[str, Any]:
    return {
        "worker_id": first_nonempty(worker.get("worker_id"), default="worker"),
        "state": first_nonempty(worker.get("state"), default="unknown"),
        "executor_identity": first_nonempty(worker.get("executor_identity"), default="executor"),
        "reviewer_identity": first_nonempty(worker.get("reviewer_identity"), default="reviewer"),
        "source_refs": [clean_ref(ref) for ref in worker.get("source_refs") or []],
    }


def summarize_snapshot(snapshot: dict[str, Any], *, input_path: Path, source_kind: str) -> dict[str, Any]:
    review = snapshot.get("review_state") if isinstance(snapshot.get("review_state"), dict) else {}
    receipt = snapshot.get("receipt_five_status") if isinstance(snapshot.get("receipt_five_status"), dict) else {}
    next_action = snapshot.get("next_safe_action") if isinstance(snapshot.get("next_safe_action"), dict) else {}
    flags = snapshot.get("state_flags") if isinstance(snapshot.get("state_flags"), dict) else {}
    boundary = snapshot.get("public_private_boundary") if isinstance(snapshot.get("public_private_boundary"), dict) else {}
    rel = repo_rel(input_path) or f"external:{source_kind}-input"
    gates = [summarize_gate(item) for item in snapshot.get("gate_states") or [] if isinstance(item, dict)]
    blockers = [summarize_blocker(item) for item in snapshot.get("blockers") or [] if isinstance(item, dict)]
    evidence = [summarize_evidence(item) for item in snapshot.get("evidence_refs") or [] if isinstance(item, dict)]
    workers = [summarize_worker(item) for item in snapshot.get("worker_state") or [] if isinstance(item, dict)]
    adapter_current_state = first_nonempty(snapshot.get("current_state"), default="missing")
    freshness_state = first_nonempty(snapshot.get("freshness_state"), default="missing")
    current_state = "private_unavailable" if freshness_state == "private_unavailable" else adapter_current_state
    snapshot_for_ui = dict(snapshot)
    snapshot_for_ui["current_state"] = current_state
    state_ui = state_ui_for(snapshot_for_ui)
    return {
        "id": first_nonempty(snapshot.get("fixture_id"), input_path.stem, default="snapshot")[:96],
        "fixture_name": first_nonempty(snapshot.get("fixture_name"), default=input_path.stem),
        "title": first_nonempty(snapshot.get("title"), default="Untitled StatusSnapshot projection"),
        "source_kind": source_kind,
        "input_ref": clean_ref(rel),
        "current_state": current_state,
        "adapter_current_state": adapter_current_state,
        "freshness_state": freshness_state,
        "state_ui": state_ui,
        "phase": first_nonempty(snapshot.get("phase"), default="F12 bounded implementation"),
        "risk_effective": first_nonempty(snapshot.get("risk_effective"), default="R2"),
        "observed_at": first_nonempty(snapshot.get("observed_at"), default="unknown"),
        "source_updated_at": clean(snapshot.get("source_updated_at")),
        "review": {
            "required": bool(review.get("required")) if review else True,
            "status": first_nonempty(review.get("status") if review else None, default="missing"),
            "executor_identity": first_nonempty(review.get("executor_identity") if review else None, default="executor"),
            "reviewer_identity": first_nonempty(review.get("reviewer_identity") if review else None, default="reviewer"),
            "reviewer_result": first_nonempty(review.get("reviewer_result") if review else None, default=""),
        },
        "receipt": {
            "status": first_nonempty(receipt.get("status"), default="missing"),
            "reviewer_required": bool(receipt.get("reviewer_required")) if receipt else True,
            "verification_result": first_nonempty(receipt.get("verification_result"), default="missing verification result"),
            "next_action": first_nonempty(receipt.get("next_action"), default="Request independent review."),
            "artifact_paths": [clean_ref(ref) for ref in receipt.get("artifact_paths") or []],
            "verification_commands": list_strings(receipt.get("verification_commands")),
        },
        "next_safe_action": {
            "action_type": first_nonempty(next_action.get("action_type"), default="block"),
            "label": first_nonempty(next_action.get("label"), default="Block until reviewed public-safe evidence exists."),
            "forbidden_action_taken": bool(next_action.get("forbidden_action_taken")),
            "source_refs": [clean_ref(ref) for ref in next_action.get("source_refs") or []],
        },
        "gate_states": gates,
        "blockers": blockers,
        "worker_state": workers,
        "evidence_refs": evidence,
        "public_private_boundary": {
            "allowed_refs": [clean_ref(ref) for ref in boundary.get("allowed_refs") or []],
            "blocked_refs": [redact_text(str(ref)) for ref in boundary.get("blocked_refs") or []],
            "raw_private_payload_included": False,
        },
        "state_flags": clean(flags),
        "traceability": {
            "source": [clean_ref(ref) for ref in (snapshot.get("traceability") or {}).get("source", [])] if isinstance(snapshot.get("traceability"), dict) else [],
            "inference": list_strings((snapshot.get("traceability") or {}).get("inference", [])) if isinstance(snapshot.get("traceability"), dict) else [],
            "decision": list_strings((snapshot.get("traceability") or {}).get("decision", [])) if isinstance(snapshot.get("traceability"), dict) else [],
        },
        "density": {
            "gate_count": len(gates),
            "blocker_count": len(blockers),
            "evidence_count": len(evidence),
            "worker_count": len(workers),
            "is_dense": len(gates) + len(blockers) + len(evidence) + len(workers) >= 8,
        },
    }


def report_input_paths(root: Path) -> list[Path]:
    reports = root / "reports"
    if not reports.exists():
        return []
    patterns = [
        "issue-84-status-snapshot-v0-*.json",
        "issue-84-readonly-status-adapter*.json",
    ]
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(reports.glob(pattern)))
    unique: list[Path] = []
    seen: set[Path] = set()
    for path in paths:
        if path not in seen:
            unique.append(path)
            seen.add(path)
    return unique


def build_status_snapshots(root: Path) -> list[dict[str, Any]]:
    adapter = load_adapter_module()
    snapshots: list[dict[str, Any]] = []
    fixture_dir = root / "fixtures" / "issue-84" / "status-snapshot-v0"
    for path in sorted(fixture_dir.glob("FX*.json")):
        projection = adapter.import_source(path)
        snapshots.append(summarize_snapshot(projection, input_path=path, source_kind="status_fixture"))
    for path in report_input_paths(root):
        projection = adapter.import_source(path)
        snapshots.append(summarize_snapshot(projection, input_path=path, source_kind="adapter_report"))
    return snapshots


def summarize_product_face(packet_path: Path | None) -> dict[str, Any]:
    fallback = {
        "surface": "local-first web cockpit",
        "mode": "reviewed Product Face packet unavailable in repo; use external reviewed packet summary",
        "user": "Open-source operator supervising product-production work from local structured snapshots.",
        "job_to_be_done": "Understand phase, blockers, evidence refs and next safe action without private runtime.",
        "required_states": list(REQUIRED_PACKET_STATES),
        "viewports": ["desktop_1440x900", "laptop_1280x800", "mobile_390x844", "mobile_360x800"],
        "proof_required": ["desktop screenshot", "mobile screenshot", "state evidence", "console error check", "performance note"],
        "visual_tone": "serious, calm, exacting operations cockpit",
        "density": "high-density desktop; mobile triage-first cards",
        "interaction_style": "read-only inspection, drill-down, filter/search, timeline replay and evidence-ref expansion",
        "must_have": ["visible source refs/provenance", "clear next safe action", "separate review/approval/done/release semantics"],
        "must_not_have": ["decorative KPIs", "generic admin-dashboard labels", "fake data implying gates passed"],
        "anti_generic_criteria": ["Every visible metric/card must tie to a factory object, gate, worker, receipt, evidence ref or next safe action."],
        "accepted_reference_directions": [],
        "rejected_reference_directions": [],
        "source_ref": "external:reviewed-product-face-packet",
    }
    if packet_path is None or not packet_path.exists():
        return fallback
    data = load_json(packet_path)
    packet = data.get("product_face_packet") if isinstance(data.get("product_face_packet"), dict) else {}
    direction = packet.get("design_direction") if isinstance(packet.get("design_direction"), dict) else {}
    visual = data.get("visual_quality_bar") if isinstance(data.get("visual_quality_bar"), dict) else {}
    refs = data.get("reference_quality_packet") if isinstance(data.get("reference_quality_packet"), dict) else {}
    return {
        "surface": first_nonempty(packet.get("surface"), default=fallback["surface"]),
        "mode": first_nonempty(packet.get("mode"), default=fallback["mode"]),
        "user": first_nonempty(packet.get("user"), default=fallback["user"]),
        "job_to_be_done": first_nonempty(packet.get("job_to_be_done"), default=fallback["job_to_be_done"]),
        "required_states": list_strings(packet.get("required_states"), fallback=list(REQUIRED_PACKET_STATES)),
        "viewports": list_strings(packet.get("device_or_viewport_scope"), fallback=fallback["viewports"]),
        "proof_required": list_strings(packet.get("proof_required"), fallback=fallback["proof_required"]),
        "visual_tone": first_nonempty(direction.get("visual_tone"), default=fallback["visual_tone"]),
        "density": first_nonempty(direction.get("density"), default=fallback["density"]),
        "interaction_style": first_nonempty(direction.get("interaction_style"), default=fallback["interaction_style"]),
        "must_have": list_strings(visual.get("must_have"), fallback=fallback["must_have"]),
        "must_not_have": list_strings(visual.get("must_not_have"), fallback=fallback["must_not_have"]),
        "anti_generic_criteria": list_strings(data.get("anti_generic_ai_dashboard_criteria"), fallback=fallback["anti_generic_criteria"]),
        "accepted_reference_directions": clean(refs.get("accepted_reference_directions") or []),
        "rejected_reference_directions": clean(refs.get("rejected_reference_directions") or []),
        "source_ref": "external:reviewed-product-face-packet",
    }


def summarize_product_face_review(review_path: Path | None) -> dict[str, Any]:
    fallback = {
        "verdict": "missing",
        "may_consume_product_face_packet": False,
        "consume_scope": "blocked until independent Product Face packet review is available",
        "still_blocked": ["Product Face Result evidence", "release", "issue completion"],
        "is_product_face_result": False,
        "source_ref": "external:product-face-packet-review",
    }
    if review_path is None or not review_path.exists():
        return fallback
    data = load_json(review_path)
    allowed = data.get("allowed_next_action") if isinstance(data.get("allowed_next_action"), dict) else {}
    return {
        "verdict": first_nonempty(data.get("verdict"), default="missing"),
        "may_consume_product_face_packet": bool(allowed.get("may_consume_product_face_packet")),
        "consume_scope": first_nonempty(allowed.get("consume_scope"), default="bounded local cockpit implementation only"),
        "still_blocked": list_strings(allowed.get("still_blocked"), fallback=fallback["still_blocked"]),
        "findings_summary": first_nonempty(data.get("findings_summary"), default="Independent packet review is an input, not a visual approval."),
        "is_product_face_result": False,
        "source_ref": "external:product-face-packet-review",
    }


def compute_metrics(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    current_counts = Counter(snapshot["current_state"] for snapshot in snapshots)
    ui_counts = Counter(snapshot["state_ui"] for snapshot in snapshots)
    review_counts = Counter(snapshot["review"]["status"] for snapshot in snapshots)
    return {
        "total_snapshots": len(snapshots),
        "status_fixture_projections": sum(1 for snapshot in snapshots if snapshot["source_kind"] == "status_fixture"),
        "adapter_report_projections": sum(1 for snapshot in snapshots if snapshot["source_kind"] == "adapter_report"),
        "current_state_counts": dict(sorted(current_counts.items())),
        "state_ui_counts": dict(sorted(ui_counts.items())),
        "review_state_counts": dict(sorted(review_counts.items())),
        "blocked_or_review_count": sum(1 for snapshot in snapshots if snapshot["current_state"] != "success"),
        "raw_private_payload_count": sum(1 for snapshot in snapshots for ev in snapshot["evidence_refs"] if ev.get("raw_payload_included")),
    }


def build_timeline(snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for snapshot in snapshots:
        rows.append(
            {
                "at": snapshot["observed_at"],
                "snapshot_id": snapshot["id"],
                "label": snapshot["title"],
                "current_state": snapshot["current_state"],
                "state_ui": snapshot["state_ui"],
                "next_action": snapshot["next_safe_action"]["action_type"],
                "source_ref": snapshot["input_ref"],
            }
        )
    return sorted(rows, key=lambda item: str(item["at"]))


def ensure_state_coverage(snapshots: list[dict[str, Any]]) -> None:
    covered = {snapshot["state_ui"] for snapshot in snapshots}
    missing = [state for state in REQUIRED_PACKET_STATES if state not in covered and state not in {"review_pending_failed_passed", "long_dense_data"}]
    if missing:
        raise ValueError("fixture/adapter projections missing required UI state coverage: " + ", ".join(missing))


def build_cockpit_data(
    root: Path = ROOT,
    *,
    product_face_packet_path: Path | None = None,
    product_face_review_path: Path | None = None,
) -> dict[str, Any]:
    root = Path(root)
    snapshots = build_status_snapshots(root)
    ensure_state_coverage(snapshots)
    product_face = summarize_product_face(product_face_packet_path)
    product_face_review = summarize_product_face_review(product_face_review_path)
    payload = {
        "$schema": "https://overkill-factory.dev/schemas/issue-84-local-cockpit-ui-data.schema.json",
        "record_type": "issue_84_local_cockpit_ui_data",
        "created_at": utc_now(),
        "source_inputs": {
            "normal_fetch_scope": "local-relative-json-only",
            "status_snapshot_fixture_dir": "fixtures/issue-84/status-snapshot-v0",
            "status_snapshot_fixture_count": sum(1 for snapshot in snapshots if snapshot["source_kind"] == "status_fixture"),
            "adapter_report_count": sum(1 for snapshot in snapshots if snapshot["source_kind"] == "adapter_report"),
            "product_face_packet": "external:reviewed-product-face-packet",
            "product_face_independent_review": "external:product-face-packet-review",
        },
        "policy": {
            "projection_only": True,
            "read_only_local_surface": True,
            "public_binding_allowed": False,
            "external_fetch_allowed": False,
            "runtime_mutation_allowed": False,
            "product_face_result_self_acceptance": False,
            "issue_completion_claim_allowed": False,
            "forbidden_actions": list(FORBIDDEN_ACTIONS),
            "approval_claims_blocked": [
                "worker_done is not reviewer approval",
                "reviewer PASS is not human gate approval",
                "Product Face packet is not Product Face result",
                "local cockpit implementation is not release or issue completion",
            ],
        },
        "product_face": product_face,
        "product_face_review": product_face_review,
        "state_registry": STATE_REGISTRY,
        "metrics": compute_metrics(snapshots),
        "snapshots": snapshots,
        "timeline": build_timeline(snapshots),
    }
    return clean(payload, max_items=500)


def write_cockpit_data(
    root: Path,
    output: Path,
    *,
    product_face_packet_path: Path | None = None,
    product_face_review_path: Path | None = None,
) -> Path:
    payload = build_cockpit_data(
        root,
        product_face_packet_path=product_face_packet_path,
        product_face_review_path=product_face_review_path,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build Issue #84 local cockpit UI data")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--product-face-packet", type=Path)
    parser.add_argument("--product-face-review", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    output = write_cockpit_data(
        args.root,
        args.out,
        product_face_packet_path=args.product_face_packet,
        product_face_review_path=args.product_face_review,
    )
    print(output.relative_to(args.root) if output.is_relative_to(args.root) else output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
