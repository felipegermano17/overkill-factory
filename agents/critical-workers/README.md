# Critical Worker Cards

This folder contains human-readable cards for workers that can block the line,
protect authority, or prevent false completion.

It is not the full worker catalog. The full catalog is:

- `agents/worker-roster.md` for the human overview;
- `docs/agents/worker-profiles.md` for every public worker;
- `agents/worker-registry.public.json` for machine-readable process contracts;
- `agents/worker-profiles.public.json` for public agent profile contracts;
- `agents/hermes-profile-bindings.public.json` for Hermes routing.

## Why These Cards Exist

The JSON contracts are precise, but they are not pleasant reading. These cards
make the highest-risk workers understandable to a human reviewer without
weakening the machine contract.

Each card must explain:

- runtime identity;
- when the worker enters;
- required inputs;
- required result;
- blocking rule;
- refusal rule;
- evidence quality;
- handoff.

## Cards

| Card | Worker |
| --- | --- |
| `factory-orchestrator.md` | `factory-orchestrator` |
| `source-ledger-worker.md` | `source-ledger-worker` |
| `product-sot-planner.md` | `product-sot-planner` |
| `product-face-validator.md` | `product-face` |
| `security-orchestrator.md` | `security-orchestrator` |
| `codex-security-runner.md` | `codex-security` |
| `solana-quasar-auditor-runner.md` | `solana-quasar-auditor` |
| `independent-reviewer.md` | `independent-reviewer` |
| `human-gate-clerk.md` | `human-gate-clerk` |
| `evidence-reconciler.md` | `evidence-reconciler` |
| `release-ops-worker.md` | `release-ops-worker` |
| `public-safety-gate.md` | `public-safety-gate` |

## Boundary

These cards are guides. They do not grant runtime authority by themselves.
Executable behavior still comes from schemas, `factoryctl.py`, Hermes bindings,
adapter hooks, generated worker packets and tests.
