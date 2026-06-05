# Hermes Adapter

Hermes is the first-class runtime for Overkill Factory.

The adapter hardens Hermes Kanban so Factory cards cannot move through the
production line unless their contracts are complete.

## Patch

```text
patches/0001-add-kaxis-factory-10-kanban-gates.patch
```

This patch adds:

- KAXIS/Overkill Factory v3.5 opt-in card gate.
- Product Face requirements.
- Onchain/Solana/Quasar work package requirements.
- Auditor requirement for R3/R4 onchain work.
- Codex Security/Cybersecurity scan packet requirements.
- Security scan result requirements before done.
- Anti-self-review.
- R4 human gate.
- Receipt Five and transition-event done gate.
- Correct CLI exit-code propagation.
- Regression tests.

## Worker Automation Hook

The patch enforces gates. The repo-level `scripts/factoryctl.py` prepares the
next layer: worker routing.

Hermes should call:

```bash
python scripts/factoryctl.py gate-report --card path/to/card.md
python scripts/factoryctl.py worker-packet --worker all --card path/to/card.md --out path/to/worker-packets
```

The generated packets tell Hermes which specialist workers must run before a
card can safely move through the factory.

Current automation is intentionally a preflight and handoff layer. It does not
replace real Codex Security scans, solanabr/Auditor runs, screenshots,
independent reviews, or human approval records.

## Apply

From a Hermes checkout:

```bash
git switch -c codex/kaxis-factory-10-gates
git am /path/to/0001-add-kaxis-factory-10-kanban-gates.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_kaxis_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
```

## Contract Version

Factory cards opt into these gates with:

```json
{
  "factory_method_version": "KAXIS_V3_5_FACTORY_10"
}
```

The legacy Hermes/KAXIS v2 cards keep their existing behavior unless they opt
into the stronger Factory 10 contract.

## Known Gap

The committed VM patch already proves the gate model and exit-code enforcement.
The automatic `factoryctl.py` hook still needs to be wired into Hermes runtime
events so worker packets are created when cards move toward `ready` or `done`.
