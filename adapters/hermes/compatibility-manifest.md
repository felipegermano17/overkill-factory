# Hermes Compatibility Manifest

Hermes is the first supported Overkill runtime. Updates must be treated as
adapter compatibility work, not as a casual package upgrade.

## Required Adapter Patch

```text
adapters/hermes/patches/0001-add-overkill-factory-10-kanban-gates.patch
adapters/hermes/patches/0002-enforce-overkill-ready-gate-in-dashboard-moves.patch
adapters/hermes/patches/0003-require-overkill-worker-results-before-done.patch
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
- `_block_ready_task_on_overkill_gate_error`
- `_overkill_v35_validate_worker_result`
- `_overkill_v35_validate_auditor_result`
- `_overkill_v35_validate_product_face_result`
- `_overkill_v35_validate_human_gate_record`

## Required Surfaces

- Hermes Kanban card validation before `ready`.
- Hermes completion validation before `done`.
- CLI exit-code propagation for blocked transitions.
- Dashboard direct move and bulk move to `ready` must converge on the same gate
  logic.
- Dashboard edits/reassignments of an already `ready` card must re-run the
  ready gate before work remains dispatchable.
- `done` must reject product-facing cards without `product_face_result`.
- `done` must reject onchain/Solana/Quasar cards when Auditor evidence is only
  preflight or lacks `audit_mode=code_audit`.
- Dashboard/API `done` failures must return HTTP 409, not an unstructured
  runtime error.
- Worker routes must converge on the same `complete_task` gate before
  production use.

## Incompatible Signs

- Overkill symbols missing after patch.
- `ready` accepts product-facing cards without `product_face_packet`.
- `done` accepts cards without Receipt Five and transition event.
- Security-sensitive cards close without `security_scan_result`.
- Executor and reviewer can be the same identity.
- Blocked transition returns exit code `0`.
- Dashboard/API can bypass CLI/Kanban gate behavior.
- Editing or reassigning a `ready` Factory card can leave invalid work
  dispatchable.
- Product-facing or onchain cards can close with Receipt Five but without the
  required worker result records.
- Auditor preflight can be represented as a real onchain code-audit PASS.

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
git am /path/to/0002-enforce-overkill-ready-gate-in-dashboard-moves.patch
git am /path/to/0003-require-overkill-worker-results-before-done.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py \
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
