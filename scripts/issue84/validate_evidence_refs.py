#!/usr/bin/env python3
"""Validate public-safe EvidenceRef values for Issue #84 StatusSnapshot fixtures.

The full fixture suite contains one deliberate negative fixture (FX10). This
validator passes the suite only when all positive fixtures are clean and the
expected negative fixture is actually rejected.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import status_snapshot_contract as contract

PRIVATE_RUNTIME_FRAGMENT = "/" + "srv/hermes"
LOCAL_PATH_RE = re.compile(
    r"(^/|[A-Za-z]:\\|\\\\|" + re.escape(PRIVATE_RUNTIME_FRAGMENT) + r"|/home/|/Users/|/tmp/)",
    re.IGNORECASE,
)
FILE_URI_RE = re.compile(r"^file:", re.IGNORECASE)
CHAT_ID_RE = re.compile(r"(discord(?:\.com|://)|slack(?:\.com|://)|telegram(?:\.me|://)|\bchannel[_-]?id\b|\bmessage[_-]?id\b)", re.IGNORECASE)
PRIVATE_TASK_RE = re.compile(r"\bt_[a-f0-9]{8}\b")
SECRET_RE = re.compile(
    r"(?i)(aws_access_key_id|aws_secret_access_key|api[_-]?key|token|secret|password|private[_-]?key)\s*[:=]\s*[A-Za-z0-9_./+=-]{8,}"
)
RAW_PRIVATE_RE = re.compile(r"(?i)(raw private|private screenshot|private log|unredacted|secret dump)")
RELATIVE_ARTIFACT_RE = re.compile(r"^(reports|schemas|fixtures|templates|examples|validation|docs|scripts)/[A-Za-z0-9._/@+\-]+$")
PUBLIC_URL_RE = re.compile(r"^https://(github\.com|raw\.githubusercontent\.com|overkill-factory\.dev)/[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%\-]+$")


def iter_strings(value: Any, prefix: str = "$") -> list[tuple[str, str]]:
    if isinstance(value, str):
        return [(prefix, value)]
    if isinstance(value, list):
        items: list[tuple[str, str]] = []
        for idx, item in enumerate(value):
            items.extend(iter_strings(item, f"{prefix}[{idx}]"))
        return items
    if isinstance(value, dict):
        items = []
        for key, item in value.items():
            items.extend(iter_strings(item, f"{prefix}.{key}"))
        return items
    return []


def classify_ref(value: str) -> str:
    if PUBLIC_URL_RE.match(value):
        return "public_url"
    if RELATIVE_ARTIFACT_RE.match(value) and ".." not in value and "//" not in value:
        return "relative_artifact"
    if value.startswith("SRC-") or value in {"ISSUE-84", "METHOD-CONTRACT", "DOCS-OS", "HUMAN-GATE", "PRODUCT-SOT"}:
        return "source_label"
    return "opaque_label"


def scan_evidence_ref(evidence: dict[str, Any], *, deny_raw_private: bool = True, deny_local_paths: bool = True, deny_chat_ids: bool = True, deny_secrets: bool = True) -> list[str]:
    errors: list[str] = []
    evidence_id = str(evidence.get("id") or "<unknown>")
    if evidence.get("raw_payload_included") is not False:
        errors.append(f"{evidence_id}: raw_payload_included must be false")

    for at, value in iter_strings(evidence):
        # Source labels and explanatory unavailable_reason text are allowed to be
        # descriptive; the concrete ref/ref_label fields carry the hard checks.
        if at.endswith(".unavailable_reason") or at.endswith(".redaction_note"):
            if deny_secrets and SECRET_RE.search(value):
                errors.append(f"{evidence_id}:{at}: secret-looking unavailable reason")
            continue
        if deny_local_paths and (FILE_URI_RE.search(value) or LOCAL_PATH_RE.search(value)):
            errors.append(f"{evidence_id}:{at}: local path or file URI is forbidden")
        if deny_chat_ids and (CHAT_ID_RE.search(value) or PRIVATE_TASK_RE.search(value)):
            errors.append(f"{evidence_id}:{at}: private task/chat identifier is forbidden")
        if deny_secrets and SECRET_RE.search(value):
            errors.append(f"{evidence_id}:{at}: secret-looking value is forbidden")
        if deny_raw_private and RAW_PRIVATE_RE.search(value):
            errors.append(f"{evidence_id}:{at}: raw private evidence marker is forbidden")

    ref = evidence.get("ref")
    if isinstance(ref, str):
        classification = classify_ref(ref)
        if classification == "opaque_label":
            errors.append(f"{evidence_id}: ref must be a public URL or repo-relative artifact path, got {ref!r}")
    elif evidence.get("public_safety_state") == "public_safe":
        errors.append(f"{evidence_id}: public_safe evidence requires concrete ref")

    if evidence.get("public_safety_state") == "private_redacted" and evidence.get("ref"):
        errors.append(f"{evidence_id}: private_redacted evidence must omit concrete ref")
    return errors


def scan_snapshot(data: dict[str, Any], **kwargs: bool) -> list[str]:
    errors: list[str] = []
    for idx, evidence in enumerate(data.get("evidence_refs") or []):
        if not isinstance(evidence, dict):
            errors.append(f"evidence_refs[{idx}]: expected object")
            continue
        errors.extend(scan_evidence_ref(evidence, **kwargs))
    return errors


def validate_directory(directory: str | Path, **kwargs: bool) -> dict[str, Any]:
    expected_blocked: list[str] = []
    missed_expected: list[str] = []
    unexpected_blocked: list[str] = []
    clean_positive: list[str] = []

    for path, data in contract.load_fixtures(directory):
        fixture_id = str(data.get("fixture_id") or path.stem)
        raw_expectations = data.get("validation_expectations")
        expectations: dict[str, Any] = raw_expectations if isinstance(raw_expectations, dict) else {}
        expected = expectations.get("evidence_ref_public_safety_expected", "pass")
        findings = scan_snapshot(data, **kwargs)
        if expected == "fail":
            if findings:
                expected_blocked.append(fixture_id)
            else:
                missed_expected.append(fixture_id)
        elif findings:
            unexpected_blocked.extend(f"{fixture_id}: {finding}" for finding in findings)
        else:
            clean_positive.append(fixture_id)

    return {
        "result": "PASS" if not missed_expected and not unexpected_blocked else "FAIL",
        "clean_positive_count": len(clean_positive),
        "expected_blocked_count": len(expected_blocked),
        "missed_expected_block_count": len(missed_expected),
        "unexpected_blocked_count": len(unexpected_blocked),
        "expected_blocked": expected_blocked,
        "missed_expected_block": missed_expected,
        "unexpected_blocked": unexpected_blocked,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--allow-public-urls", action="store_true", help="Accepted by contract; public HTTPS URLs are always allowed")
    parser.add_argument("--allow-relative-artifacts", action="store_true", help="Accepted by contract; repo-relative artifact paths are always allowed")
    parser.add_argument("--deny-raw-private", action="store_true", default=True)
    parser.add_argument("--deny-local-paths", action="store_true", default=True)
    parser.add_argument("--deny-chat-ids", action="store_true", default=True)
    parser.add_argument("--deny-secrets", action="store_true", default=True)
    parser.add_argument("--json", action="store_true", help="Emit JSON summary")
    return parser


def main_with_args(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = validate_directory(
        args.directory,
        deny_raw_private=args.deny_raw_private,
        deny_local_paths=args.deny_local_paths,
        deny_chat_ids=args.deny_chat_ids,
        deny_secrets=args.deny_secrets,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    elif summary["result"] == "PASS":
        print(
            "OK: evidence refs public-safe; "
            f"{summary['expected_blocked_count']} expected negative fixture(s) rejected"
        )
    else:
        for item in summary["missed_expected_block"]:
            print(f"missed expected evidence-ref rejection: {item}", file=sys.stderr)
        for item in summary["unexpected_blocked"]:
            print(item, file=sys.stderr)
    return 0 if summary["result"] == "PASS" else 1


def main_with_args_for_test(argv: list[str]) -> int:
    return main_with_args(argv)


def main() -> int:
    return main_with_args()


if __name__ == "__main__":
    raise SystemExit(main())
