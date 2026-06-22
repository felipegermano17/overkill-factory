# Overkill Factory

Language: English | [Portugues](README.pt-BR.md)

Overkill Factory is an open-source production system for agentic product work.
It turns rough product signals into controlled factory state: source intake,
Product SOT, full-scope planning, method routing, worker packets, gates,
evidence, review, release readiness and learnback.

It is built for operators who want agents to work without letting chat,
enthusiasm or a partial demo become the source of truth.

Public map:
https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.1.html

## Why This Exists

Agentic work usually fails in the spaces between tasks:

- a product paper becomes an informal summary;
- a first slice quietly replaces the full product scope;
- a worker says "done" without inspectable evidence;
- a dashboard looks useful but is not the runtime source of truth;
- a blocked path waits for the operator even when the factory should repair it.

Overkill Factory makes those spaces explicit. A signal is routed through known
contracts. Every important state has an owner, gate, next action and evidence
shape. Non-human blocks are expected to return to factory-owned repair routes.
Human gates remain human gates.

## How The Factory Works

The public method is a complete production line, not an MVP shortcut:

```text
raw signal
-> Universal Signal Intake
-> source ledger and source resolution
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

The input can be a product paper, bug, idea, existing repository, incident,
release request, research request, UX request, analytics request, integration,
migration or agent/runtime change. The route registry and golden signal corpus
make those paths inspectable instead of hidden in conversation.

The intended output is not "a good answer." It is a product or factory decision
that can be audited: what was requested, what was planned, what was blocked,
what was done, who or what had authority, and what evidence allows the next
state.

For product-facing work, the route must also create a project design-system
contract and AI-readable `DESIGN.md` before frontend builders or Product Face
proof can pass.

## Hermes Runtime

Hermes is the first supported factory floor. The factory does not replace
Hermes; the normal execution path today is Hermes Kanban plus Overkill Factory
contracts.

Overkill Factory provides the method, contracts, schemas, worker registry,
Hermes bindings, adapter hooks, examples and validation tools. Hermes provides
the durable Kanban runtime where cards, workers, comments, runs and state
transitions live.

The practical boundary is simple:

- `factoryctl`, schemas and tests validate public contracts.
- Hermes Kanban is the runtime authority for real cards and transitions.
- Receipt Five and worker results are the completion evidence.
- Operator Consoles and operator dashboards can project state, but they do not approve
  gates or replace Hermes.

## Use With The Codex Bridge Plugin

There are two public operating paths:

- direct: use `factoryctl` and connect generated packets to your Hermes runtime;
- bridged: install the Codex Bridge plugin so Codex can act as the human
  operator bridge.

The plugin does not run the factory. It helps the operator collect the initial
signal, start an approved factory run, read the Durable Operator Inbox, report
pending human gates, record the operator's answer and hand that answer back to
the factory.

Hermes Kanban remains the source of truth. Worker results and Receipt Five
still decide completion. The plugin is only the bridge between the operator and
the runtime.

Install from the repo root:

```bash
codex plugin marketplace add .
codex plugin add overkill-factory-bridge@overkill-factory
```

Start a new Codex thread after installation and review/trust the plugin hooks.
The hooks run when Codex starts or when the operator submits a prompt. They do
not keep Codex active 24/7, approve gates, mutate Hermes, run workers or
replace Receipt Five.

Use the bridge when you want to ask for factory status, start an approved run,
see what is blocked, answer a human gate or request a scoped change without
letting chat become the source of truth.

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

Generated worker packets and gate reports belong in `.tmp/`, release artifacts
or a private evidence store, not in the public repo.

Useful next commands:

```bash
factoryctl init --out ../my-product-factory --project-name my-product
factoryctl route-registry --route-class product_creation
factoryctl intake --route-class product_creation --request-type product_new --signal-type product_paper --summary "Public product brief enters the complete product-creation route." --source-ref external:source-card-product-brief --out .tmp/product-intake.json
factoryctl source-resolution --intake .tmp/product-intake.json --intake-ref external:sanitized-product-intake --out .tmp/source-resolution-packet.json
factoryctl source-ledger --source-resolution .tmp/source-resolution-packet.json --source-ref external:source-card-product-brief --out .tmp/product-source-ledger.json
factoryctl outcome-contract --source-ledger .tmp/product-source-ledger.json --out .tmp/outcome-contract.json
factoryctl product-sot --outcome-contract .tmp/outcome-contract.json --out .tmp/product-sot.json
factoryctl full-scope-coverage --product-sot .tmp/product-sot.json --out .tmp/full-product-sot-scope-coverage.json
factoryctl method-contract --full-scope-coverage .tmp/full-product-sot-scope-coverage.json --out .tmp/method-contract.json
factoryctl product-creation-plan --method-contract .tmp/method-contract.json --out .tmp/product-creation-plan.json
factoryctl product-implementation-readiness --product-creation-plan .tmp/product-creation-plan.json --out .tmp/product-implementation-readiness.json
factoryctl ready-work-unit-packets --product-creation-plan .tmp/product-creation-plan.json --product-implementation-readiness .tmp/product-implementation-readiness.json --out .tmp/ready-work-unit-packets
factoryctl validate-ready-work-unit-packets .tmp/ready-work-unit-packets/manifest.json
factoryctl signal-coverage --out .tmp/factory-runs/signal-coverage/factory-signal-coverage-scorecard.json
factoryctl gate-report --card examples/minimal-hermes-project/card.md
factoryctl worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
```

Read `docs/getting-started/quickstart-hermes.md` and
`docs/getting-started/install-in-hermes.md` when connecting the factory to your
own Hermes runtime.

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
| `fixtures/` | Minimal public-safe regression fixtures, including advanced product-shaped validation fixtures when scripts need them. See `fixtures/README.md`. |
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

Factory v1 is the current public kernel release line; the latest public tag is
v1.1.1. It includes:

- Universal Signal Intake and route registry;
- Golden Corpus and signal coverage checks;
- Product SOT, full-scope planning and method contracts;
- worker registry, Hermes bindings and permission classes;
- capability-pack activation rules;
- Solana AI Kit domain-brain routing for Solana and on-chain work;
- high-risk Solana/on-chain remote proof and R4 routing gates;
- Codex Bridge plugin docs and package for operator-to-factory handoff;
- Product Face packet/result contracts plus project design-system / `DESIGN.md`
  gating;
- release preflight, public-surface sync and safety scans;
- Factory v1 Completion Gate.

That claim is intentionally scoped. Factory v1 means the public kernel is
complete enough to install, inspect, validate and extend. A product built by the
factory still needs its own source material, Product SOT, worker execution,
evidence, reviews, human gates and production readiness proof.

## Read Next

- `docs/index.md`: documentation home.
- `docs/getting-started/quickstart-hermes.md`: first run with Hermes context.
- `docs/getting-started/install-in-hermes.md`: connect the factory to an
  operator-owned Hermes runtime.
- `docs/governance/document-governance.md`: document authority and public
  boundary rules.
- `docs/reference/cli.md`: supported `factoryctl` commands.
- `docs/concepts/factory-flow.md`: the production line and state model.
- `docs/concepts/overkill-factory-method.md`: method guide.
- `docs/concepts/operator-journey.md`: operator journey.
- `docs/visuals/README.md`: visual map boundary and validation.
- `agents/README.md`: human entrypoint for the worker contract directory.
- `docs/agents/worker-profiles.md`: worker roles, inputs, outputs and limits.
- `docs/agents/factory-stage-agent-map.md`: stage-to-worker ownership map.
- `docs/agents/capability-packs.md`: product-type coverage rules.
- `docs/control-tower/open-source-setup.md`: optional Control Tower setup.
- `docs/operations/validation-and-release.md`: release validation checklist.
- `docs/operations/release-policy.md`: release and versioning policy.
- `docs/operations/troubleshooting.md`: common failures and recovery path.
- `docs/architecture/hermes-integration.md`: Hermes adapter architecture.
- `docs/operator/overkill-factory-bridge.md`: Codex/operator bridge architecture.
- `docs/operator/overkill-factory-bridge-plugin.md`: Codex plugin install and hook trust.
- `docs/examples/gallery.md`: public examples.
- `docs/security/oss-security.md`: security posture.
- `docs/maintenance/repo-surface.md`: public surface maintenance rules.
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
