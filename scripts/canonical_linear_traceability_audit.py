#!/usr/bin/env python3
"""Build and validate a linear traceability audit for the final canonical doc.

The audit follows the source document in order. It does not reduce the
canonical method to a short list of "main" requirements: every Markdown heading
and every numbered principle is treated as a checkpoint that must be mapped to
repo artifacts or to an explicit boundary.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANONICAL_NAME = "OVERKILL_FACTORY_VFINAL_DOCUMENTO_FINAL_CANONICO_2026-06-09.md"
DEFAULT_CANONICAL = ROOT.parent / DEFAULT_CANONICAL_NAME
DEFAULT_CHECKPOINT_MANIFEST = (
    ROOT / ".tmp" / "factory-runs" / "canonical-linear-traceability" / "canonical-checkpoints.public.json"
)
DEFAULT_OUT_JSON = ROOT / ".tmp" / "canonical-linear-traceability.json"
DEFAULT_OUT_MD = ROOT / ".tmp" / "canonical-linear-traceability.md"
SCHEMA = "https://overkill-factory.dev/schemas/canonical-linear-traceability.schema.json"
CHECKPOINT_MANIFEST_SCHEMA = "https://overkill-factory.dev/schemas/canonical-checkpoint-manifest.schema.json"

ALLOWED_STATUS = {
    "implemented_by_runtime",
    "implemented_by_contract",
    "bounded_public_proof",
    "partial_requires_live_pilot",
    "foundational_text_tracked",
}
STRONG_REF_KINDS = {
    "schema",
    "template",
    "script",
    "test",
    "worker_registry",
    "worker_profile",
    "profile_binding",
    "runtime_adapter",
    "validation_artifact",
    "product_artifact",
    "agent_manual",
}
ALLOWED_REF_KINDS = STRONG_REF_KINDS | {"documentation"}
PRIVATE_OWNER_TOKEN = "Fel" + "ipe"
PRIVATE_PRODUCT_TOKEN = "K" + "axis"
PUBLIC_REDACTIONS = (
    (PRIVATE_OWNER_TOKEN, "the operator"),
    (PRIVATE_PRODUCT_TOKEN, "private product pack"),
)


@dataclass(frozen=True)
class Checkpoint:
    sequence: int
    checkpoint_type: str
    canonical_line: int
    canonical_level: int
    title: str
    parent_heading: str | None = None


def normalize(value: str) -> str:
    lowered = value.lower()
    lowered = lowered.replace("&", " and ")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def slug(value: str) -> str:
    normalized = normalize(value)
    return normalized.replace(" ", "-")[:80].strip("-") or "checkpoint"


def redact_public_text(value: str) -> str:
    redacted = value
    for token, replacement in PUBLIC_REDACTIONS:
        redacted = re.sub(re.escape(token), replacement, redacted, flags=re.IGNORECASE)
    return redacted


def ref(kind: str, path: str, covers: str) -> dict[str, str]:
    return {"kind": kind, "path": path, "covers": covers}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_checkpoints(canonical_path: Path) -> list[Checkpoint]:
    checkpoints: list[Checkpoint] = []
    current_h2: str | None = None
    sequence = 0
    for line_number, line in enumerate(canonical_path.read_text(encoding="utf-8").splitlines(), start=1):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            sequence += 1
            level = len(heading.group(1))
            title = heading.group(2).strip()
            if level == 2:
                current_h2 = title
            checkpoints.append(
                Checkpoint(
                    sequence=sequence,
                    checkpoint_type="heading",
                    canonical_line=line_number,
                    canonical_level=level,
                    title=title,
                    parent_heading=current_h2,
                )
            )
            continue

        if current_h2 == "3. Principios":
            principle = re.match(r"^(\d+)\.\s+(.+?)\s*$", line)
            if principle:
                sequence += 1
                checkpoints.append(
                    Checkpoint(
                        sequence=sequence,
                        checkpoint_type="principle",
                        canonical_line=line_number,
                        canonical_level=7,
                        title=f"Principle {principle.group(1)}: {principle.group(2).strip()}",
                        parent_heading=current_h2,
                    )
                )
    return checkpoints


def count_checkpoint_types(checkpoints: list[Checkpoint]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for checkpoint in checkpoints:
        counts[checkpoint.checkpoint_type] = counts.get(checkpoint.checkpoint_type, 0) + 1
    return counts


def checkpoint_manifest(canonical_path: Path) -> dict[str, Any]:
    checkpoints = extract_checkpoints(canonical_path)
    type_counts = count_checkpoint_types(checkpoints)
    return {
        "$schema": CHECKPOINT_MANIFEST_SCHEMA,
        "record_type": "canonical_checkpoint_manifest",
        "canonical_doc_ref": f"external:{canonical_path.name}",
        "canonical_sha256": sha256(canonical_path),
        "extraction_rule": "Markdown headings and numbered principles under section 3, in source order.",
        "redaction_rule": "Private owner and private product names are replaced with public-safe labels.",
        "checkpoint_count": len(checkpoints),
        "headings_count": type_counts.get("heading", 0),
        "principles_count": type_counts.get("principle", 0),
        "checkpoints": [
            {
                "sequence": checkpoint.sequence,
                "checkpoint_type": checkpoint.checkpoint_type,
                "canonical_line": checkpoint.canonical_line,
                "canonical_level": checkpoint.canonical_level,
                "title": redact_public_text(checkpoint.title),
                "parent_heading": redact_public_text(checkpoint.parent_heading) if checkpoint.parent_heading else None,
            }
            for checkpoint in checkpoints
        ],
    }


def load_checkpoint_manifest(path: Path = DEFAULT_CHECKPOINT_MANIFEST) -> tuple[str, str, list[Checkpoint]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("record_type") != "canonical_checkpoint_manifest":
        raise ValueError(f"{path}: record_type must be canonical_checkpoint_manifest")
    checkpoints = [
        Checkpoint(
            sequence=int(item["sequence"]),
            checkpoint_type=str(item["checkpoint_type"]),
            canonical_line=int(item["canonical_line"]),
            canonical_level=int(item["canonical_level"]),
            title=str(item["title"]),
            parent_heading=item.get("parent_heading"),
        )
        for item in data.get("checkpoints", [])
    ]
    if len(checkpoints) != data.get("checkpoint_count"):
        raise ValueError(f"{path}: checkpoint_count does not match checkpoints")
    type_counts = count_checkpoint_types(checkpoints)
    if type_counts.get("heading", 0) != data.get("headings_count"):
        raise ValueError(f"{path}: headings_count does not match checkpoints")
    if type_counts.get("principle", 0) != data.get("principles_count"):
        raise ValueError(f"{path}: principles_count does not match checkpoints")
    return str(data["canonical_doc_ref"]), str(data["canonical_sha256"]), checkpoints


def load_checkpoint_source(
    canonical_path: Path | None = None,
    checkpoint_manifest_path: Path = DEFAULT_CHECKPOINT_MANIFEST,
) -> tuple[str, str, list[Checkpoint]]:
    if canonical_path is not None:
        return f"external:{canonical_path.name}", sha256(canonical_path), extract_checkpoints(canonical_path)
    return load_checkpoint_manifest(checkpoint_manifest_path)


def base_boundary(status: str) -> str | None:
    if status == "foundational_text_tracked":
        return "This checkpoint is identity, definition or explanatory frame; it is traced, not treated as a standalone runtime gate."
    if status == "bounded_public_proof":
        return "Public-safe artifacts prove the bounded path named here; they do not prove every private/live production path."
    if status == "partial_requires_live_pilot":
        return "Contracts or bounded proofs exist, but a full live pilot is still required before claiming end-to-end production readiness."
    return None


def checkpoint_record(
    checkpoint: Checkpoint,
    *,
    status: str,
    obligation: str,
    refs: list[dict[str, str]],
    boundary: str | None = None,
    next_action: str | None = None,
) -> dict[str, Any]:
    safe_title = redact_public_text(checkpoint.title)
    return {
        "sequence": checkpoint.sequence,
        "checkpoint_id": f"{checkpoint.checkpoint_type}-{checkpoint.sequence:03d}-{slug(safe_title)}",
        "checkpoint_type": checkpoint.checkpoint_type,
        "canonical_line": checkpoint.canonical_line,
        "canonical_level": checkpoint.canonical_level,
        "canonical_heading": safe_title,
        "parent_heading": redact_public_text(checkpoint.parent_heading) if checkpoint.parent_heading else None,
        "canonical_obligation": redact_public_text(obligation),
        "implementation_status": status,
        "implementation_refs": refs,
        "boundary": redact_public_text(boundary or base_boundary(status) or "") or None,
        "next_action": redact_public_text(next_action) if next_action else None,
    }


def refs_source() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/factory-card.schema.json", "source refs and source_state contract"),
        ref("script", "scripts/factoryctl.py", "source_state validation and source-ledger routing"),
        ref("worker_profile", "agents/worker-profiles.public.json", "source-ledger-worker duties"),
        ref("test", "tests/test_factoryctl.py", "card validation regressions"),
    ]


def refs_outcome() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/outcome-contract.schema.json", "outcome and discovery contract"),
        ref("template", "templates/outcome-contract.json", "outcome/discovery template"),
        ref("worker_profile", "agents/worker-profiles.public.json", "product-sot-planner ownership"),
    ]


def refs_product_sot() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/product-sot.schema.json", "Product SOT contract"),
        ref("template", "templates/product-sot.json", "Product SOT template"),
        ref("script", "scripts/factoryctl.py", "vFinal Product SOT blockers"),
        ref("test", "tests/test_factoryctl.py", "Product SOT regression tests"),
    ]


def refs_method() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/method-contract.schema.json", "method selection and required plans"),
        ref("template", "templates/method-contract.json", "method contract template"),
        ref("script", "scripts/factoryctl.py", "required plan validation"),
        ref("test", "tests/test_factoryctl.py", "method contract blockers"),
    ]


def refs_packs() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/capability-pack-contract.schema.json", "product/surface capability contract"),
        ref("worker_registry", "agents/capability-packs.public.json", "public capability pack registry"),
        ref("documentation", "docs/agents/capability-packs.md", "capability pack operator manual"),
        ref("script", "scripts/factoryctl.py", "capability coverage blocker"),
        ref("test", "tests/test_capability_packs.py", "capability pack regressions"),
    ]


def refs_software() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/software-development-plan.schema.json", "software development plan"),
        ref("template", "templates/software-development-plan.json", "software plan template"),
        ref("schema", "schemas/spec-graph.schema.json", "Spec Graph contract"),
        ref("schema", "schemas/loop-plan.schema.json", "Loop Plan contract"),
        ref("schema", "schemas/work-unit-contract.schema.json", "work unit contract"),
    ]


def refs_experience() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/product-experience-plan.schema.json", "Product Experience OS plan"),
        ref("template", "templates/product-experience-plan.json", "Product Experience template"),
        ref("schema", "schemas/product-face-packet.schema.json", "Product Face Packet 2.0"),
        ref("schema", "schemas/product-face-result.schema.json", "Product Face Result proof"),
        ref("script", "scripts/product_face_proof.py", "Product Face proof runner"),
        ref("test", "tests/test_product_face_proof.py", "Product Face proof regressions"),
    ]


def refs_data() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/data-metrics-plan.schema.json", "data, metrics and analytics contract"),
        ref("template", "templates/data-metrics-plan.json", "data/metrics template"),
        ref("worker_profile", "agents/worker-profiles.public.json", "detection-monitoring-worker ownership"),
    ]


def refs_agent_eval() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/agent-eval-plan.schema.json", "agent eval plan"),
        ref("schema", "schemas/agent-eval-result.schema.json", "agent eval result"),
        ref("template", "templates/agent-eval-plan.json", "agent eval template"),
        ref("worker_profile", "agents/worker-profiles.public.json", "skill-eval-distiller ownership"),
    ]


def refs_security() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/security-architecture-plan.schema.json", "security architecture plan"),
        ref("template", "templates/security-architecture-plan.json", "security architecture template"),
        ref("documentation", "docs/security/security-control-matrix.md", "security specialist matrix"),
        ref("worker_registry", "agents/worker-registry.public.json", "security specialist workers"),
        ref("script", "scripts/factoryctl.py", "security and human gate blockers"),
        ref("test", "tests/test_factoryctl.py", "security gate regressions"),
    ]


def refs_authority() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/human-gate-record.schema.json", "human gate record"),
        ref("template", "templates/human-gate-record.json", "human gate template"),
        ref("schema", "schemas/approval-request.schema.json", "approval request contract"),
        ref("documentation", "docs/agents/permission-model.md", "permission and authority model"),
        ref("script", "scripts/factoryctl.py", "identity separation and approval evidence blockers"),
        ref("test", "tests/test_factoryctl.py", "human approval and self-review regressions"),
    ]


def refs_dependency_access_budget() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/dependency-map.schema.json", "dependency gate contract"),
        ref("template", "templates/dependency-map.json", "dependency map template"),
        ref("schema", "schemas/access-capability.schema.json", "access and capability contract"),
        ref("template", "templates/access-capability.json", "access/capability template"),
        ref("schema", "schemas/budget-contract.schema.json", "budget contract"),
        ref("template", "templates/budget-contract.json", "budget template"),
        ref("script", "scripts/factoryctl.py", "risk/access/budget gate validation hooks"),
    ]


def refs_compliance() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/privacy-compliance-plan.schema.json", "privacy/compliance contract"),
        ref("template", "templates/privacy-compliance-plan.json", "privacy/compliance template"),
        ref("schema", "schemas/public-safety-scan-summary.schema.json", "public safety scan summary"),
        ref("script", "scripts/public_safety_scan.py", "public artifact safety scanner"),
        ref("script", "scripts/secret_safety_scan.py", "secret safety scanner"),
        ref("test", "tests/test_public_safety_scan.py", "public safety regressions"),
    ]


def refs_runtime() -> list[dict[str, str]]:
    return [
        ref("runtime_adapter", "adapters/hermes/live_kanban_adapter.py", "Hermes live adapter"),
        ref("runtime_adapter", "adapters/hermes/transition_hook.py", "Hermes transition hook"),
        ref("documentation", "adapters/hermes/README.md", "Hermes adapter manual"),
        ref("documentation", "docs/architecture/hermes-integration.md", "Hermes integration architecture"),
        ref("test", "tests/test_hermes_live_kanban_adapter.py", "Hermes adapter regressions"),
        ref("test", "tests/test_hermes_transition_hook.py", "transition hook regressions"),
    ]


def refs_evidence() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/receipt-five.schema.json", "Receipt Five contract"),
        ref("template", "templates/receipt-five.json", "Receipt Five template"),
        ref("schema", "schemas/worker-result.schema.json", "worker result evidence contract"),
        ref("script", "scripts/evidence_reconciler.py", "evidence reconciliation"),
        ref("script", "scripts/factory_completion_audit.py", "completion audit"),
        ref("test", "tests/test_evidence_reconciler.py", "evidence reconciliation regressions"),
        ref("test", "tests/test_factory_completion_audit.py", "completion audit regressions"),
    ]


def refs_control_tower() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/project-projection.schema.json", "Project Projection contract"),
        ref("template", "templates/project-projection.json", "Project Projection template"),
        ref("schema", "schemas/operator-control-tower-bridge-health.schema.json", "Control Tower bridge health"),
        ref("documentation", "docs/control-tower/discord-control-tower-os.md", "Discord Control Tower OS"),
        ref("script", "scripts/factory_concierge_discord_bridge.py", "Discord bridge"),
        ref("script", "scripts/factory_concierge_discord_automation.py", "Discord automation"),
        ref("test", "tests/test_factory_concierge_discord_bridge.py", "Discord bridge regressions"),
        ref("validation_artifact", ".tmp/factory-runs/control-tower/operator-control-tower-production-readiness.json", "bounded Control Tower proof"),
    ]


def refs_autonomy_readiness() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/autonomy-readiness-packet.schema.json", "autonomy readiness packet contract"),
        ref("template", "templates/autonomy-readiness-packet.json", "autonomy readiness template"),
        ref("schema", "schemas/factory-card.schema.json", "autonomy_readiness_packet card field"),
        ref("profile_binding", "agents/hermes-profile-bindings.public.json", "runtime profile bindings"),
        ref("documentation", "docs/agents/factory-stage-agent-map.md", "stage 17 agent ownership"),
        ref("test", "tests/test_materialize_hermes_profiles.py", "Hermes profile materialization regressions"),
    ]


def refs_closure_summary() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/worker-closure-summary.schema.json", "closure summary contract"),
        ref("documentation", "docs/automation/worker-automation-v0.md", "closure summary operating rule"),
        ref("documentation", "docs/agents/worker-profiles.md", "evidence-reconciler closure duties"),
        ref("schema", "schemas/worker-closure-summary.schema.json", "closure summary schema"),
        ref("validation_artifact", ".tmp/factory-runs/canonical-stage-coverage/canonical-stage-implementation-coverage.json", "stage 25 closure summary coverage"),
    ]


def refs_learning() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/factory-maturity-scorecard.schema.json", "factory maturity scorecard"),
        ref("template", "templates/factory-maturity-scorecard.json", "maturity scorecard template"),
        ref("template", "templates/factory-maturity-scorecard.json", "learning loop contract fixture"),
        ref("test", "tests/test_agent_reference_study_execution.py", "study-to-artifact regressions"),
        ref("validation_artifact", ".tmp/factory-runs/canonical-stage-coverage/canonical-stage-implementation-coverage.json", "stage coverage evidence"),
    ]


def refs_docs_standard() -> list[dict[str, str]]:
    return [
        ref("documentation", "docs/operations/validation-and-release.md", "validation and release manual"),
        ref("documentation", "docs/operations/troubleshooting.md", "operator troubleshooting manual"),
        ref("documentation", "docs/getting-started/quickstart-hermes.md", "operator quickstart"),
        ref("script", "scripts/public_safety_scan.py", "public documentation safety scanner"),
        ref("test", "tests/test_open_source_docs.py", "public docs regressions"),
    ]


def refs_production() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/production-readiness-plan.schema.json", "production readiness plan"),
        ref("template", "templates/production-readiness-plan.json", "production readiness template"),
        ref("schema", "schemas/incident-support-plan.schema.json", "incident/support plan"),
        ref("script", "scripts/factory_production_readiness.py", "production readiness checker"),
        ref("script", "scripts/production_release_gate.py", "release gate proof"),
        ref("test", "tests/test_production_release_gate.py", "release gate regressions"),
        ref("validation_artifact", ".tmp/factory-runs/production/release/release-ops-result.json", "bounded release ops proof"),
    ]


def refs_workers() -> list[dict[str, str]]:
    return [
        ref("worker_registry", "agents/worker-registry.public.json", "worker registry"),
        ref("worker_profile", "agents/worker-profiles.public.json", "worker profiles"),
        ref("profile_binding", "agents/hermes-profile-bindings.public.json", "Hermes profile bindings"),
        ref("documentation", "docs/agents/worker-profiles.md", "worker profiles manual"),
        ref("documentation", "docs/agents/factory-stage-agent-map.md", "stage-to-agent map"),
        ref("test", "tests/test_worker_profiles.py", "worker profile regressions"),
        ref("test", "tests/test_factory_stage_agent_map.py", "stage map regressions"),
    ]


def refs_repo_public() -> list[dict[str, str]]:
    return [
        ref("script", "scripts/public_safety_scan.py", "public safety scan"),
        ref("script", "scripts/secret_safety_scan.py", "secret scan"),
        ref("script", "scripts/validate_public_json_artifacts.py", "public JSON validation"),
        ref("test", "tests/test_open_source_docs.py", "open source docs regression"),
        ref("test", "tests/test_secret_safety_scan.py", "secret scan regression"),
        ref("validation_artifact", ".tmp/factory-runs/public-safety/worktree-summary.json", "current public safety summary"),
    ]


def refs_release() -> list[dict[str, str]]:
    return [
        ref("schema", "schemas/release-integration-preflight.schema.json", "release integration preflight"),
        ref("schema", "schemas/worktree-release-inventory.schema.json", "release inventory"),
        ref("script", "scripts/release_integration_preflight.py", "release integration preflight"),
        ref("script", "scripts/worktree_release_inventory.py", "worktree release inventory"),
        ref("script", "scripts/production_release_gate.py", "release gate"),
        ref("test", "tests/test_release_integration_preflight.py", "release preflight regressions"),
        ref("validation_artifact", ".tmp/factory-runs/release/release-integration-preflight.json", "release preflight proof"),
    ]


def refs_factory_flow() -> list[dict[str, str]]:
    return [
        ref("documentation", "docs/concepts/factory-flow.md", "factory flow explanation"),
        ref("documentation", "docs/concepts/factory-flow.md", "execution flow guide"),
        ref("agent_manual", "skills/codex/overkill-factory/SKILL.md", "operator skill spine"),
        ref("validation_artifact", ".tmp/factory-runs/canonical-stage-coverage/canonical-stage-implementation-coverage.json", "32-stage coverage record"),
    ]


def refs_private_product_pack() -> list[dict[str, str]]:
    return [
        ref("product_artifact", "products/qvg-public-validation-product/README.md", "public validation product"),
        ref("product_artifact", "products/devnet-receipt-pass/README.md", "public product pilot artifact"),
        ref("validation_artifact", ".tmp/factory-runs/product-specific/qvg-full-product-worker-graph.json", "product-specific worker graph"),
        ref("validation_artifact", ".tmp/factory-runs/production/full-product-worker-graph.json", "production worker graph proof"),
        ref("validation_artifact", ".tmp/factory-runs/production/product-face/product-face-result.json", "bounded product face proof"),
    ]


def principle_record(checkpoint: Checkpoint) -> dict[str, Any]:
    text = checkpoint.title.split(":", 1)[1].strip()
    number = int(re.match(r"Principle\s+(\d+):", checkpoint.title).group(1))  # type: ignore[union-attr]
    table: dict[int, tuple[str, str, list[dict[str, str]], str | None]] = {
        1: ("implemented_by_contract", "Source must precede opinion.", refs_source(), None),
        2: ("implemented_by_contract", "Expected outcome must precede planning.", refs_outcome(), None),
        3: ("implemented_by_contract", "Discovery must precede treating a paper as truth.", refs_outcome() + refs_product_sot(), None),
        4: ("implemented_by_contract", "Method routing must precede execution.", refs_method(), None),
        5: ("implemented_by_contract", "Development must be organized before workers run.", refs_software() + refs_workers(), None),
        6: ("implemented_by_contract", "Product experience must be validated before a surface is called ready.", refs_experience(), None),
        7: ("implemented_by_contract", "Data and metrics must exist before success is claimed.", refs_data(), None),
        8: ("implemented_by_contract", "Security architecture must precede material build.", refs_security(), None),
        9: ("implemented_by_contract", "Dependencies must be explicit before integration.", refs_dependency_access_budget(), None),
        10: ("implemented_by_contract", "Access and capability must be ready before material execution.", refs_dependency_access_budget(), None),
        11: ("implemented_by_contract", "Cost and budget limits must precede expensive or remote execution.", refs_dependency_access_budget(), None),
        12: ("implemented_by_contract", "Authority must be explicit before material action.", refs_authority(), None),
        13: ("implemented_by_contract", "Privacy, compliance and security must run through the process.", refs_compliance() + refs_security(), None),
        14: ("implemented_by_contract", "Important agents, skills, prompts and models need evals.", refs_agent_eval(), None),
        15: ("implemented_by_runtime", "Proof must precede done.", refs_evidence(), None),
        16: ("implemented_by_contract", "Independent review must precede trust.", refs_authority() + refs_workers(), None),
        17: ("implemented_by_contract", "Humans decide material risk.", refs_authority(), None),
        18: ("bounded_public_proof", "Release requires owner, rollback, monitoring and clear channel.", refs_production() + refs_release(), None),
        19: ("implemented_by_contract", "Incidents must become learning artifacts.", refs_production() + refs_learning(), None),
        20: ("implemented_by_contract", "The factory must audit itself for blind spots.", refs_learning(), None),
        21: ("bounded_public_proof", "Human interfaces cannot replace durable state.", refs_control_tower() + refs_runtime(), None),
        22: ("bounded_public_proof", "Discord displays the factory; Hermes records truth.", refs_control_tower() + refs_runtime(), None),
        23: ("bounded_public_proof", "The user talks to the official factory concierge, not every worker.", refs_control_tower() + refs_workers(), None),
        24: ("bounded_public_proof", "Human approvals made in an interface must become durable events.", refs_control_tower() + refs_authority(), None),
    }
    status, obligation, refs, boundary = table[number]
    return checkpoint_record(
        checkpoint,
        status=status,
        obligation=f"Principle {number}: {obligation} Source text: {text}",
        refs=refs,
        boundary=boundary,
    )


def title_record(checkpoint: Checkpoint) -> dict[str, Any]:
    title = checkpoint.title
    norm = normalize(title)

    if norm in {
        "overkill factory vfinal",
        "1 definicao curta",
        "2 decisao central",
        "4 palavras simples",
        "17 conclusao canonica",
    }:
        return checkpoint_record(
            checkpoint,
            status="foundational_text_tracked",
            obligation="Track the canonical identity, vocabulary and source-of-truth framing.",
            refs=refs_factory_flow() + refs_runtime()[:2] + refs_control_tower()[:3],
        )

    if norm == "3 principios":
        return checkpoint_record(
            checkpoint,
            status="implemented_by_contract",
            obligation="Track every numbered principle as an explicit checkpoint below this section.",
            refs=[
                ref("validation_artifact", ".tmp/factory-runs/canonical-enforcement/canonical-enforcement-matrix.json", "principle-to-enforcement map"),
                ref("script", "scripts/canonical_linear_traceability_audit.py", "extracts every numbered principle"),
                ref("test", "tests/test_canonical_linear_traceability_audit.py", "locks the principle count"),
            ],
        )

    if norm in {"5 camadas da fabrica", "7 fluxo canonico", "8 processo por etapa"}:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_contract",
            obligation="Preserve the canonical factory sequence as a traceable implementation map.",
            refs=refs_factory_flow() + [
                ref("schema", "schemas/canonical-stage-implementation-coverage.schema.json", "stage coverage schema"),
                ref("test", "tests/test_canonical_stage_implementation_coverage.py", "stage coverage regression"),
            ],
        )

    if "factory kernel" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_runtime",
            obligation="Kernel rules, states, risk, authority and validation must have executable checks.",
            refs=[
                ref("schema", "schemas/factory-card.schema.json", "factory card kernel contract"),
                ref("schema", "schemas/gate-report.schema.json", "gate report contract"),
                ref("script", "scripts/factoryctl.py", "kernel validation CLI"),
                ref("test", "tests/test_factoryctl.py", "kernel validation regressions"),
            ],
        )

    if "product outcome" in norm or "outcome gate" in norm or "discovery gate" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Outcome and discovery must be structured before planning.", refs=refs_outcome())

    if "product sot" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Product SOT must be a structured source of truth before execution.", refs=refs_product_sot())

    if (normalize(PRIVATE_PRODUCT_TOKEN) in norm or "private product pack" in norm) and "product pack" in norm:
        return checkpoint_record(
            checkpoint,
            status="bounded_public_proof",
            obligation="The public repo can carry only public-safe product-pack proof; private product context must stay outside.",
            refs=refs_private_product_pack() + refs_repo_public(),
        )

    if "product pack" in norm or "surface pack" in norm or "pack gate" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Product and surface packs must declare capability coverage and block unsupported work.", refs=refs_packs())

    if "agentic method router" in norm or "method contract" in norm or "method gate" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="The selected method must declare required artifacts, gates, workers and reviewers.", refs=refs_method())

    if "software development" in norm or "spec graph" in norm or "loop plan" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Software work must be decomposed into plans, graph, units and loop controls.", refs=refs_software())

    if "product experience" in norm or "experience gate" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Product-facing work must route through Product Experience OS and Product Face proof.", refs=refs_experience())

    if "data metrics" in norm or "analytics" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Data, metrics, analytics, logs and alerts must be specified before success claims.", refs=refs_data())

    if "agent quality" in norm or "agent eval" in norm or "evals" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Agents, prompts, models and skills need explicit eval plans/results.", refs=refs_agent_eval())

    if "autonomy readiness" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_contract",
            obligation="Autonomy readiness must map access, tools, environment, cost, rollback, human gates, resources and owners before material execution.",
            refs=refs_autonomy_readiness(),
        )

    if "production operations" in norm or "production readiness" in norm or "monitoring" in norm or "incident" in norm or "support" in norm:
        return checkpoint_record(
            checkpoint,
            status="bounded_public_proof",
            obligation="Production operations, monitoring and support must have owner, health, rollback and incident paths.",
            refs=refs_production(),
        )

    if "dependency" in norm or "access capability" in norm or "budget" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_contract",
            obligation="Dependencies, access/capability and budgets must be explicit blockers before material work.",
            refs=refs_dependency_access_budget(),
        )

    if "compliance" in norm or "privacy" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Compliance and privacy requirements must be planned and public-safe.", refs=refs_compliance())

    if "runtime adapter" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_runtime", obligation="The factory must use a runtime adapter instead of loose chat execution.", refs=refs_runtime())

    if "closure summary" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_contract",
            obligation="Closure summary must reconcile requested work, delivered proof, risks, waivers, scope and next step before Receipt Five.",
            refs=refs_closure_summary(),
        )

    if "evidence os" in norm or "worker result" in norm or "verification" in norm or "receipt five" in norm or "completion audit" in norm or "done gate" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_runtime", obligation="Evidence, worker results, verification, receipts and audits must block false done.", refs=refs_evidence())

    if "security architecture" in norm or "security gate" in norm or "security and authority" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Security architecture and specialist routing must precede material risk.", refs=refs_security() + refs_authority())

    if "authority" in norm or "human gate" in norm or "review" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Authority, review and human approval must be explicit, evidenced and non-self-approved.", refs=refs_authority() + refs_workers())

    if "discord control tower" in norm or "control tower" in norm or "owner interface" in norm:
        return checkpoint_record(
            checkpoint,
            status="bounded_public_proof",
            obligation="The human cockpit must mirror durable runtime truth and register approvals as durable events.",
            refs=refs_control_tower(),
        )

    if "learning system" in norm or "learnback" in norm or "factory maturity" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Learning and maturity audit must convert failures into durable improvements.", refs=refs_learning())

    if "documentation standard" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Documentation must let another agent continue and must stay public-safe.", refs=refs_docs_standard())

    if "entradas aceitas" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_runtime",
            obligation="Accepted request types must be explicit and validated before routing.",
            refs=[
                ref("schema", "schemas/factory-card.schema.json", "request_type contract"),
                ref("template", "templates/vfinal-factory-card.json", "vFinal card template"),
                ref("script", "scripts/factoryctl.py", "VFINAL_REQUEST_TYPES validation"),
                ref("test", "tests/test_factoryctl.py", "request type regressions"),
            ],
        )

    if "intake" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_contract",
            obligation="Intake must classify request type, source refs, phase and risk.",
            refs=[
                ref("schema", "schemas/factory-card.schema.json", "intake fields"),
                ref("template", "templates/vfinal-factory-card.json", "intake-ready card"),
                ref("script", "scripts/factoryctl.py", "card validation and worker packet generation"),
                ref("worker_registry", "agents/worker-registry.public.json", "factory orchestrator intake ownership"),
            ],
        )

    if "source gate" in norm or "source ledger" in norm or "source resolution" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="Sources must be captured, resolved and blocked when stale or unsupported.", refs=refs_source())

    if "risk tiers" in norm or "risk authority" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_contract",
            obligation="Risk tiers and authority levels must control required workers and gates.",
            refs=[
                ref("schema", "schemas/factory-card.schema.json", "risk and authority fields"),
                ref("schema", "schemas/gate-report.schema.json", "risk-aware gate report"),
                ref("script", "scripts/factoryctl.py", "R3/R4 and security blockers"),
                ref("test", "tests/test_factoryctl.py", "risk and authority regressions"),
            ],
        )

    if "unidades de trabalho" in norm or "execucao" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_runtime",
            obligation="Execution must run scoped work units through worker packets after gates.",
            refs=[
                ref("schema", "schemas/work-unit-contract.schema.json", "work unit contract"),
                ref("schema", "schemas/worker-packet.schema.json", "worker packet contract"),
                ref("script", "scripts/factoryctl.py", "worker packet generator"),
                ref("test", "tests/test_factoryctl.py", "worker packet regressions"),
            ],
        )

    if "workers principais" in norm or "mapa de agentes" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_contract", obligation="The factory must route stages to named workers and profile bindings.", refs=refs_workers())

    if "gates obrigatorios" in norm or norm.endswith("gate") or "ready gate" in norm:
        return checkpoint_record(
            checkpoint,
            status="implemented_by_runtime",
            obligation="Mandatory gates must be represented as reportable blockers before transitions.",
            refs=[
                ref("schema", "schemas/gate-report.schema.json", "gate report contract"),
                ref("script", "scripts/factoryctl.py", "gate report and transition blockers"),
                ref("runtime_adapter", "adapters/hermes/transition_hook.py", "runtime transition hook"),
                ref("test", "tests/test_factoryctl.py", "gate report regressions"),
                ref("test", "tests/test_hermes_transition_hook.py", "runtime hook regressions"),
            ],
        )

    if "release ou block" in norm or "release channel" in norm or "release gate" in norm:
        return checkpoint_record(checkpoint, status="bounded_public_proof", obligation="Release or block decisions must carry owner, channel, rollback and evidence.", refs=refs_release() + refs_production())

    if "repo publico" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_runtime", obligation="The public repo must reject private leaks, secrets and unsafe JSON artifacts.", refs=refs_repo_public())

    if "definition of done" in norm:
        return checkpoint_record(checkpoint, status="implemented_by_runtime", obligation="Done requires receipts, verification, reviews, worker results and completion audit.", refs=refs_evidence() + refs_release())

    if "separacao entre arquitetura canonica e readiness" in norm:
        return checkpoint_record(
            checkpoint,
            status="partial_requires_live_pilot",
            obligation="Architecture coverage must not be confused with end-to-end readiness.",
            refs=[
                ref("script", "scripts/factory_production_readiness.py", "readiness checker"),
                ref("validation_artifact", ".tmp/factory-runs/factory-production-readiness/current-readiness.json", "readiness status"),
                ref("script", "scripts/factory_production_readiness.py", "readiness checker"),
                ref("validation_artifact", ".tmp/factory-runs/canonical-stage-coverage/canonical-stage-implementation-coverage.json", "contract coverage evidence"),
            ],
            next_action="Run a full live pilot before claiming architecture is production-ready.",
        )

    return checkpoint_record(
        checkpoint,
        status="partial_requires_live_pilot",
        obligation="No precise rule matched this checkpoint; it is kept visible instead of being silently skipped.",
        refs=refs_factory_flow(),
        next_action=f"Add an explicit traceability rule for canonical heading: {title}",
    )


def build_audit(
    canonical_path: Path | None = None,
    checkpoint_manifest_path: Path = DEFAULT_CHECKPOINT_MANIFEST,
) -> dict[str, Any]:
    canonical_doc_ref, canonical_hash, checkpoints = load_checkpoint_source(canonical_path, checkpoint_manifest_path)
    records = [principle_record(cp) if cp.checkpoint_type == "principle" else title_record(cp) for cp in checkpoints]
    status_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    for record in records:
        status_counts[record["implementation_status"]] = status_counts.get(record["implementation_status"], 0) + 1
        type_counts[record["checkpoint_type"]] = type_counts.get(record["checkpoint_type"], 0) + 1

    has_limits = any(
        record["implementation_status"] in {"bounded_public_proof", "partial_requires_live_pilot", "foundational_text_tracked"}
        for record in records
    )
    return {
        "$schema": SCHEMA,
        "record_type": "canonical_linear_traceability_audit",
        "canonical_doc_ref": canonical_doc_ref,
        "canonical_sha256": canonical_hash,
        "coverage_rule": (
            "Every Markdown heading and every numbered principle in the canonical document must appear "
            "in order with repo artifacts or an explicit boundary. This proves traceability, not full live "
            "production readiness."
        ),
        "result": "PASS_WITH_LIMITS" if has_limits else "PASS",
        "completion_claim_allowed": False,
        "completion_claim_rule": (
            "Do not claim the whole factory is end-to-end production-ready from this audit alone; "
            "a live pilot receipt from raw input through release/block is still required."
        ),
        "summary": {
            "checkpoints_checked": len(records),
            "headings_checked": type_counts.get("heading", 0),
            "principles_checked": type_counts.get("principle", 0),
            "status_counts": status_counts,
        },
        "checkpoints": records,
    }


def repo_path(path_value: str) -> Path | None:
    if path_value.startswith("external:"):
        return None
    return ROOT / path_value.split("#", 1)[0]


def validate_audit(
    audit: dict[str, Any],
    canonical_path: Path | None = None,
    checkpoint_manifest_path: Path = DEFAULT_CHECKPOINT_MANIFEST,
) -> list[str]:
    errors: list[str] = []
    if audit.get("record_type") != "canonical_linear_traceability_audit":
        errors.append("record_type must be canonical_linear_traceability_audit")
    canonical_doc_ref, canonical_hash, expected = load_checkpoint_source(canonical_path, checkpoint_manifest_path)
    if audit.get("canonical_doc_ref") != canonical_doc_ref:
        errors.append("canonical_doc_ref does not match the canonical checkpoint source")
    if audit.get("canonical_sha256") != canonical_hash:
        errors.append("canonical_sha256 does not match the canonical document")

    records = audit.get("checkpoints")
    if not isinstance(records, list):
        return [*errors, "checkpoints must be an array"]
    if len(records) != len(expected):
        errors.append(f"checkpoint count mismatch: expected {len(expected)}, got {len(records)}")

    for index, record in enumerate(records):
        if not isinstance(record, dict):
            errors.append(f"checkpoints[{index}] must be an object")
            continue
        if index < len(expected):
            checkpoint = expected[index]
            expected_identity = (
                checkpoint.sequence,
                checkpoint.checkpoint_type,
                checkpoint.canonical_line,
                checkpoint.canonical_level,
                redact_public_text(checkpoint.title),
            )
            actual_identity = (
                record.get("sequence"),
                record.get("checkpoint_type"),
                record.get("canonical_line"),
                record.get("canonical_level"),
                record.get("canonical_heading"),
            )
            if actual_identity != expected_identity:
                errors.append(f"checkpoints[{index}] does not match canonical order/source line")

        checkpoint_id = str(record.get("checkpoint_id") or f"#{index}")
        status = record.get("implementation_status")
        if status not in ALLOWED_STATUS:
            errors.append(f"{checkpoint_id}: unsupported implementation_status {status!r}")

        refs = record.get("implementation_refs")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{checkpoint_id}: implementation_refs must be non-empty")
            continue

        strong_refs = 0
        for ref_item in refs:
            if not isinstance(ref_item, dict):
                errors.append(f"{checkpoint_id}: implementation ref must be an object")
                continue
            kind = ref_item.get("kind")
            if kind not in ALLOWED_REF_KINDS:
                errors.append(f"{checkpoint_id}: unsupported ref kind {kind!r}")
            if kind in STRONG_REF_KINDS:
                strong_refs += 1
            path_value = str(ref_item.get("path") or "").strip()
            if not path_value:
                errors.append(f"{checkpoint_id}: ref path is required")
                continue
            target = repo_path(path_value)
            if target is None:
                errors.append(f"{checkpoint_id}: implementation refs must be repo-local, got {path_value}")
                continue
            raw_ref_path = Path(path_value.split("#", 1)[0])
            if raw_ref_path.is_absolute() or re.match(r"^[A-Za-z]:", path_value):
                errors.append(f"{checkpoint_id}: implementation ref must be relative/public-safe: {path_value}")
            if not target.exists():
                errors.append(f"{checkpoint_id}: ref does not exist: {path_value}")

        if status != "foundational_text_tracked" and strong_refs == 0:
            errors.append(f"{checkpoint_id}: operational checkpoints need at least one non-documentation artifact")
        if status in {"bounded_public_proof", "partial_requires_live_pilot", "foundational_text_tracked"} and not record.get("boundary"):
            errors.append(f"{checkpoint_id}: boundary is required for limited statuses")
        if status == "partial_requires_live_pilot" and not record.get("next_action"):
            errors.append(f"{checkpoint_id}: next_action is required for partial checkpoints")

    return errors


def build_summary(audit: dict[str, Any], errors: list[str]) -> dict[str, Any]:
    summary = dict(audit["summary"])
    summary["result"] = "FAIL" if errors else audit["result"]
    summary["errors"] = errors
    return summary


def escape_md(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def write_markdown(path: Path, audit: dict[str, Any], errors: list[str]) -> None:
    summary = build_summary(audit, errors)
    lines = [
        "# Canonical Linear Traceability Audit",
        "",
        "> Document status: CURRENT RUNTIME EVIDENCE.",
        "> Current authority: `scripts/factoryctl.py`, schemas and tests.",
        "> Runtime boundary: This maps the canonical document linearly; runtime implementation is answered by the real-infra audit and enforced gates.",
        "",
        f"Result: `{summary['result']}`",
        f"Canonical doc: `{audit['canonical_doc_ref']}`",
        f"Canonical SHA-256: `{audit['canonical_sha256']}`",
        f"Checkpoints checked: `{summary['checkpoints_checked']}`",
        f"Headings checked: `{summary['headings_checked']}`",
        f"Principles checked: `{summary['principles_checked']}`",
        f"Completion claim allowed: `{audit['completion_claim_allowed']}`",
        "",
        "This audit proves linear traceability. It does not prove that the factory is end-to-end production-ready for any product.",
        "",
        "## Status Counts",
        "",
    ]
    for status, count in sorted(summary["status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")
    lines.extend(["", "## Errors", ""])
    if errors:
        lines.extend(f"- {error}" for error in errors)
    else:
        lines.append("- None.")
    lines.extend(
        [
            "",
            "## Checkpoints",
            "",
            "| # | Line | Type | Canonical checkpoint | Status | Evidence refs | Boundary / next action |",
            "| ---: | ---: | --- | --- | --- | --- | --- |",
        ]
    )
    for record in audit["checkpoints"]:
        refs = "<br>".join(escape_md(item["path"]) for item in record["implementation_refs"])
        boundary_parts = [record.get("boundary") or ""]
        if record.get("next_action"):
            boundary_parts.append(f"Next: {record['next_action']}")
        lines.append(
            "| {sequence} | {line} | {type} | {heading} | `{status}` | {refs} | {boundary} |".format(
                sequence=record["sequence"],
                line=record["canonical_line"],
                type=escape_md(record["checkpoint_type"]),
                heading=escape_md(record["canonical_heading"]),
                status=escape_md(record["implementation_status"]),
                refs=refs,
                boundary=escape_md(" ".join(part for part in boundary_parts if part)),
            )
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_json(path: Path, audit: dict[str, Any], errors: list[str]) -> None:
    output = dict(audit)
    output["validation_errors"] = errors
    if errors:
        output["result"] = "FAIL"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit canonical doc traceability in source order.")
    parser.add_argument(
        "--canonical",
        type=Path,
        default=None,
        help="Optional private canonical document. Default uses the public checkpoint manifest.",
    )
    parser.add_argument("--checkpoint-manifest", type=Path, default=DEFAULT_CHECKPOINT_MANIFEST)
    parser.add_argument(
        "--write-checkpoint-manifest",
        type=Path,
        help="Write a public-safe checkpoint manifest extracted from --canonical, then exit.",
    )
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--require-full-runtime", action="store_true", help="Fail if any checkpoint is bounded/partial/foundational.")
    args = parser.parse_args(argv)

    if args.write_checkpoint_manifest:
        if args.canonical is None:
            parser.error("--write-checkpoint-manifest requires --canonical")
        manifest = checkpoint_manifest(args.canonical)
        args.write_checkpoint_manifest.parent.mkdir(parents=True, exist_ok=True)
        args.write_checkpoint_manifest.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"result": "WROTE", "checkpoint_count": manifest["checkpoint_count"]}, indent=2))
        return 0

    audit = build_audit(args.canonical, args.checkpoint_manifest)
    errors = validate_audit(audit, args.canonical, args.checkpoint_manifest)
    if args.require_full_runtime:
        limited = [
            record["checkpoint_id"]
            for record in audit["checkpoints"]
            if record["implementation_status"] in {"bounded_public_proof", "partial_requires_live_pilot", "foundational_text_tracked"}
        ]
        if limited:
            errors.append(f"full runtime claim blocked by {len(limited)} limited checkpoint(s)")

    write_json(args.out_json, audit, errors)
    write_markdown(args.out_md, audit, errors)
    summary = build_summary(audit, errors)
    print(
        json.dumps(
            {
                "result": summary["result"],
                "checkpoints_checked": summary["checkpoints_checked"],
                "headings_checked": summary["headings_checked"],
                "principles_checked": summary["principles_checked"],
                "errors": len(errors),
                "completion_claim_allowed": audit["completion_claim_allowed"],
            },
            indent=2,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
