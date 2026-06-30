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

- `factory/agents/worker-registry.public.json`
- `factory/agents/worker-profiles.public.json`
- `factory/agents/hermes-profile-bindings.public.json`
- `docs/agents/factory-stage-agent-map.md`
- `factory/scripts/factoryctl.py`, schemas and tests

The HTML visualizations explain those contracts; they do not replace them.

## Version Boundary

The current public map file remains `v1.0.3` to preserve the published URL, but
the content now explains Factory V3. The map is an explanation layer. The
authoritative contracts for Solana AI Kit routing, Solana/on-chain R4 gate
hardening, project design-system / `DESIGN.md`, Hermes update/no-idle controls
and Fast Autonomy Lane live in schemas, templates, registries, docs and tests.

For Solana work, capability packs, `input_contract.surface_router`,
`domain_brain_provider` and `solana_ai_kit_usage_receipt` are authoritative.
Legacy worker IDs that still contain product-specific labels are stable public
routing IDs only; they do not mean the old provider is still the Solana brain.

For operator start routing, the map's control/operator nodes are conceptual.
The durable inbox and start-request contract are defined in
`docs/operator/overkill-factory-bridge.md`.

## Current Visuals

| File | Purpose |
| --- | --- |
| `overkill-factory-map-v1.0.3.svg` | Static README preview of the factory line and public boundary. |
| `overkill-factory-map-v1.0.3.html` | Simple V3 public map for non-technical operators: how the factory routes work, what Hermes owns and why evidence gates matter. |

## Validation

Before publishing a visual, check:

```bash
python factory/scripts/validate_public_json_artifacts.py
python factory/scripts/public_safety_scan.py
python factory/scripts/secret_safety_scan.py
```

Then open the HTML in a browser and verify desktop, mobile, keyboard
navigation, no console errors and no private or project-specific text.
Verify that the SVG preview renders in the GitHub README and does not present
the visual as runtime evidence or source authority.
