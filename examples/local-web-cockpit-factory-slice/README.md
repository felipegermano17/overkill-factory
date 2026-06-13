# Local Web Cockpit Factory Slice

This example is the public factory intake for the local-first Factory Web
Cockpit.

It is not a finished UI, not a design mockup and not implementation evidence.
It exists so an operator can start the cockpit through the factory's own gated
flow instead of bypassing it with a hand-built screen.

## Files

- `input-paper.md`: source request and boundaries.
- `card.md`: vFinal factory card with Product SOT, Method Contract, Product
  Experience plan, Product Face Packet, security boundaries and proof
  requirements.
- `expected-flow.md`: what the operator should observe when running the gate.

## Run

```bash
python scripts/factoryctl.py validate-card examples/local-web-cockpit-factory-slice/card.md
python scripts/factoryctl.py gate-report --card examples/local-web-cockpit-factory-slice/card.md
python scripts/factoryctl.py worker-packet --worker all --required-only --card examples/local-web-cockpit-factory-slice/card.md --out .tmp/local-web-cockpit-worker-packets
python scripts/factoryctl.py status-snapshot --card examples/local-web-cockpit-factory-slice/card.md --out .tmp/local-web-cockpit-status-snapshot.json
```

Generated worker packets and snapshots stay under `.tmp/`. Do not commit
runtime output, screenshots, raw logs or private operator evidence.
