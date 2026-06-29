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
adapters/hermes/patches/0002-enforce-overkill-ready-gate-in-dashboard-moves.patch
adapters/hermes/patches/0003-require-overkill-worker-results-before-done.patch
adapters/hermes/patches/0004-handle-overkill-worker-completion-gate-errors.patch
```

Validation command used:

```bash
venv/bin/python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
```

Expected result: the adapter blocks weak transitions and creates worker tasks;
use `docs/architecture/hermes-integration.md` and the CI transition-hook smoke
as the current reference.

When operating Overkill/Hermes, also use the `hermes-kanban` skill.

## Worker Skill Availability

If a Factory card force-loads `overkill-factory`, the skill package must be
available to the specialist profile runtime before dispatch. A real dispatch
smoke proved this with `public-safety-gate`: the profile loaded the factory
skill, ran `python3 scripts/public_safety_scan.py`, wrote evidence and closed
with Receipt Five.

Do not treat a local Codex skill install as sufficient for Hermes workers.
Hermes profiles need access to the same skill package in their runtime skill
search path, including `SKILL.md`, references and scripts.
