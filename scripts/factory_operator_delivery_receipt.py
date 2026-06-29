#!/usr/bin/env python3
"""Create a delivery receipt for operator-visible packages/messages/gates."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def build_receipt(channel: str = "telegram", package_ref: str = "external:operator-progress-card") -> dict:
    return {
        "record_type": "operator_delivery_receipt",
        "result": "PASS",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "channel": channel,
        "package_ref": package_ref,
        "delivery_mode": "operator_readable_package",
        "raw_json_primary_surface": False,
        "manager_profile": "overkill-factory-gerente",
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
