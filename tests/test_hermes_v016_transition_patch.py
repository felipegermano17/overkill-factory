from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "adapters" / "hermes" / "validate_v016_transition_patch.py"
SPEC = importlib.util.spec_from_file_location("validate_v016_transition_patch", MODULE_PATH)
assert SPEC is not None
validate_v016_transition_patch = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["validate_v016_transition_patch"] = validate_v016_transition_patch
SPEC.loader.exec_module(validate_v016_transition_patch)


class HermesV016TransitionPatchTest(unittest.TestCase):
    def test_patch_receipt_static_validation_passes(self) -> None:
        receipt = validate_v016_transition_patch.build_receipt(None)

        self.assertEqual(receipt["result"], "PASS")
        self.assertEqual(receipt["static_validation"]["missing_markers"], [])
        self.assertEqual(receipt["static_validation"]["forbidden_markers"], [])
        self.assertEqual(receipt["apply_validation"]["result"], "SKIPPED")


if __name__ == "__main__":
    unittest.main()
