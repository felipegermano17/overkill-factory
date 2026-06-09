# Overkill Factory 10 Durability Addendum

Date: 2026-06-05

Goal: turn the Factory 10 Hermes gate proof into portable, versioned,
reviewable work that can be applied to a Hermes checkout without relying on
chat memory or private runtime details.

## Public Result

The Hermes adapter patch is kept in:

```text
adapters/hermes/patches/0001-add-overkill-factory-10-kanban-gates.patch
```

The patch adds the Factory 10 card and completion gates, plus regression tests.
The private runtime where the patch was first proven is intentionally not
documented in this public repository.

## Versioned Files Touched By The Patch

```text
hermes_cli/kanban_db.py
hermes_cli/main.py
tests/hermes_cli/test_overkill_factory_v35_gate.py
```

## Test Shape

The patch-level validation command is:

```bash
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
```

The local repository validation command is:

```bash
python -m unittest discover -s tests -p "test_*.py" -q
```

## Coverage Added

1. Product Face Packet required for visible product surfaces.
2. Executor cannot review its own work.
3. Security-sensitive cards require a scan packet.
4. Done requires `security_scan_result` when a scan is required.
5. R3/R4 onchain work requires Auditor evidence or a structured human waiver.
6. R4 requires a human gate packet with rollback and ownership.
7. Receipt Five and Kanban transition metadata are required before done.
8. CLI command failures propagate a non-zero exit code.

## Operational Decision

Do not rely on the original private runtime as the durable source of truth.
The durable artifact is the patch, the adapter documentation, the schemas, the
local `factoryctl.py` preflight, and the regression tests.

## Promotion Options

1. Apply the patch to a dedicated Hermes fork maintained by the factory.
2. Open a pull request against the appropriate Hermes upstream if the maintainers
   want this integration there.
3. Keep the patch as a public adapter until the factory owns a long-term Hermes
   compatibility branch.

## Next Hardening

1. Wire `factoryctl.py` into Hermes transition events.
2. Auto-create worker packets from gate reports.
3. Add CI for adapter patch application and local schema/preflight tests.
4. Add public safety scans so private terms cannot re-enter the repository.
