# Factory 12 Agent Profile Smoke

Date: 2026-06-06

## Scope

This artifact records public-safe evidence for the Hermes-bound agent profiles
used by the factory worker layer.

It proves profile operability only. It does not approve a product, release,
security waiver, onchain audit or human gate.

Machine-readable smoke:

- `validation/hermes-live/factory12-agent-profile-smoke.json`

## Required Checks

For each profile:

- profile exists;
- `profile.yaml` exists;
- `SOUL.md` exists;
- profile description is not a bare name;
- required public worker profile exists;
- required binding exists;
- binding result schema exists;
- binding queue policy points to `factoryctl.worker_queue_class`;
- profile output can be represented as a bounded worker packet.

## Current Status

PASS: 37/37 profiles passed the public-safe structural smoke after the Factory
13 builder-layer patch.

## Smoke Result

| Worker id | Status |
|---|---|
| `factory-orchestrator` | PASS |
| `source-ledger-worker` | PASS |
| `product-sot-planner` | PASS |
| `product-architect` | PASS |
| `product-face` | PASS |
| `solana-quasar-auditor` | PASS |
| `codex-security` | PASS |
| `appsec-owasp-specialist` | PASS |
| `agentic-ai-security-specialist` | PASS |
| `autoreview-gate` | PASS |
| `remote-proof-runner` | PASS |
| `handoff-packer` | PASS |
| `independent-reviewer` | PASS |
| `human-gate-clerk` | PASS |
| `docs-os-worker` | PASS |
| `decomposition-planner` | PASS |
| `implementation-worker` | PASS |
| `frontend-builder` | PASS |
| `backend-api-builder` | PASS |
| `data-persistence-builder` | PASS |
| `solana-quasar-builder` | PASS |
| `solana-quasar-qa-engineer` | PASS |
| `wallet-transaction-builder` | PASS |
| `integration-builder` | PASS |
| `test-automation-builder` | PASS |
| `infra-devops-builder` | PASS |
| `agent-runtime-builder` | PASS |
| `qa-verification-worker` | PASS |
| `security-orchestrator` | PASS |
| `cloud-infra-security-specialist` | PASS |
| `crypto-key-management-specialist` | PASS |
| `release-ops-worker` | PASS |
| `memory-steward` | PASS |
| `skill-eval-distiller` | PASS |
| `public-safety-gate` | PASS |
| `supply-chain-gate` | PASS |
| `detection-monitoring-worker` | PASS |

## What Passed

- profile directory exists;
- `profile.yaml` exists;
- `SOUL.md` exists;
- profile description is not a bare name;
- identity and authority sections exist;
- public worker profile exists;
- public Hermes binding exists;
- queue source points to `factoryctl.worker_queue_class`;
- result schema is present in the profile contract;
- required skill refs include `overkill-factory` and `hermes-kanban`;
- security-critical profiles include domain and waiver contracts.

## Boundary

This is not product execution proof. It confirms the Hermes-bound agent profile
layer is present, contract-shaped and ready to receive worker packets. Product
proof still requires a card-specific run through the factory.
