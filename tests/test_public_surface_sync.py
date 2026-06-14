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


surface_sync = load_module("validate_public_surface_sync", ROOT / "scripts" / "validate_public_surface_sync.py")


class PublicSurfaceSyncTest(unittest.TestCase):
    def manifest(self) -> dict:
        return json.loads((ROOT / "docs" / "public-surface.manifest.json").read_text(encoding="utf-8"))

    def test_public_surface_manifest_is_current(self) -> None:
        self.assertEqual(surface_sync.validate_manifest(), [])

    def test_worker_count_drift_is_detected(self) -> None:
        manifest = self.manifest()
        mutated = copy.deepcopy(manifest)
        mutated["surfaces"][0]["expected_worker_count"] = 999

        findings = surface_sync.validate_manifest_data(mutated)

        self.assertIn(
            "docs/visuals/overkill-factory-map-v0.1.0.html: manifest worker count 999 does not match registry count 40",
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
            "docs/visuals/overkill-factory-map-v0.1.0.html",
            "The visual map is the source of truth and map proves runtime readiness.",
        )

        self.assertEqual(
            findings,
            [
                "docs/visuals/overkill-factory-map-v0.1.0.html: public surface overclaims runtime authority",
                "docs/visuals/overkill-factory-map-v0.1.0.html: public surface overclaims runtime authority",
            ],
        )


if __name__ == "__main__":
    unittest.main()
