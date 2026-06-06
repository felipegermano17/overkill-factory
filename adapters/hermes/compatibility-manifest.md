# Hermes Compatibility Manifest

Hermes is the first supported Overkill runtime. Updates must be treated as
adapter compatibility work, not as a casual package upgrade.

## Required Adapter Patch

```text
adapters/hermes/patches/0001-add-overkill-factory-10-kanban-gates.patch
```

## Required Contract Versions

- `OVERKILL_V3_5_AGENT_WORKFORCE`
- `OVERKILL_V3_5_FACTORY_10`

## Required Symbols After Patch

- `_overkill_is_v35_card`
- `_overkill_validate_v35_card`
- `_overkill_validate_v35_completion`
- `receipt_five`
- `kanban_transition_event`
- `security_scan_packet`
- `security_scan_result`

## Required Surfaces

- Hermes Kanban card validation before `ready`.
- Hermes completion validation before `done`.
- CLI exit-code propagation for blocked transitions.
- Dashboard/API/worker routes must converge on the same gate logic.

## Incompatible Signs

- Overkill symbols missing after patch.
- `ready` accepts product-facing cards without `product_face_packet`.
- `done` accepts cards without Receipt Five and transition event.
- Security-sensitive cards close without `security_scan_result`.
- Executor and reviewer can be the same identity.
- Blocked transition returns exit code `0`.
- Dashboard/API can bypass CLI/Kanban gate behavior.

## Required Local Checks

```bash
python adapters/hermes/compatibility-check.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
```

## Required Hermes Checkout Checks

Run these on a clean Hermes checkout after applying the adapter patch:

```bash
git am /path/to/0001-add-overkill-factory-10-kanban-gates.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py
```

## Update Receipt

Every update must produce `update-receipt.template.json` filled with:

- before version;
- after version;
- patch apply result;
- compatibility check result;
- disposable smoke result;
- real-runtime decision;
- rollback plan.
