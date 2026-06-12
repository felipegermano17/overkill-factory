# Live Hermes Kanban Smoke

> Document status: HISTORICAL EVIDENCE.
> Current authority: `scripts/factoryctl.py` and `docs/validation/canonical-real-infra-audit.md`.
> Runtime boundary: This is not the current factory rule; it records one live Hermes smoke and does not prove future runtime compatibility.

Date: 2026-06-06

This smoke ran the Overkill Factory adapter against a real Hermes Kanban board.
It used a synthetic Solana/Quasar R3 card so the repository can publish the
evidence without exposing private product material.

## What Was Proven

- The live adapter created a real main Kanban card.
- It created 12 required specialist worker cards.
- It linked every worker card as a dependency of the main card.
- The done transition blocked when worker results were missing.
- The done transition passed when all 12 worker result records were present and valid.
- The main card reached `done` only after the worker dependencies were completed.

## Evidence

- `validation/hermes-live/live-smoke-summary.md`
- `validation/hermes-live/materialize-solana-r3.json`
- `validation/hermes-live/enforce-done-missing-results.json`
- `validation/hermes-live/enforce-done-pass.json`
- `validation/hermes-live/worker-results/`

## Boundary

The worker results are smoke evidence. They prove orchestration and
reconciliation, not real security, Quasar, release or human approval quality.
Real product work must replace them with real worker execution evidence.
