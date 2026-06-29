from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "canonical_enforcement_audit.py"
SPEC = importlib.util.spec_from_file_location("canonical_enforcement_audit", MODULE_PATH)
assert SPEC is not None
canonical_enforcement_audit = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules["canonical_enforcement_audit"] = canonical_enforcement_audit
SPEC.loader.exec_module(canonical_enforcement_audit)


class CanonicalEnforcementAuditTest(unittest.TestCase):
    def test_canonical_enforcement_matrix_has_no_doc_only_gaps(self) -> None:
        matrix = {
            "record_type": "canonical_enforcement_matrix",
            "requirements": [
                {
                    "id": "factoryctl.contract",
                    "claim": "Runtime gates need an executable contract.",
                    "source_doc_refs": ["external:canonical.md"],
                    "required_layers": ["contract", "runtime", "test"],
                    "enforcement_refs": [
                        {"layer": "contract", "kind": "schema", "path": "schemas/factory-card.schema.json"},
                        {"layer": "runtime", "kind": "script", "path": "scripts/factoryctl.py"},
                        {"layer": "test", "kind": "test", "path": "tests/test_factoryctl.py"},
                    ],
                    "status": "enforced",
                }
            ],
        }

        errors = canonical_enforcement_audit.validate_matrix(matrix)

        self.assertEqual(errors, [])

    def test_matrix_rejects_external_only_or_missing_layers(self) -> None:
        matrix = {
            "record_type": "canonical_enforcement_matrix",
            "requirements": [
                {
                    "id": "bad.doc-only",
                    "claim": "Documentation without enforcement is not enough.",
                    "source_doc_refs": ["external:canonical.md"],
                    "required_layers": ["contract", "runtime", "test"],
                    "enforcement_refs": [
                        {
                            "layer": "contract",
                            "kind": "schema",
                            "path": "external:some-doc.md",
                            "covers": "not enforceable"
                        }
                    ],
                    "status": "enforced"
                }
            ],
        }

        errors = canonical_enforcement_audit.validate_matrix(matrix)

        self.assertIn("bad.doc-only: missing enforcement layer(s): runtime, test", errors)
        self.assertIn("bad.doc-only: enforcement ref cannot be external-only: external:some-doc.md", errors)


if __name__ == "__main__":
    unittest.main()
