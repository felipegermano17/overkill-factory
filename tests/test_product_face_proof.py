from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "product_face_proof.py"
SPEC = importlib.util.spec_from_file_location("product_face_proof", MODULE_PATH)
assert SPEC is not None
product_face_proof = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["product_face_proof"] = product_face_proof
SPEC.loader.exec_module(product_face_proof)


class ProductFaceProofTest(unittest.TestCase):
    def test_parse_viewport_accepts_named_size(self) -> None:
        viewport = product_face_proof.parse_viewport("tablet=768x1024")

        self.assertEqual(viewport.name, "tablet")
        self.assertEqual(viewport.width, 768)
        self.assertEqual(viewport.height, 1024)
        self.assertEqual(viewport.label, "tablet 768x1024")

    def test_forced_fallback_writes_compatible_honest_result(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            html_path = tmp_path / "prototype.html"
            html_path.write_text(
                "<!doctype html><html lang='en'><head><title>Proof</title></head>"
                "<body><main><h1>Proof</h1><button aria-label='Save' disabled>Save</button></main></body></html>",
                encoding="utf-8",
            )
            out_path = tmp_path / "proof" / "product-face-result.json"

            result = product_face_proof.build_product_face_proof(
                target=str(html_path),
                out=out_path,
                force_fallback=True,
            )

            written = json.loads(out_path.read_text(encoding="utf-8"))

        self.assertEqual(result["record_type"], "product_face_result")
        self.assertEqual(written["result"], "WAIVED")
        self.assertTrue(written["blocking_findings"])
        self.assertIn("not-captured", written["screenshots"][0])
        self.assertEqual(written["a11y"]["status"], "not_run")
        self.assertEqual(written["overlap_check"]["status"], "not_run")
        self.assertTrue(written["evidence_refs"])
        serialized = json.dumps(written)
        self.assertNotIn("C:\\Users", serialized)
        self.assertNotIn("OneDrive", serialized)

    def test_forced_fallback_matches_factory_product_face_contract(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            html_path = Path(tmp) / "prototype.html"
            html_path.write_text("<html lang='en'><title>Proof</title><main>Ok</main></html>", encoding="utf-8")
            result = product_face_proof.build_product_face_proof(
                target=str(html_path),
                out=Path(tmp) / "result.json",
                force_fallback=True,
            )

        required = {
            "result",
            "tool_or_profile",
            "executed_by",
            "screenshots",
            "viewports",
            "checked_states",
            "user_journeys_checked",
            "a11y",
            "overlap_check",
            "performance_note",
            "blocking_findings",
            "evidence_refs",
            "next_action",
        }
        self.assertLessEqual(required, set(result))
        self.assertIn(result["result"], {"PASS", "WAIVED"})
        for field in ("screenshots", "viewports", "checked_states", "user_journeys_checked", "evidence_refs"):
            self.assertTrue(result[field])
        self.assertTrue(result["a11y"])
        self.assertTrue(result["overlap_check"])

    def test_card_binding_and_factory_alias_fields_are_present(self) -> None:
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            tmp_path = Path(tmp)
            html_path = tmp_path / "prototype.html"
            html_path.write_text("<html lang='en'><title>Proof</title><main>Ok</main></html>", encoding="utf-8")
            card_path = tmp_path / "card.md"
            card_path.write_text(
                "```json\n"
                + json.dumps(
                    {
                        "card_id": "CARD-001",
                        "slice_id": "SLICE-001",
                        "phase": "F13",
                        "risk_effective": "R2",
                        "surfaces": ["frontend"],
                        "executor_identity": "executor",
                        "reviewer_identity": "reviewer",
                    }
                )
                + "\n```\n",
                encoding="utf-8",
            )

            result = product_face_proof.build_product_face_proof(
                target=str(html_path),
                out=tmp_path / "result.json",
                force_fallback=True,
                card=card_path,
            )

        self.assertEqual(result["card_ref"]["card_id"], "CARD-001")
        self.assertEqual(result["card_ref"]["slice_id"], "SLICE-001")
        self.assertEqual(result["journeys"], result["user_journeys_checked"])
        self.assertEqual(result["accessibility"], result["a11y"])
        self.assertEqual(result["overlap"], result["overlap_check"])
        self.assertEqual(result["evidence_kind"], "real")
        self.assertFalse(result["reusable_for_product"])


if __name__ == "__main__":
    unittest.main()
