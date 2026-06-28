#!/usr/bin/env python3
"""Validate live Hermes profile guardrails for Overkill Factory workers."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_SKILL = ROOT / "skills" / "codex" / "overkill-factory" / "SKILL.md"
WORKER_PROFILES = ROOT / "agents" / "worker-profiles.public.json"

CANONICAL_START_PHRASES = [
    "Mandatory Factory Start",
    "factory_bridge_source_envelope",
    "factory_bridge_start_request",
    "materialize-bridge-start",
    "factory_start_path=true",
]

PROFILE_SOUL_PHRASES = [
    "HARD RULE: Kanban worker runtime contract",
    "executes only the card contract and materialized metadata delivered by Hermes Kanban",
    "must not choose phase, gate, route, board, parent/child graph, next card",
    "lacks `factory_start_path` proof",
    "block as a factory integration defect",
]

PROFILE_INTAKE_PHRASES = [
    "HARD RULE: deterministic factory start for new projects",
    "materialize-bridge-start",
    "Direct `hermes kanban boards create`, `hermes kanban create`, or agent-authored",
]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def require_phrases(path: Path, phrases: list[str], label: str, errors: list[str]) -> None:
    if not path.exists():
        errors.append(f"{label}: missing file {path}")
        return
    text = read_text(path)
    for phrase in phrases:
        if phrase not in text:
            errors.append(f"{label}: {path} missing phrase: {phrase}")


def validate_repo(errors: list[str]) -> None:
    require_phrases(CANONICAL_SKILL, CANONICAL_START_PHRASES, "canonical overkill skill", errors)
    if not WORKER_PROFILES.exists():
        errors.append(f"worker profiles registry missing: {WORKER_PROFILES}")
        return
    data = json.loads(WORKER_PROFILES.read_text(encoding="utf-8"))
    profiles_raw = data.get("profiles") if isinstance(data, dict) else None
    if isinstance(profiles_raw, dict):
        profiles = list(profiles_raw.items())
    elif isinstance(profiles_raw, list):
        profiles = [(str(idx), profile) for idx, profile in enumerate(profiles_raw)]
    else:
        profiles = []
    if not profiles:
        errors.append("worker profiles registry has no profiles")
        return
    for key, profile in profiles:
        if not isinstance(profile, dict):
            errors.append(f"worker profile {key} is not an object")
            continue
        name = str(profile.get("profile") or profile.get("name") or profile.get("worker_id") or key)
        authority = json.dumps(profile.get("authority") or profile.get("authority_contract") or profile, ensure_ascii=False)
        if "choose phase outside the deterministic phase graph" not in authority:
            errors.append(f"worker profile {name}: missing deterministic phase graph prohibition")


def validate_profiles_root(profiles_root: Path, errors: list[str]) -> None:
    if not profiles_root.exists():
        errors.append(f"profiles root does not exist: {profiles_root}")
        return
    soul_paths = sorted(profiles_root.glob("*/SOUL.md"))
    if not soul_paths:
        errors.append(f"profiles root has no SOUL.md files: {profiles_root}")
        return
    for soul in soul_paths:
        profile = soul.parent.name
        if profile == "default":
            continue
        require_phrases(soul, PROFILE_SOUL_PHRASES, f"profile {profile} SOUL", errors)
    for skill in sorted(profiles_root.glob("*/skills/overkill-factory/SKILL.md")):
        require_phrases(skill, CANONICAL_START_PHRASES, f"profile-local overkill skill {skill.parent.parent.parent.name}", errors)
    for skill in sorted(profiles_root.glob("*/skills/operations/overkill-factory-product-intake/SKILL.md")):
        require_phrases(skill, PROFILE_INTAKE_PHRASES, f"profile-local intake skill {skill.parent.parent.parent.parent.name}", errors)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profiles-root", type=Path, help="Hermes profiles root to validate, e.g. /srv/hermes/home/profiles")
    args = parser.parse_args(argv)

    errors: list[str] = []
    validate_repo(errors)
    if args.profiles_root:
        validate_profiles_root(args.profiles_root, errors)

    if errors:
        print("Hermes profile runtime contract validation FAILED:")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Hermes profile runtime contract validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
