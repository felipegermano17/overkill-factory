from __future__ import annotations

import copy
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
    return factoryctl.load_json_like(ROOT / "templates" / "vfinal-factory-card.json")


class RuntimeHardeningTest(unittest.TestCase):
    def test_placeholder_devnet_secret_mode_passes_for_non_production_proof(self) -> None:
        card = base_card()
        card["secret_delivery_policy"]["environment"] = "devnet"
        card["secret_delivery_policy"]["delivery_mode"] = "placeholder"
        card["autonomy_readiness_packet"]["secret_delivery_mode"] = "placeholder"

        self.assertEqual(factoryctl.validate_card(card), [])

    def test_production_api_key_in_startup_env_blocks_without_waiver(self) -> None:
        card = base_card()
        card["secret_delivery_policy"].update(
            {
                "secret_type": "api_key",
                "sensitivity": "high",
                "environment": "production",
                "delivery_mode": "startup_env",
                "scope": "write_limited production API",
            }
        )
        card["autonomy_readiness_packet"]["secret_delivery_mode"] = "startup_env"
        card["agent_runtime_hardening_profile"]["credential_exposure"] = "startup_env"

        errors = factoryctl.validate_card(card)
        report = factoryctl.build_gate_report(card)

        self.assertIn(
            "secret_delivery_policy.delivery_mode startup_env requires explicit human-gated waiver with compensating controls",
            errors,
        )
        self.assertEqual(report["gate_status"], "blocked")

    def test_hardware_signer_mode_passes_with_public_safe_evidence_ref(self) -> None:
        card = base_card()
        card["secret_delivery_policy"].update(
            {
                "secret_type": "signing_key",
                "sensitivity": "critical",
                "environment": "mainnet",
                "delivery_mode": "hardware_signer",
                "scope": "signing only through signer boundary",
                "audit_log_ref": "external:signer-audit-ref",
                "revocation_path": "external:signer-revocation-runbook",
                "evidence_refs": ["external:hardware-signer-proof"],
            }
        )
        card["autonomy_readiness_packet"]["secret_delivery_mode"] = "hardware_signer"
        card["agent_runtime_hardening_profile"]["credential_exposure"] = "hardware_signer"
        card["agent_runtime_hardening_profile"]["evidence_refs"] = ["external:hardware-signer-proof"]

        self.assertEqual(factoryctl.validate_card(card), [])

    def test_prompt_context_secret_exposure_always_blocks(self) -> None:
        card = base_card()
        card["secret_delivery_policy"]["delivery_mode"] = "prompt_context"
        card["secret_delivery_policy"]["human_gated_waiver"] = {
            "gate_ref": "external:human-waiver",
            "compensating_controls": ["rotate after use"],
        }
        card["autonomy_readiness_packet"]["secret_delivery_mode"] = "prompt_context"

        errors = factoryctl.validate_card(card)

        self.assertIn("secret_delivery_policy.delivery_mode prompt_context is always forbidden", errors)

    def test_read_only_worker_does_not_require_full_hardening_profile(self) -> None:
        card = factoryctl.load_json_like(ROOT / "examples" / "cards" / "v35_valid_product_face.md")
        card.pop("agent_runtime_hardening_profile", None)
        card.pop("secret_delivery_policy", None)

        self.assertEqual(factoryctl.validate_card(card), [])

    def test_shell_worker_without_hardening_profile_blocks(self) -> None:
        card = base_card()
        card.pop("agent_runtime_hardening_profile")
        card["runtime_contract"] = dict(card["runtime_contract"])
        card["runtime_contract"]["tool_surface"] = ["shell"]

        errors = factoryctl.validate_card(card)

        self.assertIn("agent_runtime_hardening_profile required for tool-using material execution", errors)

    def test_unrestricted_network_without_human_gate_blocks(self) -> None:
        card = base_card()
        card["agent_runtime_hardening_profile"]["network_scope"] = "unrestricted"
        card["agent_runtime_hardening_profile"]["human_gate_triggers"] = []

        errors = factoryctl.validate_card(card)

        self.assertIn("agent_runtime_hardening_profile.human_gate_triggers must be a non-empty array", errors)
        self.assertIn("agent_runtime_hardening_profile unrestricted network requires human_gate_triggers", errors)

    def test_material_execution_links_autonomy_to_hardening_evidence(self) -> None:
        card = base_card()
        card["autonomy_readiness_packet"].pop("runtime_hardening_profile_ref")

        errors = factoryctl.validate_card(card)

        self.assertIn("autonomy_readiness_packet.runtime_hardening_profile_ref required for material execution", errors)

    def test_blocked_prompt_injection_attempt_requires_public_safe_evidence_ref(self) -> None:
        card = base_card()
        card["agent_runtime_hardening_profile"]["blocked_abuse_evidence_refs"] = []

        errors = factoryctl.validate_card(card)

        self.assertIn("agent_runtime_hardening_profile.blocked_abuse_evidence_refs required for tool-using workers", errors)

    def test_worker_packet_omits_raw_secret_values_from_public_policy(self) -> None:
        card = base_card()
        card["secret_delivery_policy"] = copy.deepcopy(card["secret_delivery_policy"])
        card["secret_delivery_policy"]["secret_value"] = "example-raw-secret-value"

        errors = factoryctl.validate_card(card)
        packet = factoryctl.build_worker_packet("factory-orchestrator", card, ROOT / "templates" / "vfinal-factory-card.json")
        packet_text = json.dumps(packet)

        self.assertIn("secret_delivery_policy must contain refs and policy only, never raw secret values or private secret paths", errors)
        self.assertNotIn("example-raw-secret-value", packet_text)
        self.assertNotIn("secret_delivery_policy", packet)
        self.assertEqual(
            packet["agent_runtime_hardening_profile"]["secret_delivery_policy_ref"],
            "templates/vfinal-factory-card.json#secret_delivery_policy",
        )


if __name__ == "__main__":
    unittest.main()
