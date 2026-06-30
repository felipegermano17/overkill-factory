#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping
import argparse
import json
import sys


@dataclass(frozen=True)
class QualityFinding:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class QualityResult:
    artifact_type: str
    process_pass: bool
    readback_pass: bool
    quality_pass: bool
    findings: list[QualityFinding] = field(default_factory=list)


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _nonempty(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (list, tuple, set, dict)):
        return len(value) > 0
    return True


def _count(value: Any) -> int:
    if isinstance(value, (list, tuple, set, dict)):
        return len(value)
    if isinstance(value, str):
        return 1 if value.strip() else 0
    return 1 if value is not None else 0


def _finding(code: str, message: str, severity: str = "error") -> QualityFinding:
    return QualityFinding(code=code, severity=severity, message=message)


def detect_lazy_output(text: str, artifact_type: str = "generic") -> list[QualityFinding]:
    """Detect deterministic signs of shallow/satisficing work.

    This intentionally uses simple, auditable heuristics. It is not an LLM judge.
    """
    lower = (text or "").lower()
    findings: list[QualityFinding] = []
    vague_markers = [
        "considerar",
        "avaliar posteriormente",
        "pode ser",
        "deve considerar",
        "a definir",
        "tbd",
        "todo",
    ]
    if len(lower.strip()) < 600:
        findings.append(_finding("too_short", f"{artifact_type} is too short to be decision-grade."))
    if sum(1 for marker in vague_markers if marker in lower) >= 2:
        findings.append(_finding("vague_language", f"{artifact_type} uses repeated vague/lazy language."))
    if "acceptance" not in lower and "critério" not in lower and "criterio" not in lower:
        findings.append(_finding("missing_acceptance_criteria", f"{artifact_type} has no acceptance criteria signal."))
    if "source" not in lower and "fonte" not in lower and "ref" not in lower:
        findings.append(_finding("missing_source_signal", f"{artifact_type} has no source traceability signal."))
    return findings


def validate_product_sot_prd_grade(sot: Mapping[str, Any] | str) -> QualityResult:
    """Validate that a Product SOT is PRD-grade, not a shallow scope summary."""
    findings: list[QualityFinding] = []
    process_pass = _nonempty(sot)
    readback_pass = process_pass

    if isinstance(sot, str):
        text = sot
        lower = sot.lower()
        required_text_signals = {
            "missing_product_intent": ["product intent", "intenção do produto", "intencao do produto"],
            "missing_source_traceability": ["source traceability", "rastreabilidade", "fonte"],
            "missing_user_journeys": ["user journey", "jornada do usuário", "jornada do usuario"],
            "missing_admin_journeys": ["admin journey", "jornada admin", "admin"],
            "missing_functional_requirements": ["functional requirement", "requisito funcional"],
            "missing_non_functional_requirements": ["non-functional", "não funcional", "nao funcional", "nfr"],
            "missing_state_model": ["state model", "modelo de estado"],
            "missing_data_ledger_reconciliation": ["reconciliation", "reconciliação", "reconciliacao", "ledger"],
            "missing_downstream_handoff": ["downstream handoff", "handoff", "arquitetura"],
        }
        for code, signals in required_text_signals.items():
            if not any(signal in lower for signal in signals):
                findings.append(_finding(code, f"Product SOT text lacks {code.replace('missing_', '').replace('_', ' ')}."))
        findings.extend(detect_lazy_output(text, "product_sot"))
    else:
        data = _as_mapping(sot)
        if not _nonempty(data.get("product_intent")):
            findings.append(_finding("missing_product_intent", "Product SOT must state product intent, not only scope."))
        if _count(data.get("source_traceability")) < 2:
            findings.append(_finding("missing_source_traceability", "Product SOT must map sources to requirements."))
        if _count(data.get("personas")) < 1:
            findings.append(_finding("missing_personas", "Product SOT must name product personas/operators."))
        if _count(data.get("user_journeys")) < 2:
            findings.append(_finding("missing_user_journeys", "Product SOT must include user journeys."))
        if _count(data.get("admin_journeys")) < 1:
            findings.append(_finding("missing_admin_journeys", "Product SOT must include admin/operator journeys."))
        if _count(data.get("functional_requirements")) < 3:
            findings.append(_finding("missing_functional_requirements", "Product SOT must include functional requirements."))
        if _count(data.get("non_functional_requirements")) < 2:
            findings.append(_finding("missing_non_functional_requirements", "Product SOT must include non-functional requirements."))
        if _count(data.get("state_model_requirements")) < 5:
            findings.append(_finding("missing_state_model", "Product SOT must include state model requirements."))
        if _count(data.get("data_ledger_reconciliation_requirements")) < 1:
            findings.append(_finding("missing_data_ledger_reconciliation", "Product SOT must include data/ledger/reconciliation requirements."))
        if _count(data.get("acceptance_criteria_by_flow")) < 2:
            findings.append(_finding("missing_acceptance_criteria", "Product SOT must include acceptance criteria by flow."))
        handoff = data.get("downstream_handoff")
        if not isinstance(handoff, Mapping) or not {"architecture", "ux", "security", "implementation", "qa"}.issubset(handoff.keys()):
            findings.append(_finding("missing_downstream_handoff", "Product SOT must hand off to architecture, UX, security, implementation, and QA."))

    quality_pass = process_pass and readback_pass and not [f for f in findings if f.severity == "error"]
    return QualityResult(
        artifact_type="product_sot",
        process_pass=process_pass,
        readback_pass=readback_pass,
        quality_pass=quality_pass,
        findings=findings,
    )


def validate_human_gate_artifact(package: Mapping[str, Any]) -> QualityResult:
    data = _as_mapping(package)
    findings: list[QualityFinding] = []
    process_pass = _nonempty(data.get("primary_message")) and _nonempty(data.get("valid_replies"))
    readback_pass = process_pass

    attachment = _as_mapping(data.get("primary_attachment"))
    media_type = str(attachment.get("media_type", "")).lower()
    path = str(attachment.get("path", "")).lower()
    if media_type == "application/json" or path.endswith(".json"):
        findings.append(_finding("primary_attachment_json", "Raw JSON cannot be the primary human gate attachment."))
    if media_type == "application/pdf" or path.endswith(".pdf"):
        if attachment.get("fallback_renderer") is True:
            findings.append(_finding("fallback_pdf_primary", "Fallback text-style PDF cannot be the primary normal gate artifact."))
        if attachment.get("designed_artifact") is not True:
            findings.append(_finding("primary_pdf_not_marked_designed", "Primary PDF must be marked/proven as designed operator artifact."))
    elif not findings:
        findings.append(_finding("unsupported_primary_attachment", "Primary gate attachment must be designed PDF/equivalent, not a technical dump."))

    message = str(data.get("primary_message", ""))
    if len(message.strip()) < 80:
        findings.append(_finding("primary_message_too_short", "Gate message must state the decision and consequence."))
    if _count(data.get("approval_does_not_authorize")) < 4:
        findings.append(_finding("missing_non_authorization_boundary", "Gate must state what approval does not authorize."))
    if _count(data.get("approval_authorizes")) < 1:
        findings.append(_finding("missing_authorization_boundary", "Gate must state exactly what approval authorizes."))

    quality_pass = process_pass and readback_pass and not [f for f in findings if f.severity == "error"]
    return QualityResult("human_gate_artifact", process_pass, readback_pass, quality_pass, findings)


def validate_completion_readback(completion: Mapping[str, Any], root: str | Path) -> QualityResult:
    data = _as_mapping(completion)
    base = Path(root)
    findings: list[QualityFinding] = []
    artifact_paths = data.get("artifact_paths", []) or []
    process_pass = _nonempty(data)

    for item in artifact_paths:
        p = Path(str(item))
        candidate = p if p.is_absolute() else base / p
        if not candidate.exists():
            findings.append(_finding("claimed_artifact_missing", f"Claimed artifact does not exist: {item}"))

    readback_pass = not findings
    quality_pass = process_pass and readback_pass
    return QualityResult("completion_readback", process_pass, readback_pass, quality_pass, findings)


def can_promote(result: QualityResult | Iterable[QualityResult]) -> bool:
    if isinstance(result, QualityResult):
        results = [result]
    else:
        results = list(result)
    return bool(results) and all(r.process_pass and r.readback_pass and r.quality_pass for r in results)


def result_to_dict(result: QualityResult) -> dict[str, Any]:
    return {
        "artifact_type": result.artifact_type,
        "process_pass": result.process_pass,
        "readback_pass": result.readback_pass,
        "quality_pass": result.quality_pass,
        "findings": [finding.__dict__ for finding in result.findings],
    }


def load_artifact(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    return text


def validate_artifact(artifact_type: str, path: Path, *, root: Path | None = None) -> QualityResult:
    payload = load_artifact(path)
    if artifact_type == "product_sot":
        return validate_product_sot_prd_grade(payload)
    if artifact_type == "human_gate":
        if not isinstance(payload, Mapping):
            return QualityResult(
                "human_gate_artifact",
                process_pass=False,
                readback_pass=True,
                quality_pass=False,
                findings=[_finding("invalid_human_gate_payload", "Human gate artifact must be a JSON object/package.")],
            )
        return validate_human_gate_artifact(payload)
    if artifact_type == "completion_readback":
        if not isinstance(payload, Mapping):
            return QualityResult(
                "completion_readback",
                process_pass=False,
                readback_pass=False,
                quality_pass=False,
                findings=[_finding("invalid_completion_payload", "Completion readback input must be a JSON object.")],
            )
        return validate_completion_readback(payload, root or path.parent)
    raise ValueError(f"unsupported artifact_type: {artifact_type}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate Overkill Factory work-product quality floor.")
    parser.add_argument("artifact_type", choices=["product_sot", "human_gate", "completion_readback"])
    parser.add_argument("path", type=Path)
    parser.add_argument("--root", type=Path, help="Root directory for completion readback artifact paths")
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = validate_artifact(args.artifact_type, args.path, root=args.root)
    payload = result_to_dict(result)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(f"{result.artifact_type}: quality_pass={result.quality_pass} process_pass={result.process_pass} readback_pass={result.readback_pass}")
        for finding in result.findings:
            print(f"{finding.severity}: {finding.code}: {finding.message}")
    return 0 if result.quality_pass else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
