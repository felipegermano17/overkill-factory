#!/usr/bin/env python3
"""Read-only StatusSnapshot importer for Issue #84.

The adapter consumes checked-in StatusSnapshot fixtures or structured public
factory receipts and returns a projection object only. It never calls Hermes,
GitHub, network fetchers, approval paths, or runtime state changers.
"""

from __future__ import annotations

import argparse
import html
import ipaddress
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import unquote, urlparse

SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import status_snapshot_contract as contract

Resolver = Callable[[str], list[str]]

SCHEMA_URL = contract.SCHEMA_URL
SCHEMA_VERSION = contract.SCHEMA_VERSION
RECORD_TYPE = "factory_status_snapshot"
ALLOWED_RELATIVE_PREFIXES = (
    "reports/",
    "schemas/",
    "fixtures/",
    "templates/",
    "examples/",
    "validation/",
    "docs/",
    "scripts/",
    "tests/",
)
FORBIDDEN_ACTIONS = [
    "mutate factory cards or runtime state from a snapshot",
    "approve gates from projection state",
    "mark issue complete from worker done alone",
    "render raw private evidence",
    "release or publish without later human/security gates",
]
PRIVATE_HOST_LABELS = {
    "localhost",
    "metadata.google.internal",
    "metadata",
}
PRIVATE_RUNTIME_FRAGMENT = "/" + "srv/hermes"
LOCAL_PATH_RE = re.compile(
    r"(^/|^[A-Za-z]:\\|^\\\\|" + re.escape(PRIVATE_RUNTIME_FRAGMENT) + r"|/home/|/Users/|/tmp/)",
    re.IGNORECASE,
)
SAFE_EXTERNAL_LABEL_RE = re.compile(r"^external:[A-Za-z0-9][A-Za-z0-9._/-]{0,160}$")
URL_IN_TEXT_RE = re.compile(r"\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s)\]}>,]+")


@dataclass(frozen=True)
class ReferenceCheck:
    value: str
    allowed: bool
    kind: str
    reason: str = ""


def escape_text(value: Any) -> str:
    return html.escape(str(value or ""), quote=True)


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected JSON object")
    return data


def repo_relative(path: Path) -> str | None:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def _list_of_strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [escape_text(item) for item in value if str(item or "").strip()]


def _is_source_label(text: str) -> bool:
    return bool(
        text.startswith("SRC-")
        or text in {"ISSUE-84", "METHOD-CONTRACT", "DOCS-OS", "HUMAN-GATE", "PRODUCT-SOT"}
        or SAFE_EXTERNAL_LABEL_RE.match(text)
    )


def _public_safe_blocked_reason(checked: ReferenceCheck) -> str:
    """Return category-only denial metadata without copying the denied value."""
    reason_by_kind = {
        "empty": "empty reference denied",
        "file_uri": "file URI denied",
        "network_path": "scheme-relative network path denied",
        "source_label": "source label denied",
        "public_url": "public URL redirect failed safety checks",
        "url": "non-public or private-network URL denied",
        "local_path": "local absolute/private path denied",
        "path_traversal": "path traversal denied",
        "relative_artifact": "relative artifact denied",
        "opaque": "reference must be a public HTTPS URL, repo-relative artifact path, or source label",
    }
    return reason_by_kind.get(checked.kind, "unsafe reference denied")


def _blocked_ref_marker(field_name: str, idx: int, checked: ReferenceCheck) -> str:
    reason = _public_safe_blocked_reason(checked)
    return f"{field_name}[{idx}]: redacted {checked.kind} ({reason})"


def _blocked_ref_field_marker(field_name: str, checked: ReferenceCheck) -> str:
    reason = _public_safe_blocked_reason(checked)
    return f"{field_name}: redacted {checked.kind} ({reason})"


def _unsafe_reference_in_text(value: str, resolver: Resolver | None = None) -> ReferenceCheck | None:
    text = str(value or "").strip()
    if not text:
        return None
    lowered = text.lower()
    if lowered.startswith("file:") or text.startswith("//"):
        return _classify_one_reference(text)
    for match in URL_IN_TEXT_RE.findall(text):
        checked = classify_reference(match, resolver=resolver)
        if not checked.allowed:
            return checked
    if LOCAL_PATH_RE.search(text):
        return ReferenceCheck(text, False, "local_path", "local absolute/private path is forbidden")
    if _path_has_traversal(text):
        return ReferenceCheck(text, False, "path_traversal", "path traversal is forbidden")
    return None


def _normalize_ref_list(
    value: Any,
    *,
    field_name: str,
    resolver: Resolver | None = None,
    fallback: list[str] | None = None,
    allow_opaque_text: bool = False,
) -> tuple[list[str], list[str], list[str]]:
    safe_refs: list[str] = []
    allowed_refs: list[str] = []
    blocked_refs: list[str] = []
    items = value if isinstance(value, list) else []
    for idx, item in enumerate(items):
        raw_text = str(item or "").strip()
        if not raw_text:
            continue
        if allow_opaque_text:
            unsafe = _unsafe_reference_in_text(raw_text, resolver=resolver)
            if unsafe is not None:
                blocked_refs.append(_blocked_ref_marker(field_name, idx, unsafe))
                continue
            safe_refs.append(escape_text(raw_text))
            checked = classify_reference(raw_text, resolver=resolver)
            if checked.allowed:
                allowed_refs.append(checked.value)
            continue
        checked = classify_reference(raw_text, resolver=resolver)
        if checked.allowed:
            safe_refs.append(escape_text(checked.value))
            allowed_refs.append(checked.value)
        else:
            blocked_refs.append(_blocked_ref_marker(field_name, idx, checked))
    if not safe_refs and fallback:
        safe_refs = [escape_text(item) for item in fallback if str(item or "").strip()]
    return safe_refs, sorted(set(allowed_refs)), blocked_refs


def _merge_unique(*groups: Any) -> list[str]:
    merged: list[str] = []
    for group in groups:
        if not isinstance(group, list):
            continue
        for item in group:
            text = str(item or "").strip()
            if text and text not in merged:
                merged.append(text)
    return merged


def _path_has_traversal(value: str) -> bool:
    parts = [unquote(part) for part in value.replace("\\", "/").split("/")]
    return ".." in parts


def _is_private_host(hostname: str | None) -> bool:
    if not hostname:
        return True
    host = hostname.strip().lower().strip("[]")
    if host in PRIVATE_HOST_LABELS or host.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return bool(
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


def _classify_one_reference(value: str) -> ReferenceCheck:
    text = str(value or "").strip()
    if not text:
        return ReferenceCheck(text, False, "empty", "empty reference")
    lowered = text.lower()
    if lowered.startswith("file:"):
        return ReferenceCheck(text, False, "file_uri", "file URI is forbidden")
    if text.startswith("//"):
        return ReferenceCheck(text, False, "network_path", "scheme-relative network path is forbidden")
    if _is_source_label(text):
        return ReferenceCheck(text, True, "source_label")

    parsed = urlparse(text)
    if parsed.scheme:
        if parsed.scheme != "https":
            return ReferenceCheck(text, False, "url", "public URLs must use https")
        if _is_private_host(parsed.hostname):
            return ReferenceCheck(text, False, "url", "private-network or cloud-metadata URL is forbidden")
        if _path_has_traversal(parsed.path):
            return ReferenceCheck(text, False, "url", "URL path traversal is forbidden")
        return ReferenceCheck(text, True, "public_url")

    if LOCAL_PATH_RE.search(text):
        return ReferenceCheck(text, False, "local_path", "local absolute/private path is forbidden")
    if _path_has_traversal(text):
        return ReferenceCheck(text, False, "path_traversal", "path traversal is forbidden")
    if text.startswith(ALLOWED_RELATIVE_PREFIXES) and "//" not in text:
        return ReferenceCheck(text, True, "relative_artifact")
    return ReferenceCheck(text, False, "opaque", "reference must be a public HTTPS URL, repo-relative artifact path, or source label")


def classify_reference(value: str, resolver: Resolver | None = None) -> ReferenceCheck:
    initial = _classify_one_reference(value)
    if not initial.allowed or initial.kind != "public_url" or resolver is None:
        return initial
    try:
        chain = resolver(value)
    except Exception as exc:  # pragma: no cover - defensive path; callers inject resolver in tests.
        return ReferenceCheck(value, False, "public_url", f"redirect resolver failed: {exc}")
    for target in chain or []:
        checked = _classify_one_reference(str(target))
        if not checked.allowed or checked.kind != "public_url":
            return ReferenceCheck(
                value,
                False,
                "public_url",
                f"redirect target private/disallowed: {target} ({checked.reason})",
            )
    return initial


def _normalize_evidence_refs(raw_refs: Any, resolver: Resolver | None = None) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    evidence_refs: list[dict[str, Any]] = []
    blocked_refs: list[str] = []
    allowed_refs: list[str] = []
    items = raw_refs if isinstance(raw_refs, list) else []
    for idx, item in enumerate(items):
        raw = item if isinstance(item, dict) else {"id": f"EV-{idx + 1:02d}", "kind": "unknown"}
        evidence_id = escape_text(raw.get("id") or f"EV-{idx + 1:02d}")
        source_refs, source_allowed_refs, source_blocked_refs = _normalize_ref_list(
            raw.get("source_refs"),
            field_name=f"evidence_refs[{idx}].source_refs",
            resolver=resolver,
            fallback=["ISSUE-84"],
        )
        allowed_refs.extend(source_allowed_refs)
        blocked_refs.extend(source_blocked_refs)
        ref = raw.get("ref")
        raw_payload_included = raw.get("raw_payload_included") is True
        public_state = str(raw.get("public_safety_state") or "public_safe")
        verification = str(raw.get("verification_status") or "unverified")
        freshness = str(raw.get("freshness_state") or "current")
        normalized: dict[str, Any] = {
            "id": evidence_id,
            "kind": escape_text(raw.get("kind") or "worker_result"),
            "source_refs": source_refs,
            "freshness_state": freshness if freshness in contract.FRESHNESS_STATES else "current",
            "public_safety_state": public_state if public_state in contract.PUBLIC_SAFETY_STATES else "unverified",
            "verification_status": verification if verification in contract.VERIFICATION_STATES else "unverified",
            "raw_payload_included": False,
        }
        if source_blocked_refs:
            normalized["public_safety_state"] = "blocked"
            normalized["verification_status"] = "blocked"
            normalized["unavailable_reason"] = "unsafe EvidenceRef source_refs were redacted"
        if isinstance(ref, str) and ref.strip():
            checked = classify_reference(ref, resolver=resolver)
            if checked.allowed:
                normalized["ref"] = checked.value
                allowed_refs.append(checked.value)
            else:
                blocked_refs.append(_blocked_ref_field_marker(f"evidence_refs[{idx}].ref", checked))
                normalized["ref_label"] = f"redacted:{checked.kind}"
                normalized["public_safety_state"] = "blocked"
                normalized["verification_status"] = "blocked"
                normalized["unavailable_reason"] = _public_safe_blocked_reason(checked)
                normalized["redaction_note"] = "Denied EvidenceRef ref was redacted before projection; marker-only metadata retained."
        elif normalized["public_safety_state"] == "public_safe":
            normalized["public_safety_state"] = "missing"
            normalized["verification_status"] = "missing"
        if raw_payload_included:
            blocked_refs.append(f"{evidence_id}: raw_payload_included")
            normalized["public_safety_state"] = "blocked"
            normalized["verification_status"] = "blocked"
            normalized["unavailable_reason"] = "raw private payload marker was denied"
        evidence_refs.append(normalized)
    if not evidence_refs:
        evidence_refs.append(
            {
                "id": "EV-ADAPTER-INPUT",
                "kind": "adapter_input",
                "ref": "reports/issue-84-readonly-status-adapter-input.json",
                "source_refs": ["ISSUE-84"],
                "freshness_state": "missing",
                "public_safety_state": "missing",
                "verification_status": "missing",
                "raw_payload_included": False,
            }
        )
    return evidence_refs, sorted(set(allowed_refs)), sorted(set(blocked_refs))


def _receipt_from_report(report: dict[str, Any]) -> dict[str, Any]:
    for key in ("receipt_five", "receipt_five_status", "receipt"):
        value = report.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _review_status(receipt: dict[str, Any], report: dict[str, Any]) -> tuple[bool, str, str]:
    explicit = report.get("review_state")
    if isinstance(explicit, dict):
        required = explicit.get("required") is not False
        status = str(explicit.get("status") or "missing")
        result = str(explicit.get("reviewer_result") or receipt.get("reviewer_result") or "")
        if status in contract.REVIEW_STATES:
            return required, status, result
    required = receipt.get("reviewer_required") is not False
    result = str(receipt.get("reviewer_result") or report.get("reviewer_result") or "").strip()
    if not required:
        return False, "not_required", result
    lowered = result.lower()
    if not result:
        return True, "missing", "missing - independent reviewer result required"
    if "pass" in lowered or "approved" in lowered:
        return True, "passed", result
    if "fail" in lowered:
        return True, "failed", result
    if "block" in lowered:
        return True, "blocked", result
    return True, "pending", result


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def _is_stale(report: dict[str, Any]) -> bool:
    if report.get("freshness_state") == "stale":
        return True
    observed = _parse_timestamp(report.get("observed_at"))
    updated = _parse_timestamp(report.get("source_updated_at"))
    if observed and updated:
        return updated > observed
    return False


def _is_contradictory(report: dict[str, Any]) -> bool:
    contradictions = report.get("contradictions")
    if isinstance(contradictions, list) and contradictions:
        return True
    return report.get("release_state") == "released" and report.get("public_issue_state") == "reopened"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _base_snapshot(*, fixture_id: str, fixture_name: str, title: str, source_refs: list[str]) -> dict[str, Any]:
    return {
        "$schema": SCHEMA_URL,
        "schema_version": SCHEMA_VERSION,
        "record_type": RECORD_TYPE,
        "fixture_id": fixture_id,
        "fixture_name": fixture_name,
        "kind": "run",
        "title": escape_text(title),
        "phase": "F12 bounded implementation / read-only adapter",
        "risk_effective": "R2",
        "observed_at": _now(),
        "source_updated_at": None,
        "freshness_state": "current",
        "current_state": "blocked",
        "source_refs": source_refs or ["ISSUE-84"],
        "canonical_refs": ["schemas/factory-status-snapshot.schema.json"],
        "gate_states": [],
        "blockers": [],
        "worker_state": [],
        "review_state": {},
        "receipt_five_status": {},
        "evidence_refs": [],
        "public_private_boundary": {
            "allowed_refs": ["public HTTPS URLs", "repo-relative artifact paths", "redacted private-unavailable metadata"],
            "blocked_refs": ["local absolute paths", "file URIs", "path traversal", "private network/cloud metadata URLs"],
            "raw_private_payload_included": False,
        },
        "state_flags": {
            "request": True,
            "approval": False,
            "blocked": True,
            "done": False,
            "released": False,
            "superseded": False,
            "implemented": False,
            "validated": False,
            "integrated": False,
        },
        "forbidden_actions": list(FORBIDDEN_ACTIONS),
        "next_safe_action": {
            "action_type": "block",
            "label": "Block until canonical public-safe StatusSnapshot input is available.",
            "source_refs": source_refs or ["ISSUE-84"],
            "forbidden_action_taken": False,
        },
        "validation_expectations": {
            "expected_fixture_validator": "pass",
            "evidence_ref_public_safety_expected": "pass",
            "fail_closed_required": True,
            "required_assertions": [
                "projection-only adapter output",
                "no forbidden action taken",
                "public/private boundary preserved",
            ],
        },
        "adapter_metadata": {
            "projection_only": True,
            "mutations_performed": [],
            "network_fetch_performed": False,
            "runtime_mutation_performed": False,
        },
        "traceability": {"source": source_refs or ["ISSUE-84"], "inference": [], "decision": []},
    }


def _missing_snapshot(path: Path) -> dict[str, Any]:
    source = repo_relative(path) or "private-unavailable:missing-input"
    snapshot = _base_snapshot(
        fixture_id="ADAPTER-MISSING",
        fixture_name="missing adapter input",
        title="Issue 84 StatusSnapshot adapter missing input",
        source_refs=[source, "ISSUE-84"],
    )
    snapshot["freshness_state"] = "missing"
    snapshot["current_state"] = "missing"
    snapshot["receipt_five_status"] = {
        "status": "missing",
        "reviewer_required": True,
        "reviewer_result": "missing - input file did not exist",
        "changed": "No worker result could be projected because the adapter input was missing.",
        "artifact_paths": ["reports/issue-84-readonly-status-adapter-missing-input.json"],
        "verification_commands": ["python3 scripts/issue84/status_snapshot_readonly_adapter.py import <input>"],
        "verification_result": "missing input fail-closed",
        "next_action": "Provide a repo-relative public-safe report or StatusSnapshot fixture.",
    }
    snapshot["gate_states"] = [
        {"id": "canonical_input", "label": "Canonical adapter input", "state": "missing", "source_refs": [source]}
    ]
    snapshot["worker_state"] = [
        {"worker_id": "backend-api-builder", "state": "blocked", "executor_identity": "backend-api-builder", "source_refs": [source]}
    ]
    snapshot["review_state"] = {
        "required": True,
        "status": "missing",
        "executor_identity": "backend-api-builder",
        "reviewer_identity": "qa-verification-worker",
        "source_refs": [source],
    }
    snapshot["evidence_refs"] = [
        {
            "id": "EV-MISSING-INPUT",
            "kind": "adapter_input",
            "source_refs": [source],
            "freshness_state": "missing",
            "public_safety_state": "missing",
            "verification_status": "missing",
            "raw_payload_included": False,
        }
    ]
    snapshot["blockers"] = [
        {
            "id": "missing-input",
            "state": "missing",
            "summary": "Adapter input report or fixture is missing.",
            "unblock_condition": "Provide a checked-in StatusSnapshot fixture or public-safe report ref.",
            "source_refs": [source],
        }
    ]
    return snapshot


def _import_status_snapshot(data: dict[str, Any], *, source_path: Path, resolver: Resolver | None = None) -> dict[str, Any]:
    snapshot = json.loads(json.dumps(data))
    evidence_refs, allowed_refs, blocked_refs = _normalize_evidence_refs(snapshot.get("evidence_refs"), resolver=resolver)
    snapshot["evidence_refs"] = evidence_refs
    boundary = snapshot.get("public_private_boundary") if isinstance(snapshot.get("public_private_boundary"), dict) else {}
    boundary["allowed_refs"] = sorted(set(list(boundary.get("allowed_refs") or []) + allowed_refs)) or ["repo-relative artifact paths"]
    boundary["blocked_refs"] = sorted(set(list(boundary.get("blocked_refs") or []) + blocked_refs)) or ["local absolute paths"]
    boundary["raw_private_payload_included"] = False
    snapshot["public_private_boundary"] = boundary
    if blocked_refs:
        snapshot["current_state"] = "security_negative"
        snapshot["next_safe_action"] = {
            "action_type": "block",
            "label": "Block unsafe EvidenceRef values before cockpit projection.",
            "source_refs": snapshot.get("source_refs") or ["ISSUE-84"],
            "forbidden_action_taken": False,
        }
        snapshot.setdefault("state_flags", {})["blocked"] = True
        snapshot.setdefault("state_flags", {})["approval"] = False
    rel = repo_relative(source_path)
    snapshot["adapter_metadata"] = {
        "projection_only": True,
        "mutations_performed": [],
        "network_fetch_performed": False,
        "runtime_mutation_performed": False,
        "input_ref": rel or "private-unavailable:external-input",
    }
    snapshot.setdefault("traceability", {"source": snapshot.get("source_refs") or ["ISSUE-84"], "inference": [], "decision": []})
    return snapshot


def _report_snapshot(data: dict[str, Any], *, source_path: Path, resolver: Resolver | None = None) -> dict[str, Any]:
    fallback_source = repo_relative(source_path) or "ISSUE-84"
    source_refs, source_allowed_refs, source_blocked_refs = _normalize_ref_list(
        data.get("source_refs"),
        field_name="source_refs",
        resolver=resolver,
        fallback=[fallback_source],
    )
    canonical_input_refs, canonical_allowed_refs, canonical_blocked_refs = _normalize_ref_list(
        data.get("canonical_refs"),
        field_name="canonical_refs",
        resolver=resolver,
    )
    changed_file_refs, changed_allowed_refs, changed_blocked_refs = _normalize_ref_list(
        data.get("changed_files"),
        field_name="changed_files",
        resolver=resolver,
    )
    decision_refs, decision_allowed_refs, decision_blocked_refs = _normalize_ref_list(
        data.get("decision_refs"),
        field_name="decision_refs",
        resolver=resolver,
        allow_opaque_text=True,
    )
    inference_refs, inference_allowed_refs, inference_blocked_refs = _normalize_ref_list(
        data.get("inference_refs"),
        field_name="inference_refs",
        resolver=resolver,
        allow_opaque_text=True,
    )
    receipt = _receipt_from_report(data)
    artifact_refs, artifact_allowed_refs, artifact_blocked_refs = _normalize_ref_list(
        receipt.get("artifact_paths"),
        field_name="receipt_five.artifact_paths",
        resolver=resolver,
    )
    if not artifact_refs:
        artifact_refs = changed_file_refs or ["reports/issue-84-readonly-status-adapter-input.json"]
    reviewer_required, review_status, reviewer_result = _review_status(receipt, data)
    evidence_refs, allowed_refs, blocked_refs = _normalize_evidence_refs(data.get("evidence_refs"), resolver=resolver)
    non_evidence_allowed_refs = _merge_unique(
        source_allowed_refs,
        canonical_allowed_refs,
        changed_allowed_refs,
        decision_allowed_refs,
        inference_allowed_refs,
        artifact_allowed_refs,
    )
    non_evidence_blocked_refs = _merge_unique(
        source_blocked_refs,
        canonical_blocked_refs,
        changed_blocked_refs,
        decision_blocked_refs,
        inference_blocked_refs,
        artifact_blocked_refs,
    )
    all_allowed_refs = _merge_unique(allowed_refs, non_evidence_allowed_refs)
    all_blocked_refs = _merge_unique(blocked_refs, non_evidence_blocked_refs)
    worker_done = bool(receipt.get("changed") and receipt.get("verification_result")) or data.get("worker_status") == "done"
    implemented = bool(data.get("changed_files") or receipt.get("artifact_paths"))
    verification_result = str(receipt.get("verification_result") or "missing verification result")
    validated = "pass" in verification_result.lower() and review_status == "passed" and not all_blocked_refs
    human_approval = data.get("human_approval") in {True, "passed", "approved"}
    approval = bool(review_status == "passed" and human_approval)

    snapshot = _base_snapshot(
        fixture_id=escape_text(str(data.get("task_ref") or source_path.stem or "ADAPTER-REPORT"))[:64],
        fixture_name="readonly adapter report projection",
        title=data.get("title") or "Issue 84 read-only StatusSnapshot adapter projection",
        source_refs=source_refs,
    )
    snapshot["kind"] = "run"
    snapshot["phase"] = escape_text(data.get("phase") or snapshot["phase"])
    snapshot["risk_effective"] = escape_text(data.get("risk_effective") or "R2")
    snapshot["observed_at"] = escape_text(data.get("observed_at") or _now())
    snapshot["source_updated_at"] = data.get("source_updated_at") if isinstance(data.get("source_updated_at"), str) else None
    snapshot["canonical_refs"] = _merge_unique(
        ["schemas/factory-status-snapshot.schema.json"],
        canonical_input_refs,
        [ref for ref in all_allowed_refs if ref.startswith(ALLOWED_RELATIVE_PREFIXES)],
    )
    snapshot["evidence_refs"] = evidence_refs
    snapshot["public_private_boundary"] = {
        "allowed_refs": sorted(set(["public HTTPS URLs", "repo-relative artifact paths", "redacted private-unavailable metadata"] + all_allowed_refs)),
        "blocked_refs": sorted(set(["local absolute paths", "file URIs", "path traversal", "private network/cloud metadata URLs"] + all_blocked_refs)),
        "raw_private_payload_included": False,
    }

    receipt_status = "present" if receipt else "missing"
    if reviewer_required and review_status in {"missing", "blocked", "failed", "stale", "superseded"}:
        receipt_status = "review_missing" if receipt_status == "present" and review_status == "missing" else receipt_status
    verification_commands = _list_of_strings(receipt.get("verification_commands")) or ["python3 -m unittest tests.test_issue84_readonly_status_adapter"]
    snapshot["receipt_five_status"] = {
        "status": receipt_status,
        "reviewer_required": bool(reviewer_required),
        "reviewer_result": escape_text(reviewer_result) if reviewer_required else escape_text(reviewer_result or "not required"),
        "changed": escape_text(receipt.get("changed") or "Structured report imported as read-only StatusSnapshot projection."),
        "artifact_paths": artifact_refs,
        "verification_commands": verification_commands,
        "verification_result": escape_text(verification_result),
        "next_action": escape_text(receipt.get("next_action") or "Request independent review before any promotion."),
    }
    snapshot["worker_state"] = [
        {
            "worker_id": escape_text(data.get("worker_id") or "backend-api-builder"),
            "state": "done" if worker_done else "blocked",
            "executor_identity": escape_text(data.get("executor_identity") or "backend-api-builder"),
            "reviewer_identity": escape_text(data.get("reviewer_identity") or "qa-verification-worker"),
            "source_refs": source_refs,
        }
    ]
    snapshot["review_state"] = {
        "required": bool(reviewer_required),
        "status": review_status,
        "executor_identity": escape_text(data.get("executor_identity") or "backend-api-builder"),
        "reviewer_identity": escape_text(data.get("reviewer_identity") or "qa-verification-worker"),
        "source_refs": source_refs,
        "reviewer_result": escape_text(reviewer_result),
    }
    snapshot["gate_states"] = [
        {
            "id": "independent_review",
            "label": "Independent adapter review",
            "state": review_status if review_status in contract.GATE_STATES else "pending",
            "owner": "qa-verification-worker",
            "unblock_condition": "qa-verification-worker reviews read-only adapter behavior and receipt evidence",
            "source_refs": source_refs,
        }
    ]

    action_type = "none"
    action_label = "No action from projection; keep runtime immutable."
    freshness_state = "current"
    current_state = "success" if approval else "blocked"
    fail_closed = not approval
    if all_blocked_refs:
        current_state = "security_negative"
        action_type = "block"
        action_label = "Block unsafe ref-bearing report fields before cockpit projection."
    elif _is_contradictory(data):
        freshness_state = "contradictory"
        current_state = "contradictory"
        action_type = "review"
        action_label = "Review contradictory public states before any completion claim."
    elif data.get("superseded_by"):
        freshness_state = "superseded"
        current_state = "superseded"
        action_type = "review"
        action_label = "Review newer artifact before using this superseded projection."
    elif _is_stale(data):
        freshness_state = "stale"
        current_state = "stale"
        action_type = "refresh"
        action_label = "Refresh stale source export before cockpit projection."
    elif receipt_status == "missing":
        freshness_state = "missing"
        current_state = "missing"
        action_type = "block"
        action_label = "Block until Receipt Five fields are present."
    elif reviewer_required and review_status != "passed":
        current_state = "blocked"
        action_type = "review"
        action_label = "Request independent reviewer result; worker_done is not approval."
    elif not approval:
        current_state = "blocked"
        action_type = "review"
        action_label = "Keep projection blocked until reviewer and human approval gates are explicit."
    if current_state == "success" and action_type == "none":
        fail_closed = False

    snapshot["freshness_state"] = freshness_state
    snapshot["current_state"] = current_state
    snapshot["next_safe_action"] = {
        "action_type": action_type,
        "label": action_label,
        "source_refs": source_refs,
        "forbidden_action_taken": False,
    }
    if current_state != "success":
        snapshot["blockers"] = [
            {
                "id": current_state.replace("_", "-"),
                "state": current_state,
                "summary": action_label,
                "unblock_condition": "Provide fresh public-safe canonical evidence and independent review before promotion.",
                "source_refs": source_refs,
            }
        ]
    snapshot["state_flags"] = {
        "request": True,
        "approval": approval,
        "blocked": current_state != "success",
        "done": worker_done,
        "released": data.get("release_state") == "released" and current_state == "contradictory",
        "superseded": current_state == "superseded",
        "implemented": implemented,
        "validated": validated,
        "integrated": False,
    }
    snapshot["validation_expectations"]["fail_closed_required"] = fail_closed
    snapshot["validation_expectations"]["required_assertions"] = [
        "read-only projection generated without runtime mutation",
        "worker_done remains separate from reviewer/human approval",
        "EvidenceRef deny rules are enforced before projection",
        "next_safe_action uses only fail-closed action types unless fully approved",
    ]
    snapshot["traceability"] = {
        "source": source_refs,
        "inference": inference_refs or ["adapter derived fail-closed state from report metadata"],
        "decision": decision_refs or ["projection-only adapter; no runtime mutation authorized"],
    }
    snapshot["adapter_metadata"].update(
        {
            "input_ref": repo_relative(source_path) or "private-unavailable:external-input",
            "report_record_type": escape_text(data.get("record_type") or "unknown"),
        }
    )
    return snapshot


def import_source(path: str | Path, resolver: Resolver | None = None) -> dict[str, Any]:
    source_path = Path(path)
    if not source_path.exists():
        return _missing_snapshot(source_path)
    data = load_json(source_path)
    if data.get("schema_version") == SCHEMA_VERSION and data.get("record_type") == RECORD_TYPE:
        return _import_status_snapshot(data, source_path=source_path, resolver=resolver)
    return _report_snapshot(data, source_path=source_path, resolver=resolver)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Issue 84 read-only StatusSnapshot importer")
    subparsers = parser.add_subparsers(dest="command", required=True)
    import_parser = subparsers.add_parser("import", help="project a fixture or report into StatusSnapshot JSON")
    import_parser.add_argument("input", type=Path)
    import_parser.add_argument("--out", type=Path)
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "import":
        snapshot = import_source(args.input)
        payload = json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
        if args.out:
            args.out.parent.mkdir(parents=True, exist_ok=True)
            args.out.write_text(payload, encoding="utf-8")
        else:
            print(payload, end="")
        return 0
    raise AssertionError(args.command)


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
