#!/usr/bin/env python3
"""Create a reviewable learnback proposal; never silently mutates the factory."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_proposal() -> dict:
    return {
        "record_type": "factory_learnback_proposal",
        "result": "PASS",
        "mutation_mode": "proposal_only",
        "silent_mutation_allowed": False,
        "review_required": True,
        "proposal_id": "learnback-v3-master-plan-literal-dod",
        "observed_gap": "Literal Definition of Done needs explicit external-live gates, not only local audit pass.",
        "proposed_change": "Keep local support green while reporting Telegram/manager live proof as external-live pending until verified.",
        "affected_surfaces": ["factoryctl", "manager profile", "operator progress", "release readiness"],
        "required_reviewers": ["factory-orchestrator", "overkill-factory-gerente"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(".tmp/factory-learnback-proposal.json"))
    args = parser.parse_args()
    record = build_proposal()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(record["result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
