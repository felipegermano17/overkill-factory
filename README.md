# Overkill Factory

Overkill Factory is a production line for agentic product work.

You bring the first signal: an idea, a repository, a bug, a product brief, an incident, a release request or a messy set of notes. The factory turns that signal into durable work: a clear product definition, a method, a Hermes work graph, bounded specialist workers, evidence, review, human gates when a real human decision is needed, and a final Receipt Five.

It is built for one simple reason: serious product work cannot depend on a chat model remembering what to do next.

```text
signal from the operator
-> manager intake
-> source boundary
-> product definition / PRD
-> method, risk and capability route
-> Hermes work graph
-> bounded workers
-> evidence and review
-> human gate only when needed
-> Receipt Five
-> release, block, operate or learn
```

## What this is

Overkill Factory is the method layer for a Hermes-powered production system.

- Hermes is the runtime: boards, cards, dependencies, dispatch, runs, logs and task state.
- Overkill Factory is the production method: source handling, product definition, gates, worker packets, evidence rules, review rules, human-gate rules, release rules and closure receipts.
- Workers are bounded specialists. They execute or review specific work; they do not become the factory.
- Receipt Five is the closure receipt. It records what changed, where it lives, how it was verified, what reviewed it, and what remains.
- Hermes and Receipt Five remain the source of truth for runtime state and closure evidence.

A worker packet is not execution. If an agent tries to act as the factory without using the factory contracts, Hermes state and validation code, that work must fail closed. Legacy technical reference starts at `factory/legacy-docs/index.md`; it is not the new public manual.

## What makes it different

Most agentic systems fail in the space between tasks.

A plan sounds complete, but the next action is only in chat memory. A worker is assigned, but no result exists. A test passes, but release risk was never checked. A product definition changes silently. A human is asked “can I continue?” when the system already knows the next safe action. Or an agent tries to act like the factory without using the actual factory code, contracts and gates.

Overkill Factory makes those failure modes explicit and fail-closed.

If there is no source boundary, the work cannot pretend assumptions are facts. If there is no product definition, the work cannot pretend it has a target. If a packet exists but no worker result exists, the work did not happen yet. If evidence is missing, the claim does not close. If release needs human authority, the manager must present the decision package instead of hiding it in a status update.

## Repository layout

The public root is intentionally small.

```text
README.md      product entry point
LICENSE        license
.github/       GitHub automation and repository hygiene
docs/          public human documentation, English first with Portuguese companions
factory/       implementation: code, schemas, scripts, adapters, workers, tests and technical contracts
```

Everything that is code-like or machine-facing lives under `factory/`. Everything that explains the product to a human reader lives under `docs/`.

Old technical documentation, when still useful for compatibility or tests, is separated under `factory/legacy-docs/`. It is not the new public manual.

## Start reading

- [Documentation home](docs/index.md)
- [Factory manual](docs/factory-manual.md)
- [How it works](docs/how-it-works.md)
- [Product definition / PRD](docs/product-definition.md)
- [Autonomy and no-idle](docs/autonomy.md)
- [Installation and use](docs/installation-and-use.md)
- [Portuguese documentation](docs/pt-BR/index.md)

Public map: https://storage.googleapis.com/overkill-factory-public-assets-20apy/overkill-factory-map-v1.0.3.html

## Install locally

From the repository root:

```bash
python -m pip install ./factory
factoryctl doctor
factoryctl run minimal
```

For development:

```bash
cd factory
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/factoryctl.py doctor
python scripts/factoryctl.py run minimal
```

For documentation:

```bash
python -m pip install "./factory[docs]"
python -m mkdocs build -f docs/mkdocs.yml --strict --site-dir /tmp/overkill-docs-site
```

## Current status

The local factory kernel, contracts, examples, tests and documentation build path are implemented in this repository. The remaining external proof is the full live operator loop: a real operator signal, Telegram signal where applicable, manager-created FactoryRun, Hermes board dispatch, worker execution, proactive progress delivery, real manager + Hermes + worker + operator E2E, and Receipt Five returned to the operator without relying on this chat.

See [Implementation status](docs/implementation-status.md) for the honest boundary.
