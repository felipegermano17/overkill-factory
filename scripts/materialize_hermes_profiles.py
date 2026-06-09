#!/usr/bin/env python3
"""Materialize Hermes runtime profiles from the public worker registry."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_BUILDERS = [
    "frontend-builder",
    "backend-api-builder",
    "data-persistence-builder",
    "solana-quasar-builder",
    "solana-quasar-qa-engineer",
    "wallet-transaction-builder",
    "integration-builder",
    "test-automation-builder",
    "infra-devops-builder",
    "agent-runtime-builder",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def as_list(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def bullets(items: object) -> str:
    values = as_list(items)
    if not values:
        return "- none"
    return "\n".join(f"- {item}" for item in values)


def block(title: str, body: str) -> str:
    return f"## {title}\n\n{body.strip()}\n"


def render_soul(worker: dict, binding: dict) -> str:
    activation = worker.get("activation", {})
    authority = worker.get("authority", {})
    tool_policy = worker.get("tool_policy", {})
    input_contract = worker.get("input_contract", {})
    output_contract = worker.get("output_contract", {})
    evidence_contract = worker.get("evidence_contract", {})
    review_contract = worker.get("review_contract", {})
    handoff_contract = worker.get("handoff_contract", {})
    understanding_contract = worker.get("understanding_contract", {})
    failure_contract = worker.get("failure_contract", {})
    promotion_contract = worker.get("promotion_contract", {})
    dispatch_policy = binding.get("dispatch_queue_policy", {})

    parts = [
        f"# {worker.get('display_name', worker['worker_id'])}",
        block("Identity", str(worker.get("identity", ""))),
        block("Mission", str(worker.get("mission", ""))),
        block("Operating Rules", bullets(worker.get("operating_rules"))),
        block(
            "Activation",
            "\n".join(
                [
                    f"Phases: {', '.join(as_list(activation.get('phases')))}",
                    "",
                    f"Surfaces: {', '.join(as_list(activation.get('surfaces')))}",
                    "",
                    f"Risk floor: {activation.get('risk_floor', 'R0')}",
                    "",
                    "Triggers:",
                    bullets(activation.get("trigger_words")),
                ]
            ),
        ),
        block(
            "Authority",
            "\n".join(
                [
                    "May:",
                    bullets(authority.get("may")),
                    "",
                    "Must not:",
                    bullets(authority.get("must_not")),
                    "",
                    "Human gate required when:",
                    bullets(authority.get("human_gate_required_when")),
                ]
            ),
        ),
        block(
            "Tool Policy",
            "\n".join(
                [
                    "Allowed:",
                    bullets(tool_policy.get("allowed")),
                    "",
                    "Forbidden:",
                    bullets(tool_policy.get("forbidden")),
                    "",
                    f"Runtime notes: {tool_policy.get('runtime_notes', 'Use only tools allowed by the card contract.')}",
                ]
            ),
        ),
        block(
            "Hermes Binding",
            "\n".join(
                [
                    f"Queue source of truth: {dispatch_policy.get('source_of_truth', 'factoryctl.worker_queue_class')}",
                    "",
                    f"Default queue policy: {dispatch_policy.get('default_queue', 'blocking-before-done')}",
                    "",
                    "Allowed effective queues:",
                    bullets(dispatch_policy.get("allowed_effective_queues")),
                    "",
                    f"Result schema: {binding.get('result_schema', 'schemas/worker-result.schema.json')}",
                    "",
                    f"Receipt field: {binding.get('receipt_field', output_contract.get('receipt_field', 'worker_result'))}",
                    "",
                    "Skills:",
                    bullets(binding.get("skill_refs")),
                    "",
                    f"Can mutate card state: {str(binding.get('can_mutate_card_state', False)).lower()}",
                    "",
                    "Card state mutation: forbidden directly; adapter owns state mutation.",
                ]
            ),
        ),
        block(
            "Input Contract",
            "\n".join(
                [
                    "Required fields:",
                    bullets(input_contract.get("required")),
                    "",
                    "Refuse if missing:",
                    bullets(input_contract.get("refuse_if_missing")),
                ]
            ),
        ),
        block(
            "Output Contract",
            "\n".join(
                [
                    f"Receipt field: {output_contract.get('receipt_field', binding.get('receipt_field', 'worker_result'))}",
                    "",
                    "Required sections:",
                    bullets(output_contract.get("required_sections")),
                    "",
                    f"Done definition: {output_contract.get('done_definition', 'Produce a schema-shaped worker result with evidence refs.')}",
                ]
            ),
        ),
        block(
            "Evidence",
            "\n".join(
                [
                    f"Trust floor: {evidence_contract.get('trust_floor', 'product_specific')}",
                    "",
                    "Required refs:",
                    bullets(evidence_contract.get("required_refs")),
                    "",
                    "Not valid evidence:",
                    bullets(evidence_contract.get("not_valid_evidence")),
                ]
            ),
        ),
        block(
            "Review",
            "\n".join(
                [
                    f"Mode: {review_contract.get('reviewer_mode', 'independent_required')}",
                    f"Boundary: {review_contract.get('review_boundary', 'Review only this worker output and evidence.')}",
                    f"Rerun required: {str(review_contract.get('rerun_required', True))}",
                ]
            ),
        ),
        block(
            "Handoff",
            "\n".join(
                [
                    "Required when:",
                    bullets(handoff_contract.get("required_when")),
                    "",
                    "Include:",
                    bullets(handoff_contract.get("include")),
                ]
            ),
        ),
        block(
            "Operator Understanding",
            "\n".join(
                [
                    "Required when:",
                    bullets(understanding_contract.get("required_when")),
                    "",
                    "Must record:",
                    bullets(understanding_contract.get("must_record")),
                ]
            ),
        ),
        block(
            "Failure Policy",
            "\n".join(
                [
                    f"Retry limit: {failure_contract.get('retry_limit', 3)}",
                    f"First failure: {failure_contract.get('after_first_failure', 'Diagnose the failure before changing more.')}",
                    f"Second failure: {failure_contract.get('after_second_failure', 'Write a bounded fix packet.')}",
                    f"Third failure: {failure_contract.get('after_third_failure', 'Stop and hand off with evidence.')}",
                ]
            ),
        ),
        block(
            "Promotion",
            "\n".join(
                [
                    "Closed when:",
                    bullets(promotion_contract.get("closed_when")),
                    "",
                    "Demote when:",
                    bullets(promotion_contract.get("demote_when")),
                ]
            ),
        ),
        block(
            "Public Safety",
            str(
                worker.get(
                    "public_safety_notes",
                    "Never include credentials, private paths or internal product data in public receipts.",
                )
            ),
        ),
    ]

    return "\n".join(parts).strip() + "\n"


def yaml_description(description: str) -> str:
    return "description: " + json.dumps(description, ensure_ascii=True) + "\n" + "description_auto: false\n"


def create_profile_with_cli(
    hermes_bin: Path,
    profile: str,
    source_profile: str,
    description: str,
    env: dict[str, str],
    apply: bool,
) -> None:
    cmd = [
        str(hermes_bin),
        "profile",
        "create",
        "--clone",
        "--clone-from",
        source_profile,
        "--description",
        description,
        profile,
    ]
    if not apply:
        print("DRY-RUN create:", " ".join(cmd))
        return
    subprocess.run(cmd, check=True, env=env)


def copy_minimum_profile(source_dir: Path, target_dir: Path, apply: bool) -> None:
    if not apply:
        print(f"DRY-RUN copy minimal profile files from {source_dir.name} to {target_dir.name}")
        return
    target_dir.mkdir(parents=True, exist_ok=True)
    for name in [".env", "config.yaml"]:
        src = source_dir / name
        if src.exists():
            shutil.copy2(src, target_dir / name)


def copy_runtime_auth(source_dir: Path, target_dir: Path, apply: bool) -> None:
    src = source_dir / "auth.json"
    if not src.exists():
        return
    if not apply:
        print(f"DRY-RUN copy runtime auth from {source_dir.name} to {target_dir.name}")
        return
    shutil.copy2(src, target_dir / "auth.json")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--profiles-dir", type=Path, required=True)
    parser.add_argument("--source-profile", default="implementation-worker")
    parser.add_argument("--hermes-bin", type=Path)
    parser.add_argument("--workers", nargs="+", default=DEFAULT_BUILDERS)
    parser.add_argument("--copy-auth-from-source", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    repo_root = args.repo_root.resolve()
    registry = load_json(repo_root / "agents" / "worker-profiles.public.json")
    bindings_doc = load_json(repo_root / "agents" / "hermes-profile-bindings.public.json")
    profiles = registry.get("profiles", {})
    bindings = bindings_doc.get("bindings", {})

    profiles_dir = args.profiles_dir
    source_dir = profiles_dir / args.source_profile
    if not source_dir.exists():
        print(f"ERROR: source profile not found: {args.source_profile}", file=sys.stderr)
        return 2

    env = os.environ.copy()
    if "HERMES_HOME" not in env:
        env["HERMES_HOME"] = str(profiles_dir.parent)
    if "HOME" not in env:
        env["HOME"] = str(profiles_dir.parent)

    changed: list[str] = []
    for worker_id in args.workers:
        worker = profiles.get(worker_id)
        binding = bindings.get(worker_id)
        if not worker:
            print(f"ERROR: worker missing from registry: {worker_id}", file=sys.stderr)
            return 3
        if not binding:
            print(f"ERROR: worker missing from Hermes bindings: {worker_id}", file=sys.stderr)
            return 4

        profile_name = binding.get("hermes_profile_name", worker_id)
        profile_dir = profiles_dir / profile_name
        description = f"{worker.get('display_name', profile_name)} - {worker.get('mission', '')}"

        if not profile_dir.exists():
            if args.hermes_bin:
                create_profile_with_cli(args.hermes_bin, profile_name, args.source_profile, description, env, args.apply)
            else:
                copy_minimum_profile(source_dir, profile_dir, args.apply)

        if args.apply:
            profile_dir.mkdir(parents=True, exist_ok=True)
            (profile_dir / "profile.yaml").write_text(yaml_description(description), encoding="utf-8")
            (profile_dir / "SOUL.md").write_text(render_soul(worker, binding), encoding="utf-8")
            if not (profile_dir / "config.yaml").exists():
                src = source_dir / "config.yaml"
                if src.exists():
                    shutil.copy2(src, profile_dir / "config.yaml")
            if args.copy_auth_from_source:
                copy_runtime_auth(source_dir, profile_dir, args.apply)
        else:
            print(f"DRY-RUN write SOUL.md/profile.yaml for {profile_name}")
            if args.copy_auth_from_source:
                copy_runtime_auth(source_dir, profile_dir, args.apply)

        changed.append(profile_name)

    print(json.dumps({"apply": args.apply, "profiles": changed}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
