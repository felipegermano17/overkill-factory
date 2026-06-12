# Adapters

Adapters connect Overkill Factory contracts to a runtime. Hermes is the first
supported adapter.

## What Belongs Here

- Runtime integrations that translate factory cards, gates, worker packets and
  receipts into a real execution floor.
- Hermes adapter code, transition hooks and runtime patch notes.
- Small adapter fixtures that are required by tests.

## What Does Not Belong Here

- Private runtime patches from a local workspace.
- Historical proof, raw logs, screenshots or past pilot evidence.
- Runtime-specific secrets, local paths, board URLs or operator credentials.

## Source Of Truth

The factory contract remains in schemas, templates, tests and `factoryctl.py`.
The adapter is the runtime bridge, not a second methodology.

## How It Is Validated

Run adapter and public-path checks after changes:

```bash
python scripts/quickstart_smoke.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
python scripts/secret_safety_scan.py
```

For Hermes-specific behavior, inspect `adapters/hermes/README.md` and validate
the transition-hook tests before publishing.
