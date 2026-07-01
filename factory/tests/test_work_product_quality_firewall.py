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
        "product": "Product Alpha V1",
        "scope_in": ["stablecoin subscription", "signup", "admin"],
        "scope_out": ["instant payment rail", "mobile"],
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
        "product_intent": "Product Alpha V1 delivers a global web subscription product with complex payment and operations flows.",
        "source_traceability": [
            {"source_ref": "brief#flow-v6", "requirement_ids": ["REQ-UX-001", "REQ-SUB-001"]},
            {"source_ref": "legacy-app#repo-study", "requirement_ids": ["REQ-ARCH-001"]},
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
        "examples_by_flow": {
            "cadastro": ["Example: referral code expired -> user sees blocked state and support path."],
            "stake": ["Example: wallet event exists but DB row missing -> reconciliation divergence state."],
        },
        "tradeoffs": [
            {"decision": "Use explicit reconciliation state", "cost": "More admin UX", "benefit": "Safer operator recovery"},
            {"decision": "Separate claim from release", "cost": "More gate work", "benefit": "Prevents accidental production authority"},
        ],
        "rejected_alternatives": [
            {"alternative": "Treat payment success as product readiness", "reason": "Hides ledger/onchain divergence"},
        ],
        "failure_empty_blocked_states": ["empty portfolio", "payment error", "admin review blocked"],
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


def test_generic_product_sot_with_counts_but_no_excellence_depth_fails_quality():
    sot = {
        "record_type": "product_sot_candidate",
        "product_intent": "Build a useful DeFi product with onboarding, payments, dashboard, and admin operations.",
        "source_traceability": [
            {"source_ref": "chat#1", "requirement_ids": ["REQ-001"]},
            {"source_ref": "issue#595", "requirement_ids": ["REQ-002"]},
        ],
        "personas": ["user", "admin"],
        "user_journeys": [{"id": "UJ-1"}, {"id": "UJ-2"}],
        "admin_journeys": [{"id": "AJ-1"}],
        "functional_requirements": [{"id": "F1"}, {"id": "F2"}, {"id": "F3"}],
        "non_functional_requirements": [{"id": "N1"}, {"id": "N2"}],
        "state_model_requirements": ["start", "middle", "done", "pending", "review"],
        "data_ledger_reconciliation_requirements": ["reconcile data"],
        "acceptance_criteria_by_flow": {"flow1": ["works"], "flow2": ["works"]},
        "downstream_handoff": {
            "architecture": [],
            "ux": [],
            "security": [],
            "implementation": [],
            "qa": [],
        },
    }

    result = quality.validate_product_sot_prd_grade(sot)

    assert result.process_pass is True
    assert result.readback_pass is True
    assert result.quality_pass is False
    codes = {finding.code for finding in result.findings}
    assert "missing_examples" in codes
    assert "missing_tradeoffs" in codes
    assert "missing_rejected_alternatives" in codes
    assert "missing_failure_states" in codes
    assert quality.can_promote(result) is False


def test_quality_firewall_refuses_process_pass_without_quality_pass():
    result = quality.QualityResult(
        artifact_type="product_sot",
        process_pass=True,
        readback_pass=True,
        quality_pass=False,
        findings=[quality.QualityFinding("too_shallow", "error", "Artifact is shallow")],
    )

    assert quality.can_promote(result) is False


def test_real_effectiveness_refuses_comment_done_receipt_and_phase_rituals():
    proof = {
        "record_type": "real_effectiveness_proof",
        "effect_type": "process_ritual",
        "claim": "Posted a comment, wrote Receipt Five, marked the phase done, and advanced the card.",
        "ritual_refs": ["comment:kanban-update", "receipt_five", "kanban_transition_event"],
        "evidence_refs": ["comment:kanban-update"],
    }

    result = quality.validate_real_effectiveness_proof(proof)

    assert result.process_pass is True
    assert result.quality_pass is False
    codes = {finding.code for finding in result.findings}
    assert "process_ritual_not_material_progress" in codes
    assert "missing_material_evidence" in codes


def test_real_effectiveness_accepts_usable_artifact_with_validation():
    proof = {
        "record_type": "real_effectiveness_proof",
        "effect_type": "usable_artifact",
        "claim": "Generated the operator PDF decision package and validated it against the delivery profile.",
        "artifact_refs": ["reports/operator-decision-package.pdf"],
        "evidence_refs": ["reports/operator-decision-package.pdf", "reports/operator-decision-package.validation.json"],
        "validation_refs": ["pytest factory/tests/test_operator_experience.py"],
        "operator_or_product_impact": "Operator can make the Product SOT gate decision without opening raw Kanban or JSON.",
    }

    result = quality.validate_real_effectiveness_proof(proof)

    assert result.process_pass is True
    assert result.readback_pass is True
    assert result.quality_pass is True
    assert result.findings == []


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
        "record_type": "human_gate_package",
        "primary_message": "Decisão pendente: aprovar Product SOT revisada. Se aprovar, segue para método/arquitetura. Aprovar não autoriza implementação, deploy, mainnet, fundos, secrets, custody ou signing.",
        "primary_attachment": {"path": "gate.pdf", "media_type": "application/pdf", "role": "primary", "designed_artifact": True, "fallback_renderer": False},
        "valid_replies": ["Aprovo", "Corrigir: ...", "Ainda falta: ..."],
        "approval_authorizes": ["seguir para método", "seguir para arquitetura"],
        "approval_does_not_authorize": ["implementação", "deploy", "mainnet", "fundos", "secrets", "custody", "signing"],
    }

    result = quality.validate_human_gate_artifact(package)

    assert result.quality_pass is True
    assert result.findings == []


def test_operator_delivery_receipt_pdf_video_first_template_passes_quality():
    receipt = json.loads((ROOT / "templates" / "operator-delivery-receipt.json").read_text(encoding="utf-8"))

    result = quality.validate_human_gate_artifact(receipt)

    assert result.quality_pass is True
    assert result.findings == []


def test_operator_delivery_receipt_rejects_direct_watchdog_and_raw_markdown_primary():
    receipt = {
        "record_type": "operator_delivery_receipt",
        "manager_profile": "watchdog",
        "delivery_path": "watchdog_to_human",
        "direct_worker_or_watchdog_to_human": True,
        "primary_message": "Decisão pendente: leia o anexo antes de aprovar. Esta aprovação não libera implementação, deploy, Mainnet, fundos, secrets, custody ou signing.",
        "primary_artifact": {"kind": "markdown_document", "media_type": "text/markdown", "asset_ref": "gate.md", "designed_artifact": False, "fallback_renderer": True},
        "internal_evidence_refs": [],
        "material_delivered_before_question": False,
        "raw_json_markdown_primary_surface": True,
    }

    result = quality.validate_human_gate_artifact(receipt)

    assert result.quality_pass is False
    codes = {finding.code for finding in result.findings}
    assert "primary_attachment_markdown" in codes
    assert "missing_manager_delivery" in codes
    assert "invalid_delivery_path" in codes
    assert "direct_internal_signal_to_human" in codes
    assert "raw_json_markdown_primary_surface" in codes


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
