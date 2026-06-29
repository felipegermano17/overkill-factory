#!/usr/bin/env python3
"""Executable audit for Overkill Factory GitHub issue history patterns.

The raw issue snapshot is private/local. Public artifacts keep only aggregate
counts, themes, and representative public issue refs. This audit turns known
issue-history failures into anti-regression requirements for the upcoming master
update plan.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY = ROOT / "templates" / "factory-github-issue-pattern-audit-registry.json"
DEFAULT_OUT = ROOT / ".tmp" / "factory-github-issue-pattern-audit.json"
DEFAULT_MD = ROOT / ".tmp" / "factory-github-issue-pattern-audit.md"

REQUIRED_THEMES = {
    "operator_ux_friction",
    "autonomy_idle_stop",
    "runtime_kanban_worker",
    "evidence_truth_overclaim",
    "method_product_architecture",
    "security_release_authority",
    "capability_provider_agent",
    "public_docs_onboarding",
    "product_quality_surface",
    "velocity_cost_loop_control",
}
REQUIRED_OPEN_ISSUES = {419, 529, 531}
REQUIRED_MASTER_REQUIREMENT_TERMS = [
    "manager-only",
    "progress",
    "human gates",
    "no-idle",
    "worker packets",
    "evidence readback",
    "Product SOT",
    "Hermes Worker Runtime OS",
    "capability acquisition",
    "Solana AI Kit",
    "security/release authority",
    "public/private evidence",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _require(condition: bool, errors: list[str], message: str) -> None:
    if not condition:
        errors.append(message)


def audit(registry: dict[str, Any], snapshot: dict[str, Any] | None = None) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    _require(registry.get("record_type") == "factory_github_issue_pattern_audit_registry", errors, "$.record_type must be factory_github_issue_pattern_audit_registry")

    source_policy = registry.get("source_policy", {}) if isinstance(registry.get("source_policy"), dict) else {}
    _require(source_policy.get("live_github_issues_inspected") is True, errors, "$.source_policy.live_github_issues_inspected must be true")
    _require(source_policy.get("raw_issue_snapshot_private") is True, errors, "$.source_policy.raw_issue_snapshot_private must be true")
    _require(source_policy.get("raw_issue_bodies_committed") is False, errors, "$.source_policy.raw_issue_bodies_committed must be false")
    _require(source_policy.get("public_registry_uses_representative_refs_only") is True, errors, "$.source_policy.public_registry_uses_representative_refs_only must be true")

    summary = registry.get("issue_snapshot_summary", {}) if isinstance(registry.get("issue_snapshot_summary"), dict) else {}
    issue_count = int(summary.get("issue_count") or 0)
    open_count = int(summary.get("open_count") or 0)
    closed_count = int(summary.get("closed_count") or 0)
    _require(issue_count >= 250, errors, "$.issue_snapshot_summary.issue_count must reflect the full fetched issue history, expected >= 250")
    _require(issue_count == open_count + closed_count, errors, "$.issue_snapshot_summary issue_count must equal open_count + closed_count")
    open_numbers = {
        int(str(issue["number"]))
        for issue in _list(summary.get("open_issues"))
        if isinstance(issue, dict) and issue.get("number") is not None
    }
    _require(REQUIRED_OPEN_ISSUES.issubset(open_numbers), errors, "$.issue_snapshot_summary.open_issues must include #419 #529 #531")

    if snapshot is not None:
        _require(snapshot.get("issue_count") == issue_count, errors, "private snapshot issue_count does not match public summary")
        snapshot_open = {
            int(str(issue["number"]))
            for issue in _list(snapshot.get("issues"))
            if isinstance(issue, dict) and issue.get("state") == "open" and issue.get("number") is not None
        }
        _require(snapshot_open == open_numbers, errors, "private snapshot open issues do not match public summary")

    themes = _list(registry.get("issue_pattern_themes"))
    theme_keys = {str(theme.get("theme_key")) for theme in themes if isinstance(theme, dict)}
    missing_themes = sorted(REQUIRED_THEMES - theme_keys)
    _require(not missing_themes, errors, "$.issue_pattern_themes missing required themes: " + ", ".join(missing_themes))
    for theme in themes:
        if not isinstance(theme, dict):
            errors.append("$.issue_pattern_themes entries must be objects")
            continue
        key = theme.get("theme_key")
        _require(int(theme.get("issue_count") or 0) >= 1, errors, f"$.issue_pattern_themes[{key}].issue_count must be >= 1")
        _require(theme.get("must_never_happen_again") is True, errors, f"$.issue_pattern_themes[{key}].must_never_happen_again must be true")
        _require(len(_list(theme.get("representative_issues"))) >= 1, errors, f"$.issue_pattern_themes[{key}].representative_issues must not be empty")
        req_text = "\n".join(str(r) for r in _list(theme.get("anti_regression_requirements"))).lower()
        if key == "operator_ux_friction":
            for term in ("manager-only", "artifact-first", "pt-br", "human gate"):
                _require(term in req_text, errors, f"operator_ux_friction requirements must include {term}")
        if key == "autonomy_idle_stop":
            _require("no-idle" in req_text and "deterministic" in req_text, errors, "autonomy_idle_stop requirements must include deterministic no-idle behavior")

    requirements = _list(registry.get("master_plan_requirements"))
    req_text = "\n".join(str(r) for r in requirements).lower()
    _require(len(requirements) >= 10, errors, "$.master_plan_requirements must have at least 10 requirements")
    for term in REQUIRED_MASTER_REQUIREMENT_TERMS:
        _require(term.lower() in req_text, errors, f"$.master_plan_requirements missing term {term}")

    os_mapping = registry.get("os_mapping", {}) if isinstance(registry.get("os_mapping"), dict) else {}
    for theme_key in REQUIRED_THEMES:
        _require(theme_key in os_mapping and len(_list(os_mapping.get(theme_key))) >= 1, errors, f"$.os_mapping missing OS mapping for {theme_key}")

    acceptance = registry.get("acceptance", {}) if isinstance(registry.get("acceptance"), dict) else {}
    _require(acceptance.get("audit_created") is True, errors, "$.acceptance.audit_created must be true")
    _require(acceptance.get("all_issue_history_summarized") is True, errors, "$.acceptance.all_issue_history_summarized must be true")
    _require(acceptance.get("user_experience_patterns_preserved") is True, errors, "$.acceptance.user_experience_patterns_preserved must be true")
    _require(acceptance.get("master_plan_next") is True, errors, "$.acceptance.master_plan_next must be true")

    anti_regression_count = sum(len(_list(theme.get("anti_regression_requirements"))) for theme in themes if isinstance(theme, dict))
    p0_count = sum(1 for theme in themes if isinstance(theme, dict) and theme.get("severity") == "P0")
    result = "PASS" if not errors else "FAIL"
    return {
        "schema": "factory_github_issue_pattern_audit.v1",
        "result": result,
        "score": 100 if result == "PASS" else max(0, 100 - 10 * len(errors)),
        "summary": {
            "errors": len(errors),
            "source_issue_count": issue_count,
            "open_count": open_count,
            "closed_count": closed_count,
            "theme_count": len(themes),
            "p0_theme_count": p0_count,
            "anti_regression_requirement_count": anti_regression_count,
        },
        "theme_keys": sorted(theme_keys),
        "open_issue_numbers": sorted(open_numbers),
        "errors": errors,
        "warnings": warnings,
        "next_step": "feed these anti-regression requirements into the master factory update plan",
    }


def write_markdown(report: dict[str, Any], registry: dict[str, Any], path: Path) -> None:
    lines: list[str] = []
    lines.append("# Factory GitHub Issue Pattern Audit")
    lines.append("")
    lines.append(f"Result: {report['result']}")
    lines.append(f"Score: {report['score']}")
    lines.append("")
    lines.append("This audit summarizes known GitHub issue failure patterns so the master plan does not reintroduce them.")
    lines.append("Raw issue bodies are not committed; this public artifact uses aggregate counts and representative public issue refs.")
    lines.append("")
    s = report["summary"]
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Source issues inspected: {s['source_issue_count']}")
    lines.append(f"- Open/closed: {s['open_count']}/{s['closed_count']}")
    lines.append(f"- Themes: {s['theme_count']}")
    lines.append(f"- Anti-regression requirements: {s['anti_regression_requirement_count']}")
    lines.append(f"- Open issues needing current attention: {', '.join('#'+str(n) for n in report['open_issue_numbers'])}")
    lines.append("")
    lines.append("## Themes")
    lines.append("")
    for theme in registry["issue_pattern_themes"]:
        lines.append(f"- {theme['name']} (`{theme['theme_key']}`): {theme['issue_count']} issues / {theme['severity']}")
        lines.append(f"  - pattern: {theme['pattern']}")
        lines.append(f"  - user harm: {theme['user_harm']}")
        lines.append(f"  - root cause: {theme['root_cause']}")
        refs = ", ".join(f"#{issue['number']}" for issue in theme["representative_issues"][:8])
        lines.append(f"  - representative issues: {refs}")
        lines.append("  - anti-regression requirements:")
        for requirement in theme["anti_regression_requirements"]:
            lines.append(f"    - {requirement}")
    lines.append("")
    lines.append("## Master Plan Requirements")
    lines.append("")
    for requirement in registry["master_plan_requirements"]:
        lines.append(f"- {requirement}")
    if report["errors"]:
        lines.append("")
        lines.append("## Errors")
        lines.append("")
        for error in report["errors"]:
            lines.append(f"- {error}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--snapshot", type=Path, default=None, help="Optional private local raw GitHub issue snapshot for count cross-check")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--markdown", type=Path, default=DEFAULT_MD)
    args = parser.parse_args(argv)

    registry = load_json(args.registry)
    snapshot = load_json(args.snapshot) if args.snapshot else None
    report = audit(registry, snapshot=snapshot)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    write_markdown(report, registry, args.markdown)
    print(f"Wrote {args.out}")
    print(f"Wrote {args.markdown}")
    print(report["result"])
    return 0 if report["result"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
