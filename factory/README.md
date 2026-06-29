# Overkill Factory implementation package

This directory contains the factory implementation: CLI, schemas, adapters, worker definitions, templates, examples, fixtures, tests and technical contracts.

Public human documentation lives in the repository root `docs/` directory.

## Develop locally

Run from this directory when developing the factory code:

```bash
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/factoryctl.py doctor
python scripts/factoryctl.py run minimal
```

## What belongs here

- `scripts/` — CLI and validators.
- `schemas/` — machine-readable contracts.
- `templates/` — run, card, worker and receipt templates.
- `adapters/` — runtime adapters.
- `agents/` — worker/capability/profile binding definitions.
- `skills/` — factory skill packages.
- `tests/` — regression tests.
- `examples/` — small public-safe examples with a clear purpose.
- `fixtures/` — public-safe test fixtures with a clear validation purpose.
- `legacy-docs/` — older technical documentation retained only when still useful.

This folder can be technical. The repository root should stay simple.
