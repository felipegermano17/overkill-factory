#!/usr/bin/env python3
"""Create a delivery receipt for operator-visible packages/messages/gates."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def build_receipt(channel: str = "telegram", package_ref: str = "external:operator-progress-card") -> dict:
    return {
        "$schema": "https://overkill-factory.dev/schemas/operator-delivery-receipt.schema.json",
        "record_type": "operator_delivery_receipt",
        "delivery_id": "operator-delivery-receipt-runtime-sample",
        "result": "PASS",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manager_profile": "overkill-factory-gerente",
        "operator_channel": channel,
        "primary_language": "pt-BR",
        "decision_id": "status-or-gate-delivery",
        "package_refs": [package_ref, "templates/operator-briefing-package.json", "templates/approval-request.json"],
        "primary_message": (
            "Decisão pendente, se houver: leia o PDF anexado antes de aprovar, rejeitar ou pedir ajuste. "
            "Esta entrega não libera implementação, deploy, Mainnet, fundos, secrets, custódia ou signing."
        ),
        "primary_artifact": {
            "kind": "pdf_document",
            "media_type": "application/pdf",
            "asset_ref": "reports/operator-package/briefing.pdf",
            "designed_artifact": True,
            "fallback_renderer": False,
        },
        "optional_explainers": [
            {
                "kind": "video_explainer",
                "media_type": "video/mp4",
                "asset_ref": "reports/operator-package/explainer.mp4",
                "required_for_operator_decision": False,
            }
        ],
        "internal_evidence_refs": ["reports/operator-package/manifest.json", "reports/operator-package/briefing.md"],
        "material_delivered_before_question": True,
        "receipt_status": "delivered",
        "question_ref": f"{package_ref}#question",
        "raw_json_markdown_primary_surface": False,
        "delivery_path": "gerente_to_human",
        "direct_worker_or_watchdog_to_human": False,
        "delivery_mode": "operator_readable_package",
        "raw_json_primary_surface": False,
        "worker_direct_contact": False,
        "receipt_scope": ["message", "package", "gate"],
        "readback_required": True,
        "public_safe": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--channel", default="telegram")
    parser.add_argument("--package-ref", default="external:operator-progress-card")
    parser.add_argument("--out", type=Path, default=Path(".tmp/operator-delivery-receipt.json"))
    args = parser.parse_args()
    record = build_receipt(args.channel, args.package_ref)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(record["result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
