---
name: overkill-factory
description: Operate the Overkill Factory product-production line. Use when turning raw product papers into Product SOT, Product Experience OS/Product Face, security architecture, access readiness, Hermes Kanban cards, agent execution, Receipt Five evidence, human gates, pilots, or Factory VNext methodology updates.
---

# Overkill Factory

Overkill Factory is a gated product-production line for autonomous agents.
Use Hermes Kanban as the primary runtime unless the user explicitly selects a
different runtime.

## First Move

1. Identify the current factory phase: source, outcome/discovery, SOT, method,
   architecture, Product Experience OS/Product Face, access readiness, review,
   decomposition, execution, verification, production, pilot, or VNext.
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
source intake -> source resolution -> outcome/discovery -> Product SOT
-> Agentic Method Router -> method contract -> Product/Surface Pack selection
-> risk, dependency, compliance, access and budget gates
-> security architecture when material risk exists
-> software/product-experience/data/agent-eval plans -> spec graph -> loop plan
-> autonomy readiness -> Ready Gate -> execution -> worker results
-> verification -> independent review -> human gate when needed
-> closure summary -> Receipt Five -> completion audit
-> production operations -> release or block -> monitoring/support
-> learnback -> factory maturity audit
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

Block or revise cards when:

- `OVERKILL_VFINAL` cards lack `outcome_contract`, `method_contract`, or
  `loop_plan`.
- Product-facing vFinal cards lack Product Experience routing, Product Face
  Packet, or Product Face Result proof.
- Material vFinal execution lacks ready `access_capability` or
  `autonomy_readiness_packet`.
- R3/R4 or security-sensitive vFinal work lacks `security_architecture_plan`.
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
- Hermes `dispatch --dry-run` and `--initial-status blocked` are not enough to
  prove no-spawn safety. No-spawn Hermes smoke cards need a verified `blocked`
  event in `show --json`, and dry-run should be used only on disposable boards.

## References

Load only what is needed:

- `references/factory-line.md` for the full phase model and gates.
- `references/hermes-adapter.md` for Hermes/Kanban coupling and patch status.
- `references/card-contract.md` for card and Receipt Five field rules.
- `references/automation.md` for critical worker packets and `factoryctl.py`.
- `docs/methodology/overkill-factory-vfinal.md` for the public vFinal method.
- `docs/roadmap/factory-vfinal-upgrade-plan.md` for vFinal implementation order.

## Scripts

When inside the `overkill-factory` repository, prefer the repo-level
`scripts/factoryctl.py`:

```bash
python scripts/factoryctl.py gate-report --card path/to/card.md
python scripts/factoryctl.py worker-packet --worker all --card path/to/card.md --out path/to/output-dir
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
- Every important factory area needs a simple, deep Area Manual. If another
  agent cannot continue the area from the document, the document is not done.
- Explain why a proposed gate or worker is better than the alternative.
- Treat older methodology notes as evidence, not as truth by default.
- Keep final canonical documents free of doubts, backlog, raw study, and
  behind-the-scenes comparison. Put those in study, proposal, roadmap, or
  context-lock documents instead.
- Planning may continue with missing access. Material execution must not start
  until indispensable access/capabilities are ready or explicitly blocked.
- Security Review does not replace Security Architecture. Material security
  risk needs security architecture before implementation.
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
- Product Face Packet is planning; `product_face_result` is proof. Product-facing
  completion needs screenshots, viewports, checked states, journeys,
  accessibility, overlap, performance note and evidence refs.
- Product Experience OS is the official layer for product experience across
  websites, web apps, mobile, desktop, CLI/TUI, extensions, agentic interfaces,
  design systems, docs, and onboarding. Product Face is the packet/result
  inside that layer, not the whole layer.
- Auditor preflight is not a real Quasar code audit. Preflight must be marked as
  bounded evidence, not code-audit PASS.
- Keep R3/R4 human authority explicit; never fake approval records.
- Before saying "done", show evidence, tests, state, and remaining risk.
