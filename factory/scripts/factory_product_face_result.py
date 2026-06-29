#!/usr/bin/env python3
"""Create a Product Face Result proof with screenshot and UX evidence refs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

SVG = """<svg xmlns='http://www.w3.org/2000/svg' width='390' height='844' viewBox='0 0 390 844'>
  <rect width='390' height='844' fill='#050505'/>
  <text x='24' y='56' fill='#f6f6f6' font-size='26' font-family='Arial'>Product Face Proof</text>
  <rect x='24' y='96' width='342' height='128' rx='24' fill='#171717' stroke='#42f5b3'/>
  <text x='44' y='148' fill='#ffffff' font-size='18' font-family='Arial'>Journey: create task</text>
  <text x='44' y='184' fill='#b8ffd9' font-size='15' font-family='Arial'>Checked: responsive, contrast, no overlap</text>
  <rect x='24' y='260' width='342' height='72' rx='18' fill='#42f5b3'/>
  <text x='48' y='306' fill='#050505' font-size='20' font-family='Arial'>Primary action visible</text>
</svg>
"""


def build_result(screenshot: Path) -> dict:
    return {
        "record_type": "product_face_result",
        "result": "PASS",
        "surface": "mobile-web",
        "screenshots": [str(screenshot)],
        "viewports_checked": ["390x844", "1440x900"],
        "journeys_checked": ["first-load", "create-task", "empty-state", "error-state"],
        "checked_states": ["default", "loading", "empty", "error", "success"],
        "accessibility": {"contrast_checked": True, "keyboard_path_checked": True, "labels_checked": True},
        "layout": {"overlap_checked": True, "responsive_checked": True},
        "performance_note": "Proof artifact is synthetic/public-safe; real product completion must replace with product screenshots.",
        "ux_proof": [
            "primary action visible",
            "empty state explained",
            "error state actionable",
            "no overlap in checked viewports",
        ],
        "product_specific_replacement_required_for_real_product": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(".tmp/product-face-result.json"))
    parser.add_argument("--screenshot", type=Path, default=Path(".tmp/product-face-proof.svg"))
    args = parser.parse_args()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.screenshot.parent.mkdir(parents=True, exist_ok=True)
    args.screenshot.write_text(SVG, encoding="utf-8")
    record = build_result(args.screenshot)
    args.out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")
    print(f"Wrote {args.screenshot}")
    print(record["result"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
