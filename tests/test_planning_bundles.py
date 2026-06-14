from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


planning_bundles = load_module("validate_planning_bundles", ROOT / "scripts" / "validate_planning_bundles.py")


class PlanningBundleValidationTest(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads((ROOT / "planning-bundles" / "manifest.json").read_text(encoding="utf-8"))

    def test_current_manifest_passes(self) -> None:
        self.assertEqual(planning_bundles.validate(), [])

    def test_missing_included_file_is_detected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        bundle = mutated["bundles"][0]
        bundle["included_files"].append("planning-bundles/product-sot-drafting/missing.md")

        findings = planning_bundles.validate_manifest_data(mutated)

        self.assertIn(
            "product-sot-drafting-v1: included file does not exist: planning-bundles/product-sot-drafting/missing.md",
            findings,
        )

    def test_output_authority_must_remain_candidate_only(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["bundles"][0]["expected_outputs"][0]["authority"] = "approved"

        findings = planning_bundles.validate_manifest_data(mutated)

        self.assertIn(
            "product-sot-drafting-v1: expected output product_sot_candidate must be candidate_only",
            findings,
        )

    def test_missing_secret_boundary_marker_is_detected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        bundle = mutated["bundles"][0]
        bundle["safety_rules"] = ["Use public-safe excerpts."]
        bundle["included_files"] = [
            "planning-bundles/product-sot-drafting/templates/product-sot-candidate.md",
        ]
        bundle["entrypoint"] = bundle["included_files"][0]

        findings = planning_bundles.validate_manifest_data(mutated)

        self.assertIn("product-sot-drafting-v1: missing required safety marker 'Do not paste secrets'", findings)

    def test_bundle_kind_cannot_be_capability_pack(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["bundles"][0]["bundle_kind"] = "capability_pack"

        findings = planning_bundles.validate_manifest_data(mutated)

        self.assertIn("product-sot-drafting-v1: bundle_kind must be planning_protocol", findings)

    def test_included_files_must_stay_inside_bundle_directory(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["bundles"][0]["included_files"].append("docs/concepts/operator-journey.md")

        findings = planning_bundles.validate_manifest_data(mutated)

        self.assertIn(
            "product-sot-drafting-v1: included file must live under planning-bundles/: docs/concepts/operator-journey.md",
            findings,
        )
        self.assertIn(
            "product-sot-drafting-v1: included file must stay under the bundle entrypoint directory: docs/concepts/operator-journey.md",
            findings,
        )

    def test_execution_schema_refs_are_rejected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["bundles"][0]["compatible_schema_refs"].append("schemas/worker-packet.schema.json")

        findings = planning_bundles.validate_manifest_data(mutated)

        self.assertIn(
            "product-sot-drafting-v1: compatible schema crosses into execution surface 'worker-packet': schemas/worker-packet.schema.json",
            findings,
        )

    def test_import_validation_cannot_target_static_runtime_examples(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["bundles"][0]["import_validation"]["commands"].append(
            "python scripts/factoryctl.py validate-card templates/vfinal-factory-card.json"
        )

        findings = planning_bundles.validate_manifest_data(mutated)

        self.assertIn(
            "product-sot-drafting-v1: import validation command must not target fixed runtime/example artifacts 'templates/': python scripts/factoryctl.py validate-card templates/vfinal-factory-card.json",
            findings,
        )

    def test_open_decision_list_has_its_own_candidate_schema(self) -> None:
        manifest = self.manifest()
        output_refs = {output["output_id"]: output["candidate_schema_ref"] for output in manifest["bundles"][0]["expected_outputs"]}

        self.assertEqual(output_refs["open_decision_list"], "schemas/open-decision-list.schema.json")

    def test_public_surface_knows_planning_bundle_index(self) -> None:
        surface_manifest = json.loads((ROOT / "docs" / "public-surface.manifest.json").read_text(encoding="utf-8"))

        paths = {surface["path"] for surface in surface_manifest["surfaces"]}

        self.assertIn("planning-bundles/README.md", paths)


if __name__ == "__main__":
    unittest.main()
