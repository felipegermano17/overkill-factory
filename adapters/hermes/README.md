# Hermes Adapter

Hermes is the first-class runtime for Overkill Factory.

The adapter hardens Hermes Kanban so Factory cards cannot move through the
production line unless their contracts are complete.

## Patch

```text
patches/0001-add-overkill-factory-10-kanban-gates.patch
patches/0002-enforce-overkill-ready-gate-in-dashboard-moves.patch
```

This patch adds:

- Overkill Factory v3.5 opt-in card gate.
- Product Face requirements.
- Onchain/Solana/Quasar work package requirements.
- Auditor requirement for R3/R4 onchain work.
- Codex Security/Cybersecurity scan packet requirements.
- Security scan result requirements before done.
- Anti-self-review.
- R4 human gate.
- Receipt Five and transition-event done gate.
- Correct CLI exit-code propagation.
- Dashboard direct `ready`, bulk `ready` and post-edit `ready` revalidation, so
  a browser/API move cannot bypass the same Factory gate.
- Regression tests.

## Worker Automation Hook

The patch enforces gates. The executable hook in
`adapters/hermes/transition_hook.py` prepares the next layer: worker routing,
idempotent task creation and done-time evidence reconciliation.

Hermes should call:

```bash
python adapters/hermes/transition_hook.py \
  --card path/to/card.md \
  --from-status draft \
  --to-status ready \
  --ledger path/to/worker-ledger.json \
  --out path/to/ready-hook-result.json

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

The generated ledger tells Hermes which specialist workers must run before a
card can safely move through the factory. The hook is idempotent: repeated
transition attempts update the same worker tasks instead of duplicating them.

Current automation is intentionally an orchestration and reconciliation layer.
It does not replace real Codex Security scans, solanabr/Auditor runs,
screenshots, independent reviews, or human approval records.

## Transition Plan Model

Hermes should treat the factory helper output as a transition plan, not as a
loose report. The plan is the adapter contract for what the runtime is allowed
to do next.

### Toward `ready`

When a card moves toward `ready`, Hermes should generate a gate report and a
transition plan with one subtask per required worker.

Expected behavior:

- invalid cards produce `block_transition`;
- valid cards with required work produce `allow_and_create_worker_tasks`;
- workers with `blocked_missing_inputs` keep the card from reaching `ready`;
- each `requires_execution` worker becomes a Hermes subtask;
- each subtask carries its worker packet, expected Receipt Five field and queue
  class.

Queue classes are deliberately small:

| Queue | Meaning |
| --- | --- |
| `blocking-before-ready` | The card should not become ready until this task or planning gate is resolved. |
| `blocking-before-done` | The card may be ready, but cannot close until this worker result exists. |
| `advisory-review` | Useful review path; not a hard transition blocker unless the card contract says so. |

This is stronger than just attaching a gate report because the runtime gets a
concrete task graph: who must run, when the worker is required, and which
receipt field will prove completion.

### Toward `done`

When a card moves toward `done`, Hermes should not create a fresh claim of
success. It should reconcile worker results and Receipt Five.

Expected behavior:

- load the latest required-worker list from the gate report or transition plan;
- inspect each required worker result;
- match each worker to its expected Receipt Five metadata field;
- block when a required worker result is missing, failed, unsupported or only a
  preflight;
- block when Receipt Five lacks evidence refs, transition-event metadata,
  independent review, security result, Auditor result, Product Face proof or
  human gate records required by the card;
- return `allow_done` only when required worker evidence and Receipt Five agree.

The done transition is therefore a reconciliation gate. A worker packet is not
evidence. A PASS result without artifact refs is not enough. A human gate
without a real decision record is not approval.

## Public Validation Fixtures

The public fixtures under `validation/hermes-transition-plans/` show the shape:

- `*-ready.json` demonstrates `allow_and_create_worker_tasks`;
- `*-done-blocked.json` demonstrates done reconciliation blocking when required
  worker results are still missing.

## Apply

From a Hermes checkout:

```bash
git switch -c codex/overkill-factory-10-gates
git am /path/to/0001-add-overkill-factory-10-kanban-gates.patch
git am /path/to/0002-enforce-overkill-ready-gate-in-dashboard-moves.patch
python -m pytest -q -o addopts='' \
  tests/hermes_cli/test_overkill_factory_v35_gate.py \
  tests/hermes_cli/test_kanban_promote.py \
  tests/hermes_cli/test_kanban_cli.py \
  tests/plugins/test_kanban_dashboard_plugin.py
```

## Contract Version

Factory cards opt into these gates with:

```json
{
  "factory_method_version": "OVERKILL_V3_5_FACTORY_10"
}
```

The legacy Hermes/Overkill v2 cards keep their existing behavior unless they opt
into the stronger Factory 10 contract.

## Known Gap

The committed runtime patch proves the gate model and exit-code enforcement.
The transition-plan fixtures prove the intended fan-out and reconciliation
contract.

Real Hermes runtime integration is still not fully landed inside Hermes itself.
The public adapter now provides the executable hook, ledger contract, CI smoke
and dashboard `ready` parity patch. The remaining work is to wire Hermes Kanban
events into this hook, map ledger tasks to real dashboard/API worker cards,
ingest worker result artifacts, and prove `done` plus worker/API routes share
the same gate path under real dispatched execution.
