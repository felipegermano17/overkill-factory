# Hermes Adapter

Hermes is the required first runtime for Overkill Factory.

Use Hermes Kanban as the factory floor:

- Cards hold the work contract.
- Status transitions are authority boundaries.
- Gates block weak cards before execution.
- Done requires evidence, not prose.

Factory 10 was first proven on a Hermes checkout:

```text
branch: codex/overkill-factory-10-gates
commit: d297c0c78900d6858384297895ef4392e6fb85b9
```

Portable patch:

```text
adapters/hermes/patches/0001-add-overkill-factory-10-kanban-gates.patch
```

Validation command used:

```bash
venv/bin/python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
```

Expected result: `72 passed`.

When operating Overkill/Hermes, also use the `hermes-kanban` skill.
