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
https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.1.html

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

The most important point: the factory is not "a smart chat." It is a system for
preventing agents from skipping understanding, inventing scope, ignoring
security or claiming work is done without proof.

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

The public method is a complete production line, not an MVP shortcut:

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
factoryctl validate-operating-systems templates/factory-operating-system-registry.json
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

Hermes runtime proof is public-safe and redacted: it proves gateway, Codex auth,
Telegram, manager profile, worker completion and human-gate blocking without
publishing private board content. It proves the factory operating spine, not a
specific product release.

Method OS also has a method-engine registry:

```bash
factoryctl method-engines
factoryctl validate-method-engines templates/method-engine-registry.json
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

There are three practical operating paths:

| Path | Use when | What happens |
| --- | --- | --- |
| `factoryctl` only | You want to inspect, validate or generate packets locally. | The CLI writes public-safe artifacts under `.tmp/`. It does not mutate a live Hermes board. |
| Hermes runtime | You want the factory to run real cards and workers. | Hermes Kanban owns cards, workers, comments, runs and transitions. |
| Codex Bridge plugin | You want Codex to act as the human operator bridge. | Codex reads the Durable Operator Inbox and forwards operator decisions without becoming the factory. |

The bridge does not run the factory. It helps collect the initial signal, start
an approved factory run, read pending operator events, surface human gates,
record the operator's answer and hand that answer back to the factory.

Install the Codex Bridge plugin from the repo root:

```bash
codex plugin marketplace add .
codex plugin add overkill-factory-bridge@overkill-factory
```

Read `docs/operator/overkill-factory-bridge.md` for the bridge architecture and
`docs/operator/overkill-factory-bridge-plugin.md` for install, inbox resolution
and hook trust.

## First Run

From a clean checkout:

```bash
git clone https://github.com/felipegermano17/overkill-factory.git
cd overkill-factory
python -m pip install -e .
factoryctl doctor
factoryctl run minimal
```

The minimal run writes local output under `.tmp/`, including a quickstart result
and worker packets for the public example card.
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
| `.agents/` | Repo-local Codex plugin marketplace for installing the bridge. See `.agents/README.md`. |
| `.codex/` | Project-local Codex hooks for the operator bridge. See `.codex/README.md`. |
| `.github/` | GitHub workflows, templates, Dependabot and repository hygiene. See `.github/PROJECT_SURFACE.md`. |
| `adapters/` | Runtime integrations, currently Hermes hooks and patches. See `adapters/README.md`. |
| `agents/` | Public worker registry, profiles, permissions, capability packs and Hermes bindings. See `agents/README.md`. |
| `docs/` | Human guides for onboarding, concepts, operations, security and maintenance. See `docs/README.md`. |
| `examples/` | Small public examples and source fixtures for the factory path. See `examples/README.md`. |
| `fixtures/` | Minimal public-safe regression fixtures, including advanced product-shaped validation fixtures. See `fixtures/README.md`. |
| `planning-bundles/` | Public-safe planning protocols for candidate artifacts before factory validation. See `planning-bundles/README.md`. |
| `plugins/` | Public Codex plugin packages, currently the Overkill Factory Bridge. See `plugins/README.md`. |
| `schemas/` | Machine contracts for cards, receipts, workers, gates and public artifacts. See `schemas/README.md`. |
| `scripts/` | CLI entrypoints, validation tools, proof helpers and maintainer checks. See `scripts/README.md`. |
| `skills/` | Installable Codex skill material for operating the factory from a public clone. See `skills/README.md`. |
| `templates/` | Starter contracts paired with schemas and tests. See `templates/README.md`. |
| `tests/` | Regression coverage for public contracts, docs, adapters and examples. See `tests/README.md`. |

Ignored local folders such as `.tmp/`, `build/`, `dist/`, `site/` and
`*.egg-info/` are not public product surfaces.

## Current Release State

Factory v1 is the current public kernel release line. The latest public release
is v1.5.9.

It includes:

- Universal Signal Intake, route registry, Golden Corpus and signal coverage;
- operator interface profiles for Telegram, Discord, Cockpit and bridge use;
- conversational start before a formal factory start request exists;
- operator understanding confirmation before Product SOT for product creation;
- briefing packages with document/PDF attachments for important decisions;
- Product SOT, full-scope planning, method contracts and readiness checks;
- worker registry, Hermes bindings, permissions and capability-pack routing;
- Solana AI Kit domain-brain routing for Solana and on-chain work;
- high-risk Solana/on-chain remote proof and R4 routing gates;
- Codex Bridge plugin docs and package for operator-to-factory handoff;
- Product Face packet/result contracts plus project design-system and
  `DESIGN.md` gating;
- release preflight, public-surface sync, safety scans and Factory v1
  Completion Gate;
- deterministic phase lock, single active frontier and downstream freeze before
  architecture, repo cleanup, human gates or worker packets;
- deterministic Phase Engine state so materialized artifacts, not agent prose or
  declared card phase, decide the active frontier and next required artifact;
- deterministic Hermes/Kanban board reconciliation so a silent board becomes
  one allowed next-artifact task, native dispatch, or a real bounded gate
  request instead of agent-chosen phase routing;
- Kanban-native workflow binding with `workflow_template_id=overkill-vfinal`
  and deterministic `current_step_key` on factory-created Hermes tasks when the
  installed Hermes database exposes those fields;
- no-idle classification that treats missing decision packages, PDF/readback,
  owner-readable materials and repair tasks gated behind their own blocker as
  factory-owned repair, not operator approval bureaucracy;
- Solana AI Kit route repair when Solana/on-chain F4+ planning lacks the
  required structured domain-brain record;
- Hermes completion artifact projection, no-idle remediation controls, Hermes
  update guard, cron-friendly no-idle watchdog and Fast Autonomy Lane contracts.

That claim is intentionally scoped. Factory v1 means the public kernel is
complete enough to install, inspect, validate and extend. A product built by the
factory still needs its own source material, Product SOT, worker execution,
evidence, reviews, human gates and production readiness proof.
Public promises are tracked in
`docs/operations/promise-to-implementation.md` and
`docs/promise-implementation-map.public.json`; each major claim must name its
implementation, proof and boundary.

## Read Next

- `docs/index.md`: documentation home.
- `docs/getting-started/quickstart-hermes.md`: first run with Hermes context.
- `docs/getting-started/install-in-hermes.md`: connect the factory to an
  operator-owned Hermes runtime.
- `docs/governance/document-governance.md`: document authority and public
  boundary rules.
- `docs/reference/cli.md`: supported `factoryctl` commands.
- `docs/architecture/factory-operating-systems.md`: OS registry and production
  claim boundary.
- `docs/concepts/factory-flow.md`: production line and state model.
- `docs/concepts/overkill-factory-method.md`: method guide.
- `docs/concepts/operator-journey.md`: operator journey.
- `docs/visuals/README.md`: visual map boundary and validation.
- `agents/README.md`: human entrypoint for the worker contract directory.
- `docs/agents/worker-profiles.md`: worker roles, inputs, outputs and limits.
- `docs/agents/factory-stage-agent-map.md`: stage-to-worker ownership map.
- `docs/agents/capability-packs.md`: product-type coverage rules.
- `docs/control-tower/open-source-setup.md`: optional Control Tower setup.
- `docs/operations/validation-and-release.md`: release validation checklist.
- `docs/operations/promise-to-implementation.md`: promise-to-proof audit and
  drift prevention rules.
- `docs/operations/fast-autonomy-lane.md`: fast autonomous execution limits.
- `scripts/factory_no_idle_watchdog.py`: Hermes-cron no-idle heartbeat for
  Telegram-first operation.
- `factoryctl reconcile-board`: deterministic board-level next action from a
  Hermes/Kanban snapshot.
- `docs/operations/release-policy.md`: release and versioning policy.
- `docs/operations/troubleshooting.md`: common failures and recovery path.
- `docs/architecture/hermes-integration.md`: Hermes adapter architecture.
- `docs/operator/overkill-factory-bridge.md`: Codex/operator bridge architecture.
- `docs/operator/overkill-factory-bridge-plugin.md`: Codex plugin install and
  hook trust.
- `docs/examples/gallery.md`: public examples.
- `docs/security/oss-security.md`: security posture.
- `docs/maintenance/repo-surface.md`: public surface maintenance rules.
- `docs/maintenance/hermes-learn-integration.md`: Hermes `/learn` boundary for
  staged skill candidates.
- `.agents/README.md`: repo-local Codex plugin marketplace boundary.
- `plugins/README.md`: public plugin package boundary.
- `examples/minimal-hermes-project/README.md`: minimal runnable example.
- `.env.example`: safe environment variable template.
- `CHANGELOG.md`: public release history.
- `CONTRIBUTING.md`: contribution rules and required checks.
- `SECURITY.md`: security reporting and public-boundary policy.

## Validation

Before publishing public changes:

```bash
python scripts/validate_document_governance.py
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python scripts/validate_promise_implementation_map.py
python scripts/validate_planning_bundles.py
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
python scripts/validate_public_surface_sync.py --check-published
python -m unittest discover -s tests -q
```

For release readiness:

```bash
python scripts/release_integration_preflight.py
python scripts/worktree_release_inventory.py
factoryctl v1-completion-gate --github-actions-result PASS --open-v1-blockers 0 --open-prs 0
```

The public map is validated by `scripts/validate_public_surface_sync.py`. It
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
