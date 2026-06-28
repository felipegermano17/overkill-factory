#!/usr/bin/env python3
"""Validate Factory V2 agent-vs-skill boundaries."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from validate_public_json_artifacts import load_schemas, validate_node  # noqa: E402


FORBIDDEN_AGENT_AUTHORITY_MARKERS = (
    "choose phase outside",
    "choose route outside",
    "approve gates",
    "approve product decisions",
    "waive security findings",
    "mutate card state directly",
)
AUTHORITY_SUGGESTING_WORKER_ID_MARKERS = ("orchestrator", "router", "manager", "gate")


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def validate_schema(path: Path) -> list[str]:
    data = load_json(path)
    ref = str(data.get("$schema") or "")
    if not ref:
        return [f"{path.relative_to(ROOT).as_posix()}: missing $schema"]
    schemas = load_schemas()
    schema = schemas.get(ref.rsplit("/", 1)[-1])
    if not isinstance(schema, dict):
        return [f"{path.relative_to(ROOT).as_posix()}: schema not found for {ref}"]
    return [
        f"{path.relative_to(ROOT).as_posix()}: {error}"
        for error in validate_node(schema, data, "$", schemas=schemas, root_schema=schema)
    ]


def provider_ids(registry: dict[str, Any]) -> set[str]:
    return {
        str(provider.get("provider_id") or "")
        for provider in registry.get("providers", [])
        if isinstance(provider, dict)
    }


def registry_workers(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    workers: dict[str, dict[str, Any]] = {}
    for worker in registry.get("workers", []):
        if not isinstance(worker, dict):
            continue
        worker_id = str(worker.get("worker_id") or "").strip()
        if worker_id:
            workers[worker_id] = worker
    return workers


def validate_boundaries(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    registry_path = root / "agents" / "skill-provider-registry.public.json"
    worker_registry_path = root / "agents" / "worker-registry.public.json"
    bindings_path = root / "agents" / "hermes-profile-bindings.public.json"
    profiles_path = root / "agents" / "worker-profiles.public.json"
    aliases_path = root / "agents" / "profile-compatibility-aliases.public.json"
    resolution_path = root / "templates" / "skill-ref-resolution-report.json"

    for path in (registry_path, worker_registry_path, aliases_path, resolution_path):
        if not path.exists():
            errors.append(f"{path.relative_to(root).as_posix()}: missing")
        else:
            errors.extend(validate_schema(path))

    if (
        not registry_path.exists()
        or not worker_registry_path.exists()
        or not bindings_path.exists()
        or not profiles_path.exists()
        or not aliases_path.exists()
    ):
        return errors

    registry = load_json(registry_path)
    workers = registry_workers(load_json(worker_registry_path))
    bindings = load_json(bindings_path).get("bindings", {})
    profiles = load_json(profiles_path).get("profiles", {})
    aliases = load_json(aliases_path).get("aliases", [])
    known_providers = provider_ids(registry)

    for worker_id, binding in sorted(bindings.items()):
        if not isinstance(binding, dict):
            continue
        for skill_ref in binding.get("skill_refs", []):
            if str(skill_ref) not in known_providers:
                errors.append(f"{worker_id}: skill_ref {skill_ref} is not in skill-provider-registry.public.json")
        if binding.get("can_mutate_card_state") is not False:
            errors.append(f"{worker_id}: can_mutate_card_state must stay false; mutations go through reducer/adapter")

    for worker_id, worker in sorted(workers.items()):
        if any(marker in worker_id for marker in AUTHORITY_SUGGESTING_WORKER_ID_MARKERS):
            authority_text = str(worker.get("authority_max") or "").lower()
            if "cannot" not in authority_text:
                errors.append(
                    f"{worker_id}: authority-suggesting worker id requires authority_max with explicit cannot boundary"
                )
        if worker_id not in profiles:
            errors.append(f"{worker_id}: worker-registry entry has no worker profile")
        if worker_id not in bindings:
            errors.append(f"{worker_id}: worker-registry entry has no Hermes profile binding")

    for worker_id, profile in sorted(profiles.items()):
        if not isinstance(profile, dict):
            continue
        authority = profile.get("authority") if isinstance(profile.get("authority"), dict) else {}
        must_not = " ".join(str(item).lower() for item in authority.get("must_not", []))
        missing = [marker for marker in FORBIDDEN_AGENT_AUTHORITY_MARKERS if marker not in must_not]
        if missing:
            errors.append(f"{worker_id}: profile must_not is missing authority boundary markers: {', '.join(missing)}")
        operating_rules = " ".join(str(item).lower() for item in profile.get("operating_rules", []))
        if "outside the deterministic phase graph" in operating_rules and "must_not" not in authority:
            errors.append(f"{worker_id}: route authority language belongs in authority.must_not, not only operating rules")

    for index, alias in enumerate(aliases):
        if not isinstance(alias, dict):
            errors.append(f"profile-compatibility-aliases[{index}]: alias must be object")
            continue
        legacy_id = str(alias.get("legacy_id") or "").strip()
        target_worker_id = str(alias.get("target_worker_id") or "").strip()
        status = str(alias.get("status") or "").strip()
        if status not in {"removed_alias", "blocked_alias"}:
            if target_worker_id not in workers:
                errors.append(f"{legacy_id}: alias target_worker_id {target_worker_id} is not in worker registry")
            if target_worker_id not in profiles:
                errors.append(f"{legacy_id}: alias target_worker_id {target_worker_id} has no worker profile")
            if target_worker_id not in bindings:
                errors.append(f"{legacy_id}: alias target_worker_id {target_worker_id} has no Hermes binding")
        if "gerente" in legacy_id.lower() and status != "deprecated_alias":
            errors.append(f"{legacy_id}: human-facing manager alias must stay deprecated; it is not route authority")

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    errors = validate_boundaries(args.root)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
