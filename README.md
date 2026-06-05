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
- Example cards and Receipt Five metadata.
- A Codex skill for operating the factory.
- A roadmap for critical factory workers: Product Face, Codex Security,
  Solana/Quasar Auditor, independent reviewer, and R3/R4 human approval.

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

## Quick Start

Read these in order:

1. `docs/methodology/overkill-factory-v0.md`
2. `docs/planning/execution-plan.md`
3. `adapters/hermes/README.md`
4. `agents/worker-roster.md`
5. `docs/maps/factory-10-flow.mmd`

## License

MIT.
