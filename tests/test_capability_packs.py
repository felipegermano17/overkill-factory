from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
SPEC = importlib.util.spec_from_file_location("factoryctl", MODULE_PATH)
assert SPEC is not None
factoryctl = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["factoryctl"] = factoryctl
SPEC.loader.exec_module(factoryctl)


def base_card() -> dict:
    return json.loads((ROOT / "templates" / "vfinal-factory-card.json").read_text(encoding="utf-8"))


def activated_game_contract() -> dict:
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
        "worker_mapping": {
            "runtime": ["game-runtime-builder"],
            "design": ["game-design-specialist"],
            "qa": ["game-qa-specialist"],
        },
    }


class CapabilityPacksTest(unittest.TestCase):
    def test_capability_pack_registry_contains_modular_product_domains(self) -> None:
        packs = json.loads((ROOT / "agents" / "capability-packs.public.json").read_text(encoding="utf-8"))["packs"]

        for pack_id in [
            "web-saas-core",
            "operator-onboarding-pack",
            "public-docs-knowledge-pack",
            "local-web-cockpit-pack",
            "mobile-app-pack",
            "desktop-app-pack",
            "game-product-pack",
            "ai-ml-product-pack",
            "fintech-payments-pack",
            "regulated-domain-pack",
            "data-analytics-pack",
            "browser-extension-pack",
            "hardware-iot-pack",
        ]:
            with self.subTest(pack_id=pack_id):
                self.assertIn(pack_id, packs)
                self.assertTrue(packs[pack_id]["covers_surfaces"])
                self.assertTrue(packs[pack_id]["evidence_required"])

    def test_new_operator_packs_have_executable_contracts(self) -> None:
        packs = json.loads((ROOT / "agents" / "capability-packs.public.json").read_text(encoding="utf-8"))["packs"]

        for pack_id in ["operator-onboarding-pack", "public-docs-knowledge-pack"]:
            with self.subTest(pack_id=pack_id):
                pack = packs[pack_id]
                self.assertTrue(pack["plain_purpose"])
                self.assertTrue(pack["input_contract"])
                self.assertTrue(pack["output_contract"])
                self.assertTrue(pack["local_smoke_path"].startswith("python scripts/"))
                self.assertNotIn(".tmp/", json.dumps(pack))

    def test_ready_core_surfaces_pass_capability_coverage(self) -> None:
        card = base_card()

        errors = factoryctl.validate_capability_coverage(card)

        self.assertEqual(errors, [])

    def test_web_pack_separates_responsive_from_native_mobile(self) -> None:
        packs = json.loads((ROOT / "agents" / "capability-packs.public.json").read_text(encoding="utf-8"))["packs"]

        self.assertIn("responsive", packs["web-saas-core"]["covers_surfaces"])
        self.assertIn("mobile-web", packs["web-saas-core"]["covers_surfaces"])
        self.assertNotIn("mobile", packs["web-saas-core"]["covers_surfaces"])
        self.assertIn("native-mobile", packs["mobile-app-pack"]["covers_surfaces"])

    def test_ambiguous_mobile_surface_blocks(self) -> None:
        card = base_card()
        card["surfaces"] = ["mobile"]

        errors = factoryctl.validate_capability_coverage(card)

        self.assertTrue(any("ambiguous capability surface 'mobile'" in error for error in errors), errors)

    def test_local_web_cockpit_pack_covers_control_tower_without_discord_requirement(self) -> None:
        packs = json.loads((ROOT / "agents" / "capability-packs.public.json").read_text(encoding="utf-8"))["packs"]
        pack = packs["local-web-cockpit-pack"]

        self.assertIn("control-tower", pack["covers_surfaces"])
        self.assertIn("operator-cockpit", pack["covers_surfaces"])
        self.assertIn("security", pack["covers_surfaces"])
        self.assertIn("status snapshot", json.dumps(pack).lower())
        self.assertIn("Discord is not required unless explicitly requested".lower(), json.dumps(pack).lower())

    def test_game_surface_blocks_without_activated_pack(self) -> None:
        card = base_card()
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card.pop("capability_pack_contract", None)

        errors = factoryctl.validate_capability_coverage(card)

        self.assertTrue(any("game-product-pack" in error for error in errors), errors)

    def test_game_surface_passes_when_pack_is_activated(self) -> None:
        card = base_card()
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card["capability_pack_contract"] = activated_game_contract()

        errors = factoryctl.validate_capability_coverage(card)

        self.assertEqual(errors, [])

    def test_activated_pack_rejects_partial_surface_coverage(self) -> None:
        card = base_card()
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card["capability_pack_contract"] = activated_game_contract()
        card["capability_pack_contract"]["covered_surfaces"] = ["game", "asset-pipeline"]

        errors = factoryctl.validate_capability_coverage(card)

        self.assertIn("capability_pack_contract.covered_surfaces missing required surface '3d'", errors)

    def test_activated_pack_requires_profile_bindings_and_smoke_eval_refs(self) -> None:
        card = base_card()
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card["capability_pack_contract"] = activated_game_contract()
        card["capability_pack_contract"].pop("profile_binding_refs")
        card["capability_pack_contract"]["smoke_evidence_ref"] = ""
        card["capability_pack_contract"]["eval_path"] = ""

        errors = factoryctl.validate_capability_coverage(card)

        self.assertIn("capability_pack_contract.profile_binding_refs must map each specialist worker to a profile binding ref", errors)
        self.assertIn("capability_pack_contract.smoke_evidence_ref is required for activated packs", errors)
        self.assertIn("capability_pack_contract.eval_path is required for activated packs", errors)

    def test_activation_example_stays_blocked_until_real_evidence_replaces_placeholders(self) -> None:
        example = json.loads((ROOT / "templates" / "capability-pack-activation-example.json").read_text(encoding="utf-8"))

        self.assertEqual(example["pack_id"], "game-product-pack")
        self.assertEqual(example["status"], "blocked")
        self.assertEqual(example["lifecycle_state"], "proposed")
        self.assertTrue(example["missing_capabilities"])

    def test_unknown_surface_blocks_when_strict_coverage_is_required(self) -> None:
        card = base_card()
        card["surfaces"] = ["quantum-widget"]
        card.pop("capability_pack_contract", None)

        errors = factoryctl.validate_capability_coverage(card)

        self.assertIn("capability pack missing for surface 'quantum-widget'", errors)


if __name__ == "__main__":
    unittest.main()
