from __future__ import annotations

import importlib.util
import hashlib
import json
import re
import shutil
import sys
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
SPEC.loader.exec_module(factoryctl)

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


def load_card(name: str) -> dict:
    return factoryctl.load_json_like(ROOT / "examples" / "cards" / name)


def valid_quasar_toolchain_proof(**overrides: object) -> dict:
    proof = {
        "install_source": "github:blueshift-gg/quasar",
        "source_ref": "a89a9329f05740a20520607608b2b3b78c74f7c4",
        "source_head_expected": "a89a9329f05740a20520607608b2b3b78c74f7c4",
        "source_head": "a89a9329f05740a20520607608b2b3b78c74f7c4",
        "source_head_matches": True,
        "container_image": "rust:1.91.0-bookworm@sha256:e187887ec511b3d93e45c0231d2f0fd59f1347526c58aa86343aa83c74f3e1a9",
        "solana_release": "v4.0.2",
        "solana_install_url": "https://release.anza.xyz/v4.0.2/install",
        "rustc": "rustc 1.91.0",
        "cargo": "cargo 1.91.0",
        "solana": "solana-cli 4.0.2",
        "quasar": "quasar 0.0.0",
        "init_command": "quasar init factory-quasar-proof --yes --toolchain solana --test-language rust --rust-framework quasar-svm --template minimal --no-git",
        "build_command": "quasar build",
        "test_command": "quasar test",
        "build_status": "PASS",
        "test_status": "PASS",
        "evidence_refs": [".tmp/factory-runs/quasar-real-proof/quasar-source-proof-result.json"],
    }
    proof.update(overrides)
    return proof


def worker_result(
    record_type: str,
    *,
    result: str = "PASS",
    source_card: dict | None = None,
    reviewer_required: bool = False,
    reviewer_result: str = "PENDING",
    review_worker_id: str = "independent-reviewer",
) -> dict:
    worker_id = {
        "security_scan_result": "codex-security",
        "auditor_result": "solana-quasar-auditor",
        "independent_review_result": "independent-reviewer",
        "receipt_five_reconciliation_result": "evidence-reconciler",
        "qa_verification_result": "qa-verification-worker",
        "autoreview_result": "autoreview-gate",
        "orchestration_result": "factory-orchestrator",
        "source_ledger_result": "source-ledger-worker",
        "security_orchestration_result": "security-orchestrator",
        "crypto_key_management_result": "crypto-key-management-specialist",
        "remote_proof_result": "remote-proof-runner",
        "handoff_packet_result": "handoff-packer",
        "solana_quasar_build_result": "solana-quasar-builder",
        "solana_quasar_qa_result": "solana-quasar-qa-engineer",
        "supply_chain_result": "supply-chain-gate",
    }.get(record_type, "fixture-worker")
    card_id = str((source_card or {}).get("card_id") or "VAL-SOLANA-QUASAR-R3")
    slice_id = str((source_card or {}).get("slice_id") or "VAL_FACTORY_HEAVY_03")
    phase = str((source_card or {}).get("phase") or "F13")
    risk_effective = str((source_card or {}).get("risk_effective") or "R3")
    surfaces = (source_card or {}).get("surfaces") or ["solana-quasar"]
    positive_authority = result in {"PASS", "WAIVED"}
    payload = {
        "$schema": factoryctl.worker_result_schema_url(worker_id) if worker_id in factoryctl.WORKERS else "https://overkill-factory.dev/schemas/worker-result.schema.json",
        "record_type": record_type,
        "created_at": "2026-06-06T00:00:00+00:00",
        "worker": {"id": worker_id, "name": "Fixture Worker", "factory_phase": "F13"},
        "card_ref": {
            "card_id": card_id,
            "slice_id": slice_id,
            "phase": phase,
            "risk_effective": risk_effective,
            "surfaces": surfaces,
        },
        "result": result,
        "blocking_findings": False,
        "findings_summary": "Synthetic passing fixture.",
        "tool_or_profile": "fixture-tool",
        "executed_by": "fixture-runner",
        "evidence_refs": ["README.md"],
        "artifact_contract": factoryctl.artifact_contract_for_refs(["README.md"]),
        "artifact_classifications": factoryctl.artifact_contract_for_refs(["README.md"])["classifications"],
        "evidence_kind": "synthetic",
        "reusable_for_product": False,
        "next_action": "none",
        "promotion_authority": {
            "result": "PASS" if result in {"PASS", "WAIVED"} else "BLOCK",
            "predicate": "synthetic fixture authority",
            "allowed_transition_scopes": ["review"] if reviewer_required and positive_authority else ["done"] if positive_authority else [],
            "active": True,
        },
    }
    if reviewer_required:
        review_field = factoryctl.WORKERS.get(
            review_worker_id,
            factoryctl.WORKERS["independent-reviewer"],
        ).output_field
        payload.update(
            {
                "reviewer_required": True,
                "review_worker_id": review_worker_id,
                "reviewer_result": reviewer_result,
                "handoff_state": "implementation_ready_for_review" if positive_authority else "blocked",
                "review_declared": True,
                "review_ready": positive_authority,
                "authorized_downstream_scope": ["review"] if positive_authority else [],
                "review_required_handoff": {
                    "review_required": True,
                    "review_worker_id": review_worker_id,
                    "required_review_field": review_field,
                    "authorized_scope": ["review"],
                    "forbidden_scope_until_review_pass": [
                        "release",
                        "deployment",
                        "github_mutation",
                        "issue_completion",
                        "product_acceptance",
                    ],
                },
            }
        )
    if record_type == "security_scan_result":
        payload["scanner_agent"] = "codex-security-runner"
        payload["tool"] = "codex-security:security-scan"
        payload["scope"] = ["fixture"]
    if record_type == "auditor_result":
        payload["audit_mode"] = "preflight"
        payload["preflight_only"] = True
        payload["findings_summary"] = "Auditor preflight only; no code audit is claimed."
    if record_type == "autoreview_result":
        payload["reviewed_diff"] = "synthetic fixture"
    if record_type == "remote_proof_result":
        payload["runtime"] = "synthetic-smoke"
        payload["ttl"] = "synthetic"
        payload["cleanup"] = {"status": "not_applicable"}
        payload["artifact_refs"] = ["reports/fixture.md"]
    if record_type == "handoff_packet_result":
        payload["handoff_packet_ref"] = "reports/fixture.md"
    if record_type == "receipt_five_reconciliation_result":
        payload["valid"] = result == "PASS"
    if result == "WAIVED":
        payload["waiver"] = {
            "owner": "fixture-owner",
            "reason": "Synthetic fixture boundary.",
            "expires_at": "2026-12-31T00:00:00+00:00",
            "reviewer_or_human_gate_ref": "README.md",
            "compensating_controls": ["run real worker before production"],
            "evidence_refs": ["README.md"],
        }
    return payload


def human_gate_record(source_card: dict | None = None) -> dict:
    card_id = str((source_card or {}).get("card_id") or "VAL-SOLANA-QUASAR-R3")
    slice_id = str((source_card or {}).get("slice_id") or "VAL_FACTORY_HEAVY_03")
    return {
        "record_type": "human_gate_record",
        "gate_type": "R3",
        "card_id": card_id,
        "card_ref": {
            "card_id": card_id,
            "slice_id": slice_id,
        },
        "decision": "approved",
        "human_actor": "product-owner",
        "decision_at": "2026-06-06T00:00:00+00:00",
        "approval_event_id": "evt_fixture_human_approval",
        "approved_scope": ["dry validation"],
        "forbidden_scope": ["deploy"],
        "risk_owner": "product-owner",
        "security_owner": "security-owner",
        "rollback_owner": "release-owner",
        "evidence_refs": ["README.md"],
        "evidence_kind": "synthetic",
        "reusable_for_product": False,
    }


def reference_quality_comparison_fixture() -> dict:
    compared_source_ids = [
        "21st-dev-components",
        "mobbin-workflow-patterns",
        "pageflows-review-approval",
    ]
    return {
        "status": "pass",
        "basis": "Independent reviewer compared the Product Face result against selected professional references.",
        "reference_set_ref": "examples/cards/v35_valid_product_face.md#professional_design_process.reference_research",
        "compared_source_ids": compared_source_ids,
        "reviewer_independent_from_implementation": True,
        "comparison_artifacts": [
            {
                "artifact_ref": "external:product-face-fixture-reference-comparison",
                "artifact_type": "side_by_side_capture",
                "compared_source_ids": compared_source_ids,
                "basis": "Sanitized side-by-side comparison covers all selected references.",
                "bounded_acceptance": True,
                "sanitized": True,
            }
        ],
        "dimensions": {
            dimension: {
                "status": "pass",
                "basis": f"The result satisfies the {dimension} bar from the selected references.",
            }
            for dimension in factoryctl.REFERENCE_COMPARISON_DIMENSIONS
        },
    }


def product_delivery_quality_profile_fixture() -> dict:
    return {
        "record_type": "product_delivery_quality_profile",
        "profile_id": "game-product-v1",
        "archetype": "game product",
        "applies_to_surfaces": ["game", "3d", "gameplay"],
        "quality_dimensions": [
            {
                "dimension_id": "playable-loop",
                "bar": "The game has a playable loop with input, feedback and completion feedback.",
                "block_when": ["Only static screenshots exist."]
            }
        ],
        "required_proofs": [
            {
                "proof_id": "game.playable-smoke",
                "name": "Playable smoke",
                "required_at": ["before_completion"],
                "owner_worker": "game-runtime-builder",
                "reviewer_role": "game-qa-specialist",
                "evidence_kind": "runtime",
                "human_gate_required": False,
            }
        ],
        "waiver_policy": {
            "allowed": True,
            "requires_owner": True,
            "requires_reason": True,
            "cannot_claim_full_acceptance": True,
        },
        "evidence_refs": ["agents/capability-packs.public.json#game-product-pack"],
    }


def human_gated_product_delivery_quality_profile_fixture() -> dict:
    return {
        "record_type": "product_delivery_quality_profile",
        "profile_id": "human-gated-product-v1",
        "archetype": "human-gated product",
        "applies_to_surfaces": ["frontend"],
        "quality_dimensions": [
            {
                "dimension_id": "human-accepted-operator-usability",
                "bar": "Operator usability proof is accepted by the declared human reviewer.",
                "block_when": ["Proof is reviewed by the wrong role or lacks a human gate record."]
            }
        ],
        "required_proofs": [
            {
                "proof_id": "generic.operator-usability",
                "name": "Human accepted operator usability proof",
                "required_at": ["before_completion"],
                "owner_worker": "qa-verification-worker",
                "reviewer_role": "human-product-owner",
                "evidence_kind": "human_gate",
                "human_gate_required": True,
            }
        ],
        "waiver_policy": {
            "allowed": False,
            "requires_owner": True,
            "requires_reason": True,
            "cannot_claim_full_acceptance": True,
        },
        "evidence_refs": ["templates/product-delivery-quality-profile.json"],
    }


def activated_game_contract_fixture() -> dict:
    return {
        "record_type": "capability_pack_contract",
        "pack_id": "game-product-pack",
        "status": "activated",
        "lifecycle_state": "activated",
        "covered_surfaces": ["game", "3d", "asset-pipeline"],
        "specialist_workers": ["game-runtime-builder", "game-design-specialist", "game-qa-specialist"],
        "activation_evidence_refs": ["external:game-pack-activation"],
        "tool_refs": ["external:game-runtime-tool"],
        "local_smoke_path": "external:playable-game-smoke-command",
        "eval_path": "external:game-eval-command",
        "smoke_evidence_ref": "external:playable-game-smoke",
        "eval_evidence_ref": "external:game-eval",
        "profile_binding_refs": {
            "game-runtime-builder": "external:game-runtime-profile-binding",
            "game-design-specialist": "external:game-design-profile-binding",
            "game-qa-specialist": "external:game-qa-profile-binding",
        },
        "permission_class": "bounded-worker",
        "missing_capabilities": [],
        "execution_rule": "Game execution is allowed only after playable smoke, performance budget and game QA proof exist.",
        "structured_proofs_required": [
            "game.design-packet",
            "game.performance-budget",
            "game.playable-smoke",
            "game.playtest-review",
            "game.runtime-choice",
        ],
        "worker_mapping": {
            "runtime": ["game-runtime-builder"],
            "design": ["game-design-specialist"],
            "qa": ["game-qa-specialist"],
        },
    }


def usage_evidence_matrix_fixture(
    *,
    journeys: list[str],
    states: list[str],
    viewports: list[str],
) -> list[dict]:
    entries: list[dict] = []
    for journey in journeys:
        for state in states:
            for viewport in viewports:
                evidence_ref = product_face_screenshot_ref(viewport)
                entries.append(
                    {
                        "journey": journey,
                        "state": state,
                        "viewport": viewport,
                        "data_condition": f"{state} fixture",
                        "evidence_refs": [evidence_ref],
                        "a11y_status": "pass",
                        "performance_status": "pass",
                        "reviewer": "product-face-reviewer",
                        "basis": f"{journey} was checked in {state} state on {viewport}.",
                    }
                )
    return entries


def product_face_screenshot_ref(viewport: str) -> str:
    return (
        "external:product-face-fixture-mobile.png"
        if "mobile" in viewport.lower()
        else "external:product-face-fixture-desktop.png"
    )


def visual_artifacts_fixture(
    *,
    target: str,
    viewports: list[str],
    states: list[str],
    screenshots: list[str],
    captured_at: str = "2026-06-16T00:00:00+00:00",
) -> list[dict]:
    artifacts: list[dict] = []
    for viewport, screenshot in zip(viewports, screenshots):
        for state in states:
            artifacts.append(
                {
                    "evidence_ref": screenshot,
                    "target": target,
                    "viewport": viewport,
                    "state": state,
                    "captured_at": captured_at,
                    "freshness_status": "bounded_external",
                    "bounded_acceptance": True,
                    "sanitized": True,
                    "external_package_ref": "external:product-face-fixture-package",
                    "basis": "Sanitized fixture artifact bound to the declared viewport and state.",
                }
            )
    return artifacts


def external_visual_artifact_manifest_fixture(
    *,
    manifest_ref: str = "external:product-face-fixture-package",
    target: str,
    viewports: list[str],
    states: list[str],
    screenshots: list[str],
    captured_at: str = "2026-06-16T00:00:00+00:00",
    expires_at: str = "2099-01-01T00:00:00+00:00",
) -> list[dict]:
    return [
        {
            "manifest_ref": manifest_ref,
            "target": target,
            "captured_at": captured_at,
            "expires_at": expires_at,
            "bounded_acceptance": True,
            "sanitized": True,
            "owner": "product-face-fixture-owner",
            "reviewer": "product-face-fixture-reviewer",
            "artifacts": [
                {
                    "evidence_ref": screenshot,
                    "viewport": viewport,
                    "state": state,
                    "captured_at": captured_at,
                }
                for viewport, screenshot in zip(viewports, screenshots)
                for state in states
            ],
        }
    ]


def product_face_result_fixture(**overrides: object) -> dict:
    overrides = dict(overrides)
    viewports = ["desktop 1440x900", "mobile 390x844"]
    states = ["empty", "loading", "pending", "success", "error"]
    journeys = ["pilot status review", "review evidence inspection"]
    target = "external:product-face-fixture-target"
    viewports = list(overrides.pop("viewports", viewports))  # type: ignore[arg-type]
    states = list(overrides.pop("checked_states", states))  # type: ignore[arg-type]
    journeys = list(overrides.pop("user_journeys_checked", journeys))  # type: ignore[arg-type]
    screenshots = list(overrides.pop("screenshots", [product_face_screenshot_ref(viewport) for viewport in viewports]))  # type: ignore[arg-type]
    usage_matrix = overrides.pop(
        "usage_evidence_matrix",
        usage_evidence_matrix_fixture(journeys=journeys, states=states, viewports=viewports),
    )
    visual_artifacts = overrides.pop(
        "visual_artifacts",
        visual_artifacts_fixture(
            target=target,
            viewports=viewports,
            states=states,
            screenshots=screenshots,
        ),
    )
    external_visual_artifact_manifests = overrides.pop(
        "external_visual_artifact_manifests",
        external_visual_artifact_manifest_fixture(
            target=target,
            viewports=viewports,
            states=states,
            screenshots=screenshots,
        ),
    )
    result = {
        "result": "PASS",
        "tool_or_profile": "browser-proof-runner",
        "executed_by": "product-face-validator",
        "surface_evidence_profile": {
            "profile_id": "web_visual_ui",
            "surface": "web_app",
            "evidence_kind": "visual_ui",
        },
        "surface_evidence_profiles": [
            {
                "profile_id": "web_visual_ui",
                "surface": "web_app",
                "evidence_kind": "visual_ui",
            }
        ],
        "screenshots": screenshots,
        "viewports": viewports,
        "checked_states": states,
        "user_journeys_checked": journeys,
        "usage_evidence_matrix": usage_matrix,
        "visual_artifacts": visual_artifacts,
        "external_visual_artifact_manifests": external_visual_artifact_manifests,
        "a11y": {"status": "pass", "keyboard": "pass", "labels": "pass", "contrast": "pass"},
        "overlap_check": {"status": "pass", "desktop": "pass", "mobile": "pass"},
        "console": {"status": "pass"},
        "performance_note": "static validation scenario only",
        "packet_ref": "examples/cards/v35_valid_product_face.md#product_face_packet",
        "packet_comparison": {
            "status": "pass",
            "basis": "All planned screens, states and viewports are covered."
        },
        "source_promise_coverage": {
            "status": "pass",
            "basis": "The result covers the visible validation promise in the card."
        },
        "design_fit_review": {
            "status": "pass",
            "basis": "The result matches the Product Face packet."
        },
        "professional_design_process_ref": "examples/cards/v35_valid_product_face.md#professional_design_process",
        "professional_design_process_comparison": {
            "status": "pass",
            "basis": "The result satisfies the professional design process gates."
        },
        "reference_quality_comparison": reference_quality_comparison_fixture(),
        "visual_quality_result": {
            "status": "PASS",
            "reviewer": "product-face-reviewer",
            "basis": "The surface meets the Product Face packet quality bar.",
            "reference_quality_bar_checked": True,
            "ai_generic_symptoms": [],
        },
        "domain_proof_coverage": [
            {
                "proof_id": "generic.operator-usability",
                "status": "PASS",
                "evidence_refs": ["reports/product-face/operator-usability.json"],
                "reviewer": "product-face-reviewer",
                "reviewer_role": "independent-reviewer",
                "evidence_kind": "review",
                "basis": "Operator can understand current state, evidence and next action.",
            }
        ],
        "blocking_findings": False,
        "evidence_refs": ["external:product-face-fixture-report"],
        "next_action": "independent review",
    }
    result.update(overrides)
    return result


def surface_profile(profile_id: str, surface: str) -> dict:
    return {
        "profile_id": profile_id,
        "surface": surface,
        "evidence_kind": {
            "web_visual_ui": "visual_ui",
            "cli_tui": "command_transcript",
            "docs_onboarding": "reader_success",
            "agentic_interface": "task_transcript",
        }[profile_id],
    }


def product_surface_card_fixture(surface: str, profile_id: str) -> dict:
    return {
        "surfaces": [surface],
        "product_face_packet": {
            "surface": surface,
            "surface_evidence_profile": profile_id,
            "required_states": ["success", "error"],
            "proof_required": [f"{surface} product proof"],
        },
        "product_experience_plan": {
            "surface_type": surface,
            "surface_evidence_profile": profile_id,
            "required_states": ["success", "error"],
            "proof_required": [f"{surface} product proof"],
        },
    }


PRIVATE_NAME = "KA" + "XIS"
PRIVATE_ENV = "V" + "M"
PRIVATE_USERS_PATH = "C:" + "\\\\" + "Users"
PRIVATE_SYNC_ROOT = "One" + "Drive"
PRIVATE_PATH_RE = re.compile(
    PRIVATE_USERS_PATH + r"|" + PRIVATE_SYNC_ROOT + r"|" + PRIVATE_NAME + r" " + PRIVATE_ENV + r"|" + PRIVATE_NAME,
    re.IGNORECASE,
)


class FactoryCtlTest(unittest.TestCase):
    def terminal_product_face_ref_card(self) -> dict:
        card = dict(factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md"))
        card["phase"] = "F16"
        card["product_face_result_required"] = True
        card.pop("product_face_result", None)
        return card

    def write_temp_product_face_result(self, payload: object, name: str = "product-face-result.json") -> str:
        tmp_root = ROOT / ".tmp" / "test-product-face-result-refs"
        tmp_root.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(dir=tmp_root))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / name
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path.relative_to(ROOT).as_posix()

    def write_temp_visual_artifact(self, name: str = "desktop.png") -> tuple[str, str]:
        tmp_root = ROOT / ".tmp" / "test-product-face-visual-artifacts"
        tmp_root.mkdir(parents=True, exist_ok=True)
        directory = Path(tempfile.mkdtemp(dir=tmp_root))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / name
        path.write_bytes(b"product-face-visual-artifact")
        return path.relative_to(ROOT).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()

    def test_local_web_cockpit_card_routes_without_discord_bridge(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "local-web-cockpit-factory-slice" / "card.md")
        card["product_experience_plan"] = {
            **factoryctl.load_json_like(ROOT / "templates" / "product-experience-plan.json"),
            **card["product_experience_plan"],
        }
        report = factoryctl.build_gate_report(card)

        self.assertEqual(report["card_validation_errors"], [])
        self.assertEqual(report["gate_status"], "ready_for_worker_execution")
        self.assertIn("control-tower-projection-worker", report["required_workers"])
        self.assertNotIn("discord-control-tower-bridge", report["required_workers"])
        self.assertEqual(report["workers"]["discord-control-tower-bridge"]["status"], "not_required_by_current_card")
        self.assertIn("product-face", report["required_workers"])
        self.assertIn("appsec-owasp-specialist", report["required_workers"])

    def test_discord_bridge_requires_explicit_discord_surface_or_contract(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "local-web-cockpit-factory-slice" / "card.md")

        required, reason = factoryctl.worker_required("discord-control-tower-bridge", card)
        self.assertFalse(required, reason)

        card["surfaces"] = list(card["surfaces"]) + ["discord"]
        required, reason = factoryctl.worker_required("discord-control-tower-bridge", card)
        self.assertTrue(required, reason)

    def test_product_face_card_requires_product_face_and_review_workers(self) -> None:
        card = load_card("v35_valid_product_face.md")
        report = factoryctl.build_gate_report(card)

        self.assertEqual(report["card_validation_errors"], [])
        self.assertEqual(report["gate_status"], "ready_for_worker_execution")
        self.assertIn("product-face", report["required_workers"])
        self.assertEqual(report["workers"]["product-face"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["independent-reviewer"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["solana-quasar-auditor"]["status"], "not_required_by_current_card")

    def test_onchain_r3_card_requires_security_auditor_review_and_human_gate(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        report = factoryctl.build_gate_report(card)

        self.assertEqual(report["card_validation_errors"], [])
        self.assertEqual(report["gate_status"], "ready_for_worker_execution")
        self.assertIn("codex-security", report["required_workers"])
        self.assertTrue(report["workers"]["codex-security"]["required"])
        self.assertEqual(report["workers"]["codex-security"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["solana-quasar-auditor"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["independent-reviewer"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["human-gate-clerk"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["autoreview-gate"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["remote-proof-runner"]["status"], "not_required_by_current_card")
        self.assertEqual(report["workers"]["supply-chain-gate"]["status"], "requires_execution")

    def test_required_only_worker_packets_generate_only_triggered_workers(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        required_ids = factoryctl.required_worker_ids(card)

        with tempfile.TemporaryDirectory() as tmp:
            args = type(
                "Args",
                (),
                {
                    "worker": "all",
                    "card": card_path,
                    "out": Path(tmp),
                    "required_only": True,
                },
            )
            self.assertEqual(factoryctl.command_worker_packet(args), 0)
            generated = sorted(path.name for path in Path(tmp).glob("*.json"))

        self.assertEqual(generated, sorted(f"{worker_id}-request.json" for worker_id in required_ids))
        self.assertLess(len(generated), len(factoryctl.WORKERS))

    def test_worker_packet_fails_closed_without_profile_binding_manifest(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        original_path = factoryctl.PROFILE_BINDINGS_PATH
        try:
            factoryctl.PROFILE_BINDINGS_PATH = ROOT / "agents" / "missing-bindings-for-test.json"
            with self.assertRaises(FileNotFoundError):
                factoryctl.build_worker_packet("codex-security", card, card_path)
        finally:
            factoryctl.PROFILE_BINDINGS_PATH = original_path

    def test_worker_packet_carries_activated_pack_structured_proofs(self) -> None:
        card_path = ROOT / "templates" / "vfinal-factory-card.json"
        card = factoryctl.load_json_like(card_path)
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card["capability_pack_contract"] = activated_game_contract_fixture()

        packet = factoryctl.build_worker_packet("implementation-worker", card, card_path)

        self.assertEqual(
            packet["input_contract"]["required_structured_proofs"],
            [
                "game.design-packet",
                "game.performance-budget",
                "game.playable-smoke",
                "game.playtest-review",
                "game.runtime-choice",
            ],
        )

    def test_worker_packet_carries_sdlc_feedback_loop_ref(self) -> None:
        card_path = ROOT / "templates" / "vfinal-factory-card.json"
        card = factoryctl.load_json_like(card_path)

        packet = factoryctl.build_worker_packet("implementation-worker", card, card_path)

        self.assertEqual(
            packet["input_contract"]["sdlc_feedback_loop_ref"],
            card["sdlc_feedback_loop_ref"],
        )

    def test_worker_packet_schema_declares_sdlc_feedback_loop_ref(self) -> None:
        schema = json.loads((ROOT / "schemas" / "worker-packet.schema.json").read_text(encoding="utf-8"))

        self.assertIn(
            "sdlc_feedback_loop_ref",
            schema["properties"]["input_contract"]["properties"],
        )

    def test_worker_packet_schema_allows_every_registered_worker(self) -> None:
        schema = json.loads((ROOT / "schemas" / "worker-packet.schema.json").read_text(encoding="utf-8"))
        allowed = set(schema["properties"]["worker"]["properties"]["id"]["enum"])

        self.assertEqual(allowed, set(factoryctl.WORKERS))

    def test_public_artifact_card_triggers_public_safety_gate(self) -> None:
        card = dict(load_card("v35_valid_product_face.md"))
        card["phase"] = "F16"
        card["surfaces"] = ["public", "docs", "code", "ci", "supply-chain"]
        card["target_repo_paths"] = ["README.md", "docs"]
        card["product_face_result_ref"] = "reports/product-face.md"
        card.pop("security_scan_packet", None)
        report = factoryctl.build_gate_report(card)

        self.assertTrue(report["workers"]["codex-security"]["required"])
        self.assertEqual(report["workers"]["codex-security"]["status"], "blocked_missing_inputs")
        self.assertEqual(report["gate_status"], "blocked")
        self.assertIn("codex-security", report["blocked_workers"])
        self.assertEqual(report["workers"]["public-safety-gate"]["status"], "requires_execution")
        self.assertEqual(report["workers"]["release-ops-worker"]["status"], "blocked_missing_inputs")
        next_action_workers = {item["worker_id"] for item in report["next_safe_actions"]}
        self.assertTrue(next_action_workers <= set(report["required_workers"]))
        self.assertIn("codex-security", next_action_workers)
        self.assertIn("release-ops-worker", next_action_workers)
        self.assertNotIn("product-face", next_action_workers)

    def test_learnback_and_maturity_phases_route_to_skill_eval_distiller(self) -> None:
        for phase, surface in (("F26", "learnback"), ("F27", "factory-maturity")):
            with self.subTest(phase=phase):
                card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
                card["phase"] = phase
                card["surfaces"] = [surface]
                card["evidence_expected"] = ["learnback and maturity audit record"]

                required, reason = factoryctl.worker_required("skill-eval-distiller", card)
                packet = factoryctl.build_worker_packet("skill-eval-distiller", card, Path("<memory>"))

                self.assertTrue(required, reason)
                self.assertIn("learnback/maturity", reason)
                self.assertTrue(packet["trigger"]["required"])
                self.assertEqual(packet["worker"]["factory_phase"], "F8/F18/F26/F27")
                self.assertEqual(packet["status"], "requires_execution")

    def test_learnback_without_agent_eval_plan_blocks_instead_of_passing_as_status_text(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["phase"] = "F26"
        card["surfaces"] = ["learnback"]
        card["evidence_expected"] = ["blocked recovery loop learnback"]
        card.pop("agent_eval_plan", None)

        report = factoryctl.build_gate_report(card)

        self.assertIn("skill-eval-distiller", report["required_workers"])
        self.assertEqual(report["workers"]["skill-eval-distiller"]["status"], "blocked_missing_inputs")
        self.assertIn("skill-eval-distiller", report["blocked_workers"])
        self.assertEqual(report["gate_status"], "blocked")

    def test_learnback_surface_routes_to_skill_eval_distiller_before_phase_is_updated(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["phase"] = "F12"
        card["surfaces"] = ["learnback"]
        card["evidence_expected"] = ["blocked recovery loop learnback"]

        required, reason = factoryctl.worker_required("skill-eval-distiller", card)

        self.assertTrue(required, reason)
        self.assertIn("learnback/maturity", reason)

    def test_security_scan_packet_can_require_codex_security_on_r2_product_face(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")

        report = factoryctl.build_gate_report(card)

        self.assertTrue(report["workers"]["codex-security"]["required"])
        self.assertEqual(report["workers"]["codex-security"]["status"], "requires_execution")
        self.assertIn("codex-security", report["required_workers"])

    def test_worker_packet_source_card_ref_is_public_safe(self) -> None:
        card_path = ROOT / "examples" / "minimal-hermes-project" / "card.md"
        card = factoryctl.load_json_like(card_path)

        packet = factoryctl.build_worker_packet("handoff-packer", card, card_path)

        self.assertEqual(packet["source_card_path"], "examples/minimal-hermes-project/card.md")
        self.assertIsNone(PRIVATE_PATH_RE.search(packet["source_card_path"]))

    def test_external_worker_packet_source_card_ref_is_redacted(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        external_path = Path("C:/Users/private/secret-product-card.md")

        packet = factoryctl.build_worker_packet("handoff-packer", card, external_path)

        self.assertEqual(packet["source_card_path"], "external:secret-product-card.md")
        self.assertIsNone(PRIVATE_PATH_RE.search(packet["source_card_path"]))

    def test_memory_style_source_card_ref_cannot_preserve_paths(self) -> None:
        self.assertEqual(factoryctl.source_card_ref(Path("<memory>")), "external:memory")
        self.assertEqual(factoryctl.source_card_ref(Path("<C:/Users/private/card.md>")), "external:source-card")
        self.assertEqual(factoryctl.source_card_ref(Path("<private/path/card.md>")), "external:source-card")

    def test_public_worker_registry_matches_factoryctl_workers(self) -> None:
        registry = json.loads((ROOT / "agents" / "worker-registry.public.json").read_text(encoding="utf-8"))
        registered = {worker["worker_id"] for worker in registry["workers"]}

        self.assertEqual(registered, set(factoryctl.WORKERS))

    def test_worker_result_schema_allows_every_registered_output(self) -> None:
        schema = json.loads((ROOT / "schemas" / "worker-result.schema.json").read_text(encoding="utf-8"))
        allowed = set(schema["properties"]["record_type"]["enum"])
        outputs = {worker.output_field for worker in factoryctl.WORKERS.values()}

        self.assertEqual(allowed, outputs | {"human_gate_record"})

    def test_minimal_example_card_matches_hermes_ready_gate_constraints(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "minimal-hermes-project" / "card.md")
        self.assertEqual(factoryctl.validate_card(card), [])

    def test_vfinal_card_requires_core_canonical_contracts(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        self.assertEqual(factoryctl.validate_card(card), [])

        incomplete = dict(card)
        incomplete.pop("product_sot")
        incomplete.pop("spec_graph")

        errors = factoryctl.validate_card(incomplete)

        self.assertIn("OVERKILL_VFINAL card missing core contracts: product_sot, spec_graph", errors)

    def test_vfinal_material_execution_requires_sdlc_feedback_loop_ref(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card.pop("sdlc_feedback_loop_ref", None)

        errors = factoryctl.validate_card(card)

        self.assertIn("sdlc_feedback_loop_ref required for material vFinal autonomous execution", errors)

    def test_vfinal_planning_only_does_not_require_sdlc_feedback_loop_ref(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card.pop("sdlc_feedback_loop_ref", None)
        card["authority_max"] = "validate_gate_only"
        card["runtime_contract"] = dict(card["runtime_contract"], mode="planning_only")
        card["autonomy_readiness_packet"] = dict(card["autonomy_readiness_packet"], execution_mode="planning_only")
        card["agent_runtime_hardening_profile"] = dict(
            card["agent_runtime_hardening_profile"],
            execution_mode="planning_only",
        )

        errors = factoryctl.validate_card(card)

        self.assertNotIn("sdlc_feedback_loop_ref required for material vFinal autonomous execution", errors)

    def test_vfinal_feedback_loop_ref_must_be_public_safe(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["sdlc_feedback_loop_ref"] = "C:/Users/felip/private/feedback-loop.json"

        errors = factoryctl.validate_card(card)

        self.assertIn("sdlc_feedback_loop_ref must be public-safe", errors)

    def test_vfinal_method_contract_requires_named_plan_fields(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["method_contract"] = dict(card["method_contract"])
        card["method_contract"]["required_plans"] = ["software_development_plan", "agent_eval_plan"]
        card.pop("agent_eval_plan", None)

        self.assertIn(
            "method_contract required plan agent_eval_plan is missing from card",
            factoryctl.validate_card(card),
        )

    def test_product_face_decomposition_requires_result_ref(self) -> None:
        card = dict(factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md"))
        card["phase"] = "F11"
        card.pop("product_face_result_ref", None)
        card.pop("product_face_result", None)

        self.assertIn(
            "product_face_result or product_face_result_ref required before decomposition/release",
            factoryctl.validate_card(card),
        )

    def test_terminal_product_face_result_ref_missing_fails_closed(self) -> None:
        card = self.terminal_product_face_ref_card()
        card["product_face_result_ref"] = "reports/product-face/missing-result.json"

        errors = factoryctl.validate_card(card)

        self.assertIn("product_face_result_ref does not exist: reports/product-face/missing-result.json", errors)

    def test_terminal_product_face_empty_inline_result_fails_closed(self) -> None:
        card = self.terminal_product_face_ref_card()
        card["product_face_result"] = {}

        errors = factoryctl.validate_card(card)

        self.assertIn("product_face_result missing result, tool_or_profile, executed_by, performance_note, next_action", errors)

    def test_terminal_product_face_result_ref_missing_fails_in_all_result_phases(self) -> None:
        card = self.terminal_product_face_ref_card()
        card["phase"] = "F13"
        card["product_face_result_ref"] = "reports/product-face/missing-result.json"

        errors = factoryctl.validate_card(card)

        self.assertIn("product_face_result_ref does not exist: reports/product-face/missing-result.json", errors)

    def test_terminal_product_face_result_ref_malformed_json_fails_closed(self) -> None:
        card = self.terminal_product_face_ref_card()
        ref = self.write_temp_product_face_result("{not valid json")
        card["product_face_result_ref"] = ref

        errors = factoryctl.validate_card(card)

        self.assertTrue(
            any(error.startswith(f"product_face_result_ref is not valid JSON: {ref}:") for error in errors),
            errors,
        )

    def test_terminal_product_face_result_ref_weak_pass_fails_closed(self) -> None:
        card = self.terminal_product_face_ref_card()
        weak_result = product_face_result_fixture(screenshots=["not-captured: fake"])
        ref = self.write_temp_product_face_result(weak_result)
        card["product_face_result_ref"] = ref

        errors = factoryctl.validate_card(card)

        self.assertIn(
            f"product_face_result_ref {ref}: product_face_result screenshots must reference captured artifacts",
            errors,
        )

    def test_terminal_product_face_result_ref_stale_result_fails_closed(self) -> None:
        card = self.terminal_product_face_ref_card()
        stale_result = product_face_result_fixture(active=False, superseded_by="new-product-face-result.json")
        ref = self.write_temp_product_face_result(stale_result)
        card["product_face_result_ref"] = ref

        errors = factoryctl.validate_card(card)

        self.assertIn(
            f"product_face_result_ref {ref}: referenced product_face_result is inactive or superseded",
            errors,
        )

    def test_terminal_product_face_result_ref_valid_result_passes(self) -> None:
        card = self.terminal_product_face_ref_card()
        ref = self.write_temp_product_face_result(product_face_result_fixture())
        card["product_face_result_ref"] = ref

        self.assertEqual(factoryctl.validate_card(card), [])

    def test_terminal_product_face_result_ref_external_cannot_claim_full_acceptance(self) -> None:
        card = self.terminal_product_face_ref_card()
        card["product_face_result_ref"] = "external:operator-owned-product-face-result"

        self.assertIn(
            "product_face_result_ref external refs cannot satisfy full product acceptance "
            "without an inline or validated local/sanitized product_face_result package",
            factoryctl.validate_card(card),
        )

    def test_vfinal_product_surface_requires_product_experience_os_contract(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["surfaces"] = ["frontend", "product-face"]
        card["capability_pack_contract"] = dict(card["capability_pack_contract"])
        card["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
        card.pop("product_experience_plan", None)
        card["product_face_packet"] = {"screen_inventory": ["dashboard"]}

        errors = factoryctl.validate_card(card)

        self.assertIn("product_experience_plan required for vFinal product-facing surfaces", errors)
        self.assertIn("product_face_packet.surface is required", errors)
        self.assertIn("product_face_packet.design_direction is required", errors)

    def test_vfinal_product_experience_surfaces_route_to_product_face(self) -> None:
        for surface in ("website", "desktop", "extension", "docs", "agentic_interface", "ai_interface", "design_system"):
            with self.subTest(surface=surface):
                card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
                card["surfaces"] = [surface]
                card["capability_pack_contract"] = dict(card["capability_pack_contract"])
                card["capability_pack_contract"]["covered_surfaces"] = [surface]
                card.pop("product_experience_plan", None)
                card.pop("product_face_packet", None)

                errors = factoryctl.validate_card(card)

                self.assertIn("product_experience_plan required for vFinal product-facing surfaces", errors)
                self.assertIn("product_face_packet required for product-facing surfaces", errors)
                required, reason = factoryctl.worker_required("product-face", card)
                self.assertTrue(required, reason)

    def test_legacy_docs_surface_does_not_implicitly_require_product_face(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "factory-card.json")

        required, reason = factoryctl.worker_required("product-face", card)

        self.assertFalse(required, reason)

    def test_vfinal_product_surface_accepts_product_experience_os_contract(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["surfaces"] = ["frontend", "product-face"]
        card["capability_pack_contract"] = dict(card["capability_pack_contract"])
        card["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
        card["method_contract"] = dict(card["method_contract"])
        card["method_contract"]["required_plans"] = ["software_development_plan", "product_experience_plan"]
        card["product_experience_plan"] = factoryctl.load_json_like(ROOT / "templates" / "product-experience-plan.json")
        card["product_face_packet"] = factoryctl.load_json_like(ROOT / "templates" / "product-face-packet.json")
        journeys = ["primary happy path", "empty/loading/error path", "primary user flow", "blocked/error recovery flow"]
        states = ["empty", "loading", "success", "error"]
        viewports = ["desktop 1440x900", "mobile 390x844"]
        card["product_face_result_ref"] = self.write_temp_product_face_result(
            product_face_result_fixture(
                checked_states=states,
                user_journeys_checked=journeys,
                usage_evidence_matrix=usage_evidence_matrix_fixture(
                    journeys=journeys,
                    states=states,
                    viewports=viewports,
                ),
            )
        )

        self.assertEqual(factoryctl.validate_card(card), [])

    def test_product_experience_runtime_enforces_schema_required_fields(self) -> None:
        schema = factoryctl.load_json_like(ROOT / "schemas" / "product-experience-plan.schema.json")
        required_fields = schema["required"]

        for field in required_fields:
            with self.subTest(field=field):
                card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
                card["surfaces"] = ["frontend", "product-face"]
                card["capability_pack_contract"] = dict(card["capability_pack_contract"])
                card["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
                card["method_contract"] = dict(card["method_contract"])
                card["method_contract"]["required_plans"] = ["software_development_plan", "product_experience_plan"]
                card["product_experience_plan"] = factoryctl.load_json_like(
                    ROOT / "templates" / "product-experience-plan.json"
                )
                card["product_experience_plan"].pop(field, None)

                errors = factoryctl.validate_card(card)

                self.assertTrue(
                    any(error.startswith(f"product_experience_plan.{field}") for error in errors),
                    errors,
                )

    def test_product_experience_runtime_enforces_schema_field_shapes(self) -> None:
        cases = [
            (
                "product_face_result_required",
                lambda plan: plan.__setitem__("product_face_result_required", "true"),
                "product_experience_plan.product_face_result_required must be boolean",
            ),
            (
                "human_gate_reason",
                lambda plan: plan.__setitem__("human_gate", {"required": False, "approver": ""}),
                "product_experience_plan.human_gate.reason is required",
            ),
            (
                "visual_quality_bar_required_fields",
                lambda plan: plan.__setitem__("visual_quality_bar", {"reference_quality_bar": "Professional bar"}),
                "product_experience_plan.visual_quality_bar.anti_generic_criteria is required",
            ),
        ]

        for name, mutate, expected_error in cases:
            with self.subTest(name=name):
                card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
                card["surfaces"] = ["frontend", "product-face"]
                card["capability_pack_contract"] = dict(card["capability_pack_contract"])
                card["capability_pack_contract"]["covered_surfaces"] = ["frontend", "product-face"]
                card["method_contract"] = dict(card["method_contract"])
                card["method_contract"]["required_plans"] = ["software_development_plan", "product_experience_plan"]
                card["product_experience_plan"] = factoryctl.load_json_like(
                    ROOT / "templates" / "product-experience-plan.json"
                )
                mutate(card["product_experience_plan"])

                errors = factoryctl.validate_card(card)

                self.assertIn(expected_error, errors)

    def test_data_metrics_plan_rejects_prose_only_or_empty_delivery_proof(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["data_metrics_plan"] = {
            "$schema": "https://overkill-factory.dev/schemas/data-metrics-plan.schema.json",
            "gate_enforcement": "strict",
            "success_metrics": [],
            "events": ["looks good"],
            "owners": [],
            "privacy_limits": [],
            "risk_metrics": [],
            "logs": [],
            "alerts": [],
            "personal_data": [],
            "visibility": [],
            "instrumentation_proof": ["nice dashboard someday"],
            "dashboards": [],
            "evidence_refs": [],
        }

        errors = factoryctl.validate_card(card)

        self.assertIn("data_metrics_plan.success_metrics must be a non-empty array", errors)
        self.assertIn("data_metrics_plan.events[0] must be a stable event id, not prose", errors)
        self.assertIn("data_metrics_plan.dashboards must be a non-empty array", errors)
        self.assertIn("data_metrics_plan.evidence_refs must be a non-empty array", errors)

    def test_vfinal_data_metrics_plan_cannot_skip_deep_validation_by_omitting_gate(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["data_metrics_plan"] = {
            "$schema": "https://overkill-factory.dev/schemas/data-metrics-plan.schema.json",
            "success_metrics": [],
            "events": ["looks good"],
            "owners": [],
            "privacy_limits": [],
            "risk_metrics": [],
            "logs": [],
            "alerts": [],
            "personal_data": [],
            "visibility": [],
            "instrumentation_proof": ["nice dashboard someday"],
            "dashboards": [],
            "evidence_refs": [],
        }

        errors = factoryctl.validate_card(card)

        self.assertIn("data_metrics_plan.success_metrics must be a non-empty array", errors)
        self.assertIn("data_metrics_plan.events[0] must be a stable event id, not prose", errors)
        self.assertIn("data_metrics_plan.dashboards must be a non-empty array", errors)
        self.assertIn("data_metrics_plan.evidence_refs must be a non-empty array", errors)

    def test_vfinal_data_metrics_plan_rejects_advisory_gate(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["data_metrics_plan"] = factoryctl.load_json_like(ROOT / "templates" / "data-metrics-plan.json")
        card["data_metrics_plan"]["gate_enforcement"] = "advisory"

        errors = factoryctl.validate_card(card)

        self.assertIn("data_metrics_plan.gate_enforcement must be strict or production for OVERKILL_VFINAL cards", errors)

    def test_vfinal_data_metrics_plan_rejects_missing_or_unknown_gate_even_when_body_is_valid(self) -> None:
        for gate in (None, "experimental"):
            with self.subTest(gate=gate):
                card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
                card["data_metrics_plan"] = factoryctl.load_json_like(ROOT / "templates" / "data-metrics-plan.json")
                if gate is None:
                    card["data_metrics_plan"].pop("gate_enforcement", None)
                else:
                    card["data_metrics_plan"]["gate_enforcement"] = gate

                errors = factoryctl.validate_card(card)

                self.assertIn(
                    "data_metrics_plan.gate_enforcement must be strict or production for OVERKILL_VFINAL cards",
                    errors,
                )

    def test_user_docs_onboarding_plan_rejects_missing_first_success_and_proof(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["user_docs_onboarding_plan"] = {
            "$schema": "https://overkill-factory.dev/schemas/user-docs-onboarding-plan.schema.json",
            "gate_enforcement": "strict",
            "audience": "",
            "tasks_covered": [],
            "proof_required": ["someone reads it eventually"],
            "evidence_refs": [],
        }

        errors = factoryctl.validate_card(card)

        self.assertIn("user_docs_onboarding_plan.audience is required", errors)
        self.assertIn("user_docs_onboarding_plan.first_success_path is required", errors)
        self.assertIn("user_docs_onboarding_plan.tasks_covered must be a non-empty array", errors)
        self.assertIn("user_docs_onboarding_plan.evidence_refs must be a non-empty array", errors)

    def test_required_user_docs_onboarding_plan_cannot_skip_deep_validation_by_omitting_gate(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["method_contract"] = dict(card["method_contract"])
        card["method_contract"]["required_plans"] = list(card["method_contract"]["required_plans"]) + [
            "user_docs_onboarding_plan"
        ]
        card["user_docs_onboarding_plan"] = {
            "$schema": "https://overkill-factory.dev/schemas/user-docs-onboarding-plan.schema.json",
            "audience": "",
            "tasks_covered": [],
            "proof_required": ["someone reads it eventually"],
            "evidence_refs": [],
        }

        errors = factoryctl.validate_card(card)

        self.assertIn("user_docs_onboarding_plan.audience is required", errors)
        self.assertIn("user_docs_onboarding_plan.first_success_path is required", errors)
        self.assertIn("user_docs_onboarding_plan.tasks_covered must be a non-empty array", errors)
        self.assertIn("user_docs_onboarding_plan.evidence_refs must be a non-empty array", errors)

    def test_present_user_docs_onboarding_plan_cannot_skip_deep_validation_outside_required_plans(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["user_docs_onboarding_plan"] = {
            "$schema": "https://overkill-factory.dev/schemas/user-docs-onboarding-plan.schema.json",
            "audience": "",
            "tasks_covered": [],
            "proof_required": ["someone reads it eventually"],
            "evidence_refs": [],
        }

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "user_docs_onboarding_plan.gate_enforcement must be strict or production for OVERKILL_VFINAL cards",
            errors,
        )
        self.assertIn("user_docs_onboarding_plan.audience is required", errors)
        self.assertIn("user_docs_onboarding_plan.first_success_path is required", errors)
        self.assertIn("user_docs_onboarding_plan.tasks_covered must be a non-empty array", errors)
        self.assertIn("user_docs_onboarding_plan.evidence_refs must be a non-empty array", errors)

    def test_vfinal_user_docs_onboarding_plan_rejects_advisory_gate(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["method_contract"] = dict(card["method_contract"])
        card["method_contract"]["required_plans"] = list(card["method_contract"]["required_plans"]) + [
            "user_docs_onboarding_plan"
        ]
        card["user_docs_onboarding_plan"] = factoryctl.load_json_like(ROOT / "templates" / "user-docs-onboarding-plan.json")
        card["user_docs_onboarding_plan"]["gate_enforcement"] = "advisory"

        errors = factoryctl.validate_card(card)

        self.assertIn(
            "user_docs_onboarding_plan.gate_enforcement must be strict or production for OVERKILL_VFINAL cards",
            errors,
        )

    def test_vfinal_user_docs_onboarding_plan_rejects_missing_or_unknown_gate_even_when_body_is_valid(self) -> None:
        for gate in (None, "experimental"):
            with self.subTest(gate=gate):
                card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
                card["user_docs_onboarding_plan"] = factoryctl.load_json_like(
                    ROOT / "templates" / "user-docs-onboarding-plan.json"
                )
                if gate is None:
                    card["user_docs_onboarding_plan"].pop("gate_enforcement", None)
                else:
                    card["user_docs_onboarding_plan"]["gate_enforcement"] = gate

                errors = factoryctl.validate_card(card)

                self.assertIn(
                    "user_docs_onboarding_plan.gate_enforcement must be strict or production for OVERKILL_VFINAL cards",
                    errors,
                )

    def test_schema_backed_data_and_docs_plan_templates_remain_valid_for_vfinal(self) -> None:
        card = factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")
        card["method_contract"] = dict(card["method_contract"])
        card["method_contract"]["required_plans"] = list(card["method_contract"]["required_plans"]) + [
            "data_metrics_plan",
            "user_docs_onboarding_plan",
        ]
        card["data_metrics_plan"] = factoryctl.load_json_like(ROOT / "templates" / "data-metrics-plan.json")
        card["user_docs_onboarding_plan"] = factoryctl.load_json_like(ROOT / "templates" / "user-docs-onboarding-plan.json")

        errors = factoryctl.validate_card(card)

        self.assertEqual(errors, [])

    def test_product_face_completion_requires_visual_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "pending",
                "next_action": "attach Product Face proof",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md"],
            },
        }

        self.assertIn(
            "product_face_result metadata is required for product-facing completion",
            factoryctl.validate_completion(card, receipt),
        )

    def test_product_face_completion_accepts_visual_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "ready for independent review",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five", "product_face_result"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md", "reports/product-face.md"],
                "allowed": True,
            },
            "independent_review_result": worker_result("independent_review_result", source_card=card),
            "receipt_five_reconciliation_result": worker_result("receipt_five_reconciliation_result", source_card=card),
            "product_face_result": product_face_result_fixture(),
        }

        self.assertEqual(factoryctl.validate_completion(card, receipt), [])

    def test_product_face_completion_rejects_waived_visual_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        waived_result = product_face_result_fixture(
            result="WAIVED",
            blocking_findings=True,
            visual_quality_result={
                "status": "BLOCK",
                "reviewer": "product-face-reviewer",
                "basis": "Fallback proof did not establish reusable product quality.",
                "reference_quality_bar_checked": False,
                "ai_generic_symptoms": ["fallback evidence only"],
            },
            next_action="rerun Product Face proof with real rendered evidence",
        )
        receipt = {
            "receipt_five": {
                "changed": "attempted visible SaaS scenario proof",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "rerun Product Face proof",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five", "product_face_result"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md", "reports/product-face.md"],
                "allowed": True,
            },
            "independent_review_result": worker_result("independent_review_result", source_card=card),
            "receipt_five_reconciliation_result": worker_result("receipt_five_reconciliation_result", source_card=card),
            "product_face_result": waived_result,
        }

        errors = factoryctl.validate_completion(card, receipt)

        self.assertIn("product_face_result WAIVED cannot satisfy required Product Face completion", errors)

    def test_product_face_completion_requires_domain_proof_coverage_when_profile_declares_it(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile"] = product_delivery_quality_profile_fixture()

        errors = factoryctl.validate_product_face_result_against_card(product_face_result_fixture(), card)

        self.assertIn(
            "product_face_result.domain_proof_coverage missing required product delivery proof ids: game.playable-smoke",
            errors,
        )

    def test_product_face_completion_requires_usage_evidence_matrix(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        result = product_face_result_fixture(usage_evidence_matrix=[])

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn("product_face_result.usage_evidence_matrix is required for PASS", errors)
        self.assertIn("product_face_result.usage_evidence_matrix is required for product-facing completion", errors)

    def test_product_face_pass_requires_visual_artifact_records(self) -> None:
        result = product_face_result_fixture(visual_artifacts=[])

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn("product_face_result.visual_artifacts is required for PASS", errors)

    def test_product_face_pass_rejects_missing_repo_local_visual_artifact(self) -> None:
        result = product_face_result_fixture(
            screenshots=["reports/product-face/missing-desktop.png"],
            viewports=["desktop 1440x900"],
            checked_states=["success"],
            user_journeys_checked=["pilot status review"],
            usage_evidence_matrix=[
                {
                    "journey": "pilot status review",
                    "state": "success",
                    "viewport": "desktop 1440x900",
                    "data_condition": "success fixture",
                    "evidence_refs": ["reports/product-face/missing-desktop.png"],
                    "a11y_status": "pass",
                    "performance_status": "pass",
                    "reviewer": "product-face-reviewer",
                    "basis": "Missing artifact should fail closed.",
                }
            ],
            visual_artifacts=[
                {
                    "evidence_ref": "reports/product-face/missing-desktop.png",
                    "target": "examples/cards/v35_valid_product_face.md",
                    "viewport": "desktop 1440x900",
                    "state": "success",
                    "captured_at": "2026-06-16T00:00:00+00:00",
                    "freshness_status": "fresh",
                }
            ],
        )

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn(
            "product_face_result.visual_artifacts[0]: evidence ref does not exist: reports/product-face/missing-desktop.png",
            errors,
        )

    def test_product_face_pass_rejects_stale_visual_artifact(self) -> None:
        result = product_face_result_fixture()
        result["visual_artifacts"][0]["freshness_status"] = "stale"

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn("product_face_result.visual_artifacts[0].freshness_status must be fresh or bounded_external", errors)

    def test_product_face_pass_rejects_external_visual_artifact_without_manifest(self) -> None:
        result = product_face_result_fixture(external_visual_artifact_manifests=[])

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn(
            "product_face_result.visual_artifacts[0].external_package_ref must resolve to external_visual_artifact_manifests entry: external:product-face-fixture-package",
            errors,
        )

    def test_product_face_pass_rejects_stale_external_visual_manifest(self) -> None:
        result = product_face_result_fixture()
        result["external_visual_artifact_manifests"][0]["expires_at"] = "2026-01-01T00:00:00+00:00"

        errors = factoryctl.validate_product_face_result(result)

        self.assertTrue(
            any("external_manifest[external:product-face-fixture-package] is stale" in error for error in errors),
            errors,
        )

    def test_product_face_pass_rejects_external_visual_manifest_state_viewport_mismatch(self) -> None:
        result = product_face_result_fixture()
        result["external_visual_artifact_manifests"][0]["artifacts"][0]["state"] = "unrelated-state"

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn(
            "product_face_result.visual_artifacts[0].external_manifest[external:product-face-fixture-package].artifacts must include evidence_ref/state/viewport binding for external:product-face-fixture-desktop.png",
            errors,
        )

    def test_product_face_pass_accepts_external_visual_manifest_binding(self) -> None:
        result = product_face_result_fixture()

        self.assertEqual(factoryctl.validate_product_face_result(result), [])

    def test_product_face_pass_rejects_reference_quality_prose_only_comparison(self) -> None:
        result = product_face_result_fixture()
        result["reference_quality_comparison"].pop("comparison_artifacts")

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn(
            "product_face_result.reference_quality_comparison.comparison_artifacts must include material comparison artifacts for PASS",
            errors,
        )

    def test_product_face_pass_rejects_unknown_compared_reference_id(self) -> None:
        result = product_face_result_fixture()
        result["reference_quality_comparison"]["compared_source_ids"] = [
            "21st-dev-components",
            "mobbin-workflow-patterns",
            "unknown-design-reference",
        ]
        result["reference_quality_comparison"]["comparison_artifacts"][0]["compared_source_ids"] = [
            "21st-dev-components",
            "mobbin-workflow-patterns",
            "unknown-design-reference",
        ]

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn(
            "product_face_result.reference_quality_comparison.compared_source_ids not found in reference sources: unknown-design-reference",
            errors,
        )

    def test_product_face_pass_rejects_missing_reference_comparison_artifact(self) -> None:
        result = product_face_result_fixture()
        result["reference_quality_comparison"]["comparison_artifacts"] = [
            {
                "artifact_ref": "reports/product-face/missing-reference-comparison.png",
                "artifact_type": "side_by_side_capture",
                "compared_source_ids": result["reference_quality_comparison"]["compared_source_ids"],
                "basis": "Missing repo-local comparison artifact must fail closed.",
            }
        ]

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn(
            "product_face_result.reference_quality_comparison.comparison_artifacts[0]: evidence ref does not exist: reports/product-face/missing-reference-comparison.png",
            errors,
        )

    def test_product_face_pass_accepts_external_reference_source_manifest(self) -> None:
        result = product_face_result_fixture()
        compared_source_ids = result["reference_quality_comparison"]["compared_source_ids"]
        result["reference_quality_comparison"]["reference_set_ref"] = "external:product-face-reference-source-manifest"
        result["reference_quality_comparison"]["reference_source_manifest"] = {
            "manifest_ref": "external:product-face-reference-source-manifest",
            "bounded_acceptance": True,
            "sanitized": True,
            "sources": [{"source_id": source_id} for source_id in compared_source_ids],
        }

        self.assertEqual(factoryctl.validate_product_face_result(result), [])

    def test_product_face_pass_rejects_synthetic_reusable_product_claim(self) -> None:
        result = product_face_result_fixture(evidence_kind="synthetic", reusable_for_product=True)

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn("product_face_result synthetic PASS must set reusable_for_product=false", errors)

    def test_product_face_pass_allows_non_reusable_synthetic_smoke_record(self) -> None:
        result = product_face_result_fixture(
            evidence_kind="synthetic",
            reusable_for_product=False,
            product_acceptance_boundary={
                "boundary": "synthetic_smoke_only",
                "cannot_satisfy_product_acceptance": True,
                "next_required_action": "run real Product Face proof before product-facing completion",
            },
        )

        self.assertEqual(factoryctl.validate_product_face_result(result), [])

    def test_product_face_completion_rejects_synthetic_pass_even_when_non_reusable(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        result = product_face_result_fixture(
            evidence_kind="synthetic",
            reusable_for_product=False,
            product_acceptance_boundary={
                "boundary": "synthetic_smoke_only",
                "cannot_satisfy_product_acceptance": True,
                "next_required_action": "run real Product Face proof before product-facing completion",
            },
        )

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn("product_face_result synthetic evidence cannot satisfy product-facing completion", errors)

    def test_product_face_completion_accepts_real_pass_boundary(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        result = product_face_result_fixture(evidence_kind="real", reusable_for_product=True)

        self.assertEqual(factoryctl.validate_product_face_result_against_card(result, card), [])

    def test_product_face_pass_rejects_state_viewport_artifact_mismatch(self) -> None:
        result = product_face_result_fixture()
        result["visual_artifacts"] = [dict(result["visual_artifacts"][0], state="success")]

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn(
            "product_face_result.usage_evidence_matrix[0] lacks visual_artifacts binding for state/viewport",
            errors,
        )

    def test_product_face_pass_rejects_uncaptured_state_or_journey_overclaim(self) -> None:
        result = product_face_result_fixture(
            uncaptured_states=["loading"],
            uncaptured_journeys=["checkout happy path"],
        )

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn("product_face_result PASS cannot include uncaptured_states", errors)
        self.assertIn("product_face_result PASS cannot include uncaptured_journeys", errors)

    def test_product_face_pass_accepts_resolvable_visual_artifact_with_hash(self) -> None:
        artifact_ref, artifact_hash = self.write_temp_visual_artifact()
        viewports = ["desktop 1440x900"]
        states = ["success"]
        result = product_face_result_fixture(
            screenshots=[artifact_ref],
            viewports=viewports,
            checked_states=states,
            user_journeys_checked=["pilot status review"],
            usage_evidence_matrix=[
                {
                    "journey": "pilot status review",
                    "state": "success",
                    "viewport": "desktop 1440x900",
                    "data_condition": "success fixture",
                    "evidence_refs": [artifact_ref],
                    "a11y_status": "pass",
                    "performance_status": "pass",
                    "reviewer": "product-face-reviewer",
                    "basis": "Repo-local visual artifact exists and is hash-bound.",
                }
            ],
            visual_artifacts=[
                {
                    "evidence_ref": artifact_ref,
                    "target": "examples/cards/v35_valid_product_face.md",
                    "viewport": "desktop 1440x900",
                    "state": "success",
                    "captured_at": "2026-06-16T00:00:00+00:00",
                    "freshness_status": "fresh",
                    "sha256": artifact_hash,
                }
            ],
        )

        errors = factoryctl.validate_product_face_result(result)

        self.assertEqual(errors, [])

    def test_product_face_completion_requires_usage_matrix_planned_flow_coverage(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        result = product_face_result_fixture()
        result["usage_evidence_matrix"] = [
            entry for entry in result["usage_evidence_matrix"] if entry["journey"] != "review evidence inspection"
        ]

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn(
            "product_face_result.usage_evidence_matrix missing checked journey coverage: review evidence inspection",
            errors,
        )
        self.assertIn(
            "product_face_result.usage_evidence_matrix missing planned flow coverage: review evidence inspection",
            errors,
        )

    def test_product_face_completion_rejects_disconnected_usage_dimensions(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        result = product_face_result_fixture()
        result["usage_evidence_matrix"] = [
            entry
            for entry in result["usage_evidence_matrix"]
            if not (
                entry["journey"] == "pilot status review"
                and entry["state"] == "pending"
                and "mobile" in entry["viewport"]
            )
        ]

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn(
            "product_face_result.usage_evidence_matrix missing required journey/state/viewport combinations: "
            "pilot status review/pending/mobile",
            errors,
        )

    def test_product_face_completion_requires_usage_matrix_state_and_viewport_coverage(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        result = product_face_result_fixture()
        result["usage_evidence_matrix"] = [
            entry
            for entry in result["usage_evidence_matrix"]
            if entry["state"] != "pending" and "mobile" not in entry["viewport"]
        ]

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn("product_face_result.usage_evidence_matrix missing state coverage: pending", errors)
        self.assertIn("product_face_result.usage_evidence_matrix missing viewport coverage: mobile", errors)

    def test_product_face_completion_requires_activated_pack_domain_proofs(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["capability_pack_contract"] = activated_game_contract_fixture()

        errors = factoryctl.validate_product_face_result_against_card(product_face_result_fixture(), card)

        self.assertIn(
            "product_face_result.domain_proof_coverage missing required product delivery proof ids: game.design-packet, game.performance-budget, game.playable-smoke, game.playtest-review, game.runtime-choice",
            errors,
        )

    def test_product_face_completion_accepts_activated_pack_domain_proofs(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["capability_pack_contract"] = activated_game_contract_fixture()
        result = product_face_result_fixture(
            domain_proof_coverage=[
                {
                    "proof_id": "generic.operator-usability",
                    "status": "PASS",
                    "evidence_refs": ["reports/domain-proof/generic.operator-usability.json"],
                    "reviewer": "domain-proof-reviewer",
                    "reviewer_role": "independent-reviewer",
                    "evidence_kind": "review",
                    "basis": "Operator usability proof passed with structured evidence.",
                }
            ]
            + [
                {
                    "proof_id": proof_id,
                    "status": "PASS",
                    "evidence_refs": [f"reports/domain-proof/{proof_id}.json"],
                    "reviewer": "domain-proof-reviewer",
                    "basis": f"{proof_id} passed with structured evidence.",
                }
                for proof_id in card["capability_pack_contract"]["structured_proofs_required"]
            ]
        )

        self.assertEqual(factoryctl.validate_product_face_result_against_card(result, card), [])

    def test_product_face_completion_resolves_profile_ref_for_domain_proof_coverage(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile_ref"] = "templates/product-delivery-quality-profile.json"

        errors = factoryctl.validate_product_face_result_against_card(
            product_face_result_fixture(domain_proof_coverage=[]),
            card,
        )

        self.assertIn(
            "product_face_result.domain_proof_coverage missing product delivery proof coverage for required proof ids: generic.operator-usability",
            errors,
        )

    def test_product_face_completion_fails_closed_for_missing_profile_ref(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile_ref"] = "templates/missing-product-delivery-quality-profile.json"

        errors = factoryctl.validate_product_face_result_against_card(product_face_result_fixture(), card)

        self.assertIn(
            "card.product_delivery_quality_profile_ref does not resolve to a repo-local file: templates/missing-product-delivery-quality-profile.json",
            errors,
        )

    def test_product_face_completion_accepts_required_domain_proof_coverage(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile"] = product_delivery_quality_profile_fixture()
        result = product_face_result_fixture(
            domain_proof_coverage=[
                {
                    "proof_id": "game.playable-smoke",
                    "status": "PASS",
                    "evidence_refs": ["reports/game/playable-smoke.md"],
                    "reviewer": "game-qa-specialist",
                    "reviewer_role": "game-qa-specialist",
                    "evidence_kind": "runtime",
                    "basis": "Playable smoke covered input, feedback and completion feedback.",
                }
            ]
        )

        self.assertEqual(factoryctl.validate_product_face_result_against_card(result, card), [])

    def test_product_face_completion_rejects_domain_proof_wrong_reviewer_role(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile"] = human_gated_product_delivery_quality_profile_fixture()
        result = product_face_result_fixture(
            domain_proof_coverage=[
                {
                    "proof_id": "generic.operator-usability",
                    "status": "PASS",
                    "evidence_refs": ["reports/domain-proof/operator-usability.json"],
                    "reviewer_role": "domain-proof-reviewer",
                    "evidence_kind": "human_gate",
                    "human_gate_ref": "external:product-owner-approval",
                    "human_gate_bounded_acceptance": True,
                    "human_gate_sanitized": True,
                    "basis": "Wrong reviewer role should not satisfy the human-gated profile.",
                }
            ]
        )

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn(
            "product_face_result.domain_proof_coverage[0].reviewer_role must match required proof reviewer_role 'human-product-owner'",
            errors,
        )

    def test_product_face_completion_rejects_domain_proof_wrong_evidence_kind(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile"] = human_gated_product_delivery_quality_profile_fixture()
        result = product_face_result_fixture(
            domain_proof_coverage=[
                {
                    "proof_id": "generic.operator-usability",
                    "status": "PASS",
                    "evidence_refs": ["reports/domain-proof/operator-usability.json"],
                    "reviewer_role": "human-product-owner",
                    "evidence_kind": "review",
                    "human_gate_ref": "external:product-owner-approval",
                    "human_gate_bounded_acceptance": True,
                    "human_gate_sanitized": True,
                    "basis": "Wrong evidence kind should not satisfy the human-gated profile.",
                }
            ]
        )

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn(
            "product_face_result.domain_proof_coverage[0].evidence_kind must match required proof evidence_kind 'human_gate'",
            errors,
        )

    def test_product_face_completion_requires_human_gate_ref_for_human_gated_domain_proof(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile"] = human_gated_product_delivery_quality_profile_fixture()
        result = product_face_result_fixture(
            domain_proof_coverage=[
                {
                    "proof_id": "generic.operator-usability",
                    "status": "PASS",
                    "evidence_refs": ["reports/domain-proof/operator-usability.json"],
                    "reviewer_role": "human-product-owner",
                    "evidence_kind": "human_gate",
                    "basis": "Missing human gate ref should fail closed.",
                }
            ]
        )

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn(
            "product_face_result.domain_proof_coverage[0].human_gate_ref is required when required proof declares human_gate_required=true",
            errors,
        )

    def test_product_face_completion_accepts_human_gated_domain_proof_binding(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile"] = human_gated_product_delivery_quality_profile_fixture()
        result = product_face_result_fixture(
            domain_proof_coverage=[
                {
                    "proof_id": "generic.operator-usability",
                    "status": "PASS",
                    "evidence_refs": ["reports/domain-proof/operator-usability.json"],
                    "reviewer_role": "human-product-owner",
                    "evidence_kind": "human_gate",
                    "human_gate_ref": "external:product-owner-approval",
                    "human_gate_bounded_acceptance": True,
                    "human_gate_sanitized": True,
                    "basis": "Human product owner approved the operator usability proof.",
                }
            ]
        )

        self.assertEqual(factoryctl.validate_product_face_result_against_card(result, card), [])

    def test_product_face_completion_rejects_waived_domain_proof_as_full_acceptance(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_delivery_quality_profile"] = product_delivery_quality_profile_fixture()
        result = product_face_result_fixture(
            domain_proof_coverage=[
                {
                    "proof_id": "game.playable-smoke",
                    "status": "WAIVED",
                    "evidence_refs": ["reports/game/waiver.md"],
                    "basis": "Playable smoke is unavailable in this bounded proof.",
                    "waiver_owner": "product-owner",
                    "waiver_reason": "Runtime not activated yet.",
                }
            ]
        )

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn(
            "product_face_result.domain_proof_coverage[0] WAIVED proof cannot support full product acceptance",
            errors,
        )

    def test_validate_completion_requires_done_promotion_gate(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        receipt = {
            "receipt_five": {
                "changed": "validated onchain gate",
                "artifact_paths": ["examples/minimal-hermes-project/card.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md"],
                "verification_result": "PASS",
                "reviewer_required": False,
                "next_action": "continue",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "factory-orchestrator",
                "worker": "factory-orchestrator",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["examples/minimal-hermes-project/card.md"],
            },
        }

        errors = factoryctl.validate_completion(card, receipt)

        self.assertIn("kanban_transition_event.allowed must be true for done promotion", errors)
        self.assertIn("receipt_five_reconciliation_result is required for done promotion", errors)

    def test_completion_audit_blocks_done_with_blocked_sot_claim(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        audit = {
            "decision": "done",
            "sot_claim_results": [
                {"claim_ref": "product-sot#scope", "status": "BLOCKED", "owner": "product-owner"}
            ],
            "method_execution_results": [
                {"method": "security-review", "status": "EXECUTED", "evidence_refs": ["README.md"]}
            ],
        }

        errors = factoryctl.validate_completion_audit_contract(card, audit)

        self.assertIn("completion_audit.decision must be block when any SOT claim is BLOCKED", errors)

    def test_completion_audit_routes_deferred_sot_to_done_with_owner(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        audit = {
            "decision": "done",
            "sot_claim_results": [
                {"claim_ref": "product-sot#scope", "status": "DEFERRED_WITH_OWNER", "owner": "product-owner"}
            ],
            "method_execution_results": [
                {"method": "security-review", "status": "EXECUTED", "evidence_refs": ["README.md"]}
            ],
        }

        errors = factoryctl.validate_completion_audit_contract(card, audit)

        self.assertIn(
            "completion_audit.decision must be done_with_owner when any SOT claim is DEFERRED_WITH_OWNER",
            errors,
        )

    def test_product_face_completion_rejects_screenshot_without_plan_alignment(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "ready for independent review",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five", "product_face_result"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md", "reports/product-face.md"],
            },
            "product_face_result": {
                "result": "PASS",
                "tool_or_profile": "browser-proof-runner",
                "executed_by": "product-face-validator",
                "screenshots": ["reports/product-face/desktop.png", "reports/product-face/mobile.png"],
                "viewports": ["desktop 1440x900", "mobile 390x844"],
                "checked_states": ["empty", "loading", "success", "error"],
                "user_journeys_checked": ["dashboard to detail", "settings save"],
                "a11y": {"status": "pass"},
                "overlap_check": {"status": "pass"},
                "console": {"status": "pass"},
                "performance_note": "static validation scenario only",
                "blocking_findings": False,
                "evidence_refs": ["reports/product-face.md"],
                "next_action": "independent review",
            },
        }

        errors = factoryctl.validate_completion(card, receipt)

        self.assertIn("product_face_result.packet_comparison is required for product-facing completion", errors)
        self.assertIn("product_face_result.source_promise_coverage is required for product-facing completion", errors)
        self.assertIn("product_face_result.design_fit_review is required for product-facing completion", errors)
        self.assertIn("product_face_result.professional_design_process_comparison is required for product-facing completion", errors)
        self.assertIn("product_face_result.reference_quality_comparison is required for product-facing completion", errors)
        self.assertIn("product_face_result.professional_design_process_ref is required for PASS", errors)
        self.assertIn("product_face_result.visual_quality_result is required", errors)

    def test_product_face_completion_blocks_mechanically_ok_but_ai_generic_ui(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card["product_face_result_required"] = True
        receipt = {
            "receipt_five": {
                "changed": "validated visible SaaS scenario",
                "artifact_paths": ["examples/cards/v35_valid_product_face.md"],
                "verification_commands": ["python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "ready for independent review",
            },
            "kanban_transition_event": {
                "from_status": "review",
                "to_status": "done",
                "actor": "qa-verification-worker",
                "worker": "product-face",
                "receipt_refs": ["receipt_five", "product_face_result"],
                "artifact_refs": ["examples/cards/v35_valid_product_face.md", "reports/product-face.md"],
            },
            "product_face_result": {
                "result": "PASS",
                "tool_or_profile": "browser-proof-runner",
                "executed_by": "product-face-validator",
                "screenshots": ["reports/product-face/desktop.png", "reports/product-face/mobile.png"],
                "viewports": ["desktop 1440x900", "mobile 390x844"],
                "checked_states": ["empty", "loading", "success", "error"],
                "user_journeys_checked": ["dashboard to detail", "settings save"],
                "a11y": {"status": "pass"},
                "overlap_check": {"status": "pass"},
                "console": {"status": "pass"},
                "performance_note": "static validation scenario only",
                "packet_ref": "examples/cards/v35_valid_product_face.md#product_face_packet",
                "packet_comparison": {
                    "status": "pass",
                    "basis": "All planned screens, states and viewports are covered."
                },
                "source_promise_coverage": {
                    "status": "pass",
                    "basis": "The checked journey covers the product promise."
                },
                "design_fit_review": {
                    "status": "pass",
                    "basis": "Mechanical layout and state checks passed."
                },
                "professional_design_process_ref": "examples/cards/v35_valid_product_face.md#professional_design_process",
                "professional_design_process_comparison": {
                    "status": "pass",
                    "basis": "Mechanical proof claims the process was followed, but visual quality review blocks it."
                },
                "reference_quality_comparison": reference_quality_comparison_fixture(),
                "visual_quality_result": {
                    "status": "BLOCK",
                    "reviewer": "product-face-reviewer",
                    "basis": "The UI uses a generic dashboard composition with excessive explanatory copy and no product-specific visual direction.",
                    "reference_quality_bar_checked": True,
                    "ai_generic_symptoms": ["generic dashboard composition", "excessive explanatory copy"],
                },
                "blocking_findings": False,
                "evidence_refs": ["reports/product-face.md"],
                "next_action": "redesign visual system",
            },
        }

        errors = factoryctl.validate_completion(card, receipt)

        self.assertIn("product_face_result visual_quality_result BLOCK prevents Product Face PASS", errors)
        self.assertIn("product_face_result PASS requires visual_quality_result.status PASS or PASS_WITH_RESIDUALS", errors)

    def test_product_face_pass_rejects_blocking_or_warning_result(self) -> None:
        result = {
            "result": "PASS",
            "tool_or_profile": "browser-proof-runner",
            "executed_by": "product-face-validator",
            "screenshots": ["not-captured: fake"],
            "viewports": ["1440x900"],
            "checked_states": ["initial-render"],
            "user_journeys_checked": ["open target"],
            "a11y": {"status": "warn", "issues": ["missing label"]},
            "overlap_check": {"status": "warn", "issues": ["overlap"]},
            "performance_note": "static validation scenario only",
            "blocking_findings": True,
            "evidence_refs": ["reports/product-face.md"],
            "next_action": "fix UI",
        }

        errors = factoryctl.validate_product_face_result(result)

        self.assertIn("product_face_result PASS requires blocking_findings=false", errors)
        self.assertIn("product_face_result screenshots must reference captured artifacts", errors)
        self.assertIn("product_face_result PASS requires a11y.status=pass", errors)
        self.assertIn("product_face_result PASS requires overlap_check.status=pass", errors)
        self.assertIn("product_face_result.visual_quality_result is required", errors)

    def test_product_face_waived_allows_pending_reference_quality(self) -> None:
        result = {
            "result": "WAIVED",
            "tool_or_profile": "browser-proof-runner",
            "executed_by": "product-face-validator",
            "screenshots": ["not-captured: fallback"],
            "viewports": ["1440x900"],
            "checked_states": ["initial-render"],
            "user_journeys_checked": ["open target"],
            "a11y": {"status": "fail"},
            "overlap_check": {"status": "fail"},
            "performance_note": "fallback validation only",
            "packet_comparison": {"status": "pending", "basis": "Pending proof."},
            "source_promise_coverage": {"status": "pending", "basis": "Pending proof."},
            "design_fit_review": {"status": "pending", "basis": "Pending proof."},
            "professional_design_process_ref": "",
            "professional_design_process_comparison": {"status": "pending", "basis": "Pending proof."},
            "reference_quality_comparison": {
                "status": "pending",
                "basis": "Reference comparison not recorded yet.",
                "reference_set_ref": "pending-reference-set",
                "compared_source_ids": [],
                "reviewer_independent_from_implementation": False,
                "dimensions": {
                    dimension: {
                        "status": "pending",
                        "basis": "Reference comparison not recorded yet.",
                    }
                    for dimension in factoryctl.REFERENCE_COMPARISON_DIMENSIONS
                },
            },
            "visual_quality_result": {
                "status": "BLOCK",
                "reviewer": "product-face-reviewer",
                "basis": "Visual quality not approved.",
                "reference_quality_bar_checked": False,
                "ai_generic_symptoms": ["missing independent visual review"],
            },
            "blocking_findings": True,
            "evidence_refs": ["reports/product-face.md"],
            "next_action": "rerun proof",
        }

        errors = factoryctl.validate_product_face_result(result)

        self.assertNotIn(
            "product_face_result.reference_quality_comparison.compared_source_ids requires at least 3 references",
            errors,
        )
        self.assertNotIn(
            "product_face_result.reference_quality_comparison.reviewer_independent_from_implementation must be true",
            errors,
        )

    def test_cli_tui_surface_cannot_pass_with_screenshot_only_product_face(self) -> None:
        card = product_surface_card_fixture("cli", "cli_tui")
        result = product_face_result_fixture(
            surface_evidence_profile=surface_profile("cli_tui", "cli"),
            surface_evidence_profiles=[surface_profile("cli_tui", "cli")],
        )

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn("product_face_result.cli_tui_evidence is required for cli_tui PASS", errors)

    def test_cli_tui_surface_passes_with_command_profile_evidence(self) -> None:
        card = product_surface_card_fixture("cli", "cli_tui")
        result = product_face_result_fixture(
            surface_evidence_profile=surface_profile("cli_tui", "cli"),
            surface_evidence_profiles=[surface_profile("cli_tui", "cli")],
            cli_tui_evidence={
                "golden_path_transcript_refs": ["reports/cli/golden-path.txt"],
                "help_output_refs": ["reports/cli/help.txt"],
                "error_state_refs": ["reports/cli/error-state.txt"],
                "install_run_refs": ["reports/cli/install-run.txt"],
                "cross_platform_terminal_refs": ["reports/cli/windows.txt", "reports/cli/linux.txt"],
            },
        )

        self.assertEqual(factoryctl.validate_product_face_result_against_card(result, card), [])

    def test_docs_onboarding_surface_cannot_pass_with_prose_only_product_face(self) -> None:
        card = product_surface_card_fixture("docs", "docs_onboarding")
        result = product_face_result_fixture(
            surface_evidence_profile=surface_profile("docs_onboarding", "docs"),
            surface_evidence_profiles=[surface_profile("docs_onboarding", "docs")],
        )

        errors = factoryctl.validate_product_face_result_against_card(result, card)

        self.assertIn(
            "product_face_result.docs_onboarding_evidence is required for docs_onboarding PASS",
            errors,
        )

    def test_agentic_surface_requires_task_state_control_and_recovery_evidence(self) -> None:
        card = product_surface_card_fixture("agentic_interface", "agentic_interface")
        result = product_face_result_fixture(
            surface_evidence_profile=surface_profile("agentic_interface", "agentic_interface"),
            surface_evidence_profiles=[surface_profile("agentic_interface", "agentic_interface")],
            agentic_interface_evidence={
                "task_transcript_refs": ["reports/agentic/task-transcript.json"],
                "state_transition_refs": ["reports/agentic/state-transitions.json"],
                "approval_boundary_refs": ["reports/agentic/approval-boundaries.json"],
                "user_control_refs": ["reports/agentic/user-control.json"],
                "recovery_error_refs": ["reports/agentic/recovery-error.json"],
            },
        )

        self.assertEqual(factoryctl.validate_product_face_result_against_card(result, card), [])

    def test_auditor_preflight_cannot_claim_pass(self) -> None:
        bad = {
            "audit_mode": "preflight",
            "preflight_only": True,
            "result": "PASS",
            "findings_summary": "Auditor preflight only; no code audit claimed.",
            "evidence_refs": ["reports/auditor-preflight.md"],
        }

        self.assertIn(
            "auditor_result preflight must not use PASS; use WAIVED or PENDING with explicit boundary",
            factoryctl.validate_auditor_result(bad),
        )

    def test_auditor_code_audit_requires_deep_coverage_fields(self) -> None:
        incomplete = {
            "audit_mode": "code_audit",
            "result": "PASS",
            "findings_summary": "Real code audit claimed.",
            "evidence_refs": ["reports/auditor.md"],
        }

        errors = factoryctl.validate_auditor_result(incomplete)

        self.assertTrue(any(error.startswith("auditor_result code_audit missing") for error in errors))

    def test_auditor_code_audit_requires_sufficient_corpus_and_coverage(self) -> None:
        shallow = {
            "audit_mode": "code_audit",
            "result": "PASS",
            "findings_summary": "Real code audit claimed.",
            "evidence_refs": ["reports/auditor.md"],
            "auditor_head": "abc123",
            "corpus_files_loaded": ["README.md"],
            "checklist_coverage": {"01-program-account-validation": {"status": "done"}},
            "known_vectors_coverage": {"total": 2},
            "instruction_matrix": [{"instruction": "deposit"}],
            "state_model": {"accounts": ["vault"]},
            "quasar_toolchain_proof": valid_quasar_toolchain_proof(),
            "findings": [],
            "waivers": [],
        }

        errors = factoryctl.validate_auditor_result(shallow)

        self.assertIn("auditor_result code_audit corpus_files_loaded must include at least 120 files", errors)
        self.assertIn("auditor_result code_audit missing program checklist coverage 02, 03, 04, 05, 06, 07", errors)
        self.assertIn("auditor_result code_audit known_vectors_coverage must cover at least 100 vectors", errors)

    def test_auditor_code_audit_allows_empty_findings_when_coverage_is_complete(self) -> None:
        complete = {
            "audit_mode": "code_audit",
            "result": "PASS",
            "findings_summary": "Real code audit claimed with no blocking finding.",
            "evidence_refs": ["reports/auditor.md"],
            "auditor_head": "abc123",
            "corpus_files_loaded": [f"auditor/file-{index}.md" for index in range(120)],
            "checklist_coverage": {
                "01-program-account-validation": {"status": "done"},
                "02-program-access-control": {"status": "done"},
                "03-program-arithmetic-safety": {"status": "done"},
                "04-program-cpi-pda": {"status": "done"},
                "05-program-state-machine": {"status": "done"},
                "06-program-economic-logic": {"status": "done"},
                "07-program-opsec-governance": {"status": "done"},
            },
            "known_vectors_coverage": {"total": 100},
            "instruction_matrix": [{"instruction": "deposit"}],
            "state_model": {"accounts": ["vault"], "pdas": ["vault"]},
            "quasar_toolchain_proof": valid_quasar_toolchain_proof(),
            "findings": [],
            "waivers": [],
        }

        self.assertEqual(factoryctl.validate_auditor_result(complete), [])

    def test_auditor_code_audit_rejects_unpinned_quasar_crates_io_proof(self) -> None:
        proof = valid_quasar_toolchain_proof(
            install_source="crates.io:quasar-cli",
            source_head="",
            evidence_refs=[".tmp/factory-runs/quasar-real-proof/quasar-crates-proof-result.json"],
        )

        errors = factoryctl.validate_quasar_toolchain_proof(proof)

        self.assertIn(
            "auditor_result quasar_toolchain_proof cannot rely on crates.io quasar-cli without a source_head pin",
            errors,
        )

    def test_auditor_code_audit_rejects_moving_quasar_toolchain_inputs(self) -> None:
        proof = valid_quasar_toolchain_proof(
            source_head="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
            source_head_matches=False,
            container_image="rust:latest",
            solana_install_url="https://release.anza.xyz/stable/install",
        )

        errors = factoryctl.validate_quasar_toolchain_proof(proof)

        self.assertIn("auditor_result quasar_toolchain_proof source_head must match source_head_expected", errors)
        self.assertIn("auditor_result quasar_toolchain_proof source_head_matches must be true", errors)
        self.assertIn("auditor_result quasar_toolchain_proof container_image must not use latest", errors)
        self.assertIn("auditor_result quasar_toolchain_proof container_image must be digest-pinned", errors)
        self.assertIn("auditor_result quasar_toolchain_proof solana_install_url must not use stable", errors)
        self.assertIn("auditor_result quasar_toolchain_proof solana_install_url must use an explicit release", errors)

    def test_real_auditor_worker_result_uses_deep_validation(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        result = factoryctl.build_worker_result(
            "solana-quasar-auditor",
            card,
            result="PASS",
            tool_or_profile="solanabr/Auditor",
            executed_by="solana-quasar-auditor",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Real code audit claimed.",
            next_action="continue",
            evidence_kind="real",
        )

        errors = factoryctl.validate_worker_result_record(result, expected_field="auditor_result", expected_worker_id="solana-quasar-auditor", card=card, evidence_root=ROOT)

        self.assertTrue(any(error.startswith("auditor_result code_audit missing") for error in errors))

    def test_r3_without_scan_and_human_packet_is_invalid(self) -> None:
        card = load_card("v35_invalid_security_no_scan.md")
        errors = factoryctl.validate_card(card)

        self.assertIn("security_scan_packet required for R3/R4 work", errors)
        self.assertIn("human_gate_packet required for R3/R4 work", errors)

    def test_self_review_is_invalid(self) -> None:
        card = load_card("v35_invalid_self_review.md")
        self.assertIn("executor_identity and reviewer_identity must differ", factoryctl.validate_card(card))

    def test_pass_worker_result_requires_evidence(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")

        with self.assertRaisesRegex(ValueError, "require at least one evidence ref"):
            factoryctl.build_worker_result(
                "codex-security",
                card,
                result="PASS",
                tool_or_profile="codex-security:security-scan",
                executed_by="security-runner",
                evidence_refs=[],
                blocking_findings=False,
                findings_summary="",
                next_action="",
            )

    def test_pass_worker_result_cannot_have_blocking_findings(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")

        with self.assertRaisesRegex(ValueError, "PASS cannot have blocking_findings=true"):
            factoryctl.build_worker_result(
                "codex-security",
                card,
                result="PASS",
                tool_or_profile="codex-security:security-scan",
                executed_by="security-runner",
                evidence_refs=["reports/security.md"],
                blocking_findings=True,
                findings_summary="blocking issue",
                next_action="fix",
            )

    def test_blocked_worker_result_carries_recovery_recommendation_without_promotion_authority(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")

        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="BLOCKED",
            tool_or_profile="codex-security:security-scan",
            executed_by="security-runner",
            evidence_refs=["reports/security.md"],
            blocking_findings=True,
            findings_summary="Security finding blocks continuation.",
            next_action="repair finding and rerun security scan",
        )

        recovery = result["recovery_recommendation"]
        self.assertEqual(recovery["blocker_type"], "security")
        self.assertTrue(recovery["factory_owned_repair_allowed"])
        self.assertEqual(recovery["hermes_runtime_boundary"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(recovery["hermes_runtime_boundary"]["local_state_authority"])
        self.assertEqual(recovery["retry_policy"]["attempt_number"], 1)
        self.assertEqual(recovery["retry_policy"]["attempt_number_role"], "planner_seed_not_runtime_counter")
        self.assertEqual(recovery["retry_policy"]["runtime_attempt_source"], "hermes_task_history")
        self.assertEqual(recovery["retry_policy"]["runtime_attempt_marker"], "factory_recovery_attempt")
        self.assertEqual(recovery["retry_policy"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(recovery["retry_policy"]["local_state_authority"])
        errors = factoryctl.validate_worker_result_record(
            result,
            expected_field="security_scan_result",
            expected_worker_id="codex-security",
            card=card,
            evidence_root=ROOT,
        )
        self.assertIn("result must be PASS or WAIVED to satisfy a required worker", errors)
        self.assertNotIn("BLOCKED worker result requires recovery_recommendation", errors)

    def test_blocked_worker_result_rejects_local_retry_authority(self) -> None:
        card = load_card("v35_valid_security_with_scan.md")
        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="BLOCKED",
            tool_or_profile="codex-security:security-scan",
            executed_by="security-runner",
            evidence_refs=["reports/security.md"],
            blocking_findings=True,
            findings_summary="Security finding blocks continuation.",
            next_action="repair finding and rerun security scan",
        )
        bad = json.loads(json.dumps(result))
        bad["recovery_recommendation"]["retry_policy"].pop("runtime_attempt_source")
        bad["recovery_recommendation"]["retry_policy"]["local_state_authority"] = True

        errors = factoryctl.validate_worker_result_record(
            bad,
            expected_field="security_scan_result",
            expected_worker_id="codex-security",
            card=card,
            evidence_root=ROOT,
        )

        self.assertIn("recovery_recommendation.retry_policy.runtime_attempt_source must be hermes_task_history", errors)
        self.assertIn("recovery_recommendation.retry_policy must not claim local runtime state authority", errors)

    def test_human_gate_recovery_cannot_be_factory_owned_repair(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        recovery = factoryctl.recovery_recommendation_for_worker(
            worker_id="human-gate-clerk",
            card=card,
            reason="Human approval is required before continuation.",
        )
        result = worker_result("blocked_worker_result", result="BLOCKED", source_card=card)
        result.update(
            {
                "$schema": factoryctl.worker_result_schema_url("human-gate-clerk"),
                "worker": {"id": "human-gate-clerk", "name": "Human Gate Clerk", "factory_phase": "F15"},
                "tool_or_profile": "human-gate-routing-check",
                "executed_by": "human-gate-clerk",
                "blocking_findings": True,
                "findings_summary": "Human approval is required before continuation.",
                "next_action": "wait for explicit human gate record",
                "recovery_recommendation": recovery,
            }
        )

        self.assertEqual(recovery["blocker_type"], "human_gate")
        self.assertTrue(recovery["human_gate_required"])
        self.assertFalse(recovery["factory_owned_repair_allowed"])
        self.assertFalse(recovery["fresh_review_required"])
        self.assertEqual(recovery["unblock_authority_ref"], "human_gate_record")

        bad = json.loads(json.dumps(result))
        bad["recovery_recommendation"]["factory_owned_repair_allowed"] = True
        bad["recovery_recommendation"]["fresh_review_required"] = True
        bad["recovery_recommendation"]["unblock_authority_ref"] = "Hermes blocked event plus fresh review PASS"

        errors = factoryctl.validate_worker_result_record(
            bad,
            expected_worker_id="human-gate-clerk",
            card=card,
            evidence_root=ROOT,
        )

        self.assertIn("human_gate recovery must not allow factory-owned repair", errors)
        self.assertIn("human_gate recovery must not route through fresh review", errors)
        self.assertIn("human_gate recovery unblock_authority_ref must be human_gate_record", errors)

    def test_worker_result_public_card_ref_redacts_raw_kanban_task_markers(self) -> None:
        card = dict(load_card("v35_valid_security_with_scan.md"))
        raw_task = "t_" + "ready0001"
        card["card_id"] = raw_task
        card["slice_id"] = f"slice-{raw_task}"

        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="PASS",
            tool_or_profile="codex-security:scoped-security-scan",
            executed_by="codex-security-runner",
            evidence_refs=["reports/security.md"],
            blocking_findings=False,
            findings_summary="No blocking finding.",
            next_action="continue",
        )
        serialized = json.dumps(result)

        self.assertEqual(result["card_ref"]["card_id"], "kanban:<redacted>")
        self.assertEqual(result["card_ref"]["slice_id"], "slice-kanban:<redacted>")
        self.assertNotIn(raw_task, serialized)

    def test_artifact_ref_with_raw_kanban_task_marker_is_private(self) -> None:
        raw_task = "t_" + "ready0001"

        classification = factoryctl.classify_artifact_ref(f"reports/{raw_task}.json")
        sanitized, redaction = factoryctl.sanitize_public_ref(f"reports/{raw_task}.json")

        self.assertFalse(classification["public_safe"])
        self.assertEqual(classification["artifact_class"], "private_run_evidence")
        self.assertEqual(sanitized, "redacted:private-runtime-ref")
        self.assertIsNotNone(redaction)

    def test_real_specialist_result_requires_domain_contract_fields(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        result = worker_result("appsec_owasp_result")
        result["evidence_kind"] = "real"
        result["reusable_for_product"] = True

        errors = factoryctl.validate_worker_result_record(
            result,
            expected_field="appsec_owasp_result",
            expected_worker_id="appsec-owasp-specialist",
            card=card,
            evidence_root=ROOT,
        )

        self.assertIn("covered_controls is required for real appsec_owasp_result", errors)
        self.assertIn("control_coverage is required for real appsec_owasp_result", errors)

    def test_codex_security_result_matches_hermes_completion_gate_fields(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="PASS",
            tool_or_profile="codex-security:scoped-security-scan",
            executed_by="codex-security-runner",
            evidence_refs=[".tmp/security-scan-report.md"],
            blocking_findings=False,
            findings_summary="No blocking dry-pilot finding.",
            next_action="Run full scan before production.",
        )

        self.assertEqual(result["scanner_agent"], "security-runner")
        self.assertEqual(result["tool"], "codex-security:scoped-security-scan")
        self.assertIn("PDA", " ".join(result["scope"]))

    def test_duplicate_worker_result_records_choose_latest_active_result(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md")
        result = factoryctl.build_worker_result(
            "codex-security",
            card,
            result="PASS",
            tool_or_profile="codex-security:security-scan",
            executed_by="codex-security-runner",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="No blocking finding.",
            next_action="continue",
        )

        with tempfile.TemporaryDirectory() as tmp:
            results_dir = Path(tmp)
            (results_dir / "a-security.json").write_text(json.dumps(result), encoding="utf-8")
            (results_dir / "z-security.json").write_text(json.dumps(result), encoding="utf-8")

            records = factoryctl.collect_worker_result_fields(card, results_dir)

        self.assertTrue(records["security_scan_result"]["valid"])
        self.assertEqual(records["security_scan_result"]["result"], "PASS")

    def test_worker_closure_rejects_inactive_inline_worker_result(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        inactive_result = worker_result("security_scan_result", source_card=card)
        inactive_result["active"] = False

        closure = factoryctl.build_worker_closure(
            card,
            {"security_scan_result": inactive_result},
            None,
        )

        security_row = closure["workers"]["codex-security"]
        self.assertFalse(security_row["active"])
        self.assertTrue(security_row["valid"])
        self.assertTrue(security_row["consumable"])
        self.assertFalse(security_row["satisfied"])
        self.assertIn("codex-security", closure["unconsumable_blocking_workers"])

    def test_inline_worker_result_requires_existing_evidence_ref_for_done(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        receipt = {
            "receipt_five": {
                "changed": "validated onchain gate",
                "artifact_paths": ["examples/minimal-hermes-project/card.md"],
                "verification_commands": ["python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md"],
                "verification_result": "PASS",
                "reviewer_required": False,
                "next_action": "continue",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "factory-orchestrator",
                "worker": "factory-orchestrator",
                "receipt_refs": ["receipt_five", "security_scan_result"],
                "artifact_refs": ["examples/minimal-hermes-project/card.md"],
            },
            "security_scan_result": worker_result("security_scan_result"),
            "auditor_result": worker_result("auditor_result", result="WAIVED"),
            "independent_review_result": worker_result("independent_review_result"),
            "human_gate_record": human_gate_record(),
            "qa_verification_result": worker_result("qa_verification_result"),
            "autoreview_result": worker_result("autoreview_result"),
            "security_orchestration_result": worker_result("security_orchestration_result"),
            "remote_proof_result": worker_result("remote_proof_result"),
            "handoff_packet_result": worker_result("handoff_packet_result"),
            "supply_chain_result": worker_result("supply_chain_result"),
        }

        plan = factoryctl.build_transition_plan(
            card,
            ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md",
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertTrue(any("codex-security result is invalid before done" in reason for reason in plan["blocked_reasons"]))

    def test_receipt_security_result_requires_hermes_completion_gate_fields(self) -> None:
        bad_receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": False,
                "next_action": "none",
            },
            "kanban_transition_event": {},
            "security_scan_result": {
                "record_type": "security_scan_result",
                "result": "PASS",
                "evidence_refs": ["security.md"],
            },
        }

        errors = factoryctl.validate_receipt(bad_receipt)
        self.assertIn("security_scan_result missing scanner_agent, tool, findings_summary", errors)
        self.assertIn("security_scan_result scope must be a non-empty string array", errors)

    def test_minimal_example_receipt_matches_hermes_completion_gates(self) -> None:
        receipt = factoryctl.load_json_like(ROOT / "examples" / "minimal-hermes-project" / "expected-receipt-five.json")
        self.assertEqual(factoryctl.validate_receipt(receipt), [])
        self.assertTrue(receipt["public_safe"])
        self.assertIn("cto_gate", receipt["approvals"])

    def test_worker_result_builder_uses_specialized_bound_schema(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")

        auditor_result = factoryctl.build_worker_result(
            "solana-quasar-auditor",
            card,
            result="WAIVED",
            tool_or_profile="solanabr/Auditor-preflight",
            executed_by="solana-quasar-auditor",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Preflight only; no code audit is claimed.",
            next_action="run real Auditor code audit before promotion",
            evidence_kind="synthetic",
            reusable_for_product=False,
        )
        product_face_result = factoryctl.build_worker_result(
            "product-face",
            card,
            result="PASS",
            tool_or_profile="product-face-proof",
            executed_by="product-face",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Synthetic Product Face smoke.",
            next_action="run browser proof for real product",
            evidence_kind="synthetic",
            reusable_for_product=False,
        )

        self.assertEqual(auditor_result["$schema"], "https://overkill-factory.dev/schemas/auditor-result.schema.json")
        self.assertEqual(auditor_result["audit_mode"], "preflight")
        self.assertEqual(product_face_result["$schema"], "https://overkill-factory.dev/schemas/product-face-result.schema.json")
        self.assertIn("user_journeys_checked", product_face_result)
        self.assertIn("a11y", product_face_result)
        self.assertIn("overlap_check", product_face_result)
        self.assertEqual(product_face_result["product_acceptance_boundary"]["boundary"], "synthetic_smoke_only")
        self.assertTrue(product_face_result["product_acceptance_boundary"]["cannot_satisfy_product_acceptance"])

    def test_product_face_worker_result_validation_rejects_synthetic_completion(self) -> None:
        card = load_card("v35_valid_product_face.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        result = factoryctl.build_worker_result(
            "product-face",
            card,
            result="PASS",
            tool_or_profile="product-face-proof",
            executed_by="product-face",
            evidence_refs=["README.md"],
            blocking_findings=False,
            findings_summary="Synthetic Product Face smoke.",
            next_action="run browser proof for real product",
            evidence_kind="synthetic",
            reusable_for_product=False,
        )

        errors = factoryctl.validate_worker_result_record(
            result,
            expected_field="product_face_result",
            expected_worker_id="product-face",
            card=card,
            evidence_root=ROOT,
        )

        self.assertIn("product_face_result synthetic evidence cannot satisfy product-facing completion", errors)

    def test_product_face_worker_result_binds_external_visual_manifest(self) -> None:
        card = load_card("v35_valid_product_face.md")

        result = factoryctl.build_worker_result(
            "product-face",
            card,
            result="PASS",
            tool_or_profile="product-face-proof",
            executed_by="product-face",
            evidence_refs=["external:product-face-fixture-desktop.png"],
            blocking_findings=False,
            findings_summary="External visual proof package.",
            next_action="ready for independent review",
            evidence_kind="real",
            reusable_for_product=True,
        )

        manifests = result["external_visual_artifact_manifests"]
        self.assertEqual(len(manifests), 1)
        manifest = manifests[0]
        self.assertEqual(manifest["manifest_ref"], "external:product-face-worker-result-package")
        self.assertEqual(manifest["bounded_acceptance"], True)
        self.assertEqual(manifest["sanitized"], True)
        self.assertNotEqual(manifest["expires_at"], "2099-01-01T00:00:00+00:00")
        self.assertEqual(factoryctl.validate_product_face_result(result), [])

    def test_human_approval_requires_evidence(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")

        with self.assertRaisesRegex(ValueError, "approved human gates require"):
            factoryctl.build_human_gate_record(
                card,
                gate_type="R3",
                decision="approved",
                human_actor="product-owner",
                approved_scope=[],
                forbidden_scope=[],
                required_changes=[],
                risk_owner=None,
                security_owner=None,
                rollback_owner=None,
                evidence_refs=[],
                notes="",
            )

    def test_transition_plan_ready_creates_queued_worker_tasks(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
        )
        queues = {task["worker_id"]: task["queue_class"] for task in plan["worker_tasks"]}

        self.assertEqual(plan["transition_action"], "block_and_create_before_ready_tasks")
        self.assertIn("factory-orchestrator result is required before ready", plan["blocked_reasons"])
        self.assertIn("supply-chain-gate result is required before ready", plan["blocked_reasons"])
        self.assertEqual(plan["gate_report"]["gate_status"], "ready_for_worker_execution")
        self.assertEqual(queues["factory-orchestrator"], "blocking-before-ready")
        self.assertEqual(queues["supply-chain-gate"], "blocking-before-ready")
        self.assertEqual(queues["codex-security"], "blocking-before-done")
        self.assertEqual(queues["solana-quasar-auditor"], "blocking-before-done")

    def test_recovery_plan_does_not_turn_normal_execution_into_recovery(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")

        plan = factoryctl.build_factory_recovery_plan(card)

        self.assertEqual(plan["gate_predicate_result"], "PASS")
        self.assertEqual(plan["recovery_routes"], [])
        self.assertEqual(plan["hermes_runtime_boundary"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(plan["hermes_runtime_boundary"]["local_state_authority"])

    def test_recovery_plan_for_blocked_gate_uses_hermes_native_boundary(self) -> None:
        card = load_card("v35_valid_product_face.md")
        card.pop("security_scan_packet", None)

        plan = factoryctl.build_factory_recovery_plan(card)

        self.assertEqual(plan["gate_predicate_result"], "BLOCK")
        self.assertGreater(len(plan["recovery_routes"]), 0)
        route = plan["recovery_routes"][0]
        self.assertIn("repair_task_ref", route)
        self.assertIn("downstream_freeze_scope", route)
        self.assertIn("unblock_authority_ref", route)
        self.assertEqual(route["retry_policy"]["attempt_number_role"], "planner_seed_not_runtime_counter")
        self.assertEqual(route["retry_policy"]["runtime_attempt_source"], "hermes_task_history")
        self.assertFalse(route["retry_policy"]["local_state_authority"])
        self.assertEqual(route["hermes_materialization"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(route["hermes_materialization"]["local_state_authority"])
        self.assertTrue(plan["hermes_runtime_boundary"]["no_shadow_scheduler"])
        self.assertTrue(plan["hermes_runtime_boundary"]["no_shadow_dispatcher"])
        self.assertTrue(plan["hermes_runtime_boundary"]["no_shadow_dependency_engine"])

    def test_recovery_plan_routes_blocked_review_back_to_handoff_producer(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)

        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            results_dir = Path(tmpdir)
            handoff_path = results_dir / "handoff.json"
            review_path = results_dir / "review.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]
            blocked_review = factoryctl.build_worker_result(
                "independent-reviewer",
                card,
                result="BLOCKED",
                tool_or_profile="independent-review-smoke",
                executed_by="independent-reviewer",
                evidence_refs=["README.md"],
                blocking_findings=True,
                findings_summary="Review found the handoff packet incomplete.",
                next_action="repair handoff packet and rerun independent review",
                evidence_kind="synthetic",
                reusable_for_product=False,
            )
            blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]
            review_path.write_text(json.dumps(blocked_review), encoding="utf-8")

            plan = factoryctl.build_factory_recovery_plan(card, worker_results_dir=results_dir)

        self.assertEqual(plan["gate_predicate_result"], "BLOCK")
        route = plan["recovery_routes"][0]
        self.assertEqual(route["repair_owner_worker"], "handoff-packer")
        self.assertEqual(route["blocker_type"], "dependency")
        self.assertTrue(route["fresh_review_required"])
        self.assertEqual(route["retry_policy"]["attempt_number_role"], "planner_seed_not_runtime_counter")
        self.assertEqual(route["retry_policy"]["runtime_attempt_marker"], "factory_recovery_attempt")
        self.assertIn("handoff_packet_result", route["expected_repair_outputs"])
        self.assertIn("independent_review_result", route["expected_repair_outputs"])
        self.assertIn(requirement["requirement_id"], route["dependency_edge_patch"]["old_edges"])
        self.assertEqual(route["hermes_materialization"]["runtime_authority"], "hermes_kanban")
        self.assertFalse(route["hermes_materialization"]["local_state_authority"])

    def test_recovery_plan_reads_blocked_review_from_receipt_metadata(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)
        requirement = factoryctl.declared_graph_requirements(
            "handoff_packet_result",
            handoff,
            evidence_ref="receipt:handoff_packet_result",
        )[0]
        blocked_review = factoryctl.build_worker_result(
            "independent-reviewer",
            card,
            result="BLOCKED",
            tool_or_profile="independent-review-smoke",
            executed_by="independent-reviewer",
            evidence_refs=["README.md"],
            blocking_findings=True,
            findings_summary="Review found the inline handoff packet incomplete.",
            next_action="repair handoff packet and rerun independent review",
            evidence_kind="synthetic",
            reusable_for_product=False,
        )
        blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]

        plan = factoryctl.build_factory_recovery_plan(
            card,
            receipt={
                "handoff_packet_result": handoff,
                "independent_review_result": blocked_review,
            },
        )

        route = plan["recovery_routes"][0]
        self.assertEqual(plan["gate_predicate_result"], "BLOCK")
        self.assertEqual(route["repair_owner_worker"], "handoff-packer")
        self.assertIn("receipt:handoff_packet_result", route["invalidates_refs"])

    def test_transition_plan_attaches_recovery_route_to_repair_worker_task(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)

        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            results_dir = Path(tmpdir)
            handoff_path = results_dir / "handoff.json"
            review_path = results_dir / "review.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]
            blocked_review = factoryctl.build_worker_result(
                "independent-reviewer",
                card,
                result="BLOCKED",
                tool_or_profile="independent-review-smoke",
                executed_by="independent-reviewer",
                evidence_refs=["README.md"],
                blocking_findings=True,
                findings_summary="Review found the handoff packet incomplete.",
                next_action="repair handoff packet and rerun independent review",
                evidence_kind="synthetic",
                reusable_for_product=False,
            )
            blocked_review["graph_requirement_refs"] = [requirement["requirement_id"]]
            review_path.write_text(json.dumps(blocked_review), encoding="utf-8")

            plan = factoryctl.build_transition_plan(
                card,
                card_path,
                from_status="review",
                to_status="done",
                receipt={
                    "receipt_five": {
                        "changed": "fixture",
                        "artifact_paths": ["README.md"],
                        "verification_commands": ["fixture"],
                        "verification_result": "PASS",
                        "reviewer_required": True,
                        "reviewer_result": "BLOCKED",
                        "next_action": "repair",
                    },
                    "kanban_transition_event": {
                        "from_status": "review",
                        "to_status": "done",
                        "actor": "factory-orchestrator",
                        "worker": "factory-orchestrator",
                        "receipt_refs": ["receipt_five"],
                        "artifact_refs": ["README.md"],
                        "allowed": True,
                    },
                },
                worker_results_dir=results_dir,
            )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertTrue(plan["recovery_routes"])
        route_id = plan["recovery_routes"][0]["recovery_route_id"]
        repair_task = next(task for task in plan["worker_tasks"] if task["worker_id"] == "handoff-packer")
        self.assertIn(route_id, repair_task["recovery_route_refs"])
        self.assertIn(route_id, repair_task["packet"]["input_contract"]["recovery_route_refs"])
        self.assertEqual(repair_task["packet"]["input_contract"]["recovery_routes"][0]["repair_owner_worker"], "handoff-packer")
        self.assertTrue(any("requires independent-reviewer PASS" in reason for reason in plan["blocked_reasons"]))

    def test_hermes_schemas_allow_before_ready_block_action(self) -> None:
        action = "block_and_create_before_ready_tasks"
        transition_plan_schema = json.loads((ROOT / "schemas" / "hermes-transition-plan.schema.json").read_text(encoding="utf-8"))
        transition_hook_schema = json.loads((ROOT / "schemas" / "hermes-transition-hook.schema.json").read_text(encoding="utf-8"))
        worker_ledger_schema = json.loads((ROOT / "schemas" / "hermes-worker-ledger.schema.json").read_text(encoding="utf-8"))

        self.assertIn(action, transition_plan_schema["properties"]["transition_action"]["enum"])
        self.assertIn(action, transition_hook_schema["properties"]["transition_action"]["enum"])
        self.assertIn(action, worker_ledger_schema["properties"]["last_action"]["enum"])

    def test_hermes_transition_schema_rejects_factory_owned_human_gate_recovery(self) -> None:
        schema = json.loads((ROOT / "schemas" / "hermes-transition-plan.schema.json").read_text(encoding="utf-8"))
        plan = {
            "plan_type": "hermes_kanban_transition_plan",
            "created_at": "2026-06-15T00:00:00+00:00",
            "source_card_path": "examples/cards/v35_valid_onchain_auditor_scan.md",
            "event": {"from_status": "review", "to_status": "done", "card_id": "KFP-V35-POS-ONCHAIN-AUDITOR"},
            "transition_action": "block_transition",
            "blocked_reasons": ["human gate required"],
            "gate_report": {},
            "worker_tasks": [],
            "recovery_routes": [
                {
                    "recovery_route_id": "recovery:human-gate",
                    "blocker_type": "human_gate",
                    "factory_owned_repair_allowed": True,
                    "human_gate_required": False,
                    "repair_owner_worker": "human-gate-clerk",
                    "repair_task_ref": "hermes:intent:human-gate",
                    "invalidates_refs": [],
                    "supersedes_refs": [],
                    "fresh_review_required": True,
                    "unblock_authority_ref": "Hermes blocked event plus fresh review PASS",
                    "retry_policy": factoryctl.recovery_retry_policy(),
                    "hermes_materialization": {
                        "runtime_authority": "hermes_kanban",
                        "local_state_authority": False,
                    },
                }
            ],
        }

        errors = public_json_validator.validate_node(schema, plan, "$", schemas={"hermes-transition-plan.schema.json": schema}, root_schema=schema)

        joined = "\n".join(errors)
        self.assertIn("factory_owned_repair_allowed", joined)
        self.assertIn("human_gate_required", joined)
        self.assertIn("fresh_review_required", joined)
        self.assertIn("unblock_authority_ref", joined)

    def test_transition_plan_enforce_blocks_before_ready_action(self) -> None:
        args = Namespace(
            card=ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md",
            receipt=None,
            from_status="draft",
            to_status="ready",
            worker_results_dir=None,
            out=None,
            enforce=True,
        )

        self.assertEqual(factoryctl.command_transition_plan(args), 1)

    def test_transition_plan_ready_blocks_missing_worker_inputs(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_product_face.md"
        card = factoryctl.load_json_like(card_path)
        card.pop("security_scan_packet", None)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
        )

        self.assertEqual(plan["transition_action"], "block_and_create_before_ready_tasks")
        self.assertIn("security-orchestrator missing inputs for blocking-before-ready", plan["blocked_reasons"])
        self.assertIn("appsec-owasp-specialist missing inputs for blocking-before-done", plan["blocked_reasons"])
        self.assertIn("factory-orchestrator result is required before ready", plan["blocked_reasons"])

    def test_worker_closure_marks_review_required_handoff_valid_but_not_consumable(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)

        closure = factoryctl.build_worker_closure(card, {"handoff_packet_result": handoff}, None)

        handoff_row = closure["workers"]["handoff-packer"]
        self.assertTrue(handoff_row["valid"])
        self.assertFalse(handoff_row["consumable"])
        self.assertFalse(handoff_row["satisfied"])
        self.assertIn("handoff-packer", closure["unconsumable_blocking_workers"])
        self.assertEqual(closure["unsatisfied_graph_requirements"][0]["requirement_type"], "review_before_consumption")
        self.assertEqual(closure["unsatisfied_graph_requirements"][0]["review_worker_id"], "independent-reviewer")

    def test_worker_closure_ignores_inline_reviewer_pass_on_producer_handoff(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result(
            "handoff_packet_result",
            source_card=card,
            reviewer_required=True,
            reviewer_result="PASS",
        )

        closure = factoryctl.build_worker_closure(card, {"handoff_packet_result": handoff}, None)

        handoff_row = closure["workers"]["handoff-packer"]
        self.assertTrue(handoff_row["valid"])
        self.assertFalse(handoff_row["consumable"])
        self.assertFalse(handoff_row["satisfied"])
        self.assertEqual(closure["graph_requirements"][0]["status"], "pending")
        self.assertEqual(closure["graph_requirements"][0]["reviewer_result"], "PASS")
        self.assertEqual(closure["unsatisfied_graph_requirements"][0]["review_worker_id"], "independent-reviewer")

    def test_transition_plan_blocks_declared_handoff_review_before_downstream_consumption(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="draft",
            to_status="ready",
            receipt={"handoff_packet_result": handoff},
        )

        self.assertEqual(plan["graph_requirements"][0]["status"], "pending")
        self.assertIn(
            "handoff_packet_result requires independent-reviewer PASS before downstream consumption",
            plan["blocked_reasons"],
        )
        review_tasks = [task for task in plan["worker_tasks"] if task["worker_id"] == "independent-reviewer"]
        self.assertTrue(review_tasks)
        self.assertIn(plan["graph_requirements"][0]["requirement_id"], review_tasks[0]["graph_requirement_refs"])

    def test_transition_plan_allows_review_ready_for_valid_review_required_handoff(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)
        receipt = {
            "handoff_packet_result": handoff,
            "orchestration_result": worker_result("orchestration_result", source_card=card),
            "source_ledger_result": worker_result("source_ledger_result", source_card=card),
            "security_orchestration_result": worker_result("security_orchestration_result", source_card=card),
            "supply_chain_result": worker_result("supply_chain_result", source_card=card),
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="doing",
            to_status="implementation-ready-for-review",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "allow_review_ready")
        self.assertEqual(plan["blocked_reasons"], [])
        self.assertEqual(plan["review_ready_handoffs"][0]["handoff_state"], "implementation_ready_for_review")
        self.assertEqual(plan["review_ready_handoffs"][0]["authorized_downstream_scope"], ["review"])
        self.assertEqual(plan["review_task_authorizations"][0]["authorization_state"], "review_task_ready")
        review_tasks = [task for task in plan["worker_tasks"] if task["worker_id"] == "independent-reviewer"]
        self.assertEqual(review_tasks[0]["dependency_authorization_state"], "review_ready")
        self.assertEqual(review_tasks[0]["review_task_authorizations"][0]["authorized_scope"], ["review"])

    def test_transition_plan_keeps_unsafe_review_handoff_blocked(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = factoryctl.build_worker_result(
            "handoff-packer",
            card,
            result="BLOCKED",
            tool_or_profile="handoff-pack-smoke",
            executed_by="handoff-packer",
            evidence_refs=["README.md"],
            blocking_findings=True,
            findings_summary="Handoff is missing required artifacts.",
            next_action="independent review required after repair",
            evidence_kind="synthetic",
            reusable_for_product=False,
            reviewer_required=True,
        )
        receipt = {
            "handoff_packet_result": handoff,
            "orchestration_result": worker_result("orchestration_result", source_card=card),
            "source_ledger_result": worker_result("source_ledger_result", source_card=card),
            "security_orchestration_result": worker_result("security_orchestration_result", source_card=card),
            "supply_chain_result": worker_result("supply_chain_result", source_card=card),
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="doing",
            to_status="implementation-ready-for-review",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertIn(
            "handoff_packet_result cannot authorize review because result is invalid",
            plan["blocked_reasons"],
        )
        self.assertEqual(plan["review_ready_handoffs"], [])
        self.assertEqual(plan["review_task_authorizations"], [])

    def test_worker_closure_satisfies_handoff_review_from_independent_review_result(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)
        requirement_id = factoryctl.declared_graph_requirements(
            "handoff_packet_result",
            handoff,
            evidence_ref="receipt:handoff_packet_result",
        )[0]["requirement_id"]
        review = worker_result("independent_review_result", source_card=card)
        review["graph_requirement_refs"] = [requirement_id]

        closure = factoryctl.build_worker_closure(
            card,
            {
                "handoff_packet_result": handoff,
                "independent_review_result": review,
            },
            None,
        )

        handoff_row = closure["workers"]["handoff-packer"]
        self.assertTrue(handoff_row["valid"])
        self.assertTrue(handoff_row["consumable"])
        self.assertTrue(handoff_row["satisfied"])
        self.assertEqual(closure["unsatisfied_graph_requirements"], [])
        self.assertEqual(closure["graph_requirements"][0]["status"], "satisfied")

    def test_transition_plan_downstream_authorization_requires_explicit_review_worker_ids(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)
        requirement_id = factoryctl.declared_graph_requirements(
            "handoff_packet_result",
            handoff,
            evidence_ref="receipt:handoff_packet_result",
        )[0]["requirement_id"]
        review = worker_result("independent_review_result", source_card=card)
        review["graph_requirement_refs"] = [requirement_id]
        receipt = {
            "handoff_packet_result": handoff,
            "independent_review_result": review,
            "orchestration_result": worker_result("orchestration_result", source_card=card),
            "source_ledger_result": worker_result("source_ledger_result", source_card=card),
            "security_orchestration_result": worker_result("security_orchestration_result", source_card=card),
            "supply_chain_result": worker_result("supply_chain_result", source_card=card),
        }

        without_explicit_auth = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="review",
            to_status="ready",
            receipt=receipt,
        )

        self.assertEqual(without_explicit_auth["downstream_task_authorizations"], [])

        review["authorized_downstream_worker_ids"] = [
            "qa-verification-worker",
            "human-gate-clerk",
            "handoff-packer",
            "unknown-worker",
        ]
        with_explicit_auth = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="review",
            to_status="ready",
            receipt=receipt,
        )

        self.assertEqual(len(with_explicit_auth["downstream_task_authorizations"]), 1)
        authorization = with_explicit_auth["downstream_task_authorizations"][0]
        self.assertEqual(authorization["authorization_type"], "fresh_review_downstream_task")
        self.assertEqual(authorization["authorized_worker_ids"], ["qa-verification-worker"])
        self.assertIn("human-gate-clerk", authorization["forbidden_worker_ids"])
        self.assertIn("handoff-packer", authorization["forbidden_worker_ids"])
        self.assertIn("independent-reviewer", authorization["forbidden_worker_ids"])

    def test_recovery_route_review_must_close_route_before_downstream_authorization(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        route_ref = "recovery:val-solana-quasar-r3:review-block:handoff"
        route_digest = "sha256:" + ("1" * 64)
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)
        handoff["recovery_route_refs"] = [route_ref]
        handoff["recovery_route_digests"] = [route_digest]
        requirement_id = factoryctl.declared_graph_requirements(
            "handoff_packet_result",
            handoff,
            evidence_ref="receipt:handoff_packet_result",
        )[0]["requirement_id"]
        review = worker_result("independent_review_result", source_card=card)
        review["graph_requirement_refs"] = [requirement_id]
        review["authorized_downstream_worker_ids"] = ["qa-verification-worker"]
        receipt = {
            "handoff_packet_result": handoff,
            "independent_review_result": review,
            "orchestration_result": worker_result("orchestration_result", source_card=card),
            "source_ledger_result": worker_result("source_ledger_result", source_card=card),
            "security_orchestration_result": worker_result("security_orchestration_result", source_card=card),
            "supply_chain_result": worker_result("supply_chain_result", source_card=card),
        }

        generic_pass = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="review",
            to_status="ready",
            receipt=receipt,
        )

        self.assertEqual(generic_pass["downstream_task_authorizations"], [])
        self.assertEqual(generic_pass["graph_requirements"][0]["status"], "pending")

        review["reviewed_recovery_route_refs"] = [route_ref]
        review["reviewed_recovery_route_digests"] = [route_digest]
        route_closed = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="review",
            to_status="ready",
            receipt=receipt,
        )

        authorization = route_closed["downstream_task_authorizations"][0]
        self.assertEqual(authorization["authorized_worker_ids"], ["qa-verification-worker"])
        self.assertEqual(authorization["recovery_route_refs"], [route_ref])
        self.assertEqual(authorization["recovery_route_digests"], [route_digest])

    def test_worker_closure_does_not_satisfy_handoff_review_with_generic_review_result(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)

        closure = factoryctl.build_worker_closure(
            card,
            {
                "handoff_packet_result": handoff,
                "independent_review_result": worker_result("independent_review_result", source_card=card),
            },
            None,
        )

        handoff_row = closure["workers"]["handoff-packer"]
        self.assertFalse(handoff_row["consumable"])
        self.assertEqual(closure["graph_requirements"][0]["status"], "pending")
        self.assertEqual(closure["unsatisfied_graph_requirements"][0]["producer_field"], "handoff_packet_result")

    def test_worker_closure_uses_matching_review_candidate_not_newest_unrelated_review(self) -> None:
        card = load_card("v35_valid_onchain_auditor_scan.md")
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        handoff = worker_result("handoff_packet_result", source_card=card, reviewer_required=True)

        with tempfile.TemporaryDirectory(dir=ROOT) as tmpdir:
            results_dir = Path(tmpdir)
            handoff_path = results_dir / "handoff.json"
            handoff_path.write_text(json.dumps(handoff), encoding="utf-8")
            requirement_id = factoryctl.declared_graph_requirements(
                "handoff_packet_result",
                handoff,
                evidence_ref=factoryctl.source_card_ref(handoff_path),
            )[0]["requirement_id"]

            matching_review = worker_result("independent_review_result", source_card=card)
            matching_review["created_at"] = "2026-06-06T00:01:00+00:00"
            matching_review["graph_requirement_refs"] = [requirement_id]
            matching_review["authorized_downstream_worker_ids"] = ["qa-verification-worker"]
            (results_dir / "matching-review.json").write_text(json.dumps(matching_review), encoding="utf-8")

            unrelated_review = worker_result("independent_review_result", source_card=card)
            unrelated_review["created_at"] = "2026-06-06T00:02:00+00:00"
            unrelated_review["findings_summary"] = "Fresh, but for a different dependency."
            (results_dir / "z-unrelated-review.json").write_text(json.dumps(unrelated_review), encoding="utf-8")

            closure = factoryctl.build_worker_closure(card, {}, results_dir)

        requirement = closure["graph_requirements"][0]
        self.assertEqual(requirement["status"], "satisfied")
        self.assertTrue(requirement["review_evidence_ref"].endswith("/matching-review.json"))
        self.assertEqual(requirement["authorized_downstream_worker_ids"], ["qa-verification-worker"])
        self.assertEqual(closure["unsatisfied_graph_requirements"], [])
        self.assertTrue(closure["workers"]["handoff-packer"]["satisfied"])

    def test_transition_plan_done_blocks_missing_required_worker_results(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "none",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "implementation-worker",
                "worker": "implementation-worker",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["artifact"],
                "allowed": True,
            },
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertIn("codex-security result is required before done", plan["blocked_reasons"])
        self.assertIn("solana-quasar-auditor result is required before done", plan["blocked_reasons"])

    def test_transition_plan_done_allows_when_blocking_worker_results_exist(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        card["source_refs"] = [*card.get("source_refs", []), "synthetic validation fixture"]
        receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "none",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "implementation-worker",
                "worker": "implementation-worker",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["artifact"],
                "allowed": True,
            },
            "security_scan_result": worker_result("security_scan_result", source_card=card),
            "auditor_result": worker_result("auditor_result", result="WAIVED", source_card=card),
            "independent_review_result": worker_result("independent_review_result", source_card=card),
            "human_gate_record": human_gate_record(source_card=card),
            "qa_verification_result": worker_result("qa_verification_result", source_card=card),
            "autoreview_result": worker_result("autoreview_result", source_card=card),
            "security_orchestration_result": worker_result("security_orchestration_result", source_card=card),
            "crypto_key_management_result": worker_result("crypto_key_management_result", source_card=card),
            "remote_proof_result": worker_result("remote_proof_result", source_card=card),
            "handoff_packet_result": worker_result("handoff_packet_result", source_card=card),
            "solana_quasar_build_result": worker_result("solana_quasar_build_result", source_card=card),
            "solana_quasar_qa_result": worker_result("solana_quasar_qa_result", source_card=card),
            "receipt_five_reconciliation_result": worker_result("receipt_five_reconciliation_result", source_card=card),
            "orchestration_result": worker_result("orchestration_result", source_card=card),
            "source_ledger_result": worker_result("source_ledger_result", source_card=card),
            "supply_chain_result": worker_result("supply_chain_result", source_card=card),
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "allow_done")
        self.assertEqual(plan["blocked_reasons"], [])

    def test_transition_plan_done_blocks_weak_worker_result_shape(self) -> None:
        card_path = ROOT / "examples" / "cards" / "v35_valid_onchain_auditor_scan.md"
        card = factoryctl.load_json_like(card_path)
        receipt = {
            "receipt_five": {
                "changed": "x",
                "artifact_paths": ["artifact"],
                "verification_commands": ["verify"],
                "verification_result": "PASS",
                "reviewer_required": True,
                "reviewer_result": "PASS",
                "next_action": "none",
            },
            "kanban_transition_event": {
                "from_status": "ready",
                "to_status": "done",
                "actor": "implementation-worker",
                "worker": "implementation-worker",
                "receipt_refs": ["receipt_five"],
                "artifact_refs": ["artifact"],
            },
            "security_scan_result": {"record_type": "security_scan_result", "result": "PASS"},
            "auditor_result": worker_result("auditor_result", result="WAIVED"),
            "independent_review_result": worker_result("independent_review_result"),
            "human_gate_record": human_gate_record(),
            "qa_verification_result": worker_result("qa_verification_result"),
            "autoreview_result": worker_result("autoreview_result"),
            "security_orchestration_result": worker_result("security_orchestration_result"),
            "crypto_key_management_result": worker_result("crypto_key_management_result"),
            "remote_proof_result": worker_result("remote_proof_result"),
            "handoff_packet_result": worker_result("handoff_packet_result"),
            "receipt_five_reconciliation_result": worker_result("receipt_five_reconciliation_result"),
        }

        plan = factoryctl.build_transition_plan(
            card,
            card_path,
            from_status="ready",
            to_status="done",
            receipt=receipt,
        )

        self.assertEqual(plan["transition_action"], "block_transition")
        self.assertIn("codex-security result is invalid before done", plan["blocked_reasons"])
