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
