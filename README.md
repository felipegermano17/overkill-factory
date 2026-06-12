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
registry, Hermes profile bindings, adapter scripts, validation fixtures and a
small runnable example.

## Who It Is For

Use it when you already run, or want to run, product work with Hermes and need:

- repeatable gates instead of informal agent handoffs;
- explicit worker roles for planning, building, security, proof and release;
- evidence that survives beyond a chat transcript;
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
- `factoryctl.py` helpers for validating cards, creating gate reports and
  generating worker packets;
- a Hermes adapter and transition hook that can block weak `ready` and `done`
  transitions;
- public-safe examples, worker packets, receipts and validation artifacts;
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

## Quickstart

Start here:

1. Read `docs/getting-started/quickstart-hermes.md`.
2. Run the validation commands in `docs/operations/validation-and-release.md`.
3. Generate a gate report from `examples/minimal-hermes-project/card.md`.
4. Review worker responsibilities in `docs/agents/worker-profiles.md`.
5. Review stage ownership in `docs/agents/factory-stage-agent-map.md`.
6. Review product-type coverage in `docs/agents/capability-packs.md`.
7. Add Hermes and optional Control Tower configuration with `.env.example`.

Minimal local smoke:

```bash
python scripts/factoryctl.py validate-card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py gate-report --card examples/minimal-hermes-project/card.md
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/minimal-hermes-project/card.md --out .tmp/minimal-worker-packets
python -m unittest discover -s tests -p "test_*.py" -q
```

On Windows PowerShell, create the output directory first if your shell does not
create it through the helper:

```powershell
New-Item -ItemType Directory -Force .tmp\minimal-worker-packets
python scripts\factoryctl.py worker-packet --worker all --required-only --card examples\minimal-hermes-project\card.md --out .tmp\minimal-worker-packets
```

## Current Status

The public repository has validated schemas, worker profiles, Hermes profile
bindings, adapter fixtures, safety scans and a public validation product. The
adapter patch and transition hook are public, and the local validation suite is
the required first check before publication or release work.

The project is still not a hosted service and not a production launch. A user
must connect it to their own Hermes runtime, configure any real tools they want
workers to use, and provide real approval records for high-risk work.

## Documentation Authority

The current external-user path is this README, the quickstart, the concept flow,
the operations checklist and the executable gates. Methodology, review, planning
and roadmap documents are supporting evidence unless their banner says they are
a current supporting guide.

When documents disagree, use this order:

1. `scripts/factoryctl.py`, schemas, adapter hooks and tests.
2. `validation/canonical-runtime-enforcement/` and
   `validation/canonical-real-infra/`.
3. `README.md`, `docs/getting-started/quickstart-hermes.md`,
   `docs/concepts/factory-flow.md` and
   `docs/operations/validation-and-release.md`.
4. Agent, worker, capability, security and Product Face support docs.
5. Historical methodology, reviews, roadmaps, risk registers and pilot notes.

See `docs/governance/document-governance.md` for the document status rules. A
roadmap or risk-register item is not a runtime gate until it has a schema,
script, test, worker, adapter rule or validation receipt.

## Documentation Map

- `docs/governance/document-governance.md`: how to read current, backlog,
  historical and evidence documents.
- `docs/getting-started/quickstart-hermes.md`: first run with your own Hermes.
- `docs/concepts/factory-flow.md`: core concepts and phase flow.
- `docs/agents/worker-profiles.md`: worker roles, inputs, outputs, limits and
  evidence.
- `docs/agents/factory-stage-agent-map.md`: which worker owns each canonical
  factory stage and what proof blocks the next step.
- `docs/agents/capability-packs.md`: ready product coverage and pack activation
  rules.
- `docs/control-tower/open-source-setup.md`: optional Discord/Control Tower
  setup.
- `docs/operations/validation-and-release.md`: validation and release checklist.
- `docs/operations/troubleshooting.md`: common failures and how to continue.
- `docs/architecture/hermes-integration.md`: adapter and runtime integration.
- `docs/validation/canonical-real-infra-audit.md`: current answer for whether
  the actionable canonical process is enforced by runtime gates.
- `docs/roadmap/factory-vfinal-prepilot-roadmap.md`: prepilot backlog and
  follow-up rules that must stay outside the canonical narrative.
- `examples/minimal-hermes-project/README.md`: small public-safe example.
- `.env.example`: safe environment variable template.

Longer method, validation and historical artifacts remain in `docs/methodology/`,
`docs/validation/`, `validation/` and `pilots/`. Treat those as supporting
evidence, not as the first user path.

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
