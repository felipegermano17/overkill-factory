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


class CapabilityPacksTest(unittest.TestCase):
    def test_capability_pack_registry_contains_modular_product_domains(self) -> None:
        packs = json.loads((ROOT / "agents" / "capability-packs.public.json").read_text(encoding="utf-8"))["packs"]

        for pack_id in [
            "web-saas-core",
            "operator-onboarding-pack",
            "public-docs-knowledge-pack",
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

    def test_template_pack_surfaces_pass_capability_coverage(self) -> None:
        card = base_card()

        errors = factoryctl.validate_capability_coverage(card)

        self.assertEqual(errors, [])

    def test_game_surface_blocks_without_activated_pack(self) -> None:
        card = base_card()
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card.pop("capability_pack_contract", None)

        errors = factoryctl.validate_capability_coverage(card)

        self.assertTrue(any("game-product-pack" in error for error in errors), errors)

    def test_game_surface_passes_when_pack_is_activated(self) -> None:
        card = base_card()
        card["surfaces"] = ["game", "3d", "asset-pipeline"]
        card["capability_pack_contract"] = {
            "record_type": "capability_pack_contract",
            "pack_id": "game-product-pack",
            "status": "activated",
            "covered_surfaces": ["game", "3d", "asset-pipeline"],
            "specialist_workers": ["game-runtime-builder", "game-design-specialist", "game-qa-specialist"],
            "activation_evidence_refs": ["external:game-pack-activation"],
            "missing_capabilities": [],
            "execution_rule": "Game execution is allowed only after playable smoke, performance budget and game QA proof exist.",
        }

        errors = factoryctl.validate_capability_coverage(card)

        self.assertEqual(errors, [])

    def test_unknown_surface_blocks_when_strict_coverage_is_required(self) -> None:
        card = base_card()
        card["surfaces"] = ["quantum-widget"]
        card.pop("capability_pack_contract", None)

        errors = factoryctl.validate_capability_coverage(card)

        self.assertIn("capability pack missing for surface 'quantum-widget'", errors)


if __name__ == "__main__":
    unittest.main()
