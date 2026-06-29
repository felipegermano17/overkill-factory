from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path


CODE_ROOT = Path(__file__).resolve().parents[1]
ROOT = CODE_ROOT.parent


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


surface_sync = load_module("validate_public_surface_sync", CODE_ROOT / "scripts" / "validate_public_surface_sync.py")


class PublicSurfaceSyncTest(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads((ROOT / "docs" / "public-surface.manifest.json").read_text(encoding="utf-8"))

    def test_public_surface_manifest_is_current(self) -> None:
        self.assertEqual(surface_sync.validate_manifest(), [])

    def test_manifest_schema_blocks_claim_checks_string_before_semantic_checks(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["surfaces"][0]["claim_checks"] = "source_refs_exist"

        findings = surface_sync.validate_manifest_data(mutated)

        self.assertTrue(
            any("$.surfaces[0].claim_checks" in finding and "expected type array" in finding for finding in findings),
            findings,
        )

    def test_worker_count_drift_is_detected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["surfaces"][0]["expected_worker_count"] = 999

        findings = surface_sync.validate_manifest_data(mutated)

        self.assertIn(
            "docs/visuals/overkill-factory-map-v1.0.3.html: manifest worker count 999 does not match registry count 40",
            findings,
        )

    def test_missing_public_boundary_phrase_is_detected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["surfaces"][0]["required_phrases"] = ["this phrase is intentionally absent from the public map"]

        findings = surface_sync.validate_manifest_data(mutated)

        self.assertTrue(any("missing required public-boundary phrase" in finding for finding in findings))

    def test_published_map_checksum_mismatch_is_detected(self) -> None:
        manifest = self.manifest()

        findings = surface_sync.validate_manifest_data(
            manifest,
            check_published=True,
            fetcher=lambda _url: b"stale published map",
        )

        self.assertTrue(any("published_out_of_sync" in finding for finding in findings))

    def test_runtime_overclaim_is_detected(self) -> None:
        findings = surface_sync.public_doc_overclaim_findings(
            "docs/visuals/overkill-factory-map-v1.0.3.html",
            "The visual map is the source of truth and map proves runtime readiness.",
        )

        self.assertEqual(
            findings,
            [
                "docs/visuals/overkill-factory-map-v1.0.3.html: public surface overclaims runtime authority",
                "docs/visuals/overkill-factory-map-v1.0.3.html: public surface overclaims runtime authority",
            ],
        )

    def test_map_fidelity_missing_workflow_phase_coverage_is_detected(self) -> None:
        manifest = self.manifest()
        surface = copy.deepcopy(manifest["surfaces"][0])

        findings = surface_sync.validate_map_fidelity(
            surface,
            "this public map intentionally omits every canonical phase term",
            root=ROOT,
        )

        self.assertTrue(
            any("fidelity workflow phase F1 has no derived map coverage" in finding for finding in findings),
            findings,
        )

    def test_map_fidelity_stage_node_title_drift_is_detected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["surfaces"][0]["fidelity_contract"]["required_stage_nodes"] = [
            {"node_id": "intake", "title": "Old Intake Name"}
        ]

        findings = surface_sync.validate_manifest_data(mutated)

        self.assertIn(
            "docs/visuals/overkill-factory-map-v1.0.3.html: fidelity stage node intake title "
            "'Universal Signal Intake' does not match 'Old Intake Name'",
            findings,
        )

    def test_map_fidelity_missing_stage_output_term_is_detected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["surfaces"][0]["fidelity_contract"]["required_stage_nodes"] = [
            {"node_id": "completion", "title": "Factory v1 Completion Gate", "required_output_terms": ["missing closure class"]}
        ]

        findings = surface_sync.validate_manifest_data(mutated)

        self.assertIn(
            "docs/visuals/overkill-factory-map-v1.0.3.html: fidelity stage node completion "
            "missing output term 'missing closure class'",
            findings,
        )

    def test_map_fidelity_missing_template_term_is_detected(self) -> None:
        manifest = self.manifest()
        surface = copy.deepcopy(manifest["surfaces"][0])
        surface["fidelity_contract"]["required_template_refs"] = ["templates/universal-signal-intake.json"]

        findings = surface_sync.validate_map_fidelity(
            surface,
            "this public map intentionally omits the template-backed intake name",
            root=ROOT,
        )

        self.assertIn(
            "docs/visuals/overkill-factory-map-v1.0.3.html: fidelity template_ref has no map coverage: "
            "templates/universal-signal-intake.json",
            findings,
        )


if __name__ == "__main__":
    unittest.main()
