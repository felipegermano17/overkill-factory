# CLI Reference

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: scripts/factoryctl.py, README.md, tests/
> Runtime boundary: The CLI creates and validates local artifacts. Hermes remains
> the runtime source of truth for real cards and transitions.

## Operator Commands

### `factoryctl doctor`

Checks local install health, package metadata, public entrypoints, the minimal
example and whether Hermes runtime checking is configured. It does not claim a
real Hermes E2E harness.

```bash
factoryctl doctor
factoryctl doctor --json
```

### `factoryctl run minimal`

Runs the public first-value path through the single CLI entrypoint.

```bash
factoryctl run minimal
factoryctl run minimal --out .tmp/quickstart-result.json --packets-out .tmp/minimal-worker-packets
```

### `factoryctl init`

Creates a Hermes-friendly operator workspace for a product.

```bash
factoryctl init --out ../my-product-factory --project-name my-product
```

## Card And Worker Commands

```bash
factoryctl validate-card examples/minimal-hermes-project/card.md
factoryctl gate-report --card examples/minimal-hermes-project/card.md
factoryctl worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
factoryctl transition-plan --card examples/minimal-hermes-project/card.md --from-status draft --to-status ready
```

## Maintainer Scripts

Scripts outside `factoryctl` are maintainer tools or compatibility entrypoints.
Promote repeated operator flows into `factoryctl` instead of adding another
script name to the public path.
