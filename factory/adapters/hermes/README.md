# Hermes Adapter

Hermes is the live runtime floor for the Overkill Factory.

The repository defines contracts, schemas, templates, validators and worker boundaries. Hermes owns live cards, worker execution, comments, attachments, process state and runtime evidence. The adapter connects those two worlds without letting chat text or copied templates pretend to be product proof.

Read the full model in `docs/en/factory-manual.md` and `docs/en/technical-reference.md`.

## What This Adapter Does

- checks Factory card contracts before status transitions;
- builds transition plans for required workers;
- materializes safe Hermes tasks from worker packets;
- reconciles worker results, evidence and Receipt Five fields;
- blocks unsafe `ready` or `done` moves with a clear reason;
- supports no-idle recovery without creating a shadow scheduler.

## What It Must Not Do

- approve human gates;
- bypass Hermes Kanban;
- treat template examples as product evidence;
- treat a worker summary as proof without readback;
- let executor and reviewer be the same authority;
- close production, mainnet, funds, secrets or R4 work without explicit human authority.

## Current Patch Boundary

The compatibility patch is:

```text
patches/0001-overkill-factory-v35-gates-official-main.patch
```

It adds Factory gates for Product Face, onchain/Solana/Quasar packages, Auditor requirements, security scan packets, anti-self-review, R4 human gates, Receipt Five, transition-event metadata and done-time worker-result checks.

Check a Hermes checkout with:

```bash
python adapters/hermes/compatibility-check.py
```

The patch is a runtime gate layer. It is not proof that a live product was delivered.

## Transition Hook

Hermes should call the hook before important status transitions.

Toward `ready`:

```bash
python adapters/hermes/transition_hook.py \
  --card path/to/card.md \
  --from-status draft \
  --to-status ready \
  --ledger path/to/worker-ledger.json \
  --out path/to/ready-hook-result.json
```

Toward `done`:

```bash
python adapters/hermes/transition_hook.py \
  --card path/to/card.md \
  --from-status ready \
  --to-status done \
  --receipt path/to/receipt-five.json \
  --worker-results-dir path/to/worker-results \
  --ledger path/to/worker-ledger.json \
  --out path/to/done-hook-result.json \
  --enforce
```

Repeated transition attempts must be idempotent. The hook should update the same worker tasks instead of creating duplicates.

## Runtime-Strict Evidence

Runtime reconciliation treats public templates as scaffold, not product evidence. References like `templates/...`, `factoryctl:gate-report`, bare scaffold refs or placeholder packets cannot advance a real product phase by themselves.

A phase advances only when product-specific artifacts, worker results, evidence, review and required gates support the transition.

## No-Idle

No-idle is an integrity and recovery path. It may detect stale running work, missing review, declared artifacts that do not exist, blocked cards the Factory can repair and hidden human gates. It must not become the normal route authority.

Use:

```bash
python scripts/factory_no_idle_watchdog.py --board example-board
```

## Validation

From `factory/`:

```bash
python scripts/validate_public_json_artifacts.py
python scripts/validate_worker_profiles.py
python -m unittest tests.test_hermes_transition_hook tests.test_hermes_live_kanban_adapter -q
```

For live claims, local tests are not enough. A real delivery needs live Hermes state, current card data, worker results, evidence, readback, independent review, required human gates and Receipt Five.
