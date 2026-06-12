# Worker Roster

This roster names factory workers at process level. Detailed machine-readable
contracts live in `agents/worker-registry.public.json`.

The live-agent layer is separate:

- `agents/worker-profiles.public.json` defines each agent identity, authority,
  refusal rules, evidence, review, handoff and failure behavior.
- `agents/hermes-profile-bindings.public.json` maps each worker to the Hermes
  profile name, dispatch queue, skill refs and result schema.
- `agents/worker-permission-classes.public.json` maps each worker to its
  permission class and authority boundary.
- `scripts/factoryctl.py` injects this binding into generated worker packets so
  Hermes can hand the task to the correct profile.

A worker in this roster is not considered operable unless it has a profile,
binding, packet route and validation coverage.

For the full process map, see
`docs/agents/factory-stage-agent-map.md`. It maps each canonical factory stage
to a real registered worker, supporting workers, proof and blocker.

The roster has 40 public-safe operators:

- 7 planning/documentation/router workers.
- 10 specialist builders plus 1 generic fallback builder.
- 6 proof/review/handoff/closure workers.
- 10 security/onchain/release-safety workers.
- 4 human, release, memory and learning support workers.
- 2 Control Tower cockpit workers.

The Discord gateway profile `overkill-factory-gerente` is official, but it is
not counted as a worker. It is an interface profile: it talks to the operator
and registers intent through Hermes without executing product work.

That number is intentionally split by ownership. It is not meant to create 40
parallel personalities. A card should call only the operators whose surface,
risk and phase match the work.

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
| `factory-orchestrator` | hybrid | F0-F18 | Maintains phase, risk, routing, Method Contract, capability coverage, readiness, blockers and Kanban state. It does not approve product, security or R3/R4 gates. |
| `source-ledger-worker` | open | F0-F1 | Separates source, inference, decision, conflict, stale material and gap before any SOT claim is promoted. |
| `product-sot-planner` | open | F2-F3 | Owns Outcome/Discovery and turns source ledger plus answers into a Product SOT candidate. Candidate is not approval. |
| `product-architect` | open | F4-F6 | Creates architecture candidate, boundaries, tradeoffs, trust boundaries and risk map from the SOT. |
| `product-face` | hybrid | F5/F13 | Defines and validates screens, states, mobile, wallet UX, accessibility, performance and visual evidence. |
| `docs-os-worker` | closed/hybrid | F10 | Converts approved architecture into specs, ADRs, diagrams, contracts and evidence paths. |
| `decomposition-planner` | closed | F11 | Produces Spec Graph, Loop Plan, work packages and Hermes card graph with risk, runtime, reviewer, lane/worktree and gate contracts. |

## Execution Builders

These are the operators that actually create product implementation. The
generic `implementation-worker` is now only a fallback when no specialist owns
the card.

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `frontend-builder` | hybrid | F12-F13 | Builds scoped screens, components, responsive states, wallet-facing UI and browser-testable product surfaces. Product Face still validates the result. |
| `backend-api-builder` | hybrid | F12-F13 | Builds scoped API, service, validation, auth/session and server behavior with contract/API test evidence. |
| `data-persistence-builder` | hybrid | F12-F13 | Builds schema, migration, storage and data-access changes with rollback and data-risk notes. |
| `solana-quasar-builder` | hybrid | F12-F13 | Builds scoped Solana program work using Quasar. Anchor assumptions, mainnet deploys and real keys are forbidden. |
| `solana-quasar-qa-engineer` | hybrid | F13/F15 | Runs Quasar/devnet/local behavior proof, negative tests, compute-unit checks and audit handoff notes. |
| `wallet-transaction-builder` | hybrid | F12-F13 | Builds wallet connection, signing prompts and transaction states without touching real keys or funds. |
| `integration-builder` | hybrid | F12-F13 | Connects approved frontend, backend, data, wallet and onchain surfaces into an end-to-end flow. |
| `test-automation-builder` | hybrid | F12-F13/F18 | Turns acceptance criteria into repeatable unit, integration, E2E, visual or eval proof. |
| `infra-devops-builder` | hybrid | F12/F16 | Builds scoped CI/CD, runtime, environment and deploy wiring with smoke and rollback evidence. |
| `agent-runtime-builder` | hybrid | F12/F18 | Builds factory/Hermes adapter, profile, skill, MCP and worker-routing changes with profile validation. |
| `implementation-worker` | hybrid fallback | F12 | Executes or routes only generic/legacy implementation work that no specialist builder owns. |

## Proof, Review And Handoff

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `qa-verification-worker` | closed/hybrid | F13-F15 | Runs tests, screenshots, logs, regressions and evidence checks. |
| `independent-reviewer` | hybrid | F14 | Reviews another worker's output. Executor and reviewer must differ. |
| `evidence-reconciler` | deterministic | F13-F16 | Selects current worker results, records superseded stale evidence and blocks Closure Summary, Completion Audit, Receipt Five or done when closure evidence is invalid. |
| `autoreview-gate` | closed | F14/F15 | Runs structured pre-landing code review. It finds issues but does not replace independent review. |
| `remote-proof-runner` | closed | F13-F16 | Uses Crabbox/Testbox/container fallback for heavy or clean-environment proof with TTL, cost and cleanup evidence. |
| `handoff-packer` | closed | F9-F15 | Creates portable handoff packets for worker transfer, pause, context compaction or phase change. |

## Security And Onchain

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `security-orchestrator` | hybrid | F4-F16 | Chooses Security Architecture Plan routes, required security specialists and prevents generic security comments from passing as evidence. |
| `codex-security` | hybrid | F8/F13 | Runs Codex Security or equivalent scoped scans when the card requires it. |
| `appsec-owasp-specialist` | hybrid | F7/F14/F15 | Covers OWASP Web/API/AppSec, auth, session, validation and safe errors. |
| `agentic-ai-security-specialist` | hybrid | F1/F7/F12/F14 | Covers prompt injection, tool misuse, browser risk, memory poisoning and excessive agency. |
| `cloud-infra-security-specialist` | hybrid | F7/F14/F16 | Covers IAM, KMS, CI/CD, deploy, DNS, IaC, logs and rollback. |
| `crypto-key-management-specialist` | hybrid | F7/F15/F16 | Covers secrets, signing, custody, cryptography and key lifecycle. It never touches real keys or funds. |
| `solana-quasar-auditor` | hybrid | F7/F13/F15 | Runs or prepares Auditor evidence for Solana/Quasar work. Anchor assumptions are forbidden. |
| `supply-chain-gate` | closed/hybrid | F11/F13/F16 | Checks dependencies, CI, secret scan, SBOM/provenance and workflow risk. |
| `detection-monitoring-worker` | closed/hybrid | F4/F16-F17 | Owns Data/Metrics planning and ensures logs, metrics, alerts, incident owner and rollback evidence exist. |

## Human, Release And Learning

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `human-gate-clerk` | human-support | F9/F15/F16 | Prepares and records real human decisions for authority, access, budget, waiver and release. It cannot invent approval. |
| `release-ops-worker` | closed/hybrid | F16-F17 | Handles release channel, production operations, promotion packet, smoke, canary, rollback readiness and monitoring. |
| `public-safety-gate` | closed | F16-F17 | Blocks public artifacts containing private paths, internal names, raw source extraction or private links. |
| `memory-steward` | hybrid | F0/F1/F18 | Treats memory as a risk surface with source, trust tier, freshness and poisoning controls. |
| `skill-eval-distiller` | hybrid | F8/F18 | Owns Agent Quality, Learnback, Factory Maturity audits, the active Factory Improvement Radar and the Factory Mechanic Loop, then turns repeated success/failure, update signals, worker feedback or execution-history findings into compact skills, evals, templates, checklists, pack/worker changes or public-safe factory improvement issues. |

## Control Tower

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `control-tower-projection-worker` | read-only projection | F19 | Projects Hermes state into the operator cockpit without deciding gates or mutating cards. |
| `discord-control-tower-bridge` | bridge | F19/F29 | Maps Hermes and Discord events, emits bridge health and records operator responses through the runtime contract. |

## Non-Executable Critical Roles

These roles are useful for reviews, but they are not registered workers until
they get a machine-readable contract in `agents/worker-registry.public.json`.

| Role | Mode | Enters | What it does |
|---|---|---|---|
| `factory-critic` | open stance | F18 | Review stance used by `skill-eval-distiller` and `independent-reviewer` to attack ambiguity, over-complexity, under-specification and agent misinterpretation. It is not a separate executable worker until it has registry, profile, binding and eval proof. |
| `factory-mechanic-loop` | improvement protocol | F18 | Factory-wide maintenance loop operated by `skill-eval-distiller`. It may create public-safe improvement issues, but it is not a separate executable worker and cannot mutate critical contracts without human approval. |
| `factory-improvement-radar` | active source radar | F18 | Source-watch protocol operated by `skill-eval-distiller` to inspect Hermes/runtime updates, execution history, worker feedback, repo signals, dependencies and external research. It produces a radar record, then either creates an improvement issue, rejects the signal or requests a human decision. |

## Anti-Theater Rules

- A planner cannot produce implementation proof.
- A builder cannot approve its own output.
- A reviewer cannot modify implementation artifacts while acting as reviewer.
- A gate is not counted as an autonomous builder.
- A human-support worker records decisions; it cannot invent approval.
- `implementation-worker` is fallback only. If a surface-specific builder
  matches, the fallback worker is not required.
- Solana work uses `solana-quasar-builder`, `solana-quasar-qa-engineer` and
  `solana-quasar-auditor`; build, QA and audit are separate.
- Conceptual role names such as Method Router, Product Experience Router,
  Security Architect, Production Readiness, Access Capability and Factory
  Maturity Auditor are mapped to official workers in
  `docs/agents/factory-stage-agent-map.md`. They must not exist as loose Hermes
  executor profiles unless promoted through registry, profile, binding,
  permission class, packet route and proof.

## Why This Roster Is Better

It separates broad judgment from repeatable execution. That prevents the two
classic agent failures: a generic specialist trying to own everything, and a
closed worker being asked to make taste or architecture decisions it cannot
verify.

Compared with a single generic developer agent, this roster is better because
each builder has a surface, input contract, output receipt, refusal rule and
review path. Compared with a large cast of planning agents, it is better
because execution ownership is explicit and testable in `factoryctl.py`.
