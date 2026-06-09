# Official Hermes Main Patch Smoke

Date: 2026-06-06

## Scope

Validate that the public Overkill Factory Hermes adapter patch applies to a
fresh checkout of the official Hermes repository and that the patched transition
surfaces pass focused regression tests.

## Source

- Repository: `NousResearch/hermes-agent`
- Base commit tested: `56236b16e383cc656bb8c88429902f4de83f1faf`
- Patch tested:
  `adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch`

## Commands

```bash
git apply --check adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch
git apply adapters/hermes/patches/0001-overkill-factory-v35-gates-official-main.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/plugins/test_kanban_dashboard_plugin.py
```

## Observed Result

- Patch syntax check: PASS.
- Patch apply on fresh official Hermes checkout: PASS.
- Focused tests: `119 passed, 1 warning`.

## What This Proves

- The public adapter patch is not just a marker bundle; it applies to the current
  official Hermes main tested in this smoke.
- Overkill Factory `ready` and `done` gates are opt-in and do not break the
  existing Hermes promote/dashboard regression suite used in this smoke.
- CLI completion surfaces gate failures as a non-zero operational error.
- Dashboard/API `ready` and `done` transitions return structured failures rather
  than silently bypassing the gate.

## What This Does Not Prove

- This does not prove that the patch has been accepted upstream.
- This does not prove every future Hermes release remains compatible.
- This does not prove product-specific Product Face, Auditor, Remote Proof,
  release or human-gate execution.
