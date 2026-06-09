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
3. If Hermes/Overkill state matters, use the `hermes-kanban` skill and inspect
   the real Hermes runtime/board before mutating anything.
4. Do not promote work from planning to execution without the matching gate.
5. For external research, check existing local artifacts/source ledgers before
   recapturing browser or social content.
6. Do not put raw study extraction, screenshots, private ledgers, local paths,
   private links or internal product names into the public factory repository.

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

For Factory 10 / Overkill V3.5 cards, require:

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

## Validation Standard

A factory test only counts as a real test when Hermes runs the production line
through durable Kanban state: board, card, assigned profile, run log, worker
result, Receipt Five evidence and gate transition. Local scripts, chat
simulation and dry runs are preflight support only; they can prepare or debug the
factory, but they cannot be reported as end-to-end production-line validation.

Block or revise cards when:

- Product Face surfaces lack a Product Face Packet.
- Onchain/Solana/Quasar work lacks an Onchain Work Package.
- R3/R4 onchain work lacks Auditor or human waiver.
- R3/R4/security/onchain work lacks a Codex Security/Cybersecurity scan packet.
- Executor and reviewer are the same identity.
- R4 lacks explicit human gate, rollback, risk owner, and security owner.
- Done lacks Receipt Five and transition-event metadata.
- Public artifacts contain private paths, internal names, raw source extraction
  or private workspace links.
- Hermes updates have not passed compatibility manifest, update runbook,
  disposable smoke and rollback planning.

## References

Load only what is needed:

- `references/factory-line.md` for the full phase model and gates.
- `references/hermes-adapter.md` for Hermes/Kanban coupling and patch status.
- `references/card-contract.md` for card and Receipt Five field rules.
- `references/automation.md` for critical worker packets and `factoryctl.py`.
- `agents/worker-profiles.public.json` and
  `agents/hermes-profile-bindings.public.json` before changing worker profiles
  or dispatch behavior.

## Scripts

When inside the `overkill-factory` repository, prefer the repo-level
`scripts/factoryctl.py`:

```bash
python scripts/factoryctl.py gate-report --card path/to/card.md
python scripts/factoryctl.py worker-packet --worker all --card path/to/card.md --out path/to/output-dir
python scripts/validate_worker_profiles.py
```

Use `scripts/validate_factory_contract.py` to sanity-check a card or receipt
JSON file outside Hermes or outside the repo:

```bash
python scripts/validate_factory_contract.py path/to/card.json
python scripts/validate_factory_contract.py path/to/receipt.json --receipt
```

This script is a lightweight preflight. Hermes gates remain authoritative when
running on the Hermes adapter.

## Operating Rules

- Prefer one operational artifact over scattered notes.
- Explain why a proposed gate or worker is better than the alternative.
- Treat older methodology notes as evidence, not as truth by default.
- For Solana/Quasar program work, prefer Quasar and require the Auditor path.
- For security-sensitive work, make Codex Security/Cybersecurity timing explicit.
- Security is a specialist matrix: AppSec/OWASP, agentic AI, cloud/IaC,
  secrets/keys, supply chain, detection/monitoring, privacy/data and
  Solana/Quasar all need the right worker.
- Use open specialists for exploration and closed specialists only after
  repetition, predictable input and verifiable output.
- AutoReview is pre-landing evidence, not approval.
- Handoff is a replayable state packet, not a pretty summary.
- Remote proof uses Crabbox/Testbox/container only when local proof is
  insufficient and must include TTL, cost, cleanup and artifact evidence.
- Worker packets must not leak local absolute paths. Repo-local source cards use
  relative paths; external/private cards use redacted `external:<name>` refs.
- Worker packets must carry `profile_binding` so Hermes can dispatch to a real
  profile with skill refs, result schema and evidence policy.
- Do not treat a worker name as an agent configuration. Agent configuration
  lives in the worker profile and Hermes binding.
- Product Face Packet is planning; `product_face_result` is proof. Product-facing
  completion needs screenshots, viewports, checked states, journeys,
  accessibility, overlap, performance note and evidence refs.
- Auditor preflight is not a real Quasar code audit. Preflight must be marked as
  bounded evidence, not code-audit PASS.
- Keep R3/R4 human authority explicit; never fake approval records.
- Before saying "done", show evidence, tests, state, and remaining risk.
