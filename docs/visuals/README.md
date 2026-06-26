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

## Version Boundary

The current public map is `v1.0.3`. That is the visual surface version, not the
repository release tag. The map is an explanation layer. The authoritative
contracts for Solana AI Kit routing, the Codex Bridge plugin, Solana/on-chain R4
gate hardening, project design-system / `DESIGN.md`, Hermes update/no-idle
controls and Fast Autonomy Lane live in schemas, templates, registries, docs and
tests.

For Solana work, capability packs, `input_contract.surface_router`,
`domain_brain_provider` and `solana_ai_kit_usage_receipt` are authoritative.
Legacy worker IDs that still contain product-specific labels are stable public
routing IDs only; they do not mean the old provider is still the Solana brain.

For bridge operation, the map's control/operator nodes are conceptual. The
plugin install path, hook trust boundary and durable inbox behavior are defined
in `docs/operator/overkill-factory-bridge.md` and
`docs/operator/overkill-factory-bridge-plugin.md`.

## Current Visuals

| File | Purpose |
| --- | --- |
| `overkill-factory-map-v1.0.3.svg` | Static README preview of the factory line and public boundary. |
| `overkill-factory-map-v1.0.3.html` | Interactive map of the production line, R0-R4 risk tiers and the 40 public factory agents. |

## Validation

Before publishing a visual, check:

```bash
python scripts/validate_public_json_artifacts.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```

Then open the HTML in a browser and verify desktop, mobile, keyboard
navigation, no console errors and no private or project-specific text.
Verify that the SVG preview renders in the GitHub README and does not present
the visual as runtime evidence or source authority.
