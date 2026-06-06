# Hermes Compatibility Manifest

Hermes is the first supported Overkill runtime. Updates must be treated as
adapter compatibility work, not as a casual package upgrade.

## Required Adapter Patch

```text
adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch
```

## Required Contract Versions

- `OVERKILL_V3_5_FACTORY_10`

## Required Symbols After Patch

- `OVERKILL_FACTORY_VERSION`
- `_overkill_ready_gate_error`
- `_overkill_completion_gate_error`
- `overkill_ready_gate_error`
- `completion_blocked_overkill_gate`
- `receipt_five`
- `kanban_transition_event`
- `product_face_packet`
- `product_face_result`
- `security_scan_packet`
- `security_scan_result`
- `auditor_result.audit_mode=code_audit`
- `human_gate_record`

## Required Surfaces

- Hermes Kanban card validation before `ready`.
- Hermes completion validation before `done`.
- CLI exit-code propagation for blocked transitions.
- Dashboard direct move and bulk move to `ready` must converge on the same gate
  logic.
- `done` must reject product-facing cards without `product_face_result`.
- `done` must reject onchain/Solana/Quasar cards when Auditor evidence is only
  preflight or lacks `audit_mode=code_audit`.
- Dashboard/API `done` failures must return HTTP 409, not an unstructured
  runtime error.
- Worker routes must converge on the same `complete_task` gate before
  production use.
- Worker CLI completion must surface gate failures as non-zero operational
  errors.

## Incompatible Signs

- Overkill symbols missing after patch.
- `ready` accepts product-facing cards without `product_face_packet`.
- `done` accepts cards without Receipt Five and transition event.
- Security-sensitive cards close without `security_scan_result`.
- Executor and reviewer can be the same identity.
- Blocked transition returns exit code `0`.
- Dashboard/API can bypass CLI/Kanban gate behavior.
- Product-facing or onchain cards can close with Receipt Five but without the
  required worker result records.
- Auditor preflight can be represented as a real onchain code-audit PASS.

## Required Local Checks

```bash
python adapters/hermes/compatibility-check.py
python -m unittest discover -s tests -p "test_*.py" -q
python scripts/public_safety_scan.py
```

For a strong disposable compatibility check, point the checker at a Hermes
checkout:

```bash
OVERKILL_HERMES_CHECKOUT=/path/to/hermes-agent \
  python adapters/hermes/compatibility-check.py
```

## Required Hermes Checkout Checks

Run these on a clean Hermes checkout after applying the adapter patch:

```bash
git apply --check /path/to/0001-overkill-factory-v35-gates-official-main.patch
git apply /path/to/0001-overkill-factory-v35-gates-official-main.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/plugins/test_kanban_dashboard_plugin.py
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
