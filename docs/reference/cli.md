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
factoryctl unblock-plan --card examples/minimal-hermes-project/card.md
factoryctl worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
factoryctl transition-plan --card examples/minimal-hermes-project/card.md --from-status draft --to-status ready
```

### Test Runner Fallback

Worker packets should run commands as argv lists, not shell strings. Use
`scripts/safe_shell.py` as the local pattern when a packet needs a fallback for
runner failures, timeouts, or Windows sandbox launch errors. A fallback result
is `BLOCKED` until the same argv is rerun successfully or replaced by a
traceable worker result.

## Maintainer Scripts

Scripts outside `factoryctl` are maintainer tools or compatibility entrypoints.
Promote repeated operator flows into `factoryctl` instead of adding another
script name to the public path.

### `scripts/factory_self_improvement.py`

Creates dry-run self-improvement artifacts for maintainers:

```bash
python scripts/factory_self_improvement.py reference-registry --out .tmp/reference-source-registry.json
python scripts/factory_self_improvement.py missing-capability-plan --gate-report .tmp/gate-report.json --out .tmp/missing-capability-plan.json
python scripts/factory_self_improvement.py learnback-issues --record .tmp/execution-learnback-record.json --out .tmp/issue-candidates.json
python scripts/factory_self_improvement.py issue-intake --config templates/owner-issue-intake-config.json --issues .tmp/issues.json --out .tmp/issue-intake-report.json
python scripts/factory_self_improvement.py governance-audit --out .tmp/ai-codebase-governance-report.json
```

These commands do not dispatch Hermes, activate workers, post GitHub comments or
approve gates. They prepare public-safe plans and candidates for review.
