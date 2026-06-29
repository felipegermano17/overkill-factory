#!/usr/bin/env python3
"""Executable audit for Overkill Factory operator UI/UX excellence.

This audit focuses on the human product-owner experience through Telegram and
Discord, mediated by the factory manager/gerente. It intentionally excludes the
unfinished legacy frontend for now. The goal is not to claim the current runtime
UX is complete; the goal is to make the target experience and gaps executable,
validated and impossible to regress silently.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-operator-ui-ux-excellence-registry.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-operator-ui-ux-excellence-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-operator-ui-ux-excellence-audit.md"

REQUIRED_CHANNELS = {"telegram", "discord"}
REQUIRED_MANAGER_RESPONSIBILITIES = {
    "external_signal_intake",
    "factory_start_and_kanban_projection",
    "progress_reporting",
    "human_gate_delivery",
}
REQUIRED_PROGRESS_FIELDS = {
    "percent_complete",
    "done_since_last_update",
    "currently_executing",
    "remaining_work",
    "blockers_or_waiting_on",
    "next_human_gate_if_any",
}
REQUIRED_GATE_ASSETS = {
    "short_plain_language_message",
    "pdf_document",
    "decision_options",
    "scope_and_forbidden_scope",
    "delivery_receipt",
}
FORBIDDEN_GATE_PATTERNS = {
    "json_dump_as_primary_decision_surface",
    "raw_markdown_as_primary_decision_surface",
    "approval_question_without_package",
}
REQUIRED_PILLARS = {
    "conversational_signal_intake",
    "manager_single_bridge",
    "telegram_primary_experience",
    "discord_target_experience",
    "progress_visibility",
    "autonomy_without_bureaucracy",
    "human_gate_decision_package",
    "beautiful_pdf_delivery",
    "video_animation_explainers",
    "plain_language_pt_br",
    "mobile_first_attachment_ux",
    "delivery_receipts_and_ack",
    "decision_options_and_scope",
    "kanban_projection_not_board_dump",
    "failure_and_blocker_experience",
    "cross_channel_consistency",
    "manager_runtime_observability",
}


def load_registry(path: Path = DEFAULT_REGISTRY) -> dict[str, Any]:
    return json.loads(path.read_text())


def as_set(values: Any) -> set[str]:
    if not isinstance(values, list):
        return set()
    return {str(v) for v in values}


def require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def audit(registry: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    require(registry.get("record_type") == "factory_operator_ui_ux_excellence_registry", errors, "$.record_type must be factory_operator_ui_ux_excellence_registry")

    scope = registry.get("audit_scope", {})
    channels_in_scope = as_set(scope.get("primary_channels"))
    require(REQUIRED_CHANNELS.issubset(channels_in_scope), errors, "$.audit_scope.primary_channels must include telegram and discord")
    require(scope.get("front_end_currently_out_of_scope") is True, errors, "$.audit_scope.front_end_currently_out_of_scope must be true for this audit")

    channel_entries = registry.get("operator_channels", [])
    channel_names = {entry.get("channel") for entry in channel_entries if isinstance(entry, dict)}
    require(REQUIRED_CHANNELS.issubset(channel_names), errors, "$.operator_channels must define telegram and discord")
    for entry in channel_entries:
        if not isinstance(entry, dict):
            errors.append("$.operator_channels entries must be objects")
            continue
        must_support = as_set(entry.get("must_support"))
        for needed in {"conversational_intake", "progress_notifications", "human_gate_packages", "delivery_receipts"}:
            require(needed in must_support, errors, f"$.operator_channels[{entry.get('channel')}].must_support missing {needed}")

    manager = registry.get("manager_bridge", {})
    require(manager.get("manager_profile") == "overkill-factory-gerente", errors, "$.manager_bridge.manager_profile must be overkill-factory-gerente")
    require(manager.get("user_facing_role") == "single conversational bridge", errors, "$.manager_bridge.user_facing_role must be single conversational bridge")
    responsibilities = as_set(manager.get("responsibilities"))
    missing_resp = sorted(REQUIRED_MANAGER_RESPONSIBILITIES - responsibilities)
    require(not missing_resp, errors, f"$.manager_bridge.responsibilities missing {missing_resp}")
    require(manager.get("direct_worker_chat_required") is False, errors, "$.manager_bridge.direct_worker_chat_required must be false")
    require(manager.get("operator_polling_required") is False, errors, "$.manager_bridge.operator_polling_required must be false")

    progress = registry.get("progress_notification_contract", {})
    progress_fields = as_set(progress.get("required_fields"))
    missing_progress = sorted(REQUIRED_PROGRESS_FIELDS - progress_fields)
    require(not missing_progress, errors, f"$.progress_notification_contract.required_fields missing {missing_progress}")
    require(progress.get("max_silent_minutes_when_running", 999) <= 30, errors, "$.progress_notification_contract.max_silent_minutes_when_running must be <= 30")
    require(progress.get("batch_internal_noise") is True, errors, "$.progress_notification_contract.batch_internal_noise must be true")
    require(progress.get("notify_on_every_worker_event") is False, errors, "$.progress_notification_contract.notify_on_every_worker_event must be false")

    gate = registry.get("human_gate_experience_contract", {})
    require(gate.get("human_gate_only_when_material_decision_required") is True, errors, "$.human_gate_experience_contract.human_gate_only_when_material_decision_required must be true")
    require(gate.get("material_before_question_required") is True, errors, "$.human_gate_experience_contract.material_before_question_required must be true")
    require(gate.get("primary_decision_artifact") == "beautiful_pdf", errors, "$.human_gate_experience_contract.primary_decision_artifact must be beautiful_pdf")
    gate_assets = as_set(gate.get("required_assets"))
    missing_assets = sorted(REQUIRED_GATE_ASSETS - gate_assets)
    require(not missing_assets, errors, f"$.human_gate_experience_contract.required_assets missing {missing_assets}")
    optional_assets = as_set(gate.get("optional_assets"))
    require("video_explainer_mp4" in optional_assets, errors, "$.human_gate_experience_contract.optional_assets must include video_explainer_mp4")
    video_paths = as_set(gate.get("recommended_video_paths"))
    require("manim_animation" in video_paths, errors, "$.human_gate_experience_contract.recommended_video_paths must include manim_animation")
    forbidden_patterns = as_set(gate.get("forbidden_patterns"))
    missing_forbidden = sorted(FORBIDDEN_GATE_PATTERNS - forbidden_patterns)
    require(not missing_forbidden, errors, f"$.human_gate_experience_contract.forbidden_patterns missing {missing_forbidden}")

    pillars = registry.get("pillar_coverage", [])
    pillar_keys = {entry.get("key") for entry in pillars if isinstance(entry, dict)}
    missing_pillars = sorted(REQUIRED_PILLARS - pillar_keys)
    require(not missing_pillars, errors, f"$.pillar_coverage missing {missing_pillars}")
    for entry in pillars:
        if not isinstance(entry, dict):
            errors.append("$.pillar_coverage entries must be objects")
            continue
        status = entry.get("status")
        if status in {"partial", "missing"} and not entry.get("gap_or_upgrade"):
            errors.append(f"$.pillar_coverage[{entry.get('key')}].gap_or_upgrade is required for partial/missing")

    acceptance = registry.get("acceptance", {})
    require(acceptance.get("frontend_excluded") is True, errors, "$.acceptance.frontend_excluded must be true")
    require(acceptance.get("telegram_and_discord_considered") is True, errors, "$.acceptance.telegram_and_discord_considered must be true")
    require(acceptance.get("pdf_gate_required") is True, errors, "$.acceptance.pdf_gate_required must be true")
    require(acceptance.get("video_explainer_recommended") is True, errors, "$.acceptance.video_explainer_recommended must be true")
    runtime_claim = str(acceptance.get("runtime_claim", "")).lower()
    require("partial" in runtime_claim or "not" in runtime_claim, errors, "$.acceptance.runtime_claim must avoid claiming complete runtime UX")

    partial_or_missing = [entry.get("key") for entry in pillars if isinstance(entry, dict) and entry.get("status") in {"partial", "missing"}]
    strong = [entry.get("key") for entry in pillars if isinstance(entry, dict) and entry.get("status") == "strong"]
    if len(partial_or_missing) < 8:
        warnings.append("audit is unexpectedly optimistic; verify runtime delivery before reducing partial gap count")

    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_operator_ui_ux_excellence_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "summary": {
            "errors": len(errors),
            "pillar_count": len(pillars),
            "strong_count": len(strong),
            "partial_or_missing_count": len(partial_or_missing),
            "channel_count": len(channel_entries),
        },
        "operator_channels": sorted(str(ch) for ch in channel_names),
        "manager_profile": manager.get("manager_profile"),
        "frontend_considered": not bool(scope.get("front_end_currently_out_of_scope")),
        "partial_or_missing_pillars": partial_or_missing,
        "errors": errors,
        "warnings": warnings,
        "thesis": scope.get("thesis"),
        "next_capacity_themes": [
            "telegram_progress_cards_and_delivery_receipts",
            "discord_operator_journey_pack",
            "beautiful_pdf_gate_renderer",
            "video_explainer_lane",
            "manager_runtime_observer",
            "mobile_attachment_design_standard",
        ],
    }


def write_markdown(report: dict[str, Any], registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory Operator UI/UX Excellence Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append("")
    lines.append(str(report.get("thesis", "")))
    lines.append("")
    lines.append("## Scope")
    lines.append("")
    lines.append("- Primary path: Telegram")
    lines.append("- Target path: Discord")
    lines.append("- Ignored for now: unfinished legacy frontend")
    lines.append(f"- Manager bridge: {report.get('manager_profile')} / single conversational bridge")
    lines.append("")
    lines.append("## Required UX Contracts")
    lines.append("")
    progress = registry["progress_notification_contract"]
    gate = registry["human_gate_experience_contract"]
    lines.append("Progress updates must include: " + ", ".join(progress["required_fields"]))
    lines.append(f"Max silent minutes while running: {progress['max_silent_minutes_when_running']}")
    lines.append(f"Human gate primary artifact: {gate['primary_decision_artifact']}")
    lines.append("Human gate required assets: " + ", ".join(gate["required_assets"]))
    lines.append("Human gate optional assets: " + ", ".join(gate["optional_assets"]))
    lines.append("Recommended video paths: " + ", ".join(gate["recommended_video_paths"]))
    lines.append("")
    lines.append("## Pillar Coverage")
    lines.append("")
    for entry in registry["pillar_coverage"]:
        lines.append(f"- {entry['name']} (`{entry['key']}`): {entry['status']}")
        lines.append(f"  - goal: {entry['goal']}")
        lines.append(f"  - gap/upgrade: {entry['gap_or_upgrade']}")
    lines.append("")
    if report["errors"]:
        lines.append("## Errors")
        lines.append("")
        for error in report["errors"]:
            lines.append(f"- {error}")
        lines.append("")
    lines.append("## Next Capacity Themes")
    lines.append("")
    for theme in report["next_capacity_themes"]:
        lines.append(f"- {theme}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    registry = load_registry(args.registry)
    report = audit(registry)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, registry, args.markdown)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.markdown}")
    print(report["result"])
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
