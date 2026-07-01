from __future__ import annotations

import importlib.util
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = ROOT / "scripts"
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def load_script(name: str) -> Any:
    path = SCRIPT_DIR / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


factoryctl = load_script("factoryctl")
runtime_contracts = load_script("validate_v2_runtime_contracts")
agent_skill_boundaries = load_script("validate_agent_vs_skill_boundaries")
reference_superiority = load_script("validate_reference_superiority")


def copy_contract_root(tmp: Path) -> None:
    for dirname in ("agents", "schemas", "templates", "fixtures"):
        shutil.copytree(ROOT / dirname, tmp / dirname)


class V2RuntimeContractsTests(unittest.TestCase):
    def test_factoryctl_validates_runtime_contract_set(self) -> None:
        self.assertEqual(factoryctl.main_with_args_for_test(["validate-v2-runtime-contracts"]), 0)

    def test_factoryctl_validates_agent_skill_boundaries(self) -> None:
        self.assertEqual(factoryctl.main_with_args_for_test(["validate-agent-skill-boundaries"]), 0)

    def test_factoryctl_validates_reference_superiority_fixtures(self) -> None:
        self.assertEqual(factoryctl.main_with_args_for_test(["validate-reference-superiority"]), 0)

    def test_operator_delivery_rejects_decision_before_material(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            copy_contract_root(tmp)
            receipt_path = tmp / "templates" / "operator-delivery-receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["material_delivered_before_question"] = False
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

            errors = runtime_contracts.validate_runtime_contract_set(tmp)

        self.assertTrue(any("material_delivered_before_question" in error for error in errors), errors)

    def test_runtime_contract_rejects_untyped_hermes_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            copy_contract_root(tmp)
            receipt_path = tmp / "templates" / "hermes-blocked-first-protocol-receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["typed_block_policy"]["untyped_block_forbidden"] = False
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

            errors = runtime_contracts.validate_runtime_contract_set(tmp)

        self.assertTrue(any("untyped_block_forbidden" in error for error in errors), errors)

    def test_runtime_contract_rejects_missing_dependency_typed_block_kind(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            copy_contract_root(tmp)
            receipt_path = tmp / "templates" / "hermes-blocked-first-protocol-receipt.json"
            receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
            receipt["typed_block_policy"]["native_block_kinds_required"].remove("dependency")
            receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")

            errors = runtime_contracts.validate_runtime_contract_set(tmp)

        self.assertTrue(any("dependency" in error and "typed block kinds" in error for error in errors), errors)

    def test_agent_binding_rejects_unregistered_skill_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            copy_contract_root(tmp)
            bindings_path = tmp / "agents" / "hermes-profile-bindings.public.json"
            bindings = json.loads(bindings_path.read_text(encoding="utf-8"))
            bindings["bindings"]["factory-orchestrator"]["skill_refs"].append("missing-specialist-provider")
            bindings_path.write_text(json.dumps(bindings, indent=2) + "\n", encoding="utf-8")

            errors = agent_skill_boundaries.validate_boundaries(tmp)

        self.assertTrue(any("missing-specialist-provider" in error for error in errors), errors)

    def test_agent_alias_target_must_exist_in_worker_registry(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            copy_contract_root(tmp)
            aliases_path = tmp / "agents" / "profile-compatibility-aliases.public.json"
            aliases = json.loads(aliases_path.read_text(encoding="utf-8"))
            aliases["aliases"][0]["target_worker_id"] = "missing-worker"
            aliases_path.write_text(json.dumps(aliases, indent=2) + "\n", encoding="utf-8")

            errors = agent_skill_boundaries.validate_boundaries(tmp)

        self.assertTrue(any("missing-worker" in error and "worker registry" in error for error in errors), errors)

    def test_authority_sounding_worker_id_requires_cannot_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp = Path(tmp_dir)
            copy_contract_root(tmp)
            registry_path = tmp / "agents" / "worker-registry.public.json"
            registry = json.loads(registry_path.read_text(encoding="utf-8"))
            registry["workers"][0]["authority_max"] = "routes the factory"
            registry_path.write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")

            errors = agent_skill_boundaries.validate_boundaries(tmp)

        self.assertTrue(any("authority-suggesting worker id" in error for error in errors), errors)

    def test_reference_superiority_fixture_must_block_regression(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fixture_path = Path(tmp_dir) / "reference-derived-negative-fixtures.json"
            shutil.copyfile(ROOT / "fixtures" / "v2" / "reference-derived-negative-fixtures.json", fixture_path)
            fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
            fixture["fixtures"][0]["expected_factory_result"] = "PASS"
            fixture_path.write_text(json.dumps(fixture, indent=2) + "\n", encoding="utf-8")

            errors = reference_superiority.validate_reference_superiority(fixture_path)

        self.assertTrue(any("must expect BLOCKED" in error for error in errors), errors)

    def test_capability_acquisition_run_activates_existing_provider(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            out = Path(tmp_dir) / "capability-run.json"

            self.assertEqual(
                factoryctl.main_with_args_for_test(
                    [
                        "capability-acquisition-run",
                        "--capability-gap",
                        "solana-ai-kit",
                        "--surface",
                        "solana",
                        "--created-at",
                        "2026-06-26T00:00:00+00:00",
                        "--out",
                        str(out),
                    ]
                ),
                0,
            )
            packet = json.loads(out.read_text(encoding="utf-8"))

        self.assertEqual(packet["activation_decision"], "activate")
        self.assertFalse(packet["block_allowed"])
        self.assertEqual(packet["promotion_result"]["promotion_decision"], "promote")
        self.assertFalse(packet["operator_block"]["allowed"])
        self.assertIn("solana-ai-kit", {candidate["candidate_id"] for candidate in packet["candidates"]})
        self.assertEqual(factoryctl.validate_capability_acquisition_run(packet), [])

    def test_capability_acquisition_run_covers_standard_missing_capability_surfaces(self) -> None:
        cases = {
            "browser": "frontend",
            "pdf-renderer": "pdf",
            "video-artifact": "video",
            "solana-ai-kit": "solana-ai-kit",
            "cloud-infra-security": "cloud",
        }
        for expected_candidate, surface in cases.items():
            with self.subTest(surface=surface):
                packet = factoryctl.build_capability_acquisition_run(
                    capability_gap=surface,
                    surfaces=[surface],
                    reference_sources=["external:public:reference-search"],
                    created_at="2026-06-26T00:00:00+00:00",
                    run_id=f"capability-acquisition-{surface}",
                )

                self.assertEqual(packet["activation_decision"], "activate")
                self.assertEqual(packet["promotion_result"]["promotion_decision"], "promote")
                self.assertFalse(packet["operator_block"]["allowed"])
                self.assertIn(expected_candidate, {candidate["candidate_id"] for candidate in packet["candidates"]})
                self.assertEqual(factoryctl.validate_capability_acquisition_run(packet), [])

    def test_capability_acquisition_run_operator_block_only_for_true_external_authority(self) -> None:
        packet = factoryctl.build_capability_acquisition_run(
            capability_gap="unavailable-specialist",
            surfaces=["unknown-surface-for-negative-test"],
            reference_sources=["external:public:reference-search"],
            created_at="2026-06-26T00:00:00+00:00",
            run_id="capability-acquisition-operator-block-negative-test",
        )

        self.assertEqual(packet["promotion_result"]["promotion_decision"], "no_safe_candidate")
        self.assertFalse(packet["promotion_result"]["external_authority_required"])
        self.assertFalse(packet["operator_block"]["allowed"])

        packet["operator_block"]["allowed"] = True
        packet["operator_block"]["reason_class"] = "no_safe_candidate_after_completed_search"
        errors = factoryctl.validate_capability_acquisition_run(packet)

        self.assertTrue(any("human/operator block is allowed only for true_external_authority" in error for error in errors), errors)

        packet["operator_block"]["reason_class"] = "true_external_authority"
        errors = factoryctl.validate_capability_acquisition_run(packet)

        self.assertTrue(any("operator_block requires promotion_result.external_authority_required=true" in error for error in errors), errors)

    def test_capability_acquisition_run_blocks_only_after_completed_search(self) -> None:
        packet = factoryctl.build_capability_acquisition_run(
            capability_gap="unavailable-specialist",
            surfaces=["unknown-surface-for-negative-test"],
            reference_sources=["external:public:reference-search"],
            created_at="2026-06-26T00:00:00+00:00",
            run_id="capability-acquisition-negative-test",
        )

        self.assertEqual(packet["activation_decision"], "block")
        self.assertTrue(packet["block_allowed"])
        self.assertTrue(packet["search_completed"])
        self.assertEqual(factoryctl.validate_capability_acquisition_run(packet), [])

        packet["search_completed"] = False
        errors = factoryctl.validate_capability_acquisition_run(packet)

        self.assertTrue(any("cannot block before search_completed=true" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()
