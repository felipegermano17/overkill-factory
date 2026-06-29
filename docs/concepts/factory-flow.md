# Factory Flow Concepts

Overkill Factory is a gated production line. It is designed to prevent agents
from jumping straight from a vague request to a confident completion claim.

## Operating Mantra

Less mirabolante, more Kanban-native, more Hermes-native, more deterministic
and easier to trust.

That means the factory should prefer visible Kanban structure over hidden agent
interpretation: cards, dependencies, typed blocks, artifacts and native Hermes
dispatch should carry the run. Watchdogs and no-idle checks are guardrails for
integrity and recovery, not the main way the factory discovers what work exists.

In simple terms: the factory lays the rails, Hermes moves the train. When a
phase creates required work, that work becomes native Kanban dependency, not a
private note inside an agent. The next phase waits until the required parent work
is actually done.

## Core Objects

| Object | Meaning |
| --- | --- |
| Product paper | The short project brief or source material that starts the line. |
| Operator interface profile | The selected human interface, such as Telegram, Discord or Cockpit, with proactive notification and attachment rules. |
| Factory start conversation | The open conversational start that confirms the product understanding before a formal start request. |
| Source resolution | The step that separates source facts, inference, decisions, conflicts and gaps. |
| Operator briefing package | The deep review package for important decisions: short plain-text projection plus markdown/PDF attachments and optional explainers. |
| Product SOT | The source-of-truth candidate for the complete product scope, non-goals and acceptance criteria. |
| Full Product SOT scope coverage | The map that prevents a first slice from silently becoming the whole product. |
| Specialist research decision | A public-safe research result that changes SOT, architecture, method, gate, worker, proof or blocker state. |
| Product Creation Plan | The complete product decomposition into safe execution slices, proof and stop rules. |
| Decomposition Coverage Review | The multi-operator review proving every work unit has its owner, reviewer, participant signoffs, evidence and dependency coverage before readiness. |
| Product Implementation Readiness | The gate that checks SOT, method, research, architecture, work units, packs, access and proof before material execution. |
| Factory Phase Engine | The deterministic state calculator that reads materialized artifacts and decides the active frontier, next required artifact and whether a declared card phase is allowed. |
| Factory card | The machine-checkable work contract consumed by Hermes and `factoryctl.py`. |
| Worker packet | The task-specific assignment generated for one worker role. |
| Worker result | The evidence-bearing result produced after a worker actually runs. |
| Receipt Five | The closure metadata that says what changed, where evidence lives, which commands ran, review state and next action. |
| Human gate | A real human decision record for architecture, high-risk work or release promotion. |

## The Happy Path

```text
operator interface profile
-> conversational start
-> source intake
-> source resolution
-> operator understanding confirmation
-> operator briefing package when a decision is needed
-> Product SOT
-> full Product SOT scope coverage
-> specialist research decisions when needed
-> architecture and risk routing
-> method contract
-> Product Creation Plan
-> Decomposition Coverage Review
-> Product Implementation Readiness
-> ready work-unit packets
-> Product Face or surface-specific plan
-> security, access and budget gates
-> decomposition into Hermes cards
-> specialist worker execution
-> QA, review and evidence reconciliation
-> human gate when required
-> Receipt Five
-> release readiness
-> learnback
```

Not every project uses every worker. The card surfaces, risk class and done
definition decide which workers are required.

## Deterministic Phase Engine

Agents may draft, summarize, research and execute scoped work, but they do not
choose the factory route from memory or prose. `factoryctl phase-engine` computes
the current frontier from materialized artifacts:

```text
source/input artifacts
-> source resolution and understanding artifacts
-> Product SOT plus full scope coverage
-> owner-readable Product SOT briefing package
-> Method Contract
-> architecture/planning/readiness artifacts
-> Ready Gate
-> worker execution
```

If a card says it is in a later phase but the required artifacts are missing,
the engine blocks the card. For example, a declared F9 architecture or human
gate package cannot proceed while the computed frontier is still Product SOT and
the next required artifact is `operator_briefing_package`.

In Hermes/Kanban runtime reconciliation, public scaffold material is not
evidence. References such as `factory/templates/...`, `source-ledger.md`,
`factoryctl:gate-report` or embedded placeholder packets copied from
`factory/templates/vfinal-factory-card.json` do not count as product-specific source,
SOT, Method Contract, architecture, readiness or gate artifacts. They are useful
as examples and schemas; a live product board must materialize its own artifacts
before the phase engine advances.

## Deterministic Board Reconciler

`factoryctl reconcile-board` applies the phase engine to Hermes/Kanban board
state. This is the runtime rule for silent boards:

- `running` means observe running work;
- `ready` means native Hermes dispatch is the next action;
- no canonical factory card means repair the board contract, not infer a phase;
- one canonical card means compute its phase engine state and create only the
  next artifact task selected by that state;
- template/scaffold artifacts are ignored in runtime mode, so a copied public
  template reconciles back to the first missing product artifact instead of
  jumping to F9/F13;
- a human gate can be requested only when the phase engine allows it and the
  decision package is complete.

This keeps Telegram, Discord, CLI/API bridge and status messages as operator
views. They can show the reconciled state, but they do not choose F1, F2, F3 or
F9 from conversation history.

## User Role

The normal user provides material, goals, constraints, access when required,
bounded approvals and final review. The factory owns source resolution, Product
SOT drafting, method routing, research routing, worker packets, execution
routing, verification, review, evidence capture, proactive status and completion
audit.

Internal objects such as schemas, worker packets, source ledgers, method
contracts and evidence graphs may be visible for audit or maintainer work, but
they should not become mandatory user labor.

For Telegram-first operation, important decisions should not be made from a
short chat summary alone. The operator should receive a briefing package with a
deep document and PDF attachment, and the bot should proactively push meaningful
state changes instead of waiting for the operator to poll.

Telegram delivery is plain-text first. Markdown/PDF are ordinary file
attachments; Telegram rich cards, rich drafts, media groups and table-rendered
bot messages are not the primary decision package because Telegram Desktop may
render them as unsupported messages.

The manager is the only human-facing voice. Worker completions, Kanban done
events, cron/watchdog messages and artifact dumps may feed internal state, but
they must not notify the operator directly. Even a real human decision is
reported by the manager with the package, not by a raw subscription.

Operator-facing language follows the operator's primary language. That covers
chat, status, decision packages and Hermes Kanban card titles/summaries. Machine
surfaces such as schema keys, record types, phase ids, step keys, worker ids and
logs may remain in English.

## What Blocks A Card

A card should stay blocked when:

- source facts and inference are mixed;
- Product SOT or architecture is only a candidate but treated as approval;
- a first slice exists but the full Product SOT scope coverage is missing;
- research is required but no specialist research plan exists;
- Product Creation Plan, Decomposition Coverage Review or Product Implementation Readiness is missing for complete-product work;
- production or mainnet intent lacks a promotion ladder with environment-specific proof;
- a required worker packet exists but the worker result does not;
- Product Face, security, Auditor, QA or review evidence is missing;
- executor and reviewer are the same identity;
- a human gate is required but no real decision record exists;
- Receipt Five cannot point to current evidence;
- public artifacts contain secrets or private operational residue.

## Source Of Truth

Hermes Kanban state plus repo-relative evidence and receipts are the source of
truth. Telegram messages, Discord messages and status summaries are useful
operator views, but they do not close work by themselves.

## Risk Levels

Use risk to decide how much proof and authority is required:

| Risk | Typical meaning |
| --- | --- |
| R0 | Documentation or local-only inspection with no sensitive action. |
| R1 | Low-risk local validation or small planning change. |
| R2 | Product-facing, code-facing or review-relevant work. |
| R3 | Security, wallet, onchain, infra or high-impact user behavior. |
| R4 | Release, production, irreversible action or major authority boundary. |

R3 and R4 work require stronger specialist evidence and human gates. Agents can
prepare the packet, but they cannot invent approval.

## Why This Shape Exists

Autonomous agents are good at doing scoped work. They are weak when the task
mixes source, judgment, implementation, review and approval into one prompt.
The factory separates those responsibilities so each claim can be checked.
