# Overkill Factory

Overkill Factory is an open product-production factory for autonomous agents.

It turns a messy product paper into a controlled production line:

```text
raw product paper
-> source resolution
-> Product SOT
-> architecture
-> specialist reviews
-> documentation OS
-> decomposition
-> Hermes Kanban cards
-> agent execution
-> evidence
-> independent review
-> human gates
-> stable release
```

The core belief is simple: autonomous agents do not need prettier prose. They
need contracts, gates, receipts, and a runtime that refuses weak work.

## What This Repository Contains

- The Overkill Factory methodology.
- Machine-checkable card and receipt contracts.
- Hermes/Kanban adapter patches.
- Example cards, worker packets, gate reports, and Receipt Five metadata.
- A Codex skill for operating the factory.
- Initial automation for critical factory workers: Product Face, Codex Security,
  Solana/Quasar Auditor, independent reviewer, and human gate clerk.

## Why Hermes Is Required

The first supported runtime is Hermes.

Hermes is the factory floor: the agents live there, the work moves through its
Kanban, and the gates block bad transitions before autonomous execution starts.

Overkill Factory stays separate from Hermes so the methodology remains its own
project, but the Hermes adapter is a first-class and required integration.

## Current Status

Factory 10 has been validated on a real Hermes/KAXIS VM.

The Hermes adapter patch has been committed on the VM in:

```text
branch: codex/kaxis-factory-10-gates
commit: d297c0c78900d6858384297895ef4392e6fb85b9
```

The portable patch is available at:

```text
adapters/hermes/patches/0001-add-kaxis-factory-10-kanban-gates.patch
```

The first dry pilot is complete:

```text
pilot: pilots/quasar-vault-guard-test
Hermes board: overkill-factory-pilot-10
Hermes task: t_a09d1c2e
status: done
```

Primary Whimsical map:

[Overkill Factory - Factory 10+ Fluxo Linear Legivel](https://whimsical.com/felipe-s-workspace2684/overkill-factory-factory-10-fluxo-linear-legivel-XVvfzkVyVEwiPMQM9TNP84)

## Quick Start

Read these in order:

1. `docs/methodology/overkill-factory-v0.md`
2. `docs/methodology/overkill-factory-v3-6.md`
3. `docs/planning/execution-plan.md`
4. `docs/automation/worker-automation-v0.md`
5. `adapters/hermes/README.md`
6. `agents/worker-roster.md`
7. `docs/maps/whimsical-board.md`
8. `pilots/quasar-vault-guard-test/README.md`

Run the local preflight:

```bash
python scripts/factoryctl.py validate-card examples/cards/v35_valid_product_face.md
python scripts/factoryctl.py gate-report --card examples/cards/v35_valid_onchain_auditor_scan.md
python scripts/factoryctl.py worker-packet --worker all --card examples/cards/v35_valid_onchain_auditor_scan.md --out examples/worker-packets/onchain-card
```

After a specialist really runs, write structured evidence metadata:

```bash
python scripts/factoryctl.py evidence-record --worker codex-security --card examples/cards/v35_valid_security_with_scan.md --result PASS --tool codex-security:security-scan --actor kaxis-cybersecurity --evidence-ref reports/security-scan.md
python scripts/factoryctl.py human-gate-record --card examples/cards/v35_valid_onchain_auditor_scan.md --decision approved --human-actor Felipe --evidence-ref decisions/r3-human-approval.md
```

## Current Boundaries

The repo prepares contracts and worker packets. It does not fake scanner output,
Auditor results, screenshots, independent approval, or human decisions.

The dry pilot proves the factory process and Hermes gates. It does not prove
production readiness, deploy readiness, real Quasar program safety, wallet
signing, devnet/mainnet behavior, funds movement, or custody safety.

The first production-intent pilot still needs a real raw product paper.

## License

MIT.
