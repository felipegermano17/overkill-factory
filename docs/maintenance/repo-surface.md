# Repository Surface

> Document status: CURRENT SUPPORTING GUIDE.
> Current authority: README.md, scripts/factoryctl.py, tests/
> Runtime boundary: This guide keeps the repo maintainable. It does not override
> executable gates.

## Operator surface

Files a new operator should open first:

- `README.md`
- `docs/index.md`
- `docs/getting-started/install-in-hermes.md`
- `docs/reference/cli.md`
- `examples/minimal-hermes-project/`

## Maintainer internals

Files maintainers change when contracts evolve:

- `schemas/`
- `templates/`
- `agents/*.json`
- `scripts/`
- `adapters/`
- `tests/`
- `docs/maintenance/factory-mechanic-loop.md`

These are allowed to be dense. They should not be the first path a new user
must understand.

## Generated output

Generated output belongs in `.tmp/`, release artifacts or the operator's private
evidence store. Do not commit generated worker packets, gate reports, old
screenshots, raw logs or historical proof.

## Maintenance Rule

If a workflow becomes common for users, expose it through `factoryctl`. If a
workflow is only for maintainers, document it in the relevant README and keep it
covered by tests. Factory improvement findings should become public-safe GitHub
issues or explicit rejection rationale, not historical evidence committed to
the repo.
