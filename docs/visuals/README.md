# Visuals

This directory contains public visual guides that help an external operator
understand Overkill Factory faster. These files are supporting docs; the root
README remains the primary product entrypoint.

## What Belongs Here

- Self-contained diagrams that explain the factory flow, gates, workers and
  operating boundaries.
- Public-safe visual summaries generated from current public contracts.

## What Does Not Belong Here

- Screenshots from private runs, local browser captures, raw extraction,
  private paths, board links, logs or execution evidence.
- Visuals that manually mirror only part of a registry without a validation
  check.

## Source Of Truth

Executable contracts remain authoritative:

- `agents/worker-registry.public.json`
- `agents/worker-profiles.public.json`
- `agents/hermes-profile-bindings.public.json`
- `docs/agents/factory-stage-agent-map.md`
- `scripts/factoryctl.py`, schemas and tests

The HTML visualizations explain those contracts; they do not replace them.

## Current Visuals

| File | Purpose |
| --- | --- |
| `overkill-factory-map-v0.1.0.png` | Real screenshot preview of the hosted interactive map for the GitHub README. |
| `overkill-factory-map-v0.1.0.html` | Interactive map of the production line, R0-R4 risk tiers and the 40 public factory agents. |
| `overkill-factory-map-v0.1.0.svg` | Legacy static diagram kept only as a secondary source asset. |

Hosted version:
https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v0.1.0.html

## Validation

Before publishing a visual, check:

```bash
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```

Then open the HTML in a browser and verify desktop, mobile, keyboard
navigation, no console errors and no private or project-specific text.
Verify that the PNG preview renders in the GitHub README and does not present
the visual as runtime evidence or source authority.
