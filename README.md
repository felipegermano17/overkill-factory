# Overkill Factory

Overkill Factory is an open source production line for agentic product work.
It helps a Hermes operator turn a raw product or project paper into a controlled
sequence of source resolution, planning, architecture, specialist work,
evidence, review, gates and receipts.

The project is not a chat prompt. It is a set of public contracts, worker
profiles, adapter hooks, examples and validation scripts that make agent work
inspectable before it is allowed to move forward.

## What It Is

Overkill Factory gives Hermes a product-production method:

```text
paper or project brief
-> source resolution
-> Product SOT
-> architecture and risk routing
-> Hermes worker cards
-> specialist execution
-> evidence and Receipt Five
-> independent review and human gates
-> release readiness
```

The repository contains the public method, card and receipt schemas, worker
registry, Hermes profile bindings, adapter scripts, tests and a small runnable
example.

## Who It Is For

Use it when you already run, or want to run, product work with Hermes and need:

- repeatable gates instead of informal agent handoffs;
- explicit worker roles for planning, building, security, proof and release;
- receipts that make completion inspectable beyond a chat transcript;
- a way to let agents work while still preserving human authority for high-risk
  decisions.

It is especially useful for product teams, solo builders and agent operators who
want autonomous help without pretending that autonomy removes gates, access
control, review or release responsibility.

## What It Does

Overkill Factory provides:

- a card contract for describing phase, risk, scope, runtime, security and done
  evidence;
- a worker registry and Hermes profile bindings for routing work to the right
  role;
- a capability pack registry for checking whether the product type has ready
  specialist coverage before execution;
- a single `factoryctl` CLI for install health, project init, local smoke,
  card validation, gate reports and worker packets;
- a Hermes adapter and transition hook that can block weak `ready` and `done`
  transitions;
- public-safe examples and receipt contracts;
- safety scans for secrets and private/public boundary mistakes.

## What It Does Not Do

Overkill Factory does not automatically:

- understand your business without source material;
- approve architecture, security, release or human gates;
- deploy to production;
- move funds, sign transactions or handle real keys;
- replace Codex Security, Auditor, Product Face proof, QA or human review;
- require Discord as a source of truth;
- make every registered worker run on every card;
- pretend every product type already has executable specialists. If a paper
  asks for mobile, desktop, game, AI/ML, fintech, regulated, analytics,
  browser-extension or hardware work, capability-pack validation can block until
  the matching pack is activated.

Hermes and Receipt Five remain the source of truth. Discord or another Control
Tower can be a cockpit, but it is not the evidence store.

## How Hermes Fits

Hermes is the first supported runtime. Overkill Factory supplies the factory
method and contracts; Hermes supplies the Kanban floor where cards, workers and
state transitions live.

The adapter files are under `adapters/hermes/`:

- `adapters/hermes/README.md` explains the patch and transition model.
- `adapters/hermes/transition_hook.py` prepares worker routing and done-time
  evidence reconciliation.
- `agents/hermes-profile-bindings.public.json` maps public workers to Hermes
  profile names, queues, skills and receipt fields.

You can run local validation without Discord. Configure a Control Tower only
after the local card, worker packet and receipt path is clear.

## Operator Path

For a person or AI installing the factory into their own Hermes, use the CLI
path first and open dense contracts only when needed:

```bash
python -m pip install -e .
factoryctl doctor
factoryctl run minimal
factoryctl init --out ../my-product-factory --project-name my-product
```

Then read `docs/getting-started/install-in-hermes.md` and connect generated
worker packets to your Hermes test runtime. The factory is easy to maintain
when common user flows go through `factoryctl` and maintainer internals stay
behind docs, schemas and tests.

## Quickstart

Three-command local smoke from a fresh checkout:

```bash
git clone https://github.com/<owner>/overkill-factory.git
cd overkill-factory
python -m pip install -e .
factoryctl doctor
factoryctl run minimal
```

The smoke writes `.tmp/quickstart-result.json` and required worker packets under
`.tmp/minimal-worker-packets/`. Read
`docs/getting-started/quickstart-hermes.md` for the same path with Hermes
configuration notes.

`python scripts/quickstart_smoke.py` and `overkill-quickstart` remain
compatibility entrypoints, but `factoryctl run minimal` is the public operator
path.

## First Value In 10 Minutes

First value is binary: the quickstart prints `PASS`, writes
`.tmp/quickstart-result.json` and generates worker packets in
`.tmp/minimal-worker-packets/`.

After that run, you should know:

- whether the minimal card contract is valid;
- which workers are required before execution;
- whether the gate is ready for worker execution;
- which packet files Hermes would receive next.

Generated worker packets and gate reports belong in `.tmp/`, not in the public
repository. Commit source examples, schemas, scripts and tests; regenerate run
outputs locally.

## Repository Shape

Every public directory below has a local README with its purpose, boundary,
source of truth and validation path. Open that README before treating a folder
as a place to add files.

| Path | Public Purpose |
| --- | --- |
| `.github/` | CI, issue templates and pull request hygiene. |
| `adapters/` | Runtime integrations, currently Hermes transition hooks and patches. See `adapters/README.md`. |
| `agents/` | Public worker registry, profiles, permissions and Hermes bindings. See `agents/README.md`. |
| `docs/` | Human guides for getting started, concepts, operations, agents and integrations. See `docs/README.md`. |
| `examples/` | Small source examples and fixtures that teach or test the factory path. See `examples/README.md`. |
| `products/` | Public validation products used by product-like and production-lane checks. See `products/README.md`. |
| `schemas/` | Machine contracts for cards, receipts, worker outputs and gates. See `schemas/README.md`. |
| `scripts/` | CLI entrypoints, validation tools, proof helpers and maintainer checks. See `scripts/README.md`. |
| `skills/` | Installable Codex skill material for operating the factory. See `skills/README.md`. |
| `templates/` | Contract templates paired with schemas and tests. See `templates/README.md`. |
| `tests/` | Regression coverage for the public contracts and quickstart path. See `tests/README.md`. |

## Current Status

The public repository has validated schemas, worker profiles, Hermes profile
bindings, adapter hooks, safety scans, a packaged CLI and a runnable public
example. The adapter patch and transition hook are public, and the local
validation suite is the required first check before publication or release work.

The project is still not a hosted service and not a production launch. A user
must connect it to their own Hermes runtime, configure any real tools they want
workers to use, and provide real approval records for high-risk work.

## Documentation Authority

The current external-user path is this README, the quickstart, the concept flow,
the operations checklist and the executable gates. Narrative validation history,
old roadmaps, pilot writeups and research notes do not belong in the public
onboarding path.

When documents disagree, use this order:

1. `scripts/factoryctl.py`, schemas, adapter hooks and tests.
2. `README.md`, `docs/getting-started/quickstart-hermes.md`,
   `docs/concepts/factory-flow.md`,
   `docs/concepts/overkill-factory-method.md`,
   `docs/concepts/operator-journey.md` and
   `docs/operations/validation-and-release.md`.
3. Agent, worker, capability, security and Product Face support docs.
4. Generated local outputs under `.tmp/factory-runs/` only for the run that
   produced them. They are not source authority and must not be committed.
   Generated worker packets and gate reports belong in `.tmp/`.

See `docs/governance/document-governance.md` for the document status rules. A
task idea is not a runtime gate until it has a schema, script, test, worker,
adapter rule or receipt contract.

## Documentation Map

- `docs/governance/document-governance.md`: what belongs in public docs versus
  local/private evidence.
- `docs/index.md`: docs home and navigation.
- `docs/getting-started/quickstart-hermes.md`: first run with your own Hermes.
- `docs/getting-started/install-in-hermes.md`: install and connect the factory
  to an operator-owned Hermes runtime.
- `docs/reference/cli.md`: supported `factoryctl` commands.
- `docs/concepts/factory-flow.md`: core concepts and phase flow.
- `docs/concepts/overkill-factory-method.md`: human-readable method guide.
- `docs/concepts/operator-journey.md`: step-by-step operator journey.
- `docs/visuals/README.md`: public visual-map boundary and validation rules.
- Public visual map:
  `https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v0.1.0.html`.
- `docs/agents/worker-profiles.md`: worker roles, inputs, outputs, limits and
  evidence.
- `agents/README.md`: human entrypoint for the agent contract directory.
- `docs/agents/factory-stage-agent-map.md`: which worker owns each canonical
  factory stage and what proof blocks the next step.
- `docs/agents/capability-packs.md`: ready product coverage and pack activation
  rules.
- `docs/control-tower/open-source-setup.md`: optional Discord/Control Tower
  setup.
- `docs/operations/validation-and-release.md`: validation and release checklist.
- `docs/operations/release-policy.md`: semantic versioning, release checks and
  point-5 boundary.
- `docs/operations/troubleshooting.md`: common failures and how to continue.
- `docs/architecture/hermes-integration.md`: adapter and runtime integration.
- `docs/examples/gallery.md`: which example to use for minimal, Product Face,
  security and onchain paths.
- `docs/security/oss-security.md`: repository security controls.
- `docs/maintenance/repo-surface.md`: operator surface versus maintainer
  internals and generated output.
- `examples/minimal-hermes-project/README.md`: small public-safe example.
- `.env.example`: safe environment variable template.
- `CHANGELOG.md`: public release history.
- `CONTRIBUTING.md`: contribution rules and required checks.
- `SECURITY.md`: security reporting and public-boundary policy.

## Public Safety

Public artifacts must not contain secrets, private source dumps, local absolute
paths, private board links, raw logs or private operational history.

Run these before publishing:

```bash
python scripts/validate_document_governance.py
python scripts/secret_safety_scan.py
python scripts/public_safety_scan.py
python scripts/validate_public_json_artifacts.py
```

## License

MIT.
