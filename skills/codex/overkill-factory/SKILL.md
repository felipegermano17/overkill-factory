---
name: overkill-factory
description: Operate the Overkill Factory product-production line. Use when turning raw product papers into Product SOT, architecture, Product Face, security/onchain review, Hermes Kanban cards, agent execution, Receipt Five evidence, human gates, pilots, or Factory VNext methodology updates.
---

# Overkill Factory

Overkill Factory is a gated product-production line for autonomous agents.
Use Hermes Kanban as the primary runtime unless the user explicitly selects a
different runtime.

## First Move

1. Identify the current factory phase: source, SOT, architecture, Product Face,
   review, decomposition, execution, verification, promotion, pilot, or VNext.
2. Separate source facts from inference and decisions.
3. If Hermes/KAXIS state matters, use the `hermes-kanban` skill and inspect the
   real VM/board before mutating anything.
4. Do not promote work from planning to execution without the matching gate.

## Factory Spine

Use this sequence:

```text
source intake -> source resolution -> Product SOT -> alignment questions
-> architecture -> Product Face -> specialist reviews -> onchain package
-> security scan plan -> human architecture gate -> documentation OS
-> decomposition -> Hermes cards -> execution -> verification
-> independent review -> human R3/R4 gate -> promotion -> monitoring
-> learning loop
```

## Required Contracts

For Factory 10 / KAXIS V3.5 cards, require:

- `factory_method_version`
- `phase`
- `surfaces`
- `risk_initial`
- `risk_effective`
- `authority_max`
- `owner_worker`
- `executor_identity`
- `reviewer_identity`
- `runtime_contract`
- `security_contract`
- `forbidden_actions`
- `done_definition`
- `kanban_transition_event_ref`

Block or revise cards when:

- Product Face surfaces lack a Product Face Packet.
- Onchain/Solana/Quasar work lacks an Onchain Work Package.
- R3/R4 onchain work lacks Auditor or human waiver.
- R3/R4/security/onchain work lacks a Codex Security/Cybersecurity scan packet.
- Executor and reviewer are the same identity.
- R4 lacks explicit human gate, rollback, risk owner, and security owner.
- Done lacks Receipt Five and transition-event metadata.

## References

Load only what is needed:

- `references/factory-line.md` for the full phase model and gates.
- `references/hermes-adapter.md` for Hermes/Kanban coupling and patch status.
- `references/card-contract.md` for card and Receipt Five field rules.

## Scripts

Use `scripts/validate_factory_contract.py` to sanity-check a card or receipt
JSON file outside Hermes:

```bash
python scripts/validate_factory_contract.py path/to/card.json
python scripts/validate_factory_contract.py path/to/receipt.json --receipt
```

This script is a lightweight preflight. Hermes gates remain authoritative when
running on the Hermes adapter.

## Operating Rules

- Prefer one operational artifact over scattered notes.
- Explain why a proposed gate or worker is better than the alternative.
- Treat old KAXIS methodology as evidence, not as truth by default.
- For Solana/KAXIS program work, prefer Quasar and require the Auditor path.
- For security-sensitive work, make Codex Security/Cybersecurity timing explicit.
- Keep R3/R4 human authority explicit; never fake approval records.
- Before saying "done", show evidence, tests, state, and remaining risk.
