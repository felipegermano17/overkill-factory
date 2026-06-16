from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
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

VALIDATOR_PATH = ROOT / "scripts" / "validate_public_json_artifacts.py"
VALIDATOR_SPEC = importlib.util.spec_from_file_location("validate_public_json_artifacts", VALIDATOR_PATH)
assert VALIDATOR_SPEC is not None
public_json_validator = importlib.util.module_from_spec(VALIDATOR_SPEC)
assert VALIDATOR_SPEC.loader is not None
sys.modules["validate_public_json_artifacts"] = public_json_validator
VALIDATOR_SPEC.loader.exec_module(public_json_validator)


def evidence_bundle(**overrides: object) -> dict:
    bundle = {
        "$schema": "https://overkill-factory.dev/schemas/operational-evidence-bundle.schema.json",
        "record_type": "operational_evidence_bundle",
        "bundle_id": "bundle-fixture-001",
        "claim_id": "claim-fixture-001",
        "claim_text": "The fixture claim has enough public-safe evidence to be checked.",
        "claim_scope": "gate",
        "materiality": "medium",
        "verification_method": "schema_validation",
        "steps_executed": [
            "Load the operational evidence bundle fixture.",
            "Validate schema and semantic factoryctl rules."
        ],
        "expected_result": "The bundle passes schema and semantic validation.",
        "observed_result": "The bundle contains public-safe artifact references.",
        "artifacts": [
            {
                "artifact_ref": "schemas/operational-evidence-bundle.schema.json",
                "artifact_type": "schema_validation",
                "public_safe": True,
                "basis": "Public schema defines the accepted bundle shape."
            }
        ],
        "verdict": "CONFIRMED",
        "evidence_kind": "real",
        "confidence_boundary": "This proves only the fixture claim, not production runtime behavior.",
        "freshness": {
            "checked_at": "2026-06-16T00:00:00+00:00",
            "source_ref": "repo:overkill-factory"
        },
        "private_evidence_policy": {
            "contains_private_evidence": False,
            "raw_private_evidence_embedded": False,
            "public_safe_refs_only": True,
            "redaction_policy": "Raw private evidence stays outside public artifacts."
        },
        "reusable_for_product": True,
        "reviewer_ref": "external:public-contract-review",
        "next_safe_action": "Attach this bundle only to claims with matching scope."
    }
    bundle.update(overrides)
    return bundle


class OperationalEvidenceBundleTest(unittest.TestCase):
    def test_confirmed_bundle_validates(self) -> None:
        errors = factoryctl.validate_operational_evidence_bundle(evidence_bundle())

        self.assertEqual(errors, [])

    def test_refuted_bundle_validates_with_artifacts(self) -> None:
        bundle = evidence_bundle(
            verdict="REFUTED",
            observed_result="The checked artifact contradicts the claim.",
            next_safe_action="Repair the claim or rerun with corrected evidence."
        )

        errors = factoryctl.validate_operational_evidence_bundle(bundle)

        self.assertEqual(errors, [])

    def test_inconclusive_bundle_requires_next_action(self) -> None:
        bundle = evidence_bundle(verdict="INCONCLUSIVE", next_safe_action="")

        errors = factoryctl.validate_operational_evidence_bundle(bundle)

        self.assertTrue(any("next_safe_action" in error for error in errors), errors)

    def test_blocked_bundle_requires_next_action(self) -> None:
        bundle = evidence_bundle(verdict="BLOCKED", next_safe_action="retry")

        errors = factoryctl.validate_operational_evidence_bundle(bundle)

        self.assertTrue(any("smallest safe next action" in error or "next_safe_action" in error for error in errors), errors)

    def test_waived_bundle_requires_waiver_authority(self) -> None:
        bundle = evidence_bundle(verdict="WAIVED", evidence_kind="waiver")

        errors = factoryctl.validate_operational_evidence_bundle(bundle)

        self.assertTrue(any("waiver" in error for error in errors), errors)

        bundle["waiver"] = {
            "owner": "risk-owner",
            "reason": "Temporary documented exception for fixture validation.",
            "expires_at": "2026-07-16T00:00:00+00:00",
            "reviewer_or_human_gate_ref": "external:maintainer-human-gate",
            "compensating_controls": ["manual review before promotion"],
            "evidence_refs": ["external:public-waiver-review"]
        }

        self.assertEqual(factoryctl.validate_operational_evidence_bundle(bundle), [])

    def test_synthetic_bundle_cannot_be_reused_for_product(self) -> None:
        bundle = evidence_bundle(evidence_kind="synthetic", reusable_for_product=True)

        errors = factoryctl.validate_operational_evidence_bundle(bundle)

        self.assertTrue(any("reusable_for_product=false" in error for error in errors), errors)
        self.assertTrue(any("cannot_satisfy" in error for error in errors), errors)

        bundle["reusable_for_product"] = False
        bundle["cannot_satisfy"] = ["customer acceptance", "release readiness"]

        self.assertEqual(factoryctl.validate_operational_evidence_bundle(bundle), [])

    def test_unsafe_private_artifact_ref_is_rejected(self) -> None:
        bundle = evidence_bundle(
            artifacts=[
                {
                    "artifact_ref": ".tmp/factory-runs/private/raw-log.txt",
                    "artifact_type": "report_ref",
                    "public_safe": True,
                    "basis": "This should never be public."
                }
            ]
        )

        errors = factoryctl.validate_operational_evidence_bundle(bundle)

        self.assertTrue(any("artifact_ref must be public-safe" in error for error in errors), errors)

    def test_missing_claim_steps_artifacts_and_ambiguous_verdict_are_rejected(self) -> None:
        bundle = evidence_bundle(claim_text="", steps_executed=[], artifacts=[], verdict="MAYBE")

        errors = factoryctl.validate_operational_evidence_bundle(bundle)

        self.assertTrue(any("claim_text" in error for error in errors), errors)
        self.assertTrue(any("steps_executed" in error for error in errors), errors)
        self.assertTrue(any("artifacts" in error for error in errors), errors)
        self.assertTrue(any("verdict" in error for error in errors), errors)

    def test_public_template_validates_with_schema_and_domain_rules(self) -> None:
        schemas = public_json_validator.load_schemas()
        schema = schemas["operational-evidence-bundle.schema.json"]
        template = json.loads((ROOT / "templates" / "operational-evidence-bundle.json").read_text(encoding="utf-8"))

        schema_errors = public_json_validator.validate_node(schema, template, "$", schemas=schemas, root_schema=schema)
        domain_errors = public_json_validator.validate_domain_rules(template, "$")

        self.assertEqual(schema_errors + domain_errors, [])

    def test_public_validator_rejects_private_artifact_ref(self) -> None:
        bundle = evidence_bundle(
            artifacts=[
                {
                    "artifact_ref": ".tmp/factory-runs/private/raw-log.json",
                    "artifact_type": "report_ref",
                    "public_safe": True,
                    "basis": "Transient private run output."
                }
            ]
        )

        errors = public_json_validator.validate_domain_rules(bundle, "$")

        self.assertTrue(any("$.artifacts[0].artifact_ref" in error for error in errors), errors)

    def test_factoryctl_cli_validates_bundle_independently(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "bundle.json"
            path.write_text(json.dumps(evidence_bundle()), encoding="utf-8")

            result = factoryctl.main_with_args_for_test(["validate-evidence-bundle", str(path)])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
