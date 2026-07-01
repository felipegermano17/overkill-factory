from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent
MODULE_PATH = ROOT / "scripts" / "validate_promise_implementation_map.py"
SPEC = importlib.util.spec_from_file_location("validate_promise_implementation_map", MODULE_PATH)
assert SPEC is not None
validator = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(validator)


class PromiseImplementationMapTests(unittest.TestCase):
    def test_promise_map_validator_passes(self) -> None:
        self.assertEqual(validator.validate_map(), [])

    def test_promise_map_covers_required_public_claims(self) -> None:
        data = json.loads((REPO_ROOT / "docs" / "promise-implementation-map.public.json").read_text(encoding="utf-8"))
        claim_ids = {claim["claim_id"] for claim in data["claims"]}

        self.assertEqual(validator.REQUIRED_CLAIM_IDS - claim_ids, set())

    def test_all_claims_have_boundary_and_proof_refs(self) -> None:
        data = json.loads((REPO_ROOT / "docs" / "promise-implementation-map.public.json").read_text(encoding="utf-8"))

        for claim in data["claims"]:
            with self.subTest(claim_id=claim["claim_id"]):
                self.assertTrue(claim["documentation_refs"])
                self.assertTrue(claim["implementation_refs"])
                self.assertTrue(claim["proof_refs"])
                self.assertTrue(claim["boundary_refs"])
                self.assertGreaterEqual(len(claim["boundary"]), 30)
                self.assertTrue(
                    any(ref.startswith(("tests/", "scripts/", "factory/tests/", "factory/scripts/")) for ref in claim["proof_refs"]),
                    claim["proof_refs"],
                )

    def test_cli_and_ci_include_promise_map_validator(self) -> None:
        workflow = (REPO_ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
        usage = (REPO_ROOT / "docs" / "pt-BR" / "uso.md").read_text(encoding="utf-8")
        usage_pt = (REPO_ROOT / "docs" / "pt-BR" / "uso.md").read_text(encoding="utf-8")

        command = "python3 scripts/validate_promise_implementation_map.py"
        self.assertIn("python scripts/validate_promise_implementation_map.py", workflow)
        for text in [usage, usage_pt]:
            with self.subTest(text=text[:40]):
                self.assertIn(command, text)

    def test_promise_map_cli_runs(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/validate_promise_implementation_map.py"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
