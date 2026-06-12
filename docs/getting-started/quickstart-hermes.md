# Quickstart: Use Overkill Factory With Your Own Hermes

This guide gets an external operator from a fresh checkout to a local factory
smoke. It does not require a private runtime, Discord server or historical test
bundle.

## Prerequisites

- Git
- Python 3.11 or newer
- Hermes only when you are ready to route real cards

Discord is optional cockpit UI. It is not the source of truth.

## Three Commands

```bash
git clone https://github.com/<owner>/overkill-factory.git
cd overkill-factory
python scripts/quickstart_smoke.py
```

Expected first value: a `PASS` line within a few minutes on a normal Python
checkout.

The command writes:

- `.tmp/quickstart-result.json`
- `.tmp/minimal-worker-packets/*.json`

The JSON result tells you whether the minimal card validates, whether the gate
report is ready for worker execution and how many required worker packets were
created.

Those files are local outputs. Keep generated worker packets and gate reports in
`.tmp/`; do not copy them into `examples/`.

## Optional Local CLI

Install the editable package when you want shell commands instead of script
paths:

```bash
python -m pip install -e .
overkill-quickstart
factoryctl gate-report --card examples/minimal-hermes-project/card.md
```

## What To Inspect

After the smoke passes, inspect:

- `examples/minimal-hermes-project/card.md`
- `.tmp/quickstart-result.json`
- `.tmp/minimal-worker-packets/`
- `docs/agents/worker-profiles.md`
- `docs/agents/factory-stage-agent-map.md`
- `docs/agents/capability-packs.md`

Worker packets are assignments, not proof. A card is complete only when current
worker results, required reviews and Receipt Five agree.

## Connect Hermes

Read `adapters/hermes/README.md` before patching your Hermes checkout. The
adapter provides:

- a Kanban gate patch;
- a transition hook for worker routing;
- a done-time reconciliation model for Receipt Five and worker results.

From a Hermes checkout:

```bash
git switch -c overkill-factory-adapter
git apply <path-to-overkill-factory>/adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch
python -m pytest -q -o addopts='' tests/hermes_cli/test_overkill_factory_v35_gate.py
```

Wire Hermes transition events to:

```bash
python <path-to-overkill-factory>/adapters/hermes/transition_hook.py --help
```

Introduce the adapter in a test runtime before any real product or release work.

## Create A Real Project Entry

For your own project:

1. Start with a short paper or product brief.
2. Create a factory card from the relevant example in `examples/cards/`.
3. Fill source refs, scope, risk, runtime, security, forbidden actions and done
   definition.
4. Run `factoryctl validate-card`.
5. Run `factoryctl gate-report`.
6. Generate required worker packets.
7. Let Hermes create or route worker cards.
8. Attach worker results and Receipt Five before any `done` transition.

## Before Release

Run the release checks in `docs/operations/validation-and-release.md`. Keep raw
outputs in `.tmp`, a private evidence store or a release artifact. Do not commit
old screenshots, old pilot receipts or narrative validation history.
