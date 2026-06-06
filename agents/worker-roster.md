# Worker Roster

This roster names factory workers at process level. Detailed machine-readable
contracts live in `agents/worker-registry.public.json`.

## Worker Modes

- `open`: best for exploration, ambiguity, taste and judgment.
- `closed`: best for repeatable work with predictable inputs and verifiable
  outputs.
- `hybrid`: mixes judgment with repeatable checks.
- `human`: records a real human decision; agents cannot fake it.

A worker graduates from open to closed only after the same shape repeats,
inputs become predictable, output is verifiable and no mid-run taste decision is
needed.

## Planning And Architecture

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `factory-orchestrator` | hybrid | F0-F18 | Maintains phase, risk, routing, blockers and Kanban state. It does not approve product, security or R3/R4 gates. |
| `source-ledger-worker` | open | F0-F1 | Separates source, inference, decision, conflict and gap before any SOT claim is promoted. |
| `product-sot-planner` | open | F2-F3 | Turns source ledger and answers into a Product SOT candidate. Candidate is not approval. |
| `product-architect` | open | F4-F6 | Creates architecture candidate, boundaries, tradeoffs and risk map from the SOT. |
| `product-face` | hybrid | F5/F13 | Defines and validates screens, states, mobile, wallet UX, accessibility, performance and visual evidence. |
| `docs-os-worker` | closed/hybrid | F10 | Converts approved architecture into specs, ADRs, diagrams, contracts and evidence paths. |
| `decomposition-planner` | closed | F11 | Produces work packages and Hermes card graph with risk, runtime, reviewer and gate contracts. |

## Execution And Review

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `implementation-worker` | closed by stack | F12 | Executes bounded cards only. It cannot expand scope, change architecture or self-approve. |
| `qa-verification-worker` | closed/hybrid | F13-F15 | Runs tests, screenshots, logs, regressions and evidence checks. |
| `independent-reviewer` | hybrid | F14 | Reviews another worker's output. Executor and reviewer must differ. |
| `autoreview-gate` | closed | F14/F15 | Runs structured pre-landing code review. It finds issues but does not replace independent review. |
| `remote-proof-runner` | closed | F13-F16 | Uses Crabbox/Testbox/container fallback for heavy or clean-environment proof with TTL, cost and cleanup evidence. |
| `handoff-packer` | closed | F9-F15 | Creates portable handoff packets for worker transfer, pause, context compaction or phase change. |

## Security And Onchain

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `security-orchestrator` | hybrid | F6-F16 | Chooses required security specialists and prevents generic security comments from passing as evidence. |
| `codex-security` | hybrid | F8/F13 | Runs Codex Security or equivalent scoped scans when the card requires it. |
| `appsec-owasp-specialist` | hybrid | F7/F14/F15 | Covers OWASP Web/API/AppSec, auth, session, validation and safe errors. |
| `agentic-ai-security-specialist` | hybrid | F1/F7/F12/F14 | Covers prompt injection, tool misuse, browser risk, memory poisoning and excessive agency. |
| `cloud-infra-security-specialist` | hybrid | F7/F14/F16 | Covers IAM, KMS, CI/CD, deploy, DNS, IaC, logs and rollback. |
| `crypto-key-management-specialist` | hybrid | F7/F15/F16 | Covers secrets, signing, custody, cryptography and key lifecycle. It never touches real keys or funds. |
| `solana-quasar-auditor` | hybrid | F7/F13/F15 | Runs or prepares Auditor evidence for Solana/Quasar work. Anchor assumptions are forbidden. |
| `supply-chain-gate` | closed/hybrid | F11/F13/F16 | Checks dependencies, CI, secret scan, SBOM/provenance and workflow risk. |
| `detection-monitoring-worker` | closed/hybrid | F16-F17 | Ensures logs, metrics, alerts, incident owner and rollback evidence exist. |

## Human, Release And Learning

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `human-gate-clerk` | human-support | F9/F15/F16 | Prepares and records real human decisions. It cannot invent approval. |
| `release-ops-worker` | closed/hybrid | F16-F17 | Handles promotion packet, smoke, canary, rollback readiness and monitoring. |
| `public-safety-gate` | closed | F16-F17 | Blocks public artifacts containing private paths, internal names, raw source extraction or private links. |
| `memory-steward` | hybrid | F0/F1/F18 | Treats memory as a risk surface with source, trust tier, freshness and poisoning controls. |
| `skill-eval-distiller` | hybrid | F18 | Turns repeated success/failure into compact skills, evals, templates or checklists. |

## Non-Executable Critical Roles

These roles are useful for reviews, but they are not registered workers until
they get a machine-readable contract in `agents/worker-registry.public.json`.

| Role | Mode | Enters | What it does |
|---|---|---|---|
| `factory-critic` | open | F18 | Attacks the methodology for ambiguity, over-complexity, under-specification and agent misinterpretation. |

## Why This Roster Is Better

It separates broad judgment from repeatable execution. That prevents the two
classic agent failures: a generic specialist trying to own everything, and a
closed worker being asked to make taste or architecture decisions it cannot
verify.
