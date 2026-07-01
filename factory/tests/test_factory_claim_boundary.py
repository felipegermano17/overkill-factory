from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "factoryctl.py"
TEMPLATE_PATH = ROOT / "templates" / "factory-claim-boundary.json"


def load_factoryctl():
    spec = importlib.util.spec_from_file_location("factoryctl", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["factoryctl"] = module
    spec.loader.exec_module(module)
    return module


def load_template() -> dict:
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))


def test_report_only_pass_template_forbids_release_production_and_receipt_five() -> None:
    factoryctl = load_factoryctl()
    packet = load_template()

    errors = factoryctl.validate_factory_claim_boundary(packet)

    assert errors == []


def test_report_only_pass_cannot_masquerade_as_release_ready() -> None:
    factoryctl = load_factoryctl()
    packet = load_template()
    packet["claimed_state"] = "release_readiness"
    packet["source_state"] = "report_only_pass"
    packet["qa_result_ref"] = "worker-result:qa:pass"
    packet["release_evidence_ref"] = "release-readiness:proof"

    errors = factoryctl.validate_factory_claim_boundary(packet)

    assert any("cannot be promoted directly" in error for error in errors)


def test_negative_closeout_cannot_allow_release_or_receipt_five_next() -> None:
    factoryctl = load_factoryctl()
    packet = load_template()
    packet["claimed_state"] = "negative_closeout"
    packet["source_state"] = "negative_closeout"
    packet["allowed_next_states"] = ["release_readiness", "receipt_five_ready"]

    errors = factoryctl.validate_factory_claim_boundary(packet)

    assert any("negative_closeout cannot list" in error for error in errors)


def test_receipt_five_ready_requires_all_strong_evidence_refs() -> None:
    factoryctl = load_factoryctl()
    packet = load_template()
    packet["claimed_state"] = "receipt_five_ready"
    packet["source_state"] = "production_readiness"
    packet["qa_result_ref"] = "worker-result:qa:pass"
    packet["release_evidence_ref"] = "release:proof"
    # production_evidence_ref, receipt_five_ref and human_gate_ref intentionally absent.

    errors = factoryctl.validate_factory_claim_boundary(packet)

    assert "claimed_state receipt_five_ready requires production_evidence_ref" in errors
    assert "claimed_state receipt_five_ready requires receipt_five_ref" in errors
    assert "claimed_state receipt_five_ready requires human_gate_ref" in errors


def test_production_readiness_with_required_refs_passes() -> None:
    factoryctl = load_factoryctl()
    packet = copy.deepcopy(load_template())
    packet.update(
        {
            "claim_id": "production-readiness-example",
            "claimed_state": "production_readiness",
            "source_state": "release_readiness",
            "qa_result_ref": "worker-result:qa:pass",
            "release_evidence_ref": "release-readiness:pass",
            "production_evidence_ref": "production-readiness:pass",
            "human_gate_ref": "operator-gate:approved",
            "forbidden_promotions": ["receipt_five_ready"],
            "allowed_next_states": ["receipt_five_ready"],
        }
    )

    errors = factoryctl.validate_factory_claim_boundary(packet)

    assert errors == []
