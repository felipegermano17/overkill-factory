# Overkill Factory

Language: English | [Português](README.pt-BR.md)

Overkill Factory is a production line for Hermes-powered agentic product work.
It turns a rough request into controlled factory state: source intake,
understanding confirmation, Product SOT, full Product SOT scope coverage,
method routing, worker packets, gates, evidence, review, release readiness and
learnback.

It exists for operators who want agents to work with speed without letting chat,
enthusiasm or a partial demo become the source of truth.

Public map:
https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html

## What It Is Technologically

Overkill Factory is an open-source factory kernel for agentic product
execution. Technologically, it is not a hosted SaaS, not a chatbot, not a fork
of Hermes and not a standalone agent runtime.

It is a Python package, CLI, contract library, Hermes adapter and public
operator toolkit that makes product work deterministic enough for agents to run
without inventing the route.

The technology split is:

| Layer | What owns it | What it does |
| --- | --- | --- |
| Runtime | Hermes Kanban | Durable boards, cards, parent/child dependencies, typed blocks, dispatcher, worker processes, comments, runs, logs, workspaces and schedules. |
| Factory kernel | Overkill Factory | Phase graph, method contracts, schemas, templates, validation, gates, capability routing, worker authority rules, Product Experience, security/release checks and Receipt Five evidence rules. |
| CLI and validators | `factoryctl` and scripts | Generate, inspect and validate cards, packets, receipts, workflows, worker profiles, public docs and release readiness. |
| Runtime adapter | `factory/adapters/hermes/` | Connects factory contracts to the real Hermes Kanban state without replacing Hermes as the source of truth. |
| Worker catalog | `factory/agents/`, `factory/skills/`, `factory/templates/` | Defines what specialist workers are allowed to do, which factory/skills/capabilities they need and what evidence they must return. |

So the short version is:

```text
Hermes runs the factory floor.
Overkill Factory defines the production method and checks.
Agents execute bounded cards.
Humans only decide real human gates.
```

The repository contains the public kernel: schemas, templates, docs, examples,
fixtures, tests, worker/profile registries and Hermes integration code. A real product run still needs an operator-owned Hermes
runtime where the actual cards, workers, results and evidence live.

## Plain Explanation

Overkill Factory is a production line for projects built by agents.

Instead of asking an agent to "build an app" and hoping it codes the right
thing, the factory turns the idea into a controlled process: understand the
material, confirm the understanding, plan the work, split the work, call
specialist agents, demand proof, review results, block risk and only then call
something done.

In simple terms:

- **Hermes** is the factory floor: tasks, cards, agents, status and logs.
- **Overkill Factory** is the method: rules, stages, contracts, gates, workers,
  evidence and validation.
- **Factory manager** is the front door: the operator talks to it, for example
  through Telegram.
- **Workers** are specialist agents: product, architecture, frontend, backend,
  security, Solana, QA, docs, release and more.
- **Gates** are checkpoints: can this advance, is there proof, does a human need
  to decide?
- **Receipt Five** is the final receipt: the evidence package showing what was
  built, tested, reviewed and approved or blocked.

The normal flow is:

```text
your idea/material
-> product understanding
-> confirmation with you
-> product source of truth
-> complete plan
-> tasks for agents
-> execution
-> tests and review
-> approval/block
-> evidence-backed delivery
-> learnback to improve the factory
```

The most important point: the factory is not "a smart chat" and not a
mini-Hermes. Hermes owns the native runtime floor: Kanban state, typed blocks,
dependencies, dispatch and worker execution. Overkill Factory adds the product
method, contracts and gates only where Hermes needs a factory-specific layer.

The Swiss Watch reliability audit makes that rule executable:

```bash
python factory/scripts/swiss_watch_audit.py --out .tmp/swiss-watch-audit.json --markdown .tmp/swiss-watch-audit.md
```

It checks that the production-line gears have contracts, Hermes-native
authority, no-idle safeguards, operator UX rules, block classification,
security boundaries, loop control and worker quality floors.

## Why This Exists

Agentic work usually fails in the spaces between tasks:

- a product paper becomes an informal summary;
- a first slice quietly replaces the full product scope;
- a worker says "done" without inspectable evidence;
- a dashboard looks useful but is not the runtime source of truth;
- a blocked path waits for the operator even when the factory should repair it.

Overkill Factory makes those spaces explicit. A signal enters through known
contracts. Every important state has an owner, gate, next action and evidence
shape. Non-human blocks are expected to return to factory-owned repair routes.
Human gates remain human gates.

## How The Factory Works

The public method is a staged production line for controlled product work, but
Factory V3 is not a single straight conveyor belt.

There is a default happy path, shown below, because people need a simple way to
understand the factory. At runtime, the factory behaves more like a controlled
graph: the route registry, method contract, risk gates, capability packs,
Hermes dependencies and current evidence decide what can run now, what can run
in parallel, what must repair itself, and what truly needs a human.

Default happy path:

```text
raw signal
-> Universal Signal Intake
-> source ledger and source resolution
-> operator understanding confirmation
-> outcome and discovery
-> Product SOT
-> full Product SOT scope coverage
-> method contract
-> capability pack and risk routing
-> architecture, security and access gates
-> Product Creation Plan and work units
-> multi-operator Decomposition Coverage Review
-> Product Implementation Readiness
-> Hermes worker packets
-> execution, verification and independent review
-> Receipt Five
-> release/block decision
-> monitoring, support and learnback
```

Inputs can be product papers, bugs, ideas, existing repositories, incidents,
release requests, research requests, UX requests, analytics requests,
integrations, migrations or agent/runtime changes. The route registry and
golden signal corpus make those paths inspectable instead of hidden in
conversation.

The output is not "a good answer." It is a product or factory decision that can
be audited: what was requested, what was planned, what blocked, what was done,
who had authority and what evidence allows the next state.

Product-facing work must also create a project design-system contract and an
AI-readable `DESIGN.md` before frontend builders or Product Face proof can pass.

## Factory Operating Systems

Critical factory areas are grouped in a canonical Operating System registry.
This keeps the factory from becoming scattered contracts with no operational
owner.

Inspect it with:

```bash
factoryctl operating-systems
factoryctl validate-operating-systems factory/templates/factory-operating-system-registry.json
factoryctl operating-system-scorecard --runtime-proof .tmp/factory-runs/hermes-runtime/hermes-worker-runtime-proof.json
```

The registry currently tracks Product Truth and Research, Method, Authority and
Autonomy, Hermes Worker Runtime, Evidence and Product Proof, Capability and
Domain Packs, Operator Experience, Security and Release, Product Quality,
Velocity and Cost, and Factory Learning.

An OS entry names the owner worker, issue, contracts, fail-closed rules,
runtime boundary and required proof. It does not claim a product is production
ready. Production still requires Hermes state, worker results, Receipt Five,
product-specific proof and human gates when risk requires them.

Hermes runtime proof is public-safe and redacted: it proves gateway,
Telegram/operator routing, manager profile, worker completion and human-gate blocking without
publishing private board content. It proves the factory operating spine, not a
specific product release.

Method OS also has a method-engine registry:

```bash
factoryctl method-engines
factoryctl validate-method-engines factory/templates/method-engine-registry.json
```

The Method Contract must bind selected methods to engines such as spec-first
SDD, test-first TDD, behavior-first BDD, discovery/research, security-first,
design-first, legacy diagnosis or incident-first. A method label alone cannot
authorize execution.

## Hermes Runtime

Hermes is the first supported factory floor. Overkill Factory does not replace
Hermes; the normal execution path today is Hermes Kanban plus Overkill Factory
contracts.

Overkill Factory supplies method, schemas, worker registry, Hermes bindings,
adapter hooks, examples and validation tools. Hermes supplies the durable
Kanban runtime where cards, workers, comments, runs and state transitions live.

The runtime boundary is simple:

- `factoryctl`, schemas and tests validate public contracts.
- Hermes Kanban remains the source of truth for real cards and transitions.
- Worker results and Receipt Five are completion evidence.
- Operator consoles and dashboards may project state, but they do not approve
  gates or replace Hermes.

Speed is controlled by authority, not by vibe. Low-risk reversible work can use
the Fast Autonomy Lane. Production, mainnet, funds, signing, secrets, billing,
destructive actions and human-gate approval stay outside any YOLO-like mode.
See `docs/operations/fast-autonomy-lane.md`.

Hermes and Receipt Five remain the source of truth for real factory execution.

## Ways To Use It

There are two practical operating paths:

| Path | Use when | What happens |
| --- | --- | --- |
| `factoryctl` only | You want to inspect, validate or generate packets locally. | The CLI writes public-safe artifacts under `.tmp/`. It does not mutate a live Hermes board. |
| Hermes runtime | You want the factory to run real cards and workers. | Hermes Kanban owns cards, workers, comments, runs and transitions. |

The operator-facing start bridge remains a contract, not a product plugin. It
can create sealed source envelopes and `factory_bridge_start_request` records,
but the factory/Hermes start path owns board creation, card creation, routing and
blocking state. Read `docs/operator/overkill-factory-bridge.md` for that
contract.

## First Run

From a clean checkout:

```bash
git clone https://github.com/felipegermano17/overkill-factory.git
cd overkill-factory
python -m pip install -e ./factory
factoryctl doctor
factoryctl run minimal
factoryctl v3-production-activation-check
factoryctl literal-dod-audit
```

`literal-dod-audit` is intentionally stricter than the local activation check:
it reports `PARTIAL_EXTERNAL` until live Telegram/operator proof is actually
verified. A local 100% score means every implementable repo/runtime support path
exists; it is not a claim that an external Telegram user already completed a
live start.

For a live Hermes runtime proof, run the mutating smoke on a disposable board:

```bash
factoryctl v3-production-activation-check --live-hermes
```

That command must pass before a V3 activation/release claim. It writes a
Factory Perfect Run record and a live Hermes Kanban smoke under `.tmp/`; the live
smoke creates, comments, blocks, unblocks and completes a disposable card with
Receipt Five metadata.
Generated worker packets and gate reports belong in `.tmp/`. Release artifacts
and private evidence stores are valid homes for evidence that should not be
tracked in the public repo.

Create a product workspace when you are ready to connect the method to your own
material:

```bash
factoryctl init --out ../my-product-factory --project-name my-product
factoryctl operator-interface --primary-interface telegram --out .tmp/operator-interface-profile.json
factoryctl validate-operator-interface .tmp/operator-interface-profile.json
factoryctl start-conversation --operator-interface .tmp/operator-interface-profile.json --source-envelope-ref external:operator-source-envelope --out .tmp/factory-start-conversation.json
factoryctl validate-start-conversation .tmp/factory-start-conversation.json
factoryctl intake --route-class product_creation --request-type product_new --signal-type product_paper --summary "Public-safe product brief enters source resolution and understanding confirmation." --source-ref external:source-card-product-brief --out .tmp/universal-signal-intake.json
factoryctl validate-signal-intake .tmp/universal-signal-intake.json
```

Read `docs/getting-started/quickstart-hermes.md` and
`docs/getting-started/install-in-hermes.md` before connecting generated packets
to an operator-owned Hermes runtime.

## Repository Shape

Every tracked top-level directory must justify why it exists, who opens it
first, what its source of truth is and how drift is prevented.

| Path | Public purpose |
| --- | --- |
| `.github/` | GitHub workflows, templates, Dependabot and repository hygiene. See `.github/PROJECT_SURFACE.md`. |
| `factory/adapters/` | Runtime integrations, currently Hermes hooks and patches. See `factory/adapters/README.md`. |
| `factory/agents/` | Public worker registry, profiles, permissions, capability packs and Hermes bindings. See `factory/agents/README.md`. |
| `docs/` | Human guides for onboarding, concepts, operations, security and maintenance. See `docs/README.md`. |
| `factory/examples/` | Small public examples and source fixtures for the factory path. See `factory/examples/README.md`. |
| `factory/fixtures/` | Minimal public-safe regression fixtures, including advanced product-shaped validation fixtures. See `factory/fixtures/README.md`. |
| `factory/schemas/` | Machine contracts for cards, receipts, workers, gates and public artifacts. See `factory/schemas/README.md`. |
| `factory/scripts/` | CLI entrypoints, validation tools, proof helpers and maintainer checks. See `factory/scripts/README.md`. |
| `factory/skills/` | Installable factory skill material for operators/agents. See `factory/skills/README.md`. |
| `factory/templates/` | Starter contracts paired with schemas and tests. See `factory/templates/README.md`. |
| `factory/tests/` | Regression coverage for public contracts, docs, adapters and examples. See `factory/tests/README.md`. |

Ignored local folders such as `.tmp/`, `build/`, `dist/`, `site/` and
`*.egg-info/` are not public product surfaces.

## Current Release State

Factory V3 is the current public kernel release line. The latest public release
is v3.0.2.

V3 means the public kernel has executable contracts for the factory line plus
release-grade guards for the operating model itself:

- deterministic phase graph, compiled workflow, command inbox, event log,
  decision outbox and promotion packets;
- Hermes/Kanban as the real runtime source of truth for cards, workers,
  dependencies, typed blocks, dispatch and task lifecycle;
- no mini-Hermes: the factory owns method, gates, rules, schemas, audits,
  validations and release checks, not runtime queues or schedulers;
- runtime truth spine: worker packet, dispatch request, running task and
  consumable worker result are distinct states;
- canonical frontier/no-idle guard: repairable gaps route to repair before
  human input, and no-idle remains recovery/audit, not route authority;
- gerente and agent freshness guard: factory changes must update manager and
  affected agent skills, profiles, configs and bindings before E2E or release;
- Product Experience control plane: product-facing work needs Product
  Experience Plan, Product Face Packet, professional design process, project
  design system, `DESIGN.md` and Product Face Result proof;
- capability acquisition and security/release authority: missing specialists
  route through capability acquisition, Solana/on-chain work requires Solana AI
  Kit routing, and production/mainnet/funds/secrets/release decisions require
  explicit authority;
- artifact-first human gates and Receipt Five anti-overclaim: the operator gets
  material before the decision question, and `done` requires evidence readback;
- simplified public map and first-value path for external operators.

That claim is intentionally scoped. Factory V3 does not mean a specific product
is production-ready. A product built by the factory still needs its own source
material, Product SOT, worker execution, evidence, reviews, human gates and
production readiness proof.
Public promises are tracked in
`docs/operations/promise-to-implementation.md` and
`docs/promise-implementation-map.public.json`; each major claim must name its
implementation, proof and boundary.

## Read Next

- `docs/index.md`: documentation home.
- `docs/getting-started/quickstart-hermes.md`: first run with Hermes context.
- `docs/getting-started/install-in-hermes.md`: connect to an operator-owned Hermes runtime.
- `docs/reference/cli.md`: supported `factoryctl` commands.
- `docs/reference/factory-kernel-reference.md`: generated reference of the actual phases, workers, profiles, operating systems, method engines, schemas, templates and public surfaces.
- `docs/architecture/factory-v2-control-plane.md`: deterministic control plane.
- `docs/operations/telegram-operator-experience.md`: Telegram-first operator experience without turning Telegram into the runtime source of truth.
- `factory/templates/v2-study-traceability.json`: raw V2 claim ledger with bounded truth levels, evidence refs and known gaps.
- `factory/templates/v2-doc-implementation-obligations.json`: obligations that prevent documented V2 work from being mistaken for implemented code.
- `factory/templates/factory-v2-readiness-claim.json`: scoped readiness claim contract.
- `docs/operations/promise-to-implementation.md`: public promise-to-proof audit.

## Validation

Before publishing public changes:

```bash
python factory/scripts/validate_document_governance.py
python factory/scripts/generate_factory_reference_docs.py --check
python factory/scripts/validate_public_json_artifacts.py
python factory/scripts/validate_worker_profiles.py
python factory/scripts/validate_promise_implementation_map.py
python factory/scripts/factoryctl.py validate-v2-runtime-contracts
python factory/scripts/factoryctl.py validate-agent-skill-boundaries
python factory/scripts/factoryctl.py validate-reference-superiority
python factory/scripts/factoryctl.py capability-acquisition-run --capability-gap solana-ai-kit --surface solana --out .tmp/factory-runs/capability/readme-capability-acquisition-run.json
python factory/scripts/factoryctl.py validate-capability-acquisition-run .tmp/factory-runs/capability/readme-capability-acquisition-run.json
python factory/scripts/factoryctl.py validate-v2-study-traceability factory/templates/v2-study-traceability.json
python factory/scripts/factoryctl.py validate-v2-doc-implementation-obligations factory/templates/v2-doc-implementation-obligations.json --traceability factory/templates/v2-study-traceability.json
python factory/scripts/public_safety_scan.py
python factory/scripts/secret_safety_scan.py
python factory/scripts/validate_public_surface_sync.py
cd factory && python -m unittest discover -s tests -q
```

For release readiness:

```bash
python factory/scripts/release_integration_preflight.py
python factory/scripts/worktree_release_inventory.py
factoryctl v1-completion-gate --github-actions-result PASS --open-v1-blockers 0 --open-prs 0
```

The public map is validated by `factory/scripts/validate_public_surface_sync.py`. It
compares the tracked HTML against the published GCS object and checks that the
visual does not claim runtime authority.

## Public Boundary

The repository is a public product surface. It must not contain secrets, raw
private evidence, private board links, local absolute paths, private source
dumps, screenshots from private runs, generated worker packets, historical proof
archives or chat-derived authority.

Narrative validation history, old release notes disguised as proof and internal
audit trails do not belong in the public onboarding path. Public onboarding
should point to current contracts, runnable examples, validators and concise
operator guides.

Hermes and Receipt Five remain the source of truth for real factory execution.
This repo documents and validates the factory kernel; it is not a warehouse for
private runtime history.

## License

MIT.
