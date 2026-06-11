# Capability Packs

Capability packs answer one question before a paper becomes execution work:

```text
Do we have the right specialist coverage for this type of product?
```

The Factory must not pretend that one generic implementation agent can build
every kind of product well. A web app, a native mobile app, a game, a Solana
program, a fintech ledger and a hardware product need different proof, risk
controls and specialist executors.

## How It Works

Every Factory card names its surfaces, such as `frontend`, `api`, `solana`,
`game`, `ios`, `payment` or `hardware`.

`scripts/factoryctl.py validate-card` checks those surfaces against
`agents/capability-packs.public.json`.

The result is simple:

| Pack state | Meaning | Execution rule |
| --- | --- | --- |
| `core_ready` | The Factory already has enough workers, bindings and proof path for this area. | The card can continue to normal gates. |
| `pack_ready` | An optional pack has already been installed and proven. | The card can continue if the pack covers the surfaces. |
| `pack_template` | The Factory knows this area exists, but the executable specialists are not installed yet. | The card blocks until a `capability_pack_contract` activates the pack. |
| `blocked_until_installed` | The area is intentionally outside current execution coverage. | The card blocks until a dedicated pack is created and reviewed. |

## Ready Coverage

These packs are ready in the public Factory:

| Pack | Covers |
| --- | --- |
| `web-saas-core` | Web apps, SaaS, APIs, persistence, auth, integrations, tests, docs, release and monitoring. |
| `cloud-native-core` | CI/CD, runtime, deploy wiring, cloud security, observability and rollback planning. |
| `agent-runtime-core` | Hermes, Factory adapter, profiles, skills, tools, memory, MCP and agentic workflow changes. |
| `solana-quasar-core` | Quasar-first Solana/onchain program work, wallet transactions, signer boundaries and onchain QA. |

## Template Packs

These packs are recognized but not executable by default:

| Pack | Why it blocks |
| --- | --- |
| `mobile-app-pack` | Native mobile needs device lifecycle, app-store rules, simulator/device proof and mobile QA. |
| `desktop-app-pack` | Desktop needs packaging, OS permissions, installers, updates and desktop runtime proof. |
| `game-product-pack` | Games need gameplay design, runtime loop, assets, playtests and performance budgets. |
| `ai-ml-product-pack` | AI/ML needs model/data contracts, evals, drift checks and safety proof. |
| `fintech-payments-pack` | Money movement needs ledger invariants, reconciliation, fraud/compliance and human gates. |
| `regulated-domain-pack` | Legal, medical, insurance and similar products need domain and jurisdiction boundaries. |
| `data-analytics-pack` | Analytics needs metric contracts, data quality, lineage and dashboard correctness. |
| `browser-extension-pack` | Extensions need Manifest V3, permission review, content-script safety and packaging proof. |
| `hardware-iot-pack` | Hardware and IoT need device, firmware, safety and physical recovery evidence. |

## Activation Contract

A template pack becomes executable only when the card includes a
`capability_pack_contract` with:

- the pack id;
- `ready` or `activated` status;
- covered surfaces;
- specialist workers;
- activation evidence refs;
- missing capabilities, if any;
- an execution rule.

The template lives at `templates/capability-pack-contract.json`.

## Important Boundary

Capability packs do not replace worker packets, reviewers or gates. They run
before execution to decide whether the Factory is allowed to route the work at
all.

When a pack is not ready, the right behavior is to block, create the missing
specialist pack, evaluate it, bind it to Hermes and only then continue.

This is what keeps the Factory modular without pretending it has infinite
specialist competence.
