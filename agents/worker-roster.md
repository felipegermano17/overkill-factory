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
- 2 Control Tower operator console workers.

The gateway profile `overkill-factory-gerente` is official, but it is not
counted as a worker. It is an operator-interface profile: it talks to the
operator through the selected primary channel, pushes status and registers
intent through Hermes without executing product work.

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
| `factory-orchestrator` | hybrid | F0/F1/F6-F9/F11-F13/F15/F18 | Maintains phase, risk, routing, Method Contract, capability coverage, Kanban-native dependencies, decomposition readiness and blockers, then emits semantic transition/recovery intent for Hermes. It does not own Kanban runtime state or approve product, security or R3/R4 gates. |
| `source-ledger-worker` | open | F0-F3 | Separates source, inference, decision, conflict, stale material and gap before any SOT claim is promoted. |
| `product-sot-planner` | open | F2-F5 | Owns Outcome/Discovery and turns source ledger plus answers into a Product SOT candidate plus owner-readable review packet. Candidate is not approval. |
| `product-architect` | open | F4-F6 | Creates architecture candidate, boundaries, tradeoffs, trust boundaries and risk map only after owner-readable Product SOT material and Method Contract exist. |
| `product-face` | hybrid | F5/F8/F13 | Defines and validates Product Experience Plan, Product Face packet, screens, states, mobile, wallet UX, accessibility, performance and visual evidence. |
| `docs-os-worker` | closed/hybrid | F10 | Converts approved architecture into specs, ADRs, diagrams, contracts and evidence paths. |
| `decomposition-planner` | closed | F11 | Produces Spec Graph, Loop Plan, work packages and Hermes card graph with risk, runtime, reviewer, lane/worktree and gate contracts. |

## Execution Builders

These are the operators that actually create product implementation. The
generic `implementation-worker` is now only a fallback when no specialist owns
the card.

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `frontend-builder` | hybrid | F12-F13 | Builds scoped screens, components, responsive states, wallet-facing UI and browser-testable product surfaces from Product Experience and Product Face contracts. Product Face still validates the result. |
| `backend-api-builder` | hybrid | F12-F13 | Builds scoped API, service, validation, auth/session and server behavior with contract/API test evidence. |
| `data-persistence-builder` | hybrid | F12-F13 | Builds schema, migration, storage and data-access changes with rollback and data-risk notes. |
| `solana-quasar-builder` | hybrid | F12-F13 | Builds scoped Solana program work after `solana-ai-kit-core` routing, using Quasar when that implementation lane is selected. Anchor assumptions, mainnet deploys and real keys are forbidden. |
| `solana-quasar-qa-engineer` | hybrid | F13/F15 | Runs Quasar/devnet/local behavior proof, negative tests, compute-unit checks and audit handoff notes after Solana AI Kit routing is present. |
| `wallet-transaction-builder` | hybrid | F12-F13 | Builds wallet connection, signing prompts and transaction states without touching real keys or funds. |
| `integration-builder` | hybrid | F12-F13 | Connects approved frontend, backend, data, wallet and onchain surfaces into an end-to-end flow. |
| `test-automation-builder` | hybrid | F12-F13/F18 | Turns acceptance criteria into repeatable unit, integration, E2E, visual or eval proof. |
| `infra-devops-builder` | hybrid | F12/F16 | Builds scoped CI/CD, runtime, environment and deploy wiring with smoke and rollback evidence. |
| `agent-runtime-builder` | hybrid | F12/F18 | Builds factory/Hermes adapter, profile, skill, MCP and worker-routing changes with profile validation. |
| `implementation-worker` | hybrid fallback | F12/F15 | Executes or routes only generic/legacy implementation work that no specialist builder owns. |

## Proof, Review And Handoff

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `qa-verification-worker` | closed/hybrid | F13/F15/F17 | Runs tests, screenshots, logs, regressions and evidence checks. |
| `independent-reviewer` | hybrid | F12/F18 | Reviews decomposition coverage and another worker's output. Executor and reviewer must differ, and a single reviewer cannot approve complete-product decomposition alone. |
| `evidence-reconciler` | deterministic | F13/F15/F16/F18/F21/F22 | Resolves current worker results from evidence freshness rules, records superseded stale evidence and blocks Closure Summary, Completion Audit, Receipt Five or done when closure evidence is invalid. |
| `autoreview-gate` | closed | F15 | Runs structured pre-landing code review. It finds issues but does not replace independent review. |
| `remote-proof-runner` | closed | F13-F16 | Uses Crabbox/Testbox/container fallback for heavy or clean-environment proof with TTL, cost and cleanup evidence. |
| `handoff-packer` | closed | F9/F15/F20 | Creates portable handoff packets for worker transfer, pause, context compaction or phase change; it must not promote future-phase work while `factory_phase_lock` freezes downstream. |

## Security And Onchain

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `security-orchestrator` | hybrid | F4-F16 | Resolves Security Architecture Plan routes and required security specialists from the registry, then prevents generic security comments from passing as evidence. |
| `codex-security` | hybrid | F8/F13 | Runs Codex Security or equivalent scoped scans when the card requires it. |
| `appsec-owasp-specialist` | hybrid | F7/F15 | Covers OWASP Web/API/AppSec, auth, session, validation and safe errors. |
| `agentic-ai-security-specialist` | hybrid | F1/F7/F12/F15 | Covers prompt injection, tool misuse, browser risk, memory poisoning and excessive agency. |
| `cloud-infra-security-specialist` | hybrid | F7/F15/F16 | Covers IAM, KMS, CI/CD, deploy, DNS, IaC, logs and rollback. |
| `crypto-key-management-specialist` | hybrid | F7/F15/F16 | Covers secrets, signing, custody, cryptography and key lifecycle. It never touches real keys or funds. |
| `solana-quasar-auditor` | hybrid | F7/F13/F15 | Runs or prepares Auditor evidence for Solana/onchain work routed through `solana-ai-kit-core`; Quasar proof is required when the Quasar lane is selected. Anchor assumptions are forbidden. |
| `supply-chain-gate` | closed/hybrid | F11/F13/F16 | Checks dependencies, CI, secret scan, SBOM/provenance and workflow risk. |
| `detection-monitoring-worker` | closed/hybrid | F4/F16-F17 | Owns Data/Metrics planning and ensures logs, metrics, alerts, incident owner and rollback evidence exist. |

## Human, Release And Learning

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `human-gate-clerk` | human-support | F9/F15/F16/F24 | Prepares and records real human decisions for authority, access, budget, waiver, material risk and release. It must deliver the operator decision package before asking for a decision, obey `factory_phase_lock`, and must not ask approval for planning-only continuation, source resolution, method routing, specialist routing or downstream work that is still frozen. |
| `release-ops-worker` | closed/hybrid | F16/F17/F23-F25 | Handles release channel, production operations, promotion packet, smoke, canary, rollback readiness and monitoring. |
| `public-safety-gate` | closed | F16-F17 | Blocks public artifacts containing private paths, internal names, raw source extraction or private links. |
| `memory-steward` | hybrid | F0/F1/F18 | Treats memory as a risk surface with source, trust tier, freshness and poisoning controls. |
| `skill-eval-distiller` | hybrid | F8/F18/F26/F27 | Owns Agent Quality, Learnback and Factory Maturity audits, then turns repeated success/failure into compact skills, evals, templates, checklists or pack/worker changes. |

## Control Tower

| Worker | Mode | Enters | What it does |
|---|---|---|---|
| `control-tower-projection-worker` | read-only projection | operator_projection | Projects Hermes state into the operator console without deciding gates or mutating cards. |
| `discord-control-tower-bridge` | bridge | operator_projection/F27 | Maps Hermes and Discord events, emits bridge health and records operator responses through the runtime contract. |

## Non-Executable Critical Roles

These roles are useful for reviews, but they are not registered workers until
they get a machine-readable contract in `agents/worker-registry.public.json`.

| Role | Mode | Enters | What it does |
|---|---|---|---|
| `factory-critic` | open stance | F18 | Review stance used by `skill-eval-distiller` and `independent-reviewer` to attack ambiguity, over-complexity, under-specification and agent misinterpretation. It is not a separate executable worker until it has registry, profile, binding and eval proof. |

## Anti-Theater Rules

- A planner cannot produce implementation proof.
- A builder cannot approve its own output.
- A reviewer cannot modify implementation artifacts while acting as reviewer.
- A gate is not counted as an autonomous builder.
- A human-support worker records decisions; it cannot invent approval.
- `implementation-worker` is fallback only. If a surface-specific builder
  matches, the fallback worker is not required.
- Solana work first routes through `solana-ai-kit-core`. The
  `solana-quasar-builder`, `solana-quasar-qa-engineer` and
  `solana-quasar-auditor` IDs name the Quasar implementation/proof lane when
  that lane applies; Solana AI Kit remains the domain brain.
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
