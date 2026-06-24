"""Canonical method-engine registry for Overkill Factory."""

from __future__ import annotations

import json
import re
import sysconfig
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_METHOD_ENGINE_REGISTRY_PATH = ROOT / "templates" / "method-engine-registry.json"

REQUIRED_ENGINE_IDS = {
    "spec_first_sdd",
    "test_first_tdd",
    "behavior_first_bdd",
    "discovery_research",
    "security_first_threat_model",
    "design_first_product_experience",
    "legacy_diagnosis",
    "incident_first",
}

METHOD_TO_ENGINE = {
    "spec-first": "spec_first_sdd",
    "test-first": "test_first_tdd",
    "behavior-first": "behavior_first_bdd",
    "discovery-first": "discovery_research",
    "security-first": "security_first_threat_model",
    "design-first": "design_first_product_experience",
    "legacy-diagnosis": "legacy_diagnosis",
    "incident-first": "incident_first",
}

PRIVATE_REF_RE = re.compile(r"((?<![A-Za-z])[A-Za-z]:[\\/]|\\\\|/home/|/Users/|/srv/|/var/)", re.I)


def method_engine_registry_candidates() -> list[Path]:
    data_root = Path(sysconfig.get_path("data") or "")
    return [
        DEFAULT_METHOD_ENGINE_REGISTRY_PATH,
        ROOT / "share" / "overkill-factory" / "templates" / "method-engine-registry.json",
        data_root / "share" / "overkill-factory" / "templates" / "method-engine-registry.json",
    ]


def load_method_engine_registry(path: Path | None = None) -> dict[str, Any]:
    if path is not None:
        registry_path = path
    else:
        registry_path = next(
            (candidate for candidate in method_engine_registry_candidates() if candidate.exists()),
            DEFAULT_METHOD_ENGINE_REGISTRY_PATH,
        )
    return json.loads(registry_path.read_text(encoding="utf-8"))


def method_engine_entries(registry: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    data = registry or load_method_engine_registry()
    entries = data.get("engines") if isinstance(data.get("engines"), list) else []
    return {
        str(entry.get("engine_id")): entry
        for entry in entries
        if isinstance(entry, dict) and str(entry.get("engine_id") or "").strip()
    }


def method_engine_for_method(method: str, registry: dict[str, Any] | None = None) -> dict[str, Any] | None:
    engine_id = METHOD_TO_ENGINE.get(method)
    if not engine_id:
        return None
    return method_engine_entries(registry).get(engine_id)


def _list_items(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _private_ref_errors(value: Any, at: str) -> list[str]:
    errors: list[str] = []
    if isinstance(value, str):
        if PRIVATE_REF_RE.search(value):
            errors.append(f"{at}: method-engine registry must not publish private/local refs")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            errors.extend(_private_ref_errors(item, f"{at}[{index}]"))
    elif isinstance(value, dict):
        for key, item in value.items():
            errors.extend(_private_ref_errors(item, f"{at}.{key}"))
    return errors


def validate_method_engine_registry_semantics(registry: dict[str, Any], at: str = "$") -> list[str]:
    errors: list[str] = []
    entries = method_engine_entries(registry)
    missing = sorted(REQUIRED_ENGINE_IDS - set(entries))
    if missing:
        errors.append(f"{at}.engines: missing required method engines: " + ", ".join(missing))
    coverage = registry.get("coverage_policy") if isinstance(registry.get("coverage_policy"), dict) else {}
    if coverage.get("method_label_cannot_authorize_execution") is not True:
        errors.append(f"{at}.coverage_policy.method_label_cannot_authorize_execution must be true")
    if coverage.get("operator_does_not_choose_internal_method") is not True:
        errors.append(f"{at}.coverage_policy.operator_does_not_choose_internal_method must be true")
    if coverage.get("all_engines_require_artifacts_gates_workers_and_proof") is not True:
        errors.append(f"{at}.coverage_policy.all_engines_require_artifacts_gates_workers_and_proof must be true")
    boundary = registry.get("public_private_boundary") if isinstance(registry.get("public_private_boundary"), dict) else {}
    if boundary.get("public_safe_refs_only") is not True:
        errors.append(f"{at}.public_private_boundary.public_safe_refs_only must be true")
    if boundary.get("raw_private_evidence_embedded") is not False:
        errors.append(f"{at}.public_private_boundary.raw_private_evidence_embedded must be false")

    for engine_id, entry in entries.items():
        entry_at = f"{at}.engines[{engine_id}]"
        if not _list_items(entry.get("method_aliases")):
            errors.append(f"{entry_at}.method_aliases must be non-empty")
        for field in ("required_artifacts", "required_gates", "required_workers", "proof_requirements", "forbidden_shortcuts"):
            if not _list_items(entry.get(field)):
                errors.append(f"{entry_at}.{field} must be non-empty")
        if entry.get("operator_choice_required") is not False:
            errors.append(f"{entry_at}.operator_choice_required must be false")
        if entry.get("execution_allowed_by_engine_selection") is not False:
            errors.append(f"{entry_at}.execution_allowed_by_engine_selection must be false")
    errors.extend(_private_ref_errors(registry, at))
    return errors
