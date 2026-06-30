import importlib.util
import json
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "work_product_quality_firewall.py"
SPEC = importlib.util.spec_from_file_location("work_product_quality_firewall", MODULE_PATH)
assert SPEC is not None
quality = importlib.util.module_from_spec(SPEC)
sys.modules["work_product_quality_firewall"] = quality
assert SPEC.loader is not None
SPEC.loader.exec_module(quality)


def test_shallow_product_sot_scope_summary_fails_prd_grade_quality():
    sot = {
        "record_type": "product_sot_candidate",
        "product": "KAXIS V1",
        "scope_in": ["USDC stake", "cadastro", "admin"],
        "scope_out": ["Pix", "mobile"],
        "acceptance_criteria": ["operator can approve scope"],
    }

    result = quality.validate_product_sot_prd_grade(sot)

    assert result.process_pass is True
    assert result.quality_pass is False
    codes = {finding.code for finding in result.findings}
    assert "missing_product_intent" in codes
    assert "missing_source_traceability" in codes
    assert "missing_user_journeys" in codes
    assert "missing_admin_journeys" in codes
    assert "missing_downstream_handoff" in codes


def test_prd_grade_product_sot_passes_quality_firewall():
    sot = {
        "record_type": "product_sot_candidate",
        "product_intent": "KAXIS V1 delivers a global web/onchain USDC stake product with Web3 mostly under the hood.",
        "source_traceability": [
            {"source_ref": "complement#flow-v6", "requirement_ids": ["REQ-UX-001", "REQ-STAKE-001"]},
            {"source_ref": "20apy-ff#repo-study", "requirement_ids": ["REQ-ARCH-001"]},
        ],
        "personas": ["retail investor", "operations admin"],
        "user_journeys": [
            {"id": "UJ-01", "steps": ["login", "complete cadastro", "claim KX benefit", "enter platform"]},
            {"id": "UJ-02", "steps": ["choose stake", "pay USDC", "see active position", "redeem at maturity"]},
        ],
        "admin_journeys": [
            {"id": "AJ-01", "steps": ["review user", "inspect payment intent", "reconcile stake", "handle exception"]},
        ],
        "functional_requirements": [
            {"id": "REQ-STAKE-001", "text": "User can create a USDC stake payment intent."},
            {"id": "REQ-ADMIN-001", "text": "Admin can reconcile user positions and payment events."},
            {"id": "REQ-UX-001", "text": "Flow-v6 states map to real system states."},
        ],
        "non_functional_requirements": [
            {"id": "NFR-AUDIT-001", "text": "Every financial display is traceable to ledger/onchain/database events."},
            {"id": "NFR-SEC-001", "text": "No production signing or secrets use without later gate."},
        ],
        "state_model_requirements": [
            "empty", "loading", "error", "success", "blocked", "pending", "expired", "review"
        ],
        "data_ledger_reconciliation_requirements": [
            "payment intent must reconcile against wallet/onchain/database events",
            "divergence must surface as explicit operational state",
        ],
        "acceptance_criteria_by_flow": {
            "cadastro": ["CPF/WhatsApp/user/referrer fields validated", "blocked/expired code states exist"],
            "stake": ["USDC payment intent is traceable", "maturity/redemption state is visible"],
        },
        "decisions_and_open_questions": [
            {"id": "D-001", "status": "open", "owner": "architecture", "text": "Normalize exact stake pool rules."}
        ],
        "downstream_handoff": {
            "architecture": ["onchain/offchain boundaries", "ledger requirements"],
            "ux": ["flow-v6 states", "blocked modules"],
            "security": ["custody/signing forbidden now", "PII/admin constraints"],
            "implementation": ["functional requirements", "acceptance criteria"],
            "qa": ["journey and state acceptance criteria"],
        },
    }

    result = quality.validate_product_sot_prd_grade(sot)

    assert result.process_pass is True
    assert result.readback_pass is True
    assert result.quality_pass is True
    assert result.findings == []


def test_quality_firewall_refuses_process_pass_without_quality_pass():
    result = quality.QualityResult(
        artifact_type="product_sot",
        process_pass=True,
        readback_pass=True,
        quality_pass=False,
        findings=[quality.QualityFinding("too_shallow", "error", "Artifact is shallow")],
    )

    assert quality.can_promote(result) is False


def test_completion_readback_fails_missing_claimed_artifact():
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        completion = {
            "artifact_paths": ["exists.json", "missing.json"],
            "changed": ["claimed artifacts"],
            "verification_result": "PASS",
        }
        (root / "exists.json").write_text("{}", encoding="utf-8")

        result = quality.validate_completion_readback(completion, root)

    assert result.readback_pass is False
    assert result.quality_pass is False
    assert any(f.code == "claimed_artifact_missing" for f in result.findings)


def test_human_gate_primary_json_attachment_fails_operator_quality():
    package = {
        "record_type": "operator_delivery_receipt",
        "primary_message": "Decisão pendente: aprovar Product SOT. Aprovar não autoriza deploy/mainnet/fundos.",
        "primary_attachment": {"path": "manifest.json", "media_type": "application/json", "role": "primary"},
        "valid_replies": ["Aprovo", "Corrigir: ..."],
        "approval_authorizes": ["seguir para arquitetura"],
        "approval_does_not_authorize": ["deploy", "mainnet", "fundos", "secrets", "custody", "signing"],
    }

    result = quality.validate_human_gate_artifact(package)

    assert result.quality_pass is False
    assert any(f.code == "primary_attachment_json" for f in result.findings)


def test_human_gate_designed_pdf_passes_operator_quality():
    package = {
        "record_type": "operator_delivery_receipt",
        "primary_message": "Decisão pendente: aprovar Product SOT revisada. Se aprovar, segue para método/arquitetura. Aprovar não autoriza implementação, deploy, mainnet, fundos, secrets, custody ou signing.",
        "primary_attachment": {"path": "gate.pdf", "media_type": "application/pdf", "role": "primary", "designed_artifact": True, "fallback_renderer": False},
        "valid_replies": ["Aprovo", "Corrigir: ...", "Ainda falta: ..."],
        "approval_authorizes": ["seguir para método", "seguir para arquitetura"],
        "approval_does_not_authorize": ["implementação", "deploy", "mainnet", "fundos", "secrets", "custody", "signing"],
    }

    result = quality.validate_human_gate_artifact(package)

    assert result.quality_pass is True
    assert result.findings == []


def test_cli_returns_nonzero_for_shallow_product_sot(tmp_path):
    path = tmp_path / "shallow_sot.json"
    path.write_text(json.dumps({"scope_in": ["stake"], "scope_out": ["deploy"]}), encoding="utf-8")

    exit_code = quality.main(["product_sot", str(path), "--json"])

    assert exit_code == 1


def test_cli_returns_zero_for_designed_human_gate(tmp_path):
    path = tmp_path / "gate.json"
    path.write_text(
        json.dumps(
            {
                "primary_message": "Decisão pendente: aprovar Product SOT revisada. Aprovar libera só método/arquitetura e não libera implementação, deploy, mainnet, fundos, secrets, custody ou signing.",
                "primary_attachment": {"path": "gate.pdf", "media_type": "application/pdf", "designed_artifact": True, "fallback_renderer": False},
                "valid_replies": ["Aprovo", "Corrigir: ..."],
                "approval_authorizes": ["seguir para método"],
                "approval_does_not_authorize": ["implementação", "deploy", "mainnet", "fundos", "secrets", "custody", "signing"],
            }
        ),
        encoding="utf-8",
    )

    exit_code = quality.main(["human_gate", str(path), "--json"])

    assert exit_code == 0
